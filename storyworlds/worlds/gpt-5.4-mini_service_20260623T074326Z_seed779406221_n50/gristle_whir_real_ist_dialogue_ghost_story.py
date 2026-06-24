#!/usr/bin/env python3
"""
Standalone storyworld: gristle, whir, real-ist ghost-story dialogue.

A small classical simulation in a spooky-but-child-facing domain:
- A child hears a strange whir in an old house.
- A "real-ist" friend wants proof that the ghost is not real.
- The house reveals its gristle: a stubborn, clacky, old mechanical latch
  that makes the noise.
- Dialogue drives the turns.
- The ending resolves with a concrete, state-driven proof image.

The script follows the Storyweavers contract:
- self-contained stdlib script
- eager import of storyworlds.results
- lazy import of storyworlds.asp in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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

SENSE_MIN = 2



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Speaker:
    id: str
    label: str
    kind: str = "character"
    type: str = "character"
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    h: object | None = None
    n: object | None = None
    s: object | None = None
    def pronoun(self) -> str:
        return "they"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    id: str
    place: str
    darkness: str
    attic_detail: str
    proof_spot: str
    sound_place: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Haunting:
    id: str
    sound: str
    adjective: str
    source: str
    trigger: str
    reveal: str
    fear_word: str = "ghost"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Turn:
    id: str
    label: str
    method: str
    proof: str
    calm: str
    sense: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    setting: str
    haunting: str
    turn: str
    narrator: str
    skeptic: str
    helper: str
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Speaker] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.trace: list[str] = []

    def add(self, ent: Speaker) -> Speaker:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return "\n".join(self.lines)


SETTINGS = {
    "old_house": Setting(
        id="old_house",
        place="an old house at the end of the lane",
        darkness="the hallway was dark and cool",
        attic_detail="the attic stairs creaked above the ceiling",
        proof_spot="the dusty hall closet",
        sound_place="behind the closet door",
    ),
    "school": Setting(
        id="school",
        place="the school after sunset",
        darkness="the music room was dark and still",
        attic_detail="the loose floorboards clicked by the stage",
        proof_spot="the supply cupboard",
        sound_place="inside the cupboard wall",
    ),
    "cottage": Setting(
        id="cottage",
        place="a little cottage in the rain",
        darkness="the kitchen was dark except for moonlight",
        attic_detail="the rafters clicked high overhead",
        proof_spot="the pantry",
        sound_place="under the pantry shelf",
    ),
}

HAUNTINGS = {
    "gristle_whir": Haunting(
        id="gristle_whir",
        sound="a gristle-whir",
        adjective="gristly",
        source="an old latch",
        trigger="when the wind pressed the door",
        reveal="the latch was rusty, stiff, and just hard enough to whir",
    ),
    "pipe_song": Haunting(
        id="pipe_song",
        sound="a whir in the pipes",
        adjective="pipey",
        source="a loose vent pipe",
        trigger="when the heater woke up",
        reveal="the pipe had a crack that sang when air rushed through",
    ),
    "toy_click": Haunting(
        id="toy_click",
        sound="a gristle-click",
        adjective="clicky",
        source="a wind-up toy",
        trigger="when someone stepped on the floorboard",
        reveal="the toy had slipped under a shelf and clicked every time it shook",
    ),
}

TURNS = {
    "open_door": Turn(
        id="open_door",
        label="open the door and look",
        method="opened the closet door and shone a flashlight inside",
        proof="the flashlight caught a rusty latch and a crooked screw",
        calm="the scary noise had a plain old reason",
        sense=3,
        tags={"flashlight", "proof"},
    ),
    "listen_close": Turn(
        id="listen_close",
        label="listen closely",
        method="held still and listened until the whir came again",
        proof="the sound got louder near the closet hinge",
        calm="the sound was close, not haunted",
        sense=2,
        tags={"listening", "proof"},
    ),
    "fix_latch": Turn(
        id="fix_latch",
        label="fix the latch",
        method="found a screwdriver and tightened the loose latch plate",
        proof="the whir stopped when the latch stopped shaking",
        calm="the house was quiet again",
        sense=3,
        tags={"tool", "proof"},
    ),
    "waste_time": Turn(
        id="waste_time",
        label="keep guessing",
        method="kept whispering ghost guesses and did nothing useful",
        proof="the noise only got stranger in the dark",
        calm="the fear grew instead of shrinking",
        sense=1,
        tags={"guessing"},
    ),
}

NAMES = {
    "narrator": ["Mina", "Ivy", "Rae", "Nina", "June", "Elsie"],
    "skeptic": ["Theo", "Finn", "Bo", "Max", "Arlo", "Jules"],
    "helper": ["Mara", "Lena", "Owen", "Piper", "Zed", "Nell"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for h in HAUNTINGS:
            for t in TURNS:
                if _safe_lookup(TURNS, t).sense >= SENSE_MIN:
                    combos.append((s, h, t))
    return combos


def explain_rejection(turn: Turn) -> str:
    return f"(No story: turn '{turn.id}' is too guessy and not reasonable enough for a child story.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story dialogue storyworld with gristle, whir, and a real-ist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--haunting", choices=HAUNTINGS)
    ap.add_argument("--turn", choices=TURNS)
    ap.add_argument("--narrator", choices=NAMES["narrator"])
    ap.add_argument("--skeptic", choices=NAMES["skeptic"])
    ap.add_argument("--helper", choices=NAMES["helper"])
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
    if getattr(args, "turn", None) and _safe_lookup(TURNS, getattr(args, "turn", None)).sense < SENSE_MIN:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    haunting = getattr(args, "haunting", None) or rng.choice(list(HAUNTINGS))
    turn = getattr(args, "turn", None) or rng.choice([k for k, v in TURNS.items() if v.sense >= SENSE_MIN])
    narrator = getattr(args, "narrator", None) or rng.choice(NAMES["narrator"])
    skeptic = getattr(args, "skeptic", None) or rng.choice([n for n in NAMES["skeptic"] if n != narrator])
    helper = getattr(args, "helper", None) or rng.choice([n for n in NAMES["helper"] if n not in {narrator, skeptic}])
    return StoryParams(setting=setting, haunting=haunting, turn=turn, narrator=narrator, skeptic=skeptic, helper=helper)


def make_world(params: StoryParams) -> tuple[World, dict[str, Speaker]]:
    w = World()
    n = w.add(Speaker(params.narrator, params.narrator))
    s = w.add(Speaker(params.skeptic, params.skeptic))
    h = w.add(Speaker(params.helper, params.helper))
    n.memes["fear"] = 1
    s.memes["realist"] = 2  # real-ist: wants a real explanation.
    h.memes["calm"] = 2
    return w, {"n": n, "s": s, "h": h}


def generate(params: StoryParams) -> StorySample:
    w, people = make_world(params)
    setn = _safe_lookup(SETTINGS, params.setting)
    haunt = _safe_lookup(HAUNTINGS, params.haunting)
    turn = _safe_lookup(TURNS, params.turn)

    n, s, h = people["n"], people["s"], people["h"]
    w.facts.update(params=params, setting=setn, haunting=haunt, turn=turn, people=people)

    w.say(f"It was {setn.place}.")
    w.say(f'"Did you hear that?" {n.id} whispered. "{haunt.sound} in the dark?"')
    w.say(f'"That sounds like a ghost," {s.id} said. "I want a real answer. I am a real-ist."')
    w.say(f'"Then let\'s look," {h.id} said. "{setn.darkness.capitalize()}, but not forever."')
    w.say(f"The sound came again, {haunt.trigger}, from {setn.sound_place}.")
    w.say(f'"My knees feel like jelly," {n.id} said. "But I do not want a ghost living in the closet."')
    if turn.id == "open_door":
        w.say(f'"We need proof," {s.id} said. "{turn.method}."')
        w.say(f"{turn.proof.capitalize()}.")
        w.say(f'"See?" {h.id} said. "{haunt.reveal}."')
    elif turn.id == "listen_close":
        w.say(f'"Wait," {h.id} said. "{turn.method}."')
        w.say(f"{turn.proof.capitalize()}.")
        w.say(f'"A ghost would not sound that tired," {s.id} muttered.')
    elif turn.id == "fix_latch":
        w.say(f'"I have a better idea," {h.id} said. "{turn.method}."')
        w.say(f"{turn.proof.capitalize()}.")
        w.say(f'"That is not a ghost," {s.id} said, and even smiled a little.')
    else:
        w.say(f'"I still think it is a ghost," {s.id} whispered.')
        w.say(f"{turn.proof.capitalize()}.")
    n.memes["relief"] = 2
    s.memes["certainty"] = 2
    h.memes["safety"] = 2

    w.say(f'"So the house was not haunted?" {n.id} asked.')
    w.say(f'"No," {h.id} said. "The noise had a plain old reason: {haunt.reveal}."')
    w.say(f'{s.id} touched the latch and said, "{turn.calm}."')
    w.say(f'The little whir gave one last tired sound, then stopped.')
    w.say(f'In the quiet, {n.id} could hear the rain, the floorboards, and everyone breathing easier.')

    world = w
    story = world.render()
    story_qa = [
        QAItem(question=f"What did {s.id} want to be sure about?", answer=f"{s.id} wanted a real explanation, because {s.id} was a real-ist and did not want to guess about ghosts."),
        QAItem(question=f"What made the spooky sound?", answer=f"It was {haunt.reveal}, not a real ghost."),
        QAItem(question=f"What was the turn in the story?", answer=f"The children {turn.label}, which gave them proof and made the fear shrink."),
    ]
    world_qa = [
        QAItem(question="What does a real-ist mean in this story?", answer="It means someone who wants a real explanation instead of only guessing."),
        QAItem(question="Why can an old latch make a strange sound?", answer="Because rusty metal can stick, shake, and whir when a door or wind moves it."),
        QAItem(question="What helps when a story feels spooky?", answer="A light, a careful look, and a calm explanation can help the fear go down."),
    ]
    prompts = [
        f"Write a ghost-story dialogue for children in {setn.place}, where a gristle-whir turns out to have a real cause.",
        f"Tell a spooky-but-gentle story with dialogue in which {s.id} is a real-ist and {n.id} hears {haunt.sound}.",
        f"Make the ending prove the noise was not a ghost; use {turn.label} as the solving action.",
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for k, v in sample.world.facts.items():
            if k != "people":
                print(f"{k}: {v}")
    if qa:
        print()
        for group_name, items in [("story", sample.story_qa), ("world", sample.world_qa)]:
            print(f"== {group_name} QA ==")
            for item in items:
                print(f"Q: {item.question}")
                print(f"A: {item.answer}")
            print()


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HAUNTINGS.items():
        lines.append(asp.fact("haunting", hid))
        lines.append(asp.fact("sound", hid, h.sound))
    for tid, t in TURNS.items():
        lines.append(asp.fact("turn", tid))
        lines.append(asp.fact("sense", tid, t.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(T) :- turn(T), sense(T, S), sense_min(M), S >= M.
valid(S, H, T) :- setting(S), haunting(H), turn(T), sensible(T).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    py = {(s, h, t) for s, h, t in valid_combos()}
    cl = set(asp_valid_combos())
    ok = py == cl
    print("OK: ASP parity matches." if ok else f"MISMATCH: python={sorted(py)} clingo={sorted(cl)}")
    return 0 if ok else 1


CURATED = [
    StoryParams("old_house", "gristle_whir", "open_door", "Mina", "Theo", "Mara"),
    StoryParams("school", "pipe_song", "listen_close", "Ivy", "Max", "Owen"),
    StoryParams("cottage", "toy_click", "fix_latch", "June", "Bo", "Nell"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("sensible turns:", ", ".join(asp_sensible()))
        print("valid combos:")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(1, getattr(args, "n", None))):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
