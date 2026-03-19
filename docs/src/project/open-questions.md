# Open Questions

Pending design decisions to resolve during implementation.

## ~~Q001: `_io` Subpackage Naming~~ --- RESOLVED

Keeping `_io`.
Can revisit later if the stdlib shadow causes real problems.

## ~~Q002: MCP Tool Name Format~~ --- RESOLVED

Moved to [Decisions](decisions.md) as D012.

## ~~Q003: JSON-RPC Batch Requests~~ --- DEFERRED

Deferred.
No known MCP client sends batch requests.
The spec does not require servers to support them.
Can add later if a client needs it.

## ~~Q004: Session Cleanup Strategy~~ --- RESOLVED

Moved to [Decisions](decisions.md) as D015.

## Q005: Options Flow UX for Tristate Control

**Question:** How should the options flow present hundreds of HA services for
enable/disable control?

**Context:** A typical HA instance has 200+ services.
Showing all of them in a single form is unusable.
Options: group by domain, search/filter, only show non-default (overridden)
services, multi-step flow.

**No strong leaning yet.**

## ~~Q006: HA Service Call Error Mapping~~ --- RESOLVED

Resolved in the implementation plan (Stage 8).  `HamsterEffectHandler`
catches `ServiceNotFound`, `ServiceValidationError`, `HomeAssistantError`,
and generic `Exception`, formatting human-readable messages for the LLM.
Each is returned as `ServiceCallResult(success=False, error=...)`, which
`resume()` turns into `Done(CallToolResult(is_error=True))`.

## ~~Q007: Testing the HA Component~~ --- RESOLVED

Moved to [Decisions](decisions.md) as D013.

## ~~Q008: Tests in Wheel~~ --- RESOLVED

Moved to [Decisions](decisions.md) as D014.

## Q009: Schema Fidelity vs. LLM Clarity

**Question:** Should MCP tool schemas transparently mirror HA's native service
interface, or reshape it for LLM clarity?

**Context:** Two current cases where the schema diverges from HA's raw API:

- **Target properties** (`entity_id`, `device_id`, `area_id`): HA accepts both
  single strings and arrays of strings.  The MCP schema uses array-only
  (`{"type": "array", "items": {"type": "string"}}`) for consistency and
  predictability.
- **Target/data separation:** HA's `async_call` has a separate `target` parameter,
  but the MCP schema presents a flat property list.  All arguments are passed as
  `service_data` (HA extracts target keys internally).

Both choices prioritize a clear, predictable schema for the LLM over transparent
passthrough of HA's API.  This may need revisiting if edge cases emerge where the
reshaping causes problems (e.g., services that interpret target keys differently,
or LLMs that struggle with always-array semantics for single-entity calls).

**Leaning toward:** Keep the current reshaping.  Revisit if real problems surface.
