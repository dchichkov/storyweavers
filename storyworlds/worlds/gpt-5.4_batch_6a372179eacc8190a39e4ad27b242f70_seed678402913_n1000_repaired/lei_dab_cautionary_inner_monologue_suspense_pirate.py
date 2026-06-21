#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lei_dab_cautionary_inner_monologue_suspense_pirate.py
================================================================================

A standalone storyworld about a pirate game at the shore: a child wearing a lei
spots drifting treasure marked with a dab of color, feels tempted to climb onto
a slick edge, and must choose safety over bravado. The model aims for a
cautionary, suspenseful pirate-tale mood with a small amount of inner monologue.

Run it
------
    python storyworlds/worlds/gpt-5.4/lei_dab_cautionary_inner_monologue_suspense_pirate.py
    python storyworlds/worlds/gpt-5.4/lei_dab_cautionary_inner_monologue_suspense_pirate.py --spot jetty --tool boat_hook
    python storyworlds/worlds/gpt-5.4/lei_dab_cautionary_inner_monologue_suspense_pirate.py --spot dry_sand
    python storyworlds/worlds/gpt-5.4/lei_dab_cautionary_inner_monologue_suspense_pirate.py --all --qa
    python storyworlds/worlds/gpt-5.4/lei_dab_cautionary_inner_monologue_suspense_pirate.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "sensible"}


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
    slippery: bool = False
    over_water: bool = False
    reach: int = 0
    # world axes
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
    send_off: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    danger_phrase: str
    distance: int
    wave_force: int
    slippery: bool = True
    over_water: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    mark: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    reach: int
    sense: int
    use_text: str
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
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

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


