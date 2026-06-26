#!/usr/bin/env python3
"""
storyworlds/worlds/packet_flashback_conflict_detective_story.py
===============================================================

A small detective-story world built around a packet, a flashback, and a conflict.

Premise:
- A young detective sees a packet that does not seem to belong where it is.
- The packet triggers a flashback to an earlier argument about where it should go.
- The detective uses clues, asks one careful question, and resolves the conflict.

The simulation tracks:
- physical meters: packet location, seal state, dampness, clue strength
- emotional memes: curiosity, worry, conflict, relief, trust

The prose is not a frozen template. It is driven by the world state:
- what the packet is
- where it was found
- whether it is sealed or damaged
- whether the flashback reveals an earlier disagreement
- how the detective solves the case
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    sender: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    helper: object | None = None
    packet: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str = "the front porch"
    indoors: bool = False
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class PacketSpec:
    label: str
    phrase: str
    contents: str
    sender: str
    destination: str
    can_be_wet: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    place: str
    packet: str
    hero_name: str
    hero_gender: str
    helper_name: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.flashback_seen = False
        self.fired: set[tuple] = set()

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


def packet_is_out_of_place(packet: Entity, setting: Setting) -> bool:
    return packet.meters.get("location_wrong", 0.0) >= THRESHOLD and setting.place == "the front porch"


def packet_is_damaged(packet: Entity) -> bool:
    return packet.meters.get("wet", 0.0) >= THRESHOLD or packet.meters.get("creased", 0.0) >= THRESHOLD


def flashback_triggers(world: World, detective: Entity, packet: Entity) -> bool:
    return detective.memes.get("curiosity", 0.0) >= THRESHOLD and packet_is_out_of_place(packet, world.setting)


def raise_conflict(world: World, detective: Entity, helper: Entity, packet: Entity) -> None:
    detective.memes["conflict"] += 1
    helper.memes["conflict"] += 1
    packet.meters["handled_in_rush"] += 1
    world.facts["conflict"] = True


def settle_conflict(world: World, detective: Entity, helper: Entity, packet: Entity) -> None:
    detective.memes["conflict"] = 0
    helper.memes["conflict"] = 0
    detective.memes["relief"] += 1
    helper.memes["trust"] += 1
    packet.meters["location_right"] += 1
    world.facts["conflict"] = False


def establish_case(world: World, detective: Entity, helper: Entity, packet: Entity) -> None:
    detective.memes["curiosity"] += 1
    packet.meters["location_wrong"] += 1
    packet.meters["clue_visible"] += 1
    world.say(
        f"{detective.id} was a little detective who noticed every odd thing on {world.setting.place}."
    )
    world.say(
        f"One morning, {detective.id} saw {packet.phrase} lying where it did not seem to belong."
    )
    world.say(
        f"{detective.id} wanted to solve the case, but {helper.id} was already looking worried."
    )


def flashback_scene(world: World, detective: Entity, helper: Entity, packet: Entity) -> None:
    world.flashback_seen = True
    detective.memes["worry"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"The sight of the packet pulled {detective.id} into a flashback."
    )
    world.say(
        f"Yesterday, {helper.id} had said the packet should stay dry and wait for the right person."
    )
    world.say(
        f"But the wind had blown it near the step, and both of them had argued about what to do next."
    )


def clue_work(world: World, detective: Entity, helper: Entity, packet: Entity) -> None:
    packet.meters["clue_strength"] += 1
    detective.memes["curiosity"] += 1
    if packet_is_damaged(packet):
        detective.memes["worry"] += 1
    world.say(
        f"{detective.id} knelt down and checked the packet carefully."
    )
    if packet.meters.get("wet", 0.0) >= THRESHOLD:
        world.say(
            f"The corner was damp, so {detective.id} knew someone had been in a hurry."
        )
    else:
        world.say(
            f"The seal was still neat, which meant the packet had not been opened."
        )
    world.say(
        f"A small label on the front gave the real clue: it was meant for {packet.sender}, not for the doorstep."
    )


def resolve_case(world: World, detective: Entity, helper: Entity, packet: Entity) -> None:
    settle_conflict(world, detective, helper, packet)
    detective.memes["trust"] += 1
    world.say(
        f"{detective.id} showed {helper.id} the label and explained the mix-up."
    )
    world.say(
        f"Together they moved {packet.it()} to the right place, and the argument melted away."
    )
    if packet.meters.get("wet", 0.0) >= THRESHOLD:
        world.say(
            f"By the end, the packet was under shelter again, safe and dry."
        )
    else:
        world.say(
            f"By the end, the packet sat in the right spot, neat and ready for its journey."
        )


SETTING_REGISTRY = {
    "porch": Setting(place="the front porch", indoors=False),
    "hall": Setting(place="the hallway", indoors=True),
    "gate": Setting(place="the garden gate", indoors=False),
}

PACKETS = {
    "letter": PacketSpec(
        label="packet",
        phrase="a small paper packet with a blue stamp",
        contents="a folded note",
        sender="Grandma",
        destination="the kitchen table",
        can_be_wet=True,
    ),
    "parcel": PacketSpec(
        label="packet",
        phrase="a brown packet tied with string",
        contents="a tiny gift",
        sender="Uncle Ben",
        destination="the mailbox shelf",
        can_be_wet=True,
    ),
    "envelope": PacketSpec(
        label="packet",
        phrase="a stiff packet with a bright sticker",
        contents="a clue card",
        sender="Aunt Rose",
        destination="the study desk",
        can_be_wet=False,
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Lily", "Ava", "Zoe"]
BOY_NAMES = ["Theo", "Finn", "Max", "Eli", "Noah"]


@dataclass
class StoryWorld:
    pass
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def build_world(params: StoryParams) -> World:
    setting = SETTING_REGISTRY[params.place]
    world = World(setting)

    packet_spec = _safe_lookup(PACKETS, params.packet)
    hero_type = "girl" if params.hero_gender == "girl" else "boy"
    helper_type = "mother"

    detective = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=hero_type,
        label="detective",
        meters={"location_right": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "conflict": 0.0, "relief": 0.0, "trust": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=helper_type,
        label="helper",
        meters={},
        memes={"worry": 0.0, "conflict": 0.0, "trust": 0.0},
    ))
    packet = world.add(Entity(
        id="packet",
        kind="thing",
        type="packet",
        label="packet",
        phrase=packet_spec.phrase,
        owner=packet_spec.destination,
        sender=packet_spec.sender,
        meters={"location_wrong": 0.0, "location_right": 0.0, "clue_visible": 0.0, "wet": 0.0, "creased": 0.0},
    ))

    # Setup
    establish_case(world, detective, helper, packet)

    # Conflict and flashback
    if flashback_triggers(world, detective, packet):
        world.para()
        flashback_scene(world, detective, helper, packet)
        raise_conflict(world, detective, helper, packet)

    # Mid-story clue work
    world.para()
    clue_work(world, detective, helper, packet)

    # A small physical twist for the conflict
    if not setting.indoors and packet_spec.can_be_wet:
        packet.meters["wet"] += 1
        world.say(
            f"A bit of mist touched the packet, and that made the case feel more urgent."
        )

    # Resolution
    world.para()
    resolve_case(world, detective, helper, packet)

    world.facts.update(
        detective=detective,
        helper=helper,
        packet=packet,
        packet_spec=packet_spec,
    )
    return world


def story_for_world(world: World) -> str:
    return world.render()


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    detective: Entity = _safe_fact(world, f, "detective")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, f, "helper")  # type: ignore[assignment]
    packet: Entity = _safe_fact(world, f, "packet")  # type: ignore[assignment]
    spec: PacketSpec = _safe_fact(world, f, "packet_spec")  # type: ignore[assignment]
    return [
        f"Write a child-friendly detective story about {detective.id}, a little detective, who finds a packet and solves a mix-up.",
        f"Tell a short mystery story where {helper.id} and {detective.id} disagree about a packet, then remember the earlier mistake and fix it.",
        f"Write a gentle detective tale about {packet.phrase} and how the right clue ends the conflict.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = _safe_fact(world, f, "detective")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, f, "helper")  # type: ignore[assignment]
    packet: Entity = _safe_fact(world, f, "packet")  # type: ignore[assignment]
    spec: PacketSpec = _safe_fact(world, f, "packet_spec")  # type: ignore[assignment]
    place = world.setting.place
    out = [
        QAItem(
            question=f"What did {detective.id} notice on {place}?",
            answer=f"{detective.id} noticed {packet.phrase} lying where it did not seem to belong.",
        ),
        QAItem(
            question=f"Why did the story pause for a flashback?",
            answer=(
                f"The packet reminded {detective.id} of an earlier argument, so the story flashed back to when "
                f"{helper.id} said it should stay dry and wait for the right person."
            ),
        ),
        QAItem(
            question=f"What clue helped {detective.id} solve the case?",
            answer=(
                f"The label on the front showed that the packet was meant for {spec.sender}, not for the doorstep."
            ),
        ),
        QAItem(
            question=f"How did the conflict end?",
            answer=(
                f"{detective.id} and {helper.id} moved the packet to the right place, and their worry turned into relief."
            ),
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a packet?",
            answer="A packet is a small bundle or parcel that holds something inside and can be carried from place to place.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly goes back to something that happened earlier.",
        ),
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a problem or disagreement that makes characters worry until they find a solution.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.phrase:
            parts.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    lines.append(f"  flashback_seen={world.flashback_seen}")
    return "\n".join(lines)


ASP_RULES = r"""
packet_out_of_place(P) :- packet(P), wrong_place(P).
flashback(D, P) :- detective(D), packet(P), packet_out_of_place(P), curious(D).
conflict(D, H) :- flashback(D, P), helper(H), argue_about(P).
resolved(D, P) :- detective(D), packet(P), clue_visible(P), label_shows_destination(P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for pid, spec in PACKETS.items():
        lines.append(asp.fact("packet", pid))
        lines.append(asp.fact("packet_label", pid, spec.label))
        lines.append(asp.fact("packet_sender", pid, spec.sender))
        lines.append(asp.fact("packet_destination", pid, spec.destination))
        if spec.can_be_wet:
            lines.append(asp.fact("can_be_wet", pid))
    lines.append(asp.fact("wrong_place", "packet"))
    lines.append(asp.fact("curious", "detective"))
    lines.append(asp.fact("argue_about", "packet"))
    lines.append(asp.fact("label_shows_destination", "packet"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show flashback/2. #show conflict/2. #show resolved/2.")
    model = asp.one_model(program)
    flashbacks = set(asp.atoms(model, "flashback"))
    conflicts = set(asp.atoms(model, "conflict"))
    resolved = set(asp.atoms(model, "resolved"))
    ok = ("detective", "packet") in resolved and ("detective", "packet") in flashbacks and ("detective", "helper") in conflicts
    if ok:
        print("OK: ASP twin produces the expected flashback/conflict/resolution facts.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected facts.")
    print("flashbacks:", sorted(flashbacks))
    print("conflicts:", sorted(conflicts))
    print("resolved:", sorted(resolved))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective-story world about a packet, a flashback, and a conflict.")
    ap.add_argument("--place", choices=SETTING_REGISTRY.keys())
    ap.add_argument("--packet", choices=PACKETS.keys())
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTING_REGISTRY.keys()))
    packet = getattr(args, "packet", None) or rng.choice(list(PACKETS.keys()))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["Mom", "Dad", "Aunt", "Uncle"])
    return StoryParams(place=place, packet=packet, hero_name=name, hero_gender=gender, helper_name=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=story_for_world(world),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


CURATED = [
    StoryParams(place="porch", packet="letter", hero_name="Mina", hero_gender="girl", helper_name="Mom"),
    StoryParams(place="hall", packet="parcel", hero_name="Theo", hero_gender="boy", helper_name="Dad"),
    StoryParams(place="gate", packet="envelope", hero_name="Nora", hero_gender="girl", helper_name="Aunt"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show flashback/2. #show conflict/2. #show resolved/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show flashback/2. #show conflict/2. #show resolved/2."))
        print("flashback:", asp.atoms(model, "flashback"))
        print("conflict:", asp.atoms(model, "conflict"))
        print("resolved:", asp.atoms(model, "resolved"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.packet} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
