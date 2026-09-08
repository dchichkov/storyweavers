#!/usr/bin/env python3
"""
A small fable about an ambidextrous baker, gluten, repetition, and curiosity.

Seed tale:
---
Luna was an ambidextrous little baker who could stir with either hand.
She made a gluten-free loaf for the village fox, but the loaf stayed flat.
She added more flour, then more yeast, then more flour again. Each attempt
looked different, yet the loaf still sank.
Curious Luna stopped repeating guesses. She watched the dough and found that
a cold stone shelf was keeping it from rising.
She moved the bowl beside the warm oven, covered it with a cloth, and waited.
The loaf rose high, and Luna learned that a curious question can be better
than a hurried answer.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class StoryParams:
    name: str = "Luna"
    scenario: str = "loaf"
    place: str = "village_bakery"
    beat: int = 0
    refrain: int = 0
    question: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Beat:
    guest: str
    food: str
    need: str
    trouble: str
    danger: str
    attempts: tuple[str, str, str]
    setbacks: tuple[str, str, str]
    clue: str
    cause: str
    fix: str
    resolution: str
    endings: tuple[str, str, str, str]


@dataclass(frozen=True)
class Scenario:
    id: str
    action: str
    beats: tuple[Beat, ...]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "village_bakery": Setting(
        "the village bakery",
        "a blue oven, a floury counter, and a window where sparrows watched",
    ),
    "river_market": Setting(
        "the riverside market",
        "striped awnings, a warm copper oven, and boats sliding past",
    ),
    "hill_kitchen": Setting(
        "the hilltop kitchen",
        "round windows, a broad hearth, and baskets of apples",
    ),
}

SCENARIOS = {
    "loaf": Scenario(
        "loaf",
        "bake a gluten-free loaf",
        (
            Beat(
                guest="Pip the fox",
                food="a small gluten-free loaf",
                need="Pip the fox needed a warm gluten-free loaf for his family supper",
                trouble="the dough stayed flat whenever Luna tried to bake it",
                danger="the family might have no soft bread for supper",
                attempts=(
                    "add another spoonful of gluten-free flour",
                    "stir in a little more yeast with her right hand",
                    "stir the dough again with her left hand",
                ),
                setbacks=(
                    "the dough grew thick but did not rise",
                    "the yeast made tiny bubbles, then went quiet",
                    "the bowl remained as flat as a pond",
                ),
                clue="the dough felt cold whenever she touched the bowl",
                cause="the stone shelf was too cold for the yeast to wake",
                fix="move the bowl beside the warm oven, cover it with a cloth, and wait",
                resolution="the dough rose high, and the gluten-free loaf baked soft and golden",
                endings=(
                    "Pip carried the warm loaf home beneath a red napkin.",
                    "The loaf stood proudly on the counter while sparrows chirped outside.",
                    "Luna sliced the bread, and its soft middle sent a sweet smell through the bakery.",
                    "Pip shared the first piece with Luna beneath the glowing oven light.",
                ),
            ),
            Beat(
                guest="Mara the mouse",
                food="a gluten-free oat cake",
                need="Mara the mouse needed a gluten-free oat cake for the village picnic",
                trouble="the little cake sank each time Luna took it from the oven",
                danger="the picnic basket could be left without a treat",
                attempts=(
                    "beat the batter with her left hand",
                    "beat it again with her right hand",
                    "add a second pinch of baking powder",
                ),
                setbacks=(
                    "the top puffed and then dropped",
                    "the second beating made the batter even thinner",
                    "the cake sank before its edges turned brown",
                ),
                clue="a silver spoon trembled on the same cold shelf",
                cause="the shelf was far from the oven's warm air",
                fix="place the tin on the warm rack and shield it from the chilly draft",
                resolution="the oat cake rose evenly and baked firm enough for the picnic",
                endings=(
                    "Mara placed the cake beside the picnic blanket, where everyone cheered.",
                    "The golden cake cooled under a checked cloth while bees hummed nearby.",
                    "Children shared the gluten-free cake and saved Luna the largest crumb.",
                    "Mara's tiny plate came home empty except for one shining oat.",
                ),
            ),
            Beat(
                guest="Toma the tortoise",
                food="a gluten-free herb roll",
                need="Toma the tortoise needed a gluten-free herb roll for his long walk",
                trouble="the roll spread wide instead of rising tall",
                danger="it might crumble before Toma reached the far meadow",
                attempts=(
                    "shape the dough with both hands",
                    "turn the bowl around and shape it again",
                    "add more herbs and fold the dough twice",
                ),
                setbacks=(
                    "the roll slid sideways on the tray",
                    "its sides sagged when Luna lifted her hands",
                    "the herbs smelled lovely, but the dough stayed low",
                ),
                clue="the cloth covering the bowl felt damp and chilly",
                cause="the bowl was resting beside an open window",
                fix="close the window, move the bowl near the hearth, and cover it with a dry cloth",
                resolution="the roll rose into a sturdy spiral with herbs shining on top",
                endings=(
                    "Toma tucked the spiral roll into his pack and began his walk.",
                    "The herb roll traveled safely to the meadow in a little leaf basket.",
                    "Luna drew a spiral in flour while Toma nibbled the crisp edge.",
                    "At sunset, Toma waved from the meadow with the golden roll beside him.",
                ),
            ),
        ),
    ),
    "muffin": Scenario(
        "muffin",
        "bake a gluten-free berry muffin",
        (
            Beat(
                guest="Nell the squirrel",
                food="a gluten-free berry muffin",
                need="Nell the squirrel needed a gluten-free berry muffin for her brother",
                trouble="the muffin stayed small after every bake",
                danger="her brother might miss his birthday treat",
                attempts=(
                    "fold the berries with her left hand",
                    "fold the batter with her right hand",
                    "fill the cup nearly to its rim",
                ),
                setbacks=(
                    "the berries sank to the bottom",
                    "the batter became smooth but stayed low",
                    "the full cup spilled without rising",
                ),
                clue="the baking cup was sitting on a cool metal tray",
                cause="the cool tray stole heat before the muffin could rise",
                fix="warm the tray first and place the cup in the center of the oven",
                resolution="the berry muffin rose around its bright berries",
                endings=(
                    "Nell carried the muffin home with both paws around the warm cup.",
                    "Her brother blew out one candle set in the tall golden muffin.",
                    "Berry juice shone on the muffin top like tiny red windows.",
                    "Luna watched Nell share the muffin beneath the bakery awning.",
                ),
            ),
        ),
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A fable about Luna, gluten-free baking, repetition, and curiosity.")
    parser.add_argument("--name", choices=["Luna", "Luna the Baker"], default="Luna")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default=None)
    parser.add_argument("--place", choices=sorted(SETTINGS), default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scenario = args.scenario or rng.choice(sorted(SCENARIOS))
    place = args.place or rng.choice(sorted(SETTINGS))
    return StoryParams(
        name=args.name,
        scenario=scenario,
        place=place,
        beat=rng.randrange(len(SCENARIOS[scenario].beats)),
        refrain=rng.randrange(5),
        question=rng.randrange(5),
        ending=rng.randrange(4),
        seed=args.seed,
    )


def reasonableness_gate(params: StoryParams, scenario: Scenario) -> None:
    if not params.name.strip():
        raise StoryError("A baker name is required.")
    if params.name not in {"Luna", "Luna the Baker"}:
        raise StoryError("This fable belongs to Luna, the ambidextrous baker.")
    if params.scenario not in SCENARIOS:
        raise StoryError("Unknown baking scenario.")
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if not 0 <= params.beat < len(scenario.beats):
        raise StoryError("Unknown story beat.")
    if not 0 <= params.refrain < 5 or not 0 <= params.question < 5:
        raise StoryError("Unknown repetition or curiosity style.")
    if not 0 <= params.ending < 4:
        raise StoryError("Unknown ending style.")


ASP_RULES = r"""
baker(luna).
skill(ambidextrous).
ingredient(gluten_free).
feature(repetition).
feature(curiosity).
form(fable).

