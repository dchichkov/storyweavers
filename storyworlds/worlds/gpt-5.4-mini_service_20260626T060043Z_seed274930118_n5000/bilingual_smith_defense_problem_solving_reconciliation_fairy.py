#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about a bilingual smith who helps with defense,
solves a problem with a clever repair, and reconciles two worried neighbors.

The premise is simple:
- A village has a weak defense gate.
- A smith can speak two languages.
- Two neighbors argue about how to fix the danger.
- The smith listens, solves the problem, and brings them back together.

The story is generated from a live world model, not from a frozen paragraph.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "maid"}
        male = {"boy", "man", "father", "king", "smith", "prince", "guard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: callable


def _rule_fray(world: World) -> list[str]:
    out: list[str] = []
    gate = world.entities.get("gate")
    for e in world.entities.values():
        if e.kind == "weather" and e.meters.get("storm", 0.0) >= THRESHOLD and gate:
            sig = ("fray",)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            gate.meters["damage"] = gate.meters.get("damage", 0.0) + 1.0
            out.append("The old gate groaned under the storm and showed a weak crack.")
    return out


def _rule_worry(world: World) -> list[str]:
    out: list[str] = []
    gate = world.entities.get("gate")
    if not gate or gate.meters.get("damage", 0.0) < THRESHOLD:
        return out
    for eid in ("guard", "villager"):
        if eid not in world.entities:
            continue
        char = world.get(eid)
        sig = ("worry", eid)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        char.memes["worry"] = char.memes.get("worry", 0.0) + 1.0
        out.append(f"{char.label} worried that the village would not stay safe.")
    return out


RULES = [Rule("fray", _rule_fray), Rule("worry", _rule_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    fixes: str
    coverage: str


@dataclass
class StoryParams:
    place: str
    smith: str
    guard: str
    villager: str
    language_a: str
    language_b: str
    tool: str
    seed: Optional[int] = None


PLACES = ["the willow village", "the hill village", "the little stone village"]

SMITH_NAMES = ["Ari", "Mila", "Niko", "Sera", "Tomas", "Lina"]
GUARD_NAMES = ["Bran", "Kira", "Oren", "Mara", "Evan", "Tala"]
VILLAGER_NAMES = ["Pip", "Nell", "Rook", "Ivy", "Perry", "Wren"]

LANGUAGE_PAIRS = [
    ("Common", "Old Tongue"),
    ("River Speech", "Hill Speech"),
    ("Lantern Words", "Forest Words"),
]

TOOLS = {
    "iron_patch": Tool(
        id="iron_patch",
        label="an iron patch",
        phrase="a small iron patch for the gate",
        helps="seal the crack",
        fixes="mended the crack",
        coverage="the broken place",
    ),
    "brace": Tool(
        id="brace",
        label="a sturdy brace",
        phrase="a sturdy brace for the gate",
        helps="hold the gate straight",
        fixes="held the gate straight",
        coverage="the whole hinge",
    ),
    "lock": Tool(
        id="lock",
        label="a shining lock",
        phrase="a shining lock for the gate",
        helps="keep the gate closed",
        fixes="kept the gate closed",
        coverage="the latch",
    ),
}


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def is_reasonable(tool: Tool) -> bool:
    return tool.id in TOOLS


def select_tool(place: str) -> Tool:
    if "stone" in place:
        return TOOLS["brace"]
    if "willow" in place:
        return TOOLS["iron_patch"]
    return TOOLS["lock"]


def explain_invalid(tool: str) -> str:
    return f"(No story: {tool!r} is not a valid defense tool in this tiny fairy-tale world.)"


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------

def predict_damage(world: World) -> bool:
    sim = world.copy()
    sim.get("storm").meters["storm"] = 1.0
    propagate(sim, narrate=False)
    return sim.get("gate").meters.get("damage", 0.0) >= THRESHOLD


def start_world(params: StoryParams) -> World:
    world = World(params.place)
    smith = world.add(Entity(
        id="smith",
        kind="character",
        type="smith",
        label=params.smith,
        traits=["bilingual", "kind", "clever"],
    ))
    guard = world.add(Entity(
        id="guard",
        kind="character",
        type="guard",
        label=params.guard,
        traits=["stern", "brave"],
    ))
    villager = world.add(Entity(
        id="villager",
        kind="character",
        type="villager",
        label=params.villager,
        traits=["worried", "hopeful"],
    ))
    gate = world.add(Entity(
        id="gate",
        type="gate",
        label="the village gate",
        phrase="the old village gate",
        meters={"damage": 0.0},
    ))
    storm = world.add(Entity(
        id="storm",
        kind="weather",
        type="storm",
        label="the storm",
        meters={"storm": 0.0},
    ))
    world.facts.update(
        smith=smith,
        guard=guard,
        villager=villager,
        gate=gate,
        storm=storm,
        place=params.place,
        language_a=params.language_a,
        language_b=params.language_b,
        tool=TOOLS[params.tool],
    )
    return world


def tell(world: World) -> None:
    f = world.facts
    smith: Entity = f["smith"]
    guard: Entity = f["guard"]
    villager: Entity = f["villager"]
    gate: Entity = f["gate"]
    storm: Entity = f["storm"]
    tool: Tool = f["tool"]

    world.say(
        f"In {f['place']}, there lived a bilingual smith named {smith.label}. "
        f"{smith.label} could speak both {f['language_a']} and {f['language_b']}, "
        f"and that made every heart in the village a little calmer."
    )
    world.say(
        f"Near the old gate stood {guard.label}, who wanted the walls fixed fast, "
        f"and {villager.label}, who feared the storm would push the gate open."
    )

    world.para()
    world.say(
        f"One night, dark clouds rolled over the village. The wind began to tug at the gate, "
        f"and the old wood creaked."
    )
    storm.meters["storm"] = 1.0
    propagate(world)

    world.say(
        f"{guard.label} said, 'We must bar it now!' and {villager.label} said, "
        f"'No, we need a careful repair first!'"
    )
    guard.memes["conflict"] = guard.memes.get("conflict", 0.0) + 1.0
    villager.memes["conflict"] = villager.memes.get("conflict", 0.0) + 1.0

    world.para()
    world.say(
        f"{smith.label} listened to both of them. First, {smith.label} spoke in {f['language_a']} "
        f"to calm {guard.label}. Then {smith.label} answered in {f['language_b']} so "
        f"{villager.label} would feel heard."
    )
    world.say(
        f"After that, {smith.label} looked at the crack and chose {tool.label}. "
        f"It was just the right tool to {tool.helps}."
    )

    gate.meters["damage"] = gate.meters.get("damage", 0.0) + 1.0
    world.say(
        f"With steady hands, {smith.label} worked under the lantern glow and {tool.fixes}."
    )
    gate.meters["damage"] = 0.0
    guard.memes["conflict"] = 0.0
    villager.memes["conflict"] = 0.0
    guard.memes["peace"] = guard.memes.get("peace", 0.0) + 1.0
    villager.memes["peace"] = villager.memes.get("peace", 0.0) + 1.0
    smith.memes["pride"] = smith.memes.get("pride", 0.0) + 1.0
    smith.memes["reconciliation"] = smith.memes.get("reconciliation", 0.0) + 1.0

    world.para()
    world.say(
        f"When the work was done, {guard.label} and {villager.label} stopped arguing. "
        f"They both thanked {smith.label}, and {guard.label} even helped hold the lantern "
        f"while {villager.label} tied the last knot."
    )
    world.say(
        f"By dawn, the gate stood strong again, and the village slept safely behind it."
    )
    world.facts["resolved"] = True
    world.facts["tool"] = tool
    world.facts["reconciled"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    smith: Entity = f["smith"]
    return [
        f"Write a fairy tale about a bilingual smith named {smith.label} who solves a defense problem.",
        f"Tell a short story where a village gate is in danger, but a clever smith finds a peaceful fix.",
        f"Write a child-friendly fairy tale with bilingual dialogue, a smith, and reconciliation at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    smith: Entity = f["smith"]
    guard: Entity = f["guard"]
    villager: Entity = f["villager"]
    tool: Tool = f["tool"]

    return [
        QAItem(
            question=f"Who was the bilingual smith in the story?",
            answer=f"The bilingual smith was {smith.label}. {smith.label} could speak {f['language_a']} and {f['language_b']}.",
        ),
        QAItem(
            question=f"What problem did {smith.label} have to solve?",
            answer=f"{smith.label} had to solve a defense problem: the village gate was weak during the storm.",
        ),
        QAItem(
            question=f"What tool did {smith.label} choose to fix the gate?",
            answer=f"{smith.label} chose {tool.label} because it was the right tool to defend the gate.",
        ),
        QAItem(
            question=f"Who stopped arguing by the end?",
            answer=f"{guard.label} and {villager.label} stopped arguing after {smith.label} helped them understand each other.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "bilingual": [
        QAItem(
            question="What does bilingual mean?",
            answer="Bilingual means a person can speak two languages.",
        )
    ],
    "smith": [
        QAItem(
            question="What does a smith do?",
            answer="A smith works with metal and makes or repairs useful things like tools, locks, and strong parts.",
        )
    ],
    "defense": [
        QAItem(
            question="What is defense?",
            answer="Defense means protecting something so it stays safe.",
        )
    ],
    "reconciliation": [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who were upset or apart make peace and come back together.",
        )
    ],
    "problem_solving": [
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means looking carefully at a difficulty and finding a good way to fix it.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        q
        for key in ["bilingual", "smith", "defense", "problem_solving", "reconciliation"]
        for q in WORLD_KNOWLEDGE[key]
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A gate is at risk when a storm is present.
at_risk(gate) :- storm(storm).

% A repair is reasonable when the tool is suited to the gate.
reasonable(iron_patch) :- tool(iron_patch).
reasonable(brace) :- tool(brace).
reasonable(lock) :- tool(lock).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in enumerate(PLACES):
        lines.append(asp.fact("place", pid, place))
    for t in TOOLS.values():
        lines.append(asp.fact("tool", t.id))
    lines.append(asp.fact("storm", "storm"))
    lines.append(asp.fact("gate", "gate"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    py = {tool_id for tool_id in TOOLS}
    model = asp.one_model(asp_program("#show reasonable/1."))
    asp_set = {args[0] for args in asp.atoms(model, "reasonable")}
    if asp_set == py:
        print(f"OK: clingo gate matches Python registry ({len(py)} tools).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in asp:", sorted(asp_set - py))
    print("  only in python:", sorted(py - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a bilingual smith and village defense.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--smith", choices=SMITH_NAMES)
    ap.add_argument("--guard", choices=GUARD_NAMES)
    ap.add_argument("--villager", choices=VILLAGER_NAMES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(PLACES)
    tool = args.tool or select_tool(place).id
    smith = args.smith or rng.choice(SMITH_NAMES)
    guard = args.guard or rng.choice(GUARD_NAMES)
    villager = args.villager or rng.choice(VILLAGER_NAMES)
    la, lb = rng.choice(LANGUAGE_PAIRS)
    if tool not in TOOLS:
        raise StoryError(explain_invalid(tool))
    return StoryParams(place=place, smith=smith, guard=guard, villager=villager,
                       language_a=la, language_b=lb, tool=tool)


def generate(params: StoryParams) -> StorySample:
    world = start_world(params)
    tell(world)
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


# ---------------------------------------------------------------------------
# Main / CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="the willow village", smith="Ari", guard="Bran", villager="Ivy",
                language_a="Common", language_b="Old Tongue", tool="iron_patch"),
    StoryParams(place="the hill village", smith="Mila", guard="Kira", villager="Pip",
                language_a="River Speech", language_b="Hill Speech", tool="brace"),
    StoryParams(place="the little stone village", smith="Sera", guard="Oren", villager="Wren",
                language_a="Lantern Words", language_b="Forest Words", tool="lock"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonable/1."))
        print(sorted(asp.atoms(model, "reasonable")))
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
            except StoryError as e:
                print(e)
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
