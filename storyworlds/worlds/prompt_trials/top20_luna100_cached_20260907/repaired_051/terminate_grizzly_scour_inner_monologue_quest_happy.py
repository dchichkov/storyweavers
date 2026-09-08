#!/usr/bin/env python3
"""
A tiny superhero storyworld about a grizzly, a quest, and the choice to
terminate a dangerous search before courage turns into carelessness.
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
    type: str = "thing"
    meters: dict[str, float] = field(
        default_factory=lambda: {"distance": 0.0, "safety": 0.0, "brightness": 0.0}
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
    place: str = "the storm-bent city park"
    landmark: str = "the old bell tower"


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    grizzly_name: str
    quest_item: str
    place: str
    landmark: str
    scenario_index: int = 0
    voice_index: int = 0
    detail_index: int = 0
    seed: Optional[int] = None


SCENARIOS = [
    {
        "threat": "a runaway cloud-drone",
        "clue": "a bright blue spark winked beneath a fallen bridge plank",
        "wrong": "The hero began to scour every shadow at once, and the grizzly could no longer see the safe path.",
        "plan": "They marked the searched places with chalk, followed the sparks one at a time, and stopped before the cracked bank.",
        "turn": "The final spark was not a clue to chase but a signal from the trapped drone.",
        "ending": "The drone's little lights blinked a grateful heart above the clean, quiet pond.",
        "lesson": "a hero knows when to terminate a risky search and choose a wiser rescue",
    },
    {
        "threat": "a silver rescue kite",
        "clue": "a thread trembled beside the park's locked greenhouse",
        "wrong": "The hero tugged at the thread too quickly, making the kite knot tighter.",
        "plan": "The grizzly held the spool steady while the hero used a fallen reed to loosen the knot.",
        "turn": "The kite was carrying the missing quest item toward a child who needed help.",
        "ending": "The kite sailed over the greenhouse with the quest item safely tied beneath it.",
        "lesson": "careful strength can protect what hurried strength might break",
    },
    {
        "threat": "a rumbling tunnel cart",
        "clue": "three warm wheel marks curved away from the station",
        "wrong": "The hero rushed into the tunnel, but the grizzly heard the rails shaking ahead.",
        "plan": "They placed a bright warning beacon at the entrance and used a side path to reach the control lever.",
        "turn": "The cart held sleepy maintenance robots, not villains, and its brake had simply failed.",
        "ending": "The robots rolled safely into the station and repaired the park's broken lights.",
        "lesson": "superheroes investigate before they decide whom to blame",
    },
    {
        "threat": "a gust-powered paper dragon",
        "clue": "a red ribbon fluttered from the roof of the community hall",
        "wrong": "The hero tried to fly straight after it, but the wind spun the cape around a chimney.",
        "plan": "The grizzly anchored a rescue rope while the hero used the wind's rhythm instead of fighting it.",
        "turn": "The dragon was carrying a lost birthday wish toward the child's window.",
        "ending": "The wish floated gently down, and every child in the hall cheered.",
        "lesson": "helping someone reach joy is a true superhero victory",
    },
]


HERO_TYPES = ["captain", "guardian", "sky hero", "light hero"]
HERO_NAMES = ["Luna", "Pip", "Nova", "Mira", "Toby"]
GRIZZLY_NAMES = ["Bruno", "Gus", "Moss", "Big Bear", "Rumble"]
QUEST_ITEMS = ["the silver compass", "the moon badge", "the bright rescue key", "the golden signal bell"]
PLACES = [
    "the storm-bent city park",
    "the rooftop garden district",
    "the riverside hero station",
    "the lantern-lit town square",
]
LANDMARKS = [
    "the old bell tower",
    "the cracked fountain",
    "the blue footbridge",
    "the red rescue shed",
]


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero Story: a grizzly, a quest, and a safe happy ending."
    )
    parser.add_argument("--name")
    parser.add_argument("--type")
    parser.add_argument("--grizzly")
    parser.add_argument("--item")
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
    return StoryParams(
        hero_name=args.name or rng.choice(HERO_NAMES),
        hero_type=args.type or rng.choice(HERO_TYPES),
        grizzly_name=args.grizzly or rng.choice(GRIZZLY_NAMES),
        quest_item=args.item or rng.choice(QUEST_ITEMS),
        place=args.place or rng.choice(PLACES),
        landmark=args.landmark or rng.choice(LANDMARKS),
        scenario_index=rng.randrange(len(SCENARIOS)),
        voice_index=rng.randrange(4),
        detail_index=rng.randrange(10000),
    )


def validate(params: StoryParams) -> None:
    if not params.hero_name.strip():
        raise StoryError("hero name cannot be empty")
    if not params.grizzly_name.strip():
        raise StoryError("grizzly name cannot be empty")
    if params.hero_name.lower() == params.grizzly_name.lower():
        raise StoryError("the hero and grizzly need different names")
    if not params.quest_item.strip():
        raise StoryError("quest item cannot be empty")
    if not 0 <= params.scenario_index < len(SCENARIOS):
        raise StoryError("scenario index is outside the story registry")


def tell(params: StoryParams) -> World:
    validate(params)
    scenario = SCENARIOS[params.scenario_index]
    world = World(Setting(params.place, params.landmark))

    hero = world.add(Entity("hero", "animal", params.hero_name, params.hero_type))
    grizzly = world.add(Entity("grizzly", "animal", params.grizzly_name, "grizzly"))
    item = world.add(Entity("quest_item", "object", params.quest_item))
    world.facts.update(hero=hero, grizzly=grizzly, item=item, scenario=scenario)

    hero.memes["courage"] = 1.0
    grizzly.memes["trust"] = 1.0
    hero.meters["distance"] = 0.0
    item.meters["safety"] = 0.0

    openings = [
        f"At sunrise, {hero.label} the {hero.type} watched storm clouds curl over {world.setting.place}.",
        f"When the warning bell rang above {world.setting.place}, {hero.label} pulled on a bright cape.",
        f"Under a sky full of silver clouds, {hero.label} stood ready beside {world.setting.landmark}.",
        f"The town's quiet morning changed when {hero.label} saw a red signal flash over {world.setting.place}.",
    ]
    world.say(openings[params.voice_index])
    world.say(
        f"A quest had arrived: recover {item.label} before {scenario['threat']} carried it beyond the town."
    )
    world.say(
        f'"I will scour the park until I find it," {hero.label} promised. '
        f'"And I will help you notice what danger is saying," {grizzly.label} replied.'
    )
    world.para()

    hero.memes["worry"] = 1.0
    hero.meters["distance"] = 1.0
    world.say(
        f"The trail led toward {world.setting.landmark}, where {scenario['clue']}. "
        f"The wind pushed dust across the path, and the cracked ground made every step uncertain."
    )
    world.say(
        f"{scenario['wrong']} {hero.label} stopped, while {grizzly.label} placed one careful paw beside the warning line."
    )
    world.para()

    hero.memes["courage"] = 2.0
    grizzly.memes["trust"] = 2.0
    world.say(
        f'"Should we terminate the search here?" {grizzly.label} asked. '
        f'"Not the quest," {hero.label} said. "Only the unsafe way of doing it."'
    )
    world.say(scenario["plan"])
    world.say(scenario["turn"])
    world.say(
        f"Together they reached the quest item without crossing the broken ground. "
        f"{item.label.capitalize()} was safe, and {scenario['threat']} slowed above them."
    )
    world.para()

    item.meters["safety"] = 1.0
    item.meters["brightness"] = 1.0
    hero.meters["safety"] = 1.0
    grizzly.meters["safety"] = 1.0
    hero.memes["relief"] = 1.0
    grizzly.memes["joy"] = 1.0
    world.say(
        f"{hero.label} returned {item.label} to the rescue station, while {grizzly.label} "
        f"kept watch beside the safe path."
    )
    world.say(scenario["ending"])
    world.say(
        f"The townspeople clapped for the happy ending, but {hero.label} remembered the better victory: "
        f"{scenario['lesson']}."
    )
    world.log("quest_started=true")
    world.log("unsafe_search_terminated=true")
    world.log("quest_complete=true")
    world.log("happy_ending=true")
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    grizzly: Entity = world.facts["grizzly"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly Superhero Story about {hero.label} and {grizzly.label}, a grizzly helper.",
        f"Tell a quest story in which {hero.label} must recover {item.label}, scour a dangerous place, and terminate an unsafe search.",
        f"Include inner monologue, a brief dialogue exchange, a clear turn, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    grizzly: Entity = world.facts["grizzly"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]
    scenario: dict[str, str] = world.facts["scenario"]  # type: ignore[assignment]
    return [
        QAItem(
            f"What quest did {hero.label} have?",
            f"{hero.label} had to recover {item.label} before {scenario['threat']} carried it away.",
        ),
        QAItem(
            f"Why did {hero.label} stop trying to scour every shadow?",
            f"{hero.label} stopped because the search was becoming unsafe and the grizzly noticed the warning signs.",
        ),
        QAItem(
            f"What did {grizzly.label} ask the hero to terminate?",
            f"{grizzly.label} asked {hero.label} to terminate the unsafe way of searching, not to abandon the quest.",
        ),
        QAItem(
            "How did the friends solve the problem?",
            f"They followed the clue carefully, used a safer plan, and recovered {item.label} without crossing the broken ground.",
        ),
        QAItem(
            "How did the story end?",
            f"The quest item was returned safely, the town celebrated, and the friends shared a happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does terminate mean?",
            "Terminate means to stop or bring something to an end.",
        ),
        QAItem(
            "What is a grizzly?",
            "A grizzly is a large brown bear. In this story, the grizzly is a thoughtful helper.",
        ),
        QAItem(
            "What does scour mean?",
            "To scour means to search a place very carefully, often by looking in many spots.",
        ),
        QAItem(
            "What is an inner monologue?",
            "An inner monologue is a character's private thoughts, shown so readers can understand what the character is deciding.",
        ),
        QAItem(
            "What makes a happy ending?",
            "A happy ending shows that the main problem has been solved and that the characters are safe, relieved, or joyful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
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
entity(grizzly).
entity(quest_item).

quest_complete :- recovered(quest_item), safe(quest_item), unsafe_search_terminated.
happy_ending :- quest_complete, helped(grizzly).

#show quest_complete/0.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("recovered", "quest_item"),
            asp.fact("safe", "quest_item"),
            asp.fact("unsafe_search_terminated"),
            asp.fact("helped", "grizzly"),
        ]
    )


def asp_program(show: str = "#show quest_complete/0. #show happy_ending/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    atoms = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {"quest_complete/0", "happy_ending/0"}
    if atoms == expected:
        print("OK: ASP parity check passed.")
        return 0
    print(f"MISMATCH: {sorted(atoms)} != {sorted(expected)}")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    if not sample.story.strip():
        raise StoryError("generated story is empty")
    return sample


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
        hero_type="light hero",
        grizzly_name="Bruno",
        quest_item="the moon badge",
        place="the storm-bent city park",
        landmark="the old bell tower",
        scenario_index=0,
        voice_index=0,
        detail_index=11,
    ),
    StoryParams(
        hero_name="Nova",
        hero_type="sky hero",
        grizzly_name="Moss",
        quest_item="the golden signal bell",
        place="the rooftop garden district",
        landmark="the blue footbridge",
        scenario_index=1,
        voice_index=1,
        detail_index=22,
    ),
    StoryParams(
        hero_name="Mira",
        hero_type="guardian",
        grizzly_name="Gus",
        quest_item="the bright rescue key",
        place="the riverside hero station",
        landmark="the red rescue shed",
        scenario_index=2,
        voice_index=2,
        detail_index=33,
    ),
    StoryParams(
        hero_name="Pip",
        hero_type="captain",
        grizzly_name="Rumble",
        quest_item="the silver compass",
        place="the lantern-lit town square",
        landmark="the cracked fountain",
        scenario_index=3,
        voice_index=3,
        detail_index=44,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        code = asp_verify()
        if code:
            sys.exit(code)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or len(sample.story_qa) < 3:
                print("MISMATCH: generated story verification failed")
                sys.exit(1)
        print("OK: generated story checks passed.")
        return

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
