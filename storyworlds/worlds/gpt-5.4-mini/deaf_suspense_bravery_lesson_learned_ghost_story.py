#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/deaf_suspense_bravery_lesson_learned_ghost_story.py
===================================================================================

A standalone storyworld for a small ghost-story domain: a deaf child and a friend
hear nothing, notice eerie clues, face suspense in an old house, show bravery,
and learn that the "ghost" is a harmless helper leaving signs instead of sounds.

The world is built as a tiny causal simulation:
- typed entities with physical meters and emotional memes
- a forward-chained rule engine for suspense, fear, bravery, and discovery
- a reasonableness gate that prefers stories where the clues and the resolution
  actually fit together
- a Python/ASP twin for parity checking
- three Q&A sets grounded in world state, not rendered prose

This script is stdlib-only.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SUSPENSE_MIN = 2
BRAVERY_GOAL = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if case == "possessive":
            return "their"
        return "they" if case == "subject" else "them"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Place:
    id: str
    label: str
    dark: bool = True
    ghostly: bool = True
    echoes: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    revealed_by: str
    hint_text: str
    comfort_text: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Help:
    id: str
    label: str
    kind: str
    method: str
    is_real: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    place = world.facts.get("place")
    if not place:
        return out
    if not place.dark:
        return out
    sig = ("suspense", place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.characters():
        if kid.role in {"hero", "friend"}:
            kid.memes["suspense"] += 1
            kid.memes["fear"] += 1
    out.append("__suspense__")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    clue = world.facts.get("clue")
    if not hero or not clue:
        return out
    if hero.memes["courage"] < BRAVERY_GOAL:
        return out
    sig = ("bravery", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["brave"] += 1
    out.append("__bravery__")
    return out


def _r_discovery(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("clue")
    if not clue:
        return out
    if clue.id in world.fired:
        return out
    if world.facts.get("investigated") and world.facts.get("help"):
        world.fired.add(clue.id)
        world.facts["ghost_help"] = True
        out.append("__discovery__")
    return out


CAUSAL_RULES = [
    Rule("suspense", "emotional", _r_suspense),
    Rule("bravery", "emotional", _r_bravery),
    Rule("discovery", "plot", _r_discovery),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(place: Place, clue: Clue, help_item: Help) -> bool:
    return place.dark and clue.kind == "soundless_sign" and help_item.is_real


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for cid, clue in CLUES.items():
            for hid, help_item in HELPS.items():
                if reasonableness_ok(place, clue, help_item):
                    combos.append((pid, cid, hid))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    clue: str
    help_item: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    adult: str
    trait: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def tell(place: Place, clue: Clue, help_item: Help, hero_name: str = "Mina",
         hero_gender: str = "girl", friend_name: str = "Theo",
         friend_gender: str = "boy", adult_type: str = "mother",
         trait: str = "careful") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender,
                            role="hero", traits=["deaf", trait]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender,
                              role="friend", traits=["curious"]))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type,
                             role="adult", label="the adult"))
    world.add(Entity(id=place.id, type="place", label=place.label))
    clue_ent = world.add(Entity(id=clue.id, type="clue", label=clue.label))
    help_ent = world.add(Entity(id=help_item.id, type="help", label=help_item.label))
    world.facts.update(place=place, clue=clue_ent, help=help_ent, hero=hero, friend=friend, adult=adult)

    hero.memes["courage"] = 1.0 if trait in {"careful", "cautious"} else 2.0
    friend.memes["courage"] = 1.0
    world.say(
        f"On a windy evening, {hero.id} and {friend.id} slipped into {place.label}. "
        f"{hero.id} was deaf, so the old house did not speak to {hero.pronoun('object')} in words; it only answered with shadows and tiny signs."
    )
    world.say(
        f"Then they saw {clue.hint_text}. {friend.id} froze, but {hero.id} lifted "
        f"{hero.pronoun('possessive')} chin and looked again."
    )
    world.para()
    world.say(
        f'"Something is here," {friend.id} whispered. {hero.id} could not hear the whisper, '
        f'but {hero.pronoun()} could read {friend.id}\'s wide eyes and the careful way '
        f'{friend.id} pointed toward the hall.'
    )
    hero.memes["curiosity"] += 1
    friend.memes["fear"] += 1
    world.facts["investigated"] = True
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} took a brave step forward and followed the clue to the hallway. "
        f"{hero.pronoun().capitalize()} found {clue.comfort_text}."
    )
    world.facts["help"] = help_ent
    if help_item.kind == "lantern":
        world.say(
            f"In the dim light, {hero.id} noticed the lantern had been left near the stairs, "
            f"and beside it was a note with a smiley face drawn in blue ink."
        )
    else:
        world.say(
            f"Near the end of the hall, {hero.id} found a small sign that pointed to a hidden door, "
            f"as if someone wanted them to be brave and keep going."
        )
    world.para()
    world.say(
        f"{hero.id} opened the little door. Inside was not a monster at all, but a kind neighbor "
        f"who had been leaving careful signs because the family could not hear knocking."
    )
    world.facts["ghost_help"] = True
    if clue.kind == "soundless_sign":
        world.say(
            f"The strange 'ghost' was only a helpful game of clues, and the last sign explained everything."
        )
    world.say(
        f'{adult.label_word.capitalize()} came in, hugged both children, and said, '
        f'"You were scared, but you kept looking. That was brave."'
    )
    for kid in (hero, friend):
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["joy"] += 1
    world.say(
        f"By the end, the dark house felt less spooky. The window glowed, the lantern sat safely on the table, "
        f"and {hero.id} smiled because {hero.pronoun()} had learned that courage can help a deaf child read a mystery without hearing a sound."
    )

    world.facts.update(
        outcome="solved",
        lesson_learned=True,
        brave=hero.memes["brave"] >= 1,
    )
    return world


