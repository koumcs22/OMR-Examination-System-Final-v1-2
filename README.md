# OMR Examination Management System — Final v1 Production Codebase

This build is based on the supplied OMR requirements and the supplied HTML UI prototype. The navigation, terminology and workflow follow the prototype: Dashboard, School Setup, OMR Templates, Examinations, OMR Scanning, Evaluation, Results, Marksheets, Communication, Grade Configuration, Audit Log and Settings.

Source UI reference: supplied `OMR Examination Management System.html`.

## Run on Mac M1

```bash
chmod +x run_mac.sh
./run_mac.sh
```

The application stores its local SQLite database under:

`~/OMRExaminationSystem/omr.db`

Exports are written to:

`~/OMRExaminationSystem/exports/`

## Included in v1

- Native PySide6 desktop UI
- SQLite persistent database
- School profile
- Faculty accounts/records
- Student CRUD
- CSV bulk import and import history
- Configurable OMR templates
- Examination creation
- Question and answer configuration
- Marks and negative marking configuration
- OMR PDF generation
- Scanned image import workflow
- OMR sheet records and review status
- Automatic evaluation engine
- Manual correction
- Separate grace marks
- Audit log
- Result finalisation
- Configurable grades
- Marksheet PDF generation
- WhatsApp/Email distribution history structure
- Settings
- Windows GitHub Actions build workflow

## Important production integrations

The application architecture is ready for the hardware/provider-specific integrations, but those require the target environment:
- TWAIN/WIA scanner driver/API
- Actual OMR scanner model
- WhatsApp Cloud API credentials/template
- SMTP/email provider credentials
- Production licensing server

Those integrations cannot be honestly hard-coded without the scanner model, API credentials and deployment/licensing requirements.


## UI v2
The PySide6 UI follows the supplied OMR HTML reference: dark #201f1e chrome/sidebar, burgundy #7a2e2e primary actions and active state, cream #f3f2ef workspace, white cards, compact Figtree/system typography, status pills, and the same navigation/page terminology.
