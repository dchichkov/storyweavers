#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/peddle_siamese_lesson_learned_friendship_suspense_mystery.py
=============================================================================================

A compact mystery storyworld for a child, a bike, a Siamese cat, a missing item,
and a lesson learned through friendship and suspense.

Seed words:
- peddle
- siamese

Style:
- Mystery

Features:
- Lesson Learned
- Friendship
- Suspense
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "cat":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    dark_spot: str
    clue_spot: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class MysteryItem:
    id: str
    label: str
    phrase: str
    hidden_in: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Ride:
    id: str
    label: str
    phrase: str
    sound: str
    speed: int
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["searching"] >= THRESHOLD and ("cat" in e.tags or e.role == "guide"):
            sig = ("suspense", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            for child in list(world.entities.values()):
                if child.role in {"hero", "friend"}:
                    child.memes["unease"] += 1
            out.append("__suspense__")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if not hero or not friend:
        return out
    if hero.memes["trust"] >= THRESHOLD and friend.memes["helped"] >= THRESHOLD:
        sig = ("friendship",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["friendship"] += 1
            friend.memes["friendship"] += 1
            out.append("__friendship__")
    return out


CAUSAL_RULES = [Rule("suspense", _r_suspense), Rule("friendship", _r_friendship)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def reasonableness_ok(ride: Ride, place: Place, item: MysteryItem) -> bool:
    return "mystery" in place.tags and "cat" in item.tags and ride.speed >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for rid, ride in RIDES.items():
            for iid, item in ITEMS.items():
                if reasonableness_ok(ride, place, item):
                    combos.append((pid, rid, iid))
    return combos


def _mystery_title(item: MysteryItem) -> str:
    return item.label


def _search(world: World, hero: Entity, friend: Entity, ride: Ride, place: Place) -> None:
    hero.meters["searching"] += 1
    friend.meters["searching"] += 1
    world.say(
        f"That evening, {hero.id} and {friend.id} rolled into {place.label} on {ride.phrase}. "
        f"The wheels made a soft {ride.sound}, and the shadows around {place.dark_spot} looked extra long."
    )


def _find_clue(world: World, guide: Entity, item: MysteryItem, place: Place) -> None:
    guide.meters["searching"] += 1
    guide.tags.add("guide")
    world.say(
        f"At the edge of {place.clue_spot}, a Siamese cat sat very still. "
        f"It stared at a tiny clue: {item.phrase}, half-hidden where the garden leaves curled."
    )


def _warn(world: World, friend: Entity, hero: Entity) -> None:
    friend.memes["helped"] += 1
    friend.memes["trust"] += 1
    hero.memes["trust"] += 1
    world.say(
        f'{friend.id} leaned close and whispered, "{hero.id}, we should stay together. '
        f'This feels like a real mystery."'
    )


def _discover(world: World, hero: Entity, friend: Entity, item: MysteryItem, place: Place) -> None:
    hero.meters["found"] += 1
    friend.meters["found"] += 1
    world.say(
        f"Following the cat, they peeked behind the old pot and found the missing {_mystery_title(item)}. "
        f"It had been tucked away in {item.hidden_in} all along."
    )
    world.say(
        f"{hero.id} laughed in relief. {friend.id} smiled too, and the Siamese cat blinked as if it had known the answer."
    )


def _lesson(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    hero.memes["warmth"] += 1
    friend.memes["warmth"] += 1
    world.say(
        f"On the ride home, {hero.id} said the best clue was not the hidden thing at all, but "
        f"how {friend.id} had stayed nearby and helped. They promised to ask first before borrowing."
    )
    world.say(
        f"By the time they reached the gate, the mystery felt smaller and the friendship felt bigger."
    )


def tell(place: Place, ride: Ride, item: MysteryItem, hero_name: str, friend_name: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type="girl", role="friend"))
    guide = world.add(Entity(id="SiameseCat", kind="character", type="cat", role="guide", label="a Siamese cat", tags={"cat", "siamese"}))
    hero.memes["trust"] = 1.0
    friend.memes["helped"] = 0.0

    world.say(
        f"{hero.id} and {friend.id} were looking for the missing {item.label}. "
        f"The note said to search near {place.dark_spot}, but nobody knew what was waiting there."
    )
    world.para()
    _search(world, hero, friend, ride, place)
    _warn(world, friend, hero)
    _find_clue(world, guide, item, place)
    propagate(world, narrate=True)
    world.para()
    _discover(world, hero, friend, item, place)
    _lesson(world, hero, friend)

    world.facts.update(
        hero=hero, friend=friend, guide=guide, place=place, ride=ride, item=item
    )
    return world


PLACES = {
    "garden": Place(
        id="garden",
        label="the garden",
        dark_spot="the tool shed by the fence",
        clue_spot="the rose bush path",
        tags={"mystery", "garden"},
    ),
    "yard": Place(
        id="yard",
        label="the backyard",
        dark_spot="the shadow under the porch",
        clue_spot="the stepping-stone trail",
        tags={"mystery", "yard"},
    ),
}

RIDES = {
    "tricycle": Ride(
        id="tricycle",
        label="a little tricycle",
        phrase="a little tricycle",
        sound="pedal-pedal",
        speed=2,
        tags={"ride"},
    ),
    "bike": Ride(
        id="bike",
        label="a small bike",
        phrase="a small bike",
        sound="click-clack",
        speed=3,
        tags={"ride"},
    ),
}

ITEMS = {
    "bell": MysteryItem(
        id="bell",
        label="silver bell",
        phrase="a silver bell",
        hidden_in="a flowerpot",
        tags={"cat", "clue"},
    ),
    "ribbon": MysteryItem(
        id="ribbon",
        label="blue ribbon",
        phrase="a blue ribbon",
        hidden_in="the birdhouse",
        tags={"cat", "clue"},
    ),
}


@dataclass
class StoryParams:
    place: str
    ride: str
    item: str
    hero_name: str = "Milo"
    friend_name: str = "Nina"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CURATED = [
    StoryParams(place="garden", ride="tricycle", item="bell", hero_name="Milo", friend_name="Nina"),
    StoryParams(place="yard", ride="bike", item="ribbon", hero_name="Owen", friend_name="Lena"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A mystery storyworld about a child, a Siamese cat, and a lesson learned."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ride", choices=RIDES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
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
              and (args.ride is None or c[1] == args.ride)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, ride, item = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        ride=ride,
        item=item,
        hero_name=args.hero_name or rng.choice(["Milo", "Owen", "Theo", "Finn"]),
        friend_name=args.friend_name or rng.choice(["Nina", "Lena", "Ivy", "June"]),
        seed=None,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mystery story for a young child that includes the words "peddle" and "siamese".',
        f"Tell a friendship story where {f['hero'].id} and {f['friend'].id} search for a missing item and follow a Siamese cat's clue.",
        f"Write a suspenseful little mystery where a child pedals around {f['place'].label} and learns a lesson by the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, place, ride, item = f["hero"], f["friend"], f["place"], f["ride"], f["item"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, who solve a small mystery together. A Siamese cat helps lead them toward the answer."),
        ("What were they looking for?",
         f"They were looking for the missing {item.label}. They found it after following clues through {place.label}."),
        ("Why was the story suspenseful?",
         f"They did not know what was hidden near the dark spot, so every clue mattered. The quiet ride and the waiting cat made the search feel tense until the answer appeared."),
        ("What lesson did the child learn?",
         f"{hero.id} learned that it is better to stay close to a friend and ask before borrowing. The story ends with trust and kindness instead of confusion."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does peddle mean?",
         "To peddle means to push the pedals on a bike or tricycle so it moves forward."),
        ("What is a Siamese cat?",
         "A Siamese cat is a cat with a sleek body and bright-looking eyes. People often recognize it by its gentle, curious face."),
        ("What is a mystery story?",
         "A mystery story is a story where something is hidden or unexplained at first. The characters look for clues until they understand what happened."),
        ("Why do friends help each other in a mystery?",
         "Friends help because two sets of eyes can spot more clues than one. They also make the search feel braver and kinder."),
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, R, I) :- place(P), ride(R), item(I), mystery_place(P), cat_item(I), speed(R, S), S >= 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if "mystery" in p.tags:
            lines.append(asp.fact("mystery_place", pid))
    for rid, r in RIDES.items():
        lines.append(asp.fact("ride", rid))
        lines.append(asp.fact("speed", rid, r.speed))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if "cat" in it.tags:
            lines.append(asp.fact("cat_item", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP valid combos differ from Python.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        _ = sample.to_json()
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"MISMATCH: generate smoke test failed: {exc}")
    if ok:
        print("OK: ASP parity and generate smoke test passed.")
        return 0
    return 1


def generate(params: StoryParams) -> StorySample:
    for key, table in (("place", PLACES), ("ride", RIDES), ("item", ITEMS)):
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)!r}")
    world = tell(
        PLACES[params.place],
        RIDES[params.ride],
        ITEMS[params.item],
        params.hero_name,
        params.friend_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        for p, r, i in combos:
            print(f"  {p} {r} {i}")
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
