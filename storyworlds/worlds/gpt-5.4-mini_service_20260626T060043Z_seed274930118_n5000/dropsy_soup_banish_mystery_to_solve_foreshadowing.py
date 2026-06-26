#!/usr/bin/env python3
"""
storyworlds/worlds/dropsy_soup_banish_mystery_to_solve_foreshadowing.py
=======================================================================

A small comedy storyworld about a puzzling bowl of soup, a suspect named Dropsy,
and a banishment plan that turns out to be the wrong answer.

Premise:
- Someone in a tiny household keeps finding soup where it should not be.
- The household worries about a mystery.
- Little clues foreshadow the answer.

Turn:
- The family blames the wrong creature/person and tries to banish it.

Resolution:
- A careful look solves the mystery, and the real cause is funny rather than grim.

This file is standalone and uses only the standard library plus the shared
storyworlds/results.py helpers. ASP support is inline and imported lazily.
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


# ---------------------------------------------------------------------------
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    text: str
    foreshadow: str


@dataclass
class Mystery:
    id: str
    question: str
    false_suspect: str
    true_cause: str
    evidence: str
    solved_by: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    suspect: str
    hero_name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.clues: list[str] = []

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"soup"}),
    "pantry": Setting(place="the pantry", affords={"soup"}),
    "dining_room": Setting(place="the dining room", affords={"soup"}),
}

MYSTERIES = {
    "missing_ladle": Mystery(
        id="missing_ladle",
        question="Who keeps moving the soup ladle?",
        false_suspect="Dropsy",
        true_cause="the wind from the open window",
        evidence="the ladle is light enough to wobble and slide",
        solved_by="closing the window",
    ),
    "soup_slosh": Mystery(
        id="soup_slosh",
        question="Why is there soup on the floor?",
        false_suspect="Dropsy",
        true_cause="a bumped tray",
        evidence="the tray has a tiny tilt mark",
        solved_by="placing the tray flat",
    ),
    "spoon_tune": Mystery(
        id="spoon_tune",
        question="Who makes the spoon tap-tap song at night?",
        false_suspect="Dropsy",
        true_cause="the cat's tail",
        evidence="the spoon only sings when the cat passes by",
        solved_by="moving the spoon away from the shelf edge",
    ),
}

SUSPECTS = {
    "dropsy": Entity(id="Dropsy", kind="character", label="Dropsy", type="cat", plural=False),
    "teacup": Entity(id="Teacup", kind="character", label="Teacup", type="cat", plural=False),
    "muffin": Entity(id="Muffin", kind="character", label="Muffin", type="dog", plural=False),
}

CLUES = {
    "missing_ladle": [
        Clue("The ladle had a tiny scrape on its handle.", "It might have slid by itself."),
        Clue("The window was open, and the curtain was doing a silly dance.", "Something breezy was nearby."),
    ],
    "soup_slosh": [
        Clue("A wet trail led away from the tray.", "Something had tipped, not vanished."),
        Clue("The soup bowl wore a lopsided little grin of a tilt.", "It had not stayed level."),
    ],
    "spoon_tune": [
        Clue("The spoon tapped only when the cat marched past.", "A tail could have nudged it."),
        Clue("Dropsy was napping in a box and looked deeply innocent.", "The mystery had a different culprit."),
    ],
}

# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, helper: Entity, mystery: Mystery, suspect: Entity) -> None:
    world.say(
        f"In {world.setting.place}, {hero.id} was a curious {hero.type} who loved a tidy kitchen and a good laugh."
    )
    world.say(
        f"{hero.pronoun().capitalize()} and {helper.id} found a puzzling question: {mystery.question}"
    )
    world.say(
        f"At first, everyone pointed at {suspect.label}, because {suspect.label} looked suspicious in a very round way."
    )


def foreshadow(world: World, mystery: Mystery) -> None:
    for clue in CLUES[mystery.id]:
        world.say(clue.text)
        world.clues.append(clue.foreshadow)


def blame_and_banish(world: World, suspect: Entity) -> None:
    suspect.memes["blame"] = suspect.memes.get("blame", 0) + 1
    world.say(
        f"Someone even tried to banish {suspect.label} from the kitchen, which made {suspect.id} look offended and fluffy."
    )
    world.say(
        f"But {suspect.id} only blinked and sat on a chair like a tiny expert in not doing anything at all."
    )


def solve(world: World, hero: Entity, helper: Entity, mystery: Mystery, suspect: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    helper.memes["attention"] = helper.memes.get("attention", 0) + 1
    world.say(
        f"{hero.id} looked again and noticed the clue that mattered: {mystery.evidence}."
    )
    world.say(
        f"That was the funny answer. The real trouble was {mystery.true_cause}, not {suspect.label}."
    )
    world.say(
        f"So the family did not banish anyone. They simply used {mystery.solved_by}, and the kitchen felt clever instead of grumpy."
    )
    world.say(
        f"In the end, {suspect.label} got a sniff of soup, the mystery was solved, and everybody had a laugh at their own detective hats."
    )


def tell(setting: Setting, mystery: Mystery, suspect: Entity, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", label=hero_name, type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", label="Aunt Dot", type=helper_type))
    world.add(suspect)

    intro(world, hero, helper, mystery, suspect)
    world.para()
    foreshadow(world, mystery)
    world.say("The clues were small, but they waved their arms like tiny flags.")
    world.para()
    blame_and_banish(world, suspect)
    world.para()
    solve(world, hero, helper, mystery, suspect)

    world.facts.update(
        hero=hero,
        helper=helper,
        suspect=suspect,
        mystery=mystery,
        setting=setting,
        solved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Quality gates and parameter resolution
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            for sus in SUSPECTS:
                combos.append((sid, mid, sus))
    return combos


def explain_rejection() -> str:
    return "(No story: this world needs a setting, a mystery, and a suspect.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comedy mystery world about soup, dropsy, and a banishment that fails."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "cat", "dog"], dest="hero_type")
    ap.add_argument("--helper-type", choices=["woman", "man", "cat", "dog"], dest="helper_type")
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
    if args.setting and args.mystery and args.suspect:
        pass
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    suspect = args.suspect or "dropsy"
    if suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    if suspect != "dropsy":
        # Story premise requires Dropsy to be the false suspect, to keep the comedy shape.
        raise StoryError("(No story: this domain uses Dropsy as the comic false suspect.)")
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["woman", "man"])
    name = args.name or rng.choice(["Mina", "Jo", "Pip", "Toby", "Lena", "Bram"])
    return StoryParams(
        setting=setting,
        mystery=mystery,
        suspect=suspect,
        hero_name=name,
        hero_type=hero_type,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        SUSPECTS[params.suspect],
        params.hero_name,
        params.hero_type,
        params.helper_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short comedy mystery for children set in {f['setting'].place} about soup and a false suspect named Dropsy.",
        f"Tell a playful story where {f['hero'].id} notices clues, worries about {f['suspect'].label}, and solves a soup mystery.",
        f"Write a foreshadowing-heavy tiny story about a household clue, a wrong banishment idea, and a funny solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    suspect = f["suspect"]
    mystery = f["mystery"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What mystery were {hero.id} and {helper.id} trying to solve?",
            answer=f"They were trying to solve this mystery: {mystery.question}",
        ),
        QAItem(
            question=f"Who did everyone first blame before the clues were checked carefully?",
            answer=f"Everyone first blamed {suspect.label}, but that was the wrong answer.",
        ),
        QAItem(
            question="What kind of ending did the story have?",
            answer="It had a funny ending where the family solved the mystery and did not banish the innocent suspect.",
        ),
        QAItem(
            question=f"What was the real cause of the problem?",
            answer=f"The real cause was {mystery.true_cause}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives small clues early so a reader can guess what may happen later.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to figure out the real answer after looking at the clues.",
        ),
        QAItem(
            question="Why can soup be funny in a story?",
            answer="Soup can be funny because it can spill, slosh, or make a silly mess that people have to fix.",
        ),
    ]


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
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  clues: {world.clues}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(kitchen).
setting(pantry).
setting(dining_room).

mystery(missing_ladle).
mystery(soup_slosh).
mystery(spoon_tune).

suspect(dropsy).
false_suspect(missing_ladle,dropsy).
false_suspect(soup_slosh,dropsy).
false_suspect(spoon_tune,dropsy).

can_settle(missing_ladle,close_window).
can_settle(soup_slosh,place_tray_flat).
can_settle(spoon_tune,move_spoon).

valid_story(S, M, X) :- setting(S), mystery(M), suspect(X), false_suspect(M, X).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    lines.append(asp.fact("suspect", "dropsy"))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("false_suspect", mid, "dropsy"))
        lines.append(asp.fact("can_settle", mid, m.solved_by.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
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
    StoryParams(setting="kitchen", mystery="missing_ladle", suspect="dropsy", hero_name="Mina", hero_type="girl", helper_type="woman"),
    StoryParams(setting="pantry", mystery="soup_slosh", suspect="dropsy", hero_name="Toby", hero_type="boy", helper_type="man"),
    StoryParams(setting="dining_room", mystery="spoon_tune", suspect="dropsy", hero_name="Lena", hero_type="girl", helper_type="woman"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/3."))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
