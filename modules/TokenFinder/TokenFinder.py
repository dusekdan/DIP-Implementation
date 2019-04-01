class TokenFinder():

    def __init__(self):
        self.dependencies = [
            {
                "depends_on": "SiteCopier",
                "dependency_type": "output",
                "is_essential": True
            }
        ]
    
    def execute(self):
        print(" TokenFinder: Executing...")
    
    def get_dependencies(self):
        return self.dependencies