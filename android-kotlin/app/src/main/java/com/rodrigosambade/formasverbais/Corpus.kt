package com.rodrigosambade.formasverbais

import java.io.Reader
import java.text.Normalizer
import java.util.Locale

data class VerbPair(val es: String, val gl: String, val searchText: String)

data class VerbForm(
    val es: String,
    val gl: String,
    val tense: String,
    val person: String,
    val infinitiveEs: String,
    val infinitiveGl: String,
    val searchText: String,
)

/** Parses the same ES/GL, tense and person TSV conventions as the existing clients. */
class Corpus private constructor(
    val pairs: List<VerbPair>,
    val forms: List<VerbForm>,
) {
    val tenses: List<String> = forms.map { it.tense }.distinct().sorted()
    val persons: List<String> = forms.map { it.person }.distinct().sorted()

    fun findPairs(query: String, limit: Int = 250): List<VerbPair> {
        val terms = terms(query)
        return pairs.asSequence()
            .filter { item -> terms.all { item.searchText.contains(it) } }
            .take(limit.coerceIn(1, 500))
            .toList()
    }

    fun findForms(
        query: String,
        tense: String? = null,
        person: String? = null,
        limit: Int = 250,
    ): List<VerbForm> {
        val searchTerms = terms(query)
        return forms.asSequence()
            .filter { item ->
                (tense == null || item.tense == tense) &&
                    (person == null || item.person == person) &&
                    searchTerms.all { item.searchText.contains(it) }
            }
            .take(limit.coerceIn(1, 500))
            .toList()
    }

    companion object {
        private val marks = Regex("\\p{M}+")
        private val spaces = Regex("\\s+")

        fun normalized(text: String): String =
            marks.replace(Normalizer.normalize(text, Normalizer.Form.NFD), "")
                .lowercase(Locale.ROOT)
                .replace(spaces, " ")
                .trim()

        private fun terms(query: String): List<String> =
            normalized(query.take(120)).split(' ').filter(String::isNotEmpty)

        fun parse(pairsReader: Reader, formsReader: Reader): Corpus {
            val pairs = ArrayList<VerbPair>()
            val forms = ArrayList<VerbForm>()
            val seenPairs = HashSet<String>()

            pairsReader.buffered().useLines { lines ->
                lines.forEach { line ->
                    val cols = line.split('\t')
                    if (cols.size < 2) return@forEach
                    val es = cols[0].trim()
                    val gl = cols[1].trim()
                    if (es.isEmpty() || gl.isEmpty()) return@forEach
                    val key = normalized(es) + "|" + normalized(gl)
                    if (seenPairs.add(key)) {
                        pairs.add(VerbPair(es, gl, normalized("$es $gl")))
                    }
                }
            }

            var infinitiveEs = ""
            var infinitiveGl = ""
            formsReader.buffered().useLines { lines ->
                lines.forEach { line ->
                    val cols = line.split('\t')
                    if (cols.size < 4) return@forEach
                    val es = cols[0].trim()
                    val gl = cols[1].trim()
                    val tense = cols[2].trim()
                    val person = cols[3].trim()
                    if (listOf(es, gl, tense, person).any(String::isEmpty)) return@forEach
                    if (tense == "FN-FN" && person == "Inf") {
                        infinitiveEs = es
                        infinitiveGl = gl
                    }
                    // Records before a group marker cannot be assigned reliably.
                    if (infinitiveEs.isEmpty() || infinitiveGl.isEmpty()) return@forEach
                    forms.add(
                        VerbForm(
                            es, gl, tense, person, infinitiveEs, infinitiveGl,
                            normalized("$es $gl $tense $person $infinitiveEs $infinitiveGl"),
                        )
                    )
                }
            }
            return Corpus(pairs, forms)
        }
    }
}
