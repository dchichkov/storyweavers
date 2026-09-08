#!/usr/bin/env python3
"""
A child-facing superhero storyworld about a grizzly rescue, a dangerous signal,
and a quest to terminate a runaway machine.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    hero_type: str = "girl"
    bear_name: str = "Bruno"
    city_name: str = "Brightvale"
    gadget: str = "the Moonlight Beacon"


NAMES = ["Luna", "Maya", "Zara", "Theo", "Nia", "Kai", "Pip", "Ravi"]
BEARS = ["Bruno", "Cocoa", "Maple", "Grizzly", "Bramble"]
CITIES = ["Brightvale", "Sunridge", "Star Harbor", "Pinecrest"]
GADGETS = ["the Moonlight Beacon", "the Silver Signal", "the Sky Bell", "the Comet Lamp"]

INCIDENTS = [
    {
        "place": "the old mountain tunnel",
        "threat": "a snow-clearing robot that had forgotten how to stop",
        "clue": "the robot paused whenever it heard a low, warm sound",
        "action": "hummed a steady note beside the emergency panel",
        "rescue": "the grizzly led the lost hikers out through a side passage",
        "ending": "the tunnel glittered safely while the rescued hikers cheered",
        "lesson": "A brave hero listens before rushing into danger",
    },
    {
        "place": "the forest power station",
        "threat": "a storm machine spinning sparks over the pine trees",
        "clue": "its control lights formed the same pattern as the grizzly's paw prints",
        "action": "scoured the muddy ground for the matching paw-print pattern",
        "rescue": "the grizzly pulled a fallen gate away from the trapped campers",
        "ending": "lanterns glowed around a warm campfire beneath a clear sky",
        "lesson": "Careful observation can turn a frightening puzzle into a useful map",
    },
    {
        "place": "the river bridge",
        "threat": "a runaway rescue drone shouting the wrong directions",
        "clue": "the correct path was marked by three blue feathers",
        "action": "scoured the bridge stones until three blue feathers appeared beside a hatch",
        "rescue": "the grizzly carried a little boat rope to the stranded family",
        "ending": "the family crossed safely as the river sparkled below",
        "lesson": "A small clue can guide a large rescue",
    },
    {
        "place": "the crystal quarry",
        "threat": "a drilling machine shaking the valley",
        "clue": "the safest switch was hidden beneath a soft patch of moss",
        "action": "scoured the rocks gently instead of smashing them apart",
        "rescue": "the grizzly guarded the quiet path while miners returned home",
        "ending": "crystals shone like stars around the peaceful quarry",
        "lesson": "Gentle hands can solve problems that force would only worsen",
    },
]

MODES = [
    ("The city alarm rang just as the moon rose.", "Luna's first thought was bold, but her second thought was wiser."),
    ("Everyone in Brightvale knew the silver streak in the sky meant Luna was nearby.", "This time, courage meant making a careful plan."),
    ("A quiet evening turned into a superhero quest.", "The strange clue mattered more than the loud danger."),
]


def _setup(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(params.hero_name, "character", params.hero_type, params.hero_name))
    bear = world.add(Entity(params.bear_name, "character", "grizzly", params.bear_name))
    beacon = world.add(Entity("beacon", "thing", "gadget", params.gadget))
    threat = world.add(Entity("machine", "thing", "machine", "runaway machine"))
    hero.meters.update(courage=1.0, speed=1.0)
    hero.memes["worry"] = 0.0
    bear.meters["strength"] = 1.0
    bear.memes["trust"] = 0.0
    beacon.meters["light"] = 1.0
    threat.meters["danger"] = 1.0
    world.facts.update(hero=hero, bear=bear, beacon=beacon, threat=threat)


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate(
        f"{params.hero_name}|{params.bear_name}|{params.city_name}|{params.gadget}"
    ))


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    token = _token(params)
    incident = INCIDENTS[token % len(INCIDENTS)]
    mode = MODES[(token // len(INCIDENTS)) % len(MODES)]
    hero = world.facts["hero"]
    bear = world.facts["bear"]
    threat = world.facts["threat"]

    world.say(mode[0])
    world.say(
        f"{hero.label}, the superhero guardian of {params.city_name}, flew toward "
        f"{incident['place']} with {params.gadget} glowing at her side."
    )
    world.say(f"A grizzly named {bear.label} was trapped near {incident['threat']}.")

    world.para()
    world.say(f'"I must terminate that machine before anyone is hurt," {hero.label} said.')
    world.say(
        f"Inside her mind, {hero.label} thought, "
        f"I can be quick, but I must not be careless. The grizzly needs a safe path."
    )
    world.say(
        f"The machine roared, and {hero.label} nearly charged straight at it. "
        f"Then {bear.label} thumped one heavy paw against the ground."
    )
    world.say(f'"Wait for my signal," {hero.label} called. "{bear.label}, can you help me?"')
    world.say(f'"I can help if you listen," said the grizzly. "The ground is telling us something."')
    world.fired.add(("wrong_plan",))
    world.facts["hero"].memes["worry"] = 0.4

    world.para()
    world.say(
        f"The superhero began a quest to scour {incident['place']} for a safer answer. "
        f"At last, she noticed that {incident['clue']}."
    )
    world.say(f'"I know what to do now," {hero.label} said. "{bear.label}, keep everyone back."')
    world.say(
        f"The grizzly nodded and {incident['rescue']}. "
        f"While the danger moved away, {hero.label} {incident['action']}."
    )
    world.say(
        f"The clue led to the hidden control. {hero.label} pressed the blue switch, "
        "and the runaway machine slowed to a gentle hum before stopping completely."
    )
    world.fired.add(("machine_terminated",))
    threat.meters["danger"] = 0.0
    bear.memes["trust"] = 1.0

    world.para()
    world.say(f"The quest ended happily: {incident['ending']}.")
    world.say(
        f'"You saved us by listening," {bear.label} told {hero.label}. '
        f'"And you helped me find the answer," {hero.label} replied.'
    )
    world.say(f"{incident['lesson']}.")
    world.say(
        f"Under the calm moon, {hero.label} held up {params.gadget}, and the grizzly's "
        "friendly paw print shone beside it."
    )
    world.facts.update(
        params=params,
        incident=incident,
        incident_index=token % len(INCIDENTS),
        mode_index=(token // len(INCIDENTS)) % len(MODES),
        quest=True,
        happy_ending=True,
        terminated=True,
    )
    return world


def valid_story() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    return [
        f"Write a child-friendly superhero story about {p.hero_name}, a grizzly, and {incident['place']}.",
        f"Tell how {p.hero_name} scours the danger zone, listens to the grizzly, and terminates {incident['threat']}.",
        "Include inner monologue, a quest, spoken dialogue, and a happy ending that shows what changed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    return [
        QAItem(
            f"Who went on the superhero quest?",
            f"{p.hero_name} went on the quest with help from the grizzly named {p.bear_name}.",
        ),
        QAItem(
            "What danger did the hero face?",
            f"The danger was {incident['threat']} at {incident['place']}.",
        ),
        QAItem(
            "What did the hero think before acting?",
            f"The hero thought, 'I can be quick, but I must not be careless. The grizzly needs a safe path.'",
        ),
        QAItem(
            "How did the grizzly help?",
            f"The grizzly helped by {incident['rescue']}.",
        ),
        QAItem(
            "What did the hero scour for?",
            f"The hero scoured {incident['place']} and found the clue that {incident['clue']}.",
        ),
        QAItem(
            "How was the danger terminated?",
            f"The hero followed the clue to the hidden control and pressed the blue switch, which stopped the runaway machine safely.",
        ),
        QAItem(
            "What showed that the ending was happy?",
            f"{incident['ending'].capitalize()} The hero and the grizzly were safe and proud of their teamwork.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a grizzly?",
            "A grizzly is a large brown bear with strong paws and a powerful body.",
        ),
        QAItem(
            "What does terminate mean?",
            "Terminate means to bring something to an end or stop it.",
        ),
        QAItem(
            "What does scour mean?",
            "To scour means to search a place carefully and thoroughly.",
        ),
        QAItem(
            "What is a superhero?",
            "A superhero is a brave helper who uses special abilities, courage, or cleverness to protect others.",
        ),
    ]


ASP_RULES = r"""
confused(S) :- grizzly(S), runaway_machine(S), quest(S).
safe_rescue(S) :- confused(S), clue_found(S), machine_terminated(S).
happy_ending(S) :- safe_rescue(S), people_safe(S).
valid_story(S) :- happy_ending(S).
"""


def asp_facts() -> str:
    import asp
    facts = [
        asp.fact("grizzly", "story1"),
        asp.fact("runaway_machine", "story1"),
        asp.fact("quest", "story1"),
        asp.fact("clue_found", "story1"),
        asp.fact("machine_terminated", "story1"),
        asp.fact("people_safe", "story1"),
    ]
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    actual = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if actual == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(actual))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld about a grizzly, a quest, and a terminated machine."
    )
    parser.add_argument("--hero-name", choices=NAMES)
    parser.add_argument("--bear-name", choices=BEARS)
    parser.add_argument("--city-name", choices=CITIES)
    parser.add_argument("--gadget", choices=GADGETS)
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
    hero = args.hero_name or rng.choice(NAMES)
    bear = args.bear_name or rng.choice(BEARS)
    city = args.city_name or rng.choice(CITIES)
    gadget = args.gadget or rng.choice(GADGETS)
    return StoryParams(
        seed=None,
        hero_name=hero,
        bear_name=bear,
        city_name=city,
        gadget=gadget,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {entity.id:10} ({entity.kind:9}) {' '.join(details)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(hero_name="Luna", bear_name="Bruno", city_name="Brightvale", gadget="the Moonlight Beacon"),
    StoryParams(hero_name="Maya", bear_name="Maple", city_name="Pinecrest", gadget="the Silver Signal"),
    StoryParams(hero_name="Theo", bear_name="Cocoa", city_name="Sunridge", gadget="the Sky Bell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
