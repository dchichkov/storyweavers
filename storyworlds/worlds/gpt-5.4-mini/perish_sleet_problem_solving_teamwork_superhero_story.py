#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/perish_sleet_problem_solving_teamwork_superhero_story.py
========================================================================================

A standalone storyworld for a small superhero rescue tale built from the seed
words "perish" and "sleet" with the required features: problem solving and
teamwork.

The domain is a tiny city block in bad weather. A superhero team must keep a
power outage from becoming a disaster, figure out a practical fix, and work
together to protect people, a stranded delivery drone, and a slipping bridge.

This script follows the shared StorySample / QAItem / StoryError contract and
supports the standard CLI modes used by the Storyweavers repo.
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
SENSE_MIN = 2


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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Hero:
    id: str
    title: str
    power: str
    method: str
    team_role: str
    symbol: str
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
class Problem:
    id: str
    danger: str
    place: str
    risk: str
    initial: str
    worsen: str
    flourish: str
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
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("storm").meters["danger"] >= THRESHOLD and ("storm", "alarm") not in world.fired:
        world.fired.add(("storm", "alarm"))
        for hid in ("nova", "bolt"):
            world.get(hid).memes["urgency"] += 1
        out.append("__alarm__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.get("nova").memes["plan"] >= THRESHOLD and world.get("bolt").memes["helping"] >= THRESHOLD:
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("team").memes["trust"] += 1
            out.append("__teamwork__")
    return out


CAUSAL_RULES = [
    Rule("alarm", "social", _r_alarm),
    Rule("teamwork", "social", _r_teamwork),
]


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


def reasonableness_ok(problem: Problem, fix: Fix) -> bool:
    return problem.id in {"sleet_bridge"} and fix.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str]]:
    return [("sleet_bridge", fid) for fid, fx in FIXES.items() if fx.sense >= SENSE_MIN]


def issue_severity(problem: Problem, delay: int) -> int:
    return 2 + delay


def fixed_in_time(fix: Fix, problem: Problem, delay: int) -> bool:
    return fix.power >= issue_severity(problem, delay)


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("storm").meters["danger"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("storm").meters["danger"],
        "bridge_slip": sim.get("bridge").meters["slip"],
    }


def setup(world: World, hero: Hero, sidekick: Hero, problem: Problem) -> None:
    world.get("team").memes["hope"] += 1
    world.say(
        f"Over the city, {problem.initial} while {hero.id} and {sidekick.id} watched from the rooftop. "
        f"The {problem.place} was slick with {problem.danger}, and the crowd below looked worried."
    )
    world.say(
        f'"This could {problem.risk}," said {sidekick.id}. '
        f'"Not if we think," said {hero.id}, their {hero.title} voice calm and steady.'
    )


def worsen(world: World, problem: Problem, delay: int) -> None:
    world.get("storm").meters["danger"] += 1
    world.get("bridge").meters["slip"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The {problem.worsen}. A delivery drone spun low in the {problem.place}, and the bridge cables shivered."
    )


def plan(world: World, hero: Hero, sidekick: Hero, problem: Problem) -> None:
    hero_ent = world.get(hero.id)
    side_ent = world.get(sidekick.id)
    hero_ent.memes["plan"] += 1
    side_ent.memes["helping"] += 1
    pred = predict(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f"{hero.id} pointed to the soaked street and said, "
        f'"We split the job. I will shield the bridge, and {sidekick.id} can guide the drone to the plaza."'
    )
    world.say(
        f"{sidekick.id} nodded fast. " f'"I can do that. Together, we can keep nobody from coming to harm and no one will perish."'
    )


def act(world: World, hero: Hero, sidekick: Hero, problem: Problem, fix: Fix) -> None:
    if not fixed_in_time(fix, problem, int(world.facts.get("delay", 0))):
        return
    world.get("bridge").meters["slip"] = 0
    world.get("storm").meters["danger"] = 0
    world.say(
        f"{hero.id} used {fix.text}, while {sidekick.id} held the drone steady and waved cars around the slick spot."
    )
    world.say(
        f"The rain turned to sleet, then the sleet softened, and the bridge stopped shaking under the team."
    )


def rescue(world: World, hero: Hero, sidekick: Hero, problem: Problem, fix: Fix) -> None:
    world.get("team").memes["trust"] += 1
    world.get("nova").memes["relief"] += 1
    world.get("bolt").memes["relief"] += 1
    world.say(
        f"The team reached the drone just in time. {fix.qa_text}, and the little machine blinked safely as the sleet fell."
    )
    world.say(
        f"Below them, the city lights came back on, and the people on the bridge clapped for the two heroes."
    )


def ending(world: World, hero: Hero, sidekick: Hero) -> None:
    world.say(
        f"By the end, {hero.id} and {sidekick.id} stood side by side on the roof, wet capes flapping in the sleet, "
        f"smiling because their plan had worked."
    )


def tell(problem: Problem, fix: Fix, delay: int = 0, hero_name: str = "Nova", sidekick_name: str = "Bolt") -> World:
    world = World()
    hero = world.add(Entity(hero_name, kind="character", type="girl", role="leader", label="the star hero"))
    sidekick = world.add(Entity(sidekick_name, kind="character", type="boy", role="helper", label="the helper hero"))
    world.add(Entity("team", kind="team", type="team", label="the team"))
    world.add(Entity("storm", type="storm", label="the storm"))
    world.add(Entity("bridge", type="bridge", label="the bridge"))
    world.facts["delay"] = delay

    setup(world, hero, sidekick, problem)
    world.para()
    worsen(world, problem, delay)
    plan(world, hero, sidekick, problem)
    world.para()
    act(world, hero, sidekick, problem, fix)
    rescue(world, hero, sidekick, problem, fix)
    world.para()
    ending(world, hero, sidekick)

    world.facts.update(hero=hero, sidekick=sidekick, problem=problem, fix=fix, outcome="saved")
    return world


