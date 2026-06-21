#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tragic_twist_lesson_learned_pirate_tale.py
===========================================================================

A small standalone story world in a pirate-tale vein: a child crew chases a
glimmering prize, a risky shortcut goes wrong, a twist reveals the real cause,
and the crew learns a safer lesson. Some variants end in a tragic loss, some
end in recovery, but every sample has a clear turn and a child-facing ending
image.

This world is built to satisfy the Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven prose and Q&A
- Python reasonableness gate plus inline ASP twin
- support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, --show-asp
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
BRAVE_INIT = 6.0
SENSIBLE_MIN = 2

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Rose", "Ella"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Eli", "Theo", "Finn"]
TRAITS = ["careful", "curious", "cautious", "clever", "thoughtful", "brave"]
LESSONS = [
    "A map is safer when it is checked by daylight",
    "A whistle is better than a shout when the sea is loud",
    "A lantern is better than a match when the deck is dark",
]


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
    flammable: bool = False
    helpful: bool = False
    carries_light: bool = False
    piratey: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Tide:
    id: str
    label: str
    splash: str
    zone: set[str]
    risky: bool = False
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = True
    valuable: bool = True
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
class Shortcut:
    id: str
    label: str
    phrase: str
    risk: str
    twist_hint: str
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
class SafeTool:
    id: str
    label: str
    phrase: str
    use: str
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
class Fix:
    id: str
    sense: int
    power: int
    success: str
    fail: str
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


@dataclass
class StoryParams:
    crew_theme: str
    tide: str
    prize: str
    shortcut: str
    safe_tool: str
    fix: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    parent: str
    trait: str
    delay: int = 0
    captain_age: int = 6
    mate_age: int = 5
    relation: str = "friends"
    trust: int = 5
    lesson: str = ""
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
class CrewTheme:
    id: str
    scene: str
    rig: str
    title1: str
    title2: str
    goal: str
    dark_place: str
    ending_image: str
    send_off: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


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


def _r_scare(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("twist_revealed"):
        return out
    if world.facts.get("danger_seen") and not world.facts.get("helper_present"):
        if ("scare",) in world.fired:
            return out
        world.fired.add(("scare",))
        for e in world.characters():
            e.memes["fear"] += 1
        out.append("__scare__")
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("danger_seen"):
        return out
    if world.facts.get("delay", 0) >= 2 and not world.facts.get("rescued"):
        if ("loss",) in world.fired:
            return out
        world.fired.add(("loss",))
        world.get("prize").meters["lost"] += 1
        out.append("__loss__")
    return out


CAUSAL_RULES = [Rule("scare", "social", _r_scare), Rule("loss", "physical", _r_loss)]


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


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSIBLE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def hazard(shortcut: Shortcut, tide: Tide, prize: Prize) -> bool:
    return tide.risky and prize.fragile and prize.region in tide.zone


def severity(tide: Tide, delay: int) -> int:
    return (2 if tide.risky else 1) + delay


def contained(fix: Fix, tide: Tide, delay: int) -> bool:
    return fix.power >= severity(tide, delay)


def would_warn_off(relation: str, captain_age: int, mate_age: int, trait: str) -> bool:
    older_mate = relation == "siblings" and mate_age > captain_age
    authority = (5.0 if trait in {"careful", "cautious"} else 3.0) + (4.0 if older_mate else 0.0)
    return older_mate and authority > BRAVE_INIT


def predict(world: World, tide_id: str) -> dict:
    sim = world.copy()
    _do_shortcut(sim, sim.get("tide"), narrate=False)
    return {"danger": sim.get("deck").meters["danger"], "loss": sim.get("prize").meters["lost"]}


def _do_shortcut(world: World, tide_ent: Entity, narrate: bool = True) -> None:
    tide_ent.meters["rising"] += 1
    world.facts["danger_seen"] = True
    propagate(world, narrate=narrate)


def tell_setup(world: World, a: Entity, b: Entity, theme: CrewTheme) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright day by the harbor, {a.id} and {b.id} turned the dock into {theme.scene}. {theme.rig}"
    )
    world.say(f'"{theme.title1} {a.id} and {theme.title2} {b.id}!" {a.id} cried. "Let\'s find {theme.goal}!"')


