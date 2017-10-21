import os

from collections import defaultdict

from .analyzer import analyze
from .common import find_qualified_name


class Indexer:
    """The indexer keeps track of a set of modules in order to
    facilitate analyzed entity lookup.

    Attributes:
      modules(dict[str, entity])
    """

    def __init__(self):
        self.modules = {}
        self.entities_by_module = {}
        self.source_locations_by_module = {}

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

        self.entities_by_module[module_name] = entities = {}
        self.source_locations_by_module[module_name] = source_locations = defaultdict(dict)
        for entity in module.flatten():
            location = entity.source_location
            entities[entity.name] = entity
            source_locations[location.line_number][location.column_offset] = entity

    def lookup_entity(self, filename, line_number, column_offset):
        """Look up the at a given location.

        Parameters:
          filename(str):
          line_number(int):
          column_offset(int)

        Returns:
          The entity being looked up or None.
        """
        module_name = find_qualified_name(filename)
        if module_name not in self.modules:
            self.index_file(filename)

        try:
            source_locations = self.source_locations_by_module[module_name]
            columns_at_line = source_locations[line_number]
        except KeyError:
            return None

        closest_column = 0
        for line_column, entity in columns_at_line.items():
            if line_column == column_offset:
                return entity

            elif line_column < column_offset:
                closest_column = line_column

        return columns_at_line[closest_column]

    def lookup_metadata(self, filename, line_number, column_offset):
        """Look up the metadata of the entity at a given location.

        Parameters:
          filename(str):
          line_number(int):
          column_offset(int)

        Returns:
          The metadata of the entity or None.
        """
        entity = self.lookup_entity(filename, line_number, column_offset)
        if not entity:
            return None
        return entity.metadata
