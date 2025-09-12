package com.example.plaudlocal

import android.Manifest
import android.app.AlertDialog
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.media.AudioManager
import android.media.MediaRecorder
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.LayoutInflater
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.viewpager2.widget.ViewPager2
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.floatingactionbutton.FloatingActionButton
import com.google.android.material.tabs.TabLayout
import com.google.android.material.tabs.TabLayoutMediator
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
    private lateinit var selectFileButton: Button
    private lateinit var uploadButton: Button
    private lateinit var selectedFileTextView: TextView
    private lateinit var progressBar: ProgressBar
    private lateinit var statusTextView: TextView
    private lateinit var resultTextView: TextView
    
    // Authentication UI elements
    private lateinit var authStatusTextView: TextView
    private lateinit var loginButton: Button
    
    // Recording UI elements
    private lateinit var startRecordingButton: Button
    private lateinit var stopRecordingButton: Button
    private lateinit var recordingStatusTextView: TextView
    private lateinit var recordingTimeTextView: TextView
    
    // New UI elements
    private lateinit var toolbar: MaterialToolbar
    private lateinit var clearResultsButton: Button
    private lateinit var copyResultsButton: Button
    private lateinit var loadHistoryButton: Button
    private lateinit var historyRecyclerView: RecyclerView
    private lateinit var noHistoryTextView: TextView
    private lateinit var fab: FloatingActionButton
    private lateinit var levelWrap: LinearLayout
    private lateinit var levelBar: ProgressBar
    private lateinit var levelNum: TextView
    
    // Results UI elements
    private lateinit var resultsProgressLayout: LinearLayout
    private lateinit var resultsProgressText: TextView
    private lateinit var resultsTabLayout: TabLayout
    private lateinit var resultsViewPager: ViewPager2
    private lateinit var simpleResultsScrollView: ScrollView
    
    // Result parsing
    private lateinit var resultParser: ResultParser
    private var currentFormattedResult: FormattedResult? = null

    private var selectedFileUri: Uri? = null
    private var currentJobId: String? = null
    private val handler = Handler(Looper.getMainLooper())
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    // Authentication variables
    private lateinit var sharedPreferences: SharedPreferences
    private var authToken: String? = null
    private var currentUsername: String? = null
    private var isLoggedIn = false
    private var isAdmin = false
    
    // Recording variables
    private var mediaRecorder: MediaRecorder? = null
    private var isRecording = false
    private var recordingStartTime: Long = 0
    private var recordingFile: File? = null
    private val recordingTimer = Timer()
    private var recordingTimerTask: TimerTask? = null
    
    // History variables
    private lateinit var historyAdapter: HistoryAdapter
    private val historyList = mutableListOf<HistoryItem>()
    
    // Audio level monitoring
    private var audioManager: AudioManager? = null
    private var levelUpdateHandler: Handler? = null
    private var levelUpdateRunnable: Runnable? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        try {
            // Log startup
            android.util.Log.d("MainActivity", "onCreate started")
            
            // Initialize toolbar
            toolbar = findViewById(R.id.toolbar)
            setSupportActionBar(toolbar)
            
            android.util.Log.d("MainActivity", "Toolbar initialized")

            // Initialize views
            apiUrlEditText = findViewById(R.id.apiUrlEditText)
            selectFileButton = findViewById(R.id.selectFileButton)
            uploadButton = findViewById(R.id.uploadButton)
            selectedFileTextView = findViewById(R.id.selectedFileTextView)
            progressBar = findViewById(R.id.progressBar)
            statusTextView = findViewById(R.id.statusTextView)
            resultTextView = findViewById(R.id.resultTextView)
            
            // Initialize authentication views
            authStatusTextView = findViewById(R.id.authStatusTextView)
            loginButton = findViewById(R.id.loginButton)
            
            // Initialize recording views
            startRecordingButton = findViewById(R.id.startRecordingButton)
            stopRecordingButton = findViewById(R.id.stopRecordingButton)
            recordingStatusTextView = findViewById(R.id.recordingStatusTextView)
            recordingTimeTextView = findViewById(R.id.recordingTimeTextView)
            
            // Initialize new views
            clearResultsButton = findViewById(R.id.clearResultsButton)
            copyResultsButton = findViewById(R.id.copyResultsButton)
            loadHistoryButton = findViewById(R.id.loadHistoryButton)
            historyRecyclerView = findViewById(R.id.historyRecyclerView)
            noHistoryTextView = findViewById(R.id.noHistoryTextView)
            fab = findViewById(R.id.fab)
            levelWrap = findViewById(R.id.levelWrap)
            levelBar = findViewById(R.id.levelBar)
            levelNum = findViewById(R.id.levelNum)
            
            // Initialize results views
            resultsProgressLayout = findViewById(R.id.resultsProgressLayout)
            resultsProgressText = findViewById(R.id.resultsProgressText)
            resultsTabLayout = findViewById(R.id.resultsTabLayout)
            resultsViewPager = findViewById(R.id.resultsViewPager)
            simpleResultsScrollView = findViewById(R.id.simpleResultsScrollView)
            
            // Initialize result parser
            resultParser = ResultParser()
            
            // Initialize SharedPreferences
            sharedPreferences = getSharedPreferences("plaud_auth", MODE_PRIVATE)

            // Set default API URL
            apiUrlEditText.setText("https://plaud.grigofil.keenetic.link")

            // Initialize audio manager
            audioManager = getSystemService(Context.AUDIO_SERVICE) as AudioManager

            // Initialize history adapter
            historyAdapter = HistoryAdapter(historyList) { historyItem ->
                showJobDetails(historyItem)
            }
            historyRecyclerView.layoutManager = LinearLayoutManager(this)
            historyRecyclerView.adapter = historyAdapter

            // Load saved authentication
            loadAuthState()

            // Set up click listeners
            setupClickListeners()
            
            android.util.Log.d("MainActivity", "onCreate completed successfully")
            
        } catch (e: Exception) {
            // Log the error and show a toast
            android.util.Log.e("MainActivity", "Error in onCreate: ${e.message}", e)
            Toast.makeText(this, "Error initializing app: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }
    
    private fun setupClickListeners() {
        try {
            // Authentication button
            loginButton.setOnClickListener {
                if (isLoggedIn) {
                    logout()
                } else {
                    showLoginDialog()
                }
            }

            // File selection button
            selectFileButton.setOnClickListener {
                selectAudioFile()
            }

            // Upload button
            uploadButton.setOnClickListener {
                if (!checkAuth()) return@setOnClickListener
                
                if (selectedFileUri != null) {
                    uploadFile()
                } else {
                    showToast("Please select a file first")
                }
            }
            
            // Recording buttons
            startRecordingButton.setOnClickListener {
                startRecording()
            }
            
            stopRecordingButton.setOnClickListener {
                stopRecording()
            }
            
            // Clear results button
            clearResultsButton.setOnClickListener {
                clearResults()
            }
            
            // Copy results button
            copyResultsButton.setOnClickListener {
                copyResults()
            }
            
            // Load history button
            loadHistoryButton.setOnClickListener {
                if (!checkAuth()) return@setOnClickListener
                loadHistory()
            }
            
            // Floating action button
            fab.setOnClickListener {
                showQuickActionsMenu()
            }
        } catch (e: Exception) {
            android.util.Log.e("MainActivity", "Error setting up click listeners: ${e.message}", e)
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

        if (apiUrl.isEmpty()) {
            Toast.makeText(this, "Please enter API URL", Toast.LENGTH_SHORT).show()
            return
        }

        if (!isLoggedIn || authToken.isNullOrEmpty()) {
            Toast.makeText(this, getString(R.string.auth_required), Toast.LENGTH_SHORT).show()
            return
        }

        progressBar.visibility = ProgressBar.VISIBLE
        statusTextView.text = getString(R.string.uploading)
        uploadButton.isEnabled = false

        selectedFileUri?.let { uri ->
            val file = if (uri.scheme == "file") {
                File(uri.path!!)
            } else {
                // For content URIs, use scoped storage approach
                val inputStream = contentResolver.openInputStream(uri)
                val tempDir = File(getExternalFilesDir(null), "temp")
                if (!tempDir.exists()) {
                    tempDir.mkdirs()
                }
                val tempFile = File(tempDir, "temp_upload_${System.currentTimeMillis()}.3gp")
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
                .addHeader("Authorization", "Bearer $authToken")
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
        val jobId = currentJobId ?: return

        val request = Request.Builder()
            .url("$apiUrl/status/$jobId")
            .addHeader("Authorization", "Bearer $authToken")
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
        val jobId = currentJobId ?: return

        // Show progress indicator
        resultsProgressLayout.visibility = View.VISIBLE
        resultsProgressText.text = getString(R.string.processing)
        simpleResultsScrollView.visibility = View.GONE
        resultsTabLayout.visibility = View.GONE
        resultsViewPager.visibility = View.GONE

        val request = Request.Builder()
            .url("$apiUrl/result/$jobId")
            .addHeader("Authorization", "Bearer $authToken")
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                handler.post {
                    resultsProgressLayout.visibility = View.GONE
                    statusTextView.text = getString(R.string.error)
                    resultTextView.text = "Failed to fetch results: ${e.message}"
                    simpleResultsScrollView.visibility = View.VISIBLE
                }
            }

            override fun onResponse(call: Call, response: Response) {
                handler.post {
                    resultsProgressLayout.visibility = View.GONE
                    if (response.isSuccessful) {
                        val responseBody = response.body?.string()
                        try {
                            val resultData = resultParser.parseResults(responseBody ?: "")
                            if (resultData != null) {
                                currentFormattedResult = resultParser.formatResults(resultData)
                                displayFormattedResults(currentFormattedResult!!)
                            } else {
                                showError("Failed to parse results")
                            }
                        } catch (e: Exception) {
                            showError("Failed to parse results: ${e.message}")
                        }
                    } else {
                        showError("Failed to fetch results: ${response.code}")
                    }
                }
            }
        })
    }

    private fun startRecording() {
        if (!checkAuth()) return
        
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
            // Create recording file using scoped storage approach
            val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
            val recordingsDir = File(getExternalFilesDir(null), "recordings")
            if (!recordingsDir.exists()) {
                recordingsDir.mkdirs()
            }
            recordingFile = File(recordingsDir, "recording_$timestamp.3gp")
            
            // Initialize MediaRecorder with modern configuration
            mediaRecorder = MediaRecorder().apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.THREE_GPP)
                setAudioEncoder(MediaRecorder.AudioEncoder.AMR_NB)
                setOutputFile(recordingFile!!.absolutePath)
                setMaxDuration(0) // No limit
                setMaxFileSize(0) // No limit
                // Set additional parameters to reduce memory pressure
                setAudioSamplingRate(8000) // Lower sample rate to reduce memory usage
                setAudioChannels(1) // Mono recording
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
            
            // Start audio level monitoring
            startAudioLevelMonitoring()
            
            showToast("Recording started")
            
        } catch (e: Exception) {
            Toast.makeText(this, getString(R.string.recording_failed, e.message), Toast.LENGTH_LONG).show()
            resetRecordingUI()
        }
    }
    
    private fun stopRecording() {
        try {
            mediaRecorder?.apply {
                try {
                    stop()
                } catch (e: Exception) {
                    android.util.Log.w("MainActivity", "Error stopping MediaRecorder: ${e.message}")
                }
            }
            resetMediaRecorder()
            
            isRecording = false
            
            // Stop timer
            recordingTimerTask?.cancel()
            recordingTimerTask = null
            
            // Stop audio level monitoring
            stopAudioLevelMonitoring()
            
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
                // Clean up empty file
                recordingFile?.delete()
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
        resetMediaRecorder()
        recordingTimer.cancel()
        cleanupTempFiles()
    }
    
    private fun cleanupTempFiles() {
        try {
            // Clean up temp directory
            val tempDir = File(getExternalFilesDir(null), "temp")
            if (tempDir.exists()) {
                tempDir.listFiles()?.forEach { file ->
                    if (file.isFile && file.name.startsWith("temp_upload_")) {
                        file.delete()
                    }
                }
            }
        } catch (e: Exception) {
            android.util.Log.w("MainActivity", "Error cleaning up temp files: ${e.message}")
        }
    }
    
    private fun resetMediaRecorder() {
        try {
            mediaRecorder?.release()
        } catch (e: Exception) {
            android.util.Log.w("MainActivity", "Error releasing MediaRecorder: ${e.message}")
        } finally {
            mediaRecorder = null
        }
    }

    private fun loadAuthState() {
        authToken = sharedPreferences.getString("auth_token", null)
        currentUsername = sharedPreferences.getString("username", null)
        isLoggedIn = !authToken.isNullOrEmpty() && !currentUsername.isNullOrEmpty()
        
        updateAuthUI()
    }
    
    private fun updateAuthUI() {
        try {
            if (isLoggedIn) {
                authStatusTextView.text = getString(R.string.logged_in_as, currentUsername)
                loginButton.text = getString(R.string.logout)
            } else {
                authStatusTextView.text = getString(R.string.not_logged_in)
                loginButton.text = getString(R.string.login)
            }
        } catch (e: Exception) {
            android.util.Log.e("MainActivity", "Error updating auth UI: ${e.message}", e)
        }
    }
    
    private fun showLoginDialog() {
        val dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_login, null)
        val usernameEditText = dialogView.findViewById<EditText>(R.id.usernameEditText)
        val passwordEditText = dialogView.findViewById<EditText>(R.id.passwordEditText)
        val loginDialogButton = dialogView.findViewById<Button>(R.id.loginDialogButton)
        val cancelDialogButton = dialogView.findViewById<Button>(R.id.cancelDialogButton)
        val errorTextView = dialogView.findViewById<TextView>(R.id.loginErrorTextView)
        
        val dialog = AlertDialog.Builder(this)
            .setView(dialogView)
            .setCancelable(false)
            .create()
        
        loginDialogButton.setOnClickListener {
            val username = usernameEditText.text.toString().trim()
            val password = passwordEditText.text.toString()
            
            if (username.isEmpty() || password.isEmpty()) {
                errorTextView.text = getString(R.string.invalid_credentials)
                errorTextView.visibility = TextView.VISIBLE
                return@setOnClickListener
            }
            
            loginDialogButton.isEnabled = false
            errorTextView.visibility = TextView.GONE
            
            performLogin(username, password) { success, message ->
                handler.post {
                    if (success) {
                        dialog.dismiss()
                        updateAuthUI()
                        Toast.makeText(this, getString(R.string.login_success), Toast.LENGTH_SHORT).show()
                    } else {
                        errorTextView.text = message
                        errorTextView.visibility = TextView.VISIBLE
                        loginDialogButton.isEnabled = true
                    }
                }
            }
        }
        
        cancelDialogButton.setOnClickListener {
            dialog.dismiss()
        }
        
        dialog.show()
    }
    
    private fun performLogin(username: String, password: String, callback: (Boolean, String) -> Unit) {
        val apiUrl = apiUrlEditText.text.toString().trim()
        if (apiUrl.isEmpty()) {
            callback(false, getString(R.string.connection_error))
            return
        }
        
        val formData = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("username", username)
            .addFormDataPart("password", password)
            .build()
        
        val request = Request.Builder()
            .url("$apiUrl/auth/login")
            .post(formData)
            .build()
        
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                callback(false, getString(R.string.connection_error))
            }
            
            override fun onResponse(call: Call, response: Response) {
                if (response.isSuccessful) {
                    try {
                        val json = JSONObject(response.body?.string() ?: "")
                        val token = json.getString("access_token")
                        val returnedUsername = json.getString("username")
                        
                        // Save authentication data
                        sharedPreferences.edit()
                            .putString("auth_token", token)
                            .putString("username", returnedUsername)
                            .apply()
                        
                        authToken = token
                        currentUsername = returnedUsername
                        isLoggedIn = true
                        
                        callback(true, "")
                    } catch (e: Exception) {
                        callback(false, getString(R.string.login_failed))
                    }
                } else {
                    try {
                        val errorJson = JSONObject(response.body?.string() ?: "")
                        val errorMessage = errorJson.optString("detail", getString(R.string.login_failed))
                        callback(false, errorMessage)
                    } catch (e: Exception) {
                        callback(false, getString(R.string.login_failed))
                    }
                }
            }
        })
    }
    
    private fun logout() {
        sharedPreferences.edit()
            .remove("auth_token")
            .remove("username")
            .apply()
        
        authToken = null
        currentUsername = null
        isLoggedIn = false
        
        updateAuthUI()
        Toast.makeText(this, getString(R.string.logout_success), Toast.LENGTH_SHORT).show()
    }
    
    private fun checkAuth(): Boolean {
        if (!isLoggedIn) {
            Toast.makeText(this, getString(R.string.auth_required), Toast.LENGTH_SHORT).show()
            return false
        }
        return true
    }

    // New methods for enhanced functionality
    
    private fun showToast(message: String) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show()
    }
    
    private fun clearResults() {
        resultTextView.text = getString(R.string.no_results_yet)
        currentFormattedResult = null
        simpleResultsScrollView.visibility = View.VISIBLE
        resultsTabLayout.visibility = View.GONE
        resultsViewPager.visibility = View.GONE
        showToast("Results cleared")
    }
    
    private fun copyResults() {
        if (currentFormattedResult != null) {
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = ClipData.newPlainText("Results", resultParser.getCopyableText(currentFormattedResult!!))
            clipboard.setPrimaryClip(clip)
            showToast(getString(R.string.results_copied))
        } else {
            showToast(getString(R.string.no_results_to_copy))
        }
    }
    
    private fun displayFormattedResults(formattedResult: FormattedResult) {
        // For now, use simple text display
        // TODO: Implement tabbed view with ViewPager2
        val displayText = resultParser.getCopyableText(formattedResult)
        resultTextView.text = displayText
        simpleResultsScrollView.visibility = View.VISIBLE
        resultsTabLayout.visibility = View.GONE
        resultsViewPager.visibility = View.GONE
    }
    
    private fun showError(message: String) {
        statusTextView.text = getString(R.string.error)
        resultTextView.text = message
        simpleResultsScrollView.visibility = View.VISIBLE
        resultsTabLayout.visibility = View.GONE
        resultsViewPager.visibility = View.GONE
    }
    
    private fun loadHistory() {
        if (!isLoggedIn || authToken.isNullOrEmpty()) {
            showToast("Please login first")
            return
        }
        
        val apiUrl = apiUrlEditText.text.toString().trim()
        if (apiUrl.isEmpty()) {
            showToast("Please enter API URL")
            return
        }
        
        showToast("Loading history...")
        
        val request = Request.Builder()
            .url("$apiUrl/history")
            .addHeader("Authorization", "Bearer $authToken")
            .build()
        
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                handler.post {
                    showToast("Failed to load history: ${e.message}")
                }
            }
            
            override fun onResponse(call: Call, response: Response) {
                handler.post {
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
                            
                            if (historyList.isEmpty()) {
                                noHistoryTextView.visibility = View.VISIBLE
                                historyRecyclerView.visibility = View.GONE
                            } else {
                                noHistoryTextView.visibility = View.GONE
                                historyRecyclerView.visibility = View.VISIBLE
                            }
                            
                            showToast("History loaded: ${historyList.size} items")
                        } catch (e: Exception) {
                            showToast("Failed to parse history: ${e.message}")
                        }
                    } else {
                        showToast("Failed to load history: ${response.code}")
                    }
                }
            }
        })
    }
    
    private fun showJobDetails(historyItem: HistoryItem) {
        // TODO: Implement job details dialog
        showToast("Job details: ${historyItem.filename}")
    }
    
    private fun showQuickActionsMenu() {
        val options = arrayOf(
            "Start Recording",
            "Select File", 
            "Load History",
            "Settings"
        )
        
        AlertDialog.Builder(this)
            .setTitle("Quick Actions")
            .setItems(options) { _, which ->
                when (which) {
                    0 -> startRecording()
                    1 -> selectAudioFile()
                    2 -> loadHistory()
                    3 -> showSettings()
                }
            }
            .show()
    }
    
    private fun showSettings() {
        // TODO: Implement settings dialog
        showToast("Settings coming soon")
    }
    
    private fun startAudioLevelMonitoring() {
        levelWrap.visibility = View.VISIBLE
        levelUpdateHandler = Handler(Looper.getMainLooper())
        levelUpdateRunnable = object : Runnable {
            override fun run() {
                if (isRecording) {
                    // Get audio level from MediaRecorder
                    val amplitude = mediaRecorder?.maxAmplitude ?: 0
                    val level = (amplitude * 100 / 32767).coerceIn(0, 100)
                    
                    levelBar.progress = level
                    levelNum.text = "$level%"
                    
                    levelUpdateHandler?.postDelayed(this, 100)
                } else {
                    levelWrap.visibility = View.GONE
                }
            }
        }
        levelUpdateHandler?.post(levelUpdateRunnable!!)
    }
    
    private fun stopAudioLevelMonitoring() {
        levelUpdateHandler?.removeCallbacks(levelUpdateRunnable!!)
        levelWrap.visibility = View.GONE
    }
    
    override fun onCreateOptionsMenu(menu: Menu?): Boolean {
        menuInflater.inflate(R.menu.main_menu, menu)
        return true
    }
    
    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_settings -> {
                showSettings()
                true
            }
            R.id.action_history -> {
                loadHistory()
                true
            }
            R.id.action_help -> {
                showHelp()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }
    
    private fun showHelp() {
        AlertDialog.Builder(this)
            .setTitle("Help")
            .setMessage("• Tap and hold for options\n• Use floating button for quick actions\n• Swipe down to refresh")
            .setPositiveButton("OK", null)
            .show()
    }

    companion object {
        private const val FILE_SELECT_CODE = 100
        private const val RECORD_AUDIO_PERMISSION_CODE = 101
    }
}