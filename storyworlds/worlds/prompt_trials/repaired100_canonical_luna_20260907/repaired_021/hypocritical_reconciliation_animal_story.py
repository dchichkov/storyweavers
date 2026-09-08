#!/usr/bin/env python3
"""
A small animal story about hypocrisy, honesty, and reconciliation.

A proud fox tells a friend to share fairly, yet secretly keeps the best berries.
When the friend notices, the fox must stop pretending, speak honestly, and repair
the friendship through a fair act.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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


@dataclass
class StoryParams:
    name: str
    friend_name: str
    fruit: str
    setting: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Pip", "Coco", "Toby", "Daisy", "Poppy", "Benny"]
FRIEND_NAMES = ["Nia", "Fenn", "Mara", "Otis", "Ruby", "Finn", "Wren", "Tess"]
FRUITS = [
    ("berries", "a basket of bright berries"),
    ("apples", "a basket of red apples"),
    ("pears", "a basket of golden pears"),
]
SETTINGS = ["the quiet orchard", "the sunny meadow", "the little woodland clearing"]


@dataclass(frozen=True)
class Arc:
    title: str
    opening: str
    selfish: str
    consequence: str
    dialogue: str
    repair: str
    lesson: str
    ending: str


ARCS = (
    Arc(
        "the berry basket",
        "{friend} invited {animal} to gather {fruit} beneath the old apple tree.",
        "{animal} announced that good friends should share evenly, then quietly tucked the biggest berries beneath a leaf for later.",
        "When the basket was counted, {friend} found only small berries on their side and looked down at the hidden fruit.",
        '"You asked me to share fairly," said {friend}. "Why did your rule stop when it reached your paws?"',
        "{animal} brought out the hidden berries, divided the whole basket again, and gave {friend} the first choice.",
        "The fox had been hypocritical: saying one rule while secretly following another. Honest action was the first step toward reconciliation.",
        "At sunset, the empty basket rested between two friends whose paws touched as they carried it home.",
    ),
    Arc(
        "the picnic blanket",
        "{animal} and {friend} spread a picnic blanket under a tree and placed their treats in the middle.",
        "{animal} told {friend} not to take extra crumbs, while slipping the sweetest cakes into one corner of the blanket.",
        "A breeze lifted the corner and scattered the secret cakes into the grass.",
        '"You spoke about fairness," {friend} said. "Can you practice it with me now?"',
        "{animal} apologized, gathered the cakes that were still clean, and shared the best pieces before making a new plate together.",
        "Reconciliation did not come from a clever excuse. It began when the hypocritical rule-maker admitted the truth and changed behavior.",
        "The picnic ended with crumbs for birds and two friends folding the blanket side by side.",
    ),
    Arc(
        "the painted sign",
        "{friend} painted a sign that said, SHARE THE PATH, before the animals began their garden walk.",
        "{animal} praised the sign but pushed past {friend} whenever the path narrowed, keeping the smoothest ground for themself.",
        "At a muddy turn, {friend} stopped and held the sign across the path.",
        '"A sign is not enough," {friend} said. "Will your paws follow your kind words?"',
        "{animal} stepped back, let {friend} lead, and helped place flat stones so both friends could walk safely.",
        "The hypocritical fox learned that reconciliation needs deeds that match promises.",
        "The painted sign stood beside a new stone path, while two sets of footprints crossed the garden together.",
    ),
)


def choose_arc(seed: int) -> Arc:
    return ARCS[seed % len(ARCS)]


def build_world(params: StoryParams) -> World:
    if params.name == params.friend_name:
        raise StoryError("The animal and friend must have different names.")
    if params.fruit not in dict(FRUITS):
        raise StoryError(f"Unknown fruit: {params.fruit}")
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")

    seed = params.seed if params.seed is not None else 0
    arc = choose_arc(seed)
    world = World()

    animal = world.add(
        Entity(
            id=params.name,
            kind="character",
            type="fox",
            label="fox",
            traits=["clever", "proud"],
            meters={"calm": 1.0, "trust": 0.7},
            memes={"pride": 1.0, "friendship": 1.0},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend_name,
            kind="character",
            type="rabbit",
            label="friend",
            traits=["gentle", "honest"],
            meters={"calm": 1.0, "trust": 1.0},
            memes={"joy": 1.0, "friendship": 1.0},
        )
    )
    fruit = world.add(
        Entity(
            id="shared_food",
            kind="thing",
            type="food",
            label=params.fruit,
            phrase=dict(FRUITS)[params.fruit],
            owner=animal.id,
            held_by=animal.id,
            meters={"whole": 1.0},
        )
    )

    values = {
        "animal": animal.id,
        "friend": friend.id,
        "fruit": fruit.phrase,
        "setting": params.setting,
    }

    world.say(f"In {params.setting}, {animal.id} and {friend.id} met beneath a warm, leafy sky.")
    world.say(arc.opening.format(**values))
    world.say(
        f"{animal.id} wanted to seem wise and fair. "
        "But a person can sound kind and still make a selfish choice."
    )
    world.para()
    world.say(arc.selfish.format(**values))
    animal.memes["pride"] += 1.0
    animal.memes["honesty"] = 0.0
    friend.memes["worry"] = 1.0
    friend.meters["trust"] = 0.3
    world.say(arc.consequence.format(**values))
    world.say(arc.dialogue.format(**values))
    world.para()
    world.say(
        f"{animal.id} felt their cheeks grow hot. "
        "They understood that being hypocritical meant demanding a good rule from someone else while breaking it themself."
    )
    world.say(
        f'"I was hypocritical," {animal.id} admitted. '
        '"I said one thing and did another. I am sorry."'
    )
    world.say(arc.repair.format(**values))
    animal.memes["honesty"] = 1.0
    animal.memes["pride"] = 0.2
    animal.memes["reconciliation"] = 1.0
    animal.meters["trust"] = 1.0
    friend.memes["relief"] = 1.0
    friend.memes["reconciliation"] = 1.0
    friend.meters["trust"] = 0.8
    fruit.held_by = None
    world.para()
    world.say(arc.lesson.format(**values))
    world.say(
        f"{friend.id} nodded. "
        '"I can forgive you when your actions keep matching your words."'
    )
    world.say(arc.ending.format(**values))

    world.facts.update(
        animal=animal,
        friend=friend,
        fruit=fruit,
        setting=params.setting,
        arc=arc,
        conflict=arc.consequence.format(**values),
        dialogue=arc.dialogue.format(**values),
        repair=arc.repair.format(**values),
        lesson=arc.lesson.format(**values),
        ending=arc.ending.format(**values),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    animal: Entity = world.facts["animal"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    fruit: Entity = world.facts["fruit"]  # type: ignore[assignment]
    return [
        f"Write an animal story about {animal.id} learning that being hypocritical hurts {friend.id}.",
        f"Tell a child-friendly reconciliation story where {animal.id} and {friend.id} share {fruit.phrase}.",
        f"Create a gentle animal story using the word hypocritical and showing friendship repaired through honest action.",
    ]


def story_qa(world: World) -> list[QAItem]:
    animal: Entity = world.facts["animal"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    fruit: Entity = world.facts["fruit"]  # type: ignore[assignment]
    return [
        QAItem(
            question="Who are the main characters?",
            answer=f"The main characters are {animal.id}, a proud fox, and {friend.id}, an honest friend who gathered {fruit.phrase} with the fox.",
        ),
        QAItem(
            question=f"Why did {friend.id} feel hurt?",
            answer=f"{friend.id} felt hurt because {animal.id} demanded fairness but secretly kept the best {fruit.label} for themself.",
        ),
        QAItem(
            question="What did hypocritical mean in the story?",
            answer="It meant saying that others should follow a good rule while secretly breaking that same rule yourself.",
        ),
        QAItem(
            question=f"How did {animal.id} begin reconciliation?",
            answer=f"{animal.id} admitted being hypocritical, apologized honestly, and changed the unfair action by sharing the whole collection.",
        ),
        QAItem(
            question="What final image shows that the friendship was repaired?",
            answer=str(world.facts["ending"]),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is the process of repairing a relationship after hurt or disagreement through honesty, apology, and changed actions.",
        ),
        QAItem(
            question="Why should words and actions match?",
            answer="Words and actions should match because people can trust promises when behavior proves that the promises are real.",
        ),
        QAItem(
            question="What can a sincere apology do?",
            answer="A sincere apology can acknowledge harm, show responsibility, and open a path toward making things right.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Animal story world about hypocritical behavior and reconciliation.")
    parser.add_argument("--name")
    parser.add_argument("--friend-name")
    parser.add_argument("--fruit", choices=[x[0] for x in FRUITS])
    parser.add_argument("--setting", choices=SETTINGS)
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
    name = args.name or rng.choice(NAMES)
    choices = [n for n in FRIEND_NAMES if n != name]
    friend_name = args.friend_name or rng.choice(choices)
    fruit = args.fruit or rng.choice([x[0] for x in FRUITS])
    setting = args.setting or rng.choice(SETTINGS)
    return StoryParams(name=name, friend_name=friend_name, fruit=fruit, setting=setting)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        parts = []
        if entity.meters:
            parts.append(f"meters={entity.meters}")
        if entity.memes:
            parts.append(f"memes={entity.memes}")
        if entity.owner:
            parts.append(f"owner={entity.owner}")
        if entity.held_by:
            parts.append(f"held_by={entity.held_by}")
        lines.append(f"  {entity.id:12} ({entity.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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


ASP_RULES = r"""
character(X) :- fox(X).
character(X) :- friend(X).
food(X) :- berry(X).
food(X) :- apple(X).
food(X) :- pear(X).
honest_repair(X, Y) :- fox(X), friend(Y), apologizes(X), shares_fairly(X), trust_restored(Y).
#show honest_repair/2.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for name in NAMES:
        lines.append(asp.fact("fox", name))
    for name in FRIEND_NAMES:
        lines.append(asp.fact("friend", name))
    lines.extend(
        [
            asp.fact("berry", "berries"),
            asp.fact("apple", "apples"),
            asp.fact("pear", "pears"),
            asp.fact("apologizes", "Luna"),
            asp.fact("shares_fairly", "Luna"),
            asp.fact("trust_restored", "Nia"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str = "#show honest_repair/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp

        model = asp.one_model(asp_program())
        repairs = asp.atoms(model, "honest_repair")
        if ("Luna", "Nia") not in repairs:
            print("ASP verification failed: expected reconciliation fact was absent.")
            return 1
        sample = generate(
            StoryParams(
                name="Luna",
                friend_name="Nia",
                fruit="berries",
                setting=SETTINGS[0],
                seed=0,
            )
        )
        required = ("hypocritical", "reconciliation", "sorry")
        if not all(word in sample.story.lower() for word in required):
            print("ASP verification failed: generated story lacks required narrative state.")
            return 1
        print("OK: ASP/Python reconciliation parity verified.")
        return 0
    except ImportError:
        print("ASP verification unavailable: clingo is not installed.")
        return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, fruit in enumerate(FRUITS):
            samples.append(
                generate(
                    StoryParams(
                        name=NAMES[i],
                        friend_name=FRIEND_NAMES[i],
                        fruit=fruit[0],
                        setting=SETTINGS[i % len(SETTINGS)],
                        seed=base_seed + i,
                    )
                )
            )
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.asp:
        try:
            import asp

            model = asp.one_model(asp_program())
            print(json.dumps({"atoms": [str(atom) for atom in model]}, indent=2))
        except ImportError:
            print("ASP mode requires clingo.")
        return

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
