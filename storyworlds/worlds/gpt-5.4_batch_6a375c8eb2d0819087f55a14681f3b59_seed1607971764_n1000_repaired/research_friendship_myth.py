#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/research_friendship_myth.py
======================================================

A standalone story world about two friends in a mythic land who use research to
understand a magical problem and mend it together.

The domain is intentionally small and constraint-checked:

- A realm offers only some places of research and some sacred remedies.
- A problem belongs to one lore family (water, sky, or growth).
- A research source is only useful when it truly knows that lore.
- A remedy is only reasonable when it matches that lore.
- Even the right remedy can arrive too late for a full bright ending.

The style stays child-facing and myth-like: moonlit places, old towers, gentle
spirits, promises, and a closing image that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/research_friendship_myth.py
    python storyworlds/worlds/gpt-5.4/research_friendship_myth.py --realm moon_vale --problem silent_river
    python storyworlds/worlds/gpt-5.4/research_friendship_myth.py --source root_library
    python storyworlds/worlds/gpt-5.4/research_friendship_myth.py --delay 2
    python storyworlds/worlds/gpt-5.4/research_friendship_myth.py --all
    python storyworlds/worlds/gpt-5.4/research_friendship_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/research_friendship_myth.py --json
    python storyworlds/worlds/gpt-5.4/research_friendship_myth.py --asp
    python storyworlds/worlds/gpt-5.4/research_friendship_myth.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "goddess"}
        male = {"boy", "man", "father", "god"}
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


@dataclass
class Realm:
    id: str
    title: str
    opening: str
    path: str
    closing: str
    sources: set[str] = field(default_factory=set)
    remedies: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    title: str
    spirit_label: str
    spirit_type: str
    sign: str
    plea: str
    lore: str
    difficulty: int
    restored: str
    partial: str
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
class Source:
    id: str
    label: str
    phrase: str
    keeper: str
    study_line: str
    clue_line: str
    knows: set[str] = field(default_factory=set)
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
class Remedy:
    id: str
    label: str
    phrase: str
    gather_line: str
    fix_line: str
    qa_fix: str
    lore: str
    power: int
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


class World:
    def __init__(self, realm: Realm) -> None:
        self.realm = realm
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"friend_a", "friend_b"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.realm)
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


