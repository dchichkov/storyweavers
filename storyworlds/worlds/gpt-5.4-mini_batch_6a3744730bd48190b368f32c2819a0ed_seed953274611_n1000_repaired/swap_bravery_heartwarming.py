#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/swap_bravery_heartwarming.py
============================================================

A tiny heartwarming storyworld about a brave child who swaps something
unhelpful for something better, with a warm ending image proving the change.

The world is built around one small premise:
- A child wants to help.
- They face a scary or disappointing moment.
- Bravery lets them ask for help or make a kind swap.
- The ending leaves the world softer, safer, and better than before.

This script is standalone and only uses the stdlib plus the shared Storyweavers
result containers. ASP support is inline and lazy-imported.
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
BRAVERY_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
class Setting:
    id: str
    place: str
    cozy_detail: str
    dark_spot: str
    reason: str
    ending_image: str
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
class ObjectItem:
    id: str
    label: str
    phrase: str
    kind: str
    helpful: bool = False
    comforting: bool = False
    risky: bool = False
    gives_light: bool = False
    covers_need: bool = False
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
class SwapOption:
    id: str
    from_item: str
    to_item: str
    sense: int
    text: str
    qa_text: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["fear"] >= THRESHOLD and ent.memes["bravery"] >= BRAVERY_THRESHOLD:
            sig = ("settle", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["calm"] += 1
            out.append("__settle__")
    return out


CAUSAL_RULES = [Rule("settle", "social", _r_settle)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def swap_is_reasonable(give: ObjectItem, receive: ObjectItem) -> bool:
    return give.risky and (receive.helpful or receive.comforting or receive.gives_light)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for give_id, give in ITEMS.items():
            for receive_id, receive in ITEMS.items():
                if give_id == receive_id:
                    continue
                if swap_is_reasonable(give, receive):
                    combos.append((setting_id, give_id, receive_id))
    return combos


def gentle_prediction(world: World, child: Entity, setting: Setting, give: ObjectItem, receive: ObjectItem) -> dict:
    sim = world.copy()
    _do_swap(sim, sim.get(child.id), setting, give, receive, narrate=False)
    return {
        "settled": sim.get(child.id).memes["calm"] >= THRESHOLD,
        "warmth": sim.get("room").memes["warmth"],
    }


def _do_swap(world: World, child: Entity, setting: Setting, give: ObjectItem, receive: ObjectItem, narrate: bool = True) -> None:
    child.meters[give.id] = 0.0
    child.meters[receive.id] += 1
    child.memes["hope"] += 1
    child.memes["bravery"] += 1
    world.get("room").memes["warmth"] += 1
    propagate(world, narrate=narrate)


def start(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    world.say(f"On a soft afternoon, {child.id} and {helper.id} were at {setting.place}. {setting.cozy_detail}")
    world.say(f"The room felt kind, but {setting.dark_spot} still made {child.id} hesitate.")


def worry(world: World, child: Entity, helper: Entity, setting: Setting, risky: ObjectItem) -> None:
    child.memes["fear"] += 1
    world.say(
        f"{child.id} looked at {risky.phrase} and then at {setting.dark_spot}. "
        f'"I want to help, but I am scared," {child.pronoun()} whispered.'
    )


def brave_turn(world: World, child: Entity, helper: Entity, risky: ObjectItem, safe: ObjectItem, setting: Setting) -> None:
    pred = gentle_prediction(world, child, setting, risky, safe)
    world.facts["predicted_settled"] = pred["settled"]
    world.say(
        f"{child.id} took a breath, held {child.pronoun('possessive')} hands still, "
        f"and said, 'Can we swap {risky.label} for {safe.label} instead?'"
    )
    world.say(
        f"{helper.id} smiled right away. 'That is a brave idea,' {helper.pronoun()} said."
    )


def complete_swap(world: World, child: Entity, helper: Entity, risky: ObjectItem, safe: ObjectItem, setting: Setting) -> None:
    _do_swap(world, child, setting, risky, safe)
    world.say(
        f"Together they made the swap. The {risky.label} went away, and the {safe.label} fit the moment much better."
    )
    world.say(
        f"Right after that, {setting.ending_image}"
    )


def lesson(world: World, child: Entity, helper: Entity, safe: ObjectItem) -> None:
    child.memes["fear"] = 0.0
    child.memes["calm"] += 1
    child.memes["love"] += 1
    world.say(
        f"{helper.id} knelt beside {child.id} and hugged {child.pronoun('object')}. "
        f'"You were brave enough to ask," {helper.pronoun()} said softly. '
        f'"Sometimes the kindest thing is to choose the better thing."'
    )
    world.say(f"{child.id} smiled and held the {safe.label} close.")


def tell(setting: Setting, risky: ObjectItem, safe: ObjectItem, swap_option: SwapOption,
         child_name: str = "Maya", child_gender: str = "girl",
         helper_name: str = "Grandma", helper_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    room = world.add(Entity(id="room", type="room", label="the room"))

    start(world, child, helper, setting)
    world.para()
    worry(world, child, helper, setting, risky)
    brave_turn(world, child, helper, risky, safe, setting)
    world.para()
    complete_swap(world, child, helper, risky, safe, setting)
    lesson(world, child, helper, safe)

    world.facts.update(
        child=child, helper=helper, room=room,
        setting=setting, risky=risky, safe=safe, swap_option=swap_option,
        swapped=True, brave=child.memes["bravery"] >= BRAVERY_THRESHOLD,
    )
    return world


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the classroom corner",
        cozy_detail="A paper lantern glowed on the shelf, and little cushions waited by the rug.",
        dark_spot="the shadow under the reading table",
        reason="a child wants to help with a dark little corner",
        ending_image="the paper lantern glowed warmly, and the reading table looked cozy instead of scary",
        tags={"light", "cozy"},
    ),
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen table",
        cozy_detail="Warm bread smelled sweet, and a small window let in a stripe of morning sun.",
        dark_spot="the space behind the tall chair",
        reason="a child wants to help in a busy, dim spot",
        ending_image="the table shone gently, and the whole kitchen felt bright and safe again",
        tags={"home", "warm"},
    ),
    "bedroom": Setting(
        id="bedroom",
        place="the bedroom floor",
        cozy_detail="A striped blanket was folded neatly, and a tiny lamp made a honey-colored pool of light.",
        dark_spot="the corner beside the toy chest",
        reason="a child wants to help with bedtime things",
        ending_image="the honey lamp made the corner soft and calm, like a sleepy hug",
        tags={"sleep", "warm"},
    ),
}

ITEMS = {
    "candle": ObjectItem(
        id="candle", label="candle", phrase="the little candle", kind="light",
        risky=True, tags={"light", "fire"},
    ),
    "flashlight": ObjectItem(
        id="flashlight", label="flashlight", phrase="the flashlight", kind="light",
        helpful=True, gives_light=True, tags={"light", "safe"},
    ),
    "blanket": ObjectItem(
        id="blanket", label="blanket", phrase="the soft blanket", kind="cloth",
        comforting=True, covers_need=True, tags={"warm", "cozy"},
    ),
    "toy": ObjectItem(
        id="toy", label="toy train", phrase="the toy train", kind="toy",
        comforting=True, tags={"play"},
    ),
    "note": ObjectItem(
        id="note", label="note", phrase="the kind note", kind="paper",
        helpful=True, tags={"kind"},
    ),
    "flower": ObjectItem(
        id="flower", label="flower", phrase="the little flower", kind="gift",
        comforting=True, helpful=True, tags={"kind", "warm"},
    ),
}

SWAPS = {
    "candle_to_flashlight": SwapOption(
        id="candle_to_flashlight",
        from_item="candle",
        to_item="flashlight",
        sense=3,
        text="swapped the candle for the flashlight",
        qa_text="swapped the candle for the flashlight",
        tags={"light", "safety"},
    ),
    "candle_to_blanket": SwapOption(
        id="candle_to_blanket",
        from_item="candle",
        to_item="blanket",
        sense=2,
        text="swapped the candle for the blanket",
        qa_text="swapped the candle for the blanket",
        tags={"cozy"},
    ),
    "candle_to_flower": SwapOption(
        id="candle_to_flower",
        from_item="candle",
        to_item="flower",
        sense=2,
        text="swapped the candle for the flower",
        qa_text="swapped the candle for the flower",
        tags={"warm"},
    ),
    "candle_to_note": SwapOption(
        id="candle_to_note",
        from_item="candle",
        to_item="note",
        sense=2,
        text="swapped the candle for the note",
        qa_text="swapped the candle for the note",
        tags={"kind"},
    ),
}

GIRL_NAMES = ["Maya", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Noah", "Finn", "Eli", "Theo", "Ben", "Max"]


@dataclass
class StoryParams:
    setting: str
    risky: str
    safe: str
    swap: str
    child: str
    child_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld about bravery and a kind swap.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--risky", choices=ITEMS)
    ap.add_argument("--safe", choices=ITEMS)
    ap.add_argument("--swap", choices=SWAPS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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


def explain_rejection(risky: ObjectItem, safe: ObjectItem) -> str:
    return f"(No story: swapping {risky.label} for {safe.label} would not make the moment safer or kinder.)"


def sensible_swaps() -> list[SwapOption]:
    return [s for s in SWAPS.values() if s.sense >= 2]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.risky and args.safe:
        if not swap_is_reasonable(ITEMS[args.risky], ITEMS[args.safe]):
            raise StoryError(explain_rejection(ITEMS[args.risky], ITEMS[args.safe]))
    choices = []
    for sid, setting in SETTINGS.items():
        for rid, risky in ITEMS.items():
            for sid2, safe in ITEMS.items():
                if rid == sid2:
                    continue
                for swid, sw in SWAPS.items():
                    if sw.from_item == rid and sw.to_item == sid2 and swap_is_reasonable(risky, safe):
                        if args.setting and args.setting != sid:
                            continue
                        if args.risky and args.risky != rid:
                            continue
                        if args.safe and args.safe != sid2:
                            continue
                        if args.swap and args.swap != swid:
                            continue
                        choices.append((sid, rid, sid2, swid))
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    setting_id, risky_id, safe_id, swap_id = rng.choice(sorted(choices))
    swap_opt = SWAPS[swap_id]
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    helper = args.helper or rng.choice(["Grandma", "Grandpa", "Mom", "Dad"])
    return StoryParams(
        setting=setting_id,
        risky=risky_id,
        safe=safe_id,
        swap=swap_id,
        child=child,
        child_gender=child_gender,
        helper=helper,
        helper_gender=helper_gender,
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for sid in SETTINGS:
        for rid, risky in ITEMS.items():
            for safeid, safe in ITEMS.items():
                if rid == safeid:
                    continue
                if not swap_is_reasonable(risky, safe):
                    continue
                for swid, sw in SWAPS.items():
                    if sw.from_item == rid and sw.to_item == safeid:
                        out.append((sid, rid, safeid, swid))
    return out


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.risky not in ITEMS or params.safe not in ITEMS or params.swap not in SWAPS:
        raise StoryError("Invalid params.")
    setting = SETTINGS[params.setting]
    risky = ITEMS[params.risky]
    safe = ITEMS[params.safe]
    swap_opt = SWAPS[params.swap]
    if not swap_is_reasonable(risky, safe):
        raise StoryError(explain_rejection(risky, safe))
    world = tell(setting, risky, safe, swap_opt, params.child, params.child_gender, params.helper, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the word "swap" and shows bravery.',
        f"Tell a gentle story where {f['child'].id} is scared but bravely asks to swap something risky for something better.",
        f"Write a cozy story about kindness, courage, and a swap that makes the room feel safer and softer.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    risky = f["risky"]
    safe = f["safe"]
    setting = f["setting"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}. They are the two people who turn a scary moment into a kind one."),
        ("What did the child do bravely?",
         f"{child.id} bravely asked to swap {risky.label} for {safe.label}. That took courage because {risky.label} felt risky at first."),
        ("How did the story end?",
         f"It ended with the safer thing in place and the room feeling warm again. {setting.ending_image}"),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["setting"].tags)
    tags |= set(world.facts["risky"].tags)
    tags |= set(world.facts["safe"].tags)
    qa = []
    if "fire" in tags:
        qa.append(("Why can a candle be dangerous?", "A candle has a real flame, so it can start a fire if it touches something else."))
    if "light" in tags:
        qa.append(("What is a flashlight for?", "A flashlight gives light without a flame, so it is a safer way to see in the dark."))
    if "cozy" in tags or "warm" in tags:
        qa.append(("What makes a room feel cozy?", "Soft things, warm light, and kind people can make a room feel cozy and safe."))
    if "kind" in tags:
        qa.append(("What does kindness look like in a story?", "Kindness can mean helping someone feel safe, listening closely, and choosing a gentle answer."))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="classroom", risky="candle", safe="flashlight", swap="candle_to_flashlight", child="Maya", child_gender="girl", helper="Grandma", helper_gender="woman"),
    StoryParams(setting="kitchen", risky="candle", safe="blanket", swap="candle_to_blanket", child="Noah", child_gender="boy", helper="Mom", helper_gender="woman"),
    StoryParams(setting="bedroom", risky="candle", safe="flower", swap="candle_to_flower", child="Lily", child_gender="girl", helper="Dad", helper_gender="man"),
]


ASP_RULES = r"""
reasonably_safe(S,R,T) :- risky(R), safe(T), risky_item(R), helpful_item(T).
valid(Setting, R, T, Sw) :- setting(Setting), swap(Sw), from(Sw, R), to(Sw, T), reasonably_safe(Setting, R, T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        if item.risky:
            lines.append(asp.fact("risky_item", iid))
        if item.helpful or item.comforting or item.gives_light:
            lines.append(asp.fact("helpful_item", iid))
    for swid, sw in SWAPS.items():
        lines.append(asp.fact("swap", swid))
        lines.append(asp.fact("from", swid, sw.from_item))
        lines.append(asp.fact("to", swid, sw.to_item))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between ASP and Python valid combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    if rc == 0:
        print("OK: ASP parity and story generation smoke test passed.")
    return rc


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
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


def _seed_validate() -> None:
    pass


if __name__ == "__main__":
    main()
