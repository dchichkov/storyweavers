#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/clacker_foreshadowing_magic_pirate_tale.py
=====================================================================

A standalone story world for a small magical pirate tale built around a
**clacker**: an enchanted string of shells that warns of danger before danger
can be seen. The story shape is a child-facing pirate adventure with clear
foreshadowing, a magical middle turn, and a concrete ending image that proves
the crew learned to trust the warning.

The world models one small domain:

    A young pirate captain and a mate sail toward a treasure place.
    The magic clacker tied to their mast begins to clack first.
    That warning foreshadows a hidden obstacle ahead.
    The crew edges too close, sees the danger become real, then uses the right
    magical charm to calm or reveal the path.
    They reach the treasure and sail home wiser.

Reasonableness constraint
-------------------------
Not every route, obstacle, and charm make sense together.

* each route supports one specific hidden obstacle
* each obstacle is solved by one fitting magical charm

The world refuses mismatched combinations because the clacker's warning must
honestly point to a real problem, and the charm must truly solve it.

Run it
------
    python storyworlds/worlds/gpt-5.4/clacker_foreshadowing_magic_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/clacker_foreshadowing_magic_pirate_tale.py --route moon_cove
    python storyworlds/worlds/gpt-5.4/clacker_foreshadowing_magic_pirate_tale.py --obstacle mist --charm song_flute
    python storyworlds/worlds/gpt-5.4/clacker_foreshadowing_magic_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/clacker_foreshadowing_magic_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/clacker_foreshadowing_magic_pirate_tale.py --trace
    python storyworlds/worlds/gpt-5.4/clacker_foreshadowing_magic_pirate_tale.py --asp
    python storyworlds/worlds/gpt-5.4/clacker_foreshadowing_magic_pirate_tale.py --verify
