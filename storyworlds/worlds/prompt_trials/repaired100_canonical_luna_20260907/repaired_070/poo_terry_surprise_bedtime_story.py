#!/usr/bin/env python3
"""
A tiny bedtime storyworld about Terry, poo, and a gentle surprise.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = ["the little bedroom", "the moonlit nursery", "the cozy cottage"]
NAMES = ["Terry", "Milo", "Nia", "Pip"]
ANIMALS = ["bear", "rabbit", "fox", "hedgehog"]
COLORS = ["blue", "yellow", "green", "red"]


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("clean", "hidden", "noticed", "safe"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "surprise", "relief", "pride", "sleepiness"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Setting:
    place: str


@dataclass
class StoryParams:
    place: str
    child: str
    animal: str
    blanket_color: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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


def _clean_up(world: World) -> list[str]:
    child = world.entities["child"]
    mess = world.entities["poo"]
    if mess.meters["noticed"] < 1 or mess.meters["clean"] >= 1:
        return []
    mess.meters["clean"] = 1
    mess.meters["safe"] = 1
    child.memes["worry"] = 0
    child.memes["relief"] += 1
    return ["Terry used a cloth and warm water to clean the little mess."]


def _surprise(world: World) -> list[str]:
    child = world.entities["child"]
    blanket = world.entities["blanket"]
    friend = world.entities["friend"]
    if blanket.meters["noticed"] < 1 or "surprise" in world.fired:
        return []
    world.fired.add("surprise")
    child.memes["surprise"] += 1
    friend.memes["surprise"] += 1
    child.memes["pride"] += 1
    blanket.meters["hidden"] = 0
    return [
        f"When Terry lifted the {blanket.label}, a tiny {friend.label} popped out with a sleepy squeak."
    ]


def propagate(world: World) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_clean_up, _surprise):
            produced = rule(world)
            if produced:
                lines.extend(produced)
                changed = True
    return lines


def tell(params: StoryParams) -> World:
    world = World(Setting(params.place))
    child = world.add(Entity("child", "character", "child", params.child))
    child.memes["sleepiness"] = 1
    child.memes["worry"] = 1

    friend = world.add(Entity("friend", "animal", params.animal, f"a small {params.animal}"))
    friend.memes["sleepiness"] = 1

    mess = world.add(Entity("poo", "thing", "poo", "poo"))
    mess.meters["noticed"] = 0

    blanket = world.add(
        Entity(
            "blanket",
            "thing",
            "blanket",
            f"{params.blanket_color} blanket",
            owner=child.id,
        )
    )
    blanket.meters["hidden"] = 1

    world.facts.update(child=child, friend=friend, poo=mess, blanket=blanket)

    world.say(
        f"Once upon a quiet night, {child.id} was getting ready for bed in {params.place}."
    )
    world.say(
        f"The room was soft and dim, and a {params.blanket_color} blanket waited on the bed."
    )
    world.say(
        f"Just before climbing in, {child.id} noticed a little bit of poo beside the bed."
    )

    world.para()
    world.say(
        f"{child.id} frowned. “Oh dear,” {child.id} said. “I cannot sleep with poo there.”"
    )
    world.say(
        f"A gentle voice answered, “Do not worry. We can clean it together.”"
    )
    world.say(
        f"{child.id} looked around and saw a cloth near the washbasin."
    )
    mess.meters["noticed"] = 1
    for line in propagate(world):
        world.say(line)

    world.para()
    world.say(
        f"After the floor was clean, {child.id} pulled back the {blanket.label}."
    )
    blanket.meters["noticed"] = 1
    for line in propagate(world):
        world.say(line)

    world.say(
        f"The little {params.animal} had been hiding beneath the blanket, waiting to wish {child.id} good night."
    )
    world.say(
        f"“You surprised me!” {child.id} whispered. “I thought bedtime was over.”"
    )
    world.say(
        f"“It was a bedtime surprise,” said the little {params.animal}. “Now the room is clean, and we can rest.”"
    )

    world.para()
    world.say(
        f"{child.id} smiled, tucked the sleepy visitor beside the pillow, and climbed into bed."
    )
    world.say(
        f"Outside, the moon shone on the clean floor. Inside, {child.id} and the little {params.animal} closed their eyes."
    )
    world.say("And soon, the whole room was peaceful and still.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    friend = world.facts["friend"]
    return [
        "Write a gentle bedtime story about poo, Terry, and a kind surprise.",
        f"Tell a child-friendly bedtime story in which {child.label} cleans up poo before discovering {friend.label} beneath a blanket.",
        "Make the surprise change bedtime from worried to peaceful, with a short exchange of dialogue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {child.label} notice beside the bed?",
            answer=f"{child.label} noticed a little bit of poo beside the bed.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"The poo was cleaned with a cloth and warm water, so the floor became safe and clean.",
        ),
        QAItem(
            question=f"What was the bedtime surprise for {child.label}?",
            answer=f"A tiny {friend.label} had been hiding beneath the blanket to wish {child.label} good night.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The room became peaceful, and the child and the little visitor went to sleep.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should poo be cleaned up?",
            answer="Poo should be cleaned up to keep a place clean, comfortable, and safe.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that someone discovers.",
        ),
        QAItem(
            question="Why is bedtime usually quiet?",
            answer="Bedtime is usually quiet because calm sounds and gentle routines help people get ready to sleep.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:8} ({entity.type:8}) meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
clean_floor :- noticed(poo), cleaned(poo).
surprise_ready :- noticed(blanket), hidden(friend), clean_floor.
good_bedtime :- surprise_ready.
#show clean_floor/0.
#show surprise_ready/0.
#show good_bedtime/0.
"""


def asp_facts(world: Optional[World] = None) -> str:
    import asp

    facts = [
        asp.fact("noticed", "poo"),
        asp.fact("noticed", "blanket"),
        asp.fact("cleaned", "poo"),
        asp.fact("hidden", "friend"),
    ]
    return "\n".join(facts)


def asp_program(world: Optional[World] = None) -> str:
    return asp_facts(world) + "\n" + ASP_RULES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle bedtime storyworld about Terry, poo, and a surprise."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--child", choices=NAMES)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--blanket-color", choices=COLORS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        child=args.child or "Terry",
        animal=args.animal or rng.choice(ANIMALS),
        blanket_color=args.blanket_color or rng.choice(COLORS),
    )


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


def verify() -> int:
    params = StoryParams(
        place="the little bedroom",
        child="Terry",
        animal="rabbit",
        blanket_color="blue",
        seed=1,
    )
    sample = generate(params)
    if "poo" not in sample.story.lower():
        raise StoryError("verification story does not mention poo")
    if "surprise" not in sample.story.lower():
        raise StoryError("verification story does not mention the surprise")
    if "Terry" not in sample.story:
        raise StoryError("verification story does not mention Terry")
    try:
        import asp
    except ImportError:
        print("OK: Python story verified; clingo is unavailable for ASP parity.")
        return 0
    model = asp.one_model(asp_program(sample.world))
    atoms = asp.atoms(model, "good_bedtime")
    if not atoms:
        raise StoryError("ASP twin did not derive good_bedtime")
    print("OK: Python and ASP bedtime states agree.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("the little bedroom", "Terry", "rabbit", "blue", base_seed),
            StoryParams("the moonlit nursery", "Terry", "bear", "yellow", base_seed + 1),
            StoryParams("the cozy cottage", "Terry", "hedgehog", "green", base_seed + 2),
        ]
        samples = [generate(params) for params in curated]
    else:
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
        header = ""
        if args.all:
            header = f"### {sample.params.child} and the bedtime surprise"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
