#!/usr/bin/env python3
"""
A gentle bedtime storyworld about a nose, sharing, and a quiet warning.

A child discovers that a tiny bedtime problem becomes easier when a comfort
is shared. Earlier details foreshadow the turn, and the ending shows the room
settling into sleep.
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
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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


@dataclass(frozen=True)
class Tale:
    id: str
    foreshadow: str
    trouble: str
    sharing: str
    turn: str
    repair: str
    ending: str
    object_name: str


TALES = [
    Tale(
        id="moon_blanket",
        foreshadow="Before bed, Lina noticed that the moon-shaped patch on her blanket was loose at one corner",
        trouble="when a tickle made her nose wrinkle and she could not settle",
        sharing="Lina shared the blanket with her little brother, Tom, pulling the warm corner over his knees",
        turn="Tom remembered the loose moon patch and found that it had been brushing Lina's nose",
        repair="They folded the blanket back, tucked the patch safely beneath a ribbon, and chose one soft quilt to share",
        ending="Soon Lina's nose grew still, and the two children listened to the moonlight resting on the quilt",
        object_name="moon blanket",
    ),
    Tale(
        id="lavender_pillow",
        foreshadow="At story time, Noor smelled the lavender pillow and saw three little seeds tucked in its seam",
        trouble="after the lights went out, her nose began to twitch whenever she tried to breathe deeply",
        sharing="Noor shared her spare pillow with her sleepy sister, Ada, while Ada offered the smooth cotton pillowcase",
        turn="Together they remembered the seeds and discovered that one had slipped free beside Noor's cheek",
        repair="They placed the seeds in a small jar, shook the pillow gently, and shared the clean pillowcase",
        ending="Noor's nose stopped twitching, and the lavender scent became a quiet path toward sleep",
        object_name="lavender pillow",
    ),
    Tale(
        id="silver_storybook",
        foreshadow="Dad's silver bookmark kept peeking from the bedtime story, even though its sharp corner had been bent flat",
        trouble="when Pip turned onto his side, his nose met a tiny cold edge",
        sharing="Pip shared the storybook with his sister, Rose, and let her hold the pages while he listened",
        turn="Rose remembered the bookmark and found it hiding beneath the pillow",
        repair="They moved the bookmark to the bedside table and shared the last page by the warm lamp",
        ending="Pip's nose rested safely on the pillow, while the silver bookmark waited for tomorrow's story",
        object_name="silver bookmark",
    ),
    Tale(
        id="rainy_scarf",
        foreshadow="A blue scarf hung beside the bed, still carrying one cool drop from the rainy walk home",
        trouble="when Eli pulled it close, the drop tickled his nose and kept sleep away",
        sharing="Eli shared the scarf with his toy bear, wrapping the dry end around its little shoulders",
        turn="The bear's button paw caught the damp thread, showing Eli where the drop had been hiding",
        repair="He hung the scarf by the heater and shared a dry wool wrap with the bear instead",
        ending="Eli's nose felt warm again, and the rain tapped softly while both friends slept",
        object_name="blue scarf",
    ),
    Tale(
        id="carved_music_box",
        foreshadow="The wooden music box had a new splinter near its painted star, so Mira covered it with a cloth",
        trouble="later, a small itch woke her nose whenever the music box hummed",
        sharing="Mira shared the music with her grandmother, who held the cloth while Mira listened",
        turn="The cloth slipped, and together they saw the splinter caught in its loose thread",
        repair="They stopped the music, smoothed the thread away, and shared a quiet humming tune instead",
        ending="Mira's nose was peaceful, and the painted star watched over the room without a sound",
        object_name="music box",
    ),
]

TALE_BY_ID = {t.id: t for t in TALES}

CHILDREN = ["Lina", "Noor", "Pip", "Eli", "Mira", "Sami"]
HELPERS = ["Tom", "Ada", "Rose", "Grandma", "the bear", "Nana"]
MODES = ["quiet", "question", "moonlit", "memory", "whispered"]

OPENINGS = {
    "quiet": "The house had grown quiet, and bedtime wrapped the room in blue shadows.",
    "question": "Have you ever tried to sleep while your nose remembered one tiny tickle?",
    "moonlit": "Moonlight rested on the floor as the little bedroom prepared for sleep.",
    "memory": "Earlier that evening, one small detail had seemed hardly worth noticing.",
    "whispered": "The room was ready for whispers, dreams, and one last good-night hug.",
}


@dataclass
class StoryParams:
    child_name: str
    helper_name: str
    tale_id: Optional[str] = None
    mode: Optional[str] = None
    seed: Optional[int] = None


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xB3D71)
    material = "|".join([params.child_name, params.helper_name, params.tale_id or "", params.mode or ""])
    return random.Random(sum((i + 1) * ord(c) for i, c in enumerate(material)))


def build_world(params: StoryParams) -> World:
    rng = _rng(params)
    tale = TALE_BY_ID.get(params.tale_id or "")
    if tale is None:
        tale = rng.choice(TALES)
    mode = params.mode if params.mode in MODES else rng.choice(MODES)

    if params.child_name == params.helper_name:
        raise StoryError("The child and helper must have different names.")
    if not params.child_name.strip() or not params.helper_name.strip():
        raise StoryError("Child and helper names cannot be empty.")

    world = World()
    child = world.add(Entity("child", "child", params.child_name, meters={"sleepiness": 2.0}, memes={"trust": 1.0}))
    helper = world.add(Entity("helper", "helper", params.helper_name, meters={"sleepiness": 1.0}, memes={"kindness": 1.0}))
    nose = world.add(Entity("nose", "body", "nose", meters={"comfort": 0.0, "tickle": 1.0}, memes={"attention": 1.0}))
    comfort = world.add(Entity("comfort", "object", tale.object_name, meters={"safe": 0.0}, memes={"shared": 0.0}))
    room = world.add(Entity("room", "place", "bedroom", meters={"quiet": 0.0}, memes={"peace": 0.0}))

    world.facts.update(
        child=child,
        helper=helper,
        nose=nose,
        comfort=comfort,
        room=room,
        tale=tale,
        mode=mode,
        foreshadow_seen=False,
        shared=False,
        solved=False,
    )

    world.say(OPENINGS[mode])
    if mode == "question":
        world.say(f"{child.label} had one answer: a nose needs kindness when it starts to complain.")
    elif mode == "memory":
        world.say(f"{child.label} remembered that {tale.foreshadow.lower()}.")
    else:
        world.say(f"{child.label} climbed into bed while {tale.foreshadow.lower()}.")

    world.para()
    world.say(f"{tale.trouble.capitalize()}.")
    nose.meters["tickle"] = 2.0
    child.memes["worry"] = 1.0
    world.say(f"{child.label} rubbed their nose and whispered, “I wish it would stop.”")
    world.say(f"{helper.label} heard the whisper and came close without making the room bright.")

    world.para()
    world.facts["foreshadow_seen"] = True
    world.say(f"{tale.sharing.capitalize()}.")
    comfort.memes["shared"] = 1.0
    child.memes["sharing"] = 1.0
    helper.memes["sharing"] = 1.0
    world.say(f"Then the small warning from earlier became important: {tale.turn}.")
    world.say("They did not scold the room or hurry the night. They simply looked together.")

    world.para()
    world.facts["shared"] = True
    world.facts["solved"] = True
    comfort.meters["safe"] = 1.0
    nose.meters["tickle"] = 0.0
    nose.meters["comfort"] = 2.0
    room.meters["quiet"] = 2.0
    room.memes["peace"] = 2.0
    child.memes["relief"] = 1.0
    helper.memes["relief"] = 1.0
    world.say(f"{tale.repair.capitalize()}.")
    world.say(f"{child.label} thanked {helper.label}. Sharing had made the little trouble feel small enough to solve.")
    world.say(f"{tale.ending.capitalize()}.")

    return world


def generation_prompts(world: World) -> list[str]:
    tale = world.facts["tale"]
    child = world.facts["child"]
    helper = world.facts["helper"]
    return [
        f"Write a gentle bedtime story about {child.label}, whose nose is bothered by a small hidden trouble.",
        f"Foreshadow the turn with this early detail: {tale.foreshadow}. Then show {child.label} and {helper.label} sharing comfort.",
        f"End with a quiet image proving that the nose is comfortable, the cause is repaired, and bedtime feels safe.",
    ]


def make_story_qa(world: World) -> list[QAItem]:
    tale = world.facts["tale"]
    child = world.facts["child"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"Why could {child.label} not settle at bedtime?",
            answer=f"{child.label}'s nose kept reacting to a small problem connected with the {tale.object_name}. The earlier detail about {tale.foreshadow.lower()} gave a clue.",
        ),
        QAItem(
            question=f"How did {child.label} and {helper.label} solve the trouble?",
            answer=f"They looked together, remembered the warning sign, and then {tale.repair.lower()}.",
        ),
        QAItem(
            question="What did sharing change in the story?",
            answer=f"Sharing gave the characters comfort and another pair of careful eyes. It helped them solve the nose's trouble gently instead of facing bedtime worry alone.",
        ),
        QAItem(
            question="What showed that the problem was over?",
            answer=f"{tale.ending.capitalize()}. The peaceful ending showed that the nose was comfortable and the room was ready for sleep.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let someone else use, enjoy, or help with something instead of keeping it only for yourself.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early detail that gives a gentle hint about something important that happens later.",
        ),
        QAItem(
            question="Why can a bedtime story use a quiet ending?",
            answer="A quiet ending can help show that the problem is solved and make the listener feel safe and ready to rest.",
        ),
        QAItem(
            question="What is a nose?",
            answer="A nose is the part of the face used for breathing and smelling.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=make_story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    lines.append(f"  solved={world.facts.get('solved')}; shared={world.facts.get('shared')}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "bedroom"),
            asp.fact("body", "nose"),
            asp.fact("feature", "sharing"),
            asp.fact("feature", "foreshadowing"),
            asp.fact("style", "bedtime_story"),
            asp.fact("action", "notice"),
            asp.fact("action", "share"),
            asp.fact("action", "repair"),
            asp.fact("state", "quiet"),
        ]
    )


ASP_RULES = r"""
bedtime_ready :- setting(bedroom), body(nose), style(bedtime_story).
hinted :- feature(foreshadowing), action(notice).
comfort_shared :- feature(sharing), action(share).
problem_repaired :- action(repair), state(quiet).
valid_story :- bedtime_ready, hinted, comfort_shared, problem_repaired.
#show valid_story/0.
"""


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    valid = any(symbol.name == "valid_story" for symbol in model)
    if not valid:
        print("MISMATCH: ASP twin did not confirm the bedtime storyworld.")
        return 1

    for seed in range(5):
        params = StoryParams("Lina", "Tom", seed=seed)
        sample = generate(params)
        if "nose" not in sample.story.lower() or not sample.world.facts["solved"]:
            print("MISMATCH: generated story failed the world checks.")
            return 1

    print("OK: ASP twin and generated stories agree.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child or rng.choice(CHILDREN)
    helper = args.helper or rng.choice(HELPERS)
    if child == helper:
        helper = "Nana" if child != "Nana" else "Tom"
    return StoryParams(
        child_name=child,
        helper_name=helper,
        tale_id=args.tale or rng.choice(TALES).id,
        mode=args.mode or rng.choice(MODES),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A nose-sharing bedtime storyworld.")
    parser.add_argument("--child")
    parser.add_argument("--helper")
    parser.add_argument("--tale", choices=[t.id for t in TALES])
    parser.add_argument("--mode", choices=MODES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
    StoryParams("Lina", "Tom", "moon_blanket", "moonlit"),
    StoryParams("Noor", "Ada", "lavender_pillow", "quiet"),
    StoryParams("Pip", "Rose", "silver_storybook", "whispered"),
    StoryParams("Eli", "the bear", "rainy_scarf", "memory"),
    StoryParams("Mira", "Grandma", "carved_music_box", "question"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
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
