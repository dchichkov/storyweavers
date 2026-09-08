#!/usr/bin/env python3
"""
A child-friendly superhero story world about bacon, a careful removal,
a surprising twist, and reconciliation.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    partner_name: str
    setting: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Character
    partner: Character
    setting: str
    bacon_state: str = "near_machine"
    threat: str = "unknown"
    twist: str = ""
    reconciliation: bool = False
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


HERO_NAMES = ["Luna", "Nova", "Mira", "Zara", "Pip", "Kite", "Rae", "Sol"]
PARTNER_NAMES = ["Theo", "Nia", "Bo", "Ari", "Milo", "June", "Tess", "Finn"]
SETTINGS = [
    "the rooftop garden",
    "the busy town kitchen",
    "the school science fair",
    "the Moonlight Market",
    "the firehouse courtyard",
    "the train-station café",
]

SCENARIOS = [
    {
        "title": "the sizzling signal",
        "setup": "a strip of bacon slipped from a breakfast tray beside a humming rescue robot",
        "mistake": "Luna thought the bacon had jammed the robot's wheel",
        "danger": "hot grease could burn someone, and food near moving machinery could make the wheel catch",
        "action": "reached for the bacon with a bare hand",
        "clue": "the robot's wheel was clear, while a loose red cable blinked under the tray",
        "remove": "used tongs to remove the bacon from the warm floor and asked an adult to unplug the robot",
        "twist": "the bacon had not caused the trouble at all; it had hidden the cable's blinking warning",
        "ending": "the robot rolled safely again while the bacon rested in a covered dish",
    },
    {
        "title": "the cape-and-bacon mix-up",
        "setup": "a bacon strip lay across a red superhero cape in the school kitchen",
        "mistake": "Luna believed the cape had been stained and blamed her partner for spilling breakfast",
        "danger": "pulling quickly could tear the cape or splash hot grease from the nearby pan",
        "action": "tugged the bacon away with both hands",
        "clue": "the cape was clean beneath the strip, and a serving spoon had left the curved mark",
        "remove": "asked the cook to remove the bacon with a fork and move the cape away from the pan",
        "twist": "the supposed stain was only a shadow cast by the spoon",
        "ending": "the cape fluttered cleanly above a safely covered breakfast tray",
    },
    {
        "title": "the market alarm",
        "setup": "a bacon basket tipped near the Moonlight Market's tiny alarm button",
        "mistake": "Luna thought her partner had pressed the alarm while showing off",
        "danger": "the alarm could summon a crowd, and loose food could make the walkway slippery",
        "action": "started scolding her partner before checking the basket",
        "clue": "a rolling lemon had bumped the button, and one bacon strip had stopped against the wheel",
        "remove": "helped remove the bacon from the walkway and asked the vendor to reset the alarm",
        "twist": "the noisy alarm was caused by a lemon, not by the partner's prank",
        "ending": "the basket stood steady as the market bell rang only for the evening closing",
    },
    {
        "title": "the rooftop rescue",
        "setup": "a cool strip of bacon rested beside a pigeon-shaped delivery drone on the rooftop",
        "mistake": "Luna thought the drone was carrying a secret message from a rival hero",
        "danger": "touching the drone's propeller could hurt fingers, and food could attract birds into its path",
        "action": "leaned toward the drone to grab the bacon",
        "clue": "the drone's message light pointed to a missing weather sensor, not to the bacon",
        "remove": "used a long grabber to remove the bacon and called the rooftop caretaker",
        "twist": "the rival message was really a weather alert asking heroes to secure loose objects",
        "ending": "the drone carried the sensor home while the bacon stayed in a sealed lunch box",
    },
    {
        "title": "the firehouse false alarm",
        "setup": "a bacon smell drifted through the firehouse while a practice alarm flashed",
        "mistake": "Luna thought the bacon smoke had started a fire",
        "danger": "running into a kitchen without checking could cause a collision near the hot stove",
        "action": "charged through the doorway shouting for everyone to escape",
        "clue": "the alarm card said PRACTICE, and the bacon was cooking on a supervised griddle",
        "remove": "helped remove the practice sign after the drill and left the bacon with the cook",
        "twist": "the alarm was a planned safety lesson, not an emergency",
        "ending": "the firefighters clapped as Luna learned that brave heroes check signals before rushing",
    },
    {
        "title": "the missing lunch badge",
        "setup": "a bacon wrapper covered the bright badge on a lunchbox at the science fair",
        "mistake": "Luna thought the badge had vanished and suspected her partner had taken it",
        "danger": "accusing someone could hurt their friendship, and the wrapper had greasy crumbs",
        "action": "pointed at her partner and demanded an explanation",
        "clue": "the badge's corner showed beneath the wrapper, while the partner's hands were holding a model planet",
        "remove": "asked permission to remove the wrapper, washed the lunchbox, and apologized",
        "twist": "the missing badge had been there the whole time, hidden by the wrapper",
        "ending": "the badge shone beside the planet model as both friends presented their project",
    },
]

OPENINGS = [
    "The morning began with a heroic promise:",
    "At first, the day seemed as ordinary as a quiet cape hanging on a hook.",
    "Luna was checking her rescue gear when",
    "Just before the town's biggest little problem arrived,",
    "The superhero team was sharing breakfast when",
]

LESSONS = [
    "Luna learned that a real superhero checks before blaming anyone.",
    "The team discovered that careful hands can solve a problem without making a bigger one.",
    "They learned that courage includes saying, \"I was wrong,\" when new evidence appears.",
    "Luna understood that protecting a friend matters as much as protecting a machine.",
]

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero story world about bacon, removal, twist, and reconciliation."
    )
    parser.add_argument("--hero-name", choices=HERO_NAMES)
    parser.add_argument("--partner-name", choices=PARTNER_NAMES)
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero_name or rng.choice(HERO_NAMES)
    partner = args.partner_name or rng.choice(PARTNER_NAMES)
    setting = args.setting or rng.choice(SETTINGS)
    return StoryParams(hero_name=hero, partner_name=partner, setting=setting)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name == params.partner_name:
        raise StoryError("The superhero and partner need different names.")
    if params.setting not in SETTINGS:
        raise StoryError("That setting is not part of this superhero world.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    opening = rng.choice(OPENINGS)
    lesson = rng.choice(LESSONS)

    hero = Character(
        name=params.hero_name,
        kind="superhero",
        meters={"distance_to_bacon": 2.0, "distance_to_danger": 3.0},
        memes={"bravery": 1.0, "curiosity": 1.0},
    )
    partner = Character(
        name=params.partner_name,
        kind="partner",
        meters={"distance_to_hero": 1.0},
        memes={"trust": 1.0, "patience": 1.0},
    )
    world = World(hero=hero, partner=partner, setting=params.setting)
    world.threat = scenario["danger"]
    world.twist = scenario["twist"]

    lines = [
        f"{opening} {hero.name} and {partner.name} were the town's small but mighty superhero team in {params.setting}.",
        f"They noticed {scenario['setup']}.",
        f"{hero.name} made a quick mistake: {scenario['mistake']}.",
        f"Before asking a question, {hero.name} {scenario['action']}.",
        f"\"Wait,\" said {partner.name}. \"Can we look before we decide?\"",
        f"{hero.name} paused. \"You are right. What do you see?\"",
        f"Together they noticed that {scenario['clue']}.",
        f"The twist was surprising: {scenario['twist']}.",
        f"{hero.name} lowered her hands and said, \"I am sorry I blamed you. Will you help me fix this?\"",
        f"{partner.name} smiled. \"Yes. Heroes can repair trust as well as trouble.\"",
        f"Working carefully, {hero.name} {scenario['remove']}.",
        f"The danger was handled because {scenario['danger']}.",
        lesson,
        f"By sunset, {scenario['ending']}.",
        f"{hero.name} and {partner.name} bumped elbows, reconciled and ready for their next call.",
    ]

    world.bacon_state = "removed and safely contained"
    world.reconciliation = True
    world.facts.update(
        {
            "incident": scenario["title"],
            "mistake": scenario["mistake"],
            "clue": scenario["clue"],
            "twist": scenario["twist"],
            "removal": scenario["remove"],
            "ending": scenario["ending"],
            "lesson": lesson,
        }
    )
    world.facts["story"] = " ".join(lines)

    prompts = [
        f"Write a superhero story called {scenario['title']} about bacon and a careful removal.",
        f"Tell a child-friendly story in {params.setting} with a twist and reconciliation.",
        f"Show {hero.name} learning to check facts before blaming {partner.name}.",
    ]

    story_qa = [
        QAItem(
            question=f"What did {params.hero_name} first misunderstand?",
            answer=f"{params.hero_name} first thought that {scenario['mistake']}.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {scenario['twist']}.",
        ),
        QAItem(
            question="How was the bacon removed safely?",
            answer=f"The team safely handled it when {scenario['remove']}.",
        ),
        QAItem(
            question=f"How did {params.hero_name} and {params.partner_name} reconcile?",
            answer=f"{params.hero_name} apologized for blaming {params.partner_name}, and they worked together to solve the problem.",
        ),
        QAItem(
            question="What lesson did the superhero team learn?",
            answer=lesson,
        ),
    ]

    world_qa = [
        QAItem(
            question="Why should someone be careful around hot bacon?",
            answer="Hot bacon and grease can burn skin, so a child should ask a responsible adult for help and use safe tools.",
        ),
        QAItem(
            question="What does remove mean?",
            answer="Remove means to take something away from a place carefully and put it somewhere safer or more suitable.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change in what the characters or reader thought was happening.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means repairing a disagreement by telling the truth, apologizing when needed, listening, and choosing to work together again.",
        ),
        QAItem(
            question="What makes a good superhero?",
            answer="A good superhero protects people, checks facts, asks for help when needed, and uses courage with care.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        world = sample.world
        print()
        print("--- trace ---")
        print(
            f"hero={world.hero.name}, kind={world.hero.kind}, "
            f"meters={world.hero.meters}, memes={world.hero.memes}"
        )
        print(
            f"partner={world.partner.name}, kind={world.partner.kind}, "
            f"meters={world.partner.meters}, memes={world.partner.memes}"
        )
        print(
            f"setting={world.setting}, bacon_state={world.bacon_state}, "
            f"reconciliation={world.reconciliation}"
        )
        print(f"twist={world.twist}")
    if qa:
        print()
        print("== prompts ==")
        for number, prompt in enumerate(sample.prompts, 1):
            print(f"{number}. {prompt}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
valid_setting(S) :- setting(S).
#show valid_setting/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("setting", setting) for setting in SETTINGS)


def asp_program(show: str = "#show valid_setting/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_settings() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_setting")))


def asp_verify() -> int:
    py = {(setting,) for setting in SETTINGS}
    clingo_values = set(asp_valid_settings())
    if py == clingo_values:
        print(f"OK: clingo gate matches valid settings ({len(py)} settings).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - clingo_values:
        print("  only in python:", sorted(py - clingo_values))
    if clingo_values - py:
        print("  only in clingo:", sorted(clingo_values - py))
    return 1


def generation_params(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        result: list[StoryParams] = []
        for index, setting in enumerate(SETTINGS):
            hero = HERO_NAMES[index % len(HERO_NAMES)]
            partner = PARTNER_NAMES[index % len(PARTNER_NAMES)]
            result.append(StoryParams(hero_name=hero, partner_name=partner, setting=setting))
        return result
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [resolve_params(args, random.Random(base + index)) for index in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        result = asp_verify()
        if result:
            sys.exit(result)
        for index, params in enumerate(generation_params(args)):
            params.seed = (args.seed if args.seed is not None else 0) + index
            generate(params)
        print("OK: generated stories passed the Python reasonableness gate.")
        return

    if args.asp:
        print("\n".join(setting[0] for setting in asp_valid_settings()))
        return

    samples: list[StorySample] = []
    for index, params in enumerate(generation_params(args)):
        params.seed = (args.seed if args.seed is not None else 0) + index
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
