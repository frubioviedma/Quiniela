[app]
title = Quiniela Pro
package.name = quinielapro
package.domain = com.quinielapro
source.dir = .
source.include_exts = py,kv,png,jpg,ttf,txt,json,db
version = 0.1

requirements = python3,kivy,requests,beautifulsoup4
# Si necesitas numpy, descomenta y añade:
# requirements = python3,kivy,requests,beautifulsoup4,numpy

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a

android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 0


