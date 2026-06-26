#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/yolk_moral_value_problem_solving_reconciliation_adventure.py
===============================================================================================================

A standalone storyworld about a small adventure, a moral choice, a practical
problem, and a reconciliation around a precious yolk.

The seed image behind this world:
- A child on a little quest carries a bright yolk safely through a windy place.
- Something goes wrong, the group must solve it, and two friends make up.

This world keeps the story child-facing and concrete:
- physical meters: carried, cracked, wet, lost, fixed
- emotional memes: worry, pride, blame, shame, care, relief, trust

The prose is generated from simulated state, not from a fixed paragraph template.
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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["carried", "cracked", "wet", "lost", "fixed"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "pride", "blame", "shame", "care", "relief", "trust", "hope"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    weather: str
    hazard: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    verb: str
    complication: str
    fix: str
    repair_action: str
    keyword: str = "yolk"
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    label: str
    phrase: str
    type: str
    value: str
    fragile: bool = True


@dataclass
class Tool:
    id: str
    label: str
    covers: set[str]
    helps: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _worn(actor: Entity, world: World) -> list[Entity]:
    return [e for e in world.entities.values() if e.carried_by == actor.id]


def _is_covered(actor: Entity, region: str, world: World) -> bool:
    return any(t.id in TOOLS and region in TOOLS[t.id].covers for t in _worn(actor, world))


def _spill(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["carried"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.owner != actor.id or item.type != "yolk":
                continue
            if item.meters["cracked"] >= THRESHOLD:
                continue
            sig = ("spill", actor.id, item.id)
            if sig in world.fired:
                continue
            if "path" not in world.zone:
                continue
            world.fired.add(sig)
            item.meters["cracked"] += 1
            item.meters["wet"] += 1
            actor.memes["worry"] += 1
            out.append(f"The yolk trembled in {actor.pronoun('possessive')} hands.")
    return out


def _blame(world: World) -> list[str]:
    out = []
    a = world.get("hero")
    b = world.get("friend")
    yolk = world.get("yolk")
    if yolk.meters["cracked"] >= THRESHOLD and a.memes["worry"] >= THRESHOLD:
        sig = ("blame",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["blame"] += 1
            b.memes["shame"] += 1
            out.append("__blame__")
    return out


def _repair(world: World) -> list[str]:
    out = []
    yolk = world.get("yolk")
    if yolk.meters["cracked"] < THRESHOLD:
        return out
    if world.facts.get("repaired"):
        return out
    sig = ("repair",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    yolk.meters["fixed"] += 1
    world.facts["repaired"] = True
    out.append("The little team found a clean shell and a broad leaf.")
    return out


CAUSAL_RULES = [_spill, _blame, _repair]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__blame__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def resolve_conflict(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    yolk = world.get("yolk")
    tool = world.get("tool")

    hero.memes["care"] += 1
    friend.memes["care"] += 1
    world.say(f"{hero.id} saw the cracked yolk and took a deep breath.")
    world.say(f"{hero.pronoun().capitalize()} said, \"I should have carried it more carefully.\"")
    friend.memes["trust"] += 1
    world.say(f"{friend.id} looked down and said, \"I was too quick to grab the basket.\"")
    world.say(f"Together they used {tool.label} to cradle the yolk while they walked.")

    yolk.meters["cracked"] = 0.0
    yolk.meters["fixed"] = 1.0
    hero.memes["blame"] = 0.0
    friend.memes["shame"] = 0.0
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"In the end, the yolk stayed safe, the path was finished, and the two friends "
        f"walked on side by side."
    )


def tell(setting: Setting, quest: Quest, treasure: Treasure, name: str, friend_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type="boy", label=name))
    friend = world.add(Entity(id="friend", kind="character", type="girl", label=friend_name))
    yolk = world.add(Entity(id="yolk", type=treasure.type, label=treasure.label, phrase=treasure.phrase, owner="hero"))
    tool = world.add(Entity(id="tool", type="bowl", label="a shallow bowl", phrase="a shallow bowl"))
    world.facts.update(hero=hero, friend=friend, yolk=yolk, tool=tool, quest=quest, treasure=treasure)

    hero.meters["carried"] += 1
    hero.memes["pride"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"{name} and {friend_name} set out from {setting.place} on a little adventure."
    )
    world.say(
        f"They were carrying {treasure.phrase}, because {name} wanted to {quest.goal} and keep it golden."
    )
    world.say(
        f"The day was {setting.weather}, and the trail ahead looked narrow and windy."
    )

    world.para()
    world.zone = {"path"}
    world.say(f"When they reached the {setting.hazard}, {name} tried to {quest.verb}.")
    world.say(
        f"{friend_name} hurried to help, but {quest.complication}."
    )
    propagate(world, narrate=True)

    if yolk.meters["cracked"] >= THRESHOLD:
        world.say(
            f"{name} and {friend_name} stopped at once, because the bright yolk was no longer safe."
        )
        world.para()
        resolve_conflict(world)

    world.facts["resolved"] = True
    return world


SETTING_REGISTRY = {
    "orchard": Setting(place="the orchard path", weather="warm and windy", hazard="stone bridge", affords={"walk", "carry"}),
    "garden": Setting(place="the garden gate", weather="soft and breezy", hazard="narrow stepping stones", affords={"walk", "carry"}),
    "harbor": Setting(place="the harbor walk", weather="bright and gusty", hazard="wooden boardwalk", affords={"walk", "carry"}),
}

QUEST_REGISTRY = {
    "deliver": Quest(
        id="deliver",
        goal="deliver the yolk to the picnic table",
        verb="cross the bridge with the basket",
        complication="the wind knocked the basket sideways",
        fix="use a bowl and a leaf",
        repair_action="gather the yolk gently",
        tags={"yolk", "adventure", "problem_solving", "moral_value", "reconciliation"},
    ),
    "rescue": Quest(
        id="rescue",
        goal="save the yolk for the hungry chick",
        verb="step around the stones",
        complication="a loose plank tipped the basket",
        fix="use a bowl and a leaf",
        repair_action="gather the yolk gently",
        tags={"yolk", "adventure", "problem_solving", "moral_value", "reconciliation"},
    ),
}

TREASURES = {
    "yolk": Treasure(label="yolk", phrase="a bright golden yolk", type="yolk", value="precious", fragile=True),
}

TOOLS = {
    "bowl": Tool(id="bowl", label="a shallow bowl", covers={"hands"}, helps={"carrying"}, prep="hold it level", tail="kept the yolk steady"),
    "leaf": Tool(id="leaf", label="a broad leaf", covers={"top"}, helps={"cushioning"}, prep="make a soft nest", tail="turned it into a tiny bed"),
}


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    friend_name: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mina", "Tia", "Luna", "Ivy", "Nora", "Zia"]
BOY_NAMES = ["Arlo", "Finn", "Noah", "Eli", "Jude", "Otto"]


def generation_prompts(world: World) -> list[str]:
    q = world.facts["quest"]
    t = world.facts["treasure"]
    return [
        f"Write a short adventure story for a young child about {t.phrase} and a good choice.",
        f"Tell a gentle story where friends try to {q.goal}, run into a problem, and then make up.",
        f"Write a story with the word \"yolk\" that shows honesty, problem solving, and reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    yolk = world.facts["yolk"]
    q = world.facts["quest"]
    setting = world.setting

    return [
        QAItem(
            question=f"Who went on the adventure in {setting.place}?",
            answer=f"{hero.label} and {friend.label} went on the adventure together.",
        ),
        QAItem(
            question="What precious thing were they carrying?",
            answer=f"They were carrying {yolk.phrase}.",
        ),
        QAItem(
            question="What problem happened on the path?",
            answer=f"The wind and the narrow crossing made the basket tip, and the yolk cracked.",
        ),
        QAItem(
            question="How did they fix the problem?",
            answer="They found a shallow bowl and a broad leaf, then worked together to hold the yolk safely.",
        ),
        QAItem(
            question="How did the friends end the story?",
            answer=f"They apologized, trusted each other again, and walked on side by side after solving the problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a yolk?",
            answer="A yolk is the yellow part of an egg.",
        ),
        QAItem(
            question="Why do people use a bowl to carry something fragile?",
            answer="A bowl can help hold something still so it is less likely to spill or break.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a disagreement.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="orchard", quest="deliver", name="Arlo", friend_name="Mina"),
    StoryParams(place="garden", quest="rescue", name="Ivy", friend_name="Finn"),
]


def explain_invalid(args) -> Optional[str]:
    if args.place and args.place not in SETTING_REGISTRY:
        return "(No story: unknown place.)"
    if args.quest and args.quest not in QUEST_REGISTRY:
        return "(No story: unknown quest.)"
    return None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    bad = explain_invalid(args)
    if bad:
        raise StoryError(bad)
    place = args.place or rng.choice(list(SETTING_REGISTRY))
    quest = args.quest or rng.choice(list(QUEST_REGISTRY))
    name = args.name or rng.choice(BOY_NAMES)
    friend_name = args.friend_name or rng.choice(GIRL_NAMES)
    return StoryParams(place=place, quest=quest, name=name, friend_name=friend_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING_REGISTRY[params.place], QUEST_REGISTRY[params.quest], TREASURES["yolk"], params.name, params.friend_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTING_REGISTRY.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid, q in QUEST_REGISTRY.items():
        lines.append(asp.fact("quest", qid))
        for t in sorted(q.tags):
            lines.append(asp.fact("tagged", qid, t))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("value", tid, t.value))
    for tool in TOOLS.values():
        lines.append(asp.fact("tool", tool.id))
        for c in sorted(tool.covers):
            lines.append(asp.fact("covers", tool.id, c))
    return "\n".join(lines)


ASP_RULES = r"""
needs_fix(Q) :- tagged(Q, problem_solving).
needs_peace(Q) :- tagged(Q, reconciliation).
meaningful(Q) :- tagged(Q, moral_value), needs_fix(Q), needs_peace(Q).
valid_story(P, Q) :- setting(P), quest(Q), meaningful(Q), affords(P, carry).
#show valid_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    # Python gate: all curated quests are meaningful on all settings.
    py = {(p, q) for p in SETTING_REGISTRY for q in QUEST_REGISTRY if "moral_value" in QUEST_REGISTRY[q].tags and "problem_solving" in QUEST_REGISTRY[q].tags and "reconciliation" in QUEST_REGISTRY[q].tags and "carry" in SETTING_REGISTRY[p].affords}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print(" only in clingo:", sorted(cl - py))
    print(" only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small adventure storyworld about a yolk, a moral choice, and reconciliation.")
    ap.add_argument("--place", choices=SETTING_REGISTRY)
    ap.add_argument("--quest", choices=QUEST_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid story combos:")
        for row in stories:
            print(" ", row)
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} and {p.friend_name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
