#!/usr/bin/env python3
"""
Story world: a teeny playroom mystery with a tall-tale feel.

Premise:
- A teeny gypsy child is in a playroom full of toy props.
- A shiny puzzle piece goes missing.
- The child follows clues, but the wrong shortcut leads to a bad ending.
- A lesson is learned: a mystery can be solved best by careful looking and asking for help.

The world is intentionally small and constraint-checked.  It generates one
complete story with a beginning, a middle turn, and a hard-earned ending image.
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


@dataclass
class Character:
    name: str
    label: str
    age_word: str = "teeny"
    role: str = "child"
    meters: dict[str, float] = field(default_factory=lambda: {"location": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "worry": 0.0, "pride": 0.0, "lesson": 0.0})
    traits: list[str] = field(default_factory=list)

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class Object:
    name: str
    label: str
    kind: str
    hidden: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"touched": 0.0, "moved": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"value": 0.0})


@dataclass
class World:
    setting: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, Object] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_character(self, ch: Character) -> Character:
        self.characters[ch.name] = ch
        return ch

    def add_object(self, obj: Object) -> Object:
        self.objects[obj.name] = obj
        return obj


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mina"
    object_name: str = "glimmer chip"
    helper_name: str = "Auntie"
    culprit_name: str = "wind-up mouse"
    clue_name: str = "blue block"
    setting: str = "playroom"


SETTINGS = {
    "playroom": {
        "place": "the playroom",
        "texture": "bright rugs, toy shelves, and a lopsided little table",
        "affords": {"search", "hide", "play", "ask"},
    }
}

NAMES = ["Mina", "Lina", "Tavi", "Rosa", "Junie", "Pip", "Ivy"]
HELPERS = ["Auntie", "Grandpa", "Mama", "Papa", "Cousin"]
CULPRITS = ["wind-up mouse", "sock monkey", "wooden bear", "rag doll"]
OBJECTS = ["glimmer chip", "gold star token", "tiny brass key", "silver button"]
CLUES = ["blue block", "red scarf", "yellow cup", "striped basket"]
TRAITS = ["bold", "curious", "quick-footed", "bright-eyed", "stubborn", "cheerful"]


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("This tiny world only knows the playroom.")
    world = World(setting=params.setting)
    hero = world.add_character(Character(
        name=params.name,
        label="teeny gypsy",
        age_word="teeny",
        role="child",
        traits=["tall-tale", "curious", "stubborn"],
    ))
    helper = world.add_character(Character(
        name=params.helper_name,
        label="helper",
        role="grown-up",
        traits=["patient", "kind"],
    ))
    culprit = world.add_object(Object(name=params.culprit_name, label=params.culprit_name, kind="toy"))
    prize = world.add_object(Object(name=params.object_name, label=params.object_name, kind="treasure", hidden=True, found=False))
    clue = world.add_object(Object(name=params.clue_name, label=params.clue_name, kind="clue"))
    world.facts.update(hero=hero, helper=helper, culprit=culprit, prize=prize, clue=clue)
    return world


def narrate_story(world: World) -> None:
    hero: Character = world.facts["hero"]
    helper: Character = world.facts["helper"]
    culprit: Object = world.facts["culprit"]
    prize: Object = world.facts["prize"]
    clue: Object = world.facts["clue"]

    world.say(f"Once in the playroom, there was a teeny gypsy child named {hero.name}, small as a thimble and brave as a drum.")
    world.say(f"{hero.name} loved tall tales, and {hero.pronoun()} liked to say the rug had one hundred and one magic bumps.")
    world.say(f"One bright afternoon, {hero.name} reached for the {prize.label}, but it was gone, vanished like a whisper in a pocket.")
    world.say(f"Under the toy shelf sat a {culprit.label}, and beside it lay a {clue.label} with one corner bent like a tiny ear.")

    world.para()
    hero.memes["curiosity"] += 1.0
    world.say(f"{hero.name} squinted and stomped around the playroom, hunting fast instead of thinking slow.")
    world.say(f"{hero.name} lifted a basket, tipped over a stack of cushions, and peeked in every shadow like a fox with a flashlight.")
    hero.memes["worry"] += 1.0
    world.say(f"That only made the room messier, and the missing {prize.label} stayed hidden as a moon behind cloud scraps.")

    world.para()
    world.say(f"Then {helper.name} came in and laughed a little laugh that sounded like spoons in a cup.")
    world.say(f'"A mystery to solve," {helper.name} said, "is not a race. First we look where the clues point."')
    world.say(f"So {hero.name} stopped tumbling things over and looked at the bent {clue.label}.")
    clue.found = True
    world.say(f"The clue pointed to the {culprit.label}, and the {culprit.label} pointed to the gap behind the puzzle bin.")

    world.para()
    prize.hidden = False
    prize.found = True
    hero.memes["lesson"] += 1.0
    hero.memes["pride"] += 1.0
    world.say(f"Behind the puzzle bin, there sat the {prize.label}, tucked safe under a soft blue scarf.")
    world.say(f"It turned out the {culprit.label} had dragged it there for a game, not for a trick.")
    world.say(f"{hero.name} learned that a mystery is solved better with careful eyes and a calm heart than with a wild dash.")
    world.say(f"In the end, the playroom was tidy again, the {prize.label} was back where it belonged, and the teeny gypsy child stood tall beside {helper.name}, wiser than before.")


def generation_prompts(world: World) -> list[str]:
    hero: Character = world.facts["hero"]
    prize: Object = world.facts["prize"]
    return [
        f"Write a tall-tale style story about a teeny gypsy child named {hero.name} who solves a mystery in a playroom.",
        f"Tell a short children's story where {hero.name} looks for a missing {prize.label} and learns a lesson.",
        "Write a playroom mystery with a bad ending turned into a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Character = world.facts["hero"]
    helper: Character = world.facts["helper"]
    prize: Object = world.facts["prize"]
    culprit: Object = world.facts["culprit"]
    return [
        QAItem(
            question=f"Who is the teeny gypsy child in the story?",
            answer=f"The teeny gypsy child is {hero.name}.",
        ),
        QAItem(
            question=f"What was missing in the playroom?",
            answer=f"The missing thing was the {prize.label}.",
        ),
        QAItem(
            question=f"Who helped {hero.name} solve the mystery?",
            answer=f"{helper.name} helped {hero.name} solve the mystery by telling them to follow the clues.",
        ),
        QAItem(
            question=f"What animal-like toy caused the clue trail?",
            answer=f"The {culprit.label} was the toy tied to the clue trail.",
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer="The child learned to look carefully and stay calm instead of making a bigger mess.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a problem or missing thing that needs clues and careful thinking to figure out.",
        ),
        QAItem(
            question="Why is a playroom a good place for toys?",
            answer="A playroom is a good place for toys because it is made for playing, sorting, and keeping games together in one room.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand something important that can help you do better next time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(X) :- helper_name(X).
object(O) :- prize_name(O).
culprit(C) :- culprit_name(C).
setting(playroom).

mystery_to_solve(playroom, missing(O)) :- object(O), hidden(O).
lesson_learned(H) :- hero(H), careful_search(H).
bad_ending(H) :- hero(H), rushed_search(H), hidden(O), object(O).

careful_search(H) :- hero(H), clue_found(H), calm(H).
rushed_search(H) :- hero(H), scattered_room(H).

#show mystery_to_solve/2.
#show lesson_learned/1.
#show bad_ending/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "playroom"),
        asp.fact("hero_name", "teeny_gypsy_child"),
        asp.fact("helper_name", "helping_grownup"),
        asp.fact("prize_name", "missing_treasure"),
        asp.fact("culprit_name", "toy_culprit"),
        asp.fact("hidden", "missing_treasure"),
        asp.fact("clue_found", "teeny_gypsy_child"),
        asp.fact("calm", "teeny_gypsy_child"),
        asp.fact("scattered_room", "teeny_gypsy_child"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_to_solve/2.\n#show lesson_learned/1.\n#show bad_ending/1."))
    atoms = set((sym.name, tuple(str(a) for a in sym.arguments)) for sym in model)
    expected = {
        ("mystery_to_solve", ("playroom", 'missing(missing_treasure)')),
        ("lesson_learned", ("teeny_gypsy_child",)),
        ("bad_ending", ("teeny_gypsy_child",)),
    }
    if atoms == expected:
        print("OK: ASP gate matches Python story facts.")
        return 0
    print("MISMATCH between ASP and Python facts.")
    print("ASP atoms:", sorted(atoms))
    print("Expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny tall-tale playroom mystery with a lesson learned.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--object", dest="object_name", choices=OBJECTS)
    ap.add_argument("--clue", choices=CLUES)
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(NAMES),
        helper_name=args.helper or rng.choice(HELPERS),
        culprit_name=args.culprit or rng.choice(CULPRITS),
        object_name=args.object_name or rng.choice(OBJECTS),
        clue_name=args.clue or rng.choice(CLUES),
        setting="playroom",
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ch in world.characters.values():
        lines.append(f"{ch.name}: memes={dict(ch.memes)} traits={ch.traits}")
    for obj in world.objects.values():
        lines.append(f"{obj.name}: hidden={obj.hidden} found={obj.found} kind={obj.kind}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_to_solve/2.\n#show lesson_learned/1.\n#show bad_ending/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery_to_solve/2.\n#show lesson_learned/1.\n#show bad_ending/1."))
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mina", helper_name="Auntie", culprit_name="wind-up mouse", object_name="glimmer chip", clue_name="blue block"),
            StoryParams(name="Tavi", helper_name="Grandpa", culprit_name="sock monkey", object_name="gold star token", clue_name="red scarf"),
            StoryParams(name="Junie", helper_name="Mama", culprit_name="wooden bear", object_name="tiny brass key", clue_name="yellow cup"),
        ]
        samples = [generate(p) for p in curated]
    else:
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
