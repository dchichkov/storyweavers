#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about drift, a quarrel, and a change of heart.

Luna wants to carry a moon-white ribbon across a pond for a rhyme. A gust
drifts it away, and a misunderstanding makes two friends blame each other.
A small transformation reveals the truth: a bent twig becomes a little hook,
and the friends work together to bring the ribbon home.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
ROOT = next((p for p in HERE.parents if (p / "results.py").is_file()), HERE.parent)
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


NAME_POOL = ["Luna", "Milo", "Nia", "Toby", "Pip", "Iris"]
HELPER_POOL = ["Robin", "Mara", "Bramble", "Ollie"]
PLACE_POOL = ["the lily pond", "the moonlit meadow", "the reed bridge", "the silver garden"]
OBJECT_POOL = ["moon-white ribbon", "blue bell", "paper crown", "golden thread"]

SCENES = [
    {
        "object": "moon-white ribbon",
        "goal": "tie a bright bow beside the pond",
        "drift": "A puff of wind made the ribbon drift across the water.",
        "misunderstanding": "Luna thought Robin had let go on purpose, while Robin thought Luna had pulled it away.",
        "conflict": "“You pulled!” cried Luna. “You pushed!” cried Robin.",
        "clue": "a small reed bent toward the ribbon, showing that the wind had nudged it",
        "transform": "a bent reed became a little hook",
        "action": "They used the reed hook together, one guiding and one pulling.",
        "resolution": "The ribbon came home, and the bow shone like a small moon.",
        "ending": "Tip-tap, clap-clap, under the willow tree, the bow danced happily and the friends danced free.",
    },
    {
        "object": "blue bell",
        "goal": "hang a tiny bell above the meadow path",
        "drift": "A warm breeze made the blue bell drift from its string into the tall grass.",
        "misunderstanding": "Milo thought Nia had hidden the bell as a trick, while Nia thought Milo had tossed it away.",
        "conflict": "“You hid it!” said Milo. “You threw it!” said Nia.",
        "clue": "a line of shining dew led from the path toward the grass",
        "transform": "a long grass stem became a gentle bell-finder",
        "action": "They followed the dew and lifted the bell with the strong grass stem.",
        "resolution": "The bell was found and hung where its soft ring could guide everyone home.",
        "ending": "Ding-dong, sing-song, by the path so bright, the blue bell chimed a good-night light.",
    },
    {
        "object": "paper crown",
        "goal": "place a paper crown on the garden scarecrow",
        "drift": "A sudden breeze made the paper crown drift beneath the pumpkin leaves.",
        "misunderstanding": "Pip thought Mara had torn it, while Mara thought Pip had hidden it.",
        "conflict": "“You spoiled my crown!” cried Pip. “You took my crown!” cried Mara.",
        "clue": "one silver paper star was caught on a leaf near the scarecrow",
        "transform": "a broad leaf became a scoop",
        "action": "They used the leaf scoop to lift the crown without tearing it.",
        "resolution": "The crown rested on the scarecrow, and its bent point looked proudly playful.",
        "ending": "Crown up, leaves down, round and round the pumpkins smiled, while peace came skipping through the wild.",
    },
    {
        "object": "golden thread",
        "goal": "weave a shining line through the garden gate",
        "drift": "A breath of air made the golden thread drift into a thorny rosebush.",
        "misunderstanding": "Iris thought Ollie had tugged too hard, while Ollie thought Iris had dropped the thread.",
        "conflict": "“You pulled it tight!” said Iris. “You dropped it first!” said Ollie.",
        "clue": "the thorns had caught only the loose loop, not the whole thread",
        "transform": "a fallen feather became a soft thread-pusher",
        "action": "They used the feather to loosen the loop and guide the thread out.",
        "resolution": "The thread slipped free and made a golden path through the gate.",
        "ending": "Twist and twine, the garden shone; two calm friends walked safely home.",
    },
]


@dataclass
class StoryParams:
    name: str = "Luna"
    helper: str = "Robin"
    place: str = "the lily pond"
    object_name: str = "moon-white ribbon"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("distance", "drift", "tension", "visibility"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "anger", "confusion", "relief", "trust", "joy"):
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


def stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate(
        f"{params.name}|{params.helper}|{params.place}|{params.object_name}"
    ))


