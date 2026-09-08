#!/usr/bin/env python3
"""
A small mythic-romantic superhero storyworld.

Luna, a young sky-hero, must protect a moonlit city when the jealous
storm-spirit Vesper steals the bell that keeps night gentle. The conflict is
resolved not by overpowering Vesper, but by listening, sharing the bell's song,
and choosing trust over fear.
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
            "harmony": 0.0,
            "danger": 0.0,
        }
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "worry": 0.0,
            "courage": 0.0,
            "trust": 0.0,
            "love": 0.0,
            "relief": 0.0,
        }
    )


@dataclass
class Setting:
    place: str = "the moonlit city of Selene"
    landmark: str = "the silver observatory"
    sky: str = "a deep violet sky"


@dataclass
class StoryParams:
    hero_name: str
    hero_title: str
    beloved_name: str
    beloved_type: str
    spirit_name: str
    relic: str
    setting: str = "the moonlit city of Selene"
    scenario_index: int = 0
    detail_variant: int = 0
    seed: Optional[int] = None


SCENARIOS = [
    {
        "threat": "a storm-spirit had wrapped the city in thunder and stolen the Moonheart Bell",
        "clue": "Luna noticed that the thunder softened whenever someone spoke kindly",
        "method": "Luna and her beloved joined their voices in a calm, honest song",
        "turn": "Vesper was not trying to destroy the city; he was afraid that no one would remember him when the moon rose",
        "resolution": "The shared song gave Vesper a place in the city's night watch, and he returned the bell",
        "image": "the first peaceful thunder rolled above the rooftops like a drum of welcome",
        "lesson": "true strength can make room for a lonely heart",
    },
    {
        "threat": "a jealous cloud giant had chained the dawn bridge and trapped the city's star-lanterns",
        "clue": "The chains brightened whenever Luna and her beloved trusted each other enough to stop pulling",
        "method": "They solved the puzzle by matching their breathing to the bridge's three silver locks",
        "turn": "The giant believed love was a treasure that heroes kept for themselves",
        "resolution": "Luna showed that love grows when it is used to guide everyone safely home",
        "image": "the star-lanterns floated free and painted a golden bridge across the clouds",
        "lesson": "love is not a prize to guard; it is a light to share",
    },
    {
        "threat": "the river dragon had awakened beneath the palace and sent waves through the quiet streets",
        "clue": "Its scales reflected a small picture of a forgotten garden whenever Luna lowered her shield",
        "method": "Luna and her beloved followed the reflections and restored the dragon's dry garden with water from the palace well",
        "turn": "The dragon was angry because the city had built over the garden where it once slept",
        "resolution": "The dragon guided the flood back to the river after the heroes promised to protect the garden",
        "image": "lotus flowers opened along the river while the dragon curled beneath them",
        "lesson": "solving a conflict begins with discovering what was hurt",
    },
    {
        "threat": "a masked rival had stolen the city's sunrise and hidden it inside a crystal maze",
        "clue": "Every false path vanished when Luna admitted one thing she did not know",
        "method": "She and her beloved solved the maze by asking questions instead of pretending to have every answer",
        "turn": "The rival had once been praised as a hero, but now feared being forgotten",
        "resolution": "The heroes invited the rival to help carry the sunrise back to the people",
        "image": "morning spilled over the towers in bright ribbons of pink and gold",
        "lesson": "honesty can open a door that pride keeps locked",
    },
    {
        "threat": "the ancient rose knight had challenged the city to a duel and frozen every garden gate",
        "clue": "The ice melted around flowers that were given freely rather than plucked",
        "method": "Luna and her beloved planted a living path of roses and asked the knight to walk beside them",
        "turn": "The knight had guarded the gardens for centuries and believed every visitor would cause harm",
        "resolution": "The knight lowered his sword and became the gardens' patient protector",
        "image": "red roses climbed the palace walls beneath a warm and friendly moon",
        "lesson": "careful trust can turn a guard into a friend",
    },
]


HERO_NAMES = ["Luna", "Astra", "Nova", "Mira", "Celia"]
HERO_TITLES = ["Moonfire", "Starheart", "Silver Comet", "Dawn Shield", "Nightflare"]
BELOVED_NAMES = ["Orion", "Sol", "Elian", "Rowan", "Cael"]
BELOVED_TYPES = ["guardian", "sky-ranger", "inventor", "healer", "wind-rider"]
SPIRITS = ["Vesper", "Aurex", "Nox", "Thalen", "Zephra"]
RELICS = ["Moonheart Bell", "Star Compass", "Dawn Crown", "Silver Lyre", "Comet Key"]


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mythic romantic superhero conflict and problem-solving storyworld."
    )
    parser.add_argument("--name")
    parser.add_argument("--title")
    parser.add_argument("--beloved")
    parser.add_argument("--beloved-type")
    parser.add_argument("--spirit")
    parser.add_argument("--relic")
    parser.add_argument("--setting")
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
        hero_name=args.name or rng.choice(HERO_NAMES),
        hero_title=args.title or rng.choice(HERO_TITLES),
        beloved_name=args.beloved or rng.choice(BELOVED_NAMES),
        beloved_type=args.beloved_type or rng.choice(BELOVED_TYPES),
        spirit_name=args.spirit or rng.choice(SPIRITS),
        relic=args.relic or rng.choice(RELICS),
        setting=args.setting or "the moonlit city of Selene",
        scenario_index=rng.randrange(len(SCENARIOS)),
        detail_variant=rng.randrange(10000),
    )


def validate_params(params: StoryParams) -> None:
    fields = [
        params.hero_name,
        params.hero_title,
        params.beloved_name,
        params.beloved_type,
        params.spirit_name,
        params.relic,
        params.setting,
    ]
    if any(not isinstance(value, str) or not value.strip() for value in fields):
        raise StoryError("Every named story field must be a non-empty string.")
    if params.hero_name.strip().lower() == params.beloved_name.strip().lower():
        raise StoryError("The hero and beloved must have different names.")
    if params.scenario_index < 0 or params.scenario_index >= len(SCENARIOS):
        raise StoryError(f"scenario_index must be between 0 and {len(SCENARIOS) - 1}.")


def generate_world(params: StoryParams) -> World:
    validate_params(params)
    scenario = SCENARIOS[params.scenario_index]
    world = World(Setting(place=params.setting))

    hero = world.add(
        Entity(
            "hero",
            "person",
            "superhero",
            params.hero_name,
            meters={"distance": 0.0, "strength": 8.0, "harmony": 1.0, "danger": 1.0},
            memes={"worry": 1.0, "courage": 3.0, "trust": 2.0, "love": 2.0, "relief": 0.0},
        )
    )
    beloved = world.add(
        Entity(
            "beloved",
            "person",
            params.beloved_type,
            params.beloved_name,
            meters={"distance": 0.0, "strength": 5.0, "harmony": 1.0, "danger": 1.0},
            memes={"worry": 1.0, "courage": 2.0, "trust": 3.0, "love": 2.0, "relief": 0.0},
        )
    )
    spirit = world.add(
        Entity(
            "spirit",
            "mythic",
            "storm-spirit",
            params.spirit_name,
            meters={"distance": 1.0, "strength": 7.0, "harmony": 0.0, "danger": 8.0},
            memes={"worry": 4.0, "courage": 0.0, "trust": 0.0, "love": 0.0, "relief": 0.0},
        )
    )
    relic = world.add(
        Entity(
            "relic",
            "thing",
            "relic",
            params.relic,
            meters={"distance": 2.0, "strength": 4.0, "harmony": 0.0, "danger": 3.0},
            memes={"worry": 0.0, "courage": 0.0, "trust": 0.0, "love": 0.0, "relief": 0.0},
        )
    )
    world.facts.update(hero=hero, beloved=beloved, spirit=spirit, relic=relic, scenario=scenario)

    opening_options = [
        f"At dusk, {params.hero_name}, known across the rooftops as {params.hero_title}, watched the lamps awaken in {params.setting}.",
        f"When {scenario['threat'].split(' had ')[0]} stirred, {params.hero_name} stood above {params.setting} in a cape bright as moonlight.",
        f"The people of {params.setting} trusted {params.hero_name}, the superhero called {params.hero_title}, to guard their fragile peace.",
    ]
    world.say(opening_options[params.detail_variant % len(opening_options)])
    world.say(
        f"{params.beloved_name}, a brave {params.beloved_type}, joined {params.hero_name} beside "
        f"the {world.setting.landmark}."
    )
    world.say(f"Then {scenario['threat']}. Without the {params.relic}, the city's night would lose its gentle rhythm.")
    world.para()

    hero.meters["distance"] = 1.0
    beloved.meters["distance"] = 1.0
    spirit.meters["danger"] = 9.0
    world.say(
        f"Lightning crossed the {world.setting.sky}, and {params.spirit_name} rose above the towers with "
        f"the {params.relic} locked in a ring of dark clouds."
    )
    world.say(
        f'"We can defeat {params.spirit_name} together," {params.hero_name} said. '
        f'"Perhaps," replied {params.beloved_name}, "but first we should learn why the storm is angry."'
    )
    world.say(f"The words changed {params.hero_name}'s plan. A rushing attack might win a battle and lose the city.")
    world.para()

    hero.memes["worry"] += 1.0
    beloved.memes["trust"] += 1.0
    world.say(f"The heroes climbed the bell tower, where {scenario['clue']}.")
    world.say(
        f"{params.hero_name} lowered the glowing shield. {params.beloved_name} lowered their weapon. "
        f"Together they called, 'We are listening.'"
    )
    world.say(
        f"The cloud opened, and {params.spirit_name} answered, \"Everyone praises heroes and lovers, "
        f"but no one remembers the one who waits in the dark.\""
    )
    world.say(f"That was the hidden conflict: {scenario['turn']}.")
    world.para()

    hero.meters["harmony"] = 5.0
    beloved.meters["harmony"] = 5.0
    spirit.meters["harmony"] = 2.0
    hero.memes["courage"] += 2.0
    beloved.memes["love"] += 2.0
    spirit.memes["trust"] += 1.0
    world.say(
        f"{params.beloved_name} reached for {params.hero_name}'s hand. \"Then let us make a promise "
        f"that includes you,\" they said."
    )
    world.say(
        f"{params.hero_name} answered, \"No one needs to steal a place in our story. We can build one together.\""
    )
    world.say(
        f"Instead of striking, {scenario['method']}. The storm's sharp edges softened around their joined purpose."
    )
    world.para()

    relic.meters["harmony"] = 8.0
    relic.meters["danger"] = 0.0
    spirit.meters["danger"] = 2.0
    spirit.meters["harmony"] = 8.0
    spirit.memes["trust"] += 4.0
    spirit.memes["relief"] += 3.0
    hero.memes["relief"] += 3.0
    beloved.memes["relief"] += 3.0
    world.say(f"{scenario['resolution']}. The {params.relic} rang with a warm note that reached every window.")
    world.say(
        f"{params.spirit_name} bowed. \"May I guard the high clouds?\" "
        f'"You may," said {params.hero_name}, and {params.beloved_name} smiled.'
    )
    world.say(
        f"The city lights returned, and the danger faded because the heroes had solved the conflict instead of merely overpowering it."
    )
    world.para()

    world.say(f"{params.hero_name} understood that {scenario['lesson']}.")
    world.say(f"{params.beloved_name} stayed close as {scenario['image']}.")
    world.log(f"scenario={params.scenario_index}")
    world.log("conflict=understood_the_lonely_opponent")
    world.log("solution=listening_shared_purpose_and_trust")
    world.log("ending=peace_restored_without_defeat")
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    beloved: Entity = world.facts["beloved"]  # type: ignore[assignment]
    spirit: Entity = world.facts["spirit"]  # type: ignore[assignment]
    scenario: dict[str, str] = world.facts["scenario"]  # type: ignore[assignment]
    return [
        f"Write a mythic romantic superhero story about {hero.label} and {beloved.label}.",
        f"Create a conflict in which {spirit.label} threatens {world.setting.place}, then resolve it through problem solving rather than brute force.",
        f"Show how {hero.label} and {beloved.label} use trust and compassion to discover why {spirit.label} is angry.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    beloved: Entity = world.facts["beloved"]  # type: ignore[assignment]
    spirit: Entity = world.facts["spirit"]  # type: ignore[assignment]
    relic: Entity = world.facts["relic"]  # type: ignore[assignment]
    scenario: dict[str, str] = world.facts["scenario"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What danger did {spirit.label} bring to the city?",
            answer=f"{spirit.label} caused this threat: {scenario['threat']}. The stolen {relic.label} made the danger worse.",
        ),
        QAItem(
            question=f"Why did {hero.label} change the first plan?",
            answer=f"{hero.label} changed the plan because {beloved.label} suggested learning why {spirit.label} was angry instead of rushing into a fight.",
        ),
        QAItem(
            question=f"What did the heroes discover about {spirit.label}?",
            answer=f"They discovered that {scenario['turn']}. This changed the problem from a simple battle into a conflict that needed understanding.",
        ),
        QAItem(
            question=f"How did {hero.label} and {beloved.label} solve the conflict?",
            answer=f"They listened, made a promise that included {spirit.label}, and used this method: {scenario['method']}.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"{scenario['resolution']}. The city became safe without the heroes treating the lonely spirit as an enemy who had to be crushed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a character with unusual abilities or courage who uses them to protect others and face difficult problems.",
        ),
        QAItem(
            question="What is a mythic story?",
            answer="A mythic story uses legendary beings, powerful symbols, or ancient-feeling wonders to explore important human choices.",
        ),
        QAItem(
            question="What does romantic mean in this story?",
            answer="Romantic means the story includes tender affection and a caring bond between characters; here, the heroes' love helps them trust and solve the conflict.",
        ),
        QAItem(
            question="Why can listening help solve a conflict?",
            answer="Listening can reveal the need or hurt beneath someone's actions, making it possible to find a solution that protects everyone instead of creating a bigger fight.",
        ),
    ]


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
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id}: type={entity.type}, meters={meters}, memes={memes}"
        )
    lines.extend(world.trace_log)
    return "\n".join(lines)


ASP_RULES = r"""
entity(hero).
entity(beloved).
entity(spirit).
entity(relic).

