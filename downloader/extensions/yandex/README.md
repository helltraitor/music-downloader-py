## Music downloader - Yandex domain
Yandex domain urls from following sources: Track, Album, Artist, Playlist, Label.
This domain requires `Session_id` cookie from `yandex.ru` site (it can be found
in application tab in development tools of user browser).

### Supported options:
`HQ`, `HighQuality` - Forces to use a high quality tracks and covers.
                  In case if user have no plus subscribing, may entail
                  errors.

Use flag `-o` (or `--option`) for enabling a specified option.

### Examples:
    downloader fetch <url> -d %USERPROFILE%/Downloads -o HighQuality
    downloader fetch <url> -d %USERPROFILE%/Downloads -o HQ

### Warning
**Code in this part of application not well documented and represented only as an example.**
