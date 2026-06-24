#!/usr/bin/env python3
"""
Standalone storyworld: swamp teamwork, foreshadowing, inner monologue, and a comic fumble.

A small source-tale shape:
- A kid and a helper go to a swamp to deliver something important.
- The mud and reeds make the task awkward, and one character fumbles.
- A little foreshadowing hints that the "perfect" tool will matter later.
- Inner monologue shows worry, then teamwork turns the mistake into a win.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the swamp"
    feature: str = "foggy boardwalk"


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    risk: str
    risk_region: str


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    object_kind: str
    seed: Optional[int] = None


HEROES = [
    ("Mina", "girl"),
    ("Theo", "boy"),
    ("Pia", "girl"),
    ("Jules", "boy"),
]
HELPERS = [
    ("Mom", "mother"),
    ("Dad", "father"),
    ("Auntie", "woman"),
    ("Uncle", "man"),
]

OBJECTS = {
    "lantern": ObjectCfg(label="lantern", phrase="a shiny little lantern", risk="splashy mud", risk_region="hands"),
    "sandwich": ObjectCfg(label="sandwich", phrase="a neat picnic sandwich", risk="muddy squish", risk_region="hands"),
    "map": ObjectCfg(label="map", phrase="a paper map with one bold red arrow", risk="wet spots", risk_region="hands"),
    "boots": ObjectCfg(label="boots", phrase="a pair of bright boots", risk="sticky muck", risk_region="feet"),
}

SETTING = Setting()

ASP_RULES = r"""
hero(H) :- hero_name(H,_).
helper(H) :- helper_name(H,_).
object(O) :- object_kind(O).

risk_region(lantern, hands).
risk_region(sandwich, hands).
risk_region(map, hands).
risk_region(boots, feet).

swampy(swamp).

fumble_possible(O) :- risk_region(O, hands).
teamwork_story(H, K, O) :- hero_name(H,_), helper_name(K,_), object_kind(O), fumble(O), foreshadow(O), teamwork(O).

