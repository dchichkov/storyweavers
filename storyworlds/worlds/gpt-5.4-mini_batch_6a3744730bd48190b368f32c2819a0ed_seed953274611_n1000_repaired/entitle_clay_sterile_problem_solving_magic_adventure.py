#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/entitle_clay_sterile_problem_solving_magic_adventure.py
========================================================================================

A small standalone storyworld for an adventure about a child, a magic clay kit,
and a problem that must be solved without making a mess.

Premise
-------
A child receives a little enchanted clay set, but the clay is supposed to stay
sterile for making a tiny healer statue. When the clay gets tangled with mud or
lost in a bad split, the child must solve the problem with magic, care, and a
clever helper instead of giving up.

The world is designed around:
- the seed words: "entitle", "clay", "sterile"
- features: Problem Solving, Magic
- style: Adventure

The core simulation tracks physical meters and emotional memes on typed entities.
The plot is state-driven:
1. The child opens the special clay kit and wants to make an entitled hero statue.
2. A threat or mistake risks the sterile clay.
3. The child tries a magical or practical fix.
4. The story ends with a changed object state and a visible final image.

The script supports:
- default run
- -n
- --all
- --seed
- --trace
- --qa
- --json
- --asp
- --verify
- --show-asp
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    dark: bool = False
    wet: bool = False
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
class ClayKit:
    id: str
    label: str
    phrase: str
    sterile: bool = True
    magical: bool = True
    can_sing: bool = False
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
class Problem:
    id: str
    hazard: str
    fix_kind: str
    risk: int
    title: str
    fail_title: str
    clue: str
    fix_text: str
    fail_text: str
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
class MagicTool:
    id: str
    label: str
    spell: str
    power: int
    safe: bool = True
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


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    clay = world.get("clay")
    if child.meters["mud"] >= THRESHOLD and not clay.meters["muddy"]:
        sig = ("mess",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        clay.meters["muddy"] = 1.0
        clay.meters["sterile"] = 0.0
        out.append("The clay had gone muddy.")
    return out


def _r_shimmer(world: World) -> list[str]:
    out: list[str] = []
    clay = world.get("clay")
    if clay.meters["glowing"] >= THRESHOLD and not clay.meters["warm"]:
        sig = ("shimmer",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        clay.meters["warm"] = 1.0
        out.append("The clay glimmered with a soft magic glow.")
    return out


CAUSAL_RULES = [Rule("mess", "physical", _r_mess), Rule("shimmer", "magic", _r_shimmer)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for problem in PROBLEMS:
            for tool in MAGIC_TOOLS:
                if problem.fix_kind == tool.id:
                    combos.append((place, problem.id, tool.id))
    return combos


def explain_rejection(problem: Problem, tool: MagicTool) -> str:
    return (
        f"(No story: {tool.label} does not solve the {problem.hazard} problem. "
        f"Try a matching magical fix instead.)"
    )


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    child_name: str
    child_gender: str
    guide_name: str
    guide_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld about magic clay, a sterile kit, and problem solving."
    )
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--problem", choices=list(PROBLEMS))
    ap.add_argument("--tool", choices=list(MAGIC_TOOLS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-gender", choices=["girl", "boy"])
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
    if args.problem and args.tool:
        if args.tool != PROBLEMS[args.problem].fix_kind:
            raise StoryError(explain_rejection(PROBLEMS[args.problem], MAGIC_TOOLS[args.tool]))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, problem, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    guide_gender = args.guide_gender or rng.choice(["girl", "boy"])
    child_name = args.name or (rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES))
    guide_name = args.guide or (rng.choice(GIRL_NAMES if guide_gender == "girl" else BOY_NAMES))
    return StoryParams(place=place, problem=problem, tool=tool,
                       child_name=child_name, child_gender=gender,
                       guide_name=guide_name, guide_gender=guide_gender)


def predict_problem(world: World, problem: Problem) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters[problem.hazard] += 1.0
    propagate(sim, narrate=False)
    clay = sim.get("clay")
    return {"ruined": clay.meters["sterile"] < THRESHOLD, "muddy": clay.meters["muddy"] >= THRESHOLD}


def tell(place: Place, problem: Problem, tool: MagicTool, child_name: str,
         child_gender: str, guide_name: str, guide_gender: str) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name,
                             role="seeker", traits=["curious"]))
    guide = world.add(Entity(id="guide", kind="character", type=guide_gender, label=guide_name,
                             role="guide", traits=["calm"]))
    clay = world.add(Entity(id="clay", kind="thing", type="thing", label="the clay"))
    place_ent = world.add(Entity(id="place", kind="thing", type="place", label=place.label))
    child.memes["wonder"] = 1.0
    clay.meters["sterile"] = 1.0

    world.say(
        f"{child_name} and {guide_name} set out across {place.label} with a small clay kit. "
        f"{child_name} had been told the clay had to stay sterile for a special little statue."
    )
    world.say(
        f'On the lid was an old sticker that seemed to entitle the child to one brave try, '
        f'if only the path stayed clear.'
    )

    world.para()
    if place.dark:
        world.say(
            f"But the trail under the arch was dark, and the lantern sparks danced on wet stone."
        )
    else:
        world.say(f"The path was bright, but a problem soon came anyway.")

    world.say(
        f'{child_name} wanted to solve the trouble right away. '
        f'"Maybe magic can help," {child.pronoun()} said.'
    )

    pred = predict_problem(world, problem)
    child.memes["hope"] += 1.0
    if pred["ruined"]:
        world.say(
            f"{guide_name} nodded, because the clue was clear: {problem.clue}."
        )
    else:
        world.say(
            f"{guide_name} pointed at the kit and warned that the clay must not be touched by {problem.hazard}."
        )

    world.para()
    child.meters[problem.hazard] += 1.0
    child.memes["determination"] += 1.0
    propagate(world, narrate=True)
    world.say(
        f"{child_name} opened the kit, and {problem.title.lower()}. {problem.fix_text.replace('{tool}', tool.label)}"
    )
    world.say(
        f"{guide_name} whispered the spell {tool.spell}, and the clay answered with a soft glow."
    )
    clay.meters["glowing"] += 1.0
    clay.meters["sterile"] = 1.0
    clay.meters["muddy"] = 0.0
    propagate(world, narrate=True)

    world.para()
    child.memes["joy"] += 1.0
    guide.memes["joy"] += 1.0
    world.say(
        f"In the end, {child_name} packed the clean clay back in the tin and smiled at the little shape it could become."
    )
    world.say(
        f"The adventure left the clay sterile, glowing, and ready for tomorrow's hero."
    )

    world.facts.update(
        child=child, guide=guide, clay=clay, place=place_ent, problem=problem, tool=tool,
        outcome="solved", hazard=problem.hazard
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a child that includes the words "entitle", "clay", and "sterile".',
        f"Tell a magical problem-solving story where {f['child'].label} must keep clay sterile while facing {f['problem'].hazard}.",
        f"Write a child-friendly adventure about a magical clay kit, a tricky problem, and a clever fix.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    problem = f["problem"]
    tool = f["tool"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.label} and {guide.label}, who travel together with a magic clay kit."),
        ("What was the main problem?",
         f"The trouble was {problem.hazard}. It threatened the clay and made the child need to think carefully."),
        ("How was the problem solved?",
         f"They used {tool.label} and a small spell to fix it. That kept the clay sterile and ready to use."),
        ("How did the story end?",
         f"It ended with the clay clean, glowing, and safe in its tin. The final image shows that the child solved the problem instead of losing the kit."),
    ]
    if f["clay"].meters["sterile"] >= THRESHOLD:
        qa.append((
            "Why was sterile important?",
            "Sterile meant the clay stayed clean and safe for making the special statue. "
            "If the clay got dirty, the magic craft would not have worked as well."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is clay?",
         "Clay is soft earth that can be squeezed and shaped. People use it to make pots, figures, and little art pieces."),
        ("What does sterile mean?",
         "Sterile means very clean and free from dirt or germs. It is important when something must stay safe and pure."),
        ("What is a problem-solving story?",
         "It is a story where a character faces trouble, thinks about the situation, and chooses a clever way to fix it."),
        ("What is magic in a story?",
         "Magic is something special and impossible in real life, like a spell or glowing light that helps the adventure along."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("fix_kind", pid, p.fix_kind))
    for tid, t in MAGIC_TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("power", tid, t.power))
    lines.append(asp.fact("required_word", "entitle"))
    lines.append(asp.fact("required_word", "clay"))
    lines.append(asp.fact("required_word", "sterile"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Problem, Tool) :- place(Place), problem(Problem), tool(Tool), fix_kind(Problem, Tool).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        a = set(asp_valid_combos())
        p = set(valid_combos())
        if a == p:
            print(f"OK: gate matches valid_combos() ({len(a)} combos).")
        else:
            rc = 1
            print("MISMATCH in valid combos:")
            if a - p:
                print("  only in asp:", sorted(a - p))
            if p - a:
                print("  only in python:", sorted(p - a))
        # smoke test ordinary generation
        sample = generate(resolve_params(argparse.Namespace(
            place=None, problem=None, tool=None, name=None, gender=None,
            guide=None, guide_gender=None
        ), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        _ = sample.to_json()
        print("OK: smoke test generated a story and serialized it.")
    except Exception:
        rc = 1
        traceback.print_exc()
    return rc


PLACES = {
    "cavern": Place("cavern", "the moonlit cavern", dark=True),
    "garden": Place("garden", "the old garden", wet=True),
    "tower": Place("tower", "the windy tower", dark=True),
}

PROBLEMS = {
    "mud": Problem(
        id="mud",
        hazard="mud",
        fix_kind="purify",
        risk=2,
        title="A muddy splash had jumped onto the clay",
        fail_title="The mud problem got worse",
        clue="mud had splashed the path and wanted to cling to everything",
        fix_text="The child lifted the lid and called for a purifying spell from {tool}.",
        fail_text="The child tried to wipe it with a leaf, but the mud kept spreading.",
        tags={"mud"},
    ),
    "dust": Problem(
        id="dust",
        hazard="dust",
        fix_kind="seal",
        risk=1,
        title="A puff of dust sneaked into the kit",
        fail_title="The dust drifted everywhere",
        clue="dust was floating in the air from the old path",
        fix_text="The child tapped the tin and asked {tool} to seal the air around it.",
        fail_text="The child waved at the dust, but the little cloud only grew.",
        tags={"dust"},
    ),
    "spatter": Problem(
        id="spatter",
        hazard="paint spatter",
        fix_kind="wash",
        risk=2,
        title="A paint spatter leapt toward the clay",
        fail_title="The paint spatter kept hopping",
        clue="a splash of color was flying from the broken jar",
        fix_text="The child traced a wash-light circle and told {tool} to clean the edge.",
        fail_text="The child backed away, but the paint spatter still reached the kit.",
        tags={"paint"},
    ),
}

MAGIC_TOOLS = {
    "purify": MagicTool("purify", "a purifying charm", "Luma, clean and clear!", 3, tags={"magic", "clean"}),
    "seal": MagicTool("seal", "a sealing charm", "Mira, circle and keep!", 2, tags={"magic", "seal"}),
    "wash": MagicTool("wash", "a wash-light charm", "Aqua, wash away!", 3, tags={"magic", "water"}),
}

GIRL_NAMES = ["Ada", "Mira", "Nia", "Luna", "Cleo", "Iris", "Zara", "Tess"]
BOY_NAMES = ["Arin", "Jules", "Rafi", "Nico", "Theo", "Bram", "Oren", "Milo"]


def explain_response(tool: str) -> str:
    return f"(No story: {tool} does not match the problem well enough for this adventure.)"


def valid_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.problem not in PROBLEMS or params.tool not in MAGIC_TOOLS:
        raise StoryError("Invalid params.")
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    tool = MAGIC_TOOLS[params.tool]
    world = tell(place, problem, tool, params.child_name, params.child_gender, params.guide_name, params.guide_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


CURATED = [
    StoryParams(place="cavern", problem="mud", tool="purify", child_name="Mira", child_gender="girl",
                guide_name="Arin", guide_gender="boy"),
    StoryParams(place="garden", problem="dust", tool="seal", child_name="Theo", child_gender="boy",
                guide_name="Luna", guide_gender="girl"),
    StoryParams(place="tower", problem="spatter", tool="wash", child_name="Cleo", child_gender="girl",
                guide_name="Rafi", guide_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
