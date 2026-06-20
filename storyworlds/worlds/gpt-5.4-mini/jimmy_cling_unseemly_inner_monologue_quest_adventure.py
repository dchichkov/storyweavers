#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jimmy_cling_unseemly_inner_monologue_quest_adventure.py
=======================================================================================

A standalone storyworld for a tiny adventure quest with inner monologue.

Premise
-------
A child named Jimmy sets out on a small quest to find a lost map-piece hidden in
a windy garden. He keeps having to choose between a sneaky, unseemly shortcut
and the careful way. The story is driven by world state: what is locked, what
clings, what the child thinks, what gets found, and how the quest ends.

Seed words used by this world:
- jimmy
- cling
- unseemly

Features:
- Inner Monologue
- Quest
- Adventure style

The world is intentionally small and classical: a child, a helper, a place with
physical obstacles, a goal, a turn, and a resolution image proving what changed.
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
INNER_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    openable: bool = False
    locked: bool = False
    clings: bool = False
    fragile: bool = False
    clue: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Quest:
    id: str
    goal: str
    place: str
    reward: str
    clue_needed: bool = True

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
class Setting:
    id: str
    name: str
    style: str
    detail: str
    obstacle: str
    climbing: str

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
    verb: str
    risk: str
    safe: bool = True
    sense: int = 3

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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_cling(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["wind"] < THRESHOLD:
            continue
        if not ent.clings:
            continue
        sig = ("cling", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["frustration"] += 1
        out.append("__cling__")
    return out


def _r_inner_voice(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.role != "hero":
            continue
        if hero.memes["doubt"] < THRESHOLD:
            continue
        sig = ("voice", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["focus"] += 1
        out.append("__voice__")
    return out


CAUSAL_RULES = [Rule("cling", _r_cling), Rule("inner_voice", _r_inner_voice)]


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


def rude_path_is_unseemly(tool: Tool, quest: Quest, setting: Setting) -> bool:
    return (not tool.safe) or (tool.sense < 2) or ("sneak" in setting.detail.lower() and quest.clue_needed)


def can_finish(tool: Tool, quest: Quest, delay: int) -> bool:
    return tool.safe and tool.sense >= 2 and delay <= 1


def predict(world: World, tool: Tool, quest: Quest, delay: int) -> dict:
    sim = world.copy()
    _try_tool(sim, sim.get("Jimmy"), tool, quest, narrate=False)
    return {
        "found": bool(sim.get("Clue").meters["found"] >= THRESHOLD),
        "resolved": can_finish(tool, quest, delay),
    }


def _try_tool(world: World, hero: Entity, tool: Tool, quest: Quest, narrate: bool = True) -> None:
    hero.memes["doubt"] += 1
    if tool.safe:
        hero.memes["courage"] += 1
    if narrate:
        world.say(
            f"{hero.id} looked at the old gate and thought, "
            f'"Maybe I can {tool.verb} it open."'
        )


def setup(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    hero.memes["hope"] += 1
    helper.memes["steady"] += 1
    world.say(
        f"In {world.setting.name}, {hero.id} and {helper.id} began a small quest. "
        f"{world.setting.detail} The goal was {quest.goal}."
    )
    world.say(
        f"{hero.id} felt the adventure tug at {hero.pronoun('possessive')} feet, "
        f"and {helper.id} stayed close by."
    )


def obstacle(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"But the path to {quest.place} was blocked by {world.setting.obstacle}, "
        f"and the wind made everything {world.setting.climbing}."
    )
    hero.memes["doubt"] += 1
    world.say(
        f'{hero.id} thought, "If I rush, that will be unseemly."'
    )


def temptation(world: World, hero: Entity, tool: Tool) -> None:
    hero.memes["impulse"] += 1
    world.say(
        f'{hero.id} wondered, "Should I use a {tool.label}? That would be a '
        f'quick way, even if it feels a little unseemly."'
    )
    world.say("For a moment, the shortcut looked shiny and easy.")


def warn(world: World, helper: Entity, hero: Entity, tool: Tool, quest: Quest) -> None:
    pred = predict(world, tool, quest, delay=0)
    world.facts["pred"] = pred
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} said, "{hero.id}, let us do this the careful way. '
        f"A hasty trick could make the clue slip away, and this quest deserves better."
    )


def choose_carefully(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    hero.memes["doubt"] = 0.0
    hero.memes["focus"] += 1
    world.say(
        f'{hero.id} took a slow breath and nodded. "You are right," {hero.id} '
        f'said. "I want the real clue, not just the quick answer."'
    )


def choose_sneakily(world: World, hero: Entity, helper: Entity, tool: Tool) -> None:
    hero.memes["stubborn"] += 1
    world.say(
        f'"No," {hero.id} whispered, and tried to {tool.verb} the lock anyway.'
    )
    world.say(
        "The little trick did not feel brave at all. It felt wrong, the kind of "
        "wrong that makes a quest wobble."
    )


def discover_clue(world: World, quest: Quest) -> None:
    clue = world.get("Clue")
    clue.meters["found"] = 1
    clue.memes["spark"] += 1
    world.say(
        f"Under the hanging ivy, {quest.reward} was waiting on a stone ledge, "
        f"and the clue slipped free at last."
    )


def resolve(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{hero.id} and {helper.id} followed the clue to {quest.reward}. "
        f"It gleamed in the grass like treasure."
    )
    world.say(
        f"{hero.id} tucked it safely away and smiled, knowing the quest had "
        f"been won without any unseemly shortcut."
    )


def tell(setting: Setting, quest: Quest, tool: Tool,
         hero_name: str = "Jimmy", hero_type: str = "boy",
         helper_name: str = "Mara", helper_type: str = "girl") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    gate = world.add(Entity(id="Gate", label="old gate", openable=True, locked=True, clings=True))
    ivy = world.add(Entity(id="Ivy", label="ivy", clings=True))
    clue = world.add(Entity(id="Clue", label="map-piece", clue=True))
    world.facts["tool"] = tool
    world.facts["quest"] = quest
    world.facts["gate"] = gate
    world.facts["ivy"] = ivy
    world.facts["clue"] = clue

    setup(world, hero, helper, quest)
    world.para()
    obstacle(world, hero, quest)
    temptation(world, hero, tool)
    warn(world, helper, hero, tool, quest)

    if tool.safe and not rude_path_is_unseemly(tool, quest, setting):
        choose_carefully(world, hero, helper, quest)
        discover_clue(world, quest)
        world.para()
        resolve(world, hero, helper, quest)
        outcome = "resolved"
    else:
        choose_sneakily(world, hero, helper, tool)
        if tool.safe:
            discover_clue(world, quest)
            world.para()
            resolve(world, hero, helper, quest)
            outcome = "resolved"
        else:
            world.say(
                "The lock held fast, and the ivy only clung tighter in the wind."
            )
            world.say(
                "Jimmy had to stop, listen, and return to the honest path."
            )
            hero.memes["resolve"] += 1
            helper.memes["resolve"] += 1
            world.para()
            discover_clue(world, quest)
            resolve(world, hero, helper, quest)
            outcome = "rerouted"

    world.facts.update(hero=hero, helper=helper, outcome=outcome)
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        name="the lantern garden",
        style="adventure",
        detail="The path wound between little hedges, a dry fountain, and a locked gate.",
        obstacle="a tangle of thorny vines",
        climbing="too eager to cling",
    ),
    "courtyard": Setting(
        id="courtyard",
        name="the sunlit courtyard",
        style="adventure",
        detail="Old stones made a quiet maze, and a brass arch marked the center of the quest.",
        obstacle="a narrow archway",
        climbing="restless to cling",
    ),
    "harbor": Setting(
        id="harbor",
        name="the windy harbor",
        style="adventure",
        detail="Masts creaked nearby, and a tiny staircase led toward a hidden lookout.",
        obstacle="a rope fence",
        climbing="full of things that cling",
    ),
}

QUESTS = {
    "map_piece": Quest("map_piece", "the lost map-piece", "the old gate", "a silver compass", True),
    "key_bone": Quest("key_bone", "the small key-bone", "the ivy wall", "a brass token", True),
    "star_badge": Quest("star_badge", "the star badge", "the harbor stairs", "a bright ribbon", True),
}

TOOLS = {
    "jimmy": Tool("jimmy", "jimmy", "jimmy", "it looked like a sneaky shortcut", True, 1),
    "stick": Tool("stick", "stick", "push", "it might crack something", True, 3),
    "hook": Tool("hook", "hook", "lift", "it could snag badly", True, 2),
    "crowbar": Tool("crowbar", "crowbar", "force", "it was far too rough", False, 1),
}

NAMES = ["Jimmy", "Mara", "Nell", "Toby", "Ari", "Pia", "Theo", "June"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for qid in QUESTS:
            for tid, tool in TOOLS.items():
                if tool.safe and tool.sense >= 2:
                    combos.append((sid, qid, tid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    quest: str
    tool: str
    hero: str
    helper: str
    delay: int = 0
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q: Quest = f["quest"]
    t: Tool = f["tool"]
    h: Entity = f["hero"]
    helper: Entity = f["helper"]
    return [
        f'Write an adventure story for a child named {h.id} that includes the word "jimmy" and the idea of an inner monologue.',
        f"Tell a quest story where {h.id} wants to use a {t.label} to get {q.reward}, but {helper.id} helps {h.id} choose the safer path.",
        f'Write a small adventurous tale with the words "cling" and "unseemly" where a child finishes a quest by listening to a thoughtful inner voice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    quest: Quest = f["quest"]
    tool: Tool = f["tool"]
    answer1 = (
        f"The story is about {hero.id} and {helper.id}. "
        f"{hero.id} set out on a quest for {quest.goal}, and {helper.id} stayed close to help."
    )
    answer2 = (
        f"{hero.id} wanted to use a {tool.label} because it seemed like a quick way forward. "
        f"After the warning, {hero.id} listened to the careful inner thought and chose the honest path."
    )
    answer3 = (
        f"The quest ended with {quest.reward} found safely. "
        f"That changed the ending image from a blocked gate to a shining prize in the grass."
    )
    return [
        QAItem("Who goes on the quest?", answer1),
        QAItem("What does Jimmy think about the shortcut?", answer2),
        QAItem("How does the quest end?", answer3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does it mean when something clings?",
            "If something clings, it sticks close to another thing. Vines, ivy, or damp weeds can cling to walls and gates.",
        ),
        QAItem(
            "What is an inner monologue?",
            "An inner monologue is the little voice inside your mind that tells you what you are thinking. It can help you pause and choose carefully.",
        ),
        QAItem(
            "Why can an unseemly shortcut be a bad idea?",
            "An unseemly shortcut is a choice that feels sneaky or not quite right. In a quest, the better choice is usually the careful one that keeps everyone safe and honest.",
        ),
    ]


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
        if e.openable:
            bits.append("openable")
        if e.locked:
            bits.append("locked")
        if e.clings:
            bits.append("clings")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "map_piece", "jimmy", "Jimmy", "Mara", 0),
    StoryParams("courtyard", "key_bone", "stick", "Jimmy", "Nell", 0),
    StoryParams("harbor", "star_badge", "hook", "Jimmy", "Toby", 0),
]


def explain_rejection(tool: Tool) -> str:
    return f"(No story: the tool '{tool.label}' is too rough or too unseemly for this gentle quest.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: Jimmy, cling, unseemly, inner monologue, and a small quest adventure."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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
    if args.tool and not TOOLS[args.tool].safe:
        raise StoryError(explain_rejection(TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, tool = rng.choice(sorted(combos))
    hero = args.hero or "Jimmy"
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    return StoryParams(setting, quest, tool, hero, helper, args.delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], TOOLS[params.tool],
                 params.hero, "boy", params.helper, "girl")
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


ASP_RULES = r"""
valid(S, Q, T) :- setting(S), quest(Q), tool(T), safe(T), sense(T, X), X >= 2.
unseemly(T) :- tool(T), sense(T, X), X < 2.
story_ready(S, Q, T) :- valid(S, Q, T), quest(Q), setting(S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, tool.sense))
        if tool.safe:
            lines.append(asp.fact("safe", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos gate.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible stories:")
        for row in asp_valid_combos():
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
