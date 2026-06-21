#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lame_magic_conflict_heartwarming.py
==============================================================

A standalone story world about a child who blurts out that their own magic tool
is "lame," hurts a friend's feelings, and then learns that humble magic works
best with kindness.

The world is small and classical:
- a magical place has one concrete little problem,
- a child envies a friend's shinier object,
- a conflict breaks trust,
- a helper guides a repair,
- the supposedly lame charm solves the problem once the children are kind again.

Run it
------
    python storyworlds/worlds/gpt-5.4/lame_magic_conflict_heartwarming.py
    python storyworlds/worlds/gpt-5.4/lame_magic_conflict_heartwarming.py --place garden --charm twig_wand --problem dark_path
    python storyworlds/worlds/gpt-5.4/lame_magic_conflict_heartwarming.py --repair silent_shrug
    python storyworlds/worlds/gpt-5.4/lame_magic_conflict_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/lame_magic_conflict_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/lame_magic_conflict_heartwarming.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    closing: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    spell: str
    humble: str
    success: str
    fizzle: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AdmiredItem:
    id: str
    label: str
    phrase: str
    shine: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    need: str
    setup: str
    worry: str
    solved: str
    object_label: str
    object_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ConflictStyle:
    id: str
    severity: int
    line: str
    snatch: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    sense: int
    mend: int
    line: str
    action: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    charm: str
    admired: str
    problem: str
    conflict: str
    repair: str
    speaker: str
    speaker_gender: str
    friend: str
    friend_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


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


