#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ride_might_cautionary_friendship_curiosity_slice_of.py
======================================================================================

A small standalone storyworld for a slice-of-life tale about two friends, a
curious choice, and a careful warning. The seed words "ride" and "might" shape
the premise: a child wants to take a ride, wonders what might happen, and a
friend or grown-up gives a calm caution that leads to a safer, happier ending.

This world models:
- typed entities with physical meters and emotional memes
- a forward-chaining world model
- a reasonableness gate
- an inline ASP twin
- story-grounded and world-knowledge QA

The story domain is intentionally small and concrete:
- a child wants a ride on something simple: a scooter, bike, tricycle, wagon, or
  swing seat
- curiosity pushes them toward a slightly risky choice
- a friend notices what might go wrong
- the pair makes a cautious adjustment and still enjoys the ride

The result is a slice-of-life story with a gentle turn and a clear ending image.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Ride:
    id: str
    label: str
    verb: str
    noun: str
    surface: str
    speed: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Concern:
    id: str
    label: str
    risk: str
    warning: str
    fix: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out = []
    rider = world.entities.get("rider")
    if rider and rider.meters.get("wobble", 0) >= THRESHOLD:
        sig = ("spill", rider.id)
        if sig not in world.fired:
            world.fired.add(sig)
            rider.meters["shaky"] = rider.meters.get("shaky", 0) + 1
            rider.memes["nervous"] = rider.memes.get("nervous", 0) + 1
            out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(x for x in bits if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, ride: Ride) -> dict:
    sim = world.copy()
    _do_try(sim, sim.get("rider"), ride, narrate=False)
    return {
        "wobbly": sim.get("rider").meters.get("wobble", 0) >= THRESHOLD,
        "safe": sim.get("ride_obj").meters.get("scrape", 0) < THRESHOLD,
    }


def _do_try(world: World, rider: Entity, ride: Ride, narrate: bool = True) -> None:
    rider.meters["ride"] = rider.meters.get("ride", 0) + 1
    if not ride.safe:
        rider.meters["wobble"] = rider.meters.get("wobble", 0) + 1
    propagate(world, narrate=narrate)


def reasonableness_gate(ride: Ride, concern: Concern) -> bool:
    return concern.sense >= 2 and ride.safe


def tell(world_ride: Ride, concern: Concern, hero_name: str, friend_name: str, parent_type: str,
         use_helmet: bool, go_slow: bool) -> World:
    w = World()
    rider = w.add(Entity("rider", kind="character", type="boy", role="curious", traits=["curious"]))
    friend = w.add(Entity("friend", kind="character", type="girl", role="cautionary", traits=["careful"]))
    parent = w.add(Entity("parent", kind="character", type=parent_type, role="parent"))
    ride_obj = w.add(Entity("ride_obj", type="thing", label=world_ride.label, attrs={"surface": world_ride.surface}))
    helmet = w.add(Entity("helmet", type="thing", label="helmet", attrs={"protective": True}))
    rider.id = hero_name
    friend.id = friend_name

    rider.memes["curiosity"] = 1
    friend.memes["care"] = 1
    w.say(
        f"On a quiet afternoon, {hero_name} and {friend_name} found a {world_ride.label} by the curb. "
        f"{hero_name} wanted a ride, and {friend_name} was happy to come along."
    )
    w.say(
        f"{hero_name} looked at the path and wondered what {concern.risk} might happen if they went too fast."
    )
    w.para()
    rider.memes["want"] = 1
    if use_helmet:
        w.say(f'{friend_name} pointed at the helmet and said, "Let’s wear that first."')
        rider.memes["trust"] = rider.memes.get("trust", 0) + 1
    else:
        w.say(f'{hero_name} reached for the ride right away, but {friend_name} watched closely.')
    w.say(f'"If we take it slow, we can still have fun," {friend_name} said.')
    if not reasonableness_gate(world_ride, concern):
        raise StoryError("This ride choice is not reasonable for a gentle cautionary story.")

    if go_slow:
        rider.meters["wobble"] = 0
        w.say(f"{hero_name} listened, slowed down, and took the ride carefully.")
        w.say(f"The path was smooth, the wheels hummed, and nothing scraped at all.")
        w.para()
        w.say(
            f"At the end, {hero_name} rolled to a stop with a grin, helmet on and feet steady, "
            f"while {friend_name} laughed beside {hero_name}."
        )
        outcome = "safe"
    else:
        rider.meters["wobble"] = 1
        _do_try(w, rider, world_ride, narrate=False)
        w.say(
            f"{hero_name} tried the ride anyway, and the little wheels wobbled over a bump."
        )
        if predict(w, world_ride)["wobbly"]:
            w.say(
                f"{friend_name} said, 'Wait, that might tip you over.'"
            )
        w.para()
        rider.meters["wobble"] = 0
        w.say(
            f"{hero_name} slowed down at once, and the ride became steady again."
        )
        w.say(
            f"By the time they reached the gate, the scare had passed and the two friends were smiling."
        )
        outcome = "near_miss"

    w.facts.update(
        rider=rider,
        friend=friend,
        parent=parent,
        ride=world_ride,
        concern=concern,
        helmet=helmet,
        outcome=outcome,
        used_helmet=use_helmet,
    )
    return w


