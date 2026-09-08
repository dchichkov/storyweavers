#!/usr/bin/env python3
"""Luna's cumin cloud in the animal enclosure.

A small, deterministic storyworld about a hanging spice sack, a granulating
mill, and a suspiciously quiet animal enclosure.  The simulation decides what
happens; the teller turns those state changes into a tall tale with sound
effects and suspense.
"""

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


SACKS = ("canvas", "striped")
MILLS = ("hand", "wind")
ANIMALS = ("goat", "llama")
WEATHERS = ("still", "gusty")
VOICES = ("plain", "booming", "wry")
MAX_ACTIONS = 20


@dataclass
class StoryParams:
    heroine: str = "Luna"
    sack: str = "canvas"
    mill: str = "hand"
    animal: str = "goat"
    weather: str = "still"
    voice: str = "wry"
    world_seed: int = 777
    prose_seed: int = 42


@dataclass
class Entity:
    id: str
    label: str
    location: str = "enclosure"
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
        self.fact_events: dict[str, int] = {}
        self.relations: set[tuple[str, str, str]] = set()
        self.outcome = ""

    def snapshot(self) -> dict:
        return {
            "entities": {key: asdict(value) for key, value in self.entities.items()},
            "relations": sorted(self.relations),
            "outcome": self.outcome,
        }

    def record(self, kind: str, actor: str, *, facts=(), needs=(), **data):
        missing = [fact for fact in needs if fact not in self.fact_events]
        if missing:
            raise StoryError(f"{kind} needs missing evidence: {', '.join(missing)}.")
        event_id = len(self.history)
        causes = tuple(sorted({self.fact_events[fact] for fact in needs}))
        self.history.append(
            Event(
                id=event_id,
                kind=kind,
                actor=actor,
                data=data,
                facts=tuple(facts),
                causes=causes,
                state=self.snapshot(),
            )
        )
        for fact in facts:
            self.fact_events[fact] = event_id


def validate_params(p: StoryParams):
    registries = (
        (p.sack, SACKS, "sack"),
        (p.mill, MILLS, "mill"),
        (p.animal, ANIMALS, "animal"),
        (p.weather, WEATHERS, "weather"),
        (p.voice, VOICES, "voice"),
    )
    for value, choices, label in registries:
        if value not in choices:
            raise StoryError(f"Unknown {label}: {value!r}.")
    if not isinstance(p.world_seed, int) or not isinstance(p.prose_seed, int):
        raise StoryError("Seeds must be integers.")
    if not p.heroine or not p.heroine[0].isupper():
        raise StoryError("The heroine must be a capitalized name.")


def build_world(p: StoryParams) -> World:
    validate_params(p)
    w = World(p)
    w.entities = {
        "luna": Entity(
            "luna",
            p.heroine,
            meters={"reach": 2, "courage": 1},
            memes={"curiosity": 1, "suspense": 0},
        ),
        "keeper": Entity(
            "keeper",
            "the keeper",
            meters={"height": 1},
            memes={"worry": 0},
        ),
        "animal": Entity(
            "animal",
            f"the {p.animal}",
            meters={"size": 2 if p.animal == "goat" else 4, "hunger": 1},
            memes={"alertness": 1, "suspense": 0},
        ),
        "sack": Entity(
            "sack",
            f"the {p.sack} cumin sack",
            location="beam",
            meters={"mass": 1, "height": 3, "hanging": 1},
            memes={"mystery": 1},
        ),
        "mill": Entity(
            "mill",
            f"the {p.mill} granulating mill",
            location="bench",
            meters={"ground": 0, "ready": 0, "noise": 2 if p.mill == "wind" else 1},
        ),
        "beam": Entity(
            "beam",
            "the high enclosure beam",
            meters={"height": 3, "strength": 2},
        ),
        "gate": Entity(
            "gate",
            "the enclosure gate",
            meters={"closed": 1},
        ),
        "cumin": Entity(
            "cumin",
            "the cumin",
            location="sack",
            meters={"amount": 1, "ground": 0},
        ),
    }
    w.relations.add(("sack", "hangs_from", "beam"))
    w.record(
        "opening",
        "luna",
        facts=("sack_seen", "enclosure_known"),
        heroine=p.heroine,
        animal=p.animal,
        weather=p.weather,
    )
    return w


def choose_action(w: World) -> str:
    facts = w.fact_events
    if "ending" in facts:
        return "close"
    if "animal_safe" not in facts and "mill_started" in facts:
        return "calm_animal"
    if "cumin_ground" not in facts and "mill_started" in facts:
        return "granulate"
    if "mill_started" not in facts and "mill_ready" in facts:
        return "start_mill"
    if "mill_ready" not in facts and "sack_lowered" in facts:
        return "place_mill"
    if "sack_lowered" not in facts:
        return "lower_sack"
    return "inspect"


