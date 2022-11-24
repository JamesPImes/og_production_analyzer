
"""
Styles for report sections.
"""

from dataclasses import dataclass


@dataclass
class Style:
    """
    The following fields should contain empty brackets that will be
    filled with content:

    * ```header_format```  (e.g., ```'{}'```)
    * ```subheader_format```  (e.g., ```'-- {} --'```)
    * ```footer_format```  (e.g., ```'{}'```)
    * ```lineitem_bullet_format```  (e.g., ```' >> {}'```)

    Line items can be created from two component parts, in which case,
    the first component part will have its bullet added, and then be
    left-justified with a number of spaces, as configured with
    ```lineitem_justify=<int>```.

    Configure how dates should be reported with ```date_formate```
    (using ```strftime``` codes). This will be applied to ```datetime```
    objects.

    Configure how dates within a date range should be delimited with
    ```date_range_delimiter=<str>```.

    Configure how many linebreaks should come before and after a report
    section with ```leading_linebreaks=<int>``` and
    ```trailing_linebreaks=<int>```.
    """
    header_format: str = '{}'
    subheader_format: str = '---- {} ----'
    footer_format: str = '{}'
    lineitem_bullet_format: str = ' >> {}'
    lineitem_justify: int = 35
    date_range_delimiter: str = ' : '
    date_format: str = '%Y-%m-%d'
    leading_linebreaks: int = 0
    trailing_linebreaks: int = 2


__all__ = [
    'Style',
]
