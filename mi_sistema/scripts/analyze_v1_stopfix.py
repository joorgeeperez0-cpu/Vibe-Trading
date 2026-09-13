"""
Comparativa v1 (referencia archivada) vs v1_stopfix sobre los artefactos del
engine de Vibe-Trading. Genera:
    mi_sistema/results/v1_stopfix/comparison.md
    mi_sistema/results/v1_stopfix/comparison_summary.csv
    mi_sistema/results/v1_stopfix/comparison_yearly.csv

Uso: python mi_sistema/scripts/analyze_v1_stopfix.py
"""

from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "mi_sistema" / "results"
OUT = RES / "v1_stopfix"

RUNS = {
    ("v1", "IS"): RES / "v15_cripto_top7_in_sample" / "artifacts",
    ("v1", "WF"): RES / "v15_cripto_top7_walkforward" / "artifacts",
    ("stopfix", "IS"): OUT / "is_2018_2022" / "artifacts",
    ("stopfix", "WF"): OUT / "wf_2023_2026" / "artifacts",
}
BARS_PER_YEAR = 365
INITIAL = 1000.0
GATES = {"sharpe": (">=", 1.0), "calmar": (">=", 0.5), "mdd_pct": ("<=", 20.0), "profit_factor": (">=", 1.5)}


def _closed_trades(artifacts: Path) -> pd.DataFrame:
    """Filas de salida de trades.csv (la fila de entrada y la de salida van consecutivas)."""
    t = pd.read_csv(artifacts / "trades.csv")
    exits = t.iloc[1::2].copy()
    entries = t.iloc[0::2].reset_index(drop=True)
    exits = exits.reset_index(drop=True)
    assert (entries["code"] == exits["code"]).all(), "trades.csv no alterna entrada/salida"
    exits["entry_date"] = pd.to_datetime(entries["timestamp"])
    exits["exit_date"] = pd.to_datetime(exits["timestamp"])
    return exits


def _pf(pnl: pd.Series) -> float:
    gains, losses = pnl[pnl > 0].sum(), -pnl[pnl < 0].sum()
    return float(gains / losses) if losses > 0 else float("inf")


def _summary(artifacts: Path) -> dict:
    m = pd.read_csv(artifacts / "metrics.csv").iloc[0]
    tr = _closed_trades(artifacts)
    wins, losses = tr.loc[tr.pnl > 0, "pnl"], tr.loc[tr.pnl < 0, "pnl"]
    return {
        "sharpe": float(m.sharpe),
        "calmar": float(m.calmar),
        "mdd_pct": abs(float(m.max_drawdown)) * 100,
        "profit_factor": float(m.profit_factor),
        "trades": int(m.trade_count),
        "annual_return_pct": float(m.annual_return) * 100,
        "total_return_pct": float(m.total_return) * 100,
        "win_rate_pct": len(wins) / len(tr) * 100,
        "avg_win": float(wins.mean()),
        "avg_loss": float(-losses.mean()),
        "win_loss_ratio": float(wins.mean() / -losses.mean()),
        "avg_days_in_position": float(tr.holding_days.mean()),
        "max_consecutive_loss": int(m.max_consecutive_loss),
    }


def _yearly(artifacts: Path) -> pd.DataFrame:
    eq = pd.read_csv(artifacts / "equity.csv", index_col=0, parse_dates=True)["equity"]
    tr = _closed_trades(artifacts)
    rows = []
    prev_end = INITIAL
    for year, e in eq.groupby(eq.index.year):
        base = pd.concat([pd.Series([prev_end]), e.reset_index(drop=True)])
        rets = base.pct_change().dropna()
        peak = base.cummax()
        mdd = float(((base - peak) / peak).min())
        yt = tr[tr.exit_date.dt.year == year]
        rows.append({
            "year": int(year) if year < eq.index[-1].year or e.index[-1].month == 12 else f"{year} (hasta {e.index[-1].date()})",
            "return_pct": (float(e.iloc[-1]) / prev_end - 1) * 100,
            "sharpe": float(rets.mean() / (rets.std() + 1e-10) * np.sqrt(BARS_PER_YEAR)),
            "mdd_pct": abs(mdd) * 100,
            "trades": len(yt),
            "win_rate_pct": (yt.pnl > 0).mean() * 100 if len(yt) else float("nan"),
            "profit_factor": _pf(yt.pnl) if len(yt) else float("nan"),
        })
        prev_end = float(e.iloc[-1])
    return pd.DataFrame(rows)


def _gates(s: dict) -> tuple[int, list]:
    ok, detail = 0, []
    for k, (op, thr) in GATES.items():
        passed = s[k] >= thr if op == ">=" else s[k] <= thr
        ok += passed
        detail.append(f"{k} {s[k]:.2f} {op} {thr} {'OK' if passed else 'FALLA'}")
    return ok, detail


