package com.aicarscaner.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.lifecycle.viewmodel.compose.viewModel
import com.aicarscaner.mobile.data.api.ApiClient
import com.aicarscaner.mobile.data.repository.DiagnosticRepository
import com.aicarscaner.mobile.presentation.DiagnosticScreen
import com.aicarscaner.mobile.presentation.DiagnosticViewModel
import com.aicarscaner.mobile.presentation.DiagnosticViewModelFactory

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        ApiClient.loadURL(applicationContext)
        val repository = DiagnosticRepository(ApiClient.diagnosticApi, applicationContext)

        setContent {
            val diagnosticViewModel: DiagnosticViewModel = viewModel(
                factory = DiagnosticViewModelFactory(repository)
            )
            DiagnosticScreen(diagnosticViewModel)
        }
    }
}