heard(hero, spirit).
heard(beloved, spirit).
shared_purpose(hero, beloved).
shared_purpose(beloved, hero).
returned(relic).
trusted(spirit).
peace(restored) :- heard(hero, spirit), heard(beloved, spirit), shared_purpose(hero, beloved), returned(relic), trusted(spirit).
heroic_solution :- peace(restored).
romantic_bond :- shared_purpose(hero, beloved), trusted(spirit).
#show peace/1.
#show heroic_solution/0.
#show romantic_bond/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("heard", "hero", "spirit"),
            asp.fact("heard", "beloved", "spirit"),
            asp.fact("shared_purpose", "hero", "beloved"),
            asp.fact("shared_purpose", "beloved", "hero"),
            asp.fact("returned", "relic"),
            asp.fact("trusted", "spirit"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    atoms = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {"peace/1", "heroic_solution/0", "romantic_bond/0"}
    if expected.issubset(atoms):
        print("OK: ASP parity check passed.")
        return 0
    print(f"MISMATCH: expected {sorted(expected)}, got {sorted(atoms)}")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
        hero_name="Luna",
        hero_title="Moonfire",
        beloved_name="Orion",
        beloved_type="guardian",
        spirit_name="Vesper",
        relic="Moonheart Bell",
        scenario_index=0,
    ),
    StoryParams(
        hero_name="Astra",
        hero_title="Starheart",
        beloved_name="Rowan",
        beloved_type="wind-rider",
        spirit_name="Zephra",
        relic="Star Compass",
        scenario_index=1,
    ),
    StoryParams(
        hero_name="Mira",
        hero_title="Dawn Shield",
        beloved_name="Cael",
        beloved_type="healer",
        spirit_name="Thalen",
        relic="Silver Lyre",
        scenario_index=2,
    ),
]


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
        print("ASP model:", " ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n:
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            attempt += 1
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
