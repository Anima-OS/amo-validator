"""
Prototype
---------

args
    the raw list of arguments
traverser
    the traverser
node
    the current node being evaluated
"""

from jstypes import *


def createElement(args, traverser, node):
    """Handles createElement calls"""

    if not args:
        return

    simple_args = [traverser._traverse_node(a) for a in args]

    if str(simple_args[0].get_literal_value()).lower() == "script":
        _create_script_tag(traverser)
    elif not (simple_args[0].is_literal() or
              isinstance(simple_args[0].get_literal_value(), str)):
        _create_variable_element(traverser)


def createElementNS(args, traverser, node):
    """Handles createElementNS calls"""

    if not args or len(args) < 2:
        return

    simple_args = [traverser._traverse_node(a) for a in args]

    if "script" in str(simple_args[1].get_literal_value()).lower():
        _create_script_tag(traverser)
    elif not (simple_args[1].is_literal() or
              isinstance(simple_args[1].get_literal_value(), str)):
        _create_variable_element(traverser)


def QueryInterface(args, traverser, node):
    """Handles QueryInterface calls"""

    if not args:
        return

    from call_definitions import xpcom_constructor
    return xpcom_constructor("QueryInterface", True, True)(
                wrapper=node,
                arguments=args,
                traverser=traverser)

def getInterface(args, traverser, node):
    """Handles getInterface calls"""

    # This really only needs to be handled for nsIInterfaceRequestor
    # intarfaces, but as it's fair for code to assume that that
    # interface has already been queried and methods with this name
    # are unlikely to behave differently, we just process it for all
    # objects.

    if not args:
        return

    from call_definitions import xpcom_constructor
    return xpcom_constructor("getInterface")(
                wrapper=node,
                arguments=args,
                traverser=traverser)

def _create_script_tag(traverser):
    """Raises a warning that the dev is creating a script tag"""
    traverser.err.warning(
        err_id=("testcases_javascript_instanceactions", "_call_expression",
                    "called_createelement"),
        warning="createElement() used to create script tag",
        description="The createElement() function was used to create a script "
                    "tag in a JavaScript file. Add-ons are not allowed to "
                    "create script tags or load code dynamically from the "
                    "web.",
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context)


def _create_variable_element(traverser):
    """Raises a warning that the dev is creating an arbitrary element"""
    traverser.err.warning(
        err_id=("testcases_javascript_instanceactions", "_call_expression",
                    "createelement_variable"),
        warning="Variable element type being created",
        description=["createElement or createElementNS were used with a "
                     "variable rather than a raw string. Literal values should "
                     "be used when taking advantage of the element creation "
                     "functions.",
                     "E.g.: createElement('foo') rather than "
                     "createElement(el_type)"],
        filename=traverser.filename,
        line=traverser.line,
        column=traverser.position,
        context=traverser.context)


def setAttribute(args, traverser, node):
    """This ensures that setAttribute calls don't set on* attributes"""

    if not args:
        return

    simple_args = [traverser._traverse_node(a) for a in args]

    if str(simple_args[0].get_literal_value()).lower().startswith("on"):
        traverser.err.notice(
            err_id=("testcases_javascript_instanceactions", "setAttribute",
                        "setting_on*"),
            notice="on* attribute being set using setAttribute",
            description="To prevent vulnerabilities, event handlers (like "
                        "'onclick' and 'onhover') should always be defined "
                        "using addEventListener.",
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)


INSTANCE_DEFINITIONS = {"createElement": createElement,
                        "createElementNS": createElementNS,
                        "getInterface": getInterface,
                        "setAttribute": setAttribute,
                        "QueryInterface": QueryInterface}

