from core import constants as Consts
from core import utils as utils

class Presenter():
    """
        This class is responsible for presenting results of 
        the XSSFinder module.

        |>  This software is a part of the master thesis: 
        |>  "Web Application Penetration Testing Automation"
        |>  Brno, University of Technology, 2019
        |
        |>  Author: Daniel Dušek (@dusekdan - github, gitlab, twitter)
        |>  Contact: dusekdan@gmail.com
        |>  https://danieldusek.com
    """


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
        results = self.results['XSSFinder']['results']['nonparsable']

        content = Consts.EMPTY_STRING
        if len(results['discovered_xss']) > 0:
            content += self.get_discovered_number_text(
                len(results['discovered_xss'])
            )
            content += self.get_discovered_table(results['discovered_xss'])
        else:
            content += self.get_no_issues_discovered_text()

        return content


    def context_to_readable(self, ctx):
        """Translates code-name for context into human readable string."""
        if ctx == 'ATTR':
            return 'Inside attribute'
        elif ctx == 'TAG':
            return 'Inside HTML body'


    def get_discovered_table(self, discovered):
        """
        Prepares style-based table output containing discovered XSS findings.
        """
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
            attr_pl_mention = dif_pl_mention = tag_pl_mention = False
            for xss in discovered:
                ctx = Consts.EMPTY_STRING
                if "context" in xss:
                    ctx = self.context_to_readable(xss["context"])
                else:
                    ctx = "&mdash;"
                
                cnt += """
                <tr>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                    <td>%s</td>
                </tr>
                """ % (
                    utils.encode_for_html(xss["url"]), 
                    utils.encode_for_html(xss["param"]), 
                    utils.encode_for_html(xss["protection"]),
                    ctx
                )

                if xss["protection"] == 'EncodedForHTML':
                    tag_pl_mention = 1
                elif xss["protection"] == 'EncodedForAttributes':
                    attr_pl_mention = 1
                elif xss["protection"] == 'OtherwiseModified':
                    dif_pl_mention = 1
            
            cnt += "</table>"

            el_sobkys_payload= utils.encode_for_html("""jaVasCript:/*-/*/*\/*'/*"/**/(/* */oNcliCk=alert() )//0A0a//</stYle/</titLe/</teXtarEa/</scRipt/-->\x3csVg/<sVg/oNloAd=alert()//>\x3e""")
            advisory_paragraph = """
            <p><strong>Exploitation advisory</strong>: If URL and parameter are
            listed in the previous table with protection different from 'None'
            then some encoding took place prior to rendering the payload. For
            demonstration of vulnerability, following payload can be used.
            </p>
            <code>%s</code>
            """ % el_sobkys_payload


            # If non-trivial protections were mentioned, provide advisory
            if attr_pl_mention or dif_pl_mention or tag_pl_mention:
                cnt += advisory_paragraph
            
            if dif_pl_mention:
                cnt += """When parameter is protected by 
                <strong>OtherwiseModified</strong> type of protection, it is
                highly likely that it is vulnerable to XSS. Some of the special
                characters (&gt;, &lt;, ", ') were not properly encoded and 
                it is probably possible to escape the rendering context.
                """
            
            return cnt
        else:
            # Future: Plain text results presentation is default.
            return ""


    def get_no_issues_discovered_text(self):
        """Message about XSSFinder not finding any vulnerabilities."""
        if self.style == 'BWFormal':
            return """
            <p>No reflected XSS vulnerabilities were discovered.</p>
            """
        else:
            return 'No reflected XSS vulnerabilities were discovered.'

    
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