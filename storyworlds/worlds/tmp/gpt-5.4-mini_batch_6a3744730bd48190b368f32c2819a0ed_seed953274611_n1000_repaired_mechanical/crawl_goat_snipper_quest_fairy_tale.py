#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/crawl_goat_snipper_quest_fairy_tale.py
======================================================================

A tiny fairy-tale quest world: a small hero crawls into a hidden place, a goat
blocks the path, and a snipper tool is either used wisely or misused. The story
model keeps the premise concrete: a child wants to finish a quest, meets a goat
and a snipper, learns a safer way, and ends with proof that the quest changed
the world.

The seed words are intentionally preserved in the prose vocabulary:
- crawl
- goat
- snipper
- quest

The world stays child-facing and fairy-tale flavored, but the state drives the
ending image: a page of stateful changes, not a frozen paragraph with swapped
nouns.
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
SENSE_MIN = 2
BRAVERY_INIT = 5.0


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
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "witch"}
        male = {"boy", "father", "king", "knight"}
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


@dataclass
class Setting:
    id: str
    scene: str
    hidden_place: str
    dark_reason: str
    clue: str
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


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    helps_with: str
    safe: bool = True
    power: int = 0
    sense: int = 0
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    blocks: str
    danger: str
    can_crawl_past: bool = False
    is_animal: bool = False
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use_text: str
    fail_text: str
    sense: int
    power: int
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
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


