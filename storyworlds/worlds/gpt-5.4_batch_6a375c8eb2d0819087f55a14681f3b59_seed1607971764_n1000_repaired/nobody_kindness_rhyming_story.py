#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/nobody_kindness_rhyming_story.py
===========================================================

A standalone story world for gentle, child-facing rhyming stories about
kindness: one child notices another left out, tries a fitting kind act, and the
group changes so that nobody is left alone.

This world models a small social domain rather than a physical danger domain.
Entities still carry physical ``meters`` and emotional ``memes``. The simulated
state decides the prose:

- a game is already happening
- one child is left out for a concrete reason
- a helper notices and tries a specific kindness method
- if the method actually fits the reason, belonging rises and the game changes
- the ending image proves that nobody is left out

Reasonableness gate
-------------------
Not every kind act honestly solves every problem. The world refuses mismatches.

Examples:
- ``share_tool`` only works when the left-out child lacks a needed item.
- ``slow_song`` only works when the activity is too fast to join comfortably.
- ``make_room`` only works when the problem is that the space feels full.

Run it
------
    python storyworlds/worlds/gpt-5.4/nobody_kindness_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/nobody_kindness_rhyming_story.py --scene chalk_path --problem no_item --method share_tool
    python storyworlds/worlds/gpt-5.4/nobody_kindness_rhyming_story.py --scene chalk_path --problem no_item --method make_room
    python storyworlds/worlds/gpt-5.4/nobody_kindness_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/nobody_kindness_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/nobody_kindness_rhyming_story.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
    traits: list[str] = field(default_factory=list)
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
class Scene:
    id: str
    place: str
    group_noun: str
    opening: str
    game_line: str
    sound_line: str
    need_label: str
    need_phrase: str
    shared_item: str
    rhyme_end: str
    can_share: bool = False
    can_slow: bool = False
    can_make_room: bool = False
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
    label: str
    child_line: str
    cause_line: str
    need_kind: str
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
class Method:
    id: str
    label: str
    solves: str
    offer_line: str
    action_line: str
    result_line: str
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


def kindness_fits(scene: Scene, problem: Problem, method: Method) -> bool:
    if method.solves != problem.need_kind:
        return False
    if method.id == "share_tool":
        return scene.can_share
    if method.id == "slow_song":
        return scene.can_slow
    if method.id == "make_room":
        return scene.can_make_room
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for scene_id, scene in SCENES.items():
        for problem_id, problem in PROBLEMS.items():
            for method_id, method in METHODS.items():
                if kindness_fits(scene, problem, method):
                    combos.append((scene_id, problem_id, method_id))
    return combos


def explain_rejection(scene: Scene, problem: Problem, method: Method) -> str:
    if method.solves != problem.need_kind:
        return (
            f"(No story: {method.label} answers a different problem. "
            f"This child is left out because {problem.label}, so the kindness needs "
            f"to match that reason.)"
        )
    if method.id == "share_tool" and not scene.can_share:
        return (
            f"(No story: in {scene.place}, the game does not center on sharing "
            f"{scene.shared_item}, so sharing a tool is not the honest fix.)"
        )
    if method.id == "slow_song" and not scene.can_slow:
        return (
            f"(No story: the activity in {scene.place} is not something the group "
            f"can solve by slowing the song or pace.)"
        )
    if method.id == "make_room" and not scene.can_make_room:
        return (
            f"(No story: the problem in {scene.place} is not really about space, "
            f"so making room would not solve it.)"
        )
    return "(No story: that scene, problem, and kindness method do not fit together.)"