def tell_world(params: StoryParams) -> World:
    rng = random.Random(stable_seed(params))
    scene = next((s for s in SCENES if s["object"] == params.object_name), None)
    if scene is None:
        raise StoryError(f"Unknown story object: {params.object_name}")

    w = World(place=params.place)
    child = w.add(Entity("child", "character", params.name))
    friend = w.add(Entity("friend", "character", params.helper))
    object_ent = w.add(Entity("focus", "object", scene["object"]))
    wind = w.add(Entity("wind", "force", "a playful breeze"))
    w.facts.update(scene=scene, child=child, friend=friend, focus=object_ent, wind=wind)

    rhyme_openers = [
        f"By {params.place}, where the small reeds swayed, {params.name} and {params.helper} made a bright parade.",
        f"At {params.place}, in a silver tune, {params.name} and {params.helper} played beneath the moon.",
        f"Near {params.place}, with a hop and a beat, {params.name} and {params.helper} prepared something neat.",
    ]
    w.say(rng.choice(rhyme_openers))
    w.say(f"They planned to {scene['goal']}, singing a little rhyme as they worked.")
    w.say(f"“Ready, steady, one-two-three!” said {params.name}. “Together,” said {params.helper}.")
    w.para()

    child.meters["distance"] = 2
    child.meters["drift"] = 1
    friend.meters["distance"] = 2
    wind.meters["drift"] = 3
    object_ent.meters["distance"] = 5
    child.memes["worry"] = 1
    friend.memes["worry"] = 1
    w.say(scene["drift"])
    w.say(f"The {scene['object']} floated farther and farther, just beyond their reach.")
    w.say(scene["misunderstanding"])
    w.say(scene["conflict"])
    child.memes["anger"] = 2
    friend.memes["anger"] = 2
    child.memes["confusion"] = 2
    friend.memes["confusion"] = 2
    w.para()

    w.say(f"Then {params.name} stopped and looked closely.")
    w.say(f"{params.name} noticed that {scene['clue']}.")
    w.say(f"“Wait,” said {params.name}. “Maybe neither of us did it.”")
    w.say(f"“Maybe the breeze did,” said {params.helper}. “Let us mend the matter together.”")
    w.say(f"The {scene['transform']}.")

    child.meters["visibility"] = 2
    friend.meters["visibility"] = 2
    object_ent.meters["distance"] = 1
    child.memes["confusion"] = 0
    friend.memes["confusion"] = 0
    child.memes["anger"] = 0
    friend.memes["anger"] = 0
    child.memes["trust"] = 2
    friend.memes["trust"] = 2
    w.say(scene["action"])
    w.say(scene["resolution"])
    w.say(f"“I am sorry I blamed you,” said {params.name}.")
    w.say(f"“I am sorry I blamed you too,” said {params.helper}.")
    child.memes["relief"] = 2
    friend.memes["relief"] = 2
    child.memes["joy"] = 2
    friend.memes["joy"] = 2
    w.para()

    w.say(scene["ending"])
    w.facts["resolved"] = True
    w.facts["conflict"] = True
    w.facts["transformation"] = scene["transform"]
    w.facts["misunderstanding"] = scene["misunderstanding"]
    return w


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    scene = world.facts["scene"]
    return [
        f"Write a nursery-rhyme story about {p.name} and {p.helper} at {p.place}, where {scene['object']} drifts away.",
        f"Show a conflict caused by a misunderstanding, then transform a natural object into a helpful tool.",
        f"End with a child-friendly rhyme proving that the friends repaired their trust.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    scene = world.facts["scene"]
    return [
        QAItem(
            question=f"What were {p.name} and {p.helper} trying to do?",
            answer=f"They were trying to {scene['goal']}.",
        ),
        QAItem(
            question=f"What drifted away, and why did the friends argue?",
            answer=f"The {scene['object']} drifted away in the breeze. They misunderstood one another and each thought the other had caused the trouble.",
        ),
        QAItem(
            question="What clue changed their minds?",
            answer=f"They noticed that {scene['clue']}. This showed that the breeze, rather than either friend, had moved the object.",
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=f"{scene['transform']}. Then they worked together: {scene['action'][0].lower() + scene['action'][1:]}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does drift mean?",
            answer="To drift means to move slowly without a clear path, often because of wind or water.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone understands a word, action, or event incorrectly.",
        ),
        QAItem(
            question="How can friends repair a conflict?",
            answer="Friends can pause, look for the truth, listen carefully, apologize, and choose a helpful action together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id} ({entity.kind}) meters={meters} memes={memes}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
drifted(Object) :- breeze(Wind), moved_by(Object, Wind).
misunderstood(Child, Friend) :- blamed(Child, Friend), confused(Child).
repaired(Child, Friend) :- noticed_clue(Child), apologized(Child, Friend), worked_together(Child, Friend).
valid_story(Place) :- place(Place), drift_event, conflict_event, transformation_event, misunderstanding_event.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "nursery_place"),
            asp.fact("breeze", "playful_breeze"),
            asp.fact("moved_by", "story_object", "playful_breeze"),
            asp.fact("drift_event"),
            asp.fact("conflict_event"),
            asp.fact("transformation_event"),
            asp.fact("misunderstanding_event"),
            asp.fact("blamed", "child", "friend"),
            asp.fact("confused", "child"),
            asp.fact("noticed_clue", "child"),
            asp.fact("apologized", "child", "friend"),
            asp.fact("worked_together", "child", "friend"),
        ]
    )


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program())
    valid = set(asp.atoms(model, "valid_story"))
    if valid != {("nursery_place",)}:
        print(f"MISMATCH: ASP valid stories were {sorted(valid)}")
        return 1
    for seed in range(5):
        sample = generate(StoryParams(seed=seed))
        if not sample.world or not sample.world.facts.get("resolved"):
            print(f"MISMATCH: generated story {seed} did not resolve")
            return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Drift, conflict, and transformation nursery-rhyme world.")
    parser.add_argument("--name", choices=NAME_POOL)
    parser.add_argument("--helper", choices=HELPER_POOL)
    parser.add_argument("--place", choices=PLACE_POOL)
    parser.add_argument("--object", dest="object_name", choices=OBJECT_POOL)
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
    return StoryParams(
        name=args.name or rng.choice(NAME_POOL),
        helper=args.helper or rng.choice(HELPER_POOL),
        place=args.place or rng.choice(PLACE_POOL),
        object_name=args.object_name or rng.choice(OBJECT_POOL),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
    world.facts["params"] = params
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as err:
            raise SystemExit(f"ASP unavailable: {err}")
        model = asp.one_model(asp_program())
        print(sorted(asp.atoms(model, "valid_story")))
        return
    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, obj in enumerate(OBJECT_POOL):
            params = StoryParams(
                name=NAME_POOL[i % len(NAME_POOL)],
                helper=HELPER_POOL[i % len(HELPER_POOL)],
                place=PLACE_POOL[i % len(PLACE_POOL)],
                object_name=obj,
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n:
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

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
