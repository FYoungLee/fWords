import random
import re
import datetime
import json
import sqlite3
import os


class WordOBJ:
    def __init__(self):
        self.enDict = {}
        self.progress = []
        self.loadDB()
        self.myStatus = {'skilled': 0, 'in_progress': 0, 'unknown': 0}
        self.init_status()
        self.today_list = {}

    def loadDB(self):
        con = sqlite3.connect('DictDB.sqlite')
        raw = con.cursor().execute('SELECT * FROM dict').fetchall()
        for word, json_str in raw:
            self.enDict[word] = json.loads(json_str)
        if 'myProgress.json' not in os.listdir('.'):
            self.make_progress()
        else:
            with open('myProgress.json') as f:
                self.progress = json.loads(f.read())

    def init_status(self):
        for each in self.progress:
            if each['exp'] == -1:
                self.myStatus['skilled'] += 1
            elif each['exp'] > 0:
                self.myStatus['in_progress'] += 1
            elif each['exp'] == 0:
                break
        self.myStatus['unknown'] = len(self.progress) - self.myStatus['skilled'] - self.myStatus['in_progress']

    @staticmethod
    def make_progress():
        con = sqlite3.connect('DictDB.sqlite')
        raw = con.cursor().execute('SELECT * FROM dict').fetchall()
        con.close()
        frequency = {1: [], 2: [], 3: [], 4: [], 5: []}
        for word, json_str in raw:
            w = json.loads(json_str)
            frequency[int(w['frequency'])].append(word)

        f = []
        for n in range(5, 0, -1):
            for each in frequency[n]:
                f.append({'word': each, 'latest': None, 'exp': 0})
        with open('myProgress.json', 'w') as file:
            file.write(json.dumps(f))

    def dump_progress(self):
        with open('myProgress.json', 'w') as f:
            f.write(json.dumps(self.progress))

    def display_all(self, word):
        if word not in self.enDict.keys():
            return
        ret = '<h3>{}</h3>'.format(word)
        try:
            ret += '<i>'
            for each in self.enDict[word]['forms']:
                ret += '{}{};&nbsp;'.format('&nbsp;' * 2, each)
            ret += '</i><br>'

            ret += '<br>DEFINITIONS:<br>'
            for N, each in enumerate(self.enDict[word]['definitions']):
                ret += '<br><b>[{}]</b> {}:'.format(N + 1, '(<i>{}</i>)'.format(each['pos']) if each['pos'] else '')
                for _each in each['senses']:
                    ret += '<br>{}<b><i>{}</i></b><br>'.format('&nbsp;' * 4, _each['def'])
                    if 'examples' in _each and _each['examples']:
                        ret += '&nbsp;' * 6 + '- Examples:<br>'
                        for __each in _each['examples']:
                            ret += '{}<i>*&nbsp;{}</i><br>'.format('&nbsp;' * 12, __each)
                    else:
                        continue
                    if 'synonyms' in _each and _each['synonyms']:
                        ret += '{}{}<br>'.format('&nbsp;' * 6, '- Synonyms:', )
                        ret += '{}<i>{}</i><br>'.format('&nbsp;' * 12, '&nbsp;;&nbsp;&nbsp;'.join(_each['synonyms']))

            if 'phrasal' in self.enDict[word] and self.enDict[word]['phrasal']:
                ret += '<br>PHRASAL:<br>'
                for each in self.enDict[word]['phrasal']:
                    ret += '{}{}<br>'.format('&nbsp;' * 4, each)
        except (TypeError, ValueError):
            pass
        return ret

    def get_hints(self, word):
        hints = []
        for each in self.enDict[word]['definitions']:
            if 'pos' in each.keys() and each['pos']:
                if 'def' in each['senses'][0].keys() and each['senses'][0]['def']:
                    hint = each['senses'][0]['def'].lower()
                    hints.append(hint)
        return random.choice(hints)

    @staticmethod
    def _word_review_date(word):
        _t = datetime.datetime.fromtimestamp(word['latest']) + datetime.timedelta(days=word['exp'] ** word['exp'])
        return _t.timestamp()

    @staticmethod
    def _word_need_review(word):
        if word['exp'] == -1:
            return False
        elif word['exp'] == 0:
            return True
        else:
            return datetime.datetime.now().timestamp() >= WordOBJ._word_review_date(word)

    def create_today_list(self, day_max):
        for each in self.progress:
            if len(self.today_list) >= day_max:
                break
            if self._word_need_review(each):
                self.today_list[each['word']] = 0

    def get_a_word(self):
        if self.today_list:
            return random.choice(list(self.today_list.keys()))

    def word_failed(self, word):
        self.today_list[word] += 1

    def word_passed(self, word, exp=1):
        if exp:
            self.today_list[word] -= 1
            if self.today_list[word] < 0:
                self.today_list.pop(word)
                for each in self.progress:
                    if word is each['word']:
                        each['exp'] += 1
                        each['latest'] = datetime.datetime.now().timestamp()
                self.dump_progress()
                self.myStatus['in_progress'] += 1
        else:
            self.today_list.pop(word)
            for each in self.progress:
                if word is each['word']:
                    each['exp'] = -1
                    each['latest'] = datetime.datetime.now().timestamp()
            self.dump_progress()
            self.myStatus['skilled'] += 1
        self.myStatus['unknown'] -= 1