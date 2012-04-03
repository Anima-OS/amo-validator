import fnmatch
import re

from validator.constants import BUGZILLA_BUG
from validator.compat import (FX4_DEFINITION, FX5_DEFINITION, FX6_DEFINITION,
                              FX7_DEFINITION, FX8_DEFINITION, FX9_DEFINITION,
                              FX11_DEFINITION, FX12_DEFINITION, TB7_DEFINITION,
                              TB10_DEFINITION, TB11_DEFINITION)
from validator.contextgenerator import ContextGenerator


NP_WARNING = "Network preferences may not be modified."
EUP_WARNING = "Extension update settings may not be modified."
NSINHS_LINK = ("https://developer.mozilla.org/en/XPCOM_Interface_Reference"
               "/nsINavHistoryService")
TB7_LINK = "https://developer.mozilla.org/en/Thunderbird_7_for_developers"

GENERIC_PATTERNS = {
    r"globalStorage\[.*\].password":
        "Global Storage may not be used to store passwords.",
    r"launch\(\)":
        "Use of 'launch()' is disallowed because of restrictions on "
        "nsILocalFile. If the code does not use nsILocalFile, consider a "
        "different function name."}

# JS category hunting; bug 635423
# Generate regexes for all of them. Note that they all begin with
# "JavaScript". Capitalization matters, bro.
CATEGORY_REGEXES = (
        map(re.compile,
            map(lambda r: '''"%s"|'%s'|%s''' % (r, r, r.replace(' ', '-')),
                map(lambda r: "%s%s" % ("JavaScript ", r),
                    ("global constructor",
                     "global constructor prototype alias",
                     "global property",
                     "global privileged property",
                     "global static nameset",
                     "global dynamic nameset",
                     "DOM class",
                     "DOM interface")))))

PASSWORD_REGEX = re.compile("password", re.I)
PROTOTYPE_REGEX = re.compile(r"(String|Object|Number|Date|RegExp|Function|"
                             r"Boolean|Array|Iterator)\.prototype"
                             r"(\.[a-zA-Z0-9]+|\[.+\]) =", re.I)

CHROME_PATTERNS = (
    (r"(?<![\'\"])require\s*\(\s*[\'\"]"
     r"(chrome|window-utils|observer-service)"
     r"[\'\"]\s*\)",
        'Usage of non-SDK interface',
        "This SDK-based add-on uses interfaces that aren't part of the SDK."),
)


# DOM mutation events; bug 642153
DOM_MUTATION_REGEXES = map(re.compile,
        ("DOMAttrModified", "DOMAttributeNameChanged",
         "DOMCharacterDataModified", "DOMElementNameChanged",
         "DOMNodeInserted", "DOMNodeInsertedIntoDocument", "DOMNodeRemoved",
         "DOMNodeRemovedFromDocument", "DOMSubtreeModified"))

FX6_INTERFACES = {"nsIDOMDocumentTraversal": 655514,
                  "nsIDOMDocumentRange": 655513,
                  "IWeaveCrypto": 651596}
FX7_INTERFACES = {"nsIDOMDocumentStyle": 658904,
                  "nsIDOMNSDocument": 658906,
                  "nsIDOM3TypeInfo": 660539,
                  "nsIDOM3Node": 659053}
FX8_INTERFACES = {"nsISelection2": 672536,
                  "nsISelection3": 672536}
FX11_INTERFACES = {"nsICharsetResolver": 700490}
FX12_INTERFACES = {"nsIProxyObjectManager":
                       (675221,
                        "This add-on uses nsIProxyObjectManager, which was "
                        "removed in Gecko 12."),
                   "documentCharsetInfo": 713825,
                   "nsIJetpack(Service)?":
                       (711838,
                        "This add-on uses the Jetpack service, which was "
                        "deprecated long ago and is no longer included in "
                        "Gecko 12. Please update your add-on to use a more "
                        "recent version of the Add-ons SDK.")}

