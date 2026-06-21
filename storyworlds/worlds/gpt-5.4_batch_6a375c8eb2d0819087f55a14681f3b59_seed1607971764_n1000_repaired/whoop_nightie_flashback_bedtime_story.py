#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/whoop_nightie_flashback_bedtime_story.py
===================================================================

A standalone story world for soft bedtime stories about a child who hears a
night sound, grows worried in the dark, and then calms down by remembering an
earlier daytime lesson. The required flashback is part of the world model: a
matching memory helps explain the sound, so the ending proves the child changed
from frightened to settled.

Run it
------
    python storyworlds/worlds/gpt-5.4/whoop_nightie_flashback_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/whoop_nightie_flashback_bedtime_story.py --sound owl --memory owl_walk
    python storyworlds/worlds/gpt-5.4/whoop_nightie_flashback_bedtime_story.py --sound wind --memory owl_walk
    python storyworlds/worlds/gpt-5.4/whoop_nightie_flashback_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/whoop_nightie_flashback_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/whoop_nightie_flashback_bedtime_story.py --trace
    python storyworlds/worlds/gpt-5.4/whoop_nightie_flashback_bedtime_story.py --verify
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Sound:
    id: str
    label: str
    cry: str
    source_label: str
    source_type: str
    location: str
    mystery: int
    gentle: bool
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
class MemoryLesson:
    id: str
    matches: str
    place: str
    adult: str
    image: str
    line: str
    truth: str
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
class Comfort:
    id: str
    label: str
    phrase: str
    action: str
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
class Response:
    id: str
    sense: int
    needs_view: bool
    text: str
    follow: str
    qa_text: str
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


def _r_dark_unknown_fear(world: World) -> list[str]:
    child = world.get("child")
    room = world.get("room")
    sound = world.get("sound")
    if room.meters["dark"] < THRESHOLD:
        return []
    if sound.meters["mystery"] < THRESHOLD:
        return []
    sig = ("fear_from_dark_sound",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    return ["__fear__"]


def _r_memory_calms(world: World) -> list[str]:
    child = world.get("child")
    sound = world.get("sound")
    if child.memes["remembering"] < THRESHOLD:
        return []
    if sound.meters["recognized"] < THRESHOLD:
        return []
    sig = ("memory_calms",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    child.memes["calm"] += 1
    child.memes["courage"] += 1
    return ["__calm__"]


def _r_comfort_helps(world: World) -> list[str]:
    child = world.get("child")
    comfort = world.get("comfort")
    if child.memes["fear"] < THRESHOLD:
        return []
    if comfort.meters["held"] < THRESHOLD:
        return []
    sig = ("comfort_helps",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["calm"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 0.5)
    return ["__comfort__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="dark_unknown_fear", tag="emotional", apply=_r_dark_unknown_fear),
    Rule(name="memory_calms", tag="emotional", apply=_r_memory_calms),
    Rule(name="comfort_helps", tag="emotional", apply=_r_comfort_helps),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def memory_matches(sound: Sound, memory: MemoryLesson) -> bool:
    return sound.id == memory.matches


def response_fits(sound: Sound, response: Response) -> bool:
    if response.needs_view:
        return sound.source_type in {"animal", "weather", "branches"}
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid, sound in SOUNDS.items():
        for mid, memory in MEMORIES.items():
            if not memory_matches(sound, memory):
                continue
            for cid in COMFORTS:
                for rid, response in RESPONSES.items():
                    if response.sense >= SENSE_MIN and response_fits(sound, response):
                        combos.append((sid, mid, cid, rid))
    return combos


def explain_rejection(sound: Sound, memory: MemoryLesson) -> str:
    return (
        f"(No story: {memory.id} teaches about {memory.matches}, but the night sound is "
        f"{sound.id}. The flashback has to honestly explain the sound the child hears.)"
    )


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in RESPONSES.values() if r.sense >= SENSE_MIN))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_fear(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "fear": child.memes["fear"],
        "calm": child.memes["calm"],
    }


def bedtime_setup(world: World, child: Entity, parent: Entity, comfort: Comfort) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f"At bedtime, {child.id} padded into the little bedroom in a soft {child.attrs['nightwear']}. "
        f"{parent.label_word.capitalize()} tucked the blanket smooth and laid {comfort.phrase} beside the pillow."
    )
    world.say(
        f"The moon made a silver square on the floor, and the house grew quiet in the gentle way houses do when everyone is getting ready to sleep."
    )


def hear_sound(world: World, child: Entity, sound: Sound) -> None:
    room = world.get("room")
    sound_ent = world.get("sound")
    room.meters["dark"] = 1.0
    sound_ent.meters["mystery"] = float(sound.mystery)
    propagate(world, narrate=False)
    if sound.id == "owl":
        world.say(
            f"Then, from {sound.location}, there came a round little whoop, and then another. "
            f"In the dark, the sound seemed bigger than it really was."
        )
    else:
        world.say(
            f"Then a small sound came from {sound.location}: {sound.cry}. "
            f"In the dark, it felt strange enough to make {child.id} hold still."
        )
    if child.memes["fear"] >= THRESHOLD:
        world.say(
            f"{child.id} sat up and pulled the blanket close. \"What was that?\" {child.pronoun()} whispered."
        )


def parent_stays(world: World, child: Entity, parent: Entity, comfort: Comfort) -> None:
    comfort_ent = world.get("comfort")
    comfort_ent.meters["held"] = 1.0
    child.memes["trust"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} came to the bed at once, stroked {child.pronoun('possessive')} hair, and helped {child.pronoun('object')} hold {comfort.phrase}. "
        f"\"Let's listen carefully together,\" {parent.pronoun()} said."
    )


