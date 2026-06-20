#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/outlet_craze_dim_turns_rhyme_comedy.py
=================================================================

A standalone storyworld about a silly pretend show, a light that goes "craze-dim,"
and a child tempted to poke a metal thing toward an outlet. The world model keeps
the comedy child-facing while still enforcing ordinary electrical common sense:
outlets are not for children, metal tools near them can spark, and the safe fix is
always to call a grown-up and use proper lights or batteries.

Run it
------
    python storyworlds/worlds/gpt-5.4/outlet_craze_dim_turns_rhyme_comedy.py
    python storyworlds/worlds/gpt-5.4/outlet_craze_dim_turns_rhyme_comedy.py --theme robots --forbidden fork --gadget disco_lamp
    python storyworlds/worlds/gpt-5.4/outlet_craze_dim_turns_rhyme_comedy.py --forbidden crayon
    python storyworlds/worlds/gpt-5.4/outlet_craze_dim_turns_rhyme_comedy.py --all --qa
    python storyworlds/worlds/gpt-5.4/outlet_craze_dim_turns_rhyme_comedy.py --verify
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
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    conductive: bool = False
    powered: bool = False
    gives_light: bool = False
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
    setup: str
    troupe: str
    goal: str
    chant: str
    finale: str


@dataclass
class Gadget:
    id: str
    label: str
    phrase: str
    dim_line: str
    need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Forbidden:
    id: str
    label: str
    phrase: str
    cry: str
    conductive: bool
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeLight:
    id: str
    label: str
    phrase: str
    glow: str
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


def _r_spark(world: World) -> list[str]:
    out: list[str] = []
    outlet = world.get("outlet")
    if outlet.meters["sparked"] < THRESHOLD:
        return out
    sig = ("spark", "outlet")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["danger"] += 1
    world.get("room").meters["dark"] += 1
    world.get("gadget").meters["dim"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__spark__")
    return out


CAUSAL_RULES = [
    Rule("spark", "physical", _r_spark),
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


def hazard_at_risk(forbidden: Forbidden, gadget: Gadget) -> bool:
    return forbidden.conductive and bool(gadget.need)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (3.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def outage_severity(delay: int, forbidden: Forbidden) -> int:
    base = 1 if forbidden.conductive else 0
    return base + delay


def is_handled(response: Response, delay: int, forbidden: Forbidden) -> bool:
    return response.power >= outage_severity(delay, forbidden)


def predict_spark(world: World) -> dict:
    sim = world.copy()
    _do_forbidden(sim, narrate=False)
    return {
        "spark": sim.get("outlet").meters["sparked"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
        "dark": sim.get("room").meters["dark"],
    }


def _do_forbidden(world: World, narrate: bool = True) -> None:
    world.get("outlet").meters["sparked"] += 1
    propagate(world, narrate=narrate)


def play_setup(world: World, a: Entity, b: Entity, theme: Theme, gadget: Gadget) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.get("gadget").gives_light = True
    world.get("gadget").powered = True
    world.say(
        f"After lunch, {a.id} and {b.id} turned the living room into {theme.scene}. "
        f"{theme.setup}"
    )
    world.say(
        f'"{theme.troupe}!" {a.id} cried. "Today we make {theme.goal}."'
    )
    world.say(
        f"They loved the way {gadget.phrase} made the room feel silly and bright."
    )


def craze_dim(world: World, b: Entity, theme: Theme, gadget: Gadget) -> None:
    world.get("gadget").meters["dim"] += 1
    world.say(
        f"Then {gadget.dim_line} The bright joke of the room went all craze-dim."
    )
    world.say(
        f'{b.id} blinked and sang, "{theme.chant}"'
    )


def tempt(world: World, a: Entity, forbidden: Forbidden) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} spotted {forbidden.phrase} and grinned. "{forbidden.cry} '
        f'I can fix it fast and slick!"'
    )
    world.say("For one tiny second, the plan sounded funny instead of risky.")


def warn(world: World, b: Entity, a: Entity, forbidden: Forbidden, parent: Entity) -> None:
    pred = predict_spark(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_dark"] = pred["dark"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f' "{forbidden.label.title()} and outlet do not rhyme with safe," {b.id} added.'
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, no way. '
        f'An outlet is for grown-ups, not for poking with {forbidden.label}. '
        f'It can spark and make the room turn dark."{extra}'
    )
    world.say(
        f'{b.id} tried a rhyme too: "No poke, no joke; step back from the wall socket."'
    )
    world.say(
        f"{parent.label_word.capitalize()} was in the next room, close enough to call."
    )


def defy(world: World, a: Entity, b: Entity, forbidden: Forbidden) -> None:
    a.memes["defiance"] += 1
    them = "them" if forbidden.plural else "it"
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"Just a teeny peeky tweak," {a.id} said, because {a.pronoun()} was the older sibling. '
            f"{b.id} did not like the plan, but {a.id} still darted toward the outlet with {them}."
        )
    else:
        world.say(
            f'"Quick and slick!" {a.id} said, and hurried toward the outlet with {them}.'
        )


def back_down(world: World, a: Entity, b: Entity, parent: Entity, theme: Theme) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} stopped with {b.id}\'s words still bouncing in {a.pronoun("possessive")} ears. '
        f'"Okay," {a.pronoun()} said. "A rhyme can save the day too."'
    )
    world.say(
        f"They called for {parent.label_word}, and the scary idea melted before anything touched the outlet."
    )
    world.say(
        f"{theme.finale}"
    )


