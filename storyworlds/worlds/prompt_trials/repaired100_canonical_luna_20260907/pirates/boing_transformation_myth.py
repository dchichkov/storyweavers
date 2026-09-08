#!/usr/bin/env python3
"""
A tiny mythic storyworld about Boing, a springy creature who learns that
transformation is not the same as becoming someone else.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def meter(self, name: str) -> float:
        return self.meters.get(name, 0.0)

    def meme(self, name: str) -> float:
        return self.memes.get(name, 0.0)

    def add_meter(self, name: str, value: float) -> None:
        self.meters[name] = self.meter(name) + value

    def add_meme(self, name: str, value: float) -> None:
        self.memes[name] = self.meme(name) + value


@dataclass
class Transformation:
    id: str
    shape: str
    gift: str
    danger: str
    lesson: str


@dataclass
class StoryParams:
    hero: str
    companion: str
    mountain: str
    transformation: str
    moon_color: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.history.append(text)

    def render(self) -> str:
        return "\n\n".join(self.history)


TRANSFORMATIONS = {
    "eagle": Transformation(
        "eagle",
        "a silver-winged eagle",
        "the sight to see a true path",
        "the wind could carry the hero away",
        "a new shape can reveal a gift that was already inside",
    ),
    "river": Transformation(
        "river",
        "a bright, rushing river",
        "the strength to carry a lost moonstone home",
        "the current could sweep the hero into the dark gorge",
        "change can help us move forward without washing away who we are",
    ),
    "giant": Transformation(
        "giant",
        "a gentle stone giant",
        "the strength to lift the fallen gate",
        "great strength could crush the little things nearby",
        "being larger is useful only when the heart stays gentle",
    ),
}


def build_world(params: StoryParams) -> World:
    if params.transformation not in TRANSFORMATIONS:
        raise StoryError("Unknown transformation.")
    if not params.hero or not params.companion:
        raise StoryError("A myth needs both a hero and a companion.")
    if params.hero == params.companion:
        raise StoryError("The hero and companion must have different names.")

    trans = TRANSFORMATIONS[params.transformation]
    world = World()
    hero = world.add(Entity("hero", "character", params.hero, traits=["springy", "curious"]))
    companion = world.add(Entity("companion", "character", params.companion, traits=["wise", "kind"]))
    peak = world.add(Entity("peak", "place", params.mountain, traits=["steep", "ancient"]))
    moon = world.add(Entity("moonstone", "relic", "the moonstone", traits=["shining"]))
    hero.memes.update({"wonder": 1.0, "fear": 0.0, "belonging": 0.0})
    companion.memes.update({"wisdom": 1.0, "trust": 1.0})
    peak.meters.update({"distance": 1.0, "danger": 0.0})
    moon.meters.update({"lost": 1.0})
    world.facts.update(
        hero=hero,
        companion=companion,
        peak=peak,
        moon=moon,
        transformation=trans,
        transformed=False,
        recovered=False,
    )

    world.say(
        f"In the first age, when the {params.moon_color} moon still whispered to "
        f"the mountains, {params.hero} lived beneath {params.mountain}."
    )
    world.say(
        f"{params.hero} was small, bright-eyed, and made a joyful sound whenever "
        f"the world surprised them: “Boing!”"
    )
    world.say(
        f"One night, the moonstone rolled from the sky and fell beyond the "
        f"highest ridge. Without it, the valley's flowers folded their faces."
    )
    world.say(
        f'"I will bring it back," said {params.hero}. "But I am only Boing. '
        f'What can I do?"'
    )
    world.say(
        f'"You can begin," said {params.companion}. "The mountain does not ask '
        f'who you were. It asks what you are willing to become."'
    )
    hero.add_meme("courage", 1.0)
    companion.add_meme("trust", 1.0)

    world.say(
        f"At the first cliff, the path broke. {params.hero} sprang once, twice, "
        f"and a third time. “Boing!” Each leap carried them closer, but the gap "
        f"was wider than any leap before."
    )
    peak.add_meter("danger", 1.0)
    world.say(
        f"Then the old mountain breathed a golden breath. {params.hero} changed "
        f"into {trans.shape}."
    )
    world.facts["transformed"] = True
    hero.add_meme("fear", 1.0)
    hero.add_meme("belonging", 1.0)
    world.say(
        f"{params.hero} cried, “Am I still me?”"
    )
    world.say(
        f"{params.companion} answered, “Listen. Your heart still remembers the "
        f"sound of Boing. A new shape is a door, not a stolen name.”"
    )
    hero.add_meme("fear", -1.0)
    hero.add_meme("courage", 1.0)

    world.say(
        f"With {trans.gift}, {params.hero} crossed the broken path. At the far "
        f"side, the moonstone lay beside {trans.danger}."
    )
    moon.meters["lost"] = 0.0
    world.facts["recovered"] = True
    world.say(
        f"{params.hero} lifted the moonstone, and the valley bloomed beneath the "
        f"{params.moon_color} moon."
    )
    world.say(
        f"Before dawn, the golden breath faded. {params.hero} returned to the "
        f"little creature who could leap and laugh and shout, “Boing!”"
    )
    hero.add_meme("belonging", 1.0)
    world.say(
        f"From that day on, the people remembered this truth: {trans.lesson}"
    )
    world.say(
        f"And whenever someone in the valley changed, {params.hero} smiled and "
        f"said, “A transformation is a journey. It is not the end of your name.”"
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].label
    companion = f["companion"].label
    trans = f["transformation"]
    return [
        f"Tell a myth about {hero}, who says boing and transforms into {trans.shape}.",
        f"Write a gentle transformation myth where {hero} asks {companion}, "
        f"“Am I still me?” and learns that change can reveal an inner gift.",
        f"Create a child-facing myth in which a magical transformation helps {hero} "
        f"recover the moonstone, followed by a clear lesson about identity.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    companion = f["companion"].label
    peak = f["peak"].label
    trans = f["transformation"]
    return [
        QAItem(
            f"Who was {hero}?",
            f"{hero} was a small, curious creature who loved to leap and make the sound “Boing!”",
        ),
        QAItem(
            f"Why did {hero} climb {peak}?",
            f"{hero} climbed {peak} to recover the moonstone that had fallen from the sky and help the valley's flowers bloom again.",
        ),
        QAItem(
            f"What transformation happened to {hero}?",
            f"{hero} transformed into {trans.shape}, a new shape that gave {hero} {trans.gift}.",
        ),
        QAItem(
            f"What did {companion} teach {hero}?",
            f"{companion} taught {hero} that a new shape is a door, not a stolen name, so transformation does not erase who someone is.",
        ),
        QAItem(
            "How did the myth end?",
            f"{hero} recovered the moonstone, returned home, changed back, and remembered that {trans.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    trans = world.facts["transformation"]
    return [
        QAItem(
            "What is a transformation?",
            "A transformation is a change in shape, state, or appearance. In a story, it can also reveal a new ability.",
        ),
        QAItem(
            "Does changing always mean becoming a different person?",
            "No. Someone can change while still keeping their memories, values, and identity.",
        ),
        QAItem(
            "Why can myths use magic?",
            "Myths use magic to make big ideas, such as courage or identity, visible through wonderful events.",
        ),
        QAItem(
            "What did the magical shape provide?",
            f"It provided {trans.gift}, but the hero still had to choose how to use that gift kindly.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
transformation(eagle).
transformation(river).
transformation(giant).
boing(hero).
valid(T) :- transformation(T).
recovered :- transformed, courageous.
"""


