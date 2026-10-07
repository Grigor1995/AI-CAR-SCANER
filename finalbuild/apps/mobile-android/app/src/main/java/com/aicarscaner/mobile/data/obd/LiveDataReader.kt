package com.aicarscaner.mobile.data.obd

data class LiveDataSnapshot(
    val rpm: Double? = null,
    val speedKph: Double? = null,
    val coolantC: Double? = null,
    val engineLoadPct: Double? = null,
    val intakeAirC: Double? = null,
    val mafGps: Double? = null,
    val mapKpa: Double? = null,
    val throttlePct: Double? = null,
    val shortFuelTrimPct: Double? = null,
    val longFuelTrimPct: Double? = null,
    val updatedAtMs: Long = System.currentTimeMillis()
)

object LiveDataReader {
    suspend fun read(command: suspend (String) -> Result<String>): Result<LiveDataSnapshot> = runCatching {
        LiveDataSnapshot(
            rpm = command("010C").getOrNull()?.pidBytes("0C", 2)?.let { ((it[0] * 256) + it[1]) / 4.0 },
            speedKph = command("010D").getOrNull()?.pidBytes("0D", 1)?.getOrNull(0)?.toDouble(),
            coolantC = command("0105").getOrNull()?.pidBytes("05", 1)?.getOrNull(0)?.let { it - 40.0 },
            engineLoadPct = command("0104").getOrNull()?.pidBytes("04", 1)?.getOrNull(0)?.let { it * 100.0 / 255.0 },
            intakeAirC = command("010F").getOrNull()?.pidBytes("0F", 1)?.getOrNull(0)?.let { it - 40.0 },
            mafGps = command("0110").getOrNull()?.pidBytes("10", 2)?.let { ((it[0] * 256) + it[1]) / 100.0 },
            mapKpa = command("010B").getOrNull()?.pidBytes("0B", 1)?.getOrNull(0)?.toDouble(),
            throttlePct = command("0111").getOrNull()?.pidBytes("11", 1)?.getOrNull(0)?.let { it * 100.0 / 255.0 },
            shortFuelTrimPct = command("0106").getOrNull()?.pidBytes("06", 1)?.getOrNull(0)?.let { (it - 128.0) * 100.0 / 128.0 },
            longFuelTrimPct = command("0107").getOrNull()?.pidBytes("07", 1)?.getOrNull(0)?.let { (it - 128.0) * 100.0 / 128.0 }
        )
    }

    private fun String.pidBytes(pid: String, count: Int): List<Int>? {
        val hex = replace("\\s".toRegex(), "").uppercase()
        if (hex.contains("NODATA") || hex.contains("ERROR") || hex.contains("UNABLE")) return null
        val marker = "41$pid"
        val start = hex.indexOf(marker)
        if (start < 0) return null
        val dataStart = start + marker.length
        val end = dataStart + count * 2
        if (end > hex.length) return null
        return (0 until count).mapNotNull { index ->
            hex.substring(dataStart + index * 2, dataStart + index * 2 + 2).toIntOrNull(16)
        }.takeIf { it.size == count }
    }
}
