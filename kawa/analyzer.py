"""The analyzer processes an input Python file and generates a map of
all its FQNs along with some metadata about each one (source location,
docstring, outgoing references, etc.).
"""
import ast
import multipledispatch
import types
import warnings

from collections import namedtuple


class SourceLocation(namedtuple("SourceLocation", (
        "filename", "line_number", "column_offset",
))):
    pass


class Variable(namedtuple("Variable", ("name", "source_location"))):
    """Represents a variable declaration.
    """

    def flatten(self):
        yield self

    @property
    def metadata(self):
        return {
            "type": "variable",
            "name": self.name,
            "location": self.source_location._asdict(),
        }


class Reference(namedtuple("Reference", ("name", "source_location"))):
    """Represents a reference.
    """

    def flatten(self):
        yield self

    @property
    def metadata(self):
        return {
            "type": "reference",
            "name": self.name,
            "location": self.source_location._asdict(),
        }


class Scope(namedtuple("Scope", (
        "name", "arguments", "docstring", "source_location", "definitions", "references",
))):
    """Represents the introduction of a new Scope.
    """

    def __new__(cls, name, arguments=None, docstring=None, source_location=None, definitions=None, references=None):
        return super().__new__(
            cls, name, arguments, docstring, source_location,
            definitions or [], references or [],
        )

    def flatten(self):
        yield self

        for definition in self.definitions:
            yield from definition.flatten()

        for reference in self.references:
            yield from reference.flatten()


class Module(Scope):
    """Represents a Python module declaration.
    """

    @property
    def metadata(self):
        return {
            "type": "module",
            "name": self.name,
            "docstring": self.docstring,
            "location": self.source_location._asdict(),
        }


class Class(Scope):
    """Represents a Python class declaration.
    """

    @property
    def metadata(self):
        return {
            "type": "class",
            "name": self.name,
            "docstring": self.docstring,
            "location": self.source_location._asdict(),
        }


class Function(Scope):
    """Represents a Python function declaration.
    """

    @property
    def metadata(self):
        return {
            "type": "function",
            "name": self.name,
            "arguments": self.arguments,
            "docstring": self.docstring,
            "location": self.source_location._asdict(),
        }


class Analyzer:
    """Find all the definitions and references inside a module.
    """

    def __init__(self, filename, module_name, module_source):
        self.filename = filename
        self.module_name = module_name
        self.module_source = module_source

    def analyze(self):
        """Return a tree representing all the definitions and references
        inside the module.

        Returns:
          Module
        """
        module = ast.parse(self.module_source)
        return Module(
            name=self.module_name,
            docstring=_get_docstring(module),
            source_location=SourceLocation(self.filename, 0, 0),
            definitions=self._find_definitions(self.module_name, module.body),
            references=self._find_references(self.module_name, module.body),
        )

    @multipledispatch.dispatch(str, ast.arg)
    def _analyze_definition(self, parent_name, arg_node):
        return Variable(
            name=f"{parent_name}.{arg_node.arg}",
            source_location=self._get_source_location(arg_node),
        )

    @multipledispatch.dispatch(str, ast.Name)
    def _analyze_definition(self, parent_name, name_node):
        return Variable(
            name=f"{parent_name}.{name_node.id}",
            source_location=self._get_source_location(name_node),
        )

    @multipledispatch.dispatch(str, ast.Assign)
    def _analyze_definition(self, parent_name, assign_node):
        for target in assign_node.targets:
            if isinstance(target, ast.Name):
                yield self._analyze_definition(parent_name, target)

            elif isinstance(target, ast.Tuple):
                for tuple_target in target.elts:
                    yield self._analyze_definition(parent_name, tuple_target)

    @multipledispatch.dispatch(str, ast.ClassDef)
    def _analyze_definition(self, parent_name, class_node):
        name = f"{parent_name}.{class_node.name}"
        return Class(
            name=name,
            docstring=_get_docstring(class_node),
            source_location=self._get_source_location(class_node),
            definitions=self._find_definitions(name, class_node.body),
            references=self._find_references(name, class_node.body),
        )

    @multipledispatch.dispatch(str, ast.FunctionDef)
    def _analyze_definition(self, parent_name, func_node):
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
            source_location=self._get_source_location(func_node),
            definitions=self._find_definitions(name, children),
            references=self._find_references(name, func_node.body),
        )

    @multipledispatch.dispatch(str, ast.Call)
    def _analyze_reference(self, parent_name, call_node):
        yield from self._analyze_reference(parent_name, call_node.func)

        for arg in call_node.args:
            yield from self._analyze_reference(parent_name, arg)

        for keyword in call_node.keywords:
            yield from self._analyze_reference(parent_name, keyword.arg)

    @multipledispatch.dispatch(str, (ast.Assign, ast.Expr, ast.Return))
    def _analyze_reference(self, parent_name, node):
        try:
            yield from self._analyze_reference(parent_name, node.value)
        except NotImplementedError:
            pass

    @multipledispatch.dispatch(str, ast.Attribute)
    def _analyze_reference(self, parent_name, node):
        try:
            yield from self._analyze_reference(parent_name, node.value)
        except NotImplementedError:
            pass

    @multipledispatch.dispatch(str, ast.Name)
    def _analyze_reference(self, parent_name, name_node):
        yield Reference(
            name=f"{parent_name}.{name_node.id}",
            source_location=self._get_source_location(name_node),
        )

    def _get_source_location(self, node):
        return SourceLocation(self.filename, node.lineno, node.col_offset)

    def _find_definitions(self, parent_name, node_list):
        definitions = []
        for node in node_list:
            try:
                if not isinstance(node, (ast.Expr, ast.Pass, ast.Raise, ast.Return)):
                    res = self._analyze_definition(parent_name, node)
                    if isinstance(res, (list, types.GeneratorType)):
                        definitions.extend(res)
                    else:
                        definitions.append(res)
            except NotImplementedError:
                warnings.warn(f"Cannot analyze {type(node).__name__} nodes.")

        return definitions

    def _find_references(self, parent_name, node_list):
        references = []
        for node in node_list:
            try:
                res = self._analyze_reference(parent_name, node)
                if isinstance(res, (list, types.GeneratorType)):
                    references.extend(res)
                else:
                    references.append(res)
            except NotImplementedError:
                pass

        return references


def _get_docstring(node):
    docstring = ast.get_docstring(node)
    if docstring:
        return docstring.rstrip()
    return None
