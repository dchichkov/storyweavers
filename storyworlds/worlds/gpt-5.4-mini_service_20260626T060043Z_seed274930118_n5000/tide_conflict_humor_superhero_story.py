#!/usr/bin/env python3
"""
Superhero tide conflict humor storyworld.

A small, self-contained simulation about a kid hero whose big idea meets a
tricky tide, a little conflict, and a funny fix.
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

TIDE_LEVELS = {"low", "rising", "high"}
MOODS = {"calm", "proud", "worried", "embarrassed", "brave", "gleeful"}


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
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they" if self.plural else "it",
                "object": "them" if self.plural else "it",
                "possessive": "their" if self.plural else "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Shore:
    place: str = "the harbor"
    tide: str = "rising"


@dataclass
class Cape:
    label: str
    phrase: str
    protects: set[str]
    gear_name: str


@dataclass
class HeroConfig:
    name: str
    gender: str
    role: str
    trait: str


@dataclass
class StoryParams:
    shore: str
    tide: str
    cape: str
    name: str
    gender: str
    role: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, shore: Shore) -> None:
        self.shore = shore
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def _hero_title(role: str) -> str:
    return {"kid": "kid hero", "girl": "girl hero", "boy": "boy hero"}.get(role, role)


HERO_TRAITS = ["brave", "silly", "quick", "clever", "sparkly"]
NAMES = ["Nova", "Milo", "Jade", "Piper", "Zane", "Ruby", "Theo", "Iris"]


HELMETS = {
    "bubble_helmet": Cape(label="bubble helmet", phrase="a shiny bubble helmet", protects={"head"}, gear_name="bubble helmet"),
    "tide_boots": Cape(label="tide boots", phrase="tall tide boots", protects={"feet"}, gear_name="tide boots"),
    "cape_cloak": Cape(label="cape-cloak", phrase="a wind-fluttering cape-cloak", protects={"back"}, gear_name="cape-cloak"),
}

SHORES = {
    "harbor": Shore(place="the harbor", tide="rising"),
    "pier": Shore(place="the pier", tide="high"),
    "beach": Shore(place="the beach", tide="rising"),
}

ASP_RULES = r"""
hero(H) :- hero_name(H).
danger(D) :- tide(D).
need_fix(H) :- hero(H), conflict(H).
compatible(G,H) :- gear(G), hero(H), protects(G,R), at_risk(H,R).
solved(H) :- need_fix(H), compatible(_,H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sname in SHORES:
        lines.append(asp.fact("shore", sname))
    for tide in TIDE_LEVELS:
        lines.append(asp.fact("tide", tide))
    for gid, gear in HELMETS.items():
        lines.append(asp.fact("gear", gid))
        for r in sorted(gear.protects):
            lines.append(asp.fact("protects", gid, r))
    lines.append(asp.fact("at_risk", "hero", "feet"))
    lines.append(asp.fact("conflict", "hero"))
    lines.append(asp.fact("hero_name", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero tide conflict humor storyworld.")
    ap.add_argument("--shore", choices=sorted(SHORES))
    ap.add_argument("--tide", choices=sorted(TIDE_LEVELS))
    ap.add_argument("--cape", choices=sorted(HELMETS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--role", choices=["kid", "girl", "boy"])
    ap.add_argument("--trait", choices=HERO_TRAITS)
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
    shore = args.shore or rng.choice(sorted(SHORES))
    tide = args.tide or rng.choice(sorted(TIDE_LEVELS))
    if tide == "low":
        tide = "rising"
    cape = args.cape or rng.choice(sorted(HELMETS))
    gender = args.gender or rng.choice(["girl", "boy"])
    role = args.role or "kid"
    if role == "kid":
        role = gender
    trait = args.trait or rng.choice(HERO_TRAITS)
    name = args.name or rng.choice(NAMES)
    if cape == "tide_boots" and tide == "low":
        raise StoryError("Tide boots would not matter at low tide; the story would not have a real problem.")
    return StoryParams(shore=shore, tide=tide, cape=cape, name=name, gender=gender, role=role, trait=trait)


def generate(params: StoryParams) -> StorySample:
    shore = SHORES[params.shore]
    cape = HELMETS[params.cape]
    w = World(shore)

    hero = w.add(Entity(id="hero", kind="character", type=params.gender, label=params.name))
    parent = w.add(Entity(id="parent", kind="character", type="adult", label="Captain Tidewise"))
    gear = w.add(Entity(id="gear", type="gear", label=cape.label, phrase=cape.phrase, owner=hero.id))

    gear.worn_by = hero.id
    hero.memes["brave"] = 1
    hero.memes["humor"] = 1

    w.say(
        f"{params.name} was a {params.trait} { _hero_title(params.role) } who loved to help like a tiny superhero."
    )
    w.say(
        f"At {shore.place}, the tide was {shore.tide}, and {params.name} could hear the waves making splashy whoosh-sounds."
    )
    w.say(
        f"{params.name} wanted to dash in and save a lost toy boat, but {parent.label} frowned. "
        f'"Not without a plan," {parent.pronoun("subject")} said.'
    )
    hero.memes["conflict"] = 1
    w.say(
        f"{params.name} crossed {hero.pronoun('possessive')} arms. " 
        f'"But the boat is waving at me!" {hero.pronoun("subject")} said, which was funny enough to make even the gulls sound like they were giggling.'
    )

    if params.cape == "tide_boots":
        w.say(
            f"Then {parent.label} held up {gear.phrase} and said, "
            f'"Try these tide boots. They will keep your feet dry while you do your hero job."'
        )
        hero.memes["conflict"] = 0
        hero.memes["gleeful"] = 1
        w.say(
            f"{params.name} stomped into the water, splashed like a brave drum, and rescued the toy boat without soggy socks. "
            f"{params.name} laughed so hard that the boat seemed to bob along with the joke."
        )
        w.say(
            f"At the end, {params.name} was a wet but happy superhero, and the tide boots were still doing their tidy job."
        )
    else:
        w.say(
            f"Then {parent.label} pointed to {gear.phrase} and said, "
            f'"A cape is great, but your feet still need something for the tide."'
        )
        hero.memes["embarrassed"] = 1
        w.say(
            f"{params.name} snorted at {hero.pronoun('possessive')} own mistake, because even heroes sometimes forget the feet part. "
            f"So {params.name} waited, laughed at the silly plan, and used the cape only when the wave slid back."
        )
        w.say(
            f"In the end, the boat was saved, the joke was fixed, and the tide could not make a mess of {params.name}'s grand superhero smile."
        )

    w.facts.update(hero=hero, parent=parent, gear=gear, params=params, shore=shore)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_qa(w),
        world=w,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short superhero story for a child where "{p.tide}" tide causes a funny conflict.',
        f"Tell a gentle adventure story about {p.name} the tiny hero at {world.facts['shore'].place}.",
        f'Write a story with a tide, a superhero problem, and a humorous happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    shore = world.facts["shore"]
    gear = world.facts["gear"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.name}, a {p.trait} little superhero at {shore.place}.",
        ),
        QAItem(
            question=f"What problem did {p.name} face at {shore.place}?",
            answer=f"The tide was {shore.tide}, and that made it tricky for {p.name} to rush in and save the toy boat.",
        ),
        QAItem(
            question=f"How did the gear help in the end?",
            answer=f"{gear.phrase} helped {p.name} stay ready for the water while solving the problem without a soggy mistake.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tide?",
            answer="A tide is the regular rising and falling of the sea along the shore.",
        ),
        QAItem(
            question="Why can tides make rescue jobs tricky?",
            answer="Tides can change where the water is, so a place that feels safe one moment can be splashy or deep the next.",
        ),
        QAItem(
            question="Why is humor helpful in a story?",
            answer="Humor helps make a worried moment feel lighter, so the characters can laugh and keep trying.",
        ),
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
    lines.append("== (3) World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} label={e.label} worn_by={e.worn_by} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(shore="harbor", tide="rising", cape="tide_boots", name="Nova", gender="girl", role="kid", trait="brave"),
    StoryParams(shore="pier", tide="high", cape="cape_cloak", name="Milo", gender="boy", role="kid", trait="silly"),
    StoryParams(shore="beach", tide="rising", cape="bubble_helmet", name="Jade", gender="girl", role="kid", trait="clever"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SHORES:
        for t in TIDE_LEVELS:
            for c in HELMETS:
                if t == "low" and c == "tide_boots":
                    continue
                out.append((s, t, c))
    return out


def explain_rejection(tide: str, cape: str) -> str:
    if tide == "low" and cape == "tide_boots":
        return "No story: tide boots do not create a real superhero problem when the tide is low."
    return "No story: that combination does not make a believable tide conflict."


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
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


ASP_RULES = r"""
valid(S,T,C) :- shore(S), tide(T), gear(C), not bad(T,C).
bad(low,tide_boots).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_asp_list() -> str:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    rows = sorted(set(asp.atoms(model, "valid")))
    return "\n".join(f"{a} {b} {c}" for a, b, c in rows)


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
        print(build_asp_list())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: tide={p.tide}, shore={p.shore}, gear={p.cape}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
