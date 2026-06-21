#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/vein_surprise_detective_story.py
===============================================================

A standalone storyworld for a tiny detective tale with a surprise reveal.

Premise:
- A child detective and a helper search a small place for a missing clue.
- The clue turns out to be hidden by a surprising but harmless mechanism.
- The detective follows physical traces, notices the vein word, and solves the case.

This world uses typed entities with physical meters and emotional memes,
a tiny forward-chaining simulation, grounded QA, and an inline ASP twin.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

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
class Place:
    id: str
    label: str
    detail: str
    has_secret_space: bool = True
    surprise_kind: str = "hidden drawer"
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
    object_word: str
    hidden_in: str
    visible_trace: str
    surprise_trick: str
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
class Method:
    id: str
    label: str
    sense: int
    reveal_power: int
    text: str
    fail_text: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    case = world.get("case")
    clue = world.get("clue")
    if case.meters.get("opened", 0.0) >= THRESHOLD and clue.meters.get("found", 0.0) < THRESHOLD:
        sig = ("surprise", clue.id)
        if sig not in world.fired:
            world.fired.add(sig)
            clue.meters["found"] = 1.0
            detective = world.get("detective")
            detective.memes["surprise"] += 1
            out.append("__surprise__")
    return out


CAUSAL_RULES = [Rule("surprise", "mystery", _r_surprise)]


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


def hidden_trace(place: Place, clue: Clue) -> bool:
    return place.has_secret_space and clue.hidden_in == place.id


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combo(place: Place, clue: Clue, method: Method) -> bool:
    return hidden_trace(place, clue) and method.sense >= SENSE_MIN


def clue_score(place: Place, clue: Clue, delay: int) -> int:
    return 1 + delay if place.has_secret_space else delay


def can_reveal(method: Method, place: Place, delay: int) -> bool:
    return method.reveal_power >= clue_score(place, None, delay) if False else method.reveal_power >= (1 + delay)


def _open_case(world: World, detective: Entity, case: Entity) -> None:
    detective.memes["curiosity"] += 1
    case.meters["opened"] = case.meters.get("opened", 0.0) + 1


def _inspect_trace(world: World, detective: Entity, clue: Entity, place: Place) -> None:
    detective.memes["focus"] += 1
    world.say(
        f"{detective.id} crouched by the desk and noticed {clue.visible_trace}, "
        f"a tiny sign that something was hidden inside {place.label}."
    )


def _surprise_turn(world: World, helper: Entity, detective: Entity, clue: Clue) -> None:
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    world.say(
        f'{helper.id} blinked. "{detective.id}, look again," {helper.pronoun()} said. '
        f'The clue had been hidden with a {clue.surprise_trick}.'
    )


def _solve(world: World, detective: Entity, helper: Entity, clue: Clue, method: Method, place: Place) -> None:
    detective.memes["pride"] = detective.memes.get("pride", 0.0) + 1
    helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1
    world.say(
        f"{detective.id} used {method.text.format(clue=clue.label, place=place.label)}. "
        f"The case was solved, and {clue.object_word} came into the light at last."
    )
    world.say(
        f"{helper.id} laughed softly, because the answer had been hiding in plain sight."
    )


def _fail(world: World, detective: Entity, helper: Entity, clue: Clue, method: Method, place: Place) -> None:
    detective.memes["frustration"] = detective.memes.get("frustration", 0.0) + 1
    world.say(
        f"{detective.id} tried {method.fail_text.format(clue=clue.label, place=place.label)}, "
        f"but the hidden place stayed closed."
    )
    world.say(
        f"{helper.id} frowned, and the mystery still waited in the shadows."
    )


def tell(place: Place, clue: Clue, method: Method,
         detective_name: str = "Mina", detective_gender: str = "girl",
         helper_name: str = "Jules", helper_gender: str = "boy",
         delay: int = 0, surprise_note: str = "") -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    case = world.add(Entity(id="case", type="case", label="the case"))
    hidden = world.add(Entity(id="clue", type="clue", label=clue.label))
    world.facts["delay"] = delay
    world.facts["place"] = place
    world.facts["clue_cfg"] = clue
    world.facts["method"] = method
    world.facts["helper"] = helper
    world.facts["detective"] = detective

    detective.memes["curiosity"] = 1.0
    helper.memes["care"] = 1.0

    world.say(
        f"{detective.id} was a little detective with a sharp eye. {helper.id} "
        f"carried a notebook, and together they followed a small mystery in {place.detail}."
    )
    world.say(
        f"They were searching for {clue.object_word}, but the first thing they found was "
        f"{clue.visible_trace}."
    )

    world.para()
    _inspect_trace(world, detective, hidden, place)
    world.say(
        f'"Maybe the answer is there," {helper.id} said. "{surprise_note or "Something feels odd"}."'
    )
    _open_case(world, detective, case)
    if hidden_trace(place, clue):
        _surprise_turn(world, helper, detective, clue)

    if can_reveal(method, place, delay):
        world.para()
        _solve(world, detective, helper, clue, method, place)
        hidden.meters["found"] = 1.0
    else:
        world.para()
        _fail(world, detective, helper, clue, method, place)

    world.say(
        f"By the end, {clue.label} was no longer missing, and the little detective's surprise "
        f"made the whole room feel brighter."
    )

    world.facts.update(found=hidden.meters.get("found", 0.0) >= THRESHOLD)
    return world


