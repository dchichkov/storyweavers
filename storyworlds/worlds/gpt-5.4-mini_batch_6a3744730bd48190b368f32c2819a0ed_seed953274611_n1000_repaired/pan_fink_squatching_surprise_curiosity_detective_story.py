#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pan_fink_squatching_surprise_curiosity_detective_story.py
========================================================================================

A small detective-style storyworld built from the seed words:
pan, fink, squatching

Premise:
A curious child detective follows tiny clues through a kitchen and alley-side
neighborhood mystery, expecting a troublemaker called a fink and discovering
that "squatching" is not a monster at all but a noisy neighbor activity caused
by a loose pan and a set of surprise footprints.

The world uses typed entities with physical meters and emotional memes, a simple
forward causal model, a reasonableness gate, and an inline ASP twin.
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
SUSPICION_MIN = 1.0


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Clue:
    id: str
    label: str
    sound: str
    surprise: int = 1
    curiosity: int = 1
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
class Suspect:
    id: str
    label: str
    alibi: str
    truth: str
    surprise: str
    curious_hint: str
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
class Location:
    id: str
    label: str
    detail: str
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
    location: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None
    delay: int = 0
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_spread_surprise(world: World) -> list[str]:
    out: list[str] = []
    if world.get("mystery").meters["noise"] < THRESHOLD:
        return out
    sig = ("surprise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("detective").memes["surprise"] += 1
    world.get("detective").memes["curiosity"] += 1
    out.append("__surprise__")
    return out


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


CAUSAL_RULES = [Rule("spread_surprise", _r_spread_surprise)]


def clue_at_risk(clue: Clue, suspect: Suspect, location: Location) -> bool:
    return clue.id in suspect.tags and location.id in suspect.tags


def valid_clues() -> list[str]:
    return [cid for cid, clue in CLUES.items() if clue.surprise >= 1 and clue.curiosity >= 1]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for set_id in SETTINGS:
        for clue_id, clue in CLUES.items():
            for suspect_id, suspect in SUSPECTS.items():
                for loc_id, loc in LOCATIONS.items():
                    if clue_at_risk(clue, suspect, loc):
                        combos.append((set_id, clue_id, suspect_id))
    return combos


def _make_noise(world: World, clue: Clue, suspect: Suspect) -> None:
    world.get("mystery").meters["noise"] += 1
    world.get("detective").memes["curiosity"] += clue.curiosity
    world.get("detective").memes["suspicion"] += clue.surprise
    world.say(f"A {clue.label} made a {clue.sound} sound, and {world.get('detective').id} looked up at once.")


def predict_solve(world: World, clue_id: str) -> dict:
    sim = world.copy()
    _make_noise(sim, CLUES[clue_id], SUSPECTS[sim.facts["suspect"]])
    propagate(sim, narrate=False)
    return {
        "surprise": sim.get("detective").memes["surprise"],
        "curiosity": sim.get("detective").memes["curiosity"],
    }


def introduce(world: World, det: Entity, helper: Entity, setting: Location) -> None:
    world.say(
        f"{det.id} was a little detective with bright eyes and a notebook full of questions. "
        f"{helper.id} stayed close, ready to help in {setting.label}."
    )


def begin_case(world: World, det: Entity, helper: Entity, setting: Location) -> None:
    world.say(
        f"One evening, the two of them took the long way home through {setting.label}. "
        f"{setting.detail}"
    )


def clue_scene(world: World, clue: Clue, suspect: Suspect, location: Location) -> None:
    world.say(
        f"Then came the clue: {clue.label}. It made a {clue.sound} sound near {location.label}, "
        f"and that made the whole case feel strange."
    )
    world.say(
        f"{world.get('detective').id} thought about the rumor of {suspect.label}, because the clue seemed to point that way."
    )


def question(world: World, det: Entity, helper: Entity, suspect: Suspect) -> None:
    det.memes["curiosity"] += 1
    world.say(
        f'"Who is making the noise?" {det.id} asked. {helper.id} smiled and said, '
        f'"Let us follow the facts before we jump to a fink-sized answer."'
    )
    world.facts["asked_about"] = suspect.id


def reveal(world: World, det: Entity, helper: Entity, suspect: Suspect, clue: Clue) -> None:
    det.memes["surprise"] += 1
    world.say(
        f"They found {suspect.alibi}. That was the surprise: the fink rumor was wrong."
    )
    world.say(
        f"{suspect.truth.capitalize()} {suspect.surprise} There was no sneaky troublemaker at all."
    )
    world.say(
        f"Instead, {suspect.curious_hint}, and the clue's sound had simply bounced around the hall."
    )


def solve(world: World, det: Entity, helper: Entity, suspect: Suspect, clue: Clue) -> None:
    det.memes["suspicion"] = 0.0
    det.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{det.id} wrote the answer in the notebook: the mystery was solved by curiosity, not by blame."
    )
    world.say(
        f"They laughed, because the so-called fink was only a harmless surprise hiding in plain sight."
    )


