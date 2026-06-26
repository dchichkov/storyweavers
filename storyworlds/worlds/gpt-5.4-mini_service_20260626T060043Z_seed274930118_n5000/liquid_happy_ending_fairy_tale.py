#!/usr/bin/env python3
"""
storyworlds/worlds/liquid_happy_ending_fairy_tale.py
====================================================

A small fairy-tale storyworld about a child, a precious liquid, and a happy
ending.

Premise:
- A young hero carries a magical liquid in a glass vial for someone who needs it.
- The liquid is special: it can heal a fading lantern, a wilted flower, or a
  tired river spirit, but only if it stays clean and full.
- The hero wants to hurry, but the path is tricky and the vial can slip.

Turn:
- The hero fears the liquid will spill.
- A helper or wise elder notices the risk and offers a safer container or a
  careful route.
- The hero chooses caution, and the liquid stays safe.

Resolution:
- The liquid reaches its destination.
- What was fading becomes bright again.
- The story ends with a clear happy image proving the good change.

This world intentionally stays small and constraint-checked: every generated
story is a simple fairy tale with one liquid, one risk, one turn, and one happy
ending.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "woman"}
        male = {"boy", "prince", "king", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    description: str
    route: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Liquid:
    id: str
    label: str
    phrase: str
    purpose: str
    risk: str
    brightness: str
    needed_by: str
    color: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Container:
    id: str
    label: str
    phrase: str
    protects: bool
    gentle: bool
    capacity: int
    fit_for: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def maybe_article(text: str) -> str:
    return text if text.startswith(("a ", "an ", "the ")) else f"a {text}"


def join_list(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f", and {items[-1]}"


PLACES = {
    "moon_garden": Place(
        name="the moon garden",
        description="The moon garden glowed silver, and sleepy flowers lifted their heads.",
        route="along the lantern path",
        affords={"carry", "pour", "heal"},
    ),
    "forest_well": Place(
        name="the forest well",
        description="The forest well hid beneath old roots, cool and deep.",
        route="through the fern path",
        affords={"carry", "pour", "heal"},
    ),
    "castle_hall": Place(
        name="the castle hall",
        description="The castle hall sparkled under tall windows and painted beams.",
        route="down the marble corridor",
        affords={"carry", "pour", "heal"},
    ),
}

LIQUIDS = {
    "moon_drops": Liquid(
        id="moon_drops",
        label="moon drops",
        phrase="a small crystal bottle of moon drops",
        purpose="wake a sleepy lantern",
        risk="spill",
        brightness="bright and silver",
        needed_by="the lantern",
        color="silver",
        tags={"moon", "light", "liquid"},
    ),
    "rose_syrup": Liquid(
        id="rose_syrup",
        label="rose syrup",
        phrase="a glass vial of rose syrup",
        purpose="help a wilted flower stand tall again",
        risk="spill",
        brightness="sweet and rosy",
        needed_by="the flower",
        color="pink",
        tags={"rose", "flower", "liquid"},
    ),
    "star_water": Liquid(
        id="star_water",
        label="star water",
        phrase="a tiny bottle of star water",
        purpose="wake a tired river sprite",
        risk="drip away",
        brightness="clear and shining",
        needed_by="the sprite",
        color="clear",
        tags={"star", "water", "liquid"},
    ),
}

CONTAINERS = {
    "crystal_bottle": Container(
        id="crystal_bottle",
        label="a crystal bottle",
        phrase="a crystal bottle with a tight stopper",
        protects=True,
        gentle=True,
        capacity=1,
        fit_for={"moon_drops", "rose_syrup", "star_water"},
    ),
    "woven_cup": Container(
        id="woven_cup",
        label="a woven cup",
        phrase="a woven cup lined with wax",
        protects=True,
        gentle=True,
        capacity=1,
        fit_for={"rose_syrup", "star_water"},
    ),
    "old_jug": Container(
        id="old_jug",
        label="an old jug",
        phrase="an old jug with a wide handle",
        protects=False,
        gentle=False,
        capacity=2,
        fit_for={"moon_drops", "rose_syrup", "star_water"},
    ),
}

HEROES = {
    "girl": ["Mira", "Lina", "Tessa", "Nora", "Elena"],
    "boy": ["Finn", "Owen", "Perry", "Theo", "Robin"],
}

HELPERS = [
    ("fairy", "a tiny fairy"),
    ("grandmother", "a wise grandmother"),
    ("fox", "a clever fox"),
    ("knight", "a gentle knight"),
]

TRAITS = ["brave", "kind", "curious", "careful", "gentle"]


@dataclass
class StoryParams:
    place: str
    liquid: str
    helper: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def liquid_at_risk(liquid: Liquid) -> bool:
    return True


def select_container(liquid: Liquid) -> Optional[Container]:
    for cont in CONTAINERS.values():
        if liquid.id in cont.fit_for and cont.protects:
            return cont
    return None


def explain_rejection(liquid: Liquid) -> str:
    return f"(No story: {liquid.label} has no safe container in this world.)"


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    liquid = world.get("liquid")
    container = world.get("container")
    if hero.meters.get("hurry", 0) < THRESHOLD:
        return out
    if not container.carried_by == hero.id:
        return out
    if not container.meters.get("safe", 0):
        sig = ("spill", liquid.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        liquid.meters["risk"] = liquid.meters.get("risk", 0) + 1
        out.append(f"The liquid trembled in the container.")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_risk(world: World, hero: Entity) -> bool:
    sim = world.copy()
    sim.get("hero").meters["hurry"] = 1
    propagate(sim, narrate=False)
    return sim.get("liquid").meters.get("risk", 0) >= THRESHOLD


def tell(place: Place, liquid: Liquid, helper_kind: str, name: str, gender: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name, meters={}, memes={}))
    helper_label = dict(HELPERS)[helper_kind]
    helper = world.add(Entity(id="helper", kind="character", type=helper_kind, label=helper_label, meters={}, memes={}))
    liq = world.add(Entity(id="liquid", type="liquid", label=liquid.label, phrase=liquid.phrase, owner="hero", caretaker="hero", meters={"full": 1}, memes={}))
    cont_def = select_container(liquid)
    if cont_def is None:
        raise StoryError(explain_rejection(liquid))
    cont = world.add(Entity(
        id="container",
        type="container",
        label=cont_def.label,
        phrase=cont_def.phrase,
        owner="hero",
        caretaker="hero",
        carried_by="hero",
        meters={"safe": 1 if cont_def.protects else 0},
        memes={},
    ))
    world.facts.update(place=place, liquid=liq, container=cont, hero=hero, helper=helper, trait=trait, helper_kind=helper_kind, liquid_def=liquid)

    world.say(f"Once in {place.name}, there lived a {trait} young {gender} named {name}.")
    world.say(f"{name} carried {liquid.phrase} because it could {liquid.purpose}.")
    world.say(f"{place.description}")

    world.para()
    world.say(f"{name} followed {place.route}, but the path had a trick: one wrong step could make the liquid {liquid.risk}.")
    hero.meters["hurry"] = 1
    if predict_risk(world, hero):
        world.say(f"{name} slowed down, for {name.lower()} could tell the {liquid.label} was in danger.")
        world.say(f"Then {helper_label} came near and said, “Use {cont_def.label} and take your time.”")
        helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
        hero.meters["careful"] = 1
        hero.meters["hurry"] = 0
    else:
        world.say(f"{name} kept going, and the little bottle stayed steady.")

    world.para()
    if cont_def.gentle:
        world.say(f"{name} held the {cont_def.label} with both hands and walked the rest of {place.route}.")
        liq.meters["delivered"] = 1
        world.say(f"At the end, {liquid.label} reached {liquid.needed_by} and became {liquid.brightness}.")
        world.say(f"The {liquid.needed_by} shone again, and everyone smiled at the happy ending.")
        hero.memes["joy"] = 1
        helper.memes["joy"] = 1
    else:
        world.say(f"The container was not wise enough for such a precious liquid, so the tale would not be fair.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    liquid = f["liquid_def"]
    return [
        f'Write a short fairy tale for a young child about a "{liquid.label}" that must reach its destination safely.',
        f"Tell a gentle story in which {f['hero'].label} carries {liquid.phrase} and a helper warns them not to rush.",
        f'Write a happy-ending fairy tale using the word "{liquid.color}" and a careful journey through {f["place"].name}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    liquid = f["liquid_def"]
    cont = f["container"]
    place = f["place"]
    return [
        QAItem(
            question=f"What was {hero.label} carrying in {place.name}?",
            answer=f"{hero.label} was carrying {liquid.phrase}. It was special because it could {liquid.purpose}.",
        ),
        QAItem(
            question=f"Why did {hero.label} slow down on the path?",
            answer=f"{hero.label} slowed down because the liquid could {liquid.risk} on the way, and {helper.label} reminded them to be careful.",
        ),
        QAItem(
            question=f"How did the {cont.label} help the story end well?",
            answer=f"The {cont.label} kept the liquid safe, so it reached {liquid.needed_by} and the tale ended happily.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    liquid = f["liquid_def"]
    qs = [
        QAItem(
            question="What is a liquid?",
            answer="A liquid is a substance that can pour, flow, and take the shape of its container.",
        ),
        QAItem(
            question="Why do some bottles have stoppers?",
            answer="Some bottles have stoppers so the liquid inside does not spill out while it is carried.",
        ),
        QAItem(
            question="What does it mean to be careful?",
            answer="Being careful means moving gently and paying attention so something precious does not get hurt or lost.",
        ),
    ]
    if "water" in liquid.tags:
        qs.append(QAItem(
            question="What is water?",
            answer="Water is a clear liquid that people, animals, and plants need for life.",
        ))
    return qs


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.carried_by:
            parts.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="moon_garden", liquid="moon_drops", helper="fairy", name="Mira", gender="girl", trait="careful"),
    StoryParams(place="forest_well", liquid="star_water", helper="grandmother", name="Finn", gender="boy", trait="kind"),
    StoryParams(place="castle_hall", liquid="rose_syrup", helper="fox", name="Elena", gender="girl", trait="gentle"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for lid, liquid in LIQUIDS.items():
        lines.append(asp.fact("liquid", lid))
        lines.append(asp.fact("liquid_color", lid, liquid.color))
        lines.append(asp.fact("liquid_needed_by", lid, liquid.needed_by))
    for cid, cont in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        if cont.protects:
            lines.append(asp.fact("protects", cid))
        if cont.gentle:
            lines.append(asp.fact("gentle", cid))
        for lid in sorted(cont.fit_for):
            lines.append(asp.fact("fits", cid, lid))
    return "\n".join(lines)


ASP_RULES = r"""
safe_container(C, L) :- protects(C), fits(C, L), gentle(C).
valid_story(P, L, C) :- place(P), liquid(L), container(C), affords(P, carry), safe_container(C, L).
#show valid_story/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((p, l, c) for p in PLACES for l in LIQUIDS for c in CONTAINERS if CONTAINERS[c].protects and CONTAINERS[c].gentle and l in CONTAINERS[c].fit_for and "carry" in PLACES[p].affords)
    cl = asp_valid_stories()
    if set(py) == set(cl):
        print(f"OK: ASP matches Python ({len(py)} valid stories).")
        return 0
    print("Mismatch between ASP and Python")
    print("python-only:", sorted(set(py) - set(cl)))
    print("asp-only:", sorted(set(cl) - set(py)))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a liquid and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--liquid", choices=LIQUIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=[k for k, _ in HELPERS])
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(PLACES))
    liquid = args.liquid or rng.choice(list(LIQUIDS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HEROES[gender])
    helper = args.helper or rng.choice([k for k, _ in HELPERS])
    trait = args.trait or rng.choice(TRAITS)
    if liquid not in LIQUIDS:
        raise StoryError("Unknown liquid.")
    if place not in PLACES:
        raise StoryError("Unknown place.")
    if helper not in dict(HELPERS):
        raise StoryError("Unknown helper.")
    return StoryParams(place=place, liquid=liquid, helper=helper, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], LIQUIDS[params.liquid], params.helper, params.name, params.gender, params.trait)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{t}" for t in asp_valid_stories()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
