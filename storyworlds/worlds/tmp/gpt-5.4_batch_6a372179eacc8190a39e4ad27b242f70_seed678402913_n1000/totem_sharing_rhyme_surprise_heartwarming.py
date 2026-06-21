#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/totem_sharing_rhyme_surprise_heartwarming.py
========================================================================

A small heartwarming story world about two children making a little totem
together. One child starts out holding the only special treasure for the top.
A helper offers a sharing rhyme and a concrete plan for how both children can
belong in the making. A gentle surprise at the end proves that the totem has
become something shared.

The domain is intentionally narrow: a "totem" here is a child-made stack or
dangling craft built from simple pieces. The world model tracks physical state
(the totem becomes built, topped, balanced, glowing) and emotional state
(possessive, left_out, calm, included, joy, love). The rendered story follows
those state changes instead of swapping nouns in a fixed paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/totem_sharing_rhyme_surprise_heartwarming.py
    python storyworlds/worlds/gpt-5.4/totem_sharing_rhyme_surprise_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/totem_sharing_rhyme_surprise_heartwarming.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/totem_sharing_rhyme_surprise_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4/totem_sharing_rhyme_surprise_heartwarming.py --verify
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

# Make the shared result containers importable when this script is run directly:
# storyworlds/worlds/gpt-5.4/<file>.py -> add storyworlds/ to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
GENEROUS_TRAITS = {"gentle", "patient", "kind", "thoughtful"}
MAX_ATTEMPTS = 100


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "teacher", "woman"}
        male = {"boy", "father", "grandfather", "man", "neighbor_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "teacher": "teacher",
            "neighbor_man": "neighbor",
        }.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    place: str
    opening: str
    purpose: str
    base_parts: str
    ending_image: str


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    placement: str
    pairable: bool = False
    hangable: bool = False
    shiny: bool = False
    sound: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SharingPlan:
    id: str
    label: str
    difficulty: int
    need_hangable: bool = False
    intro: str = ""
    action: str = ""
    proof: str = ""


@dataclass
class Surprise:
    id: str
    label: str
    repair: int
    need_pairable: bool = False
    need_shiny: bool = False
    outdoor_only: bool = False
    indoor_only: bool = False
    reveal: str = ""
    ending: str = ""
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


