package com.aicarscaner.mobile.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.aicarscaner.mobile.data.api.DiagnosticSessionDto
import com.aicarscaner.mobile.data.api.VehicleDto
import com.aicarscaner.mobile.data.repository.DiagnosticRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class DiagnosticUiState(
    val session: DiagnosticSessionDto? = null,
    val loading: Boolean = false,
    val error: String? = null
)

class DiagnosticViewModel(private val repository: DiagnosticRepository) : ViewModel() {
    private val _uiState = MutableStateFlow(DiagnosticUiState())
    val uiState: StateFlow<DiagnosticUiState> = _uiState.asStateFlow()

    fun createSession(vehicle: VehicleDto) = execute { repository.createSession(vehicle) }
    fun addSymptom(text: String) = execute {
        val id = _uiState.value.session?.session_id ?: error("Create a session first")
        repository.addSymptom(id, text)
    }
    fun addDtc(code: String) = execute {
        val id = _uiState.value.session?.session_id ?: error("Create a session first")
        repository.addDtc(id, code)
    }
    fun analyze() = execute {
        val id = _uiState.value.session?.session_id ?: error("Create a session first")
        repository.analyze(id)
    }

    private fun execute(block: suspend () -> DiagnosticSessionDto) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(loading = true, error = null)
            runCatching { block() }
                .onSuccess { _uiState.value = DiagnosticUiState(session = it) }
                .onFailure {
                    _uiState.value = _uiState.value.copy(
                        loading = false,
                        error = it.message ?: "Request failed"
                    )
                }
        }
    }
}
