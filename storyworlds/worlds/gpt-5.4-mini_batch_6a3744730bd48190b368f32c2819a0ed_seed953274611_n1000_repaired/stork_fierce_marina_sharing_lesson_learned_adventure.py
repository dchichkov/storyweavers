#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/stork_fierce_marina_sharing_lesson_learned_adventure.py
=======================================================================================

A standalone storyworld about a small marina adventure: a proud stork, a fierce
wind or wave, a sharing problem, and a lesson learned. The world is modeled with
physical meters and emotional memes, then rendered into child-facing prose.

Seed words: stork, fierce
Setting: marina
Features: Sharing, Lesson Learned
Style: Adventure
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SURGE_THRESHOLD = 2.0


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
    shared: bool = False
    fragile: bool = False
    useful: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    scene: str
    dark_spot: str
    goal: str
    danger_word: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    shareable: bool
    helpful: bool
    fragile: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Weather:
    id: str
    label: str
    fierce: bool
    effect: str
    tags: set[str] = field(default_factory=set)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(produced)
    if narrate:
        for s in out:
            if not s.startswith("__"):
                world.say(s)
    return out


def _r_surge(world: World) -> list[str]:
    out: list[str] = []
    weather = world.get("weather")
    if weather.meters["fierce"] < THRESHOLD:
        return out
    sig = ("surge",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("dock").meters["danger"] += 1
    world.get("stork").memes["alarm"] += 1
    out.append("__surge__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    for iid in ["basket", "net"]:
        item = world.get(iid)
        if item.meters["shared"] >= THRESHOLD:
            continue
        if item.meters["given"] >= THRESHOLD:
            sig = ("share", iid)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["shared"] += 1
            world.get("stork").memes["joy"] += 1
            world.get("child").memes["joy"] += 1
            out.append("__share__")
    return out


CAUSAL_RULES = [Rule("surge", _r_surge), Rule("share", _r_share)]


def burden_level(weather: Weather) -> int:
    return 2 if weather.fierce else 1


def sensible_choice(item: Item) -> bool:
    return item.shareable and item.helpful


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for weather_id, weather in WEATHER.items():
            for item_id, item in ITEMS.items():
                if place_id == "marina" and weather.fierce and sensible_choice(item):
                    combos.append((place_id, weather_id, item_id))
    return combos


@dataclass
class StoryParams:
    place: str
    weather: str
    item: str
    child_name: str = "Mina"
    child_gender: str = "girl"
    stork_name: str = "Stork"
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


PLACES = {
    "marina": Place(
        id="marina",
        label="the marina",
        scene="a busy marina with rope coils, bright flags, and bobbing boats",
        dark_spot="the far pier under the tall dock",
        goal="the little boat at the end of the dock",
        danger_word="water",
        tags={"marina"},
    ),
}

WEATHER = {
    "breeze": Weather(
        id="breeze",
        label="a breeze",
        fierce=False,
        effect="The flags only fluttered softly.",
        tags={"calm"},
    ),
    "storm": Weather(
        id="storm",
        label="a fierce storm wind",
        fierce=True,
        effect="The wind snapped at the ropes and slapped the waves against the dock.",
        tags={"fierce"},
    ),
}

ITEMS = {
    "rope": Item(
        id="rope",
        label="rope",
        phrase="a long coil of rope",
        shareable=True,
        helpful=True,
        tags={"share"},
    ),
    "lantern": Item(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        shareable=True,
        helpful=True,
        tags={"share"},
    ),
    "snack": Item(
        id="snack",
        label="snack",
        phrase="a bag of crackers",
        shareable=True,
        helpful=True,
        tags={"share"},
    ),
}

KNOWLEDGE = {
    "stork": [
        ("What is a stork?", "A stork is a tall bird with long legs and a long beak. Storks can walk in shallow water and build nests high up."),
    ],
    "fierce": [
        ("What does fierce mean?", "Fierce means very strong or wild. A fierce wind or wave can push hard and make things hard to control."),
    ],
    "share": [
        ("What does it mean to share?", "To share means to let someone else use or have some of what you have. Sharing can help everyone enjoy the same thing."),
    ],
    "marina": [
        ("What is a marina?", "A marina is a place where boats are kept. People can walk on the docks and look at the water there."),
    ],
    "dock": [
        ("What is a dock?", "A dock is a walkway by the water where boats can tie up. It can be slippery if water splashes onto it."),
    ],
    "lesson": [
        ("What is a lesson?", "A lesson is something you learn that helps you make a better choice next time."),
    ],
}
KNOWLEDGE_ORDER = ["marina", "dock", "stork", "fierce", "share", "lesson"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Marina adventure storyworld with sharing and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--weather", choices=WEATHER)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--stork-name")
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


def explain_rejection(place: str, weather: str, item: str) -> str:
    return "(No story: this marina adventure needs a fierce weather turn and a shareable helpful item.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("(No story: unknown place.)")
    if args.weather and args.weather not in WEATHER:
        raise StoryError("(No story: unknown weather.)")
    if args.item and args.item not in ITEMS:
        raise StoryError("(No story: unknown item.)")
    if args.place and args.weather and args.item:
        if not (args.place == "marina" and WEATHER[args.weather].fierce and sensible_choice(ITEMS[args.item])):
            raise StoryError(explain_rejection(args.place, args.weather, args.item))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.weather is None or c[1] == args.weather)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, weather, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or ("Mina" if gender == "girl" else "Milo")
    stork_name = args.stork_name or "Stork"
    return StoryParams(place=place, weather=weather, item=item, child_name=name, child_gender=gender, stork_name=stork_name)


def tell(place: Place, weather: Weather, item: Item, child_name: str, child_gender: str, stork_name: str) -> World:
    world = World()
    stork = world.add(Entity(id="stork", kind="character", type="bird", label=stork_name, role="helper", traits=["tall", "careful"]))
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    dock = world.add(Entity(id="dock", type="place", label="the dock"))
    weather_ent = world.add(Entity(id="weather", type="weather", label=weather.label))
    weather_ent.meters["fierce"] = 1.0 if weather.fierce else 0.0
    basket = world.add(Entity(id="basket", type="item", label="basket", shared=False))
    net = world.add(Entity(id="net", type="item", label="net", shared=False))
    for ent in (basket, net):
        ent.meters["given"] = 0.0
    world.say(f"{child_name} and {stork_name} set off at {place.label}. {place.scene}.")
    world.say(f"{weather.effect} They were on an adventure to reach {place.goal}.")
    world.para()
    world.say(f"{child_name} found {item.phrase} near the dock and held it close.")
    world.say(f'"Look!" {child_name} said. "I want to keep it all for myself."')
    if item.shareable:
        world.say(f"{stork_name} tilted its head. " f'"At the marina, sharing helps everyone," it said.')
    world.para()
    weather_ent.meters["fierce"] = 1.0 if weather.fierce else 0.0
    propagate(world, narrate=False)
    if weather.fierce:
        world.say(f"Then the wind grew fierce. It tugged at the rope and rocked the little boats.")
        world.say(f"{stork_name} saw the trouble and pointed at the basket and the net.")
        basket.meters["given"] = 1.0
        net.meters["given"] = 1.0
        propagate(world, narrate=False)
        world.say(f'"Let us share," {child_name} said at last. "We can hold the rope together and use the net to steady the lantern."')
        world.say(f"So {child_name} shared the {item.label}, and the pair crossed the dock carefully.")
        world.para()
        world.say(f"Together they reached the boat safely. The fierce wind still blew, but now the rope was steadier and the lantern shone.")
        world.say(f"{child_name} smiled at the stork. The adventure had become a lesson learned: sharing made the hard part easier.")
    else:
        world.say(f"The marina stayed calm, and the day stayed easy.")
    world.facts.update(place=place, weather=weather, item=item, child=child, stork=stork, outcome="shared" if weather.fierce else "calm")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item = f["item"]
    return [
        f"Write an adventure story at the marina about a stork and {child.label} with the words 'stork' and 'fierce'.",
        f"Tell a story where {child.label} learns to share {item.label} when the marina wind turns fierce.",
        "Write a child-friendly marina adventure that ends with a lesson learned about sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    item = f["item"]
    weather = f["weather"]
    qa = [
        QAItem(
            question="Where did the story happen?",
            answer="The story happened at the marina, where boats were tied up and the dock led out over the water. That setting made the adventure feel open and bright."
        ),
        QAItem(
            question="What did the child want at first?",
            answer=f"{child.label} wanted to keep the {item.label} all to {child.label.lower()}self. The choice felt important until the situation changed."
        ),
    ]
    if weather.fierce:
        qa.append(QAItem(
            question="What changed the story?",
            answer="The weather turned fierce and the wind began tugging at everything on the dock. That trouble made sharing the useful things matter much more."
        ))
        qa.append(QAItem(
            question="What was the lesson learned?",
            answer="The lesson was that sharing can help everyone get through a hard moment. When they shared the rope and lantern, the adventure became safer and calmer."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"marina", "dock", "stork", "fierce", "share", "lesson"}
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            for q, a in KNOWLEDGE[key]:
                out.append(QAItem(question=q, answer=a))
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
fierce_weather(w) :- weather(w), fierce(w).
valid(place(marina), weather(W), item(I)) :- weather(W), fierce(W), item(I), shareable(I), helpful(I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
    for wid, w in WEATHER.items():
        lines.append(asp.fact("weather", wid))
        if w.fierce:
            lines.append(asp.fact("fierce", wid))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if i.shareable:
            lines.append(asp.fact("shareable", iid))
        if i.helpful:
            lines.append(asp.fact("helpful", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set((a, b, c) for a, b, c in valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in the gate.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("(No story: invalid place.)")
    if params.weather not in WEATHER:
        raise StoryError("(No story: invalid weather.)")
    if params.item not in ITEMS:
        raise StoryError("(No story: invalid item.)")
    world = tell(PLACES[params.place], WEATHER[params.weather], ITEMS[params.item], params.child_name, params.child_gender, params.stork_name)
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


CURATED = [
    StoryParams(place="marina", weather="storm", item="rope", child_name="Mina", child_gender="girl", stork_name="Stork"),
    StoryParams(place="marina", weather="storm", item="lantern", child_name="Milo", child_gender="boy", stork_name="Skim"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.weather and args.item:
        if not (args.place == "marina" and WEATHER[args.weather].fierce and sensible_choice(ITEMS[args.item])):
            raise StoryError(explain_rejection(args.place, args.weather, args.item))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.weather is None or c[1] == args.weather)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, weather, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or ("Mina" if gender == "girl" else "Milo")
    stork_name = args.stork_name or "Stork"
    return StoryParams(place=place, weather=weather, item=item, child_name=name, child_gender=gender, stork_name=stork_name)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
