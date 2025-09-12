package com.example.plaudlocal

data class ResultData(
    val transcript: String? = null,
    val summary: String? = null,
    val keyPoints: List<String>? = null,
    val actionItems: List<String>? = null,
    val risks: List<String>? = null,
    val meetingSummary: String? = null,
    val rawSummary: String? = null,
    val segments: List<TranscriptSegment>? = null,
    val fullText: String? = null,
    val owner: String? = null,
    val task: String? = null,
    val dueDate: String? = null
)

data class TranscriptSegment(
    val start: Double,
    val end: Double,
    val text: String,
    val speaker: String? = null
)

data class FormattedResult(
    val transcriptText: String,
    val summaryText: String,
    val keyPointsText: String,
    val actionItemsText: String,
    val risksText: String,
    val meetingSummaryText: String,
    val rawSummaryText: String,
    val segmentsText: String,
    val fullText: String
)
