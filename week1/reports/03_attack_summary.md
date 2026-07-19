# Deliverable ③ — Attack Summary

**QS-Net / QuantumSentinel — Team A** · Week 1 · Day 1.
Attack taxonomy, class distributions, imbalance, a **unified attack ontology**, and **zero-day
candidates** across CIC-IoT2023, TON_IoT, BoT-IoT. Counts reproduced by
[`scripts/profile_datasets.py`](../scripts/profile_datasets.py) (see `reports/_generated/*_classdist.csv`).

## 1. Class counts per dataset

### CIC-IoT2023 — 7,845,673 rows, 34 fine classes (33 attacks + Benign)
Top/representative classes (full 34 in `ciciot2023_classdist.csv`):

| Class | Count | % | | Class | Count | % |
|---|---:|---:|---|---|---:|---:|
| DDoS-ICMP_Flood | 1,210,546 | 15.43 | | Recon-HostDiscovery | 22,550 | 0.29 |
| DDoS-UDP_Flood | 910,741 | 11.61 | | DoS-HTTP_Flood | 12,125 | 0.15 |
| DDoS-TCP_Flood | 756,122 | 9.64 | | VulnerabilityScan | 6,214 | 0.08 |
| DDoS-PSHACK/SYN/RSTFIN/SynIP | ~2.65 M | ~34 | | DictionaryBruteForce | 2,150 | 0.03 |
| DoS-UDP/TCP/SYN_Flood | ~1.35 M | ~17 | | SqlInjection / CommandInjection | 886 / 871 | 0.01 |
| **BenignTraffic** | **184,766** | **2.36** | | XSS / Backdoor_Malware | 608 / 574 | 0.01 |
| Mirai-greeth/udpplain/greip | ~442 k | ~5.6 | | Recon-PingSweep | 347 | 0.004 |
| MITM-ArpSpoofing | 51,897 | 0.66 | | **Uploading_Attack** | **208** | **0.003** |

### TON_IoT (Network) — 211,043 rows, 10 classes (9 attacks + normal)
| Class | Count | % | | Class | Count | % |
|---|---:|---:|---|---|---:|---:|
| **normal** | **50,000** | 23.69 | | password | 20,000 | 9.48 |
| backdoor | 20,000 | 9.48 | | ransomware | 20,000 | 9.48 |
| ddos | 20,000 | 9.48 | | scanning | 20,000 | 9.48 |
| dos | 20,000 | 9.48 | | xss | 20,000 | 9.48 |
| injection | 20,000 | 9.48 | | **mitm** | **1,043** | 0.49 |

### BoT-IoT — 73,370,443 rows, 5 categories / 8 subcategories
| Category | Count | % | | Subcategory | Count | % |
|---|---:|---:|---|---|---:|---:|
| DDoS | 38,532,480 | 52.52 | | UDP | 39,624,597 | 54.01 |
| DoS | 33,005,194 | 44.98 | | TCP | 31,863,600 | 43.43 |
| Reconnaissance | 1,821,639 | 2.48 | | Service_Scan | 1,463,364 | 1.99 |
| **Normal** | **9,543** | 0.013 | | OS_Fingerprint | 358,275 | 0.49 |
| **Theft** | **1,587** | 0.002 | | HTTP | 49,477 | 0.07 |
| | | | | Normal / Keylogging / Data_Exfiltration | 9,543 / 1,469 / **118** | — |

## 2. Class imbalance (majority : minority)

| Dataset | Majority class | Minority class | **Ratio** |
|---|---|---|---:|
| CIC-IoT2023 | DDoS-ICMP_Flood (1.21 M) | Uploading_Attack (208) | **≈ 5,820 : 1** |
| TON_IoT | normal (50 k) | mitm (1,043) | **≈ 48 : 1** |
| BoT-IoT | DDoS (38.5 M) | Theft/Data_Exfiltration (118) | **≈ 326,000 : 1** |
| BoT-IoT (binary) | attack (73.36 M) | normal (9,543) | **≈ 7,688 : 1** |

**Implication:** every dataset needs balancing, but with very different policies. BoT-IoT and
CIC-IoT2023 require aggressive majority **undersampling** while **preserving** rare classes (a
handful of Theft / Uploading / Backdoor samples); TON_IoT needs only mild rebalancing. Naïve global
resampling would destroy the rare attacks that matter most for zero-day detection.

## 3. Unified attack ontology (label harmonization → Day 6)