"""

from __future__ import annotations

import argparse
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Route:
    id: str
    place: str
    horizon: str
    treasure: str
    treasure_phrase: str
    arrival: str
    obstacle: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    hidden: str
    reveal: str
    threat: str
    solved_by: str
    solved_text: str
    qa_reason: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    action: str
    effect: str
    qa_effect: str
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

    def crew(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_foreboding(world: World) -> list[str]:
    clacker = world.get("clacker")
    if clacker.meters["clacking"] < THRESHOLD:
        return []
    sig = ("foreboding",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for sailor in world.crew():
        sailor.memes["foreboding"] += 1
    return []


def _r_peril(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    if obstacle.meters["blocking"] < THRESHOLD or obstacle.meters["calmed"] >= THRESHOLD:
        return []
    sig = ("peril",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boat = world.get("boat")
    boat.meters["danger"] += 1
    for sailor in world.crew():
        sailor.memes["fear"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    if obstacle.meters["calmed"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boat = world.get("boat")
    boat.meters["danger"] = 0.0
    boat.meters["path_open"] += 1
    for sailor in world.crew():
        sailor.memes["relief"] += 1
        sailor.memes["trust_magic"] += 1
        sailor.memes["fear"] = 0.0
    return []


CAUSAL_RULES = [
    Rule("foreboding", "emotional", _r_foreboding),
    Rule("peril", "physical", _r_peril),
    Rule("relief", "emotional", _r_relief),
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
                produced.extend(out)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def valid_combo(route_id: str, obstacle_id: str, charm_id: str) -> bool:
    route = ROUTES[route_id]
    obstacle = OBSTACLES[obstacle_id]
    return route.obstacle == obstacle.id and obstacle.solved_by == charm_id


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for route_id, route in ROUTES.items():
        obstacle = OBSTACLES[route.obstacle]
        out.append((route_id, obstacle.id, obstacle.solved_by))
    return out


def explain_rejection(route_id: str, obstacle_id: str, charm_id: str) -> str:
    route = ROUTES[route_id]
    obstacle = OBSTACLES[obstacle_id]
    charm = CHARMS[charm_id]
    if route.obstacle != obstacle.id:
        real = OBSTACLES[route.obstacle]
        return (
            f"(No story: {route.place} hides {real.label}, not {obstacle.label}. "
            f"The clacker's warning must foreshadow a real danger on that route.)"
        )
    if obstacle.solved_by != charm.id:
        real = CHARMS[obstacle.solved_by]
        return (
            f"(No story: {charm.label} does not solve {obstacle.label}. "
            f"That obstacle needs {real.phrase} so the magic turn makes sense.)"
        )
    return "(No story: that route, obstacle, and charm do not belong together.)"


def launch(world: World, captain: Entity, mate: Entity, elder: Entity, route: Route, charm: Charm) -> None:
    for sailor in (captain, mate):
        sailor.memes["joy"] += 1
    world.say(
        f"At sunrise, {captain.id} and {mate.id} pushed their little pirate boat from the sand. "
        f"They were sailing for {route.place}, where {route.treasure_phrase} waited."
    )
    world.say(
        f'Before they left, {captain.id}\'s {elder.label_word} tied a magic clacker of bright shells to the mast '
        f'and handed them {charm.phrase}. "When that clacker talks," {elder.pronoun()} said, '
        f'"listen before the sea finishes its secret."'
    )
    world.say(
        f"The words sounded mysterious then, but {captain.id} tucked them away like a map in {captain.pronoun('possessive')} pocket."
    )


def sail_out(world: World, captain: Entity, mate: Entity, route: Route) -> None:
    world.say(
        f"The little sailboat skipped over the blue water toward {route.horizon}. "
        f"Salt sparkled on the rail, and the mast hummed in the morning wind."
    )
    world.say(
        f'"{route.treasure} will be ours by snack time," {captain.id} said, grinning like a tiny sea captain.'
    )


def foreshadow(world: World, mate: Entity, route: Route) -> None:
    clacker = world.get("clacker")
    clacker.meters["clacking"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the shell clacker gave one sharp clack. Then another. Soon it was chattering over the water, though the sky still looked clear."
    )
    world.say(
        f'{mate.id} looked up at it. "That is not just the wind," {mate.pronoun()} whispered.'
    )
    world.facts["foreshadowed"] = True


def edge_close(world: World, captain: Entity, mate: Entity, obstacle: Obstacle) -> None:
    captain.memes["doubt"] += 1
    world.say(
        f'But treasure was close, and {captain.id} squinted ahead. "Maybe it is only excited for us," {captain.pronoun()} said, steering on a little farther.'
    )
    obstacle_ent = world.get("obstacle")
    obstacle_ent.meters["blocking"] += 1
    propagate(world, narrate=False)
    boat = world.get("boat")
    boat.meters["near_obstacle"] += 1
    world.say(obstacle.reveal)
    world.say(obstacle.threat)


def remember_and_use(world: World, captain: Entity, mate: Entity, charm: Charm, obstacle: Obstacle) -> None:
    captain.memes["understanding"] += 1
    world.say(
        f"At once {captain.id} remembered the harbor words: listen before the sea finishes its secret. "
        f'The clacker had spoken first.'
    )
    world.say(
        f'{captain.id} grabbed {charm.phrase} and {charm.action}.'
    )
    obstacle_ent = world.get("obstacle")
    obstacle_ent.meters["calmed"] += 1
    propagate(world, narrate=False)
    world.say(charm.effect)
    world.say(obstacle.solved_text)


def claim_treasure(world: World, captain: Entity, mate: Entity, route: Route) -> None:
    treasure = world.get("treasure")
    treasure.meters["found"] += 1
    for sailor in (captain, mate):
        sailor.memes["wonder"] += 1
    world.say(
        f"With the path open, the boat slipped into {route.place}. There they found {route.treasure_phrase}, gleaming as if it had been waiting just for them."
    )
    world.say(route.arrival)


def return_home(world: World, captain: Entity, mate: Entity) -> None:
    world.say(
        f"On the way home, the shell clacker hung quiet and shiny in the sun."
    )
    world.say(
        f'{mate.id} tapped it gently. "Now we know," {mate.pronoun()} said. "Magic warns first."'
    )
    world.say(
        f'{captain.id} nodded and tied the clacker even tighter to the mast. From then on, the little pirate crew still loved treasure, '
        f'but they loved listening to good warnings too.'
    )


def tell(route: Route, obstacle: Obstacle, charm: Charm,
         captain_name: str = "Mina", captain_type: str = "girl",
         mate_name: str = "Toby", mate_type: str = "boy",
         elder_type: str = "grandmother", trait: str = "brave") -> World:
    world = World()
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_type,
                               role="captain", traits=[trait]))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_type,
                            role="mate", traits=["careful"]))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type,
                             role="elder", label="the elder"))
    boat = world.add(Entity(id="boat", type="boat", label="pirate boat"))
    clacker = world.add(Entity(id="clacker", type="magic", label="shell clacker"))
    obstacle_ent = world.add(Entity(id="obstacle", type="obstacle", label=obstacle.label))
    treasure = world.add(Entity(id="treasure", type="treasure", label=route.treasure))

    launch(world, captain, mate, elder, route, charm)
    sail_out(world, captain, mate, route)

    world.para()
    foreshadow(world, mate, route)
    edge_close(world, captain, mate, obstacle)

    world.para()
    remember_and_use(world, captain, mate, charm, obstacle)

    world.para()
    claim_treasure(world, captain, mate, route)
    return_home(world, captain, mate)

    world.facts.update(
        captain=captain,
        mate=mate,
        elder=elder,
        route=route,
        obstacle_cfg=obstacle,
        charm=charm,
        boat=boat,
        clacker=clacker,
        treasure=treasure,
        success=treasure.meters["found"] >= THRESHOLD,
        foreshadowed=world.facts.get("foreshadowed", False),
    )
    return world


ROUTES = {
    "moon_cove": Route(
        "moon_cove",
        "Moon Cove",
        "a silver bend of water under chalky cliffs",
        "the moon-pearl",
        "a moon-pearl resting in a tide pool",
        "The pearl made a pale circle of light on the deck, and even the oars looked enchanted beside it.",
        "mist",
        tags={"moon", "mist", "treasure"},
    ),
    "whale_bay": Route(
        "whale_bay",
        "Whale Bay",
        "a round blue bay where the water breathed in slow swells",
        "the star-chest",
        "a little star-chest tucked between smooth rocks",
        "When they opened the lid, tiny lights winked out like patient stars and danced around the mast.",
        "whale",
        tags={"whale", "treasure"},
    ),
    "coral_gate": Route(
        "coral_gate",
        "Coral Gate",
        "two coral towers with a narrow shining pass between them",
        "the singing shell",
        "a singing shell resting on a red coral shelf",
        "The shell hummed softly in {captain}'s hands, as if the sea itself were trying out a lullaby.",
        "reef",
        tags={"reef", "treasure"},
    ),
}

OBSTACLES = {
    "mist": Obstacle(
        "mist",
        "a silver mist-bank",
        "a wall of silver mist hiding sharp rocks",
        "The bow drifted so near that black rocks suddenly showed their wet teeth inside the haze, and the little boat gave an uneasy wobble.",
        "star_compass",
        "The silver mist thinned into ribbons, and the rocks stood still and plain where the crew could steer safely around them.",
        "The mist hid sharp rocks, so sailing straight ahead would have scraped the little boat.",
        tags={"mist", "rocks", "warning"},
    ),
    "whale": Obstacle(
        "whale",
        "a sleeping moon-whale",
        "the rounded back of a moon-whale asleep across the bay mouth",
        "A great sleepy eye blinked open, and the whale's slow roll made the boat tip hard enough for both children to grab the rail.",
        "song_flute",
        "The moon-whale sighed, rolled aside, and left a calm lane of water wide enough for the tiny pirate boat.",
        "The whale was blocking the bay, and if it woke badly it could tip the boat with one huge roll.",
        tags={"whale", "warning", "sea_animal"},
    ),
    "reef": Obstacle(
        "reef",
        "a whispering coral reef",
        "a whispering coral reef just under the clear water",
        "The sea began hissing around hidden coral points, and the hull scraped once with a small frightening cry.",
        "tide_lantern",
        "Blue light spread over the water, showing the safe channel while the hiss of the reef softened to a friendly whisper.",
        "The coral points were almost invisible, and they could crack the boat if the crew kept guessing.",
        tags={"reef", "warning", "coral"},
    ),
}

CHARMS = {
    "star_compass": Charm(
        "star_compass",
        "star compass",
        "the little star compass",
        "held it high until its needle caught the light",
        "At once the compass burned with a soft gold gleam and pointed a bright path through the gray.",
        "Its glow showed the safe way through the hidden rocks.",
        tags={"compass", "magic_tool"},
    ),
    "song_flute": Charm(
        "song_flute",
        "song flute",
        "the silver song flute",
        "played one slow, floating tune",
        "The notes drifted over the water like feathers and settled right on the giant creature's sleepy head.",
        "Its music soothed the whale and coaxed it gently aside.",
        tags={"flute", "magic_tool"},
    ),
    "tide_lantern": Charm(
        "tide_lantern",
        "tide lantern",
        "the blue tide lantern",
        "lifted it over the side so its light touched the water",
        "Blue fireless light bloomed in the shallows and traced a winding safe lane between the coral points.",
        "Its blue light revealed the safe channel through the reef.",
        tags={"lantern", "magic_tool"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Zoe", "Elsie", "Pia", "Rosa"]
BOY_NAMES = ["Toby", "Finn", "Leo", "Sam", "Eli", "Ben", "Owen", "Jude"]
TRAITS = ["brave", "curious", "eager", "sturdy", "hopeful"]


@dataclass
class StoryParams:
    route: str
    obstacle: str
    charm: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "clacker": [
        ("What is a clacker?",
         "A clacker is something that makes a clicking or clacking sound when pieces bump together. In this story, it is a string of shells that works like a magic warning bell."),
    ],
    "foreshadowing": [
        ("What is foreshadowing in a story?",
         "Foreshadowing is when a story gives a small hint before something important happens later. It helps the later event feel surprising and prepared at the same time."),
    ],
    "magic_tool": [
        ("Why do magic tools in stories need rules?",
         "Rules make story magic feel fair and believable inside the tale. When each magical tool does one kind of helpful job, the story's solution feels earned."),
    ],
    "compass": [
        ("What does a compass do?",
         "A compass helps show direction. Sailors use it so they know which way to steer."),
    ],
    "flute": [
        ("What is a flute?",
         "A flute is a musical instrument you blow into to make notes. In stories, music can sometimes calm frightened or sleepy creatures."),
    ],
    "lantern": [
        ("What is a lantern?",
         "A lantern is a light you can carry with you. A bright lantern helps people see where it is safe to go."),
    ],
    "mist": [
        ("Why can mist be dangerous at sea?",
         "Mist makes it hard to see far ahead. Hidden rocks or shorelines can seem to appear all at once."),
    ],
    "whale": [
        ("Why would sailors give a whale lots of space?",
         "Whales are huge animals, so even a gentle roll can move a lot of water. A small boat stays safer when it does not crowd a whale."),
    ],
    "reef": [
        ("What is a reef?",
         "A reef is a ridge of rock or coral near the water's surface. Boats have to steer carefully around reefs so the hull does not scrape or crack."),
    ],
}
KNOWLEDGE_ORDER = ["clacker", "foreshadowing", "magic_tool", "compass", "flute", "lantern", "mist", "whale", "reef"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain, mate, route, obstacle, charm = (
        f["captain"], f["mate"], f["route"], f["obstacle_cfg"], f["charm"]
    )
    return [
        'Write a short pirate tale for a 3-to-5-year-old that includes the word "clacker", uses foreshadowing, and has a magical middle turn.',
        f"Tell a gentle pirate adventure where {captain.id} and {mate.id} sail toward {route.place}, hear a magic clacker warn them first, and then use {charm.phrase} to get past {obstacle.label}.",
        f'Write a child-facing sea story in which an enchanted clacker gives an early warning, the warning turns out to be true, and the crew reaches treasure by listening carefully.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    route = f["route"]
    obstacle = f["obstacle_cfg"]
    charm = f["charm"]
    elder = f["elder"]
    qa = [
        (
            "Who is the story about?",
            f"It is about two little pirates, {captain.id} and {mate.id}, sailing in a small boat. {captain.id}'s {elder.label_word} sends them off with a magic clacker and a charm.",
        ),
        (
            "What treasure were they looking for?",
            f"They were sailing to {route.place} to find {route.treasure_phrase}. That treasure is what made them keep going even after the clacker began to warn them.",
        ),
        (
            "How did the story use foreshadowing?",
            f"The shell clacker started clacking before the danger could be seen. That early sound hinted that something important and risky was waiting ahead.",
        ),
        (
            "What danger was really hiding ahead?",
            f"It was {obstacle.hidden}. {obstacle.qa_reason}",
        ),
        (
            f"How did {captain.id} and {mate.id} solve the problem?",
            f"They used {charm.phrase}. {charm.qa_effect} Because they trusted the warning in time, the path opened instead of staying dangerous.",
        ),
        (
            "How did the story end?",
            f"They reached {route.place}, found {route.treasure_phrase}, and sailed home safely. The quiet clacker at the end shows that the crew learned to listen to wise warnings.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"clacker", "foreshadowing"} | set(world.facts["charm"].tags) | set(world.facts["obstacle_cfg"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moon_cove", "mist", "star_compass", "Mina", "girl", "Toby", "boy", "grandmother", "brave"),
    StoryParams("whale_bay", "whale", "song_flute", "Finn", "boy", "Lila", "girl", "grandfather", "curious"),
    StoryParams("coral_gate", "reef", "tide_lantern", "Rosa", "girl", "Eli", "boy", "grandmother", "eager"),
]


ASP_RULES = r"""
% route-specific hidden danger
real_obstacle(Route, Obs) :- route(Route), route_obstacle(Route, Obs).

