#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/launch_domino_mystery_to_solve_repetition_cautionary.py
==================================================================================

A small detective-story storyworld about a repeating indoor mystery:
something keeps going "click, clack, launch!" in the house.

Two children built a domino launch game with a soft projectile. Then, without
anyone touching it, the launcher keeps firing toward something fragile. The
detective child studies clues, watches for the repeating pattern, solves the
mystery, and learns a cautionary lesson about not leaving indoor launch toys
pointed at breakable things.

The world model tracks physical meters (falling dominoes, launches, wobbling
targets, room danger) and emotional memes (surprise, worry, relief, pride).
Rendered prose comes from simulated state and a small set of causal verbs.

Run it
------
    python storyworlds/worlds/gpt-5.4/launch_domino_mystery_to_solve_repetition_cautionary.py
    python storyworlds/worlds/gpt-5.4/launch_domino_mystery_to_solve_repetition_cautionary.py --target vase
    python storyworlds/worlds/gpt-5.4/launch_domino_mystery_to_solve_repetition_cautionary.py --response basket
    python storyworlds/worlds/gpt-5.4/launch_domino_mystery_to_solve_repetition_cautionary.py --all
    python storyworlds/worlds/gpt-5.4/launch_domino_mystery_to_solve_repetition_cautionary.py --qa --json
    python storyworlds/worlds/gpt-5.4/launch_domino_mystery_to_solve_repetition_cautionary.py --verify
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
    traits: list[str] = field(default_factory=list)
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
class Setting:
    id: str
    place: str
    scene: str
    clue_spot: str
    allows: set[str] = field(default_factory=set)


