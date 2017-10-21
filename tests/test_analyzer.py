import pytest

from kawa.analyzer import Module, Class, Function, Variable, analyze


@pytest.mark.parametrize("module_name,module_source,expected_output", [
    (
        # Test module docstring discovery
        "kawa.example",
        """
'''This module does something.
'''
        """,

        Module(
            name="kawa.example",
            docstring="This module does something.",
            source_location=(1, 0),
            definitions=[],
            references=[],
        )
    ),

    (
        # Test toplevel asssignment declaration discovery
        "kawa.example",
        """
x = 42
y = None
z, a = (1, 2)
        """,
        Module(
            name="kawa.example",
            definitions=[
                Variable(
                    name="kawa.example.x",
                    source_location=(2, 0),
                ),
                Variable(
                    name="kawa.example.y",
                    source_location=(3, 0),
                ),
                Variable(
                    name="kawa.example.z",
                    source_location=(4, 0),
                ),
                Variable(
                    name="kawa.example.a",
                    source_location=(4, 3),
                )
            ],
        ),
    ),

    (
        # Test toplevel function declaration discovery
        "kawa.example",
        """
def f() -> int:
    '''This function returns the number 42.
    '''
    return 42

def g():
    pass
        """,

        Module(
            name="kawa.example",
            definitions=[
                Function(
                    name="kawa.example.f",
                    arguments=[],
                    docstring="This function returns the number 42.",
                    source_location=(2, 0),
                ),
                Function(
                    name="kawa.example.g",
                    arguments=[],
                    docstring=None,
                    source_location=(7, 0),
                )
            ],
        )
    ),

    (
        # Test toplevel class declaration discovery
        "kawa.example",
        """
class Reader:
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, "r")

    def read(self, count):
        '''Reads "count" bytes from a file.
        '''
        raise NotImplementedError
        """,

        Module(
            name="kawa.example",
            definitions=[
                Class(
                    name="kawa.example.Reader",
                    source_location=(2, 0),
                    definitions=[
                        Function(
                            name="kawa.example.Reader.__init__",
                            arguments=["self", "filename"],
                            source_location=(3, 4),
                            definitions=[
                                Variable(
                                    name="kawa.example.Reader.__init__.self",
                                    source_location=(3, 17),
                                ),
                                Variable(
                                    name="kawa.example.Reader.__init__.filename",
                                    source_location=(3, 23),
                                ),
                            ],
                            references=[],
                        ),
                        Function(
                            name="kawa.example.Reader.read",
                            arguments=["self", "count"],
                            docstring='Reads "count" bytes from a file.',
                            source_location=(7, 4),
                            definitions=[
                                Variable(
                                    name="kawa.example.Reader.read.self",
                                    source_location=(7, 13),
                                ),
                                Variable(
                                    name="kawa.example.Reader.read.count",
                                    source_location=(7, 19),
                                ),
                            ],
                            references=[],
                        )
                    ]
                )
            ],
        )
    ),

    (
        # Test nested function declaration discovery
        "kawa.example",
        """
def f():
    def g():
        return 42
    return g
        """,

        Module(
            name="kawa.example",
            source_location=(1, 0),
            definitions=[
                Function(
                    name="kawa.example.f",
                    arguments=[],
                    source_location=(2, 0),
                    definitions=[
                        Function(
                            name="kawa.example.f.g",
                            arguments=[],
                            source_location=(3, 4),
                            definitions=[],
                            references=[],
                        )
                    ],
                    references=[],
                ),
            ],
            references=[],
        )
    ),

    (
        # Test function argument discovery
        "kawa.example",
        """
def f(a, b=None, *args, **kwargs):
    pass
        """,

        Module(
            name="kawa.example",
            definitions=[
                Function(
                    name="kawa.example.f",
                    arguments=["a", "b", "*args", "**kwargs"],
                    source_location=(2, 0),
                    definitions=[
                        Variable(name="kawa.example.f.a", source_location=(2, 6)),
                        Variable(name="kawa.example.f.b", source_location=(2, 9)),
                        Variable(name="kawa.example.f.args", source_location=(2, 18)),
                        Variable(name="kawa.example.f.kwargs", source_location=(2, 26)),
                    ],
                )
            ],
        )
    )
])
def test_analyzer(module_name, module_source, expected_output):
    assert analyze(module_name, module_source) == expected_output
