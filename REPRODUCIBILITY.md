# Reproduce the checks

Run from the repository root with Python 3.11 or newer.

```sh
python3 -I scripts/verify_repository.py
python3 -I verification/src/replay.py
```

The standard-library replay compares the exact small-instance decisions for two contact orders per Set Cover instance. It retains the number of late leaves ignited, which distinguishes all legal late-leaf moves up to permutation. The simulation checks stopping after spread, the legality of each ignition, an example that succeeds at the final spread, and the complete illustrated schedule.

The [PDF build guide](paper/BUILD.md) and [figure guide](visualization/README.md) describe rebuilding those artifacts.
