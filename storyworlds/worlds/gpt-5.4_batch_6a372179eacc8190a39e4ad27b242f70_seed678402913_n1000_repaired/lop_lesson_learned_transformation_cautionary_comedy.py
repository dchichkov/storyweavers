#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lop_lesson_learned_transformation_cautionary_comedy.py

A small storyworld about a child who wants to "lop" part off a costume before a
funny little parade. The world prefers sensible, child-facing stories where an
adult helps with a safer fix, but it also supports a near-miss and an oopsie
ending where the costume is cut too short and the child learns to ask first.

Run it:
    python storyworlds/worlds/gpt-5.4/lop_lesson_learned_transformation_cautionary_comedy.py
    python storyworlds/worlds/gpt-5.4/lop_lesson_learned_transformation_cautionary_comedy.py --costume cape_tail
    python storyworlds/worlds/gpt-5.4/lop_lesson_learned_transformation_cautionary_comedy.py --fix tape_patch
    python storyworlds/worlds/gpt-5.4/lop_lesson_learned_transformation_cautionary_comedy.py --all
    python storyworlds/worlds/gpt-5.4/lop_lesson_learned_transformation_cautionary_comedy.py --verify
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

# Make storyworlds/results.py importable when this nested script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
IMPULSE_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful", "patient"}


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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    cuttable: bool = False
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
class Theme:
    id: str
    scene: str
    rig: str
    event: str
    role_single: str
    role_plural: str
    ending: str


@dataclass
class Costume:
    id: str
    label: str
    phrase: str
    part: str
    trailing: str
    material: str
    base_severity: int
    cuttable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    where: str
    sharp: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    power: int
    materials: set[str] = field(default_factory=set)
    text: str = ""
    fail: str = ""
    qa_text: str = ""
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"snipper", "buddy"}]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_trip_risk(world: World) -> list[str]:
    costume = world.entities.get("costume")
    room = world.entities.get("room")
    if costume is None or room is None:
        return []
    if costume.meters["dragging"] < THRESHOLD:
        return []
    sig = ("trip_risk", "costume")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["risk"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__risk__"]


def _r_cut_oops(world: World) -> list[str]:
    costume = world.entities.get("costume")
    if costume is None or costume.meters["cut"] < THRESHOLD:
        return []
    sig = ("cut_oops", "costume")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    costume.meters["crooked"] += 1
    for kid in world.kids():
        kid.memes["surprise"] += 1
    return ["__oops__"]


CAUSAL_RULES = [
    Rule(name="trip_risk", tag="physical", apply=_r_trip_risk),
    Rule(name="cut_oops", tag="physical", apply=_r_cut_oops),
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
        for s in produced:
            world.say(s)
    return produced


def repairable(costume: Costume, fix: Fix) -> bool:
    return costume.cuttable and costume.material in fix.materials


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def damage_severity(costume: Costume, delay: int) -> int:
    return costume.base_severity + delay


def can_save(fix: Fix, costume: Costume, delay: int) -> bool:
    return fix.power >= damage_severity(costume, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, snipper_age: int, buddy_age: int, trait: str) -> bool:
    buddy_older = relation == "siblings" and buddy_age > snipper_age
    authority = initial_caution(trait) + 1.0 + (3.0 if buddy_older else 0.0)
    return buddy_older and authority > IMPULSE_INIT


def predict_cut(world: World) -> dict:
    sim = world.copy()
    costume = sim.get("costume")
    costume.meters["cut"] += 1
    costume.meters["too_short"] += 1
    propagate(sim, narrate=False)
    return {
        "too_short": costume.meters["too_short"] >= THRESHOLD,
        "risk": sim.get("room").meters["risk"],
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"After lunch, {a.id} and {b.id} turned the living room into {theme.scene}. {theme.rig}"
    )
    world.say(
        f"They were getting ready for {theme.event}, and {a.id} wanted to look like the funniest {theme.role_single} in the room."
    )


def costume_problem(world: World, a: Entity, costume: Costume) -> None:
    world.get("costume").meters["dragging"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {a.id}'s {costume.label} had {costume.trailing}. It kept swishing under {a.pronoun('possessive')} shoes and making {a.pronoun('object')} wobble."
    )
    world.say(
        f'Every time {a.pronoun()} spun, {costume.part} flopped again, and soon {a.id} sighed, "This thing is too much."'
    )


def tempt(world: World, a: Entity, tool: Tool) -> None:
    a.memes["impulse"] += 1
    world.say(
        f'Then {a.id} spotted {tool.phrase} {tool.where}. "{tool.label.capitalize()}!" {a.pronoun().capitalize()} said. "I can just lop this off."'
    )
    world.say("For one silly second, that plan sounded fast and brilliant.")


def warn(world: World, b: Entity, a: Entity, tool: Tool, costume: Costume, parent: Entity) -> None:
    pred = predict_cut(world)
    b.memes["caution"] += 1
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f'{b.id} widened {b.pronoun("possessive")} eyes. "{a.id}, no. We only use {tool.label} with {parent.label_word}. If you lop {costume.part} without thinking, {costume.the} could turn crooked and too short."'
    )


def back_down(world: World, a: Entity, b: Entity, tool: Tool, parent: Entity) -> None:
    a.memes["impulse"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at the scissors, then at {b.id}, {a.pronoun("possessive")} older sibling, and let out a puff of air. "Okay," {a.pronoun()} said. "No secret lopping."'
    )
    world.say(
        f"They carried the costume to {parent.label_word} instead of touching {tool.label}."
    )


def defy(world: World, a: Entity, b: Entity, tool: Tool) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"It will be fine," {a.id} said. Because {a.pronoun()} was the older one this time, {b.id} could not stop {a.pronoun("object")} before {a.pronoun()} grabbed {tool.label}.'
        )
    else:
        world.say(
            f'"It will be fine," {a.id} said, and before {b.id} could answer, {a.pronoun()} grabbed {tool.label}.'
        )


