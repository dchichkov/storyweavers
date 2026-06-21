#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hygienist_checker_selection_problem_solving_reconciliation_nursery.py
=================================================================================================

A standalone story world for a nursery-rhyme-flavored tale about a visiting
hygienist, a checker board, and a busy selection tray.

Tiny domain:
    In a nursery room, a hygienist brings a tray of brushing things. Two small
    children both want the same lovely part of the selection. A checker helps
    the grown-up find a fair way through the knot: turns, matched pairs, or
    colors. The children calm down, apologize, and end as friends again.

The world prefers only combinations where the chosen checker can genuinely solve
the chosen selection problem. That reasonableness gate has both a Python and an
ASP version.

Run it
------
    python storyworlds/worlds/gpt-5.4/hygienist_checker_selection_problem_solving_reconciliation_nursery.py
    python storyworlds/worlds/gpt-5.4/hygienist_checker_selection_problem_solving_reconciliation_nursery.py --selection single_mirror --checker turn_checker
    python storyworlds/worlds/gpt-5.4/hygienist_checker_selection_problem_solving_reconciliation_nursery.py --selection twin_brushes --checker color_checker
    python storyworlds/worlds/gpt-5.4/hygienist_checker_selection_problem_solving_reconciliation_nursery.py --all
    python storyworlds/worlds/gpt-5.4/hygienist_checker_selection_problem_solving_reconciliation_nursery.py --qa
    python storyworlds/worlds/gpt-5.4/hygienist_checker_selection_problem_solving_reconciliation_nursery.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
        female = {"girl", "woman", "mother", "teacher", "hygienist"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"hygienist": "hygienist", "teacher": "teacher"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    opening: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Selection:
    id: str
    label: str
    phrase: str
    kind: str
    copies: int
    wants_line: str
    solved_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CheckerTool:
    id: str
    label: str
    phrase: str
    handles: set[str]
    method: str
    rhyme: str
    tags: set[str] = field(default_factory=set)


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"first_child", "second_child"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    setting: str
    selection: str
    checker: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    hygienist_name: str
    mood: str
    seed: Optional[int] = None


SETTINGS = {
    "sunny_room": Setting(
        id="sunny_room",
        label="the sunny nursery room",
        opening="In the sunny nursery room, where little chairs stood in a row,",
        ending="Soon the room hummed soft and slow.",
        tags={"nursery"},
    ),
    "rain_window": Setting(
        id="rain_window",
        label="the nursery by the rainy window",
        opening="In the nursery by the rainy window, where small cups gave a gleam,",
        ending="Soon the room felt warm as cream.",
        tags={"nursery", "rain"},
    ),
    "morning_circle": Setting(
        id="morning_circle",
        label="the morning-circle nursery",
        opening="In the morning-circle nursery, with rugs as round as the moon,",
        ending="Soon everyone was brushing a happy tune.",
        tags={"nursery"},
    ),
}

SELECTIONS = {
    "single_mirror": Selection(
        id="single_mirror",
        label="mirror",
        phrase="a silver tooth mirror with a lion on the handle",
        kind="single",
        copies=1,
        wants_line="Both children reached for the shiny mirror at the very same tick.",
        solved_line="One child could look first, and the other could look next.",
        tags={"mirror", "selection", "hygienist"},
    ),
    "twin_brushes": Selection(
        id="twin_brushes",
        label="brushes",
        phrase="two bunny toothbrushes standing side by side",
        kind="pair",
        copies=2,
        wants_line="Both children squeaked for the bunny brushes with bright and eager eyes.",
        solved_line="There was one brush for each child, neat as a rhyme.",
        tags={"toothbrush", "selection", "hygienist"},
    ),
    "color_cups": Selection(
        id="color_cups",
        label="cups",
        phrase="a red rinse cup and a blue rinse cup in the selection tray",
        kind="color",
        copies=2,
        wants_line="Both children pointed at once and forgot that two colors could fit two hands.",
        solved_line="Each child could have the cup that matched best.",
        tags={"cup", "selection", "color"},
    ),
}

CHECKERS = {
    "turn_checker": CheckerTool(
        id="turn_checker",
        label="turn checker",
        phrase="a turn checker with a little arrow",
        handles={"single"},
        method="turns",
        rhyme='“Tick for you and tock for you; first then next is fair and true.”',
        tags={"checker", "turns"},
    ),
    "pair_checker": CheckerTool(
        id="pair_checker",
        label="pair checker",
        phrase="a pair checker with two matching stars",
        handles={"pair"},
        method="pairs",
        rhyme='“One for me and one for you; two can shine the whole rhyme through.”',
        tags={"checker", "sharing"},
    ),
    "color_checker": CheckerTool(
        id="color_checker",
        label="color checker",
        phrase="a color checker with red and blue windows",
        handles={"color"},
        method="colors",
        rhyme='“Red to red and blue to blue; each small choice can still be true.”',
        tags={"checker", "color"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Jack", "Eli"]
HYGIENIST_NAMES = ["Mina", "Nell", "Poppy", "Rita"]
MOODS = ["cheerful", "gentle", "bouncy", "bright"]

KNOWLEDGE = {
    "hygienist": [
        (
            "What does a hygienist do?",
            "A hygienist helps people keep their teeth clean and healthy. A hygienist can show children how to brush gently and carefully.",
        )
    ],
    "checker": [
        (
            "What is a checker in this story world?",
            "A checker is a little helper board or tool that helps children sort out a choice fairly. It can help with turns, pairs, or colors.",
        )
    ],
    "selection": [
        (
            "What is a selection?",
            "A selection is a group of things to choose from. You look carefully and pick the one that fits best.",
        )
    ],
    "toothbrush": [
        (
            "Why do people use a toothbrush?",
            "A toothbrush helps sweep food and sticky bits from teeth. Brushing every day helps keep teeth clean.",
        )
    ],
    "mirror": [
        (
            "Why might a hygienist use a small mirror?",
            "A small mirror helps a grown-up peek at the teeth more easily. It lets the grown-up see places that are hard to spot.",
        )
    ],
    "cup": [
        (
            "What is a rinse cup for?",
            "A rinse cup holds water for swishing after brushing. It helps keep the brushing routine tidy.",
        )
    ],
    "sharing": [
        (
            "How can children solve a problem when they both want something?",
            "They can take turns, find a pair, or choose in a fair way. A calm plan helps everyone feel heard.",
        )
    ],
    "color": [
        (
            "How can colors help with choosing?",
            "Colors can help children notice which thing is theirs. That makes the choice clear and calm.",
        )
    ],
    "turns": [
        (
            "Why do turns help?",
            "Turns help when only one person can use something at a time. Waiting becomes easier when everyone knows who is first and who is next.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "hygienist",
    "checker",
    "selection",
    "toothbrush",
    "mirror",
    "cup",
    "sharing",
    "color",
    "turns",
]


def valid_combo(selection: Selection, checker: CheckerTool) -> bool:
    return selection.kind in checker.handles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for selection_id, selection in SELECTIONS.items():
            for checker_id, checker in CHECKERS.items():
                if valid_combo(selection, checker):
                    combos.append((setting_id, selection_id, checker_id))
    return combos


def explain_rejection(selection: Selection, checker: CheckerTool) -> str:
    return (
        f"(No story: {checker.label} solves {sorted(checker.handles)} choices, "
        f"but {selection.phrase} is a {selection.kind} selection. Pick a checker "
        f"that really fits the problem.)"
    )


def solution_mode(selection_id: str, checker_id: str) -> str:
    selection = SELECTIONS[selection_id]
    checker = CHECKERS[checker_id]
    if not valid_combo(selection, checker):
        raise StoryError(explain_rejection(selection, checker))
    return checker.method


def _raise_if_bad_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.selection not in SELECTIONS:
        raise StoryError(f"(Unknown selection: {params.selection})")
    if params.checker not in CHECKERS:
        raise StoryError(f"(Unknown checker: {params.checker})")
    if not valid_combo(SELECTIONS[params.selection], CHECKERS[params.checker]):
        raise StoryError(explain_rejection(SELECTIONS[params.selection], CHECKERS[params.checker]))


def introduce(world: World, a: Entity, b: Entity, hygienist: Entity, selection: Selection, checker: CheckerTool) -> None:
    world.say(
        f"{world.setting.opening} {hygienist.id} the hygienist came in with a smile "
        f"and set down {selection.phrase} beside {checker.phrase}."
    )
    world.say(
        f"{a.id} and {b.id} sat knee to knee on the mat, each feeling {world.facts['mood']} and curious."
    )
    for kid in (a, b):
        kid.memes["curious"] += 1
        kid.memes["joy"] += 1
    hygienist.memes["calm"] += 1


def announce_selection(world: World, hygienist: Entity, selection: Selection) -> None:
    world.say(
        f'“Choose from my selection, little ones, and we shall learn about clean, bright teeth,” '
        f"said {hygienist.id}."
    )
    world.say(
        f"The tray gave a tiny clink, a tiny gleam, and every shiny piece looked nicer than a dream."
    )


def reach_together(world: World, a: Entity, b: Entity, selection: Selection) -> None:
    world.say(selection.wants_line)
    world.say(
        f"{a.id} said, “Oh, let it be mine,” and {b.id} said, “No, mine, mine, mine.”"
    )
    world.get("selection").meters["contested"] += 1
    world.facts["dispute_started"] = True


def propagate(world: World) -> None:
    selection_ent = world.get("selection")
    a = world.get("child1")
    b = world.get("child2")
    if selection_ent.meters["contested"] >= THRESHOLD and ("contest",) not in world.fired:
        world.fired.add(("contest",))
        a.memes["upset"] += 1
        b.memes["upset"] += 1
        a.memes["stubborn"] += 1
        b.memes["stubborn"] += 1
        world.say("Two little brows bent low; the room lost some of its sing-song glow.")
    if (
        a.memes["sorry"] >= THRESHOLD
        and b.memes["sorry"] >= THRESHOLD
        and ("reconcile",) not in world.fired
    ):
        world.fired.add(("reconcile",))
        a.memes["friendship"] += 1
        b.memes["friendship"] += 1
        a.memes["upset"] = 0.0
        b.memes["upset"] = 0.0


def think_and_solve(world: World, a: Entity, b: Entity, hygienist: Entity, selection: Selection, checker: CheckerTool) -> None:
    hygienist.memes["problem_solving"] += 1
    world.say(
        f"But {hygienist.id} did not scold. {hygienist.pronoun().capitalize()} tapped the {checker.label} and thought a calm thought."
    )
    world.say(checker.rhyme)
    mode = checker.method
    world.facts["solution_mode"] = mode

    if mode == "turns":
        a.attrs["order"] = "first"
        b.attrs["order"] = "next"
        a.meters["holding"] += 1
        b.meters["waiting"] += 1
        world.say(
            f"{hygienist.id} turned the checker arrow toward {a.id}, then toward {b.id}. "
            f"{selection.solved_line}"
        )
        world.say(
            f"{a.id} held the mirror first and opened wide, while {b.id} watched and waited by {hygienist.pronoun('possessive')} side."
        )
    elif mode == "pairs":
        a.meters["holding"] += 1
        b.meters["holding"] += 1
        world.say(
            f"{hygienist.id} lifted the two matching stars on the checker. {selection.solved_line}"
        )
        world.say(
            f"One bunny brush hopped to {a.id}, and the other hopped to {b.id}; the trouble grew smaller at once."
        )
    elif mode == "colors":
        a.attrs["color"] = "red"
        b.attrs["color"] = "blue"
        a.meters["holding"] += 1
        b.meters["holding"] += 1
        world.say(
            f"{hygienist.id} held the color checker up to the tray. {selection.solved_line}"
        )
        world.say(
            f"{a.id} took the red cup, {b.id} took the blue cup, and the mix-up untied itself like a loosened bow."
        )
    else:
        raise StoryError(f"(Unknown solution mode: {mode})")

    world.get("selection").meters["resolved"] += 1
    a.memes["calm"] += 1
    b.memes["calm"] += 1
    a.memes["heard"] += 1
    b.memes["heard"] += 1


def apologize(world: World, a: Entity, b: Entity) -> None:
    a.memes["sorry"] += 1
    b.memes["sorry"] += 1
    world.say(
        f"Then {a.id} looked at {b.id}, and {b.id} looked back. “I pulled too fast,” said {a.id}. “I fussed too loud,” said {b.id}."
    )
    propagate(world)
    world.say("Their small hands met in the middle, and the quarrel slipped away.")


def finish_scene(world: World, a: Entity, b: Entity, hygienist: Entity, selection: Selection, checker: CheckerTool) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    hygienist.memes["pride"] += 1
    world.say(
        f"After that, the hygienist showed them gentle circles for brushing, soft as a song and slow as a sway."
    )
    if checker.method == "turns":
        world.say(
            f"When {a.id} finished, {b.id} had a turn just as promised, and the checker arrow proved the promise true."
        )
    elif checker.method == "pairs":
        world.say(
            f"The two brushes bobbed up and down together, and even the checker seemed pleased with the pair."
        )
    else:
        world.say(
            f"The red cup and blue cup stood side by side, and the checker windows shone like two little eyes."
        )
    world.say(
        f"{world.setting.ending} {a.id} and {b.id} smiled at each other, and the fair little plan felt better than a fuss."
    )

    world.facts["resolved"] = True
    world.facts["reconciled"] = a.memes["friendship"] >= THRESHOLD and b.memes["friendship"] >= THRESHOLD
    world.facts["lesson"] = "A fair plan can mend a muddle, and kind words can mend a friendship."


def tell(
    setting: Setting,
    selection: Selection,
    checker: CheckerTool,
    child1_name: str,
    child1_gender: str,
    child2_name: str,
    child2_gender: str,
    hygienist_name: str,
    mood: str,
) -> World:
    world = World(setting=setting)
    a = world.add(
        Entity(
            id="child1",
            kind="character",
            type=child1_gender,
            label=child1_name,
            phrase=child1_name,
            role="first_child",
            traits=[mood],
        )
    )
    b = world.add(
        Entity(
            id="child2",
            kind="character",
            type=child2_gender,
            label=child2_name,
            phrase=child2_name,
            role="second_child",
            traits=[mood],
        )
    )
    hygienist = world.add(
        Entity(
            id="hygienist",
            kind="character",
            type="hygienist",
            label=hygienist_name,
            phrase=hygienist_name,
            role="guide",
            traits=["calm", "kind"],
            tags={"hygienist"},
        )
    )
    checker_ent = world.add(
        Entity(
            id="checker",
            kind="thing",
            type="checker",
            label=checker.label,
            phrase=checker.phrase,
            tags=set(checker.tags),
        )
    )
    selection_ent = world.add(
        Entity(
            id="selection",
            kind="thing",
            type="selection",
            label=selection.label,
            phrase=selection.phrase,
            tags=set(selection.tags),
        )
    )
    world.facts.update(
        child1=a,
        child2=b,
        hygienist=hygienist,
        checker=checker_ent,
        checker_cfg=checker,
        selection=selection_ent,
        selection_cfg=selection,
        setting=setting,
        mood=mood,
        child1_name=child1_name,
        child2_name=child2_name,
    )

    introduce(world, a, b, hygienist, selection, checker)
    announce_selection(world, hygienist, selection)

    world.para()
    reach_together(world, a, b, selection)
    propagate(world)

    world.para()
    think_and_solve(world, a, b, hygienist, selection, checker)
    apologize(world, a, b)

    world.para()
    finish_scene(world, a, b, hygienist, selection, checker)
    return world


def render_story(world: World) -> str:
    a = world.facts["child1"]
    b = world.facts["child2"]
    raw = world.render()
    return raw.replace("child1", a.label).replace("child2", b.label).replace("hygienist", world.facts["hygienist"].label)


def generation_prompts(world: World) -> list[str]:
    a = world.facts["child1"]
    b = world.facts["child2"]
    checker = world.facts["checker_cfg"]
    selection = world.facts["selection_cfg"]
    return [
        'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "hygienist", "checker", and "selection".',
        f"Tell a gentle problem-solving story where {a.label} and {b.label} both want {selection.phrase}, and a hygienist uses a {checker.label} to make the choice fair.",
        "Write a child-facing story with a small quarrel, a calm fair plan, and a reconciled ending where the children become friends again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    a = world.facts["child1"]
    b = world.facts["child2"]
    hygienist = world.facts["hygienist"]
    checker = world.facts["checker_cfg"]
    selection = world.facts["selection_cfg"]
    mode = world.facts["solution_mode"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.label} and {b.label} in nursery, and {hygienist.label} the hygienist who helps them. The grown-up brings a selection tray and guides them through a small problem.",
        ),
        (
            "What problem did the children have?",
            f"They both wanted {selection.phrase} at the same time. That made them fuss because each child thought the best part of the selection should be theirs first.",
        ),
        (
            "How did the hygienist solve the problem?",
            f"{hygienist.label} used the {checker.label} to make the choice fair. The checker fit the problem, so the children could see a clear plan instead of pulling and arguing.",
        ),
    ]
    if mode == "turns":
        qa.append(
            (
                "What fair plan did the checker make?",
                f"The turn checker showed that {a.label} would go first and {b.label} would go next. That helped {b.label} wait calmly because the promise of a turn was clear.",
            )
        )
    elif mode == "pairs":
        qa.append(
            (
                "What fair plan did the checker make?",
                f"The pair checker showed that there were two matching things, one for each child. The problem melted because nobody had to lose the whole choice.",
            )
        )
    else:
        qa.append(
            (
                "What fair plan did the checker make?",
                f"The color checker matched the choice into two clear parts, so {a.label} could take one color and {b.label} could take the other. That solved the muddle by making the selection easy to separate.",
            )
        )
    qa.append(
        (
            "How did the children make up?",
            f"They each admitted their part in the fuss and spoke kindly to each other. Their apology mattered because the fair plan calmed them first, and then friendship could come back.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with brushing, smiling, and no more quarrel. The ending shows that a solved problem and a kind apology changed the whole room.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"hygienist", "checker", "selection", "sharing"}
    tags |= set(world.facts["selection_cfg"].tags)
    tags |= set(world.facts["checker_cfg"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="sunny_room",
        selection="single_mirror",
        checker="turn_checker",
        child1="Lily",
        child1_gender="girl",
        child2="Ben",
        child2_gender="boy",
        hygienist_name="Mina",
        mood="cheerful",
    ),
    StoryParams(
        setting="rain_window",
        selection="twin_brushes",
        checker="pair_checker",
        child1="Mia",
        child1_gender="girl",
        child2="Zoe",
        child2_gender="girl",
        hygienist_name="Nell",
        mood="gentle",
    ),
    StoryParams(
        setting="morning_circle",
        selection="color_cups",
        checker="color_checker",
        child1="Max",
        child1_gender="boy",
        child2="Ella",
        child2_gender="girl",
        hygienist_name="Poppy",
        mood="bright",
    ),
]


ASP_RULES = r"""
valid(Sel, Chk) :- selection(Sel), checker(Chk), kind(Sel, K), handles(Chk, K).

mode(Sel, turns) :- kind(Sel, single).
mode(Sel, pairs) :- kind(Sel, pair).
mode(Sel, colors) :- kind(Sel, color).

solves_as(Sel, Chk, M) :- valid(Sel, Chk), mode(Sel, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for selection_id, selection in SELECTIONS.items():
        lines.append(asp.fact("selection", selection_id))
        lines.append(asp.fact("kind", selection_id, selection.kind))
    for checker_id, checker in CHECKERS.items():
        lines.append(asp.fact("checker", checker_id))
        for handle in sorted(checker.handles):
            lines.append(asp.fact("handles", checker_id, handle))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_solution_modes() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show solves_as/3."))
    return sorted(set(asp.atoms(model, "solves_as")))


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = {(selection_id, checker_id) for _, selection_id, checker_id in valid_combos()}
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid combos ({len(clingo_set)} selection/checker pairs).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    asp_modes = {(sel, chk): mode for sel, chk, mode in asp_solution_modes()}
    py_modes = {}
    for selection_id, selection in SELECTIONS.items():
        for checker_id, checker in CHECKERS.items():
            if valid_combo(selection, checker):
                py_modes[(selection_id, checker_id)] = checker.method
    if asp_modes == py_modes:
        print(f"OK: ASP solution modes match Python ({len(py_modes)} cases).")
    else:
        rc = 1
        print("MISMATCH in solution modes:")
        for key in sorted(set(asp_modes) | set(py_modes)):
            if asp_modes.get(key) != py_modes.get(key):
                print(f"  {key}: asp={asp_modes.get(key)} python={py_modes.get(key)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: a hygienist, a checker, a selection, a fair solution, and a friendship mended."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--selection", choices=SELECTIONS)
    ap.add_argument("--checker", choices=CHECKERS)
    ap.add_argument("--child1")
    ap.add_argument("--child2")
    ap.add_argument("--child1-gender", choices=["girl", "boy"])
    ap.add_argument("--child2-gender", choices=["girl", "boy"])
    ap.add_argument("--hygienist-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid selection/checker pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a generation smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(gender: str, rng: random.Random, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.selection and args.checker:
        selection = SELECTIONS[args.selection]
        checker = CHECKERS[args.checker]
        if not valid_combo(selection, checker):
            raise StoryError(explain_rejection(selection, checker))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.selection is None or combo[1] == args.selection)
        and (args.checker is None or combo[2] == args.checker)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, selection_id, checker_id = rng.choice(sorted(combos))
    child1_gender = args.child1_gender or rng.choice(["girl", "boy"])
    child2_gender = args.child2_gender or rng.choice(["girl", "boy"])
    child1 = args.child1 or _pick_name(child1_gender, rng)
    child2 = args.child2 or _pick_name(child2_gender, rng, avoid=child1)
    hygienist_name = args.hygienist_name or rng.choice(HYGIENIST_NAMES)
    mood = rng.choice(MOODS)

    return StoryParams(
        setting=setting_id,
        selection=selection_id,
        checker=checker_id,
        child1=child1,
        child1_gender=child1_gender,
        child2=child2,
        child2_gender=child2_gender,
        hygienist_name=hygienist_name,
        mood=mood,
    )


def generate(params: StoryParams) -> StorySample:
    _raise_if_bad_params(params)
    world = tell(
        setting=SETTINGS[params.setting],
        selection=SELECTIONS[params.selection],
        checker=CHECKERS[params.checker],
        child1_name=params.child1,
        child1_gender=params.child1_gender,
        child2_name=params.child2,
        child2_gender=params.child2_gender,
        hygienist_name=params.hygienist_name,
        mood=params.mood,
    )
    story_text = render_story(world)
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
        print(asp_program("", "#show valid/2.\n#show solves_as/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_combos()
        print(f"{len(pairs)} compatible (selection, checker) pairs:\n")
        for selection_id, checker_id in pairs:
            print(f"  {selection_id:14} {checker_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child1} & {p.child2}: {p.selection} with {p.checker} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