HEROES = {
    "nova": Hero("Nova", "leader", "bright focus", "plan ahead", "leader", "star"),
    "bolt": Hero("Bolt", "helper", "quick hands", "steady the line", "helper", "bolt"),
}

PROBLEMS = {
    "sleet_bridge": Problem(
        "sleet_bridge",
        "sleet",
        "the downtown bridge",
        "the bridge might buckle",
        "Dark clouds rolled in",
        "the sleet thickened and the bridge grew slick",
        "one drone lost altitude",
        tags={"sleet", "bridge", "problem_solving", "teamwork"},
    ),
}

FIXES = {
    "rope_and_barricade": Fix(
        "rope_and_barricade",
        3,
        3,
        "stringing rope barriers and guiding traffic away",
        "tried to stop the danger with no plan at all",
        "put up rope barriers and kept the road clear",
        tags={"problem_solving", "teamwork"},
    ),
    "reflectors": Fix(
        "reflectors",
        2,
        2,
        "setting bright reflectors along the bridge edge",
        "set out reflectors, but they were too late to matter",
        "set bright reflectors along the bridge edge",
        tags={"problem_solving"},
    ),
    "drone_net": Fix(
        "drone_net",
        4,
        4,
        "using a rescue net to catch the drone and guide it down",
        "reached for the drone net, but the wind was already too strong",
        "used a rescue net to guide the drone down",
        tags={"problem_solving", "teamwork"},
    ),
}


@dataclass
@dataclass
class StoryParams:
    problem: str
    fix: str
    delay: int = 0
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


KNOWLEDGE = {
    "sleet": [("What is sleet?", "Sleet is frozen rain or icy pellets that fall from the sky. It can make roads and roofs slippery.")],
    "bridge": [("Why can a bridge be dangerous when it is slippery?", "A slippery bridge is dangerous because people and vehicles can slide or lose balance.")],
    "teamwork": [("What is teamwork?", "Teamwork is when people help each other and do different jobs to reach the same goal.")],
    "problem_solving": [("What is problem solving?", "Problem solving means thinking carefully about a problem and choosing a good way to fix it.")],
    "drone": [("What is a drone?", "A drone is a small flying machine that someone controls from the ground.")],
    "perish": [("What does perish mean?", "Perish means to die or be lost forever. People should do their best to keep others safe so that nobody perishes.")],
}
KNOWLEDGE_ORDER = ["sleet", "bridge", "teamwork", "problem_solving", "drone", "perish"]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a superhero story for a young child that includes the words "sleet" and "perish".',
        'Tell a teamwork story where two heroes solve a problem in the sleet before anyone is in danger.',
        'Write a problem-solving rescue story where a hero team works together to save a bridge and a drone.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    problem: Problem = f["problem"]
    fix: Fix = f["fix"]
    return [
        ("Who is the story about?", f"It is about Nova and Bolt, two superheroes who work as a team."),
        ("What problem did they face?", f"They faced sleet on a bridge, and the bridge grew slick and dangerous."),
        ("How did they solve it?", f"They solved it by using {fix.qa_text.lower()} while working together to protect the bridge and guide the drone."),
        ("Did anyone perish?", "No. They acted quickly, so nobody perished and everyone stayed safe."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["problem"].tags) | set(world.facts["fix"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("sleet_bridge", "rope_and_barricade", 0),
    StoryParams("sleet_bridge", "drone_net", 1),
]


def explain_rejection(problem: Problem, fix: Fix) -> str:
    if not reasonableness_ok(problem, fix):
        return "(No story: this problem and fix are not a sensible superhero match.)"
    return "(No story: invalid combination.)"


def valid_story(params: StoryParams) -> bool:
    return params.problem in PROBLEMS and params.fix in FIXES and reasonableness_ok(PROBLEMS[params.problem], FIXES[params.fix])


def outcome_of(params: StoryParams) -> str:
    return "saved" if fixed_in_time(FIXES[params.fix], PROBLEMS[params.problem], params.delay) else "failed"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fx.sense))
        lines.append(asp.fact("power", fid, fx.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,F) :- problem(P), fix(F), sense(F,S), sense_min(M), S >= M.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches Python valid_combos().")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"MISMATCH: generate() smoke test failed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with sleet, teamwork, and problem solving.")
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.problem and args.fix and not valid_story(StoryParams(args.problem, args.fix, args.delay or 0)):
        raise StoryError(explain_rejection(PROBLEMS[args.problem], FIXES[args.fix]))
    combos = [c for c in valid_combos()
              if args.problem is None or c[0] == args.problem
              and (args.fix is None or c[1] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    problem, fix = rng.choice(sorted(combos))
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    return StoryParams(problem, fix, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(PROBLEMS[params.problem], FIXES[params.fix], params.delay)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible problem/fix combos:")
        for p, f in asp_valid_combos():
            print(f"  {p} {f}")
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
            header = f"### {p.problem} / {p.fix} / {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