def tell(
    scene: Scene,
    problem: Problem,
    method: Method,
    *,
    helper_name: str = "Mina",
    helper_gender: str = "girl",
    leftout_name: str = "Owen",
    leftout_gender: str = "boy",
    group_count: int = 3,
) -> World:
    world = World()
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            label=helper_name,
            attrs={"noticed": False},
        )
    )
    leftout = world.add(
        Entity(
            id=leftout_name,
            kind="character",
            type=leftout_gender,
            role="leftout",
            label=leftout_name,
            attrs={"joined": False},
        )
    )
    group = world.add(
        Entity(
            id="group",
            kind="thing",
            type="group",
            label="the group",
            attrs={"count": group_count},
        )
    )

    helper.memes["kindness"] = 2.0
    helper.memes["belonging"] = 1.0
    leftout.memes["lonely"] = 2.0
    leftout.memes["hope"] = 0.0
    leftout.memes["belonging"] = 0.0
    group.memes["together"] = 1.0
    group.meters["rhythm"] = 1.0

    world.facts.update(
        scene=scene,
        problem=problem,
        method=method,
        helper=helper,
        leftout=leftout,
        group=group,
        fit=kindness_fits(scene, problem, method),
    )

    world.say(
        f"In {scene.place}, where bright feet skipped {scene.rhyme_end}, "
        f"{scene.opening}"
    )
    world.say(scene.game_line)
    world.say(scene.sound_line)

    world.para()
    world.say(
        f"But {leftout.id} stood still by the side with a sigh, "
        f"and {problem.child_line}"
    )
    world.say(problem.cause_line)
    world.say(
        f"{helper.id} looked over and noticed why. "
        f"{helper.pronoun('subject').capitalize()} thought, "
        f'"Kind hearts can help, so nobody has to stand by."'
    )
    helper.attrs["noticed"] = True
    helper.memes["care"] += 1.0
    leftout.memes["hope"] += 1.0

    world.para()
    world.say(
        f'So {helper.id} smiled and softly said, "{method.offer_line}"'
    )
    world.say(method.action_line)

    leftout.memes["lonely"] = 0.0
    leftout.memes["belonging"] += 2.0
    leftout.attrs["joined"] = True
    helper.memes["joy"] += 1.0
    group.memes["together"] += 1.0

    if problem.id == "no_item":
        leftout.meters["has_need"] += 1.0
        helper.meters["shared"] += 1.0
    elif problem.id == "too_fast":
        group.meters["rhythm"] = 0.5
        leftout.meters["steady"] += 1.0
    elif problem.id == "no_space":
        group.meters["space_open"] += 1.0

    world.say(method.result_line)
    world.say(
        f"Soon {leftout.id} was in the game, not out in the cold, "
        f"and laughter came back in a bright, bouncing fold."
    )

    world.para()
    closing = {
        "chalk_path": (
            f"They drew and they hopped down the sun-sparked lane, "
            f"sharing the {scene.shared_item} again and again."
        ),
        "clap_song": (
            "They clapped with a beat that was gentle and clear, "
            "and every small voice had a place to come near."
        ),
        "story_circle": (
            "They scooted in close with a giggle and grin, "
            "till every small shoulder was tucked safely in."
        ),
    }[scene.id]
    world.say(closing)
    world.say(
        f"That is how kindness, so simple and true, "
        f"made room for one child and then warmed up the crew. "
        f"At the end of the play, this much was plain to see: "
        f"nobody was left out, and all felt glad and free."
    )

    world.facts.update(
        joined=leftout.attrs["joined"],
        nobody_left_out=leftout.memes["belonging"] >= THRESHOLD,
        shared=helper.meters["shared"] >= THRESHOLD,
        rhythm_slow=group.meters["rhythm"] < THRESHOLD,
        room_made=group.meters["space_open"] >= THRESHOLD,
    )
    return world


SCENES = {
    "chalk_path": Scene(
        id="chalk_path",
        place="the sunny schoolyard",
        group_noun="children",
        opening="a chalk path curled like a ribbon of light.",
        game_line="A few children were hopping in squares, taking turns with delight.",
        sound_line="Tap-tap went the toes, and the chalk made the stones look bright.",
        need_label="chalk",
        need_phrase="a bit of chalk to draw a turn",
        shared_item="chalk",
        rhyme_end="in a happy row",
        can_share=True,
        can_slow=False,
        can_make_room=False,
        tags={"chalk", "sharing"},
    ),
    "clap_song": Scene(
        id="clap_song",
        place="the music corner",
        group_noun="children",
        opening="a clapping song twirled through the air, quick and light.",
        game_line="A small ring of children was singing and clapping in time.",
        sound_line="Clap-clap went the hands in a neat little rhyme.",
        need_label="beat",
        need_phrase="a slower beat to step into",
        shared_item="turn",
        rhyme_end="with a jingling chime",
        can_share=False,
        can_slow=True,
        can_make_room=False,
        tags={"music", "rhythm"},
    ),
    "story_circle": Scene(
        id="story_circle",
        place="the library rug",
        group_noun="children",
        opening="a round story circle was cozy and snug.",
        game_line="A little cluster of children sat listening close to a tale.",
        sound_line="Soft page-whispers fluttered like a tiny paper sail.",
        need_label="space",
        need_phrase="a bit of room on the rug",
        shared_item="spot",
        rhyme_end="near the patchwork rug",
        can_share=False,
        can_slow=False,
        can_make_room=True,
        tags={"books", "circle"},
    ),
}

PROBLEMS = {
    "no_item": Problem(
        id="no_item",
        label="the child lacks the needed item",
        child_line="his hands were empty, and his turn could not begin.",
        cause_line="He needed a little chalk of his own, but he did not have any in hand.",
        need_kind="share",
        tags={"sharing"},
    ),
    "too_fast": Problem(
        id="too_fast",
        label="the game is moving too fast",
        child_line="the beat zipped by so fast that he could not step in.",
        cause_line="His feet were ready, but the claps came quick, and the song ran ahead of his plan.",
        need_kind="slow",
        tags={"patience"},
    ),
    "no_space": Problem(
        id="no_space",
        label="the group feels too full",
        child_line="there was no cozy place for him to tuck himself in.",
        cause_line="The circle had closed up snug, and he did not know where to land.",
        need_kind="room",
        tags={"welcome"},
    ),
}

