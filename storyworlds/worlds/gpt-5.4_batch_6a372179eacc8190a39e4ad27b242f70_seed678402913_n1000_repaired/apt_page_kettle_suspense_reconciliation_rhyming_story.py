#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/apt_page_kettle_suspense_reconciliation_rhyming_story.py
====================================================================================

A standalone storyworld for a small rhyming tale set in an apartment: a child
makes something on a page, a kettle begins to hiss, the page goes missing in a
suspenseful moment, and a misunderstanding is healed through reconciliation.

The world model is classical and state-driven:
- a warm kettle can make nearby paper damp and curl with steam
- a window draft can move a loose page across the room
- a worried child may wrongly blame a friend or sibling
- a safe helper action can recover the page without touching the hot kettle
- the ending proves the change: the page is saved or remade, and the children
  make peace

Run it
------
    python storyworlds/worlds/gpt-5.4/apt_page_kettle_suspense_reconciliation_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/apt_page_kettle_suspense_reconciliation_rhyming_story.py --page poem --helper tongs
    python storyworlds/worlds/gpt-5.4/apt_page_kettle_suspense_reconciliation_rhyming_story.py --page chalkboard
    python storyworlds/worlds/gpt-5.4/apt_page_kettle_suspense_reconciliation_rhyming_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/apt_page_kettle_suspense_reconciliation_rhyming_story.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so we need to add the
# package dir storyworlds/ to sys.path.
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
    traits: tuple = field(default_factory=tuple)
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
    owner: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    hot: bool = False
    movable: bool = True
    paper_like: bool = False
    can_reach_hot: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Apartment:
    id: str
    label: str
    nook: str
    window_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PageKind:
    id: str
    label: str
    make_line: str
    final_line: str
    paper_like: bool = True
    steam_risk: bool = True
    remakeable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class KettleKind:
    id: str
    label: str
    sound: str
    steam_line: str
    hot: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class DraftKind:
    id: str
    label: str
    move_line: str
    strength: int
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperAction:
    id: str
    label: str
    sense: int
    safe_near_hot: bool
    success_line: str
    fail_line: str
    qa_line: str
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


