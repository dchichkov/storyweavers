#!/usr/bin/env python3
"""
storyworlds/worlds/axle_dialogue_cautionary_curiosity_ghost_story.py
====================================================================

A small, standalone story world about a curious child, a cautionary warning,
and a gentle ghost story centered on an axle.

Seed tale imagined from the premise:
---
On a foggy evening, a curious child hears a soft clink-clink from an old wagon
in the shed. The wagon's axle is rusty and a little crooked. A pale ghost appears
and whispers that the wagon should not be rolled until the axle is checked.

The child wants to peek closer, but a careful parent says the same thing:
"Don't push it yet. Old wood and a bent axle can break." The child and parent
shine a lantern, inspect the wagon together, and find that the axle is loose.

The ghost, who only wanted to keep everyone safe, points to a spare axle on a
hook. Together they replace the broken part. At the end, the wagon rolls softly
and the ghost fades with a pleased smile, leaving the barn calm and quiet.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the old shed"
    indoor: bool = True
    darkness: str = "dim"


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


HERO_NAMES = ["Mina", "Ivy", "Noah", "Eli", "Theo", "Luna", "Maya", "Owen"]
TRAITS = ["curious", "brave", "quiet", "gentle", "careful", "small"]


def _spooky_sound() -> str:
    return "clink-clink"


def _night_detail(setting: Setting) -> str:
    return f"The {setting.place} was dim and still, with dust floating like tiny pale ghosts."


def _ghost_voice() -> str:
    return "a soft whisper"


def _hero_intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "small"), "curious")
    world.say(
        f"{hero.id} was a small {trait} {hero.type} who noticed every little sound."
    )


def _loves_curiosity(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} liked to peek under cloths, behind boxes, and into every corner."
    )


def _arrive(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"One foggy evening, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} went to {world.setting.place}."
    )
    world.say(_night_detail(world.setting))


def _hear_sound(world: World, hero: Entity, axle: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    axle.meters["rattle"] = axle.meters.get("rattle", 0.0) + 1
    world.say(
        f"Then {hero.id} heard {_spooky_sound()} from the old wagon."
    )
    world.say(
        f"It came from the wagon's axle, which looked rusty and a little crooked."
    )


def _ghost_appears(world: World, ghost: Entity, hero: Entity, axle: Entity) -> None:
    ghost.memes["worry"] = ghost.memes.get("worry", 0.0) + 1
    hero.memes["spooked"] = hero.memes.get("spooked", 0.0) + 1
    world.say(
        f"A pale ghost drifted out of the shadows and whispered, "
        f"\"Please don't roll the wagon yet. That axle might slip.\""
    )
    world.say(
        f"{hero.id} swallowed hard and stared at the crooked axle."
    )


def _parent_warns(world: World, parent: Entity, hero: Entity, axle: Entity) -> None:
    parent.memes["caution"] = parent.memes.get("caution", 0.0) + 1
    world.say(
        f'"{hero.id}, wait," {hero.pronoun("possessive")} {parent.label_word} said. '
        f'"Old wood and a bent axle can break."'
    )


def _child_questions(world: World, hero: Entity, parent: Entity, ghost: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f'"But why is the ghost here?" {hero.id} asked.'
    )
    world.say(
        f'"To keep you safe," the ghost said. "I do not want the wagon to wobble under anyone."'
    )


def _inspect(world: World, hero: Entity, parent: Entity, axle: Entity) -> None:
    world.say(
        f"{hero.id} and {hero.pronoun('possessive')} {parent.label_word} lifted a lantern and looked closely."
    )
    axle.meters["seen"] = axle.meters.get("seen", 0.0) + 1
    axle.meters["loose"] = axle.meters.get("loose", 0.0) + 1
    world.say(
        f"The axle was loose, and one side had worn down where the wheel had rubbed."
    )


def _find_spare(world: World, spare: Entity, parent: Entity, ghost: Entity) -> None:
    spare.meters["useful"] = spare.meters.get("useful", 0.0) + 1
    world.say(
        f"The ghost pointed a pale finger at a spare axle hanging on a hook."
    )
    world.say(
        f'"That one will fit," the ghost whispered. "{parent.label_word}, you can fix it."'
    )


def _replace_axle(world: World, hero: Entity, parent: Entity, axle: Entity, spare: Entity) -> None:
    axle.meters["broken"] = 1.0
    axle.meters["fixed"] = 1.0
    spare.worn_by = None
    world.say(
        f"{hero.id} held the lantern while {hero.pronoun('possessive')} {parent.label_word} swapped the bad axle for the spare."
    )
    world.say(
        f"At last the wagon sat straight and steady."
    )


def _resolution(world: World, hero: Entity, parent: Entity, ghost: Entity, axle: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    ghost.memes["calm"] = ghost.memes.get("calm", 0.0) + 1
    world.say(
        f'{hero.id} smiled. "It is not scary now," {hero.pronoun()} said.'
    )
    world.say(
        f'The ghost gave a tiny bow and faded into the dark, and the wagon rolled with a soft, happy rattle.'
    )


SETTING = Setting(place="the old shed", indoor=True, darkness="dim")
PLACES = {
    "shed": Setting(place="the old shed", indoor=True, darkness="dim"),
    "barn": Setting(place="the barn", indoor=True, darkness="dim"),
    "garage": Setting(place="the garage", indoor=True, darkness="dim"),
}

KNOWLEDGE = {
    "axle": [
        (
            "What is an axle?",
            "An axle is the straight bar or rod that holds a wheel in place so the wheel can turn.",
        ),
    ],
    "ghost": [
        (
            "What is a ghost in a story?",
            "A ghost in a story is often a spooky-looking character who may be mysterious, but it can still be friendly.",
        ),
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the wish to find out what is hidden or to learn how something works.",
        ),
    ],
    "caution": [
        (
            "Why do people give cautionary warnings?",
            "People give cautionary warnings to help someone stay safe before something can go wrong.",
        ),
    ],
    "dialogue": [
        (
            "What is dialogue in a story?",
            "Dialogue is the talking between characters in a story, written with their exact words.",
        ),
    ],
}


def build_world(params: StoryParams) -> World:
    setting = PLACES[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["small", params.trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    ghost = world.add(Entity(id="Ghost", kind="character", type="ghost", label="the ghost"))
    wagon = world.add(Entity(id="Wagon", type="wagon", label="wagon"))
    axle = world.add(Entity(id="Axle", type="axle", label="axle", owner="Wagon"))
    spare = world.add(Entity(id="SpareAxle", type="axle", label="spare axle", protective=True))
    world.facts.update(hero=hero, parent=parent, ghost=ghost, wagon=wagon, axle=axle, spare=spare)
    _hero_intro(world, hero)
    _loves_curiosity(world, hero)
    world.para()
    _arrive(world, hero, parent)
    _hear_sound(world, hero, axle)
    _ghost_appears(world, ghost, hero, axle)
    _parent_warns(world, parent, hero, axle)
    _child_questions(world, hero, parent, ghost)
    world.para()
    _inspect(world, hero, parent, axle)
    _find_spare(world, spare, parent, ghost)
    _replace_axle(world, hero, parent, axle, spare)
    _resolution(world, hero, parent, ghost, axle)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    return [
        f'Write a short ghost story for a young child where {hero.id} hears a spooky sound in {world.setting.place} and asks questions.',
        f'Write a gentle story with dialogue where {hero.id} is curious, {parent.label_word} gives a cautionary warning, and a ghost helps fix an axle.',
        f'Write a small nighttime story about an axle, a curious child, and a friendly ghost who wants everyone to stay safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    ghost: Entity = f["ghost"]
    axle: Entity = f["axle"]
    spare: Entity = f["spare"]
    return [
        QAItem(
            question=f"Who heard the clink-clink sound in {world.setting.place}?",
            answer=f"{hero.id} heard the clink-clink sound from the wagon's axle in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did the ghost tell {hero.id} not to do?",
            answer="The ghost told the child not to roll the wagon until the axle was checked.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} tell {hero.id} to wait?",
            answer=f"{parent.label_word.capitalize()} said the old wood and bent axle could break if they pushed the wagon too soon.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They replaced the bad axle with a spare axle, and then the wagon rolled softly while the ghost faded away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"axle", "ghost", "curiosity", "caution", "dialogue"}
    out: list[QAItem] = []
    for tag in ["axle", "ghost", "curiosity", "caution", "dialogue"]:
        if tag in tags:
            for q, a in KNOWLEDGE[tag]:
                out.append(QAItem(question=q, answer=a))
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
parent(P) :- parent_kind(P).
ghost(G) :- ghost_kind(G).
axle(A) :- axle_kind(A).
spare_axle(S) :- spare_kind(S).

curious(H) :- trait(H, curious).
warned(H) :- cautionary(P, H).
heard(H) :- hears_sound(H).

needs_caution(H) :- curious(H), heard(H).
safe_fix(H) :- needs_caution(H), spare_available(S), axle_fixable(A), axle(A), spare_axle(S).

story_ok(H) :- hero(H), parent(P), ghost(G), axle(A), safe_fix(H).

#show story_ok/1.
#show needs_caution/1.
#show safe_fix/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("hero_name", "hero"))
    lines.append(asp.fact("parent_kind", "parent"))
    lines.append(asp.fact("ghost_kind", "ghost"))
    lines.append(asp.fact("axle_kind", "axle"))
    lines.append(asp.fact("spare_kind", "spare_axle"))
    lines.append(asp.fact("trait", "hero", "curious"))
    lines.append(asp.fact("hears_sound", "hero"))
    lines.append(asp.fact("cautionary", "parent", "hero"))
    lines.append(asp.fact("spare_available", "spare_axle"))
    lines.append(asp.fact("axle_fixable", "axle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/1.\n#show needs_caution/1.\n#show safe_fix/1."))
    atoms = set((s.name, tuple(a.name if a.type == s.type else a.number for a in s.arguments)) for s in model)
    expected = {("needs_caution", ("hero",)), ("safe_fix", ("hero",)), ("story_ok", ("hero",))}
    if atoms == expected:
        print("OK: ASP rules match the Python reasonableness gate.")
        return 0
    print("MISMATCH: ASP and Python do not agree.")
    print("ASP:", sorted(atoms))
    print("Expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story world about a curious child and a cautionary axle.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(PLACES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice([t for t in TRAITS if t != "small"])
    return StoryParams(place=place, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show story_ok/1.\n#show needs_caution/1.\n#show safe_fix/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/1.\n#show needs_caution/1.\n#show safe_fix/1."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="shed", name="Mina", gender="girl", parent="mother", trait="curious"),
            StoryParams(place="barn", name="Noah", gender="boy", parent="father", trait="brave"),
            StoryParams(place="garage", name="Ivy", gender="girl", parent="father", trait="quiet"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.place} ({p.gender}, {p.trait})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
