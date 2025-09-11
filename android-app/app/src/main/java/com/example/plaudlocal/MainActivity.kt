package com.example.plaudlocal

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.media.MediaRecorder
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.Button
import android.widget.EditText
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
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

class MainActivity : AppCompatActivity() {

    private lateinit var apiUrlEditText: EditText
    private lateinit var apiTokenEditText: EditText
    private lateinit var selectFileButton: Button
    private lateinit var uploadButton: Button
    private lateinit var selectedFileTextView: TextView
    private lateinit var progressBar: ProgressBar
    private lateinit var statusTextView: TextView
    private lateinit var resultTextView: TextView
    
    // Recording UI elements
    private lateinit var startRecordingButton: Button
    private lateinit var stopRecordingButton: Button
    private lateinit var recordingStatusTextView: TextView
    private lateinit var recordingTimeTextView: TextView

    private var selectedFileUri: Uri? = null
    private var currentJobId: String? = null
    private val handler = Handler(Looper.getMainLooper())
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    // Recording variables
    private var mediaRecorder: MediaRecorder? = null
    private var isRecording = false
    private var recordingStartTime: Long = 0
    private var recordingFile: File? = null
    private val recordingTimer = Timer()
    private var recordingTimerTask: TimerTask? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Initialize views
        apiUrlEditText = findViewById(R.id.apiUrlEditText)
        apiTokenEditText = findViewById(R.id.apiTokenEditText)
        selectFileButton = findViewById(R.id.selectFileButton)
        uploadButton = findViewById(R.id.uploadButton)
        selectedFileTextView = findViewById(R.id.selectedFileTextView)
        progressBar = findViewById(R.id.progressBar)
        statusTextView = findViewById(R.id.statusTextView)
        resultTextView = findViewById(R.id.resultTextView)
        
        // Initialize recording views
        startRecordingButton = findViewById(R.id.startRecordingButton)
        stopRecordingButton = findViewById(R.id.stopRecordingButton)
        recordingStatusTextView = findViewById(R.id.recordingStatusTextView)
        recordingTimeTextView = findViewById(R.id.recordingTimeTextView)

        // Set default API URL (localhost for emulator, change for real device)
        apiUrlEditText.setText("http://10.0.2.2:8000")

        // File selection button
        selectFileButton.setOnClickListener {
            selectAudioFile()
        }

        // Upload button
        uploadButton.setOnClickListener {
            if (selectedFileUri != null) {
                uploadFile()
            } else {
                Toast.makeText(this, "Please select a file first", Toast.LENGTH_SHORT).show()
            }
        }
        
        // Recording buttons
        startRecordingButton.setOnClickListener {
            startRecording()
        }
        
        stopRecordingButton.setOnClickListener {
            stopRecording()
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
        if (requestCode == FILE_SELECT_CODE && resultCode == RESULT_OK) {
            data?.data?.let { uri ->
                selectedFileUri = uri
                val fileName = getFileName(uri)
                selectedFileTextView.text = getString(R.string.file_selected, fileName)
                uploadButton.isEnabled = true
            }
        }
    }

