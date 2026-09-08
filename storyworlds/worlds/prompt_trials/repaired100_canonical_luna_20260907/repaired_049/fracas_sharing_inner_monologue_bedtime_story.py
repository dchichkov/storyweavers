#!/usr/bin/env python3
"""
A gentle bedtime-story world about a small fracas, sharing, and the quiet
thoughts that help friends repair a mistake before sleep.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

STORYWORLDS_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
sys.path.insert(0, STORYWORLDS_ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
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
class Scenario:
    id: str
    opening: str
    obstacle: str
    clue: str
    shared_item: str
    careful_action: str
    result: str
    repair: str
    ending: str


@dataclass
class StoryParams:
    place: str
    child_name: str
    friend_name: str
    animal: str
    blanket: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "moonlit_room": "the moonlit bedroom",
    "cottage_attic": "the warm cottage attic",
    "lantern_nook": "the little lantern nook",
}

ANIMALS = ["rabbit", "kitten", "fox cub", "hedgehog", "fawn"]
BLANKETS = ["blue quilt", "starry blanket", "green knitted cover", "cloud-soft quilt"]
TRAITS = ["thoughtful", "curious", "patient", "gentle", "brave"]
CHILD_NAMES = ["Luna", "Mira", "Nia", "Tessa", "Cleo", "Pia"]
FRIEND_NAMES = ["Noah", "Finn", "Arlo", "Milo", "Sami", "Theo"]

SCENARIOS = [
    Scenario(
        "fallen_stars",
        "The children had made a little sky of paper stars above the bed.",
        "A sudden fracas began when the string slipped, and stars tumbled onto the floor.",
        "One silver star still hung from the curtain, showing that the string had loosened at only one knot.",
        "the soft ribbon and the small basket",
        "shared the basket with the friend, sorted the stars by size, and tied the loose knot again",
        "the paper sky rose safely above the bed once more",
        "they left the basket beside the bed so either child could mend a fallen star",
        "At last, the room grew still, and the stars shone softly above two peaceful sleepers.",
    ),
    Scenario(
        "pillow_mountain",
        "The children were building a pillow mountain for one last bedtime climb.",
        "A loud fracas followed when the tallest pillow slid away and bumped the storybooks.",
        "The smallest pillow had a ribbon underneath it, marking the safest place to begin.",
        "the striped pillow and the storybooks",
        "shared the pillows, moved the books out of the way, and rebuilt the mountain from the floor upward",
        "the mountain became a low, safe hill where both friends could sit",
        "they made a rule that every builder would check the floor before climbing",
        "The pillow hill became a quiet nest, and the final page turned without a wobble.",
    ),
    Scenario(
        "missing_bell",
        "A tiny brass bell was meant to ring when the bedtime story reached its happiest part.",
        "When the bell vanished, a worried fracas sent blankets and cushions sliding everywhere.",
        "A bright thread from the bell's ribbon caught on the wooden toy chest.",
        "the candle lantern and the blue cushion",
        "shared the lantern, looked beneath the chest together, and lifted it only after moving the cushions",
        "the bell was found without anyone stepping on the toys",
        "they placed the bell in a shallow bowl before every story",
        "The bell gave one soft ring, then rested in its bowl while the children drifted to sleep.",
    ),
    Scenario(
        "shadow_shapes",
        "A lamp on the dresser made friendly shapes on the wall.",
        "A small fracas started when one child thought the largest shadow was a monster.",
        "The shadow changed when the lamp moved, while the toy bear stayed still.",
        "the lamp handle and the toy bear",
        "shared the handle, moved the lamp slowly, and placed the bear where both children could see it",
        "the monster became a bear with round ears and a very small nose",
        "they agreed to ask what a shadow was copying before feeling afraid",
        "The bear-shadow bowed on the wall, and the room settled into a warm golden hush.",
    ),
]


def meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = meter(entity, key) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = meme(entity, key) + amount


def valid_combos() -> list[tuple[str, str]]:
    return [(place, "bedtime") for place in PLACES]


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown bedtime place: {params.place}.")
    if not params.child_name.strip() or not params.friend_name.strip():
        raise StoryError("Both children need names.")
    if params.child_name.strip().lower() == params.friend_name.strip().lower():
        raise StoryError("The two bedtime friends need different names.")


def choose_scenario(params: StoryParams) -> Scenario:
    value = params.seed
    if value is None:
        value = sum((i + 1) * ord(ch) for i, ch in enumerate(params.child_name + params.friend_name))
    return SCENARIOS[value % len(SCENARIOS)]


def tell(world: World, params: StoryParams) -> None:
    scenario = choose_scenario(params)
    child = world.add(Entity(params.child_name, "child", params.child_name))
    friend = world.add(Entity(params.friend_name, "friend", params.friend_name))
    animal = world.add(Entity("animal", "animal", params.animal))
    blanket = world.add(Entity("blanket", "thing", params.blanket))

    add_meme(child, "sleepiness", 1.0)
    add_meme(child, "care", 1.0)
    add_meme(friend, "worry", 1.0)

    world.say(
        f"In {PLACES[params.place]}, where the moon laid a pale path across the floor, "
        f"{params.child_name} and {params.friend_name} were getting ready for bed."
    )
    world.say(
        f"Their sleepy {params.animal} friend curled beside the {params.blanket}, "
        f"and the room smelled faintly of lavender."
    )
    world.say(f"{scenario.opening} {params.child_name} felt {params.trait} and happy.")
    world.para()

    world.say(f"Then came a little fracas. {scenario.obstacle}")
    add_meme(child, "worry", 1.0)
    add_meme(friend, "worry", 1.0)
    world.say(
        f"{params.child_name} thought, “I wanted everything to be peaceful. "
        f"Perhaps I should listen before I try to fix it.”"
    )
    world.say(
        f'"Let us stop for a breath," said {params.child_name}. '
        f'"What did you notice?"'
    )
    world.say(
        f'"I noticed this," said {params.friend_name}. '
        f'"{scenario.clue}"'
    )
    world.say(
        f'"Then we can look together," said {params.child_name}. '
        f'"Would you share the {scenario.shared_item} with me?"'
    )
    add_meter(child, "sharing", 1.0)
    add_meter(friend, "sharing", 1.0)
    add_meme(friend, "trust", 1.0)

    world.para()
    world.say(
        f"They shared the work instead of pulling at the same time. "
        f"{params.child_name} {scenario.careful_action}."
    )
    add_meter(child, "careful_action", 1.0)
    add_meter(friend, "careful_action", 1.0)
    world.say(f"At once, {scenario.result}.")
    add_meme(child, "relief", 1.0)
    add_meme(friend, "relief", 1.0)
    world.say(
        f"{params.child_name} thought, “Sharing did not make the repair smaller. "
        f"It made the worry smaller.”"
    )
    world.say(
        f"{params.friend_name} smiled and said, "
        f'"Next time, we can share the listening before the fracas grows."'
    )
    world.say(f"They made one gentle repair: {scenario.repair}.")
    world.para()

    add_meme(child, "sleepiness", 1.0)
    add_meme(friend, "sleepiness", 1.0)
    world.say(
        f"The {params.animal} gave a tiny sigh, and both children tucked themselves "
        f"under the {params.blanket}."
    )
    world.say(
        f"{scenario.ending} The moon kept watch, and every quiet thought found a place to rest."
    )

    world.facts.update(
        child=child,
        friend=friend,
        animal=animal,
        blanket=blanket,
        scenario=scenario,
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World()
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    scenario = world.facts["scenario"]
    child = world.facts["child"]
    friend = world.facts["friend"]
    return [
        f"Write a bedtime story about {child.label} and {friend.label} sharing after a small fracas.",
        f"Tell a gentle story in which {child.label} uses an inner thought to pause and listen.",
        f"Write a sleepy tale about this problem: {scenario.obstacle}",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    child = facts["child"]
    friend = facts["friend"]
    scenario = facts["scenario"]
    return [
        QAItem(
            question=f"What caused the fracas in {child.label}'s bedtime room?",
            answer=f"The fracas began because {scenario.obstacle}",
        ),
        QAItem(
            question=f"What did {child.label} think before trying to fix the problem?",
            answer=f"{child.label} thought, “I wanted everything to be peaceful. Perhaps I should listen before I try to fix it.”",
        ),
        QAItem(
            question=f"What clue did {friend.label} notice?",
            answer=f"{friend.label} noticed that {scenario.clue}",
        ),
        QAItem(
            question=f"What did the friends share?",
            answer=f"They shared {scenario.shared_item} so they could repair the bedtime problem together.",
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=f"They worked carefully together: {child.label} {scenario.careful_action}. As a result, {scenario.result}.",
        ),
        QAItem(
            question="What did the friends learn?",
            answer=f"They learned that {scenario.repair} Sharing listening and work helped the fracas become peaceful.",
        ),
        QAItem(
            question=f"How did the story end for {child.label} and {friend.label}?",
            answer=f"{scenario.ending} They tucked themselves under the blanket and went to sleep.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fracas?",
            answer="A fracas is a noisy little quarrel or commotion.",
        ),
        QAItem(
            question="Why can sharing help during a problem?",
            answer="Sharing lets people combine their tools, observations, and care, so they can solve a problem together.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's quiet thought inside their mind.",
        ),
        QAItem(
            question="Why are bedtime stories often gentle?",
            answer="Bedtime stories are often gentle because calm images and peaceful endings help listeners feel safe and ready to rest.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: {entity.kind} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
place(moonlit_room).
place(cottage_attic).
place(lantern_nook).
theme(bedtime).
valid(P, bedtime) :- place(P).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("place", place) for place in PLACES) + "\n" + asp.fact("theme", "bedtime")


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        py = set(valid_combos())
        cl = set(asp_valid_combos())
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if py != cl:
        print(f"MISMATCH: Python={sorted(py)} ASP={sorted(cl)}")
        return 1
    for params in curated_params():
        generate(params)
    print(f"OK: ASP matches Python ({len(py)} combinations); generated stories pass.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A bedtime storyworld about fracas, sharing, and inner monologue."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--child-name")
    parser.add_argument("--friend-name")
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--blanket", choices=BLANKETS)
    parser.add_argument("--trait", choices=TRAITS)
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
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    friend_name = args.friend_name or rng.choice(
        [name for name in FRIEND_NAMES if name.lower() != child_name.lower()]
    )
    return StoryParams(
        place=args.place or rng.choice(sorted(PLACES)),
        child_name=child_name,
        friend_name=friend_name,
        animal=args.animal or rng.choice(ANIMALS),
        blanket=args.blanket or rng.choice(BLANKETS),
        trait=args.trait or rng.choice(TRAITS),
    )


def curated_params() -> list[StoryParams]:
    return [
        StoryParams("moonlit_room", "Luna", "Finn", "rabbit", "starry blanket", "thoughtful", 11),
        StoryParams("cottage_attic", "Mira", "Arlo", "kitten", "blue quilt", "curious", 23),
        StoryParams("lantern_nook", "Nia", "Milo", "hedgehog", "green knitted cover", "patient", 37),
        StoryParams("moonlit_room", "Tessa", "Sami", "fawn", "cloud-soft quilt", "gentle", 41),
    ]


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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in curated_params()]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(args.n, 0)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.child_name} and {sample.params.friend_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
