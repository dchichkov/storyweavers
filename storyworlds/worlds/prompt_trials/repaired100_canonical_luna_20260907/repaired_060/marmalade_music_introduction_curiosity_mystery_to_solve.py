#!/usr/bin/env python3
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
feature(curiosity).
feature(mystery_to_solve).
feature(lesson_learned).
ingredient(marmalade).
art(music).
event(introduction).

has_clue :- ingredient(marmalade), art(music).
can_solve :- feature(curiosity), feature(mystery_to_solve), has_clue.
wise_ending :- can_solve, feature(lesson_learned).
#show wise_ending/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    companion: str = "a small brass bird"
    marmalade: str = "orange marmalade"
    instrument: str = "a wooden flute"
    place: str = "the village square"
    time: str = "morning"


@dataclass
class Character:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, delta: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta

    def add_meme(self, key: str, delta: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + delta


@dataclass
class ObjectThing:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, delta: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta

    def add_meme(self, key: str, delta: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + delta


@dataclass
class World:
    params: StoryParams
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, ObjectThing] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def add_character(self, character: Character) -> Character:
        self.characters[character.name] = character
        return character

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.name] = obj
        return obj

    def say(self, text: str) -> None:
        self.trace.append(text)

    def render(self) -> str:
        return "\n\n".join(self.trace)


SCENARIOS = [
    {
        "title": "the silent breakfast bell",
        "premise": "the baker's music bell stopped ringing before the village breakfast",
        "obstacle": "Without its cheerful tune, the baker did not know when the warm loaves were ready",
        "clue": "a sticky streak of marmalade crossed the bell rope and ended beneath a flour sack",
        "action": "Luna lifted the sack carefully and found a sleepy mouse curled around the rope",
        "dialogue": "'The music has a listener,' Luna said. 'Let us help it wake somewhere safer.'",
        "resolution": "The baker moved the mouse to a basket of grain, then cleaned the rope and rang the bell",
        "ending": "the bell played three bright notes while golden toast received its first shining spoonful of marmalade",
        "lesson": "curiosity is kindest when it solves a mystery without causing new trouble",
    },
    {
        "title": "the missing melody",
        "premise": "the town musician could play every note except the one that began the afternoon introduction",
        "obstacle": "The missing note made the new song sound as if it had lost its way",
        "clue": "a dab of marmalade marked the page beside a tiny drawing of a robin",
        "action": "Luna followed the robin's song to the garden and listened until its first call matched the missing note",
        "dialogue": "'Perhaps the song is hiding in a living throat,' Luna told the musician",
        "resolution": "The musician used the robin's call as the introduction and finished the song beautifully",
        "ending": "children hummed along while marmalade-colored leaves trembled to the music",
        "lesson": "a curious listener can find answers by paying attention to the world around them",
    },
    {
        "title": "the marmalade jar orchestra",
        "premise": "the village jars made a strange clattering music during the welcome introduction",
        "obstacle": "The clatter frightened the guests and hid the mayor's careful words",
        "clue": "only the jars on the sunny shelf rattled, and each had a loose wooden spoon beside it",
        "action": "Luna tested one spoon gently, then showed the mayor how the warm glass made the spoons dance",
        "dialogue": "'It is not a ghost,' Luna said. 'It is a little orchestra asking for space.'",
        "resolution": "The spoons were removed, and the jars became quiet while a real band played",
        "ending": "after the music, everyone spread the rescued marmalade on bread and laughed",
        "lesson": "a mystery becomes smaller when careful tests replace frightened guesses",
    },
    {
        "title": "the tune behind the pantry",
        "premise": "a faint tune came from behind the pantry whenever someone opened a marmalade jar",
        "obstacle": "The cook feared that a hungry creature had become trapped in the wall",
        "clue": "the tune began only when the jar lid clicked, and the sound echoed through a copper pipe",
        "action": "Luna asked the cook to open one jar while she listened beside the pipe",
        "dialogue": "'The music follows the click,' Luna said. 'Let us trace the sound before we worry.'",
        "resolution": "They discovered that the pipe carried the pantry bell from the courtyard",
        "ending": "the introduction music rang clearly, and every jar stood safely on its shelf",
        "lesson": "curiosity can turn a frightening sound into a friendly explanation",
    },
    {
        "title": "the fable of the forgotten flute",
        "premise": "a flute played one lonely note beneath the old fig tree before the festival introduction",
        "obstacle": "No one knew who was playing, and the lonely note made the children uneasy",
        "clue": "a marmalade fingerprint marked the flute case beside a trail of crumbs",
        "action": "Luna followed the crumbs and found a shy child practicing behind the tree",
        "dialogue": "'Your music need not hide,' Luna said. 'Would you introduce the festival with us?'",
        "resolution": "The child joined the musicians and played the opening note with a brave smile",
        "ending": "the whole square clapped as marmalade toast passed from hand to hand",
        "lesson": "curiosity can reveal not only a mystery, but also a friend waiting for welcome",
    },
]