def _r_left_out(world: World) -> list[str]:
    treasure = world.entities.get("treasure")
    friend = world.entities.get("friend")
    owner = world.entities.get("owner")
    if not treasure or not friend or not owner:
        return []
    if treasure.owner != owner.id:
        return []
    if owner.memes["possessive"] < THRESHOLD:
        return []
    sig = ("left_out", friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["left_out"] += 1
    return ["__left_out__"]


def _r_shared_balance(world: World) -> list[str]:
    totem = world.entities.get("totem")
    if not totem:
        return []
    if totem.meters["shared_touch"] < THRESHOLD:
        return []
    sig = ("balanced", "totem")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    totem.meters["balanced"] += 1
    for kid_id in ("owner", "friend"):
        if kid_id in world.entities:
            kid = world.get(kid_id)
            kid.memes["included"] += 1
            kid.memes["joy"] += 1
    return ["__balanced__"]


def _r_surprise_glow(world: World) -> list[str]:
    totem = world.entities.get("totem")
    if not totem:
        return []
    if totem.meters["balanced"] < THRESHOLD or totem.meters["surprised"] < THRESHOLD:
        return []
    sig = ("glow", "totem")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    totem.meters["glowing"] += 1
    for kid_id in ("owner", "friend"):
        if kid_id in world.entities:
            world.get(kid_id).memes["love"] += 1
    return ["__glow__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="left_out", tag="social", apply=_r_left_out),
    Rule(name="shared_balance", tag="physical", apply=_r_shared_balance),
    Rule(name="surprise_glow", tag="emotional", apply=_r_surprise_glow),
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
        for sent in produced:
            world.say(sent)
    return produced


THEMES = {
    "playroom": Theme(
        id="playroom",
        place="the playroom rug",
        opening="the afternoon light made a warm square on the playroom rug",
        purpose="a friendship totem for the shelf by the window",
        base_parts="smooth blocks, painted rings, and a round wooden base",
        ending_image="the little totem stood by the window like a quiet promise",
    ),
    "porch": Theme(
        id="porch",
        place="the front porch step",
        opening="the porch smelled like sun-warmed wood and flowerpots",
        purpose="a welcome totem for the porch rail",
        base_parts="flat stones, bright string, and a sturdy clay pot base",
        ending_image="the little totem watched the porch like a smiling guard",
    ),
    "library": Theme(
        id="library",
        place="the library craft table",
        opening="the library was soft and hushed except for the whisper of turning pages",
        purpose="a story totem for the reading corner",
        base_parts="cardboard circles, paper feathers, and a painted tube base",
        ending_image="the little totem stood near the books as if it were listening too",
    ),
}

TREASURES = {
    "sun_bead": Treasure(
        id="sun_bead",
        label="sun bead",
        phrase="a shiny sun bead",
        placement="at the very top",
        pairable=True,
        hangable=False,
        shiny=True,
        sound=False,
        tags={"bead", "totem", "sharing"},
    ),
    "shell_charm": Treasure(
        id="shell_charm",
        label="shell charm",
        phrase="a pearly shell charm",
        placement="from the top string",
        pairable=True,
        hangable=True,
        shiny=True,
        sound=False,
        tags={"shell", "totem", "sharing"},
    ),
    "bell": Treasure(
        id="bell",
        label="bell",
        phrase="a tiny silver bell",
        placement="from the top string",
        pairable=False,
        hangable=True,
        shiny=True,
        sound=True,
        tags={"bell", "totem", "sharing"},
    ),
}

SHARING = {
    "middle_spot": SharingPlan(
        id="middle_spot",
        label="middle spot",
        difficulty=3,
        need_hangable=False,
        intro="Let's make a middle spot that belongs to both of you.",
        action="Together they set the special piece where both small hands could steady it.",
        proof="That middle place made the whole totem look balanced instead of lonely.",
    ),
    "take_turns": SharingPlan(
        id="take_turns",
        label="take turns",
        difficulty=4,
        need_hangable=False,
        intro="One hand can begin, and the other hand can finish.",
        action="One child placed the special piece, and the other tied the last bright ring beneath it.",
        proof="Because each child changed the top, the totem held both of them in its shape.",
    ),
    "tie_together": SharingPlan(
        id="tie_together",
        label="tie together",
        difficulty=2,
        need_hangable=True,
        intro="If two hands tie one knot, the top belongs to both hands.",
        action="Each child held one end while they tied the special piece on together.",
        proof="The knot only worked because both children pulled at the same time.",
    ),
}

SURPRISES = {
    "matching_piece": Surprise(
        id="matching_piece",
        label="matching piece",
        repair=2,
        need_pairable=True,
        reveal="Then the helper opened a small box and found a second tiny partner for the first piece.",
        ending="Now the top no longer looked like one child's treasure. It looked like a pair keeping each other company.",
        tags={"surprise", "pair"},
    ),
    "heart_shadow": Surprise(
        id="heart_shadow",
        label="heart shadow",
        repair=1,
        need_shiny=True,
        outdoor_only=False,
        indoor_only=False,
        reveal="Then a beam of light slipped across the shiny top, and its shadow on the wall curved into a little heart.",
        ending="The children looked at the heart-shaped shadow and pressed shoulder to shoulder to admire it.",
        tags={"surprise", "light"},
    ),
    "soft_chime": Surprise(
        id="soft_chime",
        label="soft chime",
        repair=2,
        need_shiny=False,
        outdoor_only=False,
        indoor_only=False,
        reveal="When the finished top moved, it gave a soft, unexpected chime that made everybody go still and smile.",
        ending="The tiny sound felt like the totem was saying thank you for being shared.",
        tags={"surprise", "sound"},
    ),
}

HELPERS = {
    "grandmother": "grandmother",
    "teacher": "teacher",
    "grandfather": "grandfather",
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Noah", "Eli", "Theo", "Jack"]
TRAITS = ["gentle", "patient", "kind", "thoughtful", "eager", "careful"]


@dataclass
class StoryParams:
    theme: str
    treasure: str
    sharing: str
    surprise: str
    owner_name: str
    owner_gender: str
    friend_name: str
    friend_gender: str
    helper: str
    owner_trait: str
    friend_trait: str
    relation: str = "friends"
    owner_age: int = 5
    friend_age: int = 5
    seed: Optional[int] = None


def initial_generosity(trait: str) -> int:
    return 4 if trait in GENEROUS_TRAITS else 3


def relation_bonus(relation: str) -> int:
    return 1 if relation == "siblings" else 0


def compatible_plan(treasure: Treasure, plan: SharingPlan) -> bool:
    if plan.need_hangable and not treasure.hangable:
        return False
    return True


def compatible_surprise(theme: Theme, treasure: Treasure, surprise: Surprise) -> bool:
    if surprise.need_pairable and not treasure.pairable:
        return False
    if surprise.need_shiny and not treasure.shiny:
        return False
    if surprise.indoor_only and theme.id not in {"playroom", "library"}:
        return False
    if surprise.outdoor_only and theme.id not in {"porch"}:
        return False
    if surprise.id == "soft_chime" and not treasure.sound:
        return False
    return True


def outcome_of(params: StoryParams) -> str:
    treasure = TREASURES[params.treasure]
    plan = SHARING[params.sharing]
    surprise = SURPRISES[params.surprise]
    theme = THEMES[params.theme]
    if not compatible_plan(treasure, plan) or not compatible_surprise(theme, treasure, surprise):
        return "invalid"
    support = initial_generosity(params.owner_trait) + relation_bonus(params.relation) + 1
    if support >= plan.difficulty:
        return "shared_early"
    if support + surprise.repair >= plan.difficulty:
        return "shared_after_surprise"
    return "kept_apart"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id, theme in THEMES.items():
        for treasure_id, treasure in TREASURES.items():
            for sharing_id, sharing in SHARING.items():
                if not compatible_plan(treasure, sharing):
                    continue
                for surprise_id, surprise in SURPRISES.items():
                    if compatible_surprise(theme, treasure, surprise):
                        combos.append((theme_id, treasure_id, sharing_id, surprise_id))
    return combos


def explain_rejection(theme: Theme, treasure: Treasure, sharing: SharingPlan, surprise: Surprise) -> str:
    if not compatible_plan(treasure, sharing):
        return (
            f"(No story: {treasure.phrase} cannot use the '{sharing.label}' plan. "
            f"That plan needs a piece that can be tied or hung together.)"
        )
    if surprise.need_pairable and not treasure.pairable:
        return (
            f"(No story: the '{surprise.label}' surprise needs a treasure with a matching partner, "
            f"but {treasure.phrase} does not come in a sensible pair here.)"
        )
    if surprise.id == "soft_chime" and not treasure.sound:
        return (
            f"(No story: the '{surprise.label}' surprise needs a treasure that can make a sound, "
            f"but {treasure.phrase} would stay silent.)"
        )
    if surprise.need_shiny and not treasure.shiny:
        return (
            f"(No story: the '{surprise.label}' surprise needs a shiny top so light can do something visible.)"
        )
    return (
        f"(No story: {theme.place} does not support that surprise in a clear, child-facing way.)"
    )


def explain_outcome_failure(params: StoryParams) -> str:
    plan = SHARING[params.sharing]
    surprise = SURPRISES[params.surprise]
    return (
        f"(No story: with owner trait '{params.owner_trait}', the '{plan.label}' plan would not be enough, "
        f"and the '{surprise.label}' surprise would still not gently move the story into sharing.)"
    )


def predict_hurt(world: World) -> dict:
    sim = world.copy()
    owner = sim.get("owner")
    owner.memes["possessive"] += 1
    propagate(sim, narrate=False)
    friend = sim.get("friend")
    return {
        "left_out": friend.memes["left_out"] >= THRESHOLD,
        "sadness": friend.memes["left_out"],
    }


def introduce(world: World, owner: Entity, friend: Entity, theme: Theme) -> None:
    world.say(
        f"One cozy day, {theme.opening}. {owner.id} and {friend.id} sat together at {theme.place} "
        f"to make {theme.purpose}."
    )
    world.say(
        f"They sorted {theme.base_parts} into little piles, and every new piece made the small totem grow taller."
    )


def delight(world: World, owner: Entity, friend: Entity) -> None:
    owner.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f'"A little more here, and a little more there," {friend.id} said, smiling. '
        f'"We are building it with loving care."'
    )


def scarce_treasure(world: World, owner: Entity, friend: Entity, treasure: Treasure) -> None:
    world.get("totem").meters["built"] += 1
    world.add(
        Entity(
            id="treasure",
            type="treasure",
            label=treasure.label,
            phrase=treasure.phrase,
            owner=owner.id,
            tags=set(treasure.tags),
        )
    )
    world.say(
        f"At last only one special piece was left: {treasure.phrase}. It was meant to rest {treasure.placement}."
    )
    world.say(
        f"{owner.id} picked it up first and curled {owner.pronoun('possessive')} fingers around it."
    )


def tension(world: World, owner: Entity, friend: Entity, treasure: Treasure) -> None:
    owner.memes["possessive"] += 1
    pred = predict_hurt(world)
    world.facts["predicted_left_out"] = pred["left_out"]
    propagate(world, narrate=False)
    world.say(
        f'"I want to place the {treasure.label} all by myself," {owner.id} said.'
    )
    if pred["left_out"]:
        world.say(
            f"{friend.id}'s smile shrank to a small line. {friend.pronoun().capitalize()} had helped with every ring and block, "
            f"and now {friend.pronoun()} felt left out."
        )


def helper_ent(helper_type: str) -> Entity:
    return Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
    )


def helper_steps_in(world: World, helper: Entity, owner: Entity, friend: Entity, plan: SharingPlan) -> None:
    world.say(
        f"{helper.label_word.capitalize()} knelt beside them and spoke in a warm, slow voice."
    )
    world.say(
        f'"For a totem made by two, let sharing shine all the way through. {plan.intro}"'
    )
    owner.memes["calm"] += 1
    friend.memes["hope"] += 1


def share_now(world: World, owner: Entity, friend: Entity, treasure: Treasure, plan: SharingPlan) -> None:
    owner.memes["possessive"] = 0.0
    owner.memes["generous"] += 1
    friend.memes["relief"] += 1
    world.get("treasure").owner = "both"
    world.get("totem").meters["topped"] += 1
    world.get("totem").meters["shared_touch"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{owner.id} took a breath and looked at {friend.id}. "
        f'"For me and you, for me and you," {owner.pronoun()} whispered, "let\'s make it true."'
    )
    world.say(plan.action)
    world.say(plan.proof)


def surprise_bridges(world: World, helper: Entity, owner: Entity, friend: Entity, surprise: Surprise) -> None:
    world.say(surprise.reveal)
    world.get("totem").meters["surprised"] += 1
    owner.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    owner.memes["possessive"] = 0.0
    owner.memes["generous"] += 1
    friend.memes["relief"] += 1
    world.get("treasure").owner = "both"
    world.get("totem").meters["topped"] += 1
    world.get("totem").meters["shared_touch"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{owner.id} blinked, then held the special piece out at last. "
        f'"It should be ours," {owner.pronoun()} said.'
    )
    world.say(
        f"{friend.id} moved closer, and together they finished the top with careful hands."
    )


def final_surprise(world: World, surprise: Surprise) -> None:
    if world.get("totem").meters["surprised"] < THRESHOLD:
        world.get("totem").meters["surprised"] += 1
    propagate(world, narrate=False)
    world.say(surprise.ending)


def ending(world: World, owner: Entity, friend: Entity, theme: Theme) -> None:
    world.say(
        f"{owner.id} and {friend.id} stood back to admire it. Now neither child looked like the owner of the totem alone."
    )
    world.say(
        f"They looked like its makers. {theme.ending_image}."
    )


def tell(
    theme: Theme,
    treasure_cfg: Treasure,
    sharing_cfg: SharingPlan,
    surprise_cfg: Surprise,
    owner_name: str,
    owner_gender: str,
    friend_name: str,
    friend_gender: str,
    helper_type: str,
    owner_trait: str,
    friend_trait: str,
    relation: str,
    owner_age: int,
    friend_age: int,
) -> World:
    world = World()
    owner = world.add(
        Entity(
            id=owner_name,
            kind="character",
            type=owner_gender,
            role="owner",
            traits=[owner_trait],
            attrs={"relation": relation, "age": owner_age},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="friend",
            traits=[friend_trait],
            attrs={"relation": relation, "age": friend_age},
        )
    )
    helper = world.add(helper_ent(helper_type))
    totem = world.add(
        Entity(
            id="totem",
            type="totem",
            label="totem",
            phrase="their little totem",
            tags={"totem"},
        )
    )
    owner.memes["generosity_seed"] = float(initial_generosity(owner_trait))
    friend.memes["trust"] += 1

    introduce(world, owner, friend, theme)
    delight(world, owner, friend)
    world.para()
    scarce_treasure(world, owner, friend, treasure_cfg)
    tension(world, owner, friend, treasure_cfg)
    world.para()
    helper_steps_in(world, helper, owner, friend, sharing_cfg)

    outcome = outcome_of(
        StoryParams(
            theme=theme.id,
            treasure=treasure_cfg.id,
            sharing=sharing_cfg.id,
            surprise=surprise_cfg.id,
            owner_name=owner_name,
            owner_gender=owner_gender,
            friend_name=friend_name,
            friend_gender=friend_gender,
            helper=helper_type,
            owner_trait=owner_trait,
            friend_trait=friend_trait,
            relation=relation,
            owner_age=owner_age,
            friend_age=friend_age,
        )
    )

    if outcome == "shared_early":
        share_now(world, owner, friend, treasure_cfg, sharing_cfg)
        world.para()
        final_surprise(world, surprise_cfg)
    elif outcome == "shared_after_surprise":
        surprise_bridges(world, helper, owner, friend, surprise_cfg)
        world.para()
        final_surprise(world, surprise_cfg)
    else:
        raise StoryError("This parameter set would not resolve into a heartwarming sharing story.")

    world.para()
    ending(world, owner, friend, theme)
    world.facts.update(
        theme=theme,
        treasure_cfg=treasure_cfg,
        sharing_cfg=sharing_cfg,
        surprise_cfg=surprise_cfg,
        owner=owner,
        friend=friend,
        helper=helper,
        totem=totem,
        relation=relation,
        outcome=outcome,
        shared=totem.meters["shared_touch"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "totem": [
        (
            "What is a totem?",
            "In this story, a totem is a little standing craft made from pieces stacked or tied together. Children can give it meaning by making it together."
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting more than one person use, enjoy, or help with something. It can turn one special thing into something that belongs to everyone in the moment."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is a pair or group of words that sound alike at the end. Rhymes can make kind words easier to remember and say together."
        )
    ],
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something unexpected that happens or is discovered. A gentle surprise can make a happy moment feel even warmer."
        )
    ],
    "bead": [
        (
            "What is a bead?",
            "A bead is a small piece with a hole or a shape used for decorating. People can string beads or place them on crafts."
        )
    ],
    "shell": [
        (
            "What is a shell charm?",
            "A shell charm is a small decoration made from a shell or shaped like one. It can hang from a string and make a craft feel special."
        )
    ],
    "bell": [
        (
            "Why does a bell make a story feel lively?",
            "A bell makes a small ringing sound when it moves. That tiny sound can make a quiet craft feel alive."
        )
    ],
    "light": [
        (
            "How can light change how something looks?",
            "Light can make shiny things sparkle and cast shadows. Sometimes the new shadow or sparkle feels like a surprise."
        )
    ],
}
KNOWLEDGE_ORDER = ["totem", "sharing", "rhyme", "surprise", "bead", "shell", "bell", "light"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    owner = f["owner"]
    friend = f["friend"]
    treasure = f["treasure_cfg"]
    surprise = f["surprise_cfg"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the word "totem" and features sharing, rhyme, and a surprise.',
        f"Tell a gentle story where {owner.id} and {friend.id} build a little totem together, but only one {treasure.label} is left for the top.",
        f"Write a warm story in which a helper uses a small rhyme to guide two children toward sharing, and end with a soft surprise involving {surprise.label}.",
    ]


def pair_noun(owner: Entity, friend: Entity, relation: str) -> str:
    if relation == "siblings":
        if owner.type == "girl" and friend.type == "girl":
            return "two sisters"
        if owner.type == "boy" and friend.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    owner = f["owner"]
    friend = f["friend"]
    helper = f["helper"]
    theme = f["theme"]
    treasure = f["treasure_cfg"]
    surprise = f["surprise_cfg"]
    sharing = f["sharing_cfg"]
    relation = f["relation"]
    pair = pair_noun(owner, friend, relation)
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {owner.id} and {friend.id}, making a little totem together with help from {helper.label_word}. Their project matters because they both want the totem to feel special."
        ),
        (
            "What were they making?",
            f"They were making {theme.purpose}. The totem grew piece by piece until only the special top treasure was left."
        ),
        (
            f"Why did {friend.id} feel sad?",
            f"{friend.id} felt sad because {owner.id} wanted to place the only {treasure.label} alone. {friend.pronoun().capitalize()} had helped all along, so being left out hurt."
        ),
        (
            "How did the helper try to solve the problem?",
            f"{helper.label_word.capitalize()} used a small rhyme and offered the '{sharing.label}' plan. The rhyme slowed the moment down, and the plan gave both children a real part in finishing the top."
        ),
    ]
    if f["outcome"] == "shared_early":
        out.append(
            (
                f"When did {owner.id} decide to share?",
                f"{owner.id} decided to share right after hearing the rhyme and seeing a better way to finish the totem. The calm words helped {owner.pronoun('object')} move from clutching the piece to offering it."
            )
        )
    else:
        out.append(
            (
                f"What changed {owner.id}'s mind?",
                f"The surprise changed {owner.id}'s mind. When something unexpected and lovely happened, the special piece stopped feeling like something to guard and started feeling like something to share."
            )
        )
    out.append(
        (
            "What was the surprise at the end?",
            f"The surprise was {surprise.label}. It mattered because it turned the finished totem into a shared moment the children could admire together."
        )
    )
    out.append(
        (
            "How did the story end?",
            f"It ended with the children standing together beside the totem, proud of making it together. The final image proves the change: the totem no longer belonged to one child in feeling, but to both."
        )
    )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"totem", "sharing", "rhyme", "surprise"}
    treasure = f["treasure_cfg"]
    if treasure.id == "sun_bead":
        tags.add("bead")
        tags.add("light")
    elif treasure.id == "shell_charm":
        tags.add("shell")
        tags.add("light")
    elif treasure.id == "bell":
        tags.add("bell")
    if f["surprise_cfg"].id == "heart_shadow":
        tags.add("light")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="playroom",
        treasure="sun_bead",
        sharing="middle_spot",
        surprise="heart_shadow",
        owner_name="Lily",
        owner_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        helper="grandmother",
        owner_trait="gentle",
        friend_trait="kind",
        relation="friends",
        owner_age=5,
        friend_age=5,
    ),
    StoryParams(
        theme="porch",
        treasure="shell_charm",
        sharing="tie_together",
        surprise="matching_piece",
        owner_name="Mia",
        owner_gender="girl",
        friend_name="Zoe",
        friend_gender="girl",
        helper="grandfather",
        owner_trait="eager",
        friend_trait="patient",
        relation="siblings",
        owner_age=4,
        friend_age=6,
    ),
    StoryParams(
        theme="library",
        treasure="bell",
        sharing="take_turns",
        surprise="soft_chime",
        owner_name="Leo",
        owner_gender="boy",
        friend_name="Ava",
        friend_gender="girl",
        helper="teacher",
        owner_trait="thoughtful",
        friend_trait="careful",
        relation="friends",
        owner_age=6,
        friend_age=5,
    ),
]


