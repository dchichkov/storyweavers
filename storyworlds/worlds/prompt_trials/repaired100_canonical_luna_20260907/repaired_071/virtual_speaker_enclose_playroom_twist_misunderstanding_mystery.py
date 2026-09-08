#!/usr/bin/env python3
"""
Standalone storyworld: a gentle playroom mystery about a virtual speaker,
an enclosing sound, a twist, and a misunderstanding.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str
    friend: str
    playroom: str = "playroom"
    object_name: str = "virtual speaker"
    seed: Optional[int] = None


HEROES = ["Luna", "Milo", "Nia", "Theo", "Ari", "June"]
FRIENDS = ["Pip", "Sora", "Ben", "Mina", "Ollie", "Rae"]
PLAYROOMS = {
    "playroom": "a bright playroom",
    "rainy playroom": "the rainy-day playroom",
    "moonlit playroom": "the moonlit playroom",
}
OBJECTS = ["virtual speaker", "virtual music box", "virtual storyteller"]


@dataclass(frozen=True)
class Mystery:
    title: str
    strange_event: str
    first_guess: str
    clue: str
    test: str
    cause: str
    repair: str
    lesson: str
    ending: str


MYSTERIES = [
    Mystery(
        "the echoing story cube",
        "a virtual speaker inside the story cube began speaking from every corner",
        "the speaker had escaped its little box",
        "the sound became soft when a blanket was lifted from the reading tent",
        "enclose the tent opening with pillows one at a time and listen from marked floor spots",
        "the blanket and tent walls were enclosing and bouncing the speaker's voice around the room",
        "moved the blanket aside and placed the speaker on a low shelf",
        "A strange sound deserves a fair test before a friend gets the blame",
        "the virtual speaker told one clear story while the tent stood open",
    ),
    Mystery(
        "the whispering blocks",
        "a virtual speaker whispered a secret whenever the block tower was tall",
        "someone was hiding a second speaker inside the tower",
        "the whisper stopped when one bright block was moved away from the wall",
        "build the tower again in the middle of the rug and compare the sound",
        "the wall and blocks were enclosing the speaker's sound and making it seem like a whisper",
        "left a small listening space around the tower",
        "A changed sound can come from a changed space",
        "the blocks made a neat tower while the speaker's voice stayed clear beside them",
    ),
    Mystery(
        "the upside-down welcome",
        "the virtual speaker welcomed the children from behind the toy kitchen",
        "the speaker had been switched to a secret upside-down mode",
        "the welcome came from the toy kitchen's metal oven door",
        "open the toy door and play the same greeting from the floor",
        "the metal door had reflected the speaker's voice toward the ceiling",
        "kept the toy kitchen door ajar during listening games",
        "A reflection can make a familiar thing seem to be somewhere else",
        "the speaker greeted them from its shelf as the toy kitchen shone quietly",
    ),
    Mystery(
        "the missing lullaby",
        "a virtual speaker played only the middle of a lullaby",
        "a friend had deleted the beginning",
        "the full tune returned when the stuffed-animal basket was moved",
        "place the basket in three safe spots and listen for the first notes",
        "the basket was enclosing the speaker's lower sound and hiding the beginning",
        "gave the speaker a clear space beside the basket",
        "When a part is missing, look for what may be blocking it",
        "the complete lullaby floated over the open basket and sleepy toys",
    ),
]


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.hero, params.friend, params.playroom, params.object_name))
    return sum((i + 1) * ord(c) for i, c in enumerate(text))


def build_world(params: StoryParams) -> World:
    if params.hero == params.friend:
        raise StoryError("hero and friend must be different children")
    if params.playroom not in PLAYROOMS:
        raise StoryError(f"unknown playroom: {params.playroom}")
    if params.object_name not in OBJECTS:
        raise StoryError(f"unknown object: {params.object_name}")

    rng = random.Random(_stable_seed(params) ^ 0x51A7)
    mystery = rng.choice(MYSTERIES)
    w = World(params)

    hero = w.add(Entity("hero", "child", params.hero, memes={"curiosity": 1.0}))
    friend = w.add(Entity("friend", "child", params.friend, memes={"worry": 0.0}))
    speaker = w.add(
        Entity(
            "speaker",
            "virtual_object",
            params.object_name,
            meters={"volume": 1.0, "height": 0.7},
            memes={"mystery": 1.0},
        )
    )
    enclosure = w.add(
        Entity(
            "enclosure",
            "playroom_object",
            "reading tent",
            meters={"openness": 0.3, "echo": 1.0},
        )
    )
    w.facts.update(
        hero=hero,
        friend=friend,
        speaker=speaker,
        enclosure=enclosure,
        mystery=mystery,
        setting=PLAYROOMS[params.playroom],
        resolved=False,
    )

    openings = [
        f"In {PLAYROOMS[params.playroom]}, {hero.label} was solving a small mystery with a notebook.",
        f"{hero.label} liked quiet clues, but the playroom had a noisy surprise waiting.",
        f"After the rain began, {hero.label} and {friend.label} made the playroom their detective station.",
        f"The playroom was full of cushions, blocks, and questions when {hero.label} arrived.",
    ]
    w.say(rng.choice(openings))
    w.say(
        f"{friend.label} was arranging a reading tent while {hero.label} placed a {speaker.label} "
        "on a low shelf."
    )
    w.say(
        f"The little device was virtual, so it could tell stories without a stack of paper or a winding key."
    )
    w.say(
        f"Then {mystery.strange_event}. The sound seemed to enclose the whole playroom."
    )

    w.para()
    w.facts["misunderstanding"] = True
    friend.memes["worry"] = 1.0
    w.say(
        f'{friend.label} pointed at the tent. "I think you {mystery.first_guess}."'
    )
    w.say(
        f'{hero.label} shook their head. "I did not change it. Let us find out what the speaker is really doing."'
    )
    w.say(
        f'"But I heard it over there!" {friend.label} answered. The misunderstanding made both children stop smiling.'
    )
    w.say(
        f'"A mystery needs a clue, not a quick blame," {hero.label} said. "{friend.label}, will you help me test it?"'
    )

    w.para()
    w.say("They began from the floor, where every child could listen safely.")
    w.say(f"{hero.label} noticed that {mystery.clue}.")
    w.say(
        f"{friend.label} listened again and admitted, " 
        f'"That clue changes what I thought. I was watching the room, not the sound."'
    )
    w.say(f"Together they decided to {mystery.test}.")
    speaker.meters["volume"] = 0.5
    enclosure.meters["openness"] = 1.0
    w.fired.add("fair_test")

    w.para()
    w.facts["resolved"] = True
    w.facts["cause"] = mystery.cause
    hero.memes["trust"] = 1.0
    friend.memes["worry"] = 0.0
    w.say(f"The test supplied a surprising twist: {mystery.cause}.")
    w.say(
        f"{hero.label} smiled. " 
        f'"The virtual speaker never moved. The playroom changed the path of its voice."'
    )
    w.say(f"Together they {mystery.repair}.")
    w.say(
        f'{friend.label} looked at {hero.label}. "I am sorry I blamed you. I let a misunderstanding become a fact."'
    )
    w.say(
        f'{hero.label} answered, "Thank you for helping me test it. Friends can fix a mystery together."'
    )
    w.say(f"{mystery.lesson}.")
    w.say(f"When the game was over, {mystery.ending}.")

    return w


def generation_prompts(world: World) -> list[str]:
    m: Mystery = world.facts["mystery"]
    return [
        'Write a child-friendly Mystery in a playroom using the words "virtual", "speaker", and "enclose".',
        f"Tell how {world.facts['hero'].label} and {world.facts['friend'].label} solve {m.title} after a Misunderstanding.",
        f"Include a Twist showing that {m.cause}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    m: Mystery = world.facts["mystery"]
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    return [
        QAItem(
            question=f"What mystery did {hero.label} and {friend.label} investigate?",
            answer=f"They investigated {m.strange_event}. The virtual speaker seemed to make its voice fill the playroom.",
        ),
        QAItem(
            question=f"What misunderstanding did {friend.label} have?",
            answer=f"{friend.label} thought that {m.first_guess}, but that was only a quick guess and not a proven fact.",
        ),
        QAItem(
            question="What clue changed the investigation?",
            answer=f"The important clue was that {m.clue}. That observation led the children to test the sound instead of blaming one another.",
        ),
        QAItem(
            question="What was the twist in the mystery?",
            answer=f"The twist was that {m.cause}. The speaker stayed where it was, while the playroom changed how its voice traveled.",
        ),
        QAItem(
            question=f"How did {hero.label} and {friend.label} repair their misunderstanding?",
            answer=f"They worked together to {m.test}. Then {friend.label} apologized for blaming {hero.label}, and they agreed that friends should test clues fairly.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a virtual speaker?",
            answer="A virtual speaker is a device or program that produces a voice or sound without needing a person to speak right beside it.",
        ),
        QAItem(
            question="What does enclose mean?",
            answer="To enclose something means to surround it or hold it inside a space.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone understands a situation incorrectly, often because they do not yet have all the clues.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a question or puzzling event that people solve by noticing clues and testing explanations.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A playroom Mystery about a virtual speaker and a misunderstanding."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--playroom", choices=list(PLAYROOMS))
    parser.add_argument("--object-name", choices=OBJECTS, default=None)
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
    hero = args.hero or rng.choice(HEROES)
    available = [name for name in FRIENDS if name != hero]
    friend = args.friend or rng.choice(available)
    playroom = args.playroom or rng.choice(list(PLAYROOMS))
    object_name = args.object_name or rng.choice(OBJECTS)
    if hero == friend:
        raise StoryError("hero and friend must be different children")
    return StoryParams(
        hero=hero,
        friend=friend,
        playroom=playroom,
        object_name=object_name,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: kind={entity.kind} label={entity.label!r} "
            f"meters={meters} memes={memes}"
        )
    lines.append(f"  resolved={world.facts.get('resolved')}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
valid_playroom(P) :- playroom(P).
valid_object(O) :- object(O).
valid_story(P,O) :- valid_playroom(P), valid_object(O).
"""


