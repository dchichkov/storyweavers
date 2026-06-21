#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/din_sharing_conflict_flashback_whodunit.py
===========================================================================

A tiny whodunit-flavored story world about a mysterious din, a sharing dispute,
and a remembered clue that resolves the conflict.

Premise
-------
A child hears a strange din in the attic, suspects a thief, and investigates.
The "mystery" turns out to be a sharing conflict around a toy and a flashback
to where the missing clue was last seen. The ending proves what changed: the
children share the item, the din stops, and the room feels calm again.

This script is standalone and uses only the stdlib plus the shared result/ASP
helpers from the Storyweavers repo.
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

# Make shared containers importable when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SUSPICION_RISE = 1.0


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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class MysterySetting:
    id: str
    place: str
    room: str
    din_place: str
    hiding_spot: str
    mood: str
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
class SharedThing:
    id: str
    label: str
    phrase: str
    plural: bool = False
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
class Clue:
    id: str
    place: str
    line: str
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
    calm: str
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
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_din(world: World) -> list[str]:
    out: list[str] = []
    setting = world.facts["setting"]
    for obj in list(world.entities.values()):
        if obj.meters["clamor"] < THRESHOLD:
            continue
        sig = ("din", obj.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for char in list(world.entities.values()):
            if char.kind == "character":
                char.memes["alarm"] += 1
                char.memes["suspicion"] += 1
        out.append(f"The din bounced through the {setting.room}.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    toy = world.facts.get("shared")
    if not toy:
        return out
    a = world.facts["child_a"]
    b = world.facts["child_b"]
    if a.memes["greedy"] < THRESHOLD and b.memes["greedy"] < THRESHOLD:
        sig = ("share", toy.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        a.memes["peace"] += 1
        b.memes["peace"] += 1
        out.append(f"They agreed to share {toy.phrase} turn by turn.")
    return out


def _r_conflict(world: World) -> list[str]:
    a = world.facts["child_a"]
    b = world.facts["child_b"]
    toy = world.facts["shared"]
    if a.memes["greedy"] < THRESHOLD or b.memes["greedy"] < THRESHOLD:
        return []
    sig = ("conflict", toy.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["cross"] += 1
    b.memes["cross"] += 1
    world.get("mystery").meters["noise"] += 1
    return ["__conflict__"]


CAUSAL_RULES = [Rule("din", _r_din), Rule("conflict", _r_conflict), Rule("share", _r_share)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def flashback_reveal(world: World, clue: Clue) -> None:
    world.say(
        f"Then a flashback tugged at {world.facts['child_a'].id}'s thoughts: "
        f"{clue.line}"
    )


def inspect(world: World, seeker: Entity, setting: MysterySetting) -> None:
    seeker.memes["curiosity"] += 1
    world.say(
        f"{seeker.id} crept toward {setting.din_place}, trying to read the mystery in the dark."
    )


def accuse(world: World, seeker: Entity, other: Entity) -> None:
    seeker.memes["suspicion"] += 1
    world.say(
        f'"Someone is making that din," {seeker.id} whispered. '
        f'"Maybe {other.id} knows more than {seeker.pronoun("object")} is saying."'
    )


def uncover(world: World, setting: MysterySetting, clue: Clue, reveal: Resolution) -> None:
    world.say(
        f"At {clue.place}, {reveal.reveal} {reveal.method}."
    )
    world.say(
        f"The mystery loosened at once, because the clue showed the noise was really a sharing quarrel."
    )


def resolve_case(world: World, a: Entity, b: Entity, toy: SharedThing, reveal: Resolution) -> None:
    a.memes["greedy"] = 0.0
    b.memes["greedy"] = 0.0
    a.memes["peace"] += 1
    b.memes["peace"] += 1
    world.say(
        f'{reveal.calm} {a.id} handed {toy.phrase} to {b.id}, and {b.id} '
        f'promised to give it back on the next turn.'
    )
    world.say(
        "The din faded into little happy taps, and the room felt quiet enough to hear a whisper."
    )


def tell(setting: MysterySetting, toy: SharedThing, clue: Clue, reveal: Resolution,
         child_a: str = "Mia", child_b: str = "Noah",
         gender_a: str = "girl", gender_b: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    a = world.add(Entity(id=child_a, kind="character", type=gender_a, role="child"))
    b = world.add(Entity(id=child_b, kind="character", type=gender_b, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    mystery = world.add(Entity(id="mystery", type="thing", label="the mystery box"))
    shared = world.add(Entity(id=toy.id, type="thing", label=toy.label))
    shared.meters["clamor"] = 1.0
    a.memes["greedy"] = 1.0
    b.memes["greedy"] = 1.0

    world.facts.update(
        setting=setting,
        shared=shared,
        clue=clue,
        reveal=reveal,
        child_a=a,
        child_b=b,
        parent=parent,
        mystery=mystery,
    )

    world.say(
        f"On a quiet evening, {a.id} and {b.id} heard a strange din coming from the {setting.room}."
    )
    world.say(
        f"Between them sat {toy.phrase}, and both children wanted it first."
    )

    world.para()
    inspect(world, a, setting)
    accuse(world, a, b)
    propagate(world)

    world.para()
    world.say(
        f"{b.id} crossed {b.pronoun('possessive')} arms. "
        f'"I found it," {b.id} said, not wanting to share yet.'
    )
    mystery.meters["noise"] += 1
    a.memes["greedy"] += 1
    b.memes["greedy"] += 1
    propagate(world)

    world.para()
    flashback_reveal(world, clue)
    uncover(world, setting, clue, reveal)
    resolve_case(world, a, b, toy, reveal)

    world.para()
    world.say(
        f"By the end, the din had become a soft patter of turn-taking, and the {setting.room} was calm again."
    )

    world.facts.update(outcome="resolved")
    return world


SETTINGS = {
    "attic": MysterySetting(
        id="attic",
        place="the attic",
        room="attic",
        din_place="the old trunk",
        hiding_spot="under a dusty blanket",
        mood="shadowy",
        tags={"whodunit", "din"},
    ),
    "hall": MysterySetting(
        id="hall",
        place="the hallway",
        room="hallway",
        din_place="the umbrella stand",
        hiding_spot="behind a tall coat",
        mood="echoy",
        tags={"whodunit", "din"},
    ),
}

SHARED_THINGS = {
    "drum": SharedThing(
        id="drum",
        label="a small drum",
        phrase="a small drum",
        tags={"sharing", "din"},
    ),
    "bell": SharedThing(
        id="bell",
        label="a shiny bell",
        phrase="a shiny bell",
        tags={"sharing", "din"},
    ),
    "blocks": SharedThing(
        id="blocks",
        label="a stack of blocks",
        phrase="a stack of blocks",
        tags={"sharing", "din"},
    ),
}

CLUES = {
    "note": Clue(
        id="note",
        place="the windowsill",
        line="a little note remembered that the drum had been borrowed for a game earlier",
        tags={"flashback", "whodunit"},
    ),
    "ribbon": Clue(
        id="ribbon",
        place="behind the chair",
        line="a ribbon from the toy basket matched the missing pile",
        tags={"flashback", "whodunit"},
    ),
}

RESOLUTIONS = {
    "turns": Resolution(
        id="turns",
        method="by turns",
        reveal="a toy basket was open nearby, and the missing piece was inside it all along.",
        calm="With the truth out,",
        tags={"sharing", "conflict"},
    ),
    "half": Resolution(
        id="half",
        method="in half-time",
        reveal="the toy had only been put away for the next child's turn.",
        calm="When everyone understood,",
        tags={"sharing", "conflict"},
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Tess", "Nora", "Pia"]
BOY_NAMES = ["Noah", "Eli", "Owen", "Ben", "Theo"]
TRAITS = ["careful", "curious", "sharp", "patient", "observant"]


@dataclass
class StoryParams:
    setting: str
    toy: str
    clue: str
    resolution: str
    child_a: str
    gender_a: str
    child_b: str
    gender_b: str
    parent_type: str
    trait: str = "observant"
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid in SHARED_THINGS:
            for cid in CLUES:
                for rid in RESOLUTIONS:
                    combos.append((sid, tid, cid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world with din, sharing, conflict, and flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=SHARED_THINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--gender-b", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.toy is None or c[1] == args.toy)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, toy, clue = rng.choice(sorted(combos))
    resolution = args.resolution or rng.choice(sorted(RESOLUTIONS))
    gender_a = args.gender_a or rng.choice(["girl", "boy"])
    gender_b = args.gender_b or ("boy" if gender_a == "girl" else "girl")
    name_a = args.name_a or rng.choice(GIRL_NAMES if gender_a == "girl" else BOY_NAMES)
    name_b = args.name_b or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != name_a])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, toy=toy, clue=clue, resolution=resolution,
                       child_a=name_a, gender_a=gender_a, child_b=name_b,
                       gender_b=gender_b, parent_type=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    toy = f["shared"]
    return [
        f'Write a child-friendly whodunit with the word "din" in {setting.room}.',
        f"Tell a story where {f['child_a'].id} and {f['child_b'].id} disagree over {toy.phrase}, and a flashback helps solve the problem.",
        f"Write a calm mystery about a strange din, a sharing conflict, and a clue that points to the truth.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["child_a"], f["child_b"]
    toy = f["shared"]
    clue = f["clue"]
    reveal = f["reveal"]
    return [
        ("What strange sound did they hear?",
         f"They heard a strange din in the {f['setting'].room}. The noise came from a sharing quarrel, not from a real thief."),
        ("Why were the children upset?",
         f"They both wanted {toy.phrase} first. That disagreement made the room noisy and cross."),
        ("What was the flashback for?",
         f"The flashback reminded {a.id} that the toy had been borrowed for a game earlier. It helped the children see the truth instead of guessing."),
        ("Where was the clue found?",
         f"The clue was found at {clue.place}. That small detail connected the missing item to the real answer."),
        ("How did the story end?",
         f"They shared {toy.phrase} by turns, and the din faded away. The room ended quiet and peaceful."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a din?",
         "A din is a loud, messy noise that makes it hard to think clearly. It often means something is being argued about or knocked around."),
        ("What does sharing mean?",
         "Sharing means letting someone else use something too. People can take turns so everyone gets a fair chance."),
        ("What is a flashback in a story?",
         "A flashback is when a story briefly remembers something from earlier. It can help explain a mystery or a surprise."),
        ("What is a whodunit?",
         "A whodunit is a mystery story where someone tries to figure out what happened. The clues help the reader solve it too."),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
din(X) :- clamor(X), clamor(X, V), V >= 1.
conflict(A,B) :- greedy(A), greedy(B), A != B.
shared_turns(T) :- shared(T), not conflict(_, _).
resolved :- clue(C), flashback(C), shared(T), shared_turns(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in SHARED_THINGS:
        lines.append(asp.fact("shared", tid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for rid in RESOLUTIONS:
        lines.append(asp.fact("resolution", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("", "#show setting/1."))
        _ = model
        print(f"OK: ASP helper loaded and {len(valid_combos())} combinations available.")
    except Exception as e:
        print(f"ERROR: ASP check failed: {e}")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, toy=None, clue=None, resolution=None,
            name_a=None, name_b=None, gender_a=None, gender_b=None,
            parent=None, seed=None, all=False, trace=False, qa=False,
            json=False, asp=False, verify=False, show_asp=False
        ), random.Random(7)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as e:
        print(f"ERROR: generation smoke test failed: {e}")
        return 1
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.toy not in SHARED_THINGS:
        raise StoryError(f"Unknown shared thing: {params.toy}")
    if params.clue not in CLUES:
        raise StoryError(f"Unknown clue: {params.clue}")
    if params.resolution not in RESOLUTIONS:
        raise StoryError(f"Unknown resolution: {params.resolution}")
    world = tell(
        SETTINGS[params.setting],
        SHARED_THINGS[params.toy],
        CLUES[params.clue],
        RESOLUTIONS[params.resolution],
        child_a=params.child_a,
        child_b=params.child_b,
        gender_a=params.gender_a,
        gender_b=params.gender_b,
        parent_type=params.parent_type,
    )
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
    StoryParams(setting="attic", toy="drum", clue="note", resolution="turns",
                child_a="Mia", gender_a="girl", child_b="Noah", gender_b="boy",
                parent_type="mother", trait="observant"),
    StoryParams(setting="hall", toy="bell", clue="ribbon", resolution="half",
                child_a="Eli", gender_a="boy", child_b="Tess", gender_b="girl",
                parent_type="father", trait="curious"),
]


def explain_rejection() -> str:
    return "(No story: this combination does not form a reasonable mystery.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show setting/1.\n#show shared/1.\n#show clue/1.\n#show resolution/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
