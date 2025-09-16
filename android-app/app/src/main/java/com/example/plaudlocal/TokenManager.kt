package com.example.plaudlocal

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import android.widget.Toast
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
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

class TokenManager(private val context: Context) {
    
    private val sharedPreferences: SharedPreferences = context.getSharedPreferences("plaud_settings", Context.MODE_PRIVATE)
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    companion object {
        private const val TAG = "TokenManager"
        private const val REFRESH_TOKEN_URL = "/auth/refresh"
    }
    
    /**
     * Проверяет, является ли ошибка связанной с истекшим токеном
     */
    fun isTokenExpiredError(response: Response): Boolean {
        return response.code == 401 || response.code == 403
    }
    
    /**
     * Обновляет токен асинхронно
     */
    suspend fun refreshToken(): Boolean = withContext(Dispatchers.IO) {
        val apiUrl = sharedPreferences.getString("api_url", "") ?: ""
        val currentToken = sharedPreferences.getString("auth_token", "") ?: ""
        val username = sharedPreferences.getString("username", "") ?: ""
        
        if (apiUrl.isEmpty() || currentToken.isEmpty() || username.isEmpty()) {
            return@withContext false
        }
        
        try {
            val request = Request.Builder()
                .url("$apiUrl$REFRESH_TOKEN_URL")
                .post(MultipartBody.Builder()
                    .setType(MultipartBody.FORM)
                    .addFormDataPart("username", username)
                    .build())
                .addHeader("Authorization", "Bearer $currentToken")
                .build()
            
            val response = client.newCall(request).execute()
            
            if (response.isSuccessful) {
                val responseBody = response.body?.string()
                val json = JSONObject(responseBody ?: "")
                val newToken = json.getString("access_token")
                
                // Сохраняем новый токен
                sharedPreferences.edit()
                    .putString("auth_token", newToken)
                    .apply()
                
                Log.d(TAG, "Token refreshed successfully")
                return@withContext true
            } else {
                Log.w(TAG, "Token refresh failed: ${response.code}")
                return@withContext false
            }
        } catch (e: Exception) {
            Log.e(TAG, "Token refresh error: ${e.message}")
            return@withContext false
        }
    }
    
    /**
     * Обрабатывает запрос с автоматическим обновлением токена при необходимости
     */
    suspend fun <T> executeWithTokenRefresh(
        requestBuilder: (String) -> Request,
        onSuccess: (Response) -> T,
        onFailure: (Exception) -> Unit
    ): T? {
        val apiUrl = sharedPreferences.getString("api_url", "") ?: ""
        var authToken = sharedPreferences.getString("auth_token", "") ?: ""
        
        if (apiUrl.isEmpty() || authToken.isEmpty()) {
            onFailure(IOException("No API URL or auth token"))
            return null
        }
        
        var attempt = 0
        var shouldRefresh = false
        
        while (attempt < 2) {
            try {
                val request = requestBuilder(authToken)
                val response = client.newCall(request).execute()
                
                if (response.isSuccessful) {
                    return onSuccess(response)
                } else if (isTokenExpiredError(response) && attempt == 0) {
                    // Пытаемся обновить токен
                    shouldRefresh = true
                    response.close()
                } else {
                    onFailure(IOException("Request failed: ${response.code}"))
                    return null
                }
            } catch (e: Exception) {
                onFailure(e)
                return null
            }
            
            if (shouldRefresh) {
                val refreshSuccess = refreshToken()
                if (refreshSuccess) {
                    authToken = sharedPreferences.getString("auth_token", "") ?: ""
                    attempt++
                    shouldRefresh = false
                } else {
                    onFailure(IOException("Token refresh failed"))
                    return null
                }
            } else {
                break
            }
        }
        
        onFailure(IOException("Max retries exceeded"))
        return null
    }
    
    /**
     * Упрощенный метод для выполнения запросов с автоматическим обновлением токена
     */
    fun executeWithTokenRefreshAsync(
        requestBuilder: (String) -> Request,
        onSuccess: (Response) -> Unit,
        onFailure: (Exception) -> Unit
    ) {
        val apiUrl = sharedPreferences.getString("api_url", "") ?: ""
        var authToken = sharedPreferences.getString("auth_token", "") ?: ""
        
        if (apiUrl.isEmpty() || authToken.isEmpty()) {
            onFailure(IOException("No API URL or auth token"))
            return
        }
        
        var attempt = 0
        
        fun executeRequest() {
            val request = requestBuilder(authToken)
            client.newCall(request).enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    onFailure(e)
                }
                
                override fun onResponse(call: Call, response: Response) {
                    if (response.isSuccessful) {
                        onSuccess(response)
                    } else if (isTokenExpiredError(response) && attempt == 0) {
                        attempt++
                        // Пытаемся обновить токен асинхронно
                        refreshTokenAsync { success ->
                            if (success) {
                                authToken = sharedPreferences.getString("auth_token", "") ?: ""
                                executeRequest()
                            } else {
                                onFailure(IOException("Token refresh failed"))
                            }
                        }
                    } else {
                        onFailure(IOException("Request failed: ${response.code}"))
                    }
                    response.close()
                }
            })
        }
        
        executeRequest()
    }
    
    /**
     * Асинхронное обновление токена
     */
    private fun refreshTokenAsync(callback: (Boolean) -> Unit) {
        val apiUrl = sharedPreferences.getString("api_url", "") ?: ""
        val currentToken = sharedPreferences.getString("auth_token", "") ?: ""
        val username = sharedPreferences.getString("username", "") ?: ""
        
        if (apiUrl.isEmpty() || currentToken.isEmpty() || username.isEmpty()) {
            callback(false)
            return
        }
        
        val request = Request.Builder()
            .url("$apiUrl/auth/refresh")
            .post(MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("username", username)
                .build())
            .addHeader("Authorization", "Bearer $currentToken")
            .build()
        
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                Log.e(TAG, "Token refresh failed: ${e.message}")
                callback(false)
            }
            
            override fun onResponse(call: Call, response: Response) {
                if (response.isSuccessful) {
                    try {
                        val responseBody = response.body?.string()
                        val json = JSONObject(responseBody ?: "")
                        val newToken = json.getString("access_token")
                        
                        sharedPreferences.edit()
                            .putString("auth_token", newToken)
                            .apply()
                        
                        Log.d(TAG, "Token refreshed successfully")
                        callback(true)
                    } catch (e: Exception) {
                        Log.e(TAG, "Token refresh parse error: ${e.message}")
                        callback(false)
                    }
                } else {
                    Log.w(TAG, "Token refresh failed: ${response.code}")
                    callback(false)
                }
                response.close()
            }
        })
    }
}