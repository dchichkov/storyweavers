#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/trouser_current_topic_rhyme_twist_space_adventure.py
====================================================================================

A standalone storyworld about a tiny space adventure with a playful rhyme and a
small twist. Two kids on a moon station get pulled toward a glowing current,
one child loses a trouser strap, and they solve the problem by switching to a
safer route and a better topic for their mission talk.

Seed words required by the prompt:
- trouser
- current
- topic

Features:
- Rhyme
- Twist
- Style: Space Adventure
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
        return self.label or self.type


@dataclass
class Setting:
    id: str
    scene: str
    detail: str
    current: str
    allowed_topic: str


@dataclass
class Route:
    id: str
    phrase: str
    danger: str
    signal: str
    twist: str
    safe_alt: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = False
    fixed_by: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


def _r_drift(world: World) -> list[str]:
    out: list[str] = []
    ship = world.entities.get("ship")
    if ship and ship.meters["drifting"] >= THRESHOLD and ("drift",) not in world.fired:
        world.fired.add(("drift",))
        ship.meters["tremble"] += 1
        out.append("__drift__")
    return out


CAUSAL_RULES = [Rule("drift", "physical", _r_drift)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_route(route: Route, item: Item) -> bool:
    return route.id == "current" and item.region == "trouser"


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= 2]


def is_held(route: Route, remedy: Remedy, delay: int) -> bool:
    return remedy.power >= 1 + delay


def route_twist(route: Route) -> bool:
    return "twist" in route.tags


def setup(world: World, a: Entity, b: Entity, setting: Setting, route: Route) -> None:
    a.memes["curiosity"] += 1
    b.memes["calm"] += 1
    world.say(
        f"On {setting.scene}, {a.id} and {b.id} floated past the moon window, "
        f"where {setting.detail} and {setting.current} glimmered like a silver ribbon."
    )
    world.say(
        f'{a.id} grinned. "Let\'s chase the {route.id}!" {a.id} said.'
    )


def rhyme(world: World, a: Entity, b: Entity, setting: Setting, route: Route) -> None:
    world.say(
        f'{b.id} answered, "A bright little light and a safe little flight, '
        f'keep our boots tight and our hearts just right."'
    )
    world.say(
        f"The rhyme was soft, but it fit the night, and both children nodded at the same topic: the route ahead."
    )


def want_go(world: World, a: Entity, route: Route) -> None:
    a.memes["bold"] += 1
    world.say(
        f"{a.id} wanted to follow the {route.id} current at once, because it looked exciting and fast."
    )


def warn(world: World, b: Entity, a: Entity, route: Route, item: Item) -> None:
    b.memes["caution"] += 1
    world.say(
        f'{b.id} pointed at {item.label}. "{a.id}, that current can tug at your {item.region}; '
        f'it already snagged the {item.label_word if hasattr(item, "label_word") else item.label} before."'
    )


def twist(world: World, a: Entity, route: Route, item: Item) -> None:
    a.memes["defiance"] += 1
    world.say(
        f"Then came the twist: a loose panel spun open, the {route.twist} caught the {item.label}, "
        f"and one {item.label} strap slipped free."
    )


def alarm(world: World, b: Entity, a: Entity, route: Route, item: Item) -> None:
    world.say(
        f'"{a.id}! The {route.id}!" {b.id} cried. "Your {item.label} is sliding!"'
    )


def rescue(world: World, parent: Entity, remedy: Remedy, item: Item) -> None:
    item.meters["safe"] += 1
    body = remedy.text.replace("{item}", item.label)
    world.say(
        f"{parent.label_word.capitalize()} came gliding over and {body}."
    )
    world.say(
        f"The current hummed outside, but inside the cabin the trouble stayed small."
    )


