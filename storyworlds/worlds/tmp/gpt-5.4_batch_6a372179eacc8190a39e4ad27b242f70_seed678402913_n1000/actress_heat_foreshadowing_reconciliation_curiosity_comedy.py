#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/actress_heat_foreshadowing_reconciliation_curiosity_comedy.py
=========================================================================================

A standalone story world about a child actress rehearsing a funny little play on a
hot day. The world models heat-sensitive props, curiosity, a small quarrel, and a
reconciliation that arrives through apology and a sensible cooling fix.

Run it
------
    python storyworlds/worlds/gpt-5.4/actress_heat_foreshadowing_reconciliation_curiosity_comedy.py
    python storyworlds/worlds/gpt-5.4/actress_heat_foreshadowing_reconciliation_curiosity_comedy.py --show royal --prop wax_mustache
    python storyworlds/worlds/gpt-5.4/actress_heat_foreshadowing_reconciliation_curiosity_comedy.py --fix fan
    python storyworlds/worlds/gpt-5.4/actress_heat_foreshadowing_reconciliation_curiosity_comedy.py --all
    python storyworlds/worlds/gpt-5.4/actress_heat_foreshadowing_reconciliation_curiosity_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/actress_heat_foreshadowing_reconciliation_curiosity_comedy.py --verify
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
PATIENCE_TRAITS = {"patient", "gentle"}


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
    tags: set[str] = field(default_factory=set)
    heat_sensitive: bool = False
    need: str = ""
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


@dataclass
class Show:
    id: str
    scene: str
    stage: str
    role_name: str
    joke_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PropCfg:
    id: str
    label: str
    phrase: str
    material: str
    risk_text: str
    droop_text: str
    repair_text: str
    need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ContainerCfg:
    id: str
    label: str
    phrase: str
    sound: str
    secret: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FixCfg:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
    action_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    show: str
    prop: str
    container: str
    fix: str
    actress_name: str
    actress_gender: str
    helper_name: str
    helper_gender: str
    adult: str
    helper_trait: str
    seed: Optional[int] = None


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


