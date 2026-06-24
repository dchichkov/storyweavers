#!/usr/bin/env python3
"""
storyworlds/worlds/appearance_guinea_mystery_to_solve_moral_value.py
=====================================================================

A small ghost-story-style world about a mysterious appearance change in a guinea
pig, with a moral-value turn: fear gives way to kindness, and the "ghostly"
mystery is solved by careful looking.

Premise:
- A child sees a guinea pig with a startling appearance.
- The child suspects a ghostly cause.

Tension:
- The guinea pig's appearance changes because of a harmless, hidden cause.
- The child must decide whether to panic, ignore, or investigate kindly.

Turn:
- The child looks closely, asks gentle questions, and discovers the truth.

Resolution:
- The "mystery" is solved.
- The moral value is explicit in the ending image: kindness, honesty, and care
  matter more than scary guesses.

The world is intentionally small and classical: one setting, one hero, one
mysterious animal, one hidden cause, one social turn.
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

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = True
    eerie: bool = False


@dataclass
class Clue:
    id: str
    name: str
    description: str
    effect: str
    reveals: str


@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    gender: str
    adult: str
    trait: str
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "attic": Setting(place="the attic", indoor=True, eerie=True),
    "hallway": Setting(place="the hallway", indoor=True, eerie=True),
    "garden_shed": Setting(place="the garden shed", indoor=False, eerie=True),
}

CLUES = {
    "chalk": Clue(
        id="chalk",
        name="white chalk dust",
        description="a thin white powder on the guinea pig's fur",
        effect="the fur looked pale and ghostly",
        reveals="the dust came from a broken chalk bag",
    ),
    "paint": Clue(
        id="paint",
        name="silver paint flecks",
        description="tiny shiny spots on the guinea pig's back",
        effect="the fur glittered like a moonlit ghost",
        reveals="the flecks came from a tipped craft tin",
    ),
    "flour": Clue(
        id="flour",
        name="flour dust",
        description="soft flour on the guinea pig's nose and ears",
        effect="the little face looked snow-white",
        reveals="the flour came from a kitchen spill",
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Nora", "Ivy", "Maya", "Ella"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Eli", "Noah", "Luca"]
TRAITS = ["curious", "gentle", "brave", "careful", "soft-spoken", "kind"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% The guinea pig's appearance is mysterious when a visible clue makes it look
% ghostly.
mysterious(A) :- appearance(A, ghostly), visible_clue(A, _).

% A mystery is solved when the true clue is found and its cause is named.
solved(A) :- mysterious(A), found_clue(A, C), cause_named(C).

% Moral value: if the child chooses kindness, the story's ending is good.
morally_good(H) :- kind_choice(H).

#show mysterious/1.
#show solved/1.
#show morally_good/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        if s.eerie:
            lines.append(asp.fact("eerie", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("cause_named", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mysterious/1. #show solved/1. #show morally_good/1."))
    atoms = {(sym.name, tuple(getattr(a, 'number', getattr(a, 'string', a.name)) for a in sym.arguments)) for sym in model}
    if atoms:
        print("OK: ASP program solves at least one model.")
        return 0
    print("MISMATCH: ASP program produced no shown atoms.")
    return 1


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

def choose_setting(place: str) -> Setting:
    if place not in SETTINGS:
        raise StoryError(f"Unknown setting: {place}")
    return SETTINGS[place]


def choose_clue(clue: str) -> Clue:
    if clue not in CLUES:
        raise StoryError(f"Unknown clue: {clue}")
    return CLUES[clue]


def reasonableness_gate(setting: Setting, clue: Clue) -> None:
    if not setting.eerie:
        raise StoryError("This story needs an eerie setting for the ghost-story feel.")
    if clue.id not in CLUES:
        raise StoryError("The mystery clue must be one of the built-in appearance changes.")


def story_appearance_text(clue: Clue) -> str:
    return {
        "chalk": "pale with white dust",
        "paint": "sparkling with silver flecks",
        "flour": "softly snow-white",
    }[clue.id]


def solve_text(clue: Clue) -> str:
    return clue.reveals


def moral_text(hero: Entity) -> str:
    return f"{hero.id} learned that kind eyes solve scary guesses better than hurried fear."


def generate_world(params: StoryParams) -> World:
    setting = choose_setting(params.place)
    clue = choose_clue(params.clue)
    reasonableness_gate(setting, clue)

    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait],
        memes={"curiosity": 1.0, "fear": 0.0, "kindness": 0.0},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=params.adult,
        label=f"the {params.adult}",
        memes={"calm": 1.0},
    ))
    guinea = world.add(Entity(
        id="guinea",
        kind="animal",
        type="guinea pig",
        label="guinea pig",
        phrase="a small guinea pig with bright eyes",
        owner=hero.id,
        caretaker=hero.id,
        meters={"appearance": 0.0},
        memes={"mystery": 0.0, "safe": 0.0},
    ))
    world.facts.update(hero=hero, adult=adult, guinea=guinea, clue=clue, setting=setting)
    return world


def narrate(world: World) -> None:
    hero: Entity = world.facts["hero"]
    adult: Entity = world.facts["adult"]
    guinea: Entity = world.facts["guinea"]
    clue: Clue = world.facts["clue"]
    setting: Setting = world.setting

    world.say(f"One gray evening in {setting.place}, {hero.id} found a little guinea pig in a lamp glow.")
    world.say(f"The guinea pig had a {story_appearance_text(clue)} appearance, and that made it look almost like a ghost.")

    world.para()
    hero.memes["fear"] += 1.0
    guinea.meters["appearance"] = 1.0
    world.say(f"{hero.id} held still and stared. {hero.pronoun().capitalize()} wanted to run, but the tiny animal only blinked.")
    world.say(f"{adult.label.capitalize()} whispered, \"Let's look closely before we guess.\"")

    world.para()
    world.say(f"{hero.id} knelt down and used a small cloth to gently wipe the guinea pig's fur.")
    world.say(f"That was when the mystery changed shape: {solve_text(clue)}.")
    hero.memes["fear"] = 0.0
    hero.memes["kindness"] += 1.0
    guinea.meters["appearance"] = 0.0
    guinea.memes["safe"] = 1.0
    world.say(f"The guinea pig was not a ghost at all. It was only a real little pet with a funny mess on its fur.")

    world.para()
    world.say(f"{hero.id} smiled and {hero.pronoun('possessive')} shoulders softened.")
    world.say(f"{moral_text(hero)}")
    world.say(f"By the end, the guinea pig was clean, the room felt warm again, and the scary shadow had turned into a harmless story.")


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    clue: Clue = world.facts["clue"]
    return [
        f"Write a short ghost-story-style tale about {hero.id} and a guinea pig whose appearance seems haunted.",
        f"Tell a gentle mystery where a guinea pig looks {clue.description}, but the truth is ordinary and kind.",
        f"Write a child-facing story about a spooky-looking guinea pig appearance, a calm clue, and a moral lesson about kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    adult: Entity = world.facts["adult"]
    clue: Clue = world.facts["clue"]
    guinea: Entity = world.facts["guinea"]

    return [
        QAItem(
            question=f"What did {hero.id} think was strange about the guinea pig?",
            answer=f"{hero.id} thought the guinea pig's appearance looked ghostly because it was {story_appearance_text(clue)}.",
        ),
        QAItem(
            question="What helped solve the mystery?",
            answer=f"A gentle look and a careful wipe solved it, and then everyone saw that {clue.reveals}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} stay calm?",
            answer=f"The {adult.type} helped by telling {hero.id} to look closely before guessing.",
        ),
        QAItem(
            question="What was the guinea pig really like?",
            answer=f"It was a real little pet, not a ghost, and it ended the story safe and clean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    clue: Clue = world.facts["clue"]
    return [
        QAItem(
            question="What is a guinea pig?",
            answer="A guinea pig is a small pet animal with soft fur, quick feet, and a nose that wiggles when it sniffs.",
        ),
        QAItem(
            question="Why can white dust or flour make something look spooky?",
            answer="White dust can make fur or clothes look pale and ghostly, so it may seem strange in dim light.",
        ),
        QAItem(
            question=f"What is {clue.name}?",
            answer=f"{clue.name.capitalize()} is a harmless clue that can make something look different until someone finds the real cause.",
        ),
        QAItem(
            question="What is the best way to solve a mystery?",
            answer="The best way is to look closely, stay calm, ask questions, and check for an ordinary answer first.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== Prompts ==")
    for p in sample.prompts:
        lines.append(f"- {p}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story-style mystery about a guinea pig's appearance.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--name")
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
    place = args.place or rng.choice(sorted(SETTINGS.keys()))
    clue = args.clue or rng.choice(sorted(CLUES.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    adult = args.adult or rng.choice(["mother", "father"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    setting = SETTINGS[place]
    reasonableness_gate(setting, CLUES[clue])
    return StoryParams(place=place, clue=clue, name=name, gender=gender, adult=adult, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    narrate(world)
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
    StoryParams(place="attic", clue="chalk", name="Mina", gender="girl", adult="mother", trait="curious"),
    StoryParams(place="hallway", clue="paint", name="Owen", gender="boy", adult="father", trait="careful"),
    StoryParams(place="garden_shed", clue="flour", name="Ivy", gender="girl", adult="mother", trait="gentle"),
]


def asp_validity() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show mysterious/1. #show solved/1. #show morally_good/1."))
    return sorted({(sym.name, tuple(a.name if hasattr(a, "name") else getattr(a, "string", getattr(a, "number", None)) for a in sym.arguments)) for sym in model})


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mysterious/1. #show solved/1. #show morally_good/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available; use --show-asp to inspect the program.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