valid_world :- baker(luna), skill(ambidextrous), ingredient(gluten_free),
               feature(repetition), feature(curiosity), form(fable).

#show valid_world/0.
#show skill/1.
#show ingredient/1.
#show feature/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("baker", "luna"),
            asp.fact("skill", "ambidextrous"),
            asp.fact("ingredient", "gluten_free"),
            asp.fact("feature", "repetition"),
            asp.fact("feature", "curiosity"),
            asp.fact("form", "fable"),
        ]
    )


def asp_program(show: str = "#show valid_world/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    valid = set(asp.atoms(model, "valid_world"))
    expected = {()}
    if valid == expected:
        print("OK: ASP facts and fable gate agree.")
        return 0
    print("MISMATCH")
    print("clingo:", sorted(valid))
    print("python:", sorted(expected))
    return 1


def build_world(params: StoryParams, scenario: Scenario, setting: Setting) -> World:
    beat = scenario.beats[params.beat]
    world = World(setting)
    luna = world.add(Entity("baker", "character", params.name, "baker"))
    guest = world.add(Entity("guest", "character", beat.guest, "animal"))
    dough = world.add(Entity("dough", "thing", beat.food, "gluten_free_food"))
    place = world.add(Entity("place", "place", setting.place, "setting"))

    luna.memes.update(
        patience=0.0,
        curiosity=0.0,
        confidence=0.0,
        relief=0.0,
        joy=0.0,
        repetition=0.0,
    )
    dough.meters.update(rise=0.1, warmth=0.2, safety=0.7, gluten_free=1.0)
    place.meters.update(cold=0.0, warmth=0.5, danger=0.0, repair=0.0)

    openings = (
        f"{params.name} could stir with either hand, so she mixed dough with her left hand one moment and her right hand the next.",
        f"{params.name} was ambidextrous: her left hand kneaded while her right hand reached for a spoon.",
        f"In the bakery, {params.name} practiced being ambidextrous by folding dough smoothly with either hand.",
        f"{params.name} used both hands with equal care, for an ambidextrous baker wastes neither hand nor crumb.",
        f"Everyone knew {params.name} was ambidextrous, but she knew that good baking needed more than clever hands.",
    )
    world.say(f"{params.name} was a small, ambidextrous baker in {setting.place}.")
    world.say(openings[params.question % len(openings)])
    world.say(f"There were {setting.detail}.")
    world.para()

    world.say(f"One morning, {beat.need}.")
    world.say(f"Luna prepared {beat.food}, carefully keeping it free from gluten.")
    world.say(f"But {beat.trouble}. If nothing changed, {beat.danger}.")
    luna.memes["concern"] = 1.0

    refrains = (
        "Perhaps one more careful try",
        "Again, but gently",
        "Left hand, right hand, and try once more",
        "I will change the mixture",
        "The answer must be in the dough",
    )
    for number, (attempt, setback) in enumerate(zip(beat.attempts, beat.setbacks), 1):
        luna.memes["repetition"] += 1.0
        world.say(f'"{refrains[params.refrain]}," {params.name} said.')
        world.say(f"On try {number}, she tried to {attempt}, but {setback}.")
    world.para()

    questions = (
        f'"What stays the same?" {params.name} asked.',
        f'"Could the bowl be telling me something?" {params.name} wondered aloud.',
        f'"Where does the trouble begin?" {params.name} asked {beat.guest}.',
        f'"What if I watch instead of guessing?" {params.name} said.',
        f'"Is the recipe wrong, or is the place wrong?" {params.name} asked.',
    )
    world.say(questions[params.question])
    world.say(f"{beat.guest} leaned close and replied, 'The dough feels cold.'")
    world.say(f"Curious Luna watched instead of guessing. She noticed {beat.clue}.")
    luna.memes["curiosity"] = 1.0
    world.say(f"Then the cause became clear: {beat.cause}.")
    world.say(f"She used both hands to {beat.fix}.")
    dough.meters["rise"] = 1.0
    dough.meters["warmth"] = 1.0
    place.meters["cold"] = 0.0
    place.meters["warmth"] = 1.0
    place.meters["repair"] = 1.0
    luna.memes["relief"] = 1.0
    luna.memes["joy"] = 1.0
    world.para()

    world.say(f"At last, {beat.resolution}.")
    world.say(f'{beat.guest} smiled and said, "Your curious question found what repeating guesses could not."')
    world.say(beat.endings[params.ending])
    world.say(f"{params.name} cleaned the counter, keeping the lesson close: a patient question can help both hands choose the right work.")

    world.facts.update(
        baker=luna,
        guest=guest,
        dough=dough,
        place=place,
        setting=setting,
        scenario=scenario,
        beat=beat,
        refrain=refrains[params.refrain],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    beat: Beat = world.facts["beat"]
    return [
        f"Write a child-friendly fable about an ambidextrous baker named {world.facts['baker'].label}.",
        f"Tell a story in which repetition fails until curiosity discovers why {beat.food} will not rise.",
        "Use a gluten-free baking problem, a brief dialogue, and a gentle moral about asking questions.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    beat: Beat = facts["beat"]
    baker: Entity = facts["baker"]
    return [
        QAItem(
            "Who was Luna?",
            f"{baker.label} was an ambidextrous little baker who could work with either hand.",
        ),
        QAItem(
            "What problem happened to the gluten-free food?",
            f"{beat.trouble.capitalize()}. Luna feared that {beat.danger}.",
        ),
        QAItem(
            "What did Luna repeat?",
            f"She tried three different changes: to {beat.attempts[0]}, to {beat.attempts[1]}, and to {beat.attempts[2]}. Each attempt ended with a similar setback.",
        ),
        QAItem(
            "How did curiosity help Luna?",
            f"She stopped guessing and watched carefully. She noticed {beat.clue}, which showed that {beat.cause}.",
        ),
        QAItem(
            "How did the fable end?",
            f"Luna fixed the cause by {beat.fix}. Then {beat.resolution}, and her guest thanked her for asking a curious question.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does ambidextrous mean?",
            "Ambidextrous means being able to use either hand well.",
        ),
        QAItem(
            "What is gluten-free food?",
            "Gluten-free food is made without gluten, a protein found in grains such as wheat, barley, and rye.",
        ),
        QAItem(
            "Why is curiosity useful?",
            "Curiosity encourages someone to observe, ask questions, and discover the real cause of a problem.",
        ),
        QAItem(
            "What is repetition in a fable?",
            "Repetition is when an action or idea happens more than once so the reader can notice a pattern.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        parts = []
        if entity.meters:
            parts.append(f"meters={entity.meters}")
        if entity.memes:
            parts.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id} ({entity.type}) {' '.join(parts)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    scenario = SCENARIOS.get(params.scenario)
    if scenario is None:
        raise StoryError("Unknown baking scenario.")
    reasonableness_gate(params, scenario)
    world = build_world(params, scenario, SETTINGS[params.place])
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
        print(asp.atoms(model, "valid_world"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        index = 0
        for scenario_id, scenario in SCENARIOS.items():
            for place_id in SETTINGS:
                rng = random.Random(base_seed + index)
                params = StoryParams(
                    name="Luna",
                    scenario=scenario_id,
                    place=place_id,
                    beat=rng.randrange(len(scenario.beats)),
                    refrain=rng.randrange(5),
                    question=rng.randrange(5),
                    ending=rng.randrange(4),
                    seed=base_seed + index,
                )
                samples.append(generate(params))
                index += 1
    else:
        for index in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
