#!/usr/bin/env python3
"""
A standalone storyworld for a tiny superhero suspense tale.

Seed image:
A small hero watches a glowing dot near the moonlit roundabout, then must
choose how to act before danger reaches the street.

World idea:
- A child superhero patrols a roundabout at dusk.
- A blinking dot is actually a distress signal from a stuck kitten-drone.
- Suspense rises because the hero must cross safely and act fast before the
  signal fades.
- The hero uses a moonbeam glider, a helper, and a careful rescue to resolve
  the tension.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "heroine"}
        male = {"boy", "father", "man", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    nocturnal: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    noun: str
    verb: str
    gerund: str
    rush: str
    danger: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class StoryParams:
    setting: str
    challenge: str
    aid: str
    name: str
    gender: str
    ally: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "roundabout": Setting(place="the roundabout", nocturnal=True, affords={"signal", "rescue"}),
    "rooftop": Setting(place="the rooftop", nocturnal=True, affords={"signal"}),
    "harbor": Setting(place="the harbor", nocturnal=True, affords={"signal", "rescue"}),
}

CHALLENGES = {
    "dot": Challenge(
        id="dot",
        noun="dot",
        verb="follow the dot",
        gerund="following the dot",
        rush="dash toward the dot",
        danger="the dot could vanish into the dark",
        weather="clear",
        keyword="dot",
        tags={"dot", "signal"},
    ),
    "moon": Challenge(
        id="moon",
        noun="moon",
        verb="reach the moonlight",
        gerund="racing through moonlight",
        rush="run for the moonlit edge",
        danger="the path looked slippery and strange",
        weather="clear",
        keyword="moon",
        tags={"moon", "light"},
    ),
    "roundabout": Challenge(
        id="roundabout",
        noun="roundabout",
        verb="stop at the roundabout",
        gerund="circling the roundabout",
        rush="swerve into the roundabout",
        danger="cars could appear from every side",
        weather="windy",
        keyword="roundabout",
        tags={"roundabout", "street"},
    ),
}

AIDS = {
    "glider": Aid(
        id="glider",
        label="moonbeam glider",
        phrase="a moonbeam glider",
        prep="strap on the moonbeam glider first",
        tail="glided over the street on a silver beam",
        protects={"fall"},
    ),
    "signal_lens": Aid(
        id="signal_lens",
        label="signal lens",
        phrase="a bright signal lens",
        prep="hold up the signal lens",
        tail="shone the hidden signal straight ahead",
        protects={"dark"},
    ),
    "helper_cape": Aid(
        id="helper_cape",
        label="helper cape",
        phrase="a red helper cape",
        prep="tie on the helper cape",
        tail="flew side by side to keep watch",
        protects={"wind"},
    ),
}

HERO_NAMES = ["Nova", "Aria", "Milo", "Tara", "Jett", "Luna"]
ALLY_NAMES = ["Captain Pounce", "Drift", "Beacon", "Sprout", "Comet"]
TRAITS = ["brave", "quick", "careful", "spirited", "bright"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def challenge_at_risk(ch: Challenge, aid: Aid) -> bool:
    return ch.id == "dot" and aid.id == "signal_lens" or ch.id == "roundabout" and aid.id in {"glider", "helper_cape"} or ch.id == "moon" and aid.id in {"glider", "signal_lens"}


def select_aid(ch: Challenge) -> Optional[Aid]:
    if ch.id == "dot":
        return AIDS["signal_lens"]
    if ch.id == "roundabout":
        return AIDS["helper_cape"]
    if ch.id == "moon":
        return AIDS["glider"]
    return None


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def predict(world: World, hero: Entity, challenge: Challenge) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    h.memes["fear"] = h.memes.get("fear", 0) + 1
    if challenge.id == "roundabout":
        return {"danger": True, "loss": "traffic"}
    if challenge.id == "dot":
        return {"danger": True, "loss": "signal"}
    return {"danger": False, "loss": ""}


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.pronoun('subject')} who watched the city carefully at night.")


def setup(world: World, hero: Entity, ally: Entity, ch: Challenge) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"{hero.id} loved {ch.gerund}, especially when the {world.setting.place} was quiet and the moon hung high."
    )
    world.say(
        f"Tonight, {ally.id} sent a tiny {ch.noun} of light from across the street, and {hero.id} knew something was wrong."
    )


def tension(world: World, hero: Entity, ally: Entity, ch: Challenge) -> None:
    hero.memes["suspense"] = hero.memes.get("suspense", 0) + 1
    world.say(
        f"{ch.danger.capitalize()}; {hero.id} had to make a fast choice before the glow faded."
    )
    if ch.id == "roundabout":
        world.say(
            f"{hero.id} looked toward the roundabout, where headlights circled like watchful eyes."
        )
    elif ch.id == "moon":
        world.say(
            f"The moonlight slipped behind a cloud, and the path suddenly felt much longer."
        )
    else:
        world.say(
            f"The blinking dot trembled near a curb, and {hero.id} could not tell if it was a clue or a cry for help."
        )


def turn(world: World, hero: Entity, ally: Entity, ch: Challenge, aid: Aid) -> None:
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    world.say(
        f"Then {hero.id} chose the safe way: {aid.prep}, and {hero.id} asked {ally.id} to keep the street clear."
    )
    world.say(
        f"Together they moved with care, and {aid.tail}."
    )


def resolve(world: World, hero: Entity, ally: Entity, ch: Challenge, aid: Aid) -> None:
    hero.memes["fear"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    world.say(
        f"At last, the little {ch.noun} was not a mystery at all: it was a rescue signal from a stuck kitten-drone."
    )
    world.say(
        f"{hero.id} helped free it, and the tiny machine blinked happily back toward {ally.id}."
    )
    world.say(
        f"By the end, the roundabout was calm again, the moon was bright overhead, and {hero.id} stood proud in the silver light."
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    ally = world.add(Entity(id=params.ally, kind="character", type="hero", label=params.ally))
    ch = CHALLENGES[params.challenge]
    aid = AIDS[params.aid]
    world.facts.update(hero=hero, ally=ally, challenge=ch, aid=aid, setting=setting)
    intro(world, hero)
    world.para()
    setup(world, hero, ally, ch)
    tension(world, hero, ally, ch)
    world.para()
    turn(world, hero, ally, ch, aid)
    resolve(world, hero, ally, ch, aid)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ch: Challenge = f["challenge"]
    hero: Entity = f["hero"]
    ally: Entity = f["ally"]
    return [
        f'Write a suspenseful superhero story for a young child that includes the words "{ch.keyword}", "moon", and "roundabout".',
        f"Tell a gentle superhero story where {hero.id} must act fast at {world.setting.place} after {ally.id} sends a tiny {ch.noun} of light.",
        f"Write a short suspense story about a brave helper, a glowing clue, and a safe rescue at the roundabout.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    ally: Entity = f["ally"]
    ch: Challenge = f["challenge"]
    aid: Aid = f["aid"]
    return [
        QAItem(
            question=f"What made {hero.id} feel suspense at {world.setting.place}?",
            answer=f"{ally.id} sent a tiny {ch.noun} of light, and {hero.id} could tell something needed help before the glow faded.",
        ),
        QAItem(
            question=f"What did {hero.id} do to handle the danger?",
            answer=f"{hero.id} chose the safe way, put on {aid.phrase}, and worked with {ally.id} to make a careful rescue.",
        ),
        QAItem(
            question=f"What was the blinking clue really?",
            answer="It was a rescue signal from a stuck kitten-drone, not just a random light.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} freed the kitten-drone, the roundabout became calm, and the moon shone over a happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a roundabout?",
            answer="A roundabout is a circular road junction where cars move around a center and take turns going out.",
        ),
        QAItem(
            question="What does moonlight do?",
            answer="Moonlight is the light from the moon that can make streets and rooftops look silver and bright at night.",
        ),
        QAItem(
            question="What is a dot?",
            answer="A dot is a tiny spot or point, like a small light in the dark.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(roundabout).
setting(rooftop).
setting(harbor).

challenge(dot).
challenge(moon).
challenge(roundabout).

aid(signal_lens).
aid(glider).
aid(helper_cape).

risk(dot,signal_lens).
risk(moon,glider).
risk(roundabout,helper_cape).
risk(roundabout,glider).
risk(moon,signal_lens).

valid_story(S,C,A) :- setting(S), challenge(C), aid(A), risk(C,A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
    for ch, aid in [("dot", "signal_lens"), ("moon", "glider"), ("roundabout", "helper_cape"), ("roundabout", "glider"), ("moon", "signal_lens")]:
        lines.append(asp.fact("risk", ch, aid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_stories())
    if python_set == asp_set:
        print(f"OK: ASP matches Python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(python_set - asp_set))
    print("asp only:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Story selection and generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid in CHALLENGES:
            for aid in AIDS:
                if challenge_at_risk(CHALLENGES[cid], AIDS[aid]):
                    combos.append((sid, cid, aid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero suspense storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy", "heroine", "hero"])
    ap.add_argument("--ally", choices=ALLY_NAMES)
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
    if args.setting and args.challenge and args.aid:
        ch = CHALLENGES[args.challenge]
        aid = AIDS[args.aid]
        if not challenge_at_risk(ch, aid):
            raise StoryError("That aid does not fit the suspense problem in this storyworld.")

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.challenge is None or c[1] == args.challenge)
        and (args.aid is None or c[2] == args.aid)
    ]
    if not combos:
        raise StoryError("No valid combination matches the requested options.")

    setting, challenge, aid = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    ally = args.ally or rng.choice(ALLY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        challenge=challenge,
        aid=aid,
        name=name,
        gender=gender,
        ally=ally,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="roundabout", challenge="dot", aid="signal_lens", name="Nova", gender="girl", ally="Beacon", trait="brave"),
    StoryParams(setting="harbor", challenge="moon", aid="glider", name="Milo", gender="boy", ally="Drift", trait="careful"),
    StoryParams(setting="roundabout", challenge="roundabout", aid="helper_cape", name="Luna", gender="girl", ally="Captain Pounce", trait="spirited"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
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
            header = f"### {p.name}: {p.challenge} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
