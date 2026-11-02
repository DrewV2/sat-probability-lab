# Progress notes

## Project goal

I'm working toward a SAT predictor that reports a useful range and makes its assumptions clear. Along the way, I'm practicing statistics, Python, SQL, and data analysis skills that also come up in my BioCosmos work.

The main focus is the probability model and eventually testing the score predictions against real results. The topic-search notebook is a side experiment with vectors and cosine similarity.

## Initial version — November 2, 2026

The current version includes:

- A probability model for confident answers, guesses, and Math fill-ins.
- An experimental conversion from answer counts to SAT points.
- DuckDB tables for attempts, inputs, settings, and predictions.
- Notebooks for the probability calculations, data analysis, and topic similarity.
- Synthetic data and export functions.

All 10 tests and all three notebooks ran successfully at this stage. That checks the implementation, but doesn't establish that the SAT score predictions are accurate. There isn't a real score dataset or a fitted conversion yet.

## Next experiment: confidence assumptions

I want to see how much the answer-count intervals change when I change the probability assigned to confident answers.

I'll keep the module counts fixed and compare probabilities of 0.90, 0.95, 0.99, and 1.00 in notebook 01. I'll record the low, median, and high counts for each section, then add a plot and a short discussion of the results. This will focus on answer counts before converting to SAT points.

**Status:** planned; no results yet.

## Questions I'm working through

- How closely does reported confidence match actual correctness?
- What happens to the intervals if mistakes are correlated?
- What practice-test data would be enough to start fitting a score conversion?
- How should I save experiment runs so I can compare settings without losing previous results?

## Future entries

For each experiment or change, I'll note what I tried, what happened, how I checked it, and what I want to investigate next.
