#!/usr/bin/env python3
"""A tiny heartwarming storyworld about a town's surprising craze."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import itertools
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


CRAZES = ("paper_hats", "puddle_dancing", "whistling_kettles")
HEROES = ("Nell", "Mara", "Tess")
HELPERS = ("Grandma June", "Uncle Pip", "Mr. Vale")
VOICES = ("gentle", "playful", "plain")
MAX_ACTIONS = 16


@dataclass
class StoryParams:
    hero: str = "Nell"
    craze: str = "paper_hats"
    helper: str = "Grandma June"
    voice: str = "gentle"
    world_seed: int = 777
    prose_seed: int = 42


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    location: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Event:
    id: int
    kind: str
    actor: str
    data: dict
    facts: tuple[str, ...]
    causes: tuple[int, ...]
    state: dict


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity]
    history: list[Event] = field(default_factory=list)
    facts: dict[str, int] = field(default_factory=dict)
    outcome: str = ""

    def snapshot(self):
        return {
            "entities": {key: asdict(value) for key, value in self.entities.items()},
            "outcome": self.outcome,
        }

    def record(self, kind, actor, *, facts=(), needs=(), **data):
        if any(item not in self.facts for item in needs):
            raise StoryError(f"{kind} needs an earlier fact.")
        causes = tuple(sorted({self.facts[item] for item in needs}))
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
        for item in facts:
            self.facts[item] = event.id


def validate_params(p: StoryParams):
    if p.craze not in CRAZES:
        raise StoryError(f"Unknown craze: {p.craze!r}.")
    if p.hero not in HEROES:
        raise StoryError(f"Unknown hero: {p.hero!r}.")
    if p.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {p.helper!r}.")
    if p.voice not in VOICES:
        raise StoryError(f"Unknown voice: {p.voice!r}.")
    if type(p.world_seed) is not int or type(p.prose_seed) is not int:
        raise StoryError("Seeds must be integers.")


def craze_info(craze):
    return {
        "paper_hats": {
            "thing": "paper hats",
            "singular": "paper hat",
            "material": "old newspapers",
            "place": "the market square",
            "surprise": "a tiny blue bird was nesting inside the largest hat",
        },
        "puddle_dancing": {
            "thing": "puddle dancing",
            "singular": "puddle dance",
            "material": "rain boots",
            "place": "the lane behind the bakery",
            "surprise": "the puddle reflected a lost child's red kite",
        },
        "whistling_kettles": {
            "thing": "whistling kettles",
            "singular": "whistling kettle",
            "material": "a dented tin kettle",
            "place": "the community kitchen",
            "surprise": "one kettle whistled the tune of an old lullaby",
        },
    }[craze]


def build_world(p: StoryParams) -> World:
    validate_params(p)
    info = craze_info(p.craze)
    entities = {
        "hero": Entity(
            "hero", p.hero, "character", info["place"],
            memes={"curiosity": 1.0, "kindness": 0.8},
            beliefs={"craze": p.craze},
        ),
        "helper": Entity(
            "helper", p.helper, "character", info["place"],
            memes={"warmth": 1.0, "worry": 0.3},
        ),
        "crowd": Entity(
            "crowd", "the neighbors", "group", info["place"],
            memes={"excitement": 1.0},
        ),
        "object": Entity(
            "object", info["singular"], "thing", info["place"],
            meters={"size": 1, "fragility": 0.4},
        ),
        "surprise": Entity(
            "surprise", info["surprise"], "thing", "hidden",
            meters={"visible": 0},
        ),
    }
    world = World(p, entities)
    world.record(
        "opening",
        "hero",
        facts=("craze_seen", "helper_present"),
        craze=p.craze,
        place=info["place"],
        thing=info["thing"],
    )
    return world


def choose_action(w: World):
    if "ending" in w.facts:
        return "close"
    if "surprise_seen" in w.facts and "heart_shared" not in w.facts:
        return "share"
    if "clue_noticed" not in w.facts:
        return "notice"
    if "surprise_seen" not in w.facts:
        return "look_inside"
    return "comfort"


def execute(w: World, action: str):
    p = w.params
    info = craze_info(p.craze)
    if action == "notice":
        w.entities["hero"].beliefs["clue"] = "something is hidden"
        w.record(
            "notice",
            "hero",
            facts=("clue_noticed",),
            needs=("craze_seen",),
            clue=info["surprise"],
        )
    elif action == "look_inside":
        w.entities["surprise"].location = info["place"]
        w.entities["surprise"].meters["visible"] = 1
        w.entities["hero"].beliefs["surprise"] = info["surprise"]
        w.record(
            "look_inside",
            "hero",
            facts=("surprise_seen",),
            needs=("clue_noticed",),
            surprise=info["surprise"],
        )
    elif action == "share":
        w.entities["crowd"].memes["excitement"] = 1.2
        w.entities["helper"].memes["worry"] = 0.0
        w.record(
            "share",
            "hero",
            facts=("heart_shared",),
            needs=("surprise_seen",),
            news=info["surprise"],
        )
    elif action == "comfort":
        w.entities["helper"].beliefs["memory"] = "the old tune"
        w.entities["hero"].memes["kindness"] = 1.0
        w.record(
            "comfort",
            "hero",
            facts=("comfort_given",),
            needs=("surprise_seen",),
        )
    elif action == "close":
        w.outcome = "community_delighted"
        w.entities["hero"].location = "homeward_path"
        w.entities["helper"].location = "homeward_path"
        w.record(
            "close",
            "hero",
            facts=("ending",),
            needs=("heart_shared",),
            outcome=w.outcome,
        )
    else:
        raise StoryError(f"Unknown action {action!r}.")


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    for _ in range(MAX_ACTIONS):
        execute(w, choose_action(w))
        if "ending" in w.facts:
            validate_world(w)
            return w
    raise StoryError("The craze story did not reach an ending.")


def validate_world(w: World):
    if w.outcome != "community_delighted":
        raise StoryError("The community must end delighted.")
    if "surprise_seen" not in w.facts or "heart_shared" not in w.facts:
        raise StoryError("The surprise and its kind sharing are required.")
    for event in w.history:
        if any(parent >= event.id for parent in event.causes):
            raise StoryError("An event cannot depend on the future.")


class Teller:
    def __init__(self, world: World):
        self.w = world
        self.p = world.params
        self.rng = random.Random(self.p.prose_seed)
        self.info = craze_info(self.p.craze)
        self.parts = []
        self.qa = []

    def add(self, *choices):
        self.parts.append(self.rng.choice(choices))

    def dialogue(self, lines):
        for speaker, words in self.rng.choice(lines):
            name = self.p.hero if speaker == "hero" else self.p.helper
            self.parts.append(f'"{words}" {name} said.')

    def render(self):
        for event in self.w.history:
            k = event.kind
            if k == "opening":
                self.add(
                    f"In {self.info['place']}, everyone had caught the craze for {self.info['thing']}.",
                    f"The whole town was swept up in a craze for {self.info['thing']} at {self.info['place']}.",
                )
                self.dialogue((
                    (("helper", f'"Have you joined the {self.info["thing"]} craze yet?"'),
                      ("hero", '"I am still investigating it."')),
                    (("helper", '"The town is having such fun."'),
                      ("hero", '"Then I should look closely."')),
                ))
                self.parts[-2:] = [
                    self.parts[-2].replace('""', '"'),
                    self.parts[-1].replace('""', '"'),
                ]
                self.add(
                    f"{self.p.hero} laughed, but the {self.info['singular']} beside {self.p.helper} made her pause.",
                    f"{self.p.hero} smiled at the silly craze. Then she noticed that {self.p.helper} was watching one object very carefully.",
                )
                self.qa.append(QAItem(
                    f"Where did the {self.info['thing']} craze happen?",
                    f"It happened at {self.info['place']}, where the neighbors gathered to enjoy {self.info['thing']}.",
                ))
            elif k == "notice":
                self.add(
                    f"A corner of the {self.info['singular']} bulged in an odd way.",
                    f"{self.p.hero} spotted a small clue: something inside the {self.info['singular']} was breathing softly.",
                )
                self.dialogue((
                    (("hero", '"Did that move?"'), ("helper", '"I hoped you would notice."')),
                    (("hero", '"There is something inside."'), ("helper", '"Something that needs a gentle look."')),
                ))
                self.qa.append(QAItem(
                    "What clue did the hero notice?",
                    f"The {self.info['singular']} bulged and seemed to hide something breathing inside it.",
                ))
            elif k == "look_inside":
                self.add(
                    f"Very slowly, {self.p.hero} lifted the edge and found {self.info['surprise']}.",
                    f"Under the {self.info['singular']} was a surprise: {self.info['surprise']}.",
                )
                self.dialogue((
                    (("hero", '"Oh! We must not frighten it."'), ("helper", '"That is why I waited for you."')),
                    (("hero", '"The craze can pause."'), ("helper", '"Kindness cannot."')),
                ))
                self.qa.append(QAItem(
                    "What surprising thing was discovered?",
                    f"They discovered that {self.info['surprise']}.",
                ))
            elif k == "share":
                self.add(
                    f"{self.p.hero} told the neighbors, and the noisy craze became a quiet circle of care.",
                    f"The neighbors gathered around, but nobody reached or shouted. They made room for the surprise.",
                )
                self.qa.append(QAItem(
                    "How did the hero change the crowd's behavior?",
                    f"{self.p.hero} shared the discovery and helped the neighbors turn their excitement into a careful, quiet circle.",
                ))
            elif k == "comfort":
                self.add(
                    f"{self.p.helper} smiled with wet eyes, and {self.p.hero} held {self.p.helper}'s hand.",
                    f"For a moment, the craze mattered less than the warm feeling of looking after something small.",
                )
            elif k == "close":
                self.add(
                    f"By sunset, the town still loved its craze, but everyone remembered the hidden little wonder first.",
                    f"They walked home together while the neighbors whispered happily. The craze had brought them laughter; kindness had given the day its heart.",
                )
                self.dialogue((
                    (("helper", '"Will you join the craze tomorrow?"'), ("hero", '"Only if we look carefully again."')),
                    (("helper", '"Was today a success?"'), ("hero", '"The happiest kind."')),
                ))
                self.add(
                    f"{self.p.hero} and {self.p.helper} went home smiling, carrying no trophy except a story they would tell with care.",
                    f"That evening, {self.p.hero} understood that a craze could fill a square, but one gentle surprise could fill a heart.",
                )
                self.qa.append(QAItem(
                    "What changed by the end of the story?",
                    f"The neighbors stayed joyful, but they learned to put care before excitement when they discovered {self.info['surprise']}.",
                ))
        return StorySample(
            params=self.p,
            story="\n\n".join(self.parts),
            prompts=[f"Write a heartwarming story about a town craze for {self.info['thing']} with a humorous surprise."],
            story_qa=self.qa,
            world_qa=[
                QAItem(
                    "What makes a craze safe and kind?",
                    "People can enjoy a shared activity while still noticing when someone or something needs care.",
                )
            ],
            world=self.w,
        )


ASP_RULES = """
craze(paper_hats).
craze(puddle_dancing).
craze(whistling_kettles).
has_surprise(C) :- craze(C).
can_end(C) :- has_surprise(C).
#show craze/1.
#show has_surprise/1.
#show can_end/1.
"""


def asp_facts():
    from asp import fact
    return "\n".join(fact("craze", craze) for craze in CRAZES)


def asp_combos():
    from asp import atoms, one_model
    model = one_model(asp_facts() + "\n" + ASP_RULES)
    return set(atoms(model, "craze")), set(atoms(model, "has_surprise")), set(atoms(model, "can_end"))


def verify():
    from asp import atoms, one_model
    model = one_model(asp_facts() + "\n" + ASP_RULES)
    expected = {(c,) for c in CRAZES}
    if set(atoms(model, "craze")) != expected:
        raise StoryError("ASP and Python disagree about available crazes.")
    if set(atoms(model, "has_surprise")) != expected:
        raise StoryError("ASP and Python disagree about surprises.")
    count = 0
    for craze, hero, helper in itertools.product(CRAZES, HEROES, HELPERS):
        sample = generate(StoryParams(craze=craze, hero=hero, helper=helper))
        if "surprise" not in sample.story.lower() and "surprising" not in sample.story.lower():
            raise StoryError("Generated story lacks a surprise.")
        if len(sample.story_qa) < 3:
            raise StoryError("Generated story lacks grounded questions.")
        count += 1
    print(f"OK: {count} configurations; ASP parity; complete stories.")


def generate(p: StoryParams) -> StorySample:
    return Teller(simulate(p)).render()


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--craze", choices=CRAZES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--voice", choices=VOICES, default="gentle")
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng, index=0, sample=False):
    p = StoryParams(
        world_seed=args.world_seed + index,
        prose_seed=args.prose_seed + index,
        voice=args.voice,
    )
    for name, choices in (
        ("hero", HEROES),
        ("craze", CRAZES),
        ("helper", HELPERS),
    ):
        value = getattr(args, name)
        setattr(p, name, value if value is not None else rng.choice(choices) if sample else getattr(p, name))
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
        print(json.dumps({
            "state": sample.world.snapshot(),
            "history": [asdict(event) for event in sample.world.history],
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
            print(json.dumps({
                "craze": sorted(asp_combos()[0]),
                "has_surprise": sorted(asp_combos()[1]),
                "can_end": sorted(asp_combos()[2]),
            }))
            return 0
        rng = random.Random(args.world_seed)
        if args.all:
            params = [
                resolve_params(args, rng, i)
                for i, craze in enumerate(CRAZES)
                if args.craze is None or args.craze == craze
            ]
            params = [StoryParams(**{**asdict(p), "craze": craze}) for p, craze in zip(params, CRAZES)]
        else:
            params = [resolve_params(args, rng, i, sample=args.n > 1) for i in range(args.n)]
        if args.json:
            rows = [generate(p).to_dict() for p in params]
            print(json.dumps(rows[0] if len(rows) == 1 else rows, ensure_ascii=False, indent=2))
        else:
            for i, p in enumerate(params):
                emit(
                    generate(p),
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {i + 1}\n" if len(params) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
