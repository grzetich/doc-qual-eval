"""Can a model build a working integration from a project's own documentation?

This is the question *Tokens Not Jokin'* asked about REST APIs, pointed at the
protocol these targets actually document. The study measured whether
documentation format changed the quality of AI-generated code against
contamination-free APIs. Here the API is real and the documentation is the
variable under test.

The reason this gate is allowed to exist when code sample execution was
refused: MCP publishes a machine-checkable JSON Schema. A generated server's
declarations can be validated against `$defs/Tool` and friends, and its imports
can be checked against the symbols that actually exist in the cloned SDK. Both
are real oracles. Nothing here asks a model whether the output looks good.

Nothing is executed. Generated servers are parsed and inspected, never run.
Running arbitrary generated code that opens sockets and spawns subprocesses is
not a thing to do on a schedule.
"""

from __future__ import annotations

import ast
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from .model import Finding, GateResult, Tier
from .profile import Declaration, Profile

API_URL = "https://api.anthropic.com/v1/messages"

#: Override with MCPGEN_MODEL. Verify against current model documentation
#: before a run that matters; model identifiers change and a stale one fails
#: the whole gate with an unhelpful 404.
DEFAULT_MODEL = os.environ.get("MCPGEN_MODEL", "claude-sonnet-4-6")




# ---------------------------------------------------------------------------
# generation
# ---------------------------------------------------------------------------

def _bundle_docs(repo_root: Path, paths: list[str], budget: int) -> tuple[str, list[str]]:
    """Assemble the documentation the model is allowed to see.

    Only files from the target repository. If the model can produce a working
    server without these, the docs were not what carried it, and that is worth
    knowing too.
    """
    chunks, used, total = [], [], 0
    resolved: list[Path] = []
    for pattern in paths:
        if any(ch in pattern for ch in "*?["):
            resolved.extend(sorted(repo_root.glob(pattern)))
        else:
            resolved.append(repo_root / pattern)
    for path in resolved:
        rel = str(path.relative_to(repo_root)) if path.is_absolute() else str(path)
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if total + len(text) > budget:
            text = text[: max(0, budget - total)]
        if not text:
            break
        chunks.append(f"===== {rel} =====\n{text}")
        used.append(rel)
        total += len(text)
        if total >= budget:
            break
    return "\n\n".join(chunks), used


def generate(docs: str, capability: str, task: str, model: str,
             timeout: int = 180) -> tuple[str | None, str]:
    """Ask a model to write a server. Returns (code, message)."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None, "ANTHROPIC_API_KEY is unset"

    prompt = (
        "Below is the documentation for the Model Context Protocol and its "
        "Python SDK.\n\n"
        f"{docs}\n\n"
        f"Using only this documentation, write a complete MCP server in Python "
        f"that will {task}. Return only the code in a single Python code "
        f"block, with no explanation before or after."
    )
    body = json.dumps({
        "model": model,
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        API_URL, data=body,
        headers={"content-type": "application/json",
                 "x-api-key": key,
                 "anthropic-version": "2023-06-01"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:200]
        return None, f"API returned {exc.code}: {detail}"
    except Exception as exc:
        return None, f"API call failed: {exc}"

    text = "".join(block.get("text", "") for block in payload.get("content", [])
                   if block.get("type") == "text")
    if "```" in text:
        segment = text.split("```", 2)[1]
        if segment.startswith("python"):
            segment = segment[len("python"):]
        return segment.strip(), "generated"
    return text.strip() or None, "generated without a code fence"


# ---------------------------------------------------------------------------
# oracle 1: declarations validate against the MCP schema
# ---------------------------------------------------------------------------

def _annotation_type(node: ast.expr | None, types: dict) -> dict:
    if node is None:
        return {"type": "string"}
    if isinstance(node, ast.Name):
        return {"type": types.get(node.id, "string")}
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        return {"type": types.get(node.value.id, "string")}
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return {"type": types.get(node.value, "string")}
    return {"type": "string"}


def _decorator_kind(node: ast.expr, names: set[str]) -> tuple[str | None, dict]:
    """Identify @x.tool(...) style decorators and pull their keywords."""
    call_kwargs: dict = {}
    target = node
    if isinstance(node, ast.Call):
        target = node.func
        for kw in node.keywords:
            if isinstance(kw.value, ast.Constant):
                call_kwargs[kw.arg] = kw.value.value
    if isinstance(target, ast.Attribute):
        name = target.attr
        if name in names:
            return name, call_kwargs
    return None, {}


def extract_declarations(code: str, profile: Profile
                         ) -> tuple[dict[str, list[dict]], str | None]:
    """Pull tool, resource, and prompt declarations out of generated source.

    Reads the artifact rather than asking the model what it built. Covers the
    FastMCP decorator style, which is what the Python SDK documentation
    teaches. A server written against the low-level Server API declares its
    capabilities inside handler return values and will come back empty here,
    which is reported rather than scored as a failure.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {}, f"line {exc.lineno}: {exc.msg}"

    found: dict[str, list[dict]] = {d.capability: [] for d in profile.declarations}
    names = profile.decorator_names
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            kind, kwargs = _decorator_kind(decorator, names)
            if kind is None:
                continue
            spec = profile.by_decorator(kind)
            if spec is None:
                continue
            doc = ast.get_docstring(node)
            properties, required = {}, []
            args = node.args
            defaults = len(args.defaults)
            positional = args.args[1:] if args.args and args.args[0].arg in (
                "self", "cls") else args.args
            for index, arg in enumerate(positional):
                if arg.arg in ("ctx", "context"):
                    continue
                properties[arg.arg] = _annotation_type(
                    arg.annotation, profile.type_map)
                if index < len(positional) - defaults:
                    required.append(arg.arg)

            decl = _build(spec, kwargs, node, decorator, properties, required)
            description = kwargs.get("description") or doc
            if description:
                decl["description"] = description
            found.setdefault(spec.capability, []).append(decl)
    return found, None


