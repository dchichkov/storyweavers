#!/usr/bin/env python3
"""
A small adventure storyworld about Squirt, a quest, and problem solving.

Squirt is a tiny water sprite who must carry a precious drop across a sunny
garden to help a thirsty moonflower. The path is blocked, but careful clues,
a helpful friend, and brave problem solving turn the quest into a success.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
for path in (ROOT, os.path.join(ROOT, "storyworlds")):
    if path not in sys.path:
        sys.path.insert(0, path)

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
class Scene:
    place: str
    quest: str
    destination: str
    prize: str


@dataclass
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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


@dataclass
class StoryParams:
    place: str
    quest_kind: str
    squirt_name: str
    squirt_type: str
    helper_name: str
    helper_type: str
    challenge: str
    seed: Optional[int] = None


PLACES = {
    "sunny_garden": Scene(
        place="the sunny garden",
        quest="carry a bright drop of water",
        destination="the thirsty moonflower",
        prize="a silver seed",
    ),
    "whispering_grove": Scene(
        place="the whispering grove",
        quest="deliver a cool drop of water",
        destination="a sleepy fern",
        prize="a pearl-green leaf",
    ),
    "copper_canyon": Scene(
        place="the copper canyon",
        quest="guide a shining drop of water",
        destination="a tiny cloud cactus",
        prize="a copper bell",
    ),
}

CHALLENGES = {
    "fallen_bridge": "a fallen twig blocked the narrow bridge",
    "three_gates": "three little gates stood in the wrong order",
    "dry_riddle": "a dry stone asked a riddle before opening the path",
}

SQUIRT_NAMES = ["Squirt", "Ripple", "Dewdrop", "Bubbles"]
HELPER_NAMES = ["Pip", "Moss", "Tala", "Clover"]


@dataclass(frozen=True)
class Arc:
    name: str
    obstacle: str
    clue: str
    action: str
    result: str
    ending: str


ARCS = (
    Arc(
        name="twig_bridge",
        obstacle="The water drop could not pass because a fallen twig blocked the narrow bridge.",
        clue="Squirt noticed three round stones beside the twig, each marked with a tiny arrow.",
        action="Squirt and Pip placed the stones beneath the twig and rolled it aside like a little bridge gate.",
        result="The drop crossed safely, and Squirt learned that a large-looking obstacle can have a small solution.",
        ending="The moonflower opened one white petal, and the silver seed gleamed in its center.",
    ),
    Arc(
        name="mixed_gates",
        obstacle="Three leaf gates blocked the path, but their colors had been scrambled by the wind.",
        clue="Squirt remembered that the river, sky, and grass made the order blue, yellow, then green.",
        action="Squirt and Tala rearranged the gates by color instead of pushing them harder.",
        result="The path opened because Squirt used a pattern rather than guessing.",
        ending="The fern lifted its curled leaves, and a pearl-green leaf floated down like a medal.",
    ),
    Arc(
        name="stone_riddle",
        obstacle="A dry stone rolled in front of the path and asked, 'What grows smaller when it is shared?'",
        clue="Pip whispered that the answer might be a shadow, but Squirt listened to the thirsty plants nearby.",
        action="Squirt shared a tiny splash with the stone's dusty moss, and the moss revealed the answer: a worry.",
        result="The stone moved aside, showing that kindness and careful thinking could solve the same problem.",
        ending="The cloud cactus rang its copper bell, and the sound bounced happily through the canyon.",
    ),
)


OPENINGS = (
    "At sunrise, {squirt} received a brave little quest.",
    "The day began with a message carried on a leaf: {squirt} was needed for an important quest.",
    "In {place}, the plants were waiting, and {squirt} was ready to help.",
)

DIALOGUES = (
    '"Should we hurry?" {squirt} asked. "We should notice first," said {helper}.',
    '"I cannot solve this alone," said {squirt}. {helper} smiled and answered, "Then we will solve it together."',
    '{helper} asked, "What does the path tell us?" {squirt} replied, "Let us look before we leap."',
)


def simulate(params: StoryParams) -> World:
    scene = PLACES[params.place]
    world = World(scene)
    squirt = world.add(Entity(params.squirt_name, "character", params.squirt_type, params.squirt_name))
    helper = world.add(Entity(params.helper_name, "character", params.helper_type, params.helper_name))
    drop = world.add(Entity("water_drop", "thing", "water", "the bright water drop"))
    destination = world.add(Entity("destination", "thing", "plant", scene.destination))

    rng = random.Random(params.seed if params.seed is not None else 0)
    arc = rng.choice(ARCS)
    opening = rng.choice(OPENINGS)
    dialogue = rng.choice(DIALOGUES)

    world.facts.update(
        squirt=squirt,
        helper=helper,
        drop=drop,
        destination=destination,
        arc=arc,
        challenge=CHALLENGES[params.challenge],
        dialogue=dialogue,
    )

    world.say(opening.format(squirt=squirt.label, place=scene.place))
    world.say(
        f"The quest was to {scene.quest} from the little spring to {scene.destination} "
        f"before the warm sun dried it away."
    )
    world.say(
        f"{squirt.label} carried {drop.label} in a curled leaf while {helper.label} "
        f"walked close enough to spot clues."
    )
    world.para()

    drop.meters["carried"] = 1.0
    squirt.memes["brave"] = 1.0
    world.say(arc.obstacle)
    world.say(f"It was {world.facts['challenge']}, so the direct path was no longer safe.")
    world.say(arc.clue)
    world.say(dialogue)
    world.para()

    helper.memes["helpful"] = 1.0
    squirt.memes["curious"] = 1.0
    world.say(arc.action)
    drop.meters["protected"] = 1.0
    world.say(
        f"They kept the leaf level, because one careless tilt could spill the drop before "
        f"it reached {scene.destination}."
    )
    world.para()

    drop.meters["delivered"] = 1.0
    destination.meters["watered"] = 1.0
    squirt.memes["proud"] = 1.0
    world.say(
        f"At last, {squirt.label} tipped the bright drop onto {scene.destination}. "
        f"The plant drank deeply."
    )
    world.say(arc.result)
    world.say(arc.ending)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    scene = world.scene
    squirt: Entity = world.facts["squirt"]
    helper: Entity = world.facts["helper"]
    return [
        f"Write an adventure about {squirt.label} completing a quest in {scene.place}.",
        f"Tell a problem-solving story where {squirt.label} and {helper.label} protect a water drop.",
        f"Write a child-friendly adventure with a blocked path, spoken dialogue, careful clues, and a concrete ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scene = world.scene
    squirt: Entity = world.facts["squirt"]
    helper: Entity = world.facts["helper"]
    arc: Arc = world.facts["arc"]
    return [
        QAItem(
            question=f"What quest did {squirt.label} undertake?",
            answer=f"{squirt.label} had to {scene.quest} to {scene.destination} before the sun dried it away.",
        ),
        QAItem(
            question=f"What problem stopped {squirt.label} and {helper.label}?",
            answer=arc.obstacle,
        ),
        QAItem(
            question=f"How did {squirt.label} solve the problem?",
            answer=arc.action,
        ),
        QAItem(
            question=f"What happened at the end of the quest?",
            answer=f"{squirt.label} delivered the water to {scene.destination}, which drank deeply and rewarded the quest with {scene.prize}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is careful observation useful during a quest?",
            answer="Careful observation can reveal clues, patterns, and safe choices that are easy to miss when someone only rushes ahead.",
        ),
        QAItem(
            question="Why can teamwork help solve a problem?",
            answer="Teamwork lets people share ideas, notice different details, and combine their strengths when one person cannot solve a problem alone.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful journey or challenge undertaken to reach a goal or help someone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
reasonable_quest(S, H, D) :- squirt(S), helper(H), destination(D), carries(S, drop), helps(H, S).
safe_delivery(D) :- destination(D), protected(drop), delivered(drop), waters(drop, D).
solved(S, D) :- squirt(S), destination(D), safe_delivery(D).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for place_id, scene in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("destination", scene.destination.replace(" ", "_")))
    for name in SQUIRT_NAMES:
        lines.append(asp.fact("squirt", name.lower()))
    for name in HELPER_NAMES:
        lines.append(asp.fact("helper", name.lower()))
    lines.extend(
        [
            asp.fact("drop", "drop"),
            asp.fact("carries", "squirt", "drop"),
            asp.fact("helps", "pip", "squirt"),
            asp.fact("protected", "drop"),
            asp.fact("delivered", "drop"),
            asp.fact("waters", "drop", "destination"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show solved/2."))
    solved = asp.atoms(model, "solved")
    if not solved:
        print("ASP verification failed: no solved quest.")
        return 1
    print(f"OK: ASP quest solved with {len(solved)} shown atom(s).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Squirt quest problem-solving adventure.")
    parser.add_argument("--place", choices=list(PLACES))
    parser.add_argument("--quest-kind", default="water_delivery")
    parser.add_argument("--squirt-name", choices=SQUIRT_NAMES)
    parser.add_argument("--helper-name", choices=HELPER_NAMES)
    parser.add_argument("--challenge", choices=list(CHALLENGES))
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
    place = args.place or rng.choice(list(PLACES))
    squirt_name = args.squirt_name or rng.choice(SQUIRT_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    if squirt_name == helper_name:
        raise StoryError("Squirt and the helper must be different characters.")
    challenge = args.challenge or rng.choice(list(CHALLENGES))
    squirt_type = "sprite"
    helper_type = "moss_friend"
    return StoryParams(
        place=place,
        quest_kind=args.quest_kind,
        squirt_name=squirt_name,
        squirt_type=squirt_type,
        helper_name=helper_name,
        helper_type=helper_type,
        challenge=challenge,
        seed=rng.randrange(2**31),
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.label}: meters={dict(entity.meters)}, "
                f"memes={dict(entity.memes)}"
            )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show solved/2."))
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    curated = [
        StoryParams(
            place="sunny_garden",
            quest_kind="water_delivery",
            squirt_name="Squirt",
            squirt_type="sprite",
            helper_name="Pip",
            helper_type="moss_friend",
            challenge="fallen_bridge",
            seed=101,
        ),
        StoryParams(
            place="whispering_grove",
            quest_kind="water_delivery",
            squirt_name="Ripple",
            squirt_type="sprite",
            helper_name="Tala",
            helper_type="moss_friend",
            challenge="three_gates",
            seed=202,
        ),
        StoryParams(
            place="copper_canyon",
            quest_kind="water_delivery",
            squirt_name="Dewdrop",
            squirt_type="sprite",
            helper_name="Clover",
            helper_type="moss_friend",
            challenge="dry_riddle",
            seed=303,
        ),
    ]

    if args.all:
        samples = [generate(params) for params in curated]
    else:
        samples = []
        seen = set()
        for index in range(max(args.n, 1) * 20):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + index))
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
            header=f"### story {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
