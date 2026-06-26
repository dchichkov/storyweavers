#!/usr/bin/env python3
"""
A small storyworld about a camel, a stroll, and a magical troublemaker
whose ending can turn from bad to happy.

Premise:
- A child or explorer leads a camel on a calm stroll across a strange
  off-world path.
- A bit of Magic makes the path lively and risky.
- If the traveler hesitates, the story can tilt toward a Bad Ending.
- If they use the right cleverness, the trouble is vanquished and the tale
  lands in a Happy Ending.

This script models physical meters and emotional memes, supports the shared
storyworld contract, and includes a Python reasonableness gate plus inline ASP
rules that mirror it.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the moon road"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    label: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    weather: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]
    magical: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(region in getattr(e, "covers", set()) for e in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTING = Setting(place="the moon road", indoors=False, affords={"stroll", "vanquish"})

CHALLENGES = {
    "comet_dust": Challenge(
        id="comet_dust",
        label="comet dust",
        verb="stroll through the comet dust",
        gerund="strolling through comet dust",
        rush="dash through the comet dust",
        risk="dusty and dim",
        zone={"feet", "legs"},
        weather="space",
        keyword="camel",
        tags={"space", "dust", "camel"},
    ),
    "magic_mist": Challenge(
        id="magic_mist",
        label="magic mist",
        verb="stroll through the magic mist",
        gerund="strolling through magic mist",
        rush="rush into the magic mist",
        risk="sparkly and confusing",
        zone={"feet", "legs", "torso"},
        weather="space",
        keyword="magic",
        tags={"magic"},
    ),
}

AIDS = {
    "visor": Aid(
        id="visor",
        label="a bright visor",
        prep="put on a bright visor first",
        tail="put on the bright visor",
        guards={"sparkly and confusing"},
        covers={"torso"},
        magical=True,
    ),
    "boots": Aid(
        id="boots",
        label="moon boots",
        prep="wear moon boots first",
        tail="pulled on the moon boots",
        guards={"dusty and dim"},
        covers={"feet"},
        magical=False,
    ),
    "cloak": Aid(
        id="cloak",
        label="a star cloak",
        prep="wear a star cloak first",
        tail="wrapped on the star cloak",
        guards={"dusty and dim", "sparkly and confusing"},
        covers={"feet", "legs", "torso"},
        magical=True,
    ),
}

GIRL_NAMES = ["Mina", "Tara", "Nia", "Luna", "Iris"]
BOY_NAMES = ["Kai", "Noel", "Timo", "Orin", "Bex"]
TRAITS = ["brave", "curious", "gentle", "patient", "bright"]


def challenge_needs_aid(challenge: Challenge) -> bool:
    return True


def select_aid(challenge: Challenge) -> Optional[Aid]:
    for aid in AIDS.values():
        if challenge.risk in aid.guards:
            return aid
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in {"moon road": SETTING}.items():
        for cid, ch in CHALLENGES.items():
            for aid in AIDS.values():
                if ch.risk in aid.guards:
                    combos.append((place, cid, aid.id))
    return combos


def explain_rejection(challenge: Challenge) -> str:
    return (
        f"(No story: {challenge.label} has no compatible aid in this world, "
        f"so there is no fair way to build a believable vanquish.)"
    )


@dataclass
class StoryParams:
    place: str
    challenge: str
    aid: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A Space Adventure storyworld about a camel, a stroll, and magic trouble."
    )
    ap.add_argument("--place", choices=["moon road"], default=None)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait")
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
    if args.challenge and args.aid:
        ch = CHALLENGES[args.challenge]
        aid = AIDS[args.aid]
        if ch.risk not in aid.guards:
            raise StoryError(explain_rejection(ch))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    _, challenge_id, aid_id = rng.choice(sorted(combos))
    ch = CHALLENGES[challenge_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place="moon road", challenge=challenge_id, aid=aid_id,
                       name=name, gender=gender, trait=trait)


def make_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait]))
    camel = world.add(Entity(id="Camel", kind="character", type="camel", label="camel"))
    path = world.add(Entity(id="Path", kind="thing", type="path", label="moon road"))
    aid = world.add(Entity(id=params.aid, type="gear", label=AIDS[params.aid].label))
    aid.worn_by = hero.id
    world.facts.update(hero=hero, camel=camel, path=path, aid=aid, challenge=CHALLENGES[params.challenge], params=params)
    return world


def narrate(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    camel: Entity = f["camel"]
    ch: Challenge = f["challenge"]
    aid: Entity = f["aid"]
    hero.memes["hope"] = 1.0
    camel.memes["calm"] = 1.0
    world.say(f"{hero.id} was a little {hero.traits[1]} {hero.type} who loved space travel.")
    world.say(f"Beside {hero.pronoun('object')}, a calm camel waited for a quiet stroll across the moon road.")
    world.para()
    world.say(f"One night, {hero.id} and the camel began a slow stroll under silver stars.")
    world.say(f"But the path shimmered with {ch.label}, and that made the stroll tricky.")
    world.say(f"{hero.id} wanted to {ch.verb}, but {ch.risk} magic could tangle their way.")
    hero.memes["worry"] = 1.0
    if aid.id == "visor":
        world.say(f"So {hero.pronoun('possessive').capitalize()} helper said, \"{AIDS[aid.id].prep}.\"")
    elif aid.id == "boots":
        world.say(f"So {hero.pronoun('possessive').capitalize()} helper said, \"{AIDS[aid.id].prep}.\"")
    else:
        world.say(f"So {hero.pronoun('possessive').capitalize()} helper said, \"{AIDS[aid.id].prep}.\"")
    world.para()
    hero.memes["defiance"] = 1.0
    world.say(f"{hero.id} stepped forward anyway, and the magic puffed up like a bright space cloud.")
    if ch.id == "magic_mist":
        world.say(f"The mist swirled around the camel's knees and made the path look like a bad ending.")
        world.facts["bad_ending"] = True
        world.say(f"For a tiny moment, it seemed like the camel might stop and the stroll might fail.")
    else:
        world.say(f"Comet dust tried to blanket their feet, but the right gear held it back.")
    world.para()
    hero.memes["courage"] = 1.0
    world.say(f"Then {hero.id} took a breath, lifted the {aid.label}, and chose the clever way.")
    world.say(f"Together, {hero.id} and the camel could vanquish the trouble and keep going.")
    world.say(f"The magic broke apart in glittering sparks, and the stroll became a happy ending.")
    hero.memes["joy"] = 2.0
    camel.memes["calm"] = 2.0
    world.facts["happy_ending"] = True


def story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    ch: Challenge = f["challenge"]
    return [
        f"Write a Space Adventure story about a camel and {hero.id} on a stroll through {ch.label}.",
        f"Tell a gentle tale where a child and a camel vanquish magic trouble and reach a happy ending.",
        f"Write a short child-facing story using the words camel, stroll, vanquish, Magic, Bad Ending, and Happy Ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    ch: Challenge = f["challenge"]
    aid: Entity = f["aid"]
    qs = [
        QAItem(
            question=f"Who went on the stroll with the camel?",
            answer=f"{hero.id} went on the stroll with the camel.",
        ),
        QAItem(
            question=f"What made the stroll tricky?",
            answer=f"The {ch.label} made the stroll tricky because it was {ch.risk}.",
        ),
        QAItem(
            question=f"What helped {hero.id} handle the magic trouble?",
            answer=f"{hero.id} used {aid.label} to handle the magic trouble.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with the trouble vanquished and the camel's stroll becoming a happy ending.",
        ),
    ]
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a camel?",
            answer="A camel is a desert animal with long legs and a steady walk.",
        ),
        QAItem(
            question="What does stroll mean?",
            answer="To stroll means to walk slowly and calmly.",
        ),
        QAItem(
            question="What does vanquish mean?",
            answer="To vanquish means to defeat or overcome something completely.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a pretend force in stories that can make strange and wonderful things happen.",
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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
place(moon_road).
challenge(comet_dust).
challenge(magic_mist).
aid(visor).
aid(boots).
aid(cloak).

risk(comet_dust,dusty_and_dim).
risk(magic_mist,sparkly_and_confusing).

guards(boots,dusty_and_dim).
guards(visor,sparkly_and_confusing).
guards(cloak,dusty_and_dim).
guards(cloak,sparkly_and_confusing).

valid(Place, Challenge, Aid) :- place(Place), challenge(Challenge), aid(Aid),
                                 risk(Challenge,R), guards(Aid,R).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in ["moon_road"]:
        lines.append(asp.fact("place", place))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("risk", cid, ch.risk.replace(" ", "_")))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for g in aid.guards:
            lines.append(asp.fact("guards", aid_id, g.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    narrate(world)
    return StorySample(
        params=params,
        story=story_text(world),
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


CURATED = [
    StoryParams(place="moon road", challenge="comet_dust", aid="boots", name="Mina", gender="girl", trait="brave"),
    StoryParams(place="moon road", challenge="magic_mist", aid="visor", name="Kai", gender="boy", trait="curious"),
    StoryParams(place="moon road", challenge="magic_mist", aid="cloak", name="Luna", gender="girl", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print(" ", row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
