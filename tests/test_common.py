import os

from kawa.common import find_vc_root, find_qualified_name


def test_find_vc_root_can_find_roots():
    # Given the filename of the current test file
    filename = os.path.abspath(__file__)

    # When I attempt to find its vc root
    root = find_vc_root(filename)

    # Then I should get this vc's root
    assert root.endswith("/kawa")


def test_qualify_module_can_qualify_modules():
    # Given the filename of the current test file
    filename = os.path.abspath(__file__)

    # When I attempt to find its fully qualified name
    name = find_qualified_name(filename)

    # Then I should get its qualified name
    assert name == "tests.test_indexer"
