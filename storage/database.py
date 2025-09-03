from pickle import dump, load
from storage.errors import *
import logging
import gzip
import os

global logger
global debug
debug = False

def isScalar(subDatabase):
    return subDatabase[0] is None

def _updateDict(dictToUpdate : dict, dictToAdd : dict) -> dict:
    """
    Recursively explores dicts to fill out every branch\n
    Return the new dict\n
    Args:
        dictToUpdate: dictionary
        dictToAdd: dictionary

    Returns:
        dict: everything from dictToAdd, added to each keyValue in dictToUpdate, or added if key not existing
    """
    global debug
    try:    
        newDict = dictToUpdate
        for key, value in dictToAdd.items():
            
            if type(value) is dict:
                logger.info(f"debug dict: key: {key}, value: {value}\n")
                newValue = _updateDict(dictToUpdate[key], dictToAdd[key])
            elif type(value) is list:
                logger.info(f"debug list: key: {key}, value: {value}\n")
                toUpdateList, toAddList = dictToUpdate[key], dictToAdd[key] 
                newValue = _extendList(toUpdateList, toAddList)
            elif type(value) is set:
                logger.info(f"debug set: key: {key}, value: {value}\n")
                toUpdateSet, toAddSet = dictToUpdate[key], dictToAdd[key]
                newValue = _updateSet(toUpdateSet, toAddSet)
            else:
                newValue = value
            newDict[key] = newValue
        print("newdict", newDict)
        return newDict
    except:
        logger.error(f"error in _updateDict. dictToUpdate:{dictToUpdate}, dictToAdd:{dictToAdd}", exc_info=True)

def _updateSet(setToUpdate : set, setToAdd : set):
    try:
        newSet = setToUpdate
        newSet.update(setToAdd)
        return newSet
    except:
        logger.error(f"error in _updateSet. dictToUpdate:{setToUpdate}, dictToAdd:{setToAdd}", exc_info=True)

def _extendList(listToExtend, listToAdd):
    try:
        newList = listToExtend
        for item in listToAdd:
            foundExisting = False
            if type(item) is dict:
                if not item.get("id") is None:
                    for i, existingItem in enumerate(newList):
                        if existingItem["id"] == item["id"]:
                            foundExisting = True
                            newList[i] = _updateDict(existingItem, item)
                            break
                if not foundExisting:
                    newList.append(item)
            else:
                if item in listToExtend:
                    continue
                newValue = item
                newList.append(newValue)

        return newList
    except:
        logger.error(f"error in _extendList. dictToUpdate:\n{listToExtend}, \ndictToAdd:\n{listToAdd}", exc_info=True)