def spark(world: World, forbidden: Forbidden, gadget: Gadget) -> None:
    _do_forbidden(world)
    world.say(
        f"{forbidden.label.title()} came too close to the outlet. Pop! A blue wink snapped, "
        f"the {gadget.label} hiccupped, and the room turned dimmer instead of brighter."
    )
    world.say(
        "Funny vanished. Scary arrived."
    )


def alarm(world: World, b: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.upper()}! HELP BY THE OUTLET!" {b.id} shouted.')
    world.say(
        f"{b.id} did the bravest thing: {b.pronoun()} stepped back instead of grabbing."
    )


def rescue(world: World, parent: Entity, response: Response, safe_light: SafeLight) -> None:
    world.get("outlet").meters["sparked"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.get("room").meters["dark"] = 0.0
    world.get("gadget").meters["dim"] = 0.0
    for kid in world.kids():
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came fast and {response.text}."
    )
    world.say(
        f"In one more moment, {parent.pronoun()} set out {safe_light.phrase} that {safe_light.glow}."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, forbidden: Forbidden) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt down and pulled both children close. '
        f'"I am glad you called me," {parent.pronoun()} said. '
        f'"{forbidden.label.title()} does not go in an outlet. Ever. '
        f'Outlets can bite with a spark, even when a room is just acting all craze-dim."'
    )
    world.say(
        '"We will call a grown-up, not make it up," the children answered together.'
    )


def safe_ending(world: World, a: Entity, b: Entity, theme: Theme, gadget: Gadget, safe_light: SafeLight) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"Soon the show was silly again. With {safe_light.label} glowing, {gadget.phrase} could rest."
    )
    world.say(
        f"{a.id} and {b.id} took turns at the stage instead of turns near the wall."
    )
    world.say(
        f'They sang, "{theme.chant}" and then bowed so low that even the sofa looked impressed.'
    )