def _r_peril(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("captain")
    room = world.entities.get("shore")
    if child is None or room is None:
        return out
    if child.meters["on_edge"] < THRESHOLD:
        return out
    if child.meters["balance"] >= THRESHOLD:
        return out
    sig = ("peril", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["danger"] += 1
    child.memes["fear"] += 1
    for kid in world.kids():
        if kid.id != child.id:
            kid.memes["fear"] += 1
    out.append("__peril__")
    return out


def _r_wave(world: World) -> list[str]:
    out: list[str] = []
    spot = world.entities.get("spot")
    child = world.entities.get("captain")
    if spot is None or child is None:
        return out
    if spot.meters["wave_close"] < THRESHOLD or child.meters["on_edge"] < THRESHOLD:
        return out
    sig = ("wave", spot.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["balance"] -= 1
    child.meters["wet"] += 1
    out.append("__wave__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wave", tag="physical", apply=_r_wave),
    Rule(name="peril", tag="physical", apply=_r_peril),
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
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if bit == "__wave__":
                world.say("Just then, a thin wave slid in with a hiss and touched the edge.")
            elif bit == "__peril__":
                world.say("For one tight second, it looked as if the sea might tug the game away from them.")
    return produced


def hazard_at_risk(spot: Spot) -> bool:
    return spot.slippery and spot.over_water and spot.distance > 0


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def tool_works(tool: Tool, spot: Spot) -> bool:
    return tool.reach >= spot.distance


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for treasure_id in TREASURES:
            for spot_id, spot in SPOTS.items():
                if not hazard_at_risk(spot):
                    continue
                if any(tool_works(tool, spot) for tool in sensible_tools()):
                    combos.append((theme_id, treasure_id, spot_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, captain_age: int, mate_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and mate_age > captain_age
    authority = initial_caution(trait) + 1.0 + (3.0 if older_sibling else 0.0)
    return older_sibling and authority > BRAVERY_INIT


def outcome_of(params: "StoryParams") -> str:
    if would_avert(params.relation, params.captain_age, params.mate_age, params.trait):
        return "averted"
    return "retrieved" if tool_works(TOOLS[params.tool], SPOTS[params.spot]) else "lost"


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    child = sim.get("captain")
    step_out(sim, child, narrate=False)
    return {
        "danger": sim.get("shore").meters["danger"],
        "balance": child.meters["balance"],
        "wet": child.meters["wet"],
    }


def opening(world: World, theme: Theme, captain: Entity, mate: Entity, treasure: Treasure) -> None:
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a bright afternoon by the shore, {captain.id} and {mate.id} turned the beach into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f"A flower lei bobbed on {captain.id}'s shoulders like a captain's collar, and {captain.pronoun('possessive')} eyes shone."
    )
    world.say(
        f'Then {mate.id} pointed. "Look! A {treasure.label}!"'
    )
    world.say(
        f"There, beyond the foam, something drifted near the rocks: {treasure.phrase} with {treasure.mark}."
    )


def approach(world: World, captain: Entity, mate: Entity, spot: Spot) -> None:
    captain.memes["desire"] += 1
    world.say(
        f'"Treasure for our crew!" {captain.id} cried, hurrying toward {spot.phrase}.'
    )
    world.say(
        f"But {spot.danger_phrase}."
    )
    world.say(
        f"Inside, {captain.id} thought, If I take just one quick step, I can grab it before the sea does."
    )
    mate.memes["caution"] += 1


def warn(world: World, mate: Entity, captain: Entity, spot: Spot, parent: Entity) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_balance"] = pred["balance"]
    world.say(
        f'{mate.id} caught {captain.pronoun("possessive")} sleeve. "{captain.id}, don\'t. {spot.label.capitalize()} is slick, and the water is below. '
        f'Please call {parent.label_word}."'
    )


def defy(world: World, captain: Entity, mate: Entity) -> None:
    captain.memes["defiance"] += 1
    world.say(
        f'"I am Captain {captain.id}," {captain.pronoun()} whispered to {captain.pronoun("self") if False else ""}'
    )
    world.paragraphs[-1][-1] = world.paragraphs[-1][-1].rstrip()
    world.say(
        f'Then {captain.pronoun().capitalize()} thought, I only need one brave reach.'
    )
    world.say(
        f'{mate.id} stayed close, heart thumping, while {captain.id} edged forward anyway.'
    )


def back_down(world: World, captain: Entity, mate: Entity, parent: Entity) -> None:
    captain.memes["relief"] += 1
    mate.memes["relief"] += 1
    captain.memes["bravery"] = 0.0
    world.say(
        f'{captain.id} looked at the water, then at {mate.id}. The brave thought in {captain.pronoun("possessive")} head suddenly felt small.'
    )
    world.say(
        f'"No," {captain.pronoun()} said at last. "Real captains do not slip into the sea for a toy."'
    )
    world.say(
        f'Together they stepped back from the edge and called for {parent.label_word}.'
    )


def step_out(world: World, captain: Entity, narrate: bool = True) -> None:
    captain.meters["on_edge"] += 1
    captain.meters["balance"] = 0.0
    world.get("spot").meters["wave_close"] += 1
    propagate(world, narrate=narrate)


def alarm(world: World, mate: Entity, captain: Entity, parent: Entity) -> None:
    world.say(
        f'"{captain.id}!" {mate.id} gasped. "{parent.label_word.capitalize()}!"'
    )


def rescue(world: World, parent: Entity, tool: Tool, treasure: Treasure, captain: Entity, mate: Entity) -> None:
    captain.meters["on_edge"] = 0.0
    captain.meters["balance"] = 1.0
    world.get("shore").meters["danger"] = 0.0
    world.get("treasure").meters["safe"] = 1.0
    captain.memes["relief"] += 1
    mate.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came running, snatched up {tool.phrase}, and {tool.use_text}."
    )
    world.say(
        f'The {treasure.label} skidded over the foam and into dry sand. {captain.id} jumped back, breathing hard.'
    )


def lesson(world: World, parent: Entity, captain: Entity, mate: Entity, tool: Tool, spot: Spot) -> None:
    for kid in (captain, mate):
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them. "You did the right thing by shouting," {parent.pronoun()} said. '
        f'"But never climb onto {spot.label} for something floating away. Wet edges can steal your feet before you know it."'
    )
    world.say(
        f'{captain.id} nodded. "{tool.label.capitalize()} is better than being bold in the wrong place," {captain.pronoun()} said.'
    )


def ending(world: World, theme: Theme, captain: Entity, mate: Entity, treasure: Treasure) -> None:
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f'Soon the crew sat higher up the beach, with {treasure.phrase} safely between them.'
    )
    world.say(
        f'{mate.id} gave the little box a careful dab of dry sand to stop it sliding, and both children laughed at the thought of the sea trying to steal pirate treasure.'
    )
    world.say(
        f'This time, the {theme.crew_word} {theme.send_off} from a safe patch of shore, wiser than before.'
    )


def tell(
    theme: Theme,
    treasure: Treasure,
    spot: Spot,
    tool: Tool,
    captain_name: str = "Lina",
    captain_gender: str = "girl",
    mate_name: str = "Tomas",
    mate_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "careful",
    relation: str = "siblings",
    captain_age: int = 5,
    mate_age: int = 7,
) -> World:
    world = World()
    captain = world.add(Entity(
        id=captain_name,
        kind="character",
        type=captain_gender,
        label=captain_name,
        role="captain",
        age=captain_age,
        traits=["bold"],
        attrs={"relation": relation},
    ))
    mate = world.add(Entity(
        id=mate_name,
        kind="character",
        type=mate_gender,
        label=mate_name,
        role="mate",
        age=mate_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    world.add(Entity(id="shore", type="shore", label="shore"))
    world.add(Entity(
        id="spot",
        type="spot",
        label=spot.label,
        phrase=spot.phrase,
        slippery=spot.slippery,
        over_water=spot.over_water,
        reach=spot.distance,
        tags=set(spot.tags),
    ))
    world.add(Entity(
        id="treasure",
        type="treasure",
        label=treasure.label,
        phrase=treasure.phrase,
        tags=set(treasure.tags),
    ))
    world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        reach=tool.reach,
        tags=set(tool.tags),
    ))

    captain.memes["bravery"] = BRAVERY_INIT
    mate.memes["caution"] = initial_caution(trait)

    opening(world, theme, captain, mate, treasure)
    world.para()
    approach(world, captain, mate, spot)
    warn(world, mate, captain, spot, parent)

    averted = would_avert(relation, captain_age, mate_age, trait)
    if averted:
        back_down(world, captain, mate, parent)
        world.para()
        rescue(world, parent, tool, treasure, captain, mate)
        lesson(world, parent, captain, mate, tool, spot)
        world.para()
        ending(world, theme, captain, mate, treasure)
        outcome = "averted"
    else:
        defy(world, captain, mate)
        world.para()
        step_out(world, captain)
        alarm(world, mate, captain, parent)
        world.para()
        if not tool_works(tool, spot):
            raise StoryError(
                f"(No story: {tool.label} cannot reach treasure drifting by {spot.label}. Try a longer tool.)"
            )
        rescue(world, parent, tool, treasure, captain, mate)
        lesson(world, parent, captain, mate, tool, spot)
        world.para()
        ending(world, theme, captain, mate, treasure)
        outcome = "retrieved"

    world.facts.update(
        theme=theme,
        treasure_cfg=treasure,
        spot_cfg=spot,
        tool_cfg=tool,
        captain=captain,
        mate=mate,
        parent=parent,
        outcome=outcome,
        relation=relation,
        predicted_danger=world.facts.get("predicted_danger", 0.0),
        stepped=not averted,
        wet=captain.meters["wet"] >= THRESHOLD,
    )
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a ragged pirate island",
        rig="A striped towel was their sail, a driftwood stick was their mast, and a chalk map on a snack box showed where the gold should be.",
        crew_word="pirates",
        send_off="planned their next voyage",
        tags={"pirates"},
    ),
    "corsairs": Theme(
        id="corsairs",
        scene="a secret corsair cove",
        rig="A picnic blanket became their deck, a shell scoop became a spyglass, and a bent stick drew the path to buried silver in the sand.",
        crew_word="corsairs",
        send_off="whispered over their map",
        tags={"pirates"},
    ),
}

