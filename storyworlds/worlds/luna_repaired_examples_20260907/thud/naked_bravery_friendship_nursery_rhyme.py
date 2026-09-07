#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about brave friendship.

A child finds a small naked seedling after a windy night. Fear makes the
seedling droop, but two friends shelter it together until its first green
leaf rises. Here "naked" describes the seedling's bare stem, not a person.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
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


@dataclass(frozen=True)
class Tale:
    key: str
    opening: tuple[str, str]
    trouble: tuple[str, str]
    brave: tuple[str, str]
    ending: tuple[str, str]
    method: str
    result: str
    image: str


TALES = (
    Tale(
        "dew_garden",
        (
            "In {place}, {a} found a naked little seedling beside the gate.",
            "{b} heard its tiny leaves say, \"Please do not leave me to the wind's rough weight.\"",
        ),
        (
            "The cold wind bent its bare green stem and shook the soil below.",
            "The friends felt a flutter of fear, but friendship helped them know.",
        ),
        (
            "{a} held a broad leaf near the stem; {b} pressed warm earth around.",
            "They made a ring of twigs to hush the gusts and keep the roots safe and sound.",
        ),
        (
            "By noon one brave green leaf stood high above the ground.",
            "The naked stem wore morning dew, and happy friends danced round.",
        ),
        "They sheltered the bare stem with a twig ring and firm warm earth.",
        "The seedling stood upright and safe.",
        "a naked stem shining with morning dew",
    ),
    Tale(
        "window_box",
        (
            "At {place}, {a} saw a naked sprout in a little window box.",
            "{b} brought a cup of water and a ribbon bright as a fox.",
        ),
        (
            "A noisy sparrow hopped too near and made the tender stem sway.",
            "The sprout had no coat of leaves, so the friends had to be brave that day.",
        ),
        (
            "{a} raised a paper screen; {b} guided the sprout beneath its shade.",
            "They shared the work with careful hands, and soon the shaking eased away.",
        ),
        (
            "A fresh green curl unfolded where the naked stem had been.",
            "The friends clapped a soft, brave clap and watched the garden grin.",
        ),
        "They made a paper shade and moved the sprout away from the pecking sparrow.",
        "The tender sprout rested safely in gentle shade.",
        "a fresh green curl unfolding",
    ),
    Tale(
        "rainy_path",
        (
            "Along {place}, {a} found a naked sprout beside a puddled track.",
            "{b} brought a fallen bark boat and said, \"We must help it back.\"",
        ),
        (
            "Rain tapped hard upon the soil and washed one little root in sight.",
            "The friends were small, but friendship made their courage bright.",
        ),
        (
            "{a} held the bark above the stem; {b} tucked the root in mud.",
            "They waited through the drumming drops and kept their promise good.",
        ),
        (
            "When clouds rolled off, the sprout stood straight and green and new.",
            "Two friends bowed beside it while a silver raindrop grew.",
        ),
        "They used fallen bark as a roof and tucked the loose root into mud.",
        "The root was covered and the sprout stood straight again.",
        "a silver raindrop growing on a green leaf",
    ),
)


PLACES = {
    "garden": Place("garden", "the garden", {"outdoors", "green"}),
    "courtyard": Place("courtyard", "the sunny courtyard", {"outdoors", "stone"}),
    "schoolyard": Place("schoolyard", "the schoolyard garden", {"outdoors", "children"}),
}

NAMES = {
    "boy": ["Ben", "Leo", "Toby", "Sam"],
    "girl": ["Mia", "Nora", "Zoe", "Lily"],
}


@dataclass
class StoryParams:
    place: str
    hero_name: str
    friend_name: str
    hero_gender: str = "boy"
    friend_gender: str = "girl"
    seed: Optional[int] = None


