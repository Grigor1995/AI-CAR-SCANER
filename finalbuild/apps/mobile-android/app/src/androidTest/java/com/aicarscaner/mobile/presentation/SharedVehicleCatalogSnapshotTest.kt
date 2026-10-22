package com.aicarscaner.mobile.presentation

import android.content.Context
import androidx.test.platform.app.InstrumentationRegistry
import com.aicarscaner.mobile.data.repository.DiagnosticRepository
import com.aicarscaner.mobile.data.api.ApiClient
import org.junit.Assert.assertTrue
import org.junit.Test

class SharedVehicleCatalogSnapshotTest {
    @Test fun snapshotContainsDesktopReferenceVehicle() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val rows = DiagnosticRepository(ApiClient.diagnosticApi, context).offlineVehicleCatalog()
        assertTrue("Snapshot not bundled", rows.isNotEmpty())
        assertTrue(rows.any { it.make == "Mercedes-Benz" && it.model == "E-Class" &&
            it.chassis == "W211" && it.year == 2006 && it.engine == "M272 E35 3.5" })
    }
}
