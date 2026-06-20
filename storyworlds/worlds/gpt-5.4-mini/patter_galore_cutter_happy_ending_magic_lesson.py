#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/patter_galore_cutter_happy_ending_magic_lesson.py
=================================================================================

A standalone storyworld for a tiny rhyming tale: a child hears water patter
galore, wants to use a cutter for a "magic" craft, gets warned, makes a safer
choice, and ends with a happy, lesson-learned finish.

Domain idea
-----------
The child is indoors on a rainy day. The rain makes a cheerful patter on the
window. The child wants to use a sharp cutter to trim paper for a "magic" show,
but the cutter is not for little hands. A careful parent predicts the cut risk,
stops the unsafe choice, and offers a safe substitute: a blunt paper rounder and
stickers galore. The child learns the lesson, the craft becomes magical without
injury, and the ending image proves the change.

This script is self-contained, stdlib-only, and follows the Storyweavers world
contract. It includes:
- typed entities with meters and memes
- a Python reasonableness gate
- an inline ASP twin
- story-grounded QA and world-knowledge QA
- CLI support for --all, -n, --seed, --trace, --qa, --json, --asp, --verify,
  and --show-asp
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CUTTER_MIN_SAFETY = 2
MAGIC_MIN_WONDER = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    sharp: bool = False
    safe: bool = False
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
class Setting:
    id: str
    place: str
    weather: str
    rhyme_image: str
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
    noun: str
    action: str
    safety: int
    sharp: bool = False
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
class SafeAlternative:
    id: str
    label: str
    noun: str
    action: str
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
class Lesson:
    id: str
    line: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_gender: str
    parent_gender: str
    tool: str
    alt: str
    lesson: str
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


SETTINGS = {
    "rainy_window": Setting("rainy_window", "the cozy front room", "rainy",
                            "the window made a patter song", {"rain", "patter"}),
    "craft_table": Setting("craft_table", "the sunny craft table", "quiet",
                           "the table waited for glitter and glue", {"craft"}),
}

TOOLS = {
    "cutter": Tool("cutter", "cutter", "a tiny cutter", "trim", 1, sharp=True,
                   tags={"cutter", "sharp"}),
    "scissors": Tool("scissors", "scissors", "child scissors", "snip", 2,
                     sharp=False, tags={"cutter", "craft"}),
}

ALTS = {
    "paper_rounder": SafeAlternative("paper_rounder", "paper rounder", "a paper rounder",
                                     "round", {"safe", "craft"}),
    "sticker_box": SafeAlternative("sticker_box", "stickers galore", "a box of stickers",
                                   "sparkle", {"safe", "magic"}),
}

LESSONS = {
    "magic": Lesson("magic", "Magic is nicest when it is safe and kind.", {"magic"}),
    "lesson": Lesson("lesson", "A sharp thing belongs with a grown-up hand.", {"lesson"}),
    "happy": Lesson("happy", "A happy ending can shine when we choose wisely.", {"happy"}),
}

NAMES = {
    "girl": ["Mia", "Lily", "Zoe", "Ava", "Nora"],
    "boy": ["Leo", "Finn", "Max", "Theo", "Ben"],
}


