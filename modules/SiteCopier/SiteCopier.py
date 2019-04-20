from . import Crawler as c


class SiteCopier():

    def __init__(self):
        self.dependencies = []
        self.module_name = "SiteCopier"
        self.crawler = c.Crawler()

    def mprint(self, string):
        """Module-specific print wrapper."""
        print(" [%s]: %s" % (self.module_name, string))

    def execute(self, param):
        self.mprint("===================================%s===================================" % self.module_name)
        self.mprint("Target acquired: %s" % param)

        self.crawler.set_target(param)
        self.parsible_artifacts = self.crawler.crawl()
        self.mprint("Crawler work finished.")

        self.mprint("===================================%s===================================" % self.module_name)

    def get_dependencies(self):
        """Provides information about the module's dependency requirements."""
        return self.dependencies

    def get_results(self):
        """Provides module artifacts back to module launcher to be shared."""
        return {
            "nonparsable": self.parsible_artifacts,
            "parsable": {
                'anyProcessor': self.parsible_artifacts
            }
        }

    def leaves_physical_artifacts(self):
        """Does the module leave artifacts phisically on filesystem?"""
        return True