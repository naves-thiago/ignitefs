# This Python file uses the following encoding: utf-8
import sys
from PyQt5 import QtWidgets, uic

class DBEntry:
    def __init__(self, path):
        self.directory = data[path]['directory']
        self.name      = path[:path.rfind('/')]
        if self.directory:
            self.contents = data[path]['contents']
        else:
            self.size = data[path]['size']

# DB mock
data = {}
data['/'] = {'contents': ['a', 'b', 'c'], 'directory': True}
data['/a'] = {'contents': ['c', 'd', 'f'], 'directory': True}
data['/a/c'] = {'contents': ['e'], 'directory': True}
data['/a/c/e'] = {'size': 42, 'directory': False}
data['/a/d'] = {'size': 8, 'directory': False}
data['/b'] = {'size': 1333, 'directory': False}
data['/c'] = {'contents': [], 'directory': True}
data['/a/f'] = {'contents': [], 'directory': True}

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
        return DBEntry(path)

    def getFileContents(self, path):
        # MOCK (will load from a different cache)
        print("Read %s" % (path))
        return "Contents of %s" % (path)

    def saveFile(self, path, contents):
        pass

    def createFile(self, path, contents):
        self.saveFile(path, contents)
        # add to directory
        # MOCK
        bar = path.rfind('/')
        directory = path[:bar]
        if directory == '':
            directory = '/'
        name = path[bar+1:]
        data[directory]['contents'].append(name)
        data[path] = {'size': 0, 'directory': False}


class MainWindow:
    def __init__(self, db):
        self.window = uic.loadUi("mainwindow.ui")
        self.fileTree = self.window.fileTree
        self.fileTree.itemExpanded.connect(self._fileTreeItemExpanded)
        self.fileTree.itemClicked.connect(self._fileTreeItemClicked)
        self.fileContents = self.window.fileContents
        self.window.saveFile.clicked.connect(self._saveFileClick)
        self.window.newFile.clicked.connect(self._newFileClick)
        self.window.newDirectory.clicked.connect(self._newDirectoryClick)

        self.loaded = {} # Lists loaded directories and files
        self.db = db
        self.rootItem = self.addTopEntry('/', '', True)

    def show(self):
        self.window.show()

    def _currentDirItem(self):
        ''' Returns the current selected directory. Current item if it's a directory
        or its parent otherwise '''
        selected = self.selectedItem()
        if not selected:
            return self.rootItem

        if selected.childCount() > 0:
            return selected

        return selected.parent()

    def _currentDirPath(self):
        ''' Returns the path to the current directory. If the selected item is not
        a directory, returns its parent's path '''
        return self._entryPath(self._currentDirItem())

    def _newFileClick(self):
        ok, name = nameDialog()
        if not ok:
            return
        if name == '':
            msg = QtWidgets.QMessageBox()
            msg.setText('File name cannot be empty.')
            msg.exec()
            return

        currentDir = self._currentDirPath()
        if currentDir == '/':
            self.db.createFile('/' + name, '')
        else:
            self.db.createFile(currentDir + '/' + name, '')

        # TODO check if current file was not saved
        parent = self._currentDirItem()
        if parent.isExpanded():
            self._refreshDirectory(parent)
        else:
            parent.setExpanded(True)
            # refresh is a side effect of expanding

        for i in range(parent.childCount()):
            if parent.child(i).text(0) == name:
                self.fileTree.setCurrentItem(parent.child(i))
                break

        self.window.fileContents.setPlainText('')

    def _saveFileClick(self):
        pass

    def _newDirectoryClick(self):
        pass

    def _fileTreeItemClicked(self, item, column):
        print(item.text(0))

    def _fileTreeItemExpanded(self, item):
        self._refreshDirectory(item)

    def _refreshDirectory(self, item):
        item.takeChildren()
        itemPath = self._entryPath(item)
        entries = self.db.listDirectory(itemPath)
        if itemPath == '/':
            itemPath = ''

        if len(entries) == 0:
            self.addSubEntry(item, '<empty>', '', False)

        for name in entries:
            e = self.db.getMetadata(itemPath + '/' + name)
            if e.directory:
                self.addSubEntry(item, name, '', True)
            else:
                self.addSubEntry(item, name, e.size, False)

    def _entryPath(self, item):
        if item == self.rootItem:
            return '/'

        path = "/" + item.text(0)
        parent = item.parent()
        while parent != self.rootItem:
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

    def itemIsDirectory(self, item):
        return item.childCount() > 0

    def selectedItem(self):
        return self.fileTree.currentItem()

    def addTopEntry(self, name, size, directory):
        item = self._createEntry(None, name, size, directory)
        self.fileTree.insertTopLevelItem(0, item)
        return item

    def addSubEntry(self, parent, name, size, directory):
        item = self._createEntry(parent, name, size, directory)
        parent.addChild(item)
        return item

    def addSubEntryToSelected(self, name, size, directory):
        return self.addSubEntry(self.selectedItem(), name, size, directory)

def nameDialog():
    ''' Opens a dialog requesting a name to be entered. Returns True on OK, False on cancel
    and the name typed'''
    dialog = uic.loadUi("name_dialog.ui")
    return dialog.exec() == 1, dialog.name.text()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    db = DB()
    w = MainWindow(db)
    w.show()
    app.exec()
