#!/usr/bin/env python3
"""A child-friendly whodunit about an ear, brave questions, and loyal friends."""

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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    setting: str = "the little listening room"
    hero: str = "Luna"
    friend: str = "Pip"
    object_name: str = "the silver bell"
    seed: Optional[int] = None


SETTINGS = {
    "listening_room": "the little listening room",
    "school_hall": "the sunny school hall",
    "garden": "the whispering garden",
}
HERO_NAMES = ["Luna", "Mara", "Nia", "Tess", "Ravi"]
FRIEND_NAMES = ["Pip", "Ollie", "Bea", "Kito", "Mina"]
OBJECTS = ["the silver bell", "the blue music box", "the tiny drum", "the brass whistle"]


@dataclass(frozen=True)
class CASE:
    title: str
    missing: str
    clue: str
    suspect: str
    suspect_role: str
    question: str
    reveal: str
    lesson: str
    ending: str


CASES = [
    CASE(
        "The Silent Bell",
        "the silver bell had vanished from the reading table",
        "a faint ringing trail led toward a basket of folded scarves",
        "Mr. Finch",
        "the quiet caretaker",
        "who had moved the bell, and why?",
        "Mr. Finch had placed it in the scarf basket so its loose clapper would not wake the resting baby birds outside",
        "brave questions are kinder and wiser than quick blame",
        "the bell chimed softly beside the window while every friend listened together",
    ),
    CASE(
        "The Whispering Box",
        "the blue music box was missing its little paper tune",
        "Luna heard a soft scratch near the puppet shelf with one careful ear",
        "Bea",
        "the puppet maker",
        "who had taken the tune, and what was it doing there?",
        "Bea had borrowed it to copy the notes for a puppet show about helping neighbors",
        "friendship grows when people explain before they accuse",
        "the copied tune played while paper puppets bowed to their smiling audience",
    ),
    CASE(
        "The Drumbeat Trail",
        "the tiny drum had rolled away before the welcome song",
        "round dust marks curved from the stage to a basket of wool",
        "Ollie",
        "the eager stage helper",
        "who had moved the drum from its stand?",
        "Ollie had rolled it aside after hearing a crack in the stand and wanted to keep anyone safe",
        "a careful listener can find the truth hidden inside a puzzling sound",
        "the mended drum gave one proud beat as the friends began their song",
    ),
    CASE(
        "The Missing Whistle",
        "the brass whistle was gone from the garden gate",
        "a bird answered whenever Luna cupped one hand behind her ear",
        "Kito",
        "the young garden keeper",
        "who had carried the whistle away?",
        "Kito had hidden it under a fern because its sharp call startled a nest of finches",
        "bravery means speaking up gently when something may hurt another",
        "the finches fluttered safely above the gate as the whistle stayed quiet",
    ),
]


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A whodunit about listening, friendship, and bravery.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--friend", choices=FRIEND_NAMES)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
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
    hero = args.hero or rng.choice(HERO_NAMES)
    friend_choices = [name for name in FRIEND_NAMES if name != hero]
    friend = args.friend or rng.choice(friend_choices)
    if friend == hero:
        raise StoryError("The hero and friend must have different names.")
    setting_key = args.setting or rng.choice(list(SETTINGS))
    object_name = args.object_name or rng.choice(OBJECTS)
    return StoryParams(
        setting=SETTINGS[setting_key],
        hero=hero,
        friend=friend,
        object_name=object_name,
    )


def _case_for(params: StoryParams) -> CASE:
    seed = params.seed if params.seed is not None else 0
    return CASES[seed % len(CASES)]


