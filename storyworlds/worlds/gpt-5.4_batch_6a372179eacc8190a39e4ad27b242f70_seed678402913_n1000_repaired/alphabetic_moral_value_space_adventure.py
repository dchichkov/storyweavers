#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/alphabetic_moral_value_space_adventure.py
====================================================================

A small standalone storyworld about two children on a space-training mission.
They must place glowing letter tiles in alphabetic order to unlock a helpful
space device, but one letter goes missing. The tension is moral as well as
practical: a child is tempted to cheat, hide a mistake, or push ahead too fast.
The story only allows fixes that are both sensible for the physical problem and
true to the chosen moral value.

The world model tracks a few physical meters (lost, powered, waiting, found)
and emotional memes (worry, honesty, patience, kindness, pride, relief). The
rendered prose follows state and decisions rather than swapping nouns into one
frozen paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/alphabetic_moral_value_space_adventure.py
    python storyworlds/worlds/gpt-5.4/alphabetic_moral_value_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/alphabetic_moral_value_space_adventure.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/alphabetic_moral_value_space_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/alphabetic_moral_value_space_adventure.py --verify
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

# Make the shared result containers importable when this nested script is run
# directly from the repo root.
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
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Mission:
    id: str
    place: str
    task: str
    board: str
    reward: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    missing_letter: str
    scene: str
    cause: str
    where: str
    danger: str
    requires: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MoralValue:
    id: str
    noun: str
    lesson: str
    shine: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    value: str
    solves: set[str] = field(default_factory=set)
    action: str = ""
    success: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


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


def _r_power_ready(world: World) -> list[str]:
    board = world.get("board")
    if board.meters["alphabetic"] < THRESHOLD or board.meters["complete"] < THRESHOLD:
        return []
    sig = ("powered", "board")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    board.meters["powered"] += 1
    for eid in ("hero", "friend"):
        world.get(eid).memes["relief"] += 1
        world.get(eid).memes["joy"] += 1
    return ["__powered__"]


def _r_lost_worry(world: World) -> list[str]:
    tile = world.get("tile")
    if tile.meters["lost"] < THRESHOLD:
        return []
    sig = ("worry", "tile")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("hero", "friend"):
        world.get(eid).memes["worry"] += 1
    return ["__worry__"]