def execute(w: World, action: str):
    p = w.params
    luna = w.entities["luna"]
    animal = w.entities["animal"]
    sack = w.entities["sack"]
    mill = w.entities["mill"]
    cumin = w.entities["cumin"]

    if action == "inspect":
        if "sack_seen" in w.fact_events and "plan_known" not in w.fact_events:
            luna.memes["suspense"] = 1
            w.record(
                "inspect",
                "luna",
                facts=("plan_known",),
                needs=("sack_seen",),
                height=sack.meters["height"],
            )
            return
        raise StoryError("Luna has no useful inspection left to make.")

    if action == "lower_sack":
        if sack.location != "beam":
            raise StoryError("The cumin sack is not hanging from the beam.")
        if p.weather == "gusty":
            sack.meters["height"] = 2
            w.record(
                "wind_lowers_sack",
                "wind",
                facts=("sack_lowered",),
                needs=("plan_known",),
                height=2,
            )
        else:
            sack.meters["height"] = 1
            w.record(
                "rope_lowered",
                "luna",
                facts=("sack_lowered",),
                needs=("plan_known",),
                height=1,
            )
        sack.location = "ground"
        w.relations.discard(("sack", "hangs_from", "beam"))
        return

    if action == "place_mill":
        if sack.location != "ground":
            raise StoryError("The mill cannot be loaded until the sack is lowered.")
        if mill.location != "bench":
            raise StoryError("The mill is not on the bench.")
        mill.meters["ready"] = 1
        w.record(
            "place_mill",
            "luna",
            facts=("mill_ready",),
            needs=("sack_lowered",),
            mill=p.mill,
        )
        return

    if action == "start_mill":
        if not mill.meters["ready"]:
            raise StoryError("The mill is not ready.")
        mill.meters["ground"] = 1
        w.record(
            "start_mill",
            "luna",
            facts=("mill_started",),
            needs=("mill_ready",),
            noise=mill.meters["noise"],
        )
        return

    if action == "granulate":
        if not mill.meters["ground"]:
            raise StoryError("The mill has not started.")
        cumin.meters["ground"] = 1
        cumin.location = "mill"
        animal.memes["suspense"] = 1
        w.record(
            "granulate",
            "mill",
            facts=("cumin_ground",),
            needs=("mill_started",),
            spice="cumin",
        )
        return

    if action == "calm_animal":
        if "cumin_ground" not in w.fact_events:
            raise StoryError("The animal has not heard the mill yet.")
        animal.memes["suspense"] = 0
        w.entities["gate"].meters["closed"] = 1
        w.record(
            "calm_animal",
            "luna",
            facts=("animal_safe",),
            needs=("cumin_ground",),
            animal=p.animal,
        )
        return

    if action == "close":
        if "animal_safe" not in w.fact_events:
            raise StoryError("The enclosure is not safe yet.")
        w.outcome = "cumin_ready"
        luna.memes["suspense"] = 0
        w.record(
            "close",
            "luna",
            facts=("ending",),
            needs=("animal_safe",),
            outcome=w.outcome,
        )
        return

    raise StoryError(f"Unknown action: {action}.")


def validate_world(w: World):
    if "ending" not in w.fact_events or not w.outcome:
        raise StoryError("The story must end with a resolved enclosure.")
    if w.entities["animal"].memes["suspense"] != 0:
        raise StoryError("The animal must be calm at the ending.")
    if w.entities["cumin"].meters["ground"] != 1:
        raise StoryError("The cumin must be granulated.")
    for event in w.history:
        if any(parent >= event.id for parent in event.causes):
            raise StoryError("An event cannot depend on a future event.")


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    for _ in range(MAX_ACTIONS):
        execute(w, choose_action(w))
        if "ending" in w.fact_events:
            validate_world(w)
            return w
    raise StoryError("The enclosure tale did not resolve in time.")


