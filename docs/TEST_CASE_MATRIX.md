# Test case matrix

| Scenario | Required evidence / status |
|---|---|
| Existing W211 LPG/P0302 golden and recalculation | Baseline PASS; regression required after changes |
| Legacy local clients with feature off | Existing Python/Desktop/Android checks; preserve behavior |
| Register USER, reject requested ADMIN, bad password, duplicate email | Foundation API suite |
| Login expiry/logout/inactive account | Foundation negative suite; DB current state |
| USER/CUSTOMER/ADMIN selection; reject MARKET mode | Foundation RBAC suite |
| Foreign owned-profile read/write | Foundation 404/deny; never accept account ID from client |
| Invitation before accept, wrong recipient/vehicle, expired invite | Foundation deny suite |
| Explicit read consent, revoke, expired grant, inactive/foreign staff | Foundation integration suite |
| Existing SQL row preservation / FK checks / downgrade | SQLite Alembic suite; PostgreSQL execution separate |
| Daily job when disconnected/ignition OFF, duplicate runs | PLANNED Phase 2, not implemented |
| Real email/SMS and licensed diagram access | BLOCKED until providers/licenses configured |
| MARKET fitment/discount/coupon abuse | PLANNED Phase 4 |
| Physical Bluetooth/BLE/Wi-Fi/USB OBD | NOT EXECUTED; simulator coverage distinct |
| Interactive architecture zoom/pan/search/layers/theme | Local browser validation, not just file presence |
| iOS runtime and Windows installer runtime | BLOCKED on Linux |
