#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a clink, a seasonal task, and learning
to check a quiet misunderstanding before it causes trouble.
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

_repo_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_repo_root))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Kitchen:
    name: str
    season: str
    counter_clear: bool = True
    window_open: bool = False


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    neighbor_name: str
    season: str
    seed: Optional[int] = None


@dataclass
class World:
    kitchen: Kitchen
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


SETTINGS = {
    "kitchen": Kitchen(name="the apartment kitchen", season="spring"),
}

NAMES = ["Luna", "Milo", "Nia", "Owen", "Tess", "Ari", "June", "Sam"]
SEASONS = ["spring", "summer", "autumn", "winter"]

SEASON_TASKS = {
    "spring": {
        "gerund": "sorting seed packets",
        "object": "the small tin of sunflower seeds",
        "ending": "the seed tin clicked safely into the labeled drawer",
    },
    "summer": {
        "gerund": "cooling jars of berry jam",
        "object": "the warm blue jam jar",
        "ending": "the jam jars rested behind a bright paper label",
    },
    "autumn": {
        "gerund": "drying apple slices",
        "object": "the tray of apple slices",
        "ending": "the crisp apple slices filled a clean glass jar",
    },
    "winter": {
        "gerund": "checking the storm candles",
        "object": "the box of storm candles",
        "ending": "the candles stood ready beside the flashlight",
    },
}

OPENINGS = [
    "On a quiet afternoon",
    "Just before the kettle began to sing",
    "After the window fogged with warm breath",
    "Near the end of a small household chore",
    "While soft light crossed the kitchen floor",
]

WARNINGS = [
    "Careful, that lid is not fully closed",
    "Please wait; I want to check the label first",
    "That sound means something may be loose",
    "Let's put the tray down before we hurry",
]

