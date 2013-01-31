from validator.constants import PACKAGE_THEME
from validator.errorbundler import ErrorBundle
import validator.testcases.markup.csstester as csstester
import validator.testcases.themes as themes

from helper import _do_test
from js_helper import _do_real_test_raw


def test_theme_chrome_manifest():
    "Tests that a theme has a valid chrome manifest file."

    _do_test("tests/resources/themes/pass.jar",
             themes.test_theme_manifest,
             False)


def test_theme_bad_chrome_manifest():
    "Tests that a theme has an invalid chrome manifest file."

    _do_test("tests/resources/themes/fail.jar",
             themes.test_theme_manifest)


def test_no_chrome_manifest():
    "Tests that validation is skipped if there is no chrome manifest."

    assert themes.test_theme_manifest(ErrorBundle(), None) is None


def test_js_banned():
    """Test that JS is banned in themes."""

    err = _do_real_test_raw("""foo();""", detected_type=PACKAGE_THEME)
    print err.print_summary(verbose=True)
    assert err.failed()


def test_remote_css():
    """Test that remote CSS references are flagged."""

    snippet = """
    x {foo: url(http://foo.com/bar);}
    """

    err = ErrorBundle()
    csstester.test_css_snippet(err, "x.css", snippet, 0)
    assert not err.failed()

    err = ErrorBundle()
    err.detected_type = PACKAGE_THEME
    csstester.test_css_snippet(err, "x.css", snippet, 0)
    assert err.failed()
