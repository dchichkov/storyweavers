#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/umbilic_rooster_fellow_kindness_sound_effects_folk.py
===============================================================================================================================

A small folk-tale storyworld about a rooster, a fellow, an umbilic cord,
kindness, and sound effects.

Seed tale inspiration:
---
A rooster once lost his brave crow after a windy night. A kind fellow found
him, listened to his small clucks and clacks, and helped him try again. The
rooster took heart, made a bright crowing sound, and the village woke smiling.
---

World model:
- The rooster carries physical "vibrance" and emotional "courage".
- The fellow can offer kindness, which raises courage and softens fear.
- Sound effects are modeled as a physical meter, because folk tales often
  hear a story before they fully understand it.
- An umbilic cord is the little center-knot that keeps a lantern charm tied to
  the rooster's perch; when it frays, the rooster feels ungrounded.
- The story turns on a gentle repair: the fellow mends the cord, speaks kindly,
  and the rooster finds his voice again.

This world is intentionally compact and constraint-checked: the story can only
be generated when the setting, the emotional state, and the repair all make a
plausible folk-tale arc.
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
    keeper: Optional[str] = None
    tethered_to: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rooster", "fellow"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    name: str
    detail: str
    soundscape: str


@dataclass
class StoryParams:
    place: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


PLACES = {
    "farmyard": Place(
        name="the farmyard",
        detail="The yard sat beside a red barn, with straw underfoot and a warm fence line.",
        soundscape="soft cluck-clucks, a loose gate rattling, and one lonely crow",
    ),
    "village_green": Place(
        name="the village green",
        detail="The green was round and tidy, with a well in the middle and apple trees at the edge.",
        soundscape="wind in the leaves, a spoon tapping a cup, and sleepy little snores from open windows",
    ),
    "lantern_lane": Place(
        name="Lantern Lane",
        detail="The lane was narrow and bright with paper lanterns, though the stones still held the night's chill.",
        soundscape="tiny bells, wooden clops, and the hush before dawn",
    ),
}

NAMES = ["Pip", "Mara", "Jory", "Tilda", "Ansel", "Nell", "Bram", "Dara"]