def tell(params: StoryParams) -> World:
    case = _case_for(params)
    world = World(params)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        label=params.hero,
        role="detective",
        meters={"attention": 1.0, "bravery": 1.0},
        memes={"friendship": 1.0, "curiosity": 1.0},
        traits=["careful listener"],
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        label=params.friend,
        role="helper",
        meters={"attention": 1.0, "bravery": 1.0},
        memes={"friendship": 1.0, "patience": 1.0},
        traits=["loyal friend"],
    ))
    ear = world.add(Entity(
        id="ear",
        kind="body_part",
        label="Luna's ear",
        role="listening tool",
        meters={"hearing": 1.0},
        memes={"wisdom": 0.0},
        traits=["patient"],
    ))

    world.say(f"On a bright morning in {params.setting}, {hero.label} and {friend.label} were preparing a listening game.")
    world.say(f"Then {case.missing}. The empty place looked like a question with no answer.")
    world.say(f"“Someone must have taken it,” whispered {friend.label}. “Should we guess who?”")
    world.say(f"“No,” said {hero.label}. “Let us listen first. My ear may catch a clue, and our friendship can keep us fair.”")

    world.para()
    world.say(f"{hero.label} closed one eye and held still. With the careful help of {ear.label}, {hero.label} noticed that {case.clue}.")
    hero.meters["attention"] += 1
    ear.memes["wisdom"] += 1
    world.say(f"{friend.label} pointed toward {case.suspect_role}. “That makes {case.suspect} look suspicious,” said {friend.label}.")
    world.say(f"“Suspicious is not the same as guilty,” replied {hero.label}. “We should ask {case.suspect} what happened.”")
    world.say(f"They walked together to {case.suspect}. {hero.label} took a brave breath and asked, “{case.question.capitalize()}”")
    world.say(f"{case.suspect} answered, “{case.reveal.capitalize()}”")

    world.para()
    world.say(f"The friends checked the place, followed the clue, and found that the answer matched every sound and mark.")
    friend.meters["bravery"] += 1
    hero.meters["bravery"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(f"{friend.label} smiled. “I nearly blamed someone before I knew the whole story.”")
    world.say(f"{hero.label} nodded. “A true detective listens, asks, and gives people room to tell the truth.”")
    world.say(f"Together they returned {params.object_name} to its proper place and thanked {case.suspect} for caring about others.")

    world.para()
    world.say(f"The lesson learned was simple: {case.lesson}.")
    world.say(f"{case.ending}.")
    world.say(f"{hero.label} and {friend.label} began the listening game, taking turns while their friendship made every quiet sound easier to hear.")

    world.facts.update(
        hero=hero,
        friend=friend,
        ear=ear,
        case=case.title,
        missing=case.missing,
        clue=case.clue,
        suspect=case.suspect,
        question=case.question,
        reveal=case.reveal,
        lesson=case.lesson,
        ending=case.ending,
        setting=params.setting,
        dialogue=True,
        friendship=True,
        bravery=True,
        lesson_learned=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    hero = facts["hero"].label
    friend = facts["friend"].label
    return [
        f"Write a child-friendly whodunit in which {hero} and {friend} solve {facts['case']} by listening carefully.",
        f"Include an ear as a useful clue, brave questions, and a warm friendship between {hero} and {friend}.",
        "End with a clear lesson learned about asking before blaming.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"].label
    friend = facts["friend"].label
    return [
        QAItem(
            question=f"What was missing when {hero} and {friend} began their investigation?",
            answer=f"{facts['missing'].capitalize()}.",
        ),
        QAItem(
            question=f"How did {hero} use an ear to find a clue?",
            answer=f"{hero} listened carefully with an ear and noticed that {facts['clue']}.",
        ),
        QAItem(
            question=f"Why did {hero} ask {facts['suspect']} questions instead of blaming them?",
            answer=f"{hero} knew that a suspicious clue did not prove guilt, so {hero} bravely asked {facts['suspect']} for the whole story.",
        ),
        QAItem(
            question=f"What did {facts['suspect']} explain?",
            answer=f"{facts['suspect']} explained that {facts['reveal']}.",
        ),
        QAItem(
            question=f"What lesson did {hero} and {friend} learn?",
            answer=f"They learned that {facts['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an ear help a person do?",
            answer="An ear helps a person hear sounds, listen to words, and notice what is happening nearby.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing the right or helpful thing even when a person feels nervous.",
        ),
        QAItem(
            question="Why should people ask questions before blaming someone?",
            answer="Questions can reveal missing information and prevent unfair blame.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== world qa =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes} traits={entity.traits}"
        )
    lines.append(f"facts: {sorted(world.facts)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_setting/1.
valid_setting(listening_room).
valid_setting(school_hall).
valid_setting(garden).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("setting", key) for key in SETTINGS)


def asp_program(show: str = "#show valid_setting/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    actual = sorted(set(asp.atoms(model, "valid_setting")))
    expected = sorted((key,) for key in SETTINGS)
    if actual != expected:
        print("MISMATCH: ASP settings do not match Python settings.")
        return 1
    for index, params in enumerate([
        StoryParams(seed=index, setting=SETTINGS["listening_room"], hero="Luna", friend="Pip")
        for index in range(len(CASES))
    ]):
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("MISMATCH: generated story verification failed.")
            return 1
    print(f"OK: ASP/Python parity and {len(CASES)} generated stories verified.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.friend:
        raise StoryError("The hero and friend must have different names.")
    if params.setting not in SETTINGS.values():
        raise StoryError("The setting must come from the registered settings.")
    world = tell(params)
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
    StoryParams(setting=SETTINGS["listening_room"], hero="Luna", friend="Pip", object_name="the silver bell", seed=0),
    StoryParams(setting=SETTINGS["school_hall"], hero="Mara", friend="Bea", object_name="the blue music box", seed=1),
    StoryParams(setting=SETTINGS["garden"], hero="Nia", friend="Kito", object_name="the brass whistle", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("Registered settings:")
        for key, value in SETTINGS.items():
            print(f"  {key}: {value}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            index += 1
            if index > max(100, args.n * 50):
                raise StoryError("Could not create enough distinct stories.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero} and {sample.params.friend}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
