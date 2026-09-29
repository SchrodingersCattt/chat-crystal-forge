# Structure examples

## DAP-4

[`structures/DAP-4.cif`](structures/DAP-4.cif) was supplied by the project owner
for repository tracking on 2026-09-29. It is an unchanged copy of the supplied
experimental CIF, including its original refinement metadata and embedded data.

- Size: 436,274 bytes.
- SHA-256: `3967afbcdbded81841ea31c89d2cfdf623c8f3264b208c3c8a2f6ae2a0f9ef5d`.
- CIF block: `DAP-4`.
- Declared total formula: `C6 H18 Cl3 N3 O12`.
- Declared moiety formula: `?` (unspecified).
- MCK's current disorder scan detects partial occupancy/disorder. This is an input
  for inspection and preparation testing, not an already repaired structure.

When using the inspection-preview implementation, run
`mat-chat ui examples/structures/DAP-4.cif` or
`mat-chat tui examples/structures/DAP-4.cif` from the repository root.
The preview copies inputs into its session; it does not modify this tracked original.
The current preview does not yet use `_chemical_formula_sum` when moiety is `?`,
so its formula-consistency prerequisite remains blocked for this input. That is
distinct from a parser failure; it must not be reported as a repaired/all-pass result.

The root `.gitattributes` disables line-ending conversion for these source CIFs.
Keep any generated candidates/reports in the ignored runtime directory, not over
this input. Preserve the original data attribution; the software MIT license does
not assign new terms to the source research data.

### Separate from the historical oracle fixture

This file differs from `external/mattervis/scripts/data/DAP-4.cif`, whose SHA-256
is `b126b65d267ae4a6930e203c2124af09c137d466d27613792f83cf519bbc454b`.
It must not overwrite that upstream fixture or be substituted under its expected
hash. The existing upstream oracle failure concerns a recorded MCK revision and
archived expected output; adding this example does not resolve that failure.