def ending(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    world.say(
        f"After that, {a.id} and {b.id} chose a safer path, talked about the topic of docking, "
        f"and watched the stars slide by like beads on a string."
    )
    world.say(
        f"The moon station shone quiet and clean, and the two friends kept their trousers snug for the long trip home."
    )


def predict(world: World, item_id: str, route: Route) -> dict:
    sim = world.copy()
    sim.get(item_id).meters["snagged"] += 1
    sim.get("ship").meters["drifting"] += 1
    propagate(sim, narrate=False)
    return {"snagged": sim.get(item_id).meters["snagged"] >= THRESHOLD}


def tell(setting: Setting, route: Route, item: Item, remedy: Remedy,
         name1: str = "Mina", gender1: str = "girl",
         name2: str = "Jory", gender2: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    a = world.add(Entity(name1, kind="character", type=gender1, role="pilot"))
    b = world.add(Entity(name2, kind="character", type=gender2, role="navigator"))
    parent = world.add(Entity("Pilot", kind="character", type=parent_type, label="the pilot"))
    ship = world.add(Entity("ship", type="ship", label="the little ship"))
    world.facts["setting"] = setting
    world.facts["route"] = route
    world.facts["item"] = item
    world.facts["remedy"] = remedy
    world.facts["delay"] = delay

    setup(world, a, b, setting, route)
    rhyme(world, a, b, setting, route)
    world.para()
    want_go(world, a, route)
    warn(world, b, a, route, item)
    world.para()
    twist(world, a, route, item)
    alarm(world, b, a, route, item)

    if remedy.power >= 1 + delay:
        world.para()
        rescue(world, parent, remedy, item)
        ending(world, a, b, setting)
        world.facts["outcome"] = "fixed"
    else:
        world.para()
        ship.meters["drifting"] += 1
        world.say(
            f"The little ship wobbled too much, so the pilot called them back from the window and steered away."
        )
        world.say(
            f"By the time they reached calmer space, the {route.id} had faded behind them."
        )
        world.facts["outcome"] = "retreated"

    world.facts.update(pilot=a, navigator=b, parent=parent, ship=ship)
    return world


SETTINGS = {
    "station": Setting("station", "the moon station", "the airlock window", "the current", "docking"),
    "decks": Setting("decks", "the blue deck", "the starboard window", "the current", "mapping"),
}

ROUTES = {
    "current": Route("current", "current", "pulling force", "twist", "spiral twist", "safer path", {"current", "twist"}),
    "comet": Route("comet", "comet trail", "bright wake", "spark", "curling loop", "safer path", {"comet"}),
}

ITEMS = {
    "trouser": Item("trouser", "trouser", "their trouser leg", "trouser", fragile=True, fixed_by="clip", tags={"trouser"}),
    "strap": Item("strap", "strap", "the strap of the seat harness", "trouser", fragile=True, fixed_by="clip", tags={"strap"}),
}

REMEDIES = {
    "clip": Remedy("clip", 3, 2, "fastened a small clip to the strap and tugged it snug", "tried to fix the strap, but the pull was too strong", "fastened the strap with a clip", {"clip"}),
    "tape": Remedy("tape", 2, 1, "wrapped tape around the strap and gave it a careful press", "used tape, but it peeled right away", "wrapped the strap with tape", {"tape"}),
}

GIRL_NAMES = ["Mina", "Luna", "Rae", "Tia", "Nia"]
BOY_NAMES = ["Jory", "Kai", "Nate", "Tob", "Pax"]
TRAITS = ["curious", "careful", "brave", "quiet"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for rid, route in ROUTES.items():
            for iid, item in ITEMS.items():
                if valid_route(route, item):
                    combos.append((sid, rid, iid))
    return combos


@dataclass
class StoryParams:
    setting: str
    route: str
    item: str
    remedy: str
    name1: str
    gender1: str
    name2: str
    gender2: str
    parent: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with rhyme and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--remedy", choices=REMEDIES)
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
    if args.route and args.item:
        if not valid_route(ROUTES[args.route], ITEMS[args.item]):
            raise StoryError("No story: that route does not actually snag the trouser item.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.route is None or c[1] == args.route)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, route, item = rng.choice(sorted(combos))
    remedy = args.remedy or rng.choice(sorted(REMEDIES))
    gender1 = rng.choice(["girl", "boy"])
    gender2 = "boy" if gender1 == "girl" else "girl"
    name1 = rng.choice(GIRL_NAMES if gender1 == "girl" else BOY_NAMES)
    name2 = rng.choice([n for n in (GIRL_NAMES if gender2 == "girl" else BOY_NAMES) if n != name1])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = rng.randint(0, 1)
    return StoryParams(setting, route, item, remedy, name1, gender1, name2, gender2, parent, trait, delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure story for a small child that includes the words "trouser", "current", and "topic".',
        f"Tell a moon-station story where {f['pilot'].id} and {f['navigator'].id} follow a current, then switch to a safer topic after a twist.",
        f"Write a short rhyming space story with a surprise twist and a trouser problem, ending safely."
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["pilot"]
    b = f["navigator"]
    item = f["item"]
    route = f["route"]
    remedy = f["remedy"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {a.id} and {b.id}, two children on a moon station. They were exploring the current and trying to stay calm together."
        ),
        QAItem(
            question="What went wrong?",
            answer=f"A twist in the moving current snagged the {item.label}, and the strap slipped loose. That made the trip feel risky for a moment."
        ),
        QAItem(
            question="How did they fix it?",
            answer=f"{world.facts['parent'].label_word.capitalize()} fastened a clip to the {item.label} and made it snug again. That small fix kept the trouble from growing."
        ),
    ]
    if f.get("outcome") == "fixed":
        qa.append(QAItem(
            question="How did the story end?",
            answer="It ended safely. They chose a better route, talked about a safer topic, and watched the stars from inside the ship."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a current in space adventure stories?", "A current is a moving pull or flow that can tug at a ship or a person. In a story, it can act like a strong path that is hard to fight."),
        QAItem("What is a topic?", "A topic is what people are talking about. It can change when a story changes direction."),
        QAItem("What does a rhyme do?", "A rhyme makes words sound alike at the ends. It can make a story feel sing-song and fun."),
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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("station", "current", "trouser", "clip", "Mina", "girl", "Jory", "boy", "mother", "curious", 0),
    StoryParams("decks", "current", "trouser", "tape", "Luna", "girl", "Kai", "boy", "father", "careful", 1),
]


def explain_response(rid: str) -> str:
    r = REMEDIES[rid]
    return f"(Refusing remedy '{rid}': it is too weak for this little space twist. Try a stronger fix.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid, r in ROUTES.items():
        lines.append(asp.fact("route", rid))
        if "twist" in r.tags:
            lines.append(asp.fact("twist", rid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("trouser_item", iid))
    for rm, rem in REMEDIES.items():
        lines.append(asp.fact("remedy", rm))
        lines.append(asp.fact("sense", rm, rem.sense))
        lines.append(asp.fact("power", rm, rem.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,R,I) :- setting(S), route(R), item(I), R = current, I = trouser.
sensible(M) :- remedy(M), sense(M,S), sense_min(N), S >= N.
outcome(fixed) :- remedy(M), power(M,P), delay(D), P >= D+1.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate smoke test succeeded.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ROUTES[params.route],
        ITEMS[params.item],
        REMEDIES[params.remedy],
        params.name1, params.gender1, params.name2, params.gender2,
        params.parent, params.delay,
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
