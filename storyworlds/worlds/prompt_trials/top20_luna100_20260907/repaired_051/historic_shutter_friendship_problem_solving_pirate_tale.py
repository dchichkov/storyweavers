#!/usr/bin/env python3
"""
A small Pirate Tale storyworld about a historic shutter, friendship, and
problem solving.
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
    type: str
    label: str
    meters: dict[str, float] = field(
        default_factory=lambda: {
            "distance": 0.0,
            "strength": 0.0,
            "safety": 0.0,
            "readiness": 0.0,
        }
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "worry": 0.0,
            "courage": 0.0,
            "trust": 0.0,
            "joy": 0.0,
            "relief": 0.0,
        }
    )


@dataclass
class Setting:
    place: str
    weather: str


@dataclass
class StoryParams:
    captain: str
    captain_type: str
    mate: str
    mate_type: str
    parrot: str
    shutter: str
    setting: str
    weather: str
    scenario_index: int = 0
    detail_variant: int = 0
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace_log: list[str] = field(default_factory=list)

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def log(self, text: str) -> None:
        self.trace_log.append(text)


SCENARIOS = [
    {
        "mission": "open the historic shutter of the old lighthouse before nightfall",
        "place": "Blackfin Harbor",
        "obstacle": "The iron hinge was crusted with salt, and a fallen spar blocked the narrow stairs.",
        "wrong_turn": "The captain pulled hard, but the shutter only groaned and the spar rolled closer to the sea.",
        "clue": "The mate noticed a small brass pin still shining beneath the rust.",
        "method": "They used a rope as a lever, wedged a barrel under the spar, and pushed together when the tide pulled away.",
        "result": "The historic shutter swung open, revealing the lighthouse lantern and a safe channel home.",
        "lesson": "strong friends solve hard problems by sharing ideas instead of pulling alone",
        "image": "the lighthouse beam swept across the water and found every friendly sail",
        "line": "A good crew listens before it heaves",
    },
    {
        "mission": "repair the historic shutter protecting the harbor map room",
        "place": "Whispering Cape",
        "obstacle": "A storm had torn one shutter strap loose and scattered the map-room pegs across wet stones.",
        "wrong_turn": "The captain tried the largest peg first, but it split the soft wood beside the hinge.",
        "clue": "The parrot spotted three tiny nail holes in a neat triangle under the window.",
        "method": "The friends sorted the pegs by shape, held the shutter steady, and used the matching short peg in the old nail holes.",
        "result": "The historic shutter closed firmly around the map room, keeping the charts dry.",
        "lesson": "careful observation can be more useful than a big first guess",
        "image": "dry harbor charts curled safely beneath the repaired wooden shutter",
        "line": "The smallest mark may know the largest secret",
    },
    {
        "mission": "raise the historic shutter of the captain's forgotten signal tower",
        "place": "Cannonball Cove",
        "obstacle": "A thick vine wrapped around the lift chain while gulls cried over the darkening water.",
        "wrong_turn": "Cutting at random only tightened the vine around the chain.",
        "clue": "The mate heard a faint bell whenever the wind touched one loose vine loop.",
        "method": "They followed the bell's sound, loosened the loop, and pulled the chain in a slow rhythm.",
        "result": "The historic shutter rose, and the old signal flag showed the fleet the safest reef passage.",
        "lesson": "patient teamwork can untangle what hurried strength makes worse",
        "image": "the red signal flag snapped above the tower as ships turned from the reef",
        "line": "Let the bell tell us where the knot begins",
    },
    {
        "mission": "find the latch for a historic shutter on the Pearl Lantern",
        "place": "the foggy shipyard",
        "obstacle": "The latch had fallen among silver nails, shells, and pieces of an old anchor chain.",
        "wrong_turn": "The crew chose the shiniest piece, but it was a shell that could not hold the shutter.",
        "clue": "The parrot matched a square scratch on the shutter to a square notch on one dull latch.",
        "method": "They compared every edge, cleaned the dull latch with a cloth, and fitted it while two friends held the shutter.",
        "result": "The historic shutter clicked shut, protecting the ship's emergency lanterns.",
        "lesson": "a useful answer must fit the evidence, not merely look bright",
        "image": "the Pearl Lantern rested quietly while its warm emergency lamps glowed behind the shutter",
        "line": "Bright is not the same as right, matey",
    },
]


OPENINGS = [
    "At dawn",
    "Before the tide turned",
    "While gulls wheeled above the harbor",
    "As the first bell rang across the bay",
    "Under a sky striped with pink clouds",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pirate Tale: a historic shutter, friendship, and problem solving."
    )
    parser.add_argument("--captain")
    parser.add_argument("--captain-type")
    parser.add_argument("--mate")
    parser.add_argument("--mate-type")
    parser.add_argument("--parrot")
    parser.add_argument("--shutter")
    parser.add_argument("--setting")
    parser.add_argument("--weather")
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
    captain = args.captain or rng.choice(["Captain Mira", "Captain Flint", "Captain Rosa"])
    captain_type = args.captain_type or rng.choice(["human", "otter", "fox"])
    mate = args.mate or rng.choice(["Finn", "Nell", "Tavi", "Bo"])
    mate_type = args.mate_type or rng.choice(["young sailor", "seal", "monkey", "cat"])
    parrot = args.parrot or rng.choice(["Pip", "Jolly", "Feather"])
    shutter = args.shutter or rng.choice(
        ["historic shutter", "old historic shutter", "historic harbor shutter"]
    )
    setting = args.setting or rng.choice(
        ["Blackfin Harbor", "Whispering Cape", "Cannonball Cove", "Pearl Lantern"]
    )
    weather = args.weather or rng.choice(
        ["a brisk sea wind", "a silver fog", "a warm island breeze", "a restless tide"]
    )
    return StoryParams(
        captain=captain,
        captain_type=captain_type,
        mate=mate,
        mate_type=mate_type,
        parrot=parrot,
        shutter=shutter,
        setting=setting,
        weather=weather,
        scenario_index=rng.randrange(len(SCENARIOS)),
        detail_variant=rng.randrange(10000),
    )


def tell(params: StoryParams) -> World:
    scenario = SCENARIOS[params.scenario_index % len(SCENARIOS)]
    place = params.setting or scenario["place"]
    world = World(Setting(place=place, weather=params.weather))

    captain = world.add(
        Entity("captain", "person", params.captain_type, params.captain)
    )
    mate = world.add(Entity("mate", "person", params.mate_type, params.mate))
    parrot = world.add(Entity("parrot", "animal", "parrot", params.parrot))
    shutter = world.add(
        Entity("shutter", "thing", "historic shutter", params.shutter)
    )
    rope = world.add(Entity("rope", "thing", "rope", "the strong rope"))

    world.facts.update(
        captain=captain,
        mate=mate,
        parrot=parrot,
        shutter=shutter,
        rope=rope,
        scenario=scenario,
    )

    captain.memes["trust"] = 1.0
    mate.memes["trust"] = 1.0
    parrot.memes["joy"] = 1.0

    opening = OPENINGS[params.detail_variant % len(OPENINGS)]
    world.say(
        f"{opening}, {captain.label} the {captain.type} sailed into {place} with "
        f"{mate.label} the {mate.type} and {parrot.label} the parrot."
    )
    world.say(
        f"Their mission was to {scenario['mission']}. The {params.shutter} guarded "
        f"something important, and the {world.setting.weather} made the work urgent."
    )
    world.para()

    captain.memes["worry"] = 1.0
    shutter.meters["distance"] = 1.0
    world.say(
        f"When they reached the tower, {scenario['obstacle']} "
        f"{captain.label} studied the blocked way while {mate.label} held the rope."
    )
    world.say(
        f'"We must get through before the tide changes," {captain.label} said. '
        f'"Then let us solve it together," {mate.label} replied.'
    )
    world.para()

    mate.memes["courage"] = 1.0
    world.say(scenario["wrong_turn"])
    world.say(
        f'{parrot.label} squawked, "Look closer, shipmates!" '
        f"{scenario['clue']}"
    )
    world.say(
        f'"I have one idea," {mate.label} said. "{scenario["line"]}" '
        f"{captain.label} listened instead of ordering everyone to pull."
    )
    world.say(scenario["method"])
    world.para()

    shutter.meters["strength"] = 1.0
    shutter.meters["safety"] = 1.0
    shutter.meters["readiness"] = 1.0
    captain.memes["relief"] = 1.0
    mate.memes["joy"] = 1.0
    parrot.memes["joy"] = 2.0

    world.say(scenario["result"])
    world.say(
        f'"We did it because every crew member brought a useful thought," '
        f"{captain.label} said. {mate.label} grinned, and {parrot.label} "
        f"flapped around the open window."
    )
    world.say(
        f"The friends understood that {scenario['lesson']}. "
        f"Together they had turned a stubborn obstacle into a safe passage."
    )
    world.say(f"By sunset, {scenario['image']}.")
    world.log(f"scenario={params.scenario_index % len(SCENARIOS)}")
    world.log("friendship=shared_plan")
    world.log("problem_solved=historic_shutter_ready")
    return world


def generation_prompts(world: World) -> list[str]:
    scenario = world.facts["scenario"]
    captain: Entity = world.facts["captain"]
    mate: Entity = world.facts["mate"]
    shutter: Entity = world.facts["shutter"]
    return [
        f"Write a child-friendly Pirate Tale about {captain.label} and {mate.label} solving a problem together.",
        f"Tell a friendship story in which the {shutter.label} creates a difficult problem at sea.",
        f"Write a Pirate Tale that includes a historic shutter, a clever clue, teamwork, and a safe ending.",
        f"Show how {captain.label} changes plans after listening to {mate.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario = world.facts["scenario"]
    captain: Entity = world.facts["captain"]
    mate: Entity = world.facts["mate"]
    parrot: Entity = world.facts["parrot"]
    shutter: Entity = world.facts["shutter"]
    return [
        QAItem(
            question=f"What mission did {captain.label} and {mate.label} have?",
            answer=f"They had to {scenario['mission']} with the {shutter.label}.",
        ),
        QAItem(
            question=f"What made the problem difficult?",
            answer=f"{scenario['obstacle']} The difficulty made the crew search for a safer plan.",
        ),
        QAItem(
            question=f"What clue did {parrot.label} or the crew notice?",
            answer=f"{scenario['clue']} The clue helped the friends choose an action based on evidence.",
        ),
        QAItem(
            question=f"How did the friends solve the shutter problem?",
            answer=f"{scenario['method']} Their shared method allowed the {shutter.label} to work safely.",
        ),
        QAItem(
            question=f"What did the crew learn about friendship?",
            answer=f"They learned that {scenario['lesson']}. Listening and sharing ideas helped everyone succeed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a movable cover for a window or opening. It can block wind, light, rain, or danger.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means important in history or connected with the past.",
        ),
        QAItem(
            question="Why is teamwork useful for problem solving?",
            answer="Teamwork is useful because different friends can notice different clues, suggest different plans, and help carry out a safer solution.",
        ),
        QAItem(
            question="What does a pirate crew do?",
            answer="A pirate crew is a group of sailors who work together aboard a ship. In a gentle story, they can explore, help one another, and solve problems.",
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
    lines.extend(f"event: {event}" for event in world.trace_log)
    return "\n".join(lines)


ASP_RULES = r"""
entity(captain).
entity(mate).
entity(parrot).
entity(shutter).