def _r_steam_wrinkle(world: World) -> list[str]:
    out: list[str] = []
    page = world.entities.get("page")
    kettle = world.entities.get("kettle")
    if not page or not kettle:
        return out
    if page.attrs.get("place") != "near_kettle":
        return out
    if kettle.meters["steaming"] < THRESHOLD:
        return out
    if not page.paper_like:
        return out
    sig = ("steam_wrinkle", page.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    page.meters["damp"] += 1
    page.meters["curled"] += 1
    owner = world.entities.get(page.owner)
    if owner is not None:
        owner.memes["worry"] += 1
    out.append("__page_damp__")
    return out


def _r_blame_hurt(world: World) -> list[str]:
    out: list[str] = []
    maker = world.entities.get("maker")
    friend = world.entities.get("friend")
    if not maker or not friend:
        return out
    if maker.memes["blame"] < THRESHOLD:
        return out
    sig = ("blame_hurt", maker.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.memes["hurt"] += 1
    maker.memes["guilt_seed"] += 1
    out.append("__hurt__")
    return out


CAUSAL_RULES = [
    Rule(name="steam_wrinkle", tag="physical", apply=_r_steam_wrinkle),
    Rule(name="blame_hurt", tag="social", apply=_r_blame_hurt),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def page_at_risk(page: PageKind, kettle: KettleKind, draft: DraftKind) -> bool:
    return page.paper_like and page.steam_risk and kettle.hot and draft.strength >= 1


def sensible_helpers() -> list[HelperAction]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN and h.safe_near_hot]


def page_saved(helper: HelperAction) -> bool:
    return helper.safe_near_hot and helper.sense >= SENSE_MIN


def best_helper() -> HelperAction:
    return max(HELPERS.values(), key=lambda h: (h.sense, h.safe_near_hot))


def explain_rejection(page: PageKind, kettle: KettleKind, draft: DraftKind) -> str:
    if not page.paper_like:
        return (
            f"(No story: {page.label} is not a loose paper page, so the draft and steam "
            f"cannot carry it into danger. Pick a paper page that can flutter in the apt.)"
        )
    if not page.steam_risk:
        return (
            f"(No story: {page.label} does not mind steam, so the kettle creates no real suspense. "
            f"Pick a paper page that can curl or get damp.)"
        )
    if not kettle.hot:
        return "(No story: this kettle does not make hot steam, so the page is never truly at risk.)"
    if draft.strength < 1:
        return "(No story: the room is too still for the page to drift, so nothing suspenseful happens.)"
    return "(No story: this combination has no reasonable page-and-kettle danger.)"


def explain_helper(helper_id: str) -> str:
    h = HELPERS[helper_id]
    better = ", ".join(sorted(x.id for x in sensible_helpers()))
    return (
        f"(Refusing helper '{helper_id}': it is not a safe, sensible way to rescue a page near a hot kettle. "
        f"Try: {better}.)"
    )


def predict_loss(world: World) -> dict:
    sim = world.copy()
    page = sim.get("page")
    kettle = sim.get("kettle")
    page.attrs["place"] = "near_kettle"
    kettle.meters["steaming"] += 1
    propagate(sim, narrate=False)
    return {
        "damp": page.meters["damp"] >= THRESHOLD,
        "curled": page.meters["curled"] >= THRESHOLD,
    }


def opening(world: World, maker: Entity, friend: Entity, apt: Apartment, page_cfg: PageKind) -> None:
    maker.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In a snug little {apt.label}, where evening felt bright, "
        f"{maker.id} bent over a {page_cfg.label} and wrote with delight."
    )
    world.say(
        f"{page_cfg.make_line} {friend.id} sat close by, humming a tune, "
        f"while the window wore shadows of silver-blue moon."
    )


def set_kettle(world: World, parent: Entity, kettle_cfg: KettleKind, apt: Apartment) -> None:
    kettle = world.get("kettle")
    kettle.meters["warming"] += 1
    world.say(
        f"In the tiny {apt.nook}, {parent.label_word} set {kettle_cfg.label} to sing, "
        f"and soon {kettle_cfg.sound} began threading the room like a string."
    )


def promise(world: World, maker: Entity, page_cfg: PageKind) -> None:
    maker.memes["hope"] += 1
    world.say(
        f'"When this {page_cfg.label} is finished, I\'ll read every line," '
        f"said {maker.id}, 'for a cuddle-time treat that will sound just fine.'"
    )


def draft_stirs(world: World, draft_cfg: DraftKind, apt: Apartment) -> None:
    world.say(
        f"Then {apt.window_line}, and {draft_cfg.move_line}. "
        f"The page gave a shiver, then skipped out of sight."
    )


def accuse(world: World, maker: Entity, friend: Entity) -> None:
    maker.memes["fear"] += 1
    maker.memes["blame"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"My page!" cried {maker.id}. "Did you take it away?" '
        f"{friend.id} blinked twice in the hush of the gray."
    )


def search(world: World, maker: Entity, friend: Entity, kettle_cfg: KettleKind) -> None:
    maker.memes["suspense"] += 1
    friend.memes["worry"] += 1
    pred = predict_loss(world)
    world.facts["predicted_damp"] = pred["damp"]
    if pred["damp"]:
        tail = f"and there by the {kettle_cfg.label} lay paper in steam"
    else:
        tail = f"and there by the {kettle_cfg.label} lay page in a gleam"
    world.say(
        f"They looked under pillows, behind every chair, "
        f"{tail}."
    )


def danger(world: World, maker: Entity, friend: Entity, kettle_cfg: KettleKind) -> None:
    page = world.get("page")
    kettle = world.get("kettle")
    page.attrs["place"] = "near_kettle"
    kettle.meters["steaming"] += 1
    propagate(world, narrate=False)
    maker.memes["fear"] += 1
    friend.memes["fear"] += 1
    world.say(
        f"{kettle_cfg.steam_line} The lost little page curled close to the spout, "
        f"and both children wondered if hope had run out."
    )


def recover_success(world: World, helper: HelperAction, friend: Entity, page_cfg: PageKind) -> None:
    page = world.get("page")
    page.attrs["place"] = "safe_table"
    page.meters["rescued"] += 1
    page.meters["damp"] = 0.0
    page.meters["curled"] = 0.0
    friend.memes["brave"] += 1
    world.say(helper.success_line.format(friend=friend.id, page=page_cfg.label))


def recover_fail(world: World, helper: HelperAction, friend: Entity, page_cfg: PageKind) -> None:
    page = world.get("page")
    page.attrs["place"] = "near_kettle"
    page.meters["damp"] += 1
    page.meters["curled"] += 1
    friend.memes["worry"] += 1
    world.say(helper.fail_line.format(friend=friend.id, page=page_cfg.label))


def reconcile(world: World, maker: Entity, friend: Entity, page_cfg: PageKind, saved: bool) -> None:
    maker.memes["guilt"] += 1
    maker.memes["blame"] = 0.0
    maker.memes["love"] += 1
    friend.memes["love"] += 1
    friend.memes["hurt"] = 0.0
    if saved:
        world.say(
            f'{maker.id} felt a pinch in {maker.pronoun("possessive")} chest and said, '
            f'"I spoke too fast. I was frightened, not fair."'
        )
        world.say(
            f'"I did not take your {page_cfg.label}," said {friend.id} with a sigh. '
            f'"I wanted to save it, not make it say goodbye."'
        )
        world.say(
            f"They hugged in the lamplight and made their hearts right. "
            f"Then side by side they smoothed the page flat and bright."
        )
    else:
        world.say(
            f'{maker.id} looked down and whispered, "I blamed you in fear. '
            f'I am sorry I said what was unkind to hear."'
        )
        world.say(
            f'{friend.id} nodded softly. "I felt hurt for a bit, '
            f'but we can mend more than a page when together we sit."'
        )
        world.say(
            f"So they fetched a fresh sheet for the table that night, "
            f"and started again with their shoulders pulled tight."
        )


def ending(world: World, maker: Entity, friend: Entity, page_cfg: PageKind, saved: bool, apt: Apartment) -> None:
    maker.memes["relief"] += 1
    friend.memes["relief"] += 1
    if saved:
        world.say(
            f"Soon laughter came back to the warm little {apt.label} air. "
            f"{page_cfg.final_line} and friendship was mended with care."
        )
    else:
        world.say(
            f"In their quiet little {apt.label}, no one stayed sore. "
            f"A new page held room for two names and much more."
        )


def tell(
    apt: Apartment,
    page_cfg: PageKind,
    kettle_cfg: KettleKind,
    draft_cfg: DraftKind,
    helper: HelperAction,
    maker_name: str = "Mina",
    maker_gender: str = "girl",
    friend_name: str = "Jules",
    friend_gender: str = "boy",
    parent_type: str = "mother",
    relation: str = "friends",
) -> World:
    world = World()
    maker = world.add(Entity(id=maker_name, kind="character", type=maker_gender, role="maker"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    page = world.add(
        Entity(
            id="page",
            type="page",
            label=page_cfg.label,
            phrase=f"a {page_cfg.label}",
            owner=maker.id,
            paper_like=page_cfg.paper_like,
            movable=True,
            attrs={"place": "table"},
        )
    )
    world.add(
        Entity(
            id="kettle",
            type="kettle",
            label=kettle_cfg.label,
            phrase=f"the {kettle_cfg.label}",
            hot=kettle_cfg.hot,
            movable=False,
        )
    )
    world.facts["relation"] = relation

    opening(world, maker, friend, apt, page_cfg)
    promise(world, maker, page_cfg)

    world.para()
    set_kettle(world, parent, kettle_cfg, apt)
    draft_stirs(world, draft_cfg, apt)
    accuse(world, maker, friend)
    search(world, maker, friend, kettle_cfg)

    world.para()
    danger(world, maker, friend, kettle_cfg)
    saved = page_saved(helper)
    if saved:
        recover_success(world, helper, friend, page_cfg)
    else:
        recover_fail(world, helper, friend, page_cfg)

    world.para()
    reconcile(world, maker, friend, page_cfg, saved)
    ending(world, maker, friend, page_cfg, saved, apt)

    outcome = "saved" if saved else "remade"
    world.facts.update(
        maker=maker,
        friend=friend,
        parent=parent,
        page=page,
        apt=apt,
        page_cfg=page_cfg,
        kettle_cfg=kettle_cfg,
        draft_cfg=draft_cfg,
        helper=helper,
        outcome=outcome,
        saved=saved,
        damaged=page.meters["damp"] >= THRESHOLD or page.meters["curled"] >= THRESHOLD,
    )
    return world


APARTMENTS = {
    "cozy": Apartment(
        id="cozy",
        label="apt",
        nook="kitchen nook",
        window_line="the window gave one tiny clap to the night",
        tags={"apartment"},
    ),
    "brick": Apartment(
        id="brick",
        label="brick apt",
        nook="narrow kitchen corner",
        window_line="the old window whispered and clicked in the night",
        tags={"apartment"},
    ),
    "sunset": Apartment(
        id="sunset",
        label="sunset apt",
        nook="small stove-side corner",
        window_line="the curtain breathed softly and let in the night",
        tags={"apartment"},
    ),
}

PAGES = {
    "poem": PageKind(
        id="poem",
        label="poem page",
        make_line="It was a rhyming page for a bedtime show,",
        final_line="The poem page rustled but still had its glow",
        paper_like=True,
        steam_risk=True,
        remakeable=True,
        tags={"page", "poem"},
    ),
    "drawing": PageKind(
        id="drawing",
        label="drawing page",
        make_line="It was a drawing page full of stars in a row,",
        final_line="The drawing page waited with moon-colored glow",
        paper_like=True,
        steam_risk=True,
        remakeable=True,
        tags={"page", "drawing"},
    ),
    "letter": PageKind(
        id="letter",
        label="letter page",
        make_line="It was a letter page folded neat and slow,",
        final_line="The letter page rested with a soft thankful glow",
        paper_like=True,
        steam_risk=True,
        remakeable=True,
        tags={"page", "letter"},
    ),
    "chalkboard": PageKind(
        id="chalkboard",
        label="chalkboard slate",
        make_line="It was a hard little slate with chalky white snow,",
        final_line="The slate stayed sturdy wherever winds blow",
        paper_like=False,
        steam_risk=False,
        remakeable=True,
        tags={"slate"},
    ),
}

KETTLES = {
    "tea": KettleKind(
        id="tea",
        label="kettle",
        sound="a low silver whistle",
        steam_line="The kettle breathed mist with a hiss and a pout.",
        hot=True,
        tags={"kettle", "steam"},
    ),
    "blue": KettleKind(
        id="blue",
        label="blue kettle",
        sound="a thin little whistle",
        steam_line="The blue kettle sighed, sending white ribbons out.",
        hot=True,
        tags={"kettle", "steam"},
    ),
    "quiet": KettleKind(
        id="quiet",
        label="quiet kettle",
        sound="a shy little whistle",
        steam_line="The quiet kettle steamed, letting pale feathers out.",
        hot=True,
        tags={"kettle", "steam"},
    ),
}

DRAFTS = {
    "window": DraftKind(
        id="window",
        label="window draft",
        move_line="a window draft tugged at the edge of the page with a flighty little bite",
        strength=2,
        tags={"draft", "window"},
    ),
    "hall": DraftKind(
        id="hall",
        label="hall draft",
        move_line="a hall draft slipped by and teased the loose page into flight",
        strength=1,
        tags={"draft"},
    ),
    "still": DraftKind(
        id="still",
        label="still air",
        move_line="the air hardly moved at all",
        strength=0,
        tags={"still"},
    ),
}

HELPERS = {
    "tongs": HelperAction(
        id="tongs",
        label="kitchen tongs",
        sense=3,
        safe_near_hot=True,
        success_line="{friend} reached with kitchen tongs, quick and light, and lifted the {page} clear of the white steaming bright.",
        fail_line="{friend} pinched with kitchen tongs, but came in too slow, and the {page} stayed damp in the kettle's glow.",
        qa_line="used kitchen tongs to lift the page away from the hot kettle",
        tags={"tongs", "safe_help"},
    ),
    "wooden_spoon": HelperAction(
        id="wooden_spoon",
        label="wooden spoon",
        sense=2,
        safe_near_hot=True,
        success_line="{friend} slid in a wooden spoon, steady and right, and nudged the {page} back into safe light.",
        fail_line="{friend} tried with a wooden spoon, but could not quite steer, and the {page} stayed trembling too close to the steam near.",
        qa_line="used a wooden spoon to nudge the page away from the steam",
        tags={"spoon", "safe_help"},
    ),
    "bare_hand": HelperAction(
        id="bare_hand",
        label="bare hand",
        sense=0,
        safe_near_hot=False,
        success_line="{friend} snatched with a bare hand and got lucky that night.",
        fail_line="{friend} reached with a bare hand, then pulled back in fright; the {page} stayed too near to the steam and the light.",
        qa_line="reached with a bare hand",
        tags={"unsafe"},
    ),
    "blow": HelperAction(
        id="blow",
        label="blowing on it",
        sense=1,
        safe_near_hot=False,
        success_line="{friend} blew on the page and somehow it sailed right.",
        fail_line="{friend} tried blowing on the page, but the steam and the draft only made its path stranger.",
        qa_line="tried to blow the page away",
        tags={"unsafe"},
    ),
}


GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Ivy", "Ruby", "Anna", "Cora"]
BOY_NAMES = ["Jules", "Milo", "Owen", "Finn", "Theo", "Eli", "Ben", "Noah"]
TRAITS = ["gentle", "careful", "bright", "quick", "kind", "thoughtful"]


@dataclass
class StoryParams:
    apt: str
    page: str
    kettle: str
    draft: str
    helper: str
    maker: str
    maker_gender: str
    friend: str
    friend_gender: str
    parent: str
    relation: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        apt="cozy",
        page="poem",
        kettle="tea",
        draft="window",
        helper="tongs",
        maker="Mina",
        maker_gender="girl",
        friend="Jules",
        friend_gender="boy",
        parent="mother",
        relation="friends",
        trait="gentle",
    ),
    StoryParams(
        apt="brick",
        page="drawing",
        kettle="blue",
        draft="hall",
        helper="wooden_spoon",
        maker="Theo",
        maker_gender="boy",
        friend="Lila",
        friend_gender="girl",
        parent="father",
        relation="siblings",
        trait="careful",
    ),
    StoryParams(
        apt="sunset",
        page="letter",
        kettle="quiet",
        draft="window",
        helper="tongs",
        maker="Ruby",
        maker_gender="girl",
        friend="Milo",
        friend_gender="boy",
        parent="mother",
        relation="friends",
        trait="kind",
    ),
    StoryParams(
        apt="cozy",
        page="poem",
        kettle="blue",
        draft="hall",
        helper="wooden_spoon",
        maker="Eli",
        maker_gender="boy",
        friend="Anna",
        friend_gender="girl",
        parent="father",
        relation="siblings",
        trait="bright",
    ),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    if not sensible_helpers():
        return combos
    for apt_id in APARTMENTS:
        for page_id, page in PAGES.items():
            for kettle_id, kettle in KETTLES.items():
                for draft_id, draft in DRAFTS.items():
                    if page_at_risk(page, kettle, draft):
                        combos.append((apt_id, page_id, kettle_id, draft_id))
    return combos


KNOWLEDGE = {
    "apartment": [
        (
            "What is an apt?",
            "An apt is short for apartment. It is a home made of rooms inside a bigger building."
        )
    ],
    "page": [
        (
            "What is a page?",
            "A page is one sheet in a book, notebook, or letter. Paper pages can bend, flutter, and tear."
        )
    ],
    "kettle": [
        (
            "What does a kettle do?",
            "A kettle heats water until it is very hot. Some kettles whistle when the water is ready."
        )
    ],
    "steam": [
        (
            "Why can steam make paper curl?",
            "Steam is warm water in the air. When paper gets damp from it, the paper can wrinkle and curl."
        )
    ],
    "draft": [
        (
            "What is a draft from a window?",
            "A draft is a little moving stream of air. It can push light things like paper across a room."
        )
    ],
    "tongs": [
        (
            "What are kitchen tongs for?",
            "Kitchen tongs help grown-ups grab or lift hot things from a safer distance. They keep hands farther from the heat."
        )
    ],
    "spoon": [
        (
            "Why is a wooden spoon safer than a bare hand near heat?",
            "A wooden spoon lets you reach from farther away. That helps keep your skin away from hot steam."
        )
    ],
    "sorry": [
        (
            "What does it mean to reconcile after a fight?",
            "To reconcile means to make peace again after hurt feelings. People listen, say sorry, and choose kindness together."
        )
    ],
}

KNOWLEDGE_ORDER = ["apartment", "page", "kettle", "steam", "draft", "tongs", "spoon", "sorry"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    maker = f["maker"]
    friend = f["friend"]
    page_cfg = f["page_cfg"]
    helper = f["helper"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old set in an apt, where a {page_cfg.label} goes missing near a kettle and the ending includes reconciliation.',
        f"Tell a suspenseful but gentle story where {maker.id} thinks {friend.id} took a {page_cfg.label}, but the real danger is steam near a kettle.",
        f'Write a child-facing rhyming tale using the words "apt", "page", and "kettle", where someone says sorry and {helper.label} helps solve the problem.',
    ]


def pair_noun(maker: Entity, friend: Entity, relation: str) -> str:
    if relation == "siblings":
        if maker.type == "girl" and friend.type == "girl":
            return "two sisters"
        if maker.type == "boy" and friend.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    maker = f["maker"]
    friend = f["friend"]
    parent = f["parent"]
    page_cfg = f["page_cfg"]
    helper = f["helper"]
    kettle_cfg = f["kettle_cfg"]
    apt = f["apt"]
    pair = pair_noun(maker, friend, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {maker.id} and {friend.id}, in a small {apt.label}. Their {pw} also starts the kettle that helps set the problem in motion."
        ),
        (
            f"What was on the {page_cfg.label}?",
            f"{maker.id} was making something special on the {page_cfg.label}. It mattered because {maker.pronoun('subject')} hoped to share it aloud later."
        ),
        (
            "Why did the story feel suspenseful?",
            f"The page suddenly vanished, and the children did not know where it had gone. Then they spotted it near the {kettle_cfg.label}, where steam might make it curl and spoil."
        ),
        (
            f"Why did {maker.id} blame {friend.id}?",
            f"{maker.id} felt scared when the page disappeared and spoke too quickly. The fear of losing the page turned into blame before {maker.pronoun('subject')} knew the truth."
        ),
    ]
    if f["saved"]:
        qa.append(
            (
                f"How did {friend.id} help save the page?",
                f"{friend.id} {helper.qa_line}. That worked because it kept {friend.pronoun('possessive')} hand farther from the hot steam while moving the page to safety."
            )
        )
        qa.append(
            (
                "How did they reconcile?",
                f"{maker.id} admitted the blame was unfair and said sorry. {friend.id} listened, and together they smoothed the page and repaired the hurt feelings."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended warmly, with the page safe again and the friendship mended. The last image shows the little apt feeling peaceful instead of worried."
            )
        )
    else:
        qa.append(
            (
                "Was the page saved in time?",
                f"No. The page stayed too close to the steam and became too damp to keep as it was. Even so, the children solved the deeper problem by making peace and beginning again together."
            )
        )
        qa.append(
            (
                "How did they reconcile after the mistake?",
                f"{maker.id} apologized for blaming {friend.id}. Then both children chose a fresh page and worked side by side, which showed their feelings were mended."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"apartment", "page", "kettle", "steam", "sorry", "draft"}
    helper = world.facts["helper"]
    if "tongs" in helper.tags:
        tags.add("tongs")
    if "spoon" in helper.tags:
        tags.add("spoon")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [name for name, on in (("hot", e.hot), ("paper_like", e.paper_like), ("can_reach_hot", e.can_reach_hot)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def outcome_of(params: StoryParams) -> str:
    helper = HELPERS[params.helper]
    return "saved" if page_saved(helper) else "remade"


ASP_RULES = r"""
% Reasonableness gate: a valid story needs a loose page, a hot kettle,
% and enough draft to move the page into danger.
hazard(P, K, D) :- page(P), paper_like(P), steam_risk(P),
                   kettle(K), hot(K),
                   draft(D), strength(D, S), S >= 1.
sensible(H) :- helper(H), sense(H, S), sense_min(M), S >= M, safe_near_hot(H).
valid(A, P, K, D) :- apartment(A), hazard(P, K, D).

% Outcome model.
saved :- chosen_helper(H), sensible(H).
outcome(saved) :- saved.
outcome(remade) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for aid in APARTMENTS:
        lines.append(asp.fact("apartment", aid))
    for pid, page in PAGES.items():
        lines.append(asp.fact("page", pid))
        if page.paper_like:
            lines.append(asp.fact("paper_like", pid))
        if page.steam_risk:
            lines.append(asp.fact("steam_risk", pid))
    for kid, kettle in KETTLES.items():
        lines.append(asp.fact("kettle", kid))
        if kettle.hot:
            lines.append(asp.fact("hot", kid))
    for did, draft in DRAFTS.items():
        lines.append(asp.fact("draft", did))
        lines.append(asp.fact("strength", did, draft.strength))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("sense", hid, helper.sense))
        if helper.safe_near_hot:
            lines.append(asp.fact("safe_near_hot", hid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_helpers() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(h for (h,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_helper", params.helper)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_helpers = {h.id for h in sensible_helpers()}
    asp_helpers = set(asp_sensible_helpers())
    if py_helpers == asp_helpers:
        print(f"OK: sensible helpers match ({sorted(py_helpers)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible helpers: python={sorted(py_helpers)} clingo={sorted(asp_helpers)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "kettle" not in sample.story or "page" not in sample.story:
            raise StoryError("Smoke test story did not render expected content.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Rhyming apartment storyworld: a missing page, a steaming kettle, suspense, and reconciliation."
    )
    ap.add_argument("--apt", choices=APARTMENTS)
    ap.add_argument("--page", choices=PAGES)
    ap.add_argument("--kettle", choices=KETTLES)
    ap.add_argument("--draft", choices=DRAFTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--relation", choices=["friends", "siblings"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.page and args.kettle and args.draft:
        page = PAGES[args.page]
        kettle = KETTLES[args.kettle]
        draft = DRAFTS[args.draft]
        if not page_at_risk(page, kettle, draft):
            raise StoryError(explain_rejection(page, kettle, draft))
    if args.page and args.page in PAGES and not PAGES[args.page].paper_like:
        page = PAGES[args.page]
        kettle = KETTLES[args.kettle] if args.kettle else next(iter(KETTLES.values()))
        draft = DRAFTS[args.draft] if args.draft else next(iter(DRAFTS.values()))
        raise StoryError(explain_rejection(page, kettle, draft))
    if args.helper and args.helper in HELPERS and not page_saved(HELPERS[args.helper]):
        raise StoryError(explain_helper(args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.apt is None or combo[0] == args.apt)
        and (args.page is None or combo[1] == args.page)
        and (args.kettle is None or combo[2] == args.kettle)
        and (args.draft is None or combo[3] == args.draft)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    apt_id, page_id, kettle_id, draft_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(h.id for h in sensible_helpers()))
    maker, maker_gender = _pick_child(rng)
    friend, friend_gender = _pick_child(rng, avoid=maker)
    parent = args.parent or rng.choice(["mother", "father"])
    relation = args.relation or rng.choice(["friends", "siblings"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        apt=apt_id,
        page=page_id,
        kettle=kettle_id,
        draft=draft_id,
        helper=helper_id,
        maker=maker,
        maker_gender=maker_gender,
        friend=friend,
        friend_gender=friend_gender,
        parent=parent,
        relation=relation,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in (
        ("apt", APARTMENTS),
        ("page", PAGES),
        ("kettle", KETTLES),
        ("draft", DRAFTS),
        ("helper", HELPERS),
    ):
        value = getattr(params, key)
        if value not in table:
            raise StoryError(f"(Invalid {key}: {value})")

    if not page_at_risk(PAGES[params.page], KETTLES[params.kettle], DRAFTS[params.draft]):
        raise StoryError(explain_rejection(PAGES[params.page], KETTLES[params.kettle], DRAFTS[params.draft]))
    if not page_saved(HELPERS[params.helper]):
        raise StoryError(explain_helper(params.helper))

    world = tell(
        apt=APARTMENTS[params.apt],
        page_cfg=PAGES[params.page],
        kettle_cfg=KETTLES[params.kettle],
        draft_cfg=DRAFTS[params.draft],
        helper=HELPERS[params.helper],
        maker_name=params.maker,
        maker_gender=params.maker_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        relation=params.relation,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        helpers = asp_sensible_helpers()
        combos = asp_valid_combos()
        print(f"sensible helpers: {', '.join(helpers)}\n")
        print(f"{len(combos)} compatible (apt, page, kettle, draft) combos:\n")
        for apt_id, page_id, kettle_id, draft_id in combos:
            print(f"  {apt_id:8} {page_id:10} {kettle_id:8} {draft_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.maker} & {p.friend}: {p.page} in {p.apt} ({p.helper}, {outcome_of(p)})"
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
