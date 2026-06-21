#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/deep_marina_special_curiosity_kindness_friendship_comedy.py
=============================================================================================

A small comedy storyworld about curious friends at a marina, a deep-water mystery,
and a kind solution that turns a mix-up into a special little triumph.

This world is built from the seed words and features:
- deep
- marina
- special
- Curiosity
- Kindness
- Friendship
- Comedy

The premise is simple: two friends visit a marina, become curious about something
deep in the water, make a funny mistake while trying to help, and then use kindness
and teamwork to resolve it. The story stays child-facing and state-driven.

Run it
------
    python deep_marina_special_curiosity_kindness_friendship_comedy.py
    python deep_marina_special_curiosity_kindness_friendship_comedy.py --all
    python deep_marina_special_curiosity_kindness_friendship_comedy.py --qa --json
    python deep_marina_special_curiosity_kindness_friendship_comedy.py --verify
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
DEPTH_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    deep_water: bool
    special_item: str
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
class CuriousThing:
    id: str
    label: str
    phrase: str
    risky: bool
    on_water: bool
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
class KindAction:
    id: str
    text: str
    joke: str
    fix: str
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
        self.depth: float = 0.0
        self.bobbing: bool = False

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
        c.depth = self.depth
        c.bobbing = self.bobbing
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


