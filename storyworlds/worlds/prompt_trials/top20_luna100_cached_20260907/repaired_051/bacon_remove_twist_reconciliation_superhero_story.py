#!/usr/bin/env python3
"""
A small Superhero Story world about Bacon, Remove, Twist, and Reconciliation.
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
    kind: str = "person"
    type: str = "hero"
    label: str = ""
    meters: dict[str, float] = field(
        default_factory=lambda: {"distance": 0.0, "energy": 0.0, "damage": 0.0, "repair": 0.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"worry": 0.0, "courage": 0.0, "trust": 0.0, "anger": 0.0, "relief": 0.0}
    )


@dataclass
class Setting:
    place: str = "Beacon City"


@dataclass
class StoryParams:
    hero_name: str
    hero_power: str
    partner_name: str
    partner_power: str
    rival_name: str
    bacon_kind: str
    scenario_index: int = 0
    detail_variant: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        "crisis": "a runaway breakfast blimp was dropping sizzling bacon over the crowded square",
        "place": "the Clockwork Plaza",
        "twist": "the blimp was not attacking at all; its steering bell had been jammed by a loose metal twist",
        "first_plan": "Captain Ember tried to blast the blimp's engine, but the hot wind pushed it toward the school roof",
        "clue": "Bolt saw that the bacon basket was still tied safely and heard a frightened bell ringing inside the engine",
        "action": "Bolt used a soft magnetic field to hold the blimp steady while Captain Ember twisted the jammed bell back into place",
        "reconciliation": "Captain Ember apologized for blaming the blimp's owner, and the owner admitted he had ignored the loose bell during breakfast",
        "result": "The blimp floated down, and every bacon strip landed in warm baskets instead of on anyone's head",
        "image": "the square glowed with clean brass, full baskets, and a bacon-scented breeze",
        "lesson": "a hero should learn the whole problem before striking at it",
        "dialogue": "Wait! The loudest danger may be asking for help",
    },
    {
        "crisis": "a giant bacon-shaped signal balloon had snagged on the museum tower",
        "place": "the Museum Roof",
        "twist": "the balloon's rope was twisted around a weather vane, and pulling it would tear the museum's oldest banner",
        "first_plan": "Thunder Finch tugged hard on the rope, making the tower groan and sending sparks across the roof",
        "clue": "Mira noticed that the balloon rose whenever the wind came from the river",
        "action": "Mira waited for the river breeze, while Thunder Finch used a feather-light gust to untwist the rope one loop at a time",
        "reconciliation": "Thunder Finch thanked Mira for stopping him, and Mira agreed that brave work could still be careful work",
        "result": "The signal balloon rose free without removing a single stitch from the historic banner",
        "image": "the bacon balloon bobbed above the museum like a bright pink moon",
        "lesson": "strength becomes safer when it listens to patience",
        "dialogue": "I can make the wind move, but you can show me when to move it",
    },
    {
        "crisis": "a villain's breakfast machine had begun to remove every smell from the neighborhood",
        "place": "the Sunny Market",
        "twist": "the machine had been built to remove smoke from kitchens, but its filter was twisted backward",
        "first_plan": "Solar Scout accused Dr. Crumble of stealing everyone's breakfasts and chased him through the spice stalls",
        "clue": "Dr. Crumble pointed out that the machine had removed smoke but also removed the smell of fresh bread",
        "action": "The heroes stopped chasing, removed the backward filter, and twisted it into the clean position",
        "reconciliation": "Solar Scout apologized for calling Dr. Crumble a thief, and Dr. Crumble promised to ask for help before testing a machine in public",
        "result": "The market smelled of bread, apples, and bacon again, while the kitchens stayed free of smoke",
        "image": "vendors cheered as warm breakfast smells curled beneath the striped awnings",
        "lesson": "repairing trust can be part of repairing a machine",
        "dialogue": "You made a mistake, not a monster of yourself",
    },
    {
        "crisis": "a cloud of silver drones was carrying the city's emergency bacon supply away",
        "place": "the River Bridge",
        "twist": "the drones were following an old rescue signal twisted into the shape of a villain's mark",
        "first_plan": "Comet Kid fired a sparkling net before checking the signal, and three drones spun toward the bridge cables",
        "clue": "Night Nurse recognized the rescue code hidden inside the twisted mark",
        "action": "The heroes removed the false signal, sent the correct rescue code, and guided the drones to the community kitchen",
        "reconciliation": "Comet Kid admitted the mistake, and Night Nurse trusted him to carry the corrected signal",
        "result": "The bacon reached hungry families, and the drones became helpers instead of hazards",
        "image": "silver drones formed a shining arrow above the bridge at sunset",
        "lesson": "even a frightening message may hide a hopeful purpose",
        "dialogue": "Before we remove the messenger, let us read the message",
    },
]


OPENINGS = [
    "At sunrise",
    "Just as the city bells rang",
    "On a bright morning",
    "While breakfast shops opened",
    "When the first golden light touched Beacon City",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero Story: Bacon, Remove, Twist, and Reconciliation."
    )
    parser.add_argument("--name")
    parser.add_argument("--power")
    parser.add_argument("--partner")
    parser.add_argument("--partner-power")
    parser.add_argument("--rival")
    parser.add_argument("--bacon")
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
    return StoryParams(
        hero_name=args.name or rng.choice(["Captain Ember", "Solar Scout", "Comet Kid", "Thunder Finch"]),
        hero_power=args.power or rng.choice(["firelight", "sun beams", "star sparks", "storm wings"]),
        partner_name=args.partner or rng.choice(["Bolt", "Mira", "Night Nurse", "Echo"]),
        partner_power=args.partner_power or rng.choice(["magnetism", "quick thinking", "moon vision", "sound waves"]),
        rival_name=args.rival or rng.choice(["Dr. Crumble", "The Tangle", "Professor Soot", "Mister Muddle"]),
        bacon_kind=args.bacon or rng.choice(["crisp bacon", "smoky bacon", "maple bacon", "warm bacon"]),
        scenario_index=rng.randrange(len(SCENARIOS)),
        detail_variant=rng.randrange(10000),
    )


def tell(params: StoryParams) -> World:
    scenario = SCENARIOS[params.scenario_index % len(SCENARIOS)]
    world = World(Setting())
    hero = world.add(Entity("hero", label=params.hero_name, type="hero"))
    partner = world.add(Entity("partner", label=params.partner_name, type="hero"))
    rival = world.add(Entity("rival", label=params.rival_name, type="rival"))
    bacon = world.add(Entity("bacon", kind="thing", type="food", label=params.bacon_kind))

    world.facts.update(hero=hero, partner=partner, rival=rival, bacon=bacon, scenario=scenario)
    hero.memes["courage"] += 1
    partner.memes["trust"] += 1

    opening = OPENINGS[params.detail_variant % len(OPENINGS)]
    world.say(
        f"{opening}, {params.hero_name} the superhero watched over {world.setting.place} "
        f"with the power of {params.hero_power}."
    )
    world.say(
        f"Beside {params.hero_name} stood {params.partner_name}, whose gift was {params.partner_power}. "
        f"Together they protected a cart of {params.bacon_kind} for the city's breakfast picnic."
    )
    world.para()

    hero.memes["worry"] += 1
    world.say(
        f"Then {scenario['crisis'].capitalize()}. "
        f"{params.hero_name} flew toward the trouble, while {params.partner_name} hurried below."
    )
    world.say(f'"We must remove the danger before anyone gets hurt!" {params.hero_name} cried.')
    world.say(
        f'"Wait and look closely," {params.partner_name} answered. '
        f'"A twist in the story may be hiding inside the twist we can see."'
    )
    world.para()

    hero.meters["energy"] += 1
    hero.memes["anger"] += 1
    world.say(f"{scenario['first_plan']}.")
    world.say(
        f"At that moment, the twist became clear: {scenario['twist']}. "
        f"{scenario['clue']}."
    )
    world.say(
        f'"You were right to stop me," {params.hero_name} said. '
        f'"Let us remove the real problem, not punish the wrong person."'
    )
    world.say(f"{scenario['action']}.")
    world.para()

    hero.meters["repair"] += 1
    partner.meters["repair"] += 1
    hero.memes["anger"] = 0
    hero.memes["trust"] += 1
    rival.memes["trust"] += 1
    bacon.meters["damage"] = 0
    world.say(f"{scenario['reconciliation']}.")
    world.say(f"{scenario['result']}.")
    world.say(
        f"The heroes shared the {params.bacon_kind} with the people they had helped, "
        f"and even {params.rival_name} received a warm plate."
    )
    world.para()

    hero.memes["relief"] += 1
    partner.memes["relief"] += 1
    world.say(f"{params.hero_name} learned that {scenario['lesson']}.")
    world.say(
        f"As evening settled over the city, {scenario['image']}. "
        f"The heroes' greatest victory was not only saving the day, but choosing reconciliation."
    )
    world.log(f"scenario={params.scenario_index % len(SCENARIOS)}")
    world.log("twist_revealed=true")
    world.log("reconciliation_complete=true")
    world.log("bacon_safe=true")
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    partner: Entity = world.facts["partner"]  # type: ignore[assignment]
    bacon: Entity = world.facts["bacon"]  # type: ignore[assignment]
    scenario: dict[str, str] = world.facts["scenario"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly Superhero Story about {hero.label} saving {bacon.label}.",
        f"Tell a superhero adventure where a twist reveals the real problem and {hero.label} chooses reconciliation.",
        f"Write a story that includes the words bacon and remove, with {hero.label} and {partner.label} solving a problem by listening.",
        f"Show how a hero can repair both a dangerous machine and a damaged friendship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    partner: Entity = world.facts["partner"]  # type: ignore[assignment]
    rival: Entity = world.facts["rival"]  # type: ignore[assignment]
    bacon: Entity = world.facts["bacon"]  # type: ignore[assignment]
    scenario: dict[str, str] = world.facts["scenario"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What danger did {hero.label} face?",
            answer=f"{hero.label} faced {scenario['crisis']}. The danger threatened people and the safe delivery of the {bacon.label}.",
        ),
        QAItem(
            question="What was the important twist?",
            answer=f"The important twist was that {scenario['twist']}. This changed the heroes' understanding of what needed to be fixed.",
        ),
        QAItem(
            question=f"How did {partner.label} help?",
            answer=f"{scenario['clue']}. Then {scenario['action']}.",
        ),
        QAItem(
            question="Why did the heroes choose reconciliation?",
            answer=f"They realized that the problem was a mistake or misunderstanding rather than a reason to attack. {scenario['reconciliation']}.",
        ),
        QAItem(
            question=f"What did {hero.label} learn?",
            answer=f"{hero.label} learned that {scenario['lesson']}. The safe {bacon.label} and the repaired relationships proved the lesson.",
        ),
        QAItem(
            question=f"What happened to {rival.label} at the end?",
            answer=f"{rival.label} was included in the peaceful ending, because the heroes repaired the problem and made room for reconciliation instead of blame.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does remove mean?",
            answer="Remove means to take something away, move it out of a place, or get rid of a problem.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that reveals information the characters or readers did not expect.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is the process of making peace after a disagreement, mistake, or hurt feeling.",
        ),
        QAItem(
            question="Why should a superhero investigate before using force?",
            answer="A superhero should investigate first because the apparent danger may have a different cause, and careful choices can protect innocent people.",
        ),
        QAItem(
            question="What is bacon?",
            answer="Bacon is a savory food usually made from cured pork and cooked until tender or crisp.",
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
        details = [f"type={entity.type}"]
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: " + ", ".join(details))
    lines.extend(world.trace_log)
    return "\n".join(lines)


ASP_RULES = r"""
entity(hero).
entity(partner).
entity(rival).
entity(bacon).

