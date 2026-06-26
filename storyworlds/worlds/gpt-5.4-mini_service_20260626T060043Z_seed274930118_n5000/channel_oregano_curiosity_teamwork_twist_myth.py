#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/channel_oregano_curiosity_teamwork_twist_myth.py
==========================================================================================================================

A tiny myth-style story world about a curious child, a narrow channel, and a
sprig of oregano that turns into an unexpected twist. The premise is simple:
someone wants to cross or tend the channel, but the only way through is to work
together, listen closely, and follow the scent of oregano to the right place.

The world is built from a small simulated state:
- physical meters: path openness, water depth, herb freshness, boat readiness
- emotional memes: curiosity, teamwork, worry, trust, wonder

The story is intentionally classical in shape:
setup -> curiosity -> teamwork -> twist -> resolution
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the river channel"
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    helper: str
    herb: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _clamp(v: float) -> float:
    return max(0.0, min(3.0, v))


def _apply_curiosity(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child"].id)
    if child.memes.get("curiosity", 0) < THRESHOLD:
        return out
    sig = ("curious", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["wonder"] = child.memes.get("wonder", 0) + 1
    world.facts["discovered_scent"] = True
    out.append(
        f"{child.id} followed the oregano scent and wondered what secret the channel was keeping."
    )
    return out


def _apply_teamwork(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child"].id)
    helper = world.get(world.facts["helper"].id)
    if child.memes.get("worry", 0) < THRESHOLD:
        return out
    sig = ("teamwork", child.id, helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["trust"] = child.memes.get("trust", 0) + 1
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0) + 1
    world.facts["built_bridge"] = True
    out.append(
        f"{helper.id} and {child.id} worked side by side, tying reeds and stones into a small bridge."
    )
    return out


def _apply_twist(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child"].id)
    herb = world.get(world.facts["herb"].id)
    if not world.facts.get("built_bridge"):
        return out
    sig = ("twist", herb.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    herb.meters["freshness"] = _clamp(herb.meters.get("freshness", 0) + 1)
    world.facts["twist_revealed"] = True
    out.append(
        f"Then came the twist: the oregano was not a mere garnish, but a guiding herb once planted by the river spirits."
    )
    child.memes["wonder"] = child.memes.get("wonder", 0) + 1
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_apply_curiosity, _apply_teamwork, _apply_twist):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for wid, w in HEROES.items():
        lines.append(asp.fact("child", wid))
        lines.append(asp.fact("type_of", wid, w.type))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
    for herb_id, herb in HERBS.items():
        lines.append(asp.fact("herb", herb_id))
    return "\n".join(lines)


ASP_RULES = r"""
curious(X) :- child(X).
teamwork(X,Y) :- child(X), helper(Y).
twist(H) :- herb(H).
valid_story(P,H) :- affords(P, channel), herb(H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


SETTINGS = {
    "river_channel": Setting(place="the river channel", affords={"crossing", "gardening"}),
    "stone_channel": Setting(place="the stone channel", affords={"crossing"}),
}

HEROES = {
    "Ari": Entity(id="Ari", kind="character", type="boy"),
    "Mira": Entity(id="Mira", kind="character", type="girl"),
}

HELPERS = {
    "Uncle": Entity(id="Uncle", kind="character", type="man"),
    "Aunt": Entity(id="Aunt", kind="character", type="woman"),
}

HERBS = {
    "oregano": Entity(id="oregano", kind="thing", type="herb", label="oregano", phrase="a green sprig of oregano"),
}

PLACES = ["river_channel", "stone_channel"]
NAMES = ["Ari", "Mira"]
GENDERS = ["boy", "girl"]
HELPER_NAMES = ["Uncle", "Aunt"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A myth-style story world of channel, oregano, curiosity, teamwork, and twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--herb", choices=list(HERBS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(PLACES)
    name = args.name or rng.choice(NAMES)
    gender = args.gender or ("boy" if name == "Ari" else "girl")
    helper = args.helper or rng.choice(HELPER_NAMES)
    herb = args.herb or "oregano"
    return StoryParams(place=place, name=name, gender=gender, helper=helper, herb=herb)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id=params.helper, kind="character", type="man" if params.helper == "Uncle" else "woman"))
    herb = world.add(Entity(id=params.herb, kind="thing", type="herb", label="oregano", phrase="a green sprig of oregano"))

    child.memes["curiosity"] = 1
    child.memes["worry"] = 1
    world.facts.update(child=child, helper=helper, herb=herb)

    world.say(
        f"Long ago, beside {setting.place}, {child.id} was a curious child who loved to ask why the water moved in a narrow line."
    )
    world.say(
        f"One morning, {child.id} found {herb.phrase} on the wind, and the scent seemed to come from the channel itself."
    )
    world.para()
    world.say(
        f"{child.id} leaned close and peered at the water, but the crossing looked uncertain and the stones shone slick."
    )
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"Then {helper.id} arrived with patient hands and said they would solve it together."
    )
    propagate(world, narrate=True)
    world.para()
    if world.facts.get("twist_revealed"):
        world.say(
            f"In the end, the channel opened like a blessing, and {child.id} crossed with {helper.id}, carrying the oregano like a small green crown."
        )
    else:
        world.say(
            f"In the end, {child.id} crossed with {helper.id}, and the oregano stayed bright and fresh in the warm air."
        )

    story = world.render()
    prompts = [
        "Write a short myth about a curious child, a narrow channel, and a guiding herb called oregano.",
        "Tell a gentle story where teamwork helps a child cross a channel and a twist reveals the meaning of oregano.",
        "Compose a child-friendly myth about curiosity, teamwork, and an unexpected secret in the water.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {child.id} look closely at the channel?",
            answer=f"{child.id} was curious and wanted to understand the strange water and the scent of oregano."
        ),
        QAItem(
            question=f"How did {child.id} and {helper.id} solve the problem?",
            answer=f"They worked together and built a small bridge from reeds and stones so the crossing would be safe."
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The oregano was not just a plant on the wind; it was a guiding herb once planted by the river spirits."
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a channel?",
            answer="A channel is a narrow path where water moves from one place to another."
        ),
        QAItem(
            question="What is oregano?",
            answer="Oregano is a fragrant herb used in cooking, and it has small green leaves."
        ),
        QAItem(
            question="Why is teamwork helpful?",
            answer="Teamwork is helpful because two or more helpers can do a hard job together more safely and quickly."
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts={sorted(world.facts)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {("river_channel", "oregano"), ("stone_channel", "oregano")}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible story combos:\n")
        for place, herb in combos:
            print(f"  {place:12} {herb}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [
            generate(StoryParams(place="river_channel", name="Ari", gender="boy", helper="Uncle", herb="oregano")),
            generate(StoryParams(place="stone_channel", name="Mira", gender="girl", helper="Aunt", herb="oregano")),
        ]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} at {p.place} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
