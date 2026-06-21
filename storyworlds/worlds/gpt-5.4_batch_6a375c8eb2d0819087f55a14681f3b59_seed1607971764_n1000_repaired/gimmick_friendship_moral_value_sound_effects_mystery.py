#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gimmick_friendship_moral_value_sound_effects_mystery.py
===================================================================================

A standalone storyworld for a tiny child-facing mystery with friendship, a moral
about not jumping to conclusions, and playful sound effects.

Premise
-------
Two children hear strange sounds in a familiar place and begin to imagine a
mystery. The noises come from a simple gimmick built by a third child who feels
too shy to speak directly. The friends solve the mystery by investigating
kindly instead of accusing anyone, and the ending image proves that friendship
has been repaired.

Run it
------
    python storyworlds/worlds/gpt-5.4/gimmick_friendship_moral_value_sound_effects_mystery.py
    python storyworlds/worlds/gpt-5.4/gimmick_friendship_moral_value_sound_effects_mystery.py --place clubhouse --gimmick bell_string --goal apology
    python storyworlds/worlds/gpt-5.4/gimmick_friendship_moral_value_sound_effects_mystery.py --place pond --gimmick chalk_slider
    python storyworlds/worlds/gpt-5.4/gimmick_friendship_moral_value_sound_effects_mystery.py --all
    python storyworlds/worlds/gpt-5.4/gimmick_friendship_moral_value_sound_effects_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/gimmick_friendship_moral_value_sound_effects_mystery.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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
