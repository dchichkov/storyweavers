#!/usr/bin/env python3
"""A tiny gingham nursery-rhyme world about a bit of magic that must be shared."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import itertools
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


HEROES = ("Nell", "Mina", "Pip")
COLORS = ("blue", "red", "yellow")
HELPERS = ("moon", "robin", "teapot")
PLACES = ("garden", "kitchen", "hill")
MAX_STEPS = 12


@dataclass
class StoryParams:
    hero: str = "Nell"
    color: str = "blue"
    helper: str = "moon"
    place: str = "garden"
    magic: str = "mending"
    world_seed: int = 777
    prose_seed: int = 42


@dataclass
class Entity:
    id: str
    label: str
    location: str
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


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.rng = random.Random(params.world_seed)
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.facts: dict[str, int] = {}
        self.outcome = ""

    def record(self, kind, actor, facts=(), needs=(), **data):
        if any(item not in self.facts for item in needs):
            raise StoryError(f"{kind} needs an earlier part of the tale.")
        causes = tuple(sorted({self.facts[item] for item in needs}))
        event = Event(len(self.history), kind, actor, data, tuple(facts), causes)
        self.history.append(event)
        for item in facts:
            self.facts[item] = event.id


def validate_params(p: StoryParams):
    if p.hero not in HEROES:
        raise StoryError("Choose a known nursery-rhyme child.")
    if p.color not in COLORS:
        raise StoryError("Choose blue, red, or yellow gingham.")
    if p.helper not in HELPERS:
        raise StoryError("Choose the moon, a robin, or a teapot as helper.")
    if p.place not in PLACES:
        raise StoryError("Choose the garden, kitchen, or hill.")
    if p.magic != "mending":
        raise StoryError("This little world knows only mending magic.")
    if type(p.world_seed) is not int or type(p.prose_seed) is not int:
        raise StoryError("Seeds must be integers.")


def build_world(p: StoryParams) -> World:
    validate_params(p)
    w = World(p)
    w.entities = {
        "child": Entity("child", p.hero, p.place, memes={"kindness": 1}),
        "cloth": Entity("cloth", f"{p.color} gingham cloth", p.place,
                        meters={"pieces": 1, "magic": 1}, memes={"hope": 1}),
        "basket": Entity("basket", "the little basket", p.place,
                         meters={"holes": 1, "strength": 0}),
        "helper": Entity("helper", f"the {p.helper}", "nearby",
                         memes={"patience": 1}),
        "wind": Entity("wind", "the wandering wind", p.place,
                       meters={"strength": 1}),
        "crumb": Entity("crumb", "a warm seed cake", p.place),
    }
    w.record("opening", "child", facts=("problem_seen",), place=p.place,
             color=p.color, helper=p.helper)
    return w


def choose_action(w: World) -> str:
    if w.outcome:
        return "close"
    if "help_called" not in w.facts:
        return "call_help"
    if "cloth_lifted" not in w.facts:
        return "catch_cloth"
    if "cloth_ready" not in w.facts:
        return "fold_cloth"
    if "basket_mended" not in w.facts:
        return "mend_basket"
    return "share_crumb"


def execute(w: World, action: str):
    p = w.params
    child = w.entities["child"]
    cloth = w.entities["cloth"]
    basket = w.entities["basket"]

    if action == "call_help":
        w.record("call_help", "child", facts=("help_called",),
                 needs=("problem_seen",), helper=p.helper)
    elif action == "catch_cloth":
        if "help_called" not in w.facts:
            raise StoryError("The helper must be called before the cloth can be caught.")
        cloth.location = "hands"
        w.record("catch_cloth", "helper", facts=("cloth_lifted",),
                 needs=("help_called",), helper=p.helper)
    elif action == "fold_cloth":
        if cloth.location != "hands":
            raise StoryError("The gingham must be caught before it can be folded.")
        cloth.meters["magic"] = 2
        w.record("fold_cloth", "child", facts=("cloth_ready",),
                 needs=("cloth_lifted",), color=p.color)
    elif action == "mend_basket":
        if cloth.meters["magic"] < 2:
            raise StoryError("The magic gingham is not ready to mend the basket.")
        basket.meters.update(holes=0, strength=1)
        cloth.meters["pieces"] = 0
        w.record("mend_basket", "child", facts=("basket_mended",),
                 needs=("cloth_ready",), color=p.color)
    elif action == "share_crumb":
        if basket.meters["holes"] != 0:
            raise StoryError("The basket must be mended before it can carry the cake.")
        w.entities["crumb"].location = "basket"
        w.outcome = "shared"
        w.record("share_crumb", "child", facts=("kindness_complete",),
                 needs=("basket_mended",))
    elif action == "close":
        if w.outcome != "shared":
            raise StoryError("The tale is not ready to close.")
        w.record("close", "child", facts=("ending",),
                 needs=("kindness_complete",))


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    for _ in range(MAX_STEPS):
        execute(w, choose_action(w))
        if "ending" in w.facts:
            return w
    raise StoryError("The nursery rhyme did not reach its ending.")


def validate_world(w: World):
    if "ending" not in w.facts or w.outcome != "shared":
        raise StoryError("The ending must show kindness completed.")
    if w.entities["basket"].meters["holes"] != 0:
        raise StoryError("The basket must be whole at the end.")
    if w.entities["crumb"].location != "basket":
        raise StoryError("The seed cake must reach the mended basket.")


class Teller:
    def __init__(self, world: World):
        self.world = world
        self.p = world.params
        self.rng = random.Random(self.p.prose_seed)
        self.qa: list[QAItem] = []
        self.lines: list[str] = []

    def tell(self, *choices):
        self.lines.append(self.rng.choice(choices).format(
            hero=self.p.hero, color=self.p.color, helper=self.p.helper,
            place=self.p.place))

    def run(self):
        for event in self.world.history:
            self.render(event)
        validate_world(self.world)
        return "\n\n".join(self.lines)

    def render(self, event: Event):
        p = self.p
        if event.kind == "opening":
            self.tell(
                "In a {place} bright and wide, {hero} found a basket with a hole in its side.",
                "By the {place} gate, where the soft breezes blew, {hero} found a basket that leaked right through.",
            )
            self.tell(
                "Beside it lay a square of {color} gingham, neat as a song and soft as a wing.",
                "A {color} gingham cloth lay near, waiting for a little magic to appear."
            )
            self.qa.append(QAItem(
                "What was wrong with the basket?",
                "The basket had a hole, so it could not safely carry the seed cake."
            ))
        elif event.kind == "call_help":
            self.tell(
                "{hero} clapped twice: “{helper}, dear, come here! Bring a pinch of magic near!”",
                "{hero} sang, “Come, {helper}, come, for the basket is undone!”"
            )
        elif event.kind == "catch_cloth":
            self.tell(
                "The {helper} gave a twinkling puff, and up flew the gingham, light enough.",
                "A silver breeze from the {helper} lifted the cloth and set it in {hero}'s hands."
            )
            self.qa.append(QAItem(
                "Who helped lift the gingham?",
                f"The {p.helper} helped lift the gingham with a little magical breeze."
            ))
        elif event.kind == "fold_cloth":
            self.tell(
                "{hero} folded it once, folded it twice, and whispered, “Mend it nice.”",
                "Fold over fold, with a whispered rhyme, the gingham gathered magic in time."
            )
        elif event.kind == "mend_basket":
            self.tell(
                "The gingham flashed blue, and the hole was gone; the basket stood whole in the dawn.",
                "With a shimmer and shine, the gingham made the basket fine."
            )
            self.qa.append(QAItem(
                "How was the basket mended?",
                f"{hero_name(p)} folded the {p.color} gingham and used its magic to close the hole."
            ))
        elif event.kind == "share_crumb":
            self.tell(
                "{hero} placed the seed cake inside. “A whole basket makes sharing a breeze!”",
                "In went the warm seed cake, safe and snug, while the {helper} gave a happy hug."
            )
        elif event.kind == "close":
            self.tell(
                "So round went the cake, and round went the cheer: a little mending brought kindness near.",
                "The basket held the cake, the friends held hands, and magic danced through the nursery lands."
            )
            self.qa.append(QAItem(
                "What changed by the end?",
                "The hole was mended, the basket held the seed cake, and the friends could share it safely."
            ))


def hero_name(p: StoryParams) -> str:
    return p.hero


ASP_RULES = """
ok :- problem(hole), magic(mending), helper.
fixed :- ok.
#show ok/0.
#show fixed/0.
"""


def asp_facts():
    from asp import fact
    return "\n".join([
        fact("problem", "hole"),
        fact("magic", "mending"),
        fact("helper"),
    ])


def asp_status():
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "fixed"))


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    story = Teller(world).run()
    qa = Teller(world).qa if False else []
    teller = Teller(world)
    story = teller.run()
    return StorySample(
        params=params,
        story=story,
        prompts=[f"Write a nursery rhyme about {params.hero} mending a basket with magic gingham."],
        story_qa=teller.qa,
        world_qa=[
            QAItem("What is gingham?", "Gingham is a woven cloth with a simple checked pattern."),
            QAItem("What does mending do?", "Mending repairs something so it can be used again."),
        ],
        world=world,
    )


def verify():
    if asp_status() != {()}:
        raise StoryError("The ASP twin did not find the mending plan.")
    count = 0
    for hero, color, helper, place in itertools.product(HEROES, COLORS, HELPERS, PLACES):
        p = StoryParams(hero=hero, color=color, helper=helper, place=place)
        sample = generate(p)
        if "gingham" not in sample.story.lower() or "basket" not in sample.story.lower():
            raise StoryError("A generated rhyme lost its gingham or basket.")
        count += 1
    print(f"OK: {count} nursery-rhyme configurations; ASP parity.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--color", choices=COLORS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args, rng, index=0, sample=False):
    p = StoryParams(world_seed=args.world_seed + index,
                    prose_seed=args.prose_seed + index)
    for name, values in (
        ("hero", HEROES), ("color", COLORS), ("helper", HELPERS), ("place", PLACES)
    ):
        value = getattr(args, name)
        setattr(p, name, value if value is not None else
                rng.choice(values) if sample else getattr(p, name))
    validate_params(p)
    return p


def emit(sample, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "history": [asdict(event) for event in sample.world.history],
            "outcome": sample.world.outcome,
        }, indent=2))


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
            print(json.dumps(sorted(asp_status())))
            return 0

        rng = random.Random(args.world_seed)
        if args.all:
            params = [
                StoryParams(hero=hero, color=color, helper=helper, place=place,
                            world_seed=args.world_seed + i, prose_seed=args.prose_seed + i)
                for i, (hero, color, helper, place)
                in enumerate(itertools.product(HEROES, COLORS, HELPERS, PLACES))
            ]
        else:
            params = [
                resolve_params(args, rng, index, sample=args.n > 1)
                for index in range(args.n)
            ]

        if args.json:
            rows = [generate(p).to_dict() for p in params]
            print(json.dumps(rows[0] if len(rows) == 1 else rows,
                             ensure_ascii=False, indent=2))
        else:
            for index, params_item in enumerate(params):
                emit(generate(params_item), trace=args.trace, qa=args.qa,
                     header=f"\n### Story {index + 1}\n" if len(params) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
