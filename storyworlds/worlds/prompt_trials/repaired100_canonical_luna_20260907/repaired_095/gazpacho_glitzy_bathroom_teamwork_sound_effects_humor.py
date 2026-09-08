#!/usr/bin/env python3
"""A tiny mythic bathroom world about gazpacho, glitz, teamwork, and comic sounds."""

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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    label: str


@dataclass
class Incident:
    id: str
    omen: str
    problem: str
    clue: str
    plan: str
    sound: str
    resolution: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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
    "bathroom": Setting("bathroom", "the tiled bathroom"),
}

INCIDENTS = {
    "bowl_overflow": Incident(
        "bowl_overflow",
        "At moonrise, the silver bathroom mirror flashed three times.",
        "A glitzy bowl of gazpacho had begun to wobble on the marble sink, and one sneeze might send cold soup across the floor.",
        "A red pepper seed was wedged beneath the bowl's foot, making it rock.",
        "They lifted the bowl together, slid a folded towel beneath it, and cleared the seed with a cotton swab.",
        "Plop! Squee! Ta-da!",
        "The bowl settled safely, while the soup's bright surface shone like a little red moon.",
        "The towel remained under the bowl like a brave white shield.",
    ),
    "mirror_mist": Incident(
        "mirror_mist",
        "The bathroom mirror clouded over and showed a golden crown instead of a face.",
        "The glitzy crown was only a reflection from a misplaced party lamp, but the fog hid the shelf holding the gazpacho.",
        "A warm shower had filled the room with mist, and a loose fan cord lay behind the hamper.",
        "They opened the window, moved the hamper, and plugged in the fan while taking turns calling out each safe step.",
        "Whirr! Puff! Ding!",
        "The mist faded, the shelf appeared, and the gazpacho waited untouched beneath the crown-shaped reflection.",
        "The mirror finally showed two laughing helpers wearing imaginary crowns.",
    ),
    "royal_splash": Incident(
        "royal_splash",
        "A tiny bathroom drain began singing like a trumpet beneath the tiles.",
        "Each note made the glitzy soup spoon jump toward a basin of gazpacho.",
        "The spoon's handle was tapping the faucet whenever the drain bubbled.",
        "One helper held the spoon, another steadied the basin, and the third turned the faucet until the rhythm stopped.",
        "Bloop! Bonk! Hahaha!",
        "The spoon stayed still, and the drain's trumpet became a harmless little burp.",
        "The gazpacho gleamed while the spoon bowed to its rescuers.",
    ),
}

NAMES = ["Luna", "Milo", "Tavi", "Nia", "Rafi"]
PARTNERS = ["Sol", "Pip", "Mara", "Jo", "Kito"]
OPENINGS = [
    "Long ago, when the tiles still remembered every footstep,",
    "In the age when mirrors were said to know jokes,",
    "Beneath a ceiling bright as a pearl,",
    "At the hour when bathroom pipes whispered to the moon,",
]
HUMOR = [
    "The faucet made a face that looked exactly like a surprised potato.",
    "A soap bubble rose proudly, then popped as if it had forgotten its speech.",
    "The bath mat tried to look majestic, although one corner kept sneezing.",
]
REFLECTIONS = [
    "Thus the bathroom learned that a grand problem may need several small hands.",
    "The old mirror remembered that laughter makes careful work feel lighter.",
    "No hero worked alone that night; even the quietest helper changed the ending.",
]


