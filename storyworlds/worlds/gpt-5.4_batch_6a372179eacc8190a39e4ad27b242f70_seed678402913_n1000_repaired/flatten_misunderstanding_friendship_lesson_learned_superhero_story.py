#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/flatten_misunderstanding_friendship_lesson_learned_superhero_story.py
================================================================================================

A small storyworld about two friends playing superheroes, a single misunderstood
word, and the lesson of asking what a friend means before assuming the worst.

The seed asked for:
- the word "flatten"
- a misunderstanding
- friendship
- a lesson learned
- a superhero-story tone

This script models a child and a friend building a pretend rescue world. One
friend says they should flatten an extra cardboard item to make a useful rescue
tool. The hero hears only the scary part and thinks the whole shared build is in
danger. The misunderstanding changes the emotional state, the clarification
repairs it, and the ending image proves the friendship is stronger.

Run it
------
    python storyworlds/worlds/gpt-5.4/flatten_misunderstanding_friendship_lesson_learned_superhero_story.py
    python storyworlds/worlds/gpt-5.4/flatten_misunderstanding_friendship_lesson_learned_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/flatten_misunderstanding_friendship_lesson_learned_superhero_story.py --qa
    python storyworlds/worlds/gpt-5.4/flatten_misunderstanding_friendship_lesson_learned_superhero_story.py --trace
    python storyworlds/worlds/gpt-5.4/flatten_misunderstanding_friendship_lesson_learned_superhero_story.py --asp
    python storyworlds/worlds/gpt-5.4/flatten_misunderstanding_friendship_lesson_learned_superhero_story.py --verify
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

