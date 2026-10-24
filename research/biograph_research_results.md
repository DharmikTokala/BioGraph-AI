# BioGraph AI — Final Benchmark Results

## Methods

BioGraph AI was evaluated on a final benchmark containing 100 drug–disease pairs: 50 known therapeutic relationships and 50 screened mismatched controls. The control set was filtered to remove pairs with direct clinical-stage evidence, clinical reports, or direct overlap between known drug targets and disease-associated targets.

Two scoring modes were evaluated:

1. **Full Evidence Model** — combines biological target overlap, literature evidence, clinical stage, and clinical-report information.
2. **Prediction Model** — excludes clinical stage and clinical-report information and uses biological and literature evidence only.

For each model, scores were compared between known therapeutic pairs and screened controls. A decision threshold was selected by maximizing F1 score on this benchmark. Performance was summarized using accuracy, precision, recall, F1 score, and ROC-AUC.

## Results

The Full Evidence Model produced a mean score of **91.44** for known therapeutic pairs and **23.48** for screened controls. With a threshold of **31**, it classified all 100 benchmark pairs correctly, corresponding to **100% accuracy, 1.00 precision, 1.00 recall, 1.00 F1 score, and ROC-AUC = 1.00**.

The Prediction Model, which did not use clinical stage or clinical-report counts, produced a mean score of **58.76** for known therapeutic pairs and **23.48** for screened controls. At the same threshold of **31**, it also classified all 100 benchmark pairs correctly, giving **100% accuracy, 1.00 precision, 1.00 recall, 1.00 F1 score, and ROC-AUC = 1.00**.

The prediction result is especially important because it shows that the benchmark separation did not depend entirely on direct clinical-development information. Known therapeutic relationships remained strongly separated from screened controls when the model used only biological-target and literature-derived features.

## Interpretation

These results show that BioGraph AI can separate the selected known therapeutic relationships from the selected screened controls in this benchmark. The result should be interpreted as evidence of benchmark discrimination, not proof that the system can prospectively discover effective drugs.

## Limitations

The benchmark is still relatively small and was assembled from known therapeutic examples rather than from a prospectively collected dataset. The screened controls are not experimentally proven negative relationships; they are mismatched pairs filtered to remove direct clinical evidence and target overlap. The threshold was selected on the same benchmark used for evaluation, so the reported classification metrics may overestimate performance on unseen data. Literature classification also relies partly on simple keyword heuristics and therefore cannot determine clinical efficacy.

A stronger future evaluation should use an independent held-out test set, temporal validation using historical data, or a benchmark containing failed clinical candidates and difficult biologically plausible negatives.

## Conclusion

BioGraph AI achieved complete separation between the 50 known therapeutic pairs and 50 screened controls in the final benchmark. Importantly, the reduced Prediction Model preserved this separation after clinical-stage and clinical-report features were removed, suggesting that biological and literature evidence contributed meaningful discriminatory signal. Further validation on independent and more difficult datasets is required before making claims about prospective drug-repurposing performance.
