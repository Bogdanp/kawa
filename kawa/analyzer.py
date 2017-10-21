"""The analyzer processes an input Python file and generates a map of
all its FQNs along with some metadata about each one (source location,
docstring, outgoing references, etc.).
"""
import ast
import multipledispatch
import types
import warnings

from collections import namedtuple


class Variable(namedtuple("Variable", ("name", "source_location"))):
    """Represents a variable reference or  declaration.
    """


class Scope(namedtuple("Scope", (
        "name", "arguments", "docstring", "source_location", "definitions", "references",
))):
    """Represents the introduction of a new Scope.
    """

    def __new__(cls, name, arguments=None, docstring=None, source_location=(1, 0), definitions=None, references=None):
        return super().__new__(
            cls, name, arguments, docstring, source_location,
            definitions or [], references or [],
        )


class Module(Scope):
    """Represents a Python module declaration.
    """


class Class(Scope):
    """Represents a Python class declaration.
    """


class Function(Scope):
    """Represents a Python function declaration.
    """


def analyze(module_name, module_source):
    """Return a tree representing all the definitions and references
    inside a given module.

    Parameters:
      module_name(str)
      module_source(str)

    Returns:
      Module
    """
    module = ast.parse(module_source)
    definitions = _find_definitions(module_name, module.body)

    return Module(
        name=module_name,
        docstring=_get_docstring(module),
        definitions=definitions,
        references=[],  # TODO
    )


@multipledispatch.dispatch(str, ast.arg)
def _analyze_definition(parent_name, arg_node):
    return Variable(
        name=f"{parent_name}.{arg_node.arg}",
        source_location=_get_source_location(arg_node),
    )


@multipledispatch.dispatch(str, ast.Name)
def _analyze_definition(parent_name, name_node):
    return Variable(
        name=f"{parent_name}.{name_node.id}",
        source_location=_get_source_location(name_node),
    )


@multipledispatch.dispatch(str, ast.Assign)
def _analyze_definition(parent_name, assign_node):
    for target in assign_node.targets:
        if isinstance(target, ast.Name):
            yield _analyze_definition(parent_name, target)

        elif isinstance(target, ast.Tuple):
            for tuple_target in target.elts:
                yield _analyze_definition(parent_name, tuple_target)


@multipledispatch.dispatch(str, ast.ClassDef)
def _analyze_definition(parent_name, class_node):
    name = f"{parent_name}.{class_node.name}"
    return Class(
        name=name,
        docstring=_get_docstring(class_node),
        source_location=_get_source_location(class_node),
        definitions=_find_definitions(name, class_node.body),
        references=[],  # TODO
    )


@multipledispatch.dispatch(str, ast.FunctionDef)
def _analyze_definition(parent_name, func_node):
    name = f"{parent_name}.{func_node.name}"

    children = []
    for field in ("args", "vararg", "kwonlyargs", "kwarg"):
        field_value = getattr(func_node.args, field, None)
        if not field_value:
            continue

        if isinstance(field_value, list):
            children.extend(field_value)
        else:
            children.append(field_value)

    children += func_node.body
    arguments = [arg.arg for arg in func_node.args.args]
    if func_node.args.vararg:
        arguments.append(f"*{func_node.args.vararg.arg}")

    if func_node.args.kwarg:
        arguments.append(f"**{func_node.args.kwarg.arg}")

    return Function(
        name=name,
        docstring=_get_docstring(func_node),
        arguments=arguments,
        source_location=_get_source_location(func_node),
        definitions=_find_definitions(name, children),
        references=[],  # TODO
    )


def _get_docstring(node):
    docstring = ast.get_docstring(node)
    if docstring:
        return docstring.rstrip()
    return None


def _get_source_location(node):
    return node.lineno, node.col_offset


def _find_definitions(parent_name, node_list):
    definitions = []
    for node in node_list:
        try:
            if not isinstance(node, (ast.Expr, ast.Pass, ast.Raise, ast.Return)):
                res = _analyze_definition(parent_name, node)
                if isinstance(res, (list, types.GeneratorType)):
                    definitions.extend(res)
                else:
                    definitions.append(res)
        except NotImplementedError:
            warnings.warn(f"Cannot analyze {type(node).__name__} nodes.")

    return definitions
