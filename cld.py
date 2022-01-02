#!/usr/bin/python3
import queue

import pyperclip
import time
import validators
import os
from queue import Queue
from threading import Thread


sites = ['youtube', 'vimeo', 'soundcloud']
linkLogFile = "links"

# Reads previously downloaded links from log and starts downloading them again.
# If true, e.g. previously failed or incomplete downloads are resumed/tried again.
checkDownloads = True


dlq = Queue(maxsize=0)  # download queue (links to be downloaded)
links = []  # link list (All links. Downloaded and not yet downloaded)


#
# Download Thread
# Downloads links from the Queue as background thread
#
def dl(q):
    while True:
        u = q.get()
        print("download [" + str(len(links) - (q.qsize())) + "/" + str(len(links)) + "]  " + str(u).split('://')[-1])
        os.system(u)
        q.task_done()


#
# Add Download Command to urls and appends them to the download queue
# Enables future implementation of different download commands for different sites/urls
#
def add_download(link):
    dlq.put("yt-dlp -q --no-call-home " + link)


#
# Main Function and endless loop
#
#
def main():
    global links

    print("\nThank you for choosing ldl as your favourite tool to hoard unhealthy amounts of data ;)")
    print("https://www.github.com/arnediehm/ldl\n")

    dl_worker = Thread(target=dl, args=(dlq,))
    dl_worker.daemon = True

    # Init link list from link log file for duplicate checking and retry of possibly failed downloads
    print("Reading Logfile")
    with open(linkLogFile, 'a+') as f:  # a+ creates the file if missing
        f.seek(0)  # we have to set the pointer to the files beginning due to 'a+'
        links = [line.strip() for line in f]

    if checkDownloads:
        print("Restarting downloads from logfile")
        for i in links:
            add_download(i)

    dl_worker.start()

    while True:
        time.sleep(0.1)
        url = pyperclip.paste()

        if validators.url(url):
            if any(x in url for x in sites):
                if links.count(url) == 0:  # don't download the same link twice
                    os.system(
                        "notify-send '" + "Downloads pending: " + str(dlq.qsize() + 1) + ". Added " +
                        str(url).split('/')[-1] + "'")

                    add_download(str(url))
                    links.append(url)

                    with open(linkLogFile, 'a+') as f:
                        f.write(url + "\n")

                if not dl_worker.is_alive():
                    dl_worker.start()


if __name__ == "__main__":
    main()