# Make shared result containers importable when this script is run directly from
# the repo root or from inside its nested subdirectory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Project:
    id: str
    build_label: str
    build_phrase: str
    scene: str
    mission: str
    danger: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SourceItem:
    id: str
    label: str
    phrase: str
    size: int
    flattenable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class FlatPlan:
    id: str
    object_label: str
    make_text: str
    use_text: str
    min_size: int
    allowed_projects: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_hurt(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    project = world.entities.get("project")
    if not hero or not friend or not project:
        return []
    if hero.memes["misunderstanding"] < THRESHOLD:
        return []
    sig = ("hurt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["sad"] += 1
    hero.memes["distance"] += 1
    friend.memes["concern"] += 1
    return ["__hurt__"]


def _r_repair(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if not hero or not friend:
        return []
    if hero.memes["misunderstanding"] < THRESHOLD or friend.memes["clarified"] < THRESHOLD:
        return []
    sig = ("repair",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["misunderstanding"] = 0.0
    hero.memes["sad"] = 0.0
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    return ["__repair__"]


def _r_ready(world: World) -> list[str]:
    source = world.entities.get("source")
    tool = world.entities.get("tool")
    project = world.entities.get("project")
    if not source or not tool or not project:
        return []
    if source.meters["flat"] < THRESHOLD or tool.meters["made"] < THRESHOLD:
        return []
    sig = ("ready",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    project.meters["ready"] += 1
    return ["__ready__"]


def _r_complete(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    project = world.entities.get("project")
    if not hero or not friend or not project:
        return []
    if project.meters["ready"] < THRESHOLD or friend.memes["clarified"] < THRESHOLD:
        return []
    sig = ("complete",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    project.meters["complete"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    return ["__complete__"]


CAUSAL_RULES = [
    Rule(name="hurt", tag="emotional", apply=_r_hurt),
    Rule(name="repair", tag="emotional", apply=_r_repair),
    Rule(name="ready", tag="physical", apply=_r_ready),
    Rule(name="complete", tag="resolution", apply=_r_complete),
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
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def source_can_make_tool(source: SourceItem, plan: FlatPlan, project: Project) -> bool:
    return (
        source.flattenable
        and source.size >= plan.min_size
        and project.id in plan.allowed_projects
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for project_id in sorted(setting.affords):
            project = PROJECTS[project_id]
            for source_id, source in SOURCES.items():
                for plan_id, plan in PLANS.items():
                    if source_can_make_tool(source, plan, project):
                        combos.append((setting_id, project_id, source_id, plan_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    project: str
    source: str
    plan: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    grownup: str
    seed: Optional[int] = None


SETTINGS = {
    "playroom": Setting(
        id="playroom",
        place="the playroom",
        detail="Sunlight made bright squares on the rug, and every cardboard wall looked ready for a brave rescue.",
        affords={"skyline", "lab", "bridge"},
    ),
    "backyard": Setting(
        id="backyard",
        place="the backyard",
        detail="A chalk path curled past the grass, and the breeze fluttered every paper flag like a cape.",
        affords={"skyline", "bridge"},
    ),
    "hallway": Setting(
        id="hallway",
        place="the hallway",
        detail="The long runner rug became a secret street, perfect for racing from one emergency to the next.",
        affords={"skyline", "lab"},
    ),
}

PROJECTS = {
    "skyline": Project(
        id="skyline",
        build_label="cardboard city",
        build_phrase="a cardboard city with tall block towers and a tiny shining roof",
        scene="their rescue city",
        mission="save a toy cat from the highest roof",
        danger="the tallest tower was hard to reach",
        ending_image="their hero figures zoomed up the new rescue path and the toy cat stood safe above the city",
        tags={"superhero", "city"},
    ),
    "lab": Project(
        id="lab",
        build_label="villain lab",
        build_phrase="a villain lab with foil tunnels and a red paper alarm",
        scene="their secret hero lab",
        mission="stop the rolling lava marbles before they escaped the tunnel",
        danger="the tunnel needed a strong block at the end",
        ending_image="the bright barrier held firm while the lava marbles stopped exactly where the heroes wanted",
        tags={"superhero", "lab"},
    ),
    "bridge": Project(
        id="bridge",
        build_label="rescue bridge",
        build_phrase="a rescue bridge stretched over a pillow river",
        scene="their rescue crossing",
        mission="carry a stuffed puppy over the wobbling river",
        danger="the bridge needed one smooth way up",
        ending_image="the stuffed puppy rode across while both heroes ran beside the bridge with their capes flying",
        tags={"superhero", "bridge"},
    ),
}

SOURCES = {
    "shipping_box": SourceItem(
        id="shipping_box",
        label="box",
        phrase="an empty shipping box",
        size=3,
        flattenable=True,
        tags={"cardboard"},
    ),
    "cereal_box": SourceItem(
        id="cereal_box",
        label="cereal box",
        phrase="an empty cereal box",
        size=2,
        flattenable=True,
        tags={"cardboard"},
    ),
    "poster_tube": SourceItem(
        id="poster_tube",
        label="poster tube",
        phrase="a strong paper tube",
        size=1,
        flattenable=False,
        tags={"paper_tube"},
    ),
}

PLANS = {
    "ramp": FlatPlan(
        id="ramp",
        object_label="rescue ramp",
        make_text="pressed it flat and taped one end to the tower to make a rescue ramp",
        use_text="so the heroes could race upward instead of wobbling and falling",
        min_size=2,
        allowed_projects={"skyline", "bridge"},
        tags={"ramp"},
    ),
    "shield": FlatPlan(
        id="shield",
        object_label="shield wall",
        make_text="pressed it flat and set it across the tunnel like a shield wall",
        use_text="so the lava marbles would bump safely to a stop",
        min_size=3,
        allowed_projects={"lab"},
        tags={"shield"},
    ),
    "map": FlatPlan(
        id="map",
        object_label="mission map",
        make_text="flattened it into a wide board and drew a mission map across it",
        use_text="so the heroes could see the safe path before they rushed in",
        min_size=2,
        allowed_projects={"skyline", "lab", "bridge"},
        tags={"map"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Maya", "Nora"]
BOY_NAMES = ["Max", "Sam", "Leo", "Finn", "Ben", "Theo", "Jack", "Noah"]


def get_setting(setting_id: str) -> Setting:
    if setting_id not in SETTINGS:
        raise StoryError(f"(Unknown setting: {setting_id})")
    return SETTINGS[setting_id]


def get_project(project_id: str) -> Project:
    if project_id not in PROJECTS:
        raise StoryError(f"(Unknown project: {project_id})")
    return PROJECTS[project_id]


def get_source(source_id: str) -> SourceItem:
    if source_id not in SOURCES:
        raise StoryError(f"(Unknown source item: {source_id})")
    return SOURCES[source_id]


def get_plan(plan_id: str) -> FlatPlan:
    if plan_id not in PLANS:
        raise StoryError(f"(Unknown plan: {plan_id})")
    return PLANS[plan_id]


def explain_rejection(setting: Setting, project: Project, source: SourceItem, plan: FlatPlan) -> str:
    if project.id not in setting.affords:
        return (
            f"(No story: {setting.place} is not a good home for the {project.build_label} setup here. "
            f"Pick a setting that affords {project.id}.)"
        )
    if not source.flattenable:
        return (
            f"(No story: {source.phrase} cannot reasonably be flattened, so it cannot become "
            f"{plan.object_label}. Pick a cardboard box instead.)"
        )
    if source.size < plan.min_size:
        return (
            f"(No story: {source.phrase} is too small to become {plan.object_label}. "
            f"Pick a bigger cardboard item.)"
        )
    if project.id not in plan.allowed_projects:
        return (
            f"(No story: {plan.object_label} does not solve the key problem in the {project.build_label} scenario.)"
        )
    return "(No story: this combination does not make a reasonable superhero build.)"


def predict_misunderstanding(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.memes["misunderstanding"] += 1
    propagate(sim, narrate=False)
    return {
        "sad": hero.memes["sad"],
        "distance": hero.memes["distance"],
    }


def setup_play(world: World, hero: Entity, friend: Entity, project: Project) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After school, {hero.id} and {friend.id} turned {world.setting.place} into {project.scene}. "
        f"Together they had built {project.build_phrase}."
    )
    world.say(world.setting.detail)
    world.say(
        f"Both friends tied towels around their shoulders for capes and announced that today's mission was to {project.mission}."
    )


def need_tool(world: World, hero: Entity, friend: Entity, project: Project) -> None:
    world.say(
        f"But {project.danger}. The game paused for one thoughtful second while the two heroes studied their work."
    )
    if project.id == "skyline":
        world.say(f'"We need one more clever way up," {friend.id} said.')
    elif project.id == "lab":
        world.say(f'"We need something strong to stop the lava marbles," {friend.id} said.')
    else:
        world.say(f'"We need one smoother path for the rescue," {friend.id} said.')


def suggest_flatten(world: World, friend: Entity, source: SourceItem, plan: FlatPlan) -> None:
    friend.memes["idea"] += 1
    world.say(
        f"Then {friend.id} spotted {source.phrase} beside the wall. "
        f'"Wait!" {friend.pronoun().capitalize()} said. "We should flatten it first."'
    )
    world.facts["spoken_word"] = "flatten"
    world.facts["actual_plan_text"] = plan.object_label


def misunderstand(world: World, hero: Entity, friend: Entity, project: Project) -> None:
    pred = predict_misunderstanding(world)
    world.facts["predicted_sad"] = pred["sad"]
    hero.memes["misunderstanding"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} heard only the word \"flatten,\" and {hero.pronoun()} stared at {project.build_label} in shock."
    )
    world.say(
        f'"Flatten it?" {hero.pronoun().capitalize()} echoed. "You want to squash our whole {project.build_label}?"'
    )
    if hero.memes["sad"] >= THRESHOLD:
        world.say(
            f"{hero.id} stepped back and lowered {hero.pronoun('possessive')} cape. "
            f"For a moment, the rescue game felt hurt instead of heroic."
        )


def reveal_hurt(world: World, friend: Entity, hero: Entity) -> None:
    if friend.memes["concern"] >= THRESHOLD:
        world.say(
            f"{friend.id} blinked in surprise. {friend.pronoun().capitalize()} could see at once that {hero.id} thought something precious was about to be ruined."
        )


def clarify(world: World, friend: Entity, hero: Entity, source: SourceItem, plan: FlatPlan, project: Project) -> None:
    friend.memes["clarified"] += 1
    tool = world.get("tool")
    source_ent = world.get("source")
    source_ent.meters["flat"] += 1
    tool.meters["made"] += 1
    world.say(
        f'"No, not the {project.build_label}!" {friend.id} said quickly. '
        f'"I only meant {source.phrase}. If we flatten that, we can make {plan.object_label}."'
    )
    world.say(
        f"{friend.id} knelt down, {plan.make_text}, {plan.use_text}."
    )
    world.say(
        f"The idea was careful, not mean, and it fit the rescue perfectly."
    )
    propagate(world, narrate=False)


def repair_friendship(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f'{hero.id} let out the breath {hero.pronoun()} had been holding. '
        f'"Oh," {hero.pronoun()} said. "I thought you wanted to wreck everything we made."'
    )
    world.say(
        f'"I would never do that," {friend.id} said. "You are my hero partner."'
    )
    world.say(
        f"{hero.id} smiled again. This time, instead of guessing, {hero.pronoun()} listened to the whole idea."
    )


def finish_mission(world: World, hero: Entity, friend: Entity, project: Project, plan: FlatPlan) -> None:
    if project.meters["complete"] < THRESHOLD:
        raise StoryError("(Internal story error: the rescue mission never became complete.)")
    world.say(
        f"Soon both friends were back in motion. They used the new {plan.object_label}, and the mission worked at once."
    )
    world.say(
        f"{project.ending_image}."
    )
    world.say(
        f"At the end, {hero.id} learned that good teammates ask what a friend means before letting one worried word grow too big."
    )


def tell(
    setting: Setting,
    project: Project,
    source: SourceItem,
    plan: FlatPlan,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    grownup: str,
) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    parent = world.add(Entity(id="grownup", kind="character", type=grownup, label="the grown-up", role="grownup"))
    project_ent = world.add(Entity(id="project", type="project", label=project.build_label, phrase=project.build_phrase))
    source_ent = world.add(Entity(id="source", type="source", label=source.label, phrase=source.phrase))
    tool = world.add(Entity(id="tool", type="tool", label=plan.object_label))
    hero.memes["trust"] = 5.0
    friend.memes["trust"] = 5.0
    project_ent.meters["beloved"] = 1.0

    setup_play(world, hero, friend, project)
    need_tool(world, hero, friend, project)

    world.para()
    suggest_flatten(world, friend, source, plan)
    misunderstand(world, hero, friend, project)
    reveal_hurt(world, friend, hero)

    world.para()
    clarify(world, friend, hero, source, plan, project_ent_to_cfg(project_ent, project))
    repair_friendship(world, hero, friend)
    finish_mission(world, hero, friend, project_ent_to_cfg(project_ent, project), plan)

    world.facts.update(
        hero=hero,
        friend=friend,
        grownup=parent,
        project_cfg=project,
        source_cfg=source,
        plan_cfg=plan,
        source=source_ent,
        tool=tool,
        misunderstanding_happened=True,
        repaired=hero.memes["friendship"] >= THRESHOLD,
        lesson=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


def project_ent_to_cfg(project_ent: Entity, project: Project) -> Project:
    _ = project_ent
    return project


KNOWLEDGE = {
    "superhero": [
        (
            "What makes a superhero story feel heroic?",
            "A superhero story usually has a problem, a brave attempt to help, and a clever way to save the day. The hero does not need real powers if they use courage and kindness."
        )
    ],
    "cardboard": [
        (
            "Why can cardboard be useful for pretend play?",
            "Cardboard is light, easy to draw on, and easy to cut or fold into new shapes. That makes it good for building pretend cities, signs, and rescue tools."
        )
    ],
    "flatten": [
        (
            "What does flatten mean?",
            "Flatten means to press something so it becomes flat instead of puffy or tall. A box can be flattened when you push its sides down."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when one person means one thing and another person thinks it means something else. It can make people feel hurt until they explain clearly."
        )
    ],
    "friendship": [
        (
            "How can friends fix a misunderstanding?",
            "Friends can stop, explain what they meant, and listen to each other all the way through. Honest words and calm listening help trust come back."
        )
    ],
    "ramp": [
        (
            "What is a ramp?",
            "A ramp is a sloping path that goes up or down. It helps wheels, toy cars, or people move smoothly instead of climbing a sharp step."
        )
    ],
    "shield": [
        (
            "What does a shield do?",
            "A shield blocks something and protects what is behind it. In play, a shield can stop pretend danger from rushing forward."
        )
    ],
    "map": [
        (
            "What is a map for?",
            "A map shows where things are and which way to go. It helps people plan a safe path before they start moving."
        )
    ],
}
KNOWLEDGE_ORDER = ["superhero", "cardboard", "flatten", "misunderstanding", "friendship", "ramp", "shield", "map"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    project = f["project_cfg"]
    source = f["source_cfg"]
    plan = f["plan_cfg"]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the word "flatten" and ends with a friendship lesson.',
        f"Tell a gentle superhero story where {hero.label} misunderstands what {friend.label} means by saying they should flatten {source.phrase}, and the mistake is repaired with a clear explanation.",
        f"Write a story about two friends building a {project.build_label}, feeling hurt for a moment, and then using a flattened cardboard piece to make {plan.object_label} and save the day."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    project = f["project_cfg"]
    source = f["source_cfg"]
    plan = f["plan_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {hero.label} and {friend.label}, who were pretending to be superheroes together. They were building {project.build_phrase} in {world.setting.place}."
        ),
        (
            "What problem did the heroes need to solve in their game?",
            f"They wanted to {project.mission}. The trouble was that {project.danger}, so they needed one more clever tool."
        ),
        (
            f"Why did {hero.label} feel hurt when {friend.label} said the word \"flatten\"?",
            f"{hero.label} thought {friend.label} wanted to squash the whole {project.build_label}. That misunderstanding made the shared game feel unsafe for a moment, even though {friend.label} meant only the extra cardboard item."
        ),
        (
            f"What did {friend.label} really want to flatten?",
            f"{friend.label} meant {source.phrase}, not the whole build. The flat cardboard would become {plan.object_label}, which solved the mission problem."
        ),
    ]
    if f.get("repaired"):
        qa.append(
            (
                "How did the friends fix the misunderstanding?",
                f"They stopped and explained the idea clearly. When {hero.label} heard the full plan, {hero.pronoun()} understood that {friend.label} was trying to help the game, not ruin it."
            )
        )
    if f.get("lesson"):
        qa.append(
            (
                "What lesson did the hero learn at the end?",
                f"{hero.label} learned to ask what a friend means before assuming the worst. Listening all the way through helped the friendship feel strong again."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"superhero", "flatten", "misunderstanding", "friendship"}
    tags |= set(f["project_cfg"].tags)
    tags |= set(f["source_cfg"].tags)
    tags |= set(f["plan_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if ent.label:
            bits.append(f"label={ent.label!r}")
        if ent.phrase:
            bits.append(f"phrase={ent.phrase!r}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="playroom",
        project="skyline",
        source="shipping_box",
        plan="ramp",
        hero_name="Lily",
        hero_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        grownup="mother",
    ),
    StoryParams(
        setting="hallway",
        project="lab",
        source="shipping_box",
        plan="shield",
        hero_name="Sam",
        hero_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        grownup="father",
    ),
    StoryParams(
        setting="backyard",
        project="bridge",
        source="cereal_box",
        plan="map",
        hero_name="Ava",
        hero_gender="girl",
        friend_name="Leo",
        friend_gender="boy",
        grownup="mother",
    ),
]


ASP_RULES = r"""
usable_source(S) :- source(S), flattenable(S).
fits(Source, Plan) :- usable_source(Source), size(Source, SZ), min_size(Plan, Need), SZ >= Need.
solves(Project, Plan) :- allowed(Project, Plan).
valid(Setting, Project, Source, Plan) :-
    affords(Setting, Project),
    fits(Source, Plan),
    solves(Project, Plan).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for project_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, project_id))
    for project_id in PROJECTS:
        lines.append(asp.fact("project", project_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        if source.flattenable:
            lines.append(asp.fact("flattenable", source_id))
        lines.append(asp.fact("size", source_id, source.size))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("min_size", plan_id, plan.min_size))
        for project_id in sorted(plan.allowed_projects):
            lines.append(asp.fact("allowed", project_id, plan_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero misunderstanding repaired by friendship and clear words."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting is not None and args.project is not None:
        setting = get_setting(args.setting)
        project = get_project(args.project)
        if args.project not in setting.affords:
            source = get_source(args.source) if args.source else next(iter(SOURCES.values()))
            plan = get_plan(args.plan) if args.plan else next(iter(PLANS.values()))
            raise StoryError(explain_rejection(setting, project, source, plan))
    if args.project is not None and args.source is not None and args.plan is not None:
        project = get_project(args.project)
        source = get_source(args.source)
        plan = get_plan(args.plan)
        setting = get_setting(args.setting) if args.setting else next(iter(SETTINGS.values()))
        if not source_can_make_tool(source, plan, project):
            raise StoryError(explain_rejection(setting, project, source, plan))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.project is None or combo[1] == args.project)
        and (args.source is None or combo[2] == args.source)
        and (args.plan is None or combo[3] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, project_id, source_id, plan_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero or pick_name(rng, hero_gender)
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    friend_name = args.friend or pick_name(rng, friend_gender, avoid=hero_name)
    grownup = args.grownup or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        project=project_id,
        source=source_id,
        plan=plan_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        grownup=grownup,
    )


def generate(params: StoryParams) -> StorySample:
    setting = get_setting(params.setting)
    project = get_project(params.project)
    source = get_source(params.source)
    plan = get_plan(params.plan)
    if not source_can_make_tool(source, plan, project) or project.id not in setting.affords:
        raise StoryError(explain_rejection(setting, project, source, plan))

    world = tell(
        setting=setting,
        project=project,
        source=source,
        plan=plan,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        grownup=params.grownup,
    )
    story = world.render()
    if "{" in story or "}" in story:
        raise StoryError("(Internal story error: unresolved template marker reached story text.)")
    return StorySample(
        params=params,
        story=story,
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
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        default_params.seed = 123
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print(f"FAILED: resolve_params smoke test raised StoryError: {err}")

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            sink = io.StringIO()
            with redirect_stdout(sink):
                emit(sample, trace=False, qa=False, header="")
        except Exception as err:
            rc = 1
            print(f"FAILED: generation smoke test crashed for {params}: {err}")
            break
    else:
        print(f"OK: generation smoke test passed on {len(smoke_cases)} scenarios.")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, project, source, plan) combos:\n")
        for setting_id, project_id, source_id, plan_id in combos:
            print(f"  {setting_id:9} {project_id:8} {source_id:12} {plan_id}")
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
            header = f"### {p.hero_name} & {p.friend_name}: {p.project} with {p.source} -> {p.plan}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