@dataclass
class Trigger:
    id: str
    label: str
    clue: str
    action: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    the: str
    risk: int
    wobble_text: str
    ending_text: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class Response:
    id: str
    label: str
    kind: str
    sense: int
    power: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

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

    def note(self, text: str) -> None:
        self.history.append(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.history = list(self.history)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_launch(world: World) -> list[str]:
    dominoes = world.get("dominoes")
    launcher = world.get("launcher")
    target = world.get("target")
    if dominoes.meters["falling"] < THRESHOLD or launcher.meters["armed"] < THRESHOLD:
        return []
    sig = ("launch", world.facts.get("cycle", 0))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    launcher.meters["launched"] += 1
    world.get("room").meters["danger"] += float(target.attrs["risk"])
    target.meters["wobble"] += 1
    for kid in world.facts["kids"]:
        kid.memes["surprise"] += 1
    return ["__launch__"]


CAUSAL_RULES = [
    Rule(name="launch", tag="physical", apply=_r_launch),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def trigger_reaches(setting: Setting, trigger: Trigger) -> bool:
    return trigger.id in setting.allows


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for tid, trigger in TRIGGERS.items():
            if not trigger_reaches(setting, trigger):
                continue
            for gid in TARGETS:
                combos.append((sid, tid, gid))
    return combos


def outcome_of(params: "StoryParams") -> str:
    response = RESPONSES[params.response]
    target = TARGETS[params.target]
    if response.kind == "stow":
        return "stowed"
    if response.power >= target.risk:
        return "redirected"
    return "stowed"


def explain_combo(setting: Setting, trigger: Trigger) -> str:
    return (
        f"(No story: in {setting.place}, {trigger.label} cannot honestly reach the first domino, "
        f"so there is no repeating mystery to solve. Pick a trigger that can touch the domino line.)"
    )


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_cycle(world: World) -> dict:
    sim = world.copy()
    _do_trigger(sim, narrate=False)
    return {
        "launches": sim.get("launcher").meters["launched"],
        "danger": sim.get("room").meters["danger"],
        "wobble": sim.get("target").meters["wobble"],
    }


def _reset_cycle(world: World) -> None:
    world.get("dominoes").meters["falling"] = 0.0


def _do_trigger(world: World, narrate: bool = True) -> None:
    dominoes = world.get("dominoes")
    dominoes.meters["falling"] += 1
    world.facts["cycle"] = world.facts.get("cycle", 0) + 1
    propagate(world, narrate=narrate)
    _reset_cycle(world)


def introduce_case(world: World, detective: Entity, helper: Entity, launcher: Entity) -> None:
    detective.memes["curiosity"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On a rainy afternoon in {world.setting.place}, {detective.id} opened a tiny detective office with "
        f"{helper.id}. {world.setting.scene}"
    )
    world.say(
        f"To make the room feel exciting, they had lined up a long row of dominoes beside {launcher.phrase}. "
        f"If the first domino tipped, the row would race forward and launch a soft foam rocket."
    )


def first_mystery(world: World, detective: Entity, helper: Entity, target: Target) -> None:
    detective.memes["surprise"] += 1
    helper.memes["surprise"] += 1
    world.say(
        f"Then the case began. From the corner came a sudden sound: "
        f'"click, clack, launch!"'
    )
    _do_trigger(world, narrate=False)
    world.note("first launch")
    world.say(
        f"The rocket zipped across the room, and {target.wobble_text}. "
        f"{helper.id} gasped and looked all around."
    )


def inspect_scene(world: World, detective: Entity, helper: Entity, trigger: Trigger, target: Target) -> None:
    pred = predict_cycle(world)
    detective.memes["focus"] += 1
    helper.memes["worry"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'"A mystery to solve," {detective.id} whispered. {detective.pronoun("subject").capitalize()} knelt by '
        f"the dominoes and studied {world.setting.clue_spot}."
    )
    world.say(
        f"There was {trigger.clue}. The first domino was leaning the tiniest bit toward "
        f"{target.the}, as if it had been nudged instead of touched by a hand."
    )
    world.say(
        f'"Let us watch and not guess," said {detective.id}. "{helper.id}, stay very still."'
    )


def second_mystery(world: World, detective: Entity, helper: Entity, trigger: Trigger, target: Target) -> None:
    world.para()
    detective.memes["confidence"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"They waited. After a quiet moment, {trigger.detail}. Again came the sound: "
        f'"click, clack, launch!"'
    )
    _do_trigger(world, narrate=False)
    world.note("second launch")
    world.say(
        f"This time they saw the whole chain. {trigger.action.capitalize()}, the dominoes fell one after another, "
        f"and the rocket flew toward {target.the} again."
    )


def solve_case(world: World, detective: Entity, helper: Entity, trigger: Trigger) -> None:
    detective.memes["pride"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'"Case solved," said {detective.id}. "It was not a ghost at all. {trigger.action.capitalize()}, '
        f"and that started the launch every time."'
    )
    world.say(
        f"{helper.id} nodded hard. The mystery felt smaller now that it had a real reason."
    )


def caution(world: World, adult: Entity, detective: Entity, helper: Entity, target: Target, launcher: Entity) -> None:
    for kid in (detective, helper):
        kid.memes["worry"] += 1
    world.say(
        f"{adult.label_word.capitalize()} came in when {helper.id} called for help. "
        f"{adult.pronoun('subject').capitalize()} looked at the domino trail, then at {target.the}, and understood the trouble at once."
    )
    world.say(
        f'"You solved the mystery well," {adult.pronoun("subject")} said, "but a launcher left pointing at '
        f"{target.the} is not safe indoors. A repeating game can turn into a broken thing before anyone expects it."'
    )
    launcher.memes["warned"] += 1


def redirect_ending(
    world: World,
    adult: Entity,
    detective: Entity,
    helper: Entity,
    response: Response,
    target: Target,
) -> None:
    detective.memes["relief"] += 1
    helper.memes["joy"] += 1
    detective.memes["joy"] += 1
    world.say(
        f"{adult.label_word.capitalize()} {response.text}."
    )
    world.say(
        f'Soon the sound changed from danger to play. "Click, clack, launch!" the children said together, '
        f"but now the rocket flew into a safe backstop instead of toward {target.the}."
    )
    world.say(
        f"{target.ending_text} The case was closed, and the room felt calm again."
    )


def stow_ending(
    world: World,
    adult: Entity,
    detective: Entity,
    helper: Entity,
    response: Response,
    target: Target,
) -> None:
    detective.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{adult.label_word.capitalize()} {response.text}."
    )
    world.say(
        f'The children whispered the case phrase one last time -- "click, clack, launch" -- '
        f"and then smiled at the quiet."
    )
    world.say(
        f"Instead of sending another rocket toward {target.the}, they drew clue pictures in a notebook and promised "
        f"to ask before setting up a launch game indoors again."
    )


def tell(
    setting: Setting,
    trigger: Trigger,
    target_cfg: Target,
    response: Response,
    detective_name: str,
    detective_gender: str,
    helper_name: str,
    helper_gender: str,
    adult_type: str,
) -> World:
    world = World(setting)
    detective = world.add(
        Entity(
            id=detective_name,
            kind="character",
            type=detective_gender,
            role="detective",
            traits=["careful", "observant"],
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            traits=["curious"],
        )
    )
    adult = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=adult_type,
            role="adult",
            label="the parent",
        )
    )
    room = world.add(Entity(id="room", type="room", label=setting.place))
    dominoes = world.add(
        Entity(
            id="dominoes",
            type="dominoes",
            label="dominoes",
            phrase="a springy little launch ramp",
            tags={"domino"},
        )
    )
    launcher = world.add(
        Entity(
            id="launcher",
            type="launcher",
            label="launcher",
            phrase="a springy little launch ramp",
            tags={"launch"},
        )
    )
    launcher.meters["armed"] = 1.0
    target_ent = world.add(
        Entity(
            id="target",
            type="target",
            label=target_cfg.label,
            attrs={"risk": target_cfg.risk},
            tags=set(target_cfg.tags),
        )
    )
    world.facts["kids"] = [detective, helper]
    world.facts["detective"] = detective
    world.facts["helper"] = helper
    world.facts["adult"] = adult
    world.facts["setting"] = setting
    world.facts["trigger"] = trigger
    world.facts["target_cfg"] = target_cfg
    world.facts["response"] = response
    world.facts["launcher"] = launcher
    world.facts["dominoes"] = dominoes
    world.facts["target"] = target_ent
    world.facts["cycle"] = 0

    introduce_case(world, detective, helper, launcher)
    world.para()
    first_mystery(world, detective, helper, target_cfg)
    inspect_scene(world, detective, helper, trigger, target_cfg)
    second_mystery(world, detective, helper, trigger, target_cfg)
    solve_case(world, detective, helper, trigger)
    world.para()
    caution(world, adult, detective, helper, target_cfg, launcher)

    outcome = outcome_of(
        StoryParams(
            setting=setting.id,
            trigger=trigger.id,
            target=target_cfg.id,
            response=response.id,
            detective=detective_name,
            detective_gender=detective_gender,
            helper=helper_name,
            helper_gender=helper_gender,
            adult=adult_type,
            seed=None,
        )
    )
    if outcome == "redirected":
        redirect_ending(world, adult, detective, helper, response, target_cfg)
    else:
        stow_ending(world, adult, detective, helper, response, target_cfg)

    world.facts["launch_count"] = int(launcher.meters["launched"])
    world.facts["danger"] = room.meters["danger"]
    world.facts["outcome"] = outcome
    world.facts["solved"] = True
    return world


