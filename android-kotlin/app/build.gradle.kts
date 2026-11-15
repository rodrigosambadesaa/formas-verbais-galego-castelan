plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.rodrigosambade.formasverbais"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.rodrigosambade.formasverbais"
        minSdk = 24
        targetSdk = 35
        versionCode = 1
        versionName = "1.0.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }

    testOptions {
        unitTests.isReturnDefaultValues = true
    }
}

dependencies {
    testImplementation("junit:junit:4.13.2")
}

// Keep the large canonical corpus in its existing repository location.
// Gradle copies it into generated build assets, not into a second tracked file.
val corpusRoot = rootProject.projectDir.parentFile
val pairsFile = corpusRoot.resolve("web-angular/src/assets/data/verbos_relacionados.tsv")
val alignmentsFile = corpusRoot.resolve("formas_verbais_es_gl_completo.txt")
val generatedAssets = layout.buildDirectory.dir("generated/corpus-assets")
val prepareCorpusAssets = tasks.register<Copy>("prepareCorpusAssets") {
    from(pairsFile)
    from(alignmentsFile) { rename { "alineaciones_completas.tsv" } }
    into(generatedAssets)
    doFirst {
        require(pairsFile.isFile) { "Missing canonical pair dataset: $pairsFile" }
        require(alignmentsFile.isFile) { "Missing canonical alignment corpus: $alignmentsFile" }
    }
}
android.sourceSets.getByName("main").assets.srcDir(generatedAssets)
tasks.configureEach {
    if (name.startsWith("merge") && name.endsWith("Assets")) {
        dependsOn(prepareCorpusAssets)
    }
}
