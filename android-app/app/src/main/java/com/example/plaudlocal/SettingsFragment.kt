package com.example.plaudlocal

import android.app.AlertDialog
import android.content.Context
import android.content.SharedPreferences
import android.content.res.Configuration
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatDelegate
import androidx.fragment.app.Fragment
import java.util.Locale
import okhttp3.Call
import okhttp3.Callback
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

class SettingsFragment : Fragment() {
    
    private var _binding: FragmentSettingsBinding? = null
    private val binding get() = _binding!!
    
    private lateinit var sharedPreferences: SharedPreferences
    private val saveApiUrlRunnable = Runnable { saveApiUrl() }
    
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
        _binding = FragmentSettingsBinding.inflate(inflater, container, false)
        return binding.getRoot()
    }
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        sharedPreferences = requireContext().getSharedPreferences("plaud_settings", android.content.Context.MODE_PRIVATE)
        setupClickListeners()
        loadSettings()
    }
    
    private fun setupClickListeners() {
        binding.loginButton.setOnClickListener {
            val isLoggedIn = sharedPreferences.getBoolean("is_logged_in", false)
            if (isLoggedIn) {
                logout()
            } else {
                showLoginDialog()
            }
        }
        
        binding.saveApiUrlButton.setOnClickListener {
            saveApiUrl()
        }
        
        // API URL change listener
        binding.apiUrlEditText.setOnFocusChangeListener { _, hasFocus ->
            if (!hasFocus && _binding != null) {
                saveApiUrl()
            }
        }
        
        // Auto-save API URL when text changes
        binding.apiUrlEditText.addTextChangedListener(object : android.text.TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            override fun afterTextChanged(s: android.text.Editable?) {
                if (_binding == null) return
                // Save after a short delay to avoid too frequent saves
                binding.apiUrlEditText.removeCallbacks(saveApiUrlRunnable)
                binding.apiUrlEditText.postDelayed(saveApiUrlRunnable, 2000) // Increased delay to 2 seconds
            }
        })
        
        // Theme selection
        binding.themeToggleGroup.addOnButtonCheckedListener { _, checkedId, isChecked ->
            if (isChecked) {
                when (checkedId) {
                    R.id.lightThemeButton -> setTheme(AppCompatDelegate.MODE_NIGHT_NO)
                    R.id.darkThemeButton -> setTheme(AppCompatDelegate.MODE_NIGHT_YES)
                    R.id.autoThemeButton -> setTheme(AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM)
                }
            }
        }
        
        // Language selection
        binding.languageToggleGroup.addOnButtonCheckedListener { _, checkedId, isChecked ->
            if (isChecked) {
                when (checkedId) {
                    R.id.russianLanguageButton -> setLanguage("ru")
                    R.id.englishLanguageButton -> setLanguage("en")
                }
            }
        }
    }
    
    private fun loadSettings() {
        // Load theme setting
        val currentTheme = sharedPreferences.getInt("theme_mode", AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM)
        when (currentTheme) {
            AppCompatDelegate.MODE_NIGHT_NO -> binding.lightThemeButton.isChecked = true
            AppCompatDelegate.MODE_NIGHT_YES -> binding.darkThemeButton.isChecked = true
            AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM -> binding.autoThemeButton.isChecked = true
        }
        
        // Load language setting
        val currentLanguage = sharedPreferences.getString("language", "ru") ?: "ru"
        when (currentLanguage) {
            "ru" -> binding.russianLanguageButton.isChecked = true
            "en" -> binding.englishLanguageButton.isChecked = true
        }
        
        // Load API URL
        val apiUrl = sharedPreferences.getString("api_url", "https://plaud.grigofil.keenetic.link")
        binding.apiUrlEditText.setText(apiUrl)
        
        // Load auth status
        val isLoggedIn = sharedPreferences.getBoolean("is_logged_in", false)
        val username = sharedPreferences.getString("username", "")
        updateAuthStatus(isLoggedIn, username)
    }
    
    private fun setTheme(themeMode: Int) {
        AppCompatDelegate.setDefaultNightMode(themeMode)
        sharedPreferences.edit().putInt("theme_mode", themeMode).apply()
    }
    
    private fun setLanguage(language: String) {
        sharedPreferences.edit().putString("language", language).apply()
        
        // Set locale
        val locale = when (language) {
            "ru" -> Locale("ru")
            "en" -> Locale("en")
            else -> Locale.getDefault()
        }
        
        Locale.setDefault(locale)
        val config = Configuration(requireContext().resources.configuration)
        config.setLocale(locale)
        requireContext().resources.updateConfiguration(config, requireContext().resources.displayMetrics)
        
        if (_binding != null) {
            Toast.makeText(requireContext(), "Language changed to $language. Restart app to apply changes.", Toast.LENGTH_LONG).show()
        }
        
        // Note: Language change will take effect on next app restart
        // Removing automatic activity recreation to prevent infinite loops
    }
    
    private fun saveApiUrl() {
        if (_binding == null) return // Check if fragment is still alive
        
        val apiUrl = binding.apiUrlEditText.text.toString().trim()
        val currentApiUrl = sharedPreferences.getString("api_url", "")
        if (apiUrl != currentApiUrl) {
            sharedPreferences.edit().putString("api_url", apiUrl).apply()
            if (_binding != null) {
                Toast.makeText(requireContext(), "API URL saved", Toast.LENGTH_SHORT).show()
            }
        }
    }
    
    private fun updateAuthStatus(isLoggedIn: Boolean, username: String?) {
        if (_binding == null) return // Check if fragment is still alive
        
        if (isLoggedIn && !username.isNullOrEmpty()) {
            binding.authStatusTextView.text = getString(R.string.logged_in_as, username)
            binding.loginButton.text = getString(R.string.logout)
        } else {
            binding.authStatusTextView.text = getString(R.string.not_logged_in)
            binding.loginButton.text = getString(R.string.login)
        }
    }
    
    private fun showLoginDialog() {
        val dialogView = LayoutInflater.from(requireContext()).inflate(R.layout.dialog_login, null)
        val usernameEditText = dialogView.findViewById<EditText>(R.id.usernameEditText)
        val passwordEditText = dialogView.findViewById<EditText>(R.id.passwordEditText)
        val loginDialogButton = dialogView.findViewById<Button>(R.id.loginDialogButton)
        val cancelDialogButton = dialogView.findViewById<Button>(R.id.cancelDialogButton)
        val errorTextView = dialogView.findViewById<TextView>(R.id.loginErrorTextView)
        
        val dialog = AlertDialog.Builder(requireContext())
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
                requireActivity().runOnUiThread {
                    if (success) {
                        dialog.dismiss()
                        updateAuthStatus(true, username)
                        Toast.makeText(requireContext(), getString(R.string.login_success), Toast.LENGTH_SHORT).show()
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
        val apiUrl = binding.apiUrlEditText.text.toString().trim()
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
                            .putBoolean("is_logged_in", true)
                            .apply()
                        
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
            .putBoolean("is_logged_in", false)
            .apply()
        
        updateAuthStatus(false, null)
        Toast.makeText(requireContext(), getString(R.string.logout_success), Toast.LENGTH_SHORT).show()
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        // Clean up callbacks
        if (_binding != null) {
            binding.apiUrlEditText.removeCallbacks(saveApiUrlRunnable)
        }
        _binding = null
    }
}
