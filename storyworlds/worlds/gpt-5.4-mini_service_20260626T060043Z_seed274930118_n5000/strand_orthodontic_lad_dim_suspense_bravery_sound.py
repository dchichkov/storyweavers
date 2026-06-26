#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/strand_orthodontic_lad_dim_suspense_bravery_sound.py
=============================================================================================================

A tiny detective-story world with a dim orthodontic office, a brave lad,
and a suspenseful strand-shaped clue that can only be solved by listening
carefully to the sounds in the room.

The seed words guide the premise:
- strand
- orthodontic
- lad-dim

Story shape:
- Beginning: a small detective setup in a dim clinic
- Middle: suspense grows from sounds and shadows
- Turn: the lad acts bravely and follows the clue
- Ending: the mystery is resolved with a concrete, changed state

This script is self-contained and uses only the standard library for story
generation. ASP support is optional and imported lazily.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "lad", "man", "father", "dad", "detective"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    dim: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    hidden_in: str
    sound: str
    reveal: str
    suspicious_by: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    use: str
    helps_with: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.shadows: int = 0

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.shadows = self.shadows
        return clone


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "orthodontic_clinic": Setting(
        place="the orthodontic clinic",
        dim=True,
        affords={"search", "listen", "inspect"},
    ),
    "waiting_room": Setting(
        place="the waiting room",
        dim=True,
        affords={"search", "listen"},
    ),
    "hallway": Setting(
        place="the hallway outside the orthodontic room",
        dim=True,
        affords={"search", "listen", "inspect"},
    ),
}

MYSTERIES = {
    "strand": Mystery(
        id="strand",
        clue="a tiny silver strand",
        hidden_in="retainer",
        sound="a soft cling-clink",
        reveal="stuck on the retainer wire",
        suspicious_by={"dim", "orthodontic", "sound"},
    ),
    "orthodontic": Mystery(
        id="orthodontic",
        clue="a crooked orthodontic note",
        hidden_in="chart",
        sound="a paper rustle and a tiny tap",
        reveal="slipped behind the clipboard",
        suspicious_by={"dim", "sound"},
    ),
    "lad_dim": Mystery(
        id="lad_dim",
        clue="a dim little flashlight strand",
        hidden_in="bench",
        sound="a weak buzz and a click",
        reveal="resting under the bench seat",
        suspicious_by={"dim", "bravery", "sound"},
    ),
}

TOOLS = {
    "flashlight": Tool(id="flashlight", label="a flashlight", use="shine", helps_with={"dim", "strand", "lad_dim"}),
    "mirror": Tool(id="mirror", label="a tiny mirror", use="peek", helps_with={"orthodontic", "strand"}),
    "pincers": Tool(id="pincers", label="a pair of careful pincers", use="lift", helps_with={"strand"}),
}

NAMES = ["Theo", "Milo", "Eli", "Noah", "Ben", "Finn"]
TRAITS = ["curious", "brave", "quiet", "quick-thinking", "steady"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for myst_id, myst in MYSTERIES.items():
            if setting.dim and "dim" in myst.suspicious_by:
                out.append((place, myst_id))
    return out


def reason_rejection(setting: Setting, mystery: Mystery) -> str:
    return (
        f"(No story: this mystery needs a dim, suspenseful space, but {setting.place} "
        f"does not fit that setup.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective-style storyworld: a brave lad, a dim orthodontic room, and a strand-sized mystery."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
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
    if args.place and args.mystery:
        setting = SETTINGS[args.place]
        mystery = MYSTERIES[args.mystery]
        if not (setting.dim and "dim" in mystery.suspicious_by):
            raise StoryError(reason_rejection(setting, mystery))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.mystery is None or c[1] == args.mystery)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, trait=trait)


def _suspense(world: World, hero: Entity, myst: Mystery) -> None:
    hero.memes["suspense"] = hero.memes.get("suspense", 0) + 1
    world.shadows += 1
    world.say(
        f"The room felt dim, and {hero.id} noticed a {myst.sound} coming from the shadowy chair."
    )
    world.say(
        f"{hero.pronoun().capitalize()} listened like a detective, because even a small sound can point to a clue."
    )


def _brave_search(world: World, hero: Entity, tool: Entity, myst: Mystery) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    hero.meters["search"] = hero.meters.get("search", 0) + 1
    world.say(
        f"With {tool.label}, {hero.id} took a brave step closer and shone the beam under the bench."
    )
    world.say(
        f"The light made the shadows shrink, and the clue finally looked less scary."
    )
    if myst.id == "strand":
        world.facts["found"] = f"the {myst.clue}"
    elif myst.id == "orthodontic":
        world.facts["found"] = myst.clue
    else:
        world.facts["found"] = myst.clue