class Place:
    id: str
    label: str
    opening: str
    hiding_spot: str
    approach: str
    affordances: set[str] = field(default_factory=set)
    echo: str = ""
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
class Gimmick:
    id: str
    label: str
    phrase: str
    sound: str
    setup: str
    reveal: str
    needs: set[str] = field(default_factory=set)
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
class Goal:
    id: str
    hidden_item: str
    item_phrase: str
    item_the: str
    note_text: str
    reason: str
    ending_image: str
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
class Mood:
    id: str
    feeling: str
    why_quiet: str
    brave_line: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_mystery_fear(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("place")
    if room.meters["noise"] >= THRESHOLD:
        for kid in (world.get("lead"), world.get("buddy")):
            sig = ("fear", kid.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            kid.memes["wonder"] += 1
            kid.memes["fear"] += 1
            out.append("__mystery__")
    return out


def _r_kindness_calms(world: World) -> list[str]:
    out: list[str] = []
    if world.get("lead").memes["kind_choice"] < THRESHOLD:
        return out
    for kid in (world.get("lead"), world.get("buddy"), world.get("hidden")):
        sig = ("calm", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if kid.memes["fear"] >= THRESHOLD:
            kid.memes["fear"] -= 1
        kid.memes["trust"] += 1
    out.append("__calm__")
    return out


def _r_reveal_repairs(world: World) -> list[str]:
    out: list[str] = []
    hidden = world.get("hidden")
    if hidden.memes["revealed"] < THRESHOLD:
        return out
    sig = ("repair", hidden.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hidden.memes["relief"] += 1
    world.get("lead").memes["friendship"] += 1
    world.get("buddy").memes["friendship"] += 1
    hidden.memes["friendship"] += 1
    out.append("__repair__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="mystery_fear", tag="emotional", apply=_r_mystery_fear),
    Rule(name="kindness_calms", tag="emotional", apply=_r_kindness_calms),
    Rule(name="reveal_repairs", tag="social", apply=_r_reveal_repairs),
]


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
        for sent in produced:
            world.say(sent)
    return produced


def gimmick_fits(place: Place, gimmick: Gimmick) -> bool:
    return gimmick.needs.issubset(place.affordances)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for gimmick_id, gimmick in GIMMICKS.items():
            if not gimmick_fits(place, gimmick):
                continue
            for goal_id in GOALS:
                for mood_id in MOODS:
                    combos.append((place_id, gimmick_id, goal_id, mood_id))
    return combos


def predict_kind_outcome(place: Place, gimmick: Gimmick, goal: Goal, mood: Mood) -> dict:
    world = World(place)
    world.add(Entity(id="place", type="place", label=place.label))
    world.add(Entity(id="lead", kind="character", type="girl", role="lead"))
    world.add(Entity(id="buddy", kind="character", type="boy", role="buddy"))
    world.add(Entity(id="hidden", kind="character", type="girl", role="hidden"))
    world.facts["goal"] = goal
    world.facts["mood"] = mood
    trigger_noise(world, gimmick, narrate=False)
    choose_kindness(world, narrate=False)
    reveal_friend(world, gimmick, goal, mood, narrate=False)
    return {
        "solved": world.get("hidden").memes["revealed"] >= THRESHOLD,
        "friendship": world.get("hidden").memes["friendship"] >= THRESHOLD,
    }


def trigger_noise(world: World, gimmick: Gimmick, narrate: bool = True) -> None:
    place = world.get("place")
    place.meters["noise"] += 1
    world.facts["sound_word"] = gimmick.sound
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"Then it came again from {world.place.hiding_spot}: {gimmick.sound}!"
        )


def choose_kindness(world: World, narrate: bool = True) -> None:
    world.get("lead").memes["kind_choice"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(
            "Instead of blaming anyone, they promised each other that they would ask kindly first."
        )


def reveal_friend(world: World, gimmick: Gimmick, goal: Goal, mood: Mood, narrate: bool = True) -> None:
    hidden = world.get("hidden")
    hidden.memes["revealed"] += 1
    hidden.meters["visible"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"Behind the shadows stood {hidden.id}, cheeks pink, beside {gimmick.reveal} and {goal.item_the}."
        )
        world.say(
            f'"I made this little gimmick because I was {mood.feeling}," {hidden.pronoun()} said. '
            f'"{mood.why_quiet} {mood.brave_line}"'
        )


def setup_story(world: World, lead: Entity, buddy: Entity, hidden: Entity, place: Place, goal: Goal) -> None:
    for kid in (lead, buddy, hidden):
        kid.memes["friendship"] = 1.0
    hidden.memes["friendship"] = 0.0
    hidden.memes["shy"] = 1.0
    world.say(
        f"{lead.id} and {buddy.id} loved meeting at {place.label}. {place.opening}"
    )
    world.say(
        f"That afternoon, though, their friend {hidden.id} was nowhere to be seen, and {goal.item_the} was missing too."
    )


def first_clue(world: World, lead: Entity, buddy: Entity, place: Place) -> None:
    world.say(
        f"They stood still and listened. {place.echo}"
    )
    world.say(
        f'"Did you hear that?" {buddy.id} whispered. "{world.place.hiding_spot.capitalize()} sounded alive."'
    )
    world.say(
        f"{lead.id} felt a little shiver, but stepped closer to {place.approach}."
    )


def worry_beat(world: World, lead: Entity, buddy: Entity) -> None:
    lead.memes["suspicion"] += 1
    buddy.memes["suspicion"] += 1
    world.say(
        f'"Maybe someone is playing a trick," {buddy.id} said softly.'
    )
    world.say(
        f'"Or maybe there is a reason," {lead.id} answered. {lead.pronoun().capitalize()} did not want the mystery to turn mean.'
    )


def follow_clue(world: World, gimmick: Gimmick, goal: Goal) -> None:
    world.say(
        f"They followed the strange noise and found {gimmick.setup}. Beside it lay a folded note."
    )
    world.say(f'The note said, "{goal.note_text}"')


def repair_scene(world: World, lead: Entity, buddy: Entity, hidden: Entity, goal: Goal) -> None:
    lead.memes["care"] += 1
    buddy.memes["care"] += 1
    hidden.memes["care"] += 1
    world.say(
        f'{lead.id} smiled first. "You did not need to hide from us," {lead.pronoun()} said.'
    )
    world.say(
        f'"We are your friends," {buddy.id} added. "Next time, you can just tell us."'
    )
    world.say(
        f"{hidden.id} handed over {goal.item_the} and nodded hard. The mystery melted away, and something warmer took its place."
    )


def ending_scene(world: World, lead: Entity, buddy: Entity, hidden: Entity, place: Place, goal: Goal) -> None:
    for kid in (lead, buddy, hidden):
        kid.memes["joy"] += 1
    world.say(
        f"Soon the three friends were sitting together in {place.label}, reading the note again and laughing at the tiny gimmick that had sounded so huge in the dark."
    )
    world.say(goal.ending_image)


def tell(
    place: Place,
    gimmick: Gimmick,
    goal: Goal,
    mood: Mood,
    lead_name: str = "Mina",
    lead_gender: str = "girl",
    buddy_name: str = "Owen",
    buddy_gender: str = "boy",
    hidden_name: str = "Tess",
    hidden_gender: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World(place)
    lead = world.add(Entity(id=lead_name, kind="character", type=lead_gender, role="lead", traits=["careful"]))
    buddy = world.add(Entity(id=buddy_name, kind="character", type=buddy_gender, role="buddy", traits=["brave"]))
    hidden = world.add(Entity(id=hidden_name, kind="character", type=hidden_gender, role="hidden", traits=["quiet"]))
    world.add(Entity(id="place", type="place", label=place.label))
    world.add(Entity(id="parent", kind="character", type=parent_type, role="parent", label="the grown-up"))

    world.facts["place_cfg"] = place
    world.facts["gimmick_cfg"] = gimmick
    world.facts["goal_cfg"] = goal
    world.facts["mood_cfg"] = mood
    world.facts["sound_word"] = gimmick.sound

    setup_story(world, lead, buddy, hidden, place, goal)
    world.para()
    first_clue(world, lead, buddy, place)
    trigger_noise(world, gimmick)
    worry_beat(world, lead, buddy)

    world.para()
    choose_kindness(world)
    follow_clue(world, gimmick, goal)
    reveal_friend(world, gimmick, goal, mood)

    world.para()
    repair_scene(world, lead, buddy, hidden, goal)
    ending_scene(world, lead, buddy, hidden, place, goal)

    world.facts.update(
        lead=lead,
        buddy=buddy,
        hidden=hidden,
        mystery_solved=hidden.memes["revealed"] >= THRESHOLD,
        friendship_repaired=hidden.memes["friendship"] >= THRESHOLD,
        kind_choice=lead.memes["kind_choice"] >= THRESHOLD,
    )
    return world


PLACES = {
    "clubhouse": Place(
        id="clubhouse",
        label="the little clubhouse",
        opening="It was built from old boards, with a crooked window and a floor that remembered every footstep.",
        hiding_spot="the back wall",
        approach="the wobbling ladder",
        affordances={"beam", "hook", "board", "string"},
        echo="Creak... tap... creak. The boards gave small answers to the wind.",
        tags={"clubhouse", "mystery"},
    ),
    "library_nook": Place(
        id="library_nook",
        label="the reading nook behind the library curtain",
        opening="A lamp glowed there, and the cloth curtain made the corner feel like a secret cave for books.",
        hiding_spot="behind the curtain",
        approach="the striped rug",
        affordances={"hook", "curtain", "string", "paper"},
        echo="Swish... tik-tik... swish. The curtain breathed whenever the air moved.",
        tags={"library", "mystery"},
    ),
    "garden_shed": Place(
        id="garden_shed",
        label="the old garden shed",
        opening="Flowerpots lined the wall, and a narrow window let in one stripe of golden light.",
        hiding_spot="the shelf in the corner",
        approach="the stepping stones",
        affordances={"beam", "hook", "string", "tin"},
        echo="Clink... clink... hush. Something inside answered the breeze.",
        tags={"garden", "mystery"},
    ),
    "pond": Place(
        id="pond",
        label="the duck pond path",
        opening="Reeds leaned over the water, and ducks drifted by with sleepy little ripples.",
        hiding_spot="the reeds",
        approach="the muddy edge",
        affordances={"water", "mud"},
        echo="Plip... plip... quack. The pond made its own sounds.",
        tags={"pond"},
    ),
}

GIMMICKS = {
    "bell_string": Gimmick(
        id="bell_string",
        label="bell-and-string gimmick",
        phrase="a bell-and-string gimmick",
        sound="ting-ting",
        setup="a loop of string tied from a shelf to a tiny bell",
        reveal="the bell-and-string gimmick",
        needs={"hook", "string"},
        tags={"bell", "gimmick", "sound"},
    ),
    "chalk_slider": Gimmick(
        id="chalk_slider",
        label="chalk-slider gimmick",
        phrase="a chalk-slider gimmick",
        sound="scritch-scritch",
        setup="a piece of chalk hanging on string so it brushed a board when tugged",
        reveal="the chalk-slider gimmick",
        needs={"board", "string"},
        tags={"chalk", "gimmick", "sound"},
    ),
    "tin_tapper": Gimmick(
        id="tin_tapper",
        label="tin-cup gimmick",
        phrase="a tin-cup gimmick",
        sound="clink-clink",
        setup="a little string that made two tin cups tap each other",
        reveal="the tin-cup gimmick",
        needs={"tin", "string"},
        tags={"tin", "gimmick", "sound"},
    ),
    "curtain_whisper": Gimmick(
        id="curtain_whisper",
        label="curtain-whisper gimmick",
        phrase="a curtain-whisper gimmick",
        sound="swish-swish",
        setup="a ribbon pulling the curtain so it whispered against the wall",
        reveal="the curtain-whisper gimmick",
        needs={"curtain", "string"},
        tags={"curtain", "gimmick", "sound"},
    ),
}

GOALS = {
    "apology": Goal(
        id="apology",
        hidden_item="friendship bead",
        item_phrase="a friendship bead bracelet",
        item_the="the friendship bead bracelet",
        note_text="I am sorry. Please follow the sound.",
        reason="to say sorry after a small argument",
        ending_image="At the end, the bracelet was back on a wrist, and three small hands rested together on the windowsill.",
        tags={"apology", "friendship"},
    ),
    "return_map": Goal(
        id="return_map",
        hidden_item="treasure map",
        item_phrase="the hand-drawn treasure map",
        item_the="the hand-drawn treasure map",
        note_text="I found this and wanted you to have it back. Follow the sound.",
        reason="to return something important without interrupting the game",
        ending_image="At the end, the map lay open between them, and their heads leaned close over the same bright crayon path.",
        tags={"map", "friendship"},
    ),
    "share_badge": Goal(
        id="share_badge",
        hidden_item="helper badge",
        item_phrase="a shiny helper badge",
        item_the="the shiny helper badge",
        note_text="I made this for us to share. Follow the sound.",
        reason="to make peace by sharing instead of keeping a prize alone",
        ending_image="At the end, the badge was pinned to the wall between their coats, where it belonged to all of them at once.",
        tags={"sharing", "friendship"},
    ),
}

MOODS = {
    "shy": Mood(
        id="shy",
        feeling="too shy",
        why_quiet="I wanted to talk, but the words hid from me.",
        brave_line="So I made the sound lead you to me.",
        tags={"shy"},
    ),
    "worried": Mood(
        id="worried",
        feeling="worried",
        why_quiet="I thought you might still be upset with me.",
        brave_line="I hoped the noise would help me be brave.",
        tags={"worry"},
    ),
    "embarrassed": Mood(
        id="embarrassed",
        feeling="embarrassed",
        why_quiet="I felt silly after our mix-up.",
        brave_line="Making a small mystery felt easier than speaking first.",
        tags={"embarrassed"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Zoe", "Ivy", "Ella", "Tess", "Ruby", "June"]
BOY_NAMES = ["Owen", "Ben", "Max", "Leo", "Finn", "Eli", "Theo", "Noah", "Sam", "Jack"]


@dataclass
class StoryParams:
    place: str
    gimmick: str
    goal: str
    mood: str
    lead_name: str
    lead_gender: str
    buddy_name: str
    buddy_gender: str
    hidden_name: str
    hidden_gender: str
    parent: str
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


KNOWLEDGE = {
    "gimmick": [
        (
            "What is a gimmick?",
            "A gimmick is a small trick or clever device that does one special thing. It can be playful, but it should never be used to scare or fool people in a mean way.",
        )
    ],
    "bell": [
        (
            "How does a bell make a sound?",
            "A bell rings when something taps or shakes it. The metal wiggles very fast and that makes the air carry a tinging sound.",
        )
    ],
    "chalk": [
        (
            "Why does chalk make a scratchy sound?",
            "Chalk sounds scratchy because it rubs against a rough surface. Tiny bits scrape along as it moves.",
        )
    ],
    "tin": [
        (
            "Why do tin cups go clink-clink?",
            "Tin cups make a clink sound when they tap each other. Hard things can make bright little noises when they bump.",
        )
    ],
    "curtain": [
        (
            "Why can a curtain make a swishing sound?",
            "A curtain swishes when cloth slides through the air or brushes a wall. Soft fabric can still make a clear sound when it moves.",
        )
    ],
    "friendship": [
        (
            "What should friends do before blaming each other?",
            "Friends should ask kindly and listen first. A calm question can solve a problem faster than an angry guess.",
        )
    ],
    "apology": [
        (
            "Why is saying sorry important?",
            "Saying sorry shows that you know a hurt feeling matters. A real apology helps trust grow back.",
        )
    ],
    "sharing": [
        (
            "Why is sharing a good choice?",
            "Sharing can turn one prize into something everyone enjoys together. It helps friends feel included instead of left out.",
        )
    ],
    "map": [
        (
            "Why do people keep maps safe?",
            "Maps help people find where they are going. If a map is lost, the adventure can get confusing.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something hidden that people try to figure out. Good detectives look for clues instead of making wild guesses.",
        )
    ],
}
KNOWLEDGE_ORDER = ["gimmick", "mystery", "bell", "chalk", "tin", "curtain", "friendship", "apology", "sharing", "map"]


def generation_prompts(world: World) -> list[str]:
    lead = world.facts["lead"]
    buddy = world.facts["buddy"]
    hidden = world.facts["hidden"]
    gimmick = world.facts["gimmick_cfg"]
    goal = world.facts["goal_cfg"]
    place = world.facts["place_cfg"]
    mood = world.facts["mood_cfg"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the word "gimmick" and a sound like "{gimmick.sound}".',
        f"Tell a gentle friendship mystery where {lead.id} and {buddy.id} hear strange noises in {place.label} and discover that {hidden.id} built a {gimmick.label} {goal.reason}.",
        f"Write a child-friendly mystery with sound effects, a shy friend who feels {mood.feeling}, and an ending that teaches children to ask kindly before blaming anyone.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    lead = world.facts["lead"]
    buddy = world.facts["buddy"]
    hidden = world.facts["hidden"]
    place = world.facts["place_cfg"]
    gimmick = world.facts["gimmick_cfg"]
    goal = world.facts["goal_cfg"]
    mood = world.facts["mood_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.id}, {buddy.id}, and their friend {hidden.id}. The mystery matters because they care about one another, not because the place is truly dangerous.",
        ),
        (
            "What made the place feel mysterious?",
            f"The strange sound {gimmick.sound} came from {place.hiding_spot}, so the familiar place suddenly felt secret and puzzling. The children could not see who made the noise at first, which made their imaginations wake up.",
        ),
        (
            "What was the gimmick in the story?",
            f"The gimmick was {gimmick.phrase}. It was a simple little device made to create a clue-like sound and lead the friends toward the truth.",
        ),
        (
            "Why did the children choose not to blame anyone right away?",
            f"They promised to ask kindly first instead of turning the mystery mean. That choice mattered because the sounds were only clues, not proof that someone had done something bad.",
        ),
        (
            f"Why was {hidden.id} hiding?",
            f"{hidden.id} was {mood.feeling} and wanted to speak, but felt too nervous to begin. {hidden.pronoun().capitalize()} used the gimmick to guide the others to {goal.item_the} and the note.",
        ),
        (
            "How was the mystery solved?",
            f"The friends followed the sound, found the gimmick and the note, and then discovered {hidden.id} waiting nearby. Because they approached gently, the mystery ended with truth instead of hurt feelings.",
        ),
        (
            "What lesson did the story teach?",
            f"The story taught that friendship grows stronger when people ask, listen, and forgive. Kindness solved the mystery faster than suspicion could have.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    gimmick = world.facts["gimmick_cfg"]
    goal = world.facts["goal_cfg"]
    tags = {"gimmick", "friendship", "mystery"} | set(gimmick.tags) | set(goal.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="clubhouse",
        gimmick="bell_string",
        goal="apology",
        mood="shy",
        lead_name="Mina",
        lead_gender="girl",
        buddy_name="Owen",
        buddy_gender="boy",
        hidden_name="Tess",
        hidden_gender="girl",
        parent="mother",
        seed=101,
    ),
    StoryParams(
        place="library_nook",
        gimmick="curtain_whisper",
        goal="return_map",
        mood="worried",
        lead_name="Ruby",
        lead_gender="girl",
        buddy_name="Leo",
        buddy_gender="boy",
        hidden_name="June",
        hidden_gender="girl",
        parent="father",
        seed=102,
    ),
    StoryParams(
        place="garden_shed",
        gimmick="tin_tapper",
        goal="share_badge",
        mood="embarrassed",
        lead_name="Ava",
        lead_gender="girl",
        buddy_name="Finn",
        buddy_gender="boy",
        hidden_name="Nora",
        hidden_gender="girl",
        parent="mother",
        seed=103,
    ),
    StoryParams(
        place="clubhouse",
        gimmick="chalk_slider",
        goal="return_map",
        mood="worried",
        lead_name="Ella",
        lead_gender="girl",
        buddy_name="Max",
        buddy_gender="boy",
        hidden_name="Ivy",
        hidden_gender="girl",
        parent="father",
        seed=104,
    ),
]


def explain_rejection(place: Place, gimmick: Gimmick) -> str:
    needed = ", ".join(sorted(gimmick.needs))
    has = ", ".join(sorted(place.affordances))
    return (
        f"(No story: {gimmick.label} needs {needed}, but {place.label} only offers {has}. "
        f"The mystery sound would not be plausible there, so this combination is rejected.)"
    )


ASP_RULES = r"""
fits(P,G) :- place(P), gimmick(G), needs_ok(P,G).
needs_ok(P,G) :- not missing_need(P,G).
missing_need(P,G) :- needs(G,N), not affords(P,N).

valid(P,G,Goal,M) :- fits(P,G), goal(Goal), mood(M).

#show valid/4.
#show fits/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for feat in sorted(place.affordances):
            lines.append(asp.fact("affords", place_id, feat))
    for gimmick_id, gimmick in GIMMICKS.items():
        lines.append(asp.fact("gimmick", gimmick_id))
        for need in sorted(gimmick.needs):
            lines.append(asp.fact("needs", gimmick_id, need))
    for goal_id in GOALS:
        lines.append(asp.fact("goal", goal_id))
    for mood_id in MOODS:
        lines.append(asp.fact("mood", mood_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_fit_pairs() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "fits")))


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_fit = {
        (place_id, gimmick_id)
        for place_id, place in PLACES.items()
        for gimmick_id, gimmick in GIMMICKS.items()
        if gimmick_fits(place, gimmick)
    }
    asp_fit = set(asp_fit_pairs())
    if py_fit == asp_fit:
        print(f"OK: place/gimmick compatibility matches ({len(py_fit)} pairs).")
    else:
        rc = 1
        print("MISMATCH in fit pairs:")
        if asp_fit - py_fit:
            print("  only in clingo:", sorted(asp_fit - py_fit))
        if py_fit - asp_fit:
            print("  only in python:", sorted(py_fit - asp_fit))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "gimmick" not in sample.story.lower():
            raise StoryError("smoke test story missing expected content")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small mystery storyworld about a sound-making gimmick, friendship, and asking kindly before blaming."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gimmick", choices=GIMMICKS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--lead-name")
    ap.add_argument("--buddy-name")
    ap.add_argument("--hidden-name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.gimmick:
        place = PLACES[args.place]
        gimmick = GIMMICKS[args.gimmick]
        if not gimmick_fits(place, gimmick):
            raise StoryError(explain_rejection(place, gimmick))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.gimmick is None or combo[1] == args.gimmick)
        and (args.goal is None or combo[2] == args.goal)
        and (args.mood is None or combo[3] == args.mood)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, gimmick_id, goal_id, mood_id = rng.choice(sorted(combos))

    lead_gender = "girl"
    buddy_gender = "boy"
    hidden_gender = "girl"
    used: set[str] = set()
    lead_name = args.lead_name or _pick_name(rng, lead_gender, used)
    used.add(lead_name)
    buddy_name = args.buddy_name or _pick_name(rng, buddy_gender, used)
    used.add(buddy_name)
    hidden_name = args.hidden_name or _pick_name(rng, hidden_gender, used)
    parent = args.parent or rng.choice(["mother", "father"])

    return StoryParams(
        place=place_id,
        gimmick=gimmick_id,
        goal=goal_id,
        mood=mood_id,
        lead_name=lead_name,
        lead_gender=lead_gender,
        buddy_name=buddy_name,
        buddy_gender=buddy_gender,
        hidden_name=hidden_name,
        hidden_gender=hidden_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.gimmick not in GIMMICKS:
        raise StoryError(f"(Unknown gimmick: {params.gimmick})")
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal: {params.goal})")
    if params.mood not in MOODS:
        raise StoryError(f"(Unknown mood: {params.mood})")

    place = PLACES[params.place]
    gimmick = GIMMICKS[params.gimmick]
    goal = GOALS[params.goal]
    mood = MOODS[params.mood]

    if not gimmick_fits(place, gimmick):
        raise StoryError(explain_rejection(place, gimmick))

    predicted = predict_kind_outcome(place, gimmick, goal, mood)
    if not predicted["solved"]:
        raise StoryError("(No story: the mystery does not resolve cleanly.)")

    world = tell(
        place=place,
        gimmick=gimmick,
        goal=goal,
        mood=mood,
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        buddy_name=params.buddy_name,
        buddy_gender=params.buddy_gender,
        hidden_name=params.hidden_name,
        hidden_gender=params.hidden_gender,
        parent_type=params.parent,
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
        print(f"{len(combos)} compatible (place, gimmick, goal, mood) combos:\n")
        for place, gimmick, goal, mood in combos:
            print(f"  {place:12} {gimmick:15} {goal:12} {mood}")
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
            header = f"### {p.place}: {p.gimmick} for {p.goal} ({p.mood})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