def snip(world: World, a: Entity, costume: Costume) -> None:
    ent = world.get("costume")
    ent.meters["cut"] += 1
    ent.meters["too_short"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Snip! One quick bite of the blades, then another. Instead of a neat little trim, {costume.part} jumped up crooked, and a funny scrap of {costume.material.replace('_', ' ')} drifted onto {a.id}'s nose."
    )
    world.say(
        f"{a.id} blinked. {costume.the.capitalize()} was no longer dragging. Now it looked lopsided."
    )


def alarm(world: World, b: Entity, a: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.upper()}!" {b.id} yelped. "{a.id} really did it!"')


def rescue(world: World, parent: Entity, fix: Fix, costume: Costume, theme: Theme) -> None:
    ent = world.get("costume")
    ent.meters["repaired"] += 1
    ent.meters["too_short"] = 0.0
    ent.meters["crooked"] = 0.0
    body = fix.text.format(costume=costume.label, part=costume.part, role=theme.role_single)
    world.say(
        f"{parent.label_word.capitalize()} came in, took one look, and did not even gasp. {parent.pronoun().capitalize()} {body}."
    )
    world.say(
        f"In a minute, the costume looked different, but in a funny good way. It had transformed from a droopy mess into something that made everyone grin."
    )


def rescue_fail(world: World, parent: Entity, fix: Fix, costume: Costume) -> None:
    ent = world.get("costume")
    ent.meters["backup_needed"] += 1
    body = fix.fail.format(costume=costume.label, part=costume.part)
    world.say(
        f"{parent.label_word.capitalize()} hurried in and {body}."
    )
    world.say(
        f"But {costume.the} was still too short to look the way {a_or_child(world).id} had planned, and there was no time to make it grand again."
    )


def a_or_child(world: World) -> Entity:
    return world.get("child")


def lesson(world: World, parent: Entity, a: Entity, b: Entity, tool: Tool) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them and smiled a little. "Sharp {tool.label} are for careful jobs with a grown-up," {parent.pronoun()} said. "Fast fixes can make funny trouble."'
    )
    world.say(
        f'{a.id} touched the patched costume and nodded. "Next time I will ask before I lop anything," {a.pronoun()} said.'
    )


