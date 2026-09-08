#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: set[str] = field(default_factory=set)


@dataclass
class Setting:
    id: str
    label: str
    clues: list[str]
    safe_places: list[str]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs.append(text)

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


SETTINGS = {
    "rooftops": Setting(
        "rooftops",
        "the bright city rooftops",
        ["a trail of silver feathers", "a tiny star-shaped scorch mark", "a locked blue signal box"],
        ["the old clock tower", "the rooftop garden"],
    ),
    "harbor": Setting(
        "harbor",
        "the moonlit harbor",
        ["green sparks on the pier", "a backwards message in the fog", "a warm footprint on a cold crate"],
        ["the lighthouse balcony", "the harbor watchroom"],
    ),
}

HEROES = {
    "luna": {
        "name": "Luna",
        "power": "moonlight",
        "object": "a silver moon badge",
        "change": "her badge begins to glow whenever she notices someone who needs help",
    },
    "jay": {
        "name": "Jay",
        "power": "wind",
        "object": "a red scarf",
        "change": "his scarf turns into a bright guiding banner whenever he acts bravely",
    },
}

MYSTERIES = {
    "feathers": {
        "title": "the trail of silver feathers",
        "clue": "a silver feather caught on a chimney",
        "truth": "a frightened sky-dragon had become trapped inside the signal box",
        "danger": "the dragon's stormy wings were shaking the roof tiles",
        "action": "followed the feathers instead of chasing the noise",
    },
    "sparks": {
        "title": "the green sparks",
        "clue": "green sparks dancing beneath the pier",
        "truth": "a lonely tide sprite had hidden the harbor beacon because it feared being forgotten",
        "danger": "the dark water was growing rough around the boats",
        "action": "counted the sparks and listened for a small voice",
    },
}

SOLUTIONS = {
    "kindness": {
        "tool": "a warm promise",
        "act": "spoke gently and offered the frightened creature a safe home",
        "result": "the mystery opened into a friendship",
    },
    "courage": {
        "tool": "a glowing rescue rope",
        "act": "crossed the trembling roof and reached the locked place",
        "result": "the hidden friend stepped into the light",
    },
}

ENDINGS = {
    "festival": "That night, the city held a little hero festival, and every window shone like a star.",
    "garden": "By dawn, the rooftop garden was full of new silver flowers, and Luna knew the city was safe.",
    "beacon": "At sunrise, the harbor beacon flashed warmly, guiding every boat home.",
}


