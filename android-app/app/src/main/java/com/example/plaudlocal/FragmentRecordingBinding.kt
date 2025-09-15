package com.example.plaudlocal

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.viewbinding.ViewBinding
import com.google.android.material.button.MaterialButton
import com.google.android.material.button.MaterialButtonToggleGroup
import com.google.android.material.progressindicator.CircularProgressIndicator
import com.google.android.material.progressindicator.LinearProgressIndicator
import com.google.android.material.tabs.TabLayout
import com.google.android.material.textfield.TextInputEditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import androidx.viewpager2.widget.ViewPager2

class FragmentRecordingBinding private constructor(
    private val rootView: android.view.View
) : ViewBinding {
    
    override fun getRoot(): android.view.View = rootView
    
    val startRecordingButton: MaterialButton = rootView.findViewById(R.id.startRecordingButton)
    val stopRecordingButton: MaterialButton = rootView.findViewById(R.id.stopRecordingButton)
    val selectFileButton: MaterialButton = rootView.findViewById(R.id.selectFileButton)
    val uploadButton: MaterialButton = rootView.findViewById(R.id.uploadButton)
    val copyResultsButton: MaterialButton = rootView.findViewById(R.id.copyResultsButton)
    val clearResultsButton: MaterialButton = rootView.findViewById(R.id.clearResultsButton)
    val viewDetailsButton: MaterialButton = rootView.findViewById(R.id.viewDetailsButton)
    
    val recordingStatusTextView: TextView = rootView.findViewById(R.id.recordingStatusTextView)
    val recordingTimeTextView: TextView = rootView.findViewById(R.id.recordingTimeTextView)
    val selectedFileTextView: TextView = rootView.findViewById(R.id.selectedFileTextView)
    val statusTextView: TextView = rootView.findViewById(R.id.statusTextView)
    val resultTextView: TextView = rootView.findViewById(R.id.resultTextView)
    val resultsProgressText: TextView = rootView.findViewById(R.id.resultsProgressText)
    
    val progressBar: CircularProgressIndicator = rootView.findViewById(R.id.progressBar)
    val levelBar: LinearProgressIndicator = rootView.findViewById(R.id.levelBar)
    val levelNum: TextView = rootView.findViewById(R.id.levelNum)
    
    val levelWrap: LinearLayout = rootView.findViewById(R.id.levelWrap)
    val resultsProgressLayout: LinearLayout = rootView.findViewById(R.id.resultsProgressLayout)
    val resultsTabLayout: TabLayout = rootView.findViewById(R.id.resultsTabLayout)
    val resultsViewPager: ViewPager2 = rootView.findViewById(R.id.resultsViewPager)
    val simpleResultsScrollView: ScrollView = rootView.findViewById(R.id.simpleResultsScrollView)
    
    companion object {
        fun inflate(inflater: LayoutInflater, parent: ViewGroup?, attachToParent: Boolean): FragmentRecordingBinding {
            val rootView = inflater.inflate(R.layout.fragment_recording, parent, attachToParent)
            return FragmentRecordingBinding(rootView)
        }
    }
}
