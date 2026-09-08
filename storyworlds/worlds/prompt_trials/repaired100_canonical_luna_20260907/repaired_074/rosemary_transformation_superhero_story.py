#!/usr/bin/env python3
"""
A small superhero storyworld about Rosemary and a transformation.

Rosemary is a quiet garden helper who discovers that courage can transform
ordinary care into heroic action.
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

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("danger", "hope", "damage", "energy", "fear", "care"):
            self.meters.setdefault(key, 0.0)
        for key in ("bravery", "trust", "identity", "helpfulness"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    hero_name: str = "Rosemary"
    town: str = "Sunnyvale"
    danger: str = "a storm-powered machine"
    transformation: str = "a bright green superhero"
    seed: Optional[int] = None
    variation: int = 0


@dataclass(frozen=True)
class Threat:
    key: str
    name: str
    place: str
    danger_line: str
    rescue: str
    consequence: str
    ending: str


THREATS = [
    Threat(
        "storm_machine",
        "the Thunder Tumbler",
        "the town square",
        "Its spinning copper arms were pulling every lamp toward a wild blue storm.",
        "guide the machine's loose power cable into the old stone fountain",
        "The machine groaned, slowed, and poured its extra charge harmlessly into the water.",
        "The square glittered with safe little lights, and everyone cheered for the hero who had once been only a garden helper.",
    ),
    Threat(
        "bridge",
        "the rattling Sky Bridge",
        "the river crossing",
        "Its last wooden plank had snapped while a school wagon waited on the shaking bridge.",
        "tie a strong vine around the bridge post and lead the wagon back one careful step at a time",
        "The vine held firm, and the wagon rolled safely onto solid ground.",
        "Children waved from the riverbank as green leaves curled around the repaired bridge.",
    ),
    Threat(
        "fire",
        "the runaway fire cart",
        "the market lane",
        "Sparks were racing beneath the cart, and its water barrel had tipped into the dust.",
        "grow a cool wall of leafy vines between the sparks and the market stalls",
        "The vines drank the heat until the sparks faded into harmless smoke.",
        "The market smelled of fresh herbs instead of fire, and Rosemary's green cape fluttered in the warm breeze.",
    ),
]


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def paragraph(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def setup_world(params: StoryParams, threat: Threat) -> World:
    world = World(params)
    world.add(Entity("rosemary", "hero", params.hero_name, "garden"))
    world.add(Entity("mayor", "helper", "Mayor Fern", threat.place))
    world.add(Entity("threat", "danger", threat.name, threat.place))
    world.entities["rosemary"].meters["hope"] = 2
    world.entities["rosemary"].meters["fear"] = 1
    world.entities["rosemary"].memes["identity"] = 1
    world.entities["threat"].meters["danger"] = 4
    world.entities["threat"].meters["energy"] = 3
    return world


def tell_story(world: World, threat: Threat) -> None:
    hero = world.entities["rosemary"]
    mayor = world.entities["mayor"]

    world.say(
        f"In {world.params.town}, Rosemary cared for a little garden behind the library."
    )
    world.say(
        "She watered the seedlings, tied up drooping stems, and believed that small acts of care mattered."
    )
    world.say(
        f"One afternoon, {threat.danger_line}"
    )
    world.say(
        f'"Someone must help!" cried {mayor.label}. "But I am only one mayor!"'
    )
    world.say(
        f'Rosemary took a breath. "I am only Rosemary," she said, "but I can still try."'
    )

    world.paragraph()
    world.say(
        "A warm wind lifted the rosemary leaves around her. Their silver-green scent curled through the air like a shining ribbon."
    )
    world.say(
        "The little leaves became a bright green cape, sturdy vine-bracers, and boots that could grip stone."
    )
    world.say(
        f"Rosemary had transformed into Rosemary the Green Guardian, a superhero powered by patient care."
    )
    hero.meters["fear"] = 0
    hero.meters["energy"] = 4
    hero.meters["hope"] = 5
    hero.memes["bravery"] = 3
    hero.memes["identity"] = 2
    hero.memes["helpfulness"] = 3
    world.say(f'"Your new look is amazing!" said {mayor.label}. "What will you do?"')
    world.say(
        f'"I will not fight the danger with anger," said Rosemary. "I will guide it somewhere safe."'
    )

    world.paragraph()
    world.say(
        f"Rosemary hurried to {threat.place}. {threat.danger_line}"
    )
    world.say(
        f"She used her vine-bracers to {threat.rescue}."
    )
    hero.meters["care"] = 4
    hero.memes["trust"] = 2
    world.entities["threat"].meters["danger"] = 0
    world.entities["threat"].meters["energy"] = 0
    world.entities["threat"].meters["damage"] = 0
    world.say(threat.consequence)
    world.say(
        f'"You saved us!" said {mayor.label}. "Are you a superhero forever now?"'
    )
    world.say(
        '"A superhero is someone who notices a problem and helps," Rosemary answered. "Tomorrow I still have seedlings to water."'
    )

    world.paragraph()
    world.say(threat.ending)
    world.say(
        "Rosemary's transformation had changed her powers, but her caring heart had been strong all along."
    )
    world.facts.update(
        hero=hero,
        mayor=mayor,
        threat=threat,
        transformation="Rosemary transformed into Rosemary the Green Guardian.",
        rescue=threat.rescue,
        consequence=threat.consequence,
        ending=threat.ending,
    )


def story_qa(world: World) -> list[QAItem]:
    threat: Threat = world.facts["threat"]
    return [
        QAItem(
            "Who was Rosemary before she became a superhero?",
            "Rosemary was a garden helper who cared for seedlings behind the library.",
        ),
        QAItem(
            "What danger threatened the town?",
            f"{threat.name} threatened {threat.place}. {threat.danger_line}",
        ),
        QAItem(
            "How did Rosemary transform?",
            "The rosemary leaves became a bright green cape, vine-bracers, and gripping boots, transforming her into Rosemary the Green Guardian.",
        ),
        QAItem(
            "What did Rosemary decide to do with her powers?",
            f"She decided to {threat.rescue}.",
        ),
        QAItem(
            "How was the danger resolved?",
            threat.consequence,
        ),
        QAItem(
            "What did Rosemary say makes someone a superhero?",
            "Rosemary said that a superhero is someone who notices a problem and helps.",
        ),
        QAItem(
            "What changed at the end of the story?",
            threat.ending,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is rosemary?",
            "Rosemary is a fragrant herb with narrow green leaves that can be used in cooking and gardens.",
        ),
        QAItem(
            "What is a transformation?",
            "A transformation is a change from one form or condition into another.",
        ),
        QAItem(
            "What does a superhero do?",
            "A superhero uses special abilities, courage, or kindness to protect and help others.",
        ),
    ]


def generation_prompts() -> list[str]:
    return [
        "Write a child-friendly superhero story about Rosemary and a brave transformation.",
        "Tell a story in which Rosemary changes into a green superhero and uses care rather than anger to solve a danger.",
        "Create a short superhero adventure with Rosemary, a town in trouble, dialogue, transformation, and a hopeful ending.",
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a Rosemary transformation superhero story."
    )
    parser.add_argument("--hero-name", default=None)
    parser.add_argument("--town", default=None)
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
    hero_name = args.hero_name or "Rosemary"
    if hero_name.strip().lower() != "rosemary":
        raise StoryError("The hero name must be Rosemary for this storyworld.")
    town = args.town or rng.choice(["Sunnyvale", "Greenfield", "Leafside"])
    return StoryParams(
        hero_name="Rosemary",
        town=town,
        seed=args.seed,
        variation=rng.getrandbits(63),
    )


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.variation)
    threat = rng.choice(THREATS)
    world = setup_world(params, threat)
    tell_story(world, threat)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== world qa =="])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.label} [{entity.kind}] at {entity.location}: "
            f"meters={meters}, memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
hero(rosemary).
threatened(town).
transformed(rosemary, green_guardian).
uses_care(rosemary).
rescues(rosemary, town).
safe(town) :- rescued(rosemary, town), uses_care(rosemary).
#show transformed/2.
#show safe/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hero", "rosemary"),
            asp.fact("threatened", "town"),
            asp.fact("rescues", "rosemary", "town"),
            asp.fact("uses_care", "rosemary"),
        ]
    )


def asp_program(show: str = "#show transformed/2.\n#show safe/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except ImportError:
        print("ASP verification unavailable: clingo is not installed.")
        return 1
    model = asp.one_model(asp_program())
    transformed = any(
        symbol.name == "transformed"
        and len(symbol.arguments) == 2
        and str(symbol.arguments[0]) == "rosemary"
        for symbol in model
    )
    safe = any(symbol.name == "safe" for symbol in model)
    sample = generate(
        StoryParams(hero_name="Rosemary", town="Sunnyvale", variation=17)
    )
    parity = (
        "Rosemary" in sample.story
        and "transformed" in sample.story.lower()
        and "safe" in sample.story.lower()
    )
    if transformed and safe and parity:
        print("OK: Python and ASP agree that Rosemary transforms and makes the town safe.")
        return 0
    print("MISMATCH: Python and ASP superhero states disagree.")
    return 1


CURATED = [
    StoryParams("Rosemary", "Sunnyvale", variation=11),
    StoryParams("Rosemary", "Greenfield", variation=22),
    StoryParams("Rosemary", "Leafside", variation=33),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        try:
            import asp
        except ImportError:
            print("ASP mode unavailable: clingo is not installed.")
            return
        model = asp.one_model(asp_program())
        print("ASP model:")
        for symbol in model:
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            samples.append(generate(params))

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
        print(sample.story)
        if args.trace and sample.world is not None:
            print()
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
