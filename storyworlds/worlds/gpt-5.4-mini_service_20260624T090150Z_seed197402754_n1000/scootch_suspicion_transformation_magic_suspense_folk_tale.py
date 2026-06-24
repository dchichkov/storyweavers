#!/usr/bin/env python3
"""
A small folk-tale storyworld about scootching, suspicion, magic, suspense,
and transformation.

Seed tale premise:
A little forest folk grows suspicious of a strange magic gift on a misty path.
After a careful scootch forward, a bit of old magic reveals what the gift can
change, and the ending proves the world has been transformed.

This script keeps the simulation small and state-driven:
- suspicion builds or softens
- scootch is a cautious physical move
- magic can transform one thing into another
- suspense comes from not knowing whether the gift is safe
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
# World entities
# ---------------------------------------------------------------------------
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother", "witch"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather", "wizard"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    afford_magic: bool = True


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    from_form: str
    to_form: str
    suspense_hint: str
    safe_result: str


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    charm: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "glade": Setting(place="the moonlit glade", mood="soft and still"),
    "brook": Setting(place="the winding brook", mood="bright with water"),
    "hill": Setting(place="the windy hill", mood="wide and echoing"),
}

CHARACTER_TYPES = ["girl", "boy", "fox", "hare", "mouse", "goat"]
HERO_NAMES = ["Mara", "Niko", "Pip", "Tilda", "Bram", "Anya", "Luca"]
HELPER_NAMES = ["Moss", "Wren", "Bela", "Hob", "Edda", "Rune"]

CHARMS = {
    "acorn": Charm(
        id="acorn",
        label="a silver acorn",
        phrase="a silver acorn tied with red thread",
        from_form="acorn",
        to_form="oak door",
        suspense_hint="it hummed like a secret",
        safe_result="the acorn turned into a tiny oak door",
    ),
    "key": Charm(
        id="key",
        label="an old key",
        phrase="an old key with a moon-shaped handle",
        from_form="key",
        to_form="warm lantern",
        suspense_hint="it glimmered like a small eye",
        safe_result="the key became a warm lantern",
    ),
    "stone": Charm(
        id="stone",
        label="a smooth stone",
        phrase="a smooth stone wrapped in blue cloth",
        from_form="stone",
        to_form="clear bridge",
        suspense_hint="it felt heavy as a held breath",
        safe_result="the stone became a clear little bridge",
    ),
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
charm(C) :- charm_id(C).
valid_story(P,C) :- setting(P), charm_id(C), magic(C), suspense(C), transformable(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("mood", sid, s.mood))
        if s.afford_magic:
            lines.append(asp.fact("magic_place", sid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm_id", cid))
        lines.append(asp.fact("magic", cid))
        lines.append(asp.fact("suspense", cid))
        lines.append(asp.fact("transformable", cid))
        lines.append(asp.fact("from_form", cid, c.from_form))
        lines.append(asp.fact("to_form", cid, c.to_form))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, c) for p in SETTINGS for c in CHARMS}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} story settings).")
        return 0
    print("MISMATCH between ASP and Python.")
    if cl - py:
        print(" only in ASP:", sorted(cl - py))
    if py - cl:
        print(" only in Python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def build_reasonable_combo(place: Optional[str], charm: Optional[str]) -> list[tuple[str, str]]:
    combos = [(p, c) for p in SETTINGS for c in CHARMS]
    if place:
        combos = [x for x in combos if x[0] == place]
    if charm:
        combos = [x for x in combos if x[1] == charm]
    return combos


def predict(world: World, hero: Entity, charm: Charm) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    h.memes["suspicion"] = h.memes.get("suspicion", 0) + 1
    sim.facts["moved"] = True
    return {
        "suspicious": h.memes["suspicion"] >= THRESHOLD,
        "transformed": True,
    }


def _intro(world: World, hero: Entity, helper: Entity, charm: Charm) -> None:
    world.say(
        f"Long ago, in {world.setting.place}, there lived {hero.id}, a little {hero.type} "
        f"who liked quiet paths and old tales."
    )
    world.say(
        f"One dusk, {helper.id} brought {hero.pronoun('object')} {charm.phrase}; "
        f"{charm.suspense_hint}."
    )
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0) + 1
    world.say(
        f"{hero.id} looked at it with suspicion, for folk stories said gifts like that "
        f"could change more than they seemed to."
    )


def _scootch(world: World, hero: Entity) -> None:
    hero.meters["scootch"] = hero.meters.get("scootch", 0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    world.say(
        f"Still, {hero.id} made a small scootch forward, one careful step at a time."
    )


def _suspense(world: World, hero: Entity, charm: Charm) -> None:
    hero.memes["suspense"] = hero.memes.get("suspense", 0) + 1
    world.say(
        f"The charm gave no easy answer. It only waited, quiet and bright, as if it "
        f"were asking {hero.pronoun('object')} to trust the night."
    )


def _transform(world: World, hero: Entity, helper: Entity, charm: Charm) -> None:
    hero.memes["suspicion"] = max(0, hero.memes.get("suspicion", 0) - 1)
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    world.say(
        f"Then {helper.id} whispered the old magic words, and {charm.label} stirred."
    )
    world.say(
        f"In a blink, {charm.safe_result}. The air smelled sweet, and the fear in "
        f"{hero.id}'s chest grew smaller."
    )


def _ending(world: World, hero: Entity, helper: Entity, charm: Charm) -> None:
    world.say(
        f"{hero.id} smiled at the new thing beside {hero.pronoun('object')}, and the "
        f"two friends walked home while moonlight silvered the path."
    )
    world.say(
        f"By morning, the place felt changed, and even the birds seemed to know that "
        f"the little tale had turned from suspicion into wonder."
    )


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type))
    charm = CHARMS[params.charm]

    _intro(world, hero, helper, charm)
    world.para()
    _scootch(world, hero)
    _suspense(world, hero, charm)
    world.para()
    _transform(world, hero, helper, charm)
    _ending(world, hero, helper, charm)

    world.facts.update(hero=hero, helper=helper, charm=charm, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    charm: Charm = f["charm"]
    return [
        f"Write a short folk tale for a child about {hero.id}, suspicion, and {charm.label}.",
        f"Tell a magical story where {helper.id} helps {hero.id} scootch closer to a strange charm.",
        f"Write a gentle suspense story in a village-woods style that ends with a transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    charm: Charm = f["charm"]
    place = world.setting.place
    return [
        QAItem(
            question=f"What did {hero.id} first feel about the charm in {place}?",
            answer=f"{hero.id} first felt suspicion, because the charm seemed strange and full of old magic.",
        ),
        QAItem(
            question=f"What small move did {hero.id} make before the magic changed anything?",
            answer=f"{hero.id} made a small scootch forward, carefully and step by step.",
        ),
        QAItem(
            question=f"Who spoke the magic words that brought the change?",
            answer=f"{helper.id} spoke the old magic words, and that helped {charm.label} transform.",
        ),
        QAItem(
            question=f"What did the charm become at the end of the story?",
            answer=f"It became {charm.safe_result.replace('the ', '')}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does suspicion mean?",
            answer="Suspicion is a feeling that something may not be safe or honest, so you watch it carefully before you trust it.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a big change, when one thing turns into another.",
        ),
        QAItem(
            question="What is magic in a folk tale?",
            answer="Magic is a special power that can make impossible things happen, like turning one object into another.",
        ),
        QAItem(
            question="Why do stories use suspense?",
            answer="Suspense keeps you wondering what will happen next, so the story feels exciting and tense.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="glade", hero="Mara", hero_type="girl", helper="Wren", helper_type="hare", charm="acorn"),
    StoryParams(place="brook", hero="Pip", hero_type="mouse", helper="Moss", helper_type="fox", charm="key"),
    StoryParams(place="hill", hero="Bram", hero_type="boy", helper="Edda", helper_type="goat", charm="stone"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk-tale storyworld of suspicion and transformation.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=CHARACTER_TYPES)
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=CHARACTER_TYPES)
    ap.add_argument("--charm", choices=CHARMS.keys())
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
    if args.charm and args.place:
        pass
    combos = build_reasonable_combo(args.place, args.charm)
    if not combos:
        raise StoryError("No valid story matches the given options.")
    place, charm = rng.choice(combos)
    hero_type = args.hero_type or rng.choice(CHARACTER_TYPES)
    helper_type = args.helper_type or rng.choice([t for t in CHARACTER_TYPES if t != hero_type])
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    if hero == helper:
        helper = helper + " the Helper"
    return StoryParams(
        place=place,
        hero=hero,
        hero_type=hero_type,
        helper=helper,
        helper_type=helper_type,
        charm=charm,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
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
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
            header = f"### {p.hero} in {p.place} with {p.charm}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
