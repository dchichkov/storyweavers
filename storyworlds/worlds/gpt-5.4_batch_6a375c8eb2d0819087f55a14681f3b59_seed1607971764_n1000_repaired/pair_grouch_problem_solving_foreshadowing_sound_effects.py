#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pair_grouch_problem_solving_foreshadowing_sound_effects.py
======================================================================================

A small adventure storyworld about a pair of child explorers, a blocked path, and
a grouchy keeper whose bad mood is really caused by a practical problem. The
story always turns on clue-finding and repair: the children notice an ominous
sound first, meet the grouch, inspect the obstacle, solve it with the right kit,
and then see the ending image change from stuck and noisy to open and welcoming.

The world model prefers a few strong, reasonable variants over many weak ones:
only kits that actually solve the obstacle's problem are allowed, and each place
only supports the obstacles that belong there.

Run it
------
    python storyworlds/worlds/gpt-5.4/pair_grouch_problem_solving_foreshadowing_sound_effects.py
    python storyworlds/worlds/gpt-5.4/pair_grouch_problem_solving_foreshadowing_sound_effects.py --place ridge --obstacle bridge_winch --kit oil_can
    python storyworlds/worlds/gpt-5.4/pair_grouch_problem_solving_foreshadowing_sound_effects.py --place cave --obstacle bridge_winch
    python storyworlds/worlds/gpt-5.4/pair_grouch_problem_solving_foreshadowing_sound_effects.py --all
    python storyworlds/worlds/gpt-5.4/pair_grouch_problem_solving_foreshadowing_sound_effects.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/pair_grouch_problem_solving_foreshadowing_sound_effects.py --asp
    python storyworlds/worlds/gpt-5.4/pair_grouch_problem_solving_foreshadowing_sound_effects.py --verify
