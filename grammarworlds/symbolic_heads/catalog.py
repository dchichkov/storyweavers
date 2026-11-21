"""Render editable JSON head specifications as a readable example catalog."""

from .runtime import load_library


def render(library=None):
    library = library or load_library()
    lines = ["# Symbolic head library: descriptions and examples", "",
             "Generated from the editable [JSON specifications](data/). "
             "All weights and examples are authored illustrations, not trained statistics.", "",
             "**64 heads: 15 executable lookup heads and 49 explicit program-required contracts. "
             "Each has ten examples (640 total).** Deferred examples describe desired behavior; "
             "they are not claims that the algorithm runs. See [runtime and table semantics](README.md).", ""]
    for head_id in library.ids:
        s = library.describe(head_id)
        lines.extend([f'## {head_id} — {s["name"]}', "", s["description"], "",
                      f'**Status:** `{s["status"]}`. [Editable specification](data/{head_id}.json).', ""])
        if s["status"] == "program_required":
            lines.extend([f'**Raises `ProgramRequired`:** {s["required_program"]}', "",
                          "| Example | Context | Intended feature (not implemented) |",
                          "| --- | --- | --- |"])
            lines.extend(f'| {e["id"]} | {e["description"]} | {e["intended_feature"]} |' for e in s["examples"])
        else:
            lines.extend([s["input_contract"], "", s["table_semantics"], "",
                          "| Example | Description | Query → source key → transmitted feature | Favored / disfavored word |",
                          "| --- | --- | --- | --- |"])
            for e in s["examples"]:
                features = ", ".join(f'{k}:{v:g}' for k,v in e["expected_features"].items())
                key = e["sources"][0]["key"]
                lines.append(f'| {e["id"]} | {e["description"]} | `{e["query"]}` → `{key}` → `{features}` | {e["favored"]} / {e["disfavored"]} |')
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    print(render())
