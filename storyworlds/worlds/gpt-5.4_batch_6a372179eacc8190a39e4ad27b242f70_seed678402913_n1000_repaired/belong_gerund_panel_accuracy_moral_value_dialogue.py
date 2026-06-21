#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/belong_gerund_panel_accuracy_moral_value_dialogue.py
================================================================================

A small slice-of-life storyworld about a child making a school display panel.

The seed words shape the domain directly:
- "belong-gerund" appears as "belonging"
- "panel" is the display panel for open house
- "accuracy" is the core value under pressure

The story model is simple and state-driven:
a child prepares a panel for class open house, writes a fact about a small
project, feels proud and nervous, and then a friend notices the number may be
wrong. If the child used a good checking tool, the panel is already accurate and
they calmly confirm it. If the child guessed, the friend helps check with a
compatible tool, and the child chooses honesty and fixes the panel before the
families arrive. The ending image shows that truthfulness strengthens the
child's feeling of belonging in the class.

Reasonableness constraint
-------------------------
Not every project can be checked with every tool. A counting board helps with
counting objects, while a ruler helps with measuring length. The world refuses
stories where the chosen verification tool cannot honestly establish accuracy.

Run it
------
    python storyworlds/worlds/gpt-5.4/belong_gerund_panel_accuracy_moral_value_dialogue.py
    python storyworlds/worlds/gpt-5.4/belong_gerund_panel_accuracy_moral_value_dialogue.py --project beans --tool ruler
    python storyworlds/worlds/gpt-5.4/belong_gerund_panel_accuracy_moral_value_dialogue.py --project shells --tool ruler
    python storyworlds/worlds/gpt-5.4/belong_gerund_panel_accuracy_moral_value_dialogue.py --all
    python storyworlds/worlds/gpt-5.4/belong_gerund_panel_accuracy_moral_value_dialogue.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/belong_gerund_panel_accuracy_moral_value_dialogue.py --verify
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
    traits: tuple = field(default_factory=tuple)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher_f"}
        male = {"boy", "father", "man", "teacher_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "teacher_f": "teacher",
            "teacher_m": "teacher",
        }.get(self.type, self.label or self.type)


@dataclass
class Project:
    id: str
    label: str
    phrase: str
    measure_kind: str
    amount: int
    unit: str
    finding_text: str
    setup_text: str
    verify_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    measures: set[str] = field(default_factory=set)
    sense: int = 2
    action_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    id: str
    place: str
    room_detail: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = copy.deepcopy(self.facts)
        return other


