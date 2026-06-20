#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/flunk_marq_kindness_myth.py
============================================================

A small mythic story world about Marq, a kindness trial, and what happens when
someone flunks before learning the gentler way.

The domain is intentionally tiny:
- a child or young helper named Marq
- a mythic hall, shrine, or bridge
- a kindness challenge involving sharing, helping, or making room
- a brief tension beat where Marq flunks
- a turn where kindness is tried in a real, physical way
- an ending image that proves the world changed

The story should feel like a miniature myth, but still read like a child-facing
tale with concrete actions and a clear end.
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
SENSE_MIN = 2
HUMBLE_TRAITS = {"gentle", "kind", "patient", "careful", "soft-hearted"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "priestess"}
        male = {"boy", "father", "dad", "man", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "priestess": "priestess", "priest": "priest"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    glow: str
    shelter: str
    crowding: int = 0
    kind: str = "place"

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Trial:
    id: str
    name: str
    verb: str
    need: str
    strain: str
    risk: str
    kind: str = "trial"

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    action: str
    glimmer: str
    generous: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_shame(world: World) -> list[str]:
    out = []
    marq = world.entities.get("Marq")
    shrine = world.entities.get("shrine")
    if not marq or not shrine:
        return out
    if marq.memes["defiance"] < THRESHOLD:
        return out
    sig = ("shame",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    shrine.meters["quiet"] += 1
    marq.memes["worry"] += 1
    out.append("__shame__")
    return out


def _r_kindness(world: World) -> list[str]:
    out = []
    giver = world.entities.get("Marq")
    helper = world.entities.get("Guide")
    if not giver or not helper:
        return out
    if giver.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.entities["bridge"].meters["glow"] += 1
    out.append("__glow__")
    return out


CAUSAL_RULES = [
    Rule("shame", "social", _r_shame),
    Rule("kindness", "social", _r_kindness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(trial: Trial, gift: Gift, place: Place) -> bool:
    return trial.need in {"help", "sharing", "space"} and gift.generous and place.id in {"hall", "bridge", "shrine"}


def sensible_gifts() -> list[Gift]:
    return [g for g in GIFTS.values() if g.generous]


def best_gift() -> Gift:
    return max(GIFTS.values(), key=lambda g: int(g.generous))


def outcome_of(params: "StoryParams") -> str:
    if params.kindness_first:
        return "softened"
    if params.trial == "feast":
        return "kindled"
    return "flunked"


def _do_trial(world: World, marq: Entity, trial: Trial, narrate: bool = True) -> None:
    marq.meters["strain"] += 1
    marq.memes["pressure"] += 1
    if trial.id == "feast":
        marq.memes["greed"] += 1
    propagate(world, narrate=narrate)


def predict_trial(world: World, trial: Trial) -> dict:
    sim = world.copy()
    _do_trial(sim, sim.get("Marq"), trial, narrate=False)
    return {"quiet": sim.get("shrine").meters["quiet"], "worry": sim.get("Marq").memes["worry"]}


def setup(world: World, marq: Entity, guide: Entity, place: Place, trial: Trial) -> None:
    marq.memes["hope"] += 1
    guide.memes["calm"] += 1
    world.say(f"In the old days of the river and stars, Marq came to {place.label}, where the air was {place.glow}.")
    world.say(f"There stood a {trial.name}, a small mythic test of {trial.need} and {trial.strain}.")
    world.say(f'Wise Guide said, "If you choose well, the path will open."')


def challenge(world: World, marq: Entity, trial: Trial, goal: str) -> None:
    marq.memes["desire"] += 1
    world.say(f"Marq looked at the {goal} and thought the reward would be easy to grab.")
    world.say(f'Yet the {trial.name} asked for {trial.need}, not haste.')


def flunk(world: World, marq: Entity, trial: Trial) -> None:
    marq.memes["defiance"] += 1
    world.say(f'Marq rushed ahead and flunked the {trial.name}.')
    world.say(f"The shrine grew still, and even the lanterns seemed to hold their breath.")


def warn(world: World, guide: Entity, marq: Entity, trial: Trial) -> None:
    pred = predict_trial(world, trial)
    guide.memes["concern"] += 1
    world.facts["predicted_quiet"] = pred["quiet"]
    world.say(
        f'{guide.id} held up a hand. "Not that way, Marq. That choice would leave the {trial.need} unfed, '
        f'and the old stones would stay quiet."'
    )


def redeem(world: World, marq: Entity, guide: Entity, gift: Gift, place: Place) -> None:
    marq.memes["kindness"] += 1
    marq.memes["defiance"] = 0.0
    world.get("bridge").meters["glow"] += 1
    world.say(
        f'Marq stopped, bowed his head, and chose kindness instead. '
        f'He {gift.action}, and {guide.label_word if guide.label_word else guide.id} smiled.'
    )
    world.say(
        f"{gift.glimmer.capitalize()}, the {place.shelter} brightened, and the river path opened like a door."
    )


def ending(world: World, marq: Entity, guide: Entity, place: Place) -> None:
    marq.memes["joy"] += 1
    guide.memes["joy"] += 1
    world.say(
        f"In the end, Marq crossed the {place.label} with open hands, and the old world answered with light."
    )
    world.say("That night, the stars looked a little closer, as if they had seen the kindness and approved.")


def tell(place: Place, trial: Trial, gift: Gift, kindness_first: bool = False) -> World:
    world = World()
    marq = world.add(Entity("Marq", kind="character", type="boy", role="seeker"))
    guide = world.add(Entity("Guide", kind="character", type="priestess", role="guide", label="the Guide"))
    shrine = world.add(Entity("shrine", label=place.label))
    bridge = world.add(Entity("bridge", label="the bridge"))
    world.add(shrine)
    world.add(bridge)
    world.facts["place"] = place
    world.facts["trial"] = trial
    world.facts["gift"] = gift
    world.facts["kindness_first"] = kindness_first

    setup(world, marq, guide, place, trial)
    world.para()
    challenge(world, marq, trial, place.shelter)
    warn(world, guide, marq, trial)
    if kindness_first:
        redeem(world, marq, guide, gift, place)
        ending(world, marq, guide, place)
        outcome = "softened"
    else:
        flunk(world, marq, trial)
        world.para()
        redeem(world, marq, guide, gift, place)
        ending(world, marq, guide, place)
        outcome = "flunked"
    world.facts.update(marq=marq, guide=guide, outcome=outcome)
    return world


PLACES = {
    "hall": Place("hall", "the stone hall", "blue with torchlight", "doorway"),
    "shrine": Place("shrine", "the moon shrine", "silver with hush", "inner room"),
    "bridge": Place("bridge", "the river bridge", "bright with morning mist", "riverbank"),
}

TRIALS = {
    "feast": Trial("feast", "the Feast Trial", "share", "sharing", "hunger", "greed"),
    "gate": Trial("gate", "the Gate Trial", "make room", "space", "patience", "bumping"),
    "well": Trial("well", "the Well Trial", "help carry water", "help", "strength", "struggle"),
}

GIFTS = {
    "bread": Gift("bread", "round bread", "a loaf of bread", "shared the bread with the hungry child", "Warm crumbs")
,
    "lamp": Gift("lamp", "small lamp", "a small lamp", "lit the lamp for the dark path", "Soft gold"),
    "rope": Gift("rope", "river rope", "a rope", "held the rope steady for the Guide", "The line held"),
}

TRAITS = ["gentle", "kind", "patient", "careful", "soft-hearted"]


@dataclass
@dataclass
class StoryParams:
    place: str
    trial: str
    gift: str
    trait: str
    kindness_first: bool = False
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TRIALS:
            for g in GIFTS:
                if reasonableness_gate(TRIALS[t], GIFTS[g], PLACES[p]):
                    combos.append((p, t, g))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny myth storyworld about Marq, flunking, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--kindness-first", action="store_true")
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
    if args.trial and args.gift and not reasonableness_gate(TRIALS[args.trial], GIFTS[args.gift], PLACES[args.place or "hall"]):
        raise StoryError("That trial and gift do not fit together in this myth.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.trial is None or c[1] == args.trial)
              and (args.gift is None or c[2] == args.gift)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trial, gift = rng.choice(sorted(combos))
    trait = args.trait or rng.choice(TRAITS)
    kindness_first = args.kindness_first or (trait in HUMBLE_TRAITS and rng.random() < 0.25)
    return StoryParams(place, trial, gift, trait, kindness_first)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a small child that includes the word "Marq" and the word "flunk".',
        f"Tell a gentle myth where Marq comes to {f['place'].label} and faces {f['trial'].name}, then learns kindness.",
        f'Write a story in a myth style about a child named Marq who flunks first, then makes the right choice with a small gift.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    trial: Trial = f["trial"]
    place: Place = f["place"]
    gift: Gift = f["gift"]
    out = f["outcome"]
    qa = [
        ("Who is the story about?",
         "It is about Marq, a young helper in an old myth, and the Guide who teaches him the kinder path."),
        ("What did Marq have to do?",
         f"Marq had to face {trial.name} at {place.label}. The trial asked for {trial.need}, not rushing ahead."),
        ("What does flunk mean in this story?",
         "It means Marq failed the trial the first time. He chose the wrong move before he understood the kinder way.")
    ]
    if out == "flunked":
        qa.append((
            "What happened after Marq flunked?",
            f"The Guide pointed to {gift.phrase} and showed Marq how to repair the mistake. Then the story turned from shame to kindness."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with Marq choosing kindness and the old place glowing again. The ending proves the change because {gift.glimmer.lower()} returned to the path."
    ))
    return qa


WORLD_KNOWLEDGE = {
    "kindness": [
        ("What is kindness?",
         "Kindness is being gentle and helpful to someone else. It means you try to make the world better, not harder, for them.")
    ],
    "flunk": [
        ("What does flunk mean?",
         "Flunk means to fail a test or challenge. If you flunk, you can still learn and try again.")
    ],
    "bridge": [
        ("What is a bridge?",
         "A bridge is a path that helps people cross over water, roads, or other gaps."),
    ],
    "shrine": [
        ("What is a shrine?",
         "A shrine is a special place where people go to honor something important.")
    ],
    "lamp": [
        ("What does a lamp do?",
         "A lamp makes light so people can see in the dark without needing a fire.")
    ],
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"kindness", "flunk", "bridge", "shrine", "lamp"}
    out = []
    for tag in tags:
        out.extend(WORLD_KNOWLEDGE.get(tag, []))
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hall", "feast", "bread", "gentle", False),
    StoryParams("shrine", "gate", "lamp", "patient", False),
    StoryParams("bridge", "well", "rope", "kind", True),
]


def explain_response(gift: Gift) -> str:
    return f"(Refusing gift '{gift.id}': it is not a gentle enough answer for this myth.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid, t in TRIALS.items():
        lines.append(asp.fact("trial", tid))
        lines.append(asp.fact("need", tid, t.need))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        if g.generous:
            lines.append(asp.fact("generous", gid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,G) :- place(P), trial(T), gift(G), need(T,N), need_ok(N), generous(G).
need_ok(sharing).
need_ok(space).
need_ok(help).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos()")
        rc = 1
    try:
        s = generate(resolve_params(argparse.Namespace(place=None, trial=None, gift=None, trait=None, kindness_first=False), random.Random(1)))
        _ = s.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TRIALS[params.trial], GIFTS[params.gift], params.kindness_first)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible triples.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
