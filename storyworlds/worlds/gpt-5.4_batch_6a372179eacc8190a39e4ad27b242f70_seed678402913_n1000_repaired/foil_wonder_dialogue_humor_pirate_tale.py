#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/foil_wonder_dialogue_humor_pirate_tale.py
====================================================================

A small storyworld about two children playing pirates by the sea. One child is a
boastful captain; the other is the practical foil who notices trouble sooner.
Their picnic "treasure" is threatened by gulls, wind, or a sneaky wave, and the
story turns on whether the careful child can prevent the mishap or save the day
with the right little treasure chest.

The seed asked for:
- the words "foil" and "wonder"
- dialogue
- humor
- a pirate-tale flavor

So this world keeps the language playful and salty, lets the children's banter
drive the middle, and makes the careful companion an actual foil to the captain.
One treasure option is wrapped in foil so the word appears naturally, and every
story includes a moment of wonder at the sea.

Run it
------
python storyworlds/worlds/gpt-5.4/foil_wonder_dialogue_humor_pirate_tale.py
python storyworlds/worlds/gpt-5.4/foil_wonder_dialogue_humor_pirate_tale.py --all
python storyworlds/worlds/gpt-5.4/foil_wonder_dialogue_humor_pirate_tale.py --trace
python storyworlds/worlds/gpt-5.4/foil_wonder_dialogue_humor_pirate_tale.py --qa --json
python storyworlds/worlds/gpt-5.4/foil_wonder_dialogue_humor_pirate_tale.py --verify
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
CAUTIOUS_TRAITS = {"careful", "steady", "sensible", "watchful"}
BRAG_LEVEL = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    shore: str
    scene: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    exposed_phrase: str
    plural: bool = False
    lightness: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Threat:
    id: str
    label: str
    approach: str
    danger: str
    effect: str
    severity: int
    suits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Safeguard:
    id: str
    label: str
    phrase: str
    prep: str
    action: str
    power: int
    counters: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        return [e for e in self.entities.values() if e.role in {"captain", "foil"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
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


def _r_alarm(world: World) -> list[str]:
    trouble = world.facts.get("trouble")
    if not trouble:
        return []
    sig = ("alarm", trouble)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["surprise"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="alarm", tag="social", apply=_r_alarm),
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
            world.say(bit)
    return produced


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, captain_age: int, foil_age: int, trait: str) -> bool:
    if relation != "siblings":
        return False
    if foil_age <= captain_age:
        return False
    return initial_caution(trait) + 2.0 > BRAG_LEVEL


def treasure_at_risk(treasure: Treasure, threat: Threat) -> bool:
    return treasure.id in threat.suits


def valid_combo(treasure: Treasure, threat: Threat, safeguard: Safeguard) -> bool:
    return treasure_at_risk(treasure, threat) and threat.id in safeguard.counters


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for treasure_id, treasure in TREASURES.items():
        for threat_id, threat in THREATS.items():
            for guard_id, guard in SAFEGUARDS.items():
                if valid_combo(treasure, threat, guard):
                    combos.append((treasure_id, threat_id, guard_id))
    return combos


def threat_hits(threat: Threat, treasure: Treasure, delay: int) -> int:
    return threat.severity + delay


def is_saved(safeguard: Safeguard, threat: Threat, delay: int) -> bool:
    return safeguard.power >= threat_hits(threat, TREASURES["sandwich"] if False else treasure_placeholder(threat), delay)


def treasure_placeholder(threat: Threat) -> Treasure:
    return next(iter(TREASURES.values()))


def outcome_of(params: "StoryParams") -> str:
    if would_avert(params.relation, params.captain_age, params.foil_age, params.trait):
        return "averted"
    safeguard = SAFEGUARDS[params.safeguard]
    threat = THREATS[params.threat]
    return "saved" if safeguard.power >= threat.severity + params.delay else "lost"


def predict_mishap(world: World, threat_id: str, delay: int) -> dict:
    sim = world.copy()
    threat = THREATS[threat_id]
    treasure = TREASURES[sim.facts["treasure_cfg"].id]
    sim.facts["trouble"] = threat.id
    sim.get("treasure").meters["exposed"] = 1
    sim.get("treasure").meters["loss"] += float(threat.severity + delay)
    propagate(sim, narrate=False)
    return {
        "risk": treasure_at_risk(treasure, threat),
        "loss": sim.get("treasure").meters["loss"],
    }


def introduce(world: World, captain: Entity, foil: Entity, helper: Entity, treasure: Treasure) -> None:
    world.say(
        f"On a bright day at {world.place.shore}, {captain.id} and {foil.id} spread a striped towel and declared it a pirate ship."
    )
    world.say(
        f"The sea looked so wide and glittery that both children stared with wonder for a moment before {captain.id} remembered to squint like a captain."
    )
    world.say(
        f'{captain.id} puffed up {captain.pronoun("possessive")} chest. "I am Captain {captain.id} the Fearsome," {captain.pronoun()} announced.'
    )
    world.say(
        f'{foil.id}, who was {captain.id}\'s cheerful foil, looked at the wobbling paper hat and said, "Fearsome? Your hat is already trying to escape."'
    )
    world.say(
        f"They had brought {treasure.phrase} as their pirate treasure, and {helper.label_word} sat nearby, smiling over a book."
    )


def treasure_detail(treasure: Treasure) -> str:
    if treasure.id == "sandwich":
        return "The sandwich was wrapped in foil that flashed like a silver doubloon whenever the sun found it."
    if treasure.id == "crackers":
        return "The crackers sat in a paper cup so light that even a sneeze could have bossed them around."
    return "The bun sat on a napkin with raisins peeking out like tiny black buttons."


def boast(world: World, captain: Entity, treasure: Treasure) -> None:
    world.say(treasure_detail(treasure))
    world.say(
        f'"We must display the treasure on deck," said {captain.id}. "A proper pirate lunch should look dramatic."'
    )


def warn(world: World, foil: Entity, captain: Entity, threat: Threat, treasure: Treasure) -> None:
    pred = predict_mishap(world, threat.id, world.facts["delay"])
    foil.memes["caution"] += 1
    world.facts["predicted_loss"] = pred["loss"]
    world.say(
        f'{foil.id} narrowed {foil.pronoun("possessive")} eyes at {threat.approach}. "{captain.id}, if you leave {treasure.exposed_phrase} there, {threat.danger}," {foil.pronoun()} said.'
    )


def back_down(world: World, captain: Entity, foil: Entity, safeguard: Safeguard) -> None:
    captain.memes["relief"] += 1
    foil.memes["relief"] += 1
    world.say(
        f'{captain.id} opened {captain.pronoun("possessive")} mouth for a grand speech, then noticed that {foil.id} was older and not blinking at all.'
    )
    world.say(
        f'"All right," {captain.pronoun()} muttered. "A wise captain also enjoys snacks that still exist."'
    )
    world.say(
        f"They used {safeguard.phrase} at once, and the treasure stayed snug before any trouble reached the ship."
    )


def defy(world: World, captain: Entity, foil: Entity, treasure: Treasure) -> None:
    captain.memes["defiance"] += 1
    world.get("treasure").meters["exposed"] = 1
    world.say(
        f'"Nonsense," said {captain.id}. "The sea obeys me. Birds admire me. Even the wind waits its turn."'
    )
    world.say(
        f'{foil.id} snorted. "The gull did not hear that part." Still, {captain.id} set {treasure.exposed_phrase} right on the towel like a royal prize.'
    )


def mishap(world: World, threat: Threat, treasure: Treasure) -> None:
    world.facts["trouble"] = threat.id
    world.get("treasure").meters["loss"] += float(threat.severity + world.facts["delay"])
    if threat.id == "gull":
        world.say(
            f"Just then {threat.approach}. It gave one rude hop, one grabby peck, and made for the treasure with the confidence of a bird that believed all beaches belonged to it."
        )
    elif threat.id == "wind":
        world.say(
            f"Just then {threat.approach}. The paper cup wobbled, the napkin flapped, and the whole deck looked as if it had started sneezing."
        )
    else:
        world.say(
            f"Just then {threat.approach}. The water rushed over the edge of the towel with a cold slap, as if the sea had reached up to play its own joke."
        )
    world.say(threat.effect)
    propagate(world, narrate=False)


def rescue(world: World, helper: Entity, foil: Entity, safeguard: Safeguard, threat: Threat) -> None:
    world.get("treasure").meters["loss"] = 0.0
    world.get("treasure").meters["safe"] += 1
    foil.memes["pride"] += 1
    world.say(
        f'{foil.id} moved first, and {helper.label_word} moved right behind {foil.pronoun("object")}. Together they {safeguard.action}.'
    )
    if threat.id == "gull":
        world.say(
            f'The gull landed a few steps away and shouted its opinion anyway. "{helper.label_word.capitalize()}," said {foil.id}, "I believe we were nearly robbed by a flying pirate."'
        )
    elif threat.id == "wind":
        world.say(
            f'The last cracker stopped skittering just in time. "{foil.id} saved the crew," {helper.label_word} said, and {captain_name(world)} had to admit it was true.'
        )
    else:
        world.say(
            f'The wave slid back without the treasure, and everyone laughed when {captain_name(world)} saluted the bucket as if it were a hero.'
        )


def loss(world: World, helper: Entity, captain: Entity, foil: Entity, threat: Threat) -> None:
    world.get("treasure").meters["lost"] += 1
    world.say(
        f'{helper.label_word.capitalize()} hurried over, but by then the best part of the treasure was gone.'
    )
    if threat.id == "gull":
        world.say("Far down the beach, the gull strutted like a captain who had won a very silly battle.")
    elif threat.id == "wind":
        world.say("Two crackers had escaped into the dune grass, where even pirates had to admit defeat.")
    else:
        world.say("The little wave had already turned the napkin into a soggy flag.")
    world.say(
        f'{captain.id} looked so glum that even {foil.id} kept quiet for one whole breath.'
    )


def lesson(world: World, helper: Entity, captain: Entity, foil: Entity, safeguard: Safeguard, outcome: str) -> None:
    for kid in (captain, foil):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    if outcome == "lost":
        world.say(
            f'{helper.label_word.capitalize()} sat between them on the towel. "A good pirate does not need to brag at the sea," {helper.pronoun()} said. "A good pirate notices what the sea is doing."'
        )
        world.say(
            f'{captain.id} nodded. "{foil.id} was right," {captain.pronoun()} said. "{foil.pronoun().capitalize()} is the sort of mate who keeps the ship from becoming lunch."'
        )
    else:
        world.say(
            f'{helper.label_word.capitalize()} brushed sand from {captain.id}\'s sleeve and smiled. "Brave is good," {helper.pronoun()} said, "but brave plus noticing is even better."'
        )
        world.say(
            f'"That means {foil.id}," said {captain.id}. "{foil.pronoun().capitalize()} notices everything."'
        )
    world.say(
        f'{foil.id} grinned. "Including when your hat is crooked."'
    )


def safe_ending(world: World, captain: Entity, foil: Entity, safeguard: Safeguard, treasure: Treasure, outcome: str) -> None:
    captain.memes["joy"] += 1
    foil.memes["joy"] += 1
    if outcome == "lost":
        world.say(
            f'Then they packed what was left into {safeguard.phrase}, tucked it well above the water, and pretended the missing bites had gone as tax to the Queen of Gulls.'
        )
        world.say(
            f'Soon {captain.id} was laughing again, and when {captain.pronoun()} offered the first safe crumb to {foil.id}, it felt like a better kind of captaincy.'
        )
    else:
        world.say(
            f'After that, the treasure rode inside {safeguard.phrase}, safe and proper, while the two pirates marched along the shore looking for shells shaped like secret teeth.'
        )
        world.say(
            f'Every so often {captain.id} would tap the little chest, and {foil.id} would answer, "Still there, Captain." The sea kept sparkling, the children kept joking, and the adventure felt brighter because they had learned how to keep it.'
        )


def captain_name(world: World) -> str:
    return world.facts["captain"].id


def tell(
    place: Place,
    treasure_cfg: Treasure,
    threat_cfg: Threat,
    safeguard_cfg: Safeguard,
    captain_name_value: str = "Nell",
    captain_gender: str = "girl",
    foil_name: str = "Ben",
    foil_gender: str = "boy",
    helper_type: str = "aunt",
    trait: str = "careful",
    delay: int = 0,
    captain_age: int = 5,
    foil_age: int = 7,
    relation: str = "siblings",
) -> World:
    world = World(place)
    captain = world.add(
        Entity(
            id=captain_name_value,
            kind="character",
            type=captain_gender,
            role="captain",
            age=captain_age,
            traits=["boastful"],
            attrs={"relation": relation},
        )
    )
    foil = world.add(
        Entity(
            id=foil_name,
            kind="character",
            type=foil_gender,
            role="foil",
            age=foil_age,
            traits=[trait],
            attrs={"relation": relation},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
        )
    )
    treasure = world.add(
        Entity(
            id="treasure",
            kind="thing",
            type="food",
            label=treasure_cfg.label,
            phrase=treasure_cfg.phrase,
            tags=set(treasure_cfg.tags),
        )
    )
    captain.memes["brag"] = BRAG_LEVEL
    foil.memes["caution"] = initial_caution(trait)
    world.facts["captain"] = captain
    world.facts["foil"] = foil
    world.facts["helper"] = helper
    world.facts["treasure_cfg"] = treasure_cfg
    world.facts["threat_cfg"] = threat_cfg
    world.facts["safeguard_cfg"] = safeguard_cfg
    world.facts["delay"] = delay
    world.facts["relation"] = relation

    introduce(world, captain, foil, helper, treasure_cfg)
    world.para()
    boast(world, captain, treasure_cfg)
    warn(world, foil, captain, threat_cfg, treasure_cfg)

    if would_avert(relation, captain_age, foil_age, trait):
        back_down(world, captain, foil, safeguard_cfg)
        outcome = "averted"
    else:
        defy(world, captain, foil, treasure_cfg)
        world.para()
        mishap(world, threat_cfg, treasure_cfg)
        world.para()
        if safeguard_cfg.power >= threat_cfg.severity + delay:
            rescue(world, helper, foil, safeguard_cfg, threat_cfg)
            outcome = "saved"
        else:
            loss(world, helper, captain, foil, threat_cfg)
            outcome = "lost"

    world.para()
    lesson(world, helper, captain, foil, safeguard_cfg, outcome)
    safe_ending(world, captain, foil, safeguard_cfg, treasure_cfg, outcome)

    world.facts["outcome"] = outcome
    world.facts["lost_any"] = outcome == "lost"
    world.facts["averted"] = outcome == "averted"
    world.facts["saved"] = outcome == "saved"
    return world


PLACES = {
    "cove": Place(id="cove", shore="the little cove", scene="a little cove with black rocks", tags={"sea"}),
    "dunes": Place(id="dunes", shore="the sandy dunes", scene="warm dunes beside the sea", tags={"sea", "wind"}),
    "pier": Place(id="pier", shore="the old pier beach", scene="a beach beside an old wooden pier", tags={"sea", "gull"}),
}

TREASURES = {
    "sandwich": Treasure(
        id="sandwich",
        label="sandwich",
        phrase="a jam sandwich folded in foil",
        exposed_phrase="the foil-wrapped sandwich",
        plural=False,
        lightness=1,
        tags={"foil", "food"},
    ),
    "crackers": Treasure(
        id="crackers",
        label="crackers",
        phrase="a little cup of round crackers",
        exposed_phrase="the crackers",
        plural=True,
        lightness=3,
        tags={"food", "wind"},
    ),
    "bun": Treasure(
        id="bun",
        label="bun",
        phrase="a raisin bun on a napkin",
        exposed_phrase="the bun",
        plural=False,
        lightness=2,
        tags={"food"},
    ),
}

THREATS = {
    "gull": Threat(
        id="gull",
        label="gull",
        approach="a fat gull marched over sideways",
        danger="that gull will think we laid out a snack parade just for it",
        effect="With one rude peck, the bird nearly made off with the treasure.",
        severity=2,
        suits={"sandwich", "crackers", "bun"},
        tags={"gull"},
    ),
    "wind": Threat(
        id="wind",
        label="wind",
        approach="a sudden gust ran laughing down the beach",
        danger="the wind will toss it all over the place",
        effect="The treasure skittered and spun, and the pirate ship almost lost its lunch to the air.",
        severity=1,
        suits={"crackers", "bun"},
        tags={"wind"},
    ),
    "wave": Threat(
        id="wave",
        label="wave",
        approach="a sneaky wave crept farther up the sand than before",
        danger="the next wave will slap it wet",
        effect="Cold water rushed over the edge of the towel and soaked the deck.",
        severity=3,
        suits={"sandwich", "bun"},
        tags={"wave", "water"},
    ),
}

SAFEGUARDS = {
    "tin": Safeguard(
        id="tin",
        label="lidded tin",
        phrase="a little lidded tin",
        prep="pack it in the lidded tin first",
        action="snapped the lid shut on the little tin and whisked it out of danger",
        power=2,
        counters={"gull", "wind"},
        tags={"container", "tin"},
    ),
    "bucket": Safeguard(
        id="bucket",
        label="sand bucket",
        phrase="a clean sand bucket with a plate on top",
        prep="set it high in the clean bucket with a plate over it",
        action="lifted the treasure into the clean bucket and set it on a dry rock above the wash",
        power=3,
        counters={"wave", "gull"},
        tags={"bucket", "water"},
    ),
    "bag": Safeguard(
        id="bag",
        label="drawstring bag",
        phrase="a striped drawstring bag",
        prep="tie it into the drawstring bag first",
        action="cinched the striped bag tight before the beach could steal another crumb",
        power=1,
        counters={"wind"},
        tags={"bag", "wind"},
    ),
}

GIRL_NAMES = ["Nell", "Lila", "Mia", "Tess", "Ruby", "Ada", "Poppy", "June"]
BOY_NAMES = ["Ben", "Tom", "Max", "Finn", "Leo", "Otto", "Jude", "Sam"]
TRAITS = ["careful", "steady", "sensible", "watchful", "curious"]

HELPERS = ["mother", "father", "aunt", "uncle"]


@dataclass
class StoryParams:
    place: str
    treasure: str
    threat: str
    safeguard: str
    captain: str
    captain_gender: str
    foil: str
    foil_gender: str
    helper: str
    trait: str
    delay: int = 0
    captain_age: int = 5
    foil_age: int = 7
    relation: str = "siblings"
    seed: Optional[int] = None


KNOWLEDGE = {
    "foil": [
        (
            "What is foil?",
            "Foil is a very thin, shiny sheet of metal that people often use to wrap food. It crinkles loudly and can help keep a snack covered."
        )
    ],
    "gull": [
        (
            "What is a gull?",
            "A gull is a seaside bird with strong wings and a sharp beak. Gulls often look for food near people at the beach."
        )
    ],
    "wind": [
        (
            "What can wind do to light things on a beach?",
            "Wind can push, flip, and scatter light things like napkins or crackers. That is why people hold them down or tuck them into bags."
        )
    ],
    "wave": [
        (
            "Why can a wave reach farther than you expect?",
            "Some waves slide farther up the sand than the one before them. If you leave things low on the beach, the water can suddenly reach them."
        )
    ],
    "tin": [
        (
            "Why is a lidded tin useful for snacks?",
            "A lidded tin keeps a snack tucked inside and protected. The lid helps stop birds, sand, and wind from getting at the food."
        )
    ],
    "bucket": [
        (
            "How can a bucket help keep things dry at the beach?",
            "A bucket can lift things up off the wet sand. If you keep it high and covered, a wave is less likely to reach what is inside."
        )
    ],
    "bag": [
        (
            "Why does a drawstring bag help on a windy day?",
            "A drawstring bag closes tight around what is inside. That keeps light things from blowing away."
        )
    ],
    "sea": [
        (
            "Why does the sea make people feel wonder?",
            "The sea is wide, bright, and always moving, so it can feel huge and surprising. People often feel wonder when they look at something so big and lively."
        )
    ],
}
KNOWLEDGE_ORDER = ["foil", "gull", "wind", "wave", "tin", "bucket", "bag", "sea"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    foil = f["foil"]
    threat = f["threat_cfg"]
    treasure = f["treasure_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a pirate-flavored story for a 3-to-5-year-old that uses the words "foil" and "wonder" and includes funny dialogue between two children on a beach.',
            f"Tell a gentle pirate tale where boastful {captain.id} wants to show off {treasure.phrase}, but {foil.id}, the practical foil, talks {captain.pronoun('object')} into using {f['safeguard_cfg'].phrase} before {threat.label} can cause trouble.",
            f"Write a humorous story where an older sibling keeps a seaside pirate game from going wrong, and the ending shows the children enjoying their treasure safely.",
        ]
    if outcome == "lost":
        return [
            f'Write a child-facing pirate tale with dialogue, humor, and the words "foil" and "wonder".',
            f"Tell a beach story where {captain.id} ignores {foil.id}'s warning, {threat.label} spoils the pirate treasure, and the children learn that noticing danger matters more than boasting.",
            f"Write a gentle cautionary story with a funny pirate voice and a soft landing, where some lunch is lost but the children end wiser and kinder.",
        ]
    return [
        f'Write a pirate-tale story for a 3-to-5-year-old that includes dialogue, humor, and the words "foil" and "wonder".',
        f"Tell a seaside story where a boastful child captain is balanced by a careful foil, {threat.label} causes a quick scare, and the treasure is saved with {f['safeguard_cfg'].phrase}.",
        f"Write a playful beach adventure with pirate talk, a funny middle problem, and an ending image that shows the children keeping their treasure safely.",
    ]


def pair_noun(captain: Entity, foil: Entity, relation: str) -> str:
    if relation == "siblings":
        if captain.type == "boy" and foil.type == "boy":
            return "two brothers"
        if captain.type == "girl" and foil.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    foil = f["foil"]
    helper = f["helper"]
    treasure = f["treasure_cfg"]
    threat = f["threat_cfg"]
    safeguard = f["safeguard_cfg"]
    outcome = f["outcome"]
    relation = f["relation"]
    pair = pair_noun(captain, foil, relation)
    qa = [
        (
            "Who is the story about?",
            f"It is about {pair}, {captain.id} and {foil.id}, who were pretending to be pirates at the beach. {helper.label_word.capitalize()} stayed nearby while their game turned into a small real problem."
        ),
        (
            "Why did the children feel wonder at the beginning?",
            f"They looked at the big glittering sea and felt small in a happy way. The wide water made their pirate game feel grand before anything went wrong."
        ),
        (
            f"How was {foil.id} a foil to {captain.id}?",
            f"{captain.id} was boastful and dramatic, while {foil.id} was practical and quick to notice danger. Their different ways of thinking made the warning and the lesson matter."
        ),
        (
            f"What was the pirate treasure?",
            f"The children were treating {treasure.phrase} like pirate treasure. Making the snack part of the game is what put it right in the path of {threat.label if outcome != 'averted' else 'trouble'}."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"Why did {captain.id} change {captain.pronoun('possessive')} mind?",
                f"{foil.id} warned clearly, and because {foil.pronoun()} was the older sibling, {captain.id} took the warning seriously. They used {safeguard.phrase} before the danger reached them, so the problem never got to start."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the treasure safe inside {safeguard.phrase} while the children kept playing by the shining sea. The final image proves that they learned to mix fun with noticing."
            )
        )
    elif outcome == "saved":
        qa.append(
            (
                f"What happened when {captain.id} ignored the warning?",
                f"{threat.effect} The trouble happened because {captain.id} left {treasure.exposed_phrase} out on the pretend deck instead of protecting it first."
            )
        )
        qa.append(
            (
                f"How was the treasure saved?",
                f"{foil.id} and {helper.label_word} used {safeguard.phrase} to protect it. Their quick action foiled the mishap before the treasure was truly lost."
            )
        )
        qa.append(
            (
                f"What did {captain.id} learn?",
                f"{captain.id} learned that a good captain does not only sound brave. A better captain also listens when someone careful notices a real risk."
            )
        )
    else:
        qa.append(
            (
                f"Could they save all the treasure?",
                f"No. {helper.label_word.capitalize()} came quickly, but some of it was already gone. The loss happened because the danger had too much time before anyone tucked the treasure away."
            )
        )
        qa.append(
            (
                f"Why was {foil.id}'s warning important?",
                f"{foil.id} had noticed exactly what {threat.label} could do to {treasure.exposed_phrase}. The story shows that paying attention can matter more than making a grand speech."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended gently, with the children packing the rest into {safeguard.phrase} and laughing again. Even though part of the treasure was lost, the ending proves they changed how they played."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"sea"} | set(world.facts["treasure_cfg"].tags) | set(world.facts["threat_cfg"].tags) | set(world.facts["safeguard_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} delay={world.facts.get('delay')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="cove",
        treasure="sandwich",
        threat="gull",
        safeguard="tin",
        captain="Nell",
        captain_gender="girl",
        foil="Ben",
        foil_gender="boy",
        helper="aunt",
        trait="careful",
        delay=0,
        captain_age=5,
        foil_age=7,
        relation="siblings",
    ),
    StoryParams(
        place="dunes",
        treasure="crackers",
        threat="wind",
        safeguard="bag",
        captain="Max",
        captain_gender="boy",
        foil="Ruby",
        foil_gender="girl",
        helper="father",
        trait="steady",
        delay=0,
        captain_age=6,
        foil_age=6,
        relation="friends",
    ),
    StoryParams(
        place="pier",
        treasure="bun",
        threat="wave",
        safeguard="bucket",
        captain="Tom",
        captain_gender="boy",
        foil="Lila",
        foil_gender="girl",
        helper="mother",
        trait="watchful",
        delay=1,
        captain_age=6,
        foil_age=5,
        relation="siblings",
    ),
    StoryParams(
        place="cove",
        treasure="sandwich",
        threat="wave",
        safeguard="bucket",
        captain="Ada",
        captain_gender="girl",
        foil="June",
        foil_gender="girl",
        helper="uncle",
        trait="sensible",
        delay=0,
        captain_age=4,
        foil_age=7,
        relation="siblings",
    ),
]


def explain_rejection(treasure: Treasure, threat: Threat, safeguard: Safeguard) -> str:
    if not treasure_at_risk(treasure, threat):
        return (
            f"(No story: {threat.label} would not make a believable problem for {treasure.label}. "
            f"Pick a treasure that this threat could really bother.)"
        )
    if threat.id not in safeguard.counters:
        return (
            f"(No story: {safeguard.label} is not a reasonable fix for {threat.label}. "
            f"Choose a safeguard that actually protects the treasure from that trouble.)"
        )
    return "(No story: that combination is not supported.)"


ASP_RULES = r"""
at_risk(T, H) :- treasure(T), threat(H), suits(H, T).
valid(T, H, S) :- at_risk(T, H), safeguard(S), counters(S, H).

older_foil :- relation(siblings), foil_age(FA), captain_age(CA), FA > CA.
cautious_now :- trait(T), cautious_trait(T).
averted :- older_foil, cautious_now.

trouble(Sev + D) :- chosen_threat(H), severity(H, Sev), delay(D).
saved :- chosen_safeguard(S), power(S, P), trouble(V), P >= V.

outcome(averted) :- averted.
outcome(saved) :- not averted, saved.
outcome(lost) :- not averted, not saved.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        for tag in sorted(treasure.tags):
            lines.append(asp.fact("treasure_tag", tid, tag))
    for hid, threat in THREATS.items():
        lines.append(asp.fact("threat", hid))
        lines.append(asp.fact("severity", hid, threat.severity))
        for suit in sorted(threat.suits):
            lines.append(asp.fact("suits", hid, suit))
    for sid, safeguard in SAFEGUARDS.items():
        lines.append(asp.fact("safeguard", sid))
        lines.append(asp.fact("power", sid, safeguard.power))
        for counter in sorted(safeguard.counters):
            lines.append(asp.fact("counters", sid, counter))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join(
        [
            asp.fact("chosen_threat", params.threat),
            asp.fact("chosen_safeguard", params.safeguard),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("captain_age", params.captain_age),
            asp.fact("foil_age", params.foil_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
    parser = build_parser()
    for seed in range(20):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
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
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: pirate children, a silly seaside threat, and the careful foil who helps save the treasure."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--safeguard", choices=SAFEGUARDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how much head start the trouble gets")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump the world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treasure and args.threat and args.safeguard:
        treasure = TREASURES[args.treasure]
        threat = THREATS[args.threat]
        safeguard = SAFEGUARDS[args.safeguard]
        if not valid_combo(treasure, threat, safeguard):
            raise StoryError(explain_rejection(treasure, threat, safeguard))

    combos = [
        combo
        for combo in valid_combos()
        if (args.treasure is None or combo[0] == args.treasure)
        and (args.threat is None or combo[1] == args.threat)
        and (args.safeguard is None or combo[2] == args.safeguard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    treasure_id, threat_id, safeguard_id = rng.choice(sorted(combos))
    place = args.place or rng.choice(sorted(PLACES))
    captain, captain_gender = _pick_kid(rng)
    foil, foil_gender = _pick_kid(rng, avoid=captain)
    helper = args.helper or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    relation = rng.choice(["siblings", "friends"])
    captain_age, foil_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        place=place,
        treasure=treasure_id,
        threat=threat_id,
        safeguard=safeguard_id,
        captain=captain,
        captain_gender=captain_gender,
        foil=foil,
        foil_gender=foil_gender,
        helper=helper,
        trait=trait,
        delay=delay,
        captain_age=captain_age,
        foil_age=foil_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        treasure = TREASURES[params.treasure]
        threat = THREATS[params.threat]
        safeguard = SAFEGUARDS[params.safeguard]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err
    if not valid_combo(treasure, threat, safeguard):
        raise StoryError(explain_rejection(treasure, threat, safeguard))
    world = tell(
        place=place,
        treasure_cfg=treasure,
        threat_cfg=threat,
        safeguard_cfg=safeguard,
        captain_name_value=params.captain,
        captain_gender=params.captain_gender,
        foil_name=params.foil,
        foil_gender=params.foil_gender,
        helper_type=params.helper,
        trait=params.trait,
        delay=params.delay,
        captain_age=params.captain_age,
        foil_age=params.foil_age,
        relation=params.relation,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
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
        print(f"{len(combos)} valid (treasure, threat, safeguard) combos:\n")
        for treasure, threat, safeguard in combos:
            print(f"  {treasure:10} {threat:8} {safeguard}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.captain} & {p.foil}: {p.treasure} vs {p.threat} with {p.safeguard} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