def trigger_flashback(world: World, child: Entity, parent: Entity, memory: MemoryLesson) -> None:
    child.memes["remembering"] = 1.0
    world.facts["flashback_used"] = True
    world.say(
        f"Then {child.id} remembered something from earlier. That afternoon at {memory.place}, "
        f"{memory.adult} had paused with {child.pronoun('object')} and said, \"{memory.line}\""
    )
    world.say(
        f"In the memory, {memory.image}. The remembered picture came back warm and bright, as if a little daytime window had opened inside the dark room."
    )


def identify_sound(world: World, child: Entity, parent: Entity, sound: Sound, memory: MemoryLesson, response: Response) -> None:
    sound_ent = world.get("sound")
    sound_ent.meters["recognized"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} {response.text} {response.follow}"
    )
    world.say(
        f"Now the sound belonged to something real: {memory.truth}"
    )


def settle(world: World, child: Entity, parent: Entity, comfort: Comfort, sound: Sound) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f"{child.id}'s shoulders softened. \"Oh,\" {child.pronoun()} said, and this time the sound did not feel like a mystery at all."
    )
    if sound.id == "owl":
        world.say(
            f"Another whoop drifted in from the dark, but now it sounded round and far away, like the night simply speaking its own quiet language."
        )
    else:
        world.say(
            f"The same sound came again, but now it seemed small and harmless, part of the night instead of a problem inside it."
        )
    world.say(
        f"Soon {child.id} curled under the blanket, {comfort.action}, and closed {child.pronoun('possessive')} eyes while {parent.label_word} sat nearby for one last peaceful minute."
    )


