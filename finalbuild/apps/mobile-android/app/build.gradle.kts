plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    // Global asset source of truth lives under finalbuild/assets.
    // Keep the Android mipmap copy synchronized before every build.
    val globalAppIcon = rootProject.projectDir
        .resolve("../../assets/AI-Car-Scanner.webp")
        .normalize()
    val androidAppIcon = projectDir.resolve("src/main/res/mipmap/ic_launcher.webp")

    namespace = "com.aicarscaner.mobile"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.aicarscaner.mobile"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

tasks.named("preBuild").configure {
    doFirst {
        check(globalAppIcon.isFile()) {
            "Missing global app icon: " + globalAppIcon.absolutePath
        }
        globalAppIcon.copyTo(androidAppIcon, overwrite = true)
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.17.0")
    implementation("androidx.activity:activity-compose:1.10.1")
    implementation("androidx.compose.ui:ui:1.9.2")
    implementation("androidx.compose.ui:ui-tooling-preview:1.9.2")
    implementation("androidx.compose.material3:material3:1.3.2")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.9.3")
    implementation("androidx.navigation:navigation-compose:2.9.3")
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-gson:2.11.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.10.2")
    debugImplementation("androidx.compose.ui:ui-tooling:1.9.2")
}
