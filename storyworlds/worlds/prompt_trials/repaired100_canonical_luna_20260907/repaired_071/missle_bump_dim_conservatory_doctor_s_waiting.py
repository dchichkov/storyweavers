#!/usr/bin/env python3
"""
Standalone storyworld: an animal story about a missle, a bump-dim light,
sharing, and moral value in a doctor's waiting room.

The odd seed words are treated as story language: "missle" names a soft toy
rocket, "bump-dim" describes a light that briefly grows dull after a bump, and
"conservatory" is a remembered place in the waiting-room mural.
"""

from __future__ import annotations

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


PLACES = {
    "doctor's waiting room": {
        "safe": True,
        "mural": "a green conservatory filled with painted ferns",
        "lamp": "a small star lamp",
    },
}

ANIMALS = ["Luna", "Pip", "Mara", "Otis", "Nell", "Bram"]
COMPANIONS = ["Pip", "Mara", "Otis", "Nell", "Bram"]
TOYS = ["missle", "paper boat", "wooden train"]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("distance", "softness", "brightness", "bump"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "kindness", "trust", "sharing", "relief"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    place: str
    hero: str
    companion: str
    toy: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Episode:
    title: str
    worry: str
    discovery: str
    test: str
    cause: str
    repair: str
    moral: str
    ending: str


EPISODES = [
    Episode(
        "The Quiet Missle",
        "the little missle slid beneath a chair just as the waiting-room lamp gave a bump-dim blink",
        "a soft tap on the chair leg had nudged the lamp cord",
        "put a paper marker beside the chair and asked the nurse to check the cord",
        "the lamp was safe, but its plug had been jostled by the rolling toy",
        "shared the missle with the smaller animals and kept it away from the cord",
        "Sharing makes a waiting room kinder, and careful choices protect everyone",
        "the missle rested in Luna's paws while the star lamp shone steadily above the painted conservatory",
    ),
    Episode(
        "The Conservatory Clue",
        "a bright sticker on the missle looked missing after the room's lamp went bump-dim",
        "the sticker had not vanished; it was hidden behind the toy's soft fin",
        "turned the missle slowly on the nurse's clean tray instead of pulling at the sticker",
        "the fin covered the sticker whenever the toy rolled toward the mural",
        "passed the toy around so each friend could see the sticker without grabbing",
        "A fair share of the truth is better than a fast guess about a friend",
        "the sticker gleamed like a tiny leaf in the conservatory mural",
    ),
    Episode(
        "The Bump-Dim Bell",
        "the waiting-room bell made a small bump-dim sound when the missle touched the rug",
        "the sound came from the rubber mat, not from a frightened animal",
        "rolled the toy only across the marked rug while the nurse watched",
        "the missle's soft wheel pressed a loose edge of the mat",
        "placed the toy in a basket and let every friend choose a quiet turn",
        "Moral value grows when we share space as well as possessions",
        "the bell was quiet, the rug lay flat, and the friends smiled beneath the conservatory vines",
    ),
]


OPENINGS = [
    "Rain whispered against the windows of the doctor's waiting room.",
    "The doctor's waiting room held a painted conservatory, three small chairs, and a basket of toys.",
    "While grown-ups spoke softly at the desk, the animal friends waited beneath a green mural.",
]

DIALOGUE = [
    '"Please let me try the missle," said Pip. "We can share it without rushing."',
    '"I thought you broke it," Luna said. "Can we look together instead of blaming?"',
    '"The bump-dim sound scared me," said the companion. "Then let us ask for help," Luna replied.',
]

ASP_RULES = r"""
valid_place(P) :- place(P).
valid_toy(T) :- toy(T).
valid_story(P,T) :- valid_place(P), valid_toy(T).
"""


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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
    text = "|".join((params.place, params.hero, params.companion, params.toy))
    return sum((i + 1) * ord(c) for i, c in enumerate(text))


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.toy not in TOYS:
        raise StoryError(f"Unknown toy: {params.toy}")
    if params.hero == params.companion:
        raise StoryError("The hero and companion must be different animals.")

    rng = random.Random(_stable_seed(params) ^ 0xBUMP)
    episode = rng.choice(EPISODES)
    opening = rng.choice(OPENINGS)
    dialogue = rng.choice(DIALOGUE)

    world = World(params)
    hero = world.add(Entity("hero", "animal", params.hero))
    companion = world.add(Entity("companion", "animal", params.companion))
    toy = world.add(Entity("toy", "object", params.toy))
    lamp = world.add(Entity("lamp", "object", PLACES[params.place]["lamp"]))
    mural = world.add(Entity("mural", "object", PLACES[params.place]["mural"]))

    toy.meters.update(distance=0.4, softness=1.0)
    lamp.meters.update(brightness=1.0, bump=0.0)
    hero.memes["worry"] = 1.0
    companion.memes["worry"] = 1.0

    world.facts.update(
        episode=episode,
        hero=hero,
        companion=companion,
        toy=toy,
        lamp=lamp,
        mural=mural,
        place=params.place,
    )

    world.say(opening)
    world.say(
        f"{hero.label} the rabbit sat beside {companion.label} the fox, "
        f"watching the {mural.label} while they waited for the doctor."
    )
    world.say(
        f"On the toy basket lay a soft {params.toy}. Its label called it a missle, "
        "though it was only a harmless waiting-room toy."
    )

    world.para()
    world.say(f"Their calm changed when {episode.worry}.")
    world.say(dialogue)
    world.say(
        f"{companion.label} looked worried, but {hero.label} remembered that "
        "sharing meant giving every friend a fair turn."
    )
    world.say(
        f'"We will use our eyes and our words," said {hero.label}. '
        f'"The nurse can help us check the {episode.title.lower()}."'
    )

    world.para()
    world.say(f"First, they noticed that {episode.discovery}.")
    world.say(f"To test the idea safely, they {episode.test}.")
    world.say(f"The nurse listened, and the evidence showed that {episode.cause}.")
    world.say(
        f"{hero.label} passed the {params.toy} to {companion.label}, "
        "then invited two younger animals to take gentle turns."
    )
    toy.memes["sharing"] = 1.0
    hero.memes["kindness"] = 1.0
    companion.memes["kindness"] = 1.0
    lamp.meters["brightness"] = 1.0
    lamp.meters["bump"] = 0.0

    world.para()
    world.say(f"Together, the friends {episode.repair}.")
    world.say(
        f"{companion.label} smiled. 'I was scared, but you did not blame me.' "
        f"{hero.label} answered, 'We learned the truth together.'"
    )
    hero.memes["trust"] = 1.0
    companion.memes["trust"] = 1.0
    hero.memes["relief"] = 1.0
    companion.memes["relief"] = 1.0
    world.say(f"They wrote one moral value on the waiting-room card: {episode.moral}.")
    world.say(f"As the doctor called their names, {episode.ending}.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write an Animal Story in a doctor\'s waiting room using "missle", "bump-dim", and "conservatory".',
        f"Show {f['hero'].label} and {f['companion'].label} practicing Sharing with a soft {f['toy'].label}.",
        f"End with the Moral Value: {f['episode'].moral}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    companion = f["companion"].label
    return [
        QAItem(
            f"Where were {hero} and {companion} waiting?",
            f"{hero} and {companion} were in the doctor's waiting room, beneath a mural of {f['mural'].label}.",
        ),
        QAItem(
            "What was the missle?",
            f"The missle was a harmless soft {f['toy'].label} from the waiting-room toy basket.",
        ),
        QAItem(
            f"What caused the bump-dim event in {f['episode'].title}?",
            f"The investigation showed that {f['episode'].cause}.",
        ),
        QAItem(
            f"How did {hero} show Sharing?",
            f"{hero} shared the {f['toy'].label} with {companion} and invited the younger animals to take gentle turns.",
        ),
        QAItem(
            "What Moral Value did the friends learn?",
            f"They learned that {f['episode'].moral}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a conservatory?", "A conservatory is a glass room or a place filled with growing plants."),
        QAItem("What does sharing mean?", "Sharing means letting other people use or enjoy something with you."),
        QAItem("What is moral value?", "A moral value is a good principle that helps guide kind and fair choices."),
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "doctor's waiting room"
    hero = args.hero or rng.choice(ANIMALS)
    available = [name for name in COMPANIONS if name != hero]
    companion = args.companion or rng.choice(available)
    toy = args.toy or rng.choice(TOYS)
    return StoryParams(place, hero, companion, toy, args.seed)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Animal storyworld in a doctor's waiting room.")
    parser.add_argument("--place", choices=list(PLACES))
    parser.add_argument("--hero", choices=ANIMALS)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--toy", choices=TOYS)
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


def asp_facts() -> str:
    import asp
    facts = [asp.fact("place", place) for place in PLACES]
    facts.extend(asp.fact("toy", toy) for toy in TOYS)
    return "\n".join(facts)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "valid_story"))
    expected = {(place, toy) for place in PLACES for toy in TOYS}
    if found != expected:
        print("ASP/Python parity failure.")
        print("Only ASP:", sorted(found - expected))
        print("Only Python:", sorted(expected - found))
        return 1
    for seed in range(5):
        params = StoryParams("doctor's waiting room", "Luna", "Pip", "missle", seed)
        sample = generate(params)
        if not sample.story or "doctor's waiting room" not in sample.story:
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP/Python parity and generated stories verified ({len(found)} combinations).")
    return 0


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    lines.append(f"  facts={sorted(world.facts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("Compatible doctor's waiting-room stories:")
        for place in PLACES:
            for toy in TOYS:
                print(f"  {place} / {toy}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for toy in TOYS:
            params = StoryParams("doctor's waiting room", "Luna", "Pip", toy, base_seed)
            samples.append(generate(params))
    else:
        for index in range(max(1, args.n)):
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = base_seed + index
            params = resolve_params(local_args, random.Random(base_seed + index))
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
