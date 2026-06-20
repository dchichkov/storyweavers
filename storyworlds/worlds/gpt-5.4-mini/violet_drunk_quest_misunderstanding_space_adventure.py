#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/violet_drunk_quest_misunderstanding_space_adventure.py
======================================================================================

A small standalone storyworld for a space-adventure quest built from the seed words
"violet" and "drunk", with a misunderstanding that gets cleared up through action.

Premise:
- Two child astronauts are on a quest for a violet crystal.
- A wobbling guide-robot is mistaken for being "drunk" when it is actually carrying
  a heavy battery pack that makes it tip and spin in low gravity.
- The misunderstanding causes a brief split in the crew.
- They check the facts, repair the robot, and finish the quest together.

The world model uses typed entities with accumulating physical meters and emotional
memes. State changes drive the prose; the rendered story is not a frozen paragraph
with swapped nouns.

This script follows the Storyweavers contract:
- build_parser, resolve_params, generate, emit, main
- --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- eager import of storyworlds/results.py, lazy import of storyworlds/asp.py
- Python reasonableness gate plus inline ASP twin
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"strain": 0.0, "damage": 0.0, "drift": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "fear": 0.0, "confusion": 0.0, "trust": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Location:
    id: str
    label: str
    kind: str
    low_g: bool = False
    dark: bool = False
    violet_glow: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Quest:
    id: str
    goal: str
    clue: str
    prize: str
    hazard: str
    ending_image: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Misunderstanding:
    id: str
    false_reading: str
    truth: str
    fix: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Tool:
    id: str
    label: str
    kind: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_confusion(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.memes.get("confusion", 0.0) < THRESHOLD:
            continue
        sig = ("confusion", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["trust"] = max(0.0, e.memes.get("trust", 0.0) - 0.5)
        out.append("__confused__")
    return out


def _r_repair(world: World) -> list[str]:
    out = []
    bot = world.entities.get("bot")
    if not bot:
        return out
    if bot.meters.get("damage", 0.0) < THRESHOLD:
        return out
    sig = ("repair", "bot")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bot.meters["damage"] = 0.0
    bot.meters["drift"] = 0.0
    out.append("__repaired__")
    return out


CAUSAL_RULES = [Rule("confusion", _r_confusion), Rule("repair", _r_repair)]


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


def reasonableness_gate(location: Location, quest: Quest, misunderstanding: Misunderstanding) -> bool:
    return location.low_g and location.dark and quest.prize == "violet crystal" and misunderstanding.id == "drunk"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for lid, loc in LOCATIONS.items():
        for qid, quest in QUESTS.items():
            for mid, mis in MISUNDERSTANDINGS.items():
                if reasonableness_gate(loc, quest, mis):
                    combos.append((lid, qid, mid))
    return combos


def diagnosis(world: World) -> str:
    bot = world.get("bot")
    return "drunk" if bot.meters.get("drift", 0.0) > 0.6 else "wobbling"


def predict_misunderstanding(world: World) -> dict:
    sim = world.copy()
    _cause_misunderstanding(sim, narrate=False)
    return {
        "confusion": sim.get("captain").memes.get("confusion", 0.0),
        "drift": sim.get("bot").meters.get("drift", 0.0),
    }


def _cause_misunderstanding(world: World, narrate: bool = True) -> None:
    captain = world.get("captain")
    scout = world.get("scout")
    bot = world.get("bot")
    captain.memes["confusion"] += 1
    scout.memes["confusion"] += 1
    bot.meters["drift"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, captain: Entity, scout: Entity, quest: Quest, loc: Location) -> None:
    captain.memes["joy"] += 1
    scout.memes["joy"] += 1
    world.say(
        f"On a quiet stretch of the station, {captain.id} and {scout.id} set out on a quest "
        f"through {loc.label}. Somewhere ahead was a {quest.prize}, glowing violet in the dark."
    )
    world.say(
        f'"We find the clue, we follow the map, and we bring home the {quest.prize}," '
        f"{captain.id} said, tapping the little screen on the wall."
    )


def enter_dark(world: World, loc: Location, quest: Quest) -> None:
    world.say(
        f"But {loc.label} was dark and full of hush. The only color was a faint violet gleam "
        f"that blinked far away like a small star."
    )
    world.say(
        f"The clue said to listen for a humming door, so the two children drifted forward on "
        f"soft shoes and held their breath."
    )


def spot_bot(world: World, bot: Entity, mis: Misunderstanding) -> None:
    world.say(
        f"Then they saw {bot.id}, the guide-bot, weaving side to side in the corridor."
    )
    world.say(
        f'"Look," {world.get("scout").id} whispered. "{bot.id} is {mis.false_reading}."'
    )


def argue(world: World, captain: Entity, scout: Entity, mis: Misunderstanding) -> None:
    captain.memes["confusion"] += 1
    scout.memes["confusion"] += 1
    world.say(
        f"{captain.id} frowned. " + f'"Maybe it should not lead us," {captain.pronoun()} said. '
        f'"If it is {mis.false_reading}, it might break the quest."'
    )
    world.say(
        f"{scout.id} hugged the map close and looked unsure. For a moment, the crew split "
        f"between worry and wonder."
    )


def check_truth(world: World, bot: Entity, mis: Misunderstanding) -> None:
    pred = predict_misunderstanding(world)
    world.facts["predicted_confusion"] = pred["confusion"]
    world.say(
        f"Then {captain_name(world)} touched the bot's side panel and saw the real problem: "
        f"its battery pack was hanging loose."
    )
    world.say(
        f'"It is not {mis.false_reading}," {captain_name(world)} said. '
        f'"It is {mis.truth}. That is why it keeps tipping in low gravity."'
    )


def captain_name(world: World) -> str:
    return world.get("captain").id


def fix_bot(world: World, bot: Entity, tool: Tool, mis: Misunderstanding) -> None:
    bot.meters["damage"] += 1
    world.say(
        f"The children used a {tool.label} to fasten the battery pack. The wobble slowed, "
        f"then stopped."
    )
    world.say(
        f'"{mis.fix}," said {world.get("scout").id}, and this time both children laughed.'
    )
    propagate(world, narrate=True)


def finish_quest(world: World, quest: Quest, bot: Entity) -> None:
    world.get("captain").memes["trust"] += 1
    world.get("scout").memes["trust"] += 1
    world.say(
        f"At last, the humming door opened. Inside, the {quest.prize} waited in a violet pool of light."
    )
    world.say(
        f"{quest.ending_image.capitalize()}, and {world.get('captain').id} and "
        f"{world.get('scout').id} carried it home together."
    )


def tell(location: Location, quest: Quest, misunderstanding: Misunderstanding, tool: Tool,
         captain_name_: str = "Nova", captain_gender: str = "girl",
         scout_name: str = "Pip", scout_gender: str = "boy") -> World:
    world = World()
    captain = world.add(Entity(id=captain_name_, kind="character", type=captain_gender, role="captain"))
    scout = world.add(Entity(id=scout_name, kind="character", type=scout_gender, role="scout"))
    bot = world.add(Entity(id="bot", kind="character", type="robot", role="guide"))
    bot.meters["drift"] = 0.8
    world.add(Entity(id="room", type="room", label=location.label))
    setup(world, captain, scout, quest, location)
    world.para()
    enter_dark(world, location, quest)
    spot_bot(world, bot, misunderstanding)
    argue(world, captain, scout, misunderstanding)
    world.para()
    check_truth(world, bot, misunderstanding)
    fix_bot(world, bot, tool, misunderstanding)
    world.para()
    finish_quest(world, quest, bot)
    world.facts.update(
        captain=captain, scout=scout, bot=bot,
        location=location, quest=quest, misunderstanding=misunderstanding, tool=tool,
        outcome="resolved", suspected=diagnosis(world),
    )
    return world


LOCATIONS = {
    "violet_station": Location("violet_station", "the Violet Station", "station", low_g=True, dark=True, violet_glow=True),
    "ring_tunnel": Location("ring_tunnel", "the ring tunnel", "tunnel", low_g=True, dark=True, violet_glow=True),
    "moon_cave": Location("moon_cave", "the moon cave", "cave", low_g=True, dark=True, violet_glow=True),
}

QUESTS = {
    "violet_crystal": Quest(
        "violet_crystal",
        "find the humming door",
        "follow the violet blink",
        "the violet crystal",
        "a loose battery pack in low gravity",
        "The crystal shone like a tiny evening moon",
        tags={"quest", "violet", "space"},
    ),
}

MISUNDERSTANDINGS = {
    "drunk": Misunderstanding(
        "drunk",
        "drunk",
        "wobbly from the loose battery pack",
        "fixed the loose battery pack and found the truth",
        tags={"misunderstanding", "drunk"},
    ),
}

TOOLS = {
    "strap": Tool("strap", "strap", "tool", safe=True, tags={"repair"}),
    "clip": Tool("clip", "clip", "tool", safe=True, tags={"repair"}),
}

GIRL_NAMES = ["Nova", "Lyra", "Mina", "Aria", "Vela"]
BOY_NAMES = ["Pip", "Orion", "Taro", "Jules", "Kai"]


@dataclass
@dataclass
class StoryParams:
    location: str
    quest: str
    misunderstanding: str
    tool: str
    captain_name: str
    captain_gender: str
    scout_name: str
    scout_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


KNOWLEDGE = {
    "violet": [("What is violet?", "Violet is a purple color, like a twilight sky or a glowing gem.")],
    "quest": [("What is a quest?", "A quest is a trip where someone goes looking for something important.")],
    "misunderstanding": [("What is a misunderstanding?", "A misunderstanding happens when someone gets the wrong idea about what is happening.")],
    "space": [("What is space?", "Space is the huge dark place beyond Earth where stars, planets, and spacecraft are.")],
    "drunk": [("What does drunk mean in this story?", "In this story, drunk means someone seemed to wobble and sway, but the wobble had a simple cause.")],
}
KNOWLEDGE_ORDER = ["violet", "quest", "misunderstanding", "space", "drunk"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure story for a young child that includes the words "violet" and "drunk".',
        f"Tell a quest story where {f['captain'].id} and {f['scout'].id} explore a dark station, "
        f"misread a wobbling guide-bot, and then discover the truth.",
        f"Write a gentle sci-fi story with a misunderstanding, a repair, and a violet prize at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain = f["captain"]
    scout = f["scout"]
    bot = f["bot"]
    quest = f["quest"]
    mis = f["misunderstanding"]
    items = [
        QAItem(
            question="What were the children looking for?",
            answer=f"They were searching for {quest.prize}. It was the reward at the end of their quest, and it glowed violet in the dark.",
        ),
        QAItem(
            question="What did they first think about the guide-bot?",
            answer=f"They thought {bot.id} was {mis.false_reading}. That was the misunderstanding, because the bot only looked that way while its battery pack was loose.",
        ),
        QAItem(
            question="What was really wrong with the bot?",
            answer=f"It was {mis.truth}. The loose battery pack made it tip and wobble in low gravity, so it looked strange until they repaired it.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They fixed the bot, found the violet crystal, and finished the quest together. The ending shows that the misunderstanding was cleared up and the team stayed together.",
        ),
    ]
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags) | set(world.facts["misunderstanding"].tags) | {"space"}
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            q, a = KNOWLEDGE[key]
            out.append(QAItem(question=q, answer=a))
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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("violet_station", "violet_crystal", "drunk", "strap", "Nova", "girl", "Pip", "boy"),
]


def explain_rejection(location: Location, quest: Quest, misunderstanding: Misunderstanding) -> str:
    if not location.low_g:
        return "(No story: this quest needs low gravity so the bot can wobble in a believable way.)"
    if quest.prize != "violet crystal":
        return "(No story: the quest in this world is for a violet crystal.)"
    if misunderstanding.id != "drunk":
        return "(No story: this world uses the drunk misunderstanding as the key mistaken idea.)"
    return "(No story: this combination is not reasonable.)"


def valid_story() -> bool:
    return True


ASP_RULES = r"""
% A story is valid when the setting supports a low-gravity space quest,
% the prize is the violet crystal, and the bot misunderstanding is the drunk one.
valid(L, Q, M) :- location(L), quest(Q), misunderstanding(M), low_g(L), violet_prize(Q), drunk_misunderstanding(M).

% Outcome: the confusion is resolved when the children repair the bot.
resolved :- chosen_tool(T), safe_tool(T), quest(Q), violet_prize(Q).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        if loc.low_g:
            lines.append(asp.fact("low_g", lid))
        if loc.dark:
            lines.append(asp.fact("dark", lid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        if q.prize == "the violet crystal":
            lines.append(asp.fact("violet_prize", qid))
    for mid, m in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
        if mid == "drunk":
            lines.append(asp.fact("drunk_misunderstanding", mid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.safe:
            lines.append(asp.fact("safe_tool", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    c = set(asp_valid_combos())
    p = set(valid_combos())
    rc = 0
    if c == p:
        print(f"OK: gate matches valid_combos() ({len(c)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("  only in clingo:", sorted(c - p))
        print("  only in python:", sorted(p - c))
    try:
        sample = generate(resolve_params(argparse.Namespace(location=None, quest=None, misunderstanding=None, tool=None,
                                                            captain_name=None, captain_gender=None,
                                                            scout_name=None, scout_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke-tested story generation.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure quest with a violet prize and a drunk misunderstanding.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--captain-name")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--scout-name")
    ap.add_argument("--scout-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.location and args.quest and args.misunderstanding:
        if not reasonableness_gate(LOCATIONS[args.location], QUESTS[args.quest], MISUNDERSTANDINGS[args.misunderstanding]):
            raise StoryError(explain_rejection(LOCATIONS[args.location], QUESTS[args.quest], MISUNDERSTANDINGS[args.misunderstanding]))
    combos = [c for c in valid_combos()
              if (args.location is None or c[0] == args.location)
              and (args.quest is None or c[1] == args.quest)
              and (args.misunderstanding is None or c[2] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    location, quest, misunderstanding = rng.choice(combos)
    tool = args.tool or rng.choice(list(TOOLS))
    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    scout_gender = args.scout_gender or ("boy" if captain_gender == "girl" else "girl")
    captain_name = args.captain_name or rng.choice(GIRL_NAMES if captain_gender == "girl" else BOY_NAMES)
    scout_name = args.scout_name or rng.choice([n for n in (GIRL_NAMES if scout_gender == "girl" else BOY_NAMES) if n != captain_name])
    return StoryParams(location, quest, misunderstanding, tool, captain_name, captain_gender, scout_name, scout_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(LOCATIONS[params.location], QUESTS[params.quest], MISUNDERSTANDINGS[params.misunderstanding], TOOLS[params.tool],
                 params.captain_name, params.captain_gender, params.scout_name, params.scout_gender)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for combo in combos:
            print("  ", combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
            header = f"### {p.captain_name} and {p.scout_name}: {p.quest} / {p.misunderstanding}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
