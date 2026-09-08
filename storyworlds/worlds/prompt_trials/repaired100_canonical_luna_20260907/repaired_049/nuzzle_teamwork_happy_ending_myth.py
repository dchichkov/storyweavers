#!/usr/bin/env python3
"""
A small mythic storyworld about nuzzle, teamwork, and a happy ending.

In this world, a young moon-moth must help a sleepy hill spirit relight the
path to the village. Nuzzle is not magic by itself: it becomes useful when
gentle touch, listening, and shared work reveal the safe way forward.
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

STORYWORLDS_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, STORYWORLDS_ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, name: str) -> float:
        return self.meters.get(name, 0.0)

    def meme(self, name: str) -> float:
        return self.memes.get(name, 0.0)


@dataclass
class Setting:
    name: str
    affordances: set[str]


@dataclass(frozen=True)
class Trial:
    id: str
    trouble: str
    clue: str
    shared_tools: str
    careful_work: str
    result: str
    change: str
    ending: str


@dataclass(frozen=True)
class Myth:
    id: str
    opening: str
    lesson: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def paragraph(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTING = Setting(
    name="the Star Hill",
    affordances={"listening", "nuzzling", "carrying", "teamwork", "repair"},
)

TRIALS = {
    "moon_path": Trial(
        id="moon_path",
        trouble="the moon path had gone dark, and travelers could no longer see the stones above the village",
        clue="the dimmest stone warmed whenever two friends touched it together",
        shared_tools="a silver thread, three bright pebbles, and a little bell",
        careful_work="nuzzled the sleeping hill spirit awake while the others held the thread steady and placed the pebbles along the safe stones",
        result="the stones began to glow in a clear line from the hilltop to the village",
        change="the moon path would always be checked by a team, never by one watcher alone",
        ending="By dawn, the repaired path shone like a milk-white ribbon, and every traveler reached home safely.",
    ),
    "bell_garden": Trial(
        id="bell_garden",
        trouble="the dawn bells in the cloud garden had stopped ringing, so the sun did not know when to rise",
        clue="a tiny feather trembled whenever the bells were lifted as one",
        shared_tools="a woven ladder, soft cords, and a basket of cloud apples",
        careful_work="nuzzled the shy bell-maker from beneath its wing while the team lifted each bell together and tied its loose cord",
        result="the bells rang in a bright harmony, and the sun rose over the sleeping fields",
        change="the cloud garden would be tended in pairs, with a listening keeper beside every climber",
        ending="The first sunrise after the repair painted every cloud gold, and the bells sang for joy.",
    ),
}

MYTHS = {
    "hill_spirit": Myth(
        id="hill_spirit",
        opening="Long ago, before roads had names, a gentle spirit slept inside every high hill.",
        lesson="The old ones say that even a mighty spirit wakes more kindly for a gentle nuzzle than for a loud command.",
    ),
    "cloud_garden": Myth(
        id="cloud_garden",
        opening="In the first age, the sky kept a garden where bells grew from silver vines.",
        lesson="The sky remembers that shared hands can lift what one hand cannot, while a kind touch gives courage to begin.",
    ),
}

NAMES = {
    "girl": ["Luna", "Mira", "Tala", "Nia"],
    "boy": ["Oren", "Ivo", "Pax", "Tarin"],
}

COMPANIONS = ["a patient fox", "a bright beetle", "a small river bird", "a shy cloud mouse"]
TRAITS = ["curious", "kind", "brave", "patient"]
DIALOGUES = [
    ("We should not pull harder.", "Then let us listen more closely."),
    ("Can you feel where the path is warm?", "Yes. Let us follow it together."),
    ("What if the little one knows the way?", "Then we will make room for its small courage."),
    ("I can hold the cord.", "And I can watch the stones. No one needs to work alone."),
]


@dataclass
class StoryParams:
    place: str
    trial: str
    myth: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mythic teamwork storyworld about nuzzle and a happy ending."
    )
    parser.add_argument("--place", choices=["star_hill"])
    parser.add_argument("--trial", choices=TRIALS)
    parser.add_argument("--myth", choices=MYTHS)
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--companion")
    parser.add_argument("--trait", choices=TRAITS)
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
    trial = args.trial or rng.choice(list(TRIALS))
    myth = args.myth or ("hill_spirit" if trial == "moon_path" else "cloud_garden")
    if args.trial and args.trial not in TRIALS:
        raise StoryError(f"Unknown trial: {args.trial}.")
    if args.myth and args.myth not in MYTHS:
        raise StoryError(f"Unknown myth: {args.myth}.")
    if trial == "moon_path" and myth != "hill_spirit":
        raise StoryError("The moon path belongs to the hill-spirit myth.")
    if trial == "bell_garden" and myth != "cloud_garden":
        raise StoryError("The bell garden belongs to the cloud-garden myth.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    companion = args.companion or rng.choice(COMPANIONS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=args.place or "star_hill",
        trial=trial,
        myth=myth,
        name=name,
        gender=gender,
        companion=companion,
        trait=trait,
    )


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        ("star_hill", "moon_path", "hill_spirit"),
        ("star_hill", "bell_garden", "cloud_garden"),
    ]


def reasonableness_gate(params: StoryParams) -> None:
    if (params.place, params.trial, params.myth) not in valid_combos():
        raise StoryError(
            "This myth needs a Star Hill trial paired with its matching old spirit."
        )
    if not params.name.strip():
        raise StoryError("The hero needs a name.")
    if not params.companion.strip():
        raise StoryError("The helper needs a form.")


def add_meter(entity: Entity, name: str, amount: float = 1.0) -> None:
    entity.meters[name] = entity.meter(name) + amount


def add_meme(entity: Entity, name: str, amount: float = 1.0) -> None:
    entity.memes[name] = entity.meme(name) + amount


def tell(world: World, params: StoryParams) -> World:
    trial = TRIALS[params.trial]
    myth = MYTHS[params.myth]
    variant = params.seed if params.seed is not None else sum(
        (i + 1) * ord(c)
        for i, c in enumerate(
            f"{params.name}|{params.gender}|{params.companion}|{params.trait}"
        )
    )
    question, answer = DIALOGUES[variant % len(DIALOGUES)]

    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=params.gender,
            label=params.name,
            memes={"curiosity": 1.0, "courage": 1.0},
        )
    )
    companion = world.add(
        Entity(
            id="companion",
            kind="character",
            type="animal",
            label=params.companion,
            memes={"trust": 1.0},
        )
    )
    spirit = world.add(
        Entity(
            id="spirit",
            kind="character",
            type="spirit",
            label="the old hill spirit",
            memes={"sleep": 1.0},
        )
    )
    path = world.add(
        Entity(
            id="path",
            kind="place",
            type="path",
            label="the moon path",
            meters={"light": 0.0, "safety": 0.0},
        )
    )

    world.say(myth.opening)
    world.say(
        f"On {world.setting.name} lived {params.name}, a {params.trait} young keeper of small lights."
    )
    world.say(
        f"{params.name} traveled with {params.companion}, who noticed soft sounds that larger creatures missed."
    )
    world.paragraph()

    world.say(f"One evening, {trial.trouble}.")
    world.say(
        f"The village elder said, 'Whoever can mend the trouble with care may keep the path bright.'"
    )
    add_meme(hero, "worry")
    world.say(
        f"{params.name} reached for the nearest rope, but {params.companion} gave a worried chirp."
    )
    world.say(f'"{question}" {params.name} asked.')
    world.say(f'"{answer}" replied {params.companion}.')
    world.paragraph()

    add_meme(hero, "listening")
    add_meme(companion, "helpfulness")
    world.say(f"Together they discovered that {trial.clue}.")
    world.say(f"They shared {trial.shared_tools}.")
    add_meter(hero, "teamwork")
    add_meter(companion, "teamwork")
    add_meter(path, "shared_care")
    world.say(
        f"Then {params.name} {trial.careful_work}."
    )
    add_meme(spirit, "awake")
    add_meter(path, "light")
    add_meter(path, "safety")
    world.paragraph()

    world.say(f"The plan worked: {trial.result}.")
    world.say(
        f"The old spirit opened its eyes and said, 'A strong helper is not the one who works alone. A strong helper makes room for every good idea.'"
    )
    world.say(
        f"{params.name} answered, 'Then our teamwork should become part of the path.'"
    )
    add_meme(hero, "joy")
    add_meme(companion, "joy")
    world.say(f"The village agreed that {trial.change}.")
    world.say(trial.ending)
    world.say(myth.lesson)

    world.facts.update(
        hero=hero,
        companion=companion,
        spirit=spirit,
        path=path,
        trial=trial,
        myth=myth,
        question=question,
        answer=answer,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(World(SETTING), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    trial = world.facts["trial"]
    return [
        f"Write a gentle myth about {hero.label}, nuzzle, teamwork, and a happy ending.",
        f"Tell a myth in which {hero.label} must solve a problem by sharing work instead of working alone.",
        f"Write a child-friendly tale where a soft nuzzle helps awaken hope and repair {trial.trouble}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    trial = world.facts["trial"]
    path = world.facts["path"]
    return [
        QAItem(
            question=f"What trouble did {hero.label} have to solve?",
            answer=f"{hero.label} had to solve the problem that {trial.trouble}.",
        ),
        QAItem(
            question=f"Who helped {hero.label}?",
            answer=f"{companion.label} helped {hero.label} by noticing small clues and working as a teammate.",
        ),
        QAItem(
            question="What clue changed their plan?",
            answer=f"They noticed that {trial.clue}, so they stopped pulling blindly and began working carefully.",
        ),
        QAItem(
            question="How did nuzzle help?",
            answer=f"The hero nuzzled the sleeping spirit awake gently, which made it possible for the team to repair the trouble without frightening it.",
        ),
        QAItem(
            question="What did the team do together?",
            answer=f"They shared {trial.shared_tools} and then {trial.careful_work}.",
        ),
        QAItem(
            question="What proved that the ending was happy?",
            answer=f"{trial.result}. The path became safe, and {trial.ending}",
        ),
        QAItem(
            question="What lesson did the myth teach?",
            answer=f"The myth taught that teamwork lets different kinds of helpers contribute, while gentle care can awaken hope.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people or creatures share a goal, listen to one another, and combine their efforts.",
        ),
        QAItem(
            question="What does nuzzle mean?",
            answer="To nuzzle means to touch or rub gently with the nose, often as a sign of affection or comfort.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old-style story that uses wonder, spirits, or magical events to share an idea about life.",
        ),
        QAItem(
            question="What makes an ending happy?",
            answer="A happy ending shows that the danger or trouble has been resolved and that the characters are safer, wiser, or more joyful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    sections = ["== Prompts =="]
    sections.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    sections.append("")
    sections.append("== Story QA ==")
    for item in sample.story_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    sections.append("")
    sections.append("== World QA ==")
    for item in sample.world_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    return "\n".join(sections)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: {entity.type} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid(star_hill, moon_path, hill_spirit).
valid(star_hill, bell_garden, cloud_garden).
teamwork(trial) :- valid(_, _, _).
happy_ending(trial) :- teamwork(trial).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        asp.fact(name, *values)
        for name, values in [
            ("place", "star_hill"),
            ("trial", "moon_path"),
            ("myth", "hill_spirit"),
            ("feature", "teamwork"),
            ("feature", "happy_ending"),
            ("seed_word", "nuzzle"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH")
        print(f"Python: {sorted(py)}")
        print(f"ASP: {sorted(cl)}")
        return 1
    for params in CURATED:
        sample = generate(params)
        if "nuzzle" not in sample.story.lower():
            print("MISMATCH: generated story omitted nuzzle")
            return 1
        if not sample.story_qa or not sample.world_qa:
            print("MISMATCH: generated QA was incomplete")
            return 1
    print(f"OK: ASP matches Python ({len(py)} combos), and generated stories passed.")
    return 0


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
        "star_hill",
        "moon_path",
        "hill_spirit",
        "Luna",
        "girl",
        "a patient fox",
        "curious",
    ),
    StoryParams(
        "star_hill",
        "bell_garden",
        "cloud_garden",
        "Oren",
        "boy",
        "a bright beetle",
        "brave",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(args.n * 30, 30):
            current_seed = base_seed + index
            index += 1
            rng = random.Random(current_seed)
            try:
                params = resolve_params(args, rng)
                params.seed = current_seed
                sample = generate(params)
            except StoryError as error:
                print(error)
                return
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
        if args.all:
            params = sample.params
            header = f"### {params.name}: {params.trial} / {params.myth}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
