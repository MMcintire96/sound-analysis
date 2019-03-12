import sqlite3
import requests
from bs4 import BeautifulSoup
import time
import youtube_dl
import numpy as np
from pydub import AudioSegment
import os


# load in or iniatlize the arrs
try:
    f_data = np.load('audio_data.npz')
    f_label = np.load('audio_labels.npz')
    all_data = []
    all_labels = []
    for x in f_data['data']:
        all_data.append(x)
    for x in f_label['labels']:
        all_labels.append(x)
except Exception as e:
    all_data = []
    all_labels = []

# make sure len matches
print(len(all_data))
print(len(all_labels))

def encode_label(vid_id):
    ''' Hot encodes a label with shape [1, 0] '''

    conn = sqlite3.connect('db/music.db')
    c = conn.cursor()
    c.execute("SELECT * FROM music WHERE yt_id=?", (vid_id,))
    for row in c.fetchall():
        rank = row[1]
        if rank < 50:
            label = np.array([1, 0])
        else:
            label = np.array([0, 1])
        return label
    else:
        print('NOT FOUND IN DB')
        return np.array([0, 0])

def read_m4a(f, normalized=False):
    ''' Converts a m4a to numpy array '''

    a = AudioSegment.from_file(f, format='m4a')
    y = np.array(a.get_array_of_samples())
    if a.channels == 2:
        y = y.reshape((-1, 2))
    if normalized:
        return a.frame_rate, np.float32(y) / 2**15
    else:
        return a.frame_rate, y

def save_data(vid_id):
    ''' Saves the array and label '''

    label = encode_label(vid_id)
    vid_path = 'audio/' + str(vid_id) + '.m4a'
    sr, data = read_m4a(vid_path, normalized=False)
    all_data.append(data)
    all_labels.append(label)
    # why is this arr of data 10x the size of the m4a ????
    try:
        np.savez_compressed('audio_data', data=all_data)
        np.savez_compressed('audio_labels', labels=all_labels)
    except Exception as e:
        print("EXCEPTION %s" %str(e))
    return 1


def yt_downloader(link, vid_id):
    ''' downloads the video from youtube '''

    options = {
        'format': 'm4a',
        'extractaudio': True,
        'noplaylist': True,
        'outtmpl': 'audio/%(id)s.%(ext)s'
    }
    try:
        with youtube_dl.YoutubeDL(options) as ydl:
            ydl.download([link])
        loaded = save_data(vid_id)
    except Exception as e:
        print(str(e))
        loaded = 0
    return loaded


def download_song():
    ''' connects all of the above scripts and saves the data into sql '''

    conn = sqlite3.connect('db/music.db')
    c = conn.cursor()
    c.execute("SELECT * FROM music WHERE yt_path IS NULL")
    yt_base_url = 'https://youtube.com'
    search_url = '/results?search_query='
    for row in c.fetchall():
        query = row[2] + ' by ' + row[3] + ' lyrics'
        yt_content = requests.get(yt_base_url + search_url + query)
        print(yt_content.url)
        if yt_content.url[:29] == 'https://www.google.com/sorry/':
            print("Hit captcha, recalling in 30 mins")
            time.sleep(108000)
        else:
            soup = BeautifulSoup(yt_content.content, "html.parser")
            a_tags = soup.find_all('a')
            for tag in a_tags:
                try:
                    if tag.attrs['href'][:7] == '/watch?':
                        vid_id = tag.attrs['href']
                        yt_full_path = yt_base_url + vid_id
                        c.execute("""UPDATE music
                                SET yt_path = ?, yt_id = ?
                                WHERE song_name = ?""",
                                (yt_full_path, vid_id[9:], row[2]))
                        conn.commit()
                        loaded = yt_downloader(yt_full_path, vid_id[9:])
                        c.execute("""UPDATE music
                                SET loaded = ?
                                WHERE yt_path = ?""",
                                (loaded, yt_full_path))
                        conn.commit()
                        break
                    else:
                        pass
                except Exception as e:
                    print(e)
    conn.close()


if __name__ == '__main__':
    download_song()