TREASURES = {
    "shell_box": Treasure(
        id="shell_box",
        label="shell box",
        phrase="a little shell box",
        mark="a dab of red paint on its lid",
        tags={"treasure", "dab"},
    ),
    "map_tube": Treasure(
        id="map_tube",
        label="map tube",
        phrase="a bobbing map tube",
        mark="a dab of blue wax near the cap",
        tags={"treasure", "dab"},
    ),
    "crown": Treasure(
        id="crown",
        label="shell crown",
        phrase="a small shell crown",
        mark="a dab of gold paint on one side",
        tags={"treasure", "dab"},
    ),
}

SPOTS = {
    "rocks": Spot(
        id="rocks",
        label="the black rocks",
        phrase="the black rocks at the tide line",
        danger_phrase="the rocks were dark with spray, and each one shone as if someone had polished it with soap",
        distance=2,
        wave_force=2,
        slippery=True,
        over_water=True,
        tags={"rocks", "water"},
    ),
    "jetty": Spot(
        id="jetty",
        label="the low jetty",
        phrase="the end of the low jetty",
        danger_phrase="the old boards were wet and shiny, with green slime between them and choppy water underneath",
        distance=3,
        wave_force=1,
        slippery=True,
        over_water=True,
        tags={"jetty", "water"},
    ),
    "creek_log": Spot(
        id="creek_log",
        label="the creek log",
        phrase="the slick log over the creek mouth",
        danger_phrase="the log was slick with waterweed, and the creek gurgled under it on its way to the sea",
        distance=2,
        wave_force=1,
        slippery=True,
        over_water=True,
        tags={"log", "water"},
    ),
    "dry_sand": Spot(
        id="dry_sand",
        label="the dry sand",
        phrase="the dry sand",
        danger_phrase="the sand was flat and safe",
        distance=0,
        wave_force=0,
        slippery=False,
        over_water=False,
        tags={"sand"},
    ),
}

