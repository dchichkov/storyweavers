#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/drown_depiction_quest_dialogue_comedy.py
===================================================================

A small storyworld about a child on a silly quest. A funny clue with a
"depiction" leads to a runaway object near water; the child is tempted to lean
too far, a helper warns that someone or something might "drown", and a sensible
grown-up uses the right tool to save the day.

The domain is intentionally narrow. It prefers a few plausible, funny stories
over a wide but weak combination space.

Run it
------
    python storyworlds/worlds/gpt-5.4/drown_depiction_quest_dialogue_comedy.py
    python storyworlds/worlds/gpt-5.4/drown_depiction_quest_dialogue_comedy.py --all
    python storyworlds/worlds/gpt-5.4/drown_depiction_quest_dialogue_comedy.py --place fountain
    python storyworlds/worlds/gpt-5.4/drown_depiction_quest_dialogue_comedy.py --thing brick
    python storyworlds/worlds/gpt-5.4/drown_depiction_quest_dialogue_comedy.py --verify
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    edge: str
    water: str
    drift: int
    splash: str
    crowd_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    funny_name: str
    floats: bool
    washable: bool
    clue_depiction: str
    ending_pose: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    reach: int
    sense: int
    rescue_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    waterproof: bool
    funny_line: str
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


def _r_wet_clue(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    if clue.meters["in_water"] < THRESHOLD:
        return out
    if clue.attrs.get("waterproof"):
        return out
    sig = ("wet_clue", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.meters["soggy"] += 1
    out.append("__soggy__")
    return out


def _r_lean_risk(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["leaning"] < THRESHOLD:
        return out
    sig = ("lean_risk", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["slip_risk"] += 1
    hero.memes["worry"] += 1
    out.append("__risk__")
    return out


def _r_rescue_relief(world: World) -> list[str]:
    out: list[str] = []
    thing = world.get("thing")
    if thing.meters["rescued"] < THRESHOLD:
        return out
    sig = ("rescue_relief", thing.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("hero", "friend"):
        world.get(eid).memes["relief"] += 1
        world.get(eid).memes["joy"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="wet_clue", tag="physical", apply=_r_wet_clue),
    Rule(name="lean_risk", tag="physical", apply=_r_lean_risk),
    Rule(name="rescue_relief", tag="emotional", apply=_r_rescue_relief),
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
                produced.extend(sents)
    return produced


def hazard_possible(place: Place, thing: Thing) -> bool:
    return thing.floats


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def can_rescue(place: Place, tool: Tool) -> bool:
    return tool.reach >= place.drift and tool.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for thing_id, thing in THINGS.items():
            if not hazard_possible(place, thing):
                continue
            for tool_id, tool in TOOLS.items():
                if can_rescue(place, tool):
                    combos.append((place_id, thing_id, tool_id))
    return combos


def explain_rejection(place: Place, thing: Thing, tool: Tool) -> str:
    if not thing.floats:
        return (
            f"(No story: {thing.phrase} would sink in {place.water}, so the comic rescue "
            f"quest collapses into a grim problem. Pick something that floats.)"
        )
    if tool.sense < SENSE_MIN:
        return (
            f"(Refusing tool '{tool.id}': it scores too low on common sense "
            f"(sense={tool.sense} < {SENSE_MIN}). Try a net, a grabber, or a rake.)"
        )
    if tool.reach < place.drift:
        return (
            f"(No story: {tool.phrase} is too short to reach safely across {place.label}. "
            f"Pick a longer tool.)"
        )
    return "(No valid combination matches the given options.)"


def predict_trouble(place: Place, clue: Clue) -> dict:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type="girl"))
    world.add(Entity(id="friend", kind="character", type="boy"))
    clue_ent = world.add(Entity(id="clue", type="clue", label=clue.label, attrs={"waterproof": clue.waterproof}))
    world.add(Entity(id="thing", type="thing"))
    hero.meters["leaning"] += 1
    clue_ent.meters["in_water"] += 1
    propagate(world, narrate=False)
    return {
        "slip_risk": hero.meters["slip_risk"],
        "soggy": clue_ent.meters["soggy"],
    }


def open_quest(world: World, hero: Entity, friend: Entity, clue: Clue, thing: Thing, place: Place) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On Saturday morning, {hero.id} and {friend.id} began a grand quest at {place.label}. "
        f"{hero.id} carried {clue.phrase} with a wobbly depiction of {thing.funny_name}, "
        f"drawn so proudly that even the eyebrows looked surprised."
    )
    world.say(
        f'"The map says the brave prize is near {place.edge}," {hero.id} said. '
        f'"Also, the map says {clue.funny_line}," {friend.id} added.'
    )


def find_trouble(world: World, hero: Entity, friend: Entity, clue: Clue, thing: Thing, place: Place) -> None:
    thing_ent = world.get("thing")
    clue_ent = world.get("clue")
    thing_ent.meters["in_water"] += 1
    clue_ent.meters["in_water"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They found {thing.phrase} at once, but it was bobbing in {place.water} instead of waiting on the ground. "
        f"A puff of wind flipped the clue from {hero.id}'s hand, and the paper skated after it."
    )
    if clue_ent.meters["soggy"] >= THRESHOLD:
        world.say(
            f'"Oh no," {friend.id} said. "The depiction is getting all squishy."'
        )
    else:
        world.say(
            f'"At least the clue can swim," {friend.id} said.'
        )
    world.facts["clue_soggy"] = clue_ent.meters["soggy"] >= THRESHOLD


def lean_too_far(world: World, hero: Entity, friend: Entity, place: Place, thing: Thing) -> None:
    hero.meters["leaning"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} bent over {place.edge} and stretched one hand farther and farther. '
        f'"If {thing.funny_name} floats away, this quest will be a tragedy with wet socks," {hero.id} said.'
    )
    if hero.meters["slip_risk"] >= THRESHOLD:
        world.say(
            f'"Do not lean like that!" {friend.id} yelped. "You will fall in, and your shoes might drown before you do!"'
        )
    world.facts["leaned"] = True


def adult_arrives(world: World, grownup: Entity, place: Place) -> None:
    world.say(
        f"A nearby {grownup.label_word} looked up from {place.crowd_line} and hurried over."
    )


def rescue(world: World, grownup: Entity, tool: Tool, thing: Thing, clue: Clue) -> None:
    thing_ent = world.get("thing")
    clue_ent = world.get("clue")
    thing_ent.meters["rescued"] += 1
    thing_ent.meters["in_water"] = 0.0
    clue_ent.meters["in_water"] = 0.0
    world.get("hero").meters["leaning"] = 0.0
    world.get("hero").meters["slip_risk"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f'{grownup.label_word.capitalize()} grabbed {tool.phrase} and {tool.rescue_text}. '
        f'"A quest is better with a plan than with a splash," {grownup.pronoun()} said.'
    )
    if clue.waterproof:
        world.say(
            f"The clue came back only damp at the corners, and its depiction still looked proudly ridiculous."
        )
    else:
        world.say(
            f"The clue came back soft and curling, but the depiction could still be understood, mostly because the eyebrows were somehow even bigger now."
        )
    world.facts["rescued_with"] = tool.id


def finish_quest(world: World, hero: Entity, friend: Entity, thing: Thing, clue: Clue, place: Place) -> None:
    hero.memes["pride"] += 1
    friend.memes["pride"] += 1
    clue_ent = world.get("clue")
    soggy = clue_ent.meters["soggy"] >= THRESHOLD
    world.say(
        f'"We did it," {hero.id} said. "{thing.funny_name} has been saved from a terrible life as fountain treasure."'
    )
    if soggy:
        world.say(
            f'"And the depiction survived too," {friend.id} said. "It looks funnier now, which I think means better."'
        )
    else:
        world.say(
            f'"And the depiction survived too," {friend.id} said. "It still looks exactly as silly as before."'
        )
    world.say(
        f"They marched away from {place.label} with {thing.phrase} held high, laughing so hard that the whole quest sounded less like a battle cry and more like hiccups."
    )


def tell(
    place: Place,
    thing: Thing,
    tool: Tool,
    clue: Clue,
    hero_name: str = "Nina",
    hero_type: str = "girl",
    friend_name: str = "Otis",
    friend_type: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    grownup = world.add(Entity(id="Parent", kind="character", type=parent_type, role="grownup", label="the parent"))
    clue_ent = world.add(
        Entity(id="clue", type="clue", label=clue.label, phrase=clue.phrase, attrs={"waterproof": clue.waterproof})
    )
    thing_ent = world.add(
        Entity(id="thing", type="thing", label=thing.label, phrase=thing.phrase, attrs={"floats": thing.floats})
    )

    open_quest(world, hero, friend, clue, thing, place)
    world.para()
    find_trouble(world, hero, friend, clue, thing, place)
    lean_too_far(world, hero, friend, place, thing)
    world.para()
    adult_arrives(world, grownup, place)
    rescue(world, grownup, tool, thing, clue)
    finish_quest(world, hero, friend, thing, clue, place)

    world.facts.update(
        hero=hero,
        friend=friend,
        grownup=grownup,
        place=place,
        thing_cfg=thing,
        clue_cfg=clue,
        tool_cfg=tool,
        clue_soggy=world.get("clue").meters["soggy"] >= THRESHOLD,
        safe_end=world.get("thing").meters["rescued"] >= THRESHOLD,
        prediction=predict_trouble(place, clue),
    )
    return world


PLACES = {
    "fountain": Place(
        id="fountain",
        label="the town fountain",
        edge="the stone rim",
        water="the bright fountain pool",
        drift=2,
        splash="cold silver splashes",
        crowd_line="a bench beside the pigeons",
        tags={"water", "fountain"},
    ),
    "pond": Place(
        id="pond",
        label="the duck pond",
        edge="the wobbly wooden rail",
        water="the green duck pond",
        drift=3,
        splash="little green ripples",
        crowd_line="a path full of bread crumbs and duck gossip",
        tags={"water", "pond", "ducks"},
    ),
    "canal": Place(
        id="canal",
        label="the little canal bridge",
        edge="the low brick wall",
        water="the slow canal",
        drift=2,
        splash="long sleepy ripples",
        crowd_line="a flower stall at the corner",
        tags={"water", "canal"},
    ),
}

THINGS = {
    "crown": Thing(
        id="crown",
        label="toy crown",
        phrase="a toy crown with three tin bells",
        funny_name="King Jingle",
        floats=True,
        washable=True,
        clue_depiction="a crooked crown with giant eyebrows",
        ending_pose="tilted like it knew a joke",
        tags={"crown", "float"},
    ),
    "chicken": Thing(
        id="chicken",
        label="rubber chicken",
        phrase="a rubber chicken wearing a paper tie",
        funny_name="Sir Honks-a-Lot",
        floats=True,
        washable=True,
        clue_depiction="a heroic chicken with a cape",
        ending_pose="pointing its beak at the clouds",
        tags={"chicken", "float"},
    ),
    "boat": Thing(
        id="boat",
        label="paper boat",
        phrase="a paper boat with a star sticker on the nose",
        funny_name="Captain Fold",
        floats=True,
        washable=False,
        clue_depiction="a brave boat on dramatic waves",
        ending_pose="crinkled but proud",
        tags={"boat", "float", "paper"},
    ),
    "brick": Thing(
        id="brick",
        label="painted brick",
        phrase="a painted brick with googly eyes",
        funny_name="Baron Brickles",
        floats=False,
        washable=True,
        clue_depiction="a block with a mustache",
        ending_pose="sulking at the bottom",
        tags={"brick"},
    ),
}

TOOLS = {
    "net": Tool(
        id="net",
        label="pond net",
        phrase="a long pond net",
        reach=3,
        sense=3,
        rescue_text="scooped up both the runaway prize and the clue in one neat sweep",
        qa_text="used a long pond net to scoop the object and the clue out of the water",
        tags={"net", "rescue"},
    ),
    "grabber": Tool(
        id="grabber",
        label="litter grabber",
        phrase="a litter grabber with orange handles",
        reach=2,
        sense=3,
        rescue_text="pinched the clue first and then hooked the prize back to the edge",
        qa_text="used a litter grabber to pinch the clue and pull the prize back",
        tags={"grabber", "rescue"},
    ),
    "rake": Tool(
        id="rake",
        label="leaf rake",
        phrase="a leaf rake",
        reach=2,
        sense=2,
        rescue_text="dragged the floating prize gently closer and lifted the clue out by a dry corner",
        qa_text="used a leaf rake to drag the floating object close and lift the clue out",
        tags={"rake", "rescue"},
    ),
    "spoon": Tool(
        id="spoon",
        label="wooden spoon",
        phrase="a wooden spoon from a lunch bag",
        reach=1,
        sense=1,
        rescue_text="poked at the water hopefully",
        qa_text="poked at the water with a spoon",
        tags={"spoon"},
    ),
}

CLUES = {
    "poster": Clue(
        id="poster",
        label="poster",
        phrase="a folded poster",
        waterproof=False,
        funny_line="Beware of geese with opinions",
        tags={"paper", "depiction"},
    ),
    "menu": Clue(
        id="menu",
        label="menu",
        phrase="a café menu with arrows drawn on the back",
        waterproof=False,
        funny_line="Treasure may smell faintly of ketchup",
        tags={"paper", "depiction"},
    ),
    "laminated": Clue(
        id="laminated",
        label="card",
        phrase="a laminated clue card",
        waterproof=True,
        funny_line="Heroes should not step in anything quacking",
        tags={"card", "depiction"},
    ),
}

GIRL_NAMES = ["Nina", "Molly", "Ava", "Zoe", "Mira", "Lila"]
BOY_NAMES = ["Otis", "Ben", "Milo", "Theo", "Finn", "Jasper"]


@dataclass
class StoryParams:
    place: str
    thing: str
    tool: str
    clue: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="fountain",
        thing="crown",
        tool="grabber",
        clue="poster",
        hero_name="Nina",
        hero_gender="girl",
        friend_name="Otis",
        friend_gender="boy",
        parent="mother",
    ),
    StoryParams(
        place="pond",
        thing="chicken",
        tool="net",
        clue="laminated",
        hero_name="Molly",
        hero_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        parent="father",
    ),
    StoryParams(
        place="canal",
        thing="boat",
        tool="rake",
        clue="menu",
        hero_name="Ben",
        hero_gender="boy",
        friend_name="Lila",
        friend_gender="girl",
        parent="mother",
    ),
]


