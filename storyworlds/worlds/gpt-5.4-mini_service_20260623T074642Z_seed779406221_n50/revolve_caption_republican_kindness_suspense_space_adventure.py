#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/revolve_caption_republican_kindness_suspense_space_adventure.py
==============================================================================================================

A standalone story world in a small space-adventure domain.

Premise:
- A young space crew travels a tiny station that slowly revolves around a warm star.
- A mission caption, spoken into a recorder, matters because it guides what the crew believes they must do.
- The crew member called the republican is not a politics story; it is a ship nickname for a blue repair drone with a red-and-white hull badge.
- Kindness resolves suspense: the crew must choose whether to share oxygen, share a seat in the escape pod, and share the truth behind the caption.

This world keeps the tone close to a child-facing space adventure:
- short concrete scenes
- a tense middle
- a warm, generous ending image
- causal state updates, not a frozen paragraph with name swaps

It also includes:
- a Python reasonableness gate
- an inline ASP twin
- asp_facts() emission
- --verify parity checking
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
    wears: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    revolves: bool
    beacon: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
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
    delicate: bool = True


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    offer: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.caption: str = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.caption = self.caption
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_spark_damage(world: World) -> list[str]:
    out = []
    pilot = world.get(world.facts["hero"])
    mission = world.facts["mission"]
    prize = world.get(world.facts["prize"])
    if pilot.meters.get("spark", 0) < THRESHOLD:
        return out
    sig = ("spark_damage", prize.id)
    if sig in world.fired:
        return out
    if prize.region in world.zone:
        world.fired.add(sig)
        prize.meters["scuffed"] = prize.meters.get("scuffed", 0) + 1
        out.append(f"The {prize.label} got scuffed in the sparks.")
    return out


