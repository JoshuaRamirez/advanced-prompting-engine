# Spec 10 — MCP Server Surface

## Purpose

Defines the JSON schemas for all 3 MCP tools, 4 MCP prompts, and 3 MCP resources, including tool descriptions that LLMs read to determine when to use each tool.

---

## MCP Tools

### 1. create_prompt_basis

**Description (shown to LLM clients):**

> Measure a natural language intent or pre-formed coordinate across 10 philosophical dimensions and return a construction basis for prompt creation. Use this before constructing any prompt where dimensional precision, philosophical coherence, or systematic completeness matters more than speed.

**Input Schema:**

```json
{
  "type": "object",
  "properties": {
    "intent": {
      "type": "string",
      "description": "Natural language description of the prompt's purpose"
    },
    "coordinate": {
      "type": "object",
      "description": "Pre-formed coordinate with (x,y) positions per branch. Provide this OR intent, not both.",
      "properties": {
        "ontology":       { "$ref": "#/$defs/axis_position" },
        "epistemology":   { "$ref": "#/$defs/axis_position" },
        "axiology":       { "$ref": "#/$defs/axis_position" },
        "teleology":      { "$ref": "#/$defs/axis_position" },
        "phenomenology":  { "$ref": "#/$defs/axis_position" },
        "praxeology":     { "$ref": "#/$defs/axis_position" },
        "methodology":    { "$ref": "#/$defs/axis_position" },
        "semiotics":      { "$ref": "#/$defs/axis_position" },
        "hermeneutics":   { "$ref": "#/$defs/axis_position" },
        "heuristics":     { "$ref": "#/$defs/axis_position" }
      }
    }
  },
  "oneOf": [
    { "required": ["intent"] },
    { "required": ["coordinate"] }
  ],
  "$defs": {
    "axis_position": {
      "type": "object",
      "properties": {
        "x": { "type": "integer", "minimum": 0, "maximum": 9 },
        "y": { "type": "integer", "minimum": 0, "maximum": 9 },
        "weight": { "type": "number", "minimum": 0, "maximum": 1 }
      },
      "required": ["x", "y", "weight"]
    }
  }
}
```

**Output Schema:** The full construction basis as defined in DESIGN.md Construction Output section. See Spec 06, Stage 8 for the complete output structure.

**Errors:**

| Error | Condition |
|---|---|
| `InvalidCoordinate` | Pre-formed coordinate has invalid branch names, out-of-range x/y, or missing required fields |
| `ConflictingCoordinate` | Two specified positions have an EXCLUDES relationship |

---

### 2. explore_space

**Description:**

> Explore the philosophical manifold directly. Inspect graph structure, traverse neighborhoods, find paths between constructs, run stress tests, or triangulate between two coordinates.

**Input Schema:**

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "list_branches",
        "list_constructs",
        "get_construct",
        "get_neighborhood",
        "find_path",
        "get_spoke",
        "stress_test",
        "triangulate"
      ]
    },
    "branch": { "type": "string", "description": "Branch name (for branch-scoped operations)" },
    "x": { "type": "integer", "description": "Grid x-coordinate" },
    "y": { "type": "integer", "description": "Grid y-coordinate" },
    "target_branch": { "type": "string", "description": "Target branch (for find_path)" },
    "target_x": { "type": "integer" },
    "target_y": { "type": "integer" },
    "coordinate": { "type": "object", "description": "For stress_test" },
    "coordinate_a": { "type": "object", "description": "For triangulate" },
    "coordinate_b": { "type": "object", "description": "For triangulate" },
    "classification": { "type": "string", "enum": ["corner", "midpoint", "edge", "center"], "description": "Filter by classification" },
    "provenance": { "type": "string", "enum": ["canonical", "user", "merged"], "default": "merged" }
  },
  "required": ["operation"]
}
```

**Output:** Varies by operation. Each operation returns a JSON object relevant to the query.

---

### 3. extend_schema

**Description:**

> Add constructs or relations to the graph. Constructs are placed at grid positions within a branch. Relations connect two constructs. Contradiction detection is automatic — if your proposed relation contradicts an existing canonical relation, you will be warned before the write occurs.

**Input Schema:**

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["add_construct", "add_relation"]
    },
    "branch": { "type": "string", "description": "For add_construct" },
    "x": { "type": "integer", "minimum": 0, "maximum": 9 },
    "y": { "type": "integer", "minimum": 0, "maximum": 9 },
    "question": { "type": "string", "description": "Epistemic question for this position" },
    "tags": { "type": "array", "items": { "type": "string" } },
    "description": { "type": "string" },
    "source_id": { "type": "string", "description": "For add_relation" },
    "target_id": { "type": "string", "description": "For add_relation" },
    "relation_type": {
      "type": "string",
      "enum": ["COMPATIBLE_WITH", "TENSIONS_WITH", "REQUIRES", "EXCLUDES", "GENERATES", "RESOLVES"]
    },
    "strength": { "type": "number", "minimum": 0, "maximum": 1, "default": 0.5 }
  },
  "required": ["operation"]
}
```

