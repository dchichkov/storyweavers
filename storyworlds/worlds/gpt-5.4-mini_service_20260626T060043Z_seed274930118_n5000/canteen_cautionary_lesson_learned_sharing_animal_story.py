#!/usr/bin/env python3
"""
A small animal-story world about a canteen, a cautious lesson, and sharing.

Premise:
- A thirsty animal keeps a canteen to itself.
- Another animal gets too warm and needs water.
- A cautionary mistake leaves both animals with less water than they wanted.
- They learn to share the canteen and take turns.

The simulation tracks physical meters (water, heat, distance) and emotional memes
(worry, kindness, relief, gratitude). The prose is assembled from state changes,
not from a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"water": 0.0, "heat": 0.0, "distance": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "kindness": 0.0, "relief": 0.0, "gratitude": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


@dataclass
class Rule:
    name: str
    apply: callable


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class Habitat:
    place: str
    terrain: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    consequence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    thirst: float = 1.0


@dataclass
class Compromise:
    id: str
    label: str
    prep: str
    tail: str


HABITATS = {
    "watering_hole": Habitat(place="the watering hole", terrain="sun-baked grass", affords={"haul", "hide", "share"}),
    "riverbank": Habitat(place="the riverbank", terrain="soft mud", affords={"share"}),
    "shade_tree": Habitat(place="the shady tree", terrain="cool leaves", affords={"rest", "share"}),
}

ACTIVITIES = {
    "haul": Activity(
        id="haul",
        verb="haul the canteen away",
        gerund="hauling the canteen away",
        risk="runs dry",
        consequence="the water runs low",
        tags={"canteen", "water", "warning"},
    ),
    "hide": Activity(
        id="hide",
        verb="hide the canteen behind a bush",
        gerund="hiding the canteen behind a bush",
        risk="cannot be shared",
        consequence="no one can reach the water in time",
        tags={"canteen", "sharing", "warning"},
    ),
    "share": Activity(
        id="share",
        verb="share the canteen",
        gerund="sharing the canteen",
        risk="stays close",
        consequence="everyone gets a sip",
        tags={"canteen", "sharing"},
    ),
}

PRIZES = {
    "canteen": Prize(label="canteen", phrase="a little metal canteen"),
}

COMPROMISES = {
    "share_sips": Compromise(
        id="share_sips",
        label="share the canteen in small sips",
        prep="take turns with little sips",
        tail="took turns until the canteen felt lighter and the thirst was gone",
    ),
    "carry_together": Compromise(
        id="carry_together",
        label="carry the canteen together",
        prep="carry the canteen together",
        tail="walked side by side so the canteen stayed close to both of them",
    ),
}

ANIMALS = {
    "rabbit": {"type": "rabbit", "name_pool": ["Milo", "Pippa", "Toby", "Nina", "Bram"]},
    "fox": {"type": "fox", "name_pool": ["Ruby", "Finn", "Luna", "Otis", "Juno"]},
    "bear": {"type": "bear", "name_pool": ["Poppy", "Gus", "Mara", "Hugo", "Iris"]},
    "squirrel": {"type": "squirrel", "name_pool": ["Hazel", "Chip", "Sage", "Lark", "Nico"]},
}


@dataclass
class StoryParams:
    habitat: str
    activity: str
    hero_kind: str
    friend_kind: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------

def _r_heat(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["heat"] < THRESHOLD:
            continue
        sig = ("heat", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        out.append(f"{ent.id} grew hot and started to worry.")
    return out


def _r_thirst(world: World) -> list[str]:
    out: list[str] = []
    canteen = world.get("canteen")
    for ent in world.characters():
        if ent.meters["heat"] < THRESHOLD:
            continue
        if canteen.carried_by != ent.id and canteen.meters["water"] < THRESHOLD:
            sig = ("thirst", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["worry"] += 1
            out.append(f"{ent.id} noticed the canteen was not where it should be.")
    return out


def _r_share(world: World) -> list[str]:
    canteen = world.get("canteen")
    if canteen.meters["water"] < THRESHOLD:
        return []
    carriers = [e.id for e in world.characters() if canteen.carried_by == e.id]
    if len(carriers) >= 2:
        return []
    return []


RULES = [
    Rule("heat", _r_heat),
    Rule("thirst", _r_thirst),
]


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def animal_name(kind: str, rng: random.Random) -> str:
    return rng.choice(ANIMALS[kind]["name_pool"])


def valid_activity(activity: Activity, habitat: Habitat) -> bool:
    return activity.id in habitat.affords


def explain_rejection(activity: Activity, habitat: Habitat) -> str:
    return f"(No story: {activity.gerund} does not fit {habitat.place}.)"


# ---------------------------------------------------------------------------
# Story building
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    habitat = HABITATS[params.habitat]
    activity = ACTIVITIES[params.activity]

    world = World()
    world.facts["habitat"] = habitat
    world.facts["activity"] = activity

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_kind))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_kind))
    canteen = world.add(Entity(id="canteen", kind="thing", type="canteen", label="canteen", phrase="a little metal canteen"))
    canteen.carried_by = hero.id
    canteen.meters["water"] = 1.0

    # Act 1: setup.
    world.say(f"{hero.id}, a small {hero.type}, found a little canteen near {habitat.place}.")
    world.say(f"{hero.id} liked keeping the canteen close because the day felt warm and dry.")
    world.say(f"{friend.id}, a small {friend.type}, was trotting nearby when the heat began to rise.")

    # Act 2: cautionary mistake.
    world.para()
    world.say(f"At {habitat.place}, {hero.id} wanted to {activity.verb}.")
    world.say(f"But {hero.id} thought the canteen was only for later, so {hero.id} tried to keep it hidden.")
    hero.meters["heat"] += 1.0
    friend.meters["heat"] += 1.0
    canteen.carried_by = None
    canteen.meters["water"] -= 1.0
    if canteen.meters["water"] < 0:
        canteen.meters["water"] = 0.0
    propagate(world)

    world.say(f"That was a cautionary mistake, because {activity.consequence}.")

    # Act 3: lesson learned and sharing.
    world.para()
    world.say(f"{friend.id} pointed at the empty-feeling canteen and looked worried.")
    world.say(f"Then {hero.id} learned the lesson: water helps best when it is shared.")

    compromise = COMPROMISES["share_sips"]
    world.say(f"So they decided to {compromise.prep}.")
    canteen.carried_by = None
    canteen.meters["water"] = 1.0
    hero.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(f"{hero.id} and {friend.id} {compromise.tail}.")
    world.say(f"In the end, the canteen was not hidden anymore; it was shared, and both animals felt cool and calm.")

    world.facts.update(
        hero=hero,
        friend=friend,
        canteen=canteen,
        compromise=compromise,
        place=habitat.place,
        terrain=habitat.terrain,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story about a canteen, a mistake, and sharing at {f["place"]}.',
        f"Tell a gentle story where {f['hero'].id} learns a cautionary lesson about keeping water to itself.",
        f"Write a simple Animal Story with a canteen that ends with two animals taking turns.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    place = f["place"]
    compromise = f["compromise"]
    return [
        QAItem(
            question=f"Who found the canteen near {place}?",
            answer=f"{hero.id} found the canteen near {place}.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn after the mistake?",
            answer=f"{hero.id} learned that water helps best when it is shared instead of hidden away.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} solve the problem?",
            answer=f"They decided to {compromise.prep} and then share it in small sips.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer="The canteen was shared, the animals felt cooler, and the worry turned into relief.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a canteen used for?",
            answer="A canteen is a container for carrying water or another drink, especially on a trip.",
        ),
        QAItem(
            question="Why should animals share water on a hot day?",
            answer="Sharing water helps everyone stay safe, cool, and comfortable when the day is warm.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="It means understanding a better way to do something after seeing what happened before.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.

valid(H, A, P) :- habitat(H), activity(A), prize(P), affords(H, A), canteen_story(A, P).
shared(A) :- activity(A), share_act(A).
cautionary(A) :- activity(A), warning_act(A).
lesson(A) :- activity(A), lesson_act(A).
compatible(H, A, P) :- valid(H, A, P), shared(A), cautionary(A), lesson(A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid, h in HABITATS.items():
        lines.append(asp.fact("habitat", hid))
        for a in sorted(h.affords):
            lines.append(asp.fact("affords", hid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("canteen_story", aid, "canteen"))
        if aid == "share":
            lines.append(asp.fact("share_act", aid))
            lines.append(asp.fact("lesson_act", aid))
        else:
            lines.append(asp.fact("warning_act", aid))
            lines.append(asp.fact("lesson_act", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(h, a, p) for h, hobj in HABITATS.items() for a, act in ACTIVITIES.items() for p in PRIZES if valid_activity(act, hobj)}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates")
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    if py - cl:
        print("only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Params / CLI
# ---------------------------------------------------------------------------

@dataclass
class ParserParams:
    habitat: str = "watering_hole"
    activity: str = "share"
    hero_kind: str = "rabbit"
    friend_kind: str = "fox"
    hero_name: str = "Milo"
    friend_name: str = "Ruby"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about a canteen, caution, and sharing.")
    ap.add_argument("--habitat", choices=HABITATS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--hero-kind", choices=ANIMALS)
    ap.add_argument("--friend-kind", choices=ANIMALS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
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
    habitat = args.habitat or rng.choice(list(HABITATS))
    activity = args.activity or rng.choice(list(ACTIVITIES))
    if not valid_activity(ACTIVITIES[activity], HABITATS[habitat]):
        raise StoryError(explain_rejection(ACTIVITIES[activity], HABITATS[habitat]))
    hero_kind = args.hero_kind or rng.choice(list(ANIMALS))
    friend_kind = args.friend_kind or rng.choice([k for k in ANIMALS if k != hero_kind])
    hero_name = args.hero_name or animal_name(hero_kind, rng)
    friend_name = args.friend_name or animal_name(friend_kind, rng)
    return StoryParams(
        habitat=habitat,
        activity=activity,
        hero_kind=hero_kind,
        friend_kind=friend_kind,
        hero_name=hero_name,
        friend_name=friend_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(habitat="watering_hole", activity="haul", hero_kind="rabbit", friend_kind="fox", hero_name="Milo", friend_name="Ruby"),
    StoryParams(habitat="riverbank", activity="share", hero_kind="squirrel", friend_kind="bear", hero_name="Hazel", friend_name="Gus"),
    StoryParams(habitat="shade_tree", activity="hide", hero_kind="fox", friend_kind="rabbit", hero_name="Luna", friend_name="Pippa"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} compatible stories:\n")
        for h, a, p in triples:
            print(f"  {h:12} {a:8} {p:8}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.friend_name}: {p.activity} at {p.habitat}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
