#!/usr/bin/env python3
"""A gentle bedtime story about sharing a nose and noticing small clues."""

from __future__ import annotations

import argparse
import itertools
import json
import random
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


NAMES = ("Nell", "Milo", "Lina", "Tess")
ANIMALS = ("rabbit", "bear", "fox")
TREATS = ("honeycake", "apple", "berry_bun")
COLORS = ("red", "blue", "yellow")
VOICES = ("tender", "plain", "playful")
MAX_STEPS = 12


@dataclass
class StoryParams:
    hero: str = "Nell"
    animal: str = "rabbit"
    treat: str = "honeycake"
    color: str = "red"
    voice: str = "tender"
    world_seed: int = 777
    prose_seed: int = 42


@dataclass
class Entity:
    id: str
    label: str
    location: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Event:
    id: int
    kind: str
    actor: str
    data: dict
    facts: tuple[str, ...]
    causes: tuple[int, ...]
    state: dict


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.facts: dict[str, int] = {}
        self.outcome = ""

    def snapshot(self):
        return {
            "entities": {key: asdict(value) for key, value in self.entities.items()},
            "outcome": self.outcome,
        }

    def record(self, kind, actor, *, facts=(), needs=(), **data):
        missing = [fact for fact in needs if fact not in self.facts]
        if missing:
            raise StoryError(f"{kind} needs an earlier clue: {', '.join(missing)}.")
        causes = tuple(sorted({self.facts[fact] for fact in needs}))
        event = Event(
            id=len(self.history),
            kind=kind,
            actor=actor,
            data=data,
            facts=tuple(facts),
            causes=causes,
            state=self.snapshot(),
        )
        self.history.append(event)
        for fact in facts:
            self.facts[fact] = event.id


def validate_params(p: StoryParams):
    for value, choices, label in (
        (p.hero, NAMES, "hero"),
        (p.animal, ANIMALS, "animal"),
        (p.treat, TREATS, "treat"),
        (p.color, COLORS, "color"),
        (p.voice, VOICES, "voice"),
    ):
        if value not in choices:
            raise StoryError(f"Unknown {label}: {value!r}.")
    if type(p.world_seed) is not int or type(p.prose_seed) is not int:
        raise StoryError("Seeds must be integers.")


def build_world(p: StoryParams) -> World:
    validate_params(p)
    w = World(p)
    w.entities = {
        "hero": Entity("hero", p.hero, "bedroom", memes={"kindness": 1}),
        "friend": Entity(
            "friend",
            f"the little {p.animal}",
            "hall",
            memes={"worry": 1, "comfort": 0},
        ),
        "treat": Entity(
            "treat",
            f"the {p.treat}",
            "kitchen",
            owner="hero",
            meters={"pieces": 2},
        ),
        "nose": Entity(
            "nose",
            "the small red nose",
            "friend",
            owner="friend",
            meters={"warmth": 1},
        ),
        "blanket": Entity(
            "blanket",
            "the blue blanket",
            "bedroom",
            owner="hero",
            meters={"warmth": 2},
        ),
        "window": Entity("window", "the window", "bedroom", meters={"open": 0}),
        "moon": Entity("moon", "the moon", "sky"),
    }
    w.record(
        "opening",
        "hero",
        facts=("bedtime_begun",),
        hero=p.hero,
        animal=p.animal,
        treat=p.treat,
    )
    return w


def choose_action(w: World):
    if w.outcome:
        return "close"
    if "kindness_seen" not in w.facts:
        return "notice"
    if "shared_treat" not in w.facts:
        return "share_treat"
    if "window_opened" not in w.facts:
        return "open_window"
    if "nose_warmed" not in w.facts:
        return "warm_nose"
    if "friend_comforted" not in w.facts:
        return "share_blanket"
    return "sleep"


