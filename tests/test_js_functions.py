from js_helper import _do_test_raw

def test_createElement():
    "Tests that createElement and createElementNS throw errors."
    
    err = _do_test_raw("""
    var x = foo;
    foo.bar.whateverElement("script");
    """)
    assert not err.message_count

    err = _do_test_raw("""
    var x = foo;
    foo.bar.createElement("scr"+"ipt");
    """)
    assert err.message_count == 1
    
    err = _do_test_raw("""
    var x = foo;
    foo.bar.createElementNS("http://foo.bar/", "asdf:" +"scr"+"ipt");
    """)
    assert err.message_count == 1

    err = _do_test_raw("""
    let scr = "scr";
    scr += "ipt";
    foo.bar.createElement(scr);
    """)
    assert err.message_count == 1

    err = _do_test_raw("""
    document.createElement("style");
    function x(doc) {
        doc.createElement("style");
    }""")
    assert not err.message_count

    err = _do_test_raw("""
    document.createElement("sty"+"le");
    var x = "sty";
    x += "le";
    document.createElement(x);
    """)
    assert not err.message_count

def test_synchronous_xhr():
    "Tests that syncrhonous AJAX requests are marked as dangerous"

    err = _do_test_raw("""
    var x = new XMLHttpRequest();
    x.open("GET", "http://foo/bar", true);
    x.send(null);
    """)
    assert not err.message_count

    err = _do_test_raw("""
    var x = new XMLHttpRequest();
    x.open("GET", "http://foo/bar", false);
    x.send(null);
    """)
    assert err.message_count

