class TokenFinder():

    def __init__(self):
        self.dependencies = [
            {
                "depends_on": "SiteCopier",
                "dependency_type": "output",
                "is_essential": True
            }
        ]
    
    def execute(self, param):
        print(" TokenFinder: Executing...")
        self.target = param
        print(" TokenFinder: Finalizing...")

    def get_results(self):
        return { "dummy":"results" }
    
    def get_dependencies(self):
        return self.dependencies
    
    def leaves_phisical_artifacts(self):
        return False