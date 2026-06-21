#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ultra_handsome_lesson_learned_friendship_bedtime_story.py
=========================================================================================

A small bedtime-story storyworld about a child, a stubborn bedtime delay, and a
friendship lesson that ends warmly. The tale is built from a simulated world so
the prose changes with state rather than swapping nouns in a frozen paragraph.

Premise
-------
A child wants to stay up with a favorite plush friend and enjoy one more game.
A friend or sibling tries to help them settle down, but the child resists.
A gentle adult or helper shows a better bedtime routine, and the story ends with
a lesson learned and friendship strengthened.

This world intentionally includes the seed words "ultra" and "handsome" in
natural child-facing prose, and it keeps the tone soft, warm, and bedtime-like.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRIDGE_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    room: str
    child_name: str
    child_type: str
    friend_name: str
    friend_type: str
    adult_type: str
    bedtime_item: str
    bedtime_phrase: str
    delay_kind: str
    resolution_kind: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class RoomCfg:
    id: str
    label: str
    cozy_detail: str
    dark_detail: str
    bedtime_sound: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class BedtimeItem:
    id: str
    label: str
    phrase: str
    need: str
    temptation: str
    safe_use: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Delay:
    id: str
    worry: str
    resistance: str
    closeness: str
    tired_bonus: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Resolution:
    id: str
    text: str
    lesson: str
    bedtime_finish: str
    power: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self, room: RoomCfg) -> None:
        self.room = room
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
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_tired(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["sleepy"] >= THRESHOLD:
            sig = ("tired", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["fuss"] += 1
            out.append("__tired__")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    friend = world.entities.get("friend")
    if not child or not friend:
        return out
    if child.memes["trust"] >= THRESHOLD and friend.memes["kindness"] >= THRESHOLD:
        sig = ("friendship",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["warmth"] += 1
            friend.memes["warmth"] += 1
            out.append("__friendship__")
    return out


CAUSAL_RULES = [Rule("tired", _r_tired), Rule("friendship", _r_friendship)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def reasonableness_gate(room: RoomCfg, item: BedtimeItem, delay: Delay) -> bool:
    return bool(room.dark_detail and item.need == "sleep" and delay.tired_bonus >= 0)


def predict_bedtime(world: World, item: BedtimeItem, delay: Delay) -> dict:
    sim = world.copy()
    simulate_conflict(sim, sim.get("child"), sim.get("friend"), item, delay, narrate=False)
    return {
        "sleepy": sim.get("child").meters["sleepy"] >= THRESHOLD,
        "warmth": sim.get("child").memes["warmth"],
        "fuss": sim.get("child").memes["fuss"],
    }


def bedtime_setup(world: World, child: Entity, friend: Entity, room: RoomCfg, item: BedtimeItem) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"At the end of a soft, quiet evening, {child.id} and {friend.id} were in "
        f"{room.label}. {room.cozy_detail}"
    )
    world.say(
        f"The room was full of sleepy hushes, and {room.bedtime_sound}."
    )
    world.say(
        f"{child.id} held up {item.phrase} and said it was an "
        f"ultra handsome little treasure for one more game."
    )


def bedtime_need(world: World, child: Entity, friend: Entity, item: BedtimeItem, delay: Delay) -> None:
    world.say(
        f"But {room_name(world)} felt darker by the minute, and {delay.worry}."
    )
    world.say(
        f"{friend.id} rubbed {friend.pronoun('possessive')} eyes and whispered, "
        f'"It is time for {item.need}."'
    )


def room_name(world: World) -> str:
    return world.room.label


def tempt(world: World, child: Entity, item: BedtimeItem) -> None:
    child.memes["want_more"] += 1
    world.say(
        f'"Just one more turn," {child.id} said, hugging {item.id} close. '
        f"{item.temptation}"
    )


def warn(world: World, friend: Entity, child: Entity, item: BedtimeItem, delay: Delay) -> None:
    pred = predict_bedtime(world, item, delay)
    friend.memes["care"] += 1
    world.facts["predicted_fuss"] = pred["fuss"]
    world.say(
        f'{friend.id} bit {friend.pronoun("possessive")} lip and said, '
        f'"If you stay up too long, your eyes will feel heavy and your body will '
        f"want to droop into the pillow."'
    )


def resist(world: World, child: Entity, friend: Entity, delay: Delay) -> None:
    child.memes["stubborn"] += 1
    world.say(
        f"{child.id} crossed {child.pronoun('possessive')} arms, not ready to stop."
    )
    world.say(
        f"But even while {child.id} frowned, {delay.resistance}"
    )


def bridge(world: World, child: Entity, friend: Entity, adult: Entity, item: BedtimeItem, delay: Delay) -> None:
    child.meters["sleepy"] += delay.tired_bonus
    propagate(world, narrate=False)
    world.say(
        f"Then {adult.label_word} came in with a gentle smile and said, "
        f'"We can keep the friendship, and we can still make bedtime kind."'
    )
    world.say(
        f"{adult.label_word.capitalize()} tucked the {item.label} onto the shelf, "
        f"dimmed the lamp, and suggested a tiny bedtime promise."
    )


def resolve(world: World, child: Entity, friend: Entity, adult: Entity, item: BedtimeItem, res: Resolution) -> None:
    child.memes["warmth"] += 1
    friend.memes["warmth"] += 1
    child.memes["lesson"] += 1
    child.meters["sleepy"] = max(child.meters["sleepy"], 1.0)
    world.say(res.text)
    world.say(
        f"{adult.label_word.capitalize()} smiled and {res.lesson}."
    )
    world.say(
        f"At last, {res.bedtime_finish}. {child.id} and {friend.id} drifted toward sleep, "
        f"still friends, with the room calm and blue."
    )


def simulate_conflict(world: World, child: Entity, friend: Entity, item: BedtimeItem, delay: Delay, narrate: bool = True) -> None:
    child.meters["sleepy"] += 1
    if child.meters["sleepy"] >= THRESHOLD:
        propagate(world, narrate=narrate)


ROOMS = {
    "nursery": RoomCfg(id="nursery", label="the nursery", cozy_detail="A small lamp glowed like a moon, and a blanket nest waited by the bed.", dark_detail="the corners were full of velvet shadows", bedtime_sound="the clock made tiny ticking sounds", tags={"bedtime"}),
    "attic_room": RoomCfg(id="attic_room", label="the attic room", cozy_detail="A quilt was folded neatly, and the window held a silver star.", dark_detail="the slanted ceiling made the shadows gather", bedtime_sound="the floorboards sighed softly", tags={"bedtime"}),
    "shared_room": RoomCfg(id="shared_room", label="the shared bedroom", cozy_detail="Two pillows sat side by side, and a teddy bear watched over the bed.", dark_detail="the curtain made the window look deep and dark", bedtime_sound="the fan hummed low and slow", tags={"bedtime"}),
}

ITEMS = {
    "book": BedtimeItem(id="book", label="picture book", phrase="an ultra handsome picture book", need="sleep", temptation="Its shiny cover seemed to promise one more page.", safe_use="close it and save it for tomorrow", tags={"book", "bedtime"}),
    "bear": BedtimeItem(id="bear", label="stuffed bear", phrase="an ultra handsome stuffed bear", need="sleep", temptation="Its soft fur made staying awake feel cozy.", safe_use="put it on the pillow and hug it tight", tags={"toy", "bedtime"}),
    "lantern": BedtimeItem(id="lantern", label="night-light lantern", phrase="a little night-light lantern", need="sleep", temptation="It glowed so pretty that the child wanted to watch it forever.", safe_use="set it on low and listen to the hum", tags={"light", "bedtime"}),
}

DELAYS = {
    "drowsy": Delay(id="drowsy", worry="the child was getting drowsy", resistance="the yawns kept getting bigger", closeness="right beside the pillow", tired_bonus=1, tags={"sleep"}),
    "fidgety": Delay(id="fidgety", worry="the child was still fidgety and full of one-last-game energy", resistance="the feet kept tapping under the blanket", closeness="near the blanket nest", tired_bonus=0, tags={"sleep"}),
    "very_drowsy": Delay(id="very_drowsy", worry="the night had grown very late and sleep was tugging hard", resistance="the eyelids were already blinking slow", closeness="almost in dreamland", tired_bonus=2, tags={"sleep"}),
}

RESOLUTIONS = {
    "story": Resolution(id="story", text="So they chose one last bedtime story, read in a whisper with the lamp turned low.", lesson="explained that friends can help each other choose the gentle thing", bedtime_finish="the book was closed, the blanket was tucked, and the little lamp glowed softly"),
    "song": Resolution(id="song", text="So they sang one quiet song together, soft as feathers, until the room felt sleepy.", lesson="reminded them that a good friend helps make the night calm", bedtime_finish="the song ended with a yawn, and the pillow looked extra inviting"),
    "sip": Resolution(id="sip", text="So they took two tiny sips of water, shared a smile, and brushed their teeth with slow, careful hands.", lesson="said that bedtime can feel easier when everyone helps", bedtime_finish="the toothbrush cup sat neatly by the sink, and the hall light was already dim"),
}

CHILD_NAMES = ["Mia", "Noah", "Lila", "Eli", "Nora", "Theo", "Ava", "Ben"]
FRIEND_NAMES = ["Pip", "Milo", "Tess", "Zuri", "Jun", "Skye", "Kit", "Ollie"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for item in ITEMS:
            for delay in DELAYS:
                if reasonableness_gate(ROOMS[room], ITEMS[item], DELAYS[delay]):
                    combos.append((room, item, delay))
    return combos


def explain_rejection(room: RoomCfg, item: BedtimeItem, delay: Delay) -> str:
    return f"(No story: this bedtime scene is too thin or mismatched to make a gentle lesson.)"


def explain_bad_pick(name: str) -> str:
    return f"(No story: unknown choice {name!r}.)"


ASP_RULES = r"""
valid(R,I,D) :- room(R), item(I), delay(D), bedtime_scene(R,I,D).
bedtime_scene(R,I,D) :- cozy(R), needs_sleep(I), delay_ok(D).
friendship(C,F) :- child(C), friend(F), trust(C), kindness(F), trust(C) >= 1, kindness(F) >= 1.
lesson(C) :- friendship(C,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, r in ROOMS.items():
        lines.append(asp.fact("room", rid))
        lines.append(asp.fact("cozy", rid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("needs_sleep", iid))
    for did in DELAYS:
        lines.append(asp.fact("delay", did))
        lines.append(asp.fact("delay_ok", did))
    for cname in CHILD_NAMES:
        lines.append(asp.fact("child", cname))
        lines.append(asp.fact("trust", cname))
    for fname in FRIEND_NAMES:
        lines.append(asp.fact("friend", fname))
        lines.append(asp.fact("kindness", fname))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP valid combos differ from Python.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(room=None, child_name=None, child_type=None, friend_name=None, friend_type=None, adult_type=None, bedtime_item=None, bedtime_phrase=None, delay_kind=None, resolution_kind=None, seed=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, qa=True, trace=True)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    if rc == 0:
        print("OK: ASP parity and story smoke test passed.")
    return rc


@dataclass
class GeneratedChoice:
    room: str
    item: str
    delay: str
    resolution: str
    child_name: str
    child_type: str
    friend_name: str
    friend_type: str
    adult_type: str
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime storyworld about friendship and a learned lesson.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--adult-type", choices=["mother", "father"])
    ap.add_argument("--bedtime-item", choices=ITEMS)
    ap.add_argument("--bedtime-phrase")
    ap.add_argument("--delay-kind", choices=DELAYS)
    ap.add_argument("--resolution-kind", choices=RESOLUTIONS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = args.room or rng.choice(list(ROOMS))
    item = args.bedtime_item or rng.choice(list(ITEMS))
    delay = args.delay_kind or rng.choice(list(DELAYS))
    resolution = args.resolution_kind or rng.choice(list(RESOLUTIONS))
    if room not in ROOMS or item not in ITEMS or delay not in DELAYS or resolution not in RESOLUTIONS:
        raise StoryError(explain_bad_pick("invalid choice"))
    if not reasonableness_gate(ROOMS[room], ITEMS[item], DELAYS[delay]):
        raise StoryError(explain_rejection(ROOMS[room], ITEMS[item], DELAYS[delay]))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or rng.choice(["girl", "boy"])
    adult_type = args.adult_type or rng.choice(["mother", "father"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != child_name])
    bedtime_phrase = args.bedtime_phrase or ITEMS[item].phrase
    return StoryParams(room=room, child_name=child_name, child_type=child_type, friend_name=friend_name, friend_type=friend_type, adult_type=adult_type, bedtime_item=item, bedtime_phrase=bedtime_phrase, delay_kind=delay, resolution_kind=resolution)


def make_world(params: StoryParams) -> World:
    room = ROOMS[params.room]
    world = World(room)
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name, role="child"))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_type, label=params.friend_name, role="friend"))
    adult = world.add(Entity(id="adult", kind="character", type=params.adult_type, label=f"the {params.adult_type}", role="adult"))
    item = world.add(Entity(id="item", kind="thing", type="thing", label=ITEMS[params.bedtime_item].label, attrs={"phrase": params.bedtime_phrase}))
    child.memes["trust"] = 1.0
    friend.memes["kindness"] = 1.0
    child.meters["sleepy"] = 0.0
    world.facts.update(params=params, room=room, item=item, child=child, friend=friend, adult=adult, delay=DELAYS[params.delay_kind], resolution=RESOLUTIONS[params.resolution_kind])
    return world


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(explain_bad_pick(params.room))
    if params.bedtime_item not in ITEMS:
        raise StoryError(explain_bad_pick(params.bedtime_item))
    if params.delay_kind not in DELAYS:
        raise StoryError(explain_bad_pick(params.delay_kind))
    if params.resolution_kind not in RESOLUTIONS:
        raise StoryError(explain_bad_pick(params.resolution_kind))
    world = make_world(params)
    child = world.get("child")
    friend = world.get("friend")
    adult = world.get("adult")
    item = ITEMS[params.bedtime_item]
    delay = DELAYS[params.delay_kind]
    res = RESOLUTIONS[params.resolution_kind]
    bedtime_setup(world, child, friend, world.room, item)
    world.para()
    bedtime_need(world, child, friend, item, delay)
    tempt(world, child, item)
    warn(world, friend, child, item, delay)
    resist(world, child, friend, delay)
    bridge(world, child, friend, adult, item, delay)
    world.para()
    resolve(world, child, friend, adult, item, res)
    world.facts.update(outcome="lesson", item=item, delay=delay, resolution=res)
    prompts = [
        f'Write a bedtime story about friendship that includes the words "ultra" and "handsome".',
        f"Tell a gentle bedtime story where {params.child_name} learns a lesson from a friend and a grown-up helps make the night calm.",
        f"Write a small bedtime story with a warm ending, a friendship problem, and a lesson learned.",
    ]
    story_qa = [
        QAItem(question=f"Why did {params.child_name} resist going to sleep?", answer=f"{params.child_name} wanted one more happy moment with {params.friend_name} and {item.label}, so {params.child_name} was not ready to stop yet. {params.friend_name} could see the child was getting sleepy, but bedtime still felt like losing the game for a moment."),
        QAItem(question="How did the grown-up help?", answer=f"The grown-up used a gentle voice, dimmed the light, and guided everyone into a calmer bedtime routine. That helped the child keep the friendship and also learn that bedtime can be kind and safe."),
        QAItem(question="What was learned by the end?", answer=f"The child learned that a good friend can help make the night easier instead of harder. The story ends with rest, which proves the lesson changed the evening."),
    ]
    world_qa = [
        QAItem(question="What does sleepy mean?", answer="Sleepy means a body is ready to rest and the eyes want to close. At bedtime, sleepy feelings are a clue that it is time to slow down."),
        QAItem(question="What is friendship?", answer="Friendship is when people care about each other, help each other, and stay kind. A friend can make a hard moment feel softer."),
        QAItem(question="Why are bedtime routines helpful?", answer="Bedtime routines help because the same calm steps tell the body that sleep is coming. They can make it easier to settle down and feel safe."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("TRACE")
        for e in sample.world.entities.values():
            print(e.id, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print("== Q&A ==")
        for item in sample.story_qa + sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}\n")


CURATED = [
    StoryParams(room="nursery", child_name="Mia", child_type="girl", friend_name="Pip", friend_type="boy", adult_type="mother", bedtime_item="book", bedtime_phrase=ITEMS["book"].phrase, delay_kind="drowsy", resolution_kind="story"),
    StoryParams(room="shared_room", child_name="Noah", child_type="boy", friend_name="Tess", friend_type="girl", adult_type="father", bedtime_item="bear", bedtime_phrase=ITEMS["bear"].phrase, delay_kind="fidgety", resolution_kind="song"),
    StoryParams(room="attic_room", child_name="Lila", child_type="girl", friend_name="Ollie", friend_type="boy", adult_type="mother", bedtime_item="lantern", bedtime_phrase=ITEMS["lantern"].phrase, delay_kind="very_drowsy", resolution_kind="sip"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a}" for a in asp_valid_combos()))
        return
    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(seed + i))
            params.seed = seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
