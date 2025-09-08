package com.plaud.local.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.plaud.local.domain.model.AuthData
import com.plaud.local.domain.model.AuthState
import com.plaud.local.domain.usecase.LoginUseCase
import com.plaud.local.domain.usecase.GetSavedAuthDataUseCase
import com.plaud.local.domain.usecase.GetSavedTokenUseCase
import com.plaud.local.domain.usecase.ValidateTokenUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val loginUseCase: LoginUseCase,
    private val validateTokenUseCase: ValidateTokenUseCase,
    private val getSavedAuthDataUseCase: GetSavedAuthDataUseCase,
    private val getSavedTokenUseCase: GetSavedTokenUseCase
) : ViewModel() {

    private val _authState = MutableStateFlow<AuthState>(AuthState.Idle)
    val authState: StateFlow<AuthState> = _authState.asStateFlow()

    private val _username = MutableStateFlow("")
    val username: StateFlow<String> = _username.asStateFlow()

    private val _password = MutableStateFlow("")
    val password: StateFlow<String> = _password.asStateFlow()

    private val _serverUrl = MutableStateFlow("http://10.0.2.2:8000")
    val serverUrl: StateFlow<String> = _serverUrl.asStateFlow()

    private val _rememberMe = MutableStateFlow(true)
    val rememberMe: StateFlow<Boolean> = _rememberMe.asStateFlow()

    init {
        loadSavedCredentials()
    }

    fun setUsername(username: String) {
        _username.value = username
    }

    fun setPassword(password: String) {
        _password.value = password
    }

    fun setServerUrl(serverUrl: String) {
        _serverUrl.value = serverUrl
    }

    fun setRememberMe(remember: Boolean) {
        _rememberMe.value = remember
    }

    fun login() {
        if (_username.value.isEmpty() || _password.value.isEmpty() || _serverUrl.value.isEmpty()) {
            _authState.value = AuthState.Error("Please fill all fields")
            return
        }

        _authState.value = AuthState.Loading

        viewModelScope.launch {
            val authData = AuthData(
                username = _username.value,
                password = _password.value,
                serverUrl = _serverUrl.value
            )

            val result = loginUseCase(authData)
            result.onSuccess { response ->
                if (response.success && response.token != null) {
                    _authState.value = AuthState.Success(response.token, response.userId ?: "")
                } else {
                    _authState.value = AuthState.Error(response.message ?: "Login failed")
                }
            }.onFailure { exception ->
                _authState.value = AuthState.Error(exception.message ?: "Login failed")
            }
        }
    }

    fun validateSavedToken() {
        viewModelScope.launch {
            val token = getSavedTokenUseCase()
            if (token != null && validateTokenUseCase(token)) {
                _authState.value = AuthState.Success(token, "")
            } else {
                _authState.value = AuthState.Idle
            }
        }
    }

    private fun loadSavedCredentials() {
        viewModelScope.launch {
            val savedAuthData = getSavedAuthDataUseCase()
            savedAuthData?.let {
                _username.value = it.username
                _serverUrl.value = it.serverUrl
                // Пароль не сохраняем для безопасности
            }
        }
    }

    fun resetState() {
        _authState.value = AuthState.Idle
    }
}