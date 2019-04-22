from core import constants as Consts


class Presenter():


    def __init__(self, results):
        self.module_name = "XSSFinder"

        """Is media data generated as part of the presentation?"""
        self._generates_media = False
        
        """Determines how high will the output be in final report."""
        self.importance = 3

        """Minimum level of importance for data to be reported, default all."""
        self.information_level = "LOW"

        """Provides access to module-run results."""
        self.results = results

        """Default value for presenting style."""
        self.style = Consts.DEFAULT_PRESENTER_STYLE


    def present_content(self, presentation_style):
        """
        Returns a dict of content ready for presentation and description of 
        the part that is going to be presented. Style specified by parameter.
        """
        print("[%s] Presenter ready and working..." % self.module_name)
        self.style = presentation_style

        return {
            "content": self.get_content(),
            "description": self.get_description()
        }


    def get_content(self):
        """
        """
        results = self.results['XSSFinder']['results']['nonparsable']

        content = Consts.EMPTY_STRING
        if len(results['discovered_xss']) > 0:
            content += self.get_discovered_number_text(
                len(results['discovered_xss'])
            )
            content += self.get_discovered_list(results['discovered_xss'])

        return content



    def get_discovered_list(self, discovered):
        if self.style == 'BWFormal':
            cnt = """
            <table>
                <tr>
                    <th>URL</th>
                    <th>Vulnerable parameter</th>
                    <th>Protection</th>
                    <th>Rendering Context</th>
                </tr>
            """
            for xss in discovered:
                ctx = Consts.EMPTY_STRING
                if "context" in xss:
                    ctx = xss["context"]
                
                cnt += """
                <tr>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                </tr>
                """ % (xss["url"], xss["param"], xss["protection"], ctx)
            
            cnt += "</table>"
            
            return cnt
        else:
            return ""

    
    def get_discovered_number_text(self, number):
        if self.style == 'BWFormal':
            return """
            <p>Scan detected <strong>%s</strong> reflected XSS vulnerabilities.
            """ % number
        else:
            return 'Scan detected %s reflected XSS vulnerabilities.' % number



    def get_description(self):
        """Introductory section of the presented part."""
        if self.style == "BWFormal":
            # Format it as paragraphs for HTML
            description_lines = """
            <p>
            An <em>XSSFinder</em> module takes advantage of information gathered
            by both <em>SiteCopier</em> and <em>RequestMiner</em> modules. It
            looks for content supplied by the user that is reflected back into
            the page and then determines whether the website author implemented
            sufficient protection against XSS (typically encoding).
            </p>
            <p>
            XSSFinder is aware of the context in which the payload is reflected
            and before reporting discovered XSS, it verifies that necessary 
            preconditions were satisfied for the finding, thus avoiding 
            false positives.
            </p> 
            """
            
            return description_lines
        else:
            # No other presenting styles yet and introduction can be empty.
            return Consts.EMPTY_STRING

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