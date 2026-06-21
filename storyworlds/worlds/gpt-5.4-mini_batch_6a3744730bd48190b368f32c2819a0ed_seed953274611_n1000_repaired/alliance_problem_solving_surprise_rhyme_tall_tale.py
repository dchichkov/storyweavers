#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/alliance_problem_solving_surprise_rhyme_tall_tale.py
=====================================================================================

A standalone storyworld for a tall-tale-style TinyStories domain about
alliance-building, surprise helpers, problem solving, and rhyme.

Premise
-------
A little crew needs to cross a split valley to deliver a crate of moon-milk to
a far barn. A bridge goes missing, the task looks impossible, and then an
unexpected alliance of neighbors solves the problem in a playful, rhyming way.

This world is intentionally small and state-driven:
- typed entities with physical meters and emotional memes
- forward simulation that changes the world before prose is rendered
- grounded Q&A from simulated facts, not rendered text parsing
- a Python reasonableness gate and an inline ASP twin

The story style leans tall-tale: outsized imagery, lively rhythm, concrete
problem solving, and a surprise turn that feels earned by the world state.
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
SUPPORT_MIN = 2
BRAVERY_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    role: str = ""  # leader | helper | surprise | goal | obstacle
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

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
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    wide: bool = False
    high: bool = False
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
    obstacle: str
    missing: str
    need: str
    risk: str
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
class Alliance:
    id: str
    label: str
    helpers: tuple[str, str]
    method: str
    rhyme: str
    surprise: str
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


