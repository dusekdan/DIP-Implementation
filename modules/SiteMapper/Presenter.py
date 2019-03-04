class Presenter():

    def __init__(self):
        self.results = {}
        self.work_finished = False
        print(" Initialized SiteMapper Presenter")

    def run(self, parameters):
        print(" Presenter: Running with %s" % parameters)
        self.work_finished = True

    def has_finished(self):
        return self.work_finished
    
    def get_results(self):
        if (self.work_finished):
            return self.results
        else:
            raise ValueError("SiteMapperPresenter has not finished its working yet.")