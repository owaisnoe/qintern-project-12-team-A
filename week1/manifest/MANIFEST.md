# Dataset MANIFEST — source pinning & checksums

**QS-Net / QuantumSentinel — Team A.** Implements R6 (see [`reports/00_findings_and_flaws.md`](../reports/00_findings_and_flaws.md) §5): every file is pinned by **source URL + row count + SHA-256** so all three of us train on byte-identical data. Kaggle mirrors/variants differ, so the **SHA-256 is the authoritative pin**.

Layout: `datasets/<name>/raw/` (source) · `datasets/<name>/processed/` (Day-3 clean checkpoints) · `datasets/<name>/qadcp/` (Day-4/5 QADCP splits + `quantum/` angle & PCA-8 tensors) · `datasets/<name>/unified/` (Day-6 unified schema package) · `week2/partitions/`, `week2/rq3/`, and `week2/baselines/` (Week-2 artifacts) · `datasets/<name>/<name>.zip` (download artifact). Regenerate / verify:
```bash
python week1/scripts/make_manifest.py           # regenerate
python week1/scripts/make_manifest.py --verify  # re-hash vs manifest.json (0 mismatches expected)
```
Total hashed: **41.5 GB** across 665 files.

## CICIoT2023
- **Official:** <https://www.unb.ca/cic/datasets/iotdataset-2023.html>
- **Source:** Kaggle mirror: himadri07/ciciot2023 (row count is mirror-variant)
- **Paper:** Neto et al., CICIoT2023, Sensors 2023
- Files: 105 · 3.01 GB

| file | kind | MB | rows | used | sha256 (16) |
|---|:--:|---:|---:|:--:|---|
| `test.csv` | raw | 348.0 | 1,176,851 | ✓ | `15aeb1f47a7bd3e3` |
| `train.csv` | raw | 1623.4 | 5,491,971 | ✓ | `ede08dc57e57369f` |
| `validation.csv` | raw | 347.9 | 1,176,851 | ✓ | `b13775e87ef64c8d` |
| `CICIoT2023.zip` | zip | 500.6 | — |  | `793b212d1dc40973` |
| `CICIoT2023_clean.parquet` | processed | 10.6 | — |  | `ef92b6fcb27c9a60` |
| `CICIoT2023_clean_meta.json` | processed | 0.0 | — |  | `cf48b6460363a87f` |
| `CICIoT2023_sample.csv` | processed | 0.3 | 1,000 |  | `00c09dab06c25578` |
| `calibration.parquet` | qadcp | 0.8 | — |  | `159476209c7a8e0c` |
| `feature_groups.json` | qadcp | 0.0 | — |  | `0460d995a12c5889` |
| `pca_baseline.json` | qadcp | 0.0 | — |  | `69b73f19fd79a6d6` |
| `qadcp_report.json` | qadcp | 0.0 | — |  | `a97cedc64286ef1c` |
| `pca8_calibration.parquet` | qadcp | 1.5 | — |  | `ec828ac68e9a82c2` |
| `pca8_test.parquet` | qadcp | 1.5 | — |  | `30f52c05804f947a` |
| `pca8_train.parquet` | qadcp | 10.8 | — |  | `94feb2500fa7a8a7` |
| `pca8_val.parquet` | qadcp | 1.5 | — |  | `4035c0863b1da5d5` |
| `pca8_zeroday.parquet` | qadcp | 0.8 | — |  | `8a1452d1d1ae1f74` |
| `q12_calibration.parquet` | qadcp | 0.4 | — |  | `bd4f0ee63cacdb08` |
| `q12_test.parquet` | qadcp | 0.4 | — |  | `e4a6de05b727073d` |
| `q12_train.parquet` | qadcp | 2.7 | — |  | `124c0ee2580e2b68` |
| `q12_val.parquet` | qadcp | 0.4 | — |  | `bbc114b8b968598e` |
| `q12_zeroday.parquet` | qadcp | 0.3 | — |  | `995f7ca0365a57db` |
| `q16_calibration.parquet` | qadcp | 0.4 | — |  | `48992c973493fc4f` |
| `q16_test.parquet` | qadcp | 0.4 | — |  | `90309407bfe0177e` |
| `q16_train.parquet` | qadcp | 2.8 | — |  | `ce9f80c980a3569c` |
| `q16_val.parquet` | qadcp | 0.4 | — |  | `6a0a0aaf3f643e30` |
| `q16_zeroday.parquet` | qadcp | 0.3 | — |  | `734daeb4a5b57238` |
| `q4_calibration.parquet` | qadcp | 0.2 | — |  | `62b77b7cbb5ae909` |
| `q4_test.parquet` | qadcp | 0.2 | — |  | `90b42f6b663b5120` |
| `q4_train.parquet` | qadcp | 1.2 | — |  | `af4dda4ace25a309` |
| `q4_val.parquet` | qadcp | 0.2 | — |  | `20ff36733717aac0` |
| `q4_zeroday.parquet` | qadcp | 0.1 | — |  | `2eac0076ff5ddb6a` |
| `q8_calibration.parquet` | qadcp | 0.4 | — |  | `61be55b797b0dc1f` |
| `q8_test.parquet` | qadcp | 0.4 | — |  | `4ad0c8e593dfbd85` |
| `q8_train.parquet` | qadcp | 2.4 | — |  | `e4e2b929f6e54cdb` |
| `q8_val.parquet` | qadcp | 0.4 | — |  | `dadb587d294e7c8c` |
| `q8_zeroday.parquet` | qadcp | 0.3 | — |  | `ffa4bbcf98e8b592` |
| `qubit_budgets.json` | qadcp | 0.0 | — |  | `1edef2694e9a23ce` |
| `scalers.json` | qadcp | 0.0 | — |  | `f16906233074fd27` |
| `test.parquet` | qadcp | 0.8 | — |  | `f58b08c27b656f41` |
| `train.parquet` | qadcp | 5.6 | — |  | `b2d8fb081c08c429` |
| `train_balanced.parquet` | qadcp | 5.6 | — |  | `2f5d7e3ecb8a34a1` |
| `val.parquet` | qadcp | 0.8 | — |  | `a8d04fcf100effdb` |
| `zero_day_tiers.json` | qadcp | 0.0 | — |  | `efb99e576a8bb214` |
| `zeroday.parquet` | qadcp | 0.6 | — |  | `397f4f619adcf239` |
| `CICIoT2023_unified.parquet` | unified | 8.0 | — |  | `3ad515bb5e223c52` |
| `CICIoT2023_unified_meta.json` | unified | 0.0 | — |  | `507ce5abae26e760` |
| `calibration.parquet` | unified | 0.8 | — |  | `b6efad8437f559ce` |
| `encoders.json` | unified | 0.0 | — |  | `32a7293bb5dba999` |
| `feature_groups.json` | unified | 0.0 | — |  | `f66eadb49a19f16e` |
| `pca_baseline.json` | unified | 0.0 | — |  | `e84c0d1f2c30c1f4` |
| `qadcp_report.json` | unified | 0.0 | — |  | `66cd47e58553f0da` |
| `pca8_calibration.parquet` | unified | 1.5 | — |  | `9cb11f85e24d6a05` |
| `pca8_test.parquet` | unified | 1.5 | — |  | `8f2457ef2f4eeb21` |
| `pca8_train.parquet` | unified | 10.8 | — |  | `d2634dba93b2b5c2` |
| `pca8_val.parquet` | unified | 1.5 | — |  | `da9272f134b429ea` |
| `pca8_zeroday.parquet` | unified | 0.9 | — |  | `66697dedb0ce843d` |
| `q12_calibration.parquet` | unified | 0.8 | — |  | `899ec1aa796fb4d7` |
| `q12_test.parquet` | unified | 0.8 | — |  | `5446bc57c05fcb8f` |
| `q12_train.parquet` | unified | 5.4 | — |  | `2dbbff0b09447e6a` |
| `q12_val.parquet` | unified | 0.8 | — |  | `e79932a622c8b6cf` |
| `q12_zeroday.parquet` | unified | 0.5 | — |  | `8191cf7a25107955` |
| `q16_calibration.parquet` | unified | 0.8 | — |  | `d8992d652b36a332` |
| `q16_test.parquet` | unified | 0.8 | — |  | `917ca3c4b3d499a7` |
| `q16_train.parquet` | unified | 5.4 | — |  | `142678f626af0d8c` |
| `q16_val.parquet` | unified | 0.8 | — |  | `cf9517af4a6e044f` |
| `q16_zeroday.parquet` | unified | 0.5 | — |  | `4343e648a5b8d74a` |
| `q4_calibration.parquet` | unified | 0.3 | — |  | `363074f941bcdfbe` |
| `q4_test.parquet` | unified | 0.3 | — |  | `43972eecbfc7fa40` |
| `q4_train.parquet` | unified | 1.8 | — |  | `4110453b41c0c3b3` |
| `q4_val.parquet` | unified | 0.3 | — |  | `d167e441adf9da3a` |
| `q4_zeroday.parquet` | unified | 0.2 | — |  | `2f0c8fd6506836b6` |
| `q8_calibration.parquet` | unified | 0.4 | — |  | `433dfb1a2b6d51b0` |
| `q8_test.parquet` | unified | 0.4 | — |  | `377741a975cb1f4d` |
| `q8_train.parquet` | unified | 2.7 | — |  | `26bad7ed7b2eebd1` |
| `q8_val.parquet` | unified | 0.4 | — |  | `1c0a330991e672c1` |
| `q8_zeroday.parquet` | unified | 0.3 | — |  | `1059880877c8d793` |
| `qubit_budgets.json` | unified | 0.0 | — |  | `9920d8bdd923fb2f` |
| `scalers.json` | unified | 0.0 | — |  | `93f11026ac1651fb` |
| `test.parquet` | unified | 0.8 | — |  | `647f638ae9151af3` |
| `train.parquet` | unified | 5.4 | — |  | `2633ad7ba40195e3` |
| `train_balanced.parquet` | unified | 5.3 | — |  | `6595bc59febbc823` |
| `val.parquet` | unified | 0.8 | — |  | `19eeb52ddc4abee9` |
| `validation_report.json` | unified | 0.0 | — |  | `31323b4b39ffbad9` |
| `zero_day_tiers.json` | unified | 0.0 | — |  | `1f1b85c830a1c6aa` |
| `zeroday.parquet` | unified | 0.5 | — |  | `138d10e91b63492b` |
| `calibration.csv` | week2 | 3.5 | 18,883 |  | `56de4cca3b6a7072` |
| `partition_meta.json` | week2 | 0.0 | — |  | `023bfc34566c0aba` |
| `test.csv` | week2 | 3.5 | 18,883 |  | `a2f5a7062e1a9b12` |
| `train.csv` | week2 | 28.2 | 151,049 |  | `930527be9c6d056d` |
| `zeroday.csv` | week2 | 2.5 | 10,984 |  | `98531bcb07ede24d` |
| `adversarial_source_pool.csv` | week2 | 0.9 | 3,273 |  | `b117863507fe6225` |
| `eval_clean.csv` | week2 | 1.8 | 6,473 |  | `539a38ee12e70e23` |
| `rq3_schema.json` | week2 | 0.0 | — |  | `76ddcb2c995c4b0b` |
| `autoencoder.joblib` | baseline | 0.0 | — |  | `f4155c29a1f7b94c` |
| `isolation_forest.joblib` | baseline | 4.8 | — |  | `52321bef8b2cb3a5` |
| `predictions.csv` | baseline | 3.5 | 29,867 |  | `fc9a41eee7b083be` |
| `results.json` | baseline | 0.0 | — |  | `500d4e588eebd5c0` |
| `xgboost_detector.json` | baseline | 9.4 | — |  | `7e18f402bc68c1d9` |
| `calibration_scores.head.csv` | week2 | 0.0 | 10 |  | `5d3a8249b4c5a162` |
| `calibration_scores.parquet` | week2 | 7.3 | — |  | `33d9aaedeb7d325a` |
| `prototypes_meta.json` | week2 | 0.0 | — |  | `ed4413c74eac3150` |
| `test_scores.head.csv` | week2 | 0.0 | 10 |  | `836632b33ba77ee4` |
| `test_scores.parquet` | week2 | 7.3 | — |  | `aa7e4d9aca41f1f9` |
| `zeroday_scores.head.csv` | week2 | 0.0 | 10 |  | `2578e133d9c129ab` |
| `zeroday_scores.parquet` | week2 | 4.0 | — |  | `e284d8af411ab74a` |