OPENINGS = [
    "One bright morning, {name} carried {marmalade} toward {place} with {companion}.",
    "At the hour of the first birdsong, {name} arrived at {place} with {marmalade} and {companion}.",
    "{name} was preparing for a musical introduction at {place}, and {companion} carried the {marmalade}.",
    "The village woke to sunshine, toast, and the promise of music as {name} entered {place}.",
    "Before the festival began, {name} brought {marmalade} to {place}, with {companion} fluttering close behind.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fable about marmalade, music, curiosity, and a mystery to solve."
    )
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--marmalade")
    parser.add_argument("--instrument")
    parser.add_argument("--place")
    parser.add_argument("--time")
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
    name = args.name or rng.choice(["Luna", "Milo", "Anya", "Pip", "Tavi"])
    companion = args.companion or rng.choice(
        ["a small brass bird", "a sleepy hedgehog", "a blue ribbon mouse"]
    )
    marmalade = args.marmalade or rng.choice(
        ["orange marmalade", "apricot marmalade", "golden citrus marmalade"]
    )
    instrument = args.instrument or rng.choice(
        ["a wooden flute", "a little violin", "a silver music box"]
    )
    place = args.place or "the village square"
    time = args.time or "morning"
    if place != "the village square":
        raise StoryError("This fable's introduction takes place in the village square.")
    if time != "morning":
        raise StoryError("This fable begins in the morning.")
    return StoryParams(
        seed=None,
        name=name,
        companion=companion,
        marmalade=marmalade,
        instrument=instrument,
        place=place,
        time=time,
    )


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("feature", "curiosity"),
            asp.fact("feature", "mystery_to_solve"),
            asp.fact("feature", "lesson_learned"),
            asp.fact("ingredient", "marmalade"),
            asp.fact("art", "music"),
            asp.fact("event", "introduction"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return all(
        [
            "curiosity" in {"curiosity", "mystery_to_solve", "lesson_learned"},
            "marmalade",
            "music",
            "introduction",
        ]
    )


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show wise_ending/0."))
    asp_ok = bool(asp.atoms(model, "wise_ending"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the fable gate.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    p = world.params
    seed = p.seed if p.seed is not None else 0
    scenario = SCENARIOS[seed % len(SCENARIOS)]
    opening = OPENINGS[(seed // len(SCENARIOS)) % len(OPENINGS)]
    values = {
        "name": p.name,
        "companion": p.companion,
        "marmalade": p.marmalade,
        "instrument": p.instrument,
        "place": p.place,
    }

    child = world.add_character(Character(p.name, "curious child"))
    companion = world.add_object(ObjectThing(p.companion, "companion"))
    instrument = world.add_object(ObjectThing(p.instrument, "musical instrument"))

    child.add_meme("curiosity", 1.0)
    child.add_meme("kindness", 0.5)
    child.add_meme("courage", 0.25)
    companion.add_meter("helpfulness", 1.0)

    world.say(opening.format(**values))
    world.say(
        f"On the table stood a jar of {p.marmalade}, beside {p.instrument}. "
        f"It was meant for the festival introduction, but a puzzling sound interrupted the music."
    )
    world.say(f"The mystery to solve was {scenario['title']}: {scenario['premise']}.")
    world.say(f"{scenario['obstacle']}. {scenario['clue'].capitalize()}.")

    child.add_meter("careful_steps", 3.0)
    world.say(
        f"Luna's first guess fluttered away, but curiosity stayed. "
        f"{scenario['action'].capitalize()}."
    )
    world.say(scenario["dialogue"])

    child.add_meme("courage", 1.0)
    child.add_meme("patience", 1.0)
    instrument.add_meter("music_ready", 1.0)
    world.say(f"{scenario['resolution']}. The mystery had become a lesson instead of a fright.")

    child.add_meme("wisdom", 1.0)
    world.say(
        f"Luna learned that {scenario['lesson']}. "
        f"That was the lesson learned: questions are lanterns when they are carried with care."
    )
    world.say(
        f"Then the introduction began. {scenario['ending']}. "
        f"{p.name} smiled as the morning music carried the sweet smell of {p.marmalade} across the square."
    )

    world.facts = {
        "scenario": scenario["title"],
        "premise": scenario["premise"],
        "obstacle": scenario["obstacle"],
        "clue": scenario["clue"],
        "action": scenario["action"],
        "resolution": scenario["resolution"],
        "lesson": scenario["lesson"],
        "ending": scenario["ending"],
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"What mystery did {p.name} need to solve?",
            answer=f"{f['premise'].capitalize()}. It mattered because {f['obstacle'].lower()}.",
        ),
        QAItem(
            question="What clue helped reveal the answer?",
            answer=f"{f['clue'].capitalize()} {p.name} used that detail instead of trusting a frightened guess.",
        ),
        QAItem(
            question=f"How did {p.name} show curiosity?",
            answer=f"{f['action'].capitalize()} This showed curiosity because {p.name} listened, tested, and looked carefully.",
        ),
        QAItem(
            question="What happened when the mystery was solved?",
            answer=f"{f['resolution']}. The music and the festival introduction could continue safely.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer=f"{f['lesson'].capitalize()} The fable shows that careful questions can bring both understanding and kindness.",
        ),
        QAItem(
            question="What image closes the story?",
            answer=f"{f['ending'].capitalize()} It proves that the mystery ended in music, welcome, and shared marmalade.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to notice, ask, and understand something that seems new or puzzling.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a question with clues that can lead a careful thinker toward an answer.",
        ),
        QAItem(
            question="Why can music help an introduction?",
            answer="Music can help an introduction by welcoming listeners and giving a gathering a cheerful beginning.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a useful truth someone understands after an experience and can remember later.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Write a fable about {p.name}, marmalade, and music at {p.place}.",
        f"Show {p.name} solving this mystery: {f['premise']}. Include the clue: {f['clue']}.",
        f"End with the lesson learned: {f['lesson']}.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for character in world.characters.values():
        lines.append(
            f"  {character.name} ({character.role}) "
            f"meters={character.meters} memes={character.memes}"
        )
    for obj in world.objects.values():
        lines.append(
            f"  {obj.name} ({obj.kind}) meters={obj.meters} memes={obj.memes}"
        )
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(params=params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show wise_ending/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show wise_ending/0."))
        print("wise_ending" if asp.atoms(model, "wise_ending") else "(no wise_ending)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            name=args.name or "Luna",
            companion=args.companion or "a small brass bird",
            marmalade=args.marmalade or "orange marmalade",
            instrument=args.instrument or "a wooden flute",
            place="the village square",
            time="morning",
        )
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
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
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
