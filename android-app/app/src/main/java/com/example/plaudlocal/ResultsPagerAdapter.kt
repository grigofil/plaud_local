package com.example.plaudlocal

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

class ResultsPagerAdapter(
    private val activity: ResultsActivity,
    private val formattedResult: FormattedResult
) : RecyclerView.Adapter<ResultsPagerAdapter.ResultViewHolder>() {

    class ResultViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val textView: TextView = itemView.findViewById(R.id.resultTextView)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ResultViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.fragment_result_tab, parent, false)
        return ResultViewHolder(view)
    }

    override fun onBindViewHolder(holder: ResultViewHolder, position: Int) {
        val text = when (position) {
            0 -> formattedResult.transcriptText
            1 -> formattedResult.summaryText
            2 -> formattedResult.keyPointsText
            3 -> formattedResult.actionItemsText
            4 -> formattedResult.risksText
            5 -> formattedResult.segmentsText
            6 -> buildAdditionalInfo()
            else -> "Неизвестный раздел"
        }
        
        holder.textView.text = text
    }

    override fun getItemCount(): Int = 7

    private fun buildAdditionalInfo(): String {
        val sb = StringBuilder()
        
        if (formattedResult.meetingSummaryText != "Саммари встречи недоступно") {
            sb.append("=== САММАРИ ВСТРЕЧИ ===\n")
            sb.append(formattedResult.meetingSummaryText)
            sb.append("\n\n")
        }
        
        if (formattedResult.rawSummaryText != "Сырое саммари недоступно") {
            sb.append("=== СЫРОЕ САММАРИ ===\n")
            sb.append(formattedResult.rawSummaryText)
            sb.append("\n\n")
        }
        
        if (formattedResult.fullText != "Полный текст недоступен") {
            sb.append("=== ПОЛНЫЙ ТЕКСТ ===\n")
            sb.append(formattedResult.fullText)
        }
        
        return if (sb.isNotEmpty()) sb.toString() else "Дополнительная информация недоступна"
    }
}