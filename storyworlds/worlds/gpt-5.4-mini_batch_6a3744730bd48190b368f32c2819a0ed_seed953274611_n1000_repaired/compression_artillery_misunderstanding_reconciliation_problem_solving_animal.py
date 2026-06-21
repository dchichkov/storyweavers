#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/compression_artillery_misunderstanding_reconciliation_problem_solving_animal.py
===============================================================================================================

A small animal-story world about a burrowing misunderstanding, a careful
problem-solving turn, and a reconciliation image at the end.

Seed words:
- compression
- artillery

Style:
- Animal Story
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "animal"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
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
class Burrow:
    id: str
    label: str
    compressed: bool = False
    blocked: bool = False
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
class Tool:
    id: str
    label: str
    kind: str
    safe: bool
    power: int
    use_text: str
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
    burrow: str
    tool: str
    helper: str
    helper_type: str
    owner: str
    owner_type: str
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _r_compress(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["squeezed"] < THRESHOLD:
            continue
        sig = ("compress", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["blocked"] += 1
        out.append("__compressed__")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out = []
    if world.facts.get("misunderstood") and not world.facts.get("talked"):
        for e in list(world.entities.values()):
            if e.role in {"owner", "helper"}:
                e.memes["hurt"] += 1
        out.append("__hurt__")
    return out


CAUSAL_RULES = [Rule("compress", _r_compress), Rule("misunderstanding", _r_misunderstanding)]


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


def hazard_ok(burrow: Burrow, tool: Tool) -> bool:
    return burrow.blocked and not tool.safe


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.safe and t.power >= SENSE_MIN]


def best_tool() -> Tool:
    return max(TOOLS.values(), key=lambda t: t.power)


def build_scene(world: World, owner: Entity, helper: Entity, burrow: Burrow, tool: Tool) -> None:
    owner.memes["busy"] += 1
    helper.memes["curious"] += 1
    world.say(
        f"In a little meadow, {owner.id} the {owner.type} was fussing over {burrow.label}. "
        f"The burrow had become tight from the damp earth, and nobody could squeeze in properly."
    )
    world.say(
        f"{helper.id} the {helper.type} watched the tunnel and said, "
        f'"Maybe we can use {tool.label}?"'
    )


def misunderstand(world: World, owner: Entity, helper: Entity, tool: Tool) -> None:
    world.facts["misunderstood"] = True
    owner.memes["worry"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"{owner.id} blinked. " 
        f'"{tool.label}? That sounds like artillery," {owner.id} said, and {helper.id} winced.'
    )
    world.say(
        f'For a moment, it seemed like {helper.id} had suggested a noisy, scary thing, not a careful way to solve the problem.'
    )


def reconcile(world: World, owner: Entity, helper: Entity) -> None:
    world.facts["talked"] = True
    owner.memes["calm"] += 1
    helper.memes["calm"] += 1
    owner.memes["love"] += 1
    helper.memes["love"] += 1
    world.say(
        f"Then {helper.id} took a breath and explained the idea again. "
        f'"I meant the little press, not a boom," {helper.id} said. '
        f'"I want to help the burrow fit everyone safely."'
    )
    world.say(
        f"{owner.id} listened, and the knot in the air loosened. "
        f"They were no longer arguing about a scary word; they were looking at the same problem."
    )


def solve_problem(world: World, owner: Entity, helper: Entity, burrow: Burrow, tool: Tool) -> None:
    burrow.compressed = True
    burrow.blocked = False
    owner.meters["relief"] += 1
    helper.meters["relief"] += 1
    world.say(
        f"Together they used {tool.label}. {tool.use_text.capitalize()}, and the soft earth settled neatly into place."
    )
    world.say(
        f"The burrow opened wider, the tiny path became smooth, and {owner.id} and {helper.id} could crawl through side by side."
    )


def end_image(world: World, owner: Entity, helper: Entity, burrow: Burrow) -> None:
    world.say(
        f"By sunset, {owner.id} sat at the mouth of {burrow.label} with {helper.id}, "
        f"sharing berries and laughing in the quiet grass. "
        f"The burrow was snug but safe, and the two animals had learned how to fix a problem by talking first."
    )


BURROWS = {
    "burrow": Burrow(id="burrow", label="the rabbit burrow", blocked=True, tags={"animal", "burrow"}),
    "den": Burrow(id="den", label="the fox den", blocked=True, tags={"animal", "burrow"}),
}

TOOLS = {
    "tamper": Tool(
        id="tamper",
        label="a small tamper",
        kind="compression",
        safe=True,
        power=3,
        use_text="the little tamper pressed the loose dirt gently down",
        tags={"compression", "safe"},
    ),
    "packer": Tool(
        id="packer",
        label="a packer tool",
        kind="compression",
        safe=True,
        power=2,
        use_text="the packer tool made the tunnel wall firm without hurting it",
        tags={"compression", "safe"},
    ),
    "cannon": Tool(
        id="cannon",
        label="artillery",
        kind="artillery",
        safe=False,
        power=5,
        use_text="the artillery noise would have shaken the meadow",
        tags={"artillery", "unsafe"},
    ),
}

ANIMALS = {
    "rabbit": ("rabbit", "girl"),
    "fox": ("fox", "boy"),
    "badger": ("badger", "boy"),
    "mole": ("mole", "girl"),
    "squirrel": ("squirrel", "girl"),
}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for b in BURROWS:
        for t in TOOLS:
            if hazard_ok(BURROWS[b], TOOLS[t]):
                combos.append((b, t))
    return combos


def story_for(params: StoryParams) -> World:
    if params.burrow not in BURROWS:
        raise StoryError("Unknown burrow.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if params.helper not in ANIMALS or params.owner not in ANIMALS:
        raise StoryError("Unknown animal.")
    burrow = BURROWS[params.burrow]
    tool = TOOLS[params.tool]
    if not hazard_ok(burrow, tool):
        raise StoryError("No story: this combination does not create a believable misunderstanding and repair.")

    world = World()
    owner = world.add(Entity(id=params.owner, kind="character", type=params.owner_type, role="owner"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper"))
    world.add(Entity(id=burrow.id, kind="thing", type="burrow", label=burrow.label))
    world.facts.update(burrow=burrow, tool=tool, owner=owner, helper=helper)

    build_scene(world, owner, helper, burrow, tool)
    world.para()
    misunderstand(world, owner, helper, tool)
    reconcile(world, owner, helper)
    world.para()
    solve_problem(world, owner, helper, burrow, tool)
    end_image(world, owner, helper, burrow)

    world.facts["resolved"] = True
    world.facts["tool_used"] = tool.id
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story that includes the words "compression" and "artillery" without using artillery as a real weapon.',
        f"Tell a short story where {f['owner'].id} and {f['helper'].id} misunderstand one another, then reconcile and solve the burrow problem.",
        f"Write a child-friendly animal story about fixing a cramped burrow with careful compression, not scary artillery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    owner = f["owner"]
    helper = f["helper"]
    burrow = f["burrow"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Why did {helper.id} and {owner.id} disagree at first?",
            answer=f"They misunderstood the word {tool.label}. {owner.id} thought it sounded like artillery, while {helper.id} meant a careful compressing tool for the burrow."
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"They talked it through, made up, and then used {tool.label} to gently compress the soil. That opened {burrow.label} enough for both animals to use it safely."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The burrow was no longer blocked, and the animals were cheerful together. The story ends with them sharing berries beside a safe, snug tunnel."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is compression?",
            answer="Compression means pressing something together so it becomes smaller, tighter, or firmer."
        ),
        QAItem(
            question="What is artillery?",
            answer="Artillery is big weapons that make loud blasts. In this story, the word causes a misunderstanding because it sounds scary."
        ),
        QAItem(
            question="Why is talking helpful when animals misunderstand each other?",
            answer="Talking helps them explain what they meant and notice the mix-up. Then they can work together instead of staying upset."
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
    out = ["--- world model state ---"]
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
        if e.label:
            bits.append(f"label={e.label}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(out)


def explain_rejection(params: StoryParams) -> str:
    return "No story: this combination does not make a believable animal misunderstanding."

CURATED = [
    StoryParams(burrow="burrow", tool="tamper", helper="mole", helper_type="girl", owner="rabbit", owner_type="girl"),
    StoryParams(burrow="den", tool="packer", helper="fox", helper_type="boy", owner="badger", owner_type="boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about compression, artillery, misunderstanding, reconciliation, and problem solving.")
    ap.add_argument("--burrow", choices=BURROWS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=ANIMALS)
    ap.add_argument("--owner", choices=ANIMALS)
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
              if (args.burrow is None or c[0] == args.burrow)
              and (args.tool is None or c[1] == args.tool)]
    if not combos:
        raise StoryError(explain_rejection(StoryParams(burrow=args.burrow or "burrow", tool=args.tool or "tamper", helper="rabbit", helper_type="girl", owner="fox", owner_type="boy")))
    burrow, tool = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(ANIMALS))
    owner = args.owner or rng.choice([a for a in ANIMALS if a != helper])
    ht = ANIMALS[helper][1]
    ot = ANIMALS[owner][1]
    return StoryParams(burrow=burrow, tool=tool, helper=helper, helper_type=ht, owner=owner, owner_type=ot)


def generate(params: StoryParams) -> StorySample:
    world = story_for(params)
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


ASP_RULES = r"""
valid(B,T) :- burrow(B), tool(T), blocked(B), safe_tool(T).
misunderstanding(B,T) :- valid(B,T), tool_kind(T, artillery).
reconcile(B,T) :- misunderstanding(B,T).
solved(B,T) :- reconcile(B,T), valid(B,T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for b in BURROWS.values():
        lines.append(asp.fact("burrow", b.id))
        if b.blocked:
            lines.append(asp.fact("blocked", b.id))
    for t in TOOLS.values():
        lines.append(asp.fact("tool", t.id))
        if t.safe:
            lines.append(asp.fact("safe_tool", t.id))
        lines.append(asp.fact("tool_kind", t.id, t.kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH in valid combos")
    else:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generate() smoke test failed: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2.\n#show misunderstanding/2.\n#show reconcile/2.\n#show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for b, t in asp_valid_combos():
            print(f"  {b:8} {t}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
