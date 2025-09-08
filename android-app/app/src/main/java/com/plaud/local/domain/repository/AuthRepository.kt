package com.plaud.local.domain.repository

import com.plaud.local.domain.model.AuthData
import com.plaud.local.domain.model.AuthResponse

/**
 * Репозиторий для работы с авторизацией
 */
interface AuthRepository {
    /**
     * Авторизация пользователя через логин и пароль
     */
    suspend fun login(authData: AuthData): Result<AuthResponse>
    
    /**
     * Проверка валидности текущего токена
     */
    suspend fun validateToken(token: String): Boolean
    
    /**
     * Выход из системы
     */
    suspend fun logout()
    
    /**
     * Сохранение данных авторизации
     */
    suspend fun saveAuthData(authData: AuthData, token: String)
    
    /**
     * Получение сохраненных данных авторизации
     */
    suspend fun getSavedAuthData(): AuthData?
    
    /**
     * Получение сохраненного токена
     */
    suspend fun getSavedToken(): String?
}