def _r_heat_softens(world: World) -> list[str]:
    out: list[str] = []
    sun = world.entities.get("sun")
    prop = world.entities.get("prop")
    if not sun or not prop:
        return out
    if sun.meters["heat"] < THRESHOLD or prop.meters["protected"] >= THRESHOLD:
        return out
    sig = ("soften", prop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prop.meters["soft"] += 1
    prop.meters["spoiled"] += 1
    out.append("__soft__")
    return out


def _r_soft_prop_hurts(world: World) -> list[str]:
    out: list[str] = []
    prop = world.entities.get("prop")
    helper = world.entities.get("helper")
    actress = world.entities.get("actress")
    if not prop or not helper or not actress:
        return out
    if prop.meters["soft"] < THRESHOLD:
        return out
    sig = ("hurt", prop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["hurt"] += 1
    actress.memes["oops"] += 1
    out.append("__hurt__")
    return out


def _r_apology_cools(world: World) -> list[str]:
    out: list[str] = []
    actress = world.entities.get("actress")
    helper = world.entities.get("helper")
    if not actress or not helper:
        return out
    if actress.memes["apology"] < THRESHOLD:
        return out
    sig = ("cool_feelings", actress.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["hurt"] = 0.0
    helper.memes["warmth"] += 1
    actress.memes["warmth"] += 1
    out.append("__peace__")
    return out


CAUSAL_RULES = [
    Rule(name="heat_softens", tag="physical", apply=_r_heat_softens),
    Rule(name="soft_prop_hurts", tag="social", apply=_r_soft_prop_hurts),
    Rule(name="apology_cools", tag="social", apply=_r_apology_cools),
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


SHOWS = {
    "royal": Show(
        id="royal",
        scene="a crooked cardboard castle beside the tomato pots",
        stage="the backyard stage",
        role_name="Princess Pickle",
        joke_line='"Bow before me! I rule the kingdom of soup!"',
        ending_image="the little castle shook while everybody laughed",
        tags={"play", "comedy"},
    ),
    "detective": Show(
        id="detective",
        scene="a mystery office made from chair cushions and a towel",
        stage="the porch stage",
        role_name="Detective Noodle",
        joke_line='"Aha! The missing pie was stolen by gravity!"',
        ending_image="the chair-cushion office wobbled with giggles",
        tags={"play", "comedy"},
    ),
    "space": Show(
        id="space",
        scene="a moon station made from boxes and silver paper",
        stage="the park blanket stage",
        role_name="Captain Giggle",
        joke_line='"Crew, the moon is made of mashed potatoes!"',
        ending_image="the silver paper moon flashed in the sun while everyone laughed",
        tags={"play", "comedy"},
    ),
}

PROPS = {
    "wax_mustache": PropCfg(
        id="wax_mustache",
        label="wax mustache",
        phrase="a grand curly wax mustache",
        material="wax",
        risk_text="wax goes bendy in strong heat",
        droop_text="one proud curl drooped sadly like a sleepy worm",
        repair_text="they cooled the mustache and pinched the curl back into shape",
        need="shade",
        tags={"mustache", "heat", "wax"},
    ),
    "chocolate_crown": PropCfg(
        id="chocolate_crown",
        label="chocolate crown",
        phrase="a silly chocolate crown wrapped in shiny paper",
        material="chocolate",
        risk_text="chocolate melts in strong heat",
        droop_text="the little points slumped into a shiny brown puddle",
        repair_text="they tucked the crown into the cold pack until it firmed up again",
        need="chill",
        tags={"chocolate", "heat"},
    ),
    "butter_nose": PropCfg(
        id="butter_nose",
        label="butter nose",
        phrase="a fake clown nose molded from cool butter and red crumbs",
        material="butter",
        risk_text="butter slides and softens in strong heat",
        droop_text="the nose sagged sideways and looked as if it wanted a nap",
        repair_text="they cooled the nose and rounded it again with a spoon",
        need="chill",
        tags={"butter", "heat", "clown"},
    ),
}

CONTAINERS = {
    "trunk": ContainerCfg(
        id="trunk",
        label="prop trunk",
        phrase="an old prop trunk with a striped blanket over it",
        sound="something inside gave a tiny thunk-clink sound",
        secret="paper medals for the curtain call",
        tags={"trunk", "curiosity"},
    ),
    "basket": ContainerCfg(
        id="basket",
        label="covered basket",
        phrase="a covered basket with ribbon handles",
        sound="something inside rustled and tapped the lid",
        secret="a bag of lemon candies for the audience",
        tags={"basket", "curiosity"},
    ),
    "cooler": ContainerCfg(
        id="cooler",
        label="striped cooler",
        phrase="a striped cooler with stickers all over it",
        sound="ice inside gave a cheerful chink",
        secret="cold juice boxes for after the play",
        tags={"cooler", "curiosity"},
    ),
}

FIXES = {
    "umbrella": FixCfg(
        id="umbrella",
        label="big umbrella",
        phrase="a big striped umbrella",
        guards={"shade"},
        action_text="opened a big striped umbrella over the stage so the prop could rest in shadow",
        qa_text="put the prop in the shade under a big umbrella",
        tags={"shade", "umbrella"},
    ),
    "fan": FixCfg(
        id="fan",
        label="little fan",
        phrase="a little humming fan",
        guards={"shade"},
        action_text="plugged in a little fan and moved rehearsal into the shadiest corner of the porch",
        qa_text="used a little fan in the shade to cool the prop",
        tags={"fan", "shade"},
    ),
    "ice_pack": FixCfg(
        id="ice_pack",
        label="ice pack",
        phrase="a blue ice pack wrapped in a towel",
        guards={"chill"},
        action_text="wrapped the prop beside a blue ice pack until it turned firm again",
        qa_text="cooled the prop with an ice pack",
        tags={"ice_pack", "cold"},
    ),
    "cooler_fix": FixCfg(
        id="cooler_fix",
        label="cool picnic cooler",
        phrase="a cool picnic cooler with soft towels inside",
        guards={"chill"},
        action_text="settled the prop inside a cool picnic cooler for a little while",
        qa_text="set the prop inside a cool picnic cooler",
        tags={"cooler", "cold"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
HELPER_TRAITS = ["patient", "gentle", "prickly", "dramatic"]


def compatible_fix_ids(prop_id: str) -> list[str]:
    prop = PROPS[prop_id]
    return sorted(fid for fid, fix in FIXES.items() if prop.need in fix.guards)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for show_id in SHOWS:
        for prop_id in PROPS:
            for fix_id in compatible_fix_ids(prop_id):
                combos.append((show_id, prop_id, fix_id))
    return combos


def explain_fix_rejection(prop: PropCfg, fix: FixCfg) -> str:
    return (
        f"(No story: {fix.label} does not honestly solve this problem. "
        f"The {prop.label} needs {prop.need}, but {fix.label} only guards "
        f"{sorted(fix.guards)}.)"
    )


def quick_peace(helper_trait: str) -> bool:
    return helper_trait in PATIENCE_TRAITS


def outcome_of(params: StoryParams) -> str:
    return "shared_laugh" if quick_peace(params.helper_trait) else "guided_reconcile"


def play_setup(world: World, actress: Entity, helper: Entity, show: Show, prop: PropCfg, container: ContainerCfg) -> None:
    actress.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On a blazing afternoon, {actress.id} and {helper.id} built {show.scene}. "
        f"{actress.id} was the star actress, and today {actress.pronoun()} was practicing the part of {show.role_name}."
    )
    world.say(
        f"Beside them sat {container.phrase}. {container.sound.capitalize()}, and that tiny noise made both children glance over."
    )
    world.say(
        f"{helper.id} set out {prop.phrase} and grinned. {actress.id} tried {show.joke_line}"
    )
    world.say(
        f"The line was so silly that even the sparrows seemed ready to laugh."
    )


def foreshadow(world: World, actress: Entity, helper: Entity, prop: PropCfg) -> None:
    world.say(
        f"But the heat was bossy that day. {helper.id} touched the {prop.label} and whispered, "
        f'"We should be careful. {prop.risk_text}."'
    )
    world.say(
        f"For a second, {actress.id} noticed the prop already looked a little softer than before. "
        f"That was the first small warning."
    )


def curiosity_beat(world: World, actress: Entity, helper: Entity, container: ContainerCfg) -> None:
    actress.memes["curiosity"] += 1
    world.say(
        f"{actress.id} tilted {actress.pronoun('possessive')} head toward the {container.label}. "
        f'"What is in there?" {actress.pronoun()} asked. Curiosity tickled {actress.pronoun('object')} harder than a feather.'
    )
    world.say(
        f'"It is the surprise for the ending," said {helper.id}. "Wait until the play is over."'
    )


def peek_and_problem(world: World, actress: Entity, helper: Entity, prop_ent: Entity, prop: PropCfg, container: ContainerCfg) -> None:
    actress.memes["defiance"] += 1
    world.say(
        f"{actress.id} promised to wait, but then the {container.label} made one more interesting little sound."
    )
    world.say(
        f"While {helper.id} was fixing a cardboard door, {actress.id} tiptoed over for a tiny peek and forgot the {prop.label} on a sunny chair."
    )
    propagate(world, narrate=False)
    world.say(
        f"When {helper.id} turned back, the {prop.label} had changed. {prop.droop_text}."
    )


def quarrel(world: World, actress: Entity, helper: Entity, prop: PropCfg) -> None:
    actress.memes["embarrassed"] += 1
    helper.memes["annoyed"] += 1
    world.say(
        f'"Oh no," said {helper.id}. "I warned you." {helper.pronoun().capitalize()} sounded sharp because {helper.pronoun()} had worked hard on the prop.'
    )
    world.say(
        f'{actress.id} felt hot in two ways now: from the weather and from being embarrassed. '
        f'"I only wanted one little look," {actress.pronoun()} said.'
    )


def shared_laugh_reconcile(world: World, actress: Entity, helper: Entity, prop: PropCfg) -> None:
    actress.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then both children stared at the droopy {prop.label}. It looked so ridiculous that a laugh escaped {helper.id}, then another popped out of {actress.id}."
    )
    world.say(
        f'"I am sorry," said {actress.id}. "I was too curious and I forgot the warning."'
    )
    world.say(
        f'"I know," said {helper.id}, smiling at last. "Next time I will explain the surprise instead of sounding snappy."'
    )


def adult_guided_reconcile(world: World, actress: Entity, helper: Entity, adult: Entity, prop: PropCfg) -> None:
    adult.memes["calm"] += 1
    world.say(
        f"{actress.id} and {helper.id} both folded their arms, and the funny play stopped feeling funny."
    )
    world.say(
        f"That was when {adult.label_word.capitalize()} came over with a calm face and looked at the sleepy-looking {prop.label}."
    )
    world.say(
        f'"Two things can be true," {adult.pronoun()} said. "{actress.id} was too curious, and {helper.id} was disappointed because {helper.pronoun()} cared."'
    )
    actress.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{actress.id} took a breath. "I am sorry I ignored the warning," {actress.pronoun()} said.'
    )
    world.say(
        f'"And I am sorry I snapped," said {helper.id}. "I wanted the play to go well."'
    )


def apply_fix(world: World, adult: Entity, prop_ent: Entity, prop: PropCfg, fix: FixCfg) -> None:
    prop_ent.meters["protected"] += 1
    prop_ent.meters["soft"] = 0.0
    world.say(
        f"{adult.label_word.capitalize()} {fix.action_text}."
    )
    world.say(prop.repair_text.capitalize() + ".")


def reveal_secret(world: World, actress: Entity, helper: Entity, container: ContainerCfg) -> None:
    world.say(
        f"Then {helper.id} finally opened the {container.label}. Inside were {container.secret}."
    )
    world.say(
        f'"That was the mystery?" asked {actress.id}. {actress.pronoun().capitalize()} laughed. "I thought it might be a baby dragon."'
    )


def perform(world: World, actress: Entity, helper: Entity, show: Show, prop: PropCfg) -> None:
    actress.memes["joy"] += 1
    helper.memes["joy"] += 1
    actress.memes["reconciled"] += 1
    helper.memes["reconciled"] += 1
    world.say(
        f"When the family audience sat down, {actress.id} marched onto the little stage with the rescued {prop.label} and delivered the line again: {show.joke_line}"
    )
    world.say(
        f"This time {helper.id} rattled the cardboard door at exactly the right moment, the audience laughed so hard they had to wipe their eyes, and {show.ending_image}."
    )


def tell(
    show: Show,
    prop_cfg: PropCfg,
    container_cfg: ContainerCfg,
    fix_cfg: FixCfg,
    actress_name: str = "Mia",
    actress_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    adult_type: str = "mother",
    helper_trait: str = "patient",
) -> World:
    world = World()
    actress = world.add(
        Entity(
            id=actress_name,
            kind="character",
            type=actress_gender,
            role="actress",
            traits=["curious"],
            label=actress_name,
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            traits=[helper_trait],
            label=helper_name,
        )
    )
    adult = world.add(
        Entity(
            id="Adult",
            kind="character",
            type=adult_type,
            role="adult",
            label="the parent",
        )
    )
    sun = world.add(
        Entity(
            id="sun",
            type="weather",
            label="the sun",
        )
    )
    prop_ent = world.add(
        Entity(
            id="prop",
            type="prop",
            label=prop_cfg.label,
            phrase=prop_cfg.phrase,
            heat_sensitive=True,
            need=prop_cfg.need,
            tags=set(prop_cfg.tags),
        )
    )
    world.facts["container_secret"] = container_cfg.secret
    sun.meters["heat"] = 1.0
    play_setup(world, actress, helper, show, prop_cfg, container_cfg)
    foreshadow(world, actress, helper, prop_cfg)

    world.para()
    curiosity_beat(world, actress, helper, container_cfg)
    peek_and_problem(world, actress, helper, prop_ent, prop_cfg, container_cfg)
    quarrel(world, actress, helper, prop_cfg)

    world.para()
    if quick_peace(helper_trait):
        shared_laugh_reconcile(world, actress, helper, prop_cfg)
    else:
        adult_guided_reconcile(world, actress, helper, adult, prop_cfg)
    apply_fix(world, adult, prop_ent, prop_cfg, fix_cfg)
    reveal_secret(world, actress, helper, container_cfg)

    world.para()
    perform(world, actress, helper, show, prop_cfg)

    outcome = "shared_laugh" if quick_peace(helper_trait) else "guided_reconcile"
    world.facts.update(
        show=show,
        prop_cfg=prop_cfg,
        container_cfg=container_cfg,
        fix_cfg=fix_cfg,
        actress=actress,
        helper=helper,
        adult=adult,
        prop=prop_ent,
        heat=True,
        curiosity=actress.memes["curiosity"] >= THRESHOLD,
        softened=prop_ent.meters["spoiled"] >= THRESHOLD,
        reconciled=actress.memes["reconciled"] >= THRESHOLD and helper.memes["reconciled"] >= THRESHOLD,
        outcome=outcome,
        helper_trait=helper_trait,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    actress = f["actress"]
    helper = f["helper"]
    show = f["show"]
    prop_cfg = f["prop_cfg"]
    container = f["container_cfg"]
    outcome = f["outcome"]
    if outcome == "shared_laugh":
        resolution = "the children laugh, apologize, and make up quickly"
    else:
        resolution = "a calm grown-up helps the children apologize and make up"
    return [
        'Write a funny story for a 3-to-5-year-old that includes the words "actress" and "heat".',
        f"Tell a comedy where a child actress named {actress.id} grows curious about a {container.label}, ignores a warning about a {prop_cfg.label}, and {resolution}.",
        f"Write a small stage-play story with foreshadowing, curiosity, and reconciliation, where {helper.id} and {actress.id} save a hot-day rehearsal of {show.role_name}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    actress = f["actress"]
    helper = f["helper"]
    adult = f["adult"]
    show = f["show"]
    prop_cfg = f["prop_cfg"]
    container = f["container_cfg"]
    fix_cfg = f["fix_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {actress.id}, a child actress in a funny little play, and {helper.id}, who helped run the show. "
            f"They were trying to make everyone laugh on a very hot day."
        ),
        (
            "What was the first warning that trouble was coming?",
            f"The first warning was that the heat was already making the {prop_cfg.label} look a little soft. "
            f"That foreshadowed the later problem because {helper.id} had already said {prop_cfg.risk_text}."
        ),
        (
            f"Why did {actress.id} get into trouble?",
            f"{actress.id} was too curious about the {container.label} and went for a peek when {helper.id} was busy. "
            f"Because of that distraction, {actress.pronoun()} forgot the {prop_cfg.label} on a sunny chair, and the heat spoiled it."
        ),
        (
            f"Why were {helper.id}'s feelings hurt?",
            f"{helper.id}'s feelings were hurt because {helper.pronoun()} had worked hard on the {prop_cfg.label} and had already given a warning. "
            f"When the prop drooped anyway, it felt as if the warning had not mattered."
        ),
    ]
    if outcome == "shared_laugh":
        qa.append(
            (
                "How did the children make up?",
                f"They stared at the droopy prop until it looked so silly that they both laughed. "
                f"Then {actress.id} apologized for being too curious, and {helper.id} softened too, so the quarrel turned back into a team-up."
            )
        )
    else:
        qa.append(
            (
                "How did the grown-up help them reconcile?",
                f"{adult.label_word.capitalize()} reminded them that both the mistake and the hurt feelings were real. "
                f"That calm help made room for two apologies, so the children could stop arguing and work together again."
            )
        )
    qa.append(
        (
            f"How did they fix the {prop_cfg.label}?",
            f"They used {fix_cfg.phrase}. {adult.label_word.capitalize()} {fix_cfg.qa_text}, which matched what the prop needed in the heat."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the play going on after the children reconciled. "
            f"The rescued prop worked, the audience laughed, and the funny stage looked happy again."
        )
    )
    return qa


KNOWLEDGE = {
    "heat": [
        (
            "What can heat do to soft things?",
            "Heat can make soft things softer, melty, bendy, or droopy. That is why some snacks and props need shade or something cold."
        )
    ],
    "shade": [
        (
            "Why does shade help on a hot day?",
            "Shade blocks strong sunlight, so things do not warm up as quickly. It helps people and some objects stay cooler."
        )
    ],
    "cold": [
        (
            "Why does an ice pack help cool something down?",
            "An ice pack carries cold to the warm thing touching it. As the warmth moves away, the thing can firm up again."
        )
    ],
    "umbrella": [
        (
            "What does an umbrella do besides keep off rain?",
            "A big umbrella can also make shade on a sunny day. That shade helps protect faces, snacks, and props from strong sun."
        )
    ],
    "fan": [
        (
            "What does a fan do?",
            "A fan moves air around. Moving air can help people feel cooler, especially when they are resting in the shade."
        )
    ],
    "chocolate": [
        (
            "Why does chocolate melt?",
            "Chocolate gets soft when it grows warm. In strong heat, it can melt into a gooey puddle."
        )
    ],
    "wax": [
        (
            "Why can wax bend in the heat?",
            "Wax is firm when it is cooler, but heat makes it softer. That is why a wax shape can droop in the sun."
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to know more. It can lead to good questions, but you still have to listen to warnings."
        )
    ],
    "play": [
        (
            "What does an actress do in a play?",
            "An actress is a person who pretends to be a character in a story. She says lines and acts things out for an audience."
        )
    ],
    "comedy": [
        (
            "What is a comedy?",
            "A comedy is a funny kind of story. It often has silly surprises, laughs, and a happy ending."
        )
    ],
}
KNOWLEDGE_ORDER = ["play", "heat", "shade", "cold", "umbrella", "fan", "chocolate", "wax", "curiosity", "comedy"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"play", "heat", "curiosity", "comedy"}
    tags |= set(f["prop_cfg"].tags)
    tags |= set(f["fix_cfg"].tags)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.need:
            bits.append(f"need={ent.need}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        show="royal",
        prop="wax_mustache",
        container="trunk",
        fix="umbrella",
        actress_name="Mia",
        actress_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        adult="mother",
        helper_trait="patient",
    ),
    StoryParams(
        show="detective",
        prop="chocolate_crown",
        container="cooler",
        fix="ice_pack",
        actress_name="Lily",
        actress_gender="girl",
        helper_name="Tom",
        helper_gender="boy",
        adult="father",
        helper_trait="gentle",
    ),
    StoryParams(
        show="space",
        prop="butter_nose",
        container="basket",
        fix="cooler_fix",
        actress_name="Ava",
        actress_gender="girl",
        helper_name="Max",
        helper_gender="boy",
        adult="mother",
        helper_trait="dramatic",
    ),
    StoryParams(
        show="royal",
        prop="wax_mustache",
        container="basket",
        fix="fan",
        actress_name="Zoe",
        actress_gender="girl",
        helper_name="Leo",
        helper_gender="boy",
        adult="father",
        helper_trait="prickly",
    ),
]


ASP_RULES = r"""
valid(Show, Prop, Fix) :- show(Show), prop(Prop), fix(Fix), needs(Prop, Need), guards(Fix, Need).

quick_peace :- helper_trait(T), patient_trait(T).

outcome(shared_laugh)    :- quick_peace.
outcome(guided_reconcile) :- not quick_peace.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for show_id in SHOWS:
        lines.append(asp.fact("show", show_id))
    for prop_id, prop in PROPS.items():
        lines.append(asp.fact("prop", prop_id))
        lines.append(asp.fact("needs", prop_id, prop.need))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for guard in sorted(fix.guards):
            lines.append(asp.fact("guards", fix_id, guard))
    for trait in sorted(PATIENCE_TRAITS):
        lines.append(asp.fact("patient_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("helper_trait", params.helper_trait)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if mismatches:
        rc = 1
        print(f"MISMATCH in outcomes: {len(mismatches)}/{len(cases)} cases differ.")
    else:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive for batch verification
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child actress, summer heat, curiosity, and a funny reconciliation."
    )
    ap.add_argument("--show", choices=SHOWS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--helper-trait", choices=HELPER_TRAITS)
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prop and args.fix:
        prop = PROPS[args.prop]
        fix = FIXES[args.fix]
        if prop.need not in fix.guards:
            raise StoryError(explain_fix_rejection(prop, fix))

    combos = [
        c for c in valid_combos()
        if (args.show is None or c[0] == args.show)
        and (args.prop is None or c[1] == args.prop)
        and (args.fix is None or c[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    show_id, prop_id, fix_id = rng.choice(sorted(combos))
    actress_gender = "girl"
    helper_gender = rng.choice(["girl", "boy"])
    actress_name = _pick_name(rng, actress_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=actress_name)
    container_id = args.container or rng.choice(sorted(CONTAINERS))
    adult = args.adult or rng.choice(["mother", "father"])
    helper_trait = args.helper_trait or rng.choice(HELPER_TRAITS)
    return StoryParams(
        show=show_id,
        prop=prop_id,
        container=container_id,
        fix=fix_id,
        actress_name=actress_name,
        actress_gender=actress_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        adult=adult,
        helper_trait=helper_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        show = SHOWS[params.show]
        prop = PROPS[params.prop]
        container = CONTAINERS[params.container]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Unknown option in params: {err})") from err

    if prop.need not in fix.guards:
        raise StoryError(explain_fix_rejection(prop, fix))

    world = tell(
        show=show,
        prop_cfg=prop,
        container_cfg=container,
        fix_cfg=fix,
        actress_name=params.actress_name,
        actress_gender=params.actress_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        adult_type=params.adult,
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
        print(f"{len(combos)} compatible (show, prop, fix) combos:\n")
        for show_id, prop_id, fix_id in combos:
            print(f"  {show_id:10} {prop_id:16} {fix_id}")
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
            header = f"### {p.actress_name} & {p.helper_name}: {p.show} with {p.prop} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
