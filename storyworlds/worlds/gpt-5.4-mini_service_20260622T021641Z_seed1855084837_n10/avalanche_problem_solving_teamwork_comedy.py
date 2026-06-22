#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T021641Z_seed1855084837_n10/avalanche_problem_solving_teamwork_comedy.py
===============================================================================================================

A standalone storyworld about a funny mountain rescue drill that turns into a
real avalanche problem. The world uses typed entities, physical meters and
emotional memes, a small causal model, a reasonableness gate, and an inline ASP
twin for parity checks.

Seed premise:
- A small team of mountain helpers goes out to clear a blocked trail.
- Their work accidentally triggers a harmless-to-people but messy avalanche.
- They solve the problem together with teamwork, improvised tools, and comedy.
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
SNOW_TYPES = {"powder", "slab"}
TOOLS = {"shovel", "rope", "sled", "drum"}
CHOICES = {"hill", "ridge", "trail"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    plural: bool = False
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Terrain:
    place: str
    slope: str
    has_cliff: bool
    snow_kind: str
    labels: set[str] = field(default_factory=set)


@dataclass
class TeamTool:
    id: str
    label: str
    use: str
    helps: set[str]
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str = "the snowy hill"
    terrain: str = "hill"
    tool1: str = "shovel"
    tool2: str = "rope"
    helper1: str = "Mina"
    helper1_gender: str = "girl"
    helper2: str = "Ollie"
    helper2_gender: str = "boy"
    leader: str = "Coach"
    leader_gender: str = "man"
    snow_kind: str = "powder"
    seed: Optional[int] = None


class World:
    def __init__(self, terrain: Terrain) -> None:
        self.terrain = terrain
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
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
        w = World(self.terrain)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_slide(world: World) -> list[str]:
    out = []
    team = [e for e in world.characters() if e.role in {"helper1", "helper2"}]
    if not team:
        return out
    if sum(e.meters["snow"] for e in team) < THRESHOLD:
        return out
    if world.fired.__contains__(("slide", world.terrain.place)):
        return out
    world.fired.add(("slide", world.terrain.place))
    for e in team:
        e.memes["surprise"] += 1
        e.meters["mess"] += 1
    world.get("path").meters["blocked"] += 1
    out.append("An avalanche slipped down the slope and blocked the path.")
    return out


def _r_cooperate(world: World) -> list[str]:
    if world.fired.__contains__(("cooperate",)):
        return []
    if any(e.memes["panic"] >= THRESHOLD for e in world.characters()) and any(
        e.memes["plan"] >= THRESHOLD for e in world.characters()
    ):
        world.fired.add(("cooperate",))
        for e in world.characters():
            e.memes["calm"] += 1
        return ["The team took a breath and made a plan together."]
    return []


CAUSAL_RULES = [Rule("slide", "physical", _r_slide), Rule("cooperate", "social", _r_cooperate)]


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


def terrain_risk(terrain: Terrain, tool: TeamTool) -> bool:
    return "snow" in tool.helps and terrain.snow_kind in {"powder", "slab"}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, terr in TERRAINS.items():
        for tid, tool in TOOLS_REGISTRY.items():
            for aid in ACTIONS:
                if terrain_risk(terr, tool) and aid in {"dig", "clear"}:
                    out.append((place, tid, aid))
    return out


def reason(msg: str) -> str:
    return f"(No story: {msg})"


KNOWLEDGE = {
    "avalanche": [("What is an avalanche?", "An avalanche is a big slide of snow that rushes downhill.")],
    "shovel": [("What is a shovel for?", "A shovel helps people move snow, dirt, or sand.")],
    "rope": [("What is a rope for?", "A rope can help people pull, lift, or hold things together.")],
    "sled": [("What is a sled for?", "A sled lets people slide on snow in a fun and careful way.")],
    "teamwork": [("What is teamwork?", "Teamwork is when people help each other to solve a problem together.")],
    "problem": [("What does it mean to solve a problem?", "It means finding a way to fix something that is hard or stuck.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a funny mountain story for a small child that includes the word "avalanche" and shows teamwork.',
        f"Tell a comedy story where {f['a'].id} and {f['b'].id} try to clear {world.terrain.place} and a snow slide makes them think fast.",
        f"Write a problem-solving story about a small team using {f['tool1'].label} and {f['tool2'].label} to deal with an avalanche.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, lead = f["a"], f["b"], f["lead"]
    t1, t2 = f["tool1"], f["tool2"]
    qa = [
        QAItem(
            f"Who worked together at {world.terrain.place}?",
            f"{a.id} and {b.id} worked together with {lead.id} to solve the mountain problem.",
        ),
        QAItem(
            f"What problem showed up while they were clearing the trail?",
            f"An avalanche slipped down the slope and blocked the path. It made the job funny and tricky at the same time.",
        ),
        QAItem(
            f"What tools did they use to handle the problem?",
            f"They used {t1.label} and {t2.label}. One helped move snow, and the other helped them pull and steady their plan.",
        ),
    ]
    if f.get("solved"):
        qa.append(QAItem(
            f"How did they solve the avalanche problem?",
            f"They made a plan, used both tools together, and got the trail open again. Their teamwork turned a messy slip into a safe ending.",
        ))
        qa.append(QAItem(
            f"Why did everyone laugh at the end?",
            f"The snow ended up on their boots, their noses, and even the tip of a tool, so the rescue felt silly. But they still solved it together.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["terrain"].labels)
    tags.add("teamwork")
    tags.add("problem")
    tags.add("avalanche")
    tags |= set(world.facts["tool1"].tags) | set(world.facts["tool2"].tags)
    out: list[QAItem] = []
    for k in ["avalanche", "shovel", "rope", "sled", "teamwork", "problem"]:
        if k in tags and k in KNOWLEDGE:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[k])
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


TERRAINS = {
    "hill": Terrain(place="the snowy hill", slope="steep", has_cliff=False, snow_kind="powder", labels={"avalanche", "teamwork", "problem"}),
    "ridge": Terrain(place="the icy ridge", slope="steeper", has_cliff=True, snow_kind="slab", labels={"avalanche", "teamwork", "problem"}),
    "trail": Terrain(place="the mountain trail", slope="bumpy", has_cliff=False, snow_kind="powder", labels={"avalanche", "teamwork", "problem"}),
}

TOOLS_REGISTRY = {
    "shovel": TeamTool(id="shovel", label="a red shovel", use="dig", helps={"snow", "problem"}, tags={"shovel"}),
    "rope": TeamTool(id="rope", label="a long rope", use="pull", helps={"snow", "teamwork"}, tags={"rope"}),
    "sled": TeamTool(id="sled", label="a little sled", use="slide", helps={"fun", "teamwork", "snow"}, tags={"sled"}),
    "drum": TeamTool(id="drum", label="a tin drum", use="signal", helps={"teamwork"}, tags={"drum"}),
}

ACTIONS = {"dig", "clear", "pull", "signal"}

GIRL_NAMES = ["Mina", "Ivy", "Luna", "Pia", "Nia", "Ruby"]
BOY_NAMES = ["Ollie", "Noah", "Ezra", "Ben", "Theo", "Finn"]


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def explain_rejection(terrain: Terrain, tool: TeamTool) -> str:
    return reason(f"{tool.label} does not make sense for this snowy teamwork story on {terrain.place}.")


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for tid, t in TERRAINS.items():
        lines.append(asp.fact("terrain", tid))
        for lab in sorted(t.labels):
            lines.append(asp.fact("tag", tid, lab))
        lines.append(asp.fact("snowkind", tid, t.snow_kind))
    for tid, t in TOOLS_REGISTRY.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,A) :- terrain(P), tool(T), action(A), tag(P,avalanche), helps(T,snow), (A=dig; A=clear).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    ok = True
    if python_set != clingo_set:
        ok = False
        print("MISMATCH between Python and ASP valid-combos:")
        print(" python-only:", sorted(python_set - clingo_set))
        print(" asp-only:", sorted(clingo_set - python_set))
    # Smoke test ordinary generation
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        ok = False
    if ok:
        print(f"OK: ASP parity and generate() smoke test passed ({len(python_set)} combos).")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy avalanche teamwork storyworld.")
    ap.add_argument("--place", choices=TERRAINS.keys())
    ap.add_argument("--terrain", choices=TERRAINS.keys())
    ap.add_argument("--tool1", choices=TOOLS_REGISTRY.keys())
    ap.add_argument("--tool2", choices=TOOLS_REGISTRY.keys())
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
    terrain_key = args.terrain or args.place
    if terrain_key and terrain_key not in TERRAINS:
        raise StoryError("Unknown terrain.")
    combos = valid_combos()
    combos = [
        c for c in combos
        if (terrain_key is None or c[0] == terrain_key)
        and (args.tool1 is None or c[1] == args.tool1)
        and (args.tool2 is None or c[1] != c[2] or True)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_key, tool1_key, _ = rng.choice(sorted(combos))
    tool2_key = args.tool2 or rng.choice(sorted(k for k in TOOLS_REGISTRY if k != tool1_key))
    g1 = rng.choice(["girl", "boy"])
    g2 = "boy" if g1 == "girl" else "girl"
    helper1 = args.helper1 if hasattr(args, "helper1") and args.helper1 else _pick_name(rng, g1)
    helper2 = args.helper2 if hasattr(args, "helper2") and args.helper2 else _pick_name(rng, g2)
    leader = args.leader if hasattr(args, "leader") and args.leader else "Coach"
    snow_kind = TERRAINS[place_key].snow_kind
    return StoryParams(
        place=TERRAINS[place_key].place,
        terrain=place_key,
        tool1=tool1_key,
        tool2=tool2_key,
        helper1=helper1,
        helper1_gender=g1,
        helper2=helper2,
        helper2_gender=g2,
        leader=leader,
        leader_gender="man",
        snow_kind=snow_kind,
    )


def tell(params: StoryParams) -> World:
    terrain = TERRAINS.get(params.terrain)
    if terrain is None:
        raise StoryError("Invalid terrain.")
    t1 = TOOLS_REGISTRY.get(params.tool1)
    t2 = TOOLS_REGISTRY.get(params.tool2)
    if t1 is None or t2 is None:
        raise StoryError("Invalid tools.")
    world = World(terrain)
    a = world.add(Entity(id=params.helper1, kind="character", type=params.helper1_gender, role="helper1"))
    b = world.add(Entity(id=params.helper2, kind="character", type=params.helper2_gender, role="helper2"))
    lead = world.add(Entity(id=params.leader, kind="character", type=params.leader_gender, role="leader"))
    path = world.add(Entity(id="path", type="path", label="the trail"))
    snow = world.add(Entity(id="snowbank", type="thing", label="the snowbank"))
    a.meters["snow"] = 0
    b.meters["snow"] = 0
    a.memes["panic"] = 0
    b.memes["plan"] = 0
    lead.memes["calm"] = 0
    world.facts.update(a=a, b=b, lead=lead, tool1=t1, tool2=t2, terrain=terrain, path=path, snow=snow, solved=False)

    world.say(f"{a.id} and {b.id} went to {terrain.place} with {lead.id} to clear a trail.")
    world.say(f"They carried {t1.label} and {t2.label}, and {a.id} joked that the mountain looked sleepy.")
    world.para()
    a.meters["snow"] += 1
    b.meters["snow"] += 1
    a.memes["plan"] += 1
    b.memes["panic"] += 1
    world.say(f"They started digging, and the snow hissed and slid like a giant sneezing loaf.")
    propagate(world, narrate=True)
    world.para()
    if path.meters["blocked"] >= THRESHOLD:
        a.memes["panic"] += 1
        b.memes["plan"] += 1
        lead.memes["calm"] += 1
        world.say(f"{lead.id} pointed at the blockage and said, 'Teamwork time!'")
        world.say(f"{a.id} used the {t1.label} while {b.id} tied the {t2.label} to a sturdy post.")
        world.say(f"Together they nudged the snow aside, and the trail made a squeaky little sigh of relief.")
        world.say(f"In the end, the avalanche was a dramatic fuss, but the team won with brains, snow gear, and a lot of laughing.")
        world.facts["solved"] = True
    else:
        world.say("The mountain stayed polite, which was a little disappointing for everyone except the boots.")
        world.facts["solved"] = False
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(place="the snowy hill", terrain="hill", tool1="shovel", tool2="rope", helper1="Mina", helper1_gender="girl", helper2="Ollie", helper2_gender="boy", leader="Coach", leader_gender="man", snow_kind="powder"),
    StoryParams(place="the icy ridge", terrain="ridge", tool1="rope", tool2="shovel", helper1="Pia", helper1_gender="girl", helper2="Ben", helper2_gender="boy", leader="Coach", leader_gender="man", snow_kind="slab"),
]


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
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