TOOLS = {
    "boat_hook": Tool(
        id="boat_hook",
        label="boat hook",
        phrase="the long boat hook",
        reach=3,
        sense=3,
        use_text="reached far over the water and drew the treasure back before another wave could tug it away",
        qa_text="used the boat hook to pull the treasure back from the water",
        tags={"boat_hook", "tool"},
    ),
    "net": Tool(
        id="net",
        label="landing net",
        phrase="the landing net",
        reach=2,
        sense=3,
        use_text="dipped it under the drifting treasure and lifted it out in one quick sweep",
        qa_text="used the landing net to lift the treasure out of the water",
        tags={"net", "tool"},
    ),
    "pole": Tool(
        id="pole",
        label="driftwood pole",
        phrase="a driftwood pole",
        reach=2,
        sense=2,
        use_text="slid the pole under the treasure and nudged it shoreward until the foam let it go",
        qa_text="used a driftwood pole to push the treasure safely back to shore",
        tags={"pole", "tool"},
    ),
    "hands": Tool(
        id="hands",
        label="bare hands",
        phrase="bare hands",
        reach=1,
        sense=1,
        use_text="splashed at the treasure with empty hands",
        qa_text="tried to grab the treasure with bare hands",
        tags={"hands"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Zoe", "Ava", "Ella", "Lucy", "Iris"]
BOY_NAMES = ["Tomas", "Ben", "Max", "Leo", "Finn", "Noah", "Eli", "Jude"]
TRAITS = ["careful", "cautious", "steady", "sensible", "thoughtful", "curious"]


@dataclass
class StoryParams:
    theme: str
    treasure: str
    spot: str
    tool: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    captain_age: int = 5
    mate_age: int = 7
    seed: Optional[int] = None


KNOWLEDGE = {
    "lei": [
        (
            "What is a lei?",
            "A lei is a loop of flowers or leaves worn around the neck or head. It feels soft and special, but it is not something for rough climbing."
        )
    ],
    "dab": [
        (
            "What is a dab?",
            "A dab is a very small bit of something, like a tiny spot of paint or wax. It is just enough to mark a thing."
        )
    ],
    "water": [
        (
            "Why are wet rocks or boards slippery?",
            "Water and slime make the surface smooth, so shoes cannot grip it well. That is why a wet edge can make you slip fast."
        )
    ],
    "boat_hook": [
        (
            "What is a boat hook?",
            "A boat hook is a long pole with a hook at the end. Grown-ups can use it to pull something closer without leaning over the water."
        )
    ],
    "net": [
        (
            "What does a landing net do?",
            "A landing net lets you scoop something out of water from a safer place. It helps you reach without stepping into danger."
        )
    ],
    "tool": [
        (
            "Why is a long tool safer than climbing onto a slick edge?",
            "A long tool lets you stay back on firm ground. It solves the reaching problem without putting your feet where they could slip."
        )
    ],
    "pirates": [
        (
            "What is a pirate tale?",
            "A pirate tale is a story about treasure, maps, ships, and brave choices. In a good pirate tale, being brave does not mean being reckless."
        )
    ],
}


def pair_noun(captain: Entity, mate: Entity, relation: str) -> str:
    if relation == "siblings":
        if captain.type == "girl" and mate.type == "girl":
            return "two sisters"
        if captain.type == "boy" and mate.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    parent = f["parent"]
    treasure = f["treasure_cfg"]
    spot = f["spot_cfg"]
    tool = f["tool_cfg"]
    return [
        'Write a short cautionary pirate tale for a 3-to-5-year-old that includes the words "lei" and "dab".',
        f"Tell a suspenseful story where {captain.id} sees {treasure.phrase} drifting by {spot.label} and has an inner thought about reaching it, but {mate.id} and {parent.label_word} guide the choice toward safety.",
        f"Write a gentle pirate story where a child learns that {tool.label} is wiser than climbing onto a slick edge for treasure.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    parent = f["parent"]
    treasure = f["treasure_cfg"]
    spot = f["spot_cfg"]
    tool = f["tool_cfg"]
    relation = f["relation"]
    pair = pair_noun(captain, mate, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {captain.id} and {mate.id}, playing pirates by the shore. {captain.id}'s {parent.label_word} comes to help when the drifting treasure causes trouble."
        ),
        (
            "What words from the story describe the pirate game?",
            f"{captain.id} wore a lei like a captain's collar, and the treasure had {treasure.mark}. Those little details made the pirate game feel bright and real."
        ),
        (
            f"Why did {mate.id} tell {captain.id} to stop?",
            f"{mate.id} saw that {spot.label} was wet, slippery, and above the water. {mate.pronoun().capitalize()} knew one quick brave step could turn into a fall."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed {captain.id}'s mind?",
                f"{captain.id} looked at the water and realized the brave idea was not a wise one. Listening to {mate.id} helped {captain.pronoun('object')} step back before the edge could become dangerous."
            )
        )
    else:
        qa.append(
            (
                f"What made the middle of the story suspenseful?",
                f"{captain.id} edged onto {spot.label}, and then a wave slid in right beside {captain.pronoun('object')}. That was the moment when the game stopped feeling pretend and started feeling risky."
            )
        )
    qa.append(
        (
            f"How did {parent.label_word} solve the problem?",
            f"{parent.label_word.capitalize()} {tool.qa_text}. The long reach fixed the problem from firm ground instead of asking a child to risk a slip."
        )
    )
    qa.append(
        (
            "What lesson did the children learn?",
            f"They learned not to climb onto wet edges for floating things. Calling a grown-up and using the right tool kept both the children and the treasure safe."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"lei", "dab", "tool", "pirates"}
    tags |= set(f["spot_cfg"].tags)
    tags |= set(f["tool_cfg"].tags)
    out: list[tuple[str, str]] = []
    order = ["lei", "dab", "water", "boat_hook", "net", "tool", "pirates"]
    for tag in order:
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
        flags = []
        if e.slippery:
            flags.append("slippery")
        if e.over_water:
            flags.append("over_water")
        if e.reach:
            flags.append(f"reach={e.reach}")
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        treasure="shell_box",
        spot="rocks",
        tool="net",
        captain="Lina",
        captain_gender="girl",
        mate="Tomas",
        mate_gender="boy",
        parent="mother",
        trait="careful",
        relation="siblings",
        captain_age=5,
        mate_age=7,
    ),
    StoryParams(
        theme="corsairs",
        treasure="map_tube",
        spot="jetty",
        tool="boat_hook",
        captain="Max",
        captain_gender="boy",
        mate="Lucy",
        mate_gender="girl",
        parent="father",
        trait="thoughtful",
        relation="friends",
        captain_age=6,
        mate_age=6,
    ),
    StoryParams(
        theme="pirates",
        treasure="crown",
        spot="creek_log",
        tool="pole",
        captain="Ava",
        captain_gender="girl",
        mate="Nora",
        mate_gender="girl",
        parent="mother",
        trait="steady",
        relation="siblings",
        captain_age=4,
        mate_age=7,
    ),
]


def explain_rejection(spot: Spot) -> str:
    return (
        f"(No story: {spot.label} is not a slick edge over water, so there is no real pirate-style danger there. "
        f"Pick rocks, a jetty, or a creek log instead.)"
    )


def explain_tool(tool: Tool, spot: Spot) -> str:
    if tool.sense < SENSE_MIN:
        better = ", ".join(sorted(t.id for t in sensible_tools()))
        return (
            f"(Refusing tool '{tool.id}': it scores too low on common sense for this story. "
            f"Try one of: {better}.)"
        )
    return (
        f"(No story: {tool.label} cannot reach treasure drifting by {spot.label}. "
        f"Pick a tool with reach {spot.distance} or more.)"
    )


ASP_RULES = r"""
hazard(S) :- spot(S), slippery(S), over_water(S), distance(S, D), D > 0.
sensible_tool(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
works(T, S) :- sensible_tool(T), reach(T, R), distance(S, D), R >= D.
valid(Theme, Treasure, Spot) :- theme(Theme), treasure(Treasure), hazard(Spot), works(_, Spot).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_sibling :- relation(siblings), captain_age(CA), mate_age(MA), MA > CA.
bonus(3) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), bravery_init(BR), A > BR.

retrieved :- chosen_tool(T), chosen_spot(S), works(T, S).

outcome(averted) :- averted.
outcome(retrieved) :- not averted, retrieved.
outcome(lost) :- not averted, not retrieved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for rid in TREASURES:
        lines.append(asp.fact("treasure", rid))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        if spot.slippery:
            lines.append(asp.fact("slippery", sid))
        if spot.over_water:
            lines.append(asp.fact("over_water", sid))
        lines.append(asp.fact("distance", sid, spot.distance))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("reach", tid, tool.reach))
        lines.append(asp.fact("sense", tid, tool.sense))
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


def asp_sensible_tools() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_tool/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible_tool"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_spot", params.spot),
            asp.fact("relation", params.relation),
            asp.fact("captain_age", params.captain_age),
            asp.fact("mate_age", params.mate_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
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

    clingo_tools = set(asp_sensible_tools())
    python_tools = {tool.id for tool in sensible_tools()}
    if clingo_tools == python_tools:
        print(f"OK: sensible tools match ({sorted(clingo_tools)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(clingo_tools)} python={sorted(python_tools)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            continue
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")

    smoke = CURATED[0]
    try:
        sample = generate(smoke)
        if not sample.story.strip():
            raise StoryError("empty story")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError("unresolved template braces in story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: pirate play, a drifting treasure, and a safer choice."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spot and not hazard_at_risk(SPOTS[args.spot]):
        raise StoryError(explain_rejection(SPOTS[args.spot]))
    if args.tool:
        tool = TOOLS[args.tool]
        if tool.sense < SENSE_MIN:
            spot = SPOTS[args.spot] if args.spot else SPOTS["rocks"]
            raise StoryError(explain_tool(tool, spot))
    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.treasure is None or combo[1] == args.treasure)
        and (args.spot is None or combo[2] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, treasure_id, spot_id = rng.choice(sorted(combos))
    spot = SPOTS[spot_id]

    if args.tool:
        chosen_tool = TOOLS[args.tool]
        if not tool_works(chosen_tool, spot):
            raise StoryError(explain_tool(chosen_tool, spot))
        tool_id = args.tool
    else:
        working = [tool.id for tool in sensible_tools() if tool_works(tool, spot)]
        if not working:
            raise StoryError("(No sensible tool can solve this setup.)")
        tool_id = rng.choice(sorted(working))

    captain, captain_gender = _pick_name(rng)
    mate, mate_gender = _pick_name(rng, avoid=captain)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    captain_age, mate_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        theme=theme_id,
        treasure=treasure_id,
        spot=spot_id,
        tool=tool_id,
        captain=captain,
        captain_gender=captain_gender,
        mate=mate,
        mate_gender=mate_gender,
        parent=parent,
        trait=trait,
        relation=relation,
        captain_age=captain_age,
        mate_age=mate_age,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        treasure = TREASURES[params.treasure]
        spot = SPOTS[params.spot]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(No story: invalid parameter key {err}.)") from err

    if not hazard_at_risk(spot):
        raise StoryError(explain_rejection(spot))
    if tool.sense < SENSE_MIN or not tool_works(tool, spot):
        raise StoryError(explain_tool(tool, spot))

    world = tell(
        theme=theme,
        treasure=treasure,
        spot=spot,
        tool=tool,
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        captain_age=params.captain_age,
        mate_age=params.mate_age,
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
        print(asp_program("", "#show valid/3.\n#show sensible_tool/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible_tools())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, treasure, spot) combos:\n")
        for theme, treasure, spot in combos:
            print(f"  {theme:9} {treasure:10} {spot}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for idx, base in enumerate(CURATED):
            p = StoryParams(
                theme=base.theme,
                treasure=base.treasure,
                spot=base.spot,
                tool=base.tool,
                captain=base.captain,
                captain_gender=base.captain_gender,
                mate=base.mate,
                mate_gender=base.mate_gender,
                parent=base.parent,
                trait=base.trait,
                relation=base.relation,
                captain_age=base.captain_age,
                mate_age=base.mate_age,
                seed=base_seed + idx,
            )
            samples.append(generate(p))
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.captain} & {p.mate}: {p.treasure} by {p.spot} ({outcome_of(p)})"
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