def execute(w: World, action: str):
    p = w.params
    hero = w.entities["hero"]
    friend = w.entities["friend"]
    treat = w.entities["treat"]
    nose = w.entities["nose"]
    blanket = w.entities["blanket"]
    window = w.entities["window"]

    if action == "notice":
        if friend.memes["worry"] <= 0:
            raise StoryError("There is no worry left to notice.")
        hero.memes["kindness"] += 1
        w.record(
            "notice",
            "hero",
            facts=("kindness_seen",),
            needs=("bedtime_begun",),
            clue="cold nose",
        )
    elif action == "share_treat":
        if treat.meters["pieces"] < 2:
            raise StoryError("The treat must have enough pieces to share.")
        treat.meters["pieces"] -= 1
        friend.memes["worry"] -= 0.4
        friend.memes["comfort"] += 0.5
        w.record(
            "share_treat",
            "hero",
            facts=("shared_treat",),
            needs=("kindness_seen",),
            treat=p.treat,
        )
    elif action == "open_window":
        if "shared_treat" not in w.facts:
            raise StoryError("The friend should be welcomed before the window opens.")
        window.meters["open"] = 1
        w.record(
            "open_window",
            "hero",
            facts=("window_opened",),
            needs=("shared_treat",),
        )
    elif action == "warm_nose":
        if window.meters["open"] != 1:
            raise StoryError("The chilly nose needs the open window to be understood.")
        nose.location = "blanket"
        nose.meters["warmth"] = 2
        friend.memes["worry"] -= 0.4
        friend.memes["comfort"] += 0.6
        w.record(
            "warm_nose",
            "hero",
            facts=("nose_warmed",),
            needs=("window_opened",),
        )
    elif action == "share_blanket":
        if nose.location != "blanket":
            raise StoryError("The blanket is needed to warm the nose.")
        blanket.owner = "shared"
        friend.location = "bedroom"
        friend.memes["worry"] = 0
        friend.memes["comfort"] = 1
        w.record(
            "share_blanket",
            "hero",
            facts=("friend_comforted",),
            needs=("nose_warmed",),
        )
    elif action == "sleep":
        if "friend_comforted" not in w.facts:
            raise StoryError("Nobody is ready for sleep yet.")
        w.outcome = "shared_rest"
        friend.location = "bedroom"
        w.record(
            "sleep",
            "friend",
            facts=("rest_begun",),
            needs=("friend_comforted",),
        )
    elif action == "close":
        if w.outcome != "shared_rest":
            raise StoryError("The bedtime ending needs shared rest.")
        w.record(
            "close",
            "hero",
            facts=("ending",),
            needs=("rest_begun",),
        )
    else:
        raise StoryError(f"Unknown action {action!r}.")


def validate_world(w: World):
    if w.outcome != "shared_rest" or "ending" not in w.facts:
        raise StoryError("The story must end with safe shared rest.")
    if w.entities["nose"].meters["warmth"] < 2:
        raise StoryError("The nose was not warmed.")
    if w.entities["friend"].memes["worry"] != 0:
        raise StoryError("The friend's worry was not settled.")
    for event in w.history:
        if any(parent >= event.id for parent in event.causes):
            raise StoryError("An event cannot depend on a future clue.")


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    for _ in range(MAX_STEPS):
        execute(w, choose_action(w))
        if "ending" in w.facts:
            validate_world(w)
            return w
    raise StoryError("The bedtime plan did not reach its ending.")


class Teller:
    def __init__(self, world: World):
        self.world = world
        self.p = world.params
        self.rng = random.Random(self.p.prose_seed)
        self.lines: list[str] = []
        self.qa: list[QAItem] = []

    def pick(self, *choices):
        return self.rng.choice(choices).format(
            hero=self.p.hero,
            animal=self.p.animal,
            treat=self.p.treat,
        )

    def tell(self, *choices):
        self.lines.append(self.pick(*choices))

    def render(self):
        for event in self.world.history:
            self.event(event)
        return "\n\n".join(self.lines), self.qa

    def event(self, event: Event):
        k = event.kind
        p = self.p
        if k == "opening":
            self.tell(
                "When the stars came out, {hero} was getting ready for bed.",
                "The house grew quiet, and {hero} began to turn down the blankets.",
            )
            self.tell(
                "A little {animal} stood at the bedroom door, holding a small red nose in the cold air.",
                "At the door waited a little {animal}. Its tiny red nose trembled in the evening chill.",
            )
            self.qa.append(
                QAItem(
                    "Who came to the bedroom at bedtime?",
                    f"A little {p.animal} came to {p.hero}'s bedroom.",
                )
            )
        elif k == "notice":
            self.tell(
                "{hero} noticed the trembling nose before the {animal} said a word.",
                "The little {animal} tried to smile, but {hero} saw that its small red nose was cold.",
            )
            self.tell(
                "Sometimes the quietest shiver is a question waiting to be heard.",
                "A tiny shiver can say, 'Please notice me,' even when no one speaks.",
            )
            self.qa.append(
                QAItem(
                    "What did the hero notice?",
                    f"{p.hero} noticed that the {p.animal}'s small red nose was cold and trembling.",
                )
            )
        elif k == "share_treat":
            self.tell(
                "{hero} broke the {treat} in two and gave one piece to the {animal}.",
                "{hero} shared the {treat}, saving one piece and offering the other to the little visitor.",
            )
            self.tell(
                "The warm sweetness made the room feel less lonely.",
                "After the first bite, the little {animal} sat a little closer.",
            )
            self.qa.append(
                QAItem(
                    "What did the hero share?",
                    f"{p.hero} shared a piece of the {p.treat} with the {p.animal}.",
                )
            )
        elif k == "open_window":
            self.tell(
                "{hero} opened the window just a little. Moonlight slipped across the floor.",
                "A small opening let the moon shine in without letting the night rush inside.",
            )
            self.tell(
                "Far away, a night bird called, as if it knew that someone would soon need a warm place.",
                "The night bird's call floated past the window, soft and low.",
            )
        elif k == "warm_nose":
            self.tell(
                "{hero} tucked the little red nose beneath the blue blanket.",
                "{hero} made a warm fold in the blanket and invited the tiny nose to rest there.",
            )
            self.tell(
                "The nose grew warm, and the {animal}'s worried eyes began to shine with relief.",
                "Soon the small red nose was cozy beneath the blanket, and the {animal} sighed happily.",
            )
            self.qa.append(
                QAItem(
                    "How did the hero warm the nose?",
                    f"{p.hero} tucked the {p.animal}'s small red nose beneath the blue blanket.",
                )
            )
        elif k == "share_blanket":
            self.tell(
                "There was room for two, so {hero} shared the blanket too.",
                "{hero} lifted the blanket and made a place beside them.",
            )
            self.tell(
                "The {animal} curled up close, its nose warm against the soft cloth.",
                "The little {animal} settled beside {hero}, warm from nose to tail.",
            )
            self.qa.append(
                QAItem(
                    "What else did the hero share?",
                    f"{p.hero} shared the blue blanket so the {p.animal} could rest warmly.",
                )
            )
        elif k == "sleep":
            self.tell(
                "The room grew still. The moon watched over two quiet sleepers.",
                "Under the moonlight, two gentle breaths began to rise and fall together.",
            )
        elif k == "close":
            self.tell(
                "And whenever {hero} heard a small shiver after that, there was always room beneath the blanket.",
                "From that night on, {hero} remembered that sharing warmth could make even a dark night feel kind.",
            )
            self.qa.append(
                QAItem(
                    "What changed by the end of the story?",
                    f"{p.hero} and the {p.animal} rested safely together, and the little nose was warm.",
                )
            )


