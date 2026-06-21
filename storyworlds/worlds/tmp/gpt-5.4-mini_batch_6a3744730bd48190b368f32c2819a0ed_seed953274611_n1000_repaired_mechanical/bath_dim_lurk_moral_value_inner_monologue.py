#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bath_dim_lurk_moral_value_inner_monologue.py
============================================================================

A tiny whodunit-style storyworld about a dim bathroom, a lurking mystery, and
a moral choice: tell the truth, help someone, and fix the mess before bedtime.

The domain is deliberately small:
- a child notices a bath-dim room
- something seems to lurk near the tub
- the mystery is solved by observation, inner monologue, and dialogue
- the ending proves what changed in the world state

The script follows the Storyweavers contract:
- standalone stdlib script
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily in ASP helpers
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- generates three QA sets from simulated world state
- includes a Python reasonableness gate and inline ASP twin

This world is not a frozen paragraph with swapped nouns; the story is driven by
state changes in meters and memes.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SIGHT_MIN = 1.0
MORAL_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    label: str
    dim_phrase: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    hidden: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Suspect:
    id: str
    label: str
    alibi: str
    secret: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Resolution:
    id: str
    method: str
    reveal: str
    fix: str
    lesson: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    setting: str
    clue: str
    suspect: str
    resolution: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


SETTINGS = {
    "bathroom": Setting(id="bathroom", label="the bathroom", dim_phrase="bath-dim", tags={"bath-dim", "bathroom"}),
    "nursery": Setting(id="nursery", label="the nursery bathroom", dim_phrase="bath-dim", tags={"bath-dim", "bathroom"}),
    "hallway": Setting(id="hallway", label="the hallway bathroom", dim_phrase="bath-dim", tags={"bath-dim", "bathroom"}),
}

CLUES = {
    "soap": Clue(id="soap", label="soap bar", phrase="a soap bar slid near the tub", hidden=False, tags={"soap", "slip"}),
    "towel": Clue(id="towel", label="towel", phrase="a towel lay half-dropped on the floor", hidden=False, tags={"towel", "wet"}),
    "toy": Clue(id="toy", label="toy boat", phrase="a toy boat bobbed by the sink", hidden=True, tags={"toy", "boat"}),
}

SUSPECTS = {
    "cat": Suspect(id="cat", label="the cat", alibi="had been sleeping on the rug", secret="lured by the warm steam", tags={"cat", "lurk"}),
    "brother": Suspect(id="brother", label="older brother", alibi="had gone for a cup of water", secret="came back to confess about the spill", tags={"brother", "moral"}),
    "wind": Suspect(id="wind", label="the window wind", alibi="had rattled the curtain", secret="moved the toy boat", tags={"wind", "lurk"}),
}

