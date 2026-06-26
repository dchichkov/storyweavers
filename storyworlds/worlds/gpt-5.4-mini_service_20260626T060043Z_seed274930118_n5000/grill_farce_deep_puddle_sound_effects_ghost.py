#!/usr/bin/env python3
"""
storyworlds/worlds/grill_farce_deep_puddle_sound_effects_ghost.py
==================================================================

A small ghost-story farce set beside a deep puddle where a grill hisses,
clatters, and plays tricks on the brave little cast.

Premise:
- A backyard grill is set near a deep puddle.
- A child or caretaker tries to host a cheerful cookout.
- Strange sound effects make the grill seem haunted.

Turn:
- A splat, hiss, clang, or blub from the puddle starts a comic panic.
- The characters think a ghost is helping or haunting the grill.

Resolution:
- The "ghost" turns out to be a harmless cause in the scene.
- The grill is moved, dried, or covered, and the farce ends with laughter.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the deep puddle"
    depth: str = "deep"
    affords: set[str] = field(default_factory=set)


@dataclass
class SoundEffect:
    id: str
    text: str
    cause: str
    mood: str
    tag: str


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    vulnerable: bool = False
    protected_by: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str = "puddle"
    effect: str = "sizzle"
    item: str = "grill"
    name: str = "Mia"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "curious"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


SETTINGS = {
    "puddle": Setting(place="the deep puddle", depth="deep", affords={"sizzle", "clang", "splash", "blub"}),
}

EFFECTS = {
    "sizzle": SoundEffect("sizzle", "sizzle-sizzle", "wet heat", "mischievous", "wet"),
    "clang": SoundEffect("clang", "clang-clank", "windy bump", "comic", "metal"),
    "blub": SoundEffect("blub", "blub-blub", "deep water", "spooky", "water"),
    "splash": SoundEffect("splash", "splish-splash", "footstep", "playful", "water"),
}

ITEMS = {
    "grill": Item("grill", "grill", "an old grill with a crooked lid", vulnerable=True),
    "cover": Item("cover", "grill cover", "a dark grill cover", vulnerable=False, protected_by={"sizzle", "blub", "splash"}),
}

NAMES = ["Mia", "Theo", "Nora", "Ben", "Lily", "Finn"]
TRAITS = ["curious", "brave", "cheerful", "sly", "careful", "playful"]
PARENTS = ["mother", "father"]


def reasonableness_gate(effect: SoundEffect, item: Item, setting: Setting) -> bool:
    return item.id == "grill" and effect.tag in {"wet", "water", "metal"} and "splash" in setting.affords


def explain_rejection(effect: SoundEffect, item: Item) -> str:
    return f"(No story: the {effect.text} sound does not plausibly haunt {item.label} in this setup.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for eid, e in EFFECTS.items():
        lines.append(asp.fact("effect", eid))
        lines.append(asp.fact("effect_tag", eid, e.tag))
        lines.append(asp.fact("effect_mood", eid, e.mood))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if it.vulnerable:
            lines.append(asp.fact("vulnerable", iid))
        for p in sorted(it.protected_by):
            lines.append(asp.fact("protected_by", iid, p))
    return "\n".join(lines)


ASP_RULES = r"""
haunted(S,E,I) :- setting(S), effect(E), item(I), affords(S,E), vulnerable(I),
                  effect_tag(E, wet).
reasonable(S,E,I) :- haunted(S,E,I).
#show reasonable/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = {("puddle", e, "grill") for e in EFFECTS if reasonableness_gate(EFFECTS[e], ITEMS["grill"], SETTINGS["puddle"])}
    cl = set(asp_reasonable())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story farce with a grill and a deep puddle.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--effect", choices=EFFECTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or "puddle"
    effect = args.effect or "sizzle"
    item = args.item or "grill"
    if not reasonableness_gate(EFFECTS[effect], ITEMS[item], SETTINGS[place]):
        raise StoryError(explain_rejection(EFFECTS[effect], ITEMS[item]))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, effect=effect, item=item, name=name, gender=gender, parent=parent, trait=trait)


