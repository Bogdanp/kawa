# kawa

Kawa is a static analaysis tool for Python projects.

## Setup

1. Install [pipenv][pipenv].
1. Run `pipenv install --dev`
1. Run `pipenv shell`

### Running the test suite

1. Run `pipenv run py.test`


## Usage examples


### `describe`

```
$ python -m kawa describe tests/examples/reader.py 1 0
{
    "type": "class",
    "name": "tests.examples.reader.Reader",
    "docstring": null,
    "location": {
        "filename": "/Users/bogdan/sandbox/kawa/tests/examples/reader.py",
        "line_number": 1,
        "column_offset": 0
    }
}
```

```
$ python -m kawa describe tests/examples/reader.py 18 10
{
    "type": "reference",
    "name": "tests.examples.reader.read",
    "location": {
        "filename": "/Users/bogdan/sandbox/kawa/tests/examples/reader.py",
        "line_number": 18,
        "column_offset": 10
    }
}
```

```
$ git clone https://github.com/Bogdanp/dramatiq
$ python -m kawa describe dramatiq/dramatiq/actor.py 10 4
{
    "type": "function",
    "name": "dramatiq.actor.actor",
    "arguments": [
        "fn",
        "**options"
    ],
    "docstring": "Declare an actor.\n\nExamples:\n\n  >>> import dramatiq\n\n  >>> @dramatiq.actor\n  ... def add(x, y):\n  ...   print(x + y)\n  ...\n  >>> add\n  Actor(<function add at 0x106c6d488>, queue_name='default', actor_name='add')\n\n  >>> add(1, 2)\n  3\n\n  >>> add.send(1, 2)\n  Message(\n    queue_name='default',\n    actor_name='add',\n    args=(1, 2), kwargs={}, options={},\n    message_id='e0d27b45-7900-41da-bb97-553b8a081206',\n    message_timestamp=1497862448685)\n\nParameters:\n  fn(callable): The function to wrap.\n  actor_name(str): The name of the actor.\n  queue_name(str): The name of the queue to use.\n  priority(int): The actor's global priority.  If two tasks have\n    been pulled on a worker concurrently and one has a higher\n    priority than the other then it will be processed first.\n    Lower numbers represent higher priorities.\n  broker(Broker): The broker to use with this actor.\n  \\**options(dict): Arbitrary options that vary with the set of\n    middleware that you use.  See ``get_broker().actor_options``.\n\nReturns:\n  Actor: The decorated function.",
    "location": {
        "filename": "/Users/bogdan/sandbox/dramatiq/dramatiq/actor.py",
        "line_number": 10,
        "column_offset": 0
    }
}
```

### `find_definition`

```
$ python -m kawa find_definition tests/examples/reader.py 18 10
{
    "type": "function",
    "name": "tests.examples.reader.read",
    "arguments": [
        "filename",
        "count"
    ],
    "docstring": "Read \"count\" bytes from \"filename\".",
    "location": {
        "filename": "/Users/bogdan/sandbox/kawa/tests/examples/reader.py",
        "line_number": 12,
        "column_offset": 0
    }
}
```

### `find_references`

```
$ python -m kawa find_usages tests/examples/reader.py 12 9
[
    {
        "type": "variable",
        "name": "tests.examples.reader.read.filename",
        "location": {
            "filename": "/Users/bogdan/sandbox/kawa/tests/examples/reader.py",
            "line_number": 12,
            "column_offset": 9
        }
    },
    {
        "type": "reference",
        "name": "tests.examples.reader.read.filename",
        "location": {
            "filename": "/Users/bogdan/sandbox/kawa/tests/examples/reader.py",
            "line_number": 15,
            "column_offset": 18
        }
    }
]
```


## Implementation

Kawa works by walking a module's AST and converting it to a tree of
definitions and references.  Every definition and every reference in
the tree is assigned a fully-qualified name and some metadata like its
poisition in the file, its docstring, its arguments, etc..  The tree
is then stored by the Indexer (a graph-like database -- if you squint)
which is able to look up those entities by their position in a file.


## TODOs

* [x] Implement scoped lookups.
* [x] Add support for finding usages.
* [ ] Add an "interactive" mode so that editors can spawn a Kawa
  process and interface with it via pipes.  That way they won't have
  to take the perf. hit of spawning a new process every time the user
  wants to look something up.
* [ ] Add an HTTP mode for editors that can't easily use pipes.
* [ ] Add module autodiscovery and silently index them in the
  background.
* [ ] Add a way to serialize and load the indexer to/from disk.


## Caveats

Kawa uses the builtin `ast` module from Python, as such it can only
operate on syntactically valid files.  To work around this, we can
either use a lexer-based approach instead or we can write a custom
parser that intelligently skips past syntactic errors.

Definition lookup from within nested scopes is not currently
implemented.


[pipenv]: https://docs.pipenv.org/#install-pipenv-today