KNOWLEDGE = {
    "depiction": [
        (
            "What is a depiction?",
            "A depiction is a picture or drawing that shows what something looks like. It can be silly or careful, but it is meant to help you see the idea."
        )
    ],
    "drown": [
        (
            "What does drown mean?",
            "Drown means going under water and not being able to breathe. That is why children should stay back from deep water and ask a grown-up for help."
        )
    ],
    "net": [
        (
            "What is a pond net for?",
            "A pond net is a long tool with a mesh end that can scoop things from water. It lets a grown-up reach farther without leaning in."
        )
    ],
    "grabber": [
        (
            "What is a litter grabber?",
            "A litter grabber is a long-handled tool that can pinch and pick things up. It helps someone reach safely without using their hands."
        )
    ],
    "rake": [
        (
            "How can a rake help near water?",
            "A rake can pull a floating thing closer if it is used gently. A grown-up can keep both feet safe on the ground while using it."
        )
    ],
    "water": [
        (
            "Why is leaning over water risky?",
            "Leaning too far can make you lose your balance. Even a small slip can turn a joke into a dangerous fall."
        )
    ],
}
KNOWLEDGE_ORDER = ["depiction", "drown", "water", "net", "grabber", "rake"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    place = f["place"]
    thing = f["thing_cfg"]
    return [
        f'Write a funny quest story for a 3-to-5-year-old that includes the words "drown" and "depiction".',
        f"Tell a comedy about {hero.id} and {friend.id} trying to rescue {thing.phrase} from {place.label}, with lots of dialogue and a safe grown-up solution.",
        f"Write a playful story where a clue with a silly depiction starts a quest, the children talk back and forth, and the ending proves they learned not to lean over water.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    grownup = f["grownup"]
    place = f["place"]
    thing = f["thing_cfg"]
    clue = f["clue_cfg"]
    tool = f["tool_cfg"]
    soggy = f["clue_soggy"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two children on a silly quest, and {hero.id}'s {grownup.label_word} who helped them at the water."
        ),
        (
            "What started the quest?",
            f"The quest started with {clue.phrase} that had a funny depiction of {thing.funny_name}. The picture made them treat the search like a grand adventure."
        ),
        (
            f"Why did {friend.id} warn {hero.id} not to lean so far?",
            f"{friend.id} saw that {hero.id} was bending over {place.edge} to reach the floating prize. {friend.pronoun('subject').capitalize()} was afraid {hero.id} might slip into the water, which is why the word 'drown' came up in the warning."
        ),
        (
            f"How did the grown-up solve the problem?",
            f"{grownup.label_word.capitalize()} {tool.qa_text}. That worked because the tool was long enough to reach the drifting object without anyone leaning into the water."
        ),
    ]
    if soggy:
        qa.append(
            (
                "What happened to the clue?",
                f"The clue got soggy because it fell into the water before the rescue. Even so, the depiction still helped because the funny drawing was clear enough to recognize."
            )
        )
    else:
        qa.append(
            (
                "What happened to the clue?",
                f"The clue came back only a little damp and stayed readable. Its waterproof material kept the depiction from turning into a mushy blur."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended happily and foolishly: the quest prize was safe, the children were dry, and they marched away laughing. The final image shows that they finished the adventure with a tool and a plan instead of risky leaning."
        )
    )
    return qa


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"depiction", "drown", "water"} | set(f["tool_cfg"].tags)
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(P, T) :- place(P), thing(T), floats(T).
sensible_tool(R) :- tool(R), sense(R, S), sense_min(M), S >= M.
can_rescue(P, R) :- place(P), tool(R), drift(P, D), reach(R, X), X >= D, sensible_tool(R).
valid(P, T, R) :- hazard(P, T), can_rescue(P, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("drift", place_id, place.drift))
    for thing_id, thing in THINGS.items():
        lines.append(asp.fact("thing", thing_id))
        if thing.floats:
            lines.append(asp.fact("floats", thing_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("reach", tool_id, tool.reach))
        lines.append(asp.fact("sense", tool_id, tool.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a comic quest, a drifting clue, and the right tool."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.thing and args.tool:
        place = PLACES[args.place]
        thing = THINGS[args.thing]
        tool = TOOLS[args.tool]
        if not (hazard_possible(place, thing) and can_rescue(place, tool)):
            raise StoryError(explain_rejection(place, thing, tool))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        fallback_place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        fallback_thing = THINGS[args.thing] if args.thing else next(iter(THINGS.values()))
        raise StoryError(explain_rejection(fallback_place, fallback_thing, TOOLS[args.tool]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.thing is None or combo[1] == args.thing)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, thing_id, tool_id = rng.choice(sorted(combos))
    clue_id = args.clue or rng.choice(sorted(CLUES))
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = _pick_name(rng, hero_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        thing=thing_id,
        tool=tool_id,
        clue=clue_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        thing = THINGS[params.thing]
        tool = TOOLS[params.tool]
        clue = CLUES[params.clue]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err})") from None

    if not hazard_possible(place, thing):
        raise StoryError(explain_rejection(place, thing, tool))
    if not can_rescue(place, tool):
        raise StoryError(explain_rejection(place, thing, tool))

    world = tell(
        place=place,
        thing=thing,
        tool=tool,
        clue=clue,
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        friend_name=params.friend_name,
        friend_type=params.friend_gender,
        parent_type=params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_items(world)],
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

    try:
        sample = generate(CURATED[0])
        if "depiction" not in sample.story or "drown" not in sample.story:
            raise StoryError("(Smoke test failed: required seed words missing from story text.)")
        print("OK: smoke test generation passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        params.seed = 123
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: random generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, thing, tool) combos:\n")
        for place, thing, tool in combos:
            print(f"  {place:10} {thing:8} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for params in CURATED:
            samples.append(generate(params))
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} & {p.friend_name}: {p.thing} at {p.place} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
