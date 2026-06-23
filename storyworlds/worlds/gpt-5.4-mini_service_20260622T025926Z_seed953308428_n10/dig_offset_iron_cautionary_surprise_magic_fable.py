#!/usr/bin/env python3
"""
storyworlds/worlds/dig_offset_iron_cautionary_surprise_magic_fable.py
======================================================================

A small fable-like story world about a curious child, a magical iron weight,
and the surprise lesson that trying to "offset" a problem without understanding
it can make a bigger one. The simulation keeps track of physical meters and
emotional memes, and the prose follows the world state rather than a frozen
template.

Seed premise:
- A child wants to dig in a garden.
- A shiny iron charm promises to offset the soil bucket.
- Magic gives a surprise turn.
- The cautionary ending teaches care around old roots and hidden things.

The domain is intentionally compact: one entity model, one world model, a few
registry dataclasses, a forward rule, a reasonableness gate, and a tiny ASP
twin.
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
    phrase: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Place:
    id: str
    label: str
    kind: str
    afford: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    power: int
    magic: bool = False
    iron: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Risk:
    id: str
    label: str
    phrase: str
    hidden: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    fits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    tool: str
    risk: str
    remedy: str
    name: str
    gender: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_magic_offset(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    tool = world.entities.get("tool")
    risk = world.entities.get("risk")
    if not child or not tool or not risk:
        return out
    if child.meters["dig"] < THRESHOLD or tool.meters["offset"] < THRESHOLD:
        return out
    sig = ("offset", risk.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if risk.hidden:
        risk.meters["revealed"] += 1
        child.memes["surprise"] += 1
        out.append(f"The soil shifted in a surprising way, and {risk.label} showed itself.")
    if tool.magic:
        child.memes["caution"] += 1
        out.append(f"The magic of the {tool.label} made the ground feel wise and watchful.")
    return out


CAUSAL_RULES = [Rule("magic_offset", _r_magic_offset)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def valid_combo(place: Place, tool: Tool, risk: Risk, remedy: Remedy) -> bool:
    if "dig" not in place.afford:
        return False
    if not tool.iron or not tool.magic:
        return False
    if "offset" not in tool.tags:
        return False
    if "cautionary" not in remedy.tags:
        return False
    return risk.hidden and "root" in risk.tags and "dig" in risk.tags


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for pid, p in PLACES.items():
        for tid, t in TOOLS.items():
            for rid, r in RISKS.items():
                for mid, m in REMEDIES.items():
                    if valid_combo(p, t, r, m):
                        out.append((pid, tid, rid, mid))
    return out


def explain_rejection(place: Place, tool: Tool, risk: Risk, remedy: Remedy) -> str:
    if "dig" not in place.afford:
        return "(No story: this place does not support digging.)"
    if not (tool.iron and tool.magic and "offset" in tool.tags):
        return "(No story: the tool must be a magical iron offset tool.)"
    if not (risk.hidden and "root" in risk.tags and "dig" in risk.tags):
        return "(No story: this risk is not the kind that can be revealed by digging.)"
    return "(No story: the chosen setup is not a reasonable fable.)"


def build_plot(world: World) -> None:
    child = world.get("child")
    caretaker = world.get("caretaker")
    tool = world.get("tool")
    risk = world.get("risk")
    remedy = world.get("remedy")
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} lived by {world.place.label} and loved to dig where the soil looked soft."
    )
    world.say(
        f"One morning {child.id} found {tool.phrase}; the little {tool.label} could offset a bucket of earth as if it were a feather."
    )
    world.para()
    child.meters["dig"] += 1
    tool.meters["offset"] += 1
    world.say(
        f"{child.id} began to dig near the old tree, while {caretaker.id} called out a gentle warning."
    )
    world.say(
        f'"Not every hidden thing wants to be found," {caretaker.id} said. "Some roots rest under the ground for a reason."'
    )
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"Then came the surprise: the iron charm tugged the spade sideways, and the mound opened over {risk.phrase}."
    )
    child.memes["fear"] += 1
    if tool.magic:
        child.memes["awe"] += 1
    if risk.meters["revealed"] >= THRESHOLD:
        world.say(
            f"{child.id} stopped at once and set the {tool.label} down, because a fable is wiser when it listens."
        )
    world.para()
    child.memes["lesson"] += 1
    world.say(
        f"After that, {child.id} used {remedy.phrase} instead, and the path stayed even for the evening walk."
    )
    world.say(
        f"{caretaker.id} smiled, because the garden kept its secret and the child kept the lesson."
    )


def tell(place: Place, tool: Tool, risk: Risk, remedy: Remedy, name: str, gender: str, caretaker: str, trait: str) -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=gender, label=name, role="hero", attrs={"trait": trait}))
    grown = world.add(Entity(id="caretaker", kind="character", type="mother", label=caretaker, role="caretaker"))
    tool_ent = world.add(Entity(id="tool", kind="thing", type="thing", label=tool.label, phrase=tool.phrase, tags=set(tool.tags)))
    tool_ent.magic = tool.magic  # type: ignore[attr-defined]
    tool_ent.iron = tool.iron    # type: ignore[attr-defined]
    risk_ent = world.add(Entity(id="risk", kind="thing", type="thing", label=risk.label, phrase=risk.phrase, tags=set(risk.tags)))
    risk_ent.hidden = risk.hidden  # type: ignore[attr-defined]
    remedy_ent = world.add(Entity(id="remedy", kind="thing", type="thing", label=remedy.label, phrase=remedy.phrase, tags=set(remedy.tags)))
    world.facts.update(place=place, tool=tool, risk=risk, remedy=remedy, child=child, caretaker=grown)
    build_plot(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cautionary fable for a small child about digging near a hidden root at {f["place"].label}. Include the words "dig", "offset", and "iron".',
        f"Tell a magical surprise story where {f['child'].label} uses an iron charm to offset a garden tool, then learns to slow down and listen.",
        f"Write a fable with a warning, a surprise, and a gentle lesson about {f['tool'].label} and what can happen when someone digs too eagerly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    caretaker: Entity = f["caretaker"]
    place: Place = f["place"]
    tool: Tool = f["tool"]
    risk: Risk = f["risk"]
    qa = [
        QAItem(
            question=f"Where did {child.label} want to dig?",
            answer=f"{child.label} wanted to dig at {place.label}, where the soil looked soft and easy to move. That made the child curious enough to try before thinking twice.",
        ),
        QAItem(
            question=f"What did the iron tool do for the soil bucket?",
            answer=f"The iron charm helped offset the bucket of earth, so the digging felt lighter. That strange help was part of the surprise, because it made the ground move faster than the child expected.",
        ),
        QAItem(
            question=f"Why did {caretaker.label} warn {child.label}?",
            answer=f"{caretaker.label} warned {child.label} because some hidden roots should not be disturbed. The warning mattered because a surprise can be harmless, but it can also reveal something fragile under the ground.",
        ),
        QAItem(
            question=f"What changed after the hidden thing was found?",
            answer=f"After the hidden root was revealed, {child.label} stopped and chose a safer way to level the path. The ending image proves the lesson: the garden stayed calm, and the child learned caution.",
        ),
    ]
    if world.get("risk").meters["revealed"] >= THRESHOLD:
        qa.append(
            QAItem(
                question=f"What surprise appeared when the child kept digging?",
                answer=f"{risk.phrase} appeared when the dirt shifted, and that surprise made the child feel small and careful at once. The magic helped reveal it, but the lesson was to pause before digging farther.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["tool"].tags) | set(f["risk"].tags) | set(f["remedy"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
    return out


KNOWLEDGE = {
    "dig": [("What does it mean to dig?", "To dig means to move dirt away with a tool or your hands so you can make a hole or a path.")],
    "iron": [("What is iron?", "Iron is a strong metal. People use it to make sturdy tools and objects.")],
    "offset": [("What does offset mean?", "To offset something means to balance it or make up for it in another way.")],
    "root": [("What is a root?", "A root is the part of a plant that grows under the ground and helps hold it in place.")],
    "magic": [("What is magic in a story?", "Magic in a story is a special power that can do surprising things that real life cannot do.")],
    "cautionary": [("What is a cautionary story?", "A cautionary story gives a warning, so the reader learns to be careful.")],
    "surprise": [("What is a surprise in a story?", "A surprise is something unexpected that changes what happens next.")],
}

KNOWLEDGE_ORDER = ["dig", "offset", "iron", "root", "magic", "cautionary", "surprise"]


PLACES = {
    "garden": Place(id="garden", label="the garden", kind="outdoor", afford={"dig"}, tags={"garden", "dig"}),
    "orchard": Place(id="orchard", label="the orchard", kind="outdoor", afford={"dig"}, tags={"orchard", "dig"}),
    "bank": Place(id="bank", label="the riverbank", kind="outdoor", afford={"dig"}, tags={"bank", "dig"}),
}

TOOLS = {
    "iron_spade": Tool(id="iron_spade", label="iron spade", phrase="a polished iron spade", power=2, magic=True, iron=True, tags={"iron", "offset", "magic"}),
    "iron_weight": Tool(id="iron_weight", label="iron weight", phrase="a small iron weight on a cord", power=1, magic=True, iron=True, tags={"iron", "offset", "magic"}),
}

RISKS = {
    "root": Risk(id="root", label="old root", phrase="an old root under the soil", hidden=True, tags={"root", "dig"}),
    "stone": Risk(id="stone", label="buried stone", phrase="a buried stone", hidden=True, tags={"stone", "dig"}),
}

REMEDIES = {
    "rake": Remedy(id="rake", label="garden rake", phrase="a garden rake and a slower hand", fits={"cautionary"}, tags={"cautionary"}),
    "path": Remedy(id="path", label="path stones", phrase="flat path stones", fits={"cautionary"}, tags={"cautionary"}),
}

GIRL_NAMES = ["Ava", "Mira", "Nia", "Luna", "Ivy", "Tess"]
BOY_NAMES = ["Ezra", "Owen", "Leo", "Nico", "Finn", "Milo"]
TRAITS = ["careful", "curious", "bright", "steady", "thoughtful"]


CURATED = [
    StoryParams(place="garden", tool="iron_spade", risk="root", remedy="rake", name="Mira", gender="girl", caretaker="Grandma", trait="curious"),
    StoryParams(place="orchard", tool="iron_weight", risk="root", remedy="path", name="Owen", gender="boy", caretaker="Aunt", trait="careful"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    return sorted(valid_combo(PLACES[p], TOOLS[t], RISKS[r], REMEDIES[m])
                  and (p, t, r, m) for p in PLACES for t in TOOLS for r in RISKS for m in REMEDIES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a cautious fable with magic and surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker")
    ap.add_argument("--trait", choices=TRAITS)
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
              if (args.place is None or c[0] == args.place)
              and (args.tool is None or c[1] == args.tool)
              and (args.risk is None or c[2] == args.risk)
              and (args.remedy is None or c[3] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, tool, risk, remedy = rng.choice(combos)
    name = args.name or rng.choice(GIRL_NAMES if (args.gender or "girl") == "girl" else BOY_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    caretaker = args.caretaker or rng.choice(["Grandma", "Grandpa", "Aunt", "Uncle"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, tool=tool, risk=risk, remedy=remedy, name=name, gender=gender, caretaker=caretaker, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.tool not in TOOLS or params.risk not in RISKS or params.remedy not in REMEDIES:
        raise StoryError("invalid params")
    if not valid_combo(PLACES[params.place], TOOLS[params.tool], RISKS[params.risk], REMEDIES[params.remedy]):
        raise StoryError(explain_rejection(PLACES[params.place], TOOLS[params.tool], RISKS[params.risk], REMEDIES[params.remedy]))
    world = tell(PLACES[params.place], TOOLS[params.tool], RISKS[params.risk], REMEDIES[params.remedy], params.name, params.gender, params.caretaker, params.trait)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
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
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
digging(child) :- child(role, hero), meter(child, dig, D), D >= 1.
offseting(tool) :- tool(magic), tool(iron), tool_tag(tool, offset).
revealed(risk) :- hidden(risk), digging(child), offseting(tool), risk_tag(risk, dig).
lesson(child) :- revealed(risk), cautionary(remedy).
valid(P,T,R,M) :- place(P), tool(T), risk(R), remedy(M), afford(P, dig), tool(magic), tool(iron), tool_tag(T, offset), hidden(R), risk_tag(R, dig), cautionary(M).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.afford):
            lines.append(asp.fact("afford", pid, a))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.magic:
            lines.append(asp.fact("magic", tid))
        if t.iron:
            lines.append(asp.fact("iron", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tool_tag", tid, tag))
    for rid, r in RISKS.items():
        lines.append(asp.fact("risk", rid))
        if r.hidden:
            lines.append(asp.fact("hidden", rid))
        for tag in sorted(r.tags):
            lines.append(asp.fact("risk_tag", rid, tag))
    for mid, m in REMEDIES.items():
        lines.append(asp.fact("remedy", mid))
        for tag in sorted(m.tags):
            lines.append(asp.fact("cautionary", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP parity matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP parity failed.")
    for seed in (1, 7, 777):
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(seed))
        sample = generate(params)
        if not sample.story.strip():
            rc = 1
            print(f"EMPTY STORY at seed {seed}")
    sample = generate(CURATED[0])
    _ = sample.to_json()
    sample2 = generate(CURATED[1])
    if len({sample.story, sample2.story}) < 2:
        rc = 1
        print("DUPLICATE STORY")
    try:
        _ = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
    except Exception as e:
        rc = 1
        print(f"SMOKE FAIL: {e}")
    try:
        for _ in range(3):
            p = resolve_params(build_parser().parse_args([]), random.Random(random.randrange(10000)))
            s = generate(p)
            if not s.story:
                raise RuntimeError("empty")
    except Exception as e:
        rc = 1
        print(f"VERIFY FAIL: {e}")
    if rc == 0:
        print("OK: generation smoke tests passed.")
    return rc


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