def rescue_fail(world: World, parent: Entity, response: Response) -> None:
    world.get("room").meters["danger"] += 1
    world.get("room").meters["dark"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    world.say(
        f"{parent.label_word.capitalize()} {response.fail}, but the room stayed dark and jumpy for a minute."
    )
    world.say(
        "Nothing caught fire, but the grown-up still moved everyone away and made the game stop at once."
    )


def grim_but_safe(world: World, parent: Entity, a: Entity, b: Entity, safe_light: SafeLight) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say(
        f"The children sat on the hallway rug while {parent.label_word} checked the outlet and called for more help."
    )
    world.say(
        f"Later, they got {safe_light.phrase}, but the big show was over for the day."
    )
    world.say(
        f"{a.id} leaned on {b.id} and whispered, \"Next time we rhyme first and ask first.\""
    )


def tell(
    theme: Theme,
    gadget: Gadget,
    forbidden: Forbidden,
    safe_light: SafeLight,
    response: Response,
    instigator: str = "Max",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator, kind="character", type=instigator_gender, role="instigator",
        age=instigator_age, traits=["bold"], attrs={"relation": relation}
    ))
    b = world.add(Entity(
        id=cautioner, kind="character", type=cautioner_gender, role="cautioner",
        age=cautioner_age, traits=[trait], attrs={"relation": relation}
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, role="parent", label="the parent"
    ))
    room = world.add(Entity(id="room", type="room", label="the room"))
    outlet = world.add(Entity(id="outlet", type="outlet", label="the outlet"))
    show_gadget = world.add(Entity(
        id="gadget", type="gadget", label=gadget.label, powered=True, gives_light=True
    ))
    tool = world.add(Entity(
        id="tool", type="tool", label=forbidden.label, conductive=forbidden.conductive
    ))
    light = world.add(Entity(
        id="safe_light", type="light", label=safe_light.label, gives_light=True
    ))
    _ = room, outlet, show_gadget, tool, light

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)

    play_setup(world, a, b, theme, gadget)
    craze_dim(world, b, theme, gadget)

    world.para()
    tempt(world, a, forbidden)
    warn(world, b, a, forbidden, parent)

    averted = would_avert(relation, a.age, b.age, trait)

    if averted:
        back_down(world, a, b, parent, theme)
        world.para()
        rescue(world, parent, response, safe_light)
        lesson(world, parent, a, b, forbidden)
        world.para()
        safe_ending(world, a, b, theme, gadget, safe_light)
        handled = True
        severity = 0
    else:
        defy(world, a, b, forbidden)
        world.para()
        spark(world, forbidden, gadget)
        alarm(world, b, parent)
        severity = outage_severity(delay, forbidden)
        handled = is_handled(response, delay, forbidden)
        world.para()
        if handled:
            rescue(world, parent, response, safe_light)
            lesson(world, parent, a, b, forbidden)
            world.para()
            safe_ending(world, a, b, theme, gadget, safe_light)
        else:
            rescue_fail(world, parent, response)
            grim_but_safe(world, parent, a, b, safe_light)

    outcome = "averted" if averted else ("handled" if handled else "stopped")
    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        theme=theme,
        gadget_cfg=gadget,
        forbidden=forbidden,
        safe_light_cfg=safe_light,
        response=response,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
        spark=world.get("outlet").meters["sparked"] >= THRESHOLD or outcome in {"handled", "stopped"},
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


THEMES = {
    "robots": Theme(
        "robots",
        "a wobble-bobble robot theater",
        "A cardboard box became Robot Mayor, two cushions became drum hills, and a spoon became the microphone of magnificence.",
        "Beep-boop troupe",
        "the Grand Giggle Machine",
        "Dim, dim, don't be grim; we can laugh without a risky whim!",
        "The game paused, but their grins did not fall all the way off."
    ),
    "puppets": Theme(
        "puppets",
        "a noodle-doodle puppet stage",
        "A blanket over two chairs became a curtain, sock puppets wore button smiles, and a mixing bowl served as the royal gong.",
        "Sock and shock-free stars",
        "the Silliest Puppet Parade",
        "Dim, dim, never skim; ask for help when lights go slim!",
        "The curtain drooped a little, as if even it knew better than to rush a fix."
    ),
    "dinoband": Theme(
        "dinoband",
        "a stomp-chomp dinosaur concert",
        "A toy basket became the volcano, paper tails swished across the rug, and a whisk kept time like a tiny silver tail drum.",
        "Roar-more encore",
        "the Thunder-Lizard Song",
        "Dim, dim, no mad whim; safe first, then sing the dino hymn!",
        "The pretend volcano looked sleepy instead of scary, and that was much nicer."
    ),
}

GADGETS = {
    "disco_lamp": Gadget(
        "disco_lamp",
        "disco lamp",
        "the disco lamp",
        "But halfway through the first big wiggle, the disco lamp blinked and drooped like a tired jellybean.",
        "light for the show",
        tags={"lamp", "light"}
    ),
    "string_lights": Gadget(
        "string_lights",
        "string lights",
        "the string lights",
        "Then the string lights began to wink one by one until the room looked like a sleepy noodle.",
        "light for the show",
        tags={"lights", "light"}
    ),
    "star_sign": Gadget(
        "star_sign",
        "star sign",
        "the glowing star sign",
        "Then the glowing star sign fizzed down to a faint little twinkle, as if it had forgotten half its stars.",
        "light for the show",
        tags={"sign", "light"}
    ),
}

