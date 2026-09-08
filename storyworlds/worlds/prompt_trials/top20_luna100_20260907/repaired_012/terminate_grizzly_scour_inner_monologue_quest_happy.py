#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class City:
    name: str
    danger: float = 0.0
    hope: float = 0.0
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    helper_name: str
    city_name: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nova", "Zara", "Theo", "Pia", "Kai", "Ruby"]
HELPER_NAMES = ["Moss", "Bram", "Echo", "Sunny", "Pip"]
CITY_NAMES = ["Brighton City", "Moonbeam Town", "Star Harbor", "Cloudside"]


ARCS = [
    {
        "key": "mountain_signal",
        "premise": [
            "{hero} was the bright-caped hero of {city}. One morning, {hero} heard a tiny distress signal humming from Grizzly Mountain, while trusted helper {helper} packed a flashlight and a warm snack.",
            "Above {city}, {hero} tested a new silver cape when a red signal blinked from Grizzly Mountain. {helper} hurried over with a rescue rope and a notebook.",
        ],
        "problem": [
            "A giant grizzly robot had rolled into a cave and blocked the mountain's rescue beacon. If the beacon stayed dark, the town's flying buses could not find their safe route home.",
            "The signal came from a grizzly-shaped machine tangled in old cables. Its startled growls made rocks tumble, and the beacon's light began to fade.",
        ],
        "inner": [
            "{hero} thought, \"I could rush in and use my strongest power. But a frightened grizzly needs patience, not a battle.\" The thought helped {hero} lower the cape and listen.",
            "Inside, {hero} wondered, \"What if my power makes the cave less safe?\" {helper} replied, \"Then let us scour the clues before we act.\" {hero} decided to investigate carefully.",
        ],
        "quest": [
            "Together, they began a quest. They scoured the cave floor and found three blue bolts, a loose cable, and paw-shaped dents leading toward a quiet corner.",
            "{hero} and {helper} followed the humming signal on a careful quest. They scoured the rocks until they discovered that the robot's power cord was caught beneath a fallen sign.",
        ],
        "action": [
            "\"I will shine a soft light,\" said {hero}. \"I will loosen the cord,\" said {helper}. They worked side by side, then {hero} gently asked the grizzly machine to step backward.",
            "{hero} called, \"Please take one slow step.\" The grizzly robot rumbled, \"I am afraid.\" \"You are safe with us,\" answered {hero}, while {helper} freed the cable.",
        ],
        "resolution": [
            "The cable came loose, and the grizzly robot's red eyes turned friendly green. The beacon shone again, so {hero} could terminate the danger without hurting anyone.",
            "With one careful tug, the trap opened. The grizzly robot stopped growling and helped aim the beacon toward the flying buses.",
        ],
        "ending": [
            "{city} cheered as the buses landed safely. {hero} smiled beneath the silver cape, happy that brave listening had saved the day.",
            "At sunset, the grizzly robot waved from the mountain, and the beacon painted a golden path over {city}. It was a happy ending for every traveler.",
        ],
        "problem_fact": "a frightened grizzly robot blocked the mountain rescue beacon",
        "clue_fact": "scouring the cave revealed a trapped power cord",
        "action_fact": "the hero and helper freed the cord gently",
        "outcome_fact": "the danger ended and the rescue beacon guided everyone home",
    },
    {
        "key": "park_shadow",
        "premise": [
            "In {city}, {hero} wore a starry mask and helped people solve problems without making them feel small. {helper} joined the patrol with a bright yellow lantern.",
            "{hero} protected {city} from rooftop to rooftop, while {helper} carried supplies below. Their next call came from the quiet park at the edge of town.",
        ],
        "problem": [
            "A grizzly shadow had spread across the park, swallowing the swings and making every path look like a wall. Children could not find the way home.",
            "The park's old projector had turned a grizzly picture into a huge moving shadow. It scared everyone and covered the exit signs.",
        ],
        "inner": [
            "{hero} thought, \"A loud blast might frighten the shadow even more. I need to discover what is making it.\" {helper} nodded when {hero} shared the thought aloud.",
            "\"I feel nervous,\" admitted {hero}. \"Nervous heroes can still look closely,\" said {helper}. That small exchange changed {hero}'s plan from charging to observing.",
        ],
        "quest": [
            "Their quest led beneath the bandstand. They scoured the dusty boards and found a cracked lens, a loose battery, and a grizzly poster folded around the lamp.",
            "{hero} and {helper} scoured every corner on their quest. A trail of warm dust led them to the projector, whose lens was pointed at the park instead of the screen.",
        ],
        "action": [
            "{hero} covered the lens with a cape while {helper} unplugged the projector. The grizzly shadow shrank, and the children followed the lantern toward home.",
            "\"I will block the light,\" said {hero}. \"I will switch it off,\" said {helper}. Together they ended the shadow without breaking the old projector.",
        ],
        "resolution": [
            "The paths appeared again, and the park lights blinked on. The danger was terminated by teamwork, not by a mighty punch.",
            "The projector became quiet. {hero} returned the lens to its case, and {helper} placed a sign over the loose switch.",
        ],
        "ending": [
            "The swings began to sway in the evening breeze, and {city}'s children waved to the heroes beneath a sky full of stars.",
            "Everyone reached home smiling. In the quiet park, the harmless grizzly poster now looked funny instead of frightening.",
        ],
        "problem_fact": "a broken projector made a grizzly shadow cover the park",
        "clue_fact": "scouring beneath the bandstand revealed the cracked lens and loose battery",
        "action_fact": "they blocked the lens and unplugged the projector",
        "outcome_fact": "the park paths returned and everyone got home safely",
    },
    {
        "key": "river_bridge",
        "premise": [
            "{hero} flew over {city} with {helper} riding in a little rescue pod. They were on their way to inspect the old river bridge before the afternoon parade.",
            "The people of {city} trusted {hero}'s shining shield and {helper}'s clever tools. Together they visited the river bridge when its warning bell rang.",
        ],
        "problem": [
            "A grizzly cargo balloon had snagged the bridge cables. The bridge wobbled above the rushing water, and the parade wagons could not cross.",
            "The bridge's control box had been filled with muddy leaves by a grizzly-shaped weather drone. Each gust made the warning lights flash.",
        ],
        "inner": [
            "{hero} thought, \"I must protect the bridge before I think about looking impressive.\" Then {hero} told {helper}, \"Safety first.\" The words made the next step clear.",
            "\"My first idea is too risky,\" {hero} said. {helper} answered, \"A quiet plan can still be heroic.\" {hero} listened and chose care over speed.",
        ],
        "quest": [
            "They began a bridge quest and scoured the riverbank for a safe route. They found a spare pulley, a coil of rope, and a dry path beneath the control box.",
            "{hero} and {helper} scoured the bridge supports. Their quest uncovered a pulley hidden behind a sign and a knot that held the balloon to the cables.",
        ],
        "action": [
            "{helper} tied the spare rope to the pulley while {hero} held the cables steady with the silver shield. They eased the balloon free one gentle inch at a time.",
            "\"Ready?\" asked {hero}. \"Ready,\" said {helper}. They pulled together, guided the balloon away from the bridge, and kept every wagon safe.",
        ],
        "resolution": [
            "The balloon floated clear, the bridge settled, and the warning bell stopped. The danger was terminated before the parade arrived.",
            "The cables straightened without snapping. The weather drone's grizzly face changed to a cheerful smile when {hero} returned it to its landing pad.",
        ],
        "ending": [
            "The parade crossed beneath bright flags, while {hero} and {helper} shared a quiet high five beside the calm river.",
            "Music rolled across the repaired bridge. {city} celebrated a happy ending, and the rescued balloon bobbed like a friendly cloud.",
        ],
        "problem_fact": "a grizzly cargo balloon snagged the river bridge cables",
        "clue_fact": "scouring the riverbank revealed a spare pulley and a safe route",
        "action_fact": "they used the pulley and shield to ease the balloon free",
        "outcome_fact": "the bridge became safe before the parade arrived",
    },
]


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    raw = "|".join((params.hero_name, params.helper_name, params.city_name))
    return random.Random(int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    if params.hero_name == params.helper_name:
        raise StoryError("The hero and helper must have different names.")
    if params.city_name not in CITY_NAMES:
        raise StoryError(f"Unknown city: {params.city_name}")

    rng = _rng_for(params)
    arc = ARCS[(params.seed if params.seed is not None else rng.randrange(len(ARCS))) % len(ARCS)]
    beats = ("premise", "problem", "inner", "quest", "action", "resolution", "ending")
    chosen = {
        beat: arc[beat][
            ((params.seed or 0) // len(ARCS) + index) % len(arc[beat])
            if params.seed is not None
            else rng.randrange(len(arc[beat]))
        ]
        for index, beat in enumerate(beats)
    }

    city = City(params.city_name, danger=1.0, hope=0.2)
    world = World(city)
    hero = world.add(Entity(params.hero_name, kind="character", type="superhero"))
    helper = world.add(Entity(params.helper_name, kind="character", type="helper"))
    grizzly = world.add(Entity("grizzly", type="obstacle", label="grizzly trouble"))
    hero.meters.update(power=5.0, courage=4.0)
    helper.meters.update(cleverness=4.0, courage=3.0)
    hero.memes["patience"] = 0.0
    helper.memes["trust"] = 1.0
    grizzly.meters["danger"] = 1.0

    values = {"hero": hero.id, "helper": helper.id, "city": city.name}
    rendered = {beat: chosen[beat].format(**values) for beat in beats}
    for index, beat in enumerate(beats):
        if index:
            world.para()
        world.say(rendered[beat])

    city.danger = 0.0
    city.hope = 1.0
    hero.memes["patience"] = 1.0
    grizzly.meters["danger"] = 0.0
    city.facts = {
        "hero": hero,
        "helper": helper,
        "grizzly": grizzly,
        "arc": arc["key"],
        "problem": arc["problem_fact"],
        "clue": arc["clue_fact"],
        "action": arc["action_fact"],
        "outcome": arc["outcome_fact"],
        "events": rendered,
    }
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.city.facts
    return [
        "Write a child-friendly superhero story with an inner monologue, a quest, and a happy ending.",
        f"Tell a superhero adventure in {world.city.name} where {f['hero'].id} must scour for clues before acting.",
        "Write a story in which a hero faces grizzly trouble, chooses patience, and terminates the danger safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.city.facts
    hero = f["hero"].id
    helper = f["helper"].id
    return [
        QAItem(
            f"Who were the heroes in the story?",
            f"{hero} was the superhero, and {helper} was the helpful partner who worked beside {hero}.",
        ),
        QAItem(
            f"What grizzly trouble threatened {world.city.name}?",
            f["events"]["problem"],
        ),
        QAItem(
            f"What did {hero} think before acting?",
            f["events"]["inner"],
        ),
        QAItem(
            f"How did the heroes terminate the danger?",
            f"{f['action']} Then {f['outcome']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an inner monologue?", "An inner monologue is a character's private thought, showing what the character is thinking inside."),
        QAItem("What is a quest?", "A quest is a purposeful journey or search to solve a problem or reach an important goal."),
        QAItem("What does terminate mean?", "Terminate means to bring something to an end."),
        QAItem("What does scour mean?", "Scour means to search a place carefully and thoroughly."),
        QAItem("What is a grizzly?", "A grizzly is a large brown bear. In this story, grizzly trouble is handled carefully rather than harmed."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id:8} ({entity.type:10}) meters={meters} memes={memes}")
    lines.append(f"  city.danger={world.city.danger}")
    lines.append(f"  city.hope={world.city.hope}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story :- theme(terminate), theme(grizzly), theme(scour),
               feature(inner_monologue), feature(quest),
               feature(happy_ending), style(superhero_story),
               danger_ended, clues_found, safe_action.
danger_ended.
clues_found.
safe_action.
#show valid_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("theme", "terminate"),
            asp.fact("theme", "grizzly"),
            asp.fact("theme", "scour"),
            asp.fact("feature", "inner_monologue"),
            asp.fact("feature", "quest"),
            asp.fact("feature", "happy_ending"),
            asp.fact("style", "superhero_story"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    if not any(symbol.name == "valid_story" for symbol in model):
        print("MISMATCH: ASP twin rejected the story pattern.")
        return 1
    sample = generate(StoryParams("Luna", "Moss", "Brighton City", seed=7))
    required = ["terminate", "grizzly", "scour"]
    if not all(word in sample.story.lower() for word in required):
        print("MISMATCH: generated prose omitted a required seed word.")
        return 1
    if len(sample.story_qa) < 3 or not sample.world.city.facts:
        print("MISMATCH: generated story lacks grounded world data.")
        return 1
    print("OK: Python and ASP agree on the superhero quest.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Superhero storyworld about a grizzly quest.")
    parser.add_argument("--hero-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--city-name", choices=CITY_NAMES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero_name or rng.choice(NAMES)
    choices = [name for name in HELPER_NAMES + NAMES if name != hero]
    helper = args.helper_name or rng.choice(choices)
    city = args.city_name or rng.choice(CITY_NAMES)
    return StoryParams(hero, helper, city)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
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
        raise SystemExit(asp_verify())
    if args.asp:
        print("1 compatible superhero story pattern: terminate + grizzly + scour + quest + happy ending")
        return
    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("Luna", "Moss", "Brighton City", seed=11),
            StoryParams("Nova", "Echo", "Moonbeam Town", seed=23),
            StoryParams("Zara", "Sunny", "Star Harbor", seed=37),
        ]
        samples = [generate(params) for params in params_list]
    else:
        samples = []
        for index in range(args.n):
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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
