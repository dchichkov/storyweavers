#!/usr/bin/env python3
"""
A small superhero storyworld about bacon, a dangerous misunderstanding, and
the reconciliation that follows when a brave hero removes the real trouble.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: str = ""


@dataclass
class World:
    hero: Entity
    helper: Entity
    rival: Entity
    bacon: Entity
    place: str
    seed: int
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    hero_name: str
    helper_name: str
    rival_name: str
    place: str
    seed: Optional[int] = None


HERO_NAMES = ["Luna", "Nova", "Pip", "Mara", "Zed", "Tessa"]
HELPER_NAMES = ["Milo", "Bee", "Rafi", "June", "Ollie"]
RIVAL_NAMES = ["Captain Crumble", "Dr. Sizzle", "The Tin Tornado", "Baron Bluster"]
PLACES = [
    "the rooftop market",
    "the bright city square",
    "the old train station",
    "the neighborhood fair",
    "the bakery street",
]


ASP_RULES = r"""
#show brave/1.
#show rescued/1.
#show reconciled/1.

brave(H) :- notices_danger(H).
rescued(H) :- removes_bacon(H).
reconciled(H) :- explains_truth(H), forgives_rival(H).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("notices_danger", "hero"),
        asp.fact("removes_bacon", "hero"),
        asp.fact("explains_truth", "hero"),
        asp.fact("forgives_rival", "hero"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program(
        "#show brave/1.\n#show rescued/1.\n#show reconciled/1."
    ))
    actual = set()
    for atom in model:
        if atom.name in {"brave", "rescued", "reconciled"}:
            actual.add((atom.name, tuple(
                a.number if a.type.name == "Number" else a.name
                for a in atom.arguments
            )))
    expected = {
        ("brave", ("hero",)),
        ("rescued", ("hero",)),
        ("reconciled", ("hero",)),
    }
    if actual == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld about bacon, removal, and reconciliation."
    )
    parser.add_argument("--hero-name", choices=HERO_NAMES)
    parser.add_argument("--helper-name", choices=HELPER_NAMES)
    parser.add_argument("--rival-name", choices=RIVAL_NAMES)
    parser.add_argument("--place", choices=PLACES)
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
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        helper_name=args.helper_name or rng.choice(HELPER_NAMES),
        rival_name=args.rival_name or rng.choice(RIVAL_NAMES),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if params.hero_name == params.rival_name:
        raise StoryError("The hero and rival must have different names.")
    hero = Entity(
        id="hero",
        label=params.hero_name,
        kind="hero",
        meters={"speed": 8.0, "reach": 5.0},
        memes={"courage": 8.0, "trust": 4.0},
    )
    helper = Entity(
        id="helper",
        label=params.helper_name,
        kind="helper",
        meters={"speed": 4.0, "reach": 3.0},
        memes={"care": 8.0, "trust": 7.0},
    )
    rival = Entity(
        id="rival",
        label=params.rival_name,
        kind="rival",
        meters={"speed": 6.0, "reach": 4.0},
        memes={"pride": 8.0, "trust": 2.0},
    )
    bacon = Entity(
        id="bacon",
        label="the bacon banner",
        kind="snare",
        meters={"height": 7.0, "weight": 2.0},
        memes={"alarm": 7.0, "hunger": 6.0},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in "|".join([
            params.hero_name, params.helper_name, params.rival_name, params.place
        ]))
    return World(
        hero=hero,
        helper=helper,
        rival=rival,
        bacon=bacon,
        place=params.place,
        seed=seed,
    )


def _record(
    world: World,
    *,
    twist: str,
    trouble: str,
    cause: str,
    removal: str,
    reconciliation: str,
    ending: str,
    story: str,
) -> str:
    world.facts.update(
        twist=twist,
        trouble=trouble,
        cause=cause,
        removal=removal,
        reconciliation=reconciliation,
        ending=ending,
        story=story,
    )
    return story


