#!/usr/bin/env python3
"""
A standalone storyworld for a tiny Superhero Story about plankton, Spanish,
humor, and bravery.

Core premise:
- A small plankton hero wants to help the sea.
- A tricky situation scares the hero or makes the task awkward.
- Humor helps the hero keep going, and bravery turns the moment into a win.
- The ending image proves the hero changed something in the world.

This world is intentionally narrow: it focuses on one small type of rescue
story so the generated samples stay coherent and child-facing.
"""

from __future__ import annotations

import argparse
import copy
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
    wearing: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hero", "kid", "captain"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "girl-hero"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def they(self) -> str:
        return "them"


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    rush: str
    hazard: str
    cause: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    protects: set[str]
    solution_for: set[str]
    prep: str
    ending: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _happen(world: World, hero: Entity, challenge: Challenge) -> list[str]:
    out: list[str] = []
    if hero.meters.get(challenge.id, 0.0) < THRESHOLD:
        return out
    sig = ("happen", hero.id, challenge.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["alarm"] = hero.memes.get("alarm", 0.0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    out.append(f"The trouble grew bigger, but {hero.id} kept moving forward.")
    return out


def _humor(world: World, hero: Entity) -> list[str]:
    out: list[str] = []
    if hero.memes.get("humor", 0.0) < THRESHOLD:
        return out
    sig = ("humor", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(f"{hero.id} made a silly joke to keep everyone smiling.")
    return out


def _repair(world: World, hero: Entity, sidekick: Entity, aid: Aid) -> list[str]:
    out: list[str] = []
    sig = ("repair", hero.id, aid.id)
    if sig in world.fired:
        return out
    if hero.memes.get("bravery", 0.0) < THRESHOLD:
        return out
    if hero.meters.get("mist", 0.0) < THRESHOLD:
        return out
    world.fired.add(sig)
    hero.meters["mist"] = max(0.0, hero.meters.get("mist", 0.0) - 1)
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    sidekick.memes["joy"] = sidekick.memes.get("joy", 0.0) + 1
    out.append(f"{hero.id} used the {aid.label} and fixed the problem.")
    return out


def propagate(world: World, hero: Entity, sidekick: Entity, aid: Aid) -> None:
    changed = True
    while changed:
        changed = False
        for s in _happen(world, hero, world.facts["challenge"]):
            world.say(s)
            changed = True
        for s in _humor(world, hero):
            world.say(s)
            changed = True
        for s in _repair(world, hero, sidekick, aid):
            world.say(s)
            changed = True


SETTINGS = {
    "coral_bay": Setting(
        place="Coral Bay",
        mood="bright",
        affords={"freefish", "giggleguard"},
    ),
    "harbor": Setting(
        place="Moon Harbor",
        mood="windy",
        affords={"freefish", "giggleguard"},
    ),
}

CHALLENGES = {
    "net": Challenge(
        id="net",
        verb="free the fish",
        rush="swim toward the tangled net",
        hazard="caught in a net",
        cause="a sloppy fishing line",
        keyword="plankton",
        tags={"sea", "net", "humor"},
    ),
    "shadow": Challenge(
        id="shadow",
        verb="find the lost lantern",
        rush="follow the dark shadow",
        hazard="a scary shadow",
        cause="the lantern drifted under a dock",
        keyword="spanish",
        tags={"sea", "shadow", "bravery"},
    ),
}

AIDS = {
    "bubble_belt": Aid(
        id="bubble_belt",
        label="bubble belt",
        phrase="a shiny bubble belt",
        protects={"float"},
        solution_for={"freefish"},
        prep="strap on the bubble belt",
        ending="floated proudly beside the rescued fish",
    ),
    "joke_gem": Aid(
        id="joke_gem",
        label="joke gem",
        phrase="a tiny joke gem",
        protects={"mood"},
        solution_for={"giggleguard"},
        prep="tap the joke gem for courage",
        ending="laughed as the lantern sparkled above the water",
    ),
}

HERO_NAMES = ["Paco", "Mina", "Luz", "Nico", "Tia", "Rafa", "Sofia", "Beto"]
SIDEKICK_NAMES = ["Toto", "Momo", "Coco", "Luna"]
TRAITS = ["tiny", "quick", "clever", "cheerful"]


@dataclass
class StoryParams:
    setting: str
    challenge: str
    aid: str
    hero: str
    sidekick: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sname, setting in SETTINGS.items():
        for cid, ch in CHALLENGES.items():
            if cid == "net" and "freefish" in setting.affords:
                out.append((sname, cid, "bubble_belt"))
            if cid == "shadow" and "giggleguard" in setting.affords:
                out.append((sname, cid, "joke_gem"))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny superhero storyworld with plankton, Spanish, humor, and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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
    combos = valid_combos()
    if args.setting and args.challenge and args.aid:
        if (args.setting, args.challenge, args.aid) not in combos:
            raise StoryError("That combination does not make a believable superhero rescue in this world.")
    allowed = [c for c in combos
               if (args.setting is None or c[0] == args.setting)
               and (args.challenge is None or c[1] == args.challenge)
               and (args.aid is None or c[2] == args.aid)]
    if not allowed:
        raise StoryError("No valid story matches the chosen options.")
    setting, challenge, aid = rng.choice(sorted(allowed))
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICK_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, challenge=challenge, aid=aid, hero=hero, sidekick=sidekick, trait=trait)


def tell(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.hero, kind="character", type="hero", traits=["plankton", params.trait]))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="hero", traits=["fish-friend"]))
    challenge = CHALLENGES[params.challenge]
    aid = AIDS[params.aid]

    world.facts["challenge"] = challenge

    world.say(f"In {world.setting.place}, a small plankton hero named {hero.id} wore {aid.phrase} and dreamed of helping the sea.")
    world.say(f"{hero.id} loved Spanish words, so {hero.id} smiled and said, \"Hola!\" before every mission.")
    world.say(f"{hero.id} was {params.trait} and ready, even when the water felt full of trouble.")

    world.para()
    if params.challenge == "net":
        world.say(f"One day, {hero.id} saw {challenge.cause}, and the fish were stuck behind it.")
        world.say(f"{hero.id} wanted to {challenge.verb}, but first {hero.id} had to {challenge.rush}.")
    else:
        world.say(f"One night, {hero.id} saw {challenge.cause}, and the lantern light disappeared.")
        world.say(f"{hero.id} wanted to {challenge.verb}, but first {hero.id} had to {challenge.rush}.")

    hero.meters[challenge.id] = 1
    hero.memes["humor"] = 1
    hero.memes["bravery"] = 1
    propagate(world, hero, sidekick, aid)

    world.para()
    if params.challenge == "net":
        world.say(f"{hero.id} laughed, \"¡Vamos!\" and used the {aid.label} to tug the net loose.")
        world.say(f"The fish zipped free, and {hero.id} {aid.ending}.")
    else:
        world.say(f"{hero.id} laughed, \"No pasa nada!\" and used the {aid.label} to shine a brave little joke into the dark.")
        world.say(f"The shadow was only a dock post, and {hero.id} {aid.ending}.")

    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    sidekick.memes["joy"] = sidekick.memes.get("joy", 0.0) + 1

    world.facts.update(hero=hero, sidekick=sidekick, aid=aid, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    ch = CHALLENGES[p.challenge]
    return [
        f"Write a short superhero story about a plankton hero in {world.setting.place} who speaks a little Spanish and uses humor to stay brave.",
        f"Tell a child-friendly sea adventure where {p.hero} must {ch.verb} with {AIDS[p.aid].label} and a cheerful joke.",
        f"Make a tiny superhero story with plankton, Spanish words, humor, and bravery that ends with a happy rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    ch = CHALLENGES[p.challenge]
    aid = world.facts["aid"]
    return [
        QAItem(
            question=f"Who was the plankton superhero in the story?",
            answer=f"The plankton superhero was {p.hero}, a {p.trait} little hero in {world.setting.place}.",
        ),
        QAItem(
            question=f"What problem did {p.hero} face?",
            answer=f"{p.hero} faced {ch.hazard}, which made the rescue tricky.",
        ),
        QAItem(
            question=f"What helped {p.hero} keep going?",
            answer=f"Humor helped {p.hero} stay calm, and bravery helped {p.hero} solve the problem with the {aid.label}.",
        ),
        QAItem(
            question=f"Why was Spanish part of the story?",
            answer=f"{p.hero} liked Spanish words and said cheerful phrases like \"Hola\" and \"¡Vamos!\" while helping.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is plankton?",
            answer="Plankton are tiny living things that drift in the water and are an important part of ocean life.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel scared, because helping matters more.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is something funny that makes people smile or laugh.",
        ),
        QAItem(
            question="What is Spanish?",
            answer="Spanish is a language people use to talk, read, and tell stories.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when a setting affords the challenge and the aid matches it.
valid(S, C, A) :- setting(S), challenge(C), aid(A), affords(S, C), matches(A, C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for s, setting in SETTINGS.items():
        for c in sorted(setting.affords):
            lines.append(asp.fact("affords", s, c))
    for c in CHALLENGES:
        lines.append(asp.fact("challenge", c))
    for a, aid in AIDS.items():
        lines.append(asp.fact("aid", a))
        for t in sorted(aid.solution_for):
            lines.append(asp.fact("matches", a, t))
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(setting="coral_bay", challenge="net", aid="bubble_belt", hero="Paco", sidekick="Toto", trait="clever"),
    StoryParams(setting="harbor", challenge="shadow", aid="joke_gem", hero="Luz", sidekick="Luna", trait="cheerful"),
]


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    world = tell(world, params)
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
        print(asp_valid_combos())
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
            header = f"### {p.hero}: {p.challenge} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
