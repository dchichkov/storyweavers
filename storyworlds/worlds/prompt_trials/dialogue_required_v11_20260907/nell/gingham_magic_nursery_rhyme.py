#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


COLORS = ("blue", "red", "yellow")
VOICES = ("plain", "bouncy", "gentle")
SIZES = ("small", "large")


@dataclass
class StoryParams:
    hero: str = "Nell"
    color: str = "blue"
    size: str = "small"
    voice: str = "bouncy"
    world_seed: int = 777
    prose_seed: int = 42


@dataclass
class Entity:
    id: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: str = ""


@dataclass
class Event:
    id: int
    kind: str
    actor: str
    data: dict
    facts: tuple[str, ...]


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity]
    history: list[Event] = field(default_factory=list)
    outcome: str = ""

    def record(self, kind: str, actor: str, facts=(), **data):
        self.history.append(Event(len(self.history), kind, actor, data, tuple(facts)))


def validate_params(p: StoryParams):
    if p.color not in COLORS:
        raise StoryError(f"Unknown cloth color: {p.color!r}.")
    if p.size not in SIZES:
        raise StoryError(f"Unknown cloth size: {p.size!r}.")
    if p.voice not in VOICES:
        raise StoryError(f"Unknown voice: {p.voice!r}.")
    if not p.hero or not p.hero[0].isupper() or not p.hero.isalpha():
        raise StoryError("The hero must be a simple capitalized name.")
    if type(p.world_seed) is not int or type(p.prose_seed) is not int:
        raise StoryError("Seeds must be integers.")


def build_world(p: StoryParams) -> World:
    validate_params(p)
    world = World(
        params=p,
        entities={
            "nell": Entity("nell", p.hero, "nursery", memes={"curiosity": 1}),
            "mouse": Entity("mouse", "Mabel Mouse", "nursery", memes={"worry": 1}),
            "cloth": Entity(
                "cloth",
                f"{p.color} gingham cloth",
                "nursery",
                meters={"size": 1 if p.size == "small" else 2, "magic": 1},
                owner="nell",
            ),
            "moon": Entity("moon", "the moon", "sky", meters={"brightness": 2}),
            "crib": Entity("crib", "the wooden crib", "nursery", meters={"quiet": 0}),
            "bell": Entity("bell", "the silver bell", "nursery", meters={"sound": 1}),
        },
    )
    world.record("opening", "nell", ("night_started",), hour="moonrise")
    return world


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    w.record("discover", "nell", ("cloth_found",), color=p.color)
    w.record("question", "nell", ("problem_known",), problem="mouse cannot sleep")
    w.record("spell", "nell", ("magic_awake",), words="Hush-a-bye, gingham sky!")
    w.entities["cloth"].location = "crib"
    w.entities["crib"].meters["quiet"] = 1
    w.record("cover", "nell", ("crib_quiet",), material="gingham")
    w.entities["bell"].meters["sound"] = 0
    w.record("listen", "mouse", ("mouse_calm",), sound="soft")
    w.outcome = "sleeping_nursery"
    w.record("ending", "nell", ("story_resolved",), outcome=w.outcome)
    return w


def validate_world(w: World):
    if w.outcome != "sleeping_nursery":
        raise StoryError("The nursery must reach a peaceful ending.")
    if w.entities["cloth"].location != "crib":
        raise StoryError("The gingham cloth must cover the crib.")
    if w.entities["crib"].meters["quiet"] != 1:
        raise StoryError("The crib must become quiet.")
    if w.entities["bell"].meters["sound"] != 0:
        raise StoryError("The bell must be quiet at bedtime.")
    if len(w.history) < 6:
        raise StoryError("The story needs a beginning, turn, and resolution.")