**Output:**

| Result | Structure |
|---|---|
| Success | `{ "status": "created", "id": "..." }` |
| Contradiction | `{ "status": "contradiction", "existing": {...}, "proposed": {...}, "options": ["cancel", "override", "resolve"] }` |
| Error | `{ "status": "error", "message": "..." }` |

---

## MCP Prompts

### 1. orient

**Description:** Understand the philosophical manifold before using it.

**Template:**
```
Read the axiom manifest to understand the 10 philosophical branches.
Read the coordinate schema to understand how positions are specified.
Read the schema manifest to see what constructs currently exist.
```

### 2. build_construction_basis

**Description:** Build a complete construction basis from an intent.

**Template:**
```
1. Call create_prompt_basis with your intent
2. Review the active constructs and their epistemic questions
3. Review the spectrum opposites to understand what your position is NOT
4. Review the spoke profiles for per-branch behavioral signatures
5. Review the central gem for overall coherence
6. Use the construction questions to guide prompt construction
```

### 3. compare_positions

**Description:** Compare two intents dimensionally.

**Template:**
```
1. Call explore_space with operation=triangulate, providing both coordinates
2. Review the per-branch construct intersection
3. Review shared tensions and generative combinations
4. Review spoke profile comparison
```

### 4. resolve_and_construct

**Description:** Build a construction basis and resolve all tensions.

**Template:**
```
1. Call create_prompt_basis with your intent
2. Review the tensions list
3. For each tension, review the resolution paths
4. If no resolution path exists, consider adjusting the coordinate
5. Call explore_space with operation=stress_test to find improvements
```

---

## MCP Resources

### 1. axiom_manifest

**URI:** `ape://axiom_manifest`

**Content:** JSON object containing all 10 branch definitions:

```json
{
  "branches": [
    {
      "id": "ontology",
      "core_question": "What entities and relationships fundamentally exist?",
      "construction_template": "What entities and relationships does this prompt assume exist?",
      "x_axis": "Particular → Universal",
      "y_axis": "Static → Dynamic",
      "causal_order": 0
    }
  ]
}
```

### 2. schema_manifest

**URI:** `ape://schema_manifest`

**Content:** JSON object summarizing current graph state:

```json
{
  "branches": 10,
  "constructs_per_branch": 100,
  "total_constructs": 1000,
  "canonical_constructs": 1000,
  "user_constructs": 0,
  "spectrums": 180,
  "nexi": 90,
  "declared_edges": {
    "COMPATIBLE_WITH": 0,
    "TENSIONS_WITH": 0,
    "REQUIRES": 0,
    "EXCLUDES": 0,
    "GENERATES": 0,
    "RESOLVES": 0
  }
}
```

### 3. coordinate_schema

**URI:** `ape://coordinate_schema`

**Content:** The JSON schema for a valid coordinate object (same as the `coordinate` property in `create_prompt_basis` input schema), plus documentation of what each branch's sub-dimensions mean.
