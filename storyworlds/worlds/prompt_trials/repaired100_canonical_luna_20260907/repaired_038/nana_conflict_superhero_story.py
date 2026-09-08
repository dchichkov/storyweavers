#!/usr/bin/env python3
"""
A tiny superhero storyworld about Nana, a brave helper, and a conflict that
must be solved with listening, teamwork, and a careful choice.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Conflict:
    id: str
    opening: str
    problem: str
    power: str
    danger: str
    clue: str
    repair: str
    ending: str


@dataclass
class StoryParams:
    hero: str
    hero_kind: str
    power: str
    conflict: str
    place: str
    motto: int
    seed: Optional[int] = None


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


CONFLICTS = {
    "bridge_shadow": Conflict(
        "bridge_shadow",
        "At sunset, Nana and the young hero patrolled the town bridge.",
        "A huge shadow creature blocked the bridge and shouted that nobody could cross.",
        "the hero could make a bright shield from a flash of courage",
        "The shadow spread toward the traffic lights and made every road look dark.",
        "The creature was guarding a lost silver bell beneath the bridge.",
        "Nana held the lantern steady while the hero listened, found the bell, and returned it.",
        "The shadow shrank into a friendly little shape, and the bridge lights blinked on.",
    ),
    "garden_roar": Conflict(
        "garden_roar",
        "One breezy morning, Nana and the young hero visited the community garden.",
        "A roaring vine curled around the gate and refused to let anyone enter.",
        "the hero could lift a wind wall when someone nearby needed protection",
        "The vine's thorns whipped at the seed table and scattered tiny seeds.",
        "The vine was frightened because its bright watering can had rolled away.",
        "Nana spoke softly while the hero used the wind wall to bring the can back.",
        "The vine loosened its grip, and new flowers opened along the safe garden path.",
    ),
    "clocktower_battle",
    "library_storm",
    "market_mist",
}

CONFLICTS["clocktower_battle"] = Conflict(
    "clocktower_battle",
    "Before breakfast, Nana and the young hero heard a clang from the old clocktower.",
    "A metal guardian stood at the door and challenged everyone to a noisy battle.",
    "the hero could freeze a dangerous object for three heartbeats",
    "The guardian's swinging arms shook loose bricks above the square.",
    "It believed the clocktower bell had been stolen.",
    "Nana asked questions while the hero froze the swinging arms and checked the bell room.",
    "The bell was safe, the guardian bowed, and the clock struck a gentle hour.",
)

CONFLICTS["library_storm"] = Conflict(
    "library_storm",
    "During a rainy afternoon, Nana and the young hero entered the town library.",
    "A storm of flying books whirled around the reading room and yelled for everyone to leave.",
    "the hero could make a quiet bubble around people and fragile things",
    "The books were bumping the tall shelves and shaking dust onto the floor.",
    "A lonely storybook had been left open with no one reading its last page.",
    "Nana read the final page aloud while the hero sheltered the shelves in a quiet bubble.",
    "The books settled into their places, and the lonely storybook gained a new bookmark.",
)

CONFLICTS["market_mist"] = Conflict(
    "market_mist",
    "At noon, Nana and the young hero helped at the sunny town market.",
    "A thick purple mist covered the stalls and made each shopkeeper blame the next one.",
    "the hero could send a clear beam through confusion",
    "People were tripping over baskets because nobody could see the market lane.",
    "A broken perfume bottle had filled the mist with a sharp, confusing scent.",
    "Nana guided everyone apart while the hero found the bottle and opened the roof vents.",
    "The mist floated away, and the shopkeepers shared fruit while repairing the stall.",
)

HERO_NAMES = ["Milo", "Luna", "Ravi", "Tess", "Jo", "Ari"]
HERO_KINDS = ["boy", "girl", "child"]
POWERS = ["bright shield", "wind wall", "freezing touch", "quiet bubble", "clear beam"]
PLACES = ["the town", "Harbor Hill", "Maple City", "Sunbeam Village"]
MOTTOS = [
    "A real hero listens before leaping.",
    "Courage grows when it is shared.",
    "A conflict can change when someone makes room for the truth.",
    "Helping is stronger than winning.",
    "The bravest power is a careful question.",
]


def _set(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = value


def _add_meme(entity: Entity, key: str, value: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + value


def tell(params: StoryParams) -> World:
    conflict = CONFLICTS[params.conflict]
    world = World(params.place)
    hero = world.add(Entity(params.hero, "character", params.hero))
    nana = world.add(Entity("nana", "character", "Nana"))
    rival = world.add(Entity("conflict", "opponent", "the conflicted guardian"))
    world.facts.update(hero=hero, nana=nana, rival=rival, conflict=conflict)

    world.say(
        f"{conflict.opening} {params.hero} was a {params.hero_kind} superhero with a "
        f"{params.power}, and Nana was the wisest teammate in {params.place}."
    )
    world.say(conflict.problem)
    world.say(conflict.danger)
    _set(rival, "danger", 1.0)
    _add_meme(hero, "worry", 1.0)
    world.para()

    world.say(
        f'"Nana, should I blast it away?" {params.hero} asked. '
        f'"Not yet," Nana replied. "A conflict has more than one side. '
        f'Let us learn what is wrong."'
    )
    world.say(
        f"Nana listened from a safe distance. {conflict.clue} "
        f"That clue changed the hero's plan."
    )
    _set(rival, "danger", 0.5)
    _add_meme(hero, "understanding", 1.0)
    world.fired.add("listen")

    world.say(
        f'"I hear you," said {params.hero}. "We will help without hurting anyone." '
        f'"That is superhero thinking," Nana said.'
    )
    world.say(conflict.repair)
    _set(rival, "danger", 0.0)
    _set(hero, "power_used", 1.0)
    _add_meme(hero, "confidence", 1.0)
    _add_meme(nana, "pride", 1.0)
    world.fired.add("repair")

    world.say(conflict.ending)
    world.say(f"Nana smiled. "{MOTTOS[params.motto % len(MOTTOS)]}"")
    world.para()
    world.say(
        f"As the evening settled over {params.place}, {params.hero} lowered the {params.power}. "
        "The hero had not won by overpowering a foe. The hero had turned a conflict "
        "into a rescue by listening, asking, and helping."
    )
    world.facts["resolved"] = True
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [(cid, power) for cid in CONFLICTS for power in POWERS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    conflict = args.conflict or rng.choice(sorted(CONFLICTS))
    power = args.power or rng.choice(POWERS)
    if conflict not in CONFLICTS:
        raise StoryError(f"Unknown conflict: {conflict}")
    if power not in POWERS:
        raise StoryError(f"Unknown superhero power: {power}")
    return StoryParams(
        hero=args.hero or rng.choice(HERO_NAMES),
        hero_kind=args.hero_kind or rng.choice(HERO_KINDS),
        power=power,
        conflict=conflict,
        place=args.place or rng.choice(PLACES),
        motto=rng.randrange(len(MOTTOS)),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c: Conflict = f["conflict"]
    return [
        f"Write a superhero story about {f['hero'].id}, Nana, and the conflict called {c.id.replace('_', ' ')}.",
        f"Tell a child-friendly superhero adventure where Nana helps {f['hero'].id} solve a conflict without hurting anyone.",
        f"Write a story featuring a {f['hero'].meters.get('power_used', 0) and 'carefully used' or 'ready'} superhero power, a misunderstanding, and a happy repair.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c: Conflict = f["conflict"]
    hero: Entity = f["hero"]
    return [
        QAItem(
            f"Who helped {hero.id} face the conflict?",
            f"Nana helped {hero.id}. Nana encouraged the hero to listen before using a superhero power.",
        ),
        QAItem(
            "What was the main conflict?",
            f"{c.problem} The conflict seemed dangerous because {c.danger}",
        ),
        QAItem(
            "What clue changed the hero's plan?",
            c.clue,
        ),
        QAItem(
            "How was the conflict repaired?",
            c.repair,
        ),
        QAItem(
            "What showed that the story ended safely?",
            c.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a conflict?",
            "A conflict is a disagreement, problem, or struggle between people, creatures, or goals.",
        ),
        QAItem(
            "Why is listening useful during a conflict?",
            "Listening can reveal what someone needs or fears, so people can choose a safer and fairer solution.",
        ),
        QAItem(
            "What does a superhero do in this storyworld?",
            "A superhero uses special abilities responsibly to protect others, solve problems, and repair harm.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
conflict(C) :- conflict_id(C).
hero_power(P) :- power(P).
valid_story(C,P) :- conflict(C), hero_power(P), listens_before_action.
"""


