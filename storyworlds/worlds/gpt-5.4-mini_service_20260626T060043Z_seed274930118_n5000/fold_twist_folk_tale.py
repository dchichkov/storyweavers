#!/usr/bin/env python3
"""
storyworlds/worlds/fold_twist_folk_tale.py
=========================================

A small folk-tale storyworld about a fold in cloth, a twist in a path, and a
gentle resolution that changes the world state in a visible way.

Premise:
- A young hero carries a special cloth or bundle.
- A fold can hide, protect, or trap something important.
- A twist in the road or in a promise creates trouble.
- A helper, tool, or wise act can unwind the problem.

The story is simulated with entities that carry physical meters and emotional
memes. The prose is driven by those world changes rather than a fixed template.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"order": 0.0, "tangle": 0.0, "wear": 0.0, "hidden": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "worry": 0.0, "care": 0.0, "joy": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def name(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    name: str
    kind: str
    twisty: bool = False
    indoor: bool = False


@dataclass
class Bundle:
    label: str
    phrase: str
    place_in_story: str
    folded: bool = True
    valuable: bool = True


@dataclass
class TwistingForce:
    label: str
    verb: str
    effect: str
    risk: str
    can_unwind: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.twist_active: bool = False
        self.fold_active: bool = False
        self.trace_notes: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.twist_active = self.twist_active
        clone.fold_active = self.fold_active
        clone.facts = dict(self.facts)
        return clone


def _apply_fold(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "thing":
            continue
        if ent.meters.get("hidden", 0.0) >= THRESHOLD and not world.fold_active:
            sig = ("fold", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.fold_active = True
            ent.meters["hidden"] += 1
            ent.meters["order"] += 1
            out.append(f"A careful fold kept {ent.name} safe and tucked away.")
    return out


def _apply_twist(world: World) -> list[str]:
    out: list[str] = []
    if not world.twist_active:
        return out
    for hero in world.characters():
        if hero.memes["worry"] < THRESHOLD:
            continue
        sig = ("twist", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["tangle"] += 1
        out.append(f"The twist in the path made {hero.name} feel unsure.")
    return out


def _apply_unwind(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes["care"] < THRESHOLD or hero.meters["tangle"] < THRESHOLD:
            continue
        sig = ("unwind", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["tangle"] = max(0.0, hero.meters["tangle"] - 1)
        hero.memes["hope"] += 1
        out.append(f"{hero.name} found the right way to unwind the trouble.")
    return out


def _apply_resolution(world: World) -> list[str]:
    out: list[str] = []
    bundle = world.entities.get("bundle")
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not bundle or not hero or not helper:
        return out
    if bundle.meters["hidden"] < THRESHOLD or hero.meters["tangle"] >= THRESHOLD:
        return out
    sig = ("resolve",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["joy"] += 1
    helper.memes["pride"] += 1
    bundle.meters["hidden"] = 0.0
    bundle.meters["order"] += 1
    out.append(f"At last, the bundle came open, and the missing thing was found.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    rules = [_apply_fold, _apply_twist, _apply_unwind, _apply_resolution]
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in rules:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_outcome(world: World, hero: Entity, bundle: Entity, force: TwistingForce) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["worry"] += 1
    sim.get(bundle.id).meters["hidden"] += 1
    sim.twist_active = True
    propagate(sim, narrate=False)
    return {
        "tangled": sim.get(hero.id).meters["tangle"] >= THRESHOLD,
        "opened": sim.get(bundle.id).meters["hidden"] < THRESHOLD,
    }


PLACE_REGISTRY = {
    "forest": Place(name="the forest path", kind="forest", twisty=True, indoor=False),
    "hill": Place(name="the windy hill", kind="hill", twisty=True, indoor=False),
    "village": Place(name="the village lane", kind="village", twisty=False, indoor=False),
    "cottage": Place(name="the cottage room", kind="cottage", twisty=False, indoor=True),
}

BUNDLE_REGISTRY = {
    "shawl": Bundle(label="shawl", phrase="a soft wool shawl", place_in_story="around the shoulders"),
    "basket": Bundle(label="basket", phrase="a woven basket with a lid", place_in_story="by the arm"),
    "satchel": Bundle(label="satchel", phrase="a small leather satchel", place_in_story="at the side"),
}

FORCES = {
    "wind": TwistingForce(label="wind", verb="whipped", effect="twisted", risk="the bundle could slip open", can_unwind="hold it close"),
    "road": TwistingForce(label="road", verb="curved", effect="twisted", risk="the path could lead astray", can_unwind="follow the ribbon"),
    "thread": TwistingForce(label="thread", verb="snagged", effect="knotted", risk="the fold could catch", can_unwind="smooth it flat"),
}

HERO_NAMES = ["Mara", "Niko", "Anya", "Ivo", "Lina", "Bram", "Sera", "Oren"]
HELPER_NAMES = ["Grandmother", "Old Fox", "Weaver", "Brother", "Sister", "Neighbor"]
TRAITS = ["brave", "gentle", "curious", "patient", "earnest", "careful"]


@dataclass
class StoryParams:
    place: str
    bundle: str
    force: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about a fold and a twist.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--bundle", choices=BUNDLE_REGISTRY)
    ap.add_argument("--force", choices=FORCES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, p in PLACE_REGISTRY.items():
        for bundle in BUNDLE_REGISTRY:
            for force in FORCES:
                if p.twisty or force == "thread":
                    combos.append((place, bundle, force))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.bundle is None or c[1] == args.bundle)
              and (args.force is None or c[2] == args.force)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, bundle, force = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, bundle=bundle, force=force, name=name, helper=helper, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(PLACE_REGISTRY[params.place])
    force = FORCES[params.force]
    bundle_cfg = BUNDLE_REGISTRY[params.bundle]
    hero = world.add(Entity(id="hero", kind="character", type="girl", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type="woman", label=params.helper))
    bundle = world.add(Entity(id="bundle", kind="thing", type=bundle_cfg.label, label=bundle_cfg.label, phrase=bundle_cfg.phrase))
    hidden = world.add(Entity(id="hidden", kind="thing", type="secret", label="the little gift", phrase="a little gift"))
    hidden.worn_by = None

    world.say(f"Once in {world.place.name}, there was a {params.trait} child named {hero.name}.")
    world.say(f"{hero.name} carried {bundle_cfg.phrase}, folded just so, and loved how safe it felt {bundle_cfg.place_in_story}.")
    world.say(f"{helper.label} had taught {hero.name} that a good fold can keep a treasure quiet until the right hour.")

    world.para()
    world.say(f"One day, the {force.label} came along the path and began to {force.verb} everything it touched.")
    world.say(f"{hero.name} saw that the walk had a strange twist in it, and {hero.pronoun('possessive')} heart filled with worry.")
    hero.memes["worry"] += 1
    world.twist_active = True
    bundle.meters["hidden"] += 1
    hidden.meters["hidden"] += 1
    if world.place.twisty:
        world.say(f"The path itself curled like a ribbon, and the twist made the way harder to trust.")
    else:
        world.say(f"Even in the straight lane, the wind brought a twist to the day.")

    world.para()
    world.say(f"{hero.name} wanted to keep walking, but {hero.pronoun('possessive')} hands remembered the fold.")
    hero.memes["care"] += 1
    predict_outcome(world, hero, bundle, force)
    if force.can_unwind == "hold it close":
        world.say(f"So {hero.name} pressed the bundle close and tried to hold the fold firm.")
    elif force.can_unwind == "follow the ribbon":
        world.say(f"So {hero.name} looked for the ribbon of the road and followed it patiently.")
    else:
        world.say(f"So {hero.name} smoothed the cloth flat and worked gently at the knot.")

    if params.helper == "Grandmother":
        world.say(f"{helper.label} smiled and showed how a careful hand can turn a twist into a tidy line.")
    else:
        world.say(f"{helper.label} came near and offered steady hands, because no one should face a twist alone.")
    helper.memes["care"] += 1
    hero.meters["tangle"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"At last, the fold opened at the right seam, and the hidden gift came free.")
    world.say(f"{hero.name} laughed, the {force.label} lost its power, and {helper.label} watched with warm pride.")
    hero.memes["joy"] += 1
    helper.memes["pride"] += 1
    bundle.meters["hidden"] = 0.0
    world.facts.update(hero=hero, helper=helper, bundle=bundle, force=force, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    force = f["force"]
    bundle = f["bundle"]
    return [
        f'Write a short folk tale about a child named {hero.name} who keeps a {bundle.label} folded safely, then faces a twist in the road.',
        f"Tell a gentle story where {force.label} causes trouble, but a wise helper shows how to use a fold to protect a treasure.",
        f'Write a child-friendly tale that includes the words "fold" and "twist" and ends with a hidden gift being found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    bundle = f["bundle"]
    force = f["force"]
    place = world.place.name
    return [
        QAItem(
            question=f"Who was the story about in {place}?",
            answer=f"It was about a child named {hero.name} and {helper.label} who helped when the day turned tricky.",
        ),
        QAItem(
            question=f"What did {hero.name} carry that was folded carefully?",
            answer=f"{hero.name} carried {bundle.phrase}, and the fold kept it safe until the right moment.",
        ),
        QAItem(
            question=f"What caused the trouble in the story?",
            answer=f"The trouble came from the {force.label}, which made the path twist and made the day feel uncertain.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the fold opening at the right seam, the hidden gift coming free, and {hero.name} laughing happily.",
        ),
    ]


KNOWLEDGE = {
    "fold": [
        ("What is a fold?",
         "A fold is a part turned over so something can be tucked, carried, or stored neatly."),
    ],
    "twist": [
        ("What does twist mean?",
         "To twist is to turn or curl around, like a ribbon, rope, or winding path."),
    ],
    "wind": [
        ("What does wind do?",
         "Wind is moving air. It can flutter cloth, shake leaves, and push light things around."),
    ],
    "gift": [
        ("What is a gift?",
         "A gift is something given with kindness, usually without asking for anything back."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"fold", "twist", "wind", "gift"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  twist_active={world.twist_active} fold_active={world.fold_active}")
    return "\n".join(lines)


ASP_RULES = r"""
fold_safe(B) :- bundle(B), hidden(B).
twist_trouble(F) :- force(F), active_twist(F).
resolution(H,B) :- hero(H), bundle(B), fold_safe(B), cared_for(H,B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACE_REGISTRY:
        lines.append(asp.fact("place", p))
        if PLACE_REGISTRY[p].twisty:
            lines.append(asp.fact("twisty", p))
    for b in BUNDLE_REGISTRY:
        lines.append(asp.fact("bundle", b))
    for f in FORCES:
        lines.append(asp.fact("force", f))
        if f in {"wind", "road", "thread"}:
            lines.append(asp.fact("active_twist", f))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("cared_for", "hero", "bundle"))
    lines.append(asp.fact("hidden", "bundle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show fold_safe/1. #show twist_trouble/1. #show resolution/2."))
    _ = model
    print("OK: ASP program loaded and solved.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show twist_trouble/1."))
    return sorted(set(asp.atoms(model, "twist_trouble")))


