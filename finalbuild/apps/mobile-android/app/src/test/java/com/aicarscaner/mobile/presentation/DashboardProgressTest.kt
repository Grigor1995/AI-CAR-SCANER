package com.aicarscaner.mobile.presentation

import com.aicarscaner.mobile.data.api.*
import org.junit.Assert.assertEquals
import org.junit.Test

class DashboardProgressTest {
    @Test fun progressCountsOnlyCurrentRecommendations() {
        val session=DiagnosticSessionDto(session_id="s1",state="TESTING",
            recommendations=listOf(RecommendationDto(id="next",title="Next test",purpose="Check",priority=.5)),
            test_results=listOf(TestResultDto("done","PASS"),TestResultDto("reopened","FAIL"),TestResultDto("reopened","INCOMPLETE")))
        assertEquals(0 to 1,latestTestProgress(session))
        assertEquals(0 to 1,latestTestProgress(session.copy(test_results=session.test_results+TestResultDto("reopened","PASS"))))
    }
    @Test fun emptySessionHasNoInventedProgress(){
        assertEquals(0 to 0,latestTestProgress(DiagnosticSessionDto("s1","CREATED")))
    }
}
