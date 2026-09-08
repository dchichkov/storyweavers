#!/usr/bin/env python3
"""
A small rhyming storyworld about a promise, a safe haven, sharing, and kindness.
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

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
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
    friend: str
    haven: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trial:
    occasion: str
    trouble: str
    first_plan: str
    clue: str
    repair: str
    lesson: str
    ending: str


NAMES = ["Luna", "Milo", "Nia", "Owen", "Pia", "Theo"]
FRIENDS = ["Tavi", "Mira", "Sol", "Ari", "Bea", "Juno"]
HAVENS = ["the Moonbeam Haven", "the little garden haven", "the warm library haven"]

TRIALS = [
    Trial(
        occasion="a windy afternoon when small birds sought shelter from the rain",
        trouble="the haven had only one bright blanket for the coldest nest",
        first_plan="to hide the blanket under a bench until the storm passed",
        clue="the shivering birds kept looking toward the basket of old scarves",
        repair="cut soft scarf pieces into safe nest liners and shared the blanket by turns",
        lesson="a promise grows stronger when kindness makes room for everyone",
        ending="the haven hummed with warm wings while raindrops tapped a silver song",
    ),
    Trial(
        occasion="a bright morning when neighbors brought berries to the haven",
        trouble="one small basket was nearly empty before the youngest visitors arrived",
        first_plan="to keep the fullest basket behind the painted gate",
        clue="the empty cups were lined in a circle beside the weighing stone",
        repair="counted the berries, divided them fairly, and saved a cup for each latecomer",
        lesson="sharing is fairest when we remember those who have not arrived yet",
        ending="red berries shone like bells, and every guest tasted one sweet spell",
    ),
    Trial(
        occasion="a golden evening when children gathered for a quiet story",
        trouble="the lantern that lit the haven would not glow",
        first_plan="to blame the moon for hiding its light",
        clue="a loose wick lay beside the oil tin, while a dry matchbox sat nearby",
        repair="asked the keeper for help, replaced the wick, and shared the lantern's glow",
        lesson="a careful question can turn a worry into a way to help",
        ending="the lantern bloomed above the floor, and every face became a little door",
    ),
    Trial(
        occasion="a cool noon when travelers came tired to the haven",
        trouble="the water jug held enough for only one thirsty child",
        first_plan="to drink quickly before anyone else could ask",
        clue="the cups were different sizes, though each had the same blue mark",
        repair="filled small cups for everyone and fetched a second jug from the well",
        lesson="kindness means slowing down so no one is left behind",
        ending="the well rope sang, and fresh water made the haven bright as spring",
    ),
]


def tell_story(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    trial = rng.choice(TRIALS)
    opening = rng.choice([
        "In a haven so cozy, where soft breezes blew",
        "By a haven of moonlight and skies painted blue",
        "At a haven tucked under a tall willow tree",
        "Near a haven where kind hearts were happy and free",
    ])
    world = World(place=params.haven)
    child = world.add(Entity(params.name, "character", "child", params.name))
    friend = world.add(Entity(params.friend, "character", "friend", params.friend))
    promise = world.add(Entity("promise", "thing", "promise", "a promise to share"))
    gift = world.add(Entity("gift", "thing", "shared gift", "the haven's needed gift"))

    world.say(
        f"{opening}, {params.name} and {params.friend} agreed to keep the haven safe and true. "
        f"They made a gentle swear: every visitor would find welcome there."
    )
    world.say(
        f"It was {trial.occasion}. Then they discovered that {trial.trouble}. "
        f"The haven felt smaller, and the cheerful song grew faint."
    )
    world.para()
    world.say(
        f"At first, {params.name} thought {trial.first_plan}. "
        f'"Wait," said {params.friend}, "a haven is safe only when its kindness is shared."'
    )
    world.say(
        f'"Let us look closely before we choose," {params.name} replied. '
        f'"The clue may show us what to do."'
    )
    world.say(f"Together they noticed that {trial.clue}.")
    world.para()
    world.say(
        f"The friends kept their swear and {trial.repair}. "
        f"The gift moved from one pair of hands to many, and the worried faces began to glow."
    )
    world.say(
        f'"Now I understand," said {params.name}. "Sharing is not losing what we have; '
        f'it is helping joy arrive everywhere."'
    )
    world.say(
        f'"And kindness listens first," said {params.friend}. '
        f'"That is the lesson we will remember."'
    )
    world.para()
    promise.memes["kept"] = 1.0
    promise.meters["trust"] = 1.0
    gift.meters["shared"] = 1.0
    child.memes["kindness"] = 1.0
    friend.memes["kindness"] = 1.0
    world.say(
        f"The trouble was mended, the lesson was learned, and the haven became welcoming again. "
        f"{trial.ending}"
    )
    world.say(
        f"From that day on, {params.name} and {params.friend} would swear to share with care, "
        f"for kindness makes a haven everywhere."
    )
    world.facts.update(
        child=child,
        friend=friend,
        promise=promise,
        gift=gift,
        trial=trial,
        haven=params.haven,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    trial: Trial = world.facts["trial"]
    child: Entity = world.facts["child"]
    return [
        f"Write a rhyming story about {child.id} keeping a promise to share at a safe haven.",
        f"Tell a child-friendly tale in which sharing and kindness solve this problem: {trial.trouble}.",
        "Write a gentle rhyming story with a clear lesson learned and a warm ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    child: Entity = facts["child"]
    friend: Entity = facts["friend"]
    trial: Trial = facts["trial"]
    return [
        QAItem(
            f"What promise did {child.id} and {friend.id} make?",
            f"They promised to keep the haven welcoming and share with every visitor.",
        ),
        QAItem(
            f"What trouble happened at the haven?",
            f"The trouble was that {trial.trouble}.",
        ),
        QAItem(
            f"What clue helped the friends decide what to do?",
            f"They noticed that {trial.clue}. This clue helped them choose a kinder plan.",
        ),
        QAItem(
            f"How did {child.id} and {friend.id} solve the problem?",
            f"They {trial.repair}. Their sharing helped everyone.",
        ),
        QAItem(
            "What lesson was learned?",
            f"The lesson was that {trial.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does it mean to share?",
            "To share means to let other people use, enjoy, or receive part of what we have.",
        ),
        QAItem(
            "What is kindness?",
            "Kindness is caring about others and choosing helpful, gentle actions.",
        ),
        QAItem(
            "What is a haven?",
            "A haven is a safe, peaceful place where people or animals can rest and feel welcome.",
        ),
        QAItem(
            "What does it mean to swear a promise?",
            "It means to make a serious promise to do something, while remembering to speak honestly and safely.",
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
safe_haven(H) :- haven(H), shared(G), gift(G).
kind_result :- safe_haven(H), promise_kept.
#show safe_haven/1.
#show kind_result/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("haven", "moonbeam_haven"),
        asp.fact("gift", "shared_gift"),
        asp.fact("shared", "shared_gift"),
        asp.fact("promise_kept"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show kind_result/0."))
    if asp.atoms(model, "kind_result"):
        print("OK: ASP reasoning confirms kindness through sharing.")
        return 0
    print("MISMATCH: ASP reasoning did not confirm the kind result.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A rhyming storyworld about a haven, sharing, and kindness."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--haven", choices=HAVENS)
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
        friend=args.friend or rng.choice(FRIENDS),
        haven=args.haven or rng.choice(HAVENS),
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
            f"  {entity.id:10} ({entity.type:12}) {' '.join(details)}".rstrip()
        )
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
    StoryParams("Luna", "Tavi", "the Moonbeam Haven", 7201),
    StoryParams("Milo", "Mira", "the little garden haven", 7202),
    StoryParams("Nia", "Sol", "the warm library haven", 7203),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_haven/1. #show kind_result/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(
            asp_program("#show safe_haven/1. #show kind_result/0.")
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
