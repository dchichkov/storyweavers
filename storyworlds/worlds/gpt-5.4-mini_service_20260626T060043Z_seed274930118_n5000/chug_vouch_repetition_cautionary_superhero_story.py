#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chug_vouch_repetition_cautionary_superhero_story.py
=============================================================================================

A compact superhero-story world with a cautionary, repetitive beat:
a young hero wants to chug a booster drink, but a mentor vouches for
a safer plan instead. The premise is small, stateful, and constraint-checked:
the drink can help, but only after the hero slows down, listens, and uses it
carefully.

Seed words: chug, vouch
Features: Repetition, Cautionary
Style: Superhero Story
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
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("weight", "spill", "mess", "stamina"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "rush", "trust", "pride", "calm", "fear", "defiance", "relief"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the rooftop"
    affords: set[str] = field(default_factory=set)


@dataclass
class Boost:
    id: str
    label: str
    phrase: str
    verb: str
    caution: str
    safe_step: str
    surge: str
    kind: str = "boost"
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


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

    def chars(self) -> list[Entity]:
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class StoryParams:
    place: str
    boost: str
    gear: str
    name: str
    sidekick: str
    mentor: str
    gender: str
    seed: Optional[int] = None


SETTINGS = {
    "rooftop": Setting("the rooftop", {"charge", "spark"}),
    "alley": Setting("the alley", {"charge", "spark"}),
    "lab": Setting("the lab", {"charge", "spark", "smoke"}),
}

BOOSTS = {
    "charge": Boost(
        id="charge",
        label="a charge drink",
        phrase="a bright charge drink",
        verb="chug the charge drink",
        caution="chug too fast",
        safe_step="sip it slowly",
        surge="a burst of brave energy",
        tags={"energy", "drink", "charge"},
    ),
    "spark": Boost(
        id="spark",
        label="a spark serum",
        phrase="a tiny spark serum",
        verb="chug the spark serum",
        caution="rush the spark serum",
        safe_step="taste it first",
        surge="a quick spark of energy",
        tags={"energy", "spark"},
    ),
    "smoke": Boost(
        id="smoke",
        label="a smoke tonic",
        phrase="a smoky tonic bottle",
        verb="chug the smoke tonic",
        caution="gulp the smoke tonic all at once",
        safe_step="use one small sip",
        surge="a cloudy puff of power",
        tags={"tonic", "smoke"},
    ),
}

GEAR = {
    "visor": Gear(
        id="visor",
        label="a clear visor",
        phrase="a clear visor",
        guards={"spark", "smoke"},
        covers={"eyes"},
        prep="put on a clear visor first",
        tail="put on the clear visor and took one careful sip",
    ),
    "gloves": Gear(
        id="gloves",
        label="strong gloves",
        phrase="strong gloves",
        guards={"charge", "spark"},
        covers={"hands"},
        prep="pull on strong gloves first",
        tail="pull on the strong gloves and hold the bottle safely",
    ),
    "cape": Gear(
        id="cape",
        label="a calm cape",
        phrase="a calm cape",
        guards={"smoke"},
        covers={"back"},
        prep="clip on a calm cape first",
        tail="clip on the calm cape and stay steady",
        plural=False,
    ),
}

NAMES = ["Nova", "Sky", "Mara", "Tess", "Ivy", "Zane", "Jules", "Finn"]
SIDEKICKS = ["Patch", "Quill", "Beep", "Mote"]
MENTORS = ["Captain Vow", "Aunt Halo", "Major Bright"]


def _hero_pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "girl":
        return "she", "her", "her"
    return "he", "him", "his"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for boost_id in s.affords:
            boost = BOOSTS[boost_id]
            for gear_id, gear in GEAR.items():
                if boost.id in gear.guards:
                    out.append((place, boost_id, gear_id))
    return out


def _warn_repeated(world: World, hero: Entity, mentor: Entity, boost: Boost) -> None:
    hero.memes["rush"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"{mentor.id} gave the same steady warning again and again: "
        f'"Don’t {boost.caution}. {boost.safe_step}."'
    )


def _predict(world: World, hero: Entity, boost: Boost, gear: Gear) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["stamina"] += 1
    sim.get(hero.id).memes["rush"] += 1
    if boost.id in gear.guards:
        safe = True
    else:
        safe = False
    return {"safe": safe}


def _do_boost(world: World, hero: Entity, boost: Boost, gear: Optional[Gear], narrate: bool = True) -> None:
    hero.meters["stamina"] += 1
    hero.meters["weight"] += 1
    hero.memes["joy"] += 1
    if gear is None:
        hero.meters["spill"] += 1
        hero.meters["mess"] += 1
    if narrate:
        if gear:
            world.say(
                f"{hero.id} used {gear.label} and felt {boost.surge} without a mess."
            )
        else:
            world.say(
                f"{hero.id} felt {boost.surge}, but the bottle shook and made a spill."
            )


def intro(world: World, hero: Entity, mentor: Entity, sidekick: Entity, boost: Boost) -> None:
    world.say(
        f"{hero.id} was a little hero with a bright mask and a bigger wish to prove {hero.pronoun('possessive')} courage."
    )
    world.say(
        f"{hero.id} and {sidekick.id} had been practicing rescue steps on {world.setting.place} all week."
    )
    world.say(
        f"Near the bench sat {boost.phrase}, and {hero.id} kept looking at it."
    )


def desire(world: World, hero: Entity, boost: Boost) -> None:
    hero.memes["rush"] += 1
    world.say(
        f"{hero.id} wanted to {boost.verb} right away, and then want it again, and then want it again."
    )


def caution(world: World, mentor: Entity, hero: Entity, boost: Boost) -> None:
    _warn_repeated(world, hero, mentor, boost)
    world.say(
        f'{mentor.id} pointed at the bottle and said, "Careful heroes go first. '
        f"Fast heroes regret it later.""
    )


def vouch(world: World, mentor: Entity, hero: Entity, gear: Gear, boost: Boost) -> Gear:
    hero.memes["trust"] += 1
    world.say(
        f"{mentor.id} said {mentor.id.lower()} would vouch for {gear.label} because it matched {boost.label} better than bare hands did."
    )
    world.say(f'"{gear.prep}," {mentor.id} said.')
    return gear


def accept_or_refuse(world: World, hero: Entity, gear: Gear) -> None:
    hero.memes["calm"] += 1
    hero.memes["defiance"] = 0.0
    world.say(f"{hero.id} nodded, nodded again, and finally agreed.")
    world.say(f"{hero.id} reached for the gear and slowed down.")


def story(world: World, hero: Entity, mentor: Entity, sidekick: Entity, boost: Boost, gear: Gear) -> None:
    intro(world, hero, mentor, sidekick, boost)
    world.para()
    desire(world, hero, boost)
    caution(world, mentor, hero, boost)
    world.say(f"{hero.id} almost tried to {boost.caution}, but {mentor.id} warned {hero.pronoun('object')} again.")
    world.say(f"{sidekick.id} backed the warning too: careful first, fast later.")
    world.para()
    vouch(world, mentor, hero, gear, boost)
    accept_or_refuse(world, hero, gear)
    _do_boost(world, hero, boost, gear)
    world.say(
        f"At the end, {hero.id} stood straighter, {sidekick.id} smiled, and the bottle stayed safe."
    )


def generate_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    boost = BOOSTS[params.boost]
    gear = GEAR[params.gear]
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label="hero"))
    mentor = world.add(Entity(id=params.mentor, kind="character", type="woman", label="mentor"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="thing", label="sidekick"))
    bottle = world.add(Entity(id="boost", type="thing", label=boost.label, phrase=boost.phrase, owner=hero.id))
    world.facts.update(hero=hero, mentor=mentor, sidekick=sidekick, boost=boost, gear=gear, bottle=bottle)
    story(world, hero, mentor, sidekick, boost, gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    boost: Boost = f["boost"]
    return [
        f'Write a short superhero story for a young child that includes the words "chug" and "vouch".',
        f"Tell a cautionary story where {f['hero'].id} wants to {boost.verb} but a mentor vouches for a safer plan.",
        f"Write a repetitive hero story with a careful warning, a trusted helper, and a small bottle of {boost.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    sidekick = f["sidekick"]
    boost: Boost = f["boost"]
    gear: Gear = f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {boost.label}?",
            answer=f"{hero.id} wanted to {boost.verb} right away, but {mentor.id} told {hero.id} to slow down first.",
        ),
        QAItem(
            question=f"Why did {mentor.id} keep warning {hero.id} again and again?",
            answer=f"{mentor.id} kept warning {hero.id} because chugging too fast could make a mess or turn brave plans clumsy.",
        ),
        QAItem(
            question=f"How did {gear.label} help {hero.id}?",
            answer=f"{mentor.id} vouched for {gear.label}, and it helped {hero.id} handle the {boost.label} carefully without spilling it.",
        ),
        QAItem(
            question=f"Who backed up the cautionary advice?",
            answer=f"{sidekick.id} backed up the advice too, so {hero.id} heard the warning from more than one voice.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "chug": (
        "What does it mean to chug a drink?",
        "To chug a drink means to drink it very fast, usually in big gulps.",
    ),
    "vouch": (
        "What does it mean to vouch for someone or something?",
        "To vouch for someone or something means to say you trust it, believe in it, or think it is a good choice.",
    ),
    "caution": (
        "Why is caution important when trying something new?",
        "Caution helps you slow down, notice danger, and make safer choices so you are less likely to get hurt or make a mess.",
    ),
    "hero": (
        "What is a superhero story?",
        "A superhero story is a tale about a brave character who uses courage, teamwork, and smart choices to solve a problem.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE.values()]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== (2) Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:12} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
boost(B) :- boost_fact(B).
gear(G) :- gear_fact(G).

safe(P,B,G) :- affords(P,B), guards(G,B).
valid(P,B,G) :- place(P), boost(B), gear(G), safe(P,B,G).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
        for b in sorted(SETTINGS[p].affords):
            lines.append(asp.fact("affords", p, b))
    for b in BOOSTS:
        lines.append(asp.fact("boost_fact", b))
    for g in GEAR:
        lines.append(asp.fact("gear_fact", g))
        for m in sorted(GEAR[g].guards):
            lines.append(asp.fact("guards", g, m))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero cautionary storyworld with chug/vouch and repeated warning beats.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--boost", choices=sorted(BOOSTS))
    ap.add_argument("--gear", choices=sorted(GEAR))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--mentor", choices=MENTORS)
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
    if args.place or args.boost or args.gear:
        combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.boost is None or c[1] == args.boost) and (args.gear is None or c[2] == args.gear)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, boost, gear = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    mentor = args.mentor or rng.choice(MENTORS)
    return StoryParams(place=place, boost=boost, gear=gear, name=name, sidekick=sidekick, mentor=mentor, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


CURATED = [
    StoryParams(place="rooftop", boost="charge", gear="gloves", name="Nova", sidekick="Patch", mentor="Captain Vow", gender="girl"),
    StoryParams(place="alley", boost="spark", gear="visor", name="Zane", sidekick="Beep", mentor="Aunt Halo", gender="boy"),
    StoryParams(place="lab", boost="smoke", gear="cape", name="Mara", sidekick="Quill", mentor="Major Bright", gender="girl"),
]


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
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} valid combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
