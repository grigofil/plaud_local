package com.example.plaudlocal

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.viewbinding.ViewBinding
import com.google.android.material.button.MaterialButton
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

class FragmentHistoryBinding private constructor(
    private val rootView: android.view.View
) : ViewBinding {
    
    override fun getRoot(): android.view.View = rootView
    
    val loadHistoryButton: MaterialButton = rootView.findViewById(R.id.loadHistoryButton)
    val historyRecyclerView: RecyclerView = rootView.findViewById(R.id.historyRecyclerView)
    val noHistoryTextView: TextView = rootView.findViewById(R.id.noHistoryTextView)
    
    companion object {
        fun inflate(inflater: LayoutInflater, parent: ViewGroup?, attachToParent: Boolean): FragmentHistoryBinding {
            val rootView = inflater.inflate(R.layout.fragment_history, parent, attachToParent)
            return FragmentHistoryBinding(rootView)
        }
    }
}
