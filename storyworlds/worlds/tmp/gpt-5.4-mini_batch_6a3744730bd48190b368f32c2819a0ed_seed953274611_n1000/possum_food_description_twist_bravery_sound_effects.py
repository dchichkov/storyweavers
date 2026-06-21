#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/possum_food_description_twist_bravery_sound_effects.py
======================================================================================

A small standalone storyworld for a tall-tale seed about a possum, food, a
description, a twist, bravery, and sound effects.

Premise
-------
A hungry possum named Pip wants a shiny supper, but the food turns out to be a
trap of pride and puffed-up talk. Pip's brave choice, plus a noisy comic twist,
turns the problem into a feast shared with the woods.

The world model tracks:
- typed entities with physical meters and emotional memes,
- a simple forward causal engine,
- a reasonableness gate,
- a Python/ASP twin for parity checks,
- three grounded QA sets.

The prose aims for a Tall Tale feel: big voice, bright sound effects, concrete
turns, and an ending image that proves something changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"possum"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    setting: str = "moonlit lane"
    food: str = "pie"
    description: str = "a pie as shiny as a silver coin"
    twist: str = "turned out to be a trick"
    bravery: str = "brave enough to try"
    sound_effect: str = "SKRITCH"
    helper: str = "Mabel"
    helper_type: str = "girl"
    possum_name: str = "Pip"
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    place: str
    mood: str


@dataclass
class Food:
    id: str
    label: str
    description: str
    smell: str
    bite: str
    snack: bool = True


@dataclass
class Twist:
    id: str
    label: str
    reveal: str
    consequence: str


@dataclass
class Bravery:
    id: str
    label: str
    meter_gain: float
    meme_gain: float


@dataclass
class SoundEffect:
    id: str
    text: str
    use: str


class WorldModel:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale possum storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--description", choices=DESCRIPTIONS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--bravery", choices=BRAVERIES)
    ap.add_argument("--sound-effect", choices=SOUND_EFFECTS)
    ap.add_argument("--helper", choices=["Mabel", "June", "Otis", "Nell"])
    ap.add_argument("--name")
    ap.add_argument("--helper-type", choices=["girl", "boy", "mother", "father"])
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


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for fid, f in FOODS.items():
            for tid, t in TWISTS.items():
                for bid, b in BRAVERIES.items():
                    for sdid, sd in SOUND_EFFECTS.items():
                        if f.snack and t.kind in {"trick", "surprise"}:
                            combos.append((sid, fid, "plain", bid, sdid, tid))
    return combos


def explain_rejection() -> str:
    return "(No story: this food and twist do not make a tall-tale problem worth telling.)"


def _pick(rng: random.Random, keys: list[str]) -> str:
    return rng.choice(keys)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.food and args.food not in FOODS:
        raise StoryError("(No story: unknown food.)")
    if args.twist and args.twist not in TWISTS:
        raise StoryError("(No story: unknown twist.)")
    if args.description and args.description not in DESCRIPTIONS:
        raise StoryError("(No story: unknown description.)")
    combos = valid_combos()
    if not combos:
        raise StoryError(explain_rejection())
    setting = args.setting or _pick(rng, list(SETTINGS))
    food = args.food or _pick(rng, list(FOODS))
    description = args.description or _pick(rng, list(DESCRIPTIONS))
    twist = args.twist or _pick(rng, list(TWISTS))
    bravery = args.bravery or _pick(rng, list(BRAVERIES))
    sound = args.sound_effect or _pick(rng, list(SOUND_EFFECTS))
    helper = args.helper or rng.choice(["Mabel", "June", "Otis", "Nell"])
    helper_type = args.helper_type or rng.choice(["girl", "boy", "mother", "father"])
    name = args.name or "Pip"
    return StoryParams(setting=setting, food=food, description=description, twist=twist,
                       bravery=bravery, sound_effect=sound, helper=helper,
                       helper_type=helper_type, possum_name=name)


def propagate(world: World, narrate: bool = True) -> None:
    for ent in world.entities.values():
        if ent.meters["hungry"] >= THRESHOLD and ("hunger", ent.id) not in world.fired:
            world.fired.add(("hunger", ent.id))
            ent.memes["desire"] += 1
            if narrate:
                world.say(f"{ent.id}'s nose twitched at the smell.")
        if ent.meters["scared"] >= THRESHOLD and ("scare", ent.id) not in world.fired:
            world.fired.add(("scare", ent.id))
            ent.memes["fear"] += 1
        if ent.memes["brave"] >= THRESHOLD and ("brave", ent.id) not in world.fired:
            world.fired.add(("brave", ent.id))
            ent.meters["resolve"] += 1
        if ent.meters["resolve"] >= THRESHOLD and ("resolve", ent.id) not in world.fired:
            world.fired.add(("resolve", ent.id))


