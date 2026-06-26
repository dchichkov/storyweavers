#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a true fling that turns into a conflict
and is resolved with a kind act, a returned token, or a gentle choice.

This world builds a tiny causal model:
- a hero has a true wish
- the hero flings a simple object or charm
- the fling can upset another character or break a trust
- conflict rises
- a fair compromise or apology restores peace
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

SETTING_WILD = "wildwood"
SETTING_CASTLE = "castle"
SETTING_POND = "pond"
SETTING_HUT = "hut"

PLACE_REGISTRY = {
    SETTING_WILD: {
        "name": "the wildwood",
        "detail": "The trees stood close together, and the moss made the path soft underfoot.",
        "kind": "forest",
    },
    SETTING_CASTLE: {
        "name": "the castle garden",
        "detail": "The castle garden glowed with silver roses and a little stone fountain.",
        "kind": "garden",
    },
    SETTING_POND: {
        "name": "the moonlit pond",
        "detail": "The pond was still as glass, with reeds leaning over the dark water.",
        "kind": "pond",
    },
    SETTING_HUT: {
        "name": "the little hut",
        "detail": "The little hut had a warm fire and a round table by the window.",
        "kind": "home",
    },
}

CHARACTER_NAMES = ["Ayla", "Bram", "Cora", "Drew", "Elin", "Finn", "Gwen", "Hugo"]
CHARACTER_TITLES = ["princess", "prince", "witch", "knight", "goat-herd", "child", "fairy", "bard"]
CHARACTER_TRAITS = ["gentle", "brave", "small", "curious", "bright", "earnest", "stubborn"]

FLING_OBJECTS = {
    "pebble": {
        "label": "pebble",
        "phrase": "a smooth pebble",
        "verb": "fling the pebble",
        "result": "splashed into the pond",
        "risk": "made the quiet place loud",
    },
    "apple": {
        "label": "apple core",
        "phrase": "an apple core",
        "verb": "fling the apple core",
        "result": "bounced off the fountain",
        "risk": "upset the garden spirits",
    },
    "ribbon": {
        "label": "ribbon",
        "phrase": "a bright ribbon",
        "verb": "fling the ribbon",
        "result": "wrapped around a thorny branch",
        "risk": "shamed the guest who had gifted it",
    },
    "bone": {
        "label": "bone",
        "phrase": "a little bone",
        "verb": "fling the bone",
        "result": "skittered under the table",
        "risk": "angered a watchful hound",
    },
}

GIFTS = {
    "lantern": {
        "label": "lantern",
        "phrase": "a tiny lantern",
        "value": "warm light",
        "type": "object",
    },
    "key": {
        "label": "key",
        "phrase": "a silver key",
        "value": "a locked door",
        "type": "token",
    },
    "flower": {
        "label": "flower",
        "phrase": "a blue flower",
        "value": "a promise",
        "type": "token",
    },
}

HELPERS = {
    "owl": {
        "label": "owl",
        "role": "wise owl",
        "aid": "showed the way",
    },
    "miller": {
        "label": "miller",
        "role": "kind miller",
        "aid": "offered a cup of milk",
    },
    "queen": {
        "label": "queen",
        "role": "queen",
        "aid": "listened with a calm face",
    },
}

ASP_RULES = r"""
true_wish(H) :- hero(H), wished_truth(H).
has_fling(H,O) :- hero(H), fling_obj(O), used_fling(H,O).
conflict(H) :- has_fling(H,O), upset(O).
resolved(H) :- conflict(H), apology(H).
"""

@dataclass
class StoryParams:
    place: str
    fling_obj: str
    gift: str
    helper: str
    name: str
    title: str
    trait: str
    seed: Optional[int] = None

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters.setdefault("distance", 0.0)
        self.meters.setdefault("damage", 0.0)
        self.memes.setdefault("truth", 0.0)
        self.memes.setdefault("conflict", 0.0)
        self.memes.setdefault("joy", 0.0)

@dataclass
class World:
    place: dict
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

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

    def copy(self) -> "World":
        import copy
        return World(self.place, entities=copy.deepcopy(self.entities), paragraphs=[[]], facts=dict(self.facts), fired=set(self.fired), trace=list(self.trace))

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a true fling and a conflict.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--fling-obj", dest="fling_obj", choices=FLING_OBJECTS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name", choices=CHARACTER_NAMES)
    ap.add_argument("--title", choices=CHARACTER_TITLES)
    ap.add_argument("--trait", choices=CHARACTER_TRAITS)
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

def valid_combos() -> list[tuple[str, str, str, str]]:
    return [
        (p, o, g, h)
        for p in PLACE_REGISTRY
        for o in FLING_OBJECTS
        for g in GIFTS
        for h in HELPERS
    ]

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACE_REGISTRY))
    fling_obj = args.fling_obj or rng.choice(list(FLING_OBJECTS))
    gift = args.gift or rng.choice(list(GIFTS))
    helper = args.helper or rng.choice(list(HELPERS))
    name = args.name or rng.choice(CHARACTER_NAMES)
    title = args.title or rng.choice(CHARACTER_TITLES)
    trait = args.trait or rng.choice(CHARACTER_TRAITS)
    return StoryParams(place=place, fling_obj=fling_obj, gift=gift, helper=helper, name=name, title=title, trait=trait)