def _intro(world: World, hero: Entity, parent: Entity, grill: Entity) -> None:
    world.say(f"{hero.id} was a little {next(t for t in hero.traits if t != 'little')} {hero.type} who loved backyard cookouts.")
    world.say(f"{hero.pronoun().capitalize()} and {parent.pronoun().capitalize()} were setting up {grill.phrase} beside {world.setting.place}.")


def _haunt(world: World, hero: Entity, effect: SoundEffect, grill: Entity) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    grill.meters["wet"] = grill.meters.get("wet", 0) + 1
    world.say(f"Then came a {effect.text}: {effect.text}! It echoed over the water like a tiny ghost with muddy shoes.")
    world.say(f"{hero.id} blinked. The grill gave a lonely {effect.text}, and even the spatula seemed to shiver.")


def _panic(world: World, hero: Entity, parent: Entity, effect: SoundEffect) -> None:
    hero.memes["spook"] = hero.memes.get("spook", 0) + 1
    world.say(f'"Did you hear that?" {hero.id} whispered. "{effect.text}!"')
    world.say(f"{parent.id} looked at the deep puddle and laughed. " + '"That is either a ghost or a very dramatic bubble," they said.')


def _reveal(world: World, hero: Entity, parent: Entity, grill: Entity, effect: SoundEffect) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    grill.meters["moved"] = 1
    world.say(f"At last, {parent.id} nudged the grill back from {world.setting.place}, where the water had been trapping the noise.")
    world.say(f"The next {effect.text} sounded small and silly, not spooky at all.")
    world.say(f"{hero.id} laughed, and the cookout went on with a warm crackle instead of a ghostly fuss.")


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait, "stubborn"],
    ))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label="the parent"))
    grill = world.add(Entity(id="grill", type="grill", label="grill", phrase=ITEMS["grill"].phrase))
    effect = EFFECTS[params.effect]

    _intro(world, hero, parent, grill)
    world.para()
    _haunt(world, hero, effect, grill)
    _panic(world, hero, parent, effect)
    world.para()
    _reveal(world, hero, parent, grill, effect)

    world.facts = {"hero": hero, "parent": parent, "grill": grill, "effect": effect, "params": params, "setting": world.setting}
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, effect = f["hero"], f["effect"]
    return [
        f'Write a child-friendly ghost story farce that includes "{effect.text}" and a grill beside a deep puddle.',
        f"Tell a short spooky-but-funny story about {hero.id} hearing {effect.text} near a grill.",
        "Write a story where a strange sound effect seems ghostly, but the answer turns out harmless and funny.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, effect = f["hero"], f["parent"], f["effect"]
    return [
        QAItem(
            question=f"What spooky sound did {hero.id} hear by the deep puddle?",
            answer=f"{hero.id} heard {effect.text}, and it sounded like a tiny ghost making trouble near the grill.",
        ),
        QAItem(
            question=f"Why did {hero.id} think the grill was haunted?",
            answer=f"{hero.id} thought the grill was haunted because {effect.text} echoed over {world.setting.place} and made the scene feel eerie.",
        ),
        QAItem(
            question=f"How did the farce end?",
            answer=f"The farce ended when {parent.id} moved the grill back from the water, and the scary sound became just a silly noise.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a grill do?",
            answer="A grill heats food over fire or hot coals, so people can cook outside.",
        ),
        QAItem(
            question="What is a puddle?",
            answer="A puddle is a little pool of water on the ground, often left after rain.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a special noise that helps make a moment feel spooky, funny, loud, or exciting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="puddle", effect="sizzle", item="grill", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="puddle", effect="blub", item="grill", name="Theo", gender="boy", parent="father", trait="brave"),
    StoryParams(place="puddle", effect="clang", item="grill", name="Nora", gender="girl", parent="mother", trait="playful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonable/3."))
        atoms = sorted(set(asp.atoms(model, "reasonable")))
        for atom in atoms:
            print(atom)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
