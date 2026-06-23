#!/usr/bin/env python3
"""
storyworlds/worlds/tremendous_kindness_space_adventure.py
=========================================================

A small story world for a Space Adventure with a kindness beat and a
"tremendous" turn: a child crew helps a stranded traveler and uses a safe,
careful rescue to bring them home.

The world is intentionally compact:
- typed entities with meters (physical) and memes (emotional)
- a simple forward simulation
- a reasonableness gate
- an inline ASP twin
- three Q&A sets grounded in world state
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.id)


@dataclass
class Station:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    title: str
    risk: str
    rescue: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    station: str
    mission: str
    tool: str
    name: str
    gender: str
    partner: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, station: Station) -> None:
        self.station = station
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.station)
        clone.entities = {k: Entity(**{
            "id": e.id, "kind": e.kind, "type": e.type, "label": e.label,
            "phrase": e.phrase, "role": e.role, "traits": list(e.traits),
            "owner": e.owner, "caretaker": e.caretaker, "plural": e.plural,
            "tags": set(e.tags), "attrs": dict(e.attrs),
            "meters": defaultdict(float, dict(e.meters)),
            "memes": defaultdict(float, dict(e.memes)),
        }) for k, e in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.history = list(self.history)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Any


def _r_signal(world: World) -> list[str]:
    out: list[str] = []
    traveler = world.entities.get("traveler")
    beacon = world.entities.get("beacon")
    if not traveler or not beacon:
        return out
    if traveler.meters["lost"] < THRESHOLD:
        return out
    sig = ("signal", traveler.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    beacon.meters["glow"] += 1
    out.append("The beacon answered with a steady light.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("hero")
    traveler = world.entities.get("traveler")
    if not helper or not traveler:
        return out
    if helper.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kindness", helper.id, traveler.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    traveler.memes["hope"] += 1
    helper.memes["pride"] += 1
    out.append("Kindness made the rescue feel bright and steady.")
    return out


CAUSAL_RULES = [Rule("signal", "physical", _r_signal), Rule("kindness", "social", _r_kindness)]


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


def mission_risk(mission: Mission) -> bool:
    return mission.risk in {"lost", "drift"}


def select_tool(mission: Mission, tool: Tool) -> bool:
    return mission.risk in tool.helps


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for station in STATIONS:
        for mission in MISSIONS:
            for tool in TOOLS:
                if station in STATIONS and mission_risk(MISSIONS[mission]) and select_tool(MISSIONS[mission], TOOLS[tool]):
                    combos.append((station, mission, tool))
    return combos


def reason_reject(mission: Mission, tool: Tool) -> str:
    return f"(No story: {tool.label} does not fit this rescue well enough for {mission.title}.)"


def crew_names(gender: str) -> list[str]:
    return GIRL_NAMES if gender == "girl" else BOY_NAMES


def build_world(station: Station, mission: Mission, tool: Tool, name: str, gender: str, partner: str, trait: str) -> World:
    world = World(station)
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name, traits=["small", trait]))
    mate = world.add(Entity(id="mate", kind="character", type=partner, label="the partner"))
    traveler = world.add(Entity(id="traveler", kind="character", type="person", label="the stranded traveler", attrs={"mission": mission.id}))
    beacon = world.add(Entity(id="beacon", type="thing", label="the beacon", phrase="a small beacon", tags={"beacon"}))
    tool_ent = world.add(Entity(id="tool", type="thing", label=tool.label, phrase=tool.phrase, tags=set(tool.tags)))
    hero.memes["kindness"] = 1.0
    traveler.meters["lost"] = 1.0
    world.facts.update(hero=hero, mate=mate, traveler=traveler, beacon=beacon, tool=tool_ent, mission=mission, station=station)
    return world


def setup_scene(world: World) -> None:
    hero = world.facts["hero"]
    mate = world.facts["mate"]
    mission = world.facts["mission"]
    station = world.facts["station"]
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(f"{hero.label} and {mate.label} were on a tiny star station above the glittering dark.")
    world.say(f"They were helping with {mission.title}, and the whole station felt calm and tremendous.")
    world.say(f"Outside the window, {station.place} glowed like a silver shell in space.")


def turn_scene(world: World) -> None:
    hero = world.facts["hero"]
    traveler = world.facts["traveler"]
    mission = world.facts["mission"]
    tool = world.facts["tool"]
    hero.memes["curiosity"] += 1
    traveler.meters["lost"] += 0.0
    world.para()
    world.say(f"Then {traveler.label} drifted near the bay and tapped the glass with a worried hand.")
    world.say(f"{hero.label} noticed {traveler.label} was lost, so {hero.pronoun()} reached for {tool.label}.")
    world.say(f"That was the right kind of help for this space adventure, because {mission.rescue}.")


def resolve_scene(world: World) -> None:
    hero = world.facts["hero"]
    mate = world.facts["mate"]
    traveler = world.facts["traveler"]
    tool = world.facts["tool"]
    mission = world.facts["mission"]
    hero.memes["kindness"] += 1
    world.para()
    traveler.meters["rescued"] += 1
    propagate(world, narrate=False)
    world.say(f"{hero.label} and {mate.label} used {tool.label} to guide the traveler home.")
    world.say(f"The traveler smiled, and the station window shone with a tremendous, safe glow.")
    world.say(f"At the end, {mission.image}, and kindness made the whole space trip feel warm.")


def tell(station: Station, mission: Mission, tool: Tool, name: str = "Mia", gender: str = "girl", partner: str = "boy", trait: str = "curious") -> World:
    world = build_world(station, mission, tool, name, gender, partner, trait)
    setup_scene(world)
    turn_scene(world)
    resolve_scene(world)
    return world


STATIONS = {
    "orbital_hub": Station(place="the orbital hub", afford={"rescue", "dock"}),
    "moon_port": Station(place="the moon port", afford={"rescue", "dock"}),
    "deep_ship": Station(place="the deep-space ship", afford={"rescue", "scan"}),
}

MISSIONS = {
    "lost_traveler": Mission(id="lost_traveler", title="finding the lost traveler", risk="lost", rescue="a kind guide can lead them home", image="the traveler waved from the airlock while the hub lights blinked gold", tags={"lost", "kindness"}),
    "drifting_satellite": Mission(id="drifting_satellite", title="bringing back the drifting satellite", risk="drift", rescue="a kind guide can reel it in safely", image="the satellite floated back into its cradle with a soft click", tags={"drift", "kindness"}),
}

TOOLS = {
    "tether": Tool(id="tether", label="the tether", phrase="a bright tether line", helps={"lost", "drift"}, tags={"tether"}),
    "guide_lamp": Tool(id="guide_lamp", label="the guide lamp", phrase="a guide lamp", helps={"lost"}, tags={"lamp"}),
    "magnet_hook": Tool(id="magnet_hook", label="the magnet hook", phrase="a magnet hook", helps={"drift"}, tags={"hook"}),
}

GIRL_NAMES = ["Mia", "Luna", "Nia", "Ada", "Zoe", "Ava", "Ivy", "Nora"]
BOY_NAMES = ["Kai", "Leo", "Max", "Ben", "Theo", "Finn", "Noah", "Eli"]
TRAITS = ["kind", "curious", "careful", "brave", "gentle"]

CURATED = [
    StoryParams(station="orbital_hub", mission="lost_traveler", tool="tether", name="Mia", gender="girl", partner="boy", trait="kind"),
    StoryParams(station="moon_port", mission="drifting_satellite", tool="magnet_hook", name="Kai", gender="boy", partner="girl", trait="gentle"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mission = f["mission"]
    tool = f["tool"]
    station = f["station"]
    return [
        f'Write a short space adventure for a 3-to-5-year-old with the word "tremendous" and a kindness theme.',
        f"Tell a gentle story where {hero.label} helps with {mission.title} at {station.place} using {tool.label}.",
        f"Write a child-friendly space story where kindness solves a problem and the ending feels tremendous.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    traveler = f["traveler"]
    mission = f["mission"]
    tool = f["tool"]
    station = f["station"]
    return [
        QAItem(
            f"Who were the story's main helpers at {station.place}?",
            f"It was about {hero.label} and {mate.label}. They worked together on {mission.title} and helped the stranded traveler.",
        ),
        QAItem(
            f"What did {hero.label} use to help during the space adventure?",
            f"{hero.label} used {tool.label}. That fit the rescue and helped bring the traveler back safely.",
        ),
        QAItem(
            f"Why did the traveler need help?",
            f"The traveler was lost near the bay and needed a kind guide. That is why {hero.label} reached for {tool.label}.",
        ),
        QAItem(
            f"How did the story end for {traveler.label}?",
            f"{traveler.label} smiled and came home safely. The ending showed a tremendous glow, because kindness solved the problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is kindness?", "Kindness means being gentle, caring, and helpful to someone else."),
        QAItem("What is a tether?", "A tether is a line that can help keep something from drifting away."),
        QAItem("What is an airlock?", "An airlock is a safe doorway on a spacecraft that lets people go in and out without losing air."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(sample.prompts)
    parts.append("")
    parts.append("== Story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  facts={list(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
station(X) :- station_fact(X).
mission(X) :- mission_fact(X).
tool(X) :- tool_fact(X).
helper(S, M, T) :- station(S), mission(M), tool(T), mission_risk(M, R), tool_helps(T, R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in STATIONS:
        lines.append(asp.fact("station_fact", sid))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission_fact", mid))
        lines.append(asp.fact("mission_risk", mid, m.risk))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool_fact", tid))
        for r in sorted(t.helps):
            lines.append(asp.fact("tool_helps", tid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show helper/3."))
    return sorted(set(asp.atoms(model, "helper")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        ok = False
        print("MISMATCH: ASP differs from Python.")
        print("  only in asp:", sorted(cl - py))
        print("  only in py:", sorted(py - cl))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # pragma: no cover
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny space-adventure story world built around kindness.")
    ap.add_argument("--station", choices=STATIONS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--partner", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", "--n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in STATIONS:
        for m in MISSIONS:
            for t in TOOLS:
                if select_tool(MISSIONS[m], TOOLS[t]):
                    combos.append((s, m, t))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.station is None or c[0] == args.station)
              and (args.mission is None or c[1] == args.mission)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    station, mission, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    partner = args.partner or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(crew_names(gender))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(station=station, mission=mission, tool=tool, name=name, gender=gender, partner=partner, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.station not in STATIONS or params.mission not in MISSIONS or params.tool not in TOOLS:
        raise StoryError("Invalid parameters.")
    mission = MISSIONS[params.mission]
    tool = TOOLS[params.tool]
    if not select_tool(mission, tool):
        raise StoryError(reason_reject(mission, tool))
    world = tell(STATIONS[params.station], mission, tool, params.name, params.gender, params.partner, params.trait)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(asp_program("#show helper/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
