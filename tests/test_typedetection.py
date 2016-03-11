from validator.errorbundler import ErrorBundle
from validator.rdf import RDFParser
from validator.xpi import XPIManager
from validator.constants import *
import validator.typedetection as typedetection


def _test_type(file_, expectation, failure=False):
    'Tests a file against the expectations'

    err = ErrorBundle(None, True)
    package = XPIManager(open(file_), mode='r', name=file_)
    contents = package.package_contents()

    # We need to have an install.rdf.
    assert 'install.rdf' in contents

    # Load up the install.rdf into an RDFParser
    install_file = package.read('install.rdf')
    install_rdf = RDFParser(err, install_file)

    results = typedetection.detect_type(err, install_rdf, package)

    assert results == expectation
    if not failure:
        assert not err.failed()
    else:
        assert err.failed()

    return err


def test_extension():
    "Tests that type detection can detect an addon of type 'extension'"

    err = _test_type('tests/resources/typedetection/td_notype_ext.xpi',
                     PACKAGE_EXTENSION)
    assert err.notices


def test_experiment():
    """Tests that type detection can detect an addon of type 'extension' for
    the 'experiment' (see bug 1220583)."""

    err = _test_type('tests/resources/typedetection/td_experiment.xpi',
                     PACKAGE_EXTENSION)
    assert not err.notices


def test_multipackage():
    'Tests that type detection can detect multipackage add-ons'

    err = _test_type('tests/resources/typedetection/td_multipack.xpi',
                     PACKAGE_MULTI)
    assert err.get_resource('is_multipackage')


def test_theme():
    "Tests that type detection can detect an addon of type 'theme'"

    _test_type('tests/resources/typedetection/td_notype_theme.jar',
               PACKAGE_THEME)


def test_dictionary():
    "Tests that type detection can detect an addon of type 'dictionary'"

    err = _test_type('tests/resources/typedetection/td_dictionary.xpi',
                     PACKAGE_DICTIONARY)
    assert not err.notices

    err = _test_type('tests/resources/typedetection/td_notype_dictionary.xpi',
                     PACKAGE_DICTIONARY, failure=True)
    assert err.errors[0]['id'] == (
        'typedetection', 'dictionary_valid_type', 'invalid_em_type')

    err = _test_type('tests/resources/typedetection/td_badtype_dictionary.xpi',
                     PACKAGE_DICTIONARY, failure=True)
    assert err.errors[0]['id'] == (
        'typedetection', 'dictionary_valid_type', 'invalid_em_type')


def test_langpack():
    """Tests that the type detection module can detect a language pack.
    As an added bonus, this test also verifies that the <em:type>
    element is correctly interpreted."""

    _test_type('tests/resources/typedetection/td_langpack.xpi',
               PACKAGE_LANGPACK)


def test_bad_emtype():
    """Tests for a bad <em:type> value."""

    _test_type('tests/resources/typedetection/td_bad_emtype.xpi',
               None,
               True)


def test_strange():
    """Tests that in install.rdf-less package is listed as being a
    dictionary type if it has an XPI extension and otherwise passes
    back a None object."""

    err = ErrorBundle(None, True)

    non_langpack = MockXPILangpack()
    langpack = MockXPILangpack(True)

    assert typedetection.detect_type(err, None, langpack
                                     ) == PACKAGE_DICTIONARY
    assert typedetection.detect_type(err, None, non_langpack) is None


class MockXPILangpack:
    'Simulates a language pack XPI manager object'

    def __init__(self, is_xpi=False):
        if is_xpi:
            self.extension = 'xpi'
        else:
            self.extension = 'foo'  # Or anything else
