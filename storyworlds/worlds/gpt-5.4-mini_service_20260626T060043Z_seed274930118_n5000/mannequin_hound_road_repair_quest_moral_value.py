#!/usr/bin/env python3
"""
storyworlds/worlds/mannequin_hound_road_repair_quest_moral_value.py
====================================================================

A small standalone storyworld about a road-repair quest with a mannequin and
a hound, told in a child-facing, space-adventure style.

Premise:
- A repair crew must fix a broken road.
- A mannequin and a hound travel with the crew on a quest.
- The crew faces a moral choice about whether to rush unsafe repairs or do the
  careful, honest thing.

The world model tracks:
- meters: road damage, repair progress, travel distance, hazard exposure
- memes: courage, worry, honesty, pride, trust, relief

The story is built from world state, not from a frozen paragraph template.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("damage", "repair", "distance", "risk"):
            self.meters.setdefault(k, 0.0)
        for k in ("courage", "worry", "honesty", "pride", "trust", "relief"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Road:
    name: str
    place: str = "the road repair site"
    distance_goal: int = 3
    damage_goal: int = 4
    repair_goal: int = 4
    hazard: str = "loose stones"
    view: str = "star-bright lanes and blinking work lights"


class World:
    def __init__(self, road: Road) -> None:
        self.road = road
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        w = World(self.road)
        w.entities = copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    site: str
    quest: str
    moral: str
    name: str
    hound_name: str
    seed: Optional[int] = None


SITES = {
    "moonlane": Road(
        name="Moonlane",
        place="Moonlane Avenue",
        distance_goal=3,
        damage_goal=4,
        repair_goal=4,
        hazard="loose stones",
        view="silver lights on the cracked pavement",
    ),
    "orbital": Road(
        name="Orbital Loop",
        place="the Orbital Loop",
        distance_goal=4,
        damage_goal=5,
        repair_goal=5,
        hazard="frozen grit",
        view="curving lanes under a blue sky dome",
    ),
    "harbor": Road(
        name="Harbor Belt",
        place="the Harbor Belt Road",
        distance_goal=3,
        damage_goal=4,
        repair_goal=4,
        hazard="cold puddles",
        view="bright cones and a long lane beside the water",
    ),
}

QUESTS = {
    "signal": {
        "title": "find the broken signal box",
        "verb": "find",
        "goal": "signal box",
        "route": "follow the blinking cones",
        "reward": "the road could open safely again",
        "problem": "the broken signal box kept the lane blocked",
    },
    "patch": {
        "title": "patch the cracked lane",
        "verb": "patch",
        "goal": "cracked lane",
        "route": "carry warm asphalt",
        "reward": "the tires would roll smoothly again",
        "problem": "the cracked lane swallowed small wheels",
    },
    "bridge": {
        "title": "repair the little bridge ramp",
        "verb": "repair",
        "goal": "bridge ramp",
        "route": "cross the marked detour",
        "reward": "the ramp would hold steady again",
        "problem": "the ramp wobbled when anyone stepped on it",
    },
}

MORALS = {
    "honesty": {
        "prompt": "tell the truth about the damage",
        "choice": "honest",
        "turn": "admit the lane needed more work",
        "benefit": "everyone trusted the crew more",
    },
    "care": {
        "prompt": "choose the careful fix",
        "choice": "careful",
        "turn": "slow down and mend the road properly",
        "benefit": "the repair lasted longer",
    },
    "help": {
        "prompt": "help the tired crew member",
        "choice": "kind",
        "turn": "share the load before the next stretch",
        "benefit": "the whole team felt braver",
    },
}

HERO_NAMES = ["Ava", "Milo", "Nova", "Zed", "Iris", "Toby", "Luna", "Pax"]
HOUND_NAMES = ["Comet", "Radar", "Moss", "Orbit", "Scout", "Blink"]


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    return [(site, quest, moral) for site in SITES for quest in QUESTS for moral in MORALS]


def reasonableness_gate(params: StoryParams) -> None:
    if params.site not in SITES:
        raise StoryError("Unknown repair site.")
    if params.quest not in QUESTS:
        raise StoryError("Unknown quest.")
    if params.moral not in MORALS:
        raise StoryError("Unknown moral choice.")


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    road = SITES[params.site]
    world = World(road)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.name,
        phrase=f"a small repair rider named {params.name}",
    ))
    hound = world.add(Entity(
        id=params.hound_name,
        kind="character",
        type="hound",
        label=params.hound_name,
        phrase=f"a loyal hound named {params.hound_name}",
    ))
    mannequin = world.add(Entity(
        id="mannequin",
        kind="thing",
        type="mannequin",
        label="mannequin",
        phrase="a tall mannequin with a shiny jacket and blank but brave eyes",
    ))
    roadbox = world.add(Entity(
        id="roadbox",
        kind="thing",
        type="toolbox",
        label="toolbox",
        phrase="a toolbox full of cones, tape, and patch plates",
        owner=hero.id,
    ))

    quest = QUESTS[params.quest]
    moral = MORALS[params.moral]

    # Act 1: setup.
    world.say(
        f"At {road.place}, {hero.label} and {hound.label} rode in beside a tall mannequin, "
        f"with {road.view} stretching ahead like a quiet space lane."
    )
    world.say(
        f"They had a quest to {quest['title']}, because {quest['problem']}."
    )
    world.say(
        f"{hero.label} wanted to be a hero, and {hound.label} wagged as if the whole road was a map."
    )

    # Act 2: tension.
    hero.memes["courage"] += 1
    hero.memes["worry"] += 1
    hound.memes["trust"] += 1
    mannequin.meters["distance"] += 1
    hero.meters["distance"] += 1
    hound.meters["distance"] += 1

    world.say(
        f"They set out to {quest['verb']} the problem by {quest['route']}, while the wind tossed {road.hazard} across their boots."
    )

    # Unsafe shortcut temptation.
    world.say(
        f"A fast patch would have looked shiny, but {params.name} saw one crack hiding under the dust."
    )
    hero.memes["honesty"] += 1
    hero.memes["worry"] += 1

    # The mannequin functions as a moral mirror: it cannot lie, it only stands and reminds.
    mannequin.memes["pride"] += 1
    world.say(
        f"The mannequin stood by the lane like a silent captain, reminding them that a real fix had to be true, not just bright."
    )

    # Choice resolves.
    if params.moral == "honesty":
        hero.memes["honesty"] += 2
        hero.memes["trust"] += 1
        world.say(
            f"{params.name} chose the honest way and said they should {moral['turn']}."
        )
        world.say(
            f"The crew listened, and {params.name} pointed out the hidden crack before anything was covered over."
        )
    elif params.moral == "care":
        hero.memes["courage"] += 1
        hound.memes["relief"] += 1
        world.say(
            f"{params.name} chose the careful way and decided to {moral['turn']}."
        )
        world.say(
            f"They swept the stones away, smoothed the edge, and waited for the patch to settle."
        )
    else:
        hound.memes["trust"] += 2
        world.say(
            f"{params.name} chose the kind way and stopped to {moral['turn']}."
        )
        world.say(
            f"{params.hound_name} carried a cone to the tired worker, and the team shared the load."
        )

    # Repair progress.
    road_progress = 0
    while road_progress < road.repair_goal:
        road_progress += 1
        hero.meters["repair"] += 1
        mannequin.meters["distance"] += 0.5
        hound.meters["distance"] += 0.5
        world.say(
            f"One careful pass made the road stronger, and the little team moved one step farther along the quest."
        )
        if road_progress >= 2:
            hero.memes["relief"] += 1

    world.say(
        f"At last the road shone smooth again, and the lane opened like a clear path between stars."
    )
    world.say(
        f"{params.name} smiled at the mannequin, patted {params.hound_name}, and knew the brave thing was also the right thing."
    )

    world.facts = {
        "hero": hero,
        "hound": hound,
        "mannequin": mannequin,
        "roadbox": roadbox,
        "road": road,
        "quest": quest,
        "moral": moral,
        "params": params,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    q = world.facts["quest"]
    m = world.facts["moral"]
    road = world.facts["road"]
    return [
        f"Write a short space-adventure style story about {p.name}, a mannequin, and a hound on a road-repair quest.",
        f"Tell a child-friendly story set at {road.place} where the team must {q['title']} and choose the {m['choice']} path.",
        f"Write a simple story with a mannequin and a hound, where the hero learns a moral lesson while fixing a road.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    q = world.facts["quest"]
    m = world.facts["moral"]
    road = world.facts["road"]
    hero = world.facts["hero"]
    hound = world.facts["hound"]

    return [
        QAItem(
            question=f"Where did {p.name} and {hound.label} go on their quest?",
            answer=f"They went to {road.place} to work on the road repair quest.",
        ),
        QAItem(
            question=f"What was the team trying to do at {road.place}?",
            answer=f"They were trying to {q['title']}, because {q['problem']}.",
        ),
        QAItem(
            question=f"What good choice did {p.name} make during the story?",
            answer=f"{p.name} chose the {m['choice']} way and did not rush a fake fix.",
        ),
        QAItem(
            question=f"What helped the team remember the right thing to do?",
            answer="The mannequin stood by the lane like a quiet reminder that the repair had to be real and safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="The road was repaired, the lane opened again, and the team finished with relief and pride.",
        ),
        QAItem(
            question=f"Who traveled with {p.name}?",
            answer=f"{p.name} traveled with {hound.label} the hound and a mannequin.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    road = world.facts["road"]
    return [
        QAItem(
            question="What is road repair?",
            answer="Road repair is the work of fixing cracks, holes, or broken parts so people can travel safely.",
        ),
        QAItem(
            question="Why should repairs be done carefully?",
            answer="Careful repairs last longer and keep people safer than a quick fix that hides the problem.",
        ),
        QAItem(
            question="What does a hound do well in a story like this?",
            answer="A hound can follow the path, carry energy into the scene, and help the hero keep going.",
        ),
        QAItem(
            question="What is a mannequin in a story?",
            answer="A mannequin can be a silent helper or reminder that stands still while the others learn or plan.",
        ),
        QAItem(
            question=f"What kind of place is {road.place} in this story?",
            answer="It is a repair site with cones, dust, and a broken lane that needs careful work.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
valid(S, Q, M) :- site(S), quest(Q), moral(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SITES:
        lines.append(asp.fact("site", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for m in MORALS:
        lines.append(asp.fact("moral", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" only in python:", sorted(py - asp_set))
    print(" only in asp:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A road-repair quest storyworld with a mannequin and a hound.")
    ap.add_argument("--site", choices=SITES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--name")
    ap.add_argument("--hound-name")
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
    if args.site:
        combos = [c for c in combos if c[0] == args.site]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.moral:
        combos = [c for c in combos if c[2] == args.moral]
    if not combos:
        raise StoryError("No valid story matches those options.")
    site, quest, moral = rng.choice(combos)
    name = args.name or rng.choice(HERO_NAMES)
    hound_name = args.hound_name or rng.choice(HOUND_NAMES)
    return StoryParams(site=site, quest=quest, moral=moral, name=name, hound_name=hound_name)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
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
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    curated = [
        StoryParams(site="moonlane", quest="signal", moral="honesty", name="Nova", hound_name="Comet"),
        StoryParams(site="orbital", quest="patch", moral="care", name="Ava", hound_name="Scout"),
        StoryParams(site="harbor", quest="bridge", moral="help", name="Milo", hound_name="Orbit"),
    ]

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated]
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
