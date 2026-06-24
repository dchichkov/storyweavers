#!/usr/bin/env python3
"""
Story world: galaxy_surprise_magic_flashback_fairy_tale

A small, standalone fairy-tale simulation about a child in a galaxy garden,
where a magical surprise unlocks a flashback and changes the ending.

The world model tracks physical meters and emotional memes so the prose is
driven by state rather than a frozen template.
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
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "mom", "woman"}
        male = {"boy", "prince", "king", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    outdoors: bool = True
    magic: bool = False
    wonders: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    kind: str
    grants: set[str] = field(default_factory=set)
    triggers_flashback: bool = False


@dataclass
class StoryParams:
    place: str
    relic: str
    hero_name: str
    hero_type: str
    guardian_type: str
    trait: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


PLACES = {
    "moon_garden": Place("the moon garden", outdoors=True, magic=True, wonders={"galaxy", "flowers", "lantern"}),
    "star_lane": Place("the star lane", outdoors=True, magic=True, wonders={"galaxy", "dust", "lantern"}),
    "comet_courtyard": Place("the comet courtyard", outdoors=True, magic=True, wonders={"galaxy", "stones", "lantern"}),
}

RELICS = {
    "lantern": Relic("lantern", "lantern", "a silver lantern with a warm blue flame", "lantern",
                     grants={"light", "courage"}, triggers_flashback=True),
    "crown": Relic("crown", "crown", "a tiny crown of polished starlight", "crown",
                   grants={"pride", "light"}),
    "cloak": Relic("cloak", "cloak", "a velvet cloak stitched with little stars", "cloak",
                   grants={"warmth", "softness"}, triggers_flashback=True),
}

TRAITS = ["curious", "gentle", "brave", "kind", "dreamy"]
GIRL_NAMES = ["Luna", "Mira", "Nora", "Elara", "Lilia", "Sora"]
BOY_NAMES = ["Orin", "Theo", "Rian", "Milo", "Ari", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, p in PLACES.items():
        if "galaxy" not in p.wonders:
            continue
        for relic_id, r in RELICS.items():
            if p.magic and (r.triggers_flashback or "light" in r.grants):
                for hero_type in ("girl", "boy"):
                    combos.append((place, relic_id, hero_type))
    return combos


ASP_RULES = r"""
valid(Place, Relic, HeroType) :- place(Place), relic(Relic), hero_type(HeroType),
                                 galaxy_place(Place), magic_place(Place),
                                 relic_relevant(Relic).
