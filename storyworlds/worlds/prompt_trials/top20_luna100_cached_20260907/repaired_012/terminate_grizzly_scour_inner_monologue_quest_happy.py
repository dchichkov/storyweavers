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
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class City:
    name: str
    danger: float = 0.0
    signal_strength: float = 0.0
    shield_active: bool = False
    threat_ended: bool = False
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    partner_name: str
    city_name: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nova", "Zara", "Theo", "Pip", "Kira", "Jax"]
CITY_NAMES = ["Bright Harbor", "Starfall City", "Moonbridge", "Sunbeam Heights"]

ARCS = [
    {
        "key": "grizzly_signal",
        "premise": [
            "In {city}, superhero {hero} watched over the rooftops while helper {partner} tuned a little rescue radio. The moon shone on every quiet street.",
            "{hero} and {partner} began their evening patrol above {city}. They carried a silver signal lamp in case anyone needed help.",
        ],
        "problem": [
            "A giant grizzly-shaped robot stomped into the power station and swallowed the city's safety signal. If its wild gears kept turning, the signal would vanish before morning.",
            "The town's warning beacon flickered as a metal grizzly guarded the power station. Its noisy paws scattered the signal through the streets.",
        ],
        "inner": [
            "{hero} thought, \"I could blast the grizzly away, but frightened machines may stomp harder. I need to understand the noise before I act.\"",
            "Inside, {hero} wondered, \"Being strong is not enough. If I scour the grizzly's signal for a gentle pattern, I may find a safer answer.\"",
        ],
        "dialogue": [
            "\"Should we charge?\" asked {partner}. \"Not yet,\" said {hero}. \"Let's listen for the signal hidden under the grizzly's growl.\"",
            "\"The robot looks scary,\" said {partner}. {hero} answered, \"Then we will be brave and careful together.\"",
        ],
        "turn": [
            "{hero} used a small tuning beam to scour the robot's radio noise. Beneath the growl was a lonely beep repeating three times.",
            "The pair watched instead of rushing. The grizzly robot was not hunting anyone; it was searching for the signal that had guided it home.",
        ],
        "action": [
            "{hero} sent three soft flashes from the silver lamp. {partner} matched each flash on the rescue radio, and the robot's gears slowed.",
            "{partner} played the hidden three-beep pattern while {hero} opened a clear path to the power station. The grizzly followed the sound away from the wires.",
        ],
        "resolution": [
            "The robot sat beside the station and lowered its heavy head. It had lost its way, so {hero} helped it find the old mountain beacon. The city signal returned.",
            "The grizzly's red eyes changed to a warm gold. The threat was over, and the power station hummed safely again.",
        ],
        "ending": [
            "At sunrise, children waved as the friendly grizzly carried a basket of apples toward the mountain, while {hero} and {partner} smiled above the bright city.",
            "The rescue lamp glowed beside the restored beacon, and the grizzly's gentle footsteps became a happy rhythm in the morning.",
        ],
        "problem_fact": "a lost grizzly-shaped robot threatened the city's safety signal",
        "clue_fact": "careful listening found a three-beep signal beneath the robot's growl",
        "action_fact": "the heroes repeated the hidden signal with light and radio",
        "outcome_fact": "the robot became friendly and the city signal was restored",
    },
    {
        "key": "scour_cloud",
        "premise": [
            "{hero} and {partner} patrolled {city} in bright capes, looking for small troubles that needed big-hearted help.",
            "Above {city}, {hero} flew beside {partner}'s glider. Their quest was to keep every neighborhood safe before bedtime.",
        ],
        "problem": [
            "A dark cloud of runaway dust covered the central park. It began to scour the streets, hiding signs, nests, and the path home.",
            "The park's clean-up machine had gone wild, sweeping everything into a spinning gray cloud. Soon the cloud would scour the whole city.",
        ],
        "inner": [
            "{hero} thought, \"If I push the cloud harder, I may spread it. I need a calm plan that protects the small things below.\"",
            "A worried thought fluttered through {hero}'s mind: \"A hero does not only defeat danger. A hero notices who might be hurt by the rescue.\"",
        ],
        "dialogue": [
            "\"I can blow it away,\" said {hero}. \"But first, what is it carrying?\" asked {partner}. \"Good question,\" said {hero}.",
            "\"The birds are trapped!\" cried {partner}. {hero} replied, \"Then our first move is to make them a safe path.\"",
        ],
        "turn": [
            "They saw seeds and tiny nests spinning inside the cloud. The machine was following a broken street-cleaning map, not trying to hurt anyone.",
            "{partner} spotted a yellow arrow under the dust. It pointed toward a forgotten garden where the machine had been meant to gather leaves.",
        ],
        "action": [
            "{hero} lifted the nests on a gentle cushion of air while {partner} reset the map. The cloud curled toward the empty garden instead of the homes.",
            "{partner} marked the garden with bright lights. {hero} guided the dust stream slowly, leaving clean sidewalks and safe branches behind.",
        ],
        "resolution": [
            "The cloud settled into a neat pile of leaves. The machine beeped happily, and the park's paths appeared again.",
            "The runaway sweeper stopped beside the garden. No nest was harmed, and the city breathed clean air once more.",
        ],
        "ending": [
            "Birds returned to the restored trees as {hero} and {partner} shared a victory snack beneath a clear blue sky.",
            "The park sign shone through the last sparkle of dust, promising a happy place for everyone.",
        ],
        "problem_fact": "a runaway dust cloud was scouring the park and hiding its safe paths",
        "clue_fact": "the heroes discovered that the machine was following a broken garden map",
        "action_fact": "they protected the nests and guided the dust toward the leaf garden",
        "outcome_fact": "the park was clean and safe without harming the birds",
    },
    {
        "key": "terminate_alarm",
        "premise": [
            "At dusk, {hero} and {partner} began a quest through {city} after the moon alarm rang from the tallest tower.",
            "{hero} zipped across {city} with {partner} close behind. Their superhero quest was to find why every friendly streetlight had started blinking red.",
        ],
        "problem": [
            "A frightened alarm system announced that every machine in the city must terminate its work. Trains stopped, doors locked, and people could not reach home.",
            "The tower computer had mistaken a harmless meteor for a danger signal. Its loud command to terminate all city systems spread from light to light.",
        ],
        "inner": [
            "{hero} told themself, \"I must not smash the tower. The command may be confused, and people need the systems I save.\"",
            "In {hero}'s mind came a steady thought: \"First protect people, then find the mistake, then terminate only the false alarm.\"",
        ],
        "dialogue": [
            "\"Should I pull the main lever?\" asked {partner}. \"Only after we know what it controls,\" said {hero}. \"We can solve this safely.\"",
            "\"The lights are telling us something,\" said {partner}. {hero} nodded. \"Then we will read their pattern instead of fighting it.\"",
        ],
        "turn": [
            "{partner} noticed that the red lights blinked in the same rhythm as the meteor's reflection. The tower was scared by its own echo.",
            "{hero} used a visor to scour the alarm's records. The newest entry was not a threat at all; it was a bright kite reflecting moonlight.",
        ],
        "action": [
            "{hero} sent a gentle cancel code while {partner} covered the tower window. The false reflection disappeared, and the alarm command terminated.",
            "{partner} lowered the shiny kite from the tower roof. {hero} replaced the wrong warning with a clear message: ALL SAFE.",
        ],
        "resolution": [
            "The trains rolled again, doors opened, and families reached home. The tower changed its red lights to welcoming gold.",
            "The false alarm ended without a broken wire. The city systems restarted one by one, and everyone cheered for the careful heroes.",
        ],
        "ending": [
            "The moon alarm became a soft chime, and {hero} and {partner} watched the city sparkle like a field of stars.",
            "A happy gold light shone from the tower as the heroes flew home beneath the harmless meteor.",
        ],
        "problem_fact": "a confused tower ordered the city's machines to terminate their work",
        "clue_fact": "scanning the records revealed that a harmless reflection caused the alarm",
        "action_fact": "the heroes removed the reflection and sent a safe cancel command",
        "outcome_fact": "the false alarm ended and the city systems restarted",
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
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    raw = "|".join((params.hero_name, params.partner_name, params.city_name))
    value = int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big")
    return random.Random(value)


def tell(params: StoryParams) -> World:
    if params.hero_name == params.partner_name:
        raise StoryError("hero and partner must have different names")
    if params.city_name not in CITY_NAMES:
        raise StoryError(f"unknown city: {params.city_name}")

    rng = _rng_for(params)
    index = (params.seed if params.seed is not None else rng.randrange(len(ARCS))) % len(ARCS)
    arc = ARCS[index]
    beats = ("premise", "problem", "inner", "dialogue", "turn", "action", "resolution", "ending")
    if params.seed is None:
        chosen = {beat: rng.choice(arc[beat]) for beat in beats}
    else:
        code = (params.seed // len(ARCS)) % 256
        chosen = {beat: arc[beat][(code >> i) % len(arc[beat])] for i, beat in enumerate(beats)}

    city = City(params.city_name, danger=1.0, signal_strength=0.2)
    world = World(city)
    hero = world.add(Entity(params.hero_name, kind="character", type="superhero", label="superhero"))
    partner = world.add(Entity(params.partner_name, kind="character", type="helper", label="hero helper"))
    beacon = world.add(Entity("beacon", type="signal", label="rescue beacon"))
    grizzly = world.add(Entity("grizzly", type="machine", label="grizzly-shaped machine"))

    values = {"hero": params.hero_name, "partner": params.partner_name, "city": params.city_name}
    for i, beat in enumerate(beats):
        if i:
            world.para()
        world.say(chosen[beat].format(**values))

    hero.meters.update(bravery=1.0, attention=1.0)
    partner.meters.update(helpfulness=1.0, attention=1.0)
    hero.memes["hope"] = 1.0
    partner.memes["hope"] = 1.0
    city.danger = 0.0
    city.signal_strength = 1.0
    city.shield_active = True
    city.threat_ended = True
    city.facts = {
        "hero": hero,
        "partner": partner,
        "beacon": beacon,
        "grizzly": grizzly,
        "arc": arc["key"],
        "problem": arc["problem_fact"],
        "clue": arc["clue_fact"],
        "action": arc["action_fact"],
        "outcome": arc["outcome_fact"],
        "problem_event": chosen["problem"].format(**values),
        "turn_event": chosen["turn"].format(**values),
        "action_event": chosen["action"].format(**values),
        "resolution_event": chosen["resolution"].format(**values),
    }
    return world


def generate_prompts(world: World) -> list[str]:
    hero = world.city.facts["hero"].id
    partner = world.city.facts["partner"].id
    return [
        "Write a child-friendly superhero quest involving a grizzly, a careful search, and a happy ending.",
        f"Tell a superhero story about {hero} and {partner} using an inner monologue before they act.",
        "Write a story where a hero must scour a confusing danger, terminate a false threat, and protect everyone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.city.facts
    hero = f["hero"].id
    return [
        QAItem(
            question=f"What quest did {hero} face?",
            answer=f"{hero} faced this problem: {f['problem_event']}",
        ),
        QAItem(
            question="What clue changed the heroes' plan?",
            answer=f["turn_event"],
        ),
        QAItem(
            question="How did the heroes solve the danger?",
            answer=f"{f['action_event']} {f['resolution_event']}",
        ),
        QAItem(
            question="How do we know the ending was happy?",
            answer=f["outcome"] + ". The city was safe, and the heroes ended their quest with everyone protected.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does terminate mean?",
            answer="Terminate means to stop or bring something to an end.",
        ),
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large brown bear. In this story, the grizzly shape belongs to a machine, not a real bear.",
        ),
        QAItem(
            question="What does scour mean?",
            answer="To scour means to search an area carefully or clean it by rubbing and looking closely.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thought, shown so readers can understand what the character is deciding.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id:10} ({entity.type:10}) {' '.join(details)}")
    lines.extend(
        [
            f"  city.danger={world.city.danger}",
            f"  city.signal_strength={world.city.signal_strength}",
            f"  city.shield_active={world.city.shield_active}",
            f"  city.threat_ended={world.city.threat_ended}",
        ]
    )
    return "\n".join(lines)


ASP_RULES = r"""
valid_story :-
    has_seed(terminate),
    has_seed(grizzly),
    has_seed(scour),
    has_feature(inner_monologue),
    has_feature(quest),
    has_feature(happy_ending),
    style(superhero_story),
    threat_ended.
#show valid_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("has_seed", "terminate"),
            asp.fact("has_seed", "grizzly"),
            asp.fact("has_seed", "scour"),
            asp.fact("has_feature", "inner_monologue"),
            asp.fact("has_feature", "quest"),
            asp.fact("has_feature", "happy_ending"),
            asp.fact("style", "superhero_story"),
            asp.fact("threat_ended"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if any(symbol.name == "valid_story" for symbol in model):
        params = StoryParams("Luna", "Milo", "Bright Harbor", seed=17)
        sample = generate(params)
        required = ("terminate", "grizzly", "scour")
        if all(word in sample.story.lower() for word in required):
            print("OK: ASP and Python recognize the superhero quest.")
            return 0
        print("MISMATCH: generated story omitted a required seed word.")
        return 1
    print("MISMATCH: ASP twin rejected the story.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Superhero quest world with a grizzly, careful searching, and a happy ending.")
    parser.add_argument("--hero-name", choices=NAMES)
    parser.add_argument("--partner-name", choices=NAMES)
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
    choices = [name for name in NAMES if name != hero]
    partner = args.partner_name or rng.choice(choices)
    city = args.city_name or rng.choice(CITY_NAMES)
    if partner == hero:
        raise StoryError("hero and partner must have different names")
    return StoryParams(hero, partner, city)


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
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


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
        print("1 compatible superhero quest: terminate + grizzly + scour + inner monologue + happy ending")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Milo", "Bright Harbor", seed=0),
            StoryParams("Nova", "Zara", "Starfall City", seed=1),
            StoryParams("Theo", "Kira", "Moonbridge", seed=2),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
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

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