def main() -> int:
    summ = {key: _summary(p) for key, p in RUNS.items()}
    df = pd.DataFrame(summ).T
    df.index = [f"{a} {b}" for a, b in df.index]
    df.to_csv(OUT / "comparison_summary.csv", float_format="%.4f")

    v1, sf, sf_is = summ[("v1", "WF")], summ[("stopfix", "WF")], summ[("stopfix", "IS")]
    better = {
        "sharpe": sf["sharpe"] >= v1["sharpe"],
        "calmar": sf["calmar"] >= v1["calmar"],
        "mdd_pct": sf["mdd_pct"] <= v1["mdd_pct"],
        "profit_factor": sf["profit_factor"] >= v1["profit_factor"],
    }

    lines = ["# v1 vs v1_stopfix", "", "Mismos OHLCV archivados, mismo CryptoEngine, mismas configs. v1 = artefactos archivados (reproducidos al decimal con el harness local).", ""]
    lines += ["## Walk-forward 2023-01-01 a 2026-04-29 + in-sample stopfix", "",
              "| Métrica | v1 IS | v1 WF (ref) | stopfix IS | stopfix WF | Delta WF |", "|---|---|---|---|---|---|"]
    fmt = [("sharpe", "Sharpe", "{:.2f}"), ("calmar", "Calmar", "{:.2f}"), ("mdd_pct", "MDD %", "{:.1f}"),
           ("profit_factor", "PF", "{:.2f}"), ("trades", "# Trades", "{:.0f}"), ("annual_return_pct", "Retorno anual %", "{:.1f}"),
           ("win_rate_pct", "Win rate %", "{:.1f}"), ("avg_win", "Ganancia media €", "{:.2f}"), ("avg_loss", "Pérdida media €", "{:.2f}"),
           ("win_loss_ratio", "Ganancia/pérdida media", "{:.2f}"), ("avg_days_in_position", "Días medios en posición", "{:.1f}"),
           ("max_consecutive_loss", "Máx. pérdidas seguidas", "{:.0f}")]
    v1_is = summ[("v1", "IS")]
    for k, name, f in fmt:
        delta = sf[k] - v1[k]
        lines.append(f"| {name} | {f.format(v1_is[k])} | {f.format(v1[k])} | {f.format(sf_is[k])} | {f.format(sf[k])} | {delta:+.2f} |")

    yearly = []
    for eng in ("v1", "stopfix"):
        y = _yearly(RUNS[(eng, "WF")])
        y.insert(0, "engine", eng)
        yearly.append(y)
    ydf = pd.concat(yearly)
    ydf.to_csv(OUT / "comparison_yearly.csv", index=False, float_format="%.4f")

    lines += ["", "## Año a año (walk-forward)", "",
              "| Año | Retorno % v1 | Retorno % sf | Sharpe v1 | Sharpe sf | MDD % v1 | MDD % sf | PF v1 | PF sf | Trades v1 | Trades sf |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    a, b = yearly[0].reset_index(drop=True), yearly[1].reset_index(drop=True)
    for i in range(len(a)):
        lines.append(f"| {a.year[i]} | {a.return_pct[i]:.1f} | {b.return_pct[i]:.1f} | {a.sharpe[i]:.2f} | {b.sharpe[i]:.2f} | "
                     f"{a.mdd_pct[i]:.1f} | {b.mdd_pct[i]:.1f} | {a.profit_factor[i]:.2f} | {b.profit_factor[i]:.2f} | {a.trades[i]} | {b.trades[i]} |")

    ok_wf, det_wf = _gates(sf)
    ok_is, det_is = _gates(sf_is)
    n_better = sum(better.values())
    lines += ["", "## Gates", "", f"stopfix WF: {ok_wf}/4 -> " + "; ".join(det_wf), "",
              f"stopfix IS: {ok_is}/4 -> " + "; ".join(det_is), "",
              f"stopfix WF >= v1 WF en {n_better}/4 métricas: " + ", ".join(f"{k} {'sí' if v else 'no'}" for k, v in better.items())]
    if ok_wf == 4 and n_better >= 3:
        verdict = "CANDIDATO A SUSTITUCIÓN (pasa 4 gates y >= v1 en al menos 3/4 métricas WF)"
    elif ok_wf == 4:
        verdict = "EXPERIMENTO (pasa gates pero peor que v1 en 2+ métricas WF)"
    else:
        verdict = "DESCARTAR (no pasa gates)"
    lines += ["", f"**Regla automática:** {verdict}", ""]

    (OUT / "comparison.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
