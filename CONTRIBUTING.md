# Contributing

Run the tests, skill checker, example checker, and package smoke test described in the README before proposing a change. Keep rule behavior in the engine, not duplicated in skills or HTML. Add regression tests for behavior changes. Keep synthetic fixtures fictional and identify data provenance. Never commit real prospect runs, credentials, or private source material.

Schema changes must declare compatibility and update examples and tests. Generated artifacts should come from `generate_demo.py`, `generate_schemas.py`, and the CLI; document any intentional changes to expected demo counts. Don't add unimplemented connectors, simulated delivery claims, or performance claims unsupported by evidence.
