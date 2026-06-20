#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pat_dim_towel_power_teamwork_rhyming_story.py
==============================================================================

A small standalone storyworld for a rhyming teamwork tale built from the seed
words: pat-dim, towel, power.

Premise:
- Two children are trying to help a wet little friend.
- A storm has made everything damp and dim.
- They work together with towel-power to solve the problem.

The world is intentionally tiny, classical, and state-driven:
- typed entities with physical meters and emotional memes
- forward causal rules
- a reasonableness gate
- an inline ASP twin for parity checks
- three QA sets grounded in world state

The style goal is a child-facing rhyming story with a clear beginning, a turn,
and an ending image that proves what changed.
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
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Place:
    id: str
    label: str
    dim: str
    wet: bool
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
    phrase: str
    power: int
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
class Helper:
    id: str
    label: str
    phrase: str
    skill: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_wet_spark(world: World) -> list[str]:
    out: list[str] = []
    if world.get("towel").meters["wet"] >= THRESHOLD and "pat-dim" not in world.fired:
        world.fired.add(("pat-dim",))
        world.get("room").meters["dim"] += 1
        out.append("The room grew a little dim, and the wet towel sagged with a sad little sway.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child1").memes["teamwork"] >= THRESHOLD and world.get("child2").memes["teamwork"] >= THRESHOLD:
        if ("teamwork",) not in world.fired:
            world.fired.add(("teamwork",))
            world.get("towel").meters["dry"] += 1
            world.get("towel").meters["wet"] = 0
            world.get("kids").memes["pride"] += 1
            out.append("__teamwork__")
    return out


