# This Python file uses the following encoding: utf-8
import sys
from PyQt5 import QtWidgets, uic
from pyignite import Client, datatypes, GenericObjectMeta
from collections import OrderedDict

# how many time to retry to update metadata in case of conflict
WRITE_RETRYS = 3

class ItemType:
    DIRECTORY = 1
    FILE = 2
    PLACEHOLDER = 3

class DBEntry(metaclass=GenericObjectMeta, schema=OrderedDict([
    ('directory', datatypes.BoolObject),
    ('name', datatypes.String),
    ('size', datatypes.LongObject),
    ('contents', datatypes.StringArrayObject)
    ])):
    pass

def splitNamePath(path):
    ''' Returns the parent path and file / directory name for a path '''
    bar = path.rfind('/')
    directory = path[:bar]
    if directory == '':
        directory = '/'
    name = path[bar+1:]

    return directory, name

class DB:
    def __init__(self):
        client = Client()
        client.connect('10.0.3.10', 10800)
        self.client = client

        self.fileCache = client.get_or_create_cache("files")
        self.metadataCache = client.get_or_create_cache("metadata")

        # TODO replicate:
        # from pyignite.datatypes.prop_codes import *
        # from pyignite.datatypes.cache_config import CacheMode
        # self.directoryCache = client.get_or_create_cache({
        #    PROP_NAME: 'directories',
        #    PROP_CACHE_MODE: CacheMode.REPLICATED
        #})

    def __del__(self):
        self.client.close()

    def listDirectory(self, path):
        print("List %s" % (path))
        return self.getMetadata(path).contents

    def getMetadata(self, path):
        return self.metadataCache.get(path)

    def getFileContents(self, path):
        print("Read %s" % (path))
        return self.fileCache.get(path)

    def saveFile(self, path, contents):
        self.fileCache.put(path, contents)
        fileMeta = self.getMetadata(path)
        if not fileMeta:
            fileMeta = DBEntry(False, path[path.rfind('/')+1:], 0, [])
        fileMeta.size = len(contents)
        self.metadataCache.put(path, fileMeta)

    def _addToParent(self, path):
        ''' Safely add item to parent contents with retry '''
        parent, name = splitNamePath(path)
        for x in range(WRITE_RETRYS+1):
            parentMeta = self.getMetadata(parent)
            if name in parentMeta.contents:
                return True
            newParentMeta = DBEntry(True, parentMeta.name, 0, [s for s in parentMeta.contents])
            newParentMeta.contents.append(name)
            if self.metadataCache.replace_if_equals(parent, parentMeta, newParentMeta):
                return True
        return False

    def createFile(self, path, contents):
        self.saveFile(path, contents)
        # add to directory
        directory, name = splitNamePath(path)
        dirMeta = self.getMetadata(directory)
        if not name in dirMeta.contents:
            dirMeta.contents.append(name)
            self.metadataCache.put(directory, dirMeta)

        fileMeta = DBEntry(False, name, len(contents), [])
        self.metadataCache.put(path, fileMeta)

    def createDirectory(self, path):
        parent, name = splitNamePath(path)
        parentMeta = self.getMetadata(parent)
        if name in parentMeta.contents:
            # Already exists in the parent contents
            return

        newMeta = DBEntry(True, name, 0, [])
        if not self.metadataCache.put_if_absent(path, newMeta):
            # Already exists. Add to parent
            if not self._addToParent(path):
                errorMessage('Unable to create directory')
            return

        if not self._addToParent(path):
            errorMessage('Unable to create directory')

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
        self.rootItem = self.addTopItem('/', '', ItemType.DIRECTORY)

    def show(self):
        self.window.show()

    def _currentDirItem(self):
        ''' Returns the current selected directory. Current item if it's a directory
        or its parent otherwise '''
        selected = self.selectedItem()
        if not selected:
            return self.rootItem

        if self.itemIsDirectory(selected):
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
        if self.itemIsFile(self.selectedItem()):
            path = self._entryPath(self.selectedItem())
            contents = self.fileContents.toPlainText()
            self.db.saveFile(path, contents)
            self.selectedItem().setText(1, str(len(contents)))

    def _newDirectoryClick(self):
        ok, name = nameDialog()
        if not ok:
            return
        if name == '':
            msg = QtWidgets.QMessageBox()
            msg.setText('Directory name cannot be empty.')
            msg.exec()
            return

        parentPath = self._currentDirPath()
        if parentPath == '/':
            newDirPath = '/' + name
        else:
            newDirPath = parentPath + '/' + name

        self.db.createDirectory(newDirPath)

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

    def _fileTreeItemClicked(self, item, column):
        if not self.itemIsFile(item):
            self.fileContents.setPlainText('')
            return

        path = self._entryPath(item)
        self.fileContents.setPlainText(self.db.getFileContents(path))
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
            self.addSubItem(item, '<empty>', '', ItemType.PLACEHOLDER)

        for name in entries:
            e = self.db.getMetadata(itemPath + '/' + name)
            if e.directory:
                self.addSubItem(item, name, '', ItemType.DIRECTORY)
            else:
                self.addSubItem(item, name, e.size, ItemType.FILE)

    def _entryPath(self, item):
        if item == self.rootItem:
            return '/'

        path = "/" + item.text(0)
        parent = item.parent()
        while parent != self.rootItem:
            path = "/" + parent.text(0) + path
            parent = parent.parent()
        return path

    def _createItem(self, parent, name, size, itemType):
        ''' Creates a tree item. For directory entries, also add a "loading..." child '''
        if itemType == ItemType.DIRECTORY:
            item = QtWidgets.QTreeWidgetItem(parent, [name, ""], ItemType.DIRECTORY)
            loading = QtWidgets.QTreeWidgetItem(item, ["loading...", ""], ItemType.PLACEHOLDER)
            item.addChild(loading)
        else:
            item = QtWidgets.QTreeWidgetItem(parent, [name, str(size)], itemType)

        return item

    def itemIsDirectory(self, item):
        return item.type() == ItemType.DIRECTORY

    def itemIsFile(self, item):
        return item.type() == ItemType.FILE

    def selectedItem(self):
        return self.fileTree.currentItem()

    def addTopItem(self, name, size, itemType):
        item = self._createItem(None, name, size, itemType)
        self.fileTree.insertTopLevelItem(0, item)
        return item

    def addSubItem(self, parent, name, size, itemType):
        item = self._createItem(parent, name, size, itemType)
        parent.addChild(item)
        return item

    def addSubItemToSelected(self, name, size, itemType):
        return self.addSubItem(self.selectedItem(), name, size, itemType)

def nameDialog():
    ''' Opens a dialog requesting a name to be entered. Returns True on OK, False on cancel
    and the name typed'''
    dialog = uic.loadUi("name_dialog.ui")
    return dialog.exec() == 1, dialog.name.text()

def errorMessage(msg):
    msgBox = QtWidgets.QMessageBox()
    msgBox.setText(msg)
    msgBox.exec()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    db = DB()
    w = MainWindow(db)
    w.show()
    app.exec()
