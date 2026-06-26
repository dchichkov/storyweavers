#!/usr/bin/env python3
"""
A standalone storyworld for a tall-tale style elevator story:
a child wants to make a good impression, a farm-themed surprise rides the lift,
conflict builds in an inner monologue, and rhyme helps resolve the moment.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)   # physical
    memes: dict[str, float] = field(default_factory=dict)    # emotional

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "cowgirl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "cowboy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the elevator"
    level_names: list[str] = field(default_factory=lambda: ["lobby", "mid-floor", "top floor"])
    affords: set[str] = field(default_factory=lambda: {"ride", "wait", "talk"})


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    type: str = "thing"


@dataclass
class StoryParams:
    setting: str
    hero: str
    helper: str
    prop: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting()

HEROES = {
    "Mabel": {"type": "girl", "traits": ["bright", "bold"]},
    "Clem": {"type": "boy", "traits": ["lively", "wiry"]},
    "Ivy": {"type": "girl", "traits": ["curious", "quick"]},
    "Buck": {"type": "boy", "traits": ["stubborn", "good-hearted"]},
}

HELPERS = {
    "Gran": {"type": "woman", "traits": ["wise", "kind"]},
    "Dad": {"type": "man", "traits": ["steady", "patient"]},
    "Aunt Jo": {"type": "woman", "traits": ["cheerful", "sharp"]},
    "Uncle Ned": {"type": "man", "traits": ["calm", "funny"]},
}

PROPS = {
    "pitchfork": Prop(id="pitchfork", label="pitchfork", phrase="a shiny farm pitchfork"),
    "lantern": Prop(id="lantern", label="lantern", phrase="a little brass lantern"),
    "seed_sack": Prop(id="seed_sack", label="seed sack", phrase="a sack of bright seed"),
    "apple_crate": Prop(id="apple_crate", label="apple crate", phrase="a crate of red apples"),
}


# ---------------------------------------------------------------------------
# Reasonable story gate
# ---------------------------------------------------------------------------
def is_reasonable(params: StoryParams) -> bool:
    return params.setting == "elevator" and params.hero in HEROES and params.helper in HELPERS and params.prop in PROPS


def explain_rejection(params: StoryParams) -> str:
    return "No story: this world only supports a farm-flavored conflict in the elevator."


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def _rhyme(a: str, b: str) -> str:
    return f"{a.rstrip('.')} . {b.rstrip('.')}".replace(" . ", ". ")


def tell(params: StoryParams) -> World:
    world = World(SETTING)

    hero_cfg = HEROES[params.hero]
    helper_cfg = HELPERS[params.helper]
    prop = PROPS[params.prop]

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=hero_cfg["type"],
        traits=["little"] + hero_cfg["traits"],
        meters={"sweat": 0.0, "ride": 0.0},
        memes={"hope": 0.0, "nervous": 0.0, "conflict": 0.0, "relief": 0.0, "pride": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=helper_cfg["type"],
        traits=helper_cfg["traits"],
        meters={"ride": 0.0},
        memes={"smile": 0.0, "conflict": 0.0, "pride": 0.0},
    ))
    item = world.add(Entity(
        id=prop.id,
        type=prop.type,
        label=prop.label,
        owner=hero.id,
        meters={"shine": 1.0, "dust": 0.0},
    ))

    # Act 1: setup
    world.say(
        f"In the tallest little elevator by the farmyard, {hero.id} stood with {hero.pronoun('possessive')} "
        f"{item.label} and tried to look brave enough to make a fine impression."
    )
    world.say(
        f"{hero.id} wanted {helper.id} to see a neat, ready-for-work helper, not a jittery sack of knees."
    )
    hero.memes["hope"] += 1
    hero.memes["nervous"] += 1
    hero.meters["ride"] += 1

    # Inner monologue / tension
    world.para()
    world.say(
        f"Inside {hero.pronoun('possessive')} head, {hero.id} thought, "
        f"\"Keep your back straight, keep your grin bright, and do not let the old worry bite.\""
    )
    world.say(
        f"But when the elevator shivered between floors, {hero.id}'s heart began to pound like a bucket on a barn door."
    )
    hero.memes["conflict"] += 1
    helper.memes["conflict"] += 1

    # Conflict
    world.say(
        f"{helper.id} noticed the wobble and said, \"Hold steady, now. This lift has more gust than a rooster in a gale.\""
    )
    world.say(
        f"{hero.id} blurted, \"I wanted to make a grand impression!\" and nearly dropped {hero.pronoun('possessive')} {item.label}."
    )
    item.meters["dust"] += 1
    hero.meters["sweat"] += 1

    # Tall tale escalation
    world.para()
    world.say(
        f"The elevator gave one grand groan, as if the whole farm were leaning in to listen."
    )
    world.say(
        f"Up went the lift, up went the nerves, and the floor numbers ticked by like shy chickens."
    )

    # Resolution through rhyme
    world.say(
        f"Then {helper.id} laughed softly and said, "
        f"\"A true hand on a farm is not perfect and prim; a true hand is sturdy, cheerful, and trim.\""
    )
    world.say(
        f"{hero.id} answered with a rhyme of {hero.pronoun('possessive')} own: "
        f"\"If I shake like a leaf, I still can be keen; a kind heart shines best when the boots are not clean.\""
    )
    hero.memes["conflict"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    helper.memes["conflict"] = 0.0
    helper.memes["pride"] += 1

    world.say(
        f"By the time the doors slid open, {hero.id} was standing straighter, smiling wider, "
        f"and holding {item.label} like it was a banner for the whole farm."
    )
    world.say(
        f"{helper.id} said that the best impression was not fancy at all; it was brave, kind, and true."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        item=item,
        prop=prop,
        setting=params.setting,
        conflict=True,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    prop: Prop = f["prop"]
    return [
        f"Write a tall-tale story set in an elevator where {hero.id} wants to make a good impression with {prop.phrase}.",
        f"Tell a child-friendly story with inner monologue, conflict, and rhyme about {hero.id} and {helper.id} in the elevator.",
        f"Write a short farm-flavored elevator adventure where a worried child learns that a kind heart matters more than a perfect impression.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]

    return [
        QAItem(
            question=f"What did {hero.id} want to do in the elevator?",
            answer=f"{hero.id} wanted to make a good impression and look brave in the elevator while holding {hero.pronoun('possessive')} {item.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} think to {hero.pronoun('possessive')}self when the elevator shook?",
            answer=f"{hero.id} thought to stay straight, keep the grin bright, and not let the worry bite.",
        ),
        QAItem(
            question=f"How did {helper.id} help calm the conflict?",
            answer=f"{helper.id} joked about the wild elevator, then reminded {hero.id} that a true farm helper can be kind and steady, not perfect.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The doors opened, {hero.id} stood straighter, and {helper.id} said the best impression was brave, kind, and true.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an elevator?",
            answer="An elevator is a small moving room that carries people up and down between floors in a building.",
        ),
        QAItem(
            question="What is a farm?",
            answer="A farm is a place where people grow crops or raise animals and do lots of outdoor work.",
        ),
        QAItem(
            question="What is an impression?",
            answer="An impression is the feeling or idea someone gets about a person or thing after seeing it.",
        ),
        QAItem(
            question="Why can rhyme make a story fun?",
            answer="Rhyme makes words sound musical together, so a story can feel lively and memorable.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(elevator).
hero(mabel). hero(clem). hero(ivy). hero(buck).
helper(gran). helper(dad). helper(aunt_jo). helper(uncle_ned).
prop(pitchfork). prop(lantern). prop(seed_sack). prop(apple_crate).

reasonable(H, He, P) :- hero(H), helper(He), prop(P), setting(elevator).
#show reasonable/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("setting", "elevator")]
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for p in PROPS:
        lines.append(asp.fact("prop", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_count() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return len(asp.atoms(model, "reasonable"))


def asp_verify() -> int:
    py = len(HEROES) * len(HELPERS) * len(PROPS)
    cl = asp_reasonable_count()
    if py == cl:
        print(f"OK: ASP parity matches Python ({py} combinations).")
        return 0
    print(f"MISMATCH: Python={py}, ASP={cl}")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale elevator storyworld with farm flavor, impression, inner monologue, conflict, and rhyme.")
    ap.add_argument("--setting", choices=["elevator"], default="elevator")
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--prop", choices=sorted(PROPS))
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
    hero = args.hero or rng.choice(sorted(HEROES))
    helper = args.helper or rng.choice(sorted(HELPERS))
    prop = args.prop or rng.choice(sorted(PROPS))
    return StoryParams(setting="elevator", hero=hero, helper=helper, prop=prop)


def generate(params: StoryParams) -> StorySample:
    if not is_reasonable(params):
        raise StoryError(explain_rejection(params))
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
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
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{asp_reasonable_count()} reasonable combinations.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for hero in sorted(HEROES):
            for helper in sorted(HELPERS):
                for prop in sorted(PROPS):
                    samples.append(generate(StoryParams(setting="elevator", hero=hero, helper=helper, prop=prop)))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
