from core import constants as Consts
from core import utils as utils


class Presenter():


    def __init__(self, results):
        self.module_name = "TokenFinder"

        """Is media data generated as part of the presentation?"""
        self._generates_media = False
        
        """Determines how high will the output be in final report."""
        self.importance = 1

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


    def get_description(self):
        """Introductory section of the presented part."""
        if self.style == 'BWFormal':
            description_lines = """
            <p>A <em>TokenFinder</em> modules scans source code as retrieved
            by SiteCopier and searches for highly-entropic string sequences.
            High-entropy is a property of a string that was generated to be as
            random as possible on purpose. This property is fairly common for 
            strings that serve as private keys, access tokens and other forms
            of credentials that should be kept secret. This module identifies
            such strings in responses returned by the target application.</p>
            """
            return description_lines
        else:
            # Plain-text default.
            return """
            A TokenFinder modules scans source code as retrieved by SiteCopier
            and searches for highly-entropic string sequences. High-entropy is
            a property of a string that was generated to be as random as 
            possible on purpose. This property is fairly common for strings 
            that serve as private keys, access tokens and other forms of 
            credentials that should be kept secret. This module identifies such
            strings in responses returned by the target application.
            """


    def get_content(self):
        """
        Assembles content to be returned from the presenter. In the future,
        this might be the place where a decision about style-specific 
        assembler method call will be made based on self.style.
        """
        results = self.results['TokenFinder']['results']['nonparsable']

        content = Consts.EMPTY_STRING
        if len(results) > 0:
            # Something will be presented
            content += self.get_secrets_table(results)
        else:
            content += self.get_no_secrets_found_text()
        
        return content


    def get_secrets_table(self, secrets):
        """Prepares style-based table output containing discovered secrets."""
        if self.style == 'BWFormal':
            print(secrets)
            cnt = """
            <table>
                <tr>
                    <th>Secret string</th>
                    <th>Instances</th>
                </tr>
            """

            for secret, record in secrets.items():
                cnt += """
                <tr>
                    <td><textarea>%s</textarea></td>
                    <td>
                    <table>
                        <tr>
                        <th>URL</th>
                        <th>Line (in source code)</th>
                        <th>Entropy (Min: 1.0, Max: 8.0)</th>
                        </tr>""" % utils.encode_for_html(secret)
                
                for sr in record:
                    cnt += """
                    <tr>
                        <td>%s</td>
                        <td>%s</td>
                        <td>%s</td>
                    </tr>
                    """ % (
                    utils.encode_for_html(sr["url"]),
                    utils.encode_for_html(sr["line"]),
                    utils.encode_for_html(sr["entropy"])
                    )

                cnt += "</table></td></tr>"

            cnt += "</table>"
            return cnt
        else:
            # FUTURE: Plain-text table presentation
            return Consts.EMPTY_STRING


    def get_no_secrets_found_text(self):
        """Returns message about no secrets being found."""
        if self.style == 'BWFormal':
            return """
            <p>TokenFinder did not identify any secrets in the source code.</p>
            """
        else:
            return "TokenFinder did not identify any secrets in the source code."


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