class Teller:
    def __init__(self, world: World):
        self.world = world
        self.p = world.params
        self.rng = random.Random(self.p.prose_seed)
        self.parts: list[str] = []
        self.qa: list[QAItem] = []
        self.dialogue_turns = 0

    def say(self, text: str):
        self.parts.append(text)

    def exchange(self, lines: list[tuple[str, str]]):
        rendered = []
        for speaker, line in lines:
            name = self.p.heroine if speaker == "luna" else "the keeper"
            rendered.append(f'"{line}" {name} said.')
            self.dialogue_turns += 1
        self.parts.extend(rendered)

    def tell(self, event: Event):
        p = self.p
        k = event.kind
        if k == "opening":
            self.say(
                f"In the animal enclosure, Luna found a {p.sack} sack of cumin hanging "
                f"higher than a cloud and twice as suspicious."
            )
            self.exchange(
                [
                    ("luna", "Why is the cumin hanging up there?"),
                    ("keeper", "Because the animals cannot eat what they cannot reach."),
                    ("luna", "Then I will bring it down carefully."),
                ]
            )
            self.say(
                f"The {p.animal} stared at the sack. Even the fence seemed to hold its breath."
            )
            self.qa.append(
                QAItem(
                    "What was hanging in the animal enclosure?",
                    f"A {p.sack} sack of cumin was hanging from the high enclosure beam.",
                )
            )
        elif k == "inspect":
            self.say(
                f"Luna inspected the rope. It quivered above the {p.animal}, and the "
                "silence below it felt as tight as a drumskin."
            )
            self.exchange(
                [
                    ("keeper", "Will it fall?"),
                    ("luna", "Not if we lower it before the wind or the animals decide otherwise."),
                ]
            )
            self.qa.append(
                QAItem(
                    "Why did Luna inspect the hanging sack?",
                    "She wanted to understand how to lower it safely before the wind or an animal could make it fall.",
                )
            )
        elif k == "wind_lowers_sack":
            self.say(
                "The wind gave one enormous whoosh. The rope slid, the sack dipped, "
                "and the whole enclosure whispered, 'Oh!'"
            )
            self.exchange(
                [
                    ("keeper", "That was not my idea of careful."),
                    ("luna", "It was the wind's idea. We must hurry."),
                ]
            )
        elif k == "rope_lowered":
            self.say(
                "Luna pulled the rope hand over hand. Scritch, creak, swish—the sack "
                "descended until her boots could reach it."
            )
            self.exchange(
                [
                    ("keeper", "Do you have it?"),
                    ("luna", "I have the rope, the sack, and my courage."),
                ]
            )
        elif k == "place_mill":
            self.say(
                f"She set the {p.mill} mill on the bench and fitted the cumin sack above it. "
                "The machine looked small enough to grind a seed and loud enough to wake a mountain."
            )
            self.exchange(
                [
                    ("keeper", "That mill is tiny."),
                    ("luna", "Tiny tools can make very large smells."),
                ]
            )
        elif k == "start_mill":
            if p.mill == "wind":
                sound = "whump-whump-whump"
            else:
                sound = "clack-clack-clack"
            self.say(
                f"Luna started the mill. It answered with {sound}! The {p.animal} froze, "
                "and a long suspenseful second stretched from gate to roof."
            )
            self.exchange(
                [
                    ("keeper", "The animal is listening."),
                    ("luna", "Then it will hear that we mean no harm."),
                ]
            )
            self.qa.append(
                QAItem(
                    "What happened when Luna started the mill?",
                    f"The {p.mill} mill made a loud sound, and the {p.animal} froze to listen.",
                )
            )
        elif k == "granulate":
            self.say(
                "The cumin rattled into the mill. Crunch! Grind! Puff! The seeds became "
                "fine golden granules, and the scent rolled through the enclosure like a cheerful cloud."
            )
            self.exchange(
                [
                    ("keeper", "Is that the frightening part?"),
                    ("luna", "No. The frightening part is waiting to see who sneezes first."),
                ]
            )
            self.qa.append(
                QAItem(
                    "What did the mill do to the cumin?",
                    "It ground the cumin seeds into fine golden granules.",
                )
            )
        elif k == "calm_animal":
            self.say(
                f"The {p.animal} lifted its nose. Luna closed the gate, lowered her voice, "
                "and offered a quiet hand. The animal sniffed once, twice, then gave a tiny "
                "and dignified snort."
            )
            self.exchange(
                [
                    ("keeper", "Is the enclosure safe?"),
                    ("luna", "The gate is shut, the animal is calm, and the cumin is behaving."),
                ]
            )
            self.qa.append(
                QAItem(
                    "How did Luna keep the animal safe?",
                    "She kept the enclosure gate closed and calmed the animal after the mill startled it.",
                )
            )
        elif k == "close":
            self.say(
                f"At last, the {p.animal} settled beside the fence while the golden granulated "
                "cumin cooled in its bowl. The hanging mystery had become a useful spice."
            )
            self.exchange(
                [
                    ("keeper", "Will you hang the sack again?"),
                    ("luna", "Only after we build a shelf lower than the clouds."),
                ]
            )
            self.say(
                "Outside the enclosure, the wind sighed. Inside, nothing fell, nobody fled, "
                "and Luna's little cumin cloud smelled like victory."
            )
            self.qa.append(
                QAItem(
                    "How did the story end?",
                    "The animal stayed calm and safe while the cumin cooled as useful granules in its bowl.",
                )
            )
        else:
            raise StoryError(f"No prose rendering for event {k!r}.")

    def run(self) -> tuple[str, list[QAItem]]:
        for event in self.world.history:
            self.tell(event)
        if self.dialogue_turns < 4:
            raise StoryError("The story needs a real back-and-forth exchange.")
        return "\n\n".join(self.parts), self.qa