METHODS = {
    "share_tool": Method(
        id="share_tool",
        label="sharing the needed tool",
        solves="share",
        offer_line="You can use my chalk with me; one piece is enough for two.",
        action_line="Then the chalk changed hands with a friendly white streak, and the path grew longer for each little shoe.",
        result_line="The squares reached farther, and Owen could hop with the rest of the line.",
        tags={"sharing", "chalk"},
    ),
    "slow_song": Method(
        id="slow_song",
        label="slowing the song",
        solves="slow",
        offer_line="Let's clap it more slowly, so you can join in too.",
        action_line="So the ring took a breath and softened the beat, making room in the rhythm instead of racing it through.",
        result_line="The song grew steadier, and Owen found the clap and the step in time.",
        tags={"patience", "music"},
    ),
    "make_room": Method(
        id="make_room",
        label="making room",
        solves="room",
        offer_line="Scoot close to me; we can make a small place for you.",
        action_line="So knees tucked in, elbows folded, and the circle grew kinder by shifting a few.",
        result_line="A warm little gap opened up, and Owen could sit where the story-shine fell.",
        tags={"welcome", "circle"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Ruby", "Nora", "Ella", "Poppy", "Zoe", "Ava"]
BOY_NAMES = ["Owen", "Milo", "Ben", "Theo", "Finn", "Leo", "Eli", "Sam"]


@dataclass
class StoryParams:
    scene: str
    problem: str
    method: str
    helper_name: str
    helper_gender: str
    leftout_name: str
    leftout_gender: str
    group_count: int = 3
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
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting someone else use something with you instead of keeping it only for yourself. It can help another child join in and feel included.",
        )
    ],
    "patience": [
        (
            "What does patience look like in a game?",
            "Patience means slowing down, waiting, or giving someone time to catch up. That can turn a hard moment into a friendly one.",
        )
    ],
    "welcome": [
        (
            "How can you make someone feel welcome?",
            "You can move over, invite them in, and speak kindly. Small actions can show that they belong with the group.",
        )
    ],
    "chalk": [
        (
            "What is chalk used for?",
            "Chalk can be used to draw lines or boxes on the ground. Children often use it for games and pictures outside.",
        )
    ],
    "music": [
        (
            "Why can slowing a song help someone join?",
            "A slower beat is easier to hear and follow. That gives a child time to match the rhythm and feel confident.",
        )
    ],
    "circle": [
        (
            "Why does making room matter in a circle?",
            "A circle only feels friendly when everyone has a place in it. Scooting over can show that there is space for another person too.",
        )
    ],
}
KNOWLEDGE_ORDER = ["sharing", "patience", "welcome", "chalk", "music", "circle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    helper = f["helper"]
    leftout = f["leftout"]
    scene = f["scene"]
    problem = f["problem"]
    method = f["method"]
    return [
        (
            f'Write a short rhyming story for a 3-to-5-year-old about kindness, '
            f'where a child notices another child left out in {scene.place}, and include the word "nobody".'
        ),
        (
            f"Tell a gentle rhyming story where {helper.id} sees that {leftout.id} is left out because "
            f"{problem.label}, then helps by {method.label}."
        ),
        (
            f"Write a simple kindness poem-story with a beginning, a small social problem, "
            f"and an ending where nobody is left out."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    helper = f["helper"]
    leftout = f["leftout"]
    scene = f["scene"]
    problem = f["problem"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {helper.id}, who noticed another child, and {leftout.id}, who was standing outside the game. The story is also about the whole group learning a kinder way to play.",
        ),
        (
            f"Why was {leftout.id} left out at first?",
            f"{leftout.id} was left out because {problem.label}. That concrete problem kept {leftout.pronoun('object')} from joining the others right away.",
        ),
        (
            f"What did {helper.id} notice?",
            f"{helper.id} noticed that {leftout.id} was not joining in and understood why. That mattered because kindness in this story begins with paying attention before acting.",
        ),
        (
            f"How did {helper.id} help {leftout.id}?",
            f"{helper.id} helped by {method.label}. The help worked because it matched the real problem instead of only sounding nice.",
        ),
    ]
    if f.get("nobody_left_out"):
        qa.append(
            (
                "What changed by the end of the story?",
                f"By the end, {leftout.id} was part of the game and nobody was left out. The group changed because one kind action spread into a more welcoming way to play.",
            )
        )
    if f.get("shared"):
        qa.append(
            (
                "Why did sharing help in this story?",
                f"Sharing helped because {leftout.id} needed the same tool the game used. Once the chalk was shared, {leftout.pronoun('subject')} could take a real turn instead of only watching.",
            )
        )
    elif f.get("rhythm_slow"):
        qa.append(
            (
                "Why did slowing down help in this story?",
                f"Slowing down helped because the fast rhythm was the problem. When the beat became gentler, {leftout.id} had time to hear it and join confidently.",
            )
        )
    elif f.get("room_made"):
        qa.append(
            (
                "Why did making room help in this story?",
                f"Making room helped because {leftout.id} needed an actual place in the circle. Once the children shifted over, the welcome became visible and easy to trust.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["problem"].tags) | set(world.facts["method"].tags) | set(world.facts["scene"].tags)
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
        attrs = {k: v for k, v in ent.attrs.items() if v}
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if attrs:
            parts.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(parts)}")
    lines.append(f"  facts: joined={world.facts.get('joined')} nobody_left_out={world.facts.get('nobody_left_out')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        scene="chalk_path",
        problem="no_item",
        method="share_tool",
        helper_name="Mina",
        helper_gender="girl",
        leftout_name="Owen",
        leftout_gender="boy",
        group_count=3,
    ),
    StoryParams(
        scene="clap_song",
        problem="too_fast",
        method="slow_song",
        helper_name="Theo",
        helper_gender="boy",
        leftout_name="Ruby",
        leftout_gender="girl",
        group_count=4,
    ),
    StoryParams(
        scene="story_circle",
        problem="no_space",
        method="make_room",
        helper_name="Lila",
        helper_gender="girl",
        leftout_name="Finn",
        leftout_gender="boy",
        group_count=5,
    ),
]


ASP_RULES = r"""
needs(no_item,share).
needs(too_fast,slow).
needs(no_space,room).

scene_can(Scene,share) :- can_share(Scene).
scene_can(Scene,slow)  :- can_slow(Scene).
scene_can(Scene,room)  :- can_make_room(Scene).

fits(Scene, Problem, Method) :-
    scene(Scene), problem(Problem), method(Method),
    solves(Method, Need), needs(Problem, Need), scene_can(Scene, Need).

#show fits/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for scene_id, scene in SCENES.items():
        lines.append(asp.fact("scene", scene_id))
        if scene.can_share:
            lines.append(asp.fact("can_share", scene_id))
        if scene.can_slow:
            lines.append(asp.fact("can_slow", scene_id))
        if scene.can_make_room:
            lines.append(asp.fact("can_make_room", scene_id))
    for problem_id in PROBLEMS:
        lines.append(asp.fact("problem", problem_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("solves", method_id, method.solves))
    return "\n".join(lines)


def asp_program(show: str = "#show fits/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show fits/3."))
    return sorted(set(asp.atoms(model, "fits")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "nobody" not in sample.story.lower():
            raise StoryError("smoke test failed: story missing or lacks required word 'nobody'")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming kindness story world: one child notices another left out and helps in a fitting way."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper-name")
    ap.add_argument("--leftout-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--leftout-gender", choices=["girl", "boy"])
    ap.add_argument("--group-count", type=int, choices=[2, 3, 4, 5])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.problem and args.method:
        scene = SCENES[args.scene]
        problem = PROBLEMS[args.problem]
        method = METHODS[args.method]
        if not kindness_fits(scene, problem, method):
            raise StoryError(explain_rejection(scene, problem, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.problem is None or combo[1] == args.problem)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, problem_id, method_id = rng.choice(sorted(combos))
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    leftout_gender = args.leftout_gender or rng.choice(["girl", "boy"])
    helper_name = args.helper_name or _pick_name(rng, helper_gender)
    leftout_name = args.leftout_name or _pick_name(rng, leftout_gender, avoid=helper_name)
    group_count = args.group_count if args.group_count is not None else rng.choice([3, 4, 5])

    return StoryParams(
        scene=scene_id,
        problem=problem_id,
        method=method_id,
        helper_name=helper_name,
        helper_gender=helper_gender,
        leftout_name=leftout_name,
        leftout_gender=leftout_gender,
        group_count=group_count,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        scene = SCENES[params.scene]
        problem = PROBLEMS[params.problem]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(No story: unknown parameter value {err.args[0]!r}.)") from None

    if not kindness_fits(scene, problem, method):
        raise StoryError(explain_rejection(scene, problem, method))

    if params.helper_name == params.leftout_name:
        raise StoryError("(No story: helper and left-out child need different names.)")

    world = tell(
        scene=scene,
        problem=problem,
        method=method,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        leftout_name=params.leftout_name,
        leftout_gender=params.leftout_gender,
        group_count=params.group_count,
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
        print(asp_program("#show fits/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (scene, problem, method) combos:\n")
        for scene_id, problem_id, method_id in combos:
            print(f"  {scene_id:12} {problem_id:10} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.scene} / {p.problem} / {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
