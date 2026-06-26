#!/usr/bin/env python3
"""
storyworlds/worlds/scale_bad_ending_bravery_space_adventure.py
==============================================================

A small space-adventure story world about scale, bravery, and a bad ending.

Seed tale:
---
A brave young astronaut wants to rescue a tiny beacon from a huge alien ruin.
A cautious captain warns that the ruin is much bigger than it looks, and that
the tunnel inside is too narrow for their ship. The astronaut still tries to
push forward. The ship scrapes the walls, the rescue goes wrong, and the beacon
stays lost deep inside the ruin. The child leaves with courage intact, but the
mission ends badly.

World model:
- physical meters: distance, damage, pressure, glow, drift
- emotional memes: bravery, worry, relief, sadness, pride
- the "scale" tension comes from size mismatch between ship, passage, and target
- the ending is intentionally bad: bravery matters, but it is not enough

The story samples are complete, state-driven, and child-facing.
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
    kind: str = "thing"  # "character" | "ship" | "place" | "object"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    scale: str
    danger: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    warning: str
    consequence: str
    site_tag: str
    scale_mismatch: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    size: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mission: str
    prize: str
    name: str
    role: str
    guide: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "orbital_hall": Setting(place="the orbital hall", scale="huge", danger="tight walls", afford={"crawl", "dock"}),
    "moon_cave": Setting(place="the moon cave", scale="deep", danger="sharp rocks", afford={"crawl", "shine"}),
    "asteroid_rim": Setting(place="the asteroid rim", scale="wide", danger="fast drift", afford={"fly", "dock"}),
}

MISSIONS = {
    "crawl": Mission(
        id="crawl",
        verb="crawl into the tiny tunnel",
        gerund="crawling into the tiny tunnel",
        rush="push toward the tunnel entrance",
        warning="the tunnel was too small for the ship",
        consequence="the hull scraped the rock",
        site_tag="tunnel",
        scale_mismatch="too small",
        tags={"scale", "cave"},
    ),
    "fly": Mission(
        id="fly",
        verb="fly through the giant ring",
        gerund="flying through the giant ring",
        rush="race toward the bright ring",
        warning="the ring was too big and too far away",
        consequence="the ship drifted off course",
        site_tag="ring",
        scale_mismatch="too big",
        tags={"scale", "space"},
    ),
    "dock": Mission(
        id="dock",
        verb="dock at the narrow bay",
        gerund="docking at the narrow bay",
        rush="swerve toward the bay",
        warning="the bay was much narrower than it looked",
        consequence="the ship bumped the edge",
        site_tag="bay",
        scale_mismatch="too narrow",
        tags={"scale", "dock"},
    ),
}

PRIZES = {
    "beacon": Prize(
        label="beacon",
        phrase="a tiny silver beacon",
        type="beacon",
        size="tiny",
        tags={"glow", "scale"},
    ),
    "map": Prize(
        label="star map",
        phrase="a folded star map",
        type="map",
        size="small",
        tags={"paper", "scale"},
    ),
    "key": Prize(
        label="key",
        phrase="a little brass key",
        type="key",
        size="small",
        tags={"metal", "scale"},
    ),
}

ROLES = ["pilot", "cadet", "engineer"]
TRAITS = ["brave", "curious", "bold", "steady"]
NAMES = ["Ari", "Mina", "Tess", "Jax", "Pip", "Nova", "Kai", "Luna"]


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting_ok(S,M,P) :- setting(S), mission(M), prize(P), afford(S,M), risky(M,P).
risky(crawl, beacon).
risky(crawl, map).
risky(fly, beacon).
risky(dock, key).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for m in sorted(s.afford):
            lines.append(asp.fact("afford", sid, m))
    for mid in MISSIONS:
        lines.append(asp.fact("mission", mid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting_ok/3."))
    return sorted(set(asp.atoms(model, "setting_ok")))


# ---------------------------------------------------------------------------
# Logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for mid in s.afford:
            for pid in PRIZES:
                if (mid, pid) in {("crawl", "beacon"), ("crawl", "map"), ("fly", "beacon"), ("dock", "key")}:
                    out.append((sid, mid, pid))
    return out


def is_reasonable(setting: Setting, mission: Mission, prize: Prize) -> bool:
    if mission.id == "crawl" and prize.label == "star map":
        return True
    if mission.id == "crawl" and prize.label == "beacon":
        return True
    if mission.id == "fly" and prize.label == "beacon":
        return True
    if mission.id == "dock" and prize.label == "key":
        return True
    return False


def explain_rejection(mission: Mission, prize: Prize) -> str:
    return (
        f"(No story: {mission.verb} does not make a believable scale problem "
        f"for {prize.phrase}. The warning would not matter.)"
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with a scale problem and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--guide", choices=["captain", "friend"])
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
    if args.mission and args.prize:
        if not is_reasonable(MISSIONS[args.mission], PRIZES[args.prize]):
            raise StoryError(explain_rejection(MISSIONS[args.mission], PRIZES[args.prize]))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mission is None or c[1] == args.mission)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, mission, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    guide = args.guide or "captain"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mission=mission, prize=prize, name=name, role=role, guide=guide, trait=trait)


def _say_intro(world: World, hero: Entity, guide: Entity, prize: Entity, mission: Mission) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', 'brave')} {hero.type} who loved space and wanted to find {prize.phrase}."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {guide.label} warned that {mission.warning}."
    )


def generate_story(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.name, kind="character", type=params.role, memes={"bravery": 1.0, "trait": params.trait}))
    guide = world.add(Entity(id="Guide", kind="character", type=params.guide, label=f"the {params.guide}", memes={"worry": 1.0}))
    ship = world.add(Entity(id="Ship", kind="ship", type="ship", label="the little ship", meters={"damage": 0.0, "drift": 0.0}))
    prize = world.add(Entity(id="Prize", kind="object", type=params.prize, label=params.prize, phrase=PRIZES[params.prize].phrase, owner=hero.id, location=world.setting.place, meters={"glow": 1.0}))
    mission = MISSIONS[params.mission]

    world.facts.update(hero=hero, guide=guide, ship=ship, prize=prize, mission=mission, setting=world.setting)

    _say_intro(world, hero, guide, prize, mission)
    world.para()
    world.say(
        f"One day at {world.setting.place}, {hero.id} saw the {prize.label} light up near a {mission.site_tag}."
    )
    world.say(
        f"{hero.id} felt brave and rushed to {mission.verb}."
    )
    world.say(
        f"{guide.pronoun('subject').capitalize()} called out that {mission.warning}."
    )

    # state change: bravery rises, caution ignored, damage occurs
    hero.memes["bravery"] += 1.0
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - 0.5)
    ship.meters["damage"] += 1.0
    ship.meters["drift"] += 1.0
    prize.meters["glow"] += 0.5
    world.para()
    world.say(
        f"But {hero.id} kept going because {hero.pronoun('subject')} wanted to be the bravest one on the ship."
    )
    world.say(
        f"Then {mission.consequence}, and the ship got a dent."
    )

    # bad ending
    world.para()
    hero.memes["sadness"] = 1.0
    guide.memes["sadness"] = 0.5
    prize.location = "deep inside the ruin"
    prize.meters["glow"] += 0.5
    world.say(
        f"{hero.id} stopped at the broken opening and listened to the tiny beacon still blinking far away."
    )
    world.say(
        f"The rescue was over, and the {prize.label} stayed lost inside the dark place."
    )
    world.say(
        f"{hero.id} was still brave, but the day ended with a dented ship and an empty hand."
    )

    return world


def story_text(world: World) -> str:
    return world.render()


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    generate_story(world, params)
    return StorySample(
        params=params,
        story=story_text(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure for a young child about bravery and scale that includes the word "scale".',
        f"Tell a story where {f['hero'].id} is brave, but {f['guide'].label} warns that {f['mission'].warning}.",
        f"Write a simple adventure story set at {f['setting'].place} where a small rescue ends badly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    prize: Entity = f["prize"]
    mission: Mission = f["mission"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"Who was the story about at {setting.place}?",
            answer=f"It was about {hero.id}, a {hero.memes['trait']} {hero.type} who wanted to rescue {prize.phrase}.",
        ),
        QAItem(
            question=f"What did {guide.label} warn about?",
            answer=f"{guide.label.capitalize()} warned that {mission.warning}.",
        ),
        QAItem(
            question=f"Why did the mission go badly?",
            answer=f"It went badly because {hero.id} pushed ahead anyway, so {mission.consequence} and the rescue failed.",
        ),
        QAItem(
            question=f"What was the ending image?",
            answer=f"The ending showed a dented ship, a blinking {prize.label} far away, and {hero.id} standing brave but sad.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does brave mean?",
            answer="Brave means you keep going even when something feels scary.",
        ),
        QAItem(
            question="What is scale?",
            answer="Scale is how big or small something is compared with something else.",
        ),
        QAItem(
            question="What is a rescue mission?",
            answer="A rescue mission is when someone tries to help or save something that is in trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verification / listing
# ---------------------------------------------------------------------------
def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting_ok/3."))
    return sorted(set(asp.atoms(model, "setting_ok")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python combos:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="moon_cave", mission="crawl", prize="beacon", name="Mina", role="cadet", guide="captain", trait="brave"),
    StoryParams(place="orbital_hall", mission="dock", prize="key", name="Jax", role="pilot", guide="captain", trait="bold"),
    StoryParams(place="asteroid_rim", mission="fly", prize="beacon", name="Nova", role="engineer", guide="friend", trait="curious"),
]


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
        print(asp_program("#show setting_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible (setting, mission, prize) combos:\n")
        for s, m, p in triples:
            print(f"  {s:15} {m:8} {p}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mission} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
