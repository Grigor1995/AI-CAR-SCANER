# AI CAR SCANER — Android Mobile

Native Android client built with Kotlin and Jetpack Compose.

## Architecture

- Presentation: Jetpack Compose + ViewModel
- Domain: diagnostic session use cases and models
- Data: REST API, local persistence, repositories
- Device: BLE / USB / OBD / future VCI integration

The existing Flutter client is intentionally preserved during migration until the Kotlin client is verified.