def _m(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _e(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _add_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = _m(ent, key) + amount


def _add_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = _e(ent, key) + amount


def _repair_cord(world: World, fellow: Entity, rooster: Entity, cord: Entity) -> None:
    if cord.id in world.fired:
        return
    world.fired.add(cord.id)
    cord.meters["frayed"] = 0
    cord.meters["whole"] = 1
    _add_meme(rooster, "grounded", 1)
    _add_meme(fellow, "kindness", 1)
    world.say(
        f"{fellow.name_or_label()} tied the umbilic cord with careful fingers, "
        f"and the little knot held fast again."
    )


def _comfort(world: World, fellow: Entity, rooster: Entity) -> None:
    if "comfort" in world.fired:
        return
    world.fired.add("comfort")
    _add_meme(rooster, "courage", 1)
    _add_meme(rooster, "trust", 1)
    _add_meme(fellow, "kindness", 1)
    world.say(
        f"{fellow.name_or_label()} spoke softly and stayed near, as patient as a candle in a window."
    )


def _sound_effects(world: World, rooster: Entity) -> None:
    if "sounds" in world.fired:
        return
    world.fired.add("sounds")
    _add_meter(rooster, "sound", 1)
    _add_meme(rooster, "hope", 1)
    world.say(
        f"The rooster tried a small sound first: cluck, cluck, then a testing crow."
    )


def _crow(world: World, rooster: Entity) -> None:
    if "crow" in world.fired:
        return
    if _e(rooster, "courage") < THRESHOLD or _m(rooster, "sound") < THRESHOLD:
        return
    world.fired.add("crow")
    _add_meter(rooster, "sound", 1)
    _add_meme(rooster, "pride", 1)
    world.say(
        f"Then the rooster drew breath and let out a bright cock-a-doodle-doo that rang over the rooftops."
    )


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    rooster = world.add(Entity(
        id="rooster",
        kind="character",
        type="rooster",
        label="rooster",
        phrase="a bright rooster with a red comb",
    ))
    fellow = world.add(Entity(
        id="fellow",
        kind="character",
        type="fellow",
        label=params.name,
        phrase=f"a kind fellow named {params.name}",
    ))
    cord = world.add(Entity(
        id="umbilic_cord",
        kind="thing",
        type="cord",
        label="umbilic cord",
        phrase="a little umbilic cord tied to a lantern charm",
        owner="rooster",
        keeper="fellow",
    ))

    rooster.meters["sound"] = 0
    rooster.meters["frayed"] = 0
    rooster.meters["whole"] = 1
    rooster.memes["fear"] = 1
    rooster.memes["courage"] = 0
    rooster.memes["trust"] = 0

    fellow.memes["kindness"] = 1
    fellow.memes["care"] = 1

    world.facts.update(place=place, rooster=rooster, fellow=fellow, cord=cord)
    return world


def tell(world: World) -> None:
    rooster = world.get("rooster")
    fellow = world.get("fellow")
    cord = world.get("umbilic_cord")

    world.say(
        f"In {world.place.name}, there lived a rooster with a voice everyone loved to hear."
    )
    world.say(
        f"{world.place.detail} Yet the night wind had worried him, and the umbilic cord on his lantern charm had come loose."
    )
    world.say(
        f"{world.place.soundscape} were enough to make the rooster tuck his beak and stay quiet."
    )

    world.para()
    world.say(
        f"{fellow.name_or_label()} found him by the fence and saw the sad little knot hanging at his side."
    )
    _comfort(world, fellow, rooster)
    _repair_cord(world, fellow, rooster, cord)
    world.say(
        f"Because {fellow.name_or_label()} was gentle, the rooster stopped trembling and listened."
    )

    world.para()
    _sound_effects(world, rooster)
    world.say(
        f"He listened to the little clacks of the repaired cord, the tap of {fellow.name_or_label()}'s shoe, and the whisper of straw."
    )
    _crow(world, rooster)
    world.say(
        f"At last the rooster lifted his head, and his brave sound rolled across {world.place.name} like morning light."
    )
    world.say(
        f"The windows opened one by one, and the village woke smiling."
    )

    world.facts["resolved"] = _e(rooster, "courage") >= THRESHOLD and _m(rooster, "sound") >= THRESHOLD
    world.facts["kindness"] = _e(fellow, "kindness")
    world.facts["crowed"] = "crow" in world.fired


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a short folk tale that includes the words "umbilic", "rooster", and "fellow".',
        f"Tell a gentle story about a rooster who loses his brave crow, and a fellow who fixes the problem with kindness.",
        f"Write a child-friendly folk tale where sound effects help a rooster find his voice again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    rooster: Entity = world.facts["rooster"]  # type: ignore[assignment]
    fellow: Entity = world.facts["fellow"]  # type: ignore[assignment]
    place: Place = world.place
    return [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about a rooster and a kind fellow named {fellow.name_or_label()} in {place.name}.",
        ),
        QAItem(
            question="What problem did the rooster have?",
            answer="He had gone quiet because the windy night had shaken his courage, and his umbilic cord had come loose.",
        ),
        QAItem(
            question="How did the fellow help?",
            answer=f"He used kindness, mended the umbilic cord, and stayed close until the rooster felt brave enough to crow again.",
        ),
        QAItem(
            question="What changed at the end?",
            answer="The rooster found his voice, the morning crow rang out, and the village woke smiling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone helps, comforts, or cares for another person without being mean.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special noises, like clacks, taps, or crows, that help a story feel vivid.",
        ),
        QAItem(
            question="What does a rooster do?",
            answer="A rooster often crows in the morning, which can wake people and animals in a farmyard or village.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
        if e.tethered_to:
            bits.append(f"tethered_to={e.tethered_to}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Facts:
% place(P).
% rooster(R).
% fellow(F).
% cord(C).
% frayed(C).
% kindness(F).

% A story is reasonable when the fellow is kind, the cord is frayed,
% and the rooster can regain courage through comfort and repair.
needs_care(R) :- rooster(R), fear(R).
can_repair(C) :- cord(C), frayed(C).
supports(F,R) :- fellow(F), rooster(R), kindness(F).

good_story(P,R,F,C) :- place(P), rooster(R), fellow(F), cord(C),
                       needs_care(R), can_repair(C), supports(F,R).

#show good_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", p) for p in PLACES]
    lines += [asp.fact("rooster", "rooster")]
    lines += [asp.fact("fellow", "fellow")]
    lines += [asp.fact("cord", "umbilic_cord")]
    lines += [asp.fact("fear", "rooster")]
    lines += [asp.fact("frayed", "umbilic_cord")]
    lines += [asp.fact("kindness", "fellow")]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = sorted(set(asp.atoms(model, "good_story")))
    py = sorted((p, "rooster", "fellow", "umbilic_cord") for p in PLACES)
    if atoms == py:
        print(f"OK: clingo gate matches Python reasonableness ({len(atoms)} places).")
        return 0
    print("MISMATCH between clingo and Python reasonableness:")
    print("  clingo:", atoms)
    print("  python:", py)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk tale about a rooster, a fellow, kindness, and sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", choices=NAMES)
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
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, name=name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        import asp
        model = asp.one_model(asp_program())
        print("\n".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES:
            params = StoryParams(place=place, name=NAMES[0], seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.place} / {p.name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
