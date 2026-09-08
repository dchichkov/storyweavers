#!/usr/bin/env python3
"""
A tiny comic storyworld about Luna, a wobbly bridge, a shining shard,
and the bravery needed to rescue a picnic basket.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "storyworlds"))
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
    place: str
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


@dataclass
class StoryParams:
    name: str
    companion: str
    animal: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trial:
    title: str
    danger: str
    silly_event: str
    clue: str
    action: str
    truth: str
    salvation: str
    ending: str


NAMES = ["Luna", "Mira", "Tessa", "Nora", "Pip", "Zoe"]
COMPANIONS = ["Ari", "Ben", "Cleo", "Juno", "Max", "Sage"]
ANIMALS = ["goat", "duck", "raccoon", "pony", "llama"]

TRIALS = [
    Trial(
        "the noodle bridge",
        "the little bridge began to sway above a shallow stream",
        "a goat wore the picnic napkin like a royal cape",
        "a bright shard of blue glass caught in the bridge rope",
        "tied the rope to a sturdy post and crawled low, one careful hand at a time",
        "the rope had slipped loose when the goat tugged the napkin",
        "pulled the picnic basket and the goat back to solid ground",
        "the goat bowed, then ate the royal napkin",
    ),
    Trial(
        "the pudding hill",
        "the picnic cart rolled toward a steep hill",
        "three pudding cups bounced like tiny marching drums",
        "a silver shard from the cart bell pointed downhill",
        "wedged a branch behind the wheel and asked the companion to hold the handle",
        "the cart pin had popped out when the llama sneezed",
        "stopped the cart before it reached the blackberry bushes",
        "the llama sneezed again and politely requested a second pudding",
    ),
    Trial(
        "the hat tree",
        "the wind lifted the picnic blanket toward a tall tree",
        "the raccoon landed inside the basket and wore a sandwich as a hat",
        "a golden shard glittered beneath the tree roots",
        "climbed only as high as the low branch and used a long stick to pull the blanket down",
        "the blanket had snagged on a branch while the raccoon chased a cracker",
        "saved the food and guided the raccoon safely away",
        "the raccoon kept the sandwich hat because it matched its eyes",
    ),
    Trial(
        "the sneezy gate",
        "an old gate began to sway while the picnic party stood nearby",
        "the duck sneezed so loudly that everyone said, 'Bless you!' to a bush",
        "a white shard was wedged beneath the gate hinge",
        "cleared the shard with a stick and held the gate while the companion latched it",
        "the shard had jammed the hinge and made the gate wobble",
        "made the path safe for everyone and the duck",
        "the duck sneezed once more, and the bush seemed very grateful",
    ),
]


def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    trial = rng.choice(TRIALS)
    world = World(place="the sunny town picnic grounds")
    child = world.add(Entity(params.name, "character", "child"))
    companion = world.add(Entity(params.companion, "character", "friend"))
    animal = world.add(Entity("animal", "animal", params.animal))
    shard = world.add(Entity("shard", "thing", "shard"))
    basket = world.add(Entity("basket", "thing", "picnic basket"))

    child.memes["bravery"] = 0.0
    child.meters["distance_to_safety"] = 1.0
    shard.meters["noticed"] = 0.0
    basket.meters["safe"] = 0.0

    world.say(
        f"{params.name} and {params.companion} arrived at {world.place} with a picnic basket "
        f"and one extremely confident {params.animal}."
    )
    world.say(f"They had barely spread the blanket when {trial.danger}.")
    world.say(f"At that exact moment, {trial.silly_event}.")
    world.say(
        f'"I have a plan," {params.name} said. "It is a small plan, and I would like it to remain small."'
    )
    world.say(
        f'"I will help," {params.companion} replied. "But if the goat asks me to wear a crown, I am leaving."'
    )

    world.para()
    world.say(
        f"{params.name} took a breath and spotted {trial.clue}. The shard flashed like a tiny "
        f"sunbeam, showing where the trouble began."
    )
    shard.meters["noticed"] = 1.0
    child.memes["bravery"] = 1.0
    world.say(
        f"Bravery did not make the {trial.danger.split(' began')[0]} perfectly still. "
        f"It helped {params.name} choose a safe next step."
    )
    world.say(f"Together, the two friends {trial.action}.")
    world.say(
        f'"Look at that!" {params.name} cried. "The shard was a clue, not a snack."'
    )
    world.say(
        f'"Excellent," said {params.companion}. "I was about to ask the {params.animal} for its opinion."'
    )

    world.para()
    world.say(f"They discovered that {trial.truth}.")
    world.say(f"Their careful work brought salvation to the picnic: they {trial.salvation}.")
    basket.meters["safe"] = 1.0
    child.meters["distance_to_safety"] = 0.0
    world.say(
        f"{params.name} felt brave because bravery meant noticing danger, asking for help, "
        f"and moving carefully instead of pretending to be fearless."
    )
    world.say(
        f"Then {trial.ending}. Everyone laughed, even the {params.animal}, who appeared to "
        f"believe the whole adventure had been organized for its entertainment."
    )

    world.facts.update(
        child=child,
        companion=companion,
        animal=animal,
        shard=shard,
        basket=basket,
        trial=trial,
        place=world.place,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    trial: Trial = world.facts["trial"]
    child: Entity = world.facts["child"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a comic bravery story in which {child.id} follows a shard clue.",
            f"Tell a funny rescue story about sway, salvation, and a picnic problem.",
            f"Write a child-friendly adventure where careful bravery solves {trial.title}.",
        ],
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    companion: Entity = f["companion"]
    trial: Trial = f["trial"]
    return [
        QAItem(
            f"What danger did {child.id} notice?",
            f"{child.id} noticed that {trial.danger}.",
        ),
        QAItem(
            f"What did the shard reveal to {child.id} and {companion.id}?",
            f"The shard showed useful evidence: {trial.clue}. It pointed toward the cause of the trouble.",
        ),
        QAItem(
            "How did bravery help?",
            f"Bravery helped by making the child notice danger, ask for help, and {trial.action}.",
        ),
        QAItem(
            "What caused the problem?",
            f"They discovered that {trial.truth}.",
        ),
        QAItem(
            "How did the story reach salvation?",
            f"The friends {trial.salvation}. This made the picnic safe again.",
        ),
        QAItem(
            "What was funny at the end?",
            f"{trial.ending}. The animal acted as if the adventure were its own show.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does sway mean?",
            "To sway means to move gently from side to side, often because something is loose or affected by wind.",
        ),
        QAItem(
            "What is a shard?",
            "A shard is a small, sharp piece broken from something such as glass, pottery, or metal.",
        ),
        QAItem(
            "What does bravery mean?",
            "Bravery means facing a difficult or frightening situation while still making careful, sensible choices.",
        ),
        QAItem(
            "What does salvation mean in this story?",
            "Salvation means being rescued from danger and brought back to safety.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
dangerous_sway :- sway(bridge), loose(rope).
clue_found :- shard_present, noticed(shard).
brave_choice :- clue_found, asks_for_help, careful_action.
salvation :- brave_choice, basket_safe.
happy_ending :- salvation, laughter.

#show dangerous_sway/0.
#show clue_found/0.
#show brave_choice/0.
#show salvation/0.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("sway", "bridge"),
            asp.fact("loose", "rope"),
            asp.fact("shard_present"),
            asp.fact("noticed", "shard"),
            asp.fact("asks_for_help"),
            asp.fact("careful_action"),
            asp.fact("basket_safe"),
            asp.fact("laughter"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show happy_ending/0."))
    if asp.atoms(model, "happy_ending"):
        print("OK: ASP confirms careful bravery brings salvation and a happy ending.")
        return 0
    print("MISMATCH: ASP did not confirm the happy ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A comic storyworld about sway, salvation, a shard, and bravery."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        animal=args.animal or rng.choice(ANIMALS),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        state = []
        if meters:
            state.append(f"meters={meters}")
        if memes:
            state.append(f"memes={memes}")
        lines.append(f"  {entity.id:10} ({entity.type:9}) {' '.join(state)}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "Ari", "goat", 7101),
    StoryParams("Mira", "Juno", "duck", 7102),
    StoryParams("Tessa", "Max", "raccoon", 7103),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show dangerous_sway/0. #show clue_found/0. #show brave_choice/0. #show salvation/0. #show happy_ending/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show dangerous_sway/0. #show clue_found/0. #show brave_choice/0. "
                "#show salvation/0. #show happy_ending/0."
            )
        )
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(max(0, args.n)):
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