class Database:
    """
    Base database class to customize
    """
    def __init__(self, databaseFileName : str, structTemplate : dict, loggerToAdd, userDir):
        """
        Initializes the database

        Args:
        databaseFileName\t #What you want the filname to be called. Type .pkl
        structTemplate\t #structure of the database dict
        """
        global logger
        logger = loggerToAdd
        self.userDir = userDir
        self.name = databaseFileName
        self.file_path = os.path.join(userDir, databaseFileName+".pkl")
        self._structure : dict = structTemplate

    def add(self, databaseKey : str, additions):
        """
        Top level function to add items to database
        """
        global debug
        debug=False
        try:

            #Check if it exists
            databaseKeyExists = not self._structure.get(databaseKey) is None
            if not databaseKeyExists:
                raise KeyError
            subDatabase = self._structure[databaseKey]

            if type(subDatabase[1]) is dict:
                if debug:
                    logger.info(f"debug: adding in {self.name}\nAdding dicts")
                self._addDicts(databaseKey, additions)
            else:
                self._addScalars(databaseKey, additions)
        except TypeError:
            logger.error(f"{databaseKey} in {self.name} database, with additions of type {type(additions)}", exc_info=True)
        except:
            logger.error(f"Unknown in {self.name} database, with databasekey:{databaseKey}, additons of type:{type(additions)}\n{self._structure}", exc_info=True)

    def remove(self, databaseKey : str, removables):
        """
        Top level function to remove items from database
        """
        try:
            databaseKeyExists = not self._structure.get(databaseKey) is None
            if not databaseKeyExists:
                raise KeyError
            subDatabase = self._structure[databaseKey]
            if isScalar(removables):
                if subDatabase[0] is set:
                    if removables in self.activeDatabase[databaseKey]:
                        self.activeDatabase[databaseKey].remove(item)
                elif subDatabase[0] is list:
                    if item is dict:
                        for i, existingDict in self.activeDatabase[databaseKey]:
                            if item["id"] == existingDict["id"]:
                                self.activeDatabase[databaseKey].pop(i)
                                break
                    else:
                        if item in self.activeDatabase[databaseKey]:
                            self.activeDatabase[databaseKey].remove(item)
            else:
                if subDatabase[0] is set:
                    for item in removables:
                        if item in self.activeDatabase[databaseKey]:
                            self.activeDatabase[databaseKey].remove(item)
            
                elif subDatabase[0] is list:
                    for item in removables:
                        if item is dict:
                            for i, existingDict in self.activeDatabase[databaseKey]:
                                if item["id"] == existingDict["id"]:
                                    self.activeDatabase[databaseKey].pop(i)
                                    break
                        else:
                            if item in self.activeDatabase[databaseKey]:
                                self.activeDatabase[databaseKey].remove(item)
                else:
                    if type(removables) in {set, list}:
                        raise TypeError
                    if self.activeDatabase[databaseKey] == removables:
                        self.activeDatabase[databaseKey] == subDatabase[0]()
        except TypeError:
            logger.error(f"{databaseKey} in {self.name} database, with additions of type {type(removables)}", exc_info=True)
        except:
            pass

    def get(self, databaseKey : str, conditional = None):
        """
        Top level function to get items. Optional filter dict with conditional functions within
        """
        try:

            databaseKeyExists = not self._structure.get(databaseKey) is None
            if not databaseKeyExists:
                raise KeyError

            subDatabase = self._structure[databaseKey]
            if subDatabase[0] is None:
                return self._getScalar(databaseKey)
            else:
                if conditional is None:
                    return self.activeDatabase[databaseKey]
                elif not callable(conditional):
                    raise FunctionChoiceError
                else:
                    return self._getIterable(databaseKey, conditional)
        except KeyError:
            logger.error(f"Couldnt find {self.name}[{databaseKey}] with function database.get()")
        except FunctionChoiceError:
            logger.error(f"Filter didnt work in {self.name} database.get")
        except:
            logger.error(f"Error database.get with {self.name} database, with databasekey:{databaseKey}, filters:{conditional}\n{self._structure}")
            pass

    def overWrite(self, databaseKey, newSubDatabase):
        """
        Force overwrite of entire database. Used in 1 function due to necessity
        """
        if self._structure[databaseKey][0] is None:
            if type(newSubDatabase) in {set, list}:
                raise TypeError
            self.activeDatabase[databaseKey] = newSubDatabase
        else:
            if self._structure[databaseKey][0] is type(newSubDatabase):
                self.activeDatabase[databaseKey] = newSubDatabase

    def _getIterable(self, databasekey, conditional):
        """
        Get items within iterable that fulfill conditional
        """
        iterables = self._structure[databasekey][0]()
        
        if self._structure[databasekey][0] is list:
            return [item for item in self.activeDatabase[databasekey] if conditional(item)]
        elif self._structure[databasekey][0] is set:
            
            return {item for item in self.activeDatabase[databasekey] if conditional(item)}
        else:
            logger.error(f"Hmm hmm in {self.name} database", exc_info=True)

    def _addDicts(self, databaseKey : str, additions : list[dict]):
        """
        Special handling needed to update keys of dicts, if dict with id already exist
        """
        global debug
        try:
            subDatabase = self._structure[databaseKey]
            if isScalar(subDatabase):
                if type(additions) in {set, list}:
                    raise TypeError
                logger.info(f"debug: adding single dict in {self.name}\nAdding {type(additions)}")
                newDict = _updateDict(self.activeDatabase[databaseKey], additions)
                self.activeDatabase[databaseKey] = newDict
            elif subDatabase[0] is list:
                if debug:
                    logger.info(f"debug: adding dicts in {self.name}\nAdding {type(additions)}")
                if type(additions) is list:
                    newList = _extendList(self.activeDatabase[databaseKey], additions)
                else:
                    newList = _extendList(self.activeDatabase[databaseKey], [additions])
                self.activeDatabase[databaseKey] = newList
            else:
                logger.error(f"unknown in {self.name} database", additions)
            pass
        except:
            logger.error(f"Unknown in {self.name} database, with databasekey:{databaseKey}, additons of type:{type(additions)}", exc_info=True)

    

    def _addScalars(self, databaseKey : str, additions ):
        """
        Check if exists, then append the new ones.
        If scalar, overwrite
        """
        try:
            subDatabase = self._structure[databaseKey]
            if isScalar(subDatabase):
                if type(additions) in {set, list}:
                    raise TypeError
                self._addScalar(databaseKey, additions)

            elif subDatabase[0] is list:
                if not type(additions) is list:
                    self._addToList(databaseKey, [additions])
                else:
                    self._addToList(databaseKey, additions)

            elif subDatabase[0] is set:
                if not type(additions) is set:
                    self._addToSet(databaseKey, {additions})
                else:
                    self._addToSet(databaseKey, additions)
            else:
                logger.error(f"subDatabase[0] is not list or set?:\n{subDatabase[0]}")
                raise Exception
        except:
            logger.error(f"Unknown error in {self.name}[{databaseKey}] database\n_addScalars additions:\n{additions}")

    def _addScalar(self, databaseKey : str, newScalar : int | str | dict | float):
        """
        Overwrites a scalar with a new one
        """
        try:
            scalarType = self._structure[databaseKey][1]
            if not type(newScalar) is scalarType:
                raise TypeError(databaseKey, newScalar)
            self.activeDatabase[databaseKey] = newScalar
        except TypeError:
            logger.error(f"Invalid type of newScalar-{newScalar}, in database-{databaseKey} in {self.name}", exc_info=True)
        except:
            logger.error(f"Unknown error in {self.name} database, with databaseKey:{databaseKey}, newScalar:{newScalar}", exc_info=True)

    def _addToList(self, databaseKey : str, additions : list[int] | list[str] | list[dict] | list[float]):
        #Check if any additions already exist
        try:
            toAdd = []
            for item in additions:
                if not item in self.activeDatabase[databaseKey]:
                    toAdd.append(item)
            self.activeDatabase[databaseKey].extend(toAdd)
        except:
            logger.error(f"Error in {self.name} database with databasekey:{databaseKey} and additions of type:{type(additions)}")
        
    def _addToSet(self, databaseKey : str, additions : set[int] | set[str] | set[dict] | set[float]):
        try:
            toAdd = set()
            for item in additions:
                if not item in self.activeDatabase[databaseKey]:
                    toAdd.add(item)
            self.activeDatabase[databaseKey].update(toAdd)
        except:
            logger.error(f"Error in {self.name} database with databasekey:{databaseKey} and additions of type:{type(additions)}")

    def _initialiseDict(self, structure : dict):
        """
        Recursive dict creation from structure templates
        """
        newDict = dict()
        if structure is None:
            return None

        for key, value in structure.items():
            if value[0] is None:
                newDict[key] = None
            else:
                newDict[key] = value[0]()
        return newDict

    def _createStructure(self, structureTemplate : dict):
        """
        Creates the intended structure if not present

        Argument is dict in following format:
            dict: { "key" : tuple(iterable, datatype) }
        
        Any datatype dicts within has the same structure for typechecking
        """
        newDatabase = self._initialiseDict(structureTemplate)
        return newDatabase
    
    def _save_db(self):
        """
        Saves the database to file
        """
        try:
            with gzip.open(self.file_path, "wb") as databaseFile:
                dump(self.activeDatabase,databaseFile)   
                databaseFile.close()
        except:
            logger.error(f"Some error with saving in {self.name} database", exc_info=True)

    def _load_db(self):
        """
        Loads database into active memory
        """
        if os.path.exists(self.file_path) and os.path.getsize(self.file_path) > 0:
            with gzip.open(self.file_path, "rb") as databaseFile:
                self.activeDatabase = load(databaseFile)   
                databaseFile.close()

        else:
            self.activeDatabase = self._createStructure(self._structure)

