#!/usr/bin/env python3
"""
Story world: a snazzy manatee at a bus stop, with suspense and reconciliation,
told in a gentle rhyming story style.

A short source-tale idea:
- A young manatee waits at a bus stop in a snazzy outfit.
- A small mix-up creates suspense: the bus is late and the snazzy hat goes missing.
- The manatee and a friend search together, reconcile, and the bus arrives in time.
- The ending proves the change: the hat is found, the worry fades, and the pair
  ride away smiling.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- state-driven prose
- QA generation
- inline ASP twin with parity verification
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


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    wearer: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"manatee"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"child", "friend"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bus stop"
    affords: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    kind: str
    wear_zone: str
    flair: str
    risk: str
    protects: Optional[str] = None


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    suspense_line: str
    mess: str
    zone: str
    weather: str
    rhyme: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bus_stop": Setting(place="the bus stop", affords={"wait", "search", "ride"}),
}

ACTIONS = {
    "wait": Action(
        id="wait",
        verb="wait for the bus",
        gerund="waiting for the bus",
        suspense_line="the bus was late, and the minute hand seemed to skate",
        mess="nervous",
        zone="heart",
        weather="windy",
        rhyme="gate",
    ),
    "search": Action(
        id="search",
        verb="look for the missing hat",
        gerund="looking for the missing hat",
        suspense_line="the hat was not on the bench, which made the worry stretch",
        mess="nervous",
        zone="heart",
        weather="windy",
        rhyme="patch",
    ),
}

ITEMS = {
    "snazzy_hat": Thing(
        id="snazzy_hat",
        label="snazzy hat",
        phrase="a snazzy hat with a shiny blue band",
        kind="hat",
        wear_zone="head",
        flair="snazzy",
        risk="blowy",
        protects=None,
    ),
    "snazzy_scarf": Thing(
        id="snazzy_scarf",
        label="snazzy scarf",
        phrase="a snazzy scarf with silver stripes",
        kind="scarf",
        wear_zone="neck",
        flair="snazzy",
        risk="blowy",
        protects=None,
    ),
    "shell_bag": Thing(
        id="shell_bag",
        label="shell bag",
        phrase="a shell bag with a neat clasp",
        kind="bag",
        wear_zone="side",
        flair="snazzy",
        risk="safe",
        protects="hat",
    ),
}

NAMES = ["Milo", "Nina", "Pip", "Luna", "Drew", "Ruby"]


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    friend: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def item_is_snazzy(item: Thing) -> bool:
    return item.flair == "snazzy"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for item_id, item in ITEMS.items():
            if place == "bus_stop" and item_is_snazzy(item):
                combos.append((place, item_id))
    return combos


def explain_rejection(item: Thing) -> str:
    return (
        f"(No story: the {item.label} is not the right sort of snazzy thing for a bus stop "
        f"reconciliation tale.)"
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def rhyme_pair(a: str, b: str) -> str:
    return f"{a}, {b}."


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    hero = world.add(Entity(id=params.name, kind="character", type="manatee", label=params.name))
    friend = world.add(Entity(id=params.friend, kind="character", type="child", label=params.friend))
    item = ITEMS[params.item]
    prized = world.add(Entity(
        id=item.id,
        kind="thing",
        type=item.kind,
        label=item.label,
        phrase=item.phrase,
        owner=hero.id,
        wearer=hero.id,
    ))

    hero.memes["anticipation"] = 1
    hero.memes["worry"] = 0
    hero.memes["hope"] = 1
    friend.memes["guilt"] = 0
    friend.memes["kindness"] = 1

    # Act 1
    world.say(
        f"At the bus stop by the bay, {hero.id} came to wait and sway; "
        f"{hero.pronoun('subject').capitalize()} wore {prized.phrase}, bright and neat, "
        f"and tapped a tiny, tidy beat."
    )
    world.say(
        f"{hero.id} loved the look, so crisp and keen; "
        f"the {item.label} sparkled, snazzy, clean."
    )

    # Act 2: suspense
    world.para()
    hero.memes["worry"] += 1
    world.say(
        f"Then came suspense beneath the sky: {ACTIONS['wait'].suspense_line}, "
        f"and the bus did not roll by."
    )
    world.say(
        f"{friend.id} rushed up quick, then gave a gasp: the {item.label} slipped away in a splash of brash."
    )
    if prized.wearer == hero.id:
        prized.wearer = None
    hero.memes["fear"] = 1
    hero.memes["loss"] = 1
    world.fired.add(("missing", prized.id))
    world.say(
        f"{hero.id} felt the hush, the pause, the ache; {hero.pronoun('possessive')} heart went thump, a shaky shake."
    )

    # Act 3: reconciliation
    world.para()
    friend.memes["guilt"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"{friend.id} said, 'I'm sorry for the snatch. Let's search together, round each patch and latch.'"
    )
    world.say(
        f"They looked by the bench, the sign, the curb; they peered through puddles, still and perturbed."
    )
    world.say(
        f"At last, behind a post, so sly, the {item.label} sat with a single sigh."
    )
    world.say(
        f"{hero.id} forgave {friend.id}, and friends were new; the worry melted, soft and true."
    )
    world.say(
        f"Then the bus came groaning, blue and bright; they climbed aboard in happy light."
    )
    world.say(
        f"{hero.id} wore the {item.label} once more, and smiled at {friend.id} by the door."
    )

    hero.memes["worry"] = 0
    hero.memes["joy"] = 2
    friend.memes["guilt"] = 0
    friend.memes["relief"] = 1

    world.facts.update(
        hero=hero,
        friend=friend,
        item=prized,
        item_cfg=item,
        place=params.place,
        action=ACTIONS["wait"],
        reconciled=True,
        suspense=True,
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(bus_stop).
affords(bus_stop, wait).
affords(bus_stop, search).
affords(bus_stop, ride).

hero_type(manatee).
hero_type(child).

snazzy_item(snazz_hat) :- item(snazz_hat), flair(snazz_hat, snazzy).
snazzy_item(snazz_scarf) :- item(snazz_scarf), flair(snazz_scarf, snazzy).
snazzy_item(shell_bag) :- item(shell_bag), flair(shell_bag, snazzy).

compatible_story(P, I) :- place(P), affords(P, wait), item(I), snazzy_item(I).
reconciled_story(P, I) :- compatible_story(P, I).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("flair", iid, item.flair))
        lines.append(asp.fact("wear_zone", iid, item.wear_zone))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible_story/2."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# QA and presentation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story about a manatee named {f["hero"].id} waiting at {f["place"]} in a snazzy way.',
        f"Tell a gentle suspense story where {f['hero'].id} loses {f['item'].label} at {f['place']} and then makes up with {f['friend'].id}.",
        f'Write a simple child-friendly rhyming story that includes the word "snazzy" and ends with reconciliation at {f["place"]}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    return [
        QAItem(
            question=f"Who waited at the bus stop in the story?",
            answer=f"{hero.id}, the manatee, waited at the bus stop wearing {item.label}.",
        ),
        QAItem(
            question=f"What created suspense in the middle of the story?",
            answer=f"The suspense came when the {item.label} went missing and the bus was late.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} fix the problem?",
            answer=f"They searched together, found the {item.label}, and made up before the bus arrived.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bus stop?",
            answer="A bus stop is a place where people wait for a bus to come and pick them up.",
        ),
        QAItem(
            question="What does snazzy mean?",
            answer="Snazzy means bright, stylish, and a little fancy.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace again after a disagreement or a mistake.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of waiting and wondering what will happen next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{ent.id}: {ent.type} {' '.join(parts)}")
    lines.extend(world.trace)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters, parsing, generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="bus_stop", item="snazzy_hat", name="Milo", friend="Nina"),
    StoryParams(place="bus_stop", item="snazzy_scarf", name="Luna", friend="Pip"),
    StoryParams(place="bus_stop", item="shell_bag", name="Ruby", friend="Drew"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world: a snazzy manatee at a bus stop.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != name])
    return StoryParams(place=place, item=item, name=name, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item) combos:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} and {p.friend} at {p.place} with {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
