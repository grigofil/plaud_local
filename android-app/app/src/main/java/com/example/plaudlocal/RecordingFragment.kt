package com.example.plaudlocal

import android.Manifest
import android.app.AlertDialog
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.media.MediaRecorder
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import okhttp3.Call
import okhttp3.Callback
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody
import okhttp3.Response
import org.json.JSONObject
import java.io.File
import java.io.IOException
import java.text.SimpleDateFormat
import java.util.*
import java.util.concurrent.TimeUnit

class RecordingFragment : Fragment() {
    
    private var _binding: FragmentRecordingBinding? = null
    private val binding get() = _binding!!
    
    private var mediaRecorder: MediaRecorder? = null
    private var isRecording = false
    private var recordingStartTime: Long = 0
    private var recordingHandler: Handler? = null
    private var recordingRunnable: Runnable? = null
    private var recordingFile: File? = null
    
    // File and API variables
    private var selectedFileUri: Uri? = null
    private var currentJobId: String? = null
    private var currentFormattedResult: FormattedResult? = null
    private lateinit var sharedPreferences: SharedPreferences
    private lateinit var resultParser: ResultParser
    
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted: Boolean ->
        if (isGranted) {
            startRecording()
        } else {
            Toast.makeText(requireContext(), getString(R.string.permission_denied), Toast.LENGTH_SHORT).show()
        }
    }
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentRecordingBinding.inflate(inflater, container, false)
        return binding.getRoot()
    }
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        // Initialize components
        sharedPreferences = requireContext().getSharedPreferences("plaud_settings", Context.MODE_PRIVATE)
        resultParser = ResultParser()
        
        setupClickListeners()
        updateRecordingUI()
        updateFileSelectionUI()
    }
    
    private fun setupClickListeners() {
        binding.startRecordingButton.setOnClickListener {
            if (ContextCompat.checkSelfPermission(
                    requireContext(),
                    Manifest.permission.RECORD_AUDIO
                ) == PackageManager.PERMISSION_GRANTED
            ) {
                startRecording()
            } else {
                requestPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
            }
        }
        
        binding.stopRecordingButton.setOnClickListener {
            stopRecording()
        }
        
        binding.selectFileButton.setOnClickListener {
            selectAudioFile()
        }
        
        binding.uploadButton.setOnClickListener {
            uploadAudioFile()
        }
        
        binding.copyResultsButton.setOnClickListener {
            copyResults()
        }
        
        binding.clearResultsButton.setOnClickListener {
            clearResults()
        }
        
        binding.viewDetailsButton.setOnClickListener {
            viewDetails()
        }
    }
    
    private fun startRecording() {
        try {
            mediaRecorder = MediaRecorder().apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.THREE_GPP)
                setAudioEncoder(MediaRecorder.AudioEncoder.AMR_NB)
                
                val outputDir = File(requireContext().filesDir, "recordings")
                if (!outputDir.exists()) {
                    outputDir.mkdirs()
                }
                
                val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
                val fileName = "recording_$timestamp.3gp"
                recordingFile = File(outputDir, fileName)
                
                setOutputFile(recordingFile!!.absolutePath)
                prepare()
                start()
            }
            
            isRecording = true
            recordingStartTime = System.currentTimeMillis()
            startRecordingTimer()
            updateRecordingUI()
            
            Toast.makeText(requireContext(), getString(R.string.recording), Toast.LENGTH_SHORT).show()
            
        } catch (e: IOException) {
            Toast.makeText(requireContext(), getString(R.string.recording_failed, e.message), Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun stopRecording() {
        try {
            mediaRecorder?.apply {
                stop()
                release()
            }
            mediaRecorder = null
            
            isRecording = false
            stopRecordingTimer()
            updateRecordingUI()
            
            // Check if file was created and has content
            if (recordingFile?.exists() == true && recordingFile!!.length() > 0) {
                // Update UI to show recorded file
                updateFileSelectionUI()
                Toast.makeText(requireContext(), getString(R.string.recording_finished), Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(requireContext(), getString(R.string.no_audio_data), Toast.LENGTH_SHORT).show()
                recordingFile = null
            }
            
        } catch (e: Exception) {
            Toast.makeText(requireContext(), getString(R.string.recording_error), Toast.LENGTH_SHORT).show()
            recordingFile = null
        }
    }
    
    private fun startRecordingTimer() {
        recordingHandler = Handler(Looper.getMainLooper())
        recordingRunnable = object : Runnable {
            override fun run() {
                if (isRecording) {
                    val elapsedTime = System.currentTimeMillis() - recordingStartTime
                    val minutes = (elapsedTime / 60000).toInt()
                    val seconds = ((elapsedTime % 60000) / 1000).toInt()
                    
                    binding.recordingTimeTextView.text = getString(R.string.format_time, minutes, seconds)
                    binding.recordingTimeTextView.visibility = View.VISIBLE
                    
                    recordingHandler?.postDelayed(this, 1000)
                }
            }
        }
        recordingHandler?.post(recordingRunnable!!)
    }
    
    private fun stopRecordingTimer() {
        recordingHandler?.removeCallbacks(recordingRunnable!!)
        binding.recordingTimeTextView.visibility = View.GONE
    }
    
    private fun updateRecordingUI() {
        binding.startRecordingButton.isEnabled = !isRecording
        binding.stopRecordingButton.isEnabled = isRecording
        
        if (isRecording) {
            binding.recordingStatusTextView.text = getString(R.string.recording)
            binding.levelWrap.visibility = View.VISIBLE
        } else {
            binding.recordingStatusTextView.text = getString(R.string.not_recording)
            binding.levelWrap.visibility = View.GONE
        }
    }
    
    private fun updateFileSelectionUI() {
        if (_binding == null) return // Check if fragment is still alive
        
        if (recordingFile != null && recordingFile!!.exists()) {
            val file = recordingFile!!
            val fileName = file.name
            val fileSize = file.length()
            val fileSizeMB = fileSize / (1024.0 * 1024.0)
            
            binding.selectedFileTextView.text = getString(R.string.file_selected, fileName)
            binding.statusTextView.text = getString(R.string.ready_to_upload)
            binding.uploadButton.isEnabled = true
            
            // Show file info
            Toast.makeText(requireContext(), 
                "File recorded: $fileName (${String.format("%.1f", fileSizeMB)} MB)", 
                Toast.LENGTH_LONG).show()
        } else if (selectedFileUri != null) {
            val fileName = getFileName(selectedFileUri!!)
            binding.selectedFileTextView.text = getString(R.string.file_selected, fileName)
            binding.statusTextView.text = getString(R.string.ready_to_upload)
            binding.uploadButton.isEnabled = true
        } else {
            binding.selectedFileTextView.text = getString(R.string.no_file_selected)
            binding.statusTextView.text = getString(R.string.ready_to_upload)
            binding.uploadButton.isEnabled = false
        }
    }
    
    private fun selectAudioFile() {
        val intent = Intent(Intent.ACTION_GET_CONTENT)
        intent.type = "audio/*"
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        startActivityForResult(intent, FILE_SELECT_CODE)
    }
    
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == FILE_SELECT_CODE && resultCode == android.app.Activity.RESULT_OK) {
            data?.data?.let { uri ->
                selectedFileUri = uri
                val fileName = getFileName(uri)
                binding.selectedFileTextView.text = getString(R.string.file_selected, fileName)
                binding.uploadButton.isEnabled = true
                binding.statusTextView.text = getString(R.string.ready_to_upload)
            }
        }
    }
    
    private fun getFileName(uri: Uri): String {
        var result: String? = null
        if (uri.scheme == "content") {
            requireContext().contentResolver.query(uri, null, null, null, null)?.use { cursor ->
                if (cursor.moveToFirst()) {
                    val displayNameIndex = cursor.getColumnIndex("_display_name")
                    if (displayNameIndex != -1) {
                        result = cursor.getString(displayNameIndex)
                    }
                }
            }
        }
        if (result == null) {
            result = uri.path
            val cut = result?.lastIndexOf('/')
            if (cut != -1) {
                result = result?.substring(cut!! + 1)
            }
        }
        return result ?: "Unknown file"
    }
    
    private fun uploadAudioFile() {
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
        
        val fileToUpload = if (recordingFile != null && recordingFile!!.exists()) {
            recordingFile!!
        } else if (selectedFileUri != null) {
            // Handle selected file URI
            val inputStream = requireContext().contentResolver.openInputStream(selectedFileUri!!)
            val tempDir = File(requireContext().filesDir, "temp")
            if (!tempDir.exists()) {
                tempDir.mkdirs()
            }
            val tempFile = File(tempDir, "temp_upload_${System.currentTimeMillis()}.3gp")
            tempFile.outputStream().use { output ->
                inputStream?.copyTo(output)
            }
            tempFile
        } else {
            Toast.makeText(requireContext(), "No file selected", Toast.LENGTH_SHORT).show()
            return
        }
        
        binding.progressBar.visibility = View.VISIBLE
        binding.statusTextView.text = getString(R.string.uploading)
        binding.uploadButton.isEnabled = false
        
        val requestBody = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("file", fileToUpload.name, RequestBody.create("audio/*".toMediaType(), fileToUpload))
            .build()
        
        val request = Request.Builder()
            .url("$apiUrl/upload?language=ru")
            .post(requestBody)
            .addHeader("Authorization", "Bearer $authToken")
            .build()
        
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                requireActivity().runOnUiThread {
                    if (_binding == null) return@runOnUiThread
                    binding.progressBar.visibility = View.GONE
                    binding.statusTextView.text = getString(R.string.error)
                    binding.uploadButton.isEnabled = true
                    Toast.makeText(requireContext(), "Upload failed: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
            
            override fun onResponse(call: Call, response: Response) {
                requireActivity().runOnUiThread {
                    if (_binding == null) return@runOnUiThread
                    binding.progressBar.visibility = View.GONE
                    if (response.isSuccessful) {
                        val responseBody = response.body?.string()
                        try {
                            val json = JSONObject(responseBody)
                            currentJobId = json.getString("job_id")
                            binding.statusTextView.text = getString(R.string.processing)
                            checkJobStatus()
                        } catch (e: Exception) {
                            binding.statusTextView.text = getString(R.string.error)
                            Toast.makeText(requireContext(), "Failed to parse response: ${e.message}", Toast.LENGTH_SHORT).show()
                        }
                    } else {
                        binding.statusTextView.text = getString(R.string.error)
                        Toast.makeText(requireContext(), "Upload failed: ${response.code}", Toast.LENGTH_SHORT).show()
                    }
                    binding.uploadButton.isEnabled = true
                }
            }
        })
    }
    
    private fun checkJobStatus() {
        val apiUrl = sharedPreferences.getString("api_url", "") ?: ""
        val authToken = sharedPreferences.getString("auth_token", "") ?: ""
        val jobId = currentJobId ?: return
        
        val request = Request.Builder()
            .url("$apiUrl/status/$jobId")
            .addHeader("Authorization", "Bearer $authToken")
            .build()
        
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                requireActivity().runOnUiThread {
                    if (_binding == null) return@runOnUiThread
                    binding.statusTextView.text = getString(R.string.error)
                    Toast.makeText(requireContext(), "Status check failed: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
            
            override fun onResponse(call: Call, response: Response) {
                requireActivity().runOnUiThread {
                    if (_binding == null) return@runOnUiThread
                    if (response.isSuccessful) {
                        val responseBody = response.body?.string()
                        try {
                            val json = JSONObject(responseBody)
                            val status = json.getString("status")
                            when (status) {
                                "done" -> {
                                    binding.statusTextView.text = getString(R.string.completed)
                                    fetchResults()
                                }
                                "processing", "transcribed_waiting_summary" -> {
                                    binding.statusTextView.text = getString(R.string.processing)
                                    // Check again after 5 seconds
                                    Handler(Looper.getMainLooper()).postDelayed({ checkJobStatus() }, 5000)
                                }
                                else -> {
                                    binding.statusTextView.text = getString(R.string.error)
                                    Toast.makeText(requireContext(), "Unknown status: $status", Toast.LENGTH_SHORT).show()
                                }
                            }
                        } catch (e: Exception) {
                            binding.statusTextView.text = getString(R.string.error)
                            Toast.makeText(requireContext(), "Failed to parse status: ${e.message}", Toast.LENGTH_SHORT).show()
                        }
                    } else {
                        binding.statusTextView.text = getString(R.string.error)
                        Toast.makeText(requireContext(), "Status check failed: ${response.code}", Toast.LENGTH_SHORT).show()
                    }
                }
            }
        })
    }
    
    private fun fetchResults() {
        val apiUrl = sharedPreferences.getString("api_url", "") ?: ""
        val authToken = sharedPreferences.getString("auth_token", "") ?: ""
        val jobId = currentJobId ?: return
        
        if (_binding == null) return
        binding.resultsProgressLayout.visibility = View.VISIBLE
        binding.resultsProgressText.text = getString(R.string.processing)
        binding.simpleResultsScrollView.visibility = View.GONE
        binding.resultsTabLayout.visibility = View.GONE
        binding.resultsViewPager.visibility = View.GONE
        
        val request = Request.Builder()
            .url("$apiUrl/result/$jobId")
            .addHeader("Authorization", "Bearer $authToken")
            .build()
        
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                requireActivity().runOnUiThread {
                    if (_binding == null) return@runOnUiThread
                    binding.resultsProgressLayout.visibility = View.GONE
                    binding.statusTextView.text = getString(R.string.error)
                    binding.simpleResultsScrollView.visibility = View.VISIBLE
                    Toast.makeText(requireContext(), "Failed to fetch results: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
            
            override fun onResponse(call: Call, response: Response) {
                requireActivity().runOnUiThread {
                    if (_binding == null) return@runOnUiThread
                    binding.resultsProgressLayout.visibility = View.GONE
                    if (response.isSuccessful) {
                        val responseBody = response.body?.string()
                        try {
                            val resultData = resultParser.parseResults(responseBody ?: "")
                            if (resultData != null) {
                                currentFormattedResult = resultParser.formatResults(resultData)
                                displayFormattedResults(currentFormattedResult!!)
                            } else {
                                Toast.makeText(requireContext(), "Failed to parse results", Toast.LENGTH_SHORT).show()
                            }
                        } catch (e: Exception) {
                            Toast.makeText(requireContext(), "Failed to parse results: ${e.message}", Toast.LENGTH_SHORT).show()
                        }
                    } else {
                        Toast.makeText(requireContext(), "Failed to fetch results: ${response.code}", Toast.LENGTH_SHORT).show()
                    }
                }
            }
        })
    }
    
    private fun displayFormattedResults(formattedResult: FormattedResult) {
        if (_binding == null) return
        val displayText = resultParser.getCopyableText(formattedResult)
        binding.resultTextView.text = displayText
        binding.simpleResultsScrollView.visibility = View.VISIBLE
        binding.resultsTabLayout.visibility = View.GONE
        binding.resultsViewPager.visibility = View.GONE
        binding.viewDetailsButton.visibility = View.VISIBLE
    }
    
    private fun copyResults() {
        if (currentFormattedResult != null) {
            val clipboard = requireContext().getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = ClipData.newPlainText("Results", resultParser.getCopyableText(currentFormattedResult!!))
            clipboard.setPrimaryClip(clip)
            Toast.makeText(requireContext(), getString(R.string.results_copied), Toast.LENGTH_SHORT).show()
        } else {
            Toast.makeText(requireContext(), getString(R.string.no_results_to_copy), Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun clearResults() {
        binding.resultTextView.text = getString(R.string.no_results_yet)
        currentFormattedResult = null
        currentJobId = null
        binding.simpleResultsScrollView.visibility = View.VISIBLE
        binding.resultsTabLayout.visibility = View.GONE
        binding.resultsViewPager.visibility = View.GONE
        binding.viewDetailsButton.visibility = View.GONE
        binding.statusTextView.text = getString(R.string.ready_to_upload)
        Toast.makeText(requireContext(), "Results cleared", Toast.LENGTH_SHORT).show()
    }
    
    private fun viewDetails() {
        if (currentFormattedResult != null && currentJobId != null) {
            val intent = Intent(requireContext(), ResultsActivity::class.java).apply {
                putExtra("job_id", currentJobId)
                putExtra("formatted_result", currentFormattedResult)
            }
            startActivity(intent)
        } else {
            Toast.makeText(requireContext(), "No results to view", Toast.LENGTH_SHORT).show()
        }
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        if (isRecording) {
            stopRecording()
        }
        recordingFile = null
        _binding = null
    }
    
    companion object {
        private const val FILE_SELECT_CODE = 100
    }
}
