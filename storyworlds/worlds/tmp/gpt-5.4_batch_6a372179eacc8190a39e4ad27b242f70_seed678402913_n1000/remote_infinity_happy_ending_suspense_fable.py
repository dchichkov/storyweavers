#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/remote_infinity_happy_ending_suspense_fable.py
==========================================================================

A small fable-flavored storyworld about young animals, a dropped remote, and an
Infinity Lantern that can only shine once the remote is safely recovered.

The world is built around one reasonable constraint: a retrieval method must
actually match where the remote landed. A twig hook can lift something from
reeds or mud near the bank, but it cannot safely fetch a remote floating in deep
water. A leaf boat can carry the remote across water, but it is the wrong tool
for thorns. Invalid choices are rejected with a clear explanation.

Every valid story keeps the "Happy Ending" promise: the middle is suspenseful,
but the world only tells solutions that sensibly work, and the ending image
proves what changed when patience beats a rash grab.

Run it
------
    python storyworlds/worlds/gpt-5.4/remote_infinity_happy_ending_suspense_fable.py
    python storyworlds/worlds/gpt-5.4/remote_infinity_happy_ending_suspense_fable.py --spot deep_pool
    python storyworlds/worlds/gpt-5.4/remote_infinity_happy_ending_suspense_fable.py --method paw_grab
    python storyworlds/worlds/gpt-5.4/remote_infinity_happy_ending_suspense_fable.py --all
    python storyworlds/worlds/gpt-5.4/remote_infinity_happy_ending_suspense_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/remote_infinity_happy_ending_suspense_fable.py --verify
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