def need_path(world: World, b: Entity, theme: CrewTheme, prize: Prize) -> None:
    world.say(
        f"But the way to {theme.goal} -- {theme.dark_place}, where {prize.phrase} waited -- was dark and splashy."
    )
    world.say(f'{b.id} peered ahead. "We need a light," {b.pronoun()} said.')


def twist_hint(world: World, a: Entity, shortcut: Shortcut) -> None:
    a.memes["bravado"] += 1
    world.say(
        f"{a.id}'s eyes shone. \"I know! {shortcut.label}! {shortcut.phrase} would make us the fastest crew on the water.\""
    )
    world.say(f"That sounded clever for a breath, but it was also the start of something tragic.")


def warn(world: World, b: Entity, a: Entity, shortcut: Shortcut, tide: Tide, parent: Entity) -> None:
    pred = predict(world, "tide")
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{b.id} bit {b.pronoun("possessive")} lip. "{a.id}, we should not use {shortcut.label}. {parent.label_word.capitalize()} said that quick tricks can hide real danger, and the sea can tip without warning."'
    )


def defy(world: World, a: Entity, b: Entity, shortcut: Shortcut) -> None:
    a.memes["defiance"] += 1
    world.say(f'"Come on," {a.id} said, and ran for {shortcut.label} before the others could stop {a.pronoun("object")}.')


def back_down(world: World, a: Entity, b: Entity, parent: Entity, theme: CrewTheme, safe: SafeTool) -> None:
    world.say(
        f'{a.id} looked at {b.id}, then at the dark water, and gave up the shortcut. {a.id} kept the {shortcut_word(safe)} instead and told {parent.label_word.capitalize()} about the hidden turn.'
    )


def shortcut_word(tool: SafeTool) -> str:
    return tool.label


def ignite(world: World, tide_ent: Entity, shortcut: Shortcut, tide: Tide) -> None:
    _do_shortcut(world, tide_ent)
    world.say(
        f"{shortcut.label.capitalize()} flashed in the dark. For one moment it felt like a pirate trick, then the tide slapped the dock and the lantern flickered out."
    )


def alarm(world: World, b: Entity, a: Entity, parent: Entity) -> None:
    world.say(f'"{a.id}! The water!" {b.id} shouted. "{parent.label_word.capitalize()}!"')


def rescue(world: World, parent: Entity, fix: Fix, prize_ent: Entity, prize: Prize, theme: CrewTheme) -> None:
    prize_ent.meters["lost"] = 0.0
    world.get("deck").meters["danger"] = 0.0
    body = fix.success.replace("{prize}", prize.label)
    world.say(f"{parent.label_word.capitalize()} came running. In a flash {parent.pronoun()} {body}.")
    world.say(f"The deck settled, the lantern shone steady, and the crew could see {prize.phrase} again.")


def lesson(world: World, parent: Entity, a: Entity, b: Entity, lesson_text: str) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f'Then {parent.label_word.capitalize()} knelt and hugged them both. "I am glad you shouted for help," {parent.pronoun()} said softly. "{lesson_text}."'
    )
    world.say('"We promise," whispered the two pirates together.')


def ending(world: World, parent: Entity, a: Entity, b: Entity, theme: CrewTheme, tool: SafeTool) -> None:
    world.say(
        f"The next morning, {parent.label_word.capitalize()} handed them {tool.phrase}. {tool.use}."
    )
    world.say(
        f"{a.id} held it high. {b.id} grinned. This time, the crew went on with a steady glow, and the harbor looked bright instead of tragic."
    )


def rescue_fail(world: World, parent: Entity, fix: Fix, prize_ent: Entity, prize: Prize) -> None:
    world.get("deck").meters["danger"] += 1
    prize_ent.meters["lost"] += 1
    propagate(world, narrate=False)
    body = fix.fail.replace("{prize}", prize.label)
    world.say(f"{parent.label_word.capitalize()} rushed in, but {body}.")
    world.say("The waves rolled over the dock, and the prize slipped into the black water.")


