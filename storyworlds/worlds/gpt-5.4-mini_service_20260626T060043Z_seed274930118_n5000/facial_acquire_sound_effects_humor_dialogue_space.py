#!/usr/bin/env python3
"""
A small space-adventure storyworld about a crew trying to acquire a strange
signal while their faces, feelings, and gear change along the way.

Premise:
- A tiny crew travels through space to acquire a floating power core.
- The core is protected by a noisy alien ruin and a playful robot helper.
- The crew must choose between reckless grabbing and a careful method.

Narrative instruments:
- Sound effects
- Humor
- Dialogue

The seed words "facial" and "acquire" are modeled as:
- facial expressions carrying emotional state in the crew
- acquiring the core as the central plot goal
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
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
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pilot", "engineer", "scientist"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    place: str
    ambience: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    ship: str
    quest: str
    prize: str
    name: str
    role: str
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        w = World(self.ship)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        return w


SHIPS = {
    "orbital": Ship(name="the orbital station", place="orbital station", ambience="bright and humming", affords={"scan", "dock"}),
    "moonbase": Ship(name="the moonbase", place="moonbase", ambience="dusty and quiet", affords={"scan", "walk"}),
    "asteroid": Ship(name="the asteroid outpost", place="asteroid outpost", ambience="tiny and echoing", affords={"scan", "repair"}),
}

QUESTS = {
    "scan": Quest(
        id="scan",
        verb="scan the drifting core",
        gerund="scanning the drifting core",
        rush="dash toward the control panel",
        sound="beep-beep",
        risk="sparkly and noisy",
        zone={"torso", "hands"},
        keyword="scan",
        tags={"sound", "space"},
    ),
    "dock": Quest(
        id="dock",
        verb="dock with the sleeping ship",
        gerund="docking with the sleeping ship",
        rush="hurry to the airlock",
        sound="clank-clank",
        risk="bumpy and loud",
        zone={"feet", "hands"},
        keyword="dock",
        tags={"sound", "space"},
    ),
    "walk": Quest(
        id="walk",
        verb="walk outside on the moon",
        gerund="walking on the moon",
        rush="step into the moon dust",
        sound="crunch-crunch",
        risk="dusty and tickly",
        zone={"feet", "legs"},
        keyword="moon",
        tags={"space"},
    ),
    "repair": Quest(
        id="repair",
        verb="repair the blinking antenna",
        gerund="repairing the blinking antenna",
        rush="grab the tool kit",
        sound="whirr-whirr",
        risk="fizzy and jumpy",
        zone={"hands", "torso"},
        keyword="repair",
        tags={"space", "humor"},
    ),
}

PRIZES = {
    "core": Prize(id="core", label="power core", phrase="a glowing power core", region="hands"),
    "visor": Prize(id="visor", label="visor", phrase="a shiny face visor", region="face"),
    "gloves": Prize(id="gloves", label="gloves", phrase="a pair of blue gloves", region="hands", plural=True),
}

GEAR = [
    Gear(id="mask", label="a bubble mask", covers={"face"}, guards={"sparkly", "dusty"}, prep="put on a bubble mask first", tail="went to get the bubble mask"),
    Gear(id="gloves", label="insulated gloves", covers={"hands"}, guards={"sparkly", "fizzy"}, prep="put on insulated gloves first", tail="grabbed the insulated gloves", plural=True),
    Gear(id="boots", label="magnetic boots", covers={"feet"}, guards={"bumpy", "dusty"}, prep="strap on magnetic boots first", tail="slid into the magnetic boots", plural=True),
    Gear(id="suit", label="an old EVA suit", covers={"face", "hands", "feet", "torso", "legs"}, guards={"sparkly", "dusty", "fizzy", "bumpy"}, prep="climb into the old EVA suit", tail="climbed into the old EVA suit"),
]

NAMES = ["Nova", "Milo", "Iris", "Pip", "Zed", "Rae", "Kita", "Juno"]
ROLES = ["captain", "pilot", "engineer", "scientist"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_id, ship in SHIPS.items():
        for q_id in ship.affords:
            q = QUESTS[q_id]
            for p_id, prize in PRIZES.items():
                if prize.region in q.zone and select_gear(q, prize):
                    out.append((s_id, q_id, p_id))
    return out


def prize_at_risk(quest: Quest, prize: Prize) -> bool:
    return prize.region in quest.zone


def select_gear(quest: Quest, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if prize.region in g.covers and any(m in g.guards for m in quest.risk.split()):
            return g
    return None


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was the {hero.role} aboard {world.ship.name}, and "
        f"{hero.pronoun('subject').capitalize()} had a very serious face whenever the sensors beeped."
    )


def set_scene(world: World, quest: Quest) -> None:
    world.say(f"{world.ship.name} was {world.ship.ambience}, and the hallway kept making a soft humming sound: {quest.sound}.")


def desire(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(
        f"{hero.pronoun('subject').capitalize()} wanted to {quest.verb}, but {hero.pronoun('possessive')} face made a tiny worried look."
    )


def warn(world: World, hero: Entity, quest: Quest, prize: Prize) -> bool:
    if not prize_at_risk(quest, prize):
        return False
    world.facts["risk"] = quest.risk
    world.say(
        f'"Careful," {hero.pronoun("possessive")} radio crackled. "That could leave your {prize.label} {quest.risk}!"'
    )
    return True


def humor(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} blinked. 'My face is already doing the brave-captain look,' {hero.pronoun('subject')} said. "
        f"'Do I get extra points for that?'"
    )


def conflict(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0) + 1
    world.say(f"{hero.pronoun('subject').capitalize()} made a determined face and went {quest.rush}, even though the warning was still ringing.")


def offer_fix(world: World, hero: Entity, quest: Quest, prize: Prize) -> Optional[Gear]:
    gear = select_gear(quest, prize)
    if gear is None:
        return None
    world.say(
        f"Then the ship's helper robot rolled in with a cheerful chirp. 'How about we {gear.prep} and try again?'"
    )
    return gear


def resolve(world: World, hero: Entity, quest: Quest, prize: Prize, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["stubborn"] = 0
    world.say(
        f"{hero.id} laughed. 'Okay,' {hero.pronoun('subject')} said. 'The suit can be the hero today.'"
    )
    world.say(
        f"With a soft {quest.sound} and a careful grin, {hero.id} {gear.tail}, {quest.gerund}, and managed to acquire {prize.phrase} without any sparks on {hero.pronoun('possessive')} {prize.label}."
    )


def tell(ship: Ship, quest: Quest, prize_cfg: Prize, name: str, role: str) -> World:
    world = World(ship)
    hero = world.add(Entity(id=name, kind="character", type=role, role=role))
    prize = world.add(Entity(id="prize", type=prize_cfg.label, label=prize_cfg.label, phrase=prize_cfg.phrase))
    helper = world.add(Entity(id="helper", kind="character", type="robot", role="helper"))

    introduce(world, hero)
    set_scene(world, quest)
    world.para()
    desire(world, hero, quest)
    if warn(world, hero, quest, prize_cfg):
        humor(world, hero, quest)
        conflict(world, hero, quest)
        gear = offer_fix(world, hero, quest, prize_cfg)
        if gear:
            resolve(world, hero, quest, prize_cfg, gear)

    world.facts.update(hero=hero, prize=prize_cfg, quest=quest, ship=ship, helper=helper, gear=gear if "gear" in locals() else None)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    prize = f["prize"]
    return [
        f'Write a short space-adventure story for young children about a {hero.role} who wants to {quest.verb} and acquire {prize.phrase}.',
        f'Tell a funny dialogue-rich story with sound effects where {hero.id} learns to use safer gear before {quest.gerund}.',
        f'Write a story in space where the words "facial" and "acquire" make sense through expressions and the goal of getting something important.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    prize = f["prize"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do on the ship?",
            answer=f"{hero.id} wanted to {quest.verb}.",
        ),
        QAItem(
            question=f"Why did the helper worry about the {prize.label}?",
            answer=f"The helper worried because {prize.phrase} could get {quest.risk}.",
        ),
        QAItem(
            question=f"What helped {hero.id} do the job safely?",
            answer=f"{gear.label if gear else 'Careful planning'} helped {hero.id} do it safely.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a visor for?", answer="A visor helps protect a person's face from bright light, dust, or sparks."),
        QAItem(question="What does acquire mean?", answer="To acquire something means to get it or obtain it."),
        QAItem(question="Why do spacesuits have helmets?", answer="Spacesuit helmets help protect a person in space where there is no air."),
        QAItem(question="What does a robot helper do?", answer="A robot helper can carry tools, give warnings, and help with tricky jobs."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(Q,P) :- zone(Q,R), region(P,R).
gear_ok(G,Q,P) :- prize_at_risk(Q,P), covers(G,R), region(P,R), guards(G,M), risk(Q,Txt), contains_word(Txt,M).
valid(Ship,Q,P) :- affords(Ship,Q), prize_at_risk(Q,P), gear_ok(_,Q,P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, ship in SHIPS.items():
        lines.append(asp.fact("ship", sid))
        for q in sorted(ship.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for z in sorted(q.zone):
            lines.append(asp.fact("zone", qid, z))
        lines.append(asp.fact("risk", qid, q.risk))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    lines.append('contains_word(Txt,M) :- Txt = Txt, M = M.')
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_asp())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld about facial expressions and acquiring a core.")
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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
    combos = valid_combos()
    combos = [c for c in combos if (args.ship is None or c[0] == args.ship) and (args.quest is None or c[1] == args.quest) and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    ship, quest, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    return StoryParams(ship=ship, quest=quest, prize=prize, name=name, role=role)


def generate(params: StoryParams) -> StorySample:
    world = tell(SHIPS[params.ship], QUESTS[params.quest], PRIZES[params.prize], params.name, params.role)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for sid, qid, pid in sorted(valid_combos()):
            params = StoryParams(ship=sid, quest=qid, prize=pid, name=random.choice(NAMES), role=random.choice(ROLES), seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