def _r_kindness(world: World) -> list[str]:
    out = []
    hero = world.get(world.facts["hero"])
    helper = world.get(world.facts["helper"])
    if hero.memes.get("kindness", 0) < THRESHOLD or helper.memes.get("fear", 0) < THRESHOLD:
        return out
    sig = ("kindness", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    helper.memes["calm"] = helper.memes.get("calm", 0) + 1
    out.append("Kindness made the tense room feel smaller.")
    return out


CAUSAL_RULES = [
    Rule("spark_damage", _r_spark_damage),
    Rule("kindness", _r_kindness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def setting_detail(setting: Setting, mission: Mission) -> str:
    if setting.revolves:
        return f"The station revolved slowly, and {setting.beacon} flashed past the window again and again."
    return f"{setting.place.capitalize()} stayed still, but the {setting.beacon} blinked like a tiny star."


def predict_risk(world: World, hero: Entity, mission: Mission, prize_id: str) -> bool:
    sim = world.copy()
    _do_mission(sim, sim.get(hero.id), mission, narrate=False)
    prize = sim.get(prize_id)
    return prize.meters.get("scuffed", 0) >= THRESHOLD


def _do_mission(world: World, hero: Entity, mission: Mission, narrate: bool = True) -> None:
    if mission.id not in world.setting.afford:
        raise StoryError("That place cannot host this mission.")
    world.zone = set(mission.zone)
    hero.meters["spark"] = hero.meters.get("spark", 0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a little space kid who loved counting stars, and {helper.label} was always nearby."
    )


def caption_scene(world: World, hero: Entity, mission: Mission) -> None:
    world.caption = f"CAPTION: {hero.id} will {mission.verb} before the station turns again."
    world.say(
        f"One day, a glowing recorder read out a caption: \"{hero.id} must {mission.verb}.\""
    )


def worry(world: World, helper: Entity, hero: Entity, mission: Mission, prize: Entity) -> bool:
    if not predict_risk(world, hero, mission, prize.id):
        return False
    helper.memes["fear"] = helper.memes.get("fear", 0) + 1
    world.facts["predicted"] = True
    world.say(
        f'"If you {mission.verb}, the {prize.label} will get {mission.risk}," {helper.label} warned.'
    )
    return True


def suspense(world: World, hero: Entity, helper: Entity, mission: Mission) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(
        f"{hero.id} still wanted to go, so the corridor felt quiet and suspenseful."
    )
    world.say(f"{hero.id} leaned toward the launch hatch, ready to {mission.verb}.")


def share_choice(world: World, helper: Entity, hero: Entity, mission: Mission, prize: Entity) -> Optional[Gear]:
    for gear in GEARS:
        if mission.risk in gear.guards and prize.region in gear.covers:
            return gear
    return None


def resolve(world: World, helper: Entity, hero: Entity, mission: Mission, prize: Entity) -> None:
    gear = share_choice(world, helper, hero, mission, prize)
    if gear is None:
        raise StoryError("No kind enough gear can solve this mission.")
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    hero.memes["fear"] = 0
    helper.memes["fear"] = 0
    world.say(
        f"{helper.label} smiled and offered {gear.label}. \"We can share the safe way,\" {helper.pronoun()} said."
    )
    world.say(
        f"They used it at once, and soon {hero.id} was {mission.gerund} while the {prize.label} stayed clean."
    )


def tell(setting: Setting, mission: Mission, prize_cfg: Prize, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type="robot", label="the republican"))
    prize = world.add(Entity(id="prize", type="thing", label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    world.facts.update(hero=hero.id, helper=helper.id, prize=prize.id, mission=mission, setting=setting)
    intro(world, hero, helper)
    world.para()
    caption_scene(world, hero, mission)
    world.say(setting_detail(setting, mission))
    worry(world, helper, hero, mission, prize)
    suspense(world, hero, helper, mission)
    world.para()
    resolve(world, helper, hero, mission, prize)
    world.facts["resolved"] = True
    world.facts["gear"] = next((g for g in GEARS if mission.risk in g.guards and prize.region in g.covers), None)
    return world


SETTINGS = {
    "orbit": Setting(place="the orbiting station", revolves=True, beacon="the blue beacon", afford={"revolve"}),
    "dock": Setting(place="the moon dock", revolves=False, beacon="the dock light", afford={"caption"}),
}

MISSIONS = {
    "revolve": Mission(
        id="revolve",
        verb="turn the wheel that helps the station revolve",
        gerund="turning the wheel while the station revolved",
        risk="sparks",
        zone={"hands"},
        keyword="revolve",
        tags={"space", "wheel"},
    ),
    "caption": Mission(
        id="caption",
        verb="read the captain's caption aloud",
        gerund="reading the glowing caption",
        risk="echoes",
        zone={"ears"},
        keyword="caption",
        tags={"space", "message"},
    ),
}

PRIZES = {
    "badge": Prize(id="badge", label="badge", phrase="a shiny mission badge", region="hands"),
    "glass": Prize(id="glass", label="glass globe", phrase="a glass globe", region="hands"),
}

GEARS = [
    Gear(id="gloves", label="soft gloves", covers={"hands"}, guards={"sparks"}, offer="wear soft gloves", tail="wore the soft gloves"),
    Gear(id="earmuffs", label="earmuffs", covers={"ears"}, guards={"echoes"}, offer="put on earmuffs", tail="put on the earmuffs"),
]

NAMES = ["Nova", "Tess", "Pip", "Milo", "Iris", "Juno"]


@dataclass
class StoryParams:
    place: str
    mission: str
    prize: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mission_id in setting.afford:
            mission = MISSIONS[mission_id]
            for prize_id, prize in PRIZES.items():
                if mission.risk and prize.region in mission.zone or mission.id == "caption":
                    if any(mission.risk in g.guards and prize.region in g.covers for g in GEARS):
                        combos.append((place, mission_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mission: Mission = f["mission"]
    return [
        f'Write a short space adventure story with the word "{mission.keyword}" in it.',
        f"Tell a child-friendly story where {f['hero'].id} must {mission.verb} and the republican helps with kindness.",
        f"Write a suspenseful but gentle story about a revolving station, a caption, and a safe choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.get(f["hero"])
    helper = world.get(f["helper"])
    mission: Mission = f["mission"]
    prize = world.get(f["prize"])
    return [
        QAItem(
            question=f"What was the caption asking {hero.id} to do?",
            answer=f"It asked {hero.id} to {mission.verb}.",
        ),
        QAItem(
            question=f"Why did the republican worry about the {prize.label}?",
            answer=f"Because if {hero.id} did {mission.verb}, the {prize.label} could get {mission.risk}.",
        ),
        QAItem(
            question="How did the suspense end?",
            answer=f"The republican offered help, and kindness let them do the mission safely.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does revolve mean?",
            answer="Revolve means to turn around in a circle again and again.",
        ),
        QAItem(
            question="What is a caption?",
            answer="A caption is a short line of words that explains a picture or gives a message.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means choosing to help, share, or care about someone else.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the tense feeling you get when you wonder what will happen next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(M,P) :- mission(M), prize(P), zone(M,R), region(P,R).
compatible(M,P) :- mission(M), prize(P), guards(G, MESS), covers(G,R), zone(M,R), region(P,R).
valid(Place,M,P) :- affords(Place,M), compatible(M,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.revolves:
            lines.append(asp.fact("revolves", pid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("zone", mid, "hands" if "hands" in m.zone else "ears"))
        lines.append(asp.fact("risk", mid, m.risk))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for g in GEARS:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for gd in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, gd))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - cl:
        print("only python:", sorted(py - cl))
    if cl - py:
        print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with revolve, caption, republican, kindness, and suspense.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper", default="republican")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mission is None or c[1] == args.mission)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, mission, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        mission=mission,
        prize=prize,
        hero_name=args.name or rng.choice(NAMES),
        helper_name=args.helper,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MISSIONS[params.mission], PRIZES[params.prize], params.hero_name, params.helper_name)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, mission=m, prize=z, hero_name="Nova", helper_name="republican")) for p, m, z in sorted(valid_combos())]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
