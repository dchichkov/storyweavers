#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/caboose_messenger_tidal_pool_foreshadowing_kindness_mystery.py
===============================================================================================

A standalone storyworld for a tiny mystery set at a tidal pool.

Premise:
- A child explorer at a tidal pool notices an odd message from a messenger.
- Clues foreshadow a hidden problem around the caboose.
- Kindness helps the characters share information, solve the mystery, and end
  with a small, bright image that proves the change.

The simulation is state-driven: physical meters track clues, tide, and discovered
objects; emotional memes track worry, curiosity, and kindness. The renderer
turns the state transitions into child-facing prose.

Supports:
- default run
- -n, --all, --seed, --trace, --qa, --json
- --asp, --verify, --show-asp
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
EVIDENCE_MIN = 2
TIDE_WARN_LEVEL = 2
TIDE_DANGER_LEVEL = 3


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
    tags: set[str] = field(default_factory=set)

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
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def _r_tide_rises(world: World) -> list[str]:
    out: list[str] = []
    tide = world.get("tide")
    if tide.meters["level"] < TIDE_WARN_LEVEL:
        return out
    sig = ("tide_rises", int(tide.meters["level"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.role == "messenger":
            e.memes["worry"] += 1
        if e.role == "child":
            e.memes["curiosity"] += 1
    out.append("__tide__")
    return out


def _r_footprints(world: World) -> list[str]:
    out: list[str] = []
    if world.get("clue").meters["seen"] < THRESHOLD:
        return out
    sig = ("footprints",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("clue").meters["evidence"] += 1
    out.append("The wet sand held a clue-shaped print near the rocks.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    rules = [Rule("tide", _r_tide_rises), Rule("footprints", _r_footprints)]
    while changed:
        changed = False
        for rule in rules:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    setting: str
    style: str
    feature1: str
    feature2: str
    hero: str
    hero_gender: str
    messenger: str
    messenger_gender: str
    caboose: str
    tide_level: int = 1
    clue_kind: str = "shell"
    scenario: str = "missing_logbook"
    opening_variant: int = 0
    investigation_variant: int = 0
    kindness_variant: int = 0
    ending_variant: int = 0
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


SETTINGS = {
    "tidal_pool": {
        "place": "the tidal pool",
        "scene": "a quiet cove with shiny rocks and little pools of water",
        "dark_spot": "the far rocks where the water slipped in and out",
    }
}

FEATURES = {"foreshadowing": "foreshadowing", "kindness": "kindness"}
STYLES = {"mystery": "mystery"}

HERO_NAMES = ["Mira", "Nina", "Owen", "Tess", "Arlo", "Ivy", "Jun", "Lena"]
MESSENGER_NAMES = ["Pip", "Wren", "Rowan", "Bea", "Moss", "June", "Rae", "Kit"]
CABOOSE_NAMES = ["Caboose", "the caboose", "old caboose"]

SCENARIOS = {
    "missing_logbook": {
        "oddity": "the nature logbook was gone and its empty strap tapped the wall",
        "message": "The last page is still telling us where it went",
        "sign": "a line of damp paper flecks led away from the door",
        "cause": "a gust had lifted the unfastened logbook from the nature station",
        "solution": "They followed the paper flecks from the dry path and found the logbook wedged beneath the boardwalk ramp",
        "proof": "The messenger buckled the logbook into its strap, and its pages lay flat beneath the caboose window",
    },
    "silent_bell": {
        "oddity": "the caboose's warning bell had stopped ringing before the incoming tide",
        "message": "Something small has silenced the bell, but nothing should be pulled from a pool",
        "sign": "a loose blue cord made a wavy mark across the dry gravel",
        "cause": "wind had slipped the bell cord off its hook and wrapped it around a railing post",
        "solution": "They traced the cord along the gravel and, from the boardwalk, looped it back over its painted hook",
        "proof": "One clear bell note floated over the pools while the cord hung safely above the rocks",
    },
    "mixed_markers": {
        "oddity": "the colored tide markers beside the caboose were in the wrong order",
        "message": "Read the colors from the shadows, not from where the pieces landed",
        "sign": "three clean rectangles showed where signs had blocked the morning sun",
        "cause": "a night wind had knocked the removable markers onto the station deck",
        "solution": "They matched each marker to its sun-pale rectangle without stepping off the deck",
        "proof": "The markers made a neat green-yellow-red row, and the red one gleamed above the rising water",
    },
    "mystery_knock": {
        "oddity": "a hollow knock came from the caboose whenever the cove grew quiet",
        "message": "Count the knocks and watch what moves between them",
        "sign": "a narrow shadow swung across the same patch of gravel after every third knock",
        "cause": "the wind was swinging a loose wooden tide ruler against the caboose",
        "solution": "They timed the knocks, spotted the ruler from the viewing rail, and asked the ranger to tighten its top hinge",
        "proof": "The ruler stood still beside the caboose, and the next quiet moment held only wave sounds",
    },
    "vanishing_flags": {
        "oddity": "two orange safety flags had vanished from their rack on the caboose",
        "message": "The flags did not go toward the water; look where the wind had to turn",
        "sign": "orange threads clung to a splinter on the landward fence",
        "cause": "a strong breeze had carried the flags inland behind the visitor bench",
        "solution": "They searched the landward side and found both flags folded together under the bench",
        "proof": "Both flags fluttered from the caboose rack, pointing visitors toward the safe overlook",
    },
    "covered_map": {
        "oddity": "the caboose map showed every pool except the one marked for today's observation",
        "message": "The missing pool has not moved; a newer clue is lying over it",
        "sign": "one corner of the map looked twice as thick and smelled faintly of fresh paste",
        "cause": "a new visitor notice had accidentally been pasted over part of the tide-pool map",
        "solution": "They compared the map with the shore from the overlook, then asked the ranger to lift the notice with a safe paper tool",
        "proof": "The restored map showed the little pool again, with a bright circle around the no-touch viewing spot",
    },
}

CURATED = [
    StoryParams(
        setting="tidal_pool",
        style="mystery",
        feature1="foreshadowing",
        feature2="kindness",
        hero="Mira",
        hero_gender="girl",
        messenger="Pip",
        messenger_gender="boy",
        caboose="old caboose",
        tide_level=3,
        clue_kind="shell",
    ),
    StoryParams(
        setting="tidal_pool",
        style="mystery",
        feature1="kindness",
        feature2="foreshadowing",
        hero="Owen",
        hero_gender="boy",
        messenger="Wren",
        messenger_gender="girl",
        caboose="caboose",
        tide_level=2,
        clue_kind="rope",
    ),
]


def valid_combos() -> list[tuple[str, int]]:
    combos = []
    for setting in SETTINGS:
        for level in range(1, 4):
            combos.append((setting, level))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Storyworld: a tidal-pool mystery with kindness and foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--style", choices=STYLES)
    ap.add_argument("--feature1", choices=FEATURES)
    ap.add_argument("--feature2", choices=FEATURES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--messenger")
    ap.add_argument("--messenger-gender", choices=["girl", "boy"])
    ap.add_argument("--caboose")
    ap.add_argument("--tide-level", type=int, choices=[1, 2, 3])
    ap.add_argument("--clue-kind", choices=["shell", "rope", "key", "map"])
    ap.add_argument("--scenario", choices=SCENARIOS)
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
    setting = args.setting or "tidal_pool"
    style = args.style or "mystery"
    f1 = args.feature1 or "foreshadowing"
    f2 = args.feature2 or "kindness"
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    messenger_gender = args.messenger_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(HERO_NAMES)
    messenger = args.messenger or rng.choice([n for n in MESSENGER_NAMES if n != hero])
    caboose = args.caboose or rng.choice(CABOOSE_NAMES)
    tide_level = args.tide_level or rng.choice([1, 2, 3])
    clue_kind = args.clue_kind or rng.choice(["shell", "rope", "key", "map"])
    return StoryParams(setting=setting, style=style, feature1=f1, feature2=f2, hero=hero,
                       hero_gender=hero_gender, messenger=messenger, messenger_gender=messenger_gender,
                       caboose=caboose, tide_level=tide_level, clue_kind=clue_kind)


def _make_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Only the tidal-pool setting is supported.")
    if params.style != "mystery":
        raise StoryError("This world keeps a mystery style.")
    if {params.feature1, params.feature2} != {"foreshadowing", "kindness"}:
        raise StoryError("This storyworld needs foreshadowing and kindness.")
    if params.tide_level not in (1, 2, 3):
        raise StoryError("The tide level must be 1, 2, or 3.")
    w = World()
    hero = w.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="child"))
    messenger = w.add(Entity(id=params.messenger, kind="character", type=params.messenger_gender, role="messenger"))
    caboose_label = params.caboose
    if caboose_label in {"caboose", "old caboose"}:
        caboose_label = f"the {caboose_label}"
    caboose = w.add(Entity(id="caboose", kind="thing", type="thing", label=caboose_label))
    tide = w.add(Entity(id="tide", kind="thing", type="thing", label="tide"))
    clue = w.add(Entity(id="clue", kind="thing", type="thing", label=params.clue_kind))
    tide.meters["level"] = float(params.tide_level)
    clue.meters["seen"] = 0.0
    clue.meters["evidence"] = 0.0
    hero.memes["curiosity"] = 1.0
    messenger.memes["worry"] = 0.0
    w.facts.update(params=params, hero=hero, messenger=messenger, caboose=caboose, tide=tide, clue=clue)
    return w


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    messenger: Entity = f["messenger"]
    caboose: Entity = f["caboose"]
    tide: Entity = f["tide"]
    clue: Entity = f["clue"]
    params: StoryParams = f["params"]
    plot = SCENARIOS[params.scenario]
    openings = [
        f"At the morning low tide, {hero.id} followed the tidal pool boardwalk to {caboose.label_word}, a retired rail car now used as a shore nature station.",
        f"Cloud shadows crossed the tidal pool when {hero.id} reached {caboose.label_word}, the bright little nature station above the high-water line.",
        f"From the safe tidal pool overlook, {hero.id} watched anemones fold and tiny fish flash while {caboose.label_word} waited on the gravel behind the rail.",
        f"The tidal pool cove smelled of salt when {hero.id} arrived at {caboose.label_word}, where visitors recorded what they saw without touching the pools.",
    ]
    tide_hints = [
        "A wet line was already climbing the lowest rock, a quiet hint that there would not be forever to investigate.",
        "Farther out, a gull hopped away from a rock just before a wave washed over it.",
        "The ranger's tide clock clicked one mark higher, and silver water filled a crack below.",
        "A ribbon of foam curled around the seaward stones, then returned a little closer than before.",
    ]
    investigations = [
        f"They crouched on the dry path and compared the {clue.label_word} clue with the station map instead of picking up anything living.",
        f"They took a photograph of the {clue.label_word} clue and enlarged it on the messenger's screen, leaving the pool exactly as they found it.",
        f"Using the viewing rail as a boundary, they looked from the {clue.label_word} clue to the caboose and searched for a repeating shape.",
        f"They sketched the {clue.label_word} clue in a notebook, then checked which direction its marks pointed from the boardwalk.",
    ]
    kindness_beats = [
        (f"{messenger.id}'s words tumbled together, so {hero.id} waited, offered a dry towel, and let the messenger begin again.",
         f'"Thank you for listening," {messenger.id} said. "Here is the part I was afraid I had spoiled."'),
        (f"When {messenger.id} admitted losing track of the clue, {hero.id} said that mistakes were easier to solve when nobody had to hide them.",
         f'"Then I can show you my whole message," {messenger.id} said, smoothing the damp paper.'),
        (f"{hero.id} noticed {messenger.id} shivering and shared the sheltered side of the caboose before asking another question.",
         f'"I remember one more detail now," {messenger.id} said. "It happened when the wind changed."'),
        (f"Instead of grabbing the message, {hero.id} held out a notebook and asked {messenger.id} to draw the clue at a comfortable pace.",
         f'"That helps," {messenger.id} said. "The strange part was beside the caboose, not inside a pool."'),
    ]
    endings = [
        "In the last light, a bead of seawater shone below the boardwalk while the solved clue stayed safe and dry above it.",
        "As they left, a tiny fish crossed the pool's reflection and the caboose window answered with one warm square of light.",
        "The next wave filled the pool without carrying away a single shell, sign, or secret.",
        "Behind them, the caboose cast a tidy red reflection, and every creature in the pool remained undisturbed.",
    ]

    world.say(openings[params.opening_variant % len(openings)])
    world.say(f"Something was wrong: {plot['oddity']}.")
    world.say(tide_hints[(params.opening_variant + params.ending_variant) % len(tide_hints)])

    world.para()
    world.say(f"A messenger named {messenger.id} hurried up the path with a damp note. \"{plot['message']},\" {messenger.id} read.")
    clue.meters["seen"] = 1.0
    world.say(f"Near the caboose, {plot['sign']}. Beside it was the {clue.label_word} symbol from the note.")
    world.say(investigations[params.investigation_variant % len(investigations)])
    propagate(world)

    world.para()
    messenger.memes["kindness"] = 1.0
    hero.memes["kindness"] = 1.0
    kind_action, kind_reply = kindness_beats[params.kindness_variant % len(kindness_beats)]
    world.say(kind_action)
    world.say(kind_reply)
    world.say(f"That small kindness gave {messenger.id} time to remember the missing detail.")
    world.say(f"Now the early hint made sense: {plot['cause']}.")
    world.say("The odd detail had quietly foreshadowed the answer without giving the mystery away.")

    world.para()
    clue.meters["evidence"] += 1
    world.say(f"{plot['solution']}. They never entered a pool or moved a shell or animal.")
    world.say(f"{plot['proof']}.")
    world.say(f'"Mystery solved," {hero.id} said. "And nothing here had to be harmed to solve it."')
    world.say(endings[params.ending_variant % len(endings)])
    world.facts.update(
        mystery_oddity=plot["oddity"],
        mystery_sign=plot["sign"],
        mystery_cause=plot["cause"],
        mystery_solution=plot["solution"],
        mystery_proof=plot["proof"],
        kindness_action=kind_action,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    messenger: Entity = f["messenger"]
    caboose: Entity = f["caboose"]
    return [
        QAItem(
            question="What was the story about?",
            answer=f"It was about {hero.id} and a messenger named {messenger.id} investigating why {f['mystery_oddity']}. They solved the mystery near {caboose.label_word} by studying clues and trusting each other."
        ),
        QAItem(
            question="How did the early clue foreshadow the answer?",
            answer=f"The early clue was that {f['mystery_sign']}. It pointed toward the later discovery that {f['mystery_cause']}."
        ),
        QAItem(
            question="How did kindness help?",
            answer=f"{f['kindness_action']} That kindness helped {messenger.id} share the missing detail, so the two children could reason from the complete message."
        ),
        QAItem(
            question="What proved that the mystery was solved?",
            answer=f"{f['mystery_solution']}. The visible proof was that {f['mystery_proof']}."
        ),
        QAItem(
            question="How did the children protect the tidal pool?",
            answer="They investigated from the dry path, boardwalk, or viewing rail and did not enter the pools. They left shells and animals where they were and asked a ranger for help when a repair needed tools."
        ),
    ]


def prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    messenger: Entity = f["messenger"]
    caboose: Entity = f["caboose"]
    return [
        f"Write a child-friendly mystery story set at a tidal pool with foreshadowing and kindness, and include the words caboose and messenger.",
        f"Tell a short mystery where {hero.id} follows a clue from a messenger and learns what is hidden near {caboose.label_word}.",
        f"Write a story about a tidal pool, a waiting caboose, and a kind messenger whose warning makes the puzzle clearer.",
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tidal pool?",
            answer="A tidal pool is a small pool of seawater left behind near the shore when the tide goes out. It can change as the water moves in and out."
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small hint about something important that will matter later. It helps readers notice clues before the answer arrives."
        ),
        QAItem(
            question="Why is kindness useful in a mystery?",
            answer="Kindness helps people trust each other and share clues. When someone feels safe, they are more likely to explain what they know."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    try:
        world = _make_world(params)
    except KeyError as exc:
        raise StoryError(f"Invalid parameter key: {exc}") from exc
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "tidal_pool"),
        asp.fact("style", "mystery"),
        asp.fact("feature", "foreshadowing"),
        asp.fact("feature", "kindness"),
        asp.fact("tide_level", 1),
        asp.fact("tide_level", 2),
        asp.fact("tide_level", 3),
        asp.fact("warn_level", TIDE_WARN_LEVEL),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S) :- setting(S), S = tidal_pool.
mystery_style(mystery).
feature_ok(foreshadowing).
feature_ok(kindness).
story_ok :- compatible(tidal_pool), mystery_style(mystery), feature_ok(foreshadowing), feature_ok(kindness).
rising_tide(L) :- tide_level(L), warn_level(M), L >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_compatible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show compatible/1."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    py = {"tidal_pool"}
    clingo = {s[0] for s in asp_compatible()}
    if py == clingo:
        print("OK: ASP compatibility matches Python.")
    else:
        print("MISMATCH: compatibility differs.")
        rc = 1

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_valid_combos() -> list[tuple[str, int]]:
    return valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or "tidal_pool"
    style = args.style or "mystery"
    feature1 = args.feature1 or "foreshadowing"
    feature2 = args.feature2 or "kindness"
    hero = args.hero or rng.choice(HERO_NAMES)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    messenger = args.messenger or rng.choice([n for n in MESSENGER_NAMES if n != hero])
    messenger_gender = args.messenger_gender or rng.choice(["girl", "boy"])
    caboose = args.caboose or rng.choice(CABOOSE_NAMES)
    tide_level = args.tide_level or rng.choice([1, 2, 3])
    clue_kind = args.clue_kind or rng.choice(["shell", "rope", "key", "map"])
    scenario = args.scenario or rng.choice(list(SCENARIOS))
    if setting != "tidal_pool":
        raise StoryError("Only tidal_pool is valid in this storyworld.")
    if style != "mystery":
        raise StoryError("Only mystery style is supported.")
    return StoryParams(
        setting=setting,
        style=style,
        feature1=feature1,
        feature2=feature2,
        hero=hero,
        hero_gender=hero_gender,
        messenger=messenger,
        messenger_gender=messenger_gender,
        caboose=caboose,
        tide_level=tide_level,
        clue_kind=clue_kind,
        scenario=scenario,
        opening_variant=rng.randrange(4),
        investigation_variant=rng.randrange(4),
        kindness_variant=rng.randrange(4),
        ending_variant=rng.randrange(4),
    )


def valid_combos() -> list[tuple[str, int]]:
    return [("tidal_pool", level) for level in (1, 2, 3)]


def generation_sample(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show compatible/1.\n#show rising_tide/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible settings: tidal_pool")
        print("tide levels:", ", ".join(str(n) for n in (1, 2, 3)))
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


if __name__ == "__main__":
    main()
