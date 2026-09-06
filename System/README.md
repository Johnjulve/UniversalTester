# 🌐 System & End-to-End (E2E) Testing

System testing verifies complete end-to-end workflows across the frontend and backend to ensure all integrated components function harmoniously from a user perspective.

---

## 🎯 Target E2E Workflows

1. **Student Voter Journey**:
   - Google OAuth / Credentials Login &rarr; Profile verification check &rarr; View active elections &rarr; Fill out and submit secret ballot &rarr; Receive and download cryptographic receipt code (`ABCD-EFGH`).
2. **First-Time Student Onboarding**:
   - Roster-imported student signs in with temporary password &rarr; Intercepted by mandatory first-login password reset modal &rarr; Updates password &rarr; Redirected to dashboard.
3. **Registrar Roster Sync**:
   - Admin uploads `.xlsx` or `.csv` roster &rarr; In-memory preview inspects diffs &rarr; Admin confirms sync &rarr; Database updates verified voters atomically.
4. **Election Commission Lifecycle**:
   - Create election draft &rarr; Configure positions & parties &rarr; Publish candidate applications &rarr; Review & approve candidates &rarr; Launch election &rarr; Tally votes & publish audit ledger.
5. **Receipt Verification**:
   - Enter receipt code on `/verify-receipt` &rarr; Verify zero-knowledge ballot inclusion without decrypting candidate selections.

---

## 🛠️ Recommended Tooling

- **Playwright (Recommended)** or **Cypress**: For browser automation across Chromium, Firefox, and WebKit.
- **Newman / Postman**: For multi-step API integration sequences.

---

## 📁 Directory Structure

```text
Testing/System/
├── README.md               <-- System test guidelines & scenario specifications
├── test_system_e2e.py      <-- Automated 7-step system & E2E workflow verification suite
├── e2e/                    <-- Browser automation test specs (e.g., voter_flow.spec.js)
└── integration/            <-- Cross-service API workflow test collections
```

---

## 🚀 Execution Guide

Run the automated Python system & integration verification suite:
```powershell
.\env\Scripts\python.exe Testing/System/test_system_e2e.py
```
This executes and verifies all 7 critical system workflows:
1. System configuration and administrative access
2. Student onboarding and mandatory first-login password reset boundary
3. Registrar student roster parser and diff classification
4. End-to-end ballot casting, receipt minting, and blockchain hash chaining
5. Cryptographic ledger tamper detection and rejection
6. Zero-knowledge voter receipt code verification
7. Real-time turnout and results statistics calculation

