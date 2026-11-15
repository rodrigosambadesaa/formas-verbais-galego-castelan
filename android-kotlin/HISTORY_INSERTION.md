# Historical chronology and preserving Git history

This client was written after the repository's 2022-dated historical series.
A date on a Git commit must not be treated as proof of when the code was
actually authored or tested. Do not rewrite the public `master` branch
without first preserving the original refs: rebasing its historical series
changes every descendant SHA (including the 2026 security patch and PR links).

The Android implementation is therefore proposed as a regular pull request.
A backdated commit inserted in the middle of the public graph is NOT created
by this PR. If a curator chooses to reconstruct a historical sequence,
do it in a separate audited branch and disclose that it is a reconstruction.