# Make the shared result containers importable when this script is run directly
# from its nested directory under storyworlds/worlds/gpt-5.4/.
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
    sex: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.sex == "female":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.sex == "male":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    bank: str
    sky: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    the: str
    surface: str
    distance: int
    drift: int
    detail: str
    danger_line: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    verb: str
    reach: int
    power: int
    sense: int
    safe_surfaces: set[str] = field(default_factory=set)
    text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Lantern:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_remote_danger(world: World) -> list[str]:
    remote = world.get("remote")
    if remote.meters["stuck"] < THRESHOLD:
        return []
    sig = ("danger",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    friend = world.get("friend")
    hero.memes["worry"] += 1
    friend.memes["caution"] += 1
    return ["__danger__"]


def _r_lantern_calm(world: World) -> list[str]:
    lantern = world.get("lantern")
    if lantern.meters["glowing"] < THRESHOLD:
        return []
    sig = ("calm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ch in world.characters():
        ch.memes["relief"] += 1
        ch.memes["joy"] += 1
        ch.memes["fear"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="remote_danger", tag="suspense", apply=_r_remote_danger),
    Rule(name="lantern_calm", tag="ending", apply=_r_lantern_calm),
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


SETTINGS = {
    "willow_pond": Setting(
        id="willow_pond",
        place="the willow pond",
        bank="the mossy bank",
        sky="The evening sky was turning blue and silver.",
        ending="The willow leaves shivered above the light like quiet green hands.",
        tags={"pond", "water"},
    ),
    "mill_stream": Setting(
        id="mill_stream",
        place="the old mill stream",
        bank="the smooth stone bank",
        sky="The last gold of day was sliding off the water.",
        ending="The stream carried the lantern-glow in long bright ribbons.",
        tags={"stream", "water"},
    ),
    "cattail_marsh": Setting(
        id="cattail_marsh",
        place="the cattail marsh",
        bank="the soft grassy edge",
        sky="The dusk air held still for one listening moment.",
        ending="The cattails stood around the light like tall brown candles.",
        tags={"marsh", "water"},
    ),
}

SPOTS = {
    "reed_edge": Spot(
        id="reed_edge",
        label="reed edge",
        the="the reed edge",
        surface="reeds",
        distance=1,
        drift=1,
        detail="It had slipped between two reeds where the water only lapped and whispered.",
        danger_line="One more clumsy reach could knock it into deeper water.",
        tags={"reeds", "near"},
    ),
    "mud_bank": Spot(
        id="mud_bank",
        label="mud bank",
        the="the mud bank",
        surface="mud",
        distance=1,
        drift=0,
        detail="It lay in a ribbon of sticky mud just below the bank.",
        danger_line="A paw pushed in too fast might bury it under brown slime.",
        tags={"mud", "near"},
    ),
    "deep_pool": Spot(
        id="deep_pool",
        label="deep pool",
        the="the deep pool",
        surface="water",
        distance=2,
        drift=2,
        detail="It bobbed on dark water where the bank dropped away all at once.",
        danger_line="The current kept nudging it toward the shadowy middle.",
        tags={"water", "far"},
    ),
    "thorn_bush": Spot(
        id="thorn_bush",
        label="thorn bush",
        the="the thorn bush",
        surface="thorns",
        distance=2,
        drift=0,
        detail="It had bounced into a low thorn bush where the twigs held it tight.",
        danger_line="A rushed paw could come back scratched and still miss the remote.",
        tags={"thorns", "far"},
    ),
}

METHODS = {
    "paw_grab": Method(
        id="paw_grab",
        label="paw grab",
        phrase="a quick paw grab",
        verb="reached straight out with a careful paw",
        reach=1,
        power=1,
        sense=1,
        safe_surfaces={"mud"},
        text="reached straight down and pinched the remote out of the mud before it could sink any farther",
        qa_text="used a careful paw to lift the remote from the mud",
        tags={"patience", "grab"},
    ),
    "reed_hook": Method(
        id="reed_hook",
        label="reed hook",
        phrase="a bent reed hook",
        verb="bent a strong reed into a little hook",
        reach=2,
        power=2,
        sense=3,
        safe_surfaces={"reeds", "mud", "thorns"},
        text="bent a strong reed into a hook and drew the remote back inch by inch",
        qa_text="used a bent reed hook to pull the remote back",
        tags={"tool", "hook"},
    ),
    "leaf_boat": Method(
        id="leaf_boat",
        label="leaf boat",
        phrase="a curled leaf boat",
        verb="set a curled leaf on the water and guided it with a twig",
        reach=3,
        power=4,
        sense=3,
        safe_surfaces={"water", "reeds"},
        text="set a curled leaf on the water, guided it with a twig, and ferried the remote safely to shore",
        qa_text="used a curled leaf boat to ferry the remote to shore",
        tags={"water", "boat"},
    ),
    "forked_branch": Method(
        id="forked_branch",
        label="forked branch",
        phrase="a forked branch",
        verb="slid a forked branch forward very slowly",
        reach=3,
        power=3,
        sense=2,
        safe_surfaces={"thorns", "reeds", "water"},
        text="slid a forked branch forward and lifted the remote free without letting it fall farther",
        qa_text="used a forked branch to lift the remote free",
        tags={"tool", "branch"},
    ),
}

LANTERNS = {
    "infinity_lantern": Lantern(
        id="infinity_lantern",
        label="Infinity Lantern",
        phrase="the Infinity Lantern",
        glow="tiny stars seemed to open inside it and go on and on, almost to infinity",
        tags={"light", "infinity"},
    ),
    "infinity_orb": Lantern(
        id="infinity_orb",
        label="Infinity Orb",
        phrase="the Infinity Orb",
        glow="little rings of light folded into one another until they looked endless, like a small infinity song",
        tags={"light", "infinity"},
    ),
}

HEROES = [
    ("Pip", "mouse", "male"),
    ("Mira", "rabbit", "female"),
    ("Tavi", "fox", "male"),
    ("Nell", "squirrel", "female"),
    ("Bram", "hedgehog", "male"),
    ("Wren", "otter", "female"),
]

FRIENDS = [
    ("Luma", "owl", "female"),
    ("Fern", "tortoise", "female"),
    ("Rowan", "beaver", "male"),
    ("Ash", "badger", "male"),
    ("Clover", "deer", "female"),
    ("Moss", "frog", "male"),
]

TRAITS = ["eager", "bright", "restless", "hopeful", "quick", "earnest"]


def spot_difficulty(spot: Spot) -> int:
    return spot.distance + spot.drift


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def method_works(method: Method, spot: Spot) -> bool:
    return (
        method.sense >= SENSE_MIN
        and spot.surface in method.safe_surfaces
        and method.reach >= spot.distance
        and method.power >= spot_difficulty(spot)
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for spot_id, spot in SPOTS.items():
            for method_id, method in METHODS.items():
                if method_works(method, spot):
                    combos.append((setting_id, spot_id, method_id))
    return combos


def danger_prediction(spot: Spot, rashness: int) -> dict:
    slip_risk = spot.distance + spot.drift + rashness
    return {
        "slip_risk": slip_risk,
        "too_risky": slip_risk >= 3,
    }


def outcome_of(params: "StoryParams") -> str:
    method = METHODS[params.method]
    spot = SPOTS[params.spot]
    margin = method.power - spot_difficulty(spot)
    return "narrow" if margin == 0 else "steady"


def introduce(world: World, hero: Entity, friend: Entity, lantern: Lantern) -> None:
    trait = hero.attrs.get("trait", "")
    world.say(
        f"In {world.setting.place}, there lived a little {hero.type} named {hero.id}, "
        f"an {trait} creature who loved evening wonders."
    )
    world.say(
        f"Each dusk, {hero.id} and {friend.id} climbed to {world.setting.bank} to watch "
        f"{lantern.phrase}, a lamp that only woke when its remote was pressed."
    )
    world.say(world.setting.sky)


def carry_remote(world: World, hero: Entity, lantern: Lantern) -> None:
    hero.memes["anticipation"] += 1
    world.say(
        f"That evening {hero.id} carried the small remote in both paws, already imagining "
        f"how {lantern.label} would shine."
    )


def slip(world: World, hero: Entity, spot: Spot) -> None:
    remote = world.get("remote")
    remote.meters["stuck"] += 1
    remote.meters["distance"] = float(spot.distance)
    remote.meters["drift"] = float(spot.drift)
    propagate(world, narrate=False)
    world.say(
        f"But as {hero.id} stepped over a root, the remote slipped, bounced once, and landed in {spot.the}. "
        f"{spot.detail}"
    )


def rush_impulse(world: World, hero: Entity, spot: Spot) -> None:
    hero.memes["impatience"] += 1
    hero.memes["fear"] += 1
    world.say(
        f'{hero.id} gave a small gasp. "If it drifts away, the lantern will stay dark!" '
        f'{hero.pronoun().capitalize()} darted forward, but {spot.danger_line}'
    )


def warn(world: World, hero: Entity, friend: Entity, spot: Spot) -> None:
    pred = danger_prediction(spot, rashness=1)
    world.facts["predicted_slip_risk"] = pred["slip_risk"]
    friend.memes["care"] += 1
    world.say(
        f'{friend.id} touched {hero.id}\'s shoulder. "Do not snatch at it," '
        f'{friend.pronoun()} said. "A frightened paw makes a bigger trouble. '
        f'One wrong push and the remote may be gone for good."'
    )


def pause(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["patience"] += 1
    world.say(
        f"{hero.id} froze at the edge. The dark water and thorns seemed larger in that quiet pause, "
        f"and {hero.pronoun()} listened."
    )


def recover(world: World, friend: Entity, method: Method) -> None:
    remote = world.get("remote")
    remote.meters["stuck"] = 0.0
    remote.meters["safe"] += 1
    world.say(
        f"Then {friend.id} {method.verb}. Inch by inch, {friend.pronoun()} moved with the calm of someone "
        f"who cared more for success than speed."
    )
    world.say(method.text + ".")
    if world.facts.get("outcome") == "narrow":
        world.say(
            "For one breath the remote wobbled, and both friends held still. Then it slid onto the bank at last."
        )
    else:
        world.say(
            "It came back clean and sure, without one last frightening slip."
        )


def press_remote(world: World, hero: Entity, lantern_cfg: Lantern) -> None:
    lantern = world.get("lantern")
    lantern.meters["glowing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} held the rescued remote as if it were a promise kept, then pressed the bright round button."
    )
    world.say(
        f"At once {lantern_cfg.phrase} opened its warm eye, and {lantern_cfg.glow}."
    )


def ending(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f'{hero.id} smiled at {friend.id}. "The light came because we were careful," '
        f'{hero.pronoun()} said.'
    )
    world.say(
        f'"Yes," said {friend.id}. "Haste loves the edge, but patience brings things home."'
    )
    world.say(world.setting.ending)


def tell(
    setting: Setting,
    spot: Spot,
    method: Method,
    lantern_cfg: Lantern,
    hero_name: str,
    hero_type: str,
    hero_sex: str,
    friend_name: str,
    friend_type: str,
    friend_sex: str,
    trait: str,
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        sex=hero_sex,
        role="hero",
        attrs={"trait": trait},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_type,
        label=friend_name,
        sex=friend_sex,
        role="friend",
    ))
    remote = world.add(Entity(
        id="remote",
        kind="thing",
        type="remote",
        label="remote",
        phrase="the small remote",
    ))
    lantern = world.add(Entity(
        id="lantern",
        kind="thing",
        type="lantern",
        label=lantern_cfg.label,
        phrase=lantern_cfg.phrase,
    ))

    introduce(world, hero, friend, lantern_cfg)
    carry_remote(world, hero, lantern_cfg)

    world.para()
    slip(world, hero, spot)
    rush_impulse(world, hero, spot)
    warn(world, hero, friend, spot)
    pause(world, hero, friend)

    world.para()
    world.facts["outcome"] = "narrow" if method.power == spot_difficulty(spot) else "steady"
    recover(world, friend, method)
    press_remote(world, hero, lantern_cfg)

    world.para()
    ending(world, hero, friend)

    world.facts.update(
        hero=hero,
        friend=friend,
        remote=remote,
        lantern=lantern,
        setting=setting,
        spot=spot,
        method=method,
        lantern_cfg=lantern_cfg,
        retrieved=remote.meters["safe"] >= THRESHOLD,
        glowing=lantern.meters["glowing"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    spot: str
    method: str
    lantern: str
    hero_name: str
    hero_type: str
    hero_sex: str
    friend_name: str
    friend_type: str
    friend_sex: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="willow_pond",
        spot="reed_edge",
        method="reed_hook",
        lantern="infinity_lantern",
        hero_name="Mira",
        hero_type="rabbit",
        hero_sex="female",
        friend_name="Fern",
        friend_type="tortoise",
        friend_sex="female",
        trait="eager",
    ),
    StoryParams(
        setting="mill_stream",
        spot="deep_pool",
        method="leaf_boat",
        lantern="infinity_orb",
        hero_name="Pip",
        hero_type="mouse",
        hero_sex="male",
        friend_name="Rowan",
        friend_type="beaver",
        friend_sex="male",
        trait="restless",
    ),
    StoryParams(
        setting="cattail_marsh",
        spot="thorn_bush",
        method="forked_branch",
        lantern="infinity_lantern",
        hero_name="Nell",
        hero_type="squirrel",
        hero_sex="female",
        friend_name="Clover",
        friend_type="deer",
        friend_sex="female",
        trait="hopeful",
    ),
    StoryParams(
        setting="willow_pond",
        spot="mud_bank",
        method="reed_hook",
        lantern="infinity_orb",
        hero_name="Bram",
        hero_type="hedgehog",
        hero_sex="male",
        friend_name="Luma",
        friend_type="owl",
        friend_sex="female",
        trait="bright",
    ),
]


KNOWLEDGE = {
    "remote": [
        (
            "What is a remote?",
            "A remote is a small thing with buttons that can make another device work from a distance. You press the button here, and the other thing answers over there."
        )
    ],
    "infinity": [
        (
            "What does infinity mean?",
            "Infinity means something that feels as if it could go on without ending. In stories, a shining pattern can look endless even when it fits in a small lantern."
        )
    ],
    "patience": [
        (
            "Why can patience help in a tricky moment?",
            "Patience helps because it gives you time to see the problem clearly instead of making it worse in a rush. A calm pause can be safer than a fast grab."
        )
    ],
    "water": [
        (
            "Why is it hard to pick something up from water?",
            "Water can make things drift, wobble, or sink away from your hand. That is why a floating object often needs the right tool."
        )
    ],
    "thorns": [
        (
            "Why should you be careful around thorns?",
            "Thorns can scratch your skin and catch your fur or clothes. Reaching too fast into them can hurt you without solving the problem."
        )
    ],
    "hook": [
        (
            "What does a hook do?",
            "A hook catches onto something so you can pull it gently toward you. It is useful when your hand should not go straight into a risky place."
        )
    ],
    "boat": [
        (
            "How can a little boat help rescue something?",
            "A small boat can carry an object across water without making it sink. Even a leaf can work like a tiny boat if the water is calm enough and someone guides it carefully."
        )
    ],
    "light": [
        (
            "Why do stories use light at the end?",
            "Light often shows that fear has passed and understanding has arrived. A bright ending lets you see the change with your eyes."
        )
    ],
}
KNOWLEDGE_ORDER = ["remote", "infinity", "water", "thorns", "hook", "boat", "patience", "light"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    spot = f["spot"]
    lantern = f["lantern_cfg"]
    return [
        'Write a short fable for a 3-to-5-year-old that includes the words "remote" and "infinity", has suspense in the middle, and ends happily.',
        f"Tell a gentle suspense story where {hero.label}, a little {hero.type}, drops a remote near {spot.the} just before lighting {lantern.phrase}, and a wiser friend helps.",
        f'Write a fable about patience and careful thinking, where a remote is almost lost and the ending image is a bright light that feels close to infinity.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    spot = f["spot"]
    method = f["method"]
    lantern = f["lantern_cfg"]
    risk = f.get("predicted_slip_risk", 0)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a little {hero.type}, and {friend.label}, {friend.pronoun('possessive')} careful friend. Together they wanted to light {lantern.phrase} at dusk."
        ),
        (
            "What problem started the suspense?",
            f"The remote slipped from {hero.label}'s paws and landed in {spot.the}. That was scary because without the remote the lantern would stay dark, and a rushed grab could send it farther away."
        ),
        (
            f"Why did {friend.label} tell {hero.label} not to snatch at the remote?",
            f"{friend.label} knew the place was risky and that a quick reach could make the trouble worse. The danger was high enough that one wrong push might have lost the remote for good."
        ),
        (
            f"How did {friend.label} get the remote back?",
            f"{friend.label} {method.qa_text}. The method matched the place where the remote had landed, so care worked better than hurry."
        ),
        (
            "How did the story end?",
            f"{hero.label} pressed the rescued remote, and {lantern.phrase} glowed with light that seemed to go on almost to infinity. The bright ending shows that the danger passed because the friends stayed patient."
        ),
    ]
    if risk >= 3:
        qa.append(
            (
                "Was the problem truly dangerous or only surprising?",
                "It was truly dangerous for the remote, even though no one was badly hurt. The place could have hidden it, scratched a paw, or let it drift away if they had acted too fast."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"remote", "infinity", "patience", "light"}
    spot = f["spot"]
    method = f["method"]
    if spot.surface == "water":
        tags.add("water")
    if spot.surface == "thorns":
        tags.add("thorns")
    if method.id == "reed_hook" or method.id == "forked_branch":
        tags.add("hook")
    if method.id == "leaf_boat":
        tags.add("boat")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(method: Method, spot: Spot) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(No story: {method.phrase} is too rash for this fable-world. "
            f"It scores below the common-sense gate, so the story refuses to praise a hasty snatch.)"
        )
    if spot.surface not in method.safe_surfaces:
        return (
            f"(No story: {method.phrase} does not suit {spot.the}. "
            f"That place needs a tool safe for {spot.surface}, or the remote would likely be lost.)"
        )
    if method.reach < spot.distance:
        return (
            f"(No story: {method.phrase} cannot reach {spot.the}. "
            f"The remote is too far away for that method.)"
        )
    if method.power < spot_difficulty(spot):
        return (
            f"(No story: {method.phrase} is not strong enough for {spot.the}. "
            f"The pull of drift and distance is too much for it.)"
        )
    return "(No story: that method and spot do not make a sensible match.)"


ASP_RULES = r"""
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
difficulty(S, D) :- spot(S), distance(S, A), drift(S, B), D = A + B.

works(S, M) :- sensible(M),
               chosen_surface(S, Surf), safe_on(M, Surf),
               distance(S, Dist), reach(M, R), R >= Dist,
               difficulty(S, Need), power(M, P), P >= Need.

valid(Setting, S, M) :- setting(Setting), spot(S), method(M), works(S, M).

outcome(narrow) :- chosen_spot(S), chosen_method(M),
                   works(S, M),
                   difficulty(S, Need), power(M, Need).
outcome(steady) :- chosen_spot(S), chosen_method(M),
                   works(S, M),
                   difficulty(S, Need), power(M, P), P > Need.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        lines.append(asp.fact("chosen_surface", spot_id, spot.surface))
        lines.append(asp.fact("distance", spot_id, spot.distance))
        lines.append(asp.fact("drift", spot_id, spot.drift))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("reach", method_id, method.reach))
        lines.append(asp.fact("power", method_id, method.power))
        for surf in sorted(method.safe_surfaces):
            lines.append(asp.fact("safe_on", method_id, surf))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_spot", params.spot),
        asp.fact("chosen_method", params.method),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for setting_id, spot_id, method_id in sorted(valid_combos())[:12]:
        cases.append(
            StoryParams(
                setting=setting_id,
                spot=spot_id,
                method=method_id,
                lantern="infinity_lantern",
                hero_name="Pip",
                hero_type="mouse",
                hero_sex="male",
                friend_name="Fern",
                friend_type="tortoise",
                friend_sex="female",
                trait="eager",
            )
        )
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a dropped remote, an Infinity Lantern, and a careful rescue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--lantern", choices=LANTERNS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_pair(rng: random.Random) -> tuple[tuple[str, str, str], tuple[str, str, str]]:
    hero = rng.choice(HEROES)
    friend = rng.choice(FRIENDS)
    while friend[0] == hero[0]:
        friend = rng.choice(FRIENDS)
    return hero, friend


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_rejection(METHODS[args.method], SPOTS[args.spot] if args.spot else next(iter(SPOTS.values()))))

    if args.spot and args.method:
        if not method_works(METHODS[args.method], SPOTS[args.spot]):
            raise StoryError(explain_rejection(METHODS[args.method], SPOTS[args.spot]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.spot is None or combo[1] == args.spot)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, spot_id, method_id = rng.choice(sorted(combos))
    lantern_id = args.lantern or rng.choice(sorted(LANTERNS))
    hero, friend = pick_pair(rng)
    return StoryParams(
        setting=setting_id,
        spot=spot_id,
        method=method_id,
        lantern=lantern_id,
        hero_name=hero[0],
        hero_type=hero[1],
        hero_sex=hero[2],
        friend_name=friend[0],
        friend_type=friend[1],
        friend_sex=friend[2],
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.lantern not in LANTERNS:
        raise StoryError(f"(Unknown lantern: {params.lantern})")

    spot = SPOTS[params.spot]
    method = METHODS[params.method]
    if not method_works(method, spot):
        raise StoryError(explain_rejection(method, spot))

    world = tell(
        setting=SETTINGS[params.setting],
        spot=spot,
        method=method,
        lantern_cfg=LANTERNS[params.lantern],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        hero_sex=params.hero_sex,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        friend_sex=params.friend_sex,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name).replace("friend", params.friend_name),
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
        print(f"{len(combos)} compatible (setting, spot, method) combos:\n")
        for setting_id, spot_id, method_id in combos:
            print(f"  {setting_id:13} {spot_id:10} {method_id}")
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
            header = f"### {p.hero_name} at {p.setting}: {p.method} for {p.spot} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
