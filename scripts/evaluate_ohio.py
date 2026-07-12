"""
Zero-shot evaluation of the trained GlucoseTransformer on the OhioT1DM dataset.

Uses the test splits from both 2018 and 2020 cohorts (12 patients total).
Model was trained purely on UVA/Padova ODE simulation — no fine-tuning.

Outputs:
  results/ohio/metrics_ohio.csv          — per-horizon aggregate metrics
  results/ohio/per_patient_ohio.csv      — per-patient breakdown
  results/ohio/clarke_ohio_30min.png
  results/ohio/clarke_ohio_60min.png
  results/ohio/scatter_ohio.png
  results/ohio/error_hist_ohio.png
  results/ohio/tir_bars_ohio.png
  results/ohio/traces_ohio.png
  results/ohio/sim_vs_ohio_comparison.png
"""

import sys
import pickle
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.stats import norm
from sklearn.metrics import r2_score

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.data.ode_features import build_features, make_sequences, FEATURE_NAMES, N_FEATURES
from src.models.glucose_predictor import GlucosePredictor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CHECKPOINT = ROOT / "checkpoints/best_model.pt"
OHIO_DIR   = ROOT / "OhioT1DM"
OUT_DIR    = ROOT / "results/ohio"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HORIZONS   = [6, 12, 18, 24]   # steps × 5 min = 30/60/90/120 min
SEQ_LEN    = 24
MAX_GAP    = 3                  # allow up to 3 consecutive missing CGM steps (15 min)

GRAY   = "#555555"
BLUES  = ["#1a6bb5", "#3499d9", "#62b8f0", "#9dd5f7"]
GREEN  = "#2ecc71"
ORANGE = "#e67e22"
RED    = "#e74c3c"


# ─────────────────────────────────────────────────────────────────────────────
# 1. Model loading
# ─────────────────────────────────────────────────────────────────────────────

def load_model(device):
    @dataclass
    class TrainingConfig:
        batch_size: int = 32
        learning_rate: float = 1e-3
        weight_decay: float = 0.01
        epochs: int = 100
        early_stopping_patience: int = 15
        val_split: float = 0.2
        gradient_clip: float = 1.0
        model_type: str = "transformer"
        hidden_size: int = 128
        num_layers: int = 4
        num_heads: int = 8
        dropout: float = 0.1
        use_pinn: bool = True
        pinn_lambda: float = 0.1
        checkpoint_dir: str = "./checkpoints"

    import __main__
    __main__.TrainingConfig = TrainingConfig

    ckpt = torch.load(CHECKPOINT, map_location=device, weights_only=False)
    config = ckpt["config"]

    model = GlucosePredictor(
        input_size=N_FEATURES,
        model_type=getattr(config, "model_type", "transformer"),
        hidden_size=getattr(config, "hidden_size", 128),
        num_layers=getattr(config, "num_layers", 4),
        num_horizons=4,
        dropout=getattr(config, "dropout", 0.1),
        use_pinn=False,
    ).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    scaler_bytes = ckpt.get("scaler")
    if scaler_bytes is None:
        raise RuntimeError("No scaler in checkpoint.")
    scaler = pickle.loads(scaler_bytes)

    logger.info("Model loaded — val MAE: %.2f mg/dL", ckpt.get("metrics", {}).get("val_mae", float("nan")))
    return model, scaler


# ─────────────────────────────────────────────────────────────────────────────
# 2. XML → DataFrame
# ─────────────────────────────────────────────────────────────────────────────

def _ts(s: str) -> pd.Timestamp:
    for fmt in ("%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M"):
        try:
            return pd.Timestamp(pd.to_datetime(s, format=fmt))
        except Exception:
            pass
    return pd.NaT


