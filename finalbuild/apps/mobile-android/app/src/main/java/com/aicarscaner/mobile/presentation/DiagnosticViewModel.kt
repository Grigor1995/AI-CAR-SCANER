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
import kotlinx.coroutines.CancellationException
import retrofit2.HttpException

data class DiagnosticUiState(
    val session: DiagnosticSessionDto? = null,
    val loading: Boolean = false,
    val error: String? = null
)

class DiagnosticViewModel(private val repository: DiagnosticRepository) : ViewModel() {
    private val _uiState = MutableStateFlow(DiagnosticUiState())
    val uiState: StateFlow<DiagnosticUiState> = _uiState.asStateFlow()

    fun createSession(vehicle: VehicleDto) = execute { repository.createSession(vehicle) }

    fun clearSession() {
        _uiState.value = DiagnosticUiState()
    }

    fun updateVehicle(vehicle: VehicleDto) = execute {
        val id = _uiState.value.session?.session_id ?: error("Create a session first")
        repository.updateVehicle(id, vehicle)
    }

    fun addSymptom(text: String) = execute {
        val id = _uiState.value.session?.session_id ?: error("Create a session first")
        repository.addSymptom(id, text)
    }

    fun updateSymptom(symptomId: String, text: String) = execute {
        val id = _uiState.value.session?.session_id ?: error("Create a session first")
        repository.updateSymptom(id, symptomId, text)
    }

    fun deleteSymptom(symptomId: String) = execute {
        val id = _uiState.value.session?.session_id ?: error("Create a session first")
        repository.deleteSymptom(id, symptomId)
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
            try {
                val result = block()
                _uiState.value = DiagnosticUiState(session = result, loading = false)
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (error: Throwable) {
                _uiState.value = _uiState.value.copy(
                    loading = false,
                    error = friendlyError(error)
                )
            }
        }
    }

    private fun friendlyError(error: Throwable): String {
        if (error is HttpException) {
            val body = runCatching { error.response()?.errorBody()?.string() }.getOrNull()
            return buildString {
                append("HTTP ${error.code()}")
                if (!body.isNullOrBlank()) {
                    append(": ")
                    append(body.take(500))
                }
            }
        }
        return error.message ?: "Request failed"
    }
}
