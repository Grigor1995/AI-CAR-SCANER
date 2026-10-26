package com.aicarscaner.mobile.presentation

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.ScrollState
import androidx.compose.foundation.gestures.detectDragGesturesAfterLongPress
import androidx.compose.foundation.gestures.scrollBy
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.boundsInRoot
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.semantics.CustomAccessibilityAction
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.customActions
import androidx.compose.ui.unit.IntOffset
import com.aicarscaner.mobile.settings.LauncherOrderStore
import com.aicarscaner.mobile.settings.moveLauncherItem
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlin.math.roundToInt
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
                // Shared 4x3 atlas order matches Desktop: 11,3,2,1,4,6,8,7,9,10,0,5.
                // Android route IDs are different; map by workflow meaning.
                val index=when(kind) {
                    0->0; 14->1; 2->2; 3->4; 8,13->5; 4->6
                    7->7; 9->8; 10->9; 6,12->10; 5->11; else->10
                }
                val width=sheet.width/4;val height=sheet.height/3
                Bitmap.createBitmap(sheet,index%4*width,index/4*height,(width*.96f).toInt(),height)
            }.asImageBitmap()
        }
}
@Composable
internal fun DashboardIcon(kind: Int, modifier: Modifier = Modifier.size(24.dp), color: Color = MaterialTheme.colorScheme.primary) {
    val resources=LocalContext.current.resources
    val icon=remember(kind,resources) {DesktopIconCache.image(resources,kind)}
    Image(bitmap=icon,contentDescription=null,modifier=modifier)
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
internal fun DashboardSections(
    scrollState: ScrollState? = null,
    orderStore: LauncherOrderStore? = null,
    navigate: (Int) -> Unit
) {
    val sections=listOf(
        0 to "Symptoms", 14 to "Diagnostic", 2 to "VCI / Devices", 1 to "Vehicles", 3 to "Live Data", 8 to "Tests",
        4 to "AI Analysis", 7 to "DTC", 9 to "Reports", 10 to "Teach AI",
        6 to "Dashboard", 5 to "Activity", 13 to "Testing progress", 12 to "Custom dashboard"
    )
    val context=LocalContext.current
    val store=remember(context,orderStore) { orderStore ?: LauncherOrderStore(context) }
    var order by remember(store) { mutableStateOf(store.load(sections.map {it.first})) }
    val bounds=remember {mutableMapOf<Int,Rect>()}
    var gridOrigin by remember {mutableStateOf(Offset.Zero)}
    var dragging by remember {mutableStateOf<Int?>(null)}
    var pointer by remember {mutableStateOf(Offset.Zero)}
    var grabOffset by remember {mutableStateOf(Offset.Zero)}
    var sourceSize by remember {mutableStateOf(androidx.compose.ui.geometry.Size.Zero)}
    var target by remember {mutableStateOf<Int?>(null)}
    val density=LocalDensity.current
    val viewportHeight=LocalView.current.height.toFloat()
    val edge=with(density) {88.dp.toPx()}
    val scrollStep=with(density) {10.dp.toPx()}
    val earlier=dashboardLabel("Move earlier")
    val later=dashboardLabel("Move later")
    fun move(source:Int,destination:Int) {
        val next=moveLauncherItem(order,source,destination)
        if(next!=order) {order=next;store.save(next)}
    }
    LaunchedEffect(dragging,scrollState) {
        while(isActive && dragging!=null) {
            val delta=when {pointer.y<edge*2 -> -scrollStep;pointer.y>viewportHeight-edge -> scrollStep;else->0f}
            if(delta!=0f) scrollState?.scrollBy(delta)
            target=bounds.entries.firstOrNull {it.value.contains(pointer)}?.key
            delay(16)
        }
    }
    Text(dashboardLabel("Main menu"),style=MaterialTheme.typography.headlineSmall,fontWeight=FontWeight.Bold)
    Text(dashboardLabel("Hold and drag to reorder"),style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
    BoxWithConstraints(Modifier.onGloballyPositioned {gridOrigin=it.boundsInRoot().topLeft}) {
        val columns=if(maxWidth>=600.dp) 3 else 2
        val byId=sections.toMap()
        Column(verticalArrangement=Arrangement.spacedBy(12.dp)) {
            order.chunked(columns).forEach { row ->
                Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                    row.forEach { id ->
                        val title=byId.getValue(id)
                        Card(onClick={if(dragging==null) navigate(id)},
                            modifier=Modifier.weight(1f).heightIn(min=112.dp)
                                .onGloballyPositioned {bounds[id]=it.boundsInRoot()}
                                .graphicsLayer {alpha=if(dragging==id) .35f else 1f}
                                .semantics {
                                    customActions=listOf(
                                        CustomAccessibilityAction(earlier) {val index=order.indexOf(id);if(index>0) move(id,order[index-1]);true},
                                        CustomAccessibilityAction(later) {val index=order.indexOf(id);if(index<order.lastIndex) move(id,order[index+1]);true}
                                    )
                                }
                                .pointerInput(id) {
                                    detectDragGesturesAfterLongPress(
                                        onDragStart={local ->
                                            bounds[id]?.let {rect ->
                                                dragging=id;grabOffset=local;pointer=rect.topLeft+local;sourceSize=rect.size;target=id
                                            }
                                        },
                                        onDrag={change,_ ->
                                            change.consume()
                                            pointer=(bounds[id]?.topLeft ?: Offset.Zero)+change.position
                                            target=bounds.entries.firstOrNull {it.value.contains(pointer)}?.key
                                        },
                                        onDragEnd={
                                            val destination=bounds.entries.firstOrNull {it.value.contains(pointer)}?.key
                                            if(destination!=null) move(id,destination)
                                            dragging=null;target=null
                                        },
                                        onDragCancel={dragging=null;target=null}
                                    )
                                },
                            shape=RoundedCornerShape(18.dp),
                            colors=CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface,containerColor=Color.Transparent),
                            border=BorderStroke(if(target==id && dragging!=null) 2.dp else 1.dp,MaterialTheme.colorScheme.primary.copy(alpha=.65f)),
                            elevation=CardDefaults.cardElevation(9.dp)) {
                            LauncherTileContent(id,dashboardLabel(title))
                        }
                    }
                    repeat(columns-row.size) {Spacer(Modifier.weight(1f))}
                }
            }
        }
        dragging?.let {id ->
            Card(modifier=Modifier.offset {val at=pointer-grabOffset-gridOrigin;IntOffset(at.x.roundToInt(),at.y.roundToInt())}
                .size(with(density){sourceSize.width.toDp()},with(density){sourceSize.height.toDp()})
                .clearAndSetSemantics {},shape=RoundedCornerShape(18.dp),
                border=BorderStroke(2.dp,MaterialTheme.colorScheme.primary),elevation=CardDefaults.cardElevation(12.dp)) {
                LauncherTileContent(id,dashboardLabel(byId.getValue(id)))
            }
        }
    }
}

@Composable
private fun LauncherTileContent(id:Int,title:String) {
    // Same text-only Main menu cards as Desktop and iOS.
    Column(Modifier.fillMaxWidth().heightIn(min=104.dp).background(desktopPanelBrush()).padding(12.dp),
        horizontalAlignment=Alignment.CenterHorizontally,verticalArrangement=Arrangement.Center) {
        Text(title,style=MaterialTheme.typography.titleMedium,fontWeight=FontWeight.Bold,
            textAlign=androidx.compose.ui.text.style.TextAlign.Center)
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
            TextButton(onClick={menuOpen=true},contentPadding=PaddingValues(4.dp)) { Text("⋮",modifier=Modifier.semantics{contentDescription="Application menu"}) }
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
