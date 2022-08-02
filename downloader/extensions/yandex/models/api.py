# Copyright (c) 2022 Helltraitor <helltraitor@hotmail.com>
#
# This file is under MIT License (see full license text in music-downloader-py/LICENSE file)
import json
import logging
import pathlib
import time

from downloader.requests import PartialRequestBuilder, PartialSection


Logger = logging.getLogger(__file__)

with open(pathlib.Path(__file__).parent / "headers.json", mode="r") as file:
    HEADERS = json.loads(file.read())

if not isinstance(HEADERS, dict):
    Logger.error("Headers must be dict of string to string, not %s", type(HEADERS))
    raise TypeError(f"Headers must be dict of string to string, not {type(HEADERS)}")


ALBUM_INFO_REQUEST = (
    PartialRequestBuilder("GET")
    .with_url("https://music.yandex.ru/handlers/album.jsx")
    .with_section("headers", PartialSection(filled=HEADERS))
    .with_section("params", PartialSection(automatic={"ncrnd": lambda: str(int(time.time()))},
                                           filled={
                                               "external-domain": "music.yandex.ru",
                                               "lang": "ru",
                                               "overembed": "false"
                                           },
                                           required={"album"}))
    .build())

ARTIST_INFO_REQUEST = (
    PartialRequestBuilder("GET")
    .with_url("https://music.yandex.ru/handlers/artist.jsx")
    .with_section("headers", PartialSection(filled=HEADERS))
    .with_section("params", PartialSection(automatic={"ncrnd": lambda: str(int(time.time()))},
                                           filled={
                                               "external-domain": "music.yandex.ru",
                                               "lang": "ru",
                                               "overembed": "false",
                                               "what": "albums"
                                           },
                                           required={"artist"}))
    .build())

LABEL_INFO_REQUEST = (
    PartialRequestBuilder("GET")
    .with_url("https://music.yandex.ru/handlers/label.jsx")
    .with_section("headers", PartialSection(filled=HEADERS))
    .with_section("params", PartialSection(automatic={"ncrnd": lambda: str(int(time.time()))},
                                           filled={
                                               "external-domain": "music.yandex.ru",
                                               "lang": "ru",
                                               "overembed": "false",
                                               "what": "albums",
                                               "sort": "year",
                                               "page": ""
                                           },
                                           required={"id"}))
    .build())

PLAYLIST_INFO_REQUEST = (
    PartialRequestBuilder("GET")
    .with_url("https://music.yandex.ru/handlers/playlist.jsx")
    .with_section("headers", PartialSection(filled=HEADERS))
    .with_section("params", PartialSection(automatic={"ncrnd": lambda: str(int(time.time()))},
                                           filled={
                                               "external-domain": "music.yandex.ru",
                                               "lang": "ru",
                                               "overembed": "false"
                                           },
                                           required={"kinds", "owner"}))
    .build())

TRACK_COVER_REQUEST = (
    PartialRequestBuilder("GET")
    .with_url("https://{src}", PartialSection(required={"src"}))
    .with_section("headers", PartialSection(filled=HEADERS))
    .build())

TRACK_DOWN_REQUEST = (
    PartialRequestBuilder("GET")
    .with_url("https://{src}", PartialSection(required={"src"}))
    .with_section("headers", PartialSection(filled=HEADERS))
    .build())

TRACK_FILE_REQUEST = (
    PartialRequestBuilder("GET")
    .with_url("https://{host}/get-mp3/{hash}/{ts}/{path}",
              PartialSection(required={"host", "hash", "ts", "path"}))
    .with_section("headers", PartialSection(filled=HEADERS))
    .with_section("params",
                  PartialSection(filled={
                                     "from": "service-10-track",
                                     "similarities-experiment": "default"},
                                 required={"track-id"}))
    .build())

TRACK_INFO_REQUEST = (
    PartialRequestBuilder("GET")
    .with_url("https://music.yandex.ru/handlers/track.jsx")
    .with_section("headers", PartialSection(filled=HEADERS))
    .with_section("params",
                  PartialSection(automatic={"ncrnd": lambda: str(int(time.time()))},
                                 filled={
                                     "lang": "ru",
                                     "external-domain": "music.yandex.ru",
                                     "overembed": "false"},
                                 required={"track"}))
    .build())

TRACK_META_REQUEST = (
    PartialRequestBuilder("GET")
    .with_url("https://music.yandex.ru/api/v2.1/handlers/track/"
              "{track}:{album}/web-album_track-track-track-main/download/m",
              PartialSection(required={"track", "album"}))
    .with_section("headers", PartialSection(filled=HEADERS))
    .with_section("params",
                  PartialSection(automatic={"__t": lambda: str(int(time.time()))},
                                 filled={
                                     "external-domain": "music.yandex.ru",
                                     "overembed": "no"},
                                 required={"hq"}))
    .build())
