# AI CAR SCANNER — Architecture summary

This package contains an interactive architecture visualization for the AI CAR SCANNER project.

## Files
- `AI_CAR_SCANNER_architecture_map.html` — interactive clickable architecture map
- `AI_CAR_SCANNER_architecture_summary.md` — this summary

## What the interactive map shows
1. **Clients**
   - Desktop (PySide6 / Windows)
   - Android (Kotlin / Compose)
   - iOS (SwiftUI)

2. **Shared cross-platform assets**
   - shared offline vehicle catalog
   - shared vehicle portraits
   - common UX/navigation concepts and localization/theme ideas

3. **Application-facing orchestration**
   - Desktop launcher / recovery supervisor
   - Mobile API clients

4. **Server core**
   - FastAPI backend
   - route groups:
     - vehicle / reference APIs
     - session / diagnostic APIs
     - acquisition / telemetry APIs
     - discovery / device / OBD APIs
     - AI / RAG / knowledge APIs

5. **Execution services**
   - reasoning / decision / intelligence engines
   - acquisition & discovery services
   - OBD / protocol layer

6. **External state and targets**
   - persistence (SQLite / PostgreSQL / session store)
   - AI providers (local llama-server / external)
   - devices (ELM327 / simulator / vehicle ECUs / future custom VCI)

## Best flows to click
- **Live data** — shows the clearest runtime path from app to adapter/ECU
- **Device discovery** — shows how VCI / device actions reach the connection layer
- **AI analyze live data** — shows how session, telemetry, engines, and AI provider fit together
- **App startup** — shows Desktop launcher behavior and local backend/local AI startup

## Important interpretation note
This is an architecture-level visualization, not a formal runtime trace exported from the codebase.
It is designed to explain the current project structure clearly and visually, using the repository and session context.