#!/usr/bin/env python3
"""
storyworlds/worlds/power_ful_surprise_space_adventure.py
========================================================

A standalone story world for a small Space Adventure tale with a surprise,
a power-ful helper, and a child-friendly turn from caution to wonder.

Premise:
- A young space explorer wants to rush into a surprise mission.
- A careful grown-up notices the ship's power is low.
- A small power-ful gadget can solve the problem without breaking the rules.

The world is intentionally tiny: one surprise, one risk, one compatible fix.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"bright": 0.0, "low_power": 0.0, "broken": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "surprise": 0.0, "conflict": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    surprise: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False
    power_ful: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.mission_zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone.mission_zone = set(self.mission_zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_battery(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["low_power"] < THRESHOLD:
            continue
        sig = ("battery", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append(f"{e.id} felt the ship grow dim and a little worrisome.")
    return out


def _r_tool(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["low_power"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if not item.protective:
                continue
            if not (item.covers & world.mission_zone):
                continue
            sig = ("tool", item.id, actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["joy"] += 1
            out.append(f"{actor.id} had the right tool ready.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_battery, _r_tool):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_problem(world: World, actor: Entity, mission: Mission, gadget_id: str) -> dict:
    sim = world.copy()
    _do_mission(sim, sim.get(actor.id), mission, narrate=False)
    gadget = sim.entities.get(gadget_id)
    return {
        "dim": bool(gadget and gadget.meters["low_power"] >= THRESHOLD),
        "joy": sum(e.memes["joy"] for e in sim.characters()),
    }


def _do_mission(world: World, actor: Entity, mission: Mission, narrate: bool = True) -> None:
    world.mission_zone = set(mission.zone)
    actor.meters["low_power"] += 1
    actor.memes["surprise"] += 1
    propagate(world, narrate=narrate)


def mission_risk(mission: Mission, gadget: Tool) -> bool:
    return bool(mission.zone & gadget.covers)


def choose_tool(mission: Mission, gadget: Tool) -> Optional[Tool]:
    if mission.risk in gadget.guards and mission.zone & gadget.covers:
        return gadget
    return None


def tell(setting: Setting, mission: Mission, gadget_cfg: Tool, hero_name: str,
         hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            traits=["little", "curious", "brave"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the captain"))
    gadget = world.add(Entity(
        id=gadget_cfg.id,
        type="tool",
        label=gadget_cfg.label,
        phrase=gadget_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gadget_cfg.covers),
        plural=gadget_cfg.plural,
    ))
    gadget.worn_by = hero.id

    world.say(f"{hero.id} was a little space explorer who loved surprises in the stars.")
    world.say(f"{hero.pronoun().capitalize()} liked {mission.gerund}, because {mission.surprise}.")
    world.say(f"One day, {hero.id}'s {parent.label_word} showed {hero.pronoun('object')} {gadget.phrase}.")
    world.say(f"{hero.id} thought the {gadget.label} looked power-ful and shiny.")

    world.para()
    world.say(f"Then they went to {world.setting.place}.")
    world.say(f"{hero.id} wanted to {mission.verb}, but {hero.pronoun('possessive')} {parent.label_word} paused first.")
    if predict_problem(world, hero, mission, gadget.id)["dim"]:
        world.say(f'"If we rush in now, the ship will feel {mission.risk}," {hero.pronoun("possessive")} {parent.label_word} said.')
    world.say(f"{hero.id} tried to {mission.rush}, and the lights flickered.")

    world.para()
    hero.meters["low_power"] += 1
    if mission_risk(mission, gadget_cfg):
        world.say(f"{hero.id} frowned, but then {hero.pronoun('possessive')} {parent.label_word} smiled.")
        if choose_tool(mission, gadget_cfg):
            hero.memes["joy"] += 1
            hero.memes["conflict"] = 0
            world.say(f'"How about we use the {gadget.label} for the job first?" {hero.pronoun("possessive")} {parent.label_word} asked.')
            world.say(f"{hero.id} nodded, and together they followed the plan.")
            world.say(f"Soon the {gadget.label} gave the little ship a bright boost, and {hero.id} could {mission.gerund} safely.")
            world.say(f"At the end, the surprise was still there, only now it was a happy, glowing surprise.")
        else:
            raise StoryError("No reasonable tool can solve this mission safely.")
    else:
        raise StoryError("The chosen mission and tool do not match this storyworld.")

    world.facts.update(hero=hero, parent=parent, gadget=gadget, mission=mission, setting=setting, resolved=True)
    return world


SETTINGS = {
    "starport": Setting(place="the starport deck", affords={"beacon", "cargo"}),
    "moonbase": Setting(place="the moonbase hallway", affords={"beacon"}),
    "observatory": Setting(place="the observatory dock", affords={"cargo", "beacon"}),
}

MISSIONS = {
    "beacon": Mission(
        id="beacon",
        verb="switch on the surprise beacon",
        gerund="checking surprise beacons",
        rush="dash to the control panel",
        risk="low-power",
        zone={"head", "torso"},
        surprise="a hidden message was waiting inside",
        keyword="surprise",
        tags={"surprise", "light"},
    ),
    "cargo": Mission(
        id="cargo",
        verb="open the surprise cargo pod",
        gerund="opening surprise cargo pods",
        rush="pull the hatch wide open",
        risk="low-power",
        zone={"torso"},
        surprise="a tiny helper might be tucked inside",
        keyword="cargo",
        tags={"surprise", "helper"},
    ),
}

TOOLS = {
    "starcell": Tool(
        id="starcell",
        label="a star cell",
        phrase="a power-ful star cell",
        guards={"low-power"},
        covers={"head", "torso"},
        prep="plug in the star cell first",
        tail="plugged in the star cell",
        power_ful=True,
    ),
    "glowpack": Tool(
        id="glowpack",
        label="a glow pack",
        phrase="a small power-ful glow pack",
        guards={"low-power"},
        covers={"torso"},
        prep="turn on the glow pack first",
        tail="turned on the glow pack",
        power_ful=True,
    ),
}

HERO_NAMES = ["Luna", "Milo", "Nova", "Arlo", "Iris", "Kai"]
TRAITS = ["brave", "curious", "cheerful", "lively"]


@dataclass
class StoryParams:
    place: str
    mission: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid in setting.affords:
            mission = MISSIONS[mid]
            for tid, tool in TOOLS.items():
                if mission_risk(mission, tool) and choose_tool(mission, tool):
                    combos.append((place, mid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with a surprise and a power-ful fix.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.mission and args.tool:
        m, t = MISSIONS[args.mission], TOOLS[args.tool]
        if not (mission_risk(m, t) and choose_tool(m, t)):
            raise StoryError("That mission and tool do not form a safe surprise-space story.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mission is None or c[1] == args.mission)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, mission, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, mission=mission, tool=tool, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, mission, gadget = f["hero"], f["parent"], f["mission"], f["gadget"]
    return [
        f'Write a short space adventure story for a child about a surprise and a {gadget.phrase}.',
        f"Tell a gentle story where {hero.id} wants to {mission.verb} but {hero.pronoun('possessive')} {parent.label_word} worries about the ship's power.",
        f'Write a simple story with the word "power-ful" and end with a happy surprise in space.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, mission, gadget = f["hero"], f["parent"], f["mission"], f["gadget"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {mission.verb}, and the day felt like a surprise mission in space.",
        ),
        QAItem(
            question=f"Why did {hero.id}'s {parent.label_word} pause before the mission?",
            answer=f"{parent.label_word.capitalize()} paused because the ship's power was low and the surprise could have gone wrong.",
        ),
        QAItem(
            question=f"What helped the child do the mission safely?",
            answer=f"{gadget.phrase} helped because it was power-ful and gave the ship enough bright energy.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {parent.label_word} enjoying the surprise after the ship got its power boost.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a star cell for?",
            answer="A star cell gives a ship or gadget energy so lights and machines can work.",
        ),
        QAItem(
            question="What does surprise mean in a story?",
            answer="A surprise is something unexpected that makes a story exciting or special.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="starport", mission="beacon", tool="starcell", name="Nova", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="moonbase", mission="beacon", tool="glowpack", name="Kai", gender="boy", parent="father", trait="brave"),
    StoryParams(place="observatory", mission="cargo", tool="starcell", name="Luna", gender="girl", parent="mother", trait="cheerful"),
]


ASP_RULES = r"""
mission_risk(M,T) :- mission(M), tool(T), risk_mission(M,R), guards(T,R), covers(T,C), zone(M,Z), overlap(Z,C).
safe_combo(P,M,T) :- place(P), affords(P,M), mission_risk(M,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for m in sorted(s.affords):
            lines.append(asp.fact("affords", pid, m))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("risk_mission", mid, m.risk.replace("-", "_")))
        for z in sorted(m.zone):
            lines.append(asp.fact("zone", mid, z))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", tid, g.replace("-", "_")))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", tid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_stories() -> list[tuple]:
    return [(p, m, t) for (p, m, t) in valid_combos()]


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(valid_stories())
    if py == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MISSIONS[params.mission], TOOLS[params.tool],
                 params.name, params.gender, params.parent)
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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show safe_combo/3."))
        return
    if args.asp:
        triples = valid_stories()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mission} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
