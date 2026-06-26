#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/elegant_momentum_body_snowy_curb_transformation_sound.py
==============================================================================================================================

A compact fairy-tale storyworld about an elegant snowy curb, a body that can
change, and sound effects that nudge the change along.

Seed story idea:
---
On a snowy curb, a little child in an elegant coat met a tiny bell-fox who
could not cross the drift because its body was too stiff. The child rang a
silver bell, and the sound made the fox's body soften, stretch, and turn
graceful. Snow sparkled, the curb sang back, and the fox trotted away with
lively momentum.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    transformed: bool = False
    from_form: str = ""
    to_form: str = ""

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "fairy"}
        male = {"boy", "father", "dad", "man", "king", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the snowy curb"
    climate: str = "snowy"
    afford: set[str] = field(default_factory=set)


@dataclass
class Sound:
    id: str
    label: str
    effects: list[str]
    rhythm: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    from_form: str
    to_form: str
    body_shift: str
    result_image: str
    requires: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    sound: str
    transformation: str
    name: str
    gender: str
    role: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


SETTING = Setting(place="the snowy curb", climate="snowy", afford={"sound", "transformation"})

SOUNDS = {
    "bell": Sound(
        id="bell",
        label="silver bell",
        effects=["ding", "ding-ding", "tinkle"],
        rhythm="a bright little rhythm",
        mood="hopeful",
        tags={"sound", "bright", "elegant"},
    ),
    "wand": Sound(
        id="wand",
        label="wand tap",
        effects=["tap", "tik", "ping"],
        rhythm="a careful rhythm",
        mood="gentle",
        tags={"sound", "gentle", "magic"},
    ),
    "lantern": Sound(
        id="lantern",
        label="lantern hum",
        effects=["hummm", "whirr", "soft chime"],
        rhythm="a soft humming beat",
        mood="calm",
        tags={"sound", "calm"},
    ),
}

TRANSFORMS = {
    "fox": Transformation(
        id="fox",
        from_form="a stiff little snow fox",
        to_form="a lively fox of warm breath and bright paws",
        body_shift="its body softened, stretched, and found its own quick balance",
        result_image="the fox left tiny sparkles where its paws touched the curb",
        requires="bell",
        tags={"transformation", "body", "momentum", "elegant"},
    ),
    "doll": Transformation(
        id="doll",
        from_form="a pale doll of frosted wood",
        to_form="a smiling doll with a light, dancing body",
        body_shift="its body loosened, its arms became graceful, and its feet could turn",
        result_image="the doll spun once and the snowflakes applauded",
        requires="wand",
        tags={"transformation", "body", "elegant"},
    ),
    "swan": Transformation(
        id="swan",
        from_form="a snow swan with a locked neck",
        to_form="a proud swan with a sweeping neck and easy momentum",
        body_shift="its body uncurled, rose high, and moved like a ribbon on the wind",
        result_image="the curb glittered like a stage for the swan's first glide",
        requires="lantern",
        tags={"transformation", "body", "momentum"},
    ),
}

NAMES = ["Lina", "Mara", "Nell", "Iris", "Pia", "June", "Eva", "Sora"]
ROLES = ["girl", "boy"]


def story_intro(hero: Entity, sound: Sound, trans: Transformation) -> str:
    return (
        f"{hero.id} was a little {hero.type} with an elegant coat and a curious heart, "
        f"walking beside the snowy curb where the world looked hush-hush and white."
    )


def tell_sound(world: World, hero: Entity, sound: Sound) -> None:
    world.say(
        f"Then {hero.id} found {sound.label}, and the air answered with {', '.join(sound.effects[:2])}."
    )
    if len(sound.effects) > 2:
        world.say(
            f"The little noises made {sound.rhythm}, and even the snow seemed to listen."
        )


def tell_transformation(world: World, hero: Entity, trans: Transformation, sound: Sound) -> None:
    target = world.facts["target"]
    target.transformed = True
    target.from_form = trans.from_form
    target.to_form = trans.to_form
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    hero.meters["momentum"] = hero.meters.get("momentum", 0.0) + 1
    target.meters["body"] = target.meters.get("body", 0.0) + 1
    target.meters["grace"] = target.meters.get("grace", 0.0) + 1
    world.say(
        f"The sound touched the curb like a spell, and {target.from_form} began to change."
    )
    world.say(
        f"{trans.body_shift.capitalize()}, because {sound.label} woke the magic in its body."
    )
    world.say(
        f"At last it became {trans.to_form}, and {trans.result_image}."
    )


def tell_resolve(world: World, hero: Entity, trans: Transformation) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"{hero.id} laughed softly, gave the transformed creature a bow, and watched it go with new momentum."
    )
    world.say(
        f"By the end, the snowy curb was no longer quiet; it shimmered with the memory of that elegant sound."
    )


