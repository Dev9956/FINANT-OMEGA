"""FININT OMEGA — Tool registry with typed tool definitions."""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, Field


class ParameterType(str, Enum):
    STRING = "string"
    FLOAT = "float"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    LIST = "list"


class ParameterDef(BaseModel):
    """Definition of a tool parameter."""

    name: str
    param_type: ParameterType = ParameterType.STRING
    description: str = ""
    required: bool = False
    default: Any = None


class ToolDefinition(BaseModel):
    """Full definition of an available tool."""

    name: str
    description: str = ""
    parameters: list[ParameterDef] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    enabled: bool = True


class ToolRegistry:
    """Registry for typed tool definitions and their implementations."""

    def __init__(self) -> None:
        self._definitions: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, Callable] = {}

    def register(self, definition: ToolDefinition, handler: Callable | None = None) -> None:
        self._definitions[definition.name] = definition
        if handler:
            self._handlers[definition.name] = handler

    def unregister(self, name: str) -> None:
        self._definitions.pop(name, None)
        self._handlers.pop(name, None)

    def get_definition(self, name: str) -> ToolDefinition | None:
        return self._definitions.get(name)

    def get_handler(self, name: str) -> Callable | None:
        return self._handlers.get(name)

    def list_tools(self, enabled_only: bool = True) -> list[ToolDefinition]:
        tools = list(self._definitions.values())
        if enabled_only:
            tools = [t for t in tools if t.enabled]
        return tools

    def search(self, query: str, tags: list[str] | None = None) -> list[ToolDefinition]:
        results: list[ToolDefinition] = []
        q = query.lower()
        for tool in self._definitions.values():
            if q in tool.name.lower() or q in tool.description.lower():
                if tags is None or any(t in tool.tags for t in tags):
                    results.append(tool)
        return results

    def execute(self, name: str, **kwargs) -> Any:
        handler = self._handlers.get(name)
        if handler is None:
            raise ValueError(f"Tool '{name}' not registered or no handler")
        return handler(**kwargs)
