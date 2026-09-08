#!/usr/bin/env python3
"""
A small fable storyworld about anatomy, a kind lady, and pork.

Lady Elin learns that a kitchen lesson is not only about cooking. By listening
to the village healer, she discovers how the body's anatomy needs care, changes
a hasty choice, and turns a worried supper into a happy ending.
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
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class StoryParams:
    lady_name: str
    helper_name: str
    animal_name: str
    seed: Optional[int] = None
    lesson_id: Optional[str] = None


LADY_NAMES = ["Mara", "Elin", "Rosa", "Nell", "Ada", "Lina"]
HELPER_NAMES = ["the village healer", "Grandmother Bea", "Old Tomas", "Aunt Sella"]
ANIMAL_NAMES = ["Pip", "Bramble", "Clover", "Moss"]


@dataclass(frozen=True)
class Lesson:
    id: str
    body_clue: str
    mistake: str
    discovery: str
    repair: str
    moral: str
    ending: str


LESSONS = [
    Lesson(
        "slow_cooking",
        "the healer explained that muscles, bones, and the stomach all need gentle care",
        "she planned to serve a thick piece of pork before it had cooked through",
        "the center of the pork was still pink and cool, while the outside was already brown",
        "she returned the meat to the covered pot and waited until it was fully cooked",
        "A wise cook does not hurry what the body must safely receive",
        "The supper table shone with warm bowls, and every guest ate gladly",
    ),
    Lesson(
        "clean_hands",
        "the lady's hands carry many tiny helpers and germs that eyes cannot see",
        "she reached for the pork after touching the muddy garden gate",
        "the healer pointed to the mud beneath her nails and asked her to wash before cooking",
        "she scrubbed her hands, cleaned the board, and prepared the pork safely",
        "Small clean habits protect the whole body",
        "After supper, the children copied her careful hand-washing song",
    ),
    Lesson(
        "balanced_plate",
        "the body uses bones, muscles, and blood together, so it needs more than one kind of food",
        "she filled every plate with pork and forgot the beans, apples, and greens",
        "the healer showed her that a colorful plate gave the body a better team of foods",
        "she added beans, greens, apples, and a little pork to each plate",
        "A strong body welcomes balance rather than excess",
        "The village children made a rainbow around their plates and laughed through dessert",
    ),
    Lesson(
        "safe_tools",
        "fingers, skin, and eyes are precious parts of anatomy that sharp tools can harm",
        "she waved a carving knife while calling everyone to the table",
        "the healer gently lowered her hand and showed her the safe way to place the knife",
        "she set the knife on its board and asked an adult to carve the pork",
        "Careful hands make a feast happier than hurried hands",
        "The carving was done safely, and the knife rested quietly while the village sang",
    ),
    Lesson(
        "rest_and_food",
        "the heart, lungs, and muscles work hard and need both nourishing food and rest",
        "she tried to carry a heavy pork basket alone after a long day",
        "her quick breath and tired arms told her body to pause",
        "she rested, called for help, and carried the basket with two friends",
        "Listening to the body is a kind of courage",
        "The basket reached the kitchen, and the tired helpers rested together after the feast",
    ),
    Lesson(
        "kind_animal_care",
        "a living body has bones, skin, breath, and feelings that deserve gentle care",
        "she forgot to leave fresh water for the pig who had helped the village",
        "the animal's dry bowl and quiet nudge reminded her that gratitude needs action",
        "she filled the bowl, gave the pig shade, and thanked it before preparing the meal",
        "Kindness should reach every living body",
        "The pig rested happily in the shade while the village shared a grateful supper",
    ),
]


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xBEEF088)
    text = "|".join([params.lady_name, params.helper_name, params.animal_name, params.lesson_id or ""])
    return random.Random(sum((i + 1) * ord(c) for i, c in enumerate(text)))


def _validate(params: StoryParams) -> None:
    if not params.lady_name.strip():
        raise StoryError("lady_name must not be empty")
    if not params.helper_name.strip():
        raise StoryError("helper_name must not be empty")
    if params.lesson_id is not None and params.lesson_id not in {x.id for x in LESSONS}:
        raise StoryError(f"unknown lesson_id: {params.lesson_id}")


def build_world(params: StoryParams) -> World:
    _validate(params)
    rng = _rng(params)
    lesson = next((x for x in LESSONS if x.id == params.lesson_id), None) or rng.choice(LESSONS)
    world = World()

    lady = world.add(Entity(params.lady_name, "character", "lady", params.lady_name))
    helper = world.add(Entity("helper", "character", "helper", params.helper_name))
    pork = world.add(Entity("pork", "thing", "food", "pork"))
    body = world.add(Entity("body", "thing", "anatomy", "the human body"))
    animal = world.add(Entity("animal", "animal", "pig", params.animal_name))

    lady.memes.update(worry=1.0, haste=1.0)
    helper.memes.update(wisdom=1.0)
    body.meters.update(safety=0.0, care=0.0)
    pork.meters.update(prepared=0.0)
    animal.meters.update(thirst=0.0)

    openings = [
        f"Lady {lady.label} lived beside a bright kitchen where the smell of pork drifted over the village.",
        f"One morning, Lady {lady.label} carried a basket of pork toward the village kitchen.",
        f"Lady {lady.label} was proud of her cooking, but that day the pork brought her a lesson she did not expect.",
    ]
    world.say(rng.choice(openings))
    world.say(f"She wanted a grand meal, yet she had forgotten that {lesson.body_clue}.")
    world.para()

    world.say(f'"The feast must be ready at once," said Lady {lady.label}.')
    world.say(f'"A happy feast begins with a safe body and a careful choice," replied {helper.label}.')
    world.say(f"Lady {lady.label} made a hurried choice: {lesson.mistake}.")
    lady.memes["haste"] = 2.0

    world.para()
    world.say(f"{helper.label.capitalize()} did not scold her. Instead, the helper said, \"Let us look closely and learn.\"")
    world.say(f"Together they discovered that {lesson.discovery}.")
    world.say(f"Lady {lady.label} listened, and her worry changed into understanding.")
    lady.memes["haste"] = 0.0
    lady.memes["learning"] = 1.0
    body.meters["care"] = 1.0

    world.para()
    world.say(f"Then Lady {lady.label} acted wisely: {lesson.repair}.")
    lady.memes["kindness"] = 1.0
    body.meters["safety"] = 1.0
    pork.meters["prepared"] = 1.0
    world.say(f'"I have learned the lesson," said Lady {lady.label}. "{lesson.moral}."')
    world.say(f"{lesson.ending}.")
    world.say("And so the village remembered that knowledge becomes kindness when it guides what our hands do.")

    world.facts.update(
        lady=lady,
        helper=helper,
        pork=pork,
        body=body,
        animal=animal,
        lesson=lesson,
        place="the village kitchen",
        lesson_learned=True,
        happy_ending=True,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lesson = f["lesson"]
    return [
        f"Write a child-friendly fable about Lady {f['lady'].label}, anatomy, and pork in a village kitchen.",
        f"Show how {f['lady'].label} makes this mistake: {lesson.mistake}, then learns from {f['helper'].label}.",
        f"End with a lesson learned, a concrete safe repair, and a happy ending: {lesson.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    lesson = f["lesson"]
    lady = f["lady"].label
    return [
        QAItem(
            f"What was Lady {lady} preparing?",
            f"Lady {lady} was preparing pork for a village meal in the kitchen.",
        ),
        QAItem(
            f"What did Lady {lady} learn about anatomy?",
            f"She learned that {lesson.body_clue}, so a cook must make choices that care for the body.",
        ),
        QAItem(
            f"What mistake did Lady {lady} make?",
            f"She made a hurried choice: {lesson.mistake}.",
        ),
        QAItem(
            "How did the lesson change what she did?",
            f"After seeing that {lesson.discovery}, she followed the repair: {lesson.repair}.",
        ),
        QAItem(
            "How did the story end?",
            f"It ended happily: {lesson.ending}. The village also remembered that knowledge should guide kind and safe actions.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is anatomy?",
            "Anatomy is the study of the parts of a living body, such as bones, muscles, skin, and organs.",
        ),
        QAItem(
            "Why should pork be prepared carefully?",
            "Pork should be prepared carefully so it is safe to eat and kind to the people who share it.",
        ),
        QAItem(
            "What is a lesson learned?",
            "A lesson learned is useful understanding gained from noticing a mistake and choosing a better action.",
        ),
        QAItem(
            "What makes a happy ending?",
            "A happy ending shows that a problem has been repaired and that people or animals are safer, wiser, or kinder.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    lines = ["--- world model ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  lesson_learned={world.facts.get('lesson_learned')}")
    lines.append(f"  happy_ending={world.facts.get('happy_ending')}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("domain", "fable"),
            asp.fact("subject", "anatomy"),
            asp.fact("food", "pork"),
            asp.fact("character_role", "lady"),
            asp.fact("feature", "lesson_learned"),
            asp.fact("feature", "happy_ending"),
            asp.fact("action", "listen"),
            asp.fact("action", "repair"),
        ]
    )


ASP_RULES = r"""
has_subject :- domain(fable), subject(anatomy), food(pork), character_role(lady).
has_turn :- action(listen), action(repair).
valid_story :- has_subject, has_turn, feature(lesson_learned), feature(happy_ending).
#show valid_story/0.
"""


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    valid = any(symbol.name == "valid_story" for symbol in model)
    if not valid:
        print("MISMATCH: ASP twin rejected the fable domain.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("lesson_learned"):
            print("MISMATCH: generated story lacks its lesson learned.")
            return 1
        if not sample.world.facts.get("happy_ending"):
            print("MISMATCH: generated story lacks its happy ending.")
            return 1
    print("OK: ASP twin confirms the fable world and generated stories.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fable storyworld about anatomy, a lady, and pork.")
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--animal")
    parser.add_argument("--lesson")
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
    if args.lesson and args.lesson not in {x.id for x in LESSONS}:
        raise StoryError(f"unknown lesson: {args.lesson}")
    return StoryParams(
        lady_name=args.name or rng.choice(LADY_NAMES),
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        animal_name=args.animal or rng.choice(ANIMAL_NAMES),
        lesson_id=args.lesson or rng.choice(LESSONS).id,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Mara", "the village healer", "Pip", "clean_hands"),
    StoryParams("Elin", "Grandmother Bea", "Bramble", "balanced_plate"),
    StoryParams("Rosa", "Old Tomas", "Clover", "slow_cooking"),
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
        if args.n < 1:
            raise StoryError("-n must be at least 1")
        for index in range(args.n):
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
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
