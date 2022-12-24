package eladfinish.bible.test

import org.junit.Test

import org.junit.Assert.*
import java.io.File

/**
 * Example local unit test, which will execute on the development machine (host).
 *
 * See [testing documentation](http://d.android.com/tools/testing).
 */
//class ExampleUnitTest {
//    @Test
//    fun addition_isCorrect() {
//        assertEquals(4, 2 + 2)
//    }
//}

fun main(){
    println("elad_finish")
    val directory = "formatted"
    val number = "151450"
    val type = ".json"
    val bufferedReader = File("$directory/$number$type").bufferedReader(charset = Charsets.UTF_16)
    val inputString = bufferedReader.use { it.readText() }
    println(inputString)
}
