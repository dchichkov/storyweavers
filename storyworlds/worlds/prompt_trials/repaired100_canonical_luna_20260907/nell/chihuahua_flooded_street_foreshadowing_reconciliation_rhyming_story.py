#!/usr/bin/env python3
"""A tiny rhyming storyworld about a chihuahua, a flooded street, and repair."""

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


NAMES = ("Nell", "Luna", "Milo", "Pip")
DOG_COLORS = ("tan", "black", "white")
HELPERS = ("neighbor", "mail carrier")
MAX_STEPS = 18


@dataclass
class StoryParams:
    hero: str = "Nell"
    dog_name: str = "Luna"
    dog_color: str = "tan"
    helper: str = "neighbor"
    rain_level: str = "high"
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
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.facts: dict[str, int] = {}
        self.outcome = ""

    def record(self, kind, actor, facts=(), needs=(), **data):
        if any(item not in self.facts for item in needs):
            raise StoryError(f"{kind} lacks a recorded cause.")
        causes = tuple(sorted(self.facts[item] for item in needs))
        event = Event(len(self.history), kind, actor, data, tuple(facts), causes)
        self.history.append(event)
        for item in facts:
            self.facts[item] = event.id


def validate_params(p: StoryParams):
    if p.dog_color not in DOG_COLORS:
        raise StoryError("Choose a tan, black, or white chihuahua.")
    if p.helper not in HELPERS:
        raise StoryError("Choose a neighbor or mail carrier.")
    if p.rain_level not in ("high", "steady"):
        raise StoryError("Rain must be high or steady.")
    if not all(isinstance(value, int) for value in (p.world_seed, p.prose_seed)):
        raise StoryError("Seeds must be integers.")
    if not p.hero or not p.dog_name:
        raise StoryError("The hero and chihuahua need names.")


def build_world(p: StoryParams) -> World:
    validate_params(p)
    w = World(p)
    w.entities = {
        "hero": Entity("hero", p.hero, "porch", memes={"worry": 0.4, "kindness": 1}),
        "dog": Entity("dog", f"{p.dog_name}, the {p.dog_color} chihuahua", "porch",
                      meters={"height": 1, "current": 0}, memes={"fear": 0.8, "trust": 0.3}),
        "helper": Entity("helper", f"the {p.helper}", "sidewalk", memes={"patience": 1}),
        "cart": Entity("cart", "a red garden cart", "shed", meters={"floats": 1, "capacity": 2}),
        "rope": Entity("rope", "a long yellow rope", "shed", meters={"length": 8}),
        "bridge": Entity("bridge", "a wooden plank", "porch", meters={"strength": 2}),
        "street": Entity("street", "the flooded street", "between_houses",
                         meters={"water": 3, "current": 2, "safe_path": 0}),
        "box": Entity("box", "a floating cardboard box", "street"),
    }
    w.record("opening", "hero", facts=("flood_seen", "dog_home"), water="ankle_deep")
    return w


def choose_action(w: World):
    p = w.params
    if "ending" in w.facts:
        return "close"
    if "dog_safe" in w.facts:
        return "reconcile"
    if "dog_reached" in w.facts:
        return "lift"
    if "rope_tied" in w.facts and "cart_ready" in w.facts:
        return "guide"
    if "rope_tied" in w.facts:
        return "fetch_cart"
    if "warning_seen" not in w.facts:
        return "notice_warning"
    if "argument" not in w.facts:
        return "argue"
    return "tie_rope"


def execute(w: World, action: str):
    p = w.params
    if action == "notice_warning":
        w.entities["hero"].memes["worry"] = 1
        w.record(action, "hero", facts=("warning_seen",), needs=("flood_seen",),
                 warning="the drain cover is loose")
    elif action == "argue":
        w.entities["helper"].memes["patience"] = 0.5
        w.record(action, "hero", facts=("argument",), needs=("warning_seen",))
    elif action == "tie_rope":
        w.entities["rope"].location = "cart"
        w.record(action, "hero", facts=("rope_tied",), needs=("argument",))
    elif action == "fetch_cart":
        w.entities["cart"].location = "street_edge"
        w.record(action, "helper", facts=("cart_ready",), needs=("rope_tied",))
    elif action == "guide":
        w.entities["dog"].location = "cart"
        w.entities["dog"].meters["current"] = 0
        w.record(action, "hero", facts=("dog_reached",), needs=("cart_ready", "rope_tied"))
    elif action == "lift":
        w.entities["dog"].location = "porch"
        w.entities["dog"].memes["fear"] = 0.1
        w.record(action, "helper", facts=("dog_safe",), needs=("dog_reached",))
    elif action == "reconcile":
        w.entities["hero"].memes["worry"] = 0
        w.entities["helper"].memes["patience"] = 1
        w.outcome = "reconciled"
        w.record(action, "hero", facts=("peace",), needs=("dog_safe",))
    elif action == "close":
        w.record(action, "hero", facts=("ending",), needs=("peace",))
    else:
        raise StoryError(f"Unknown action {action!r}.")


def validate_world(w: World):
    if w.outcome != "reconciled" or "ending" not in w.facts:
        raise StoryError("The chihuahua story must end with reconciliation.")
    if w.entities["dog"].location != "porch":
        raise StoryError("The chihuahua must be safe on the porch.")
    for event in w.history:
        if any(parent >= event.id for parent in event.causes):
            raise StoryError("An event cannot depend on a future event.")


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    for _ in range(MAX_STEPS):
        execute(w, choose_action(w))
        if "ending" in w.facts:
            validate_world(w)
            return w
    raise StoryError("The rescue did not finish.")


