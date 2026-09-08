#!/usr/bin/env python3
"""
A nursery-rhyme storyworld about a tram, a perception exhibit, and a bad
ending repaired by careful noticing.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Exhibit:
    id: str
    name: str
    illusion: str
    truth: str
    clue: str
    mistake: str
    consequence: str
    repair: str
    ending: str


@dataclass
class World:
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
    place: str = "tram_hall"
    activity: str = "perception"
    name: str = "Luna"
    friend_name: str = "Pip"
    trait: str = "bright"
    seed: Optional[int] = None


EXHIBITS = [
    Exhibit(
        "moon_window",
        "the Moon Window",
        "a silver moon seemed to follow the tram",
        "the moon stayed still while the tram moved past it",
        "the moon's reflection slid across the glass while the painted stars did not move",
        "pulled the red emergency bell because the moon looked ready to crash",
        "the tram stopped with a clank, and the passengers lost their sunny afternoon ride",
        "watched the reflection, then checked the quiet stars and the steady rails",
        "the tram rolled on, and the moon winked safely from the window",
    ),
    Exhibit(
        "tilting_room",
        "the Tilting Room",
        "the floor seemed to slope toward the ceiling",
        "the room was level but its stripes leaned to fool the eye",
        "a marble rolled straight across the floor",
        "crawled on hands and knees and knocked over the guide's basket",
        "bright marbles scattered beneath the exhibit benches",
        "tested the floor with a marble before trusting the slanting stripes",
        "the marbles clicked in a neat line while the room only pretended to lean",
    ),
    Exhibit(
        "giant_teacup",
        "the Giant Teacup",
        "a tiny tram appeared to fit inside a giant cup",
        "curved mirrors stretched the tram's image",
        "the same yellow handle appeared twice in the mirror",
        "shouted that the tram had shrunk and chased its reflection",
        "a little child missed the exhibit talk while everyone watched the chase",
        "counted the handles and followed the real tram's wheels",
        "the real tram chimed outside as its mirrored twin bowed inside the cup",
    ),
    Exhibit(
        "backward_clock",
        "the Backward Clock",
        "the clock hands seemed to run backward",
        "the numbers were painted in reverse around a turning mirror",
        "the second hand's shadow moved forward on the wall",
        "turned the clock's large silver knob",
        "the exhibit froze and the next visitors could not see its trick",
        "watched the shadow instead of grabbing the tempting knob",
        "the clock ticked forward, though its bright face still played backward",
    ),
]

NAMES = ["Luna", "Mara", "Nia", "Tess", "Ada", "Jo"]
FRIENDS = ["Pip", "Milo", "Toby", "Bea", "Finn", "Rue"]
TRAITS = ["bright", "curious", "gentle", "swift", "thoughtful"]
MODES = ["rhyme_first", "tram_first", "question_first", "friend_first"]


def meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def reasonable(params: StoryParams) -> bool:
    return params.place == "tram_hall" and params.activity == "perception"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A nursery-rhyme tram story about perception and a bad ending."
    )
    parser.add_argument("--place", choices=["tram_hall"])
    parser.add_argument("--activity", choices=["perception"])
    parser.add_argument("--name")
    parser.add_argument("--friend-name", dest="friend_name")
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    friend_name = args.friend_name or rng.choice(FRIENDS)
    if name == friend_name:
        raise StoryError("The rider and the friend must have different names.")
    return StoryParams(
        place=args.place or "tram_hall",
        activity=args.activity or "perception",
        name=name,
        friend_name=friend_name,
        trait=args.trait or rng.choice(TRAITS),
    )


def tell(params: StoryParams) -> World:
    world = World()
    rider = world.add(Entity(params.name, "character", "child"))
    friend = world.add(Entity(params.friend_name, "character", "child"))
    tram = world.add(Entity("tram", "vehicle", "tram", "the blue tram"))
    exhibit = world.add(Entity("exhibit", "place", "exhibit", "the perception exhibit"))

    route = params.seed if params.seed is not None else sum(
        ord(c) for c in params.name + params.friend_name
    )
    chosen = EXHIBITS[route % len(EXHIBITS)]
    mode = MODES[(route // len(EXHIBITS)) % len(MODES)]

    openings = {
        "rhyme_first": [
            f"Clang, clang, rang the tram through the hall, while {params.name} stood {params.trait} and small.",
            f"{params.friend_name} held a ticket bright as a star beside {chosen.name}, the perception exhibit afar.",
        ],
        "tram_first": [
            f"The blue tram went clickety-clack past {chosen.name}, the perception exhibit.",
            f"{params.name} and {params.friend_name} climbed aboard, with wonder in every seat.",
        ],
        "question_first": [
            f'"Can eyes tell truth, or can eyes play?" asked {params.name} beside the tram that day.',
            f"{params.friend_name} pointed toward {chosen.name}, where a curious perception game was underway.",
        ],
        "friend_first": [
            f"{params.friend_name} waved from the tram with a bright ticket in hand.",
            f"{params.name} joined the friend at {chosen.name}, where odd sights filled the stand.",
        ],
    }
    for line in openings[mode]:
        world.say(line)

    world.say(
        f"Inside the exhibit, {chosen.illusion}; it shimmered like a riddle in the sun."
    )
    world.say(
        f"{params.name} cried, \"The tram is in danger! Look at what I see!\""
    )
    world.say(
        f"{params.friend_name} answered, \"I see it too, but let's check before we flee.\""
    )

    world.para()
    meter(rider, "attention", 1)
    meme(rider, "alarm", 1)
    world.say(f"Yet {params.name} trusted the first look and {chosen.mistake}.")
    world.say(
        f"That was the bad ending: {chosen.consequence}."
    )
    meme(friend, "worry", 1)
    meter(friend, "careful_observation", 1)
    world.say(
        f"The tram bell gave a lonely ding, and the exhibit grew quiet as a winter wing."
    )

    world.para()
    world.say(f"{params.friend_name} took a breath and said, \"Let's test the sight.")
    world.say(f"{chosen.clue.capitalize()}—that clue may make the picture right.\"")
    world.say(
        f"{params.name} looked again. The frightening shape was a trick of light, glass, and motion, not a real plight."
    )
    meter(rider, "understanding", 1)
    meme(rider, "relief", 1)
    meme(rider, "alarm", -1)
    meme(friend, "kindness", 1)
    world.say(
        f"Together they {chosen.repair}, then told the conductor what they had learned."
    )
    world.say(
        f'"First look, then check," said {params.name}. "That is a lesson worth keeping."'
    )
    world.say(
        f'"And ask a friend," said {params.friend_name}. "A second pair of eyes can help."'
    )

    world.para()
    meter(tram, "safe_motion", 1)
    meme(rider, "friendship", 1)
    meme(friend, "friendship", 1)
    world.say(
        f"The conductor rang the bell, and {chosen.ending}."
    )
    world.say(
        f"Clang, clang, the tram went on; the bad ending ended, and a wiser ride began."
    )

    world.facts.update(
        rider=rider,
        friend=friend,
        tram=tram,
        exhibit=exhibit,
        selected=chosen,
        mode=mode,
        bad_ending=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    exhibit = world.facts["selected"]
    rider = world.facts["rider"]
    friend = world.facts["friend"]
    return [
        "Write a child-friendly nursery rhyme about a tram and a perception exhibit.",
        f"Show how {rider.id} mistakes {exhibit.illusion}, causing a bad ending, while {friend.id} uses a concrete clue to repair it.",
        f"End with the tram safe and moving after the children learn to check what they see.",
    ]


def story_qa(world: World) -> list[QAItem]:
    exhibit = world.facts["selected"]
    rider = world.facts["rider"]
    friend = world.facts["friend"]
    return [
        QAItem(
            f"What did {rider.id} believe at first?",
            f"{rider.id} believed that {exhibit.illusion}. The first appearance seemed dangerous, but it was only a perception trick.",
        ),
        QAItem(
            f"What clue did {friend.id} notice?",
            f"{friend.id} noticed that {exhibit.clue}. That evidence helped the children separate the real tram from the misleading appearance.",
        ),
        QAItem(
            "What was the bad ending in the story?",
            f"The bad ending was that {exhibit.consequence}. The tram stopped because the child acted before checking the exhibit.",
        ),
        QAItem(
            "How did the children fix the trouble?",
            f"They {exhibit.repair}. They checked the evidence together and then explained the mistake to the conductor.",
        ),
        QAItem(
            "What final image showed that the story had a good resolution?",
            f"{exhibit.ending}. The moving tram showed that the danger had passed.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a tram?",
            "A tram is a vehicle that carries people along rails, usually through streets or a town.",
        ),
        QAItem(
            "What does perception mean?",
            "Perception is the way a person notices and understands information through the senses, such as sight and hearing.",
        ),
        QAItem(
            "Why should someone check an unusual sight?",
            "Checking an unusual sight can reveal whether it is real, a reflection, or an illusion before someone makes a risky choice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
tram(t).
perception_exhibit(e).
rider(r).
friend(f).
misperception(r).
checks(f).
helps(f,r).
resolved(r) :- misperception(r), checks(f), helps(f,r).
safe_tram(t) :- resolved(r).
#show resolved/1.
#show safe_tram/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("tram", "t"),
            asp.fact("perception_exhibit", "e"),
            asp.fact("rider", "r"),
            asp.fact("friend", "f"),
            asp.fact("misperception", "r"),
            asp.fact("checks", "f"),
            asp.fact("helps", "f", "r"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    resolved = bool(asp.atoms(model, "resolved"))
    safe = bool(asp.atoms(model, "safe_tram"))
    if resolved and safe:
        print("OK: ASP and Python reasonableness agree.")
        return 0
    print("MISMATCH between ASP and Python reasonableness.")
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(
            f"  {entity.id:10} ({entity.type:12}) {' '.join(details)}"
        )
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if not reasonable(params):
        raise StoryError("This world requires a tram-hall perception story.")
    world = tell(params)
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


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams("tram_hall", "perception", "Luna", "Pip", "bright", 0),
        StoryParams("tram_hall", "perception", "Mara", "Milo", "curious", 1),
        StoryParams("tram_hall", "perception", "Nia", "Bea", "gentle", 2),
        StoryParams("tram_hall", "perception", "Tess", "Finn", "thoughtful", 3),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:", " ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in valid_story_params()]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            rng = random.Random(base_seed + index)
            index += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} and {sample.params.friend_name} ride the tram"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