CAUSAL_RULES = [
    Rule(name="power_ready", tag="physical", apply=_r_power_ready),
    Rule(name="lost_worry", tag="emotional", apply=_r_lost_worry),
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
        for sent in produced:
            world.say(sent)
    return produced


MISSIONS = {
    "beacon": Mission(
        id="beacon",
        place="the little training ship Comet Bell",
        task="wake the rescue beacon",
        board="a round panel with glowing letter slots",
        reward="the beacon would shine a path through the dark",
        ending="Outside the window, the rescue beacon blinked steady and brave.",
        tags={"space", "beacon"},
    ),
    "map": Mission(
        id="map",
        place="the moon station Skylark Dock",
        task="unlock the star map",
        board="a silver wall board with bright letter slots",
        reward="the map would draw a safe line between the moons",
        ending="On the wall, the star map opened like a ribbon of light.",
        tags={"space", "map"},
    ),
    "garden": Mission(
        id="garden",
        place="the orbiting greenhouse Sunseed",
        task="start the water stars in the garden dome",
        board="a clear console with glowing letter slots",
        reward="the tiny moon plants would get their shining drink",
        ending="In the dome, the water stars twinkled over the sleepy plants.",
        tags={"space", "garden"},
    ),
}

PROBLEMS = {
    "under_seat": Problem(
        id="under_seat",
        missing_letter="C",
        scene="One slot stayed dark where the letter C should have glowed.",
        cause="The little tile had slipped away during a sharp turn.",
        where="under the pilot seat",
        danger="The board could not finish its alphabetic song without it.",
        requires="search",
        tags={"alphabet", "search"},
    ),
    "robot_tray": Problem(
        id="robot_tray",
        missing_letter="M",
        scene="The row paused at L, and the slot for M stayed empty.",
        cause="A tiny service robot had picked the shiny tile up with the snack trays.",
        where="on the robot's tray",
        danger="Without M, the alphabetic pattern broke in the middle.",
        requires="help_robot",
        tags={"alphabet", "robot"},
    ),
    "foggy_window": Problem(
        id="foggy_window",
        missing_letter="S",
        scene="The line reached R, but S looked missing in the misty glow.",
        cause="Warm breath had fogged the panel cover, and the small tile was hard to see.",
        where="behind the cloudy cover",
        danger="Rushing would only make the letters blur more.",
        requires="wait_scan",
        tags={"alphabet", "patience"},
    ),
}

VALUES = {
    "honesty": MoralValue(
        id="honesty",
        noun="honesty",
        lesson="telling the truth, even when a mistake feels embarrassing",
        shine="truth can be brave enough to light the dark",
        tags={"honesty"},
    ),
    "kindness": MoralValue(
        id="kindness",
        noun="kindness",
        lesson="helping someone small and busy before thinking only of yourself",
        shine="a kind choice can open doors faster than grabbing",
        tags={"kindness"},
    ),
    "patience": MoralValue(
        id="patience",
        noun="patience",
        lesson="slowing your hands so your eyes and heart can work properly",
        shine="slow and steady can be stronger than a rush",
        tags={"patience"},
    ),
}

FIXES = {
    "confess_search": Fix(
        id="confess_search",
        value="honesty",
        solves={"under_seat"},
        action="took a breath, admitted the missing tile was not in the right place, and crawled with a lamp to look under the seat",
        success="There, tucked by a silver boot, lay the little C tile.",
        qa_text="They told the truth and searched under the seat until they found the C tile.",
        tags={"honesty", "search", "flashlight"},
    ),
    "help_robot": Fix(
        id="help_robot",
        value="kindness",
        solves={"robot_tray"},
        action="stopped chasing the tray, helped the wobbling service robot stack its cups, and then asked politely about the shiny letter",
        success="The robot chirped happily and lifted the M tile right out of its tray.",
        qa_text="They helped the service robot first, and the robot gave back the M tile.",
        tags={"kindness", "robot"},
    ),
    "wait_scan": Fix(
        id="wait_scan",
        value="patience",
        solves={"foggy_window"},
        action="rested their hands, counted slowly to five, and wiped the mist away before scanning the board again",
        success="When the cover cleared, the S tile was waiting in plain sight.",
        qa_text="They slowed down, cleared the fog, and then saw the S tile clearly.",
        tags={"patience", "scan"},
    ),
}

GIRL_NAMES = ["Luna", "Mira", "Nia", "Ava", "Zoe", "Tara", "Ivy", "Nora"]
BOY_NAMES = ["Leo", "Milo", "Kai", "Finn", "Theo", "Noah", "Eli", "Sam"]
TRAITS = ["careful", "eager", "curious", "gentle", "brave", "thoughtful"]


def valid_combo(problem_id: str, value_id: str, fix_id: str) -> bool:
    if problem_id not in PROBLEMS or value_id not in VALUES or fix_id not in FIXES:
        return False
    fix = FIXES[fix_id]
    return value_id == fix.value and problem_id in fix.solves


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for problem_id in PROBLEMS:
        for value_id in VALUES:
            for fix_id in FIXES:
                if valid_combo(problem_id, value_id, fix_id):
                    combos.append((problem_id, value_id, fix_id))
    return combos


def predict_success(world: World, problem: Problem, fix: Fix) -> dict:
    sim = world.copy()
    tile = sim.get("tile")
    board = sim.get("board")
    if problem.requires in fix.solves or problem.id in fix.solves:
        tile.meters["lost"] = 0.0
        tile.meters["found"] += 1
        board.meters["complete"] += 1
        board.meters["alphabetic"] += 1
    propagate(sim, narrate=False)
    return {
        "found": tile.meters["found"] >= THRESHOLD,
        "powered": board.meters["powered"] >= THRESHOLD,
    }


def setup_scene(world: World, hero: Entity, friend: Entity, mentor: Entity, mission: Mission) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{hero.id} and {friend.id} were junior space scouts aboard {mission.place}. "
        f"Before them stood {mission.board}. If they could place the glowing letter tiles in alphabetic order, they could {mission.task}."
    )
    world.say(
        f'"A, B, C, all the way on," said {mentor.id}, smiling. "When the letters line up, {mission.reward}."'
    )


def begin_task(world: World, hero: Entity, friend: Entity, mission: Mission) -> None:
    board = world.get("board")
    board.meters["alphabetic"] += 0.5
    world.say(
        f"The children clicked the first bright tiles into place. Each one made a tiny chiming sound, and the board hummed as if it liked good alphabetic order."
    )
    world.say(
        f'{hero.id} grinned. "This is the best kind of space adventure," {hero.pronoun()} said. "{mission.task.capitalize()} by letters!"'
    )


def problem_appears(world: World, hero: Entity, friend: Entity, problem: Problem) -> None:
    tile = world.get("tile")
    tile.meters["lost"] += 1
    propagate(world, narrate=False)
    world.say(problem.scene)
    world.say(
        f"{problem.cause} It was now {problem.where}, and {problem.danger}"
    )
    world.say(
        f'{friend.id} leaned close. "We are stuck," {friend.pronoun()} whispered.'
    )


