
import setuptools


DESCRIPTION = (
    'A tool for examining monthly oil and/or gas records for gaps in '
    'production.'
)
LONG_DESCRIPTION = DESCRIPTION
MODULE_DIR = 'production_analyzer'


def get_constant(constant):
    setters = {
        'version': '__version__ = ',
        'author': '__author__ = ',
        'author_email': '__email__ = ',
        'url': '__website__ = ',
        'license': '__license__ = ',
    }
    var_setter = setters[constant]
    with open(rf".\{MODULE_DIR}\_constants.py", "r") as file:
        for line in file:
            if line.startswith(var_setter):
                return line[len(var_setter):].strip('\'\n \"')
        raise RuntimeError(f"Could not get {constant} info.")


setuptools.setup(
    name='production_checker',
    version=get_constant('version'),
    packages=setuptools.find_packages(),
    url=get_constant('url'),
    license=get_constant('license'),
    author=get_constant('author'),
    author_email=get_constant("author_email"),
    DESCRIPTION=DESCRIPTION,
    LONG_DESCRIPTION=LONG_DESCRIPTION,
    LONG_DESCRIPTION_content_type="text/markdown",
    include_package_data=True
)
