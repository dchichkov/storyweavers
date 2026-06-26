#!/usr/bin/env python3
"""
storyworlds/worlds/tantalize_wreckage_conflict_sharing_sound_effects_fable.py
=============================================================================

A small fable-style story world about temptation, wreckage, conflict,
sharing, and sound effects.

Premise:
- A character is tempted by a tasty or shiny thing.
- Chasing or snatching it creates wreckage.
- The conflict is resolved by sharing, which restores calm.

The world model tracks physical damage and emotional tension so the prose is
driven by simulated state rather than a fixed paragraph with swapped nouns.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"worn": 0.0, "wrecked": 0.0}
        if not self.memes:
            self.memes = {"desire": 0.0, "conflict": 0.0, "joy": 0.0, "sharing": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"hare", "rabbit", "squirrel", "fox", "bird", "mouse"}
        male = {"wolf", "bear", "badger", "crow", "deer", "cat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.id if self.kind == "character" else self.label or self.id


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Temptation:
    id: str
    lure: str
    verb: str
    sound: str
    wreckage: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SharedThing:
    id: str
    label: str
    phrase: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.lines = []
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    temptation: str
    shared: str
    name: str
    species: str
    companion: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "orchard": Setting(place="the orchard", afford={"apple", "berries"}),
    "barn": Setting(place="the barn", afford={"hay"}),
    "brook": Setting(place="the brook", afford={"pebbles", "shells"}),
}

TEMPTATIONS = {
    "apple": Temptation(
        id="apple",
        lure="a glossy red apple",
        verb="reach for the apple",
        sound="crunch",
        wreckage="a little wreckage of broken stems and scattered leaves",
        mess="scattered",
        tags={"apple", "sound"},
    ),
    "berries": Temptation(
        id="berries",
        lure="a bowl of berries",
        verb="snatch the berries",
        sound="plip",
        wreckage="berry juice on the moss and a tiny mess",
        mess="stained",
        tags={"berries", "sound"},
    ),
    "hay": Temptation(
        id="hay",
        lure="a tall golden hay stack",
        verb="climb the hay",
        sound="rustle",
        wreckage="a slumped pile of hay and a dusty floor",
        mess="scattered",
        tags={"hay", "sound"},
    ),
    "pebbles": Temptation(
        id="pebbles",
        lure="a shining pebble pile",
        verb="gather the pebbles",
        sound="click",
        wreckage="pebbles rolling everywhere",
        mess="scattered",
        tags={"pebbles", "sound"},
    ),
}

SHARED = {
    "basket": SharedThing(
        id="basket",
        label="basket",
        phrase="a basket full of fruit",
        tags={"share", "fruit"},
    ),
    "bell": SharedThing(
        id="bell",
        label="bell",
        phrase="a small brass bell",
        tags={"sound"},
    ),
    "blanket": SharedThing(
        id="blanket",
        label="blanket",
        phrase="a warm blanket for everyone",
        tags={"share"},
    ),
}

SPECIES_NAMES = {
    "hare": ["Hazel", "Milo", "Nina", "Pip", "Bram"],
    "fox": ["Ruby", "Finn", "Tessa", "Gus", "Luna"],
    "mouse": ["Tilly", "Ollie", "Poppy", "Jasper", "Mina"],
    "rabbit": ["Lily", "Otto", "Brie", "Remy", "June"],
}

TRAITS = ["curious", "hungry", "proud", "gentle", "busy", "eager"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for tempt in setting.afford:
            for shared_id in SHARED:
                out.append((place, tempt, shared_id))
    return out


def reasonableness_gate(setting: Setting, temptation: Temptation, shared: SharedThing) -> bool:
    return temptation.id in setting.afford and shared.id in SHARED


def explain_rejection(setting: Setting, temptation: Temptation, shared: SharedThing) -> str:
    return (
        f"(No story: {temptation.lure} and {shared.label} do not make a reasonable "
        f"fable together in {setting.place}. Pick a temptation that fits the place.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fable world about temptation, wreckage, and sharing."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--shared", choices=SHARED)
    ap.add_argument("--name")
    ap.add_argument("--species", choices=sorted(SPECIES_NAMES))
    ap.add_argument("--companion", choices=sorted(SPECIES_NAMES))
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.temptation is None or c[1] == args.temptation)
              and (args.shared is None or c[2] == args.shared)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, temptation, shared = rng.choice(sorted(combos))
    species = args.species or rng.choice(sorted(SPECIES_NAMES))
    companion = args.companion or rng.choice([s for s in sorted(SPECIES_NAMES) if s != species])
    name = args.name or rng.choice(SPECIES_NAMES[species])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        temptation=temptation,
        shared=shared,
        name=name,
        species=species,
        companion=companion,
        trait=trait,
    )


def _sound_line(sound: str) -> str:
    return {
        "crunch": "CRUNCH!",
        "plip": "PLIP-PLIP!",
        "rustle": "RUSTLE!",
        "click": "CLICK!",
    }.get(sound, sound.upper() + "!")


def tell(setting: Setting, temptation: Temptation, shared: SharedThing,
         hero_name: str, species: str, companion_species: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=species, traits=["little", trait]))
    companion = world.add(Entity(id="Companion", kind="character", type=companion_species, traits=["kind"]))
    shared_item = world.add(Entity(id=shared.id, type="thing", label=shared.label, phrase=shared.phrase))
    world.facts.update(hero=hero, companion=companion, shared=shared_item, temptation=temptation, setting=setting)

    world.say(f"Once in {setting.place}, there lived a little {trait} {species} named {hero_name}.")
    world.say(f"{hero_name} and {companion.name_or_label()} liked to sit together by the path, and they shared {shared.phrase}.")
    world.say(f"But one day, {temptation.lure} began to tempt {hero_name}; it made a sound like {_sound_line(temptation.sound)}.")

    hero.memes["desire"] += 1
    if temptation.id in setting.afford:
        world.say(f"{hero_name} wanted to {temptation.verb} at once.")
        hero.memes["conflict"] += 1
        world.say(f"{hero_name} hurried too fast, and that made {temptation.wreckage}.")
        hero.meters["wrecked"] += 1
        companion.memes["conflict"] += 1
        world.say(f"{companion.name_or_label()} frowned at the {temptation.mess} ground.")

    world.say(f"Then {companion.name_or_label()} took a breath and offered to share the {shared.label}.")
    hero.memes["sharing"] += 1
    companion.memes["sharing"] += 1
    hero.memes["conflict"] = 0.0
    companion.memes["conflict"] = 0.0
    hero.memes["joy"] += 1
    companion.memes["joy"] += 1
    shared_item.meters["worn"] += 1
    world.say(
        f"They sat side by side and shared it slowly. The fable ended quietly, "
        f"with {_sound_line(temptation.sound)} fading into a happy hush."
    )
    return world


KNOWLEDGE = {
    "share": [(
        "What does it mean to share?",
        "To share means to let other people use, enjoy, or have part of something with you.",
    )],
    "sound": [(
        "What is a sound effect in a story?",
        "A sound effect is a word that helps you imagine a noise, like crunch, click, or plip.",
    )],
    "wreckage": [(
        "What is wreckage?",
        "Wreckage is what is left after something gets broken, ruined, or scattered.",
    )],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    temptation = f["temptation"]
    shared = f["shared"]
    return [
        f'Write a short fable for children about {hero.id}, who is tempted by {temptation.lure}, and ends by sharing {shared.phrase}.',
        f"Tell a gentle animal story that includes the sound effect '{temptation.sound}' and the word 'wreckage'.",
        f"Write a moral tale where a little {hero.type} learns that sharing can calm conflict.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    temptation = f["temptation"]
    shared = f["shared"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who was tempted by {temptation.lure} in {place}?",
            answer=f"{hero.id} was tempted by {temptation.lure} in {place}.",
        ),
        QAItem(
            question=f"What sound did the tempting thing make?",
            answer=f"It made a sound like {temptation.sound}.",
        ),
        QAItem(
            question=f"What happened when {hero.id} hurried too fast?",
            answer=f"{temptation.wreckage.capitalize()}. That was the wreckage that followed the rush.",
        ),
        QAItem(
            question=f"How did {hero.id} and {companion.name_or_label()} solve the conflict?",
            answer=f"They solved it by sharing {shared.phrase} and sitting together in peace.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in KNOWLEDGE["share"] + KNOWLEDGE["sound"] + KNOWLEDGE["wreckage"]]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="orchard", temptation="apple", shared="basket", name="Hazel", species="hare", companion="mouse", trait="curious"),
    StoryParams(place="barn", temptation="hay", shared="blanket", name="Milo", species="fox", companion="rabbit", trait="eager"),
    StoryParams(place="brook", temptation="pebbles", shared="bell", name="Tilly", species="mouse", companion="hare", trait="gentle"),
]


ASP_RULES = r"""
tempting(P,T) :- place(P), temptation(T), allows(P,T).
wreckage(P,T) :- tempting(P,T), makes_wreckage(T).
conflict(H) :- tempting(P,T), hero(H), wants(H,T), wreckage(P,T).
sharing(H,S) :- hero(H), shared(S).
resolved(H) :- conflict(H), sharing(H,S).
valid_story(P,T,S) :- tempting(P,T), shared(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(setting.afford):
            lines.append(asp.fact("allows", pid, t))
    for tid, t in TEMPTATIONS.items():
        lines.append(asp.fact("temptation", tid))
        lines.append(asp.fact("makes_wreckage", tid))
    for sid in SHARED:
        lines.append(asp.fact("shared", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set((p, t, s) for p, t, s in asp_valid_stories())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        TEMPTATIONS[params.temptation],
        SHARED[params.shared],
        params.name,
        params.species,
        params.companion,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for p, t, s in stories:
            print(f"  {p:8} {t:10} {s:10}")
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
            header = f"### {p.name}: {p.temptation} at {p.place} (shared: {p.shared})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
