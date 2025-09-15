package com.example.plaudlocal

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.viewbinding.ViewBinding
import com.google.android.material.button.MaterialButton
import com.google.android.material.button.MaterialButtonToggleGroup
import com.google.android.material.textfield.TextInputEditText
import android.widget.TextView

class FragmentSettingsBinding private constructor(
    private val rootView: android.view.View
) : ViewBinding {
    
    override fun getRoot(): android.view.View = rootView
    
    val loginButton: MaterialButton = rootView.findViewById(R.id.loginButton)
    val saveApiUrlButton: MaterialButton = rootView.findViewById(R.id.saveApiUrlButton)
    val lightThemeButton: MaterialButton = rootView.findViewById(R.id.lightThemeButton)
    val darkThemeButton: MaterialButton = rootView.findViewById(R.id.darkThemeButton)
    val autoThemeButton: MaterialButton = rootView.findViewById(R.id.autoThemeButton)
    val russianLanguageButton: MaterialButton = rootView.findViewById(R.id.russianLanguageButton)
    val englishLanguageButton: MaterialButton = rootView.findViewById(R.id.englishLanguageButton)
    
    val authStatusTextView: TextView = rootView.findViewById(R.id.authStatusTextView)
    val versionTextView: TextView = rootView.findViewById(R.id.versionTextView)
    
    val apiUrlEditText: TextInputEditText = rootView.findViewById(R.id.apiUrlEditText)
    
    val themeToggleGroup: MaterialButtonToggleGroup = rootView.findViewById(R.id.themeToggleGroup)
    val languageToggleGroup: MaterialButtonToggleGroup = rootView.findViewById(R.id.languageToggleGroup)
    
    companion object {
        fun inflate(inflater: LayoutInflater, parent: ViewGroup?, attachToParent: Boolean): FragmentSettingsBinding {
            val rootView = inflater.inflate(R.layout.fragment_settings, parent, attachToParent)
            return FragmentSettingsBinding(rootView)
        }
    }
}
