#!/usr/bin/env python3
"""
A small storyworld about a castle, a bit of magic, a hurt feeling, and a kind
repair. The tale is written in a gentle rhyming style and driven by a simple
world model so the ending changes what the characters feel and do.
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

TITLE = "castle_magic_reconciliation_inner_monologue_rhyming_story"

CASTLE_NAMES = [
    "Moongate Castle",
    "Pebblekeep Castle",
    "Rosewind Castle",
    "Brighttower Castle",
    "Candlebrook Castle",
]

CHARACTER_NAMES = ["Milo", "Nia", "Oren", "Pia", "Lina", "Jasper", "Tessa", "Bram"]
ROLES = ["young page", "small helper", "castle child", "apprentice", "messenger"]
MAGIC_OBJECTS = ["a silver bell", "a tiny wand", "a ribbon star", "a glowing key", "a warm lantern"]
SPELLS = ["sparkle a door open", "mend a torn banner", "make a pebble sing", "light a dark stair", "turn crumbs to crumbs of gold"]
FEELINGS = ["sad", "cross", "hurt", "lonely", "worried"]
FIXES = ["say sorry", "share the spell", "listen carefully", "give back the charm", "make it right"]
RHYMES = {
    "castle": "brassel",
    "magic": "tragic",
    "reconciliation": "restoration",
    "monologue": "dialogue",
    "spark": "lark",
    "glow": "flow",
    "stone": "tone",
    "light": "bright",
    "heart": "start",
    "kind": "mind",
}

ASP_RULES = r"""
castle(castle_one).
room(courtyard).
room(hall).
room(tower).
character(hero).
character(friend).
magic_item(charm).
feeling(sad).
feeling(hurt).

can_use_magic(hero,charm).
can_break_trust(hero,friend) :- can_use_magic(hero,charm).
needs_reconciliation(hero,friend) :- can_break_trust(hero,friend), feeling(hurt).
can_reconcile(hero,friend) :- needs_reconciliation(hero,friend).
resolved(hero,friend) :- can_reconcile(hero,friend).
#show needs_reconciliation/2.
#show resolved/2.
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    castle: str
    hero: str
    friend: str
    role: str
    magic_object: str
    spell: str
    feeling: str
    fix: str
    seed: Optional[int] = None


@dataclass
class World:
    castle: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Castle magic reconciliation rhyming storyworld.")
    ap.add_argument("--castle", choices=["castle"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    castle = args.castle or "castle"
    hero = rng.choice(CHARACTER_NAMES)
    friend = rng.choice([n for n in CHARACTER_NAMES if n != hero])
    role = rng.choice(ROLES)
    magic_object = rng.choice(MAGIC_OBJECTS)
    spell = rng.choice(SPELLS)
    feeling = rng.choice(FEELINGS)
    fix = rng.choice(FIXES)
    return StoryParams(
        castle=castle,
        hero=hero,
        friend=friend,
        role=role,
        magic_object=magic_object,
        spell=spell,
        feeling=feeling,
        fix=fix,
    )


def _build_world(params: StoryParams) -> World:
    world = World(castle=CASTLE_NAMES[0])
    hero = world.add(Entity(id=params.hero, kind="character", type=params.role, label=params.hero))
    friend = world.add(Entity(id=params.friend, kind="character", type="friend", label=params.friend))
    charm = world.add(Entity(id="charm", type="magic_object", label=params.magic_object, phrase=params.magic_object, owner=hero.id))
    hero.memes["joy"] = 1
    friend.memes["trust"] = 1
    world.facts.update(hero=hero, friend=friend, charm=charm, params=params)
    return world


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    charm: Entity = world.facts["charm"]

    world.say(f"In {world.castle}, {hero.id} was small and spry,")
    world.say(f"With {charm.label} in hand and a twinkle in eye.")
    world.say(f"{hero.id} loved one spell and liked its bright tune,")
    world.say(f"To {params.spell} by morning or by moon.")

    world.para()
    world.say(f"But {friend.id} came near with a worried face,")
    world.say(f"For the magic had happened too quickly in place.")
    friend.memes[params.feeling] = 1
    hero.memes["pride"] = 1
    world.say(f"Inside {hero.id}'s heart came a hush and a hum,")
    world.say(f"An inner monologue: 'Oh no, what have I done?'")

    world.para()
    world.say(f"'I felt so {params.feeling},' thought {hero.id} with care,")
    world.say(f"'Yet I can make room for a kinder repair.'")
    hero.memes["remorse"] = 1
    friend.memes["hurt"] = 1
    world.say(f"{hero.id} chose to {params.fix}, soft as a dove,")
    world.say(f"And offered the charm with apology and love.")

    world.para()
    friend.memes["forgive"] = 1
    friend.memes["hurt"] = 0
    hero.memes["peace"] = 1
    hero.memes["remorse"] = 0
    world.say(f"{friend.id} smiled, and the cloud drifted light,")
    world.say(f"Reconciliation glimmered, warm and bright.")
    world.say(f"They shared the spell, and the castle rang clear,")
    world.say(f"With laughter and trust blooming near.")

    world.facts["resolved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short rhyming story set in a castle where {p.hero} uses magic and then makes things right.',
        f"Tell a gentle castle tale about {p.hero} and {p.friend} with an inner monologue, a mistake, and reconciliation.",
        f'Write a child-friendly rhyme using the word "castle" and ending in a kind apology.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    qa = [
        QAItem(
            question=f"Where does the story happen?",
            answer=f"It happens in {world.castle}, a castle where {p.hero} and {p.friend} can meet, worry, and then mend things together.",
        ),
        QAItem(
            question=f"What did {p.hero} want to do with the magic?",
            answer=f"{p.hero} wanted to {p.spell}, because the magic object made the spell feel exciting and new.",
        ),
        QAItem(
            question=f"How did {p.hero} feel after the problem?",
            answer=f"{p.hero} felt {p.feeling} at first, and then felt peaceful after choosing to {p.fix}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {p.hero} and {p.friend} were reconciled, the hurt was gone, and they shared the magic kindly.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a castle?",
            answer="A castle is a large strong building with walls and rooms where people can live or gather in a story.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset, make peace, and feel close again after a hurt feeling.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talking someone does in their own mind when they think about what to do.",
        ),
        QAItem(
            question="Why can magic be tricky in a story?",
            answer="Magic can be tricky because it can change things very fast, so someone may need to think carefully before using it.",
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
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(castle="castle", hero="Milo", friend="Nia", role="young page", magic_object="a silver bell", spell="sparkle a door open", feeling="sad", fix="say sorry"),
    StoryParams(castle="castle", hero="Lina", friend="Oren", role="apprentice", magic_object="a glowing key", spell="light a dark stair", feeling="hurt", fix="listen carefully"),
]


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("castle", "castle_one"),
        asp.fact("character", "hero"),
        asp.fact("character", "friend"),
        asp.fact("magic_item", "charm"),
        asp.fact("feeling", "sad"),
        asp.fact("feeling", "hurt"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/2."))
    atoms = set(asp.atoms(model, "resolved"))
    expected = {("hero", "friend")}
    if atoms == expected:
        print("OK: ASP twin matches the reasonableness gate.")
        return 0
    print("MISMATCH:", sorted(atoms), "expected", sorted(expected))
    return 1


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
        print(asp_program("#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/2."))
        print(sorted(set(asp.atoms(model, "resolved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