def temptation(world: World, hero: Entity, friend: Entity, value: MoralValue, problem: Problem) -> None:
    hero.memes["worry"] += 1
    hero.memes["pride"] += 1
    if value.id == "honesty":
        world.say(
            f'{hero.id} looked at the dark slot and felt heat in {hero.pronoun("possessive")} cheeks. "Maybe we could slide the next letter over and pretend," {hero.pronoun()} murmured.'
        )
    elif value.id == "kindness":
        world.say(
            f'{hero.id} watched the robot roll away with the shiny tile and stamped one small boot. "Maybe we should just grab it back and hurry," {hero.pronoun()} said.'
        )
    else:
        world.say(
            f'{hero.id} squinted at the foggy cover. "Maybe I should press every button fast until something works," {hero.pronoun()} said.'
        )
    world.say(
        f"But even in the blue ship-light, that idea did not feel as good as it first sounded."
    )
    friend.memes[value.id] += 1


def moral_warning(world: World, hero: Entity, friend: Entity, value: MoralValue, problem: Problem) -> None:
    if value.id == "honesty":
        world.say(
            f'{friend.id} shook {friend.pronoun("possessive")} head. "If the letters are wrong, the board will still know. {value.noun.capitalize()} means telling the truth about the missing {problem.missing_letter}," {friend.pronoun()} said.'
        )
    elif value.id == "kindness":
        world.say(
            f'{friend.id} touched the little robot gently. "It looks busy, not mean. {value.noun.capitalize()} means helping first instead of grabbing," {friend.pronoun()} said.'
        )
    else:
        world.say(
            f'{friend.id} rested a hand on the console. "{value.noun.capitalize()} means slow hands and clear eyes. If we rush, we will only miss the letter again," {friend.pronoun()} said.'
        )


def apply_fix(world: World, hero: Entity, friend: Entity, value: MoralValue, problem: Problem, fix: Fix) -> None:
    hero.memes[value.id] += 1
    friend.memes[value.id] += 1
    world.say(
        f"{hero.id} took another breath and chose {value.noun}. {hero.pronoun().capitalize()} {fix.action}."
    )
    world.say(fix.success)
    tile = world.get("tile")
    board = world.get("board")
    tile.meters["lost"] = 0.0
    tile.meters["found"] += 1
    board.meters["complete"] += 1
    board.meters["alphabetic"] += 1
    propagate(world, narrate=False)


def finish_mission(world: World, hero: Entity, friend: Entity, mentor: Entity, mission: Mission, value: MoralValue, problem: Problem) -> None:
    board = world.get("board")
    if board.meters["powered"] < THRESHOLD:
        raise StoryError("The board never powered on, so the story has no honest ending.")
    world.say(
        f"At last, {hero.id} set the {problem.missing_letter} tile into its place. The whole row shone in alphabetic order from edge to edge."
    )
    world.say(
        f"The console answered with a bright whoom, and {mission.reward}. {mentor.id} clapped softly. "{value.noun.capitalize()} helped more than hurrying today."'
    )
    world.say(
        f"{mission.ending} {hero.id} and {friend.id} looked at each other and smiled, because the mission had worked and their choice had worked too."
    )


