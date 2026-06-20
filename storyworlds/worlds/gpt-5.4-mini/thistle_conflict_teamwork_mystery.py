#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/thistle_conflict_teamwork_mystery.py
====================================================================

A standalone storyworld for a small mystery about a missing thistle, a clash
between two children, and the teamwork that solves it.

Premise
-------
A child finds a thorny thistle, someone thinks it was taken or ruined, and the
children argue over what happened. They follow clues around a garden, discover
the truth, and work together to fix the little problem.

This world is intentionally small:
- physical meters: loss, muddle, repair, bloom, solved
- emotional memes: worry, anger, trust, relief, teamwork, curiosity

It includes a Python reasonableness gate and an inline ASP twin.
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
PAIR_THRESHOLD = 1.5
CONFIRM_THRESHOLD = 2.0


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
    found: bool = False
    carried_by: str = ""
    fixed: bool = False

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
class Garden:
    id: str
    name: str
    hiding_spots: list[str]
    clue_spots: list[str]
    thistle_spots: list[str]
    suspicious_spots: list[str]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    useful: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class SceneChoice:
    id: str
    sense: int
    clue: str
    effect: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    a = world.entities.get("child_a")
    b = world.entities.get("child_b")
    if not a or not b:
        return out
    if a.memes["anger"] < THRESHOLD or b.memes["anger"] < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["stubborn"] += 1
    b.memes["stubborn"] += 1
    out.append("__conflict__")
    return out


