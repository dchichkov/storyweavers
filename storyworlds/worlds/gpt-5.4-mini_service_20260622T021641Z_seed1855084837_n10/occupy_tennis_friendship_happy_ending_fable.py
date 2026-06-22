#!/usr/bin/env python3
"""
storyworlds/worlds/occupy_tennis_friendship_happy_ending_fable.py
==================================================================

A standalone story world about two children, a shared tennis court, and a
fable-like lesson about friendship: do not occupy the whole play space, and
leave room for others. The story always ends happily through a fair turn-taking
compromise.

Core premise:
- One child arrives first and begins to occupy the tennis court.
- A friend arrives wanting to play tennis too.
- The tension is caused by scarce space, but the turn comes when kindness and
  fairness matter more than winning the whole court.
- The ending image proves the change: both children play tennis together.

The world uses typed entities with physical meters and emotional memes, a small
forward-chaining causal model, a reasonableness gate, an inline ASP twin, and
three Q&A sets grounded in the simulated state.
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
MIN_SHARING = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    held_by: str = ""
    occupied: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    kind: str
    can_be_occupied: bool = True
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectDef:
    id: str
    label: str
    type: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_blocked(world: World) -> list[str]:
    out: list[str] = []
    court = world.get("court")
    for c in world.characters():
        if c.meters["blocking"] < THRESHOLD:
            continue
        sig = ("blocked", c.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        court.meters["crowded"] += 1
        out.append("__blocked__")
    return out


def _r_respect(world: World) -> list[str]:
    out: list[str] = []
    for c in world.characters():
        if c.memes["fairness"] < THRESHOLD or c.memes["shared"] < THRESHOLD:
            continue
        sig = ("respect", c.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        c.memes["joy"] += 1
        out.append("__respect__")
    return out


CAUSAL_RULES = [Rule("blocked", "physical", _r_blocked), Rule("respect", "social", _r_respect)]


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


def can_afford(place: Place, activity: Activity) -> bool:
    return activity.id in place.affords and place.can_be_occupied


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for aid, activity in ACTIVITIES.items():
            for oid, obj in OBJECTS.items():
                if activity.keyword in obj.tags and can_afford(place, activity):
                    combos.append((pid, aid, oid))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    object: str
    first_name: str
    first_gender: str
    second_name: str
    second_gender: str
    first_trait: str
    second_trait: str
    seed: Optional[int] = None


PLACES = {
    "green_court": Place(
        id="green_court",
        label="the green tennis court",
        kind="court",
        can_be_occupied=True,
        affords={"tennis"},
        tags={"tennis", "court", "occupy"},
    ),
    "school_court": Place(
        id="school_court",
        label="the school court",
        kind="court",
        can_be_occupied=True,
        affords={"tennis"},
        tags={"tennis", "school", "occupy"},
    ),
}

ACTIVITIES = {
    "tennis": Activity(
        id="tennis",
        verb="play tennis",
        gerund="playing tennis",
        keyword="tennis",
        tags={"tennis", "sport", "ball"},
    )
}

OBJECTS = {
    "court_time": ObjectDef(
        id="court_time",
        label="court time",
        type="time",
        plural=False,
        tags={"tennis", "occupy"},
    ),
    "net_space": ObjectDef(
        id="net_space",
        label="net space",
        type="space",
        plural=False,
        tags={"tennis", "occupy"},
    ),
}

NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Ava", "Zoe"],
    "boy": ["Eli", "Finn", "Theo", "Noah", "Leo"],
}

TRAITS = ["kind", "patient", "cheerful", "thoughtful", "gentle", "fair"]


def make_valid_story(world: World, hero: Entity, friend: Entity, court: Entity, activity: Activity) -> None:
    hero.meters["blocking"] = 1
    court.occupied = True
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    friend.memes["desire"] += 1


def predict_outcome(world: World, hero: Entity, friend: Entity) -> dict[str, object]:
    sim = world.copy()
    sim.get(hero.id).meters["blocking"] += 1
    propagate(sim, narrate=False)
    return {
        "crowded": sim.get("court").meters["crowded"] > 0,
        "joy": sim.get(friend.id).memes["joy"],
    }


def introduce(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    world.say(
        f"At {world.place.label}, {hero.id} loved {activity.gerund} and arrived early with a bright smile."
    )
    world.say(
        f"Not long after, {friend.id} came too, because {friend.pronoun()} also wanted to {activity.verb}."
    )


def occupy_set_up(world: World, hero: Entity, court: Entity, obj: Entity) -> None:
    hero.meters["blocking"] += 1
    hero.memes["pride"] += 1
    court.occupied = True
    obj.occupied = True
    world.say(
        f"{hero.id} tried to occupy the whole court and keep {obj.label} for {hero.pronoun('possessive')}self."
    )


def friend_request(world: World, friend: Entity, hero: Entity, activity: Activity) -> None:
    friend.memes["desire"] += 1
    world.say(
        f"{friend.id} asked gently, \"May I join you and play {activity.keyword} too?\""
    )


def warn_and_think(world: World, friend: Entity, hero: Entity) -> None:
    if predict_outcome(world, hero, friend)["crowded"]:
        friend.memes["fairness"] += 1
        world.say(
            f"{friend.id} could see that one child did not need to occupy the whole court."
        )


def turn_to_friendship(world: World, hero: Entity, friend: Entity, court: Entity, activity: Activity, obj: Entity) -> None:
    hero.memes["share"] += 1
    friend.memes["share"] += 1
    hero.memes["fairness"] += 1
    friend.memes["fairness"] += 1
    hero.memes["shared"] += 1
    friend.memes["shared"] += 1
    court.occupied = False
    court.meters["crowded"] = 0
    obj.occupied = False
    world.say(
        f"{hero.id} nodded and moved over, because friendship is bigger than owning every bit of space."
    )
    world.say(
        f"Together they marked turns, shared {obj.label}, and agreed to let each friend have a fair serve."
    )


def happy_end(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 2
    friend.memes["joy"] += 2
    world.say(
        f"By sunset, {hero.id} and {friend.id} were {activity.gerund} side by side, laughing as the ball bounced back and forth."
    )
    world.say(
        "The court was no longer occupied by one child alone; it was full of friendship, fair turns, and happy play."
    )


def tell(place: Place, activity: Activity, objdef: ObjectDef,
         first_name: str = "Mina", first_gender: str = "girl",
         second_name: str = "Eli", second_gender: str = "boy",
         first_trait: str = "kind", second_trait: str = "fair") -> World:
    world = World(place)
    court = world.add(Entity(id="court", kind="thing", type="court", label=place.label))
    hero = world.add(Entity(id=first_name, kind="character", type=first_gender, traits=[first_trait]))
    friend = world.add(Entity(id=second_name, kind="character", type=second_gender, traits=[second_trait]))
    obj = world.add(Entity(id="object", kind="thing", type=objdef.type, label=objdef.label, plural=objdef.plural))
    world.facts.update(hero=hero, friend=friend, court=court, activity=activity, object=obj, place=place, object_def=objdef)
    make_valid_story(world, hero, friend, court, activity)

    introduce(world, hero, friend, activity)
    world.para()
    occupy_set_up(world, hero, court, obj)
    friend_request(world, friend, hero, activity)
    warn_and_think(world, friend, hero)
    world.para()
    turn_to_friendship(world, hero, friend, court, activity, obj)
    happy_end(world, hero, friend, activity)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    activity = f["activity"]
    return [
        f'Write a fable-like story for a young child that includes the words "occupy" and "{activity.keyword}", and ends with friendship.',
        f"Tell a happy ending story where {hero.id} starts to occupy {f['place'].label}, but {friend.id} shares the space and they both play {activity.keyword}.",
        f"Write a short moral story about two friends and a tennis court, where no one keeps the whole place to themselves.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    activity = f["activity"]
    court = f["court"]
    obj = f["object"]
    return [
        QAItem(
            question=f"Why did {friend.id} speak up when {hero.id} tried to occupy the court?",
            answer=f"{friend.id} wanted to play {activity.keyword} too, and one child should not occupy the whole court. That is why {friend.id} asked to join instead of walking away."
        ),
        QAItem(
            question=f"What changed after {hero.id} listened to {friend.id}?",
            answer=f"{hero.id} stopped trying to keep {court.label} alone and made room to share. After that, both friends could use {obj.label} and play together."
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {friend.id}?",
            answer=f"It ended happily, with both children playing {activity.gerund} side by side. Their friendship made the court feel fair and bright."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to occupy a place?",
            answer="To occupy a place means to stay in it or use it. If one person occupies everything, other people may not get a turn."
        ),
        QAItem(
            question="Why is tennis easier when people share the court?",
            answer="Tennis needs space to move and hit the ball back and forth. Sharing the court lets more than one player enjoy the game."
        ),
        QAItem(
            question="What is a friendship fable?",
            answer="A friendship fable is a short story that uses simple events to teach a lesson about being kind, fair, and good to one another."
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.occupied:
            bits.append("occupied=True")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(place: Place, activity: Activity, obj: ObjectDef) -> str:
    return f"(No story: {place.label} does not fit this tennis story, or {obj.label} does not match {activity.keyword}.)"


ASP_RULES = r"""
% A combination is valid when the place supports tennis and the object belongs to tennis.
valid(P, A, O) :- place(P), activity(A), object(O), affords(P, A), object_for(O, A).

