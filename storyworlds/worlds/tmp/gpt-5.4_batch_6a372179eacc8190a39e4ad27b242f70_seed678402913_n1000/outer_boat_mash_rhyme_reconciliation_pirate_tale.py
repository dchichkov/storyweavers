#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/outer_boat_mash_rhyme_reconciliation_pirate_tale.py
===============================================================================

A standalone story world for a tiny pirate-style tale about a toy boat, a bowl
of mash, a hurtful rhyme, and a reconciliation that lets two children work
together again.

The world model prefers a plausible physical problem over wide coverage:
a child launches a small boat alone after a boastful rhyme hurts a playmate's
feelings; the boat drifts toward the outer water; only a sensible long-reach
tool can recover it. The emotional turn matters too: the rescue works because
the captain apologizes and the two children pull together.

Run it
------
    python storyworlds/worlds/gpt-5.4/outer_boat_mash_rhyme_reconciliation_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/outer_boat_mash_rhyme_reconciliation_pirate_tale.py --setting cove --tool net
    python storyworlds/worlds/gpt-5.4/outer_boat_mash_rhyme_reconciliation_pirate_tale.py --tool hands
    python storyworlds/worlds/gpt-5.4/outer_boat_mash_rhyme_reconciliation_pirate_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/outer_boat_mash_rhyme_reconciliation_pirate_tale.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    outer_phrase: str
    launch_text: str
    water_text: str
    outer_distance: int
    drift_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mash:
    id: str
    label: str
    phrase: str
    color: str
    use_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    reach: int
    power: int
    sense: int
    teamwork: bool
    rescue_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mash: str
    tool: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    relation: str
    trait: str
    delay: int = 0
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


