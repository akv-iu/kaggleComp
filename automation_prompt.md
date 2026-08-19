# Kaggriculture strategy proposal

You are producing one read-only proposal. You cannot use tools, edit files,
benchmark, submit, or request more turns. Everything relevant is included below.

Choose the smallest evidence-backed change to `main.py`. Prefer the first viable
item in `candidateBacklog`, but do not repeat an attempt unless its recorded retry
condition is now satisfied. Compare our farm with the replay winner in assets,
cash timing, production, logistics, and market exposure. Treat the competition
configuration facts as authoritative.

Return `status: "wait"` when the evidence is too weak or every viable idea is a
repeat. Otherwise return exactly one `status: "proposal"` with:

- a short title and falsifiable hypothesis;
- 2-5 numerical evidence statements;
- one git-compatible unified diff that modifies only existing `main.py`, with
  `diff --git`, `--- a/main.py`, and `+++ b/main.py` headers;
- a Kaggle message under 200 characters;
- the condition that would justify retrying after rejection.

The patch must be minimal and self-contained. Do not change tests, the evaluator,
the loop, ledgers, or runtime files. Do not combine hypotheses. Never claim the
patch is safe merely because it is small; connect it to the measured mechanism.
