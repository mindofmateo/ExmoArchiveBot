import praw
import mmap
from datetime import datetime, timedelta
import bot
import urllib
import math
import os
import webbrowser
import time
import requests
import selenium
from urllib.request import Request, urlopen
from ghost import Ghost
from bs4 import BeautifulSoup
import mechanicalsoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Don't tell me I need to clean this up and polish it before deploying in real time, I know...

##   https://github.com/spfaffly/phantomjs-linux-armv6l          this is for phantomjs on raspberrypi!!!!

phantomjslocation = ""

subreddit='exmormon'
qtyofposts = 10

app_ua = "ExmoArchiver v2.0 by /u/mindofmateo"
app_id = ''
app_secret = ''
app_uri = ''
app_refresh = ''

acct_code = ''
scopes = 'account creddits edit flair history identity livemanage modconfig modcontributors modflair modlog modothers modposts modself modwiki mysubreddits privatemessages read report save submit subscribe vote wikiedit wikiread'

# Omit these domains when archiving:
skip = ('reddit','redd.it')

username = ''
password = ''

def commentbuilder(input_url):
    urlparse = urllib.parse.urlparse(input_url)
    if str(urlparse[1]).find('youtube') != -1:
        linktype = 'youtube'
    elif str(urlparse[1]).find('youtu.be') != -1:
        linktype = 'youtube'
    elif str(urlparse[1]).find('lds') != -1:
        linktype = 'pass'
    elif str(urlparse[1]).find('mormon') != -1:
        linktype = 'pass'
    elif str(urlparse[1]).find('byu') != -1:
        linktype = 'pass'
    elif str(urlparse[1]).find('imgur') != -1:
        linktype = 'imgur'
    else:
        linktype = 'other'
    
    record_url = 'https://web.archive.org/web/*/' + input_url
    
    youtubecomment = 'YouTube links cannot be archived on the Internet Archive\'s Wayback Machine. To manually download a copy of this video for recordkeeping, click [here](http://en.savefrom.net/#url=' + input_url + ').\n\n'
    autoarchivecomment = "This link has automatically been archived [here](" + record_url + ") on the Internet Archive's Wayback Machine, accessible in the future if it is lost down the memory hole, modified, redacted, etc. \n\n  If there is video embedded, you can try to manually download a copy of this video for recordkeeping by clicking [here](http://en.savefrom.net/#url=" + input_url + ").\n\n"
    defaultcomment = 'Hmmm... I don\'t recognize this link\'s domain.  You can try to manually archive it by clicking [here](https://web.archive.org/save/' + input_url + ').  To access the record once it is archived, click [here](http://web.archive.org/web/*/' + input_url + '). \n\n Or you can also try to download embedded video for recordkeeping by checking [here](http://en.savefrom.net/#url=' + input_url + '). \n\n'
    imgurcomment = 'This image has automatically been archived [here](' + record_url + ') on the Internet Archive\'s Wayback Machine.'
    current_timestamp = time.time()
    datetime_ts = datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S')
    endofcomment = datetime_ts + "\n\n ************************************************************************* \n\n ^^Bleep ^^bloop ^^I'm ^^a ^^robot! ^^Didn't ^^work? ^^Advice, ^^suggestions? ^^Let ^^me ^^know. [^^PM](https://www.reddit.com/message/compose/?to=mindofmateo)  ^^Just ^^ask ^^for ^^the ^^source ^^code."

    if linktype == 'pass' or linktype == 'imgur':
        archive(input_url)
    else:
        pass

    
    commenttext = {
        'youtube': (youtubecomment + endofcomment),
        'pass': (autoarchivecomment + endofcomment),
        'imgur': (imgurcomment + endofcomment),
        'other': (defaultcomment + endofcomment),
    }.get(linktype, ('Uhh... Something went wrong.' + endofcomment))
    
    return commenttext
# End of commentbuilder()

def make_comment(incomingurl, item):
    # reply is the plain text that will be entered into the comment/reply field.
    reply = commentbuilder(incomingurl)
    item.add_comment(reply)
    time.sleep(10)
# End of make_comment()

def login():
    r = praw.Reddit(app_ua)                                     # Creates a reddit/PRAW object
    r.set_oauth_app_info(app_id, app_secret, app_uri)
    r.refresh_access_information(app_refresh)
    return r
# End of login()

def archive(input_url):
    print(input_url)
    archive_url = ('https://web.archive.org/save/' + input_url)
    try:
        urllib.request.urlopen(archive_url)                         # Uncommenting this line will actually archive the URL.
    except urllib.HTTPError:
        print('Well, there was a fucking error on this one: ' + input_url + ' Error code: ' + err.code)
    time.sleep(2)
# End of archive()

def run_bot(subreddit):
    print('The main function run_bot() is running. ', end="\n\n")
    print('Logging in... ', end="")
    r = login()
    print('Logged in as', r.user, end='.\n\n')

    submissions = r.get_subreddit(subreddit).get_new(limit=qtyofposts)  # Fetches subreddit data.
    print('Retrieved %i posts from the subreddit /r/%s. \n' % (qtyofposts, subreddit))

    post_count = 0
    archived_count = 0

    inner_counter = 1 # WTF is this for?!  --> This is for counting output lines in the console.
    
    for item in submissions:                                    # Loops through recent submission list.
        flat_comments = praw.helpers.flatten_tree(item.comments)
        commenters = []
        urlparse = urllib.parse.urlparse(item.url)
        skip_count = 0
        for i in skip:
            if str(urlparse[1]).find(i) != -1:          # Checks for omitted domains.
                skip_count += 1
                break
            else:
                pass
        if skip_count == 0:                             # Begin the archive process.
            for i in flat_comments:
                commenters.append(str(i.author))
            if 'ExmoArchiveBot' in commenters:
                print(inner_counter, "|", 'This post has already been archived/replied to.(', item.id, ')', sep=' ')
                inner_counter += 1
            elif 'ExmoArchiveBot' not in commenters:
                print(inner_counter, "|", item.id, item.url[:55], urlparse[0], sep= ' ')
                inner_counter += 1 # See above, WTF is this for?!  --> This is for counting output lines in the console.
                make_comment(item.url, item)
                archived_count += 1
            else:
                print('I don\'t know what the fuck happened.')
        else:
            print(inner_counter, "|", 'outer else invalid: ', urlparse[1], '(', item.id, ')', sep= ' ') # Prints troubleshooting info.
            inner_counter += 1
        post_count += 1
    print(post_count,' posts were evaluated. ', archived_count, ' were commented.')  # update this
# End of run_bot()

run_bot(subreddit)

print('End of pyscript.')
