import java.io.File

fun main() {
    println("elad_finish")
    val directory = "formatted"
    val number = "151450"
    val type = ".json"
    val bufferedReader = File("$directory/$number$type").bufferedReader(charset = Charsets.UTF_16)
    val inputString = bufferedReader.use { it.readText() }
    println(inputString)
}

fun aa(){


//    val string = Json.encodeToString(data)


//    val gson = Gson()

}

