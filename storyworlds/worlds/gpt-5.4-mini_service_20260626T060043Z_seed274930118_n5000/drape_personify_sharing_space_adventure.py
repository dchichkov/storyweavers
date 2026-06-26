#!/usr/bin/env python3
"""
storyworlds/worlds/drape_personify_sharing_space_adventure.py
==============================================================

A small classical story world in a Space Adventure style.

Seed premise:
- A child astronaut or space helper is on a station or ship.
- They want to keep a fragile shared thing cozy or private in space.
- They drape a cover over a seat, hatch, or sleeping pod.
- Someone personifies a shared object or helper-bot, making the scene warm.
- The story turns on sharing space fairly, then ends with a calm, cooperative image.

This world keeps a tight, constraint-checked set of plausible variants:
sharing a bunk, sharing a viewing window, sharing a telescope, or sharing a
drift pod. The prose is driven by simulated meters and memes, not a frozen
template swap.
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
    shared_with: set[str] = field(default_factory=set)
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"comfort": 0.0, "mess": 0.0, "use": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "care": 0.0, "sharing": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "pilot"}
        male = {"boy", "man", "father", "captain"}
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
    kind: str
    shared_spots: list[str]
    outer: str


@dataclass
class Object:
    id: str
    label: str
    phrase: str
    target: str
    shareable: bool
    needs_drape: bool = False
    plural: bool = False


@dataclass
class Drape:
    id: str
    label: str
    phrase: str
    covers: set[str]
    softens: set[str]


@dataclass
class StoryParams:
    place: str
    object: str
    drape: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_events: list[str] = []

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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def shared_entities(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if actor.id in e.shared_with]


def _r_comfort(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.meters["comfort"] >= THRESHOLD and ent.id not in world.fired:
            world.fired.add((ent.id, "comfort"))
            out.append(f"{ent.label} looked cozier at once.")
    return out


def _r_share(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.memes["sharing"] < THRESHOLD:
            continue
        for other in world.entities.values():
            if other.id == ent.id:
                continue
            sig = ("share", ent.id, other.id)
            if sig in world.fired:
                continue
            if other.owner == ent.id or ent.owner == other.id:
                continue
            if other.kind == "character":
                world.fired.add(sig)
                out.append(f"They made room for each other.")
    return out


CAUSAL_RULES = [
    _r_comfort,
    _r_share,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def drape_effect(world: World, drape: Entity, target: Entity) -> None:
    target.meters["comfort"] += 1
    drape.meters["use"] += 1
    propagate(world)


def personify_effect(world: World, hero: Entity, object_ent: Entity) -> None:
    hero.memes["care"] += 1
    hero.memes["joy"] += 1
    object_ent.meters["use"] += 1
    world.say(
        f"{hero.id} smiled and said {object_ent.label} was being brave, "
        f"like a tiny space traveler waiting its turn."
    )


def setting_line(world: World) -> str:
    if world.setting.kind == "station":
        return f"The {world.setting.place} hummed softly as it orbited above the blue world."
    if world.setting.kind == "ship":
        return f"The {world.setting.place} drifted through dark space with a gentle buzz."
    return f"The {world.setting.place} floated quiet and silver in the starlight."


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.memes.get("traits", []) if t != "little"), "curious")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} aboard the {world.setting.place}."
    )
    world.say(setting_line(world))


def love_sharing(world: World, hero: Entity, obj: Entity) -> None:
    hero.memes["sharing"] += 1
    world.say(
        f"{hero.id} loved sharing space with friends, and {obj.label} was the one "
        f"thing everyone wanted a turn with."
    )


def arrival(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"One evening, {hero.id} and {hero.pronoun('possessive')} {parent.label} "
        f"floated over to the shared corner of the ship."
    )


def want(world: World, hero: Entity, obj: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} wanted to use {obj.label}, but there was only one good spot for it."
    )


def drape(world: World, hero: Entity, cloth: Entity, obj: Entity) -> None:
    cloth.worn_by = hero.id
    world.say(
        f"{hero.id} draped {cloth.label} over {obj.label} so the shared place would feel soft and calm."
    )
    drape_effect(world, cloth, obj)


def personify(world: World, hero: Entity, obj: Entity) -> None:
    world.say(
        f"{hero.id} personified {obj.label}, as if it could feel proud about taking turns."
    )
    personify_effect(world, hero, obj)


def share_turns(world: World, hero: Entity, other: Entity, obj: Entity) -> None:
    hero.memes["sharing"] += 1
    other.memes["sharing"] += 1
    obj.meters["use"] += 1
    world.say(
        f"Then {hero.id} offered {obj.label} to {other.id}, and they took turns by the window."
    )
    world.say(
        f"Their laughter drifted through the station like a small bright comet."
    )


def ending(world: World, hero: Entity, other: Entity, obj: Entity, cloth: Entity) -> None:
    world.say(
        f"In the end, {obj.label} stayed cozy under {cloth.label}, and {hero.id} "
        f"shared it happily with {other.id} while the stars blinked outside."
    )


SETTINGS = {
    "station": Setting(
        place="space station",
        kind="station",
        shared_spots=["window seat", "bunk corner", "observation ring"],
        outer="Earth",
    ),
    "ship": Setting(
        place="little starship",
        kind="ship",
        shared_spots=["sleep nook", "view hatch", "control bench"],
        outer="the moon",
    ),
    "outpost": Setting(
        place="moon outpost",
        kind="station",
        shared_spots=["table nook", "sleep pod", "glass dome"],
        outer="the stars",
    ),
}

OBJECTS = {
    "blanket": Object(
        id="blanket",
        label="a soft travel blanket",
        phrase="a soft travel blanket",
        target="bunk",
        shareable=True,
        needs_drape=False,
    ),
    "telescope": Object(
        id="telescope",
        label="a little telescope",
        phrase="a little telescope",
        target="window",
        shareable=True,
        needs_drape=False,
    ),
    "glowball": Object(
        id="glowball",
        label="a glowball",
        phrase="a glowball that shone like a tiny moon",
        target="table",
        shareable=True,
        needs_drape=False,
    ),
    "driftpod": Object(
        id="driftpod",
        label="a drift pod",
        phrase="a round drift pod",
        target="corner",
        shareable=True,
        needs_drape=False,
    ),
}

DRAPES = {
    "sheet": Drape(
        id="sheet",
        label="a quilted sheet",
        phrase="a quilted sheet",
        covers={"bunk", "corner", "seat"},
        softens={"hard", "cold"},
    ),
    "cape": Drape(
        id="cape",
        label="a star cape",
        phrase="a star cape",
        covers={"window", "seat"},
        softens={"bright", "drafty"},
    ),
    "cloth": Drape(
        id="cloth",
        label="a moon cloth",
        phrase="a moon cloth",
        covers={"table", "corner"},
        softens={"cold", "scratchy"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Iris", "Nova", "Ari", "Zia"]
BOY_NAMES = ["Kai", "Pip", "Finn", "Orin", "Tess", "Jett"]
TRAITS = ["brave", "curious", "gentle", "cheerful", "clever", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for obj_id, obj in OBJECTS.items():
            for drape_id, drape in DRAPES.items():
                if obj.target in drape.covers:
                    combos.append((place, obj_id, drape_id))
    return combos


def explain_rejection(obj: Object, drape: Drape) -> str:
    return (
        f"(No story: {drape.label} cannot really drape over {obj.label} in a way "
        f"that changes the shared space. Try an object whose spot is covered by the drape.)"
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    obj_cfg = OBJECTS[params.object]
    drape_cfg = DRAPES[params.drape]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        memos := {},  # type: ignore
    ))
    hero.memes.update({"traits": [params.trait], "sharing": 0.0, "worry": 0.0, "joy": 0.0, "care": 0.0})

    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="crew parent",
    ))
    obj = world.add(Entity(
        id=obj_cfg.id,
        type="thing",
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        owner=hero.id,
    ))
    drape_ent = world.add(Entity(
        id=drape_cfg.id,
        type="thing",
        label=drape_cfg.label,
        phrase=drape_cfg.phrase,
        owner=hero.id,
        protective=True,
    ))
    other = world.add(Entity(
        id="Rin",
        kind="character",
        type="girl",
        label="Rin",
    ))

    world.facts.update(hero=hero, parent=parent, obj=obj, drape=drape_ent, other=other, setting=setting, obj_cfg=obj_cfg)
    intro(world, hero)
    love_sharing(world, hero, obj)
    world.para()
    arrival(world, hero, parent)
    want(world, hero, obj)
    world.say(f"{hero.id} noticed that everyone was waiting for a turn, so {hero.id} took a breath.")
    drape(world, hero, drape_ent, obj)
    personify(world, hero, obj)
    share_turns(world, hero, other, obj)
    world.para()
    ending(world, hero, other, obj, drape_ent)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obj_cfg = f["obj_cfg"]
    return [
        f'Write a gentle Space Adventure story for a young child that includes the word "drape" and the word "personify".',
        f"Tell a small story where {hero.id} learns to share {obj_cfg.label} aboard the {world.setting.place}.",
        f"Write a child-friendly space story about taking turns, a cozy drape, and a friendly object that feels almost alive.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    other: Entity = f["other"]
    obj: Entity = f["obj"]
    drape: Entity = f["drape"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with {obj.label} at first?",
            answer=f"{hero.id} wanted to use {obj.label}, but there was only one shared spot for it.",
        ),
        QAItem(
            question=f"Why did {hero.id} drape {drape.label} over {obj.label}?",
            answer=f"{hero.id} draped {drape.label} over {obj.label} to make the shared place feel soft and calm.",
        ),
        QAItem(
            question=f"Who shared {obj.label} with {hero.id} in the end?",
            answer=f"{other.id} shared {obj.label} with {hero.id}, and they took turns together.",
        ),
        QAItem(
            question=f"What did {hero.id} do that personified {obj.label}?",
            answer=f"{hero.id} personified {obj.label} by speaking about it like it could feel proud about taking turns.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does drape mean?",
            answer="To drape something means to put it loosely over something else so it hangs down softly.",
        ),
        QAItem(
            question="What does personify mean?",
            answer="To personify something means to talk about it as if it were a person or had human feelings.",
        ),
        QAItem(
            question="Why is sharing important on a space station?",
            answer="Sharing is important on a space station because space is small, so people need to take turns and make room for each other.",
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
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.protective:
            bits.append("protective=True")
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "traits"}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
shared_turns(H,O,X) :- hero(H), other(O), object(X), H != O.
cozy(X) :- draped(D,X), drape(D), object(X).
good_story(H,O,X,D) :- hero(H), other(O), object(X), drape(D), cozy(X), shared_turns(H,O,X).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for o in OBJECTS.values():
        lines.append(asp.fact("object", o.id))
        lines.append(asp.fact("target", o.id, o.target))
    for d in DRAPES.values():
        lines.append(asp.fact("drape", d.id))
        for c in sorted(d.covers):
            lines.append(asp.fact("covers", d.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    program = asp_program("#show good_story/4.")
    model = asp.one_model(program)
    cl = set(asp.atoms(model, "good_story"))
    if cl == py:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure story world about draping, personifying, and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--drape", choices=DRAPES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = valid_combos()
    if args.object and args.drape:
        if not any((o == args.object and d == args.drape) for _, o, d in combos):
            raise StoryError(explain_rejection(OBJECTS[args.object], DRAPES[args.drape]))
    filtered = [c for c in combos if (args.place is None or c[0] == args.place)
                and (args.object is None or c[1] == args.object)
                and (args.drape is None or c[2] == args.drape)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj, drape = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, object=obj, drape=drape, name=name, gender=gender, parent=parent, trait=trait)


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
        print(asp_program("#show good_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show good_story/4."))
        print(sorted(asp.atoms(model, "good_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("station", "blanket", "sheet", "Mina", "girl", "mother", "gentle"),
            StoryParams("ship", "telescope", "cape", "Kai", "boy", "father", "curious"),
            StoryParams("outpost", "glowball", "cloth", "Luna", "girl", "mother", "cheerful"),
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.object} with {p.drape} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