def _r_mismatch_worry(world: World) -> list[str]:
    panel = world.get("panel")
    child = world.get("child")
    if panel.meters["mismatch"] < THRESHOLD:
        return []
    sig = ("mismatch_worry", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    return []


def _r_truth_pride(world: World) -> list[str]:
    panel = world.get("panel")
    child = world.get("child")
    if panel.meters["accurate"] < THRESHOLD or child.memes["honesty"] < THRESHOLD:
        return []
    sig = ("truth_pride", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["pride"] += 1
    child.memes["belonging"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="mismatch_worry", tag="emotional", apply=_r_mismatch_worry),
    Rule(name="truth_pride", tag="emotional", apply=_r_truth_pride),
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
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PROJECTS = {
    "beans": Project(
        id="beans",
        label="bean sprouts",
        phrase="three paper cups of bean sprouts",
        measure_kind="length",
        amount=12,
        unit="centimeters",
        finding_text="the tallest bean sprout was 12 centimeters high",
        setup_text="small green bean sprouts leaned toward the window",
        verify_text="checked the tallest sprout from the soil line to the tip",
        tags={"plants", "measure", "accuracy"},
    ),
    "sunflower": Project(
        id="sunflower",
        label="sunflower stem",
        phrase="a sunflower stem in a jar",
        measure_kind="length",
        amount=18,
        unit="centimeters",
        finding_text="the sunflower stem was 18 centimeters tall",
        setup_text="a sunny yellow flower head nodded above the jar",
        verify_text="measured the stem carefully from the table to the flower head",
        tags={"plants", "measure", "accuracy"},
    ),
    "shells": Project(
        id="shells",
        label="shells",
        phrase="a tray of beach shells",
        measure_kind="count",
        amount=14,
        unit="shells",
        finding_text="the tray held 14 shells",
        setup_text="striped and pearly shells lay in neat little rows",
        verify_text="counted each shell once and slid it to the finished side",
        tags={"count", "accuracy"},
    ),
    "buttons": Project(
        id="buttons",
        label="buttons",
        phrase="a dish of bright buttons",
        measure_kind="count",
        amount=16,
        unit="buttons",
        finding_text="the dish held 16 buttons",
        setup_text="red, blue, and yellow buttons shone like tiny coins",
        verify_text="counted the buttons into two tidy groups",
        tags={"count", "accuracy"},
    ),
}

TOOLS = {
    "ruler": Tool(
        id="ruler",
        label="ruler",
        phrase="a clear ruler",
        measures={"length"},
        sense=3,
        action_text="lined up the ruler and looked closely at the marks",
        tags={"ruler", "measure"},
    ),
    "tape": Tool(
        id="tape",
        label="measuring tape",
        phrase="a soft measuring tape",
        measures={"length"},
        sense=3,
        action_text="held the tape steady and read the number at the edge",
        tags={"tape", "measure"},
    ),
    "counting_board": Tool(
        id="counting_board",
        label="counting board",
        phrase="a little counting board",
        measures={"count"},
        sense=3,
        action_text="moved each piece to a new square so none would be counted twice",
        tags={"count", "board"},
    ),
    "sticky_notes": Tool(
        id="sticky_notes",
        label="sticky note checklist",
        phrase="a sticky note checklist",
        measures={"count"},
        sense=2,
        action_text="tapped each item and marked one neat box for it",
        tags={"count", "checklist"},
    ),
    "eyeballing": Tool(
        id="eyeballing",
        label="quick glance",
        phrase="just a quick glance",
        measures=set(),
        sense=1,
        action_text="looked quickly and hoped the number was close enough",
        tags={"guess"},
    ),
}

SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the classroom",
        room_detail="The room smelled faintly of crayons, paper, and damp jackets drying by the door.",
        ending_image="Families drifted past the desks, and the corrected panel stood straight under the warm classroom lights.",
        tags={"school", "classroom"},
    ),
    "library": Setting(
        id="library",
        place="the school library",
        room_detail="The library was hushed except for soft chair-scrapes and the whisper of pages turning.",
        ending_image="Parents walked between the low shelves, and the neat panel looked calm and true beside the books.",
        tags={"school", "library"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "Lucy", "Anna"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Theo", "Eli", "Noah", "Jack"]
TRAITS = ["careful", "eager", "thoughtful", "shy", "curious", "steady"]


def tool_fits(project: Project, tool: Tool) -> bool:
    return project.measure_kind in tool.measures


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for project_id, project in PROJECTS.items():
            for tool_id, tool in TOOLS.items():
                if tool.sense >= SENSE_MIN and tool_fits(project, tool):
                    combos.append((setting_id, project_id, tool_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    project: str
    tool: str
    method: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    teacher_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="classroom",
        project="beans",
        tool="ruler",
        method="guess",
        child_name="Lily",
        child_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        teacher_type="teacher_f",
        trait="careful",
    ),
    StoryParams(
        setting="library",
        project="shells",
        tool="counting_board",
        method="guess",
        child_name="Max",
        child_gender="boy",
        friend_name="Nora",
        friend_gender="girl",
        teacher_type="teacher_m",
        trait="thoughtful",
    ),
    StoryParams(
        setting="classroom",
        project="sunflower",
        tool="tape",
        method="check",
        child_name="Ava",
        child_gender="girl",
        friend_name="Leo",
        friend_gender="boy",
        teacher_type="teacher_f",
        trait="steady",
    ),
    StoryParams(
        setting="library",
        project="buttons",
        tool="sticky_notes",
        method="check",
        child_name="Theo",
        child_gender="boy",
        friend_name="Lucy",
        friend_gender="girl",
        teacher_type="teacher_m",
        trait="eager",
    ),
]


def actual_written_value(project: Project, method: str) -> int:
    if method == "check":
        return project.amount
    return max(1, project.amount + 2)


def predict_panel(world: World, project: Project, method: str, tool: Tool) -> dict:
    sim = world.copy()
    panel = sim.get("panel")
    panel.attrs["written_value"] = actual_written_value(project, method)
    if panel.attrs["written_value"] == project.amount:
        panel.meters["accurate"] = 1
    else:
        panel.meters["mismatch"] = 1
    if tool_fits(project, tool):
        panel.attrs["verified_value"] = project.amount
    return {
        "accurate": panel.attrs["written_value"] == project.amount,
        "can_verify": tool_fits(project, tool),
        "written_value": panel.attrs["written_value"],
    }


def introduce(world: World, child: Entity, friend: Entity, teacher: Entity, project: Project) -> None:
    child.memes["belonging"] += 1
    world.say(
        f"After lunch, {child.id} stayed in {world.setting.place} to finish a display panel for class open house."
    )
    world.say(world.setting.room_detail)
    world.say(
        f"{child.id}'s project used {project.phrase}, and {friend.id} worked at the next table while their {teacher.label_word} pinned student work along the wall."
    )


def setup_panel(world: World, child: Entity, project: Project) -> None:
    world.say(
        f"On the panel, {child.id} had drawn a neat title in blue marker. Beside it, {project.setup_text}."
    )
    world.say(
        f"{child.pronoun().capitalize()} wanted the panel to look so good that families would stop and smile."
    )


def write_claim(world: World, child: Entity, panel: Entity, project: Project, method: str) -> None:
    written = actual_written_value(project, method)
    panel.attrs["written_value"] = written
    panel.attrs["actual_value"] = project.amount
    if method == "check":
        panel.meters["accurate"] = 1
        world.say(
            f"Before writing the final sentence, {child.id} checked the number carefully and wrote that {project.finding_text}."
        )
    else:
        panel.meters["mismatch"] = 1
        child.memes["rush"] += 1
        world.say(
            f"The room was getting busy, and {child.id} hurried. {child.pronoun().capitalize()} guessed at the number and wrote it onto the panel in a dark, hopeful line."
        )
    panel.meters["ready"] += 1
    propagate(world, narrate=False)


def notice_problem(world: World, friend: Entity, child: Entity, panel: Entity, project: Project) -> None:
    friend.memes["care"] += 1
    if panel.meters["mismatch"] >= THRESHOLD:
        world.say(
            f'{friend.id} leaned over and read the panel. "Are you sure that is right?" {friend.pronoun()} asked. "It looked different when we checked the table earlier."'
        )
        world.say(
            f'{child.id} looked at the sentence again, and {child.pronoun("possessive")} stomach gave a small nervous flip.'
        )
    else:
        world.say(
            f'{friend.id} read the panel and smiled. "That looks good," {friend.pronoun()} said. "Do you want to check it once more, just to be sure?"'
        )


def verify_panel(world: World, child: Entity, friend: Entity, panel: Entity, project: Project, tool: Tool) -> None:
    if not tool_fits(project, tool):
        raise StoryError(explain_rejection(project, tool))
    panel.attrs["tool"] = tool.id
    world.say(
        f'{child.id} nodded. Together they used {tool.phrase}. {tool.action_text}.'
    )
    world.say(
        f"They {project.verify_text}."
    )
    panel.attrs["verified_value"] = project.amount
    if panel.attrs["written_value"] == project.amount:
        child.memes["calm"] += 1
        world.say(
            f'"It matches," {friend.id} said, and {child.id} let out a slow breath.'
        )
    else:
        panel.meters["accurate"] = 1
        panel.meters["mismatch"] = 0
        child.memes["honesty"] += 1
        child.memes["worry"] = 0
        world.say(
            f'"Oh," {child.id} said softly. "I guessed."'
        )
        world.say(
            f'"Then let\'s fix it," {friend.id} said. "{project.amount} is the true number, and accuracy matters more than a fast guess."'
        )
        panel.attrs["written_value"] = project.amount
        panel.meters["revised"] += 1
        propagate(world, narrate=False)


def teacher_response(world: World, teacher: Entity, child: Entity, panel: Entity) -> None:
    if panel.meters["revised"] >= THRESHOLD:
        teacher.memes["trust"] += 1
        world.say(
            f"Their {teacher.label_word} stopped by just as {child.id} finished erasing the old number."
        )
        world.say(
            f'"Thank you for correcting it," {teacher.pronoun()} said. "A truthful panel teaches more than a perfect-looking one."'
        )
    else:
        teacher.memes["trust"] += 1
        world.say(
            f"Their {teacher.label_word} glanced over the panel and nodded."
        )
        world.say(
            f'"Nice work checking for accuracy," {teacher.pronoun()} said. "Careful work helps people trust what they read."'
        )
    child.memes["honesty"] += 1
    propagate(world, narrate=False)


def ending(world: World, child: Entity, friend: Entity, panel: Entity) -> None:
    if panel.meters["revised"] >= THRESHOLD:
        world.say(
            f"{child.id} stepped back and looked at the clean new number. The panel was simpler now, but it felt steadier."
        )
    else:
        world.say(
            f"{child.id} smoothed one corner of the panel and smiled at how neat and true it looked."
        )
    world.say(
        f"{friend.id} stood beside {child.pronoun('object')}, and for a warm little moment {child.id} felt a deep sense of belonging in the room."
    )
    world.say(world.setting.ending_image)


def tell(
    setting: Setting,
    project: Project,
    tool: Tool,
    method: str,
    child_name: str,
    child_gender: str,
    friend_name: str,
    friend_gender: str,
    teacher_type: str,
    trait: str,
) -> World:
    world = World(setting=setting)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    teacher = world.add(Entity(id="teacher", kind="character", type=teacher_type, label="the teacher", role="teacher"))
    panel = world.add(Entity(id="panel", kind="thing", type="panel", label="panel", phrase="the display panel"))

    child.attrs["name"] = child_name
    child.attrs["trait"] = trait
    friend.attrs["name"] = friend_name
    teacher.attrs["kind"] = teacher_type

    introduce(world, child, friend, teacher, project)
    setup_panel(world, child, project)

    world.para()
    write_claim(world, child, panel, project, method)
    notice_problem(world, friend, child, panel, project)

    world.para()
    verify_panel(world, child, friend, panel, project, tool)
    teacher_response(world, teacher, child, panel)

    world.para()
    ending(world, child, friend, panel)

    outcome = "corrected" if panel.meters["revised"] >= THRESHOLD else "confirmed"
    world.facts.update(
        setting=setting,
        project=project,
        tool=tool,
        child=child,
        friend=friend,
        teacher=teacher,
        panel=panel,
        method=method,
        outcome=outcome,
        corrected=panel.meters["revised"] >= THRESHOLD,
        accurate=panel.meters["accurate"] >= THRESHOLD,
        written_value=panel.attrs.get("written_value", 0),
        actual_value=project.amount,
    )
    return world


KNOWLEDGE = {
    "accuracy": [
        (
            "What does accuracy mean?",
            "Accuracy means getting the facts right. When something is accurate, it matches what is really there."
        )
    ],
    "panel": [
        (
            "What is a display panel?",
            "A display panel is a board that shows information, pictures, or labels. People make one so others can stop, look, and learn."
        )
    ],
    "honesty": [
        (
            "Why is it good to fix a mistake?",
            "Fixing a mistake helps other people trust your work. It also shows honesty, because you care more about the truth than about pretending to be right."
        )
    ],
    "ruler": [
        (
            "What is a ruler used for?",
            "A ruler is used to measure length. It helps you see how long or tall something is by using marked lines and numbers."
        )
    ],
    "count": [
        (
            "How can you count carefully?",
            "You can count carefully by touching or moving each item once. That helps you avoid skipping one or counting the same one twice."
        )
    ],
    "belonging": [
        (
            "What does belonging mean?",
            "Belonging is the feeling that you are part of a group and welcome there. Small acts of kindness and honesty can make that feeling stronger."
        )
    ],
}
KNOWLEDGE_ORDER = ["panel", "accuracy", "honesty", "ruler", "count", "belonging"]


def pair_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    project = f["project"]
    tool = f["tool"]
    outcome = f["outcome"]
    prompts = [
        'Write a short slice-of-life story for a 3-to-5-year-old that includes the words "panel", "accuracy", and "belonging".',
        f"Tell a classroom story where {pair_name(child)} makes a display panel about {project.label}, talks with {pair_name(friend)}, and learns that accuracy matters.",
        f"Write a gentle moral story with dialogue where children use {tool.label} to check a project before open house.",
    ]
    if outcome == "corrected":
        prompts.append(
            f"Include a moment where {pair_name(child)} notices a mistake, tells the truth, and fixes the panel before families arrive."
        )
    else:
        prompts.append(
            f"Include a calm double-check where {pair_name(child)} confirms the panel is correct and feels proud to share it."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    teacher = f["teacher"]
    project = f["project"]
    panel = f["panel"]
    child_name = pair_name(child)
    friend_name = pair_name(friend)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, who is making a school panel, and {friend_name}, who helps check it. Their teacher also appears and guides the moment kindly."
        ),
        (
            "What was on the panel?",
            f"The panel showed {project.phrase} and a sentence about the project result. It was meant for open house, so families could stop and learn from it."
        ),
        (
            f"Why did {friend_name} speak up?",
            f"{friend_name} cared about the work and noticed the number might not be right. Speaking up gave {child_name} a chance to check for accuracy instead of leaving the mistake there."
        ),
    ]
    if f["corrected"]:
        qa.append(
            (
                f"How did {child_name} fix the problem?",
                f"{child_name} used {f['tool'].phrase} with {friend_name} to check the project again and found the true number was {project.amount}. Then {child.pronoun().capitalize()} admitted the guess and changed the panel, so the final version was accurate and honest."
            )
        )
        qa.append(
            (
                "What is the moral of the story?",
                f"The moral is that telling the truth matters more than trying to look perfect. When {child_name} corrected the panel, the class became a place of trust and belonging instead of worry."
            )
        )
    else:
        qa.append(
            (
                f"Was the panel already right?",
                f"Yes. {child_name} had checked carefully before writing, so the panel already matched the real result of {project.amount}. Checking again helped everyone feel calm because the accuracy was confirmed."
            )
        )
        qa.append(
            (
                "What is the moral of the story?",
                f"The moral is that careful work and honesty go together. By checking the panel instead of only hoping it was right, {child_name} earned trust and felt more belonging in the classroom."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    project = world.facts["project"]
    tool = world.facts["tool"]
    tags = {"panel", "accuracy", "honesty", "belonging"}
    if project.measure_kind == "length":
        tags.add("ruler")
    if project.measure_kind == "count":
        tags.add("count")
    if tool.id in {"ruler", "tape"}:
        tags.add("ruler")
    if tool.id in {"counting_board", "sticky_notes"}:
        tags.add("count")
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(project: Project, tool: Tool) -> str:
    if tool.sense < SENSE_MIN:
        return (
            f"(No story: '{tool.id}' is too weak for careful checking. A quick glance does not support accuracy on a school panel.)"
        )
    return (
        f"(No story: {tool.label} cannot honestly verify {project.label}. "
        f"This project needs a tool for {project.measure_kind}, so the panel would have no trustworthy way to check its accuracy.)"
    )


def outcome_of(params: StoryParams) -> str:
    project = PROJECTS[params.project]
    return "confirmed" if actual_written_value(project, params.method) == project.amount else "corrected"


ASP_RULES = r"""
sensible_tool(Tl) :- tool(Tl), sense(Tl, S), sense_min(M), S >= M.
fits(P, Tl) :- project(P), tool(Tl), measure_kind(P, K), measures(Tl, K).
valid(S, P, Tl) :- setting(S), project(P), sensible_tool(Tl), fits(P, Tl).

accurate_from_start :- chosen_project(P), chosen_method(check), amount(P, A), written_value(A).
guessed_wrong       :- chosen_project(P), chosen_method(guess), amount(P, A), written_value(W), W != A.

outcome(confirmed) :- accurate_from_start.
outcome(corrected) :- guessed_wrong, chosen_project(P), chosen_tool(Tl), fits(P, Tl), sensible_tool(Tl).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        lines.append(asp.fact("measure_kind", project_id, project.measure_kind))
        lines.append(asp.fact("amount", project_id, project.amount))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        for kind in sorted(tool.measures):
            lines.append(asp.fact("measures", tool_id, kind))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    project = PROJECTS[params.project]
    extra = "\n".join(
        [
            asp.fact("chosen_project", params.project),
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_method", params.method),
            asp.fact("written_value", actual_written_value(project, params.method)),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test_generation() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    emit(sample, trace=False, qa=False, header="")


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
    for seed in range(40):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)
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
        _smoke_test_generation()
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Slice-of-life storyworld about a school panel, accuracy, and belonging."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--method", choices=["guess", "check"])
    ap.add_argument("--teacher", choices=["teacher_f", "teacher_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.tool:
        project = PROJECTS[args.project]
        tool = TOOLS[args.tool]
        if not (tool.sense >= SENSE_MIN and tool_fits(project, tool)):
            raise StoryError(explain_rejection(project, tool))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        project = PROJECTS[args.project] if args.project else next(iter(PROJECTS.values()))
        raise StoryError(explain_rejection(project, TOOLS[args.tool]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.project is None or combo[1] == args.project)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, project_id, tool_id = rng.choice(sorted(combos))
    method = args.method or rng.choice(["guess", "check", "guess"])
    child_name, child_gender = _pick_child(rng)
    friend_name, friend_gender = _pick_child(rng, avoid=child_name)
    teacher_type = args.teacher or rng.choice(["teacher_f", "teacher_m"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        project=project_id,
        tool=tool_id,
        method=method,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        teacher_type=teacher_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.method not in {"guess", "check"}:
        raise StoryError(f"(Unknown method: {params.method})")
    project = PROJECTS[params.project]
    tool = TOOLS[params.tool]
    if tool.sense < SENSE_MIN or not tool_fits(project, tool):
        raise StoryError(explain_rejection(project, tool))

    world = tell(
        setting=SETTINGS[params.setting],
        project=project,
        tool=tool,
        method=params.method,
        child_name=params.child_name,
        child_gender=params.child_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        teacher_type=params.teacher_type,
        trait=params.trait,
    )

    child = world.facts["child"]
    friend = world.facts["friend"]
    world.get("child").label = params.child_name
    world.get("friend").label = params.friend_name
    story_text = world.render().replace("child", params.child_name).replace("friend", params.friend_name)

    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, project, tool) combos:\n")
        for setting_id, project_id, tool_id in combos:
            print(f"  {setting_id:10} {project_id:10} {tool_id}")
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
            header = f"### {p.child_name}: {p.project} on a panel ({p.method}, {p.tool}, {outcome_of(p)})"
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