CAUSAL_RULES = [
    Rule("wet_spark", "physical", _r_wet_spark),
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


def reasonableness_gate(place: Place, tool: Tool, helper: Helper) -> bool:
    return place.wet and tool.power >= 1 and helper.skill == "help-dry"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid, tool in TOOLS.items():
            for hid, helper in HELPERS.items():
                if reasonableness_gate(place, tool, helper):
                    combos.append((pid, tid, hid))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    tool: str
    helper: str
    child1: str
    child2: str
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


def tell(place: Place, tool: Tool, helper: Helper, child1: str, child2: str) -> World:
    world = World()
    c1 = world.add(Entity(id=child1, kind="character", type="girl" if child1 in GIRL_NAMES else "boy", role="helper"))
    c2 = world.add(Entity(id=child2, kind="character", type="girl" if child2 in GIRL_NAMES else "boy", role="helper"))
    t = world.add(Entity(id="towel", type="thing", label="towel"))
    r = world.add(Entity(id="room", type="room", label=place.label))
    team = world.add(Entity(id="kids", kind="character", type="group", label="the two kids"))
    c1.memes["teamwork"] = 1
    c2.memes["teamwork"] = 1
    t.meters["wet"] = 1
    world.say(
        f"On a pat-dim morning, {child1} and {child2} came to the {place.label}, "
        f"where a towel lay heavy and damp. \"Let's make towel power,\" they chirped, "
        f"and their voices rhymed in a happy ramp."
    )
    world.say(
        f"{helper.phrase.capitalize()} showed them how to work as a team: one held, one spread, "
        f"one tapped the corners clean and keen."
    )
    world.para()
    world.say(
        f"The towel went pat-dim on the line, and the kids saw it sag like a sleepy vine."
    )
    t.meters["wet"] += 1
    propagate(world, narrate=True)
    world.para()
    c1.memes["teamwork"] += 1
    c2.memes["teamwork"] += 1
    world.say(
        f"Then {child1} held the left side, {child2} held the right, and together they "
        f"fluffed the cloth in the morning light."
    )
    propagate(world, narrate=True)
    if t.meters["dry"] >= THRESHOLD:
        world.say(
            f"At last the towel felt soft and light; no more pat-dim, no more damp night. "
            f"The kids grinned wide, their hearts all bright, for teamwork gave the day its power and might."
        )
    world.facts.update(
        place=place,
        tool=tool,
        helper=helper,
        child1=c1,
        child2=c2,
        towel=t,
        room=r,
        team=team,
        outcome="dry" if t.meters["dry"] >= THRESHOLD else "wet",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short rhyming story for a child that includes the words "pat-dim", "towel", and "power".',
        f"Tell a teamwork rhyme where {f['child1'].id} and {f['child2'].id} help with a wet towel and learn that teamwork has power.",
        "Write a gentle story with a damp towel, a cheerful helper, and a bright ending image that proves the towel got dry.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c1, c2, towel = f["child1"], f["child2"], f["towel"]
    return [
        QAItem(
            question="What problem did the children have?",
            answer="They had a wet towel that felt heavy and gloomy. The towel needed help, and the children had to work together to fix it."
        ),
        QAItem(
            question="How did they solve it?",
            answer="They used teamwork and listened to the helper, so one child held the towel while the other spread it out. That made the towel dry again."
        ),
        QAItem(
            question="What changed by the end?",
            answer="The towel was no longer pat-dim or damp. It felt soft and light, and the children felt proud because their teamwork had power."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other to do one job together. When everyone joins in, the job can feel easier and faster."
        ),
        QAItem(
            question="What does a towel do?",
            answer="A towel can soak up water and help dry things off. People use towels after washing, swimming, or getting caught in the rain."
        ),
        QAItem(
            question="What does it mean when something is damp?",
            answer="Damp means a little bit wet. It is not dripping, but it still feels moist to the touch."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


PLACES = {
    "laundry": Place("laundry", "laundry room", "inside", True, {"wet"}),
    "porch": Place("porch", "porch", "outside", True, {"wet"}),
    "bath": Place("bath", "bathroom", "inside", True, {"wet"}),
}

TOOLS = {
    "towel": Tool("towel", "towel", "a fluffy towel", 1, {"towel"}),
    "big_towel": Tool("big_towel", "big towel", "a big bright towel", 2, {"towel"}),
}

HELPERS = {
    "helper": Helper("helper", "helper", "a kind helper", "help-dry", {"teamwork"}),
}

GIRL_NAMES = ["Mia", "Nia", "Luna", "Zoe"]
BOY_NAMES = ["Max", "Noah", "Eli", "Sam"]


CURATED = [
    StoryParams("laundry", "towel", "helper", "Mia", "Noah"),
    StoryParams("porch", "big_towel", "helper", "Luna", "Eli"),
]


def explain_rejection(place: Place, tool: Tool, helper: Helper) -> str:
    return "(No story: this combination does not fit the tiny teamwork setup.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.wet:
            lines.append(asp.fact("wet", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("power", tid, t.power))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("skill", hid, h.skill))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,H) :- wet(P), tool(T), helper(H), power(T, Pwr), Pwr >= 1, skill(H, help_dry).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class CLIStoryParams:
    place: str
    tool: str
    helper: str
    child1: str
    child2: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming teamwork storyworld with pat-dim, towel, and power.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child1")
    ap.add_argument("--child2")
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations.")
    place, tool, helper = rng.choice(combos)
    if args.place:
        place = args.place
    if args.tool:
        tool = args.tool
    if args.helper:
        helper = args.helper
    if (place, tool, helper) not in combos:
        raise StoryError(explain_rejection(PLACES[place], TOOLS[tool], HELPERS[helper]))
    c1 = args.child1 or rng.choice(GIRL_NAMES)
    pool = [n for n in BOY_NAMES if n != c1] if c1 in GIRL_NAMES else [n for n in GIRL_NAMES if n != c1]
    c2 = args.child2 or rng.choice(pool)
    return StoryParams(place, tool, helper, c1, c2)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TOOLS[params.tool], HELPERS[params.helper], params.child1, params.child2)
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


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH in valid combos.")
        return 1
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: story generation failed.")
        return 1
    print("OK: ASP parity and story smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
