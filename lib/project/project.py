import os
import yaml
from ..utils.yaml_parser import YamlParser
from ..variable.variable import Variable

class Project():
    def __init__(self, name, path, db=None):
        self.defaultProjectFile = "dude.yml"
        self.name = name
        self.gitHooks = []
        self.path = path
        self.variables = {}
        self.workflow = {}
        self.initialized = False
        self.filePath = "/".join([self.path, self.defaultProjectFile])
        self.isFileCreated = os.path.isfile(self.filePath)
        self.db = None
        self.id = None

        if db is not None:
            self.db = db
            self.id = self.existsInDb(self.db)

        if self.isFileCreated:
            self.discover()

    def __repr__(self):
        line = ''
        line += 'name: '  + self.name + '\n'
        line += 'path: ' + self.path + '\n'
        if len(self.gitHooks) > 0:
            line += 'git hooks: \n'
            for hook in self.gitHooks:
                line += '\t' +  hook + '\n'

        if len(self.variables) > 0:
            line += 'variables: \n'
            for var in self.variables:
                line += '\t {}: {}\n'.format(var, self.variables[var])

        if len(self.workflow) > 0:
            print (self.workflow)

        return line

    def checkStatus(self):
        rewrite = self.variablesChanged()
        if rewrite:
            # update scripts
            print ('scripts need to be updated')

    def getProject(self):
        project = {
            "name": self.name,
            "path": self.path
        }

        if len(self.variables) > 0:
            project['variables'] = self.variables

        if len(self.workflow) > 0:
            project['workflow'] = self.workflow

        return project

    def existsInDb(self, db):
        query = 'select id from projects where path = "{}"'.format(self.path)
        result = db.fetch(query)

        if len(result) > 0:
            id  = result[0][0]
            return id
        else:
            return None

    def readFromDb(self, db):
        if not self.initialized:
            print ('Project is not initialized yet')
            return False

        query = """ select * from projects where path = '{}' """.format(self.path)
        return db.fetch(query)

    def createToDb(self, db):
        project = {
            "name": self.name,
            "path": self.path
        }

        id = db.insert('projects', project)
        self.id = id

        for variable in self.variables:

            bundle = {
                "title": variable,
                "value": self.variables[variable],
                "project": str(id)
            }

            db.insert('variables', bundle)

    def saveToDb(self, db):
        pass

    def discover(self):
        filePath = "/".join([self.path, self.defaultProjectFile])

        with open(filePath, "r") as stream:
            file = yaml.load(stream)

        if 'name' in file:
            self.name = file["name"]

        if 'hooks' in file:
            self.gitHooks = file["hooks"]

        if 'variables' in file:
            for key in file['variables']:
                self.variables[key] = file['variables'][key]

        if 'workflow' in file:
            if 'init' in file['workflow']:
                self.workflow['init'] = file['workflow']['init']

            if 'open' in file['workflow']:
                self.workflow['open'] = file['workflow']['open']

            if 'close' in file['workflow']:
                self.workflow['close'] = file['workflow']['close']

            if 'clean' in file['workflow']:
                self.workflow['clean'] = file['workflow']['clean']

        print (self)
        self.initialized = True

    def create(self):
        # if not self.isFileCreated:
        data = self.getProject()
        yaml = YamlParser()
        yaml.write(path=self.filePath, content=data)

    def readFile(self):
        print  ('reading the configuration file')

    def saveFile(self):
        data = self.getProject()
        yaml = YamlParser()
        yaml.write(path=self.filePath, content=data)

    def save(self, db):
        # check if exists in DB
        if not self.initialized:
            print('The project is not ready yet')
            return False


        id = self.existsInDb(db)
        if id is None:
            self.createToDb(db)
        else:
            self.saveToDb(db)

        # for variable in self.variables:
        #
        #     bundle = {
        #         "title": variable.name,
        #         "value": variable.value,
        #         "project": str(projectId)
        #     }
        #     db.insert('variables', bundle)
        #
        # for hook in self.gitHooks:
        #     bundle = {
        #         "hook": str(1),
        #         "project": str(projectId)
        #     }
        #
        #     db.insert('githook_assignments', bundle)

    def addVariable(self, name, value):
        self.variables[name] = value
        self.create()

    def removeVarible(self, name):
        self.variables[name] = None

    def setup(self):
        pass

    def variablesChanged(self, database=None):
        db = None
        if database is not None:
            db = database
        elif self.db is not None:
            db = self.db
        else:
            raise Exception()

        query = 'select title, value from variables where id = {}'.format(self.id)
        dbVars = db.fetch(query)

        rewrite = False

        for variable in dbVars:
            dbKey = variable[0]
            dbValue = variable[1]

            if not self.variables[dbKey] or self.variables[dbKey] is None:
                query = 'delete from variables where project = {} and title = {}'.fromat(
                    self.id, dbKey)
            elif self.variables[dbKey] != dbValue:
                query = '''update variables set value = '{}' where project = {}
                        and title = '{}' '''.format(
                        dbValue,
                        self.id, dbKey)

                db.execute(query)
                rewrite = True

        query = 'select title, value from variables where project = {}'.format(self.id)

        return rewrite
