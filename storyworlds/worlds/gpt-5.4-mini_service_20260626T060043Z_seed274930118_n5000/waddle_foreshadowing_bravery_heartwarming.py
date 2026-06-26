#!/usr/bin/env python3
"""
storyworlds/worlds/waddle_foreshadowing_bravery_heartwarming.py
================================================================

A small, self-contained storyworld about a little waddling animal who notices
small clues, finds the courage to keep going, and ends up in a warm, safe,
heartwarming place.

Premise:
- A child-facing protagonist wants to waddle to a cozy destination.
- Foreshadowing matters: the world reveals tiny hints before the harder moment.
- Bravery matters: the protagonist chooses to keep going with a helper.

This world is intentionally narrow: a few plausible variants, each with a clear
beginning, turn, and ending image.
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False
    cozy: str = ""


@dataclass
class Path:
    id: str
    label: str
    verb: str
    gerund: str
    clue: str
    risk: str
    weather: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    action: str
    gift: str
    covers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

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


@dataclass
class StoryParams:
    place: str
    path: str
    helper: str
    hero_name: str
    hero_type: str
    caretaker_type: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "pond": Setting(place="the pond", indoors=False, cozy="soft reeds and a warm bank"),
    "barn": Setting(place="the little barn", indoors=True, cozy="a hay nest and a lantern glow"),
    "garden": Setting(place="the garden path", indoors=False, cozy="a flower bed and a sunny porch"),
}

PATHS = {
    "puddle": Path(
        id="puddle",
        label="a little puddle",
        verb="waddle around the puddle",
        gerund="waddling around puddles",
        clue="the ground looked shiny and wet",
        risk="a slippery splash",
        weather="drizzly",
        tags={"water", "wet", "foreshadowing"},
    ),
    "hill": Path(
        id="hill",
        label="a small hill",
        verb="waddle up the hill",
        gerund="waddling up hills",
        clue="the hill had a steep side and tiny pebbles",
        risk="a shaky climb",
        weather="breezy",
        tags={"hill", "foreshadowing", "bravery"},
    ),
    "gate": Path(
        id="gate",
        label="the garden gate",
        verb="waddle through the gate",
        gerund="waddling through gates",
        clue="the gate was half open and softly creaked",
        risk="a scary narrow squeeze",
        weather="quiet",
        tags={"gate", "foreshadowing", "bravery"},
    ),
}

HELPERS = {
    "scarf": Helper(
        id="scarf",
        label="a tiny scarf",
        action="wrapped it around the little neck",
        gift="warm and steady",
        covers={"neck"},
        tags={"warm", "cozy"},
    ),
    "lantern": Helper(
        id="lantern",
        label="a small lantern",
        action="held it up so the path looked less dark",
        gift="a brave little glow",
        covers={"eyes"},
        tags={"light", "bravery"},
    ),
    "boots": Helper(
        id="boots",
        label="soft boots",
        action="slid them onto the little feet",
        gift="dry and safe",
        covers={"feet"},
        tags={"safe", "water"},
    ),
}

HERO_TYPES = ["duckling", "penguin", "gosling"]
CARETAKERS = ["mother", "father", "grandparent"]
TRAITS = ["tiny", "gentle", "shy", "curious", "brave"]


def path_at_risk(path: Path) -> bool:
    return True


def select_helper(path: Path) -> Optional[Helper]:
    if path.id == "puddle":
        return HELPERS["boots"]
    if path.id == "hill":
        return HELPERS["lantern"]
    if path.id == "gate":
        return HELPERS["scarf"]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for path in PATHS:
            if select_helper(PATHS[path]) is not None:
                combos.append((place, path, next(iter(HELPERS.keys()))))
    return combos


def foreshadow(world: World, hero: Entity, path: Path) -> None:
    if path.id == "puddle":
        world.say(f"Before anything else, {path.clue}, and that made {hero.id} slow down and look carefully.")
    elif path.id == "hill":
        world.say(f"Before the climb, {path.clue}, like the path was whispering that the brave part would come next.")
    else:
        world.say(f"Before the gate, {path.clue}, and {hero.id} noticed it might take a deep breath to go on.")


def brave_choice(world: World, hero: Entity, caretaker: Entity, path: Path, helper: Helper) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    world.say(
        f"{hero.id} took a small breath, {path.verb}, and kept going even though {path.risk} waited ahead."
    )
    world.say(
        f"Then {caretaker.id} {helper.action}, and that made {hero.pronoun('subject')} feel less alone."
    )


def resolve(world: World, hero: Entity, caretaker: Entity, path: Path, helper: Helper) -> None:
    world.say(
        f"At the end, {hero.id} made it to {world.setting.place} with {helper.label}, feeling {helper.gift}."
    )
    world.say(
        f"{caretaker.id} smiled, because {hero.id}'s brave little waddle had carried {hero.pronoun('object')} all the way through."
    )


def tell(setting: Setting, path: Path, helper: Helper, hero_name: str, hero_type: str,
         caretaker_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", trait],
        meters={"distance": 0.0},
        memes={"curiosity": 1.0, "bravery": 0.0},
    ))
    caretaker = world.add(Entity(
        id="Caretaker",
        kind="character",
        type=caretaker_type,
        label="the caretaker",
        memes={"love": 1.0},
    ))
    world.facts.update(hero=hero, caretaker=caretaker, path=path, helper=helper)

    world.say(f"{hero.id} was a little {trait} {hero.type} who loved to waddle.")
    world.say(f"{caretaker.label if caretaker.label else caretaker.id} stayed close, ready with a kind smile.")
    world.para()
    foreshadow(world, hero, path)
    world.say(f"{hero.id} wanted to {path.verb}, because {path.clue} looked interesting and not too scary.")
    world.para()
    brave_choice(world, hero, caretaker, path, helper)
    resolve(world, hero, caretaker, path, helper)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    path = f["path"]
    return [
        f'Write a heartwarming story for a young child about {hero.id} who loves to waddle and notices a small clue before being brave.',
        f"Tell a gentle story where a {hero.type} named {hero.id} sees {path.clue} and keeps going with help.",
        f'Write a short story that includes the word "waddle", a foreshadowing clue, and a brave ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    caretaker = f["caretaker"]
    path = f["path"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What kind of animal was {hero.id}?",
            answer=f"{hero.id} was a little {hero.type} who loved to waddle.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice before the brave part?",
            answer=f"{hero.id} noticed that {path.clue}. That was a little foreshadowing clue before the harder moment.",
        ),
        QAItem(
            question=f"How did {helper.label} help {hero.id} stay brave?",
            answer=f"{caretaker.id} used {helper.label} to help, and that made {hero.id} feel steadier and less afraid while going on.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{hero.id} reached {world.setting.place} safely, and the brave little waddle ended with a warm, happy feeling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to waddle?",
            answer="To waddle is to walk with small steps that sway a little from side to side.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small clue that hints something important may happen later.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something even when you feel nervous or scared.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
path_valid(P) :- path(P).
helper_for(puddle,boots).
helper_for(hill,lantern).
helper_for(gate,scarf).
valid_story(Place,Path,Helper) :- setting(Place), path(Path), helper_for(Path,Helper).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PATHS:
        lines.append(asp.fact("path", p))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    python_set = set((place, path, helper) for place, path, helper in valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if clingo_set - python_set:
        print("  only in ASP:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in Python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming waddle storyworld with foreshadowing and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--caretaker-type", choices=CARETAKERS)
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
    choices = []
    for place in SETTINGS:
        if args.place and args.place != place:
            continue
        for path in PATHS:
            if args.path and args.path != path:
                continue
            if select_helper(PATHS[path]) is None:
                continue
            choices.append((place, path))
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, path = rng.choice(choices)
    helper = args.helper or select_helper(PATHS[path]).id
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    caretaker_type = args.caretaker_type or rng.choice(CARETAKERS)
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice(["Pip", "Milo", "Lulu", "Nina", "Toby"])
    return StoryParams(
        place=place,
        path=path,
        helper=helper,
        hero_name=name,
        hero_type=hero_type,
        caretaker_type=caretaker_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        PATHS[params.path],
        HELPERS[params.helper],
        params.hero_name,
        params.hero_type,
        params.caretaker_type,
        params.trait,
    )
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
    StoryParams(place="pond", path="puddle", helper="boots", hero_name="Pip", hero_type="duckling", caretaker_type="mother", trait="shy"),
    StoryParams(place="barn", path="hill", helper="lantern", hero_name="Milo", hero_type="penguin", caretaker_type="father", trait="curious"),
    StoryParams(place="garden", path="gate", helper="scarf", hero_name="Lulu", hero_type="gosling", caretaker_type="grandparent", trait="gentle"),
]


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
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for place, path, helper in combos:
            print(f"{place:8} {path:8} {helper}")
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.hero_name}: {p.path} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
