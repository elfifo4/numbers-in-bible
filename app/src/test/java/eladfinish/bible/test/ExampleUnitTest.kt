package eladfinish.bible.test

import com.google.gson.GsonBuilder
import com.google.gson.JsonParser
import java.io.File

fun main() {
    val directory = "formatted"
    val number = "151450"
    val type = ".json"
    val bufferedReader = File("$directory/$number$type").bufferedReader(charset = Charsets.UTF_16)
    val inputString = bufferedReader.use { it.readText() }
    println(inputString)
    println(minify(inputString))
}

private fun minify(json: String): String {
    val gson = GsonBuilder()
        .disableHtmlEscaping()
        .create()
    val element = JsonParser.parseString(json)
    return gson.toJson(element)
}