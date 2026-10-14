package com.aicarscaner.mobile.presentation

import com.aicarscaner.mobile.data.api.VehicleCatalogEntryDto
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class VehicleCatalogTest {
    private val remoteCatalog = listOf(
        entry(make = "Mercedes-Benz", model = "E-Class", chassis = "W211", year = 2006, engine = "M272", ecu = "ME9.7"),
        entry(make = "Mercedes-Benz", model = "E-Class", chassis = "W211", year = 2004, engine = "M272", ecu = "ME9.7"),
        entry(make = "Mercedes-Benz", model = "E-Class", chassis = "W212", year = 2010, engine = "M276", ecu = null),
        entry(make = "BMW", model = "3 Series", chassis = "E90", year = 2008, engine = "N52", ecu = "MSV70"),
        entry(make = "Mercedes-Benz", model = "E-Class", chassis = "W211", year = 2006, engine = "M272", ecu = "ME9.7")
    )

    @Test
    fun localCatalogFindsModelsByMakeAndUnknownMakeReturnsEmpty() {
        val models = modelOptionsFor("Mercedes-Benz")
        assertEquals(listOf("E-Class", "C-Class", "E-Class"), models.map { it.name })
        assertTrue(modelOptionsFor("Not a Make").isEmpty())
    }

    @Test
    fun localCatalogFiltersChassisAndReturnsEmptyForUnknownModel() {
        assertEquals(listOf("W211", "W212"), chassisOptionsFor("Mercedes-Benz", "E-Class").map { it.chassis })
        assertTrue(chassisOptionsFor("Mercedes-Benz", "Unknown").isEmpty())
        assertTrue(chassisOptionsFor("Unknown", "E-Class").isEmpty())
    }

    @Test
    fun localCatalogReturnsYearsForExactMakeModelAndChassis() {
        assertEquals((2002..2009).toList(), yearOptionsFor("Mercedes-Benz", "E-Class", "W211"))
        assertTrue(yearOptionsFor("Mercedes-Benz", "E-Class", "W999").isEmpty())
    }

    @Test
    fun localCatalogReturnsEnginesAndEcusForExactSelection() {
        val engines = engineOptionsFor("Mercedes-Benz", "E-Class", "W211")
        assertEquals(4, engines.size)
        assertEquals(listOf("ME9.7"), ecuOptionsFor("Mercedes-Benz", "E-Class", "W211", "M272 E35 3.5"))
        assertTrue(ecuOptionsFor("Mercedes-Benz", "E-Class", "W211", "unknown engine").isEmpty())
    }

    @Test
    fun remoteCatalogReturnsDistinctSortedModelsAndChassis() {
        assertEquals(listOf("E-Class"), modelOptionsFor(remoteCatalog, "Mercedes-Benz"))
        assertEquals(listOf("W211", "W212"), chassisOptionsFor(remoteCatalog, "Mercedes-Benz", "E-Class"))
        assertEquals(listOf("3 Series"), modelOptionsFor(remoteCatalog, "BMW"))
        assertTrue(modelOptionsFor(remoteCatalog, "unknown").isEmpty())
    }

    @Test
    fun remoteCatalogReturnsDistinctYearsDescending() {
        assertEquals(
            listOf(2006, 2004),
            yearOptionsFor(remoteCatalog, "Mercedes-Benz", "E-Class", "W211")
        )
        assertTrue(yearOptionsFor(remoteCatalog, "Mercedes-Benz", "E-Class", "unknown").isEmpty())
    }

    @Test
    fun remoteCatalogFiltersEngineByOptionalYear() {
        assertEquals(
            listOf("M272"),
            engineOptionsFor(remoteCatalog, "Mercedes-Benz", "E-Class", "W211", year = 2004)
        )
        assertEquals(
            listOf("M272"),
            engineOptionsFor(remoteCatalog, "Mercedes-Benz", "E-Class", "W211")
        )
        assertTrue(engineOptionsFor(remoteCatalog, "Mercedes-Benz", "E-Class", "W211", year = 2015).isEmpty())
    }

    @Test
    fun remoteCatalogFiltersEcuByEngineAndOptionalYear() {
        assertEquals(
            listOf("ME9.7"),
            ecuOptionsFor(remoteCatalog, "Mercedes-Benz", "E-Class", "W211", "M272", year = 2004)
        )
        assertEquals(
            listOf("ME9.7"),
            ecuOptionsFor(remoteCatalog, "Mercedes-Benz", "E-Class", "W211", "M272")
        )
        assertTrue(ecuOptionsFor(remoteCatalog, "Mercedes-Benz", "E-Class", "W212", "M276").isEmpty())
        assertTrue(ecuOptionsFor(remoteCatalog, "Mercedes-Benz", "E-Class", "W211", "M272", year = 2015).isEmpty())
    }

    private fun entry(
        make: String,
        model: String,
        chassis: String?,
        year: Int,
        engine: String,
        ecu: String?
    ) = VehicleCatalogEntryDto(
        make = make,
        model = model,
        chassis = chassis,
        year = year,
        engine = engine,
        ecu = ecu
    )
}
