package com.aicarscaner.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.aicarscaner.mobile.data.api.ApiClient

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        ApiClient.loadURL(applicationContext)
        setContent {
            androidx.compose.material3.MaterialTheme(colorScheme=com.aicarscaner.mobile.presentation.AutomotiveDarkColors) {
                com.aicarscaner.mobile.presentation.BusinessWorkspace(
                    onClose={finish()},
                    fixedWorkspace=BuildConfig.APP_WORKSPACE
                )
            }
        }
    }
}
