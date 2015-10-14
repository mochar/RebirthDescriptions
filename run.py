"""
"""
import sys
import sqlite3
from collections import defaultdict

from PySide import QtGui, QtCore

from mainwindow import Ui_MainWindow


class Database:
    def __init__(self, dbname):
        self.conn = sqlite3.connect(dbname)
        self.cur = self.conn.cursor()

    def table(self, table_name):
        self.cur.execute('SELECT * FROM {}'.format(table_name))
        return self.cur.fetchall()

    def item(self, itemID):
        self.cur.execute('SELECT * FROM ITEM WHERE ID = ?', [itemID])
        _, title, pickup, description, _ = self.cur.fetchone()
        return (title, pickup, description)

    def __del__(self):
        self.conn.close()


class MainWindow(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUi()
        self.database = Database('./items.db')

        # File stuff
        self.logFile = '/home/mochar/.local/share/binding of isaac rebirth/log.txt'
        with open(self.logFile, 'r') as f:
            self.onByte = f.seek(0, 2)
        self.fileWatcher = QtCore.QFileSystemWatcher([self.logFile])
        self.fileWatcher.fileChanged.connect(self.handleFileChange)

    def initUi(self):
        self.setupUi(self)
        self.setFixedSize(350, 450)
        self.setWindowTitle('rebirth Item Descriptions')

        # Handle events
        self.closeButton.clicked.connect(self.close)
        #self.minButton.clicked.connect(self.hide)
        self.nextItemButton.clicked.connect(self.nextItem)
        self.prevItemButton.clicked.connect(self.prevItem)

        # Set the background image.
        background = QtGui.QPixmap('./resources/background.png')
        palette = QtGui.QPalette()
        palette.setBrush(QtGui.QPalette.Background, background)
        self.setPalette(palette)

    def handleFileChange(self, logFile):
        with open(logFile, 'r') as f:
            f.seek(self.onByte)
            for line in f:
                if 'Level::Init m_Stage' in line:  # New level.
                    self.handleNewLevel(int(line.split()[2].split(',')[0]))
                elif 'Adding collectible' in line:  # Picked up item.
                    self.handleNewItem(int(line.split()[2]))
            self.onByte = f.tell()

    def handleNewLevel(self, level):
        self.level = level
        if level == 1:  # Started a new run.
            self.pickedUpItems = defaultdict(list)  # New run, new items.

    def handleNewItem(self, itemID):
        ''' TODO: take run into account in self.pickedUpItems? '''
        self.pickedUpItems[self.level].append(itemID)
        self.updateItem(itemID)

    #--- GUI stuff
    def updateItem(self, itemID):
        title, pickup, description = self.database.item(itemID)
        self.titleLabel.setText(title)
        self.pickupLabel.setText(pickup)
        #self.itemImage.setPixmap(QtGui.QPixmap('resources/items/{}.png'.format(itemID.zfill(3))))
        self.itemImage.setPixmap(QtGui.QPixmap('resources/items/{}.png'.format(itemID)))
        self.descriptionLabel.setText(description)
        self.idLabel.setText(str(itemID))

        if len(self.pickedUpItems[self.level]) > 1:
            self.prevItemButton.enable()

    def nextItem(self):
        items = self.pickedUpItems[self.level]
        newIndex = items.index(int(self.id.text())) + 1
        if newIndex == len(items)-1:
            self.nextItemButton.setDisabled(True)
        self.prevItemButton.setEnabled(True)
        self.updateItem(items[newIndex])

    def prevItem(self):
        items = self.pickedUpItems[self.level]
        newIndex = items.index(int(self.id.text())) - 1
        if newIndex == 0:
            # First item, no previous item, so disable previous item button.
            self.prevItemButton.setDisabled(True)
        self.nextItemButton.setEnabled(True)
        self.updateItem(items[newIndex])

    #--- Window handling
    def mousePressEvent(self, event):
        self.offset = event.pos()

    def mouseMoveEvent(self, event):
        newX = event.globalX() - self.offset.x()
        newY = event.globalY() - self.offset.y()
        self.move(newX, newY)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
    window.show()
    sys.exit(app.exec_())
