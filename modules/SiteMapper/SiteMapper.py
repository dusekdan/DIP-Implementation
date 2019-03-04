import sys
from . import Collector as c
from . import Presenter as p
from . import Processor as proc

class SiteMapper():

    def __init__(self):
        self.collector = c.Collector()
        self.presenter = p.Presenter()
        self.processor = proc.Processor()
        self.dependencies = ["Requester", ""]

    def execute(self):
        print(" SiteMapperModule: Executing...")

    def get_deps(self):
        return self.dependencies

    def check_deps(self):
        print(sys.modules.keys())