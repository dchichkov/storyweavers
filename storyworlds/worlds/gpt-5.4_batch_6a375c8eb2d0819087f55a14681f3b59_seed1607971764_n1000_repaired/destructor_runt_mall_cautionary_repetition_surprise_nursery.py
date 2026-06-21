#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/destructor_runt_mall_cautionary_repetition_surprise_nursery.py
=========================================================================================

A standalone story world for a nursery-rhyme-shaped cautionary tale about
little Runt at the mall. Runt keeps tapping the demo button on a toy called the
Destructor beside a high display. The repeated tapping makes the display wobble.
A calm grown-up warns Runt, and the story turns on whether Runt heeds the
warning in time. Either way, the ending changes the world: the dangerous shelf
play is replaced by a low, safe surprise.

The domain is intentionally small and constrained:

* The setting is always a mall toy shop or kiosk.
* The repeated action is always the same tempting act: tapping the demo button.
* The hazard is only reasonable when the chosen display is actually fragile.
* The surprise ending must also be sensible: a safe low play setup strong enough
  for the chosen display pieces.

Run it
------
    python storyworlds/worlds/gpt-5.4/destructor_runt_mall_cautionary_repetition_surprise_nursery.py
    python storyworlds/worlds/gpt-5.4/destructor_runt_mall_cautionary_repetition_surprise_nursery.py --display cup_castle
    python storyworlds/worlds/gpt-5.4/destructor_runt_mall_cautionary_repetition_surprise_nursery.py --surprise ribbon_hat
    python storyworlds/worlds/gpt-5.4/destructor_runt_mall_cautionary_repetition_surprise_nursery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/destructor_runt_mall_cautionary_repetition_surprise_nursery.py --all
    python storyworlds/worlds/gpt-5.4/destructor_runt_mall_cautionary_repetition_surprise_nursery.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
