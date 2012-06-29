import json
import os
from StringIO import StringIO

import validator.constants
import validator.loader
import validator.submain
import validator.testcases.targetapplication
from validator.errorbundler import ErrorBundle
from validator.constants import PACKAGE_ANY


def validate(path, format="json",
             approved_applications=os.path.join(os.path.dirname(__file__),
                                                "app_versions.json"),
             determined=True,
             spidermonkey=False,
             listed=True,
             expectation=PACKAGE_ANY,
             for_appversions=None,
             overrides=None,
             timeout=None,
             market_urls=None):
    """
    Perform validation in one easy step!

    format : The format to output the results in
    approved_applications : Path to the list of approved application versions
    determined : Whether the validator should continue after a tier fails
    spidermonkey : Path to the local spidermonkey installation (Default: False)
    listed : True if the add-on is destined for AMO, false if not
    expectation : The type of package that should be expected
    for_appversions : A dict of app GUIDs referencing lists of versions.
                      Determines which version-dependant tests should be run.
    timeout: Number of seconds before aborting addon validation.
    """

    # Load up the target applications.
    with open(approved_applications) as approved_apps:
        apps = json.load(approved_apps)
        validator.constants.APPROVED_APPLICATIONS.clear()
        validator.constants.APPROVED_APPLICATIONS.update(apps)

    # Set the marketplace URLs if they're provided.
    if market_urls is not None:
        validator.constants.DEFAULT_WEBAPP_MRKT_URLS.extend(market_urls)

    bundle = ErrorBundle(listed=listed, determined=determined,
                         overrides=overrides, spidermonkey=spidermonkey,
                         for_appversions=for_appversions)
    validator.submain.prepare_package(bundle, path, expectation,
                                      for_appversions=for_appversions,
                                      timeout=timeout)

    # Write the results to the pipe
    formats = {"json": lambda b: b.render_json()}
    if format is not None:
        return formats[format](bundle)
    else:
        return bundle

