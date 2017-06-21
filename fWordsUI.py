from PyQt5.QtWidgets import QWidget, QTabWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QTextBrowser, \
    QPushButton, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QCheckBox, QGridLayout, QDialog, QHeaderView
from PyQt5.Qt import QIcon, QSize, QDesktopServices, QUrl, QPixmap, pyqtSignal, QWebEngineView, QTextCursor, QWebEnginePage
import os
import re
import fWordCore


class fWordsMainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.myDictDB = fWordCore.WordOBJ()
        self.the_word = None
        self.setWindowTitle('fWords by Fyang')
        self.mainTabWidget = QTabWidget()
        self.mainLayout = QVBoxLayout()

        self.vocaWidget = QWidget()
        self.mainTabWidget.addTab(self.vocaWidget, 'Vocabulary')

        self.dictWidget = QWidget()
        self.mainTabWidget.addTab(self.dictWidget, ' Dictionary ')

        uppervocaLayout = QHBoxLayout()
        self.voLabel = QTextBrowser()
        self.voLabel.setMinimumWidth(480)
        uppervocaLayout.addWidget(self.voLabel)
        btnLabel = QVBoxLayout()
        uppervocaLayout.addLayout(btnLabel)

        self.previousLabel = QLabel()
        self.previousLabel.setMinimumWidth(200)
        self.checkLine = QLineEdit()
        self.checkLine.returnPressed.connect(self.check_the_word)
        self.checkBtn = QPushButton('Check')
        self.checkBtn.clicked.connect(self.check_the_word)
        vocabottomLabel = QHBoxLayout()
        vocabottomLabel.addStretch()
        vocabottomLabel.addWidget(self.previousLabel)
        vocabottomLabel.addWidget(self.checkLine)
        vocabottomLabel.addWidget(self.checkBtn)

        self.todayLine = QLineEdit()
        self.todayLine.setText('50')
        self.todayBtn = QPushButton('Load words')
        self.todayBtn.clicked.connect(self.loadToday)

        self.statusLabel = QLabel()
        self.statusLabel.setMinimumHeight(80)
        self.refresh_status()

        self.knewBtn = QPushButton('Knew')
        self.knewBtn.clicked.connect(self.word_passed)
        # self.nextBtn = QPushButton('Next')
        # self.nextBtn.clicked.connect(self.get_word)
        self.speakBtn = QPushButton('Speak')
        self.speakBtn.clicked.connect(self.speakWord)
        self.voiceHintBtn = QPushButton('Voice Hint')
        self.voiceHintBtn.clicked.connect(self.voice_hint)
        self.textHintBtn = QPushButton('Text Hint')
        self.textHintBtn.clicked.connect(self.text_hint)
        # self.picHintBtn = QPushButton('Pictures')
        btnLabel.addWidget(self.todayLine)
        btnLabel.addWidget(self.todayBtn)
        btnLabel.addWidget(self.statusLabel)
        btnLabel.addWidget(self.knewBtn)
        # btnLabel.addWidget(self.nextBtn)
        btnLabel.addWidget(self.speakBtn)
        btnLabel.addWidget(self.voiceHintBtn)
        btnLabel.addWidget(self.textHintBtn)
        # btnLabel.addWidget(self.picHintBtn)

        vocaLabel = QVBoxLayout()
        vocaLabel.addLayout(uppervocaLayout)
        vocaLabel.addLayout(vocabottomLabel)
        self.vocaWidget.setLayout(vocaLabel)


        dictLayout = QVBoxLayout()
        self.dictWidget.setLayout(dictLayout)

        searchBox = QHBoxLayout()
        self.searchLine = QLineEdit()
        self.searchLine.returnPressed.connect(self.search_word)
        self.searchLine.setMaximumWidth(100)
        self.searchBtn = QPushButton("Search")
        self.searchBtn.clicked.connect(self.search_word)
        self.speakBtn2 = QPushButton('Speak')
        self.speakBtn2.clicked.connect(self.speakWord)

        searchBox.addWidget(self.searchLine)
        searchBox.addWidget(self.searchBtn)
        searchBox.addWidget(self.speakBtn2)
        searchBox.addStretch()

        self.resultPage = QTextBrowser()
        self.resultPage.setMinimumWidth(480)
        self.resultPage.selectionChanged.connect(self.tips)

        dictLayout.addLayout(searchBox)
        dictLayout.addWidget(self.resultPage)

        self.browser = QWebEngineView()
        self.browser.setVisible(False)
        self.showPicBtn = QPushButton('Search for Pictures')
        self.showPicBtn.clicked.connect(self.displayPic)
        self.mainLayout.addWidget(self.mainTabWidget)
        self.mainLayout.addWidget(self.browser)
        self.mainLayout.addWidget(self.showPicBtn)
        self.setLayout(self.mainLayout)

        self.refresh_status()
        self.show()

    def refresh_status(self):
        t = '''Today      \t{}\nSkilled    \t{}\nIn Progress\t{}\nUnknown\t{}'''\
            .format(len(self.myDictDB.today_list),
                    self.myDictDB.myStatus['skilled'],
                    self.myDictDB.myStatus['in_progress'],
                    self.myDictDB.myStatus['unknown'])
        self.statusLabel.setText(t)

    def search_word(self):
        word = self.searchLine.text().lower()
        if word:
            text = self.myDictDB.display_all(word)
            if text is None:
                os.system('say no such word')
                return
            self.resultPage.setText(text)
            self.speakWord()
            self.browser.setVisible(False)
            self.showPicBtn.setText('Search for Pictures')
            self.browser.load(QUrl('http://www.bing.com/images/search?q={}'.format(self.searchLine.text())))

    def tips(self):
        word = self.resultPage.textCursor().selectedText().lower()
        if word.isalpha():
            html = self.myDictDB.display_all(word)
            if html is None:
                return
            self.resultPage.setToolTip(html)

    def speakWord(self):
        if self.searchLine.text():
            os.system('say {}'.format(self.searchLine.text()))

    def displayPic(self):
        if 'Search for Pictures' in self.showPicBtn.text():
            self.browser.setVisible(True)
            self.showPicBtn.setText('Hide Pictures')
        else:
            self.browser.setVisible(False)
            self.showPicBtn.setText('Search for Pictures')

    def loadToday(self):
        if self.todayLine.text().isdigit():
            self.myDictDB.create_today_list(int(self.todayLine.text()))
            self.get_word()

    def word_passed(self):
        if self.the_word:
            self.myDictDB.word_passed(self.the_word, 0)
            self.get_word()

    def get_word(self):
        if self.the_word:
            self.previousLabel.setText('previous : <b><i>{}</i></b>'.format(self.the_word))
        self.the_word = self.myDictDB.get_a_word()
        if self.the_word:
            self.voLabel.clear()
            # os.system('say {}'.format(self.the_word))
            self.searchLine.setText(self.the_word)
            self.search_word()
        else:
            self.voLabel.setText('<h1>You have finished today</h1>')
        self.refresh_status()

    def check_the_word(self):
        if not self.checkLine.text():
            return
        if self.checkLine.text().lower() == self.the_word.lower():
            self.myDictDB.word_passed(self.the_word)
            self.get_word()
            self.checkLine.clear()
        else:
            self.myDictDB.word_failed(self.the_word)
            self.voLabel.setText('<h1>{}</h1>'.format(self.the_word))

    def voice_hint(self):
        text = re.sub(r'[^a-zA-Z0-9]', ' ', self.myDictDB.get_hints(self.the_word))
        os.system('say {}'.format(text))

    def text_hint(self):
        text = self.myDictDB.get_hints(self.the_word)
        self.voLabel.setText('<h3>{}</h3>'.format(text))
        self.myDictDB.word_failed(self.the_word)