#!/usr/bin/env python3
"""
A tiny superhero story world about bacon, a removal problem, a twist, and a reconciliation.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass
class Character:
    name: str
    role: str
    meme: dict[str, float] = field(default_factory=dict)
    meter: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str = "Nova"
    sidekick_name: str = "Zip"
    place: str = "the city plaza"
    seed: Optional[int] = None


@dataclass
class World:
    hero: Character
    sidekick: Character
    place: str
    bacon_removed: bool = False
    twist: str = ""
    reconciliation: bool = False
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


HERO_NAMES = ["Nova", "Astra", "Bolt", "Mira", "Jet", "Vega", "Talon", "Pip"]
SIDEKICK_NAMES = ["Zip", "Echo", "Mox", "Lumi", "Dash", "Kite", "Penny", "Rex"]
PLACES = ["the city plaza", "the rooftop garden", "the busy museum", "the moonlit bridge", "the train station"]

TWISTS = [
    {
        "name": "the bacon decoy",
        "setup": "a shiny tray of bacon sat on a bench beside the fountain",
        "twist": "the bacon was only a prop, and the real trouble was a missing lunchbox hidden under the bench",
        "problem": "the smell drew hungry pigeons, and the lunchbox needed to be removed before the birds pecked at it",
        "clue": "a taped note on the tray said PROP FOR PARADE and pointed to the lunchbox shadow",
        "first_move": "reached for the bacon tray in a rush",
        "heroic_move": "lifted the bench, removed the lunchbox, and carried it to a safe table",
        "dialogue": (
            "\"That's not a snack,\" said the sidekick.\n"
            "\"Then what is it?\" asked the hero.\n"
            "\"A clue,\" said the sidekick. \"Look under the bench!\""
        ),
        "ending": "the pigeons wandered off while the bench stayed clear and the lunchbox sat safely in the hero's hands",
    },
    {
        "name": "the bacon signal",
        "setup": "a bacon-shaped signal light flashed red over the alley gate",
        "twist": "the signal was not an alarm about food at all; it was a rescue beacon made for a cat in a box",
        "problem": "the city guard had mistaken the signal and wanted to remove every crate from the alley at once",
        "clue": "the beacon's instruction card showed a cat paw and a bright arrow, not a warning about the snack cart",
        "first_move": "started clearing the snack cart from the alley",
        "heroic_move": "read the card, stopped the cart removal, and guided the guard to the trapped cat",
        "dialogue": (
            "\"Why is there bacon on the light?\" asked the sidekick.\n"
            "\"Because someone painted it that way,\" said the hero.\n"
            "\"Then the light is lying,\" said the sidekick. \"Let's read the card.\""
        ),
        "ending": "the cat curled up on a blanket while the snack cart rolled back into place",
    },
    {
        "name": "the bacon cape mix-up",
        "setup": "a bacon-colored cape hung from the statue's arm",
        "twist": "it belonged to the mayor's costume, and the real issue was a broken ribbon that kept snagging the cape",
        "problem": "if nobody removed the snagged ribbon, the statue display would collapse during the parade",
        "clue": "the ribbon had a museum tag that matched the costume box, not the snack stand",
        "first_move": "tugged at the cape to free it",
        "heroic_move": "carefully removed the ribbon, then folded the cape and returned it to the costume box",
        "dialogue": (
            "\"I thought the cape was the problem,\" said the hero.\n"
            "\"The ribbon is the twist,\" said the sidekick.\n"
            "\"Good catch,\" said the hero. \"Let's fix the real thing.\""
        ),
        "ending": "the statue stood tall again, wearing only a smooth cape and a proud parade smile",
    },
    {
        "name": "the bacon bridge rumor",
        "setup": "people whispered that bacon crumbs were falling from the bridge cables",
        "twist": "the crumbs were actually tiny red paint flakes from a repair crew overhead",
        "problem": "the wrong rumor made the crew want to remove the bridge sign and close the walkway",
        "clue": "the flakes matched the fresh paint on the repair bucket and not any picnic food",
        "first_move": "announced that the bridge needed to be shut immediately",
        "heroic_move": "showed the paint bucket, calmed the crowd, and helped the crew remove only the loose flakes",
        "dialogue": (
            "\"Smell the bacon?\" asked the sidekick.\n"
            "\"I smell paint,\" said the hero.\n"
            "\"Then the rumor needs a cape of its own,\" the sidekick joked."
        ),
        "ending": "the bridge stayed open, and the paint crew waved from above with clean hands",
    },
    {
        "name": "the bacon locker twist",
        "setup": "a locker door in the school hall stuck open beside a lunch tray of bacon",
        "twist": "the tray belonged to a class party, while the locker held a missing science robot",
        "problem": "the robot battery needed to be removed before it overheated behind the warm tray",
        "clue": "a buzzing sound came from the locker, not from the bacon tray",
        "first_move": "tried to shut the locker with one hand and grab the tray with the other",
        "heroic_move": "opened the locker fully, removed the battery, and returned the lunch tray to the party table",
        "dialogue": (
            "\"Lunch first?\" whispered the sidekick.\n"
            "\"Safety first,\" said the hero.\n"
            "\"Then let's rescue the robot before the bacon gets any ideas,\" said the sidekick."
        ),
        "ending": "the robot blinked happily on the shelf while the party tray stayed warm and harmless",
    },
]

OPENINGS = [
    "One ordinary afternoon in {place},",
    "Just before the patrol bell rang,",
    "While the sun slid between the tall buildings,",
    "At the start of a very busy hour,",
    "During a quiet round of hero watch,",
]

TURNS = [
    "That was when the real twist appeared.",
    "Then the situation changed in a way nobody expected.",
    "Right away, the first guess turned out to be wrong.",
    "A second look made the mystery make sense.",
    "The clue changed everything.",
]

RECONCILIATIONS = [
    "The hero and sidekick looked at each other and smiled, because now they were solving the same problem again.",
    "After the misunderstanding, they apologized, listened, and worked side by side.",
    "Once the mix-up was clear, the two friends felt better and put the plan back together.",
    "Their voices softened, and the team became a team again.",
    "With the mistake fixed, they shared a relieved laugh and shook hands over the repaired mess.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny superhero story world with bacon and a twist.")
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--sidekick-name", choices=SIDEKICK_NAMES)
    ap.add_argument("--place", choices=PLACES)
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
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick_name or rng.choice([n for n in SIDEKICK_NAMES if n != hero_name])
    place = args.place or rng.choice(PLACES)
    return StoryParams(hero_name=hero_name, sidekick_name=sidekick_name, place=place)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name == params.sidekick_name:
        raise StoryError("The hero and sidekick need different names.")
    if params.place not in PLACES:
        raise StoryError("That setting is not part of this superhero world.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)

    seed = params.seed if params.seed is not None else 0
    rng = random.Random(seed)
    twist = rng.choice(TWISTS)
    opening = rng.choice(OPENINGS).format(place=params.place)
    turn = rng.choice(TURNS)
    reconciliation = rng.choice(RECONCILIATIONS)

    hero = Character(name=params.hero_name, role="hero", meme={"brave": 1.0, "careful": 1.0}, meter={"energy": 8})
    sidekick = Character(name=params.sidekick_name, role="sidekick", meme={"sharp": 1.0, "kind": 1.0}, meter={"energy": 7})
    world = World(hero=hero, sidekick=sidekick, place=params.place)

    lines = [
        f"{hero.name} wore a bright cape and kept watch over {params.place}.",
        f"{opening} {twist['setup']}.",
        f"{hero.name} thought the bacon was the problem, so {twist['first_move']}.",
        f"{turn} {twist['twist']}.",
        twist["dialogue"],
        f"{sidekick.name} pointed out the clue: {twist['clue']}.",
        f"The real danger was plain: {twist['problem']}.",
        f"With a steady breath, {hero.name} {twist['heroic_move']}.",
        f"{reconciliation}",
        f"In the end, {twist['ending']}.",
    ]

    world.bacon_removed = True
    world.twist = twist["name"]
    world.reconciliation = True
    world.facts["story"] = " ".join(lines)
    world.facts["twist"] = twist["name"]
    world.facts["problem"] = twist["problem"]
    world.facts["clue"] = twist["clue"]
    world.facts["repair"] = twist["heroic_move"]

    prompts = [
        f"Write a superhero story called {twist['name']} set in {params.place}.",
        f"Tell a child-friendly story where {params.hero_name} and {params.sidekick_name} must remove bacon-related confusion and find the real problem.",
        f"Make the story include a twist and reconciliation, with dialogue that changes what the characters decide to do.",
    ]

    story_qa = [
        QAItem(
            question=f"What did {params.hero_name} think was the problem at first?",
            answer=f"{params.hero_name} first thought the bacon was the problem.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=twist["twist"],
        ),
        QAItem(
            question=f"What clue helped {params.sidekick_name} solve the mix-up?",
            answer=f"The clue was that {twist['clue']}.",
        ),
        QAItem(
            question="How did the hero fix the real problem?",
            answer=f"{params.hero_name} {twist['heroic_move']}.",
        ),
        QAItem(
            question="How did the hero and sidekick feel at the end?",
            answer="They reconciled and worked together again with relief.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What makes a superhero story exciting?",
            answer="A superhero story is exciting when a brave character faces a problem, learns the truth, and helps fix things.",
        ),
        QAItem(
            question="What is a twist?",
            answer="A twist is a surprising change that shows the first idea was not the whole truth.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people repair a misunderstanding and become friendly or cooperative again.",
        ),
        QAItem(
            question="What should a hero do before acting on a guess?",
            answer="A hero should look for clues and check the facts before taking action.",
        ),
        QAItem(
            question="Why is dialogue important in a story?",
            answer="Dialogue lets characters explain, question, and change their plans in a lively, clear way.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        w = sample.world
        print(f"hero={w.hero.name}, role={w.hero.role}, meme={w.hero.meme}, meter={w.hero.meter}")
        print(f"sidekick={w.sidekick.name}, role={w.sidekick.role}, meme={w.sidekick.meme}, meter={w.sidekick.meter}")
        print(f"place={w.place}, bacon_removed={w.bacon_removed}, twist={w.twist}, reconciliation={w.reconciliation}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
hero(H) :- hero_name(H).
sidekick(S) :- sidekick_name(S).
place(P) :- place_name(P).

twist(T) :- twist_name(T).
reconciliation :- reconciliation_fact.

valid_story :- hero(H), sidekick(S), place(P), H != S.
#show valid_story/0.
"""


