package com.aicarscaner.mobile.presentation

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.aicarscaner.mobile.data.api.ApiClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/** Account browser only. Business mutations remain typed backend workflows.
 * Password and bearer are memory-only, never preferences or saved-instance state.
 */
@Composable
internal fun BusinessWorkspace(fixedWorkspace:String?=null,onClose:()->Unit) {
    val scope=rememberCoroutineScope()
    val context=LocalContext.current
    var base by remember {mutableStateOf(ApiClient.BASE_URL.trimEnd('/'))}
    val client=remember {OkHttpClient.Builder().connectTimeout(15,TimeUnit.SECONDS).readTimeout(15,TimeUnit.SECONDS).followRedirects(false).followSslRedirects(false).build()}
    var businessName by remember {mutableStateOf("")}
    var address by remember {mutableStateOf("")}
    var onboarding by remember {mutableStateOf(false)}
    var fullName by remember {mutableStateOf("")}
    var email by remember {mutableStateOf("")};var password by remember {mutableStateOf("")}
    var token by remember {mutableStateOf("")};var modes by remember {mutableStateOf(emptyList<String>())}
    var language by remember {mutableStateOf("en")};var pages by remember {mutableStateOf(emptyList<Pair<String,String>>())}
    var output by remember {mutableStateOf("")};var busy by remember {mutableStateOf(false)}
    val prefix="/api/v2/ecosystem"
    suspend fun operation(path:String,method:String="GET",data:JSONObject?=null,bearer:String=token):JSONObject=withContext(Dispatchers.IO) {
        require(path.startsWith("$prefix/"))
        val uri=java.net.URI(base)
        require(uri.scheme in listOf("http","https") && !uri.host.isNullOrBlank() && uri.userInfo==null && uri.rawQuery==null && uri.fragment==null) {"Use an HTTP(S) backend URL without credentials/query"}
        val body=if(method=="GET") null else RequestBody.create(MediaType.parse("application/json"),data?.toString()?:"{}")
        val request=Request.Builder().url(base+path).method(method,body).apply {if(bearer.isNotEmpty())header("Authorization","Bearer $bearer")}.build()
        client.newCall(request).execute().use {r->
            val text=r.body()?.string().orEmpty()
            if(!r.isSuccessful)error("HTTP ${r.code()}: "+runCatching {JSONObject(text).optString("detail")}.getOrDefault("Request failed"))
            if(text.startsWith("["))JSONObject().put("items",org.json.JSONArray(text)) else if(text.isBlank())JSONObject() else JSONObject(text)
        }
    }
    fun run(block:suspend ()->Unit) {if(!busy)scope.launch {busy=true;try{block()}catch(e:Exception){if(e is kotlinx.coroutines.CancellationException)throw e;output=e.message?:"Request failed"}finally{busy=false}}}
    Dialog(onDismissRequest=onClose,properties=DialogProperties(usePlatformDefaultWidth=false)) {
        Surface(Modifier.fillMaxSize(),color=MaterialTheme.colorScheme.background) {
            Column(Modifier.fillMaxSize().padding(20.dp).verticalScroll(rememberScrollState()),verticalArrangement=Arrangement.spacedBy(10.dp)) {
                Text("AI Car Scanner • "+(fixedWorkspace?:"Account workspace"),style=MaterialTheme.typography.titleLarge)
                Text("Account workspace • ecosystem backend required")
                TextButton(onClick=onClose){Text("Close")}
                if(token.isEmpty()) {
                    OutlinedTextField(base,{base=it},enabled=!busy,label={Text("Backend URL")},modifier=Modifier.fillMaxWidth())
                    OutlinedTextField(fullName,{fullName=it},label={Text("Full name")},modifier=Modifier.fillMaxWidth())
                    OutlinedTextField(email,{email=it},label={Text("Email")},modifier=Modifier.fillMaxWidth())
                    OutlinedTextField(password,{password=it},label={Text("Password")},visualTransformation=PasswordVisualTransformation(),modifier=Modifier.fillMaxWidth())
                    OutlinedButton(enabled=!busy,onClick={val secret=password;password="";run {output=operation("$prefix/accounts","POST",JSONObject().put("email",email).put("password",secret).put("full_name",fullName),"").toString(2)}}){Text("Create account")}
                    Button(enabled=!busy,onClick={val secret=password;password="";run {
                        val auth=operation("$prefix/auth/login","POST",JSONObject().put("email",email).put("password",secret),"")
                        context.getSharedPreferences("backend",0).edit().putString("url",base.trimEnd('/')).apply()
                        token=auth.getString("access_token");val me=operation("$prefix/me")
                        val authorized=listOf("modes","portals").flatMap {key->val a=me.getJSONArray(key);(0 until a.length()).map {a.getString(it)}}
                        modes=if(fixedWorkspace==null) authorized else authorized.filter {it==fixedWorkspace}
                        onboarding=fixedWorkspace in listOf("CUSTOMER","MARKET") && modes.isEmpty()
                        output=me.toString(2)
                    }}){Text("Sign in")}
                } else {
                    Row(horizontalArrangement=Arrangement.spacedBy(6.dp)){listOf("en","hy","ru","fr").forEach {code->TextButton(onClick={language=code}){Text(code)}}}
                    if(onboarding) {
                        OutlinedTextField(businessName,{businessName=it},label={Text("Business name")},modifier=Modifier.fillMaxWidth())
                        OutlinedTextField(address,{address=it},label={Text("Business address")},modifier=Modifier.fillMaxWidth())
                        Button(enabled=!busy,onClick={run {
                            operation(prefix+(if(fixedWorkspace=="CUSTOMER") "/service-centers" else "/merchants"),"POST",JSONObject().put("name",businessName).put("address",address))
                            modes=listOf(fixedWorkspace!!);onboarding=false
                        }}){Text(if(fixedWorkspace=="CUSTOMER") "Register workshop" else "Register shop")}
                    }
                    modes.forEach {mode->OutlinedButton(enabled=!busy,onClick={run {
                        val nav=operation("$prefix/navigation?workspace=$mode&language=$language").getJSONArray("pages")
                        pages=(0 until nav.length()).map {nav.getJSONObject(it).let {p->p.getString("label") to p.getString("path")}}
                    }}){Text(mode)}}
                    pages.forEach {(label,path)->Button(enabled=!busy,onClick={run {output=operation(path).toString(2)}}){Text(label)}}
                    TextButton(enabled=!busy,onClick={run {try {operation("$prefix/auth/logout","POST")}finally{token="";modes=emptyList();pages=emptyList();output=""}}}){Text("Sign out")}
                }
                if(busy)LinearProgressIndicator(Modifier.fillMaxWidth())
                Text(output,style=MaterialTheme.typography.bodySmall)
            }
        }
    }
}
