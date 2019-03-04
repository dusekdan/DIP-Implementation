class Processor():

    def __init__(self):
        self.results = {}
        self.work_finished = False
        print(" Initialized SiteMapper Processor")

    def run(self, parameters):
        print(" Processor: Running with %s" % parameters)
        self.work_finished = True

    def has_finished(self):
        return self.work_finished
    
    def get_results(self):
        if (self.work_finished):
            return self.results
        else:
            raise ValueError("SiteMapperProcessor has not finished its working yet.")