#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/whirly_cellar_cabaret_moral_value_humor_comedy.py
=============================================================================

A standalone story world for a tiny comedy domain: two children turn a cellar
into a little cabaret, one of them tries a silly shortcut with a whirly stool,
and the story teaches that asking for help beats showing off.

Seed words and instruments
--------------------------
Words: whirly, cellar, cabaret
Features: Moral Value, Humor
Style: Comedy

This world models a short tale with a clear causal shape:

- premise: children build a funny cellar cabaret
- tension: something needs to be hung high above the stage
- turn: a bold child wants to use an unsafe, whirly perch
- resolution: either the warning is heeded, or there is a comic wobble and a
  grown-up helps them fix it properly
- moral value: ask for help, choose the steady way, and clean up what you knock over

The world includes:
- typed entities with physical meters and emotional memes
- a Python reasonableness gate plus an inline ASP twin
- deterministic StoryParams
- prose, trace, JSON, Q&A, ASP, and verify modes
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
# from the repo root or from this nested world directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
SHOW_OFF_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "sensible", "steady", "thoughtful"}


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
    rollers: bool = False
    steady: bool = False
    overhead: bool = False
    fragile: bool = False
    # physical and emotional axes
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
    opener: str
    title_a: str
    title_b: str
    act_name: str
    finale: str
    prop_line: str
    send_off: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    rolls: bool
    funny: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Decoration:
    id: str
    label: str
    phrase: str
    place: str
    fragile: bool
    tumble: str
    after: str
    chaos: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    theme: str
    perch: str
    decoration: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 6
    helper_item: str = ""
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
        return [e for e in self.entities.values() if e.role in ("instigator", "cautioner")]

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
    if perch is None or perch.meters["climbed"] < THRESHOLD or not perch.rollers:
        return out
    sig = ("wobble", perch.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    perch.meters["wobble"] += 1
    world.get("cellar").meters["noise"] += 1
    for kid in world.kids():
        kid.memes["alarm"] += 1
    out.append("__wobble__")
    return out


def _r_drop(world: World) -> list[str]:
    out: list[str] = []
    perch = world.entities.get("perch")
    deco = world.entities.get("decoration")
    if perch is None or deco is None:
        return out
    if perch.meters["wobble"] < THRESHOLD or deco.meters["being_hung"] < THRESHOLD:
        return out
    sig = ("drop", deco.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    deco.meters["fallen"] += 1
    deco.meters["mess"] += deco.attrs.get("chaos", 1)
    world.get("cellar").meters["mess"] += deco.attrs.get("chaos", 1)
    world.get("cellar").meters["noise"] += 1
    for kid in world.kids():
        kid.memes["embarrassment"] += 1
        kid.memes["fear"] += 1
    out.append("__drop__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="drop", tag="physical", apply=_r_drop),
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
    "song": Theme(
        id="song",
        scene="a tiny cellar cabaret",
        opener="Old blankets became curtains, a crate became a stage, and a jam jar held paper tickets.",
        title_a="Maestro",
        title_b="Manager",
        act_name="the moon-song",
        finale="a bow so grand it nearly tipped the ticket jar",
        prop_line="They wanted one shining thing above the stage to make the room feel special.",
        send_off="their song bounced off the cellar walls in the happiest way",
        tags={"cabaret", "music"},
    ),
    "magic": Theme(
        id="magic",
        scene="a tiny cellar cabaret",
        opener="Old blankets became curtains, a laundry basket became a backstage room, and three spoons became a drum roll.",
        title_a="Professor",
        title_b="Assistant",
        act_name="the disappearing carrot trick",
        finale="a bow so serious that it made both of them giggle",
        prop_line="They wanted one bright sign above the stage so every trick would feel important.",
        send_off="their magic show ended with claps, laughs, and one very confused carrot",
        tags={"cabaret", "magic"},
    ),
    "dance": Theme(
        id="dance",
        scene="a tiny cellar cabaret",
        opener="Old blankets became curtains, a chalk line became a stage edge, and a saucepan lid served as a shiny gong.",
        title_a="Captain",
        title_b="Coach",
        act_name="the tap-tap turn",
        finale="a bow so fancy that even the cellar steps seemed to grin",
        prop_line="They wanted one cheerful thing above the stage to make the dance feel grand.",
        send_off="their dance ended with little stamps, laughter, and a perfect final pose",
        tags={"cabaret", "dance"},
    ),
}

PERCHES = {
    "whirly_stool": Perch(
        id="whirly_stool",
        label="whirly stool",
        phrase="a whirly stool from the old workbench",
        rolls=True,
        funny="It spun a tiny bit even when nobody asked it to.",
        tags={"whirly", "unsafe"},
    ),
    "jam_crate": Perch(
        id="jam_crate",
        label="jam crate",
        phrase="an upside-down jam crate",
        rolls=False,
        funny="It gave one dry wooden creak.",
        tags={"crate"},
    ),
    "toy_wagon": Perch(
        id="toy_wagon",
        label="toy wagon",
        phrase="a red toy wagon with squeaky wheels",
        rolls=True,
        funny="Its wheels whispered a sneaky squeak.",
        tags={"wagon", "unsafe"},
    ),
    "paint_can": Perch(
        id="paint_can",
        label="paint can",
        phrase="an empty paint can turned upside down",
        rolls=False,
        funny="It made a hollow bonk sound.",
        tags={"can", "unsafe"},
    ),
}

DECORATIONS = {
    "paper_moon": Decoration(
        id="paper_moon",
        label="paper moon",
        phrase="a silver paper moon",
        place="over the little stage",
        fragile=False,
        tumble="The paper moon swooped down like a sleepy pancake.",
        after="It landed on the ticket jar and slid off with a shush.",
        chaos=1,
        tags={"moon", "paper"},
    ),
    "tin_star": Decoration(
        id="tin_star",
        label="tin star",
        phrase="a shiny tin star",
        place="over the little stage",
        fragile=False,
        tumble="The tin star clanged down and spun in a proud little circle.",
        after="It made such a dramatic ding that both children blinked.",
        chaos=1,
        tags={"star", "shiny"},
    ),
    "feather_sign": Decoration(
        id="feather_sign",
        label="feather sign",
        phrase='a sign that said "Cellar Cabaret" in wobbly paint, edged with feathers',
        place="above the curtain line",
        fragile=True,
        tumble="The sign tipped, the feathers flew, and the whole cellar sneezed with fluff.",
        after="One feather drifted onto the instigator's nose and stayed there.",
        chaos=2,
        tags={"feathers", "cabaret"},
    ),
    "pickle_lantern": Decoration(
        id="pickle_lantern",
        label="pickle lantern",
        phrase="a clean pickle jar with a paper lantern tucked inside",
        place="above the curtain line",
        fragile=True,
        tumble="The pickle lantern slipped free and bumped the floor with a sad plunk.",
        after="The paper lantern crumpled, but the jar did not shatter.",
        chaos=2,
        tags={"lantern", "jar"},
    ),
}

RESPONSES = {
    "step_ladder": Response(
        id="step_ladder",
        sense=3,
        power=3,
        text="brought the little step ladder down to the cellar and held it steady while the sign was tied properly",
        fail="brought the little step ladder down, but by then feathers and paper were already all over the floor",
        qa_text="used the little step ladder and held it steady while the decoration was tied properly",
        tags={"ladder", "help"},
    ),
    "grownup_reach": Response(
        id="grownup_reach",
        sense=3,
        power=2,
        text="reached up with calm hands, retied the decoration, and moved the silly perch out of the way",
        fail="reached up to fix it, but too many bits had already tumbled down and the whole stage needed rebuilding",
        qa_text="reached up and fixed the decoration with calm hands",
        tags={"help", "grownup"},
    ),
    "broom_hook": Response(
        id="broom_hook",
        sense=1,
        power=1,
        text="poked at the decoration with a broom until it caught by luck",
        fail="poked at the decoration with a broom and only stirred the mess more",
        qa_text="poked at it with a broom",
        tags={"broom"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Eli"]
TRAITS = ["careful", "sensible", "steady", "thoughtful", "curious", "cheerful"]
HELPER_ITEMS = ["kazoo", "red scarf", "paper tickets", "toy drum", "bow tie", "feather boa", ""]

KNOWLEDGE = {
    "cabaret": [
        (
            "What is a cabaret?",
            "A cabaret is a small show with songs, jokes, or little acts for an audience. It often feels cozy and playful instead of grand and formal.",
        )
    ],
    "cellar": [
        (
            "What is a cellar?",
            "A cellar is a room under a house, often down some stairs. People store things there because it is cool and out of the way.",
        )
    ],
    "whirly": [
        (
            "What does whirly mean?",
            "Whirly means something that spins or twirls around. A whirly thing can be fun, but it is not always steady for standing on.",
        )
    ],
    "ladder": [
        (
            "Why is a step ladder safer than a spinning stool?",
            "A step ladder is made for climbing and can stand steady on the floor. A spinning stool can wobble or turn when you do not want it to.",
        )
    ],
    "help": [
        (
            "Why should children ask for help with high things?",
            "High things can be hard to reach safely. A grown-up or a steady tool can help before a silly accident happens.",
        )
    ],
    "cleanup": [
        (
            "Why is it good to clean up a mess you made?",
            "Cleaning up shows responsibility. It helps make things right after a mistake.",
        )
    ],
}
KNOWLEDGE_ORDER = ["cabaret", "cellar", "whirly", "ladder", "help", "cleanup"]


def valid_perch(perch: Perch) -> bool:
    return perch.rolls


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def hazard_at_risk(perch: Perch, decoration: Decoration) -> bool:
    return perch.rolls and decoration.chaos >= 1


def mess_severity(decoration: Decoration, delay: int) -> int:
    return decoration.chaos + delay


def is_contained(response: Response, decoration: Decoration, delay: int) -> bool:
    return response.power >= mess_severity(decoration, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (4.0 if older else 0.0)
    return older and authority > SHOW_OFF_INIT


def predict_wobble(world: World, decoration_id: str) -> dict:
    sim = world.copy()
    _do_shortcut(sim, sim.get("perch"), sim.get(decoration_id), narrate=False)
    deco = sim.get(decoration_id)
    return {
        "wobble": sim.get("perch").meters["wobble"] >= THRESHOLD,
        "fallen": deco.meters["fallen"] >= THRESHOLD,
        "mess": sim.get("cellar").meters["mess"],
    }


def _do_shortcut(world: World, perch: Entity, decoration: Entity, narrate: bool = True) -> None:
    perch.meters["climbed"] += 1
    decoration.meters["being_hung"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"One rainy afternoon, {a.id} and {b.id} turned the cellar into {theme.scene}. "
        f"{theme.opener}"
    )
    world.say(
        f'"{theme.title_a} {a.id} and {theme.title_b} {b.id}!" {a.id} declared. '
        f'"Tonight we present {theme.act_name}!"'
    )
    world.say(theme.prop_line)


def need_height(world: World, b: Entity, decoration: Decoration) -> None:
    world.say(
        f"{b.id} looked up at {decoration.phrase}. It belonged {decoration.place}, "
        "but their arms were not nearly long enough."
    )


def tempt(world: World, a: Entity, perch: Perch) -> None:
    a.memes["show_off"] += 1
    world.say(
        f'Then {a.id} spotted {perch.phrase}. "{perch.label.capitalize()}!" '
        f"{a.pronoun().capitalize()} said. {perch.funny}"
    )
    world.say("For one cheerful second, the shortcut sounded like genius.")


def warn(world: World, b: Entity, a: Entity, perch: Perch, decoration: Decoration, parent: Entity) -> None:
    pred = predict_wobble(world, "decoration")
    b.memes["caution"] += 1
    world.facts["predicted_mess"] = pred["mess"]
    extra = ""
    if pred["fallen"]:
        extra = f" {b.pronoun().capitalize()} could almost picture feathers and paper on the floor."
    world.say(
        f'{b.id} wrinkled {b.pronoun("possessive")} nose. "{a.id}, that is not a standing thing. '
        f'{parent.label_word.capitalize()} says rolling things are for moving, not climbing. '
        f'If you use the {perch.label}, {decoration.label} could come right down."{extra}'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["show_off"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    rel = "big brother" if b.type == "boy" else "big sister"
    world.say(
        f'{a.id} opened {a.pronoun("possessive")} mouth to argue, then looked at {b.id}. '
        f"Because {b.id} was {a.pronoun('possessive')} {rel}, the warning landed harder than the joke."
    )
    world.say(
        f'"Fine," {a.id} sighed. "We will do it the non-whirly way." They carried the silly perch aside and went to ask '
        f"{parent.label_word} for help."
    )


def defy(world: World, a: Entity, b: Entity, perch: Perch) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"I will only be up for one tiny second," {a.id} said. Because {a.id} was the older one, '
            f"{b.id} could not stop {a.pronoun('object')} in time."
        )
    else:
        world.say(f'"I will only be up for one tiny second," {a.id} said, and grabbed the {perch.label}.')
    if not older:
        return
    world.say(f"Then {a.id} grabbed the {perch.label} anyway.")


def wobble_scene(world: World, a: Entity, decoration: Decoration) -> None:
    _do_shortcut(world, world.get("perch"), world.get("decoration"))
    world.say(
        f"{a.id} climbed up, reached for the string, and the cellar seemed to hold its breath."
    )
    if world.get("perch").meters["wobble"] >= THRESHOLD:
        world.say(
            f"The {world.get('perch').label} gave a whirly wiggle."
        )
    if world.get("decoration").meters["fallen"] >= THRESHOLD:
        world.say(f"{decoration.tumble} {decoration.after}")


def alarm(world: World, b: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.upper()}!" {b.id} yelped. "The stage is attacking itself!"')


def rescue(world: World, parent: Entity, response: Response, a: Entity, b: Entity, decoration: Decoration) -> None:
    world.get("decoration").meters["fallen"] = 0.0
    world.get("cellar").meters["mess"] = 0.0
    body = response.text
    world.say(
        f"{parent.label_word.capitalize()} came down the cellar steps, took one look, and {body}."
    )
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["trust"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'Soon {decoration.phrase} was finally hanging where it belonged, and the little cabaret looked proud instead of puffy.'
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["teamwork"] += 1
    world.say(
        f'{parent.label_word.capitalize()} did not scold first. {parent.pronoun().capitalize()} checked that everyone was safe, '
        f'then smiled a little and said, "A good joke is funny. A bad shortcut is only noisy. Next time, ask for help before the floor gets a vote."'
    )
    world.say(
        f"{a.id} looked at the mess they had nearly made and nodded. "
        f'"I wanted to look clever," {a.pronoun()} admitted. "I think steady is cleverer."'
    )
    helper_item = world.facts.get("helper_item")
    if helper_item:
        world.say(f"{b.id} handed over the {helper_item} like a tiny peace offering, and both children laughed.")


def restart_show(world: World, theme: Theme, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"At last the show began. {a.id} made a grand face, {b.id} bowed to a row of upside-down jars, and {theme.send_off}."
    )
    world.say(
        f"They finished with {theme.finale}. This time, the only thing spinning was the applause in their heads."
    )


def postpone(world: World, parent: Entity, response: Response, theme: Theme, a: Entity, b: Entity) -> None:
    body = response.fail
    world.say(
        f"{parent.label_word.capitalize()} hurried down the steps and {body}."
    )
    world.say(
        "Feathers, paper, and stage string had drifted into such a silly heap that the cabaret had to wait."
    )
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["sadness"] += 1
    world.say(
        f'{parent.label_word.capitalize()} said, "We can still have a show, but first we fix what fell and clean what we can."'
    )
    world.say(
        f"So they spent the rest of the afternoon sorting string, gathering fluff, and making the cellar neat again."
    )
    world.say(
        f"Only after supper did they try once more, with proper help and no whirly ideas at all. "
        f"The later cabaret was smaller, but everyone laughed harder because they had learned something."
    )


def tell(
    theme: Theme,
    perch_cfg: Perch,
    decoration_cfg: Decoration,
    response: Response,
    *,
    instigator: str,
    instigator_gender: str,
    cautioner: str,
    cautioner_gender: str,
    parent_type: str,
    trait: str,
    delay: int,
    instigator_age: int,
    cautioner_age: int,
    relation: str,
    trust: int,
    helper_item: str,
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            age=instigator_age,
            traits=["bold"],
            attrs={"relation": relation},
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            age=cautioner_age,
            traits=[trait],
            attrs={"relation": relation},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    cellar = world.add(
        Entity(
            id="cellar",
            type="room",
            label="cellar",
            phrase="the cellar",
            tags={"cellar"},
        )
    )
    perch = world.add(
        Entity(
            id="perch",
            type="perch",
            label=perch_cfg.label,
            phrase=perch_cfg.phrase,
            rollers=perch_cfg.rolls,
            steady=not perch_cfg.rolls,
            tags=set(perch_cfg.tags),
        )
    )
    decoration = world.add(
        Entity(
            id="decoration",
            type="decoration",
            label=decoration_cfg.label,
            phrase=decoration_cfg.phrase,
            overhead=True,
            fragile=decoration_cfg.fragile,
            attrs={"chaos": decoration_cfg.chaos},
            tags=set(decoration_cfg.tags),
        )
    )

    a.memes["show_off"] = SHOW_OFF_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)
    world.facts["helper_item"] = helper_item

    introduce(world, a, b, theme)
    need_height(world, b, decoration_cfg)

    world.para()
    tempt(world, a, perch_cfg)
    warn(world, b, a, perch_cfg, decoration_cfg, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, parent)
        world.para()
        rescue(world, parent, response, a, b, decoration_cfg)
        lesson(world, parent, a, b)
        world.para()
        restart_show(world, theme, a, b)
        severity = 0
        contained = True
    else:
        defy(world, a, b, perch_cfg)
        world.para()
        wobble_scene(world, a, decoration_cfg)
        alarm(world, b, parent)
        severity = mess_severity(decoration_cfg, delay)
        contained = is_contained(response, decoration_cfg, delay)

        world.para()
        if contained:
            rescue(world, parent, response, a, b, decoration_cfg)
            lesson(world, parent, a, b)
            world.para()
            restart_show(world, theme, a, b)
        else:
            postpone(world, parent, response, theme, a, b)

    outcome = "averted" if averted else ("tidied" if contained else "postponed")
    world.facts.update(
        theme=theme,
        perch_cfg=perch_cfg,
        decoration_cfg=decoration_cfg,
        response=response,
        instigator=a,
        cautioner=b,
        parent=parent,
        cellar=cellar,
        perch=perch,
        decoration=decoration,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
        helper_item=helper_item,
        fell=decoration.meters["fallen"] >= THRESHOLD,
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for theme_id in THEMES:
        for perch_id, perch in PERCHES.items():
            for deco_id, deco in DECORATIONS.items():
                if hazard_at_risk(perch, deco):
                    combos.append((theme_id, perch_id, deco_id))
    return combos


def explain_rejection(perch: Perch, decoration: Decoration) -> str:
    if not perch.rolls:
        return (
            f"(No story: {perch.phrase} does not create the silly wobble this world is about. "
            "Pick a rolling, whirly perch so there is a real shortcut to refuse.)"
        )
    if decoration.chaos < 1:
        return (
            f"(No story: {decoration.phrase} would not create a visible comic mess if it fell. "
            "Pick a decoration that can tumble and change the scene.)"
        )
    return "(No story: this combination does not create a reasonable cellar-cabaret problem.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a steadier fix such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response], DECORATIONS[params.decoration], params.delay)
    return "tidied" if contained else "postponed"


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
    theme = f["theme"]
    perch = f["perch_cfg"]
    deco = f["decoration_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a funny story for a 3-to-5-year-old that includes the words "whirly", '
        f'"cellar", and "cabaret", where children put on a tiny show and face a silly problem.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a comedy where {a.id} wants to use a {perch.label} in a cellar cabaret, but {b.id} stops the shortcut before anything falls.",
            f"Write a gentle moral story where children ask for help instead of showing off, and the cabaret ends happily with {theme.act_name}.",
        ]
    if outcome == "postponed":
        return [
            base,
            f"Tell a comic cautionary story where {a.id} ignores a warning, uses a {perch.label}, and turns the cabaret into a feathery mess before the show can begin.",
            "Write a humorous story with a clear lesson: a bad shortcut makes extra work, but people can still clean up and try again the right way.",
        ]
    return [
        base,
        f"Tell a funny story where {a.id} tries to hang {deco.phrase} in a cellar cabaret by standing on a {perch.label}, and a grown-up helps fix the mess properly.",
        "Write a comedy with a moral value about asking for help and choosing the steady way, ending in a successful little show.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    theme = f["theme"]
    perch = f["perch_cfg"]
    deco = f["decoration_cfg"]
    resp = f["response"]
    pair = pair_noun(a, b, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, making a tiny cellar cabaret together. Their {pw} comes to help when the silly shortcut goes wrong or is wisely avoided.",
        ),
        (
            "What were the children making?",
            f"They were building a little cabaret in the cellar and planning {theme.act_name}. The show gave them a reason to make the space look grand and funny.",
        ),
        (
            f"What did {a.id} want to use to reach the decoration?",
            f"{a.id} wanted to use {perch.phrase}. It seemed fast and clever for one second, but it was not a steady thing to stand on.",
        ),
        (
            f"Why did {b.id} warn {a.id}?",
            f"{b.id} warned that the {perch.label} could wobble and bring {deco.label} down. The danger was not just the climb itself, but the mess it could cause over the little stage.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What did {a.id} do after the warning?",
                f"{a.id} gave up the shortcut and asked for help instead. That choice kept the cabaret neat and showed that listening can be braver than showing off.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the decoration hung safely and the children performing their cabaret. The ending proves they changed because they chose the steady way from the start.",
            )
        )
    elif f["outcome"] == "tidied":
        qa.append(
            (
                f"What happened when {a.id} climbed up?",
                f"The {perch.label} gave a whirly wobble and {deco.label} came tumbling down. That silly fall turned the show problem into a real mess that needed help.",
            )
        )
        qa.append(
            (
                f"How did {pw} fix the problem?",
                f"{pw.capitalize()} {resp.qa_text}. The proper help solved the same problem safely and let the children finish the cabaret.",
            )
        )
        qa.append(
            (
                f"What lesson did {a.id} learn?",
                f"{a.id} learned that looking clever is not the same as being careful. Asking for help and using a steady tool was the wiser choice.",
            )
        )
    else:
        qa.append(
            (
                f"Could the cabaret start right away after the tumble?",
                f"No. Too many bits had fallen into a silly heap, so the show had to wait while everyone cleaned up and rebuilt the stage. The delay happened because the shortcut made more work than it saved.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended later, after cleanup and proper help, with a smaller but happier cabaret. The children still laughed, but only after learning to fix what they had knocked out of place.",
            )
        )
        qa.append(
            (
                "What moral value does the story teach?",
                "It teaches responsibility as well as caution. If you make a mess by showing off, you should help put things right and choose a better way next time.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"cabaret", "cellar", "help"}
    if "whirly" in f["perch_cfg"].id:
        tags.add("whirly")
    if f["response"].id == "step_ladder":
        tags.add("ladder")
    if f["outcome"] in {"tidied", "postponed"}:
        tags.add("cleanup")
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
        if e.rollers:
            bits.append("rollers=True")
        if e.steady:
            bits.append("steady=True")
        if e.overhead:
            bits.append("overhead=True")
        if e.fragile:
            bits.append("fragile=True")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:11} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="song",
        perch="whirly_stool",
        decoration="feather_sign",
        response="step_ladder",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=5,
        helper_item="kazoo",
    ),
    StoryParams(
        theme="magic",
        perch="toy_wagon",
        decoration="pickle_lantern",
        response="grownup_reach",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="father",
        trait="thoughtful",
        delay=0,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        trust=4,
        helper_item="red scarf",
    ),
    StoryParams(
        theme="dance",
        perch="whirly_stool",
        decoration="feather_sign",
        response="grownup_reach",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="mother",
        trait="cheerful",
        delay=1,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=3,
        helper_item="paper tickets",
    ),
    StoryParams(
        theme="song",
        perch="toy_wagon",
        decoration="paper_moon",
        response="step_ladder",
        instigator="Ella",
        instigator_gender="girl",
        cautioner="Rose",
        cautioner_gender="girl",
        parent="father",
        trait="sensible",
        delay=0,
        instigator_age=4,
        cautioner_age=6,
        relation="siblings",
        trust=6,
        helper_item="bow tie",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a whirly shortcut in a cellar cabaret. "
        "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--decoration", choices=DECORATIONS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra head start for the mess before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.perch and not PERCHES[args.perch].rolls:
        deco = DECORATIONS[args.decoration] if args.decoration else next(iter(DECORATIONS.values()))
        raise StoryError(explain_rejection(PERCHES[args.perch], deco))
    if args.perch and args.decoration:
        perch = PERCHES[args.perch]
        deco = DECORATIONS[args.decoration]
        if not hazard_at_risk(perch, deco):
            raise StoryError(explain_rejection(perch, deco))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.perch is None or combo[1] == args.perch)
        and (args.decoration is None or combo[2] == args.decoration)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, perch_id, deco_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    helper_item = rng.choice(HELPER_ITEMS)
    return StoryParams(
        theme=theme_id,
        perch=perch_id,
        decoration=deco_id,
        response=response_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
        helper_item=helper_item,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Invalid theme: {params.theme})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Invalid perch: {params.perch})")
    if params.decoration not in DECORATIONS:
        raise StoryError(f"(Invalid decoration: {params.decoration})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Invalid response: {params.response})")
    if not hazard_at_risk(PERCHES[params.perch], DECORATIONS[params.decoration]):
        raise StoryError(explain_rejection(PERCHES[params.perch], DECORATIONS[params.decoration]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        THEMES[params.theme],
        PERCHES[params.perch],
        DECORATIONS[params.decoration],
        RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
        helper_item=params.helper_item,
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


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(P, D) :- rolls(P), chaos(D, C), C >= 1.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(T, P, D) :- theme(T), perch(P), decoration(D), hazard(P, D).

% --- outcome inference -----------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), show_off_init(S), A > S.

severity(C + D) :- chosen_decoration(X), chaos(X, C), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(tidied) :- not averted, contained.
outcome(postponed) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        if perch.rolls:
            lines.append(asp.fact("rolls", perch_id))
    for deco_id, deco in DECORATIONS.items():
        lines.append(asp.fact("decoration", deco_id))
        lines.append(asp.fact("chaos", deco_id, deco.chaos))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("show_off_init", int(SHOW_OFF_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_decoration", params.decoration),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            continue

    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


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
        print(f"{len(combos)} compatible (theme, perch, decoration) combos:\n")
        for theme_id, perch_id, deco_id in combos:
            print(f"  {theme_id:8} {perch_id:13} {deco_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.instigator} & {p.cautioner}: {p.perch} under {p.decoration} ({p.theme}, {outcome_of(p)})"
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
