#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/walrus_foreshadowing_repetition_curiosity_comedy.py
===============================================================================

A standalone story world about a curious child, a string of funny clues, and a
wandering walrus that should not be where it is.

The domain is built for a gentle comedy shape with three strong instruments:

- Foreshadowing: early clues point toward the walrus before anyone sees it.
- Repetition: a recurring sound/question keeps pulling the story forward.
- Curiosity: the child follows clue after clue until the funny reveal.

Run it
------
    python storyworlds/worlds/gpt-5.4/walrus_foreshadowing_repetition_curiosity_comedy.py
    python storyworlds/worlds/gpt-5.4/walrus_foreshadowing_repetition_curiosity_comedy.py --setting harbor --hideout fish_crate
    python storyworlds/worlds/gpt-5.4/walrus_foreshadowing_repetition_curiosity_comedy.py --setting bakery
    python storyworlds/worlds/gpt-5.4/walrus_foreshadowing_repetition_curiosity_comedy.py --all
    python storyworlds/worlds/gpt-5.4/walrus_foreshadowing_repetition_curiosity_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/walrus_foreshadowing_repetition_curiosity_comedy.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/ to
# sys.path by walking up two package levels.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "keeper", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "keeper": "keeper",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    helper_type: str
    helper_label: str
    watery: bool = True
    faucets: bool = False
    bells: bool = False
    fishy: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Hideout:
    id: str
    label: str
    phrase: str
    clue1: str
    clue2: str
    clue3: str
    reveal: str
    splashy: bool = False
    roomy: bool = True
    chilly: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Lure:
    id: str
    label: str
    setup: str
    action: str
    success: str
    sense: int = 2
    needs_fish: bool = False
    needs_bell: bool = False
    needs_faucet: bool = False
    tags: set[str] = field(default_factory=set)


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


