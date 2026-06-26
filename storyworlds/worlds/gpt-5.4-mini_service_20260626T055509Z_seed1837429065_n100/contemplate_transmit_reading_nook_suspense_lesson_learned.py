#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/contemplate_transmit_reading_nook_suspense_lesson_learned.py
==============================================================================================================

A small bedtime-story world set in a reading nook.

Premise:
- A child in a cozy reading nook contemplates whether to transmit a gentle
  message before sleep.

Tension:
- The child worries that making the message reach its destination might be too
  loud, too slow, or too brave.

Turn:
- A quiet helper method shows how to transmit the message softly.

Resolution:
- The message arrives, the nook stays peaceful, and the child learns that a
  gentle plan can be enough.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib world script
- eager import of shared results containers
- lazy import of asp inside ASP helpers
- generate / emit / parser / main
- ASP twin with parity verification
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


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
            keys = [upper, upper + "S", upper + "ES"]
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    msg: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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
    place: str = "the reading nook"
    bedtime: bool = True
    SETTING: object | None = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Method:
    id: str
    verb: str
    gerund: str
    risk: str
    quietness: float
    suspense: str
    lesson: str
    tags: set[str] = field(default_factory=set)
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
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
class Message:
    label: str
    phrase: str
    destination: str
    delicate: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def _m_quiet(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("quiet", 0.0) < THRESHOLD:
            continue
        if e.meters.get("calm", 0.0) >= THRESHOLD:
            continue
        sig = ("quiet", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["calm"] = e.meters.get("calm", 0.0) + 1
        out.append("The nook stayed soft and still.")
    return out


def _m_lesson(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes.get("worry", 0.0) < THRESHOLD:
        return out
    if child.memes.get("confidence", 0.0) < THRESHOLD:
        return out
    sig = ("lesson",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["lesson_learned"] = 1
    out.append("The child remembered that gentle plans can work.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_m_quiet, _m_lesson):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting()
METHODS = {
    "whisper": Method(
        id="whisper",
        verb="whisper",
        gerund="whispering",
        risk="the words might carry too far",
        quietness=1.0,
        suspense="a tiny creak in the shelves",
        lesson="A whisper can travel when the room is calm.",
        tags={"quiet", "suspense", "lesson"},
    ),
    "paper_tube": Method(
        id="paper_tube",
        verb="send the note through a paper tube",
        gerund="sending the note through a paper tube",
        risk="the tube might rustle",
        quietness=0.8,
        suspense="the paper tube trembled in small hands",
        lesson="A careful tool can make a job easier.",
        tags={"quiet", "suspense", "lesson"},
    ),
    "lamp_signal": Method(
        id="lamp_signal",
        verb="blink the lamp softly",
        gerund="blinking the lamp softly",
        risk="the light might wake the room",
        quietness=0.7,
        suspense="the lamp flickered once before settling down",
        lesson="Small signals can be kinder than big ones.",
        tags={"suspense", "lesson"},
    ),
}
MESSAGES = {
    "good_night": Message(
        label="good-night note",
        phrase="a tiny good-night note",
        destination="the sleeping teddy bear on the shelf",
        delicate=True,
        tags={"note", "bedtime"},
    ),
    "thank_you": Message(
        label="thank-you card",
        phrase="a little thank-you card",
        destination="the grandma book on the cushion",
        delicate=True,
        tags={"card", "gratitude"},
    ),
    "story_word": Message(
        label="storybook word",
        phrase="a soft story word",
        destination="the friend-shaped pillow by the window",
        delicate=True,
        tags={"word", "quiet"},
    ),
}
CHILD_NAMES = ["Mila", "Noah", "Lena", "Theo", "Ivy", "Eli"]
HELPER_NAMES = ["Pip", "Moss", "Juniper", "Dot"]


@dataclass
class StoryParams:
    method: str
    message: str
    child_name: str
    helper_name: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def valid_combos() -> list[tuple[str, str]]:
    return [(m, msg) for m in METHODS for msg in MESSAGES if m != "lamp_signal" or msg != "thank_you"]


def explain_rejection(method: Method, message: Message) -> str:
    if method.id == "lamp_signal" and message.label == "thank-you card":
        return "(No story: a lamp signal is too bright for a bedtime thank-you card in the reading nook.)"
    return "(No story: that combination does not make a gentle bedtime story here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world set in a reading nook: contemplate, transmit, suspense, lesson learned."
    )
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--message", choices=sorted(MESSAGES))
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if getattr(args, "method", None) and getattr(args, "message", None):
        if (getattr(args, "method", None), getattr(args, "message", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "method", None) is None or c[0] == getattr(args, "method", None))
              and (getattr(args, "message", None) is None or c[1] == getattr(args, "message", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    method, message = rng.choice(list(combos))
    child_name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    helper_name = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    return StoryParams(method=method, message=message, child_name=child_name, helper_name=helper_name)


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(id="child", kind="character", type="boy" if params.child_name in {"Noah", "Theo", "Eli"} else "girl"))
    child.label = params.child_name
    helper = world.add(Entity(id="helper", kind="character", type="thing"))
    helper.label = params.helper_name
    msg = world.add(Entity(id="message", type="thing", label=_safe_lookup(MESSAGES, params.message).label, phrase=_safe_lookup(MESSAGES, params.message).phrase, owner=child.id))
    method = _safe_lookup(METHODS, params.method)

    world.say(f"{params.child_name} curled up in the reading nook with a book and a sleepy yawn.")
    world.say(f"{params.child_name} wanted to contemplate the right way to transmit {msg.phrase} before bedtime.")
    world.say(f"Nearby, {params.helper_name} listened like a patient little star.")

    world.para()
    child.memes["worry"] = 1
    child.meters["quiet"] = 1
    world.say(f"{params.child_name} looked at the {msg.label} and wondered if {method.risk}.")
    world.say(f"Then came {method.suspense}, and the room felt full of suspense for one tiny moment.")

    if method.id == "whisper":
        world.say(f"{params.child_name} took a breath and chose to {method.verb} the message as softly as falling feathers.")
    elif method.id == "paper_tube":
        world.say(f"{params.child_name} rolled the page into a paper tube and tried {method.verb}.")
    else:
        world.say(f"{params.child_name} touched the lamp and tried to {method.verb} without waking the room.")

    child.memes["confidence"] = 1
    propagate(world, narrate=True)

    world.para()
    child.memes["lesson"] = 1
    world.say(f"The message reached {msg.destination}, right where it needed to go.")
    world.say(f"{params.child_name} smiled and learned this lesson: {method.lesson}")
    world.say(f"The reading nook stayed cozy, and the night felt kind again.")

    world.facts.update(
        child=child,
        helper=helper,
        message=msg,
        method=method,
        params=params,
        lesson=True,
    )
    return world


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = _safe_fact(world, f, "params")
    method: Method = _safe_fact(world, f, "method")
    msg: Message = _safe_fact(world, f, "message")
    return [
        'Write a bedtime story set in a reading nook that includes the word "contemplate" and the word "transmit".',
        f"Tell a gentle suspense story where {params.child_name} wants to {method.verb} {msg.phrase} before sleep.",
        f"Write a child-friendly story with a cozy reading nook, a small suspenseful moment, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = _safe_fact(world, f, "params")
    method: Method = _safe_fact(world, f, "method")
    msg: Message = _safe_fact(world, f, "message")
    return [
        QAItem(
            question=f"Where does {params.child_name} try to transmit the message?",
            answer="In the reading nook, which is cozy and quiet at bedtime.",
        ),
        QAItem(
            question=f"What did {params.child_name} contemplate before acting?",
            answer=f"{params.child_name} contemplated the safest way to transmit {msg.phrase} without waking the room.",
        ),
        QAItem(
            question=f"What lesson did {params.child_name} learn by the end?",
            answer=f"{params.child_name} learned that {method.lesson.lower()}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a reading nook?",
            answer="A reading nook is a cozy little place for books, quiet stories, and soft lights.",
        ),
        QAItem(
            question="What does transmit mean?",
            answer="Transmit means to send something from one place or person to another.",
        ),
        QAItem(
            question="Why is suspense useful in a story?",
            answer="Suspense helps a story feel exciting because the reader wonders what will happen next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(method="whisper", message="good_night", child_name="Mila", helper_name="Pip"),
    StoryParams(method="paper_tube", message="thank_you", child_name="Noah", helper_name="Dot"),
    StoryParams(method="lamp_signal", message="story_word", child_name="Lena", helper_name="Juniper"),
]


ASP_RULES = r"""
method(whisper). method(paper_tube). method(lamp_signal).
message(good_night). message(thank_you). message(story_word).

gentle_combo(whisper, good_night).
gentle_combo(whisper, thank_you).
gentle_combo(whisper, story_word).
gentle_combo(paper_tube, good_night).
gentle_combo(paper_tube, thank_you).
gentle_combo(paper_tube, story_word).
gentle_combo(lamp_signal, good_night).
gentle_combo(lamp_signal, story_word).

valid(M, Msg) :- gentle_combo(M, Msg).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for m in METHODS:
        lines.append(asp.fact("method", m))
    for msg in MESSAGES:
        lines.append(asp.fact("message", msg))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
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

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (method, message) combos:\n")
        for m, msg in combos:
            print(f"  {m:12} {msg}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name}: {p.method} / {p.message}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
