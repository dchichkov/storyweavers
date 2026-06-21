#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/failure_road_problem_solving_superhero_story.py
==============================================================================

A standalone storyworld for a tiny superhero domain: a small hero meets a road
problem, suffers a failure, and solves it with planning, tools, and teamwork.

Seed words: failure, road
Style: Superhero Story
Feature: Problem Solving
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
CAUSE_MIN = 1.0


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
class Scene:
    city: str
    road_name: str
    road_kind: str
    danger: str
    problem: str
    fix_hint: str
    finish_image: str
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
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    power: int
    sense: int
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
class Problem:
    id: str
    label: str
    source: str
    severity: int
    can_fail: bool = True
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
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


def _r_bump(w: World) -> list[str]:
    out: list[str] = []
    for e in w.entities.values():
        if e.meters["stuck"] >= THRESHOLD and ("bump", e.id) not in w.fired:
            w.fired.add(("bump", e.id))
            e.meters["frustration"] += 1
            out.append("__bump__")
    return out


def _r_help(w: World) -> list[str]:
    out: list[str] = []
    hero = w.entities.get("hero")
    road = w.entities.get("road")
    if hero and road and hero.memes["plan"] >= THRESHOLD and road.meters["blocked"] >= THRESHOLD:
        sig = ("help",)
        if sig not in w.fired:
            w.fired.add(sig)
            hero.memes["focus"] += 1
            out.append("__help__")
    return out


RULES = [Rule("bump", _r_bump), Rule("help", _r_help)]