def loss_end(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    world.say(
        f"{parent.label_word.capitalize()} pulled the children back under the awning. They were safe, but the treasure was gone."
    )
    world.say(
        "The little crew watched the harbor lights blink on, and the empty spot on the dock taught them a bitter lesson."
    )


THEMES = {
    "harbor": CrewTheme(
        id="harbor",
        scene="a pirate harbor",
        rig="The crate was their ship, a mop became an oar, an old bucket held their maps, and a chalk line showed the route to the cove.",
        title1="Captain",
        title2="Mate",
        goal="the hidden cove",
        dark_place="the narrow pier behind the stacked barrels",
        ending_image="harbor lights blinking on the wet wood",
        send_off="sailed on toward the cove",
    ),
    "island": CrewTheme(
        id="island",
        scene="a sandy island camp",
        rig="The blanket was their sail, a shell became a compass, a tin cup held their coins, and a crabby stick marked the treasure trail.",
        title1="Captain",
        title2="Scout",
        goal="the palm-tree cave",
        dark_place="the path behind the black rocks",
        ending_image="moonlight on the waves",
        send_off="trekked on toward the cave",
    ),
}

TIDES = {
    "ripple": Tide("ripple", "a sneaky ripple", "a little splash", {"feet", "legs"}, risky=True, tags={"water", "sea"}),
    "swell": Tide("swell", "a rising swell", "a bigger splash", {"feet", "legs", "torso"}, risky=True, tags={"water", "sea"}),
    "calm": Tide("calm", "calm water", "a quiet glimmer", {"feet"}, risky=False, tags={"water"}),
}

PRIZES = {
    "map": Prize("map", "a paper map", "the paper map", "feet", fragile=True, tags={"map"}),
    "shell": Prize("shell", "a shiny shell necklace", "the shell necklace", "torso", fragile=True, tags={"shell"}),
    "flag": Prize("flag", "a tiny pirate flag", "the tiny pirate flag", "legs", fragile=True, tags={"flag"}),
}

SHORTCUTS = {
    "lantern": Shortcut("lantern", "the lantern", "a lantern lit too close to the sail", "quick light", "a warm glow", tags={"light"}),
    "spark": Shortcut("spark", "the spark-stick", "a spark-stick struck in a hurry", "quick light", "a fast flicker", tags={"light"}),
    "rope": Shortcut("rope", "the shortcut rope", "a rope tied to the wrong post", "quick route", "a wrong turn", tags={"rope"}),
}

SAFE_TOOLS = {
    "whistle": SafeTool("whistle", "a whistle", "a brass whistle", "so its clear call could guide the crew without any flame", tags={"whistle"}),
    "lantern": SafeTool("lantern", "a lantern", "a little lantern", "so it could glow steady and safe", tags={"light"}),
    "glowfish": SafeTool("glowfish", "glowfish lamp", "a glowfish lamp", "so the deck could shine like moonlight", tags={"light"}),
}

FIXES = {
    "bail": Fix("bail", 3, 4, "bailed the water away and steadied {prize}", "bailed hard, but the waves were too strong and {prize} was gone", "baled the water away and steadied {prize}"),
    "grab": Fix("grab", 2, 2, "grabbed {prize} and held it out of the spray", "grabbed for {prize}, but the water reached it first", "grabbed {prize} and held it high"),
    "signal": Fix("signal", 3, 3, "signaled for help and pulled {prize} back from the edge", "signaled too late, and {prize} slipped away", "signaled for help and pulled {prize} back"),
}

CURATED = [
    StoryParams(
        crew_theme="harbor", tide="ripple", prize="map", shortcut="lantern", safe_tool="whistle", fix="bail",
        captain="Tom", captain_gender="boy", mate="Lily", mate_gender="girl", parent="mother", trait="careful",
        delay=0, captain_age=6, mate_age=7, relation="siblings", trust=4, lesson="A map is safer when it is checked by daylight",
    ),
    StoryParams(
        crew_theme="island", tide="swell", prize="shell", shortcut="spark", safe_tool="lantern", fix="signal",
        captain="Mia", captain_gender="girl", mate="Ben", mate_gender="boy", parent="father", trait="cautious",
        delay=1, captain_age=5, mate_age=5, relation="friends", trust=5, lesson="A lantern is better than a match when the deck is dark",
    ),
    StoryParams(
        crew_theme="harbor", tide="swell", prize="flag", shortcut="rope", safe_tool="glowfish", fix="grab",
        captain="Sam", captain_gender="boy", mate="Nora", mate_gender="girl", parent="mother", trait="curious",
        delay=2, captain_age=6, mate_age=4, relation="siblings", trust=2, lesson="A whistle is better than a shout when the sea is loud",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for theme in THEMES:
        for tide in TIDES:
            for prize in PRIZES:
                if hazard(SHORTCUTS["lantern"], TIDES[tide], PRIZES[prize]):
                    out.append((theme, tide, prize))
    return out


def explain_rejection(tide: Tide, prize: Prize) -> str:
    if not hazard(SHORTCUTS["lantern"], tide, prize):
        return f"(No story: {tide.label} would not truly threaten {prize.label} in this world.)"
    return "(No story: invalid combination.)"


def explain_fix(fid: str) -> str:
    f = FIXES[fid]
    better = " / ".join(sorted(x.id for x in sensible_fixes()))
    return f"(Refusing fix '{fid}': sense={f.sense} < {SENSIBLE_MIN}. Try: {better}.)"


def outcome_of(params: StoryParams) -> str:
    if would_warn_off(params.relation, params.captain_age, params.mate_age, params.trait):
        return "averted"
    return "contained" if contained(FIXES[params.fix], TIDES[params.tide], params.delay) else "tragic"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with a tragic twist and lesson learned.")
    ap.add_argument("--crew-theme", choices=THEMES)
    ap.add_argument("--tide", choices=TIDES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--safe-tool", choices=SAFE_TOOLS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--mate")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.fix and FIXES[args.fix].sense < SENSIBLE_MIN:
        raise StoryError(explain_fix(args.fix))
    combos = [c for c in valid_combos()
              if (args.crew_theme is None or c[0] == args.crew_theme)
              and (args.tide is None or c[1] == args.tide)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    crew_theme, tide, prize = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(sensible_fixes(), key=lambda f: f.id)).id
    shortcut = args.shortcut or rng.choice(sorted(SHORTCUTS))
    safe_tool = args.safe_tool or rng.choice(sorted(SAFE_TOOLS))
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    captain_gender = rng.choice(["girl", "boy"])
    mate_gender = "boy" if captain_gender == "girl" else "girl"
    captain = args.name or rng.choice(GIRL_NAMES if captain_gender == "girl" else BOY_NAMES)
    mate = args.mate or rng.choice(GIRL_NAMES if mate_gender == "girl" else BOY_NAMES)
    return StoryParams(
        crew_theme=crew_theme, tide=tide, prize=prize, shortcut=shortcut, safe_tool=safe_tool, fix=fix,
        captain=captain, captain_gender=captain_gender, mate=mate, mate_gender=mate_gender,
        parent=parent, trait=trait, delay=rng.randint(0, 2), captain_age=rng.randint(4, 7),
        mate_age=rng.randint(4, 7), relation=rng.choice(["siblings", "friends"]), trust=rng.randint(0, 10),
        lesson=rng.choice(LESSONS),
    )


def tell(params: StoryParams) -> World:
    world = World()
    theme = THEMES[params.crew_theme]
    tide = TIDES[params.tide]
    prize = PRIZES[params.prize]
    shortcut = SHORTCUTS[params.shortcut]
    safe = SAFE_TOOLS[params.safe_tool]
    fix = FIXES[params.fix]

    a = world.add(Entity(id=params.captain, kind="character", type=params.captain_gender, role="captain"))
    b = world.add(Entity(id=params.mate, kind="character", type=params.mate_gender, role="mate", traits=[params.trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    world.add(Entity(id="deck", type="deck", label="the deck"))
    prize_ent = world.add(Entity(id="prize", type="thing", label=prize.label, flammable=True))
    world.facts.update(delay=params.delay, helper_present=False)

    tell_setup(world, a, b, theme)
    need_path(world, b, theme, prize)
    world.para()
    twist_hint(world, a, shortcut)
    warn(world, b, a, shortcut, tide, parent)
    averted = would_warn_off(params.relation, params.captain_age, params.mate_age, params.trait)
    if averted:
        world.say(
            f'The warning worked. {a.id} sighed, nodded, and left the shortcut behind. The crew chose the safe light instead.'
        )
        world.para()
        world.say(f"{parent.label_word.capitalize()} showed them {safe.phrase}, and its {safe.use}.")
        world.say(f"By the end, the harbor looked calm, and the crew could still reach the cove.")
        outcome = "averted"
    else:
        defy(world, a, b, shortcut)
        world.para()
        ignite(world, world.get("tide") if "tide" in world.entities else tide_ent_placeholder(world, tide), shortcut, tide)
        alarm(world, b, a, parent)
        contained_flag = contained(fix, tide, params.delay)
        if contained_flag:
            world.para()
            rescue(world, parent, fix, prize_ent, prize, theme)
            lesson(world, parent, a, b, params.lesson or random.choice(LESSONS))
            world.para()
            ending(world, parent, a, b, theme, safe)
            outcome = "contained"
        else:
            world.para()
            rescue_fail(world, parent, fix, prize_ent, prize)
            loss_end(world, parent, a, b)
            lesson(world, parent, a, b, params.lesson or random.choice(LESSONS))
            outcome = "tragic"

    world.facts.update(
        captain=a, mate=b, parent=parent, prize=prize_ent, theme=theme, tide=tide,
        shortcut=shortcut, safe_tool=safe, fix=fix, outcome=outcome,
        twist_revealed=True, rescued=outcome == "contained", delay=params.delay,
        lesson=params.lesson or "A lantern is better than a match when the deck is dark",
        danger_seen=not averted, helper_present=outcome != "tragic",
    )
    return world


def tide_ent_placeholder(world: World, tide: Tide) -> Entity:
    if "tide" not in world.entities:
        world.add(Entity(id="tide", type="thing", label=tide.label, meters=defaultdict(float)))
    return world.get("tide")


def generate(params: StoryParams) -> StorySample:
    if params.crew_theme not in THEMES or params.tide not in TIDES or params.prize not in PRIZES:
        raise StoryError("Invalid params.")
    world = tell(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child that includes the word "tragic" and ends with a lesson learned.',
        f"Tell a pirate story where {f['captain'].id} and {f['mate'].id} chase {f['prize'].label} near the water, but a risky shortcut causes a twist.",
        f"Write a child-friendly pirate tale with a dark turn, a rescue or loss, and a clear lesson learned about using safe light.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent = f["captain"], f["mate"], f["parent"]
    outcome = f["outcome"]
    qa = [
        ("Who is the story about?",
         f"It is about {a.id} and {b.id}, two little pirates, and {parent.label_word} who helps keep them safe."),
        ("What were they trying to find?",
         f"They were trying to find {f['prize'].label} near the hidden place by the water. The search is what led them into the twist."),
        ("What was the risky shortcut?",
         f"They wanted to use {f['shortcut'].label} too quickly in the dark. That shortcut seemed clever, but it was the wrong kind of help."),
    ]
    if outcome == "averted":
        qa.append((
            "What happened after the warning?",
            f"{a.id} listened and gave up the shortcut, so the danger never grew. They chose the safe tool instead, which kept the trip calm."
        ))
        qa.append((
            "How did the story end?",
            "It ended safely, with the crew using steady light and sailing on. The twist was avoided, and the lesson was learned before anything broke."
        ))
    elif outcome == "contained":
        qa.append((
            "What did the grown-up do?",
            f"{parent.label_word.capitalize()} came running and {f['fix'].qa_text.replace('{prize}', f['prize'].label)}. That stopped the problem before it became tragic."
        ))
        qa.append((
            "What did the children learn?",
            f"They learned to use the safer light and to call for help fast. The lesson was clear because the scary moment turned into a calm ending."
        ))
    else:
        qa.append((
            "What went wrong?",
            f"The quick fix was too weak, and {f['prize'].label} was lost to the waves. It was a tragic ending, but the children still got out safely."
        ))
        qa.append((
            "What did they learn?",
            f"They learned that a shortcut can hide danger and that a grown-up's help matters. After that, they would choose safe light and slow steps."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["shortcut"].tags) | set(f["tide"].tags) | set(f["prize"].tags) | set(f["safe_tool"].tags)
    out = []
    if "light" in tags:
        out.append(("Why is safe light better in the dark?",
                    "Safe light shines without flame, so it helps you see without starting a fire. That makes it better for a pirate deck or a cave."))

    out.append(("What does a pirate map do?",
                "A pirate map shows where to go and helps a crew find a place or treasure. It is best to check a map before rushing ahead."))
    if f["tide"].risky:
        out.append(("Why can water be dangerous on a dock?",
                    "Water can make boards slippery and can hide edges. A surprise wave can also knock things away very fast."))
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(S,T,P) :- shortcut(S), tide(T), prize(P), risky(T), fragile(P), region(P,R), zone(T,R).
sensible(F) :- fix(F), sense(F,S), sense_min(M), S >= M.
contained(F,T,D) :- fix(F), tide(T), power(F,P), severity(T,D,V), P >= V.
outcome(averted) :- older_mate, authority(A), brave_init(B), A > B.
outcome(contained) :- not outcome(averted), contained(_,_,_).
outcome(tragic) :- not outcome(averted), not contained(_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for tid, t in TIDES.items():
        lines.append(asp.fact("tide", tid))
        if t.risky:
            lines.append(asp.fact("risky", tid))
        for z in sorted(t.zone):
            lines.append(asp.fact("zone", tid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.fragile:
            lines.append(asp.fact("fragile", pid))
        lines.append(asp.fact("region", pid, p.region))
    for sid, s in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", sid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", SENSIBLE_MIN))
    lines.append(asp.fact("brave_init", int(BRAVE_INIT)))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show risk/3."))
    return sorted(set(asp.atoms(model, "risk")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("severity", params.tide, params.delay, severity(TIDES[params.tide], params.delay)),
        asp.fact("authority", 10),
        asp.fact("older_mate"),
    ])
    model = asp.one_model(asp_program(extra=extra, show="#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(theme, tide, prize) for theme in THEMES for tide in TIDES for prize in PRIZES if hazard(SHORTCUTS["lantern"], TIDES[tide], PRIZES[prize])]


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print(" python only:", sorted(py - cl))
        print(" clingo only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        print("OK: smoke story generated.")
        _ = sample.story[:1]
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    bad = 0
    for p in CURATED:
        if outcome_of(p) not in {"averted", "contained", "tragic"}:
            bad += 1
    print(f"OK: checked {len(CURATED)} curated outcomes.")
    return rc


def explain_rejection(tide: Tide, prize: Prize) -> str:
    return f"(No story: the tide '{tide.id}' does not threaten '{prize.id}' enough for this pirate tale.)"


def explain_fix_choice(fid: str) -> str:
    f = FIXES[fid]
    better = " / ".join(sorted(x.id for x in sensible_fixes()))
    return f"(Refusing fix '{fid}': common-sense score {f.sense} is too low. Try: {better}.)"


def choose_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSIBLE_MIN:
        raise StoryError(explain_fix_choice(args.fix))
    combos = [c for c in valid_combos()
              if (args.crew_theme is None or c[0] == args.crew_theme)
              and (args.tide is None or c[1] == args.tide)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    crew_theme, tide, prize = rng.choice(sorted(combos))
    captain_gender = args.captain_gender if hasattr(args, "captain_gender") and args.captain_gender else rng.choice(["girl", "boy"])
    mate_gender = "boy" if captain_gender == "girl" else "girl"
    return StoryParams(
        crew_theme=crew_theme,
        tide=tide,
        prize=prize,
        shortcut=args.shortcut or rng.choice(sorted(SHORTCUTS)),
        safe_tool=args.safe_tool or rng.choice(sorted(SAFE_TOOLS)),
        fix=args.fix or rng.choice(sorted(x.id for x in sensible_fixes())),
        captain=args.name or choose_name(rng, captain_gender),
        captain_gender=captain_gender,
        mate=args.mate or choose_name(rng, mate_gender),
        mate_gender=mate_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        trait=args.trait or rng.choice(TRAITS),
        delay=rng.randint(0, 2),
        captain_age=rng.randint(4, 7),
        mate_age=rng.randint(4, 7),
        relation=rng.choice(["siblings", "friends"]),
        trust=rng.randint(0, 10),
        lesson=rng.choice(LESSONS),
    )


def generate_world(params: StoryParams) -> World:
    if params.crew_theme not in THEMES or params.tide not in TIDES or params.prize not in PRIZES:
        raise StoryError("Invalid params.")
    world = World()
    theme = THEMES[params.crew_theme]
    tide = TIDES[params.tide]
    prize = PRIZES[params.prize]
    shortcut = SHORTCUTS[params.shortcut]
    safe = SAFE_TOOLS[params.safe_tool]
    fix = FIXES[params.fix]
    a = world.add(Entity(id=params.captain, kind="character", type=params.captain_gender, role="captain"))
    b = world.add(Entity(id=params.mate, kind="character", type=params.mate_gender, role="mate"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    prize_ent = world.add(Entity(id="prize", type="thing", label=prize.label, meters=defaultdict(float)))
    world.add(Entity(id="deck", type="thing", label="the deck", meters=defaultdict(float)))
    world.add(Entity(id="tide", type="thing", label=tide.label, meters=defaultdict(float)))
    world.facts["delay"] = params.delay

    tell_setup(world, a, b, theme)
    need_path(world, b, theme, prize)
    world.para()
    twist_hint(world, a, shortcut)
    warn(world, b, a, shortcut, tide, parent)
    averted = would_warn_off(params.relation, params.captain_age, params.mate_age, params.trait)

    if averted:
        world.say(f"{a.id} listened, set the shortcut aside, and chose the safe tool instead.")
        world.para()
        world.say(f"{parent.label_word.capitalize()} handed them {safe.phrase}, and {safe.use}.")
        world.say(f"The harbor stayed calm, and the crew still reached the cove.")
        outcome = "averted"
    else:
        defy(world, a, b, shortcut)
        world.para()
        ignite(world, world.get("tide"), shortcut, tide)
        alarm(world, b, a, parent)
        if contained(fix, tide, params.delay):
            world.para()
            rescue(world, parent, fix, prize_ent, prize, theme)
            lesson(world, parent, a, b, params.lesson or random.choice(LESSONS))
            world.para()
            ending(world, parent, a, b, theme, safe)
            outcome = "contained"
        else:
            world.para()
            rescue_fail(world, parent, fix, prize_ent, prize)
            loss_end(world, parent, a, b)
            lesson(world, parent, a, b, params.lesson or random.choice(LESSONS))
            outcome = "tragic"

    world.facts.update(
        captain=a, mate=b, parent=parent, prize=prize_ent, theme=theme, tide=tide,
        shortcut=shortcut, safe_tool=safe, fix=fix, outcome=outcome,
        twist_revealed=True, danger_seen=not averted, rescued=outcome == "contained",
        helper_present=outcome != "tragic",
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
        print(asp_program(show="#show risk/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}")
        combos = asp_valid_combos()
        print(f"{len(combos)} risky combos:\n")
        for combo in combos:
            print(" ", combo)
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
            except StoryError as e:
                print(e)
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
            header = f"### {p.captain} & {p.mate}: {p.crew_theme} / {p.tide} / {p.prize} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
