#!/usr/bin/env python3
"""
A small slice-of-life story world about a child, moss, and a legendary sound
effect that turns an ordinary day into a gentle adventure.

Premise:
- A child notices soft moss in a quiet place.
- They try to make a "legendary" sound effect with a toy or object.
- A small mishap or mismatch creates tension.
- A kinder, more careful sound makes the ending feel complete.

This script models the physical world with meters and the emotional world with
memes, then narrates from the resulting state.
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
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the garden"
    indoor: bool = False
    mossy: bool = True
    calm: bool = True


@dataclass
class SoundEffect:
    id: str
    label: str
    onomatopoeia: str
    source: str
    charm: str
    ripple: str
    volume: str
    gentle: bool = True


@dataclass
class Object:
    id: str
    label: str
    phrase: str
    type: str
    fragile: bool = False
    acoustic: bool = False
    held: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.objects: dict[str, Object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_object(self, obj: Object) -> Object:
        self.objects[obj.id] = obj
        return obj

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


@dataclass
class StoryParams:
    place: str
    sound_effect: str
    object: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, mossy=True, calm=True),
    "yard": Setting(place="the backyard", indoor=False, mossy=False, calm=True),
    "porch": Setting(place="the porch", indoor=False, mossy=False, calm=True),
    "laundry_room": Setting(place="the laundry room", indoor=True, mossy=False, calm=True),
}

SOUND_EFFECTS = {
    "plink": SoundEffect(
        id="plink",
        label="a legendary plink",
        onomatopoeia="plink",
        source="a spoon against a glass",
        charm="tiny and bright",
        ripple="a clear little ring",
        volume="soft",
        gentle=True,
    ),
    "whoosh": SoundEffect(
        id="whoosh",
        label="a legendary whoosh",
        onomatopoeia="whoosh",
        source="a scarf swinging through the air",
        charm="smooth and swoopy",
        ripple="a long airy sweep",
        volume="soft",
        gentle=True,
    ),
    "tap": SoundEffect(
        id="tap",
        label="a legendary tap",
        onomatopoeia="tap-tap",
        source="two wooden spoons",
        charm="neat and perky",
        ripple="a lively little beat",
        volume="moderate",
        gentle=True,
    ),
    "swish": SoundEffect(
        id="swish",
        label="a legendary swish",
        onomatopoeia="swish",
        source="a broom across the floor",
        charm="quick and tidy",
        ripple="a smooth hush",
        volume="moderate",
        gentle=True,
    ),
}

OBJECTS = {
    "spoon": Object(id="spoon", label="spoon", phrase="a shiny spoon", type="kitchen thing", acoustic=True),
    "glass": Object(id="glass", label="glass", phrase="a little glass cup", type="kitchen thing", fragile=True, acoustic=True),
    "scarf": Object(id="scarf", label="scarf", phrase="a soft scarf", type="clothing", acoustic=True),
    "broom": Object(id="broom", label="broom", phrase="a small broom", type="cleaning thing", acoustic=True),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for sid, effect in SOUND_EFFECTS.items():
            for oid, obj in OBJECTS.items():
                if place == "laundry_room" and obj.fragile:
                    continue
                if setting.mossy and sid in {"plink", "tap"}:
                    combos.append((place, sid, oid))
                elif not setting.mossy and sid in {"whoosh", "swish", "tap"}:
                    combos.append((place, sid, oid))
    return combos


def reasonableness_gate(place: str, sound_effect: str, object_id: str) -> None:
    if (place, sound_effect, object_id) not in valid_combos():
        raise StoryError(
            f"(No story: {SOUND_EFFECTS[sound_effect].label} with {OBJECTS[object_id].label} "
            f"does not fit naturally in {SETTINGS[place].place}.)"
        )


class SoundWorld:
    def __init__(self, world: World) -> None:
        self.world = world

    def record(self, key: str, value) -> None:
        self.world.facts[key] = value


def moss_detail(setting: Setting) -> str:
    if setting.mossy:
        return "The moss felt like a green cushion underfoot."
    return "The ground was neat and dry, with only a few little patches of green."


def do_sound(world: World, child: Entity, effect: SoundEffect, obj: Object) -> None:
    child.memes["wonder"] = child.memes.get("wonder", 0.0) + 1
    child.meters["attention"] = child.meters.get("attention", 0.0) + 1
    world.say(
        f"{child.id} lifted {obj.phrase} and tried {effect.onomatopoeia}. "
        f"It sounded {effect.charm}."
    )


def add_tension(world: World, child: Entity, parent: Entity, effect: SoundEffect, obj: Object) -> None:
    child.memes["eager"] = child.memes.get("eager", 0.0) + 1
    parent.memes["curious"] = parent.memes.get("curious", 0.0) + 1
    if obj.fragile and effect.id == "tap":
        child.memes["oops"] = child.memes.get("oops", 0.0) + 1
        world.say(
            f"{child.id} wanted the sound to be legendary, but the glass gave a tiny wobble. "
            f"{parent.pronoun().capitalize()} looked over with a careful smile."
        )
    else:
        world.say(
            f"{child.id} wanted the sound to be legendary, and {parent.id} listened from nearby."
        )


def resolve(world: World, child: Entity, parent: Entity, effect: SoundEffect, obj: Object) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    child.memes["wonder"] = child.memes.get("wonder", 0.0) + 1
    world.say(
        f"Then {child.id} made {effect.onomatopoeia} again, but this time it was slower and gentler. "
        f"The sound floated through {world.setting.place} like a small parade."
    )
    if world.setting.mossy:
        world.say(
            f"Even the moss seemed to listen. {moss_detail(world.setting)} "
            f"{child.id} smiled because the legendary sound fit the quiet place perfectly."
        )
    else:
        world.say(
            f"The room felt brighter after the little sound. {child.id} set {obj.phrase} down, "
            f"and {parent.id} laughed softly beside {child.pronoun('object')}."
        )


def tell(setting: Setting, effect: SoundEffect, obj: Object, child_name: str, gender: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add_entity(Entity(id=child_name, kind="character", type=gender, meters={}, memes={}))
    parent = world.add_entity(Entity(id="Parent", kind="character", type=parent_type, label="parent", meters={}, memes={}))
    item = world.add_object(obj)

    world.say(f"{child.id} was a little {gender} who loved quiet afternoons and small surprises.")
    world.say(
        f"On that day, {child.id} noticed {moss_detail(setting)} "
        f"and decided to make {effect.label} with {obj.phrase}."
    )
    world.para()
    add_tension(world, child, parent, effect, item)
    do_sound(world, child, effect, item)
    world.para()
    resolve(world, child, parent, effect, item)

    world.facts.update(
        child=child,
        parent=parent,
        object=obj,
        setting=setting,
        effect=effect,
    )
    return world


GIRL_NAMES = ["Mina", "Lina", "Tia", "Nora", "Iris", "Mila"]
BOY_NAMES = ["Owen", "Finn", "Nico", "Theo", "Arlo", "Milo"]
TRAITS = ["curious", "gentle", "playful", "thoughtful", "quiet", "bright"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    effect = f["effect"]
    obj = f["object"]
    return [
        f'Write a short slice-of-life story for a child who discovers moss and makes {effect.onomatopoeia}.',
        f"Tell a gentle story where {child.id} uses {obj.phrase} to make a legendary sound effect.",
        f'Write a warm story that includes moss, a little sound, and a calm ending image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    effect = f["effect"]
    obj = f["object"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What did {child.id} try to make with {obj.phrase}?",
            answer=f"{child.id} tried to make {effect.label}, and the sound went {effect.onomatopoeia}.",
        ),
        QAItem(
            question=f"Where did {child.id} hear the little legendary sound?",
            answer=f"{child.id} made the sound in {setting.place}, where the day felt calm and close.",
        ),
        QAItem(
            question=f"Why did the parent watch carefully?",
            answer=f"The parent watched carefully because {child.id} wanted the sound to be legendary, and the moment felt important.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the sound became gentler, and {child.id} felt happy and proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is moss?",
            answer="Moss is a soft, green plant that often grows in damp places and feels springy to the touch.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a made or chosen sound that helps a moment feel playful, dramatic, or special.",
        ),
        QAItem(
            question="What does the word legendary mean?",
            answer="Legendary means so good or special that people remember it and talk about it like a story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
place(garden;yard;porch;laundry_room).
effect(plink;whoosh;tap;swish).
object(spoon;glass;scarf;broom).

mossy(garden).
not_mossy(yard;porch;laundry_room).

compatible(P,E,O) :- mossy(P), effect(E), object(O), E != whoosh, O != glass.
compatible(P,E,O) :- not_mossy(P), effect(E), object(O), E != plink.
compatible_story(P,E,O) :- compatible(P,E,O).
#show compatible_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        if SETTINGS[p].mossy:
            lines.append(asp.fact("mossy", p))
        else:
            lines.append(asp.fact("not_mossy", p))
    for e in SOUND_EFFECTS:
        lines.append(asp.fact("effect", e))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/3."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about moss and a legendary sound effect.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--sound-effect", choices=SOUND_EFFECTS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    if args.place and args.sound_effect and args.object_:
        reasonableness_gate(args.place, args.sound_effect, args.object_)
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.sound_effect is None or c[1] == args.sound_effect)
        and (args.object_ is None or c[2] == args.object_)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, sound_effect, obj = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, sound_effect=sound_effect, object=obj, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        SOUND_EFFECTS[params.sound_effect],
        OBJECTS[params.object],
        params.name,
        params.gender,
        params.parent,
    )
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
        print(asp_program("#show compatible_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} compatible stories:")
        for v in vals:
            print(" ", v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="garden", sound_effect="plink", object="glass", name="Mina", gender="girl", parent="mother", trait="curious"),
            StoryParams(place="yard", sound_effect="whoosh", object="scarf", name="Owen", gender="boy", parent="father", trait="gentle"),
            StoryParams(place="porch", sound_effect="tap", object="spoon", name="Nora", gender="girl", parent="mother", trait="thoughtful"),
            StoryParams(place="laundry_room", sound_effect="swish", object="broom", name="Theo", gender="boy", parent="father", trait="playful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.sound_effect} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