def _r_mystery(world: World) -> list[str]:
    out: list[str] = []
    thistle = world.entities.get("thistle")
    if not thistle or thistle.found:
        return out
    if world.entities["garden"].meters["searched"] < THRESHOLD:
        return out
    sig = ("mystery_revealed",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    thistle.found = True
    thistle.meters["found"] += 1
    out.append("__reveal__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    a = world.entities.get("child_a")
    b = world.entities.get("child_b")
    thistle = world.entities.get("thistle")
    if not a or not b or not thistle:
        return out
    if a.memes["teamwork"] < THRESHOLD or b.memes["teamwork"] < THRESHOLD:
        return out
    if not thistle.fixed:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    out.append("__teamwork__")
    return out


CAUSAL_RULES = [Rule("conflict", "social", _r_conflict), Rule("mystery", "mystery", _r_mystery), Rule("teamwork", "social", _r_teamwork)]


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


def reasonableness_ok(garden: Garden, choice: SceneChoice, item: Item) -> bool:
    return choice.sense >= 2 and item.kind in {"jar", "cloth", "box"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for g in GARDENS:
        for c in CHOICES:
            for i in ITEMS:
                if reasonableness_ok(g, CHOICES[c], ITEMS[i]):
                    combos.append((g, c, i))
    return combos


@dataclass
@dataclass
class StoryParams:
    garden: str
    clue: str
    item: str
    child_a: str
    child_a_gender: str
    child_b: str
    child_b_gender: str
    grownup: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


GARDENS = {
    "rose_path": Garden("rose_path", "the rose path", ["under the bench", "behind the watering can"], ["by the stone path", "near the gate"], ["under the bench"], ["near the gate"]),
    "glasshouse": Garden("glasshouse", "the glasshouse garden", ["behind the fern", "under the shelf"], ["near the small pond", "beside the pots"], ["behind the fern"], ["beside the pots"]),
}

ITEMS = {
    "jar": Item("jar", "glass jar", "a clear glass jar", "jar", "hold clues", False, {"glass", "clue"}),
    "cloth": Item("cloth", "soft cloth", "a soft cloth", "cloth", "cover scratches", False, {"cloth", "repair"}),
    "box": Item("box", "cardboard box", "a little cardboard box", "box", "carry finds", False, {"box", "clue"}),
}

CHOICES = {
    "search_bench": SceneChoice("search_bench", 3, "under the bench", "look closely under the bench", {"search", "bench"}),
    "follow_track": SceneChoice("follow_track", 3, "near the gate", "follow the bent stem toward the gate", {"track", "gate"}),
    "check_fern": SceneChoice("check_fern", 3, "behind the fern", "peek behind the fern and the pots", {"fern", "pots"}),
    "ask_together": SceneChoice("ask_together", 2, "beside the path", "work together and ask what really happened", {"teamwork"}),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Maya", "Sara"]
BOY_NAMES = ["Eli", "Finn", "Owen", "Theo", "Noah", "Leo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with thistle, conflict, and teamwork.")
    ap.add_argument("--garden", choices=GARDENS)
    ap.add_argument("--clue", choices=CHOICES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name-a")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--name-b")
    ap.add_argument("--gender-b", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father"])
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


def explain_rejection() -> str:
    return "(No story: this combination does not give a believable clue-and-fix mystery.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.clue not in CHOICES:
        raise StoryError("(Unknown clue choice.)")
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid story combinations available.)")
    filtered = [c for c in combos
                if (args.garden is None or c[0] == args.garden)
                and (args.clue is None or c[1] == args.clue)
                and (args.item is None or c[2] == args.item)]
    if not filtered:
        raise StoryError(explain_rejection())
    g, clue, item = rng.choice(sorted(filtered))
    ga = args.gender_a or rng.choice(["girl", "boy"])
    gb = args.gender_b or ("boy" if ga == "girl" else "girl")
    na = args.name_a or rng.choice(GIRL_NAMES if ga == "girl" else BOY_NAMES)
    nb = args.name_b or rng.choice(GIRL_NAMES if gb == "girl" else BOY_NAMES)
    grownup = args.grownup or rng.choice(["mother", "father"])
    return StoryParams(g, clue, item, na, ga, nb, gb, grownup)


def _setup(world: World, params: StoryParams) -> None:
    a = world.add(Entity("child_a", kind="character", type=params.child_a_gender, role="lead", label=params.child_a))
    b = world.add(Entity("child_b", kind="character", type=params.child_b_gender, role="friend", label=params.child_b))
    g = world.add(Entity("grownup", kind="character", type=params.grownup, role="grownup", label=params.grownup))
    garden = world.add(Entity("garden", type="place", label=GARDENS[params.garden].name))
    thistle = world.add(Entity("thistle", type="plant", label="the thistle", role="mystery"))
    clue = CHOICES[params.clue]
    item = ITEMS[params.item]
    world.facts.update(a=a, b=b, g=g, garden=garden, thistle=thistle, clue=clue, item=item, garden_cfg=GARDENS[params.garden], outcome="")
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.say(f"On a quiet morning, {a.label} and {b.label} wandered into {garden.label}.")
    world.say(f"They noticed a thistle with one bent stem, and that made the garden feel like a mystery.")
    world.para()
    a.memes["anger"] += 1
    b.memes["anger"] += 1
    world.say(f'"Someone moved it," {a.label} said. "No, someone broke it," {b.label} said.')
    world.say("Their voices got sharp, and the little mystery turned into a conflict.")


def _search(world: World, params: StoryParams) -> None:
    clue = world.facts["clue"]
    garden_cfg = world.facts["garden_cfg"]
    world.say(f"Then they stopped arguing and looked again.")
    world.say(f"They chose to {clue.effect}, because the clue seemed to point that way.")
    world.facts["garden"].meters["searched"] += 1
    if clue.effect.endswith("gate"):
        world.say(f"Near the gate, they found a trail of crumbs and a leaf caught on a nail.")
    elif clue.effect.endswith("fern"):
        world.say(f"Behind the fern, they found a tiny basket hiding under the pots.")
    else:
        world.say(f"Under the bench, they found a muddy paw print and a snapped stem.")
    propagate(world, narrate=False)


def _reveal(world: World) -> None:
    thistle = world.facts["thistle"]
    a = world.facts["a"]
    b = world.facts["b"]
    world.say("The clues fit together.")
    world.say("The thistle had not been stolen at all; it had blown loose in the wind and rolled into a hidden spot.")
    thistle.found = True
    thistle.meters["found"] += 1
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    world.say(f"{a.label} and {b.label} looked at each other and began to work together instead of blame each other.")


def _repair(world: World) -> None:
    thistle = world.facts["thistle"]
    item = world.facts["item"]
    a = world.facts["a"]
    b = world.facts["b"]
    thistle.fixed = True
    thistle.meters["bloom"] += 1
    item.meters["repair"] += 1
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    world.say(f"They used the {item.label} to clean the scratched pot and set the thistle upright again.")
    world.say("By working together, they made the small garden look calmer and brighter.")
    world.say(f"In the end, the thistle stood safe, and the mystery had a neat answer.")


def tell(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    world.para()
    _search(world, params)
    world.para()
    if world.facts["thistle"].found:
        _reveal(world)
    world.para()
    _repair(world)
    world.facts["outcome"] = "solved"
    return world


KNOWLEDGE = {
    "thistle": [("What is a thistle?", "A thistle is a prickly plant with sharp little spines. It can grow in gardens and by paths.")],
    "mystery": [("What is a mystery?", "A mystery is something you do not understand at first. You look for clues to find the answer.")],
    "teamwork": [("What is teamwork?", "Teamwork means people help each other and do a job together. It can make a hard task easier.")],
    "conflict": [("What is conflict?", "Conflict is when people disagree or get upset with each other. Talking calmly can help fix it.")],
    "garden": [("What is a garden?", "A garden is a place where plants grow. It can have flowers, paths, and hidden spots.")],
    "clue": [("What is a clue?", "A clue is a small piece of information that helps you solve a mystery.")],
    "repair": [("What does repair mean?", "Repair means fixing something that got damaged or broken.")],
}

KNOWLEDGE_ORDER = ["thistle", "mystery", "teamwork", "conflict", "garden", "clue", "repair"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child that includes the word "thistle" and ends with teamwork.',
        f"Tell a gentle mystery where {f['a'].label} and {f['b'].label} have a conflict about a thistle, follow a clue, and solve the puzzle together.",
        f'Write a story with a garden mystery, a small argument, and a calm team fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["a"]
    b = f["b"]
    garden_cfg = f["garden_cfg"]
    item = f["item"]
    qa = [
        QAItem(question="Who is the story about?", answer=f"It is about {a.label} and {b.label}, two children exploring {garden_cfg.name}. They run into a thistle mystery and solve it together."),
        QAItem(question="Why did the children argue?", answer="They thought something bad had happened to the thistle, so they started blaming each other. Their worry turned into a sharp little conflict."),
        QAItem(question="How did they solve the mystery?", answer=f"They followed a clue, looked closely, and found that the thistle had simply blown into a hidden spot. Then they used the {item.label} and worked together to make the garden neat again."),
    ]
    if world.facts["thistle"].found:
        qa.append(QAItem(question="What proved the thistle was not stolen?", answer="The clues in the garden fit together, and they found the missing plant where the wind had carried it. That showed nobody had taken it on purpose."))
    qa.append(QAItem(question="How did the story end?", answer="It ended with the thistle standing safely again and the children feeling proud. The conflict turned into teamwork, and the mystery was solved."))

    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"thistle", "mystery", "teamwork", "conflict", "garden", "clue", "repair"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            for q, a in KNOWLEDGE[tag]:
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.fixed:
            bits.append("fixed=True")
        if e.found:
            bits.append("found=True")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams("rose_path", "search_bench", "jar", "Mina", "girl", "Eli", "boy", "mother"),
        StoryParams("glasshouse", "check_fern", "cloth", "Noah", "boy", "Lila", "girl", "father"),
        StoryParams("rose_path", "follow_track", "box", "Ivy", "girl", "Theo", "boy", "mother"),
    ]


ASP_RULES = r"""
valid(G,C,I) :- garden(G), clue(C), item(I), sense(C,S), S >= 2, useful_ok(I).
useful_ok(jar).
useful_ok(cloth).
useful_ok(box).
outcome(solved) :- valid(_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for gid in GARDENS:
        lines.append(asp.fact("garden", gid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("sense", cid, c.sense))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(_: StoryParams) -> str:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))
        rc = 1
    try:
        sample = generate(valid_story_params()[0])
        print("OK: generate smoke test succeeded.")
        if not sample.story:
            rc = 1
            print("MISMATCH: empty story.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: generate crashed: {exc}")
    return rc


def build_story(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = valid_story_params()


def resolve_story(params: StoryParams) -> StoryParams:
    return params


def resolve_choice(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.garden is None or c[0] == args.garden)
              and (args.clue is None or c[1] == args.clue)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError(explain_rejection())
    g, clue, item = rng.choice(sorted(combos))
    ga = args.gender_a or rng.choice(["girl", "boy"])
    gb = args.gender_b or ("boy" if ga == "girl" else "girl")
    na = args.name_a or rng.choice(GIRL_NAMES if ga == "girl" else BOY_NAMES)
    nb = args.name_b or rng.choice(GIRL_NAMES if gb == "girl" else BOY_NAMES)
    grownup = args.grownup or rng.choice(["mother", "father"])
    return StoryParams(g, clue, item, na, ga, nb, gb, grownup)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (garden, clue, item) combos:")
        for t in asp_valid_combos():
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_choice(args, random.Random(base_seed + i))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