def tell(
    sound: Sound,
    memory: MemoryLesson,
    comfort: Comfort,
    response: Response,
    *,
    child_name: str = "Mina",
    child_type: str = "girl",
    parent_type: str = "mother",
    trait: str = "thoughtful",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        traits=[trait],
        attrs={"nightwear": "nightie"},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label="bedroom",
        meters=defaultdict(float, {"dark": 0.0}),
    ))
    comfort_ent = world.add(Entity(
        id="comfort",
        type="comfort",
        label=comfort.label,
        phrase=comfort.phrase,
        tags=set(comfort.tags),
        meters=defaultdict(float, {"held": 0.0}),
    ))
    sound_ent = world.add(Entity(
        id="sound",
        type="sound",
        label=sound.label,
        tags=set(sound.tags),
        attrs={"source_label": sound.source_label, "location": sound.location},
        meters=defaultdict(float, {"mystery": 0.0, "recognized": 0.0}),
    ))

    world.facts.update(
        sound=sound,
        memory=memory,
        comfort=comfort,
        response=response,
        child=child,
        parent=parent,
        flashback_used=False,
    )
    child.memes["fear"] = 0.0
    child.memes["calm"] = 0.0
    child.memes["courage"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["remembering"] = 0.0
    child.memes["sleepy"] = 0.0

    bedtime_setup(world, child, parent, comfort)
    world.para()
    hear_sound(world, child, sound)
    parent_stays(world, child, parent, comfort)
    world.para()
    trigger_flashback(world, child, parent, memory)
    identify_sound(world, child, parent, sound, memory, response)
    world.para()
    settle(world, child, parent, comfort, sound)

    world.facts.update(
        recognized=world.get("sound").meters["recognized"] >= THRESHOLD,
        calm=child.memes["calm"] >= THRESHOLD,
        final_fear=child.memes["fear"],
    )
    return world


KNOWLEDGE = {
    "owl": [
        (
            "Why do owls make a whoop sound at night?",
            "Owls call to each other in the dark so they can tell where they are. A whoop can sound mysterious, but it is usually just an owl being an owl."
        )
    ],
    "rain": [
        (
            "Why does rain sound louder at night?",
            "Night can feel quieter, so raindrops stand out more. When everything else settles down, small sounds are easier to notice."
        )
    ],
    "wind": [
        (
            "Why do branches tap or scrape in the wind?",
            "Wind pushes branches and leaves, and they can brush against each other or a window. That can make soft knocking sounds even when nothing is wrong."
        )
    ],
    "cat": [
        (
            "Why might a cat make sounds outside at night?",
            "Cats are often awake when people are getting sleepy. They may mew, rustle, or move around while exploring."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is when a story remembers something that happened earlier. It can help a character understand what is happening now."
        )
    ],
    "comfort": [
        (
            "Why can a favorite bedtime toy help when a child feels scared?",
            "Holding something familiar can make a child feel safer and calmer. It helps the body slow down while a grown-up stays close."
        )
    ],
    "night": [
        (
            "Why can ordinary sounds seem scary in the dark?",
            "In the dark, you cannot see right away what made the sound. When your mind does not know yet, the sound can feel bigger than it is."
        )
    ],
}
KNOWLEDGE_ORDER = ["flashback", "night", "owl", "rain", "wind", "cat", "comfort"]

SOUNDS = {
    "owl": Sound(
        id="owl",
        label="owl call",
        cry="whoop",
        source_label="an owl in the tree",
        source_type="animal",
        location="the garden tree beyond the window",
        mystery=2,
        gentle=True,
        tags={"owl", "night"},
    ),
    "rain": Sound(
        id="rain",
        label="rain on the window",
        cry="patter patter",
        source_label="rain on the glass",
        source_type="weather",
        location="the window",
        mystery=1,
        gentle=True,
        tags={"rain", "night"},
    ),
    "wind": Sound(
        id="wind",
        label="branches in the wind",
        cry="scritch-swish",
        source_label="branches brushing the wall",
        source_type="branches",
        location="the side of the house",
        mystery=2,
        gentle=True,
        tags={"wind", "night"},
    ),
    "cat": Sound(
        id="cat",
        label="porch cat sound",
        cry="mrrp",
        source_label="the neighbor's cat at the porch",
        source_type="animal",
        location="the front porch",
        mystery=1,
        gentle=True,
        tags={"cat", "night"},
    ),
}

MEMORIES = {
    "owl_walk": MemoryLesson(
        id="owl_walk",
        matches="owl",
        place="the park at dusk",
        adult="Grandpa",
        image="they had stood very still under a tree and listened to a soft owl call from high above",
        line="That round sound is an owl saying where it is.",
        truth="the whoop was only an owl calling from the garden tree",
        tags={"flashback", "owl"},
    ),
    "rain_panes": MemoryLesson(
        id="rain_panes",
        matches="rain",
        place="the kitchen window",
        adult="Mom",
        image="they had watched clear drops race each other down the glass",
        line="Rain can drum on windows and make a room sound fuller than it is.",
        truth="the patter was just rain tapping on the window",
        tags={"flashback", "rain"},
    ),
    "kite_wind": MemoryLesson(
        id="kite_wind",
        matches="wind",
        place="the hill by the school",
        adult="Dad",
        image="their kite had pulled at the string while the trees whispered and brushed together",
        line="Wind can make branches talk in scratchy little voices.",
        truth="the scratchy sound came from branches moving in the wind",
        tags={"flashback", "wind"},
    ),
    "porch_cat": MemoryLesson(
        id="porch_cat",
        matches="cat",
        place="the front steps",
        adult="Grandma",
        image="they had set out a small bowl of water while the striped cat blinked in the evening light",
        line="That tiny voice is the porch cat asking if anyone is there.",
        truth="the small sound was only the neighbor's cat near the porch",
        tags={"flashback", "cat"},
    ),
}

COMFORTS = {
    "rabbit": Comfort(
        id="rabbit",
        label="cloth rabbit",
        phrase="the cloth rabbit",
        action="with the cloth rabbit tucked under one arm",
        tags={"comfort"},
    ),
    "blanket": Comfort(
        id="blanket",
        label="patchwork blanket",
        phrase="the patchwork blanket",
        action="with the patchwork blanket snug beneath the chin",
        tags={"comfort"},
    ),
    "bear": Comfort(
        id="bear",
        label="little teddy bear",
        phrase="the little teddy bear",
        action="with the little teddy bear warm against the cheek",
        tags={"comfort"},
    ),
}

RESPONSES = {
    "listen_together": Response(
        id="listen_together",
        sense=3,
        needs_view=False,
        text="listened with",
        follow="for another breath and smiled softly.",
        qa_text="They listened together until the sound matched the remembered lesson.",
        tags={"comfort"},
    ),
    "peek_window": Response(
        id="peek_window",
        sense=3,
        needs_view=True,
        text="lifted the curtain edge and peeked with",
        follow="into the night for a moment before pointing out the harmless source.",
        qa_text="They peeked together and saw what was making the sound.",
        tags={"night"},
    ),
    "hall_shout": Response(
        id="hall_shout",
        sense=1,
        needs_view=False,
        text="called loudly down the hall for the sound to stop, which did not explain anything to",
        follow="at all.",
        qa_text="The grown-up only shouted, which did not really help the child understand the sound.",
        tags=set(),
    ),
}


@dataclass
class StoryParams:
    sound: str
    memory: str
    comfort: str
    response: str
    child_name: str
    child_type: str
    parent_type: str
    trait: str
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


GIRL_NAMES = ["Mina", "Lila", "Nora", "Eva", "Ivy", "Tess", "Ruby", "Anna"]
BOY_NAMES = ["Owen", "Milo", "Ben", "Noah", "Theo", "Finn", "Eli", "Sam"]
TRAITS = ["thoughtful", "sleepy", "curious", "gentle", "quiet", "careful"]

CURATED = [
    StoryParams(
        sound="owl",
        memory="owl_walk",
        comfort="rabbit",
        response="peek_window",
        child_name="Mina",
        child_type="girl",
        parent_type="mother",
        trait="thoughtful",
    ),
    StoryParams(
        sound="rain",
        memory="rain_panes",
        comfort="blanket",
        response="listen_together",
        child_name="Owen",
        child_type="boy",
        parent_type="father",
        trait="quiet",
    ),
    StoryParams(
        sound="wind",
        memory="kite_wind",
        comfort="bear",
        response="peek_window",
        child_name="Lila",
        child_type="girl",
        parent_type="mother",
        trait="careful",
    ),
    StoryParams(
        sound="cat",
        memory="porch_cat",
        comfort="rabbit",
        response="listen_together",
        child_name="Theo",
        child_type="boy",
        parent_type="father",
        trait="curious",
    ),
]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    sound = world.facts["sound"]
    memory = world.facts["memory"]
    comfort = world.facts["comfort"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "whoop" and "nightie" and uses a flashback to explain a night sound.',
        f"Tell a gentle bedtime story where {child.id} hears {sound.label} in the dark, remembers an earlier moment at {memory.place}, and feels safe again while holding {comfort.phrase}.",
        f"Write a soft story about a child in a nightie who gets frightened by a sound at bedtime, then calms down because a flashback helps the child understand what the sound really is.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    sound = world.facts["sound"]
    memory = world.facts["memory"]
    comfort = world.facts["comfort"]
    response = world.facts["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a sleepy little {child.type} getting ready for bed, and {child.pronoun('possessive')} {parent.label_word} who stayed close and helped. The story happens in the child's bedroom at bedtime."
        ),
        (
            "Why did the sound feel scary at first?",
            f"It felt scary because the room was dark and {child.id} could not tell what was making the sound yet. When a sound is still a mystery, it can seem much bigger than it really is."
        ),
        (
            "What was the flashback about?",
            f"The flashback took {child.id} back to {memory.place}, where {memory.adult} had already explained this kind of sound. That earlier lesson gave the child something true and warm to remember in the dark."
        ),
        (
            f"How did {parent.label_word} help {child.id} calm down?",
            f"{parent.label_word.capitalize()} stayed beside the bed, helped {child.id} hold {comfort.phrase}, and then {response.qa_text} Because the grown-up stayed calm and the memory matched the sound, fear turned into understanding."
        ),
        (
            "What was really making the sound?",
            f"{memory.truth[0].upper()}{memory.truth[1:]}. Once {child.id} knew the cause, the sound stopped feeling like a danger."
        ),
        (
            "How did the story end?",
            f"It ended peacefully, with {child.id} settled under the blanket and ready to sleep. The ending shows the change clearly: the same night sound was still there, but now it felt gentle instead of frightening."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    sound = world.facts["sound"]
    memory = world.facts["memory"]
    comfort = world.facts["comfort"]
    tags = set(sound.tags) | set(memory.tags) | set(comfort.tags) | {"flashback", "night"}
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
matches_sound(M, S) :- memory(M), memory_matches(M, S).
usable_response(S, R) :- response(R), sense(R, V), sense_min(Min), V >= Min, not needs_view(R).
usable_response(S, R) :- response(R), sense(R, V), sense_min(Min), V >= Min, needs_view(R), source_viewable(S).

valid(S, M, C, R) :- sound(S), memory(M), comfort(C), response(R),
                     matches_sound(M, S), usable_response(S, R).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, sound in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        if sound.source_type in {"animal", "weather", "branches"}:
            lines.append(asp.fact("source_viewable", sid))
    for mid, memory in MEMORIES.items():
        lines.append(asp.fact("memory", mid))
        lines.append(asp.fact("memory_matches", mid, memory.matches))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort", cid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        if response.needs_view:
            lines.append(asp.fact("needs_view", rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for params in CURATED:
        try:
            generate(params)
        except Exception as err:  # pragma: no cover
            rc = 1
            print(f"CURATED GENERATION FAILED for {params}: {err}")
            break

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime flashback story world: a child hears a night sound, remembers an earlier lesson, and settles safely."
    )
    ap.add_argument("--sound", choices=sorted(SOUNDS))
    ap.add_argument("--memory", choices=sorted(MEMORIES))
    ap.add_argument("--comfort", choices=sorted(COMFORTS))
    ap.add_argument("--response", choices=sorted(RESPONSES))
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sound and args.memory:
        sound = SOUNDS[args.sound]
        memory = MEMORIES[args.memory]
        if not memory_matches(sound, memory):
            raise StoryError(explain_rejection(sound, memory))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.sound and args.response:
        if not response_fits(SOUNDS[args.sound], RESPONSES[args.response]):
            raise StoryError("(No story: that response does not sensibly fit this kind of night sound.)")

    combos = [
        combo for combo in valid_combos()
        if (args.sound is None or combo[0] == args.sound)
        and (args.memory is None or combo[1] == args.memory)
        and (args.comfort is None or combo[2] == args.comfort)
        and (args.response is None or combo[3] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    sound_id, memory_id, comfort_id, response_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        sound=sound_id,
        memory=memory_id,
        comfort=comfort_id,
        response=response_id,
        child_name=name,
        child_type=child_type,
        parent_type=parent_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.sound not in SOUNDS:
        raise StoryError(f"(Unknown sound: {params.sound})")
    if params.memory not in MEMORIES:
        raise StoryError(f"(Unknown memory: {params.memory})")
    if params.comfort not in COMFORTS:
        raise StoryError(f"(Unknown comfort: {params.comfort})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    sound = SOUNDS[params.sound]
    memory = MEMORIES[params.memory]
    comfort = COMFORTS[params.comfort]
    response = RESPONSES[params.response]

    if not memory_matches(sound, memory):
        raise StoryError(explain_rejection(sound, memory))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not response_fits(sound, response):
        raise StoryError("(No story: that response does not sensibly fit this kind of night sound.)")

    world = tell(
        sound=sound,
        memory=memory,
        comfort=comfort,
        response=response,
        child_name=params.child_name,
        child_type=params.child_type,
        parent_type=params.parent_type,
        trait=params.trait,
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
        print(f"{len(combos)} compatible (sound, memory, comfort, response) combos:\n")
        for sound_id, memory_id, comfort_id, response_id in combos:
            print(f"  {sound_id:6} {memory_id:10} {comfort_id:8} {response_id}")
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
            header = f"### {p.child_name}: {p.sound} with {p.memory} ({p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