PLACES = {
    "old_house": Place("old_house", "the old house", dark=True, ghostly=True, echoes=False),
    "attic": Place("attic", "the attic", dark=True, ghostly=True, echoes=True),
    "hall": Place("hall", "the long hall", dark=True, ghostly=True, echoes=False),
}

CLUES = {
    "footprints": Clue("footprints", "dusty footprints", "soundless_sign", "a trail of dust", "They were a clue that someone had walked there.", "The footprints meant the mystery could be solved step by step."),
    "lantern_note": Clue("lantern_note", "a lantern with a note", "soundless_sign", "a glowing lantern", "It looked like a message left by a ghost.", "The note showed the ghost was trying to help, not frighten anyone."),
    "wind_chimes": Clue("wind_chimes", "wind chimes tapping softly", "soundless_sign", "a moving window", "The silver chimes trembled without a voice.", "The chimes pointed to an open window and a gentle helper."),
}

HELPS = {
    "lantern": Help("lantern", "a warm lantern", "light", "carry into the dark hall", True),
    "flashlight": Help("flashlight", "a bright flashlight", "light", "shine on the clue", True),
    "paper_sign": Help("paper_sign", "a paper sign", "message", "leave a note for later", True),
}

GIRL_NAMES = ["Mina", "Lily", "Ava", "Nora", "Zoe", "Maya"]
BOY_NAMES = ["Theo", "Ben", "Max", "Eli", "Noah", "Sam"]
TRAITS = ["careful", "cautious", "curious", "steady", "brave"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a ghost story for a young child where {f['hero'].id}, who is deaf, notices a strange clue in {f['place'].label}.",
        f"Tell a suspenseful story with bravery and a lesson learned, where {f['hero'].id} follows a silent sign instead of a voice.",
        f"Write a gentle ghost story that includes the word 'deaf' and ends with the mystery becoming kind instead of scary.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    place = f["place"]
    clue = f["clue"]
    adult = f["adult"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, who went into {place.label} and found a strange clue. {hero.id} was deaf, so {hero.pronoun()} watched closely for signs instead of sounds."),
        ("Why was the story suspenseful?",
         f"It was suspenseful because the old house was dark and the children did not know what left the clue. That mystery made every shadow feel important until they looked closely."),
        ("What did {0} do that was brave?".format(hero.id),
         f"{hero.id} kept going even though the house felt spooky. {hero.pronoun().capitalize()} followed the clue and opened the little door instead of running away."),
        ("What lesson did they learn?",
         f"They learned that a scary-looking mystery can have a kind explanation. They also learned that a deaf child can solve a puzzle by watching carefully and staying brave."),
        ("How did the adult respond?",
         f"{adult.id} hugged them and said they were brave. The adult was happy because the children did not give up when the house felt eerie."),
    ]
    if f.get("ghost_help"):
        qa.append((
            "Was the ghost real?",
            "The story only seemed like a ghost story at first. In the end, the mystery turned out to be a harmless helper leaving silent signs, not a monster."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {f["clue"].id, f["help"].id, f["place"].id, "deaf", "bravery", "suspense", "lesson"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


KNOWLEDGE = {
    "deaf": [("What does deaf mean?",
              "Deaf means a person cannot hear sounds. They may use signs, reading, and watching faces to understand what is happening.")],
    "bravery": [("What is bravery?",
                 "Bravery means doing something even when you feel scared. It does not mean you are never afraid; it means you keep going carefully.")],
    "suspense": [("What is suspense?",
                  "Suspense is the feeling of wondering what will happen next. A story feels suspenseful when you are waiting to find out a secret.")],
    "lesson": [("What is a lesson learned in a story?",
                "A lesson learned is the idea the characters understand by the end. It is something useful they will remember later.")],
    "lantern": [("What is a lantern?",
                 "A lantern is a light that can help people see in the dark. It can be safe when it uses a battery or another grown-up source.")],
    "flashlight": [("What is a flashlight?",
                    "A flashlight is a small light you turn on with a button. It shines without fire.")],
    "old_house": [("What is an old house?",
                   "An old house is a house that has been around for a long time. It can creak, echo, and feel spooky at night.")],
}
KNOWLEDGE_ORDER = ["deaf", "suspense", "bravery", "lesson", "lantern", "flashlight", "old_house"]


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, clue: Clue, help_item: Help) -> str:
    return "(No story: this combination does not make a sensible silent-ghost mystery.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dark:
            lines.append(asp.fact("dark", pid))
        if p.ghostly:
            lines.append(asp.fact("ghostly", pid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("kind", cid, c.kind))
    for hid, h in HELPS.items():
        lines.append(asp.fact("help", hid))
        if h.is_real:
            lines.append(asp.fact("real", hid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, C, H) :- place(P), dark(P), clue(C), kind(C, soundless_sign), help(H), real(H).
"""


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid combos:")
        print("  only in python:", sorted(py - cl))
        print("  only in clingo:", sorted(cl - py))
        rc = 1

    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, clue=None, help_item=None, hero=None, hero_gender=None, friend=None, friend_gender=None, adult=None, trait=None, seed=None), random.Random(777)))
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with a deaf child, suspense, bravery, and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--help-item", dest="help_item", choices=HELPS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.help_item is None or c[2] == args.help_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, help_item = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    adult = args.adult or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, clue, help_item, hero, hero_gender, friend, friend_gender, adult, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CLUES[params.clue], HELPS[params.help_item],
                 params.hero, params.hero_gender, params.friend, params.friend_gender,
                 params.adult, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    StoryParams("old_house", "footprints", "lantern", "Mina", "girl", "Theo", "boy", "mother", "careful"),
    StoryParams("attic", "lantern_note", "flashlight", "Lily", "girl", "Max", "boy", "father", "curious"),
    StoryParams("hall", "wind_chimes", "paper_sign", "Noah", "boy", "Ava", "girl", "mother", "brave"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (place, clue, help) combos:")
        for p, c, h in asp_valid_combos():
            print(f"  {p:10} {c:14} {h}")
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