RIDES = {
    "bike": Ride("bike", "bike", "ride", "bike", "sidewalk", "fast", safe=True, tags={"bike", "ride"}),
    "scooter": Ride("scooter", "scooter", "ride", "scooter", "driveway", "quick", safe=True, tags={"scooter", "ride"}),
    "trike": Ride("trike", "tricycle", "ride", "tricycle", "path", "slow", safe=True, tags={"trike", "ride"}),
}

CONCERNS = {
    "bump": Concern("bump", "bumpy path", "the wheels might wobble on a bump", "might tip over", "slow down and steady the ride", 3, 3, tags={"bump"}),
    "speed": Concern("speed", "too much speed", "the rider might go too fast", "might hurry and wobble", "take it slow and keep both hands on", 3, 2, tags={"speed"}),
    "curb": Concern("curb", "curb edge", "the wheel might catch the curb", "might scrape the side", "turn carefully around the edge", 3, 3, tags={"curb"}),
}

NAMES_GIRL = ["Maya", "Lina", "Nina", "Ivy", "Zoe", "Tia"]
NAMES_BOY = ["Eli", "Noah", "Theo", "Ari", "Leo", "Owen"]


@dataclass
class StoryParams:
    ride: str
    concern: str
    hero: str
    friend: str
    hero_gender: str
    friend_gender: str
    parent: str
    use_helmet: bool = True
    go_slow: bool = True
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for rid in RIDES:
        for cid in CONCERNS:
            if reasonableness_gate(RIDES[rid], CONCERNS[cid]):
                combos.append((rid, cid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small slice-of-life ride storyworld.")
    ap.add_argument("--ride", choices=RIDES)
    ap.add_argument("--concern", choices=CONCERNS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--helmet", action="store_true", default=False)
    ap.add_argument("--go-slow", action="store_true", default=False)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.ride and args.concern:
        if not reasonableness_gate(RIDES[args.ride], CONCERNS[args.concern]):
            raise StoryError("That combination is too unreasonable for this storyworld.")
    combos = [c for c in valid_combos()
              if (args.ride is None or c[0] == args.ride) and (args.concern is None or c[1] == args.concern)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    ride, concern = rng.choice(sorted(combos))
    rg = args.hero_gender or rng.choice(["girl", "boy"])
    fg = args.friend_gender or ("boy" if rg == "girl" else "girl")
    hero = args.hero or rng.choice(NAMES_GIRL if rg == "girl" else NAMES_BOY)
    friend = args.friend or rng.choice([n for n in (NAMES_GIRL if fg == "girl" else NAMES_BOY) if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        ride=ride,
        concern=concern,
        hero=hero,
        friend=friend,
        hero_gender=rg,
        friend_gender=fg,
        parent=parent,
        use_helmet=args.helmet or True,
        go_slow=args.go_slow or True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child that includes the words "ride" and "might".',
        f"Tell a gentle friendship story where {f['rider'].id} wants a ride, {f['friend'].id} worries about what might happen, and they choose a careful way forward.",
        f"Write a cautionary but warm story about a small ride, a curious child, and a friend who notices a possible mistake before it gets worse.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    rider, friend, concern, ride = f["rider"], f["friend"], f["concern"], f["ride"]
    return [
        ("Who is the story about?",
         f"It is about {rider.id} and {friend.id}, two friends who are spending a quiet afternoon together. Their friendship is what keeps the story gentle and warm."),
        ("What did {0} wonder about?".format(rider.id),
         f"{rider.id} wondered what {concern.risk} might happen on the ride. That curious thought helped the story turn toward caution instead of trouble."),
        ("How did the friends solve the problem?",
         f"They slowed down and chose a careful way to use the {ride.label}. The ride stayed fun, but it was calmer and safer for both of them."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a ride?",
         "A ride is a trip or motion on something like a bike, scooter, or wagon. It can be fun when you use it carefully."),
        ("What does might mean in a story?",
         "Might means something could happen, but it is not certain. It is often used when someone is thinking about a possibility."),
        ("Why is it good to listen to a careful friend?",
         "A careful friend can notice danger early and help everyone stay safe. That makes the fun last longer."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        eemo = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if eemo:
            bits.append(f"memes={eemo}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(R, C) :- ride(R), concern(C), reasonable(R, C).
reasonable(R, C) :- safe(R), sense(C, S), S >= 2.

outcome(safe) :- chosen_go_slow, chosen_helmet.
outcome(near_miss) :- not chosen_go_slow.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid, r in RIDES.items():
        lines.append(asp.fact("ride", rid))
        if r.safe:
            lines.append(asp.fact("safe", rid))
    for cid, c in CONCERNS.items():
        lines.append(asp.fact("concern", cid))
        lines.append(asp.fact("sense", cid, c.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import sys as _sys
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP gate differs from Python gate.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP gate and story generation smoke test passed.")
    return rc


def explain_rejection(ride: Ride, concern: Concern) -> str:
    return f"(No story: this ride and concern combination is not reasonable for a small, calm slice-of-life tale.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(
        RIDES[params.ride],
        CONCERNS[params.concern],
        params.hero,
        params.friend,
        params.parent,
        params.use_helmet,
        params.go_slow,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("bike", "bump", "Maya", "Eli", "girl", "boy", "mother", True, True),
    StoryParams("scooter", "speed", "Noah", "Ivy", "boy", "girl", "father", True, True),
    StoryParams("trike", "curb", "Lina", "Theo", "girl", "boy", "mother", True, True),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid ride/concern combos:")
        for r, c in asp_valid_combos():
            print(f"  {r:8} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.friend}: {p.ride} / {p.concern}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
