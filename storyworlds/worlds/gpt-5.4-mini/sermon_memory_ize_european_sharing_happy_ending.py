#!/usr/bin/env python3
"""Storyworld: a pirate-style tale about sharing, a sermon, and memory-izing.

The tiny domain is a pretend pirate game on a dockside deck. A child finds a
fancy European sea chart, a grown-up gives a short sermon about sharing, and the
children memory-ize the rule so the treasure can be enjoyed together.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)



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
    detail: str

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
class Treasure:
    id: str
    label: str
    phrase: str
    shareable: bool = True

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
class Sermon:
    id: str
    speaker: str
    text: str
    memory_line: str

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
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

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


def _r_share(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["sharing"] < THRESHOLD:
            continue
        sig = ("share", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["warmth"] += 1
        out.append("__share__")
    return out


def _r_memory(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["memoryized"] < THRESHOLD:
            continue
        sig = ("memory", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["pride"] += 1
        out.append("__memory__")
    return out


CAUSAL_RULES = [Rule("share", _r_share), Rule("memory", _r_memory)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "dock": Setting("dock", "the dock", "The masts creaked, the ropes swayed, and the deck felt like a pirate ship."),
    "pier": Setting("pier", "the pier", "The water slapped the posts, and the gulls called like lookout birds."),
}

TREASURES = {
    "cookies": Treasure("cookies", "a tin of star cookies", "the star cookies"),
    "coins": Treasure("coins", "a pouch of chocolate coins", "the chocolate coins"),
}

SERMONS = {
    "sharing": Sermon(
        "sharing",
        "the old sailor",
        """"Treasure is sweeter when it is shared," he said. "A crew that shares stays brave.""",
        "share the treasure so the whole crew can smile",
    ),
    "kindness": Sermon(
        "kindness",
        "the harbor aunt",
        """"A kind hand makes a strong crew," she said. "Remember it, and remember it well.""",
        "remember to be kind and keep one heart for the whole crew",
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Eli", "Finn"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    treasure: str
    sermon: str
    name1: str
    gender1: str
    name2: str
    gender2: str
    parent: str
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


CURATED = [
    StoryParams("dock", "cookies", "sharing", "Lily", "girl", "Tom", "boy", "mother"),
    StoryParams("pier", "coins", "kindness", "Max", "boy", "Mia", "girl", "father"),
]


KNOWLEDGE = {
    "sermon": [("What is a sermon?", "A sermon is a calm talk that teaches a lesson, often about how to live well and treat others kindly." )],
    "memory-ize": [("What does memory-ize mean?", "It means to learn something so well that you can remember it easily without reading it again." )],
    "european": [("What does European mean?", "European means it comes from Europe, which is a part of the world made of many countries." )],
    "sharing": [("Why is sharing good?", "Sharing helps everyone feel included, and it can make a game or snack feel happier." )],
    "treasure": [("What is treasure?", "Treasure is something valuable that people want to keep safe, like coins, jewels, or a special prize." )],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-style storyworld about sermon, memory-ize, and European treasure.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--sermon", choices=SERMONS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--gender2", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, t, se) for s in SETTINGS for t in TREASURES for se in SERMONS]


