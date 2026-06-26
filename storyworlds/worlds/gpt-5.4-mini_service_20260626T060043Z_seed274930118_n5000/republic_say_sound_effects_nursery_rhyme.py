#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/republic_say_sound_effects_nursery_rhyme.py
==============================================================================================================

A small storyworld about a tiny republic where children and neighbors say
sound effects in a nursery-rhyme style tale.

The world is built from the seed words:
- republic
- say

Domain idea:
A little republic gathers in a square or hall. A child wants to say sound
effects to help start a cheerful rhyme-parade. If the sound is too loud for the
setting, sleepy neighbors may stir; a gentler sound effect, prop, or helper
can solve the problem.

The world model keeps physical meters and emotional memes, and prose is driven
from the simulated state rather than from a frozen template.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["noise", "tangle", "sleep", "joy", "worry", "confidence", "softness", "crowd"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "mayor"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class SoundEffect:
    id: str
    phrase: str
    say: str
    loudness: float
    softness: float
    rhyme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    help_noise: float
    help_softness: float
    covers: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    sound: str
    prop: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.lines = [[]]
        w.facts = dict(self.facts)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny republic stories with sound effects in a nursery-rhyme style.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--sound", choices=sorted(SOUND_EFFECTS))
    ap.add_argument("--prop", choices=sorted(PROPS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["mayor", "neighbor"])
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


SETTINGS = {
    "square": Setting("the little square", False, {"bell", "drum", "clap"}),
    "hall": Setting("the town hall", True, {"bell", "clap", "tap"}),
    "garden": Setting("the green garden", False, {"clap", "tap", "whisper"}),
    "lane": Setting("the narrow lane", False, {"tap", "whisper"}),
}

SOUND_EFFECTS = {
    "bell": SoundEffect("bell", "ding-ding", "say 'ding-ding'", loudness=2.0, softness=0.2, rhyme="ling-ling", tags={"loud", "alert"}),
    "drum": SoundEffect("drum", "boom-boom", "say 'boom-boom'", loudness=2.5, softness=0.1, rhyme="dum-dum", tags={"loud", "beat"}),
    "clap": SoundEffect("clap", "clap-clap", "say 'clap-clap'", loudness=1.0, softness=0.8, rhyme="tap-tap", tags={"bright", "friendly"}),
    "tap": SoundEffect("tap", "tap-tap", "say 'tap-tap'", loudness=0.7, softness=1.0, rhyme="pat-pat", tags={"soft", "friendly"}),
    "whisper": SoundEffect("whisper", "shh-shh", "say 'shh-shh'", loudness=0.1, softness=1.5, rhyme="hush-hush", tags={"soft", "sleep"}),
}

PROPS = {
    "broom": Prop("broom", "a broom", "a little broom", help_noise=-0.5, help_softness=0.3),
    "ribbon": Prop("ribbon", "a ribbon wand", "a ribbon wand", help_noise=-0.1, help_softness=0.8),
    "pillow": Prop("pillow", "a pillow", "a soft pillow", help_noise=-1.0, help_softness=1.2),
    "drumstick": Prop("drumstick", "a drumstick", "a drumstick", help_noise=0.4, help_softness=0.0),
}

TRAITS = ["cheerful", "tiny", "curious", "brave", "gentle", "lively"]
GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Ben", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for sound in setting.affords:
            for prop in PROPS:
                if reasonableness_gate(setting, SOUND_EFFECTS[sound], PROPS[prop]):
                    out.append((place, sound, prop))
    return out


def reasonableness_gate(setting: Setting, sound: SoundEffect, prop: Prop) -> bool:
    if sound.id == "whisper":
        return True
    if sound.loudness >= 2.0 and setting.indoors:
        return prop.id in {"pillow", "ribbon"}
    if sound.id == "drum":
        return setting.place != "the narrow lane"
    return True


def explain_rejection(setting: Setting, sound: SoundEffect, prop: Prop) -> str:
    return (
        f"(No story: {sound.phrase} is too loud for {setting.place} with {prop.label}. "
        f"Try a softer sound effect or a gentler prop.)"
    )


def select_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def introduce(world: World, child: Entity) -> None:
    world.say(f"In the little republic, {child.id} was a {child.memes.get('trait_word', 'cheerful')} little {child.type} who loved to sing and say sound effects.")


def setup_scene(world: World, child: Entity, guide: Entity, sound: SoundEffect, prop: Prop) -> None:
    world.say(f"{child.id} had {prop.phrase}, and {guide.label_word} smiled at the bright idea.")
    world.say(f"{child.id} loved to {sound.say} because {sound.rhyme} made the whole day feel like a rhyme.")


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    sound = SOUND_EFFECTS[params.sound]
    prop = PROPS[params.prop]
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender, memes={"trait_word": 0.0}))
    child.memes["trait_word"] = 1.0
    guide = world.add(Entity(id="Guide", kind="character", type=params.guide, label=params.guide))
    prop_ent = world.add(Entity(id="Prop", type="thing", label=prop.label, phrase=prop.phrase, caretaker=guide.id))
    prop_ent.meters["softness"] = prop.help_softness
    prop_ent.meters["noise"] = prop.help_noise

    child.memes["joy"] += 1
    child.memes["confidence"] += 0.5
    guide.memes["worry"] += 0.2

    introduce(world, child)
    world.say(f"They were in {setting.place}, where the republic gathered to decide the next happy thing to do.")
    world.para()
    setup_scene(world, child, guide, sound, prop)
    if sound.id not in setting.affords:
        world.say(f"But the chosen sound did not fit the place, so the day had to think again.")
    return world


