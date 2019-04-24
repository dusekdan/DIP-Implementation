from core import constants as Consts
from core import utils as utils
from urllib.parse import urlparse, parse_qs

class Presenter():


    def __init__(self, results):
        self.module_name = "RequestMiner"

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
        results = self.results['RequestMiner']['results']['parsable']

        content = Consts.EMPTY_STRING
        if len(results) > 0:
            # There are results to be presented
            content += self.get_results_table(results)
        else:
            content += self.get_no_data()

        return content


    def get_results_table(self, results):
        """Returns information collected by the RequestsMiner module."""
        if self.style == 'BWFormal':
            
            table_3 = """
            <h5>List of Discovered Hidden URL Parameters</h5>
            <p>These parameters were mined on URL: %s</p>
            <table>
            <tr>
                <th>Parameter name</th>
                <th>Reflected?</th>
            </tr>
            """ % utils.encode_for_html(results["hidden_params"]["source_url"])

            discovered_params = results["hidden_params"]["discovered"]
            reflected_params = results["hidden_params"]["reflected"]
            
            for param in discovered_params:
                
                if param in reflected_params:
                    reflected = "Yes"
                else:
                    reflected = "No"

                table_3 += "<tr><td>%s</td><td>%s</td></tr>" % (
                    utils.encode_for_html(param),
                    reflected
                )
            
            table_3 += "</table>"

            
            
            table_1 = """
            <h5>List of Detected URL Parameters in Use</h5>
            <table>
            <tr>
                <th>Parameter name</th>
                <th>Details</th>
            </tr>
            """

            for param, record in results["existing_params"].items():
                table_1 += """<tr>
                <td>%s</td>
                <td>
                    <table>
                    <tr>
                        <th>Source</th>
                        <th>Values</th>
                        <th>Is reflected?</th>
                    </tr>""" % utils.encode_for_html(param)

                
                sources = self.classify_param_sources(record["sources"])

                table_1 += "<tr><td>"
                for _, values in sources.items():
                    table_1 += utils.encode_for_html(values[0]) + "<br>"
                table_1 += "</td>"

                table_1 += "<td>"
                values = ', '.join(
                    [utils.encode_for_html(str(x)) for x in record["values"]]
                )
                

                table_1 += "%s</td></tr></table>" % values
                table_1 += """
                </td>
                </tr>"""

            table_1 += "</table>"

            # Return also a table of discovered headers

            table_2 = """
            <h5>List of Detected Non-Standard Headers in Use</h5>
            <table>
                <tr>
                    <th>Header name</th>
                </tr>
            """

            for header in results["existing_headers"]:
                table_2 += "<tr><td>%s</td></tr>" % utils.encode_for_html(
                    header
                )

            table_2 += """
            </table>

            <p>Previous table does not include required and the most common 
            headers.</p>
            """

            return table_3 + table_1 + table_2
        else:
            # FUTURE: Return plain-text data in table
            return Consts.EMPTY_STRING

    
    def classify_param_sources(self, sources):
        """
        Classify parameter sources by the number of parameters that appear in
        their query string. For each class, only one reflection should be 
        checked.
        """
        classes = {}
        for source in sources:
            parts = urlparse(source)
            query = parts.query
            query_hash = ''.join(sorted(list(parse_qs(query).keys())))
            
            if query_hash not in classes:
                classes[query_hash] = [source]
            else:
                classes[query_hash].append(source)
        
        return classes


    
    def get_no_data(self):
        """Returns a message about no data being collected."""
        if self.style == 'BWFormal':
            return """
            <p>RequestMiner module did not collect any presentable data</p>
            """
        else:
            return """
            RequestMiner did not collect any presentable data.
            """


    def get_description(self):
        """Introductory section of the presented part."""
        if self.style == 'BWFormal':
            intro = """
            <p><em>RequestMiner</em> module goes over the physical artifacts 
            collected by the SiteCopier module and searches them for relevant
            information regarding the target application security standing.</p>
            """
            return intro
        else:
            return """
            RequestMiner  module goes over the physical artifacts collected
            by the SiteCopier module and searches them for relevant information
            regarding the target application security standing.
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