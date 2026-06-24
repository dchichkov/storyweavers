#!/usr/bin/env python3
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    name: str
    sky: str
    has_spire: bool
    launchpad: bool
    beacon: bool


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    surprise: str
    foreshadow: str
    rhyme: str
    path: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_bits: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c

    def worn(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]


THRESHOLD = 1.0


def _r_spark(world: World) -> list[str]:
    out = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.memes.get("wonder", 0) < THRESHOLD:
            continue
        if world.setting.has_spire and world.facts.get("spire_seen") and ("spark", actor.id) not in world.fired:
            world.fired.add(("spark", actor.id))
            actor.meters["energy"] = actor.meters.get("energy", 0) + 1
            out.append(f"{actor.id} felt a bright spark of courage.")
    return out


def _r_noise(world: World) -> list[str]:
    out = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters.get("noise", 0) < THRESHOLD:
            continue
        if ("noise", actor.id) in world.fired:
            continue
        world.fired.add(("noise", actor.id))
        actor.memes["nervous"] = actor.memes.get("nervous", 0) + 1
        out.append(f"The humming path made {actor.id} a little nervous.")
    return out


RULES = [_r_spark, _r_noise]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "moonport": Setting(name="the moonport", sky="silver", has_spire=True, launchpad=True, beacon=True),
    "skydock": Setting(name="the skydock", sky="blue", has_spire=True, launchpad=True, beacon=False),
    "starfield": Setting(name="the starfield station", sky="dark", has_spire=False, launchpad=False, beacon=True),
}

MISSIONS = {
    "spire": Mission(
        id="spire",
        verb="reach the spire",
        gerund="racing toward the spire",
        surprise="At the top, a tiny door was already open.",
        foreshadow="A blinking light on the spire had winked twice before they left.",
        rhyme="High in the sky, they heard a soft cry, then a shy reply.",
        path="up the spiral stairs",
        keyword="spire",
        tags={"spire", "space", "tower"},
    ),
    "beacon": Mission(
        id="beacon",
        verb="find the beacon",
        gerund="following the beacon",
        surprise="The beacon was not a lamp at all, but a sleepy robot.",
        foreshadow="A warm beep had been pulsing from the hallway panel.",
        rhyme="Near the bright light, they giggled in delight.",
        path="through the bright hall",
        keyword="beacon",
        tags={"beacon", "space", "light"},
    ),
    "comet": Mission(
        id="comet",
        verb="catch the comet map",
        gerund="chasing the comet map",
        surprise="The map floated out of a glove box and twirled like a leaf.",
        foreshadow="A silver scrap had been stuck to the window all morning.",
        rhyme="Up past the moon, they raced to the tune.",
        path="along the telescope bridge",
        keyword="comet",
        tags={"comet", "space", "map"},
    ),
}

PRIZES = {
    "crystal": Prize(label="crystal", phrase="a small sky crystal", type="crystal", location="pocket"),
    "badge": Prize(label="badge", phrase="a shiny captain badge", type="badge", location="shirt"),
    "glove": Prize(label="glove", phrase="a soft star glove", type="glove", location="hand", plural=False),
}

TOOLS = {
    "lantern": Tool(id="lantern", label="a lantern helmet", prep="put on a lantern helmet first", tail="slid the lantern helmet on", protects={"dark"}),
    "boots": Tool(id="boots", label="moon boots", prep="strap on moon boots first", tail="buckled the moon boots", protects={"slippery"}),
    "cloak": Tool(id="cloak", label="a sparkle cloak", prep="wear a sparkle cloak first", tail="draped the sparkle cloak around them", protects={"dust", "bright"}),
}

NAMES = ["Ari", "Mina", "Toby", "Luna", "Nova", "Pip", "Rin", "Juno"]
TYPES = {"girl": ["Ari", "Mina", "Luna", "Nova", "Juno"], "boy": ["Toby", "Pip", "Rin"]}
TRAITS = ["curious", "brave", "bouncy", "gentle", "bold"]


@dataclass
class StoryParams:
    setting: str
    mission: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def mission_needs_spire(m: Mission, setting: Setting) -> bool:
    return m.id == "spire" and setting.has_spire


def compatible_tool(m: Mission, prize: Prize) -> Optional[Tool]:
    if prize.location == "shirt" and m.id in {"spire", "beacon"}:
        return TOOLS["cloak"]
    if prize.location == "hand" and m.id in {"spire", "comet"}:
        return TOOLS["lantern"]
    if prize.location == "pocket":
        return TOOLS["boots"]
    return None


def predict(world: World, actor: Entity, mission: Mission, prize_id: str) -> dict:
    sim = world.copy()
    do_mission(sim, sim.get(actor.id), mission, narrate=False)
    prize = sim.get(prize_id)
    return {"scared": prize.meters.get("shaken", 0) >= THRESHOLD, "noise": actor.meters.get("noise", 0)}


