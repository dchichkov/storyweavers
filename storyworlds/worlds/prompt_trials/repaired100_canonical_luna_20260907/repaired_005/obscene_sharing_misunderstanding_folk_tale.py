#!/usr/bin/env python3
"""
A gentle folk-tale story world about an obscene-looking pumpkin, sharing,
and a misunderstanding that is repaired by honest words.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str = "Luna"
    village: str = "Mossy Hollow"
    seed: Optional[int] = None
    trial: int = 0
    sharing: int = 0
    misunderstanding: int = 0
    ending: int = 0


@dataclass(frozen=True)
class Trial:
    setting: str
    treasure: str
    odd_shape: str
    mistaken_belief: str
    clue: str
    truth: str
    sharing_act: str
    ending_image: str


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


TRIALS = (
    Trial(
        setting="the village market beneath the old walnut tree",
        treasure="a round loaf of honey bread",
        odd_shape="two long bumps and a crooked little tail",
        mistaken_belief="that Luna had brought an obscene joke to the village table",
        clue="a sweet smell drifting from the cloth",
        truth="the strange bumps were only the loaf's baked ears, and the tail was a twisted braid of dough",
        sharing_act="cut the loaf into warm pieces for every hungry neighbor",
        ending_image="The walnut tree filled with the smell of honey, and even the shyest child found a place at the table.",
    ),
    Trial(
        setting="the lantern festival beside the village pond",
        treasure="a bundle of bright river gourds",
        odd_shape="a foolish-looking cluster with crooked stems",
        mistaken_belief="that Luna had hung something obscene beside the festival lanterns",
        clue="golden seeds rattling inside the largest gourd",
        truth="the cluster was an old harvest charm, shaped by the river wind and meant to bring a full pantry",
        sharing_act="open the gourds and give their seeds to the gardeners for next spring",
        ending_image="By moonrise, new lanterns glowed over the pond, and the saved seeds rested safely in many gardens.",
    ),
    Trial(
        setting="the baker's courtyard after the first autumn rain",
        treasure="a basket of purple figs",
        odd_shape="one fig split into a comical, open shape",
        mistaken_belief="that Luna was passing around an obscene fruit",
        clue="a bee crawling from a crack in the basket",
        truth="the fig had simply ripened too far, while the other fruits were sweet and wholesome",
        sharing_act="wash the figs and offer the good ones to the baker and the children",
        ending_image="Purple sweetness shone on little plates, while the overripe fig fed the grateful bees.",
    ),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A folk-tale world about sharing and a repaired misunderstanding."
    )
    parser.add_argument("--name", default="Luna")
    parser.add_argument("--village", default="Mossy Hollow")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trial", type=int, choices=range(len(TRIALS)), default=None)
    parser.add_argument("--sharing", type=int, choices=range(4), default=None)
    parser.add_argument("--misunderstanding", type=int, choices=range(4), default=None)
    parser.add_argument("--ending", type=int, choices=range(3), default=None)
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
    return StoryParams(
        name=args.name,
        village=args.village,
        seed=args.seed,
        trial=args.trial if args.trial is not None else rng.randrange(len(TRIALS)),
        sharing=args.sharing if args.sharing is not None else rng.randrange(4),
        misunderstanding=(
            args.misunderstanding
            if args.misunderstanding is not None
            else rng.randrange(4)
        ),
        ending=args.ending if args.ending is not None else rng.randrange(3),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("The tale needs a storyteller's name.")
    if not params.village.strip():
        raise StoryError("The village name cannot be empty.")
    if not 0 <= params.trial < len(TRIALS):
        raise StoryError("That folk-tale trial does not exist.")
    if not 0 <= params.sharing < 4:
        raise StoryError("The sharing choice is outside the story.")
    if not 0 <= params.misunderstanding < 4:
        raise StoryError("The misunderstanding choice is outside the story.")
    if not 0 <= params.ending < 3:
        raise StoryError("The ending choice is outside the story.")


ASP_RULES = r"""
village(mossy_hollow).
feature(sharing).
feature(misunderstanding).
style(folk_tale).
word(obscene).

valid_domain :- village(mossy_hollow), feature(sharing),
                 feature(misunderstanding), style(folk_tale),
                 word(obscene).