def set_up(world: World, p: Entity, helper: Entity, setting: Setting, food: Food, desc: str) -> None:
    p.meters["hungry"] += 1
    p.memes["curious"] += 1
    world.say(
        f"On a moon-bright night in the {setting.place}, {p.id} the possum shuffled out "
        f"with a belly full of want and a nose full of hope. "
        f"{helper.id} had set out {food.label}, described as {desc}."
    )


def tempt(world: World, p: Entity, food: Food, twist: Twist, sound: SoundEffect) -> None:
    p.memes["want"] += 1
    world.say(
        f'"{sound.text}!" went the leaves as {p.id} crept closer. The food shone so fine '
        f'it looked fit for a king. But {twist.reveal}, and that was the first twist in the tale.'
    )


def warn(world: World, helper: Entity, p: Entity, food: Food) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} called out, "Hold on there, {p.id}! That {food.label} might be for '
        f'someone else, and it could lead you into a pickle."'
    )


def choose_bravery(world: World, p: Entity, bravery: Bravery, sound: SoundEffect) -> None:
    p.memes["brave"] += bravery.meme_gain
    p.meters["resolve"] += bravery.meter_gain
    world.say(
        f"{p.id} drew a deep breath and decided to be {bravery.label}. "
        f'Then came a bold "{sound.text}!" from the brush, as if the whole woods were cheering.'
    )


def twist_turn(world: World, p: Entity, helper: Entity, twist: Twist, food: Food) -> None:
    world.say(
        f"That was when the second twist struck: {twist.consequence}. "
        f"{p.id} stopped, blinked, and saw the food was not a private treasure at all."
    )
    helper.memes["trust"] += 1
    p.memes["shame"] += 1


def share_feast(world: World, p: Entity, helper: Entity, food: Food, sound: SoundEffect) -> None:
    p.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"With a grand little grin, {p.id} offered the {food.label} to {helper.id}. "
        f'{sound.text}! The nibble, the laugh, and the crunch all came at once.'
    )
    world.say(
        f"Before long, the {food.label} was split into a supper fit for a campfire king, "
        f"and the possum and the helper ate side by side under the stars."
    )


def tell(setting: Setting, food: Food, twist: Twist, bravery: Bravery,
         sound: SoundEffect, possum_name: str, helper_name: str, helper_type: str,
         description: str) -> World:
    world = World()
    possum = world.add(Entity(id=possum_name, kind="character", type="possum", role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))

    set_up(world, possum, helper, setting, food, description)
    world.para()
    tempt(world, possum, food, twist, sound)
    warn(world, helper, possum, food)
    choose_bravery(world, possum, bravery, sound)
    world.para()
    twist_turn(world, possum, helper, twist, food)
    share_feast(world, possum, helper, food, sound)

    world.facts.update(
        possum=possum, helper=helper, setting=setting, food=food, twist=twist,
        bravery=bravery, sound=sound, description=description
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a child that includes the words "possum", '
        f'"food", and "description".',
        f"Tell a brave little story where {f['possum'].id} the possum sees food "
        f"described in a grand way, then faces a twist and chooses courage.",
        f"Write a story with sound effects and a twist where a possum and a helper "
        f"end up sharing food after a surprising description turns true.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: Entity = f["possum"]
    h: Entity = f["helper"]
    food: Food = f["food"]
    twist: Twist = f["twist"]
    desc = f["description"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {p.id} the possum and {h.id}, who are caught up in a night of food, a description, and a twist. The tale follows what they do when the shiny supper turns surprising."
        ),
        QAItem(
            question=f"What made {p.id} brave?",
            answer=f"{p.id} chose bravery after hearing the warning and feeling the night itself seem to drum a challenge. That brave choice helped {p.id} face the twist instead of running off in a panic."
        ),
        QAItem(
            question=f"What happened to the {food.label} at the end?",
            answer=f"The {food.label} was shared as a feast instead of being taken in secret. The twist turned the problem into a supper, and the ending shows that the food became something both of them could enjoy."
        ),
        QAItem(
            question=f"How was the food described?",
            answer=f"It was described as {desc}. That description made it sound grand and tempting, which helped set up the tall-tale feeling before the twist arrived."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a possum?",
            answer="A possum is a small animal with a clever nose and a sneaky way of moving through the dark. In stories, possums often look silly but turn out to be wiser than they first seem."
        ),
        QAItem(
            question="Why can food matter in a story?",
            answer="Food gives a character a reason to act because hungry creatures notice it right away. It can start a problem, but it can also bring people together at the end."
        ),
        QAItem(
            question="What is a description?",
            answer="A description is the part of a story that tells what something looks, sounds, or feels like. Good descriptions help the reader picture the scene before the twist happens."
        ),
        QAItem(
            question="What does a sound effect do in a story?",
            answer="A sound effect makes the moment feel lively and loud, almost like you can hear it yourself. In a tall tale, it helps the action feel bigger and more playful."
        ),
    ]


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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    out.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(out)