PLACES = {
    "study": Place(id="study", label="the study", detail="a quiet room with a desk and a lamp", has_secret_space=True, surprise_kind="false bottom drawer", tags={"study", "mystery"}),
    "kitchen": Place(id="kitchen", label="the kitchen", detail="a bright kitchen with a white table and a small cupboard", has_secret_space=True, surprise_kind="bread box compartment", tags={"kitchen", "mystery"}),
    "attic": Place(id="attic", label="the attic", detail="a dusty attic with boxes and a slanted window", has_secret_space=True, surprise_kind="loose floorboard", tags={"attic", "mystery"}),
}

CLUES = {
    "ring": Clue(id="ring", label="a silver ring", object_word="the silver ring", hidden_in="study", visible_trace="a tiny shine near a book", surprise_trick="false bottom drawer", tags={"metal", "shine"}),
    "key": Clue(id="key", label="a brass key", object_word="the brass key", hidden_in="kitchen", visible_trace="a line of flour leading behind the cupboard", surprise_trick="bread box compartment", tags={"metal", "key"}),
    "map": Clue(id="map", label="a folded map", object_word="the folded map", hidden_in="attic", visible_trace="a corner of paper sticking out from under a trunk", surprise_trick="loose floorboard", tags={"paper", "papertrail"}),
}

METHODS = {
    "slow_search": Method(id="slow_search", label="slow search", sense=3, reveal_power=2, text="slowly searched the {place} until the hidden drawer clicked open", fail_text="slowly searched the {place}, but no hidden clue came out", tags={"search"}),
    "careful_tap": Method(id="careful_tap", label="careful tap", sense=2, reveal_power=3, text="tapped the floor and found the weak board under the rug", fail_text="tapped the floor, but the board stayed stubbornly quiet", tags={"tap"}),
    "lamp_glance": Method(id="lamp_glance", label="lamp glance", sense=4, reveal_power=4, text="shined the lamp across the desk and spotted the clue by the shadow line", fail_text="shined the lamp across the desk, but the shadow line gave nothing away", tags={"lamp"}),
}

SENSE_MIN = 2

GIRL_NAMES = ["Mina", "Ruby", "Nia", "Ivy", "Lena"]
BOY_NAMES = ["Jules", "Theo", "Owen", "Noah", "Evan"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for cid, clue in CLUES.items():
            if clue.hidden_in != pid:
                continue
            for mid, method in METHODS.items():
                if valid_combo(place, clue, method):
                    combos.append((pid, cid, mid))
    return combos


@dataclass
class StoryParams:
    place: str
    clue: str
    method: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    delay: int = 0
    surprise_note: str = ""
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld with a surprise reveal.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
    ap.add_argument("--detective-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.place and CLUES[args.clue].hidden_in != args.place:
        raise StoryError("That clue is not hidden in that place.")
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError("That method is too weak for this detective story.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.method is None or c[2] == args.method)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, method = rng.choice(sorted(combos))
    c = CLUES[clue]
    m = METHODS[method]
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if detective_gender == "girl" else "girl")
    detective_name = args.detective_name or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in (BOY_NAMES if helper_gender == "boy" else GIRL_NAMES) if n != detective_name])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    note = rng.choice(["Wait, that's strange.", "Something is off.", "Look closely."])
    return StoryParams(place=place, clue=clue, method=method,
                       detective_name=detective_name, detective_gender=detective_gender,
                       helper_name=helper_name, helper_gender=helper_gender,
                       delay=delay, surprise_note=note)


