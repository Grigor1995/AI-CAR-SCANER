package com.aicarscaner.mobile.presentation

// Backend entries and the bundled shared/vehicle_catalog.json snapshot are the
// only catalog sources. Never maintain a separate Kotlin vehicle seed list.

/** Remote catalog helpers. The backend DB is authoritative; local data is only a fallback. */
fun modelOptionsFor(catalog: List<com.aicarscaner.mobile.data.api.VehicleCatalogEntryDto>, make: String): List<String> =
    catalog.filter { it.make == make }.map { it.model }.distinct().sorted()

fun chassisOptionsFor(catalog: List<com.aicarscaner.mobile.data.api.VehicleCatalogEntryDto>, make: String, model: String): List<String> =
    catalog.filter { it.make == make && it.model == model }.mapNotNull { it.chassis }.distinct().sorted()

fun yearOptionsFor(catalog: List<com.aicarscaner.mobile.data.api.VehicleCatalogEntryDto>, make: String, model: String, chassis: String): List<Int> =
    catalog.filter { it.make == make && it.model == model && it.chassis == chassis }.map { it.year }.distinct().sortedDescending()

fun engineOptionsFor(catalog: List<com.aicarscaner.mobile.data.api.VehicleCatalogEntryDto>, make: String, model: String, chassis: String, year: Int? = null): List<String> =
    catalog.filter {
        it.make == make && it.model == model && it.chassis == chassis &&
            (year == null || it.year == year)
    }.map { it.engine }.distinct().sorted()

fun ecuOptionsFor(catalog: List<com.aicarscaner.mobile.data.api.VehicleCatalogEntryDto>, make: String, model: String, chassis: String, engine: String, year: Int? = null): List<String> =
    catalog.filter {
        it.make == make && it.model == model && it.chassis == chassis &&
            it.engine == engine && (year == null || it.year == year)
    }.mapNotNull { it.ecu }.distinct().sorted()
