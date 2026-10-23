package com.aicarscaner.mobile.presentation

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.aicarscaner.mobile.settings.AppLanguage
import com.aicarscaner.mobile.settings.dashboardText

internal val LocalDashboardLanguage = staticCompositionLocalOf { AppLanguage.EN }
@Composable internal fun dashboardLabel(english: String) = dashboardText(LocalDashboardLanguage.current, english)

// Stroke icons stay crisp on small screens and do not depend on emoji fonts.
@Composable
internal fun DashboardIcon(kind: Int, modifier: Modifier = Modifier, color: Color = MaterialTheme.colorScheme.primary) {
    Canvas(modifier.size(24.dp)) {
        val stroke = Stroke(width = 2.dp.toPx())
        val w = size.width; val h = size.height
        when (kind) {
            1, 6 -> { // vehicle / home
                drawRoundRect(color, Offset(w*.12f,h*.4f), Size(w*.76f,h*.35f), androidx.compose.ui.geometry.CornerRadius(3.dp.toPx()), style=stroke)
                drawLine(color,Offset(w*.23f,h*.4f),Offset(w*.34f,h*.2f),stroke.width)
                drawLine(color,Offset(w*.34f,h*.2f),Offset(w*.67f,h*.2f),stroke.width)
                drawLine(color,Offset(w*.67f,h*.2f),Offset(w*.78f,h*.4f),stroke.width)
                drawCircle(color,w*.07f,Offset(w*.28f,h*.78f)); drawCircle(color,w*.07f,Offset(w*.72f,h*.78f))
            }
            3, 12 -> { for (i in 0..3) drawLine(color,Offset(w*(.2f+i*.2f),h*.8f),Offset(w*(.2f+i*.2f),h*(.6f-i*.13f)),4.dp.toPx()) }
            8, 13 -> { drawCircle(color,w*.38f,style=stroke);drawLine(color,Offset(w*.28f,h*.5f),Offset(w*.44f,h*.66f),stroke.width);drawLine(color,Offset(w*.44f,h*.66f),Offset(w*.74f,h*.32f),stroke.width) }
            4, 10 -> { drawCircle(color,w*.34f,Offset(w*.5f,h*.43f),style=stroke);drawLine(color,Offset(w*.4f,h*.78f),Offset(w*.6f,h*.78f),stroke.width);drawLine(color,Offset(w*.5f,h*.1f),Offset(w*.5f,h*.68f),stroke.width);drawCircle(color,w*.1f,Offset(w*.5f,h*.43f),style=stroke) }
            11 -> { for(x in listOf(.3f,.7f)) for(y in listOf(.3f,.7f)) drawRoundRect(color,Offset(w*(x-.12f),h*(y-.12f)),Size(w*.24f,h*.24f),style=stroke) }
            else -> { drawRoundRect(color,Offset(w*.2f,h*.1f),Size(w*.6f,h*.8f),androidx.compose.ui.geometry.CornerRadius(3.dp.toPx()),style=stroke);for(i in 0..2) drawLine(color,Offset(w*.34f,h*(.32f+i*.18f)),Offset(w*.66f,h*(.32f+i*.18f)),stroke.width) }
        }
    }
}

internal val dashboardDestinations = listOf(6 to "Home", 2 to "Adapter", 3 to "Data", 9 to "Reports", 11 to "More")

@Composable
internal fun DashboardBottomBar(selected: Int, navigate: (Int) -> Unit) {
    NavigationBar(containerColor=MaterialTheme.colorScheme.surface, tonalElevation=0.dp, modifier=Modifier.heightIn(min=76.dp)) {
        dashboardDestinations.forEach { (id,title) ->
            NavigationBarItem(selected=selected==id,onClick={navigate(id)}, icon={DashboardIcon(id)},
                label={Text(if(id==9 && LocalDashboardLanguage.current==AppLanguage.HY) "Հաշվետ." else dashboardLabel(title),maxLines=1,style=MaterialTheme.typography.labelSmall)},
                colors=NavigationBarItemDefaults.colors(indicatorColor=MaterialTheme.colorScheme.primary.copy(alpha=.18f)))
        }
    }
}

@Composable
internal fun DashboardSections(navigate: (Int) -> Unit, settings: () -> Unit) {
    val sections=listOf(
        6 to "Dashboard", 1 to "Vehicles", 2 to "VCI / Devices",
        14 to "Diagnostic", 0 to "Symptoms", 3 to "Live Data", 8 to "Tests",
        7 to "DTC", 4 to "AI Analysis", 9 to "Reports", 10 to "Teach AI",
        13 to "Testing progress", 12 to "Custom dashboard", 5 to "Activity"
    )
    sections.forEachIndexed { index,(id,title) ->
        Card(onClick={navigate(id)},modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(12.dp),
            colors=CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface, containerColor=MaterialTheme.colorScheme.surface)) {
            Row(Modifier.padding(16.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(14.dp)) {
                DashboardIcon(id)
                Text(dashboardLabel(title),Modifier.weight(1f),fontWeight=FontWeight.Medium)
                Text("${index+1}",color=MaterialTheme.colorScheme.onSurfaceVariant)
                Text("›",color=MaterialTheme.colorScheme.primary)
            }
        }
    }
    Button(onClick=settings,modifier=Modifier.fillMaxWidth()) { Text(dashboardLabel("Settings")) }
}

/** Persistent actions stay reachable when the page below scrolls. */
@Composable
internal fun DashboardToolbar(
    title:String,
    hasSession:Boolean,
    showBack:Boolean,
    loading:Boolean,
    onHome:()->Unit,
    onSettings:()->Unit,
    onNewSession:()->Unit,
    onSymptoms:()->Unit,
    onAnalyze:()->Unit,
    showSettings:Boolean=true
) {
    val text=com.aicarscaner.mobile.settings.strings(LocalDashboardLanguage.current)
    Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(8.dp)) {
        if(showBack) TextButton(onClick=onHome,contentPadding=PaddingValues(4.dp)) {Text("‹",style=MaterialTheme.typography.headlineMedium)}
        else DashboardIcon(6,Modifier.size(28.dp))
        Text(title,Modifier.weight(1f),style=MaterialTheme.typography.titleMedium,fontWeight=FontWeight.Bold,color=MaterialTheme.colorScheme.onSurface)
        if(showSettings) TextButton(onClick=onSettings,contentPadding=PaddingValues(4.dp)) {Text("⚙",modifier=Modifier.semantics{contentDescription=text.settings})}
        if(hasSession) TextButton(onClick=onNewSession,contentPadding=PaddingValues(4.dp)) {Text("+",modifier=Modifier.semantics{contentDescription=text.newSession},style=MaterialTheme.typography.titleLarge)}
    }
    if(hasSession) Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(8.dp)) {
        FilledTonalButton(onClick=onSymptoms,modifier=Modifier.weight(1f),enabled=!loading) {Text(text.symptoms)}
        Button(onClick=onAnalyze,modifier=Modifier.weight(1f),enabled=!loading) {Text(dashboardLabel("Analyze session"))}
    }
}
