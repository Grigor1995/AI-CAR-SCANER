package com.aicarscaner.mobile.presentation

import android.content.Intent
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.ui.Alignment
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.contentDescription
import com.aicarscaner.mobile.settings.strings
import com.aicarscaner.mobile.settings.localizedState
import com.aicarscaner.mobile.settings.localizedEvidenceStatus
import kotlin.math.roundToInt
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.aicarscaner.mobile.data.api.DiagnosticSessionDto
import com.aicarscaner.mobile.data.obd.LiveDataSnapshot

@Composable
internal fun DemoPanel(title: String, content: @Composable ColumnScope.() -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = androidx.compose.foundation.shape.RoundedCornerShape(16.dp),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = .45f)),
        colors = CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface, containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            if (title.isNotEmpty()) Text(title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            content()
        }
    }
}

@Composable
internal fun DemoHome(session: DiagnosticSessionDto, titles: List<String>, navigate: (Int) -> Unit) {
    val language = LocalDashboardLanguage.current
    val completed = latestTestProgress(session)
    DemoPanel("") {
        session.vehicle?.let { VehicleModelArtwork(it.make, it.model, it.chassis.orEmpty(),height=130.dp) }
        Text(session.vehicle?.let { "${it.make} ${it.model}" } ?: "—", modifier=Modifier.fillMaxWidth().clickable {navigate(1)}, textAlign=TextAlign.Center, style=MaterialTheme.typography.titleLarge, fontWeight=FontWeight.Bold)
        Text(session.vehicle?.let { "${it.chassis.orEmpty()} • ${it.year ?: "—"} • ${it.engine.orEmpty()}" } ?: "—", modifier=Modifier.fillMaxWidth(), textAlign=TextAlign.Center, color=MaterialTheme.colorScheme.onSurfaceVariant)
        Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
            DemoMetric("DTC",session.dtcs.size,Color(0xFFFF5D79),Modifier.weight(1f))
            DemoMetric(dashboardLabel("Completed"),completed.first,Color(0xFF21D6A0),Modifier.weight(1f))
            DemoMetric(dashboardLabel("AI hypotheses"),session.hypotheses.size,Color(0xFFB67CFF),Modifier.weight(1f))
        }
    }
    Text(dashboardLabel("Quick actions"),style=MaterialTheme.typography.titleSmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
    listOf(listOf(7 to "DTC list & details",3 to "Live data"),listOf(8 to "Guided tests",4 to "AI analysis")).forEach { row ->
        Row(horizontalArrangement=Arrangement.spacedBy(10.dp)) {
            row.forEach { (id,title) ->
                Card(onClick={navigate(id)},modifier=Modifier.weight(1f),shape=RoundedCornerShape(12.dp),border=BorderStroke(1.dp,MaterialTheme.colorScheme.primary.copy(alpha=.45f)),colors=CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface, containerColor=MaterialTheme.colorScheme.surface)) {
                    Row(Modifier.padding(14.dp).heightIn(min=36.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(10.dp)) {
                        DashboardIcon(id,color=if(id==4) Color(0xFFB67CFF) else MaterialTheme.colorScheme.primary)
                        Text(dashboardLabel(title),style=MaterialTheme.typography.labelLarge)
                    }
                }
            }
        }
    }
    DemoPanel(dashboardLabel("Testing progress")) {
        LinearProgressIndicator(progress={if(completed.second==0) 0f else completed.first.toFloat()/completed.second},modifier=Modifier.fillMaxWidth())
        Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween) {
            Text("${completed.first}/${completed.second}",fontWeight=FontWeight.Bold)
            Text(localizedState(language,session.state),style=MaterialTheme.typography.labelSmall)
        }
        Text(dashboardLabel("Incomplete results remain open"),style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
        TextButton(onClick={navigate(13)}) { Text(dashboardLabel("View details")+" ›") }
    }
}

internal fun latestTestProgress(session: DiagnosticSessionDto): Pair<Int,Int> {
    val latest=session.test_results.associateBy { it.test_id }
    val completed=latest.values.count { it.result=="PASS" || it.result=="FAIL" }
    val all=session.recommendations.map { it.id }.toSet()+latest.keys
    return completed to all.size
}