    private fun getFileName(uri: Uri): String {
        var result: String? = null
        if (uri.scheme == "content") {
            contentResolver.query(uri, null, null, null, null)?.use { cursor ->
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

    private fun uploadFile() {
        val apiUrl = apiUrlEditText.text.toString().trim()
        val apiToken = apiTokenEditText.text.toString().trim()

        if (apiUrl.isEmpty()) {
            Toast.makeText(this, "Please enter API URL", Toast.LENGTH_SHORT).show()
            return
        }

        if (apiToken.isEmpty()) {
            Toast.makeText(this, "Please enter API token", Toast.LENGTH_SHORT).show()
            return
        }

        progressBar.visibility = ProgressBar.VISIBLE
        statusTextView.text = getString(R.string.uploading)
        uploadButton.isEnabled = false

        selectedFileUri?.let { uri ->
            val file = if (uri.scheme == "file") {
                File(uri.path!!)
            } else {
                // For content URIs, we need to read the file differently
                val inputStream = contentResolver.openInputStream(uri)
                val tempFile = File(getExternalFilesDir(null), "temp_upload.3gp")
                tempFile.outputStream().use { output ->
                    inputStream?.copyTo(output)
                }
                tempFile
            }
            
            val requestBody = MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("file", file.name, RequestBody.create("audio/*".toMediaType(), file))
                .build()

            val request = Request.Builder()
                .url("$apiUrl/upload?language=ru")
                .post(requestBody)
                .addHeader("X-API-Key", apiToken)
                .build()

            client.newCall(request).enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    handler.post {
                        progressBar.visibility = ProgressBar.GONE
                        statusTextView.text = getString(R.string.error)
                        resultTextView.text = "Upload failed: ${e.message}"
                        uploadButton.isEnabled = true
                    }
                }

                override fun onResponse(call: Call, response: Response) {
                    handler.post {
                        progressBar.visibility = ProgressBar.GONE
                        if (response.isSuccessful) {
                            val responseBody = response.body?.string()
                            try {
                                val json = JSONObject(responseBody)
                                currentJobId = json.getString("job_id")
                                statusTextView.text = getString(R.string.processing)
                                checkJobStatus()
                            } catch (e: Exception) {
                                statusTextView.text = getString(R.string.error)
                                resultTextView.text = "Failed to parse response: ${e.message}"
                            }
                        } else {
                            statusTextView.text = getString(R.string.error)
                            resultTextView.text = "Upload failed: ${response.code} - ${response.message}"
                        }
                        uploadButton.isEnabled = true
                    }
                }
            })
        }
    }

    private fun checkJobStatus() {
        val apiUrl = apiUrlEditText.text.toString().trim()
        val apiToken = apiTokenEditText.text.toString().trim()
        val jobId = currentJobId ?: return

        val request = Request.Builder()
            .url("$apiUrl/status/$jobId")
            .addHeader("X-API-Key", apiToken)
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                handler.post {
                    statusTextView.text = getString(R.string.error)
                    resultTextView.text = "Status check failed: ${e.message}"
                }
            }