relic_relevant(R) :- triggers_flashback(R).
relic_relevant(R) :- grants(R, light).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.magic:
            lines.append(asp.fact("magic_place", pid))
        if "galaxy" in place.wonders:
            lines.append(asp.fact("galaxy_place", pid))
        for w in sorted(place.wonders):
            lines.append(asp.fact("wonders", pid, w))
    for rid, rel in RELICS.items():
        lines.append(asp.fact("relic", rid))
        if rel.triggers_flashback:
            lines.append(asp.fact("triggers_flashback", rid))
        for g in sorted(rel.grants):
            lines.append(asp.fact("grants", rid, g))
    for g in ("girl", "boy"):
        lines.append(asp.fact("hero_type", g))
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
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale galaxy storyworld with surprise, magic, and flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guardian", choices=["mother", "father", "queen", "king"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.relic is None or c[1] == args.relic)
              and (args.gender is None or c[2] == args.gender)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, relic, gender = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(["mother", "father", "queen", "king"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, relic=relic, hero_name=name, hero_type=gender, guardian_type=guardian, trait=trait)


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    relic = RELICS[params.relic]
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, traits=[params.trait]))
    guardian = world.add(Entity(id="Guardian", kind="character", type=params.guardian_type, label=f"the {params.guardian_type}"))
    item = world.add(Entity(id="Relic", kind="thing", type=relic.kind, label=relic.label, phrase=relic.phrase, owner=hero.id, caretaker=guardian.id))
    item.meters["light"] = 0.0
    hero.memes["wonder"] = 0.0
    guardian.memes["worry"] = 0.0

    world.say(f"Once in {place.name}, there lived a {params.trait} little {hero.type} named {hero.id}.")
    world.say(f"{hero.id} loved {place.name} because it shimmered with {', '.join(sorted(place.wonders))}.")
    world.say(f"One evening, {guardian.label} gave {hero.id} {item.phrase}.")
    world.say(f"{hero.id} treasured the {item.label} and carried it as though it were a star.")

    world.para()
    world.say(f"Then a surprise came from the sky: a tiny comet dropped a kiss of light beside them.")
    guardian.memes["worry"] += 1
    hero.memes["wonder"] += 1
    item.meters["light"] += 1
    world.say(f"The {item.label} answered at once, glowing softly in {hero.id}'s hands.")

    world.para()
    if relic.triggers_flashback:
        world.facts["flashback"] = True
        world.say(f"That glow woke a flashback in {hero.id}.")
        world.say(f"{hero.id} remembered being very small, lost in a dark hall, until a kind hand held up a lantern just like this one.")
        hero.memes["fear"] = 1.0
        hero.memes["comfort"] = 1.0
        guardian.memes["worry"] += 1
        world.say(f"Now {hero.id} understood why the old light felt so gentle.")
    else:
        world.facts["flashback"] = False
        world.say(f"For a breath, {hero.id} almost remembered an old night, but the memory stayed quiet.")

    world.para()
    if relic.triggers_flashback:
        world.say(f"{hero.id} smiled through the memory and held the {item.label} higher.")
        world.say(f"The little light chased the dark away, and {guardian.label} smiled too.")
        world.say(f"Together they walked under the galaxy, and the moon garden looked kind and near.")
    else:
        world.say(f"{hero.id} lifted the relic and the garden seemed brighter than before.")
        world.say(f"{guardian.label} watched with a calm heart, and the night stayed sweet.")

    world.facts.update(hero=hero, guardian=guardian, relic=item, params=params, place=place, relic_cfg=relic)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short fairy tale for young children about a {p.hero_type} named {p.hero_name} in a galaxy garden.',
        f'Tell a gentle story with a surprise, a little magic, and a flashback set at {world.place.name}.',
        f'Write a child-friendly story where {p.hero_name} receives a magical {world.facts["relic"].label} and remembers an old moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guardian = f["guardian"]
    relic = f["relic"]
    place = f["place"].name
    qa = [
        QAItem(
            question=f"Who is the story about in {place}?",
            answer=f"The story is about a little {hero.type} named {hero.id} who lives in {place}.",
        ),
        QAItem(
            question=f"What surprise happened in {place}?",
            answer=f"A tiny comet dropped a surprise of light, and {relic.label} began to glow in {hero.id}'s hands.",
        ),
        QAItem(
            question=f"Why did {hero.id} have a flashback?",
            answer=f"{hero.id} had a flashback because the glowing {relic.label} reminded {hero.pronoun('object')} of an old night when a kind light helped.",
        ),
        QAItem(
            question=f"How did {guardian.label} feel when the magic happened?",
            answer=f"{guardian.label} felt worried at first, then calm when {hero.id} understood the memory and the light felt safe.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a galaxy?", answer="A galaxy is a huge group of stars, dust, and space that stretches far beyond one little sky."),
        QAItem(question="What is a surprise?", answer="A surprise is something unexpected that suddenly happens."),
        QAItem(question="What is magic in a fairy tale?", answer="Magic in a fairy tale is when something impossible or wondrous happens, like a glowing lantern or a talking star."),
        QAItem(question="What is a flashback?", answer="A flashback is when a character remembers something that happened before."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="moon_garden", relic="lantern", hero_name="Luna", hero_type="girl", guardian_type="queen", trait="gentle"),
    StoryParams(place="star_lane", relic="cloak", hero_name="Orin", hero_type="boy", guardian_type="father", trait="curious"),
    StoryParams(place="comet_courtyard", relic="crown", hero_name="Mira", hero_type="girl", guardian_type="mother", trait="brave"),
]


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
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for t in vals:
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
            header = f"### {p.hero_name}: {p.relic} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
