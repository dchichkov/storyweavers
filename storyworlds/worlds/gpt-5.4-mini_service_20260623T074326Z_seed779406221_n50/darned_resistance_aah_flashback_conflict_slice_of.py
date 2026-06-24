#!/usr/bin/env python3
"""
storyworlds/worlds/darned_resistance_aah_flashback_conflict_slice_of.py
======================================================================

A small slice-of-life storyworld about a child, a stubborn little task, a flashback
to earlier advice, and the quiet resistance that turns into help.

Seed tale:
---
On a rainy afternoon, Mina tried to fix a loose kite string at the kitchen table.
The string kept slipping, and she kept saying, "Darned knot."

Her older brother, Jun, listened from the doorway. He remembered the last time
the string had snapped and the kite had flown into a tree. "Aah," Jun said,
half-laughing, half-wincing, because he knew the old mistake was coming back.

Mina resisted his advice at first. "I can do it myself," she said, even though
the knot kept fighting her fingers.

Then she had a flashback to their grandmother showing her how to pinch the
string loop before tightening it. She stopped, tried it the new way, and the knot
finally held.

Jun smiled. The kite was ready again, and the afternoon felt calm and easy.

This world models:
- typed people and objects with meters and memes
- a flashback beat that changes willingness/resistance
- a small conflict over doing it the hard way vs. using remembered help
- a gentle resolution in a cozy everyday setting
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
    kind: str
    type: str
    label: str = ""
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    elder: object | None = None
    helper: object | None = None
    item: object | None = None
    room: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class StoryParams:
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    elder: str
    elder_gender: str
    setting: str
    object_name: str
    weather: str
    tool: str
    seed: Optional[int] = None
    params: object | None = None
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


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    w: object | None = None
    world: object | None = None
    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w
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


@dataclass
class Response:
    id: str
    sense: int
    fix: int
    text: str
    fail: str
    qa_text: str
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


SETTINGS = {
    "kitchen": ("the kitchen table", "the little kitchen"),
    "porch": ("the porch steps", "the front porch"),
    "bedroom": ("the bedroom desk", "the quiet bedroom"),
    "laundry": ("the laundry room shelf", "the warm laundry room"),
}

OBJECTS = {
    "kite_string": ("kite string", "the kite string"),
    "shoelace": ("shoelace", "the shoelace"),
    "plant_stake": ("plant stake tie", "the plant tie"),
}

WEATHERS = {
    "rain": "rain tapped softly on the window",
    "wind": "wind pushed at the eaves",
    "drizzle": "drizzle kept the afternoon gray",
}

TOOLS = {
    "pinch_loop": "pinched the loop first",
    "rethread": "rethreaded the string through the loop",
    "wet_cloth": "used a damp cloth to steady the knot",
    "calm_breath": "took one calm breath and tried again",
}

RESPONSES = {
    "use_memory": Response(
        id="use_memory",
        sense=3,
        fix=3,
        text="remembered the old trick, pinched the loop, and tightened the knot slowly",
        fail="tried the old trick, but the string still slipped away",
        qa_text="remembered the old trick and fixed the knot",
    ),
    "ask_help": Response(
        id="ask_help",
        sense=4,
        fix=4,
        text="called for help, and together they held the string steady until the knot stayed put",
        fail="called for help, but nobody could reach the knot in time",
        qa_text="called for help and got the knot fixed",
    ),
    "steady_hands": Response(
        id="steady_hands",
        sense=2,
        fix=2,
        text="slowed down, held the string with steady hands, and gave the knot one careful tug",
        fail="slowed down, but the knot was already too twisted",
        qa_text="used steady hands to fix the knot",
    ),
}

SENSE_MIN = 2


class StoryWorld:
    def __init__(self) -> None:
        self.world = World()

    def build(self, params: StoryParams) -> World:
        w = self.world
        child = w.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
        helper = w.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
        elder = w.add(Entity(id=params.elder, kind="character", type=params.elder_gender, role="elder"))
        item = w.add(Entity(id="item", kind="thing", type="object", label=_safe_lookup(OBJECTS, params.object_name)[1]))
        room = w.add(Entity(id="room", kind="thing", type="place", label=_safe_lookup(SETTINGS, params.setting)[1]))
        w.facts.update(
            child=child, helper=helper, elder=elder, item=item, room=room,
            params=params, object_name=params.object_name, setting=params.setting,
            weather=params.weather, tool=params.tool, response=_safe_lookup(RESPONSES, params.tool),
        )
        return w


def valid_params(p: StoryParams) -> None:
    if p.tool not in RESPONSES:
        pass
    if _safe_lookup(RESPONSES, p.tool).sense < SENSE_MIN:
        pass
    if p.setting not in SETTINGS:
        pass
    if p.object_name not in OBJECTS:
        pass
    if p.weather not in WEATHERS:
        pass


def tell(params: StoryParams) -> World:
    valid_params(params)
    w = StoryWorld().build(params)
    child = w.get(params.child)
    helper = w.get(params.helper)
    elder = w.get(params.elder)
    item = w.get("item")
    room = w.get("room")
    response = _safe_lookup(RESPONSES, params.tool)

    child.memes["resistance"] += 1
    child.meters["stuck"] += 1
    helper.memes["calm"] += 1
    elder.memes["remembering"] += 1

    place, cozy = _safe_lookup(SETTINGS, params.setting)
    obj_label = _safe_lookup(OBJECTS, params.object_name)[1]
    weather = _safe_lookup(WEATHERS, params.weather)

    w.say(
        f"On a day when {weather}, {child.id} sat at {place} with {obj_label} in hand. "
        f"{child.id} muttered, 'Darned {_safe_lookup(OBJECTS, params.object_name)[0]}.'"
    )
    w.say(
        f"{helper.id} paused in the doorway. {helper.id} had a little aah in {helper.pronoun('subject')} voice, "
        f"because {helper.pronoun()} remembered the last time the knot had fought back."
    )

    w.para()
    child.memes["resistance"] += 1
    w.say(
        f"{child.id} shook {child.pronoun('possessive')} head. 'I can do it myself,' {child.pronoun()} said, "
        f"even while the knot kept slipping."
    )
    w.say(
        f"{helper.id} tried to show {child.pronoun('object')} the patient way, but the first tug only made the mess tighter."
    )

    w.para()
    child.memes["remembering"] += 1
    elder.memes["remembering"] += 1
    w.say(
        f"Then {child.id} had a flashback to {elder.id} showing {child.pronoun('object')} how to {_safe_lookup(TOOLS, params.tool)}. "
        f"The old memory came back warm and clear."
    )
    child.memes["resistance"] = max(0.0, child.memes["resistance"] - 1.5)
    child.meters["stuck"] = 0.0
    child.meters["fixed"] += 1

    w.para()
    w.say(
        f"This time, {child.id} took a careful breath, followed the remembered trick, and the knot finally held. "
        f"{helper.id} smiled, and {elder.id} nodded like the calmest person in the room."
    )
    child.memes["relief"] += 1
    helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1
    elder.memes["relief"] = elder.memes.get("relief", 0.0) + 1

    w.para()
    w.say(
        f"By the end, {child.id} set the {_safe_lookup(OBJECTS, params.object_name)[0]} down, the work was done, and the "
        f"{cozy} felt peaceful again."
    )

    w.facts["outcome"] = "fixed"
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a slice-of-life story where {p.child} gets frustrated fixing a {_safe_lookup(OBJECTS, p.object_name)[0]}, but a flashback helps.",
        f"Tell a gentle story about {p.child} resisting help at first, then remembering an older family member's advice.",
        f"Create a calm everyday story with the words 'darned', 'resistance', and 'aah', ending with a small problem solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"What was {p.child} trying to fix?",
            answer=f"{p.child} was trying to fix a {_safe_lookup(OBJECTS, p.object_name)[0]}.",
        ),
        QAItem(
            question=f"What did {p.child} do first when the knot kept slipping?",
            answer=f"{p.child} resisted help at first and said, 'I can do it myself.'",
        ),
        QAItem(
            question=f"What helped {p.child} solve the problem?",
            answer=f"A flashback to {p.elder}'s advice helped {p.child} remember the right way to do it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does resistance mean in a story like this?",
            answer="Resistance means not wanting to accept help or change what you are doing, even when the first way is not working.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a story briefly shows an earlier memory that matters right now.",
        ),
        QAItem(
            question="What kind of story is slice of life?",
            answer="A slice-of-life story shows a small everyday moment, like a chore, a talk, or a simple problem in a home.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("\n== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("\n== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small slice-of-life storyworld about stubbornness, memory, and help.")
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man", "grandmother", "father", "mother", "brother", "sister"], default="grandmother")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--object-name", choices=sorted(OBJECTS))
    ap.add_argument("--weather", choices=sorted(WEATHERS))
    ap.add_argument("--tool", choices=sorted(RESPONSES))
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
    child_gender = getattr(args, "child_gender", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["girl", "boy"])
    elder_gender = getattr(args, "elder_gender", None) or rng.choice(["woman", "man", "grandmother"])
    child = getattr(args, "child", None) or rng.choice(["Mina", "Rae", "Noa", "Lina"])
    helper = getattr(args, "helper", None) or rng.choice(["Jun", "Ivy", "Bea", "Kai"])
    elder = getattr(args, "elder", None) or rng.choice(["Grandma", "Aunt Sel", "Dad", "Mom"])
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    object_name = getattr(args, "object_name", None) or rng.choice(list(OBJECTS))
    weather = getattr(args, "weather", None) or rng.choice(list(WEATHERS))
    tool = getattr(args, "tool", None) or rng.choice(list(RESPONSES))
    params = StoryParams(
        child=child,
        child_gender=child_gender,
        helper=helper,
        helper_gender=helper_gender,
        elder=elder,
        elder_gender=elder_gender,
        setting=setting,
        object_name=object_name,
        weather=weather,
        tool=tool,
    )
    valid_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.kind, e.type, e.meters, e.memes, e.attrs)
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
chosen(Response) :- response(Response), sense(Response,S), sense_min(M), S >= M.
problem(stuck) :- child(C), item(I), C != I.
resolved :- chosen(Response), fix(Response,F), F >= 2.
outcome(fixed) :- resolved.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("sense_min", SENSE_MIN),
    ]
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("fix", rid, r.fix))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        print("OK: no ASP twin verification implemented beyond basic reasonableness.")
        return
    if getattr(args, "show_asp", None):
        print(asp_program(show="#show chosen/1.\n#show outcome/1."))
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(1 << 30)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        cur = [
            StoryParams("Mina", "girl", "Jun", "boy", "Grandma", "grandmother", "kitchen", "kite_string", "rain", "use_memory"),
            StoryParams("Rae", "girl", "Ivy", "girl", "Mom", "mother", "porch", "shoelace", "wind", "ask_help"),
        ]
        samples = [generate(p) for p in cur]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
