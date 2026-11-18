from uuid import uuid1 as uuid

class Application:

    def __init__(self, **attr):
        self.id = uuid().int
        self.name = ""
        self.container = None
        self.scheduleAlgorithm = None
        self.scheduleOptions = {}
        for var, value in attr.items():
            if var in self.__dict__:
                self.__setattr__(var, value)

class Layer:

    def __init__(self, **attr):
        self.id = uuid().int
        self.size = 0
        for var, value in attr.items():
            if var in self.__dict__:
                self.__setattr__(var, value)

class Container:

    def __init__(self, **attr):
        self.id = uuid().int
        self.layers = []
        self.memory = 0
        self.ipt = 0
        self.startDelay = 0
        self.stopDelay = 0
        self.timeout = None
        self.stage = "NotFound"
        for var, value in attr.items():
            if var in self.__dict__:
                self.__setattr__(var, value)
