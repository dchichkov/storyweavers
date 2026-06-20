#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/creak_absurd_friendship_inner_monologue_surprise_fable.py
=========================================================================================

A standalone story world for a tiny fable-like friendship tale built from the
seed words "creak" and "absurd", with inner monologue and surprise as the main
narrative instruments.

The domain is small on purpose: two animal friends cross a creaky old footbridge
to reach a quiet little hill, argue inside their own heads about a strange,
absurd rumor, and discover that the "surprise" is not danger but a kind act.
The turn is state-driven: fear, trust, noise, and kindness all change the path
the story takes.

The script supports:
- default random generation
- -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp

The world model uses typed entities with physical meters and emotional memes.
The prose is authored from state, not from a frozen paragraph template.

Run examples:
    python storyworlds/worlds/gpt-5.4-mini/creak_absurd_friendship_inner_monologue_surprise_fable.py
    python storyworlds/worlds/gpt-5.4-mini/creak_absurd_friendship_inner_monologue_surprise_fable.py --qa
    python storyworlds/worlds/gpt-5.4-mini/creak_absurd_friendship_inner_monologue_surprise_fable.py --all
    python storyworlds/worlds/gpt-5.4-mini/creak_absurd_friendship_inner_monologue_surprise_fable.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



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
    creaks: bool
    kind: str = "place"
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Friendship:
    id: str
    friends: tuple[str, str]
    bond: str
    trust: int
    shared_goal: str
    rumor: str
    note: str

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
class Surprise:
    id: str
    label: str
    hidden_kind: str
    reveals: str
    gentle: bool = True
    tags: set[str] = field(default_factory=set)

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
@dataclass
class StoryParams:
    friendship: str
    place: str
    surprise: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.places: dict[str, Place] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_place(self, place: Place) -> Place:
        self.places[place.id] = place
        return place

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
        clone.places = copy.deepcopy(self.places)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_creak(world: World) -> list[str]:
    out: list[str] = []
    for place in world.places.values():
        if place.meters["pressure"] < THRESHOLD:
            continue
        sig = ("creak", place.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        place.meters["noise"] += 1
        out.append("__creak__")
    return out


def _r_shared_nervousness(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["doubt"] += 1
        out.append("__doubt__")
    return out


CAUSAL_RULES = [
    Rule("creak", "physical", _r_creak),
    Rule("worry", "social", _r_shared_nervousness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def safe_belief(fb: Friendship) -> bool:
    return fb.trust >= SENSE_MIN


def surprise_is_kind(sur: Surprise) -> bool:
    return sur.gentle


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for fid, fb in FRIENDSHIPS.items():
        for sid, sur in SURPRISES.items():
            if safe_belief(fb) and surprise_is_kind(sur):
                combos.append((fid, sid))
    return combos


def _name_pool(kind: str) -> list[str]:
    return GIRL_NAMES if kind == "girl" else BOY_NAMES


def tell(fb: Friendship, place: Place, sur: Surprise,
         hero: str, hero_type: str, friend: str, friend_type: str) -> World:
    w = World()
    h = w.add(Entity(id=hero, kind="character", type=hero_type, role="hero", traits=["thoughtful"]))
    f = w.add(Entity(id=friend, kind="character", type=friend_type, role="friend", traits=["gentle"]))
    bridge = w.add_place(place)

    h.memes["trust"] = float(fb.trust)
    f.memes["trust"] = float(fb.trust)
    h.memes["friendship"] = 1.0
    f.memes["friendship"] = 1.0

    bridge.meters["pressure"] += 1
    if place.creaks:
        bridge.meters["pressure"] += 1

    w.say(
        f"Once, {h.id} and {f.id} were the best of friends. "
        f"They lived near {place.label}, and every day they walked there together."
    )
    w.say(
        f"The bridge had a small {sur.label} hidden in its boards. "
        f"The sign of the day was a long, lonely {fb.note}."
    )

    w.para()
    h.memes["curiosity"] += 1
    f.memes["curiosity"] += 1
    w.say(
        f"{h.id} paused and listened. The boards made a {('creak' if place.creaks else 'soft tap')}, "
        f"and in {h.pronoun('possessive')} head a small voice wondered, "
        f'"What if the old bridge is trying to warn us?"'
    )
    w.say(
        f"{f.id} also listened, and {f.pronoun('subject')} thought, "
        f'"That is absurd. An old bridge cannot speak. But it can still scare a small heart."'
    )

    bridge.meters["pressure"] += 1
    propagate(w, narrate=False)

    w.para()
    if safe_belief(fb):
        h.memes["worry"] += 1
        f.memes["worry"] += 1
        w.say(
            f"Their thoughts grew louder than the wind. "
            f"{h.id} imagined the bridge snapping, while {f.id} imagined a silly monster "
            f"with a broom for a tail."
        )
        if place.creaks:
            w.say(
                f"Then the bridge gave another {('creak' if place.creaks else 'tap')}, "
                f"as if it were clearing its throat."
            )
        w.say(
            f"{h.id} whispered, \"We should turn back.\" "
            f"{f.id} nodded, because friendship means hearing a friend's fear before joking about it."
        )

        w.para()
        w.say(
            f"At the far end of the bridge, {sur.label} waited. "
            f"Not trouble -- a surprise."
        )
        w.say(
            f"{h.id} and {f.id} found that {sur.reveals}. "
            f"It was meant for both of them, because someone had noticed how kindly they walked together."
        )
        w.say(
            f"The absurd rumor was only a story their own worries had invented. "
            f"In truth, the bridge held, the path was safe, and the surprise made them laugh."
        )
        w.say(
            f"They crossed home again with lighter steps, and the old bridge kept its secret: "
            f"even a creak can become a lesson, if friends listen instead of rushing."
        )
        outcome = "gentle"
    else:
        raise StoryError("(No story: this friendship is not calm enough for the fable-like turn.)")

    w.facts.update(
        friendship=fb,
        place=place,
        surprise=sur,
        hero=h,
        friend=f,
        outcome=outcome,
        creak=place.creaks,
        absurd=True,
    )
    return w


THEMES = {
    "fable": "a little fable of listening and trust",
}

PLACES = {
    "bridge": Place("bridge", "the old footbridge over the creek", True),
    "path": Place("path", "the boardwalk path by the garden", True),
    "orchard": Place("orchard", "the wooden gate at the orchard", True),
}

FRIENDSHIPS = {
    "close": Friendship(
        "close",
        ("hero", "friend"),
        bond="close",
        trust=6,
        shared_goal="reach the hill",
        rumor="the bridge might collapse",
        note="creak",
    ),
    "kind": Friendship(
        "kind",
        ("hero", "friend"),
        bond="kind",
        trust=5,
        shared_goal="carry the basket to the meadow",
        rumor="something impossible waits ahead",
        note="absurd",
    ),
    "steady": Friendship(
        "steady",
        ("hero", "friend"),
        bond="steady",
        trust=4,
        shared_goal="cross to the quiet bank",
        rumor="the path is hiding a secret",
        note="creak",
    ),
}

SURPRISES = {
    "gift": Surprise("gift", "a ribboned basket", "gift", "someone had left honey cakes and pears", True, {"gift"}),
    "note": Surprise("note", "a folded note", "note", "someone had written, 'For the best friends on the hill'", True, {"note"}),
    "lantern": Surprise("lantern", "a tiny lantern", "lantern", "the lantern glowed beside a bottle of warm milk", True, {"lantern"}),
}

GIRL_NAMES = ["Mira", "Lena", "Nora", "Ivy", "Ada", "Elin"]
BOY_NAMES = ["Owen", "Bram", "Theo", "Finn", "Perry", "Jude"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable-like friendship world.")
    ap.add_argument("--friendship", choices=FRIENDSHIPS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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
    if args.friendship and not safe_belief(FRIENDSHIPS[args.friendship]):
        raise StoryError("(No story: that friendship is too uneasy for this fable.)")
    if args.surprise and not surprise_is_kind(SURPRISES[args.surprise]):
        raise StoryError("(No story: the surprise must be gentle, not frightening.)")

    combos = [c for c in valid_combos()
              if (args.friendship is None or c[0] == args.friendship)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    friendship, surprise = rng.choice(sorted(combos))
    fb = FRIENDSHIPS[friendship]
    sur = SURPRISES[surprise]
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if hero_type == "girl" and rng.random() < 0.5 else "girl")
    hero = args.hero or rng.choice(_name_pool(hero_type))
    friend = args.friend or rng.choice([n for n in _name_pool(friend_type) if n != hero])
    place = args.place or rng.choice(list(PLACES))
    return StoryParams(friendship, place, surprise, hero, hero_type, friend, friend_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    fb: Friendship = f["friendship"]
    sur: Surprise = f["surprise"]
    return [
        f'Write a short fable for a child that includes the words "creak" and "absurd".',
        f"Tell a friendship story where two friends hear a {fb.note} and think a strange, absurd thought before discovering a surprise.",
        f"Write a gentle fable about {f['hero'].id} and {f['friend'].id} that ends with {sur.label} and a lesson about listening.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    fb: Friendship = f["friendship"]
    sur: Surprise = f["surprise"]
    place: Place = f["place"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {friend.id}, two friends who walk together near {place.label}. Their bond matters because the story turns on how they listen to each other."
        ),
        QAItem(
            question="What made the hero worry?",
            answer=f"The old bridge gave a creak, and {hero.id} imagined something bad might happen. That inner monologue made the moment feel bigger than the real danger."
        ),
        QAItem(
            question="Why did the friend call the thought absurd?",
            answer=f"{friend.id} thought the bridge could not truly speak or plan anything, so the idea sounded absurd. Even so, {friend.id} still respected the fear and did not laugh it away."
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"The surprise was {sur.label}, and it revealed that {sur.reveals}. It was a kind gift, not a trap, so the ending turned from worry to warmth."
        ),
        QAItem(
            question="How did friendship help in the story?",
            answer=f"Friendship helped because they stayed together, listened, and did not leave the other one alone on the bridge. Trust let them calm down enough to reach the surprise and understand it."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a creak sound like?",
            answer="A creak is a small, old wooden sound. It often happens when boards or doors move under weight."
        ),
        QAItem(
            question="What does absurd mean?",
            answer="Absurd means so strange or silly that it is hard to believe. It can make a thought feel funny or impossible."
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected. It may be a gift, a note, or a kind event that nobody saw coming."
        ),
        QAItem(
            question="What does friendship do in a fable?",
            answer="Friendship helps characters listen, trust, and choose wisely. In a fable, that kind of choice usually teaches a lesson."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    for p in world.places.values():
        meters = {k: v for k, v in p.meters.items() if v}
        lines.append(f"  {p.id:8} (place  ) meters={dict(meters)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for fid in FRIENDSHIPS:
        lines.append(asp.fact("friendship", fid))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        if s.gentle:
            lines.append(asp.fact("gentle", sid))
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.creaks:
            lines.append(asp.fact("creaks", pid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
safe_friendship(F) :- friendship(F), trust(F, T), sense_min(M), T >= M.
kind_surprise(S) :- surprise(S), gentle(S).
valid(F, P, S) :- safe_friendship(F), kind_surprise(S), place(P).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    import asp
    # add trust facts inline for parity check
    facts = []
    for fid, fb in FRIENDSHIPS.items():
        facts.append(asp.fact("trust", fid, fb.trust))
    prog = asp_facts() + "\n" + "\n".join(facts) + "\n" + ASP_RULES + "\n#show safe_friendship/1.\n#show kind_surprise/1.\n#show valid/3.\n"
    model = asp.one_model(prog)
    clingo_valid = sorted(set(asp.atoms(model, "valid")))
    python_valid = sorted(valid_combos())
    if clingo_valid != python_valid:
        rc = 1
        print("MISMATCH in valid combos:")
        print("  clingo:", clingo_valid)
        print("  python:", python_valid)
    else:
        print(f"OK: ASP parity for valid combos ({len(python_valid)} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(friendship=None, place=None, surprise=None, hero=None, hero_type=None, friend=None, friend_type=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def valid_story_params() -> list[StoryParams]:
    out = []
    for fid, sid in valid_combos():
        fb = FRIENDSHIPS[fid]
        # deterministic names for all runs
        hero_type = "girl"
        friend_type = "boy"
        out.append(StoryParams(fid, "bridge", sid, "Mira", hero_type, "Owen", friend_type))
    return out


def generate(params: StoryParams) -> StorySample:
    world = tell(
        FRIENDSHIPS[params.friendship],
        PLACES[params.place],
        SURPRISES[params.surprise],
        params.hero,
        params.hero_type,
        params.friend,
        params.friend_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


def explain_rejection() -> str:
    return "(No story: this combination is too uneasy or too frightening for a fable-like friendship tale.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in valid_story_params()]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