def ending(world: World, det: Entity, helper: Entity, location: Location, clue: Clue) -> None:
    world.say(
        f"By the end, {det.id} kept the notebook open and {helper.id} kept the light on. "
        f"The little detective had learned to listen for clues before naming a suspect."
    )
    world.say(
        f"And as the last {clue.label} sound faded in {location.label}, the night felt quiet, clever, and safe."
    )


def tell(setting: Location, clue: Clue, suspect: Suspect, location: Location,
         detective_name: str = "Mina", detective_gender: str = "girl",
         helper_name: str = "Pip", helper_gender: str = "boy") -> World:
    world = World()
    det = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    mystery = world.add(Entity(id="mystery", type="thing", label="the mystery"))
    world.facts["suspect"] = suspect.id

    introduce(world, det, helper, setting)
    begin_case(world, det, helper, setting)
    world.para()
    _make_noise(world, clue, suspect)
    clue_scene(world, clue, suspect, location)
    question(world, det, helper, suspect)
    world.para()
    reveal(world, det, helper, suspect, clue)
    solve(world, det, helper, suspect, clue)
    world.para()
    ending(world, det, helper, location, clue)

    world.facts.update(
        detective=det,
        helper=helper,
        mystery=mystery,
        setting=setting,
        clue=clue,
        suspect=suspect,
        location=location,
        outcome="solved",
    )
    return world


SETTINGS = {
    "kitchen": Location(
        id="kitchen",
        label="the kitchen",
        detail="A pan on the counter gleamed in the lamp light.",
        tags={"pan", "detective"},
    ),
    "alley": Location(
        id="alley",
        label="the alley behind the bakery",
        detail="The bricks were damp, and one pan was clinking near a crate.",
        tags={"pan", "detective"},
    ),
}

CLUES = {
    "pan": Clue(
        id="pan",
        label="a pan",
        sound="clink-clink",
        surprise=1,
        curiosity=2,
        tags={"pan", "sound"},
    ),
    "footprint": Clue(
        id="footprint",
        label="a surprise footprint",
        sound="tap-tap",
        surprise=2,
        curiosity=2,
        tags={"surprise", "curiosity"},
    ),
    "whistle": Clue(
        id="whistle",
        label="a little whistle",
        sound="tweet-tweet",
        surprise=1,
        curiosity=1,
        tags={"curiosity"},
    ),
}

SUSPECTS = {
    "fink": Suspect(
        id="fink",
        label="Fink",
        alibi="the door to the shed was wide open",
        truth="The answer was simple:",
        surprise="the shed held only a cat and a loose pan.",
        curious_hint="a curious cat had nudged the pan",
        tags={"fink", "pan", "surprise"},
    ),
    "nephew": Suspect(
        id="nephew",
        label="the baker's nephew",
        alibi="the baker's nephew had been asleep upstairs",
        truth="The answer was plain:",
        surprise="he had not gone squatching at all.",
        curious_hint="a gust of wind had rolled the pan over the floor",
        tags={"pan", "squatching"},
    ),
    "neighbor": Suspect(
        id="neighbor",
        label="the neighbor",
        alibi="the neighbor had been painting a sign",
        truth="The answer was kinder:",
        surprise="the noise came from a cart wheel, not a fink.",
        curious_hint="the neighbor was only squatching for lost beans",
        tags={"surprise", "curiosity", "squatching"},
    ),
}

LOCATIONS = {
    "doorstep": Location(
        id="doorstep",
        label="the doorstep",
        detail="A tiny trail of dust led toward the back gate.",
        tags={"surprise", "curiosity"},
    ),
    "bakery": Location(
        id="bakery",
        label="the bakery yard",
        detail="Warm bread smell floated out of the window.",
        tags={"pan", "squatching"},
    ),
}

TRAITS = ["curious", "careful", "bright", "patient", "thoughtful"]
GIRL_NAMES = ["Mina", "Lena", "Tia", "Nora", "Ivy"]
BOY_NAMES = ["Pip", "Eli", "Jon", "Theo", "Max"]


