#!/usr/bin/env python3
"""
candle_vivid_dentist_office_moral_value_transformation_4.py
===========================================================

A myth-toned dentist-office storyworld built around a vivid candle,
misunderstanding, moral repair, and visible transformation.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STORYWORLDS = Path(__file__).resolve().parents[1]
for base in (ROOT, STORYWORLDS):
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Chamber:
    key: str
    phrase: str
    chair: str
    basin: str
    candle_holder: str
    keeper: str
    room_image: str
    allowed_misunderstandings: tuple[str, ...]


@dataclass(frozen=True)
class Misunderstanding:
    key: str
    belief: str
    fear_result: str
    correction: str
    allowed_morals: tuple[str, ...]


@dataclass(frozen=True)
class Transformation:
    key: str
    initial_form: str
    final_form: str
    visible_change: str
    ending_image: str


@dataclass(frozen=True)
class MoralValue:
    key: str
    title: str
    hidden_trouble: str
    confession: str
    repair_action: str
    promise: str
    teaching: str
    keepsake: str
    transformation: str


@dataclass
class StoryParams:
    chamber: str
    misunderstanding: str
    moral: str
    transformation: str
    hero: str
    gender: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    inventory: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class World:
    params: StoryParams
    chamber: Chamber
    misunderstanding: Misunderstanding
    moral: MoralValue
    transformation: Transformation
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    lesson_focus: str = ""
    initial_hero_meters: dict[str, float] = field(default_factory=dict)
    initial_hero_memes: dict[str, float] = field(default_factory=dict)
    story: str = ""

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        lines.append(f"  chamber={self.chamber.key}")
        lines.append(f"  misunderstanding={self.misunderstanding.key}")
        lines.append(f"  moral={self.moral.key}")
        lines.append(f"  transformation={self.transformation.key}")
        for key, entity in self.entities.items():
            lines.append(f"  {key}: {entity.name} [{entity.kind}] @ {entity.location}")
            if entity.meters:
                meter_bits = ", ".join(f"{name}={value:.2f}" for name, value in sorted(entity.meters.items()))
                lines.append(f"    meters: {meter_bits}")
            if entity.memes:
                meme_bits = ", ".join(f"{name}={value:.2f}" for name, value in sorted(entity.memes.items()))
                lines.append(f"    memes: {meme_bits}")
            if entity.inventory:
                lines.append(f"    inventory: {', '.join(entity.inventory)}")
            if entity.notes:
                lines.append(f"    notes: {', '.join(entity.notes)}")
        lines.append(f"  events: {', '.join(self.events) if self.events else 'none'}")
        lines.append(f"  lesson_focus={self.lesson_focus}")
        return "\n".join(lines)


CHAMBERS: dict[str, Chamber] = {
    "pearl_chair": Chamber(
        key="pearl_chair",
        phrase="a dentist office of pearl tiles and sea-bright glass",
        chair="the pearl chair shaped like a moon boat",
        basin="a shell-bright rinsing basin",
        candle_holder="a blue glass cup",
        keeper="Doctor Samira",
        room_image="silver tools hung like small constellations above the chair",
        allowed_misunderstandings=("judgment_flame", "dragon_flame"),
    ),
    "shell_basin": Chamber(
        key="shell_basin",
        phrase="a dentist office built around a shell-carved basin",
        chair="the high white chair with carved armrests",
        basin="the shell basin that sang when water touched it",
        candle_holder="a cup of green enamel",
        keeper="Doctor Ilyas",
        room_image="mint steam drifted between jars and the mirror caught it like mist",
        allowed_misunderstandings=("judgment_flame", "lost_tooth_signal"),
    ),
    "mint_cabinet": Chamber(
        key="mint_cabinet",
        phrase="a dentist office with cedar cabinets and bright mint jars",
        chair="the cedar-backed chair under the round mirror",
        basin="a white basin cool as river stone",
        candle_holder="a small brass lantern cup",
        keeper="Doctor Thalia",
        room_image="painted stars shone on the cabinet doors above the folded bibs",
        allowed_misunderstandings=("dragon_flame", "lost_tooth_signal"),
    ),
}


MISUNDERSTANDINGS: dict[str, Misunderstanding] = {
    "judgment_flame": Misunderstanding(
        key="judgment_flame",
        belief="the vivid candle was counting the lies of children",
        fear_result="Every flicker felt like a warning that a confession would bring shame instead of help.",
        correction="the candle was only a healing light, lit so hidden trouble could be seen gently and mended early",
        allowed_morals=("truthfulness", "care"),
    ),
    "dragon_flame": Misunderstanding(
        key="dragon_flame",
        belief="the vivid candle was feeding a tiny tooth-dragon inside the buzzing tools",
        fear_result="The child imagined that any sound from the tray meant the dragon had smelled fear and would bite harder.",
        correction="the flame was there to warm the room and steady the keeper's hands, not to feed pain or danger",
        allowed_morals=("care", "courage"),
    ),
    "lost_tooth_signal": Misunderstanding(
        key="lost_tooth_signal",
        belief="the vivid candle was a signal for children whose teeth were beyond saving",
        fear_result="Its glow made the room seem like a harbor of farewell instead of a place of repair.",
        correction="the light meant welcome, and it told the keeper to look with patience before any tooth trouble became worse",
        allowed_morals=("truthfulness", "courage"),
    ),
}


TRANSFORMATIONS: dict[str, Transformation] = {
    "wax_lion_moth": Transformation(
        key="wax_lion_moth",
        initial_form="a little wax lion crouched at the candle's base",
        final_form="a pearl moth",
        visible_change="the wax lion softened, opened pale wings, and rose as a pearl moth",
        ending_image="The pearl moth circled the basin once and rested beside the vivid candle as if mercy had found a perch.",
    ),
    "ember_to_blue": Transformation(
        key="ember_to_blue",
        initial_form="a narrow red flame in the cup",
        final_form="a blue lily of fire",
        visible_change="the narrow red flame widened into a blue lily of fire",
        ending_image="The blue flame shone in the cup glass until even the mirror looked calm and kind.",
    ),
    "shadow_to_bridge": Transformation(
        key="shadow_to_bridge",
        initial_form="a hooked shadow beneath the chair",
        final_form="a silver bridge in the mirror",
        visible_change="the hooked shadow beneath the chair straightened into a silver bridge inside the mirror",
        ending_image="The silver bridge lay across the round mirror as if fear itself had learned the way home.",
    ),
}


MORALS: dict[str, MoralValue] = {
    "truthfulness": MoralValue(
        key="truthfulness",
        title="truthfulness",
        hidden_trouble="that sticky fig sweets had been eaten after brushing, and the ache had been hidden all morning",
        confession="admitted the midnight sweets and the secret ache at last",
        repair_action="The keeper rinsed the sore tooth, found the sweet fibers caught near the gum, and explained that honest words let help arrive before pain grows proud.",
        promise="to speak early when pain or trouble begins",
        teaching="Truth opens the door that fear tries to bar.",
        keepsake="a cool coil of mint thread",
        transformation="wax_lion_moth",
    ),
    "care": MoralValue(
        key="care",
        title="care",
        hidden_trouble="that the moon-thread for cleaning had been left folded away for three nights",
        confession="confessed that the small cleaning thread had been ignored because one missed night had seemed too small to matter",
        repair_action="Together they drew the mint thread between the teeth, slow as a river through reeds, until the trapped sweetness was gone and the sore place could breathe.",
        promise="to guard the small places before trouble grows large",
        teaching="Small acts of care protect a body better than grand excuses.",
        keepsake="a fresh spool of moon-thread",
        transformation="ember_to_blue",
    ),
    "courage": MoralValue(
        key="courage",
        title="courage",
        hidden_trouble="that a sharp ache had been hidden behind brave nods and a tight smile",
        confession="asked at last why the tooth hurt and why the bright tools sang when they touched the tray",
        repair_action="The keeper named each tool, let the child touch the mirror handle, and cleaned the aching tooth while every step was explained in plain, gentle words.",
        promise="to ask questions before fear invents its own answers",
        teaching="A brave question can quiet a whole storm of guessing.",
        keepsake="a tiny silver mirror charm",
        transformation="shadow_to_bridge",
    ),
}


HEROES: dict[str, tuple[str, ...]] = {
    "girl": ("Mira", "Suri", "Lina", "Nadia", "Leila"),
    "boy": ("Tomas", "Ilan", "Milo", "Ari", "Jonah"),
}


def _pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def valid_combo(
    chamber_key: str,
    misunderstanding_key: str,
    moral_key: str,
    transformation_key: str,
) -> bool:
    if chamber_key not in CHAMBERS:
        return False
    if misunderstanding_key not in MISUNDERSTANDINGS:
        return False
    if moral_key not in MORALS:
        return False
    if transformation_key not in TRANSFORMATIONS:
        return False

    chamber = CHAMBERS[chamber_key]
    misunderstanding = MISUNDERSTANDINGS[misunderstanding_key]
    moral = MORALS[moral_key]
    if misunderstanding_key not in chamber.allowed_misunderstandings:
        return False
    if moral_key not in misunderstanding.allowed_morals:
        return False
    return transformation_key == moral.transformation


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for chamber_key in sorted(CHAMBERS):
        for misunderstanding_key in sorted(MISUNDERSTANDINGS):
            for moral_key in sorted(MORALS):
                for transformation_key in sorted(TRANSFORMATIONS):
                    if valid_combo(chamber_key, misunderstanding_key, moral_key, transformation_key):
                        combos.append((chamber_key, misunderstanding_key, moral_key, transformation_key))
    return combos


def describe_rejection(
    chamber_key: str,
    misunderstanding_key: str,
    moral_key: str,
    transformation_key: str,
) -> str:
    if chamber_key not in CHAMBERS:
        return f"No story: unknown chamber {chamber_key!r}."
    if misunderstanding_key not in MISUNDERSTANDINGS:
        return f"No story: unknown misunderstanding {misunderstanding_key!r}."
    if moral_key not in MORALS:
        return f"No story: unknown moral value {moral_key!r}."
    if transformation_key not in TRANSFORMATIONS:
        return f"No story: unknown transformation {transformation_key!r}."
    chamber = CHAMBERS[chamber_key]
    misunderstanding = MISUNDERSTANDINGS[misunderstanding_key]
    moral = MORALS[moral_key]
    if misunderstanding_key not in chamber.allowed_misunderstandings:
        return f"No story: {chamber.phrase} does not support the {misunderstanding_key.replace('_', ' ')} misunderstanding."
    if moral_key not in misunderstanding.allowed_morals:
        return f"No story: the {misunderstanding_key.replace('_', ' ')} misunderstanding does not plausibly turn on {moral.title}."
    return f"No story: {transformation_key.replace('_', ' ')} does not match the chosen moral turn."


def _hero_initial_meters(moral_key: str) -> dict[str, float]:
    base = {
        "tooth_pain": 0.58 if moral_key in {"truthfulness", "courage"} else 0.42,
        "tooth_cleanliness": 0.28 if moral_key == "care" else 0.46,
        "posture": 0.37,
    }
    return {key: _clamp(value) for key, value in base.items()}


def _hero_initial_memes(misunderstanding_key: str, moral_key: str) -> dict[str, float]:
    fear = {
        "judgment_flame": 0.78,
        "dragon_flame": 0.82,
        "lost_tooth_signal": 0.74,
    }[misunderstanding_key]
    honesty = 0.30 if moral_key == "truthfulness" else 0.40
    trust = 0.25 if moral_key != "courage" else 0.20
    wonder = 0.18
    return {
        "fear": fear,
        "trust": trust,
        "honesty": honesty,
        "wonder": wonder,
        "care": 0.35 if moral_key == "care" else 0.28,
        "courage": 0.55 if moral_key == "courage" else 0.32,
    }


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.chamber, params.misunderstanding, params.moral, params.transformation):
        raise StoryError(
            describe_rejection(
                params.chamber,
                params.misunderstanding,
                params.moral,
                params.transformation,
            )
        )

    chamber = CHAMBERS[params.chamber]
    misunderstanding = MISUNDERSTANDINGS[params.misunderstanding]
    moral = MORALS[params.moral]
    transformation = TRANSFORMATIONS[params.transformation]

    hero = Entity(
        name=params.hero,
        kind="child",
        location="dentist_office",
        meters=_hero_initial_meters(params.moral),
        memes=_hero_initial_memes(params.misunderstanding, params.moral),
        notes=[misunderstanding.belief],
    )
    keeper = Entity(
        name=chamber.keeper,
        kind="dentist_keeper",
        location="dentist_office",
        meters={"steadiness": 0.96, "voice_warmth": 0.92},
        memes={"patience": 0.98, "kindness": 0.95, "wisdom": 0.91},
    )
    candle = Entity(
        name="the vivid candle",
        kind="healing_light",
        location="dentist_office",
        meters={"brightness": 0.88, "wax_height": 0.64},
        memes={"welcome": 0.80, "mercy": 0.84},
        notes=[transformation.initial_form],
    )
    tooth = Entity(
        name="the aching tooth",
        kind="body_part",
        location=f"{params.hero}'s mouth",
        meters={
            "soreness": 0.62 if params.moral in {"truthfulness", "courage"} else 0.36,
            "cleanliness": hero.meters["tooth_cleanliness"],
        },
        memes={},
    )

    world = World(
        params=params,
        chamber=chamber,
        misunderstanding=misunderstanding,
        moral=moral,
        transformation=transformation,
        initial_hero_meters=dict(hero.meters),
        initial_hero_memes=dict(hero.memes),
        entities={
            "hero": hero,
            "keeper": keeper,
            "candle": candle,
            "tooth": tooth,
        },
    )

    world.events.append("arrival_in_dentist_office")
    world.events.append(f"misread_candle_as_{misunderstanding.key}")
    world.events.append("fear_hides_truth")

    hero.memes["fear"] = _clamp(hero.memes["fear"] - 0.38)
    hero.memes["trust"] = _clamp(hero.memes["trust"] + 0.56)
    hero.memes["wonder"] = _clamp(hero.memes["wonder"] + 0.60)
    hero.memes["honesty"] = _clamp(hero.memes["honesty"] + (0.52 if params.moral == "truthfulness" else 0.22))
    hero.memes["care"] = _clamp(hero.memes["care"] + (0.50 if params.moral == "care" else 0.16))
    hero.memes["courage"] = _clamp(hero.memes["courage"] + (0.38 if params.moral == "courage" else 0.12))
    hero.meters["posture"] = _clamp(hero.meters["posture"] + 0.45)
    hero.meters["tooth_cleanliness"] = _clamp(hero.meters["tooth_cleanliness"] + (0.42 if params.moral == "care" else 0.20))
    tooth.meters["cleanliness"] = hero.meters["tooth_cleanliness"]
    tooth.meters["soreness"] = _clamp(tooth.meters["soreness"] - 0.28)
    candle.meters["brightness"] = _clamp(candle.meters["brightness"] + 0.07)
    candle.meters["wax_height"] = _clamp(candle.meters["wax_height"] - 0.08)

    hero.inventory.append(moral.keepsake)
    hero.notes.append(moral.promise)
    world.events.append(f"embraced_{moral.key}")
    world.events.append(f"transformation_{transformation.key}")
    world.lesson_focus = moral.teaching
    return world


def _opening(world: World) -> list[str]:
    hero = world.entities["hero"]
    initial_meters = world.initial_hero_meters
    initial_memes = world.initial_hero_memes
    pain_line = (
        "A quiet throb kept tapping from the back tooth."
        if initial_meters["tooth_pain"] >= 0.5
        else "The mouth was not in great pain yet, but something still felt wrong."
    )
    fear_line = (
        "Fear made the white room feel larger than it truly was."
        if initial_memes["fear"] < 0.80
        else "Fear made the white room feel as wide as a temple hall."
    )
    return [
        f"In {world.chamber.phrase}, {hero.name} climbed onto {world.chamber.chair}, and a vivid candle burned in {world.chamber.candle_holder} beside {world.chamber.basin}.",
        f"{world.chamber.room_image.capitalize()}. {pain_line}",
        f"Yet {hero.name} believed {world.misunderstanding.belief}. {world.misunderstanding.fear_result} {fear_line}",
    ]


def _turn(world: World) -> list[str]:
    hero = world.entities["hero"]
    trust_line = (
        "The keeper's calm explanation gave the room back its true shape."
        if hero.memes["trust"] >= 0.70
        else "The explanation helped, though the child still sat stiffly for a breath."
    )
    repair_line = (
        "When the cleaning was done, the sore place no longer ruled the child's thoughts."
        if world.entities["tooth"].meters["soreness"] <= 0.40
        else "The sore place eased enough for the child to breathe without flinching."
    )
    return [
        f"{world.chamber.keeper} looked at the trembling hands and said that {world.misunderstanding.correction}.",
        f"Then {hero.name} {world.moral.confession}. {world.moral.repair_action}",
        f"{trust_line} {repair_line}",
    ]


def _ending(world: World) -> list[str]:
    hero = world.entities["hero"]
    wonder_line = (
        "Wonder rose where dread had been."
        if hero.memes["wonder"] >= 0.70
        else "The last of the fear drifted away."
    )
    posture_line = (
        f"{hero.name} left the dentist office standing straighter, with {world.moral.keepsake} in hand."
        if hero.meters["posture"] >= 0.75
        else f"{hero.name} left the dentist office more settled than before, carrying {world.moral.keepsake}."
    )
    return [
        f"At that moment, {world.transformation.visible_change}. {world.transformation.ending_image}",
        f"{posture_line} A promise stayed close: {world.moral.promise}.",
        f"{wonder_line} {world.moral.teaching}",
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = "\n\n".join([
        " ".join(_opening(world)),
        " ".join(_turn(world)),
        " ".join(_ending(world)),
    ])
    world.story = story

    hero = world.entities["hero"].name
    prompts = [
        f"Write a myth-like dentist office story about {hero}, a vivid candle, and a misunderstanding that turns into wisdom.",
        f"Use {world.moral.title} as the moral value, and show {world.transformation.final_form} as the visible transformation.",
        "Keep the story child-facing, concrete, and complete, with a clear turn and ending image.",
    ]

    story_qa = [
        QAItem(
            "What did the child misunderstand at the beginning?",
            f"{hero} misunderstood the vivid candle and believed {world.misunderstanding.belief}. That mistake changed the whole mood of the dentist office, because fear made help look like danger.",
        ),
        QAItem(
            "Why did the child keep quiet at first?",
            f"The child stayed quiet because {world.misunderstanding.fear_result.lower()} Hiding {world.moral.hidden_trouble} seemed safer than speaking, at least until the keeper explained the truth.",
        ),
        QAItem(
            "What changed the middle of the story?",
            f"{world.chamber.keeper} corrected the misunderstanding and spoke gently about what the candle meant. After that, {hero} {world.moral.confession}, which let the real healing begin.",
        ),
        QAItem(
            "How did the moral value appear in action?",
            f"The moral value was {world.moral.title}, and it appeared through a concrete choice rather than a sermon. {world.moral.repair_action}",
        ),
        QAItem(
            "What transformed at the end, and why did it matter?",
            f"At the end, {world.transformation.visible_change}. That image mattered because it showed the room had changed in the child's eyes once fear gave way to understanding.",
        ),
        QAItem(
            "What lesson did the child carry away?",
            f"{hero} carried away this lesson: {world.moral.teaching} The promise to keep was {world.moral.promise}, so the ending joins wisdom to a future habit.",
        ),
    ]

    world_qa = [
        QAItem(
            "Why might a myth-like dentist office keep a small candle or lamp burning?",
            "A small light can symbolize welcome, clarity, or patient attention. In a healing room, that kind of symbol tells a child that hidden trouble should be noticed gently rather than ignored.",
        ),
        QAItem(
            "What should a child do when a tool or room feels frightening?",
            "The child should ask what the tool is for and what will happen next. A clear explanation often shrinks fear, because guessing usually makes a room seem harsher than it is.",
        ),
        QAItem(
            "Why do little cleaning habits matter so much for teeth?",
            "Small habits matter because trouble often starts in tiny places between meals and between teeth. Daily care prevents a small problem from growing into pain that feels sudden later.",
        ),
        QAItem(
            "How can honesty help during tooth care?",
            "Honesty helps the dentist find the real cause of pain or soreness sooner. It also turns the visit into teamwork, because care works best when the child and the healer are speaking about the same truth.",
        ),
    ]

    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts"]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.extend(["", "== (2) Story-grounded QA"])
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.extend(["", "== (3) World-knowledge QA"])
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Myth-like dentist office storyworld with a vivid candle and moral transformation.")
    parser.add_argument("--chamber", choices=sorted(CHAMBERS))
    parser.add_argument("--misunderstanding", choices=sorted(MISUNDERSTANDINGS))
    parser.add_argument("--moral", choices=sorted(MORALS))
    parser.add_argument("--transformation", choices=sorted(TRANSFORMATIONS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HEROES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true", help="render every gate-valid combination")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true", help="list only gate-valid combinations from inline ASP")
    parser.add_argument("--verify", action="store_true", help="check ASP parity and exercise generated stories")
    parser.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if (args.chamber is None or combo[0] == args.chamber)
        and (args.misunderstanding is None or combo[1] == args.misunderstanding)
        and (args.moral is None or combo[2] == args.moral)
        and (args.transformation is None or combo[3] == args.transformation)
    ]
    if not combos:
        raise StoryError(
            describe_rejection(
                args.chamber or "pearl_chair",
                args.misunderstanding or "judgment_flame",
                args.moral or "truthfulness",
                args.transformation or "wax_lion_moth",
            )
        )

    chamber_key, misunderstanding_key, moral_key, transformation_key = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HEROES))
    hero = args.hero or rng.choice(HEROES[gender])
    return StoryParams(
        chamber=chamber_key,
        misunderstanding=misunderstanding_key,
        moral=moral_key,
        transformation=transformation_key,
        hero=hero,
        gender=gender,
        seed=(args.seed if args.seed is not None else 1000) + index,
    )


ASP_RULES = r"""
chamber(C) :- dental_chamber(C).
misunderstanding(M) :- mistake(M).
moral(V) :- moral_value(V).
transformation(T) :- change(T).

