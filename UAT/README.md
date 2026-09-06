# 👥 User Acceptance Testing (UAT)

User Acceptance Testing evaluates E-Botar in realistic campus election scenarios to ensure the platform satisfies the real-world operational needs of students, election commissioners, and university administrators.

---

## 🎯 Primary Evaluation Personas

1. **Student Voter (Primary Stakeholder)**:
   - Evaluates clarity of ballot interfaces, candidate profile accessibility, voting ease, receipt code generation, and mobile responsiveness.
2. **Election Officer / Student Supreme Council (Administrator)**:
   - Evaluates election configuration, candidate filing reviews, voter roster upload, live turnout monitoring, and official tally exports.
3. **Campus Registrar Staff (Institutional Stakeholder)**:
   - Evaluates spreadsheet roster import (`.xlsx`/`.csv`), error reporting on malformed student IDs, and unlisted account deactivation.

---

## 📋 Standard UAT Evaluation Rubric

Users rate each dimension using a standard 5-point Likert scale (1 = Strongly Disagree, 5 = Strongly Agree) based on the **System Usability Scale (SUS)** and **ISO/IEC 25010** software quality models:

| Metric | Evaluation Focus | Target Score |
| :--- | :--- | :--- |
| **Ease of Use** | Voter navigation, ballot submission, receipt verification | &ge; 4.5 / 5.0 |
| **System Transparency** | Clear voting status, receipt auditability, public results display | &ge; 4.6 / 5.0 |
| **Visual Appeal** | Clean modern UI, contrast, readability on mobile and desktop | &ge; 4.5 / 5.0 |
| **Confidence & Trust** | Trust in ballot secrecy and tamper-evident cryptographic receipts | &ge; 4.7 / 5.0 |

---

## 📁 Directory Structure

```text
Testing/UAT/
├── README.md               <-- UAT methodology & scenario guidelines
├── scripts/                <-- Step-by-step test scripts for participant evaluations
└── questionnaires/         <-- Post-test usability survey forms (SUS & Likert)
```
