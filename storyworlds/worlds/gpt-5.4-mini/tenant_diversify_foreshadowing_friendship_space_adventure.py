#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tenant_diversify_foreshadowing_friendship_space_adventure.py
============================================================================================

A standalone storyworld for a tiny Space Adventure about a station tenant, a
friendship problem, a foreshadowed rescue, and a small act of diversifying the
crew's plan so everyone can help.

Seed words: tenant, diversify
Features: foreshadowing, friendship
Style: space adventure
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
WANDER_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Station:
    id: str
    label: str
    theme: str
    foreshadow: str
    features: set[str] = field(default_factory=set)

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
class Route:
    id: str
    label: str
    kind: str
    risk: str
    landing: str
    safe_tool: str
    rescue: str
    speed: int
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
class CrewPlan:
    id: str
    label: str
    diversify_line: str
    safer_way: str
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_wander(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["lost"] < THRESHOLD:
            continue
        sig = ("wander", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] += 1
        out.append("__wander__")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["trust"] < THRESHOLD:
            continue
        if e.memes["teamwork"] < THRESHOLD:
            continue
        sig = ("friendship", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["joy"] += 1
        out.append("__friendship__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("wander", "physical", _r_wander),
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


def predict_lost(world: World, route_id: str) -> dict:
    sim = world.copy()
    _launch(sim, sim.get(route_id), narrate=False)
    return {
        "lost": sim.get("ship").meters["lost"] >= THRESHOLD,
        "fear": sim.get("pilot").memes["fear"],
    }


def _launch(world: World, route: Entity, narrate: bool = True) -> None:
    route.meters["speed"] += 1
    route.meters["lost"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, tenant: Entity, friend: Entity, station: Station) -> None:
    tenant.memes["curiosity"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"On the orbital station, {tenant.id} and {friend.id} were both tenants of "
        f"{station.label}. {station.foreshadow}"
    )
    world.say(
        f'They loved their friendship and their tiny room with a round window that '
        f'looked out at the stars.'
    )


def want_adventure(world: World, tenant: Entity, friend: Entity, route: Route) -> None:
    tenant.memes["bravery"] += 1
    world.say(
        f'When the stars glittered over the docking bay, {tenant.id} pointed at the '
        f'{route.label}. "Let\'s take the {route.kind} route!" {tenant.id} said.'
    )
    world.say(f"It sounded thrilling, like the start of a space adventure.")


def foreshadow(world: World, friend: Entity, route: Route) -> bool:
    pred = predict_lost(world, "ship")
    friend.memes["caution"] += 1
    world.facts["pred"] = pred
    world.say(
        f'{friend.id} touched the window latch and remembered the warning light '
        f'from earlier. "{route.risk}," {friend.id} said softly. '
        f'"If we rush it, the ship could get lost."'
    )
    return pred["lost"]


def diversify(world: World, tenant: Entity, friend: Entity, plan: CrewPlan) -> None:
    tenant.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    world.say(
        f"{plan.diversify_line} The crew decided to diversify their jobs, so one "
        f"friend could watch the map while the other handled the controls."
    )
    world.say(
        f"They chose {plan.safer_way}, and the whole little team moved together."
    )


def launch(world: World, route: Route) -> None:
    ship = world.get("ship")
    ship.label = route.label
    _launch(world, ship, narrate=False)
    world.say(
        f"The little craft glided out of the bay. At first it was beautiful, but "
        f"then the route marker blinked and the stars seemed to spin."
    )


def rescue(world: World, helper: Entity, route: Route, station: Station) -> None:
    ship = world.get("ship")
    ship.meters["lost"] = 0.0
    world.say(
        f"Then {helper.id} called to the station guide, and the guide pulled up a "
        f"bright beacon path. In a blink, the ship found {station.label} again."
    )
    world.say(
        f"The lost feeling vanished, and the crew could breathe again."
    )


def ending(world: World, tenant: Entity, friend: Entity, plan: CrewPlan) -> None:
    tenant.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Back home, they laughed about how the smallest idea had saved the day. "
        f"{plan.label} made the adventure safer, and their friendship felt bigger "
        f"than the station itself."
    )
    world.say(
        f"From their window they watched the ship lights twinkle, steady and close."
    )


def tell(station: Station, route: Route, plan: CrewPlan,
         tenant_name: str = "Mina", tenant_gender: str = "girl",
         friend_name: str = "Jax", friend_gender: str = "boy",
         captain_type: str = "mother") -> World:
    world = World()
    tenant = world.add(Entity(id=tenant_name, kind="character", type=tenant_gender,
                              role="tenant", traits=["curious"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender,
                              role="friend", traits=["kind"]))
    captain = world.add(Entity(id="Captain", kind="character", type=captain_type,
                               role="guide", label="the captain"))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label=route.label))
    world.facts.update(station=station, route=route, plan=plan, captain=captain,
                       tenant=tenant, friend=friend, ship=ship)
    setup(world, tenant, friend, station)
    world.para()
    want_adventure(world, tenant, friend, route)
    foreshadow(world, friend, route)
    world.para()
    diversify(world, tenant, friend, plan)
    launch(world, route)
    rescue(world, captain, route, station)
    world.para()
    ending(world, tenant, friend, plan)
    world.facts["outcome"] = "rescued"
    return world


STATIONS = {
    "orbital_home": Station(
        "orbital_home", "Orbital Home Nine", "a cozy space station",
        "A warning light blinked once near the airlock, as if the station was trying to say, be careful.",
        {"station", "space", "home"},
    ),
    "moon_hab": Station(
        "moon_hab", "Luna Nest", "a moon habitat",
        "A tiny map on the wall kept slipping sideways, like it was hinting that directions could matter.",
        {"station", "moon", "home"},
    ),
}

ROUTES = {
    "glitter_lane": Route(
        "glitter_lane", "Glitter Lane", "shortcut", "the shortcut could send them off course",
        "the beacon dock", "map tablet", "the captain's beacon path", 2,
        {"route", "space", "risk"},
    ),
    "comet_curve": Route(
        "comet_curve", "Comet Curve", "detour", "the long path could waste fuel",
        "the bright channel", "star chart", "the captain's beacon path", 1,
        {"route", "space"},
    ),
}

PLANS = {
    "split_tasks": CrewPlan(
        "split_tasks", "split tasks",
        "Let's diversify our jobs so nobody has to do everything alone.",
        "The two friends shared the work and watched different parts of the map.",
        {"teamwork", "friendship"},
    ),
    "mixed_tools": CrewPlan(
        "mixed_tools", "mixed tools",
        "We can diversify our tools and use both the map and the beacon.",
        "The crew mixed careful watching with quick steering.",
        {"teamwork", "friendship"},
    ),
}

NAMES_GIRL = ["Mina", "Iris", "Nia", "Luna", "Ada", "Rae"]
NAMES_BOY = ["Jax", "Oren", "Toby", "Kai", "Leo", "Milo"]


@dataclass
@dataclass
class StoryParams:
    station: str
    route: str
    plan: str
    tenant: str
    tenant_gender: str
    friend: str
    friend_gender: str
    captain: str
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
    return [(sid, rid, pid) for sid in STATIONS for rid in ROUTES for pid in PLANS]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure story for a 3-to-5-year-old that uses the word "tenant" and shows friendship on a station.',
        f"Tell a story where {f['tenant'].id} and {f['friend'].id} are station tenants, a warning is foreshadowed, and they diversify their jobs to solve a problem.",
        f'Write a gentle sci-fi story with foreshadowing and friendship that ends with a safe landing and the word "diversify".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    tenant = f["tenant"]
    friend = f["friend"]
    station = f["station"]
    route = f["route"]
    plan = f["plan"]
    return [
        QAItem(
            question="Who lived on the station?",
            answer=f"{tenant.id} and {friend.id} lived there as tenants, and they shared a tiny home on {station.label}.",
        ),
        QAItem(
            question="What warning was hinted at early in the story?",
            answer=f"The blinking light and slipping map foreshadowed trouble. They hinted that the route could go wrong if the crew rushed without a careful plan.",
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=f"They decided to diversify their jobs, which means they split the work into different parts. That made it easier to follow {route.label} safely and stay together.",
        ),
        QAItem(
            question="What happened at the end?",
            answer="The ship found the station again, and the friends ended the day safe and happy. Their friendship made the rescue feel calm instead of scary.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tenant?",
            answer="A tenant is a person who lives in a place that belongs to someone else, like an apartment or a station room.",
        ),
        QAItem(
            question="What does diversify mean?",
            answer="To diversify means to make a plan more varied by using different jobs, tools, or choices instead of only one.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue near the start of a story that hints something important may happen later.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship means people care about each other, help each other, and work together kindly.",
        ),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("orbital_home", "glitter_lane", "split_tasks", "Mina", "girl", "Jax", "boy", "mother"),
    StoryParams("moon_hab", "comet_curve", "mixed_tools", "Nia", "girl", "Kai", "boy", "father"),
]


def explain_rejection(route: Route) -> str:
    return f"(No story: {route.label} is not a valid tiny route for this world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld about tenant friends and a foreshadowed rescue.")
    ap.add_argument("--station", choices=STATIONS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--tenant")
    ap.add_argument("--tenant-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["mother", "father"])
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
    combos = valid_combos()
    station = args.station or rng.choice(sorted(STATIONS))
    route = args.route or rng.choice(sorted(ROUTES))
    plan = args.plan or rng.choice(sorted(PLANS))
    if (station, route, plan) not in combos:
        raise StoryError("(No valid combination matches the given options.)")
    tenant_gender = args.tenant_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if tenant_gender == "girl" else "girl")
    tenant = args.tenant or (rng.choice(NAMES_GIRL if tenant_gender == "girl" else NAMES_BOY))
    friend_pool = [n for n in (NAMES_GIRL if friend_gender == "girl" else NAMES_BOY) if n != tenant]
    friend = args.friend or rng.choice(friend_pool)
    captain = args.captain or rng.choice(["mother", "father"])
    return StoryParams(station, route, plan, tenant, tenant_gender, friend, friend_gender, captain)


def generate(params: StoryParams) -> StorySample:
    world = tell(STATIONS[params.station], ROUTES[params.route], PLANS[params.plan],
                 params.tenant, params.tenant_gender, params.friend, params.friend_gender,
                 params.captain)
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


ASP_RULES = r"""
valid(S, R, P) :- station(S), route(R), plan(P).
foreshadowing(S) :- station(S), hint(S).
friendship(S) :- station(S), friend_zone(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in STATIONS:
        lines.append(asp.fact("station", sid))
    for rid in ROUTES:
        lines.append(asp.fact("route", rid))
    for pid in PLANS:
        lines.append(asp.fact("plan", pid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in combo gate.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for triple in asp_valid_combos():
            print(triple)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
