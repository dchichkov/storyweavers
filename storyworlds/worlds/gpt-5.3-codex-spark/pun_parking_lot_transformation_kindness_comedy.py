#!/usr/bin/env python3
"""A tiny parking-lot comedy world from a short source tale.

Seed story:
    Word: pun
    Setting: parking lot
    Features: Transformation, Kindness
    Style: Comedy

Source tale used for simulation:
    In a busy parking lot, a child meets a crooked sign that blocks a spot.
    The child refuses to take the short-cut and instead helps the lot helper.
    When kindness is shown, the sign transforms into a joking guide marker that
    reveals the best place to park, and the lot gets calmer right away.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


WORLD_FEATURES = ("Transformation", "Kindness", "Comedy")
PUN = "pun"


@dataclass(frozen=True)
class StoryParams:
    lot: str
    sign: str
    hero: str
    helper: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Lot:
    id: str
    name: str
    scene: str
    sign_ids: tuple[str, ...]
    helper_ids: tuple[str, ...]
    ending_image: str
    flavor: tuple[str, ...]


@dataclass(frozen=True)
class Sign:
    id: str
    label: str
    start_line: str
    transformed_line: str
    transformed_look: str
    transform_memes: tuple[str, ...]
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Hero:
    id: str
    name: str
    gender: str
    trait: str
    pronoun_subject: str
    pronoun_object: str
    pronoun_possessive: str


@dataclass(frozen=True)
class Helper:
    id: str
    name: str
    title: str
    tool: str
    tone: str


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    location: str = ""
    states: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "helper":
            return "they" if case == "subject" else ("them" if case == "object" else "their")
        if self.kind == "sign":
            return "it"
        return "it"


def readable_sign(label: str) -> str:
    return label.removeprefix("an ").removeprefix("a ")


@dataclass
class StoryWorld:
    params: StoryParams
    rng: random.Random
    lot: Lot
    sign_cfg: Sign
    hero_cfg: Hero
    helper_cfg: Helper
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    events: list[str] = field(default_factory=list)
    facts: dict[str, str | int | bool | float] = field(default_factory=dict)

    def add(self, ent: Entity) -> None:
        self.entities[ent.id] = ent

    def get(self, ent_id: str) -> Entity:
        return self.entities[ent_id]

    def say(self, text: str) -> None:
        text = text.strip()
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, event: str) -> None:
        self.events.append(event)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "StoryWorld":
        return copy.deepcopy(self)


def valid_combo(lot_id: str, sign_id: str, hero_id: str, helper_id: str) -> bool:
    if lot_id not in LOTS:
        return False
    if sign_id not in SIGNS:
        return False
    if hero_id not in HEROES:
        return False
    if helper_id not in HELPERS:
        return False
    lot = LOTS[lot_id]
    return sign_id in lot.sign_ids and helper_id in lot.helper_ids


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for lot_id in sorted(LOTS):
        lot = LOTS[lot_id]
        for sign_id in sorted(SIGNS):
            for hero_id in sorted(HEROES):
                for helper_id in sorted(HELPERS):
                    if valid_combo(lot_id, sign_id, hero_id, helper_id):
                        combos.append((lot_id, sign_id, hero_id, helper_id))
    return combos


def explain_rejection(lot_id: str, sign_id: str, hero_id: str, helper_id: str) -> str:
    if lot_id not in LOTS:
        return f"Unknown parking lot {lot_id!r}."
    if sign_id not in SIGNS:
        return f"Unknown sign type {sign_id!r}."
    if hero_id not in HEROES:
        return f"Unknown hero {hero_id!r}."
    if helper_id not in HELPERS:
        return f"Unknown helper {helper_id!r}."
    lot = LOTS[lot_id]
    if sign_id not in lot.sign_ids:
        return f"The lot '{lot.name}' cannot host the sign '{SIGNS[sign_id].label}'."
    if helper_id not in lot.helper_ids:
        return f"The helper '{HELPERS[helper_id].name}' does not work at '{lot.name}'."
    return "That parking-lot mix is not available in this world."


def create_world(params: StoryParams) -> StoryWorld:
    if not valid_combo(params.lot, params.sign, params.hero, params.helper):
        raise StoryError(explain_rejection(params.lot, params.sign, params.hero, params.helper))

    lot = LOTS[params.lot]
    sign_cfg = SIGNS[params.sign]
    hero_cfg = HEROES[params.hero]
    helper_cfg = HELPERS[params.helper]
    seed = params.seed if params.seed is not None else 0
    world = StoryWorld(
        params=params,
        rng=random.Random(seed),
        lot=lot,
        sign_cfg=sign_cfg,
        hero_cfg=hero_cfg,
        helper_cfg=helper_cfg,
    )

    hero = Entity(
        id="hero",
        label=hero_cfg.name,
        kind="child",
        location=lot.id,
    )
    helper = Entity(
        id="helper",
        label=helper_cfg.name,
        kind="helper",
        location=lot.id,
    )
    sign = Entity(
        id="sign",
        label=sign_cfg.label,
        kind="sign",
        location=lot.id,
        meters=defaultdict(float, {"bent": 1.0, "strength": 0.5, "helped": 0.0, "transformed": 0.0}),
        memes=defaultdict(float, {"embarrassed": 1.0}),
    )
    car = Entity(
        id="car",
        label="a little hatchback",
        kind="car",
        location=lot.id,
        meters=defaultdict(float, {"spot_needed": 1.0, "parked": 0.0}),
    )

    hero.states.add("arrived")
    hero.memes["hope"] = 1.0
    helper.memes["responsibility"] = 1.0
    world.add(hero)
    world.add(helper)
    world.add(sign)
    world.add(car)

    world.facts.update(
        lot_id=lot.id,
        sign_id=sign_cfg.id,
        hero_id=hero_cfg.id,
        helper_id=helper_cfg.id,
    )
    return world


def introduce(world: StoryWorld) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    sign = world.get("sign")
    lot = world.lot
    hero_cfg = world.hero_cfg
    helper_cfg = world.helper_cfg

    helper_name = world.get("helper").label
    flavor = world.rng.choice(lot.flavor)

    hero_label = hero_cfg.name
    world.say(
        f"Once upon a time, {hero_label} drove into {lot.name}, a busy parking lot with {flavor}."
    )
    world.say(
        f"{hero_label} needed a spot for the car, but {helper_name} the {helper_cfg.title} pointed at a crooked {readable_sign(sign.label)} that still said something like {sign_cfg_line(world)}."
    )
    world.say(
        f"{helper_name} said, 'This is a hard rule and a funny place at the same time. Want some help with it first?'"
    )
    world.record("introduced")


def sign_cfg_line(world: StoryWorld) -> str:
    return world.sign_cfg.start_line


def tension(world: StoryWorld) -> None:
    hero = world.get("hero")
    sign = world.get("sign")
    helper = world.get("helper")
    hero_cfg = world.hero_cfg
    helper_cfg = world.helper_cfg

    world.para()
    world.say(
        f"{hero_cfg.name} reached for the spot anyway and felt worried because the line on the sign was bent and hard to read."
    )
    world.say(
        f"The sign trembled, and everyone heard a faint rattle like a cartoon throat preparing a big joke."
    )
    sign.meters["bent"] = 1.0
    hero.memes["conflict"] = 1.0
    helper.memes["strain"] = 1.0
    world.record("tension")
    world.facts["tension"] = True


def kindness_turn(world: StoryWorld) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    sign = world.get("sign")
    car = world.get("car")
    lot = world.lot
    hero_cfg = world.hero_cfg
    helper_cfg = world.helper_cfg

    world.para()
    world.say(
        f"{hero_cfg.name} stopped worrying and chose to help {helper_cfg.name} before parking."
    )
    world.say(
        f"{hero_cfg.name} held the sign steady, lifted the wheel-chock out of the way, and steadied the line while {helper_cfg.name} reset it with {helper_cfg.tool}."
    )
    world.say(
        f'With a grin, {helper_cfg.name} said, "You can park when you smile first. Make me a {PUN}ny face and I will make you a kind place."'
    )
    hero.memes["kindness"] += 1.0
    helper.memes["grateful"] += 1.0
    sign.memes["trust"] += 1.0
    hero.meters["kindness"] += 1.0
    sign.meters["helped"] += 1.0
    sign.meters["strength"] += 1.0
    car.meters["parked"] = 0.0
    world.record("kindness_turn")
    if hero_cfg.trait:
        world.record(f"trait_{hero_cfg.trait}")

    if hero.meters["kindness"] > 0.5 and sign.meters["helped"] > 0.5:
        world.facts["kindness_gate"] = True
        transform_sign(world)
    else:
        world.facts["kindness_gate"] = False

    world.say(
        f"{hero_cfg.name} then asked the driver next to them, {helper_cfg.name} smiled and marked out a new line, making the lot look like it had room for everyone."
    )
    helper.name = helper.label  # keep helper string stable for trace readability
    world.facts["helper_name"] = helper_cfg.name
    world.facts["lot_name"] = lot.name


def transform_sign(world: StoryWorld) -> None:
    sign = world.get("sign")
    if sign.meters["transformed"] >= 1.0:
        return
    sign.meters["transformed"] = 1.0
    sign.states.add("transformed")
    base_sign_label = readable_sign(sign.label)
    if not base_sign_label.startswith("bent "):
        base_sign_label = f"bent {base_sign_label}"
    sign.label = base_sign_label
    sign.label = f"{sign.label} transformed into {world.sign_cfg.transformed_look}"
    sign.memes["joy"] = 1.0
    world.record("sign_transformed")


def finish_story(world: StoryWorld) -> None:
    hero = world.get("hero")
    sign = world.get("sign")
    helper = world.get("helper")
    car = world.get("car")
    lot = world.lot
    hero_cfg = world.hero_cfg
    helper_cfg = world.helper_cfg
    helper_name = helper.label

    world.para()
    if sign.meters.get("transformed", 0.0) >= 1.0:
        world.say(
        f"Then the sign gave one bright beep, snapped upright, and now read: "
        f"\"{world.sign_cfg.transformed_line}\"."
        )
        world.say(
            f"It seemed to wink whenever the word '{PUN}' appeared, as if the whole lot had learned a single new joke."
        )
    else:
        world.say("The sign stayed bent, but the helpers and {hero_cfg.name} found a safer lane anyway.")

    world.say(
        f"With a fresh space marked by the new sign, {hero_cfg.name} parked {car.label} neatly. "
        f"{helper_name} the {helper_cfg.title} thanked them and promised extra good luck for the next rainy day."
    )
    car.meters["parked"] = 1.0
    car.states.add("parked")
    helper.memes["pride"] += 1.0
    hero.memes["joy"] += 1.0
    world.record("parked")

    world.say(
        f"Image of the ending: {lot.ending_image}; "
        f"the once bent sign now looked like {sign.label}, and everyone at {lot.name} pointed and laughed."
    )

    world.facts.update(
        transformed=int(sign.meters.get("transformed", 0.0) >= 1.0),
        kindness_used=round(float(hero.memes["kindness"]), 2),
        sign_helped=sign.meters["helped"],
        park_success=car.meters["parked"] >= 1.0,
        helper_name=helper_name,
    )


def compose(world: StoryWorld) -> str:
    introduce(world)
    tension(world)
    kindness_turn(world)
    finish_story(world)
    return world.render()


def generation_prompts(world: StoryWorld) -> list[str]:
    lot = world.lot
    hero = world.hero_cfg
    sign = world.sign_cfg
    return [
        f"Write a kid-friendly parking-lot comedy featuring {hero.name}, who is {hero.trait}, and the word '{PUN}'.",
        f"Set the story in {lot.name}. {hero.name} should solve a parking problem by helping the lot helper, not by taking a shortcut.",
        f"Include a transformation where a bent sign changes after kindness and ends in a clear visual image.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    hero = world.hero_cfg
    helper = world.helper_cfg
    sign = world.sign_cfg
    transformed = bool(world.facts.get("transformed", False))
    return [
        QAItem(
            f"Who helped {hero.name} in the parking lot?",
            f"{hero.name} was helped by {helper.name}, who is the lot {helper.title}. "
            f"They worked together to fix the bent sign and calm the line."
        ),
        QAItem(
            "What changed at the center of the lot after kindness was shown?",
            f"The bent sign moved from being an obstacle to a friendly guide. "
            "After the helper and hero worked side by side, the sign was repaired and could be read clearly."
        ),
        QAItem(
            f"What happened because {hero.name} told a joke?",
            f"{hero.name} said a {PUN}ny line while helping, which made the helper relax and made the lot helpers coordinate better. "
            "That is what allowed the lot to open a clear space quickly."
        ),
        QAItem(
            "Was the story's ending concrete and visible?",
            (
                f"Yes. The ending image explicitly shows that the sign transformed and the car was parked: "
                f"{world.lot.ending_image}, plus the sign became {sign.transformed_look}."
                if transformed
                else "The ending image was not as clear because the sign did not transform."
            ),
        ),
        QAItem(
            f"How was kindness shown in this story?",
            f"{hero.name} chose to help first, held the line, and assisted the helper before looking for a spot. "
            "The world state records this as kindness used, then the sign could transform into a helpful marker."
        ),
    ]


def world_qa(world: StoryWorld) -> list[QAItem]:
    lot = world.lot
    sign = world.sign_cfg
    return [
        QAItem(
            "What happens in a parking lot story world like this one?",
            "A parking lot world has cars, people, and signs that control where vehicles can sit. "
            "Kind actions can change what is possible in the scene by changing the state of a sign or helper.",
        ),
        QAItem(
            "Why can the sign transform in this world?",
            f"The sign in this domain carries a hidden change state. When the helper and hero increase the "
            f"'helped' meter on the sign, it can convert from bent and confusing to a clearer guide marker.",
        ),
        QAItem(
            "What is meant by kindness in this simulation?",
            "Kindness is modeled as the hero helping the lot helper first, then sharing cooperative action instead "
            "of pushing forward with a selfish plan. That shifts world state toward resolution.",
        ),
        QAItem(
            "What is special about the ending image?",
            f"The image is not an abstract summary; it is an observed state: {lot.ending_image}, and the sign "
            f"finishes as \"{sign.transformed_line}\" in the transformed state."
            if world.facts.get("transformed", False)
            else "The lot still remains tense because the transformation gate failed to trigger.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story-grounded Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"params: {world.params}")
    lines.append(f"events: {len(world.events)}")
    for ev in world.events:
        lines.append(f" - {ev}")
    lines.append("entities:")
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        states = ", ".join(sorted(ent.states)) or "none"
        lines.append(
            f"  {ent.id:8} kind={ent.kind:7} "
            f"location={ent.location:12} states=[{states}]"
        )
        if meters:
            lines.append(f"    meters: {dict(meters)}")
        if memes:
            lines.append(f"    memes: {dict(memes)}")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = create_world(params)
    story = compose(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print()
        print(format_qa(sample))
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))


def emit_samples(samples: list[StorySample], trace: bool = False, qa: bool = False) -> None:
    for index, sample in enumerate(samples, start=1):
        if len(samples) > 1:
            print(f"=== pun_parking_lot_transformation_kindness_comedy #{index} seed={sample.params.seed} ===")
        emit(sample, trace=trace, qa=qa)
        if index != len(samples):
            print("\n" + "=" * 74 + "\n")


LOT = None


LOTS: dict[str, Lot] = {
    "harvest_mall": Lot(
        id="harvest_mall",
        name="Harvest Mall Parking Lot",
        scene="a sunlit, striped lot beside a grocery entrance",
        sign_ids=("bent_cone", "drift_arrow"),
        helper_ids=("attendant_ali", "attendant_jan"),
        ending_image="the cone stood at the front lane with a clean glow and a bright empty space beneath it",
        flavor=("one gentle breeze, one loud ice-cream truck, and a lot of people rushing",
                "fresh bread smell and a very patient line of cars"),
    ),
    "river_cinema": Lot(
        id="river_cinema",
        name="River Cinema Parking Lot",
        scene="a riverview lot where headlights looked like fireflies",
        sign_ids=("bent_cone", "bright_screen"),
        helper_ids=("attendant_ali", "security_ryan"),
        ending_image="a blue cone marker blinked and a new parking lane opened by the cinema entry",
        flavor=("a quiet lake breeze and a bus idling nearby",
                "a string of movie posters fluttering above the lot"),
    ),
    "lakeside_library": Lot(
        id="lakeside_library",
        name="Lakeside Library Lot",
        scene="a calm lot near a branch of the town library",
        sign_ids=("drift_arrow", "bright_screen"),
        helper_ids=("attendant_jan", "security_ryan"),
        ending_image="a calm path marker pointed to a freshly cleared spot beside the library ramp",
        flavor=("the smell of old paper and wet asphalt",
                "a row of bikes leaning near a reading pavilion"),
    ),
}


SIGNS: dict[str, Sign] = {
    "bent_cone": Sign(
        id="bent_cone",
        label="a bent blue traffic cone",
        start_line='"PARK" where the last letters fell off',
        transformed_line='PUN-STOP. PARK WITH KINDNESS.',
        transformed_look="an actor-cone with a painted smile",
        transform_memes=("hope", "humor"),
        tags=("traffic", "kindness"),
    ),
    "drift_arrow": Sign(
        id="drift_arrow",
        label="a tilted plastic arrow sign",
        start_line='"KEEP DRIFTING" with arrows all in the wrong places',
        transformed_line='PUN-LOADER: "You can PARK. Also, be kind."',
        transformed_look="a laughing arrow sign with a tiny paper hat",
        transform_memes=("clarity", "humor"),
        tags=("direction", "kindness"),
    ),
    "bright_screen": Sign(
        id="bright_screen",
        label="a quiet LED lot display",
        start_line='"NO PARKING" with half the letters flickering',
        transformed_line='PUN MODE: "A KIND SPOT FOR EVERY FRIEND."',
        transformed_look="a glowing lot display with changing smiley icons",
        transform_memes=("light", "humor"),
        tags=("digital", "kindness"),
    ),
}


HEROES: dict[str, Hero] = {
    "milo": Hero(
        id="milo",
        name="Milo",
        gender="boy",
        trait="curious",
        pronoun_subject="he",
        pronoun_object="him",
        pronoun_possessive="his",
    ),
    "zoe": Hero(
        id="zoe",
        name="Zoe",
        gender="girl",
        trait="bold",
        pronoun_subject="she",
        pronoun_object="her",
        pronoun_possessive="her",
    ),
    "ivy": Hero(
        id="ivy",
        name="Ivy",
        gender="girl",
        trait="kind",
        pronoun_subject="she",
        pronoun_object="her",
        pronoun_possessive="her",
    ),
}


HELPERS: dict[str, Helper] = {
    "attendant_ali": Helper(
        id="attendant_ali",
        name="Ali",
        title="attendant",
        tool="a reflective stick and a soft elbow",
        tone="warm",
    ),
    "attendant_jan": Helper(
        id="attendant_jan",
        name="Jan",
        title="attendant",
        tool="a bright glove and a calm smile",
        tone="cheerful",
    ),
    "security_ryan": Helper(
        id="security_ryan",
        name="Ryan",
        title="security guard",
        tool="a walkie-talkie and a spare cone stand",
        tone="steady",
    ),
}


CURATED: list[StoryParams] = [
    StoryParams("harvest_mall", "bent_cone", "milo", "attendant_ali", 101),
    StoryParams("river_cinema", "bright_screen", "zoe", "security_ryan", 102),
    StoryParams("lakeside_library", "drift_arrow", "ivy", "attendant_jan", 103),
    StoryParams("harvest_mall", "drift_arrow", "ivy", "attendant_jan", 104),
]


ASP_RULES = r"""
lot_helper(L, H) :- lot(L), helper(H), lot_allows_helper(L, H).
lot_sign(L, S) :- lot(L), sign(S), lot_allows_sign(L, S).

