from js_helper import _do_test_raw, _get_var

def test_new_overwrite():
    "Tests that objects created with `new` can be overwritten"

    results = _do_test_raw("""
    var x = new String();
    x += "asdf";
    x = "foo";
    """)
    assert not results.message_count

def test_redefine_new_instance():
    "Test the redefinition of an instance of a global type."

    results = _do_test_raw("""
    var foo = "asdf";
    var r = new RegEx(foo, "i");
    r = new RegExp(foo, "i");
    r = null;
    """)
    assert not results.message_count

def test_property_members():
    "Tests that properties and members are treated fairly"

    results = _do_test_raw("""
    var x = {"foo":"bar"};
    var y = x.foo;
    var z = x["foo"];
    """)
    assert _get_var(results, "y") == "bar"
    assert _get_var(results, "z") == "bar"

def test_bug621106():
    "Tests that important objects cannot be overridden by JS"

    err = _do_test_raw("""
    Number.prototype = "This is the new prototype";
    Object.prototype.test = "bar";
    Object = "asdf";
    var x = Object.prototype;
    x.test = "asdf";
    """)
    # There should be four errors (prototypes are only readonly)
    print err.message_count
    assert err.message_count == 4

def test_with_statement():
    "Tests that 'with' statements work as intended"

    err = _do_test_raw("""
    var x = {"foo":"bar"};
    with(x) {
        foo = "zap";
    }
    var z = x["foo"];
    """)
    assert not err.failed()

    print _get_var(err, "z")
    assert _get_var(err, "z") == "zap"


    # Assert that the contets of a with statement are still evaluated even
    # if the context object is not available.
    err = _do_test_raw("""
    with(foo.bar) { // These do not exist yet
        eval("evil");
    }
    """)
    assert err.failed()

