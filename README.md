# numbers-in-bible

https://elfifo4.github.io/numbers-in-bible/

This repository contains json files of all the numbers in the Bible and their occurrences within the verses, where the words forming the number are enclosed by bold tags.<br/>
(in Hebrew language)<br/>
If you find any mistake, please open up a new issue.<br/>
Thanks

## Usage

```java

public class RetrofitClientInstanceSearch {

    private static Retrofit retrofit;
    private static final String BASE_URL = "https://raw.githubusercontent.com";

    public static Retrofit getRetrofitInstance() {
        if (retrofit == null) {
            retrofit = new retrofit2.Retrofit.Builder()
                    .baseUrl(BASE_URL)
                    .addConverterFactory(GsonConverterFactory.create())
                    .build();
        }
        return retrofit;
    }
}

public interface GithubServiceApi {
    @GET("/elfifo4/numbers-in-bible/master/minified/{num}.json")
    Call<ResponseBody> getJson(@Path("num") int num);
}

private void handleNumberSearching(int number) {
    Retrofit retrofitInstance = RetrofitClientInstanceSearch.getRetrofitInstance();
    GithubServiceApi service = retrofitInstance.create(GithubServiceApi.class);
    Call<ResponseBody> call = service.getJson(number);

        call.enqueue(new Callback<ResponseBody>() {
            @Override
            public void onResponse(@NotNull Call<ResponseBody> call, @NotNull Response<ResponseBody> response) {
                try {
                    String body = response.body().string();
                    System.out.println(body);
                } catch (JSONException e) {
                    e.printStackTrace();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }

            @Override
            public void onFailure(@NotNull Call<ResponseBody> call, @NotNull Throwable t) {
                System.err.println(t.toString());
            }
        });

}

/*
example:
handleNumberSearching(777)
get data from:
https://raw.githubusercontent.com/elfifo4/numbers-in-bible/master/minified/777.json
and print:
{"times":1,"verses":[{"b":"בראשית","c":"ה","t":"וַֽיְהִי֙ כׇּל יְמֵי לֶ֔מֶךְ <b>שֶׁ֤בַע<\/b> <b>וְשִׁבְעִים֙<\/b> שָׁנָ֔ה <b>וּשְׁבַ֥ע<\/b> <b>מֵאֹ֖ות<\/b> שָׁנָ֑ה וַיָּמֹֽת","v":"לא"}]}
 */

```


## License

```
Copyright 2019 Elad Finish

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
