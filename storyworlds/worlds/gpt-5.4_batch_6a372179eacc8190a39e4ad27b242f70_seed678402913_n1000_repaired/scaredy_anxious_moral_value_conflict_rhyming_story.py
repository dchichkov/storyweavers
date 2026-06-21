#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/scaredy_anxious_moral_value_conflict_rhyming_story.py
================================================================================

A standalone story world about a child who is teased for being "scaredy" and
feels anxious when a game turns risky. The conflict is solved by choosing care,
kind words, and a safe way to help.

The style leans toward a child-facing rhyming story: short lyrical sentences,
echoing sounds, and ending images that prove what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/scaredy_anxious_moral_value_conflict_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/scaredy_anxious_moral_value_conflict_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/scaredy_anxious_moral_value_conflict_rhyming_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/scaredy_anxious_moral_value_conflict_rhyming_story.py --qa
    python storyworlds/worlds/gpt-5.4/scaredy_anxious_moral_value_conflict_rhyming_story.py --trace
    python storyworlds/worlds/gpt-5.4/scaredy_anxious_moral_value_conflict_rhyming_story.py --verify
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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "gentle", "thoughtful", "patient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
class Place:
    id: str
    label: str
    opening: str
    breeze: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LostThing:
    id: str
    label: str
    phrase: str
    launch: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Location:
    id: str
    label: str
    phrase: str
    height: int
    rhyme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    unstable: bool = True
    wobble: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    reach: int
    sense: int
    action: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    lost: str
    location: str
    perch: str
    aid: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    relation: str = "friends"
    instigator_age: int = 5
    cautioner_age: int = 5
    trust: int = 5
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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    perch = world.entities.get("perch")
    if perch is None:
        return out
    if perch.meters["loaded"] < THRESHOLD:
        return out
    if not perch.attrs.get("unstable", False):
        return out
    sig = ("wobble", perch.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    perch.meters["wobbling"] += float(perch.attrs.get("wobble", 1))
    if "place" in world.entities:
        world.get("place").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__wobble__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
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


PLACES = {
    "yard": Place(
        id="yard",
        label="the yard",
        opening="In the yard, where clover leaned and bees went by, the afternoon felt wide as sky.",
        breeze="A skipping breeze came whistling through, and made the leaves bow low, then blue.",
        tags={"yard"},
    ),
    "garden": Place(
        id="garden",
        label="the garden",
        opening="In the garden, neat and bright, the petals blinked in specks of light.",
        breeze="A merry breeze went slip and sweep, and woke the roses from their sleep.",
        tags={"garden"},
    ),
    "playground": Place(
        id="playground",
        label="the playground",
        opening="At the playground, under swings that squeaked, the day felt bold and shiny-cheeked.",
        breeze="A playful breeze zipped round the slide and sent small shadows for a ride.",
        tags={"playground"},
    ),
}

LOST_THINGS = {
    "kite": LostThing(
        id="kite",
        label="kite",
        phrase="a red kite with a tail of bows",
        launch="up and away with a flap and flight",
        tags={"kite", "wind"},
    ),
    "hat": LostThing(
        id="hat",
        label="hat",
        phrase="a straw hat with a blue band round",
        launch="off in a twirl with a windy sound",
        tags={"hat", "wind"},
    ),
    "paper_bird": LostThing(
        id="paper_bird",
        label="paper bird",
        phrase="a folded paper bird with painted wings",
        launch="up with a hop and a papery spring",
        tags={"paper", "wind"},
    ),
}

LOCATIONS = {
    "low_branch": Location(
        id="low_branch",
        label="low branch",
        phrase="a low branch in the apple tree",
        height=1,
        rhyme="It trembled there where leaves could sway, so close, yet not for hands at play.",
        tags={"tree"},
    ),
    "high_branch": Location(
        id="high_branch",
        label="high branch",
        phrase="a high branch near the top of the tree",
        height=2,
        rhyme="It clung up high where sparrows peep, above the reach of little feet.",
        tags={"tree", "high"},
    ),
    "gazebo_roof": Location(
        id="gazebo_roof",
        label="gazebo roof",
        phrase="the slanted roof of the little gazebo",
        height=3,
        rhyme="It rested where the shingles shone, too high to claim with hands alone.",
        tags={"roof", "high"},
    ),
}

PERCHES = {
    "stool": Perch(
        id="stool",
        label="stool",
        phrase="a little wobble stool",
        unstable=True,
        wobble=1,
        tags={"stool", "wobble"},
    ),
    "crate": Perch(
        id="crate",
        label="crate",
        phrase="an upside-down crate with shaky slats",
        unstable=True,
        wobble=2,
        tags={"crate", "wobble"},
    ),
    "rolling_chair": Perch(
        id="rolling_chair",
        label="rolling chair",
        phrase="a rolling chair with squeaky wheels",
        unstable=True,
        wobble=3,
        tags={"chair", "wobble"},
    ),
}

AIDS = {
    "long_pole": Aid(
        id="long_pole",
        label="long pole",
        phrase="a long garden pole",
        reach=2,
        sense=3,
        action="used a long garden pole to lift it down",
        qa_text="used a long garden pole to lift it down safely",
        tags={"pole", "ask_help"},
    ),
    "step_ladder": Aid(
        id="step_ladder",
        label="step-ladder",
        phrase="a steady step-ladder",
        reach=3,
        sense=3,
        action="opened a steady step-ladder, climbed carefully, and brought it down",
        qa_text="used a steady step-ladder and brought it down safely",
        tags={"ladder", "ask_help"},
    ),
    "leaf_rake": Aid(
        id="leaf_rake",
        label="leaf rake",
        phrase="a leaf rake with a wide head",
        reach=1,
        sense=2,
        action="hooked it gently with a leaf rake and guided it down",
        qa_text="hooked it gently with a leaf rake and guided it down",
        tags={"rake", "ask_help"},
    ),
    "jump_for_it": Aid(
        id="jump_for_it",
        label="jump for it",
        phrase="no safe tool at all",
        reach=0,
        sense=1,
        action="told them to keep jumping for it",
        qa_text="told them to keep jumping for it",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Ava", "Lucy", "Maya", "Ella", "Ruby"]
BOY_NAMES = ["Ben", "Milo", "Theo", "Sam", "Noah", "Finn", "Eli", "Leo"]
TRAITS = ["careful", "gentle", "thoughtful", "patient", "quiet", "kind"]


def aid_can_reach(aid: Aid, location: Location) -> bool:
    return aid.reach >= location.height


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id in PLACES:
        for lost_id in LOST_THINGS:
            for loc_id, loc in LOCATIONS.items():
                for perch_id, perch in PERCHES.items():
                    if not perch.unstable:
                        continue
                    for aid_id, aid in AIDS.items():
                        if aid.sense >= SENSE_MIN and aid_can_reach(aid, loc):
                            combos.append((place_id, lost_id, loc_id, perch_id, aid_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str, trust: int) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + (2.0 if cautioner_older else 0.0) + (1.0 if trust <= 4 else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def explain_rejection(location: Location, aid: Aid) -> str:
    if aid.sense < SENSE_MIN:
        better = ", ".join(sorted(a.id for a in AIDS.values() if a.sense >= SENSE_MIN))
        return (
            f"(Refusing aid '{aid.id}': it scores too low on common sense "
            f"(sense={aid.sense} < {SENSE_MIN}). Try a safer helper tool such as {better}.)"
        )
    return (
        f"(No story: {aid.label} cannot reasonably reach {location.phrase}. "
        f"Pick a tool that can reach that height.)"
    )


def predict_wobble(world: World) -> dict:
    sim = world.copy()
    perch = sim.get("perch")
    perch.meters["loaded"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("perch").meters["wobbling"],
        "danger": sim.get("place").meters["danger"],
    }


def play_setup(world: World, place: Place, a: Entity, b: Entity, lost: LostThing) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(place.opening)
    world.say(
        f"{a.id} and {b.id} ran in loops and whoops, chasing {lost.phrase} through skips and swoops."
    )
    world.say(place.breeze)


def loss(world: World, lost: LostThing, location: Location) -> None:
    world.get("lost").meters["stuck"] += 1
    world.say(
        f"Then the {lost.label} flew {lost.launch}, and landed on {location.phrase}. {location.rhyme}"
    )


def tempt(world: World, a: Entity, perch: Perch, location: Location) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"I can get it in a tick," said {a.id}. {a.pronoun().capitalize()} dragged over {perch.phrase} '
        f'and pointed up at the {location.label}.'
    )


def warn(world: World, b: Entity, a: Entity, parent: Entity, perch: Perch) -> None:
    pred = predict_wobble(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_danger"] = pred["danger"]
    b.memes["anxiety"] += 1
    world.say(
        f'{b.id} felt anxious clear to {b.pronoun("possessive")} toes. '
        f'"Please don\'t climb that {perch.label}," {b.pronoun()} said. '
        f'"It will wobble, and {parent.label_word} can help us instead."'
    )


def taunt(world: World, a: Entity, b: Entity) -> None:
    a.memes["tease"] += 1
    b.memes["hurt"] += 1
    world.say(
        f'"Don\'t be such a scaredy thing," said {a.id}, with a sharp little sting. '
        f'The words were unkind, and they made {b.id} shrink small.'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["defiance"] = 0.0
    a.memes["reflection"] += 1
    b.memes["relief"] += 1
    world.say(
        f"But {b.id} stood steady instead of mean, and the quiet in {b.pronoun('possessive')} face was plainly seen."
    )
    world.say(
        f"{a.id} looked at the perch, then down at the ground, and the brave-sounding boast lost its noisy sound."
    )
    world.say(
        f'"You are right," {a.pronoun()} said at last. "Let\'s get {parent.label_word} and not climb fast."'
    )


def climb_and_wobble(world: World, a: Entity, perch: Entity) -> None:
    perch.meters["loaded"] += 1
    a.meters["up_high"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{a.id} stepped onto the {perch.label}. It gave a creak and a squeak and a side-to-side sway."
    )
    if perch.meters["wobbling"] >= THRESHOLD:
        world.say(
            f"The {perch.label} wobbled and bobbled in a risky way, and the game stopped feeling fun to play."
        )


def alarm(world: World, b: Entity, parent: Entity, a: Entity) -> None:
    b.memes["care"] += 1
    world.say(
        f'"{parent.label_word.capitalize()}!" cried {b.id}. "{a.id} is too high!" '
        f'Calling for help was the bravest cry.'
    )


def rescue(world: World, parent: Entity, aid: Aid, a: Entity, lost: LostThing) -> None:
    world.get("lost").meters["stuck"] = 0.0
    world.get("place").meters["danger"] = 0.0
    world.get("perch").meters["loaded"] = 0.0
    a.meters["up_high"] = 0.0
    a.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came quickly, calm and light, and {aid.action}. "
        f'Soon the {lost.label} was safe in sight.'
    )


def lesson(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["kindness"] += 1
    b.memes["relief"] += 1
    b.memes["worth"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them there and said, '
        f'"Being careful is wise, not something to dread."'
    )
    world.say(
        f'"And calling someone scaredy to make them small is not brave talk at all."'
    )
    world.say(
        f'{a.id} looked at {b.id} and whispered, "I was wrong. I used a teasing, hurtful song."'
    )


def ending(world: World, a: Entity, b: Entity, lost: LostThing) -> None:
    a.memes["love"] += 1
    b.memes["love"] += 1
    world.say(
        f'{b.id} smiled a little, and {a.id} held out the {lost.label}. "Next time," {a.pronoun()} said, '
        f'"we choose safe help instead."'
    )
    world.say(
        f"So side by side, with kinder hearts in view, they ran again beneath the blue. "
        f"Their play was bright, their voices soft, and not one mean word drifted off."
    )


def tell(
    place: Place,
    lost_cfg: LostThing,
    location: Location,
    perch_cfg: Perch,
    aid_cfg: Aid,
    instigator: str = "Ben",
    instigator_gender: str = "boy",
    cautioner: str = "Lila",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    relation: str = "friends",
    instigator_age: int = 5,
    cautioner_age: int = 5,
    trust: int = 5,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation, "trust": trust},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    place_ent = world.add(Entity(id="place", type="place", label=place.label, tags=set(place.tags)))
    lost_ent = world.add(Entity(id="lost", type="thing", label=lost_cfg.label, phrase=lost_cfg.phrase, tags=set(lost_cfg.tags)))
    perch_ent = world.add(Entity(
        id="perch",
        type="perch",
        label=perch_cfg.label,
        phrase=perch_cfg.phrase,
        tags=set(perch_cfg.tags),
        attrs={"unstable": perch_cfg.unstable, "wobble": perch_cfg.wobble},
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)

    play_setup(world, place, a, b, lost_cfg)
    loss(world, lost_cfg, location)

    world.para()
    tempt(world, a, perch_cfg, location)
    warn(world, b, a, parent, perch_cfg)
    taunt(world, a, b)

    averted = would_avert(relation, instigator_age, cautioner_age, trait, trust)
    if averted:
        back_down(world, a, b, parent)
        world.para()
        rescue(world, parent, aid_cfg, a, lost_cfg)
        lesson(world, a, b, parent)
        ending(world, a, b, lost_cfg)
    else:
        world.para()
        climb_and_wobble(world, a, perch_ent)
        alarm(world, b, parent, a)
        world.para()
        rescue(world, parent, aid_cfg, a, lost_cfg)
        lesson(world, a, b, parent)
        ending(world, a, b, lost_cfg)

    outcome = "averted" if averted else "wobbled"
    world.facts.update(
        place=place,
        lost_cfg=lost_cfg,
        location=location,
        perch_cfg=perch_cfg,
        aid=aid_cfg,
        instigator=a,
        cautioner=b,
        parent=parent,
        outcome=outcome,
        relation=relation,
        predicted_danger=world.facts.get("predicted_danger", 0),
        taunt_used=a.memes["tease"] >= THRESHOLD,
        wobble_happened=perch_ent.meters["wobbling"] >= THRESHOLD,
        apologized=a.memes["kindness"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "kite": [(
        "What is a kite?",
        "A kite is a light frame covered with paper or cloth that can fly in the wind on a string."
    )],
    "hat": [(
        "Why can the wind blow a hat away?",
        "A hat is light, so a gust of wind can lift it or push it if it is not held on tightly."
    )],
    "paper": [(
        "Why does paper fly so easily?",
        "Paper is light and thin, so moving air can push it up and carry it along."
    )],
    "wind": [(
        "What is wind?",
        "Wind is moving air. You cannot see it by itself, but you can see leaves, kites, and clothes move when it blows."
    )],
    "tree": [(
        "Why is climbing for a stuck thing risky?",
        "Something stuck in a tree can make children want to reach too high. If they climb on something shaky, they can fall."
    )],
    "roof": [(
        "Why should children not climb onto a roof?",
        "Roofs are high and slippery, and a child could fall badly. A grown-up should handle things that are stuck up there."
    )],
    "ladder": [(
        "What is a ladder for?",
        "A ladder helps a grown-up reach high places more safely. It needs steady feet and careful climbing."
    )],
    "pole": [(
        "What can a long pole do?",
        "A long pole can reach something above your hands and nudge it down without climbing."
    )],
    "rake": [(
        "How can a rake help?",
        "A rake can sometimes hook a light object that is only a little bit out of reach and guide it down."
    )],
    "ask_help": [(
        "Why is asking a grown-up for help brave?",
        "Asking for help is brave because it means you care more about safety than showing off. It is a smart choice when something feels risky."
    )],
    "kindness": [(
        "Why is it hurtful to call someone 'scaredy'?",
        "That word can make someone feel small for trying to be careful. Kind words help people speak up when something seems unsafe."
    )],
}
KNOWLEDGE_ORDER = ["kite", "hat", "paper", "wind", "tree", "roof", "ladder", "pole", "rake", "ask_help", "kindness"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    lost = f["lost_cfg"]
    loc = f["location"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a rhyming story for a 3-to-5-year-old that includes the words "scaredy" and "anxious", where a child wants to climb for a {lost.label} but another child stops the risky plan.',
            f"Tell a gentle moral-value story in rhyme where {b.id} feels anxious, is teased as scaredy, yet stays calm and helps {a.id} choose the safe way.",
            f"Write a conflict story in couplet-like prose where a stuck {lost.label} causes an argument, but kindness and asking for help win in the end.",
        ]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the words "scaredy" and "anxious", where a child climbs for a stuck {lost.label} and a grown-up helps safely.',
        f"Tell a child-facing conflict story in rhyme where {a.id} teases {b.id} as scaredy, the perch wobbles, and the lesson is that careful words and safe choices matter.",
        f"Write a moral-value story with a clear turn: a risky climb, an anxious warning, and a safe rescue that ends with an apology.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    lost = f["lost_cfg"]
    loc = f["location"]
    perch = f["perch_cfg"]
    aid = f["aid"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, and {a.id}'s {parent.label_word} who helps at the risky moment."
        ),
        (
            f"What got stuck, and where did it land?",
            f"The {lost.label} got blown away and landed on {loc.phrase}. That is what started the problem."
        ),
        (
            f"Why did {b.id} feel anxious?",
            f"{b.id} felt anxious because {a.id} wanted to climb on {perch.phrase} to reach the {lost.label}. {b.pronoun().capitalize()} could tell the perch would wobble and someone might fall."
        ),
        (
            f"What unkind word did {a.id} use?",
            f"{a.id} called {b.id} scaredy. That was hurtful because {b.id} was trying to keep everyone safe, not spoil the game."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What changed {a.id}'s mind?",
            f"{a.id} saw that {b.id} stayed calm and serious instead of teasing back. That helped {a.pronoun()} realize the climb was not worth the risk."
        ))
    else:
        qa.append((
            f"What happened when {a.id} climbed up?",
            f"The {perch.label} wobbled under {a.id}. The game stopped feeling fun because the danger had become real."
        ))
    qa.append((
        f"How did {parent.label_word} solve the problem?",
        f"{parent.label_word.capitalize()} {aid.qa_text}. The grown-up used a safer method than climbing on the shaky perch."
    ))
    qa.append((
        "What is the moral of the story?",
        f"The story teaches that asking for help and being careful can be brave. It also teaches that calling someone scaredy for speaking up is unkind."
    ))
    qa.append((
        "How did the story end?",
        f"It ended with the children together again, using kinder words and safer choices. The ending image shows that their play felt light and happy after the apology."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["lost_cfg"].tags) | set(f["location"].tags) | set(f["aid"].tags) | {"kindness"}
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="yard",
        lost="kite",
        location="high_branch",
        perch="crate",
        aid="step_ladder",
        instigator="Ben",
        instigator_gender="boy",
        cautioner="Lila",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        relation="friends",
        instigator_age=6,
        cautioner_age=5,
        trust=6,
    ),
    StoryParams(
        place="garden",
        lost="hat",
        location="low_branch",
        perch="stool",
        aid="leaf_rake",
        instigator="Mina",
        instigator_gender="girl",
        cautioner="Theo",
        cautioner_gender="boy",
        parent="father",
        trait="gentle",
        relation="siblings",
        instigator_age=4,
        cautioner_age=7,
        trust=3,
    ),
    StoryParams(
        place="playground",
        lost="paper_bird",
        location="gazebo_roof",
        perch="rolling_chair",
        aid="step_ladder",
        instigator="Noah",
        instigator_gender="boy",
        cautioner="Ruby",
        cautioner_gender="girl",
        parent="father",
        trait="thoughtful",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
        trust=4,
    ),
    StoryParams(
        place="yard",
        lost="hat",
        location="high_branch",
        perch="stool",
        aid="long_pole",
        instigator="Ella",
        instigator_gender="girl",
        cautioner="Maya",
        cautioner_gender="girl",
        parent="mother",
        trait="patient",
        relation="siblings",
        instigator_age=5,
        cautioner_age=8,
        trust=2,
    ),
]


ASP_RULES = r"""
sensible(A) :- aid(A), sense(A, S), sense_min(M), S >= M.
reachable(A, L) :- aid(A), location(L), reach(A, R), height(L, H), R >= H.
valid(P, Lost, L, Perch, A) :- place(P), lost(Lost), location(L), perch(Perch),
                               unstable(Perch), sensible(A), reachable(A, L).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
trust_bonus(1) :- trust(T), T <= 4.
trust_bonus(0) :- trust(T), T > 4.
age_bonus(2) :- older_sibling.
age_bonus(0) :- not older_sibling.
authority(C + A + T) :- init_caution(C), age_bonus(A), trust_bonus(T).
averted :- older_sibling, authority(X), bravery_init(B), X > B.

outcome(averted) :- averted.
outcome(wobbled) :- not averted.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for lid in LOST_THINGS:
        lines.append(asp.fact("lost", lid))
    for loc_id, loc in LOCATIONS.items():
        lines.append(asp.fact("location", loc_id))
        lines.append(asp.fact("height", loc_id, loc.height))
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        if perch.unstable:
            lines.append(asp.fact("unstable", perch_id))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("reach", aid_id, aid.reach))
        lines.append(asp.fact("sense", aid_id, aid.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
        asp.fact("trust", params.trust),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(
        params.relation, params.instigator_age, params.cautioner_age, params.trait, params.trust
    ) else "wobbled"


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

    c_sens = set(asp_sensible())
    p_sens = {aid.id for aid in AIDS.values() if aid.sense >= SENSE_MIN}
    if c_sens == p_sens:
        print(f"OK: sensible aids match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible aids: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for s in range(80):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    mismatches = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        emit(sample, trace=False, qa=False)
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a risky climb, anxious warning, and a kinder safer choice. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--lost", choices=LOST_THINGS)
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.aid and args.location:
        aid = AIDS[args.aid]
        location = LOCATIONS[args.location]
        if aid.sense < SENSE_MIN or not aid_can_reach(aid, location):
            raise StoryError(explain_rejection(location, aid))
    if args.aid and args.aid in AIDS and AIDS[args.aid].sense < SENSE_MIN:
        raise StoryError(explain_rejection(LOCATIONS[args.location] if args.location else next(iter(LOCATIONS.values())), AIDS[args.aid]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.lost is None or c[1] == args.lost)
        and (args.location is None or c[2] == args.location)
        and (args.perch is None or c[3] == args.perch)
        and (args.aid is None or c[4] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, lost_id, location_id, perch_id, aid_id = rng.choice(sorted(combos))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["friends", "siblings"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7, 8], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        place=place_id,
        lost=lost_id,
        location=location_id,
        perch=perch_id,
        aid=aid_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        lost = LOST_THINGS[params.lost]
        location = LOCATIONS[params.location]
        perch = PERCHES[params.perch]
        aid = AIDS[params.aid]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})")

    if aid.sense < SENSE_MIN or not aid_can_reach(aid, location):
        raise StoryError(explain_rejection(location, aid))

    world = tell(
        place=place,
        lost_cfg=lost,
        location=location,
        perch_cfg=perch,
        aid_cfg=aid,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        trust=params.trust,
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
        print(asp_program("", "#show valid/5.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible aids: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, lost, location, perch, aid) combos:\n")
        for combo in combos:
            print("  " + " ".join(combo))
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
            header = (
                f"### {p.instigator} & {p.cautioner}: {p.lost} at {p.location} "
                f"({p.perch}, {p.aid}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
