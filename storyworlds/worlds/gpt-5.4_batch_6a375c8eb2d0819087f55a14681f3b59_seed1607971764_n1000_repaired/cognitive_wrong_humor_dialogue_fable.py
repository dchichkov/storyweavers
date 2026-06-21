#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cognitive_wrong_humor_dialogue_fable.py
==================================================================

A standalone story world about a foolish shortcut at a forest snack stall.

Tiny premise
------------
A hungry animal wants a treat from a row of covered dishes. Instead of checking,
the animal trusts a silly rule such as "the tallest lid hides the best food."
A friend points out that this is only a cognitive shortcut and may be wrong.
Sometimes the hungry animal listens in time; sometimes the animal opens the
wrong dish first and gets a comic surprise. Then a better method -- smelling,
reading tags, or asking the baker -- reveals the right dish.

The resulting stories are short, dialogue-heavy, a little funny, and shaped
like simple fables: a desire, a wrong idea, a correction, and an ending image
that shows wiser behavior.

Run it
------
    python storyworlds/worlds/gpt-5.4/cognitive_wrong_humor_dialogue_fable.py
    python storyworlds/worlds/gpt-5.4/cognitive_wrong_humor_dialogue_fable.py --target honey_bun --method sniff
    python storyworlds/worlds/gpt-5.4/cognitive_wrong_humor_dialogue_fable.py --method sniff --target rice_cake
    python storyworlds/worlds/gpt-5.4/cognitive_wrong_humor_dialogue_fable.py --all
    python storyworlds/worlds/gpt-5.4/cognitive_wrong_humor_dialogue_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/cognitive_wrong_humor_dialogue_fable.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"hen", "vixen", "doe"}
        male = {"fox", "crow", "bear", "mole", "badger", "hare", "wolf"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------
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
class Treat:
    id: str
    label: str
    phrase: str
    aroma: str
    tag_symbol: str
    fragrant: bool = True
    tagged: bool = True
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
class Decoy:
    id: str
    label: str
    phrase: str
    reaction: str
    after_line: str
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
class Shortcut:
    id: str
    saying: str
    cue: str
    pick_text: str
    decoy: str
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
    can_smell: bool = False
    can_read: bool = False
    can_ask: bool = False
    action_text: str = ""
    proof_text: str = ""
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_wrong_bite(world: World) -> list[str]:
    out: list[str] = []
    chooser = world.get("chooser")
    wrong = world.get("wrong_dish")
    if chooser.meters["ate_wrong"] < THRESHOLD:
        return out
    sig = ("wrong_bite", wrong.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    chooser.meters["hunger"] += 1
    chooser.meters["sneeze"] += 1
    chooser.memes["embarrassment"] += 1
    chooser.memes["respect_for_helper"] += 1
    out.append("__wrong__")
    return out


def _r_found_right(world: World) -> list[str]:
    out: list[str] = []
    chooser = world.get("chooser")
    right = world.get("right_dish")
    if right.meters["chosen"] < THRESHOLD:
        return out
    sig = ("found_right", right.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    chooser.meters["hunger"] = 0.0
    chooser.memes["joy"] += 1
    chooser.memes["wisdom"] += 1
    chooser.memes["trust"] += 1
    out.append("__right__")
    return out


CAUSAL_RULES = [
    Rule(name="wrong_bite", tag="physical", apply=_r_wrong_bite),
    Rule(name="found_right", tag="resolution", apply=_r_found_right),
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
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------
def method_reveals(method: Method, treat: Treat) -> bool:
    if method.can_ask:
        return True
    if method.can_read and treat.tagged:
        return True
    if method.can_smell and treat.fragrant:
        return True
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for treat_id in TREATS:
        for shortcut_id, shortcut in SHORTCUTS.items():
            if shortcut.decoy == treat_id:
                continue
            for method_id, method in METHODS.items():
                if method_reveals(method, TREATS[treat_id]):
                    combos.append((treat_id, shortcut_id, method_id))
    return combos


def chooser_resists(chooser_trait: str, helper_trait: str) -> bool:
    return CHOOSER_TRAITS[chooser_trait] >= HELPER_TRAITS[helper_trait]


def explain_method_rejection(method: Method, treat: Treat) -> str:
    if method.id == "sniff":
        return (
            f"(No story: {treat.phrase} does not give off a strong smell here, so "
            f"sniffing would not honestly reveal it. Pick read_tag or ask_baker.)"
        )
    if method.id == "read_tag":
        return (
            f"(No story: {treat.phrase} has no clear tag to read here, so reading "
            f"would not solve the puzzle. Pick sniff or ask_baker.)"
        )
    return "(No story: that checking method would not reveal the right dish.)"


def explain_combo_rejection(treat: Treat, shortcut: Shortcut, method: Method) -> str:
    if shortcut.decoy == treat.id:
        return (
            f"(No story: the shortcut '{shortcut.id}' accidentally points to the "
            f"real treat {treat.label}, so there is no wrong guess to correct.)"
        )
    return explain_method_rejection(method, treat)


def outcome_of(params: "StoryParams") -> str:
    return "oops" if chooser_resists(params.chooser_trait, params.helper_trait) else "averted"


# ---------------------------------------------------------------------------
# Silent prediction
# ---------------------------------------------------------------------------
def predict_shortcut(world: World) -> dict:
    sim = world.copy()
    _open_wrong(sim, narrate=False)
    return {
        "wrong_opened": sim.get("chooser").meters["ate_wrong"] >= THRESHOLD,
        "sneeze": sim.get("chooser").meters["sneeze"],
        "hunger": sim.get("chooser").meters["hunger"],
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, chooser: Entity, helper: Entity, baker: Entity) -> None:
    chooser.memes["appetite"] += 1
    helper.memes["care"] += 1
    world.say(
        f"At the edge of the forest fair, {baker.id} the {baker.type} set three "
        f"covered dishes on a stump table. {chooser.id} the {chooser.type} and "
        f"{helper.id} the {helper.type} stopped to look, because the warm air "
        f"smelled of lunch and nonsense."
    )


def desire(world: World, chooser: Entity, treat: Treat) -> None:
    chooser.meters["hunger"] = 1.0
    world.say(
        f'"I hope one of those lids hides {treat.phrase}," said {chooser.id}. '
        f"{chooser.pronoun().capitalize()} licked {chooser.pronoun('possessive')} "
        f"lips and stared as if wishing could lift metal."
    )


def temptation(world: World, chooser: Entity, shortcut: Shortcut) -> None:
    chooser.memes["pride"] += 1
    world.say(
        f'{chooser.id} puffed up and announced, "{shortcut.saying}"'
    )
    world.say(
        f"{chooser.pronoun().capitalize()} pointed at {shortcut.pick_text} and "
        f"added, \"I do not need patience. I have a plan.\""
    )


def warning(world: World, helper: Entity, chooser: Entity, shortcut: Shortcut) -> None:
    pred = predict_shortcut(world)
    world.facts["predicted_sneeze"] = pred["sneeze"]
    helper.memes["concern"] += 1
    extra = " and make you sneeze in front of the whole fair" if pred["sneeze"] >= THRESHOLD else ""
    world.say(
        f'{helper.id} tilted {helper.pronoun("possessive")} head. "That is a '
        f'cognitive shortcut," {helper.pronoun()} said. "It may be wrong{extra}. '
        f'The {shortcut.cue} tells you about the lid, not the lunch."'
    )


def argue(world: World, chooser: Entity) -> None:
    chooser.memes["stubbornness"] += 1
    world.say(
        f'"Wrong?" said {chooser.id}. "Then the world is being very rude today."'
    )


def listen(world: World, chooser: Entity, helper: Entity) -> None:
    chooser.memes["humility"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{chooser.id} twitched one ear, thought a little longer, and let the paw "
        f"above the lid drift back down. \"Very well,\" {chooser.pronoun()} said. "
        f"\"I shall try wisdom before mustard.\""
    )


def _open_wrong(world: World, narrate: bool = True) -> None:
    chooser = world.get("chooser")
    wrong = world.get("wrong_dish")
    wrong.meters["opened"] += 1
    chooser.meters["ate_wrong"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"{chooser.id} flipped the lid anyway. Inside sat {wrong.attrs['phrase']}. "
            f"{wrong.attrs['reaction']}"
        )
        world.say(
            f'"Oh," said {chooser.id}. "{wrong.attrs["after_line"]}"'
        )


def mistake(world: World, chooser: Entity, helper: Entity) -> None:
    _open_wrong(world, narrate=True)
    helper.memes["patience"] += 1
    world.say(
        f'{helper.id} did not laugh at first. Then one small chuckle escaped. '
        f'"Shall we try evidence now?" {helper.pronoun()} asked.'
    )


def investigate(world: World, helper: Entity, baker: Entity, method: Method, treat: Treat) -> None:
    helper.memes["care"] += 1
    if method.can_smell:
        world.say(
            f'{helper.id} closed {helper.pronoun("possessive")} eyes and {method.action_text}. '
            f'"There -- {method.proof_text.format(aroma=treat.aroma)}," {helper.pronoun()} said.'
        )
    elif method.can_read:
        world.say(
            f'{helper.id} leaned close and {method.action_text}. '
            f'"There -- {method.proof_text.format(tag=treat.tag_symbol)}," {helper.pronoun()} said.'
        )
    else:
        world.say(
            f'{helper.id} {method.action_text}. "{method.proof_text.format(baker=baker.id, treat=treat.label)}"'
        )


def choose_right(world: World, chooser: Entity, treat: Treat) -> None:
    right = world.get("right_dish")
    right.meters["chosen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Under the proper lid waited {treat.phrase}, warm and shining. "
        f"{chooser.id}'s nose softened, and even the fair looked kinder."
    )


def share(world: World, chooser: Entity, helper: Entity, treat: Treat, baker: Entity) -> None:
    chooser.memes["gratitude"] += 1
    helper.memes["joy"] += 1
    world.say(
        f'"Let us split it," said {chooser.id}. "{treat.label.capitalize()} tastes '
        f'better when pride is smaller."'
    )
    world.say(
        f'{baker.id} the {baker.type} laughed into {baker.pronoun("possessive")} whiskers. '
        f'{chooser.id} broke the treat in two, gave the larger half to {helper.id}, '
        f'and from then on looked at clues before boasting at them.'
    )


def closing_image(world: World, chooser: Entity, helper: Entity, method: Method) -> None:
    world.say(
        f"When another tray arrived, {chooser.id} did not salute the tallest lid "
        f"or the brightest ribbon. {chooser.pronoun().capitalize()} turned to "
        f"{helper.id} and asked, \"What shall we check first?\" Together they "
        f"used {method.label}, and the forest fair felt wiser than it had that morning."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    treat: Treat,
    shortcut: Shortcut,
    method: Method,
    chooser_name: str = "Fox",
    chooser_type: str = "fox",
    helper_name: str = "Tortoise",
    helper_type: str = "badger",
    baker_name: str = "Mole",
    baker_type: str = "mole",
    chooser_trait: str = "proud",
    helper_trait: str = "patient",
) -> World:
    world = World()

    chooser = world.add(
        Entity(
            id=chooser_name,
            kind="character",
            type=chooser_type,
            label=chooser_name,
            role="chooser",
            traits=[chooser_trait],
            attrs={},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            label=helper_name,
            role="helper",
            traits=[helper_trait],
            attrs={},
        )
    )
    baker = world.add(
        Entity(
            id=baker_name,
            kind="character",
            type=baker_type,
            label=baker_name,
            role="baker",
            traits=["observant"],
            attrs={},
        )
    )
    world.add(
        Entity(
            id="right_dish",
            type="dish",
            label=treat.label,
            attrs={
                "phrase": treat.phrase,
                "aroma": treat.aroma,
                "tag": treat.tag_symbol,
            },
        )
    )
    world.add(
        Entity(
            id="wrong_dish",
            type="dish",
            label=DECOYS[shortcut.decoy].label,
            attrs={
                "phrase": DECOYS[shortcut.decoy].phrase,
                "reaction": DECOYS[shortcut.decoy].reaction,
                "after_line": DECOYS[shortcut.decoy].after_line,
            },
        )
    )

    world.facts["predicted_sneeze"] = 0.0

    introduce(world, chooser, helper, baker)
    desire(world, chooser, treat)

    world.para()
    temptation(world, chooser, shortcut)
    warning(world, helper, chooser, shortcut)

    if chooser_resists(chooser_trait, helper_trait):
        argue(world, chooser)
        world.para()
        mistake(world, chooser, helper)
    else:
        listen(world, chooser, helper)

    world.para()
    investigate(world, helper, baker, method, treat)
    choose_right(world, chooser, treat)
    share(world, chooser, helper, treat, baker)

    world.para()
    closing_image(world, chooser, helper, method)

    world.facts.update(
        chooser=chooser,
        helper=helper,
        baker=baker,
        treat=treat,
        shortcut=shortcut,
        method=method,
        wrong=DECOYS[shortcut.decoy],
        outcome="oops" if chooser_resists(chooser_trait, helper_trait) else "averted",
        wrong_opened=world.get("wrong_dish").meters["opened"] >= THRESHOLD,
        sneezed=chooser.meters["sneeze"] >= THRESHOLD,
        learned=chooser.memes["wisdom"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
TREATS = {
    "honey_bun": Treat(
        id="honey_bun",
        label="honey bun",
        phrase="a glossy honey bun",
        aroma="warm honey and cinnamon",
        tag_symbol="a little painted bee",
        fragrant=True,
        tagged=True,
        tags={"bun", "smell", "tag"},
    ),
    "plum_tart": Treat(
        id="plum_tart",
        label="plum tart",
        phrase="a neat plum tart",
        aroma="sweet plum and butter",
        tag_symbol="a purple moon",
        fragrant=True,
        tagged=True,
        tags={"tart", "smell", "tag"},
    ),
    "acorn_cookie": Treat(
        id="acorn_cookie",
        label="acorn cookie",
        phrase="an acorn cookie with crisp edges",
        aroma="toasty nuts and brown sugar",
        tag_symbol="an oak leaf",
        fragrant=True,
        tagged=True,
        tags={"cookie", "smell", "tag"},
    ),
    "rice_cake": Treat(
        id="rice_cake",
        label="rice cake",
        phrase="a plain rice cake",
        aroma="almost nothing at all",
        tag_symbol="",
        fragrant=False,
        tagged=False,
        tags={"rice_cake"},
    ),
}

DECOYS = {
    "beet_pickles": Decoy(
        id="beet_pickles",
        label="beet pickles",
        phrase="a bowl of beet pickles",
        reaction="The vinegar smell marched up {chooser}'s nose before the first nibble even landed."
                 .replace("{chooser}", "the chooser"),
        after_line="This is not dessert. This is a lesson wearing juice",
        tags={"pickle", "sour"},
    ),
    "onion_pudding": Decoy(
        id="onion_pudding",
        label="onion pudding",
        phrase="a wobbling onion pudding",
        reaction="One brave bite made the chooser blink so hard that even the spoons looked startled.",
        after_line="I asked for sweetness and received a conversation with an onion",
        tags={"onion", "wrong_food"},
    ),
    "pepper_porridge": Decoy(
        id="pepper_porridge",
        label="pepper porridge",
        phrase="a steaming bowl of pepper porridge",
        reaction="The first puff tickled like a feather made of fire, and a sneeze burst out at once.",
        after_line="Achoo! My mouth appears to be wearing boots",
        tags={"pepper", "sneeze"},
    ),
}

SHORTCUTS = {
    "brightest_ribbon": Shortcut(
        id="brightest_ribbon",
        saying="The brightest ribbon always hides the best food.",
        cue="ribbon",
        pick_text="the dish with the brightest ribbon",
        decoy="beet_pickles",
        tags={"ribbon", "guessing"},
    ),
    "tallest_lid": Shortcut(
        id="tallest_lid",
        saying="The tallest lid must cover the grandest bite.",
        cue="height of the lid",
        pick_text="the tallest lid",
        decoy="onion_pudding",
        tags={"height", "guessing"},
    ),
    "jingle_handle": Shortcut(
        id="jingle_handle",
        saying="Anything with a jingle on the handle surely contains joy.",
        cue="jingle on the handle",
        pick_text="the lid with the jingle on its handle",
        decoy="pepper_porridge",
        tags={"jingle", "guessing"},
    ),
}

METHODS = {
    "sniff": Method(
        id="sniff",
        label="a careful sniff",
        can_smell=True,
        action_text="took one careful sniff above each lid",
        proof_text="the right dish smells like {aroma}",
        tags={"smell"},
    ),
    "read_tag": Method(
        id="read_tag",
        label="reading the little tags",
        can_read=True,
        action_text="read the tiny chalk tags tied to the handles",
        proof_text="the honest lid is marked with {tag}",
        tags={"tag"},
    ),
    "ask_baker": Method(
        id="ask_baker",
        label="asking the baker",
        can_ask=True,
        action_text="looked straight at the baker and asked politely",
        proof_text="{baker} said, 'The {treat} is under the plain round lid.'",
        tags={"ask", "adult_help"},
    ),
}

CHOOSER_TRAITS = {
    "proud": 3,
    "hasty": 2,
    "thoughtful": 1,
}

HELPER_TRAITS = {
    "patient": 3,
    "calm": 2,
    "witty": 1,
}

ANIMAL_PAIRS = [
    ("Fox", "fox", "Tortoise", "badger"),
    ("Crow", "crow", "Hare", "hare"),
    ("Vixen", "vixen", "Badger", "badger"),
    ("Bear", "bear", "Mole", "mole"),
]

BAKERS = [
    ("Mole", "mole"),
    ("Hen", "hen"),
    ("Badger", "badger"),
]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    target: str
    shortcut: str
    method: str
    chooser_name: str
    chooser_type: str
    helper_name: str
    helper_type: str
    baker_name: str
    baker_type: str
    chooser_trait: str
    helper_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
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


KNOWLEDGE = {
    "cognitive": [
        (
            "What is a cognitive shortcut?",
            "A cognitive shortcut is a quick guess your mind makes so you do not have to think for long. It can help sometimes, but it can also be wrong when the clue is only shallow."
        )
    ],
    "smell": [
        (
            "How can smelling help you find food?",
            "Many foods give off a smell, and that smell can tell you what they are before you taste them. A careful sniff is better than a wild guess."
        )
    ],
    "tag": [
        (
            "Why do tags help sort things?",
            "A tag gives clear information, like a name or symbol, so you do not have to guess from looks alone. Reading the tag can stop a mistake before it starts."
        )
    ],
    "ask": [
        (
            "Why is it smart to ask someone who knows?",
            "Someone who made or arranged the food often knows the answer already. Asking can save time and keep you from choosing the wrong thing."
        )
    ],
    "adult_help": [
        (
            "When should you ask a grown-up for help?",
            "You should ask a grown-up when they know more about the problem or can help you check safely. Good questions are a wise tool."
        )
    ],
    "guessing": [
        (
            "Why can guessing by looks alone be risky?",
            "Things that look bright, tall, or fancy are not always the thing you want. Looking only at the outside can fool you."
        )
    ],
}
KNOWLEDGE_ORDER = ["cognitive", "guessing", "smell", "tag", "ask", "adult_help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    chooser = f["chooser"]
    helper = f["helper"]
    treat = f["treat"]
    shortcut = f["shortcut"]
    method = f["method"]
    if f["outcome"] == "oops":
        return [
            f'Write a short fable with humor and dialogue that includes the words "cognitive" and "wrong". A hungry {chooser.type} should trust a silly rule about {shortcut.cue}, choose badly, and then be corrected.',
            f"Tell a funny animal story where {chooser.id} wants {treat.label}, ignores {helper.id}'s warning, and learns to check before guessing.",
            f"Write a fable-like story in which a boastful animal uses {method.label} only after making a comic mistake."
        ]
    return [
        f'Write a short fable with humor and dialogue that includes the words "cognitive" and "wrong". A hungry {chooser.type} should start with a silly rule, then listen to a wiser friend in time.',
        f"Tell a gentle animal story where {chooser.id} wants {treat.label}, hears that the quick guess may be wrong, and chooses evidence instead.",
        f"Write a light fable in which {helper.id} helps a friend check first and avoid an embarrassing mistake."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    chooser = f["chooser"]
    helper = f["helper"]
    baker = f["baker"]
    treat = f["treat"]
    shortcut = f["shortcut"]
    method = f["method"]
    wrong = f["wrong"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {chooser.id} the {chooser.type} and {helper.id} the {helper.type} at a forest fair snack table. {baker.id} the {baker.type} is there too, because the baker arranged the dishes."
        ),
        (
            f"What did {chooser.id} want?",
            f"{chooser.id} wanted {treat.phrase}. That hunger is why the silly shortcut felt tempting in the first place."
        ),
        (
            f"What was {chooser.id}'s wrong idea?",
            f"{chooser.id} believed, '{shortcut.saying}' That was a cognitive shortcut based on {shortcut.cue}, not on real evidence about the food."
        ),
        (
            f"How did {helper.id} try to help?",
            f"{helper.id} warned that the quick guess might be wrong and said the clue only described the lid. Then {helper.pronoun().capitalize()} used {method.label} to check what was really under the covers."
        ),
    ]

    if f["wrong_opened"]:
        qa.append(
            (
                f"What happened when {chooser.id} trusted the shortcut?",
                f"{chooser.id} opened the wrong dish and found {wrong.phrase} instead of {treat.label}. The surprise was funny, but it also proved that showy clues can mislead a hungry mind."
            )
        )
        if f["sneezed"]:
            qa.append(
                (
                    f"Why did {chooser.id} sneeze?",
                    f"{chooser.id} sneezed because the wrong dish was a peppery, sharp surprise. The sneeze came right after the bad guess, so it turned the mistake into a comic lesson."
                )
            )
    else:
        qa.append(
            (
                f"Did {chooser.id} make the bad guess in the end?",
                f"No. {chooser.id} paused and listened before opening the wrong dish. That small moment of humility kept the mistake from happening."
            )
        )

    qa.append(
        (
            f"How did they finally find the right treat?",
            f"They used {method.label}, and that gave them a real clue about the hidden food. After checking instead of guessing, they found {treat.phrase} under the correct lid."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the friends sharing the treat and checking clues together on the next tray. The final image shows that {chooser.id} changed from boasting first to asking what to check first."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"cognitive"} | set(f["shortcut"].tags) | set(f["method"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits: list[str] = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        target="honey_bun",
        shortcut="jingle_handle",
        method="sniff",
        chooser_name="Fox",
        chooser_type="fox",
        helper_name="Tortoise",
        helper_type="badger",
        baker_name="Mole",
        baker_type="mole",
        chooser_trait="proud",
        helper_trait="calm",
    ),
    StoryParams(
        target="plum_tart",
        shortcut="tallest_lid",
        method="read_tag",
        chooser_name="Crow",
        chooser_type="crow",
        helper_name="Hare",
        helper_type="hare",
        baker_name="Hen",
        baker_type="hen",
        chooser_trait="thoughtful",
        helper_trait="patient",
    ),
    StoryParams(
        target="acorn_cookie",
        shortcut="brightest_ribbon",
        method="ask_baker",
        chooser_name="Bear",
        chooser_type="bear",
        helper_name="Mole",
        helper_type="mole",
        baker_name="Badger",
        baker_type="badger",
        chooser_trait="hasty",
        helper_trait="patient",
    ),
    StoryParams(
        target="rice_cake",
        shortcut="jingle_handle",
        method="ask_baker",
        chooser_name="Vixen",
        chooser_type="vixen",
        helper_name="Badger",
        helper_type="badger",
        baker_name="Mole",
        baker_type="mole",
        chooser_trait="thoughtful",
        helper_trait="calm",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% valid stories: a shortcut must actually be wrong, and the checking method
% must genuinely reveal the target treat.
reveals(M, T) :- method(M), treat(T), can_ask(M).
reveals(M, T) :- method(M), treat(T), can_read(M), tagged(T).
reveals(M, T) :- method(M), treat(T), can_smell(M), fragrant(T).

valid(T, S, M) :- treat(T), shortcut(S), wrong_target(S, D), D != T, reveals(M, T).

% outcome model: the chooser resists if stubbornness is at least the helper's
% steadiness. Then the wrong dish gets opened before the correction.
resists :- chooser_trait(C), helper_trait(H), stubborn(C, SV), steady(H, HV), SV >= HV.
outcome(oops) :- resists.
outcome(averted) :- not resists.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for treat_id, treat in TREATS.items():
        lines.append(asp.fact("treat", treat_id))
        if treat.fragrant:
            lines.append(asp.fact("fragrant", treat_id))
        if treat.tagged:
            lines.append(asp.fact("tagged", treat_id))
    for shortcut_id, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", shortcut_id))
        lines.append(asp.fact("wrong_target", shortcut_id, shortcut.decoy))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        if method.can_smell:
            lines.append(asp.fact("can_smell", method_id))
        if method.can_read:
            lines.append(asp.fact("can_read", method_id))
        if method.can_ask:
            lines.append(asp.fact("can_ask", method_id))
    for trait, val in CHOOSER_TRAITS.items():
        lines.append(asp.fact("stubborn", trait, val))
    for trait, val in HELPER_TRAITS.items():
        lines.append(asp.fact("steady", trait, val))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chooser_trait", params.chooser_trait),
            asp.fact("helper_trait", params.helper_trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="### smoke")
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a silly shortcut, a wrong guess, and a wiser check."
    )
    ap.add_argument("--target", choices=TREATS)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target is not None and args.target not in TREATS:
        raise StoryError(f"(No story: unknown target '{args.target}'.)")
    if args.shortcut is not None and args.shortcut not in SHORTCUTS:
        raise StoryError(f"(No story: unknown shortcut '{args.shortcut}'.)")
    if args.method is not None and args.method not in METHODS:
        raise StoryError(f"(No story: unknown method '{args.method}'.)")

    if args.target and args.shortcut and args.method:
        treat = TREATS[args.target]
        shortcut = SHORTCUTS[args.shortcut]
        method = METHODS[args.method]
        if shortcut.decoy == treat.id or not method_reveals(method, treat):
            raise StoryError(explain_combo_rejection(treat, shortcut, method))
    elif args.target and args.method:
        treat = TREATS[args.target]
        method = METHODS[args.method]
        if not method_reveals(method, treat):
            raise StoryError(explain_method_rejection(method, treat))

    combos = [
        combo
        for combo in valid_combos()
        if (args.target is None or combo[0] == args.target)
        and (args.shortcut is None or combo[1] == args.shortcut)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    target_id, shortcut_id, method_id = rng.choice(sorted(combos))
    chooser_name, chooser_type, helper_name, helper_type = rng.choice(ANIMAL_PAIRS)
    baker_name, baker_type = rng.choice(BAKERS)
    chooser_trait = rng.choice(sorted(CHOOSER_TRAITS))
    helper_trait = rng.choice(sorted(HELPER_TRAITS))

    return StoryParams(
        target=target_id,
        shortcut=shortcut_id,
        method=method_id,
        chooser_name=chooser_name,
        chooser_type=chooser_type,
        helper_name=helper_name,
        helper_type=helper_type,
        baker_name=baker_name,
        baker_type=baker_type,
        chooser_trait=chooser_trait,
        helper_trait=helper_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.target not in TREATS:
        raise StoryError(f"(No story: unknown target '{params.target}'.)")
    if params.shortcut not in SHORTCUTS:
        raise StoryError(f"(No story: unknown shortcut '{params.shortcut}'.)")
    if params.method not in METHODS:
        raise StoryError(f"(No story: unknown method '{params.method}'.)")
    if params.chooser_trait not in CHOOSER_TRAITS:
        raise StoryError(f"(No story: unknown chooser trait '{params.chooser_trait}'.)")
    if params.helper_trait not in HELPER_TRAITS:
        raise StoryError(f"(No story: unknown helper trait '{params.helper_trait}'.)")

    treat = TREATS[params.target]
    shortcut = SHORTCUTS[params.shortcut]
    method = METHODS[params.method]
    if shortcut.decoy == treat.id or not method_reveals(method, treat):
        raise StoryError(explain_combo_rejection(treat, shortcut, method))

    world = tell(
        treat=treat,
        shortcut=shortcut,
        method=method,
        chooser_name=params.chooser_name,
        chooser_type=params.chooser_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        baker_name=params.baker_name,
        baker_type=params.baker_type,
        chooser_trait=params.chooser_trait,
        helper_trait=params.helper_trait,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (target, shortcut, method) combos:\n")
        for target, shortcut, method in combos:
            print(f"  {target:13} {shortcut:17} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.chooser_name}: {p.target} via {p.shortcut} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