% A child is occupying if their blocking meter reaches threshold.
occupying(C) :- blocking(C, N), N >= 1.

% Fair sharing resolves the tension.
happy_end(C1, C2) :- shared(C1), shared(C2), fair(C1), fair(C2).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("affords", pid, "tennis"))
        if p.can_be_occupied:
            lines.append(asp.fact("occupiable", pid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        for tag in sorted(o.tags):
            lines.append(asp.fact("object_for", oid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in asp:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story.strip()
        assert sample.prompts
        print("OK: generate() smoke test passed.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A friendship fable about occupying a tennis court fairly.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--first-name")
    ap.add_argument("--first-gender", choices=["girl", "boy"])
    ap.add_argument("--second-name")
    ap.add_argument("--second-gender", choices=["girl", "boy"])
    ap.add_argument("--first-trait")
    ap.add_argument("--second-trait")
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
              and (args.activity is None or c[1] == args.activity)
              and (args.object_ is None or c[2] == args.object_)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, obj = rng.choice(sorted(combos))
    fg = args.first_gender or rng.choice(["girl", "boy"])
    sg = args.second_gender or ("boy" if fg == "girl" else "girl")
    fn = args.first_name or rng.choice(NAMES[fg])
    sn = args.second_name or rng.choice([n for n in NAMES[sg] if n != fn] or NAMES[sg])
    ft = args.first_trait or rng.choice(TRAITS)
    st = args.second_trait or rng.choice([t for t in TRAITS if t != ft] or TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        object=obj,
        first_name=fn,
        first_gender=fg,
        second_name=sn,
        second_gender=sg,
        first_trait=ft,
        second_trait=st,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.activity not in ACTIVITIES or params.object not in OBJECTS:
        raise StoryError("Invalid story parameters.")
    world = tell(
        PLACES[params.place],
        ACTIVITIES[params.activity],
        OBJECTS[params.object],
        first_name=params.first_name,
        first_gender=params.first_gender,
        second_name=params.second_name,
        second_gender=params.second_gender,
        first_trait=params.first_trait,
        second_trait=params.second_trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(
        place="green_court",
        activity="tennis",
        object="court_time",
        first_name="Mina",
        first_gender="girl",
        second_name="Eli",
        second_gender="boy",
        first_trait="kind",
        second_trait="fair",
    ),
    StoryParams(
        place="school_court",
        activity="tennis",
        object="net_space",
        first_name="Nora",
        first_gender="girl",
        second_name="Theo",
        second_gender="boy",
        first_trait="thoughtful",
        second_trait="gentle",
    ),
]


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
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