def predict(world: World, sound: SoundEffect, prop: Prop) -> dict:
    sim = world.copy()
    child = sim.characters()[0]
    child.meters["noise"] += sound.loudness + prop.help_noise
    child.meters["softness"] += sound.softness + prop.help_softness
    sleeping = sim.get("Nap") if "Nap" in sim.entities else None
    wake = child.meters["noise"] >= 2.0 and child.meters["softness"] < 1.0
    return {"wake": wake}


def narrative_turn(world: World, child: Entity, guide: Entity, sound: SoundEffect, prop: Prop) -> None:
    if sound.id == "whisper":
        world.say(f"{child.id} wanted to {sound.say}, and the guide nodded, because hushy sounds are kind to sleepy ears.")
        return
    if world.setting.indoors and sound.loudness >= 2.0:
        world.say(f"{child.id} wanted to {sound.say}, but the little hall held its breath.")
        world.say(f"From the next room, a sleepy kitten twitched its whiskers.")
    else:
        world.say(f"{child.id} wanted to {sound.say}, and the republic clapped along in a little circle.")
    world.say(f"Still, the guide worried that too much {sound.phrase} might startle the nap-time hush.")


def resolve(world: World, child: Entity, guide: Entity, sound: SoundEffect, prop: Prop) -> None:
    if sound.id == "whisper":
        child.memes["joy"] += 1
        child.memes["confidence"] += 1
        world.say(f"So {child.id} said it again, soft as a feather: {sound.phrase}.")
        world.say(f"The tiny republic listened, and the nap-time hush stayed cozy.")
        return
    if world.setting.indoors and sound.loudness >= 2.0:
        if prop.id == "pillow":
            world.say(f"Then {guide.label_word} brought {prop.phrase}, and {child.id} tapped it like a drum with a cloud on top.")
        else:
            world.say(f"Then {guide.label_word} lifted {prop.phrase}, and {child.id} used it to make the beat softer.")
        child.meters["noise"] += prop.help_noise
        child.meters["softness"] += prop.help_softness
    else:
        world.say(f"Then {child.id} used {prop.phrase}, and the sound changed into a gentler little patter.")

    child.memes["confidence"] += 1
    child.memes["joy"] += 1
    world.say(f"{child.id} could still {sound.say}, only now the sound was kinder: {sound.rhyme}.")
    world.say(f"That was enough for the republic, and the square went bright with smiles.")