def reasonableness(tool: Tool, alt: SafeAlternative) -> bool:
    return tool.safety < CUTTER_MIN_SAFETY and "safe" in alt.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, t in TOOLS.items():
            for aid in ALTS:
                if reasonableness(t, ALTS[aid]):
                    combos.append((sid, tid, aid))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("safety", tid, t.safety))
        if t.sharp:
            lines.append(asp.fact("sharp", tid))
    for aid, a in ALTS.items():
        lines.append(asp.fact("alt", aid))
        if "safe" in a.tags:
            lines.append(asp.fact("safe_alt", aid))
    lines.append(asp.fact("cutter_min_safety", CUTTER_MIN_SAFETY))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(S, T, A) :- tool(T), alt(A), safety(T, V), cutter_min_safety(M), V < M, safe_alt(A), setting(S).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming storyworld with patter, galore, and a cutter.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--alt", choices=ALTS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
              and (args.tool is None or c[1] == args.tool)
              and (args.alt is None or c[2] == args.alt)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, alt = rng.choice(sorted(combos))
    lesson = args.lesson or rng.choice(sorted(LESSONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, name, gender, parent, tool, alt, lesson)


def _predict(world: World, tool: Tool) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["cut_risk"] += 1 if tool.sharp else 0
    return {"risk": child.meters["cut_risk"] >= THRESHOLD}


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    tool = TOOLS[params.tool]
    alt = ALTS[params.alt]
    lesson = LESSONS[params.lesson]

    child = world.add(Entity("child", kind="character", type=params.child_gender, label=params.child_name,
                             role="child", traits=["curious", "gentle"]))
    parent = world.add(Entity("parent", kind="character", type=params.parent_gender, label="the parent",
                              role="parent"))
    cutter = world.add(Entity("cutter", type="thing", label=tool.label, sharp=tool.sharp))
    safe = world.add(Entity("safe", type="thing", label=alt.label, safe=True))
    room = world.add(Entity("room", type="thing", label=setting.place))

    child.memes["wonder"] += 1
    child.memes["joy"] += 1
    world.say(f"On a rainy day, in {setting.place}, the wind made the window sing patter galore.")
    world.say(f"{child.id} danced in place and clapped along, for the drops had a happy tune.")
    world.say(f"Then {child.id} saw the {tool.noun} and wanted to {tool.action} paper for a magic show.")

    world.para()
    child.memes["desire"] += 1
    world.say(f'"I can make a trick!" {child.id} said. "A tiny cut, a fancy flip, a magic show to woo!"')
    if _predict(world, tool)["risk"]:
        child.memes["warning"] += 1
        world.say(f"{parent.label_word.capitalize()} frowned with care and gave a gentle, steady clue.")
        world.say(f'"Not that way, my dear one. A sharp tool can hurt you through and through."')
    child.memes["defiance"] += 0 if tool.safety >= CUTTER_MIN_SAFETY else 1

    world.para()
    if tool.safety < CUTTER_MIN_SAFETY:
        world.say(f"{child.id} paused, then nodded slow, and set the cutter out of sight.")
        world.say(f"Together they chose {alt.noun} instead, and stickers galore began to gleam.")
        world.say(f"They rounded paper edges, then added stars and moons until the page looked like a dream.")
        world.say(f"{lesson.line}")
        child.memes["lesson"] += 1
        child.memes["love"] += 1
        child.memes["safety"] += 1
        world.say(f"At last the magic show was ready, bright and kind, with glittering, cheerful shine.")
        world.say(f"{child.id} bowed to {parent.label_word} and smiled, " 
                  f'"A safe idea can still be fine!"')
    else:
        world.say(f"{child.id} used the tool with help and made a careful, neat design.")
        world.say(f"The show stayed gentle, and the lesson was that grown-up help is fine.")

    world.facts.update(setting=setting, child=child, parent=parent, tool=tool, alt=alt, lesson=lesson,
                       happy=True, learned=child.memes["lesson"] >= THRESHOLD)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a rhyming story for a young child that includes "patter" and ends happy.',
        f'Create a gentle magic story where {f["child"].id} wants to use a cutter, but the grown-up teaches a safer choice.',
        f'Write a lesson-learned story with a rainy patter, a magic craft, and stickers galore.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    tool = f["tool"]
    alt = f["alt"]
    qa = [
        QAItem(question="What sound did the rain make?",
               answer="The rain made a cheerful patter on the window, like a tiny drum song."),
        QAItem(question=f"What did {child.id} want to use?",
               answer=f"{child.id} wanted to use the {tool.label} for a magic craft. The grown-up knew that sharp tool could hurt little hands."),
        QAItem(question="What did they choose instead?",
               answer=f"They chose {alt.label} instead, along with stickers galore. That made the craft feel magical without the risk."),
        QAItem(question="How did the story end?",
               answer=f"It ended happily, with {child.id} smiling and using a safer idea. The lesson was learned, and the magic stayed kind."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem("What does a cutter do?",
               "A cutter is a sharp tool used to cut things like paper. Children should only use one with grown-up help."),
        QAItem("Why can sharp tools be dangerous?",
               "Sharp tools can make cuts very quickly. That is why they are handled carefully and kept away from little hands."),
        QAItem("What does it mean when something is galore?",
               "When something is galore, there is lots and lots of it. In a story, stickers galore means plenty of stickers."),
    ]
    if f["lesson"].id == "magic":
        out.append(QAItem("Can magic be part of a safe craft?",
                                  "Yes. A pretend magic craft can be safe when children use gentle tools and a grown-up guides the plan."))
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge Q&A ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        if e.sharp:
            bits.append("sharp")
        if e.safe:
            bits.append("safe")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("rainy_window", "Mia", "girl", "mother", "cutter", "sticker_box", "magic"),
    StoryParams("rainy_window", "Leo", "boy", "father", "cutter", "paper_rounder", "lesson"),
    StoryParams("craft_table", "Nora", "girl", "mother", "cutter", "sticker_box", "happy"),
]


def explain_rejection(tool: Tool) -> str:
    return f"(No story: {tool.label} is not a reasonable toy choice for this tiny craft tale.)"


def asp_verify() -> int:
    import asp
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    rc = 0
    if cset == pset:
        print(f"OK: ASP matches Python valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in combo gate:")
        if cset - pset:
            print("  only in ASP:", sorted(cset - pset))
        if pset - cset:
            print("  only in Python:", sorted(pset - cset))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(s, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
