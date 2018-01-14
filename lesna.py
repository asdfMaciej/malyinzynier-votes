#!/usr/bin/python3
# Python 3.x, licencja GNU GPL - Maciej Kaszkowiak (asdfMaciej), 2017

import urllib
import urllib.request
import sqlite3
import argparse
from time import gmtime, strftime


class HTMLFetcher:
	def __init__(self, debug=False):
		self.url = "http://szkolamalegoinzyniera.pl/zaglosuj-na-szkole"
		self.spoof_headers = {  # niech mysla ze jakas przegladarka to recznie odswieza
			'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0',
			'Accept-Language': 'en-US,en;q=0.5'
		}
		self.debug = debug

	def fetch(self):
		request = urllib.request.Request(self.url, None, self.spoof_headers)
		html = urllib.request.urlopen(request).read()
		if self.debug:
			with open("fff.html", 'wb') as f:
				f.write(html)
		return html

class ListaParser:
	def __init__(self, db_callback):
		self.db = db_callback

	def parse(self, html):  # nie używam beautifulsoup ani innego parsera aby na wszystkim chodzilo
		data = strftime("%Y-%m-%d %H:%M:%S", gmtime())
		_szkoly = html.split('<li id="school-')[1:]
		pozycja = 1
		for s in _szkoly:
			szkola_id = int(s.split('" ')[0])
			nazwa = s.split('<li class="voting__column voting__column--wide">  ')[1].split('\n')[0]
			glosy = int(s.split('</li>\n    <li class="voting__column">')[1].split('</li>')[0])
			self.db.add(szkola_id, data, pozycja, glosy, nazwa)
			pozycja += 1

		self.db.finish()

class DBHelper:
	def __init__(self, db, first_time=False):
		self.db = sqlite3.connect(db)
		self.first_time = first_time
		if first_time:
			self.init_db()

	def init_db(self):
		kurs = self.db.cursor()
		try:
			kurs.execute('''CREATE TABLE szkoly
						(szkola_id integer, nazwa text)''')  # przechowuje szkoly
			kurs.execute('''CREATE TABLE glosy
						(szkola_id integer, pozycja integer, glosy integer, data text)''')  # przechowuje glosy
		except:
			print("DB init error - nalezy usunac db i jeszcze raz sprobowac")
		self.db.commit()

	def add(self, szkola_id, data, pozycja, glosy, nazwa):
		kurs = self.db.cursor()
		if self.first_time:
			kurs.execute('INSERT INTO szkoly VALUES (?, ?)', (szkola_id, nazwa))
		kurs.execute('INSERT INTO glosy VALUES (?, ?, ?, ?)', (szkola_id, pozycja, glosy, data))

	def finish(self):
		self.db.commit()
		self.db.close()
		print("Zamknieto polaczenie z db")

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="Podlicza głosy szkoły małego inżyniera do bazy danych - Pierwsze uruchomienie z -i"
	)
	parser.add_argument("-d" ,"--debug", help="Włącza drobny debug", action="store_true")
	parser.add_argument("-i" ,"--init", help="Init bazy danych - użyć raz i tylko raz", action="store_true")
	parser.add_argument("dbname", type=str, help="Plik bazy danych sqlite3 [.db]")

	args = parser.parse_args()
	data = DBHelper(args.dbname, first_time=args.init)
	par = ListaParser(data)
	abc = HTMLFetcher(args.debug)
	html = str(abc.fetch(), 'utf-8')
	par.parse(html)
