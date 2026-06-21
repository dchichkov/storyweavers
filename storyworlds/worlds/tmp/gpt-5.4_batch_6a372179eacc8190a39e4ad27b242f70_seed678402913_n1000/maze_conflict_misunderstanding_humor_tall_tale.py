#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/maze_conflict_misunderstanding_humor_tall_tale.py
=============================================================================

A standalone storyworld about a child-sized tall tale in a maze: two playmates
enter a hedge maze to fetch a picnic prize, a misunderstanding turns small
trouble into silly conflict, and the children learn to listen and laugh
together.

The world model tracks physical meters (lostness, stuckness, wind, snack safety)
and emotional memes (pride, worry, irritation, relief, affection). The prose is
rendered from simulated state instead of a frozen template. A reasonableness
gate only allows combinations where a mistaken interpretation can plausibly
cause the conflict and where the chosen helper/tool can actually resolve the
maze problem.

Run it
------
    python storyworlds/worlds/gpt-5.4/maze_conflict_misunderstanding_humor_tall_tale.py
    python storyworlds/worlds/gpt-5.4/maze_conflict_misunderstanding_humor_tall_tale.py --maze hedge --mixup shout --helper gardener
    python storyworlds/worlds/gpt-5.4/maze_conflict_misunderstanding_humor_tall_tale.py --tool kite
    python storyworlds/worlds/gpt-5.4/maze_conflict_misunderstanding_humor_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/maze_conflict_misunderstanding_humor_tall_tale.py --verify
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
HELPFUL_MIN = 2


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
        female = {"girl", "mother", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "man", "gardener", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "gardener": "gardener",
            "goat": "goat",
        }
        return mapping.get(self.type, self.type)


@dataclass
class MazeKind:
    id: str
    label: str
    phrase: str
    turns: str
    boast: str
    hazard: str
    overhead_ok: bool
    breeze_ok: bool
    spread: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Mixup:
    id: str
    hear_line: str
    meant_line: str
    mistaken_belief: str
    conflict_line: str
    repair_line: str
    needs_sound: bool = False
    needs_height: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    sense: int
    power: int
    helps_sound: bool = False
    helps_height: bool = False
    success_text: str = ""
    fail_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    smell: str
    ending_image: str
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


def _r_lost_conflict(world: World) -> list[str]:
    out: list[str] = []
    maze = world.get("maze")
    a = world.get("hero")
    b = world.get("friend")
    if maze.meters["lostness"] >= THRESHOLD and a.memes["misunderstanding"] >= THRESHOLD:
        sig = ("lost_conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["irritation"] += 1
            b.memes["irritation"] += 1
            out.append("__conflict__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    maze = world.get("maze")
    a = world.get("hero")
    b = world.get("friend")
    if maze.meters["found_way"] >= THRESHOLD:
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["relief"] += 1
            b.memes["relief"] += 1
            a.memes["affection"] += 1
            b.memes["affection"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="lost_conflict", tag="social", apply=_r_lost_conflict),
    Rule(name="relief", tag="social", apply=_r_relief),
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


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= HELPFUL_MIN]


def mixup_plausible(maze: MazeKind, mixup: Mixup, tool: Tool) -> bool:
    if mixup.needs_sound and not maze.breeze_ok:
        return False
    if mixup.needs_height and not maze.overhead_ok:
        return False
    if mixup.needs_sound and not tool.helps_sound:
        return False
    if mixup.needs_height and not tool.helps_height:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for maze_id, maze in MAZES.items():
        for mix_id, mixup in MIXUPS.items():
            for tool_id, tool in TOOLS.items():
                if tool.sense < HELPFUL_MIN:
                    continue
                if mixup_plausible(maze, mixup, tool):
                    combos.append((maze_id, mix_id, tool_id))
    return combos


def predict_trouble(world: World, mixup: Mixup) -> dict:
    sim = world.copy()
    do_mixup(sim, mixup, narrate=False)
    return {
        "lostness": sim.get("maze").meters["lostness"],
        "conflict": sim.get("hero").memes["irritation"] + sim.get("friend").memes["irritation"],
    }


def introduce(world: World, hero: Entity, friend: Entity, maze: MazeKind, prize: Prize) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"One windy afternoon, {hero.id} and {friend.id} marched toward {maze.phrase} "
        f"to fetch {prize.phrase} for the family picnic. {maze.boast}"
    )
    world.say(
        f"{hero.id} lifted {hero.pronoun('possessive')} chin and promised that {hero.pronoun()} "
        f"could walk through any maze before a raindrop had time to think about falling."
    )
    world.say(
        f"{friend.id} laughed, because in stories with {hero.id}, even the hedges seemed to lean in to listen."
    )


