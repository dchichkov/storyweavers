#!/usr/bin/env python3
"""
A small farmyard mystery story world with a misunderstanding and a problem to
solve.

Seed tale idea:
- A child in angelic knickerbockers notices a tiny zit-like spot.
- Everyone assumes the wrong animal caused it.
- The child follows clues around the farmyard and solves the mystery.

The world is built as a tiny simulation:
- physical meters track clues, mess, and repaired/ruined items
- emotional memes track worry, suspicion, relief, and delight
- prose is narrated from the changing world state, not from a frozen template
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the farmyard"
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    place: str
    leads_to: str
    hint: str


@dataclass
class Mystery:
    id: str
    title: str
    culprit: str
    cause: str
    solved_by: str
    reveals: str


@dataclass
class StoryParams:
    clue: str
    mystery: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTING = Setting(place="the farmyard", affords={"seek", "inspect", "solve"})

CLUES = {
    "red_spot": Clue(
        id="red_spot",
        label="a tiny red zit",
        place="the fence post",
        leads_to="straw",
        hint="It looks like a dot, but it is really a berry stain.",
    ),
    "feather": Clue(
        id="feather",
        label="a pale feather",
        place="the coop door",
        leads_to="nest",
        hint="It is a soft sign that a bird has been nearby.",
    ),
    "hoofprint": Clue(
        id="hoofprint",
        label="a neat hoofprint",
        place="the muddy path",
        leads_to="goat",
        hint="It points to an animal with hooves, not paws.",
    ),
    "crumbs": Clue(
        id="crumbs",
        label="crumbs of cracked corn",
        place="the feed bin",
        leads_to="hen",
        hint="They tell you something small and hungry passed here.",
    ),
}

MYSTERIES = {
    "stain": Mystery(
        id="stain",
        title="The Mystery of the Tiny Red Zit",
        culprit="the raspberry bush",
        cause="a berry that burst when a robin pecked at it",
        solved_by="following the berry marks",
        reveals="the red spot on the knickerbockers was only a stain",
    ),
    "missing_bell": Mystery(
        id="missing_bell",
        title="The Mystery of the Missing Bell",
        culprit="the sleepy goat",
        cause="the bell had slipped into the hay",
        solved_by="listening for the little clink in the hay",
        reveals="the missing bell was tucked under a straw pile",
    ),
    "lost_key": Mystery(
        id="lost_key",
        title="The Mystery of the Lost Shed Key",
        culprit="the nest under the roof",
        cause="a magpie carried the shiny key to decorate its nest",
        solved_by="watching where the magpie flew",
        reveals="the key was hidden in a tidy nest",
    ),
}

NAMES = {
    "girl": ["Mina", "Tessa", "Lila", "Nora", "Poppy", "June"],
    "boy": ["Eli", "Noah", "Finn", "Owen", "Theo", "Milo"],
}

HELPERS = ["grandpa", "grandma", "aunt", "uncle", "farmer", "neighbor"]


def valid_combos() -> list[tuple[str, str]]:
    return [(c, m) for c in CLUES for m in MYSTERIES]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_suspicion(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes.get("curiosity", 0) < THRESHOLD:
        return out
    if hero.memes.get("worry", 0) >= THRESHOLD and ("suspicion", "hero") not in world.fired:
        world.fired.add(("suspicion", "hero"))
        hero.memes["suspicion"] = 1.0
        out.append("The farmyard felt full of guesses.")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    clue = world.facts["clue"]
    mystery = world.facts["mystery"]
    if hero.memes.get("insight", 0) < THRESHOLD:
        return out
    sig = ("reveal", clue.id, mystery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["relief"] = 1.0
    world.facts["revealed"] = True
    out.append(f"The clue pointed to the truth: {mystery.reveals}.")
    return out


RULES = [
    Rule("suspicion", _r_suspicion),
    Rule("reveal", _r_reveal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"curiosity": 1.0},
        memes={"wonder": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=f"the {params.helper}",
        meters={"attention": 1.0},
        memes={"care": 1.0},
    ))
    knickers = world.add(Entity(
        id="knickers",
        type="clothing",
        label="angelic knickerbockers",
        phrase="angelic knickerbockers",
        owner=hero.id,
        worn_by=hero.id,
        meters={"clean": 1.0},
    ))
    clue = CLUES[params.clue]
    mystery = MYSTERIES[params.mystery]
    world.facts.update(hero=hero, helper=helper, knickers=knickers, clue=clue, mystery=mystery)

    world.say(f"{hero.label} wore angelic knickerbockers and loved to wander in the farmyard.")
    world.say(f"One morning, {hero.label} noticed {clue.label} near {clue.place}.")
    world.say(f"It looked like a little zit on the cloth, and that made {hero.label} frown.")
    hero.memes["worry"] = 1.0

    world.para()
    world.say(f"The {params.helper} said, '{clue.label.capitalize()}? That must be from the pigs.'")
    hero.memes["misunderstanding"] = 1.0
    world.say(f"But {hero.label} peered closer and thought the guess sounded wrong.")
    world.say(f"Near the spot, there was only {clue.hint.lower()}")

    world.para()
    world.say(f"So {hero.label} began to solve {mystery.title.lower()}.")
    world.say(f"{hero.label} followed {mystery.solved_by} from the fence post to the strawberry patch.")
    hero.memes["insight"] = 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(f"At last, the truth came out: {mystery.culprit} had made the trouble.")
    world.say(f"{hero.label} smiled, because the knickerbockers were still neat and the mystery was solved.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue, mystery, hero = f["clue"], f["mystery"], f["hero"]
    return [
        f"Write a short farmyard mystery for a young child about {hero.label}, angelic knickerbockers, and {clue.label}.",
        f"Tell a gentle story where a tiny zit-like mark leads to a misunderstanding and then to a solved mystery.",
        f"Write a simple mystery in the farmyard that includes angelic knickerbockers and ends with the truth revealed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, clue, mystery = f["hero"], f["clue"], f["mystery"]
    return [
        QAItem(
            question=f"What did {hero.label} notice in the farmyard?",
            answer=f"{hero.label} noticed {clue.label} near {clue.place}. It looked like a tiny zit on the angelic knickerbockers.",
        ),
        QAItem(
            question=f"Why was there a misunderstanding about the clue?",
            answer=f"The {f['helper']} guessed wrong and thought the problem came from the pigs, but the clue was really leading toward {mystery.culprit}.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{hero.label} solved it by following {mystery.solved_by}. That led to the truth about {mystery.culprit}.",
        ),
        QAItem(
            question=f"What did the solved mystery reveal?",
            answer=f"It revealed that {mystery.reveals}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that you do not understand yet, so you look for clues until you learn the answer.",
        ),
        QAItem(
            question="What do clues do in a mystery?",
            answer="Clues help you think about what happened and guide you toward the truth.",
        ),
        QAItem(
            question="What are knickerbockers?",
            answer="Knickerbockers are short, old-fashioned trousers that cover the legs and end below the knee.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.worn_by:
            parts.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(parts)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
clue_at(C) :- clue(C).
misunderstood(C) :- clue_at(C), wrong_guess(G), not correct_guess(G).
solved(M) :- mystery(M), clue_at(C), leads_to(C, X), reveals(M, X).
valid_story(C, M) :- clue(C), mystery(M), solved(M), misunderstood(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("leads_to", cid, clue.leads_to))
    for mid, myst in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("reveals", mid, myst.cause.split()[-1] if myst.cause else mid))
    lines.append(asp.fact("wrong_guess", "pigs"))
    lines.append(asp.fact("correct_guess", "berries"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Farmyard mystery story world.")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = valid_combos()
    if args.clue and args.mystery:
        if (args.clue, args.mystery) not in combos:
            raise StoryError("That clue and mystery do not fit together in this farmyard.")
    clue = args.clue or rng.choice(sorted(CLUES))
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(clue=clue, mystery=mystery, name=name, gender=gender, helper=helper)


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


CURATED = [
    StoryParams(clue="red_spot", mystery="stain", name="Mina", gender="girl", helper="grandpa"),
    StoryParams(clue="feather", mystery="lost_key", name="Eli", gender="boy", helper="aunt"),
    StoryParams(clue="hoofprint", mystery="missing_bell", name="Nora", gender="girl", helper="farmer"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
