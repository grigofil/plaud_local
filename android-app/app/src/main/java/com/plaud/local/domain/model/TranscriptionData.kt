package com.plaud.local.domain.model

/**
 * Модель данных для задачи транскрипции
 */
data class TranscriptionJob(
    val jobId: String,
    val status: TranscriptionStatus,
    val fileName: String? = null,
    val fileSize: Long? = null,
    val createdAt: Long = System.currentTimeMillis(),
    val completedAt: Long? = null,
    val errorMessage: String? = null
)

/**
 * Статус обработки транскрипции
 */
enum class TranscriptionStatus {
    UPLOADING,
    PROCESSING,
    TRANSCRIBED_WAITING_SUMMARY,
    DONE,
    ERROR
}

/**
 * Модель результатов транскрипции
 */
data class TranscriptionResult(
    val jobId: String,
    val transcript: Transcript? = null,
    val summary: Summary? = null,
    val status: TranscriptionStatus
)

/**
 * Модель транскрипции
 */
data class Transcript(
    val text: String,
    val segments: List<TranscriptSegment>? = null,
    val language: String? = null,
    val duration: Long? = null
)

/**
 * Сегмент транскрипции
 */
data class TranscriptSegment(
    val start: Long,
    val end: Long,
    val text: String,
    val speaker: String? = null
)

/**
 * Модель саммари
 */
data class Summary(
    val text: String,
    val keyPoints: List<String>? = null,
    val duration: Long? = null
)

/**
 * Состояние загрузки файла
 */
sealed class FileUploadState {
    object Idle : FileUploadState()
    object Selecting : FileUploadState()
    data class Selected(val fileName: String, val fileSize: Long) : FileUploadState()
    data class Uploading(val progress: Int) : FileUploadState()
    data class Uploaded(val jobId: String) : FileUploadState()
    data class Error(val message: String) : FileUploadState()
}