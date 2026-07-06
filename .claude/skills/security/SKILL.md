---
name: security
description: OWASP Top 10 checklist to apply on every change, plus how to run the security tooling (Bandit, pip-audit, Trivy). Use when adding endpoints, handling input, or before opening a PR.
---

# Security (OWASP Top 10)

## Per-change checklist

- **A01 Access Control**: MVP API is public (only non-sensitive catalog data). When auth lands, enforce RBAC and ownership, deny-by-default.
- **A02 Cryptography**: secrets only via env/`get_settings()`; TLS in deploy. (Argon2 hashing + signed JWT arrive with auth.)
- **A03 Injection**: parameterized SQLAlchemy only; validate every input with Pydantic; sanitize chatbot input; separate data from instructions in LLM prompts.
- **A04 Insecure Design**: secure defaults, rate limiting on public/expensive endpoints (chatbot).
- **A05 Misconfiguration**: security headers middleware, strict CORS allowlist, no debug in prod, non-root Docker images.
- **A06 Vulnerable Components**: keep deps updated (Dependabot); run pip-audit / npm audit / Trivy.
- **A07 Auth Failures** *(with auth)*: login rate limiting, password policy, token expiry/rotation.
- **A08 Data Integrity**: lockfiles, reproducible CI.
- **A09 Logging**: structured logs; **never log secrets or PII**.
- **A10 SSRF**: allowlist outbound LLM provider hosts; validate URLs.

## Tooling

```bash
# Backend
bandit -r backend/app -c backend/pyproject.toml    # SAST
pip-audit                                           # dependency CVEs
# Frontend
cd frontend && npm audit
# Docker images
trivy image muscleapp-backend:ci
```

## Rules

- Report vulnerabilities privately, never in public issues.
- Prompt-injection guards are mandatory for any LLM-facing endpoint.