## TON_IoT
- **Official:** <https://research.unsw.edu.au/projects/toniot-datasets>
- **Source:** UNSW TON_IoT — Train_Test_Network 50k-Normal variant (211,043 rows)
- **Paper:** Moustafa, TON_IoT, 2021
- Files: 163 · 10.31 GB

| file | kind | MB | rows | used | sha256 (16) |
|---|:--:|---:|---:|:--:|---|
| `IoT_Fridge.csv` | raw | 25.0 | 587,076 |  | `e5c7fd42c1d44898` |
| `IoT_GPS_Tracker.csv` | raw | 31.4 | 595,686 |  | `aa1146435bd964b7` |
| `IoT_Garage_Door.csv` | raw | 25.8 | 591,446 |  | `76639fd3e4b5a800` |
| `IoT_Modbus.csv` | raw | 15.3 | 287,194 |  | `1cdb245661db3f15` |
| `IoT_Motion_Light.csv` | raw | 16.6 | 452,262 |  | `6bdd41ac3c3e9fc2` |
| `IoT_Thermostat.csv` | raw | 19.0 | 442,228 |  | `abb919eb3816d300` |
| `IoT_Weather.csv` | raw | 42.0 | 650,242 |  | `1b5e379011d37a1b` |
| `Linux_process_1.csv` | raw | 64.8 | 1,000,000 |  | `71ad491da40a83df` |
| `Linux_process_2.csv` | raw | 60.6 | 927,968 |  | `462d8e5eef2f9985` |
| `linux_disk_1.csv` | raw | 44.5 | 1,000,000 |  | `f7e314c7ff01285a` |
| `linux_disk_2.csv` | raw | 40.1 | 927,361 |  | `0c43702c3eeb47be` |
| `linux_memory1.csv` | raw | 60.7 | 1,000,000 |  | `7588cd7c21ffe662` |
| `linux_memory2.csv` | raw | 60.9 | 1,000,000 |  | `da7341144cea6819` |
| `Network_dataset_1.csv` | raw | 146.7 | 1,000,000 |  | `37ea5238fcd2a7a1` |
| `Network_dataset_10.csv` | raw | 146.5 | 1,000,000 |  | `c33290654db525d0` |
| `Network_dataset_11.csv` | raw | 148.4 | 1,000,000 |  | `ffd77ddb051852fa` |
| `Network_dataset_12.csv` | raw | 153.6 | 1,000,000 |  | `80fd7d6782d4acdd` |
| `Network_dataset_13.csv` | raw | 151.0 | 1,000,000 |  | `fc295ee26ebee93e` |
| `Network_dataset_14.csv` | raw | 153.3 | 1,000,000 |  | `8eb759212e6b36c2` |
| `Network_dataset_15.csv` | raw | 153.2 | 1,000,000 |  | `f7dded78b7670900` |
| `Network_dataset_16.csv` | raw | 153.0 | 1,000,000 |  | `415376cfbd6a4592` |
| `Network_dataset_17.csv` | raw | 149.9 | 1,000,000 |  | `d933a39088804258` |
| `Network_dataset_18.csv` | raw | 150.8 | 1,000,000 |  | `32d04d9cfefee407` |
| `Network_dataset_19.csv` | raw | 157.0 | 1,000,000 |  | `162203394dc41b30` |
| `Network_dataset_2.csv` | raw | 145.5 | 1,000,000 |  | `63b70bb96a95499b` |
| `Network_dataset_20.csv` | raw | 157.6 | 1,000,000 |  | `ca793a8ff6860c2a` |
| `Network_dataset_21.csv` | raw | 158.7 | 1,000,000 |  | `63fe9f2c91c48c0f` |
| `Network_dataset_22.csv` | raw | 153.3 | 1,000,000 |  | `a1f6009f2be53bc1` |
| `Network_dataset_23.csv` | raw | 51.7 | 339,021 |  | `e89c54673961c2b2` |
| `Network_dataset_3.csv` | raw | 145.6 | 1,000,000 |  | `7c8710722f26679c` |
| `Network_dataset_4.csv` | raw | 145.2 | 1,000,000 |  | `a20b2aed18fa4746` |
| `Network_dataset_5.csv` | raw | 145.2 | 1,000,000 |  | `2cfccfbc2816418b` |
| `Network_dataset_6.csv` | raw | 165.8 | 1,000,000 |  | `e8aa726d8551ffe5` |
| `Network_dataset_7.csv` | raw | 147.2 | 1,000,000 |  | `e5d3303520909b2e` |
| `Network_dataset_8.csv` | raw | 146.6 | 1,000,000 |  | `485c53e676016c73` |
| `Network_dataset_9.csv` | raw | 146.5 | 1,000,000 |  | `ed86e18cd03c6b9e` |
| `windows10_dataset.csv` | raw | 37.3 | 35,975 |  | `b66bef4541ad3b4a` |
| `windows7_dataset.csv` | raw | 25.1 | 28,367 |  | `5f36c505cb3df800` |
| `GroundTruth_IoT_Fridge.csv` | raw | 2.6 | 63,449 |  | `e9c3e2b953ec2938` |
| `GroundTruth_IoT_GPS_Tracker.csv` | raw | 2.7 | 64,565 |  | `467e412b300afaf3` |
| `GroundTruth_IoT_Garage_Door.csv` | raw | 2.4 | 58,633 |  | `c6e2a9401d9b972e` |
| `GroundTruth_IoT_Modbus.csv` | raw | 2.5 | 59,989 |  | `07199c40dab24da4` |
| `GroundTruth_IoT_Motion_Light.csv` | raw | 2.1 | 52,910 |  | `3b16012ea71acfe3` |
| `GroundTruth_IoT_Thermostat.csv` | raw | 2.1 | 49,601 |  | `3e3bc7c7a78ed176` |
| `GroundTruth_IoT_Weather.csv` | raw | 2.3 | 55,890 |  | `8c967703b1081581` |
| `GroundTruth_Linux_disk.csv` | raw | 7.6 | 316,637 |  | `54f4d83cb69d751b` |
| `GroundTruth_Linux_memory.csv` | raw | 4.9 | 205,623 |  | `7612840f907c33ef` |
| `GroundTruth_Linux_process.csv` | raw | 6.9 | 291,364 |  | `ebed9eec2531858b` |
| `GroundTruth_Network_1.csv` | raw | 63.4 | 1,000,000 |  | `79f2d99bf3496512` |
| `GroundTruth_Network_10.csv` | raw | 57.2 | 1,000,000 |  | `b0746eb0cd48473b` |
| `GroundTruth_Network_11.csv` | raw | 57.2 | 1,000,000 |  | `864b940ac93a6160` |
| `GroundTruth_Network_12.csv` | raw | 57.2 | 1,000,000 |  | `d6486f75626c511c` |
| `GroundTruth_Network_13.csv` | raw | 57.3 | 1,000,000 |  | `7b93a47bd2a09d99` |
| `GroundTruth_Network_14.csv` | raw | 58.3 | 1,000,000 |  | `2411ab4164dd93ca` |
| `GroundTruth_Network_15.csv` | raw | 58.5 | 1,000,000 |  | `d1d4cb491cb6edda` |
| `GroundTruth_Network_16.csv` | raw | 58.5 | 1,000,000 |  | `d1d4cb491cb6edda` |
| `GroundTruth_Network_17.csv` | raw | 55.5 | 1,000,000 |  | `68e999eaa3cb21b7` |
| `GroundTruth_Network_18.csv` | raw | 45.8 | 801,188 |  | `446170e48b77da49` |
| `GroundTruth_Network_2.csv` | raw | 63.1 | 1,000,000 |  | `3a688436c600ad26` |
| `GroundTruth_Network_3.csv` | raw | 62.8 | 1,000,000 |  | `89088705e97c0569` |
| `GroundTruth_Network_4.csv` | raw | 62.6 | 1,000,000 |  | `7dd2fd0469db61e5` |
| `GroundTruth_Network_5.csv` | raw | 62.7 | 1,000,000 |  | `dfa804275035d651` |
| `GroundTruth_Network_6.csv` | raw | 62.8 | 1,000,000 |  | `e66dfa775b3b1eb4` |
| `GroundTruth_Network_7.csv` | raw | 63.5 | 1,000,000 |  | `9c099cfd1c39117a` |
| `GroundTruth_Network_8.csv` | raw | 60.0 | 1,000,000 |  | `826d9a9938741826` |
| `GroundTruth_Network_9.csv` | raw | 57.5 | 1,000,000 |  | `5fab83f3602faea6` |
| `GroundTruth_Windows10.csv` | raw | 0.2 | 11,104 |  | `57ab1bf2dd63a64c` |
| `GroundTruth_Windows7.csv` | raw | 0.1 | 5,980 |  | `e503ddf710e263d1` |
| `Train_Test_IoT_Fridge.csv` | raw | 1.7 | 39,944 |  | `56377a00b97204ea` |
| `Train_Test_IoT_GPS_Tracker.csv` | raw | 2.1 | 38,960 |  | `71c6cc302b14822a` |
| `Train_Test_IoT_Garage_Door.csv` | raw | 1.7 | 39,587 |  | `44b2d63f233ed239` |
| `Train_Test_IoT_Modbus.csv` | raw | 1.7 | 31,106 |  | `78345a857244e671` |
| `Train_Test_IoT_Motion_Light.csv` | raw | 1.5 | 39,488 |  | `e0e145ff3d8145d4` |
| `Train_Test_IoT_Thermostat.csv` | raw | 1.5 | 32,774 |  | `b475654a43ec885f` |
| `Train_Test_IoT_Weather.csv` | raw | 2.6 | 39,260 |  | `10c49fe8a6eae98d` |
| `Train_Test_Linux_process.csv` | raw | 4.9 | 90,112 |  | `63a878f944bea1d3` |
| `Train_test_linux_disk.csv` | raw | 3.0 | 90,112 |  | `6116cd5d3a7c7bf1` |
| `Train_test_linux_memory.csv` | raw | 3.5 | 70,112 |  | `cfa9b8f32e4a1ba0` |
| `train_test_network.csv` | raw | 29.9 | 211,043 | ✓ | `26ddc513552de36d` |
| `Train_Test_Windows_10.csv` | raw | 21.8 | 21,104 |  | `85f0827697ef5b0f` |
| `Train_Test_Windows_7.csv` | raw | 14.1 | 15,980 |  | `5ed0c685148449bb` |
| `TON_IoT.zip` | zip | 5134.3 | — |  | `8c30f8f660a1bb1d` |
| `TON_IoT_clean.parquet` | processed | 1.8 | — |  | `d8a02c8a260e6b15` |
| `TON_IoT_clean_meta.json` | processed | 0.0 | — |  | `6b153e27617e27c9` |
| `TON_IoT_sample.csv` | processed | 0.2 | 1,000 |  | `76a7a9718cfae540` |
| `calibration.parquet` | qadcp | 0.2 | — |  | `c1c1fe0cd2798ba8` |
| `feature_groups.json` | qadcp | 0.0 | — |  | `6bca82ff265f978a` |
| `pca_baseline.json` | qadcp | 0.0 | — |  | `4723962f8b73351e` |
| `qadcp_report.json` | qadcp | 0.0 | — |  | `003e584c981fb2de` |
| `pca8_calibration.parquet` | qadcp | 0.7 | — |  | `2f7cccdb35afd3e4` |
| `pca8_test.parquet` | qadcp | 0.7 | — |  | `14646d8e88911bc2` |
| `pca8_train.parquet` | qadcp | 5.0 | — |  | `aa5bb6643d3dceda` |
| `pca8_val.parquet` | qadcp | 0.7 | — |  | `4c4bfb5b328cc6a4` |
| `pca8_zeroday.parquet` | qadcp | 0.0 | — |  | `0ca58830cff685ff` |
| `q12_calibration.parquet` | qadcp | 0.1 | — |  | `8da6d94adc3b4313` |
| `q12_test.parquet` | qadcp | 0.1 | — |  | `f483461be7c16d35` |
| `q12_train.parquet` | qadcp | 0.5 | — |  | `74c0b3912baf0d00` |
| `q12_val.parquet` | qadcp | 0.1 | — |  | `6dc1ec7196c0884b` |
| `q12_zeroday.parquet` | qadcp | 0.0 | — |  | `a967912a5e037949` |
| `q16_calibration.parquet` | qadcp | 0.2 | — |  | `23b0c3c1d40a35e6` |
| `q16_test.parquet` | qadcp | 0.2 | — |  | `0a8c3ca25fe377a2` |
| `q16_train.parquet` | qadcp | 1.2 | — |  | `08ee55bf194f59c4` |
| `q16_val.parquet` | qadcp | 0.2 | — |  | `e6bdacce9e90e810` |
| `q16_zeroday.parquet` | qadcp | 0.0 | — |  | `d232dfe0ef95672b` |
| `q4_calibration.parquet` | qadcp | 0.0 | — |  | `d35ccb2eac2f8993` |
| `q4_test.parquet` | qadcp | 0.0 | — |  | `621ddf82c1c1aeec` |
| `q4_train.parquet` | qadcp | 0.3 | — |  | `cd77c0fb083cd8b4` |
| `q4_val.parquet` | qadcp | 0.0 | — |  | `206d872fc504c71b` |
| `q4_zeroday.parquet` | qadcp | 0.0 | — |  | `3f04f9f660180cbd` |
| `q8_calibration.parquet` | qadcp | 0.1 | — |  | `6ed876b53283fd77` |
| `q8_test.parquet` | qadcp | 0.1 | — |  | `8fb5dd84047a5f6c` |
| `q8_train.parquet` | qadcp | 0.4 | — |  | `ed0e97fc6db84e51` |
| `q8_val.parquet` | qadcp | 0.1 | — |  | `6333a97a5ab30e6d` |
| `q8_zeroday.parquet` | qadcp | 0.0 | — |  | `fa4974d63bf22ce1` |
| `qubit_budgets.json` | qadcp | 0.0 | — |  | `f8003d7ad0b7eced` |
| `scalers.json` | qadcp | 0.0 | — |  | `361d91bef1e8cea8` |
| `test.parquet` | qadcp | 0.2 | — |  | `e7a2d9712df6c71f` |
| `train.parquet` | qadcp | 1.3 | — |  | `3e9c98f7bb2a63a4` |
| `train_balanced.parquet` | qadcp | 1.3 | — |  | `3450529a2d892b71` |
| `val.parquet` | qadcp | 0.2 | — |  | `20e6355132dde663` |
| `zero_day_tiers.json` | qadcp | 0.0 | — |  | `40f1b654b1fb48ef` |
| `zeroday.parquet` | qadcp | 0.0 | — |  | `1218fa56164eee5f` |
| `TON_IoT_unified.parquet` | unified | 3.6 | — |  | `ff8e11fc43c5cc07` |
| `TON_IoT_unified_meta.json` | unified | 0.0 | — |  | `c78044d2a9c996be` |
| `calibration.parquet` | unified | 0.4 | — |  | `86b8dbe272379e22` |
| `encoders.json` | unified | 0.0 | — |  | `cca858853d5ce467` |
| `feature_groups.json` | unified | 0.0 | — |  | `78eb1b1535b98a80` |
| `pca_baseline.json` | unified | 0.0 | — |  | `ee3badd0acc60871` |
| `qadcp_report.json` | unified | 0.0 | — |  | `f44a36511421ea7d` |
| `pca8_calibration.parquet` | unified | 0.7 | — |  | `a5a23ad48853f6db` |
| `pca8_test.parquet` | unified | 0.7 | — |  | `435380190f513513` |
| `pca8_train.parquet` | unified | 4.8 | — |  | `17ad37823afd2c61` |
| `pca8_val.parquet` | unified | 0.7 | — |  | `fbb5dd22ec8d456b` |
| `pca8_zeroday.parquet` | unified | 0.0 | — |  | `a28b15c05ea74725` |
| `q12_calibration.parquet` | unified | 0.4 | — |  | `797859bb1e2f0785` |
| `q12_test.parquet` | unified | 0.4 | — |  | `5d25af5f3449b8b0` |
| `q12_train.parquet` | unified | 2.5 | — |  | `eaddd449cef0c1c1` |
| `q12_val.parquet` | unified | 0.4 | — |  | `0d3534c1871768d4` |
| `q12_zeroday.parquet` | unified | 0.0 | — |  | `f267f0a9777b9198` |
| `q16_calibration.parquet` | unified | 0.4 | — |  | `c3e5d046e0556366` |
| `q16_test.parquet` | unified | 0.4 | — |  | `100733c21bd611fa` |
| `q16_train.parquet` | unified | 2.5 | — |  | `ace549b789cac1b6` |
| `q16_val.parquet` | unified | 0.4 | — |  | `3aec40ae3d8f11bb` |
| `q16_zeroday.parquet` | unified | 0.0 | — |  | `1471721ef396e8f1` |
| `q4_calibration.parquet` | unified | 0.0 | — |  | `df50bb1ea7dde54a` |
| `q4_test.parquet` | unified | 0.0 | — |  | `602e09958e4a0d87` |
| `q4_train.parquet` | unified | 0.3 | — |  | `138b7f743f264240` |
| `q4_val.parquet` | unified | 0.0 | — |  | `9617fb17bcd19c07` |
| `q4_zeroday.parquet` | unified | 0.0 | — |  | `be2f9d8e87480645` |
| `q8_calibration.parquet` | unified | 0.2 | — |  | `8ca41488d3686df3` |
| `q8_test.parquet` | unified | 0.2 | — |  | `d4ebc02462b51b63` |
| `q8_train.parquet` | unified | 1.0 | — |  | `56f64b49562f6ff0` |
| `q8_val.parquet` | unified | 0.2 | — |  | `9c46c0053a7ace7c` |
| `q8_zeroday.parquet` | unified | 0.0 | — |  | `16eb12552e9d3536` |
| `qubit_budgets.json` | unified | 0.0 | — |  | `bde9205a09efa840` |
| `scalers.json` | unified | 0.0 | — |  | `c0522cece20c36f8` |
| `test.parquet` | unified | 0.4 | — |  | `dbe62f6791649dd7` |
| `train.parquet` | unified | 2.6 | — |  | `5d8626ee2b25fc09` |
| `train_balanced.parquet` | unified | 2.6 | — |  | `495e8d0b17277e67` |
| `val.parquet` | unified | 0.4 | — |  | `76dda7382172b2a9` |
| `validation_report.json` | unified | 0.0 | — |  | `56f9d51e3415bc3b` |
| `zero_day_tiers.json` | unified | 0.0 | — |  | `c53ddfac1241ec11` |
| `zeroday.parquet` | unified | 0.0 | — |  | `a31f208fdd6af02d` |