def explain_rejection() -> str:
    return "(No story: this tiny world only makes happy pirate tales where the crew can share the treasure.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.treasure is None or c[1] == args.treasure)
              and (args.sermon is None or c[2] == args.sermon)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, treasure, sermon = rng.choice(sorted(combos))
    gender1 = args.gender1 or rng.choice(["girl", "boy"])
    gender2 = args.gender2 or ("boy" if gender1 == "girl" else "girl")
    name1 = args.name1 or rng.choice(GIRL_NAMES if gender1 == "girl" else BOY_NAMES)
    name2 = args.name2 or rng.choice([n for n in (GIRL_NAMES if gender2 == "girl" else BOY_NAMES) if n != name1])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, treasure, sermon, name1, gender1, name2, gender2, parent)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    a = world.add(Entity(params.name1, "character", params.gender1, role="leader", traits=["bold"]))
    b = world.add(Entity(params.name2, "character", params.gender2, role="mate", traits=["careful"]))
    parent = world.add(Entity("Parent", "character", params.parent, label="the parent", role="adult"))
    treasure = world.add(Entity("treasure", "thing", TREASURES[params.treasure].label, role="treasure"))
    sermon = SERMONS[params.sermon]

    a.meters["wanting"] += 1
    b.meters["wanting"] += 1
    world.say(
        f"On {world.setting.place}, {a.id} and {b.id} turned the deck into a pirate ship. "
        f"{world.setting.detail} They found {treasure.label} in a little chest, and their eyes went wide."
    )
    world.say(
        f'"Look at that European sea chart!" {a.id} said, pointing at a fancy {params.sermon} note tucked under the lid.'
    )
    world.say(
        f"The note was a sermon from {sermon.speaker}: {sermon.text}"
    )
    world.para()
    world.say(
        f"{b.id} leaned closer and said, 'We should memory-ize it.' So {b.id} said the line again and again until it stuck in memory."
    )
    world.get(b.id).meters["memoryized"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {a.id} wanted to keep the whole prize, but {b.id} held up a hand and pointed at the sermon note."
    )
    world.say(
        f'"{sermon.memory_line}," {b.id} said. "If we share, the whole crew gets a happy ending."'
    )
    world.get(a.id).meters["sharing"] += 1
    world.get(b.id).meters["sharing"] += 1
    propagate(world, narrate=False)
    world.para()
    a.memes["greed"] += 1 if a.id else 0
    a.memes["thoughtfulness"] += 1
    world.say(
        f"{a.id} looked at the shiny treats, then at {b.id}, and at {parent.label_word}."
    )
    world.say(
        f'"All right," {a.id} said at last. "Let\'s share it like a true crew."'
    )
    treasure.meters["shared"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    parent.memes["pride"] += 1
    world.para()
    world.say(
        f"{parent.label_word.capitalize()} smiled and cut the {treasure.label} in half. {a.id} got one half and {b.id} got the other, and nobody had to beg or grab."
    )
    world.say(
        f"The little pirate crew ate together while the sea sparkled beside the pier, and the European chart stayed safe in the chest as a memory of their good turn."
    )
    world.say(
        f"That was the happiest part: the treasure was smaller in each hand, but the smile was bigger in every face."
    )
    world.facts.update(params=params, a=a, b=b, parent=parent, treasure=treasure, sermon=sermon, outcome="shared")
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a pirate-style story that includes the words "sermon", "memory-ize", and "European" and ends with sharing.',
        f"Tell a happy ending story where {p.name1} and {p.name2} find treasure, listen to a sermon, memory-ize the lesson, and share the prize.",
        f"Write a small pirate tale about a {p.parent} who teaches children to share their treasure after they hear a sermon note.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent, treasure = f["a"], f["b"], f["parent"], f["treasure"]
    sermon = f["sermon"]
    return [
        ("What did the children find?", f"They found {treasure.label} in a little chest on the pirate deck. That was the prize they had to decide how to handle."),
        ("What was the sermon about?", f"It was about sharing. The sermon said that treasure is sweeter when it is shared, and the children remembered that line."),
        ("What did memory-ize mean in the story?", f"It meant to say the lesson again and again until it stayed in memory. {b.id} did that with the sermon note so the crew would not forget."),
        (f"How did {a.id} change by the end?", f"{a.id} stopped trying to keep the whole prize and chose to share it. That made the ending calm and happy instead of selfish."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"sermon", "memory-ize", "european", "sharing", "treasure"}
    out = []
    for key in ["sermon", "memory-ize", "european", "sharing", "treasure"]:
        out.extend(KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
share_done(E) :- sharing(E), entity(E).
memory_done(E) :- memoryized(E), entity(E).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for sid in SERMONS:
        lines.append(asp.fact("sermon", sid))
    for tag in ["entity"]:
        lines.append(asp.fact(tag, "x"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show setting/1. #show treasure/1. #show sermon/1."))
    clingo = set(asp.atoms(model, "setting")) | set(asp.atoms(model, "treasure")) | set(asp.atoms(model, "sermon"))
    py = set((s,) for s in SETTINGS) | set((t,) for t in TREASURES) | set((s,) for s in SERMONS)
    if clingo == py:
        print(f"OK: ASP facts match Python registries ({len(py)} items).")
        return 0
    print("MISMATCH between ASP and Python registries.")
    return 1


def build_story(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("", "#show setting/1. #show treasure/1. #show sermon/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible stories:\n")
        for s, t, se in valid_combos():
            print(f"  {s:6} {t:8} {se}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [build_story(p) for p in CURATED]
    else:
        seen = set()
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
            sample = build_story(params)
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
            header = f"### {p.name1} & {p.name2}: {p.setting}, {p.sermon}, happy ending"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
