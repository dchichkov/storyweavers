"""Synthetic apply_patch grammar, validation, and deterministic composition."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import json
import random

from .quality import record_from_bundle, validate_bundle


ALLOWED_FILES = {"outline.json", "story.md", "conversations.json"}
BROAD_TIERS = {"significant", "major"}


@dataclass(frozen=True)
class Hunk:
    header: str
    lines: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class Update:
    path: str
    hunks: tuple[Hunk, ...]


@dataclass(frozen=True)
class PatchSlot:
    id: str
    tier: str
    focus: str
    section: str
    conversation: str

    def instruction(self) -> str:
        breadth = {
            "trivial": "Make a small substitution or detail change; keep the plot unchanged.",
            "moderate": "Rewrite or extend one local beat without changing the central outcome.",
            "significant": "Change a consequential beat or ending and update the outline.",
            "major": "Change a kernel, character, setting, or plot mechanism and update the outline.",
        }[self.tier]
        return (
            f"PATCH SLOT {self.id}\nTier: {self.tier}\nFocus: {self.focus}\n"
            f"Primary story section: {self.section}\nPrimary conversation item: {self.conversation}\n"
            f"{breadth} Update story.md and conversations.json together. "
            "Preserve all three required words and any required dialogue. "
            "Return exactly one apply_patch tool call."
        )


FOCI = {
    "trivial": (
        "rename a character consistently", "replace a prop with a similar prop",
        "vary a sensory detail", "vary a harmless action verb", "change a small visual detail",
        "adjust one line of dialogue", "change a minor object name", "vary weather flavor",
        "vary a reaction", "vary the final image wording",
    ),
    "moderate": (
        "add a short dialogue exchange", "remove a redundant exchange", "strengthen a discovery",
        "add a failed attempt", "change who offers help", "make a clue clearer",
        "deepen a relationship beat", "add a comic complication", "tighten the opening problem",
        "make the resolution more active",
    ),
    "significant": (
        "replace the ending consequence", "add a consequential story beat", "remove a weak beat",
        "reverse a mistaken belief", "change the successful solution", "change the lesson image",
        "turn help into reconciliation", "change who solves the problem", "introduce a meaningful cost",
        "alter the central discovery",
    ),
    "major": (
        "add a compatible kernel", "replace the structural kernel", "add a new character",
        "remove a character and redistribute actions", "move the story to a different setting",
        "change the genre while preserving causality", "replace the central situation",
        "make the antagonist an environmental obstacle", "change the main relationship",
        "rebuild the final act around another kernel",
    ),
}
SECTIONS = ("opening", "setup", "inciting", "attempt", "turn", "ending")
TIER_COUNTS = (("trivial", 25), ("moderate", 30), ("significant", 30), ("major", 15))


def patch_slots() -> list[PatchSlot]:
    slots, number = [], 0
    for tier, count in TIER_COUNTS:
        for index in range(count):
            slots.append(PatchSlot(
                id=f"p{number:03d}",
                tier=tier,
                focus=FOCI[tier][index % len(FOCI[tier])],
                section=SECTIONS[index % len(SECTIONS)],
                conversation=f"q{index % 6 + 1:02d}",
            ))
            number += 1
    return slots


def parse_patch(text: str) -> tuple[Update, ...]:
    lines = text.strip().splitlines()
    if len(lines) < 5 or lines[0] != "*** Begin Patch" or lines[-1] != "*** End Patch":
        raise ValueError("patch needs exact Begin Patch and End Patch markers")
    updates, index = [], 1
    while index < len(lines) - 1:
        if not lines[index].startswith("*** Update File: "):
            raise ValueError(f"expected Update File header, got: {lines[index][:80]}")
        path = lines[index].removeprefix("*** Update File: ").strip()
        if path not in ALLOWED_FILES:
            raise ValueError(f"patch path is not allowed: {path}")
        index += 1
        hunks = []
        while index < len(lines) - 1 and not lines[index].startswith("*** Update File: "):
            if not lines[index].startswith("@@"):
                raise ValueError(f"expected hunk header, got: {lines[index][:80]}")
            header, body = lines[index][2:].strip(), []
            index += 1
            while index < len(lines) - 1 and not lines[index].startswith(("@@", "*** Update File: ")):
                line = lines[index]
                if not line or line[0] not in " +-":
                    raise ValueError("every hunk line must begin with space, - or +")
                body.append((line[0], line[1:]))
                index += 1
            if not body or not any(kind in "+-" for kind, _ in body):
                raise ValueError("every hunk must contain a change")
            if not any(kind in " -" for kind, _ in body):
                raise ValueError("addition-only hunks need context")
            hunks.append(Hunk(header, tuple(body)))
        if not hunks:
            raise ValueError(f"update has no hunks: {path}")
        updates.append(Update(path, tuple(hunks)))
    paths = [update.path for update in updates]
    if len(paths) != len(set(paths)):
        raise ValueError("each file may have only one Update File section")
    return tuple(updates)


def _positions(lines: list[str], needle: list[str]) -> list[int]:
    return [index for index in range(len(lines) - len(needle) + 1)
            if lines[index:index + len(needle)] == needle]


def apply_patch(bundle: dict[str, str], text: str) -> dict[str, str]:
    updated = dict(bundle)
    for update in parse_patch(text):
        if update.path not in updated:
            raise ValueError(f"bundle does not contain {update.path}")
        lines = updated[update.path].splitlines()
        for hunk in update.hunks:
            old = [line for kind, line in hunk.lines if kind in " -"]
            new = [line for kind, line in hunk.lines if kind in " +"]
            positions = _positions(lines, old)
            if len(positions) != 1:
                raise ValueError(f"hunk context must match exactly once in {update.path}")
            start = positions[0]
            lines[start:start + len(old)] = new
        updated[update.path] = "\n".join(lines) + "\n"
    return updated


def bundle_digest(bundle: dict[str, str]) -> str:
    return hashlib.sha256("".join(f"{key}\0{bundle[key]}\0" for key in sorted(bundle)).encode()).hexdigest()


def validate_patch(base: dict[str, str], text: str, slot: PatchSlot, seed: dict,
                   seen: set[str] | None = None) -> tuple[dict[str, str], str]:
    updates = parse_patch(text)
    paths = {update.path for update in updates}
    required = {"story.md", "conversations.json"} | ({"outline.json"} if slot.tier in BROAD_TIERS else set())
    if not required <= paths:
        raise ValueError("patch does not update all files required by its tier")
    result = apply_patch(base, text)
    if result["story.md"] == base["story.md"] or result["conversations.json"] == base["conversations.json"]:
        raise ValueError("patch must change story and conversations")
    if slot.tier in BROAD_TIERS and result["outline.json"] == base["outline.json"]:
        raise ValueError("significant and major patches must change the outline")
    validate_bundle(result, seed)
    digest = bundle_digest(result)
    if seen is not None and digest in seen:
        raise ValueError("patch produces a duplicate standalone result")
    return result, digest


def conflict_graph(base: dict[str, str], patches: list[dict]) -> dict[str, list[str]]:
    conflicts = {row["id"]: set() for row in patches}
    for left, right in itertools.combinations(patches, 2):
        same_target = left["section"] == right["section"] or left["conversation"] == right["conversation"]
        broad_pair = left["tier"] in BROAD_TIERS and right["tier"] in BROAD_TIERS
        try:
            current = apply_patch(base, left["patch"])
            apply_patch(current, right["patch"])
        except ValueError:
            same_target = True
        if same_target or broad_pair:
            conflicts[left["id"]].add(right["id"])
            conflicts[right["id"]].add(left["id"])
    return {key: sorted(value) for key, value in conflicts.items()}


def compose_variants(base: dict[str, str], patches: list[dict], seed: dict, *,
                     count=100) -> tuple[list[dict], dict[str, list[str]]]:
    conflicts = conflict_graph(base, patches)
    rng = random.Random(seed["seed"] ^ 0x5A17C0DE)
    records, story_hashes, patch_sets = [], set(), set()
    attempts = 0
    while len(records) < count and attempts < count * 2000:
        attempts += 1
        if len(patches) < 3:
            raise ValueError("at least three patches are required for composition")
        chosen = rng.sample(patches, rng.randint(3, min(5, len(patches))))
        ids = tuple(sorted(row["id"] for row in chosen))
        if ids in patch_sets or sum(row["tier"] in BROAD_TIERS for row in chosen) > 1:
            continue
        if any(right["id"] in conflicts[left["id"]] for left, right in itertools.combinations(chosen, 2)):
            continue
        current = dict(base)
        try:
            for row in sorted(chosen, key=lambda item: item["id"]):
                current = apply_patch(current, row["patch"])
            validate_bundle(current, seed)
        except ValueError:
            continue
        story_hash = hashlib.sha256(current["story.md"].encode()).hexdigest()
        if story_hash in story_hashes:
            continue
        records.append(record_from_bundle(current, patch_ids=list(ids), seed=len(records)))
        story_hashes.add(story_hash)
        patch_sets.add(ids)
    if len(records) != count:
        raise ValueError(f"only composed {len(records)} valid unique variants after {attempts} attempts")
    return records, conflicts