TB11_STRINGS = {"newToolbarCmd\.label": 694027,
                "newToolbarCmd\.tooltip": 694027,
                "openToolbarCmd\.label": 694027,
                "openToolbarCmd\.tooltip": 694027,
                "saveToolbarCmd\.tooltip": 694027,
                "publishToolbarCmd\.tooltip": 694027,
                "messengerWindow\.title": 701671,
                "folderContextSearchMessages\.label": 652555,
                "folderContextSearchMessages\.accesskey": 652555,
                "importFromSeamonkey2\.label": 689437,
                "importFromSeamonkey2\.accesskey": 689437,
                "comm4xMailImportMsgs\.properties": 689437,
                "specialFolderDeletionErr": 39121,
                "sourceNameSeamonkey": 689437,
                "sourceNameOExpress": 689437,
                "sourceNameOutlook": 689437,
                "failedDuplicateAccount": 709020}

TB11_JS = {"onViewToolbarCommand": 644169,
                "nsContextMenu": 680192,
                "MailMigrator\.migrateMail": 712395,
                "AddUrlAttachment": 708982,
                "makeFeedObject": 705504,
                "deleteFeed": 705504}

def run_regex_tests(document, err, filename, context=None, is_js=False):
    """Run all of the regex-based JS tests."""

    if context is None:
        context = ContextGenerator(document)

    def _generic_test(pattern, title, message, metadata={}):
        """Run a single regex test."""
        match = pattern.search(document)
        if match:
            line = context.get_line(match.start())
            err.warning(
                err_id=("testcases_javascript_regex", "generic",
                        "_generic_test"),
                warning=title,
                description=message,
                filename=filename,
                line=line,
                context=context)
            if metadata:
                err.metadata.update(metadata)

    def _substring_test(pattern, title, message):
        """Run a single substringest."""
        match = re.compile(pattern).search(document)
        if match:
            line = context.get_line(match.start())
            err.warning(
                err_id=("testcases_javascript_regex", "generic",
                        "_generic_test"),
                warning=title,
                description=message,
                filename=filename,
                line=line,
                context=context)

    def _compat_test(pattern, title, message, compatibility_type,
                     appversions=None, logFunc=err.notice):
        """Run a single regex test and return a compatibility message."""
        match = pattern.search(document)
        if match:
            line = context.get_line(match.start())
            logFunc(
                ("testcases_javascript_regex", "generic", "_compat_test"),
                title,
                description=message,
                filename=filename,
                line=line,
                context=context,
                compatibility_type=compatibility_type,
                for_appversions=appversions,
                tier=5)

    if not filename.startswith("defaults/preferences/"):
        from javascript.predefinedentities import (BANNED_PREF_BRANCHES,
                                                   BANNED_PREF_REGEXPS)
        for pattern in BANNED_PREF_REGEXPS:
            _generic_test(
                re.compile("[\"']" + pattern),
                "Potentially unsafe preference branch referenced",
                "Extensions should not alter preferences matching /%s/"
                    % pattern)

        for branch in BANNED_PREF_BRANCHES:
            _substring_test(
                branch.replace(r".", r"\."),
                "Potentially unsafe preference branch referenced",
                "Extensions should not alter preferences in the '%s' "
                "preference branch" % branch)

    for pattern, message in GENERIC_PATTERNS.items():
        _generic_test(
                re.compile(pattern),
                "Potentially unsafe JS in use.",
                message)

    for pattern, title, message in CHROME_PATTERNS:
        _generic_test(re.compile(pattern), title, message,
                      {'requires_chrome': True})

    if is_js:
        for pattern in CATEGORY_REGEXES:
            _generic_test(
                    pattern,
                    "Potential JavaScript category registration",
                    "Add-ons should not register JavaScript categories. It "
                    "appears that a JavaScript category was registered via a "
                    "script to attach properties to JavaScript globals. This "
                    "is not allowed.")

        if fnmatch.fnmatch(filename, "defaults/preferences/*.js"):
            _generic_test(
                PASSWORD_REGEX,
                "Passwords may be stored in /defaults/preferences JS files.",
                "Storing passwords in the preferences is insecure and the "
                "Login Manager should be used instead.")

        is_jsm = filename.endswith(".jsm") or "EXPORTED_SYMBOLS" in document

        if not is_jsm:
            # Have a non-static/dynamic test for prototype extension.
            _generic_test(
                    PROTOTYPE_REGEX,
                    "JS Prototype extension",
                    "It appears that an extension of a built-in JS type was "
                    "made. This is not allowed for security and compatibility "
                    "reasons.")

    for pattern in DOM_MUTATION_REGEXES:
        _generic_test(
                pattern,
                "DOM Mutation Events Prohibited",
                "DOM mutation events are flagged because of their "
                "deprecated status, as well as their extreme "
                "inefficiency. Consider using a different event.")

    # Firefox 5 Compatibility
    if err.supports_version(FX5_DEFINITION):
        _compat_test(
                re.compile(r"navigator\.language"),
                "navigator.language may not behave as expected",
                ("JavaScript code was found that references "
                 "navigator.language, which will no longer indicate "
                 "the language of Firefox's UI. To maintain existing "
                 "functionality, general.useragent.locale should be "
                 "used in place of `navigator.language`."),
                compatibility_type="error",
                appversions=FX5_DEFINITION)

    # Firefox 6 Compatibility
    if err.supports_version(FX6_DEFINITION):
        for pattern, bug in FX6_INTERFACES.items():
            _compat_test(
                    re.compile(pattern),
                    "Unsupported interface in use",
                    ("Your add-on uses interface %s, which has been removed "
                     "from Firefox 6. Please refer to %s for possible "
                     "alternatives.") % (pattern, BUGZILLA_BUG % bug),
                    compatibility_type="error",
                    appversions=FX6_DEFINITION,
                    logFunc=err.warning)

        # app.update.timer
        _compat_test(
                re.compile(r"app\.update\.timer"),
                "app.update.timer is incompatible with Firefox 6",
                ("The 'app.update.timer' preference is being replaced by the "
                 "'app.update.timerMinimumDelay' preference in Firefox 6. "
                 "Please refer to %s for more details.") %
                     (BUGZILLA_BUG % 614181),
                compatibility_type="error",
                appversions=FX6_DEFINITION)
        if is_js:
            # javascript/data: URI usage in the address bar
            _compat_test(
                    re.compile(r"['\"](javascript|data):"),
                    "javascript:/data: URIs may be incompatible with Firefox "
                    "6.",
                    ("Loading 'javascript:' and 'data:' URIs through the "
                     "location bar may no longer work as expected in Firefox "
                     "6. If you load these types of URIs, please test your "
                     "add-on on the latest Firefox 6 builds, or refer to %s "
                     "for more information.") %
                         (BUGZILLA_BUG % 656433),
                    compatibility_type="warning",
                    appversions=FX6_DEFINITION)

    # Firefox 7 Compatibility
    if err.supports_version(FX7_DEFINITION):
        for pattern, bug in FX7_INTERFACES.items():
            _compat_test(
                    re.compile(pattern),
                    "Unsupported interface in use",
                    ("Your add-on uses interface %s, which has been removed "
                     "from Firefox 7. Please refer to %s for possible "
                     "alternatives.") % (pattern, BUGZILLA_BUG % bug),
                    compatibility_type="error",
                    appversions=FX7_DEFINITION,
                    logFunc=err.warning)

        # nsINavHistoryObserver
        _compat_test(
                re.compile(r"nsINavHistoryObserver"),
                "nsINavHistoryObserver interface has changed in Firefox 7",
                ("The nsINavHistoryObserver interface has changed in Firefox "
                 "7. Most function calls now required a GUID parameter, "
                 "please refer to %s and %s for more information.") %
                    (NSINHS_LINK, BUGZILLA_BUG % 633266),
                compatibility_type="error",
                appversions=FX7_DEFINITION)
        # nsIMarkupDocumentViewer_MOZILLA_2_0_BRANCH
        _compat_test(
                re.compile(r"nsIMarkupDocumentViewer_MOZILLA_2_0_BRANCH"),
                "MOZILLA_2_0 Namespace has been merged in Firefox 7",
                ("The '_MOZILLA_2_0_BRANCH' interfaces have been merged out. "
                 "You should now use the namespace without the "
                 "'_MOZILLA_2_0_BRANCH' suffix. Please refer to %s for more "
                 "details.") %
                     (BUGZILLA_BUG % 617539),
                compatibility_type="warning",
                appversions=FX7_DEFINITION)

    # Firefox 8 Compatibility
    if err.supports_version(FX8_DEFINITION):
        for pattern, bug in FX8_INTERFACES.items():
            _compat_test(
                    re.compile(pattern),
                    "Removed, deprecated, or unsupported interface in use.",
                    ("The nsISelection2 and nsISelection3 interfaces have "
                     "been removed in Firefox 8. You can use the nsISelection "
                     "interface instead. See %s for more details.") %
                        (BUGZILLA_BUG % bug),
                    compatibility_type="error",
                    appversions=FX8_DEFINITION,
                    logFunc=err.warning)

        # nsIDOMWindowInternal
        NSIDWI_MDN = ("https://developer.mozilla.org/en/"
                          "XPCOM_Interface_Reference/nsIDOMWindow")
        _compat_test(
                re.compile(r"nsIDOMWindowInternal"),
                "nsIDOMWindowInternal has been deprecated in Firefox 8.",
                ("The nsIDOMWindowInternal interface has been deprecated in "
                 "Firefox 8. You can use the nsIDOMWindow interface instead. "
                 "See %s for more information.") % NSIDWI_MDN,
                compatibility_type="warning",
                appversions=FX8_DEFINITION)

        # ISO8601DateUtils
        # TODO(basta): Make this a string test instead once they're invented.
        ISO8601_MDC = ("https://developer.mozilla.org/en/JavaScript/Reference/"
                           "Global_Objects/Date")
        _compat_test(
                re.compile(r"ISO8601DateUtils"),
                "ISO8601DateUtils.jsm was removed in Firefox 8.",
                ("The ISO8601DateUtils object is no longer available in "
                 "Firefox 8. You can use the normal Date object instead. See "
                 "%s for more information.") % ISO8601_MDC,
                compatibility_type="error",
                appversions=FX8_DEFINITION,
                logFunc=err.warning)

    # Firefox 9 Compatibility
    if err.supports_version(FX9_DEFINITION):
        TAINTENABLED_BUG = BUGZILLA_BUG % 679971
        _compat_test(
                re.compile(r"navigator\.taintEnabled"),
                "navigator.taintEnabled was removed in Firefox 9.",
                ("The taintEnabled function is no longer available in"
                 " Firefox 9. Since this function was only used for "
                 "browser detection and this doesn't belong in extension"
                 " code, you should remove it if possible. For more "
                 "information, please see %s.") % TAINTENABLED_BUG,
                compatibility_type="warning",
                appversions=FX9_DEFINITION,
                logFunc=err.warning)
        XRAYPROPS_BUG = BUGZILLA_BUG % 660233
        _compat_test(
            re.compile(r"\.nodePrincipal"),
            ("nodePrincipal only available in chrome context"),
            ("The nodePrincipal property is no longer accessible from "
             "untrusted scripts. For more information, please see %s."
             ) % XRAYPROPS_BUG,
            compatibility_type="warning",
            appversions=FX9_DEFINITION)
        _compat_test(
            re.compile(r"\.documentURIObject"),
            ("documentURIObject only available in chrome context"),
            ("The documentURIObject property is no longer accessible from "
             "untrusted scripts. For more information, please see %s."
             ) % XRAYPROPS_BUG,
            compatibility_type="warning",
            appversions=FX9_DEFINITION)
        _compat_test(
            re.compile(r"\.baseURIObject"),
            ("baseURIObject only available in chrome context"),
            ("The baseURIObject property is no longer accessible from "
             "untrusted scripts. For more information, please see %s."
             ) % XRAYPROPS_BUG,
            compatibility_type="warning",
            appversions=FX9_DEFINITION)
        _compat_test(
            re.compile(r"nsIGlobalHistory3"),
            "nsIGlobalHistory3 was removed in Firefox 9",
            ("The nsIGlobalHistory3 interface has been removed from Firefox."
             " For more information, please see %s."
             ) % (BUGZILLA_BUG % 568971),
            compatibility_type="warning",
            appversions=FX9_DEFINITION,
            logFunc=err.warning)

        # geo.wifi.* warnings
        geo_wifi_description = (
                "The geo.wifi.* preferences are no longer created by default "
                "in Gecko 9. Reading them without testing for their presence "
                "can result in unexpected errors. See %s for more "
                "information." % BUGZILLA_BUG % 689252)
        _compat_test(
            re.compile(r"geo\.wifi\.uri"),
            "The preference 'geo.wifi.uri' was removed in Firefox 9",
            geo_wifi_description,
            compatibility_type="error",
            appversions=FX9_DEFINITION,
            logFunc=err.warning)
        _compat_test(
            re.compile(r"geo\.wifi\.protocol"),
            "The preference 'geo.wifi.protocol' was removed in Firefox 9",
            geo_wifi_description,
            compatibility_type="error",
            appversions=FX9_DEFINITION,
            logFunc=err.warning)

    # Firefox 11 Compatibility
    if err.supports_version(FX11_DEFINITION):
        for pattern, bug in FX11_INTERFACES.items():
            _compat_test(
                    re.compile(pattern),
                    "Unsupported interface in use",
                    "Your add-on uses interface %s, which has been removed "
                    "from Firefox 11. Please refer to %s for possible "
                    "alternatives." % (pattern, BUGZILLA_BUG % bug),
                    compatibility_type="error",
                    appversions=FX11_DEFINITION,
                    logFunc=err.warning)

        # omni.jar renamed
        for instance in re.finditer(r"omni\.jar", document):
            err.warning(
                err_id=("testcases_regex", "regex_regex_tests", "omni.jar"),
                warning="'omni.jar' renamed to 'omni.ja'",
                description="This add-on references omni.jar, which was "
                            "renamed to omni.ja. You should avoid referencing "
                            "this file directly, and at least update this "
                            "reference for any versions that support Firefox "
                            "11 and above. See %s for more information." %
                                BUGZILLA_BUG % 701875,
                filename=filename,
                line=context.get_line(instance.start()),
                context=context,
                for_appversions=FX11_DEFINITION,
                compatibility_type="error",
                tier=5)

    # Firefox 12 Compatibility
    if err.supports_version(FX12_DEFINITION):
        for pattern, bug in FX12_INTERFACES.items():
            if isinstance(bug, tuple):
                bug, message = bug
            else:
                message = ("Your add-on uses interface %s, which has been "
                           "removed from Gecko 12.") % pattern

            message = "%s See %s for more infomration." % (message,
                                                           BUGZILLA_BUG % bug)
            _compat_test(
                    re.compile(pattern),
                    "Unsupported interface in use",
                    message,
                    compatibility_type="error",
                    appversions=FX12_DEFINITION,
                    logFunc=err.warning)

        # Test for `chromemargin` (bug 735876)
        for instance in re.finditer(r"chromemargin", document):
            err.notice(
                err_id=("testcases_regex", "regex_regex_tests", "chromemargin"),
                notice="`chromemargin` attribute changed in Gecko 12",
                description="This add-on uses the chromemargin attribute, "
                            "which after Gecko 12 will not work in the same "
                            "way  with values other than 0 or -1. Please see "
                            "%s for more information." % BUGZILLA_BUG % 735876,
                filename=filename,
                line=context.get_line(instance.start()),
                context=context,
                for_appversions=FX12_DEFINITION,
                compatibility_type="error",
                tier=5)

    # Thunderbird 7 Compatibility rdf:addressdirectory
    if err.supports_version(TB7_DEFINITION):
        # dictUtils.js removal
        _compat_test(
                re.compile(r"resource:///modules/dictUtils.js"),
                "dictUtils.js was removed in Thunderbird 7.",
                "The dictUtils.js file is no longer available in "
                "Thunderbird 7. You can use Dict.jsm instead. See"
                "%s for more information." % BUGZILLA_BUG % 621213,
                compatibility_type="error",
                appversions=TB7_DEFINITION,
                logFunc=err.warning)
        # de-RDF the addressbook
        _compat_test(
                re.compile(r"rdf:addressdirectory"),
                "The address book does not use RDF in Thunderbird 7.",
                "The address book was changed to use a look up table in "
                "Thunderbird 7. See %s and %s for more information." %
                    (TB7_LINK, BUGZILLA_BUG % 621213),
                compatibility_type="error",
                appversions=TB7_DEFINITION)
        # Second test for de-RDFing the addressbook
        # r"GetResource(.*?)\s*\.\s*QueryInterface(.*?nsIAbDirectory);"
        _compat_test(
                re.compile(r"GetResource\(.*?\)\s*\.\s*"
                           r"QueryInterface\(.*?nsIAbDirectory\)"),
                "The address book does not use RDF in Thunderbird 7.",
                "The address book was changed to use a look up table in "
                "Thunderbird 7. See %s and %s for more information." %
                    (TB7_LINK, BUGZILLA_BUG % 621213),
                compatibility_type="error",
                appversions=TB7_DEFINITION)

    # Thunderbird 10 Compatibility
    if err.supports_version(TB10_DEFINITION):
        # gDownloadManagerStrings removal
        _compat_test(
                re.compile(r"gDownloadManagerStrings"),
                "gDownloadManagerStrings was removed in Thunderbird 10.",
                "This global is no longer available in "
                "Thunderbird 10. See %s for more information." %
                    BUGZILLA_BUG % 700220,
                compatibility_type="error",
                appversions=TB10_DEFINITION,
                logFunc=err.warning)
        # nsTryToClose.js removal
        _compat_test(
                re.compile(r"nsTryToClose.js"),
                "nsTryToClose.js was removed in Thunderbird 10.",
                "The nsTryToClose.js file is no longer available in "
                "Thunderbird 10. See %s for more information." %
                    BUGZILLA_BUG % 539997,
                compatibility_type="error",
                appversions=TB10_DEFINITION,
                logFunc=err.warning)

    # Thunderbird 11 Compatibility
    if err.supports_version(TB11_DEFINITION):
        # specialFoldersDeletionAllowed removal
        _compat_test(
                re.compile(r"specialFoldersDeletionAllowed"),
                "specialFoldersDeletionAllowed was removed in Thunderbird 11.",
                "This global is no longer available in "
                "Thunderbird 11. See %s for more information." %
                    BUGZILLA_BUG % 39121,
                compatibility_type="error",
                appversions=TB11_DEFINITION,
                logFunc=err.notice)

        for pattern, bug in TB11_STRINGS.items():
            _compat_test(
                    re.compile(pattern),
                    "Removed, renamed, or changed strings in use",
                    "Your add-on uses string %s, which has been changed or "
                    "removed from Thunderbird 11. Please refer to %s for "
                    "possible alternatives." % (pattern, BUGZILLA_BUG % bug),
                    compatibility_type="error",
                    appversions=TB11_DEFINITION,
                    logFunc=err.warning)
        for pattern, bug in TB11_JS.items():
            _compat_test(
                    re.compile(pattern),
                    "Removed, renamed, or changed javascript in use",
                    "Your add-on uses the javascript method or class %s, which "
                    "has been changed or removed from Thunderbird 11. Please "
                    "refer to %s for possible alternatives." %
                        (pattern, BUGZILLA_BUG % bug),
                    compatibility_type="error",
                    appversions=TB11_DEFINITION,
                    logFunc=err.notice)

