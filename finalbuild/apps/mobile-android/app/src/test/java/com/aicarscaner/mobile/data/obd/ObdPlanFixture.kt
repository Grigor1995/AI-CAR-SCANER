package com.aicarscaner.mobile.data.obd

// Transport tests inject a server-owned plan instead of requesting a live API.
internal val backendInitializationFixture = listOf("ATZ", "ATE0", "ATL0", "ATS0", "ATSP0")
