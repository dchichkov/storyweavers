#!/usr/bin/env python3
"""
storyworlds/worlds/commodore_mystery_to_solve_sound_effects_rhyming.py
======================================================================

A tiny, standalone storyworld about a commodore, a mystery to solve, and
rhyming sound-effects prose.

Seed tale idea:
- A neat little harbor has a missing bell.
- A commodore hears funny sounds: "clink-clink", "creak-creak", "splash!"
- The search follows the sounds, finds the real cause, and ends in a happy,
  tidy reveal.

The world is intentionally small and constraint-driven:
- A mystery must be plausible for the chosen setting.
- A solving tool or clue must actually fit the mystery.
- The story is state-driven: curiosity grows, clues accumulate, the answer is
  found, and the ending image proves the change.

This script follows the shared Storyweavers storyworld contract.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | clue | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    wearer: Optional[str] = None
    hidden: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "lady"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "gentleman"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)
    mood: str = ""


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    sound: str
    clue: str
    solve_tool: str
    reveal: str
    setting_tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    title: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "harbor": Setting(place="the harbor", affordances={"echoes", "boats", "ropes"}, mood="salt-bright"),
    "ship": Setting(place="the ship", affordances={"echoes", "ropes", "lanterns"}, mood="rocking"),
    "dock": Setting(place="the dock", affordances={"echoes", "boats", "ropes"}, mood="breezy"),
}

MYSTERIES = {
    "missing_bell": Mystery(
        id="missing_bell",
        label="a missing bell",
        phrase="the bright brass bell",
        sound="clink-clink",
        clue="a loose rope near the net",
        solve_tool="a lantern",
        reveal="the bell had snagged in a fishing net",
        setting_tags={"harbor", "ship", "dock"},
    ),
    "stolen_whistle": Mystery(
        id="stolen_whistle",
        label="a stolen whistle",
        phrase="the silver whistle",
        sound="tweet-tweet",
        clue="a trail of crumbs by the snack crate",
        solve_tool="a magnifying glass",
        reveal="the whistle had rolled behind the snack crate",
        setting_tags={"harbor", "dock"},
    ),
    "muffled_drum": Mystery(
        id="muffled_drum",
        label="a muffled drumbeat",
        phrase="the marching drum",
        sound="thump-thump",
        clue="a canvas sack tied with a knot",
        solve_tool="a needle",
        reveal="the drum was wrapped in a sailcloth sack",
        setting_tags={"ship", "dock"},
    ),
}

TOOLS = {
    "lantern": "a lantern",
    "magnifier": "a magnifying glass",
    "needle": "a needle",
}

NAMES = {
    "girl": ["Nina", "Mina", "Lena", "Tia", "Sora"],
    "boy": ["Theo", "Milo", "Finn", "Rowan", "Jude"],
}

TRAITS = ["brave", "curious", "cheery", "snappy", "spry"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def rhyme2(a: str, b: str) -> str:
    # Light rhyme-ish pairings for child-facing cadence.
    return a.rstrip(" .,!?:;") + " " + b.rstrip(" .,!?:;") + "!"

def sound_line(sound: str) -> str:
    return f"{sound.capitalize()} went the clue in the blue sea breeze."

def is_plausible(setting: str, mystery: str) -> bool:
    return setting in MYSTERIES[mystery].setting_tags

def explain_rejection(setting: str, mystery: str) -> str:
    return f"(No story: {MYSTERIES[mystery].label} does not fit {SETTINGS[setting].place}.)"


# ---------------------------------------------------------------------------
# Simulated beats
# ---------------------------------------------------------------------------
def tell(setting: Setting, mystery: Mystery, name: str, gender: str, title: str, helper: str) -> World:
    world = World(setting)

    hero = world.add(Entity(id=name, kind="character", type=gender, label=title))
    ally = world.add(Entity(id=helper, kind="character", type="helper", label=helper))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=mystery.clue, phrase=mystery.clue, hidden=True))
    item = world.add(Entity(id="item", kind="thing", type="thing", label=mystery.label, phrase=mystery.phrase, hidden=True))

    world.facts.update(hero=hero, ally=ally, clue=clue, item=item, mystery=mystery, setting=setting)

    world.say(
        f"At {setting.place}, a commodore named {hero.id} kept watch in the salt-bright day."
    )
    world.say(
        f"{hero.id} had {title} eyes and a {helper}-small smile, and {hero.pronoun().capitalize()} liked neat decks and tidy bays."
    )
    world.say(
        f"Then came the sound: '{mystery.sound}!' '{mystery.sound}!' like a tiny tune in a spoon."
    )

    world.para()
    hero.memes["curiosity"] = 1
    hero.memes["worry"] = 1
    world.say(
        f"{hero.id} frowned and listened long. '{mystery.sound}?' {hero.pronoun().capitalize()} said, 'That sound won't belong!'"
    )
    world.say(sound_line(mystery.sound))
    world.say(
        f"{helper.capitalize()} pointed to {mystery.clue}, and the clue looked sly in the light."
    )

    world.para()
    hero.meters["search"] = 1
    world.say(
        f"So {hero.id} took {TOOLS['lantern'] if mystery.solve_tool == 'a lantern' else TOOLS['magnifier'] if mystery.solve_tool == 'a magnifying glass' else TOOLS['needle']} and shone, pried, and peered."
    )
    world.say(
        f"{hero.id} followed the clue with care, step by step near the pier."
    )

    if mystery.id == "missing_bell":
        world.say("Clink-clank, went the rope, and the net gave a little shake.")
        world.say("Snip-snap, went the seaweed as the lantern made the shadows break.")
    elif mystery.id == "stolen_whistle":
        world.say("Tweet-twirl, went the crumbs as the magnifier looked near.")
        world.say("Peer-gleam, went the glass, and the crate looked clear and dear.")
    else:
        world.say("Thump-thump, went the sack from a sleepy, bumpy nook.")
        world.say("Prick-pick, went the needle, and the sailcloth gave a look.")

    world.para()
    item.hidden = False
    item.found = True
    clue.hidden = False
    world.say(
        f"At last {hero.id} found {mystery.phrase}; {mystery.reveal}."
    )
    hero.memes["joy"] = 1
    hero.memes["worry"] = 0
    world.say(
        f"'Oh!' said {hero.id}. 'A mystery solved is a happy road.'"
    )
    world.say(
        f"{helper.capitalize()} laughed, and the harbor hummed like a kindly toad."
    )
    world.say(
        f"So the day went bright, and {hero.id} stood proud and grand, "
        f"with {mystery.label} safe and sound again in hand."
    )

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f"Write a rhyming mystery story for little kids about Commodore {hero.id} and {mystery.label}.",
        f"Tell a short, child-friendly story where a commodore hears '{mystery.sound}' and solves a mystery.",
        f"Write a gentle rhyming tale with sound effects, a clue, and a happy ending at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    setting = f["setting"]
    ally = f["ally"]
    return [
        QAItem(
            question=f"Who was the commodore in the story?",
            answer=f"The commodore was {hero.id}, who watched over {setting.place}.",
        ),
        QAItem(
            question=f"What mystery did {hero.id} need to solve?",
            answer=f"{hero.id} needed to solve {mystery.label}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} notice the clue?",
            answer=f"{ally.id} helped point out the clue and stay close during the search.",
        ),
        QAItem(
            question=f"What sound kept coming back during the search?",
            answer=f"The sound was '{mystery.sound}', and it helped guide the search.",
        ),
        QAItem(
            question=f"What was the clue?",
            answer=f"The clue was {mystery.clue}.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"It ended with {mystery.reveal}, and the lost thing was found again.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What does a lantern do?",
        answer="A lantern gives light in dark places so people can look for things more safely.",
    ),
    QAItem(
        question="What is a magnifying glass for?",
        answer="A magnifying glass makes small things look bigger so they are easier to see.",
    ),
    QAItem(
        question="What is a clue?",
        answer="A clue is a little piece of information that helps solve a mystery.",
    ),
    QAItem(
        question="Why do sound effects matter in stories?",
        answer="Sound effects help listeners imagine what the characters hear and feel.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is valid for a setting when the setting supports it.
valid_story(S, M) :- setting(S), mystery(M), allowed_in(M, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for st in sorted(m.setting_tags):
            lines.append(asp.fact("allowed_in", mid, st))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((s, m) for s in SETTINGS for m in MYSTERIES if is_plausible(s, m))
    cl = asp_valid_combos()
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py != cl:
        print("python:", py)
        print("clingo:", cl)
    return 1


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def generation_pool() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES if is_plausible(s, m)]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mystery and not is_plausible(args.place, args.mystery):
        raise StoryError(explain_rejection(args.place, args.mystery))

    combos = [c for c in generation_pool()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    title = args.title or rng.choice(TRAITS)
    helper = args.helper or rng.choice(["Matey", "Pip", "Bree", "Sailor Sam"])
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, title=title, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], params.name, params.gender, params.title, params.helper)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.found:
            bits.append("found=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="harbor", mystery="missing_bell", name="Nina", gender="girl", title="brave", helper="Matey"),
    StoryParams(place="dock", mystery="stolen_whistle", name="Theo", gender="boy", title="curious", helper="Pip"),
    StoryParams(place="ship", mystery="muffled_drum", name="Milo", gender="boy", title="cheery", helper="Bree"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming commodore mystery storyworld with sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--title", choices=TRAITS)
    ap.add_argument("--helper")
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
        for setting, mystery in combos:
            print(f"{setting} {mystery}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base = args.seed if args.seed is not None else random.randrange(2 ** 31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            i += 1
            rng = random.Random(base + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
