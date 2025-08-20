from pickle import dump, load
from storage.errors import *
import logging
import gzip
import os

logging.basicConfig(
    filename="error.log",  # or just leave it blank to log to console
    level=logging.ERROR,   # Only log warnings/errors
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def getAllowedDatatypes(subDatabase):
    allowedDatatypes = set()
    #Check if the structure is iterable, meaning it has multiple valid datatypes
    if type(subDatabase[1]) is str:
        allowedDatatypes.add(str)
    else:
        try:
            for datatype in subDatabase[1]:
                allowedDatatypes.add(datatype)
        except:
            allowedDatatypes.add(subDatabase[1])
    return allowedDatatypes

class Database:
    """
    Base database class to customize
    """
    def __init__(self, databaseFileName, structTemplate ):
        """
        Initializes the database

        Args:
        databaseFileName\t #What you want the filname to be called. Type .pkl
        structTemplate\t #structure of the database dict
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.file_path = os.path.join(script_dir, databaseFileName+".pkl")
        self._structure : dict = structTemplate

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

    def _initialiseDict(self, structure):
        """
        Recursive dict creation from structure templates
        """
        newDict = dict()
        if structure is None:
            return None
        for key, value in structure.items():
            if value[0] is None:
                newDict[key] = None
            elif value[0] is dict:
                newDict[key] = self._initialiseDict(value[1])
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
    
    def _add(self, databaseKey, addition):
        """
        Adds a single item to the key of the active database.
        Only works on iterable sub-databases.
        Use _overwrite for scalars.
        Provides necessary function + typechecking per iterable and datatype
        """
        try:
            if self._structure.get(databaseKey) is None:
                raise KeyError
            
            subDatabase = self._structure[databaseKey]
            allowedDatatypes = getAllowedDatatypes(subDatabase)
            if type(addition) not in allowedDatatypes:
                raise TypeError(addition)

            #Do correct based on method available
            if hasattr(subDatabase[0], "append"):
                self.activeDatabase[databaseKey].append(addition)
            elif hasattr(subDatabase[0], "add"):
                self.activeDatabase[databaseKey].add(addition)
            else:
                raise KeyError
        except (KeyError, TypeError, InnerKeyError, InnerTypeError):
            logging.error("_add error", exc_info=True)
        except:
            logging.error("Unknown _add error", exc_info=True)

    def _addDict(self, databaseKey, addition):
        """
        Adds a single dict to the key of the active database.
        Only works on iterable sub-databases.
        Use _overwrite for scalars.
        Provides necessary function + typechecking per iterable and datatype
        """
        try:
            if self._structure.get(databaseKey) is None:
                raise KeyError
            if type(addition) is not dict:
                raise FunctionChoiceError
            
            subDatabase = self._structure[databaseKey]

            #Do correct based on method available
            if hasattr(subDatabase[0], "append"):
                self.activeDatabase[databaseKey].append(addition)
            elif hasattr(subDatabase[0], "add"):
                self.activeDatabase[databaseKey].add(addition)
            else:
                raise KeyError
        except (KeyError, TypeError, InnerKeyError, InnerTypeError):
            logging.error("_addDict error", exc_info=True)
        except:
            logging.error("Unknown _addDict error", exc_info=True)
        
    def _updateMultipleDict(self, key, identifierKey, additions):
        try:
            if self._structure.get(key) is None:
                raise KeyError
            subDatabase = self._structure[key]

            if type(additions) is dict:
                raise FunctionChoiceError

            if len(additions) < 1:
                raise Exception
            
            dictStructure = subDatabase[1]
            if dictStructure.get(identifierKey) is None:
                raise InnerKeyError
            
            #Check for correct types
            allowedDatatypesItems = getAllowedDatatypes(subDatabase)
            if not type(additions) in allowedDatatypesItems:
                raise TypeError
            if type(additions) is not subDatabase[0]:
                raise TypeError

            toAdd = additions

            #Do correct based on method available
            for existingItem in self.activeDatabase[key]:
                for addition in additions:
                    if existingItem[identifierKey] == addition[identifierKey]:
                        break
                if hasattr(toAdd, "append"):
                    toAdd.append(addition)
                elif hasattr(toAdd, "add"):
                    toAdd.add(addition)
                else:
                    raise KeyError
            
            self._overwrite(key, toAdd)

        except (KeyError, TypeError, InnerKeyError, FunctionChoiceError, InnerTypeError):
            logging.error("_addMultiple error", exc_info=True)
        except:
            logging.error("Unknown _addMultiple error", exc_info=True)

    def _addMultiple(self, key, additions):
        """
        Adds a single item to the key of the active database.
        Provides necessary function + typechecking per iterable and datatype
        """
        try:
            if self._structure.get(key) is None:
                raise KeyError
            subDatabase = self._structure[key]

            if type(additions) is dict:
                raise FunctionChoiceError

            if len(additions) < 1:
                raise Exception
            #Check for correct types
            allowedDatatypesItems = getAllowedDatatypes(subDatabase)
            if additions[0] not in allowedDatatypesItems:
                raise TypeError
            if type(additions) is not subDatabase[0]:
                raise TypeError

            #Do correct based on method available
            for addition in additions:
                self._add(key, addition)
        except (KeyError, TypeError, InnerKeyError, FunctionChoiceError, InnerTypeError):
            logging.error("_addMultiple error", exc_info=True)
        except:
            logging.error("Unknown _addMultiple error", exc_info=True)
    
    def getDatabase(self):
        """
        Returns entire database
        """
        return self.activeDatabase

    def _getItems(self, databaseKey):
        """
        Gives all items from within a subdatabase
        """
        if self._structure.get(databaseKey) is None:
            raise KeyError
        
        return self.activeDatabase[databaseKey]

    def _getItemFromKeyValue(self, databaseKey, valueKey, value) -> any:
        """
        Gives first item which matches value in database[databaseKey][x][valueKey]
        """
        try:
            if self._structure.get(databaseKey) is None:
                raise KeyError(f"Wrong key: {databaseKey}")
            
            subDatabase = self._structure[databaseKey]
            #Only for dicts
            if type(subDatabase[0]) is not type(dict):
                raise TypeError
            
            #If key nonexist
            if subDatabase[1].get(valueKey) is None:
                raise InnerKeyError(f"Wrong key: {valueKey} in {subDatabase}")
            success = False

            #Loop through. Give success if looped through without errors. Return item | None
            try:
                for item in self.activeDatabase[databaseKey]:
                    print(item, value)
                    if item[valueKey] == value:
                        retrievedItem = item
                        break
                success = True
            except:
                success, retrievedItem = False, None
            if not success:
                raise
            return retrievedItem
        except (TypeError, InnerTypeError, KeyError, InnerKeyError):
            logging.error("Error within _getItemFromKeyValue", exc_info=True)
        except:
            logging.error("Unknown error within _getItemFromkeyValue", exc_info=True)
        return None

        
    def _overwrite(self, databaseKey, newSubDatabase):
        """
        Overwrites entire key. Be certain in what function you use this in
        """
        try:
            if self._structure.get(databaseKey) is None:
                raise KeyError(f"Wrong key: {databaseKey}")
            subDatabase = self._structure[databaseKey]

            if subDatabase[0] is not type(newSubDatabase):
                raise TypeError
            
            self.activeDatabase[databaseKey] = newSubDatabase
        except (KeyError, InnerKeyError, TypeError, InnerTypeError):
            logging.error("Issue with _overwrite", exc_info=True)
        except:
            logging.error("Unknown issue with _overwrite", exc_info=True)


    def _conditionalGetDictItems(self, databaseKey, valueKey, condition):
        try:
            #Check subdatabase exists
            if self._structure.get(databaseKey) is None:
                raise KeyError(f"Wrong key: {databaseKey}")
            subDatabase = self._structure[databaseKey]
            
            #Check if key is correct assuming the calling function is setup correctly
            if type(subDatabase[0]) is not type(dict):
                raise TypeError(f"Wrong type of target: {subDatabase[0]}")
            if subDatabase[1].get(valueKey) is None:
                raise InnerKeyError(f"Wrong key: {valueKey}")
            
            #Check if condition is a function
            if not callable(condition):
                raise ConditionError
            
            retrievedItems = []

            #Check if the structure is iterable, meaning it has multiple valid datatypes        
            for item in self.activeDatabase[databaseKey]:
                if condition(item[valueKey]):
                    retrievedItems.append(item)
        except (KeyError, InnerKeyError, TypeError, InnerTypeError):
            logging.error("Issue with _conditionalGetDictItems", exc_info=True)
        except ConditionError:
            logging.error("Condition was not callable", exc_info=True)
        return retrievedItems

    

    def _remove(self, databaseKey, removal):
        """
        Adds a single item to the key of the active database.
        Provides necessary function + typechecking per iterable and datatype
        """

        if self._structure.get(databaseKey) is None:
            raise KeyError(f"Error with key: {databaseKey}")
        
        subDatabase = self._structure[databaseKey]
        
        allowedDatatypes = getAllowedDatatypes(subDatabase)
        
        if type(removal) not in allowedDatatypes:
            raise TypeError
        
        #Do correct based on method available
        if hasattr(subDatabase, "remove"):
            self.activeDatabase[databaseKey].remove(removal)
        elif hasattr(subDatabase, "pop") and type(subDatabase) is type(dict):
            self.activeDatabase[databaseKey].pop(removal)     #remove assuming removal is key instead 
        else:
            raise Exception
        

    def _removeDict(self, databaseKey, identifierKey, identifierValue):
        """
        Removes an item based on key, value pair within a dict item
        """

        if self._structure.get(databaseKey) is None:
            raise KeyError(f"Error with key: {databaseKey}")
        
        subDatabase = self._structure[databaseKey]
        dictStructure = subDatabase[1]
        if dictStructure.get(identifierKey) is None:
            raise KeyError(f"Error with key: {identifierKey}")
        
        allowedDatatypes = getAllowedDatatypes(subDatabase)
        
        if type(identifierValue) not in allowedDatatypes:
            raise TypeError

        try:
            for item in self.activeDatabase[databaseKey]:
                if item[identifierKey] == identifierValue:
                    success = True
                    self.activeDatabase[databaseKey].remove(item)
            success = True
        except:
            success = False
        if success:
            return True
        return False
        
    def _addToIterableInDict(self, databaseKey, changeKey, addition):
        try:
            #Check if databaseKey exists
            if self._structure.get(databaseKey) is None:
                raise KeyError(f"Error with key: {databaseKey}")
            
            subDatabase = self._structure[databaseKey]
            if subDatabase[0] is not dict:
                raise InnerTypeError
            
            subDictStructure = subDatabase[1]
            if subDictStructure.get(changeKey) is None:
                raise KeyError(f"Error with key: {changeKey}")

            allowedDatatypesChange = getAllowedDatatypes(subDictStructure[changeKey])
            if not type(addition) in allowedDatatypesChange:
                print(allowedDatatypesChange, type(addition))
                raise TypeError

            if hasattr(self.activeDatabase[databaseKey][changeKey], "append"):
                self.activeDatabase[databaseKey][changeKey].append(addition)
            if hasattr(self.activeDatabase[databaseKey][changeKey], "add"):
                self.activeDatabase[databaseKey][changeKey].add(addition)
        
        except (KeyError, InnerKeyError, TypeError, InnerTypeError):
            logging.error("Complicated error", exc_info=True)
        except:
            logging.error("Unknown error", exc_info=True)

    def _addToDictInIterable(self, databaseKey, identifierKey, identifierValue, changeKey, addition):
        try:
            #Check if databaseKey exists
            if self._structure.get(databaseKey) is None:
                raise KeyError(f"Error with key: {databaseKey}")
            
            subDatabase = self._structure[databaseKey]
            if type(subDatabase[1]) is not dict:
                raise FunctionChoiceError(f"database[{databaseKey}] values are not of type {type(subDatabase[1])}")
            
            subDictStructure = subDatabase[1]
            if subDictStructure[identifierKey] is None or subDictStructure[changeKey] is None:
                raise KeyError(f"Error with key: {identifierKey if subDictStructure[identifierKey] is None else changeKey}")
            
            allowedDatatypesChange = getAllowedDatatypes(subDictStructure[changeKey])
            allowedDatatypesIdentifier = getAllowedDatatypes(subDictStructure[identifierKey])
            if not (type(addition) in allowedDatatypesChange) or not (type(identifierValue) in allowedDatatypesIdentifier):
                wrongTypeValue = addition in allowedDatatypesChange and addition or identifierValue
                wrongType = addition in allowedDatatypesChange and type(addition) or type(identifierValue)
                correctTypes = addition in allowedDatatypesChange and allowedDatatypesChange or allowedDatatypesIdentifier
                if len(correctTypes) > 1:
                    types = ""
                    for typeVar in correctTypes:
                        types += str(typeVar) + ", "
                else:
                    types = str(list(correctTypes)[0])
                raise TypeError(
                    f"""Wrong type: {wrongTypeValue} of type {wrongType} should be of type {types}""")
            a = dict()

            for dictionary in self.activeDatabase[databaseKey]:
                if dictionary[identifierKey] == identifierValue:
                    if hasattr(dictionary[changeKey], "append"):
                        dictionary[changeKey].append(addition)
                    if hasattr(dictionary[changeKey], "add"):
                        dictionary[changeKey].add(addition)
        except (KeyError, InnerKeyError, TypeError, InnerTypeError):
            logging.error("Complicated error", exc_info=True)
        except:
            logging.error("Unknown error", exc_info=True)

    def _addMultipleToDictIterable(self, databaseKey, identifierKey, identifierValue, changeKey, additions, types):
        try:
            #Check if databaseKey exists
            if self._structure.get(databaseKey) is None:
                raise KeyError(f"Error with key: {databaseKey}")
            
            subDatabase = self._structure[databaseKey]
            if subDatabase[0] is not dict:
                raise FunctionChoiceError
            
            subDictStructure = subDatabase[1]
            if subDictStructure[identifierKey] is None or subDictStructure[changeKey] is None:
                raise KeyError(f"Error with key: {identifierKey if subDictStructure[identifierKey] is None else changeKey}")
            
            allowedDatatypesChange = getAllowedDatatypes(subDictStructure[changeKey])
            allowedDatatypesIdentifier = getAllowedDatatypes(subDictStructure[identifierKey])
            for typeVar in types:
                if not typeVar in allowedDatatypesChange:
                    raise InnerTypeError
            if not type(identifierValue) in allowedDatatypesIdentifier:
                raise TypeError
            if type(additions) is not subDatabase[0]:
                raise TypeError

            for dictionary in self.activeDatabase[databaseKey]:
                if dictionary[identifierKey] == identifierValue:
                    if hasattr(dictionary[changeKey], "extend"):
                        dictionary[changeKey].extend(additions)
                    if hasattr(dictionary[changeKey], "update"):
                        dictionary[changeKey].update(additions)
        except (KeyError, InnerKeyError, TypeError, InnerTypeError):
            logging.error("Complicated error", exc_info=True)
        except:
            logging.error("Unknown error", exc_info=True)

    def _overwriteDictItem(self, databaseKey, identifierKey, identifierValue, changeKey, newValue):
        try:
            #Check if databaseKey exists
            if self._structure.get(databaseKey) is None:
                raise KeyError(f"Error with key: {databaseKey}")
            
            subDatabase = self._structure[databaseKey]
            if subDatabase[0] is not dict:
                raise InnerTypeError
            
            subDictStructure = subDatabase[1]
            if subDictStructure[identifierKey] is None or subDictStructure[changeKey] is None:
                raise KeyError(identifierKey if subDictStructure[identifierKey] is None else changeKey)
            
            allowedDatatypesChange = getAllowedDatatypes(subDictStructure[changeKey])
            allowedDatatypesIdentifier = getAllowedDatatypes(subDictStructure[identifierKey])
            if not type(newValue) in allowedDatatypesChange or not type(identifierValue) in allowedDatatypesIdentifier:
                raise TypeError

            for dictionary in self.activeDatabase[databaseKey]:
                if dictionary[identifierKey] == identifierValue:
                    dictionary[changeKey] = newValue
        except (KeyError, InnerKeyError, TypeError, InnerTypeError):
            logging.error("Complicated error", exc_info=True)
        except:
            logging.error("Unknown error", exc_info=True)
                

    def _updateItemKey(self, databaseKey, identifierKey, identifierValue, valueToChangeKey, newValue):
        """
        Updates an items valueToChangeKey into newValue. Item is found based on identifierKey, identifierValue
        """
        try:
            #Check if databasekey exists
            if self._structure.get(databaseKey) is None:
                raise KeyError
            
            subDatabase = self._structure[databaseKey]

            if type(subDatabase[0]) is not type(dict):
                raise InnerTypeError(f"database[{databaseKey}] is not dict")
            
            dictStructure = subDatabase[1]
            
            if dictStructure.get(identifierKey) is None:
                raise InnerKeyError(f"{identifierKey} is not in database[{databaseKey}]")
            
            dictSubDatabaseIdentifier = dictStructure[identifierKey]
            allowedIdentifierDatatypes = getAllowedDatatypes(dictSubDatabaseIdentifier)
            if not type(identifierValue) in allowedIdentifierDatatypes:
                raise InnerTypeError(f"{identifierValue} of type {type(identifierValue)} should be {allowedIdentifierDatatypes}")
            
            dictSubDatabaseChange = dictStructure[valueToChangeKey]
            allowedChangeDatatypes = getAllowedDatatypes(dictSubDatabaseChange)
            if not type(newValue) in allowedChangeDatatypes:
                raise InnerTypeError(f"{newValue} of type {type(newValue)} should be {allowedChangeDatatypes}")
            
            try:
                for item in self.activeDatabase[databaseKey]:
                    if item[identifierKey] == identifierValue:
                        item[valueToChangeKey] = newValue
                        break
                success = True
            except:
                success = False
            if not success:
                raise UpdateError(identifierKey=identifierKey, identifierValue=identifierValue, valueToChangeKey=valueToChangeKey, newValue=newValue)
        except (TypeError, InnerTypeError, KeyError, InnerKeyError):
            logging.error("Complicated error", exc_info=True)
        except UpdateError:
            print("Error when updating dict")
        except:
            logging.error("Unknwon error", exc_info=True)
        
    def _save_db(self):
        """
        Saves the database to file
        """
        try:
            with gzip.open(self.file_path, "wb") as databaseFile:
                dump(self.activeDatabase,databaseFile)   
                databaseFile.close()
        except:
            logging.error("Some error with saving", exc_info=True)