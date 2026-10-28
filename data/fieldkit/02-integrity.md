# FieldKit: integrity checks

## Verifying a field bundle

FieldKit verifies every field bundle with a SHA-256 checksum before import.

The operator compares the computed checksum with the manifest. If the checksums differ, the bundle is quarantined for inspection. Retrying an import does not bypass the comparison.
