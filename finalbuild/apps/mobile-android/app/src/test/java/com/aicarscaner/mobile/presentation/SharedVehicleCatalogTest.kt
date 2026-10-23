package com.aicarscaner.mobile.presentation

import com.aicarscaner.mobile.data.parseSharedVehicleCatalog
import com.aicarscaner.mobile.data.mergeVehicleCatalog
import org.junit.Assert.*
import org.junit.Test

class SharedVehicleCatalogTest {
    @Test fun sharedSnapshotParsingKeepsFuelAndUnknownEcu() {
        val offline = parseSharedVehicleCatalog("""{"vehicles":[{"make":"Toyota","model":"Corolla","chassis":"E210","year":2020,"engine":"Hybrid","ecu":null,"fuel":"Hybrid"}]}""")
        assertEquals(listOf("hybrid"), offline.single().fuel)
        assertNull(offline.single().ecu)
        assertTrue(ecuOptionsFor(offline,"Toyota","Corolla","E210","Hybrid",2020).isEmpty())
    }
    @Test fun serverWinsExactDuplicatesAndSnapshotRetainsOtherGenerations() {
        val offline = parseSharedVehicleCatalog("""{"vehicles":[{"make":"Toyota","model":"Corolla","chassis":"E210","year":2020,"engine":"Hybrid","ecu":null,"fuel":"Hybrid"},{"make":"Toyota","model":"Corolla","chassis":"E150","year":2010,"engine":"1.6","ecu":null,"fuel":["petrol"]}]}""")
        val online = offline.first().copy(source="backend-authoritative",fuel=listOf("petrol","hybrid"))
        val merged=mergeVehicleCatalog(listOf(online),offline)
        assertEquals(2,merged.size)
        assertEquals("backend-authoritative",merged.first().source)
        assertEquals(listOf("E150","E210"),chassisOptionsFor(merged,"Toyota","Corolla"))
    }
    @Test fun unitConversionIsPresentationOnlyAndGaugeUsesMatchingScale() {
        val raw=ChartChannel("Speed","km/h",androidx.compose.ui.graphics.Color.Blue,listOf(100.0))
        assertEquals(62.137119,displayChannel(raw,true).values.single(),.00001)
        assertEquals(listOf(100.0),raw.values)
        assertEquals("mph",displayChannel(raw,true).unit)
        val temperature=raw.copy(unit="°C",values=listOf(90.0))
        assertEquals(194.0,displayChannel(temperature,true).values.single(),.00001)
        assertEquals(-40.0 to 320.0,gaugeRange("°F",194.0))
    }
}