def _signal_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    f = world.helper.label
    r = world.rival.label
    p = world.place
    alarm = rng.choice(["a siren", "a brass bell", "a whooping whistle"])
    twist = "the bacon banner was not a villain's flag but a torn rescue signal"
    trouble = "the city mistook the banner for a dangerous weapon and chased the rival"
    cause = "the rival had hung the bacon banner to signal that a bridge rope was breaking"
    removal = f"{h} removed the bacon banner from the snapping rope and lowered it safely"
    reconciliation = f"{h} listened to {r}'s explanation, and {r} admitted that pride had made the warning too hard to understand"
    ending = "the bacon banner became a bright rescue flag instead of a frightening mystery"
    story = " ".join([
        f"At {p}, {h} patrolled above the stalls while {f} carried a basket of warm bacon rolls.",
        f"Suddenly, {alarm} rang, and a giant bacon banner whipped across the sky.",
        f'"Stop that flying bacon!" shouted {h}. {r} pointed from the bridge and cried, "Do not come closer!"',
        f"The crowd gasped, because {r} looked like the one who had caused the trouble.",
        f"{h} flew toward the bridge, but {f} called, "Look at the rope, not the shouting!"',
        f"That was the twist: {twist}.",
        f"{h} saw the rope fraying beneath the banner and chose to help before choosing whom to blame.",
        f"{removal}. The bridge settled with a long, tired creak.",
        f'"I thought you were attacking us," said {h}. "I was trying to warn you," said {r}.',
        f"{reconciliation}.",
        f"{f} offered everyone a bacon roll, and even {r} smiled before taking the smallest one.",
        f"By sunset, {ending}, and {h} learned that a true superhero removes danger first and anger second.",
    ])
    return _record(
        world,
        twist=twist,
        trouble=trouble,
        cause=cause,
        removal=removal,
        reconciliation=reconciliation,
        ending=ending,
        story=story,
    )


def _crown_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    f = world.helper.label
    r = world.rival.label
    p = world.place
    object_name = rng.choice(["the mayor's crown", "a golden lunchbox", "the fair trophy"])
    twist = f"the bacon was wrapped around {object_name} to keep it from falling into a drain"
    trouble = f"everyone believed {r} had stolen {object_name}"
    cause = f"{r} had grabbed the bacon-wrapped object when a gust pushed it toward the drain"
    removal = f"{h} removed the bacon carefully and pulled {object_name} away from the drain"
    reconciliation = f"{h} apologized for the accusation, and {r} explained the rescue without boasting"
    ending = f"{object_name} stood safely on the fair table while the bacon became lunch for the rescuers"
    story = " ".join([
        f"At {p}, {h} watched the fair while {f} guarded a tray of sizzling bacon.",
        f"A gust sent {object_name} rolling toward a storm drain.",
        f"{r} dashed after it and caught the object with a bacon strip wrapped around one corner.",
        f'"Thief!" cried the crowd. "Wait!" called {h}.',
        f"{h} noticed muddy skid marks leading to the drain. The chase had looked suspicious, but the danger was underneath it.",
        f"Here came the twist: {twist}.",
        f"{h} reached down, {removal}.",
        f'"You saved it," said {f}. "I thought you wanted it," said {h} to {r}.',
        f'"I wanted it safe," {r} answered. {reconciliation}.',
        f"The crowd clapped, and {f} passed around fresh bacon rolls as peace gifts.",
        f"That evening, {ending}. A superhero can be strong enough to stop a mistake and kind enough to repair one.",
    ])
    return _record(
        world,
        twist=twist,
        trouble=trouble,
        cause=cause,
        removal=removal,
        reconciliation=reconciliation,
        ending=ending,
        story=story,
    )


def _cloud_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    f = world.helper.label
    r = world.rival.label
    p = world.place
    cloud = rng.choice(["a smoky cloud", "a gray puff", "a peppery cloud"])
    twist = "the bacon smoke was hiding a flock of frightened pigeons, not a monster"
    trouble = f"the crowd blamed {r} when the smoky cloud covered the square"
    cause = f"{r} had tried to cook bacon for hungry children, but the pan had tipped and filled the air with smoke"
    removal = f"{h} removed the hot pan from the cart and opened the market shutters"
    reconciliation = f"{r} confessed the accident, while {h} thanked {r} for trying to feed everyone"
    ending = "the clean air returned, and the rescued pigeons flew above a shared breakfast"
    story = " ".join([
        f"At {p}, {h} heard a rumble and saw {cloud} roll over the rooftops.",
        f"{f} pointed at {r}. "Who started that?" asked the helper.",
        f'"I did not summon a cloud!" said {r}. "But you are standing beside the bacon cart," replied {h}.',
        f"The crowd began to shout, and the pigeons fluttered wildly inside the gray air.",
        f"{h} zoomed closer instead of throwing a gust at the cloud.",
        f"The twist appeared: {twist}.",
        f"{cause.capitalize()}.",
        f"{removal}. The shutters swung open, and fresh air swept the smoke away.",
        f'"You should have told us," said {h}. "I was afraid you would laugh," said {r}.',
        f"{reconciliation}.",
        f"{f} found clean plates, and the three friends shared the bacon after checking the pan twice.",
        f"At dusk, {ending}. The city remembered that honest words can clear a cloud faster than anger.",
    ])
    return _record(
        world,
        twist=twist,
        trouble=trouble,
        cause=cause,
        removal=removal,
        reconciliation=reconciliation,
        ending=ending,
        story=story,
    )


