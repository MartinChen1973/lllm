# Test Data for Ragas Evaluation

## Context Precision Demonstrations

| Rows | Scenario | Expected |
|------|----------|----------|
| 5–6 | **Japan capital**: Row 5 has relevant doc first `[Tokyo, Sydney, Paris]`; Row 6 has relevant doc last `[Sydney, Paris, Tokyo]` | Row 5: high precision; Row 6: lower precision |
| 9 | **France capital**: Only irrelevant docs `[Berlin, Rome]` | Zero precision |

## Context Recall Demonstrations

| Rows | Scenario | Expected |
|------|----------|----------|
| 7 | **France capital**: Full context includes both claims (Paris + Eiffel Tower) | High recall |
| 8 | **France capital**: Partial context—only "Paris is capital", missing "Eiffel Tower" claim from ground_truth | Lower recall |
| 9 | **France capital**: No relevant context | Zero recall |

## Data Source

The script loads from `data_samples.json`. The original `data_samples.csv` (3 rows) is kept for reference but is not used when the JSON file exists.
