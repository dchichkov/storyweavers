#!/usr/bin/env python3
"""
Story world: a folk tale about a pitcher, a rhyme, teamwork, and a lesson learned.

A village pitcher wants to carry water to a thirsty garden. When a cracked path
and a leaky jug make the task seem impossible, a helpful rhyme guides a team
toward a clever repair.
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

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    village: str = "Willowmere"
    hero_name: str = "Luna"
    helper_name: str = "Mara"
    task: str = "carry water to the thirsty garden"
    obstacle: str = "cracked path"
    rhyme: str = "Many hands, one steady stream"
    telling_mode: str = "old tale opening"
    seed: Optional[int] = None


class World:
    def __init__(self, village: str) -> None:
        self.village = village
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


VILLAGES = {
    "Willowmere": "a village beside a silver stream",
    "Briar Glen": "a village tucked beneath green hills",
    "Sunspindle": "a village where golden wheat met the road",
    "Mossbell": "a village surrounded by cool forest",
}

HERO_NAMES = ["Luna", "Nia", "Tavi", "Milo", "Rin"]
HELPER_NAMES = ["Mara", "Pip", "Eli", "Suri", "Tomas"]

TASKS = [
    "carry water to the thirsty garden",
    "fill the village fountain before noon",
    "bring water to the baker's cooling oven",
    "help the new orchard's smallest trees",
]

OBSTACLES = {
    "cracked path": {
        "premise": "The path to the garden had cracked after a long, dry summer.",
        "mistake": "{hero} hurried over the broken stones, and the pitcher bumped against every ridge.",
        "clue": "{helper} noticed that the water spilled most whenever the pitcher crossed the deepest crack.",
        "change": "The team laid flat boards over the worst cracks and passed the pitcher hand to hand.",
        "result": "The water reached the garden in a bright, unbroken stream.",
        "lesson": "a difficult road is easier when people repair it together",
        "ending": "By sunset, the garden leaves stood up as if they were applauding.",
    },
    "leaky handle": {
        "premise": "The old pitcher's handle had loosened, and every lift made it drip.",
        "mistake": "{hero} gripped the handle harder, but the shaking only widened the little gap.",
        "clue": "{helper} saw a thin line of water shining beneath the handle's wooden peg.",
        "change": "The team wrapped the peg with willow fiber while two friends held the pitcher steady.",
        "result": "The repaired handle carried a full pitcher without losing a precious drop.",
        "lesson": "gentle care can mend what force would damage",
        "ending": "The willow fiber gleamed beside the handle like a small green crown.",
    },
    "steep hill": {
        "premise": "The spring stood above the village, reached by a steep and slippery hill.",
        "mistake": "{hero} tried to climb alone, and the heavy pitcher made each step wobble.",
        "clue": "{helper} saw that the safest steps were the ones marked by flat stones.",
        "change": "The team made a line, marked the flat stones, and passed the pitcher upward one careful step at a time.",
        "result": "The pitcher arrived full, and every helper stayed safely on the hill.",
        "lesson": "steady teamwork is stronger than lonely rushing",
        "ending": "The villagers drank beneath the spring while the hill path shone with wet footprints.",
    },
    "strong wind": {
        "premise": "A strong wind swept across the field between the spring and the village.",
        "mistake": "{hero} held the pitcher high, and the wind nearly pulled it from their arms.",
        "clue": "{helper} watched the grass bend and chose a lower path beside the stone wall.",
        "change": "The team walked close to the wall and shielded the pitcher with their woven baskets.",
        "result": "The water stayed calm even while the wind raced overhead.",
        "lesson": "wisdom means changing your plan when the world changes",
        "ending": "When the wind faded, the full pitcher reflected one peaceful cloud.",
    },
    "crowded bridge": {
        "premise": "The narrow bridge was crowded with villagers carrying baskets to market.",
        "mistake": "{hero} tried to squeeze through, and the pitcher's rim knocked against a basket.",
        "clue": "{helper} noticed that the bell at the bridge entrance signaled when the path was clear.",
        "change": "The team waited for the bell, crossed in a single line, and let others pass first.",
        "result": "No basket fell, and the pitcher reached the far bank safely.",
        "lesson": "patience makes room for everyone",
        "ending": "At market, even the busiest travelers raised a cup to the careful team.",
    },
}

RHYMES = [
    "Many hands, one steady stream",
    "Step by step, the drops stay bright",
    "Share the load and mend the road",
    "Slow feet keep the water sweet",
    "When friends unite, the path grows right",
]

ASP_RULES = r"""
pitcher(P) :- pitcher_name(P).
teamwork(T) :- team_name(T), joined(T).
rhyme(R) :- rhyme_name(R), remembered(R).
lesson_learned(H) :- hero(H), learned(H).
repaired(P) :- pitcher_state(P, repaired).
delivers(P) :- repaired(P), full(P), safe_path.
"""


def asp_facts() -> str:
    import asp

    return "\n".join([
        asp.fact("pitcher_name", "village_pitcher"),
        asp.fact("team_name", "water_team"),
        asp.fact("rhyme_name", "many_hands_one_stream"),
        asp.fact("hero", "hero"),
        asp.fact("joined", "water_team"),
        asp.fact("remembered", "many_hands_one_stream"),
        asp.fact("learned", "hero"),
        asp.fact("pitcher_state", "village_pitcher", "repaired"),
        asp.fact("full", "village_pitcher"),
        asp.fact("safe_path"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show pitcher/1.\n#show teamwork/1.\n#show rhyme/1.\n"
            "#show lesson_learned/1.\n#show delivers/1."
        )
    )
    found = {
        (sym.name, tuple(
            a.string if a.type == a.type.String
            else a.number if a.type == a.type.Number
            else a.name
            for a in sym.arguments
        ))
        for sym in model
    }
    wanted = {
        ("pitcher", ("village_pitcher",)),
        ("teamwork", ("water_team",)),
        ("rhyme", ("many_hands_one_stream",)),
        ("lesson_learned", ("hero",)),
        ("delivers", ("village_pitcher",)),
    }
    if found == wanted:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(found))
    print("PY :", sorted(wanted))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk tale about a pitcher, a rhyme, teamwork, and a lesson learned."
    )
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    village = args.village or rng.choice(list(VILLAGES))
    hero = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    if hero == helper:
        raise StoryError("The hero and helper must be different people.")
    return StoryParams(
        village=village,
        hero_name=hero,
        helper_name=helper,
        task=args.task or rng.choice(TASKS),
        obstacle=args.obstacle or rng.choice(list(OBSTACLES)),
        rhyme=args.rhyme or rng.choice(RHYMES),
        telling_mode="old tale opening",
    )


def generate(params: StoryParams) -> StorySample:
    if params.village not in VILLAGES:
        raise StoryError(f"Unknown village: {params.village}")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"Unknown obstacle: {params.obstacle}")
    if params.rhyme not in RHYMES:
        raise StoryError(f"Unknown rhyme: {params.rhyme}")
    if params.hero_name == params.helper_name:
        raise StoryError("The hero and helper must be different people.")

    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.village}:{params.hero_name}:{params.helper_name}:{params.obstacle}"
    )
    obstacle = OBSTACLES[params.obstacle]
    world = World(params.village)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        label=params.hero_name,
        phrase=f"young {params.hero_name}",
        meters={"strength": 0.4, "care": 0.6},
        memes={"worry": 0.0, "hope": 0.4},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        label=params.helper_name,
        phrase=f"neighbor {params.helper_name}",
        meters={"strength": 0.5, "care": 0.7},
        memes={"patience": 0.8, "trust": 0.5},
    ))
    pitcher = world.add(Entity(
        id="pitcher",
        kind="thing",
        label="pitcher",
        phrase=rng.choice([
            "a round clay pitcher with a blue stripe",
            "a sturdy earthen pitcher painted with leaves",
            "a little red pitcher with a wide mouth",
            "an old village pitcher polished by many hands",
        ]),
        owner="hero",
        meters={"fullness": 1.0, "leak": 0.6, "stability": 0.4},
        memes={"usefulness": 0.8, "worry": 0.3},
    ))

    world.say(
        f"Long ago, in {params.village}, {VILLAGES[params.village]}, "
        f"{params.hero_name} was asked to {params.task}."
    )
    world.say(
        f"{params.hero_name} lifted {pitcher.phrase} and said, "
        f"“I can carry it quickly.”"
    )
    world.say(
        f"{params.helper_name} smiled. “Quickly is not always safely. "
        f"Remember our rhyme: ‘{params.rhyme}.’”"
    )
    world.say(obstacle["premise"].format(hero=params.hero_name, helper=params.helper_name))
    world.say(obstacle["mistake"].format(hero=params.hero_name, helper=params.helper_name))
    pitcher.meters["leak"] = 1.0
    pitcher.meters["stability"] = 0.2
    pitcher.memes["worry"] = 1.0
    hero.memes["worry"] = 1.0
    world.say(
        f"“The pitcher is losing water!” cried {params.hero_name}. "
        f"“We will have nothing left to give.”"
    )
    world.say(
        f"“Then let us stop and look,” said {params.helper_name}. "
        f"“A rhyme is useful only when it guides our hands.”"
    )
    world.say(obstacle["clue"].format(hero=params.hero_name, helper=params.helper_name))
    world.say(
        f"The two friends invited nearby villagers to help. "
        f"One brought cord, one brought boards, and another carried a clean cloth."
    )
    world.say(
        f"Together they repeated, “{params.rhyme},” and each person took one small job."
    )

    pitcher.label = "repaired pitcher"
    pitcher.phrase = "a repaired pitcher ready for the village"
    pitcher.meters["leak"] = 0.0
    pitcher.meters["stability"] = 1.0
    pitcher.memes["worry"] = 0.0
    pitcher.memes["pride"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["hope"] = 1.0
    hero.memes["lesson"] = 1.0
    world.say(obstacle["change"].format(hero=params.hero_name, helper=params.helper_name))
    world.say(obstacle["result"].format(hero=params.hero_name, helper=params.helper_name))
    world.say(
        f"{params.hero_name} looked at the pitcher and said, "
        f"“I thought I had to do everything alone.”"
    )
    world.say(
        f"{params.helper_name} answered, “A shared task gives every helper a place.”"
    )
    world.say(
        f"Then {params.hero_name} understood the lesson learned: "
        f"{obstacle['lesson']}."
    )
    world.say(obstacle["ending"].format(hero=params.hero_name, helper=params.helper_name))

    world.facts.update(
        hero=hero,
        helper=helper,
        pitcher=pitcher,
        obstacle=params.obstacle,
        rhyme=params.rhyme,
        teamwork=True,
        repaired=True,
        lesson=obstacle["lesson"],
        delivered=True,
    )

    prompts = [
        f"Tell a folk tale about {params.hero_name} carrying a pitcher in {params.village}.",
        f"Use the rhyme “{params.rhyme}” to show how teamwork solves a problem.",
        f"Write a child-facing tale with a repaired pitcher and a clear lesson learned: {obstacle['lesson']}.",
    ]

    story_qa = [
        QAItem(
            question="What was the pitcher meant to carry?",
            answer=f"The pitcher was meant to carry water so {params.hero_name} could {params.task}.",
        ),
        QAItem(
            question="What problem interrupted the journey?",
            answer=obstacle["premise"],
        ),
        QAItem(
            question="What clue helped the friends understand the problem?",
            answer=obstacle["clue"].format(hero=params.hero_name, helper=params.helper_name),
        ),
        QAItem(
            question="How did teamwork solve the problem?",
            answer=obstacle["change"].format(hero=params.hero_name, helper=params.helper_name),
        ),
        QAItem(
            question="What lesson did the hero learn?",
            answer=f"{params.hero_name} learned that {obstacle['lesson']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a pitcher?",
            answer="A pitcher is a container with a handle and a spout, used for holding and pouring liquids.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people share jobs and help one another to reach a common goal.",
        ),
        QAItem(
            question="Why can a rhyme help someone remember a plan?",
            answer="A rhyme uses a pleasing pattern of sounds, which can make important words easier to remember.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for key, entity in sample.world.entities.items():
            print(f"{key}: {entity.label} meters={entity.meters} memes={entity.memes}")
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(
            "#show pitcher/1.\n#show teamwork/1.\n#show rhyme/1.\n"
            "#show lesson_learned/1.\n#show delivers/1."
        ))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for obstacle in OBSTACLES:
            params = StoryParams(
                village="Willowmere",
                hero_name="Luna",
                helper_name="Mara",
                task=TASKS[0],
                obstacle=obstacle,
                rhyme=RHYMES[0],
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
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
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
