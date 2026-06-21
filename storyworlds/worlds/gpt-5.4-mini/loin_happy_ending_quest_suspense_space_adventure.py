#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/loin_happy_ending_quest_suspense_space_adventure.py
====================================================================================

A small standalone storyworld: a child astronaut quest with suspense, a risky
space crossing, and a happy ending. The seed word "loin" is treated as the name
of a small moon-pony mascot the crew must rescue, keeping the story child-facing
while still letting the prose use the exact seed word.

The world simulates:
- a crew with physical meters and emotional memes
- a quest to reach a faraway moon gate
- suspense from a low-fuel crossing and a closing hatch
- a rescue turn where the crew uses a safe tool
- a happy ending image that proves the change

Run it:
    python storyworlds/worlds/gpt-5.4-mini/loin_happy_ending_quest_suspense_space_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/loin_happy_ending_quest_suspense_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4-mini/loin_happy_ending_quest_suspense_space_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/loin_happy_ending_quest_suspense_space_adventure.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"fuel": 0.0, "danger": 0.0, "found": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "fear": 0.0, "joy": 0.0, "courage": 0.0}

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
class Setting:
    id: str
    label: str
    danger: str
    detail: str
    sparkly: str

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
class QuestItem:
    id: str
    label: str
    phrase: str
    risk: str
    where: str
    clue: str
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
    power: int
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "orbit": Setting("orbit", "a bright orbit station", "low fuel", "The station windows glowed like little stars.", "space"),
    "moon": Setting("moon", "a moon base", "a closing hatch", "The moon dust was pale and soft under the boots.", "moon"),
    "comet": Setting("comet", "a comet outpost", "a drifting cable", "The outpost shook when the comet tail hummed past.", "comet"),
}

QUEST_ITEMS = {
    "loin": QuestItem("loin", "Loin", "the little moon pony Loin", "lost under a hatch", "near the far storage bay", "a tiny silver mane", {"moon", "pony"}),
    "beacon": QuestItem("beacon", "beacon", "the glowing beacon", "hidden in a dark tunnel", "behind the blue door", "a blinking red light", {"beacon", "light"}),
    "satchel": QuestItem("satchel", "satchel", "the explorer satchel", "stuck on a hook", "by the air lock", "a strap with star buttons", {"satchel", "gear"}),
}