def finish(world: World, child: Entity, guide: Entity, sound: SoundEffect) -> None:
    world.para()
    world.say(f"At the end, {child.id} was still singing the little rhyme, {sound.rhyme}, {sound.rhyme}.")
    world.say(f"The guide laughed, and the republic went on in peace, soft feet, and happy echoes.")


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    child = next(e for e in world.characters() if e.id == params.name)
    guide = world.get("Guide")
    sound = SOUND_EFFECTS[params.sound]
    prop = PROPS[params.prop]

    world.para()
    narrative_turn(world, child, guide, sound, prop)
    resolve(world, child, guide, sound, prop)
    finish(world, child, guide, sound)

    world.facts = {
        "child": child,
        "guide": guide,
        "sound": sound,
        "prop": prop,
        "setting": world.setting,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    sound = f["sound"]
    return [
        f'Write a short nursery-rhyme style story about a tiny republic where {child.id} says "{sound.phrase}".',
        f"Tell a gentle story with a republic, a child, and the sound effect {sound.phrase}, ending in a soft resolution.",
        f'Write a child-friendly story that uses the words "republic" and "say" and includes the sound "{sound.phrase}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    sound = f["sound"]
    prop = f["prop"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who wanted to say {sound.phrase} in the tiny republic?",
            answer=f"{child.id} wanted to say {sound.phrase} in {setting.place}, and {guide.label_word} listened with care.",
        ),
        QAItem(
            question=f"Why did the guide worry when {child.id} tried to say {sound.phrase}?",
            answer=f"The guide worried that {sound.phrase} might be too loud for {setting.place}, especially before the hush of nap time.",
        ),
        QAItem(
            question=f"What helped {child.id} make the sound gentler?",
            answer=f"{prop.phrase} helped {child.id} turn the sound into something softer and kinder.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    sound = f["sound"]
    out = [
        QAItem(
            question="What is a republic?",
            answer="A republic is a kind of government where people share decisions instead of having a king or queen in charge.",
        ),
        QAItem(
            question="What does it mean to say a sound effect?",
            answer="It means to speak a word like ding-ding, clap-clap, or shh-shh so the sound helps tell the story or set the mood.",
        ),
        QAItem(
            question="Why can soft sounds be helpful?",
            answer="Soft sounds can be helpful because they do not wake sleeping babies, kittens, or other quiet little listeners.",
        ),
    ]
    if sound.id == "whisper":
        out.append(
            QAItem(
                question="What is a whisper?",
                answer="A whisper is a very quiet way to speak, almost like your words are tiptoeing.",
            )
        )
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 3) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for sid, s in SOUND_EFFECTS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("sound_phrase", sid, s.phrase))
        if s.loudness >= 2.0:
            lines.append(asp.fact("loud", sid))
        if s.softness >= 0.8:
            lines.append(asp.fact("soft", sid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if p.help_softness >= 0.8:
            lines.append(asp.fact("gentle", pid))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S, P, Place) :- affords(Place, S), sound(S), prop(P), not impossible(S, P, Place).
impossible(S, P, Place) :- loud(S), indoors(Place), not gentle(P).
#show compatible/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set((p, s, pr) for p, s, pr in valid_combos())
    cl = set(asp_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.sound and args.prop:
        if not reasonableness_gate(SETTINGS[args.place], SOUND_EFFECTS[args.sound], PROPS[args.prop]):
            raise StoryError(explain_rejection(SETTINGS[args.place], SOUND_EFFECTS[args.sound], PROPS[args.prop]))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.sound is None or c[1] == args.sound)
        and (args.prop is None or c[2] == args.prop)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, sound, prop = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or select_name(gender, rng)
    guide = args.guide or rng.choice(["mayor", "neighbor"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, sound=sound, prop=prop, name=name, gender=gender, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


CURATED = [
    StoryParams(place="square", sound="clap", prop="ribbon", name="Mia", gender="girl", guide="mayor", trait="cheerful"),
    StoryParams(place="hall", sound="whisper", prop="pillow", name="Leo", gender="boy", guide="neighbor", trait="gentle"),
    StoryParams(place="garden", sound="tap", prop="broom", name="Nora", gender="girl", guide="neighbor", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_combos()
        print(f"{len(combos)} compatible (place, sound, prop) combos:\n")
        for place, sound, prop in combos:
            print(f"  {place:8} {sound:9} {prop}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.sound} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
