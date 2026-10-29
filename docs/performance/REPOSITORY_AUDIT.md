# Repository Audit

Date: 2026-10-29 (Asia/Yerevan). Repository: `Grigor1995/AI-CAR-SCANER`.

Audit scope: all 1,041 tracked paths at baseline `540e00f`; 454 Python,
58 Kotlin, 19 Swift files; zero tracked C++/headers/CMake files at baseline.
A C++ experiment is added by this audit, not discovered as existing production code.
No files, icons or application screens are removed. New empty NEW_AI_CAR_SCANER
is excluded; existing project remains in AI-CAR-SCANER.

Verified stack: Python 3.13/FastAPI/Pydantic/SQLAlchemy/Alembic/psycopg;
PySide6/QThread/QPainter Desktop; Kotlin Compose/coroutines/Retrofit/native
Bluetooth/BLE/Wi-Fi/USB Android; SwiftUI/URLSession/CoreBluetooth iOS.
Python tests use pytest/asyncio/coverage; Desktop has isolated five-group runner;
Android Gradle wrapper/JVM/instrumentation; iOS Xcode. Local runner/build/installer
scripts retained. No CI/CD introduced.

AI is Python orchestration around optional HTTP llama-server/OpenAI-compatible
providers; llama.cpp already supplies native model inference. RAG has lexical and
optional vector/pgvector adapters. No loaded model or physical adapter is available.
Existing ecosystem account/ownership/consent is opt-in and blocks legacy APIs when
enabled. USER/CUSTOMER/ADMIN are preserved; MARKET is an unimplemented merchant
integration target, not a working production shop. Notification delivery, durable
scheduler and offline account synchronization are incomplete, not benchmark successes.

See CURRENT_ARCHITECTURE.md for actual paths and all eight candidate assessments
in CPP_FEASIBILITY_MATRIX.md. Full existing feature inventory is retained in
../CURRENT_SYSTEM_AUDIT.md and ../FEATURE_MATRIX.md.
