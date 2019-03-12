import sqlite3

import requests
from bs4 import BeautifulSoup
import downloader

class SongData():

    def __init__(self, url):
        self.url = url
        self.year = url[-4:]
        self.tags = self.get_contents()
        self.num = self.get_num()
        self.name = self.get_name()
        self.artist = self.get_artist()
        self.data = self.combine_data()

    def get_contents(self):
        """ Gets all the tags """

        url_contents = requests.get(self.url).content
        soup = BeautifulSoup(url_contents, "html.parser")
        tags = [tag for tag in soup.find_all('tr')]
        start_tag = tags[1].find('th').text.strip('\n')
        if start_tag == '1':
            return tags[1:101]
        else:
            return tags[2:102]

    def get_num(self):
        """ Gets all the song ranking numbers """

        nums = []
        for tag in self.tags:
            num = tag.find('th').text.strip('\n')
            nums.append(num)
        return nums

    def get_name(self):
        """ Gets all the song names """

        names = []
        for tag in self.tags:
            name = tag.find('td').text[1:-1]
            names.append(name)
        return names

    def get_artist(self):
        """ Gets the first artist found for a song """

        artists = []
        for tag in self.tags:
            artist = tag.find('td').next_sibling.next_sibling.find('a').text
            artists.append(artist)
        return artists

    def combine_data(self):
        """ Combines all the data into a dict """

        data = []
        for i in enumerate(self.num):
            d = [x[i[0]] for x in (self.num, self.name, self.artist)]
            dset = {
                'year': self.year,
                'num': d[0],
                'name': d[1],
                'artist': d[2],
            }
            data.append(dset)
        return data

    def __repr__(self):
        return "SongData('{}', '{}', '{}')".format(self.url, self.year, len(self.data))

    def __str__(self):
        return "SongData('{}', '{}')".format(self.url, self.year)

    def __len__(self):
        return len(self.data)


def save_data(data):
    """ Saves the data to the database """

    conn = sqlite3.connect('db/music.db')
    c = conn.cursor()
    for d_set in data:
        c.execute("""INSERT INTO music
                    (year, rank,
                    song_name, artist)
                    values (?,?,?,?)""",
                    (d_set['year'], d_set['num'], d_set['name'], d_set['artist']))
        conn.commit()
    conn.close()


def request_data(years):
    """ Sends all data from a year to save_data() """
    for year in years:
        url = 'https://en.wikipedia.org/wiki/Billboard_Year-End_Hot_100_singles_of_%s' %year
        d = SongData(url)
        print('Adding to db:', str(d))
        save_data(d.data)
    # start downloading
    downloader.download_song()



if __name__ == '__main__':
    old_years = [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009]
    years = old_years + [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018]
    print("Adding %s years to db" %len(years))
    request_data(years)

