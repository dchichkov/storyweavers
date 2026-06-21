#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ratio_transformation_mystery.py
==========================================================

A tiny storyworld about a child solving a gentle mystery: a white plant left in
colored water changes overnight, and the child learns that the water-to-dye
ratio made the transformation visible.

This world keeps a small, reasoned domain:
- only absorbent white plants make a good transformation mystery
- only strong-enough dye ratios create a visible change worth narrating
- the story is driven by simulated state, not a frozen template

Run it
------
python storyworlds/worlds/gpt-5.4/ratio_transformation_mystery.py
python storyworlds/worlds/gpt-5.4/ratio_transformation_mystery.py --plant carnation --dye blue --ratio bold
python storyworlds/worlds/gpt-5.4/ratio_transformation_mystery.py --plant tulip
python storyworlds/worlds/gpt-5.4/ratio_transformation_mystery.py --all
python storyworlds/worlds/gpt-5.4/ratio_transformation_mystery.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/ratio_transformation_mystery.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher", "grandmother", "aunt"}
        male = {"boy", "father", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Plant:
    id: str
    label: str
    phrase: str
    part_word: str
    absorbent: bool = True
    whiteness: float = 1.0
    uptake: float = 1.0
    tags: set[str] = field(default_factory=set)


@dataclass
class Dye:
    id: str
    color: str
    bottle: str
    shimmer: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MixRatio:
    id: str
    text: str
    dye_parts: int
    water_parts: int
    strength: float
    tags: set[str] = field(default_factory=set)

    @property
    def phrase(self) -> str:
        return f"{self.dye_parts}-to-{self.water_parts} ratio"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def visible_change_score(plant: Plant, ratio: MixRatio) -> float:
    return plant.whiteness * plant.uptake * ratio.strength


def transformation_visible(plant: Plant, ratio: MixRatio) -> bool:
    return plant.absorbent and visible_change_score(plant, ratio) >= 0.9


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for plant_id, plant in PLANTS.items():
            for ratio_id, ratio in RATIOS.items():
                if transformation_visible(plant, ratio):
                    combos.append((setting_id, plant_id, ratio_id))
    return combos


def explain_rejection(plant: Plant, ratio: MixRatio) -> str:
    if not plant.absorbent:
        return (
            f"(No story: {plant.phrase} would stay much the same in colored water, "
            f"so there is no honest transformation mystery to solve.)"
        )
    return (
        f"(No story: the {ratio.phrase} is too weak to make {plant.phrase} change "
        f"enough to notice. Pick a stronger ratio for a visible transformation.)"
    )


def _r_drink(world: World) -> list[str]:
    plant = world.get("plant")
    cup = world.get("cup")
    if cup.meters["colored_water"] < THRESHOLD:
        return []
    sig = ("drink", plant.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ratio = world.facts["ratio_cfg"]
    plant_cfg = world.facts["plant_cfg"]
    plant.meters["soaked"] += plant_cfg.uptake
    plant.meters["tint"] += visible_change_score(plant_cfg, ratio)
    return []


def _r_show_color(world: World) -> list[str]:
    plant = world.get("plant")
    if plant.meters["tint"] < THRESHOLD:
        return []
    sig = ("show_color", plant.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["changed"] += 1
    hero = world.get("hero")
    hero.memes["wonder"] += 1
    hero.memes["worry"] += 1
    return []


RULES = [
    Rule(name="drink", tag="physical", apply=_r_drink),
    Rule(name="show_color", tag="physical", apply=_r_show_color),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        fired_count = len(world.fired)
        again = False
        for rule in RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) > before:
                again = True
        if again:
            changed = True
        if len(world.fired) == fired_count and not again:
            break
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_change(plant: Plant, ratio: MixRatio) -> dict:
    return {
        "visible": transformation_visible(plant, ratio),
        "score": visible_change_score(plant, ratio),
    }


def introduce(world: World, hero: Entity, helper: Entity, plant: Plant, dye: Dye) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"One quiet afternoon in {world.setting.place}, {hero.id} felt like a tiny detective."
    )
    world.say(
        f"{world.setting.detail} On the table stood {plant.phrase} beside {dye.bottle}, "
        f"and that was enough to make the room feel full of secrets."
    )
    world.say(
        f'{helper.label_word.capitalize()} smiled and said, "Would you like to help me with a little color test?"'
    )


def mix(world: World, hero: Entity, helper: Entity, dye: Dye, ratio: MixRatio) -> None:
    cup = world.get("cup")
    cup.meters["water"] += ratio.water_parts
    cup.meters["dye"] += ratio.dye_parts
    cup.meters["colored_water"] += 1
    hero.memes["focus"] += 1
    world.say(
        f"Together they counted the drops carefully: {ratio.text}. "
        f'"That is a {ratio.phrase}," {helper.label_word} said, tapping the spoon gently.'
    )
    world.say(
        f"Soon the water {dye.shimmer}, and {hero.id} could not look away."
    )


def place_plant(world: World, hero: Entity, plant: Plant) -> None:
    world.get("plant").meters["standing"] += 1
    world.say(
        f"{hero.id} set the {plant.label} into the cup and watched its {plant.part_word} disappear into the color."
    )
    world.say("Nothing else happened right then, which made the waiting feel even more mysterious.")


def pass_time(world: World, hero: Entity) -> None:
    hero.memes["anticipation"] += 1
    world.say(
        "They left it by the window while the afternoon grew softer and the shadows slid across the floor."
    )


def discover(world: World, hero: Entity, plant: Plant, dye: Dye) -> None:
    plant_ent = world.get("plant")
    hero.memes["wonder"] += 1
    if plant_ent.meters["changed"] >= THRESHOLD:
        world.say(
            f"When {hero.id} came back, the {plant.label} was no longer plain white. "
            f"Faint {dye.color} had climbed into the {plant.part_word}, as if the plant had learned a new secret."
        )
        world.say(
            f'{hero.id} whispered, "That was white before. Who colored it?"'
        )
    else:
        world.say(
            f"When {hero.id} came back, the {plant.label} still looked almost the same."
        )


def inspect(world: World, hero: Entity, helper: Entity, plant: Plant, dye: Dye) -> None:
    hero.memes["reasoning"] += 1
    world.say(
        f"{hero.id} looked for clues: the lower water line, the stained spoon, and the pale stem drinking from the cup."
    )
    world.say(
        f'"A mystery likes clues," said {helper.label_word}, "so let us ask what changed first."'
    )


def solve(world: World, hero: Entity, helper: Entity, plant: Plant, ratio: MixRatio, dye: Dye) -> None:
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    world.facts["solved"] = True
    world.say(
        f"{hero.id}'s eyes grew round. It was not a sneaky painter after all. "
        f"The {plant.label} had pulled the colored water upward by itself."
    )
    world.say(
        f'"So the {ratio.phrase} mattered," {hero.id} said. '
        f'"Yes," said {helper.label_word}. "There was enough color in the water for the change to show."'
    )
    world.say(
        f"To prove it, they set a second white stem beside the first and watched the same {dye.color} trail begin again."
    )


def ending(world: World, hero: Entity, helper: Entity, plant: Plant, dye: Dye, ratio: MixRatio) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"By evening, {world.setting.ending_image} The mystery was gone, but the wonder stayed."
    )
    world.say(
        f"{hero.id} wrote a small note for the cup: {ratio.phrase}, {dye.color} dye, one brave {plant.label}."
    )


def tell(
    setting: Setting,
    plant: Plant,
    dye: Dye,
    ratio: MixRatio,
    hero_name: str = "Mia",
    hero_type: str = "girl",
    helper_type: str = "grandmother",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper"))
    cup = world.add(Entity(id="cup", type="cup", label="glass cup"))
    plant_ent = world.add(Entity(id="plant", type="plant", label=plant.label, phrase=plant.phrase))
    world.facts.update(setting=setting, plant_cfg=plant, dye_cfg=dye, ratio_cfg=ratio, hero=hero, helper=helper)

    introduce(world, hero, helper, plant, dye)
    mix(world, hero, helper, dye, ratio)
    place_plant(world, hero, plant)

    world.para()
    pass_time(world, hero)
    propagate(world, narrate=False)
    discover(world, hero, plant, dye)

    world.para()
    inspect(world, hero, helper, plant, dye)
    solve(world, hero, helper, plant, ratio, dye)
    ending(world, hero, helper, plant, dye, ratio)

    world.facts.update(
        cup=cup,
        plant=plant_ent,
        changed=plant_ent.meters["changed"] >= THRESHOLD,
        visible_score=visible_change_score(plant, ratio),
        solved=world.facts.get("solved", False),
    )
    return world


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen",
        detail="The window made a bright square on the table.",
        ending_image="two colored flowers glowed on the sill like tiny lanterns",
        tags={"home"},
    ),
    "classroom": Setting(
        id="classroom",
        place="the classroom",
        detail="Sunlight rested on the science shelf near a stack of paper and crayons.",
        ending_image="the cup sat beside a row of notebooks, and every child wanted a closer look",
        tags={"school"},
    ),
    "greenhouse": Setting(
        id="greenhouse",
        place="the little greenhouse",
        detail="Warm glass walls held the smell of leaves and damp soil.",
        ending_image="the colored petals shone among the green leaves like a clue that had turned into a jewel",
        tags={"garden"},
    ),
}

