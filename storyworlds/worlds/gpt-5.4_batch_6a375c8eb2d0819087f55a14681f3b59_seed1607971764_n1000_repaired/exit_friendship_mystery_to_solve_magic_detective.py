#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/exit_friendship_mystery_to_solve_magic_detective.py
=============================================================================

A standalone storyworld about two child detectives in a magical place where the
way out seems to disappear. The central mystery is small and concrete: the exit
is not truly gone, but hidden by a spell side effect. A helper tool and a
friend's patience solve the case.

Run it
------
    python storyworlds/worlds/gpt-5.4/exit_friendship_mystery_to_solve_magic_detective.py
    python storyworlds/worlds/gpt-5.4/exit_friendship_mystery_to_solve_magic_detective.py --place observatory --clue glitter_dust
    python storyworlds/worlds/gpt-5.4/exit_friendship_mystery_to_solve_magic_detective.py --cause giant_sleeping_cat
    python storyworlds/worlds/gpt-5.4/exit_friendship_mystery_to_solve_magic_detective.py --all
    python storyworlds/worlds/gpt-5.4/exit_friendship_mystery_to_solve_magic_detective.py --qa --json
    python storyworlds/worlds/gpt-5.4/exit_friendship_mystery_to_solve_magic_detective.py --verify
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
HELPFUL_MIN = 2


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Place:
    id: str
    label: str
    opening: str
    nook: str
    ending: str
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
class Cause:
    id: str
    label: str
    clue_line: str
    reveal_line: str
    danger: str
    solved_by: set[str] = field(default_factory=set)
    hidden_exit: bool = True
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
class Clue:
    id: str
    label: str
    discovery: str
    meaning: str
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
class Tool:
    id: str
    label: str
    action: str
    helpful: int
    works_on: set[str] = field(default_factory=set)
    qa_text: str = ""
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


