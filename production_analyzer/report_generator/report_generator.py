
"""
A class for converting production review data into a plaintext report.
"""


class ReportGenerator:
    def __init__(
            self,
            report_sections: list = None
    ):
        """
        :param report_sections: A list of objects of the
         ``ReportSection`` class (or any of its child classes), in the
         order in which they should be written to the report.
        """
        if report_sections is None:
            report_sections = []
        self.report_sections = report_sections

    def generate_report_text(self) -> str:
        """Generate the plaintext of the report."""
        components = [rs.output_string() for rs in self.report_sections]
        return ''.join(components)

    def write_report_to_file(self, output_fp, mode) -> str:
        """
        Generate the report text and save it to the configured file.
        :param output_fp: The filepath to a ``.txt`` file where this
        report will be written.
        :param mode: The mode in which to open the output file.
        :return: The report text.
        """
        s = self.generate_report_text()
        with open(output_fp, mode) as file:
            file.write(s)
        return s
