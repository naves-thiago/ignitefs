# This Python file uses the following encoding: utf-8
import sys
from PyQt5 import QtWidgets, uic

class DBEntry:
    def __init__(self, data):
        self.directory = data['directory']
        self.name      = data['name']
        if self.directory:
            self.contents = data['contents']
        else:
            self.size = data['size']

# DB mock
data = {}
data['/'] = {'name': '/', 'contents': ['a', 'b', 'c'], 'directory': True}
data['/a'] = {'name': 'a', 'contents': ['c', 'd', 'f'], 'directory': True}
data['/a/c'] = {'name': 'c', 'contents': ['e'], 'directory': True}
data['/a/c/e'] = {'name': 'e', 'size': 42, 'directory': False}
data['/a/d'] = {'name': 'd', 'size': 8, 'directory': False}
data['/b'] = {'name': 'b', 'size': 1333, 'directory': False}
data['/c'] = {'name': 'c', 'contents': [], 'directory': True}
data['/a/f'] = {'name': 'f', 'contents': [], 'directory': True}

class DB:
    def __init__(self):
        # Connect to ignite here
        pass

    def listDirectory(self, path):
        # MOCK
        print("List %s" % (path))
        return data[path]['contents']

    def getMetadata(self, path):
        # MOCK
        return DBEntry(data[path])

    def getFileContents(self, path):
        # MOCK (will load from a different cache)
        print("Read %s" % (path))
        return "Contents of %s" % (data[path]['name'])

    def saveFile(self, path, contents):
        pass

    def createFile(self, path, contents):
        self.saveFile(path, contents)
        # add to directory

class MainWindow:
    def __init__(self, db):
        self.window = uic.loadUi("mainwindow.ui")
        self.fileTree = self.window.fileTree
        self.fileTree.itemExpanded.connect(self.fileTreeItemExpanded)
        self.btnSaveFile = self.window.saveFile
        self.btnSaveFile.clicked.connect(self._saveFileClick)
        self.btnNewFile = self.window.newFile
        self.btnNewFile.clicked.connect(self._newFileClick)
        self.btnNewDirectory = self.window.newDirectory
        self.btnNewDirectory.clicked.connect(self._newDirectoryClick)

        self.loaded = {} # Lists loaded directories and files
        self.db = db
        entries = self.db.listDirectory('/')
        if len(entries) == 0:
            self.addSubEntry(item, '<empty>', '', False)

        for name in entries:
            e = self.db.getMetadata('/' + name)
            if e.directory:
                self.addTopEntry(name, '', True)
            else:
                self.addTopEntry(name, e.size, False)

    def show(self):
        self.window.show()

    def _newFileClick(self):
        pass

    def _saveFileClick(self):
        pass

    def _newDirectoryClick(self):
        pass

    def fileTreeItemExpanded(self, item):
        item.takeChildren()
        itemPath = self._entryPath(item)
        entries = self.db.listDirectory(itemPath)
        if len(entries) == 0:
            self.addSubEntry(item, '<empty>', '', False)

        for name in entries:
            e = self.db.getMetadata(itemPath + '/' + name)
            if e.directory:
                self.addSubEntry(item, name, '', True)
            else:
                self.addSubEntry(item, name, e.size, False)

    def _entryPath(self, item):
        path = "/" + item.text(0)
        parent = item.parent()
        while parent:
            path = "/" + parent.text(0) + path
            parent = parent.parent()
        return path

    def _createEntry(self, parent, name, size, directory):
        ''' Creates a tree item. For directory entries, also add a "loading..." child '''
        if directory:
            item = QtWidgets.QTreeWidgetItem(parent, [name, ""], 1)
            loading = QtWidgets.QTreeWidgetItem(item, ["loading...", ""], 1)
            item.addChild(loading)
        else:
            item = QtWidgets.QTreeWidgetItem(parent, [name, str(size)], 1)

        return item

    def addTopEntry(self, name, size, directory):
        item = self._createEntry(None, name, size, directory)
        self.fileTree.insertTopLevelItem(0, item)

    def addSubEntry(self, parent, name, size, directory):
        item = self._createEntry(parent, name, size, directory)
        parent.addChild(item)

    def addSubEntryToSelected(self, name, size, directory):
        sel = self.fileTree.currentItem()
        self.addSubEntry(self, name, size, directory)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    db = DB()
    w = MainWindow(db)
    w.show()
    app.exec()
