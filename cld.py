#!/usr/bin/python3
import pyperclip
import time
import validators
import os
from queue import Queue
from threading import Thread
from enum import IntEnum
from sys import platform


link_log = "links"   # log file
polling_interval_hz = 10  # Clipboard Polling Interval  in HZ (x/second)


def site_config():

    # add_site(
    #   site name from url "dot" - e.g. "youtube."
    #   download command
    #   download timeout (seconds) - increase when downloading a lot to prevent getting banned (e.g. http error 429)
    #   download links (from log) again on script startup. Continues e.g. temporarily failed downloads.
    # )

    # Configuration Examples.
    # Youtube has two configurations. So youtube links get downloaded two times (as mp3 AND as mkv)
    #

    # Download mp3 from youtube (best audio). Download playlist if the url refers to a video and a playlist.
    add_site(  # Youtube -> MP3
        "youtube.",
        "yt-dlp -q -x -f 251/ba* --audio-format mp3 --yes-playlist --audio-quality 0  --embed-metadata "
        "--embed-thumbnail --embed-chapters --embed-info-json",
        5,
        True
    )

    # Download video from youtube (convert to mkv). Ignore playlist if the url refers to a video and a playlist.
    add_site(  # Youtube -> Video
        "youtube.",
        "yt-dlp -q --remux-video mkv --no-playlist --embed-metadata "
        "--embed-thumbnail --embed-chapters --embed-info-json",
        0,
        True
    )

    # Download mp3 or wav (if available) from soundcloud. Convert wav files to mp3.
    add_site(  # Soundcloud -> MP3
        "soundcloud.",
        "yt-dlp -q --no-mtime --add-metadata --embed-thumbnail -x --audio-format mp3 --audio-quality 0",
        0,
        False
    )

    # Download Videos to mkv for all unconfigured sites
    add_site(  # Website -> MP4
        "default.",
        "yt-dlp -q --remux-video mp4 --embed-metadata --embed-thumbnail --embed-chapters --embed-info-json",
        0,
        False
    )


dlq = Queue(maxsize=0)  # download queue
links = set()  # Contains (All links. Downloaded and not yet downloaded)
configs = []  # site configurations


class Config(IntEnum):
    SITE = 0
    CMD = 1
    TIMEOUT = 2
    RE_DL = 3


#
# Downloads the link queue in background thread
#
def download(queue):
    while True:
        dl = queue.get()
        conf = dl[0]
        url = dl[1]

        download_nr = str(len(links) - (queue.qsize()))

        print("Downloading [" + download_nr + "/" + str(len(links)) + "]  " + str(url).split('://')[-1])

        os.system(conf[Config.CMD] + " '" + url + "'")
        time.sleep(conf[Config.TIMEOUT])

        queue.task_done()


#
# Add Download Command to urls and appends them to the download queue
# Enables future implementation of different download commands for different sites/urls
#
def queue_download(conf, link):
    dlq.put([conf, link])


def add_site(url_dot, dl_command, dl_timeout, dl_again):
    configs.append([url_dot, dl_command, dl_timeout, dl_again])


def notification(msg):
    if platform == "linux" or platform == "linux2":  # linux2 deprecated from python3.3 onwards
        os.system("notify-send '" + msg + "'")
    elif platform == "darwin":
        os.system("osascript -e 'display notification \"" + msg + "\"'")
    elif platform == "win32":
        os.system('createobject("wscript.shell").popup "cld.py", 5, "' + msg + '", 64')


# Windows...

#
# Main Function and endless loop
#
#
def main():
    global links

    print("\nThank you for choosing cld as your favourite tool to hoard unhealthy amounts of data ;)")
    print("https://www.github.com/arnediehm/cld\n\n")

    site_config()

    print("Reading Logfile\n")

    with open(link_log, 'a+') as f:  # a+ creates the file if missing
        f.seek(0)  # we have to set the pointer to the files beginning due to 'a+'
        links = [line.strip() for line in f]

    for link in links:
        conf_available = False

        for config in configs:
            if config[Config.SITE] in link:
                conf_available = True
                if config[Config.RE_DL]:
                    queue_download(config, link)

        if not conf_available:
            for config in configs:
                if "default." in config:
                    if config[Config.RE_DL]:
                        queue_download(config, link)

    dl_worker = Thread(target=download, args=(dlq,))
    dl_worker.daemon = True

    while True:
        time.sleep(1 / polling_interval_hz)

        url = pyperclip.paste()

        if validators.url(url):
            if links.count(url) == 0:  # don't download the same link twice
                for config in configs:
                    if config[Config.SITE] in url:

                        notification("Pending: " + str(dlq.qsize() + 1) + " Downloads. Queued: " + str(url).split('/')[-1])

                        if links.count(url) == 0:
                            open(link_log, 'a+').write(url + "\n")

                        queue_download(config, url)
                        links.append(url)

                if not dl_worker.is_alive():
                    dl_worker.start()


if __name__ == "__main__":
    main()
