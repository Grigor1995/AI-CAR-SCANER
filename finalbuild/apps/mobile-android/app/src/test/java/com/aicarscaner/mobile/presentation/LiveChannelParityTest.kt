package com.aicarscaner.mobile.presentation
import com.aicarscaner.mobile.data.obd.LiveDataSnapshot
import org.junit.Test
import org.junit.Assert.*
class LiveChannelParityTest {
    @Test fun everyDecodedFieldCanBeSelectedInLocalCharts() {
        val values=channels(listOf(LiveDataSnapshot(rpm=1000.0,mafGps=12.0,shortFuelTrimPct=-5.0,longFuelTrimPct=2.0)))
        assertEquals(10,values.size)
        assertEquals(listOf(12.0),values.single{it.key=="MAF"}.values)
        assertEquals(listOf(-5.0),values.single{it.key=="STFT"}.values)
        assertEquals(listOf(2.0),values.single{it.key=="LTFT"}.values)
    }
}