% each obstacle has exactly one fitting charm
fitting_charm(Obs, Charm) :- obstacle(Obs), solved_by(Obs, Charm).

valid(Route, Obs, Charm) :- real_obstacle(Route, Obs), fitting_charm(Obs, Charm).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("route_obstacle", route_id, route.obstacle))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("solved_by", obstacle_id, obstacle.solved_by))
    for charm_id in CHARMS:
        lines.append(asp.fact("charm", charm_id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("Generated sample missed required QA or prompts.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a magic clacker warns a tiny pirate crew about a hidden sea danger."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--captain")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid route/obstacle/charm triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.obstacle and args.charm:
        if not valid_combo(args.route, args.obstacle, args.charm):
            raise StoryError(explain_rejection(args.route, args.obstacle, args.charm))

    route_choices = [rid for rid in ROUTES if args.route is None or rid == args.route]
    if not route_choices:
        raise StoryError("(No valid route matches the given options.)")
    route_id = rng.choice(sorted(route_choices))
    route = ROUTES[route_id]

    obstacle_choices = [
        oid for oid in OBSTACLES
        if (args.obstacle is None or oid == args.obstacle) and route.obstacle == oid
    ]
    if not obstacle_choices:
        chosen_obstacle = args.obstacle or next(iter(OBSTACLES))
        chosen_charm = args.charm or next(iter(CHARMS))
        raise StoryError(explain_rejection(route_id, chosen_obstacle, chosen_charm))
    obstacle_id = rng.choice(sorted(obstacle_choices))
    obstacle = OBSTACLES[obstacle_id]

    charm_choices = [
        cid for cid in CHARMS
        if (args.charm is None or cid == args.charm) and obstacle.solved_by == cid
    ]
    if not charm_choices:
        chosen_charm = args.charm or next(iter(CHARMS))
        raise StoryError(explain_rejection(route_id, obstacle_id, chosen_charm))
    charm_id = rng.choice(sorted(charm_choices))

    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or rng.choice(["girl", "boy"])
    captain = args.captain or pick_name(rng, captain_gender)
    mate = args.mate or pick_name(rng, mate_gender, avoid=captain)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(route_id, obstacle_id, charm_id, captain, captain_gender, mate, mate_gender, elder, trait)


def _final_story_text(world: World) -> str:
    text = world.render()
    captain = world.facts["captain"]
    route = world.facts["route"]
    if route.id == "coral_gate":
        text = text.replace("{captain}", captain.id)
    return text


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.route, params.obstacle, params.charm):
        raise StoryError(explain_rejection(params.route, params.obstacle, params.charm))
    world = tell(
        ROUTES[params.route],
        OBSTACLES[params.obstacle],
        CHARMS[params.charm],
        params.captain,
        params.captain_gender,
        params.mate,
        params.mate_gender,
        params.elder,
        params.trait,
    )
    story = _final_story_text(world)
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (route, obstacle, charm) combos:\n")
        for route, obstacle, charm in combos:
            print(f"  {route:11} {obstacle:8} {charm}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.captain} & {p.mate}: {p.route} / {p.obstacle} / {p.charm}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
