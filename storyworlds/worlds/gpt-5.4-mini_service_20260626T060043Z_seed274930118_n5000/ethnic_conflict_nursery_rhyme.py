#!/usr/bin/env python3
"""
storyworlds/worlds/ethnic_conflict_nursery_rhyme.py
===================================================

A small story world about a gentle ethnic conflict at a nursery-rhyme festival:
two neighboring communities, one shared song, a brief quarrel, and a child-safe
turn toward sharing.

The world is modeled as a tiny simulation with physical meters and emotional
memes. State changes drive the prose: who holds the drum, who feels crossed,
what the helper suggests, and how the ending image proves the change.

This world is intentionally narrow:
- the conflict is about a festival song, not hatred or violence
- the resolution is about turn-taking, shared rhythm, and mutual respect
- the prose style stays close to a nursery rhyme
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
# Story model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    group: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    festive: bool = True


@dataclass
class SharedThing:
    id: str
    label: str
    phrase: str
    kind: str
    can_be_held: bool = True


@dataclass
class StoryParams:
    place: str
    hero_group: str
    other_group: str
    shared_thing: str
    helper: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "village_green": Place(id="village_green", label="the village green"),
    "school_yard": Place(id="school_yard", label="the school yard"),
    "market_square": Place(id="market_square", label="the market square"),
    "river_stage": Place(id="river_stage", label="the river stage"),
}

GROUPS = {
    "hill": {
        "label": "the hill folk",
        "song": "a lilting hill song",
        "color": "gold",
    },
    "river": {
        "label": "the river folk",
        "song": "a rippling river song",
        "color": "blue",
    },
    "orchard": {
        "label": "the orchard folk",
        "song": "a bright orchard song",
        "color": "green",
    },
}

SHARED_THINGS = {
    "drum": SharedThing(id="drum", label="drum", phrase="a little hand drum", kind="music"),
    "bell": SharedThing(id="bell", label="bell", phrase="a shiny festival bell", kind="music"),
    "songbook": SharedThing(id="songbook", label="songbook", phrase="a paper songbook", kind="music"),
}

HELPERS = {
    "grandma": "grandma",
    "teacher": "teacher",
    "older_sibling": "older sibling",
}

NAMES = {
    "hill": ["Mina", "Tavi", "Luka", "Nori"],
    "river": ["Suri", "Pema", "Rina", "Kavi"],
    "orchard": ["Lio", "Anya", "Mira", "Toma"],
}


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------

def conflict_rises(world: World, hero: Entity, other: Entity, thing: Entity) -> None:
    sig = ("conflict", hero.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["cross"] = hero.memes.get("cross", 0.0) + 1
    other.memes["cross"] = other.memes.get("cross", 0.0) + 1
    thing.meters["held"] = thing.meters.get("held", 0.0) + 1


def calm_with_turns(world: World, hero: Entity, other: Entity, thing: Entity) -> None:
    sig = ("calm", hero.id)
    if sig in world.fired:
        return
    if hero.memes.get("cross", 0.0) < THRESHOLD:
        return
    world.fired.add(sig)
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    other.memes["calm"] = other.memes.get("calm", 0.0) + 1
    hero.memes["cross"] = 0.0
    other.memes["cross"] = 0.0
    thing.meters["held"] = 0.0


def propagate(world: World) -> None:
    hero = world.facts["hero"]
    other = world.facts["other"]
    thing = world.facts["thing"]
    if hero.memes.get("want", 0.0) >= THRESHOLD and other.meters.get("held", 0.0) >= THRESHOLD:
        conflict_rises(world, hero, other, thing)
    if world.facts.get("resolved"):
        calm_with_turns(world, hero, other, thing)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place: Place, hero_group: str, other_group: str, thing: SharedThing) -> bool:
    if hero_group == other_group:
        return False
    if thing.kind != "music":
        return False
    return place.festive


def explain_rejection(place: Place, hero_group: str, other_group: str, thing: SharedThing) -> str:
    if hero_group == other_group:
        return "(No story: the same community on both sides is not an ethnic conflict.)"
    if not place.festive:
        return "(No story: this place does not fit the nursery-rhyme festival shape.)"
    return f"(No story: the shared {thing.label} would not make a clear little conflict here.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Two different groups and one shared festive thing can make a gentle conflict.
different(G1,G2) :- group(G1), group(G2), G1 != G2.

valid(P,G1,G2,T) :- place(P), festive(P), different(G1,G2), thing(T), music(T).
conflict(P,G1,G2,T) :- valid(P,G1,G2,T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.festive:
            lines.append(asp.fact("festive", pid))
    for gid in GROUPS:
        lines.append(asp.fact("group", gid))
    for tid, t in SHARED_THINGS.items():
        lines.append(asp.fact("thing", tid))
        lines.append(asp.fact("music", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = {
        (p.id, g1, g2, t)
        for p in PLACES.values()
        for g1 in GROUPS
        for g2 in GROUPS
        for t in SHARED_THINGS
        if valid_combo(p, g1, g2, SHARED_THINGS[t])
    }
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combo() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(python_set - clingo_set))
    print("only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Storytelling
# ---------------------------------------------------------------------------

def build_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    other: Entity = world.facts["other"]
    helper: Entity = world.facts["helper"]
    thing: Entity = world.facts["thing"]
    place: Place = world.place
    hero_group = world.facts["hero_group"]
    other_group = world.facts["other_group"]

    hero_song = GROUPS[hero_group]["song"]
    other_song = GROUPS[other_group]["song"]

    world.say(
        f"At {place.label}, little {hero.id} from {GROUPS[hero_group]['label']} came with {hero.pronoun('possessive')} bright feet."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved {hero_song}, and {other.id} from {GROUPS[other_group]['label']} loved {other_song}."
    )
    world.say(
        f"They both saw {thing.phrase}, and each sweet voice said, 'Please let me lead the song.'"
    )

    world.para()
    hero.memes["want"] = 1.0
    other.meters["held"] = 1.0
    propagate(world)
    world.say(
        f"{hero.id} tugged a little, and {other.id} held on tight, so the tiny tune turned tense."
    )
    world.say(
        f"'{hero.id} first!' chirped one side, and '{other.id} first!' came the other, like raindrops in a pail."
    )

    if world.facts.get("resolved"):
        world.para()
        world.say(
            f"Then {helper.id} came smiling by, with a soft voice like bread and milk."
        )
        world.say(
            f"'{thing.label.capitalize()} can go around,' {helper.id} said, 'for one turn, then the next, and both songs can shine.'"
        )
        thing.meters["held"] = 0.0
        hero.memes["want"] = 0.0
        other.memes["want"] = 0.0
        propagate(world)
        world.say(
            f"So {hero.id} sang one verse, and {other.id} sang the next, while {thing.label} kept the beat."
        )
        world.say(
            f"At the end, the two groups clapped together, and the little festival sounded like one happy rhyme."
        )
    else:
        world.para()
        world.say(
            f"No one found a fair turn, so the song stayed stuck and the drum stayed still."
        )

    world.facts.update(hero=hero, other=other, helper=helper, thing=thing, resolved=True)


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    other: Entity = world.facts["other"]
    helper: Entity = world.facts["helper"]
    thing: Entity = world.facts["thing"]
    hero_group = world.facts["hero_group"]
    other_group = world.facts["other_group"]
    place: Place = world.place

    return [
        QAItem(
            question=f"Who was the little child from {GROUPS[hero_group]['label']} at {place.label}?",
            answer=f"It was {hero.id}, a little {hero.type} from {GROUPS[hero_group]['label']}.",
        ),
        QAItem(
            question=f"Why did the two sides feel cross about {thing.label}?",
            answer=(
                f"They both wanted to lead the song at once, so {hero.id} from {GROUPS[hero_group]['label']} "
                f"and {other.id} from {GROUPS[other_group]['label']} got into a small tug-of-war over {thing.label}."
            ),
        ),
        QAItem(
            question=f"Who helped the children share the song?",
            answer=f"{helper.id} helped by suggesting turns, so both groups could sing and keep the beat together.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"The quarrel turned into sharing. {hero.id} and {other.id} took turns, and the {thing.label} became part of one happy rhyme."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    hero_group = world.facts["hero_group"]
    thing: Entity = world.facts["thing"]
    return [
        QAItem(
            question="What does it mean to take turns?",
            answer="To take turns means each person gets a fair time to do something, then someone else gets a chance.",
        ),
        QAItem(
            question="Why can music help when people disagree?",
            answer="Music can help because people can listen, share a beat, and make something pretty together instead of arguing.",
        ),
        QAItem(
            question=f"What is a {thing.label} used for?",
            answer=f"A {thing.label} is used to keep rhythm, so people can sing or march together.",
        ),
        QAItem(
            question="What does ethnic mean in a child-friendly way?",
            answer="Ethnic means the story is about people from different cultural groups, each with their own songs, foods, or customs.",
        ),
        QAItem(
            question=f"What is special about {GROUPS[hero_group]['label']}?",
            answer=f"{GROUPS[hero_group]['label'].capitalize()} are one community in this story world, with their own song and color.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    other: Entity = world.facts["other"]
    thing: Entity = world.facts["thing"]
    place: Place = world.place
    return [
        f"Write a nursery-rhyme story about {hero.id} and {other.id} sharing {thing.phrase} at {place.label}.",
        f"Tell a child-safe story where two ethnic groups disagree over a {thing.label}, then make peace with turns.",
        f"Write a short rhyming story about a festival, a small conflict, and a gentle helper who teaches sharing.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.group:
            bits.append(f"group={e.group}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameter selection
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES.values():
        for g1 in GROUPS:
            for g2 in GROUPS:
                if g1 == g2:
                    continue
                for t in SHARED_THINGS:
                    if valid_combo(p, g1, g2, SHARED_THINGS[t]):
                        combos.append((p.id, g1, g2, t))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small nursery-rhyme story world about ethnic conflict and sharing."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-group", choices=GROUPS)
    ap.add_argument("--other-group", choices=GROUPS)
    ap.add_argument("--shared-thing", choices=SHARED_THINGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.hero_group:
        combos = [c for c in combos if c[1] == args.hero_group]
    if args.other_group:
        combos = [c for c in combos if c[2] == args.other_group]
    if args.shared_thing:
        combos = [c for c in combos if c[3] == args.shared_thing]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, hero_group, other_group, shared_thing = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(list(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[hero_group])
    return StoryParams(
        place=place,
        hero_group=hero_group,
        other_group=other_group,
        shared_thing=shared_thing,
        helper=helper,
        hero_name=name,
        hero_type=gender,
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    world = World(place)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        group=params.hero_group,
        meters={},
        memes={},
    ))
    other_name = random.choice([n for n in NAMES[params.other_group] if n != params.hero_name])
    other = world.add(Entity(
        id=other_name,
        kind="character",
        type="boy" if params.hero_type == "girl" else "girl",
        group=params.other_group,
        meters={},
        memes={},
    ))
    helper = world.add(Entity(
        id=HELPERS[params.helper],
        kind="character",
        type="adult",
        group="helper",
    ))
    thing = world.add(Entity(
        id=params.shared_thing,
        kind="thing",
        type="thing",
        label=SHARED_THINGS[params.shared_thing].label,
        phrase=SHARED_THINGS[params.shared_thing].phrase,
    ))

    world.facts.update(
        hero=hero,
        other=other,
        helper=helper,
        thing=thing,
        hero_group=params.hero_group,
        other_group=params.other_group,
        resolved=True,
    )

    build_story(world)

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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show conflict/4."))
    return sorted(set(asp.atoms(model, "conflict")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible story combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("village_green", "hill", "river", "drum", "grandma", "Mina", "girl"),
            StoryParams("school_yard", "river", "orchard", "bell", "teacher", "Rina", "boy"),
            StoryParams("market_square", "orchard", "hill", "songbook", "older_sibling", "Anya", "girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
