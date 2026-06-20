#!/usr/bin/env python3
"""A fairy-tale storyworld about willow, a dusty lamp, and a post office surprise.

Seed:
    Words: willow, dusty lamp
    Setting: post office
    Features: Surprise, Transformation
    Style: Fairy Tale

Internal source tale:
    In a village post office at dusk, a child helper finds one last strange
    piece of mail waiting under a dusty lamp. The child tends the lamp with a
    willow tool instead of giving up. Once the lamp burns true, the mail
    changes form and reveals a hidden surprise for someone who thought they had
    been forgotten. The ending image proves that the post office, the lamp, and
    the waiting heart have all been transformed by careful light.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def reflexive(self) -> str:
        if self.type == "girl":
            return "herself"
        if self.type == "boy":
            return "himself"
        return "themself"


@dataclass(frozen=True)
class Office:
    key: str
    name: str
    lane: str
    postmaster: str
    counter_detail: str
    willow_detail: str
    dusk_detail: str
    ending_glow: str
    support_keys: tuple[str, ...]
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Delivery:
    key: str
    support_key: str
    parcel_label: str
    parcel_type: str
    concern_line: str
    clue_line: str
    worry_line: str
    reveal_line: str
    surprise_line: str
    recipient_name: str
    destination: str
    ending_image: str
    lesson: str
    outcome: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Ritual:
    key: str
    support_key: str
    tool_label: str
    action_line: str
    lamp_change_line: str
    result_line: str
    afterglow_line: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Event:
    key: str
    subject: str
    detail: str
    consequence: str = ""


@dataclass
class StoryParams:
    office: str
    delivery: str
    ritual: str
    name: str
    gender: str
    trait: str
    seed: int | None = None


@dataclass(frozen=True)
class Rule:
    name: str
    apply: Callable[["World"], bool]


class World:
    def __init__(self, params: StoryParams, office: Office, delivery: Delivery, ritual: Ritual) -> None:
        self.params = params
        self.office = office
        self.delivery = delivery
        self.ritual = ritual
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[Event] = []
        self.fired: set[tuple[object, ...]] = set()
        self.fired_names: list[str] = []
        self.facts: dict[str, object] = {
            "support_key": delivery.support_key,
            "lamp_restored": False,
            "mail_revealed": False,
            "route_known": False,
            "delivered": False,
            "surprise_known": False,
        }

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, sentence: str) -> None:
        sentence = sentence.strip()
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def record(self, key: str, subject: str, detail: str, consequence: str = "") -> None:
        self.history.append(Event(key, subject, detail, consequence))

    def trace(self) -> str:
        lines = [
            f"params: {self.params}",
            f"support_key: {self.facts['support_key']}",
            f"lamp_restored: {self.facts['lamp_restored']}",
            f"mail_revealed: {self.facts['mail_revealed']}",
            f"route_known: {self.facts['route_known']}",
            f"delivered: {self.facts['delivered']}",
            f"surprise_known: {self.facts['surprise_known']}",
            f"fired_rules: {', '.join(self.fired_names) if self.fired_names else 'none'}",
        ]
        for entity in self.entities.values():
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            lines.append(f"  {entity.id} | {entity.kind} | {entity.type} | {entity.label or entity.id}")
            if entity.role:
                lines.append(f"    role={entity.role}")
            if meters:
                lines.append(f"    meters={meters}")
            if memes:
                lines.append(f"    memes={memes}")
        if self.history:
            lines.append("  history:")
            for event in self.history:
                tail = f" -> {event.consequence}" if event.consequence else ""
                lines.append(f"    {event.key}: {event.subject} | {event.detail}{tail}")
        return "\n".join(lines)


def _mark(world: World, name: str, *parts: object) -> bool:
    sig = (name, *parts)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.fired_names.append(name)
    return True


def _ensure_sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    if text[-1] in ".!?":
        return text
    return f"{text}."


def _lower_first(text: str) -> str:
    if not text:
        return text
    return text[0].lower() + text[1:]


def _r_closing_worry(world: World) -> bool:
    hero = world.get("hero")
    office = world.get("office")
    parcel = world.get("parcel")
    lamp = world.get("lamp")
    if (
        office.meters["closing_hour"] < THRESHOLD
        or parcel.meters["awaiting_route"] < THRESHOLD
        or lamp.meters["dusty"] < THRESHOLD
    ):
        return False
    if not _mark(world, "closing_worry", hero.id):
        return False
    hero.memes["concern"] += 1
    hero.memes["care"] += 1
    office.meters["hush"] += 1
    return True


def _r_lamp_renewed(world: World) -> bool:
    hero = world.get("hero")
    lamp = world.get("lamp")
    office = world.get("office")
    if hero.meters["tended_lamp"] < THRESHOLD:
        return False
    if world.ritual.support_key != world.delivery.support_key:
        return False
    if world.delivery.support_key not in world.office.support_keys:
        return False
    if not _mark(world, "lamp_renewed", lamp.id):
        return False
    lamp.meters["dusty"] = 0.0
    lamp.meters["clear"] += 1
    lamp.meters["glowing"] += 1
    office.meters["lit_counter"] += 1
    hero.memes["hope"] += 1
    world.facts["lamp_restored"] = True
    return True


def _r_mail_revealed(world: World) -> bool:
    hero = world.get("hero")
    parcel = world.get("parcel")
    if hero.meters["raised_mail"] < THRESHOLD or not world.facts["lamp_restored"]:
        return False
    if not _mark(world, "mail_revealed", parcel.id):
        return False
    parcel.meters["transformed"] += 1
    parcel.meters["known"] += 1
    hero.memes["wonder"] += 1
    hero.memes["surprise"] += 1
    world.facts["mail_revealed"] = True
    world.facts["route_known"] = True
    world.facts["surprise_known"] = True
    return True


def _r_delivery_made(world: World) -> bool:
    hero = world.get("hero")
    recipient = world.get("recipient")
    parcel = world.get("parcel")
    if hero.meters["carried_mail"] < THRESHOLD or not world.facts["route_known"]:
        return False
    if not _mark(world, "delivery_made", recipient.id):
        return False
    hero.memes["joy"] += 1
    recipient.memes["gratitude"] += 1
    parcel.meters["delivered"] += 1
    world.facts["delivered"] = True
    return True


def _r_room_blessed(world: World) -> bool:
    office = world.get("office")
    lamp = world.get("lamp")
    if not world.facts["delivered"]:
        return False
    if not _mark(world, "room_blessed", office.id):
        return False
    office.meters["glowing"] += 1
    lamp.memes["transformation"] += 1
    return True


RULES = [
    Rule("closing_worry", _r_closing_worry),
    Rule("lamp_renewed", _r_lamp_renewed),
    Rule("mail_revealed", _r_mail_revealed),
    Rule("delivery_made", _r_delivery_made),
    Rule("room_blessed", _r_room_blessed),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            if rule.apply(world):
                changed = True


OFFICES: dict[str, Office] = {
    "willow_window": Office(
        key="willow_window",
        name="the Willow Window Post Office",
        lane="Willow Lane",
        postmaster="Postmaster Elva",
        counter_detail="A willow sorting arch bent over the counter like a green ribbon frozen in mid-sway.",
        willow_detail="Beside the parcel scale stood a crock full of willow ties and narrow willow tools for bundling letters.",
        dusk_detail="Outside, dusk laid violet color over the cobbles, and the brass bell above the door had already rung the hour of last collections.",
        ending_glow="The front panes held the lamp's gold so softly that the whole post office looked newly awakened.",
        support_keys=("glow", "warmth"),
        tags=("post_office", "willow"),
    ),
    "bellstep": Office(
        key="bellstep",
        name="the Bellstep Post Office",
        lane="Bellstep Lane",
        postmaster="Postmaster Rowan",
        counter_detail="Willow baskets slept beneath the stamp shelf, and the sorting table stood under a wall of tiny numbered pigeonholes.",
        willow_detail="A loop of willow twine hung near the ledger, and a willow rack kept the polishing things from rolling away.",
        dusk_detail="Outside, the lane bells were calling the last walkers home, but one stubborn piece of mail still waited indoors.",
        ending_glow="The numbered slots shone as if each one held a tame star for the night shift.",
        support_keys=("warmth", "shadow"),
        tags=("post_office", "willow"),
    ),
    "river_arch": Office(
        key="river_arch",
        name="the River Arch Post Office",
        lane="River Arch",
        postmaster="Postmaster Fen",
        counter_detail="Willow branches were woven above the mail slots, and the long counter faced a window where the river carried sunset in copper strips.",
        willow_detail="A blue jar of willow twine and a narrow tray of willow-handled tools waited beside the registry book.",
        dusk_detail="Outside, the river was dimming into blue glass, and the post office had only a little time before closing.",
        ending_glow="Even the window latch flashed with clean light when the work was done.",
        support_keys=("glow", "shadow"),
        tags=("post_office", "willow"),
    ),
}


DELIVERIES: dict[str, Delivery] = {
    "hidden_invitation": Delivery(
        key="hidden_invitation",
        support_key="glow",
        parcel_label="a pale envelope with no address on its front",
        parcel_type="envelope",
        concern_line="No one dared send it out while the paper looked blank, for a letter with no name can wander all night.",
        clue_line="Yet its tiny willow seal glittered whenever even the faintest thread of lamplight touched it.",
        worry_line="What if the letter has forgotten its own home",
        reveal_line="As the clear light crossed the paper, silver ink climbed out of hiding and wrote the name of Old Neri the clockmender.",
        surprise_line="Inside waited an invitation to a surprise supper from the whole village, signed by neighbors who had kept the kind secret for days.",
        recipient_name="Old Neri",
        destination="the clock shop at the end of Willow Lane",
        ending_image="At the end, Old Neri stood in his doorway holding the shining envelope, and the post office windows glowed back at him like friendly clocks.",
        lesson="A careful light can wake what kindness has hidden.",
        outcome="invitation_delivered",
        tags=("glow", "surprise", "ink"),
    ),
    "paper_garden_box": Delivery(
        key="paper_garden_box",
        support_key="warmth",
        parcel_label="a squat brown parcel tied with string and stamped with a sleeping flower",
        parcel_type="box",
        concern_line="The string would not loosen, and no one wished to tug rude hands across a parcel that seemed to be waiting for the right hour.",
        clue_line="A sweet smell like summer bread drifted from the knot whenever the dusty lamp gave off a shy little breath of heat.",
        worry_line="What if the parcel has turned stubborn forever",
        reveal_line="Warm light softened the wax flower until the little box opened and a folded paper garden lifted itself into shape across the counter.",
        surprise_line="Beneath the paper leaves lay a surprise ribbon of thanks for Marta the gardener, woven by children whose pumpkins she had saved after the spring hail.",
        recipient_name="Marta",
        destination="the greenhouse behind the market square",
        ending_image="By the end, Marta wore the ribbon on her sleeve while the paper garden stood open on the post office counter like a tiny midsummer hedge.",
        lesson="Gentle warmth can open what force would only crease.",
        outcome="garden_box_delivered",
        tags=("warmth", "surprise", "paper"),
    ),
    "swallow_shadow_packet": Delivery(
        key="swallow_shadow_packet",
        support_key="shadow",
        parcel_label="a narrow gray packet as quiet as a feather",
        parcel_type="packet",
        concern_line="It made no sound at all, and still it seemed too alive to be shoved into the wrong sack before night.",
        clue_line="Whenever the lamp trembled, the packet threw a bird-shaped shadow over the mail wall.",
        worry_line="What if a night bird is trapped inside and fading away",
        reveal_line="When the lamp glass stood clean and true, the shadow gathered itself into a paper swallow that pointed its beak toward the river cottages.",
        surprise_line="Tucked in the packet was a bright thank-you star for Toma the ferryman, sent by children he had carried across the flood weeks before.",
        recipient_name="Toma",
        destination="the last blue cottage by the river",
        ending_image="By the end, the paper swallow perched above Toma's mantel, and the once-dusty lamp in the post office burned clear as a little moon.",
        lesson="A true shadow can point the way when someone learns how to look.",
        outcome="swallow_packet_delivered",
        tags=("shadow", "surprise", "paper"),
    ),
}


RITUALS: dict[str, Ritual] = {
    "willow_cloth": Ritual(
        key="willow_cloth",
        support_key="glow",
        tool_label="a soft willow cloth",
        action_line="lifted the dusty lamp from its hook, wiped the glass in slow circles, and tied the cloth around the handle so it would not slip",
        lamp_change_line="The soot gave way, and the flame stopped sulking behind gray smudges.",
        result_line="The lamp changed from a dusty lamp into a clear honey lamp that could tell silver ink where to bloom.",
        afterglow_line="Its light lay across the counter like a warm ribbon unrolling itself.",
        tags=("glow", "repair"),
    ),
    "willow_oil": Ritual(
        key="willow_oil",
        support_key="warmth",
        tool_label="a bottle of willow-blossom oil",
        action_line="rubbed one shining drop into the dry hinge, trimmed the wick, and breathed the flame awake",
        lamp_change_line="The metal warmed, and the small stiff flame began to purr instead of sputter.",
        result_line="The lamp changed from a dusty lamp into a warm amber lamp that could coax folded things to open kindly.",
        afterglow_line="Its glow made the brass look almost baked by afternoon sun.",
        tags=("warmth", "repair"),
    ),
    "willow_brush": Ritual(
        key="willow_brush",
        support_key="shadow",
        tool_label="a willow whisk brush",
        action_line="brushed dust from the cutwork shade, set the chimney straight, and turned the lamp until its beam fell neatly over the parcels",
        lamp_change_line="The shade holes opened like tiny windows, and the wandering shadow suddenly learned its shape.",
        result_line="The lamp changed from a dusty lamp into a bright pattern-casting lamp that could teach a shadow to speak plainly.",
        afterglow_line="Little leaf-shaped lights danced over the pigeonholes.",
        tags=("shadow", "repair"),
    ),
}


GIRL_NAMES = ["Mira", "Elsie", "Nora", "Wren", "Lina", "Tansy"]
BOY_NAMES = ["Milo", "Theo", "Finn", "Alder", "Jules", "Otis"]
TRAITS = ["careful", "curious", "gentle", "brave", "patient", "thoughtful"]


def office_supports(office: Office, delivery: Delivery) -> bool:
    return delivery.support_key in office.support_keys


def ritual_matches(delivery: Delivery, ritual: Ritual) -> bool:
    return delivery.support_key == ritual.support_key


def valid_combo(office_key: str, delivery_key: str, ritual_key: str) -> bool:
    if office_key not in OFFICES or delivery_key not in DELIVERIES or ritual_key not in RITUALS:
        return False
    office = OFFICES[office_key]
    delivery = DELIVERIES[delivery_key]
    ritual = RITUALS[ritual_key]
    return office_supports(office, delivery) and ritual_matches(delivery, ritual)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for office_key in sorted(OFFICES):
        for delivery_key in sorted(DELIVERIES):
            for ritual_key in sorted(RITUALS):
                if valid_combo(office_key, delivery_key, ritual_key):
                    combos.append((office_key, delivery_key, ritual_key))
    return combos


def outcome_of(params: StoryParams) -> str:
    office = OFFICES[params.office]
    delivery = DELIVERIES[params.delivery]
    ritual = RITUALS[params.ritual]
    if not office_supports(office, delivery):
        return "office_mismatch"
    if not ritual_matches(delivery, ritual):
        return "ritual_mismatch"
    return delivery.outcome


def explain_rejection(office: Office, delivery: Delivery, ritual: Ritual) -> str:
    if not office_supports(office, delivery):
        return (
            f"No story: {office.name} does not physically support the "
            f"{delivery.support_key} lamp-and-mail reveal needed for {delivery.key}."
        )
    if not ritual_matches(delivery, ritual):
        return (
            f"No story: {ritual.tool_label} serves a {ritual.support_key} reveal, "
            f"but {delivery.key} needs a {delivery.support_key} transformation."
        )
    return "No story: this setup falls outside the willow post office rules."


def build_world(params: StoryParams) -> World:
    office = OFFICES[params.office]
    delivery = DELIVERIES[params.delivery]
    ritual = RITUALS[params.ritual]
    if not valid_combo(params.office, params.delivery, params.ritual):
        raise StoryError(explain_rejection(office, delivery, ritual))

    world = World(params, office, delivery, ritual)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.gender,
        label=params.name,
        role="child helper",
        traits=[params.trait],
    ))
    postmaster = world.add(Entity(
        id="postmaster",
        kind="character",
        type="postmaster",
        label=office.postmaster,
        role="postmaster",
    ))
    office_entity = world.add(Entity(
        id="office",
        kind="place",
        type="post_office",
        label=office.name,
        role="setting",
    ))
    lamp = world.add(Entity(
        id="lamp",
        kind="thing",
        type="lamp",
        label="the dusty lamp",
        role="lamp",
    ))
    parcel = world.add(Entity(
        id="parcel",
        kind="thing",
        type=delivery.parcel_type,
        label=delivery.parcel_label,
        role="mail",
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=ritual.tool_label,
        role="tool",
    ))
    recipient = world.add(Entity(
        id="recipient",
        kind="character",
        type="adult",
        label=delivery.recipient_name,
        role="recipient",
    ))

    hero.memes["wonder"] += 1
    office_entity.meters["closing_hour"] += 1
    lamp.meters["dusty"] += 1
    parcel.meters["awaiting_route"] += 1
    world.facts.update(
        hero_name=params.name,
        hero_trait=params.trait,
        postmaster_name=office.postmaster,
        destination=delivery.destination,
        recipient_name=delivery.recipient_name,
        parcel_label=delivery.parcel_label,
        tool_label=ritual.tool_label,
    )
    propagate(world)
    return world


def introduce(world: World) -> None:
    hero = world.get("hero")
    office = world.office
    world.say(
        f"Once upon a violet evening, {hero.label}, a {hero.traits[0]} little {hero.type}, helped close "
        f"{office.name}, the old post office on {office.lane}."
    )
    world.say(office.counter_detail)
    world.say(
        f"{office.willow_detail} Above the counter hung a dusty lamp, so gray with sleep that even its brass looked tired."
    )
    world.say(office.dusk_detail)
    world.record("opening", hero.label, f"helped in {office.name}", "the last piece of mail still waited")


def raise_tension(world: World) -> None:
    hero = world.get("hero")
    postmaster = world.get("postmaster")
    delivery = world.delivery
    world.say(
        f"Only one thing remained on the counter: {delivery.parcel_label}. {delivery.concern_line}"
    )
    world.say(delivery.clue_line)
    world.say(
        f"\"We cannot shut the post office while one true piece of mail still wonders where to go,\" said {postmaster.label}."
    )
    world.say(
        f"\"{delivery.worry_line}?\" {hero.label} whispered to {hero.reflexive()}, though {hero.pronoun()} kept both hands very still."
    )
    world.record("trouble", postmaster.label, delivery.concern_line, delivery.clue_line)


def turning_point(world: World) -> None:
    hero = world.get("hero")
    ritual = world.ritual
    delivery = world.delivery
    hero.meters["tended_lamp"] += 1
    propagate(world)
    if not world.facts["lamp_restored"]:
        raise StoryError("No story: the child tended the lamp, but the lamp never became a true revealing object.")

    world.say(
        f"So {hero.label} reached for {ritual.tool_label}, {ritual.action_line}."
    )
    world.say(ritual.lamp_change_line)
    world.say(ritual.result_line)
    world.say(ritual.afterglow_line)

    hero.meters["raised_mail"] += 1
    propagate(world)
    if not world.facts["mail_revealed"]:
        raise StoryError("No story: the restored lamp never transformed the waiting mail.")

    world.say(
        f"Then {hero.label} lifted the parcel into the new light. {delivery.reveal_line}"
    )
    world.say(delivery.surprise_line)
    world.record("turn", hero.label, ritual.action_line, delivery.reveal_line)


def resolution(world: World) -> None:
    hero = world.get("hero")
    postmaster = world.get("postmaster")
    recipient = world.get("recipient")
    delivery = world.delivery

    hero.meters["carried_mail"] += 1
    propagate(world)
    if not world.facts["delivered"]:
        raise StoryError("No story: the child learned the surprise but never completed the delivery.")

    world.say(
        f"With {postmaster.label} beside {hero.pronoun('object')}, {hero.label} hurried to {delivery.destination}, and {recipient.label} opened the door before the echo of their knock had faded."
    )
    world.say(
        f"When {recipient.label} saw what the lamp had revealed, the last worry in the evening went gentle. {delivery.lesson}"
    )
    world.say(
        f"They carried the wonder back in their smiles, and {_lower_first(world.office.ending_glow)}"
    )
    world.say(delivery.ending_image)
    world.record("resolution", hero.label, f"delivered the mail to {recipient.label}", delivery.ending_image)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    introduce(world)
    world.para()
    raise_tension(world)
    world.para()
    turning_point(world)
    resolution(world)
    return world


KNOWLEDGE: dict[str, list[tuple[str, str]]] = {
    "post_office": [
        (
            "Why does a post office matter in a fairy tale?",
            "A post office is a house of waiting messages. That makes it a natural place for secrets, kindness, and surprises to arrive in physical form.",
        )
    ],
    "glow": [
        (
            "Why can clear lamplight reveal hidden writing?",
            "A steady light shows what dimness keeps secret. In a fairy tale, that physical change can let a hidden name step into view.",
        )
    ],
    "warmth": [
        (
            "Why would warmth help a folded parcel change?",
            "Warmth softens stiff wax and paper without harming them. That makes it a gentle force for transformation instead of a rough one.",
        )
    ],
    "shadow": [
        (
            "How can a shadow become a clue?",
            "A shadow can show the shape of something that is not easy to see directly. Once the light is set right, the shadow stops confusing people and starts guiding them.",
        )
    ],
    "surprise": [
        (
            "What makes a surprise kind instead of cruel?",
            "A kind surprise brings hidden love or thanks to the right person. It leaves the world warmer than it was before.",
        )
    ],
    "transformation": [
        (
            "What transforms in this story world?",
            "Ordinary objects change when careful action meets the right physical condition. A dusty lamp becomes a truthful lamp, and waiting mail becomes readable or open at last.",
        )
    ],
}
KNOWLEDGE_ORDER = ["post_office", "glow", "warmth", "shadow", "surprise", "transformation"]


def generation_prompts(world: World) -> list[str]:
    hero = world.get("hero")
    delivery = world.delivery
    ritual = world.ritual
    return [
        'Write a TinyStories-style fairy tale that includes the words "willow" and "dusty lamp" and takes place in a post office.',
        f"Make the middle turn on a physical ritual: {hero.label} uses {ritual.tool_label}, and the lamp changes before the mail does.",
        f"Resolve the story with a surprise delivery for {delivery.recipient_name}, after {delivery.parcel_label} reveals its true message in the transformed light.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.get("hero")
    postmaster = world.get("postmaster")
    recipient = world.get("recipient")
    delivery = world.delivery
    ritual = world.ritual
    return [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a {hero.traits[0]} little {hero.type} helping in {world.office.name}. The child becomes the one who notices the clue and carries the final surprise.",
        ),
        (
            "Where does the story happen?",
            f"It happens in {world.office.name}, a post office full of willow details and evening hush. The setting matters because the last waiting piece of mail can only be saved before the doors close.",
        ),
        (
            "What problem kept the post office open?",
            f"The problem was {delivery.parcel_label}. {delivery.concern_line} That meant the child and {postmaster.label} could not finish closing the room.",
        ),
        (
            f"Why did {hero.label} pay attention to the lamp?",
            f"{hero.label} noticed that the clue changed with the weak light: {delivery.clue_line.lower()} That linked the waiting mail to the dusty lamp instead of to random magic.",
        ),
        (
            "How did the transformation begin?",
            f"It began when {hero.label} used {ritual.tool_label} and {ritual.action_line}. {ritual.result_line} The lamp had to change first so the mail could tell the truth afterward.",
        ),
        (
            "What surprise did the transformed mail reveal?",
            f"The transformed mail revealed this surprise: {delivery.surprise_line} Because the hidden message finally showed itself, the delivery became an act of kindness instead of a guess.",
        ),
        (
            "How did the ending prove that something had changed?",
            f"The ending image proved the change clearly: {delivery.ending_image} The lamp, the post office, and the waiting heart were all brighter than they had been at the start.",
        ),
        (
            f"Who received the final delivery?",
            f"{recipient.label} received it at {delivery.destination}. The journey mattered because the surprise was not complete until it reached the right pair of hands.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"post_office", "surprise", "transformation"} | set(world.delivery.tags) | set(world.ritual.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for idx, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{idx}. {prompt}")
    lines.append("")
    lines.append("== (2) Story-grounded questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Story world: willow, a dusty lamp, a post office, and a fairy-tale surprise transformation."
    )
    parser.add_argument("--office", choices=sorted(OFFICES))
    parser.add_argument("--delivery", choices=sorted(DELIVERIES))
    parser.add_argument("--ritual", choices=sorted(RITUALS))
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true", help="render every valid combination")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true", help="list valid combinations from the ASP gate")
    parser.add_argument("--verify", action="store_true", help="compare Python and ASP reasoning and smoke-test generated stories")
    parser.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return parser


def _pick_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if (args.office is None or combo[0] == args.office)
        and (args.delivery is None or combo[1] == args.delivery)
        and (args.ritual is None or combo[2] == args.ritual)
    ]
    if not combos:
        office = OFFICES[args.office or "willow_window"]
        delivery = DELIVERIES[args.delivery or "hidden_invitation"]
        ritual = RITUALS[args.ritual or "willow_cloth"]
        raise StoryError(explain_rejection(office, delivery, ritual))

    office_key, delivery_key, ritual_key = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    return StoryParams(
        office=office_key,
        delivery=delivery_key,
        ritual=ritual_key,
        name=args.name or _pick_name(rng, gender),
        gender=gender,
        trait=args.trait or rng.choice(TRAITS),
        seed=(args.seed or 1000) + index,
    )


ASP_RULES = r"""
valid(O,D,R) :-
    office(O), delivery(D), ritual(R),
    office_support(O,K), delivery_key(D,K), ritual_key(R,K).

