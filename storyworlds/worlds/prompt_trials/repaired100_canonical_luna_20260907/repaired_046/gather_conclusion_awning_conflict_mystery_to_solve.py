#!/usr/bin/env python3
"""A gentle bedtime mystery about gathering beneath an awning and sharing a conclusion."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    setting: str = "the quiet garden"
    hero: str = "Luna"
    friend: str = "Theo"
    object: str = "a silver bell"
    seed: Optional[int] = None


SETTINGS = {
    "garden": "the quiet garden",
    "meadow": "the moonlit meadow",
    "cottage": "the cottage yard",
}
HEROES = ["Luna", "Mira", "Nell", "Sora"]
FRIENDS = ["Theo", "Pip", "Owen", "Tess"]
OBJECTS = ["a silver bell", "a blue lantern", "a tiny music box", "a red ribbon"]


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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


@dataclass(frozen=True)
class Mystery:
    name: str
    clue: str
    guess: str
    hero_job: str
    friend_job: str
    discovery: str
    sharing: str
    ending: str


MYSTERIES = [
    Mystery(
        "the missing bell",
        "a thin silver mark curved from the path to the awning post",
        "the wind carried it away",
        "follow the mark with a little lantern",
        "listen beneath the folded picnic cloth",
        "the bell was tucked in a basket where the evening breeze had rolled it",
        "the friends passed it from hand to hand so everyone could hear its clear note",
        "the bell chimed softly while sleepy moths circled the awning",
    ),
    Mystery(
        "the hidden lantern",
        "three warm dots glowed beneath the awning's lowest flap",
        "someone had taken it to the shed",
        "lift the awning cloth carefully",
        "gather the cushions and look behind them",
        "the lantern rested inside a cushion basket, glowing through its weave",
        "they shared its light instead of letting one friend carry it alone",
        "a golden pool of light waited beneath the quiet awning",
    ),
    Mystery(
        "the wandering ribbon",
        "a red thread hung from the awning and fluttered toward the herb bed",
        "a bird had carried it to a nest",
        "follow the thread without pulling it",
        "check the garden chairs and the low branches",
        "the ribbon had caught on a chair and was tugged by the night breeze",
        "they tied it back with a knot each friend could help hold",
        "the ribbon rested safely above them like a small sunset",
    ),
    Mystery(
        "the whispering box",
        "a faint music note sounded whenever the awning swayed",
        "the box had fallen into the tall grass",
        "stand still and count each sound",
        "steady the awning while checking the table",
        "the music box was beneath a folded blanket, and the moving cloth pressed its key",
        "they shared the tune by taking turns winding it",
        "one soft melody floated into the darkening garden",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bedtime awning mystery story world.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--object", choices=OBJECTS)
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
    hero = args.hero or rng.choice(HEROES)
    choices = [name for name in FRIENDS if name != hero]
    friend = args.friend or rng.choice(choices)
    return StoryParams(
        setting=SETTINGS[args.setting or rng.choice(list(SETTINGS))],
        hero=hero,
        friend=friend,
        object=args.object or rng.choice(OBJECTS),
    )


def _mystery(params: StoryParams) -> Mystery:
    seed = params.seed if params.seed is not None else 0
    return MYSTERIES[seed % len(MYSTERIES)]


def tell(params: StoryParams) -> World:
    world = World(params)
    hero = world.add(Entity(
        "hero", "character", params.hero, "hero",
        meters={"curiosity": 1.0, "calm": 0.5},
        memes={"trust": 1.0, "sharing": 0.0},
        traits=["patient"],
    ))
    friend = world.add(Entity(
        "friend", "character", params.friend, "friend",
        meters={"curiosity": 1.0, "calm": 0.5},
        memes={"trust": 1.0, "sharing": 0.0},
        traits=["kind"],
    ))
    object_entity = world.add(Entity(
        "mystery_object", "thing", params.object, "mystery object",
        meters={"safety": 1.0},
        memes={},
        traits=["beloved"],
    ))
    awning = world.add(Entity(
        "awning", "place", "the striped awning", "shelter",
        meters={"shelter": 1.0},
        memes={"welcome": 1.0},
        traits=["cozy"],
    ))
    mystery = _mystery(params)

    world.say(f"Night folded its blue blanket over {params.setting}.")
    world.say(
        f"{hero.label} and {friend.label} went to gather their favorite things beneath "
        f"{awning.label}, where they planned to listen for the first sleepy crickets."
    )
    world.say(
        f"But {object_entity.label} was gone. Only an empty place remained beside the cushions."
    )
    world.say(f"“Did you move it?” asked {hero.label}.")
    world.say(
        f"“No,” said {friend.label}. “Let us not quarrel. We can share our eyes and solve the mystery together.”"
    )

    world.para()
    world.say(
        f"Their small conflict made the awning seem unusually large and quiet. "
        f"Then {hero.label} noticed {mystery.clue}."
    )
    world.say(f"“Perhaps {mystery.guess},” whispered {hero.label}.")
    world.say(
        f"{friend.label} shook {friend.label}'s head. “That is only a guess. "
        f"A careful conclusion needs more than a worried thought.”"
    )
    hero.meters["curiosity"] += 1.0
    friend.meters["calm"] += 1.0

    world.para()
    world.say("So they made a gentle plan.")
    world.say(
        f"{hero.label} would {mystery.hero_job}, while {friend.label} would {mystery.friend_job}."
    )
    world.say(
        f"They moved slowly, because rushing could hide a clue. "
        f"Together, {hero.label} and {friend.label} found that {mystery.discovery}."
    )
    world.say(
        f"“Now we know,” said {hero.label}. “That is our conclusion.”"
    )
    world.say(
        f"“And now we can share the good news,” said {friend.label}."
    )
    hero.memes["trust"] += 1.0
    friend.memes["trust"] += 1.0
    hero.memes["sharing"] += 1.0
    friend.memes["sharing"] += 1.0

    world.para()
    world.say(f"{mystery.sharing.capitalize()}.")
    world.say(
        f"Their worry softened into a warm smile. The empty place beneath the awning no longer felt lonely."
    )
    world.say(
        f"At last, {mystery.ending}. "
        f"{hero.label} and {friend.label} leaned together and watched the stars blink awake."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        object=object_entity,
        awning=awning,
        mystery=mystery.name,
        clue=mystery.clue,
        guess=mystery.guess,
        hero_job=mystery.hero_job,
        friend_job=mystery.friend_job,
        discovery=mystery.discovery,
        sharing=mystery.sharing,
        ending=mystery.ending,
        conflict=True,
        conclusion=True,
        awning=True,
        dialogue=True,
        sharing=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle bedtime mystery in which {f['hero'].label} and {f['friend'].label} gather beneath an awning.",
        f"Include a conflict, a clue, and a clear conclusion about {f['mystery']}.",
        "Show two friends sharing both the search and the happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    friend = f["friend"].label
    return [
        QAItem(
            question=f"Why did {hero} and {friend} begin searching?",
            answer=f"They began searching because {f['object'].label} was missing from beneath the awning.",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f"The clue was that {f['clue']}. It gave the friends a useful place to look.",
        ),
        QAItem(
            question=f"How did {hero} and {friend} handle their conflict?",
            answer=f"They stopped blaming each other and shared their eyes, making a careful plan to investigate together.",
        ),
        QAItem(
            question="What was their conclusion?",
            answer=f"Their conclusion was that {f['discovery']}.",
        ),
        QAItem(
            question="How did the friends show sharing?",
            answer=f"They shared the search and then {f['sharing']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is it useful to listen before reaching a conclusion?",
            answer="Listening and checking clues can help people understand what really happened instead of relying on a guess.",
        ),
        QAItem(
            question="What is an awning?",
            answer="An awning is a covering that provides shade or shelter above a doorway, window, or outdoor space.",
        ),
        QAItem(
            question="Why can sharing make a problem easier?",
            answer="Sharing work, ideas, and care gives everyone a chance to help and makes a difficult task feel less lonely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== world qa =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: meters={entity.meters} memes={entity.memes} traits={entity.traits}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_setting/1.
valid_setting(garden).
valid_setting(meadow).
valid_setting(cottage).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("setting", key) for key in SETTINGS)


def asp_program(show: str = "#show valid_setting/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    actual = sorted(set(asp.atoms(model, "valid_setting")))
    expected = sorted((key,) for key in SETTINGS)
    if actual != expected:
        print("MISMATCH")
        return 1
    for index, setting in enumerate(SETTINGS.values()):
        params = StoryParams(
            setting=setting,
            hero=HEROES[index % len(HEROES)],
            friend=FRIENDS[index % len(FRIENDS)],
            object=OBJECTS[index % len(OBJECTS)],
            seed=index,
        )
        sample = generate(params)
        if not sample.story or "conclusion" not in sample.story.lower():
            print("MISMATCH: generated story failed")
            return 1
    print(f"OK: ASP gate matches settings ({len(actual)}); generated stories pass.")
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        setting=SETTINGS["garden"],
        hero="Luna",
        friend="Theo",
        object="a silver bell",
        seed=0,
    ),
    StoryParams(
        setting=SETTINGS["meadow"],
        hero="Mira",
        friend="Pip",
        object="a blue lantern",
        seed=1,
    ),
    StoryParams(
        setting=SETTINGS["cottage"],
        hero="Nell",
        friend="Owen",
        object="a red ribbon",
        seed=2,
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
        print(f"{len(SETTINGS)} valid settings:")
        for key in SETTINGS:
            print(f"  {key}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(args.n * 50, 50):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero} and {sample.params.friend} in {sample.params.setting}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