FORBIDDEN = {
    "fork": Forbidden(
        "fork", "fork", "a shiny fork", "A fork! One quick poke and we're back in business!", True,
        tags={"fork", "outlet", "electricity"}
    ),
    "key": Forbidden(
        "key", "key", "a house key", "The key can do the trick!", True,
        tags={"key", "outlet", "electricity"}
    ),
    "hairpin": Forbidden(
        "hairpin", "hairpin", "a silver hairpin", "This hairpin is skinny-winny!", True,
        tags={"hairpin", "outlet", "electricity"}
    ),
    "crayon": Forbidden(
        "crayon", "crayon", "a red crayon", "Maybe the crayon can help?", False,
        tags={"crayon"}
    ),
}

SAFE_LIGHTS = {
    "flashlight": SafeLight(
        "flashlight", "flashlight", "a flashlight", "clicked on bright as a tiny moon",
        tags={"flashlight", "safe_light"}
    ),
    "lantern": SafeLight(
        "lantern", "lantern", "a battery lantern", "glowed warm and round",
        tags={"lantern", "safe_light"}
    ),
    "headlamp": SafeLight(
        "headlamp", "head-lamp", "a head-lamp", "lit up their noses and everything else nearby",
        tags={"headlamp", "safe_light"}
    ),
}