SETTINGS = {
    "living_room": Setting(
        id="living_room",
        place="the living room",
        scene="A blanket on two chairs made their detective tent, and rain tapped softly at the window.",
        clue_spot="the rug by the curtains",
        allows={"cat", "breeze"},
    ),
    "hallway": Setting(
        id="hallway",
        place="the hallway",
        scene="Their detective badges were paper stars, and the long runner rug made the place feel like a secret corridor.",
        clue_spot="the shiny floor near the shoe shelf",
        allows={"breeze", "robot"},
    ),
    "sunroom": Setting(
        id="sunroom",
        place="the sunroom",
        scene="Potted leaves made green shadows on the floor, and the room felt perfect for a make-believe case.",
        clue_spot="the mat beside the plant stand",
        allows={"cat", "breeze"},
    ),
}

TRIGGERS = {
    "cat": Trigger(
        id="cat",
        label="the cat",
        clue="a stripe of soft fur and one tiny paw print",
        action="the cat's tail brushed the first domino",
        detail="the family cat padded past with its tail held high",
        tags={"cat", "domino"},
    ),
    "breeze": Trigger(
        id="breeze",
        label="the breeze",
        clue="the curtain edge was puffing toward the domino line",
        action="a breeze from the open window tapped the first domino",
        detail="the curtain lifted and swayed toward the first domino",
        tags={"wind", "domino"},
    ),
    "robot": Trigger(
        id="robot",
        label="the toy robot",
        clue="two neat wheel marks and a shiny little bump on the first tile",
        action="the toy robot rolled into the first domino",
        detail="the toy robot buzzed from under the shoe shelf and bumped the line",
        tags={"robot", "domino"},
    ),
}