REFLECTIONS = [
    "The ordinary chore felt different after they learned that a quick guess can hide a real warning.",
    "Nothing dramatic had happened, but checking together had kept a small mistake from becoming a large one.",
    "They decided that careful questions belonged in everyday life, especially when a familiar sound made them worry.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A slice-of-life clink storyworld.")
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--name")
    parser.add_argument("--neighbor")
    parser.add_argument("--season", choices=SEASONS)
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
    hero = args.name or rng.choice(NAMES)
    neighbor_pool = [name for name in NAMES if name != hero]
    neighbor = args.neighbor or rng.choice(neighbor_pool)
    return StoryParams(
        setting=args.setting or "kitchen",
        hero_name=hero,
        neighbor_name=neighbor,
        season=args.season or rng.choice(SEASONS),
    )


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.season not in SEASONS:
        raise StoryError(f"Unknown season: {params.season}")
    if params.hero_name == params.neighbor_name:
        raise StoryError("The hero and neighbor must have different names.")

    template = SETTINGS[params.setting]
    task = SEASON_TASKS[params.season]
    kitchen = Kitchen(
        name=template.name,
        season=params.season,
        counter_clear=True,
        window_open=False,
    )
    world = World(kitchen)
    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="person",
            type="child",
            label="careful helper",
            meters={"attention": 1.0, "urgency": 0.4},
            memes={"pride": 0.4, "trust": 0.7},
        )
    )
    neighbor = world.add(
        Entity(
            id=params.neighbor_name,
            kind="person",
            type="neighbor",
            label="helpful neighbor",
            meters={"attention": 0.8, "urgency": 0.3},
            memes={"worry": 0.3, "trust": 0.7},
        )
    )

    rng = random.Random(params.seed or 0)
    opening = rng.choice(OPENINGS)
    warning = rng.choice(WARNINGS)
    reflection = rng.choice(REFLECTIONS)

    world.say(
        f"{opening}, {hero.id} was in {kitchen.name}, {task['gerund']} for the {params.season}."
    )
    world.say(
        f"{neighbor.id} came in carrying {task['object']}, and the two friends worked side by side."
    )
    world.say(
        f"When the metal lid made a little clink, {hero.id} quickly moved the object away from the edge."
    )
    world.para()

    world.say(
        f"{neighbor.id} frowned. They thought the sudden movement meant {hero.id} did not trust them with the chore."
    )
    world.say(f'"Why did you grab that?" {neighbor.id} asked.')
    world.say(
        f'"I heard a clink and thought it was slipping," {hero.id} replied. "I was trying to keep it safe."'
    )
    world.say(
        f'"I thought you were taking it away from me," {neighbor.id} said.'
    )
    world.para()

    world.say(
        f"The misunderstanding grew because neither friend had checked what the sound meant. "
        f"Then {hero.id} noticed a bent spoon beside the counter and remembered the warning sign."
    )
    world.say(f'"{warning}," {hero.id} said. "Can we look before we decide?"')
    world.say(
        f"{neighbor.id} listened. Together they lifted the object, checked its lid, and found that the spoon had struck the metal."
    )
    world.say(
        f"The object was safe, but the cautionary clink had been real: the counter edge was crowded, and one careless bump could have broken it."
    )
    world.para()

    world.say(
        f'"I am sorry I guessed what you meant," {neighbor.id} said.'
    )
    world.say(
        f'"And I am sorry I moved it without explaining," {hero.id} answered. '
        f'"Next time, let us name the problem before we act."'
    )
    world.say(
        f"They cleared the counter, finished {task['gerund']}, and placed everything where both of them could find it."
    )
    world.say(
        f"{reflection} {task['ending'].capitalize()}."
    )

    hero.meters["attention"] = 1.0
    hero.meters["urgency"] = 0.1
    hero.memes["pride"] = 0.1
    hero.memes["trust"] = 1.0
    neighbor.meters["attention"] = 1.0
    neighbor.memes["worry"] = 0.0
    neighbor.memes["trust"] = 1.0

    world.facts.update(
        hero=hero,
        neighbor=neighbor,
        task=task,
        warning=warning,
        reflection=reflection,
        season=params.season,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    task = world.facts["task"]
    return [
        f"Write a Slice of Life story about {task['gerund']} and a surprising clink.",
        "Write a dialogue-rich story about a misunderstanding resolved by checking evidence.",
        "Write a cautionary everyday story with foreshadowing shown through an ordinary sound.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"]
    neighbor = facts["neighbor"]
    task = facts["task"]
    return [
        QAItem(
            question=f"What caused the misunderstanding between {hero.id} and {neighbor.id}?",
            answer=f"{neighbor.id} thought {hero.id}'s quick movement meant distrust, but {hero.id} had moved {task['object']} after hearing a clink.",
        ),
        QAItem(
            question="What did the clink foreshadow?",
            answer="The clink foreshadowed that the crowded counter could cause a real accident if the friends did not check the object and clear the space.",
        ),
        QAItem(
            question="How did the friends discover what happened?",
            answer=f"They stopped guessing, inspected the object together, and found that a spoon had struck the metal lid.",
        ),
        QAItem(
            question="What did the friends change after their conversation?",
            answer=f"They apologized, agreed to explain concerns before acting, cleared the counter, and finished {task['gerund']}.",
        ),
        QAItem(
            question="Why was the ending important?",
            answer=f"The ending showed that their repair lasted because {task['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is a mistaken idea about what someone said, meant, or did.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives an early hint about something that may matter later.",
        ),
        QAItem(
            question="Why can a clink be useful?",
            answer="A clink can be a small warning that objects touched, shifted, or may need to be checked.",
        ),
        QAItem(
            question="What makes a warning cautionary?",
            answer="A cautionary warning encourages people to slow down and avoid harm or a larger mistake.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(
        f"setting={world.kitchen.name}, season={world.kitchen.season}, "
        f"counter_clear={world.kitchen.counter_clear}"
    )
    for entity in world.entities.values():
        lines.append(f"{entity.id}: meters={entity.meters} memes={entity.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(kitchen).
feature(misunderstanding).
feature(cautionary).
feature(foreshadowing).
feature(dialogue).
sound(clink).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("setting", "kitchen"),
            asp.fact("feature", "misunderstanding"),
            asp.fact("feature", "cautionary"),
            asp.fact("feature", "foreshadowing"),
            asp.fact("feature", "dialogue"),
            asp.fact("sound", "clink"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(
        asp_program("#show feature/1.\n#show sound/1.")
    )
    features = set(asp.atoms(model, "feature"))
    sounds = set(asp.atoms(model, "sound"))
    expected_features = {
        ("misunderstanding",),
        ("cautionary",),
        ("foreshadowing",),
        ("dialogue",),
    }
    if features != expected_features or sounds != {("clink",)}:
        print("Mismatch in ASP verification.")
        return 1

    params = StoryParams(
        setting="kitchen",
        hero_name="Luna",
        neighbor_name="Milo",
        season="spring",
        seed=17,
    )
    sample = generate(params)
    required = ["clink", "misunderstanding", "counter", "sorry"]
    lowered = sample.story.lower()
    if any(word not in lowered for word in required):
        print("Generated story verification failed.")
        return 1
    print("OK: ASP facts match Python story features and story generation works.")
    return 0


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show feature/1.\n#show sound/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(
            asp_program("#show feature/1.\n#show sound/1.")
        )
        print(
            {
                "features": sorted(set(asp.atoms(model, "feature"))),
                "sounds": sorted(set(asp.atoms(model, "sound"))),
            }
        )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, season in enumerate(SEASONS):
            params = StoryParams(
                setting="kitchen",
                hero_name=NAMES[index],
                neighbor_name=NAMES[index + 1],
                season=season,
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n) and attempt < max(50, args.n * 20):
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