PLANTS = {
    "carnation": Plant(
        id="carnation",
        label="carnation",
        phrase="a white carnation",
        part_word="petals",
        absorbent=True,
        whiteness=1.0,
        uptake=1.0,
        tags={"flower", "plants"},
    ),
    "daisy": Plant(
        id="daisy",
        label="daisy",
        phrase="a white daisy",
        part_word="petals",
        absorbent=True,
        whiteness=0.95,
        uptake=0.95,
        tags={"flower", "plants"},
    ),
    "celery": Plant(
        id="celery",
        label="celery stalk",
        phrase="a pale celery stalk with leaves",
        part_word="leaves",
        absorbent=True,
        whiteness=0.9,
        uptake=1.1,
        tags={"plants", "celery"},
    ),
    "tulip": Plant(
        id="tulip",
        label="tulip",
        phrase="a yellow tulip",
        part_word="petals",
        absorbent=False,
        whiteness=0.2,
        uptake=0.4,
        tags={"flower"},
    ),
}

DYES = {
    "blue": Dye(
        id="blue",
        color="blue",
        bottle="a little bottle of blue food coloring",
        shimmer="turned blue as a robin's egg",
        tags={"blue", "dye"},
    ),
    "red": Dye(
        id="red",
        color="red",
        bottle="a little bottle of red food coloring",
        shimmer="turned red like berry juice",
        tags={"red", "dye"},
    ),
    "purple": Dye(
        id="purple",
        color="purple",
        bottle="a little bottle of purple food coloring",
        shimmer="turned purple like twilight",
        tags={"purple", "dye"},
    ),
}

