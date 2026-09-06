# 🔒 Security & Cryptographic Audit

Security testing validates the cryptographic integrity of the append-only vote ledger, access control enforcement, authentication boundaries, and resilience against common web application vulnerabilities (OWASP Top 10).

---

## 🎯 Security Evaluation Areas

1. **Blockchain Vote Ledger Immutability**:
   - Verify SHA-256 hash chaining between consecutive `VoteBlock` entries.
   - Inject simulated block alterations to ensure the tampering detection engine immediately flags corrupted chains.
2. **Zero-Knowledge Voter Receipt Anonymity**:
   - Ensure vote receipts (`ABCD-EFGH`) reveal ballot inclusion without exposing candidate choices or voter identity.
3. **Role-Based Access Control (RBAC) Enforcement**:
   - Ensure student voter tokens are rejected with `403 Forbidden` on administrative endpoints (`/api/admin/*`, `/api/voting/audit/`, `/api/auth/students/roster-import/`).
   - Validate staff privilege restrictions (cannot edit superuser profiles or students above their year level).
4. **Authentication & Rate Limiting (Brute Force Defense)**:
   - Verify registration lockdown rejects public unauthenticated sign-ups.
   - Verify Django REST Framework throttling triggers `429 Too Many Requests` on aggressive login or verification polling.

---

## 🛠️ Recommended Tooling

- **Bandit**: Static application security testing (SAST) for Python code.
  ```bash
  bandit -r backend/apps/
  ```
- **pip-audit / safety**: Known dependency vulnerability scanner.
  ```bash
  pip-audit
  ```
- **OWASP ZAP**: Automated dynamic application security scanner for web endpoints.

---

## 📁 Directory Structure

```text
Testing/Security/
├── README.md                     <-- Security test criteria & threat model
├── test_cryptographic_audit.py   <-- Automated blockchain hash chain & receipt audit suite
├── audit_scripts/                <-- Penetration and vulnerability assessment scripts
└── reports/                      <-- Security scan and penetration test reports
```

---

## 🚀 Execution Guide

Run the automated forensic blockchain & cryptographic receipt audit:
```powershell
.\env\Scripts\python.exe Testing/Security/test_cryptographic_audit.py
```
This audits every recorded `VoteBlock` across all elections, validates sequential SHA-256 links, verifies zero-knowledge receipt codes, and detects any data tampering.