def generation_prompts(world: World) -> list[str]:
    p = world.facts["place"]
    c = world.facts["clue_cfg"]
    return [
        f'Write a child-friendly detective story that includes the word "{c.label.split()[1] if " " in c.label else c.label}" and a surprise reveal.',
        f"Tell a detective story where a clue is hidden in {p.label} and the detective notices a surprising trace.",
        f"Write a short mystery with a surprise ending: the detective searches {p.label}, follows a tiny trace, and finds {c.object_word}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["place"]
    c = world.facts["clue_cfg"]
    d = world.facts["detective"]
    h = world.facts["helper"]
    m = world.facts["method"]
    qas = [
        QAItem(question="Who is the story about?", answer=f"It is about {d.id} and {h.id}, who work together as a tiny detective team. They follow a clue and solve the mystery."),
        QAItem(question="What was the surprise in the story?", answer=f"The surprise was that {c.label} was hidden with a {p.surprise_kind}. That meant the clue could be found only after noticing the tiny trace and opening the right place."),
        QAItem(question=f"What did {d.id} notice first?", answer=f"{d.id} noticed {c.visible_trace}. That small sign pointed toward the hidden clue instead of the empty places around it."),
    ]
    if world.facts.get("found"):
        qas.append(QAItem(question="How was the case solved?", answer=f"{d.id} used {m.text.format(place=p.label, clue=c.label)}. The surprise was opened, and the missing clue came out at last."))
        qas.append(QAItem(question="How did the ending feel?", answer=f"It felt bright and happy because the mystery was solved. The room changed from puzzling and quiet to clear and calm."))
    else:
        qas.append(QAItem(question="Why did the clue stay hidden?", answer=f"The method was not strong enough to reveal it, so the hidden place stayed closed. The detective still learned from the trace, but the answer did not come out yet."))
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.facts["place"]
    c = world.facts["clue_cfg"]
    items = [
        QAItem(question="What does a detective do?", answer="A detective looks for clues, notices small details, and tries to solve a mystery."),
        QAItem(question="What is a clue?", answer="A clue is a small sign that helps someone figure out what happened."),
        QAItem(question="What is a surprise?", answer="A surprise is something you do not expect. In a story, it can make the ending feel exciting."),
    ]
    if "shine" in c.tags:
        items.append(QAItem(question="Why can a shine be useful in a mystery?", answer="A little shine can show that something metal is nearby, even when it is partly hidden. That helps a detective know where to look next."))
    if p.has_secret_space:
        items.append(QAItem(question="What is a secret space?", answer="A secret space is a hidden part of a place, like a drawer, floorboard, or compartment. It can keep something tucked away until someone finds the trick to open it."))
    return items


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        parts.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    parts.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(parts)


CURATED = [
    StoryParams(place="study", clue="ring", method="lamp_glance", detective_name="Mina", detective_gender="girl", helper_name="Jules", helper_gender="boy", delay=0, surprise_note="Look closely."),
    StoryParams(place="kitchen", clue="key", method="slow_search", detective_name="Ruby", detective_gender="girl", helper_name="Theo", helper_gender="boy", delay=1, surprise_note="Something is off."),
    StoryParams(place="attic", clue="map", method="careful_tap", detective_name="Noah", detective_gender="boy", helper_name="Ivy", helper_gender="girl", delay=0, surprise_note="Wait, that's strange."),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.method not in METHODS:
        raise StoryError("Invalid parameters.")
    world = tell(PLACES[params.place], CLUES[params.clue], METHODS[params.method],
                 detective_name=params.detective_name, detective_gender=params.detective_gender,
                 helper_name=params.helper_name, helper_gender=params.helper_gender,
                 delay=params.delay, surprise_note=params.surprise_note)
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


ASP_RULES = r"""
place(study). place(kitchen). place(attic).
clue(ring). clue(key). clue(map).
method(slow_search). method(careful_tap). method(lamp_glance).

hidden_in(ring,study). hidden_in(key,kitchen). hidden_in(map,attic).
sense(slow_search,3). sense(careful_tap,2). sense(lamp_glance,4).
power(slow_search,2). power(careful_tap,3). power(lamp_glance,4).
sense_min(2).

valid(P,C,M) :- place(P), clue(C), method(M), hidden_in(C,P), sense(M,S), sense_min(N), S >= N.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("hidden_in", cid, clue.hidden_in))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("power", mid, method.reveal_power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from Python.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: normal generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generate() crashed: {e}")
    return rc


def build_parser_and_resolve():
    pass


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError("That method is too weak for this detective story.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.method is None or c[2] == args.method)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, method = rng.choice(sorted(combos))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if detective_gender == "girl" else "girl")
    detective_name = args.detective_name or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in (BOY_NAMES if helper_gender == "boy" else GIRL_NAMES) if n != detective_name])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place, clue=clue, method=method,
        detective_name=detective_name, detective_gender=detective_gender,
        helper_name=helper_name, helper_gender=helper_gender,
        delay=delay, surprise_note="Look closely."
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective storyworld with a surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--detective-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid detective combos:\n")
        for p, c, m in combos:
            print(f"  {p:8} {c:6} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name} and {p.helper_name}: {p.place}, {p.clue}, {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