def _hero(world: World, params: StoryParams) -> Entity:
    return world.add(Entity(id="hero", kind="character", label=params.name, phrase=f"{params.trait} {params.title} {params.name}"))

def _other(world: World, params: StoryParams) -> Entity:
    return world.add(Entity(id="other", kind="character", label="other", phrase=""))

def _helper_entity(world: World, params: StoryParams) -> Entity:
    info = HELPERS[params.helper]
    return world.add(Entity(id="helper", kind="character", label=info["role"], phrase=info["role"]))

def generate_story(world: World, params: StoryParams) -> None:
    place = PLACE_REGISTRY[params.place]
    fling = FLING_OBJECTS[params.fling_obj]
    gift = GIFTS[params.gift]
    helper = HELPERS[params.helper]
    hero = _hero(world, params)
    other = _other(world, params)
    wise = _helper_entity(world, params)
    hero.memes["truth"] += 1.0
    world.say(f"Once in {place['name']}, there lived a {params.trait} {params.title} named {params.name}.")
    world.say(f"{params.name} had a true wish: to do the right thing, even when the day grew strange.")
    world.say(f"One day, {params.name} held {fling['phrase']} and chose to {fling['verb']}.")
    hero.meters["distance"] += 1.0
    hero.meters["damage"] += 0.0
    world.facts["wished_truth"] = True
    world.facts["used_fling"] = True
    if params.fling_obj == "ribbon":
        other.memes["conflict"] += 1.0
        world.say(f"The ribbon {fling['result']}, and that {fling['risk']}.")
    elif params.fling_obj == "apple":
        other.memes["conflict"] += 1.0
        world.say(f"The core {fling['result']}, and that {fling['risk']}.")
    elif params.fling_obj == "bone":
        other.memes["conflict"] += 1.0
        world.say(f"The bone {fling['result']}, and that {fling['risk']}.")
    else:
        other.memes["conflict"] += 1.0
        world.say(f"The pebble {fling['result']}, and that {fling['risk']}.")
    world.para()
    world.say(f"{place['detail']}")
    world.say(f"{helper['role'].capitalize()} {helper['aid']}, and {params.name} felt the first pinch of conflict in the chest.")
    world.say(f"Then {params.name} spoke a true apology and set down the wrong thing.")
    world.facts["apology"] = True
    other.memes["conflict"] = max(0.0, other.memes["conflict"] - 1.0)
    hero.memes["joy"] += 1.0
    world.para()
    world.say(f"To make amends, {params.name} gave {gift['phrase']} as a gentle gift.")
    world.say(f"The gift brought {gift['value']}, and the conflict melted away.")
    world.say(f"In the end, {params.name} kept the true wish close and walked home under a calm sky.")

def generate(params: StoryParams) -> StorySample:
    world = World(place=PLACE_REGISTRY[params.place])
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )

def generation_prompts(world: World) -> list[str]:
    p = world.facts
    return [
        "Write a short fairy tale about a true wish, a fling, and a conflict that ends in peace.",
        f"Tell a child-friendly story set in {world.place['name']} where a hero makes a mistake, apologizes, and restores harmony.",
        "Write a simple story where a small fling causes trouble but a kind helper helps solve the conflict.",
    ]

def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What was the hero's true wish?",
            answer="The hero's true wish was to do the right thing, even when the day grew strange.",
        ),
        QAItem(
            question="What caused the conflict?",
            answer=f"The conflict began when the hero chose to fling a {world.facts.get('fling_obj', 'small object')} and it upset the other character.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The hero apologized, made amends with a gentle gift, and the conflict melted away.",
        ),
    ]

def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a true wish in a fairy tale?",
            answer="A true wish is a wish that comes from the heart and guides a character toward honest, kind choices.",
        ),
        QAItem(
            question="Why can a fling cause trouble?",
            answer="A fling can cause trouble if something is thrown carelessly and upsets another character or disturbs a peaceful place.",
        ),
        QAItem(
            question="What helps end a conflict in a fairy tale?",
            answer="An apology, a kind gift, or a careful promise can help end a conflict and bring peace back.",
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

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACE_REGISTRY:
        lines.append(asp.fact("place", p))
    for o in FLING_OBJECTS:
        lines.append(asp.fact("fling_obj", o))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show true_wish/1.\n#show has_fling/2.\n#show conflict/1.\n#show resolved/1."))
    atoms = set((sym.name, tuple(a.number if a.type == a.type.Number else a.string if a.type == a.type.String else a.name for a in sym.arguments)) for sym in model)
    if any(name == "true_wish" for name, _ in atoms):
        print("OK: ASP model produced.")
        return 0
    print("MISMATCH: ASP model empty.")
    return 1

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))

CURATED = [
    StoryParams(place=SETTING_CASTLE, fling_obj="ribbon", gift="flower", helper="queen", name="Ayla", title="princess", trait="gentle"),
    StoryParams(place=SETTING_POND, fling_obj="pebble", gift="lantern", helper="owl", name="Bram", title="knight", trait="curious"),
    StoryParams(place=SETTING_HUT, fling_obj="bone", gift="key", helper="miller", name="Cora", title="witch", trait="earnest"),
]

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show true_wish/1.\n#show has_fling/2.\n#show conflict/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show true_wish/1.\n#show has_fling/2.\n#show conflict/1.\n#show resolved/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
