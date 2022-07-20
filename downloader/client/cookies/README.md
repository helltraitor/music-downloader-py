## Music downloader cookies
This folder will contain all cookies that was set\updated during application
working. This allows to reuse cookies and to reduce the load on the servers,
also it helps to avoid captcha (because server already met application in
previous sessions). If you are using `Linux` operating system make sure that,
application have **enough permissions** to use this folder (or make pull request
with solution for this, because there is no plans for changing application
behavior for this case).

### Warning
Use ` downloader cookies delete --domain <domain>` for delete domain, **do not**
change any files - that may break application.

### Domains.json
File `domains.json` contains a mapping of `"domain": "filename"`, where `domain`
is a real string of the real domain (e.g. `"yandex.ru"`), the special `""` domain
means that cookie from `filename` will be applied to all sessions.

This is a typical `domains.json` scheme example:
```json
{
    "yandex.ru": "83c04328c2935e8aef7cdd3eb4395d04"
}
```

#### Note
Filename creates from unsafe md5 hash as hex-digest. This allows to not sanitize
filenames and save as is.
```Python
import hashlib


hashlib.md5("yandex.ru".encode("utf-8")).hexdigest()
```

### Cookie representation
Downloader keeps all cookies in their original view. `CookieJar` from `aiohttp`
consists of `SimpleCookie` from `http` that allows to safe keep them as pickled.

```Python
import pickle


# Example of loading
with open("83c04328c2935e8aef7cdd3eb4395d04", mode="rb") as file:
    cookie = pickle.loads(file.read())

# Example of saving
with open("83c04328c2935e8aef7cdd3eb4395d04", mode="wb") as file:
    file.write(pickle.dumps(cookie, protocol=5))
```
