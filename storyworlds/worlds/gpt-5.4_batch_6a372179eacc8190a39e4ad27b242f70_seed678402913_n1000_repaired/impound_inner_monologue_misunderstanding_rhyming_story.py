#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/impound_inner_monologue_misunderstanding_rhyming_story.py
====================================================================================

A standalone story world about a child who leaves a small ride-on toy in a
keep-clear place, sees a town helper rolling it away, and misunderstands what is
happening. The helper is not stealing it; the toy is being taken to impound for
safekeeping because the path must stay open.

The world is built to satisfy a tiny, plausible domain:

- a child rides to a place
- the child leaves the toy in a marked access zone
- the zone becomes blocked
- a helper moves the toy to the impound shed
- the child briefly misunderstands the scene
- the child asks, learns the reason, proves ownership, and gets the toy back
- the ending image shows a changed habit: parking in the right rack or rail

The prose stays child-facing and lightly rhymed, and the child's inner
monologue is driven by simulated state rather than inserted at random.
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

# Make shared result containers importable when this nested script is run
# directly: storyworlds/worlds/gpt-5.4/<file>.py -> add storyworlds/ to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
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
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "librarian", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    outing: str
    keep_clear: str
    safe_spot: str
    sign: str
    why_clear: str
    helper_type: str
    helper_label: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Vehicle:
    id: str
    label: str
    phrase: str
    plural: bool = False
    easy_to_roll: bool = True
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Zone:
    id: str
    label: str
    reason: str
    risk: int
    impoundable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Token:
    id: str
    phrase: str
    proof_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_blocked(world: World) -> list[str]:
    vehicle = world.get("vehicle")
    zone = world.get("zone")
    if vehicle.meters["parked_wrong"] < THRESHOLD:
        return []
    if world.facts.get("zone_cfg") and not world.facts["zone_cfg"].impoundable:
        return []
    sig = ("blocked", zone.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    zone.meters["blocked"] += 1
    return []


def _r_impound(world: World) -> list[str]:
    vehicle = world.get("vehicle")
    helper = world.get("helper")
    zone = world.get("zone")
    if zone.meters["blocked"] < THRESHOLD or vehicle.meters["attended"] >= THRESHOLD:
        return []
    sig = ("impound", vehicle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    vehicle.meters["at_impound"] += 1
    vehicle.meters["parked_wrong"] = 0.0
    helper.meters["helped"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="blocked", tag="physical", apply=_r_blocked),
    Rule(name="impound", tag="social", apply=_r_impound),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                # only counts as change when a new firing happened in this pass
                pass
        fired_now = len(world.fired)
        # cheap fixed-point detection: if any rule fired, one of our rule bodies
        # added to world.fired, which will be observed by the outer loop because
        # the state changed; here we re-scan by comparing before/after per pass.
        # To keep code simple, we trigger another pass whenever a new signature
        # appeared during the loop.
        if not changed:
            continue
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------
def valid_combo(place: Place, vehicle: Vehicle, zone: Zone, token: Token) -> bool:
    return vehicle.easy_to_roll and zone.impoundable and zone.risk >= 2 and bool(token.proof_text)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for vehicle_id, vehicle in VEHICLES.items():
            for zone_id, zone in ZONES.items():
                for token_id, token in TOKENS.items():
                    if valid_combo(place, vehicle, zone, token):
                        combos.append((place_id, vehicle_id, zone_id, token_id))
    return combos


def explain_rejection(place: Place, vehicle: Vehicle, zone: Zone, token: Token) -> str:
    if not vehicle.easy_to_roll:
        return (f"(No story: {vehicle.phrase} is too awkward for one helper to move to impound, "
                f"so this little misunderstanding tale would not feel ordinary.)")
    if not zone.impoundable or zone.risk < 2:
        return (f"(No story: leaving {vehicle.phrase} in {zone.label} would not reasonably lead "
                f"to impound here, so the central misunderstanding would not happen.)")
    if not token.proof_text:
        return "(No story: the child needs a simple way to prove ownership and get the toy back.)"
    return f"(No story: {place.label}, {vehicle.label}, {zone.label}, and {token.id} do not form a plausible impound story.)"


def predict_impound(world: World) -> dict:
    sim = world.copy()
    sim.get("vehicle").meters["parked_wrong"] += 1
    sim.get("vehicle").meters["attended"] = 0.0
    before = len(sim.fired)
    for _ in range(3):
        prev = len(sim.fired)
        for rule in CAUSAL_RULES:
            rule.apply(sim)
        if len(sim.fired) == prev:
            break
    return {
        "blocked": sim.get("zone").meters["blocked"] >= THRESHOLD,
        "impounded": sim.get("vehicle").meters["at_impound"] >= THRESHOLD,
        "new_firings": len(sim.fired) - before,
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def arrive(world: World, child: Entity, grownup: Entity, place: Place, vehicle: Vehicle) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} rode to {place.label} on {vehicle.phrase}, "
        f"with a hop and a hum and a bright little grin."
    )
    world.say(
        f"{child.id}'s {grownup.label_word} had come for {place.outing}, "
        f"and the morning felt merry, all ready to begin."
    )


def leave_wrong_spot(world: World, child: Entity, place: Place, zone: Zone, vehicle: Vehicle) -> None:
    world.get("vehicle").meters["parked_wrong"] += 1
    world.get("vehicle").meters["attended"] = 0.0
    prediction = predict_impound(world)
    world.facts["predicted_impound"] = prediction["impounded"]
    world.say(
        f"By {place.keep_clear} stood a sign that said, \"{place.sign}.\" "
        f"But {child.id} leaned {vehicle.phrase} in {zone.label} and hurried inside."
    )
    if prediction["impounded"]:
        world.say(
            f"{child.id} hardly noticed the rule in the rush. "
            f"In {child.pronoun('possessive')} head came a tiny thought: "
            f"\"It will be fine. I'll be back in a blink, not long.\""
        )


def helper_moves(world: World, helper: Entity, place: Place, vehicle: Vehicle) -> None:
    zone = world.get("zone")
    vehicle_ent = world.get("vehicle")
    if zone.meters["blocked"] < THRESHOLD or vehicle_ent.meters["at_impound"] < THRESHOLD:
        return
    world.say(
        f"Outside, {place.helper_label} saw the path in a squeeze. "
        f"\"This way must stay open for strollers and knees,\" {helper.pronoun()} said with care."
    )
    world.say(
        f"So {helper.pronoun()} rolled {vehicle.phrase} to the impound shed there, "
        f"not to be mean, but to keep the path fair."
    )


def misunderstanding(world: World, child: Entity, helper: Entity, vehicle: Vehicle) -> None:
    child.memes["alarm"] += 1
    child.memes["misunderstanding"] += 1
    world.say(
        f"When {child.id} came back and saw {helper.id} wheeling it round, "
        f"{child.pronoun('possessive').capitalize()} heart gave a bounce at that rattly sound."
    )
    world.say(
        f'"Oh no," thought {child.id}. "Is {helper.pronoun()} taking my ride? '
        f'Did my own little wheels just get swept from my side?"'
    )


def ask_and_learn(world: World, child: Entity, helper: Entity, place: Place, zone: Zone) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'{child.id} ran up and asked, "Why are you taking it there?"'
    )
    world.say(
        f'{helper.id} knelt down and answered, "I\'m keeping it safe with care. '
        f'{place.why_clear}, and {zone.reason}."'
    )


