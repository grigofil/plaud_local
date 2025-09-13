package com.example.plaudlocal

import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.*

class ResultParser {
    
    fun parseResults(jsonString: String): ResultData? {
        return try {
            val json = JSONObject(jsonString)
            val transcript = json.optJSONObject("transcript")
            val summary = json.optJSONObject("summary")
            
            ResultData(
                transcript = parseTranscript(transcript),
                summary = parseSummary(summary),
                keyPoints = parseKeyPoints(summary),
                actionItems = parseActionItems(summary),
                risks = parseRisks(summary),
                meetingSummary = parseMeetingSummary(summary),
                rawSummary = parseRawSummary(summary),
                segments = parseSegments(transcript),
                fullText = parseFullText(transcript),
                owner = parseOwner(summary),
                task = parseTask(summary),
                dueDate = parseDueDate(summary)
            )
        } catch (e: Exception) {
            android.util.Log.e("ResultParser", "Error parsing results: ${e.message}", e)
            null
        }
    }
    
    private fun parseTranscript(transcript: JSONObject?): String? {
        return transcript?.optString("text") ?: transcript?.optString("transcript")
    }
    
    private fun parseSummary(summary: JSONObject?): String? {
        return summary?.optString("summary") ?: summary?.optString("text")
    }
    
    private fun parseKeyPoints(summary: JSONObject?): List<String>? {
        val keyPoints = summary?.optJSONArray("key_points")
        return if (keyPoints != null) {
            val points = mutableListOf<String>()
            for (i in 0 until keyPoints.length()) {
                points.add(keyPoints.getString(i))
            }
            points
        } else null
    }
    
    private fun parseActionItems(summary: JSONObject?): List<String>? {
        val actionItems = summary?.optJSONArray("action_items")
        return if (actionItems != null) {
            val items = mutableListOf<String>()
            for (i in 0 until actionItems.length()) {
                items.add(actionItems.getString(i))
            }
            items
        } else null
    }
    
    private fun parseRisks(summary: JSONObject?): List<String>? {
        val risks = summary?.optJSONArray("risks")
        return if (risks != null) {
            val riskList = mutableListOf<String>()
            for (i in 0 until risks.length()) {
                riskList.add(risks.getString(i))
            }
            riskList
        } else null
    }
    
    private fun parseMeetingSummary(summary: JSONObject?): String? {
        return summary?.optString("meeting_summary")
    }
    
    private fun parseRawSummary(summary: JSONObject?): String? {
        return summary?.optString("raw_summary")
    }
    
    private fun parseSegments(transcript: JSONObject?): List<TranscriptSegment>? {
        val segments = transcript?.optJSONArray("segments")
        return if (segments != null) {
            val segmentList = mutableListOf<TranscriptSegment>()
            for (i in 0 until segments.length()) {
                val segment = segments.getJSONObject(i)
                segmentList.add(
                    TranscriptSegment(
                        start = segment.optDouble("start", 0.0),
                        end = segment.optDouble("end", 0.0),
                        text = segment.optString("text", ""),
                        speaker = segment.optString("speaker", null)
                    )
                )
            }
            segmentList
        } else null
    }
    
    private fun parseFullText(transcript: JSONObject?): String? {
        return transcript?.optString("full_text") ?: transcript?.optString("text")
    }
    
    private fun parseOwner(summary: JSONObject?): String? {
        return summary?.optString("owner")
    }
    
    private fun parseTask(summary: JSONObject?): String? {
        return summary?.optString("task")
    }
    
    private fun parseDueDate(summary: JSONObject?): String? {
        return summary?.optString("due_date")
    }
    
    fun formatResults(resultData: ResultData): FormattedResult {
        return FormattedResult(
            transcriptText = formatTranscript(resultData),
            summaryText = formatSummary(resultData),
            keyPointsText = formatKeyPoints(resultData),
            actionItemsText = formatActionItems(resultData),
            risksText = formatRisks(resultData),
            meetingSummaryText = formatMeetingSummary(resultData),
            rawSummaryText = formatRawSummary(resultData),
            segmentsText = formatSegments(resultData),
            fullText = formatFullText(resultData)
        )
    }
    