def asp_facts() -> str:
    from storyworlds import asp
    facts = []
    facts.extend(asp.fact("hero_name", name) for name in HERO_NAMES)
    facts.extend(asp.fact("sidekick_name", name) for name in SIDEKICK_NAMES)
    facts.extend(asp.fact("place_name", place) for place in PLACES)
    facts.extend(asp.fact("twist_name", t["name"]) for t in TWISTS)
    facts.append("reconciliation_fact.")
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    from storyworlds import asp
    program = asp_program("#show valid_story/0.")
    model = asp.one_model(program)
    atoms = asp.atoms(model, "valid_story")
    py_ok = True
    asp_ok = len(atoms) == 1
    if py_ok == asp_ok:
        print("OK: ASP rules are present and produce a valid story marker.")
        return 0
    print("MISMATCH between Python and ASP validity checks.")
    return 1


def generation_samples(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        out: list[StoryParams] = []
        for i, place in enumerate(PLACES):
            out.append(StoryParams(hero_name=HERO_NAMES[i % len(HERO_NAMES)], sidekick_name=SIDEKICK_NAMES[i % len(SIDEKICK_NAMES)], place=place))
        return out
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [resolve_params(args, random.Random(base + i)) for i in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        from storyworlds import asp
        model = asp.one_model(asp_program("#show valid_story/0."))
        print("\n".join(str(a) for a in asp.atoms(model, "valid_story")))
        return

    samples: list[StorySample] = []
    for i, params in enumerate(generation_samples(args)):
        params.seed = (args.seed if args.seed is not None else 0) + i
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
