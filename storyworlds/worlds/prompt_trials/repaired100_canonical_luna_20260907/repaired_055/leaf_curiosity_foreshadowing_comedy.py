#!/usr/bin/env python3
"""
A small storyworld about a curious child, a suspicious leaf, and a comic
foreshadowed surprise.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
class Episode:
    id: str
    place: str
    odd_clue: str
    guess: str
    comic_action: str
    consequence: str
    friend_clue: str
    reveal: str
    repair: str
    ending: str
    lesson: str


EPISODES = [
    Episode(
        "hat_leaf",
        "the village square",
        "a green leaf was stuck to the mayor's hat",
        "the leaf was a tiny flag announcing a secret meeting",
        "Luna marched after the mayor, saluting every pigeon",
        "the pigeons scattered and the mayor's hat spun into a fountain",
        "the same kind of leaf trembled on a low tree branch beside the square",
        "a squirrel had dropped the leaf while carrying lunch",
        "Luna dried the mayor's hat and apologized to the startled pigeons",
        "the squirrel nibbled its leaf lunch above the square",
        "curiosity is useful when it asks questions before it makes a parade",
    ),
    Episode(
        "leaf_letter",
        "the garden path",
        "a leaf had a hole shaped like a letter C",
        "the leaf was a message from a very small mail carrier",
        "Luna whispered replies to three beetles and one mushroom",
        "the beetles hid under stones while Luna waited for an answer",
        "a caterpillar had chewed the hole while eating breakfast",
        "the caterpillar appeared wearing a crumb like a tiny hat",
        "Luna placed the leaf near the hedge and shared a berry with the caterpillar",
        "the caterpillar crawled through the C-shaped hole as if entering a door",
        "a strange clue deserves a careful look before a grand explanation",
    ),
    Episode(
        "leaf_alarm",
        "the school garden",
        "a leaf kept tapping against a window",
        "the leaf was warning everyone about a dragon",
        "Luna rang the school bell and hid beneath a watering can",
        "the class rushed outside and found only Luna's muddy shoes",
        "a loose vine stretched from the window to a windy branch",
        "the vine tapped again, right after a sparrow landed on it",
        "Luna helped tie the vine safely to its trellis",
        "the next tap made everyone laugh, but nobody ran away",
        "curiosity becomes brave wisdom when it checks the ordinary causes too",
    ),
    Episode(
        "leaf_crown",
        "the park",
        "a bright leaf landed on Luna's head",
        "the park squirrels had chosen Luna as their queen",
        "Luna bowed to a dog, a bench, and a surprised trash can",
        "the dog barked and chased her in a very undignified circle",
        "a gust had blown leaves from the maple above her",
        "another leaf landed on the trash can like a crown",
        "Luna gave the leaf crown to the dog, who carried it proudly",
        "even a mistaken royal ceremony can end kindly",
    ),
]


@dataclass
class StoryParams:
    place: str = "park"
    activity: str = "investigate"
    name: str = "Luna"
    friend_name: str = "Pip"
    trait: str = "curious"
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nia", "Toby", "Pia", "Ollie"]
FRIENDS = ["Pip", "Mara", "Finn", "Bee", "Jo", "Nell"]
TRAITS = ["curious", "bright", "mischievous", "watchful", "cheerful"]
PLACES = {"park", "garden", "square", "school"}
ACTIVITIES = {"investigate", "observe", "explore"}


def reasonable(params: StoryParams) -> bool:
    return params.place in PLACES and params.activity in ACTIVITIES and params.name != params.friend_name


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A comic leaf-curiosity storyworld.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--activity", choices=sorted(ACTIVITIES))
    parser.add_argument("--name")
    parser.add_argument("--friend-name", dest="friend_name")
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    activity = args.activity or rng.choice(sorted(ACTIVITIES))
    name = args.name or rng.choice(NAMES)
    friend_name = args.friend_name or rng.choice(FRIENDS)
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(place, activity, name, friend_name, trait)
    if not reasonable(params):
        raise StoryError("The two characters must have different names, and the place and activity must be supported.")
    return params


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(params.name, "character", "child"))
    friend = world.add(Entity(params.friend_name, "character", "friend"))
    leaf = world.add(Entity("leaf", "thing", "leaf", "a mysterious leaf"))
    episode = EPISODES[(params.seed or 0) % len(EPISODES)]

    child.memes["curiosity"] = 1.0
    child.meters["attention"] = 1.0
    friend.memes["patience"] = 1.0

    world.say(f"{params.name} was the most {params.trait} child in {episode.place}.")
    world.say(f"While {params.name} and {params.friend_name} went to {params.activity} near the path, {episode.odd_clue.capitalize()}.")
    world.say(f'"That leaf is trying to tell us something," {params.name} said.')
    world.say(f'"It may be trying to fall," {params.friend_name} replied, though {params.name} was already studying it with great seriousness.')

    world.para()
    child.memes["wonder"] = 1.0
    world.say(f"{params.name} decided that {episode.guess}.")
    world.say(f"With a grand flourish, {params.name} {episode.comic_action}.")
    world.say(f"As a result, {episode.consequence}.")
    child.meters["confusion"] = 1.0
    friend.meters["patience"] += 1.0
    world.say(f"{params.friend_name} pointed toward the clue and said, \"Look closely. {episode.friend_clue.capitalize()}.\"")

    world.para()
    friend.memes["helpfulness"] = 1.0
    child.memes["understanding"] = 1.0
    world.say(f"{params.name} and {params.friend_name} waited quietly.")
    world.say(f"Then {episode.reveal.capitalize()}.")
    world.say(f'"So the leaf was not a secret warning?" {params.name} asked.')
    world.say(f'"It was a secret only to us," {params.friend_name} said. "Nature had already explained it."')
    world.say(f"Together they {episode.repair}.")
    child.meters["confusion"] = 0.0
    child.memes["relief"] = 1.0

    world.para()
    world.say(f"{params.name} laughed at the enormous adventure caused by one small leaf.")
    world.say(f"They learned that {episode.lesson}.")
    world.say(f"At the end, {episode.ending}.")
    world.facts.update(child=child, friend=friend, leaf=leaf, episode=episode)
    return world


def generation_prompts(world: World) -> list[str]:
    episode = world.facts["episode"]
    child = world.facts["child"].id
    friend = world.facts["friend"].id
    return [
        f"Write a comic child-facing story in {episode.place} about {child}, {friend}, and a mysterious leaf.",
        f"Use curiosity and foreshadowing: let {child} misread {episode.odd_clue}, then let {friend} notice evidence.",
        "End with a concrete funny image that proves the misunderstanding has been resolved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    episode = world.facts["episode"]
    child = world.facts["child"].id
    friend = world.facts["friend"].id
    return [
        QAItem(f"What did {child} first think the leaf meant?", f"{child} thought {episode.guess}."),
        QAItem(f"How did {friend} help?", f"{friend} pointed out that {episode.friend_clue}, giving {child} a real clue to inspect."),
        QAItem("What was the leaf's real explanation?", f"{episode.reveal.capitalize()}."),
        QAItem("How did the friends repair the trouble?", f"They {episode.repair}."),
        QAItem("What final image made the ending funny?", f"{episode.ending.capitalize()}."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("Why is curiosity helpful?", "Curiosity is helpful because it encourages people to notice details and ask questions before deciding what something means."),
        QAItem("What is foreshadowing?", "Foreshadowing is an earlier clue that quietly prepares us for something revealed later."),
        QAItem("Why can a misunderstanding be funny?", "A misunderstanding can be funny when a harmless clue leads someone to take a surprisingly silly action."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
curious(child).
has_leaf(child).
friend(friend).
notices(friend, leaf).
explains(friend, child).
resolved(child) :- curious(child), has_leaf(child), notices(friend, leaf), explains(friend, child).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("curious", "child"),
        asp.fact("has_leaf", "child"),
        asp.fact("friend", "friend"),
        asp.fact("notices", "friend", "leaf"),
        asp.fact("explains", "friend", "child"),
    ])


def asp_program(show: str = "#show resolved/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if asp.atoms(model, "resolved") == [("child",)]:
        print("OK: ASP and Python reasonableness agree.")
        return 0
    print("MISMATCH between ASP and Python reasonableness.")
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(f"  {entity.id}: meters={entity.meters} memes={entity.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if not reasonable(params):
        raise StoryError("Unsupported story parameters.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams("park", "investigate", "Luna", "Pip", "curious", 0),
        StoryParams("garden", "observe", "Milo", "Mara", "watchful", 1),
        StoryParams("square", "explore", "Nia", "Finn", "bright", 2),
        StoryParams("school", "investigate", "Toby", "Bee", "mischievous", 3),
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in valid_story_params()]
    else:
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### {sample.params.name} and {sample.params.friend_name}" if args.all or len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
