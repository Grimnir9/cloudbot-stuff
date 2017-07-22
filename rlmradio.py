#Grabs Current Info for RLM Radio Stream

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