@dataclass
class StoryParams:
    setting: str = "rooftops"
    hero: str = "luna"
    mystery: str = "feathers"
    solution: str = "kindness"
    ending: str = "festival"
    seed: Optional[int] = None


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.hero not in HEROES:
        raise StoryError(f"Unknown hero: {params.hero}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"Unknown solution: {params.solution}")
    if params.ending not in ENDINGS:
        raise StoryError(f"Unknown ending: {params.ending}")

    setting = SETTINGS[params.setting]
    hero_cfg = HEROES[params.hero]
    mystery = MYSTERIES[params.mystery]
    solution = SOLUTIONS[params.solution]

    world = World(setting)
    hero = world.add(Entity(
        "hero",
        "hero",
        hero_cfg["name"],
        meters={"energy": 2.0, "power": 1.0},
        memes={"curiosity": 1.0, "worry": 0.0, "hope": 1.0},
        traits={"brave", "kind"},
    ))
    hidden = world.add(Entity(
        "hidden_friend",
        "mystery",
        "the hidden friend",
        meters={"danger": 1.0, "trust": 0.0},
        memes={"loneliness": 1.0, "fear": 1.0},
        traits={"misunderstood"},
    ))
    world.add(Entity(
        "signal",
        "object",
        "the blue signal box",
        meters={"locked": 1.0},
        memes={"silence": 1.0},
        traits={"mysterious"},
    ))

    world.facts.update(
        hero=hero,
        hero_cfg=hero_cfg,
        mystery=mystery,
        solution=solution,
        hidden=hidden,
        ending=ENDINGS[params.ending],
        params=params,
    )
    return world


def create_story(world: World) -> None:
    hero = world.facts["hero"]
    cfg = world.facts["hero_cfg"]
    mystery = world.facts["mystery"]
    solution = world.facts["solution"]
    hidden = world.facts["hidden"]
    setting = world.setting

    world.say(
        f"One evening, {hero.label} became the city's newest superhero. "
        f"{hero.label} wore {cfg['object']} and could call on the power of {cfg['power']}."
    )
    world.say(
        f"Then something bad happened in {setting.label}: {mystery['title']} appeared, "
        f"and the city's warning lights began to blink."
    )
    world.say(
        f'"That is not a normal alarm," {hero.label} said. '
        f'"I will solve this mystery before anyone gets hurt."'
    )
    world.say(
        f"The first clue was {mystery['clue']}. {hero.label} remembered that a mystery is easier to solve "
        f"when a hero looks closely, so {hero.label} {mystery['action']}."
    )
    world.say(
        f"Behind {setting.safe_places[0]} stood the blue signal box. "
        f"{mystery['danger'].capitalize()}, and the locked door rattled."
    )
    world.say(
        f'"Are you causing all this trouble?" {hero.label} called. '
        f'"No," answered a small voice. "I am scared, and I do not know how to ask for help."'
    )
    hidden.meters["danger"] = 0.0
    hidden.meters["trust"] = 1.0
    hidden.memes["fear"] = 0.0
    hidden.memes["hope"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["understanding"] = 1.0
    hero.meters["power"] = 2.0
    world.say(
        f"{hero.label} changed from a hurried fighter into a careful helper. "
        f"Using {solution['tool']}, {hero.label} {solution['act']}."
    )
    world.say(
        f"The lock clicked open. The hidden friend stepped out, and {solution['result']}. "
        f"The warning lights turned from red to cheerful gold."
    )
    world.say(
        f'"You are not bad," {hero.label} said. "You only needed someone to listen." '
        f'"And you are my hero," said the friend.'
    )
    world.say(
        f"Together they repaired the signal and watched the city sparkle. {world.facts['ending']}"
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    create_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story in {world.setting.label} about {f['hero'].label} solving {f['mystery']['title']}.",
        f"Show how {f['hero'].label} changes from a hurried fighter into a careful helper.",
        f"End happily after the hidden friend is understood and the city becomes safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    solution = f["solution"]
    return [
        QAItem(
            "What bad problem did the hero need to solve?",
            f"{hero.label} needed to solve {mystery['title']} in {world.setting.label}, where warning lights were blinking.",
        ),
        QAItem(
            f"How did {hero.label} discover the truth?",
            f"{hero.label} followed {mystery['clue']}, listened to a small voice, and learned that {mystery['truth']}.",
        ),
        QAItem(
            f"How did {hero.label} change?",
            f"{hero.label} changed from a hurried fighter into a careful helper by using {solution['tool']} and listening before acting.",
        ),
        QAItem(
            "How did the story end?",
            f"The hidden friend was safe, the signal was repaired, and the city celebrated with a happy ending: {f['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a superhero?", "A superhero is a character who uses special courage, skills, or powers to help others."),
        QAItem("What is a mystery?", "A mystery is a problem or secret that must be understood by finding and connecting clues."),
        QAItem("Why can listening help solve a problem?", "Listening can reveal what someone needs and prevent a hero from making a wrong guess."),
        QAItem("What is a transformation in a story?", "A transformation is a meaningful change in a character's feelings, choices, or behavior."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story Q&A ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---", f"setting: {world.setting.label}"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.label}: meters={meters}, memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(rooftops).
setting(harbor).
mystery(feathers).
mystery(sparks).
solution(kindness).
solution(courage).
danger(feathers).
danger(sparks).
clue(feathers).
clue(sparks).
solves(kindness, feathers).
solves(kindness, sparks).
solves(courage, feathers).
solves(courage, sparks).
valid_story(S, M, X) :- setting(S), mystery(M), solution(X), solves(X, M).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    facts = []
    for setting in SETTINGS:
        facts.append(asp.fact("setting", setting))
    for mystery in MYSTERIES:
        facts.append(asp.fact("mystery", mystery))
        facts.append(asp.fact("danger", mystery))
        facts.append(asp.fact("clue", mystery))
    for solution in SOLUTIONS:
        facts.append(asp.fact("solution", solution))
    for solution in SOLUTIONS:
        for mystery in MYSTERIES:
            facts.append(asp.fact("solves", solution, mystery))
    return "\n".join(facts)


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (setting, mystery, solution)
        for setting in SETTINGS
        for mystery in MYSTERIES
        for solution in SOLUTIONS
    ]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(asp_valid_combos())
    if expected != actual:
        print("MISMATCH between Python and ASP story gates.")
        print("only in Python:", sorted(expected - actual))
        print("only in ASP:", sorted(actual - expected))
        return 1
    for combo in sorted(expected):
        sample = generate(StoryParams(setting=combo[0], mystery=combo[1], solution=combo[2]))
        if not sample.story.strip() or "bad" not in sample.story.lower():
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP/Python parity and {len(expected)} generated stories verified.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        hero=args.hero or rng.choice(list(HEROES)),
        mystery=args.mystery or rng.choice(list(MYSTERIES)),
        solution=args.solution or rng.choice(list(SOLUTIONS)),
        ending=args.ending or rng.choice(list(ENDINGS)),
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A superhero mystery storyworld about a bad problem, transformation, and happy ending.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--mystery", choices=MYSTERIES)
    parser.add_argument("--solution", choices=SOLUTIONS)
    parser.add_argument("--ending", choices=ENDINGS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(json.dumps(asp.atoms(asp.one_model(asp_program()), "valid_story"), indent=2))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            for mystery in MYSTERIES:
                samples.append(generate(StoryParams(
                    setting=setting,
                    mystery=mystery,
                    seed=base_seed,
                )))
    else:
        for index in range(max(1, args.n)):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
