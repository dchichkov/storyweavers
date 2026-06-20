#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sopaipilla_teamwork_mystery_to_solve_foreshadowing_mystery.py
==============================================================================================

A small mystery storyworld for a kid-friendly "who took the sopaipilla?" tale.

Premise:
- A family or small group is preparing sopaipillas in a cozy kitchen/café.
- One warm sopaipilla goes missing.
- The children notice clues: a dusting of flour, a little sticky trail, a warm plate left behind.
- They work together to solve the mystery.
- A helpful reveal explains where the sopaipilla went and what the team learned.

This world uses:
- typed entities with meters and memes
- a forward-chained causal simulation
- a reasonableness gate and inline ASP twin
- story prompts, story-grounded QA, and world-knowledge QA

The prose is designed to stay concrete, child-facing, and state-driven.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
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
    mood: str
    clues: list[str] = field(default_factory=list)

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
class Suspicion:
    id: str
    clue: str
    thought: str
    weight: int
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
class Mystery:
    id: str
    missing: str
    hidden_place: str
    reveal: str
    trail: str
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
class Tool:
    id: str
    label: str
    use: str
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


def _r_unsolved(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("missing") and not world.facts.get("solved"):
        if "table" in world.entities:
            world.get("table").meters["mystery"] += 1
        for ch in world.characters():
            ch.memes["curiosity"] += 1
        if ("unsolved", world.facts["missing"]) not in world.fired:
            world.fired.add(("unsolved", world.facts["missing"]))
            out.append("__mystery__")
    return out


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


CAUSAL_RULES = [Rule("unsolved", "social", _r_unsolved)]


def reasonableness_gate(mystery: Mystery, setting: Setting) -> bool:
    return mystery.missing == "sopaipilla" and "kitchen" in setting.place.lower()


def inspect_clue(world: World, child: Entity, suspicion: Suspicion) -> None:
    child.memes["curiosity"] += suspicion.weight
    world.say(f"{child.id} noticed {suspicion.clue}. {suspicion.thought}")


def compare_notes(world: World, a: Entity, b: Entity, suspicion: Suspicion) -> None:
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    world.say(
        f"{a.id} and {b.id} compared their notes. Together they remembered "
        f"the clue about {suspicion.clue} and decided to follow it."
    )


def solve(world: World, helper1: Entity, helper2: Entity, mystery: Mystery, tool: Tool) -> None:
    helper1.memes["joy"] += 1
    helper2.memes["joy"] += 1
    world.facts["solved"] = True
    world.get("tray").meters["found"] += 1
    world.say(
        f"At last, the mystery made sense: the {mystery.missing} had gone to "
        f"{mystery.hidden_place}. {helper1.id} and {helper2.id} used {tool.label} "
        f"to get it back."
    )
    world.say(
        f"The warm {mystery.missing} came back to the table, and the little trail "
        f"of flour was no longer a puzzle."
    )


def foreshadow(world: World, setting: Setting, mystery: Mystery) -> None:
    world.say(
        f"Earlier, {setting.place} had seemed extra quiet, and a tiny bit of flour "
        f"near the chair looked like nothing important yet."
    )
    world.say(
        f"That small clue mattered later, because it pointed toward {mystery.hidden_place}."
    )


def tell(setting: Setting, mystery: Mystery, suspicion1: Suspicion, suspicion2: Suspicion,
         tool: Tool, names: tuple[str, str] = ("Mina", "Jasper")) -> World:
    world = World()
    a = world.add(Entity(id=names[0], kind="character", type="girl", role="helper"))
    b = world.add(Entity(id=names[1], kind="character", type="boy", role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type="mother", role="grownup"))
    world.add(Entity(id="table", type="thing", label="the table"))
    world.add(Entity(id="tray", type="thing", label="the tray"))
    world.facts.update(setting=setting, mystery=mystery, tool=tool, parent=parent)

    world.say(
        f"At {setting.place}, the room smelled sweet and warm, like sugar and cinnamon."
    )
    world.say(
        f"A plate should have held a fresh {mystery.missing}, but one was missing from the tray."
    )
    foreshadow(world, setting, mystery)
    world.para()
    inspect_clue(world, a, suspicion1)
    inspect_clue(world, b, suspicion2)
    compare_notes(world, a, b, suspicion1)
    if reasonableness_gate(mystery, setting):
        world.say(
            f"Their grown-up did not brush them off. Instead, she smiled and let them "
            f"keep looking, because careful teamwork could solve small mysteries."
        )
    propagate(world, narrate=False)
    world.para()
    solve(world, a, b, mystery, tool)
    world.say(
        f"In the end, the kitchen was bright again, and {a.id} and {b.id} knew that "
        f"working together could find even a lost sopaipilla."
    )
    world.facts.update(helper1=a, helper2=b, solved=True)
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "cozy", clues=["flour", "tray", "plate"]),
    "cafe": Setting("cafe", "the little café", "busy", clues=["tray", "counter", "napkin"]),
    "house": Setting("house", "the house kitchen", "quiet", clues=["flour", "chair", "door"]),
}

MYSTERIES = {
    "sopaipilla": Mystery(
        "sopaipilla", "sopaipilla", "the warm covered basket",
        "it was tucked beside the warm oven", "a tiny trail of flour",
        tags={"sopaipilla", "mystery", "food"},
    ),
}

