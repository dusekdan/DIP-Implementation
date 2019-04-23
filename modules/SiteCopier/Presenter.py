from core import constants as Consts
from core import utils as utils
from core import config as cfg


class Presenter():


    def __init__(self, results):
        self.module_name = "SiteCopier"

        """Is media data generated as part of the presentation?"""
        self._generates_media = False
        
        """Determines how high will the output be in final report."""
        self.importance = -1

        """Minimum level of importance for data to be reported, default all."""
        self.information_level = "LOW"

        """Provides access to module-run results."""
        self.results = results

        """Default value for presenting style."""
        self.style = Consts.DEFAULT_PRESENTER_STYLE


    def present_content(self, presentation_style):
        """
        Returns content ready for presentation in style specified by parameter.
        """
        self.style = presentation_style
        return {
            "content": self.get_content(),
            "description": self.get_description()
        }

    
    def get_content(self):
        """
        Assembles content to be returned from the presenter. In the future,
        this might be the place where a decision about style-specific 
        assembler method call will be made based on self.style.
        """
        results = self.results['SiteCopier']['results']['nonparsable'][0]

        content = Consts.EMPTY_STRING
        if len(results) > 0:
            # There are data to be presented
            content += self.get_requests_overview(results)
        else:
            content += self.get_no_output()
        
        return content


    def get_requests_overview(self, results):
        """
        Presents information about requests that were made during SiteCopier's
        operations.
        """
        number_of_crawled_requests = len(results["crawledUrls"])
        number_of_failed_requests = len(results["failedUrls"])
        number_of_filtered_requests = len(results["filteredUrls"])
        if self.style == 'BWFormal':
            cnt = """
            <p>SiteCopier issued <b>%s requests</b> against the target 
            application, out of which <b>%s</b> failed. Additionally, there 
            were <b>%s</b> links which pointed outside the target and they were
            not requested.</p>
            """ % (
                number_of_crawled_requests,
                number_of_failed_requests,
                number_of_filtered_requests
            )


            # Print out table of failed, filtered and requested links
            table_1 = """
            <h5>Failed & Filtered targets</h5>
            <table>"""

            if number_of_failed_requests > 0:
                table_1 += """
                <tr>
                    <th>Requests to following URLs failed to reach the target</th>
                </tr>
                <tr>
                """
                for url in results["failedUrls"]:
                    table_1 += "<tr><td>%s</td></tr>" % utils.encode_for_html(url)

            table_1 += """
            <tr>
                <th>Requests to following URLs were out of the target scope</th>
            </tr>
            """

            for url in results["filteredUrls"]:
                table_1 += "<tr><td>%s</td></tr>" % utils.encode_for_html(url)
            
            table_1 += "</table>"

            cnt += table_1

            table_2 = """
            <h5>Successfully Sent Requests</h5>
            <table>
                <tr>
                    <th>Requests that successfully reached the target</th>
                </tr>
            """

            for url in results["crawledUrls"]:
                table_2 += "<tr><td>%s</td></tr>" % utils.encode_for_html(url)
            
            table_2 += "</table>"
            
            cnt += table_2
        else:
            # FUTURE: Return plain-text table data as above
            cnt = """
            SiteCopier issued %s requests against the target application,
            out of which %s failed. Additionally, there were %s links which
            pointed outside the target and they were not requested.
            """ % (
                number_of_crawled_requests,
                number_of_failed_requests,
                number_of_filtered_requests
            )

        return cnt


    def get_description(self):
        """Introductory section of the presented part."""
        if self.style == 'BWFormal':
            intro = """
            <p> SiteCopier module crawls the target from its root address,
            finds and processes every link. Links that are in scope of the 
            target application are then requested and the response is recorded.
            Recorded responses can be found in <em>output/%s/SiteCopier</em> 
            folder.
            </p>
            """ % cfg.CURRENT_RUN_ID
            return intro
        else:
            return """
            SiteCopier module crawls the target from its root address,
            finds and processes every link. Links that are in scope of the 
            target application are then requested and the response is recorded.
            Recorded responses can be found in output/%s/SiteCopier
            """ % cfg.CURRENT_RUN_ID


    def get_no_output(self):
        """Returns message about no output being provided by the module."""
        if self.style == 'BWFormal':
            return """
            <p>
            No output was generated by the SiteCopier module run. Being this 
            the case, results of this run are highly likely skewed. This module
            is an essential component that should be run at the beginning of
            every scan.
            </p>
            """
        else:
            return """
            No output was generated by the SiteCopier module run. Being this 
            the case, results of this run are highly likely skewed. This module
            is an essential component that should be run at the beginning of
            every scan.
            """


    def generates_media(self):
        """
        Returns True when presenter generated media data for presentation 
        purposes. False otherwise.
        """
        return self._generates_media


    def get_media_path(self):
        """
        Returns path to directory in which this presenter's media data
        are generated.
        """
        return Consts.EMPTY_STRING


    def set_information_level(self, level):
        """
        Influcences what minimum importance level data should be included in 
        generated report (only high, medium and above, low and above).
        """
        allowed_values = ["HIGH", "MEDIUM", "LOW"]
        if level in allowed_values:
            self.information_level = level


    def get_importance(self):
        """
        Returns information about how module perceives its own importance 
        compared to other modules (use case should be similar the use of 
        z-index in CSS - module can force itself on top, or to the very
        bottom). This value determines where in generated final output 
        report will be this module's content located. 

        -1 = Bottom part of the report
        0+ = Above bottom (the higher the more on top) 
        """
        return self.importance


    def override_modules(self):
        """
        Returns modules which should not use their native presenters as their
        output will be overriden/presented by this module.
        FUTURE: This is not part of the implementation scope for master project
        """
        pass