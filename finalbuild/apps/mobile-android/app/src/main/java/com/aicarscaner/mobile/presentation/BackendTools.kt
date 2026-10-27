package com.aicarscaner.mobile.presentation

import android.content.Intent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import com.aicarscaner.mobile.data.api.*
import com.aicarscaner.mobile.settings.AppLanguage
import kotlinx.coroutines.*
import java.io.File

/** Native controls; simulation, reasoning, storage and PDF rendering run on Backend. */
@Composable
internal fun BackendTools(mode: String, session: DiagnosticSessionDto?, onOpen: (String) -> Unit = {}, onRefresh: () -> Unit = {}) {
    val context = LocalContext.current
    val language = LocalDashboardLanguage.current
    fun tr(en:String,ru:String,hy:String) = when(language) { AppLanguage.HY->hy; AppLanguage.RU->ru;else->en }
    var expanded by remember(mode) { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    var busy by remember(mode,session?.session_id) { mutableStateOf(false) }
    var output by remember(mode,session?.session_id) { mutableStateOf("") }
    var devices by remember { mutableStateOf(emptyList<com.google.gson.JsonObject>()) }
    var host by remember { mutableStateOf("") }
    var port by remember { mutableStateOf("35000") }
    var pendingDelete by remember(mode,session?.session_id) {mutableStateOf<VehicleProfileDto?>(null)}
    var profiles by remember { mutableStateOf(emptyList<VehicleProfileDto>()) }
    var title by remember { mutableStateOf("") }
    var note by remember { mutableStateOf("") }
    val values = remember { mutableStateMapOf("rpm" to "750", "coolant_c" to "90", "speed_kmh" to "40", "throttle_percent" to "32") }
    val api = ApiClient.diagnosticApi
    fun run(block: suspend () -> String) {
        if (busy) return
        busy=true; output=""
        scope.launch {
            try { output=withTimeout(300_000) { block() }; onRefresh() }
            catch(e:TimeoutCancellationException) {output=tr("Request timed out. Retry when the backend is available.","Истекло время ожидания. Проверьте сервер.","Սպասման ժամանակը սպառվել է։ Ստուգեք backend-ը։")}
            catch(e:CancellationException) { throw e }
            catch(e:Exception) { output=e.message ?: tr("Request failed","Ошибка запроса","Հարցումը ձախողվեց") }
            finally { busy=false }
        }
    }
    fun shown(value: com.google.gson.JsonObject):String {
        fun clean(e:com.google.gson.JsonElement):com.google.gson.JsonElement = when {
            e.isJsonObject -> com.google.gson.JsonObject().also { obj -> e.asJsonObject.entrySet().filter { it.key !in setOf("session_id","connected_device_id") }.forEach { obj.add(it.key,clean(it.value)) } }
            e.isJsonArray -> com.google.gson.JsonArray().also { arr -> e.asJsonArray.forEach { arr.add(clean(it)) } }
            else -> e
        }
        return com.google.gson.GsonBuilder().setPrettyPrinting().create().toJson(clean(value)).replace(session?.session_id ?: "\u0000", "[internal]")
    }
    pendingDelete?.let { profile ->
        AlertDialog(onDismissRequest={pendingDelete=null},
            title={Text(tr("Delete shared vehicle?","Удалить общий автомобиль?","Ջնջե՞լ ընդհանուր մեքենան։"))},
            text={Text("${profile.vehicle.make} ${profile.vehicle.model}")},
            confirmButton={TextButton(onClick={pendingDelete=null;run {api.deleteProfile(profile.id);profiles=api.profiles();tr("Deleted","Удалено","Ջնջված է")}}) {Text(tr("Delete","Удалить","Ջնջել"))}},
            dismissButton={TextButton(onClick={pendingDelete=null}) {Text(tr("Cancel","Отмена","Չեղարկել"))}})
    }
    DemoPanel(when(mode) {
        "decision"->tr("Diagnostic plan","План диагностики","Ախտորոշման պլան")
        "devices"->tr("Server adapters","Адаптеры сервера","Սերվերի ադապտերներ")
        "live"->tr("Acquisition / telemetry","Сбор / телеметрия","Տվյալների հավաքում / վերլուծություն")
        "network"->tr("ECU network","Сеть ЭБУ","ECU ցանց")
        "teach"->tr("Send repair reference","Отправить материал ремонта","Ուղարկել վերանորոգման նյութ")
        "profiles"->tr("Shared vehicles","Общие автомобили","Ընդհանուր մեքենաներ")
        else->tr("Export report","Экспорт отчёта","Արտահանել հաշվետվություն")
    }) {
        TextButton(onClick={expanded=!expanded}) {Text(if(expanded) tr("Close controls","Скрыть управление","Փակել կառավարումը") else tr("Open controls","Открыть управление","Բացել կառավարումը"))}
        if(!expanded) return@DemoPanel
        if(busy) LinearProgressIndicator(Modifier.fillMaxWidth())
        val id=session?.session_id
        if(mode=="devices") {
            Text(tr("Adapters attached to Backend, including USB. Phone-local adapters use VCI controls above.","Адаптеры сервера, включая USB. Локальные адаптеры телефона — в VCI выше.","Backend-ին միացված ադապտերներ՝ ներառյալ USB։ Հեռախոսի տեղային ադապտերները՝ վերևի VCI-ում։"))
            Button(onClick={run {devices=api.devices().getAsJsonArray("devices")?.map {it.asJsonObject} ?: emptyList();""}},enabled=!busy) {Text(tr("Refresh","Обновить","Թարմացնել"))}
            listOf("usb","ble").forEach { transport -> Button(onClick={run {val result=api.scanServerDevices(transport);devices=api.devices().getAsJsonArray("devices")?.map {it.asJsonObject} ?: emptyList();shown(result)}},enabled=!busy) {Text(tr("Scan","Поиск","Որոնել")+" "+transport.uppercase())} }
            OutlinedTextField(host,{host=it},label={Text(tr("Wi-Fi host","Адрес Wi-Fi","Wi-Fi հասցե"))},modifier=Modifier.fillMaxWidth())
            OutlinedTextField(port,{port=it},label={Text(tr("Port","Порт","Պորտ"))},modifier=Modifier.fillMaxWidth())
            Button(onClick={run {val result=api.probeServerWifi(mapOf("host" to host,"port" to (port.toIntOrNull() ?: error("Invalid port"))));devices=api.devices().getAsJsonArray("devices")?.map {it.asJsonObject} ?: emptyList();shown(result)}},enabled=!busy && host.isNotBlank()) {Text(tr("Find Wi-Fi adapter","Найти Wi-Fi адаптер","Գտնել Wi-Fi ադապտերը"))}
            devices.forEach { device ->
                val deviceId=device.get("device_id")?.asString ?: return@forEach
                Text(device.get("model")?.takeUnless {it.isJsonNull}?.asString ?: deviceId)
                val body=mapOf<String,Any>("config" to emptyMap<String,String>())
                Button(onClick={run {shown(api.connectServerDevice(deviceId,body))}},enabled=!busy) {Text(tr("Connect","Подключить","Միացնել"))}
                Button(onClick={run {shown(api.disconnectServerDevice(deviceId))}},enabled=!busy) {Text(tr("Disconnect","Отключить","Անջատել"))}
                Button(onClick={run {shown(api.discoverServerDevice(deviceId,body))}},enabled=!busy) {Text(tr("Identify vehicle","Определить автомобиль","Նույնականացնել մեքենան"))}
                if(id!=null) Button(onClick={run {shown(api.startAcquisition(id,mapOf("adapter" to "bound","device_id" to deviceId)))}},enabled=!busy) {Text(tr("Start Live Data","Запустить данные","Գործարկել տվյալները"))}
            }
        } else if(mode=="profiles") {
            Button(onClick={run { profiles=api.profiles(); tr("Updated","Обновлено","Թարմացված է") }},enabled=!busy) { Text(tr("Refresh vehicles","Обновить автомобили","Թարմացնել մեքենաները")) }
            if(session?.vehicle!=null) Button(onClick={run { api.saveProfile(VehicleProfileRequest("",session.vehicle));profiles=api.profiles();tr("Saved","Сохранено","Պահպանված է") }},enabled=!busy) { Text(tr("Save current vehicle","Сохранить автомобиль","Պահպանել ընթացիկ մեքենան")) }
            profiles.forEach { profile ->
                Text("${profile.vehicle.make} ${profile.vehicle.model} • ${profile.vehicle.year ?: ""}")
                Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                    TextButton(onClick={run { val created=api.createSession(profile.vehicle);onOpen(created.session_id);"" }},enabled=!busy) { Text(tr("Use","Выбрать","Ընտրել")) }
                    if(session?.vehicle!=null) TextButton(onClick={run {api.updateProfile(profile.id,VehicleProfileRequest(profile.name,session.vehicle));profiles=api.profiles();tr("Saved","Сохранено","Պահպանված է")}},enabled=!busy) { Text(tr("Replace with current","Заменить текущим","Փոխարինել ընթացիկով")) }
                    TextButton(onClick={pendingDelete=profile},enabled=!busy) {Text(tr("Delete","Удалить","Ջնջել"))}
                }
            }
        } else if(mode=="teach") {
            OutlinedTextField(title,{title=it},label={Text(tr("Title","Название","Վերնագիր"))},modifier=Modifier.fillMaxWidth())
            OutlinedTextField(note,{note=it},label={Text(tr("Verified repair / measurements","Подтверждённый ремонт / измерения","Հաստատված վերանորոգում / չափումներ"))},minLines=3,modifier=Modifier.fillMaxWidth())
            Text(tr("Reference ingestion; no model training","Добавление справочных данных; без обучения модели","Տեղեկատու նյութի ավելացում․ մոդելը չի ուսուցանվում"))
            Button(onClick={run {shown(api.ingestReference(mapOf("title" to title,"text" to note,"metadata" to mapOf("source" to "user-reported-repair","document_type" to "repair_note"))))}},enabled=!busy && note.isNotBlank() && title.isNotBlank()) { Text(tr("Send to backend","Отправить на сервер","Ուղարկել backend-ին")) }
        } else if(id==null) Text(tr("Create or open a session","Создайте или откройте сеанс","Ստեղծեք կամ բացեք սեսիա"))
        else when(mode) {
            "live" -> {
                Text(tr("Simulator values are SI; they never change a physical car.","Параметры симулятора в СИ; они не изменяют реальный автомобиль.","Սիմուլյատորի արժեքները SI են․ իրական մեքենան չեն փոխում։"))
                Button(onClick={run {shown(api.startAcquisition(id,mapOf("adapter" to "simulator")))}},enabled=!busy) {Text(tr("Start simulator","Запустить симулятор","Գործարկել սիմուլյատորը"))}
                Button(onClick={run {shown(api.startAcquisition(id,mapOf("adapter" to "bound")))}},enabled=!busy) {Text(tr("Start server-connected adapter","Запустить адаптер сервера","Գործարկել սերվերին միացված ադապտերը"))}
                values.keys.toList().forEach { key -> OutlinedTextField(values[key].orEmpty(),{values[key]=it},label={Text(when(key){"rpm"->"RPM";"coolant_c"->tr("Coolant °C","Охлаждение °C","Հովացուցիչ °C");"speed_kmh"->tr("Speed km/h","Скорость км/ч","Արագություն կմ/ժ");else->tr("Throttle %","Дроссель %","Դրոսել %")})},modifier=Modifier.fillMaxWidth()) }
                Button(onClick={run { val numbers=values.mapValues { it.value.toDoubleOrNull()?.takeIf { n->n.isFinite() } ?: error(tr("Enter finite numbers","Введите числа","Մուտքագրեք վերջավոր թվեր")) };shown(api.simulatorParameters(id,numbers)) }},enabled=!busy) {Text(tr("Apply simulator values","Применить параметры","Կիրառել սիմուլյատորի արժեքները"))}
                Button(onClick={run {shown(api.stopAcquisition(id))}},enabled=!busy) {Text(tr("Stop acquisition","Остановить сбор","Դադարեցնել հավաքումը"))}
                Button(onClick={run {shown(api.telemetrySummary(id))}},enabled=!busy) {Text(tr("Telemetry summary","Сводка телеметрии","Տվյալների ամփոփում"))}
                Button(onClick={run {val summary=api.analyzeTelemetry(id);api.analyze(id,language.code);shown(summary)}},enabled=!busy) {Text(tr("Analyze telemetry","Анализ телеметрии","Վերլուծել տվյալները"))}
                Button(onClick={run {shown(api.analyzeLive(id,language.code))}},enabled=!busy) {Text(tr("AI live analysis","ИИ-анализ данных","AI տվյալների վերլուծություն"))}
            }
            "decision" -> {
                Button(onClick={run {shown(api.decisionPlan(id,language.code))}},enabled=!busy) {Text(tr("Refresh plan / missing information","Обновить план / недостающие данные","Թարմացնել պլանը / բացակայող տվյալները"))}
                Button(onClick={run {shown(api.aiProvider())}},enabled=!busy) {Text(tr("AI provider status","Состояние ИИ","AI ծառայության վիճակ"))}
            }
            "network" -> {
                Button(onClick={run {shown(api.networkMap(id))}},enabled=!busy) {Text(tr("Refresh ECU map","Обновить карту ЭБУ","Թարմացնել ECU քարտեզը"))}
                Button(onClick={run {shown(api.activeProbe(id))}},enabled=!busy) {Text(tr("Active read-only probe","Активный опрос без записи","Ակտիվ միայն ընթերցման հարցում"))}
            }
            else -> listOf("pdf","json").forEach { format ->
                Button(onClick={run {
                    val bytes=api.report(id,format,language.code).bytes()
                    val dir=File(context.cacheDir,"reports").apply {mkdirs()};val file=File(dir,"diagnostic-report.$format");file.writeBytes(bytes)
                    val uri=FileProvider.getUriForFile(context,context.packageName+".files",file)
                    context.startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).setType(if(format=="pdf") "application/pdf" else "application/json").putExtra(Intent.EXTRA_STREAM,uri).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION),tr("Share report","Поделиться отчётом","Կիսվել հաշվետվությամբ")))
                    tr("Report ready","Отчёт готов","Հաշվետվությունը պատրաստ է")
                }},enabled=!busy) {Text(tr("Export","Экспорт","Արտահանել")+" "+format.uppercase())}
            }
        }
        if(output.isNotBlank()) Text(output.replace(session?.session_id ?: "\u0000","[internal]"),style=MaterialTheme.typography.bodySmall)
    }
}

