#!/usr/bin/env python3
"""
A heartwarming dining-room quest about deciding what to do when a darling
keepsake is missing.

The storyworld simulates a child, a darling helper, a small suspenseful search,
and an inner monologue that changes from worry to patient courage.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass
class StoryParams:
    child_name: str
    darling_name: str
    keepsake: str
    quest_id: Optional[str] = None
    telling_mode: Optional[str] = None
    seed: Optional[int] = None


CHILD_NAMES = ["Maya", "Leo", "Nina", "Owen", "Iris", "Eli"]
DARLING_NAMES = ["Darling", "Grandma", "Aunt June", "Milo", "Nora", "Dad"]
KEEPSAKES = [
    "a tiny silver thimble",
    "a blue ribbon charm",
    "a wooden bird",
    "a round kitchen button",
    "a little brass bell",
]

TELLING_MODES = ["quiet_start", "question_start", "suspense_start", "memory_start"]

QUESTS = [
    {
        "id": "napkin_map",
        "opening": "A folded napkin sat beneath the centerpiece like a secret map.",
        "clue": "A corner of blue thread caught on the napkin ring.",
        "false_clue": "They checked the chair cushions first, but found only crumbs and a soft feather.",
        "decisive": "The blue thread matched the ribbon tied around the bread basket.",
        "cause": "Someone had moved the keepsake while clearing the table and tucked it safely beside the clean napkins.",
        "repair": "They returned the keepsake to its small dish and placed a bright label beside the napkin basket.",
        "ending": "When supper began, the keepsake gleamed in its dish, and the folded napkin looked like a friendly map home.",
    },
    {
        "id": "candle_shadow",
        "opening": "A candle made a long, trembling shadow across the dining-room table.",
        "clue": "The shadow ended exactly where the keepsake's dish should have been.",
        "false_clue": "They searched beneath the table, but the darkness held only table legs and a dropped spoon.",
        "decisive": "The candlelight revealed a faint circle on the sideboard beside the family recipe book.",
        "cause": "The keepsake had been moved to the sideboard so the table could be polished, then forgotten there.",
        "repair": "They carried it back carefully and made a marked resting place that would stay clear during polishing.",
        "ending": "The candle shone on the returned keepsake, and its little shadow rested beside the recipe book.",
    },
    {
        "id": "plate_riddle",
        "opening": "Three plates stood in a row, each holding one unusual crumb.",
        "clue": "The crumbs made an arrow that pointed toward the china cabinet.",
        "false_clue": "The cabinet was empty except for clean plates and a tall glass that chimed when the door moved.",
        "decisive": "The third crumb rested beside a note saying, 'Safe for later,' tucked under a folded table runner.",
        "cause": "A careful helper had hidden the keepsake with the special linens so it would not be bumped during lunch.",
        "repair": "They returned the keepsake and added a shallow covered box for treasures that needed to be safe.",
        "ending": "The three plates became a snack, while the keepsake rested in its new box under the table runner.",
    },
    {
        "id": "bell_sound",
        "opening": "A tiny bell rang once from somewhere near the dining-room window.",
        "clue": "The sound came again whenever the curtain lifted.",
        "false_clue": "They blamed the wind, but the window was shut and the curtain tie was still.",
        "decisive": "Behind the curtain, the keepsake had slipped into a basket of clean tablecloths.",
        "cause": "The keepsake had been carried there with a tablecloth when the room was tidied before guests arrived.",
        "repair": "They rescued it from the basket and placed a shallow tray beneath the window for small objects.",
        "ending": "The curtain lifted once more, but the only sound was a happy bell from the new tray.",
    },
]

QUEST_BY_ID = {item["id"]: item for item in QUESTS}


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xDADA1)
    material = "|".join(
        [params.child_name, params.darling_name, params.keepsake, params.quest_id or ""]
    )
    return random.Random(sum((i + 1) * ord(ch) for i, ch in enumerate(material)))


def _opening(mode: str, child: str, darling: str, keepsake: str, opening: str) -> str:
    options = {
        "quiet_start": (
            f"The dining room was warm and quiet until {child} noticed that "
            f"{keepsake} was missing from its little dish. {opening}"
        ),
        "question_start": (
            f'"Where could {keepsake} be?" {child} wondered in the dining room. '
            f"{opening}"
        ),
        "suspense_start": (
            f"Something small was missing from the dining-room table, and the "
            f"silence made the mystery feel bigger. It was {keepsake}. {opening}"
        ),
        "memory_start": (
            f"That morning, {child} had shown {darling} {keepsake} in the dining room. "
            f"Now its dish was empty. {opening}"
        ),
    }
    return options[mode]


def build_world(params: StoryParams) -> World:
    rng = _rng(params)
    quest = QUEST_BY_ID.get(params.quest_id or "")
    if quest is None:
        quest = rng.choice(QUESTS)
    mode = params.telling_mode if params.telling_mode in TELLING_MODES else rng.choice(TELLING_MODES)
    world = World("the dining room")

    child = world.add(Entity(
        id="child",
        kind="character",
        type="child",
        label=params.child_name,
        memes={"worry": 1.0, "curiosity": 1.0, "courage": 0.0},
    ))
    darling = world.add(Entity(
        id="darling",
        kind="character",
        type="helper",
        label=params.darling_name,
        memes={"warmth": 1.0, "patience": 1.0},
    ))
    treasure = world.add(Entity(
        id="keepsake",
        kind="thing",
        type="keepsake",
        label=params.keepsake,
        meters={"safety": 0.0, "distance_from_dish": 1.0},
        memes={"belonging": 1.0},
    ))
    table = world.add(Entity(
        id="table",
        kind="thing",
        type="table",
        label="the dining table",
        meters={"order": 1.0},
    ))

    world.facts.update(
        child=child,
        darling=darling,
        keepsake=treasure,
        table=table,
        quest=quest,
        mode=mode,
        decided=False,
        found=False,
        repaired=False,
    )

    world.say(_opening(mode, child.label, darling.label, treasure.label, quest["opening"]))
    world.say(
        f"{child.label}'s first inner monologue was a worried whisper: "
        f'"I should decide what to do, darling, but I do not want to make the mystery worse."'
    )
    child.memes["worry"] = 2.0

    world.para()
    world.say(
        f"{darling.label} knelt beside {child.label}. "
        f'"A good quest begins with a calm choice," {darling.label} said. '
        f'"We can look carefully and leave every place as safe as we found it."'
    )
    world.say(
        f"{child.label} decided to search with {darling.label}, not to accuse anyone "
        f"and not to snatch through the room."
    )
    child.memes["courage"] = 1.0
    child.memes["worry"] = 1.0
    world.facts["decided"] = True

    world.say(quest["clue"])
    world.say(
        f"In a second inner monologue, {child.label} thought, "
        f'"Suspense feels prickly, but a clue is better than a guess."'
    )
    world.say(quest["false_clue"])

    world.para()
    world.say(
        f"{child.label} almost hurried away, but {darling.label} gently pointed to "
        f"the things that had changed. Together they followed the quiet evidence."
    )
    world.say(quest["decisive"])
    world.say(
        f"Then the answer became clear: {quest['cause']}."
    )
    child.memes["curiosity"] = 2.0
    child.memes["worry"] = 0.0
    child.memes["courage"] = 2.0
    treasure.meters["distance_from_dish"] = 0.0
    treasure.meters["safety"] = 1.0
    world.facts["found"] = True

    world.para()
    world.say(
        f"{child.label}'s final inner monologue sounded different: "
        f'"I could not control the surprise, but I could decide to care for what I found."'
    )
    world.say(quest["repair"])
    world.say(
        f"{child.label} thanked {darling.label}, and {darling.label} smiled as if the "
        f"small quest had made the whole room kinder."
    )
    table.meters["order"] = 2.0
    treasure.meters["safety"] = 2.0
    child.memes["relief"] = 1.0
    world.facts["repaired"] = True
    world.say(quest["ending"])

    return world


def reasonableness(world: World) -> None:
    facts = world.facts
    if not facts.get("decided"):
        raise StoryError("The child must decide on a safe search before following clues.")
    if not facts.get("found"):
        raise StoryError("The quest must locate the missing keepsake.")
    if not facts.get("repaired"):
        raise StoryError("The ending must restore the keepsake and the dining room.")
    if facts["child"].memes.get("worry", 0.0) > 0.0:
        raise StoryError("The child's worry should ease after the cause is understood.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming Quest in a dining room where {f['keepsake'].label} goes missing.",
        f"Include an Inner Monologue showing how {f['child'].label} decides to search with {f['darling'].label} instead of blaming anyone.",
        f"Use gentle Suspense and end with this concrete image: {f['quest']['ending']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"].label
    darling = f["darling"].label
    keepsake = f["keepsake"].label
    quest = f["quest"]
    return [
        QAItem(
            question=f"What was missing from the dining room?",
            answer=f"{keepsake} was missing from its little dish on the dining-room table.",
        ),
        QAItem(
            question=f"What did {child} decide to do?",
            answer=f"{child} decided to search carefully with {darling}, without accusing anyone or making the room less safe.",
        ),
        QAItem(
            question=f"What clue helped {child} and {darling} solve the quest?",
            answer=f"The decisive clue was this: {quest['decisive']}",
        ),
        QAItem(
            question=f"Why had {keepsake} disappeared?",
            answer=f"{quest['cause']}",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{quest['repair']}. {quest['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to decide?",
            answer="To decide means to choose what you will do after thinking about the choices.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful journey or search to reach an important goal.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private stream of thoughts a person has inside their mind.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next while a problem is still unsolved.",
        ),
        QAItem(
            question="What does darling mean?",
            answer="Darling is a warm word for someone or something dearly loved.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.type}; meters={entity.meters}; memes={entity.memes}"
        )
    lines.append(f"  place: {world.place}")
    lines.append(f"  decided: {world.facts.get('decided')}")
    lines.append(f"  found: {world.facts.get('found')}")
    lines.append(f"  repaired: {world.facts.get('repaired')}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "dining_room"),
            asp.fact("feature", "quest"),
            asp.fact("feature", "inner_monologue"),
            asp.fact("feature", "suspense"),
            asp.fact("action", "decide"),
            asp.fact("action", "search"),
            asp.fact("action", "repair"),
            asp.fact("value", "care"),
        ]
    )


ASP_RULES = r"""
has_setting :- setting(dining_room).
has_features :- feature(quest), feature(inner_monologue), feature(suspense).
has_decision :- action(decide), value(care).
quest_resolved :- action(search), action(repair).
valid_story :- has_setting, has_features, has_decision, quest_resolved.
#show valid_story/0.
"""


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    valid = any(symbol.name == "valid_story" for symbol in model)
    if not valid:
        print("MISMATCH: ASP twin did not confirm the storyworld.")
        return 1

    for params in CURATED:
        sample = generate(params)
        try:
            reasonableness(sample.world)
        except StoryError as exc:
            print(f"MISMATCH: generated story failed: {exc}")
            return 1

    print("OK: ASP twin and generated stories agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming dining-room quest about deciding with care."
    )
    parser.add_argument("--name")
    parser.add_argument("--darling")
    parser.add_argument("--keepsake")
    parser.add_argument("--quest")
    parser.add_argument("--mode")
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
    quest_id = args.quest if args.quest in QUEST_BY_ID else rng.choice(QUESTS)["id"]
    mode = args.mode if args.mode in TELLING_MODES else rng.choice(TELLING_MODES)
    return StoryParams(
        child_name=args.name or rng.choice(CHILD_NAMES),
        darling_name=args.darling or rng.choice(DARLING_NAMES),
        keepsake=args.keepsake or rng.choice(KEEPSAKES),
        quest_id=quest_id,
        telling_mode=mode,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    reasonableness(world)
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


CURATED = [
    StoryParams(
        child_name="Maya",
        darling_name="Grandma",
        keepsake="a tiny silver thimble",
        quest_id="napkin_map",
        telling_mode="quiet_start",
    ),
    StoryParams(
        child_name="Leo",
        darling_name="Darling",
        keepsake="a blue ribbon charm",
        quest_id="candle_shadow",
        telling_mode="suspense_start",
    ),
    StoryParams(
        child_name="Iris",
        darling_name="Aunt June",
        keepsake="a wooden bird",
        quest_id="bell_sound",
        telling_mode="memory_start",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
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
