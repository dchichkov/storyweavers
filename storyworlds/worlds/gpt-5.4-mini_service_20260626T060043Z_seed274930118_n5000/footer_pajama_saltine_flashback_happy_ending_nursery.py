#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/footer_pajama_saltine_flashback_happy_ending_nursery.py
================================================================================================

A tiny nursery-rhyme storyworld about a child in pajamas, a saltine snack, and
a remembered bedtime mishap with a book footer. The story is built from a small
simulated world with physical meters and emotional memes.

Premise:
- A little child loves bedtime, a cozy pajama, and a plain saltine.
- A worn storybook has a footer on the last page.
- Crumbs from the saltine can fall onto the book or pajama.

Tension:
- The child wants to munch the saltine before sleep.
- A parent remembers, via a flashback, that crumbs once hid in the footer and
  made the book sticky and sad.

Turn:
- The parent offers a napkin and a careful way to eat.

Resolution:
- The saltine stays neat, the pajama stays clean, and the footer is left tidy.
- The ending is gentle and happy, like a small nursery rhyme with a warm moon.

The world includes:
- footer: the bottom of the storybook page, which can catch crumbs.
- pajama: the child's bedtime clothes.
- saltine: the plain cracker snack.

Features:
- Flashback
- Happy Ending
- Nursery rhyme cadence
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CRUMBS = {"crumby"}
REGIONS = {"hands", "mouth", "torso", "page"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["crumby", "dirty", "neat", "snug"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "memory", "care"]:
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
    place: str = "the bedside"
    affords: set[str] = field(default_factory=lambda: {"snack", "read"})


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    mess: str
    zone: set[str]
    keyword: str = "saltine"


@dataclass
class Cover:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


def _r_crumbs(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["crumby"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in {"torso", "hands"}:
                continue
            sig = ("crumbs", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["crumby"] += 1
            item.meters["dirty"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got crumby.")
    return out


def _r_cleanliness(world: World) -> list[str]:
    out = []
    for item in world.entities.values():
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["care"] += 1
        out.append(f"That would mean extra tidying for {carer.label}.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_crumbs, _r_cleanliness):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting()

SNACKS = {
    "saltine": Snack(
        id="saltine",
        label="saltine",
        phrase="a plain saltine",
        mess="crumby",
        zone={"hands", "mouth"},
        keyword="saltine",
    )
}

COVERS = [
    Cover(
        id="napkin",
        label="a napkin",
        covers={"hands", "mouth"},
        guards={"crumby"},
        prep="place a napkin under the snack",
        tail="set the napkin beside the plate",
    ),
    Cover(
        id="tray",
        label="a little tray",
        covers={"hands"},
        guards={"crumby"},
        prep="set the saltine on a little tray",
        tail="slid the tray close by",
    ),
]

GIRL_NAMES = ["Lily", "Mia", "Nora", "Rose", "Tia", "June"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Eli", "Theo"]


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    snack: str = "saltine"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [("bedside", "saltine")]


def make_world(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    snack = world.add(Entity(
        id="snack",
        type="snack",
        label="saltine",
        phrase="a plain saltine",
        owner=child.id,
        caretaker=parent.id,
        region="hands",
        plural=False,
    ))
    footer = world.add(Entity(
        id="footer",
        type="page",
        label="footer",
        phrase="the footer on the last page",
        caretaker=parent.id,
        region="page",
    ))
    napkin = world.add(Entity(
        id="napkin",
        type="cloth",
        label="napkin",
        phrase="a little napkin",
        owner=child.id,
        caretaker=parent.id,
        protective=True,
        covers={"hands", "mouth"},
    ))

    child.memes["joy"] += 1
    child.memes["care"] += 1
    world.say(f"{child.id} was a little {params.gender} in a snug pajama, soft and neat.")
    world.say(f"{child.id} loved {snack.phrase} at bedtime, and loved the quiet moonlight too.")
    world.say(f"{parent.label} kept the storybook near, with its footer resting at the very end.")

    world.para()
    world.say(f"One night, just before sleep, {child.id} reached for the saltine with a tiny grin.")
    world.say(f"{child.id} wanted to nibble and crunch, while the pajama sleeves danced about.")
    world.say(f"Then came a flashback: one crumbly day, crumbs had slipped into the footer and made the page look sad.")
    parent.memes["memory"] += 1
    parent.memes["worry"] += 1
    world.say(f"So {parent.label} said, \"Oh dear, let us mind the crumbs, and keep the footer clean.\"")

    world.para()
    world.say(f"{child.id} paused, then nodded with a sleepy little smile.")
    world.say(f"{parent.label} laid out the napkin and said, \"Place the saltine there, and munch away with care.\"")
    napkin.worn_by = None
    snack.worn_by = child.id
    snack.meters["crumby"] += 0.0
    propagate(world)
    child.memes["joy"] += 1
    parent.memes["care"] += 1
    world.say(f"{child.id} ate neatly, and the pajama stayed tidy, and the footer stayed bright and free.")

    world.facts.update(child=child, parent=parent, snack=snack, footer=footer, napkin=napkin)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f'Write a nursery-rhyme style bedtime story about {child.id}, a pajama, and a saltine.',
        f'Write a gentle flashback story where crumbs once troubled a footer, but the ending turns happy.',
        f'Tell a short cozy story for little listeners that includes the words "footer", "pajama", and "saltine".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    return [
        QAItem(
            question=f"Who was the bedtime story about?",
            answer=f"It was about {child.id}, a little child in a pajama, and {parent.label}.",
        ),
        QAItem(
            question="Why did the parent remember the footer?",
            answer="The parent had a flashback to an older night when crumbs had slipped into the footer and made the page messy.",
        ),
        QAItem(
            question="How did they keep the saltine from making a mess?",
            answer="They used a napkin and ate carefully, so the pajama stayed clean and the footer stayed tidy.",
        ),
        QAItem(
            question="What was the ending like?",
            answer="The ending was happy and quiet, with a clean pajama, a neat saltine snack, and a bright footer at the bottom of the page.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a saltine?",
            answer="A saltine is a plain, crisp cracker that can be eaten as a simple snack.",
        ),
        QAItem(
            question="What is a pajama for?",
            answer="A pajama is soft bedtime clothing that helps a child feel cozy and ready for sleep.",
        ),
        QAItem(
            question="What is a footer on a page?",
            answer="A footer is the bottom part of a page, where small bits of text or decoration can rest.",
        ),
    ]


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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(out)


ASP_RULES = r"""
at_risk(S, I) :- snack(S), region(S, R), zone(I, R).
protected(S) :- cover(C), guards(C, crumby), covers(C, R), region(S, R).
good_story(S) :- snack(S), not ruined(S).
ruined(S) :- snack(S), at_risk(S, I), not protected(S).
happy_ending :- good_story(snack).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("setting", "bedside"))
    lines.append(asp.fact("snack", "snack"))
    lines.append(asp.fact("region", "snack", "hands"))
    lines.append(asp.fact("zone", "snack", "hands"))
    lines.append(asp.fact("zone", "snack", "mouth"))
    for c in COVERS:
        lines.append(asp.fact("cover", c.id))
        for r in sorted(c.covers):
            lines.append(asp.fact("covers", c.id, r))
        for g in sorted(c.guards):
            lines.append(asp.fact("guards", c.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show ruined/1. #show happy_ending/0."))
    ruined = set(asp.atoms(model, "ruined"))
    happy = bool(asp.atoms(model, "happy_ending"))
    python_ok = True
    if ruined:
        python_ok = False
    if not happy:
        python_ok = False
    if python_ok:
        print("OK: ASP gate matches the Python reasonableness gate.")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: footer, pajama, saltine, flashback, happy ending.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
        print(asp_program("#show ruined/1. #show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(name="Lily", gender="girl", parent="mother"))]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