def parse_ohio_xml(xml_path: Path) -> pd.DataFrame:
    """Parse one OhioT1DM XML file → 5-min-grid DataFrame."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    weight_kg = float(root.get("weight", 75))

    # ── CGM ──────────────────────────────────────────────────────────────────
    cgm_rows = []
    gl = root.find("glucose_level")
    for ev in (gl if gl is not None else []):
        t = _ts(ev.get("ts", ""))
        v = ev.get("value")
        if t is not pd.NaT and v:
            cgm_rows.append({"ts": t, "cgm": float(v)})
    if not cgm_rows:
        return pd.DataFrame()

    cgm_df = pd.DataFrame(cgm_rows).set_index("ts").sort_index()
    # Build a clean 5-min grid from first to last CGM reading
    grid = pd.date_range(cgm_df.index[0], cgm_df.index[-1], freq="5min")
    df = pd.DataFrame(index=grid)
    df["cgm_mg_dl"] = np.nan
    df.loc[cgm_df.index.intersection(df.index), "cgm_mg_dl"] = cgm_df["cgm"].reindex(df.index.intersection(cgm_df.index))

    # Forward-fill gaps ≤ MAX_GAP steps; leave longer gaps as NaN
    consec_nan = 0
    cgm_arr = df["cgm_mg_dl"].values.copy()
    for i in range(len(cgm_arr)):
        if np.isnan(cgm_arr[i]):
            consec_nan += 1
            if consec_nan <= MAX_GAP and i > 0:
                cgm_arr[i] = cgm_arr[i - 1]   # forward fill
        else:
            consec_nan = 0
    df["cgm_mg_dl"] = cgm_arr

    # ── Basal ─────────────────────────────────────────────────────────────────
    basal_rows = []
    _basal_el = root.find("basal")
    for ev in (_basal_el if _basal_el is not None else []):
        t = _ts(ev.get("ts", ""))
        v = ev.get("value")
        if t is not pd.NaT and v:
            basal_rows.append({"ts": t, "basal": float(v)})
    if basal_rows:
        bdf = pd.DataFrame(basal_rows).set_index("ts").sort_index()
        df["basal_u_h"] = bdf["basal"].reindex(df.index, method="ffill")
        df["basal_u_h"] = df["basal_u_h"].bfill().fillna(0.7)
    else:
        df["basal_u_h"] = 0.7  # fallback 0.7 U/h

    # ── Bolus ─────────────────────────────────────────────────────────────────
    df["bolus_u"] = 0.0
    _bolus_el = root.find("bolus")
    for ev in (_bolus_el if _bolus_el is not None else []):
        t = _ts(ev.get("ts_begin", ""))
        dose = ev.get("dose")
        if t is not pd.NaT and dose and t in df.index:
            df.loc[t, "bolus_u"] += float(dose)
        elif t is not pd.NaT and dose:
            # snap to nearest grid point within bounds
            idx = df.index.searchsorted(t, side="left")
            if idx < len(df.index):
                df.loc[df.index[idx], "bolus_u"] += float(dose)

    # Convert bolus U (delivered in one step) → U/h equivalent for that step
    df["insulin_u_h"] = df["basal_u_h"] + df["bolus_u"] * 12.0  # 1 step = 5 min = 1/12 h

    # ── Meals ─────────────────────────────────────────────────────────────────
    df["cho_g"] = 0.0
    _meal_el = root.find("meal")
    for ev in (_meal_el if _meal_el is not None else []):
        t = _ts(ev.get("ts", ""))
        carbs = ev.get("carbs")
        if t is not pd.NaT and carbs:
            # snap to nearest grid point
            idx = df.index.searchsorted(t, side="left")
            if idx < len(df.index):
                df.iloc[idx, df.columns.get_loc("cho_g")] += float(carbs)

    # ── Exercise ──────────────────────────────────────────────────────────────
    df["is_exercising"] = 0.0
    df["exercise_intensity"] = 0.0
    df["time_since_exercise"] = 240.0
    df["exercise_minutes_2h"] = 0.0

    exercise_events = []
    _exercise_el = root.find("exercise")
    for ev in (_exercise_el if _exercise_el is not None else []):
        t = _ts(ev.get("ts", ""))
        dur = ev.get("duration")
        intensity = ev.get("intensity", "5")
        if t is not pd.NaT and dur:
            exercise_events.append({
                "start": t,
                "end": t + pd.Timedelta(minutes=float(dur)),
                "intensity": float(intensity) / 10.0,
                "duration": float(dur),
            })

    for ex in exercise_events:
        mask = (df.index >= ex["start"]) & (df.index <= ex["end"])
        df.loc[mask, "is_exercising"] = 1.0
        df.loc[mask, "exercise_intensity"] = ex["intensity"]

    # time_since_exercise
    last_ex_end = pd.NaT
    for i, ts in enumerate(df.index):
        for ex in exercise_events:
            if ex["end"] <= ts and (last_ex_end is pd.NaT or ex["end"] > last_ex_end):
                last_ex_end = ex["end"]
        if last_ex_end is not pd.NaT:
            mins = (ts - last_ex_end).total_seconds() / 60.0
            df.iloc[i, df.columns.get_loc("time_since_exercise")] = min(240.0, max(0.0, mins))

    # ── t_min (relative minutes from start) ───────────────────────────────────
    df["t_min"] = ((df.index - df.index[0]).total_seconds() / 60).astype(float)

    return df.reset_index().rename(columns={"index": "timestamp"})


# ─────────────────────────────────────────────────────────────────────────────
# 3. Inference helpers
# ─────────────────────────────────────────────────────────────────────────────

def run_inference(df: pd.DataFrame, model, scaler, device) -> tuple[np.ndarray, np.ndarray]:
    """
    Build features, make sequences, run model, return (preds, targets).
    Only returns samples where neither input sequence nor target has NaN in CGM.
    """
    # Drop rows with NaN CGM (unbridgeable gaps)
    valid_mask = ~df["cgm_mg_dl"].isna()
    df_clean = df[valid_mask].reset_index(drop=True)

    if len(df_clean) < SEQ_LEN + max(HORIZONS) + 1:
        return np.empty((0, 4)), np.empty((0, 4))

    # Build feature matrix using the same pipeline as training
    feat_df = df_clean[["t_min", "cgm_mg_dl", "insulin_u_h", "cho_g", "basal_u_h"]].copy()

    # Override exercise features — ode_features zeros them, but Ohio has real data
    feat_matrix = build_features(feat_df)

    # Inject real exercise features (columns 31-34: is_exercising, intensity, time_since, min_2h)
    ex_cols = ["is_exercising", "exercise_intensity", "time_since_exercise", "exercise_minutes_2h"]
    for i, col in enumerate(ex_cols):
        if col in df_clean.columns:
            feat_matrix[:, 31 + i] = df_clean[col].values.astype(np.float32)

    glucose = df_clean["cgm_mg_dl"].values.astype(np.float32)
    X, y = make_sequences(feat_matrix, glucose, SEQ_LEN, HORIZONS)

    if len(X) == 0:
        return np.empty((0, 4)), np.empty((0, 4))

    # Scale features (same scaler used during training)
    flat = X.reshape(-1, N_FEATURES)
    X_scaled = scaler.transform(flat).reshape(X.shape).astype(np.float32)

    # Batch inference
    BATCH = 512
    preds = []
    with torch.no_grad():
        for i in range(0, len(X_scaled), BATCH):
            xb = torch.from_numpy(X_scaled[i:i+BATCH]).to(device)
            out = model(xb).cpu().numpy()
            preds.append(out)

    preds = np.concatenate(preds, axis=0)
    return preds, y


# Alias so train_ohio.py can pass a freshly-fit Ohio scaler instead of the sim one
run_inference_with_scaler = run_inference


# ─────────────────────────────────────────────────────────────────────────────
# 4. Metrics
# ─────────────────────────────────────────────────────────────────────────────

def rmse(a, b): return float(np.sqrt(np.mean((a - b) ** 2)))
def mae(a, b):  return float(np.mean(np.abs(a - b)))
def mard(a, b): return float(np.mean(np.abs(a - b) / np.maximum(a, 1)) * 100)

def tir_metrics(g):
    g = np.asarray(g).ravel()
    n = len(g)
    if n == 0:
        return dict(tir=0, tar1=0, tar2=0, tbr1=0, tbr2=0)
    return dict(
        tir  = float(np.mean((g >= 70)  & (g <= 180)) * 100),
        tar1 = float(np.mean((g > 180)  & (g <= 250)) * 100),
        tar2 = float(np.mean(g > 250) * 100),
        tbr1 = float(np.mean((g >= 54)  & (g < 70))  * 100),
        tbr2 = float(np.mean(g < 54) * 100),
    )

def clarke_zone(ref, pred):
    """Return Clarke EGA zone label for a single (ref, pred) pair."""
    r, p = float(ref), float(pred)
    if r < 70 and p < 70:
        return "A"
    if r >= 70 and r <= 180 and p >= 70 and p <= 180:
        return "A"
    if r >= 70 and r <= 290 and abs(p - r) / r <= 0.20:
        return "A"
    if r > 290 and p > 290:
        return "A"
    if r < 70 and p > 70 and p < 180:
        return "B"
    if r > 180 and p > 70 and p < 180:
        return "B"
    if r > 240 and p > 180 and abs(p - r) / r <= 0.20:
        return "B"
    if r < 70 and p > 180:
        return "D"
    if r > 180 and p < 70:
        return "D"
    if r < 70 and p > 180:
        return "E"
    if r > 180 and p < 70:
        return "E"
    return "C"

def ega_zones(refs, preds):
    counts = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
    for r, p in zip(refs, preds):
        counts[clarke_zone(r, p)] += 1
    total = max(1, sum(counts.values()))
    return {k: v / total * 100 for k, v in counts.items()}


# ─────────────────────────────────────────────────────────────────────────────
# 5. Plots
# ─────────────────────────────────────────────────────────────────────────────

def _style():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "figure.dpi": 150,
    })

def plot_clarke(refs, preds, horizon_min, out_path):
    _style()
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.scatter(refs, preds, s=3, alpha=0.25, color=BLUES[0], rasterized=True)

    ax.plot([0, 400], [0, 400], "k-", lw=0.8)
    ax.plot([0, 175], [0, 240], color=GRAY, lw=0.6, ls="--")
    ax.plot([175, 400], [240, 400], color=GRAY, lw=0.6, ls="--")
    ax.plot([0, 70],   [84, 400], color=GRAY, lw=0.6, ls="--")
    ax.plot([70, 400], [0, 400*70/400], color=GRAY, lw=0.6, ls="--")

    zones = ega_zones(refs, preds)
    ax.set_xlim(0, 400); ax.set_ylim(0, 400)
    ax.set_xlabel("Reference glucose (mg/dL)")
    ax.set_ylabel("Predicted glucose (mg/dL)")
    ax.set_title(f"Clarke EGA — {horizon_min}-min horizon (OhioT1DM)\n"
                 f"A={zones['A']:.1f}%  B={zones['B']:.1f}%  C={zones['C']:.1f}%  "
                 f"D={zones['D']:.1f}%  E={zones['E']:.1f}%", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out_path)


def plot_scatter_grid(all_preds, all_targets, out_path):
    _style()
    labels = ["30 min", "60 min", "90 min", "120 min"]
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    for i, (ax, lbl) in enumerate(zip(axes, labels)):
        p = all_preds[:, i]
        t = all_targets[:, i]
        ax.scatter(t, p, s=2, alpha=0.2, color=BLUES[i], rasterized=True)
        lo, hi = min(t.min(), p.min()), max(t.max(), p.max())
        ax.plot([lo, hi], [lo, hi], "k--", lw=0.8)
        r2 = r2_score(t, p)
        ax.set_title(f"{lbl}\nRMSE={rmse(t,p):.1f}  R²={r2:.3f}", fontsize=9)
        ax.set_xlabel("Actual (mg/dL)")
        if i == 0:
            ax.set_ylabel("Predicted (mg/dL)")
    fig.suptitle("OhioT1DM — Zero-shot evaluation", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out_path)


def plot_error_hist(all_preds, all_targets, out_path):
    _style()
    labels = ["30 min", "60 min", "90 min", "120 min"]
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.5))
    for i, (ax, lbl) in enumerate(zip(axes, labels)):
        errs = all_preds[:, i] - all_targets[:, i]
        ax.hist(errs, bins=60, color=BLUES[i], alpha=0.7, density=True)
        mu, sigma = errs.mean(), errs.std()
        x = np.linspace(mu - 4*sigma, mu + 4*sigma, 200)
        ax.plot(x, norm.pdf(x, mu, sigma), "k-", lw=1.2)
        ax.axvline(0, color="red", lw=0.8, ls="--")
        ax.set_title(f"{lbl}\nμ={mu:.1f}  σ={sigma:.1f}", fontsize=9)
        ax.set_xlabel("Error (mg/dL)")
        if i == 0:
            ax.set_ylabel("Density")
    fig.suptitle("Prediction error distribution (OhioT1DM)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out_path)


def plot_tir_bars(all_preds, all_targets, out_path):
    _style()
    labels = ["30 min", "60 min", "90 min", "120 min"]
    fig, axes = plt.subplots(1, 4, figsize=(14, 4))
    zone_colors = ["#e74c3c", "#e67e22", "#2ecc71", "#3498db", "#1a6bb5"]
    zone_labels = ["TBR2\n<54", "TBR1\n54-70", "TIR\n70-180", "TAR1\n180-250", "TAR2\n>250"]

    for i, (ax, lbl) in enumerate(zip(axes, labels)):
        a = tir_metrics(all_targets[:, i])
        p = tir_metrics(all_preds[:, i])

        actual_vals = [a["tbr2"], a["tbr1"], a["tir"], a["tar1"], a["tar2"]]
        pred_vals   = [p["tbr2"], p["tbr1"], p["tir"], p["tar1"], p["tar2"]]

        x = np.arange(5)
        width = 0.35
        bars_a = ax.bar(x - width/2, actual_vals, width, label="Actual", color=zone_colors, alpha=0.9)
        bars_p = ax.bar(x + width/2, pred_vals,   width, label="Predicted", color=zone_colors, alpha=0.4, hatch="//")

        ax.set_xticks(x)
        ax.set_xticklabels(zone_labels, fontsize=7)
        ax.set_ylim(0, 100)
        ax.set_title(lbl, fontsize=9)
        if i == 0:
            ax.set_ylabel("% time")
            ax.legend(fontsize=7)

    fig.suptitle("TIR zones: actual vs predicted (OhioT1DM)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out_path)


def plot_traces(patient_data, out_path, n_patients=6):
    """Show ~4h prediction traces for a sample of patients."""
    _style()
    n = min(n_patients, len(patient_data))
    fig, axes = plt.subplots(n, 1, figsize=(14, 2.8 * n), sharex=False)
    if n == 1:
        axes = [axes]

    for ax, (pid, (preds, targets)) in zip(axes, list(patient_data.items())[:n]):
        n_pts = min(500, len(targets))
        t = np.arange(n_pts) * 5  # minutes
        ax.plot(t, targets[:n_pts, 0], "k-", lw=1.2, label="Actual CGM")
        for j, (lbl, color) in enumerate(zip(["30min", "60min", "90min", "120min"], BLUES)):
            ax.plot(t, preds[:n_pts, j], "-", color=color, lw=0.8, alpha=0.8, label=lbl)
        ax.axhspan(70, 180, alpha=0.07, color=GREEN)
        ax.axhline(70, color=ORANGE, lw=0.5, ls="--")
        ax.axhline(180, color=RED, lw=0.5, ls="--")
        ax.set_ylabel("Glucose (mg/dL)")
        ax.set_title(f"Patient {pid}", fontsize=9)
        ax.set_ylim(30, 380)
        if ax == axes[0]:
            ax.legend(ncol=5, fontsize=7, loc="upper right")
        ax.set_xlabel("Time (min)")

    fig.suptitle("OhioT1DM — Sample prediction traces (zero-shot)", fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out_path)


def plot_sim_vs_ohio(sim_metrics_path, ohio_metrics_path, out_path):
    """Side-by-side comparison of in-silico vs real-world performance."""
    _style()
    sim = pd.read_csv(sim_metrics_path)
    ohio = pd.read_csv(ohio_metrics_path)

    metrics_to_plot = ["RMSE_mg_dL", "MAE_mg_dL", "EGA_A_%"]
    titles = ["RMSE (mg/dL)", "MAE (mg/dL)", "Clarke A zone (%)"]
    horizons = [30, 60, 90, 120]

    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    x = np.arange(4)
    width = 0.35

    for ax, col, title in zip(axes, metrics_to_plot, titles):
        s_vals = sim[col].values if col in sim.columns else np.zeros(4)
        o_vals = ohio[col].values if col in ohio.columns else np.zeros(4)
        ax.bar(x - width/2, s_vals, width, label="In-silico (ODE)", color=BLUES[0], alpha=0.85)
        ax.bar(x + width/2, o_vals, width, label="OhioT1DM (real)", color=ORANGE, alpha=0.85)
        ax.set_xticks(x)
        ax.set_xticklabels([f"{h}min" for h in horizons])
        ax.set_title(title)
        ax.legend(fontsize=8)

    fig.suptitle("In-silico vs Real-world performance", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", out_path)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Device: %s", device)

    model, scaler = load_model(device)

    # Collect test XML files from both cohorts
    test_files = (
        list((OHIO_DIR / "2018" / "test").glob("*.xml")) +
        list((OHIO_DIR / "2020" / "test").glob("*.xml"))
    )
    logger.info("Found %d test patients", len(test_files))

    all_preds   = []
    all_targets = []
    patient_results = []
    patient_data = {}   # pid → (preds, targets) for trace plot

    for xml_path in sorted(test_files):
        pid = xml_path.stem.split("-")[0]
        year = xml_path.parts[-3]
        logger.info("Processing patient %s (%s)…", pid, year)

        df = parse_ohio_xml(xml_path)
        if df.empty or len(df) < SEQ_LEN + max(HORIZONS) + 10:
            logger.warning("  Skipped — insufficient data")
            continue

        preds, targets = run_inference(df, model, scaler, device)
        if len(preds) == 0:
            logger.warning("  No valid sequences for patient %s", pid)
            continue

        logger.info("  Sequences: %d | 30-min RMSE=%.1f MAE=%.1f",
                    len(preds), rmse(targets[:, 0], preds[:, 0]), mae(targets[:, 0], preds[:, 0]))

        all_preds.append(preds)
        all_targets.append(targets)
        patient_data[f"{pid}({year})"] = (preds, targets)

        # Per-patient metrics
        row = {"patient_id": pid, "year": year, "n_sequences": len(preds)}
        for j, h in enumerate([30, 60, 90, 120]):
            p, t = preds[:, j], targets[:, j]
            zones = ega_zones(t, p)
            row[f"RMSE_{h}min"] = round(rmse(t, p), 2)
            row[f"MAE_{h}min"]  = round(mae(t, p), 2)
            row[f"EGA_A_{h}min"] = round(zones["A"], 1)
        patient_results.append(row)

    if not all_preds:
        logger.error("No patient data processed — check XML paths.")
        return

    all_preds   = np.concatenate(all_preds,   axis=0)
    all_targets = np.concatenate(all_targets, axis=0)
    logger.info("Total sequences: %d", len(all_preds))

    # ── Aggregate metrics ─────────────────────────────────────────────────────
    metric_rows = []
    for j, h in enumerate([30, 60, 90, 120]):
        p, t = all_preds[:, j], all_targets[:, j]
        zones = ega_zones(t, p)
        ta = tir_metrics(t)
        tp = tir_metrics(p)
        metric_rows.append({
            "horizon_min": h,
            "RMSE_mg_dL": round(rmse(t, p), 2),
            "MAE_mg_dL":  round(mae(t, p), 2),
            "R2":         round(r2_score(t, p), 4),
            "MARD_%":     round(mard(t, p), 2),
            "TIR_actual_%": round(ta["tir"], 1),
            "TIR_pred_%":   round(tp["tir"], 1),
            "TAR_actual_%": round(ta["tar1"] + ta["tar2"], 1),
            "TAR_pred_%":   round(tp["tar1"] + tp["tar2"], 1),
            "TBR_actual_%": round(ta["tbr1"] + ta["tbr2"], 1),
            "TBR_pred_%":   round(tp["tbr1"] + tp["tbr2"], 1),
            "EGA_A_%": round(zones["A"], 1),
            "EGA_B_%": round(zones["B"], 1),
            "EGA_C_%": round(zones["C"], 1),
            "EGA_D_%": round(zones["D"], 1),
        })

    metrics_df = pd.DataFrame(metric_rows)
    per_patient_df = pd.DataFrame(patient_results)

    metrics_df.to_csv(OUT_DIR / "metrics_ohio.csv", index=False)
    per_patient_df.to_csv(OUT_DIR / "per_patient_ohio.csv", index=False)
    logger.info("Metrics saved.")
    print("\n" + metrics_df.to_string(index=False))

    # ── Plots ─────────────────────────────────────────────────────────────────
    plot_clarke(all_targets[:, 0], all_preds[:, 0], 30,  OUT_DIR / "clarke_ohio_30min.png")
    plot_clarke(all_targets[:, 1], all_preds[:, 1], 60,  OUT_DIR / "clarke_ohio_60min.png")
    plot_scatter_grid(all_preds, all_targets,             OUT_DIR / "scatter_ohio.png")
    plot_error_hist(all_preds, all_targets,               OUT_DIR / "error_hist_ohio.png")
    plot_tir_bars(all_preds, all_targets,                 OUT_DIR / "tir_bars_ohio.png")
    plot_traces(patient_data,                             OUT_DIR / "traces_ohio.png")

    sim_metrics = ROOT / "results/metrics.csv"
    if sim_metrics.exists():
        plot_sim_vs_ohio(sim_metrics, OUT_DIR / "metrics_ohio.csv",
                         OUT_DIR / "sim_vs_ohio_comparison.png")

    logger.info("Done — results in %s", OUT_DIR)


if __name__ == "__main__":
    main()