RATIOS = {
    "bold": MixRatio(
        id="bold",
        text="one part dye to four parts water",
        dye_parts=1,
        water_parts=4,
        strength=1.2,
        tags={"ratio", "mixing"},
    ),
    "balanced": MixRatio(
        id="balanced",
        text="one part dye to six parts water",
        dye_parts=1,
        water_parts=6,
        strength=1.0,
        tags={"ratio", "mixing"},
    ),
    "faint": MixRatio(
        id="faint",
        text="one part dye to twelve parts water",
        dye_parts=1,
        water_parts=12,
        strength=0.45,
        tags={"ratio", "mixing"},
    ),
}

HELPERS = ["mother", "father", "grandmother", "grandfather", "teacher"]
GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Lucy"]
BOY_NAMES = ["Ben", "Leo", "Max", "Noah", "Theo", "Eli", "Sam"]
TRAITS = ["careful", "curious", "quiet", "patient"]


@dataclass
class StoryParams:
    setting: str
    plant: str
    dye: str
    ratio: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="kitchen",
        plant="carnation",
        dye="blue",
        ratio="balanced",
        name="Mia",
        gender="girl",
        helper="grandmother",
    ),
    StoryParams(
        setting="classroom",
        plant="daisy",
        dye="red",
        ratio="bold",
        name="Ben",
        gender="boy",
        helper="teacher",
    ),
    StoryParams(
        setting="greenhouse",
        plant="celery",
        dye="purple",
        ratio="balanced",
        name="Nora",
        gender="girl",
        helper="grandfather",
    ),
]