URGE_TO_TAP = 3


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    movable: bool = True
    fragile: bool = False
    low_safe: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "clerk_woman", "woman"}
        male = {"boy", "father", "uncle", "clerk_man", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
            "clerk_woman": "clerk",
            "clerk_man": "clerk",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Display:
    id: str
    label: str
    phrase: str
    pieces: str
    wobble_text: str
    fall_text: str
    fragility: int
    fragile: bool = True
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
class Surprise:
    id: str
    label: str
    phrase: str
    setup_text: str
    ending_text: str
    qa_text: str
    sense: int
    power: int
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
class HelperKind:
    id: str
    type: str
    title: str
    authority: int
    gentle_line: str
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
    display: str
    surprise: str
    helper: str
    trait: str
    runt_name: str = "Runt"
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
        self.trace_lines: list[str] = []

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
        clone.trace_lines = []
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    machine = world.get("machine")
    display = world.get("display")
    if machine.meters["rolling"] < THRESHOLD:
        return out
    sig = ("wobble", int(machine.meters["rolling"]), int(display.meters["wobble"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    display.meters["wobble"] += world.facts["machine_force"]
    if display.meters["wobble"] >= THRESHOLD and display.meters["toppled"] < THRESHOLD:
        out.append("__wobble__")
    return out


def _r_topple(world: World) -> list[str]:
    out: list[str] = []
    display = world.get("display")
    runt = world.get("runt")
    shop = world.get("shop")
    if display.meters["wobble"] < world.facts["display_fragility"]:
        return out
    sig = ("topple", display.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    display.meters["toppled"] += 1
    display.meters["scattered"] += 1
    shop.meters["mess"] += 1
    runt.memes["fear"] += 1
    runt.memes["lesson"] += 1
    out.append("__topple__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="topple", tag="physical", apply=_r_topple),
]


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
        for sent in produced:
            world.say(sent)
    return produced


DISPLAYS = {
    "block_town": Display(
        id="block_town",
        label="block town",
        phrase="a tiny block town with square blue doors",
        pieces="wooden blocks",
        wobble_text="The little houses gave a shiver and a sway.",
        fall_text="Down came the block town, clack-clack-clatter, all over the mat.",
        fragility=3,
        fragile=True,
        tags={"blocks", "topple"},
    ),
    "cup_castle": Display(
        id="cup_castle",
        label="cup castle",
        phrase="a tall cup castle stacked in shiny rings",
        pieces="paper cups",
        wobble_text="The cup castle trembled like a bell in a breeze.",
        fall_text="Down came the cup castle, flip-flap-flutter, cups rolling every way.",
        fragility=2,
        fragile=True,
        tags={"cups", "topple"},
    ),
    "card_bridge": Display(
        id="card_bridge",
        label="card bridge",
        phrase="a card bridge with a silver road beneath",
        pieces="stiff cards",
        wobble_text="The card bridge quivered, thin and twitchy.",
        fall_text="Down came the card bridge, whisper-whisk-swish, sliding into a heap.",
        fragility=2,
        fragile=True,
        tags={"cards", "topple"},
    ),
    "stone_arch": Display(
        id="stone_arch",
        label="stone arch",
        phrase="a heavy stone arch of painted foam rock",
        pieces="foam stones",
        wobble_text="The stone arch barely nodded at all.",
        fall_text="The stone arch did not fall.",
        fragility=99,
        fragile=False,
        tags={"stones"},
    ),
}

SURPRISES = {
    "road_mat": Surprise(
        id="road_mat",
        label="road mat",
        phrase="a soft road mat spread flat on the floor",
        setup_text="unrolled a soft road mat on the floor and set the game down low",
        ending_text="On the low road mat, the wheels could hum without knocking anything high.",
        qa_text="set up a soft road mat on the floor for safe play",
        sense=3,
        power=3,
        tags={"safe_play", "floor"},
    ),
    "foam_ring": Surprise(
        id="foam_ring",
        label="foam ring",
        phrase="a round foam ring with plenty of room inside",
        setup_text="set a round foam ring on the floor and made a little play circle",
        ending_text="Inside the foam ring, the Destructor could rumble and the pieces stayed where they belonged.",
        qa_text="made a safe foam play circle on the floor",
        sense=3,
        power=2,
        tags={"safe_play", "floor"},
    ),
    "tray_track": Surprise(
        id="tray_track",
        label="tray track",
        phrase="a low tray track with raised wooden sides",
        setup_text="brought a low tray track with raised sides and moved the pieces inside it",
        ending_text="Inside the tray track, the rolling toy could race and the little pieces could not scatter away.",
        qa_text="moved the play onto a low tray track with raised sides",
        sense=3,
        power=3,
        tags={"safe_play", "tray"},
    ),
    "ribbon_hat": Surprise(
        id="ribbon_hat",
        label="ribbon hat",
        phrase="a ribbon hat with a silver bow",
        setup_text="plopped a ribbon hat on Runt's head and laughed",
        ending_text="The hat was funny, but it did not make the shelf safer.",
        qa_text="put a funny ribbon hat on Runt",
        sense=1,
        power=0,
        tags={"silly"},
    ),
}

HELPERS = {
    "aunt": HelperKind(
        id="aunt",
        type="aunt",
        title="Aunt May",
        authority=3,
        gentle_line="Small paws, small pause, little one.",
        tags={"family"},
    ),
    "clerk": HelperKind(
        id="clerk",
        type="clerk_woman",
        title="Ms. Bell",
        authority=2,
        gentle_line="Mall toys may hum, but high shelves are not for drumming.",
        tags={"shop"},
    ),
    "dad": HelperKind(
        id="dad",
        type="father",
        title="Dad",
        authority=3,
        gentle_line="Tap on the floor, not near the store display.",
        tags={"family"},
    ),
}

TRAITS = {
    "careful": 2,
    "thoughtful": 2,
    "bouncy": 1,
    "eager": 1,
    "stubborn": 0,
}

RUNT_NAMES = ["Runt", "Runt Pip", "Runt Dot"]


def display_at_risk(display: Display) -> bool:
    return display.fragile


def sensible_surprises() -> list[Surprise]:
    return [s for s in SURPRISES.values() if s.sense >= SENSE_MIN]


def surprise_fits(display: Display, surprise: Surprise) -> bool:
    return surprise.power >= display.fragility


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for did, display in DISPLAYS.items():
        if not display_at_risk(display):
            continue
        for sid, surprise in SURPRISES.items():
            if surprise.sense >= SENSE_MIN and surprise_fits(display, surprise):
                combos.append((did, sid))
    return combos


def would_heed(helper: HelperKind, trait: str) -> bool:
    return helper.authority + TRAITS[trait] > URGE_TO_TAP


def predict_topple(world: World, extra_taps: int) -> dict:
    sim = world.copy()
    for _ in range(extra_taps):
        _tap_machine(sim, narrate=False)
    display = sim.get("display")
    return {
        "toppled": display.meters["toppled"] >= THRESHOLD,
        "wobble": int(display.meters["wobble"]),
    }


def _tap_machine(world: World, narrate: bool = True) -> None:
    runt = world.get("runt")
    machine = world.get("machine")
    display = world.get("display")
    runt.memes["delight"] += 1
    machine.meters["rolling"] += 1
    world.facts["tap_count"] += 1
    produced = propagate(world, narrate=False)
    if narrate:
        tap_no = world.facts["tap_count"]
        if tap_no == 1:
            world.say(f'Tap, tap, tap went {runt.id}. The little Destructor gave a growly whirr.')
        elif tap_no == 2:
            world.say(f'Tap again, tap again, tap went {runt.id}. The Destructor bumped the shelf once more.')
        else:
            world.say(f'Tap once more, tap once more, tap went {runt.id}. The toy rumbled harder than before.')
        if "__wobble__" in produced and display.meters["toppled"] < THRESHOLD:
            world.say(display.attrs["wobble_text"])


def introduce(world: World, runt: Entity, helper: Entity, display: Display) -> None:
    world.say(
        f"In the mall, in the mall, under lights both bright and tall, "
        f"{runt.id} the little runt trotted by a toy-shop wall."
    )
    world.say(
        f"There sat the Destructor, shiny and red, beside {display.phrase}. "
        f"{helper.id} held {runt.pronoun('possessive')} hand and smiled."
    )
    world.say(
        f'"Look with your eyes, not with wild little paws," said {helper.id}.'
    )


def temptation(world: World, runt: Entity) -> None:
    runt.memes["temptation"] += 1
    world.say(
        f"But the button was round, and the button was bright, and it winked at {runt.id} in the mall-shop light."
    )


def warning(world: World, runt: Entity, helper: Entity, display: Display) -> None:
    pred = predict_topple(world, 1)
    runt.memes["caution_heard"] += 1
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_topple"] = pred["toppled"]
    if pred["toppled"]:
        line = (
            f'"Hush now, hush now," said {helper.id}. '
            f'"One more tap and down it goes. High things tumble faster than small feet can chase."'
        )
    else:
        line = (
            f'"Hush now, hush now," said {helper.id}. '
            f'"See it sway? High things should stay. Little taps can make big messes."'
        )
    world.say(line)
    world.say(helper.attrs["gentle_line"])


def heed(world: World, runt: Entity, helper: Entity) -> None:
    runt.memes["relief"] += 1
    runt.memes["lesson"] += 1
    world.say(
        f"{runt.id} looked at the wobbling shelf, looked at {helper.id}, and tucked {runt.pronoun('possessive')} paws close."
    )
    world.say(
        f'"No more tap, no more tap," whispered {runt.id}.'
    )


def ignore(world: World, runt: Entity) -> None:
    runt.memes["defiance"] += 1
    world.say(
        f"But the rhyme in {runt.pronoun('possessive')} head went tap-tap-tap, and {runt.id} bounced on tiptoe with a grin."
    )


def topple(world: World, display_cfg: Display) -> None:
    _tap_machine(world, narrate=True)
    if world.get("display").meters["toppled"] >= THRESHOLD:
        world.say(display_cfg.fall_text)


def comfort(world: World, runt: Entity, helper: Entity) -> None:
    runt.memes["fear"] = 0.0
    runt.memes["relief"] += 1
    helper.memes["calm"] += 1
    world.say(
        f'No one was hurt. {helper.id} knelt low and gave {runt.id} a calm hug.'
    )
    world.say(
        f'"We fix with quiet hands," said {helper.id}. "We do not drum on high displays."'
    )


def safe_surprise(world: World, runt: Entity, helper: Entity, surprise: Surprise, display_cfg: Display) -> None:
    world.get("safe_zone").meters["ready"] += 1
    runt.memes["joy"] += 1
    runt.memes["lesson"] += 1
    world.say(
        f"Then came a surprise: {helper.id} {surprise.setup_text}."
    )
    world.say(
        f'"Low and slow, low and slow," sang {helper.id}. '
        f'"That is where the Destructor may go."'
    )
    if world.get("display").meters["toppled"] >= THRESHOLD:
        world.say(
            f"{helper.id} gathered the {display_cfg.pieces} and made a new little play place down below."
        )
    world.say(
        f"{surprise.ending_text} {runt.id} laughed, but this time the laugh was gentle."
    )


def ending(world: World, runt: Entity) -> None:
    if world.get("display").meters["toppled"] >= THRESHOLD:
        world.say(
            f"So in the mall, in the mall, {runt.id} remembered it all: high shelf, small tap, great big sprawl."
        )
    else:
        world.say(
            f"So in the mall, in the mall, {runt.id} remembered it all: stop when warned, and nothing need fall."
        )
    world.say(
        f"And ever after, when a button gleamed bright, {runt.id} asked for a safe low place before play began."
    )


def tell(display: Display, surprise: Surprise, helper_kind: HelperKind,
         trait: str, runt_name: str = "Runt") -> World:
    world = World()

    runt = world.add(Entity(
        id=runt_name,
        kind="character",
        type="animal",
        label="the little runt",
        role="runt",
        traits=[trait, "small"],
        attrs={},
    ))
    helper = world.add(Entity(
        id=helper_kind.title,
        kind="character",
        type=helper_kind.type,
        label="the helper",
        role="helper",
        attrs={"gentle_line": helper_kind.gentle_line},
    ))
    machine = world.add(Entity(
        id="machine",
        kind="thing",
        type="toy",
        label="Destructor",
        phrase="the red Destructor",
        attrs={},
    ))
    display_ent = world.add(Entity(
        id="display",
        kind="thing",
        type="display",
        label=display.label,
        phrase=display.phrase,
        fragile=display.fragile,
        attrs={"wobble_text": display.wobble_text},
    ))
    safe_zone = world.add(Entity(
        id="safe_zone",
        kind="thing",
        type="safe_zone",
        label=surprise.label,
        low_safe=True,
        attrs={},
    ))
    shop = world.add(Entity(
        id="shop",
        kind="thing",
        type="mall_shop",
        label="the mall toy shop",
        attrs={},
    ))

    world.facts["tap_count"] = 0
    world.facts["machine_force"] = 1
    world.facts["display_fragility"] = display.fragility
    world.facts["heeded"] = False
    world.facts["toppled"] = False
    world.facts["display_cfg"] = display
    world.facts["surprise_cfg"] = surprise
    world.facts["helper_cfg"] = helper_kind
    world.facts["trait"] = trait

    introduce(world, runt, helper, display)
    temptation(world, runt)

    world.para()
    _tap_machine(world, narrate=True)
    _tap_machine(world, narrate=True)
    warning(world, runt, helper, display)

    heeded = would_heed(helper_kind, trait)
    world.facts["heeded"] = heeded

    world.para()
    if heeded:
        heed(world, runt, helper)
        safe_surprise(world, runt, helper, surprise, display)
    else:
        ignore(world, runt)
        topple(world, display)
        world.facts["toppled"] = world.get("display").meters["toppled"] >= THRESHOLD
        world.para()
        comfort(world, runt, helper)
        safe_surprise(world, runt, helper, surprise, display)

    world.para()
    ending(world, runt)

    world.facts.update(
        runt=runt,
        helper=helper,
        machine=machine,
        display=display_ent,
        shop=shop,
        surprise=surprise,
        outcome="averted" if heeded else "toppled",
        toppled=world.get("display").meters["toppled"] >= THRESHOLD,
        safe_ready=world.get("safe_zone").meters["ready"] >= THRESHOLD,
    )
    return world


def explain_display_rejection(display: Display) -> str:
    return (
        f"(No story: {display.phrase} is too sturdy for this cautionary world. "
        f"If the Destructor cannot truly threaten it, the warning feels false. "
        f"Pick a fragile display like a cup castle or card bridge.)"
    )


def explain_surprise_rejection(surprise_id: str, display: Display) -> str:
    surprise = SURPRISES[surprise_id]
    if surprise.sense < SENSE_MIN:
        return (
            f"(Refusing surprise '{surprise_id}': it is too silly to solve the problem "
            f"(sense={surprise.sense} < {SENSE_MIN}). The ending must offer a real safe place to play.)"
        )
    return (
        f"(No story: {surprise.phrase} is not strong enough for {display.label}. "
        f"The surprise must actually make play safer, not just look cheerful.)"
    )


def outcome_of(params: StoryParams) -> str:
    helper = HELPERS[params.helper]
    return "averted" if would_heed(helper, params.trait) else "toppled"


def generation_prompts(world: World) -> list[str]:
    runt = world.facts["runt"]
    helper = world.facts["helper"]
    display_cfg = world.facts["display_cfg"]
    outcome = world.facts["outcome"]
    if outcome == "averted":
        return [
            'Write a nursery-rhyme-style cautionary story set in a mall, using the words "destructor", "runt", and "mall".',
            f"Tell a rhythmic story where {runt.id}, a little runt, keeps tapping a toy called the Destructor near a {display_cfg.label}, but listens just in time when {helper.id} warns about the wobble.",
            "Write a repetitive, child-facing story with a surprise safe-play ending, where the danger is avoided before anything falls.",
        ]
    return [
        'Write a nursery-rhyme-style cautionary story set in a mall, using the words "destructor", "runt", and "mall".',
        f"Tell a rhythmic story where {runt.id}, a little runt, repeats the same tempting tap on the Destructor until a high {display_cfg.label} tumbles, and then a calm grown-up teaches a safer way.",
        "Write a story with repetition, a mild surprise, and a clear lesson that high displays are not for rough play.",
    ]


KNOWLEDGE = {
    "topple": [
        (
            "Why can a high stack fall when it starts to wobble?",
            "A tall stack can fall because its pieces are balanced above the floor. When it wobbles too much, gravity pulls it down."
        )
    ],
    "mall": [
        (
            "What is a mall?",
            "A mall is a big building with many shops inside. People go there to buy things, walk around, and visit stores together."
        )
    ],
    "safe_play": [
        (
            "Why is it safer to play with rolling toys on the floor?",
            "The floor is low, so toys have less chance to knock high things down. A low play place also keeps small pieces from scattering far away."
        )
    ],
    "blocks": [
        (
            "What are blocks used for?",
            "Blocks are pieces children can stack and arrange to make towers, houses, and little towns. They can topple if you bump them too hard."
        )
    ],
    "cups": [
        (
            "Why do stacked cups tumble easily?",
            "Stacked cups are light and tall, so even a small bump can make them slide and tip. That is why careful hands matter around them."
        )
    ],
    "cards": [
        (
            "Why is a card bridge delicate?",
            "A card bridge stands only because its cards balance carefully together. A shake or a bump can make the whole thing slide apart."
        )
    ],
}


def story_qa(world: World) -> list[tuple[str, str]]:
    runt = world.facts["runt"]
    helper = world.facts["helper"]
    display_cfg = world.facts["display_cfg"]
    surprise = world.facts["surprise_cfg"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {runt.id}, a little runt at the mall, and {helper.id}, the grown-up who stayed close. They stood by a shiny toy called the Destructor."
        ),
        (
            "What did Runt keep doing again and again?",
            f"{runt.id} kept tapping the demo button on the Destructor. The repeated tapping made the toy rumble beside the high {display_cfg.label}."
        ),
        (
            f"Why did {helper.id} warn {runt.id}?",
            f"{helper.id} warned {runt.id} because the {display_cfg.label} was already wobbling. One more tap could make it topple, so the warning came from a real danger in front of them."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What changed when {runt.id} listened?",
                f"{runt.id} stopped before the last dangerous tap, so the {display_cfg.label} stayed up. Then {helper.id} surprised {runt.pronoun('object')} with a safer place to play down low."
            )
        )
        qa.append(
            (
                "What was the surprise at the end?",
                f"The surprise was that {helper.id} {surprise.qa_text}. That gave the Destructor a safe place to roll without bothering anything high."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {runt.id} did not stop?",
                f"The {display_cfg.label} toppled and its pieces scattered across the shop. No one was hurt, but the tumble showed how a small repeated act can make a big mess."
            )
        )
        qa.append(
            (
                "How did the grown-up fix the problem afterward?",
                f"{helper.id} stayed calm, comforted {runt.id}, and {surprise.qa_text}. The new low setup changed the play itself, so the same toy could be used more safely."
            )
        )
        qa.append(
            (
                "What lesson did Runt learn?",
                f"{runt.id} learned that high displays are for looking, not rough tapping. The surprise ending taught a better habit: ask for a low safe place before play begins."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mall"}
    display_cfg = world.facts["display_cfg"]
    surprise = world.facts["surprise_cfg"]
    tags |= set(display_cfg.tags)
    tags |= set(surprise.tags)
    out: list[tuple[str, str]] = []
    for tag in ["mall", "topple", "blocks", "cups", "cards", "safe_play"]:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.fragile:
            bits.append("fragile=True")
        if ent.low_safe:
            bits.append("low_safe=True")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
display_at_risk(D) :- display(D), fragile(D).

sensible(S) :- surprise(S), sense(S, N), sense_min(M), N >= M.
fits(D, S) :- display(D), surprise(S), fragility(D, F), power(S, P), P >= F.
valid(D, S) :- display_at_risk(D), sensible(S), fits(D, S).

trait_caution(2) :- chosen_trait(T), cautious_trait(T).
trait_caution(1) :- chosen_trait(T), middling_trait(T).
trait_caution(0) :- chosen_trait(T), not cautious_trait(T), not middling_trait(T).

heed :- helper_authority(H), trait_caution(C), urge(U), H + C > U.
outcome(averted) :- heed.
outcome(toppled) :- not heed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for did, display in DISPLAYS.items():
        lines.append(asp.fact("display", did))
        lines.append(asp.fact("fragility", did, display.fragility))
        if display.fragile:
            lines.append(asp.fact("fragile", did))
    for sid, surprise in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("sense", sid, surprise.sense))
        lines.append(asp.fact("power", sid, surprise.power))
    for trait, score in TRAITS.items():
        lines.append(asp.fact("trait_name", trait))
        if score >= 2:
            lines.append(asp.fact("cautious_trait", trait))
        elif score == 1:
            lines.append(asp.fact("middling_trait", trait))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("authority", hid, helper.authority))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("urge", URGE_TO_TAP))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(v for (v,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_trait", params.trait),
        asp.fact("chosen_helper", params.helper),
        asp.fact("helper_authority", HELPERS[params.helper].authority),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


CURATED = [
    StoryParams(
        display="cup_castle",
        surprise="foam_ring",
        helper="clerk",
        trait="eager",
        runt_name="Runt",
    ),
    StoryParams(
        display="block_town",
        surprise="road_mat",
        helper="aunt",
        trait="careful",
        runt_name="Runt Pip",
    ),
    StoryParams(
        display="card_bridge",
        surprise="tray_track",
        helper="dad",
        trait="stubborn",
        runt_name="Runt Dot",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: little Runt, the Destructor, and a mall display."
    )
    ap.add_argument("--display", choices=DISPLAYS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("--runt-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible display/surprise set from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.display:
        display = DISPLAYS[args.display]
        if not display_at_risk(display):
            raise StoryError(explain_display_rejection(display))
    if args.display and args.surprise:
        display = DISPLAYS[args.display]
        if SURPRISES[args.surprise].sense < SENSE_MIN or not surprise_fits(display, SURPRISES[args.surprise]):
            raise StoryError(explain_surprise_rejection(args.surprise, display))

    combos = [
        combo for combo in valid_combos()
        if (args.display is None or combo[0] == args.display)
        and (args.surprise is None or combo[1] == args.surprise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    display_id, surprise_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    trait = args.trait or rng.choice(sorted(TRAITS))
    runt_name = args.runt_name or rng.choice(RUNT_NAMES)

    return StoryParams(
        display=display_id,
        surprise=surprise_id,
        helper=helper_id,
        trait=trait,
        runt_name=runt_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.display not in DISPLAYS:
        raise StoryError(f"(Unknown display '{params.display}'.)")
    if params.surprise not in SURPRISES:
        raise StoryError(f"(Unknown surprise '{params.surprise}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'.)")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait '{params.trait}'.)")

    display = DISPLAYS[params.display]
    surprise = SURPRISES[params.surprise]
    helper = HELPERS[params.helper]

    if not display_at_risk(display):
        raise StoryError(explain_display_rejection(display))
    if surprise.sense < SENSE_MIN or not surprise_fits(display, surprise):
        raise StoryError(explain_surprise_rejection(params.surprise, display))

    world = tell(
        display=display,
        surprise=surprise,
        helper_kind=helper,
        trait=params.trait,
        runt_name=params.runt_name,
    )

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


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {s.id for s in sensible_surprises()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible surprises match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible surprises: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases: list[StoryParams] = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(11))
        smoke_sample = generate(smoke_params)
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(smoke_sample, trace=False, qa=True)
        if not smoke_sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible()
        print(f"sensible surprises: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (display, surprise) combos:\n")
        for display_id, surprise_id in combos:
            print(f"  {display_id:12} {surprise_id}")
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
            header = f"### {p.runt_name}: {p.display} with {p.surprise} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