## BoT-IoT
- **Official:** <https://research.unsw.edu.au/projects/bot-iot-dataset>
- **Source:** UNSW BoT-IoT full 'Entire Dataset' — 74 CSV files
- **Paper:** Koroniotis et al., FGCS 2019
- Files: 178 · 16.46 GB

| file | kind | MB | rows | used | sha256 (16) |
|---|:--:|---:|---:|:--:|---|
| `data_1.csv` | raw | 218.3 | 1,000,000 | ✓ | `119b2b2f92db5ea5` |
| `data_10.csv` | raw | 203.2 | 1,000,000 | ✓ | `0c852ecc50cf038a` |
| `data_11.csv` | raw | 204.7 | 1,000,000 | ✓ | `255ae04c7a6fda77` |
| `data_12.csv` | raw | 201.3 | 1,000,000 | ✓ | `c543c6717a0e1769` |
| `data_13.csv` | raw | 205.2 | 1,000,000 | ✓ | `5fd8f19fc8566a0b` |
| `data_14.csv` | raw | 205.9 | 1,000,000 | ✓ | `91e3ce2d1fec828a` |
| `data_15.csv` | raw | 204.6 | 1,000,000 | ✓ | `363a75c0c7ab02f6` |
| `data_16.csv` | raw | 206.0 | 1,000,000 | ✓ | `ab3d4c644b180d09` |
| `data_17.csv` | raw | 202.0 | 1,000,000 | ✓ | `c7dcb87ca074f395` |
| `data_18.csv` | raw | 204.8 | 1,000,000 | ✓ | `90389431309fec72` |
| `data_19.csv` | raw | 204.6 | 1,000,000 | ✓ | `a056230eaf69a0a7` |
| `data_2.csv` | raw | 218.3 | 1,000,000 | ✓ | `640929e6502f00a7` |
| `data_20.csv` | raw | 197.8 | 1,000,000 | ✓ | `6a28c651f7e133dc` |
| `data_21.csv` | raw | 206.7 | 1,000,000 | ✓ | `716fa22469ee4a7d` |
| `data_22.csv` | raw | 205.7 | 1,000,000 | ✓ | `cae994b4faac1c84` |
| `data_23.csv` | raw | 205.6 | 1,000,000 | ✓ | `bb56d828ee44724d` |
| `data_24.csv` | raw | 206.0 | 1,000,000 | ✓ | `a19fa58534ad6ffc` |
| `data_25.csv` | raw | 205.1 | 1,000,000 | ✓ | `e2a84101f943f319` |
| `data_26.csv` | raw | 196.8 | 1,000,000 | ✓ | `cd7fddf917accc5d` |
| `data_27.csv` | raw | 207.1 | 1,000,000 | ✓ | `9b688ce7cdf65fd6` |
| `data_28.csv` | raw | 203.3 | 1,000,000 | ✓ | `70360ffb1ca93bdb` |
| `data_29.csv` | raw | 206.8 | 1,000,000 | ✓ | `f29bb1cef6db112c` |
| `data_3.csv` | raw | 204.1 | 1,000,000 | ✓ | `16c797f1aba26bb0` |
| `data_30.csv` | raw | 205.2 | 1,000,000 | ✓ | `5e24fcc46adc7917` |
| `data_31.csv` | raw | 198.9 | 1,000,000 | ✓ | `c2da8232ce030214` |
| `data_32.csv` | raw | 206.8 | 1,000,000 | ✓ | `c1043981c50f3f90` |
| `data_33.csv` | raw | 197.9 | 1,000,000 | ✓ | `305ea2b6210acf10` |
| `data_34.csv` | raw | 206.0 | 1,000,000 | ✓ | `3c757cd0ae647d4e` |
| `data_35.csv` | raw | 202.5 | 1,000,000 | ✓ | `931b05daab545803` |
| `data_36.csv` | raw | 208.6 | 1,000,000 | ✓ | `e3e215bce9f247a7` |
| `data_37.csv` | raw | 206.8 | 1,000,000 | ✓ | `eb4349e4bbd8fcf6` |
| `data_38.csv` | raw | 207.5 | 1,000,000 | ✓ | `4f987b83ec4d80e7` |
| `data_39.csv` | raw | 207.4 | 1,000,000 | ✓ | `998fd618f068cb17` |
| `data_4.csv` | raw | 204.4 | 1,000,000 | ✓ | `f73f341f5eca3c88` |
| `data_40.csv` | raw | 202.4 | 1,000,000 | ✓ | `3966fde140fc5fe9` |
| `data_41.csv` | raw | 208.5 | 1,000,000 | ✓ | `66727702450ef3e2` |
| `data_42.csv` | raw | 202.1 | 1,000,000 | ✓ | `e9f80d9bc7035d62` |
| `data_43.csv` | raw | 203.1 | 1,000,000 | ✓ | `2b4c9a9f40a33f92` |
| `data_44.csv` | raw | 204.9 | 1,000,000 | ✓ | `684aadf6f84fd078` |
| `data_45.csv` | raw | 207.8 | 1,000,000 | ✓ | `949f1833a122839c` |
| `data_46.csv` | raw | 207.3 | 1,000,000 | ✓ | `4183e6435f6ec47a` |
| `data_47.csv` | raw | 199.2 | 1,000,000 | ✓ | `6e4132dff26cac56` |
| `data_48.csv` | raw | 197.3 | 1,000,000 | ✓ | `abefbcc44019e8a6` |
| `data_49.csv` | raw | 203.7 | 1,000,000 | ✓ | `6974529ce7daa71c` |
| `data_5.csv` | raw | 204.3 | 1,000,000 | ✓ | `b0e0678896929b1f` |
| `data_50.csv` | raw | 203.7 | 1,000,000 | ✓ | `64f915311ebf50ef` |
| `data_51.csv` | raw | 192.8 | 1,000,000 | ✓ | `c40e272b7c559b01` |
| `data_52.csv` | raw | 203.8 | 1,000,000 | ✓ | `57b9f4e137b68ad7` |
| `data_53.csv` | raw | 207.1 | 1,000,000 | ✓ | `ab8612ca9adc512d` |
| `data_54.csv` | raw | 207.0 | 1,000,000 | ✓ | `f47309fb0c2869ad` |
| `data_55.csv` | raw | 204.1 | 1,000,000 | ✓ | `5b03ce2146775a79` |
| `data_56.csv` | raw | 210.1 | 1,000,000 | ✓ | `52b14c1cc476d17e` |
| `data_57.csv` | raw | 208.7 | 1,000,000 | ✓ | `b8ed09fc778207de` |
| `data_58.csv` | raw | 208.2 | 1,000,000 | ✓ | `7fd6cee66226b312` |
| `data_59.csv` | raw | 207.9 | 1,000,000 | ✓ | `0969742604b1b63a` |
| `data_6.csv` | raw | 201.3 | 1,000,000 | ✓ | `2c5fdd0c9f21ee71` |
| `data_60.csv` | raw | 209.5 | 1,000,000 | ✓ | `a666f8c9df78bc12` |
| `data_61.csv` | raw | 210.4 | 1,000,000 | ✓ | `a57194731e3ff748` |
| `data_62.csv` | raw | 210.5 | 1,000,000 | ✓ | `41d587a547711251` |
| `data_63.csv` | raw | 208.6 | 1,000,000 | ✓ | `4088ec65f6d84bef` |
| `data_64.csv` | raw | 205.6 | 1,000,000 | ✓ | `e5a84f67a546a3a5` |
| `data_65.csv` | raw | 203.7 | 1,000,000 | ✓ | `776024daccdd74e3` |
| `data_66.csv` | raw | 203.6 | 1,000,000 | ✓ | `1fe01e57773c5f89` |
| `data_67.csv` | raw | 200.2 | 1,000,000 | ✓ | `7d71da951a2a3698` |
| `data_68.csv` | raw | 199.7 | 1,000,000 | ✓ | `6523ef9574da0035` |
| `data_69.csv` | raw | 200.8 | 1,000,000 | ✓ | `5308580f3e4977fc` |
| `data_7.csv` | raw | 203.7 | 1,000,000 | ✓ | `cbf5b6c030c9f346` |
| `data_70.csv` | raw | 187.9 | 1,000,000 | ✓ | `64e602bf984a30e6` |
| `data_71.csv` | raw | 201.4 | 1,000,000 | ✓ | `10a3b0f1773f22da` |
| `data_72.csv` | raw | 202.9 | 1,000,000 | ✓ | `e95cd0e2dabccf28` |
| `data_73.csv` | raw | 202.4 | 1,000,000 | ✓ | `8f1ea93c43f22742` |
| `data_74.csv` | raw | 73.5 | 370,443 | ✓ | `5ffd6482a3feda1c` |
| `data_8.csv` | raw | 204.3 | 1,000,000 | ✓ | `db8af330e8a87129` |
| `data_9.csv` | raw | 198.3 | 1,000,000 | ✓ | `0d9b34c2f17da964` |
| `data_names.csv` | raw | 0.0 | 0 | ✓ | `0c7516e0fb425ba0` |
| `BoT-IoT.zip` | zip | 1257.1 | — |  | `7869754e4b6192b4` |
| `BoT-IoT_clean.parquet` | processed | 13.1 | — |  | `3f18181730ad86c7` |
| `BoT-IoT_clean_meta.json` | processed | 0.0 | — |  | `47eb4207457c1124` |
| `BoT-IoT_sample.csv` | processed | 0.3 | 1,000 |  | `075c20e614a1b980` |
| `calibration.parquet` | qadcp | 1.3 | — |  | `b8bdadf2a16e3fb1` |
| `feature_groups.json` | qadcp | 0.0 | — |  | `1ca1456c230cc517` |
| `pca_baseline.json` | qadcp | 0.0 | — |  | `d16fd2a7f47baad6` |
| `qadcp_report.json` | qadcp | 0.0 | — |  | `f9f648fd53f59582` |
| `pca8_calibration.parquet` | qadcp | 1.5 | — |  | `9adf10e9657ffaec` |
| `pca8_test.parquet` | qadcp | 1.5 | — |  | `b512adb5205576bc` |
| `pca8_train.parquet` | qadcp | 10.6 | — |  | `bef5aeb21e37bf5c` |
| `pca8_val.parquet` | qadcp | 1.5 | — |  | `ab3df2668d7a5484` |
| `pca8_zeroday.parquet` | qadcp | 0.1 | — |  | `7d818c3062ef3f70` |
| `q12_calibration.parquet` | qadcp | 0.9 | — |  | `f1a868448689c63d` |
| `q12_test.parquet` | qadcp | 0.9 | — |  | `62021b097f2093d4` |
| `q12_train.parquet` | qadcp | 6.3 | — |  | `70db33b9e0c82590` |
| `q12_val.parquet` | qadcp | 0.9 | — |  | `4db8be340f41cfbf` |
| `q12_zeroday.parquet` | qadcp | 0.0 | — |  | `d1813ff147d49c17` |
| `q16_calibration.parquet` | qadcp | 1.3 | — |  | `965d95d40d8dfb83` |
| `q16_test.parquet` | qadcp | 1.3 | — |  | `a4616a8622d05fad` |
| `q16_train.parquet` | qadcp | 9.1 | — |  | `567e063d052c796e` |
| `q16_val.parquet` | qadcp | 1.3 | — |  | `e0f076e4e8b31d8a` |
| `q16_zeroday.parquet` | qadcp | 0.1 | — |  | `07a5d13ec1a71e72` |
| `q4_calibration.parquet` | qadcp | 0.4 | — |  | `f0cfbc9912006d7f` |
| `q4_test.parquet` | qadcp | 0.4 | — |  | `b5f43e4ac9ad8cde` |
| `q4_train.parquet` | qadcp | 2.5 | — |  | `28892a546bb6873a` |
| `q4_val.parquet` | qadcp | 0.4 | — |  | `40263ccee96440b9` |
| `q4_zeroday.parquet` | qadcp | 0.0 | — |  | `aedcbe012620de16` |
| `q8_calibration.parquet` | qadcp | 0.6 | — |  | `e0cda1d07093723c` |
| `q8_test.parquet` | qadcp | 0.6 | — |  | `6aa7ee4198c3a797` |
| `q8_train.parquet` | qadcp | 4.1 | — |  | `adc7131a37e2e156` |
| `q8_val.parquet` | qadcp | 0.6 | — |  | `315049bd5766de90` |
| `q8_zeroday.parquet` | qadcp | 0.0 | — |  | `84c2465e1282c227` |
| `qubit_budgets.json` | qadcp | 0.0 | — |  | `141aa13654b9b980` |
| `scalers.json` | qadcp | 0.0 | — |  | `7f85ff5ba190939f` |
| `test.parquet` | qadcp | 1.3 | — |  | `d206c2be02a5ff2f` |
| `train.parquet` | qadcp | 9.1 | — |  | `d18ab0b064220594` |
| `train_balanced.parquet` | qadcp | 3.4 | — |  | `93100a8fdd043008` |
| `val.parquet` | qadcp | 1.3 | — |  | `2259ee653c7557d5` |
| `zero_day_tiers.json` | qadcp | 0.0 | — |  | `1771c70eacbe3981` |
| `zeroday.parquet` | qadcp | 0.1 | — |  | `855fd79278baa131` |
| `BoT-IoT_unified.parquet` | unified | 11.5 | — |  | `a81e2c68a9c34290` |
| `BoT-IoT_unified_meta.json` | unified | 0.0 | — |  | `a5110ecff25e44bb` |
| `calibration.parquet` | unified | 1.2 | — |  | `cb28112bab90bc83` |
| `encoders.json` | unified | 0.0 | — |  | `1ebe5c7f56fd0eda` |
| `feature_groups.json` | unified | 0.0 | — |  | `f66eadb49a19f16e` |
| `pca_baseline.json` | unified | 0.0 | — |  | `6afeccf9dbaa43d8` |
| `qadcp_report.json` | unified | 0.0 | — |  | `bc582ad19b53e4e5` |
| `pca8_calibration.parquet` | unified | 1.5 | — |  | `2fb84e4b36b3bde3` |
| `pca8_test.parquet` | unified | 1.5 | — |  | `41b9d2e9df41ae5c` |
| `pca8_train.parquet` | unified | 10.6 | — |  | `39f7c85cdef64712` |
| `pca8_val.parquet` | unified | 1.5 | — |  | `fade62cc31ccea68` |
| `pca8_zeroday.parquet` | unified | 0.1 | — |  | `d89e5493b2b7f519` |
| `q12_calibration.parquet` | unified | 1.0 | — |  | `f74e2ca783b94203` |
| `q12_test.parquet` | unified | 1.0 | — |  | `18fe0d669f82da92` |
| `q12_train.parquet` | unified | 6.5 | — |  | `6b7600155689d95b` |
| `q12_val.parquet` | unified | 1.0 | — |  | `caf517a871424897` |
| `q12_zeroday.parquet` | unified | 0.0 | — |  | `d9f766e54b1788e4` |
| `q16_calibration.parquet` | unified | 1.2 | — |  | `95db10b705660c4d` |
| `q16_test.parquet` | unified | 1.2 | — |  | `f9908cd9e6cef910` |
| `q16_train.parquet` | unified | 8.2 | — |  | `79913d2c095c95e0` |
| `q16_val.parquet` | unified | 1.2 | — |  | `52b7d596dcd8059d` |
| `q16_zeroday.parquet` | unified | 0.1 | — |  | `d2327cd0bf4da094` |
| `q4_calibration.parquet` | unified | 0.4 | — |  | `f28b8ba924d0f864` |
| `q4_test.parquet` | unified | 0.4 | — |  | `228035c9c364c9cf` |
| `q4_train.parquet` | unified | 2.5 | — |  | `36ba862abff0ad1d` |
| `q4_val.parquet` | unified | 0.4 | — |  | `4d9af95dcfe0765e` |
| `q4_zeroday.parquet` | unified | 0.0 | — |  | `6567a165faba4e2f` |
| `q8_calibration.parquet` | unified | 0.5 | — |  | `cc28b646f8078b77` |
| `q8_test.parquet` | unified | 0.5 | — |  | `b683bd8e4cd52072` |
| `q8_train.parquet` | unified | 3.1 | — |  | `d590666870455782` |
| `q8_val.parquet` | unified | 0.5 | — |  | `a14343bcee1eaf61` |
| `q8_zeroday.parquet` | unified | 0.0 | — |  | `db902078d61c99f7` |
| `qubit_budgets.json` | unified | 0.0 | — |  | `8b21064c7322a44d` |
| `scalers.json` | unified | 0.0 | — |  | `0df83d6d483ff0f0` |
| `test.parquet` | unified | 1.2 | — |  | `5b9ea500c15c0ace` |
| `train.parquet` | unified | 8.2 | — |  | `b7d187efac0acbd1` |
| `train_balanced.parquet` | unified | 3.1 | — |  | `a60f310caf50e530` |
| `val.parquet` | unified | 1.2 | — |  | `fe6acf99d02cf6d4` |
| `validation_report.json` | unified | 0.0 | — |  | `f62365267be55b84` |
| `zero_day_tiers.json` | unified | 0.0 | — |  | `bef8df46499f0589` |
| `zeroday.parquet` | unified | 0.1 | — |  | `310432da39104872` |
| `calibration.csv` | week2 | 4.6 | 18,591 |  | `6f3d2aff1ed822f2` |
| `partition_meta.json` | week2 | 0.0 | — |  | `6d1aaeb018c331a0` |
| `test.csv` | week2 | 4.6 | 18,591 |  | `cfc238692a4e2c4e` |
| `train.csv` | week2 | 36.8 | 148,729 |  | `fd6a8b7d1a6f5004` |
| `zeroday.csv` | week2 | 0.2 | 683 |  | `fe35fd90b63550f0` |
| `adversarial_source_pool.csv` | week2 | 0.2 | 600 |  | `4d5d085bbd3caf2b` |
| `eval_clean.csv` | week2 | 0.5 | 1,483 |  | `e80014f787445b6d` |
| `rq3_schema.json` | week2 | 0.0 | — |  | `15cfbf1cc2f832f5` |
| `autoencoder.joblib` | baseline | 0.0 | — |  | `2927a2ae61f70324` |
| `isolation_forest.joblib` | baseline | 4.4 | — |  | `37fb36f3e81b584e` |
| `ocsvm.joblib` | baseline | 0.0 | — |  | `c46dcd8b43632014` |
| `predictions.csv` | baseline | 2.3 | 19,274 |  | `b0f5882e51809797` |
| `results.json` | baseline | 0.0 | — |  | `494e68bb029ede58` |
| `xgboost_detector.json` | baseline | 2.2 | — |  | `0e9a926538529cb9` |
| `calibration_scores.head.csv` | week2 | 0.0 | 10 |  | `cee8fc4b7d46957b` |
| `calibration_scores.parquet` | week2 | 2.2 | — |  | `d523512d143309da` |
| `prototypes_meta.json` | week2 | 0.0 | — |  | `2d6c1d5f53019bda` |
| `test_scores.head.csv` | week2 | 0.0 | 10 |  | `4413c269ce27a11c` |
| `test_scores.parquet` | week2 | 2.2 | — |  | `0525144c96bb4d4a` |
| `zeroday_scores.head.csv` | week2 | 0.0 | 10 |  | `336919481ebfd100` |
| `zeroday_scores.parquet` | week2 | 0.1 | — |  | `15089239ed8647d8` |

