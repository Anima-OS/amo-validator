import sys

from nose.tools import eq_

from validator.errorbundler import ErrorBundle
from validator.outputhandlers.shellcolors import OutputHandler
import validator.unicodehelper
import validator.testcases.scripting


# Originated from bug 626496
def _do_test(path):
    script = validator.unicodehelper.decode(open(path, 'rb').read())
    print script.encode('ascii', 'replace')

    err = ErrorBundle(instant=True)
    err.supported_versions = {}
    err.handler = OutputHandler(sys.stdout, False)
    validator.testcases.scripting.test_js_file(err, path, script)
    return err


def test_controlchars_ascii_ok():
    """Test that multi-byte characters are decoded properly (utf-8)."""

    errs = _do_test('tests/resources/controlchars/controlchars_ascii_ok.js')
    assert not errs.message_count


def test_controlchars_ascii_warn():
    """
    Test that multi-byte characters are decoded properly (utf-8) but remaining
    non ascii characters raise warnings.
    """

    err = _do_test('tests/resources/controlchars/controlchars_ascii_warn.js')
    eq_(len(err.warnings), 1)
    eq_(err.warnings[0]['id'][2], 'syntax_error')
