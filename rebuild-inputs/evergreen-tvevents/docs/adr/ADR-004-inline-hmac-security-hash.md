# ADR-004: Inline HMAC Security Hash Validation

## Status

Accepted

## Context

The legacy application validates TV identity using `cnlib.cnlib.token_hash.security_hash_match(tvid, h_value, salt_key)`. This function is part of the cnlib git submodule — a fragile dependency that requires `git submodule init/update` and `setup.py install`. The entire cnlib package is installed for this single function (plus Firehose and logging, which are being replaced separately). The HMAC algorithm is a standard hash comparison that can be implemented inline.

## Decision

Inline the HMAC security hash validation in a dedicated `security.py` module within the rebuilt service. Do not depend on cnlib for this functionality.

## Rationale

1. **Eliminates cnlib dependency** — The last remaining cnlib import is removed
2. **Transparent algorithm** — The hash validation logic is visible in the service source, not hidden in an external library
3. **Testable** — Can be unit tested with known tvid/hash/salt vectors
4. **Simple implementation** — Standard `hashlib.md5` (or equivalent) comparison using `hmac.compare_digest()` for constant-time comparison

## Implementation Notes

- The T1_SALT environment variable is the shared secret
- The hash algorithm must be verified against production behavior using known test vectors from `s3://cn-secure/salt_external_pillar/tvevents-development-iad.yaml`
- Use `hmac.compare_digest()` for constant-time string comparison to prevent timing attacks
- The `security.py` module should expose a single function: `validate_security_hash(tvid: str, h_value: str, salt: str) -> bool`

## Consequences

- **Positive:** No more cnlib git submodule, simpler dependency management, transparent security code
- **Positive:** Constant-time comparison prevents timing side-channel attacks
- **Negative:** Must verify algorithm matches cnlib exactly — incorrect implementation breaks TV authentication
- **Risk mitigation:** Test with known tvid/hash/salt test vectors before production deployment
