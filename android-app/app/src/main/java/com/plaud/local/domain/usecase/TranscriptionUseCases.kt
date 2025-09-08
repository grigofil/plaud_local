package com.plaud.local.domain.usecase

import com.plaud.local.domain.model.TranscriptionJob
import com.plaud.local.domain.model.TranscriptionResult
import com.plaud.local.domain.repository.TranscriptionRepository
import java.io.File
import javax.inject.Inject

/**
 * Use case для загрузки аудиофайла
 */
class UploadAudioUseCase @Inject constructor(
    private val transcriptionRepository: TranscriptionRepository
) {
    suspend operator fun invoke(
        file: File,
        serverUrl: String,
        token: String,
        language: String = "ru"
    ): Result<String> {
        return transcriptionRepository.uploadAudioFile(file, serverUrl, token, language)
    }
}

/**
 * Use case для проверки статуса задачи
 */
class GetJobStatusUseCase @Inject constructor(
    private val transcriptionRepository: TranscriptionRepository
) {
    suspend operator fun invoke(
        jobId: String,
        serverUrl: String,
        token: String
    ): Result<TranscriptionJob> {
        return transcriptionRepository.getJobStatus(jobId, serverUrl, token)
    }
}

/**
 * Use case для получения результатов транскрипции
 */
class GetTranscriptionResultUseCase @Inject constructor(
    private val transcriptionRepository: TranscriptionRepository
) {
    suspend operator fun invoke(
        jobId: String,
        serverUrl: String,
        token: String
    ): Result<TranscriptionResult> {
        return transcriptionRepository.getTranscriptionResult(jobId, serverUrl, token)
    }
}

/**
 * Use case для сохранения результатов локально
 */
class SaveTranscriptionResultUseCase @Inject constructor(
    private val transcriptionRepository: TranscriptionRepository
) {
    suspend operator fun invoke(result: TranscriptionResult) {
        transcriptionRepository.saveTranscriptionResult(result)
    }
}

/**
 * Use case для получения истории транскрипций
 */
class GetTranscriptionHistoryUseCase @Inject constructor(
    private val transcriptionRepository: TranscriptionRepository
) {
    suspend operator fun invoke(): List<TranscriptionJob> {
        return transcriptionRepository.getTranscriptionHistory()
    }
}

/**
 * Use case для удаления задачи из истории
 */
class DeleteTranscriptionJobUseCase @Inject constructor(
    private val transcriptionRepository: TranscriptionRepository
) {
    suspend operator fun invoke(jobId: String) {
        transcriptionRepository.deleteTranscriptionJob(jobId)
    }
}