SUSPICIONS = {
    "flour": Suspicion("flour", "a tiny trail of flour", "That looked like a clue, not a mistake.", 2, {"flour"}),
    "tray": Suspicion("tray", "the empty tray", "The missing snack might have been moved carefully.", 1, {"tray"}),
    "napkin": Suspicion("napkin", "a napkin on the floor", "That could hide a crumb trail.", 1, {"napkin"}),
}

TOOLS = {
    "notes": Tool("notes", "their notes", "compare clues", {"teamwork"}),
    "ladle": Tool("ladle", "a long ladle", "reach into a warm corner", {"kitchen"}),
}

GALLERY_NAMES = ["Mina", "Jasper", "Lila", "Pablo", "Nora", "Tomas", "Ivy", "Rosa"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    clue1: str
    clue2: str
    tool: str
    name1: str
    name2: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            if not reasonableness_gate(mystery, setting):
                continue
            for c1 in SUSPICIONS:
                for c2 in SUSPICIONS:
                    if c1 != c2:
                        combos.append((sid, mid, f"{c1}:{c2}"))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld about a missing sopaipilla.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue1", choices=SUSPICIONS)
    ap.add_argument("--clue2", choices=SUSPICIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or "sopaipilla"
    clue1 = args.clue1 or rng.choice(list(SUSPICIONS))
    clue2 = args.clue2 or rng.choice([k for k in SUSPICIONS if k != clue1])
    tool = args.tool or rng.choice(list(TOOLS))
    if args.clue1 and args.clue2 and args.clue1 == args.clue2:
        raise StoryError("Pick two different clues so the children can compare notes.")
    if not reasonableness_gate(MYSTERIES[mystery], SETTINGS[setting]):
        raise StoryError("This mystery only works in a kitchen-like place with a missing sopaipilla.")
    name1 = args.name1 or rng.choice(GALLERY_NAMES)
    name2 = args.name2 or rng.choice([n for n in GALLERY_NAMES if n != name1])
    return StoryParams(setting, mystery, clue1, clue2, tool, name1, name2)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        SUSPICIONS[params.clue1],
        SUSPICIONS[params.clue2],
        TOOLS[params.tool],
        (params.name1, params.name2),
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]
    s: Setting = f["setting"]
    return [
        f"Write a cozy mystery for a young child set in {s.place} where a {m.missing} is missing and small clues point to the answer.",
        f"Tell a teamwork story in {s.place} where two children follow clues and solve the mystery of the missing sopaipilla.",
        f"Write a foreshadowing mystery that includes a warm {m.missing}, a tiny clue, and a happy reveal.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    m: Mystery = f["mystery"]
    s: Setting = f["setting"]
    a: Entity = f["helper1"]
    b: Entity = f["helper2"]
    return [
        ("What was missing from the table?",
         f"A sopaipilla was missing from the table. That was the mystery everyone needed to solve."),
        ("What clue helped the children notice where to look?",
         f"They noticed a tiny trail of flour. That clue foreshadowed the answer by pointing toward where the snack had been taken."),
        ("How did the children solve the mystery?",
         f"They worked together, compared their notes, and used {f['tool'].label} to check the warm hiding place. Teamwork helped them bring the sopaipilla back."),
        ("How did the story end?",
         f"It ended happily with the sopaipilla back on the table and the room feeling calm again. The little clues finally made sense."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a sopaipilla?", "A sopaipilla is a warm fried bread or pastry. People often enjoy it fresh and soft."),
        QAItem("What does teamwork mean?", "Teamwork means people help each other and share the job. Together, they can solve a problem faster."),
        QAItem("What is foreshadowing in a story?", "Foreshadowing is when a story gives a small clue early on. That clue hints at what will matter later."),
        QAItem("Why do clues matter in a mystery?", "Clues matter because they help solve the puzzle. Each clue can point to the right answer."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
missing(sopaipilla).
setting_kitchen(S) :- setting(S).
clue(C) :- clue_item(C).
teamwork :- helper(A), helper(B), A != B.
solved :- missing(sopaipilla), teamwork, clue(flour).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("missing", mid))
    for cid in SUSPICIONS:
        lines.append(asp.fact("clue_item", cid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show missing/1. #show clue/1."))
    _ = asp.atoms(model, "missing")
    sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, clue1=None, clue2=None, tool=None, name1=None, name2=None), random.Random(7)))
    rc = 0
    if not sample.story or "sopaipilla" not in sample.story:
        print("MISMATCH: story generation failed smoke test.")
        rc = 1
    if rc == 0:
        print("OK: story generation smoke test passed.")
    return rc


CURATED = [
    StoryParams("kitchen", "sopaipilla", "flour", "tray", "notes", "Mina", "Jasper"),
    StoryParams("cafe", "sopaipilla", "tray", "napkin", "ladle", "Lila", "Pablo"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show setting/1. #show missing/1. #show clue_item/1."))
    return sorted(set(asp.atoms(model, "setting")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show setting/1. #show missing/1. #show clue_item/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
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
            header = f"### {p.name1} & {p.name2}: missing sopaipilla in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        if header:
            print(header)
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly mystery with teamwork and foreshadowing.",
        "Tell a story about a missing sopaipilla and two helpers who solve the puzzle together.",
        "Create a cozy mystery where a small early clue hints at the answer.",
    ]


if __name__ == "__main__":
    main()
