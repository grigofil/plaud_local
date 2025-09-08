package com.plaud.local.ui.auth

import android.content.Intent
import android.os.Bundle
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.isVisible
import androidx.core.widget.addTextChangedListener
import com.plaud.local.databinding.ActivityLoginBinding
import com.plaud.local.ui.main.MainActivity
import com.plaud.local.domain.model.AuthState
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class LoginActivity : AppCompatActivity() {

    private lateinit var binding: ActivityLoginBinding
    private val viewModel: AuthViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityLoginBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupUI()
        setupObservers()
        
        // Проверить сохраненный токен при запуске
        viewModel.validateSavedToken()
    }

    private fun setupUI() {
        binding.usernameEditText.addTextChangedListener {
            viewModel.setUsername(it.toString())
            updateLoginButtonState()
        }

        binding.passwordEditText.addTextChangedListener {
            viewModel.setPassword(it.toString())
            updateLoginButtonState()
        }

        binding.serverUrlEditText.addTextChangedListener {
            viewModel.setServerUrl(it.toString())
            updateLoginButtonState()
        }

        binding.rememberMeCheckBox.setOnCheckedChangeListener { _, isChecked ->
            viewModel.setRememberMe(isChecked)
        }

        binding.loginButton.setOnClickListener {
            viewModel.login()
        }
    }

    private fun setupObservers() {
        viewModel.username.observe(this) { username ->
            if (binding.usernameEditText.text.toString() != username) {
                binding.usernameEditText.setText(username)
            }
        }

        viewModel.serverUrl.observe(this) { serverUrl ->
            if (binding.serverUrlEditText.text.toString() != serverUrl) {
                binding.serverUrlEditText.setText(serverUrl)
            }
        }

        viewModel.authState.observe(this) { state ->
            when (state) {
                is AuthState.Idle -> {
                    showLoading(false)
                    binding.loginButton.isEnabled = true
                }
                is AuthState.Loading -> {
                    showLoading(true)
                    binding.loginButton.isEnabled = false
                }
                is AuthState.Success -> {
                    showLoading(false)
                    navigateToMainActivity(state.token, state.userId)
                }
                is AuthState.Error -> {
                    showLoading(false)
                    binding.loginButton.isEnabled = true
                    showError(state.message)
                }
            }
        }
    }

    private fun updateLoginButtonState() {
        val username = binding.usernameEditText.text.toString()
        val password = binding.passwordEditText.text.toString()
        val serverUrl = binding.serverUrlEditText.text.toString()
        
        binding.loginButton.isEnabled = username.isNotEmpty() && 
                password.isNotEmpty() && serverUrl.isNotEmpty()
    }

    private fun showLoading(show: Boolean) {
        binding.progressBar.isVisible = show
        binding.loginButton.text = if (show) {
            getString(R.string.logging_in)
        } else {
            getString(R.string.login_button)
        }
    }

    private fun showError(message: String) {
        // Можно добавить Snackbar или Toast для показа ошибки
        binding.errorTextView.text = message
        binding.errorTextView.isVisible = true
    }

    private fun navigateToMainActivity(token: String, userId: String) {
        val intent = Intent(this, MainActivity::class.java).apply {
            putExtra("auth_token", token)
            putExtra("user_id", userId)
        }
        startActivity(intent)
        finish()
    }

    override fun onBackPressed() {
        // Prevent going back to previous activity
        moveTaskToBack(true)
    }
}