def do_mission(world: World, actor: Entity, mission: Mission, narrate: bool = True) -> None:
    actor.meters["noise"] = actor.meters.get("noise", 0) + 1
    actor.memes["wonder"] = actor.memes.get("wonder", 0) + 1
    world.facts["mission_done"] = mission.id
    propagate(world, narrate=narrate)


def tell(setting: Setting, mission: Mission, prize_cfg: Prize, name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, location=setting.name))
    parent = world.add(Entity(id="Guide", kind="character", type="mother", label="the guide"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, location=prize_cfg.location))
    tool_def = compatible_tool(mission, prize_cfg)
    if not tool_def:
        raise StoryError("No reasonable tool can support this space adventure.")
    tool = world.add(Entity(id=tool_def.id, type="thing", label=tool_def.label, owner=hero.id, carried_by=hero.id, plural=tool_def.plural))

    world.facts.update(hero=hero, parent=parent, prize=prize, mission=mission, tool=tool, tool_def=tool_def)
    world.facts["spire_seen"] = setting.has_spire and mission.id == "spire"

    world.say(f"{name} was a {trait} young {gender} at {setting.name}, where a tall spire watched the sky.")
    world.say(f"{name} loved {mission.gerund}; {mission.foreshadow}")
    world.say(f"One day, the guide gave {hero.pronoun('object')} {prize.phrase}, and {hero.id} smiled at once.")
    world.para()
    world.say(f"The path led {mission.path} under a {setting.sky} sky.")
    world.say(f"{mission.rhyme} {mission.surprise}")
    world.say(f"{name} wanted to {mission.verb}, but the {prize.label} could get shaken on the climb.")
    world.say(f'"You may {mission.verb}, but let us be careful," the guide said.')
    world.say(f"So they {tool_def.prep} and stepped on together.")
    do_mission(world, hero, mission)
    world.para()
    world.say(f"The spire glowed ahead, and {name} kept going with steady feet.")
    world.say(f"They {tool_def.tail}, then {mission.gerund} all the way to the top.")
    world.say(f"{mission.surprise} At the end, {name} held the {prize.label} safely and laughed with the guide.")
    world.say(f"The little space rhyme had come true: high and bright, they made it right.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mission = f["mission"]
    prize = f["prize"]
    return [
        f"Write a short space adventure for a child named {hero.id} who wants to {mission.verb}.",
        f"Tell a gentle story with foreshadowing, surprise, and rhyme about a {prize.label} and a tall spire.",
        f"Create a tiny space mission story where a guide warns that {prize.phrase} could be shaken during the trip.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, mission, prize, tool = f["hero"], f["parent"], f["mission"], f["prize"], f["tool"]
    return [
        QAItem(
            question=f"Who went to the spire in the story?",
            answer=f"{hero.id} went with the guide to the spire and stayed careful with the {prize.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {mission.verb}, and that became the big space adventure.",
        ),
        QAItem(
            question=f"How did they keep the {prize.label} safe?",
            answer=f"They used {tool.label} first, so {prize.phrase} stayed safe during the climb.",
        ),
        QAItem(
            question=f"What surprise happened at the top?",
            answer=f"The story surprised them with the line: {mission.surprise}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spire?",
            answer="A spire is a tall, narrow tower that points up toward the sky.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a little clue early on about something that may matter later.",
        ),
        QAItem(
            question="Why do stories use rhyme?",
            answer="Rhyme makes words sound playful and helps a story feel musical and fun.",
        ),
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
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.has_spire:
            lines.append(asp.fact("has_spire", sid))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("at", pid, p.location))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(t.protects):
            lines.append(asp.fact("protects", tid, p))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,M,P) :- setting(S), mission(M), prize(P), has_spire(S), M = spire.
compatible_tool(M,P,T) :- mission(M), prize(P), tool(T), at(P, shirt), protects(T, bright), M = spire.
compatible_tool(M,P,T) :- mission(M), prize(P), tool(T), at(P, pocket), M = spire.
compatible_tool(M,P,T) :- mission(M), prize(P), tool(T), at(P, hand), M = comet.
safe_combo(S,M,P) :- valid_story(S,M,P), compatible_tool(M,P,_).
#show valid_story/3.
#show safe_combo/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for mid, m in MISSIONS.items():
            for pid in PRIZES:
                if s.has_spire and mid == "spire":
                    out.append((sid, mid, pid))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(a - b))
    print(" only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with a spire, surprise, foreshadowing, and rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    mission = args.mission or "spire"
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice(TYPES[gender])
    if mission != "spire" and not SETTINGS[setting].has_spire:
        raise StoryError("This story needs a spire in the setting.")
    return StoryParams(setting=setting, mission=mission, prize=prize, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MISSIONS[params.mission], PRIZES[params.prize], params.name, params.gender, params.trait)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/3."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for sid in SETTINGS:
            for mid in MISSIONS:
                for pid in PRIZES:
                    if sid in SETTINGS and MISSIONS[mid].id == "spire":
                        samples.append(generate(StoryParams(setting=sid, mission=mid, prize=pid, name="Nova", gender="girl", trait="curious")))
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
