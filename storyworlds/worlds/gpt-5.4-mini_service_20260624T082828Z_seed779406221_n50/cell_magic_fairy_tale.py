#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T082828Z_seed779406221_n50/cell_magic_fairy_tale.py
====================================================================================================

A small fairy-tale story world about a child-like hero, a cell, and a bit of
magic used to turn a locked, lonely place into a hopeful escape.

The seed tale behind this world is simple:
A tiny fairy is stuck in a stone cell. She cannot open the iron door by herself.
She remembers a sparkle spell, calls a helpful moth, and lights the dark cell.
The guard grows sleepy, the key falls, and the fairy slips out into the moonlit
garden. The cold cell is left behind, but the fairy carries the glow with her.

The simulated world tracks:
- a hero with joy, fear, and hope
- a cell with door, lock, light, and magical shimmer
- a helper creature or object
- a key that can be found, stolen, or enchanted
- a simple turn where magic changes the balance
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
    held_by: Optional[str] = None
    location: str = ""
    magical: bool = False
    openable: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "fairy", "woman", "mother"}
        male = {"boy", "king", "prince", "wizard", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old castle"
    indoors: bool = True
    mood: str = "moonlit"


@dataclass
class Magic:
    id: str
    name: str
    chant: str
    effect: str
    light: str
    helper_needed: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Cell:
    id: str
    label: str
    lock_kind: str
    dark: bool = True
    stone_cold: bool = True
    barred: bool = True


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _ensure_meter(ent: Entity, key: str) -> float:
    return ent.meters.setdefault(key, 0.0)


def _ensure_meme(ent: Entity, key: str) -> float:
    return ent.memes.setdefault(key, 0.0)


def _r_magic_light(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    cell = world.get("cell")
    wand = world.entities.get("wand")
    if not wand or wand.held_by != hero.id:
        return out
    if hero.memes.get("hope", 0.0) < THRESHOLD:
        return out
    sig = ("light",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cell.meters["light"] = cell.meters.get("light", 0.0) + 1
    cell.dark = False
    out.append("A soft gold glow filled the cell.")
    return out


def _r_sleepy_guard(world: World) -> list[str]:
    out: list[str] = []
    guard = world.entities.get("guard")
    cell = world.entities.get("cell")
    if not guard or cell.meters.get("light", 0.0) < THRESHOLD:
        return out
    sig = ("sleepy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guard.memes["sleepy"] = guard.memes.get("sleepy", 0.0) + 1
    guard.memes["watchful"] = max(0.0, guard.memes.get("watchful", 0.0) - 1.0)
    out.append("The guard blinked and grew sleepy.")
    return out


def _r_drop_key(world: World) -> list[str]:
    out: list[str] = []
    guard = world.entities.get("guard")
    key = world.entities.get("key")
    if not guard or not key:
        return out
    if guard.memes.get("sleepy", 0.0) < THRESHOLD:
        return out
    sig = ("drop_key",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    key.held_by = None
    key.location = "cell floor"
    out.append("The iron key slipped from the guard's hand.")
    return out


def _r_open_door(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    cell = world.get("cell")
    key = world.entities.get("key")
    if not key or key.location != "cell floor":
        return out
    if hero.location != cell.id:
        return out
    sig = ("open",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cell.barred = False
    cell.openable = True
    out.append("The little door creaked open.")
    return out


CAUSAL_RULES = [_r_magic_light, _r_sleepy_guard, _r_drop_key, _r_open_door]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world) if hasattr(rule, "apply") else rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_use_magic(world: World, hero: Entity, magic: Magic) -> bool:
    return hero.memes.get("hope", 0.0) >= THRESHOLD and magic.id in world.facts.get("known_magic", set())


def predict_escape(world: World, hero: Entity, magic: Magic) -> dict:
    sim = world.copy()
    sim.get("hero").memes["hope"] = max(sim.get("hero").memes.get("hope", 0.0), 1.0)
    wand = sim.entities.get("wand")
    if wand:
        wand.held_by = hero.id
    simulate_magic(sim, hero, magic, narrate=False)
    cell = sim.get("cell")
    return {
        "open": not cell.barred,
        "light": cell.meters.get("light", 0.0),
        "sleepy_guard": sim.get("guard").memes.get("sleepy", 0.0) if "guard" in sim.entities else 0.0,
    }


def simulate_magic(world: World, hero: Entity, magic: Magic, narrate: bool = True) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    hero.meters["spark"] = hero.meters.get("spark", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, cell: Cell) -> None:
    trait = next((t for t in hero.traits if t != "little"), "tiny")
    world.say(
        f"In {world.setting.place}, there lived a little {trait} {hero.type} named {hero.id}, "
        f"and she was locked in {cell.label}."
    )


def describe_cell(world: World, cell: Cell) -> None:
    world.say(
        f"The cell was cold stone with a heavy lock, and even the moonlight had to slip through the bars."
    )


def longing(world: World, hero: Entity, magic: Magic) -> None:
    hero.memes["sad"] = hero.memes.get("sad", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"{hero.id} pressed a hand to the bars and whispered that she wished for {magic.name}."
    )


def find_helper(world: World, hero: Entity, helper: Entity) -> None:
    helper.held_by = None
    helper.location = world.entities["cell"].id
    world.say(
        f"A shy little {helper.type} fluttered near the bars and listened to {hero.id}'s soft voice."
    )


def ask_for_help(world: World, hero: Entity, helper: Entity, magic: Magic) -> None:
    hero.memes["need"] = hero.memes.get("need", 0.0) + 1
    world.say(
        f"{hero.id} asked the {helper.type} to bring the {magic.name} spark to the dark cell."
    )


def cast_spell(world: World, hero: Entity, magic: Magic, helper: Entity) -> None:
    wand = world.entities.get("wand")
    if wand:
        wand.held_by = hero.id
    world.say(
        f"{hero.id} lifted {hero.pronoun('possessive')} wand and spoke the gentle chant, "
        f'"{magic.chant}."'
    )
    world.say(f"The {helper.type} tapped the wall, and the spell began to shimmer.")
    simulate_magic(world, hero, magic, narrate=True)


def take_key(world: World, hero: Entity) -> None:
    key = world.entities.get("key")
    if key and key.location == "cell floor":
        key.held_by = hero.id
        key.location = ""
        world.say(f"{hero.id} picked up the iron key with both hands.")


def escape(world: World, hero: Entity, cell: Cell, magic: Magic) -> None:
    if cell.barred:
        return
    hero.location = "garden"
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1.0)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"{hero.id} slipped out of {cell.label} and into the moonlit garden, "
        f"carrying {magic.light} in her heart."
    )


SETTING = Setting(place="the old castle", indoors=True, mood="moonlit")

MAGICS = {
    "spark": Magic(
        id="spark",
        name="sparkle magic",
        chant="Twinkle, twist, and open the way",
        effect="light",
        light="a small golden glow",
        helper_needed=True,
        tags={"light", "key", "cell"},
    ),
    "lull": Magic(
        id="lull",
        name="lullaby magic",
        chant="Hush, hush, sleepy eyes",
        effect="sleep",
        light="a silver hush",
        helper_needed=True,
        tags={"sleep", "guard", "cell"},
    ),
}

CELL = Cell(id="cell", label="the stone cell", lock_kind="iron lock")

GIRL_NAMES = ["Lily", "Mira", "Nora", "Ivy", "Ruby", "Ella", "Rose", "Ada"]
BOY_NAMES = ["Finn", "Theo", "Bram", "Noel", "Pip", "Leo", "Jace"]
HELPERS = [
    ("moth", "a tiny moth"),
    ("mouse", "a little mouse"),
    ("bird", "a bright sparrow"),
]
TRAITS = ["brave", "gentle", "curious", "tiny", "hopeful", "sweet"]


@dataclass
class StoryParams:
    magic: str
    name: str
    gender: str
    trait: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about a cell and a bit of magic.")
    ap.add_argument("--magic", choices=sorted(MAGICS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["moth", "mouse", "bird"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for mid, magic in MAGICS.items():
        for helper, _phrase in HELPERS:
            if magic.helper_needed:
                combos.append((mid, helper))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if args.magic is None or c[0] == args.magic
              and (args.helper is None or c[1] == args.helper)]
    if not combos:
        raise StoryError("(No valid magic/helper combination matches the given options.)")
    magic, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(magic=magic, name=name, gender=gender, trait=trait, helper=helper)


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(
        id=params.name, kind="character", type="fairy" if params.gender == "girl" else "boy",
        traits=["little", params.trait],
        location="cell",
    ))
    cell = world.add(Entity(id="cell", kind="place", type="cell", label="the stone cell", meters={"light": 0.0}))
    guard = world.add(Entity(id="guard", kind="character", type="guard", label="the guard", memes={"watchful": 1.0}))
    key = world.add(Entity(id="key", type="key", label="iron key", openable=True, location="guard"))
    wand = world.add(Entity(id="wand", type="wand", label="wand", magical=True, held_by=hero.id))
    helper_type, helper_phrase = next((h, p) for h, p in HELPERS if h == params.helper)
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_phrase, location="outside"))
    world.facts["known_magic"] = {params.magic}

    magic = MAGICS[params.magic]

    intro(world, hero, CELL)
    describe_cell(world, CELL)
    world.para()
    longing(world, hero, magic)
    find_helper(world, hero, helper)
    ask_for_help(world, hero, helper, magic)
    world.para()
    cast_spell(world, hero, magic, helper)
    take_key(world, hero)
    escape(world, hero, CELL, magic)

    world.facts.update(hero=hero, cell=cell, guard=guard, key=key, wand=wand, helper=helper, magic=magic)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    magic = f["magic"]
    helper = f["helper"]
    return [
        f'Write a short fairy tale for a child about a {hero.type} trapped in a cell who uses {magic.name}.',
        f"Tell a gentle story where {hero.id} is locked in a stone cell and a {helper.type} helps with {magic.name}.",
        f'Write a magical story that includes the word "cell" and ends with a soft escape into the garden.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    magic = f["magic"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Where was {hero.id} at the start of the story?",
            answer=f"{hero.id} was locked in the stone cell inside the old castle.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with {magic.name}?",
            answer=f"A shy little {helper.type} helped {hero.id} with the magic.",
        ),
        QAItem(
            question=f"What happened after the spell worked?",
            answer=f"The cell became bright, the key fell free, and {hero.id} slipped out into the moonlit garden.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    magic = f["magic"]
    out = [
        QAItem(
            question="What is a cell?",
            answer="A cell is a small enclosed room with walls or bars, often used to keep someone from leaving.",
        ),
        QAItem(
            question="What does magic do in fairy tales?",
            answer="Magic can change what seems impossible, like opening a locked door or lighting a dark room.",
        ),
    ]
    if magic.id == "spark":
        out.append(QAItem(
            question="Why is light helpful in a dark place?",
            answer="Light helps you see the room, find keys, and feel less scared in the dark.",
        ))
    else:
        out.append(QAItem(
            question="Why can a lullaby make someone sleepy?",
            answer="A lullaby is gentle and soft, so it can calm busy eyes and help a listener rest.",
        ))
    return out


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.magical:
            bits.append("magical=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
cell_closed :- cell.
magic_ready :- magic(spark), helper_needed(spark).
lighted :- magic_ready.
sleepy_guard :- lighted.
key_falls :- sleepy_guard.
door_open :- key_falls.
escape :- door_open.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("cell"))
    for mid, magic in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        if magic.helper_needed:
            lines.append(asp.fact("helper_needed", mid))
    for helper, _ in HELPERS:
        lines.append(asp.fact("helper", helper))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show escape/0.\n#show door_open/0.\n"))
    atoms = {sym.name for sym in model}
    if "escape" in atoms and "door_open" in atoms:
        print("OK: ASP rules derive the escape.")
        return 0
    print("MISMATCH: ASP rules did not derive the escape.")
    return 1


def asp_list() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show escape/0.\n"))
    return [tuple()] if any(sym.name == "escape" for sym in model) else []


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(magic="spark", name="Lily", gender="girl", trait="gentle", helper="moth"),
    StoryParams(magic="lull", name="Finn", gender="boy", trait="hopeful", helper="mouse"),
    StoryParams(magic="spark", name="Mira", gender="girl", trait="brave", helper="bird"),
]


def build_main_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
        return samples
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(args.n * 50, 50):
        seed = base_seed + i
        i += 1
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show escape/0.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP-compatible magic stories:")
        for mid, helper in valid_combos():
            print(f"  {mid:6} helper={helper}")
        return

    try:
        samples = build_main_samples(args)
    except StoryError as err:
        print(err)
        return

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
            header = f"### {p.name}: {p.magic} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