def tell(
    mission: Mission,
    problem: Problem,
    value: MoralValue,
    fix: Fix,
    hero_name: str = "Luna",
    hero_gender: str = "girl",
    friend_name: str = "Leo",
    friend_gender: str = "boy",
    mentor_type: str = "mother",
    hero_trait: str = "curious",
    friend_trait: str = "gentle",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=[hero_trait],
        tags={"child"},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=[friend_trait],
        tags={"child"},
    ))
    mentor = world.add(Entity(
        id="Captain Sol",
        kind="character",
        type=mentor_type,
        role="mentor",
        label="the captain",
        tags={"adult"},
    ))
    board = world.add(Entity(
        id="board",
        type="console",
        label="letter board",
        phrase=mission.board,
        tags={"alphabetic", "space"},
    ))
    tile = world.add(Entity(
        id="tile",
        type="tile",
        label=f"{problem.missing_letter} tile",
        phrase=f"the glowing {problem.missing_letter} tile",
        tags={"letter"},
    ))

    setup_scene(world, hero, friend, mentor, mission)
    begin_task(world, hero, friend, mission)

    world.para()
    problem_appears(world, hero, friend, problem)
    temptation(world, hero, friend, value, problem)
    moral_warning(world, hero, friend, value, problem)

    prediction = predict_success(world, problem, fix)
    if not prediction["found"]:
        raise StoryError("This fix would not honestly solve the missing-letter problem.")

    world.para()
    apply_fix(world, hero, friend, value, problem, fix)
    finish_mission(world, hero, friend, mentor, mission, value, problem)

    world.facts.update(
        hero=hero,
        friend=friend,
        mentor=mentor,
        mission=mission,
        problem=problem,
        value=value,
        fix=fix,
        board=board,
        tile=tile,
        solved=tile.meters["found"] >= THRESHOLD,
        powered=board.meters["powered"] >= THRESHOLD,
    )
    return world


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    mission: str
    problem: str
    value: str
    fix: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    mentor: str
    hero_trait: str
    friend_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        mission="beacon",
        problem="under_seat",
        value="honesty",
        fix="confess_search",
        hero_name="Luna",
        hero_gender="girl",
        friend_name="Milo",
        friend_gender="boy",
        mentor="mother",
        hero_trait="eager",
        friend_trait="careful",
    ),
    StoryParams(
        mission="map",
        problem="robot_tray",
        value="kindness",
        fix="help_robot",
        hero_name="Kai",
        hero_gender="boy",
        friend_name="Mira",
        friend_gender="girl",
        mentor="father",
        hero_trait="brave",
        friend_trait="gentle",
    ),
    StoryParams(
        mission="garden",
        problem="foggy_window",
        value="patience",
        fix="wait_scan",
        hero_name="Nia",
        hero_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        mentor="mother",
        hero_trait="curious",
        friend_trait="thoughtful",
    ),
]


