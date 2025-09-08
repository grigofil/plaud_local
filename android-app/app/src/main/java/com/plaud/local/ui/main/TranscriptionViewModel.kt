package com.plaud.local.ui.main

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.plaud.local.domain.model.FileUploadState
import com.plaud.local.domain.model.TranscriptionJob
import com.plaud.local.domain.model.TranscriptionResult
import com.plaud.local.domain.model.TranscriptionStatus
import com.plaud.local.domain.usecase.DeleteTranscriptionJobUseCase
import com.plaud.local.domain.usecase.GetTranscriptionHistoryUseCase
import com.plaud.local.domain.usecase.GetTranscriptionResultUseCase
import com.plaud.local.domain.usecase.GetJobStatusUseCase
import com.plaud.local.domain.usecase.SaveTranscriptionResultUseCase
import com.plaud.local.domain.usecase.UploadAudioUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.File
import javax.inject.Inject

@HiltViewModel
class TranscriptionViewModel @Inject constructor(
    private val uploadAudioUseCase: UploadAudioUseCase,
    private val getJobStatusUseCase: GetJobStatusUseCase,
    private val getTranscriptionResultUseCase: GetTranscriptionResultUseCase,
    private val saveTranscriptionResultUseCase: SaveTranscriptionResultUseCase,
    private val getTranscriptionHistoryUseCase: GetTranscriptionHistoryUseCase,
    private val deleteTranscriptionJobUseCase: DeleteTranscriptionJobUseCase
) : ViewModel() {

    private val _uploadState = MutableStateFlow<FileUploadState>(FileUploadState.Idle)
    val uploadState: StateFlow<FileUploadState> = _uploadState.asStateFlow()

    private val _currentJob = MutableStateFlow<TranscriptionJob?>(null)
    val currentJob: StateFlow<TranscriptionJob?> = _currentJob.asStateFlow()

    private val _transcriptionResult = MutableStateFlow<TranscriptionResult?>(null)
    val transcriptionResult: StateFlow<TranscriptionResult?> = _transcriptionResult.asStateFlow()

    private val _transcriptionHistory = MutableStateFlow<List<TranscriptionJob>>(emptyList())
    val transcriptionHistory: StateFlow<List<TranscriptionJob>> = _transcriptionHistory.asStateFlow()

    private var statusCheckJob: Job? = null

    init {
        loadTranscriptionHistory()
    }

    fun selectFile(fileName: String, fileSize: Long) {
        _uploadState.value = FileUploadState.Selected(fileName, fileSize)
    }

    fun uploadFile(file: File, serverUrl: String, token: String, language: String = "ru") {
        _uploadState.value = FileUploadState.Uploading(0)

        viewModelScope.launch {
            val result = uploadAudioUseCase(file, serverUrl, token, language)
            result.onSuccess { jobId ->
                _uploadState.value = FileUploadState.Uploaded(jobId)
                _currentJob.value = TranscriptionJob(
                    jobId = jobId,
                    status = TranscriptionStatus.UPLOADING,
                    fileName = file.name,
                    fileSize = file.length()
                )
                startStatusChecking(jobId, serverUrl, token)
            }.onFailure { exception ->
                _uploadState.value = FileUploadState.Error(exception.message ?: "Upload failed")
            }
        }
    }

    private fun startStatusChecking(jobId: String, serverUrl: String, token: String) {
        statusCheckJob?.cancel()
        statusCheckJob = viewModelScope.launch {
            while (true) {
                delay(5000) // Check every 5 seconds

                val result = getJobStatusUseCase(jobId, serverUrl, token)
                result.onSuccess { job ->
                    _currentJob.value = job

                    when (job.status) {
                        TranscriptionStatus.DONE -> {
                            fetchResults(jobId, serverUrl, token)
                            break
                        }
                        TranscriptionStatus.ERROR -> {
                            _uploadState.value = FileUploadState.Error(
                                job.errorMessage ?: "Processing error"
                            )
                            break
                        }
                        else -> {
                            // Continue checking
                        }
                    }
                }.onFailure {
                    _uploadState.value = FileUploadState.Error("Status check failed")
                    break
                }
            }
        }
    }

    private fun fetchResults(jobId: String, serverUrl: String, token: String) {
        viewModelScope.launch {
            val result = getTranscriptionResultUseCase(jobId, serverUrl, token)
            result.onSuccess { transcriptionResult ->
                _transcriptionResult.value = transcriptionResult
                saveTranscriptionResultUseCase(transcriptionResult)
                loadTranscriptionHistory()
            }.onFailure {
                _uploadState.value = FileUploadState.Error("Failed to fetch results")
            }
        }
    }

    fun loadTranscriptionHistory() {
        viewModelScope.launch {
            _transcriptionHistory.value = getTranscriptionHistoryUseCase()
        }
    }

    fun deleteJob(jobId: String) {
        viewModelScope.launch {
            deleteTranscriptionJobUseCase(jobId)
            loadTranscriptionHistory()
        }
    }

    fun resetState() {
        _uploadState.value = FileUploadState.Idle
        _currentJob.value = null
        _transcriptionResult.value = null
        statusCheckJob?.cancel()
    }

    override fun onCleared() {
        super.onCleared()
        statusCheckJob?.cancel()
    }
}