## Edge-IIoTset
- **Official:** <https://www.kaggle.com/datasets/mohamedamineferrag/edgeiiotset-cyber-security-dataset-of-iot-iiot>
- **Source:** Kaggle: mohamedamineferrag/edgeiiotset-cyber-security-dataset-of-iot-iiot
- **Paper:** Ferrag et al., 2022 (IEEE Access / TechRxiv)
- Files: 108 · 10.81 GB

| file | kind | MB | rows | used | sha256 (16) |
|---|:--:|---:|---:|:--:|---|
| `Backdoor_attack.csv` | raw | 17.9 | 24,862 |  | `a3da7bfd919c5f23` |
| `DDoS_HTTP_Flood_attack.csv` | raw | 95.7 | 229,022 |  | `526ef4221d74c046` |
| `DDoS_ICMP_Flood_attack.csv` | raw | 892.1 | 2,914,354 |  | `bd3a180a18e33197` |
| `DDoS_TCP_SYN_Flood_attack.csv` | raw | 941.2 | 2,020,120 |  | `623e8a331af6412b` |
| `DDoS_UDP_Flood_attack.csv` | raw | 900.2 | 3,201,626 |  | `62dcd279cd2068d2` |
| `MITM_attack.csv` | raw | 0.3 | 1,229 |  | `c4fd9f0d33c1bcbf` |
| `OS_Fingerprinting_attack.csv` | raw | 0.3 | 1,001 |  | `b2dc428e1b5159cc` |
| `Password_attack.csv` | raw | 653.3 | 1,053,385 |  | `e8458c89e7170622` |
| `Port_Scanning_attack.csv` | raw | 7.3 | 22,564 |  | `26f7f094254daa23` |
| `Ransomware_attack.csv` | raw | 7.6 | 10,925 |  | `60fa5257c73f0eef` |
| `SQL_injection_attack.csv` | raw | 26.9 | 51,203 |  | `59d62ccfab6b708c` |
| `Uploading_attack.csv` | raw | 17.5 | 37,634 |  | `f65ae75444183004` |
| `Vulnerability_scanner_attack.csv` | raw | 175.7 | 145,869 |  | `5b8d9bca352875d9` |
| `XSS_attack.csv` | raw | 7.0 | 15,915 |  | `acce72d7e9f8d373` |
| `Distance.csv` | raw | 366.1 | 1,143,540 |  | `067fcf364a6c4e35` |
| `Flame_Sensor.csv` | raw | 343.5 | 1,070,196 |  | `e0f6812bd54e564d` |
| `Heart_Rate.csv` | raw | 52.6 | 165,319 |  | `f5104511c7b67988` |
| `IR_Receiver.csv` | raw | 412.7 | 1,307,778 |  | `40325a578b4edc47` |
| `Modbus.csv` | raw | 67.9 | 159,502 |  | `6ae11be7ebd50642` |
| `Soil_Moisture.csv` | raw | 381.6 | 1,192,777 |  | `d3bf5662fd28b515` |
| `Sound_Sensor.csv` | raw | 479.0 | 1,512,883 |  | `1ac318ea539be09a` |
| `Temperature_and_Humidity.csv` | raw | 922.6 | 1,615,722 |  | `2b48ddce8f1d60db` |
| `Water_Level.csv` | raw | 731.5 | 2,295,288 |  | `19153cba2da0c69e` |
| `phValue.csv` | raw | 237.3 | 746,908 |  | `7cd2d143bd079f2a` |
| `DNN-EdgeIIoT-dataset.csv` | raw | 1217.4 | 2,219,201 | ✓ | `1d3ef6c7cc22784a` |
| `ML-EdgeIIoT-dataset.csv` | raw | 82.2 | 157,800 | ✓ | `53101fad091af20b` |
| `Edge-IIoTset.zip` | zip | 1746.6 | — |  | `42df619d4a222c5a` |
| `Edge-IIoTset_clean.parquet` | processed | 3.5 | — |  | `81cac58f3ccc5f13` |
| `Edge-IIoTset_clean_meta.json` | processed | 0.0 | — |  | `cf630e60108b9aed` |
| `Edge-IIoTset_sample.csv` | processed | 0.3 | 1,000 |  | `e21c1aa1b077ccca` |
| `calibration.parquet` | qadcp | 0.4 | — |  | `36233953095a2ff5` |
| `feature_groups.json` | qadcp | 0.0 | — |  | `c48070e36552bdd1` |
| `pca_baseline.json` | qadcp | 0.0 | — |  | `50b96aa795de4068` |
| `qadcp_report.json` | qadcp | 0.0 | — |  | `06009dcdd8debdfd` |
| `pca8_calibration.parquet` | qadcp | 1.0 | — |  | `91aeb6ecf6fa26af` |
| `pca8_test.parquet` | qadcp | 1.0 | — |  | `e5b6326722cc1fd1` |
| `pca8_train.parquet` | qadcp | 7.3 | — |  | `362b8bde365fe204` |
| `pca8_val.parquet` | qadcp | 1.0 | — |  | `4b496115032bcd70` |
| `pca8_zeroday.parquet` | qadcp | 0.8 | — |  | `a01843a964053e37` |
| `q12_calibration.parquet` | qadcp | 0.1 | — |  | `96f34beebbd3369b` |
| `q12_test.parquet` | qadcp | 0.1 | — |  | `352e52e11f7d2caf` |
| `q12_train.parquet` | qadcp | 0.4 | — |  | `ff31ce788720be30` |
| `q12_val.parquet` | qadcp | 0.1 | — |  | `4a101446857aa239` |
| `q12_zeroday.parquet` | qadcp | 0.0 | — |  | `92f16f9264c066c9` |
| `q16_calibration.parquet` | qadcp | 0.1 | — |  | `cddd48114741c904` |
| `q16_test.parquet` | qadcp | 0.1 | — |  | `42cbe1483d1e4c11` |
| `q16_train.parquet` | qadcp | 0.5 | — |  | `5a0f34a5652f07ee` |
| `q16_val.parquet` | qadcp | 0.1 | — |  | `db649b5235770cad` |
| `q16_zeroday.parquet` | qadcp | 0.0 | — |  | `4838dc5c17443a6e` |
| `q4_calibration.parquet` | qadcp | 0.0 | — |  | `023d6408915e785b` |
| `q4_test.parquet` | qadcp | 0.0 | — |  | `e3c2f08f0af254c0` |
| `q4_train.parquet` | qadcp | 0.0 | — |  | `c1cd66f7e4ee0c32` |
| `q4_val.parquet` | qadcp | 0.0 | — |  | `80b774f8525af65b` |
| `q4_zeroday.parquet` | qadcp | 0.0 | — |  | `a70a932821248b0c` |
| `q8_calibration.parquet` | qadcp | 0.0 | — |  | `063dd6e7e240a9d4` |
| `q8_test.parquet` | qadcp | 0.0 | — |  | `61f86e6a8ef3d99d` |
| `q8_train.parquet` | qadcp | 0.0 | — |  | `a0408502a984fbf9` |
| `q8_val.parquet` | qadcp | 0.0 | — |  | `4c12c99dfc4d746c` |
| `q8_zeroday.parquet` | qadcp | 0.0 | — |  | `84646093dd65af89` |
| `qubit_budgets.json` | qadcp | 0.0 | — |  | `a30515c2cb65ad22` |
| `scalers.json` | qadcp | 0.0 | — |  | `5322b1c60f4e4174` |
| `test.parquet` | qadcp | 0.4 | — |  | `ea29fa0eef8d7216` |
| `train.parquet` | qadcp | 2.3 | — |  | `5b65cb606e2f6e86` |
| `train_balanced.parquet` | qadcp | 2.9 | — |  | `fadd5b1167db13a6` |
| `val.parquet` | qadcp | 0.4 | — |  | `21b2b63d904c4f3d` |
| `zero_day_tiers.json` | qadcp | 0.0 | — |  | `6947630556786610` |
| `zeroday.parquet` | qadcp | 0.3 | — |  | `6ca14510fc008dfb` |
| `Edge-IIoTset_unified.parquet` | unified | 0.2 | — |  | `7b5258969988a294` |
| `Edge-IIoTset_unified_meta.json` | unified | 0.0 | — |  | `88a818d60c7412bc` |
| `calibration.parquet` | unified | 0.0 | — |  | `9aa432001798a513` |
| `encoders.json` | unified | 0.0 | — |  | `f487a13470d08aec` |
| `feature_groups.json` | unified | 0.0 | — |  | `f66eadb49a19f16e` |
| `pca_baseline.json` | unified | 0.0 | — |  | `2553162bf7123ce0` |
| `qadcp_report.json` | unified | 0.0 | — |  | `72df6349122c7329` |
| `pca8_calibration.parquet` | unified | 0.1 | — |  | `dbdae06b4851643d` |
| `pca8_test.parquet` | unified | 0.1 | — |  | `650caea5872d7c81` |
| `pca8_train.parquet` | unified | 0.9 | — |  | `150cb9efc6b7cd6f` |
| `pca8_val.parquet` | unified | 0.1 | — |  | `58ac1bce9957bfce` |
| `pca8_zeroday.parquet` | unified | 0.0 | — |  | `6ee6204c9da7e735` |
| `q12_calibration.parquet` | unified | 0.0 | — |  | `8db9f11aea45af42` |
| `q12_test.parquet` | unified | 0.0 | — |  | `86d75cd17bd51c66` |
| `q12_train.parquet` | unified | 0.1 | — |  | `2f25d010877d9e0e` |
| `q12_val.parquet` | unified | 0.0 | — |  | `bfef007faf2230b0` |
| `q12_zeroday.parquet` | unified | 0.0 | — |  | `fd13d52672dafda2` |
| `q16_calibration.parquet` | unified | 0.0 | — |  | `37b77ddbc6b9eb45` |
| `q16_test.parquet` | unified | 0.0 | — |  | `6330626442449906` |
| `q16_train.parquet` | unified | 0.1 | — |  | `1217b80e520cd306` |
| `q16_val.parquet` | unified | 0.0 | — |  | `9bab9a27c87af1d5` |
| `q16_zeroday.parquet` | unified | 0.0 | — |  | `d8ceb3c0e67d57c4` |
| `q4_calibration.parquet` | unified | 0.0 | — |  | `2a9fd111f9c30f2c` |
| `q4_test.parquet` | unified | 0.0 | — |  | `613dfae7eeb89c0c` |
| `q4_train.parquet` | unified | 0.1 | — |  | `939e26f32babfff5` |
| `q4_val.parquet` | unified | 0.0 | — |  | `f851300705a82c46` |
| `q4_zeroday.parquet` | unified | 0.0 | — |  | `5993345f432364ac` |
| `q8_calibration.parquet` | unified | 0.0 | — |  | `efeb7ed9c80f729a` |
| `q8_test.parquet` | unified | 0.0 | — |  | `2866b2439992c934` |
| `q8_train.parquet` | unified | 0.1 | — |  | `bb4fc8cf7600b5d7` |
| `q8_val.parquet` | unified | 0.0 | — |  | `f121c836cd2f1ec8` |
| `q8_zeroday.parquet` | unified | 0.0 | — |  | `a278eff011105c8d` |
| `qubit_budgets.json` | unified | 0.0 | — |  | `7df30b00833f6da3` |
| `scalers.json` | unified | 0.0 | — |  | `fd54c9ee049a1c61` |
| `test.parquet` | unified | 0.0 | — |  | `db673c142c603053` |
| `train.parquet` | unified | 0.1 | — |  | `98e15222bd5978ec` |
| `train_balanced.parquet` | unified | 0.1 | — |  | `bbd1232ed54c86ea` |
| `val.parquet` | unified | 0.0 | — |  | `d0da1f6d7bf4d5c2` |
| `validation_report.json` | unified | 0.0 | — |  | `595d52794f35a195` |
| `zero_day_tiers.json` | unified | 0.0 | — |  | `7c6f66f326979dff` |
| `zeroday.parquet` | unified | 0.0 | — |  | `0abde204bf412181` |