valid(L, S, Hero, Helper) :-
    lot(L),
    sign(S),
    hero(Hero),
    helper(Helper),
    lot_sign(L, S),
    lot_helper(L, Helper).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for lot_id, lot in LOTS.items():
        lines.append(asp.fact("lot", lot_id))
        for sign_id in lot.sign_ids:
            lines.append(asp.fact("lot_allows_sign", lot_id, sign_id))
        for helper_id in lot.helper_ids:
            lines.append(asp.fact("lot_allows_helper", lot_id, helper_id))
    for sign_id in SIGNS:
        lines.append(asp.fact("sign", sign_id))
    for hero_id in HEROES:
        lines.append(asp.fact("hero", hero_id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    combos: set[tuple[str, str, str, str]] = set()
    for model in asp.solve(asp_program("#show valid/4.")):
        for atom in asp.atoms(model, "valid"):
            combos.add(tuple(atom))  # type: ignore[misc]
    return sorted(combos)


def asp_verify() -> int:
    py = set(valid_combos())
    lp = set(asp_valid_combos())
    if py != lp:
        print("MISMATCH: ASP and Python valid combos differ.")
        if py - lp:
            print("  only Python:", sorted(py - lp))
        if lp - py:
            print("  only ASP:", sorted(lp - py))
        return 1

    for index, combo in enumerate(sorted(py), start=0):
        params = StoryParams(*combo, seed=1000 + index)
        generate(params)

    print(f"OK: ASP parity check passed for {len(py)} combos; generated {len(py)} stories.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lot", choices=sorted(LOTS))
    parser.add_argument("--sign", choices=sorted(SIGNS))
    parser.add_argument("--hero", choices=sorted(HEROES))
    parser.add_argument("--helper", choices=sorted(HELPERS))
    parser.add_argument("-n", type=int, default=1, help="number of stories")
    parser.add_argument("--seed", type=int, default=None, help="seed for reproducible samples")
    parser.add_argument("--all", action="store_true", help="render curated stories")
    parser.add_argument("--trace", action="store_true", help="show world-state trace")
    parser.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--asp", action="store_true", help="show valid ASP combos")
    parser.add_argument("--verify", action="store_true", help="compare ASP and python gates and regenerate samples")
    parser.add_argument("--show-asp", action="store_true", help="print full ASP program")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    if args.lot and args.sign and args.helper and not valid_combo(args.lot, args.sign, args.hero or sorted(HEROES)[0], args.helper):
        raise StoryError(explain_rejection(args.lot, args.sign, args.hero or sorted(HEROES)[0], args.helper))

    choices = [
        (lot_id, sign_id, hero_id, helper_id)
        for lot_id, sign_id, hero_id, helper_id in valid_combos()
        if (args.lot is None or lot_id == args.lot)
        and (args.sign is None or sign_id == args.sign)
        and (args.hero is None or hero_id == args.hero)
        and (args.helper is None or helper_id == args.helper)
    ]
    if not choices:
        lot = args.lot or sorted(LOTS)[0]
        sign = args.sign or sorted(SIGNS)[0]
        hero = args.hero or sorted(HEROES)[0]
        helper = args.helper or sorted(HELPERS)[0]
        raise StoryError(explain_rejection(lot, sign, hero, helper))

    lot_id, sign_id, hero_id, helper_id = rng.choice(choices)
    seed = args.seed if args.seed is not None else random.randrange(1_000_000)
    return StoryParams(lot_id, sign_id, hero_id, helper_id, seed=seed + index)


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        return [generate(p) for p in CURATED]

    samples: list[StorySample] = []
    seen: set[str] = set()
    attempts = 0
    i = 0
    target = max(1, args.n)
    base_seed = args.seed if args.seed is not None else random.randrange(1_000_000)
    while len(samples) < target and attempts < target * 80:
        seed = base_seed + i
        i += 1
        attempts += 1
        local = argparse.Namespace(**vars(args))
        local.seed = seed
        params = resolve_params(local, random.Random(seed), index=i)
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < target:
        raise StoryError("Could not generate enough unique parking-lot stories with the current filters.")
    return samples


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.show_asp:
        print(asp_program(""))
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print(" ".join(combo))
        return 0

    try:
        samples = build_samples(args)
    except StoryError as error:
        print(str(error))
        return 2

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return 0

    emit_samples(samples, trace=args.trace, qa=args.qa)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