valid(C,M,V,T) :-
    chamber(C),
    misunderstanding(M),
    moral(V),
    transformation(T),
    chamber_allows(C,M),
    misunderstanding_allows(M,V),
    moral_turn(V,T).

#show valid/4.
"""


def asp_facts() -> str:
    from storyworlds import asp as aspmod

    rows: list[str] = []
    for chamber in CHAMBERS.values():
        rows.append(aspmod.fact("dental_chamber", chamber.key))
        rows.extend(aspmod.fact("chamber_allows", chamber.key, key) for key in chamber.allowed_misunderstandings)
    for misunderstanding in MISUNDERSTANDINGS.values():
        rows.append(aspmod.fact("mistake", misunderstanding.key))
        rows.extend(aspmod.fact("misunderstanding_allows", misunderstanding.key, key) for key in misunderstanding.allowed_morals)
    for moral in MORALS.values():
        rows.append(aspmod.fact("moral_value", moral.key))
        rows.append(aspmod.fact("moral_turn", moral.key, moral.transformation))
    for transformation in TRANSFORMATIONS.values():
        rows.append(aspmod.fact("change", transformation.key))
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    from storyworlds import asp as aspmod

    model = aspmod.one_model(asp_program("#show valid/4."))
    return sorted(set(aspmod.atoms(model, "valid")))


def verify_samples() -> list[str]:
    errors: list[str] = []
    for index, combo in enumerate(valid_combos(), start=1):
        gender = "girl" if index % 2 else "boy"
        hero = HEROES[gender][index % len(HEROES[gender])]
        sample = generate(StoryParams(*combo, hero=hero, gender=gender, seed=10_000 + index))
        story_lower = sample.story.lower()
        if "dentist office" not in story_lower:
            errors.append(f"story missing dentist office phrase for {combo}")
        if "candle" not in story_lower:
            errors.append(f"story missing candle for {combo}")
        if "vivid" not in story_lower:
            errors.append(f"story missing vivid for {combo}")
        if sample.story.count("\n\n") < 2:
            errors.append(f"story missing full three-part shape for {combo}")
        if sample.world is None or len(sample.world.events) < 5:
            errors.append(f"world state too thin for {combo}")
        if combo[3] not in sample.world.events[-1]:
            errors.append(f"transformation event not recorded for {combo}")
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            errors.append(f"missing prompts or QA for {combo}")
        for qa in list(sample.story_qa) + list(sample.world_qa):
            if len(qa.answer.split()) < 12 or "." not in qa.answer:
                errors.append(f"thin QA answer for {combo}: {qa.question!r}")
                break
        if any(token in sample.story for token in ["{", "}", "None", "meters", "memes"]):
            errors.append(f"debug/template leak in story for {combo}")
    return errors


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    status = 0
    if python_set == asp_set:
        print(f"OK: inline ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        status = 1
        print("MISMATCH between Python gate and inline ASP gate:")
        if python_set - asp_set:
            print("  only in Python:", sorted(python_set - asp_set))
        if asp_set - python_set:
            print("  only in ASP:", sorted(asp_set - python_set))

    sample_errors = verify_samples()
    if sample_errors:
        status = 1
        print("Sample verification failed:")
        for err in sample_errors:
            print(" ", err)
    else:
        print(f"OK: exercised {len(valid_combos())} generated stories with QA and required seed details.")
    return status


def _emit_variants(samples: list[StorySample], args: argparse.Namespace) -> None:
    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                "### "
                f"chamber={p.chamber} misunderstanding={p.misunderstanding} "
                f"moral={p.moral} transformation={p.transformation}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed or 7
    gender = args.gender or "girl"
    default_hero = args.hero or HEROES[gender][0]
    samples: list[StorySample] = []
    for index, combo in enumerate(valid_combos(), start=1):
        params = StoryParams(*combo, hero=default_hero, gender=gender, seed=base_seed + index)
        samples.append(generate(params))
    return samples


def main() -> int:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print("\t".join(combo))
        return 0

    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []

    try:
        if args.all:
            samples = _sample_all(args)
        else:
            seen: set[str] = set()
            attempts = 0
            while len(samples) < args.n and attempts < max(args.n * 60, 60):
                params = resolve_params(args, random.Random(base_seed + attempts), index=attempts)
                sample = generate(params)
                attempts += 1
                if sample.story in seen:
                    continue
                seen.add(sample.story)
                samples.append(sample)
            if len(samples) < args.n:
                raise StoryError("Could not generate enough unique stories with the current constraints.")

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        _emit_variants(samples, args)
        return 0
    except StoryError as err:
        print(err)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
