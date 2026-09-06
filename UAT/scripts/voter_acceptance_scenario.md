# 📋 Student Voter User Acceptance Testing (UAT) Scenario Script

**Test ID**: `UAT-STU-01`  
**Target Role**: Student Voter  
**Platform**: E-Botar Electronic Voting System  
**Estimated Time**: 5–8 minutes  

---

## 🎯 Test Objective
Evaluate whether a university student can intuitively navigate the voting portal, review candidates, securely cast an anonymized ballot, receive a cryptographic receipt, and verify their ballot on the audit ledger.

---

## 📝 Pre-Requisites
- System running and active election present.
- Student credentials or university Google account available.

---

## 🚶 Step-by-Step Testing Protocol

| Step | User Action | Expected System Response | Pass / Fail |
| :---: | :--- | :--- | :---: |
| **1** | Navigate to `/login` and sign in with student credentials. | Redirected to voter dashboard; active elections visible. | [ ] |
| **2** | *(If temporary password)* First-login password modal prompts for new password. | Modal enforces 8+ characters; upon submit, full access granted. | [ ] |
| **3** | Click **"Vote Now"** on the active university election. | Ballot interface loads showing configured positions and candidate profiles. | [ ] |
| **4** | Review candidate manifestos and select preferred candidates. | Radio buttons / checkboxes update cleanly; selection summary updates. | [ ] |
| **5** | Click **"Review Ballot"** and verify choices on summary dialog. | Confirmation modal shows selected candidates before final commit. | [ ] |
| **6** | Click **"Submit Vote"**. | Ballot successfully committed; 8-character receipt code (`XXXX-XXXX`) displayed with download button. | [ ] |
| **7** | Navigate to `/verify-receipt` and enter the receipt code. | System confirms ballot inclusion with timestamp and election title without decrypting candidate choices. | [ ] |
| **8** | Return to voter dashboard. | Voting status indicates **"Voted"**; student cannot re-cast for same election. | [ ] |

---

## ✍️ Evaluator Notes & Observations
- **Did the user encounter any confusion during candidate selection?** `[ ] Yes  [ ] No`
- **Was the receipt code easily copied/downloaded?** `[ ] Yes  [ ] No`
- **Comments**: ____________________________________________________________________
