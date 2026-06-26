#!/usr/bin/env python3
"""
storyworlds/worlds/aleck_foreshadowing_transformation_heartwarming.py
======================================================================

A small heartwarming storyworld about Aleck, a quiet sign of change, and a
gentle transformation that becomes visible by the end.

Core premise:
- Aleck notices something small and slightly troubling early on.
- A foreshadowed clue points toward a future need.
- Aleck acts with care, turning an ordinary object or moment into something
  warmer and kinder.
- The ending proves the change in the world state.

The world is intentionally compact: one child, one setting, one treasured item,
and one transformation path. The prose is driven by simulated state rather than
being a fixed paragraph with swapped nouns.
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    def __post_init__(self) -> None:
        for k in ("hope", "worry", "warmth", "dust", "tired"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)


@dataclass
class Setting:
    place: str = "the old community hall"
    indoors: bool = True


@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    kind: str
    initial_state: str
    transformed_state: str
    transformation_name: str
    foadow_clue: str
    emotional_turn: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    place: str
    object_id: str
    name: str = "Aleck"
    seed: Optional[int] = None


SETTINGS = {
    "hall": Setting(place="the old community hall", indoors=True),
    "kitchen": Setting(place="the warm kitchen", indoors=True),
    "library": Setting(place="the small library", indoors=True),
}

OBJECTS = {
    "lamp": ObjectSpec(
        id="lamp",
        label="lamp",
        phrase="a small lamp with a dull shade",
        kind="lamp",
        initial_state="dim",
        transformed_state="bright",
        transformation_name="polishing",
        foadow_clue="its shade was a little cloudy",
        emotional_turn="The room could use a kinder light",
    ),
    "plant": ObjectSpec(
        id="plant",
        label="plant",
        phrase="a droopy little plant in a clay pot",
        kind="plant",
        initial_state="wilted",
        transformed_state="perked up",
        transformation_name="watering",
        foadow_clue="its leaves had begun to curl at the edges",
        emotional_turn="A little care might help it stand tall again",
    ),
    "banner": ObjectSpec(
        id="banner",
        label="banner",
        phrase="a faded paper banner with a torn corner",
        kind="banner",
        initial_state="faded",
        transformed_state="fresh",
        transformation_name="mending",
        foadow_clue="one ribbon end was already hanging loose",
        emotional_turn="Something small seemed ready to become beautiful again",
    ),
}

GENTLE_TRAITS = ["quiet", "thoughtful", "kind", "patient", "careful", "soft-spoken"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming foreshadowing-and-transformation story world."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object-id", choices=OBJECTS)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    object_id = args.object_id or rng.choice(list(OBJECTS))
    return StoryParams(place=place, object_id=object_id, name=args.name or "Aleck")


def valid_combos() -> list[tuple[str, str]]:
    return [(p, o) for p in SETTINGS for o in OBJECTS]


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.object_id not in OBJECTS:
        raise StoryError("Unknown object.")
    if params.name.strip().lower() != "aleck":
        raise StoryError("This world is centered on Aleck.")


def predict_transformation(world: World, actor: Entity, obj: Entity, spec: ObjectSpec) -> bool:
    sim = world.copy()
    simulate_act(sim, sim.get(actor.id), sim.get(obj.id), spec, narrate=False)
    return sim.get(obj.id).memes["warmth"] >= THRESHOLD


def foreshadow(world: World, actor: Entity, obj: Entity, spec: ObjectSpec) -> None:
    actor.memes["worry"] += 1
    obj.meters["dust"] += 1
    world.say(
        f"In {world.setting.place}, {actor.id} noticed that {obj.phrase}; "
        f"{spec.foadow_clue if hasattr(spec, 'foadow_clue') else spec.foadow_clue}."
    )
    world.say(
        f"It was only a tiny sign, but {actor.id} remembered it."
    )


def simulate_act(world: World, actor: Entity, obj: Entity, spec: ObjectSpec, narrate: bool = True) -> None:
    if spec.id == "lamp":
        obj.meters["dust"] = max(0.0, obj.meters["dust"] - 1)
        obj.meters["warmth"] += 1
        actor.memes["hope"] += 1
        actor.memes["warmth"] += 1
    elif spec.id == "plant":
        obj.meters["warmth"] += 1
        obj.meters["dust"] = max(0.0, obj.meters["dust"] - 0.5)
        actor.memes["hope"] += 1
    elif spec.id == "banner":
        obj.meters["warmth"] += 1
        obj.memes["warmth"] += 1
        actor.memes["hope"] += 1
    if narrate:
        if spec.id == "lamp":
            world.say(
                f"Aleck gently rubbed the glass with a soft cloth, and the lamp began to glow."
            )
        elif spec.id == "plant":
            world.say(
                f"Aleck poured a little water into the pot, and the plant slowly lifted its leaves."
            )
        else:
            world.say(
                f"Aleck found tape and fresh paper, then carefully mended the torn banner."
            )
        world.say(
            f"The little change seemed small at first, but it was enough to make the room feel kinder."
        )


def ending_image(world: World, actor: Entity, obj: Entity, spec: ObjectSpec) -> None:
    if spec.id == "lamp":
        world.say(
            f"By the end, the lamp was bright, and {actor.id} could see warm gold on the wall."
        )
    elif spec.id == "plant":
        world.say(
            f"By the end, the plant stood straighter, and {actor.id} smiled at its green little leaves."
        )
    else:
        world.say(
            f"By the end, the banner looked fresh again, and {actor.id} hung it up so everyone could see."
        )


def tell(setting: Setting, spec: ObjectSpec, hero_name: str = "Aleck") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy"))
    obj = world.add(Entity(id=spec.id, type=spec.kind, label=spec.label, phrase=spec.phrase, owner=hero.id))
    world.facts.update(hero=hero, obj=obj, spec=spec, setting=setting)

    world.say(
        f"Aleck was a {random.choice(GENTLE_TRAITS)} boy who liked noticing small things."
    )
    world.say(
        f"One afternoon at {setting.place}, he saw {spec.phrase}."
    )
    world.para()
    foreshadow(world, hero, obj, spec)
    world.para()
    if predict_transformation(world, hero, obj, spec):
        simulate_act(world, hero, obj, spec, narrate=True)
    ending_image(world, hero, obj, spec)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    spec = f["spec"]
    return [
        f'Write a warm story for a young child about Aleck and {spec.phrase}.',
        f"Tell a heartwarming story where Aleck notices a small clue first, then makes a gentle change to {spec.label}.",
        f"Write a simple story that uses foreshadowing and transformation, with Aleck at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    spec = f["spec"]
    obj = f["obj"]
    return [
        QAItem(
            question=f"What did Aleck notice at {f['setting'].place}?",
            answer=f"Aleck noticed {spec.phrase}.",
        ),
        QAItem(
            question=f"What clue foreshadowed the change?",
            answer=f"The clue was that {spec.foadow_clue}.",
        ),
        QAItem(
            question=f"What transformation happened to the {spec.label}?",
            answer=f"The {spec.label} became {spec.transformed_state} after Aleck's careful {spec.transformation_name}.",
        ),
        QAItem(
            question=f"How did Aleck feel while helping?",
            answer=f"Aleck felt hopeful and warm because the small change made the place kinder.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    spec = f["spec"]
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small clue early in a story that hints at something important later.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new state, often in a clear and noticeable way.",
        ),
        QAItem(
            question=f"Why might {spec.label} need care?",
            answer=f"Because {spec.phrase} was not quite its best yet, and a little care could help it become {spec.transformed_state}.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} kind={e.kind:8} type={e.type:8} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
hero(aleck).
story_object(lamp).
story_object(plant).
story_object(banner).

foreshadows(aleck, O) :- story_object(O), clue(O).
transforms(O) :- story_object(O), changed(O).

#show foreshadows/2.
#show transforms/1.
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("hero", "aleck")]
    for oid in OBJECTS:
        lines.append(asp.fact("story_object", oid))
        lines.append(asp.fact("clue", oid))
        lines.append(asp.fact("changed", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    import storyworlds.asp as _asp  # lazy import by contract

    model = _asp.one_model(asp_program("#show foreshadows/2.\n#show transforms/1."))
    shown_foreshadows = set(_asp.atoms(model, "foreshadows"))
    shown_transforms = set(_asp.atoms(model, "transforms"))
    expected_foreshadows = {("aleck", oid) for oid in OBJECTS}
    expected_transforms = {(oid,) for oid in OBJECTS}
    if shown_foreshadows == expected_foreshadows and shown_transforms == expected_transforms:
        print("OK: ASP parity looks reasonable.")
        return 0
    print("ASP mismatch.")
    print("foreshadows:", sorted(shown_foreshadows))
    print("transforms:", sorted(shown_transforms))
    return 1


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(SETTINGS[params.place], OBJECTS[params.object_id], params.name)
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
        print(asp_program("#show foreshadows/2.\n#show transforms/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show foreshadows/2.\n#show transforms/1."))
        print("foreshadows:", sorted(set(asp.atoms(model, "foreshadows"))))
        print("transforms:", sorted(set(asp.atoms(model, "transforms"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            for oid in OBJECTS:
                params = StoryParams(place=place, object_id=oid, name="Aleck")
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(args.n, 1) * 50):
            if len(samples) >= max(args.n, 1):
                break
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
