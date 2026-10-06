package com.aicarscaner.mobile.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.aicarscaner.mobile.data.repository.DiagnosticRepository

class DiagnosticViewModelFactory(private val repository: DiagnosticRepository) : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        require(modelClass.isAssignableFrom(DiagnosticViewModel::class.java))
        return DiagnosticViewModel(repository) as T
    }
}