def asp_facts() -> str:
    import asp

    lines = ["listens_before_action."]
    for cid in CONFLICTS:
        lines.append(asp.fact("conflict_id", cid))
    for power in POWERS:
        lines.append(asp.fact("power", power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_pairs = set(valid_combos())
    asp_pairs = set(asp_valid_combos())
    if python_pairs == asp_pairs:
        print(f"OK: clingo gate matches valid_combos() ({len(python_pairs)} combos).")
        return 0
    print("MISMATCH between clingo and Python.")
    print("Only in Python:", sorted(python_pairs - asp_pairs))
    print("Only in ASP:", sorted(asp_pairs - python_pairs))
    return 1


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nana superhero conflict storyworld."
    )
    parser.add_argument("--hero")
    parser.add_argument("--hero-kind", choices=HERO_KINDS)
    parser.add_argument("--power", choices=POWERS)
    parser.add_argument("--conflict", choices=sorted(CONFLICTS))
    parser.add_argument("--place")
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


CURATED = [
    StoryParams(
        hero="Luna",
        hero_kind="girl",
        power="bright shield",
        conflict="bridge_shadow",
        place="Maple City",
        motto=0,
    ),
    StoryParams(
        hero="Milo",
        hero_kind="boy",
        power="quiet bubble",
        conflict="library_storm",
        place="the town",
        motto=3,
    ),
    StoryParams(
        hero="Ravi",
        hero_kind="child",
        power="wind wall",
        conflict="garden_roar",
        place="Sunbeam Village",
        motto=1,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
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
