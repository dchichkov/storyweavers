#!/usr/bin/env python3
"""A tiny nursery-rhyme world about a coarse fence and a kind repair."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
from dataclasses import asdict, dataclass, field
import itertools
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


MATERIALS = ("rope", "reeds")
WEATHERS = ("breezy", "still")
SOUNDS = ("jingle", "clack")
MAX_ACTIONS = 12


@dataclass
class StoryParams:
    hero: str = "Nell"
    material: str = "rope"
    weather: str = "breezy"
    sound: str = "jingle"
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
    state: dict


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.fact_events: dict[str, int] = {}
        self.relations: set[tuple[str, str, str]] = set()
        self.outcome = ""

    def snapshot(self):
        return {
            "entities": {key: asdict(value) for key, value in self.entities.items()},
            "relations": sorted(self.relations),
            "outcome": self.outcome,
        }

    def record(self, kind, actor, *, facts=(), needs=(), **data):
        missing = [fact for fact in needs if fact not in self.fact_events]
        if missing:
            raise StoryError(f"{kind} needs earlier facts: {', '.join(missing)}.")
        event_id = len(self.history)
        causes = tuple(sorted({self.fact_events[fact] for fact in needs}))
        self.history.append(
            Event(event_id, kind, actor, data, tuple(facts), causes, self.snapshot())
        )
        for fact in facts:
            self.fact_events[fact] = event_id


def validate_params(p: StoryParams):
    if p.material not in MATERIALS:
        raise StoryError(f"Unknown material: {p.material!r}.")
    if p.weather not in WEATHERS:
        raise StoryError(f"Unknown weather: {p.weather!r}.")
    if p.sound not in SOUNDS:
        raise StoryError(f"Unknown sound: {p.sound!r}.")
    if not isinstance(p.world_seed, int) or not isinstance(p.prose_seed, int):
        raise StoryError("Seeds must be integers.")


def build_world(p: StoryParams):
    validate_params(p)
    w = World(p)
    w.entities = {
        "nell": Entity("nell", p.hero, "garden", memes={"kindness": 1}),
        "lamb": Entity("lamb", "the little lamb", "garden", memes={"worry": 1}),
        "gate": Entity(
            "gate", "the garden gate", "garden",
            meters={"perimeter": 1, "gap": 2, "safe": 0},
            memes={"welcome": 0},
        ),
        "bell": Entity("bell", "the small bell", "shed", meters={"sound": 1}),
        "rope": Entity("rope", "a coarse rope", "shed", meters={"length": 3}),
        "reeds": Entity("reeds", "three stout reeds", "garden", meters={"length": 3}),
        "moon": Entity("moon", "the moon", "sky", memes={"calm": 1}),
    }
    w.record(
        "opening",
        "nell",
        facts=("perimeter_seen", "lamb_worried"),
        gap=2,
        weather=p.weather,
        sound=p.sound,
    )
    return w


def choose_action(w: World):
    facts = w.fact_events
    if "ending" in facts:
        return "close"
    if "kindness_shown" not in facts:
        return "notice"
    if "material_ready" not in facts:
        return "gather"
    if "gate_mended" not in facts:
        return "mend"
    if "bell_hung" not in facts:
        return "hang_bell"
    return "comfort"


def execute(w: World, action: str):
    p = w.params
    if action == "notice":
        w.entities["nell"].memes["kindness"] = 2
        w.entities["lamb"].memes["worry"] = 0.7
        w.record(
            "notice", "nell",
            facts=("kindness_shown",),
            needs=("perimeter_seen", "lamb_worried"),
        )
    elif action == "gather":
        if p.material == "rope":
            w.entities["rope"].location = "gate"
        else:
            w.entities["reeds"].location = "gate"
        w.record("gather", "nell", facts=("material_ready",), needs=("kindness_shown",),
                 material=p.material)
    elif action == "mend":
        material = w.entities[p.material]
        if material.location != "gate":
            raise StoryError("The chosen material is not at the gate.")
        w.entities["gate"].meters.update(gap=0, safe=1)
        w.relations.add((p.material, "mends", "gate"))
        w.record("mend", "nell", facts=("gate_mended",), needs=("material_ready",),
                 material=p.material)
    elif action == "hang_bell":
        w.entities["bell"].location = "gate"
        w.entities["bell"].meters["sound"] = 2
        w.relations.add(("bell", "warns", "lamb"))
        w.record("hang_bell", "nell", facts=("bell_hung",), needs=("gate_mended",),
                 sound=p.sound)
    elif action == "comfort":
        w.entities["lamb"].location = "garden"
        w.entities["lamb"].memes["worry"] = 0
        w.entities["gate"].memes["welcome"] = 1
        w.outcome = "safe_perimeter"
        w.record("comfort", "nell", facts=("kindness_complete",), needs=("bell_hung",))
        w.record("close", "nell", facts=("ending",), needs=("kindness_complete",))
    elif action == "close":
        raise StoryError("The nursery-rhyme ending has already been made.")
    else:
        raise StoryError(f"Unknown action: {action}.")


def validate_world(w: World):
    if not w.outcome or "ending" not in w.fact_events:
        raise StoryError("The story must end with a safe garden.")
    if w.entities["gate"].meters["gap"] != 0:
        raise StoryError("The perimeter gate still has a gap.")
    if w.entities["lamb"].memes["worry"] != 0:
        raise StoryError("The lamb is still worried.")
    if ("bell", "warns", "lamb") not in w.relations:
        raise StoryError("The bell must warn the lamb.")
    for event in w.history:
        if any(parent >= event.id for parent in event.causes):
            raise StoryError("An event cannot depend on a future event.")


def simulate(p: StoryParams):
    w = build_world(p)
    for _ in range(MAX_ACTIONS):
        execute(w, choose_action(w))
        if "ending" in w.fact_events:
            validate_world(w)
            return w
    raise StoryError("The bounded garden plan did not finish.")


def render(w: World):
    p = w.params
    material = "coarse rope" if p.material == "rope" else "stout reeds"
    sound = "Jingle-jangle!" if p.sound == "jingle" else "Clack-clack!"
    lines = [
        f"{p.hero} walked round the perimeter, round and round the green.",
        "She saw a gap beside the gate, the widest gap she'd seen.",
        f'"The lamb is scared," said {p.hero}. "I\'ll make the garden kind."',
        '"Can you mend it?" asked the lamb. "Please do, if you can."',
        f"She fetched {material}, sturdy, plain, and fit,",
        f"Then tied it to the gate, bit by bit.",
        "The coarse repair held firm and true; the chilly wind blew through.",
        f"She hung a bell above the latch. {sound}",
        f'"Now I know the garden\'s edge," said the lamb. "And I trust you."',
        f"{p.hero} smiled beneath the moon, while flowers nodded bright.",
        "The safe perimeter sang a song, and all was well that night.",
    ]
    story = "\n".join(lines)
    qa = [
        QAItem(
            "Why did Nell mend the garden gate?",
            "Nell mended the garden gate because its gap worried the little lamb and left the garden perimeter unsafe.",
        ),
        QAItem(
            "How did the bell help?",
            f"The bell made a clear {p.sound} sound at the gate, so the lamb could notice the garden's edge and feel safe.",
        ),
        QAItem(
            "What changed at the end?",
            "The gap was closed, the bell was hung, and the lamb stopped worrying in the safe garden.",
        ),
    ]
    return story, qa


ASP_RULES = """
allowed_material(rope).
allowed_material(reeds).
mended(M) :- allowed_material(M), chosen(M).
bell_needed :- mended(_).
safe_perimeter :- bell_needed.
#show safe_perimeter/0.
#show mended/1.
"""


def asp_facts():
    from asp import fact
    return "\n".join(fact("chosen", material) for material in MATERIALS)


def asp_outcome():
    from asp import atoms, one_model
    model = one_model(asp_facts() + "\n" + ASP_RULES)
    return set(atoms(model, "safe_perimeter")), set(atoms(model, "mended"))


def generate(p: StoryParams):
    world = simulate(p)
    story, qa = render(world)
    return StorySample(
        params=p,
        story=story,
        prompts=["Write a Nursery Rhyme about Nell repairing a coarse perimeter for a worried lamb."],
        story_qa=qa,
        world_qa=[
            QAItem("What does a perimeter surround?", "A perimeter is the boundary around a place."),
            QAItem("What is kindness?", "Kindness means helping someone with care."),
        ],
        world=world,
    )


def verify():
    for material, weather, sound in itertools.product(MATERIALS, WEATHERS, SOUNDS):
        sample = generate(StoryParams(material=material, weather=weather, sound=sound))
        if "perimeter" not in sample.story or "coarse" not in sample.story:
            raise StoryError("The required seed words are missing.")
        if len(sample.story_qa) < 2:
            raise StoryError("The story needs grounded questions.")
    safe, mended = asp_outcome()
    if safe != {()} or mended != {(material,) for material in MATERIALS}:
        raise StoryError("Python and ASP disagree about the repaired perimeter.")
    print("OK: perimeter repairs, kindness, sound effects, and ASP parity.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--material", choices=MATERIALS)
    parser.add_argument("--weather", choices=WEATHERS)
    parser.add_argument("--sound", choices=SOUNDS)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args, rng, index=0, sample=False):
    return StoryParams(
        material=args.material or (rng.choice(MATERIALS) if sample else "rope"),
        weather=args.weather or (rng.choice(WEATHERS) if sample else "breezy"),
        sound=args.sound or (rng.choice(SOUNDS) if sample else "jingle"),
        world_seed=args.world_seed + index,
        prose_seed=args.prose_seed + index,
    )


def emit(sample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps(
            {"state": sample.world.snapshot(),
             "history": [asdict(event) for event in sample.world.history]},
            indent=2,
        ))


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
            safe, mended = asp_outcome()
            print(json.dumps({"safe_perimeter": sorted(safe), "mended": sorted(mended)}))
            return 0

        rng = random.Random(args.world_seed)
        if args.all:
            params = [
                resolve_params(args, rng, index=i). __class__(
                    material=material,
                    weather=weather,
                    sound=sound,
                    world_seed=args.world_seed + i,
                    prose_seed=args.prose_seed + i,
                )
                for i, (material, weather, sound)
                in enumerate(itertools.product(MATERIALS, WEATHERS, SOUNDS))
            ]
        else:
            params = [
                resolve_params(args, rng, i, sample=args.n > 1)
                for i in range(args.n)
            ]

        samples = [generate(params_item) for params_item in params]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
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