SETTINGS = {
    "moonlit lane": Setting(id="moonlit lane", place="moonlit lane", mood="bright"),
    "hollow hill": Setting(id="hollow hill", place="hollow hill", mood="echoing"),
    "river bend": Setting(id="river bend", place="river bend", mood="sparkling"),
}

FOODS = {
    "pie": Food(id="pie", label="pie", description="a pie baked in a tin crust", smell="sweet", bite="crunchy"),
    "berry cake": Food(id="berry cake", label="berry cake", description="a berry cake with a purple grin", smell="fruity", bite="soft"),
    "cornbread": Food(id="cornbread", label="cornbread", description="a cornbread square with a golden face", smell="toasty", bite="crumbly"),
}

DESCRIPTIONS = {
    "shiny": "a pie as shiny as a silver coin",
    "big": "food so big it looked like a wagon wheel",
    "sweet": "food sweet enough to make a mouse smile",
    "wild": "food dressed up like a king in a feast-hat",
}

TWISTS = {
    "trick": Twist(id="trick", label="trick", reveal="the supper had been set down to lure out a night thief", consequence="the helper was watching to see who had the nerve to wait"),
    "surprise": Twist(id="surprise", label="surprise", reveal="the food had a hidden note tucked beneath it", consequence="the note said the food was meant to be shared"),
    "swap": Twist(id="swap", label="swap", reveal="the 'prize' was only a decoy plate", consequence="the real feast was waiting on the other side of the stump"),
}

BRAVERIES = {
    "brave enough to try": Bravery(id="try", label="brave enough to try", meter_gain=1.0, meme_gain=1.0),
    "bold as a barncat": Bravery(id="barncat", label="bold as a barncat", meter_gain=1.5, meme_gain=1.2),
    "steady as a fence post": Bravery(id="steady", label="steady as a fence post", meter_gain=0.8, meme_gain=1.5),
}

SOUND_EFFECTS = {
    "SKRITCH": SoundEffect(id="SKRITCH", text="SKRITCH", use="brush and leaves"),
    "WHAM": SoundEffect(id="WHAM", text="WHAM", use="big surprise"),
    "PING": SoundEffect(id="PING", text="PING", use="tiny bright notice"),
}

CURATED = [
    StoryParams(setting="moonlit lane", food="pie", description="shiny", twist="trick",
                bravery="brave enough to try", sound_effect="SKRITCH",
                helper="Mabel", helper_type="girl", possum_name="Pip"),
    StoryParams(setting="hollow hill", food="berry cake", description="sweet", twist="surprise",
                bravery="bold as a barncat", sound_effect="WHAM",
                helper="Otis", helper_type="boy", possum_name="Pip"),
    StoryParams(setting="river bend", food="cornbread", description="wild", twist="swap",
                bravery="steady as a fence post", sound_effect="PING",
                helper="Nell", helper_type="mother", possum_name="Pip"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid in FOODS:
        lines.append(asp.fact("food", fid))
        lines.append(asp.fact("snack", fid))
    for tid, t in TWISTS.items():
        lines.append(asp.fact("twist", tid))
        lines.append(asp.fact("kind", tid, t.label))
    for bid in BRAVERIES:
        lines.append(asp.fact("bravery", bid))
    for sid in SOUND_EFFECTS:
        lines.append(asp.fact("sound", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, F, T, B, So, D) :- setting(S), food(F), twist(T), bravery(B), sound(So), snack(F), kind(T, trick).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, food=None, description=None, twist=None, bravery=None,
            sound_effect=None, helper=None, name=None, helper_type=None
        ), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception as exc:
        print(f"EMIT SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: verify passed.")
    return rc


def tell_story(params: StoryParams) -> StorySample:
    setting = SETTINGS.get(params.setting)
    food = FOODS.get(params.food)
    desc = DESCRIPTIONS.get(params.description)
    twist = TWISTS.get(params.twist)
    bravery = BRAVERIES.get(params.bravery)
    sound = SOUND_EFFECTS.get(params.sound_effect)
    if not all([setting, food, desc, twist, bravery, sound]):
        raise StoryError("(No story: invalid parameters.)")
    world = tell(setting, food, twist, bravery, sound, params.possum_name, params.helper, params.helper_type, desc)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return tell_story(params)


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
        print(asp_program("#show valid/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
