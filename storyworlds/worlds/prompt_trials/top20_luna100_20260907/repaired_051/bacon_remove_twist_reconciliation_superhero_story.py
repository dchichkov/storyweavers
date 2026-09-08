#!/usr/bin/env python3
"""
A small superhero storyworld about Bacon, a removable problem, a twist,
and a reconciliation.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(
        default_factory=lambda: {
            "distance": 0.0,
            "danger": 0.0,
            "power": 0.0,
            "damage": 0.0,
        }
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "worry": 0.0,
            "courage": 0.0,
            "trust": 0.0,
            "anger": 0.0,
            "relief": 0.0,
            "joy": 0.0,
        }
    )


@dataclass
class Setting:
    place: str
    landmark: str


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    rival_name: str
    rival_type: str
    bacon_kind: str
    place: str
    landmark: str
    scenario_index: int = 0
    twist_index: int = 0
    detail_variant: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace_log: list[str] = []

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

    def log(self, text: str) -> None:
        self.trace_log.append(text)


SCENARIOS = [
    {
        "mission": "remove the giant bacon balloon from the school roof before it blocked the sun",
        "problem": "A runaway bacon-shaped balloon had wrapped its string around the weather vane.",
        "first_plan": "The hero pulled hard, but the balloon tugged the vane loose and spun it faster.",
        "clue": "The rival noticed that the balloon relaxed whenever the school bell rang.",
        "action": "They rang the bell in a steady rhythm while the hero climbed close enough to loosen the string.",
        "result": "The balloon floated down into a soft net instead of crashing onto the playground.",
        "lesson": "a rival may see the clue a hero misses",
        "image": "the school roof shone again, and the bacon balloon rested harmlessly beside the flagpole",
        "reconciliation": "The hero thanked the rival for hearing the pattern, and the rival accepted the thanks with a grin.",
    },
    {
        "mission": "remove a bacon-powered smoke cloud from the city fountain",
        "problem": "A broken breakfast machine was puffing smoky bacon clouds over the town square.",
        "first_plan": "The hero blasted the cloud upward, but the wind pushed it toward the library windows.",
        "clue": "The rival remembered that the machine had a tiny red release lever behind its copper drum.",
        "action": "The hero shielded the crowd while the rival reached through the steam and pulled the lever.",
        "result": "The machine sighed, the cloud vanished, and the fountain water sparkled clearly again.",
        "lesson": "strength works best when it protects another person's careful idea",
        "image": "clear water leaped in the fountain while clean morning light returned to the square",
        "reconciliation": "The hero admitted that the rival's small plan had saved the library, and they agreed to guard the square together.",
    },
    {
        "mission": "remove the bacon comet from the town's emergency signal",
        "problem": "A bright bacon-shaped comet had stuck to the signal tower and made every warning light flash.",
        "first_plan": "The hero tried to push it away, but the comet split into three sizzling sparks.",
        "clue": "The rival saw that the sparks always flew toward the old copper mirror.",
        "action": "They turned the mirror toward the river, and the reflected moonlight guided every spark safely away.",
        "result": "The signal tower became quiet and ready for a real emergency.",
        "lesson": "an odd mistake can reveal the path to a safer solution",
        "image": "the tower's blue signal blinked once, calmly, above the sleeping town",
        "reconciliation": "The hero apologized for laughing at the rival's strange idea, and the rival shared the mirror without hesitation.",
    },
    {
        "mission": "remove a giant strip of bacon from the bridge cables",
        "problem": "A gust had carried a magical strip of bacon onto the bridge, where it clung to the highest cable.",
        "first_plan": "The hero flew up alone, but the bacon twisted around the cape and pulled the hero sideways.",
        "clue": "The rival discovered that the bacon came loose when warmed by the bridge lamps.",
        "action": "The rival switched on the lamps while the hero held a rescue blanket beneath the cable.",
        "result": "The bacon slid down onto the blanket, leaving the bridge safe for every traveler.",
        "lesson": "asking for help can turn a dangerous solo trick into a safe rescue",
        "image": "cars rolled over the bridge while the rescued bacon cooled in a silver lunch tin",
        "reconciliation": "The hero promised not to fly off alone next time, and the rival promised to call before teasing.",
    },
    {
        "mission": "remove bacon-colored paint from the museum's hero statue",
        "problem": "A prank had covered the statue in sticky orange paint that looked like bacon.",
        "first_plan": "The hero scrubbed one arm quickly, spreading the paint across the statue's shining chest.",
        "clue": "The rival found a cleaning cloth marked with the museum keeper's safe-removal symbol.",
        "action": "They tested the cloth on a hidden corner, then wiped the statue together from top to bottom.",
        "result": "The statue's silver shield appeared again without a single scratch.",
        "lesson": "repair begins with listening to the person who knows the material",
        "image": "the silver statue reflected two friends standing side by side in the museum hall",
        "reconciliation": "The hero listened to the rival's warning, and the rival forgave the hurried mistake after the statue was safe.",
    },
]

HERO_TYPES = ["flying hero", "speedy hero", "shield hero", "storm hero", "bright hero"]
RIVAL_TYPES = ["inventor hero", "quiet hero", "night hero", "puzzle hero", "wind hero"]
PLACES = [
    ("Maple City", "the school roof"),
    ("Harbor City", "the city fountain"),
    ("Brighton", "the signal tower"),
    ("River City", "the high bridge"),
    ("Silver Square", "the museum hall"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Superhero Story: Bacon, a twist, and reconciliation.")
    parser.add_argument("--name")
    parser.add_argument("--type")
    parser.add_argument("--rival")
    parser.add_argument("--rival-type")
    parser.add_argument("--bacon")
    parser.add_argument("--place")
    parser.add_argument("--landmark")
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
    place, landmark = rng.choice(PLACES)
    return StoryParams(
        hero_name=args.name or rng.choice(["Nova", "Comet", "Bolt", "Skye", "Flare"]),
        hero_type=args.type or rng.choice(HERO_TYPES),
        rival_name=args.rival or rng.choice(["Echo", "Mira", "Patch", "Sparrow", "Vega"]),
        rival_type=args.rival_type or rng.choice(RIVAL_TYPES),
        bacon_kind=args.bacon or rng.choice(
            ["bacon balloon", "bacon cloud", "bacon comet", "magic strip of bacon"]
        ),
        place=args.place or place,
        landmark=args.landmark or landmark,
        scenario_index=rng.randrange(len(SCENARIOS)),
        twist_index=rng.randrange(4),
        detail_variant=rng.randrange(10000),
    )


def _choose(items: list[str], variant: int, offset: int) -> str:
    return items[(variant // (offset + 1) + offset) % len(items)]


def tell(params: StoryParams) -> World:
    if params.hero_name == params.rival_name:
        raise StoryError("hero and rival must have different names")
    if not params.hero_name.strip() or not params.rival_name.strip():
        raise StoryError("hero and rival names cannot be empty")

    scenario = SCENARIOS[params.scenario_index % len(SCENARIOS)]
    setting = Setting(params.place, params.landmark)
    world = World(setting)

    hero = world.add(Entity("hero", "superhero", params.hero_name, params.hero_type))
    rival = world.add(Entity("rival", "superhero", params.rival_name, params.rival_type))
    bacon = world.add(Entity("bacon", "object", params.bacon_kind, "magical obstacle"))
    citizen = world.add(Entity("citizen", "person", "the townspeople", "people to protect"))

    world.facts.update(hero=hero, rival=rival, bacon=bacon, citizen=citizen, scenario=scenario)
    hero.meters["power"] = 2.0
    rival.meters["power"] = 1.0
    bacon.meters["danger"] = 2.0
    hero.memes["courage"] = 1.0
    rival.memes["trust"] = 1.0
    citizen.memes["worry"] = 2.0

    openings = [
        f"In {params.place}, {hero.label} the {hero.role} watched over {setting.landmark}.",
        f"At dawn in {params.place}, {hero.label} patrolled above {setting.landmark}.",
        f"When the city bells rang, {hero.label} stood ready beside {setting.landmark}.",
    ]
    world.say(_choose(openings, params.detail_variant, 1))
    world.say(f'Then an alarm flashed: "{scenario["mission"].capitalize()}!"')
    world.say(
        f"The strange {bacon.label} was dangerous because it threatened the people below, "
        f"so {hero.label} hurried to help."
    )
    world.para()

    bacon.meters["distance"] = 1.0
    hero.memes["worry"] = 1.0
    world.say(f"{scenario['problem']} {hero.label} raised a brave hand and made a quick plan.")
    world.say(f"{scenario['first_plan']}")
    hero.meters["damage"] = 1.0
    bacon.meters["danger"] = 3.0
    world.say(
        f'"I can fix this alone!" {hero.label} called. '
        f'"Maybe," answered {rival.label}, "but first let us look more closely."'
    )
    world.para()

    rival.memes["courage"] = 1.0
    hero.memes["anger"] = 1.0
    twist_lines = [
        f"That was the twist: {scenario['clue']}",
        f"Just when the rescue seemed stuck, the truth turned around. {scenario['clue']}",
        f"The problem was not what it first appeared to be. {scenario['clue']}",
        f"A surprising clue changed the mission. {scenario['clue']}",
    ]
    world.say(_choose(twist_lines, params.twist_index, 3))
    world.say(
        f'"You found the missing piece," {hero.label} said. '
        f'"And you have the power to use it safely," {rival.label} replied.'
    )
    hero.memes["anger"] = 0.0
    hero.memes["trust"] = 2.0
    rival.memes["trust"] = 2.0
    world.say(scenario["action"])
    world.para()

    bacon.meters["danger"] = 0.0
    bacon.meters["damage"] = 0.0
    hero.meters["damage"] = 0.0
    citizen.memes["worry"] = 0.0
    citizen.memes["relief"] = 2.0
    hero.memes["relief"] = 1.0
    rival.memes["joy"] = 1.0
    world.say(scenario["result"])
    world.say(f"{scenario['reconciliation']}")
    world.say(
        f'"A real superhero does not have to be the only one with an idea," '
        f'{hero.label} admitted. "{rival.label}, will you team up with me?"'
    )
    world.say(
        f'"Yes," said {rival.label}. "We can remove trouble better when we trust each other."'
    )
    world.para()

    world.say(
        f"The two heroes promised to protect {params.place} together and to speak kindly "
        "before making their next rescue plan."
    )
    world.say(f"By evening, {scenario['image']}.")
    world.log(f"scenario={params.scenario_index % len(SCENARIOS)}")
    world.log("twist=the rival's overlooked clue solved the problem")
    world.log("reconciliation=the heroes apologized and formed a team")
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    rival: Entity = world.facts["rival"]  # type: ignore[assignment]
    bacon: Entity = world.facts["bacon"]  # type: ignore[assignment]
    scenario: dict[str, str] = world.facts["scenario"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly Superhero Story about {hero.label} and {rival.label}.",
        f"Include bacon, and have the heroes remove the {bacon.label} from danger.",
        f"Make the story include a twist, a brief dialogue exchange, and reconciliation after a disagreement.",
        f"Show how the clue changes what {hero.label} decides to do.",
        f"End with the heroes trusting one another after they {scenario['mission']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    rival: Entity = world.facts["rival"]  # type: ignore[assignment]
    bacon: Entity = world.facts["bacon"]  # type: ignore[assignment]
    scenario: dict[str, str] = world.facts["scenario"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What danger did {hero.label} and {rival.label} face?",
            answer=f"They had to {scenario['mission']}. The {bacon.label} threatened people or an important place.",
        ),
        QAItem(
            question="What was the twist in the rescue?",
            answer=f"The twist was that {scenario['clue']} This changed the heroes' plan.",
        ),
        QAItem(
            question=f"Why did {hero.label}'s first plan fail?",
            answer=f"It failed because {scenario['first_plan'].replace('The hero ', '').replace('the hero ', '').rstrip('.')}. The danger grew until the heroes examined the clue.",
        ),
        QAItem(
            question=f"How did {rival.label} help?",
            answer=f"{rival.label} noticed the important clue, and then the heroes worked together: {scenario['action']}",
        ),
        QAItem(
            question="How did the heroes reconcile?",
            answer=f"They apologized, thanked each other, and promised to trust one another. {scenario['reconciliation']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a character with unusual abilities or courage who uses those gifts to protect and help others.",
        ),
        QAItem(
            question="What does remove mean?",
            answer="Remove means to take something away from a place or to separate it so the place becomes safer or clearer.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is making peace after a disagreement by listening, apologizing, and choosing to trust or cooperate again.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change in what the characters or readers expect, often revealing a better way to solve the problem.",
        ),
        QAItem(
            question="Why should heroes work together?",
            answer="Heroes should work together because different people may notice different clues, skills, or safe ways to help.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        details = [f"kind={entity.kind}", f"role={entity.role}"]
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: " + ", ".join(details))
    lines.extend(world.trace_log)
    return "\n".join(lines)


ASP_RULES = r"""
entity(hero).
entity(rival).
entity(bacon).
entity(citizen).

