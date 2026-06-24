#!/usr/bin/env python3
"""
storyworlds/worlds/note_hijk_magic_twist_humor_folk_tale.py
============================================================

A small folk-tale storyworld about a note, the letters hijk, and a magical
twist that turns worry into humor.

The seed image is a childlike old-country tale:
- Someone finds a note.
- The note contains the curious letters hijk.
- A bit of magic makes the note matter in a surprising way.
- The twist is gentle and funny, not mean.
- The ending proves something changed in the world.

This script models the story as a little state machine with physical meters and
emotional memes, plus an ASP twin for the reasonableness gate.
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
# Core model
# ---------------------------------------------------------------------------
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("torn", "hidden", "glowing", "helped", "found"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "worry", "joy", "amusement", "relief", "wonder"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    local_color: str
    affords: set[str] = field(default_factory=set)


@dataclass
class NoteSpell:
    id: str
    title: str
    words: str
    effect: str
    twist: str
    humor: str
    requires: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    breakable: bool = False
    fixable: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.story: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.story[-1].append(text)

    def para(self) -> None:
        if self.story[-1]:
            self.story.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.story if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "cottage": Setting("the cottage", "a low stone house with a warm chimney", {"find", "read", "mend"}),
    "forest": Setting("the forest edge", "pine needles and foxglove shadows", {"find", "read", "mend"}),
    "market": Setting("the market square", "stalls, baskets, and bright cloth", {"find", "read"}),
    "barn": Setting("the old barn", "hay dust and a creaky beam", {"find", "read", "mend"}),
}

SPELLS = {
    "hijk": NoteSpell(
        id="hijk",
        title="The H-I-J-K Note",
        words="hijk",
        effect="a small spell that makes a broken thing behave in a surprising way",
        twist="the note was not a warning at all, but a joke with a kind heart",
        humor="the spell makes a grumpy object act as if it has learned to laugh",
        requires="a calm reader and a listening heart",
        tags={"magic", "twist", "humor", "note", "hijk"},
    ),
    "note": NoteSpell(
        id="note",
        title="The Plain Note",
        words="note",
        effect="a folded message that asks to be read aloud",
        twist="the message hides a second meaning",
        humor="the message ends with a silly little rhyme",
        requires="someone who will open it",
        tags={"note"},
    ),
}

PROPS = {
    "note": Prop("note", "note", "a folded note with tidy corners", breakable=False, fixable=False),
    "basket": Prop("basket", "basket", "a wicker basket", breakable=True, fixable=True),
    "shoe": Prop("shoe", "shoe", "a squeaky shoe", breakable=True, fixable=True),
    "lantern": Prop("lantern", "lantern", "a tin lantern", breakable=True, fixable=True),
}

HERO_NAMES = ["Mina", "Toma", "Lena", "Pavel", "Sana", "Ivo", "Nora", "Bela"]
GUIDE_NAMES = ["Grandmother", "Old Kestrel", "Aunt Anya", "the miller", "the neighbor"]
TRAITS = ["curious", "patient", "bright-eyed", "gentle", "clever", "wary"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    spell: str
    prop: str
    name: str
    guide: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def is_reasonable(setting: str, spell: str, prop: str) -> bool:
    if setting not in SETTINGS or spell not in SPELLS or prop not in PROPS:
        return False
    if "note" not in SPELLS[spell].tags:
        return False
    # A good folk-tale twist needs a readable object and a fixable mishap.
    return prop in {"basket", "shoe", "lantern"}


def explain_rejection(setting: str, spell: str, prop: str) -> str:
    return (
        f"(No story: the tale needs a readable note, the letters hijk, and a small "
        f"problem that can change by magic. The choice setting={setting!r}, spell={spell!r}, "
        f"prop={prop!r} does not make a complete folk-tale turn.)"
    )


def choose_name(rng: random.Random) -> tuple[str, str]:
    name = rng.choice(HERO_NAMES)
    guide = rng.choice(GUIDE_NAMES)
    return name, guide


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id="hero", kind="character", type="child", label=params.name))
    guide = world.add(Entity(id="guide", kind="character", type="adult", label=params.guide))
    prop = world.add(Entity(
        id="prop",
        type=params.prop,
        label=PROPS[params.prop].label,
        phrase=PROPS[params.prop].phrase,
    ))
    note = world.add(Entity(id="note", type="note", label="note", phrase="a folded note"))
    spell = world.add(Entity(id="spell", type="spell", label=params.spell, phrase=SPELLS[params.spell].words))

    world.facts.update(hero=hero, guide=guide, prop=prop, note=note, spell=spell, params=params)
    return world


def narrate_story(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    prop: Entity = f["prop"]
    params: StoryParams = f["params"]
    spell = SPELLS[params.spell]
    setting = world.setting

    hero.memes["curiosity"] += 1
    world.say(
        f"Once in {setting.place}, {hero.label} was a {params.trait} child who liked old stories and "
        f"quiet paths. {setting.local_color.capitalize()} made the day feel like it might hide a secret."
    )
    world.say(
        f"One morning, {hero.label} found {prop.phrase} tucked where the wind had left it. "
        f"It looked plain, but the crease held a little whisper of trouble."
    )
    world.say(
        f"When {hero.label} opened the note, the first thing inside was the word {spell.words.upper()}. "
        f"The rest of the line said it was {spell.requires}."
    )

    # tension
    hero.memes["worry"] += 1
    prop.meters["torn"] += 1
    world.say(
        f"{hero.label} nearly folded it shut again, because the letters felt strange. "
        f"Then {hero.pronoun().capitalize()} read it aloud, and the note gave a tiny warm glow."
    )

    # magical twist
    world.para()
    if params.prop == "basket":
        prop.meters["hidden"] += 1
        hero.memes["wonder"] += 1
        world.say(
            f"At once, the basket on the doorstep began to hum like a beesong. "
            f"Inside it, the bread had not vanished at all; it had been hiding under a cloth all along."
        )
        world.say(
            f"The twist was funny as well as kind: the note had not promised a treasure, only a trick "
            f"to make the missing thing appear where everyone could see it."
        )
    elif params.prop == "shoe":
        prop.meters["helped"] += 1
        hero.memes["amusement"] += 1
        world.say(
            f"Then the squeaky shoe hopped once, twice, and sat politely by the door. "
            f"It had been stuck in the mud, and the spell turned its grumble into a hop."
        )
        world.say(
            f"{hero.label} laughed so hard that the crows on the fence blinked at the sound."
        )
    else:
        prop.meters["glowing"] += 1
        hero.memes["joy"] += 1
        world.say(
            f"The tin lantern lit without fire, and its little light made the whole room look like honey."
        )
        world.say(
            f"Then the lantern tipped sideways and shone on the missing latch behind the flour barrel, "
            f"where the lost thing had been hiding the whole time."
        )

    # resolution
    world.para()
    guide.memes["relief"] += 1
    guide.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"{guide.label} came in, saw the glow, and smiled as if the old house had just told a joke. "
        f"{guide.label} said the note had always been meant for a careful reader."
    )
    world.say(
        f"So {hero.label} put the note on the shelf, now a little bent but still whole, and the house felt "
        f"warmer for it. By evening, the missing thing was found, and the letters hijk seemed less strange "
        f"than friendly."
    )
    world.say(
        f"In the end, {hero.label} kept the note as a memory of the day magic wore a grin. "
        f"The little surprise had turned worry into laughter, and the tale was better for it."
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f'Write a short folk tale about a child who finds a note with the letters "{SPELLS[p.spell].words}".',
        f"Tell a gentle magical story set in {world.setting.place} where {p.name} learns that a note can have a funny twist.",
        f"Write a child-friendly story where a mysterious note leads to a small problem, a magic surprise, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    guide: Entity = world.facts["guide"]
    prop: Entity = world.facts["prop"]
    spell = SPELLS[p.spell]

    return [
        QAItem(
            question=f"What did {hero.label} find in {world.setting.place}?",
            answer=f"{hero.label} found {prop.phrase}, and inside it was a note with the letters {spell.words.upper()}.",
        ),
        QAItem(
            question=f"Why did the note feel magical to {hero.label}?",
            answer=f"It felt magical because the note was meant to be read aloud, and the word {spell.words.upper()} made it glow with a kind of spell.",
        ),
        QAItem(
            question=f"What was the funny twist in the tale?",
            answer=f"The twist was that the note did not bring a scary warning. It was a kind joke that helped reveal what was hidden and turned worry into laughter.",
        ),
        QAItem(
            question=f"How did {hero.label} feel at the end?",
            answer=f"{hero.label} felt relieved, happy, and amused, because the note stayed safe and the problem was solved in a gentle way.",
        ),
        QAItem(
            question=f"Who helped {hero.label} understand the note?",
            answer=f"{guide.label} helped by showing that the note was meant for a careful reader who would listen closely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    spell: NoteSpell = world.facts["spell"].label and SPELLS[world.facts["params"].spell]
    return [
        QAItem(
            question="What is a note?",
            answer="A note is a short message written on paper. People use notes to tell, remind, or warn someone about something.",
        ),
        QAItem(
            question="What do the letters hijk mean in this story?",
            answer="In this story, hijk is a magic word inside the note. It is not a normal secret code; it is part of the little spell.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what the reader expected. It makes the story feel new and interesting.",
        ),
        QAItem(
            question="Why can humor help a folk tale?",
            answer="Humor can make a folk tale feel warm and friendly. A funny moment can turn a scary or worried feeling into a happy one.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_story(S, P) :- setting(S), spell(P), prop_ok(P), place_ok(S).
prop_ok(hijk).
prop_ok(note).
place_ok(cottage).
place_ok(forest).
place_ok(market).
place_ok(barn).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in SPELLS:
        lines.append(asp.fact("spell", pid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, p) for s in SETTINGS for p in SPELLS if is_reasonable(s, p, "note")}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Parameter handling
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about a magical note and the letters hijk.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--spell", choices=sorted(SPELLS))
    ap.add_argument("--prop", choices=sorted(PROPS))
    ap.add_argument("--name")
    ap.add_argument("--guide")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    spell = args.spell or rng.choice(list(SPELLS))
    prop = args.prop or rng.choice(list(PROPS))
    if args.setting and args.spell and args.prop and not is_reasonable(setting, spell, prop):
        raise StoryError(explain_rejection(setting, spell, prop))
    if not is_reasonable(setting, spell, prop):
        # keep random generation constrained to a good story.
        setting = rng.choice(list(SETTINGS))
        spell = "hijk"
        prop = rng.choice(["basket", "shoe", "lantern"])
    name = args.name or rng.choice(HERO_NAMES)
    guide = args.guide or rng.choice(GUIDE_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, spell=spell, prop=prop, name=name, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate_story(world)
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
        m = {k: v for k, v in e.meters.items() if v}
        s = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if s:
            bits.append(f"memes={s}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(setting="cottage", spell="hijk", prop="basket", name="Mina", guide="Grandmother", trait="curious"),
    StoryParams(setting="forest", spell="hijk", prop="shoe", name="Toma", guide="Old Kestrel", trait="gentle"),
    StoryParams(setting="barn", spell="hijk", prop="lantern", name="Nora", guide="Aunt Anya", trait="bright-eyed"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
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
