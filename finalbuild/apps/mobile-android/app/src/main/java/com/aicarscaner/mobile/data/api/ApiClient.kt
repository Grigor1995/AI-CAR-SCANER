package com.aicarscaner.mobile.data.api

import okhttp3.OkHttpClient
import java.util.concurrent.TimeUnit
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object ApiClient {
    var BASE_URL = com.aicarscaner.mobile.BuildConfig.API_BASE_URL.trimEnd('/') + "/"

    fun loadURL(context:android.content.Context) {
        val saved=context.getSharedPreferences("backend",0).getString("url",null)
        if(saved!=null) BASE_URL=saved.trimEnd('/')+"/"
    }
    @Volatile private var cached: DiagnosticApi? = null
    fun changeURL(url:String) { BASE_URL=url.trimEnd('/')+"/";cached=null }
    val diagnosticApi: DiagnosticApi
        get() = cached ?: synchronized(this) { cached ?: buildApi().also {cached=it} }
    private fun buildApi():DiagnosticApi {
        val httpClient = OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(300, TimeUnit.SECONDS)
            .writeTimeout(15, TimeUnit.SECONDS)
            .build()

        return Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(httpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(DiagnosticApi::class.java)
    }
}