def _reveal(world: World, hero: Entity, myst: Mystery, tool: Entity) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.say(
        f"In the end, the mystery was simple: {myst.clue} was {myst.reveal}."
    )
    world.say(
        f"{hero.id} used {tool.label} to show the orthodontist, and the little clue was easy to pick up."
    )


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="lad", traits=["little", hero_trait, "brave"]))
    ortho = world.add(Entity(id="Orthodontist", kind="character", type="adult", label="the orthodontist"))
    tool = world.add(Entity(id="flashlight", type="tool", label="a flashlight"))
    clue = world.add(Entity(id=mystery.id, type="clue", label=mystery.clue, phrase=mystery.clue))
    world.facts["mystery"] = mystery
    world.facts["hero"] = hero
    world.facts["orthodontist"] = ortho
    world.facts["tool"] = tool
    world.facts["clue"] = clue

    world.say(
        f"{hero.id} was a little {hero_trait} lad who liked detective games, especially in {setting.place}."
    )
    world.say(
        f"The orthodontic room was dim, and that made every shiny corner feel important."
    )
    world.para()
    world.say(
        f"Then there came a soft sound: {mystery.sound}. {hero.id} stopped and frowned."
    )
    _suspense(world, hero, mystery)
    world.para()
    world.say(
        f"{hero.id} was brave enough to follow the sound instead of running away."
    )
    _brave_search(world, hero, tool, mystery)
    world.para()
    _reveal(world, hero, mystery, tool)
    world.say(
        f"After that, the room did not feel eerie anymore; it felt like a place where careful eyes and brave hearts could solve things."
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    myst = f["mystery"]
    return [
        f'Write a child-friendly detective story about a brave lad named {hero.id} in a dim orthodontic clinic.',
        f'Tell a suspenseful story where the sound "{myst.sound}" leads {hero.id} to a tiny clue.',
        f'Write a short detective tale that includes an orthodontic room, bravery, and the word "{myst.clue}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    myst = world.facts["mystery"]
    setting = world.setting.place
    return [
        QAItem(
            question=f"Where did {hero.id} look for the clue?",
            answer=f"{hero.id} looked in {setting}, where the dim light made the clue hard to see at first.",
        ),
        QAItem(
            question=f"What made the story feel suspenseful?",
            answer=f"The soft sound of {myst.sound} and the dim room made the story feel suspenseful.",
        ),
        QAItem(
            question=f"How did {hero.id} act when the clue seemed scary?",
            answer=f"{hero.id} acted bravely and moved closer instead of backing away.",
        ),
        QAItem(
            question=f"What was the mystery in the end?",
            answer=f"The mystery was that {myst.clue} was {myst.reveal}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a flashlight do?",
            answer="A flashlight shines a beam of light so people can see in dark or dim places.",
        ),
        QAItem(
            question="What is an orthodontist?",
            answer="An orthodontist is a tooth doctor who helps people with braces and other tools that straighten teeth.",
        ),
        QAItem(
            question="Why do detectives listen carefully?",
            answer="Detectives listen carefully because small sounds can give away a clue or a hidden thing.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  shadows={world.shadows}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="orthodontic_clinic", mystery="strand", name="Theo", trait="brave"),
    StoryParams(place="hallway", mystery="orthodontic", name="Milo", trait="quiet"),
    StoryParams(place="waiting_room", mystery="lad_dim", name="Eli", trait="quick-thinking"),
]


ASP_RULES = r"""
% A mystery works for this story when the place is dim and the clue is soundy.
fits(Place, Mystery) :- setting(Place), mystery(Mystery), dim_place(Place), suspicious(Mystery, dim).
fits(Place, Mystery) :- setting(Place), mystery(Mystery), dim_place(Place), suspicious(Mystery, sound).

% The story is valid when the detective can follow a clue in a fitting place.
valid_story(Place, Mystery) :- fits(Place, Mystery).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.dim:
            lines.append(asp.fact("dim_place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for tag in sorted(m.suspicious_by):
            lines.append(asp.fact("suspicious", mid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import itertools
    py = {(p, m) for p, m in valid_combos()}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], params.name, params.trait)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid combos:\n")
        for place, mystery in combos:
            print(f"  {place:22} {mystery}")
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