"""

from __future__ import annotations

import argparse
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
        female = {"girl", "woman"}
        male = {"boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    trail: str
    destination: str
    ending_view: str
    affords: set[str] = field(default_factory=set)
    keeper_name: str = ""
    keeper_title: str = ""
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
class Obstacle:
    id: str
    label: str
    kind: str
    sound: str
    clue: str
    inspect_text: str
    fix_result: str
    open_text: str
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
class Kit:
    id: str
    label: str
    phrase: str
    fixes: set[str] = field(default_factory=set)
    use_text: str = ""
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
        return [e for e in self.entities.values() if e.role in {"leader", "partner"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


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


def _r_tested_jammed(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.get("obstacle")
    keeper = world.get("keeper")
    if obstacle.meters["tested"] >= THRESHOLD and obstacle.meters["jammed"] >= THRESHOLD:
        sig = ("tested_jammed", obstacle.id)
        if sig not in world.fired:
            world.fired.add(sig)
            obstacle.meters["noise"] += 1
            keeper.memes["grouchy"] += 1
            for kid in world.kids():
                kid.memes["worry"] += 1
            out.append("__noise__")
    return out


def _r_repaired_opens(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.get("obstacle")
    if obstacle.meters["repaired"] >= THRESHOLD and obstacle.meters["open"] < THRESHOLD:
        sig = ("repaired_opens", obstacle.id)
        if sig not in world.fired:
            world.fired.add(sig)
            obstacle.meters["open"] = 1.0
            obstacle.meters["jammed"] = 0.0
            keeper = world.get("keeper")
            keeper.memes["relief"] += 1
            keeper.memes["trust"] += 1
            if keeper.memes["grouchy"] >= THRESHOLD:
                keeper.memes["grouchy"] = max(0.0, keeper.memes["grouchy"] - 1.0)
            out.append("__open__")
    return out


CAUSAL_RULES = [
    Rule(name="tested_jammed", tag="physical", apply=_r_tested_jammed),
    Rule(name="repaired_opens", tag="physical", apply=_r_repaired_opens),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if sent == "__noise__":
                obstacle_cfg = world.facts["obstacle_cfg"]
                world.say(
                    f'The children gave it a tiny try. "{obstacle_cfg.sound}!" '
                    f"the stuck {obstacle_cfg.label} complained, and the noise bounced all over the place."
                )
            elif sent == "__open__":
                obstacle_cfg = world.facts["obstacle_cfg"]
                world.say(
                    f'This time the {obstacle_cfg.label} answered with a happy sound instead of a bad one, '
                    f"and it moved the way it was meant to move."
                )
    return produced


def compatible(setting: Setting, obstacle: Obstacle, kit: Kit) -> bool:
    return obstacle.id in setting.affords and obstacle.kind in kit.fixes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for obstacle_id, obstacle in OBSTACLES.items():
            for kit_id, kit in KITS.items():
                if compatible(setting, obstacle, kit):
                    combos.append((place, obstacle_id, kit_id))
    return sorted(combos)


def explain_rejection(setting: Setting, obstacle: Obstacle, kit: Optional[Kit]) -> str:
    if obstacle.id not in setting.affords:
        return (
            f"(No story: {setting.place} does not have a {obstacle.label} in this world, "
            f"so that adventure path would not make sense there.)"
        )
    if kit is not None and obstacle.kind not in kit.fixes:
        return (
            f"(No story: {kit.label} cannot fix the {obstacle.label}. "
            f"The repair has to match the real problem, so this combination is refused.)"
        )
    return "(No story: this combination is not part of the world.)"


def introduce(world: World, leader: Entity, partner: Entity, setting: Setting) -> None:
    for kid in (leader, partner):
        kid.memes["excitement"] += 1
    world.say(
        f"{leader.id} and {partner.id} were a brave pair of young explorers with a rolled map, "
        f"a snack tin, and bright eyes for adventure."
    )
    world.say(
        f"That morning they set out along {setting.trail}, hoping to reach {setting.destination} before sunset."
    )


def foreshadow(world: World, obstacle: Obstacle, setting: Setting) -> None:
    world.say(
        f"Long before they saw the last turn in the path, a strange sound floated toward them from ahead: "
        f'"{obstacle.sound}... {obstacle.sound}..."'
    )
    world.say(
        f"The noise made the air feel full of warning, as if something near {setting.destination} was asking for help."
    )


def meet_keeper(world: World, leader: Entity, partner: Entity, keeper: Entity, setting: Setting, obstacle: Obstacle) -> None:
    keeper.memes["grouchy"] += 1
    world.say(
        f"At the end of the trail they found {setting.keeper_name}, the {setting.keeper_title}, standing beside the {obstacle.label} "
        f"with folded arms and a stormy face."
    )
    world.say(
        f'"No one is getting through today," {keeper.id} said. "Everything is stuck, noisy, and awful. '
        f'If you ask me, this whole day has turned me into a real grouch."'
    )
    world.say(
        f"{leader.id} and {partner.id} looked at the obstacle, then at each other. They could have grumbled back, but a problem was sitting right in front of them."
    )


def inspect(world: World, leader: Entity, partner: Entity, obstacle: Entity, obstacle_cfg: Obstacle) -> None:
    leader.memes["focus"] += 1
    partner.memes["focus"] += 1
    obstacle.meters["tested"] += 1
    world.say(
        f"{leader.id} knelt beside the {obstacle_cfg.label}, and {partner.id} leaned close. "
        f"They noticed {obstacle_cfg.clue}"
    )
    world.say(obstacle_cfg.inspect_text)
    propagate(world, narrate=True)


def solve(world: World, leader: Entity, partner: Entity, keeper: Entity, obstacle: Entity, obstacle_cfg: Obstacle, kit: Kit) -> None:
    obstacle.meters["repaired"] += 1
    leader.memes["pride"] += 1
    partner.memes["pride"] += 1
    world.say(
        f'"Let\'s try {kit.phrase}," {partner.id} whispered. {leader.id} nodded, and together the pair {kit.use_text}.'
    )
    world.say(obstacle_cfg.fix_result)
    propagate(world, narrate=True)
    keeper.memes["warmth"] += 1
    world.say(
        f"{keeper.id} blinked in surprise. The hard line in {keeper.pronoun('possessive')} face softened, and the grouch in {keeper.pronoun('object')} began to melt away."
    )


def share_reward(world: World, leader: Entity, partner: Entity, keeper: Entity, setting: Setting) -> None:
    for kid in (leader, partner):
        kid.memes["joy"] += 1
    world.say(
        f'"You two saw the clue, thought it through, and fixed it," {keeper.id} said. "That is better than stomping and blaming."'
    )
    world.say(
        f"Then {keeper.pronoun().capitalize()} led them onward, and soon the three of them stood at {setting.destination}, looking out at {setting.ending_view}."
    )
    world.say(
        f"The breeze fluttered their map, the path behind them lay open, and the adventure ended with smiles where the grouching had been."
    )


def tell(setting: Setting, obstacle_cfg: Obstacle, kit: Kit, leader_name: str, leader_gender: str,
         partner_name: str, partner_gender: str) -> World:
    world = World(setting)
    leader = world.add(Entity(id=leader_name, kind="character", type=leader_gender, role="leader"))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner"))
    keeper = world.add(
        Entity(
            id=setting.keeper_name,
            kind="character",
            type="woman" if setting.keeper_title in {"lightkeeper", "cave guide"} else "man",
            role="keeper",
            label=setting.keeper_title,
        )
    )
    obstacle = world.add(Entity(id="obstacle", type="obstacle", label=obstacle_cfg.label, role="obstacle"))
    obstacle.meters["jammed"] = 1.0
    obstacle.meters["tested"] = 0.0
    obstacle.meters["repaired"] = 0.0
    obstacle.meters["open"] = 0.0
    obstacle.meters["noise"] = 0.0
    keeper.memes["grouchy"] = 0.0
    keeper.memes["relief"] = 0.0
    keeper.memes["trust"] = 0.0
    keeper.memes["warmth"] = 0.0
    for kid in (leader, partner):
        kid.memes["worry"] = 0.0
        kid.memes["focus"] = 0.0
        kid.memes["pride"] = 0.0
        kid.memes["joy"] = 0.0
        kid.memes["excitement"] = 0.0

    world.facts.update(
        leader=leader,
        partner=partner,
        keeper=keeper,
        obstacle=obstacle,
        setting=setting,
        obstacle_cfg=obstacle_cfg,
        kit=kit,
    )

    introduce(world, leader, partner, setting)
    foreshadow(world, obstacle_cfg, setting)

    world.para()
    meet_keeper(world, leader, partner, keeper, setting, obstacle_cfg)
    inspect(world, leader, partner, obstacle, obstacle_cfg)

    world.para()
    solve(world, leader, partner, keeper, obstacle, obstacle_cfg, kit)
    share_reward(world, leader, partner, keeper, setting)

    world.facts.update(
        solved=obstacle.meters["open"] >= THRESHOLD,
        sounded_bad=obstacle.meters["noise"] >= THRESHOLD,
        keeper_changed=keeper.memes["warmth"] >= THRESHOLD or keeper.memes["trust"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "ridge": Setting(
        id="ridge",
        place="the windy ridge",
        trail="a ribbon of stone steps up the windy ridge",
        destination="the old lookout platform",
        ending_view="a silver river curling through the valley below",
        affords={"bridge_winch"},
        keeper_name="Toma",
        keeper_title="bridge warden",
        tags={"bridge", "adventure"},
    ),
    "cave": Setting(
        id="cave",
        place="the echo cave",
        trail="a lantern path into the echo cave",
        destination="the glow pool chamber",
        ending_view="blue light trembling over the cave water",
        affords={"lift_pulley"},
        keeper_name="Mira",
        keeper_title="cave guide",
        tags={"cave", "adventure"},
    ),
    "dunes": Setting(
        id="dunes",
        place="the sunlit dunes",
        trail="a winding path between tall dunes",
        destination="the shell tower",
        ending_view="the sea flashing like scattered coins",
        affords={"sand_latch"},
        keeper_name="Borin",
        keeper_title="tower keeper",
        tags={"tower", "adventure"},
    ),
}

OBSTACLES = {
    "bridge_winch": Obstacle(
        id="bridge_winch",
        label="bridge winch",
        kind="oil",
        sound="creeak-clack",
        clue="a dry metal axle with pale scratch marks all around it.",
        inspect_text="The handle would barely move, and every tiny turn sounded thirsty for oil.",
        fix_result="A dark shine spread over the tired metal, and the handle stopped fighting their hands.",
        open_text="The bridge rolled down over the gap.",
        tags={"bridge", "oil"},
    ),
    "lift_pulley": Obstacle(
        id="lift_pulley",
        label="lift pulley",
        kind="untangle",
        sound="whirrr-kink",
        clue="a vine twisted in the pulley wheel like a green knot.",
        inspect_text="The rope kept snagging in the same place, and the pulley shivered instead of turning cleanly.",
        fix_result="The knot came free, the rope straightened, and the pulley spun in one smooth circle.",
        open_text="The little lift basket floated gently down.",
        tags={"pulley", "rope"},
    ),
    "sand_latch": Obstacle(
        id="sand_latch",
        label="stone latch",
        kind="brush",
        sound="grrk-scritch",
        clue="fine sand packed into the latch seam so tightly it looked glued shut.",
        inspect_text="When they pressed the latch, grains scraped and blocked the moving part.",
        fix_result="Dusty sand whisked away in little puffs, and the latch clicked free at last.",
        open_text="The tower gate swung inward.",
        tags={"sand", "latch"},
    ),
}

KITS = {
    "oil_can": Kit(
        id="oil_can",
        label="oil can",
        phrase="the little oil can from their satchel",
        fixes={"oil"},
        use_text="tipped one bright drop after another onto the axle",
        tags={"oil"},
    ),
    "hook_pole": Kit(
        id="hook_pole",
        label="hook pole",
        phrase="the hook pole tied beside the wall",
        fixes={"untangle"},
        use_text="lifted the vine loop up and away from the wheel",
        tags={"rope"},
    ),
    "stiff_brush": Kit(
        id="stiff_brush",
        label="stiff brush",
        phrase="the stiff brush clipped to the tower rail",
        fixes={"brush"},
        use_text="swept the seam with quick, careful strokes",
        tags={"sand"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Zoe", "Ava", "Nora", "Tess", "Ivy", "Ruby"]
BOY_NAMES = ["Finn", "Leo", "Max", "Eli", "Sam", "Theo", "Owen", "Jude"]
TRAITS = ["brave", "careful", "clever", "steady", "curious"]


@dataclass
class StoryParams:
    place: str
    obstacle: str
    kit: str
    leader_name: str
    leader_gender: str
    partner_name: str
    partner_gender: str
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
    "bridge": [
        (
            "What does a bridge winch do?",
            "A bridge winch is a turning machine that helps raise or lower a bridge. If its moving parts get dry or stuck, it can creak and stop working well.",
        )
    ],
    "oil": [
        (
            "Why does oil help squeaky metal?",
            "Oil makes a thin slippery layer between moving metal parts. That helps them rub less, so they move more smoothly and make less noise.",
        )
    ],
    "pulley": [
        (
            "What is a pulley?",
            "A pulley is a wheel with a rope running over it. It helps lift or lower things more easily.",
        )
    ],
    "rope": [
        (
            "Why is a tangled rope a problem?",
            "A tangled rope catches on itself and cannot slide the right way. That can make a lift or pulley jerk and stop.",
        )
    ],
    "sand": [
        (
            "Why can sand make a latch stick?",
            "Tiny grains of sand can sneak into a small gap and block moving parts. Then the latch cannot slide or click the way it should.",
        )
    ],
    "adventure": [
        (
            "What is problem solving in an adventure?",
            "Problem solving means noticing what is wrong, thinking carefully, and trying a smart fix. In an adventure story, that often helps the heroes move forward.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bridge", "oil", "pulley", "rope", "sand", "adventure"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    obstacle_cfg = f["obstacle_cfg"]
    leader = f["leader"]
    partner = f["partner"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the words "pair" and "grouch".',
        f"Tell a story where a pair of child explorers hears {obstacle_cfg.sound} before seeing the problem, meets a grouchy keeper, and solves the trouble at {setting.destination}.",
        f"Write a gentle adventure with sound effects, foreshadowing, and problem solving, starring {leader.id} and {partner.id}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    keeper = f["keeper"]
    setting = f["setting"]
    obstacle_cfg = f["obstacle_cfg"]
    kit = f["kit"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a pair of young explorers, {leader.id} and {partner.id}, and {keeper.id}, the {setting.keeper_title}. They meet because the path to {setting.destination} is blocked by the stuck {obstacle_cfg.label}.",
        ),
        (
            "What sound warned them that something was wrong?",
            f'They heard "{obstacle_cfg.sound}" coming from ahead before they saw the trouble. That sound foreshadowed that a machine near the end of the trail was jammed.',
        ),
        (
            f"Why was {keeper.id} acting like a grouch?",
            f"{keeper.id} was not mean for no reason; {keeper.pronoun('subject')} was upset because the {obstacle_cfg.label} was stuck and making an awful sound. The broken machine had spoiled the day and made {keeper.pronoun('object')} snappy.",
        ),
        (
            "How did the children solve the problem?",
            f"They looked closely, found {obstacle_cfg.clue.rstrip('.')}, and used {kit.phrase}. Because the repair matched the real problem, the stuck {obstacle_cfg.label} could move properly again.",
        ),
    ]
    if f.get("keeper_changed"):
        qa.append(
            (
                f"How did {keeper.id} change by the end?",
                f"{keeper.id} softened after seeing the repair work. The grouchiness faded because {keeper.pronoun('subject')} felt relieved and trusted the children.",
            )
        )
    if f.get("solved"):
        qa.append(
            (
                "How did the story end?",
                f"The path opened, and they reached {setting.destination} together. The ending image showed that the problem was truly solved, because the way ahead was open and peaceful instead of stuck and noisy.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"adventure"}
    tags |= set(world.facts["setting"].tags)
    tags |= set(world.facts["obstacle_cfg"].tags)
    tags |= set(world.facts["kit"].tags)
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
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="ridge",
        obstacle="bridge_winch",
        kit="oil_can",
        leader_name="Lina",
        leader_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
    ),
    StoryParams(
        place="cave",
        obstacle="lift_pulley",
        kit="hook_pole",
        leader_name="Zoe",
        leader_gender="girl",
        partner_name="Max",
        partner_gender="boy",
    ),
    StoryParams(
        place="dunes",
        obstacle="sand_latch",
        kit="stiff_brush",
        leader_name="Nora",
        leader_gender="girl",
        partner_name="Theo",
        partner_gender="boy",
    ),
]


ASP_RULES = r"""
compatible(Place, Obstacle, Kit) :-
    setting(Place), obstacle(Obstacle), kit(Kit),
    affords(Place, Obstacle),
    problem(Obstacle, Kind),
    fixes(Kit, Kind).

