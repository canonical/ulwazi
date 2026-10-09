# Test infrastructure

These tests check the tooling that runs and reports the other tests: the
category recap, the live progress estimate, and the coverage metrics. They
don't build or render the theme. They are the only tests in the "Test
infrastructure" recap line, which has no category number because it isn't one
of the {doc}`testing strategy <../testing-strategy>` categories. All of them
are fast and run with `make test`.

## Reporting and progress

`tests/test_test_reporting.py` checks the behaviour described in
{ref}`test-output-convention` and {ref}`test-progress-estimate`. Most tests
call the reporting functions in `tests/conftest.py` directly, with fake
reports. The last test runs a real pytest session.

| Test | What it checks |
| --- | --- |
| `test_reporting_category_matches_test_and_tier` | Test files map to their category and tier, including the slow-tier override for `test_layout_smoke.py`. An unmapped file maps to "Other tests". |
| `test_responsive_recap_counts_each_parameter_and_accessibility_separately` | Each parameter counts as its own case, and different categories get separate lines. |
| `test_category_recap_mixed_outcomes` | Failures, fixture errors, skips and unfinished cases each appear in the breakdown. |
| `test_category_recap_separates_tiers_and_does_not_count_xfails_as_passes` | An expected failure (`xfail`) counts as skipped, not passed. Passing setup alone doesn't count. |
| `test_category_recap_combines_successful_tiers` | Fast and slow results share one line. |
| `test_category_recap_failure_in_one_tier_keeps_other_tier_green` | A failing tier doesn't hide a passing tier on the same line. |
| `test_unregistered_cases_report_individual_ids_and_outcomes` | Each case from an unmapped file is listed by its pytest ID, with its outcome. |
| `test_unregistered_cases_do_not_change_registered_category_count` | Unmapped cases don't change the counts of mapped categories. |
| `test_recap_reserves_green_for_passing_results` | Only the passing count and `PASSED` are green. Failures are red, and category names are bold. |
| `test_live_progress_estimates_time_left_from_previous_durations` | The time left adds up previous durations and uses an average for new tests. Nothing is shown when there's no data. |
| `test_new_file_appears_by_name_in_actual_pytest_output` | In a real pytest run, a new unmapped file appears in the recap by test ID, with no setup. |

These tests don't check terminal drawing, such as escape codes or line width,
or behaviour with xdist. To see the real output, run `make test` in a terminal.

## Coverage metrics

`tests/test_coverage_metrics.py` checks the helpers behind the three
percentages described in {doc}`coverage`, using small sample files in a
temporary folder.

| Test | What it checks |
| --- | --- |
| `test_nested_v8_ranges_do_not_count_unexecuted_lines` | A function that never ran isn't counted as covered, even inside a script that did run. |
| `test_v8_ranges_use_utf16_offsets_and_skip_comments` | Line numbers stay correct after non-ASCII characters, and comment lines aren't counted. |
| `test_js_report_includes_unvisited_theme_scripts` | A theme script that no page loaded counts as 0%, rather than being left out. |
| `test_final_summary_uses_aggregate_js_and_python_line_rates` | The totals count lines across all files instead of averaging per-file percentages. Python branch counts are kept out of the line percentage. |
| `test_final_summary_rejects_incomplete_js_report` | A JavaScript report that is missing a theme script stops the summary instead of producing a higher percentage. |
| `test_pr_coverage_compares_unrounded_percentages` | A decrease hidden by rounding to one decimal place still fails the pull request check. |
| `test_pr_coverage_skips_unavailable_baseline` | A missing baseline skips the comparison instead of counting as 0%. |

These tests don't run Chromium or coverage.py; `make test-coverage` does.

## Supporting modules

| Module | Role |
| --- | --- |
| `tests/conftest.py` | Sets up the shared docs build, assigns test categories, and produces the recap, the live progress estimate and the feature coverage results. |
| `tests/js_coverage.py` | Converts Chromium's coverage data into line coverage for the theme's scripts. |
| `tests/coverage_summary.py` | Prints the three coverage figures at the end of `make test-coverage`. |
| `tests/pr_coverage.py` | Compares a pull request's coverage with its base revision in the `Coverage` workflow. |

## When to add a test here

Add or update a test here when you change the recap, the progress estimate, or
the coverage scripts. A new test file in this category needs a
`"Test infrastructure"` entry in `TEST_CATEGORIES`; see
{ref}`test-addition-checklist`.
