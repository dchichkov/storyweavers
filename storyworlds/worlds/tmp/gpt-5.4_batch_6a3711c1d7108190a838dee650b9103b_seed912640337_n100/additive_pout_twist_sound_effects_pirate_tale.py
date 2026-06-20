#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/additive_pout_twist_sound_effects_pirate_tale.py
============================================================================

A standalone story world for a tiny pirate-tale domain: two children playing
pirates want a glowing "sea potion" to light a treasure hunt, one child is
tempted to use a mysterious boat-cleaning additive, and the safer path is to
ask a grown-up for a lantern or use moonlight instead.

The domain is built to satisfy the seed words "additive" and "pout" while
including a twist and plenty of sound effects. The twist is state-driven:
the "treasure" is not gold at all, but a message-and-snack surprise hidden by
the parent, and the ending image proves the children's idea of treasure
changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/additive_pout_twist_sound_effects_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/additive_pout_twist_sound_effects_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/additive_pout_twist_sound_effects_pirate_tale.py --verify
    python storyworlds/worlds/gpt-5.4/additive_pout_twist_sound_effects_pirate_tale.py -n 5 --seed 7 --qa
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    slippery: bool = False
    glowing: bool = False
    safe_light: bool = False
    edible: bool = False
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
    crew_word: str
    quest: str
    dark_place: str
    ride: str
    ending_image: str


@dataclass
class Additive:
    id: str
    label: str
    phrase: str
    where: str
    effect: str
    bubble_sound: str
    warning: str
    slippery_power: int
    sensible: int
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeLight:
    id: str
    label: str
    phrase: str
    shine: str
    sound: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    chest_phrase: str
    true_reveal: str
    edible: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Route:
    id: str
    label: str
    phrase: str
    dimness: int
    safe: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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
        return [e for e in self.entities.values() if e.role in ("captain", "mate")]

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


