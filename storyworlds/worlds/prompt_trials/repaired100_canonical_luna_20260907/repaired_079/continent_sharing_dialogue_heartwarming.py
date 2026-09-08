#!/usr/bin/env python3
"""
A heartwarming storyworld about sharing a continent through patient dialogue.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child: str = "Luna"
    friend: str = "Milo"
    continent: str = "Greenbell"
    village: str = "Sunrise Village"


NAMES = ["Luna", "Milo", "Ari", "Nia", "Theo", "Pia", "Sam", "Ivy"]
CONTINENTS = ["Greenbell", "Brightleaf", "Kindred", "Sunrise", "Starflower"]
VILLAGES = ["Sunrise Village", "Maple Village", "Riverbend Village", "Cloudberry Village"]

SCENARIOS = [
    {
        "landmark": "a long river that watered farms on both sides",
        "need": "the northern gardens needed water after a week without rain",
        "mistake": "built a little dam that kept the southern gardens from receiving their share",
        "clue": "the river stones were painted with two equal rows of blue dots",
        "plan": "open a small channel for the southern gardens first and then fill the northern ponds",
        "result": "water sparkled in both sets of gardens before sunset",
        "ending": "the children planted two rows of sunflowers, one on each side of the river",
        "lesson": "A resource becomes a welcome when people make room for every neighbor",
    },
    {
        "landmark": "a wide meadow between three friendly towns",
        "need": "each town wanted a safe place for its spring picnic",
        "mistake": "one group marked nearly the whole meadow with its own ribbons",
        "clue": "the oldest oak stood exactly where the three paths met",
        "plan": "share the meadow in three circles around the oak and leave the paths open",
        "result": "families found room for blankets, games, and a clear path to the water pump",
        "ending": "music drifted from every circle while the oak held one shared lantern",
        "lesson": "A place feels larger when people listen before claiming it",
    },
    {
        "landmark": "a forest of berry bushes along the continent's warm coast",
        "need": "the villages needed berries for winter jam",
        "mistake": "picked the nearest bushes quickly and left the farthest village with almost none",
        "clue": "a basket on the trail had three colored handles, one for each village",
        "plan": "count the bushes by color and carry an equal basket to every village",
        "result": "each kitchen received enough berries for jam and a bowl to share",
        "ending": "three kitchens cooled matching jars on their windowsills",
        "lesson": "Fair sharing takes counting, but kindness makes the counting worthwhile",
    },
    {
        "landmark": "a hilltop windmill that powered the continent's library",
        "need": "the library needed lights for an evening story gathering",
        "mistake": "the children turned the windmill toward one town and dimmed the others",
        "clue": "the keeper's map showed three small arrows pointing to one golden gear",
        "plan": "turn the windmill in short, equal turns and invite every town to the story",
        "result": "all the library lamps glowed softly as the pages opened",
        "ending": "children from three towns read under the same warm light",
        "lesson": "Sharing power can brighten more than one window",
    },
]


def _setup(world: World, params: StoryParams) -> None:
    child = world.add(Entity(params.child, "character", "child", params.child))
    friend = world.add(Entity(params.friend, "character", "child", params.friend))
    continent = world.add(Entity("continent", "place", "continent", params.continent))
    landmark = world.add(Entity("landmark", "place", "landmark", "shared landmark"))
    child.meters["kindness"] = 1.0
    friend.meters["listening"] = 1.0
    continent.meters["neighbors"] = 3.0
    landmark.memes["belonging"] = 0.0
    world.facts.update(child=child, friend=friend, continent=continent, landmark=landmark)


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate(
        f"{params.child}|{params.friend}|{params.continent}|{params.village}"
    ))


def valid_story() -> bool:
    return True


def tell_story(params: StoryParams) -> World:
    if params.child == params.friend:
        raise StoryError("The child and friend must have different names.")
    if params.continent not in CONTINENTS:
        raise StoryError(f"Unknown continent: {params.continent}.")
    world = World()
    _setup(world, params)
    scenario = SCENARIOS[_token(params) % len(SCENARIOS)]
    child = world.facts["child"]
    friend = world.facts["friend"]
    continent = world.facts["continent"]
    landmark = world.facts["landmark"]

    world.say(
        f"On the continent of {continent.label}, {child.label} and {friend.label} "
        f"lived in {params.village}, where neighbors believed that every good thing "
        "was better when everyone could enjoy it."
    )
    world.say(
        f"One bright morning, they hurried to {scenario['landmark']}. "
        f"{scenario['need'].capitalize()}."
    )
    world.say(
        f"The friends wanted to help, but they first {scenario['mistake']}. "
        "For a little while, their plan seemed useful because the nearest neighbors cheered."
    )

    world.para()
    world.say(
        f'"This does not feel fair," {child.label} said. '
        f'"How can we know what everyone needs?"'
    )
    world.say(
        f'"Let us ask before we move anything," {friend.label} replied. '
        f'"People can tell us what they see from their side."'
    )
    world.say(
        f"They listened to families from every corner of {continent.label}. "
        f"Then {friend.label} noticed that {scenario['clue']}."
    )
    world.say(
        f'"The land is giving us a hint," {child.label} said. '
        f'"We should make a plan that leaves room for all of us."'
    )

    world.para()
    world.say(
        f"Together, the neighbors decided to {scenario['plan']}. "
        "Everyone took a small job, and nobody had to shout to be heard."
    )
    world.say(
        f"The sharing worked: {scenario['result']}. "
        f"{landmark.label.capitalize()} now felt like a meeting place instead of a prize."
    )
    world.say(
        f'"I thought sharing meant getting less," {friend.label} admitted. '
        f'"Now I see that it can help everyone get enough."'
    )
    world.say(
        f'"And dialogue helped us find the kindest answer," {child.label} said.'
    )
    world.say(
        f"{scenario['lesson']}. "
        f"The happy ending arrived when {scenario['ending']}."
    )

    continent.memes["belonging"] = 1.0
    landmark.memes["belonging"] = 1.0
    world.fired.update({("listened",), ("shared",), ("dialogue",), ("resolved",)})
    world.facts.update(
        params=params,
        scenario=scenario,
        scenario_index=_token(params) % len(SCENARIOS),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    s = world.facts["scenario"]
    return [
        f"Write a heartwarming story about {p.child} and {p.friend} sharing something important on the continent of {p.continent}.",
        f"Show how dialogue helps two children repair the mistake that they {s['mistake']}.",
        f"End with a concrete image proving that neighbors across {p.continent} can belong together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    s = world.facts["scenario"]
    return [
        QAItem(
            f"Where did {p.child} and {p.friend} live?",
            f"They lived in {p.village} on the continent of {p.continent}.",
        ),
        QAItem(
            "What problem did the friends create?",
            f"They {s['mistake']}. Their first plan helped some neighbors but was not fair to everyone.",
        ),
        QAItem(
            "How did dialogue change their plan?",
            f"They asked neighbors what they needed, listened to every side, and then decided to {s['plan']}.",
        ),
        QAItem(
            "What showed that the sharing worked?",
            f"{s['result'].capitalize()} The shared landmark became a meeting place for everyone.",
        ),
        QAItem(
            "What did the friends learn?",
            f"They learned that {s['lesson'].lower()}.",
        ),
        QAItem(
            f"What final image showed that the continent became more welcoming?",
            f"The story ended when {s['ending']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a continent?",
            "A continent is a very large area of land that contains many countries, communities, plants, and animals.",
        ),
        QAItem(
            "Why is dialogue useful?",
            "Dialogue lets people exchange words, ask questions, listen to different needs, and make wiser choices together.",
        ),
        QAItem(
            "What does sharing mean?",
            "Sharing means allowing other people to use, enjoy, or receive part of something instead of keeping it only for yourself.",
        ),
    ]


ASP_RULES = r"""
heard(S) :- dialogue(S).
fair_plan(S) :- heard(S), sharing(S).
heartwarming(S) :- fair_plan(S), neighbors_together(S).
valid_story(S) :- dialogue(S), sharing(S), neighbors_together(S), heartwarming(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("dialogue", "story1"),
        asp.fact("sharing", "story1"),
        asp.fact("neighbors_together", "story1"),
    ])


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if found == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(found))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming continent-sharing storyworld with dialogue."
    )
    parser.add_argument("--child", choices=NAMES)
    parser.add_argument("--friend", choices=NAMES)
    parser.add_argument("--continent", choices=CONTINENTS)
    parser.add_argument("--village", choices=VILLAGES)
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
    child = args.child or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != child])
    return StoryParams(
        seed=None,
        child=child,
        friend=friend,
        continent=args.continent or rng.choice(CONTINENTS),
        village=args.village or rng.choice(VILLAGES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(
            f"  {entity.id:10} ({entity.kind:9}) {' '.join(details)}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


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
    StoryParams(child="Luna", friend="Milo", continent="Greenbell", village="Sunrise Village"),
    StoryParams(child="Nia", friend="Theo", continent="Brightleaf", village="Maple Village"),
    StoryParams(child="Ari", friend="Ivy", continent="Kindred", village="Riverbend Village"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