def _r_drift_alarm(world: World) -> list[str]:
    boat = world.get("boat")
    room = world.get("shore")
    out: list[str] = []
    if boat.meters["drifting"] < THRESHOLD:
        return out
    sig = ("outer", "boat")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["risk"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__outer__")
    return out


def _r_hurt_distance(world: World) -> list[str]:
    captain = world.get("captain")
    mate = world.get("mate")
    if mate.memes["hurt"] < THRESHOLD:
        return []
    sig = ("distance", "feelings")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    captain.memes["lonely"] += 1
    mate.memes["distance"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="drift_alarm", tag="physical", apply=_r_drift_alarm),
    Rule(name="hurt_distance", tag="social", apply=_r_hurt_distance),
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


SETTINGS = {
    "pond": Setting(
        id="pond",
        place="the pond by the park",
        outer_phrase="the outer reeds",
        launch_text="at the wooden edge of the pond",
        water_text="The pond looked shiny and still, except for tiny ripples near the reeds.",
        outer_distance=1,
        drift_word="glided",
        tags={"pond", "outer"},
    ),
    "cove": Setting(
        id="cove",
        place="a little cove",
        outer_phrase="the outer rocks",
        launch_text="where the cove opened toward the sea",
        water_text="Small waves licked the sand, and the deeper water moved beyond the quiet shallows.",
        outer_distance=2,
        drift_word="bobbed",
        tags={"cove", "outer"},
    ),
    "harbor": Setting(
        id="harbor",
        place="the harbor wall",
        outer_phrase="the outer posts by the tide",
        launch_text="beside the old harbor steps",
        water_text="The water slapped softly against the wall, and the tide tugged anything loose toward the posts outside.",
        outer_distance=3,
        drift_word="slid",
        tags={"harbor", "outer"},
    ),
}

MASHES = {
    "berry": Mash(
        id="berry",
        label="berry mash",
        phrase="a bowl of berry mash",
        color="purple",
        use_text="to smear a pretend treasure mark on their map and save a little for a pirate snack",
        tags={"mash", "berries"},
    ),
    "banana": Mash(
        id="banana",
        label="banana mash",
        phrase="a cup of banana mash",
        color="gold",
        use_text="to look like golden island pudding for their pirate feast",
        tags={"mash", "banana"},
    ),
    "apple": Mash(
        id="apple",
        label="apple mash",
        phrase="a tin of apple mash",
        color="pink",
        use_text="to dab soft pink clues along the edge of their treasure paper",
        tags={"mash", "apple"},
    ),
}

TOOLS = {
    "hook": Tool(
        id="hook",
        label="boat hook",
        phrase="a long boat hook",
        reach=3,
        power=4,
        sense=3,
        teamwork=True,
        rescue_text="reached far with the long boat hook while {mate} steadied {captain}'s elbow, and together they drew the little boat back through the water",
        fail_text="stretched with the boat hook, but the current had already pulled the little boat too far beyond the tip",
        qa_text="used the long boat hook together to draw the little boat back",
        tags={"hook", "boat"},
    ),
    "net": Tool(
        id="net",
        label="fishing net",
        phrase="a fishing net with a long handle",
        reach=2,
        power=3,
        sense=3,
        teamwork=True,
        rescue_text="lowered the fishing net in front of the drifting boat, and with both children guiding the handle, they scooped it in before it bumped the stones",
        fail_text="swished the net through the water, but the boat had already drifted past the mouth of the net",
        qa_text="guided the long-handled net together and scooped the boat in",
        tags={"net", "boat"},
    ),
    "oar": Tool(
        id="oar",
        label="oar",
        phrase="a spare oar",
        reach=3,
        power=3,
        sense=2,
        teamwork=True,
        rescue_text="lay flat on the stones and reached the oar out while {mate} held onto {captain}'s waist, and they nudged the toy boat back within reach",
        fail_text="poked with the oar, but each nudge only turned the boat and let it drift farther away",
        qa_text="used a spare oar together to nudge the boat back",
        tags={"oar", "boat"},
    ),
    "hands": Tool(
        id="hands",
        label="hands",
        phrase="bare hands from the edge",
        reach=1,
        power=1,
        sense=1,
        teamwork=False,
        rescue_text="splashed in and grabbed the toy boat with bare hands",
        fail_text="leaned and splashed with bare hands, but the boat stayed out in the outer water",
        qa_text="reached with bare hands",
        tags={"boat"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Zoe", "Ella", "Lucy", "Anna"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]
TRAITS = ["careful", "cheerful", "gentle", "stubborn", "thoughtful", "proud"]
RELATIONS = ["siblings", "friends"]


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def valid_combo(setting: Setting, tool: Tool) -> bool:
    return tool.sense >= SENSE_MIN and tool.reach >= setting.outer_distance


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for mash_id in MASHES:
            for tool_id, tool in TOOLS.items():
                if valid_combo(setting, tool):
                    combos.append((setting_id, mash_id, tool_id))
    return combos


def explain_tool(tool: Tool) -> str:
    return (
        f"(Refusing tool '{tool.id}': it is not a sensible rescue here "
        f"(sense={tool.sense} < {SENSE_MIN}). A drifting boat in outer water needs "
        f"a long, safe tool, not {tool.phrase}.)"
    )


def explain_setting_tool(setting: Setting, tool: Tool) -> str:
    return (
        f"(No story: {tool.phrase} can only reach {tool.reach}, but {setting.outer_phrase} "
        f"sit at distance {setting.outer_distance}. Pick a longer tool for this water.)"
    )


def rescue_severity(setting: Setting, delay: int) -> int:
    return setting.outer_distance + delay


def is_recovered(setting: Setting, tool: Tool, delay: int) -> bool:
    teamwork_bonus = 1 if tool.teamwork else 0
    return tool.power + teamwork_bonus >= rescue_severity(setting, delay)


def predict_drift(world: World) -> dict:
    sim = world.copy()
    boat = sim.get("boat")
    boat.meters["drifting"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("shore").meters["risk"],
        "worry": sum(k.memes["worry"] for k in sim.kids()),
    }


def introduce(world: World, captain: Entity, mate: Entity, setting: Setting, mash: Mash) -> None:
    for kid in (captain, mate):
        kid.memes["joy"] += 1
    relation_text = "brother and sister" if world.facts["relation"] == "siblings" and captain.type != mate.type else (
        "two brothers" if world.facts["relation"] == "siblings" and captain.type == "boy" and mate.type == "boy" else (
            "two sisters" if world.facts["relation"] == "siblings" and captain.type == "girl" and mate.type == "girl" else "two friends"
        )
    )
    world.say(
        f"On a bright afternoon, {captain.id} and {mate.id}, {relation_text}, played pirate at {setting.place}. "
        f"They had a toy boat, a crinkly treasure map, and {mash.phrase} {mash.use_text}."
    )
    world.say(
        f"{setting.water_text} The little boat waited {setting.launch_text}, ready for its first brave voyage."
    )


def start_rhyme(world: World, captain: Entity, mate: Entity, mash: Mash) -> None:
    captain.memes["pride"] += 1
    world.say(
        f'{captain.id} thumped the side of the toy boat and made up a pirate rhyme: '
        f'"Captain {captain.id} gets the boat and gold. {mate.id} can watch from the shore in the cold!"'
    )
    world.say(
        f"The words were meant to sound grand, but they landed with a thud. Even the {mash.label} in the bowl seemed to go quiet."
    )


def hurt_reaction(world: World, mate: Entity, captain: Entity, setting: Setting) -> None:
    pred = predict_drift(world)
    mate.memes["hurt"] += 1
    propagate(world, narrate=False)
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f'{mate.id} stopped smiling. "{captain.id}, that is not a sharing rhyme," {mate.pronoun()} said softly.'
    )
    world.say(
        f"{mate.id} folded {mate.pronoun('possessive')} arms and stepped back from the water, so {captain.id} stood alone by the boat."
    )


def launch_alone(world: World, captain: Entity, boat: Entity, setting: Setting) -> None:
    captain.memes["defiance"] += 1
    boat.meters["drifting"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I can sail it myself," {captain.id} said, and gave the toy boat a proud push.'
    )
    world.say(
        f"At first it only {setting.drift_word} a little. Then the current caught it and carried it toward {setting.outer_phrase}."
    )


def panic(world: World, captain: Entity, mate: Entity, boat: Entity, mash: Mash) -> None:
    boat.meters["tipping"] += 1
    captain.memes["fear"] += 1
    mate.memes["fear"] += 1
    world.say(
        f"The bowl tied inside wobbled, and a smear of {mash.color} mash slid across the treasure paper."
    )
    world.say(
        f'"Oh no! The boat!" {captain.id} cried. This time {captain.pronoun()} did not sound proud at all.'
    )
    world.say(
        f"{mate.id} looked at the drifting boat, then at {captain.id}'s worried face."
    )


def apologize(world: World, captain: Entity, mate: Entity) -> None:
    captain.memes["regret"] += 1
    captain.memes["distance"] = 0.0
    mate.memes["distance"] = 0.0
    world.say(
        f'{captain.id} swallowed hard. "I am sorry," {captain.pronoun()} said. '
        f'"That rhyme was mean. I wanted to sound big, but I made you feel small."'
    )
    world.say(
        f'{captain.id} tried again, slower this time: "Mate and captain, side by side, '
        f'two kind hearts can ride the tide."'
    )
    mate.memes["forgiven"] += 1
    mate.memes["trust"] += 1
    world.say(
        f"The new rhyme sounded softer, and it made room for both of them."
    )


def choose_tool(world: World, tool: Tool) -> None:
    world.say(
        f"Beside the stones lay {tool.phrase}. It was the sort of thing that could actually reach the outer water."
    )


def rescue_success(world: World, captain: Entity, mate: Entity, tool: Tool, boat: Entity, mash: Mash) -> None:
    boat.meters["drifting"] = 0.0
    boat.meters["saved"] += 1
    for kid in (captain, mate):
        kid.memes["relief"] += 1
        kid.memes["peace"] += 1
        kid.memes["joy"] += 1
        kid.memes["worry"] = 0.0
        kid.memes["hurt"] = 0.0
    text = tool.rescue_text.format(captain=captain.id, mate=mate.id)
    world.say(
        f"Quickly they {text}."
    )
    world.say(
        f"The toy boat came home rocking but safe, and only a little ribbon of {mash.color} mash had escaped."
    )


def rescue_fail(world: World, captain: Entity, mate: Entity, tool: Tool, boat: Entity, setting: Setting, mash: Mash) -> None:
    boat.meters["lost"] += 1
    boat.meters["drifting"] += 1
    for kid in (captain, mate):
        kid.memes["sad"] += 1
        kid.memes["peace"] += 1
        kid.memes["hurt"] = 0.0
    world.say(
        f"They hurried together, but {tool.fail_text}."
    )
    world.say(
        f"The tiny boat spun once near {setting.outer_phrase}, and the treasure paper with its smear of {mash.color} mash slipped away with it."
    )


def ending_recovered(world: World, captain: Entity, mate: Entity, mash: Mash) -> None:
    world.say(
        f"Back on the shore, {mate.id} straightened the treasure map while {captain.id} wiped the spilled {mash.label} from the boat's rim."
    )
    world.say(
        f"Then they shared the rest of the mash with little spoons and sang the kinder rhyme again, louder now because both voices belonged in it."
    )
    world.say(
        "Their pirate game went on, not with one grand captain and one lonely watcher, but with two shipmates steering together."
    )


def ending_lost(world: World, captain: Entity, mate: Entity, mash: Mash) -> None:
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"For a moment they watched the empty water. Then {mate.id} nudged the bowl of {mash.label} toward {captain.id}."
    )
    world.say(
        f'Together they made a fresh map on dry paper and sang, "Side by side, we mend and share; kind words make the best ship there."'
    )
    world.say(
        "The first little boat was gone, but their friendship was back, and that was the treasure they could still hold."
    )


def tell(
    setting: Setting,
    mash: Mash,
    tool: Tool,
    captain_name: str = "Tom",
    captain_gender: str = "boy",
    mate_name: str = "Lily",
    mate_gender: str = "girl",
    relation: str = "friends",
    trait: str = "thoughtful",
    delay: int = 0,
) -> World:
    world = World()
    captain = world.add(Entity(
        id="captain",
        kind="character",
        type=captain_gender,
        label=captain_name,
        role="captain",
        traits=["bold"],
        attrs={"display": captain_name, "relation": relation},
    ))
    mate = world.add(Entity(
        id="mate",
        kind="character",
        type=mate_gender,
        label=mate_name,
        role="mate",
        traits=[trait],
        attrs={"display": mate_name, "relation": relation},
    ))
    boat = world.add(Entity(
        id="boat",
        kind="thing",
        type="boat",
        label="toy boat",
        phrase="the toy boat",
        tags={"boat"},
    ))
    world.add(Entity(
        id="shore",
        kind="thing",
        type="shore",
        label="shore",
    ))

    world.facts["relation"] = relation

    introduce(world, captain, mate, setting, mash)
    world.para()
    start_rhyme(world, captain, mate, mash)
    hurt_reaction(world, mate, captain, setting)
    launch_alone(world, captain, boat, setting)
    world.para()
    panic(world, captain, mate, boat, mash)
    apologize(world, captain, mate)
    choose_tool(world, tool)

    severity = rescue_severity(setting, delay)
    boat.meters["severity"] = float(severity)
    recovered = is_recovered(setting, tool, delay)

    if delay > 0:
        world.say(
            f"But the boat had already drifted for {delay} extra breath{'s' if delay != 1 else ''}, and that made the rescue harder."
        )

    if recovered:
        rescue_success(world, captain, mate, tool, boat, mash)
        world.para()
        ending_recovered(world, captain, mate, mash)
    else:
        rescue_fail(world, captain, mate, tool, boat, setting, mash)
        world.para()
        ending_lost(world, captain, mate, mash)

    world.facts.update(
        setting=setting,
        mash=mash,
        tool=tool,
        captain=captain,
        mate=mate,
        boat=boat,
        outcome="recovered" if recovered else "lost",
        recovered=recovered,
        delay=delay,
        severity=severity,
        apologized=captain.memes["regret"] >= THRESHOLD,
    )
    return world


def pair_noun(captain: Entity, mate: Entity, relation: str) -> str:
    if relation == "siblings":
        if captain.type == "boy" and mate.type == "boy":
            return "two brothers"
        if captain.type == "girl" and mate.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    setting = f["setting"]
    mash = f["mash"]
    tool = f["tool"]
    outcome = f["outcome"]
    base = (
        f'Write a pirate-style story for a 3-to-5-year-old that includes the words '
        f'"outer", "boat", and "mash", and uses a rhyme that leads to reconciliation.'
    )
    if outcome == "recovered":
        return [
            base,
            f"Tell a gentle pirate tale where {captain.label} hurts {mate.label}'s feelings with a selfish rhyme, "
            f"their toy boat drifts toward {setting.outer_phrase}, and they make up in time to rescue it with {tool.phrase}.",
            f"Write a story set at {setting.place} where children playing pirates carry {mash.label}, say a kinder second rhyme, and end by sharing the boat and the treasure game.",
        ]
    return [
        base,
        f"Tell a pirate tale where {captain.label} apologizes after a boastful rhyme, but the toy boat drifts too far into {setting.outer_phrase} to save. Let the reconciliation still be the true treasure.",
        f"Write a gentle sad ending where the children lose the little boat but mend their friendship with a shared rhyme and a fresh map made beside the water.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    setting = f["setting"]
    mash = f["mash"]
    tool = f["tool"]
    relation = world.facts["relation"]
    pair = pair_noun(captain, mate, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {captain.label} and {mate.label}, pretending to be pirate shipmates. "
            f"They were playing with a toy boat and {mash.label} by {setting.place}.",
        ),
        (
            f"Why did {mate.label} feel hurt?",
            f"{mate.label} felt hurt because {captain.label} made a rhyme that left {mate.pronoun('object')} out of the adventure. "
            f"The rhyme made one child sound important and the other child sound lonely.",
        ),
        (
            "What physical problem happened in the middle of the story?",
            f"The toy boat drifted away toward {setting.outer_phrase}, and the mash inside started to smear across the map. "
            f"That turned a hurt feeling into a real rescue problem.",
        ),
        (
            f"How did the children start to make up?",
            f"{captain.label} apologized and admitted the first rhyme had been mean. "
            f"Then {captain.pronoun()} made a new rhyme that gave both children a place in the game.",
        ),
    ]
    if f["outcome"] == "recovered":
        qa.append((
            "How did they get the boat back?",
            f"They {tool.qa_text}. The rescue worked because they stopped quarreling and used the tool together before the boat drifted any farther.",
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the boat safe on the shore and the two children sharing the rest of the {mash.label}. "
            f"The last image shows that the game changed from lonely boasting to teamwork.",
        ))
    else:
        qa.append((
            "Did they save the boat?",
            f"No. Even after they made up, the boat had drifted too far toward {setting.outer_phrase}. "
            f"They could not keep the toy boat, but they did keep their friendship.",
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a fresh map, a shared rhyme, and peace between the children. "
            f"They lost the little boat, but the reconciliation still changed the day.",
        ))
    return qa


KNOWLEDGE = {
    "boat": [
        (
            "Why can a small boat drift away?",
            "A small boat can drift away because water moves it even when nobody is touching it. Wind and current can carry it farther each moment.",
        )
    ],
    "outer": [
        (
            "What does outer mean in a place like outer water?",
            "Outer means farther away from the safe inside edge. In outer water, things are usually harder to reach and control.",
        )
    ],
    "mash": [
        (
            "What is mash?",
            "Mash is soft food that has been crushed until it is squishy. It can smear easily if a bowl tips or shakes.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme uses words that sound alike, like tide and side. Rhymes can sound playful and easy to remember.",
        )
    ],
    "reconciliation": [
        (
            "What does it mean to reconcile after a quarrel?",
            "To reconcile means to make peace after being upset. It usually starts when someone tells the truth, says sorry, and chooses kinder words.",
        )
    ],
    "net": [
        (
            "What does a fishing net do?",
            "A fishing net can scoop or catch something in the water. A long handle helps it reach farther from the shore.",
        )
    ],
    "hook": [
        (
            "What is a boat hook for?",
            "A boat hook is a long pole with a hooked end. People use it to pull a boat closer without stepping into deep water.",
        )
    ],
    "oar": [
        (
            "What is an oar?",
            "An oar is a long piece of wood used to push water and move a boat. It can also reach out to nudge something floating nearby.",
        )
    ],
}
KNOWLEDGE_ORDER = ["outer", "boat", "mash", "rhyme", "reconciliation", "net", "hook", "oar"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"boat", "outer", "mash", "rhyme", "reconciliation"}
    tags |= set(f["tool"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="pond",
        mash="berry",
        tool="net",
        captain="Tom",
        captain_gender="boy",
        mate="Lily",
        mate_gender="girl",
        relation="friends",
        trait="gentle",
        delay=0,
    ),
    StoryParams(
        setting="cove",
        mash="banana",
        tool="hook",
        captain="Max",
        captain_gender="boy",
        mate="Nora",
        mate_gender="girl",
        relation="siblings",
        trait="thoughtful",
        delay=1,
    ),
    StoryParams(
        setting="harbor",
        mash="apple",
        tool="oar",
        captain="Sam",
        captain_gender="boy",
        mate="Ben",
        mate_gender="boy",
        relation="friends",
        trait="cheerful",
        delay=1,
    ),
    StoryParams(
        setting="harbor",
        mash="berry",
        tool="hook",
        captain="Ava",
        captain_gender="girl",
        mate="Lucy",
        mate_gender="girl",
        relation="siblings",
        trait="careful",
        delay=2,
    ),
]


ASP_RULES = r"""
sensible_tool(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
valid(S, M, T) :- setting(S), mash(M), tool(T), sensible_tool(T),
                  outer_distance(S, D), reach(T, R), R >= D.

team_bonus(1) :- chosen_tool(T), teamwork(T).
team_bonus(0) :- chosen_tool(T), not teamwork(T).
severity(D + L) :- chosen_setting(S), outer_distance(S, D), delay(L).
rescue_power(P + B) :- chosen_tool(T), power(T, P), team_bonus(B).
outcome(recovered) :- rescue_power(P), severity(V), P >= V.
outcome(lost) :- not outcome(recovered).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        lines.append(asp.fact("outer_distance", setting_id, setting.outer_distance))
    for mash_id in MASHES:
        lines.append(asp.fact("mash", mash_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        lines.append(asp.fact("reach", tool_id, tool.reach))
        lines.append(asp.fact("power", tool_id, tool.power))
        if tool.teamwork:
            lines.append(asp.fact("teamwork", tool_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
        asp.fact("chosen_setting", params.setting),
        asp.fact("chosen_tool", params.tool),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    setting = SETTINGS[params.setting]
    tool = TOOLS[params.tool]
    return "recovered" if is_recovered(setting, tool, params.delay) else "lost"


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
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a pirate game, a drifting boat, a bowl of mash, and a reconciliatory rhyme."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mash", choices=MASHES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra breaths before the children reach for the rescue tool")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible triples from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool:
        tool = TOOLS[args.tool]
        if tool.sense < SENSE_MIN:
            raise StoryError(explain_tool(tool))
    if args.setting and args.tool:
        setting = SETTINGS[args.setting]
        tool = TOOLS[args.tool]
        if not valid_combo(setting, tool):
            raise StoryError(explain_setting_tool(setting, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.mash is None or combo[1] == args.mash)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mash_id, tool_id = rng.choice(sorted(combos))
    captain, captain_gender = _pick_kid(rng)
    mate, mate_gender = _pick_kid(rng, avoid=captain)
    relation = rng.choice(RELATIONS)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        setting=setting_id,
        mash=mash_id,
        tool=tool_id,
        captain=captain,
        captain_gender=captain_gender,
        mate=mate,
        mate_gender=mate_gender,
        relation=relation,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        mash = MASHES[params.mash]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err.args[0]})") from err

    if tool.sense < SENSE_MIN:
        raise StoryError(explain_tool(tool))
    if not valid_combo(setting, tool):
        raise StoryError(explain_setting_tool(setting, tool))

    world = tell(
        setting=setting,
        mash=mash,
        tool=tool,
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
        relation=params.relation,
        trait=params.trait,
        delay=params.delay,
    )

    story = world.render()
    story = story.replace("captain", world.get("captain").label)
    story = story.replace("mate", world.get("mate").label)

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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mash, tool) combos:\n")
        for setting, mash, tool in combos:
            print(f"  {setting:7} {mash:7} {tool}")
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
            header = f"### {p.captain} and {p.mate}: {p.setting}, {p.mash}, {p.tool}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
