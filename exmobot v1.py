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
from urllib.request import Request, urlopen

subreddit='test'
skip = ('reddit','redd.it')                                     # Omit these domains when archiving.
username = ''                                                   # Username and password go here, but
password = ''                                                   # this will need to be updated by OAuth2 **ASAP**.
r = praw.Reddit(user_agent = "ExmoArchiver v1.0 by /u/mindofmateo") # Creates a reddit/PRAW object

# user_agent reply, by line:
line1 = "This link has automatically been archived on the Internet Archive's Wayback Machine,"
line2 = "accessible in the future if it is lost down the memory hole, modified, redacted, etc."
# line3 defined below.   line3 = "To view the record, [click here](%s)."
line4 = "*************************************************************************"
line5 = "^^Bleep ^^bloop ^^I'm ^^a ^^robot! ^^Didn't ^^work? ^^Advice, ^^suggestions? ^^Let ^^me ^^know. [^^PM](https://www.reddit.com/message/compose/?to=mindofmateo)"

print('Logging in... ', end="")
r.login(username, password, disable_warning=True)               # Logs in to reddit.  'disable_warnings=True' handles
print('Log in complete. ', end="")                              # the error/warning alerting the user that '.login()'
                                                                # is going away in favor of OAuth2.
# spool_reset() wipes the URL cache after 24 hours.
# run_bot() won't archive a URL more than once a day, and will
# not archive/comment on a post more than once.

def spool_reset():
    today = int(time.time())                                    # Today's date as Unix time integer.
    print(today, 'Today')
    date_check = open('spool_reset_date.txt', 'r')              # Read's saved date.
    file_date = date_check.readline()                           # ^
    print(file_date, 'Date on file', end='')
    file_date = (int(file_date) + 86400)                        # Makes file date an integer, plus one Unix day.
    
    if today > file_date:                                       # If today more than one day from saved
        date_check.close()                                      # date, it will reset the date and log.
        print(today, ' is greater than ', file_date, '. Date on file will be reset.')
        file_date = open('spool_reset_date.txt', 'w')           # Wipes the saved date.
        new_log_date = str(time.time())
        file_date.write(new_log_date[:10])                      # Saves new reference date.
        file_date.close()
        spool = open('url_spool.log', 'w')                      # Wipes the 24 hour spool.
        spool.close()
        postid = open('postid.log', 'a+')                       # Logs the datetime of the spool reset.
        postid.write('The URL spool was reset on: ')
        postid.write(new_log_date)
        postid.write('\n')
        postid.close()
    else:
        print(today, ' is less than or equal to ', file_date, '. No need to reset the file date.')
        date_check.close()
# End of spool_reset()


def run_bot(subreddit):
    print('run_bot() is running. ', end="")

    spool_reset()                                               # This block makes a list of
    spool_log = open('url_spool.log', 'r+')                     # URLs from the past 24 hours
    spool_list = spool_log.readlines()                          # to omit any matches with
    for i in range(len(spool_list)):                            # incoming data.
        if '\n' in spool_list[i]:
            temp = spool_list[i]
            spool_list[i] = temp[:-1]

    submissions = r.get_subreddit(subreddit).get_new(limit=20)  # Fetches subreddit data.
    print('Retrieved the subreddit /r/%s. ' % subreddit)

    url_count = 0
    archived_count = 0
    posts_replied_to_log = open("post_ids_replied_to.log", "r+")
    posts_replied_to = posts_replied_to_log.read()
    posts_replied_to = posts_replied_to.split("\n")
    posts_replied_to = filter(None, posts_replied_to)

    for item in submissions:                                    # Loops through recent submission list.
        if str(item.url) not in spool_list:                     # Verify URL has not been archived in
            urlparse = urllib.parse.urlparse(item.url)          # last 24 hours.
            print(item.id, item.url[:55], urlparse[0], end=" ")
            if urlparse[0] == 'http' or urlparse[0] == 'https': # Checks for allowed protocols.
                skip_count = 0
                for i in skip:
                    if str(urlparse[1]).find(i) != -1:          # Checks for omitted domains.
                        print(i, end=" ")
                        skip_count += 1
                        break
                print(skip_count, end=' ')
                if skip_count == 0:
                    print('inner if valid: ', urlparse[1], ' ') # Prints troubleshooting info.
                    archive_url = ('https://web.archive.org/save/' + item.url)
                    record_url = ('https://web.archive.org/web/*/' + item.url)
                    # urllib.request.urlopen(archive_url)         # Uncommenting this line will actually archive the URL.
                    time.sleep(1)
                    spool_log_new_line = item.url + '\n'
                    print(spool_log_new_line)
                    spool_log.write(spool_log_new_line)         # Adds the URL to the 24 hour log.
                    archived_count += 1
                    if item.id not in posts_replied_to:         # If PostID not logged, bot makes a comment, logs the PostID.
                        line3 = ("To view the record, [click here](%s)." % record_url)
                        prereply = [line1, line2, line3, line4, line5]
                        reply = '  \n'.join(prereply)           # Builds the bot's reply text.
                        item.add_comment(reply)
                        posts_replied_to_log.write(item.id + '\n')
                        time.sleep(540)                         # A long delay, script will break if it goes too fast because
                else:                                           # '/u/ExmoArchiveBot doesn't have enough karma to post very fast.
                    print('inner else invalid: ', urlparse[1], ' ') # Prints troubleshooting info.
            else:
                print('outer else INVALID: ', ' ', urlparse[1]) # Prints troubleshooting info.
            url_count += 1
    spool_log.close()
    posts_replied_to_log.close()
    print(url_count,' URLs were evaluated. ', archived_count, ' URLs were archived and spooled.')
# End of run_bot()


run_bot(subreddit)

print('End of pyscript.')