ASP_RULES = """
safe_plan :- hanging_sack, lower_first, mill_ready, animal_safe.
hanging_sack.
lower_first.
mill_ready.
animal_safe.
#show safe_plan/0.
"""


def asp_facts():
    from asp import fact
    return "\n".join(
        [
            fact("sack_type", sack) for sack in SACKS
        ]
        + [fact("mill_type", mill) for mill in MILLS]
        + [fact("animal_type", animal) for animal in ANIMALS]
    )


def asp_signature() -> set[tuple]:
    from asp import atoms, one_model
    model = one_model(asp_facts() + "\n" + ASP_RULES)
    return set(atoms(model, "safe_plan"))


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    story, qa = Teller(world).run()
    return StorySample(
        params=params,
        story=story,
        prompts=[
            f"Write a suspenseful Tall Tale about {params.heroine} using a hanging "
            f"cumin sack and a {params.mill} mill in an animal enclosure."
        ],
        story_qa=qa,
        world_qa=[
            QAItem(
                "What is granulate?",
                "To granulate something is to break it into small grains or granules.",
            ),
            QAItem(
                "Why can a hanging sack be risky?",
                "It may swing or fall, so it should be lowered carefully before anyone works beneath it.",
            ),
        ],
        world=world,
    )


def verify():
    if asp_signature() != {()}:
        raise StoryError("ASP did not confirm the safe plan.")
    count = 0
    for sack, mill, animal, weather in itertools.product(
        SACKS, MILLS, ANIMALS, WEATHERS
    ):
        params = StoryParams(sack=sack, mill=mill, animal=animal, weather=weather)
        sample = generate(params)
        if "cumin" not in sample.story or "granulat" not in sample.story:
            raise StoryError("The generated story lost the seed vocabulary.")
        if len(sample.story_qa) < 3:
            raise StoryError("Generated stories need grounded questions.")
        count += 1
    print(f"OK: {count} enclosure worlds; Python/ASP parity; dialogue and QA verified.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--heroine", default="Luna")
    parser.add_argument("--sack", choices=SACKS)
    parser.add_argument("--mill", choices=MILLS)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--weather", choices=WEATHERS)
    parser.add_argument("--voice", choices=VOICES, default="wry")
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng: random.Random, index: int = 0, sample: bool = False):
    params = StoryParams(
        heroine=args.heroine,
        world_seed=args.world_seed + index,
        prose_seed=args.prose_seed + index,
        voice=args.voice,
    )
    for name, choices in (
        ("sack", SACKS),
        ("mill", MILLS),
        ("animal", ANIMALS),
        ("weather", WEATHERS),
    ):
        value = getattr(args, name)
        setattr(
            params,
            name,
            value if value is not None else rng.choice(choices) if sample else getattr(params, name),
        )
    validate_params(params)
    return params


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
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
                    "world": sample.world.snapshot(),
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
            print(json.dumps(sorted(asp_signature())))
            return 0

        rng = random.Random(args.world_seed)
        if args.all:
            params_list = []
            for sack, mill, animal, weather in itertools.product(
                SACKS, MILLS, ANIMALS, WEATHERS
            ):
                if args.sack is not None and args.sack != sack:
                    continue
                if args.mill is not None and args.mill != mill:
                    continue
                if args.animal is not None and args.animal != animal:
                    continue
                if args.weather is not None and args.weather != weather:
                    continue
                params_list.append(
                    StoryParams(
                        heroine=args.heroine,
                        sack=sack,
                        mill=mill,
                        animal=animal,
                        weather=weather,
                        voice=args.voice,
                        world_seed=args.world_seed + len(params_list),
                        prose_seed=args.prose_seed + len(params_list),
                    )
                )
        else:
            params_list = [
                resolve_params(args, rng, index, sample=args.n > 1)
                for index in range(args.n)
            ]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
