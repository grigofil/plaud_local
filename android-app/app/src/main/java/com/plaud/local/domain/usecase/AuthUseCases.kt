package com.plaud.local.domain.usecase

import com.plaud.local.domain.model.AuthData
import com.plaud.local.domain.model.AuthResponse
import com.plaud.local.domain.repository.AuthRepository
import javax.inject.Inject

/**
 * Use case для авторизации пользователя
 */
class LoginUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {
    suspend operator fun invoke(authData: AuthData): Result<AuthResponse> {
        return authRepository.login(authData)
    }
}

/**
 * Use case для проверки валидности токена
 */
class ValidateTokenUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {
    suspend operator fun invoke(token: String): Boolean {
        return authRepository.validateToken(token)
    }
}

/**
 * Use case для выхода из системы
 */
class LogoutUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {
    suspend operator fun invoke() {
        authRepository.logout()
    }
}

/**
 * Use case для сохранения данных авторизации
 */
class SaveAuthDataUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {
    suspend operator fun invoke(authData: AuthData, token: String) {
        authRepository.saveAuthData(authData, token)
    }
}

/**
 * Use case для получения сохраненных данных авторизации
 */
class GetSavedAuthDataUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {
    suspend operator fun invoke(): AuthData? {
        return authRepository.getSavedAuthData()
    }
}

/**
 * Use case для получения сохраненного токена
 */
class GetSavedTokenUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {
    suspend operator fun invoke(): String? {
        return authRepository.getSavedToken()
    }
}