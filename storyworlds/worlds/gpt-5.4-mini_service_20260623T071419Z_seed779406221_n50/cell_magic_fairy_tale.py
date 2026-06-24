#!/usr/bin/env python3
"""
storyworlds/worlds/cell_magic_fairy_tale.py
===========================================

A small fairy-tale storyworld about a locked cell, a little spell, and a kind
turn toward freedom.

The seed image:
---
In a gray castle under a moonlit sky, a tiny fairy named Nia was trapped in a
stone cell. She had a spark of magic, but the iron door was shut tight. A
gentle mouse brought her a crumb of moon sugar, and Nia whispered a clever spell
that made the key glow. The guard heard the glow, opened the cell, and Nia
flew out into the night with the mouse on her shoulder.

World model:
- physical meters: trapped, locked, lit, open, tired, bright, heavy
- emotional memes: hope, fear, courage, kindness, wonder, relief

The story is driven by state changes:
- being trapped raises fear and lowers comfort
- using magic raises brightness and hope
- a helper can change the result if they are kind and present
- the ending proves the change through an open door, flight, and relief
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
CHARACTER_KINDS = {"fairy", "girl", "boy", "guard", "mouse", "king", "queen", "witch", "wizard"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "woman", "fairy", "witch"}
        male = {"boy", "king", "man", "wizard", "guard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"queen": "queen", "king": "king", "guard": "guard"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    dark: bool = False
    cold: bool = False
    has_cell: bool = False
    has_magic: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Spell:
    id: str
    name: str
    phrase: str
    effect: str
    requires_kindness: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    kind: str
    label: str
    phrase: str
    aid: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_trapped(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["trapped"] < THRESHOLD:
            continue
        sig = ("trapped", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["fear"] += 1
        out.append(f"{ent.id} felt fear in the stone cell.")
    return out


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["spell"] < THRESHOLD:
            continue
        sig = ("magic", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["bright"] += 1
        ent.memes["hope"] += 1
        out.append(f"A bright little magic woke up around {ent.id}.")
    return out


def _r_helper(world: World) -> list[str]:
    out: list[str] = []
    fairy = world.facts.get("hero")
    helper = world.facts.get("helper")
    if not fairy or not helper:
        return out
    if helper.memes["kindness"] < THRESHOLD:
        return out
    if fairy.meters["bright"] < THRESHOLD:
        return out
    sig = ("help", helper.id, fairy.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fairy.meters["open"] += 1
    fairy.memes["relief"] += 1
    out.append(f"{helper.id} helped the spell reach the key.")
    return out


CAUSAL_RULES = [
    Rule(name="trapped", tag="emotional", apply=_r_trapped),
    Rule(name="magic", tag="physical", apply=_r_magic),
    Rule(name="help", tag="social", apply=_r_helper),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        if not place.has_cell:
            continue
        for spell_id, spell in SPELLS.items():
            if not place.has_magic:
                continue
            for helper_id, helper in HELPERS.items():
                combos.append((place_id, spell_id, helper_id))
    return combos


@dataclass
class StoryParams:
    place: str
    spell: str
    helper: str
    hero_name: str
    hero_type: str
    hero_trait: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


PLACES = {
    "castle_cell": Place(id="castle_cell", label="the castle cell", dark=True, cold=True, has_cell=True, has_magic=True, tags={"cell", "castle", "magic"}),
    "moon_tower": Place(id="moon_tower", label="the moon tower cell", dark=True, cold=True, has_cell=True, has_magic=True, tags={"cell", "tower", "magic"}),
}

SPELLS = {
    "key_glow": Spell(id="key_glow", name="glow spell", phrase="a tiny glow spell", effect="made the key glow", requires_kindness=True, tags={"magic", "key"}),
    "mouse_song": Spell(id="mouse_song", name="song spell", phrase="a soft song spell", effect="made the lock hum open", requires_kindness=False, tags={"magic", "song"}),
    "moon_step": Spell(id="moon_step", name="moon step", phrase="a moon step spell", effect="made the bars soften", requires_kindness=True, tags={"magic", "moon"}),
}

HELPERS = {
    "mouse": Helper(id="mouse", kind="mouse", label="a tiny mouse", phrase="a tiny mouse", aid="nibbled the crumb and listened kindly", tags={"mouse", "kindness"}),
    "bird": Helper(id="bird", kind="bird", label="a blue bird", phrase="a blue bird", aid="carried a silver feather", tags={"bird", "kindness"}),
}

GIRL_NAMES = ["Nia", "Mina", "Luna", "Tessa", "Elia", "Mira"]
BOY_NAMES = ["Finn", "Oren", "Bram", "Pax", "Theo", "Niko"]
TRAITS = ["brave", "curious", "gentle", "hopeful", "lonely", "small"]


def tell(place: Place, spell: Spell, helper: Helper, hero_name: str, hero_type: str, hero_trait: str, helper_name: str, helper_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", hero_trait]))
    help_ent = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper.label, phrase=helper.phrase, traits=["kind"]))
    cell = world.add(Entity(id="cell", kind="thing", type="cell", label="cell"))
    key = world.add(Entity(id="key", kind="thing", type="key", label="key", attrs={"locked": True}))
    # initialize all read state before propagation
    hero.meters["trapped"] = 1
    hero.meters["spell"] = 0
    hero.meters["bright"] = 0
    hero.meters["open"] = 0
    hero.memes["fear"] = 0
    hero.memes["hope"] = 0
    hero.memes["relief"] = 0
    help_ent.memes["kindness"] = 1 if helper.kind in {"mouse", "bird"} else 0
    help_ent.memes["hope"] = 0
    world.facts.update(hero=hero, helper=help_ent, spell=spell, cell=cell, key=key)

    world.say(f"In {place.label}, {hero.id} was trapped in a little stone cell.")
    world.say(f"{hero.pronoun().capitalize()} had only {spell.phrase} and a heart full of waiting.")
    world.para()
    world.say(f"Then {helper.phrase} came by and {helper.aid}.")
    hero.meters["spell"] += 1
    propagate(world, narrate=True)
    if spell.requires_kindness and help_ent.memes["kindness"] < THRESHOLD:
        raise StoryError("This spell needs a kind helper.")
    if helper.kind == "mouse":
        world.say(f"{hero.id} whispered, \"Little friend, help me with the {spell.name}.\"")
    else:
        world.say(f"{hero.id} whispered, \"Kind friend, help me with the {spell.name}.\"")
    world.para()
    if hero.meters["bright"] >= THRESHOLD:
        key.meters["glow"] += 1
        key.attrs["unlocked"] = True
        hero.meters["trapped"] = 0
        hero.meters["open"] = 1
        world.say(f"The key began to glow, and the cell door opened with a small sigh.")
        world.say(f"{hero.id} flew out into the moonlit night, and {helper.id} rode home on {hero.pronoun('possessive')} shoulder.")
    else:
        world.say(f"The spell only winked, and the cell stayed shut until a guard heard the soft light.")
    world.facts["resolved"] = hero.meters["open"] >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    spell = f["spell"]
    helper = f["helper"]
    return [
        f'Write a fairy tale for a 3-to-5-year-old about {hero.id} trapped in a cell who uses {spell.phrase} and gets help from {helper.phrase}.',
        f"Tell a gentle story where a small fairy named {hero.id} learns a magic way out of a cell with help from {helper.phrase}.",
        f'Write a short fairy tale about a cell, a magic spell, and a kind helper, ending with {hero.id} free in the moonlight.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    spell = f["spell"]
    place = f["place"]
    qa = [
        QAItem(question=f"Who was trapped in the cell?", answer=f"{hero.id} was trapped in the cell in {place.label}."),
        QAItem(question=f"What magic did {hero.id} use?", answer=f"{hero.id} used {spell.phrase} to make the key glow."),
        QAItem(question=f"Who helped {hero.id}?", answer=f"{helper.id} helped with the spell and made the little plan kinder and stronger."),
    ]
    if f.get("resolved"):
        qa.append(QAItem(question=f"What happened at the end?", answer=f"The cell door opened, and {hero.id} flew out into the night free and happy."))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a cell?", answer="A cell is a small locked room or space, often made of stone or bars."),
        QAItem(question="What does magic mean in a fairy tale?", answer="Magic is a special pretend power that can make strange, wonderful things happen."),
        QAItem(question="Why is a kind helper important?", answer="A kind helper can bring hope, tools, or courage when someone is stuck."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("\n== Story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}\nA: {q.answer}")
    parts.append("\n== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)} attrs={e.attrs}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="castle_cell", spell="key_glow", helper="mouse", hero_name="Nia", hero_type="fairy", hero_trait="hopeful", helper_name="Milo", helper_type="mouse"),
    StoryParams(place="moon_tower", spell="moon_step", helper="bird", hero_name="Luna", hero_type="fairy", hero_trait="gentle", helper_name="Blue", helper_type="bird"),
]


def explain_rejection(spell: Spell, helper: Helper) -> str:
    return f"(No story: the spell {spell.name} needs a kind helper, and this helper is not a fit.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: a cell, a little magic, and a kind helper.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--type", dest="hero_type", choices=["fairy", "girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mouse", "bird"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.spell is None or c[1] == args.spell)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, spell, helper = rng.choice(sorted(combos))
    hero_type = args.hero_type or "fairy"
    name = args.name or rng.choice(GIRL_NAMES if hero_type == "fairy" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    helper_name = args.helper_name or rng.choice(["Milo", "Pip", "Blue", "Nell"])
    helper_type = args.helper_type or helper
    return StoryParams(place=place, spell=spell, helper=helper, hero_name=name, hero_type=hero_type, hero_trait=trait, helper_name=helper_name, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    spell = SPELLS[params.spell]
    helper = HELPERS[params.helper]
    if spell.requires_kindness and helper.kind not in {"mouse", "bird"}:
        raise StoryError(explain_rejection(spell, helper))
    world = tell(place, spell, helper, params.hero_name, params.hero_type, params.hero_trait, params.helper_name, params.helper_type)
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


ASP_RULES = r"""
has_cell(P) :- place(P), cell_place(P).
has_magic(P) :- place(P), magic_place(P).
valid(P,S,H) :- has_cell(P), has_magic(P), spell(S), helper(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        if PLACES[p].has_cell:
            lines.append(asp.fact("cell_place", p))
        if PLACES[p].has_magic:
            lines.append(asp.fact("magic_place", p))
    for s in SPELLS:
        lines.append(asp.fact("spell", s))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("Mismatch between ASP and Python valid combos.")
        return 1
    print(f"OK: {len(py)} valid combos.")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("Smoke test failed: empty story.")
        return 1
    print("OK: smoke test story generated.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
