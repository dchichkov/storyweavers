#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chance_sharing_slice_of_life.py
===============================================================

A standalone storyworld for a small slice-of-life domain built from the seed
words "chance" and the feature "sharing".

Premise
-------
Two children are sharing a small everyday thing — a snack, a toy, or an umbrella —
when a little chance twist changes who needs it most. The story stays grounded in
ordinary life: asking politely, noticing someone else, making room, and ending
with a concrete image of sharing done well.

The world model tracks:
- physical meters: how much of the shared item is available, needed, or given
- emotional memes: wanting, fairness, worry, kindness, relief, gratitude

The story branches into a few classic outcomes:
- the children share smoothly
- one child hesitates, then shares after a gentle nudge
- a chance event creates a small problem, and the sharing adapts
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    shareable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Scenario:
    place: str
    shared_item: str
    chance_event: str
    need: str
    turn: str
    ending_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["shared"] < THRESHOLD:
            continue
        sig = ("relief", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["relief"] += 1
        e.memes["kindness"] += 1
        out.append("__relief__")
    return out


def _r_gratitude(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["relief"] < THRESHOLD:
            continue
        sig = ("gratitude", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["gratitude"] += 1
        out.append("__gratitude__")
    return out


CAUSAL_RULES = [Rule("relief", "social", _r_relief), Rule("gratitude", "social", _r_gratitude)]


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


@dataclass
@dataclass
class StoryParams:
    place: str
    shared_item: str
    chance_event: str
    need: str
    turn: str
    ending_image: str
    child_a: str
    child_b: str
    child_a_gender: str
    child_b_gender: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


PLACES = {
    "kitchen": "the kitchen table",
    "park_bench": "the park bench",
    "playroom": "the playroom rug",
    "bus_stop": "the bus stop bench",
}

SHARED_ITEMS = {
    "cookies": ("a small plate of cookies", "cookies", True),
    "crayons": ("a box of crayons", "crayons", True),
    "umbrella": ("a blue umbrella", "umbrella", True),
    "book": ("a picture book", "book", True),
}

CHANCE_EVENTS = {
    "rain_sprinkle": "A little sprinkle of rain started to fall.",
    "friend_arrives": "A friend came by and wanted to look too.",
    "wind_gust": "A gust of wind nudged the shared thing closer to the edge.",
}

NEEDS = {
    "stay_dry": "stay dry",
    "draw": "draw a picture",
    "read": "read the next page",
    "walk": "walk home together",
}

TURNS = {
    "gentle_offer": "so the children made room and took turns",
    "split_share": "so they split it into two little parts and shared fairly",
    "ask_help": "so they asked a grown-up for help and found a better way to share",
}

ENDING_IMAGES = {
    "umbrella": "one child held the handle while the other tucked close underneath the dry side",
    "cookies": "two crumbs sat on the plate while both children smiled with sticky fingers",
    "crayons": "the box stayed open between them, with half the colors on one side and half on the other",
    "book": "one child held the left page while the other pointed at the right page",
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Maya", "Anna"]
BOY_NAMES = ["Leo", "Ben", "Noah", "Sam", "Theo", "Finn", "Max", "Eli"]
TRAITS = ["careful", "thoughtful", "quiet", "kind", "curious", "patient"]


class ScenarioWorld:
    pass


def tell(params: StoryParams) -> World:
    world = World()
    a = world.add(Entity(id=params.child_a, kind="character", type=params.child_a_gender,
                         role="sharer", traits=[rng_trait(params.child_a)]))
    b = world.add(Entity(id=params.child_b, kind="character", type=params.child_b_gender,
                         role="sharer", traits=[rng_trait(params.child_b)]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    item_label, item_word, shareable = SHARED_ITEMS[params.shared_item]
    item = world.add(Entity(id="shared_item", type="thing", label=item_word, shareable=shareable))

    a.memes["want"] += 1
    b.memes["want"] += 1
    item.meters["available"] = 2.0
    world.say(
        f"On a quiet day at {PLACES[params.place]}, {a.id} and {b.id} found {item_label}. "
        f"They both wanted a chance to enjoy it."
    )
    world.say(f"{a.id} liked to {params.need}, and {b.id} liked to {params.need} too.")

    world.para()
    world.say(CHANCE_EVENTS[params.chance_event])

    if params.chance_event == "friend_arrives":
        b.memes["worry"] += 1
        world.say(
            f"{b.id} looked at the extra face and then back at {item.label_word}, "
            f"wondering whether there would be enough to go around."
        )
    elif params.chance_event == "rain_sprinkle":
        if params.shared_item == "umbrella":
            a.memes["worry"] += 1
            world.say(f"{a.id} glanced up and noticed the umbrella was suddenly needed right away.")
        else:
            world.say("The little change in the air made the day feel different, but the children stayed calm.")
    else:
        world.say("The breeze only moved things a little, but it gave them a small idea.")

    world.para()
    if params.turn == "ask_help":
        parent.memes["helpful"] += 1
        world.say(
            f"{a.id} and {b.id} paused and asked {parent.label_word} what to do. "
            f"{parent.label_word.capitalize()} showed them a simple way to share without fuss."
        )
    elif params.turn == "split_share":
        world.say(
            f"They smiled at each other, then decided to split the good part into two small parts "
            f"so each child had a turn."
        )
    else:
        world.say(
            f"{a.id} held back for a moment, then made room, and {b.id} did the same."
        )

    item.meters["shared"] += 1
    propagate(world, narrate=False)

    if params.shared_item == "umbrella":
        a.meters["dry"] += 1
        b.meters["dry"] += 1
    else:
        a.meters["happy"] += 1
        b.meters["happy"] += 1

    world.say(
        f"In the end, {params.ending_image}, and the day felt easy again."
    )
    world.say(
        f"The shared thing did its job, and the children kept their good mood as they went on with their day."
    )

    world.facts.update(
        child_a=a, child_b=b, parent=parent, item=item, params=params,
        outcome="shared", chance=params.chance_event, turn=params.turn
    )
    return world


def rng_trait(name: str) -> str:
    return TRAITS[sum(ord(c) for c in name) % len(TRAITS)]


def random_choice(rng: random.Random, seq: list[str]) -> str:
    return rng.choice(seq)


def build_scenario(rng: random.Random) -> StoryParams:
    place = rng.choice(list(PLACES))
    shared_item = rng.choice(list(SHARED_ITEMS))
    chance_event = rng.choice(list(CHANCE_EVENTS))
    need = rng.choice(list(NEEDS))
    turn = rng.choice(list(TURNS))
    ending_image = ENDING_IMAGES[shared_item]
    a_name = rng.choice(GIRL_NAMES + BOY_NAMES)
    b_name = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != a_name])
    a_gender = "girl" if a_name in GIRL_NAMES else "boy"
    b_gender = "girl" if b_name in GIRL_NAMES else "boy"
    parent = rng.choice(["mother", "father"])
    return StoryParams(place, shared_item, chance_event, need, turn, ending_image,
                       a_name, b_name, a_gender, b_gender, parent)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for s in SHARED_ITEMS:
            for c in CHANCE_EVENTS:
                if s == "umbrella" or c != "rain_sprinkle":
                    combos.append((p, s, c))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f'Write a slice-of-life story for a young child that includes the word "chance" and focuses on sharing {p.shared_item}.',
        f"Tell a calm everyday story where {p.child_a} and {p.child_b} get a chance to share {SHARED_ITEMS[p.shared_item][0]}.",
        f"Write a gentle story about two children, a small chance event, and a kind sharing ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    p: StoryParams = f["params"]
    a, b = f["child_a"], f["child_b"]
    item_label = SHARED_ITEMS[p.shared_item][1]
    return [
        ("Who is the story about?",
         f"It is about {a.id} and {b.id}, two children who were spending a quiet day together."),
        ("What did they share?",
         f"They shared {SHARED_ITEMS[p.shared_item][0]}. That gave both children a chance to enjoy it."),
        ("What changed in the middle of the story?",
         f"A small chance event happened, and the children had to notice each other and make room. "
         f"Because of that, they chose a kinder way to use the shared thing."),
        ("How did the story end?",
         f"It ended with {p.ending_image}. The sharing worked, so the day stayed calm and pleasant."),
    ]


WORLD_KNOWLEDGE = {
    "chance": [("What does chance mean?",
                "Chance means something may happen, but nobody knows for sure until it does.")],
    "sharing": [("What is sharing?",
                 "Sharing means letting someone else use or enjoy something too. It is a kind thing to do.")],
    "umbrella": [("What is an umbrella for?",
                  "An umbrella helps keep people dry when it rains.")],
    "cookies": [("Why do people share snacks?",
                 "People share snacks so everyone can have some and nobody feels left out.")],
    "crayons": [("What are crayons for?",
                 "Crayons are used for drawing and coloring pictures.")],
    "book": [("Why do people share books?",
               "People share books so they can read together and look at the pictures together.")],
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    p: StoryParams = world.facts["params"]
    items = ["chance", "sharing", p.shared_item]
    out: list[tuple[str, str]] = []
    for k in items:
        out.extend(WORLD_KNOWLEDGE.get(k, []))
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
    StoryParams("kitchen", "cookies", "friend_arrives", "read", "split_share", ENDING_IMAGES["cookies"],
                "Mia", "Nora", "girl", "girl", "mother"),
    StoryParams("playroom", "crayons", "wind_gust", "draw", "gentle_offer", ENDING_IMAGES["crayons"],
                "Leo", "Sam", "boy", "boy", "father"),
    StoryParams("bus_stop", "umbrella", "rain_sprinkle", "stay_dry", "ask_help", ENDING_IMAGES["umbrella"],
                "Ava", "Ben", "girl", "boy", "mother"),
    StoryParams("park_bench", "book", "friend_arrives", "read", "ask_help", ENDING_IMAGES["book"],
                "Ella", "Max", "girl", "boy", "father"),
]


def explain_rejection(params: StoryParams) -> str:
    return "(No story: that combination does not make a reasonable sharing scene.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life sharing storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--shared-item", dest="shared_item", choices=SHARED_ITEMS)
    ap.add_argument("--chance-event", dest="chance_event", choices=CHANCE_EVENTS)
    ap.add_argument("--turn", choices=TURNS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--parent", choices=["mother", "father"])
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
              and (args.shared_item is None or c[1] == args.shared_item)
              and (args.chance_event is None or c[2] == args.chance_event)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, shared_item, chance_event = rng.choice(sorted(combos))
    turn = args.turn or rng.choice(list(TURNS))
    need = rng.choice(list(NEEDS))
    ending_image = ENDING_IMAGES[shared_item]
    a_name = args.name_a or rng.choice(GIRL_NAMES + BOY_NAMES)
    b_name = args.name_b or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != a_name])
    a_gender = "girl" if a_name in GIRL_NAMES else "boy"
    b_gender = "girl" if b_name in GIRL_NAMES else "boy"
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place, shared_item, chance_event, need, turn, ending_image,
                       a_name, b_name, a_gender, b_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


ASP_RULES = r"""
shared(P) :- params(P).
chance_event(C) :- params(C).
valid(Place, Item, Event) :- place(Place), item(Item), event(Event).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for s in SHARED_ITEMS:
        lines.append(asp.fact("item", s))
    for c in CHANCE_EVENTS:
        lines.append(asp.fact("event", c))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid_combos()")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:\n")
        for t in combos:
            print(" ", t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