danger_removed.
twist_understood.
bacon_safe.
apology_given.
trust_restored :- apology_given, twist_understood.
happy_end :- danger_removed, twist_understood, bacon_safe, trust_restored.

#show danger_removed/0.
#show twist_understood/0.
#show bacon_safe/0.
#show apology_given/0.
#show trust_restored/0.
#show happy_end/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("danger_removed"),
            asp.fact("twist_understood"),
            asp.fact("bacon_safe"),
            asp.fact("apology_given"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show danger_removed/0. #show twist_understood/0. "
            "#show bacon_safe/0. #show apology_given/0. "
            "#show trust_restored/0. #show happy_end/0."
        )
    )
    atoms = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {
        "danger_removed/0",
        "twist_understood/0",
        "bacon_safe/0",
        "apology_given/0",
        "trust_restored/0",
        "happy_end/0",
    }
    if atoms != expected:
        print(f"MISMATCH: {sorted(atoms)} != {sorted(expected)}")
        return 1
    print("OK: ASP parity check passed.")
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
        hero_name="Captain Ember",
        hero_power="firelight",
        partner_name="Bolt",
        partner_power="magnetism",
        rival_name="Dr. Crumble",
        bacon_kind="crisp bacon",
        scenario_index=0,
    ),
    StoryParams(
        hero_name="Solar Scout",
        hero_power="sun beams",
        partner_name="Mira",
        partner_power="quick thinking",
        rival_name="The Tangle",
        bacon_kind="maple bacon",
        scenario_index=1,
    ),
    StoryParams(
        hero_name="Comet Kid",
        hero_power="star sparks",
        partner_name="Night Nurse",
        partner_power="moon vision",
        rival_name="Professor Soot",
        bacon_kind="smoky bacon",
        scenario_index=2,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show danger_removed/0. #show twist_understood/0. "
                "#show bacon_safe/0. #show apology_given/0. "
                "#show trust_restored/0. #show happy_end/0."
            )
        )
        print("ASP model:", " ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 30, 30):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            attempt += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No story variants could be generated.")

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