@dataclass
class StoryParams:
    setting: str = "bathroom"
    incident: str = "bowl_overflow"
    name: str = "Luna"
    partner: str = "Sol"
    helper: str = "Milo"
    opening: int = 0
    humor: int = 0
    reflection: int = 0
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A mythic bathroom tale of gazpacho and teamwork.")
    parser.add_argument("--setting", choices=SETTINGS, default=None)
    parser.add_argument("--incident", choices=INCIDENTS, default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--partner", default=None)
    parser.add_argument("--helper", default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    remaining = [x for x in PARTNERS if x != name]
    partner = args.partner or rng.choice(remaining)
    helper_choices = [x for x in NAMES + PARTNERS if x not in {name, partner}]
    helper = args.helper or rng.choice(helper_choices)
    if len({name, partner, helper}) < 3:
        raise StoryError("The three bathroom helpers must have different names.")
    return StoryParams(
        setting=args.setting or "bathroom",
        incident=args.incident or rng.choice(list(INCIDENTS)),
        name=name,
        partner=partner,
        helper=helper,
        opening=rng.randrange(len(OPENINGS)),
        humor=rng.randrange(len(HUMOR)),
        reflection=rng.randrange(len(REFLECTIONS)),
    )


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.incident not in INCIDENTS:
        raise StoryError(f"Unknown incident: {params.incident}")
    if len({params.name, params.partner, params.helper}) != 3:
        raise StoryError("Team members must have distinct names.")

    world = World(SETTINGS[params.setting])
    luna = world.add(Entity(params.name, "hero", params.name))
    partner = world.add(Entity(params.partner, "helper", params.partner))
    helper = world.add(Entity(params.helper, "helper", params.helper))
    incident = INCIDENTS[params.incident]

    for entity in (luna, partner, helper):
        entity.meters.update({"care": 0.0, "confidence": 0.0, "joy": 0.0})
        entity.memes.update({"teamwork": 0.0, "humor": 0.0})

    world.facts.update(
        hero=luna,
        partner=partner,
        helper=helper,
        incident=incident,
        food="gazpacho",
        object="a glitzy silver bowl",
        sound=incident.sound,
    )

    world.say(
        f"{OPENINGS[params.opening]} {incident.omen} "
        f"{luna.label}, keeper of the {world.setting.label}, found {incident.problem}"
    )
    world.say(
        f'{luna.label} cried, "The gazpacho is in peril!" '
        f'{partner.label} answered, "Then we shall not face it alone." '
        f'{helper.label} added, "I brought teamwork—and a towel."'
    )
    world.para()

    luna.meters["care"] += 1
    luna.memes["teamwork"] += 1
    partner.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    world.say(f"{HUMOR[params.humor]} {incident.clue}")
    world.say(
        f'"Let us make a plan," said {luna.label}. '
        f'{incident.plan} The three helpers moved together, each watching a different part of the bathroom.'
    )
    world.para()

    luna.meters["confidence"] += 1
    partner.meters["confidence"] += 1
    helper.meters["confidence"] += 1
    luna.memes["humor"] += 1
    world.say(
        f"Then came the mighty sound: {incident.sound} "
        f"{incident.resolution} Even the glitzy tiles seemed to applaud."
    )
    world.say(
        f'{partner.label} laughed, "We sounded like a royal orchestra." '
        f'{helper.label} replied, "A royal orchestra with excellent towels." '
        f'{luna.label} grinned, and the bathroom echoed with friendly laughter.'
    )
    world.para()

    for entity in (luna, partner, helper):
        entity.meters["joy"] += 1
    world.facts["resolved"] = True
    world.say(
        f"{REFLECTIONS[params.reflection]} {incident.ending} "
        f"The gazpacho rested safely, cold and bright, beneath the glitzy bathroom light."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    incident = world.facts["incident"]
    return [
        "Write a child-friendly myth set in a bathroom where teamwork solves a funny danger.",
        f"Include gazpacho, a glitzy object, spoken dialogue, and these sound effects: {incident.sound}",
        f"Show the clue and plan clearly: {incident.clue} {incident.plan}",
    ]


def story_qa(world: World) -> list[QAItem]:
    incident = world.facts["incident"]
    hero = world.facts["hero"]
    partner = world.facts["partner"]
    helper = world.facts["helper"]
    return [
        QAItem(
            f"What danger did {hero.label} discover?",
            f"{hero.label} discovered that {incident.problem}",
        ),
        QAItem(
            "What clue helped the team?",
            incident.clue,
        ),
        QAItem(
            "How did the helpers use teamwork?",
            incident.plan,
        ),
        QAItem(
            "What sound effects appeared during the rescue?",
            f"The rescue sounded like {incident.sound}",
        ),
        QAItem(
            "Who worked together?",
            f"{hero.label}, {partner.label}, and {helper.label} worked together and shared the careful jobs.",
        ),
        QAItem(
            "How did the story end?",
            f"{incident.resolution} {incident.ending}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is gazpacho?",
            "Gazpacho is a cold soup, often made with vegetables such as tomatoes, peppers, cucumbers, and onions.",
        ),
        QAItem(
            "What does glitzy mean?",
            "Glitzy means very shiny, sparkling, or showy.",
        ),
        QAItem(
            "What is teamwork?",
            "Teamwork is when people cooperate, share jobs, and help one another reach a goal.",
        ),
        QAItem(
            "Why can sound effects make a story funny?",
            "Sound effects give actions a vivid sound, and an unexpected sound can make a serious moment playful.",
        ),
        QAItem(
            "What is a myth?",
            "A myth is an imaginative traditional-style story that explains an event, value, or remarkable feature through memorable characters and events.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---", f"  setting: {world.setting.label}"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  resolved: {world.facts.get('resolved', False)}")
    lines.append(f"  food: {world.facts.get('food')}")
    return "\n".join(lines)


ASP_RULES = r"""
teamwork :- helper(hero), helper(partner), helper(assistant).
safe_food :- teamwork, clue_found, plan_used.
happy_ending :- safe_food, sound_made.
#show teamwork/0.
#show safe_food/0.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("helper", "hero"),
            asp.fact("helper", "partner"),
            asp.fact("helper", "assistant"),
            asp.fact("clue_found"),
            asp.fact("plan_used"),
            asp.fact("sound_made"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    expected = {"teamwork", "safe_food", "happy_ending"}
    model = asp.one_model(
        asp_program("#show teamwork/0. #show safe_food/0. #show happy_ending/0.")
    )
    actual = {symbol.name for symbol in model}
    if actual == expected:
        sample = generate(
            StoryParams(
                setting="bathroom",
                incident="bowl_overflow",
                name="Luna",
                partner="Sol",
                helper="Milo",
            )
        )
        if "gazpacho" not in sample.story.lower() or "glitzy" not in sample.story.lower():
            print("Generated story failed required-word verification.")
            return 1
        print("OK: ASP twin and generated story checks passed.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("  asp:", sorted(actual))
    print("  expected:", sorted(expected))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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

    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp:
        print(asp_program("#show teamwork/0. #show safe_food/0. #show happy_ending/0."))
        return
    if args.asp:
        import asp
        model = asp.one_model(
            asp_program("#show teamwork/0. #show safe_food/0. #show happy_ending/0.")
        )
        print("\n".join(sorted(str(atom) for atom in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, incident in enumerate(INCIDENTS):
            params = StoryParams(
                setting="bathroom",
                incident=incident,
                name="Luna",
                partner="Sol",
                helper="Milo",
                opening=index % len(OPENINGS),
                humor=index % len(HUMOR),
                reflection=index % len(REFLECTIONS),
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
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
