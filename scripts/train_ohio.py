"""
Train GlucoseTransformer from scratch on the OhioT1DM dataset only.

Train split:  OhioT1DM/2018/train + 2020/train  (12 patients)
Val split:    held-out 20% of sequences per patient (time-ordered: last 20%)
Test split:   OhioT1DM/2018/test  + 2020/test   (evaluated after training)

Key difference from simulation training:
 - Refit the StandardScaler on Ohio data (correct distribution)
 - Same model architecture and hyperparams as original training
 - Clinical Penalty Loss to prioritise hypo/hyper events
 - Saves to checkpoints/best_model_ohio_scratch.pt
"""

import sys, pickle, logging
from pathlib import Path
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.data.ode_features import build_features, make_sequences, FEATURE_NAMES, N_FEATURES
from src.models.glucose_predictor import GlucosePredictor
from scripts.evaluate_ohio import (
    parse_ohio_xml, run_inference_with_scaler,
    rmse, mae, mard, tir_metrics, ega_zones,
    plot_clarke, plot_scatter_grid, plot_error_hist, plot_tir_bars, plot_traces,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CHECKPOINT_OUT = ROOT / "checkpoints/best_model_ohio_scratch.pt"
OHIO_DIR       = ROOT / "OhioT1DM"
OUT_DIR        = ROOT / "results/ohio_scratch"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HORIZONS   = [6, 12, 18, 24]
SEQ_LEN    = 24
BATCH_SIZE = 64
MAX_EPOCHS = 80
PATIENCE   = 15
LR         = 1e-3
WEIGHT_DECAY = 0.01
VAL_FRAC   = 0.20   # last 20% of each patient's sequences → val


@dataclass
class Config:
    model_type: str = "transformer"
    hidden_size: int = 128
    num_layers: int = 4
    num_heads: int = 8
    dropout: float = 0.1
    use_pinn: bool = False
    pinn_lambda: float = 0.0
    batch_size: int = BATCH_SIZE
    learning_rate: float = LR
    weight_decay: float = WEIGHT_DECAY
    epochs: int = MAX_EPOCHS
    early_stopping_patience: int = PATIENCE
    val_split: float = VAL_FRAC
    gradient_clip: float = 1.0
    checkpoint_dir: str = "./checkpoints"


def clinical_penalty_loss(pred, target, p_miss_hypo=2.0, p_miss_hyper=6.0):
    """
    Weighted MSE with higher penalty for clinically dangerous misses:
      - Predicting safe (≥70) when actual is hypo (<70):  weight p_miss_hypo
      - Predicting safe (≤180) when actual is hyper (>180): weight p_miss_hyper
      - Otherwise: weight 1
    """
    sq = (pred - target) ** 2
    w = torch.ones_like(sq)
    # Miss hypo: actual < 70, predicted >= 70
    miss_hypo  = (target < 70) & (pred >= 70)
    # Miss hyper: actual > 180, predicted <= 180
    miss_hyper = (target > 180) & (pred <= 180)
    w[miss_hypo]  = p_miss_hypo
    w[miss_hyper] = p_miss_hyper
    return (w * sq).mean()


def build_ohio_sequences(xml_files):
    """
    Parse all Ohio XMLs and split each patient's sequences into train/val
    (last VAL_FRAC of time-ordered sequences = val).

    Returns separate lists so we can refit scaler on train only.
    """
    train_X_raw, train_y, val_X_raw, val_y = [], [], [], []

    for xml_path in sorted(xml_files):
        pid = xml_path.stem.split("-")[0]
        df = parse_ohio_xml(xml_path)
        if df.empty or len(df) < SEQ_LEN + max(HORIZONS) + 10:
            logger.warning("  Skipping %s — insufficient data", pid)
            continue

        valid = ~df["cgm_mg_dl"].isna()
        feat_df = df[valid].reset_index(drop=True)
        if len(feat_df) < SEQ_LEN + max(HORIZONS) + 10:
            continue

        feat_matrix = build_features(feat_df[["t_min","cgm_mg_dl","insulin_u_h","cho_g","basal_u_h"]])
        # Inject real exercise features
        ex_cols = ["is_exercising","exercise_intensity","time_since_exercise","exercise_minutes_2h"]
        for i, col in enumerate(ex_cols):
            if col in feat_df.columns:
                feat_matrix[:, 31 + i] = feat_df[col].values.astype(np.float32)

        glucose = feat_df["cgm_mg_dl"].values.astype(np.float32)
        X, y = make_sequences(feat_matrix, glucose, SEQ_LEN, HORIZONS)
        if len(X) == 0:
            continue

        n_val = max(1, int(len(X) * VAL_FRAC))
        train_X_raw.append(X[:-n_val])
        train_y.append(y[:-n_val])
        val_X_raw.append(X[-n_val:])
        val_y.append(y[-n_val:])
        logger.info("  Patient %s: %d train + %d val sequences", pid, len(X)-n_val, n_val)

    if not train_X_raw:
        return None, None, None, None, None

    train_X_raw = np.concatenate(train_X_raw, axis=0)
    train_y     = np.concatenate(train_y, axis=0)
    val_X_raw   = np.concatenate(val_X_raw, axis=0)
    val_y       = np.concatenate(val_y, axis=0)

    # Fit scaler on training sequences only
    scaler = StandardScaler()
    flat = train_X_raw.reshape(-1, N_FEATURES)
    scaler.fit(flat)

    train_X = scaler.transform(flat).reshape(train_X_raw.shape).astype(np.float32)
    val_X   = scaler.transform(val_X_raw.reshape(-1, N_FEATURES)).reshape(val_X_raw.shape).astype(np.float32)

    return train_X, train_y, val_X, val_y, scaler


def train(model, train_loader, val_X, val_y, device):
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", patience=5, factor=0.5, min_lr=1e-6
    )

    best_mae = float("inf")
    best_state = None
    patience_count = 0
    history = []

    val_X_t = torch.from_numpy(val_X).to(device)
    val_y_np = val_y

    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        train_losses = []
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            pred = model(xb)
            loss = clinical_penalty_loss(pred, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_losses.append(loss.item())

        model.eval()
        with torch.no_grad():
            chunks = []
            for i in range(0, len(val_X_t), 512):
                chunks.append(model(val_X_t[i:i+512]).cpu().numpy())
            val_pred = np.concatenate(chunks, axis=0)

        val_mae = float(np.mean(np.abs(val_pred[:, 0] - val_y_np[:, 0])))
        train_loss = float(np.mean(train_losses))
        scheduler.step(val_mae)

        history.append({"epoch": epoch, "train_loss": train_loss, "val_mae_30": val_mae})
        logger.info("Epoch %3d | train_loss=%.3f | val_MAE_30=%.2f", epoch, train_loss, val_mae)

        if val_mae < best_mae - 0.05:
            best_mae = val_mae
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_count = 0
        else:
            patience_count += 1
            if patience_count >= PATIENCE:
                logger.info("Early stop at epoch %d, best val MAE=%.2f", epoch, best_mae)
                break

    model.load_state_dict(best_state)
    logger.info("Best val MAE (30 min): %.2f mg/dL", best_mae)
    return model, pd.DataFrame(history)


def plot_curve(history, out_path):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(history["epoch"], history["val_mae_30"], "o-", color="#2ecc71",
            lw=2, ms=4, label="Val MAE (30 min)")
    ax.plot(history["epoch"], history["train_loss"], "-", color="#95a5a6",
            lw=1, label="Train loss")
    ax.set_xlabel("Epoch"); ax.set_ylabel("Loss / MAE (mg/dL)")
    ax.set_title("Ohio-only training curve", fontweight="bold")
    ax.legend(); ax.spines[["top","right"]].set_visible(False); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(out_path, dpi=150, bbox_inches="tight"); plt.close(fig)


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Device: %s", device)

    train_files = (
        sorted((OHIO_DIR / "2018" / "train").glob("*.xml")) +
        sorted((OHIO_DIR / "2020" / "train").glob("*.xml"))
    )
    logger.info("Building dataset from %d training patients…", len(train_files))
    train_X, train_y, val_X, val_y, scaler = build_ohio_sequences(train_files)

    if train_X is None:
        logger.error("No data built."); return

    logger.info("Train: %d  Val: %d  Features: %d", len(train_X), len(val_X), N_FEATURES)

    # Log Ohio vs sim distribution shift
    ohio_mean = train_X[:, :, 0].mean() * scaler.scale_[0] + scaler.mean_[0]
    logger.info("Ohio training CGM mean (approx): %.1f mg/dL", ohio_mean)

    config = Config()
    model = GlucosePredictor(
        input_size=N_FEATURES,
        model_type=config.model_type,
        hidden_size=config.hidden_size,
        num_layers=config.num_layers,
        num_horizons=4,
        dropout=config.dropout,
        use_pinn=False,
    ).to(device)

    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info("Model parameters: %d", n_params)

    ds = TensorDataset(torch.from_numpy(train_X), torch.from_numpy(train_y))
    loader = DataLoader(ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)

    model, history = train(model, loader, val_X, val_y, device)
    plot_curve(history, OUT_DIR / "training_curve.png")

    # Save checkpoint
    torch.save({
        "model_state_dict": model.state_dict(),
        "config": config,
        "scaler": pickle.dumps(scaler),
        "feature_names": FEATURE_NAMES,
        "metrics": {"val_mae": float(history["val_mae_30"].min()),
                    "epochs": len(history)},
    }, CHECKPOINT_OUT)
    logger.info("Saved checkpoint → %s", CHECKPOINT_OUT)

    # Evaluate on test split
    test_files = (
        sorted((OHIO_DIR / "2018" / "test").glob("*.xml")) +
        sorted((OHIO_DIR / "2020" / "test").glob("*.xml"))
    )
    logger.info("Evaluating on %d test patients…", len(test_files))

    model.eval()
    all_preds, all_targets, patient_results, patient_data = [], [], [], {}

    for xml_path in sorted(test_files):
        pid = xml_path.stem.split("-")[0]
        year = xml_path.parts[-3]
        df = parse_ohio_xml(xml_path)
        if df.empty or len(df) < SEQ_LEN + max(HORIZONS) + 10:
            logger.warning("  Skipped %s", pid); continue

        preds, targets = run_inference_with_scaler(df, model, scaler, device)
        if len(preds) == 0:
            logger.warning("  No sequences for %s", pid); continue

        logger.info("  %s | seqs=%d | RMSE_30=%.1f | MAE_30=%.1f",
                    pid, len(preds), rmse(targets[:,0], preds[:,0]), mae(targets[:,0], preds[:,0]))

        all_preds.append(preds); all_targets.append(targets)
        patient_data[f"{pid}({year})"] = (preds, targets)

        row = {"patient_id": pid, "year": year, "n_sequences": len(preds)}
        for j, h in enumerate([30, 60, 90, 120]):
            p, t = preds[:, j], targets[:, j]
            zones = ega_zones(t, p)
            row[f"RMSE_{h}min"] = round(rmse(t, p), 2)
            row[f"MAE_{h}min"]  = round(mae(t, p), 2)
            row[f"EGA_A_{h}min"] = round(zones["A"], 1)
        patient_results.append(row)

    all_preds   = np.concatenate(all_preds, axis=0)
    all_targets = np.concatenate(all_targets, axis=0)

    metric_rows = []
    for j, h in enumerate([30, 60, 90, 120]):
        p, t = all_preds[:, j], all_targets[:, j]
        zones = ega_zones(t, p)
        ta, tp = tir_metrics(t), tir_metrics(p)
        metric_rows.append({
            "horizon_min": h,
            "RMSE_mg_dL": round(rmse(t, p), 2),
            "MAE_mg_dL":  round(mae(t, p), 2),
            "R2":         round(r2_score(t, p), 4),
            "MARD_%":     round(mard(t, p), 2),
            "TIR_actual_%": round(ta["tir"], 1),
            "TIR_pred_%":   round(tp["tir"], 1),
            "EGA_A_%": round(zones["A"], 1),
            "EGA_B_%": round(zones["B"], 1),
            "EGA_C_%": round(zones["C"], 1),
            "EGA_D_%": round(zones["D"], 1),
        })

    metrics_df    = pd.DataFrame(metric_rows)
    per_patient_df = pd.DataFrame(patient_results)
    metrics_df.to_csv(OUT_DIR / "metrics_ohio_scratch.csv", index=False)
    per_patient_df.to_csv(OUT_DIR / "per_patient_ohio_scratch.csv", index=False)

    print("\n=== Ohio-only (scratch) results ===")
    print(metrics_df.to_string(index=False))

    print("\n=== Comparison at 30 min ===")
    sim_r  = (10.94, 4.99, 99.4)
    zs_r   = (78.47, 59.14, 58.4)
    ft_r   = (30.44, 22.15, 85.8)
    sc_r   = tuple(float(metrics_df.loc[metrics_df["horizon_min"]==30, c].values[0])
                   for c in ["RMSE_mg_dL","MAE_mg_dL","EGA_A_%"])
    print(f"  {'Method':<22} {'RMSE':>8} {'MAE':>8} {'Clarke A%':>10}")
    print(f"  {'In-silico':<22} {sim_r[0]:>8.1f} {sim_r[1]:>8.1f} {sim_r[2]:>9.1f}%")
    print(f"  {'Zero-shot':<22} {zs_r[0]:>8.1f} {zs_r[1]:>8.1f} {zs_r[2]:>9.1f}%")
    print(f"  {'Sim → fine-tuned':<22} {ft_r[0]:>8.1f} {ft_r[1]:>8.1f} {ft_r[2]:>9.1f}%")
    print(f"  {'Ohio-only (scratch)':<22} {sc_r[0]:>8.1f} {sc_r[1]:>8.1f} {sc_r[2]:>9.1f}%")

    plot_clarke(all_targets[:,0], all_preds[:,0], 30,  OUT_DIR / "clarke_scratch_30min.png")
    plot_scatter_grid(all_preds, all_targets,           OUT_DIR / "scatter_scratch.png")
    plot_error_hist(all_preds, all_targets,             OUT_DIR / "error_hist_scratch.png")
    plot_tir_bars(all_preds, all_targets,               OUT_DIR / "tir_bars_scratch.png")
    plot_traces(patient_data,                           OUT_DIR / "traces_scratch.png")

    logger.info("Done — results in %s", OUT_DIR)


if __name__ == "__main__":
    main()
