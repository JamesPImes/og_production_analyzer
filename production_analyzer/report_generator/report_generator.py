
"""
A class for converting production review data into a plaintext report.
"""


class ReportGenerator:
    def __init__(
            self,
            output_fp=None,
            mode='w',
            report_sections: list = None
    ):
        """
        :param output_fp: (Optional) The filepath to a ```.txt``` file
         where this report will be written. (If not specified, this
         object can still be used to generate the report string.)
        :param mode: (Optional) The mode in which to open the output
         file.
        :param report_sections: A list of objects of the
         ```ReportSection``` class (or any of its child classes), in the
         order in which they should be written to the report.
        """
        self.output_fp = output_fp
        self.file = None
        self.mode = mode
        if report_sections is None:
            report_sections = []
        self.report_sections = report_sections

    def generate_report_text(self) -> str:
        """Generate the plaintext of the report."""
        components = [rs.output_string() for rs in self.report_sections]
        return ''.join(components)

    def write_report_to_file(self) -> str:
        """
        Generate the report text and save it to the configured file.
        :return: The report text.
        """
        s = self.generate_report_text()
        with open(self.output_fp, self.mode) as file:
            file.write(s)
        return s
