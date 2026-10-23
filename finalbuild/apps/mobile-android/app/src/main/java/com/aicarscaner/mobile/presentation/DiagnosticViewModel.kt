package com.aicarscaner.mobile.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.aicarscaner.mobile.data.mergeVehicleCatalog
import com.aicarscaner.mobile.data.api.DiagnosticSessionDto
import com.aicarscaner.mobile.data.api.VehicleCatalogEntryDto
import com.aicarscaner.mobile.data.api.VehicleDto
import com.aicarscaner.mobile.data.api.BackendLiveRecordDto
import com.aicarscaner.mobile.data.repository.DiagnosticRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.Job
import kotlinx.coroutines.CancellationException
import retrofit2.HttpException

data class DiagnosticUiState(
    val session: DiagnosticSessionDto? = null,
    val history: List<DiagnosticSessionDto> = emptyList(),
    val backendLiveRecords: List<BackendLiveRecordDto> = emptyList(),
    val backendLiveLoading: Boolean = false,
    val backendLiveError: String? = null,
    val vehicleCatalog: List<VehicleCatalogEntryDto> = emptyList(),
    val catalogOnline: Boolean = false,
    val loading: Boolean = false,
    val error: String? = null,
    val testResultSaving: Boolean = false,
    val testResultError: String? = null,
    val testResultRevision: Int = 0,
    val testResultCompletion: Int = 0
)

class DiagnosticViewModel(private val repository: DiagnosticRepository) : ViewModel() {
    private val offlineCatalog = repository.offlineVehicleCatalog()
    private val _uiState = MutableStateFlow(DiagnosticUiState(vehicleCatalog = offlineCatalog))
    val uiState: StateFlow<DiagnosticUiState> = _uiState.asStateFlow()

    fun openSession(id: String, language: String = "en") = execute { repository.getSession(id, language) }

    private var liveRefreshJob: Job? = null
    private var liveRefreshSession: String? = null
    private var liveRefreshRevision = 0

    /** Reads persisted server samples; never labels them as the locally connected adapter. */
    fun refreshBackendLiveRecords() {
        val sessionId = _uiState.value.session?.session_id ?: return
        if (liveRefreshJob?.isActive == true && liveRefreshSession == sessionId) return
        val revision = ++liveRefreshRevision
        liveRefreshJob?.cancel()
        liveRefreshSession = sessionId
        liveRefreshJob = viewModelScope.launch {
            _uiState.value = _uiState.value.copy(backendLiveLoading = true, backendLiveError = null)
            try {
                val rows = repository.acquisitionRecords(sessionId).records
                if (revision == liveRefreshRevision && _uiState.value.session?.session_id == sessionId) {
                    _uiState.value = _uiState.value.copy(
                        backendLiveRecords = rows, backendLiveLoading = false
                    )
                }
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (error: Exception) {
                if (revision == liveRefreshRevision && _uiState.value.session?.session_id == sessionId) {
                    _uiState.value = _uiState.value.copy(
                        backendLiveLoading = false, backendLiveError = error.message
                    )
                }
            } finally {
                if (revision == liveRefreshRevision && _uiState.value.session?.session_id == sessionId && liveRefreshSession == sessionId) {
                    _uiState.value = _uiState.value.copy(backendLiveLoading = false)
                }
            }
        }
    }

    fun loadHistory() {
        viewModelScope.launch {
            try { _uiState.value = _uiState.value.copy(history = repository.listSessions(), error = null) }
            catch (cancelled: CancellationException) { throw cancelled }
            catch (error: Exception) { _uiState.value = _uiState.value.copy(error = error.message) }
        }
    }

    fun loadVehicleCatalog() {
        viewModelScope.launch {
            try {
                val catalog = repository.vehicleCatalog()
                _uiState.value = _uiState.value.copy(vehicleCatalog = mergeVehicleCatalog(catalog, offlineCatalog), catalogOnline = true)
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (_: Exception) {
                _uiState.value = _uiState.value.copy(catalogOnline = false)
            }
        }
    }


    fun createSession(vehicle: VehicleDto) = execute { repository.createSession(vehicle) }

    fun clearSession() {
        liveRefreshRevision++
        liveRefreshSession = null
        liveRefreshJob?.cancel()
        val catalog = _uiState.value.vehicleCatalog
        _uiState.value = DiagnosticUiState(vehicleCatalog = catalog, catalogOnline = _uiState.value.catalogOnline)
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
    ) {
        if (_uiState.value.testResultSaving) return
        // Set synchronously so two taps in one frame cannot submit twice.
        _uiState.value = _uiState.value.copy(testResultSaving = true, testResultError = null)
        execute(resultRecorded = true) {
            val id = _uiState.value.session?.session_id ?: error("Create a session first")
            kotlinx.coroutines.withTimeout(60_000) {
                repository.recordTestResult(id, testId, result, notes, language)
            }
        }
    }

    private fun execute(resultRecorded: Boolean = false, block: suspend () -> DiagnosticSessionDto) {
        val requestRevision = _uiState.value.testResultRevision
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(loading = true, error = null)
            try {
                val result = block()
                val previous = _uiState.value
                if (!resultRecorded && previous.session?.session_id == result.session_id &&
                    previous.testResultRevision != requestRevision) {
                    _uiState.value = previous.copy(loading = false)
                    return@launch
                }
                if (previous.session?.session_id != result.session_id) {
                    liveRefreshRevision++
                    liveRefreshSession = null
                    liveRefreshJob?.cancel()
                }
                val revision = if (previous.session?.session_id == result.session_id) previous.testResultRevision else 0
                // The result endpoint already recalculates the diagnostic session.
                // Publish that complete response without a second analysis overwriting it.
                _uiState.value = previous.copy(
                    session = result,
                    backendLiveRecords = if (previous.session?.session_id == result.session_id) previous.backendLiveRecords else emptyList(),
                    backendLiveLoading = if (previous.session?.session_id == result.session_id) previous.backendLiveLoading else false,
                    backendLiveError = if (previous.session?.session_id == result.session_id) previous.backendLiveError else null,
                    loading = false,
                    error = null,
                    testResultSaving = if (resultRecorded) false else previous.testResultSaving,
                    testResultError = if (resultRecorded) null else previous.testResultError,
                    testResultRevision = revision + if (resultRecorded) 1 else 0,
                    testResultCompletion = previous.testResultCompletion + if (resultRecorded) 1 else 0
                )
            } catch (timeout: kotlinx.coroutines.TimeoutCancellationException) {
                _uiState.value = _uiState.value.copy(
                    loading = false, error = "Request timed out. Check the backend connection and retry.",
                    testResultSaving = if (resultRecorded) false else _uiState.value.testResultSaving,
                    testResultError = if (resultRecorded) "Request timed out. Check the backend connection and retry." else _uiState.value.testResultError,
                    testResultCompletion = _uiState.value.testResultCompletion + if (resultRecorded) 1 else 0
                )
            } catch (cancelled: CancellationException) {
                if (resultRecorded) _uiState.value = _uiState.value.copy(loading = false, testResultSaving = false)
                throw cancelled
            } catch (error: Throwable) {
                val message = friendlyError(error)
                _uiState.value = _uiState.value.copy(
                    loading = false,
                    error = message,
                    testResultSaving = if (resultRecorded) false else _uiState.value.testResultSaving,
                    testResultError = if (resultRecorded) message else _uiState.value.testResultError,
                    testResultCompletion = _uiState.value.testResultCompletion + if (resultRecorded) 1 else 0
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