def _r_rattle(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["rattled"] < THRESHOLD:
            continue
        sig = ("rattle", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in list(world.entities.values()):
            if kid.role == "hero":
                kid.memes["worry"] += 1
        out.append("__rattle__")
    return out


def _r_brave(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["bravery"] < THRESHOLD or e.role != "hero":
            continue
        sig = ("brave", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["resolve"] += 1
        out.append("__resolve__")
    return out


CAUSAL_RULES = [Rule("rattle", _r_rattle), Rule("brave", _r_brave)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def valid_combo(setting: Setting, obstacle: Obstacle, tool: Tool) -> bool:
    return obstacle.can_crawl_past or (obstacle.is_animal and tool.power >= 2) or (tool.power >= 3 and tool.sense >= SENSE_MIN)


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for oid, o in OBSTACLES.items():
            for tid, t in TOOLS.items():
                if valid_combo(SETTINGS[sid], o, t):
                    out.append((sid, oid, tid))
    return out


def story_setup(world: World, hero: Entity, companion: Entity, setting: Setting) -> None:
    hero.memes["bravery"] = BRAVERY_INIT
    companion.memes["hope"] = 1
    world.say(
        f"Once in a fairy tale village, {hero.id} and {companion.id} came to "
        f"{setting.scene}. {setting.clue}"
    )
    world.say(
        f"They had a quest to find the lost key under {setting.hidden_place}, "
        f"where the dark came from {setting.dark_reason}."
    )


def approach(world: World, hero: Entity, obstacle: Obstacle) -> None:
    world.say(
        f"But the path narrowed, and a {obstacle.label} stood in the way. "
        f"It blocked the way to the hidden key."
    )
    world.say(f'{hero.id} took a breath and chose to crawl closer.')


def tempt(world: World, hero: Entity, tool: Tool) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id}'s eyes landed on the {tool.label}. "
        f'"I know," {hero.id} whispered, "the snipper can help me here."'
    )


def warn(world: World, companion: Entity, hero: Entity, obstacle: Obstacle, tool: Tool) -> None:
    companion.memes["care"] += 1
    world.say(
        f'{companion.id} frowned. "{hero.id}, that {tool.label} is for careful '
        f'work, not for wild snipping. And the {obstacle.label} could get hurt."'
    )


def use_tool(world: World, hero: Entity, obstacle: Obstacle, tool: Tool) -> None:
    hero.memes["resolve"] += 1
    obstacle.meters["rattled"] += 1
    world.say(
        f"{hero.id} held the {tool.label} with both hands. "
        f"{tool.use_text.replace('{obstacle}', obstacle.label)}"
    )
    propagate(world, narrate=False)


def fail_use(world: World, hero: Entity, obstacle: Obstacle, tool: Tool) -> None:
    world.say(
        f"{hero.id} tried the {tool.label}, but {tool.fail_text.replace('{obstacle}', obstacle.label)}"
    )
    obstacle.meters["danger"] += 1


def resolve_quest(world: World, hero: Entity, companion: Entity, obstacle: Obstacle, tool: Tool, setting: Setting) -> None:
    hero.memes["joy"] += 1
    companion.memes["joy"] += 1
    world.say(
        f"Then {hero.id} remembered the gentler way: crawl under the low branch, "
        f"step around the {obstacle.label}, and leave the {tool.label} for later."
    )
    world.say(
        f"They found the hidden key at last, shining beside {setting.hidden_place}. "
        f"The quest was done without a scratch on the {obstacle.label}."
    )
    world.say(
        f"That night, the {tool.label} slept in its little pouch, and the {obstacle.label} "
        f"watched the moon from the path, calm and safe."
    )


def tell(setting: Setting, obstacle: Obstacle, tool: Tool, quest: QuestItem,
         hero_name: str = "Mira", hero_gender: str = "girl",
         companion_name: str = "Finn", companion_gender: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    companion = world.add(Entity(id=companion_name, kind="character", type=companion_gender, role="companion"))
    hero.memes["bravery"] = BRAVERY_INIT
    world.facts["setting"] = setting
    world.facts["obstacle"] = obstacle
    world.facts["tool"] = tool
    world.facts["quest"] = quest

    story_setup(world, hero, companion, setting)
    world.para()
    approach(world, hero, obstacle)
    tempt(world, hero, tool)
    warn(world, companion, hero, obstacle, tool)

    if tool.sense < SENSE_MIN:
        fail_use(world, hero, obstacle, tool)
        world.para()
        world.say(
            f"The quest could not go on with such a foolish snipper. "
            f"They turned back and asked a grown-up for a safer way."
        )
        world.say(
            f"The next morning, they returned with a lantern, a loaf of bread, "
            f"and a kinder plan."
        )
    else:
        use_tool(world, hero, obstacle, tool)
        world.para()
        resolve_quest(world, hero, companion, obstacle, tool, setting)

    world.facts["outcome"] = "resolved" if tool.sense >= SENSE_MIN else "turned_back"
    world.facts["hero"] = hero
    world.facts["companion"] = companion
    return world


SETTINGS = {
    "wood": Setting(
        id="wood",
        scene="the edge of an old wood",
        hidden_place="the mossy root",
        dark_reason="the leaves grew thick and made a shadowy arch",
        clue="A silver bird sang above the trees.",
    ),
    "hill": Setting(
        id="hill",
        scene="a windy hill path",
        hidden_place="the stone arch",
        dark_reason="the hill curled around a steep bend",
        clue="A little brook glittered at the side of the road.",
    ),
    "garden": Setting(
        id="garden",
        scene="the queen's garden gate",
        hidden_place="the rose bush",
        dark_reason="the roses grew in a tangled green wall",
        clue="A white butterfly drifted from leaf to leaf.",
    ),
}

OBSTACLES = {
    "goat": Obstacle(
        id="goat",
        label="goat",
        phrase="a stubborn goat",
        blocks="the narrow path",
        danger="it might shove or nip",
        can_crawl_past=True,
        is_animal=True,
    ),
    "bramble": Obstacle(
        id="bramble",
        label="bramble patch",
        phrase="a prickly bramble patch",
        blocks="the low tunnel",
        danger="the thorns could scratch skin",
        can_crawl_past=True,
        is_animal=False,
    ),
    "gate": Obstacle(
        id="gate",
        label="wooden gate",
        phrase="a locked wooden gate",
        blocks="the path",
        danger="it simply stood shut",
        can_crawl_past=False,
        is_animal=False,
    ),
}

QUESTS = {
    "key": QuestItem(
        id="key",
        label="key",
        phrase="the lost silver key",
        helps_with="unlocking the garden door",
        safe=True,
        power=0,
        sense=0,
    )
}

TOOLS = {
    "snipper": Tool(
        id="snipper",
        label="snipper",
        phrase="a small snipper tool",
        use_text="With a careful snip, the tool trimmed a tiny vine near the {obstacle}.",
        fail_text="the snipper slipped and made the path worse.",
        sense=2,
        power=3,
    ),
    "shears": Tool(
        id="shears",
        label="garden shears",
        phrase="a pair of garden shears",
        use_text="With a careful cut, the shears opened a space near the {obstacle}.",
        fail_text="the shears were too heavy and clumsy.",
        sense=3,
        power=4,
    ),
    "twig": Tool(
        id="twig",
        label="twig",
        phrase="a little twig",
        use_text="The twig only wiggled and did not help at all.",
        fail_text="the twig broke at once.",
        sense=0,
        power=0,
    ),
}

GIRL_NAMES = ["Mira", "Nina", "Lila", "Tessa", "June", "Elsa"]
BOY_NAMES = ["Finn", "Owen", "Pip", "Theo", "Ari", "Jace"]


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    tool: str
    quest: str
    hero: str
    hero_gender: str
    companion: str
    companion_gender: str
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
    "goat": [("What is a goat?", "A goat is a farm animal with a beard and strong feet. It likes to nibble leaves and climb."),
             ("Why can a goat be stubborn?", "A goat can plant its feet and refuse to move if it does not want to go.")] ,
    "snipper": [("What is a snipper?", "A snipper is a small cutting tool for careful work. It is not a toy and should be used gently.")],
    "crawl": [("What does it mean to crawl?", "To crawl means to move low to the ground on hands and knees. People crawl when a place is too small or too low to walk through.")],
    "quest": [("What is a quest?", "A quest is a journey to find something important or solve a problem. In fairy tales, quests often have a brave helper and a happy ending.")],
    "key": [("Why is a key useful?", "A key can unlock a door or a box. It helps someone open something that was closed.")],
}

KNOWLEDGE_ORDER = ["crawl", "goat", "snipper", "quest", "key"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s, o, t = f["setting"], f["obstacle"], f["tool"]
    return [
        f'Write a fairy tale quest story that includes the words "{o.label}", "{t.label}", and "crawl".',
        f"Tell a child-friendly quest tale where a hero must crawl past a {o.label} and learns to use the {t.label} wisely.",
        f"Write a small fairy tale about a quest, a {o.label}, and a {t.label}, ending with a safe discovery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    setting = f["setting"]
    obstacle = f["obstacle"]
    tool = f["tool"]
    quest = f["quest"]
    out = [
        QAItem(
            question="Who went on the quest?",
            answer=f"{hero.id} went on the quest with {companion.id}. They traveled together like a tiny fairy-tale team.",
        ),
        QAItem(
            question="What blocked the path?",
            answer=f"A {obstacle.label} blocked the path. It made the way feel tricky, so the hero had to crawl and think carefully.",
        ),
        QAItem(
            question="What was the snipper for?",
            answer=f"The snipper was a small tool for careful cutting, not for rushing or rough play. It was supposed to help with a tiny vine, not scare anyone.",
        ),
        QAItem(
            question="What was the quest about?",
            answer=f"The quest was about finding {quest.phrase}. That treasure mattered because it could help with {quest.helps_with}.",
        ),
    ]
    if f["outcome"] == "resolved":
        out.append(
            QAItem(
                question=f"How did {hero.id} finish the quest?",
                answer=f"{hero.id} remembered a gentler path, crawled under the low place, and left the {tool.label} for careful work only. That choice let the quest end safely.",
            )
        )
        out.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with the key found, the goat calm, and the tool tucked away. The ending showed that the brave choice was also the kind choice.",
            )
        )
    else:
        out.append(
            QAItem(
                question="Why did they turn back?",
                answer=f"The {tool.label} was too foolish for the moment, so they turned back and asked for help. The story made room for a safer plan instead of a rush.",
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"crawl", "quest", world.facts["obstacle"].label, world.facts["tool"].id}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="wood", obstacle="goat", tool="snipper", quest="key",
        hero="Mira", hero_gender="girl", companion="Finn", companion_gender="boy"
    ),
    StoryParams(
        setting="hill", obstacle="bramble", tool="shears", quest="key",
        hero="Nina", hero_gender="girl", companion="Owen", companion_gender="boy"
    ),
    StoryParams(
        setting="garden", obstacle="gate", tool="twig", quest="key",
        hero="Tessa", hero_gender="girl", companion="Pip", companion_gender="boy"
    ),
]


def explain_rejection(obstacle: Obstacle, tool: Tool) -> str:
    if tool.sense < SENSE_MIN:
        return f"(No story: the {tool.label} is too foolish for a fairy-tale quest.)"
    if not obstacle.can_crawl_past and tool.power < 3:
        return f"(No story: the {obstacle.label} cannot be crawled past, and the {tool.label} is not strong enough to help.)"
    return "(No story: this combination does not make a believable quest.)"


def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.obstacle in OBSTACLES and params.tool in TOOLS and params.quest in QUESTS


def outcome_of(params: StoryParams) -> str:
    return "resolved" if TOOLS[params.tool].sense >= SENSE_MIN else "turned_back"


ASP_RULES = r"""
sensible(T) :- tool(T), sense(T,S), min_sense(M), S >= M.
quest_ok(S,O,T) :- setting(S), obstacle(O), tool(T), sensible(T).
resolved :- sensible(snipper).
resolved :- sensible(shears).
turned_back :- tool(twig).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, t.sense))
        lines.append(asp.fact("power", tid, t.power))
    lines.append(asp.fact("min_sense", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest_ok/3."))
    return sorted(set(asp.atoms(model, "quest_ok")))


def asp_verify() -> int:
    import tempfile
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        params = CURATED[0]
        sample = generate(params)
        if not sample.story:
            ok = False
            print("MISMATCH: empty story from curated generate().")
    except Exception as exc:
        ok = False
        print(f"MISMATCH: generate smoke test failed: {exc}")
    print("OK" if ok else "FAILED")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale quest story world: crawl, goat, snipper.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_rejection(OBSTACLES[args.obstacle] if args.obstacle else OBSTACLES["goat"], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.obstacle is None or c[1] == args.obstacle)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obstacle, tool = rng.choice(sorted(combos))
    quest = args.quest or "key"
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(BOY_NAMES if companion_gender == "boy" else GIRL_NAMES)
    if companion == hero:
        companion = companion + "a"
    return StoryParams(
        setting=setting, obstacle=obstacle, tool=tool, quest=quest,
        hero=hero, hero_gender=hero_gender, companion=companion, companion_gender=companion_gender
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("Invalid parameters for this story world.")
    setting = SETTINGS[params.setting]
    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    quest = QUESTS[params.quest]
    world = tell(setting, obstacle, tool, quest, params.hero, params.hero_gender, params.companion, params.companion_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_knowledge_qa(world)],
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
        print(asp_program("#show quest_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible quest combos:")
        for s, o, t in asp_valid_combos():
            print(f"  {s:8} {o:10} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

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
            header = f"### {p.hero}: {p.obstacle} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
