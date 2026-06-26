#!/usr/bin/env python3
"""
storyworlds/worlds/appendix_hippopotamus_bravery_moral_value_problem_solving.py
==============================================================================

A small folk-tale storyworld about a brave hippopotamus, a dusty appendix, and
a problem that can only be solved with care, courage, and kindness.

Seed tale:
---
A young hippopotamus lived beside a quiet river with her grandmother.
One day, grandmother's recipe book went missing its brass spoon, the one tucked
into the appendix at the back. The hippopotamus was afraid of the dark, dusty
pages, but she also knew that supper could not be made without the spoon.
So she took a lantern, followed a ribbon trail, and crawled into the appendix.
Inside, she found the spoon stuck behind a page and carried it home. Grandmother
smiled, supper was made, and the hippopotamus learned that bravery means doing
the helpful thing even when you are scared.

World model:
---
    bravery -> actor.memes["bravery"] += 1
    helpful choice -> actor.memes["moral_value"] += 1
    careful plan -> actor.memes["problem_solving"] += 1
    dusty appendix -> object.meters["dust"] may rise, but the prize is recovered
    returned prize -> actor.memes["relief"] += 1 and the household eases
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

THEME = "Folk Tale"


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
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["dust", "lost", "clean"]:
            self.meters.setdefault(k, 0.0)
        for k in ["bravery", "moral_value", "problem_solving", "relief", "fear"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the river hut"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = "appendix"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "hands"
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "river_hut": Setting(place="the river hut", indoors=True, affords={"appendix_search"}),
}

ACTIVITIES = {
    "appendix_search": Activity(
        id="appendix_search",
        verb="search the appendix",
        gerund="searching the appendix",
        rush="hurry toward the back pages",
        mess="dust",
        soil="dusty",
        zone={"hands"},
        keyword="appendix",
        tags={"appendix", "dust"},
    )
}

PRIZES = {
    "spoon": Prize(
        label="brass spoon",
        phrase="a brass spoon for supper",
        type="spoon",
        region="hands",
    )
}

GEAR = [
    Gear(
        id="lantern",
        label="a tiny lantern",
        prep="take a tiny lantern first",
        tail="followed the ribbon trail back",
        covers={"hands"},
        guards={"dust"},
    ),
    Gear(
        id="ribbon",
        label="a blue ribbon",
        prep="tie on a blue ribbon as a guide",
        tail="kept the blue ribbon in sight",
        covers={"hands"},
        guards={"dust"},
    ),
]

HEROES = [
    ("Mosi", "girl"),
    ("Tala", "girl"),
    ("Kofi", "boy"),
    ("Baba", "boy"),
]

HELPERS = {
    "grandmother": "grandmother",
    "mother": "mother",
}


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


ASP_RULES = r"""
% A valid story is one where the activity really can disturb the prize,
% and a piece of gear exists that makes the brave plan reasonable.
at_risk(A,P) :- activity(A), prize(P), splashes(A,R), worn_on(P,R).
has_fix(A,P) :- at_risk(A,P), gear(G), covers(G,R), worn_on(P,R), guards(G,M), mess_of(A,M).
valid_story(Place,A,P) :- affords(Place,A), at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for act_id in s.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    combos.append((place, act_id, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale world: appendix, hippopotamus, bravery, moral value, problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list(HELPERS))
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid story matches those options.")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice([n for n, g in HEROES if g == gender])
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, helper=helper)


def _setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper))
    prize = world.add(Entity(
        id=params.prize,
        type=PRIZES[params.prize].type,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=helper.id,
        caretaker=helper.id,
        region=PRIZES[params.prize].region,
    ))
    world.facts.update(hero=hero, helper=helper, prize=prize, activity=ACTIVITIES[params.activity], setting=world.setting)
    return world


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    prize = world.facts["prize"]
    act = world.facts["activity"]

    hero.memes["fear"] += 1
    world.say(f"Long ago, in {world.setting.place}, there lived a young hippopotamus named {hero.id}.")
    world.say(f"{hero.id} loved {act.gerund}, but the old book's appendix was dark and dusty.")
    world.say(f"One evening, {helper.id} said that the brass spoon was missing, and supper could not begin without it.")
    world.para()
    hero.memes["bravery"] += 1
    hero.memes["moral_value"] += 1
    hero.memes["problem_solving"] += 1
    world.say(f"{hero.id} felt her knees tremble, yet she chose to be brave and help.")
    world.say(f"She took a tiny lantern, went to {act.verb}, and remembered to keep a ribbon trail behind her.")
    world.say(f"Inside the appendix, she found the spoon wedged behind a page, just where the dust was thickest.")
    world.para()
    hero.memes["relief"] += 1
    prize.meters["lost"] = 0
    prize.meters["clean"] = 1
    world.say(f"She carried the spoon back with care.")
    world.say(f"{helper.id} smiled, supper was stirred at last, and the little hippopotamus learned that bravery is using a good heart to solve a hard problem.")

    prompts = [
        f"Write a short {THEME.lower()} story about a hippopotamus, an appendix, and a lost spoon.",
        f"Tell a gentle tale where {hero.id} is brave, does the right thing, and solves a problem for {helper.id}.",
        f"Write a child-friendly story that includes the words appendix and hippopotamus and ends with a kind solution.",
    ]

    story_qa = [
        QAItem(
            question=f"Why did {hero.id} go into the appendix?",
            answer=f"{hero.id} went into the appendix because the brass spoon was missing and supper needed it. She wanted to help {helper.id}, even though the dark pages made her nervous.",
        ),
        QAItem(
            question=f"What did {hero.id} show when she took the lantern and kept the ribbon trail?",
            answer=f"She showed bravery and problem solving. She was afraid, but she still chose the helpful thing and used a simple plan so she could find her way back.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn by the end?",
            answer=f"{hero.id} learned that bravery is not loud boasting. It is doing the kind and useful thing when someone needs help, even if the task feels scary.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is an appendix?",
            answer="An appendix is a small extra part or section at the back of something, like a book, where extra notes can be kept.",
        ),
        QAItem(
            question="What is a hippopotamus?",
            answer="A hippopotamus is a very large animal that likes water and spends much of its time near rivers and lakes.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something helpful or important even when you feel scared.",
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    clingo_set = set(asp.atoms(asp.one_model(asp_program("#show valid_story/3.")).copy() if False else asp.one_model(asp_program("#show valid_story/3.")), "valid_story"))
    if py == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - clingo_set:
        print("  only in python:", sorted(py - clingo_set))
    if clingo_set - py:
        print("  only in clingo:", sorted(clingo_set - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:\n")
        for item in stories:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(place="river_hut", activity="appendix_search", prize="spoon", name=n, gender=g, helper="grandmother")) for n, g in HEROES]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
