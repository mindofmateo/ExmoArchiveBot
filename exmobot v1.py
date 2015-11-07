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
# YES I know I need to clean this ^ shit up.
##   https://github.com/spfaffly/phantomjs-linux-armv6l          this is for phantomjs on raspberrypi!!!!

phantomjslocation = ""

subreddit=''

app_ua = "ExmoArchiver v1.0 by /u/mindofmateo"
app_id = ''
app_secret = ''
app_uri = 'https://127.0.0.1:65010/authorize_callback'
app_refresh = ''

acct_code = ''
scopes = ''

skip = ('reddit','redd.it', 'washingtonpost.com')               # Omit these domains when archiving.

username = 'ExmoArchiveBot'
password = ''

# Post reply, comment line by line:
line1 = "**This comment is a test**.  Feedback is appreciated.  Upvotes are helpful. \n\n ************************************* \n\n This link has automatically been archived on the Internet Archive's Wayback Machine,"
line2 = "accessible in the future if it is lost down the memory hole, modified, redacted, etc."
# line3 defined below.   line3 = "To view the record, [click here](%s)."
line4 = "************************************************************************* \n\n"
line5 = "^^Bleep ^^bloop ^^I'm ^^a ^^robot! ^^Didn't ^^work? ^^Advice, ^^suggestions? ^^Let ^^me ^^know. [^^PM](https://www.reddit.com/message/compose/?to=mindofmateo)  ^^Just ^^ask ^^for ^^the ^^source ^^code."

def login():
    r = praw.Reddit(app_ua)                                     # Creates a reddit/PRAW object
    r.set_oauth_app_info(app_id, app_secret, app_uri)
    r.refresh_access_information(app_refresh)
    return r
# End of login()

# spool_reset() wipes the URL cache after 24 hours.
# run_bot() won't archive a URL more than once a day, and will
# not comment on/archive a post more than once.
# get_video() gets the direct video link if available in the submission.

def get_video(input_url):
    found = ''
    driver = webdriver.PhantomJS(executable_path=phantomjslocation)
    driver.get('http://en.savefrom.net/#url=' + input_url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    finds = soup.find_all("a")
    found = finds[6].get('href')
    if found == '/user.php?vid=323':
        found = 'novideo'
    print("Video URL: ", found)
    driver.quit()
    return found
# End of get_video()

def archive(input_url):
    archive_url = ('https://web.archive.org/save/' + input_url)
    record_url = ('https://web.archive.org/web/*/' + input_url)
    urllib.request.urlopen(archive_url)                         # Uncommenting this line will actually archive the URL.
    time.sleep(2)
    return record_url
# End of archive()

def spool_reset():
    today = int(time.time())                                    # Today's date as Unix time integer.
    print('Today: ', today)
    date_check = open('spool_reset_date.txt', 'r')              # Read's saved date.
    file_date = date_check.readline()                           # ^
    print('Date on file: ', file_date)
    file_date = (int(file_date) + 86400)                        # Makes file date an integer, plus one Unix day.
    
    if today > file_date:                                       # If today more than one day from saved
        date_check.close()                                      # date, it will reset the date and log.
        print(today, ' is greater than ', file_date, '. Date on file and URL spool will be reset.', sep = '', end = '\n\n')
        file_date = open('spool_reset_date.txt', 'w')           # Wipes the saved date.
        new_log_date = str(time.time())
        file_date.write(new_log_date[:10])                      # Saves new reference date.
        file_date.close()
        spool = open('url_spool.log', 'w')                      # Wipes the 24 hour spool.
        spool.close()
        postid = open('postidreset.log', 'a+')                       # Logs the datetime of the spool reset.
        postid.write('The URL spool was reset on: ')
        postid.write(new_log_date)
        postid.write('\n')
        postid.close()
    else:
        print(today, ' is less than or equal to ', file_date, '. No need to reset the file date.', sep='', end = '\n\n')
        date_check.close()
# End of spool_reset()

def make_comment(item, record_url):
    if item.id not in posts_replied_to:                         # If PostID not logged, bot makes a comment, logs the PostID.
        current_timestamp = time.time()
        datetime_ts = datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        line3 = ["To view the record (archived approximately ", datetime_ts, "), [click here](", record_url, ")."]
        line3 = "".join(line3)
        prereply = [line1, line2, line3, line4, line5]
        reply = '  \n'.join(prereply)                           # Builds the bot's reply text.
        item.add_comment(reply)
        posts_replied_to_log.write(item.id + '\n')
        time.sleep(20)                                          # Activity too fast will break because of API call limits (Just a safety buffer).
    else:
        pass
# End of make_comment()

def run_bot(subreddit):
    print('run_bot() is running. ', end="\n\n")

    spool_reset()                                               # This block makes a list of
    spool_log = open('url_spool.log', 'r+')                     # URLs from the past 24 hours
    spool_list = spool_log.readlines()                          # to omit any matches with
    for i in range(len(spool_list)):                            # incoming data.
        if '\n' in spool_list[i]:
            temp = spool_list[i]
            spool_list[i] = temp[:-1]
        else:
            pass

    submissions = r.get_subreddit(subreddit).get_new(limit=5)  # Fetches subreddit data.
    print('Retrieved the subreddit /r/%s. ' % subreddit)

    url_count = 0
    archived_count = 0

    inner_counter = 0 # WTF is this for?!
    
    for item in submissions:                                    # Loops through recent submission list.
        if str(item.url) not in spool_list:                     # Verify URL has not been archived in
            urlparse = urllib.parse.urlparse(item.url)          # last 24 hours.
            print(inner_counter, item.id, item.url[:55], urlparse[0], end=" ")
            inner_counter += 1 # See above, WTF is this for?!
            if urlparse[0] == 'http' or urlparse[0] == 'https' or urlparse[0] == 'ftp': # Checks for allowed protocols.
                skip_count = 0
                for i in skip:
                    if str(urlparse[1]).find(i) != -1:          # Checks for omitted domains.
                        print(i, end=" ")
                        skip_count += 1
                        break
                    else:
                        pass
                print(skip_count, end=' ')
                if skip_count == 0:                             # Begin the archive process.
                    print('inner if valid: ', urlparse[1], ' ') # Prints troubleshooting info.
                    # videourl = get_video(item.url)
                    # if videourl != 'novideo':
                    recorded = archive(item.url)
                    spool_log_new_line = item.url + '\n'
                    print(spool_log_new_line)
                    spool_log.write(spool_log_new_line)         # Adds the URL to the 24 hour log.
                    archived_count += 1
                    make_comment(item, recorded)
                else:
                    print('inner else invalid: ', urlparse[1], ' ') # Prints troubleshooting info.
            else:
                print('outer else INVALID: ', ' ', urlparse[1]) # Prints troubleshooting info.
            url_count += 1
        else:
            pass
    spool_log.close()
    posts_replied_to_log.close()
    print(url_count,' URLs were not in the log and were evaluated. ', archived_count, ' URLs were archived and spooled.')
# End of run_bot()

print('Logging in... ', end="")
r = login()
print('Logged in as', r.user, end='.\n')

posts_replied_to_log = open("post_ids_replied_to.log", "r+")
posts_replied_to = posts_replied_to_log.read()
posts_replied_to = posts_replied_to.split("\n")
posts_replied_to = [x for x in posts_replied_to if x != '']

run_bot(subreddit)

print('End of pyscript.')