observed_clue :- clue_found.
shared_plan :- listened, suggested.
shutter_safe :- shared_plan, shutter_repaired.
friendship_success :- shutter_safe, helped_each_other.
#show observed_clue/0.
#show shared_plan/0.
#show shutter_safe/0.
#show friendship_success/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("clue_found"),
            asp.fact("listened"),
            asp.fact("suggested"),
            asp.fact("shutter_repaired"),
            asp.fact("helped_each_other"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    program = asp_program(
        "#show observed_clue/0. #show shared_plan/0. "
        "#show shutter_safe/0. #show friendship_success/0."
    )
    model = asp.one_model(program)
    found = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {
        "observed_clue/0",
        "shared_plan/0",
        "shutter_safe/0",
        "friendship_success/0",
    }
    if found != expected:
        print(f"MISMATCH: {sorted(found)} != {sorted(expected)}")
        return 1

    params = StoryParams(
        captain="Captain Mira",
        captain_type="human",
        mate="Finn",
        mate_type="seal",
        parrot="Pip",
        shutter="historic shutter",
        setting="Blackfin Harbor",
        weather="a brisk sea wind",
    )
    sample = generate(params)
    required = ["historic shutter", "together", "solved"]
    lowered = sample.story.lower()
    if not all(word in lowered for word in required):
        print("MISMATCH: generated story exercise failed.")
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
        captain="Captain Mira",
        captain_type="human",
        mate="Finn",
        mate_type="seal",
        parrot="Pip",
        shutter="historic shutter",
        setting="Blackfin Harbor",
        weather="a brisk sea wind",
        scenario_index=0,
    ),
    StoryParams(
        captain="Captain Flint",
        captain_type="otter",
        mate="Nell",
        mate_type="monkey",
        parrot="Jolly",
        shutter="old historic shutter",
        setting="Whispering Cape",
        weather="a silver fog",
        scenario_index=1,
    ),
    StoryParams(
        captain="Captain Rosa",
        captain_type="fox",
        mate="Tavi",
        mate_type="cat",
        parrot="Feather",
        shutter="historic harbor shutter",
        setting="Cannonball Cove",
        weather="a restless tide",
        scenario_index=2,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show observed_clue/0. #show shared_plan/0. "
                "#show shutter_safe/0. #show friendship_success/0."
            )
        )
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show observed_clue/0. #show shared_plan/0. "
                "#show shutter_safe/0. #show friendship_success/0."
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

    if not samples:
        raise StoryError("No story could be generated from the requested options.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        return

    for index, sample in enumerate(samples):
        header = (
            f"### variant {index + 1}"
            if len(samples) > 1 and not args.all
            else ""
        )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