TOOLS = {
    "rope": Tool("rope", "grabber rope", "a long grabber rope", "pulled things close without bumping them", 2, {"rope"}),
    "lamp": Tool("lamp", "moon lamp", "a moon lamp", "lit the path with a soft glow", 2, {"lamp", "light"}),
    "panel": Tool("panel", "control panel key", "a little panel key", "opened the hatch safely", 3, {"panel"}),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Leo", "Finn", "Sam", "Max", "Theo", "Ben"]
TRAITS = ["brave", "curious", "careful", "gentle", "bold"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    item: str
    tool: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    trait: str
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


def risk_matches(setting: Setting, item: QuestItem) -> bool:
    return setting.id == "moon" and item.id == "loin" or item.id == "beacon"


def tool_works(item: QuestItem, tool: Tool, setting: Setting) -> bool:
    if item.id == "loin":
        return tool.id in {"rope", "lamp"}
    if item.id == "beacon":
        return tool.id in {"lamp", "panel"}
    return tool.id in {"rope", "panel"}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for iid, item in QUEST_ITEMS.items():
            if not risk_matches(s, item):
                continue
            for tid, tool in TOOLS.items():
                if tool_works(item, tool, s):
                    out.append((sid, iid, tid))
    return out


def setup(world: World, hero: Entity, helper: Entity, setting: Setting, item: QuestItem) -> None:
    hero.memes["hope"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"On a quiet day in {setting.label}, {hero.id} and {helper.id} began a "
        f"small space adventure. They had a quest: find {item.phrase}."
    )
    world.say(
        f"The station looked calm, but {setting.danger} could make the search tricky. "
        f"{setting.detail}"
    )


def suspense(world: World, hero: Entity, helper: Entity, setting: Setting, item: QuestItem) -> None:
    hero.memes["fear"] += 1
    helper.memes["courage"] += 1
    world.say(
        f"They followed {item.where}, listening for the tiniest sound. "
        f"Somewhere ahead, {item.risk} waited, and the hallway felt very still."
    )
    world.say(
        f"{helper.id} pointed at {item.clue} and whispered, "
        f"\"I think {item.label} is close.\""
    )


def choose_tool(world: World, helper: Entity, tool: Tool) -> None:
    helper.memes["courage"] += 1
    world.say(
        f"Then {helper.id} lifted {tool.phrase}. It could {tool.use}, which was "
        f"much safer than rushing."
    )


def find_item(world: World, hero: Entity, helper: Entity, item: QuestItem, tool: Tool) -> None:
    hero.meters["found"] += 1
    world.get(item.id).meters["found"] += 1
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    if item.id == "loin":
        world.say(
            f"Together, they used {tool.label} to reach the little hidden nook. "
            f"There was Loin at last, blinking with sleepy moon eyes."
        )
    else:
        world.say(
            f"Together, they used {tool.label} to open the way. {item.label} was "
            f"right there, safe and waiting."
        )


def ending(world: World, hero: Entity, helper: Entity, item: QuestItem, setting: Setting) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"They brought {item.label} back into the bright room, and the whole base "
        f"felt lighter. The quest was done."
    )
    world.say(
        f"At the end, {hero.id} and {helper.id} watched {setting.sparkly} shine "
        f"through the window, happy that the day had turned out just right."
    )


def tell(setting: Setting, item: QuestItem, tool: Tool, hero_name: str, hero_gender: str,
         helper_name: str, helper_gender: str, trait: str) -> World:
    world = World()
    hero = world.add(Entity(hero_name, "character", hero_gender, role="hero"))
    helper = world.add(Entity(helper_name, "character", helper_gender, role="helper"))
    qitem = world.add(Entity(item.id, "thing", "thing", label=item.label))
    world.add(Entity(tool.id, "thing", "thing", label=tool.label))
    world.facts.update(setting=setting, item=item, tool=tool, hero=hero, helper=helper)
    setup(world, hero, helper, setting, item)
    world.para()
    suspense(world, hero, helper, setting, item)
    choose_tool(world, helper, tool)
    world.para()
    find_item(world, hero, helper, item, tool)
    ending(world, hero, helper, item, setting)
    world.facts["item_found"] = qitem.meters["found"] >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a suspenseful space adventure for a child that includes the word "{f["item"].label}" and ends happily.',
        f"Tell a quest story where {f['hero'].id} and {f['helper'].id} search for {f['item'].phrase} in {f['setting'].label}.",
        f"Write a small space rescue tale with a gentle suspense moment, a careful tool, and a happy ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    item = f["item"]
    hero = f["hero"]
    helper = f["helper"]
    setting = f["setting"]
    tool = f["tool"]
    return [
        ("Who was the story about?",
         f"It was about {hero.id} and {helper.id}, who went on a quest in {setting.label}. They worked together to find {item.phrase}."),
        ("Why was the story suspenseful?",
         f"The search felt suspenseful because the base was quiet and the path was tricky. They had to be careful before opening the hidden place."),
        ("How did they solve the problem?",
         f"They used {tool.phrase} instead of rushing. That safe choice let them reach {item.label} without any trouble."),
        ("How did the story end?",
         f"It ended happily. {item.label.capitalize()} was found, brought back, and the bright room felt cheerful again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    item = f["item"].id
    tool = f["tool"].id
    q = []
    if item == "loin":
        q.append(("What is Loin in this story?",
                  "Loin is a tiny moon pony mascot. The crew searches for it like a precious friend on their quest."))
    q.append(("What does a grabber rope do?",
               "A grabber rope helps you pull something close from far away without bumping into it."))
    if tool == "lamp":
        q.append(("What is a moon lamp?",
                  "A moon lamp gives off a soft light, so you can see in the dark without a flame."))
    if tool == "panel":
        q.append(("What is a control panel key for?",
                  "A control panel key can help open a hatch or door safely."))
    return q


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
        lines.append(f"  {e.id:8} ({e.kind:8}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams("orbit", "beacon", "lamp", "Mia", "girl", "Leo", "boy", "careful"),
    StoryParams("moon", "loin", "rope", "Nora", "girl", "Sam", "boy", "brave"),
    StoryParams("comet", "satchel", "panel", "Finn", "boy", "Ava", "girl", "gentle"),
]


def explain_rejection(setting: str, item: str, tool: str) -> str:
    return f"(No story: {tool} does not fit that quest in {setting} for {item}.)"


ASP_RULES = r"""
valid(S,I,T) :- setting(S), item(I), tool(T), risk(S,I), works(I,T,S).
"""


def asp_facts() -> str:
    import asp
    out = []
    for sid in SETTINGS:
        out.append(asp.fact("setting", sid))
    for iid in QUEST_ITEMS:
        out.append(asp.fact("item", iid))
    for tid in TOOLS:
        out.append(asp.fact("tool", tid))
    for sid, s in SETTINGS.items():
        for iid, item in QUEST_ITEMS.items():
            if risk_matches(s, item):
                out.append(asp.fact("risk", sid, iid))
    for iid, item in QUEST_ITEMS.items():
        for tid, tool in TOOLS.items():
            for sid, s in SETTINGS.items():
                if tool_works(item, tool, s):
                    out.append(asp.fact("works", iid, tid, sid))
    return "\n".join(out)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, item=None, tool=None, seed=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke-test generate() succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure quest story world with suspense and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=QUEST_ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
              and (args.item is None or c[1] == args.item)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, tool = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, item, tool, hero, hero_gender, helper, helper_gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUEST_ITEMS[params.item], TOOLS[params.tool],
                 params.hero, params.hero_gender, params.helper, params.helper_gender, params.trait)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
            header = f"### {p.hero}: {p.item} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