def _r_big_body_makes_bumps(world: World) -> list[str]:
    walrus = world.get("walrus")
    if walrus.meters["hidden"] < THRESHOLD:
        return []
    if walrus.meters["shuffle"] < THRESHOLD:
        return []
    sig = ("bumps",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("room").meters["mystery"] += 1
    world.get("child").memes["curiosity"] += 1
    return ["__mystery__"]


def _r_curiosity_follows_clues(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["curiosity"] < 2:
        return []
    sig = ("follows",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["bravery"] += 1
    return ["__follow__"]


def _r_reveal_brings_relief(world: World) -> list[str]:
    walrus = world.get("walrus")
    if walrus.meters["seen"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("child").memes["surprise"] += 1
    world.get("child").memes["relief"] += 1
    world.get("helper").memes["calm"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="big_body_makes_bumps", tag="physical", apply=_r_big_body_makes_bumps),
    Rule(name="curiosity_follows_clues", tag="emotion", apply=_r_curiosity_follows_clues),
    Rule(name="reveal_brings_relief", tag="emotion", apply=_r_reveal_brings_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "harbor": Setting(
        id="harbor",
        place="the little harbor",
        detail="Boats rocked against the dock, and gulls shouted at anything that looked even a little bit like lunch.",
        helper_type="aunt",
        helper_label="Aunt June",
        watery=True,
        faucets=True,
        bells=False,
        fishy=True,
        tags={"harbor", "water", "fish"},
    ),
    "aquarium": Setting(
        id="aquarium",
        place="the aquarium back hall",
        detail="The floor smelled faintly of salt, and bright tanks made wiggly blue light on the walls.",
        helper_type="keeper",
        helper_label="Keeper Ana",
        watery=True,
        faucets=True,
        bells=True,
        fishy=True,
        tags={"aquarium", "water", "keeper"},
    ),
    "fish_market": Setting(
        id="fish_market",
        place="the fish market",
        detail="Crushed ice sparkled in wooden boxes, and every table smelled like the sea had packed a picnic.",
        helper_type="father",
        helper_label="Dad",
        watery=False,
        faucets=False,
        bells=True,
        fishy=True,
        tags={"market", "fish"},
    ),
    "bakery": Setting(
        id="bakery",
        place="the bakery storeroom",
        detail="Flour dust floated in the warm air, and buns sat in neat rows like sleepy pillows.",
        helper_type="mother",
        helper_label="Mom",
        watery=False,
        faucets=False,
        bells=False,
        fishy=False,
        tags={"bakery", "bread"},
    ),
}

HIDEOUTS = {
    "fish_crate": Hideout(
        id="fish_crate",
        label="fish crate",
        phrase="a stack of fish crates with a striped tarp over them",
        clue1="a wet whisker lay on the floor like a silver question mark",
        clue2="something inside the crate said, very softly, 'plop... plop... plop'",
        clue3="the tarp puffed up and settled down again, as if it had just sighed",
        reveal="the tarp rose, and out popped a walrus face with whiskers as wide as little paintbrushes",
        splashy=False,
        roomy=True,
        chilly=False,
        tags={"crate", "fish"},
    ),
    "ice_bin": Hideout(
        id="ice_bin",
        label="ice bin",
        phrase="a giant ice bin with its lid wobbling up and down",
        clue1="three cubes of ice slid across the floor all by themselves",
        clue2="from under the lid came the same sound again: 'plop... plop... plop'",
        clue3="the lid gave a polite bounce, as if something underneath had hiccupped",
        reveal="the lid tipped back, and a walrus blinked up through the frost with a fishy grin",
        splashy=True,
        roomy=True,
        chilly=True,
        tags={"ice", "cold"},
    ),
    "lifeboat": Hideout(
        id="lifeboat",
        label="lifeboat",
        phrase="a red lifeboat pulled halfway onto the floor",
        clue1="a line of wet flipper prints curved around the corner",
        clue2="the boat thumped once, then twice: 'plop... plop... plop'",
        clue3="one rope twitched the way a sleeping tail might twitch in a dream",
        reveal="the boat rocked, and a walrus sat up inside it as if it had booked the boat for a nap",
        splashy=False,
        roomy=True,
        chilly=False,
        tags={"boat", "dock"},
    ),
}

LURES = {
    "fish_bucket": Lure(
        id="fish_bucket",
        label="fish bucket",
        setup="picked up a small bucket of fish from a nearby table",
        action="held the bucket a little way off and gave it a gentle swish",
        success="The walrus followed the fishy smell with such eager dignity that everyone had to hide a laugh.",
        sense=3,
        needs_fish=True,
        needs_bell=False,
        needs_faucet=False,
        tags={"fish_bucket", "fish"},
    ),
    "bell": Lure(
        id="bell",
        label="bell",
        setup="lifted a brass hand bell",
        action="rang it in a bright ding-ding rhythm and stepped toward the open door",
        success="The walrus bobbed after the sound like a very large gentleman late for tea.",
        sense=2,
        needs_fish=False,
        needs_bell=True,
        needs_faucet=False,
        tags={"bell"},
    ),
    "hose_spray": Lure(
        id="hose_spray",
        label="hose spray",
        setup="turned on a hose until a cool ribbon of water danced across the floor",
        action="made a sparkling trail of water toward the outside ramp",
        success="The walrus slid after the shining trail with a happy snort, as if the floor had suddenly remembered it was part pond.",
        sense=2,
        needs_fish=False,
        needs_bell=False,
        needs_faucet=True,
        tags={"hose", "water"},
    ),
    "bun_basket": Lure(
        id="bun_basket",
        label="bun basket",
        setup="lifted a basket of warm buns",
        action="waved the basket hopefully toward the door",
        success="The buns smelled lovely, but the walrus only blinked and looked offended.",
        sense=1,
        needs_fish=False,
        needs_bell=False,
        needs_faucet=False,
        tags={"bread"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Sam", "Leo", "Finn", "Max", "Theo"]
TRAITS = ["curious", "bouncy", "careful", "bright", "nosy", "cheerful"]


def hideout_fits(setting: Setting, hideout: Hideout) -> bool:
    if setting.id == "bakery":
        return False
    if hideout.id == "ice_bin" and not (setting.watery or setting.id == "fish_market"):
        return False
    if hideout.id == "lifeboat" and setting.id not in {"harbor", "aquarium"}:
        return False
    if hideout.id == "fish_crate" and not setting.fishy:
        return False
    return hideout.roomy


def lure_works(setting: Setting, lure: Lure) -> bool:
    if lure.sense < SENSE_MIN:
        return False
    if lure.needs_fish and not setting.fishy:
        return False
    if lure.needs_bell and not setting.bells:
        return False
    if lure.needs_faucet and not setting.faucets:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for hideout_id, hideout in HIDEOUTS.items():
            if not hideout_fits(setting, hideout):
                continue
            for lure_id, lure in LURES.items():
                if lure_works(setting, lure):
                    out.append((setting_id, hideout_id, lure_id))
    return out


@dataclass
class StoryParams:
    setting: str
    hideout: str
    lure: str
    child_name: str
    child_gender: str
    trait: str
    repetition_count: int = 3
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="harbor",
        hideout="fish_crate",
        lure="fish_bucket",
        child_name="Mia",
        child_gender="girl",
        trait="curious",
        repetition_count=3,
    ),
    StoryParams(
        setting="aquarium",
        hideout="ice_bin",
        lure="bell",
        child_name="Ben",
        child_gender="boy",
        trait="bright",
        repetition_count=3,
    ),
    StoryParams(
        setting="harbor",
        hideout="lifeboat",
        lure="hose_spray",
        child_name="Nora",
        child_gender="girl",
        trait="careful",
        repetition_count=3,
    ),
    StoryParams(
        setting="fish_market",
        hideout="fish_crate",
        lure="fish_bucket",
        child_name="Theo",
        child_gender="boy",
        trait="cheerful",
        repetition_count=4,
    ),
]


def explain_rejection(setting: Setting, hideout: Hideout) -> str:
    if setting.id == "bakery":
        return (
            "(No story: a wandering walrus needs a chilly, watery, or fishy place "
            "to plausibly turn up. A warm bakery storeroom is too far from the "
            "walrus's world for this little comedy.)"
        )
    if hideout.id == "lifeboat" and setting.id == "fish_market":
        return (
            "(No story: a lifeboat makes sense by a dock or aquarium service bay, "
            "not in the middle of a fish market.)"
        )
    if hideout.id == "ice_bin" and not (setting.watery or setting.id == "fish_market"):
        return (
            "(No story: an ice bin hideout only makes sense in a cold, sea-smelling "
            "place with big bins of ice.)"
        )
    if hideout.id == "fish_crate" and not setting.fishy:
        return (
            "(No story: a fish crate hideout needs a place where fish crates actually belong.)"
        )
    return "(No story: that setting and hideout do not make a reasonable walrus comedy.)"


def explain_lure(setting: Setting, lure: Lure) -> str:
    if lure.sense < SENSE_MIN:
        return (
            f"(Refusing lure '{lure.id}': it scores too low on common sense "
            f"(sense={lure.sense} < {SENSE_MIN}). The walrus needs a sensible way "
            "to be guided out, not a random snack that it would ignore.)"
        )
    if lure.needs_fish and not setting.fishy:
        return "(No story: this lure needs fish nearby, and that setting does not have them.)"
    if lure.needs_bell and not setting.bells:
        return "(No story: this lure needs a bell or keeper cue available in the setting.)"
    if lure.needs_faucet and not setting.faucets:
        return "(No story: this lure needs running water, and that setting has no hose or faucet.)"
    return "(No story: that lure does not fit the setting.)"


ASP_RULES = r"""
% reasonableness gate
bad_setting(bakery).

fit_hideout(S, H) :- setting(S), hideout(H), roomy(H), not impossible_hideout(S, H).
impossible_hideout(bakery, H) :- hideout(H).
impossible_hideout(S, lifeboat) :- setting(S), S != harbor, S != aquarium.
impossible_hideout(S, fish_crate) :- setting(S), not fishy(S).
impossible_hideout(S, ice_bin) :- setting(S), S != fish_market, not watery(S).

usable_lure(S, L) :- lure(L), sense(L, V), sense_min(M), V >= M,
                     not needs_fish(L), not needs_bell(L), not needs_faucet(L), setting(S).
usable_lure(S, L) :- lure(L), sense(L, V), sense_min(M), V >= M,
                     needs_fish(L), fishy(S),
                     not needs_bell(L), not needs_faucet(L), setting(S).
usable_lure(S, L) :- lure(L), sense(L, V), sense_min(M), V >= M,
                     needs_bell(L), bells(S),
                     not needs_fish(L), not needs_faucet(L), setting(S).
usable_lure(S, L) :- lure(L), sense(L, V), sense_min(M), V >= M,
                     needs_faucet(L), faucets(S),
                     not needs_fish(L), not needs_bell(L), setting(S).

valid(S, H, L) :- fit_hideout(S, H), usable_lure(S, L).

% simple outcome model: all valid stories reveal and guide the walrus out.
outcome(revealed) :- chosen_setting(S), chosen_hideout(H), chosen_lure(L), valid(S, H, L).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.watery:
            lines.append(asp.fact("watery", sid))
        if s.faucets:
            lines.append(asp.fact("faucets", sid))
        if s.bells:
            lines.append(asp.fact("bells", sid))
        if s.fishy:
            lines.append(asp.fact("fishy", sid))
    for hid, h in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        if h.roomy:
            lines.append(asp.fact("roomy", hid))
    for lid, l in LURES.items():
        lines.append(asp.fact("lure", lid))
        lines.append(asp.fact("sense", lid, l.sense))
        if l.needs_fish:
            lines.append(asp.fact("needs_fish", lid))
        if l.needs_bell:
            lines.append(asp.fact("needs_bell", lid))
        if l.needs_faucet:
            lines.append(asp.fact("needs_faucet", lid))
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
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_hideout", params.hideout),
            asp.fact("chosen_lure", params.lure),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def predict_reveal(world: World) -> dict:
    sim = world.copy()
    sim.get("walrus").meters["shuffle"] += 1
    propagate(sim, narrate=False)
    return {
        "mystery": sim.get("room").meters["mystery"],
        "curiosity": sim.get("child").memes["curiosity"],
    }


def opening(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    world.say(
        f"One bright day, {child.id} visited {setting.place} with {helper.label}. "
        f"{setting.detail}"
    )
    world.say(
        f"{child.id} had come ready to notice everything, because {child.pronoun()} was a very {child.attrs.get('trait', 'curious')} child."
    )


def plant_first_clue(world: World, child: Entity, hideout: Hideout) -> None:
    walrus = world.get("walrus")
    walrus.meters["hidden"] += 1
    walrus.meters["shuffle"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before {child.id} saw anything strange, {child.pronoun()} saw something small: {hideout.clue1}."
    )
    world.say(
        f'{child.id} blinked. "That is the sort of clue that belongs to a very odd somebody," {child.pronoun()} said.'
    )


def repeat_sound(world: World, child: Entity, hideout: Hideout, count: int) -> None:
    pieces = [hideout.clue2]
    if count >= 3:
        pieces.append(f"Then it came again from {hideout.phrase}: 'plop... plop... plop'.")
    if count >= 4:
        pieces.append("And then, just to be extra sure it had everyone's attention, it said it one more time: 'plop... plop... plop'.")
    for line in pieces:
        world.say(line)
        child.memes["curiosity"] += 1
    world.say(f'"What makes that plop-plop-plop?" {child.id} asked.')
    world.say(f'"What makes that plop-plop-plop?" {child.id} asked again, because once was not enough for such a question.')


def second_clue(world: World, child: Entity, hideout: Hideout) -> None:
    pred = predict_reveal(world)
    world.facts["predicted_mystery"] = pred["mystery"]
    world.facts["predicted_curiosity"] = pred["curiosity"]
    world.say(hideout.clue3 + ".")
    if pred["curiosity"] >= 2:
        world.say(
            f"{child.id} took one careful step closer. Curiosity tugged {child.pronoun('object')} forward harder than caution tugged {child.pronoun('object')} back."
        )


def funny_guesses(world: World, child: Entity, helper: Entity, setting: Setting, hideout: Hideout) -> None:
    guesses = [
        "a sleepy drum",
        "a polite sea monster",
        "a pile of coats learning to breathe",
    ]
    guess = guesses[(len(setting.id) + len(hideout.id)) % len(guesses)]
    child.memes["curiosity"] += 1
    world.say(
        f'"Is it {guess}?" {child.id} whispered.'
    )
    world.say(
        f'{helper.label} smiled without answering. "{child.id}, I think your question is smarter than your guess," {helper.pronoun()} said.'
    )


def reveal_walrus(world: World, child: Entity, helper: Entity, hideout: Hideout) -> None:
    walrus = world.get("walrus")
    walrus.meters["seen"] += 1
    walrus.meters["hidden"] = 0.0
    walrus.memes["hungry"] += 1
    propagate(world, narrate=False)
    world.say(hideout.reveal + ".")
    world.say(
        f'It was a walrus, enormous and whiskery and much too pleased with itself.'
    )
    world.say(
        f'{child.id} gasped, then laughed. "I knew it was somebody odd," {child.pronoun()} said.'
    )


def calm_plan(world: World, child: Entity, helper: Entity, lure: Lure) -> None:
    helper.memes["plan"] += 1
    world.say(
        f"{helper.label} did not shout or flap about. {helper.pronoun().capitalize()} simply {lure.setup}."
    )
    world.say(
        f'"Let us be calm," {helper.pronoun()} said. "A walrus is big, but a good plan can be bigger."'
    )
    world.say(
        f"{helper.pronoun().capitalize()} {lure.action}."
    )


def guide_out(world: World, child: Entity, helper: Entity, setting: Setting, lure: Lure) -> None:
    walrus = world.get("walrus")
    walrus.meters["guided_out"] += 1
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    world.say(lure.success)
    world.say(
        f"Step by step, the walrus followed {helper.label} out of {setting.place} and back toward the proper sea-smelling side of the day."
    )
    world.say(
        f"As it went, it gave one last happy snort, almost as if it were saying goodbye in walrus language."
    )


def ending_image(world: World, child: Entity, setting: Setting) -> None:
    world.say(
        f'After that, whenever {child.id} heard a funny little "plop... plop... plop" at {setting.place}, {child.pronoun()} grinned before turning the corner.'
    )
    world.say(
        f"{child.pronoun().capitalize()} still felt curious, but now the curiosity came with a laugh and a story to tell."
    )


def tell(
    setting: Setting,
    hideout: Hideout,
    lure: Lure,
    *,
    child_name: str,
    child_gender: str,
    trait: str,
    repetition_count: int,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=child_gender,
            label=child_name,
            phrase=child_name,
            role="child",
            attrs={"trait": trait},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=setting.helper_type,
            label=setting.helper_label,
            phrase=setting.helper_label,
            role="helper",
        )
    )
    walrus = world.add(
        Entity(
            id="walrus",
            kind="character",
            type="walrus",
            label="the walrus",
            phrase="a wandering walrus",
            role="walrus",
            tags={"walrus"},
        )
    )
    room = world.add(
        Entity(
            id="room",
            type="place",
            label=setting.place,
        )
    )

    child.id = child_name

    opening(world, child, helper, setting)
    world.para()
    plant_first_clue(world, child, hideout)
    repeat_sound(world, child, hideout, repetition_count)
    second_clue(world, child, hideout)
    funny_guesses(world, child, helper, setting, hideout)
    world.para()
    reveal_walrus(world, child, helper, hideout)
    calm_plan(world, child, helper, lure)
    guide_out(world, child, helper, setting, lure)
    world.para()
    ending_image(world, child, setting)

    world.facts.update(
        child=child,
        helper=helper,
        walrus=walrus,
        room=room,
        setting=setting,
        hideout=hideout,
        lure=lure,
        revealed=walrus.meters["seen"] >= THRESHOLD,
        guided_out=walrus.meters["guided_out"] >= THRESHOLD,
        repetition_count=repetition_count,
    )
    return world


KNOWLEDGE = {
    "walrus": [
        (
            "What is a walrus?",
            "A walrus is a very large sea animal with whiskers and long tusks. It lives in cold water and likes to rest on ice or along the shore.",
        )
    ],
    "harbor": [
        (
            "What is a harbor?",
            "A harbor is a safe place by the water where boats can stop. People tie boats there so they do not drift away.",
        )
    ],
    "aquarium": [
        (
            "What is an aquarium?",
            "An aquarium is a place where people care for water animals and let visitors learn about them. It often has tanks, pumps, and keepers.",
        )
    ],
    "market": [
        (
            "What is a fish market?",
            "A fish market is a place where fish are sold. It often smells like the sea because fish are kept cold on ice.",
        )
    ],
    "ice": [
        (
            "Why would a walrus like ice?",
            "Ice is cold, and walruses are animals from chilly places. A cold spot can feel more comfortable to them than a warm room.",
        )
    ],
    "fish_bucket": [
        (
            "Why would fish attract a walrus?",
            "Fish smell like food to a walrus. A strong fishy smell can make it follow along to see where the snack is going.",
        )
    ],
    "bell": [
        (
            "Why might an animal follow a bell?",
            "If an animal has learned that a bell means feeding time or a routine, the sound can catch its attention. It may follow the sound because it expects something familiar.",
        )
    ],
    "hose": [
        (
            "Why might a walrus like a trail of water?",
            "Walruses are water animals, so a cool wet path can feel inviting. The shining water also gives them an easy trail to follow.",
        )
    ],
}

KNOWLEDGE_ORDER = ["walrus", "harbor", "aquarium", "market", "ice", "fish_bucket", "bell", "hose"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    hideout = f["hideout"]
    return [
        'Write a funny story for a 3-to-5-year-old that includes the word "walrus" and uses foreshadowing, repetition, and curiosity.',
        f"Tell a gentle comedy where {child.label} keeps hearing 'plop... plop... plop' in {setting.place} and follows the clues until a walrus pops out of {hideout.phrase}.",
        f"Write a short story with a repeated question, a string of clues, and a silly reveal: the hidden mystery turns out to be a walrus in {setting.place}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    setting = f["setting"]
    hideout = f["hideout"]
    lure = f["lure"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, {helper.label}, and a wandering walrus. The story follows {child.label}'s curiosity as the strange clues pile up.",
        ),
        (
            "What was the first clue that something odd was nearby?",
            f"The first clue was that {hideout.clue1}. That small clue quietly hinted that a big, unusual visitor was hiding close by.",
        ),
        (
            'What kept being repeated in the story?',
            f'The repeated sound was "plop... plop... plop," and {child.label} kept asking what made it. The repetition made the mystery feel funnier each time it came back.',
        ),
        (
            f"Why did {child.label} keep going closer instead of walking away?",
            f"{child.label} was too curious to leave the mystery alone. Each new clue made the hidden creature feel more real, so curiosity pulled {child.pronoun('object')} forward.",
        ),
    ]
    if f["revealed"]:
        qa.append(
            (
                "What was hiding there all along?",
                f"A walrus was hiding in {hideout.phrase}. The early clues had been foreshadowing the reveal before anyone actually saw it.",
            )
        )
    if f["guided_out"]:
        qa.append(
            (
                f"How did {helper.label} help solve the problem?",
                f"{helper.label} stayed calm and used {lure.label} to guide the walrus out. The plan worked because it gave the walrus something sensible to follow instead of causing a fuss.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the walrus being guided safely back out of {setting.place}. The last image shows {child.label} still feeling curious, but now laughing whenever that sound comes back.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    setting = f["setting"]
    hideout = f["hideout"]
    lure = f["lure"]
    tags = {"walrus"} | set(setting.tags) | set(hideout.tags) | set(lure.tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a curious child follows funny clues to a wandering walrus."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against the Python gate")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.hideout:
        setting = SETTINGS[args.setting]
        hideout = HIDEOUTS[args.hideout]
        if not hideout_fits(setting, hideout):
            raise StoryError(explain_rejection(setting, hideout))
    if args.setting and args.lure:
        setting = SETTINGS[args.setting]
        lure = LURES[args.lure]
        if not lure_works(setting, lure):
            raise StoryError(explain_lure(setting, lure))
    if args.lure and LURES[args.lure].sense < SENSE_MIN:
        setting = SETTINGS[args.setting] if args.setting else next(iter(SETTINGS.values()))
        raise StoryError(explain_lure(setting, LURES[args.lure]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.hideout is None or combo[1] == args.hideout)
        and (args.lure is None or combo[2] == args.lure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, hideout_id, lure_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    trait = rng.choice(TRAITS)
    repetition_count = rng.choice([3, 4])
    return StoryParams(
        setting=setting_id,
        hideout=hideout_id,
        lure=lure_id,
        child_name=name,
        child_gender=gender,
        trait=trait,
        repetition_count=repetition_count,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(No story: unknown hideout '{params.hideout}'.)")
    if params.lure not in LURES:
        raise StoryError(f"(No story: unknown lure '{params.lure}'.)")
    setting = SETTINGS[params.setting]
    hideout = HIDEOUTS[params.hideout]
    lure = LURES[params.lure]
    if not hideout_fits(setting, hideout):
        raise StoryError(explain_rejection(setting, hideout))
    if not lure_works(setting, lure):
        raise StoryError(explain_lure(setting, lure))

    world = tell(
        setting=setting,
        hideout=hideout,
        lure=lure,
        child_name=params.child_name,
        child_gender=params.child_gender,
        trait=params.trait,
        repetition_count=params.repetition_count,
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        cases.append(default_params)
    except StoryError as err:
        rc = 1
        print("Default resolve_params failed:", err)

    for params in cases:
        asp_out = asp_outcome(params)
        py_out = "revealed"
        if asp_out != py_out:
            rc = 1
            print(f"MISMATCH outcome for {params}: asp={asp_out} python={py_out}")

    try:
        sample = generate(cases[0])
        if not sample.story or "walrus" not in sample.story.lower():
            raise StoryError("(Verify smoke test failed: story missing walrus or text.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generated and emitted.")
    except Exception as err:
        rc = 1
        print(f"Smoke test failed: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, hideout, lure) combos:\n")
        for setting, hideout, lure in combos:
            print(f"  {setting:12} {hideout:10} {lure}")
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
            header = f"### {p.child_name}: {p.setting}, {p.hideout}, {p.lure}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
