# kawa

Kawa is a static analaysis tool for Python projects.

## Setup

1. Install [pipenv][pipenv].
1. Run `pipenv install --dev`

### Running the test suite

1. Run `pipenv run py.test`


## Usage examples

```
$ python -m kawa describe tests/examples/reader.py 1 0
{
    "type": "class",
    "name": "tests.examples.reader.Reader",
    "docstring": null,
    "location": [
        1,
        0
    ]
}
```

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
    "location": [
        12,
        0
    ]
}
```

```
$ python -m kawa describe tests/examples/reader.py 18 10
{
    "type": "reference",
    "name": "tests.examples.reader.read",
    "location": [
        18,
        10
    ]
}
```


[pipenv]: https://docs.pipenv.org/#install-pipenv-today
