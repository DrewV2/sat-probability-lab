-- SELECT and aggregation: one row per attempt and section.
SELECT attempt_id, section,
       SUM(confident) AS confident_count,
       SUM(guess2 + guess3 + guess4) AS multiple_choice_guesses,
       SUM(fill_uncertain) AS uncertain_fill_ins
FROM module_inputs
GROUP BY attempt_id, section
ORDER BY attempt_id, section;

-- JOIN: attach prediction output to its source metadata.
SELECT a.attempt_id, a.student_id, a.test_form_id, a.is_synthetic,
       p.low, p.median, p.high, p.score_status
FROM attempts a JOIN predictions p USING (attempt_id)
ORDER BY a.attempt_id;

-- Evaluation scaffold. Demo rows are synthetic and have NULL labels: n = 0.
-- Even when labels exist, training/test leakage must be prevented BEFORE this query.
SELECT COUNT(*) AS n,
       AVG(CASE WHEN actual_rw + actual_math BETWEEN low AND high THEN 1.0 ELSE 0.0 END) AS coverage,
       AVG(high - low) AS mean_interval_width,
       AVG(ABS(median - (actual_rw + actual_math))) AS mean_absolute_error
FROM attempts JOIN predictions USING (attempt_id)
WHERE NOT is_synthetic AND actual_rw IS NOT NULL AND actual_math IS NOT NULL;