CURATED = [
    StoryParams("garden", "Ben", "Mia", "boy", "girl", 11),
    StoryParams("courtyard", "Nora", "Leo", "girl", "boy", 22),
    StoryParams("schoolyard", "Zoe", "Sam", "girl", "boy", 33),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A nursery-rhyme world of naked seedlings, bravery, and friendship."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--hero-gender", choices=["boy", "girl"])
    parser.add_argument("--friend-gender", choices=["boy", "girl"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero_gender = args.hero_gender or rng.choice(["boy", "girl"])
    friend_gender = args.friend_gender or ("girl" if hero_gender == "boy" else "boy")
    hero_name = args.hero or rng.choice(NAMES[hero_gender])
    options = [n for n in NAMES[friend_gender] if n != hero_name]
    friend_name = args.friend or rng.choice(options)
    return StoryParams(
        place=place,
        hero_name=hero_name,
        friend_name=friend_name,
        hero_gender=hero_gender,
        friend_gender=friend_gender,
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.hero_name == params.friend_name:
        raise StoryError("The two friends must have different names.")
    if params.hero_gender not in NAMES or params.friend_gender not in NAMES:
        raise StoryError("Each child must have a valid gender choice.")

    world = World(PLACES[params.place])
    hero = world.add(Entity(params.hero_name, "character", params.hero_gender, params.hero_name))
    friend = world.add(Entity(params.friend_name, "character", params.friend_gender, params.friend_name))
    seedling = world.add(Entity("seedling", "plant", "seedling", "naked little seedling"))
    rng = random.Random(params.seed if params.seed is not None else 0)
    tale = TALES[rng.randrange(len(TALES))]

    values = {"a": hero.label, "b": friend.label, "place": world.place.label}
    for line in tale.opening:
        world.say(line.format(**values))
    world.para()

    seedling.meters.update({"root_covered": 0.0, "upright": 0.0, "leaf_open": 0.0})
    seedling.memes["fear"] = 1.0
    hero.memes["worry"] = 1.0
    friend.memes["worry"] = 1.0
    world.trace.append("The naked seedling bent in danger.")
    for line in tale.trouble:
        world.say(line.format(**values))
    world.para()

    hero.memes["bravery"] = 1.0
    friend.memes["bravery"] = 1.0
    hero.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0
    seedling.meters["root_covered"] = 1.0
    seedling.meters["upright"] = 1.0
    seedling.meters["leaf_open"] = 1.0
    seedling.memes["fear"] = 0.0
    world.trace.append(tale.method)
    for line in tale.brave:
        world.say(line.format(**values))
    world.para()

    hero.memes["joy"] = 1.0
    friend.memes["joy"] = 1.0
    world.trace.append(tale.result)
    for line in tale.ending:
        world.say(line.format(**values))

    world.facts.update(
        hero=hero.label,
        friend=friend.label,
        place=world.place.label,
        tale=tale.key,
        problem="the naked seedling was bent and exposed to danger",
        method=tale.method,
        result=tale.result,
        image=tale.image,
        brave=True,
        friendship=True,
        seedling_safe=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a gentle nursery rhyme that uses the word "naked" for a bare seedling.',
        f"Tell a story in which {f['hero']} and {f['friend']} show bravery and friendship.",
        f"Describe how two friends help a naked seedling in {f['place']} and end with {f['image']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "What problem did the friends notice?",
            "They noticed that the naked seedling was bent and exposed to danger, so its small root and stem needed care.",
        ),
        QAItem(
            "How did bravery and friendship help?",
            f"{f['hero']} and {f['friend']} stayed together and used this careful plan: {f['method']} Because they shared the work, {f['result']}",
        ),
        QAItem(
            "What ending image showed that the seedling was safe?",
            f"The story ended with {f['image']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does naked mean in this story?",
            "Here naked means that the seedling had a bare stem without its full coat of leaves. It does not describe a person.",
        ),
        QAItem(
            "What is bravery?",
            "Bravery is trying to do the right thing even when something feels frightening.",
        ),
        QAItem(
            "What is friendship?",
            "Friendship is caring about someone, staying near, and helping one another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.label}: type={entity.type}, meters={meters}, memes={memes}"
        )
    lines.append("  causal trace:")
    lines.extend(f"    - {entry}" for entry in world.trace)
    return "\n".join(lines)


ASP_RULES = r"""
safe(seedling) :- root_covered(seedling), upright(seedling).
brave(hero) :- brave_action(hero).
brave(friend) :- brave_action(friend).
friendship(hero,friend) :- brave(hero), brave(friend), shared_plan.
outcome(growing) :- safe(seedling), friendship(hero,friend).
#show safe/1.
#show friendship/2.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("seedling", "seedling"),
            asp.fact("hero", "hero"),
            asp.fact("friend", "friend"),
            asp.fact("root_covered", "seedling"),
            asp.fact("upright", "seedling"),
            asp.fact("brave_action", "hero"),
            asp.fact("brave_action", "friend"),
            asp.fact("shared_plan"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


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


def asp_verify() -> int:
    import asp

    try:
        symbols = asp.one_model(asp_program())
        safe = asp.atoms(symbols, "safe")
        bonds = asp.atoms(symbols, "friendship")
        outcomes = asp.atoms(symbols, "outcome")
        if ("seedling",) not in safe or ("hero", "friend") not in bonds or ("growing",) not in outcomes:
            print("ASP parity failed: expected safe, friendship, and growing atoms.")
            return 1
        sample = generate(StoryParams("garden", "Ben", "Mia", "boy", "girl", 4))
        if not sample.story.strip() or "naked" not in sample.story.lower():
            print("Story smoke test failed.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: Python and ASP story checks passed.")
    return 0


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
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
        import asp

        print(asp.atoms(asp.one_model(asp_program()), "outcome"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
