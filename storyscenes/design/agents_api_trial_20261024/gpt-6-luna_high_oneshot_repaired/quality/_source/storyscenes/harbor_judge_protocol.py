"""Keep the story rubric; attach group membership to each mandatory rating.

Large sets made a separate list-of-ID partition easy to omit entries from. This
format has one assignment per rated story and converts to the historical report
shape only after validating the complete ID and group sets.
"""
from copy import deepcopy


def request_body(quality, item):
    body = deepcopy(quality.request_body(item, cache_prompts=True))
    count = len(item["stories"])
    body["max_output_tokens"] = max(4000, 180 * count + 1200)
    body["input"][0]["content"] += (
        "\nOutput-format detail: put each story's group_id beside its rating. "
        "plot_groups lists each used group_id and its summary exactly once. "
        "Use the same group_id for stories with the same causal plot. This is "
        "the membership partition requested above, not an additional score.")
    fmt = body["text"]["format"]
    fmt["name"] = "harbor_story_set_v2"
    schema = fmt["schema"]
    group = dict(type="integer", enum=list(range(count)))
    row = schema["properties"]["stories"]["items"]
    row["properties"]["group_id"] = group
    row["required"].append("group_id")
    schema["properties"]["plot_groups"]["items"] = quality.object_schema(dict(
        group_id=group, summary=dict(type="string")))
    return body


def validate(quality, value, item):
    if not isinstance(value, dict) or set(value) != {"stories", "diversity", "diversity_evidence", "plot_groups"}:
        raise ValueError("Unexpected set fields")
    expected = {s["id"] for s in item["stories"]}
    groups = {}
    for group in value["plot_groups"]:
        if not isinstance(group, dict) or set(group) != {"group_id", "summary"}:
            raise ValueError("Unexpected group fields")
        key = group["group_id"]
        if type(key) is not int or not 0 <= key < len(expected) or key in groups:
            raise ValueError("Invalid or repeated plot group")
        groups[key] = dict(story_ids=[], summary=group["summary"])
    stories = []
    for row in value["stories"]:
        if not isinstance(row, dict) or set(row) != {"id", "rating", "note", "group_id"}:
            raise ValueError("Unexpected story fields")
        key = row["group_id"]
        if type(key) is not int or key not in groups:
            raise ValueError("Story names an undefined plot group")
        groups[key]["story_ids"].append(row["id"])
        stories.append({k: row[k] for k in ("id", "rating", "note")})
    return quality.validate(dict(stories=stories, diversity=value["diversity"],
        diversity_evidence=value["diversity_evidence"], plot_groups=list(groups.values())), item)