def enter_maze(world: World, hero: Entity, friend: Entity, maze: MazeKind) -> None:
    world.say(
        f"Inside, the maze had {maze.turns}, and the green walls stood so tall that they looked ready to comb the clouds."
    )
    world.say(
        f"Every corner smelled of leaves and warm dirt, and somewhere ahead the path curled around {maze.hazard}."
    )
    world.get("maze").meters["twists"] += float(maze.spread)


def setup_need(world: World, hero: Entity, friend: Entity, prize: Prize) -> None:
    world.say(
        f'"Follow me," said {hero.id}. "I can smell {prize.smell} all the way from here."'
    )
    world.say(
        f'"That is either very good nose work or very big bragging," said {friend.id}.'
    )


def warn(world: World, hero: Entity, friend: Entity, mixup: Mixup) -> None:
    pred = predict_trouble(world, mixup)
    friend.memes["worry"] += 1
    world.facts["predicted_lostness"] = pred["lostness"]
    world.facts["predicted_conflict"] = pred["conflict"]
    world.say(
        f'{friend.id} listened carefully and said, "{mixup.meant_line}"'
    )
    if pred["lostness"] >= THRESHOLD:
        world.say(
            f"{friend.id} had a prickly feeling that one wrong guess in the maze could turn one silly moment into a real mix-up."
        )


def do_mixup(world: World, mixup: Mixup, narrate: bool = True) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    maze = world.get("maze")
    hero.memes["misunderstanding"] += 1
    hero.memes["pride"] += 1
    maze.meters["lostness"] += 1
    maze.meters["echo"] += 1 if mixup.needs_sound else 0
    maze.meters["tower_need"] += 1 if mixup.needs_height else 0
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"But {hero.id} heard {mixup.hear_line} instead. At once {hero.pronoun()} decided that {mixup.mistaken_belief}."
        )


def quarrel(world: World, hero: Entity, friend: Entity, mixup: Mixup) -> None:
    world.say(
        f'"{mixup.conflict_line}" {hero.id} cried.'
    )
    world.say(
        f'"That is not what I said at all!" said {friend.id}. The two of them stood nose to nose while the maze snickered with rustly leaves.'
    )
    if world.get("hero").memes["irritation"] >= THRESHOLD:
        world.say(
            f"By then they had marched in a proud circle and arrived right back beside the same crooked stone they had already passed twice."
        )


def helper_arrives(world: World, helper: Entity) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"Just then {helper.label} appeared beyond the hedge, as sudden as a rabbit in boots."
    )


def resolve(world: World, helper: Entity, tool: Tool, mixup: Mixup, maze: MazeKind, prize: Prize) -> bool:
    maze_ent = world.get("maze")
    success = tool.power >= 1
    if success:
        maze_ent.meters["found_way"] += 1
        maze_ent.meters["lostness"] = 0.0
        propagate(world, narrate=False)
        world.say(
            f"{helper.label.capitalize()} {tool.success_text}"
        )
        world.say(
            f'Soon everyone could see the truth: {mixup.repair_line}'
        )
        world.say(
            f"The path untangled itself at once, as if the maze had only been waiting for the right kind of listening."
        )
        world.say(
            f"At the middle table sat {prize.phrase}, and it looked so cheerful that even the chairs seemed hungry."
        )
        return True
    world.say(
        f"{helper.label.capitalize()} {tool.fail_text}"
    )
    world.say(
        "But that only led them to another dead end, where even the daisies looked confused."
    )
    return False


