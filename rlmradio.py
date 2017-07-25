#Grabs Current Info for RLM Radio Stream and others

import requests
import re
from cloudbot import hook
import urllib
import urllib.request

@hook.command("rlmradio", autohelp=False)
def rlmradio(text):

    url = "http://38.135.36.125:7359/7.html"
    html = urllib.request.urlopen(url).read()
    htmlout = html[28:-14]
    pw_bytes = htmlout.decode("utf-8")
    filtered = pw_bytes.replace("&apos;", "'")
    filtered = "Now on the RLM Radio Stream: " + filtered
    out = filtered
    return out

''' BU4B is blocked
@hook.command("bu4b", autohelp=False)
def bu4b(text):

    url = "http://72.13.82.82:5100/7.html"
    html = urllib.request.urlopen(url).read()
    htmlout = html[83:-14]
    pw_bytes = htmlout.decode("utf-8")
    filtered = pw_bytes.replace("&apos;", "'")
    filtered = "Now on the Belly Up For Blues Stream: " + filtered
    out = filtered
    return out
'''

@hook.command("aardvark", autohelp=False)
def aardvark(text):

    url = "http://orion.prostreaming.net:8288/7.html"
    html = urllib.request.urlopen(url).read()
    htmlout = html[35:-14]
    pw_bytes = htmlout.decode("utf-8")
    filtered = pw_bytes.replace("&apos;", "'")
    filtered = "Now on the Aardvark Radio Stream: " + filtered
    out = filtered
    return out


@hook.command("radiocrypto", autohelp=False)
def radiocrypto(text):

    url = "http://104.131.121.96:8000/7.html"
    html = urllib.request.urlopen(url).read()
    htmlout = html[30:-14]
    pw_bytes = htmlout.decode("utf-8")
    filtered = pw_bytes.replace("&apos;", "'")
    filtered = "Now on the http://radiocrypto.com/ Radio Stream: " + filtered
    out = filtered
    return out
