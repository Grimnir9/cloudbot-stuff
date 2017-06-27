import requests
import re
from bs4 import BeautifulSoup
from cloudbot import hook

# This will match ANY we url including youtube, reddit, twitch, etc... Some additional work needs to go into
# not sending the web request etc if the match also matches an existing web regex.

# 2017-06-26 Modified to exclude YouTube and twitter urls as they are handled by other modules. Also eliminated at link.
# 2017-06-27 added code to remove blank lines from title if found.

url_re = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')


@hook.regex(url_re)
def print_url_title(match):
    # It would be a good idea to also include useragent headers in the request
    r = requests.get(match.group())
    html = BeautifulSoup(r.text)
    title = html.title.text
    # out = "Title: {} at: {}".format(title, r.url)
    filtered = re.sub(u'(?imu)^\s*\n', u'', title)
    if 'youtu' not in r.url and 'twitter' not in r.url:  #exclude YouTube URL's
        out = "Title: {}".format(filtered)
        return out
    