def asp_valid_stories() -> list[tuple]:
    return []


def explain_rejection(_: object, __: object) -> str:
    return "(No story: this folk tale needs a real fold-and-twist tension to be worth telling.)"


def explain_gender(_: str, __: str) -> str:
    return "(No story: this world does not use gender as a gate.)"


CURATED = [
    StoryParams(place="forest", bundle="shawl", force="wind", name="Mara", helper="Grandmother", trait="careful"),
    StoryParams(place="hill", bundle="basket", force="road", name="Niko", helper="Weaver", trait="curious"),
    StoryParams(place="village", bundle="satchel", force="thread", name="Anya", helper="Neighbor", trait="gentle"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACE_REGISTRY))
    bundle = args.bundle or rng.choice(list(BUNDLE_REGISTRY))
    force = args.force or rng.choice(list(FORCES))
    if place not in PLACE_REGISTRY or bundle not in BUNDLE_REGISTRY or force not in FORCES:
        raise StoryError("(Invalid options.)")
    if not PLACE_REGISTRY[place].twisty and force != "thread":
        raise StoryError("(No story: this place needs a twisty force for the folk-tale turn.)")
    return StoryParams(
        place=place,
        bundle=bundle,
        force=force,
        name=args.name or rng.choice(HERO_NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def build_storyworld_args() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolution/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show twist_trouble/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n, 1)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
            if len(samples) >= args.n:
                break

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
            header = f"### {p.name}: {p.bundle} with {p.force} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
