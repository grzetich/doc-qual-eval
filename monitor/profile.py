"""What a generation profile describes.

The generation gate started out with MCP and Python baked into five constants
scattered through the scorer. That made it a demonstration rather than a tool:
useful to whoever wrote it, closed to everyone else.

A profile lifts those decisions into configuration. Anything that says "this
is what MCP calls a tool" or "this is how a Python decorator looks" belongs
here, so pointing the gate at a different protocol or SDK is an edit to
`targets.yml` rather than a fork.

What still needs code is a new language. Extraction reads Python syntax trees,
so a TypeScript SDK needs a different extractor. The profile says which
language it expects and the gate refuses rather than guessing when it does not
match, because silently mis-parsing a language is worse than declining it.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Declaration:
    """One kind of thing a server can declare.

    `shape` names how a declaration is assembled from a decorated function:

    - `schema_object`: name plus an inputSchema built from the signature,
      which is how MCP tools work
    - `uri_object`: name plus a URI taken from the decorator argument, which
      is how MCP resources work
    - `argument_list`: name plus a list of named arguments, which is how MCP
      prompts work

    `schema_def` is the definition in the target's JSON Schema that the
    assembled declaration is validated against. Leave it unset and the
    declaration is extracted but not schema-checked, which costs the strongest
    oracle, so it is worth setting where a schema exists.
    """

    decorator: str
    capability: str
    shape: str = "schema_object"
    schema_def: str | None = None


@dataclass
class Profile:
    """A protocol and SDK the generation gate knows how to score."""

    name: str = "mcp-python"
    language: str = "python"
    #: Imports from this top-level package are checked against the SDK symbol
    #: table. Imports from anywhere else are somebody else's problem.
    import_namespace: str = "mcp"
    declarations: list[Declaration] = field(default_factory=list)
    #: capability name to the job the model is asked to do. One generation
    #: each, so this list is also the cost of a run.
    tasks: dict[str, str] = field(default_factory=dict)
    #: Python annotation names to JSON Schema types.
    type_map: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        declarations = [
            Declaration(
                decorator=item["decorator"],
                capability=item.get("capability", item["decorator"] + "s"),
                shape=item.get("shape", "schema_object"),
                schema_def=item.get("schema_def"),
            )
            for item in data.get("declarations", [])
        ]
        return cls(
            name=data.get("name", "unnamed"),
            language=data.get("language", "python"),
            import_namespace=data.get("import_namespace", ""),
            declarations=declarations,
            tasks=data.get("tasks", {}),
            type_map=data.get("type_map", DEFAULT_TYPE_MAP),
        )

    def by_decorator(self, name: str) -> Declaration | None:
        for declaration in self.declarations:
            if declaration.decorator == name:
                return declaration
        return None

    def by_capability(self, name: str) -> Declaration | None:
        for declaration in self.declarations:
            if declaration.capability == name:
                return declaration
        return None

    @property
    def decorator_names(self) -> set[str]:
        return {d.decorator for d in self.declarations}


DEFAULT_TYPE_MAP = {
    "int": "integer", "float": "number", "str": "string", "bool": "boolean",
    "list": "array", "dict": "object", "bytes": "string",
    "Any": "object", "None": "null",
}
