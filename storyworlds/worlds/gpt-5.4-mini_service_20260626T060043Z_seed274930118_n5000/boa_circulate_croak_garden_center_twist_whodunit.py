#!/usr/bin/env python3
"""
A standalone storyworld for a small whodunit set in a garden center.

Premise:
A curious child and a careful worker notice that something is wrong at the
garden center: a prized boa plant ribbon keeps slipping around, a crate of
seeds has been moved, and a frog-shaped toy croaks from somewhere it should not
be. The child and the worker follow clues, ask who moved what, and discover that
Twist -- a lively little helper -- had been trying to circulate watering cans
between the shelves and made a puzzle out of the paths.

The storyworld supports a child-friendly mystery with:
- a garden center setting
- the seed words "boa", "circulate", and "croak"
- a Twist character
- a whodunit-style reveal and resolution

The model uses meters and memes, a reasonableness gate, and an inline ASP twin
for parity checking.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    carried_by: Optional[str] = None
    hidden_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the garden center"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    clue: str
    mess: str
    zone: set[str]
    reveal: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectItem:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False


@dataclass
class TwistPlan:
    label: str
    verb: str
    trail: str
    fix: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.revealed: bool = False
        self.suspects: list[str] = []
        self.clues: list[str] = []

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


@dataclass
class StoryParams:
    suspect: str
    clue_item: str
    hero_name: str
    hero_gender: str
    helper_name: str
    twist_name: str
    seed: Optional[int] = None


SETTINGS = {
    "garden_center": Setting(place="the garden center", affords={"circulate", "croak"}),
}

ACTIVITIES = {
    "circulate": Action(
        id="circulate",
        verb="circulate the watering cans",
        gerund="circulating watering cans",
        clue="a trail of wet footprints",
        mess="wet",
        zone={"floor"},
        reveal="the cans had been moved to the wrong aisle",
        keyword="circulate",
        tags={"water", "path", "wet"},
    ),
    "croak": Action(
        id="croak",
        verb="listen for the croak",
        gerund="listening for a croak",
        clue="a soft croak from behind the seed shelf",
        mess="noise",
        zone={"air"},
        reveal="the croak was a toy frog in a plant basket",
        keyword="croak",
        tags={"frog", "toy", "sound"},
    ),
}

OBJECTS = {
    "boa": ObjectItem(
        label="boa",
        phrase="a green boa ribbon for the display plant",
        type="boa",
        location="display shelf",
    ),
    "twist": ObjectItem(
        label="Twist",
        phrase="Twist's little red helper badge",
        type="badge",
        location="counter",
    ),
    "seed_box": ObjectItem(
        label="seed box",
        phrase="a box of seed packets",
        type="box",
        location="seed aisle",
    ),
    "toy_frog": ObjectItem(
        label="toy frog",
        phrase="a squeaky toy frog",
        type="toy",
        location="plant basket",
    ),
}

HERO_NAMES = ["Mina", "Jules", "Pip", "Nora", "Elsie", "Theo"]
HELPER_NAMES = ["Moe", "Lena", "Iris", "Ben"]
TWIST_NAMES = ["Twist", "Tess", "Toby", "Tara"]
TRAITS = ["curious", "careful", "brave", "quiet", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_name, setting in SETTINGS.items():
        for action_name in setting.affords:
            for obj_name in OBJECTS:
                if action_name == "circulate" and obj_name in {"boa", "seed_box"}:
                    combos.append((setting_name, action_name, obj_name))
                if action_name == "croak" and obj_name in {"toy_frog"}:
                    combos.append((setting_name, action_name, obj_name))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Garden-center whodunit storyworld with boa, circulate, croak, and Twist."
    )
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--activity", choices=list(ACTIVITIES))
    ap.add_argument("--object", choices=list(OBJECTS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--twist")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    if args.object == "boa" and args.activity != "circulate":
        raise StoryError("The boa clue belongs to the circulate mystery, not the croak one.")
    if args.object == "toy_frog" and args.activity != "croak":
        raise StoryError("The toy frog clue belongs to the croak mystery.")
    if args.activity == "croak" and args.object != "toy_frog":
        raise StoryError("Croak stories need the toy frog clue.")
    if args.activity == "circulate" and args.object not in {"boa", "seed_box"}:
        raise StoryError("Circulate stories need either the boa or the seed box clue.")

    setting_name, activity_name, object_name = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    twist_name = args.twist or "Twist"
    if twist_name == hero_name:
        raise StoryError("Twist should be a separate helper or suspect, not the hero.")
    return StoryParams(
        suspect=object_name,
        clue_item=object_name,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        twist_name=twist_name,
        seed=None,
    )


def _pronoun_gender(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def tell(setting: Setting, activity: Action, clue_item: ObjectItem, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=_pronoun_gender(params.hero_gender),
        traits=["curious"],
        meters={"attention": 1.0},
        memes={"unease": 0.0, "clarity": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="adult",
        traits=["careful"],
        meters={"attention": 1.0},
        memes={"concern": 0.0},
    ))
    twist = world.add(Entity(
        id=params.twist_name,
        kind="character",
        type="adult",
        traits=["lively"],
        meters={"attention": 1.0},
        memes={"nervousness": 0.0},
    ))
    clue = world.add(Entity(
        id=clue_item.label,
        type=clue_item.type,
        label=clue_item.label,
        phrase=clue_item.phrase,
        location=clue_item.location,
    ))
    boa = world.add(Entity(
        id="boa",
        type="boa",
        label="boa",
        phrase="a green boa ribbon",
        location="display shelf",
    ))
    if clue_item.label == "boa":
        boa.carried_by = twist.id
    world.say(f"At {world.setting.place}, {hero.id} noticed something odd near the plant shelves.")
    world.say(f"A bright {boa.label} ribbon kept seeming to circulate from one display to another.")
    world.say(f"Then {activity.clue}.")
    world.para()
    world.say(f"{helper.id} frowned and whispered, \"Who moved the clue?\"")
    world.say(f"{hero.id} looked at the shelves and tried to follow the trail like a tiny detective.")
    world.say(f"The answer was hiding in plain sight: {activity.reveal}.")
    world.para()
    world.say(f"At last, {twist.id} admitted it. {twist.id} had been trying to {activity.verb} quickly.")
    world.say(f"But that made the clues look spooky and strange.")
    world.say(f"{helper.id} helped put everything back in order, and the garden center felt calm again.")
    world.say(f"{hero.id} smiled when the little mystery was solved.")
    world.revealed = True
    world.facts = {
        "hero": hero,
        "helper": helper,
        "twist": twist,
        "clue": clue,
        "activity": activity,
        "setting": setting,
        "clue_item": clue_item,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short whodunit for a child set in a garden center with the words "boa", "circulate", and "croak".',
        f"Tell a gentle mystery where {f['hero'].id} and {f['helper'].id} notice clues around {f['setting'].place}.",
        "Make the hidden cause a small misunderstanding, then end with the mystery solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    twist = f["twist"]
    clue_item = f["clue_item"]
    activity = f["activity"]
    qa = [
        QAItem(
            question="Where does the story happen?",
            answer=f"It happens at {world.setting.place}, where the shelves and plants made the clues look puzzling.",
        ),
        QAItem(
            question=f"What did {hero.id} notice near the plant shelves?",
            answer=f"{hero.id} noticed a clue about the {clue_item.label} and a strange trail that made the place feel like a mystery.",
        ),
        QAItem(
            question=f"Who was really behind the odd clues?",
            answer=f"It was {twist.id}. {twist.id} had been trying to {activity.verb}, and that made everything look mysterious.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{helper.id} helped put the clues back in order, and then {twist.id} admitted the mistake.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a garden center?",
            answer="A garden center is a shop where people buy plants, soil, pots, seeds, and tools for gardens.",
        ),
        QAItem(
            question="What does it mean to circulate?",
            answer="To circulate means to move around and pass from one place to another.",
        ),
        QAItem(
            question="What does a croak sound like?",
            answer="A croak is a deep frog-like sound, often soft and a little funny.",
        ),
        QAItem(
            question="What is a boa?",
            answer="A boa can be a long ribbon or scarf that hangs in a loose, wavy shape.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.hidden_by:
            bits.append(f"hidden_by={e.hidden_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_story(params: StoryParams) -> bool:
    return (
        (params.clue_item == "boa" and params.suspect == "boa")
        or (params.clue_item == "toy_frog" and params.suspect == "toy_frog")
    )


ASP_RULES = r"""
setting(garden_center).
affords(garden_center,circulate).
affords(garden_center,croak).

activity(circulate).
activity(croak).

clue(boa).
clue(toy_frog).

valid(garden_center,circulate,boa) :- affords(garden_center,circulate), clue(boa).
valid(garden_center,croak,toy_frog) :- affords(garden_center,croak), clue(toy_frog).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sname in SETTINGS:
        lines.append(asp.fact("setting", sname))
        for act in SETTINGS[sname].affords:
            lines.append(asp.fact("affords", sname, act))
    for aname in ACTIVITIES:
        lines.append(asp.fact("activity", aname))
    for oname in OBJECTS:
        lines.append(asp.fact("clue", oname))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS["garden_center"]
    activity = ACTIVITIES["circulate"] if params.suspect == "boa" else ACTIVITIES["croak"]
    clue_item = OBJECTS[params.clue_item]
    world = tell(setting, activity, clue_item, params)
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


CURATED = [
    StoryParams(suspect="boa", clue_item="boa", hero_name="Mina", hero_gender="girl", helper_name="Moe", twist_name="Twist"),
    StoryParams(suspect="toy_frog", clue_item="toy_frog", hero_name="Jules", hero_gender="boy", helper_name="Lena", twist_name="Twist"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.clue_item} mystery"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
