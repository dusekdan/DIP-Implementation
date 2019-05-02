from . import Crawler as c
from . import Presenter as p


class SiteCopier():


    def __init__(self):
        self.dependencies = []
        self.module_name = "SiteCopier"
        self.crawler = c.Crawler()
        self.presenter = None


    def mprint(self, string):
        """Module-specific print wrapper."""
        print(" [%s]: %s" % (self.module_name, string))


    def execute(self, param):
        self.mprint("Starting crawling operations...")
        self.mprint("Target acquired: %s" % param)

        self.crawler.set_target(param)
        self.parsible_artifacts = self.crawler.crawl()

        self.mprint("Crawler work finished. Goodbye!")


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


    def set_options(self, options):
        """Sets options for a module."""
        self.crawler.set_options(options)


    def get_presenter(self, results):
        """Prepares module's presenter with results structure."""
        self.presenter = p.Presenter(results)
        return self.presenter


    def leaves_physical_artifacts(self):
        """Does the module leave artifacts phisically on filesystem?"""
        return True