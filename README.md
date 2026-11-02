# SAT Probability Lab

I'm building a SAT predictor that estimates a likely low, median, and high score based on how someone thinks they performed on each module. The inputs distinguish between confident answers, guesses with different numbers of choices remaining, and Math fill-in responses.

This is a personal project where I'm applying statistics and computer science together. I'm also using it to get more comfortable with Python, Jupyter, DuckDB, SQL, and data visualization—topics relevant to my work on the BioCosmos subteam of the BioVision lab. The SAT project is independent of the lab, but gives me another setting to work with these concepts.

**The project is still in an early stage.** The answer-count model works under its stated assumptions. The SAT score conversion is experimental python.analysis.typeCheckingModeand has not been calibrated against actual scores.

## The approach

I model each answer as a Bernoulli random variable with a probability of being correct. For example, a uniform guess between two remaining choices has probability 1/2, provided the correct answer is still among them. Confident answers and uncertain fill-ins have adjustable probabilities.

Because those probabilities differ across questions, I use a Poisson-binomial distribution to calculate the possible numbers of correct answers. Dynamic programming computes that distribution without needing a simulation. I then use its quantiles to report a range rather than one predicted count.

Converting those counts into SAT points is a harder problem. The current version includes an approximate model for unknown pretest questions, Module 1-dependent routing, and route-specific score conversions. Those assumptions need real data before I can treat the output as a reliable SAT prediction.

## What's implemented

- Answer-count distributions for both modules of Reading & Writing and Math.
- Confidence, multiple-choice guessing, and Math fill-in categories.
- Low, median, and high estimates using configurable probability intervals.
- An optional experimental SAT score conversion.
- DuckDB storage for attempts, module inputs, settings, and predictions.
- Tests for the probability calculations and database operations.
- A separate study-topic search experiment using keyword vectors and cosine similarity.

The included examples are synthetic. There are no actual student score labels in the project yet.

## Notebooks

I use the notebooks to work through the math, inspect results, and record experiments.

| Notebook | Contents |
|---|---|
| [01: Probability and predictions](notebooks/01_probability_and_predictions.ipynb) | Probability model, derivations, score assumptions, and sensitivity analysis |
| [02: DuckDB workflows](notebooks/02_duckdb_workflows.ipynb) | Storing attempts, querying inputs, saving predictions, and defining evaluation metrics |
| [03: Vectors and similarity](notebooks/03_vectors_and_similarity.ipynb) | A side experiment with SAT study-topic search |

The similarity experiment helps me explore vector representations and SQL ranking. It uses keyword counts, not a pretrained embedding model, and is separate from the score predictor.

## Next steps

- [ ] Compare answer-count intervals at different confidence probabilities.
- [ ] Make it easier to enter and validate an attempt.
- [ ] Save separate experiment runs instead of overwriting previous predictions.
- [ ] Define a dataset format for practice attempts and actual scores.
- [ ] Fit a score conversion and evaluate it on held-out students and test forms.
- [ ] Measure interval coverage, interval width, and median prediction error.

I keep more detailed notes in [PROGRESS.md](PROGRESS.md).

## Running locally

The project requires Python 3.11 or later. From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m ipykernel install --prefix .venv --name sat-lab --display-name "SAT Lab (Python)"
jupyter lab
```

The notebook kernel is **SAT Lab (Python)**. In VS Code, select the project's `.venv/bin/python` interpreter.

`requirements.txt` lists dependency ranges. `requirements-lock.txt` records the environment used for verification on Python 3.14 and Linux.

## Project structure

```text
satlab/         Python model, database functions, and similarity code
notebooks/      Analysis and experiment notes
sql/            Analysis queries
tests/          Automated tests
tools/          Notebook execution check
PROGRESS.md     Progress notes and open questions
```

The local DuckDB files, generated exports in `artifacts/`, virtual environment, and caches are ignored by Git. The GitHub repository should start at `sat-probability-lab/`, rather than the enclosing workspace.

## Running checks

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python tools/check_notebooks.py
```

The second command runs the notebooks in fresh kernels and saves executed copies in `artifacts/executed/`. It needs the registered kernel and permission to start local Jupyter sockets.

## Limitations

The probability model assumes independent answers. Guessing probabilities also assume that the correct choice has not been eliminated and that the remaining choices are equally likely to be selected. The default confidence probability of 99% is an assumption, not a measured value.

The SAT score model uses an assumed routing function, linear conversions, route caps, and score noise. It also approximates the two unknown pretest positions in each module as a uniformly selected pair. SAT-point output requires `include_illustrative_scores=True` because these choices are not calibrated.

The total-score calculation assumes independence between sections. Low and high estimates are quantiles, not guaranteed bounds. The mathematical derivations support the calculations under these assumptions; actual prediction accuracy and interval coverage still need to be tested with real score data.

## References

- [College Board: How scores are calculated](https://satsuite.collegeboard.org/scores/what-scores-mean/how-scores-calculated)
- [College Board: Digital SAT Suite technical manual](https://research.collegeboard.org/media/pdf/Digital%20SAT%20Suite%20of%20Assessments%20Technical%20Manual-FINAL.pdf)
- [DuckDB Python API](https://duckdb.org/docs/stable/clients/python/overview)
- [DuckDB list functions](https://duckdb.org/docs/current/sql/functions/list)
- [Jupyter installation](https://jupyter.org/install)
