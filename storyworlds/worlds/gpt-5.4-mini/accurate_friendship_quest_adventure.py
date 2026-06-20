#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/accurate_friendship_quest_adventure.py
======================================================================

A standalone story world for a small adventure about friendship, a quest, and
being accurate.

Seed premise
------------
Two friends set out on a quest with a hand-drawn map. One friend keeps making
wild guesses, but the other notices the clues carefully. Their accurate thinking
helps them solve the quest, avoid a wrong turn, and finish with a new promise to
work together.

This world keeps the classical tiny-story shape:
- clear setup
- a tension beat caused by inaccuracy
- a turn where accurate observation matters
- a resolved ending that changes the world state

It also includes:
- typed entities with physical meters and emotional memes
- a Python reasonableness gate
- an inline ASP twin
- three separate QA sets grounded in world state
- standard CLI flags for generation, JSON, trace, QA, ASP, and verify
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
ACCURACY_MIN = 3
TRUST_HIGH = 6


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



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
    clue: str
    place: str
    risky_turn: str
    reward: str
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
    phrase: str
    use: str
    helps: str
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
        return clone

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
class Rule:
    name: str
    tag: str
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


def _r_confuse(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["confusion"] < THRESHOLD:
            continue
        sig = ("confuse", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        out.append("__confuse__")
    return out


def _r_accuracy(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["accuracy"] < THRESHOLD:
            continue
        sig = ("accuracy", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["trust"] += 1
        out.append("__accuracy__")
    return out


CAUSAL_RULES = [Rule("confuse", "social", _r_confuse), Rule("accuracy", "social", _r_accuracy)]


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


@dataclass
@dataclass
class StoryParams:
    hero: str
    friend: str
    hero_gender: str
    friend_gender: str
    parent: str
    quest: str
    tool: str
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


@dataclass
class Setting:
    name: str
    place: str
    mood: str

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


QUESTS = {
    "treasure": Quest("treasure", "find the hidden treasure", "a pine tree with three rings",
                      "the old map trail", "a dark shortcut", "a bright coin box",
                      tags={"quest", "treasure", "map"}),
    "bridge": Quest("bridge", "reach the stone bridge", "a red scarf on a fence",
                    "the river path", "a muddy wrong turn", "a safe crossing",
                    tags={"quest", "bridge", "river"}),
    "signal": Quest("signal", "deliver the signal horn", "a bell by the gate",
                    "the hill path", "the steep wrong path", "a brave shout",
                    tags={"quest", "signal", "hill"}),
}

TOOLS = {
    "map": Tool("map", "map", "a hand-drawn map", "follow the clues", "keeps the path clear",
                tags={"map", "quest"}),
    "compass": Tool("compass", "compass", "a little compass", "check direction", "shows north",
                    tags={"compass", "quest"}),
    "notebook": Tool("notebook", "notebook", "a small notebook", "write the clues", "keeps notes accurate",
                     tags={"notes", "accurate"}),
}

SETTINGS = {
    "forest": Setting("forest", "the forest trail", "quiet and green"),
    "shore": Setting("shore", "the windy shore path", "bright and breezy"),
    "hill": Setting("hill", "the hill road", "open and sunny"),
}

NAMES = ["Mia", "Nora", "Lina", "Ava", "Eli", "Noah", "Theo", "Ben", "Zoe", "Maya"]
QUEST_PROMPTS = ["quest", "friendship", "accurate"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for qid, quest in QUESTS.items():
            for tid in TOOLS:
                if qid == "treasure" and tid == "map":
                    combos.append((sid, qid, tid))
                elif qid == "bridge" and tid in {"map", "compass"}:
                    combos.append((sid, qid, tid))
                elif qid == "signal" and tid in {"compass", "notebook"}:
                    combos.append((sid, qid, tid))
    return combos


def reason_ok(quest: Quest, tool: Tool) -> bool:
    if quest.id == "treasure":
        return tool.id == "map"
    if quest.id == "bridge":
        return tool.id in {"map", "compass"}
    if quest.id == "signal":
        return tool.id in {"compass", "notebook"}
    return False


ASP_RULES = r"""
compatible(S,Q,T) :- setting(S), quest(Q), tool(T), qtool(Q,T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for qid, q in QUESTS.items():
        for tid in TOOLS:
            if reason_ok(q, TOOLS[tid]):
                lines.append(asp.fact("qtool", qid, tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    print("OK: ASP matches Python." if ok else "MISMATCH: ASP and Python differ.")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small friendship quest adventure world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, tool = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    hero_gender = "girl" if hero in {"Mia", "Nora", "Lina", "Ava", "Zoe", "Maya"} else "boy"
    friend_gender = "girl" if friend in {"Mia", "Nora", "Lina", "Ava", "Zoe", "Maya"} else "boy"
    return StoryParams(hero, friend, hero_gender, friend_gender, parent, quest, tool)


def _tell(setting: Setting, quest: Quest, tool: Tool, hero: Entity, friend: Entity, parent: Entity) -> World:
    w = World()
    w.add(hero); w.add(friend); w.add(parent)
    hero.memes["curiosity"] += 1
    friend.memes["accuracy"] += 2
    world_desc = f"On a {setting.mood} day, {hero.id} and {friend.id} turned {setting.place} into an adventure."
    w.say(world_desc)
    w.say(f'Together they wanted to {quest.goal}, because their quest felt big and exciting.')
    w.para()
    w.say(f'They carried {tool.phrase}, and {friend.id} kept checking it {tool.use}.')
    hero.meters["confusion"] += 1
    propagate(w)
    if quest.id == "treasure":
        w.say(f'"{friend.id}, that mark is accurate," {friend.id} said, pointing at the clue.')
    else:
        w.say(f'But {hero.id} guessed wrong and almost took the {quest.risky_turn}.')
    w.para()
    w.say(f"{parent.label_word.capitalize()} smiled and listened when {friend.id} explained the clue again.")
    hero.memes["accuracy"] += 1
    friend.memes["trust"] += 1
    w.say(f"At last, they chose the right path together and found {quest.reward}.")
    w.say(f"Their friendship grew stronger, and the quest ended with cheers instead of doubt.")
    w.facts.update(hero=hero, friend=friend, parent=parent, quest=quest, tool=tool, setting=setting)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that uses the word "accurate" and shows friendship on a quest.',
        f"Tell a story where {f['hero'].id} and {f['friend'].id} go on a quest, make a mistake, and then use accurate clues to solve it.",
        f"Write a short friendship adventure with a map, a wrong turn, and a happy ending that proves careful observation matters.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, quest = f["hero"], f["friend"], f["quest"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, two friends who went on a quest together."),
        ("What did the friends want to do?",
         f"They wanted to {quest.goal}. That made the day feel like a real adventure."),
        ("Why did the friend help?",
         f"{friend.id} kept the clues accurate and noticed the right path. That helped the pair avoid the wrong turn and finish the quest safely."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does accurate mean?",
         "Accurate means correct and true to the facts. An accurate clue points to the right answer."),
        ("What is a quest?",
         "A quest is a journey to find something or complete a special goal. It often feels exciting and adventurous."),
        ("What is friendship?",
         "Friendship is when people care about each other and help one another. Friends can be brave together."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Mia", "Noah", "girl", "boy", "mother", "treasure", "map"),
    StoryParams("Eli", "Lina", "boy", "girl", "father", "bridge", "compass"),
    StoryParams("Ava", "Ben", "girl", "boy", "mother", "signal", "notebook"),
]


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    tool = TOOLS[params.tool]
    world = World()
    hero = world.add(Entity(params.hero, kind="character", type=params.hero_gender, role="hero"))
    friend = world.add(Entity(params.friend, kind="character", type=params.friend_gender, role="friend"))
    parent = world.add(Entity("Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    hero.memes["hope"] += 1
    friend.memes["accuracy"] += 2
    world.say(f"On a {setting.mood} day, {hero.id} and {friend.id} set out on a quest.")
    world.say(f"They wanted to {quest.goal}, and they carried {tool.phrase} for the journey.")
    world.para()
    world.say(f"{friend.id} studied the clue carefully, while {hero.id} wanted to hurry ahead.")
    hero.meters["confusion"] += 1
    hero.memes["impatience"] += 1
    world.say(f"The path seemed sure at first, but the shortcut looked tempting and wrong.")
    world.para()
    world.say(f'"That is not accurate," {friend.id} said softly. "{tool.helps.capitalize()}."')
    hero.memes["trust"] += 1
    world.say(f"{hero.id} listened, and {parent.label_word.capitalize()} nodded when the clue matched the tree.")
    world.say(f"Together they found {quest.reward}, and their friendship felt even stronger at the end.")
    world.facts.update(hero=hero, friend=friend, parent=parent, quest=quest, tool=tool, setting=setting)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, quest, tool) combos:\n")
        for s, q, t in combos:
            print(f"  {s:8} {q:8} {t}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.hero} & {p.friend}: {p.quest} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
