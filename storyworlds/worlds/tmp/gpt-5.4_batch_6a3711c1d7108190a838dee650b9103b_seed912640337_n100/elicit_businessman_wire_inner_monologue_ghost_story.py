#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/elicit_businessman_wire_inner_monologue_ghost_story.py
=================================================================================

A small ghost-story storyworld about a lone businessman, a trembling wire, and a
restless spirit trying to elicit help.

The world model is not a frozen template. A ghost can only signal through the
kind of wire that actually reaches the hidden object in a given old building.
The businessman's fear, curiosity, and kindness shift as the haunting unfolds.
A strong enough response can lay the ghost to rest; a weak or delayed one leaves
the room uneasy at dawn.

Run it
------
    python storyworlds/worlds/gpt-5.4/elicit_businessman_wire_inner_monologue_ghost_story.py
    python storyworlds/worlds/gpt-5.4/elicit_businessman_wire_inner_monologue_ghost_story.py --setting hotel --wire bell_wire --burden wage_envelope
    python storyworlds/worlds/gpt-5.4/elicit_businessman_wire_inner_monologue_ghost_story.py --wire bell_wire --burden safe_note
    python storyworlds/worlds/gpt-5.4/elicit_businessman_wire_inner_monologue_ghost_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/elicit_businessman_wire_inner_monologue_ghost_story.py --verify
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
        male = {"boy", "father", "dad", "man", "businessman", "porter", "clerk", "bookkeeper"}
        female = {"girl", "mother", "mom", "woman", "widow"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    desk: str
    dark_corner: str
    keeper: str
    keeper_type: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class WireKind:
    id: str
    label: str
    sound: str
    verb: str
    reaches: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Burden:
    id: str
    label: str
    phrase: str
    hidden_place: str
    clue_place: str
    owner: str
    owner_type: str
    debt: str
    peace_text: str
    sadness: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    act_text: str
    fail_text: str
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


def _r_wire_haunt(world: World) -> list[str]:
    out: list[str] = []
    wire = world.get("wire")
    ghost = world.get("ghost")
    man = world.get("businessman")
    room = world.get("room")
    if wire.meters["vibration"] >= THRESHOLD:
        sig = ("wire_haunt",)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["cold"] += 1
            ghost.meters["presence"] += 1
            man.memes["fear"] += 1
            man.memes["attention"] += 1
            out.append("__haunt__")
    return out


def _r_presence_press(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    man = world.get("businessman")
    if ghost.meters["presence"] >= THRESHOLD:
        sig = ("presence_press",)
        if sig not in world.fired:
            world.fired.add(sig)
            man.memes["curiosity"] += 1
            if ghost.meters["unrest"] >= THRESHOLD:
                man.memes["pity"] += 1
            out.append("__presence__")
    return out


def _r_return_peace(world: World) -> list[str]:
    out: list[str] = []
    burden = world.get("burden")
    ghost = world.get("ghost")
    room = world.get("room")
    man = world.get("businessman")
    if burden.meters["returned"] >= THRESHOLD and ghost.meters["unrest"] >= THRESHOLD:
        sig = ("return_peace",)
        if sig not in world.fired:
            world.fired.add(sig)
            ghost.meters["unrest"] = 0.0
            ghost.meters["presence"] = 0.0
            room.meters["cold"] = 0.0
            man.memes["relief"] += 1
            man.memes["kindness"] += 1
            out.append("__peace__")
    return out


CAUSAL_RULES = [
    Rule("wire_haunt", "physical", _r_wire_haunt),
    Rule("presence_press", "social", _r_presence_press),
    Rule("return_peace", "social", _r_return_peace),
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
        for s in produced:
            world.say(s)
    return produced


def valid_combo(setting: Setting, wire: WireKind, burden: Burden) -> bool:
    return burden.hidden_place in setting.supports and burden.hidden_place in wire.reaches


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def haunting_level(burden: Burden, delay: int) -> int:
    return burden.sadness + delay


def lays_to_rest(response: Response, burden: Burden, delay: int) -> bool:
    return response.power >= haunting_level(burden, delay)


def predict_lingering(world: World, response: Response, burden: Burden, delay: int) -> bool:
    sim = world.copy()
    sim.get("wire").meters["vibration"] += 1
    propagate(sim, narrate=False)
    if response.power < haunting_level(burden, delay):
        sim.get("ghost").meters["unrest"] += 1
    return sim.get("ghost").meters["unrest"] >= THRESHOLD


def opening_scene(world: World, setting: Setting, man: Entity) -> None:
    man.memes["duty"] += 1
    world.say(
        f"{man.id} was a traveling businessman who stopped for the night at {setting.place}. "
        f"{setting.opening}"
    )
    world.say(
        f"He sat alone at {setting.desk}, adding long columns by lamplight while the rest of the building slept."
    )


def first_sign(world: World, wire: WireKind) -> None:
    world.get("wire").meters["vibration"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the {wire.label} gave {wire.sound}, a small sound that should not have come from an empty house."
    )


def inner_monologue(world: World, man: Entity, wire: WireKind, burden: Burden, delay: int) -> None:
    lingering = predict_lingering(world, RESPONSES["follow_and_return"], burden, delay)
    thought1 = (
        f'"No wind should make a {wire.label} {wire.verb}," {man.id} thought. '
        f'"If someone wants to elicit my notice, why not simply speak?"'
    )
    world.say(thought1)
    if lingering:
        world.say(
            f'He listened again, and a colder thought came after it: '
            f'"If I pretend not to hear, this poor trouble may stay awake all night with me."'
        )
    else:
        world.say(
            f'He drew one slow breath and thought, '
            f'"There is fear in this house, but perhaps there is also a reason."'
        )


def second_sign(world: World, setting: Setting, wire: WireKind, burden: Burden) -> None:
    ghost = world.get("ghost")
    ghost.meters["unrest"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The {wire.label} trembled again and pointed his eyes toward {burden.clue_place}, near {setting.dark_corner}."
    )
    world.say(
        "A pale shine stood there only for a heartbeat, like a person remembered badly by the dark."
    )


def search(world: World, man: Entity, burden: Burden) -> None:
    man.memes["resolve"] += 1
    burden_ent = world.get("burden")
    burden_ent.meters["found"] += 1
    world.say(
        f"With a hand that would not keep still, {man.id} followed the hint and found {burden.phrase} hidden in {burden.hidden_place}."
    )
    world.say(
        f'Inside was proof that it belonged to {burden.owner}. "{burden.debt}," he whispered.'
    )


def respond_success(world: World, man: Entity, setting: Setting, burden: Burden, response: Response) -> None:
    world.get("burden").meters["returned"] += 1
    propagate(world, narrate=False)
    body = response.act_text.format(owner=burden.owner, keeper=setting.keeper, item=burden.label)
    world.say(f"{man.id} {body}.")
    world.say(
        f'At once he felt the room change. "{burden.peace_text}," he thought, though no lips had moved.'
    )
    world.say(
        "The cold lifted from the floorboards, and the last faint shimmer by the wall looked less lonely than before."
    )


def respond_failure(world: World, man: Entity, setting: Setting, burden: Burden, response: Response) -> None:
    ghost = world.get("ghost")
    ghost.meters["presence"] += 1
    ghost.meters["unrest"] += 1
    man.memes["fear"] += 1
    body = response.fail_text.format(owner=burden.owner, keeper=setting.keeper, item=burden.label)
    world.say(f"{man.id} {body}.")
    world.say(
        "But the room only grew colder. The unseen presence stayed near the ceiling, patient and sad, as if the right deed had not yet been done."
    )
    world.say(
        f'With dawn still far away, he thought, "I have not helped at all. I have only heard the sorrow more clearly."'
    )


def dawn_rest(world: World, setting: Setting, man: Entity, burden: Burden) -> None:
    man.memes["wonder"] += 1
    world.say(
        f"At dawn he gave the matter to {setting.keeper}, who promised that {burden.owner} would have what was owed."
    )
    world.say(
        f"Outside, the morning was gray and ordinary again, but {man.id} walked into it gentler than when he had entered."
    )


def dawn_lingering(world: World, setting: Setting, man: Entity, burden: Burden) -> None:
    world.say(
        f"When dawn finally thinned the windows, {man.id} still carried {burden.label} in both hands, unsure how to make the night right."
    )
    world.say(
        f"He left it with {setting.keeper} at last, but the memory of the shivering wire stayed with him, and sometimes in lonely offices he still looked up when metal sang."
    )


SETTINGS = {
    "hotel": Setting(
        "hotel",
        "an old hotel at the edge of town",
        "The front hall smelled of wax, coal dust, and old rain.",
        "the narrow check-in desk",
        "the stairs that led to the shuttered upper floor",
        "the innkeeper",
        "man",
        supports={"desk_drawer", "attic_box"},
        tags={"hotel", "night"},
    ),
    "station": Setting(
        "station",
        "a little railway station where no train stopped after dark",
        "The waiting room clock clicked too loudly, and every bench looked as if it were listening.",
        "the station clerk's table",
        "the locked parcel room",
        "the station master",
        "man",
        supports={"parcel_locker", "telegraph_shelf"},
        tags={"station", "night"},
    ),
    "counting_house": Setting(
        "counting_house",
        "an old counting house with tall ledgers and taller shadows",
        "Ink, dust, and cedar filled the still air.",
        "the bookkeeper's high desk",
        "the iron safe by the back wall",
        "the watchman",
        "man",
        supports={"iron_safe", "ledger_shelf"},
        tags={"office", "night"},
    ),
}

WIRES = {
    "bell_wire": WireKind(
        "bell_wire",
        "bell wire",
        "one thin silver shiver",
        "quiver without a hand",
        reaches={"desk_drawer", "attic_box"},
        tags={"wire", "bell"},
    ),
    "telegraph_wire": WireKind(
        "telegraph_wire",
        "telegraph wire",
        "a long, lonely hum",
        "sing after midnight",
        reaches={"parcel_locker", "telegraph_shelf"},
        tags={"wire", "telegraph"},
    ),
    "pull_wire": WireKind(
        "pull_wire",
        "service wire",
        "three quick little twangs",
        "jump on its own",
        reaches={"iron_safe", "ledger_shelf"},
        tags={"wire"},
    ),
}

BURDENS = {
    "wage_envelope": Burden(
        "wage_envelope",
        "the wage envelope",
        "a yellow wage envelope tied with faded blue string",
        "desk_drawer",
        "the old brass bell",
        "the widow of the night porter",
        "widow",
        "The wages had never been delivered.",
        "The debt was ending at last",
        2,
        tags={"debt", "letter"},
    ),
    "music_key": Burden(
        "music_key",
        "the brass key",
        "a brass key wrapped in a child's handkerchief",
        "attic_box",
        "the shadowed stair rail",
        "the bellman's daughter",
        "girl",
        "It opened a music box promised long ago.",
        "A promise could finally be kept",
        2,
        tags={"key", "promise"},
    ),
    "parcel_receipt": Burden(
        "parcel_receipt",
        "the parcel receipt",
        "a folded parcel receipt under a crust of dust",
        "parcel_locker",
        "the barred parcel window",
        "the old porter's son",
        "boy",
        "A winter coat had been waiting there for years.",
        "Someone forgotten would be forgotten no longer",
        3,
        tags={"receipt", "family"},
    ),
    "lost_contract": Burden(
        "lost_contract",
        "the signed contract",
        "a signed contract tucked behind a telegraph ledger",
        "telegraph_shelf",
        "the dead telegraph key",
        "the station clerk's sister",
        "woman",
        "Its payment had been meant for her schooling.",
        "The withheld kindness was being released",
        2,
        tags={"paper", "school"},
    ),
    "safe_note": Burden(
        "safe_note",
        "the sealed note",
        "a sealed note behind the iron cash box",
        "iron_safe",
        "the black iron handle",
        "the watchman's mother",
        "woman",
        "It held the apology he had meant to send.",
        "The unsent words had found their road",
        3,
        tags={"note", "apology"},
    ),
    "charity_ledger": Burden(
        "charity_ledger",
        "the charity ledger",
        "a thin charity ledger wedged behind the lowest shelf",
        "ledger_shelf",
        "the row of silent account books",
        "the orphan house on Mill Lane",
        "thing",
        "The promised coins had never been carried there.",
        "The good gift could move at last",
        2,
        tags={"ledger", "charity"},
    ),
}

RESPONSES = {
    "follow_and_return": Response(
        "follow_and_return",
        3,
        4,
        "carried {item} downstairs and wrote a careful note so {keeper} would send it to {owner} at first light",
        "hid {item} in his case instead of trusting the night, meaning to decide later",
        "followed the clue and arranged for the hidden item to be returned",
        tags={"return", "kindness"},
    ),
    "ask_then_return": Response(
        "ask_then_return",
        3,
        3,
        'spoke softly into the dark, then took {item} to {keeper} with a promise that it would reach {owner}',
        "stood talking bravely to the empty room, but waited too long before doing anything useful with the item",
        "asked who needed help, then returned the hidden item",
        tags={"return", "ghost"},
    ),
    "lock_it_away": Response(
        "lock_it_away",
        1,
        1,
        "locked {item} back where he had found it",
        "locked {item} away again, hoping the noise would stop",
        "locked the hidden item away again",
        tags={"fear"},
    ),
}

GIVEN_NAMES = ["Mr. Hale", "Mr. Finch", "Mr. Rowan", "Mr. Pike", "Mr. Vale", "Mr. Mercer"]
TRAITS = ["careful", "tired", "practical", "kind", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for wid, wire in WIRES.items():
            for bid, burden in BURDENS.items():
                if valid_combo(setting, wire, burden):
                    combos.append((sid, wid, bid))
    return combos


@dataclass
class StoryParams:
    setting: str
    wire: str
    burden: str
    response: str
    businessman: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "wire": [(
        "What is a wire?",
        "A wire is a thin piece of metal that can carry a pull, a ring, or a signal from one place to another."
    )],
    "bell": [(
        "What does a bell wire do?",
        "A bell wire lets a bell ring when someone pulls or moves the wire. In an old building, even a tiny shake can make it sound."
    )],
    "telegraph": [(
        "What was a telegraph wire used for?",
        "A telegraph wire carried messages over long distances. People used it before telephones were common."
    )],
    "ghost": [(
        "What is a ghost story?",
        "A ghost story is a spooky tale about someone from long ago whose presence is still felt. It is meant to feel mysterious, not just frightening."
    )],
    "debt": [(
        "Why is it important to return something that belongs to someone else?",
        "Returning what belongs to someone else is fair and kind. It can also fix an old hurt that has lasted too long."
    )],
    "apology": [(
        "Why can an apology matter so much?",
        "An apology can help heal a sad feeling when someone has been wronged. Honest words can bring peace even after a long time."
    )],
    "charity": [(
        "What is charity?",
        "Charity means giving help, money, or goods to people who need them. It is a way of sharing kindness."
    )],
}
KNOWLEDGE_ORDER = ["wire", "bell", "telegraph", "ghost", "debt", "apology", "charity"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    man = f["businessman"]
    setting = f["setting"]
    wire = f["wire_cfg"]
    burden = f["burden_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a gentle ghost story for a 3-to-5-year-old about a businessman in {setting.place} '
        f'who hears a {wire.label}. Use inner monologue and include the word "elicit".'
    )
    if outcome == "rest":
        return [
            base,
            f"Tell a ghost story where {man.id} follows a strange sound in the night, discovers {burden.label}, and helps a restless spirit find peace.",
            f"Write a spooky but kind story in which a lonely wire leads a businessman to make an old wrong right by morning.",
        ]
    return [
        base,
        f"Tell a ghost story where {man.id} hears a warning in the wire and finds {burden.label}, but his first choice is too weak to calm the sorrow in the room.",
        f"Write a quiet haunting story with inner thoughts, where a businessman understands the ghost's need but cannot fully set things right before dawn.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    man = f["businessman"]
    setting = f["setting"]
    wire = f["wire_cfg"]
    burden = f["burden_cfg"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {man.id}, a traveling businessman spending the night at {setting.place}. He is alone when the strange sound begins."
        ),
        (
            f"What first made {man.id} feel that something was wrong?",
            f"The {wire.label} made a sound even though no one should have been there to touch it. That small, impossible noise told him the building was not as empty as it seemed."
        ),
        (
            f"What did {man.id} think to himself when he heard the {wire.label}?",
            f"He wondered who or what was trying to elicit his notice. His inner thoughts show that he was frightened, but also curious enough to keep listening."
        ),
        (
            "What hidden thing did he find?",
            f"He found {burden.phrase}. Finding it showed that the haunting was tied to an old unfinished duty."
        ),
    ]
    if f["outcome"] == "rest":
        qa.append((
            "How did he help the ghost?",
            f"{man.id} {response.qa_text}. Because he acted with kindness instead of hiding from the problem, the cold room grew peaceful."
        ))
        qa.append((
            "How did the story end?",
            f"By dawn the ghost was quiet, and the old wrong was on its way to being mended. The ending feels calm because the businessman chose to help."
        ))
    else:
        qa.append((
            "Why did the ghost stay restless?",
            f"{man.id} found what was hidden, but his choice was not strong enough to finish the task. The spirit needed the right deed, not just brave words or a secret kept in the dark."
        ))
        qa.append((
            "How did the story end?",
            f"Dawn came, but the memory of the trembling wire stayed with him. The ending proves that the sorrow had been understood, though not fully healed."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["wire_cfg"].tags) | {"ghost"}
    burden = f["burden_cfg"]
    if "debt" in burden.tags or "receipt" in burden.tags or "paper" in burden.tags:
        tags.add("debt")
    if "apology" in burden.tags or "note" in burden.tags:
        tags.add("apology")
    if "charity" in burden.tags or "ledger" in burden.tags:
        tags.add("charity")
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


def tell(
    setting: Setting,
    wire: WireKind,
    burden: Burden,
    response: Response,
    businessman: str = "Mr. Hale",
    trait: str = "careful",
    delay: int = 0,
) -> World:
    world = World()
    man = world.add(Entity(id=businessman, kind="character", type="businessman", role="businessman", traits=[trait]))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", role="ghost"))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    wire_ent = world.add(Entity(id="wire", type="wire", label=wire.label))
    burden_ent = world.add(Entity(id="burden", type="thing", label=burden.label, attrs={"owner": burden.owner}))

    ghost.meters["unrest"] = float(burden.sadness + delay)
    man.memes["fear"] = 0.0
    man.memes["curiosity"] = 0.0
    man.memes["pity"] = 0.0

    opening_scene(world, setting, man)
    world.para()
    first_sign(world, wire)
    inner_monologue(world, man, wire, burden, delay)
    second_sign(world, setting, wire, burden)
    world.para()
    search(world, man, burden)

    outcome = "rest" if lays_to_rest(response, burden, delay) else "linger"
    world.para()
    if outcome == "rest":
        respond_success(world, man, setting, burden, response)
        dawn = dawn_rest
    else:
        respond_failure(world, man, setting, burden, response)
        dawn = dawn_lingering
    world.para()
    dawn(world, setting, man, burden)

    world.facts.update(
        businessman=man,
        setting=setting,
        wire_cfg=wire,
        burden_cfg=burden,
        response=response,
        outcome=outcome,
        delay=delay,
        haunting=haunting_level(burden, delay),
    )
    return world


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hotel", "bell_wire", "wage_envelope", "follow_and_return", "Mr. Hale", "careful", 0),
    StoryParams("station", "telegraph_wire", "parcel_receipt", "ask_then_return", "Mr. Finch", "steady", 0),
    StoryParams("counting_house", "pull_wire", "safe_note", "ask_then_return", "Mr. Rowan", "kind", 1),
    StoryParams("hotel", "bell_wire", "music_key", "ask_then_return", "Mr. Pike", "tired", 0),
    StoryParams("counting_house", "pull_wire", "safe_note", "ask_then_return", "Mr. Vale", "practical", 2),
]


def explain_rejection(setting: Setting, wire: WireKind, burden: Burden) -> str:
    if burden.hidden_place not in setting.supports:
        return (
            f"(No story: {setting.place} has no {burden.hidden_place}, so {burden.label} cannot be hidden there. "
            f"Choose a burden that fits the building.)"
        )
    if burden.hidden_place not in wire.reaches:
        return (
            f"(No story: the {wire.label} does not run near the hidden place for {burden.label}, "
            f"so the ghost would have no way to point the businessman there.)"
        )
    return "(No story: this haunting has no plausible path through the building.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "rest" if lays_to_rest(RESPONSES[params.response], BURDENS[params.burden], params.delay) else "linger"


ASP_RULES = r"""
supports_place(S, P) :- setting(S), supports(S, P).
reaches_place(W, P)  :- wire(W), reaches(W, P).
valid(S, W, B) :- setting(S), wire(W), burden(B),
                  hidden_place(B, P), supports_place(S, P), reaches_place(W, P).

sensible(R) :- response(R), sense(R, V), sense_min(M), V >= M.

haunting(H + D) :- chosen_burden(B), sadness(B, H), delay(D).
can_rest :- chosen_response(R), power(R, P), haunting(H), P >= H.
outcome(rest) :- can_rest.
outcome(linger) :- not can_rest.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for place in sorted(s.supports):
            lines.append(asp.fact("supports", sid, place))
    for wid, w in WIRES.items():
        lines.append(asp.fact("wire", wid))
        for place in sorted(w.reaches):
            lines.append(asp.fact("reaches", wid, place))
    for bid, b in BURDENS.items():
        lines.append(asp.fact("burden", bid))
        lines.append(asp.fact("hidden_place", bid, b.hidden_place))
        lines.append(asp.fact("sadness", bid, b.sadness))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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

    extra = "\n".join([
        asp.fact("chosen_burden", params.burden),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
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

    clingo_sens, python_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke generate/emit passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story world: a businessman hears a wire in the night and must decide how to answer the haunting."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--wire", choices=WIRES)
    ap.add_argument("--burden", choices=BURDENS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the sorrow has had to deepen before the clue is answered")
    ap.add_argument("--businessman")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.setting and args.wire and args.burden:
        s, w, b = SETTINGS[args.setting], WIRES[args.wire], BURDENS[args.burden]
        if not valid_combo(s, w, b):
            raise StoryError(explain_rejection(s, w, b))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.wire is None or c[1] == args.wire)
        and (args.burden is None or c[2] == args.burden)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, wire, burden = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    businessman = args.businessman or rng.choice(GIVEN_NAMES)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, wire, burden, response, businessman, trait, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        WIRES[params.wire],
        BURDENS[params.burden],
        RESPONSES[params.response],
        params.businessman,
        params.trait,
        params.delay,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, wire, burden) combos:\n")
        for setting, wire, burden in combos:
            print(f"  {setting:15} {wire:14} {burden}")
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
            header = f"### {p.businessman}: {p.setting}, {p.wire}, {p.burden} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
