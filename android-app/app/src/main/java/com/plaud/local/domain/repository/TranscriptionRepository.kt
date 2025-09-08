package com.plaud.local.domain.repository

import com.plaud.local.domain.model.TranscriptionJob
import com.plaud.local.domain.model.TranscriptionResult
import java.io.File

/**
 * Репозиторий для работы с транскрипцией аудио
 */
interface TranscriptionRepository {
    /**
     * Загрузка аудиофайла на сервер
     */
    suspend fun uploadAudioFile(
        file: File,
        serverUrl: String,
        token: String,
        language: String = "ru"
    ): Result<String> // возвращает jobId

    /**
     * Проверка статуса задачи транскрипции
     */
    suspend fun getJobStatus(
        jobId: String,
        serverUrl: String,
        token: String
    ): Result<TranscriptionJob>

    /**
     * Получение результатов транскрипции
     */
    suspend fun getTranscriptionResult(
        jobId: String,
        serverUrl: String,
        token: String
    ): Result<TranscriptionResult>

    /**
     * Сохранение результатов транскрипции локально
     */
    suspend fun saveTranscriptionResult(result: TranscriptionResult)

    /**
     * Получение истории задач транскрипции
     */
    suspend fun getTranscriptionHistory(): List<TranscriptionJob>

    /**
     * Удаление задачи из истории
     */
    suspend fun deleteTranscriptionJob(jobId: String)
}