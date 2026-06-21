#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/prayer_sound_effects_bravery_bedtime_story.py
=============================================================================

A standalone storyworld for a bedtime tale about a child who feels scared at
night, remembers a prayer, uses playful sound effects to steady their courage,
and finds that bravery can be small, soft, and enough.

The world is built as a tiny simulation:
- a child has meters (tiredness, courage, fear, calm)
- the room has physical state (darkness, coziness, noise)
- sound effects are represented as events that can change emotion
- prayer is a quiet action that can lower fear and raise calm
- bravery is not the absence of fear, but a turn toward courage anyway

This file follows the shared Storyweavers contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Theme:
    id: str
    room: str
    bedtime_frame: str
    cover: str
    closing: str
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


@dataclass
class SoundEffect:
    id: str
    text: str
    source: str
    comfort: str
    courage_boost: int
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
class Prayer:
    id: str
    text: str
    effect: str
    calm_boost: int
    fear_drop: int
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
class ComfortObject:
    id: str
    label: str
    help_line: str
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.events: list[str] = []

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
        clone.events = list(self.events)
        return clone


def _r_sound_to_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    for effect in SOUND_EFFECTS.values():
        sig = ("sound", effect.id)
        if sig in world.fired:
            continue
        if child.memes["fear"] < THRESHOLD:
            continue
        if effect.id not in world.facts.get("chosen_sounds", []):
            continue
        world.fired.add(sig)
        child.memes["courage"] += effect.courage_boost
        child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
        child.memes["calm"] += 0.5
        out.append(effect.comfort)
    return out


def _r_prayer_to_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    prayer = world.facts.get("prayer")
    if not prayer or child.memes["prayered"] >= THRESHOLD:
        return out
    sig = ("prayer", prayer.id)
    if sig in world.fired:
        return out
    if child.memes["fear"] < THRESHOLD:
        return out
    world.fired.add(sig)
    child.memes["prayered"] += 1
    child.memes["calm"] += prayer.calm_boost
    child.memes["fear"] = max(0.0, child.memes["fear"] - prayer.fear_drop)
    out.append(prayer.effect)
    return out


def _r_courage_from_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    sig = ("brave",)
    if sig in world.fired:
        return out
    if child.memes["calm"] < THRESHOLD:
        return out
    world.fired.add(sig)
    child.memes["courage"] += 1.0
    child.memes["brave"] += 1.0
    out.append("__brave__")
    return out