def ending(world: World, hero: Entity, friend: Entity, prize: Prize, success: bool) -> None:
    if success:
        hero.memes["humor"] += 1
        friend.memes["humor"] += 1
        world.say(
            f'{hero.id} blinked, then laughed first. "So you did not call me a turnip?"'
        )
        world.say(
            f'"No," said {friend.id}, laughing too. "Though for one minute you were the proudest turnip in the whole maze."'
        )
        world.say(
            f"They carried out {prize.label} together, and {prize.ending_image}."
        )
    else:
        world.say(
            f"In the end they had to wait quietly until a grown-up walked in after them. The story still became funny later, but first it had to become safe."
        )


MAZES = {
    "hedge": MazeKind(
        id="hedge",
        label="hedge maze",
        phrase="the tallest hedge maze in the county fair",
        turns="turns enough to make a squirrel ask for directions",
        boast="People said the top of that maze scratched the bellies of passing clouds.",
        hazard="a whispery fountain",
        overhead_ok=True,
        breeze_ok=True,
        spread=2,
        tags={"maze", "hedge", "outside"},
    ),
    "corn": MazeKind(
        id="corn",
        label="corn maze",
        phrase="the autumn corn maze behind the red barn",
        turns="rows that wiggled like yellow snakes wearing green hats",
        boast="The corn was so high that crows needed lunch before flying over it.",
        hazard="a shiny scarecrow",
        overhead_ok=False,
        breeze_ok=True,
        spread=2,
        tags={"maze", "corn", "outside"},
    ),
    "snow": MazeKind(
        id="snow",
        label="snow maze",
        phrase="the snow maze built beside the winter pond",
        turns="icy turns bright enough to make mittens squint",
        boast="That snow maze rose so high that the moon nearly stubbed its toe on it.",
        hazard="a squeaky blue gate",
        overhead_ok=True,
        breeze_ok=False,
        spread=1,
        tags={"maze", "snow", "winter"},
    ),
}

MIXUPS = {
    "shout": Mixup(
        id="shout",
        hear_line='friend said, "Shout if you spot the middle!"',
        meant_line="Shout if you spot the middle!",
        mistaken_belief="being loud was the secret map",
        conflict_line="I am following your plan exactly, and it is an excellent plan!",
        needs_sound=True,
        needs_height=False,
        tags={"misunderstanding", "echo", "maze"},
    ),
    "climb": Mixup(
        id="climb",
        hear_line='friend said, "Climb if you spot the middle!"',
        meant_line="Wave if you spot the middle!",
        mistaken_belief="the only sensible thing was to scramble onto the little viewing stump at every corner",
        conflict_line="You said to climb, and I have been climbing with great dedication!",
        needs_sound=False,
        needs_height=True,
        tags={"misunderstanding", "height", "maze"},
    ),
    "left": Mixup(
        id="left",
        hear_line='friend said, "Left at the lantern!"',
        meant_line="Let us stop at the lantern!",
        mistaken_belief="every left turn in the maze was blessed by genius",
        conflict_line="I trusted your lefts, and now even my feet are arguing!",
        needs_sound=True,
        needs_height=False,
        tags={"misunderstanding", "echo", "maze"},
    ),
}

