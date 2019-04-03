class SiteCopier():

    def __init__(self):
        self.dependencies = []
    
    def execute(self, param):
        print(" SiteCopier: Executing...")
        self.target = param
        print(" SiteCopier: Will be attacking %s" % param)

    def get_dependencies(self):
        return self.dependencies

    def get_results(self):
        return { "dummy":"results" }

    def leaves_physical_artifacts(self):
        return True