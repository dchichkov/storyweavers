#!/usr/bin/env python3
"""
storyworlds/worlds/handiwork_billy_pass_quest_space_adventure.py
===============================================================

A small space-adventure story world about Billy, handiwork, and a pass
needed for a quest through a tricky station.

Premise:
- Billy wants to help with handiwork on a little ship or station.
- A pass is needed to continue the quest.
- The captain worries the pass might be bent, lost, or not ready.
- Billy tries a bold move, learns the safer method, and the quest continues.

The simulation tracks:
- physical meters: repair progress, pass integrity, ship readiness
- emotional memes: eagerness, worry, trust, relief

The story is written from world state, not from a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Station:
    place: str = "the starport"
    has_passage: bool = True
    has_repair_bay: bool = True
    has_observatory: bool = False
    route: str = "the bright corridor"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    objective: str
    verb: str
    risk: str
    success: str
    keyword: str = "Quest"
    tags: set[str] = field(default_factory=set)


@dataclass
class Pass:
    label: str
    phrase: str
    type: str = "pass"
    fragile: bool = True
    owner_role: str = "captain"


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    cautious: str
    finish: str


class World:
    def __init__(self, station: Station) -> None:
        self.station = station
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.route = station.route

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
        import copy
        clone = World(self.station)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.route = self.route
        clone.paragraphs = [[]]
        return clone

    def character(self) -> Entity:
        for e in self.entities.values():
            if e.kind == "character":
                return e
        raise KeyError("no character")


def _narrate(world: World, text: str) -> None:
    world.say(text)


def _repair_pass(world: World) -> list[str]:
    out: list[str] = []
    billy = world.get("Billy")
    p = world.get("Pass")
    if billy.meter("handiwork") < THRESHOLD:
        return out
    if p.meter("damage") >= THRESHOLD and ("repair", "pass") not in world.fired:
        world.fired.add(("repair", "pass"))
        p.meters["damage"] = 0.0
        p.meters["ready"] = 1.0
        billy.memes["trust"] = billy.meme("trust") + 1.0
        out.append("Billy carefully fixed the pass with steady hands.")
    return out


def _quest_progress(world: World) -> list[str]:
    out: list[str] = []
    billy = world.get("Billy")
    q = world.get("Quest")
    p = world.get("Pass")
    if q.meter("started") < THRESHOLD:
        return out
    if p.meter("ready") >= THRESHOLD and ("quest", "advance") not in world.fired:
        world.fired.add(("quest", "advance"))
        q.meters["progress"] = q.meter("progress") + 1.0
        billy.memes["relief"] = billy.meme("relief") + 1.0
        out.append("The quest could move on through the shining passage.")
    return out


RULES = [_repair_pass, _quest_progress]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_outcome(world: World, billy: Entity, quest: Quest, pass_ent: Entity) -> dict:
    sim = world.copy()
    sim.get("Billy").meters["handiwork"] += 1.0
    sim.get("Pass").meters["damage"] += 1.0
    propagate(sim, narrate=False)
    return {
        "pass_ready": sim.get("Pass").meter("ready") >= THRESHOLD,
        "quest_progress": sim.get("Quest").meter("progress"),
    }


SETTINGS = {
    "starport": Station(place="the starport", has_passage=True, has_repair_bay=True, route="the bright corridor", affords={"repair", "quest"}),
    "dock": Station(place="the dock", has_passage=True, has_repair_bay=False, route="the silver tunnel", affords={"quest"}),
    "moonbase": Station(place="the moonbase", has_passage=True, has_repair_bay=True, route="the glass passage", affords={"repair", "quest"}),
}

QUESTS = {
    "pass": Quest(
        id="pass",
        objective="cross the guarded passage",
        verb="go through the passage",
        risk="the pass could bend or tear",
        success="the route stays open",
        keyword="Quest",
        tags={"pass", "quest", "space"},
    ),
    "mission": Quest(
        id="mission",
        objective="finish the station quest",
        verb="continue the quest",
        risk="the route could stay blocked",
        success="the crew reaches the next door",
        keyword="Quest",
        tags={"quest", "space"},
    ),
}

PASSES = {
    "gatepass": Pass(label="a shiny gate pass", phrase="a shiny gate pass"),
    "badge": Pass(label="a bright mission badge", phrase="a bright mission badge"),
}

TOOLS = [
    Tool(
        id="tape",
        label="a roll of silver tape",
        phrase="a roll of silver tape",
        helps={"repair"},
        cautious="wrap the torn edge first",
        finish="they walked on with the pass safely taped",
    ),
    Tool(
        id="scanner",
        label="a tiny scanner",
        phrase="a tiny scanner",
        helps={"check"},
        cautious="check the pass before the door",
        finish="the scan showed the pass was fine",
    ),
    Tool(
        id="case",
        label="a hard case",
        phrase="a hard case",
        helps={"protect"},
        cautious="keep the pass inside a hard case",
        finish="the pass stayed safe inside the case",
    ),
]

NAMES = ["Billy", "Mina", "Jory", "Nia", "Tess", "Owen"]
TRAITS = ["brave", "curious", "careful", "cheerful", "determined"]


@dataclass
class StoryParams:
    station: str
    quest: str
    pass_kind: str
    name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sname, station in SETTINGS.items():
        for qid, quest in QUESTS.items():
            for pid, p in PASSES.items():
                if station.has_passage and quest.id == "pass":
                    combos.append((sname, qid, pid))
                elif station.has_repair_bay:
                    combos.append((sname, qid, pid))
    return combos


ASP_RULES = r"""
at_risk(Q,P) :- quest(Q), pass(P), needs_pass(Q).
fix(Q,P) :- at_risk(Q,P), tool(T), helps(T, repair).
valid(S,Q,P) :- station(S), at_risk(Q,P), fix(Q,P), affords(S, repair).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("station", sid))
        if s.has_passage:
            lines.append(asp.fact("affords", sid, "quest"))
        if s.has_repair_bay:
            lines.append(asp.fact("affords", sid, "repair"))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
        if qid == "pass":
            lines.append(asp.fact("needs_pass", qid))
    for pid in PASSES:
        lines.append(asp.fact("pass", pid))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Space Adventure story for a child about {f["name"]}, handiwork, and a quest that needs a pass.',
        f"Tell a gentle story where {f['name']} wants to help with handiwork at {world.station.place} so the quest can continue.",
        f'Write a simple space quest story that includes the word "pass" and ends with a safer plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    billy = f["billy"]
    q = f["quest"]
    p = f["pass"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What did Billy want to do at {world.station.place}?",
            answer=f"Billy wanted to help with handiwork so the {q.objective} could happen.",
        ),
        QAItem(
            question=f"Why was the pass important in the story?",
            answer=f"The pass was important because Billy needed it to {q.verb}, and it had to stay ready.",
        ),
        QAItem(
            question=f"What helped Billy keep the pass safe?",
            answer=f"They used {tool.label}, which helped Billy repair and protect the pass.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal or journey someone works hard to finish.",
        ),
        QAItem(
            question="What is handiwork?",
            answer="Handiwork is careful work done by hand, like fixing, building, or mending something.",
        ),
        QAItem(
            question="Why can a pass matter on a station?",
            answer="A pass can matter because it lets someone go through a door or reach the next place safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def tell(station: Station, quest: Quest, pass_cfg: Pass, name: str, trait: str) -> World:
    world = World(station)
    billy = world.add(Entity(id="Billy", kind="character", type="boy", label=name, meters={}, memes={"eagerness": 1.0}))
    captain = world.add(Entity(id="Captain", kind="character", type="adult", label="the captain", memes={"worry": 1.0}))
    quest_ent = world.add(Entity(id="Quest", type="quest", label=quest.keyword, meters={"started": 1.0}, memes={}))
    pass_ent = world.add(Entity(id="Pass", type="pass", label=pass_cfg.label, phrase=pass_cfg.phrase, owner=captain.id, caretaker=captain.id, meters={"damage": 1.0}, memes={}))
    tool = world.add(Entity(id="Tool", type="tool", label="a silver repair tool", phrase="a silver repair tool"))

    world.facts.update(billy=billy, captain=captain, quest=quest, pass=pass_ent, tool=tool, station=station)

    _narrate(world, f"Billy was a {trait} boy aboard {station.place}, and he loved shiny space handiwork.")
    _narrate(world, f"He wanted to help with the pass so the {quest.keyword} could go on through {station.route}.")
    _narrate(world, f"The captain held up {pass_ent.label} and frowned. \"We need this to stay ready,\" {captain.pronoun('subject')} said.")
    world.para()
    _narrate(world, f"Billy looked at the broken edge and rolled up his sleeves.")
    billy.meters["handiwork"] += 1.0
    billy.memes["eagerness"] += 1.0
    predict = predict_outcome(world, billy, quest, pass_ent)
    if predict["pass_ready"]:
        _narrate(world, "He knew careful hands would help more than rushing.")
    else:
        _narrate(world, "He could tell a quick tug might make the pass worse.")

    _narrate(world, f"\"Let me fix it,\" Billy said, and he chose {tool.label} instead of forcing it.")
    world.para()
    pass_ent.meters["damage"] += 0.0
    propagate(world, narrate=True)
    if pass_ent.meter("ready") < THRESHOLD:
        pass_ent.meters["ready"] = 1.0
    quest_ent.meters["progress"] = quest_ent.meter("progress") + 1.0
    billy.memes["trust"] += 1.0
    billy.memes["relief"] += 1.0
    _narrate(world, f"At last, the pass was safe again, and Billy could go on the {quest.objective}.")
    _narrate(world, f"They walked into {station.route}, with the pass steady in Billy's hands and the stars waiting ahead.")
    return world


CURATED = [
    StoryParams(station="starport", quest="pass", pass_kind="gatepass", name="Billy", trait="curious"),
    StoryParams(station="moonbase", quest="mission", pass_kind="badge", name="Billy", trait="careful"),
    StoryParams(station="dock", quest="pass", pass_kind="gatepass", name="Billy", trait="brave"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.station and args.quest and args.pass_kind:
        if (args.station, args.quest, args.pass_kind) not in valid_combos():
            raise StoryError("No valid combination matches the given space quest options.")
    combos = [c for c in valid_combos()
              if (args.station is None or c[0] == args.station)
              and (args.quest is None or c[1] == args.quest)
              and (args.pass_kind is None or c[2] == args.pass_kind)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    station, quest, pass_kind = rng.choice(combos)
    name = args.name or "Billy"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(station=station, quest=quest, pass_kind=pass_kind, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.station], QUESTS[params.quest], PASSES[params.pass_kind], params.name, params.trait)
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
    ap = argparse.ArgumentParser(description="Space Adventure story world about Billy, handiwork, and a pass.")
    ap.add_argument("--station", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--pass-kind", choices=PASSES)
    ap.add_argument("--name")
    ap.add_argument("--trait")
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(f"{asp_facts()}\n{ASP_RULES}\n#show valid/3.\n")
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible space-quest combos:\n")
        for c in combos:
            print("  ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
