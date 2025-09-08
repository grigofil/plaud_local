package com.plaud.local.domain.model

/**
 * Модель данных для авторизации через логин и пароль
 */
data class AuthData(
    val username: String,
    val password: String,
    val serverUrl: String
)

/**
 * Модель ответа авторизации
 */
data class AuthResponse(
    val token: String? = null,
    val userId: String? = null,
    val message: String? = null,
    val success: Boolean = false
)

/**
 * Модель состояния авторизации
 */
sealed class AuthState {
    object Idle : AuthState()
    object Loading : AuthState()
    data class Success(val token: String, val userId: String) : AuthState()
    data class Error(val message: String) : AuthState()
}