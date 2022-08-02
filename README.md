# Music downloader
Music downloader is a package for downloading and managing music on personal device.

This project aims to be flexible (extendable) and user-friendly (simple for use).

## Features
### About
About command allows fetching information about entire application or some concrete domain.

Example:
    downloader about yandex

### Cookies
Cookies command allows to set, get or delete cookies, that is important for fetcher.

Note that some values or keys may not be set properly in the shell. You can use `""`
for wrapping keys and values to fix it.

Example:
    downloader cookies set yandex.ru Session_id "value_from_cookies"

### Fetch
This is all about. Fetch allows to download required resource from domain.

Example:
    downloader fetch https://music.yandex.ru/artist/1480281 -d %USERPROFILE%/Downloads

For updating, you can use `-c ignore`. That allows to skip tracks with the same names.
And there is the problem. Naming. It is easier to redownload all library instead of updating.
(When you have previous library. But if you fetch tracks via downloader, you can just use flag
above.)

I strongly believe that in yandex domain tracks will have same principles of naming that will
allow simple updating of tracks.

## Contributing
It's open project, just make PR.
If you have any proposals, just create an issue.
