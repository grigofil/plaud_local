package com.example.plaudlocal

import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import okhttp3.Call
import okhttp3.Callback
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit
import androidx.recyclerview.widget.RecyclerView

class HistoryFragment : Fragment() {
    
    private var _binding: FragmentHistoryBinding? = null
    private val binding get() = _binding!!
    
    private lateinit var historyAdapter: HistoryAdapter
    private val historyList = mutableListOf<HistoryItem>()
    private lateinit var sharedPreferences: SharedPreferences
    private lateinit var resultParser: ResultParser
    
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentHistoryBinding.inflate(inflater, container, false)
        return binding.getRoot()
    }
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        // Initialize components
        sharedPreferences = requireContext().getSharedPreferences("plaud_settings", Context.MODE_PRIVATE)
        resultParser = ResultParser()
        
        setupRecyclerView()
        setupClickListeners()
        loadHistory()
    }
    
    private fun setupRecyclerView() {
        historyAdapter = HistoryAdapter(historyList) { historyItem, action ->
            when (action) {
                "view_details" -> viewDetails(historyItem)
                "download" -> downloadJob(historyItem)
                "delete" -> deleteJob(historyItem)
            }
        }
        
        binding.historyRecyclerView.apply {
            layoutManager = LinearLayoutManager(requireContext())
            adapter = historyAdapter
        }
    }
    
    private fun setupClickListeners() {
        binding.loadHistoryButton.setOnClickListener {
            loadHistory()
        }
    }
    
    private fun loadHistory() {
        val apiUrl = sharedPreferences.getString("api_url", "") ?: ""
        val authToken = sharedPreferences.getString("auth_token", "") ?: ""
        
        if (apiUrl.isEmpty()) {
            Toast.makeText(requireContext(), "Please set API URL in settings", Toast.LENGTH_SHORT).show()
            return
        }
        
        if (authToken.isEmpty()) {
            Toast.makeText(requireContext(), "Please login first", Toast.LENGTH_SHORT).show()
            return
        }
        
        Toast.makeText(requireContext(), "Loading history...", Toast.LENGTH_SHORT).show()
        
        val request = Request.Builder()
            .url("$apiUrl/history")
            .addHeader("Authorization", "Bearer $authToken")
            .build()
        
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                requireActivity().runOnUiThread {
                    if (_binding == null) return@runOnUiThread
                    Toast.makeText(requireContext(), "Failed to load history: ${e.message}", Toast.LENGTH_SHORT).show()
                    updateHistoryUI()
                }
            }
            
            override fun onResponse(call: Call, response: Response) {
                requireActivity().runOnUiThread {
                    if (_binding == null) return@runOnUiThread
                    if (response.isSuccessful) {
                        try {
                            val json = JSONObject(response.body?.string() ?: "")
                            val jobsArray = json.getJSONArray("jobs")
                            
                            historyList.clear()
                            for (i in 0 until jobsArray.length()) {
                                val job = jobsArray.getJSONObject(i)
                                val historyItem = HistoryItem(
                                    jobId = job.getString("job_id"),
                                    filename = job.optString("filename", "Unknown"),
                                    status = job.getString("status"),
                                    createdAt = job.optLong("created_at", System.currentTimeMillis() / 1000),
                                    hasTranscript = job.optBoolean("has_transcript", false),
                                    hasSummary = job.optBoolean("has_summary", false),
                                    language = job.optString("language", null)
                                )
                                historyList.add(historyItem)
                            }
                            
                            historyAdapter.notifyDataSetChanged()
                            updateHistoryUI()
                            
                            Toast.makeText(requireContext(), "History loaded: ${historyList.size} items", Toast.LENGTH_SHORT).show()
                        } catch (e: Exception) {
                            Toast.makeText(requireContext(), "Failed to parse history: ${e.message}", Toast.LENGTH_SHORT).show()
                            updateHistoryUI()
                        }
                    } else {
                        Toast.makeText(requireContext(), "Failed to load history: ${response.code}", Toast.LENGTH_SHORT).show()
                        updateHistoryUI()
                    }
                }
            }
        })
    }
    
    private fun updateHistoryUI() {
        if (_binding == null) return
        if (historyList.isEmpty()) {
            binding.historyRecyclerView.visibility = View.GONE
            binding.noHistoryTextView.visibility = View.VISIBLE
        } else {
            binding.historyRecyclerView.visibility = View.VISIBLE
            binding.noHistoryTextView.visibility = View.GONE
        }
    }
    
    private fun viewDetails(historyItem: HistoryItem) {
        if (historyItem.status == "done" && (historyItem.hasTranscript || historyItem.hasSummary)) {
            fetchJobResults(historyItem.jobId)
        } else {
            Toast.makeText(requireContext(), "Results for this job are not ready yet", Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun fetchJobResults(jobId: String) {
        val apiUrl = sharedPreferences.getString("api_url", "") ?: ""
        val authToken = sharedPreferences.getString("auth_token", "") ?: ""
        
        Toast.makeText(requireContext(), "Loading results...", Toast.LENGTH_SHORT).show()
        
        val request = Request.Builder()
            .url("$apiUrl/result/$jobId")
            .addHeader("Authorization", "Bearer $authToken")
            .build()
        
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                requireActivity().runOnUiThread {
                    if (_binding == null) return@runOnUiThread
                    Toast.makeText(requireContext(), "Failed to load results: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
            
            override fun onResponse(call: Call, response: Response) {
                requireActivity().runOnUiThread {
                    if (_binding == null) return@runOnUiThread
                    if (response.isSuccessful) {
                        val responseBody = response.body?.string()
                        try {
                            val resultData = resultParser.parseResults(responseBody ?: "")
                            if (resultData != null) {
                                val formattedResult = resultParser.formatResults(resultData)
                                val intent = Intent(requireContext(), ResultsActivity::class.java).apply {
                                    putExtra("job_id", jobId)
                                    putExtra("formatted_result", formattedResult)
                                }
                                startActivity(intent)
                            } else {
                                Toast.makeText(requireContext(), "Failed to parse results", Toast.LENGTH_SHORT).show()
                            }
                        } catch (e: Exception) {
                            Toast.makeText(requireContext(), "Failed to parse results: ${e.message}", Toast.LENGTH_SHORT).show()
                        }
                    } else {
                        Toast.makeText(requireContext(), "Failed to load results: ${response.code}", Toast.LENGTH_SHORT).show()
                    }
                }
            }
        })
    }
    
    private fun downloadJob(historyItem: HistoryItem) {
        // TODO: Implement download job
        Toast.makeText(requireContext(), "Download ${historyItem.filename}", Toast.LENGTH_SHORT).show()
    }
    
    private fun deleteJob(historyItem: HistoryItem) {
        // TODO: Implement delete job
        Toast.makeText(requireContext(), "Delete ${historyItem.filename}", Toast.LENGTH_SHORT).show()
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
