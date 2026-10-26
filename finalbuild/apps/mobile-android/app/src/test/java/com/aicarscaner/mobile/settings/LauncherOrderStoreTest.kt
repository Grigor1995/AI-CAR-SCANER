package com.aicarscaner.mobile.settings

import android.content.Context
import android.content.SharedPreferences
import io.mockk.every
import io.mockk.mockk
import org.junit.Assert.assertEquals
import org.junit.Test

class LauncherOrderStoreTest {
    @Test fun rearrangementKeepsStableIdsAndSurvivesNewAndRemovedSections() {
        val original=listOf(0,14,2,1)
        val changed=moveLauncherItem(original,14,0)
        assertEquals(listOf(14,0,2,1),changed)
        assertEquals(original.toSet(),changed.toSet())
        assertEquals(listOf(14,0,1,9),normalizeLauncherOrder(changed+listOf(14,999),listOf(0,14,1,9)))
        assertEquals(changed,moveLauncherItem(changed,999,0))
    }

    @Test fun aNewStoreRestoresTheUserOrderWithoutChangingOtherPreferences() {
        val context=mockk<Context>()
        val preferences=mockk<SharedPreferences>()
        val editor=mockk<SharedPreferences.Editor>()
        var stored:String?=null
        every {context.applicationContext} returns context
        every {context.getSharedPreferences("layout-test",Context.MODE_PRIVATE)} returns preferences
        every {preferences.getString("order","")} answers {stored}
        every {preferences.edit()} returns editor
        every {editor.putString("order",any())} answers {stored=secondArg();editor}
        every {editor.apply()} returns Unit
        val defaults=listOf(0,14,2)
        LauncherOrderStore(context,"layout-test").save(listOf(14,0,2))
        assertEquals(listOf(14,0,2),LauncherOrderStore(context,"layout-test").load(defaults))
        stored="bad,14,14,999"
        assertEquals(listOf(14,0,2),LauncherOrderStore(context,"layout-test").load(defaults))
    }
}