def _magnet_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    f = world.helper.label
    r = world.rival.label
    p = world.place
    tool = rng.choice(["a magnetic glove", "a metal hook", "a rolling robot"])
    twist = "the bacon was stuck to a giant magnet that was pulling the town signs loose"
    trouble = f"the loose signs made it appear that {r} was rearranging the whole street"
    cause = f"{r} had brought the magnet to lift a fallen sign but accidentally caught the bacon tray"
    removal = f"{h} removed the bacon from the magnet with {tool}, then shut the magnet off"
    reconciliation = f"{h} and {r} rebuilt the sign together and agreed to ask for help sooner"
    ending = "the street signs pointed correctly again, and the bacon was served on plates instead of signs"
    story = " ".join([
        f"At {p}, {h} saw street signs wobbling while {f} carried a plate of bacon.",
        f"{r} rolled in a machine, and the bacon leaped from the plate with a loud CLANG.",
        f'"My breakfast!" cried {f}. "My machine!" cried {r}.',
        f"People ducked as a bakery sign slid toward the fountain.",
        f"{h} followed the bacon instead of the shouting and discovered the hidden pull.",
        f"The twist was clear: {twist}.",
        f"{cause.capitalize()}.",
        f"{removal}. The signs stopped dancing.",
        f'"I thought you were stealing the bacon," said {h}. "I thought you were breaking my invention," said {r}.',
        f"{reconciliation}.",
        f"{f} divided the rescued bacon into three equal piles.",
        f"Before nightfall, {ending}. Even a superhero knows that a problem can look like a person until the real cause is found.",
    ])
    return _record(
        world,
        twist=twist,
        trouble=trouble,
        cause=cause,
        removal=removal,
        reconciliation=reconciliation,
        ending=ending,
        story=story,
    )


ARC_BUILDERS = [_signal_arc, _crown_arc, _cloud_arc, _magnet_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0xBacon)
    return ARC_BUILDERS[world.seed % len(ARC_BUILDERS)](world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    f = world.facts
    return [
        QAItem(
            question=f"What was the twist in {h}'s adventure?",
            answer=f"The twist was that {f['twist']}.",
        ),
        QAItem(
            question="What caused the trouble?",
            answer=f"The trouble began because {f['cause']}.",
        ),
        QAItem(
            question=f"What did {h} remove?",
            answer=f"{h} solved the immediate danger when {f['removal']}.",
        ),
        QAItem(
            question="How did the characters reconcile?",
            answer=f"They reconciled when {f['reconciliation']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should someone remove a danger before arguing about blame?",
            answer="Removing the danger protects people first and leaves time to learn what really happened.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is the process of repairing trust after people understand a mistake or disagreement.",
        ),
        QAItem(
            question="Why can bacon smoke spread quickly?",
            answer="Hot bacon releases vapor and smoke, and moving air can carry it through a room or street.",
        ),
        QAItem(
            question="What makes someone a superhero in this storyworld?",
            answer="A superhero notices danger, acts carefully, tells the truth, and helps repair friendships after the danger ends.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly superhero story involving bacon and the need to remove a danger.",
        f"Tell a superhero adventure at {world.place} with a surprising twist and reconciliation.",
        "Create a story where listening changes a hero's decision and repairs a friendship.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.hero, world.helper, world.rival, world.bacon]:
        lines.append(
            f"  {entity.id:7} {entity.kind:8} label={entity.label!r} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.place!r}")
    lines.append(f"  twist={world.facts.get('twist', '')!r}")
    lines.append(f"  reconciliation={world.facts.get('reconciliation', '')!r}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(
            "#show brave/1.\n#show rescued/1.\n#show reconciled/1."
        ))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "3 compatible logical atoms: brave(hero), rescued(hero), "
            "reconciled(hero)"
        )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Milo", "Captain Crumble", "the rooftop market"),
            StoryParams("Nova", "Bee", "Dr. Sizzle", "the bright city square"),
            StoryParams("Pip", "Rafi", "The Tin Tornado", "the old train station"),
            StoryParams("Mara", "June", "Baron Bluster", "the neighborhood fair"),
        ]
        for index, params in enumerate(curated):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and index < limit:
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
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
        return

    for index, sample in enumerate(samples):
        if args.all:
            params = sample.params
            header = f"### {params.hero_name} at {params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