TOOLS = {
    "kite": Tool(
        id="kite",
        label="kite",
        phrase="a bright red kite",
        sense=3,
        power=2,
        helps_sound=False,
        helps_height=True,
        success_text="sent up a bright red kite on a long string, and its tail pointed above the twists toward the middle opening",
        fail_text="sent up a kite, but the string only bobbed over another wall and told them almost nothing",
        qa_text="used a kite above the maze so they could see where the middle opening was",
        tags={"kite", "maze", "up"},
    ),
    "bell": Tool(
        id="bell",
        label="bell",
        phrase="a brass handbell",
        sense=3,
        power=2,
        helps_sound=True,
        helps_height=False,
        success_text="rang a brass handbell in a steady pattern, so the echoes stopped being silly and started sounding like a real guide",
        fail_text="rang a bell, but the sound bounced around too wildly to help",
        qa_text="rang a bell in a careful pattern so they could follow the truest echo",
        tags={"bell", "sound", "maze"},
    ),
    "ladder": Tool(
        id="ladder",
        label="ladder",
        phrase="a folding ladder",
        sense=2,
        power=2,
        helps_sound=False,
        helps_height=True,
        success_text="opened a short ladder by the wall, climbed high enough to peek over the green tops, and called down the right turn",
        fail_text="opened a ladder, but it was still not high enough to show a safe path",
        qa_text="climbed a short ladder to look over the maze and call the right turn",
        tags={"ladder", "up", "maze"},
    ),
    "megaphone": Tool(
        id="megaphone",
        label="megaphone",
        phrase="a paper megaphone",
        sense=2,
        power=2,
        helps_sound=True,
        helps_height=False,
        success_text="used a paper megaphone to send one clear sentence through the paths, and this time every word arrived wearing its proper hat",
        fail_text="used a megaphone, but the maze swallowed half the words anyway",
        qa_text="used a megaphone so the directions sounded clear instead of muddled",
        tags={"megaphone", "sound", "maze"},
    ),
    "spoon": Tool(
        id="spoon",
        label="spoon",
        phrase="a picnic spoon",
        sense=1,
        power=0,
        helps_sound=False,
        helps_height=False,
        success_text="waved a spoon with great confidence",
        fail_text="waved a spoon bravely, which impressed nobody except a beetle",
        qa_text="waved a spoon",
        tags={"spoon"},
    ),
}

PRIZES = {
    "pie": Prize(
        id="pie",
        label="the pie",
        phrase="a blueberry pie under a checked cloth",
        smell="blueberries and sugar",
        ending_image="blueberry smell streamed behind them like a purple parade flag",
        tags={"pie", "picnic"},
    ),
    "lemonade": Prize(
        id="lemonade",
        label="the lemonade jug",
        phrase="a glass jug of lemonade with slices floating like tiny yellow boats",
        smell="lemons and summer",
        ending_image="the lemonade flashed in the sun like a piece of friendly treasure",
        tags={"lemonade", "picnic"},
    ),
    "sandwiches": Prize(
        id="sandwiches",
        label="the sandwich basket",
        phrase="a basket of picnic sandwiches wrapped in a blue napkin",
        smell="bread and dill",
        ending_image="the blue napkin bobbed between them like a little victory flag",
        tags={"sandwiches", "picnic"},
    ),
}

HELPERS = {
    "gardener": {
        "type": "gardener",
        "label": "the gardener",
        "phrase": "the gardener with grass on his boots",
        "tags": {"gardener", "helper"},
    },
    "grandma": {
        "type": "grandmother",
        "label": "Grandma June",
        "phrase": "Grandma June with a basket on her arm",
        "tags": {"grandma", "helper"},
    },
    "goat": {
        "type": "goat",
        "label": "Biscuit the goat",
        "phrase": "Biscuit the goat with one ribbon on one horn",
        "tags": {"goat", "helper", "humor"},
    },
}

GIRL_NAMES = ["Lila", "Mina", "Poppy", "Ruth", "Daisy", "Tess", "Nell", "Ivy"]
BOY_NAMES = ["Jasper", "Milo", "Toby", "Finn", "Ned", "Arlo", "Ben", "Eli"]
TRAITS = ["bold", "cheerful", "boasty", "eager", "sparky", "sturdy"]


@dataclass
class StoryParams:
    maze: str
    mixup: str
    tool: str
    helper: str
    prize: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


def pair_noun(hero: Entity, friend: Entity) -> str:
    if hero.type == "girl" and friend.type == "girl":
        return "two girls"
    if hero.type == "boy" and friend.type == "boy":
        return "two boys"
    return "two friends"