def _build(spec: Declaration, kwargs: dict, node: ast.AST, decorator: ast.expr,
           properties: dict, required: list) -> dict:
    """Assemble a declaration according to the shape the profile names."""
    name = kwargs.get("name") or getattr(node, "name", "unnamed")
    if spec.shape == "uri_object":
        return {"name": name,
                "uri": kwargs.get("uri") or _first_positional(decorator)}
    if spec.shape == "argument_list":
        return {"name": name,
                "arguments": [{"name": key} for key in properties]}
    # schema_object, the default
    return {
        "name": name,
        "inputSchema": {"type": "object", "properties": properties,
                        **({"required": required} if required else {})},
    }


def _first_positional(decorator: ast.expr) -> str | None:
    if isinstance(decorator, ast.Call) and decorator.args:
        first = decorator.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            return first.value
    return None


def validate_declarations(declarations: dict[str, list[dict]],
                          schema: dict, profile: Profile) -> list[str]:
    """Validate each declaration against the published MCP schema.

    This is the oracle. A declaration either satisfies `$defs/Tool` or it does
    not, and the answer does not depend on anyone's judgement.
    """
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema not installed, declarations unchecked"]

    defs = schema.get("$defs", {})
    errors: list[str] = []
    for kind, items in declarations.items():
        declaration = profile.by_capability(kind)
        name = declaration.schema_def if declaration else None
        if not name or name not in defs:
            continue
        sub = {"$defs": defs, "$ref": f"#/$defs/{name}"}
        validator = jsonschema.Draft202012Validator(sub)
        for item in items:
            for error in validator.iter_errors(item):
                errors.append(
                    f"{kind[:-1]} '{item.get('name', '?')}': {error.message[:120]}"
                )
    return errors


# ---------------------------------------------------------------------------
# oracle 2: imported symbols exist in the SDK
# ---------------------------------------------------------------------------

def sdk_symbols(sdk_root: Path) -> dict[str, set[str]]:
    """Map module path to the names it defines, read from the cloned SDK.

    Lets the gate tell an invented API surface from a real one without
    installing anything. A model that imports `mcp.server.FastMCP` when the
    class lives elsewhere has been failed by the documentation, and that is a
    finding about the docs.
    """
    table: dict[str, set[str]] = {}
    src = sdk_root / "src"
    # A src layout can hold several distribution directories, and the
    # directory name is not the import name: src/mcp-types/ contains the
    # mcp_types package. Treat each package directory under src as its own
    # root, or the module paths come out wrong and every import looks invented.
    roots: list[Path] = []
    if src.exists():
        for child in sorted(src.iterdir()):
            if not child.is_dir():
                continue
            if (child / "__init__.py").exists():
                # The directory is itself the importable package.
                roots.append(child)
                continue
            # Otherwise it is a distribution directory whose name need not
            # match the import name, as with src/mcp-types/mcp_types.
            roots.extend(d for d in sorted(child.iterdir())
                         if d.is_dir() and (d / "__init__.py").exists())
    if not roots:
        roots = [sdk_root]

    for base in roots:
      package_parent = base.parent
      for path in base.rglob("*.py"):
        if "tests" in path.parts or path.name.startswith("test_"):
            continue
        rel = path.relative_to(package_parent)
        parts = list(rel.parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1][:-3]
        module = ".".join(parts)
        if not module:
            continue
        names: set[str] = set()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    names.add(alias.asname or alias.name)
        table.setdefault(module, set()).update(names)
    return table


