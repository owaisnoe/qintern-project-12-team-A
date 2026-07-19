"""Unified schema projection helpers (Day 6)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema" / "unified_schema.json"
LABELS = ["label_multiclass", "label_binary"]
CAT_COLS = ["protocol_cat", "conn_state_cat"]
NUM_COLS = [
    "duration", "n_pkts_total", "n_bytes_total", "src_pkts", "dst_pkts",
    "src_bytes", "dst_bytes", "rate", "rate_src", "rate_dst",
    "pkt_size_min", "pkt_size_max", "pkt_size_mean", "pkt_size_std", "iat",
]


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _safe_sum(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    present = [c for c in cols if c in df.columns]
    if not present:
        return pd.Series(np.nan, index=df.index)
    return df[present].sum(axis=1)


def _first_present(df: pd.DataFrame, cols: list[str], default=np.nan) -> pd.Series:
    for c in cols:
        if c in df.columns:
            return df[c]
    return pd.Series(default, index=df.index)


def _cic_protocol(df: pd.DataFrame) -> pd.Series:
    flags = {
        "tcp": "TCP", "udp": "UDP", "icmp": "ICMP", "arp": "ARP",
        "dns": "DNS", "http": "HTTP", "https": "HTTPS",
    }
    out = pd.Series("other", index=df.index, dtype=object)
    for name, col in flags.items():
        if col in df.columns:
            out = out.where(df[col] <= 0, other=name)
    return out


def _cic_conn_state(df: pd.DataFrame) -> pd.Series:
    syn = df["syn_flag_number"] if "syn_flag_number" in df.columns else 0
    fin = df["fin_flag_number"] if "fin_flag_number" in df.columns else 0
    rst = df["rst_flag_number"] if "rst_flag_number" in df.columns else 0
    ack = df["ack_flag_number"] if "ack_flag_number" in df.columns else 0
    out = pd.Series("other", index=df.index, dtype=object)
    out = out.where(~((syn > 0) & (ack <= 0)), other="syn")
    out = out.where(~((fin > 0) & (rst <= 0)), other="fin")
    out = out.where(~(rst > 0), other="rst")
    out = out.where(~((ack > 0) & (syn <= 0)), other="established")
    return out


def _ton_protocol(df: pd.DataFrame) -> pd.Series:
    if "proto" not in df.columns:
        return pd.Series("other", index=df.index)
    m = {1: "tcp", 2: "udp", 3: "icmp", 0: "other"}
    return df["proto"].round().astype(int).map(m).fillna("other")


def _ton_conn_state(df: pd.DataFrame) -> pd.Series:
    if "conn_state" not in df.columns:
        return pd.Series("other", index=df.index)
    cs = df["conn_state"].round().astype(int)
    m = {0: "other", 1: "syn", 2: "rej", 3: "rst", 4: "established",
         5: "closed", 6: "established", 7: "fin", 8: "syn", 9: "closed",
         10: "established", 11: "rej", 12: "other", 13: "other"}
    return cs.map(m).fillna("other")


def _bot_protocol(df: pd.DataFrame) -> pd.Series:
    if "proto" not in df.columns:
        return pd.Series("other", index=df.index)
    p = df["proto"].round().astype(int)
    m = {1: "tcp", 2: "udp", 3: "icmp", 4: "arp", 5: "dns", 6: "tcp", 7: "udp"}
    return p.map(m).fillna("other")


def _bot_conn_state(df: pd.DataFrame) -> pd.Series:
    if "state" in df.columns:
        s = df["state"].round().astype(int)
        m = {0: "other", 1: "established", 2: "closed", 3: "syn", 4: "rst", 5: "rej",
             6: "fin", 7: "established", 8: "closed", 9: "other"}
        return s.map(m).fillna("other")
    return pd.Series("other", index=df.index)


def _edge_protocol(df: pd.DataFrame) -> pd.Series:
    out = pd.Series("other", index=df.index, dtype=object)
    if "mqtt.protoname" in df.columns:
        out = out.where(df["mqtt.protoname"] <= 0, other="mqtt")
    if "tcp.len" in df.columns:
        out = out.where(df["tcp.len"] <= 0, other="tcp")
    if "udp.port" in df.columns:
        out = out.where(df["udp.port"] <= 0, other="udp")
    if "icmp.checksum" in df.columns:
        out = out.where(df["icmp.checksum"] <= 0, other="icmp")
    if "arp.opcode" in df.columns:
        out = out.where(df["arp.opcode"] <= 0, other="arp")
    return out


def _edge_conn_state(df: pd.DataFrame) -> pd.Series:
    out = pd.Series("other", index=df.index, dtype=object)
    if "tcp.connection.syn" in df.columns:
        out = out.where(df["tcp.connection.syn"] <= 0, other="syn")
    if "tcp.connection.fin" in df.columns:
        out = out.where(df["tcp.connection.fin"] <= 0, other="fin")
    if "tcp.connection.rst" in df.columns:
        out = out.where(df["tcp.connection.rst"] <= 0, other="rst")
    if "tcp.connection.synack" in df.columns:
        out = out.where(df["tcp.connection.synack"] <= 0, other="established")
    return out


def _unsw_protocol(df: pd.DataFrame) -> pd.Series:
    if "proto" not in df.columns:
        return pd.Series("other", index=df.index)
    p = df["proto"].round().astype(int)
    buckets = {0: "tcp", 1: "udp", 2: "icmp", 3: "arp"}
    out = p.map(buckets)
    out = out.fillna("other")
    out = out.where(p <= 10, other="other")
    return out


def _unsw_conn_state(df: pd.DataFrame) -> pd.Series:
    if "state" not in df.columns:
        return pd.Series("other", index=df.index)
    s = df["state"].round().astype(int)
    m = {0: "other", 1: "established", 2: "fin", 3: "closed", 4: "syn",
         5: "rst", 6: "rej", 7: "established", 8: "closed", 9: "other", 10: "other"}
    return s.map(m).fillna("other")


def project_ciciot2023(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    out["duration"] = _first_present(df, ["flow_duration", "Duration"])
    pkt_cols = [c for c in ["syn_count", "ack_count", "fin_count", "rst_count", "urg_count"] if c in df.columns]
    out["n_pkts_total"] = _safe_sum(df, pkt_cols) if pkt_cols else _first_present(df, ["Tot size"])
    out["n_bytes_total"] = _first_present(df, ["Tot sum", "Tot size"])
    out["src_pkts"] = np.nan
    out["dst_pkts"] = np.nan
    out["src_bytes"] = np.nan
    out["dst_bytes"] = np.nan
    out["rate"] = _first_present(df, ["Rate"])
    # CIC clean checkpoint has Drate but no Srate — leave src NaN for train-median impute
    out["rate_src"] = _first_present(df, ["Srate"])
    out["rate_dst"] = _first_present(df, ["Drate"])
    out["pkt_size_min"] = _first_present(df, ["Min"])
    out["pkt_size_max"] = _first_present(df, ["Max"])
    out["pkt_size_mean"] = _first_present(df, ["Magnitue", "Std"])
    out["pkt_size_std"] = _first_present(df, ["Std", "Variance"])
    out["iat"] = _first_present(df, ["IAT"])
    out["protocol_cat"] = _cic_protocol(df)
    out["conn_state_cat"] = _cic_conn_state(df)
    return out


def project_ton_iot(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    out["duration"] = _first_present(df, ["duration"])
    out["src_pkts"] = _first_present(df, ["src_pkts"])
    out["dst_pkts"] = _first_present(df, ["dst_pkts"])
    out["n_pkts_total"] = out["src_pkts"] + out["dst_pkts"]
    out["src_bytes"] = _first_present(df, ["src_bytes"])
    out["dst_bytes"] = _first_present(df, ["dst_bytes"])
    out["n_bytes_total"] = out["src_bytes"] + out["dst_bytes"]
    dur = out["duration"].replace(0, np.nan)
    out["rate"] = out["n_pkts_total"] / dur
    out["rate_src"] = out["src_pkts"] / dur
    out["rate_dst"] = out["dst_pkts"] / dur
    out["pkt_size_min"] = np.nan
    out["pkt_size_max"] = np.nan
    out["pkt_size_mean"] = np.nan
    out["pkt_size_std"] = np.nan
    out["iat"] = np.nan
    out["protocol_cat"] = _ton_protocol(df)
    out["conn_state_cat"] = _ton_conn_state(df)
    return out


def project_bot_iot(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    out["duration"] = _first_present(df, ["dur"])
    out["n_pkts_total"] = _first_present(df, ["pkts"])
    out["n_bytes_total"] = _first_present(df, ["bytes"])
    out["src_pkts"] = _first_present(df, ["spkts"])
    out["dst_pkts"] = _first_present(df, ["dpkts"])
    out["src_bytes"] = _first_present(df, ["sbytes"])
    out["dst_bytes"] = _first_present(df, ["dbytes"])
    out["rate"] = _first_present(df, ["rate"])
    out["rate_src"] = _first_present(df, ["srate"])
    out["rate_dst"] = _first_present(df, ["drate"])
    out["pkt_size_min"] = _first_present(df, ["min"])
    out["pkt_size_max"] = _first_present(df, ["max"])
    out["pkt_size_mean"] = _first_present(df, ["mean"])
    out["pkt_size_std"] = _first_present(df, ["stddev"])
    out["iat"] = np.nan
    out["protocol_cat"] = _bot_protocol(df)
    out["conn_state_cat"] = _bot_conn_state(df)
    return out


def project_edge_iiotset(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    out["duration"] = _first_present(df, ["udp.time_delta", "tcp.len"])
    tcp_len = _first_present(df, ["tcp.len"], 0)
    udp_stream = _first_present(df, ["udp.stream"], 0)
    out["n_pkts_total"] = tcp_len + udp_stream
    out["n_bytes_total"] = _safe_sum(df, ["http.content_length", "tcp.len"])
    out["src_pkts"] = np.nan
    out["dst_pkts"] = np.nan
    out["src_bytes"] = np.nan
    out["dst_bytes"] = np.nan
    out["rate"] = _first_present(df, ["udp.time_delta"])
    out["rate_src"] = np.nan
    out["rate_dst"] = np.nan
    out["pkt_size_min"] = np.nan
    out["pkt_size_max"] = _first_present(df, ["tcp.len"])
    out["pkt_size_mean"] = np.nan
    out["pkt_size_std"] = np.nan
    out["iat"] = np.nan
    out["protocol_cat"] = _edge_protocol(df)
    out["conn_state_cat"] = _edge_conn_state(df)
    return out


def project_unsw_nb15(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    out["duration"] = _first_present(df, ["dur"])
    out["src_pkts"] = _first_present(df, ["spkts"])
    out["dst_pkts"] = _first_present(df, ["dpkts"])
    out["n_pkts_total"] = out["src_pkts"] + out["dst_pkts"]
    out["src_bytes"] = _first_present(df, ["sbytes"])
    out["dst_bytes"] = _first_present(df, ["dbytes"])
    out["n_bytes_total"] = out["src_bytes"] + out["dst_bytes"]
    out["rate"] = _first_present(df, ["rate"])
    out["rate_src"] = _first_present(df, ["sload"])
    out["rate_dst"] = _first_present(df, ["dload"])
    out["pkt_size_min"] = np.nan
    out["pkt_size_max"] = np.nan
    out["pkt_size_mean"] = (_first_present(df, ["smean"]) + _first_present(df, ["dmean"])) / 2
    out["pkt_size_std"] = np.nan
    out["iat"] = _first_present(df, ["sinpkt"])
    out["protocol_cat"] = _unsw_protocol(df)
    out["conn_state_cat"] = _unsw_conn_state(df)
    return out


PROJECTORS = {
    "CICIoT2023": project_ciciot2023,
    "TON_IoT": project_ton_iot,
    "BoT-IoT": project_bot_iot,
    "Edge-IIoTset": project_edge_iiotset,
    "UNSW-NB15": project_unsw_nb15,
}


def project_dataset(name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Map clean checkpoint -> unified columns + labels (cats as strings)."""
    proj = PROJECTORS[name](df)
    for lbl in LABELS:
        if lbl in df.columns:
            proj[lbl] = df[lbl].values
    proj = proj.replace([np.inf, -np.inf], np.nan)
    return proj


def dedup_features(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    feat_cols = [c for c in NUM_COLS + CAT_COLS + LABELS if c in df.columns]
    before = len(df)
    out = df.drop_duplicates(subset=feat_cols).reset_index(drop=True)
    return out, before - len(out)


def frequency_encode(train: pd.Series, series: pd.Series) -> tuple[pd.Series, dict]:
    """Train-fit frequency encoding; unknown -> 0."""
    counts = train.astype(str).value_counts(normalize=True)
    mapping = counts.to_dict()
    encoded = series.astype(str).map(mapping).fillna(0.0)
    return encoded, {"type": "frequency", "mapping": mapping, "unknown": 0.0}