def render(w: World) -> tuple[str, list[QAItem]]:
    p = w.params
    dog = p.dog_name
    story = [
        f"Rain tapped the roof with a silver sound, while water curled and whirled around.",
        f"{p.hero} watched {dog}, a {p.dog_color} chihuahua, wait by the door, "
        "while waves slipped softly across the floor.",
        f'"Stay back," said {p.hero}. "The street is wide."',
        f'"I know the road," said the {p.helper}. "I can guide."',
        "But under the rain, a warning showed: the drain cover wobbled below.",
        f"{p.hero} frowned. " + '"That current may sweep him away."',
        f'"Then let us plan, not pull and pray," said the {p.helper} with a steady sway.',
        "They tied a yellow rope to a red cart bright, then rolled it slowly through the night.",
        f"{p.hero} called, " + f'"Come, {dog}, come near!"',
        f"The little chihuahua crossed the water, trembling with fear.",
        f"The cart came back; the {p.helper} reached down, and {dog} was safe on higher ground.",
        f'"I was too sharp," said {p.hero}. "Your warning was true."',
        f'"I was too proud," said the {p.helper}. "I should have listened to you."',
        "They shared a warm blanket as the rain passed by; peace made a small rainbow in the sky.",
        f"{dog} curled beside {p.hero}, dry and snug, while the two friends smiled and hugged.",
    ]
    qa = [
        QAItem(
            question=f"How did {p.hero} and the {p.helper} rescue {dog}?",
            answer=f"They tied a yellow rope to a red garden cart, guided {dog} across the flooded street, and lifted the chihuahua onto the porch.",
        ),
        QAItem(
            question="What warning helped them make a safer plan?",
            answer="They noticed that the drain cover was loose and that the current could sweep the small dog away.",
        ),
        QAItem(
            question="How did the characters reconcile?",
            answer=f"{p.hero} admitted being too sharp, and the {p.helper} admitted being too proud, so they listened to each other and shared a warm blanket.",
        ),
    ]
    return "\n\n".join(story), qa


ASP_RULES = """
safe(dog) :- rope_tied, cart_ready, dog_reached, lifted.
reconciled :- safe(dog), apology.
#show safe/1.
#show reconciled/0.
"""


def asp_facts():
    from asp import fact
    return "\n".join([
        fact("rope_tied"), fact("cart_ready"), fact("dog_reached"),
        fact("lifted"), fact("apology"),
    ])


def asp_check():
    from asp import atoms, one_model
    model = one_model(asp_facts() + "\n" + ASP_RULES)
    return set(atoms(model, "safe")), set(atoms(model, "reconciled"))


def generate(p: StoryParams) -> StorySample:
    world = simulate(p)
    story, qa = render(world)
    return StorySample(
        params=p,
        story=story,
        prompts=[f"Write a rhyming story about {p.hero}, a chihuahua, and a flooded street."],
        story_qa=qa,
        world_qa=[
            QAItem("What is a chihuahua?", "A chihuahua is a very small dog."),
            QAItem("What is reconciliation?", "Reconciliation is making peace after a disagreement."),
        ],
        world=world,
    )


def verify():
    p = StoryParams()
    sample = generate(p)
    if "chihuahua" not in sample.story.lower() or "flooded" not in sample.story.lower():
        raise StoryError("The story omitted the required domain words.")
    if not any("reconcil" in item.answer.lower() for item in sample.story_qa + sample.world_qa):
        raise StoryError("The story omitted reconciliation evidence.")
    safe, reconciled = asp_check()
    if safe != {("dog",)} or reconciled != {()}:
        raise StoryError("ASP and Python safety facts disagree.")
    for seed in range(10):
        other = StoryParams(world_seed=seed, prose_seed=seed)
        result = generate(other)
        if result.world.outcome != "reconciled":
            raise StoryError("A seeded story failed to reconcile.")
    print("OK: flooded-street chihuahua stories, foreshadowing, reconciliation, and ASP parity.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--dog-name", choices=NAMES)
    parser.add_argument("--dog-color", choices=DOG_COLORS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--rain-level", choices=("high", "steady"))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng, index=0, sample=False):
    p = StoryParams(
        world_seed=args.world_seed + index,
        prose_seed=args.prose_seed + index,
        hero=args.hero or (rng.choice(NAMES) if sample else "Nell"),
        dog_name=args.dog_name or (rng.choice(NAMES) if sample else "Luna"),
        dog_color=args.dog_color or (rng.choice(DOG_COLORS) if sample else "tan"),
        helper=args.helper or (rng.choice(HELPERS) if sample else "neighbor"),
        rain_level=args.rain_level or "high",
    )
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
            safe, reconciled = asp_check()
            print(json.dumps({"safe": sorted(safe), "reconciled": sorted(reconciled)}))
            return 0
        rng = random.Random(args.world_seed)
        if args.all:
            params = []
            for color, helper in itertools.product(DOG_COLORS, HELPERS):
                p = resolve_params(args, rng)
                p.dog_color = color
                p.helper = helper
                params.append(p)
        else:
            params = [resolve_params(args, rng, i, sample=args.n > 1) for i in range(args.n)]
        samples = [generate(p) for p in params]
        if args.json:
            rows = [sample.to_dict() for sample in samples]
            print(json.dumps(rows[0] if len(rows) == 1 else rows, ensure_ascii=False, indent=2))
        else:
            for i, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {i + 1}\n" if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
