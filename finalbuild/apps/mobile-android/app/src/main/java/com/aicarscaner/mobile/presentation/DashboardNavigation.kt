package com.aicarscaner.mobile.presentation

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.BorderStroke
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.LocalContext
import android.graphics.BitmapFactory
import android.graphics.Bitmap
import com.aicarscaner.mobile.R
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

// Reuse cropped artwork across all pages rather than decoding the large atlas per icon.
private object DesktopIconCache {
    private val images=mutableMapOf<Int,androidx.compose.ui.graphics.ImageBitmap>()
    private var atlas:Bitmap?=null
    @Synchronized fun image(resources:android.content.res.Resources,kind:Int):androidx.compose.ui.graphics.ImageBitmap =
        images.getOrPut(kind) {
            if(kind==1 || kind==11) BitmapFactory.decodeResource(resources,R.drawable.launcher_car)
            else {
                val sheet=atlas ?: BitmapFactory.decodeResource(resources,R.drawable.launcher_icons).also {atlas=it}
                val index=when(kind) {0->0;14->1;2->2;3,12->4;8,13->5;4->6;7->7;9->8;10->9;6->10;else->11}
                val width=sheet.width/4;val height=sheet.height/3
                Bitmap.createBitmap(sheet,index%4*width,index/4*height,(width*.96f).toInt(),height)
            }.asImageBitmap()
        }
}
@Composable
internal fun DashboardIcon(kind: Int, modifier: Modifier = Modifier, color: Color = MaterialTheme.colorScheme.primary) {
    val resources=LocalContext.current.resources
    val icon=remember(kind,resources) {DesktopIconCache.image(resources,kind)}
    Image(bitmap=icon,contentDescription=null,modifier=modifier.size(24.dp))
}

@Composable
internal fun desktopPanelBrush(): Brush = Brush.verticalGradient(listOf(
    MaterialTheme.colorScheme.surfaceVariant, MaterialTheme.colorScheme.surface,
    MaterialTheme.colorScheme.background))

@Composable
internal fun DesktopBackground(modifier: Modifier = Modifier) {
    Image(painter=androidx.compose.ui.res.painterResource(R.drawable.launcher_background),
        contentDescription=null,contentScale=androidx.compose.ui.layout.ContentScale.Crop,
        alpha=if(MaterialTheme.colorScheme.background.luminanceForNeon()) .22f else .07f,
        modifier=modifier.fillMaxSize())
}
private fun Color.luminanceForNeon() = red + green + blue < 1f

internal val dashboardDestinations = listOf(11 to "Main menu", 2 to "Adapter", 3 to "Data", 9 to "Reports", 0 to "Symptoms")

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
internal fun DashboardSections(navigate: (Int) -> Unit) {
    val sections=listOf(
        0 to "Symptoms", 14 to "Diagnostic", 2 to "VCI / Devices", 1 to "Vehicles", 3 to "Live Data", 8 to "Tests",
        4 to "AI Analysis", 7 to "DTC", 9 to "Reports", 10 to "Teach AI",
        6 to "Dashboard", 5 to "Activity", 13 to "Testing progress", 12 to "Custom dashboard"
    )
    Text(dashboardLabel("Main menu"),style=MaterialTheme.typography.headlineSmall,fontWeight=FontWeight.Bold)
    BoxWithConstraints {
    val columns=if(maxWidth >= 600.dp) 3 else 2
    Column(verticalArrangement=Arrangement.spacedBy(12.dp)) {
    sections.chunked(columns).forEach { pair ->
        Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(12.dp)) {
            pair.forEach { (id,title) ->
                Card(onClick={navigate(id)},modifier=Modifier.weight(1f).heightIn(min=124.dp),shape=RoundedCornerShape(18.dp),
                    colors=CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface,containerColor=Color.Transparent),border=BorderStroke(1.dp,MaterialTheme.colorScheme.primary.copy(alpha=.65f)),elevation=CardDefaults.cardElevation(5.dp)) {
                    Column(Modifier.fillMaxWidth().background(desktopPanelBrush()).padding(14.dp),horizontalAlignment=Alignment.CenterHorizontally,verticalArrangement=Arrangement.spacedBy(14.dp)) {
                        DashboardIcon(id,Modifier.size(64.dp))
                        Text(dashboardLabel(title),fontWeight=FontWeight.Medium,textAlign=androidx.compose.ui.text.style.TextAlign.Center)
                    }
                }
            }
            repeat(columns-pair.size) { Spacer(Modifier.weight(1f)) }
        }
    }
    }
    }
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
    onAnalyze:()->Unit
) {
    val text=com.aicarscaner.mobile.settings.strings(LocalDashboardLanguage.current)
    Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(8.dp)) {
        if(showBack) TextButton(onClick=onHome,contentPadding=PaddingValues(4.dp)) {Text("‹",style=MaterialTheme.typography.headlineMedium)}
        else DashboardIcon(11,Modifier.size(36.dp))
        Text(title,Modifier.weight(1f),style=MaterialTheme.typography.titleMedium,fontWeight=FontWeight.Bold,color=MaterialTheme.colorScheme.onSurface)
        var menuOpen by remember { mutableStateOf(false) }
        Box {
            TextButton(onClick={menuOpen=true},contentPadding=PaddingValues(4.dp)) { Text("⋮",modifier=Modifier.semantics{contentDescription=text.settings}) }
            DropdownMenu(expanded=menuOpen,onDismissRequest={menuOpen=false}) {
                DropdownMenuItem(text={Text(text.settings)},onClick={menuOpen=false;onSettings()})
            }
        }
        if(hasSession) TextButton(onClick=onNewSession,contentPadding=PaddingValues(4.dp)) {Text("+",modifier=Modifier.semantics{contentDescription=text.newSession},style=MaterialTheme.typography.titleLarge)}
    }
    if(hasSession) Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(8.dp)) {
        FilledTonalButton(onClick=onSymptoms,modifier=Modifier.weight(1f),enabled=!loading) {Text(text.symptoms)}
        Button(onClick=onAnalyze,modifier=Modifier.weight(1f),enabled=!loading) {Text(dashboardLabel("Analyze session"))}
    }
}