def _r_slippery_fear(world: World) -> list[str]:
    deck = world.get("deck")
    if deck.meters["slick"] < THRESHOLD:
        return []
    sig = ("slippery_fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
    world.get("deck").meters["risk"] += 1
    return ["__slick__"]


def _r_pout(world: World) -> list[str]:
    captain = world.get("captain")
    if captain.memes["blocked"] < THRESHOLD:
        return []
    sig = ("pout",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    captain.memes["pout"] += 1
    return ["__pout__"]


CAUSAL_RULES = [
    Rule("slippery_fear", "physical", _r_slippery_fear),
    Rule("pout", "social", _r_pout),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def route_needs_light(route: Route) -> bool:
    return route.dimness >= 2


def additive_is_reasonable(additive: Additive) -> bool:
    return additive.sensible >= SENSE_MIN


def can_light_route(light: SafeLight, route: Route) -> bool:
    return light.power >= route.dimness


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme in THEMES:
        for route_id, route in ROUTES.items():
            for light_id, light in SAFE_LIGHTS.items():
                for treasure_id in TREASURES:
                    if route_needs_light(route) and can_light_route(light, route):
                        combos.append((theme, route_id, light_id, treasure_id))
    return combos


def predict_additive(world: World, additive: Additive) -> dict:
    sim = world.copy()
    deck = sim.get("deck")
    deck.meters["slick"] += additive.slippery_power
    propagate(sim, narrate=False)
    return {
        "slick": deck.meters["slick"] >= THRESHOLD,
        "risk": deck.meters["risk"],
    }


def introduce(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"At sunset, {a.id} and {b.id} turned the porch into {theme.scene}. {theme.rig}"
    )
    world.say(
        f'"Captain {a.id} and Mate {b.id}!" {a.id} cried. "{theme.quest}!"'
    )


def need_light(world: World, b: Entity, route: Route, theme: Theme) -> None:
    world.say(
        f"But {route.phrase} was dusky and hard to see. The shadows under {theme.dark_place} "
        f"looked like they were hiding the next clue."
    )
    world.say(f'"We need light," {b.id} said.')


def tempt(world: World, a: Entity, additive: Additive) -> None:
    a.memes["bold"] += 1
    world.say(
        f'{a.id} pointed to {additive.phrase} {additive.where}. '
        f'"Let\'s use the additive! It says {additive.effect}."'
    )
    world.say(f'{additive.bubble_sound} went {a.id}\'s pirate voice, just imagining it.')


def warn(world: World, b: Entity, a: Entity, additive: Additive, parent: Entity) -> None:
    pred = predict_additive(world, additive)
    world.facts["predicted_risk"] = pred["risk"]
    extra = ""
    if pred["slick"]:
        extra = " It would make the boards slick, and pirates who slip do not find treasure."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. '
        f'"No, {a.id}. {parent.label_word.capitalize()} said {additive.warning}.{extra}"'
    )


def block_attempt(world: World, a: Entity, b: Entity, additive: Additive) -> None:
    a.memes["blocked"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{b.id} put a careful hand over the bottle before {a.id} could reach it.'
    )
    if a.memes["pout"] >= THRESHOLD:
        world.say(
            f'{a.id} made a big pirate pout and folded {a.pronoun("possessive")} arms. '
            f'"But it would go {additive.bubble_sound} and make sea-glow!"'
        )


def ask_parent(world: World, parent: Entity, light: SafeLight) -> None:
    parent.memes["helpfulness"] += 1
    world.say(
        f'Just then, {parent.label_word.capitalize()} came out with {light.phrase}. '
        f'"If you need light for a quest, use this instead," {parent.pronoun()} said.'
    )
    world.say(f'{light.sound} went the switch, and it {light.shine}.')


def travel(world: World, a: Entity, b: Entity, route: Route, light: SafeLight, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
    world.say(
        f'Together they followed {route.phrase}, with the {light.label} leading the way. '
        f'Tap-tap! went their pirate feet over the boards of {theme.ride}.'
    )


def reveal_twist(world: World, parent: Entity, treasure: Treasure) -> None:
    chest = world.get("chest")
    chest.meters["opened"] += 1
    world.say('Clink! The tiny chest popped open.')
    world.say(
        f"Inside was not a pile of gold at all. It was {treasure.true_reveal}"
    )
    if treasure.edible:
        world.say(
            f'{parent.label_word.capitalize()} laughed softly. '
            f'"A good crew needs a snack as much as silver," {parent.pronoun()} said.'
        )
    else:
        world.say(
            f'{parent.label_word.capitalize()} smiled. '
            f'"The best treasure is something made for you," {parent.pronoun()} said.'
        )


def ending(world: World, a: Entity, b: Entity, treasure: Treasure, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{a.id} stopped pouting and grinned at {b.id}. '
        f'"You were right. Safe light is better than slippery sparkle."'
    )
    world.say(
        f"They shared {treasure.label} together and {theme.ending_image}."
    )


def tell(
    theme: Theme,
    route: Route,
    additive: Additive,
    light: SafeLight,
    treasure: Treasure,
    captain_name: str = "Tom",
    captain_gender: str = "boy",
    mate_name: str = "Lily",
    mate_gender: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World()
    a = world.add(Entity(id=captain_name, kind="character", type=captain_gender, role="captain"))
    b = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="deck", type="deck", label="the porch boards"))
    world.add(Entity(id="chest", type="chest", label="the tiny chest"))
    world.add(Entity(id="light", type="light", label=light.label, safe_light=True, glowing=True))
    world.add(Entity(id="additive", type="bottle", label=additive.label))
    world.facts["twist_reveal"] = treasure.true_reveal

    introduce(world, a, b, theme)
    need_light(world, b, route, theme)

    world.para()
    tempt(world, a, additive)
    warn(world, b, a, additive, parent)
    block_attempt(world, a, b, additive)

    world.para()
    ask_parent(world, parent, light)
    travel(world, a, b, route, light, theme)

    world.para()
    reveal_twist(world, parent, treasure)
    ending(world, a, b, treasure, theme)

    world.facts.update(
        captain=a,
        mate=b,
        parent=parent,
        theme=theme,
        route=route,
        additive=additive,
        light_cfg=light,
        treasure=treasure,
        pouted=a.memes["pout"] >= THRESHOLD,
        used_safe_light=True,
        chest_opened=True,
    )
    return world


THEMES = {
    "porch_ship": Theme(
        "porch_ship",
        "a moonlit pirate harbor",
        "A laundry basket was their ship, a rolled towel was the sail, and a string of shells was the captain's bell.",
        "pirates",
        "Find the last chest before the tide turns",
        "the rocking chair",
        "their make-believe ship",
        "sat side by side on the porch-ship, swinging their feet while the safe light glowed between them",
    ),
    "blanket_deck": Theme(
        "blanket_deck",
        "a whispery pirate deck",
        "A blanket over two chairs made a cabin, a spoon became a spyglass, and a cardboard box became a sea chest.",
        "pirates",
        "Follow the map to the hidden chest",
        "the blanket cave",
        "their make-believe deck",
        "curled up under the blanket-deck, nibbling treasure and listening to the night bugs sing",
    ),
}

ADDITIVES = {
    "bubble_boat_additive": Additive(
        "bubble_boat_additive",
        "bubble boat additive",
        "a bottle of bubble boat additive",
        "on the washing shelf",
        "add sparkle to old wood",
        "Fssshhh!",
        "the additive is for cleaning boats, not for pirate play",
        slippery_power=2,
        sensible=1,
        tags={"additive", "slippery"},
    ),
    "shine_additive": Additive(
        "shine_additive",
        "shine additive",
        "a bottle of shine additive",
        "by the mop bucket",
        "make dull boards shine",
        "Glup-glup!",
        "the additive is for grown-up cleaning jobs, not for games",
        slippery_power=2,
        sensible=1,
        tags={"additive", "slippery"},
    ),
}

SAFE_LIGHTS = {
    "lantern": SafeLight(
        "lantern",
        "lantern",
        "a little camping lantern",
        "glowed warm as butter",
        "Click!",
        power=3,
        tags={"lantern", "safe_light"},
    ),
    "flashlight": SafeLight(
        "flashlight",
        "flashlight",
        "a sturdy flashlight",
        "shone bright as a silver fish",
        "Click-click!",
        power=3,
        tags={"flashlight", "safe_light"},
    ),
    "headlamp": SafeLight(
        "headlamp",
        "head-lamp",
        "a head-lamp with a soft band",
        "spilled a neat white circle ahead",
        "Snick!",
        power=2,
        tags={"headlamp", "safe_light"},
    ),
}

TREASURES = {
    "cookies_note": Treasure(
        "cookies_note",
        "star cookies and a folded note",
        "a tiny shell-painted chest",
        "star cookies and a folded note from Parent that said, \"Brave crews use safe tools.\"",
        edible=True,
        tags={"snack", "note", "twist"},
    ),
    "berries_map": Treasure(
        "berries_map",
        "sweet berries and a new map",
        "a little rope-handled chest",
        "a small cloth bag of sweet berries and a new pirate map drawn in blue crayon.",
        edible=True,
        tags={"snack", "map", "twist"},
    ),
    "bracelet_letter": Treasure(
        "bracelet_letter",
        "a bead bracelet and a letter",
        "a tiny brass-look chest",
        "a bead bracelet for each child and a letter that called them the kindest crew on the porch sea.",
        edible=False,
        tags={"gift", "letter", "twist"},
    ),
}

ROUTES = {
    "under_chair": Route(
        "under_chair",
        "under the rocking chair",
        "the dark lane under the rocking chair",
        dimness=2,
        safe=True,
        tags={"dark", "porch"},
    ),
    "blanket_tunnel": Route(
        "blanket_tunnel",
        "through the blanket tunnel",
        "the dim tunnel under the blanket",
        dimness=2,
        safe=True,
        tags={"dark", "blanket"},
    ),
    "crate_corner": Route(
        "crate_corner",
        "past the crate corner",
        "the shadowy corner behind the old crate",
        dimness=3,
        safe=True,
        tags={"dark", "corner"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Maya", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]


@dataclass
class StoryParams:
    theme: str
    route: str
    additive: str
    light: str
    treasure: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    parent: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "additive": [
        (
            "What is an additive?",
            "An additive is something you mix into something else to change it a little. Some additives are only for grown-up jobs, so children should not use them without help.",
        )
    ],
    "slippery": [
        (
            "Why are slippery boards dangerous?",
            "Slippery boards are dangerous because your feet can slide out from under you. A fast slip can make you fall before you are ready.",
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light that glows and helps you see in the dark. A safe lantern gives light without needing children to use unsafe grown-up things.",
        )
    ],
    "flashlight": [
        (
            "What does a flashlight do?",
            "A flashlight makes a bright beam so you can see where you are going. It is a safe way to explore dark places.",
        )
    ],
    "headlamp": [
        (
            "What is a head-lamp?",
            "A head-lamp is a small light you wear on your head. It keeps your hands free while you look around.",
        )
    ],
    "safe_light": [
        (
            "Why is safe light better for a game than a slippery cleaning thing?",
            "Safe light helps you see without making the floor dangerous. A game stays fun when the players can move safely.",
        )
    ],
    "note": [
        (
            "Can a note be treasure?",
            "Yes. Treasure does not always have to be gold. A kind note can feel special because it was made just for you.",
        )
    ],
    "snack": [
        (
            "Why can sharing a snack feel like treasure?",
            "Sharing a snack can feel like treasure because it is tasty and joyful, and everyone gets to enjoy it together. Sometimes the happy surprise matters more than shiny coins.",
        )
    ],
    "gift": [
        (
            "Can a small gift be a treasure?",
            "Yes. A small gift can be a treasure when it shows love or thoughtfulness. The value is in what it means, not just what it costs.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "additive",
    "slippery",
    "lantern",
    "flashlight",
    "headlamp",
    "safe_light",
    "note",
    "snack",
    "gift",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["captain"]
    b = f["mate"]
    add = f["additive"]
    route = f["route"]
    treasure = f["treasure"]
    light = f["light_cfg"]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the words "{add.label}" and "pout".',
        f"Tell a gentle pirate tale where {a.id} wants to use {add.label} to explore {route.label}, but {b.id} stops the idea and a safe light saves the quest.",
        f"Write a story with sound effects and a twist ending where the treasure is really {treasure.label}, and the children finish the adventure with a {light.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["captain"]
    b = f["mate"]
    parent = f["parent"]
    route = f["route"]
    add = f["additive"]
    light = f["light_cfg"]
    treasure = f["treasure"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two pretend pirates, {a.id} and {b.id}, and their {parent.label_word} who helped with the quest.",
        ),
        (
            "Why did the children think they needed something extra?",
            f"They wanted to search {route.label}, but that part of the game was too dim to see well. The darkness made {a.id} think of using {add.label} in a silly pirate way.",
        ),
        (
            f"What did {b.id} say about the additive?",
            f"{b.id} warned that {add.label} was for grown-up cleaning, not for pirate play. {b.pronoun().capitalize()} also knew it could make the boards slippery and turn the game unsafe.",
        ),
    ]
    if f.get("pouted"):
        qa.append(
            (
                f"Why did {a.id} pout?",
                f"{a.id} pouted because {b.id} stopped {a.pronoun('object')} from grabbing the additive. {a.pronoun().capitalize()} wanted the adventure right away and did not like being told no, even though the warning was sensible.",
            )
        )
    qa.extend(
        [
            (
                "How did the problem get solved?",
                f"Their {parent.label_word} brought {light.phrase}, and that gave them the light they really needed. The safe tool fixed the problem without making the porch slippery.",
            ),
            (
                "What was the twist at the end?",
                f"The chest did not hold gold at all. Instead it held {treasure.label}, which showed that the real treasure was a kind surprise waiting for them.",
            ),
            (
                "What changed by the end of the story?",
                f"At first, {a.id} cared about flashy pirate sparkle, but by the end both children cared more about being safe and sharing the treasure together. The ending proves it because {a.id} stops pouting and gladly enjoys the safer adventure.",
            )
        ]
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["additive"].tags) | set(world.facts["light_cfg"].tags) | set(world.facts["treasure"].tags)
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
        flags = [n for n, on in (("slippery", e.slippery), ("glowing", e.glowing), ("safe_light", e.safe_light), ("edible", e.edible)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("porch_ship", "under_chair", "bubble_boat_additive", "lantern", "cookies_note", "Tom", "boy", "Lily", "girl", "mother"),
    StoryParams("blanket_deck", "blanket_tunnel", "shine_additive", "flashlight", "bracelet_letter", "Max", "boy", "Mia", "girl", "father"),
    StoryParams("porch_ship", "crate_corner", "bubble_boat_additive", "headlamp", "berries_map", "Sam", "boy", "Nora", "girl", "mother"),
]


def explain_additive(additive_id: str) -> str:
    add = ADDITIVES[additive_id]
    return (
        f"(No story: refusing {add.label}. In this world it is a grown-up cleaning additive that makes boards slick, so it is not a sensible tool for a pirate quest. Use a safe light instead.)"
    )


ASP_RULES = r"""
needs_light(R) :- route(R), dimness(R, D), D >= 2.
can_light(L, R) :- light(L), route(R), light_power(L, P), dimness(R, D), P >= D.
valid(T, R, L, Tr) :- theme(T), route(R), light(L), treasure(Tr), needs_light(R), can_light(L, R).

bad_additive(A) :- additive(A), additive_sense(A, S), sense_min(M), S < M.
reasonable_additive(A) :- additive(A), additive_sense(A, S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("dimness", rid, route.dimness))
    for lid, light in SAFE_LIGHTS.items():
        lines.append(asp.fact("light", lid))
        lines.append(asp.fact("light_power", lid, light.power))
    for aid, add in ADDITIVES.items():
        lines.append(asp.fact("additive", aid))
        lines.append(asp.fact("additive_sense", aid, add.sensible))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_bad_additives() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show bad_additive/1."))
    return sorted(a for (a,) in asp.atoms(model, "bad_additive"))


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

    bad_py = sorted(aid for aid, add in ADDITIVES.items() if not additive_is_reasonable(add))
    bad_asp = asp_bad_additives()
    if bad_py == bad_asp:
        print(f"OK: additive reasonableness matches ({bad_py}).")
    else:
        rc = 1
        print(f"MISMATCH in additive reasonableness: python={bad_py} clingo={bad_asp}")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "pout" not in sample.story.lower():
            raise StoryError("smoke test story missing required content")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate children, a foolish additive idea, and a safer glowing twist."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--additive", choices=ADDITIVES)
    ap.add_argument("--light", choices=SAFE_LIGHTS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    pool = [n for n in pool if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    additive_id = args.additive or rng.choice(sorted(ADDITIVES))
    if args.additive and not additive_is_reasonable(ADDITIVES[args.additive]):
        raise StoryError(explain_additive(args.additive))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.route is None or c[1] == args.route)
        and (args.light is None or c[2] == args.light)
        and (args.treasure is None or c[3] == args.treasure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, route, light, treasure = rng.choice(sorted(combos))
    captain, cg = _pick_kid(rng)
    mate, mg = _pick_kid(rng, avoid=captain)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        theme=theme,
        route=route,
        additive=additive_id,
        light=light,
        treasure=treasure,
        captain=captain,
        captain_gender=cg,
        mate=mate,
        mate_gender=mg,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if not additive_is_reasonable(ADDITIVES[params.additive]):
        # The story knows about bad additives but still allows them as the foolish temptation.
        # Refuse only if the user explicitly pinned one in resolve_params; curated/default stories
        # keep them as the unsafe object inside the plot.
        pass

    world = tell(
        THEMES[params.theme],
        ROUTES[params.route],
        ADDITIVES[params.additive],
        SAFE_LIGHTS[params.light],
        TREASURES[params.treasure],
        params.captain,
        params.captain_gender,
        params.mate,
        params.mate_gender,
        params.parent,
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
        print(asp_program("", "#show valid/4.\n#show bad_additive/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, route, light, treasure) combos:\n")
        for theme, route, light, treasure in combos:
            print(f"  {theme:12} {route:14} {light:10} {treasure}")
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
            header = f"### {p.captain} & {p.mate}: {p.route} with {p.light} ({p.treasure})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