KNOWLEDGE = {
    "ratio": [
        (
            "What is a ratio?",
            "A ratio tells how much of one thing there is compared with another thing. In mixing, it helps you keep the amounts in the right balance.",
        )
    ],
    "dye": [
        (
            "What is food coloring?",
            "Food coloring is a strong liquid color. Just a few drops can tint water or batter.",
        )
    ],
    "plants": [
        (
            "How can a plant drink water?",
            "A plant pulls water up through tiny tubes in its stem. That water can travel all the way to leaves or petals.",
        )
    ],
    "flower": [
        (
            "Why can white petals change color in dyed water?",
            "White petals show new color easily. When the stem drinks dyed water, the color can spread into the petals.",
        )
    ],
    "celery": [
        (
            "Why do celery leaves change in colored water?",
            "Celery has little tubes inside its stalk. When it drinks colored water, the dye can move up into the leaves.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    plant = world.facts["plant_cfg"]
    dye = world.facts["dye_cfg"]
    ratio = world.facts["ratio_cfg"]
    helper = world.facts["helper"]
    return [
        f'Write a gentle mystery story for a 3-to-5-year-old that includes the word "ratio" and a visible transformation.',
        f"Tell a story where {hero.id} notices that {plant.phrase} has changed color and solves the mystery by thinking about the {ratio.phrase}.",
        f"Write a child-facing mystery in which {helper.label_word} helps a child discover why {dye.color} water changed a plant.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    plant = world.facts["plant_cfg"]
    dye = world.facts["dye_cfg"]
    ratio = world.facts["ratio_cfg"]
    changed = world.facts["changed"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who felt like a little detective, and {helper.label_word}, who helped with the color test.",
        ),
        (
            "What made the room feel mysterious at the start?",
            f"{plant.phrase} was standing beside {dye.bottle}, and they mixed colored water very carefully. That quiet setup made {hero.id} feel as if a secret might be hiding in plain sight.",
        ),
        (
            "What ratio did they use?",
            f"They used {ratio.text}. {helper.label_word.capitalize()} even called it a {ratio.phrase} so {hero.id} would remember the careful balance.",
        ),
    ]
    if changed:
        qa.append(
            (
                f"What changed about the {plant.label}?",
                f"It stopped looking plain white and began to show {dye.color} in the {plant.part_word}. The change happened because the plant drank the colored water through its stem.",
            )
        )
    qa.append(
        (
            "How was the mystery solved?",
            f"{hero.id} looked at clues like the lower water line and the stained stem, then realized nobody had painted the plant by hand. The plant had changed itself by drinking the dyed water, and the strong-enough ratio made the color easy to see.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the mystery solved and the experiment repeated to prove it. The ending image shows color shining on the window sill, so the change feels real and gentle instead of scary.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ratio", "dye", "plants"}
    plant = world.facts["plant_cfg"]
    if "flower" in plant.tags:
        tags.add("flower")
    if "celery" in plant.tags:
        tags.add("celery")
    order = ["ratio", "dye", "plants", "flower", "celery"]
    out: list[tuple[str, str]] = []
    for tag in order:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
visible_score(P, R, S) :- whiteness(P, W), uptake(P, U), strength(R, T), S = W * U * T.
visible(P, R) :- absorbent(P), visible_score(P, R, S), S >= 0.9.
valid(Setting, P, R) :- setting(Setting), plant(P), ratio(R), visible(P, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for plant_id, plant in PLANTS.items():
        lines.append(asp.fact("plant", plant_id))
        if plant.absorbent:
            lines.append(asp.fact("absorbent", plant_id))
        lines.append(asp.fact("whiteness", plant_id, plant.whiteness))
        lines.append(asp.fact("uptake", plant_id, plant.uptake))
    for ratio_id, ratio in RATIOS.items():
        lines.append(asp.fact("ratio", ratio_id))
        lines.append(asp.fact("strength", ratio_id, ratio.strength))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
    try:
        _smoke_test()
        print("OK: smoke test story generation passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    for params in CURATED:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
        except Exception as err:
            rc = 1
            print(f"CURATED GENERATION FAILED for {params}: {err}")
    if rc == 0:
        print(f"OK: curated generation passed ({len(CURATED)} stories).")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child solves a color-change mystery with a ratio."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--dye", choices=DYES)
    ap.add_argument("--ratio", choices=RATIOS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plant and args.ratio:
        plant = PLANTS[args.plant]
        ratio = RATIOS[args.ratio]
        if not transformation_visible(plant, ratio):
            raise StoryError(explain_rejection(plant, ratio))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.plant is None or combo[1] == args.plant)
        and (args.ratio is None or combo[2] == args.ratio)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, plant_id, ratio_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    helper = args.helper or rng.choice(HELPERS)
    dye = args.dye or rng.choice(sorted(DYES))
    return StoryParams(
        setting=setting_id,
        plant=plant_id,
        dye=dye,
        ratio=ratio_id,
        name=name,
        gender=gender,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.plant not in PLANTS:
        raise StoryError(f"(Unknown plant: {params.plant})")
    if params.dye not in DYES:
        raise StoryError(f"(Unknown dye: {params.dye})")
    if params.ratio not in RATIOS:
        raise StoryError(f"(Unknown ratio: {params.ratio})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    plant = PLANTS[params.plant]
    ratio = RATIOS[params.ratio]
    if not transformation_visible(plant, ratio):
        raise StoryError(explain_rejection(plant, ratio))

    world = tell(
        setting=SETTINGS[params.setting],
        plant=plant,
        dye=DYES[params.dye],
        ratio=ratio,
        hero_name=params.name,
        hero_type=params.gender,
        helper_type=params.helper,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, plant, ratio) combos:\n")
        for setting_id, plant_id, ratio_id in combos:
            print(f"  {setting_id:10} {plant_id:10} {ratio_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.plant} in {p.setting} ({p.dye}, {p.ratio})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