def _r_join(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["plan"] < THRESHOLD:
            continue
        sig = ("join", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["hope"] += 1
        out.append("__join__")
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    if "bridge" not in world.entities or "crate" not in world.entities:
        return out
    bridge = world.get("bridge")
    crate = world.get("crate")
    if bridge.meters["fixed"] < THRESHOLD:
        return out
    sig = ("solve", bridge.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crate.meters["delivered"] += 1
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["joy"] += 1
    out.append("__solve__")
    return out


CAUSAL_RULES = [Rule("join", "social", _r_join), Rule("solve", "physical", _r_solve)]


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


def reasonable_alliance(problem: Problem, alliance: Alliance) -> bool:
    return problem.id in PROBLEMS and alliance.id in ALLIANCES


def can_fix(problem: Problem, alliance: Alliance, helper_power: int) -> bool:
    return helper_power >= problem.risk.count("hard") + 1


def predict_fix(world: World, alliance_id: str, problem_id: str) -> dict:
    sim = world.copy()
    alliance = ALLIANCES[alliance_id]
    problem = PROBLEMS[problem_id]
    _attempt_fix(sim, sim.get("leader"), alliance, problem, narrate=False)
    return {
        "fixed": sim.get("bridge").meters["fixed"] >= THRESHOLD,
        "delivered": sim.get("crate").meters["delivered"] >= THRESHOLD,
    }


def _attempt_fix(world: World, leader: Entity, alliance: Alliance, problem: Problem, narrate: bool = True) -> None:
    bridge = world.get("bridge")
    bridge.meters["trying"] += 1
    leader.memes["plan"] += 1
    world.say(
        f"The {problem.label} was a big, stubborn thing, with {problem.obstacle} and a {problem.missing} so plain it could make a mule blink."
    )
    world.say(
        f"{leader.id} scratched {leader.pronoun('possessive')} head and called for an alliance, because a tall problem calls for a taller plan."
    )
    if narrate:
        propagate(world, narrate=True)


def rally(world: World, leader: Entity, helpers: tuple[Entity, Entity], alliance: Alliance) -> None:
    a, b = helpers
    for ent in (a, b):
        ent.memes["plan"] += 1
        ent.memes["bravery"] += 1
    world.say(
        f"Then came a surprise: {alliance.surprise}. {a.id} and {b.id} showed up together, shoulder to shoulder, grinning like rain on a tin roof."
    )
    world.say(
        f'"{alliance.rhyme}," said {a.id}. "{alliance.method}," said {b.id}.'
    )


def solve_problem(world: World, problem: Problem, alliance: Alliance) -> None:
    bridge = world.get("bridge")
    crate = world.get("crate")
    bridge.meters["fixed"] += 1
    bridge.meters["steady"] += 1
    crate.meters["loaded"] += 1
    world.say(
        f"So the whole crew worked by the lantern glow: one held the plank, one tied the rope, and one sang a rhyme that kept every hammer stroke in time."
    )
    world.say(
        f"They patched the {problem.label} right smart, until the bridge stood proud as a fence post in a thunderstorm."
    )
    world.say(
        f"At last the crate rolled over safe and sound, and the barn door swung open like it had been waiting all week for the feast."
    )


def ending(world: World, leader: Entity, helpers: tuple[Entity, Entity], alliance: Alliance) -> None:
    a, b = helpers
    leader.memes["relief"] += 1
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"By supper time, the three of them were laughing at the moon, and even the river seemed to hum the same old rhyme: {alliance.rhyme}."
    )
    world.say(
        f"That is how {leader.id} learned that an alliance can be the biggest tool in the county, especially when surprise and rhyme ride along."
    )


def tell(problem: Problem, alliance: Alliance, leader_name: str, helper1: str, helper2: str) -> World:
    world = World()
    leader = world.add(Entity(id=leader_name, kind="character", type="boy", role="leader"))
    h1 = world.add(Entity(id=helper1, kind="character", type="girl", role="helper"))
    h2 = world.add(Entity(id=helper2, kind="character", type="boy", role="helper"))
    bridge = world.add(Entity(id="bridge", kind="thing", type="thing", label="river bridge", role="obstacle"))
    crate = world.add(Entity(id="crate", kind="thing", type="thing", label="moon-milk crate", role="goal"))
    bridge.meters["broken"] += 1
    crate.meters["waiting"] += 1

    world.say(
        f"On a day so wide it seemed to have room for three sunsets, {leader.id} came to the river with a moon-milk crate and a face full of worry."
    )
    world.say(
        f"The bridge was gone in the middle, and the river below was singing louder than a row of geese at market."
    )
    world.say(
        f'{" " .join([leader.id + " knew the job had to be done, but not a single person alone could do it."])}'
    )

    world.para()
    _attempt_fix(world, leader, alliance, problem)
    rally(world, leader, (h1, h2), alliance)

    world.para()
    solve_problem(world, problem, alliance)
    ending(world, leader, (h1, h2), alliance)

    world.facts.update(
        leader=leader,
        helpers=(h1, h2),
        problem=problem,
        alliance=alliance,
        bridge=bridge,
        crate=crate,
        solved=bridge.meters["fixed"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    problem: str
    alliance: str
    leader: str
    helper1: str
    helper2: str
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


PROBLEMS = {
    "river_gap": Problem(
        id="river_gap",
        label="river gap",
        obstacle="a gap wide as a yawning barn door",
        missing="a missing middle plank",
        need="a safe crossing",
        risk="hard to cross",
        tags={"river", "bridge"},
    ),
    "wind_gate": Problem(
        id="wind_gate",
        label="wind gate",
        obstacle="wind that could knock a hat into next Tuesday",
        missing="a latch that kept popping open",
        need="a steady gate",
        risk="hard to hold",
        tags={"wind", "gate"},
    ),
    "mule_cart": Problem(
        id="mule_cart",
        label="mule cart jam",
        obstacle="a wheel stuck in a rut deep enough to hide a boot",
        missing="a lever with no pull",
        need="a wheel freed up",
        risk="hard to budge",
        tags={"cart", "wheel"},
    ),
}

ALLIANCES = {
    "neighbors": Alliance(
        id="neighbors",
        label="neighborly alliance",
        helpers=("pep", "spark"),
        method="We lift, we heft, we keep it tight; together we can do it right!",
        rhyme="Lift and heft, left and right, make the big thing work tonight!",
        surprise="out of the blue came two neighbors with a wagon, a wrench, and a grin",
        tags={"alliance", "surprise", "rhyme"},
    ),
    "cousins": Alliance(
        id="cousins",
        label="cousin alliance",
        helpers=("dot", "bo"),
        method="Tap and tap, and slap the strap; no tall job beats a cousin rap!",
        rhyme="Tap the strap and clap the pace; teamwork puts a smile on space!",
        surprise="from the orchard path bounced two cousins carrying a ladder and a pie pan",
        tags={"alliance", "surprise", "rhyme"},
    ),
    "barnhands": Alliance(
        id="barnhands",
        label="barnhand alliance",
        helpers=("nora", "jake"),
        method="Tie that twine and keep in line; a problem shrinks when hands combine!",
        rhyme="Twine and line, shine and time, every chore can learn a rhyme!",
        surprise="from behind the hay bales popped two barnhands who had been listening all along",
        tags={"alliance", "surprise", "rhyme"},
    ),
}


def valid_combos() -> list[tuple[str, str]]:
    return [(p, a) for p in PROBLEMS for a in ALLIANCES if reasonable_alliance(PROBLEMS[p], ALLIANCES[a])]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about alliance, problem solving, surprise, and rhyme.")
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--alliance", choices=ALLIANCES)
    ap.add_argument("--leader")
    ap.add_argument("--helper1")
    ap.add_argument("--helper2")
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
              if (args.problem is None or c[0] == args.problem)
              and (args.alliance is None or c[1] == args.alliance)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    if args.problem and args.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if args.alliance and args.alliance not in ALLIANCES:
        raise StoryError("Unknown alliance.")
    problem, alliance = rng.choice(sorted(combos))
    leader = args.leader or rng.choice(["Milo", "Jory", "Penny", "Nell"])
    helper1 = args.helper1 or rng.choice(["June", "Sadie", "Ada", "Beau"])
    helper2 = args.helper2 or rng.choice(["Otis", "Mabel", "Clive", "Ruby"])
    if helper2 == helper1:
        helper2 = "Wren"
    return StoryParams(problem=problem, alliance=alliance, leader=leader, helper1=helper1, helper2=helper2)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story including the word "alliance" where {f["leader"].id} faces {f["problem"].label} and finds help in a surprising way.',
        f"Tell a rhyming problem-solving story where {f['leader'].id} can't fix the {f['problem'].label} alone, so an alliance appears.",
        f'Write a child-friendly tall tale with surprise helpers, a rhyme, and a strong alliance that gets the job done.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    leader, h1, h2 = f["leader"], f["helpers"][0], f["helpers"][1]
    problem, alliance = f["problem"], f["alliance"]
    return [
        QAItem(
            question="What big problem had to be solved?",
            answer=f"The crew had to solve {problem.label}, because the way across was broken and the crate could not reach the barn until the bridge was fixed."
        ),
        QAItem(
            question="What surprising thing helped?",
            answer=f"A surprise alliance helped. {h1.id} and {h2.id} arrived together with tools and a rhyme, and that extra help turned a stuck job into a workable plan."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily with the crate delivered and everyone laughing beside the fixed bridge. The tall problem became a small one because they worked together."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an alliance?",
            answer="An alliance is when people agree to help one another and work as a team toward the same goal."
        ),
        QAItem(
            question="Why can surprise be useful in a story?",
            answer="Surprise can make the help feel exciting and bigger than expected. It can turn a hard moment into a cheerful turn when the new helpers arrive just in time."
        ),
        QAItem(
            question="Why do rhymes fit tall tales?",
            answer="Rhymes give a tall tale a marching, bouncy sound. They make the big story feel lively, memorable, and a little bit larger than life."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.tags:
            parts.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(problem="river_gap", alliance="neighbors", leader="Milo", helper1="June", helper2="Otis"),
    StoryParams(problem="wind_gate", alliance="cousins", leader="Penny", helper1="Ada", helper2="Ruby"),
    StoryParams(problem="mule_cart", alliance="barnhands", leader="Jory", helper1="Beau", helper2="Wren"),
]


def explain_rejection(problem: Problem, alliance: Alliance) -> str:
    return f"(No story: the chosen problem and alliance do not make a strong enough tall-tale fix.)"


def generate(params: StoryParams) -> StorySample:
    if params.problem not in PROBLEMS or params.alliance not in ALLIANCES:
        raise StoryError("(Invalid params.)")
    problem = PROBLEMS[params.problem]
    alliance = ALLIANCES[params.alliance]
    world = tell(problem, alliance, params.leader, params.helper1, params.helper2)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


ASP_RULES = r"""
alliance_ok(P,A) :- problem(P), alliance(A).
surprise(A) :- alliance(A).
rhyme(A) :- alliance(A).
solved(P) :- alliance_ok(P,A), can_fix(P,A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for a in ALLIANCES:
        lines.append(asp.fact("alliance", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show alliance_ok/2."))
    return sorted(set(asp.atoms(model, "alliance_ok")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combo sets differ.")
        rc = 1
    else:
        print(f"OK: ASP and Python combo sets match ({len(valid_combos())}).")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: generate() smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show alliance_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, a in combos:
            print(f"  {p:10} {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.leader}: {p.problem} via {p.alliance}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