#show compatible/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for obstacle_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place, obstacle_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("problem", obstacle_id, obstacle.kind))
    for kit_id, kit in KITS.items():
        lines.append(asp.fact("kit", kit_id))
        for kind in sorted(kit.fixes):
            lines.append(asp.fact("fixes", kit_id, kind))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld: a pair of children meet a grouch and solve the real problem."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--kit", choices=KITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP facts and inline rules")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.obstacle:
        setting = SETTINGS[args.place]
        obstacle = OBSTACLES[args.obstacle]
        if obstacle.id not in setting.affords:
            raise StoryError(explain_rejection(setting, obstacle, KITS.get(args.kit) if args.kit else None))
    if args.place and args.obstacle and args.kit:
        setting = SETTINGS[args.place]
        obstacle = OBSTACLES[args.obstacle]
        kit = KITS[args.kit]
        if not compatible(setting, obstacle, kit):
            raise StoryError(explain_rejection(setting, obstacle, kit))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.kit is None or combo[2] == args.kit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, obstacle_id, kit_id = rng.choice(combos)
    leader_gender = rng.choice(["girl", "boy"])
    partner_gender = "boy" if leader_gender == "girl" else "girl"
    leader_name = _pick_name(rng, leader_gender)
    partner_name = _pick_name(rng, partner_gender, avoid=leader_name)
    return StoryParams(
        place=place,
        obstacle=obstacle_id,
        kit=kit_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.kit not in KITS:
        raise StoryError(f"(Unknown kit: {params.kit})")
    setting = SETTINGS[params.place]
    obstacle = OBSTACLES[params.obstacle]
    kit = KITS[params.kit]
    if not compatible(setting, obstacle, kit):
        raise StoryError(explain_rejection(setting, obstacle, kit))

    world = tell(
        setting=setting,
        obstacle_cfg=obstacle,
        kit=kit,
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
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
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gates:")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, obstacle, kit) combos:\n")
        for place, obstacle, kit in combos:
            print(f"  {place:8} {obstacle:13} {kit}")
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.leader_name} & {p.partner_name}: {p.place} / {p.obstacle} / {p.kit}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
