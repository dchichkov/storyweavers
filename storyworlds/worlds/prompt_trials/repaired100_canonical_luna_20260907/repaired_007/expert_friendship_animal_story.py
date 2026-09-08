#!/usr/bin/env python3
"""
A small animal-story world about friendship and learning from an expert.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    species: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass(frozen=True)
class Place:
    id: str
    label: str
    feature: str


@dataclass
class World:
    place: Place
    animals: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, animal: Entity) -> Entity:
        self.animals[animal.id] = animal
        return animal

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class StoryArc:
    key: str
    object_name: str
    problem: str
    method: str
    result: str
    opening: tuple[str, str]
    trouble: tuple[str, str]
    teaching: tuple[str, str]
    ending: tuple[str, str]


PLACES = {
    "meadow": Place("meadow", "a sunny meadow", "a creek and tall grass"),
    "forest": Place("forest", "a quiet forest", "mossy trees and a clear stream"),
    "orchard": Place("orchard", "a warm orchard", "apple trees and a little hill"),
    "marsh": Place("marsh", "a green marsh", "reeds, lily pads, and shallow water"),
}

ANIMAL_NAMES = {
    "rabbit": ["Luna", "Pip", "Clover", "Hazel"],
    "fox": ["Fern", "Ruby", "Sage", "Ember"],
    "beaver": ["Bramble", "Moss", "Nell", "Pebble"],
    "owl": ["Olive", "Echo", "Willow", "Moon"],
}

ARCS = (
    StoryArc(
        "stream_bridge",
        "a bundle of reeds",
        "the small bridge over the stream had broken",
        "the expert beaver showed them how to weave reeds between sturdy sticks",
        "the animals could cross safely together",
        (
            "In {place}, {friend} and {expert} gathered berries beside a sparkling stream.",
            "{friend} liked to hurry, but {expert} liked to notice how each thing fit.",
        ),
        (
            "A loud crack split the little bridge, and one plank bobbed away.",
            '"I can fix it alone," said {friend}. "You do not have to," answered {expert}.',
        ),
        (
            '{expert} smiled. "A good friend shares what they know, not just what they have."',
            "{friend} watched closely, then helped weave the reeds around the sticks.",
        ),
        (
            "The bridge held firm. The friends crossed side by side, carrying berries for everyone.",
            "From then on, {friend} asked questions gladly, and {expert} taught with a patient heart.",
        ),
    ),
    StoryArc(
        "fallen_nest",
        "a soft nest",
        "a young bird's nest had fallen from a low branch",
        "the expert owl taught the friends to make a safe cradle from twigs and grass",
        "the nest rested safely in a forked tree",
        (
            "At {place}, {friend} and {expert} followed a trail of feathers beneath the trees.",
            "They found a tiny nest on the ground and heard a worried peep above.",
        ),
        (
            '"We must lift it quickly," said {friend}. The nest wobbled when {friend} touched it.',
            '"First we look," said {expert}. "Its soft lining needs support."',
        ),
        (
            "{expert} showed how to place strong twigs below and gentle grass around the sides.",
            "{friend} held the cradle steady and copied every careful turn.",
        ),
        (
            "The nest rested in a forked branch, and the young bird chirped from its safe home.",
            "The friends listened together, happy that patience had helped more than rushing.",
        ),
    ),
    StoryArc(
        "berry_path",
        "a basket of berries",
        "the berry path had vanished beneath a muddy puddle",
        "the expert fox taught them to mark firm stones and step around the deep mud",
        "the basket reached the hungry hedgehogs without spilling",
        (
            "In {place}, {friend} carried berries while {expert} led the way along a winding path.",
            "They were bringing breakfast to three hedgehogs waiting near the old oak.",
        ),
        (
            "Rain had filled the path with mud. {friend} stepped forward and sank to the ankle.",
            '"The berries are heavy," said {friend}. "Maybe we should turn back."',
        ),
        (
            '"A path is not always the straightest line," said {expert}. The expert pointed to flat stones.',
            "{friend} tested each stone, and together they made a careful trail around the puddle.",
        ),
        (
            "They reached the old oak with every berry safe in the basket.",
            "The hedgehogs cheered, while {friend} thanked the expert for showing a wiser way.",
        ),
    ),
    StoryArc(
        "windy_den",
        "a leafy den",
        "the wind had loosened the roof of the friends' den",
        "the expert beaver taught them to anchor leaves with branches and roots",
        "the den became warm and sturdy again",
        (
            "Under the trees, {friend} and {expert} built a leafy den for a rainy afternoon.",
            "They planned to share stories there while the clouds rolled past.",
        ),
        (
            "A gust lifted the roof and sent golden leaves swirling through the air.",
            '"Hold it down!" cried {friend}. "We need a stronger plan," said {expert}.',
        ),
        (
            "{expert} showed {friend} how to tuck branches across the roof and loop roots around them.",
            "They worked on opposite sides, checking that each branch held before adding another.",
        ),
        (
            "The next gust shook the den, but its roof stayed snug and dry.",
            "The two friends curled up inside, proud that teaching and helping had made a safe place.",
        ),
    ),
)


@dataclass
class StoryParams:
    place: str
    friend_name: str
    expert_name: str
    friend_species: str = "rabbit"
    expert_species: str = "beaver"
    seed: Optional[int] = None


NAMES = ANIMAL_NAMES


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, "rabbit", "beaver") for place in PLACES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    friend_species = args.friend_species or rng.choice(["rabbit", "fox", "owl"])
    expert_species = args.expert_species or rng.choice(["beaver", "owl", "fox"])
    if friend_species == expert_species:
        expert_species = "beaver" if friend_species != "beaver" else "owl"
    friend_name = args.friend or rng.choice(NAMES[friend_species])
    expert_choices = [name for name in NAMES[expert_species] if name != friend_name]
    expert_name = args.expert or rng.choice(expert_choices)
    return StoryParams(
        place=place,
        friend_name=friend_name,
        expert_name=expert_name,
        friend_species=friend_species,
        expert_species=expert_species,
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}.")
    if params.friend_species not in NAMES or params.expert_species not in NAMES:
        raise StoryError("Both animals must be known animal types.")
    if params.friend_name == params.expert_name:
        raise StoryError("The two friends need different names.")

    place = PLACES[params.place]
    world = World(place)
    friend = world.add(Entity(
        params.friend_name.lower(),
        "animal",
        params.friend_species,
        params.friend_name,
        "friend",
        meters={"curious": 1.0},
        memes={"friendship": 1.0, "confidence": 0.5},
    ))
    expert = world.add(Entity(
        params.expert_name.lower(),
        "animal",
        params.expert_species,
        params.expert_name,
        "expert",
        meters={"skill": 1.0, "patience": 1.0},
        memes={"friendship": 1.0, "kindness": 1.0},
    ))

    rng = random.Random(params.seed if params.seed is not None else sum(
        (i + 1) * ord(c) for i, c in enumerate(
            f"{params.place}:{params.friend_name}:{params.expert_name}"
        )
    ))
    arc = ARCS[rng.randrange(len(ARCS))]
    values = {
        "place": place.label,
        "friend": friend.label,
        "expert": expert.label,
    }

    for line in arc.opening:
        world.say(line.format(**values))
    world.para()

    friend.meters["confidence"] = 0.0
    friend.memes["worry"] = 1.0
    expert.memes["calm"] = 1.0
    for line in arc.trouble:
        world.say(line.format(**values))
    world.para()

    friend.meters["learned"] = 1.0
    friend.memes["confidence"] = 1.0
    expert.meters["taught"] = 1.0
    friend.memes["gratitude"] = 1.0
    expert.memes["friendship"] = 2.0
    for line in arc.teaching:
        world.say(line.format(**values))
    world.para()

    friend.meters["helped"] = 1.0
    expert.meters["helped"] = 1.0
    friend.memes["joy"] = 1.0
    expert.memes["joy"] = 1.0
    world.facts.update(
        friend=friend,
        expert=expert,
        place=place,
        arc=arc,
        object_name=arc.object_name,
        problem=arc.problem,
        method=arc.method,
        result=arc.result,
        final_image=arc.ending[-1].format(**values),
        friendship=True,
        learned=True,
    )
    for line in arc.ending:
        world.say(line.format(**values))
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a gentle Animal Story using the word "expert" and showing Friendship.',
        f"Tell how {f['friend'].label} learned from expert {f['expert'].label} after {f['problem']}.",
        f"Write a child-friendly animal adventure in {f['place'].label} where friendship grows through patient teaching.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "What problem did the animals face?",
            f"{f['friend'].label} and {f['expert'].label} faced this problem: {f['problem']}.",
        ),
        QAItem(
            "How did the expert help?",
            f"{f['expert'].label} shared careful knowledge. Together, they solved it by {f['method']}.",
        ),
        QAItem(
            "How did Friendship change the ending?",
            f"Their Friendship helped them cooperate, so {f['result']}. The final image was that {f['final_image']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is an expert?",
            "An expert is someone who has practiced and learned a lot about something. A kind expert explains what they know so others can learn too.",
        ),
        QAItem(
            "What is Friendship?",
            "Friendship is a caring relationship in which friends listen, help one another, and share happy and difficult moments.",
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
    for animal in world.animals.values():
        meters = {k: v for k, v in animal.meters.items() if v}
        memes = {k: v for k, v in animal.memes.items() if v}
        lines.append(
            f"  {animal.label}: species={animal.species}, role={animal.role}, "
            f"meters={meters}, memes={memes}"
        )
    arc = world.facts.get("arc")
    if arc:
        lines.append(f"  resolved_arc={arc.key}, friendship={world.facts['friendship']}")
    return "\n".join(lines)


ASP_RULES = r"""
expert(E) :- animal(E), expert_role(E).
friend(F) :- animal(F), friend_role(F).
learned(F) :- friend(F), taught(E), expert(E), helped(F).
friendship_grows :- friend(F), expert(E), learned(F), helped(E).
outcome(success) :- friendship_grows.
"""


def asp_facts() -> str:
    import asp
    facts = [
        asp.fact("animal", "friend"),
        asp.fact("animal", "expert"),
        asp.fact("friend_role", "friend"),
        asp.fact("expert_role", "expert"),
        asp.fact("taught", "expert"),
        asp.fact("helped", "friend"),
        asp.fact("helped", "expert"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show outcome/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show outcome/1."))
    return sorted(set(asp.atoms(model, "outcome")))


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program())
        if ("success",) not in asp.atoms(model, "outcome"):
            print("ASP parity check failed: friendship outcome was absent.")
            return 1
        sample = generate(StoryParams(
            place="meadow",
            friend_name="Luna",
            expert_name="Bramble",
            friend_species="rabbit",
            expert_species="beaver",
            seed=7,
        ))
        if not sample.story.strip() or not sample.story_qa:
            print("Generation smoke test failed.")
            return 1
        if not sample.world.facts["learned"]:
            print("Python parity check failed: friend did not learn.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: smoke tests passed.")
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="An Animal Story world about expert knowledge and Friendship."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--friend")
    parser.add_argument("--expert")
    parser.add_argument("--friend-species", choices=sorted(NAMES))
    parser.add_argument("--expert-species", choices=sorted(NAMES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("meadow", "Luna", "Bramble", "rabbit", "beaver", base_seed),
            StoryParams("forest", "Fern", "Olive", "fox", "owl", base_seed + 1),
            StoryParams("orchard", "Pip", "Moss", "rabbit", "beaver", base_seed + 2),
            StoryParams("marsh", "Echo", "Ruby", "owl", "fox", base_seed + 3),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        for index in range(max(1, args.n)):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