def explain_rejection(clue: Clue, suspect: Suspect, location: Location) -> str:
    if not clue_at_risk(clue, suspect, location):
        return "(No story: that combination does not produce a real mystery path.)"
    return "(No story: the clue, suspect, and place do not fit this detective setup.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly detective story that includes the words "{f["clue"].label}", '
        f'"fink", and "squatching".',
        f"Tell a curious detective story where {f['detective'].id} follows a clue, suspects a fink, "
        f"and learns the real answer was about squatching.",
        "Write a mystery story with surprise, curiosity, and a clear solved ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    det = f["detective"]
    helper = f["helper"]
    clue = f["clue"]
    suspect = f["suspect"]
    location = f["location"]
    qa = [
        ("Who is the story about?",
         f"It is about {det.id}, a little detective, and {helper.id}, who helped look for clues."),
        ("What clue started the mystery?",
         f"The mystery started with {clue.label} making a {clue.sound} sound. That small noise made the case feel important right away."),
        ("Why did the detective think about Fink?",
         f"{det.id} thought about {suspect.label} because the clue seemed to point that way. The surprise was that the clue was misleading, so the first guess was wrong."),
        ("What solved the mystery?",
         f"Curiosity solved it. {det.id} kept asking questions, and the truth turned out to be ordinary rather than sneaky."),
        ("How did the story end?",
         f"It ended with {det.id} and {helper.id} calm and pleased, because they found the real answer and did not blame the wrong person. The last clue sound faded away in {location.label}."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["clue"].tags) | set(f["suspect"].tags) | set(f["location"].tags)
    qa = []
    if "pan" in tags:
        qa.append(("What is a pan?",
                    "A pan is a flat cooking dish with a handle. Grown-ups use it in the kitchen to cook food."))
    if "curiosity" in tags:
        qa.append(("What is curiosity?",
                    "Curiosity is the feeling that makes you want to ask questions and find out more. It helps detectives notice clues."))
    if "surprise" in tags:
        qa.append(("What is surprise?",
                    "Surprise is the feeling you get when something happens that you did not expect. It can make a mystery more exciting."))
    if "squatching" in tags:
        qa.append(("What does squatching mean here?",
                    "In this story, squatching means making a strange sounding search or shuffle that sounds mysterious. It is not a real monster; it just sounds odd."))
    return qa


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery_noise :- clue(pan).
mystery_noise :- clue(footprint).
surprised :- mystery_noise.
curious :- mystery_noise.
valid(S, C, X) :- setting(S), clue(C), suspect(X), clue_tags(C, pan), suspect_tags(X, pan).
valid(S, C, X) :- setting(S), clue(C), suspect(X), clue_tags(C, surprise), suspect_tags(X, surprise).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for tag in sorted(clue.tags):
            lines.append(asp.fact("clue_tags", cid, tag))
    for xid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", xid))
        for tag in sorted(suspect.tags):
            lines.append(asp.fact("suspect_tags", xid, tag))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    rc = 0
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        print("  only in clingo:", sorted(clingo_set - python_set))
        print("  only in python:", sorted(python_set - clingo_set))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        assert sample.story
        print("OK: default generation smoke test passed.")
    except Exception as err:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld with pan, fink, and squatching.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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
    if args.clue and args.suspect and args.location:
        if not clue_at_risk(CLUES[args.clue], SUSPECTS[args.suspect], LOCATIONS[args.location]):
            raise StoryError(explain_rejection(CLUES[args.clue], SUSPECTS[args.suspect], LOCATIONS[args.location]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, suspect = rng.choice(sorted(combos))
    location = args.location or rng.choice(sorted(LOCATIONS))
    det_gender = args.detective_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if det_gender == "girl" else "girl")
    det_name = args.detective_name or rng.choice(GIRL_NAMES if det_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in (BOY_NAMES if helper_gender == "boy" else GIRL_NAMES) if n != det_name])
    return StoryParams(setting=setting, clue=clue, suspect=suspect, location=location,
                       detective_name=det_name, detective_gender=det_gender,
                       helper_name=helper_name, helper_gender=helper_gender, delay=args.delay)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.clue not in CLUES or params.suspect not in SUSPECTS or params.location not in LOCATIONS:
        raise StoryError("Invalid params.")
    setting = LOCATIONS[params.setting]
    clue = CLUES[params.clue]
    suspect = SUSPECTS[params.suspect]
    location = LOCATIONS[params.location]
    world = tell(setting, clue, suspect, location, params.detective_name, params.detective_gender, params.helper_name, params.helper_gender)
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, clue, suspect) combos:")
        for c in combos:
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(setting=s, clue=c, suspect=x, location="doorstep",
                                        detective_name="Mina", detective_gender="girl",
                                        helper_name="Pip", helper_gender="boy"))
                   for s, c, x in CURATED]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


CURATED = [
    ("kitchen", "pan", "fink"),
    ("alley", "footprint", "neighbor"),
    ("bakery", "whistle", "nephew"),
]


if __name__ == "__main__":
    main()
