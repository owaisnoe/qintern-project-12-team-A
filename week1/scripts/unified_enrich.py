#!/usr/bin/env python3
"""
Enriched unified schema **v1.1** — AK (@Thedaemon-AK) · Day-6 additive proposal.

Iwo's unified v1.0 (`unified_schema.py`, 17 features) is a clean common-flow core, but its
down-map sets 5/15 numerics to NaN for TON_IoT and 10/15 for Edge-IIoTset, so those two
datasets' **zero-day splits collapse to 1–2 rows** after feature-space + cross-split dedup
(`qadcp.py --unified` S7b). This script proposes a **richer, NetFlow-v2-aligned schema**
(Sarhan/Layeghy/Portmann standardized UNSW-NB15/BoT-IoT/ToN-IoT to a common **43-feature**
NetFlow set) that restores the discriminative fields the 17-schema discards — `service`,
directional `*_ip_bytes`, `missed_bytes`, app-layer byte counts, TCP seq/ack, dst port, TTL,
DNS activity — so TON/Edge ransomware/fingerprinting flows stay distinct and survive the holdout.

It is **fully additive**: it does NOT touch Iwo's frozen v1.0. It reuses the *verified*
`qadcp.process_dataframe` (split → S7b dedup → train-fit encode/impute/scale → angle [0,π] →
gates) via three local monkeypatches (4 categoricals, matching encoder, enriched column order)
and writes a parallel package to `datasets/<name>/unified_v1_1/qadcp/`. Leakage-safe by
construction (all fits are on the train split, inside `process_dataframe`).

Run inside the venv, after `unified_schema.py`/`qadcp.py --unified` exist:
    python week1/scripts/unified_enrich.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import qadcp
import _unified
from _unified import PROJECTORS

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "datasets"
GEN = BASE / "week1" / "reports" / "_generated"
SCHEMA_V2 = BASE / "week1" / "schema" / "unified_schema_v2.json"

# 11 enriched numerics + 2 enriched categoricals, on top of Iwo's 15 num + 2 cat.
ENRICH_NUM = ["src_ip_bytes", "dst_ip_bytes", "missed_bytes", "app_req_bytes", "app_resp_bytes",
              "tcp_seq", "tcp_ack", "dstport", "ttl_total", "dns_signal", "flag_count"]
ENRICH_CAT = ["service_cat", "app_proto_cat"]
ALL_CAT = _unified.CAT_COLS + ENRICH_CAT                       # 4 string cats
# encoded numeric column produced per categorical
CAT_PAIRS = [("protocol_cat", "protocol"), ("conn_state_cat", "conn_state"),
             ("service_cat", "service"), ("app_proto_cat", "app_proto")]
FEATURE_ORDER = _unified.NUM_COLS + ENRICH_NUM + [enc for _, enc in CAT_PAIRS]  # 30 features


def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def _g(df, col, default=np.nan):
    return df[col].astype("float64") if col in df.columns else pd.Series(default, index=df.index, dtype="float64")


def _svc_from_flags(df, mapping):
    out = pd.Series("other", index=df.index, dtype=object)
    for col, name in mapping:                                  # last hit wins → priority order
        if col in df.columns:
            out = out.where(df[col] <= 0, other=name)
    return out


# --- enriched extra columns per dataset (fill what the checkpoint has; NaN/"other" otherwise) ---
def _enrich_ton(df):
    dns = _g(df, "dns_qtype").fillna(0) + _g(df, "dns_rcode").fillna(0) + _g(df, "dns_AA").fillna(0)
    svc = df["service"].astype(str) if "service" in df.columns else pd.Series("other", index=df.index)
    app = np.where(_g(df, "dns_qtype").fillna(0) > 0, "dns",
          np.where(_g(df, "http_status_code").fillna(0) > 0, "http", svc.astype(str)))
    return pd.DataFrame({
        "src_ip_bytes": _g(df, "src_ip_bytes"), "dst_ip_bytes": _g(df, "dst_ip_bytes"),
        "missed_bytes": _g(df, "missed_bytes"),
        "app_req_bytes": _g(df, "http_request_body_len"), "app_resp_bytes": _g(df, "http_response_body_len"),
        "tcp_seq": np.nan, "tcp_ack": np.nan, "dstport": np.nan, "ttl_total": np.nan,
        "dns_signal": dns, "flag_count": np.nan,
        "service_cat": svc, "app_proto_cat": pd.Series(app, index=df.index),
    }, index=df.index)


def _enrich_edge(df):
    dstport = _g(df, "tcp.dstport")
    dstport = dstport.where(dstport > 0, _g(df, "udp.port"))
    svc = _svc_from_flags(df, [("arp.opcode", "arp"), ("icmp.checksum", "icmp"), ("udp.port", "udp"),
                               ("tcp.len", "tcp"), ("dns.qry.name.len", "dns"),
                               ("http.content_length", "http"), ("mqtt.protoname", "mqtt")])
    return pd.DataFrame({
        "src_ip_bytes": np.nan, "dst_ip_bytes": np.nan, "missed_bytes": np.nan,
        "app_req_bytes": _g(df, "http.content_length"), "app_resp_bytes": _g(df, "http.response"),
        "tcp_seq": _g(df, "tcp.seq"), "tcp_ack": _g(df, "tcp.ack"), "dstport": dstport,
        "ttl_total": np.nan, "dns_signal": _g(df, "dns.qry.name.len"), "flag_count": _g(df, "tcp.flags"),
        "service_cat": svc, "app_proto_cat": svc,
    }, index=df.index)


def _enrich_cic(df):
    flags = ["syn_count", "ack_count", "fin_count", "rst_count", "urg_count"]
    svc = _svc_from_flags(df, [("SSH", "ssh"), ("DNS", "dns"), ("HTTP", "http"), ("HTTPS", "https")])
    return pd.DataFrame({
        "src_ip_bytes": np.nan, "dst_ip_bytes": np.nan, "missed_bytes": np.nan,
        "app_req_bytes": np.nan, "app_resp_bytes": np.nan, "tcp_seq": np.nan, "tcp_ack": np.nan,
        "dstport": np.nan, "ttl_total": _g(df, "Header_Length"), "dns_signal": _g(df, "DNS"),
        "flag_count": sum((_g(df, c).fillna(0) for c in flags), start=pd.Series(0.0, index=df.index)),
        "service_cat": svc, "app_proto_cat": svc,
    }, index=df.index)


def _enrich_bot(df):
    return pd.DataFrame({
        "src_ip_bytes": np.nan, "dst_ip_bytes": np.nan, "missed_bytes": np.nan,
        "app_req_bytes": np.nan, "app_resp_bytes": np.nan, "tcp_seq": np.nan, "tcp_ack": np.nan,
        "dstport": np.nan, "ttl_total": np.nan, "dns_signal": np.nan, "flag_count": _g(df, "flgs"),
        "service_cat": pd.Series("other", index=df.index), "app_proto_cat": _unified._bot_protocol(df),
    }, index=df.index)


def _enrich_unsw(df):
    svc = df["service"].astype(str) if "service" in df.columns else pd.Series("other", index=df.index)
    return pd.DataFrame({
        "src_ip_bytes": np.nan, "dst_ip_bytes": np.nan,
        "missed_bytes": _g(df, "sloss").fillna(0) + _g(df, "dloss").fillna(0),
        "app_req_bytes": np.nan, "app_resp_bytes": _g(df, "response_body_len"),
        "tcp_seq": np.nan, "tcp_ack": np.nan, "dstport": np.nan,
        "ttl_total": _g(df, "sttl").fillna(0) + _g(df, "dttl").fillna(0),
        "dns_signal": np.nan, "flag_count": np.nan,
        "service_cat": svc, "app_proto_cat": _unified._unsw_protocol(df),
    }, index=df.index)


ENRICHERS = {"CICIoT2023": _enrich_cic, "TON_IoT": _enrich_ton, "BoT-IoT": _enrich_bot,
             "Edge-IIoTset": _enrich_edge, "UNSW-NB15": _enrich_unsw}


def project_enriched(name: str, df: pd.DataFrame) -> pd.DataFrame:
    base = PROJECTORS[name](df)                                 # 15 num + 2 cat
    extra = ENRICHERS[name](df)                                 # 11 num + 2 cat
    out = pd.concat([base, extra], axis=1)
    for lbl in _unified.LABELS:
        if lbl in df.columns:
            out[lbl] = df[lbl].values
    return out.replace([np.inf, -np.inf], np.nan)


# --- monkeypatched encoder: like qadcp.apply_unified_encoding but for all 4 categoricals ---
def apply_enriched_encoding(splits):
    encoders = {"fit_on": "train split only", "frequency": {}, "impute_medians": {}}
    for cat, out_col in CAT_PAIRS:
        if cat not in splits["train"].columns:
            continue
        ref = splits["train"][cat]
        _, fm = _unified.frequency_encode(ref, ref)
        encoders["frequency"][out_col] = fm
        for s in splits:
            if len(splits[s]) and cat in splits[s].columns:
                splits[s][out_col], _ = _unified.frequency_encode(ref, splits[s][cat])
                splits[s] = splits[s].drop(columns=[cat])
    numeric = [c for c in splits["train"].columns if c not in qadcp.LABELS and c not in ALL_CAT]
    for c in numeric:
        med = float(splits["train"][c].median()) if splits["train"][c].notna().any() else 0.0
        encoders["impute_medians"][c] = med
        for s in splits:
            if len(splits[s]) and c in splits[s].columns:
                splits[s][c] = splits[s][c].fillna(med)
    return splits, encoders


def main():
    SCHEMA_V2.write_text(json.dumps({
        "version": "1.1-enriched", "author": "AK (@Thedaemon-AK)",
        "rationale": "NetFlow-v2-aligned superset of the 17-feature v1.0 core to recover TON/Edge zero-day",
        "feature_order": FEATURE_ORDER, "n_features": len(FEATURE_ORDER),
        "enriched_numeric": ENRICH_NUM, "enriched_categorical": ENRICH_CAT,
    }, indent=1), encoding="utf-8")

    # patch the verified pipeline: 4 cats, matching encoder, enriched column order
    qadcp.CAT_COLS = ALL_CAT
    qadcp.apply_unified_encoding = apply_enriched_encoding
    qadcp.load_schema = lambda: {"feature_order": FEATURE_ORDER + qadcp.LABELS}  # keep labels in output

    def final_zeroday(qdir: Path) -> int:
        p = qdir / "zeroday.parquet"
        return int(len(pd.read_parquet(p))) if p.exists() else 0

    rows = []
    for name in qadcp.DATASET_DIRS:
        clean = pd.read_parquet(DATA / name / "processed" / f"{name}_clean.parquet")
        enr = project_enriched(name, clean)
        feat_cols = [c for c in _unified.NUM_COLS + ENRICH_NUM + ALL_CAT if c in enr.columns]
        before = len(enr)
        enr = enr.drop_duplicates(subset=feat_cols).reset_index(drop=True)
        out = DATA / name / "unified_v1_1" / "qadcp"
        log(f"enriched {name}: {before:,} -> dedup -{before - len(enr):,} -> {len(enr):,} rows x {len(FEATURE_ORDER)} feats")
        rep = qadcp.process_dataframe(enr, name, out, f"unified_v1_1 (enriched {len(FEATURE_ORDER)}f)", unified=True)
        zd_v10 = final_zeroday(DATA / name / "unified" / "qadcp")       # Iwo v1.0 (17f), post-dedup
        zd_v11 = final_zeroday(out)                                     # enriched v1.1, post-dedup
        rows.append({"dataset": name, "zeroday_v1_0_17f": zd_v10, "zeroday_v1_1_enriched": zd_v11,
                     "delta": zd_v11 - zd_v10, "n_features": rep["s6_quantum"]["n_features"]})

    (GEN / "unified_enriched_recovery.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    log("=== zero-day recovery: v1.0 (17f) -> v1.1 (enriched) ===")
    for r in rows:
        log(f"  {r['dataset']:13s} zeroday {r['zeroday_v1_0_17f']:>6} -> {r['zeroday_v1_1_enriched']:>6}  (Δ{r['delta']:+})")
    log(f"done -> datasets/<name>/unified_v1_1/qadcp/ + reports/_generated/unified_enriched_recovery.json")


if __name__ == "__main__":
    main()
