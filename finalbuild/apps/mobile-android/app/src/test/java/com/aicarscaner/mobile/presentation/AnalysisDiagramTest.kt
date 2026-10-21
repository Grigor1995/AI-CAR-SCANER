package com.aicarscaner.mobile.presentation

import com.aicarscaner.mobile.data.api.TestResultDto
import org.junit.Assert.*
import org.junit.Test

class AnalysisDiagramTest {
    @Test fun onlyValidServerScoresBecomeDiagramValues() {
        assertEquals(.65, diagramEvidenceScore("possible:0.65")!!, .0001)
        assertEquals(0.0, diagramEvidenceScore("rejected:0")!!, .0001)
        assertEquals(1.0, diagramEvidenceScore("supported_by_test:1")!!, .0001)
        listOf("possible", "possible:", "possible:NaN", "possible:Infinity", "possible:-0.1", "possible:1.1", "possible:0.5:0.7").forEach {
            assertNull(it, diagramEvidenceScore(it))
        }
    }
    @Test fun latestOutcomeReplacesPreviousAttemptInsteadOfDoubleCounting() {
        val counts = diagramResultCounts(listOf(
            TestResultDto("t1", "FAIL"), TestResultDto("t2", "INCOMPLETE"),
            TestResultDto("t1", "PASS"), TestResultDto("t3", "FAIL")))
        assertEquals(mapOf("PASS" to 1, "FAIL" to 1, "INCOMPLETE" to 1), counts)
        assertEquals(mapOf("PASS" to 0, "FAIL" to 0, "INCOMPLETE" to 0), diagramResultCounts(emptyList()))
    }
}
