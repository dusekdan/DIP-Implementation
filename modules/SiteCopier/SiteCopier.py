from . import Crawler as c

class SiteCopier():

    def __init__(self):
        self.dependencies = []
        self.module_name = "SiteCopier"
        self.crawler = c.Crawler()

    def mprint(self, string):
        print(" [%s]: %s" % (self.module_name, string))

    def execute(self, param):
        self.mprint("===================================%s===================================" % self.module_name)
        self.mprint("Target acquired: %s" % param)


        self.crawler.set_target(param)
        crawling_output = self.crawler.crawl()
        self.mprint("Crawler work finished. %s" % crawling_output)


        self.mprint("===================================%s===================================" % self.module_name)

    def get_dependencies(self):
        return self.dependencies

    def get_results(self):
        return { "dummy":"results" }

    def leaves_physical_artifacts(self):
        return True