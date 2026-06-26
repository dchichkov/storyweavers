#!/usr/bin/env python3
"""
Standalone storyworld: a small Animal-Story about a brig, rhyme, and teamwork.

Premise:
- A little crew of animals sails a brig.
- They want to make a rhyme for their trip.
- Something useful must be moved or fixed on the ship.
- A teamwork-based plan resolves the problem, and the ending shows the ship ready.

This world keeps one constraint-gated structure:
- A challenge is only reasonable when the ship needs a fix that the crew can actually do together.
- The declarative ASP twin mirrors the Python reasonableness gate.
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


@dataclass(frozen=True)
class CrewSpec:
    name: str
    species: str
    role: str
    pronoun: str
    possessive: str


@dataclass(frozen=True)
class JobSpec:
    id: str
    verb: str
    gerund: str
    risk: str
    fix: str
    tool: str
    requires: str
    keyword: str


@dataclass(frozen=True)
class SettingSpec:
    place: str
    deck_detail: str
    weather: str


@dataclass
class StoryParams:
    setting: str
    job: str
    hero: str
    helper: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "character"
    species: str = ""
    role: str = ""
    name: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, setting: SettingSpec) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines).strip()

    def trace(self) -> str:
        bits = ["--- world model state ---"]
        for e in self.entities.values():
            m = {k: v for k, v in e.meters.items() if v}
            n = {k: v for k, v in e.memes.items() if v}
            bits.append(f"{e.id}: species={e.species} role={e.role} meters={m} memes={n}")
        bits.append(f"setting={self.setting.place}")
        return "\n".join(bits)


SETTINGS: dict[str, SettingSpec] = {
    "harbor": SettingSpec(
        place="the harbor",
        deck_detail="The water rocked against the brig, and the ropes tapped the mast.",
        weather="breezy",
    ),
    "island": SettingSpec(
        place="the island dock",
        deck_detail="The brig creaked softly beside the dock, with gulls gliding overhead.",
        weather="sunny",
    ),
    "cove": SettingSpec(
        place="the cove",
        deck_detail="The brig bobbed in the cove while the foam flickered white on the waves.",
        weather="misty",
    ),
}

CREW: dict[str, CrewSpec] = {
    "pip": CrewSpec("Pip", "mouse", "rhyming lookout", "he", "his"),
    "mara": CrewSpec("Mara", "otter", "knot-tyer", "she", "her"),
    "tess": CrewSpec("Tess", "fox", "map reader", "she", "her"),
    "beet": CrewSpec("Beet", "bear", "hatch lifter", "he", "his"),
    "lulu": CrewSpec("Lulu", "rabbit", "bell ringer", "she", "her"),
}

JOBS: dict[str, JobSpec] = {
    "rope": JobSpec(
        id="rope",
        verb="pull the rope",
        gerund="pulling the rope",
        risk="the sail stays slack",
        fix="tighten the rope together",
        tool="a coil of rope",
        requires="rope",
        keyword="rhyme",
    ),
    "crate": JobSpec(
        id="crate",
        verb="move the crate",
        gerund="moving the crate",
        risk="the deck stays blocked",
        fix="lift the crate together",
        tool="a wooden crate",
        requires="crate",
        keyword="teamwork",
    ),
    "bucket": JobSpec(
        id="bucket",
        verb="carry the bucket",
        gerund="carrying the bucket",
        risk="the bilge stays wet",
        fix="pass the bucket together",
        tool="a tin bucket",
        requires="bucket",
        keyword="brig",
    ),
}

HERO_LINES = [
    "Pip loved to rhyme while the brig rocked on the waves.",
    "Mara liked teamwork and never let a friend work alone.",
    "Tess always noticed the safest way to help on deck.",
    "Beet was strong, but he liked a plan even more than a push.",
    "Lulu rang the bell with a bright smile and a tiny song.",
]

ENDINGS = [
    "Soon the brig was ready to go, and the crew sang their rhyme as the sails filled.",
    "At last the ship felt steady, and the animals laughed together as the water shone around them.",
    "When the job was done, the brig glided on happily, and the crew's little rhyme bounced over the waves.",
]


def choose_crew(rng: random.Random, avoid: Optional[str] = None) -> str:
    names = [k for k in CREW if k != avoid]
    return rng.choice(names)


def valid_combo(setting: str, job: str, hero: str, helper: str) -> bool:
    return setting in SETTINGS and job in JOBS and hero in CREW and helper in CREW and hero != helper


def build_story(world: World, params: StoryParams) -> None:
    setting = SETTINGS[params.setting]
    job = JOBS[params.job]
    hero = CREW[params.hero]
    helper = CREW[params.helper]

    h = world.add(Entity(id=params.hero, species=hero.species, role=hero.role, name=hero.name))
    a = world.add(Entity(id=params.helper, species=helper.species, role=helper.role, name=helper.name))

    h.memes["joy"] = 1
    h.memes["love_rhyme"] = 1
    a.memes["joy"] = 1
    a.memes["love_teamwork"] = 1

    world.say(f"{hero.name} the {hero.species} was on a brig at {setting.place}.")
    world.say(HEIRLOOM := HERO_LINES[list(CREW).index(params.hero) % len(HERO_LINES)])
    world.say(f"{helper.name} the {helper.species} smiled, because {helper.name} liked teamwork on deck.")
    world.say(setting.deck_detail)
    world.say(f"Then {hero.name} noticed {job.risk}, and the crew could not sail on like that.")
    world.say(f"{hero.name} wanted to {job.verb}, but it was too hard for one small animal alone.")
    h.memes["worry"] = 1
    a.memes["worry"] = 1
    world.say(f"{helper.name} said, 'Let's use teamwork and {job.fix}.'")
    world.say(f"So {hero.name} and {helper.name} worked side by side with {job.tool}.")
    h.meters[job.requires] = 1
    a.meters[job.requires] = 1
    h.memes["pride"] = 1
    a.memes["pride"] = 1
    world.say(f"They did it together, and {job.risk} was gone.")
    world.say(random.choice(ENDINGS))
    world.facts.update(
        setting=params.setting,
        job=params.job,
        hero=params.hero,
        helper=params.helper,
    )


def story_qa(world: World) -> list[QAItem]:
    hero = CREW[world.facts["hero"]]
    helper = CREW[world.facts["helper"]]
    job = JOBS[world.facts["job"]]
    setting = SETTINGS[world.facts["setting"]]
    return [
        QAItem(
            question=f"Who was the story about on the brig at {setting.place}?",
            answer=f"It was about {hero.name} the {hero.species}, who was on a brig at {setting.place} with {helper.name} helping.",
        ),
        QAItem(
            question=f"What problem did the crew notice on the brig?",
            answer=f"They noticed that {job.risk}, so the ship needed help before it could sail on happily.",
        ),
        QAItem(
            question=f"How did {hero.name} and {helper.name} fix the problem?",
            answer=f"They used teamwork and got together to {job.fix}, which made the brig ready again.",
        ),
        QAItem(
            question=f"What kind of song did the story want to include?",
            answer="It wanted a rhyme, so the animals could sing while they worked together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a brig?",
            answer="A brig is a small sailing ship with masts and ropes, used for traveling on the water.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people or animals help each other and do a job together.",
        ),
        QAItem(
            question="Why do crews tie down things on a ship?",
            answer="They tie things down so the wind and waves do not make the ship unsafe or messy.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    setting = SETTINGS[world.facts["setting"]]
    job = JOBS[world.facts["job"]]
    hero = CREW[world.facts["hero"]]
    helper = CREW[world.facts["helper"]]
    return [
        f"Write a short animal story about {hero.name} and {helper.name} on a brig at {setting.place}.",
        f"Tell a gentle story that includes a rhyme and teamwork while animals solve a ship problem.",
        f"Write a child-friendly story where a brig needs help and two animal friends fix it together.",
    ]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for jid, job in JOBS.items():
        lines.append(asp.fact("job", jid))
        lines.append(asp.fact("requires", jid, job.requires))
        lines.append(asp.fact("risk", jid, job.risk.replace(" ", "_")))
    for cid, c in CREW.items():
        lines.append(asp.fact("crew", cid))
        lines.append(asp.fact("species", cid, c.species))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,J,H,K) :- setting(S), job(J), crew(H), crew(K), H != K.
#show valid_story/4.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}"


def asp_valid() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid_story"))


def python_valid() -> set[tuple]:
    return {(s, j, h, k) for s in SETTINGS for j in JOBS for h in CREW for k in CREW if h != k}


def asp_verify() -> int:
    a = asp_valid()
    b = python_valid()
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} combinations).")
        return 0
    print("Mismatch:")
    print("only ASP:", sorted(a - b))
    print("only Python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: brig, rhyme, teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--job", choices=JOBS)
    ap.add_argument("--hero", choices=CREW)
    ap.add_argument("--helper", choices=CREW)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    job = args.job or rng.choice(list(JOBS))
    hero = args.hero or rng.choice(list(CREW))
    helper = args.helper or choose_crew(rng, avoid=hero)
    if not valid_combo(setting, job, hero, helper):
        raise StoryError("No valid story matches the given options.")
    return StoryParams(setting=setting, job=job, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    build_story(world, params)
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
        print(sample.world.trace())
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"PROMPT {i}: {p}")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid story combinations")
        for row in vals[:50]:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s in SETTINGS:
            for j in JOBS:
                for h in CREW:
                    for k in CREW:
                        if h == k:
                            continue
                        params = StoryParams(setting=s, job=j, hero=h, helper=k)
                        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(100, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
