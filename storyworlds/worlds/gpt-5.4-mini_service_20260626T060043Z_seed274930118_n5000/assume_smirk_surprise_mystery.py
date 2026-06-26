#!/usr/bin/env python3
"""
A standalone storyworld for a small mystery tale built from the seed words
"assume" and "smirk", with a surprise turn and a gentle child-facing reveal.

The world centers on a simple mistaken assumption: a child thinks a favorite
object is missing, follows clues with a smirk and a worried friend, and then
finds a surprise that changes what they believed.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    location: str = ""
    hidden: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the library nook"
    details: str = "a small reading corner"
    supports: set[str] = field(default_factory=lambda: {"search", "hide", "find"})


@dataclass
class Clue:
    label: str
    phrase: str
    hint: str
    location: str


@dataclass
class StoryParams:
    place: str
    clue: str
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "library": Setting(place="the library nook", details="a tiny reading corner"),
    "kitchen": Setting(place="the kitchen table", details="a sunny table by the window"),
    "garden": Setting(place="the garden shed", details="a narrow shed with dusty shelves"),
}

CLUES = {
    "book": Clue(
        label="storybook",
        phrase="a red storybook with a ribbon",
        hint="pages",
        location="under the cushion",
    ),
    "key": Clue(
        label="key",
        phrase="a tiny brass key",
        hint="metal",
        location="in the teacup",
    ),
    "treat": Clue(
        label="treat",
        phrase="a wrapped honey cookie",
        hint="sweet crumbs",
        location="inside the jar",
    ),
    "note": Clue(
        label="note",
        phrase="a folded note with blue ink",
        hint="paper",
        location="behind the lamp",
    ),
}

SETTING_BY_PLACE = {
    "library": SETTINGS["library"],
    "kitchen": SETTINGS["kitchen"],
    "garden": SETTINGS["garden"],
}

HERO_NAMES = ["Mina", "Toby", "Nora", "Eli", "Pia", "Owen", "Lila", "Noah"]
COMPANION_NAMES = ["June", "Arlo", "Mara", "Finn", "Bea", "Otis", "Ivy", "Theo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
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


def reasonableness_gate(setting: Setting, clue: Clue) -> bool:
    return "search" in setting.supports and clue.location


def explain_rejection(setting: Setting, clue: Clue) -> str:
    return f"(No story: {setting.place} does not support a believable search for {clue.label}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    clue_id = args.clue or rng.choice(list(CLUES))
    setting = SETTINGS[place]
    clue = CLUES[clue_id]
    if not reasonableness_gate(setting, clue):
        raise StoryError(explain_rejection(setting, clue))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    companion_gender = args.companion_gender or ("boy" if gender == "girl" else "girl")
    companion = args.companion or rng.choice(COMPANION_NAMES)
    return StoryParams(
        place=place,
        clue=clue_id,
        hero_name=name,
        hero_type=gender,
        companion_name=companion,
        companion_type=companion_gender,
    )


def setup_world(params: StoryParams) -> World:
    world = World(SETTING_BY_PLACE[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    companion = world.add(Entity(id="companion", kind="character", type=params.companion_type, label=params.companion_name))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type=params.clue,
        label=CLUES[params.clue].label,
        phrase=CLUES[params.clue].phrase,
        owner=hero.id,
        location=CLUES[params.clue].location,
        hidden=True,
        found=False,
    ))
    helper = world.add(Entity(id="helper", kind="thing", type="basket", label="small basket", phrase="a small basket"))
    world.facts.update(hero=hero, companion=companion, clue=clue, helper=helper, clue_cfg=CLUES[params.clue], setting=world.setting)
    return world


def search_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    companion: Entity = world.facts["companion"]
    clue: Entity = world.facts["clue"]
    clue_cfg: Clue = world.facts["clue_cfg"]
    setting: Setting = world.setting

    hero.memes["curiosity"] = 1
    hero.memes["assumption"] = 1
    world.say(f"{hero.label} was a curious child who loved noticing little details at {setting.place}.")
    world.say(f"{hero.label} assumed {clue.label} was missing, because the shelf looked too neat.")
    world.say(f"{companion.label} gave a small smirk and said there might be a better place to look.")
    world.para()
    hero.memes["worry"] = 1
    world.say(f"They searched {setting.details}, peeking behind soft things and under quiet corners.")
    world.say(f"{hero.label} kept following the {clue_cfg.hint}, hoping the clue would finally make sense.")
    if clue.location == "under the cushion":
        world.say("Then a cushion tipped, and something flashed bright red beneath it.")
    elif clue.location == "in the teacup":
        world.say("Then a teacup rattled, and something tiny clinked inside.")
    elif clue.location == "inside the jar":
        world.say("Then a jar lid clicked, and something sweet peeped from inside.")
    else:
        world.say("Then the lamp moved, and something folded was hiding behind it.")
    clue.hidden = False
    clue.found = True
    hero.memes["surprise"] = 1
    hero.memes["joy"] = 1
    world.para()
    world.say(f"{hero.label} blinked in surprise: the {clue.label} had not been lost at all.")
    world.say(f"It had only been tucked away, waiting for the right pair of eyes to find it.")
    world.say(f"{hero.label} laughed, and {companion.label} smiled again, this time without hiding the smirk.")
    world.say(f"By the end, the little mystery was solved, and the {clue.label} was safe back in {hero.label}'s hands.")


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    search_story(world)
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
    hero = f["hero"]
    clue_cfg = f["clue_cfg"]
    return [
        f"Write a short mystery story for a young child about {hero.label} and a missing {clue_cfg.label}.",
        f"Tell a gentle story where someone assumes something is lost, but a smirk and a surprise help solve the puzzle.",
        f"Write a simple child-friendly mystery with the words assume and smirk, ending with a happy surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    clue = f["clue"]
    clue_cfg = f["clue_cfg"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Why did {hero.label} think the {clue.label} was gone?",
            answer=f"{hero.label} assumed it was missing because the place looked too neat at {setting.place}.",
        ),
        QAItem(
            question=f"What did {companion.label} do when {hero.label} worried?",
            answer=f"{companion.label} gave a smirk and suggested looking carefully in a better place.",
        ),
        QAItem(
            question=f"Where was the {clue.label} hiding?",
            answer=f"It was hiding {clue.location}, which matched the clue about {clue_cfg.hint}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The mystery ended with a surprise, because the {clue.label} was found and {hero.label} felt happy again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to assume something?",
            answer="To assume means to think something is true before you check carefully.",
        ),
        QAItem(
            question="What is a smirk?",
            answer="A smirk is a small, sly smile that can show someone has a secret or a playful idea.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you did not expect, so it makes you feel suddenly startled or delighted.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append("hidden=True")
        if e.found:
            bits.append("found=True")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(hero).
companion(companion).

assume_state(X) :- assumption(X).
smirk_state(X) :- smirk(X).
surprise_state(X) :- surprise(X).

found(X) :- hidden(X), search(X), clue_place(X, _).
mystery_solved(X) :- found(X), surprise(X).

#show found/1.
#show mystery_solved/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_place", cid, clue.location))
    lines.append(asp.fact("assumption", "hero"))
    lines.append(asp.fact("smirk", "companion"))
    lines.append(asp.fact("surprise", "hero"))
    lines.append(asp.fact("search", "hero"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set((sym.name, tuple(a.name if a.type != a.type.Number and a.type != a.type.String else (a.number if a.type == a.type.Number else a.string) for a in sym.arguments)) for sym in model)
    if ("found", ("hero",)) in atoms and ("mystery_solved", ("hero",)) in atoms:
        print("OK: ASP twin produces the expected mystery outcome.")
        return 0
    print("Mismatch in ASP twin.")
    return 1


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "mystery_solved")))


CURATED = [
    StoryParams(place="library", clue="book", hero_name="Mina", hero_type="girl", companion_name="June", companion_type="girl"),
    StoryParams(place="kitchen", clue="key", hero_name="Toby", hero_type="boy", companion_name="Arlo", companion_type="boy"),
    StoryParams(place="garden", clue="note", hero_name="Lila", hero_type="girl", companion_name="Finn", companion_type="boy"),
    StoryParams(place="library", clue="treat", hero_name="Noah", hero_type="boy", companion_name="Ivy", companion_type="girl"),
]


def build_story_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Invalid place.")
    if args.clue and args.clue not in CLUES:
        raise StoryError("Invalid clue.")
    return resolve_params(args, rng)


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid())
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
            header = f"### {p.hero_name}: mystery at {p.place} ({p.clue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