def tell(
    maze: MazeKind,
    mixup: Mixup,
    tool: Tool,
    prize: Prize,
    helper_key: str,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, traits=[trait], role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, traits=["careful"], role="friend"))
    maze_ent = world.add(Entity(id="maze", kind="thing", type="maze", label=maze.label, phrase=maze.phrase, tags=set(maze.tags)))
    prize_ent = world.add(Entity(id="prize", kind="thing", type="prize", label=prize.label, phrase=prize.phrase, tags=set(prize.tags)))
    helper_cfg = HELPERS[helper_key]
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_cfg["type"],
            label=helper_cfg["label"],
            phrase=helper_cfg["phrase"],
            tags=set(helper_cfg["tags"]),
            role="helper",
        )
    )

    introduce(world, hero, friend, maze, prize)
    enter_maze(world, hero, friend, maze)
    setup_need(world, hero, friend, prize)

    world.para()
    warn(world, hero, friend, mixup)
    do_mixup(world, mixup, narrate=True)
    quarrel(world, hero, friend, mixup)

    world.para()
    helper_arrives(world, helper)
    success = resolve(world, helper, tool, mixup, maze, prize)
    ending(world, hero, friend, prize, success)

    world.facts.update(
        maze_cfg=maze,
        mixup_cfg=mixup,
        tool_cfg=tool,
        prize_cfg=prize,
        helper_cfg=helper_cfg,
        hero=hero,
        friend=friend,
        helper=helper,
        prize=prize_ent,
        outcome="solved" if success else "stuck",
        misunderstanding=hero.memes["misunderstanding"] >= THRESHOLD,
        conflict=hero.memes["irritation"] + friend.memes["irritation"] >= THRESHOLD,
        found_way=maze_ent.meters["found_way"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "maze": [
        (
            "What is a maze?",
            "A maze is a place with many paths and wrong turns. You have to choose carefully to find the way through."
        )
    ],
    "echo": [
        (
            "What is an echo?",
            "An echo is a sound that bounces back after you make noise. In a twisty place, that can make directions sound confusing."
        )
    ],
    "kite": [
        (
            "How can a kite help in a maze?",
            "If a kite flies above high walls, it can show where open space is. Seeing from higher up can make the path easier to understand."
        )
    ],
    "bell": [
        (
            "Why might a bell help someone who is lost?",
            "A bell makes a clear repeated sound. A steady sound can help people follow the same direction instead of guessing."
        )
    ],
    "ladder": [
        (
            "Why is looking from high up useful?",
            "When you can look from high up, you can see more of the paths at once. That helps you choose a better direction."
        )
    ],
    "megaphone": [
        (
            "What does a megaphone do?",
            "A megaphone makes a voice louder and clearer. That can help people hear directions better."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or understands something the wrong way. It can cause problems until people stop and explain."
        )
    ],
    "conflict": [
        (
            "What is a conflict in a story?",
            "A conflict is a problem or struggle between people or between a person and a situation. It gives the story tension until something changes."
        )
    ],
    "picnic": [
        (
            "What is a picnic?",
            "A picnic is a meal people take outside to eat together. They often bring food in baskets or cloth-covered dishes."
        )
    ],
}
KNOWLEDGE_ORDER = ["maze", "misunderstanding", "conflict", "echo", "kite", "bell", "ladder", "megaphone", "picnic"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    maze = f["maze_cfg"]
    mixup = f["mixup_cfg"]
    prize = f["prize_cfg"]
    return [
        f'Write a child-facing tall tale about a maze where a misunderstanding causes a funny conflict, and include the word "maze".',
        f"Tell a humorous story about {hero.label} and {friend.label} getting turned around in {maze.label} because one sentence is heard the wrong way.",
        f"Write a playful tall tale where two children go after {prize.label}, quarrel because of a misunderstanding, and then laugh once the truth is cleared up.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    maze = f["maze_cfg"]
    mixup = f["mixup_cfg"]
    tool = f["tool_cfg"]
    prize = f["prize_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, friend)}, {hero.label} and {friend.label}, who went into a {maze.label}. {helper.label.capitalize()} also helped when the mix-up got them stuck."
        ),
        (
            f"Why did {hero.label} and {friend.label} go into the maze?",
            f"They went in to fetch {prize.phrase} for the picnic. That simple job turned harder because the maze had so many twisting paths."
        ),
        (
            "What was the misunderstanding?",
            f"{friend.label} meant to say, \"{mixup.meant_line}\" but {hero.label} heard {mixup.hear_line}. Because of that mistake, {hero.label} believed that {mixup.mistaken_belief}."
        ),
    ]
    if f["conflict"]:
        qa.append(
            (
                "How did the misunderstanding cause a conflict?",
                f"It made {hero.label} and {friend.label} argue about what had been said. While they were busy defending themselves, they walked in circles and became even more lost in the maze."
            )
        )
    if f["found_way"]:
        qa.append(
            (
                f"How did {helper.label} help them?",
                f"{helper.label.capitalize()} {tool.qa_text}. That solved both problems at once, because it showed the right path and helped everyone understand what had really been said."
            )
        )
        qa.append(
            (
                "Why is the ending funny?",
                f"The ending is funny because the great argument came from hearing one small sentence the wrong way. Once the truth was clear, the children could laugh at how serious they had sounded in the middle of such a silly mix-up."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"maze", "misunderstanding", "conflict", "picnic"}
    mixup = f["mixup_cfg"]
    tool = f["tool_cfg"]
    if mixup.needs_sound:
        tags.add("echo")
    if tool.id in {"kite", "bell", "ladder", "megaphone"}:
        tags.add(tool.id)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        shown_label = ent.label or ent.id
        lines.append(f"  {ent.id:8} ({ent.type:11}) label={shown_label!r} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        maze="hedge",
        mixup="shout",
        tool="bell",
        helper="gardener",
        prize="pie",
        hero="Jasper",
        hero_gender="boy",
        friend="Mina",
        friend_gender="girl",
        trait="boasty",
    ),
    StoryParams(
        maze="snow",
        mixup="climb",
        tool="kite",
        helper="grandma",
        prize="lemonade",
        hero="Lila",
        hero_gender="girl",
        friend="Toby",
        friend_gender="boy",
        trait="bold",
    ),
    StoryParams(
        maze="corn",
        mixup="left",
        tool="megaphone",
        helper="goat",
        prize="sandwiches",
        hero="Milo",
        hero_gender="boy",
        friend="Daisy",
        friend_gender="girl",
        trait="cheerful",
    ),
]


def explain_rejection(maze: MazeKind, mixup: Mixup, tool: Tool) -> str:
    if tool.sense < HELPFUL_MIN:
        return (
            f"(No story: {tool.label} is too weak and silly to solve a real maze problem here. "
            f"Pick a more useful helper tool like {', '.join(sorted(t.id for t in sensible_tools()))}.)"
        )
    if mixup.needs_sound and not maze.breeze_ok:
        return (
            f"(No story: this misunderstanding depends on sound carrying and bouncing, but the {maze.label} "
            f"does not support that kind of echo trick in this world.)"
        )
    if mixup.needs_height and not maze.overhead_ok:
        return (
            f"(No story: this misunderstanding needs a high-overhead view, but the {maze.label} "
            f"does not allow that kind of look-over resolution.)"
        )
    if mixup.needs_sound and not tool.helps_sound:
        return (
            f"(No story: {mixup.id} needs a sound-clearing tool, but {tool.label} does not help with hearing or echoes.)"
        )
    if mixup.needs_height and not tool.helps_height:
        return (
            f"(No story: {mixup.id} needs a height-based fix, but {tool.label} cannot help anyone see over the maze.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
sensible_tool(T) :- tool(T), sense(T, S), helpful_min(M), S >= M.

plausible(Mz, Mix) :- maze(Mz), mixup(Mix),
                      not needs_sound(Mix), not needs_height(Mix).
plausible(Mz, Mix) :- maze(Mz), mixup(Mix),
                      needs_sound(Mix), breeze_ok(Mz), not needs_height(Mix).
plausible(Mz, Mix) :- maze(Mz), mixup(Mix),
                      needs_height(Mix), overhead_ok(Mz), not needs_sound(Mix).

tool_fits(Mix, T) :- mixup(Mix), tool(T),
                     not needs_sound(Mix), not needs_height(Mix).
tool_fits(Mix, T) :- mixup(Mix), tool(T),
                     needs_sound(Mix), helps_sound(T), not needs_height(Mix).
tool_fits(Mix, T) :- mixup(Mix), tool(T),
                     needs_height(Mix), helps_height(T), not needs_sound(Mix).

valid(Mz, Mix, T) :- plausible(Mz, Mix), sensible_tool(T), tool_fits(Mix, T).

outcome(solved) :- chosen_tool(T), power(T, P), P >= 1.
outcome(stuck) :- chosen_tool(T), power(T, P), P < 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for maze_id, maze in MAZES.items():
        lines.append(asp.fact("maze", maze_id))
        if maze.overhead_ok:
            lines.append(asp.fact("overhead_ok", maze_id))
        if maze.breeze_ok:
            lines.append(asp.fact("breeze_ok", maze_id))
    for mix_id, mixup in MIXUPS.items():
        lines.append(asp.fact("mixup", mix_id))
        if mixup.needs_sound:
            lines.append(asp.fact("needs_sound", mix_id))
        if mixup.needs_height:
            lines.append(asp.fact("needs_height", mix_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        lines.append(asp.fact("power", tool_id, tool.power))
        if tool.helps_sound:
            lines.append(asp.fact("helps_sound", tool_id))
        if tool.helps_height:
            lines.append(asp.fact("helps_height", tool_id))
    lines.append(asp.fact("helpful_min", HELPFUL_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("chosen_tool", params.tool)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    tool = TOOLS[params.tool]
    return "solved" if tool.power >= 1 else "stuck"


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

    for params in CURATED:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print(f"MISMATCH in outcome for curated case: {params}")
            break
    else:
        print(f"OK: outcome model matches on {len(CURATED)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        _ = sample.to_json()
        print("OK: smoke test generate() and serialization succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a maze misunderstanding becomes a funny tall tale."
    )
    ap.add_argument("--maze", choices=MAZES)
    ap.add_argument("--mixup", choices=MIXUPS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.maze and args.mixup and args.tool:
        maze = MAZES[args.maze]
        mixup = MIXUPS[args.mixup]
        tool = TOOLS[args.tool]
        if not mixup_plausible(maze, mixup, tool):
            raise StoryError(explain_rejection(maze, mixup, tool))
        if tool.sense < HELPFUL_MIN:
            raise StoryError(explain_rejection(maze, mixup, tool))
    elif args.tool and TOOLS[args.tool].sense < HELPFUL_MIN:
        maze = MAZES[args.maze] if args.maze else next(iter(MAZES.values()))
        mixup = MIXUPS[args.mixup] if args.mixup else next(iter(MIXUPS.values()))
        raise StoryError(explain_rejection(maze, mixup, TOOLS[args.tool]))

    combos = [
        combo for combo in valid_combos()
        if (args.maze is None or combo[0] == args.maze)
        and (args.mixup is None or combo[1] == args.mixup)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    maze_id, mixup_id, tool_id = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    prize = args.prize or rng.choice(sorted(PRIZES))
    hero, hero_gender = _pick_child(rng)
    friend, friend_gender = _pick_child(rng, avoid=hero)
    trait = rng.choice(TRAITS)
    return StoryParams(
        maze=maze_id,
        mixup=mixup_id,
        tool=tool_id,
        helper=helper,
        prize=prize,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        maze = MAZES[params.maze]
        mixup = MIXUPS[params.mixup]
        tool = TOOLS[params.tool]
        prize = PRIZES[params.prize]
        if params.helper not in HELPERS:
            raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    except KeyError as err:
        raise StoryError(f"(No story: invalid parameter {err!s}.)") from err

    if tool.sense < HELPFUL_MIN or not mixup_plausible(maze, mixup, tool):
        raise StoryError(explain_rejection(maze, mixup, tool))

    world = tell(
        maze=maze,
        mixup=mixup,
        tool=tool,
        prize=prize,
        helper_key=params.helper,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        trait=params.trait,
    )

    story_text = world.render().replace(" hero ", f" {params.hero} ").replace(" friend ", f" {params.friend} ")
    story_text = story_text.replace("hero", params.hero).replace("friend", params.friend)

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
        print(f"{len(combos)} compatible (maze, mixup, tool) combos:\n")
        for maze, mixup, tool in combos:
            print(f"  {maze:7} {mixup:7} {tool}")
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.friend}: {p.maze} / {p.mixup} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
