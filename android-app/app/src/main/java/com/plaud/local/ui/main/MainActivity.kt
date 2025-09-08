package com.plaud.local.ui.main

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.viewModels
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.isVisible
import com.plaud.local.databinding.ActivityMainBinding
import com.plaud.local.domain.model.FileUploadState
import com.plaud.local.domain.model.TranscriptionStatus
import com.plaud.local.ui.auth.LoginActivity
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val viewModel: TranscriptionViewModel by viewModels()

    private var authToken: String = ""
    private var serverUrl: String = ""

    private val filePickerLauncher = registerForActivityResult(
        ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        uri?.let { handleFileSelection(it) }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Получаем данные авторизации
        authToken = intent.getStringExtra("auth_token") ?: ""
        serverUrl = intent.getStringExtra("server_url") ?: "http://10.0.2.2:8000"

        if (authToken.isEmpty()) {
            navigateToLogin()
            return
        }

        setupUI()
        setupObservers()
    }

    private fun setupUI() {
        binding.welcomeTextView.text = getString(R.string.welcome_message, "User")

        binding.selectFileButton.setOnClickListener {
            openFilePicker()
        }

        binding.uploadButton.setOnClickListener {
            // Upload будет обрабатываться после выбора файла
        }

        binding.logoutButton.setOnClickListener {
            // TODO: Реализовать logout
            navigateToLogin()
        }
    }

    private fun setupObservers() {
        viewModel.uploadState.observe(this) { state ->
            handleUploadState(state)
        }

        viewModel.currentJob.observe(this) { job ->
            job?.let { updateJobStatus(it) }
        }

        viewModel.transcriptionResult.observe(this) { result ->
            result?.let { showResults(it) }
        }
    }

    private fun openFilePicker() {
        filePickerLauncher.launch("audio/*")
    }

    private fun handleFileSelection(uri: Uri) {
        val fileName = getFileNameFromUri(uri)
        val fileSize = getFileSizeFromUri(uri)
        
        if (fileName != null && fileSize != null) {
            viewModel.selectFile(fileName, fileSize)
            // TODO: Сохранить URI для последующей загрузки
        }
    }

    private fun getFileNameFromUri(uri: Uri): String? {
        return contentResolver.query(uri, null, null, null, null)?.use { cursor ->
            if (cursor.moveToFirst()) {
                val displayNameIndex = cursor.getColumnIndex("_display_name")
                if (displayNameIndex != -1) {
                    cursor.getString(displayNameIndex)
                } else {
                    uri.lastPathSegment
                }
            } else {
                uri.lastPathSegment
            }
        }
    }

    private fun getFileSizeFromUri(uri: Uri): Long? {
        return contentResolver.openFileDescriptor(uri, "r")?.use { parcel ->
            parcel.statSize
        }
    }

    private fun handleUploadState(state: FileUploadState) {
        when (state) {
            is FileUploadState.Idle -> {
                binding.progressBar.isVisible = false
                binding.statusTextView.text = getString(R.string.ready_to_upload)
                binding.uploadButton.isEnabled = false
            }
            is FileUploadState.Selecting -> {
                binding.progressBar.isVisible = false
                binding.statusTextView.text = getString(R.string.select_file)
            }
            is FileUploadState.Selected -> {
                binding.progressBar.isVisible = false
                binding.selectedFileTextView.text = getString(R.string.file_selected, state.fileName)
                binding.uploadButton.isEnabled = true
                binding.statusTextView.text = getString(R.string.ready_to_upload)
            }
            is FileUploadState.Uploading -> {
                binding.progressBar.isVisible = true
                binding.statusTextView.text = getString(R.string.uploading)
                binding.uploadButton.isEnabled = false
            }
            is FileUploadState.Uploaded -> {
                binding.progressBar.isVisible = true
                binding.statusTextView.text = getString(R.string.processing)
                binding.uploadButton.isEnabled = false
            }
            is FileUploadState.Error -> {
                binding.progressBar.isVisible = false
                binding.statusTextView.text = getString(R.string.error)
                binding.resultTextView.text = state.message
                binding.uploadButton.isEnabled = true
            }
        }
    }

    private fun updateJobStatus(job: com.plaud.local.domain.model.TranscriptionJob) {
        when (job.status) {
            TranscriptionStatus.UPLOADING -> {
                binding.statusTextView.text = getString(R.string.uploading)
            }
            TranscriptionStatus.PROCESSING -> {
                binding.statusTextView.text = getString(R.string.processing)
            }
            TranscriptionStatus.TRANSCRIBED_WAITING_SUMMARY -> {
                binding.statusTextView.text = "Generating summary..."
            }
            TranscriptionStatus.DONE -> {
                binding.statusTextView.text = getString(R.string.completed)
            }
            TranscriptionStatus.ERROR -> {
                binding.statusTextView.text = getString(R.string.error)
                binding.resultTextView.text = job.errorMessage ?: "Unknown error"
            }
        }
    }

    private fun showResults(result: com.plaud.local.domain.model.TranscriptionResult) {
        val resultText = buildString {
            appendLine("=== TRANSCRIPT ===")
            result.transcript?.let { transcript ->
                appendLine(transcript.text)
                transcript.segments?.forEach { segment ->
                    appendLine("[${segment.start}-${segment.end}]: ${segment.text}")
                }
            } ?: appendLine("No transcript available")
            
            appendLine("\n=== SUMMARY ===")
            result.summary?.let { summary ->
                appendLine(summary.text)
                summary.keyPoints?.forEach { point ->
                    appendLine("• $point")
                }
            } ?: appendLine("No summary available")
        }
        
        binding.resultTextView.text = resultText
    }

    private fun navigateToLogin() {
        val intent = Intent(this, LoginActivity::class.java)
        startActivity(intent)
        finish()
    }
}