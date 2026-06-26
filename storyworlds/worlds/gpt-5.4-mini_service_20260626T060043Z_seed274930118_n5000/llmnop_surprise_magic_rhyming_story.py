#!/usr/bin/env python3
"""
A tiny storyworld for a Rhyming Story with Surprise and Magic.

Seed premise:
A child finds a surprise note and a small magic show begins. The child tries
to keep the rhythm, learns the surprise is a friendly one, and ends with a
bright little rhyme.

This world models a small simulated domain with physical meters and emotional
memes:
- meter: sparkle, wobble, tidy, bright
- meme: wonder, worry, delight, calm

The story is generated from world state, not from a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

VOWEL_RE = re.compile(r"^[aeiou]", re.I)


def a_an(word: str) -> str:
    return "an" if VOWEL_RE.match(word) else "a"


def title_case(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


# ---------------------------------------------------------------------------
# Entities and world state
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    label: str = ""
    type: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("sparkle", "wobble", "tidy", "bright"):
            self.meters.setdefault(key, 0.0)
        for key in ("wonder", "worry", "delight", "calm", "pride"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    place: str
    hero_name: str
    hero_type: str
    helper_type: str
    surprise: str
    magic_item: str
    rhyme_word: str
    mood: str = "quiet"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        clone = World(
            place=self.place,
            hero_name=self.hero_name,
            hero_type=self.hero_type,
            helper_type=self.helper_type,
            surprise=self.surprise,
            magic_item=self.magic_item,
            rhyme_word=self.rhyme_word,
            mood=self.mood,
        )
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class Place:
    id: str
    label: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    verb: str
    reveal: str
    spark: str
    tag: str


@dataclass
class Magic:
    id: str
    label: str
    action: str
    shine: str
    rhyme: str
    tag: str


PLACES = {
    "room": Place("room", "the cozy room", "quiet", {"surprise", "magic"}),
    "garden": Place("garden", "the small garden", "fresh", {"surprise", "magic"}),
    "stage": Place("stage", "the tiny stage", "bright", {"surprise", "magic"}),
}

SURPRISES = {
    "note": Surprise(
        "note",
        "a folded note",
        "find",
        "It said, “Try the rhyme, and look behind the little door.”",
        "a secret",
        "note",
    ),
    "box": Surprise(
        "box",
        "a painted box",
        "open",
        "Inside was a ribbon and a glimmering coin.",
        "a hidden thing",
        "box",
    ),
    "hat": Surprise(
        "hat",
        "a floppy hat",
        "lift",
        "Under it, a star-shaped card smiled up at them.",
        "a surprise",
        "hat",
    ),
}

MAGICS = {
    "bell": Magic(
        "bell",
        "a silver bell",
        "ring",
        "It chimed in a twinkly line.",
        "ding and sing",
        "bell",
    ),
    "wand": Magic(
        "wand",
        "a tiny wand",
        "wave",
        "It made a ribbon loop like a bird.",
        "glow and show",
        "wand",
    ),
    "book": Magic(
        "book",
        "a blue spell book",
        "whisper to",
        "Its pages rustled and a picture blinked awake.",
        "wink and think",
        "book",
    ),
}

RHYMES = [
    "glow",
    "show",
    "sing",
    "ring",
    "bright",
    "light",
    "twirl",
    "sparkle",
]

HERO_NAMES = ["Mia", "Lily", "Noah", "Theo", "Ava", "Zoe", "Eli", "Nora"]
HERO_TYPES = ["girl", "boy"]
HELPER_TYPES = ["mother", "father", "friend"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the place affords both surprise and magic.
valid(Place, Surprise, Magic) :- place(Place), surprise(Surprise), magic(Magic),
                                 affords(Place, surprise), affords(Place, magic).

% A compatible surprise and magic pair should have distinct tags so the story
% feels like a turn, not a repetition.
interesting(Place, S, M) :- valid(Place, S, M), surprise_tag(S, TS), magic_tag(M, TM), TS != TM.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("surprise_tag", sid, s.tag))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("magic_tag", mid, m.tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only python:", sorted(py - cl))
    print(" only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES.values():
        for s in SURPRISES.values():
            for m in MAGICS.values():
                if "surprise" in place.affords and "magic" in place.affords:
                    if s.tag != m.tag:
                        combos.append((place.id, s.id, m.id))
    return combos


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def setup_world(params: "StoryParams") -> World:
    world = World(
        place=PLACES[params.place].label,
        hero_name=params.name,
        hero_type=params.hero_type,
        helper_type=params.helper_type,
        surprise=params.surprise,
        magic_item=params.magic,
        rhyme_word=params.rhyme_word,
    )
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_type))
    surprise = world.add(Entity(id="surprise", kind="thing", type=params.surprise, label=SURPRISES[params.surprise].label))
    magic = world.add(Entity(id="magic", kind="thing", type=params.magic, label=MAGICS[params.magic].label))
    note = world.add(Entity(id="note", kind="thing", type="note", label="the note"))

    world.facts.update(hero=hero, helper=helper, surprise=surprise, magic=magic, note=note)
    return world


def predict_turn(world: World) -> bool:
    sim = world.copy()
    hero = sim.get("hero")
    surprise = sim.get("surprise")
    magic = sim.get("magic")
    hero.memes["wonder"] += 1
    surprise.meters["sparkle"] += 1
    magic.meters["bright"] += 1
    return surprise.meters["sparkle"] >= THRESHOLD and magic.meters["bright"] >= THRESHOLD


def open_story(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    world.say(
        f"At {world.place}, {hero.label} was quiet and small, with a heart that liked to hum."
    )
    world.say(
        f"{hero.label} loved a little rhyme, a gentle chime, and a shining thing to come."
    )
    world.say(
        f"{helper.label.capitalize()} smiled nearby and said, “Come close; I have something to show.”"
    )


def surprise_beats(world: World) -> None:
    hero = world.get("hero")
    surprise = world.get("surprise")
    helper = world.get("helper")
    s = SURPRISES[world.surprise]
    world.para()
    hero.memes["wonder"] += 1
    surprise.meters["sparkle"] += 1
    world.say(
        f"Then came a little surprise: {s.label} to {s.verb}, with a hush and a glow."
    )
    world.say(
        f"{s.reveal} {hero.label} blinked, then laughed, because the secret felt kind, not scary."
    )
    helper.memes["calm"] += 1


def magic_turn(world: World) -> None:
    hero = world.get("hero")
    magic = world.get("magic")
    m = MAGICS[world.magic_item]
    world.para()
    magic.meters["bright"] += 1
    hero.memes["worry"] = 0.0
    hero.memes["delight"] += 1
    world.say(
        f"Next came {m.label}; to {m.action} was all it took, and the room grew merry and airy."
    )
    world.say(
        f"{m.shine} The air made room for a tiny tune, and the tune began to rhyme."
    )


def rhyming_end(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    world.para()
    hero.memes["calm"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.label} answered with a bright little line, using the word “{world.rhyme_word}” at the end."
    )
    world.say(
        f"{hero.label.capitalize()} and {helper.label} sang it twice, then once again, till the rhyme would bend."
    )
    world.say(
        f"And so the surprise stayed sweet, the magic stayed neat, and the evening shone like a friend."
    )


def tell_story(params: "StoryParams") -> World:
    world = setup_world(params)
    open_story(world)
    surprise_beats(world)
    magic_turn(world)
    rhyming_end(world)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    surprise: str
    magic: str
    rhyme_word: str
    name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming Story world with Surprise and Magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--rhyme-word", choices=RHYMES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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
    if args.surprise and args.magic:
        if (args.place is None):
            pass
        else:
            combo = (args.place, args.surprise, args.magic)
            if combo not in valid_combos():
                raise StoryError("No valid story for that place/surprise/magic combination.")
    choices = valid_combos()
    if args.place:
        choices = [c for c in choices if c[0] == args.place]
    if args.surprise:
        choices = [c for c in choices if c[1] == args.surprise]
    if args.magic:
        choices = [c for c in choices if c[2] == args.magic]
    if not choices:
        raise StoryError("No valid combination matches the given options.")
    place, surprise, magic = rng.choice(sorted(choices))
    rhyme_word = args.rhyme_word or rng.choice(RHYMES)
    name = args.name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    return StoryParams(
        place=place,
        surprise=surprise,
        magic=magic,
        rhyme_word=rhyme_word,
        name=name,
        hero_type=hero_type,
        helper_type=helper_type,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a short Rhyming Story about {world.hero_name} at {world.place} with a surprise and magic.',
        f"Tell a child-friendly story where {world.hero_name} finds {SURPRISES[world.surprise].label} and then uses {MAGICS[world.magic_item].label}.",
        f'Write a gentle rhyme that ends with the word "{world.rhyme_word}" and includes a happy surprise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, who is with {helper.label.capitalize()} at {world.place}.",
        ),
        QAItem(
            question=f"What surprise appears in the story?",
            answer=f"The surprise is {SURPRISES[world.surprise].label}, and it brings a friendly turn to the day.",
        ),
        QAItem(
            question=f"What kind of magic is used?",
            answer=f"The magic comes from {MAGICS[world.magic_item].label}, which helps the story sparkle and rhyme.",
        ),
        QAItem(
            question=f"How does the story end?",
            answer=f"It ends with {hero.label} and {helper.label} sharing a happy rhyme and feeling calm and proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you do not expect, so it can make a moment feel exciting or new.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is a special pretend power that can make strange, bright, or wonderful things happen.",
        ),
        QAItem(
            question="What does it mean to rhyme?",
            answer="To rhyme means two words or lines end with the same sound, like glow and show.",
        ),
        QAItem(
            question="Why do children like rhyming stories?",
            answer="Children like rhyming stories because the beat is fun to hear and easy to remember.",
        ),
        QAItem(
            question="What does a silver bell do?",
            answer="A silver bell makes a clear dinging sound when it is rung.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==", ""]
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams(place="room", surprise="note", magic="bell", rhyme_word="glow", name="Mia", hero_type="girl", helper_type="mother"),
    StoryParams(place="garden", surprise="box", magic="wand", rhyme_word="show", name="Noah", hero_type="boy", helper_type="father"),
    StoryParams(place="stage", surprise="hat", magic="book", rhyme_word="ring", name="Ava", hero_type="girl", helper_type="friend"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible (place, surprise, magic) combos:\n")
        for p, s, m in combos:
            print(f"  {p:8} {s:8} {m:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: surprise={p.surprise}, magic={p.magic}, place={p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