## UNSW-NB15
- **Official:** <https://research.unsw.edu.au/projects/unsw-nb15-dataset>
- **Source:** Kaggle mirror: UNSW-NB15 complete (exact slug to confirm — several mirrors exist)
- **Paper:** Moustafa & Slay, 2015 (MilCIS)
- Files: 111 · 0.94 GB

| file | kind | MB | rows | used | sha256 (16) |
|---|:--:|---:|---:|:--:|---|
| `NUSW-NB15_features.csv` | raw | 0.0 | 49 | ✓ | `c55f19cceebb6360` |
| `UNSW-NB15_1.csv` | raw | 169.0 | 700,001 | ✓ | `7d851bbeabd27894` |
| `UNSW-NB15_2.csv` | raw | 165.2 | 700,001 | ✓ | `6130ad02873cc606` |
| `UNSW-NB15_3.csv` | raw | 154.6 | 700,001 | ✓ | `ae990a96c3dfcd42` |
| `UNSW-NB15_4.csv` | raw | 97.6 | 440,044 | ✓ | `cdf563692d51d405` |
| `UNSW-NB15_LIST_EVENTS.csv` | raw | 0.0 | 208 |  | `5b40f8128e2c87e6` |
| `UNSW_NB15_testing-set.csv` | raw | 32.3 | 175,341 | ✓ | `bec7dd5ec88dc2a0` |
| `UNSW_NB15_training-set.csv` | raw | 15.4 | 82,332 | ✓ | `734fe6642edf758f` |
| `UNSW-NB15.zip` | zip | 156.3 | — |  | `d923de23e2378ff9` |
| `UNSW-NB15_clean.parquet` | processed | 14.2 | — |  | `8b01213ccc4aa98a` |
| `UNSW-NB15_clean_meta.json` | processed | 0.0 | — |  | `0783b8c9c8210476` |
| `UNSW-NB15_sample.csv` | processed | 0.5 | 1,000 |  | `bbbbdb9d73781127` |
| `calibration.parquet` | qadcp | 1.3 | — |  | `f4327d4266407dda` |
| `feature_groups.json` | qadcp | 0.0 | — |  | `ba7a73f3817900ea` |
| `pca_baseline.json` | qadcp | 0.0 | — |  | `13544e10047491d0` |
| `qadcp_report.json` | qadcp | 0.0 | — |  | `36a029e97fb50d85` |
| `pca8_calibration.parquet` | qadcp | 1.0 | — |  | `8e4ac714527ade64` |
| `pca8_test.parquet` | qadcp | 1.0 | — |  | `b741e2ec6afa34b7` |
| `pca8_train.parquet` | qadcp | 6.9 | — |  | `305b1994c98d52e9` |
| `pca8_val.parquet` | qadcp | 1.0 | — |  | `c54b12f9ffb9574d` |
| `pca8_zeroday.parquet` | qadcp | 0.1 | — |  | `ed0cfaf51b95e02f` |
| `q12_calibration.parquet` | qadcp | 0.6 | — |  | `0140536f34b581d2` |
| `q12_test.parquet` | qadcp | 0.6 | — |  | `5a4cf05affb9039c` |
| `q12_train.parquet` | qadcp | 4.0 | — |  | `13cfaf8b6a0208cc` |
| `q12_val.parquet` | qadcp | 0.6 | — |  | `be80c29686ce0a49` |
| `q12_zeroday.parquet` | qadcp | 0.1 | — |  | `97dd607fdaa9e825` |
| `q16_calibration.parquet` | qadcp | 0.8 | — |  | `6ee843292050036b` |
| `q16_test.parquet` | qadcp | 0.8 | — |  | `abba9d6e75213d83` |
| `q16_train.parquet` | qadcp | 5.3 | — |  | `90ba741997b75235` |
| `q16_val.parquet` | qadcp | 0.8 | — |  | `2eee860440d29f12` |
| `q16_zeroday.parquet` | qadcp | 0.1 | — |  | `eca34ed052bec9d6` |
| `q4_calibration.parquet` | qadcp | 0.1 | — |  | `7e06aefa14d2c2e0` |
| `q4_test.parquet` | qadcp | 0.1 | — |  | `6f7267dcf96dcd2f` |
| `q4_train.parquet` | qadcp | 0.9 | — |  | `d7c897ad306148aa` |
| `q4_val.parquet` | qadcp | 0.1 | — |  | `192b092dad91ad62` |
| `q4_zeroday.parquet` | qadcp | 0.0 | — |  | `ffb4da5780d2b1c1` |
| `q8_calibration.parquet` | qadcp | 0.4 | — |  | `0f4d8170e10f1d71` |
| `q8_test.parquet` | qadcp | 0.4 | — |  | `cf10350687f7cfa9` |
| `q8_train.parquet` | qadcp | 2.4 | — |  | `489ce3d6573771c4` |
| `q8_val.parquet` | qadcp | 0.4 | — |  | `7ac0dc40251b78c6` |
| `q8_zeroday.parquet` | qadcp | 0.0 | — |  | `52d7016906b52445` |
| `qubit_budgets.json` | qadcp | 0.0 | — |  | `975ec339033388f9` |
| `scalers.json` | qadcp | 0.0 | — |  | `b360b07a48065bee` |
| `test.parquet` | qadcp | 1.3 | — |  | `5b06eb86ae1ddfe0` |
| `train.parquet` | qadcp | 9.0 | — |  | `b983ed9ee36807a3` |
| `train_balanced.parquet` | qadcp | 6.3 | — |  | `6fb3e0f8439b7a27` |
| `val.parquet` | qadcp | 1.3 | — |  | `d2bcc57cc0a8f3fd` |
| `zero_day_tiers.json` | qadcp | 0.0 | — |  | `720c73aaeee29270` |
| `zeroday.parquet` | qadcp | 0.2 | — |  | `8bb169a6ab7797f9` |
| `UNSW-NB15_unified.parquet` | unified | 6.5 | — |  | `91896a181818199d` |
| `UNSW-NB15_unified_meta.json` | unified | 0.0 | — |  | `a270fcda65733c1c` |
| `calibration.parquet` | unified | 0.7 | — |  | `71b70c6952f4f322` |
| `encoders.json` | unified | 0.0 | — |  | `eae35b61c541fbbb` |
| `feature_groups.json` | unified | 0.0 | — |  | `78eb1b1535b98a80` |
| `pca_baseline.json` | unified | 0.0 | — |  | `93e3e00257a9545d` |
| `qadcp_report.json` | unified | 0.0 | — |  | `e48542a44b9093dc` |
| `pca8_calibration.parquet` | unified | 0.8 | — |  | `04c5bad78715dc3b` |
| `pca8_test.parquet` | unified | 0.8 | — |  | `0ef98312d2850e3f` |
| `pca8_train.parquet` | unified | 5.8 | — |  | `13256c7a7921f8bf` |
| `pca8_val.parquet` | unified | 0.8 | — |  | `99e4fc983c4aa6c5` |
| `pca8_zeroday.parquet` | unified | 0.1 | — |  | `1d44cac6589685fe` |
| `q12_calibration.parquet` | unified | 0.7 | — |  | `1f3e70204cba85d8` |
| `q12_test.parquet` | unified | 0.7 | — |  | `c43eac1a3c5225cd` |
| `q12_train.parquet` | unified | 4.4 | — |  | `093ec77f9009f2dc` |
| `q12_val.parquet` | unified | 0.7 | — |  | `f9add7b9b79dfc40` |
| `q12_zeroday.parquet` | unified | 0.1 | — |  | `01c31365ec0d65f7` |
| `q16_calibration.parquet` | unified | 0.7 | — |  | `56c93a4adf76315d` |
| `q16_test.parquet` | unified | 0.7 | — |  | `f309c94e480c2939` |
| `q16_train.parquet` | unified | 4.5 | — |  | `1e291eafbb5685d1` |
| `q16_val.parquet` | unified | 0.7 | — |  | `0836cede729d7d32` |
| `q16_zeroday.parquet` | unified | 0.1 | — |  | `b4a8536bf3cb38a2` |
| `q4_calibration.parquet` | unified | 0.4 | — |  | `125ff9eadd3fd1c4` |
| `q4_test.parquet` | unified | 0.4 | — |  | `8e613056be55ab03` |
| `q4_train.parquet` | unified | 2.7 | — |  | `0df9a5ebac40ddff` |
| `q4_val.parquet` | unified | 0.4 | — |  | `9b57d08005c5957c` |
| `q4_zeroday.parquet` | unified | 0.0 | — |  | `50754aae1f65cb37` |
| `q8_calibration.parquet` | unified | 0.5 | — |  | `c110b629c2520a1b` |
| `q8_test.parquet` | unified | 0.5 | — |  | `47272c8de3f3cdb7` |
| `q8_train.parquet` | unified | 3.6 | — |  | `9b20811ecd6cea43` |
| `q8_val.parquet` | unified | 0.5 | — |  | `89dc7e84421b54b5` |
| `q8_zeroday.parquet` | unified | 0.1 | — |  | `56e97227286fc7be` |
| `qubit_budgets.json` | unified | 0.0 | — |  | `bea5054592d8fabd` |
| `scalers.json` | unified | 0.0 | — |  | `57d746240952aeb6` |
| `test.parquet` | unified | 0.7 | — |  | `3ad6fa97fd7633a1` |
| `train.parquet` | unified | 4.5 | — |  | `fe9555c79d9deecc` |
| `train_balanced.parquet` | unified | 3.3 | — |  | `3245c95963dc08b3` |
| `val.parquet` | unified | 0.7 | — |  | `642cc9c9a6b2aaa6` |
| `validation_report.json` | unified | 0.0 | — |  | `17de76f499e96409` |
| `zero_day_tiers.json` | unified | 0.0 | — |  | `14a0f083e07702d4` |
| `zeroday.parquet` | unified | 0.1 | — |  | `16842ae614ab87a1` |
| `calibration.csv` | week2 | 2.8 | 10,112 |  | `a2a020c2ddeb45da` |
| `partition_meta.json` | week2 | 0.0 | — |  | `e9400cb0e3a53900` |
| `test.csv` | week2 | 2.8 | 10,086 |  | `fe08553d2a1fcdad` |
| `train.csv` | week2 | 22.3 | 81,215 |  | `b0304194dcc656de` |
| `zeroday.csv` | week2 | 0.3 | 1,216 |  | `73406316ae0dec45` |
| `adversarial_source_pool.csv` | week2 | 0.3 | 956 |  | `d8b5892df2cd3fde` |
| `eval_clean.csv` | week2 | 0.8 | 2,372 |  | `1ef59ee6f99e539a` |
| `rq3_schema.json` | week2 | 0.0 | — |  | `68b6f4433087bdb5` |
| `autoencoder.joblib` | baseline | 0.0 | — |  | `81ddc1e05937ece8` |
| `isolation_forest.joblib` | baseline | 3.8 | — |  | `412d795c9fe596fe` |
| `ocsvm.joblib` | baseline | 0.0 | — |  | `c3ef036ebbbfa7fc` |
| `predictions.csv` | baseline | 1.4 | 11,302 |  | `a980295cf49b76b0` |
| `results.json` | baseline | 0.0 | — |  | `0082430a95b18c88` |
| `xgboost_detector.json` | baseline | 4.9 | — |  | `bc4118d67d7a1972` |
| `calibration_scores.head.csv` | week2 | 0.0 | 10 |  | `3ad9f3261845c653` |
| `calibration_scores.parquet` | week2 | 1.6 | — |  | `78bb81b44620121a` |
| `prototypes_meta.json` | week2 | 0.0 | — |  | `c5b8b86f39531f04` |
| `test_scores.head.csv` | week2 | 0.0 | 10 |  | `cd65a1fa43731bdc` |
| `test_scores.parquet` | week2 | 1.6 | — |  | `105538e05417b046` |
| `zeroday_scores.head.csv` | week2 | 0.0 | 10 |  | `fc10c2dae43bd67b` |
| `zeroday_scores.parquet` | week2 | 0.2 | — |  | `560c492256faa74e` |

## Concerns & Recommendations
- **Mirror/slug ambiguity:** several datasets have many Kaggle mirrors (UNSW-NB15: alextamboli, primus11, harshwardhanbhangale…); the exact download slug for some is unconfirmed. The **official URL + SHA-256** here are authoritative — pin by checksum, not slug.
- **Verify before training:** all three members run `--verify` before any experiment; a non-zero mismatch means someone has a different variant/mirror → re-sync from the pinned source.
- **Curated outputs — pinned:** each dataset's `processed/*_clean.parquet` (Day-3) **and** its `qadcp/` splits + `quantum/` tensors (Day-4/5, incl. the `pca8_*` baseline) are hashed here too, so Team B/C consume checksum-pinned curated data — not just the raw.
- **Classical baselines — pinned:** Week-2 `baselines/<name>/` model, prediction, and result artifacts are included for byte-identical handoff and audit.
- **TON_IoT variant & CIC mirror:** row counts are valid variants/mirror (not errors); this manifest records exactly which bytes we standardized on.