outcome(office_mismatch) :-
    chosen_office(O), chosen_delivery(D),
    delivery_key(D,K), not office_support(O,K).

outcome(ritual_mismatch) :-
    chosen_office(O), chosen_delivery(D), chosen_ritual(R),
    delivery_key(D,K), office_support(O,K), ritual_key(R,RK), RK != K.

outcome(Out) :-
    chosen_office(O), chosen_delivery(D), chosen_ritual(R),
    valid(O,D,R), delivery_outcome(D,Out).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for office in OFFICES.values():
        lines.append(asp.fact("office", office.key))
        for key in office.support_keys:
            lines.append(asp.fact("office_support", office.key, key))
    for delivery in DELIVERIES.values():
        lines.append(asp.fact("delivery", delivery.key))
        lines.append(asp.fact("delivery_key", delivery.key, delivery.support_key))
        lines.append(asp.fact("delivery_outcome", delivery.key, delivery.outcome))
    for ritual in RITUALS.values():
        lines.append(asp.fact("ritual", ritual.key))
        lines.append(asp.fact("ritual_key", ritual.key, ritual.support_key))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import storyworlds.asp as asp

    chosen = "\n".join([
        asp.fact("chosen_office", params.office),
        asp.fact("chosen_delivery", params.delivery),
        asp.fact("chosen_ritual", params.ritual),
    ])
    model = asp.one_model(asp_program(extra=chosen, show="#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "no_outcome"


CURATED: list[StoryParams] = [
    StoryParams("willow_window", "hidden_invitation", "willow_cloth", "Mira", "girl", "careful"),
    StoryParams("willow_window", "paper_garden_box", "willow_oil", "Theo", "boy", "gentle"),
    StoryParams("bellstep", "paper_garden_box", "willow_oil", "Elsie", "girl", "patient"),
    StoryParams("bellstep", "swallow_shadow_packet", "willow_brush", "Milo", "boy", "thoughtful"),
    StoryParams("river_arch", "hidden_invitation", "willow_cloth", "Nora", "girl", "curious"),
    StoryParams("river_arch", "swallow_shadow_packet", "willow_brush", "Otis", "boy", "brave"),
]


def _story_checks(sample: StorySample) -> list[str]:
    problems: list[str] = []
    text = sample.story
    if "willow" not in text.lower():
        problems.append("story text lost required willow seed word")
    if "dusty lamp" not in text.lower():
        problems.append("story text lost required dusty lamp seed phrase")
    if "post office" not in text.lower():
        problems.append("story text lost required setting phrase")
    if text.count("\n\n") < 2:
        problems.append("story is missing a clear beginning, turn, and ending paragraph shape")
    if "changed from a dusty lamp" not in text and "opened and a folded paper garden" not in text and "paper swallow" not in text:
        problems.append("story is missing a visible transformation beat")
    if "surprise" not in text.lower() and "thank-you" not in text.lower():
        problems.append("story is missing a clear surprise beat")
    if "{" in text or "}" in text:
        problems.append("story leaked unresolved template markers")
    if len(sample.prompts) < 3 or len(sample.story_qa) < 6 or len(sample.world_qa) < 3:
        problems.append("prompt or QA sets are too thin")
    if "No story:" in text:
        problems.append("story leaked a failure string into prose")
    if "_" in text:
        problems.append("story leaked an internal id into prose")
    return problems


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: clingo gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("ASP/Python mismatch in valid combos:")
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))

    cases: list[StoryParams] = list(CURATED)
    cases.extend([
        StoryParams("bellstep", "hidden_invitation", "willow_cloth", "Mira", "girl", "careful"),
        StoryParams("willow_window", "swallow_shadow_packet", "willow_brush", "Theo", "boy", "thoughtful"),
        StoryParams("river_arch", "paper_garden_box", "willow_oil", "Nora", "girl", "gentle"),
        StoryParams("willow_window", "hidden_invitation", "willow_oil", "Milo", "boy", "brave"),
    ])
    empty = build_parser().parse_args([])
    for seed in range(60):
        params = resolve_params(empty, random.Random(seed), index=seed)
        params.seed = seed
        cases.append(params)

    mismatches = [params for params in cases if asp_outcome(params) != outcome_of(params)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"Outcome mismatch on {len(mismatches)}/{len(cases)} scenarios.")
        for params in mismatches[:5]:
            print(" ", params, asp_outcome(params), outcome_of(params))

    invalids = cases[len(CURATED):len(CURATED) + 4]
    for params in invalids:
        if outcome_of(params) == DELIVERIES[params.delivery].outcome:
            continue
        try:
            generate(params)
        except StoryError:
            continue
        rc = 1
        print("Expected StoryError for invalid params but generation succeeded:", params)

    issues: list[str] = []
    for params in CURATED:
        sample = generate(params)
        issues.extend(f"{params.name}: {problem}" for problem in _story_checks(sample))
    if not issues:
        print(f"OK: curated stories passed shape and QA checks ({len(CURATED)} samples).")
    else:
        rc = 1
        print("QUALITY CHECK FAILURES:")
        for issue in issues:
            print(" ", issue)
    return rc


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed or 7
    samples: list[StorySample] = []
    for index, combo in enumerate(valid_combos(), start=1):
        gender = args.gender or ("girl" if index % 2 else "boy")
        params = StoryParams(
            office=combo[0],
            delivery=combo[1],
            ritual=combo[2],
            name=args.name or _pick_name(random.Random(base_seed + index), gender),
            gender=gender,
            trait=args.trait or TRAITS[(index - 1) % len(TRAITS)],
            seed=base_seed + index,
        )
        samples.append(generate(params))
    return samples


def main() -> int:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print("\t".join(combo))
        return 0

    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    try:
        if args.all:
            samples = _sample_all(args)
        else:
            samples = []
            seen: set[str] = set()
            i = 0
            while len(samples) < args.n and i < max(args.n * 100, 100):
                params = resolve_params(args, random.Random(base_seed + i), index=i)
                sample = generate(params)
                i += 1
                if sample.story in seen:
                    continue
                seen.add(sample.story)
                samples.append(sample)
            if len(samples) < args.n:
                raise StoryError("Could not generate enough unique stories with these constraints.")

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for idx, sample in enumerate(samples):
            header = ""
            if args.all:
                p = sample.params
                header = f"### office={p.office} delivery={p.delivery} ritual={p.ritual}"
            elif len(samples) > 1:
                header = f"### variant {idx + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if idx < len(samples) - 1:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as err:
        print(err)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
