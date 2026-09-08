#!/usr/bin/env python3
"""
A small Superhero Story world about Luna's quest to terminate a dangerous
problem, scour a grizzly's cave, and discover that careful listening can save
the day.
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
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(
        default_factory=lambda: {
            "distance": 0.0,
            "danger": 0.0,
            "cleanliness": 0.0,
            "energy": 0.0,
        }
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "worry": 0.0,
            "courage": 0.0,
            "trust": 0.0,
            "joy": 0.0,
            "relief": 0.0,
        }
    )


@dataclass
class Setting:
    place: str = "Moonrise Mountain"
    landmark: str = "the silver signal tower"


@dataclass
class StoryParams:
    hero_name: str
    hero_power: str
    grizzly_name: str
    helper_name: str
    helper_type: str
    quest_index: int = 0
    voice_index: int = 0
    detail_variant: int = 0
    seed: Optional[int] = None


QUESTS = [
    {
        "goal": "terminate the runaway shadow signal before it reached the town",
        "danger": "The signal made every friendly light look like a monster's eye.",
        "clue": "The grizzly heard the signal pause whenever a bell on the old trail rang.",
        "first_try": "Luna blasted the brightest shadow, but it split into three smaller shadows.",
        "method": "Luna placed small mirrors around the tower while the grizzly rang the trail bell in a steady rhythm.",
        "result": "The false signal folded into one harmless spark and went out.",
        "lesson": "a hero should learn what a danger is doing before trying to defeat it",
        "image": "the town lights shone gently below the quiet moon",
        "question": "What helped Luna understand the runaway signal?",
    },
    {
        "goal": "scour the grizzly's cave before the mountain spring overflowed",
        "danger": "Pebbles and old vines blocked the spring, and water was rising around the grizzly's bed.",
        "clue": "The helper noticed that the water moved fastest beneath a flat blue stone.",
        "first_try": "Luna pulled at a thick vine, but the vine tightened around the stone.",
        "method": "Luna lifted the stone with her star-rope while the grizzly gathered the loose vines into a safe pile.",
        "result": "The spring ran clear, and the cave floor dried before the water reached the doorway.",
        "lesson": "strength works best when it is guided by a careful clue",
        "image": "a bright stream curled past the cave while the grizzly slept safely",
        "question": "Why did the first attempt fail?",
    },
    {
        "goal": "terminate the alarm that had trapped the village's flying buses in the clouds",
        "danger": "The alarm shrieked whenever a bus tried to land, so passengers were circling above the rooftops.",
        "clue": "The helper saw a loose red ribbon brushing the alarm's listening horn.",
        "first_try": "Luna shouted toward the horn, but her voice made the alarm shriek louder.",
        "method": "Luna flew beneath the horn while the grizzly held a blanket over the ribbon and the helper tied it down.",
        "result": "The alarm became quiet, and every bus landed beside the cheering passengers.",
        "lesson": "a quiet answer can be stronger than a loud command",
        "image": "the last flying bus touched down under a sky full of waving scarves",
        "question": "How did the heroes stop the alarm?",
    },
    {
        "goal": "scour the old hero tunnel and recover its missing rescue map",
        "danger": "Dust hid the floor, and a wrong turn could send rescuers toward a cliff.",
        "clue": "The grizzly found fresh chalk marks near a narrow wall.",
        "first_try": "Luna rushed into the widest passage, but it ended at a locked iron gate.",
        "method": "The grizzly brushed the dust aside while Luna followed the chalk marks and the helper held up a glowing leaf-lamp.",
        "result": "They found the rescue map tucked behind the narrow wall and returned it to the hero station.",
        "lesson": "the smallest path can lead to the most important answer",
        "image": "the restored map glowed above the hero station's bright red door",
        "question": "Where was the rescue map found?",
    },
    {
        "goal": "terminate the frost spell covering the playground before morning",
        "danger": "The slide, swings, and climbing bars had become too slippery for children to use.",
        "clue": "The grizzly discovered that the frost vanished wherever someone sang the playground welcome song.",
        "first_try": "Luna warmed the gate with her gloves, but the ice quickly spread back.",
        "method": "Luna led the song while the grizzly and the helper sang at the three corners of the playground.",
        "result": "The frost melted into glittering drops, leaving the playground safe and bright.",
        "lesson": "shared hope can reach places that force cannot",
        "image": "morning sun sparkled on the safe swings as children laughed",
        "question": "What melted the frost spell?",
    },
]

OPENINGS = [
    "Under a round silver moon",
    "Just as the first stars appeared",
    "When the city clock struck nine",
    "At the edge of a windy evening",
    "While the mountain clouds glowed pink",
]

INNER_THOUGHTS = [
    "Luna thought, I can be brave without being reckless.",
    "Inside, Luna wondered, What is the danger trying to tell us?",
    "Luna told herself, A true hero protects people and listens carefully.",
    "Her heart beat quickly, but Luna thought, I can pause, notice, and choose.",
]


class World:
    def __init__(self) -> None:
        self.setting = Setting()
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace_log: list[str] = []

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

    def log(self, text: str) -> None:
        self.trace_log.append(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero Story: Luna's quest with a grizzly."
    )
    parser.add_argument("--name")
    parser.add_argument("--power")
    parser.add_argument("--grizzly")
    parser.add_argument("--helper")
    parser.add_argument("--helper-type")
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
        hero_name=args.name or rng.choice(["Luna", "Nova", "Mira", "Skye", "Sol"]),
        hero_power=args.power
        or rng.choice(
            [
                "star-rope",
                "moonlight gloves",
                "a silver shield",
                "wind boots",
                "a glowing compass",
            ]
        ),
        grizzly_name=args.grizzly
        or rng.choice(["Bruno", "Moss", "Grumble", "Boulder", "Honey"]),
        helper_name=args.helper
        or rng.choice(["Pip", "Tavi", "Nell", "Juno", "Clover"]),
        helper_type=args.helper_type
        or rng.choice(["fox", "raccoon", "owl", "rabbit", "squirrel"]),
        quest_index=rng.randrange(len(QUESTS)),
        voice_index=rng.randrange(len(INNER_THOUGHTS)),
        detail_variant=rng.randrange(10000),
    )


def tell(params: StoryParams) -> World:
    if params.hero_name.strip().lower() == params.grizzly_name.strip().lower():
        raise StoryError("The hero and grizzly need different names.")
    if not params.hero_name.strip() or not params.grizzly_name.strip():
        raise StoryError("Hero and grizzly names cannot be empty.")

    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="person",
            type="hero",
            label=params.hero_name,
            meters={"distance": 0.0, "danger": 0.0, "cleanliness": 0.0, "energy": 1.0},
            memes={"worry": 0.0, "courage": 1.0, "trust": 0.0, "joy": 0.0, "relief": 0.0},
        )
    )
    grizzly = world.add(
        Entity(
            id="grizzly",
            kind="animal",
            type="grizzly",
            label=params.grizzly_name,
            memes={"worry": 1.0, "courage": 0.0, "trust": 0.0, "joy": 0.0, "relief": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="animal",
            type=params.helper_type,
            label=params.helper_name,
            memes={"worry": 0.0, "courage": 0.5, "trust": 1.0, "joy": 0.0, "relief": 0.0},
        )
    )
    quest = QUESTS[params.quest_index % len(QUESTS)]
    world.facts.update(hero=hero, grizzly=grizzly, helper=helper, quest=quest)

    opening = OPENINGS[params.detail_variant % len(OPENINGS)]
    world.say(
        f"{opening}, {hero.label} arrived at {world.setting.place} wearing her "
        f"{params.hero_power}."
    )
    world.say(
        f"The mountain beacon flashed three times. {grizzly.label} the grizzly "
        f"hurried from {world.setting.landmark} and called, "
        f'"Please help us to {quest["goal"]}!"'
    )
    world.say(f'{hero.label} answered, "I will help, but we must understand the trouble first."')
    world.para()

    hero.meters["distance"] = 1.0
    hero.meters["danger"] = 1.0
    grizzly.meters["danger"] = 1.0
    world.say(quest["danger"])
    world.say(
        f"{params.helper_name} the {params.helper_type} joined them and pointed toward "
        f"the problem. {INNER_THOUGHTS[params.voice_index % len(INNER_THOUGHTS)]}"
    )
    world.say(
        f'"I have a quick idea," said {params.helper_name}. "{quest["first_try"]}"'
    )
    world.say(
        f'{hero.label} shook her head. "{quest["first_try"].split(",")[0]} '
        f'was not enough. Let us look for a clue."'
    )
    world.para()

    grizzly.memes["trust"] += 1.0
    hero.memes["trust"] += 1.0
    world.say(f"{quest['clue']}")
    world.say(
        f'"I heard it too," {grizzly.label} said. "The clue tells us where to begin."'
    )
    world.say(
        f'"Then we work together," {hero.label} replied. '
        f'"{params.helper_name}, watch the safe path. {grizzly.label}, help me with the heavy part."'
    )
    world.say(quest["method"])
    world.para()

    hero.meters["danger"] = 0.0
    grizzly.meters["danger"] = 0.0
    grizzly.meters["cleanliness"] = 1.0
    hero.memes["courage"] += 1.0
    grizzly.memes["relief"] += 1.0
    grizzly.memes["joy"] += 1.0
    helper.memes["joy"] += 1.0
    world.say(quest["result"])
    world.say(
        f'{params.helper_name} clapped. "{quest["question"].replace("?", "")}?" '
        f'the helper asked.'
    )
    world.say(
        f'{hero.label} smiled. "We listened to the clue, changed our plan, and '
        f'used each person\'s strength."'
    )
    world.para()

    world.say(
        f"The quest was complete, and the danger was gone. {grizzly.label} gave "
        f"{hero.label} a grateful hug."
    )
    world.say(
        f'"You did not just rush in like a superhero," {grizzly.label} said. '
        f'"You made everyone safer."'
    )
    world.say(
        f"{hero.label} looked at the calm mountain and thought, "
        f"I want every rescue to end with people feeling safe."
    )
    world.say(f"At last, {quest['image']}.")
    world.log(f"quest_index={params.quest_index % len(QUESTS)}")
    world.log("danger=resolved")
    world.log("ending=happy")
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    grizzly: Entity = world.facts["grizzly"]  # type: ignore[assignment]
    quest: dict[str, str] = world.facts["quest"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly Superhero Story about {hero.label} on a quest to {quest['goal']}.",
        f"Tell a story where {hero.label} uses an inner monologue, listens to {grizzly.label}, and reaches a happy ending.",
        f'Include the words "terminate", "grizzly", and "scour" naturally in a story about {hero.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    grizzly: Entity = world.facts["grizzly"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    quest: dict[str, str] = world.facts["quest"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What quest did {hero.label} accept?",
            answer=f"{hero.label} accepted the quest to {quest['goal']}.",
        ),
        QAItem(
            question=f"What danger did {grizzly.label} face?",
            answer=f"{grizzly.label} faced this danger: {quest['danger']}",
        ),
        QAItem(
            question=f"What clue changed the heroes' plan?",
            answer=f"The clue was that {quest['clue'].replace('The ', 'the ')} "
            f"It showed them how to act more safely.",
        ),
        QAItem(
            question=f"How did {hero.label}, {grizzly.label}, and {helper.label} solve the problem?",
            answer=f"They worked together: {quest['method']} This teamwork resolved the danger.",
        ),
        QAItem(
            question="Why was the ending happy?",
            answer=f"The ending was happy because {quest['result']} Everyone became safer and the quest was complete.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is an important journey or task that someone undertakes to find, fix, or protect something.",
        ),
        QAItem(
            question="What does terminate mean?",
            answer="Terminate means to bring something to an end or stop it.",
        ),
        QAItem(
            question="What does scour mean?",
            answer="Scour means to search a place carefully, or to clean it by rubbing and washing.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private stream of thoughts, showing what the character is thinking inside.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending resolves the main danger and shows that the characters are safe, helped, or hopeful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


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
    lines.extend(world.trace_log)
    return "\n".join(lines)


ASP_RULES = r"""
entity(hero).
entity(grizzly).
entity(helper).

