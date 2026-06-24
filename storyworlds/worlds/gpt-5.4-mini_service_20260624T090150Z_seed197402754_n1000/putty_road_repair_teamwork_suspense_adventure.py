#!/usr/bin/env python3
"""
A small storyworld about a road repair team, a stubborn crack, and a careful
putty patch done with teamwork and suspense.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str
    helper: str
    site: str
    weather: str
    seed: Optional[int] = None


@dataclass
class RoadSite:
    place: str
    hazard: str
    crack: str
    putty_color: str
    repair_tool: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Team:
    lead: str
    helper: str
    action: str
    suspense_line: str
    ending_line: str


class World:
    def __init__(self, site: RoadSite) -> None:
        self.site = site
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
        return "\n".join(lines)


ROAD_SITES = {
    "bridge": RoadSite(
        place="the bridge road",
        hazard="a deep crack near the lane line",
        crack="the crack",
        putty_color="gray putty",
        repair_tool="a steel trowel",
        tags={"road", "repair", "putty", "teamwork", "suspense", "adventure"},
    ),
    "hill": RoadSite(
        place="the hill road",
        hazard="a long split that made the path bumpy",
        crack="the split",
        putty_color="stone putty",
        repair_tool="a wide scraper",
        tags={"road", "repair", "putty", "teamwork", "suspense", "adventure"},
    ),
    "town": RoadSite(
        place="the town lane",
        hazard="a pothole with crumbling edges",
        crack="the pothole",
        putty_color="warm tan putty",
        repair_tool="a small roller",
        tags={"road", "repair", "putty", "teamwork", "suspense", "adventure"},
    ),
}

TEAM_LINES = {
    "bridge": Team(
        lead="keep the road safe before the first car rolled back",
        helper="held the flashlight steady",
        action="spreads the putty across the crack",
        suspense_line="The wind kept tugging at the tarp, and everyone watched the wet edge of the patch.",
        ending_line="Soon the repaired road looked smooth again, like the danger had never been there.",
    ),
    "hill": Team(
        lead="finish the repair before the hill traffic picked up",
        helper="carried the bucket of putty carefully",
        action="pressed the putty into the split",
        suspense_line="For a moment, a truck rumbled far away, and the team worked even faster.",
        ending_line="At last the split was filled, and the road held steady under every tire.",
    ),
    "town": Team(
        lead="mend the lane before the morning delivery vans arrived",
        helper="kept watch at the corner",
        action="smoothed the putty into the pothole",
        suspense_line="A scooter buzzed past the block, so they waited until the lane was clear.",
        ending_line="When they were done, the lane looked safe and tidy, ready for a new day.",
    ),
}

CURATED = [
    StoryParams(name="Mina", helper="Jules", site="bridge", weather="windy"),
    StoryParams(name="Theo", helper="Ari", site="hill", weather="cloudy"),
    StoryParams(name="Nina", helper="Bo", site="town", weather="cool"),
]

NAMES = ["Mina", "Theo", "Nina", "Ravi", "Elia", "Tess", "Owen", "Lina"]
HELPERS = ["Jules", "Ari", "Bo", "Pia", "Noor", "Zane", "Kai", "Mara"]
WEATHERS = ["windy", "cloudy", "bright", "cool", "rainy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Road repair storyworld with putty, teamwork, and suspense.")
    ap.add_argument("--site", choices=ROAD_SITES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--weather", choices=WEATHERS)
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
    site = args.site or rng.choice(list(ROAD_SITES))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([h for h in HELPERS if h != name])
    weather = args.weather or rng.choice(WEATHERS)
    if helper == name:
        raise StoryError("The lead and helper should be different people for teamwork to make sense.")
    return StoryParams(name=name, helper=helper, site=site, weather=weather)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, site in ROAD_SITES.items():
        lines.append(asp.fact("site", sid))
        lines.append(asp.fact("hazard", sid, site.hazard))
        lines.append(asp.fact("site_tag", sid, "road"))
        lines.append(asp.fact("site_tag", sid, "repair"))
        lines.append(asp.fact("site_tag", sid, "putty"))
        lines.append(asp.fact("site_tag", sid, "teamwork"))
        lines.append(asp.fact("site_tag", sid, "suspense"))
        lines.append(asp.fact("site_tag", sid, "adventure"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_site(S) :- site(S).
#show valid_site/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(params: StoryParams) -> None:
    if params.name == params.helper:
        raise StoryError("A teamwork story needs two different workers.")
    if params.site not in ROAD_SITES:
        raise StoryError("Unknown repair site.")


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    site = ROAD_SITES[params.site]
    team = TEAM_LINES[params.site]
    world = World(site)

    lead = world.add(Entity(id=params.name, kind="character", label=params.name, type="worker"))
    helper = world.add(Entity(id=params.helper, kind="character", label=params.helper, type="worker"))
    road = world.add(Entity(id="road", kind="thing", label=site.place, type="road"))
    putty = world.add(Entity(id="putty", kind="thing", label=f"the {site.putty_color}", type="putty"))
    tool = world.add(Entity(id="tool", kind="thing", label=site.repair_tool, type="tool"))

    lead.memes["worry"] = 1
    helper.memes["focus"] = 1
    road.meters["damage"] = 1
    putty.meters["ready"] = 1
    tool.meters["ready"] = 1

    world.say(f"{lead.id} and {helper.id} arrived at {site.place} on a {params.weather} morning.")
    world.say(f"Everyone could see {site.hazard}, and the team knew they had to {team.lead}.")
    world.para()
    world.say(f"{helper.id} {team.helper}, while {lead.id} checked the bucket of putty and {tool.label}.")
    world.say(team.suspense_line)
    world.para()
    road.meters["damage"] = 0
    road.meters["repaired"] = 1
    putty.meters["used"] = 1
    lead.memes["worry"] = 0
    lead.memes["pride"] = 1
    helper.memes["pride"] = 1
    world.say(f"Together, they {team.action} with {tool.label}.")
    world.say(team.ending_line)

    world.facts.update(
        lead=lead,
        helper=helper,
        road=road,
        putty=putty,
        tool=tool,
        site=site,
        team=team,
        params=params,
    )

    prompts = [
        f"Write a short adventure story about {params.name} and {params.helper} fixing {site.place} with putty.",
        f"Tell a suspenseful teamwork tale where two road workers repair {site.hazard}.",
        f"Write a child-friendly story in which putty helps save a road and the team finishes together.",
    ]
    story_qa = [
        QAItem(
            question=f"Who worked together at {site.place}?",
            answer=f"{params.name} and {params.helper} worked together at {site.place}. They shared the repair job and finished it as a team.",
        ),
        QAItem(
            question=f"What problem did they fix on the road?",
            answer=f"They fixed {site.hazard} by using putty to fill and smooth the damaged spot.",
        ),
        QAItem(
            question=f"Why was the middle of the story suspenseful?",
            answer=f"It felt suspenseful because the team had to repair the road before traffic came back, and they kept watching the road while they worked.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is putty used for?",
            answer="Putty is a soft material that can be pressed into gaps, cracks, or holes so a surface becomes smooth again.",
        ),
        QAItem(
            question="Why is teamwork helpful on a repair job?",
            answer="Teamwork is helpful because each person can do a part of the job, and together they can finish safely and faster.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print("== Prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== Story Q&A ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== World Q&A ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def generate_many(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
        return samples
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(50, args.n * 20):
        rng = random.Random(base_seed + i)
        i += 1
        params = resolve_params(args, rng)
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_site/1."))
        return
    if args.verify:
        print("OK: storyworld is structurally valid.")
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_site/1."))
        print(f"{len(asp.atoms(model, 'valid_site'))} valid sites")
        for (sid,) in sorted(set(asp.atoms(model, "valid_site"))):
            print(sid)
        return

    samples = generate_many(args)
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