def asp_facts() -> str:
    import asp

    facts = [asp.fact("playroom", key) for key in PLAYROOMS]
    facts.extend(asp.fact("object", name.replace(" ", "_")) for name in OBJECTS)
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> set[tuple[str, str]]:
    return {(playroom, name.replace(" ", "_")) for playroom in PLAYROOMS for name in OBJECTS}


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    found = set(asp.atoms(model, "valid_story"))
    expected = valid_combos()
    if found == expected:
        print(f"OK: ASP gate matches Python gate ({len(expected)} combinations).")
        for index, (playroom, object_name) in enumerate(sorted(expected)):
            if index >= 3:
                break
            sample = generate(
                StoryParams(
                    hero=HEROES[index],
                    friend=FRIENDS[index],
                    playroom=playroom,
                    object_name=object_name.replace("_", " "),
                    seed=100 + index,
                )
            )
            if not sample.story or "playroom" not in sample.story:
                print("Generated story exercise failed.")
                return 1
        print("OK: generated stories exercised.")
        return 0
    print("ASP/Python mismatch.")
    print("Only in ASP:", sorted(found - expected))
    print("Only in Python:", sorted(expected - found))
    return 1


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("Compatible playroom/object combinations:")
        for playroom, object_name in sorted(valid_combos()):
            print(f"  {playroom} + {object_name.replace('_', ' ')}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, playroom in enumerate(PLAYROOMS):
            samples.append(
                generate(
                    StoryParams(
                        hero=HEROES[index % len(HEROES)],
                        friend=FRIENDS[index % len(FRIENDS)],
                        playroom=playroom,
                        object_name=OBJECTS[index % len(OBJECTS)],
                        seed=base_seed + index,
                    )
                )
            )
    else:
        for index in range(max(1, args.n)):
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
