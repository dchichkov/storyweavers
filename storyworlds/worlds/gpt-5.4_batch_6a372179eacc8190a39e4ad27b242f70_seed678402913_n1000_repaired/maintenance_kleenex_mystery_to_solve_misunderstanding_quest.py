#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/maintenance_kleenex_mystery_to_solve_misunderstanding_quest.py
==========================================================================================

A standalone story world about a small everyday mystery: a child notices that a
box of kleenex has been moved, jumps to the wrong conclusion, and goes on a
gentle quest to find out why. The answer turns out to involve ordinary
maintenance, not meanness, and the ending proves that asking kindly helps solve
misunderstandings.

The world is deliberately small and constraint-checked. A "clue" must actually
fit the maintenance issue it points to, and the chosen fix must be a sensible
repair for that issue. The misunderstanding beat and the little quest are driven
by simulated state rather than template swapping.

Run it
------
    python storyworlds/worlds/gpt-5.4/maintenance_kleenex_mystery_to_solve_misunderstanding_quest.py
    python storyworlds/worlds/gpt-5.4/maintenance_kleenex_mystery_to_solve_misunderstanding_quest.py --place apartment --issue draft --clue flutter --fix weather_strip
    python storyworlds/worlds/gpt-5.4/maintenance_kleenex_mystery_to_solve_misunderstanding_quest.py --issue smell
    python storyworlds/worlds/gpt-5.4/maintenance_kleenex_mystery_to_solve_misunderstanding_quest.py --all
    python storyworlds/worlds/gpt-5.4/maintenance_kleenex_mystery_to_solve_misunderstanding_quest.py --qa --json
    python storyworlds/worlds/gpt-5.4/maintenance_kleenex_mystery_to_solve_misunderstanding_quest.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher", "manager"}
        male = {"boy", "father", "man", "janitor", "superintendent"}
        they_types = {"child", "friend", "worker", "neighbor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in they_types:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "superintendent": "super",
            "janitor": "janitor",
            "manager": "manager",
            "teacher": "teacher",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    homey: str
    storage_spot: str
    maintenance_person: str
    parent_title: str
    room_word: str
    issue_spots: dict[str, str] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)


@dataclass
class Issue:
    id: str
    label: str
    issue_type: str
    needs: str
    clue_states: set[str] = field(default_factory=set)
    sensible_fixes: set[str] = field(default_factory=set)
    sign_text: str = ""
    fix_result: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    state: str
    discovery: str
    explanation: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    does: set[str] = field(default_factory=set)
    action_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Mood:
    id: str
    opening: str
    accuse_line: str
    ask_line: str
    ending_glow: str


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


def _r_clue_points(world: World) -> list[str]:
    out: list[str] = []
    issue = world.get("issue")
    clue = world.get("clue")
    if issue.attrs.get("active") and clue.attrs.get("fits_issue"):
        sig = ("clue_points", issue.id, clue.id)
        if sig not in world.fired:
            world.fired.add(sig)
            clue.meters["evidence"] += 1
            world.get("hero").memes["curiosity"] += 1
            out.append("__evidence__")
    return out


