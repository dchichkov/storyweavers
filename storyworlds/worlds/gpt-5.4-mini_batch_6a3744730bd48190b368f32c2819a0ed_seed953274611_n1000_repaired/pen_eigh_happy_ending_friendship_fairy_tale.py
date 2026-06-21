#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pen_eigh_happy_ending_friendship_fairy_tale.py
===============================================================================

A standalone fairy-tale storyworld about two friends, a small pen, and a tiny
word that helps them mend a problem and end happily.

Premise
-------
In a little kingdom, a child finds a pen that can only finish its magic when
two friends use it together. They must write the strange little word "eigh" on
a torn ribbon to help a shy fairy open a gate and bring back the missing light.

The world is intentionally small and state-driven:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate for valid story combinations
- a Python gate with an inline ASP twin
- story-grounded QA and world-knowledge QA

The tone stays child-facing and fairy-tale-like, with a happy ending and a
friendship-centered resolution.
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    writes: bool = False
    magical: bool = False
    fragile: bool = False
    helps: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "fairy"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    mood: str
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
class Pen:
    id: str
    label: str
    phrase: str
    color: str
    shine: str
    ink_kind: str
    clue: str
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


@dataclass
class Bond:
    id: str
    label: str
    promise: str
    help_line: str
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
class Problem:
    id: str
    label: str
    lack: str
    fix: str
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
class StoryParams:
    setting: str
    pen: str
    bond: str
    problem: str
    child_a: str
    child_a_type: str
    child_b: str
    child_b_type: str
    helper: str
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
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_shared_joy(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["shared"] < THRESHOLD:
            continue
        sig = ("joy", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["joy"] += 1
        out.append("__joy__")
    return out


def _r_mended_light(world: World) -> list[str]:
    if world.facts.get("gate_open") and not world.facts.get("light_returned"):
        world.facts["light_returned"] = True
        return ["__light__"]
    return []


CAUSAL_RULES = [Rule("shared_joy", "social", _r_shared_joy), Rule("mended_light", "magic", _r_mended_light)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for pen in PENS:
            for bond in BONDS:
                for problem in PROBLEMS:
                    if setting in SETTINGS and problem == "missing_light":
                        combos.append((setting, pen, problem))
    return combos


def enough_reason_to_tell(setting: Setting, pen: Pen, problem: Problem, bond: Bond) -> bool:
    return pen.writes and problem.id == "missing_light" and "friendship" in bond.tags


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.pen and args.pen not in PENS:
        raise StoryError("Unknown pen choice.")
    if args.problem and args.problem not in PROBLEMS:
        raise StoryError("Unknown problem choice.")
    if args.bond and args.bond not in BONDS:
        raise StoryError("Unknown bond choice.")
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting choice.")

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.pen is None or c[1] == args.pen)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, pen, problem = rng.choice(sorted(combos))
    bond = args.bond or rng.choice(sorted(BONDS))
    child_a = args.child_a or rng.choice(["Ivy", "Mina", "Lena", "Nora"])
    child_b = args.child_b or rng.choice([n for n in ["Pip", "Timo", "Jun", "Elli"] if n != child_a])
    child_a_type = args.child_a_type or rng.choice(["girl", "boy"])
    child_b_type = args.child_b_type or ("boy" if child_a_type == "girl" else "girl")
    helper = args.helper or rng.choice(["the tiny fairy", "a kind mouse", "the moonbeam"])
    return StoryParams(setting=setting, pen=pen, bond=bond, problem=problem,
                       child_a=child_a, child_a_type=child_a_type,
                       child_b=child_b, child_b_type=child_b_type, helper=helper)


def tell(setting: Setting, pen: Pen, bond: Bond, problem: Problem,
         a_name: str, a_type: str, b_name: str, b_type: str, helper: str) -> World:
    world = World()
    a = world.add(Entity(id=a_name, kind="character", type=a_type, role="friend", traits=["kind"]))
    b = world.add(Entity(id=b_name, kind="character", type=b_type, role="friend", traits=["gentle"]))
    pen_e = world.add(Entity(id="pen", type="pen", label=pen.label, phrase=pen.phrase, writes=True, magical=True))
    ribbon = world.add(Entity(id="ribbon", type="thing", label="ribbon", fragile=True))
    fairy = world.add(Entity(id="helper", kind="character", type="fairy", label=helper, role="helper", helps=True))
    world.facts.update(setting=setting, pen=pen, bond=bond, problem=problem, helper=fairy)

    a.memes["hope"] += 1
    b.memes["hope"] += 1
    world.say(
        f"Once in {setting.place}, {a.id} and {b.id} were friends who loved to wander "
        f"under {setting.detail}."
    )
    world.say(
        f"They found {pen.phrase}, and {pen.label} gleamed {pen.shine}. "
        f"{pen.clue.capitalize()}, whispered the little sign beside it."
    )
    world.say(
        f'“We can help,” said {a.id}, and {b.id} nodded. They wanted to write '
        f'the tiny word “eigh” on a ribbon so the shy helper could hear it.'
    )

    world.para()
    a.memes["worry"] += 1
    b.memes["worry"] += 1
    world.say(
        f"But the ribbon had torn, and the fairy gate would not open without a neat line. "
        f"{problem.lack.capitalize()}, and the moonlit path grew quiet."
    )
    world.say(
        f'“What if we fail?” asked {b.id}. “We can try together,” said {a.id}, '
        f'and they shared the {pen.label} between them.'
    )
    a.memes["shared"] += 1
    b.memes["shared"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"{a.id} held the ribbon still while {b.id} guided the tip. The {pen.label} moved "
        f"slowly, and the word “eigh” curled across the cloth like a silver thread."
    )
    world.say(
        f"At once, {bond.promise} came true. The helper smiled, and {bond.help_line}."
    )
    world.facts["gate_open"] = True
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"The hidden gate opened with a soft glow, and the helper returned the missing light "
        f"to the lane. {a.id} and {b.id} laughed, because the whole kingdom looked warmer now."
    )
    world.say(
        f"{a.id} kept the {pen.label} safe in a satchel, and {b.id} kept the ribbon, "
        f"so they would remember how friendship had helped the day end well."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting: Setting = f["setting"]
    pen: Pen = f["pen"]
    return [
        f'Write a fairy tale for a 3-to-5-year-old set in {setting.place} that includes the words "pen" and "eigh".',
        f"Tell a happy friendship story about two children sharing a magic pen to fix a small problem.",
        f'Write a gentle fairy tale where a pen and the word "eigh" help two friends make something good happen.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = next(e for e in world.characters() if e.role == "friend")
    chars = [e for e in world.characters() if e.role == "friend"]
    if len(chars) >= 2:
        c1, c2 = chars[0], chars[1]
    else:
        c1 = c2 = a
    pen = f["pen"]
    problem = f["problem"]
    bond = f["bond"]
    return [
        QAItem(
            question="What did the friends find?",
            answer=f"They found {pen.phrase}. It looked magical, and they used it together instead of keeping it to themselves."
        ),
        QAItem(
            question="Why did they need to share the pen?",
            answer=f"They needed a neat line to solve {problem.label}. Sharing helped them hold the ribbon steady and write the word they needed."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily. The helper opened the gate, the missing light came back, and the friends stayed close."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    pen = f["pen"]
    return [
        QAItem(
            question="What is a pen?",
            answer="A pen is a writing tool used to make marks on paper or cloth. Some pens can be special and feel magical in fairy tales."
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means people care about each other, help each other, and share things fairly. Friends can make hard tasks feel easier."
        ),
        QAItem(
            question="Why did the word eigh matter?",
            answer='It mattered because it was the special word the friends needed to write. In the story, writing it helped the shy helper and opened the gate.'
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
        if e.magical:
            bits.append("magical=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "moon_garden": Setting(id="moon_garden", place="the moon garden", detail="silver rosebushes and a pearly fountain", mood="gentle"),
    "rose_lane": Setting(id="rose_lane", place="the rose lane", detail="twining roses and lantern leaves", mood="bright"),
}

PENS = {
    "silver": Pen(id="silver", label="silver pen", phrase="a silver pen", color="silver", shine="like moonlight", ink_kind="star-ink", clue="it waited for kind hands", tags={"pen"}),
    "feather": Pen(id="feather", label="feather pen", phrase="a feather pen", color="white", shine="like a swan's wing", ink_kind="rose-ink", clue="it liked patient fingers", tags={"pen"}),
}

BONDS = {
    "shared_writing": Bond(id="shared_writing", label="shared writing", promise="their friendship grew brighter", help_line="the little fairy bowed with joy", tags={"friendship"}),
    "kind_help": Bond(id="kind_help", label="kind help", promise="the friends trusted each other more", help_line="the helper lit the path with a smile", tags={"friendship"}),
}

PROBLEMS = {
    "missing_light": Problem(id="missing_light", label="the missing light", lack="the gate was dark and shy", fix="the writing would wake the gate", tags={"fairy"}),
}

CURATED = [
    StoryParams(setting="moon_garden", pen="silver", bond="shared_writing", problem="missing_light",
                child_a="Ivy", child_a_type="girl", child_b="Pip", child_b_type="boy", helper="the tiny fairy"),
    StoryParams(setting="rose_lane", pen="feather", bond="kind_help", problem="missing_light",
                child_a="Lena", child_a_type="girl", child_b="Jun", child_b_type="boy", helper="a kind mouse"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PENS:
            for pr in PROBLEMS:
                if enough_reason_to_tell(SETTINGS[s], PENS[p], PROBLEMS[pr], BONDS["shared_writing"]):
                    combos.append((s, p, pr))
    return combos


def explain_rejection(setting: Setting, pen: Pen, problem: Problem) -> str:
    return "(No story: this tiny fairy tale only tells a friendship story where a magic pen can solve the problem happily.)"


ASP_RULES = r"""
valid(S,P,Pr) :- setting(S), pen(P), problem(Pr), writes(P), missing_light(Pr), friendship_bond(shared_writing).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PENS.items():
        lines.append(asp.fact("pen", pid))
        if p.writes:
            lines.append(asp.fact("writes", pid))
    for bid, b in BONDS.items():
        lines.append(asp.fact("friendship_bond", bid))
    for prid in PROBLEMS:
        lines.append(asp.fact("problem", prid))
        lines.append(asp.fact("missing_light", prid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        py = set(valid_combos())
        cl = set(asp_valid_combos())
        if py == cl:
            print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        else:
            rc = 1
            print("MISMATCH in valid combos:")
            print(" python:", sorted(py))
            print(" clingo:", sorted(cl))
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story or "eigh" not in sample.story or "pen" not in sample.story:
            raise RuntimeError("smoke test story missing required words")
        print("OK: generate() smoke test passed.")
    except Exception:
        rc = 1
        traceback.print_exc()
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world about friendship, a pen, and a happy ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--pen", choices=PENS)
    ap.add_argument("--bond", choices=BONDS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--child-a")
    ap.add_argument("--child-a-type", choices=["girl", "boy"])
    ap.add_argument("--child-b")
    ap.add_argument("--child-b-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
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
    if args.pen and args.pen not in PENS:
        raise StoryError("Unknown pen.")
    if args.problem and args.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.pen is None or c[1] == args.pen)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, pen, problem = rng.choice(sorted(combos))
    bond = args.bond or rng.choice(sorted(BONDS))
    return StoryParams(
        setting=setting,
        pen=pen,
        bond=bond,
        problem=problem,
        child_a=args.child_a or rng.choice(["Ivy", "Mina", "Lena", "Nora"]),
        child_a_type=args.child_a_type or rng.choice(["girl", "boy"]),
        child_b=args.child_b or rng.choice(["Pip", "Jun", "Timo", "Elli"]),
        child_b_type=args.child_b_type or rng.choice(["girl", "boy"]),
        helper=args.helper or rng.choice(["the tiny fairy", "a kind mouse", "the moonbeam"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.pen not in PENS or params.bond not in BONDS or params.problem not in PROBLEMS:
        raise StoryError("Invalid params.")
    world = tell(
        SETTINGS[params.setting],
        PENS[params.pen],
        BONDS[params.bond],
        PROBLEMS[params.problem],
        params.child_a,
        params.child_a_type,
        params.child_b,
        params.child_b_type,
        params.helper,
    )
    story = world.render()
    if "pen" not in story or "eigh" not in story:
        raise StoryError("Generated story missing required words.")
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
