package com.example.plaudlocal

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.viewpager2.widget.ViewPager2
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.tabs.TabLayout
import com.google.android.material.tabs.TabLayoutMediator

class ResultsActivity : AppCompatActivity() {

    private lateinit var toolbar: MaterialToolbar
    private lateinit var tabLayout: TabLayout
    private lateinit var viewPager: ViewPager2
    private lateinit var resultsAdapter: ResultsPagerAdapter
    private var formattedResult: FormattedResult? = null
    private var jobId: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_results)

        // Get data from intent
        jobId = intent.getStringExtra("job_id")
        formattedResult = intent.getParcelableExtra("formatted_result")

        if (formattedResult == null) {
            finish()
            return
        }

        // Initialize views
        toolbar = findViewById(R.id.toolbar)
        tabLayout = findViewById(R.id.tabLayout)
        viewPager = findViewById(R.id.viewPager)

        // Setup toolbar
        setSupportActionBar(toolbar)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = "Результаты ${jobId ?: ""}"

        // Setup ViewPager
        resultsAdapter = ResultsPagerAdapter(this, formattedResult!!)
        viewPager.adapter = resultsAdapter

        // Setup TabLayout
        TabLayoutMediator(tabLayout, viewPager) { tab, position ->
            tab.text = when (position) {
                0 -> "Транскрипт"
                1 -> "Саммари"
                2 -> "Ключевые моменты"
                3 -> "Задачи"
                4 -> "Риски"
                5 -> "Сегменты"
                else -> "Дополнительно"
            }
        }.attach()
    }

    override fun onCreateOptionsMenu(menu: Menu?): Boolean {
        menuInflater.inflate(R.menu.results_menu, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            android.R.id.home -> {
                finish()
                true
            }
            R.id.action_copy_all -> {
                copyAllResults()
                true
            }
            R.id.action_share -> {
                shareResults()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }

    private fun copyAllResults() {
        formattedResult?.let { result ->
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = ClipData.newPlainText("Results", ResultParser().getCopyableText(result))
            clipboard.setPrimaryClip(clip)
            android.widget.Toast.makeText(this, "Результаты скопированы", android.widget.Toast.LENGTH_SHORT).show()
        }
    }

    private fun shareResults() {
        formattedResult?.let { result ->
            val shareIntent = android.content.Intent().apply {
                action = android.content.Intent.ACTION_SEND
                putExtra(android.content.Intent.EXTRA_TEXT, ResultParser().getCopyableText(result))
                type = "text/plain"
            }
            startActivity(android.content.Intent.createChooser(shareIntent, "Поделиться результатами"))
        }
    }
}
