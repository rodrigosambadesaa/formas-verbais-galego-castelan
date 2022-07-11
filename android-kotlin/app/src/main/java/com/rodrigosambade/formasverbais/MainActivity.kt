package com.rodrigosambade.formasverbais

import android.app.Activity
import android.os.Bundle
import android.text.Editable
import android.text.InputFilter
import android.text.TextWatcher
import android.view.View
import android.view.ViewGroup
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ListView
import android.widget.Spinner
import android.widget.TextView
import java.io.InputStreamReader
import java.util.concurrent.Executors

class MainActivity : Activity() {
    private val worker = Executors.newSingleThreadExecutor()
    private var corpus: Corpus? = null
    private var searchVersion = 0
    private lateinit var search: EditText
    private lateinit var mode: Spinner
    private lateinit var tense: Spinner
    private lateinit var person: Spinner
    private lateinit var status: TextView
    private lateinit var rows: ArrayAdapter<String>

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(16), dp(16), dp(16), dp(8))
        }
        root.addView(TextView(this).apply {
            text = "Formas verbais · Castelán ↔ Galego"
            textSize = 22f
            setPadding(0, 0, 0, dp(12))
        })
        search = EditText(this).apply {
            hint = "Infinitivo, forma conxugada, tempo ou persoa"
            isSingleLine = true
            filters = arrayOf(InputFilter.LengthFilter(120))
        }
        root.addView(search, LinearLayout.LayoutParams(-1, -2))

        mode = spinner(listOf("Formas conxugadas", "Pares de infinitivos"))
        root.addView(mode, LinearLayout.LayoutParams(-1, -2))
        tense = spinner(listOf("Todos os tempos"))
        root.addView(tense, LinearLayout.LayoutParams(-1, -2))
        person = spinner(listOf("Todas as persoas"))
        root.addView(person, LinearLayout.LayoutParams(-1, -2))
        status = TextView(this).apply {
            text = "Cargando corpus local…"
            setPadding(0, dp(10), 0, dp(8))
        }
        root.addView(status, LinearLayout.LayoutParams(-1, -2))
        rows = ArrayAdapter(this, android.R.layout.simple_list_item_1, ArrayList())
        root.addView(ListView(this).apply { adapter = rows },
            LinearLayout.LayoutParams(-1, 0, 1f))
        setContentView(root)

        search.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) = requestSearch()
            override fun afterTextChanged(s: Editable?) {}
        })
        val listener = object : AdapterView.OnItemSelectedListener {
            override fun onNothingSelected(parent: AdapterView<*>?) {}
            override fun onItemSelected(parent: AdapterView<*>?, view: View?, position: Int, id: Long) =
                requestSearch()
        }
        mode.onItemSelectedListener = listener
        tense.onItemSelectedListener = listener
        person.onItemSelectedListener = listener

        worker.execute {
            try {
                val loaded = Corpus.parse(
                    InputStreamReader(assets.open("verbos_relacionados.tsv"), Charsets.UTF_8),
                    InputStreamReader(assets.open("alineaciones_completas.tsv"), Charsets.UTF_8),
                )
                runOnUiThread {
                    if (isDestroyed) return@runOnUiThread
                    corpus = loaded
                    tense.adapter = spinnerAdapter(listOf("Todos os tempos") + loaded.tenses)
                    person.adapter = spinnerAdapter(listOf("Todas as persoas") + loaded.persons)
                    requestSearch()
                }
            } catch (e: Exception) {
                runOnUiThread {
                    if (!isDestroyed) {
                        status.text = "Erro ao abrir o corpus: " + (e.message ?: "erro descoñecido")
                    }
                }
            }
        }
    }

    private fun requestSearch() {
        val loaded = corpus ?: return
        val version = ++searchVersion
        val phrase = search.text.toString()
        val pairsMode = mode.selectedItemPosition == 1
        val chosenTense = if (tense.selectedItemPosition > 0) tense.selectedItem.toString() else null
        val chosenPerson = if (person.selectedItemPosition > 0) person.selectedItem.toString() else null
        tense.isEnabled = !pairsMode
        person.isEnabled = !pairsMode
        worker.execute {
            val results = if (pairsMode) {
                loaded.findPairs(phrase).map { "ES: " + it.es + "\nGL: " + it.gl }
            } else {
                loaded.findForms(phrase, chosenTense, chosenPerson).map {
                    "ES: " + it.es + "  ·  GL: " + it.gl +
                        "\n" + it.infinitiveEs + " ↔ " + it.infinitiveGl +
                        "  ·  " + it.tense + "  ·  " + it.person
                }
            }
            runOnUiThread {
                if (isDestroyed || version != searchVersion) return@runOnUiThread
                rows.clear()
                rows.addAll(results)
                rows.notifyDataSetChanged()
                val total = if (pairsMode) loaded.pairs.size else loaded.forms.size
                status.text = "$total rexistros dispoñibles · " +
                    results.size + " resultados amosados (máximo 250)"
            }
        }
    }

    private fun spinner(options: List<String>): Spinner = Spinner(this).apply {
        adapter = spinnerAdapter(options)
    }

    private fun spinnerAdapter(options: List<String>): ArrayAdapter<String> =
        ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, options)

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    override fun onDestroy() {
        searchVersion++
        worker.shutdownNow()
        super.onDestroy()
    }
}
