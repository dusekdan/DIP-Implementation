from core import constants as Consts
from core import utils as utils


class Presenter():


    def __init__(self, results):
        self.module_name = "MisconfChecker"

        """Is media data generated as part of the presentation?"""
        self._generates_media = False
        
        """Determines how high will the output be in final report."""
        self.importance = 2

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
        results = self.results['MisconfChecker']['results']['nonparsable']

        content = Consts.EMPTY_STRING
        if len(results) > 0:
            content += self.get_findings(results)
        else:
            content += self.get_no_data()

        # Corner case when nothing was discovered
        if  len(results["directory_listing"]) == 0 and \
            len(results["vcs_resources"]) == 0 and \
            len(results["hidden_resources"]) == 0:
            content += self.get_no_data()

        return content


    def get_findings(self, results):
        """Returns discovered findings in presentable format."""
        directory_listing_found = len(results["directory_listing"]) > 0
        vcs_leftovers_found = len(results["vcs_resources"]) > 0
        resources_found = len(results["hidden_resources"]) > 0
        if self.style == 'BWFormal':
            # Information paragraphs about what was found.
            info = Consts.EMPTY_STRING
            if directory_listing_found:
                info += """
                <p><strong>Enabled directory browsing/listing</strong> was
                discovered in the following locations:</p>
                <ul>"""

                for dl_item in results["directory_listing"]:
                    info += "<li>%s</li>" % utils.encode_for_html(dl_item)

                info += "</ul>"
            if vcs_leftovers_found:
                info += """
                <p><strong>Version control files</strong> were pushed into the
                production along with the code. Sometimes, it is possible to 
                recreate the codebase and discover take over the application.
                See following locations:</p>
                <ul>
                """

                for vcs_item in results["vcs_resources"]:
                    info += "<li>%s</li>" % utils.encode_for_html(vcs_item)
                
                info += "</ul>"
            if resources_found:
                info += """<p>Other interesting <strong>resources</strong> were
                found in the following locations:</p>
                <ul>
                """

                for resource in results["hidden_resources"]:
                    info += "<li>%s</li>" % utils.encode_for_html(resource)
                
                info += "</ul>"
                
            return info
        else:
            # Future: Return this in plain-text format.
            return Consts.EMPTY_STRING


    def get_no_data(self):
        """Returns a message about no data being collected."""
        if self.style == 'BWFormal':
            return """
            <p>MisconfChecker module did not collect any presentable data</p>
            """
        else:
            return """
            MisconfChecker did not collect any presentable data.
            """


    def get_description(self):
        """Introductory section of the presented part."""
        if self.style == 'BWFormal':
            intro = """
            <p><em>MisconfChecker</em> module checks for configuration errors
            in deployed application, such as enabled directory listing, 
            VCS structures put into the production and hidden resources that
            are available, but not meant to be seen.</p>
            """
            return intro
        else:
            return """
            MisconfChecker module checks for configuration errors
            in deployed application, such as enabled directory listing, 
            VCS structures put into the production and hidden resources that
            are available, but not meant to be seen.
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