def _r_affliction(world: World) -> list[str]:
    spirit = world.get("spirit")
    if spirit.meters["afflicted"] < THRESHOLD:
        return []
    sig = ("affliction", spirit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__trouble__"]


def _r_understanding(world: World) -> list[str]:
    if not world.facts.get("studied"):
        return []
    source = world.facts.get("source_cfg")
    problem = world.facts.get("problem_cfg")
    if source is None or problem is None or problem.lore not in source.knows:
        return []
    sig = ("understanding", source.id, problem.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("spirit").meters["understood"] += 1
    for kid in world.kids():
        kid.memes["hope"] += 1
    return ["__clue__"]


def _r_restoration(world: World) -> list[str]:
    if not world.facts.get("used_remedy"):
        return []
    spirit = world.get("spirit")
    remedy = world.facts.get("remedy_cfg")
    problem = world.facts.get("problem_cfg")
    if remedy is None or problem is None:
        return []
    if spirit.meters["understood"] < THRESHOLD:
        return []
    if remedy.lore != problem.lore:
        return []
    sig = ("restoration", remedy.id, problem.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    need = problem.difficulty + int(world.facts.get("delay", 0))
    if remedy.power >= need:
        spirit.meters["restored"] += 1
        spirit.meters["afflicted"] = 0.0
        for kid in world.kids():
            kid.memes["joy"] += 1
            kid.memes["friendship"] += 1
        return ["__restored__"]
    spirit.meters["partial"] += 1
    for kid in world.kids():
        kid.memes["sadness"] += 1
        kid.memes["friendship"] += 1
    return ["__partial__"]


CAUSAL_RULES = [
    Rule(name="affliction", tag="emotional", apply=_r_affliction),
    Rule(name="understanding", tag="knowledge", apply=_r_understanding),
    Rule(name="restoration", tag="physical", apply=_r_restoration),
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
        for s in produced:
            world.say(s)
    return produced


def source_matches(problem: Problem, source: Source) -> bool:
    return problem.lore in source.knows


def remedy_matches(problem: Problem, remedy: Remedy) -> bool:
    return problem.lore == remedy.lore


def valid_combo(realm: Realm, problem: Problem, source: Source, remedy: Remedy) -> bool:
    return (
        source.id in realm.sources
        and remedy.id in realm.remedies
        and source_matches(problem, source)
        and remedy_matches(problem, remedy)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for realm_id, realm in REALMS.items():
        for problem_id, problem in PROBLEMS.items():
            for source_id, source in SOURCES.items():
                for remedy_id, remedy in REMEDIES.items():
                    if valid_combo(realm, problem, source, remedy):
                        combos.append((realm_id, problem_id, source_id, remedy_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    problem = PROBLEMS[params.problem]
    remedy = REMEDIES[params.remedy]
    return "restored" if remedy.power >= problem.difficulty + params.delay else "partial"


def predict_research(world: World, source_id: str) -> dict:
    sim = world.copy()
    sim.facts["source_cfg"] = SOURCES[source_id]
    sim.facts["studied"] = True
    propagate(sim, narrate=False)
    return {
        "understood": sim.get("spirit").meters["understood"] >= THRESHOLD,
        "hope": sum(k.memes["hope"] for k in sim.kids()),
    }


def introduce(world: World, a: Entity, b: Entity, problem: Problem) -> None:
    world.say(
        f"In {world.realm.title}, where old stories were still treated like true things, "
        f"{world.realm.opening} {a.id} and {b.id} were friends who did nearly everything together."
    )
    world.say(
        f"They shared figs, secrets, and the brave feeling that comes when two children walk side by side."
    )
    world.say(problem.sign)


def spirit_plea(world: World, spirit: Entity, a: Entity, b: Entity, problem: Problem) -> None:
    spirit.meters["afflicted"] += 1
    propagate(world, narrate=False)
    world.say(
        f"From the troubled place came {spirit.label}, the {problem.spirit_label}, small and solemn. "
        f'"{problem.plea}"'
    )
    worry = "Both friends felt a pinch of worry at once." if sum(k.memes["worry"] for k in world.kids()) >= 2 else ""
    world.say(worry)


def promise_friendship(world: World, a: Entity, b: Entity) -> None:
    a.memes["loyalty"] += 1
    b.memes["loyalty"] += 1
    world.say(
        f'"Then we will help together," said {a.id}. "{b.id} can watch what I miss."'
    )
    world.say(
        f'"And {a.id} can be brave when my knees wobble," said {b.id}. They touched hands like a tiny oath.'
    )


def choose_research(world: World, a: Entity, b: Entity, source: Source) -> None:
    a.memes["impulse"] += 1
    b.memes["care"] += 1
    pred = predict_research(world, source.id)
    world.facts["predicted_understood"] = pred["understood"]
    world.say(
        f"At first {a.id} wanted to guess the answer and run ahead, because guessing is faster than waiting."
    )
    world.say(
        f'But {b.id} shook {b.pronoun("possessive")} head. "No. We need research, not guessing. Let us go to {source.phrase}."'
    )
    if pred["understood"]:
        world.say(
            f"The thought steadied them. A true clue was waiting somewhere among old words."
        )


def study(world: World, a: Entity, b: Entity, source: Source) -> None:
    world.facts["source_cfg"] = source
    world.facts["studied"] = True
    world.say(
        f"They followed {world.realm.path} to {source.phrase}, where {source.keeper} kept watch."
    )
    world.say(source.study_line)
    propagate(world, narrate=False)
    if world.get("spirit").meters["understood"] >= THRESHOLD:
        world.say(source.clue_line)
    else:
        world.say(
            f"They searched until the moon climbed higher, but nothing in that place answered the trouble before them."
        )


def setback(world: World, a: Entity, b: Entity, delay: int) -> None:
    if delay <= 0:
        return
    if delay == 1:
        world.say(
            f"Coming back, a silver mist curled over the path and slowed their steps. {b.id} nearly slipped, and {a.id} caught {b.pronoun('object')} by the sleeve."
        )
        world.say(
            f"They did not let go until the stones were steady again."
        )
        return
    world.say(
        f"But the night had grown heavy. A river of fog filled the low places, the path bent the wrong way twice, and the moon was already leaning toward dawn."
    )
    world.say(
        f"When {a.id} grew tired, {b.id} sang the smallest marching song. When {b.id} grew cold, {a.id} wrapped half a cloak around both of them."
    )


def gather(world: World, remedy: Remedy) -> None:
    world.facts["remedy_cfg"] = remedy
    world.say(remedy.gather_line)


def restore(world: World, a: Entity, b: Entity, spirit: Entity, problem: Problem, remedy: Remedy) -> None:
    world.facts["used_remedy"] = True
    propagate(world, narrate=False)
    if spirit.meters["restored"] >= THRESHOLD:
        world.say(remedy.fix_line)
        world.say(problem.restored)
        world.say(
            f"{spirit.label.capitalize()} laughed like water over stones, and the sound made both friends laugh too."
        )
    else:
        world.say(remedy.fix_line)
        world.say(problem.partial)
        world.say(
            f"{spirit.label.capitalize()} bowed anyway, because even a small healing is precious when friends bring it."
        )


def closing(world: World, a: Entity, b: Entity, spirit: Entity, outcome: str) -> None:
    if outcome == "restored":
        world.say(
            f"After that night, people said the old wonder had returned because two friends had been wiser than haste."
        )
        world.say(
            f"Whenever {a.id} and {b.id} passed, {spirit.label} lifted a bright face to them, and {world.realm.closing}"
        )
    else:
        world.say(
            f"The old wonder was not as strong as before, yet it was no longer alone in its trouble."
        )
        world.say(
            f"From then on, {a.id} and {b.id} came back often with lanterns and patient hearts, and {world.realm.closing}"
        )


def tell(
    realm: Realm,
    problem: Problem,
    source: Source,
    remedy: Remedy,
    *,
    friend_a: str = "Ira",
    friend_a_gender: str = "girl",
    friend_b: str = "Tarin",
    friend_b_gender: str = "boy",
    delay: int = 0,
) -> World:
    world = World(realm)
    a = world.add(Entity(id=friend_a, kind="character", type=friend_a_gender, label=friend_a, role="friend_a"))
    b = world.add(Entity(id=friend_b, kind="character", type=friend_b_gender, label=friend_b, role="friend_b"))
    spirit = world.add(
        Entity(
            id="spirit",
            kind="character",
            type=problem.spirit_type,
            label=problem.spirit_label,
            role="spirit",
            attrs={"problem": problem.id},
            tags=set(problem.tags),
        )
    )
    world.facts.update(
        realm=realm,
        problem_cfg=problem,
        source_cfg=None,
        remedy_cfg=None,
        delay=delay,
        studied=False,
        used_remedy=False,
        predicted_understood=False,
    )

    introduce(world, a, b, problem)
    world.para()
    spirit_plea(world, spirit, a, b, problem)
    promise_friendship(world, a, b)

    world.para()
    choose_research(world, a, b, source)
    study(world, a, b, source)
    setback(world, a, b, delay)

    world.para()
    gather(world, remedy)
    restore(world, a, b, spirit, problem, remedy)
    outcome = "restored" if spirit.meters["restored"] >= THRESHOLD else "partial"
    closing(world, a, b, spirit, outcome)

    world.facts.update(
        friend_a=a,
        friend_b=b,
        spirit=spirit,
        source_cfg=source,
        remedy_cfg=remedy,
        outcome=outcome,
        understood=spirit.meters["understood"] >= THRESHOLD,
        fully_restored=spirit.meters["restored"] >= THRESHOLD,
        friendship_grew=(a.memes["friendship"] + b.memes["friendship"]) >= 2,
    )
    return world


REALMS = {
    "moon_vale": Realm(
        id="moon_vale",
        title="Moon Vale",
        opening="silver reeds bent around a listening river",
        path="a path of shell-white stones beside the water",
        closing="the river sang their names softly under the moon.",
        sources={"shell_archive", "owl_tower"},
        remedies={"echo_pearl", "moon_thread"},
        tags={"water", "sky"},
    ),
    "cedar_peak": Realm(
        id="cedar_peak",
        title="Cedar Peak",
        opening="cedar roots held the mountain like old fingers around a cup",
        path="a stair of roots and carved lantern posts",
        closing="the orchard leaves rustled as if blessing their friendship.",
        sources={"root_library", "owl_tower"},
        remedies={"dawn_seed", "moon_thread"},
        tags={"growth", "sky"},
    ),
    "sunstep_isle": Realm(
        id="sunstep_isle",
        title="Sunstep Isle",
        opening="basalt cliffs watched a bay that kept the first light of morning",
        path="a warm cliff road painted with old sun marks",
        closing="the sea kept a gentler gleam wherever they wandered.",
        sources={"shell_archive", "root_library"},
        remedies={"echo_pearl", "dawn_seed"},
        tags={"water", "growth"},
    ),
}

PROBLEMS = {
    "silent_river": Problem(
        id="silent_river",
        title="the silent river",
        spirit_label="river sprite",
        spirit_type="spirit",
        sign="One evening they found the river moving, yet making no song at all.",
        plea="The song has fallen out of the water. Will you help me call it home?",
        lore="water",
        difficulty=2,
        restored="As soon as the remedy touched the bank, the river found its voice again and sang clear through the reeds.",
        partial="A few clear notes returned to the river, but the full song stayed thin and far away.",
        tags={"water", "song"},
    ),
    "dark_bridge": Problem(
        id="dark_bridge",
        title="the dark bridge",
        spirit_label="bridge warden",
        spirit_type="spirit",
        sign="That night the sky bridge above the valley stood dark, with no blue fire along its rails.",
        plea="Children, the bridge has forgotten its light. Will you help me wake it?",
        lore="sky",
        difficulty=1,
        restored="Blue fire ran along the bridge rails once more, and each plank shone like a strip of dawn.",
        partial="A pale glow woke along the bridge, enough for careful feet, though not enough to make the whole valley shine.",
        tags={"sky", "light"},
    ),
    "sleeping_orchard": Problem(
        id="sleeping_orchard",
        title="the sleeping orchard",
        spirit_label="orchard keeper",
        spirit_type="spirit",
        sign="Near the hill they found an orchard of star-fig trees, all still as if they had forgotten spring.",
        plea="The roots are dreaming too deeply. Will you help me wake them kindly?",
        lore="growth",
        difficulty=2,
        restored="The first leaves unfurled at once, then figs of pale gold swelled under the branches as if morning had bloomed there.",
        partial="A few leaves opened and one brave fig shone at the center tree, but the whole orchard did not wake at once.",
        tags={"growth", "tree"},
    ),
}

SOURCES = {
    "shell_archive": Source(
        id="shell_archive",
        label="shell archive",
        phrase="the Shell Archive",
        keeper="an old turtle scribe",
        study_line="Inside, shelves of spiral shells held tide-songs and water histories. The friends leaned close and traced the tiny writing with careful fingers.",
        clue_line="At last they found a shell etched with river runes, and it told them what the hurt place needed.",
        knows={"water"},
        tags={"research", "water", "archive"},
    ),
    "owl_tower": Source(
        id="owl_tower",
        label="owl tower",
        phrase="the Owl Tower",
        keeper="a white owl librarian",
        study_line="The tower windows were open to the stars. Feathers whispered over old charts while the friends turned pages bright with moon dust.",
        clue_line="On the highest table they found a sky chart whose silver marks pointed them toward the right gift.",
        knows={"sky"},
        tags={"research", "sky", "tower"},
    ),
    "root_library": Source(
        id="root_library",
        label="root library",
        phrase="the Root Library",
        keeper="a moss-robed mole sage",
        study_line="The library lay under a cedar where living roots made quiet arches. The friends read bark-scrolls and listened to the slow creak of earth wisdom.",
        clue_line="In a cracked bark-scroll they found the old answer hidden between drawings of sleeping seeds.",
        knows={"growth"},
        tags={"research", "growth", "library"},
    ),
}

REMEDIES = {
    "echo_pearl": Remedy(
        id="echo_pearl",
        label="echo pearl",
        phrase="an echo pearl",
        gather_line="Together they climbed down to a hidden pool and lifted an echo pearl from the water, carrying it in both hands so neither courage nor caution would be left out.",
        fix_line="Then they set the echo pearl where the silence hurt most.",
        qa_fix="set the echo pearl in the hurt place",
        lore="water",
        power=2,
        tags={"water", "pearl"},
    ),
    "moon_thread": Remedy(
        id="moon_thread",
        label="moon thread",
        phrase="a moon thread",
        gather_line="Together they caught a hanging strand of moon thread from the night air and wound it carefully around a willow wand.",
        fix_line="Then they drew the moon thread across the dark place, as if stitching light back into the world.",
        qa_fix="stitched the dark place with moon thread",
        lore="sky",
        power=2,
        tags={"sky", "light"},
    ),
    "dawn_seed": Remedy(
        id="dawn_seed",
        label="dawn seed",
        phrase="a dawn seed",
        gather_line="Together they found a dawn seed sleeping in warm soil beneath the oldest tree and cupped it from the wind.",
        fix_line="Then they pressed the dawn seed into the waiting earth and covered it with both their hands.",
        qa_fix="planted the dawn seed in the waiting earth",
        lore="growth",
        power=2,
        tags={"growth", "seed"},
    ),
}

GIRL_NAMES = ["Ira", "Mira", "Nela", "Suri", "Luma", "Ari", "Tala", "Nori"]
BOY_NAMES = ["Tarin", "Eren", "Pavel", "Sorin", "Kian", "Marek", "Daro", "Lio"]


@dataclass
class StoryParams:
    realm: str
    problem: str
    source: str
    remedy: str
    friend_a: str
    friend_a_gender: str
    friend_b: str
    friend_b_gender: str
    delay: int = 0
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
    "research": [
        (
            "What is research?",
            "Research means looking carefully for real answers instead of guessing. You read, ask, observe, and compare clues until something true becomes clear.",
        )
    ],
    "water": [
        (
            "Why do rivers make sounds?",
            "A river makes sounds because water bumps over stones, slides around bends, and splashes against the banks. Those little movements join together into a river song.",
        )
    ],
    "sky": [
        (
            "Why do stars and moonlight help people in stories?",
            "In many old stories, stars and moonlight help because they let travelers see in the dark and feel guided. They become signs of hope, direction, and wonder.",
        )
    ],
    "growth": [
        (
            "What helps seeds grow?",
            "Seeds need the right mix of soil, water, warmth, and time. When those things work together, the seed wakes and begins to grow.",
        )
    ],
    "friendship": [
        (
            "How can friendship help with a hard problem?",
            "A friend can notice what you miss and stay with you when the work feels long or scary. Two kind people together can be braver and wiser than one alone.",
        )
    ],
    "archive": [
        (
            "What is an archive?",
            "An archive is a place where important old things are kept safe so people can learn from them later. It can hold papers, stories, maps, shells, or other records.",
        )
    ],
    "library": [
        (
            "What is a library for?",
            "A library is for finding books and other things to read and learn from. It helps people search for answers and share knowledge.",
        )
    ],
    "tower": [
        (
            "Why do stories put wise watchers in towers?",
            "A tower gives a watcher a high place to see far away. In stories, that height can make a tower feel wise, quiet, and full of old knowledge.",
        )
    ],
    "pearl": [
        (
            "What is a pearl?",
            "A pearl is a smooth round treasure that forms inside some shells. In stories it often stands for something precious and hidden.",
        )
    ],
    "seed": [
        (
            "Why is a seed a good symbol in stories?",
            "A seed looks small, but it can hold the start of a whole plant. That makes it a good story symbol for hope, patience, and new beginnings.",
        )
    ],
    "light": [
        (
            "Why do many myths talk about light returning?",
            "Light returning shows that fear or confusion is ending. It tells us that the world is becoming safe and understandable again.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "research",
    "friendship",
    "water",
    "sky",
    "growth",
    "archive",
    "library",
    "tower",
    "pearl",
    "seed",
    "light",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["friend_a"]
    b = f["friend_b"]
    problem = f["problem_cfg"]
    source = f["source_cfg"]
    remedy = f["remedy_cfg"]
    outcome = f["outcome"]
    if outcome == "restored":
        return [
            f'Write a short myth for a 3-to-5-year-old that includes the word "research" and is about friendship, where two children solve {problem.title} by studying old clues.',
            f"Tell a gentle myth where {a.id} and {b.id} go to {source.phrase}, do research together, and use {remedy.phrase} to heal a magical place.",
            f'Write a child-facing myth in which friendship keeps two young helpers together long enough to find the true answer instead of guessing.',
        ]
    return [
        f'Write a bittersweet myth for a 3-to-5-year-old that includes the word "research" and shows friendship helping two children mend a magical trouble, even though they are a little late.',
        f"Tell a myth where {a.id} and {b.id} do research at {source.phrase}, learn the truth, and bring {remedy.phrase}, but the healing is only partly complete.",
        f'Write a simple myth with a hopeful ending where friendship matters as much as magic, because two friends keep coming back to help.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["friend_a"]
    b = f["friend_b"]
    spirit = f["spirit"]
    problem = f["problem_cfg"]
    source = f["source_cfg"]
    remedy = f["remedy_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {a.id} and {b.id}, and {spirit.label}, who asked them for help. The story follows how the friends stayed together while trying to heal {problem.title}.",
        ),
        (
            f"What problem did {a.id} and {b.id} find?",
            f"They found {problem.title}. {problem.sign.split(' they ')[-1] if ' they ' in problem.sign else problem.sign} That trouble is what called the friends into the adventure.",
        ),
        (
            "Why did they choose research instead of guessing?",
            f"They chose research because guessing might have made them rush without understanding the real hurt. By going to {source.phrase}, they hoped to find a true clue before using any magic at all.",
        ),
        (
            f"What did they learn at {source.phrase}?",
            f"They learned the clue that told them what kind of gift the troubled place needed. The research mattered because it changed them from worried helpers into informed helpers.",
        ),
        (
            f"How did friendship help them?",
            f"Friendship helped them stay brave in different ways. {a.id} wanted to move quickly, while {b.id} insisted on care, and together those two strengths kept the journey balanced.",
        ),
    ]
    if outcome == "restored":
        qa.append(
            (
                f"How did they fix {problem.title}?",
                f"They {remedy.qa_fix}. Because the remedy matched what their research had taught them, the healing worked fully and the magical place came back to life.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended brightly: {problem.restored} The ending image shows that the world truly changed, not just the children's feelings.",
            )
        )
    else:
        qa.append(
            (
                f"Did they help even though they were late?",
                f"Yes. They {remedy.qa_fix}, and some healing came back. The trouble was not fully gone, but their help still mattered because it gave the place hope and a beginning.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with only part of the wonder restored. Even so, the friends kept returning, which shows that friendship and patience can continue a healing that starts small.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"research", "friendship"} | set(f["problem_cfg"].tags) | set(f["source_cfg"].tags) | set(f["remedy_cfg"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        realm="moon_vale",
        problem="silent_river",
        source="shell_archive",
        remedy="echo_pearl",
        friend_a="Ira",
        friend_a_gender="girl",
        friend_b="Tarin",
        friend_b_gender="boy",
        delay=0,
    ),
    StoryParams(
        realm="cedar_peak",
        problem="dark_bridge",
        source="owl_tower",
        remedy="moon_thread",
        friend_a="Mira",
        friend_a_gender="girl",
        friend_b="Sorin",
        friend_b_gender="boy",
        delay=1,
    ),
    StoryParams(
        realm="sunstep_isle",
        problem="sleeping_orchard",
        source="root_library",
        remedy="dawn_seed",
        friend_a="Nela",
        friend_a_gender="girl",
        friend_b="Kian",
        friend_b_gender="boy",
        delay=2,
    ),
    StoryParams(
        realm="cedar_peak",
        problem="sleeping_orchard",
        source="root_library",
        remedy="dawn_seed",
        friend_a="Tala",
        friend_a_gender="girl",
        friend_b="Lio",
        friend_b_gender="boy",
        delay=0,
    ),
    StoryParams(
        realm="moon_vale",
        problem="dark_bridge",
        source="owl_tower",
        remedy="moon_thread",
        friend_a="Ari",
        friend_a_gender="girl",
        friend_b="Marek",
        friend_b_gender="boy",
        delay=2,
    ),
]


def explain_rejection(realm: Realm, problem: Problem, source: Source, remedy: Remedy) -> str:
    if source.id not in realm.sources:
        return f"(No story: {source.phrase} does not belong to {realm.title}, so the friends cannot do their research there.)"
    if remedy.id not in realm.remedies:
        return f"(No story: {remedy.phrase} is not a sacred gift kept in {realm.title}.)"
    if not source_matches(problem, source):
        return f"(No story: {source.phrase} does not hold lore about {problem.title}, so the research would not reveal a true clue.)"
    if not remedy_matches(problem, remedy):
        return f"(No story: {remedy.phrase} does not match the kind of hurt in {problem.title}, so it would not be a reasonable healing.)"
    return "(No story: this combination is not reasonable in the world.)"


ASP_RULES = r"""
source_matches(P,S) :- problem(P), source(S), lore_of_problem(P,L), knows(S,L).
remedy_matches(P,R) :- problem(P), remedy(R), lore_of_problem(P,L), lore_of_remedy(R,L).

valid(Realm,P,S,R) :- realm(Realm), problem(P), source(S), remedy(R),
                      offers_source(Realm,S), offers_remedy(Realm,R),
                      source_matches(P,S), remedy_matches(P,R).

need(P,N) :- chosen_problem(P), difficulty(P,D), delay(T), N = D + T.
restored  :- chosen_problem(P), chosen_remedy(R), need(P,N), power(R,PR), PR >= N.
partial   :- chosen_problem(P), chosen_remedy(R), need(P,N), power(R,PR), PR < N.

outcome(restored) :- restored.
outcome(partial)  :- partial.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for realm_id, realm in REALMS.items():
        lines.append(asp.fact("realm", realm_id))
        for source_id in sorted(realm.sources):
            lines.append(asp.fact("offers_source", realm_id, source_id))
        for remedy_id in sorted(realm.remedies):
            lines.append(asp.fact("offers_remedy", realm_id, remedy_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("lore_of_problem", problem_id, problem.lore))
        lines.append(asp.fact("difficulty", problem_id, problem.difficulty))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        for lore in sorted(source.knows):
            lines.append(asp.fact("knows", source_id, lore))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("lore_of_remedy", remedy_id, remedy.lore))
        lines.append(asp.fact("power", remedy_id, remedy.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_problem", params.problem),
            asp.fact("chosen_remedy", params.remedy),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic friendship story world: two friends use research to heal a magical trouble."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how late the friends arrive with the remedy")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and smoke-test ordinary generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.realm and args.problem and args.source and args.remedy:
        realm = REALMS[args.realm]
        problem = PROBLEMS[args.problem]
        source = SOURCES[args.source]
        remedy = REMEDIES[args.remedy]
        if not valid_combo(realm, problem, source, remedy):
            raise StoryError(explain_rejection(realm, problem, source, remedy))

    combos = [
        c
        for c in valid_combos()
        if (args.realm is None or c[0] == args.realm)
        and (args.problem is None or c[1] == args.problem)
        and (args.source is None or c[2] == args.source)
        and (args.remedy is None or c[3] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm_id, problem_id, source_id, remedy_id = rng.choice(sorted(combos))
    friend_a, friend_a_gender = _pick_name(rng)
    friend_b, friend_b_gender = _pick_name(rng, avoid=friend_a)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        realm=realm_id,
        problem=problem_id,
        source=source_id,
        remedy=remedy_id,
        friend_a=friend_a,
        friend_a_gender=friend_a_gender,
        friend_b=friend_b,
        friend_b_gender=friend_b_gender,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        realm = REALMS[params.realm]
        problem = PROBLEMS[params.problem]
        source = SOURCES[params.source]
        remedy = REMEDIES[params.remedy]
    except KeyError as err:
        raise StoryError(f"(No story: unknown parameter value {err.args[0]!r}.)") from None

    if not valid_combo(realm, problem, source, remedy):
        raise StoryError(explain_rejection(realm, problem, source, remedy))

    world = tell(
        realm=realm,
        problem=problem,
        source=source,
        remedy=remedy,
        friend_a=params.friend_a,
        friend_a_gender=params.friend_a_gender,
        friend_b=params.friend_b,
        friend_b_gender=params.friend_b_gender,
        delay=params.delay,
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


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_params.seed = 123
        smoke = generate(smoke_params)
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(smoke, trace=True, qa=True, header="### smoke")
        rendered = buf.getvalue()
        if "smoke" not in rendered or not smoke.story.strip():
            raise StoryError("smoke emit produced empty output")
        print("OK: ordinary generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (realm, problem, source, remedy) combos:\n")
        for realm, problem, source, remedy in combos:
            print(f"  {realm:12} {problem:17} {source:14} {remedy}")
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
            header = f"### {p.friend_a} & {p.friend_b}: {p.problem} in {p.realm} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