@Composable
internal fun DemoProgress(session: DiagnosticSessionDto, openTests: () -> Unit) {
    val (done,total)=latestTestProgress(session)
    val fraction=if(total==0) 0f else done.toFloat()/total
    val accent=MaterialTheme.colorScheme.primary
    val track=MaterialTheme.colorScheme.surfaceVariant
    val extra=strings(LocalDashboardLanguage.current).extra
    DemoPanel(dashboardLabel("Testing progress")) {
        Box(Modifier.fillMaxWidth().height(180.dp),contentAlignment=Alignment.Center) {
            Canvas(Modifier.size(154.dp)) {
                drawArc(track,-90f,360f,false,style=Stroke(14.dp.toPx()))
                if(fraction>0) drawArc(accent,-90f,360f*fraction,false,style=Stroke(14.dp.toPx(),cap=androidx.compose.ui.graphics.StrokeCap.Round))
            }
            Column(horizontalAlignment=Alignment.CenterHorizontally) {
                Text("$done/$total",style=MaterialTheme.typography.headlineLarge,fontWeight=FontWeight.Bold)
                Text("${(fraction*100).roundToInt()}%",color=accent)
            }
        }
        Text(dashboardLabel("Incomplete results remain open"),color=MaterialTheme.colorScheme.onSurfaceVariant)
        val latest=session.test_results.associateBy { it.test_id }
        latest.values.forEachIndexed { index,result ->
            Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(10.dp)) {
                Text("${index+1}",color=accent)
                Text(result.testName ?: result.test_id.take(8),Modifier.weight(1f))
                Text(when(result.result){"PASS"->extra.pass;"FAIL"->extra.fail;else->extra.incomplete},color=outcomeColor(result.result),style=MaterialTheme.typography.labelSmall)
            }
        }
        if(latest.isEmpty()) Text(dashboardLabel("No test results yet"))
        Button(onClick=openTests,modifier=Modifier.fillMaxWidth()) { Text(dashboardLabel("Open tests")) }
    }
}

private fun outcomeColor(result:String)=when(result){"PASS"->Color(0xFF21D6A0);"FAIL"->Color(0xFFFF5D79);else->Color(0xFFFFC663)}

@Composable
private fun DemoMetric(title: String, count: Int, color: Color, modifier: Modifier) {
    Card(modifier = modifier, colors=CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface, containerColor=color.copy(alpha=.10f)), border = BorderStroke(1.dp, color.copy(alpha = .55f))) {
        Column(Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(count.toString(), color = color, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
            Text(title, style = MaterialTheme.typography.labelSmall)
        }
    }
}

@Composable
internal fun DemoDtcList(session: DiagnosticSessionDto, title: String) {
    val language=LocalDashboardLanguage.current
    val extra=strings(language).extra
    Text(dashboardLabel("DTC list & details"),style=MaterialTheme.typography.titleLarge,fontWeight=FontWeight.Bold)
    Text(dashboardLabel("Reported codes do not confirm a component failure."),style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
    session.dtcs.forEach { code ->
        var expanded by remember(code.code) { mutableStateOf(false) }
        val color=MaterialTheme.colorScheme.error
        Card(onClick={expanded=!expanded},modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(14.dp),border=BorderStroke(1.dp,color.copy(alpha=.35f)),colors=CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface, containerColor=MaterialTheme.colorScheme.surface)) {
            Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(10.dp)) {
                Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                    Text("!",color=color,style=MaterialTheme.typography.headlineMedium,fontWeight=FontWeight.Black)
                    Column(Modifier.weight(1f)) {
                        Text(code.code,color=color,style=MaterialTheme.typography.titleLarge,fontWeight=FontWeight.Bold)
                        Text(code.description ?: dashboardLabel("No description supplied"),style=MaterialTheme.typography.bodyMedium)
                    }
                    Text(if(expanded) "⌄" else "›",color=MaterialTheme.colorScheme.primary)
                }
                if(expanded) {
                    HorizontalDivider()
                    Text(dashboardLabel("Evidence"),fontWeight=FontWeight.Bold)
                    session.evidence.filter { it.fact.contains(code.code,true) }.forEach {
                        Text("${localizedEvidenceStatus(language,it.status,extra)} • ${it.fact}",style=MaterialTheme.typography.bodySmall)
                    }
                    if(session.evidence.none { it.fact.contains(code.code,true) }) Text(dashboardLabel("No measurements"))
                }
            }
        }
    }
    if(session.dtcs.isEmpty()) DemoPanel(dashboardLabel("No diagnostic codes")) { Text(dashboardLabel("Read codes from your adapter or add a DTC in Diagnostics.")) }
}

