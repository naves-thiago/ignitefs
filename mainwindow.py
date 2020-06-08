# This Python file uses the following encoding: utf-8
import sys
from PyQt5 import QtWidgets, uic

class MainWindow:
    def __init__(self):
        self.window = uic.loadUi("mainwindow.ui")
        self.fileTree = self.window.fileTree
        self.fileTree.itemExpanded.connect(self.fileTreeItemExpanded)
        self.btnTop = self.window.btnTop
        self.btnTop.clicked.connect(self.btnTopClick)
        self.btnChild = self.window.btnChild
        self.btnChild.clicked.connect(self.btnChildClick)
        self.edit = self.window.edit
        self.label = self.window.label

        self.loaded = {} # Lists loaded directories and files

    def show(self):
        self.window.show()

    def btnTopClick(self):
        self.addTopEntry(self.edit.text(), 123, True)
        #self.label.setText(self.edit.text())

    def btnChildClick(self):
        sel = self.fileTree.currentItem()
        if sel:
            item = QtWidgets.QTreeWidgetItem(sel, [self.edit.text(), "bar"], 2)
            sel.addChild(item)

    def fileTreeItemExpanded(self, item):
        self.label.setText(self._entryPath(item))

    def _entryPath(self, item):
        path = "/" + item.text(0)
        parent = item.parent()
        while parent:
            path = "/" + parent.text(0) + path
            parent = parent.parent()
        return path

    def _createDirectoryEntry(self, parent, name):
        ''' Creates a directory entry, "loading..." child '''
        item = QtWidgets.QTreeWidgetItem(parent, [name, ""], 1)
        loading = QtWidgets.QTreeWidgetItem(item, ["loading...", ""], 1)
        item.addChild(loading)

    def addTopEntry(self, name, size, directory):
        item = QtWidgets.QTreeWidgetItem([name, "" if directory else str(size)], 1)
        self.fileTree.insertTopLevelItem(0, item)
        if directory:
            loading = QtWidgets.QTreeWidgetItem(item, ["loading...", ""], 1)
            item.addChild(loading)

    def addSubEntry(self, parent, name, size, directory):
        item = QtWidgets.QTreeWidgetItem(parent, [name, "" if directory else str(size)], 1)
        parent.addChild(item)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
