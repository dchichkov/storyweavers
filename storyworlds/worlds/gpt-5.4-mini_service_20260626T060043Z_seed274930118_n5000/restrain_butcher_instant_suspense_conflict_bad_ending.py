#!/usr/bin/env python3
"""
storyworlds/worlds/restrain_butcher_instant_suspense_conflict_bad_ending.py
============================================================================

A small space-adventure storyworld about a crew under pressure, where a fast
decision can either restrain a danger in time or end in a bad, suspenseful
failure.

Seed tale:
---
A tiny scout crew flies through a quiet stretch of space.
When a butcher-bot aboard the ship starts carving up the emergency supplies,
the captain must restrain it instantly before the mission fails.
But the warning comes too late, the conflict grows, and the ending turns bad.

World idea:
- A crew member or helper is carrying a risky tool or machine.
- The machine's job is useful, but under stress it can butcher the wrong thing.
- The captain can restrain it with a tether or clamp.
- If restraint is delayed, the supplies are ruined and the crew ends stranded.

This world is intentionally narrow: a few plausible combinations, strong causal
state changes, and a complete story beat with suspense, conflict, and a bad end.
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    danger: str
    effect: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _do_mission(world: World, actor: Entity, mission: Mission, narrate: bool = True) -> None:
    if mission.id not in world.setting.affords:
        raise StoryError(f"(No story: {world.setting.place} cannot support {mission.id}.)")
    world.zone = set(mission.zone)
    actor.meters[mission.id] = actor.meters.get(mission.id, 0) + 1
    actor.memes["pressure"] = actor.memes.get("pressure", 0) + 1
    if narrate:
        world.say(f"{actor.id} moved at once, and the ship filled with suspense.")


def _r_butcher(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("butcher", 0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.kind == "thing" and item.worn_by == actor.id:
                if item.id == "supplies" and "hands" in world.zone:
                    sig = ("butcher", item.id)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.meters["ruined"] = item.meters.get("ruined", 0) + 1
                    actor.memes["conflict"] = actor.memes.get("conflict", 0) + 1
                    out.append("The butcher-bot cut the emergency supplies into useless pieces.")
    return out


def _r_restraint(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("restrain", 0) < THRESHOLD:
            continue
        sig = ("restrained", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["calm"] = actor.memes.get("calm", 0) + 1
        out.append("The crew managed to hold the machine still.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_butcher, _r_restraint):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_damage(world: World, actor: Entity, mission: Mission, prize_id: str) -> dict:
    sim = world.copy()
    _do_mission(sim, sim.get(actor.id), mission, narrate=False)
    prize = sim.get(prize_id)
    propagate(sim, narrate=False)
    return {
        "ruined": prize.meters.get("ruined", 0) >= THRESHOLD,
        "pressure": sum(e.memes.get("pressure", 0) for e in sim.characters()),
    }


SETTINGS = {
    "scoutship": Setting(place="the scout ship", affords={"butcher", "restrain"}),
    "corridor": Setting(place="the narrow corridor", affords={"butcher", "restrain"}),
    "cargo_bay": Setting(place="the cargo bay", affords={"butcher", "restrain"}),
}

MISSIONS = {
    "butcher": Mission(
        id="butcher",
        verb="butcher the supplies",
        gerund="butchering the supplies",
        danger="sharp sparks",
        effect="ruined",
        zone={"hands"},
        keyword="butcher",
        tags={"butcher", "suspense"},
    ),
    "restrain": Mission(
        id="restrain",
        verb="restrain the butcher-bot",
        gerund="restraining the butcher-bot",
        danger="a sudden lunge",
        effect="held still",
        zone={"arms", "hands"},
        keyword="restrain",
        tags={"restrain", "suspense"},
    ),
    "instant": Mission(
        id="instant",
        verb="act instantly",
        gerund="acting instantly",
        danger="no time at all",
        effect="before the damage spread",
        zone={"hands", "arms"},
        keyword="instant",
        tags={"instant", "conflict"},
    ),
}

PRIZES = {
    "rations": Prize(label="rations", phrase="the emergency rations", region="hands", plural=True),
    "map": Prize(label="map", phrase="the star map", region="hands"),
    "scanner": Prize(label="scanner", phrase="the ship scanner", region="hands"),
}

GEAR = [
    Gear(
        id="clamp",
        label="a metal clamp",
        covers={"hands", "arms"},
        guards={"butcher"},
        prep="throw a metal clamp around the bot",
        tail="snapped the clamp shut and held on",
    ),
    Gear(
        id="tether",
        label="a restraint tether",
        covers={"hands", "arms"},
        guards={"butcher"},
        prep="wrap a restraint tether around the bot",
        tail="yanked the tether tight until the machine stopped",
    ),
]


@dataclass
class StoryParams:
    place: str
    mission: str
    prize: str
    name: str
    captain: str
    seed: Optional[int] = None


NAMES = ["Nova", "Iris", "Milo", "Zane", "Kira", "Juno"]
CAPTAIN_TYPES = ["captain"]


def reasonableness_gate(place: str, mission: str, prize: str) -> bool:
    return mission in {"butcher", "restrain", "instant"} and prize in PRIZES and place in SETTINGS


def select_gear(mission: Mission, prize: Prize) -> Optional[Gear]:
    if prize.region not in {"hands", "arms"}:
        return None
    for gear in GEAR:
        if mission.id == "butcher" and "butcher" in gear.guards:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for mission in MISSIONS:
            for prize in PRIZES:
                if reasonableness_gate(place, mission, prize) and select_gear(MISSIONS[mission], PRIZES[prize]):
                    out.append((place, mission, prize))
    return out


def tell(setting: Setting, mission: Mission, prize_cfg: Prize, hero_name: str, captain_type: str) -> World:
    world = World(setting)
    captain = world.add(Entity(id=hero_name, kind="character", type=captain_type, label=hero_name))
    bot = world.add(Entity(id="butcher-bot", kind="character", type="thing", label="the butcher-bot"))
    prize = world.add(Entity(id="supplies", type=prize_cfg.label, label=prize_cfg.label, phrase=prize_cfg.phrase, caretaker=captain.id))
    prize.worn_by = bot.id

    world.say(f"{hero_name} was the captain of a tiny scout ship drifting past a silent star.")
    world.say(f"Inside the ship, {bot.label} began to butcher the emergency supplies.")
    world.say(f"{hero_name} felt the suspense at once, because the ship needed those supplies to go home.")

    world.para()
    world.say(f"{hero_name} saw the danger and tried to restrain the machine {mission.keyword} and fast.")
    captain.meters["restrain"] = captain.meters.get("restrain", 0) + 1
    if mission.id == "instant":
        captain.meters["instant"] = captain.meters.get("instant", 0) + 1
        world.say("It had to happen in an instant, before the sharp arm could cut again.")
    else:
        world.say(f"The captain reached for the controls, but the {mission.danger} made the moment tense.")
    if mission.id == "butcher":
        captain.meters["butcher"] = captain.meters.get("butcher", 0) + 1
    propagate(world, narrate=True)

    world.para()
    if prize.meters.get("ruined", 0) >= THRESHOLD:
        world.say(f"The attempt came too late. The {prize.label} were ruined, and the crew grew quiet.")
        world.say(f"{hero_name} stared at the broken rations while the ship drifted on with almost no hope left.")
        captain.memes["bad_ending"] = captain.memes.get("bad_ending", 0) + 1
    else:
        world.say(f"The clamp held, and the captain saved the supplies.")
        world.say(f"{hero_name} breathed out, and the little ship kept flying with a safer plan.")
    world.facts.update(
        hero=captain,
        bot=bot,
        prize=prize,
        mission=mission,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a suspenseful space adventure story about {f['hero'].id} and a butcher-bot on {f['setting'].place}.",
        f"Tell a short story where the captain must restrain a machine instantly before the emergency supplies are ruined.",
        f"Create a child-friendly space tale with conflict, suspense, and a bad ending if the rescue comes too late.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    mission = f["mission"]
    return [
        QAItem(
            question=f"Who was trying to stop the butcher-bot?",
            answer=f"{hero.id} was trying to stop it, because {hero.id} was the captain on the ship.",
        ),
        QAItem(
            question=f"What did the butcher-bot ruin?",
            answer=f"It ruined the {prize.label}, which were the emergency supplies the crew needed.",
        ),
        QAItem(
            question=f"Why was the story full of suspense?",
            answer=f"It was full of suspense because the captain had to {mission.verb} before the damage spread.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a restraint for?",
            answer="A restraint is used to hold something still when it needs to stop moving.",
        ),
        QAItem(
            question="Why is a butcher-bot dangerous on a ship?",
            answer="A butcher-bot is dangerous because it can cut the wrong thing if nobody stops it.",
        ),
        QAItem(
            question="What does instantly mean?",
            answer="Instantly means right away, with no delay at all.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("danger", mid, m.danger))
    for prid, pr in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("on_region", prid, pr.region))
    for gid, g in enumerate(GEAR):
        lines.append(asp.fact("gear", g.id))
        for gk in g.guards:
            lines.append(asp.fact("guards", g.id, gk))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,M,R) :- place(P), mission(M), prize(R), prize_at_risk(M,R), has_gear(M,R).
prize_at_risk(M,R) :- mission(M), on_region(R, hands), M = butcher.
has_gear(M,R) :- gear(G), guards(G, M), prize_at_risk(M,R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


CURATED = [
    StoryParams(place="scoutship", mission="restrain", prize="rations", name="Nova", captain="captain"),
    StoryParams(place="cargo_bay", mission="butcher", prize="map", name="Kira", captain="captain"),
    StoryParams(place="corridor", mission="instant", prize="scanner", name="Iris", captain="captain"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld with suspense, conflict, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--captain", choices=CAPTAIN_TYPES)
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
              and (args.mission is None or c[1] == args.mission)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mission, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    captain = args.captain or "captain"
    return StoryParams(place=place, mission=mission, prize=prize, name=name, captain=captain)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MISSIONS[params.mission], PRIZES[params.prize], params.name, params.captain)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combinations:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            params.seed = seed
            sample.params = params
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