#show valid_domain/0.
#show feature/1.
#show style/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("village", "mossy_hollow"),
            asp.fact("feature", "sharing"),
            asp.fact("feature", "misunderstanding"),
            asp.fact("style", "folk_tale"),
            asp.fact("word", "obscene"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_domain/0."))
    found = set(asp.atoms(model, "valid_domain"))
    expected = {()}
    if found == expected:
        print("OK: clingo matches the Python domain gate.")
        return 0
    print("MISMATCH")
    print("clingo:", sorted(found))
    print("python:", sorted(expected))
    return 1


def build_world(params: StoryParams, trial: Trial) -> World:
    world = World()
    luna = world.add(
        Entity(
            id="luna",
            kind="character",
            label=params.name,
            type="child",
            memes={"kindness": 0.4, "worry": 0.0, "courage": 0.2, "relief": 0.0},
        )
    )
    basket = world.add(
        Entity(
            id="basket",
            label=trial.treasure,
            type="shared_treasure",
            owner=params.name,
            meters={"safety": 0.8, "goodness": 0.8, "oddness": 0.7},
        )
    )
    village = world.add(
        Entity(
            id="village",
            label=params.village,
            type="village",
            meters={"hunger": 0.5, "trust": 0.6, "welcome": 0.7},
        )
    )
    neighbor = world.add(
        Entity(
            id="neighbor",
            kind="character",
            label="Old Mara",
            type="neighbor",
            memes={"suspicion": 0.0, "curiosity": 0.3, "warmth": 0.5},
        )
    )

    openings = (
        f"In {params.village}, people said that a shared meal made a poor day smaller.",
        f"Long ago, in {params.village}, no good thing was meant to stay hidden in one person's cupboard.",
        f"At the edge of {params.village}, the village bell rang whenever someone brought a gift to share.",
        f"The people of {params.village} believed that kind hands could turn a puzzling day toward joy.",
    )
    world.say(f"{params.name} lived in {params.village}, where {openings[params.sharing]}")
    world.say(f"One morning, {params.name} carried {trial.treasure} to {trial.setting}.")
    world.say(
        f"It had {trial.odd_shape}, and from a distance it looked so strange that "
        f"some villagers whispered {trial.mistaken_belief}."
    )
    village.meters["trust"] -= 0.2
    neighbor.memes["suspicion"] += 0.7
    luna.memes["worry"] += 0.5
    world.para()

    world.say(
        f"Old Mara frowned and said, "
        f'"Why have you brought an obscene thing to our table, {params.name}?"'
    )
    world.say(
        f'{params.name} answered, "I brought it to share, but I do not yet know what it is."'
    )
    world.say(
        f'Mara replied, "Then we must look before we judge."'
    )
    world.say(
        f"They looked from three sides, because a picture seen from one side can tell a crooked tale."
    )

    observations = (
        f"The first look made the shape seem even sillier, but it also revealed {trial.clue}.",
        f"The second look showed a clean cloth beneath it, and then they noticed {trial.clue}.",
        f"The third look was made in the bright sun. There they found {trial.clue}.",
        f"At last, {params.name} gently touched the basket and discovered {trial.clue}.",
    )
    world.say(observations[params.misunderstanding])
    world.say(f"Then the misunderstanding loosened: {trial.truth}.")
    basket.meters["goodness"] = 1.0
    neighbor.memes["suspicion"] = 0.0
    luna.memes["courage"] += 0.6
    luna.memes["worry"] -= 0.4
    world.para()

    sharing_lines = (
        f"{params.name} smiled and said, \"Since we have learned the truth, let us {trial.sharing_act}.\"",
        f'"A strange shape should not stop a generous heart," {params.name} said. "Let us {trial.sharing_act}."',
        f'{params.name} lifted the basket and said, "No one should miss a gift because it looks unusual. Let us {trial.sharing_act}."',
        f'"Now that we understand it, we can enjoy it together," said {params.name}. Then they {trial.sharing_act}.',
    )
    world.say(sharing_lines[params.sharing])
    world.say(
        f'Mara nodded. "I was too quick to believe my first glance," she said. '
        f'"Thank you for speaking plainly and sharing kindly."'
    )
    world.say(
        f'{params.name} replied, "And thank you for asking instead of turning away."'
    )
    village.meters["hunger"] = 0.0
    village.meters["trust"] = 1.0
    village.meters["welcome"] = 1.0
    neighbor.memes["warmth"] += 0.5
    luna.memes["relief"] += 0.8
    luna.memes["kindness"] = 1.0
    world.para()

    endings = (
        f"From that day on, the villagers looked twice before calling anything obscene, and they looked once more before wasting a gift.",
        f"The village children made a rule: ask a question before making a judgment, and make room before taking the last piece.",
        f"Whenever a puzzling shape appeared at market, Mara rang the bell and called, \"Come, let us understand it together!\"",
    )
    world.say(endings[params.ending])
    world.say(trial.ending_image)

    world.facts.update(
        luna=luna,
        basket=basket,
        village=village,
        neighbor=neighbor,
        trial=trial,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    trial: Trial = world.facts["trial"]
    return [
        f"Tell a gentle folk tale about {world.facts['luna'].label}, sharing, and a misunderstanding about {trial.treasure}.",
        f"Write a child-friendly story in which something looks obscene at first but has an innocent explanation.",
        "Show two characters speaking honestly, discovering the truth, and sharing the corrected gift.",
    ]


def story_qa(world: World) -> list[QAItem]:
    trial: Trial = world.facts["trial"]
    params: StoryParams = world.facts["params"]
    return [
        QAItem(
            question="Who brought the unusual gift?",
            answer=f"{params.name} brought {trial.treasure} to {trial.setting}.",
        ),
        QAItem(
            question="Why did the villagers misunderstand the gift?",
            answer=f"They saw {trial.odd_shape} from a distance and mistakenly thought {trial.mistaken_belief}.",
        ),
        QAItem(
            question="How did the characters learn the truth?",
            answer=f"They stopped to look carefully and noticed {trial.clue}. They then understood that {trial.truth}.",
        ),
        QAItem(
            question="How did sharing repair the problem?",
            answer=f"{params.name} chose to {trial.sharing_act}, so the villagers could enjoy the gift together instead of fearing it.",
        ),
        QAItem(
            question="What lesson did the village learn?",
            answer="The villagers learned to ask questions and look carefully before judging something that seems strange.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means willingly giving part of something so other people can enjoy or use it too.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is a mistaken idea caused by incomplete or confusing information.",
        ),
        QAItem(
            question="Why is it helpful to ask questions?",
            answer="Questions can replace a quick guess with clearer knowledge and help people treat one another fairly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        parts = []
        if entity.meters:
            parts.append(f"meters={entity.meters}")
        if entity.memes:
            parts.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id} ({entity.type}) {' '.join(parts)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params, TRIALS[params.trial])
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_domain/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_domain/0."))
        print(asp.atoms(model, "valid_domain"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index in range(len(TRIALS)):
            rng = random.Random(base_seed + index)
            params = StoryParams(
                name=args.name,
                village=args.village,
                seed=base_seed + index,
                trial=index,
                sharing=rng.randrange(4),
                misunderstanding=rng.randrange(4),
                ending=rng.randrange(3),
            )
            samples.append(generate(params))
    else:
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
