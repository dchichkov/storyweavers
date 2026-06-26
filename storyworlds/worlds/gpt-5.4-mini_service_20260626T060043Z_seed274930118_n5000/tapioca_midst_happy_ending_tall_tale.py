#!/usr/bin/env python3
"""
storyworlds/worlds/tapioca_midst_happy_ending_tall_tale.py
===========================================================

A standalone story world for a tall-tale style, happy-ending story about
tapioca in the midst of a small problem that turns into a sweet fix.

Premise:
- A child or helper is making a big pot of tapioca.
- In the midst of the cooking, something goes sideways: the pudding gets too
  thick, the spoon sticks, or the pot needs help.
- A giant-hearted helper, clever tool, or simple trick saves the day.
- The ending proves the change: the tapioca is shared, and everyone is glad.

The world keeps one small simulated state:
- physical meters: fullness, heat, stickiness, wobble, sweetness
- emotional memes: hope, worry, pride, joy, teamwork

The prose is authored from the state, not from a frozen template swap.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["full", "heat", "stickiness", "wobble", "sweetness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["hope", "worry", "pride", "joy", "teamwork", "delight"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    mood: str = "bright"


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    trouble: str
    fix_hint: str
    meter: str
    impact: float
    keyword: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    solves: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"stir", "boil", "share"}, mood="sunny"),
    "pantry": Setting(place="the pantry", affords={"stir", "carry", "share"}, mood="cozy"),
    "porch": Setting(place="the porch", affords={"stir", "carry", "share"}, mood="windy"),
}

ACTIVITIES = {
    "stir": Activity(
        id="stir",
        verb="stir the tapioca",
        gerund="stirring the tapioca",
        trouble="it can turn sticky and heavy in a blink",
        fix_hint="a long spoon or a patient helper",
        meter="stickiness",
        impact=1.0,
        keyword="tapioca",
    ),
    "boil": Activity(
        id="boil",
        verb="boil the tapioca pearls",
        gerund="boiling the tapioca pearls",
        trouble="the pot can bubble up and wobble like a wagon on a hill",
        fix_hint="a steady hand and a lower flame",
        meter="wobble",
        impact=1.0,
        keyword="tapioca",
    ),
    "carry": Activity(
        id="carry",
        verb="carry the pudding to the table",
        gerund="carrying the pudding",
        trouble="the bowl can slosh and spill if it is too full",
        fix_hint="a wide tray and two careful hands",
        meter="full",
        impact=1.0,
        keyword="tapioca",
    ),
}

TOOLS = [
    Tool(
        id="longspoon",
        label="a long spoon",
        phrase="a long wooden spoon",
        helps={"stir"},
        solves={"stickiness"},
        prep="fetch a long wooden spoon",
        tail="carried the long wooden spoon back to the pot",
    ),
    Tool(
        id="lowflame",
        label="a lower flame",
        phrase="a lower flame",
        helps={"boil"},
        solves={"wobble"},
        prep="turn the fire down low",
        tail="tipped the flame low and steady",
    ),
    Tool(
        id="tray",
        label="a wide tray",
        phrase="a wide tray",
        helps={"carry"},
        solves={"full"},
        prep="find a wide tray",
        tail="set the wide tray beneath the bowl",
    ),
]

GIRL_NAMES = ["Mina", "Lena", "Ruby", "Annie", "June", "Mabel"]
BOY_NAMES = ["Finn", "Otis", "Eli", "Bram", "Nico", "Jasper"]
TRAITS = ["cheerful", "spry", "curious", "bold", "kind"]


@dataclass
class StoryParams:
    setting: str
    activity: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def reasonableness(setting: Setting, activity: Activity) -> bool:
    return activity.id in setting.affords


ASP_RULES = r"""
at_risk(A) :- activity(A), trouble(A,T), T != "".
has_tool(A) :- activity(A), tool(T), helps(T,A).
valid_story(S,A) :- setting(S), affords(S,A), activity(A), at_risk(A), has_tool(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("trouble", aid, a.trouble))
        lines.append(asp.fact("meter", aid, a.meter))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for a in sorted(t.helps):
            lines.append(asp.fact("helps", t.id, a))
        for m in sorted(t.solves):
            lines.append(asp.fact("solves", t.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((sid, aid) for sid, s in SETTINGS.items() for aid in s.affords if reasonableness(s, ACTIVITIES[aid]))
    cl = asp_valid()
    if set(py) == set(cl):
        print(f"OK: clingo gate matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("python only:", sorted(set(py) - set(cl)))
    print("clingo only:", sorted(set(cl) - set(py)))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale tapioca story world with a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [(sid, aid) for sid, s in SETTINGS.items() for aid in s.affords if reasonableness(s, ACTIVITIES[aid])]
    if args.setting:
        combos = [(sid, aid) for sid, aid in combos if sid == args.setting]
    if args.activity:
        combos = [(sid, aid) for sid, aid in combos if aid == args.activity]
    if not combos:
        raise StoryError("(No valid story matches the given options.)")
    setting_id, activity_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["grandma", "uncle", "neighbor", "big sister"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting_id, activity=activity_id, name=name, gender=gender, helper=helper, trait=trait)


def _tool_for(activity: Activity) -> Tool:
    for t in TOOLS:
        if activity.id in t.helps:
            return t
    raise StoryError("No useful tool exists for this activity.")


def tell(setting: Setting, activity: Activity, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="Helper", kind="character", type="woman" if params.helper in {"grandma", "neighbor", "big sister"} else "man", label=params.helper))
    pudding = world.add(Entity(id="tapioca", type="tapioca", label="tapioca pudding", phrase="a big bowl of tapioca pudding", caretaker=helper.id))
    tool = _tool_for(activity)

    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} was a {params.trait} little {hero.pronoun('object')} who loved sweet bowls and big adventures."
    )
    world.say(
        f"On a bright day in {setting.place}, {hero.id} wanted to {activity.verb} and make the whole house smell like vanilla and wonder."
    )
    world.say(
        f"{hero.id} and {params.helper} began with {pudding.phrase}, and the kettle sang so loud it seemed to wake the rafters."
    )

    world.para()
    if activity.id == "stir":
        pudding.meters["stickiness"] += 1.5
        hero.memes["worry"] += 1
        world.say(
            f"In the midst of stirring, the tapioca grew thick as a snowdrift in July, and the spoon nearly stuck fast."
        )
        world.say(
            f"{hero.id} blinked at the pot, because {activity.trouble}."
        )
    elif activity.id == "boil":
        pudding.meters["wobble"] += 1.5
        hero.memes["worry"] += 1
        world.say(
            f"In the midst of boiling, the pot shivered and bobbed like a goose on a fence rail."
        )
        world.say(f"{hero.id} feared the boil would run wild, because {activity.trouble}.")
    else:
        pudding.meters["full"] += 1.5
        hero.memes["worry"] += 1
        world.say(
            f"In the midst of carrying, the bowl brimmed high and threatened a splash on every step."
        )
        world.say(f"{hero.id} feared a spill, because {activity.trouble}.")

    world.para()
    tool.memes = {}
    hero.memes["hope"] += 1
    helper.memes["teamwork"] += 1
    world.say(
        f"Then {params.helper} grinned and said, \"No trouble is too tall for us to trim.\""
    )
    world.say(
        f"They decided to {tool.prep}, and together they {tool.tail}."
    )

    if activity.id == "stir":
        pudding.meters["stickiness"] = 0.0
        pudding.meters["sweetness"] += 1.5
        world.say(
            f"With the long spoon, the pudding swirled smooth again, soft as a cloud on a spoon."
        )
    elif activity.id == "boil":
        pudding.meters["wobble"] = 0.0
        pudding.meters["sweetness"] += 1.5
        world.say(
            f"With the flame turned low, the pot settled down, and the pearls bobbed like happy minnows."
        )
    else:
        pudding.meters["full"] = 0.0
        pudding.meters["sweetness"] += 1.5
        world.say(
            f"With the wide tray, the bowl rode steady to the table, proud as a parade drum."
        )

    hero.memes["joy"] += 2
    hero.memes["pride"] += 1
    helper.memes["joy"] += 1
    helper.memes["pride"] += 1

    world.say(
        f"In the happy ending, {hero.id} and {params.helper} shared the tapioca with everyone nearby, and not a drop was lost."
    )
    world.say(
        f"The whole place felt cozy and grand at once, and {hero.id} laughed because the sweetest part was how the problem turned into a feast."
    )

    world.facts.update(hero=hero, helper=helper, pudding=pudding, tool=tool, setting=setting, activity=activity)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    return [
        f'Write a tall tale for children about {hero.id} and {activity.keyword}, using the word "midst".',
        f"Tell a happy-ending story where someone tries to {activity.verb} but needs a clever fix in the midst of the trouble.",
        f"Write a playful story about tapioca that feels big as a barn and ends with everyone smiling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    activity = f["activity"]
    tool = f["tool"]
    pudding = f["pudding"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the tapioca at first?",
            answer=f"{hero.id} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"What went wrong in the midst of the cooking?",
            answer=f"In the midst of the cooking, {activity.trouble}.",
        ),
        QAItem(
            question=f"Who helped fix the problem?",
            answer=f"{helper.label if helper.label else 'The helper'} helped by using {tool.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended happily, with the tapioca shared and everyone smiling.",
        ),
        QAItem(
            question=f"Why was the ending a happy one?",
            answer=f"The trouble was fixed, the pudding stayed safe, and the family shared the tapioca together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tapioca?",
            answer="Tapioca is a starchy food that can be cooked into little pearls or a soft pudding.",
        ),
        QAItem(
            question="What does midst mean?",
            answer="Midst means in the middle of something, when it is already going on.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets fixed and the characters finish feeling glad.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(parts)}")
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


CURATED = [
    StoryParams(setting="kitchen", activity="stir", name="Mina", gender="girl", helper="grandma", trait="cheerful"),
    StoryParams(setting="pantry", activity="boil", name="Finn", gender="boy", helper="uncle", trait="curious"),
    StoryParams(setting="porch", activity="carry", name="Ruby", gender="girl", helper="neighbor", trait="bold"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:\n")
        for item in combos:
            print(" ", item)
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
