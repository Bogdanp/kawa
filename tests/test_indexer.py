import pytest
import os

from kawa.indexer import Indexer


def rel(path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), path))


@pytest.fixture
def indexer():
    indexer = Indexer()
    indexer.index_file(rel("examples/reader.py"))
    return indexer


def test_indexers_can_index_files():
    # Given an indexer
    indexer = Indexer()

    # When I attempt to index a file
    indexer.index_file(rel("examples/reader.py"))

    # Then I expect the file to be indexed
    assert "tests.examples.reader" in indexer.modules


@pytest.mark.parametrize("filename,line_number,column_offset,expected", [
    (
        "examples/reader.py", 1, 6,
        "tests.examples.reader.Reader"
    ),

    (
        "examples/reader.py", 2, 8,
        "tests.examples.reader.Reader.__init__",
    ),

    (
        "examples/reader.py", 2, 10,
        "tests.examples.reader.Reader.__init__",
    ),

    (
        "examples/reader.py", 6, 8,
        "tests.examples.reader.Reader.read",
    ),

    (
        "examples/reader.py", 12, 8,
        "tests.examples.reader.read",
    ),

    (
        "examples/reader.py", 12, 9,
        "tests.examples.reader.read.filename",
    ),
])
def test_indexers_can_look_up_entities(indexer, filename, line_number, column_offset, expected):
    assert indexer.lookup_entity(rel(filename), line_number, column_offset).name == expected


@pytest.mark.parametrize("filename,line_number,column_offset,expected", [
    (
        "examples/reader.py", 0, 0,
        {
            "type": "module",
            "name": "tests.examples.reader",
            "docstring": None,
            "location": (0, 0),
        }
    ),

    (
        "examples/reader.py", 1, 0,
        {
            "type": "class",
            "name": "tests.examples.reader.Reader",
            "docstring": None,
            "location": (1, 0),
        }
    ),

    (
        "examples/reader.py", 6, 8,
        {
            "type": "function",
            "name": "tests.examples.reader.Reader.read",
            "arguments": ["self", "count"],
            "docstring": 'Reads "count" bytes from the current file.',
            "location": (6, 4),
        }
    ),
])
def test_indexers_can_look_up_metadata(indexer, filename, line_number, column_offset, expected):
    assert indexer.lookup_metadata(rel(filename), line_number, column_offset) == expected


@pytest.mark.parametrize("filename,line_number,column_offset,expected", [
    (
        "examples/reader.py", 1, 5,
        {
            "type": "class",
            "name": "tests.examples.reader.Reader",
            "docstring": None,
            "location": (1, 0),
        }
    ),

    (
        "examples/reader.py", 18, 10,
        {
            "type": "function",
            "name": "tests.examples.reader.read",
            "arguments": ["filename", "count"],
            "docstring": 'Read "count" bytes from "filename".',
            "location": (12, 0),
        }
    ),
])
def test_indexers_can_look_up_definitions(indexer, filename, line_number, column_offset, expected):
    assert indexer.lookup_definition(rel(filename), line_number, column_offset) == expected


@pytest.mark.parametrize("filename,line_number,column_offset,expected", [
    (
        "examples/reader.py", 2, 23,
        [
            {
                "type": "variable",
                "name": "tests.examples.reader.Reader.__init__.filename",
                "location": (2, 23),
            },
            {
                "type": "reference",
                "name": "tests.examples.reader.Reader.__init__.filename",
                "location": (3, 24),
            }
        ]
    ),

    (
        "examples/reader.py", 12, 4,
        [
            {
                "type": "function",
                "name": "tests.examples.reader.read",
                "arguments": ["filename", "count"],
                "docstring": 'Read "count" bytes from "filename".',
                "location": (12, 0),
            },
            {
                "type": "reference",
                "name": "tests.examples.reader.read",
                "location": (18, 10),
            }
        ]
    )
])
def test_indexers_can_look_up_references(indexer, filename, line_number, column_offset, expected):
    assert indexer.lookup_references(rel(filename), line_number, column_offset) == expected