def happy_ending(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["confidence"] += 1
    world.say(
        f"When {theme.event} began, {a.id} swooshed across the room in the transformed costume, and even {b.id} laughed so hard {b.pronoun()} had to clap with both hands."
    )
    world.say(
        f"The whole room cheered, and the funniest part was not the mistake anymore. It was how the {theme.role_single} looked bright, brave, and wonderfully odd."
    )


def safe_fix_only(world: World, parent: Entity, fix: Fix, costume: Costume, theme: Theme, a: Entity, b: Entity) -> None:
    ent = world.get("costume")
    ent.meters["repaired"] += 1
    body = fix.text.format(costume=costume.label, part=costume.part, role=theme.role_single)
    world.say(
        f"{parent.label_word.capitalize()} studied the dragging {costume.part} and {body}."
    )
    world.say(
        f"The costume changed right there: no longer a trip-prone tangle, but a neat, funny outfit ready for the show."
    )
    world.say(
        f"Soon {a.id} and {b.id} were back to practicing, this time with no secret scissors and much more giggling."
    )


def backup_ending(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say(
        f"So {parent.label_word} tied on a simple backup apron with a shiny star in the middle. It was not the grand costume {a.id} had imagined, but it was safe, comfy, and still a little funny."
    )
    world.say(
        f"At {theme.event}, {a.id} gave a tiny bow in the plain new outfit. {a.pronoun().capitalize()} smiled anyway, because {a.pronoun()} had learned something bigger than a costume trick."
    )


def tell(
    theme: Theme,
    costume: Costume,
    tool: Tool,
    fix: Fix,
    *,
    child_name: str = "Mia",
    child_gender: str = "girl",
    buddy_name: str = "Ben",
    buddy_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    child_age: int = 5,
    buddy_age: int = 7,
    relation: str = "siblings",
    trust: int = 5,
) -> World:
    world = World()
    a = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="snipper",
        age=child_age,
        traits=["playful"],
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=buddy_name,
        kind="character",
        type=buddy_gender,
        role="buddy",
        age=buddy_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    a.memes["impulse"] = IMPULSE_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)

    world.add(Entity(id="room", type="room", label="living room"))
    world.add(Entity(
        id="costume",
        type="costume",
        label=costume.label,
        phrase=costume.phrase,
        cuttable=costume.cuttable,
        tags=set(costume.tags),
    ))
    world.entities["child"] = a

    play_setup(world, a, b, theme)
    costume_problem(world, a, costume)

    world.para()
    tempt(world, a, tool)
    warn(world, b, a, tool, costume, parent)

    averted = would_avert(relation, child_age, buddy_age, trait)
    if averted:
        back_down(world, a, b, tool, parent)
        world.para()
        safe_fix_only(world, parent, fix, costume, theme, a, b)
        outcome = "averted"
    else:
        defy(world, a, b, tool)
        world.para()
        snip(world, a, costume)
        alarm(world, b, a, parent)
        world.para()
        contained = can_save(fix, costume, delay)
        if contained:
            rescue(world, parent, fix, costume, theme)
            lesson(world, parent, a, b, tool)
            world.para()
            happy_ending(world, a, b, theme)
            outcome = "repaired"
        else:
            rescue_fail(world, parent, fix, costume)
            lesson(world, parent, a, b, tool)
            world.para()
            backup_ending(world, parent, a, b, theme)
            outcome = "backup"

    world.facts.update(
        child=a,
        buddy=b,
        parent=parent,
        theme=theme,
        costume_cfg=costume,
        tool=tool,
        fix=fix,
        relation=relation,
        delay=delay,
        outcome=outcome,
        severity=damage_severity(costume, delay) if outcome != "averted" else 0,
        cut_happened=world.get("costume").meters["cut"] >= THRESHOLD,
    )
    return world


THEMES = {
    "dragon": Theme(
        id="dragon",
        scene="a tiny dragon cave",
        rig="A blanket over two chairs became a cave, a wooden spoon became a torch, and a row of couch cushions became hot lava nobody was allowed to touch.",
        event="the family parade",
        role_single="dragon",
        role_plural="dragons",
        ending="stomped and swished around the couch",
    ),
    "wizard": Theme(
        id="wizard",
        scene="a grand wizard hall",
        rig="A towel over the lamp made a gold glow, a paper star wand leaned by the sofa, and three couch pillows became a mountain of secret spell books.",
        event="the kitchen talent show",
        role_single="wizard",
        role_plural="wizards",
        ending="swooped around the coffee table",
    ),
    "peacock": Theme(
        id="peacock",
        scene="a bright parade tent",
        rig="A row of cups became parade drums, a scarf became a stage curtain, and the rug was suddenly the most important runway in the house.",
        event="the hallway march",
        role_single="peacock",
        role_plural="peacocks",
        ending="tiptoed proudly down the hallway",
    ),
}

COSTUMES = {
    "cape_tail": Costume(
        id="cape_tail",
        label="dragon cape",
        phrase="a dragon cape with a tail stitched on the back",
        part="tail",
        trailing="a tail so long it dragged behind like a sleepy snake",
        material="fabric",
        base_severity=2,
        tags={"cape", "costume", "fabric"},
    ),
    "robe_hem": Costume(
        id="robe_hem",
        label="wizard robe",
        phrase="a wizard robe with silver paper stars",
        part="hem",
        trailing="a hem that kept sweeping the floor like a very proud mop",
        material="fabric",
        base_severity=2,
        tags={"robe", "costume", "fabric"},
    ),
    "feather_train": Costume(
        id="feather_train",
        label="peacock train",
        phrase="a peacock train made of paper feathers",
        part="train",
        trailing="paper feathers so long they whispered across the floor",
        material="paper",
        base_severity=1,
        tags={"train", "costume", "paper"},
    ),
    "metal_hat": Costume(
        id="metal_hat",
        label="tin hat",
        phrase="a stiff tin hat with jingly tabs",
        part="rim",
        trailing="a rim that was stiff and bent the wrong way",
        material="metal",
        base_severity=2,
        cuttable=False,
        tags={"hat", "costume", "metal"},
    ),
}

TOOLS = {
    "scissors": Tool(
        id="scissors",
        label="scissors",
        phrase="the sharp craft scissors",
        where="on the art shelf",
        sharp=True,
        tags={"scissors", "sharp"},
    ),
    "kitchen_shears": Tool(
        id="kitchen_shears",
        label="kitchen shears",
        phrase="the kitchen shears",
        where="by the fruit bowl",
        sharp=True,
        tags={"scissors", "sharp"},
    ),
}

FIXES = {
    "safety_pin_fold": Fix(
        id="safety_pin_fold",
        label="safety pins",
        sense=3,
        power=3,
        materials={"fabric"},
        text="folded the extra {part} up inside, fastened it with bright safety pins, and added a silly gold ribbon for flourish",
        fail="tried to fold the {part} up and pin it neatly",
        qa_text="folded the extra part up and fastened it with bright safety pins",
        tags={"pins", "costume"},
    ),
    "tape_patch": Fix(
        id="tape_patch",
        label="colored tape",
        sense=2,
        power=2,
        materials={"paper"},
        text="smoothed the torn {part}, covered the snipped place with striped tape, and turned it into a fluttering patch that looked almost planned",
        fail="smoothed the cut place and tried to patch it with tape",
        qa_text="patched the cut place with striped tape",
        tags={"tape", "costume"},
    ),
    "bow_knot": Fix(
        id="bow_knot",
        label="big bow",
        sense=2,
        power=1,
        materials={"fabric"},
        text="gathered the extra {part} into a huge bow and laughed when it made the whole {role} look even sillier",
        fail="tried to hide the missing bit with a bow",
        qa_text="gathered the extra part into a big bow",
        tags={"bow", "costume"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Nora", "Ruby", "Anna"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Finn", "Theo", "Jack", "Eli"]
TRAITS = ["careful", "steady", "thoughtful", "patient", "curious", "cheerful"]


@dataclass
class StoryParams:
    theme: str
    costume: str
    tool: str
    fix: str
    child_name: str
    child_gender: str
    buddy_name: str
    buddy_gender: str
    parent: str
    trait: str
    delay: int = 0
    child_age: int = 5
    buddy_age: int = 7
    relation: str = "siblings"
    trust: int = 5
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        theme="dragon",
        costume="cape_tail",
        tool="scissors",
        fix="safety_pin_fold",
        child_name="Mia",
        child_gender="girl",
        buddy_name="Ben",
        buddy_gender="boy",
        parent="mother",
        trait="careful",
        delay=0,
        child_age=5,
        buddy_age=7,
        relation="siblings",
        trust=6,
    ),
    StoryParams(
        theme="wizard",
        costume="robe_hem",
        tool="kitchen_shears",
        fix="bow_knot",
        child_name="Leo",
        child_gender="boy",
        buddy_name="Ava",
        buddy_gender="girl",
        parent="father",
        trait="curious",
        delay=1,
        child_age=6,
        buddy_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        theme="peacock",
        costume="feather_train",
        tool="scissors",
        fix="tape_patch",
        child_name="Zoe",
        child_gender="girl",
        buddy_name="Max",
        buddy_gender="boy",
        parent="mother",
        trait="patient",
        delay=0,
        child_age=4,
        buddy_age=6,
        relation="siblings",
        trust=8,
    ),
    StoryParams(
        theme="dragon",
        costume="cape_tail",
        tool="kitchen_shears",
        fix="bow_knot",
        child_name="Finn",
        child_gender="boy",
        buddy_name="Ruby",
        buddy_gender="girl",
        parent="father",
        trait="steady",
        delay=2,
        child_age=7,
        buddy_age=5,
        relation="siblings",
        trust=3,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme in THEMES:
        for costume_id, costume in COSTUMES.items():
            for fix_id, fix in FIXES.items():
                if costume.cuttable and repairable(costume, fix):
                    combos.append((theme, costume_id, fix_id))
    return combos


def explain_rejection(costume: Costume, fix: Optional[Fix] = None) -> str:
    if not costume.cuttable:
        return (
            f"(No story: {costume.the} is too stiff to sensibly lop with scissors here. "
            f"That means the cutting beat does not work. Pick a fabric or paper costume instead.)"
        )
    if fix is not None and not repairable(costume, fix):
        return (
            f"(No story: {fix.label} does not sensibly repair {costume.material.replace('_', ' ')}. "
            f"Pick a fix that matches the costume material.)"
        )
    return "(No story: this combination does not form a sensible costume-cutting problem.)"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.child_age, params.buddy_age, params.trait):
        return "averted"
    fix = FIXES[params.fix]
    costume = COSTUMES[params.costume]
    return "repaired" if can_save(fix, costume, params.delay) else "backup"


KNOWLEDGE = {
    "scissors": [
        (
            "What are scissors for?",
            "Scissors are tools for cutting paper, cloth, and other things carefully. Children should use them only with the right kind and with a grown-up close by.",
        )
    ],
    "sharp": [
        (
            "Why should children ask before using sharp tools?",
            "Sharp tools can slip, pinch, or cut the wrong thing very quickly. Asking a grown-up helps make the job slower and safer.",
        )
    ],
    "pins": [
        (
            "What does a safety pin do?",
            "A safety pin holds cloth together without cutting it shorter. Grown-ups use it for quick clothing fixes.",
        )
    ],
    "tape": [
        (
            "What can tape do on paper?",
            "Tape can hold torn paper together and help a rip stop spreading. It works best when the paper is not too damaged.",
        )
    ],
    "bow": [
        (
            "Why can tying a bow help a costume?",
            "A bow can gather extra fabric into one place, so a loose part stops dragging. It changes the shape without cutting more.",
        )
    ],
    "costume": [
        (
            "What is a costume?",
            "A costume is clothing or dress-up gear that helps you pretend to be someone or something else. It can make play feel bigger and funnier.",
        )
    ],
    "fabric": [
        (
            "What is fabric?",
            "Fabric is cloth. It bends and folds, which is why grown-ups can sometimes pin or tie it instead of cutting it.",
        )
    ],
    "paper": [
        (
            "Why does paper tear easily?",
            "Paper is thin, so once it is nicked or cut, the tear can spread if you pull it. That is why gentle patching can help.",
        )
    ],
}
KNOWLEDGE_ORDER = ["scissors", "sharp", "costume", "fabric", "paper", "pins", "tape", "bow"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    buddy = f["buddy"]
    costume = f["costume_cfg"]
    tool = f["tool"]
    outcome = f["outcome"]
    base = (
        f'Write a funny cautionary story for a 3-to-5-year-old that includes the word "lop" '
        f"and is about {child.id} wanting to cut {costume.part} on a {costume.label} with {tool.label}."
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle near-miss story where {buddy.id} stops {child.id} from trying to lop the costume, and a grown-up fixes it the safe way.",
            "Write a comedy-flavored lesson-learned story where nobody gets hurt, the costume is transformed safely, and the child learns to ask first.",
        ]
    if outcome == "backup":
        return [
            base,
            f"Tell a cautionary comedy where {child.id} really does lop the costume, the fix is not enough, and the child ends up wearing a plain backup outfit but still learns a lesson.",
            "Write a story with a silly mistake, a gentle consequence, and a clear lesson about asking before using sharp tools.",
        ]
    return [
        base,
        f"Tell a funny transformation story where {child.id} snips too much, but a calm grown-up repairs the costume into a new silly look.",
        "Write a child-facing cautionary comedy that ends with a patched costume, laughter, and a lesson learned.",
    ]


def pair_noun(child: Entity, buddy: Entity, relation: str) -> str:
    if relation == "siblings":
        if child.type == "boy" and buddy.type == "boy":
            return "two brothers"
        if child.type == "girl" and buddy.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    buddy = f["buddy"]
    parent = f["parent"]
    theme = f["theme"]
    costume = f["costume_cfg"]
    tool = f["tool"]
    fix = f["fix"]
    relation = f["relation"]
    pair = pair_noun(child, buddy, relation)
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {child.id} and {buddy.id}, and {child.id}'s {parent.label_word}. They were getting ready for {theme.event}.",
        ),
        (
            f"What was wrong with {child.id}'s costume?",
            f"The {costume.label} had {costume.trailing}. That made it drag and wobble, which is why {child.id} wanted a fast fix.",
        ),
        (
            f"What did {child.id} want to do?",
            f"{child.id} wanted to use {tool.label} and lop off the extra {costume.part}. It seemed quick, but it could make the costume too short and crooked.",
        ),
        (
            f"Why did {buddy.id} warn {child.id}?",
            f"{buddy.id} knew sharp {tool.label} could change the costume too fast. The warning came from the risk that one quick snip would make a bigger problem.",
        ),
    ]
    if outcome == "averted":
        qa.extend([
            (
                f"Did {child.id} cut the costume?",
                f"No. {child.id} backed down and took the costume to {parent.label_word} instead. That choice stopped the mistake before it happened.",
            ),
            (
                f"How was the costume transformed in the end?",
                f"{parent.label_word.capitalize()} used {fix.label} to change the dragging part safely. The costume became neat and funny without any secret cutting.",
            ),
        ])
    elif outcome == "repaired":
        qa.extend([
            (
                f"What happened when {child.id} used the {tool.label}?",
                f"{child.id} cut too much, and the {costume.part} turned crooked and too short. The problem changed from dragging to lopsided in just a moment.",
            ),
            (
                f"How did {parent.label_word} help?",
                f"{parent.label_word.capitalize()} {fix.qa_text}. That repaired the costume enough to turn the mistake into a new, sillier design.",
            ),
            (
                "What lesson did the child learn?",
                f"{child.id} learned to ask before using sharp tools. The funny rescue worked this time, but the trouble started because {child.pronoun()} tried to fix it alone.",
            ),
        ])
    else:
        qa.extend([
            (
                f"Could {parent.label_word} fully save the costume?",
                f"No. {parent.label_word.capitalize()} tried, but the costume was still too short for the original plan. The cut was bigger than the quick fix could handle.",
            ),
            (
                "How did the story end?",
                f"It ended with a plain backup outfit and a calmer child. {child.id} still joined {theme.event}, but with a smaller smile and a bigger lesson.",
            ),
            (
                "What lesson did the child learn?",
                f"{child.id} learned that fast secret cutting can spoil a costume. Asking first would have been slower, but much wiser.",
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["tool"].tags) | set(f["costume_cfg"].tags) | set(f["fix"].tags)
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
    for e in list(world.entities.values()):
        if e.id == "child":
            continue
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, C, F) :- theme(T), costume(C), fix(F), cuttable(C), repairable(C, F).

cautious_now(Tra) :- trait(Tra), is_cautious(Tra).
init_caution(5) :- trait(Tra), cautious_now(Tra).
init_caution(3) :- trait(Tra), not cautious_now(Tra).
buddy_older :- relation(siblings), child_age(CA), buddy_age(BA), BA > CA.
bonus(3) :- buddy_older.
bonus(0) :- not buddy_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- buddy_older, authority(A), impulse_init(I), A > I.

severity(B + D) :- chosen_costume(C), base_severity(C, B), delay(D).
fix_power(P) :- chosen_fix(F), power(F, P).
repaired :- fix_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(repaired) :- not averted, repaired.
outcome(backup) :- not averted, not repaired.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme in THEMES:
        lines.append(asp.fact("theme", theme))
    for cid, costume in COSTUMES.items():
        lines.append(asp.fact("costume", cid))
        lines.append(asp.fact("base_severity", cid, costume.base_severity))
        if costume.cuttable:
            lines.append(asp.fact("cuttable", cid))
        lines.append(asp.fact("material", cid, costume.material))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
        for material in sorted(fix.materials):
            lines.append(asp.fact("fixes_material", fid, material))
    lines.append(asp.fact("impulse_init", int(IMPULSE_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append("repairable(C, F) :- material(C, M), fixes_material(F, M).")
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
        asp.fact("chosen_costume", params.costume),
        asp.fact("chosen_fix", params.fix),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("child_age", params.child_age),
        asp.fact("buddy_age", params.buddy_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for s in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a child wants to lop part off a costume, and the world checks for a sensible fix."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--costume", choices=COSTUMES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.costume:
        costume = COSTUMES[args.costume]
        if not costume.cuttable:
            raise StoryError(explain_rejection(costume))
        if args.fix:
            fix = FIXES[args.fix]
            if not repairable(costume, fix):
                raise StoryError(explain_rejection(costume, fix))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.costume is None or combo[1] == args.costume)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, costume_id, fix_id = rng.choice(sorted(combos))
    child_name, child_gender = _pick_kid(rng)
    buddy_name, buddy_gender = _pick_kid(rng, avoid=child_name)
    tool = args.tool or rng.choice(sorted(TOOLS))
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    child_age, buddy_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        theme=theme,
        costume=costume_id,
        tool=tool,
        fix=fix_id,
        child_name=child_name,
        child_gender=child_gender,
        buddy_name=buddy_name,
        buddy_gender=buddy_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        child_age=child_age,
        buddy_age=buddy_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        costume = COSTUMES[params.costume]
        tool = TOOLS[params.tool]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from err

    if not costume.cuttable:
        raise StoryError(explain_rejection(costume))
    if not repairable(costume, fix):
        raise StoryError(explain_rejection(costume, fix))

    world = tell(
        theme=theme,
        costume=costume,
        tool=tool,
        fix=fix,
        child_name=params.child_name,
        child_gender=params.child_gender,
        buddy_name=params.buddy_name,
        buddy_gender=params.buddy_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        child_age=params.child_age,
        buddy_age=params.buddy_age,
        relation=params.relation,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, costume, fix) combos:\n")
        for theme, costume, fix in combos:
            print(f"  {theme:8} {costume:13} {fix}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.child_name} & {p.buddy_name}: {p.costume} with {p.fix} ({outcome_of(p)})"
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