def render(w: World) -> tuple[str, list[QAItem]]:
    p = w.params
    rng = random.Random(p.prose_seed)
    cloth = f"{p.color} gingham"
    if p.voice == "plain":
        opening = f"At moonrise, {p.hero} tiptoed into the nursery."
        middle = f"She found a {cloth} cloth and held it up to the moon."
        ending = "The nursery grew still, and Mabel Mouse slept."
    elif p.voice == "gentle":
        opening = f"Moon climbed high while {p.hero} watched the nursery glow."
        middle = f"Beside the crib lay a {cloth} cloth, soft as a cloud."
        ending = "Under the quiet cloth, Mabel Mouse dreamed a silver dream."
    else:
        opening = f"At moonrise bright, {p.hero} came light, light, light, into the nursery."
        middle = f"She found {cloth}, check by check, and held it high above the little crib."
        ending = "Hush went the bell, hush went the room, and Mabel Mouse slept till noon."

    if rng.random() < 0.5:
        dialogue = (
            f'"Mabel, what troubles you?" asked {p.hero}.\n'
            f'"The bell is loud, and sleep will not come," said Mabel.\n'
            f'"Then listen closely," said {p.hero}. "We shall make a quieter spell."'
        )
    else:
        dialogue = (
            f'"Can gingham work magic?" asked Mabel.\n'
            f'"Only when someone kind believes," said {p.hero}.\n'
            f'"Then I believe," whispered Mabel.'
        )

    story = (
        f"{opening}\n\n"
        f"{dialogue}\n\n"
        f"{middle} She touched its corner and sang, "
        f'"Hush-a-bye, gingham sky; let every noisy worry fly!" '
        f"The magic shimmered through the checks. The silver bell stopped ringing, "
        f"and the crib became calm.\n\n"
        f"{ending}"
    )
    qa = [
        QAItem(
            "What did Nell use to quiet the nursery?",
            f"Nell used a {cloth} cloth and a gentle magic rhyme to quiet the nursery.",
        ),
        QAItem(
            "Why did Mabel Mouse need help?",
            "Mabel Mouse could not sleep because the silver bell was too loud.",
        ),
        QAItem(
            "What changed at the end?",
            "The bell became quiet, the crib grew calm, and Mabel Mouse fell asleep.",
        ),
    ]
    return story, qa


ASP_RULES = """
cloth(blue). cloth(red). cloth(yellow).
magic(yes).
works(yes) :- cloth(_), magic(yes).
quiet(yes) :- works(yes).
#show works/1.
#show quiet/1.
"""


def asp_facts():
    from asp import fact
    return "\n".join(fact("cloth", color) for color in COLORS) + "\n" + fact("magic", "yes")


def verify():
    from asp import atoms, one_model
    model = one_model(asp_facts() + "\n" + ASP_RULES)
    if set(atoms(model, "works")) != {("yes",)}:
        raise StoryError("ASP does not permit magic gingham.")
    if set(atoms(model, "quiet")) != {("yes",)}:
        raise StoryError("ASP does not prove a quiet nursery.")
    for color in COLORS:
        for size in SIZES:
            p = StoryParams(color=color, size=size)
            w = simulate(p)
            validate_world(w)
            story, qa = render(w)
            if "gingham" not in story or len(qa) < 2:
                raise StoryError("Generated prose lost the seed word or QA.")
    print("OK: gingham magic nursery rhyme cases verified.")


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    validate_world(world)
    story, qa = render(world)
    return StorySample(
        params=params,
        story=story,
        prompts=[
            f"Write a nursery rhyme about {params.hero}, a magic {params.color} gingham cloth, and a sleepy mouse."
        ],
        story_qa=qa,
        world_qa=[
            QAItem(
                "What kind of cloth belongs in this world?",
                "Gingham is a checked cloth that can become magical in the nursery rhyme.",
            ),
            QAItem(
                "What does a bedtime spell do?",
                "A bedtime spell turns a noisy, worried nursery into a quiet place for sleep.",
            ),
        ],
        world=world,
    )


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--hero")
    parser.add_argument("--color", choices=COLORS)
    parser.add_argument("--size", choices=SIZES)
    parser.add_argument("--voice", choices=VOICES, default="bouncy")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args, index=0, sample=False):
    rng = random.Random(args.seed + index)
    return StoryParams(
        hero=args.hero or "Nell",
        color=args.color or (rng.choice(COLORS) if sample else "blue"),
        size=args.size or (rng.choice(SIZES) if sample else "small"),
        voice=args.voice,
        world_seed=args.seed + index,
        prose_seed=args.prose_seed + index,
    )


def emit(sample: StorySample, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(
            json.dumps(
                {
                    "world": {
                        "entities": {
                            key: asdict(value) for key, value in sample.world.entities.items()
                        },
                        "outcome": sample.world.outcome,
                    },
                    "history": [asdict(event) for event in sample.world.history],
                },
                indent=2,
            )
        )


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            from asp import atoms, one_model
            print(json.dumps(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "quiet")))
            return 0

        if args.all:
            params = [
                resolve_params(
                    argparse.Namespace(
                        **{
                            **vars(args),
                            "color": color,
                            "size": size,
                        }
                    ),
                    index,
                    False,
                )
                for index, (color, size) in enumerate(
                    (color, size) for color in COLORS for size in SIZES
                )
            ]
        else:
            params = [resolve_params(args, i, args.n > 1) for i in range(args.n)]

        samples = [generate(p) for p in params]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload, ensure_ascii=False, indent=2))
        else:
            for i, sample in enumerate(samples):
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {i + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
