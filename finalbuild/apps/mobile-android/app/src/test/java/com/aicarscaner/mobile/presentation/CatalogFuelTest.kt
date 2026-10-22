package com.aicarscaner.mobile.presentation

import com.aicarscaner.mobile.data.api.VehicleCatalogEntryDto
import org.junit.Assert.assertEquals
import org.junit.Test

class CatalogFuelTest {
    @Test fun dieselAndHybridUseServerDefaultsInsteadOfPetrolCheckboxes() {
        for (fuel in listOf("diesel", "hybrid")) {
            val catalog = listOf(VehicleCatalogEntryDto("Make", "Model", "Chassis", 2010, "Engine", fuel=listOf(fuel)))
            assertEquals(listOf(fuel), formFuel(catalog,"Make","Model","Chassis","Engine",true,true))
        }
    }
    @Test fun petrolAndLpgRemainUserFormChoices() {
        assertEquals(listOf("petrol"), formFuel(emptyList(),"Make","Model","Chassis","Engine",true,false))
    }
}