| Unified family | CIC-IoT2023 | TON_IoT | BoT-IoT |
|---|---|---|---|
| **Benign** | BenignTraffic | normal | Normal |
| **DDoS** | DDoS-ICMP/UDP/TCP/PSHACK/SYN/RSTFIN/SynIP/HTTP/SlowLoris/Frag… | ddos | DDoS (UDP/TCP/HTTP) |
| **DoS** | DoS-UDP/TCP/SYN/HTTP_Flood | dos | DoS (UDP/TCP/HTTP) |
| **Recon / Scanning** | Recon-Host/OS/Port/PingSweep, VulnerabilityScan | scanning | Reconnaissance (Service_Scan, OS_Fingerprint) |
| **Botnet (Mirai)** | Mirai-greeth/udpplain/greip | — | *(whole set is botnet)* |
| **Spoofing / MITM** | MITM-ArpSpoofing, DNS_Spoofing | mitm | — |
| **Injection / Web** | SqlInjection, CommandInjection, XSS, BrowserHijacking, Uploading_Attack | injection, xss | — |
| **Brute Force / Password** | DictionaryBruteForce | password | — |
| **Backdoor / Malware / Ransomware** | Backdoor_Malware | backdoor, ransomware | — |
| **Theft / Exfiltration** | (Uploading_Attack≈) | — | Theft: Keylogging, Data_Exfiltration |

Naming is inconsistent (`DDoS-ICMP_Flood` vs `ddos` vs `DDoS/UDP`; `Backdoor_Malware` vs `backdoor`),
so a canonical family map + a fine-label map are both required.

## 4. Zero-day candidates (→ Day-5 difficulty-aware splits)
Attacks that appear in **only one** of the three datasets are natural hold-outs for cross-dataset
zero-day evaluation (train on datasets that lack the family, test on the one that has it):

- **Mirai botnet variants** — CIC-IoT2023 only.
- **Ransomware** — TON_IoT only (among these three).
- **Theft: Keylogging & Data_Exfiltration** — BoT-IoT only (Data_Exfiltration = just 118 samples).
- **MITM / DNS spoofing** — CIC-IoT2023 & TON_IoT, absent in BoT-IoT.
- **Web/Injection family** — CIC-IoT2023 & TON_IoT, absent in BoT-IoT.

These, plus the ultra-rare tail classes (Uploading_Attack 208, Data_Exfiltration 118, Backdoor_Malware
574), are the "hard" difficulty tier for the Day-5 Easy/Medium/Hard zero-day benchmark.

## 5. Takeaways for the pipeline
1. Harmonize labels to the family ontology **and** keep a fine-label map (for granular evaluation).
2. Balance **per dataset**, protecting rare classes explicitly (no global resampling).
3. Reserve unique families (Mirai / Ransomware / Theft) as cross-dataset **zero-day** hold-outs.
4. Derive CIC-IoT2023's missing **7-category** and **binary** labels so all three align at coarse level.

## 6. Day-2 — Edge-IIoTset & UNSW-NB15 attack taxonomies
- **Edge-IIoTset (14 attacks + Normal, 24:1):** DDoS (UDP/ICMP/TCP/HTTP), SQL_injection, Uploading,
  XSS, Password, Backdoor, Ransomware, Port_Scanning, Vulnerability_scanner, MITM, Fingerprinting.
  Rare = Fingerprinting (1,001), MITM (1,214).
- **UNSW-NB15 (9 attacks + Normal):** Generic (58,871), Exploits (44,525), Fuzzers, DoS,
  Reconnaissance, Analysis, Backdoor(s), Shellcode, Worms (174). New families **Exploits, Generic,
  Fuzzers, Shellcode, Worms, Analysis** have **no equivalent** in the IoT datasets → strong
  **cross-domain zero-day** hold-outs.

**Ontology additions:** add Generic/Exploits/Fuzzers/Shellcode/Worms/Analysis (UNSW-NB15) as their own
families; map Edge-IIoTset onto existing families. **Normalize** UNSW "Backdoors"→"Backdoor" and fill
blank `attack_cat`→"Normal" *before* counting.

## Concerns & Recommendations
- **Concern:** label vocabularies now span 3 conventions; UNSW's blank-Normal + "Backdoor/Backdoors"
  will corrupt class counts if not normalized first.
- **Recommendation:** implement one `harmonize_labels()` (family + fine maps) applied uniformly;
  reserve UNSW-exclusive families and IoT-exclusive families (Mirai, Ransomware, Theft) as the
  difficulty-tiered **zero-day** benchmark (Day 5).

---
*Full distributions: `reports/_generated/ciciot2023_classdist.csv`, `toniot_network_classdist.csv`,
`botiot_category_classdist.csv`, `botiot_subcategory_classdist.csv`,
`edge_iiotset_classdist.csv`, `unsw_nb15_mlready_classdist.csv`, `unsw_nb15_raw_classdist.csv`.*
