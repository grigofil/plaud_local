package com.example.plaudlocal

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.button.MaterialButton
import java.text.SimpleDateFormat
import java.util.*

class HistoryAdapter(
    private val historyList: List<HistoryItem>,
    private val onItemClick: (HistoryItem) -> Unit
) : RecyclerView.Adapter<HistoryAdapter.HistoryViewHolder>() {

    class HistoryViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val filenameTextView: TextView = itemView.findViewById(R.id.filenameTextView)
        val statusTextView: TextView = itemView.findViewById(R.id.statusTextView)
        val jobIdTextView: TextView = itemView.findViewById(R.id.jobIdTextView)
        val createdAtTextView: TextView = itemView.findViewById(R.id.createdAtTextView)
        val transcriptStatusTextView: TextView = itemView.findViewById(R.id.transcriptStatusTextView)
        val summaryStatusTextView: TextView = itemView.findViewById(R.id.summaryStatusTextView)
        val viewDetailsButton: MaterialButton = itemView.findViewById(R.id.viewDetailsButton)
        val downloadButton: MaterialButton = itemView.findViewById(R.id.downloadButton)
        val deleteButton: MaterialButton = itemView.findViewById(R.id.deleteButton)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): HistoryViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_history, parent, false)
        return HistoryViewHolder(view)
    }

    override fun onBindViewHolder(holder: HistoryViewHolder, position: Int) {
        val item = historyList[position]
        
        holder.filenameTextView.text = item.filename
        holder.jobIdTextView.text = "Job ID: ${item.jobId}"
        
        // Format created date
        val dateFormat = SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault())
        holder.createdAtTextView.text = "Created: ${dateFormat.format(Date(item.createdAt * 1000))}"
        
        // Set status
        holder.statusTextView.text = when (item.status) {
            "done" -> "Done"
            "processing" -> "Processing"
            "transcribed_waiting_summary" -> "Transcribing"
            "error" -> "Error"
            else -> "Unknown"
        }
        
        // Set transcript and summary status
        holder.transcriptStatusTextView.text = if (item.hasTranscript) "Transcript: Available" else "Transcript: Not available"
        holder.transcriptStatusTextView.setTextColor(
            if (item.hasTranscript) 
                holder.itemView.context.getColor(R.color.success_color)
            else 
                holder.itemView.context.getColor(R.color.text_secondary)
        )
        
        holder.summaryStatusTextView.text = if (item.hasSummary) "Summary: Available" else "Summary: Not available"
        holder.summaryStatusTextView.setTextColor(
            if (item.hasSummary) 
                holder.itemView.context.getColor(R.color.success_color)
            else 
                holder.itemView.context.getColor(R.color.text_secondary)
        )
        
        // Set click listeners
        holder.viewDetailsButton.setOnClickListener {
            onItemClick(item)
        }
        
        holder.downloadButton.setOnClickListener {
            // TODO: Implement download
        }
        
        holder.deleteButton.setOnClickListener {
            // TODO: Implement delete
        }
    }

    override fun getItemCount(): Int = historyList.size
}
