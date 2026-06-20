#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/traffic_friendship_heartwarming.py
===================================================================

A small heartwarming story world about friendship, traffic, and a safe,
kind way to get home.

The core premise:
- Two friends want to cross a busy street.
- Traffic is loud and slow.
- One friend notices someone else who needs help.
- They wait, help, and cross safely together.
- The ending proves their friendship grew warmer and calmer.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- shared results containers imported eagerly
- StoryParams, build_parser, resolve_params, generate, emit, main
- -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- Python reasonableness gate with inline ASP twin
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Place:
    id: str
    label: str
    traffic: str
    safe_wait: str
    ending: str
    helpers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class TrafficSituation:
    id: str
    label: str
    noise: str
    speed: str
    delay: int
    risky: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendshipBeat:
    id: str
    label: str
    turn: str
    comfort: str
    action: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_anxiety(world: World) -> list[str]:
    out: list[str] = []
    for child in world.characters():
        if child.meters["traffic_close"] < THRESHOLD:
            continue
        sig = ("anxiety", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["worry"] += 1
        out.append("__anxiety__")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    a = world.entities.get("A")
    b = world.entities.get("B")
    if not a or not b:
        return out
    if a.memes["care"] >= THRESHOLD and b.memes["care"] >= THRESHOLD:
        sig = ("friendship",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["warmth"] += 1
            b.memes["warmth"] += 1
            out.append("__friendship__")
    return out


CAUSAL_RULES = [
    Rule("anxiety", "social", _r_anxiety),
    Rule("friendship", "social", _r_friendship),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonable_combo(place: Place, traffic: TrafficSituation, beat: FriendshipBeat) -> bool:
    return traffic.risky and "crossing" in place.helpers and beat.id in FRIENDSHIP_BEATS


def delay_cost(delay: int) -> int:
    return max(1, delay + 1)


def can_help(beat: FriendshipBeat, delay: int) -> bool:
    return delay_cost(delay) <= 3


def predict(world: World, traffic: TrafficSituation) -> dict:
    sim = world.copy()
    sim.get("traffic").meters["traffic_close"] += 1
    propagate(sim, narrate=False)
    return {
        "worry": sim.get("A").memes["worry"],
        "warmth": sim.get("A").memes["warmth"] + sim.get("B").memes["warmth"],
        "traffic_close": sim.get("traffic").meters["traffic_close"],
    }


def _traffic_arrives(world: World, place: Place, traffic: TrafficSituation) -> None:
    world.get("traffic").meters["traffic_close"] += 1
    world.get("A").meters["traffic_close"] += 1
    world.get("B").meters["traffic_close"] += 1
    world.get("A").memes["joy"] += 0.5
    world.get("B").memes["joy"] += 0.5
    propagate(world, narrate=True)
    world.say(
        f"At {place.label}, the traffic was loud and slow, and the light kept blinking "
        f"while cars waited in a shining line."
    )


def _friend_worries(world: World, a: Entity, b: Entity) -> None:
    a.memes["care"] += 1
    b.memes["care"] += 1
    world.say(
        f'{a.id} looked at the street and held {a.pronoun("possessive")} breath. '
        f'"The traffic is too busy," {a.id} said softly.'
    )
    world.say(
        f'{b.id} smiled back and squeezed {b.id.lower() if False else a.id}\'s hand. '
        f'"We can wait together," {b.id} said.'
    )


def _help_other(world: World, helper: Entity, other: Entity, place: Place) -> None:
    helper.memes["kindness"] += 1
    other.memes["gratitude"] += 1
    world.say(
        f"Then {helper.id} noticed a little child near the curb, blinking at the noise. "
        f"{helper.id} waved them over and stood beside them too."
    )
    world.say(
        f"Together, the two friends made a small safe circle on the sidewalk, so nobody "
        f"felt alone while the cars passed."
    )


def _cross_safely(world: World, place: Place, beat: FriendshipBeat) -> None:
    world.get("A").memes["worry"] = 0
    world.get("B").memes["worry"] = 0
    world.get("A").memes["warmth"] += 1
    world.get("B").memes["warmth"] += 1
    world.say(
        f"When the walk sign finally turned, the friends crossed carefully with the "
        f"little child between them, holding hands and moving in step."
    )
    world.say(
        f"On the other side, {place.ending} glowed warm and golden, and the waiting "
        f"felt worth it."
    )
    world.say(
        f"{beat.comfort.capitalize()} made the ending even sweeter, because friendship "
        f"had turned a noisy traffic moment into a kind one."
    )


def tell(place: Place, traffic: TrafficSituation, beat: FriendshipBeat,
         name_a: str = "Maya", gender_a: str = "girl",
         name_b: str = "Noah", gender_b: str = "boy") -> World:
    world = World()
    a = world.add(Entity(id="A", kind="character", type=gender_a, label=name_a, role="friend"))
    b = world.add(Entity(id="B", kind="character", type=gender_b, label=name_b, role="friend"))
    t = world.add(Entity(id="traffic", kind="thing", type="traffic", label="the traffic"))
    world.facts["place"] = place
    world.facts["traffic"] = traffic
    world.facts["beat"] = beat
    world.facts["a_name"] = name_a
    world.facts["b_name"] = name_b

    world.say(
        f"One afternoon, {name_a} and {name_b} walked to {place.label} together. "
        f"They were friends, and they liked doing small things side by side."
    )
    world.say(
        f"They paused at the curb because {place.label} was full of traffic, and the cars "
        f"were making the street feel bigger than it really was."
    )

    world.para()
    _traffic_arrives(world, place, traffic)
    _friend_worries(world, a, b)

    world.para()
    if can_help(beat, traffic.delay):
        _help_other(world, a, b, place)
        _cross_safely(world, place, beat)
        outcome = "warm"
    else:
        world.say(
            f"They tried to hurry, but the traffic was still too close, so they chose the "
            f"bravest thing: they stepped back and waited until it was truly safe."
        )
        world.say(
            f"That quiet choice kept everyone calm, and the friends stayed close until the road "
            f"opened again."
        )
        outcome = "waited"

    world.facts.update(
        outcome=outcome,
        a=a,
        b=b,
        traffic_entity=t,
        traffic_close=t.meters["traffic_close"] >= THRESHOLD,
        friendship=a.memes["warmth"] + b.memes["warmth"],
    )
    return world


PLACES = {
    "crosswalk": Place("crosswalk", "the crosswalk", "busy", "wait together", "the little park bench",
                       helpers={"crossing"}, tags={"street", "traffic", "walk"}),
    "school_gate": Place("school_gate", "the school gate", "busy", "wait together", "the front steps",
                         helpers={"crossing"}, tags={"school", "traffic", "friends"}),
    "corner_shop": Place("corner_shop", "the corner shop", "slow", "wait together", "the warm doorway",
                         helpers={"crossing"}, tags={"shop", "traffic"}),
}

TRAFFIC = {
    "cars": TrafficSituation("cars", "cars", "horns and engines", "slow and heavy", 1, tags={"cars", "traffic"}),
    "buses": TrafficSituation("buses", "buses", "rumbling wheels", "big and slow", 2, tags={"bus", "traffic"}),
    "rush_hour": TrafficSituation("rush_hour", "rush hour traffic", "a long murmur of engines", "dense and noisy", 1, tags={"traffic"}),
}

FRIENDSHIP_BEATS = {
    "wait": FriendshipBeat("wait", "wait together", "their friendship grew calmer", "the warm sidewalk",
                           "waited side by side", tags={"friendship", "kindness"}),
    "help": FriendshipBeat("help", "help together", "their kindness felt brighter", "the safe little circle",
                           "helped the other child", tags={"friendship", "helping"}),
    "share": FriendshipBeat("share", "share a smile", "their smiles made the street feel softer",
                            "the shared grin", "shared a smile", tags={"friendship", "smile"}),
}

GIRL_NAMES = ["Maya", "Lila", "Zoe", "Ava", "Nina", "Ella"]
BOY_NAMES = ["Noah", "Eli", "Owen", "Leo", "Finn", "Theo"]


@dataclass
class StoryParams:
    place: str
    traffic: str
    beat: str
    a_name: str
    a_gender: str
    b_name: str
    b_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TRAFFIC:
            for b in FRIENDSHIP_BEATS:
                if reasonable_combo(PLACES[p], TRAFFIC[t], FRIENDSHIP_BEATS[b]):
                    combos.append((p, t, b))
    return combos


KNOWLEDGE = {
    "traffic": [("What is traffic?",
                 "Traffic is cars, buses, and other vehicles moving on roads. When traffic is busy, people should wait and cross carefully.")],
    "crosswalk": [("What is a crosswalk?",
                   "A crosswalk is a safe place on the street where people can cross when drivers can see them.")],
    "friendship": [("What does a good friend do?",
                    "A good friend stays kind, listens, and helps make hard moments feel easier.")],
    "wait": [("Why is waiting important near traffic?",
              "Waiting gives cars time to pass and helps people cross when the road is safe.")],
    "kindness": [("What is kindness?",
                  "Kindness means doing something gentle and helpful for someone else.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a young child that includes the word "traffic" and shows friendship.',
        f"Tell a gentle story where {f['a_name']} and {f['b_name']} wait through busy traffic and help someone feel safe.",
        f"Write a story about two friends at {f['place'].label} who choose kindness while traffic passes by.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["a_name"]
    b = f["b_name"]
    place = f["place"]
    traffic = f["traffic"]
    beat = f["beat"]
    outcome = f["outcome"]
    qa = [
        ("Who is the story about?",
         f"It is about {a} and {b}, two friends who went out together and faced busy traffic."),
        ("Why did they stop at the curb?",
         f"They stopped because the traffic at {place.label} was busy and loud. They wanted to cross only when it was safe."),
        ("What did the friends do for the little child?",
         f"They made a safe circle on the sidewalk and stayed nearby until the road opened. That kind choice helped the child feel less scared."),
    ]
    if outcome == "warm":
        qa.append((
            "How did the friends end the story?",
            f"They crossed together when it was safe and felt warm and happy afterward. Their friendship grew even kinder because they helped someone else first."
        ))
    else:
        qa.append((
            "How did the friends keep everyone safe?",
            f"They stepped back and waited until the traffic was not so close. The careful pause protected everyone and kept the moment calm."
        ))
    qa.append((
        "What did friendship change in the story?",
        f"Friendship changed the moment from noisy and nervous to gentle and caring. The friends looked after each other, and that made the street feel softer."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"traffic", "friendship", "crosswalk", "kindness", "wait"}
    out: list[tuple[str, str]] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(items)
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("crosswalk", "cars", "help", "Maya", "girl", "Noah", "boy"),
    StoryParams("school_gate", "buses", "wait", "Lila", "girl", "Eli", "boy"),
    StoryParams("corner_shop", "rush_hour", "share", "Owen", "boy", "Nina", "girl"),
]


def explain_rejection() -> str:
    return "(No story: that combination does not feel like a safe, heartwarming friendship moment with traffic.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for h in sorted(p.helpers):
            lines.append(asp.fact("helper", pid, h))
    for tid, t in TRAFFIC.items():
        lines.append(asp.fact("traffic", tid))
        lines.append(asp.fact("delay", tid, t.delay))
        lines.append(asp.fact("risky", tid))
    for bid, b in FRIENDSHIP_BEATS.items():
        lines.append(asp.fact("beat", bid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, T, B) :- place(P), traffic(T), beat(B), risky(T), helper(P, crossing).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH:")
        if a - b:
            print("  only in clingo:", sorted(a - b))
        if b - a:
            print("  only in python:", sorted(b - a))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming traffic friendship story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--traffic", choices=TRAFFIC)
    ap.add_argument("--beat", choices=FRIENDSHIP_BEATS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--gender-b", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.traffic is None or c[1] == args.traffic)
              and (args.beat is None or c[2] == args.beat)]
    if not combos:
        raise StoryError(explain_rejection())
    place, traffic, beat = rng.choice(sorted(combos))
    a_gender = args.gender_a or rng.choice(["girl", "boy"])
    b_gender = args.gender_b or ("boy" if a_gender == "girl" else "girl")
    a_name = args.name_a or rng.choice(GIRL_NAMES if a_gender == "girl" else BOY_NAMES)
    b_name = args.name_b or rng.choice([n for n in (GIRL_NAMES if b_gender == "girl" else BOY_NAMES) if n != a_name])
    return StoryParams(place, traffic, beat, a_name, a_gender, b_name, b_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TRAFFIC[params.traffic], FRIENDSHIP_BEATS[params.beat],
                 params.a_name, params.a_gender, params.b_name, params.b_gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, t, b in combos:
            print(f"  {p:12} {t:10} {b}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.a_name} & {p.b_name}: {p.place}, {p.traffic}, {p.beat}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
