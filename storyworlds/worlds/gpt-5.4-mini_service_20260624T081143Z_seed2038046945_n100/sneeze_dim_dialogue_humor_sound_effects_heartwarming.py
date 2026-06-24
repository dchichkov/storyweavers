#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/sneeze_dim_dialogue_humor_sound_effects_heartwarming.py
===============================================================================================================================

A small heartwarming storyworld about a child with a sneezy, dim little evening
that turns warm again through dialogue, humor, and gentle sound effects.

Premise seed:
- "sneeze-dim"

Style:
- Heartwarming
- Dialogue
- Humor
- Sound effects
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


BRIGHTNESS_THRESHOLD = 1.0
HUMOR_THRESHOLD = 1.0
SNEEZE_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    cozy: bool = True
    can_sing: bool = True
    can_make_tea: bool = True


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    object: str
    seed: Optional[int] = None


SETTINGS = {
    "bedroom": Setting("the bedroom"),
    "kitchen": Setting("the kitchen"),
    "living_room": Setting("the living room"),
}

OBJECTS = {
    "lamp": {"label": "little lamp", "phrase": "a little lamp with a yellow shade"},
    "book": {"label": "picture book", "phrase": "a bright picture book"},
    "blanket": {"label": "soft blanket", "phrase": "a soft blanket with stars"},
}

GIRL_NAMES = ["Lia", "Mia", "Nora", "Ava", "Rose", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Noah", "Eli", "Max", "Sam"]
PARENTS = ["mother", "father"]
PLACES = list(SETTINGS)
OBJECT_IDS = list(OBJECTS)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.lines = []
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


def _sneeze(world: World, child: Entity) -> list[str]:
    if child.meters.get("sneeze", 0.0) < SNEEZE_THRESHOLD:
        return []
    sig = "sneeze"
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["tired"] = child.meters.get("tired", 0.0) + 1
    world.facts["sneeze_sound"] = "achoo!"
    return [f"{child.pronoun().capitalize()} went, \"Achoo!\""]


def _dim(world: World) -> list[str]:
    if world.facts.get("sneeze_sound") != "achoo!":
        return []
    sig = "dim"
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["room_dim"] = True
    return ["The lamp seemed to dim for a moment, like it was blinking with surprise."]


def _comfort(world: World, child: Entity, parent: Entity, obj: Entity) -> list[str]:
    if child.memes.get("comfort", 0.0) < 1.0 or parent.memes.get("love", 0.0) < 1.0:
        return []
    sig = "comfort"
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 1)
    child.meters["warmth"] = child.meters.get("warmth", 0.0) + 1
    obj.meters["used"] = obj.meters.get("used", 0.0) + 1
    return [
        f"{parent.pronoun().capitalize()} tucked {child.id} under the {obj.label} and said, \"I am right here.\"",
        "Snip, snip went the tissue, and the room felt gentler right away.",
    ]


def _humor(world: World, child: Entity) -> list[str]:
    if child.meters.get("sneeze", 0.0) < SNEEZE_THRESHOLD:
        return []
    sig = "humor"
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["cheer"] = child.memes.get("cheer", 0.0) + 1
    return ["\"My nose just said the biggest hello,\" the child giggled."]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for fn in (_sneeze, _dim, _humor):
            before = len(world.lines)
            lines = fn(world)  # type: ignore[arg-type]
            if lines:
                changed = True
                for line in lines:
                    world.say(line)


def tell_story(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    obj_info = OBJECTS[params.object]
    obj = world.add(Entity(id=params.object, type=params.object, label=obj_info["label"], phrase=obj_info["phrase"], caretaker=parent.id))
    child.meters["sneeze"] = 1.0
    child.memes["worry"] = 1.0
    parent.memes["love"] = 1.0
    child.memes["comfort"] = 1.0

    world.say(f"It was quiet in {setting.place}, and {child.id} gave a little sniffle.")
    world.say(f"{parent.pronoun().capitalize()} asked, \"Are you feeling okay, sweetie?\"")
    propagate(world)
    world.say(f"{child.id} blinked and whispered, \"I am okay. I just sneezed my tiny sneeze-dim sneeze.\"")
    world.say(f"{parent.pronoun().capitalize()} smiled and said, \"Then we need a cozy plan.\"")
    world.say("Warm tea went clink, clink in the cup.")
    world.say("Then the blanket came swish, and the room felt bright again.")
    _comfort(world, child, parent, obj)
    world.say(f"{child.id} smiled, and the tiny sneeze became just a funny memory.")
    world.facts.update(child=child, parent=parent, obj=obj, setting=setting)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for name_kind in ("girl", "boy"):
            for obj in OBJECT_IDS:
                combos.append((place, name_kind, obj))
    return combos


def explain_rejection(place: str, gender: str, obj: str) -> str:
    return f"(No story: the requested trio {place!r}, {gender!r}, {obj!r} does not fit this cozy sneeze-dim world.)"


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for obj in OBJECT_IDS:
        lines.append(asp.fact("object", obj))
    for g in ("girl", "boy"):
        lines.append(asp.fact("gender", g))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Gender, Obj) :- place(Place), gender(Gender), object(Obj).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    model = asp.one_model(asp_program())
    cl = set(asp.atoms(model, "valid"))
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming sneeze-dim storyworld with dialogue and sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--object", choices=OBJECT_IDS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
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
    place = args.place or rng.choice(PLACES)
    gender = args.gender or rng.choice(["girl", "boy"])
    obj = args.object or rng.choice(OBJECT_IDS)
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, name=name, gender=gender, parent=parent, object=obj)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    obj: Entity = f["obj"]  # type: ignore[assignment]
    return [
        f'Write a heartwarming story with dialogue where {child.id} has a sneeze-dim moment in {world.setting.place}.',
        f'Include a funny "Achoo!" sound effect, a caring reply from {parent.pronoun()}, and {obj.label}.',
        f"Tell a cozy little story where a sneeze makes the room dim for a moment and the family makes it better.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    obj: Entity = f["obj"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What happened first in {world.setting.place}?",
            answer=f"{child.id} gave a little sniffle and then sneezed. The story says the sneeze made the room feel sneeze-dim for a moment.",
        ),
        QAItem(
            question=f"What did {parent.label or parent.type} say to {child.id}?",
            answer=f"{parent.pronoun().capitalize()} asked if {child.id} was okay and then said, \"I am right here.\"",
        ),
        QAItem(
            question=f"What cozy thing helped after the sneeze?",
            answer=f"Warm tea, a soft blanket, and kind words helped {child.id} feel better.",
        ),
        QAItem(
            question=f"What sound effect appeared in the story?",
            answer='The story used "Achoo!" for the sneeze and "Snip, snip" for the tissue.',
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a tissue do?",
            answer="A tissue is a soft paper used to wipe a nose, catch sneezes, or gently clean a little spill.",
        ),
        QAItem(
            question="Why do people say gesundheit or bless you after a sneeze?",
            answer="People often say a kind word after a sneeze to show care and good manners.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(SETTINGS[params.place], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        print(asp.atoms(model, "valid"))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        for place in PLACES:
            for gender in ("girl", "boy"):
                for obj in OBJECT_IDS:
                    params = StoryParams(place=place, name=(GIRL_NAMES[0] if gender == "girl" else BOY_NAMES[0]), gender=gender, parent="mother", object=obj)
                    samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = args.seed
            key = (params.place, params.gender, params.object, params.name, params.parent)
            if key in seen:
                continue
            seen.add(key)
            samples.append(generate(params))

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
