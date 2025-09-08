package com.plaud.local

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class PlaudLocalApplication : Application() {
    
    override fun onCreate() {
        super.onCreate()
        // Здесь можно добавить инициализацию библиотек, если необходимо
    }
}