# This Python file uses the following encoding: utf-8
import sys
from PyQt5 import QtWidgets, uic

class DBEntry:
    def __init__(self, name, size, directory = False):
        self.name      = name
        self.size      = size
        self.directory = directory

class DBDirectory(DBEntry):
    def __init__(self, name, contents):
        super().__init__(name, 0, True)
        self.contents = contents

# DB mock
data = {}
data['/'] = DBDirectory('/', ['a', 'b'])
data['/a'] = DBDirectory('a', ['c', 'd'])
data['/a/c'] = DBDirectory('c', ['e'])
data['/a/c/e'] = DBEntry('e', 42)
data['/a/d'] = DBEntry('d', '8')
data['/b'] = DBEntry('b', '1333')

class DB:
    def __init__(self):
        # Connect to ignite here
        pass

    def listDirectory(self, path):
        # MOCK
        print("List %s" % (path))
        return data[path].contents

    def getMetadata(self, path):
        # MOCK
        return data[path]

    def getFileContents(self, path):
        # MOCK (will load from a different cache)
        print("Read %s" % (path))
        return "Contents of %s" % (data[path].name)

class MainWindow:
    def __init__(self, db):
        self.window = uic.loadUi("mainwindow.ui")
        self.fileTree = self.window.fileTree
        self.fileTree.itemExpanded.connect(self.fileTreeItemExpanded)
        self.btnSaveFile = self.window.saveFile
        self.btnSaveFile.clicked.connect(self.saveFileClick)
        self.btnNewFile = self.window.newFile
        self.btnNewFile.clicked.connect(self.newFileClick)
        self.edtFileName = self.window.fileName
        self.edtFileContents = self.window.fileContents

        self.loaded = {} # Lists loaded directories and files
        self.db = db
        entries = self.db.listDirectory('/')
        for name in entries:
            e = self.db.getMetadata('/' + name)
            if e.directory:
                self.addTopEntry(name, '', True)
            else:
                self.addTopEntry(name, e.size, False)

    def show(self):
        self.window.show()

    def newFileClick(self):
        pass

    def saveFileClick(self):
        pass

    def fileTreeItemExpanded(self, item):
        item.takeChildren()
        itemPath = self._entryPath(item)
        entries = self.db.listDirectory(itemPath)
        for name in entries:
            e = self.db.getMetadata(itemPath + '/' + name)
            if e.directory:
                self.addSubEntry(item, name, 0, True)
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