@Composable
internal fun DemoGuidedTests(session: DiagnosticSessionDto, title: String, record: (String,String)->Unit) {
    val extra=strings(LocalDashboardLanguage.current).extra
    Text(title,style=MaterialTheme.typography.titleLarge,fontWeight=FontWeight.Bold)
    session.recommendations.forEachIndexed { index,test ->
        DemoPanel("${index+1}  ${test.title}") {
            Text(test.purpose)
            test.prerequisites.forEach { Text("• $it",style=MaterialTheme.typography.bodySmall) }
            test.safety_notes.forEach { Text(it,color=MaterialTheme.colorScheme.error,style=MaterialTheme.typography.bodySmall) }
            Button(onClick={record(test.id,test.title)},modifier=Modifier.fillMaxWidth()) { Text(dashboardLabel("Record result")) }
        }
    }
    if(session.recommendations.isEmpty()) DemoPanel(dashboardLabel("No recommended tests yet")) { Text(dashboardLabel("Add symptoms and analyze the session to get recommended tests.")) }
    if(session.test_results.isNotEmpty()) Text(dashboardLabel("Recorded results"),style=MaterialTheme.typography.titleSmall)
    session.test_results.associateBy { it.test_id }.values.forEach { result ->
        DemoPanel(result.testName ?: result.test_id.take(8)) { Text(when(result.result){"PASS"->extra.pass;"FAIL"->extra.fail;else->extra.incomplete},color=outcomeColor(result.result),fontWeight=FontWeight.Bold) }
    }
}

private data class ChartChannel(val key:String,val unit:String,val color:Color,val values:List<Double>)
private fun channels(history:List<LiveDataSnapshot>)=listOf(
    ChartChannel("RPM","rpm",Color(0xFF20B9FF),history.mapNotNull{it.rpm}),
    ChartChannel("Coolant","°C",Color(0xFFFF5D79),history.mapNotNull{it.coolantC}),
    ChartChannel("MAP pressure","kPa",Color(0xFFB67CFF),history.mapNotNull{it.mapKpa}),
    ChartChannel("Speed","km/h",Color(0xFF21D6A0),history.mapNotNull{it.speedKph}),
    ChartChannel("Engine load","%",Color(0xFFFFC663),history.mapNotNull{it.engineLoadPct}),
    ChartChannel("Intake air","°C",Color(0xFF20B9FF),history.mapNotNull{it.intakeAirC}),
    ChartChannel("Throttle","%",Color(0xFFB67CFF),history.mapNotNull{it.throttlePct})
)

@Composable
private fun ChannelTrace(channel:ChartChannel,modifier:Modifier=Modifier) {
    val grid=MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha=.16f)
    Canvas(modifier.fillMaxWidth().height(68.dp)) {
        for(line in 1..3) drawLine(grid,Offset(0f,size.height*line/4),Offset(size.width,size.height*line/4))
        val values=channel.values
        if(values.size>=2){
            val min=values.minOrNull() ?: 0.0
            val span=((values.maxOrNull() ?: 0.0)-min).coerceAtLeast(.00001)
            val path=Path()
            values.forEachIndexed { index,value ->
                val x=size.width*index/(values.size-1)
                val y=size.height*(.92f-.84f*((value-min)/span).toFloat())
                if(index==0) path.moveTo(x,y) else path.lineTo(x,y)
            }
            drawPath(path,channel.color,style=Stroke(width=2.dp.toPx()))
        }
    }
}