def build_world(params: StoryParams) -> World:
    if params.sound not in SOUNDS:
        raise StoryError("Unknown sound choice.")
    if params.transformation not in TRANSFORMS:
        raise StoryError("Unknown transformation choice.")
    sound = SOUNDS[params.sound]
    trans = TRANSFORMS[params.transformation]
    if trans.requires != sound.id:
        raise StoryError(
            f"(No story: {trans.id} needs the {trans.requires} sound, not the {sound.label}.)"
        )

    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.role))
    target = world.add(Entity(
        id="target",
        kind="character",
        type="thing",
        label=trans.id,
        transformed=False,
        from_form=trans.from_form,
        to_form=trans.to_form,
    ))
    world.facts.update(hero=hero, target=target, sound=sound, trans=trans, params=params)

    world.say(story_intro(hero, sound, trans))
    world.say(
        f"On the snowy curb stood {trans.from_form}, still as a little statue, with its body waiting for a change."
    )
    world.para()
    world.say(
        f"{hero.id} lifted {sound.label} and listened to the hush before the first note."
    )
    tell_sound(world, hero, sound)
    world.para()
    tell_transformation(world, hero, trans, sound)
    tell_resolve(world, hero, trans)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a fairy tale about an elegant child on a snowy curb, where a sound effect causes a transformation.',
        f"Tell a small fairy tale in which {f['hero'].id} uses the {f['sound'].label} to help a body change at the snowy curb.",
        f"Write a child-friendly story with bells, transformation, and a snowy curb, ending with a new body and a clear image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sound = f["sound"]
    trans = f["trans"]
    target = f["target"]
    return [
        QAItem(
            question=f"Where did {hero.id} meet the creature that needed a change?",
            answer=f"{hero.id} met it on the snowy curb, where the snow made everything quiet and bright.",
        ),
        QAItem(
            question=f"What sound helped start the transformation?",
            answer=f"The {sound.label} helped start it. Its {', '.join(sound.effects[:2])} sound carried the magic forward.",
        ),
        QAItem(
            question=f"What changed about the creature's body?",
            answer=f"{trans.body_shift.capitalize()}, and that was how its body changed from {trans.from_form} into {trans.to_form}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {target.to_form} and a snowy curb that still seemed to remember the elegant sound.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "bell": [
        QAItem(
            question="What does a bell sound like?",
            answer="A bell often makes a bright dinging sound that people can hear clearly.",
        )
    ],
    "snow": [
        QAItem(
            question="What happens to snow when it is stepped on?",
            answer="Snow can crunch and pack down when someone steps on it.",
        )
    ],
    "body": [
        QAItem(
            question="What is a body?",
            answer="A body is the part of a person or animal that can move, rest, and grow.",
        )
    ],
    "transformation": [
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another form.",
        )
    ],
    "momentum": [
        QAItem(
            question="What does momentum mean in a story?",
            answer="Momentum is the feeling of moving forward with energy and ease.",
        )
    ],
    "elegant": [
        QAItem(
            question="What does elegant mean?",
            answer="Elegant means graceful, neat, and very lovely to look at.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["sound"].tags) | set(world.facts["trans"].tags) | {"body"}
    out: list[QAItem] = []
    for key in ["elegant", "bell", "transformation", "momentum", "body", "snow"]:
        if key in tags:
            out.extend(WORLD_KNOWLEDGE[key])
    return out


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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.transformed:
            bits.append(f"from={e.from_form!r}")
            bits.append(f"to={e.to_form!r}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    return sorted((sound_id, trans_id) for trans_id, trans in TRANSFORMS.items() for sound_id in SOUNDS if trans.requires == sound_id)


@dataclass
class _ArgsLike:
    sound: Optional[str] = None
    transformation: Optional[str] = None
    gender: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sound and args.transformation:
        trans = TRANSFORMS[args.transformation]
        if trans.requires != args.sound:
            raise StoryError(
                f"(No story: {trans.id} only wakes to the {trans.requires} sound.)"
            )

    combos = valid_combos()
    if args.sound:
        combos = [c for c in combos if c[0] == args.sound]
    if args.transformation:
        combos = [c for c in combos if c[1] == args.transformation]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    sound_id, trans_id = rng.choice(combos)
    gender = args.gender or rng.choice(ROLES)
    name = args.name or rng.choice(NAMES)
    role = args.role or ("little princess" if gender == "girl" else "little prince")
    return StoryParams(sound=sound_id, transformation=trans_id, name=name, gender=gender, role=role)


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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s_id in SOUNDS:
        lines.append(asp.fact("sound", s_id))
    for t_id, trans in TRANSFORMS.items():
        lines.append(asp.fact("transformation", t_id))
        lines.append(asp.fact("requires", t_id, trans.requires))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T) :- sound(S), transformation(T), requires(T, S).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: an elegant snowy curb, sound effects, and transformation."
    )
    ap.add_argument("--sound", choices=sorted(SOUNDS))
    ap.add_argument("--transformation", choices=sorted(TRANSFORMS))
    ap.add_argument("--gender", choices=ROLES)
    ap.add_argument("--name")
    ap.add_argument("--role")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (sound, transformation) combos:\n")
        for s, t in combos:
            print(f"  {s:10} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [
        StoryParams(sound="bell", transformation="fox", name="Lina", gender="girl", role="little princess"),
        StoryParams(sound="wand", transformation="doll", name="Mara", gender="girl", role="little princess"),
        StoryParams(sound="lantern", transformation="swan", name="Iris", gender="girl", role="little princess"),
    ]

    if args.all:
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
