"""
Shared dataset paths + source registry for QS-Net Week-1 scripts.

Single source of truth after the `datasets/<name>/{raw,processed}/` restructure.
Imported by profile_datasets.py, eda_datasets.py and make_manifest.py so a path
change lands in exactly one place.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent      # week1/scripts
WEEK1 = HERE.parent                          # week1
PROJ = WEEK1.parent                          # qi26_12
DATASETS = PROJ / "datasets"
REPORTS = WEEK1 / "reports"
GEN = REPORTS / "_generated"
FIG = REPORTS / "figures"


def _raw(name: str) -> Path:
    return DATASETS / name / "raw"


# --- canonical file paths the pipeline reads ---
CICIOT_SPLITS = {s: _raw("CICIoT2023") / "CICIOT23" / s / f"{s}.csv"
                 for s in ("train", "test", "validation")}
TONIOT_NETWORK = (_raw("TON_IoT") / "Train_Test_datasets"
                  / "Train_Test_Network_dataset" / "train_test_network.csv")
BOTIOT_DIR = _raw("BoT-IoT")
EDGE_ML = (_raw("Edge-IIoTset") / "Edge-IIoTset dataset"
           / "Selected dataset for ML and DL" / "ML-EdgeIIoT-dataset.csv")
EDGE_DNN = (_raw("Edge-IIoTset") / "Edge-IIoTset dataset"
            / "Selected dataset for ML and DL" / "DNN-EdgeIIoT-dataset.csv")
UNSW_DIR = _raw("UNSW-NB15")
UNSW_FEATURES = UNSW_DIR / "NUSW-NB15_features.csv"
UNSW_RAW = [UNSW_DIR / f"UNSW-NB15_{i}.csv" for i in (1, 2, 3, 4)]
UNSW_TRAIN = UNSW_DIR / "UNSW_NB15_training-set.csv"
UNSW_TEST = UNSW_DIR / "UNSW_NB15_testing-set.csv"

# --- per-dataset dirs + provenance (for the manifest) ---
DATASET_DIRS = ["CICIoT2023", "TON_IoT", "BoT-IoT", "Edge-IIoTset", "UNSW-NB15"]

SOURCES = {
    "CICIoT2023": {
        "official": "https://www.unb.ca/cic/datasets/iotdataset-2023.html",
        "source": "Kaggle mirror: himadri07/ciciot2023 (row count is mirror-variant)",
        "paper": "Neto et al., CICIoT2023, Sensors 2023"},
    "TON_IoT": {
        "official": "https://research.unsw.edu.au/projects/toniot-datasets",
        "source": "UNSW TON_IoT — Train_Test_Network 50k-Normal variant (211,043 rows)",
        "paper": "Moustafa, TON_IoT, 2021"},
    "BoT-IoT": {
        "official": "https://research.unsw.edu.au/projects/bot-iot-dataset",
        "source": "UNSW BoT-IoT full 'Entire Dataset' — 74 CSV files",
        "paper": "Koroniotis et al., FGCS 2019"},
    "Edge-IIoTset": {
        "official": "https://www.kaggle.com/datasets/mohamedamineferrag/edgeiiotset-cyber-security-dataset-of-iot-iiot",
        "source": "Kaggle: mohamedamineferrag/edgeiiotset-cyber-security-dataset-of-iot-iiot",
        "paper": "Ferrag et al., 2022 (IEEE Access / TechRxiv)"},
    "UNSW-NB15": {
        "official": "https://research.unsw.edu.au/projects/unsw-nb15-dataset",
        "source": "Kaggle mirror: UNSW-NB15 complete (exact slug to confirm — several mirrors exist)",
        "paper": "Moustafa & Slay, 2015 (MilCIS)"},
}


def used_files() -> set:
    """Absolute path strings of the files the pipeline actually reads."""
    files = [*CICIOT_SPLITS.values(), TONIOT_NETWORK, EDGE_ML, EDGE_DNN,
             UNSW_FEATURES, *UNSW_RAW, UNSW_TRAIN, UNSW_TEST]
    files += sorted(BOTIOT_DIR.glob("data_*.csv"))   # all 74 + data_names.csv
    return {str(p) for p in files}
