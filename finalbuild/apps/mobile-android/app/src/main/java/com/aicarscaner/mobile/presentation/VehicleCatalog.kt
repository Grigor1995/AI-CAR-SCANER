package com.aicarscaner.mobile.presentation

data class VehicleEngineOption(val name: String, val ecus: List<String>)

data class VehicleModelOption(
    val name: String,
    val chassis: String,
    val years: List<Int>,
    val engines: List<VehicleEngineOption>
)

data class VehicleMakeOption(val name: String, val models: List<VehicleModelOption>)

/** Curated real-world seed catalog. Exact fitment still requires VIN/ECU identification. */
val vehicleCatalog: List<VehicleMakeOption> = listOf(
    VehicleMakeOption("Mercedes-Benz", listOf(
        VehicleModelOption("E-Class","W211",(2002..2009).toList(),listOf(
            VehicleEngineOption("M112 E32 3.2",listOf("ME2.8 / Auto-detect")),
            VehicleEngineOption("M113 E50 5.0",listOf("ME2.8 / Auto-detect")),
            VehicleEngineOption("M272 E35 3.5",listOf("ME9.7")),
            VehicleEngineOption("OM642 3.0 V6",listOf("CDI / Auto-detect")))),
        VehicleModelOption("C-Class","W204",(2007..2014).toList(),listOf(
            VehicleEngineOption("M271 1.8",listOf("ME9.7 / Auto-detect")),
            VehicleEngineOption("M272 3.5 V6",listOf("ME9.7")),
            VehicleEngineOption("OM651 2.1",listOf("CDI / Auto-detect")))),
        VehicleModelOption("E-Class","W212",(2009..2016).toList(),listOf(
            VehicleEngineOption("M271 1.8",listOf("ME9.7 / Auto-detect")),
            VehicleEngineOption("M276 3.5 V6",listOf("MED17 / Auto-detect")),
            VehicleEngineOption("OM651 2.1",listOf("CDI / Auto-detect")),
            VehicleEngineOption("OM642 3.0 V6",listOf("CDI / Auto-detect"))))
    )),
    VehicleMakeOption("BMW", listOf(
        VehicleModelOption("3 Series","E90",(2005..2012).toList(),listOf(
            VehicleEngineOption("N43B16 1.6",listOf("MSD80/Auto-detect")),
            VehicleEngineOption("N46B20 2.0",listOf("MSV70/Auto-detect")),
            VehicleEngineOption("N52B25 2.5",listOf("MSV70/Auto-detect")),
            VehicleEngineOption("N52B30 3.0",listOf("MSV70/Auto-detect")))),
        VehicleModelOption("3 Series","F30",(2012..2018).toList(),listOf(
            VehicleEngineOption("N20B20 2.0 Turbo",listOf("MEVD17 / Auto-detect")),
            VehicleEngineOption("N55B30 3.0 Turbo",listOf("MEVD17 / Auto-detect")),
            VehicleEngineOption("B47 2.0 Diesel",listOf("DDE / Auto-detect")))),
        VehicleModelOption("5 Series","E60",(2003..2010).toList(),listOf(
            VehicleEngineOption("M54B30 3.0",listOf("MS43/Auto-detect")),
            VehicleEngineOption("N52B25 2.5",listOf("MSV70/Auto-detect")),
            VehicleEngineOption("N52B30 3.0",listOf("MSV70/Auto-detect"))))
    )),
    VehicleMakeOption("Toyota", listOf(
        VehicleModelOption("Corolla","E140/E150",(2007..2013).toList(),listOf(
            VehicleEngineOption("1ZR-FE 1.6",listOf("Auto-detect")),
            VehicleEngineOption("2ZR-FE 1.8",listOf("Auto-detect")))),
        VehicleModelOption("Camry","XV40",(2006..2011).toList(),listOf(
            VehicleEngineOption("2AZ-FE 2.4",listOf("Auto-detect")),
            VehicleEngineOption("2GR-FE 3.5 V6",listOf("Auto-detect")))),
        VehicleModelOption("RAV4","XA30",(2005..2012).toList(),listOf(
            VehicleEngineOption("2AZ-FE 2.4",listOf("Auto-detect")),
            VehicleEngineOption("2GR-FE 3.5 V6",listOf("Auto-detect"))))
    )),
    VehicleMakeOption("Kia", listOf(
        VehicleModelOption("Forte","TD",(2010..2013).toList(),listOf(
            VehicleEngineOption("G4FC 1.6",listOf("Auto-detect")),
            VehicleEngineOption("G4KD 2.0",listOf("Auto-detect")))),
        VehicleModelOption("Forte","YD",(2014..2018).toList(),listOf(
            VehicleEngineOption("G4FG 1.6",listOf("Auto-detect")),
            VehicleEngineOption("G4NC 2.0",listOf("Auto-detect")))),
        VehicleModelOption("Sportage","SL",(2011..2015).toList(),listOf(
            VehicleEngineOption("G4KD 2.0",listOf("Auto-detect")),
            VehicleEngineOption("G4KE 2.4",listOf("Auto-detect"))))
    )),
    VehicleMakeOption("Hyundai", listOf(
        VehicleModelOption("Elantra","MD",(2011..2016).toList(),listOf(
            VehicleEngineOption("G4FG 1.6",listOf("Auto-detect")),
            VehicleEngineOption("G4NA 2.0",listOf("Auto-detect")))),
        VehicleModelOption("Elantra","AD",(2017..2020).toList(),listOf(
            VehicleEngineOption("G4FG 1.6",listOf("Auto-detect")),
            VehicleEngineOption("G4NA 2.0",listOf("Auto-detect")))),
        VehicleModelOption("Tucson","TL",(2016..2020).toList(),listOf(
            VehicleEngineOption("G4NA 2.0",listOf("Auto-detect")),
            VehicleEngineOption("G4FJ 1.6 Turbo",listOf("Auto-detect"))))
    )),
    VehicleMakeOption("Honda", listOf(
        VehicleModelOption("Civic","FD",(2006..2011).toList(),listOf(
            VehicleEngineOption("R18A 1.8",listOf("Auto-detect")),
            VehicleEngineOption("K20Z 2.0",listOf("Auto-detect")))),
        VehicleModelOption("Accord","CU",(2008..2012).toList(),listOf(
            VehicleEngineOption("K24Z 2.4",listOf("Auto-detect")),
            VehicleEngineOption("J35Z 3.5 V6",listOf("Auto-detect"))))
    )),
    VehicleMakeOption("Volkswagen", listOf(
        VehicleModelOption("Golf","Mk6",(2009..2013).toList(),listOf(
            VehicleEngineOption("1.4 TSI",listOf("Auto-detect")),
            VehicleEngineOption("2.0 TDI",listOf("Auto-detect")))),
        VehicleModelOption("Golf","Mk7",(2013..2020).toList(),listOf(
            VehicleEngineOption("1.4 TSI",listOf("Auto-detect")),
            VehicleEngineOption("1.5 TSI",listOf("Auto-detect")),
            VehicleEngineOption("2.0 TDI",listOf("Auto-detect")))),
        VehicleModelOption("Passat","B7",(2011..2014).toList(),listOf(
            VehicleEngineOption("1.8 TSI",listOf("Auto-detect")),
            VehicleEngineOption("2.0 TDI",listOf("Auto-detect"))))
    )),
    VehicleMakeOption("Ford", listOf(
        VehicleModelOption("Focus","Mk3",(2011..2018).toList(),listOf(
            VehicleEngineOption("1.6 Ti-VCT",listOf("Auto-detect")),
            VehicleEngineOption("1.0 EcoBoost",listOf("Auto-detect")),
            VehicleEngineOption("2.0 TDCi",listOf("Auto-detect")))),
        VehicleModelOption("Mondeo","Mk4",(2007..2014).toList(),listOf(
            VehicleEngineOption("2.0 Duratec",listOf("Auto-detect")),
            VehicleEngineOption("2.0 TDCi",listOf("Auto-detect"))))
    ))
)

fun modelOptionsFor(make: String) = vehicleCatalog.firstOrNull { it.name == make }?.models.orEmpty()
fun chassisOptionsFor(make: String, model: String) = modelOptionsFor(make).filter { it.name == model }
fun yearOptionsFor(make: String, model: String, chassis: String) =
    modelOptionsFor(make).firstOrNull { it.name == model && it.chassis == chassis }?.years.orEmpty()
fun engineOptionsFor(make: String, model: String, chassis: String) =
    modelOptionsFor(make).firstOrNull { it.name == model && it.chassis == chassis }?.engines.orEmpty()
fun ecuOptionsFor(make: String, model: String, chassis: String, engine: String) =
    engineOptionsFor(make, model, chassis).firstOrNull { it.name == engine }?.ecus.orEmpty()


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
