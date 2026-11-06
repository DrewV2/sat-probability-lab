# Website plan

## Goal

I want to turn the Python model into a website where someone can enter their confidence counts for the whole SAT and see a low, median, and high prediction. This document records the product decisions so far and a proposed stack. The website is not implemented yet.

## Inputs and results

The calculator will have four module forms: two for Reading & Writing and two for Math.

Each module will collect counts for:

- Answers the user is 100% confident are correct.
- Guesses between two, three, or four choices.
- Answers known to be wrong or left blank, both counted as wrong.

Math will also have separate fill-in counts for 100% confident correct and 0% confident correct. The website will treat these as probabilities 1 and 0. It will not ask for an uncertain fill-in probability, even though the current Python library supports one.

Each question must appear in exactly one category. Reading & Writing module counts must total 27 and Math module counts must total 22, including fill-ins. I won't assume every Math module has a fixed fill-in count without a verified reason to enforce one.

The user will select the easier or harder Module 2 route separately for Reading & Writing and Math. The label will describe this as the route they believe they received.

The intended result is a low, median, and high total SAT score, with section results available for context. The current SAT-point conversion is still experimental. A website does not remove the need to calibrate and validate it.

## Optional contributions

Calculating a result will not save it to the contributions database. After seeing the result, the user can choose **Contribute this scenario**.

The aggregate statistic will be the arithmetic mean of contributed median predictions:

`average = sum(contributed median predictions) / number of contributions`

This is the average of scenario medians, not the median of all contributions. The display will include the contribution count and be labeled **Average predicted score of contributed scenarios**. With no contributions, it will show no data rather than a score of zero.

These are self-selected scenarios, potentially including several from one person. They do not describe a representative sample of SAT test takers or establish prediction accuracy. No accounts or identifying information are needed for the planned feature.

## Proposed stack

| Part | Technology | Role |
|---|---|---|
| Page structure | HTML | Labels, four module forms, route choices, and result sections |
| Appearance | CSS | Layout, spacing, colors, and mobile presentation |
| Browser behavior | JavaScript | Validate counts, send requests, and update the result display |
| Web backend | Python + FastAPI | Validate requests, call the Python model, and return structured results |
| Prediction logic | Existing `satlab` Python package | Keep the model reusable between notebooks and the website |
| Contribution storage | PostgreSQL | Store explicitly contributed inputs, prediction results, and model versions |
| Research | Jupyter + DuckDB | Continue experiments and analyze exported contribution data |
| Graphs | Browser chart library, to be chosen | Plot aggregate results once there is useful contributed data |

I'm proposing plain HTML, CSS, and JavaScript first so I can understand the browser code before deciding whether I need a frontend framework. FastAPI keeps the backend in Python. PostgreSQL is the proposed website database; the existing DuckDB files remain part of the analysis workflow.

FastAPI can serve the frontend files as well as the API. This allows the first version to use one web service with an attached PostgreSQL database. Hosting providers and a chart library can be chosen when the calculator works locally.

Technology choices in this section are proposals, not installed dependencies or completed features.

## Request flow

```text
Browser form
    → Python API validates counts and route selections
    → satlab calculates the distribution and quantiles
    → Browser displays low, median, and high

Only if the user selects Contribute this scenario:
    → Python API validates inputs and calculates the result again
    → PostgreSQL stores the contribution
    → Aggregate query returns the average median and contribution count
    → Browser updates the statistics display
```

The backend will calculate the saved prediction itself instead of trusting score values supplied by the browser. A single result should not be saved twice because of an accidental double-click.

## API sketch

These names are a starting point for implementation:

| Request | Purpose | Saves a contribution? |
|---|---|---|
| `POST /api/predict` | Calculate a range for the submitted module inputs | No |
| `POST /api/contributions` | Recalculate and store a voluntarily contributed scenario | Yes |
| `GET /api/stats` | Return the average contributed median and number of scenarios | No |

The contribution record should include a generated scenario ID, submission time, module counts, route selections, interval level, low/median/high results, model version, and model settings. Model versions need to be kept separate in summaries so changes in the prediction algorithm are not silently mixed together.

## Build order

1. Continue the Python experiments and define a function that accepts all four modules.
2. Build one HTML form, then expand it to the full input structure.
3. Add CSS and JavaScript validation.
4. Connect the forms to the Python prediction endpoint.
5. Add optional contribution storage and the aggregate statistic.
6. Add graphs and deploy a first version.


## References

- [MDN: HTML, CSS, and JavaScript basics](https://developer.mozilla.org/en-US/docs/Learn_web_development/Getting_started/Your_first_website)
- [FastAPI features and validation](https://fastapi.tiangolo.com/features/)
- [FastAPI static files](https://fastapi.tiangolo.com/tutorial/static-files/)
- [PostgreSQL overview](https://www.postgresql.org/about/)