ASP_RULES = """
can_share_treat :- pieces(2).
can_open_window :- shared_treat.
can_warm_nose :- window_opened.
can_share_blanket :- nose_warmed.
can_sleep :- friend_comforted.
#show can_share_treat/0.
#show can_open_window/0.
#show can_warm_nose/0.
#show can_share_blanket/0.
#show can_sleep/0.
"""


def asp_facts():
    from asp import fact

    return "\n".join(
        [
            fact("pieces", 2),
            fact("shared_treat"),
            fact("window_opened"),
            fact("nose_warmed"),
            fact("friend_comforted"),
        ]
    )


def asp_status():
    from asp import atoms, one_model

    return atoms(one_model(asp_facts() + "\n" + ASP_RULES), "can_sleep")


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    story, qa = Teller(world).render()
    return StorySample(
        params=params,
        story=story,
        prompts=[
            f"Write a gentle bedtime story about {params.hero} sharing warmth with a little {params.animal}."
        ],
        story_qa=qa,
        world_qa=[
            QAItem(
                "Why can sharing help someone feel better?",
                "Sharing food, warmth, or space can help a worried friend feel safe and cared for.",
            )
        ],
        world=world,
    )


def verify():
    if not asp_status():
        raise StoryError("ASP did not find a complete bedtime path.")
    for hero, animal, treat in itertools.product(NAMES, ANIMALS, TREATS):
        sample = generate(
            StoryParams(hero=hero, animal=animal, treat=treat, prose_seed=91)
        )
        if "nose" not in sample.story.lower():
            raise StoryError("The generated story lost the nose seed word.")
        validate_world(sample.world)
    print("OK: sharing, foreshadowing, bedtime resolution, and ASP parity.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--treat", choices=TREATS)
    parser.add_argument("--color", choices=COLORS)
    parser.add_argument("--voice", choices=VOICES, default="tender")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args, rng, index=0, sample=False):
    p = StoryParams(
        world_seed=args.world_seed + index,
        prose_seed=args.prose_seed + index,
        voice=args.voice,
    )
    choices = {
        "hero": NAMES,
        "animal": ANIMALS,
        "treat": TREATS,
        "color": COLORS,
    }
    for name, values in choices.items():
        supplied = getattr(args, name)
        setattr(
            p,
            name,
            supplied if supplied is not None else rng.choice(values) if sample else getattr(p, name),
        )
    validate_params(p)
    return p


def emit(sample, *, trace=False, qa=False, header=""):
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
                    "state": sample.world.snapshot(),
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
            print(json.dumps(asp_status()))
            return 0

        rng = random.Random(args.world_seed)
        if args.all:
            params = []
            for hero, animal, treat in itertools.product(NAMES, ANIMALS, TREATS):
                if args.hero and args.hero != hero:
                    continue
                if args.animal and args.animal != animal:
                    continue
                if args.treat and args.treat != treat:
                    continue
                params.append(
                    StoryParams(
                        hero=hero,
                        animal=animal,
                        treat=treat,
                        color=args.color or COLORS[0],
                        voice=args.voice,
                        world_seed=args.world_seed + len(params),
                        prose_seed=args.prose_seed + len(params),
                    )
                )
        else:
            params = [
                resolve_params(args, rng, index, sample=args.n > 1)
                for index in range(args.n)
            ]

        if args.json:
            rows = [generate(p).to_dict() for p in params]
            print(json.dumps(rows[0] if len(rows) == 1 else rows, ensure_ascii=False, indent=2))
        else:
            for index, params_item in enumerate(params):
                emit(
                    generate(params_item),
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n" if len(params) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
