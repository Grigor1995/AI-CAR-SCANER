package com.aicarscaner.mobile.presentation

data class VehicleEngineOption(
    val name: String,
    val ecus: List<String>
)

data class VehicleModelOption(
    val name: String,
    val years: List<Int>,
    val engines: List<VehicleEngineOption>
)

data class VehicleMakeOption(
    val name: String,
    val models: List<VehicleModelOption>
)

/**
 * Seed catalog for guided vehicle selection.
 *
 * ECU values are intentionally conservative. Where an exact ECU cannot be
 * safely determined from the selected vehicle profile, the UI offers
 * Auto-detect instead of inventing a controller identifier.
 */
val vehicleCatalog: List<VehicleMakeOption> = listOf(
    VehicleMakeOption(
        "Mercedes",
        listOf(
            VehicleModelOption(
                "W211",
                (2002..2009).toList(),
                listOf(
                    VehicleEngineOption("M112 3.2", listOf("ME2.8")),
                    VehicleEngineOption("M113 5.0", listOf("ME2.8")),
                    VehicleEngineOption("M272 3.5", listOf("ME9.7")),
                    VehicleEngineOption("OM642 3.0", listOf("CDI / Auto-detect"))
                )
            ),
            VehicleModelOption(
                "W204",
                (2007..2014).toList(),
                listOf(
                    VehicleEngineOption("M271 1.8", listOf("ME9.7 / Auto-detect")),
                    VehicleEngineOption("M271 2.0", listOf("ME9.7 / Auto-detect")),
                    VehicleEngineOption("M272 3.5", listOf("ME9.7")),
                    VehicleEngineOption("OM651 2.1", listOf("CDI / Auto-detect"))
                )
            ),
            VehicleModelOption(
                "W212",
                (2009..2016).toList(),
                listOf(
                    VehicleEngineOption("M271 1.8", listOf("ME9.7 / Auto-detect")),
                    VehicleEngineOption("M276 3.5", listOf("MED17 / Auto-detect")),
                    VehicleEngineOption("OM651 2.1", listOf("CDI / Auto-detect")),
                    VehicleEngineOption("OM642 3.0", listOf("CDI / Auto-detect"))
                )
            )
        )
    ),
    VehicleMakeOption(
        "Kia",
        listOf(
            VehicleModelOption(
                "Forte",
                (2014..2018).toList(),
                listOf(
                    VehicleEngineOption("1.8", listOf("Auto-detect")),
                    VehicleEngineOption("2.0", listOf("Auto-detect"))
                )
            ),
            VehicleModelOption(
                "Sportage",
                (2014..2020).toList(),
                listOf(
                    VehicleEngineOption("2.0", listOf("Auto-detect")),
                    VehicleEngineOption("2.4", listOf("Auto-detect")),
                    VehicleEngineOption("2.0 Diesel", listOf("Auto-detect"))
                )
            )
        )
    ),
    VehicleMakeOption(
        "Hyundai",
        listOf(
            VehicleModelOption(
                "Elantra",
                (2016..2020).toList(),
                listOf(
                    VehicleEngineOption("1.6", listOf("Auto-detect")),
                    VehicleEngineOption("1.8", listOf("Auto-detect")),
                    VehicleEngineOption("2.0", listOf("Auto-detect"))
                )
            ),
            VehicleModelOption(
                "Tucson",
                (2016..2021).toList(),
                listOf(
                    VehicleEngineOption("2.0", listOf("Auto-detect")),
                    VehicleEngineOption("1.6 Turbo", listOf("Auto-detect")),
                    VehicleEngineOption("2.0 Diesel", listOf("Auto-detect"))
                )
            )
        )
    ),
    VehicleMakeOption(
        "Toyota",
        listOf(
            VehicleModelOption(
                "Corolla",
                (2014..2019).toList(),
                listOf(
                    VehicleEngineOption("1.6", listOf("Auto-detect")),
                    VehicleEngineOption("1.8", listOf("Auto-detect"))
                )
            ),
            VehicleModelOption(
                "Camry",
                (2012..2017).toList(),
                listOf(
                    VehicleEngineOption("2.5", listOf("Auto-detect")),
                    VehicleEngineOption("3.5", listOf("Auto-detect"))
                )
            )
        )
    ),
    VehicleMakeOption(
        "BMW",
        listOf(
            VehicleModelOption(
                "3 Series F30",
                (2012..2018).toList(),
                listOf(
                    VehicleEngineOption("2.0 Turbo", listOf("Auto-detect")),
                    VehicleEngineOption("3.0 Turbo", listOf("Auto-detect"))
                )
            ),
            VehicleModelOption(
                "5 Series F10",
                (2010..2017).toList(),
                listOf(
                    VehicleEngineOption("2.0 Turbo", listOf("Auto-detect")),
                    VehicleEngineOption("3.0 Turbo", listOf("Auto-detect")),
                    VehicleEngineOption("3.0 Diesel", listOf("Auto-detect"))
                )
            )
        )
    ),
    VehicleMakeOption(
        "Volkswagen",
        listOf(
            VehicleModelOption(
                "Golf Mk7",
                (2013..2020).toList(),
                listOf(
                    VehicleEngineOption("1.4 TSI", listOf("Auto-detect")),
                    VehicleEngineOption("1.5 TSI", listOf("Auto-detect")),
                    VehicleEngineOption("2.0 TDI", listOf("Auto-detect"))
                )
            ),
            VehicleModelOption(
                "Passat B8",
                (2014..2022).toList(),
                listOf(
                    VehicleEngineOption("1.4 TSI", listOf("Auto-detect")),
                    VehicleEngineOption("2.0 TSI", listOf("Auto-detect")),
                    VehicleEngineOption("2.0 TDI", listOf("Auto-detect"))
                )
            )
        )
    )
)

fun modelOptionsFor(make: String): List<VehicleModelOption> =
    vehicleCatalog.firstOrNull { it.name == make }?.models.orEmpty()

fun yearOptionsFor(make: String, model: String): List<Int> =
    modelOptionsFor(make).firstOrNull { it.name == model }?.years.orEmpty()

fun engineOptionsFor(make: String, model: String): List<VehicleEngineOption> =
    modelOptionsFor(make).firstOrNull { it.name == model }?.engines.orEmpty()

fun ecuOptionsFor(make: String, model: String, engine: String): List<String> =
    engineOptionsFor(make, model).firstOrNull { it.name == engine }?.ecus.orEmpty()
