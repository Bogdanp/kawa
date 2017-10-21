import os

from collections import defaultdict

from .analyzer import Reference, analyze
from .common import find_qualified_name


class Indexer:
    """The indexer keeps track of a set of modules in order to
    facilitate analyzed entity lookup.

    Attributes:
      modules(dict[str, entity])
    """

    def __init__(self):
        self.modules = {}
        self.entities_by_fqn = {}
        self.entities_by_module = {}
        self.source_locations_by_module = {}
        self.references_by_fqn = defaultdict(list)

    def index_file(self, filename, module_name=None):
        """Add a file to the index.

        Parameters:
          filename(str)
        """
        filename = os.path.abspath(filename)
        with open(filename, "r") as f:
            module_name = module_name or find_qualified_name(filename)
            module_source = f.read()

        self.modules[module_name] = module = analyze(module_name, module_source)
        self.entities_by_module[module_name] = entities_by_module = {}
        self.source_locations_by_module[module_name] = source_locations = defaultdict(dict)

        entities = self.entities_by_fqn
        references = []
        for entity in module.flatten():
            location = entity.source_location
            if not isinstance(entity, Reference):
                entities[entity.name] = entity
                entities_by_module[entity.name] = entity

            else:
                references.append(entity)

            source_locations[location.line_number][location.column_offset] = entity

        for reference in references:
            name = self._resolve_reference(reference)
            self.references_by_fqn[name].append(reference)

    def lookup_entity(self, filename, line_number, column_offset):
        """Look up the at a given location.

        Returns:
          An object representing the entity or None.
        """
        module_name = find_qualified_name(filename)
        if module_name not in self.modules:
            self.index_file(filename)

        source_locations = self.source_locations_by_module[module_name]
        columns_at_line = source_locations[line_number]
        if not columns_at_line:
            return None

        closest_column = 0
        for line_column, entity in columns_at_line.items():
            if line_column == column_offset:
                return entity

            elif line_column < column_offset:
                closest_column = line_column

        return columns_at_line[closest_column]

    def lookup_metadata(self, filename, line_number, column_offset):
        """Look up the metadata of an entity.

        Returns:
          A dictionary describing the entity or None.
        """
        entity = self.lookup_entity(filename, line_number, column_offset)
        if not entity:
            return None
        return entity.metadata

    def lookup_definition(self, filename, line_number, column_offset):
        """Look up the definition of an entity.

        Returns:
          A dictionary describing where the entity is defined or None.
        """
        module_name = find_qualified_name(filename)
        entity = self.lookup_entity(filename, line_number, column_offset)
        if not entity:
            return None

        if not isinstance(entity, Reference):
            return entity.metadata

        try:
            return self.entities_by_module[module_name][entity.name].metadata
        except KeyError:
            name = self._resolve_reference(entity)
            return self.entities_by_fqn[name].metadata

    def lookup_references(self, filename, line_number, column_offset):
        """Look up the list of references of an entity.

        Returns:
          A list of dictionaries describing the references to the entity.
        """
        entity = self.lookup_entity(filename, line_number, column_offset)
        if not entity:
            return []

        references = [entity] + self.references_by_fqn[entity.name]
        return [entity.metadata for entity in references]

    def _resolve_reference(self, reference):
        name = reference.name
        while True:
            if name in self.entities_by_fqn or "." not in name:
                return name

            # foo.bar.baz.x -> foo.bar.x
            pieces = name.split(".")
            pieces = pieces[:-2] + [pieces[-1]]
            name = ".".join(pieces)