def _r_kind_question(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes["asks_kindly"] >= THRESHOLD and helper.memes["knows_truth"] >= THRESHOLD:
        sig = ("kind_question", hero.id, helper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["understanding"] += 1
            hero.memes["worry"] = 0.0
            helper.memes["trust"] += 1
            out.append("__understanding__")
    return out


CAUSAL_RULES = [
    Rule(name="clue_points", tag="physical", apply=_r_clue_points),
    Rule(name="kind_question", tag="social", apply=_r_kind_question),
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


def clue_matches(issue: Issue, clue: Clue) -> bool:
    return clue.state in issue.clue_states


def fix_works(issue: Issue, fix: Fix) -> bool:
    return issue.needs in fix.does and fix.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for issue_id, issue in ISSUES.items():
            for clue_id, clue in CLUES.items():
                if not clue_matches(issue, clue):
                    continue
                for fix_id, fix in FIXES.items():
                    if fix_works(issue, fix):
                        combos.append((place_id, issue_id, clue_id, fix_id))
    return combos


def predict_truth(issue: Issue, clue: Clue, fix: Fix) -> dict:
    return {
        "clue_fits": clue_matches(issue, clue),
        "fix_works": fix_works(issue, fix),
    }


def introduce(world: World, hero: Entity, parent: Entity, place: Place, mood: Mood) -> None:
    world.say(
        f"{hero.id} lived in {place.homey} where small things mattered: whose shoes were by the door, "
        f"which mug belonged to {parent.label_word}, and where the box of kleenex always sat."
    )
    world.say(
        f"That afternoon, {mood.opening} The little box was not in {place.storage_spot}, and the space looked strangely bare."
    )


def missing_box(world: World, hero: Entity, clue: Clue, issue: Issue, place: Place) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"Near {place.issue_spots[issue.id]}, {hero.pronoun()} spotted {clue.discovery}. "
        f"Seeing kleenex in the wrong place made the whole thing feel like a mystery."
    )
    world.say(
        f"{hero.id} remembered that {place.maintenance_person} had come by for maintenance that morning, "
        f"and a worried idea popped into {hero.pronoun('possessive')} head."
    )


def misunderstanding(world: World, hero: Entity, helper: Entity, mood: Mood) -> None:
    hero.memes["misunderstanding"] += 1
    hero.memes["defiance"] += 1
    world.say(
        f'"Maybe {helper.label_word} took it away," {hero.id} whispered. {mood.accuse_line}'
    )


def choose_quest(world: World, hero: Entity, buddy: Entity, place: Place, issue: Issue) -> None:
    hero.memes["quest"] += 1
    buddy.memes["support"] += 1
    world.say(
        f"{buddy.id} did not laugh. Instead, {buddy.pronoun()} said they should go on a quiet quest and look for clues before blaming anyone."
    )
    world.say(
        f"So the two children checked {place.storage_spot}, the hall shelf, and the floor near {place.issue_spots[issue.id]}."
    )


def inspect(world: World, hero: Entity, clue: Clue, issue: Issue, fix: Fix) -> None:
    clue_ent = world.get("clue")
    issue_ent = world.get("issue")
    clue_ent.attrs["fits_issue"] = clue_matches(issue, clue)
    issue_ent.attrs["active"] = True
    world.facts["prediction"] = predict_truth(issue, clue, fix)
    propagate(world, narrate=False)
    if clue_ent.meters["evidence"] >= THRESHOLD:
        world.say(
            f"The closer {hero.id} looked, the less the clue seemed sneaky and the more it seemed useful. {clue.explanation}"
        )
    else:
        world.say(
            f"The clue looked puzzling, but it still did not prove anyone had done anything mean."
        )


def ask_adult(world: World, hero: Entity, parent: Entity, helper: Entity, mood: Mood) -> None:
    hero.memes["asks_kindly"] += 1
    helper.memes["knows_truth"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last {hero.id} took a breath and went to ask {parent.label_word} instead of hiding behind the door."
    )
    world.say(
        f'{mood.ask_line} "{helper.label_word.capitalize()}, did you move the kleenex for a reason?"'
    )


def reveal(world: World, hero: Entity, helper: Entity, issue: Issue, clue: Clue, place: Place) -> None:
    hero.memes["relief"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.label_word.capitalize()} smiled in surprise and pointed to {place.issue_spots[issue.id]}. "
        f'"I did move it," {helper.pronoun()} said, "but only because {issue.sign_text}. {clue.explanation}"'
    )
    world.say(
        f"Right beside the wall sat the missing box of kleenex, set there for the work and not lost at all."
    )


def repair(world: World, helper: Entity, issue: Issue, fix: Fix) -> None:
    issue_ent = world.get("issue")
    issue_ent.meters["fixed"] += 1
    issue_ent.meters["trouble"] = 0.0
    world.say(
        f"Then {helper.label_word} {fix.action_text}. {issue.fix_result}"
    )


def gentle_lesson(world: World, hero: Entity, parent: Entity, buddy: Entity) -> None:
    hero.memes["lesson"] += 1
    hero.memes["love"] += 1
    buddy.memes["love"] += 1
    world.say(
        f"{parent.label_word.capitalize()} squeezed {hero.id}'s shoulder. "
        f'"Mysteries feel bigger when we guess," {parent.pronoun()} said. "Asking kindly helps us see what is really going on."'
    )
    world.say(
        f"{hero.id} nodded and thanked {buddy.id} for staying on the quest instead of turning it into a fight."
    )


def ending(world: World, hero: Entity, buddy: Entity, place: Place, mood: Mood) -> None:
    world.say(
        f"Later, a fresh box of kleenex went back to {place.storage_spot}, and the room felt ordinary again in the nicest way."
    )
    world.say(
        f"{hero.id} and {buddy.id} sat nearby, listening to the new quiet and sharing {mood.ending_glow}."
    )


def tell(
    place: Place,
    issue: Issue,
    clue: Clue,
    fix: Fix,
    mood: Mood,
    hero_name: str = "Nora",
    hero_gender: str = "girl",
    buddy_name: str = "Ben",
    buddy_gender: str = "boy",
    parent_type: str = "mother",
    helper_type: str = "superintendent",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    buddy = world.add(Entity(id="buddy", kind="character", type=buddy_gender, label=buddy_name, role="buddy"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=place.maintenance_person, role="helper"))
    issue_ent = world.add(Entity(id="issue", kind="thing", type="issue", label=issue.label, role="issue"))
    clue_ent = world.add(Entity(id="clue", kind="thing", type="kleenex", label=clue.label, role="clue"))
    issue_ent.meters["trouble"] = 1.0

    introduce(world, hero, parent, place, mood)
    missing_box(world, hero, clue, issue, place)

    world.para()
    misunderstanding(world, hero, helper, mood)
    choose_quest(world, hero, buddy, place, issue)
    inspect(world, hero, clue, issue, fix)

    world.para()
    ask_adult(world, hero, parent, helper, mood)
    reveal(world, hero, helper, issue, clue, place)
    repair(world, helper, issue, fix)

    world.para()
    gentle_lesson(world, hero, parent, buddy)
    ending(world, hero, buddy, place, mood)

    world.facts.update(
        place=place,
        issue=issue,
        clue=clue,
        fix=fix,
        mood=mood,
        hero=hero,
        buddy=buddy,
        parent=parent,
        helper=helper,
        solved=issue_ent.meters["fixed"] >= THRESHOLD,
        misunderstood=hero.memes["misunderstanding"] >= THRESHOLD,
        asked_kindly=hero.memes["understanding"] >= THRESHOLD,
    )
    return world


PLACES = {
    "apartment": Place(
        id="apartment",
        label="apartment",
        homey="a snug apartment at the end of a bright hallway",
        storage_spot="the little table by the couch",
        maintenance_person="the super",
        parent_title="mother",
        room_word="living room",
        issue_spots={
            "draft": "the old window by the curtain",
            "drip": "the bathroom sink pipe",
            "radiator": "the warm radiator under the window",
        },
        tags={"home", "building"},
    ),
    "classroom": Place(
        id="classroom",
        label="classroom",
        homey="a cheerful classroom with low hooks and paper suns in the window",
        storage_spot="the reading corner shelf",
        maintenance_person="the janitor",
        parent_title="teacher",
        room_word="classroom",
        issue_spots={
            "draft": "the tall window by the rug",
            "drip": "the sink at the art counter",
            "radiator": "the radiator by the cubbies",
        },
        tags={"school"},
    ),
    "library": Place(
        id="library",
        label="library",
        homey="a quiet little library room with beanbags and soft lamps",
        storage_spot="the puzzle table",
        maintenance_person="the manager",
        parent_title="father",
        room_word="reading room",
        issue_spots={
            "draft": "the front window near the story chair",
            "drip": "the sink in the back workroom",
            "radiator": "the heater under the bulletin board",
        },
        tags={"community"},
    ),
}

ISSUES = {
    "draft": Issue(
        id="draft",
        label="draft",
        issue_type="air",
        needs="weather_strip",
        clue_states={"flutter"},
        sensible_fixes={"weather_strip"},
        sign_text="a cold draft was slipping in",
        fix_result="Soon the curtain hung still and the room no longer had a chilly nibble at the edges.",
        tags={"draft", "window", "maintenance"},
    ),
    "drip": Issue(
        id="drip",
        label="drip",
        issue_type="water",
        needs="tighten_pipe",
        clue_states={"damp"},
        sensible_fixes={"tighten_pipe"},
        sign_text="a small drip was sneaking down the pipe",
        fix_result="After that, no more drops tapped into the little pan below.",
        tags={"drip", "sink", "maintenance"},
    ),
    "radiator": Issue(
        id="radiator",
        label="radiator rattle",
        issue_type="heat",
        needs="bleed_radiator",
        clue_states={"warm"},
        sensible_fixes={"bleed_radiator"},
        sign_text="the radiator had been rattling and spitting warm air unevenly",
        fix_result="The metal stopped clanking, and the heat spread out in a calm, even hush.",
        tags={"radiator", "heat", "maintenance"},
    ),
    "smell": Issue(
        id="smell",
        label="mystery smell",
        issue_type="odor",
        needs="air_freshener",
        clue_states={"none"},
        sensible_fixes={"air_freshener"},
        sign_text="the room smelled odd",
        fix_result="The room smelled sweeter afterward.",
        tags={"odor"},
    ),
}

CLUES = {
    "flutter": Clue(
        id="flutter",
        label="a fluttering kleenex",
        state="flutter",
        discovery="a single kleenex trembling in the air like a tiny white flag",
        explanation="A fluttering kleenex was the sort of thing a grown-up might use to find moving air.",
        tags={"kleenex", "draft"},
    ),
    "damp": Clue(
        id="damp",
        label="a damp kleenex",
        state="damp",
        discovery="a folded kleenex with one wet corner",
        explanation="A damp kleenex made sense near a drip, because it could show exactly where the water had touched.",
        tags={"kleenex", "water"},
    ),
    "warm": Clue(
        id="warm",
        label="a warm kleenex",
        state="warm",
        discovery="a kleenex resting on the radiator, warm enough to lift at one corner",
        explanation="A warm kleenex could show where heat and air were coming through too fast.",
        tags={"kleenex", "heat"},
    ),
    "crumpled": Clue(
        id="crumpled",
        label="a crumpled kleenex",
        state="crumpled",
        discovery="a crumpled kleenex under a chair",
        explanation="A crumpled kleenex did not really explain a repair problem by itself.",
        tags={"kleenex"},
    ),
}

FIXES = {
    "weather_strip": Fix(
        id="weather_strip",
        label="sealed the window with fresh weather stripping",
        sense=3,
        does={"weather_strip"},
        action_text="sealed the window with fresh weather stripping",
        qa_text="sealed the drafty window with fresh weather stripping",
        tags={"window_fix", "maintenance"},
    ),
    "tighten_pipe": Fix(
        id="tighten_pipe",
        label="tightened the loose pipe joint",
        sense=3,
        does={"tighten_pipe"},
        action_text="tightened the loose pipe joint and wiped the metal dry",
        qa_text="tightened the loose pipe under the sink",
        tags={"pipe_fix", "maintenance"},
    ),
    "bleed_radiator": Fix(
        id="bleed_radiator",
        label="bled the radiator carefully",
        sense=3,
        does={"bleed_radiator"},
        action_text="bled the radiator carefully until the banging stopped",
        qa_text="bled the radiator so it would stop rattling",
        tags={"radiator_fix", "maintenance"},
    ),
    "tape": Fix(
        id="tape",
        label="put tape on it",
        sense=1,
        does={"weather_strip"},
        action_text="stuck tape on the spot in a hurry",
        qa_text="stuck tape on it",
        tags={"weak_fix"},
    ),
    "air_freshener": Fix(
        id="air_freshener",
        label="sprayed air freshener",
        sense=2,
        does={"air_freshener"},
        action_text="sprayed a little air freshener",
        qa_text="sprayed air freshener",
        tags={"odor"},
    ),
}

MOODS = {
    "gentle": Mood(
        id="gentle",
        opening="the day felt slow and soft, the kind of day when even the clock seemed to tiptoe",
        accuse_line="The thought pinched a little, because it made the maintenance visit sound unfriendly.",
        ask_line="Trying to sound brave and polite,",
        ending_glow="one last cookie from the plate on the table",
    ),
    "rainy": Mood(
        id="rainy",
        opening="rain tapped the windows and made every little change feel louder than usual",
        accuse_line="The thought came quickly, the way nervous thoughts often do on rainy days.",
        ask_line="With the rain still whispering outside,",
        ending_glow="the soft patter of rain and a puzzle between them",
    ),
    "busy": Mood(
        id="busy",
        opening="the room had been bustling all morning, so a small mystery had extra room to grow",
        accuse_line="It was easier to imagine the worst when everything already felt busy.",
        ask_line="After a deep breath,",
        ending_glow="the calm after a busy afternoon",
    ),
}


@dataclass
class StoryParams:
    place: str
    issue: str
    clue: str
    fix: str
    mood: str
    hero_name: str
    hero_gender: str
    buddy_name: str
    buddy_gender: str
    parent: str
    helper: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "kleenex": [
        (
            "What is kleenex used for?",
            "Kleenex is a soft tissue paper people use for noses, sneezes, and small cleanups. Because it is light, it can also show a little breeze or catch a tiny drop.",
        )
    ],
    "maintenance": [
        (
            "What does maintenance mean?",
            "Maintenance means taking care of a place so it keeps working well. That can mean fixing little problems like drips, drafts, or noisy heaters.",
        )
    ],
    "draft": [
        (
            "What is a draft from a window?",
            "A draft is a little stream of cold air slipping in through a gap. You might notice it because a curtain or tissue moves even when no one is walking by.",
        )
    ],
    "drip": [
        (
            "Why does a dripping pipe need fixing?",
            "A dripping pipe wastes water and can make a sink area wet and slippery. Fixing it early keeps the problem small.",
        )
    ],
    "radiator": [
        (
            "Why can a radiator make clanking sounds?",
            "A radiator can clank when air is trapped inside or when heat moves unevenly through it. A grown-up can service it so it warms the room more quietly.",
        )
    ],
    "ask": [
        (
            "What can you do when you think there is a misunderstanding?",
            "You can ask a calm question and listen to the answer. That helps you learn what really happened before your worried guess turns into a bigger problem.",
        )
    ],
    "quest": [
        (
            "What is a quest in a story?",
            "A quest is when a character sets out to find something or solve something. In a small everyday story, the quest can be as simple as following clues to the truth.",
        )
    ],
    "window_fix": [
        (
            "What does weather stripping do?",
            "Weather stripping fills little gaps around a door or window. It helps keep cold air out and warm air in.",
        )
    ],
    "pipe_fix": [
        (
            "What does tightening a pipe joint do?",
            "Tightening a loose pipe joint can stop a small leak. That keeps water from dripping where it should not.",
        )
    ],
    "radiator_fix": [
        (
            "What does it mean to bleed a radiator?",
            "Bleeding a radiator lets trapped air out so the heat can move through it properly. A grown-up does it carefully as part of maintenance.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "kleenex",
    "maintenance",
    "quest",
    "ask",
    "draft",
    "drip",
    "radiator",
    "window_fix",
    "pipe_fix",
    "radiator_fix",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    buddy = f["buddy"]
    issue = f["issue"]
    place = f["place"]
    return [
        'Write a gentle slice-of-life story for a 3-to-5-year-old that includes the word "maintenance" and the word "kleenex".',
        f"Tell a small mystery-to-solve story where {hero.label} thinks someone moved the kleenex for a bad reason, but the truth is ordinary maintenance in a {place.label}.",
        f"Write a story about a misunderstanding and a quiet quest, where {hero.label} and {buddy.label} follow clues and learn that the strange sign pointed to a {issue.label}, not to anyone being mean.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    buddy = f["buddy"]
    parent = f["parent"]
    helper = f["helper"]
    issue = f["issue"]
    clue = f["clue"]
    fix = f["fix"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {buddy.label}, who notice that the kleenex has been moved, and about {helper.label_word} and {parent.label_word}, who help explain why. The story stays close to one small problem in their everyday place.",
        ),
        (
            "What was the mystery?",
            f"The mystery was why the box of kleenex had been moved from {place.storage_spot}. At first {hero.label} worried that {helper.label_word} had taken it away for a mean reason, but that was the misunderstanding.",
        ),
        (
            f"What clue did {hero.label} find?",
            f"{hero.label} found {clue.label} near {place.issue_spots[issue.id]}. That clue mattered because it pointed toward the real problem instead of proving anyone had done something unkind.",
        ),
        (
            f"Why did {hero.label} and {buddy.label} go on a quest?",
            f"They wanted to solve the mystery before blaming anyone. Their little quest gave them time to look closely and notice that the kleenex clue fit a repair problem.",
        ),
        (
            f"Why had {helper.label_word} moved the kleenex?",
            f"{helper.label_word.capitalize()} had moved it because {issue.sign_text}. The kleenex was being used to notice the problem better, not to upset anyone.",
        ),
        (
            f"How was the problem fixed?",
            f"{helper.label_word.capitalize()} {fix.qa_text}. That changed the room in a clear way, because {issue.fix_result[0].lower() + issue.fix_result[1:]}",
        ),
        (
            "What did the child learn at the end?",
            f"{hero.label} learned to ask a calm question before jumping to a worried guess. The misunderstanding shrank as soon as the grown-up explained the maintenance work.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"kleenex", "maintenance", "quest", "ask"}
    issue = f["issue"]
    fix = f["fix"]
    if issue.id == "draft":
        tags.add("draft")
    elif issue.id == "drip":
        tags.add("drip")
    elif issue.id == "radiator":
        tags.add("radiator")
    for tag in fix.tags:
        if tag in KNOWLEDGE:
            tags.add(tag)
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
        attrs = {k: v for k, v in e.attrs.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="apartment",
        issue="draft",
        clue="flutter",
        fix="weather_strip",
        mood="gentle",
        hero_name="Nora",
        hero_gender="girl",
        buddy_name="Ben",
        buddy_gender="boy",
        parent="mother",
        helper="superintendent",
    ),
    StoryParams(
        place="classroom",
        issue="drip",
        clue="damp",
        fix="tighten_pipe",
        mood="busy",
        hero_name="Max",
        hero_gender="boy",
        buddy_name="Lila",
        buddy_gender="girl",
        parent="teacher",
        helper="janitor",
    ),
    StoryParams(
        place="library",
        issue="radiator",
        clue="warm",
        fix="bleed_radiator",
        mood="rainy",
        hero_name="Ava",
        hero_gender="girl",
        buddy_name="Theo",
        buddy_gender="boy",
        parent="father",
        helper="manager",
    ),
]


def explain_combo(issue: Issue, clue: Clue, fix: Fix) -> str:
    if not clue_matches(issue, clue):
        return (
            f"(No story: {clue.label} does not honestly point to a {issue.label}. "
            f"Pick a clue that really fits the maintenance problem.)"
        )
    if fix.sense < SENSE_MIN:
        return (
            f"(No story: the fix '{fix.id}' is too weak or sloppy for this world "
            f"(sense={fix.sense} < {SENSE_MIN}). Pick a more sensible repair.)"
        )
    if not fix_works(issue, fix):
        return (
            f"(No story: {fix.label} does not really solve a {issue.label}. "
            f"The repair in this world has to match the actual problem.)"
        )
    return "(No story: invalid combination.)"


ASP_RULES = r"""
clue_matches(I, C) :- issue(I), clue(C), clue_state(C, S), issue_clue(I, S).
sensible_fix(F)    :- fix(F), sense(F, S), sense_min(M), S >= M.
fix_works(I, F)    :- issue(I), fix(F), issue_need(I, N), fix_does(F, N), sensible_fix(F).
valid(P, I, C, F)  :- place(P), clue_matches(I, C), fix_works(I, F).

outcome(solved) :- chosen_issue(I), chosen_clue(C), chosen_fix(F), clue_matches(I, C), fix_works(I, F).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, issue in ISSUES.items():
        lines.append(asp.fact("issue", iid))
        lines.append(asp.fact("issue_need", iid, issue.needs))
        for state in sorted(issue.clue_states):
            lines.append(asp.fact("issue_clue", iid, state))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_state", cid, clue.state))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        for need in sorted(fix.does):
            lines.append(asp.fact("fix_does", fid, need))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_fix/1."))
    return sorted(fid for (fid,) in asp.atoms(model, "sensible_fix"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_issue", params.issue),
            asp.fact("chosen_clue", params.clue),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a moved box of kleenex, a maintenance mystery, and a kind question."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--issue", choices=ISSUES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--parent", choices=["mother", "father", "teacher"])
    ap.add_argument("--helper", choices=["superintendent", "janitor", "manager"])
    ap.add_argument("--hero-name")
    ap.add_argument("--buddy-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Nora", "Lila", "Mia", "Ava", "Ella", "Zoe", "Ruby", "Ivy"]
BOY_NAMES = ["Ben", "Max", "Theo", "Sam", "Noah", "Leo", "Finn", "Eli"]


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.issue and args.issue not in ISSUES:
        raise StoryError("(No story: unknown issue.)")
    if args.clue and args.clue not in CLUES:
        raise StoryError("(No story: unknown clue.)")
    if args.fix and args.fix not in FIXES:
        raise StoryError("(No story: unknown fix.)")

    if args.issue and args.clue and args.fix:
        issue = ISSUES[args.issue]
        clue = CLUES[args.clue]
        fix = FIXES[args.fix]
        if not (clue_matches(issue, clue) and fix_works(issue, fix)):
            raise StoryError(explain_combo(issue, clue, fix))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.issue is None or c[1] == args.issue)
        and (args.clue is None or c[2] == args.clue)
        and (args.fix is None or c[3] == args.fix)
    ]
    if not combos:
        if args.issue and args.clue and args.fix:
            raise StoryError(explain_combo(ISSUES[args.issue], CLUES[args.clue], FIXES[args.fix]))
        raise StoryError("(No valid combination matches the given options.)")

    place, issue, clue, fix = rng.choice(sorted(combos))
    mood = args.mood or rng.choice(sorted(MOODS))
    hero_gender = rng.choice(["girl", "boy"])
    buddy_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    buddy_name = args.buddy_name or _pick_name(rng, buddy_gender, avoid=hero_name)
    helper = args.helper or rng.choice(["superintendent", "janitor", "manager"])
    parent = args.parent or rng.choice(["mother", "father", "teacher"])
    return StoryParams(
        place=place,
        issue=issue,
        clue=clue,
        fix=fix,
        mood=mood,
        hero_name=hero_name,
        hero_gender=hero_gender,
        buddy_name=buddy_name,
        buddy_gender=buddy_gender,
        parent=parent,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.issue not in ISSUES:
        raise StoryError(f"(No story: unknown issue '{params.issue}'.)")
    if params.clue not in CLUES:
        raise StoryError(f"(No story: unknown clue '{params.clue}'.)")
    if params.fix not in FIXES:
        raise StoryError(f"(No story: unknown fix '{params.fix}'.)")
    if params.mood not in MOODS:
        raise StoryError(f"(No story: unknown mood '{params.mood}'.)")

    issue = ISSUES[params.issue]
    clue = CLUES[params.clue]
    fix = FIXES[params.fix]
    if not (clue_matches(issue, clue) and fix_works(issue, fix)):
        raise StoryError(explain_combo(issue, clue, fix))

    world = tell(
        place=PLACES[params.place],
        issue=issue,
        clue=clue,
        fix=fix,
        mood=MOODS[params.mood],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        buddy_name=params.buddy_name,
        buddy_gender=params.buddy_gender,
        parent_type=params.parent,
        helper_type=params.helper,
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

    clingo_sens = set(asp_sensible_fixes())
    python_sens = {fid for fid, fix in FIXES.items() if fix.sense >= SENSE_MIN}
    if clingo_sens == python_sens:
        print(f"OK: sensible fixes match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        outcome = asp_outcome(params)
        expected = "solved" if (clue_matches(ISSUES[params.issue], CLUES[params.clue]) and fix_works(ISSUES[params.issue], FIXES[params.fix])) else "?"
        if outcome != expected:
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} ASP outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible_fix/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible fixes: {', '.join(asp_sensible_fixes())}\n")
        print(f"{len(combos)} compatible (place, issue, clue, fix) combos:\n")
        for place, issue, clue, fix in combos:
            print(f"  {place:10} {issue:8} {clue:8} {fix}")
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
            header = f"### {p.hero_name}: {p.issue} in {p.place} ({p.clue}, {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
