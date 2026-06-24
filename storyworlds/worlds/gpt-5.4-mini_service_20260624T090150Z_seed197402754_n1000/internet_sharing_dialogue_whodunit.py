#!/usr/bin/env python3
"""
A whodunit storyworld about sharing an internet connection.

Premise:
- A small cast shares one internet connection in a quiet place.
- Something goes wrong: the connection slows or disappears.
- The characters talk, suspect each other, and investigate.
- The ending reveals who caused the trouble, using world state and dialogue.

The world is intentionally tiny: one connection, a few devices, a small set of
possible causes, and a clear reveal.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    connected_to: Optional[str] = None
    shared: bool = False
    secret: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    label: str
    quiet: bool = True
    shared: bool = True


@dataclass
class InternetPlan:
    label: str
    speed: int
    data_limit: int
    shared_with: set[str] = field(default_factory=set)


@dataclass
class SuspectProfile:
    id: str
    type: str
    trait: str


class World:
    def __init__(self, place: Place, plan: InternetPlan):
        self.place = place
        self.plan = plan
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


@dataclass
class StoryParams:
    place: str
    plan: str
    culprit: str
    victim: str
    witness: str
    seed: Optional[int] = None


PLACES = {
    "apartment": Place(label="the apartment", quiet=True, shared=True),
    "library": Place(label="the library", quiet=True, shared=True),
    "boat": Place(label="the boat", quiet=True, shared=True),
}

PLANS = {
    "tiny": InternetPlan(label="a tiny plan", speed=3, data_limit=3),
    "small": InternetPlan(label="a small plan", speed=6, data_limit=6),
    "family": InternetPlan(label="a family plan", speed=10, data_limit=10),
}

HEROES = [
    SuspectProfile("Nina", "girl", "curious"),
    SuspectProfile("Milo", "boy", "careful"),
    SuspectProfile("June", "girl", "bright"),
    SuspectProfile("Owen", "boy", "quiet"),
]

DEVICE_LABELS = {
    "phone": "a phone",
    "tablet": "a tablet",
    "laptop": "a laptop",
    "game": "a game console",
}

DEVICE_TYPES = list(DEVICE_LABELS.keys())


class StoryState:
    def __init__(self):
        self.noise: float = 0.0
        self.slow: float = 0.0
        self.data_used: int = 0
        self.accusation: str = ""
        self.reveal: str = ""
        self.resolved: bool = False


def _use_data(world: World, actor: Entity, amount: int, reason: str) -> None:
    actor.meters["usage"] = actor.meters.get("usage", 0) + amount
    world.plan.speed = max(1, world.plan.speed - amount // 2)
    world.plan.data_limit = max(0, world.plan.data_limit - amount)
    world.facts["data_used"] = world.facts.get("data_used", 0) + amount
    world.say(f"{actor.id} kept {reason}, and the connection felt slower.")


def _share(world: World, sharer: Entity, other: Entity) -> None:
    sharer.memes["generous"] = sharer.memes.get("generous", 0) + 1
    other.connected_to = sharer.id
    world.say(f'"Here," {sharer.id} said. "You can use my internet too."')


def _witness_dialogue(world: World, witness: Entity, suspect: Entity) -> None:
    world.say(
        f'"Did you touch the router?" {witness.id} asked. '
        f'"No," {suspect.id} said. "I only used the internet."'
    )


def _detective_beat(world: World, detective: Entity, suspect: Entity, clue: str) -> None:
    world.say(
        f'{detective.id} looked at the clue and said, "That part matches {suspect.id}." '
        f'"It was {clue}, not a broken wire."'
    )


def _cause_slowdown(world: World, culprit: Entity, device: Entity, amount: int) -> None:
    if ("cause", culprit.id) in world.fired:
        return
    world.fired.add(("cause", culprit.id))
    culprit.memes["nervous"] = culprit.memes.get("nervous", 0) + 1
    culprit.meters["usage"] = culprit.meters.get("usage", 0) + amount
    device.meters["downloads"] = device.meters.get("downloads", 0) + amount
    world.facts["slowdown_cause"] = culprit.id
    world.facts["clue"] = device.label
    world.say(f"{culprit.id} had been using {device.label} the whole time.")


def tell(place: Place, plan: InternetPlan, culprit: Entity, victim: Entity, witness: Entity) -> World:
    world = World(place, plan)

    router = world.add(Entity(id="Router", kind="thing", type="router", label="the router", secret=True))
    detective = world.add(Entity(id="Ari", kind="character", type="boy", label="Ari"))
    culprit = world.add(culprit)
    victim = world.add(victim)
    witness = world.add(witness)

    phone = world.add(Entity(id="Phone", kind="thing", type="phone", label="a phone", owner=victim.id))
    tablet = world.add(Entity(id="Tablet", kind="thing", type="tablet", label="a tablet", owner=witness.id))
    laptop = world.add(Entity(id="Laptop", kind="thing", type="laptop", label="a laptop", owner=culprit.id))

    world.facts.update(
        router=router,
        detective=detective,
        culprit=culprit,
        victim=victim,
        witness=witness,
        phone=phone,
        tablet=tablet,
        laptop=laptop,
        place=place,
        plan=plan,
    )

    world.say(f"At {place.label}, one little internet plan served everyone.")
    world.say(f"{victim.id} wanted to share it so the room could stay happy.")
    _share(world, victim, witness)
    _share(world, victim, culprit)

    world.para()
    world.say(f"Then the pages began to crawl.")
    world.say(f'"The internet is slow," {witness.id} said. "Who is using it so much?"')
    world.say(f'"Not me," {culprit.id} said at once.')

    _use_data(world, culprit, 4, "streaming videos")
    _cause_slowdown(world, culprit, laptop, 4)

    world.say(f'"I only asked for one little thing," {victim.id} said.')
    world.say(f'"One little thing?" {detective.id} repeated. "That does not sound little to a tiny plan."')

    world.para()
    _witness_dialogue(world, witness, culprit)
    world.say(f"{detective.id} looked at the laptop and frowned.")
    _detective_beat(world, detective, culprit, "the laptop had the biggest usage")
    world.say(f'"The clue is simple," {detective.id} said. "The one who said " +
               f'"No" was the one who was hiding the most."')
    world.say(f"{culprit.id} looked down and finally nodded.")
    world.say(f'"I wanted to finish my videos," {culprit.id} said, "but I should have asked first."')

    world.para()
    culprit.memes["guilty"] = culprit.memes.get("guilty", 0) + 1
    victim.memes["relieved"] = victim.memes.get("relieved", 0) + 1
    witness.memes["relieved"] = witness.memes.get("relieved", 0) + 1
    world.facts["resolved"] = True
    world.say(f"{victim.id} shared the plan more carefully after that.")
    world.say(f"{culprit.id} waited for a turn, and the connection became smooth again.")
    world.say(f"In the end, the room was quiet, the internet worked, and the mystery was solved.")

    return world


def _pick(rng: random.Random, items: list[str]) -> str:
    return rng.choice(items)


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out = []
    for place in PLACES:
        for plan in PLANS:
            for culprit in [h.id for h in HEROES]:
                for victim in [h.id for h in HEROES if h.id != culprit]:
                    for witness in [h.id for h in HEROES if h.id not in {culprit, victim}]:
                        if PLANS[plan].data_limit >= 3:
                            out.append((place, plan, culprit, victim, witness))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A whodunit about sharing internet.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--culprit", choices=[h.id for h in HEROES])
    ap.add_argument("--victim", choices=[h.id for h in HEROES])
    ap.add_argument("--witness", choices=[h.id for h in HEROES])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    culprits = [h.id for h in HEROES]
    victims = [h.id for h in HEROES]
    witnesses = [h.id for h in HEROES]
    place = args.place or _pick(rng, list(PLACES))
    plan = args.plan or _pick(rng, list(PLANS))
    culprit = args.culprit or _pick(rng, culprits)
    victim_choices = [x for x in victims if x != culprit]
    victim = args.victim or _pick(rng, victim_choices)
    witness_choices = [x for x in witnesses if x not in {culprit, victim}]
    if not witness_choices:
        raise StoryError("Need three different characters for a whodunit.")
    witness = args.witness or _pick(rng, witness_choices)
    return StoryParams(place=place, plan=plan, culprit=culprit, victim=victim, witness=witness)


def generate(params: StoryParams) -> StorySample:
    culprit = next(h for h in HEROES if h.id == params.culprit)
    victim = next(h for h in HEROES if h.id == params.victim)
    witness = next(h for h in HEROES if h.id == params.witness)
    world = tell(PLACES[params.place], PLANS[params.plan],
                 Entity(id=culprit.id, kind="character", type=culprit.type, label=culprit.id),
                 Entity(id=victim.id, kind="character", type=victim.type, label=victim.id),
                 Entity(id=witness.id, kind="character", type=witness.type, label=witness.id))
    story = world.render()
    prompts = [
        "Write a short whodunit story about children sharing an internet connection.",
        f"Tell a mystery where {params.victim} shares the internet but someone else causes the slowdown.",
        "Write a gentle dialogue-driven mystery where the clue is a device using too much internet.",
    ]
    story_qa = [
        QAItem(question=f"Who shared the internet at {PLACES[params.place].label}?", answer=f"{params.victim} shared the internet with everyone."),
        QAItem(question="Why did the internet get slow?", answer=f"It got slow because {params.culprit} kept using the internet on a laptop."),
        QAItem(question="How was the mystery solved?", answer=f"{params.witness} and Ari noticed the laptop had the biggest usage, so {params.culprit} was revealed."),
    ]
    world_qa = [
        QAItem(question="What is the internet?", answer="The internet is a network that lets people send messages, look at pages, and use online things."),
        QAItem(question="What does it mean to share?", answer="To share means to let more than one person use the same thing."),
        QAItem(question="Why can a connection get slow?", answer="A connection can get slow when many people or devices use a lot of data at once."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
plan(N) :- internet_plan(N).
character(C) :- hero(C).
slowdown(C) :- uses(C,D), data_heavy(D), culprit(C).
guilty(C) :- slowdown(C), says_no(C).
solved :- guilty(C), notices_clue(D), device(D), biggest_usage(D).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("setting", p))
    for p in PLANS:
        lines.append(asp.fact("internet_plan", p))
    for h in HEROES:
        lines.append(asp.fact("hero", h.id))
    lines.append(asp.fact("data_heavy", "laptop"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show place/1."))
    if model is None:
        print("No ASP model.")
        return 1
    print("OK: ASP available.")
    return 0


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
    StoryParams(place="library", plan="tiny", culprit="Nina", victim="Milo", witness="June"),
    StoryParams(place="apartment", plan="small", culprit="Owen", victim="June", witness="Nina"),
    StoryParams(place="boat", plan="family", culprit="Milo", victim="Owen", witness="June"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show place/1.\n#show solved/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