    private fun formatTranscript(resultData: ResultData): String {
        return resultData.transcript ?: "Транскрипт недоступен"
    }
    
    private fun formatSummary(resultData: ResultData): String {
        return resultData.summary ?: "Саммари недоступно"
    }
    
    private fun formatKeyPoints(resultData: ResultData): String {
        return if (!resultData.keyPoints.isNullOrEmpty()) {
            val sb = StringBuilder()
            resultData.keyPoints.forEachIndexed { index, point ->
                sb.append("${index + 1}. $point\n")
            }
            sb.toString().trim()
        } else {
            "Ключевые моменты недоступны"
        }
    }
    
    private fun formatActionItems(resultData: ResultData): String {
        return if (!resultData.actionItems.isNullOrEmpty()) {
            val sb = StringBuilder()
            resultData.actionItems.forEachIndexed { index, item ->
                sb.append("${index + 1}. $item\n")
            }
            sb.toString().trim()
        } else {
            "Задачи недоступны"
        }
    }
    
    private fun formatRisks(resultData: ResultData): String {
        return if (!resultData.risks.isNullOrEmpty()) {
            val sb = StringBuilder()
            resultData.risks.forEachIndexed { index, risk ->
                sb.append("${index + 1}. $risk\n")
            }
            sb.toString().trim()
        } else {
            "Риски не определены"
        }
    }
    
    private fun formatMeetingSummary(resultData: ResultData): String {
        return resultData.meetingSummary ?: "Саммари встречи недоступно"
    }
    
    private fun formatRawSummary(resultData: ResultData): String {
        return resultData.rawSummary ?: "Сырое саммари недоступно"
    }
    
    private fun formatSegments(resultData: ResultData): String {
        return if (!resultData.segments.isNullOrEmpty()) {
            val sb = StringBuilder()
            resultData.segments.forEach { segment ->
                val time = formatTime(segment.start)
                val speaker = if (!segment.speaker.isNullOrEmpty()) "[${segment.speaker}] " else ""
                sb.append("$time $speaker${segment.text}\n\n")
            }
            sb.toString().trim()
        } else {
            "Сегменты недоступны"
        }
    }
    
    private fun formatFullText(resultData: ResultData): String {
        return resultData.fullText ?: "Полный текст недоступен"
    }
    
    private fun formatTime(seconds: Double): String {
        val minutes = (seconds / 60).toInt()
        val remainingSeconds = (seconds % 60).toInt()
        return String.format("%02d:%02d", minutes, remainingSeconds)
    }
    
    fun getCopyableText(formattedResult: FormattedResult): String {
        val sb = StringBuilder()
        sb.append("=== ТРАНСКРИПТ ===\n")
        sb.append(formattedResult.transcriptText)
        sb.append("\n\n=== САММАРИ ===\n")
        sb.append(formattedResult.summaryText)
        
        if (formattedResult.keyPointsText != "Ключевые моменты недоступны") {
            sb.append("\n\n=== КЛЮЧЕВЫЕ МОМЕНТЫ ===\n")
            sb.append(formattedResult.keyPointsText)
        }
        
        if (formattedResult.actionItemsText != "Задачи недоступны") {
            sb.append("\n\n=== ЗАДАЧИ ===\n")
            sb.append(formattedResult.actionItemsText)
        }
        
        if (formattedResult.risksText != "Риски не определены") {
            sb.append("\n\n=== РИСКИ ===\n")
            sb.append(formattedResult.risksText)
        }
        
        if (formattedResult.meetingSummaryText != "Саммари встречи недоступно") {
            sb.append("\n\n=== САММАРИ ВСТРЕЧИ ===\n")
            sb.append(formattedResult.meetingSummaryText)
        }
        
        return sb.toString()
    }
}
