import requests
import json
import threading
from queue import Queue, Empty
import sqlite3

from bs4 import BeautifulSoup as bsoup


def def_cooker(content):
    ret = []
    homs = content.find_all('div', {'class': 'hom'})
    for hom in homs:
        temp_dict = {}
        try:
            temp_dict['pos'] = hom.find('span', {'class': 'pos'}).text
        except AttributeError:
            temp_dict['pos'] = None
        temp_dict['senses'] = sense_cooker(hom)
        ret.append(temp_dict)
    return ret


def sense_cooker(content):
    senses = content.find_all('div', {'class': 'sense'})
    if not senses:
        try:
            return [{'def': content.find('span', {'class': 'xr'}).text.strip().replace('\n', ' ')}]
        except (AttributeError, ValueError):
            return None
    ret = []
    for each in senses:
        temp_dict = {}
        try:
            temp_dict['def'] = each.find('div', {'class': 'def'}).text.strip().replace('\n', ' ')
        except AttributeError:
            temp_dict['def'] = each.text.strip().replace('\n', ' '*2)
            ret.append(temp_dict)
            continue
        try:
            temp_dict['examples'] = [exam.text.strip().replace('\n', ' ')
                                     for exam in each.find_all('div', {'class': 'cit type-example'})]
        except AttributeError:
            temp_dict['examples'] = None
        try:
            temp_dict['synonyms'] = [syn.text
                                     for syn in each.find('div', {'class', 'thes'}).find_all('span', {'class': 'form'})]
        except AttributeError:
            temp_dict['synonyms'] = None
        ret.append(temp_dict)

    return ret


def scrap_word(word):
    try:
        rawpage = requests.get('https://www.collinsdictionary.com/dictionary/english/{}'.format(word), timeout=20)
    except requests.exceptions.RequestException:
        return 'Timeout'
    if 'Sorry, no results' in rawpage.text:
        return None
    psoup = bsoup(rawpage.content, 'html5lib')
    try:
        frequency = psoup.find('div', {'class': 'word-frequency-img'})['data-band']
    except TypeError:
        return None
    try:
        word_forms = [x.strip().replace('  ', ': ')
                      for x in psoup.find('span', {'class': 'form inflected_forms type-infl'}).text
                          .replace('\n', ' ')
                          .replace('Word forms:', '')
                          .split(',')]
    except AttributeError:
        word_forms = []

    if psoup.find('div', {'class': 'dictionary Cob_Adv_Brit'}):
        content = psoup.find('div', {'class': 'dictionary Cob_Adv_Brit'})
        all_def = def_cooker(content)
    elif psoup.find('div', {'class': 'dictionary Collins_Eng_Dict'}):
        content = psoup.find('div', {'class': 'dictionary Collins_Eng_Dict'})
        all_def = def_cooker(content)
    else:
        return None

    phrasal = [x.text.strip() for x in psoup.find_all('div', {'class': 're type-phrasalverb'})]

    try:
        extra_examples = [x.text.strip()
                          for x in psoup.find('div', {'class': 'assets'})
                              .find('div', {'class': 'cit type-example'})
                              .find_all('div')]
    except AttributeError:
        extra_examples = None

    return {'frequency': frequency,
            'forms': word_forms,
            'definitions': all_def,
            'phrasal': phrasal,
            'extra_examples': extra_examples}

    # except (AttributeError, TypeError) as err:
    #     print(err)
    #     return None


if __name__ == '__main__':
    # with open('words.json') as f:
    #     words = json.loads(f.read())
    # con = sqlite3.connect('DictDB.sqlite')
    # finished_words = [x[0] for x in con.cursor().execute('SELECT word FROM dict').fetchall()]
    # con.close()

    # for each in finished_words:
    #     if each in words:
    #         words.remove(each)
    #

    words = ['cat']
    words_len = len(words)
    counter = [0, 0]

    # con = sqlite3.connect('DictDB.sqlite')
    # con.cursor().execute('CREATE TABLE dict(word PRIMARY KEY, json_str)')
    # con.close()
    # word_dict = {}

    def scraper():
        while words:
            w = words.pop()
            w_content = scrap_word(w)
            counter[0] += 1
            if w_content is 'Timeout':
                words.append(w)
                counter[0] -= 1
                print('{:20} Timeout\t({:.2%})\t[{}]'.format(w, counter[0] / words_len, counter[1]))
            elif w_content:
                # word_dict[w] = w_content
                insertQ.put((w, w_content))
                counter[1] += 1
                print('{:20} Finished\t({:.2%})\t[{}]'.format(w, counter[0] / words_len, counter[1]))
            else:
                print('{:20} Unknown\t({:.2%})\t[{}]'.format(w, counter[0] / words_len, counter[1]))


    def insertDB():
        con = sqlite3.connect('DictDB.sqlite')

        while True:
            try:
                w, c = insertQ.get(timeout=60)
            except Empty:
                break
            try:
                con.cursor().execute('INSERT INTO dict VALUES(?, ?)', (w, json.dumps(c)))
            except sqlite3.IntegrityError:
                continue
            con.commit()
        con.close()

    insertQ = Queue()
    th = []
    for each in range(1):
        _t = threading.Thread(target=scraper)
        _t.start()
        th.append(_t)

    threading.Thread(target=insertDB).start()

    for each in th:
        each.join()


