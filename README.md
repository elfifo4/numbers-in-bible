# numbers-in-bible

קובץ JSON עם כל המספרים בתנ"ך ומופעיהם בתוך הפסוקים


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


//
private void handleNumberSearching(int number) {
    Retrofit retrofitInstance = RetrofitClientInstanceSearch.getRetrofitInstance();
    GithubServiceApi service = retrofitInstance.create(GithubServiceApi.class);
    Call<ResponseBody> call = service.getJson(number);

    ...

}
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