def _r_hidden_exit(world: World) -> list[str]:
    hall = world.get("hall")
    if hall.meters["confusion"] < THRESHOLD:
        return []
    sig = ("hidden_exit",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hall.meters["exit_hidden"] += 1
    for kid in world.facts["kids"]:
        kid.memes["worry"] += 1
    return ["__hidden__"]


def _r_two_clues_make_theory(world: World) -> list[str]:
    hall = world.get("hall")
    if hall.meters["clues_found"] < 2:
        return []
    sig = ("theory",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hall.meters["theory_ready"] += 1
    for kid in world.facts["kids"]:
        kid.memes["hope"] += 1
    return ["__theory__"]


def _r_solve(world: World) -> list[str]:
    hall = world.get("hall")
    if hall.meters["theory_ready"] < THRESHOLD:
        return []
    if hall.meters["spell_lifted"] >= THRESHOLD:
        return []
    if hall.meters["tool_strength"] < THRESHOLD:
        return []
    sig = ("solve",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hall.meters["spell_lifted"] += 1
    hall.meters["exit_hidden"] = 0.0
    hall.meters["safe_path"] += 1
    for kid in world.facts["kids"]:
        kid.memes["relief"] += 1
        kid.memes["trust"] += 1
    return ["__solved__"]


CAUSAL_RULES = [
    Rule(name="hidden_exit", tag="physical", apply=_r_hidden_exit),
    Rule(name="theory", tag="mental", apply=_r_two_clues_make_theory),
    Rule(name="solve", tag="physical", apply=_r_solve),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(s for s in produced if not s.startswith("__"))
    if narrate:
        for line in out:
            world.say(line)
    return out


def cause_reasonable(cause: Cause, tool: Tool) -> bool:
    return cause.hidden_exit and tool.id in cause.solved_by and tool.helpful >= HELPFUL_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for cause_id, cause in CAUSES.items():
            for clue_id in CLUES:
                for tool_id, tool in TOOLS.items():
                    if cause_reasonable(cause, tool):
                        combos.append((place_id, cause_id, clue_id, tool_id))
    return combos


def explain_rejection(cause: Cause, tool: Tool) -> str:
    if tool.helpful < HELPFUL_MIN:
        return (
            f"(No story: {tool.label} is known in the world, but it is too weak or "
            f"unhelpful for this mystery. A detective story here needs a tool that can "
            f"honestly reveal the hidden exit.)"
        )
    if tool.id not in cause.solved_by:
        return (
            f"(No story: {tool.label} does not solve the spell caused by {cause.label}. "
            f"Pick a tool that can really uncover the hidden exit.)"
        )
    return "(No story: this combination does not produce a workable hidden-exit mystery.)"


def investigate_with(world: World, clue: Clue) -> None:
    hall = world.get("hall")
    hall.meters["clues_found"] += 1
    world.facts.setdefault("clue_hits", []).append(clue.id)
    propagate(world, narrate=False)


def opening(world: World, a: Entity, b: Entity, place: Place) -> None:
    for kid in world.facts["kids"]:
        kid.memes["joy"] += 1
    world.say(
        f"After school, {a.id} and {b.id} visited {place.label}. "
        f"{place.opening}"
    )
    world.say(
        f"They liked pretending they were detective partners. {a.id} carried a tiny notebook, "
        f"and {b.id} liked spotting the small things other people missed."
    )


def mystery_appears(world: World, a: Entity, b: Entity, place: Place) -> None:
    hall = world.get("hall")
    hall.meters["confusion"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When they finished exploring {place.nook}, they turned to go home. "
        f"But the bright sign that should have pointed to the exit was gone."
    )
    world.say(
        f'"That is a real mystery," {a.id} whispered. "{place.label} is not supposed to lose its exit."'
    )


def friendship_beat(world: World, a: Entity, b: Entity) -> None:
    b.memes["care"] += 1
    a.memes["care"] += 1
    world.say(
        f'{b.id} slipped {b.pronoun("possessive")} hand into {a.id}\'s and said, '
        f'"We will solve it together. Detectives do not leave friends alone with a puzzle."'
    )


def find_first_clue(world: World, a: Entity, clue: Clue, cause: Cause) -> None:
    investigate_with(world, clue)
    world.say(
        f"{a.id} knelt by the floor and found {clue.discovery}. "
        f'"Look," {a.pronoun()} said. "{clue.meaning}"'
    )
    world.say(cause.clue_line)


def find_second_clue(world: World, b: Entity, cause: Cause) -> None:
    hall = world.get("hall")
    hall.meters["clues_found"] += 1
    world.facts.setdefault("clue_hits", []).append("scene_mark")
    propagate(world, narrate=False)
    world.say(
        f"{b.id} studied the air, then pointed at the wall. "
        f'Tiny silver curls of magic were drifting in one corner instead of by the door.'
    )
    world.say(
        f'"The spell slid sideways," {b.id} said. "Something tugged the exit sign away from where it belongs."'
    )
    world.facts["second_clue_text"] = cause.reveal_line


def theory(world: World, a: Entity, b: Entity, cause: Cause) -> None:
    world.say(
        f"The two friends put their clues together. {a.id} tapped the notebook, and "
        f"{b.id} looked at the sparkling corner one more time."
    )
    world.say(
        f'"I know," {a.id} said. "{cause.reveal_line}"'
    )


def solve_spell(world: World, a: Entity, b: Entity, tool: Tool, place: Place) -> None:
    hall = world.get("hall")
    hall.meters["tool_strength"] += tool.helpful
    propagate(world, narrate=False)
    world.say(
        f"Very carefully, {a.id} and {b.id} used {tool.label}. "
        f"{tool.action}"
    )
    world.say(
        f"At once the wall shimmered. A gold arrow blinked, the word exit glowed again, "
        f"and a safe doorway opened exactly where it should have been."
    )
    world.say(place.ending)


def closing(world: World, a: Entity, b: Entity) -> None:
    for kid in world.facts["kids"]:
        kid.memes["pride"] += 1
    world.say(
        f'Outside, {a.id} grinned at {b.id}. "Case solved," {a.pronoun()} said.'
    )
    world.say(
        f'{b.id} grinned back. "Best part?" {b.pronoun().capitalize()} asked. '
        f'"We found the way out because we were good friends first, and good detectives second."'
    )


def tell(
    place: Place,
    cause: Cause,
    clue: Clue,
    tool: Tool,
    detective_a: str = "Nora",
    detective_a_gender: str = "girl",
    detective_b: str = "Eli",
    detective_b_gender: str = "boy",
    trait_a: str = "careful",
    trait_b: str = "patient",
) -> World:
    world = World()
    a = world.add(Entity(
        id=detective_a,
        kind="character",
        type=detective_a_gender,
        role="lead",
        traits=[trait_a],
    ))
    b = world.add(Entity(
        id=detective_b,
        kind="character",
        type=detective_b_gender,
        role="partner",
        traits=[trait_b],
    ))
    hall = world.add(Entity(id="hall", type="hall", label=place.label))
    hall.meters["confusion"] = 0.0
    hall.meters["clues_found"] = 0.0
    hall.meters["theory_ready"] = 0.0
    hall.meters["tool_strength"] = 0.0
    hall.meters["spell_lifted"] = 0.0
    hall.meters["exit_hidden"] = 0.0
    hall.meters["safe_path"] = 0.0
    world.facts["kids"] = [a, b]
    world.facts["place"] = place
    world.facts["cause"] = cause
    world.facts["clue"] = clue
    world.facts["tool"] = tool
    world.facts["clue_hits"] = []
    world.facts["second_clue_text"] = ""

    opening(world, a, b, place)
    world.para()
    mystery_appears(world, a, b, place)
    friendship_beat(world, a, b)
    world.para()
    find_first_clue(world, a, clue, cause)
    find_second_clue(world, b, cause)
    theory(world, a, b, cause)
    world.para()
    solve_spell(world, a, b, tool, place)
    closing(world, a, b)

    world.facts.update(
        detective_a=a,
        detective_b=b,
        hidden=hall.meters["exit_hidden"] < THRESHOLD and hall.meters["spell_lifted"] >= THRESHOLD,
        solved=hall.meters["spell_lifted"] >= THRESHOLD,
        escape=hall.meters["safe_path"] >= THRESHOLD,
    )
    return world


PLACES = {
    "library": Place(
        id="library",
        label="the Moonberry Library",
        opening="Tall shelves curved like moonlight, and the lamps hummed with soft blue magic.",
        nook="the whispering atlas room",
        ending="The children stepped through the doorway into the sunny front hall, where the librarian gave them a surprised but proud smile.",
        tags={"library", "magic_place"},
    ),
    "observatory": Place(
        id="observatory",
        label="the Star Clock Observatory",
        opening="Round windows showed the evening sky, and tiny constellations drifted over the floor like sleepy fireflies.",
        nook="the spinning map chamber",
        ending="They came out beside the brass telescope, and the keeper of the observatory bowed as if the young detectives had solved an important case.",
        tags={"observatory", "magic_place"},
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="the Fernbell Greenhouse",
        opening="Glass walls shone with green light, and floating seed-lanterns bobbed over winding paths.",
        nook="the fern tunnel",
        ending="They walked back into the warm main path while a row of flowers slowly turned their bright faces toward them.",
        tags={"greenhouse", "magic_place"},
    ),
}

CAUSES = {
    "sneezy_sprite": Cause(
        id="sneezy_sprite",
        label="a sneezy sprite",
        clue_line="Near the baseboard lay a pearl-bright feather and a sprinkle of glittery dust, just the kind little sprites leave behind when they sneeze magic the wrong way.",
        reveal_line="A sprite must have sneezed, and the spell pushed the sign behind a shimmer instead of keeping it above the door.",
        danger="The children could wander in circles if they guessed instead of solving the clue.",
        solved_by={"echo_lens", "kind_rhyme"},
        tags={"sprite", "magic"},
    ),
    "mixed_up_broom": Cause(
        id="mixed_up_broom",
        label="a mixed-up sweeping broom",
        clue_line="A ribbon of sparkling sweep-marks curved across the tiles, as if an enchanted broom had polished the wall and the sign into the same shiny blur.",
        reveal_line="A cleaning broom must have swept the magic too hard and brushed the exit sign out of sight.",
        danger="The wrong hallway would only lead them deeper into the building.",
        solved_by={"echo_lens", "chalk_compass"},
        tags={"broom", "magic"},
    ),
    "giant_sleeping_cat": Cause(
        id="giant_sleeping_cat",
        label="a giant sleeping cat",
        clue_line="On a windowsill they found a silver whisker as long as a ribbon. Only the greenhouse cat, Misty, shed whiskers like that when she slept under spell-lamps.",
        reveal_line="Misty's dream-magic must have curled over the doorway and hidden the sign under a sleepy shimmer.",
        danger="If they tiptoed the wrong way, they might wake the cat and make the hallway even twistier.",
        solved_by={"kind_rhyme", "chalk_compass"},
        tags={"cat", "magic"},
    ),
}

CLUES = {
    "glitter_dust": Clue(
        id="glitter_dust",
        label="glitter dust",
        discovery="a dusting of glitter that sparkled even in the shadows",
        meaning="Magic drifted this way first. Something small made the trouble, not the whole building.",
        tags={"glitter", "clue"},
    ),
    "silver_whisker": Clue(
        id="silver_whisker",
        label="a silver whisker",
        discovery="a silver whisker caught under a cracked tile",
        meaning="A magical creature brushed past here, and the spell bent with it.",
        tags={"whisker", "clue"},
    ),
    "sweeping_marks": Clue(
        id="sweeping_marks",
        label="sweeping marks",
        discovery="curved sweeping marks that shone brighter than the rest of the floor",
        meaning="The magic was moved, almost like someone had swept a trail across the room.",
        tags={"sweeping", "clue"},
    ),
}

TOOLS = {
    "echo_lens": Tool(
        id="echo_lens",
        label="the echo lens",
        action="The round glass showed where old magic had gone, and a pale path of sparkles drew a line back to the hidden doorway.",
        helpful=3,
        works_on={"sneezy_sprite", "mixed_up_broom"},
        qa_text="used the echo lens to see where the magic had moved",
        tags={"lens", "magic_tool"},
    ),
    "kind_rhyme": Tool(
        id="kind_rhyme",
        label="a kind rhyme",
        action="They spoke a gentle little rhyme that untangled nervous magic without hurting anyone who had caused the trouble.",
        helpful=2,
        works_on={"sneezy_sprite", "giant_sleeping_cat"},
        qa_text="spoke a kind rhyme that calmed the mixed-up magic",
        tags={"rhyme", "magic_tool"},
    ),
    "chalk_compass": Tool(
        id="chalk_compass",
        label="the chalk compass",
        action="The little arrow spun once, then settled and pointed straight toward the truest doorway in the room.",
        helpful=2,
        works_on={"mixed_up_broom", "giant_sleeping_cat"},
        qa_text="used the chalk compass to point toward the true doorway",
        tags={"compass", "magic_tool"},
    ),
    "guessing_game": Tool(
        id="guessing_game",
        label="a guessing game",
        action="They guessed and guessed, but guessing only made the mystery feel foggier.",
        helpful=1,
        works_on=set(),
        qa_text="only guessed instead of using evidence",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Eli", "Ben", "Max", "Sam", "Leo", "Theo"]
TRAITS_A = ["careful", "sharp-eyed", "curious", "calm"]
TRAITS_B = ["patient", "kind", "steady", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    cause: str
    clue: str
    tool: str
    detective_a: str
    detective_a_gender: str
    detective_b: str
    detective_b_gender: str
    trait_a: str
    trait_b: str
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


CURATED = [
    StoryParams(
        place="library",
        cause="sneezy_sprite",
        clue="glitter_dust",
        tool="echo_lens",
        detective_a="Nora",
        detective_a_gender="girl",
        detective_b="Eli",
        detective_b_gender="boy",
        trait_a="careful",
        trait_b="patient",
    ),
    StoryParams(
        place="observatory",
        cause="mixed_up_broom",
        clue="sweeping_marks",
        tool="chalk_compass",
        detective_a="Mia",
        detective_a_gender="girl",
        detective_b="Theo",
        detective_b_gender="boy",
        trait_a="sharp-eyed",
        trait_b="steady",
    ),
    StoryParams(
        place="greenhouse",
        cause="giant_sleeping_cat",
        clue="silver_whisker",
        tool="kind_rhyme",
        detective_a="Leo",
        detective_a_gender="boy",
        detective_b="Ava",
        detective_b_gender="girl",
        trait_a="curious",
        trait_b="kind",
    ),
]


KNOWLEDGE = {
    "exit": [(
        "What does exit mean?",
        "An exit is the way out of a place. Signs that say exit help people leave safely."
    )],
    "detective": [(
        "What does a detective do?",
        "A detective looks for clues and uses them to solve a mystery. Good detectives do not just guess."
    )],
    "clue": [(
        "What is a clue?",
        "A clue is a small sign that helps you understand what happened. One clue may not be enough, but clues together can solve a puzzle."
    )],
    "magic": [(
        "What is magic in a story like this?",
        "Magic is a special power that can make unusual things happen, like signs glowing or doors hiding. In a mystery story, the characters still need careful thinking to understand it."
    )],
    "friendship": [(
        "How can friendship help solve a problem?",
        "Friends can stay calm together, share ideas, and help each other be brave. Working together often makes a hard problem easier."
    )],
    "lens": [(
        "What does a lens help you do?",
        "A lens helps you see something more clearly. In a magic story, it can also help reveal things that are hidden."
    )],
    "rhyme": [(
        "Why might a kind rhyme help with nervous magic?",
        "Gentle words can calm a frightened creature in stories. If the magic came from worry or sleepiness, kindness can help untangle it."
    )],
    "compass": [(
        "What does a compass do?",
        "A compass points a way to go. In stories, a special compass can help characters find the true path."
    )],
}
KNOWLEDGE_ORDER = ["exit", "detective", "clue", "magic", "friendship", "lens", "rhyme", "compass"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["detective_a"]
    b = f["detective_b"]
    place = f["place"]
    cause = f["cause"]
    return [
        f'Write a short detective story for a 3-to-5-year-old where two friends must solve a magical mystery about a missing exit in {place.label}. Include the word "exit".',
        f"Tell a gentle mystery where {a.id} and {b.id} collect clues, stay kind to each other, and discover that {cause.label} hid the way out by mistake.",
        f'Write a child-facing detective story with friendship, magic, and a clear solved ending where clues matter more than guessing.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["detective_a"]
    b = f["detective_b"]
    place = f["place"]
    cause = f["cause"]
    clue = f["clue"]
    tool = f["tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two young detective friends, {a.id} and {b.id}. They work together in {place.label} when the exit seems to disappear."
        ),
        (
            "What was the mystery?",
            f"The mystery was that the exit sign and doorway seemed to be gone. That mattered because the children needed a safe way out instead of wandering deeper inside."
        ),
        (
            f"What clue did {a.id} find first?",
            f"{a.id} found {clue.discovery}. That clue told the friends the trouble came from magic moving through the room, not from an ordinary broken sign."
        ),
        (
            f"How did friendship help {a.id} and {b.id}?",
            f"They stayed together and shared what each one noticed. Because neither friend panicked, they could think clearly and solve the mystery as a team."
        ),
        (
            "Why was the exit hidden?",
            f"The exit was hidden because {cause.reveal_line[0].lower() + cause.reveal_line[1:] if cause.reveal_line else cause.label}. The clue trail showed that the magic had been pushed away from the doorway."
        ),
        (
            "How did they solve the case?",
            f"They {tool.qa_text}. Once they had two clues and the right tool, the spell lifted and the true exit appeared again."
        ),
        (
            "How did the story end?",
            f"The friends found a safe doorway and got out together. The ending proves they solved the mystery because the glowing exit returned where it belonged."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"exit", "detective", "clue", "magic", "friendship"}
    tool = f["tool"]
    if tool.id == "echo_lens":
        tags.add("lens")
    elif tool.id == "kind_rhyme":
        tags.add("rhyme")
    elif tool.id == "chalk_compass":
        tags.add("compass")
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% Valid combinations: the cause really hides the exit, and the chosen tool is
% helpful enough and works on that cause.
valid(P, C, Cl, T) :- place(P), cause(C), clue(Cl), tool(T),
                      hides_exit(C),
                      solves(C, T),
                      helpful(T, H), helpful_min(M), H >= M.

% Outcome model: every valid scenario finds two clues, forms a theory, and the
% right tool lifts the spell.
two_clues(C, Cl) :- cause(C), clue(Cl).
theory_ready(C, Cl) :- two_clues(C, Cl).
solved(C, T, Cl) :- theory_ready(C, Cl), solves(C, T), helpful(T, H), helpful_min(M), H >= M.
outcome(solved) :- chosen_cause(C), chosen_tool(T), chosen_clue(Cl), solved(C, T, Cl).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        if cause.hidden_exit:
            lines.append(asp.fact("hides_exit", cid))
        for tid in sorted(cause.solved_by):
            lines.append(asp.fact("solves", cid, tid))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("helpful", tid, tool.helpful))
    lines.append(asp.fact("helpful_min", HELPFUL_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_clue", params.clue),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    items = asp.atoms(model, "outcome")
    return items[0][0] if items else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: friendship detectives solve a magical hidden-exit mystery."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.tool:
        cause = CAUSES[args.cause]
        tool = TOOLS[args.tool]
        if not cause_reasonable(cause, tool):
            raise StoryError(explain_rejection(cause, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cause is None or combo[1] == args.cause)
        and (args.clue is None or combo[2] == args.clue)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, cause, clue, tool = rng.choice(sorted(combos))
    gender_a = rng.choice(["girl", "boy"])
    gender_b = rng.choice(["girl", "boy"])
    detective_a = _pick_name(rng, gender_a)
    detective_b = _pick_name(rng, gender_b, avoid=detective_a)
    return StoryParams(
        place=place,
        cause=cause,
        clue=clue,
        tool=tool,
        detective_a=detective_a,
        detective_a_gender=gender_a,
        detective_b=detective_b,
        detective_b_gender=gender_b,
        trait_a=rng.choice(TRAITS_A),
        trait_b=rng.choice(TRAITS_B),
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        cause = CAUSES[params.cause]
        clue = CLUES[params.clue]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from err
    if not cause_reasonable(cause, tool):
        raise StoryError(explain_rejection(cause, tool))

    world = tell(
        place=place,
        cause=cause,
        clue=clue,
        tool=tool,
        detective_a=params.detective_a,
        detective_a_gender=params.detective_a_gender,
        detective_b=params.detective_b,
        detective_b_gender=params.detective_b_gender,
        trait_a=params.trait_a,
        trait_b=params.trait_b,
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

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP valid combinations match Python ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    bad = 0
    for p in cases:
        if asp_outcome(p) != "solved":
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches expected solved ending on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} scenarios did not solve in ASP.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story or "exit" not in smoke.story:
            raise StoryError("smoke story was empty or missing required word")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation/emit test passed.")
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
        print(f"{len(combos)} valid (place, cause, clue, tool) combos:\n")
        for place, cause, clue, tool in combos:
            print(f"  {place:11} {cause:18} {clue:15} {tool}")
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
            header = f"### {p.detective_a} & {p.detective_b}: {p.place}, {p.cause}, {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