@Composable
internal fun DemoLiveCharts(history:List<LiveDataSnapshot>,dashboard:Boolean=false) {
    val all=channels(history)
    val removeLabel=dashboardLabel("Remove widget")
    var visible by remember { mutableStateOf(setOf("RPM","Coolant","MAP pressure","Speed")) }
    var adding by remember { mutableStateOf(false) }
    if(history.isEmpty()) Text(dashboardLabel("Connect an adapter and start live data to see measured values."),color=MaterialTheme.colorScheme.onSurfaceVariant)
    val shown=all.filter { it.key in visible }
    if(dashboard){
        shown.chunked(2).forEach { row ->
            Row(horizontalArrangement=Arrangement.spacedBy(10.dp)) {
                row.forEach { channel ->
                    Box(Modifier.weight(1f)) { DemoPanel("") {
                        Row(verticalAlignment=Alignment.CenterVertically) {
                            Text(dashboardLabel(channel.key),Modifier.weight(1f),style=MaterialTheme.typography.labelMedium)
                            TextButton(onClick={visible=visible-channel.key},modifier=Modifier.size(32.dp),contentPadding=PaddingValues(0.dp)) { Text("×",modifier=Modifier.semantics{contentDescription=removeLabel}) }
                        }
                        Text(channel.values.lastOrNull()?.let{"%.1f".format(it)} ?: "—",style=MaterialTheme.typography.headlineMedium,color=channel.color,fontWeight=FontWeight.Bold)
                        Text(channel.unit,style=MaterialTheme.typography.labelSmall)
                        ChannelTrace(channel)
                    } }
                }
                if(row.size==1) Spacer(Modifier.weight(1f))
            }
        }
        OutlinedButton(onClick={adding=true},enabled=visible.size<all.size,modifier=Modifier.fillMaxWidth()) { Text("+ "+dashboardLabel("Add widget")) }
        if(adding) AlertDialog(onDismissRequest={adding=false},title={Text(dashboardLabel("Add widget"))},text={Column{all.filter{it.key !in visible}.forEach{channel->TextButton(onClick={visible=visible+channel.key;adding=false}){Text(dashboardLabel(channel.key))}}}},confirmButton={TextButton(onClick={adding=false}){Text(strings(LocalDashboardLanguage.current).cancel)}})
    }else{
        shown.forEach { channel -> DemoPanel(dashboardLabel(channel.key)) {
            Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween) {
                Text(channel.values.lastOrNull()?.let{"%.1f ${channel.unit}".format(it)} ?: "—",style=MaterialTheme.typography.titleLarge,color=channel.color,fontWeight=FontWeight.Bold)
                Text(dashboardLabel("Last measured value"),style=MaterialTheme.typography.labelSmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
            }
            ChannelTrace(channel)
        } }
    }
}

@Composable
internal fun DemoHypotheses(session:DiagnosticSessionDto) {
    Text(dashboardLabel("AI hypotheses"),style=MaterialTheme.typography.titleLarge,fontWeight=FontWeight.Bold)
    Text(dashboardLabel("Scores describe supporting evidence, not confirmed failures."),style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
    session.hypotheses.forEachIndexed { index,hypothesis ->
        var expanded by remember(hypothesis.id){mutableStateOf(false)}
        val colors=listOf(Color(0xFF20B9FF),Color(0xFF21D6A0),Color(0xFFFFC663),Color(0xFFB67CFF))
        val color=colors[index%colors.size]
        Card(onClick={expanded=!expanded},modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(14.dp),colors=CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface, containerColor=MaterialTheme.colorScheme.surface),border=BorderStroke(1.dp,color.copy(alpha=.3f))){
            Column(Modifier.padding(14.dp),verticalArrangement=Arrangement.spacedBy(10.dp)) {
                Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(10.dp)) {
                    Surface(shape=RoundedCornerShape(30.dp),color=color.copy(alpha=.2f)){Text("${index+1}",Modifier.padding(horizontal=11.dp,vertical=6.dp),color=color,fontWeight=FontWeight.Bold)}
                    Text(hypothesis.category,Modifier.weight(1f),fontWeight=FontWeight.SemiBold)
                    Text(if(expanded) "⌄" else "›",color=color)
                }
                Text(hypothesis.statement,style=MaterialTheme.typography.bodySmall,maxLines=if(expanded) Int.MAX_VALUE else 2,color=MaterialTheme.colorScheme.onSurfaceVariant)
                val score=hypothesis.status.substringAfterLast(":", "").toDoubleOrNull()?.takeIf {it in 0.0..1.0}
                if(score!=null){
                    Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween){Text(dashboardLabel("Evidence score"),style=MaterialTheme.typography.labelSmall);Text("${(score*100).roundToInt()}%",color=color,style=MaterialTheme.typography.labelSmall)}
                    LinearProgressIndicator(progress={score.toFloat()},color=color,modifier=Modifier.fillMaxWidth())
                }
                if(expanded){
                    val ids=hypothesis.supporting_evidence_ids+hypothesis.contradicting_evidence_ids
                    session.evidence.filter{it.id in ids}.forEach { Text("• ${it.fact}",style=MaterialTheme.typography.bodySmall) }
                    Text(hypothesis.status,style=MaterialTheme.typography.labelSmall,color=color)
                }
            }
        }
    }
    if(session.hypotheses.isEmpty()) DemoPanel(dashboardLabel("No hypotheses yet")){Text(dashboardLabel("Add symptoms and analyze the session to get recommended tests."))}
}

