package com.aicarscaner.mobile.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.aicarscaner.mobile.data.api.DiagnosticSessionDto
import com.aicarscaner.mobile.data.api.VehicleCatalogEntryDto
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
    val history: List<DiagnosticSessionDto> = emptyList(),
    val vehicleCatalog: List<VehicleCatalogEntryDto> = emptyList(),
    val loading: Boolean = false,
    val error: String? = null
)

class DiagnosticViewModel(private val repository: DiagnosticRepository) : ViewModel() {
    private val _uiState = MutableStateFlow(DiagnosticUiState())
    val uiState: StateFlow<DiagnosticUiState> = _uiState.asStateFlow()

    fun openSession(id: String, language: String = "en") = execute { repository.getSession(id, language) }

    fun loadHistory() {
        viewModelScope.launch {
            try { _uiState.value = _uiState.value.copy(history = repository.listSessions(), error = null) }
            catch (cancelled: CancellationException) { throw cancelled }
            catch (error: Exception) { _uiState.value = _uiState.value.copy(error = error.message) }
        }
    }

    fun loadVehicleCatalog() {
        viewModelScope.launch {
            runCatching { repository.vehicleCatalog() }
                .onSuccess { catalog ->
                    _uiState.value = _uiState.value.copy(vehicleCatalog = catalog, error = null)
                }
                .onFailure {
                    // The screen keeps its local safety catalog as a fallback.
                    // Catalog transport failures must not block session creation.
                }
        }
    }

    fun createSession(vehicle: VehicleDto) = execute { repository.createSession(vehicle) }

    fun clearSession() {
        val catalog = _uiState.value.vehicleCatalog
        _uiState.value = DiagnosticUiState(vehicleCatalog = catalog)
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

    fun updateDtc(dtcId: String, code: String) = execute {
        val id = _uiState.value.session?.session_id ?: error("Create a session first")
        repository.updateDtc(id, dtcId, code)
    }

    fun deleteDtc(dtcId: String) = execute {
        val id = _uiState.value.session?.session_id ?: error("Create a session first")
        repository.deleteDtc(id, dtcId)
    }

    fun analyze(language: String = "en") = execute {
        val id = _uiState.value.session?.session_id ?: error("Create a session first")
        repository.analyze(id, language)
    }

    fun recordTestResult(
        testId: String,
        result: String,
        notes: String?,
        language: String = "en"
    ) = execute {
        val id = _uiState.value.session?.session_id ?: error("Create a session first")
        repository.recordTestResult(id, testId, result, notes, language)
    }

    private fun execute(block: suspend () -> DiagnosticSessionDto) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(loading = true, error = null)
            try {
                val result = block()
                _uiState.value = DiagnosticUiState(
                    session = result,
                    vehicleCatalog = _uiState.value.vehicleCatalog,
                    loading = false
                )
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