def _r_wave(world: World) -> list[str]:
    out: list[str] = []
    if world.depth >= DEPTH_MIN and not world.bobbing:
        world.bobbing = True
        for ent in list(world.entities.values()):
            if ent.role == "friend":
                ent.memes["surprise"] += 1
        out.append("__wave__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    if world.bobbing and (("laugh",) not in world.fired):
        world.fired.add(("laugh",))
        for ent in list(world.entities.values()):
            if ent.role in {"friend", "parent"}:
                ent.memes["joy"] += 1
        out.append("A gull gave a serious squeak and everyone laughed.")
    return out


CAUSAL_RULES = [Rule("wave", _r_wave), Rule("laugh", _r_laugh)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def reasonableness_gate(place: Place, thing: CuriousThing, action: KindAction) -> bool:
    return place.deep_water and thing.on_water and thing.risky and action.id in {"help", "apologize"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, p in PLACES.items():
        for tid, t in THINGS.items():
            for aid, a in ACTIONS.items():
                if reasonableness_gate(p, t, a):
                    combos.append((pid, tid, aid))
    return combos


def predict(world: World, thing_id: str) -> dict:
    sim = world.copy()
    sim.depth += 1.0
    simulate_help(sim, sim.get("hero"), THINGS[thing_id], narrate=False)
    return {"bobbing": sim.bobbing, "joy": sim.get("friend").memes["joy"]}


def _kindly_ask(world: World, hero: Entity, friend: Entity, thing: CuriousThing, place: Place) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"At the {place.label}, {hero.id} leaned over the rail and peered into the deep water. "
        f"Something special shimmered below."
    )
    world.say(
        f'"Look!" {hero.id} said. "{thing.phrase} down there!" {friend.id} smiled, because curiosity '
        f'can be a funny little flashlight.'
    )


def _oops(world: World, hero: Entity, friend: Entity, thing: CuriousThing) -> None:
    hero.memes["determination"] += 1
    world.depth += 2.0
    world.say(
        f"{hero.id} reached for the {thing.label}, and the special little hook wiggled, slipped, "
        f"and bonked the dock with a tiny thunk."
    )
    world.say(
        f"{friend.id} blinked. " +
        '"We were trying to rescue the mystery, not start a dock dance," ' +
        f"{friend.id} said."
    )
    propagate(world, narrate=True)


def simulate_help(world: World, hero: Entity, thing: CuriousThing, narrate: bool = True) -> None:
    world.depth += 1.0
    world.say(
        f"{hero.id} used a net and a long stick to nudge the {thing.label} closer without falling in."
    )
    if narrate:
        propagate(world, narrate=True)


def _kindness_fix(world: World, parent: Entity, hero: Entity, friend: Entity, thing: CuriousThing, action: KindAction) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"Then {parent.label_word} came along, saw the funny tangle, and laughed kindly. "
        f"'{action.text},' {parent.pronoun()} said."
    )
    world.say(
        f"{hero.id} and {friend.id} used the net again, more carefully this time. "
        f"{action.fix}."
    )
    world.say(
        f"At last, the {thing.label} drifted safely into a bucket, and everyone agreed it was a very special save."
    )


def tell(place: Place, thing: CuriousThing, action: KindAction,
         hero_name: str = "Nina", hero_type: str = "girl",
         friend_name: str = "Mo", friend_type: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", traits=["curious"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend", traits=["kind"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    item = world.add(Entity(id="thing", kind="thing", type="thing", label=thing.label, tags=set(thing.tags)))
    world.facts.update(place=place, thing=thing, action=action, hero=hero, friend=friend, parent=parent, item=item)

    world.say(
        f"One afternoon at the {place.label}, {hero.id} and {friend.id} were having a very curious day. "
        f"{place.special_item} made the marina feel extra special."
    )
    world.say(
        f"{hero.id} had the bright idea to look for {thing.phrase}. {friend.id} said yes right away, because friendship is better with shared curiosity."
    )
    world.para()
    _kindly_ask(world, hero, friend, thing, place)
    world.say(
        f"But the water looked deep, deeper than a spoon and way deeper than a shoe."
    )
    _oops(world, hero, friend, thing)
    world.para()
    _kindness_fix(world, parent, hero, friend, thing, action)
    world.say(
        f"By the end, the marina was calm again, the friends were smiling, and the deep water had kept its secret while they kept their special prize."
    )

    world.facts["outcome"] = "rescued"
    return world


PLACES = {
    "marina": Place(id="marina", label="marina", deep_water=True, special_item="A row of painted boats gleamed at the dock.", tags={"marina", "deep", "special"}),
    "harbor": Place(id="harbor", label="harbor", deep_water=True, special_item="A sleepy lighthouse winked from the end of the pier.", tags={"marina", "deep"}),
    "dock": Place(id="dock", label="dock", deep_water=True, special_item="A cheese-cracker boat float bobbed near the ropes.", tags={"marina", "special"}),
}

THINGS = {
    "seashell": CuriousThing(id="seashell", label="seashell", phrase="a special seashell", risky=True, on_water=True, tags={"special"}),
    "bucket": CuriousThing(id="bucket", label="bucket", phrase="a bucket that had floated away", risky=True, on_water=True, tags={"deep"}),
    "balloon": CuriousThing(id="balloon", label="balloon", phrase="a shiny balloon", risky=True, on_water=True, tags={"special", "deep"}),
}

ACTIONS = {
    "help": KindAction(id="help", text="That is what kind friends do", joke="the bucket had no idea it was famous now", fix="The net scooped it up with one polite swoosh", tags={"kindness", "friendship"}),
    "apologize": KindAction(id="apologize", text="No big splash, just a smarter plan", joke="the dock gave an embarrassed creak", fix="The friends took one more careful try and the prize bobbed right in", tags={"kindness"}),
}

GIRL_NAMES = ["Nina", "Mina", "Lila", "Pia", "Zara", "Maya"]
BOY_NAMES = ["Mo", "Leo", "Taj", "Ben", "Ollie", "Sam"]
TRAITS = ["curious", "kind", "careful", "cheerful"]


@dataclass
class StoryParams:
    place: str
    thing: str
    action: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
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
    StoryParams(place="marina", thing="seashell", action="help", hero="Nina", hero_gender="girl", friend="Mo", friend_gender="boy", parent="mother"),
    StoryParams(place="harbor", thing="bucket", action="apologize", hero="Lila", hero_gender="girl", friend="Ben", friend_gender="boy", parent="father"),
    StoryParams(place="dock", thing="balloon", action="help", hero="Taj", hero_gender="boy", friend="Maya", friend_gender="girl", parent="mother"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the words "deep", "marina", and "special".',
        f"Tell a comedy story about {f['hero'].id} and {f['friend'].id} at the marina, where curiosity leads to a small oops and then a kind rescue.",
        f"Write a friendship story where two children notice something special in the deep water and solve the problem kindly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, place, thing, action = f["hero"], f["friend"], f["place"], f["thing"], f["action"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, two friends at the {place.label}. Their curiosity got them into a silly little marina problem."),
        ("What did they want to do?",
         f"They wanted to look at {thing.phrase} in the deep water. The prize seemed special, so both friends wanted to help."),
        ("How did the problem get fixed?",
         f"They used a net and a long stick, and then a grown-up joined in kindly. {action.fix}"),
        ("How did the story end?",
         "It ended happily and a little sillily. The friends stayed dry, the special thing was safe, and everyone laughed at the dock."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a marina?",
         "A marina is a place where boats are kept and tied up near the water. It often has docks, ropes, and people taking care of boats."),
        ("What does deep mean?",
         "Deep means far down from the top. Deep water goes down a long way, which is why people must be careful near it."),
        ("Why can kindness help friends solve a problem?",
         "Kindness helps because it keeps people calm and willing to work together. When friends are kind, they can share tools, take turns, and fix mistakes without being mean."),
        ("What is friendship?",
         "Friendship means caring about someone and helping them. Friends share adventures, laughs, and help when things go a bit wrong."),
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, thing: CuriousThing, action: KindAction) -> str:
    if not reasonableness_gate(place, thing, action):
        return "(No story: this combination does not make a good marina comedy. The thing must be risky in deep water, and the action must be a kind rescue.)"
    return "(No story: unknown reason.)"


def valid_story_choices() -> list[tuple[str, str, str]]:
    return valid_combos()


ASP_RULES = r"""
place_ok(P) :- place(P), deep_water(P).
thing_ok(T) :- thing(T), risky(T), on_water(T).
action_ok(A) :- action(A), kind_action(A).
valid(P, T, A) :- place_ok(P), thing_ok(T), action_ok(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.deep_water:
            lines.append(asp.fact("deep_water", pid))
    for tid, t in THINGS.items():
        lines.append(asp.fact("thing", tid))
        if t.risky:
            lines.append(asp.fact("risky", tid))
        if t.on_water:
            lines.append(asp.fact("on_water", tid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("kind_action", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and python gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, thing=None, action=None, hero=None, hero_gender=None, friend=None, friend_gender=None, parent=None), random.Random(7)))
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy marina storyworld with curiosity, kindness, and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", dest="hero_gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", dest="friend_gender", choices=["girl", "boy"])
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
              and (args.thing is None or c[1] == args.thing)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError(explain_rejection(PLACES[args.place], THINGS[args.thing], ACTIONS[args.action]) if args.place and args.thing and args.action else "(No valid combination matches the given options.)")
    place, thing, action = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend_pool = [n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != hero]
    friend = args.friend or rng.choice(friend_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, thing=thing, action=action, hero=hero, hero_gender=hero_gender, friend=friend, friend_gender=friend_gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.thing not in THINGS or params.action not in ACTIONS:
        raise StoryError("(Invalid params.)")
    place, thing, action = PLACES[params.place], THINGS[params.thing], ACTIONS[params.action]
    world = tell(place, thing, action, hero_name=params.hero, hero_type=params.hero_gender, friend_name=params.friend, friend_type=params.friend_gender, parent_type=params.parent)
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
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.friend}: {p.place}, {p.thing}, {p.action}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
