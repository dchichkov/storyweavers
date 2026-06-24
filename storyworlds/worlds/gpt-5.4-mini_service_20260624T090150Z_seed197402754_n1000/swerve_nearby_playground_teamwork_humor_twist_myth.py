#!/usr/bin/env python3
"""
A small story world for a playground myth: a child, a nearby mishap, teamwork,
a humorous twist, and a tidy ending.

The seed tale imagined for this world:
---
On a bright afternoon at the playground, a child named Nia was helping her older
brother, Sol, build a grand "dragon road" with chalk and little sticks. Near the
sandbox stood a wobbly old cart that everyone called the Wagon of Wind, because
its front wheel liked to swerve when the path was uneven.

Nia and Sol wanted to roll a shiny tin crown to the top of the hill slide and
place it in the bird nest they had made from leaves. But the wagon swerved
nearby and bumped the crown away each time they tried. The littlest kids laughed,
and the crown kept spinning in silly circles.

Then Nia noticed that if Sol pushed from one side and she guided from the other,
the wagon rolled straight. Together they steered it past the rough patch, and
the crown reached the nest at last. The bird nest turned out to be a toy nest
belonging to the playground cat, who wore the crown and looked very proud.
---

The simulated world below turns that premise into a tiny causal model.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "cat"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str = "the playground"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "playground": Place(name="the playground", affords={"swerve"}),
}

ACTIONS = {
    "swerve": Action(
        id="swerve",
        verb="swerve nearby",
        gerund="swerving nearby",
        rush="swerve toward the hill",
        mess="jostled",
        zone={"path"},
        weather="bright",
        keyword="swerve",
        tags={"swerve", "nearby", "twist"},
    ),
}

PRIZES = {
    "crown": Prize(
        label="crown",
        phrase="a shiny tin crown",
        type="crown",
        region="head",
    ),
}

GEAR = [
    Gear(
        id="rope",
        label="a braided rope",
        covers={"hands"},
        guards={"jostled"},
        prep="hold the braided rope on both sides",
        tail="held the braided rope and walked the wagon straight",
    ),
    Gear(
        id="flags",
        label="little chalk flags",
        covers={"path"},
        guards={"jostled"},
        prep="mark the rough patch with little chalk flags",
        tail="followed the chalk flags and kept the wagon on the smooth line",
    ),
]

NAMES = ["Nia", "Sol", "Milo", "Ari", "Luna", "Tess"]
HELPERS = ["brother", "sister", "friend", "cousin"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in PLACES.items():
        for act in setting.affords:
            for prize in PRIZES:
                combos.append((place, act, prize))
    return combos


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region in action.zone or prize.region == "head"


def select_gear(action: Action, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if action.mess in gear.guards:
            return gear
    return None


def intro(world: World, hero: Entity, helper: Entity, prize: Entity, action: Action) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} at {world.place.name}, and {hero.id} "
        f"loved {action.gerund} with {helper.id}."
    )
    world.say(
        f"Together they watched over {hero.pronoun('possessive')} {prize.label}, "
        f"for it looked like a treasure from an old tale."
    )


def predict(world: World, hero: Entity, action: Action, prize_id: str) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters[action.mess] = sim.get(hero.id).meters.get(action.mess, 0) + 1
    return {"would_jostle": True, "prize_safe": False if prize_id in sim.entities else False}


def start_problem(world: World, hero: Entity, helper: Entity, prize: Entity, action: Action) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(
        f"One bright afternoon, {hero.id} and {helper.id} tried to bring "
        f"{hero.pronoun('possessive')} {prize.label} to the top of the hill slide."
    )
    world.say(
        f"But a wagon nearby liked to {action.verb}, and every swerve bumped the crown "
        f"into a silly spin."
    )


def fix(world: World, hero: Entity, helper: Entity, prize: Entity, action: Action) -> Optional[Gear]:
    gear = select_gear(action, prize)
    if gear is None:
        return None
    if hero.memes.get("want", 0) < THRESHOLD:
        return None
    world.say(
        f"{helper.id} pointed to the rough patch and smiled. "
        f'"If we {gear.prep}, the wagon may stop dancing," {helper.id} said.'
    )
    return gear


def resolve(world: World, hero: Entity, helper: Entity, prize: Entity, action: Action, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0) + 1
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0) + 1
    world.say(
        f"{hero.id} nodded, and {hero.id} and {helper.id} worked as one."
    )
    world.say(
        f"They {gear.tail}. At last the crown stayed steady and reached the toy nest, "
        f"where a tiny playground cat wore it like a moonlit king."
    )
    world.say(
        f"The littlest kids laughed, because the grand trouble had turned into a joke, "
        f"and the playground felt like a myth that had decided to grin."
    )


def tell(place: Place, action: Action, prize_cfg: Prize, name: str, helper_kind: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type="girl", meters={}, memes={}))
    helper = world.add(Entity(id=f"the {helper_kind}", kind="character", type="boy", meters={}, memes={}))
    prize = world.add(Entity(id="crown", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))

    intro(world, hero, helper, prize, action)
    world.para()
    start_problem(world, hero, helper, prize, action)
    world.para()
    gear = fix(world, hero, helper, prize, action)
    if gear is None:
        raise StoryError("No reasonable teamwork fix exists for this playground twist.")
    resolve(world, hero, helper, prize, action, gear)

    world.facts.update(hero=hero, helper=helper, prize=prize, action=action, gear=gear)
    return world


SETTINGS = PLACES
ACTIVITIES = ACTIONS
GEAR_CATALOG = GEAR

GIRL_NAMES = ["Nia", "Luna", "Tess", "Mira", "Ava", "Maya"]
BOY_NAMES = ["Sol", "Milo", "Ari", "Theo", "Owen", "Finn"]
HELPER_KINDS = ["brother", "sister", "friend", "cousin"]
TRAITS = ["gentle", "brave", "clever", "cheerful"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    action = f["action"]
    prize = f["prize"]
    return [
        f'Write a short myth-like story for young children set at a playground about {hero.id}, '
        f'{helper.id}, and the word "{action.keyword}".',
        f"Tell a playful story where {hero.id} and {helper.id} use teamwork to protect "
        f"{hero.pronoun('possessive')} {prize.label} from a nearby swerve.",
        f'Write a gentle playground tale that includes "{action.keyword}" and ends with a funny twist.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    action = f["action"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who did the story follow at the playground?",
            answer=f"It followed {hero.id} and {helper.id}, who were working together on a small treasure.",
        ),
        QAItem(
            question=f"What kept going wrong when they tried to move the crown?",
            answer=f"A wagon nearby kept {action.gerund}, so the crown spun away in a silly way.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They used teamwork and {gear.label} to guide the wagon straight, so {prize.label} could reach the nest safely.",
        ),
        QAItem(
            question=f"What was the funny twist at the end?",
            answer="The toy nest belonged to a playground cat, and the cat wore the crown like a proud little ruler.",
        ),
    ]


KNOWLEDGE = {
    "swerve": [
        (
            "What does it mean to swerve?",
            "To swerve means to turn suddenly or move to the side in a quick, curving way.",
        )
    ],
    "nearby": [
        (
            "What does nearby mean?",
            "Nearby means close by, not far away.",
        )
    ],
    "playground": [
        (
            "What is a playground?",
            "A playground is a place with things like slides, swings, and ladders where children can play.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when two or more people help each other to do something together.",
        )
    ],
    "humor": [
        (
            "What is humor?",
            "Humor is something funny or playful that makes people smile or laugh.",
        )
    ],
    "twist": [
        (
            "What is a twist in a story?",
            "A twist is a surprising turn that changes what you thought would happen.",
        )
    ],
    "myth": [
        (
            "What is a myth?",
            "A myth is an old story about special happenings, often told in a grand and magical way.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ["swerve", "nearby", "playground", "teamwork", "humor", "twist", "myth"]:
        if tag in {"swerve", "nearby", "playground", "teamwork", "humor", "twist", "myth"}:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="playground", action="swerve", prize="crown", name="Nia", helper="brother"),
    StoryParams(place="playground", action="swerve", prize="crown", name="Maya", helper="friend"),
]


ASP_RULES = r"""
place(playground).
action(swerve).
prize(crown).
affords(playground, swerve).
zone(swerve, path).
worn_on(crown, head).
gear(rope).
guards(rope, jostled).
gear(flags).
guards(flags, jostled).

prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
prize_at_risk(swerve,crown).

select_fix(A,P,G) :- prize_at_risk(A,P), guards(G,jostled).
valid_story(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), select_fix(A,P,_).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        for a in SETTINGS[p].affords:
            lines.append(asp.fact("affords", p, a))
    for a in ACTIVITIES:
        lines.append(asp.fact("action", a))
        for r in ACTIVITIES[a].zone:
            lines.append(asp.fact("zone", a, r))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
        lines.append(asp.fact("worn_on", p, PRIZES[p].region))
    for g in GEAR_CATALOG:
        lines.append(asp.fact("gear", g.id))
        for m in g.guards:
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Playground myth story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.action and args.action not in ACTIVITIES:
        raise StoryError("Unknown action.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES)
    helper = args.helper or rng.choice(HELPER_KINDS)
    return StoryParams(place=place, action=action, prize=prize, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.action], PRIZES[params.prize], params.name, params.helper)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [("playground", "swerve", "crown")]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
