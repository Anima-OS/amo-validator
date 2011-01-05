from validator import decorator
from validator.constants import PACKAGE_DICTIONARY, FF4_MIN

APPLICATIONS = {
    "{ec8030f7-c20a-464f-9b0e-13a3a9e97384}": "firefox",
    "{86c18b42-e466-45a9-ae7a-9b95ba6f5640}": "mozilla",
    "{3550f703-e582-4d05-9a08-453d09bdfdc6}": "thunderbird",
    "{718e30fb-e89b-41dd-9da7-e25a45638b28}": "sunbird",
    "{92650c4d-4b8e-4d2a-b7eb-24ecf4f6b63a}": "seamonkey",
    "{a23983c0-fd0e-11dc-95ff-0800200c9a66}": "fennec"
}

APPROVED_APPLICATIONS = {}

APP_VERSIONS_URL = \
        "https://addons.mozilla.org/en-US/firefox/pages/appversions/"

@decorator.register_test(tier=1)
def test_targetedapplications(err, package_contents=None,
                              xpi_package=None):
    """Tests to make sure that the targeted applications in the
    install.rdf file are legit and that any associated files (I'm
    looking at you, SeaMonkey) are where they need to be."""
    
    if not err.get_resource("has_install_rdf"):
        return
    
    install = err.get_resource("install_rdf")
    
    # Search through the install.rdf document for the SeaMonkey
    # GUID string.
    ta_predicate = install.uri("targetApplication")
    ta_guid_predicate = install.uri("id")
    ta_min_ver = install.uri("minVersion")
    ta_max_ver = install.uri("maxVersion")
    
    used_targets = [];
    
    mismatch_pattern = "Version numbers for %s are invalid."
    
    # Isolate all of the bnodes referring to target applications
    for target_app in install.get_objects(None, ta_predicate):
        
        # Get the GUID from the target application
        
        for ta_guid in install.get_objects(target_app,
                                           ta_guid_predicate):
            
            used_targets.append(ta_guid)
            
            if ta_guid == "{92650c4d-4b8e-4d2a-b7eb-24ecf4f6b63a}":
                
                # Time to test for some install.js.
                if "install.js" not in package_contents:
                    err.warning(("testcases_targetapplication",
                                 "test_targetedapplications",
                                 "missing_seamonkey_installjs"),
                                "Missing install.js for SeaMonkey.",
                                """SeaMonkey requires install.js, which
                                was not found. install.rdf indicates
                                that the addon supports SeaMonkey.""",
                                "install.rdf")
                    # Only reject if it's a dictionary.
                    if err.detected_type == PACKAGE_DICTIONARY:
                        err.reject = True
                
                break
            
            found_guid = False
            for (guid, key) in [(x["guid"], y) for (y, x) in
                                    APPROVED_APPLICATIONS.items()]:
                if guid == ta_guid:
                    found_guid = key

            if found_guid:
                # Remember if the addon supports Firefox.
                is_firefox = APPLICATIONS[ta_guid] == "firefox"
                
                # Grab the minimum and maximum version numbers.
                min_version = install.get_object(target_app, ta_min_ver)
                max_version = install.get_object(target_app, ta_max_ver)
                
                app_versions = APPROVED_APPLICATIONS[found_guid]["versions"]
                
                # Ensure that the version numbers are in the app's
                # list of acceptable version numbers.
                
                app_name = APPLICATIONS[ta_guid] if \
                           ta_guid in APPLICATIONS else \
                           ta_guid

                try:
                    if min_version is not None:
                        min_ver_pos = app_versions.index(min_version)
                except ValueError:
                    err.error(("testcases_targetapplication",
                               "test_targetedapplications",
                               "invalid_min_version"),
                              "Invalid minimum version number",
                              ["The minimum version that was specified is not "
                               "an acceptable version number for the Mozilla "
                               "product that it corresponds with.",
                               'Version "%s" isn\'t compatible with "%s".' %
                                   (min_version, app_name),
                               APP_VERSIONS_URL],
                              "install.rdf")
                    continue
                    
                try:
                    if max_version is not None:
                        max_ver_pos = app_versions.index(max_version)
                except ValueError:
                    err.error(("testcases_targetapplication",
                               "test_targetedapplications",
                               "invalid_max_version"),
                              "Invalid maximum version number",
                              ["The maximum version that was specified is not "
                               "an acceptable version number for the Mozilla "
                               "product that it corresponds with.",
                               'Version "%s" isn\'t compatible with "%s".' %
                                   (max_version, app_name),
                               APP_VERSIONS_URL],
                              "install.rdf")
                    continue
                
                # Now we need to check to see if the version numbers
                # are in the right order.
                if min_version is not None and \
                   max_version is not None and \
                   min_ver_pos > max_ver_pos:
                    err.error(("testcases_targetapplication",
                               "test_targetedapplications",
                               "invalid_version_order"),
                              "Invalid min/max versions",
                              ["""The version numbers provided for the
                               application in question are not in the correct
                               order. The maximum version must be greater than
                               the minimum version.""",
                               '"%s" is not less than "%s".' % (min_version,
                                                                max_version)],
                              "install.rdf")
                    continue
                
                # Test whether it's a FF4 addon

                # NOTE: This should probably also be extrapolated for
                # Thunderbird and the like when they get up to speed. The tests
                # will likely be the same down the line, so we can keep the
                # "ff4" resource as a legacy thing and worry about it later.
                if is_firefox:
                    ff4_pos = app_versions.index(FF4_MIN)
                    if max_ver_pos >= ff4_pos:
                        err.save_resource("ff4", True)
    
    no_duplicate_targets = set(used_targets)
    
    if len(used_targets) != len(no_duplicate_targets):
        err.warning(("testcases_targetapplication",
                     "test_targetedapplication",
                     "duplicate_targetapps"),
                    "Found duplicate <em:targetApplication> elements.",
                    """Multiple targetApplication elements were found
                    in the install.manifest file that refer to the same
                    application GUID. There should not be duplicate
                    target applications entries.""",
                    "install.rdf")
    
    # This finds the UUID of the supported applications and puts it in
    # a fun and easy-to-use format for use in other tests.
    supports = []
    for target in used_targets:
        key = str(target)
        if key in APPLICATIONS:
            supports.append(APPLICATIONS[key])
    err.save_resource("supports", supports)
    