RESPONSES = {
    "switch_off_and_cover": Response(
        "switch_off_and_cover", 3, 3,
        "switched the power off, moved the metal thing away, and snapped a safety cover over the outlet",
        "switched the power off, but the room still needed a grown-up repair before anyone could play there again",
        "switched the power off and put a safety cover on the outlet",
        tags={"outlet_cover", "electricity"}
    ),
    "move_back_and_flashlight": Response(
        "move_back_and_flashlight", 3, 2,
        "moved the children back, took the object away, and brought safe battery light instead of touching the outlet again",
        "moved the children back and brought safe light, but the room still had to stay dark until the outlet was checked",
        "moved the children back and used safe battery light instead",
        tags={"battery_light", "electricity"}
    ),
    "just_pull_hand": Response(
        "just_pull_hand", 1, 1,
        "yanked a child away by the sleeve",
        "pulled a child away by the sleeve, but that was not a calm or complete fix",
        "pulled the child away by the sleeve",
        tags={"bad_fix"}
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Max", "Ben", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]
TRAITS = ["careful", "cautious", "sensible", "steady", "curious", "clever"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for fid, forbidden in FORBIDDEN.items():
            for gid, gadget in GADGETS.items():
                if hazard_at_risk(forbidden, gadget):
                    combos.append((theme, fid, gid))
    return combos


@dataclass
class StoryParams:
    theme: str
    forbidden: str
    gadget: str
    safe_light: str
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
    seed: Optional[int] = None


KNOWLEDGE = {
    "outlet": [(
        "What is an outlet?",
        "An outlet is a wall socket where grown-ups plug in lights or other devices. Children should never poke things into it."
    )],
    "electricity": [(
        "Why is electricity dangerous?",
        "Electricity can move through wires and some metal objects very fast. It can shock you or make a spark, so children must ask a grown-up for help."
    )],
    "fork": [(
        "Why should a fork stay out of an outlet?",
        "A fork is metal, and metal can carry electricity. Putting a fork in an outlet can cause a spark or a shock."
    )],
    "key": [(
        "Why is a key not a toy for an outlet?",
        "A metal key can carry electricity too. That is why keys should stay in safe grown-up places, not near outlets."
    )],
    "hairpin": [(
        "Why can a hairpin be dangerous near an outlet?",
        "A metal hairpin is thin, but it is still metal. Thin does not mean safe around electricity."
    )],
    "flashlight": [(
        "What is a flashlight for?",
        "A flashlight gives light from batteries, so it can help you see without poking at a wall outlet. It is a safe tool when a grown-up says it is time to use one."
    )],
    "lantern": [(
        "What is a battery lantern?",
        "A battery lantern is a safe little light that glows without plugging metal things into a wall. It can help during a dark game or a power problem."
    )],
    "headlamp": [(
        "What is a head-lamp?",
        "A head-lamp is a light you wear on your head. It keeps your hands free and does not need you to poke around an outlet."
    )],
    "outlet_cover": [(
        "What does an outlet cover do?",
        "An outlet cover blocks the little holes so children cannot poke things inside. It helps make a room safer."
    )],
    "battery_light": [(
        "Why use battery light when a room gets dim?",
        "Battery lights can brighten a room without anyone touching an outlet in a risky way. They solve the seeing problem safely."
    )],
}
KNOWLEDGE_ORDER = [
    "outlet", "electricity", "fork", "key", "hairpin",
    "flashlight", "lantern", "headlamp", "outlet_cover", "battery_light",
]


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
    forbidden = f["forbidden"]
    gadget = f["gadget_cfg"]
    outcome = f["outcome"]
    safe_light = f["safe_light_cfg"]
    base = (
        f'Write a funny rhyming story for a 3-to-5-year-old where two children put on {theme.scene} '
        f'and a {gadget.label} goes craze-dim. Include the words "outlet", "craze-dim", and "turns".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a comedy story where {a.id} wants to use {forbidden.label} near an outlet, "
            f"but {b.id} stops the mistake with a rhyme and they call a grown-up instead.",
            f"Write a light, bouncy story where the children take turns safely after choosing {safe_light.label} over a risky wall outlet."
        ]
    if outcome == "handled":
        return [
            base,
            f"Tell a rhyming cautionary comedy where {a.id} ignores a warning and a little spark by the outlet makes the room turn dark, "
            f"but a calm grown-up fixes the problem safely.",
            f"Write a story that stays playful but teaches that {forbidden.label} and outlet do not belong together, then ends with safe light and taking turns."
        ]
    return [
        base,
        f"Tell a child-facing story where a risky poke near an outlet stops the whole show for the day, and the children learn to ask first and rhyme first.",
        f"Write a comedy with a sharper consequence: no one is hurt, but the game ends early because the grown-up has to make the room safe again."
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    theme = f["theme"]
    gadget = f["gadget_cfg"]
    forbidden = f["forbidden"]
    response = f["response"]
    safe_light = f["safe_light_cfg"]
    pw = parent.label_word
    pair = pair_noun(a, b, f.get("relation", "friends"))
    qa = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, and their {pw} who helps when the game turns risky. "
            f"They are putting on {theme.goal} in the living room."
        ),
        (
            "What was the problem at the start of the story?",
            f"The {gadget.label} that helped their show started to go craze-dim, so the room stopped feeling bright and funny. "
            f"That change is what made {a.id} want a too-fast fix."
        ),
        (
            f"Why did {b.id} tell {a.id} not to use the {forbidden.label} near the outlet?",
            f"{b.id} knew the outlet was not for children and that a metal {forbidden.label} could make a spark. "
            f"{b.pronoun().capitalize()} was warning about real danger, not just trying to spoil the game."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What did {a.id} do after the warning?",
            f"{a.id} backed away before touching the outlet, and the children called for {pw} instead. "
            f"Because they stopped in time, nothing sparked and the story could end in relief instead of fear."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with safe light, a calm lesson, and the children taking turns in their pretend show. "
            f"The ending proves the game changed from risky rushing to safe waiting."
        ))
    elif f["outcome"] == "handled":
        qa.append((
            "What happened when the forbidden object got too close to the outlet?",
            f"There was a little pop and the room turned dimmer instead of brighter. "
            f"The spark made everyone feel scared because the fast fix had turned into a bigger problem."
        ))
        qa.append((
            f"How did {pw} solve the problem?",
            f"{pw.capitalize()} {response.qa_text}. "
            f"Then {pw} used {safe_light.phrase}, which met the same need for light without another risky move."
        ))
        qa.append((
            "What changed by the end?",
            f"At the end, the children were still playful, but they were more careful too. "
            f"They took turns on the stage instead of taking chances near the outlet."
        ))
    else:
        qa.append((
            "Was anyone hurt?",
            f"No one was hurt, because the children stepped back and the grown-up took charge. "
            f"But the room still had to stay quiet and safe for the rest of the day."
        ))
        qa.append((
            "How did the story end?",
            f"The big pretend show stopped early while the grown-up checked the outlet and made the room safe. "
            f"The children still learned the lesson, but they did not get their silly ending until later."
        ))
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["forbidden"].tags)
    tags |= set(f["response"].tags)
    tags |= set(f["safe_light_cfg"].tags)
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
        flags = [name for name, on in (
            ("conductive", e.conductive),
            ("powered", e.powered),
            ("gives_light", e.gives_light),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        "robots", "fork", "disco_lamp", "flashlight", "switch_off_and_cover",
        "Max", "boy", "Lily", "girl", "mother", "careful", 0,
        instigator_age=6, cautioner_age=4, relation="siblings"
    ),
    StoryParams(
        "puppets", "key", "string_lights", "lantern", "move_back_and_flashlight",
        "Mia", "girl", "Ben", "boy", "father", "sensible", 0,
        instigator_age=5, cautioner_age=7, relation="siblings"
    ),
    StoryParams(
        "dinoband", "hairpin", "star_sign", "headlamp", "move_back_and_flashlight",
        "Theo", "boy", "Nora", "girl", "mother", "clever", 1,
        instigator_age=6, cautioner_age=5, relation="friends"
    ),
]


def explain_rejection(forbidden: Forbidden, gadget: Gadget) -> str:
    if not forbidden.conductive:
        return (
            f"(No story: {forbidden.label} is not the kind of metal object that creates the outlet hazard this world models. "
            f"Pick a conductive object like a fork, key, or hairpin.)"
        )
    if not gadget.need:
        return "(No story: this gadget gives the children no reason to fuss about power or light.)"
    return "(No story: this combination has no outlet hazard.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = " / ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a calmer, fuller fix such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "handled" if is_handled(RESPONSES[params.response], params.delay, FORBIDDEN[params.forbidden]) else "stopped"


ASP_RULES = r"""
hazard(F, G) :- conductive(F), gadget(G).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(T, F, G) :- theme(T), forbidden(F), gadget(G), hazard(F, G).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(3) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(B), A > B.

severity(1 + D) :- chosen_forbidden(F), conductive(F), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
handled :- resp_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(handled) :- not averted, handled.
outcome(stopped) :- not averted, not handled.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for fid, forbidden in FORBIDDEN.items():
        lines.append(asp.fact("forbidden", fid))
        if forbidden.conductive:
            lines.append(asp.fact("conductive", fid))
    for gid in GADGETS:
        lines.append(asp.fact("gadget", gid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
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
    scenario = "\n".join([
        asp.fact("chosen_forbidden", params.forbidden),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sensible, python_sensible = set(asp_sensible()), {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(80):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(seed)))
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
        if not sample.story or not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("smoke test produced incomplete sample")
        _ = sample.to_dict()
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming comedy storyworld about a dim show, an outlet hazard, and a safe grown-up fix."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--forbidden", choices=FORBIDDEN)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how long the grown-up takes to fully settle the outage")
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.forbidden and args.gadget:
        forbidden = FORBIDDEN[args.forbidden]
        gadget = GADGETS[args.gadget]
        if not hazard_at_risk(forbidden, gadget):
            raise StoryError(explain_rejection(forbidden, gadget))
    if args.forbidden and not FORBIDDEN[args.forbidden].conductive:
        gadget = GADGETS[args.gadget] if args.gadget else next(iter(GADGETS.values()))
        raise StoryError(explain_rejection(FORBIDDEN[args.forbidden], gadget))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.forbidden is None or combo[1] == args.forbidden)
        and (args.gadget is None or combo[2] == args.gadget)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, forbidden, gadget = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    safe_light = rng.choice(sorted(SAFE_LIGHTS))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    return StoryParams(
        theme, forbidden, gadget, safe_light, response,
        instigator, ig, cautioner, cg, parent, trait, delay,
        instigator_age=instigator_age, cautioner_age=cautioner_age, relation=relation
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        THEMES[params.theme],
        GADGETS[params.gadget],
        FORBIDDEN[params.forbidden],
        SAFE_LIGHTS[params.safe_light],
        RESPONSES[params.response],
        params.instigator,
        params.instigator_gender,
        params.cautioner,
        params.cautioner_gender,
        params.parent,
        params.trait,
        params.delay,
        params.instigator_age,
        params.cautioner_age,
        params.relation,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (theme, forbidden, gadget) combos:\n")
        for theme, forbidden, gadget in combos:
            print(f"  {theme:10} {forbidden:8} {gadget}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.forbidden} near outlet for {p.gadget} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