@Composable
internal fun DemoReports(session: DiagnosticSessionDto, title: String, shareLabel: String) {
    val context = LocalContext.current
    DemoPanel(title) {
        Text(session.vehicle?.let { "${it.make} ${it.model}" } ?: "—", style = MaterialTheme.typography.titleLarge)
        Text(session.session_id)
        Text("DTC: ${session.dtcs.size} • ${localizedState(LocalDashboardLanguage.current,session.state)}")
        Button(onClick = {
            val intent = Intent(Intent.ACTION_SEND).apply {
                type = "text/plain"
                putExtra(Intent.EXTRA_TEXT, com.google.gson.Gson().toJson(session))
            }
            context.startActivity(Intent.createChooser(intent, shareLabel))
        }, modifier = Modifier.fillMaxWidth()) { Text(shareLabel) }
        session.audit_log.takeLast(20).reversed().forEach { Text(it.event) }
    }
}

@Composable
internal fun DemoTeach(title:String,draftLabel:String,shareLabel:String) {
    val context=LocalContext.current
    val preferences=remember {context.getSharedPreferences("repair_notes",0)}
    val keys=listOf("Vehicle / model","Observed problem","DTC codes","Measurements","Repair / solution","Verified outcome")
    val values=remember {mutableStateMapOf<String,String>().apply {keys.forEach {key->put(key,preferences.getString(key,if(key=="Repair / solution") preferences.getString("draft","") else "").orEmpty())}}}
    val labels=keys.associateWith {dashboardLabel(it)}
    Text(title,style=MaterialTheme.typography.titleLarge,fontWeight=FontWeight.Bold)
    Text(draftLabel,style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
    keys.forEach {key->
        OutlinedTextField(value=values[key].orEmpty(),onValueChange={value->values[key]=value;preferences.edit().putString(key,value).apply()},modifier=Modifier.fillMaxWidth(),minLines=if(key=="Observed problem" || key=="Repair / solution") 3 else 1,label={Text(labels[key].orEmpty())})
    }
    Button(onClick={
        val note=keys.filter{!values[it].isNullOrBlank()}.joinToString("\n\n"){"${labels[it]}: ${values[it]}"}
        val intent=Intent(Intent.ACTION_SEND).apply{type="text/plain";putExtra(Intent.EXTRA_TEXT,note)}
        context.startActivity(Intent.createChooser(intent,shareLabel))
    },enabled=values.values.any{it.isNotBlank()},modifier=Modifier.fillMaxWidth()){Text(shareLabel)}
}

@Composable
internal fun DemoAdapterHeader(connected:Boolean,status:String){
    val color=if(connected) Color(0xFF21D6A0) else MaterialTheme.colorScheme.primary
    DemoPanel(dashboardLabel("Adapter connection")) {
        Icon(
            painter = androidx.compose.ui.res.painterResource(com.aicarscaner.mobile.R.drawable.ic_obd_connector),
            contentDescription = "OBD-II",
            tint = color,
            modifier = Modifier.align(Alignment.CenterHorizontally).size(width = 144.dp, height = 96.dp)
        )
        Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(12.dp)) {
            DashboardIcon(if(connected) 8 else 2,color=color)
            Column {Text("OBD-II",fontWeight=FontWeight.Bold,color=color);Text(status,style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)}
        }
    }
}