def _r_hurt_breaks_trust(world: World) -> list[str]:
    speaker = world.get("speaker")
    friend = world.get("friend")
    if friend.memes["hurt"] < THRESHOLD:
        return []
    sig = ("hurt_breaks_trust",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["trust"] = 0.0
    speaker.memes["distance"] += 1
    return ["__hurt__"]


def _r_magic_answer(world: World) -> list[str]:
    charm = world.get("charm")
    problem = world.get("problem")
    speaker = world.get("speaker")
    friend = world.get("friend")
    charm_cfg: Charm = world.facts["charm_cfg"]
    problem_cfg: Problem = world.facts["problem_cfg"]
    if charm.meters["used"] < THRESHOLD or problem.meters["solved"] >= THRESHOLD:
        return []
    if charm_cfg.spell == problem_cfg.need and friend.memes["trust"] >= THRESHOLD:
        sig = ("magic_works",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        problem.meters["solved"] += 1
        world.get("place").meters["glow"] += 1
        speaker.memes["relief"] += 1
        friend.memes["joy"] += 1
        return [charm_cfg.success, problem_cfg.solved]
    sig = ("magic_fizzles",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    charm.meters["fizzled"] += 1
    speaker.memes["embarrassed"] += 1
    return [charm_cfg.fizzle]


CAUSAL_RULES = [
    Rule(name="hurt_breaks_trust", tag="social", apply=_r_hurt_breaks_trust),
    Rule(name="magic_answer", tag="magic", apply=_r_magic_answer),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "garden": Place(
        id="garden",
        label="the moonlit garden",
        scene="Behind the house, the moonlit garden smelled like mint and wet soil.",
        closing="Soon the stepping-stones looked like little moons, and the children walked side by side through the garden.",
        affords={"dark_path", "lost_kitten"},
        tags={"garden"},
    ),
    "attic": Place(
        id="attic",
        label="the attic playroom",
        scene="Up in the attic playroom, trunks and quilts made soft little hills under the rafters.",
        closing="Soon the cozy attic glowed again, and the children sat together on the quilt, smiling into the warm light.",
        affords={"dark_path", "windy_quilt"},
        tags={"attic"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="the stone courtyard",
        scene="In the stone courtyard, evening stars blinked above the fountain.",
        closing="Soon the courtyard felt gentle again, and the children laughed as the fountain whispered beside them.",
        affords={"windy_quilt", "lost_kitten"},
        tags={"courtyard"},
    ),
}

CHARMS = {
    "twig_wand": Charm(
        id="twig_wand",
        label="twig wand",
        phrase="a little twig wand wrapped with blue thread",
        spell="light",
        humble="It was plain, only a twig with thread around it, but it fit perfectly in a small hand.",
        success="The twig wand gave one shy blink, then little pearly lights hopped from its tip.",
        fizzle="The twig wand only made one lonely spark and then went still.",
        tags={"wand", "light_magic"},
    ),
    "patched_cape": Charm(
        id="patched_cape",
        label="patched cape",
        phrase="a patched moon-blue cape",
        spell="calm",
        humble="Its hem was mended in three places, and the stitches showed if you looked closely.",
        success="The patched cape puffed once like a sleepy bird, and the rushing air curled down into a quiet swirl.",
        fizzle="The patched cape flapped wildly and only stirred the air more.",
        tags={"cape", "wind_magic"},
    ),
    "tin_whistle": Charm(
        id="tin_whistle",
        label="tin whistle",
        phrase="a dull tin whistle on a string",
        spell="find",
        humble="It had lost most of its shine long ago, but its small note was clear.",
        success="The tin whistle sang one bright note, and something hidden answered right away.",
        fizzle="The whistle squeaked softly, but nothing answered from the shadows.",
        tags={"whistle", "finding_magic"},
    ),
}

ADMIRED = {
    "crystal_wand": AdmiredItem(
        id="crystal_wand",
        label="crystal wand",
        phrase="a crystal wand",
        shine="It flashed with tiny rainbow sparks whenever it moved.",
        tags={"wand", "sparkly"},
    ),
    "star_cloak": AdmiredItem(
        id="star_cloak",
        label="star cloak",
        phrase="a silver-star cloak",
        shine="Its little stitched stars winked whenever moonlight touched them.",
        tags={"cloak", "sparkly"},
    ),
    "gold_flute": AdmiredItem(
        id="gold_flute",
        label="gold flute",
        phrase="a tiny gold flute",
        shine="Its sides shone so brightly that it looked almost sunlit.",
        tags={"flute", "sparkly"},
    ),
}

PROBLEMS = {
    "dark_path": Problem(
        id="dark_path",
        need="light",
        setup="A short path of stepping-stones led to the evening treat table, but the stones were already going dark.",
        worry="Without a little light, the children would have to stop their moonlit game and go back inside.",
        solved="One by one, the dark stones lit up until the whole path could be followed safely.",
        object_label="path",
        object_phrase="the stepping-stone path",
        tags={"dark", "light"},
    ),
    "windy_quilt": Problem(
        id="windy_quilt",
        need="calm",
        setup="A picnic quilt kept flipping at the corners, and napkins skittered away every time the breeze ran through.",
        worry="If the wind kept tugging like that, their cozy snack would never stay put.",
        solved="The quilt corners settled flat, and the napkins rested as still as sleeping mice.",
        object_label="quilt",
        object_phrase="the picnic quilt",
        tags={"wind", "picnic"},
    ),
    "lost_kitten": Problem(
        id="lost_kitten",
        need="find",
        setup="A soft gray kitten had slipped behind the tall pots and would not come when anyone called.",
        worry="Until the kitten was found, nobody felt ready for a game or a snack.",
        object_label="kitten",
        object_phrase="the little gray kitten",
        solved="A tiny mew answered, and the little gray kitten padded out with its tail high.",
        tags={"kitten", "finding"},
    ),
}

CONFLICTS = {
    "mutter_lame": ConflictStyle(
        id="mutter_lame",
        severity=1,
        line='"{charm_word} is so lame," {speaker} muttered. "{friend} gets the nice one."',
        snatch=False,
        tags={"unkind_words"},
    ),
    "blurt_lame_and_reach": ConflictStyle(
        id="blurt_lame_and_reach",
        severity=2,
        line='"{charm_word} is lame. I want yours instead!" {speaker} blurted, and {speaker_pronoun} reached for {friend_possessive} {admired}.',
        snatch=True,
        tags={"unkind_words", "grabbing"},
    ),
}

REPAIRS = {
    "quick_sorry": Repair(
        id="quick_sorry",
        sense=2,
        mend=1,
        line='"I am sorry I said that," {speaker} whispered.',
        action="A small sorry softened the air, but only a little.",
        qa_text="said sorry for the unkind words",
        tags={"apology"},
    ),
    "sorry_and_share": Repair(
        id="sorry_and_share",
        sense=3,
        mend=2,
        line='"I am sorry. Your magic matters, and mine does too. Will you take turns with me?" {speaker} asked.',
        action="{friend} nodded, and the two children agreed to take turns and stand shoulder to shoulder.",
        qa_text="apologized and suggested taking turns",
        tags={"apology", "sharing"},
    ),
    "sorry_and_help": Repair(
        id="sorry_and_help",
        sense=3,
        mend=2,
        line='"I am sorry I hurt your feelings. Let me help with the problem using my own charm first," {speaker} said.',
        action="{friend} stepped closer, and the children bent over the problem together.",
        qa_text="apologized and offered to help with the problem",
        tags={"apology", "helping"},
    ),
    "silent_shrug": Repair(
        id="silent_shrug",
        sense=1,
        mend=0,
        line='{speaker} only shrugged and looked away.',
        action="The silence did not mend anything.",
        qa_text="shrugged instead of apologizing",
        tags={"poor_repair"},
    ),
}

HELPERS = {
    "grandma": ("grandmother", "Grandma"),
    "grandpa": ("grandfather", "Grandpa"),
    "aunt": ("aunt", "Aunt May"),
    "uncle": ("uncle", "Uncle Ben"),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Eli"]


def place_supports(place: Place, problem: Problem) -> bool:
    return problem.id in place.affords


def charm_fits_problem(charm: Charm, problem: Problem) -> bool:
    return charm.spell == problem.need


def repair_is_sensible(repair: Repair) -> bool:
    return repair.sense >= SENSE_MIN


def repair_heals(conflict: ConflictStyle, repair: Repair) -> bool:
    return repair.mend >= conflict.severity


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for charm_id, charm in CHARMS.items():
            for problem_id, problem in PROBLEMS.items():
                if not (place_supports(place, problem) and charm_fits_problem(charm, problem)):
                    continue
                for conflict_id, conflict in CONFLICTS.items():
                    for repair_id, repair in REPAIRS.items():
                        if repair_is_sensible(repair) and repair_heals(conflict, repair):
                            combos.append((place_id, charm_id, problem_id, conflict_id, repair_id))
    return combos


def explain_place(place: Place, problem: Problem) -> str:
    return (
        f"(No story: {problem.object_phrase} does not belong in {place.label} here. "
        f"Pick a place that actually supports that little magical problem.)"
    )


def explain_charm(charm: Charm, problem: Problem) -> str:
    return (
        f"(No story: {charm.phrase} handles {charm.spell} magic, but this problem needs "
        f"{problem.need} magic. The supposed solution must actually fit the trouble.)"
    )


def explain_repair(conflict: ConflictStyle, repair: Repair) -> str:
    if repair.sense < SENSE_MIN:
        return (
            f"(Refusing repair '{repair.id}': it is not a sensible way to mend hurt feelings. "
            f"Try an apology that actually repairs trust.)"
        )
    return (
        f"(No story: repair '{repair.id}' is too weak for conflict '{conflict.id}'. "
        f"The quarrel needs enough kindness to heal before the magic can work.)"
    )


def outcome_of(params: StoryParams) -> str:
    conflict = CONFLICTS[params.conflict]
    repair = REPAIRS[params.repair]
    place = PLACES[params.place]
    charm = CHARMS[params.charm]
    problem = PROBLEMS[params.problem]
    if not place_supports(place, problem):
        return "impossible"
    if not charm_fits_problem(charm, problem):
        return "impossible"
    return "healed" if repair_heals(conflict, repair) else "unhealed"


def introduction(world: World, speaker: Entity, friend: Entity, helper: Entity,
                 charm: Charm, admired: AdmiredItem, problem: Problem) -> None:
    place = world.place
    charm_ent = world.get("charm")
    admired_ent = world.get("admired")
    problem_ent = world.get("problem")
    speaker.memes["joy"] += 1
    friend.memes["joy"] += 1
    friend.memes["trust"] = 2.0
    speaker.memes["hope"] += 1
    world.say(place.scene)
    world.say(
        f"{speaker.id} and {friend.id} were helping {helper.label_word} get ready for a little evening treat."
    )
    world.say(
        f"{speaker.id} carried {charm.phrase}. {charm.humble}"
    )
    world.say(
        f"{friend.id} carried {admired.phrase}. {admired.shine}"
    )
    problem_ent.meters["active"] += 1
    world.say(problem.setup)
    world.say(problem.worry)
    charm_ent.attrs["spell"] = charm.spell
    admired_ent.attrs["sparkle"] = admired.id


def envy_and_conflict(world: World, speaker: Entity, friend: Entity, charm: Charm,
                      admired: AdmiredItem, conflict: ConflictStyle) -> None:
    speaker.memes["envy"] += 1
    line = conflict.line.format(
        charm_word=("This " + charm.label) if conflict.id == "mutter_lame" else "This one",
        speaker=speaker.id,
        friend=friend.id,
        speaker_pronoun=speaker.pronoun(),
        friend_possessive=friend.pronoun("possessive"),
        admired=admired.label,
    )
    world.say(line)
    friend.memes["hurt"] += 1
    if conflict.snatch:
        speaker.meters["reached"] += 1
        friend.memes["alarm"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{friend.id}'s smile fell at once. The warm feeling between them thinned, and even the magic seemed to wait."
    )


def first_try(world: World, speaker: Entity) -> None:
    charm_ent = world.get("charm")
    charm_ent.meters["used"] += 1
    speaker.memes["trying"] += 1
    propagate(world, narrate=True)


def helper_guidance(world: World, helper: Entity, speaker: Entity, friend: Entity,
                    charm: Charm, problem: Problem) -> None:
    world.say(
        f'{helper.label_word.capitalize()} came closer and knelt beside them. '
        f'"A shiny thing is not always the right thing," {helper.pronoun()} said gently.'
    )
    world.say(
        f'"{charm.label.capitalize()} knows {charm.spell} magic, and this trouble needs exactly that. '
        f'But magic listens best when hearts are soft."'
    )
    if problem.id == "lost_kitten":
        world.say(
            f'{friend.id} looked toward the pots where {problem.object_phrase} was hiding and hugged {friend.pronoun("possessive")} elbows.'
        )
    else:
        world.say(
            f'{speaker.id} looked down at the ground, hearing how quiet the place had gone.'
        )


def repair_scene(world: World, speaker: Entity, friend: Entity,
                 conflict: ConflictStyle, repair: Repair) -> None:
    line = repair.line.format(speaker=speaker.id)
    action = repair.action.format(friend=friend.id)
    world.say(line)
    world.say(action)
    speaker.memes["remorse"] += 1
    friend.memes["hurt"] = max(0.0, friend.memes["hurt"] - float(repair.mend))
    friend.memes["trust"] = min(2.0, friend.memes["trust"] + float(repair.mend))
    speaker.memes["kindness"] += 1
    if conflict.snatch:
        speaker.meters["reached"] = 0.0


def second_try(world: World, speaker: Entity, friend: Entity, charm: Charm, problem: Problem) -> None:
    charm_ent = world.get("charm")
    problem_ent = world.get("problem")
    charm_ent.meters["used"] += 1
    world.say(
        f"{speaker.id} lifted the {charm.label} again while {friend.id} stayed close beside {speaker.pronoun('object')}."
    )
    propagate(world, narrate=True)
    if problem_ent.meters["solved"] >= THRESHOLD:
        speaker.memes["joy"] += 1
        friend.memes["joy"] += 1
        world.say(
            f"{speaker.id} blinked, surprised, and then smiled at {friend.id} instead of looking at the shiny thing at all."
        )


def closing(world: World, speaker: Entity, friend: Entity, helper: Entity,
            charm: Charm, problem: Problem, repair: Repair) -> None:
    world.say(
        f'{helper.label_word.capitalize()} wrapped an arm around both children. '
        f'"There now," {helper.pronoun()} said. "Kind words make room for good magic."'
    )
    if problem.id == "lost_kitten":
        world.say(
            f"The kitten tucked itself between {speaker.id} and {friend.id}, as if it liked the kinder feeling too."
        )
    elif problem.id == "dark_path":
        world.say(
            f"The children took the treat tray together, and not one crumb spilled on the newly bright path."
        )
    else:
        world.say(
            f"They smoothed the quilt together and sat down shoulder to shoulder, close enough for both knees to touch the same fold."
        )
    world.say(world.place.closing)
    world.facts["repair_phrase"] = repair.qa_text


def tell(place: Place, charm: Charm, admired: AdmiredItem, problem: Problem,
         conflict: ConflictStyle, repair: Repair, speaker_name: str, speaker_gender: str,
         friend_name: str, friend_gender: str, helper_name: str, helper_gender: str) -> World:
    if not place_supports(place, problem):
        raise StoryError(explain_place(place, problem))
    if not charm_fits_problem(charm, problem):
        raise StoryError(explain_charm(charm, problem))
    if not repair_is_sensible(repair) or not repair_heals(conflict, repair):
        raise StoryError(explain_repair(conflict, repair))

    world = World(place)
    speaker = world.add(Entity(id=speaker_name, kind="character", type=speaker_gender, role="speaker"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    world.add(Entity(id="place", type="place", label=place.label, role="place"))
    world.add(Entity(id="charm", type="charm", label=charm.label, phrase=charm.phrase, role="tool"))
    world.add(Entity(id="admired", type="admired", label=admired.label, phrase=admired.phrase, role="envy_target"))
    world.add(Entity(
        id="problem",
        type="problem",
        label=problem.object_label,
        phrase=problem.object_phrase,
        role="problem",
    ))
    world.facts.update(
        place_cfg=place,
        charm_cfg=charm,
        admired_cfg=admired,
        problem_cfg=problem,
        conflict_cfg=conflict,
        repair_cfg=repair,
        speaker=speaker,
        friend=friend,
        helper=helper,
    )

    introduction(world, speaker, friend, helper, charm, admired, problem)
    world.para()
    envy_and_conflict(world, speaker, friend, charm, admired, conflict)
    first_try(world, speaker)
    world.para()
    helper_guidance(world, helper, speaker, friend, charm, problem)
    repair_scene(world, speaker, friend, conflict, repair)
    world.para()
    second_try(world, speaker, friend, charm, problem)
    closing(world, speaker, friend, helper, charm, problem, repair)

    world.facts.update(
        healed=friend.memes["trust"] >= THRESHOLD,
        solved=world.get("problem").meters["solved"] >= THRESHOLD,
        sparkled=world.get("place").meters["glow"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "wand": [(
        "Can a plain wand still be special?",
        "Yes. In stories and pretend play, a plain wand can still matter very much. What it does and how it is used can matter more than how shiny it looks."
    )],
    "light_magic": [(
        "Why do people use light in stories about magic?",
        "Light helps characters see and feel safe. A small light can also show hope when things seem dark."
    )],
    "wind_magic": [(
        "What does it mean to calm the wind in a story?",
        "It means making a wild, rushing feeling become gentle and still. Writers often use that to show that a problem has softened."
    )],
    "finding_magic": [(
        "Why is finding magic helpful?",
        "Finding magic helps someone notice what was hidden or lost. In a gentle story, it can turn worry into relief."
    )],
    "apology": [(
        "What is an apology?",
        "An apology is when you say you are sorry for something hurtful you did or said. A real apology tries to make the other person feel seen and cared for."
    )],
    "sharing": [(
        "Why does taking turns help after a quarrel?",
        "Taking turns shows fairness. It helps both people feel included again."
    )],
    "helping": [(
        "Why does helping fix hurt feelings?",
        "Helping shows care with actions, not just words. That can rebuild trust."
    )],
    "dark": [(
        "Why can a dark path feel scary?",
        "A dark path can feel scary because it is hard to see where to step. Light helps people feel safer and more sure."
    )],
    "wind": [(
        "What can wind do to a picnic blanket?",
        "Wind can flap the blanket and blow napkins away. That makes it hard to keep a picnic calm and cozy."
    )],
    "kitten": [(
        "What should you do if a small kitten is hiding and scared?",
        "You should stay gentle and patient. Loud grabbing can scare it more, but a calm voice can help it come out."
    )],
}
KNOWLEDGE_ORDER = [
    "wand", "light_magic", "wind_magic", "finding_magic", "apology", "sharing",
    "helping", "dark", "wind", "kitten",
]


def generation_prompts(world: World) -> list[str]:
    charm: Charm = world.facts["charm_cfg"]
    admired: AdmiredItem = world.facts["admired_cfg"]
    problem: Problem = world.facts["problem_cfg"]
    speaker: Entity = world.facts["speaker"]
    friend: Entity = world.facts["friend"]
    return [
        f'Write a heartwarming magic story for a 3-to-5-year-old that includes the word "lame" and ends with kindness fixing the magic.',
        f"Tell a gentle conflict story where {speaker.id} thinks {speaker.pronoun('possessive')} {charm.label} is lame because {friend.id} has {admired.phrase}, but the plain charm is exactly what the problem needs.",
        f"Write a small magical story where hurt feelings must be mended before {problem.object_phrase} can be helped.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    speaker: Entity = world.facts["speaker"]
    friend: Entity = world.facts["friend"]
    helper: Entity = world.facts["helper"]
    charm: Charm = world.facts["charm_cfg"]
    admired: AdmiredItem = world.facts["admired_cfg"]
    problem: Problem = world.facts["problem_cfg"]
    conflict: ConflictStyle = world.facts["conflict_cfg"]
    repair: Repair = world.facts["repair_cfg"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(speaker, friend)}, {speaker.id} and {friend.id}, and {helper.label_word} who helps them slow down and be kind."
        ),
        (
            f"What problem did the children need to solve?",
            f"They needed to help {problem.object_phrase}. {problem.worry}"
        ),
        (
            f"Why did {speaker.id} say the charm was lame?",
            f"{speaker.id} felt jealous because {friend.id} had {admired.phrase}, which looked much shinier. That envy made {speaker.pronoun('object')} forget that {speaker.pronoun('possessive')} own {charm.label} had a different gift."
        ),
    ]
    if conflict.snatch:
        out.append((
            f"How did the conflict get worse?",
            f"It got worse because {speaker.id} did not only use unkind words; {speaker.pronoun()} also reached for {friend.id}'s magic item. That made {friend.id} feel hurt and unsafe, so the trust between them dropped."
        ))
    else:
        out.append((
            f"What changed after the unkind words?",
            f"{friend.id}'s feelings were hurt, and the warm feeling between the children faded. In this world, the magic goes quiet when trust is missing."
        ))
    out.append((
        f"How did they fix the problem?",
        f"{speaker.id} {repair.qa_text}. That repaired the friendship enough for the {charm.label} to work, and then {problem.object_phrase} was helped."
    ))
    out.append((
        "How did the story end?",
        f"It ended warmly: the children were kind again, the magic answered, and {world.place.closing.lower()} The ending image shows that both the problem and the quarrel were settled."
    ))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    charm: Charm = world.facts["charm_cfg"]
    problem: Problem = world.facts["problem_cfg"]
    repair: Repair = world.facts["repair_cfg"]
    tags = set(charm.tags) | set(problem.tags) | set(repair.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden",
        charm="twig_wand",
        admired="crystal_wand",
        problem="dark_path",
        conflict="mutter_lame",
        repair="quick_sorry",
        speaker="Lily",
        speaker_gender="girl",
        friend="Tom",
        friend_gender="boy",
        helper="Grandma",
        helper_gender="grandmother",
    ),
    StoryParams(
        place="attic",
        charm="patched_cape",
        admired="star_cloak",
        problem="windy_quilt",
        conflict="blurt_lame_and_reach",
        repair="sorry_and_share",
        speaker="Max",
        speaker_gender="boy",
        friend="Nora",
        friend_gender="girl",
        helper="Grandpa",
        helper_gender="grandfather",
    ),
    StoryParams(
        place="courtyard",
        charm="tin_whistle",
        admired="gold_flute",
        problem="lost_kitten",
        conflict="blurt_lame_and_reach",
        repair="sorry_and_help",
        speaker="Ava",
        speaker_gender="girl",
        friend="Ben",
        friend_gender="boy",
        helper="Aunt May",
        helper_gender="aunt",
    ),
    StoryParams(
        place="garden",
        charm="tin_whistle",
        admired="gold_flute",
        problem="lost_kitten",
        conflict="mutter_lame",
        repair="quick_sorry",
        speaker="Finn",
        speaker_gender="boy",
        friend="Lucy",
        friend_gender="girl",
        helper="Uncle Ben",
        helper_gender="uncle",
    ),
]


ASP_RULES = r"""
supports(Place, Problem) :- place(Place), problem(Problem), affords(Place, Problem).
fits(Charm, Problem) :- charm(Charm), problem(Problem), spell_of(Charm, Need), needs(Problem, Need).
sensible_repair(R) :- repair(R), sense(R, S), sense_min(M), S >= M.
heals(C, R) :- conflict(C), repair(R), severity(C, V), mend(R, M), M >= V.
valid(Place, Charm, Problem, Conflict, Repair) :-
    supports(Place, Problem),
    fits(Charm, Problem),
    sensible_repair(Repair),
    heals(Conflict, Repair).

outcome(healed) :- conflict(C), repair(R), severity(C, V), mend(R, M), M >= V.
outcome(unhealed) :- conflict(C), repair(R), severity(C, V), mend(R, M), M < V.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for problem_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, problem_id))
    for charm_id, charm in CHARMS.items():
        lines.append(asp.fact("charm", charm_id))
        lines.append(asp.fact("spell_of", charm_id, charm.spell))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("needs", problem_id, problem.need))
    for conflict_id, conflict in CONFLICTS.items():
        lines.append(asp.fact("conflict", conflict_id))
        lines.append(asp.fact("severity", conflict_id, conflict.severity))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("mend", repair_id, repair.mend))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(conflict_id: str, repair_id: str) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("conflict", conflict_id),
        asp.fact("repair", repair_id),
        asp.fact("severity", conflict_id, CONFLICTS[conflict_id].severity),
        asp.fact("mend", repair_id, REPAIRS[repair_id].mend),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = [(cid, rid) for cid in CONFLICTS for rid in REPAIRS]
    bad = []
    for cid, rid in cases:
        py_out = "healed" if repair_heals(CONFLICTS[cid], REPAIRS[rid]) else "unhealed"
        asp_out = asp_outcome(cid, rid)
        if py_out != asp_out:
            bad.append((cid, rid, py_out, asp_out))
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} conflict/repair pairs.")
    else:
        rc = 1
        print("MISMATCH in outcome model:")
        for row in bad[:10]:
            print(" ", row)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generated and emitted a story.")
    except Exception as err:  # pragma: no cover - used only in verification mode
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming magic storyworld where a child calls a charm lame, hurts a friend, and learns that kindness wakes the right magic."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--admired", choices=ADMIRED)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid story skeletons from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.problem:
        place = PLACES[args.place]
        problem = PROBLEMS[args.problem]
        if not place_supports(place, problem):
            raise StoryError(explain_place(place, problem))
    if args.charm and args.problem:
        charm = CHARMS[args.charm]
        problem = PROBLEMS[args.problem]
        if not charm_fits_problem(charm, problem):
            raise StoryError(explain_charm(charm, problem))
    if args.conflict and args.repair:
        conflict = CONFLICTS[args.conflict]
        repair = REPAIRS[args.repair]
        if not repair_is_sensible(repair) or not repair_heals(conflict, repair):
            raise StoryError(explain_repair(conflict, repair))
    elif args.repair:
        repair = REPAIRS[args.repair]
        if not repair_is_sensible(repair):
            raise StoryError(explain_repair(CONFLICTS["mutter_lame"], repair))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.charm is None or c[1] == args.charm)
        and (args.problem is None or c[2] == args.problem)
        and (args.conflict is None or c[3] == args.conflict)
        and (args.repair is None or c[4] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, charm_id, problem_id, conflict_id, repair_id = rng.choice(sorted(combos))
    admired_id = args.admired or rng.choice(sorted(ADMIRED))
    helper_key = args.helper or rng.choice(sorted(HELPERS))
    helper_gender, helper_name = HELPERS[helper_key]
    speaker, speaker_gender = _pick_child(rng)
    friend, friend_gender = _pick_child(rng, avoid=speaker)
    return StoryParams(
        place=place_id,
        charm=charm_id,
        admired=admired_id,
        problem=problem_id,
        conflict=conflict_id,
        repair=repair_id,
        speaker=speaker,
        speaker_gender=speaker_gender,
        friend=friend,
        friend_gender=friend_gender,
        helper=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in (
        ("place", PLACES),
        ("charm", CHARMS),
        ("admired", ADMIRED),
        ("problem", PROBLEMS),
        ("conflict", CONFLICTS),
        ("repair", REPAIRS),
    ):
        value = getattr(params, key)
        if value not in table:
            raise StoryError(f"(Invalid {key}: {value})")
    world = tell(
        place=PLACES[params.place],
        charm=CHARMS[params.charm],
        admired=ADMIRED[params.admired],
        problem=PROBLEMS[params.problem],
        conflict=CONFLICTS[params.conflict],
        repair=REPAIRS[params.repair],
        speaker_name=params.speaker,
        speaker_gender=params.speaker_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, charm, problem, conflict, repair) combos:\n")
        for row in combos:
            print(" ", " ".join(f"{part:16}" for part in row))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            header = (
                f"### {p.speaker} and {p.friend}: {p.charm} for {p.problem} "
                f"({p.place}, {p.conflict}, {p.repair})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