KNOWLEDGE = {
    "alphabetic": [
        (
            "What does alphabetic order mean?",
            "Alphabetic order means putting letters in the same order they come in the alphabet, like A, B, C, D. It helps people find things and notice when a letter is missing.",
        )
    ],
    "beacon": [
        (
            "What is a beacon?",
            "A beacon is a light or signal that helps show the way. In space stories, a beacon can guide travelers through the dark.",
        )
    ],
    "map": [
        (
            "What is a star map?",
            "A star map is a picture or chart that shows where stars or space places are. It helps travelers know where to go.",
        )
    ],
    "robot": [
        (
            "What is a service robot?",
            "A service robot is a helpful machine that carries things or does small jobs. It follows simple rules and can help people when they are kind to it.",
        )
    ],
    "honesty": [
        (
            "Why is honesty important?",
            "Honesty is important because telling the truth helps people fix real problems. Pretending everything is fine can leave the problem waiting there.",
        )
    ],
    "kindness": [
        (
            "Why can kindness solve problems?",
            "Kindness helps because people and helpers often work better when they feel safe and respected. A gentle choice can open a path that grabbing would close.",
        )
    ],
    "patience": [
        (
            "Why is patience useful?",
            "Patience is useful because slowing down gives your eyes, hands, and mind time to notice what is really there. Rushing can make mistakes bigger.",
        )
    ],
    "scan": [
        (
            "What does it mean to scan something?",
            "To scan means to look over something carefully so you can find details. You move your eyes slowly instead of guessing.",
        )
    ],
}
KNOWLEDGE_ORDER = ["alphabetic", "beacon", "map", "robot", "honesty", "kindness", "patience", "scan"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    mission = f["mission"]
    value = f["value"]
    problem = f["problem"]
    return [
        f'Write a short space adventure for a 3-to-5-year-old that includes the word "alphabetic" and teaches {value.noun}.',
        f"Tell a gentle story where {hero.id} and {friend.id} are junior space scouts trying to {mission.task}, but the letter {problem.missing_letter} goes missing and they solve the problem with {value.noun}.",
        f'Write a child-facing story about glowing letters in alphabetic order, a small moral choice, and a happy ending aboard a spaceship or station.',
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    mission = f["mission"]
    problem = f["problem"]
    value = f["value"]
    fix = f["fix"]
    mentor = f["mentor"]
    out = [
        (
            "Who is the story about?",
            f"It is about two junior space scouts, {hero.id} and {friend.id}, and Captain Sol who guides them. They are on a mission to {mission.task}.",
        ),
        (
            "What were they trying to do?",
            f"They were trying to place glowing letter tiles in alphabetic order so they could {mission.task}. The letters had to be correct for the board to work.",
        ),
        (
            f"What problem happened with the letter {problem.missing_letter}?",
            f"The {problem.missing_letter} tile was missing, so one slot stayed dark. That broke the alphabetic pattern and stopped the mission from finishing.",
        ),
    ]
    if value.id == "honesty":
        out.append(
            (
                f"Why was honesty important in this story?",
                f"Honesty mattered because the children could not truly fix the board by pretending the letters were right. When {hero.id} admitted the mistake and searched properly, they found the real {problem.missing_letter} tile and the mission could work.",
            )
        )
    elif value.id == "kindness":
        out.append(
            (
                "How did kindness help solve the problem?",
                f"Kindness helped because the missing tile was with a busy little robot. When the children helped it first and asked politely, the robot gladly gave back the {problem.missing_letter} tile.",
            )
        )
    else:
        out.append(
            (
                "How did patience help solve the problem?",
                f"Patience helped because the foggy cover made the letters hard to see. When the children slowed down and cleared the mist, they could finally spot the {problem.missing_letter} tile properly.",
            )
        )
    out.append(
        (
            "How did they fix the mission?",
            f"{fix.qa_text} After that, they placed the tile in its proper spot and the board powered up.",
        )
    )
    out.append(
        (
            "How did the story end?",
            f"It ended happily: the mission worked, the glowing board came alive, and Captain Sol praised {value.noun}. The ending image shows that a good choice changed the whole room.",
        )
    )
    out.append(
        (
            f"What did Captain Sol teach the children?",
            f'{mentor.id} taught them that {value.lesson}. That lesson mattered because the problem was solved by the right choice, not by rushing or pretending.',
        )
    )
    return out


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"alphabetic", f["value"].id}
    mission = f["mission"]
    problem = f["problem"]
    tags |= mission.tags
    tags |= problem.tags
    fix = f["fix"]
    if "robot" in fix.tags:
        tags.add("robot")
    if "scan" in fix.tags:
        tags.add("scan")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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


ASP_RULES = r"""
% A fix is valid only when it teaches the same moral value and truly solves
% the specific problem.
valid(P, V, F) :- problem(P), value(V), fix(F), fix_value(F, V), solves(F, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for vid in VALUES:
        lines.append(asp.fact("value", vid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("fix_value", fid, fix.value))
        for problem_id in sorted(fix.solves):
            lines.append(asp.fact("solves", fid, problem_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
        if not sample.story or "alphabetic" not in sample.story.lower():
            raise StoryError("Smoke test story missing text or required seed word.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: alphabetic space adventure with a moral choice. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--mentor", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (problem, value, fix) triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def explain_rejection(problem_id: str, value_id: str, fix_id: str) -> str:
    if problem_id not in PROBLEMS or value_id not in VALUES or fix_id not in FIXES:
        return "(No story: one of the requested options is unknown.)"
    problem = PROBLEMS[problem_id]
    value = VALUES[value_id]
    fix = FIXES[fix_id]
    if fix.value != value.id:
        return (
            f"(No story: fix '{fix_id}' teaches {fix.value}, not {value.id}. "
            f"The repair and the moral value need to match.)"
        )
    if problem_id not in fix.solves:
        return (
            f"(No story: fix '{fix_id}' does not honestly solve problem '{problem_id}'. "
            f"This world only tells stories where the chosen method really finds the missing letter.)"
        )
    return "(No story: this combination is not valid.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.value and args.fix and not valid_combo(args.problem, args.value, args.fix):
        raise StoryError(explain_rejection(args.problem, args.value, args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.problem is None or combo[0] == args.problem)
        and (args.value is None or combo[1] == args.value)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    problem_id, value_id, fix_id = rng.choice(sorted(combos))
    mission_id = args.mission or rng.choice(sorted(MISSIONS))
    hero_name, hero_gender = _pick_child(rng)
    friend_name, friend_gender = _pick_child(rng, avoid=hero_name)
    mentor = args.mentor or rng.choice(["mother", "father"])
    hero_trait = rng.choice(TRAITS)
    friend_trait = rng.choice([t for t in TRAITS if t != hero_trait] or TRAITS)
    return StoryParams(
        mission=mission_id,
        problem=problem_id,
        value=value_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        mentor=mentor,
        hero_trait=hero_trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        mission = MISSIONS[params.mission]
        problem = PROBLEMS[params.problem]
        value = VALUES[params.value]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"Unknown parameter choice: {err}") from err

    if not valid_combo(params.problem, params.value, params.fix):
        raise StoryError(explain_rejection(params.problem, params.value, params.fix))

    world = tell(
        mission=mission,
        problem=problem,
        value=value,
        fix=fix,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        mentor_type=params.mentor,
        hero_trait=params.hero_trait,
        friend_trait=params.friend_trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_items(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (problem, value, fix) combos:\n")
        for problem_id, value_id, fix_id in combos:
            print(f"  {problem_id:12} {value_id:9} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} & {p.friend_name}: {p.problem} / {p.value} / {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
