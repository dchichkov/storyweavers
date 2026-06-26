#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/flower_sharing_curiosity_detective_story.py
==========================================================================================================================

A small detective-style storyworld about a curious child, a shared flower, and a
gentle mystery that turns into a kind solution.

Premise:
- A child detective notices something interesting about a flower.
- Curiosity leads to looking, asking, and following clues.
- Sharing resolves the problem in a kind, concrete way.

The world is intentionally small and classical:
- one setting
- one mystery object
- one detective protagonist
- one helper/possible friend
- one resolution beat
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
    caretaker: Optional[str] = None
    holds: list[str] = field(default_factory=list)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"fuzzy": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "kindness": 0.0, "worry": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    clue: str
    question: str
    answer: str
    turn: str


@dataclass
class StoryParams:
    place: str
    case: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "garden_gate": Setting(
        place="the garden gate",
        detail="A row of pots stood by the path, and one small flower leaned toward the light.",
        affords={"search", "share"},
    ),
    "window_box": Setting(
        place="the window box",
        detail="The window box was bright and tidy, with little leaves, soft soil, and one careful bloom.",
        affords={"search", "share"},
    ),
    "backyard_patch": Setting(
        place="the backyard patch",
        detail="The backyard patch was full of green stems, bees, and a flower that almost seemed to listen.",
        affords={"search", "share"},
    ),
}

CASES = {
    "missing_petals": Case(
        clue="a few petals on the path",
        question="What made the detective curious about the flower?",
        answer="The detective noticed a few petals on the path and wondered where they came from.",
        turn="The petals were not a disaster; they were the first clue.",
    ),
    "two_blooms": Case(
        clue="two flowers leaning toward the same sun",
        question="Why did the detective think something was worth sharing?",
        answer="There were two flowers leaning toward the same sun, so the detective wanted both to have enough room and water.",
        turn="Sharing the sunny spot helped both flowers look happier.",
    ),
    "watering_can": Case(
        clue="a small watering can beside one pot",
        question="Why did the helper seem important?",
        answer="The helper had a small watering can, which meant the flower could be shared with water instead of being left thirsty.",
        turn="A shared watering can made the little mystery easy to solve.",
    ),
    "note_from_neighbor": Case(
        clue="a folded note under a leaf",
        question="What did the folded note suggest?",
        answer="The folded note suggested that a neighbor had moved the flower to keep it safe, and the detective needed to ask kindly.",
        turn="A polite question brought the flower back into the open.",
    ),
}

GIRL_NAMES = ["Mia", "Lila", "Nora", "Zoe", "Ava", "June", "Iris", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Theo", "Max", "Noah", "Owen", "Eli"]
HELPERS = ["mother", "father", "friend", "neighbor"]
TRAITS = ["curious", "careful", "brave", "gentle", "bright-eyed"]


def reasonableness_gate(setting: Setting, case: Case) -> None:
    if "flower" not in case.clue and "flower" not in case.answer:
        raise StoryError("This world must center a flower.")
    if not setting.affords:
        raise StoryError("The setting must afford the small search-and-share mystery.")


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for case_id in CASES:
            combos.append((place, case_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective-style flower storyworld with curiosity and sharing."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.place and args.case:
        reasonableness_gate(SETTINGS[args.place], CASES[args.case])

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.case is None or c[1] == args.case)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    place, case_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, case=case_id, name=name, gender=gender, helper=helper, trait=trait)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("has_flower", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Case) :- setting(Place), case(Case), affords(Place, search), has_flower(Case).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def _entity_name(ent: Entity) -> str:
    return ent.label or ent.id


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    case = CASES[params.case]
    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        memes={"curiosity": 0.0, "kindness": 0.0, "worry": 0.0, "joy": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=f"the {params.helper}",
        memes={"curiosity": 0.0, "kindness": 0.0, "worry": 0.0, "joy": 0.0},
    ))
    flower = world.add(Entity(
        id="flower",
        kind="thing",
        type="flower",
        label="flower",
        phrase="a small flower with bright petals",
        owner=helper.id,
        caretaker=helper.id,
        meters={"freshness": 1.0, "petals": 5.0, "water": 1.0},
        memes={"curiosity": 0.0, "kindness": 0.0, "worry": 0.0, "joy": 0.0},
    ))
    world.facts.update(hero=hero, helper=helper, flower=flower, case=case, setting=setting)
    return world