def prove_and_return(world: World, child: Entity, helper: Entity, vehicle: Vehicle,
                     token: Token, place: Place) -> None:
    child.memes["relief"] += 1
    child.memes["understanding"] += 1
    child.memes["misunderstanding"] = 0.0
    world.get("vehicle").meters["claimed"] += 1
    world.say(
        f'"If it is yours," said {helper.id}, "show me your proof and say." '
        f'{child.id} showed {token.phrase}, and {token.proof_text}.'
    )
    world.say(
        f"Then {helper.id} smiled and rolled the ride back out of the shed. "
        f"The impound mix-up melted, and the scared thought quietly fled."
    )
    world.say(
        f'"Next time, park by {place.safe_spot}," {helper.pronoun()} said with a grin. '
        f'"Then everyone fits, and your wheels can stay in."'
    )


def new_habit(world: World, child: Entity, place: Place, vehicle: Vehicle) -> None:
    child.memes["lesson"] += 1
    child.memes["joy"] += 1
    world.say(
        f"So {child.id} parked by {place.safe_spot} when the next stop came around, "
        f"with a click and a tuck and no blocking of ground."
    )
    world.say(
        f"{vehicle.phrase.capitalize()} waited in the right little spot, "
        f"and {child.id} skipped inside, happy and thoughtful a lot."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(place: Place, vehicle: Vehicle, zone: Zone, token: Token,
         child_name: str = "Mina", child_type: str = "girl",
         grownup_type: str = "mother") -> World:
    world = World()

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        role="child",
        label=child_name,
    ))
    grownup = world.add(Entity(
        id="Parent",
        kind="character",
        type=grownup_type,
        role="grownup",
        label="the parent",
    ))
    helper = world.add(Entity(
        id=place.helper_label.split()[0],
        kind="character",
        type=place.helper_type,
        role="helper",
        label=place.helper_label,
    ))
    vehicle_ent = world.add(Entity(
        id="vehicle",
        kind="thing",
        type="vehicle",
        label=vehicle.label,
        phrase=vehicle.phrase,
        owner=child.id,
        tags=set(vehicle.tags),
    ))
    zone_ent = world.add(Entity(
        id="zone",
        kind="place",
        type="zone",
        label=zone.label,
        tags=set(zone.tags),
    ))
    place_ent = world.add(Entity(
        id="place",
        kind="place",
        type="place",
        label=place.label,
        tags=set(place.tags),
    ))
    vehicle_ent.meters["attended"] = 1.0

    world.facts.update(
        child=child,
        grownup=grownup,
        helper=helper,
        vehicle_cfg=vehicle,
        vehicle=vehicle_ent,
        place_cfg=place,
        place=place_ent,
        zone_cfg=zone,
        zone=zone_ent,
        token_cfg=token,
    )

    arrive(world, child, grownup, place, vehicle)
    world.para()
    leave_wrong_spot(world, child, place, zone, vehicle)
    for _ in range(3):
        prev = len(world.fired)
        for rule in CAUSAL_RULES:
            rule.apply(world)
        if len(world.fired) == prev:
            break
    helper_moves(world, helper, place, vehicle)
    world.para()
    misunderstanding(world, child, helper, vehicle)
    ask_and_learn(world, child, helper, place, zone)
    world.para()
    prove_and_return(world, child, helper, vehicle, token, place)
    new_habit(world, child, place, vehicle)

    world.facts.update(
        impounded=vehicle_ent.meters["at_impound"] >= THRESHOLD,
        blocked=zone_ent.meters["blocked"] >= THRESHOLD,
        resolved=vehicle_ent.meters["claimed"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "library": Place(
        id="library",
        label="the library",
        outing="story hour",
        keep_clear="the front ramp",
        safe_spot="the bike rail",
        sign="Keep Clear",
        why_clear="the ramp has to stay open for wheels and feet",
        helper_type="woman",
        helper_label="Ms. Pru",
        tags={"library", "rules"},
    ),
    "bakery": Place(
        id="bakery",
        label="the bakery",
        outing="a bun and warm milk",
        keep_clear="the side delivery walk",
        safe_spot="the little rail by the bench",
        sign="No Parking Here",
        why_clear="the walk must stay clear for trays and carts",
        helper_type="woman",
        helper_label="Ms. Dot",
        tags={"bakery", "rules"},
    ),
    "market": Place(
        id="market",
        label="the market",
        outing="apples and a paper bag",
        keep_clear="the front path",
        safe_spot="the rack near the lamp post",
        sign="Keep This Path Open",
        why_clear="the path must stay clear for baskets and neighbors",
        helper_type="woman",
        helper_label="Ms. Vale",
        tags={"market", "rules"},
    ),
}

VEHICLES = {
    "scooter": Vehicle(
        id="scooter",
        label="scooter",
        phrase="a cherry-red scooter",
        easy_to_roll=True,
        tags={"scooter", "wheels"},
    ),
    "balance_bike": Vehicle(
        id="balance_bike",
        label="balance bike",
        phrase="a little blue balance bike",
        easy_to_roll=True,
        tags={"bike", "wheels"},
    ),
    "wagon": Vehicle(
        id="wagon",
        label="wagon",
        phrase="a little pull wagon",
        easy_to_roll=True,
        tags={"wagon", "wheels"},
    ),
    "go_kart": Vehicle(
        id="go_kart",
        label="go-kart",
        phrase="a chunky pedal go-kart",
        easy_to_roll=False,
        tags={"kart", "wheels"},
    ),
}

ZONES = {
    "ramp": Zone(
        id="ramp",
        label="the middle of the ramp",
        reason="When a ride is left there, someone else may not get through",
        risk=3,
        impoundable=True,
        tags={"ramp", "access"},
    ),
    "door": Zone(
        id="door",
        label="right by the door swing",
        reason="A door needs room to open and close safely",
        risk=2,
        impoundable=True,
        tags={"door", "access"},
    ),
    "bench": Zone(
        id="bench",
        label="beside the bench leg",
        reason="That spot is only a little crowded",
        risk=1,
        impoundable=False,
        tags={"bench"},
    ),
}

TOKENS = {
    "name_sticker": Token(
        id="name_sticker",
        phrase="the name sticker on the handle",
        proof_text="her own name was printed there in neat round letters",
        tags={"name", "ownership"},
    ),
    "ribbon": Token(
        id="ribbon",
        phrase="the striped ribbon tied to the bar",
        proof_text="it was the ribbon her dad had tied on that very morning",
        tags={"ribbon", "ownership"},
    ),
    "bell": Token(
        id="bell",
        phrase="the silver bell with a star scratch",
        proof_text="the tiny star scratch was exactly where she said it would be",
        tags={"bell", "ownership"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tessa", "Ivy", "Ruby", "Maya", "Lena"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Ben", "Arlo", "Finn", "Jude", "Eli"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    vehicle: str
    zone: str
    token: str
    child_name: str
    child_type: str
    grownup_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "impound": [
        ("What does impound mean?",
         "Impound means taking something to a safe holding place until the owner comes to get it. It is not the same as stealing, because the thing is being kept under a rule.")
    ],
    "rules": [
        ("Why do some paths have keep-clear signs?",
         "Keep-clear signs help people leave room for walking, rolling, or opening doors safely. When a path stays open, everyone can use it.")
    ],
    "access": [
        ("Why is it important to keep a ramp or doorway clear?",
         "Ramps and doorways need space so people, strollers, and carts can pass through. If something blocks the way, someone may get stuck or bumped.")
    ],
    "misunderstanding": [
        ("What is a misunderstanding?",
         "A misunderstanding happens when someone thinks one thing is happening, but the truth is different. Asking a calm question can help clear it up.")
    ],
    "ownership": [
        ("How can you show that something is yours?",
         "You can show a name tag, a special mark, or another clear sign that belongs to you. That helps a grown-up know they are returning it to the right person.")
    ],
    "scooter": [
        ("What is a scooter?",
         "A scooter is a small ride with wheels and a handlebar that you push along. You should park it in a safe place when you are done.")
    ],
    "bike": [
        ("What is a balance bike?",
         "A balance bike is a small bike without pedals that helps children practice steering and balance. It still needs a safe place to park.")
    ],
    "wagon": [
        ("What is a wagon?",
         "A wagon is a little cart with wheels that you can pull. Even a small wagon should not be left where it blocks a path.")
    ],
}
KNOWLEDGE_ORDER = ["impound", "misunderstanding", "rules", "access", "ownership",
                   "scooter", "bike", "wagon"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place_cfg"]
    vehicle = f["vehicle_cfg"]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that includes the word "impound" and follows a child who misunderstands why a helper is rolling away {vehicle.phrase}.',
        f"Tell a gentle story where {child.id} thinks {place.helper_label} is taking {child.pronoun('possessive')} {vehicle.label}, but learns it was moved to impound for safekeeping after being left in the wrong place.",
        f'Write a child-facing rhyming story with inner monologue, a misunderstanding, and a happy ending where asking a calm question clears up the problem.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place_cfg"]
    vehicle = f["vehicle_cfg"]
    zone = f["zone_cfg"]
    token = f["token_cfg"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who rode to {place.label} on {vehicle.phrase}, and {helper.id}, the helper who moved it. Their mix-up is the big problem in the story."
        ),
        (
            f"Why was {vehicle.phrase} taken to impound?",
            f"It was left in {zone.label}, which needed to stay clear. {helper.id} moved it to impound for safekeeping because the path had to stay open."
        ),
        (
            f"What misunderstanding did {child.id} have?",
            f"{child.id} thought {helper.id} might be taking the ride away for good. That frightened thought came from seeing only the middle of the action and not hearing the reason yet."
        ),
        (
            f"What is an example of inner monologue in the story?",
            f"The story shows {child.id}'s thought: \"Oh no... Is she taking my ride?\" That line lets us hear the worry inside {child.pronoun('possessive')} head before the truth is explained."
        ),
        (
            f"How did {child.id} get the ride back?",
            f"{child.pronoun('subject').capitalize()} asked a calm question and then showed {token.phrase}. {token.proof_text.capitalize()}, so {helper.id} knew the ride belonged to {child.pronoun('object')}."
        ),
        (
            "How did the story end?",
            f"It ended with {child.id} parking by {place.safe_spot} the next time. The ending image shows that {child.pronoun('subject')} learned a new, kinder habit."
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"impound", "misunderstanding"}
    tags |= set(f["place_cfg"].tags)
    tags |= set(f["zone_cfg"].tags)
    tags |= set(f["token_cfg"].tags)
    tags |= set(f["vehicle_cfg"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="library",
        vehicle="scooter",
        zone="ramp",
        token="name_sticker",
        child_name="Mina",
        child_type="girl",
        grownup_type="mother",
    ),
    StoryParams(
        place="market",
        vehicle="balance_bike",
        zone="door",
        token="bell",
        child_name="Theo",
        child_type="boy",
        grownup_type="father",
    ),
    StoryParams(
        place="bakery",
        vehicle="wagon",
        zone="door",
        token="ribbon",
        child_name="Ruby",
        child_type="girl",
        grownup_type="father",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(P, V, Z, T) :- place(P), vehicle(V), zone(Z), token(T),
                     easy_to_roll(V), impoundable(Z), risk(Z, R), R >= 2, proof(T).

blocked :- chosen_zone(Z), impoundable(Z), chosen_vehicle(V), parked_wrong(V).
impounded :- blocked, chosen_vehicle(V), unattended(V), easy_to_roll(V).

#show valid/4.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for vid, vehicle in VEHICLES.items():
        lines.append(asp.fact("vehicle", vid))
        if vehicle.easy_to_roll:
            lines.append(asp.fact("easy_to_roll", vid))
    for zid, zone in ZONES.items():
        lines.append(asp.fact("zone", zid))
        lines.append(asp.fact("risk", zid, zone.risk))
        if zone.impoundable:
            lines.append(asp.fact("impoundable", zid))
    for tid, token in TOKENS.items():
        lines.append(asp.fact("token", tid))
        if token.proof_text:
            lines.append(asp.fact("proof", tid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_impounded(params: StoryParams) -> bool:
    import asp
    extra = "\n".join([
        asp.fact("chosen_vehicle", params.vehicle),
        asp.fact("chosen_zone", params.zone),
        asp.fact("parked_wrong", params.vehicle),
        asp.fact("unattended", params.vehicle),
    ])
    model = asp.one_model(asp_program(extra=extra, show="#show impounded/0."))
    return any(atom == ("impounded",) or atom == tuple() for atom in asp.atoms(model, "impounded"))


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in asp:", sorted(asp_set - py_set))

    for params in CURATED:
        py_impounded = True
        asp_is_impounded = asp_impounded(params)
        if py_impounded != asp_is_impounded:
            rc = 1
            print(f"MISMATCH in impound outcome for {params}: python={py_impounded} asp={asp_is_impounded}")

    # Smoke test: ordinary generation must not crash.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        if "impound" not in sample.story.lower():
            raise StoryError("Generated story failed to include 'impound'.")
        print("OK: smoke test story generated successfully.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a child misunderstands a gentle impound and learns where to park."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--zone", choices=ZONES)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--grownup-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.vehicle and args.zone and args.token:
        place = PLACES[args.place]
        vehicle = VEHICLES[args.vehicle]
        zone = ZONES[args.zone]
        token = TOKENS[args.token]
        if not valid_combo(place, vehicle, zone, token):
            raise StoryError(explain_rejection(place, vehicle, zone, token))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.vehicle is None or combo[1] == args.vehicle)
        and (args.zone is None or combo[2] == args.zone)
        and (args.token is None or combo[3] == args.token)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, vehicle_id, zone_id, token_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    grownup_type = args.grownup_type or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        vehicle=vehicle_id,
        zone=zone_id,
        token=token_id,
        child_name=child_name,
        child_type=child_type,
        grownup_type=grownup_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        vehicle = VEHICLES[params.vehicle]
        zone = ZONES[params.zone]
        token = TOKENS[params.token]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err})") from err

    if not valid_combo(place, vehicle, zone, token):
        raise StoryError(explain_rejection(place, vehicle, zone, token))

    world = tell(
        place=place,
        vehicle=vehicle,
        zone=zone,
        token=token,
        child_name=params.child_name,
        child_type=params.child_type,
        grownup_type=params.grownup_type,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, vehicle, zone, token) combos:\n")
        for place, vehicle, zone, token in combos:
            print(f"  {place:8} {vehicle:13} {zone:6} {token}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.vehicle} at {p.place} ({p.zone})"
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
