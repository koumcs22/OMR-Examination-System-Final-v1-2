# Implementation Notes

The desktop client uses PySide6. SQLite is the local source of truth. Services isolate business operations from UI. The OMR engine is isolated so scanner/image-recognition implementations can evolve without changing screens.

Data flow:
License/Auth -> School -> Students -> Template -> Examination -> OMR PDF -> Scan -> Recognition -> Evaluation -> Manual Review -> Audit -> Finalise -> Marksheet -> Distribution.

Never overwrite automatic marks when a correction is made. `automatic_marks`, `correction_marks`, `grace_marks` and `final_marks` remain separate.
