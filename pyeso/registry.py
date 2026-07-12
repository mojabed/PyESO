from __future__ import annotations

from collections.abc import Iterator
from typing import Optional

from pyeso.models import (
    Constant,
    Deprecation,
    Domain,
    Event,
    EventInfo,
    Function,
    Table,
)


class Registry:
    """In-memory registry of the entire known ESOUI API surface."""

    def __init__(self) -> None:
        self._functions: dict[str, Function] = {}
        self._constants: dict[str, Constant] = {}
        self._events: dict[str, Event] = {}
        self._event_infos: dict[str, EventInfo] = {}
        self._tables: dict[str, Table] = {}
        self._deprecations: dict[str, Deprecation] = {}
        self._names: set[str] = set()
        self._domain_map: dict[str, Domain] = {}
        self._source: str = "seed"
        self._object_methods: dict[str, dict[str, Function]] = {}
        self._all_method_names: set[str] = set()

    def add_function(self, fn: Function) -> None:
        self._functions[fn.name] = fn
        self._names.add(fn.name)

    def add_constant(self, c: Constant) -> None:
        self._constants[c.name] = c
        self._names.add(c.name)

    def add_event(self, ev: Event) -> None:
        self._events[ev.name] = ev
        self._names.add(ev.name)

    def add_event_info(self, ev: EventInfo) -> None:
        """Register a typed event from ESOUIDocumentation.txt."""
        self._event_infos[ev.name] = ev
        self._names.add(ev.name)

    def add_table(self, tbl: Table) -> None:
        self._tables[tbl.name] = tbl
        self._names.add(tbl.name)

    def add_deprecation(self, dep: Deprecation) -> None:
        self._deprecations[dep.old_name] = dep
        self._names.add(dep.old_name)

    def add_name(self, name: str) -> None:
        """Register a name as known (builtins, keywords, etc.)."""
        self._names.add(name)

    def add_constant_name(self, name: str) -> None:
        """Register a constant name without creating a full Constant object."""
        self._names.add(name)

    def add_method(self, class_name: str, method_name: str, fn: Function) -> None:
        """Register a method on an Object API class."""
        if class_name not in self._object_methods:
            self._object_methods[class_name] = {}
        self._object_methods[class_name][method_name] = fn
        self._all_method_names.add(method_name)

    def set_domain(self, name: str, domain: Domain) -> None:
        self._domain_map[name] = domain

    def is_known(self, name: str) -> bool:
        return name in self._names

    def get_function(self, name: str) -> Optional[Function]:
        return self._functions.get(name)

    def get_constant(self, name: str) -> Optional[Constant]:
        return self._constants.get(name)

    def get_event(self, name: str) -> Optional[Event]:
        return self._events.get(name)

    def get_event_info(self, name: str) -> Optional[EventInfo]:
        """Get typed event info (from ESOUIDocumentation.txt)."""
        return self._event_infos.get(name)

    def is_event(self, name: str) -> bool:
        """Check if name is a known event."""
        return name in self._event_infos

    def get_table(self, name: str) -> Optional[Table]:
        return self._tables.get(name)

    def get_deprecation(self, name: str) -> Optional[Deprecation]:
        return self._deprecations.get(name)

    def is_deprecated(self, name: str) -> bool:
        return name in self._deprecations

    def domain_of(self, name: str) -> Optional[Domain]:
        return self._domain_map.get(name)

    def is_known_method(self, method_name: str) -> bool:
        """Check if method_name exists on ANY ESOUI Object API class."""
        return method_name in self._all_method_names

    def get_method(self, class_name: str, method_name: str) -> Optional[Function]:
        """Get a specific method on a specific class."""
        cls_methods = self._object_methods.get(class_name)
        if cls_methods:
            return cls_methods.get(method_name)
        return None

    def find_method(self, method_name: str) -> Optional[Function]:
        """Find a method by name across all Object API classes.
        Returns the first match (for existence/param checking)."""
        for cls_methods in self._object_methods.values():
            if method_name in cls_methods:
                return cls_methods[method_name]
        return None

    @property
    def functions(self) -> Iterator[Function]:
        return iter(self._functions.values())

    @property
    def constants(self) -> Iterator[Constant]:
        return iter(self._constants.values())

    @property
    def events(self) -> Iterator[Event]:
        return iter(self._events.values())

    @property
    def tables(self) -> Iterator[Table]:
        return iter(self._tables.values())

    @property
    def deprecations(self) -> Iterator[Deprecation]:
        return iter(self._deprecations.values())

    def search(self, query: str) -> list[Function]:
        """Case-insensitive search over function names."""
        q = query.lower()
        return [f for name, f in self._functions.items() if q in name.lower()]

    def by_domain(self, domain: Domain) -> list[Function]:
        """Get all functions in a domain category."""
        return [
            self._functions[name]
            for name, d in self._domain_map.items()
            if d == domain and name in self._functions
        ]

    @property
    def function_count(self) -> int:
        return len(self._functions)

    @property
    def constant_count(self) -> int:
        return len(self._constants)

    @property
    def event_count(self) -> int:
        return len(self._events)

    @property
    def event_info_count(self) -> int:
        return len(self._event_infos)

    @property
    def table_count(self) -> int:
        return len(self._tables)

    @property
    def deprecation_count(self) -> int:
        return len(self._deprecations)

    @property
    def total_known(self) -> int:
        return len(self._names)

    @property
    def source_label(self) -> str:
        return self._source

    @property
    def object_class_count(self) -> int:
        return len(self._object_methods)

    def get_signature(self, name: str) -> Optional[Function]:
        """Backward-compatible alias for get_function()."""
        return self.get_function(name)

    def get_deprecated(self, name: str) -> Optional[Deprecation]:
        """Backward-compatible alias for get_deprecation()."""
        return self.get_deprecation(name)
