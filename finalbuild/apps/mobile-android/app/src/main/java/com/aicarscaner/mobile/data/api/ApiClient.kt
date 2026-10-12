package com.aicarscaner.mobile.data.api

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object ApiClient {
    private const val BASE_URL = "https://ai-car-scaner.onrender.com/"

    val diagnosticApi: DiagnosticApi by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(DiagnosticApi::class.java)
    }
}