@Composable
internal fun BackendConnectionSettings() {
    val context=LocalContext.current
    val language=LocalDashboardLanguage.current
    fun tr(en:String,ru:String,hy:String)=when(language){AppLanguage.HY->hy;AppLanguage.RU->ru;else->en}
    var url by remember {mutableStateOf(ApiClient.BASE_URL)}
    var error by remember {mutableStateOf(false)}
    DemoPanel(tr("Backend connection","Подключение к серверу","Backend կապ")) {
        OutlinedTextField(url,{url=it;error=false},label={Text("API URL")},isError=error,modifier=Modifier.fillMaxWidth())
        Text(tr("Changing servers closes this screen and opens a fresh app session.","Смена сервера откроет приложение заново без активного сеанса.","Սերվերը փոխելիս հավելվածը կբացվի նորից՝ առանց ակտիվ սեսիայի։"))
        Button(onClick={
            val uri=runCatching {java.net.URI(url.trim())}.getOrNull()
            if(uri?.scheme !in listOf("http","https") || uri?.host.isNullOrEmpty() || uri?.rawUserInfo!=null || uri?.rawQuery!=null || uri?.rawFragment!=null) {error=true}
            else {
                context.getSharedPreferences("backend",0).edit().putString("url",url.trim().trimEnd('/')).commit()
                // Clear the Activity task so old session/view-model state is never used on another server.
                ApiClient.changeURL(url.trim())
                val intent=context.packageManager.getLaunchIntentForPackage(context.packageName)!!
                val restart=Intent.makeRestartActivityTask(intent.component)
                context.startActivity(restart)

            }
        }) {Text(tr("Apply and reopen","Применить и открыть заново","Կիրառել և վերաբացել"))}
    }
}
