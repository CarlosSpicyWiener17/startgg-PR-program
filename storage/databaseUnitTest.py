from database import Database
from random import randint

testDictStructure1 = {
    "dictList" : (list, int),
    "dictSet" : (set, int),
    "dictDict" : (dict, None)
}

testDictStructure2 = {
    "dictList" : (list, int),
    "dictSet" : (set, int),
    "dictDict" : (dict, None),
    "id" : (None, int)
}

testDatabaseStructure = {
    "listOfValues" : (list, int),
    "setOfValues" : (set, int),
    "dict" : (dict, testDictStructure1),
    "multipleDatatypes" : (list, (int, None)),
    "scalar" : (None, int),
    "listOfDicts" : (list, testDictStructure2)
}

class testDatabase(Database):
    def __init__(self):
        super().__init__("testDatabase", testDatabaseStructure)

    def testAddToList(self):
        self._add("listOfValues", randint(0,10))
    
    def testAddToListFail(self):
        self._add("listOfValues", "Hello")

    def testAddToSet(self):
        self._add("setOfValues", randint(0,10))
    
    def testAddToSetFail(self):
        self._add("setOfValues", "Hello")
    
    def testAddToDict(self):
        self._addToDictIterable("dict", "dictList", randint(0,10))

    def testAddToDictFail(self):
        self._addToDictIterable("dict", "dictList", "Hello")

    def testAdd(self):
        print(self.activeDatabase)
        print("test7")
        self.testAddToSpecificDictInIterable()
        input()

    def testAddToSpecificDictInIterable(self):
        self._addDict("listOfDicts", {
            "dictList" : list(),
            "dictSet" : set(),
            "dictDict" : dict(),
            "id" : 3
        })

        self._addToDictInIterable("listOfDicts", "id", 3, "dictList", 8)
        self._getItemFromKeyValue("listOfDicts", "id", 4)
        result = self._getItemFromKeyValue("listOfDicts", "id", 3)

    def loadDatabase(self):
        self._load_db()

td = testDatabase()
td.loadDatabase()
td.testAdd()