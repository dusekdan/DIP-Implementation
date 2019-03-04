class Collector():

    def __init__(self):
        self.results = {}
        self.work_finished = False
        print(" Initialized SiteMapper Collector")

    def run(self, parameters):
        print(" SiteMapper: Running with %s" % parameters)
        self.work_finished = True

    def has_finished(self):
        return self.work_finished
    
    def get_results(self):
        if (self.work_finished):
            return self.results
        else:
            raise ValueError("SiteMapperCollector has not finished its working yet.")