ASP_RULES = r"""
% structural reasonableness
valid(Th, Tr, Sh, Su) :- theme(Th), treasure(Tr), sharing(Sh), surprise(Su),
                         compatible_plan(Tr, Sh), compatible_surprise(Th, Tr, Su).

compatible_plan(Tr, Sh) :- treasure(Tr), sharing(Sh), not need_hangable(Sh).
compatible_plan(Tr, Sh) :- treasure(Tr), sharing(Sh), need_hangable(Sh), hangable(Tr).

compatible_surprise(Th, Tr, Su) :- surprise(Su),
                                   not need_pairable(Su), not need_shiny(Su),
                                   not surprise_sound(Su),
                                   not indoor_only(Su), not outdoor_only(Su).
compatible_surprise(Th, Tr, Su) :- surprise(Su),
                                   need_pairable(Su), pairable(Tr),
                                   not need_shiny(Su), not surprise_sound(Su),
                                   not indoor_only(Su), not outdoor_only(Su).
compatible_surprise(Th, Tr, Su) :- surprise(Su),
                                   need_shiny(Su), shiny(Tr),
                                   not need_pairable(Su), not surprise_sound(Su),
                                   not indoor_only(Su), not outdoor_only(Su).
compatible_surprise(Th, Tr, Su) :- surprise(Su),
                                   surprise_sound(Su), sound(Tr),
                                   not need_pairable(Su), not need_shiny(Su),
                                   not indoor_only(Su), not outdoor_only(Su).
compatible_surprise(Th, Tr, Su) :- surprise(Su),
                                   need_pairable(Su), pairable(Tr),
                                   need_shiny(Su), shiny(Tr),
                                   not surprise_sound(Su),
                                   not indoor_only(Su), not outdoor_only(Su).

support(V) :- owner_trait(T), generous_trait(T), relation_bonus(B), V = 4 + B + 1.
support(V) :- owner_trait(T), not generous_trait(T), relation_bonus(B), V = 3 + B + 1.
relation_bonus(1) :- relation(siblings).
relation_bonus(0) :- not relation(siblings).

shared_early :- plan_difficulty(D), support(S), S >= D.
shared_after_surprise :- not shared_early, plan_difficulty(D), support(S), surprise_repair(R), S + R >= D.
kept_apart :- not shared_early, not shared_after_surprise.

outcome(shared_early) :- shared_early.
outcome(shared_after_surprise) :- shared_after_surprise.
outcome(kept_apart) :- kept_apart.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for treasure_id, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", treasure_id))
        if treasure.hangable:
            lines.append(asp.fact("hangable", treasure_id))
        if treasure.pairable:
            lines.append(asp.fact("pairable", treasure_id))
        if treasure.shiny:
            lines.append(asp.fact("shiny", treasure_id))
        if treasure.sound:
            lines.append(asp.fact("sound", treasure_id))
    for sharing_id, sharing in SHARING.items():
        lines.append(asp.fact("sharing", sharing_id))
        lines.append(asp.fact("plan_difficulty", sharing_id, sharing.difficulty))
        if sharing.need_hangable:
            lines.append(asp.fact("need_hangable", sharing_id))
    for surprise_id, surprise in SURPRISES.items():
        lines.append(asp.fact("surprise", surprise_id))
        lines.append(asp.fact("surprise_repair", surprise_id, surprise.repair))
        if surprise.need_pairable:
            lines.append(asp.fact("need_pairable", surprise_id))
        if surprise.need_shiny:
            lines.append(asp.fact("need_shiny", surprise_id))
        if surprise.outdoor_only:
            lines.append(asp.fact("outdoor_only", surprise_id))
        if surprise.indoor_only:
            lines.append(asp.fact("indoor_only", surprise_id))
        if surprise.id == "soft_chime":
            lines.append(asp.fact("surprise_sound", surprise_id))
    for trait in sorted(GENEROUS_TRAITS):
        lines.append(asp.fact("generous_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("owner_trait", params.owner_trait),
            asp.fact("plan_difficulty", params.sharing, SHARING[params.sharing].difficulty),
            asp.fact("surprise_repair", params.surprise, SURPRISES[params.surprise].repair),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid_combos parity holds ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for s in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if outcome_of(params) != asp_outcome(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome parity holds on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: two children make a little totem, learn to share, and end in a gentle surprise."
    )
    ap.add_argument("--theme", choices=sorted(THEMES))
    ap.add_argument("--treasure", choices=sorted(TREASURES))
    ap.add_argument("--sharing", choices=sorted(SHARING))
    ap.add_argument("--surprise", choices=sorted(SURPRISES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--relation", choices=["friends", "siblings"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.theme and args.treasure and args.sharing and args.surprise:
        theme = THEMES[args.theme]
        treasure = TREASURES[args.treasure]
        sharing = SHARING[args.sharing]
        surprise = SURPRISES[args.surprise]
        if not (compatible_plan(treasure, sharing) and compatible_surprise(theme, treasure, surprise)):
            raise StoryError(explain_rejection(theme, treasure, sharing, surprise))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.treasure is None or combo[1] == args.treasure)
        and (args.sharing is None or combo[2] == args.sharing)
        and (args.surprise is None or combo[3] == args.surprise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    helper = args.helper or rng.choice(sorted(HELPERS))
    relation = args.relation or rng.choice(["friends", "siblings"])

    for _ in range(MAX_ATTEMPTS):
        theme_id, treasure_id, sharing_id, surprise_id = rng.choice(sorted(combos))
        owner_name, owner_gender = pick_child(rng)
        friend_name, friend_gender = pick_child(rng, avoid=owner_name)
        owner_trait = rng.choice(TRAITS)
        friend_trait = rng.choice(TRAITS)
        owner_age, friend_age = rng.sample([4, 5, 6, 7], 2)
        params = StoryParams(
            theme=theme_id,
            treasure=treasure_id,
            sharing=sharing_id,
            surprise=surprise_id,
            owner_name=owner_name,
            owner_gender=owner_gender,
            friend_name=friend_name,
            friend_gender=friend_gender,
            helper=helper,
            owner_trait=owner_trait,
            friend_trait=friend_trait,
            relation=relation,
            owner_age=owner_age,
            friend_age=friend_age,
        )
        outcome = outcome_of(params)
        if outcome in {"shared_early", "shared_after_surprise"}:
            return params

    raise StoryError("(No heartwarming sharing story could be made from those options.)")


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"Unknown theme: {params.theme}")
    if params.treasure not in TREASURES:
        raise StoryError(f"Unknown treasure: {params.treasure}")
    if params.sharing not in SHARING:
        raise StoryError(f"Unknown sharing plan: {params.sharing}")
    if params.surprise not in SURPRISES:
        raise StoryError(f"Unknown surprise: {params.surprise}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")

    theme = THEMES[params.theme]
    treasure = TREASURES[params.treasure]
    sharing = SHARING[params.sharing]
    surprise = SURPRISES[params.surprise]
    if not (compatible_plan(treasure, sharing) and compatible_surprise(theme, treasure, surprise)):
        raise StoryError(explain_rejection(theme, treasure, sharing, surprise))
    if outcome_of(params) not in {"shared_early", "shared_after_surprise"}:
        raise StoryError(explain_outcome_failure(params))

    world = tell(
        theme=theme,
        treasure_cfg=treasure,
        sharing_cfg=sharing,
        surprise_cfg=surprise,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        helper_type=params.helper,
        owner_trait=params.owner_trait,
        friend_trait=params.friend_trait,
        relation=params.relation,
        owner_age=params.owner_age,
        friend_age=params.friend_age,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, treasure, sharing, surprise) combos:\n")
        for theme_id, treasure_id, sharing_id, surprise_id in combos:
            print(f"  {theme_id:8} {treasure_id:12} {sharing_id:12} {surprise_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.owner_name} and {p.friend_name}: {p.treasure}, {p.sharing}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