            override fun onResponse(call: Call, response: Response) {
                handler.post {
                    if (response.isSuccessful) {
                        val responseBody = response.body?.string()
                        try {
                            val json = JSONObject(responseBody)
                            val status = json.getString("status")
                            when (status) {
                                "done" -> {
                                    statusTextView.text = getString(R.string.completed)
                                    fetchResults()
                                }
                                "processing", "transcribed_waiting_summary" -> {
                                    statusTextView.text = getString(R.string.processing)
                                    // Check again after 5 seconds
                                    handler.postDelayed({ checkJobStatus() }, 5000)
                                }
                                else -> {
                                    statusTextView.text = getString(R.string.error)
                                    resultTextView.text = "Unknown status: $status"
                                }
                            }
                        } catch (e: Exception) {
                            statusTextView.text = getString(R.string.error)
                            resultTextView.text = "Failed to parse status: ${e.message}"
                        }
                    } else {
                        statusTextView.text = getString(R.string.error)
                        resultTextView.text = "Status check failed: ${response.code}"
                    }
                }
            }
        })
    }

    private fun fetchResults() {
        val apiUrl = apiUrlEditText.text.toString().trim()
        val apiToken = apiTokenEditText.text.toString().trim()
        val jobId = currentJobId ?: return

        val request = Request.Builder()
            .url("$apiUrl/result/$jobId")
            .addHeader("X-API-Key", apiToken)
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                handler.post {
                    statusTextView.text = getString(R.string.error)
                    resultTextView.text = "Failed to fetch results: ${e.message}"
                }
            }

            override fun onResponse(call: Call, response: Response) {
                handler.post {
                    if (response.isSuccessful) {
                        val responseBody = response.body?.string()
                        try {
                            val json = JSONObject(responseBody)
                            val transcript = json.optJSONObject("transcript")
                            val summary = json.optJSONObject("summary")
                            
                            val resultText = StringBuilder()
                            resultText.append("=== TRANSCRIPT ===\n")
                            if (transcript != null) {
                                resultText.append(transcript.toString(2))
                            } else {
                                resultText.append("No transcript available")
                            }
                            
                            resultText.append("\n\n=== SUMMARY ===\n")
                            if (summary != null) {
                                resultText.append(summary.toString(2))
                            } else {
                                resultText.append("No summary available")
                            }
                            
                            resultTextView.text = resultText.toString()
                        } catch (e: Exception) {
                            resultTextView.text = "Failed to parse results: ${e.message}"
                        }
                    } else {
                        resultTextView.text = "Failed to fetch results: ${response.code}"
                    }
                }
            }
        })
    }

    private fun startRecording() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) 
            != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.RECORD_AUDIO),
                RECORD_AUDIO_PERMISSION_CODE
            )
            return
        }
        
        try {
            // Create recording file
            val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
            recordingFile = File(getExternalFilesDir(null), "recording_$timestamp.3gp")
            
            // Initialize MediaRecorder
            mediaRecorder = MediaRecorder().apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.THREE_GPP)
                setAudioEncoder(MediaRecorder.AudioEncoder.AMR_NB)
                setOutputFile(recordingFile!!.absolutePath)
                prepare()
                start()
            }
            
            isRecording = true
            recordingStartTime = System.currentTimeMillis()
            
            // Update UI
            startRecordingButton.isEnabled = false
            stopRecordingButton.isEnabled = true
            recordingStatusTextView.text = getString(R.string.recording)
            recordingTimeTextView.visibility = TextView.VISIBLE
            
            // Start timer
            startRecordingTimer()
            
            Toast.makeText(this, "Recording started", Toast.LENGTH_SHORT).show()
            
        } catch (e: Exception) {
            Toast.makeText(this, getString(R.string.recording_failed, e.message), Toast.LENGTH_LONG).show()
            resetRecordingUI()
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
            
            // Stop timer
            recordingTimerTask?.cancel()
            recordingTimerTask = null
            
            // Update UI
            resetRecordingUI()
            
            // Check if file was created and has content
            if (recordingFile?.exists() == true && recordingFile!!.length() > 0) {
                recordingStatusTextView.text = getString(R.string.recording_finished)
                recordingTimeTextView.text = ""
                
                // Set the recorded file as selected file
                selectedFileUri = Uri.fromFile(recordingFile)
                selectedFileTextView.text = getString(R.string.file_selected, recordingFile!!.name)
                uploadButton.isEnabled = true
                
                Toast.makeText(this, "Recording completed", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this, getString(R.string.no_audio_data), Toast.LENGTH_LONG).show()
                recordingStatusTextView.text = getString(R.string.recording_error)
            }
            
        } catch (e: Exception) {
            Toast.makeText(this, getString(R.string.recording_failed, e.message), Toast.LENGTH_LONG).show()
            resetRecordingUI()
        }
    }
    
    private fun resetRecordingUI() {
        startRecordingButton.isEnabled = true
        stopRecordingButton.isEnabled = false
        recordingStatusTextView.text = getString(R.string.not_recording)
        recordingTimeTextView.visibility = TextView.GONE
    }
    
    private fun startRecordingTimer() {
        recordingTimerTask = object : TimerTask() {
            override fun run() {
                if (isRecording) {
                    val elapsedTime = System.currentTimeMillis() - recordingStartTime
                    val seconds = elapsedTime / 1000
                    val minutes = seconds / 60
                    val remainingSeconds = seconds % 60
                    
                    handler.post {
                        recordingTimeTextView.text = getString(
                            R.string.recording_time,
                            String.format("%02d:%02d", minutes, remainingSeconds)
                        )
                    }
                }
            }
        }
        recordingTimer.scheduleAtFixedRate(recordingTimerTask, 0, 1000)
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        when (requestCode) {
            RECORD_AUDIO_PERMISSION_CODE -> {
                if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                    startRecording()
                } else {
                    Toast.makeText(this, getString(R.string.permission_denied), Toast.LENGTH_LONG).show()
                }
            }
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        if (isRecording) {
            stopRecording()
        }
        recordingTimer.cancel()
    }

    companion object {
        private const val FILE_SELECT_CODE = 100
        private const val RECORD_AUDIO_PERMISSION_CODE = 101
    }
}