RESOLUTIONS = {
    "confess": Resolution(id="confess", method="confess and clean", reveal="admitted the mistake", fix="wiped the floor and picked up the clue", lesson="telling the truth helps", tags={"moral", "dialogue"}),
    "fetch": Resolution(id="fetch", method="fetch a towel", reveal="noticed the clue", fix="dried the wet tile and opened the curtain", lesson="careful looking solves puzzles", tags={"dialogue"}),
    "ask": Resolution(id="ask", method="ask a grown-up", reveal="called for help", fix="brought a lamp and checked the room", lesson="asking for help is wise", tags={"dialogue", "moral"}),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Tess", "Ada", "Ivy"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Finn", "Leo", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for c in CLUES:
            for u in SUSPECTS:
                out.append((s, c, u))
    return out


def resolve_rejection(params: StoryParams) -> str:
    return "(No story: the choices should still leave a mystery, a clue, and a way to resolve it.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld: bath-dim mystery with moral value and inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.clue and args.suspect:
        pass
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    resolution = args.resolution or rng.choice(list(RESOLUTIONS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or _pick_name(rng, hero_gender)
    helper = args.helper or _pick_name(rng, helper_gender)
    if hero == helper:
        helper = _pick_name(rng, helper_gender)
    return StoryParams(
        setting=setting,
        clue=clue,
        suspect=suspect,
        resolution=resolution,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if params.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    if params.resolution not in RESOLUTIONS:
        raise StoryError("Unknown resolution.")


def _setup(world: World, p: StoryParams) -> None:
    hero = world.add(Entity(id=p.hero, kind="character", type=p.hero_gender, role="hero"))
    helper = world.add(Entity(id=p.helper, kind="character", type=p.helper_gender, role="helper"))
    room = world.add(Entity(id="room", type="room", label=SETTINGS[p.setting].label))
    clue = world.add(Entity(id="clue", type="thing", label=CLUES[p.clue].label, tags=set(CLUES[p.clue].tags)))
    suspect = world.add(Entity(id="suspect", type="person", label=SUSPECTS[p.suspect].label, tags=set(SUSPECTS[p.suspect].tags)))
    world.facts.update(hero=hero, helper=helper, room=room, clue=clue, suspect=suspect, params=p)


def _investigate(world: World) -> None:
    p: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    clue: Entity = world.facts["clue"]
    suspect: Entity = world.facts["suspect"]
    room: Entity = world.facts["room"]

    room.meters["dim"] += 1
    room.memes["unease"] += 1
    clue.meters["noticed"] += 1
    hero.memes["curiosity"] += 1
    helper.memes["watchful"] += 1

    world.say(f"It was {SETTINGS[p.setting].dim_phrase} in {SETTINGS[p.setting].label}, and that made the tiles look almost secret.")
    world.say(f"{hero.id} narrowed {hero.pronoun('possessive')} eyes. '{clue.label_word.capitalize()}?' {hero.id} thought. 'Something is out of place here.'")
    world.say(f"{hero.id} whispered, 'Do you hear that? Something is trying to lurk in the dark.'")
    world.say(f"{helper.id} looked around and said, 'Then let's solve it before bedtime.'")


def _inner_monologue(world: World) -> None:
    p: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    suspect: Entity = world.facts["suspect"]
    world.say(f"{hero.id} thought, 'If the clue moved, then someone or something must have passed by this spot.'")
    world.say(f"{hero.id} thought again, 'But who would lurk near the bath-dim tub? I need a fair answer, not a guess.'")
    world.say(f"{hero.id} listened to the quiet and remembered that a good detective should tell the truth, even when the truth is small.")


def _dialogue_and_reveal(world: World) -> None:
    p: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    clue: Entity = world.facts["clue"]
    suspect: Entity = world.facts["suspect"]
    res = RESOLUTIONS[p.resolution]

    if p.resolution == "confess":
        suspect.memes["guilt"] += 1
        world.say(f"'{res.method},' {helper.id} said. 'Let's ask who was here.'")
        world.say(f"'{I can explain!}' said {suspect.label}.")
        world.say(f"{suspect.label} {res.reveal}, and that was the whodunit answer all along.")
    elif p.resolution == "fetch":
        world.say(f"'{res.method},' {helper.id} said. 'The clue will tell us the rest.'")
        world.say(f"{hero.id} leaned closer and saw that the {clue.label} had been nudged by someone in a hurry.")
        world.say(f"'{suspect.label.capitalize()} did it,' {hero.id} said softly, 'and now we know why the room felt so strange.'")
    else:
        world.say(f"'{res.method},' {helper.id} said. 'A grown-up can help us check the shadowy corner.'")
        world.say(f"The lamp came on, and the supposed lurk turned out to be {suspect.label}.")
        world.say(f"{suspect.label.capitalize()} was not a monster at all; {suspect.secret}.")


def _resolve(world: World) -> None:
    p: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    clue: Entity = world.facts["clue"]
    room: Entity = world.facts["room"]
    suspect: Entity = world.facts["suspect"]
    res = RESOLUTIONS[p.resolution]

    room.meters["dim"] = 0.0
    room.memes["unease"] = 0.0
    clue.meters["noticed"] += 1
    hero.memes["moral"] += 1
    helper.memes["moral"] += 1
    world.say(f"Then they did what {res.method} asked for: {res.fix}.")
    world.say(f"The room felt different after that -- less bath-dim, less eerie, and much more honest.")
    world.say(f"{hero.id} breathed out. '{res.lesson},' {hero.id} thought, and {helper.id} nodded.")


def tell(p: StoryParams) -> World:
    world = World()
    _setup(world, p)
    _investigate(world)
    world.para()
    _inner_monologue(world)
    world.para()
    _dialogue_and_reveal(world)
    world.para()
    _resolve(world)
    world.facts["outcome"] = "solved"
    return world


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a whodunit story for a child that uses the words 'bath-dim' and 'lurk'.",
        f"Tell a small mystery where {p.hero} notices something bath-dim in the bathroom and wonders who lurks there.",
        f"Write a story with inner monologue and dialogue where a child solves a bathroom mystery and chooses a moral answer.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    p: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    suspect: Entity = world.facts["suspect"]
    clue: Entity = world.facts["clue"]
    room: Entity = world.facts["room"]
    return [
        ("What kind of story is this?", "It is a little whodunit mystery about a dim bathroom, a clue, and a question of who was there."),
        ("What did the hero notice?", f"{hero.id} noticed that the room felt {SETTINGS[p.setting].dim_phrase}, and {clue.label_word} looked out of place."),
        ("What did the hero think about?", f"{hero.id} kept wondering who could lurk near the tub, and {hero.id} tried to be fair instead of guessing."),
        ("Who turned out to be involved?", f"{suspect.label.capitalize()} was the one tied to the mystery, and the clue helped explain it."),
        ("How did the mystery end?", f"{helper.id} helped solve it, and the room was cleaned up so it was no longer bath-dim."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does dim mean?", "Dim means not very bright. A dim room needs a light or a careful look to see what is happening."),
        ("What is a clue?", "A clue is a small piece of information that helps solve a mystery."),
        ("What does lurk mean?", "To lurk means to stay hidden or hang around in a sneaky way."),
        ("Why is telling the truth a good choice?", "Telling the truth helps people understand what really happened. It can stop a small problem from getting bigger."),
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="bathroom", clue="soap", suspect="cat", resolution="confess", hero="Mina", hero_gender="girl", helper="Owen", helper_gender="boy"),
    StoryParams(setting="nursery", clue="toy", suspect="brother", resolution="fetch", hero="Theo", hero_gender="boy", helper="Lily", helper_gender="girl"),
    StoryParams(setting="hallway", clue="towel", suspect="wind", resolution="ask", hero="Nora", hero_gender="girl", helper="Eli", helper_gender="boy"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "bath-dim" in s.tags:
            lines.append(asp.fact("bath_dim", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for t in c.tags:
            lines.append(asp.fact("tag", cid, t))
    for uid, u in SUSPECTS.items():
        lines.append(asp.fact("suspect", uid))
        for t in u.tags:
            lines.append(asp.fact("tag", uid, t))
    for rid, r in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", rid))
        for t in r.tags:
            lines.append(asp.fact("tag", rid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,U) :- setting(S), clue(C), suspect(U), bath_dim(S).
solvable(R) :- resolution(R).
story_ready(S,C,U,R) :- valid(S,C,U), solvable(R).
#show valid/3.
#show story_ready/4.
#show solvable/1.
"""


def asp_program(show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_story_ready() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ready/4."))
    return sorted(set(asp.atoms(model, "story_ready")))


def valid_story_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s, c, u in valid_combos():
        for r in RESOLUTIONS:
            out.append((s, c, u, r))
    return out


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python valid_combos().")
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    if set(asp_story_ready()) != set(valid_story_combos()):
        rc = 1
        print("MISMATCH: ASP story_ready differs from Python world readiness.")
    else:
        print(f"OK: ASP story_ready matches ({len(valid_story_combos())} combos).")

    sample_params = CURATED[0]
    try:
        sample = generate(sample_params)
        assert sample.story.strip()
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample)
        print("OK: generate/emit smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"MISMATCH: smoke test failed: {exc}")

    return rc


def resolve_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.clue not in CLUES or params.suspect not in SUSPECTS or params.resolution not in RESOLUTIONS:
        raise StoryError("Invalid parameters for this storyworld.")
    reasonableness_gate(params)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3.\n#show story_ready/4.\n#show solvable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid mystery combos:\n")
        for s, c, u in combos:
            print(f"  {s:10} {c:8} {u}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_combo(args, random.Random(base_seed + i))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} / {p.setting} / {p.clue} / {p.suspect} / {p.resolution}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