#show teamwork_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("setting", "swamp"),
        asp.fact("feature", "foreshadowing"),
        asp.fact("feature", "inner_monologue"),
        asp.fact("feature", "teamwork"),
        asp.fact("style", "comedy"),
    ]
    for name, kind in HEROES:
        lines.append(asp.fact("hero_name", name, kind))
    for name, kind in HELPERS:
        lines.append(asp.fact("helper_name", name, kind))
    for obj in OBJECTS:
        lines.append(asp.fact("object_kind", obj))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show teamwork_story/3."))
    return sorted(set(asp.atoms(model, "teamwork_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    return [("swamp", h[0], o) for h in HEROES for o in OBJECTS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy swamp storyworld with teamwork and foreshadowing.")
    ap.add_argument("--place", choices=["swamp"], default="swamp")
    ap.add_argument("--hero", choices=[h[0] for h in HEROES])
    ap.add_argument("--helper", choices=[h[0] for h in HELPERS])
    ap.add_argument("--object", dest="object_kind", choices=list(OBJECTS))
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
    hero = args.hero or rng.choice([h[0] for h in HEROES])
    helper = args.helper or rng.choice([h[0] for h in HELPERS if h[0] != hero])
    obj = args.object_kind or rng.choice(list(OBJECTS))
    return StoryParams(place="swamp", hero=hero, helper=helper, object_kind=obj)


def make_world(params: StoryParams) -> dict:
    hero_type = next(k for n, k in HEROES if n == params.hero)
    helper_type = next(k for n, k in HELPERS if n == params.helper)
    obj = OBJECTS[params.object_kind]
    hero = Entity(params.hero, kind="character", type=hero_type, memes={"worry": 0.0, "hope": 0.0, "relief": 0.0})
    helper = Entity(params.helper, kind="character", type=helper_type, memes={"worry": 0.0, "hope": 0.0, "relief": 0.0})
    item = Entity(obj.label, kind="thing", type=obj.label, label=obj.label, phrase=obj.phrase, owner=hero.id,
                  meters={"clean": 1.0, "wet": 0.0, "muddy": 0.0})
    world = {
        "setting": SETTING,
        "hero": hero,
        "helper": helper,
        "item": item,
        "risk": obj.risk,
        "risk_region": obj.risk_region,
        "paragraphs": [[]],
        "facts": {
            "foreshadow": False,
            "fumble": False,
            "teamwork": False,
            "resolved": False,
            "object": obj,
        },
        "fired": set(),
    }
    return world


def say(world, text: str) -> None:
    if text:
        world["paragraphs"][-1].append(text)


def para(world) -> None:
    if world["paragraphs"][-1]:
        world["paragraphs"].append([])


def render(world) -> str:
    return "\n\n".join(" ".join(p) for p in world["paragraphs"] if p)


def inner_monologue(hero: Entity, obj: ObjectCfg) -> str:
    if obj.label == "map":
        return f"{hero.pronoun().capitalize()} thought, I am definitely following the arrows and absolutely not the frogs."
    if obj.label == "lantern":
        return f"{hero.pronoun().capitalize()} thought, If this lantern falls in the muck, it will look like a swamp sun with bad manners."
    if obj.label == "sandwich":
        return f"{hero.pronoun().capitalize()} thought, Please let the sandwich survive one tiny adventure."
    return f"{hero.pronoun().capitalize()} thought, These boots had better be smarter than the mud."


def generate_story_world(params: StoryParams):
    world = make_world(params)
    hero = world["hero"]
    helper = world["helper"]
    item = world["item"]
    obj = world["facts"]["object"]

    say(world, f"{hero.id} and {helper.id} went to the swamp on a squishy afternoon.")
    say(world, f"They carried {obj.phrase}, because the plan was to cross the boardwalk and finish one very important errand.")
    say(world, f"On the way, {hero.id} noticed a bent sign that said, 'Keep your grip.' That felt like a joke waiting to happen.")
    world["facts"]["foreshadow"] = True
    say(world, inner_monologue(hero, obj))

    para(world)
    say(world, f"The swamp made every step wobble. A heron stared at them like it had already heard the punchline.")
    say(world, f"{hero.id} tried to step over a root, but {hero.pronoun('possessive')} foot slipped and {hero.pronoun()} fumbled the {item.label}.")
    world["facts"]["fumble"] = True
    item.meters["wet"] += 1
    item.meters["muddy"] += 1
    hero.memes["worry"] += 1
    say(world, f"The {item.label} landed with a soft plop, wearing one ugly mud mustache.")

    para(world)
    say(world, f"{helper.id} laughed, not in a mean way, but in the way grown-ups laugh when trouble is trying very hard to be dramatic.")
    say(world, f"{helper.id} said, 'Teamwork time.' {hero.id} held one side, and {helper.id} held the other, and together they lifted the {item.label} onto a dry stump.")
    world["facts"]["teamwork"] = True
    if obj.label == "boots":
        say(world, f"Then they used the boots to hop the worst puddles, which was helpful because the swamp was clearly feeling extra enthusiastic.")
    else:
        say(world, f"They also tucked the {item.label} inside a spare dry bag, which had been sitting in the basket the whole time like a smug little hero.")
    hero.memes["hope"] += 1
    helper.memes["hope"] += 1

    para(world)
    world["facts"]["resolved"] = True
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    say(world, f"In the end, the errand got finished, the {item.label} stayed usable, and the swamp lost the argument.")
    say(world, f"{hero.id} grinned and thought the swamp had tried to win, but teamwork had been the bigger splash.")

    return world


def generation_prompts(world) -> list[str]:
    f = world["facts"]
    obj = f["object"]
    hero = world["hero"]
    helper = world["helper"]
    return [
        f'Write a funny story about a swamp, a fumble, and teamwork that includes the word "{obj.label}".',
        f"Tell a child-friendly comedy where {hero.id} and {helper.id} try to cross a swamp and keep {obj.phrase} safe.",
        f"Write a short story with foreshadowing and inner monologue where a muddy mistake becomes a teamwork win.",
    ]


def story_qa(world) -> list[QAItem]:
    hero = world["hero"]
    helper = world["helper"]
    item = world["item"]
    obj = world["facts"]["object"]
    return [
        QAItem(
            question=f"What did {hero.id} and {helper.id} take through the swamp?",
            answer=f"They took {obj.phrase} through the swamp.",
        ),
        QAItem(
            question=f"What problem happened when {hero.id} tried to carry the {item.label}?",
            answer=f"{hero.id} fumbled the {item.label}, and it landed in the mud.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} fix the problem?",
            answer=f"They worked together, lifted the {item.label} onto a dry stump, and kept going as a team.",
        ),
    ]


def world_knowledge_qa(world) -> list[QAItem]:
    return [
        QAItem(
            question="What is a swamp?",
            answer="A swamp is a wet place with mud, water, reeds, and lots of squishy ground.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small hint that tells you something important may happen later.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private thoughts a character has inside their head.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world) -> str:
    hero = world["hero"]
    helper = world["helper"]
    item = world["item"]
    lines = ["--- world model state ---"]
    lines.append(f"  {hero.id:8} meters={hero.meters} memes={hero.memes}")
    lines.append(f"  {helper.id:8} meters={helper.meters} memes={helper.memes}")
    lines.append(f"  {item.id:8} meters={item.meters} owner={item.owner}")
    lines.append(f"  facts={world['facts']}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="swamp", hero="Mina", helper="Mom", object_kind="map"),
    StoryParams(place="swamp", hero="Theo", helper="Dad", object_kind="lantern"),
    StoryParams(place="swamp", hero="Pia", helper="Auntie", object_kind="sandwich"),
    StoryParams(place="swamp", hero="Jules", helper="Uncle", object_kind="boots"),
]


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
    return StorySample(
        params=params,
        story=render(world),
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
        print(asp_program("#show teamwork_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show teamwork_story/3."))
        triples = sorted(set(asp.atoms(model, "teamwork_story")))
        print(f"{len(triples)} compatible story triples:\n")
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
            seed = base_seed + i
            i += 1
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} with {p.object_kind} in the swamp"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
