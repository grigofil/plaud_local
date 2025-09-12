package com.example.plaudlocal

data class HistoryItem(
    val jobId: String,
    val filename: String,
    val status: String,
    val createdAt: Long,
    val hasTranscript: Boolean,
    val hasSummary: Boolean,
    val language: String? = null
)