TARGETS = {
    "books": Target(
        id="books",
        label="stack of books",
        the="the stack of books",
        risk=1,
        wobble_text="it tapped the stack of books and made the top one slide sideways",
        ending_text="The books stayed neat on their shelf",
        tags={"books"},
    ),
    "lamp": Target(
        id="lamp",
        label="lamp",
        the="the lamp",
        risk=2,
        wobble_text="it thumped the lamp shade and made the light wobble",
        ending_text="The lamp stood straight with its shade still and tidy",
        tags={"lamp"},
    ),
    "frame": Target(
        id="frame",
        label="picture frame",
        the="the picture frame",
        risk=2,
        wobble_text="it bumped the picture frame and made it knock against the wall",
        ending_text="The picture frame hung quietly where it belonged",
        tags={"frame"},
    ),
    "vase": Target(
        id="vase",
        label="vase",
        the="the vase",
        risk=3,
        wobble_text="it clipped the vase and made the flowers tremble in the water",
        ending_text="The vase stayed safe on its table, with not one flower spilled",
        tags={"vase"},
    ),
}

RESPONSES = {
    "basket": Response(
        id="basket",
        label="laundry basket",
        kind="redirect",
        sense=2,
        power=1,
        text="turned the launcher toward a laundry basket full of folded towels and set the basket at the end of the domino trail",
        qa_text="turned the launcher toward a laundry basket full of towels",
        tags={"basket", "safe_play"},
    ),
    "cushion_wall": Response(
        id="cushion_wall",
        label="cushion wall",
        kind="redirect",
        sense=3,
        power=2,
        text="stacked sofa cushions into a soft wall and pointed the launcher at the middle of it",
        qa_text="built a soft cushion wall and pointed the launcher at it",
        tags={"cushion", "safe_play"},
    ),
    "put_away": Response(
        id="put_away",
        label="put it away",
        kind="stow",
        sense=3,
        power=3,
        text="unhooked the launcher, set the dominoes in their box, and said the launch game could come out later with a grown-up watching",
        qa_text="put the launcher and dominoes away for later",
        tags={"put_away", "safe_play"},
    ),
    "ignore": Response(
        id="ignore",
        label="ignore it",
        kind="redirect",
        sense=1,
        power=0,
        text="left everything exactly where it was",
        qa_text="left the setup alone",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Ruby"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Eli", "Theo"]


@dataclass
class StoryParams:
    setting: str
    trigger: str
    target: str
    response: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    adult: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "domino": [
        (
            "What is a domino?",
            "A domino is a small standing block. When one falls and taps the next one, they can make a whole line tip over."
        )
    ],
    "launch": [
        (
            "What does launch mean?",
            "To launch something means to send it off quickly. A toy launcher can make a soft object shoot forward fast."
        )
    ],
    "cat": [
        (
            "Why can a cat start a domino line by accident?",
            "A cat's tail or paw can brush the first piece without meaning to. Then the rest may fall one after another."
        )
    ],
    "wind": [
        (
            "How can a breeze move light things indoors?",
            "A breeze can puff a curtain or nudge a very light object. If something is already wobbly, that little push can matter."
        )
    ],
    "robot": [
        (
            "Why can a rolling toy cause trouble?",
            "A rolling toy keeps moving until something stops it. If it bumps another object, it can start a chain of motion."
        )
    ],
    "lamp": [
        (
            "Why should you keep toys away from a lamp?",
            "A lamp can tip or its shade can bend if toys hit it. Indoor launch games should point away from things that can break."
        )
    ],
    "frame": [
        (
            "Why is a picture frame a bad target indoors?",
            "A picture frame can fall or crack if it gets bumped. That is why people move launch games away from it."
        )
    ],
    "vase": [
        (
            "Why is a vase fragile?",
            "A vase can spill, chip, or break if it is knocked. Glass and water make accidents bigger very quickly."
        )
    ],
    "basket": [
        (
            "Why is a basket safer than a lamp for catching toys?",
            "A soft basket of towels can stop a toy without hurting anything. It gives the moving toy a gentle place to land."
        )
    ],
    "cushion": [
        (
            "Why do cushions make a good backstop?",
            "Cushions are soft and wide, so they can catch a toy and slow it down. That makes indoor play calmer and safer."
        )
    ],
    "put_away": [
        (
            "When should a grown-up put a toy away for later?",
            "A grown-up can put a toy away when the setup is too risky or too hard to control. Waiting is a safe choice."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "domino",
    "launch",
    "cat",
    "wind",
    "robot",
    "lamp",
    "frame",
    "vase",
    "basket",
    "cushion",
    "put_away",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    trigger = f["trigger"]
    target = f["target_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    prompts = [
        'Write a short detective story for a 3-to-5-year-old that includes the words "launch" and "domino".',
        f"Tell a mystery-to-solve story where {detective.id} hears a repeating indoor sound -- click, clack, launch -- and must figure out why a rocket keeps flying toward {target.the}.",
    ]
    if outcome == "redirected":
        prompts.append(
            f"Write a gentle cautionary story where {detective.id} solves the case of {trigger.label}, and a grown-up helps the children make the launch game safe with {response.label}."
        )
    else:
        prompts.append(
            f"Write a cautionary detective story where {detective.id} solves the case of {trigger.label}, but the grown-up decides the launch game should be put away instead of pointed near {target.the}."
        )
    prompts.append(
        f"Use repetition in the mystery by repeating the sound phrase 'click, clack, launch' while {helper.id} helps watch for clues."
    )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    adult = f["adult"]
    trigger = f["trigger"]
    target = f["target_cfg"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, who played detective, and {helper.id}, who helped watch the room. {adult.label_word.capitalize()} came in at the end to help them make a safe choice."
        ),
        (
            "What was the mystery?",
            f"The mystery was why the domino line kept ending in a launch all by itself. The children heard the same sound again and again and had to learn what was starting it."
        ),
        (
            f"What clue helped {detective.id} solve the case?",
            f"{detective.id} found {trigger.clue} near the first domino. That clue matched the thing that was really nudging the line."
        ),
        (
            f"What happened each time the mystery repeated?",
            f"Each time, the first domino was nudged, the whole row fell, and the launcher sent the foam rocket across the room. The repeating sound was 'click, clack, launch,' and the rocket went toward {target.the}."
        ),
        (
            f"Why did {adult.label_word} say the game was not safe as it was?",
            f"{adult.label_word.capitalize()} said a launcher should not be left pointing at {target.the} indoors. Even a repeating game that seems funny can break something before anyone expects it."
        ),
    ]
    if f["outcome"] == "redirected":
        qa.append(
            (
                "How did they solve the problem after solving the mystery?",
                f"They changed the setup instead of leaving it dangerous. {adult.label_word.capitalize()} {response.qa_text}, so the rocket had a soft place to land and did not fly toward {target.the} anymore."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children still playing, but in a safer way. They could say 'click, clack, launch' with smiles because the danger had been moved out of the path."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly and safely. {adult.label_word.capitalize()} {response.qa_text}, because the room was not a good place for another launch toward {target.the}."
            )
        )
        qa.append(
            (
                f"What did {detective.id} and {helper.id} learn?",
                f"They learned that solving a mystery is only the first step. After you find the cause, you also need to choose the safe thing to do next."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"domino", "launch"} | set(f["trigger"].tags) | set(f["target_cfg"].tags) | set(f["response"].tags)
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  history: {world.history}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="living_room",
        trigger="cat",
        target="lamp",
        response="cushion_wall",
        detective="Lily",
        detective_gender="girl",
        helper="Ben",
        helper_gender="boy",
        adult="mother",
        seed=None,
    ),
    StoryParams(
        setting="hallway",
        trigger="robot",
        target="books",
        response="basket",
        detective="Max",
        detective_gender="boy",
        helper="Zoe",
        helper_gender="girl",
        adult="father",
        seed=None,
    ),
    StoryParams(
        setting="sunroom",
        trigger="breeze",
        target="vase",
        response="cushion_wall",
        detective="Nora",
        detective_gender="girl",
        helper="Leo",
        helper_gender="boy",
        adult="mother",
        seed=None,
    ),
    StoryParams(
        setting="living_room",
        trigger="breeze",
        target="vase",
        response="put_away",
        detective="Theo",
        detective_gender="boy",
        helper="Mia",
        helper_gender="girl",
        adult="father",
        seed=None,
    ),
]


ASP_RULES = r"""
% reachability of the mystery trigger
valid(S, Tr, T) :- setting(S), trigger(Tr), target(T), allows(S, Tr).

% sensible responses
sensible(R) :- response(R), sense(R, V), sense_min(M), V >= M.

% outcome model
outcome(stowed) :- chosen_response(R), kind(R, stow).
outcome(redirected) :- chosen_response(R), kind(R, redirect),
                       target_risk(Tg, Risk), chosen_target(Tg),
                       power(R, P), P >= Risk.
outcome(stowed) :- chosen_response(R), kind(R, redirect),
                   target_risk(Tg, Risk), chosen_target(Tg),
                   power(R, P), P < Risk.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for trig in sorted(setting.allows):
            lines.append(asp.fact("allows", sid, trig))
    for tid in TRIGGERS:
        lines.append(asp.fact("trigger", tid))
    for gid, target in TARGETS.items():
        lines.append(asp.fact("target", gid))
        lines.append(asp.fact("target_risk", gid, target.risk))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
        lines.append(asp.fact("kind", rid, response.kind))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_response", params.response),
            asp.fact("chosen_target", params.target),
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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(25):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective-style storyworld: a repeating domino launch mystery with a cautionary ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.trigger:
        setting = SETTINGS[args.setting]
        trigger = TRIGGERS[args.trigger]
        if not trigger_reaches(setting, trigger):
            raise StoryError(explain_combo(setting, trigger))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.trigger is None or combo[1] == args.trigger)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, trigger_id, target_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    detective, detective_gender = _pick_name(rng)
    helper, helper_gender = _pick_name(rng, avoid=detective)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        trigger=trigger_id,
        target=target_id,
        response=response_id,
        detective=detective,
        detective_gender=detective_gender,
        helper=helper,
        helper_gender=helper_gender,
        adult=adult,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        trigger = TRIGGERS[params.trigger]
        target = TARGETS[params.target]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err

    if not trigger_reaches(setting, trigger):
        raise StoryError(explain_combo(setting, trigger))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(response.id))

    world = tell(
        setting=setting,
        trigger=trigger,
        target_cfg=target,
        response=response,
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        adult_type=params.adult,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, trigger, target) combos:\n")
        for setting, trigger, target in combos:
            print(f"  {setting:12} {trigger:8} {target}")
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
                f"### {p.detective} & {p.helper}: {p.trigger} in {p.setting} "
                f"toward {p.target} ({p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
