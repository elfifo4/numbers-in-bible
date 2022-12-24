package eladfinish.bible.data

import com.google.gson.GsonBuilder
import com.google.gson.JsonParser
import java.io.File

fun main() {
    val directory = "formatted"
    val number = "186400"
    val type = ".json"
    val bufferedReader = File("$directory/$number$type").bufferedReader(charset = Charsets.UTF_16)
    val inputString = bufferedReader.use { it.readText() }
    println(inputString)
    println(inputString.minified())
}

private fun String.minified(): String {
    val gson = GsonBuilder()
        .disableHtmlEscaping()
        .create()
    val element = JsonParser.parseString(this)
    return gson.toJson(element)
}