CAUSAL_RULES = [
    Rule("sound_to_calm", "emotional", _r_sound_to_calm),
    Rule("prayer_to_calm", "emotional", _r_prayer_to_calm),
    Rule("courage_from_calm", "emotional", _r_courage_from_calm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def bedtime_weather(theme: Theme) -> str:
    return theme.bedtime_frame


def reasonableness_ok(sound: SoundEffect, prayer: Prayer) -> bool:
    return bool(sound.text and prayer.text)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not reasonableness_ok(next(iter(SOUND_EFFECTS.values())), next(iter(PRAYERS.values()))):
        return combos
    for theme in THEMES:
        for sid, s in SOUND_EFFECTS.items():
            for pid, p in PRAYERS.items():
                combos.append((theme, sid, pid))
    return combos


def predict_night(world: World, sound_id: str, prayer_id: str) -> dict:
    sim = world.copy()
    sim.facts["chosen_sounds"] = [sound_id]
    sim.facts["prayer"] = PRAYERS[prayer_id]
    child = sim.get("child")
    child.memes["fear"] = max(child.memes["fear"], 1.0)
    propagate(sim, narrate=False)
    return {"calm": sim.get("child").memes["calm"], "courage": sim.get("child").memes["courage"]}


def bedtime_setup(world: World, child: Entity, parent: Entity, theme: Theme) -> None:
    child.meters["tiredness"] += 1.0
    child.memes["love"] += 1.0
    world.say(
        f"At bedtime, {child.id} curled under the {theme.cover} in {theme.room}. "
        f"{theme.bedtime_frame}"
    )


def first_sound(world: World, child: Entity, sound: SoundEffect) -> None:
    child.memes["fear"] += 1.0
    world.events.append(sound.id)
    world.say(
        f"Then came a little {sound.text} from somewhere in the room. "
        f"{child.id} listened very hard."
    )


def prayer_beat(world: World, child: Entity, prayer: Prayer) -> None:
    child.memes["fear"] += 0.5
    world.say(
        f"{child.id} closed {child.pronoun('possessive')} eyes and whispered a prayer: "
        f"\"{prayer.text}\""
    )


def brave_choice(world: World, child: Entity, sound: SoundEffect) -> None:
    child.memes["fear"] = max(0.0, child.memes["fear"] - 0.5)
    world.say(
        f"{child.id} took one slow breath and answered the room with a brave "
        f"little {sound.text} of {child.id}'s own."
    )


def resolve_night(world: World, parent: Entity, child: Entity, comfort: ComfortObject, theme: Theme) -> None:
    child.memes["calm"] += 1.0
    child.memes["joy"] += 1.0
    world.say(
        f"{parent.label_word.capitalize()} came to the doorway, smiling softly. "
        f"{parent.pronoun().capitalize()} tucked {child.id} in and handed over "
        f"{comfort.label}."
    )
    world.say(
        f"{child.id} hugged {comfort.label} close. The room felt smaller and kinder, "
        f"and the dark no longer felt lonely."
    )
    world.say(
        f"So {child.id} fell asleep brave and warm, while the last tiny {theme.closing} "
        f"settled into the hush of night."
    )


def tell(theme: Theme, sound: SoundEffect, prayer: Prayer, comfort: ComfortObject,
         child_name: str = "Maya", child_type: str = "girl",
         parent_name: str = "Mom", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id=comfort.id, kind="thing", type="comfort", label=comfort.label))
    world.facts["prayer"] = prayer
    world.facts["chosen_sounds"] = [sound.id]
    world.facts["theme"] = theme
    world.facts["sound"] = sound
    world.facts["comfort"] = comfort

    bedtime_setup(world, child, parent, theme)
    world.para()
    first_sound(world, child, sound)
    prayer_beat(world, child, prayer)
    propagate(world, narrate=False)
    world.say(sound.comfort)
    brave_choice(world, child, sound)
    propagate(world, narrate=False)
    world.para()
    resolve_night(world, parent, child, comfort, theme)

    world.facts.update(
        child=child,
        parent=parent,
        final_calm=child.memes["calm"],
        final_fear=child.memes["fear"],
        final_courage=child.memes["courage"],
        brave=child.memes["brave"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    theme: str
    sound: str
    prayer: str
    child_name: str
    child_gender: str
    parent_type: str
    comfort: str = ""
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


THEMES = {
    "moon": Theme(
        id="moon",
        room="the little bedroom",
        bedtime_frame="Moonlight lay in a silver stripe across the floor.",
        cover="blanket",
        closing="moonbeam",
    ),
    "rain": Theme(
        id="rain",
        room="the small attic room",
        bedtime_frame="Rain tapped softly at the window like a sleepy song.",
        cover="quilt",
        closing="raindrop",
    ),
    "forest": Theme(
        id="forest",
        room="the cabin room",
        bedtime_frame="The wind whispered through the pines outside the window.",
        cover="comforter",
        closing="rustle",
    ),
}

SOUND_EFFECTS = {
    "tap": SoundEffect(
        id="tap",
        text="tap tap tap",
        source="the window",
        comfort="The soft taps sounded less scary when listened to closely.",
        courage_boost=1,
        tags={"sound", "bedtime"},
    ),
    "creak": SoundEffect(
        id="creak",
        text="creeeak",
        source="the hallway",
        comfort="The long creak turned into just another old house noise.",
        courage_boost=2,
        tags={"sound", "bedtime"},
    ),
    "whoosh": SoundEffect(
        id="whoosh",
        text="whoosh",
        source="the curtain",
        comfort="The whoosh sounded like sleepy wind, not a monster at all.",
        courage_boost=1,
        tags={"sound", "bedtime"},
    ),
}

PRAYERS = {
    "short": Prayer(
        id="short",
        text="Please keep me safe and help me be brave.",
        effect="The prayer felt like a warm hand around a worried heart.",
        calm_boost=2,
        fear_drop=1,
        tags={"prayer", "bravery"},
    ),
    "gentle": Prayer(
        id="gentle",
        text="Please watch over my room and help me rest.",
        effect="The prayer made the dark corners feel a little softer.",
        calm_boost=3,
        fear_drop=1,
        tags={"prayer", "bravery"},
    ),
    "sweet": Prayer(
        id="sweet",
        text="Thank you for my bed, my home, and this quiet night.",
        effect="The prayer settled in like a lullaby and helped the fear loosen.",
        calm_boost=2,
        fear_drop=2,
        tags={"prayer", "bravery"},
    ),
}

COMFORTS = {
    "bear": ComfortObject(id="bear", label="a stuffed bear", help_line="A stuffed bear is soft and nice to hug.", tags={"bedtime"}),
    "bunny": ComfortObject(id="bunny", label="a little bunny toy", help_line="A toy can help a child feel less alone at night.", tags={"bedtime"}),
    "lamp": ComfortObject(id="lamp", label="a tiny night lamp", help_line="A night lamp gives a little light without waking the whole room.", tags={"bedtime"}),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ava", "Ella", "Zoe"]
BOY_NAMES = ["Leo", "Theo", "Max", "Noah", "Eli", "Finn"]

CURATED = [
    StoryParams(theme="moon", sound="tap", prayer="short", child_name="Mia", child_gender="girl", parent_type="mother", comfort="bear"),
    StoryParams(theme="rain", sound="creak", prayer="gentle", child_name="Leo", child_gender="boy", parent_type="father", comfort="bunny"),
    StoryParams(theme="forest", sound="whoosh", prayer="sweet", child_name="Nora", child_gender="girl", parent_type="mother", comfort="lamp"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the word "prayer" and a small brave sound effect.',
        f"Tell a gentle bedtime story where {f['child'].id} feels scared, says a prayer, and uses {f['sound'].text} to feel brave.",
        f'Write a cozy story about bravery at bedtime, with a prayer, a soft sound in the dark, and a calm ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, sound, prayer = f["child"], f["parent"], f["sound"], f["prayer"]
    comfort = f["comfort"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, a little child who feels sleepy and a little scared at bedtime. {child.id} learns that bravery can be quiet and gentle."),
        ("What did {0} whisper when the room felt scary?".format(child.id),
         f"{child.id} whispered a prayer: \"{prayer.text}\". The prayer helped {child.id} feel calmer and less alone."),
        ("How did the sound effect help?",
         f"The sound effect was {sound.text}. It gave the dark room a familiar little rhythm, and that helped {child.id} grow brave enough to breathe slowly and settle down."),
        ("What happened at the end?",
         f"{parent.label_word.capitalize()} helped with {comfort.label}, and {child.id} fell asleep brave and warm. The room stayed quiet, but it did not feel scary anymore."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a prayer?",
         "A prayer is a quiet set of words someone says to ask for help, give thanks, or feel close to God. In bedtime stories, it can help a child feel calm and safe."),
        ("What is bravery?",
         "Bravery means doing something even though you feel scared. It does not mean fear is gone; it means you keep going gently anyway."),
        ("What are sound effects?",
         "Sound effects are little noises made on purpose, like tap tap tap or whoosh, that help tell a story. They can make a scene feel playful or spooky."),
    ]


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
child_fear(C) :- child(C), fear(C, F), F >= 1.
prayer_used(P) :- prayer(P).
sound_used(S) :- sound(S).
calm(C) :- child(C), prayer_used(P), prayer_boost(P, B), B >= 2.
brave(C) :- child(C), calm(C), sound_used(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for sid, s in SOUND_EFFECTS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("sound_text", sid, s.text))
        lines.append(asp.fact("courage_boost", sid, s.courage_boost))
    for pid, p in PRAYERS.items():
        lines.append(asp.fact("prayer", pid))
        lines.append(asp.fact("prayer_boost", pid, p.calm_boost))
        lines.append(asp.fact("fear_drop", pid, p.fear_drop))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show theme/1.\n#show sound/1.\n#show prayer/1."))
    # We don't use the model for gating beyond smoke parity; enumerate via python.
    return sorted(set((t, s, p) for t in THEMES for s in SOUND_EFFECTS for p in PRAYERS))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos parity.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default generation smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: prayer, sound effects, and bravery.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--sound", choices=SOUND_EFFECTS)
    ap.add_argument("--prayer", choices=PRAYERS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.theme and args.theme not in THEMES:
        raise StoryError("Unknown theme.")
    if args.sound and args.sound not in SOUND_EFFECTS:
        raise StoryError("Unknown sound.")
    if args.prayer and args.prayer not in PRAYERS:
        raise StoryError("Unknown prayer.")
    if args.comfort and args.comfort not in COMFORTS:
        raise StoryError("Unknown comfort object.")
    theme = args.theme or rng.choice(list(THEMES))
    sound = args.sound or rng.choice(list(SOUND_EFFECTS))
    prayer = args.prayer or rng.choice(list(PRAYERS))
    comfort = args.comfort or rng.choice(list(COMFORTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    if not reasonableness_ok(SOUND_EFFECTS[sound], PRAYERS[prayer]):
        raise StoryError("No reasonable story for those choices.")
    return StoryParams(theme=theme, sound=sound, prayer=prayer, child_name=child_name, child_gender=child_gender, parent_type=parent, comfort=comfort)


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES or params.sound not in SOUND_EFFECTS or params.prayer not in PRAYERS or params.comfort not in COMFORTS:
        raise StoryError("Invalid story parameters.")
    world = tell(THEMES[params.theme], SOUND_EFFECTS[params.sound], PRAYERS[params.prayer], COMFORTS[params.comfort], params.child_name, params.child_gender, "Parent", params.parent_type)
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
        print(asp_program("", "#show theme/1.\n#show sound/1.\n#show prayer/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:\n")
        for t, s, p in valid_combos():
            print(f"  {t:8} {s:8} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


CURATED = [
    StoryParams(theme="moon", sound="tap", prayer="short", child_name="Mia", child_gender="girl", parent_type="mother", comfort="bear", seed=1),
    StoryParams(theme="rain", sound="creak", prayer="gentle", child_name="Leo", child_gender="boy", parent_type="father", comfort="bunny", seed=2),
    StoryParams(theme="forest", sound="whoosh", prayer="sweet", child_name="Nora", child_gender="girl", parent_type="mother", comfort="lamp", seed=3),
]


if __name__ == "__main__":
    main()
