package com.aicarscaner.mobile.data

import com.aicarscaner.mobile.data.api.VehicleCatalogEntryDto
import com.google.gson.JsonParser

/** The same backend-generated offline snapshot packaged by Desktop. */
internal fun parseSharedVehicleCatalog(json: String): List<VehicleCatalogEntryDto> =
    JsonParser.parseString(json).asJsonObject.getAsJsonArray("vehicles").map { element ->
        val row = element.asJsonObject
        fun text(key: String) = row.get(key)?.takeUnless { it.isJsonNull }?.asString
        val fuel = row.get("fuel")
        VehicleCatalogEntryDto(
            make = text("make").orEmpty(), model = text("model").orEmpty(),
            chassis = text("chassis"), year = row.get("year").asInt,
            engine = text("engine").orEmpty(), ecu = text("ecu"),
            fuel = if (fuel?.isJsonArray == true) fuel.asJsonArray.map { it.asString.lowercase() }
                else text("fuel").orEmpty().split('+', ',').map { it.trim().lowercase() }.filter { it.isNotEmpty() },
            source = text("source") ?: "shared-offline-snapshot",
            scope = text("scope") ?: "curated-fitment"
        )
    }

internal fun mergeVehicleCatalog(server: List<VehicleCatalogEntryDto>, offline: List<VehicleCatalogEntryDto>): List<VehicleCatalogEntryDto> =
    (server + offline).distinctBy { row ->
        listOf(row.make, row.model, row.chassis.orEmpty(), row.year.toString(), row.engine, row.ecu.orEmpty()).map { it.trim().lowercase() }
    }