def check_imports(code: str, table: dict[str, set[str]],
                  namespace: str) -> list[str]:
    """Report imports from the SDK namespace that do not resolve."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    problems: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if not namespace or node.module.split(".")[0] != namespace:
                continue
            known = table.get(node.module)
            if known is None:
                problems.append(f"module '{node.module}' does not exist in the SDK")
                continue
            for alias in node.names:
                if alias.name != "*" and alias.name not in known:
                    problems.append(
                        f"'{alias.name}' is not defined in '{node.module}'")
    return problems


# ---------------------------------------------------------------------------
# scoring
# ---------------------------------------------------------------------------

def score_generation(code: str, capability: str, schema: dict,
                     table: dict[str, set[str]], profile: Profile) -> dict:
    """Score one generated server. Every criterion is checkable."""
    criteria: dict[str, bool] = {}
    notes: list[str] = []

    declarations, syntax_error = extract_declarations(code, profile)
    criteria["parses"] = syntax_error is None
    if syntax_error:
        notes.append(f"syntax error at {syntax_error}")
        return {"criteria": criteria, "notes": notes, "score": 0.0}

    namespace = profile.import_namespace
    criteria["imports_sdk"] = bool(namespace) and namespace in code \
        and "import" in code

    # An empty symbol table means the SDK source could not be read, so the
    # check is unavailable rather than failed. Reporting "every import is
    # invented" because this runner could not build a table would be the
    # pipeline blaming the documentation for its own gap.
    if table:
        import_problems = check_imports(code, table, namespace)
        criteria["imports_resolve"] = not import_problems
        notes += import_problems[:4]
    else:
        notes.append("SDK symbol table unavailable, imports unchecked")

    declared = declarations.get(capability, [])
    criteria["declares_capability"] = bool(declared)
    if not declared:
        notes.append(f"no {capability} declared via the documented decorators")

    schema_errors = validate_declarations(
        {capability: declared} if declared else {}, schema, profile)
    criteria["schema_valid"] = bool(declared) and not schema_errors
    notes += schema_errors[:4]

    criteria["documented"] = all(
        item.get("description") for item in declared) if declared else False
    if declared and not criteria["documented"]:
        notes.append("declarations carry no description, so a client sees an "
                     "unlabelled capability")

    passed = sum(1 for value in criteria.values() if value)
    return {"criteria": criteria, "notes": notes,
            "score": round(10 * passed / len(criteria), 1),
            "declared": declared}


# ---------------------------------------------------------------------------
# gate
# ---------------------------------------------------------------------------

def gate_generation(target: str, repo_root: Path, sdk_root: Path,
                    schema_path: Path | None, doc_paths: list[str],
                    profile: Profile, threshold: float,
                    model: str = DEFAULT_MODEL,
                    doc_budget: int = 60000) -> GateResult:
    """Generate against a profile and score the result.

    Schema validation is the strongest oracle here, so its absence is reported
    rather than passed over: a run without it is still useful and is a weaker
    claim, and the summary says which one you got.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return GateResult("generation", "skipped", "ANTHROPIC_API_KEY is unset")
    if profile.language != "python":
        # Extraction reads Python syntax trees. Guessing at another language
        # would produce confident nonsense.
        return GateResult(
            "generation", "skipped",
            f"profile '{profile.name}' targets {profile.language}; only "
            f"python extraction is implemented",
        )
    if not profile.declarations or not profile.tasks:
        return GateResult("generation", "error",
                          f"profile '{profile.name}' declares no capabilities")

    schema: dict = {}
    schema_note = ""
    if schema_path and schema_path.exists():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    else:
        schema_note = (" without schema validation, so declarations were "
                       "extracted but not checked against a specification")

    table = sdk_symbols(sdk_root)
    docs, used = _bundle_docs(repo_root, doc_paths, doc_budget)
    if not docs:
        return GateResult("generation", "error",
                          "no documentation files matched")

    findings: list[Finding] = []
    scores: list[float] = []
    for capability, task in profile.tasks.items():
        code, message = generate(docs, capability, task, model)
        if code is None:
            return GateResult("generation", "error", f"{capability}: {message}")
        result = score_generation(code, capability, schema, table, profile)
        scores.append(result["score"])
        if result["score"] < threshold:
            failed = [k for k, v in result["criteria"].items() if not v]
            findings.append(Finding(
                target=target, gate="mcp_generation",
                kind="generation_gap",
                message=(f"{capability}: scored {result['score']}/10, failed "
                         f"{', '.join(failed)}"),
                tier=Tier.REVIEW_ONLY,
                evidence={"capability": capability,
                          "criteria": result["criteria"],
                          "notes": result["notes"],
                          "model": model, "profile": profile.name,
                          "docs_used": used},
            ))

    mean = sum(scores) / len(scores) if scores else 0.0
    return GateResult(
        "generation", "ok",
        f"profile {profile.name}: mean {mean:.1f}/10 across {len(scores)} "
        f"capabilities using {model}, {len(used)} documentation files in "
        f"context{schema_note}",
        findings,
    )