noticed_clue(rival).
trusted(hero,rival).
trusted(rival,hero).
removed(bacon).
protected(citizen).
reconciled(hero,rival).

safe_rescue :- noticed_clue(rival), removed(bacon), protected(citizen).
team_restored :- trusted(hero,rival), trusted(rival,hero), reconciled(hero,rival).
happy_end :- safe_rescue, team_restored.

#show safe_rescue/0.
#show team_restored/0.
#show happy_end/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("noticed_clue", "rival"),
            asp.fact("trusted", "hero", "rival"),
            asp.fact("trusted", "rival", "hero"),
            asp.fact("removed", "bacon"),
            asp.fact("protected", "citizen"),
            asp.fact("reconciled", "hero", "rival"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show safe_rescue/0. #show team_restored/0. #show happy_end/0."
        )
    )
    atoms = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {"safe_rescue/0", "team_restored/0", "happy_end/0"}
    if atoms != expected:
        print(f"MISMATCH: {sorted(atoms)} != {sorted(expected)}")
        return 1

    rng = random.Random(91827)
    for _ in range(5):
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if "twist" not in sample.story.lower():
            print("MISMATCH: generated story lacks the twist marker")
            return 1
        if "reconcil" not in sample.story.lower():
            print("MISMATCH: generated story lacks reconciliation")
            return 1
        if "bacon" not in sample.story.lower() or "remove" not in sample.story.lower():
            print("MISMATCH: generated story lacks required seed words")
            return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


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


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        hero_name="Nova",
        hero_type="flying hero",
        rival_name="Echo",
        rival_type="inventor hero",
        bacon_kind="bacon balloon",
        place="Maple City",
        landmark="the school roof",
        scenario_index=0,
        twist_index=0,
        detail_variant=3,
    ),
    StoryParams(
        hero_name="Bolt",
        hero_type="speedy hero",
        rival_name="Mira",
        rival_type="quiet hero",
        bacon_kind="bacon cloud",
        place="Harbor City",
        landmark="the city fountain",
        scenario_index=1,
        twist_index=1,
        detail_variant=7,
    ),
    StoryParams(
        hero_name="Skye",
        hero_type="storm hero",
        rival_name="Patch",
        rival_type="puzzle hero",
        bacon_kind="bacon comet",
        place="Brighton",
        landmark="the signal tower",
        scenario_index=2,
        twist_index=2,
        detail_variant=11,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_rescue/0. #show team_restored/0. #show happy_end/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show safe_rescue/0. #show team_restored/0. #show happy_end/0."
            )
        )
        print("ASP model:", " ".join(str(atom) for atom in model))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 20, 20):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            attempt += 1
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

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
