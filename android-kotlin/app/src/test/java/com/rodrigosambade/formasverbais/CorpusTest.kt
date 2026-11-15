package com.rodrigosambade.formasverbais

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.StringReader

class CorpusTest {
    private val pairs = "hablar\tfalar\tV\ncomer\tcomer\tV\nhablar\tfalar\tV\nmalformed\n"
    private val alignments =
        "orphan\torfo\tPI-PI\t1PS\n" +
        "hablar\tfalar\tFN-FN\tInf\n" +
        "hablo\tfalo\tPI-PI\t1PS\n" +
        "hablé\tfalei\tEI-EI\t1PS\n" +
        "comer\tcomer\tFN-FN\tInf\n" +
        "como\tcomo\tPI-PI\t1PS\n" +
        "invalid\n"

    private fun corpus() = Corpus.parse(StringReader(pairs), StringReader(alignments))

    @Test fun deduplicatesPairsAndSkipsMalformedLines() {
        assertEquals(2, corpus().pairs.size)
        assertEquals(5, corpus().forms.size)
    }

    @Test fun associatesFormsWithTheirCorrectInfinitive() {
        assertEquals("hablar", corpus().forms[1].infinitiveEs)
        assertEquals("comer", corpus().forms.last().infinitiveGl)
    }

    @Test fun searchesBothLanguagesIgnoringAccentsAndCase() {
        assertEquals("falei", corpus().findForms("FALÉI").single().gl)
        assertEquals("hablé", corpus().findForms("  HABLÉ ").single().es)
        assertEquals(1, corpus().findPairs("  FALAR ").size)
    }

    @Test fun filtersByTenseAndPerson() {
        val matches = corpus().findForms("hab", "PI-PI", "1PS")
        assertEquals(listOf("hablo"), matches.map { it.es })
        assertTrue(corpus().findForms("hab", "PI-PI", "2PP").isEmpty())
    }

    @Test fun capsResultCounts() {
        assertEquals(2, corpus().findForms("", limit = 2).size)
        assertEquals(1, corpus().findPairs("", limit = 1).size)
    }
}