def tell(world: World, params: StoryParams) -> None:
    hero = world.get(params.name)
    helper = world.get("helper")
    flower = world.get("flower")
    case = world.facts["case"]
    setting = world.setting

    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.label} was a {params.trait} little detective who liked to notice tiny clues."
    )
    world.say(
        f"One day at {setting.place}, {hero.label} saw {case.clue} near the flower."
    )
    world.say(setting.detail)
    world.say(
        f"{hero.label.capitalize()} became more curious and asked, "
        f"“Why is the flower looking that way?”"
    )

    world.para()
    flower.memes["worry"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"{hero.label} followed the clue with careful steps and looked around the pots."
    )
    if params.case == "missing_petals":
        flower.meters["petals"] -= 1
        world.say(
            f"The detective found one petal, then another, and knew the flower had not been lost at all."
        )
    elif params.case == "two_blooms":
        world.say(
            f"{hero.label} noticed both flowers wanted the same sunny patch, so neither one had enough space."
        )
    elif params.case == "watering_can":
        flower.meters["water"] -= 0.5
        world.say(
            f"{hero.label} spotted a small watering can, which meant the flower could be helped right away."
        )
    else:
        world.say(
            f"{hero.label} found a folded note under a leaf, and that made the mystery feel friendly instead of scary."
        )

    world.para()
    hero.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"{hero.label} shared the clue with {helper.label} instead of keeping it secret."
    )
    if params.case == "missing_petals":
        world.say(
            f"Together they gathered the fallen petals, placed them in a little dish, and made the flower look tidy again."
        )
    elif params.case == "two_blooms":
        world.say(
            f"Together they moved one pot, watered both stems, and shared the sunny spot so each bloom could stand up straight."
        )
    elif params.case == "watering_can":
        world.say(
            f"Together they poured water slowly and shared the watering can until the flower lifted its face toward the light."
        )
    else:
        world.say(
            f"Together they asked the neighbor kindly, and the flower was put back where everyone could see it."
        )

    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    flower.memes["joy"] += 1
    world.say(
        f"In the end, {hero.label} smiled like a true detective, and the flower stayed safe, bright, and shared."
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short detective story for a young child about a curious helper and a flower clue.",
        f"Tell a gentle mystery set at {world.setting.place} where someone notices {f['case'].clue} and chooses to share the clue.",
        "Write a simple story in which curiosity leads to a kind solution and the flower ends safe and happy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    case = f["case"]
    return [
        QAItem(
            question=f"What kind of story is this about {hero.label}?",
            answer=f"It is a detective story about {hero.label}, who is curious and looks for clues near a flower.",
        ),
        QAItem(
            question=f"What clue made {hero.label} curious at {world.setting.place}?",
            answer=f"{hero.label} noticed {case.clue}, and that made the flower seem important.",
        ),
        QAItem(
            question=f"How did {hero.label} and {helper.label} solve the little mystery?",
            answer=case.answer + f" They shared what they knew and solved it kindly.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The flower stayed safe and bright, and {hero.label} felt proud for sharing the clue.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flower?",
            answer="A flower is a plant part that can bloom with petals and often grows from a stem.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone want to look, ask questions, and learn what is going on.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use, enjoy, or know about something too.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.phrase:
            bits.append(f'phrase="{ent.phrase}"')
        lines.append(f"  {ent.id} ({ent.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden_gate", case="missing_petals", name="Mia", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="window_box", case="watering_can", name="Leo", gender="boy", helper="friend", trait="careful"),
    StoryParams(place="backyard_patch", case="two_blooms", name="Nora", gender="girl", helper="father", trait="gentle"),
]


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.case} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