def propagate(w: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(w)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            w.say(s)
    return produced


def valid_problem(problem: Problem) -> bool:
    return problem.can_fail and problem.severity >= 1


def valid_combo(scene: Scene, problem: Problem, tool: Tool) -> bool:
    return valid_problem(problem) and tool.power >= problem.severity


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SCENES:
        for p in PROBLEMS.values():
            for t in TOOLS.values():
                if valid_combo(s, p, t):
                    combos.append((s.city, p.id, t.id))
    return combos


def reasonableness_gate(problem: Problem, tool: Tool) -> bool:
    return tool.sense >= 2 and tool.power >= problem.severity


def _plan_text(hero: Entity, sidekick: Entity, scene: Scene, problem: Problem) -> str:
    return (
        f"{hero.id} and {sidekick.id} flew over {scene.city}. "
        f"Around {scene.road_name}, the {scene.road_kind} had a {problem.label}."
    )


def predict_failure(w: World, problem_id: str) -> dict:
    sim = w.copy()
    sim.get("road").meters["blocked"] += 1
    sim.get("hero").meters["stuck"] += 1
    return {"stuck": sim.get("hero").meters["stuck"] >= THRESHOLD}


def tell(scene: Scene, problem: Problem, tool: Tool, hero_name: str, sidekick_name: str,
         hero_type: str = "boy", sidekick_type: str = "girl") -> World:
    w = World()
    hero = w.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    sidekick = w.add(Entity(id=sidekick_name, kind="character", type=sidekick_type, role="sidekick"))
    guide = w.add(Entity(id="Guide", kind="character", type="adult", label="the guide", role="guide"))
    road = w.add(Entity(id="road", kind="thing", type="road", label=scene.road_name))
    road.meters["blocked"] = 1.0
    hero.memes["bravery"] = 1.0
    sidekick.memes["hope"] = 1.0

    w.say(f"On a bright day in {scene.city}, {hero.id} wore a small cape and {sidekick.id} carried a map.")
    w.say(f"They zoomed toward {scene.road_name}, ready to help people on the {scene.road_kind}.")
    w.say(_plan_text(hero, sidekick, scene, problem))
    w.para()

    hero.meters["stuck"] += 1
    hero.memes["failure"] += 1
    w.say(f"But the plan hit a failure when {problem.source} blocked the road.")
    w.say(f"{hero.id} tried first, and it was not enough.")

    predicted = predict_failure(w, problem.id)
    w.facts["predicted_failure"] = predicted["stuck"]

    if reasonableness_gate(problem, tool):
        hero.memes["plan"] += 1
        w.say(f"{sidekick.id} pointed at {tool.phrase}. “Use {tool.label},” {sidekick.id} said.")
        w.say(f"{hero.id} nodded, changed the plan, and used the {tool.label} to {tool.use}.")
        road.meters["blocked"] = 0
        hero.meters["stuck"] = 0
        guide.memes["pride"] += 1
        propagate(w, narrate=False)
        w.para()
        w.say(f"The {scene.road_kind} opened again, and the vehicles could roll through.")
        w.say(f"At the end, {scene.finish_image}, and {hero.id} and {sidekick.id} smiled like real superheroes.")
        outcome = "fixed"
    else:
        raise StoryError("This tool is too weak for the road problem; choose a stronger fix.")

    w.facts.update(hero=hero, sidekick=sidekick, guide=guide, road=road, scene=scene, problem=problem, tool=tool, outcome=outcome)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene: Scene = f["scene"]
    problem: Problem = f["problem"]
    tool: Tool = f["tool"]
    return [
        f'Write a superhero story for a child that includes the words "failure" and "road".',
        f"Tell a problem-solving adventure where {f['hero'].id} faces a failure on {scene.road_name} and fixes the road with {tool.label}.",
        f"Write a story about a superhero team that sees a road problem, makes a better plan, and gets people moving again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    scene: Scene = f["scene"]
    problem: Problem = f["problem"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question="What problem did the superheroes find?",
            answer=f"They found a failure on {scene.road_name} because {problem.source} blocked the road. That made their first plan stop working."
        ),
        QAItem(
            question="How did they solve it?",
            answer=f"{sidekick.id} suggested {tool.label}, and {hero.id} used it to {tool.use}. That changed the road from blocked to open."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {scene.finish_image}. The heroes fixed the road and kept people moving safely."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a road?",
            answer="A road is a path for cars, bikes, and people to travel from one place to another."
        ),
        QAItem(
            question="What should a superhero do when the first plan fails?",
            answer="A superhero should stop, think, and try a better plan. Good problem solving means using the right tool or asking for help."
        ),
        QAItem(
            question="Why is it smart to clear a blocked road?",
            answer="A blocked road can stop travel and help people get stuck. Clearing it lets everyone move safely again."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
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
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


SCENES = [
    Scene(
        city="Sunbeam City",
        road_name="Harbor Road",
        road_kind="main road",
        danger="a fallen sign",
        problem="sign",
        fix_hint="lift the sign away",
        finish_image="the road shone clear under the morning sun",
    ),
    Scene(
        city="Cloud Tower",
        road_name="Maple Road",
        road_kind="busy road",
        danger="a broken box",
        problem="box",
        fix_hint="move the box aside",
        finish_image="the buses rolled past in a safe bright line",
    ),
    Scene(
        city="River Square",
        road_name="Rainbow Road",
        road_kind="curvy road",
        danger="a mud pile",
        problem="mud",
        fix_hint="sweep the mud off",
        finish_image="the road sparkled and the crowd cheered",
    ),
]

PROBLEMS = {
    "sign": Problem(id="sign", label="tangled sign", source="a heavy fallen sign", severity=2, tags={"road", "problem"}),
    "box": Problem(id="box", label="broken box", source="a broken delivery box", severity=1, tags={"road", "problem"}),
    "mud": Problem(id="mud", label="mud pile", source="a slippery mud pile", severity=1, tags={"road", "problem"}),
}

TOOLS = {
    "wrench": Tool(id="wrench", label="a bright wrench", phrase="a bright wrench", use="loosen the bent sign", power=2, sense=3, tags={"tool"}),
    "scoop": Tool(id="scoop", label="a rescue scoop", phrase="a rescue scoop", use="scoop the mud aside", power=1, sense=3, tags={"tool"}),
    "beam": Tool(id="beam", label="a strong beam", phrase="a strong beam", use="lift the box off the road", power=1, sense=2, tags={"tool"}),
}

@dataclass
class StoryParams:
    scene: str
    problem: str
    tool: str
    hero: str
    sidekick: str
    hero_type: str = "boy"
    sidekick_type: str = "girl"
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


CURATED = [
    StoryParams() if False else None
]


def resolve_scene_lookup(key: str) -> Scene:
    for s in SCENES:
        if s.road_name == key or s.city == key or s.problem == key:
            return s
    raise StoryError("Unknown scene.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scene = rng.choice(SCENES)
    problem = PROBLEMS[args.problem] if getattr(args, "problem", None) else rng.choice(list(PROBLEMS.values()))
    tool = TOOLS[args.tool] if getattr(args, "tool", None) else rng.choice(list(TOOLS.values()))
    if not valid_combo(scene, problem, tool):
        raise StoryError("That tool cannot solve this road problem.")
    hero = args.hero or rng.choice(["Nova", "Bolt", "Mira", "Flash"])
    sidekick = args.sidekick or rng.choice(["Pip", "Zee", "Sky", "Juno"])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    sidekick_type = args.sidekick_type or ("girl" if hero_type == "boy" else "boy")
    return StoryParams(scene=scene.road_name, problem=problem.id, tool=tool.id, hero=hero, sidekick=sidekick, hero_type=hero_type, sidekick_type=sidekick_type)


def tell_story(params: StoryParams) -> World:
    scene = next(s for s in SCENES if s.road_name == params.scene)
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    return tell(scene, problem, tool, params.hero, params.sidekick, params.hero_type, params.sidekick_type)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny superhero road problem-solving storyworld.")
    ap.add_argument("--scene", choices=[s.road_name for s in SCENES])
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--sidekick-type", choices=["boy", "girl"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_facts() -> str:
    import asp
    lines = []
    for s in SCENES:
        lines.append(asp.fact("scene", s.road_name))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("severity", pid, p.severity))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("power", tid, t.power))
        lines.append(asp.fact("sense", tid, t.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,T) :- scene(S), problem(P), tool(T), severity(P,V), power(T,W), W >= V.
sensible(T) :- tool(T), sense(T,S), sense_min(M), S >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(set(asp.atoms(model, "sensible")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP valid combos differ from Python.")
        rc = 1
    if {t[0] for t in asp_sensible()} != {tid for tid, t in TOOLS.items() if t.sense >= 2}:
        print("MISMATCH: ASP sensible tools differ from Python.")
        rc = 1
    try:
        sample = generate(StoryParams(scene="Harbor Road", problem="sign", tool="wrench", hero="Nova", sidekick="Pip"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return f"(No story: {tool.label} is too weak for this road problem, so the hero would not solve it.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(scene="Harbor Road", problem="sign", tool="wrench", hero="Nova", sidekick="Pip", hero_type="girl", sidekick_type="boy"),
            StoryParams(scene="Maple Road", problem="box", tool="beam", hero="Bolt", sidekick="Sky", hero_type="boy", sidekick_type="girl"),
            StoryParams(scene="Rainbow Road", problem="mud", tool="scoop", hero="Mira", sidekick="Juno", hero_type="girl", sidekick_type="girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
