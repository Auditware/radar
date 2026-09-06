Fixtures for the test-code exclusion gate (`test_test_exclusion.py`).

`cfg_test_above_production.rs` places `#[cfg(test)] mod tests` above the
production code, which is the arrangement that breaks if items are pruned
before span enrichment: enrichment hands out the nth textual occurrence of an
identifier, so removing nodes first shifts the spans of everything below.
