#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/park_inner_monologue_happy_ending_folk_tale.py
========================================================================

A small folk-tale-like storyworld set in a park. A child sees someone in a small
trouble, thinks carefully to avoid making the trouble worse, and finds the right
kind of help. Every valid story ends happily, but the world still models a real
tension: some helpers fit the obstacle and some do not, and some children must
first steady themselves with an inner thought before acting wisely.

Run it
------
    python storyworlds/worlds/gpt-5.4/park_inner_monologue_happy_ending_folk_tale.py
    python storyworlds/worlds/gpt-5.4/park_inner_monologue_happy_ending_folk_tale.py --situation kite_tree --helper keeper_ladder
    python storyworlds/worlds/gpt-5.4/park_inner_monologue_happy_ending_folk_tale.py --situation ball_thorns --helper branch_pole
    python storyworlds/worlds/gpt-5.4/park_inner_monologue_happy_ending_folk_tale.py --helper gloves
    python storyworlds/worlds/gpt-5.4/park_inner_monologue_happy_ending_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/park_inner_monologue_happy_ending_folk_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/park_inner_monologue_happy_ending_folk_tale.py --qa --json
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "keeper"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"keeper": "park keeper"}.get(self.type, self.label or self.type)


@dataclass
class Situation:
    id: str
    friend_kind: str
    friend_label: str
    friend_type: str
    item: str
    item_phrase: str
    obstacle: str
    obstacle_phrase: str
    scene: str
    need: str
    direct_risk: str
    compatible: set[str] = field(default_factory=set)
    risky: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    method: str
    handles: set[str] = field(default_factory=set)
    sense: int = 2
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


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if hero is None or friend is None:
        return out
    if hero.meters["unsafe_reach"] < THRESHOLD:
        return out
    sig = ("tension",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    friend.memes["fear"] += 1
    out.append("__tension__")
    return out


def _r_free(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    item = world.entities.get("item")
    if hero is None or friend is None or item is None:
        return out
    if hero.meters["uses_help"] < THRESHOLD:
        return out
    if hero.meters["right_help"] < THRESHOLD:
        return out
    sig = ("free",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["stuck"] = 0.0
    item.meters["freed"] += 1
    hero.memes["relief"] += 1
    hero.memes["kindness"] += 1
    friend.memes["relief"] += 1
    friend.memes["joy"] += 1
    out.append("__freed__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="tension", tag="emotion", apply=_r_tension),
    Rule(name="free", tag="physical", apply=_r_free),
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


def valid_helper_for(situation: Situation, helper: Helper) -> bool:
    return situation.id in helper.handles and helper.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for sid, situation in SITUATIONS.items():
        for hid, helper in HELPERS.items():
            if valid_helper_for(situation, helper):
                combos.append((sid, hid))
    return combos


def predict_direct_reach(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["unsafe_reach"] += 1
    propagate(sim, narrate=False)
    return {
        "worry": hero.memes["worry"],
        "item_still_stuck": sim.get("item").meters["stuck"] >= THRESHOLD,
        "friend_fear": sim.get("friend").memes["fear"],
    }


def outcome_of(params: "StoryParams") -> str:
    situation = SITUATIONS[params.situation]
    if situation.risky and params.trait == "impulsive":
        return "startled"
    return "steady"


def open_tale(world: World, hero: Entity, situation: Situation) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"Once, when the morning was gentle and the sparrows stitched songs through the park, "
        f"{hero.id} walked under the green trees with watchful eyes and a kind heart."
    )
    world.say(
        f"Near {situation.scene}, {hero.pronoun()} saw {situation.friend_phrase if 'friend_phrase' in situation.__dict__ else situation.friend_label} "
        f"standing in trouble, for {situation.item_phrase} was caught by {situation.obstacle_phrase}."
    )


def friend_plea(world: World, friend: Entity, situation: Situation) -> None:
    friend.memes["worry"] += 1
    world.say(
        f'"Oh dear," said {friend.id}, "my {situation.item} is stuck, and I need it {situation.need}."'
    )


def first_impulse(world: World, hero: Entity, situation: Situation, startled: bool) -> None:
    if startled:
        hero.meters["unsafe_reach"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{hero.id} took one quick step forward, ready to tug at once."
        )
        world.say(
            f'But in {hero.pronoun("possessive")} own heart {hero.pronoun()} thought, '
            f'"If I rush, {situation.direct_risk}. I must be small and still inside before I can be brave outside."'
        )
    else:
        hero.memes["care"] += 1
        world.say(
            f'{hero.id} looked once, then twice, and thought, '
            f'"A hasty hand can make a little trouble grow. I will find the wise way first."'
        )


def choose_help(world: World, hero: Entity, helper: Helper, situation: Situation) -> None:
    hero.memes["courage"] += 1
    hero.meters["uses_help"] += 1
    if valid_helper_for(situation, helper):
        hero.meters["right_help"] += 1
    world.say(
        f"So {hero.id} sought {helper.phrase}. {helper.method}"
    )
    propagate(world, narrate=False)


def resolution(world: World, hero: Entity, friend: Entity, helper: Helper, situation: Situation) -> None:
    item = world.get("item")
    if item.meters["freed"] < THRESHOLD:
        raise StoryError("The chosen helper could not truly solve the trouble.")
    world.say(
        f"Soon {situation.item_phrase} came free. {friend.id}'s face brightened as if a cloud had moved away from the sun."
    )
    world.say(
        f'"Thank you," said {friend.id}. "{selfless_line(hero)}"'
    )
    world.say(
        f"And there in the park, beneath the patient trees, they set the matter right and shared a glad laugh together."
    )


def selfless_line(hero: Entity) -> str:
    return {
        "she": "A good day grows better when we help one another.",
        "he": "A good day grows better when we help one another.",
        "they": "A good day grows better when we help one another.",
    }[hero.pronoun()]


def ending_image(world: World, hero: Entity, friend: Entity, situation: Situation) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After that, {friend.id} could use {hero.pronoun('possessive')} {situation.item} as it was meant to be used, "
        f"and {hero.id} walked on through the park feeling taller inside than before."
    )
    world.say(
        "So the tale says: the quickest hand is not always the wisest one, but a thoughtful heart can turn a small sorrow into a bright ending."
    )


def tell(
    situation: Situation,
    helper: Helper,
    hero_name: str = "Mira",
    hero_type: str = "girl",
    friend_name: str = "Pip",
    trait: str = "thoughtful",
) -> World:
    if not valid_helper_for(situation, helper):
        raise StoryError(explain_rejection(situation, helper))

    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", label=hero_name))
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=situation.friend_type,
            role="friend",
            label=situation.friend_label,
            phrase=situation.friend_label,
        )
    )
    item = world.add(Entity(id="item", kind="thing", type="item", label=situation.item, phrase=situation.item_phrase))
    obstacle = world.add(Entity(id="obstacle", kind="thing", type="obstacle", label=situation.obstacle, phrase=situation.obstacle_phrase))
    place = world.add(Entity(id="park", kind="thing", type="place", label="park", phrase="the park"))
    item.meters["stuck"] += 1
    hero.attrs["trait"] = trait
    world.facts["park_name"] = "the park"

    open_tale(world, hero, situation)
    friend_plea(world, friend, situation)

    world.para()
    startled = outcome_of(
        StoryParams(
            situation=situation.id,
            helper=helper.id,
            hero_name=hero_name,
            hero_type=hero_type,
            friend_name=friend_name,
            trait=trait,
            seed=None,
        )
    ) == "startled"
    pred = predict_direct_reach(world)
    world.facts["predicted_worry"] = pred["worry"]
    world.facts["predicted_friend_fear"] = pred["friend_fear"]
    first_impulse(world, hero, situation, startled)

    world.para()
    choose_help(world, hero, helper, situation)
    resolution(world, hero, friend, helper, situation)

    world.para()
    ending_image(world, hero, friend, situation)

    world.facts.update(
        hero=hero,
        friend=friend,
        item=item,
        obstacle=obstacle,
        place=place,
        situation=situation,
        helper=helper,
        outcome=outcome_of(
            StoryParams(
                situation=situation.id,
                helper=helper.id,
                hero_name=hero_name,
                hero_type=hero_type,
                friend_name=friend_name,
                trait=trait,
                seed=None,
            )
        ),
        freed=item.meters["freed"] >= THRESHOLD,
    )
    return world


SITUATIONS = {
    "kite_tree": Situation(
        id="kite_tree",
        friend_kind="child",
        friend_label="a little boy named Pip",
        friend_type="boy",
        item="kite",
        item_phrase="the blue kite",
        obstacle="willow branch",
        obstacle_phrase="a high willow branch",
        scene="the willow at the edge of the grass",
        need="to catch the afternoon wind",
        direct_risk="the branch may shake, the kite may tear, and I may tumble in my hurry",
        compatible={"keeper_ladder", "branch_pole"},
        risky=True,
        tags={"kite", "tree", "park"},
    ),
    "ball_thorns": Situation(
        id="ball_thorns",
        friend_kind="child",
        friend_label="a little girl named Tessa",
        friend_type="girl",
        item="red ball",
        item_phrase="the red ball",
        obstacle="thorn hedge",
        obstacle_phrase="a thorny hedge",
        scene="the rose hedge by the winding path",
        need="for her game to go on",
        direct_risk="the thorns may scratch my hands and push the ball farther in",
        compatible={"gloves", "branch_pole"},
        risky=True,
        tags={"ball", "thorns", "park"},
    ),
    "sailboat_pond": Situation(
        id="sailboat_pond",
        friend_kind="animal",
        friend_label="a duckling named Gold-Down",
        friend_type="thing",
        item="paper boat",
        item_phrase="the little paper boat",
        obstacle="pond reeds",
        obstacle_phrase="the reeds at the edge of the pond",
        scene="the bright pond where reeds whispered together",
        need="for its tiny journey to continue",
        direct_risk="the mud may swallow my shoes, and the boat may sink before I reach it",
        compatible={"branch_pole", "keeper_ladder"},
        risky=True,
        tags={"pond", "boat", "duckling", "park"},
    ),
}

HELPERS = {
    "keeper_ladder": Helper(
        id="keeper_ladder",
        label="the park keeper's ladder",
        phrase="the park keeper with a short ladder",
        method="The keeper came kindly, set the ladder firm, and reached with careful hands.",
        handles={"kite_tree", "sailboat_pond"},
        sense=3,
        tags={"keeper", "ladder"},
    ),
    "branch_pole": Helper(
        id="branch_pole",
        label="a long fallen branch",
        phrase="a long fallen branch from under the oak",
        method="With slow hands and a steady breath, the long branch nudged and lifted without hurting anything.",
        handles={"kite_tree", "ball_thorns", "sailboat_pond"},
        sense=2,
        tags={"branch", "tool"},
    ),
    "gloves": Helper(
        id="gloves",
        label="gardening gloves",
        phrase="a pair of thick gardening gloves from the gardener's cart",
        method="With the gloves on, the hands could part the prickly stems and pull gently where bare fingers should not go.",
        handles={"ball_thorns"},
        sense=3,
        tags={"gloves", "gardener"},
    ),
    "bread": Helper(
        id="bread",
        label="crumbs of bread",
        phrase="a pocketful of bread crumbs",
        method="The crumbs floated and scattered, but they did not truly free what was stuck.",
        handles=set(),
        sense=1,
        tags={"bread"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Ava", "Ella", "Rosa", "Wren", "Ivy"]
BOY_NAMES = ["Oren", "Pip", "Milo", "Finn", "Theo", "Leo", "Ben", "Sam"]
TRAITS = ["thoughtful", "patient", "gentle", "impulsive"]


@dataclass
class StoryParams:
    situation: str
    helper: str
    hero_name: str
    hero_type: str
    friend_name: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        situation="kite_tree",
        helper="keeper_ladder",
        hero_name="Mira",
        hero_type="girl",
        friend_name="Pip",
        trait="thoughtful",
        seed=None,
    ),
    StoryParams(
        situation="ball_thorns",
        helper="gloves",
        hero_name="Oren",
        hero_type="boy",
        friend_name="Tessa",
        trait="impulsive",
        seed=None,
    ),
    StoryParams(
        situation="sailboat_pond",
        helper="branch_pole",
        hero_name="Lina",
        hero_type="girl",
        friend_name="Gold-Down",
        trait="patient",
        seed=None,
    ),
    StoryParams(
        situation="kite_tree",
        helper="branch_pole",
        hero_name="Theo",
        hero_type="boy",
        friend_name="Pip",
        trait="gentle",
        seed=None,
    ),
]


KNOWLEDGE = {
    "park": [
        (
            "What is a park?",
            "A park is a green public place where people can walk, play, and rest among grass, trees, and paths."
        )
    ],
    "kite": [
        (
            "What makes a kite fly?",
            "A kite flies when the wind pushes against it while someone holds the string. The moving air helps lift it up."
        )
    ],
    "tree": [
        (
            "Why can things get stuck in a tree?",
            "Branches spread out like many little arms. Light things like kites and ribbons can catch on them."
        )
    ],
    "thorns": [
        (
            "Why are thorns sharp?",
            "Thorns help protect a plant. They can poke skin, so people should be careful around them."
        )
    ],
    "gloves": [
        (
            "Why do gardeners wear gloves?",
            "Gloves protect hands from rough bark, dirt, and thorns. They let someone work more safely."
        )
    ],
    "pond": [
        (
            "What grows at the edge of a pond?",
            "Many ponds have reeds and grasses growing at the edge. They like wet ground and shallow water."
        )
    ],
    "keeper": [
        (
            "What does a park keeper do?",
            "A park keeper helps care for the park and keeps it safe and tidy. They often know the best tools for a small problem."
        )
    ],
    "tool": [
        (
            "Why is a long stick useful for reaching something far away?",
            "A long stick lets you touch something without leaning your whole body into danger. That can make a rescue safer."
        )
    ],
}
KNOWLEDGE_ORDER = ["park", "kite", "tree", "thorns", "gloves", "pond", "keeper", "tool"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    situation = f["situation"]
    helper = f["helper"]
    return [
        f'Write a short folk tale for a 3-to-5-year-old set in a park. Include inner monologue and a happy ending.',
        f"Tell a gentle story where {hero.id} sees {situation.friend_label} in trouble because {situation.item_phrase} is caught by {situation.obstacle_phrase}, then thinks carefully before using {helper.label}.",
        f'Write a child-facing tale that includes the word "park", shows a character thinking quietly inside, and ends with help given in the right way.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    situation = f["situation"]
    helper = f["helper"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who was walking in the park, and {friend.id}, who needed help. The story follows how {hero.id} chose kindness and care."
        ),
        (
            f"What trouble did {hero.id} find in the park?",
            f"{hero.id} found that {situation.item_phrase} was stuck because of {situation.obstacle_phrase}. That is why {friend.id} could not use it the way they hoped."
        ),
        (
            f"What did {hero.id} think inside before helping?",
            f"{hero.id} told {hero.pronoun('object')}self not to rush. {hero.pronoun().capitalize()} understood that hurrying could make the trouble worse."
        ),
        (
            f"How did {hero.id} solve the problem?",
            f"{hero.id} used {helper.label} to help free {situation.item_phrase}. That worked because the helper fit the kind of trouble in front of them."
        ),
    ]
    if outcome == "startled":
        qa.append(
            (
                f"Did {hero.id} rush at first?",
                f"Almost. {hero.id} stepped forward quickly at first, but then paused and listened to the wise thought in {hero.pronoun('possessive')} heart. That pause kept the trouble from growing."
            )
        )
    else:
        qa.append(
            (
                f"Was {hero.id} careful from the start?",
                f"Yes. {hero.id} looked closely and chose not to grab right away. That careful thinking led to the happy ending."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended happily in the park, with {situation.item_phrase} safely freed and {friend.id} smiling again. The ending shows that thoughtful help can mend a small worry."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    situation = f["situation"]
    helper = f["helper"]
    tags = set(situation.tags) | set(helper.tags) | {"park"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(situation: Situation, helper: Helper) -> str:
    if helper.sense < SENSE_MIN:
        return (
            f"(No story: '{helper.id}' is known, but it is not a sensible fix here "
            f"(sense={helper.sense} < {SENSE_MIN}). A happy folk tale should prefer a safer, more fitting help.)"
        )
    return (
        f"(No story: {helper.label} does not truly solve {situation.id}. "
        f"The helper must match the obstacle, or the child would not have an honest way to help.)"
    )


ASP_RULES = r"""
sensible(H) :- helper(H), sense(H, S), sense_min(M), S >= M.
valid(Sit, H) :- situation(Sit), helper(H), handles(H, Sit), sensible(H).

startled :- chosen_situation(Sit), risky(Sit), trait(impulsive).
steady :- chosen_situation(Sit), not risky(Sit).
steady :- chosen_situation(Sit), risky(Sit), not trait(impulsive).

outcome(startled) :- startled.
outcome(steady) :- steady.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, situation in SITUATIONS.items():
        lines.append(asp.fact("situation", sid))
        if situation.risky:
            lines.append(asp.fact("risky", sid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("sense", hid, helper.sense))
        for sid in sorted(helper.handles):
            lines.append(asp.fact("handles", hid, sid))
    for trait in TRAITS:
        lines.append(asp.fact("trait_name", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_situation", params.situation),
            asp.fact("trait", params.trait),
        ]
    )
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

    cases: list[StoryParams] = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child in a park thinks carefully and helps in the right way."
    )
    ap.add_argument("--situation", choices=sorted(SITUATIONS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--hero", dest="hero_name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=sorted(TRAITS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper is not None and HELPERS[args.helper].sense < SENSE_MIN:
        helper = HELPERS[args.helper]
        raise StoryError(
            f"(No story: '{helper.id}' is too weak or whimsical for this world. Try one of: "
            f"{', '.join(sorted(h for h in HELPERS if HELPERS[h].sense >= SENSE_MIN))}.)"
        )
    if args.situation is not None and args.helper is not None:
        situation = SITUATIONS[args.situation]
        helper = HELPERS[args.helper]
        if not valid_helper_for(situation, helper):
            raise StoryError(explain_rejection(situation, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.situation is None or combo[0] == args.situation)
        and (args.helper is None or combo[1] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    situation_id, helper_id = rng.choice(sorted(combos))
    hero_type = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)

    default_friend_name = {
        "kite_tree": "Pip",
        "ball_thorns": "Tessa",
        "sailboat_pond": "Gold-Down",
    }[situation_id]
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        situation=situation_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=default_friend_name,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.situation not in SITUATIONS:
        raise StoryError(f"Unknown situation: {params.situation}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    if params.trait not in TRAITS:
        raise StoryError(f"Unknown trait: {params.trait}")
    if params.hero_type not in {"girl", "boy"}:
        raise StoryError(f"Unknown hero_type: {params.hero_type}")

    situation = SITUATIONS[params.situation]
    helper = HELPERS[params.helper]
    if not valid_helper_for(situation, helper):
        raise StoryError(explain_rejection(situation, helper))

    world = tell(
        situation=situation,
        helper=helper,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        trait=params.trait,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (situation, helper) combos:\n")
        for situation_id, helper_id in combos:
            print(f"  {situation_id:12} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name}: {p.situation} with {p.helper} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