heard_clue(grizzly).
worked_together(hero, grizzly, helper).
danger_resolved.
quest_complete :- heard_clue(grizzly), worked_together(hero, grizzly, helper), danger_resolved.
happy_ending :- quest_complete.
#show quest_complete/0.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("heard_clue", "grizzly"),
            asp.fact("worked_together", "hero", "grizzly", "helper"),
            asp.fact("danger_resolved"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program("#show quest_complete/0. #show happy_ending/0.")
    )
    atoms = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {"quest_complete/0", "happy_ending/0"}
    if atoms != expected:
        print(f"MISMATCH: {sorted(atoms)} != {sorted(expected)}")
        return 1

    params = StoryParams(
        hero_name="Luna",
        hero_power="star-rope",
        grizzly_name="Bruno",
        helper_name="Pip",
        helper_type="fox",
        quest_index=0,
        voice_index=0,
        detail_variant=0,
    )
    sample = generate(params)
    required = ["terminate", "grizzly", "scour"]
    if any(word not in sample.story.lower() for word in required):
        print("MISMATCH: generated story omitted a required seed word")
        return 1
    if "happy" not in sample.story.lower() and "safe" not in sample.story.lower():
        print("MISMATCH: generated story did not resolve safely")
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
        hero_name="Luna",
        hero_power="star-rope",
        grizzly_name="Bruno",
        helper_name="Pip",
        helper_type="fox",
        quest_index=0,
        voice_index=0,
        detail_variant=3,
    ),
    StoryParams(
        hero_name="Nova",
        hero_power="moonlight gloves",
        grizzly_name="Moss",
        helper_name="Tavi",
        helper_type="owl",
        quest_index=1,
        voice_index=1,
        detail_variant=8,
    ),
    StoryParams(
        hero_name="Mira",
        hero_power="a silver shield",
        grizzly_name="Boulder",
        helper_name="Nell",
        helper_type="rabbit",
        quest_index=4,
        voice_index=2,
        detail_variant=14,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_complete/0. #show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(
            asp_program("#show quest_complete/0. #show happy_ending/0.")
        )
        print("ASP model:", " ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(args.n * 20, 20):
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = (
            f"### variant {index + 1}"
            if len(samples) > 1 and not args.all
            else ""
        )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
