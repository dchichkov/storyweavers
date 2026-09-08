#!/usr/bin/env python3
"""
A small mystery storyworld about a helpful mechanism, friendship, and a
cautionary twist.

Luna discovers that the brass bell mechanism in an old clock tower has stopped.
With her friend Rowan, she follows a trail of clues, learns to be cautious
about a tempting shortcut, and discovers that the missing piece was moved by a
friendly magpie trying to protect it from rain.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(
        default_factory=lambda: {
            "distance": 0.0,
            "safety": 0.0,
            "working": 0.0,
            "visibility": 0.0,
        }
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "worry": 0.0,
            "courage": 0.0,
            "trust": 0.0,
            "curiosity": 0.0,
            "relief": 0.0,
            "joy": 0.0,
        }
    )


@dataclass
class Setting:
    place: str = "the old moon-clock tower"


@dataclass
class StoryParams:
    luna_name: str
    luna_type: str
    friend_name: str
    friend_type: str
    mechanism_name: str
    clue_style: str
    scenario_index: int = 0
    detail_variant: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace_log: list[str] = []

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

    def log(self, text: str) -> None:
        self.trace_log.append(text)


SCENARIOS = [
    {
        "opening": "At midnight, the tower clock gave one tiny click and then fell silent",
        "problem": "The bell's brass mechanism had stopped, and the moon festival would begin at dawn.",
        "clue": "A thread of blue wool led from the silent gear to a locked balcony door.",
        "false_lead": "A bright scratch on the stair rail seemed to point upward, but it ended at a loose weather vane.",
        "caution": "The upper stair was slick with dew, so climbing quickly could send both friends tumbling.",
        "turn": "Rowan noticed that the blue thread was caught on a small wooden cover, not pulled toward the roof.",
        "action": "Luna held the lantern low while Rowan loosened the cover with a flat shell and kept the tiny screws in a cup.",
        "twist": "Behind the cover lay the missing pin, wrapped in leaves by a magpie that had hidden it from the rain.",
        "result": "After they dried the pin and fitted it back into the mechanism, the bell rang across the sleeping village.",
        "lesson": "a mystery deserves careful looking, and a friend is safer than a hurried guess",
        "image": "the moon-clock shone above the rooftops while two friends shared the warm bell rope",
        "dialogue": "A clue can sparkle and still be wrong. Let us test it before we trust it.",
    },
    {
        "opening": "Just before sunrise, a shiver ran through the clock tower",
        "problem": "Its bell mechanism would not turn, leaving the village without its morning signal.",
        "clue": "Three crumbs of red berry cake rested beside the lowest gear.",
        "false_lead": "The friends followed muddy pawprints into the square, where they found only a sleepy dog.",
        "caution": "The heavy counterweight hung above the passage, and touching the wrong rope could make it swing.",
        "turn": "Luna saw that the crumbs formed a little arrow toward a narrow maintenance hatch.",
        "action": "They tied the counterweight rope still, opened the hatch together, and examined the gears without reaching blindly.",
        "twist": "Inside, a hedgehog had tucked the missing spring beneath moss while sheltering from a storm.",
        "result": "The clean spring restored the mechanism, and the first bell called bakers and gardeners to their work.",
        "lesson": "a safe plan protects both the helpers and the hidden creature",
        "image": "the first sunbeam touched the bell as the hedgehog slept beneath a basket",
        "dialogue": "We can solve the puzzle without frightening whoever left the crumbs.",
    },
    {
        "opening": "When silver clouds covered the moon, the clock tower began ticking backward",
        "problem": "The old mechanism had lost its small gear, and the village clocks disagreed.",
        "clue": "A line of flour crossed the floor and stopped beneath the keeper's workbench.",
        "false_lead": "A note on the bench blamed the wind, but its ink was still wet.",
        "caution": "The workbench was crowded with sharp tools, so searching by feel would be dangerous.",
        "turn": "Rowan used a mirror to look beneath the bench and spotted a gear inside a flour tin.",
        "action": "Luna moved the tools aside while Rowan slid the tin out with a wooden ruler.",
        "twist": "The keeper had placed the gear there on purpose after hearing a crack; the missing part was a warning, not a theft.",
        "result": "They found the crack, replaced the worn gear, and made the clock safe before setting it again.",
        "lesson": "a missing part may be a warning, so repair should begin with understanding",
        "image": "the clocks agreed at last, and the moonlit hands pointed to a peaceful hour",
        "dialogue": "Before we put the piece back, we should ask why someone removed it.",
    },
    {
        "opening": "On the evening of the lantern parade, the tower's little bell refused to ring",
        "problem": "The bell mechanism was jammed, and the parade route depended on its signal.",
        "clue": "A line of silver dust glittered from the bell room to a nest above the rafters.",
        "false_lead": "The friends first blamed a broken window, though the dust did not reach it.",
        "caution": "The rafters were high, and one careless step could shake the nest loose.",
        "turn": "Luna realized the silver dust came from the bell's polishing cloth, which had been dragged upward.",
        "action": "They built a broad platform from empty crates and waited for the mother bird to fly out before looking inside the nest.",
        "twist": "The missing lever was there, keeping three warm eggs from rolling toward a hole.",
        "result": "They moved the eggs to a safer nest box, returned the lever, and rang the parade bell gently.",
        "lesson": "helping a friend can include helping the small stranger at the center of the mystery",
        "image": "lanterns bobbed below while the mother bird settled beside her safe eggs",
        "dialogue": "We will not snatch the lever until we know who needs it.",
    },
]


OPENINGS = [
    "Luna had never heard the tower so quiet",
    "Rowan noticed the silence before anyone else",
    "The first strange sign was a clock hand that would not move",
    "Everyone in the village expected the tower to ring",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mystery storyworld about a mechanism, friendship, and a cautious twist."
    )
    parser.add_argument("--name")
    parser.add_argument("--type")
    parser.add_argument("--friend")
    parser.add_argument("--friend-type")
    parser.add_argument("--mechanism")
    parser.add_argument("--clue-style")
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
        luna_name=args.name or rng.choice(["Luna", "Mira", "Nell", "Suri"]),
        luna_type=args.type or rng.choice(["rabbit", "fox", "mouse", "cat"]),
        friend_name=args.friend or rng.choice(["Rowan", "Pip", "Tavi", "Moss"]),
        friend_type=args.friend_type or rng.choice(["badger", "raccoon", "squirrel", "otter"]),
        mechanism_name=args.mechanism or rng.choice(
            ["brass bell mechanism", "moon-clock mechanism", "tower bell mechanism"]
        ),
        clue_style=args.clue_style or rng.choice(
            ["a thread", "a line of dust", "a trail of crumbs", "a faint scratch"]
        ),
        scenario_index=rng.randrange(len(SCENARIOS)),
        detail_variant=rng.randrange(10000),
    )


def _choose(items: list[str], variant: int, offset: int) -> str:
    return items[(variant + offset) % len(items)]


def tell(params: StoryParams) -> World:
    scenario = SCENARIOS[params.scenario_index % len(SCENARIOS)]
    world = World(Setting())

    luna = world.add(
        Entity(id="luna", kind="animal", type=params.luna_type, label=params.luna_name)
    )
    friend = world.add(
        Entity(id="friend", kind="animal", type=params.friend_type, label=params.friend_name)
    )
    mechanism = world.add(
        Entity(
            id="mechanism",
            kind="thing",
            type="mechanism",
            label=params.mechanism_name,
        )
    )
    mystery = world.add(
        Entity(id="mystery", kind="thing", type="mystery", label="the mystery")
    )
    magpie = world.add(
        Entity(id="helper", kind="animal", type="magpie", label="a watchful magpie")
    )

    world.facts.update(
        luna=luna,
        friend=friend,
        mechanism=mechanism,
        mystery=mystery,
        helper=magpie,
        scenario=scenario,
    )

    luna.memes["curiosity"] = 1.0
    friend.memes["trust"] = 1.0
    mechanism.meters["working"] = 0.0
    mechanism.meters["safety"] = 0.4

    world.say(
        f'{_choose(OPENINGS, params.detail_variant, 0)}. '
        f'{scenario["opening"]}.'
    )
    world.say(
        f'{luna.label} the {luna.type} and {friend.label} the {friend.type} hurried to '
        f'{world.setting.place}, where the {params.mechanism_name} guarded the village time.'
    )
    world.say(f'{scenario["problem"]} The silence made the coming celebration feel uncertain.')
    world.para()

    luna.memes["worry"] = 1.0
    friend.memes["courage"] = 0.8
    world.say(
        f'{scenario["clue"]} It was the first useful sign in a mystery that had no clear beginning.'
    )
    world.say(
        f'{scenario["false_lead"]} {luna.label} nearly followed it, but {friend.label} touched '
        f'{luna.label}\'s sleeve.'
    )
    world.say(
        f'"{scenario["dialogue"]}" {friend.label} said. '
        f'"Then we can follow the clue together."'
    )
    world.para()

    mechanism.meters["distance"] = 1.0
    mechanism.meters["visibility"] = 0.5
    world.say(scenario["caution"])
    world.say(
        f'{luna.label} took a slow breath. "You are right. We will make the tower safer before we search."'
    )
    world.say(f'{scenario["turn"]} Their friendship changed the search from a chase into a careful investigation.')
    world.say(scenario["action"])
    world.para()

    mechanism.meters["safety"] = 1.0
    mechanism.meters["visibility"] = 1.0
    luna.memes["courage"] = 1.0
    friend.memes["trust"] = 2.0
    world.say(f'The hidden place revealed a surprising answer. {scenario["twist"]}')
    world.say(
        f'{luna.label} and {friend.label} helped the small creature first, then examined the '
        f'{params.mechanism_name} without forcing it.'
    )
    world.say(scenario["result"])
    mechanism.meters["working"] = 1.0
    luna.memes["relief"] = 1.0
    friend.memes["joy"] = 1.0
    world.para()

    world.say(
        f'{luna.label} understood that {scenario["lesson"]}. '
        f'{friend.label} smiled because neither friend had needed to solve the mystery alone.'
    )
    world.say(f'{scenario["image"]}.')
    world.log(f"scenario={params.scenario_index % len(SCENARIOS)}")
    world.log("mechanism_working=1")
    world.log("friends_used_caution=1")
    world.log("twist_revealed=1")
    return world


def generation_prompts(world: World) -> list[str]:
    scenario = world.facts["scenario"]
    luna: Entity = world.facts["luna"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    mechanism: Entity = world.facts["mechanism"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly mystery about {luna.label} and {friend.label} repairing a {mechanism.label}.",
        f"Tell a friendship story in which caution prevents danger and a twist explains the missing part of the {mechanism.label}.",
        f'Include a clue, a false lead, spoken dialogue, and the idea that "{scenario["lesson"]}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario = world.facts["scenario"]
    luna: Entity = world.facts["luna"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    mechanism: Entity = world.facts["mechanism"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {luna.label} and {friend.label} investigate the {mechanism.label}?",
            answer=f"They investigated because {scenario['problem']} The village needed the mechanism working again.",
        ),
        QAItem(
            question="What clue helped the friends?",
            answer=f"{scenario['clue']} It pointed them toward a careful search rather than a quick guess.",
        ),
        QAItem(
            question="What caution did the friends follow?",
            answer=f"{scenario['caution']} They made the place safer before touching the mechanism.",
        ),
        QAItem(
            question="What was the mystery's twist?",
            answer=f"{scenario['twist']} The missing piece had been hidden for a protective reason, not simply stolen.",
        ),
        QAItem(
            question=f"How did friendship help {luna.label} and {friend.label}?",
            answer=f"They listened to each other, tested clues together, and solved the problem without taking a dangerous shortcut.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move, signal, or perform a task.",
        ),
        QAItem(
            question="Why is caution useful in a mystery?",
            answer="Caution helps people notice evidence, avoid danger, and avoid damaging something before they understand it.",
        ),
        QAItem(
            question="What makes a friendship helpful?",
            answer="A helpful friendship includes listening, sharing ideas, protecting one another, and solving problems together.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change in understanding that explains earlier clues in a new way.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        details = [f"type={entity.type}"]
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: " + ", ".join(details))
    lines.extend(f"event: {entry}" for entry in world.trace_log)
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
entity(luna).
entity(friend).
entity(mechanism).
entity(helper).

clue_found.
friends_cautious.
helper_protected.
mechanism_repaired.

mystery_solved :-
    clue_found,
    friends_cautious,
    helper_protected,
    mechanism_repaired.

friendship_strengthened :-
    mystery_solved.

happy_ending :-
    mystery_solved,
    friendship_strengthened.

#show mystery_solved/0.
#show friendship_strengthened/0.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("clue_found"),
            asp.fact("friends_cautious"),
            asp.fact("helper_protected"),
            asp.fact("mechanism_repaired"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show mystery_solved/0. "
            "#show friendship_strengthened/0. "
            "#show happy_ending/0."
        )
    )
    names = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {
        "mystery_solved/0",
        "friendship_strengthened/0",
        "happy_ending/0",
    }
    if names != expected:
        print(f"MISMATCH: {sorted(names)} != {sorted(expected)}")
        return 1

    for params in CURATED:
        sample = generate(params)
        required = ["mechanism", "friend", "careful", "mystery"]
        if any(word not in sample.story.lower() for word in required):
            print("MISMATCH: generated story lacks required narrative evidence")
            return 1
        if not sample.story_qa or not sample.world_qa:
            print("MISMATCH: generated story lacks QA")
            return 1

    print("OK: ASP parity and generated-story checks passed.")
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        luna_name="Luna",
        luna_type="rabbit",
        friend_name="Rowan",
        friend_type="badger",
        mechanism_name="brass bell mechanism",
        clue_style="a thread",
        scenario_index=0,
        detail_variant=1,
    ),
    StoryParams(
        luna_name="Mira",
        luna_type="fox",
        friend_name="Pip",
        friend_type="raccoon",
        mechanism_name="moon-clock mechanism",
        clue_style="a line of dust",
        scenario_index=1,
        detail_variant=4,
    ),
    StoryParams(
        luna_name="Nell",
        luna_type="mouse",
        friend_name="Moss",
        friend_type="otter",
        mechanism_name="tower bell mechanism",
        clue_style="a trail of crumbs",
        scenario_index=2,
        detail_variant=7,
    ),
    StoryParams(
        luna_name="Suri",
        luna_type="cat",
        friend_name="Tavi",
        friend_type="squirrel",
        mechanism_name="brass bell mechanism",
        clue_style="a faint scratch",
        scenario_index=3,
        detail_variant=10,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_solved/0. #show friendship_strengthened/0. #show happy_ending/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show mystery_solved/0. "
                "#show friendship_strengthened/0. "
                "#show happy_ending/0."
            )
        )
        print("ASP model:", " ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 30, 30):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            attempt += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No stories could be generated from the requested options.")

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