def asp_facts() -> str:
    import importlib
    asp = importlib.import_module("asp")
    return "\n".join(
        [
            asp.fact("boing", "hero"),
            *[asp.fact("transformation", key) for key in TRANSFORMATIONS],
        ]
    )


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def verify_asp() -> int:
    try:
        import importlib
        asp = importlib.import_module("asp")
        model = asp.one_model(asp_program("#show transformation/1."))
        found = {x[0] for x in asp.atoms(model, "transformation")}
        expected = set(TRANSFORMATIONS)
        if found != expected:
            print("ASP mismatch.")
            return 1
        print("OK: ASP transformation registry matches Python.")
        for name in ("eagle", "river", "giant"):
            sample = generate(
                StoryParams("Luna", "Milo", "Mount Luma", name, "blue")
            )
            if "Boing" not in sample.story or "transformed" not in sample.story.lower():
                print("Generated story verification failed.")
                return 1
        print("OK: generated stories contain the transformation arc.")
        return 0
    except ImportError:
        print("ASP verification requires clingo.")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A myth of Boing and transformation.")
    parser.add_argument("--hero")
    parser.add_argument("--companion")
    parser.add_argument("--mountain")
    parser.add_argument("--transformation", choices=sorted(TRANSFORMATIONS))
    parser.add_argument("--moon-color", default=None)
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
    heroes = ["Luna", "Nia", "Tavi", "Mara", "Pip"]
    companions = ["Milo", "Suri", "Orin", "Tala", "Kito"]
    mountains = ["Mount Luma", "the Singing Peak", "Cloudback Mountain"]
    colors = ["blue", "silver", "violet", "golden"]
    hero = args.hero or rng.choice(heroes)
    companion = args.companion or rng.choice([x for x in companions if x != hero])
    if hero == companion:
        raise StoryError("Hero and companion must have different names.")
    return StoryParams(
        hero=hero,
        companion=companion,
        mountain=args.mountain or rng.choice(mountains),
        transformation=args.transformation or rng.choice(sorted(TRANSFORMATIONS)),
        moon_color=args.moon_color or rng.choice(colors),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id}: kind={entity.kind}, meters={meters}, memes={memes}, traits={entity.traits}"
        )
    lines.append(f"facts: transformed={world.facts['transformed']}, recovered={world.facts['recovered']}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        raise SystemExit(verify_asp())
    if args.show_asp:
        print(asp_program("#show transformation/1."))
        return
    if args.asp:
        try:
            import importlib
            asp = importlib.import_module("asp")
            model = asp.one_model(asp_program("#show transformation/1."))
            print("\n".join(str(x) for x in model))
        except ImportError:
            print("ASP mode requires clingo.")
        return

    rng = random.Random(args.seed)
    samples: list[StorySample] = []
    count = len(TRANSFORMATIONS) if args.all else args.n
    for i in range(count):
        if args.all:
            transformation = sorted(TRANSFORMATIONS)[i]
            params = StoryParams(
                hero=["Luna", "Nia", "Tavi"][i],
                companion=["Milo", "Suri", "Orin"][i],
                mountain=["Mount Luma", "the Singing Peak", "Cloudback Mountain"][i],
                transformation=transformation,
                moon_color=["blue", "silver", "violet"][i],
                seed=args.seed,
            )
        else:
            params = resolve_params(args, rng)
            params.seed = args.seed
        samples.append(generate(params))

    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if index:
            print("\n" + "=" * 70 + "\n")
        emit(sample, trace=args.trace, qa=args.qa)


if __name__ == "__main__":
    main()
