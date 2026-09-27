# Evaluation on IR-Plag

Pairs compared: 460 (original vs every other file, per case). Time: 84.8s.

Cells = % of pairs flagged. L1-L6 should be high (plagiarized); NON should be low (independent work).

## Structural

| Threshold | L1 | L2 | L3 | L4 | L5 | L6 | NON |
|---|---|---|---|---|---|---|---|
| 0.50 | 100% | 96% | 98% | 48% | 12% | 3% | 44% |
| 0.60 | 100% | 95% | 79% | 13% | 2% | 2% | 31% |
| 0.70 | 100% | 95% | 44% | 8% | 0% | 0% | 16% |
| 0.80 | 82% | 71% | 26% | 2% | 0% | 0% | 7% |

AUC per level (1.0 = perfect separation from independent work, 0.5 = coin flip): L1 0.97, L2 0.94, L3 0.81, L4 0.54, L5 0.37, L6 0.28

## Exact

| Threshold | L1 | L2 | L3 | L4 | L5 | L6 | NON |
|---|---|---|---|---|---|---|---|
| 0.50 | 100% | 27% | 25% | 10% | 0% | 0% | 3% |
| 0.60 | 100% | 18% | 19% | 0% | 0% | 0% | 1% |
| 0.70 | 83% | 9% | 14% | 0% | 0% | 0% | 1% |
| 0.80 | 73% | 5% | 14% | 0% | 0% | 0% | 0% |

AUC per level (1.0 = perfect separation from independent work, 0.5 = coin flip): L1 1.00, L2 0.69, L3 0.62, L4 0.46, L5 0.33, L6 0.27

## Semantic

| Threshold | L1 | L2 | L3 | L4 | L5 | L6 | NON |
|---|---|---|---|---|---|---|---|
| 0.85 | 18% | 14% | 12% | 3% | 3% | 3% | 9% |
| 0.90 | 7% | 2% | 0% | 0% | 0% | 0% | 3% |
| 0.95 | 2% | 0% | 0% | 0% | 0% | 0% | 0% |

AUC per level (1.0 = perfect separation from independent work, 0.5 = coin flip): L1 0.57, L2 0.54, L3 0.50, L4 0.44, L5 0.42, L6 0.43

