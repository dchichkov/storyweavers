#!/usr/bin/env python3
"""
storyworlds/worlds/paralyze_meadow_juniper_sharing_twist_comedy.py
===================================================================

A tiny comedy story world about sharing at a meadow by a juniper bush, where a
small twist of circumstance leaves everyone briefly paralyzed with surprise
before the joke lands and the sharing gets sweeter.

Seed tale sketch:
---
Two friends meet in a meadow near a juniper bush with a basket of snacks.
They want to share everything fairly, but a silly twist of wind tangles the
blanket and freezes them in place for a moment. After a beat of stunned
silence, they laugh, sort it out, and share the treats anyway.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caregiver: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    twist: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SharingThing:
    label: str
    phrase: str
    type: str
    plural: bool = False
    fit_for: set[str] = field(default_factory=set)
    risk: str = "messy"


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    current_activity: Optional[str] = None

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.current_activity = self.current_activity
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "meadow": Place(
        name="the meadow",
        detail="The meadow was soft and green, with a round juniper bush swaying at the edge.",
        affords={"sharing", "twist"},
    )
}

ACTIVITIES = {
    "sharing": Activity(
        id="sharing",
        verb="share the snack basket",
        gerund="sharing snacks",
        twist="a tiny disagreement over the last berry tart",
        result="they got back to laughing and dividing things fairly",
        tags={"sharing", "snack", "meadow"},
    ),
    "twist": Activity(
        id="twist",
        verb="twist the blanket",
        gerund="twisting the blanket",
        twist="a silly gust of wind gave the blanket a spin",
        result="the blanket puffed up like a comic sail",
        tags={"twist", "wind", "meadow"},
    ),
}

SHARING_THINGS = {
    "basket": SharingThing(
        label="snack basket",
        phrase="a picnic basket full of berries and little crackers",
        type="basket",
        fit_for={"sharing"},
        risk="messy",
    ),
    "blanket": SharingThing(
        label="picnic blanket",
        phrase="a checkered picnic blanket",
        type="blanket",
        fit_for={"twist"},
        risk="wrinkly",
    ),
    "tart": SharingThing(
        label="berry tart",
        phrase="a berry tart with a shiny crust",
        type="tart",
        fit_for={"sharing"},
        risk="squished",
    ),
}

NAMES = ["Juniper", "Milo", "Pia", "Bea", "Nico", "Tess", "Owen", "Rae"]
TYPES = ["girl", "boy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the setting affords the featured activity and the
% sharing thing fits that activity.
valid_story(Place, Act, Thing) :- affords(Place, Act), fit_for(Thing, Act).

% A twist is funny if it can happen in the meadow and does not ruin the story.
funny_twist(Place, Act, Thing) :- valid_story(Place, Act, Thing), place_has_juniper(Place).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_has_juniper", pid))
        for act in sorted(place.affords):
            lines.append(asp.fact("affords", pid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for tag in sorted(act.tags):
            lines.append(asp.fact("tag", aid, tag))
    for tid, thing in SHARING_THINGS.items():
        lines.append(asp.fact("thing", tid))
        for act in sorted(thing.fit_for):
            lines.append(asp.fact("fit_for", tid, act))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, a, t) for p, a, t in valid_combos()}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for act_id in place.affords:
            for thing_id, thing in SHARING_THINGS.items():
                if act_id in thing.fit_for:
                    out.append((place_id, act_id, thing_id))
    return out


def explain_rejection(place: str, activity: str, thing: str) -> str:
    p = PLACES[place]
    a = ACTIVITIES[activity]
    t = SHARING_THINGS[thing]
    return (
        f"(No story: {p.name} can host {a.gerund}, but {t.label} is not a natural fit "
        f"for that setup, so the little comedy would not land cleanly.)"
    )


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def narrate_setup(world: World, hero: Entity, friend: Entity, thing: Entity) -> None:
    world.say(f"{hero.id} and {friend.id} met in {world.place.name}.")
    world.say(world.place.detail)
    world.say(
        f"They brought {thing.phrase} because they wanted to share it fairly and make "
        f"the afternoon feel like a tiny celebration."
    )


def predict(world: World, activity: Activity, thing: Entity) -> dict:
    sim = world.copy()
    apply_activity(sim, activity, narrate=False)
    tense = sim.facts.get("paralyzed", False)
    return {"paralyzed": tense, "comic": True}


def apply_activity(world: World, activity: Activity, narrate: bool = True) -> None:
    if world.current_activity == activity.id:
        return
    world.current_activity = activity.id

    if activity.id == "sharing":
        for e in world.characters():
            e.memes["goodwill"] = e.memes.get("goodwill", 0) + 1
        world.facts["shared"] = True
        if narrate:
            world.say("They opened the basket and started to split the treats into two tidy piles.")
        # The twist arrives during sharing.
        apply_twist(world, ACTIVITIES["twist"], narrate=narrate)
    elif activity.id == "twist":
        apply_twist(world, activity, narrate=narrate)


def apply_twist(world: World, activity: Activity, narrate: bool = True) -> None:
    if ("twist", activity.id) in world.fired:
        return
    world.fired.add(("twist", activity.id))

    hero, friend = world.characters()
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
    friend.memes["surprise"] = friend.memes.get("surprise", 0) + 1
    hero.memes["paralyzed"] = 1
    friend.memes["paralyzed"] = 1
    world.facts["paralyzed"] = True

    if narrate:
        world.say(
            f"Then {activity.twist}, and for one second both friends were so shocked "
            f"they looked paralyzed, like two statues with snack crumbs."
        )
        world.say(
            f"Their blanket did a funny twist in the wind, and even the juniper bush "
            f"seemed to be trying not to laugh."
        )


def resolve(world: World, hero: Entity, friend: Entity, thing: Entity) -> None:
    hero.memes["paralyzed"] = 0
    friend.memes["paralyzed"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    world.say(
        f"Then {hero.id} blinked, {friend.id} snorted a giggle, and the two of them "
        f"carefully straightened the blanket."
    )
    world.say(
        f"They laughed at the whole silly twist, shared the last tart in half, and "
        f"sat by the juniper bush with crumbs on their smiles."
    )


def tell(place: Place, activity: Activity, thing_cfg: SharingThing,
         hero_name: str = "Juniper", friend_name: str = "Milo",
         hero_type: str = "girl", friend_type: str = "boy") -> World:
    world = World(place)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["cheerful", "patient"],
        meters={"energy": 1.0},
        memes={"hope": 1.0},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_type,
        traits=["silly", "kind"],
        meters={"energy": 1.0},
        memes={"hope": 1.0},
    ))
    thing = world.add(Entity(
        id=thing_cfg.type,
        kind="thing",
        type=thing_cfg.type,
        label=thing_cfg.label,
        phrase=thing_cfg.phrase,
        owner=hero.id,
        plural=thing_cfg.plural,
    ))

    narrate_setup(world, hero, friend, thing)

    world.para()
    world.say(f"They wanted to {activity.verb}, but the meadow had a twist ready.")
    world.say(
        f"{hero.id} reached for the basket first, and {friend.id} reached for the blanket "
        f"at the same time, which made the moment wobble in the funniest way."
    )
    apply_activity(world, activity, narrate=True)

    world.para()
    resolve(world, hero, friend, thing)

    world.facts.update(
        hero=hero,
        friend=friend,
        thing=thing,
        activity=activity,
        place=place,
        shared=True,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Story text, Q&A
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    thing: str
    name: str
    friend_name: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy story for a young child set in {f["place"].name} that includes the word "sharing".',
        f'Tell a gentle story where {f["hero"].id} and {f["friend"].id} try to share {f["thing"].label} in the meadow near a juniper bush, but a twist makes them freeze for a moment.',
        f'Write a simple story about friends in a meadow, a juniper bush, and a silly twist that ends in laughter and sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    thing: Entity = f["thing"]
    act: Activity = f["activity"]

    return [
        QAItem(
            question=f"Who went to the meadow to share the snack?",
            answer=f"{hero.id} and {friend.id} went to the meadow together because they wanted to share {thing.label}.",
        ),
        QAItem(
            question=f"What made the friends look paralyzed for a second?",
            answer=f"A silly twist in the wind made them freeze in surprise for a moment, like little statues with crumbs.",
        ),
        QAItem(
            question=f"What did they do after the twist was over?",
            answer=f"They laughed, straightened the blanket, and kept sharing the treats fairly.",
        ),
        QAItem(
            question=f"Why was the juniper bush important in the story?",
            answer=f"The juniper bush gave the meadow a cozy landmark, and it stood there while the friends shared and laughed.",
        ),
        QAItem(
            question=f"What kind of story was this?",
            answer=f"It was a comedy about sharing and a twist that turned into a joke instead of a problem.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "sharing": [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people enjoy part of what you have, like food, toys, or space.",
        ),
        QAItem(
            question="Why do children share snacks?",
            answer="Children share snacks so everyone can have some and the moment can feel friendly and fair.",
        ),
    ],
    "twist": [
        QAItem(
            question="What is a twist?",
            answer="A twist is a turning or spinning motion, like when a ribbon curls or a blanket flips in the wind.",
        ),
    ],
    "meadow": [
        QAItem(
            question="What is a meadow?",
            answer="A meadow is a wide open field with grass and often flowers, where birds and little animals can play.",
        ),
    ],
    "juniper": [
        QAItem(
            question="What is a juniper?",
            answer="A juniper is a kind of plant that can be a bush or a tree, with green needles or berries.",
        ),
    ],
    "paralyze": [
        QAItem(
            question="What does paralyze mean?",
            answer="Paralyze means to make someone unable to move for a while, or to leave them feeling frozen with surprise or fear.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.update({"meadow", "juniper", "sharing", "twist", "paralyze"})
    out: list[QAItem] = []
    for tag in ["sharing", "twist", "meadow", "juniper", "paralyze"]:
        out.extend(WORLD_KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="meadow", activity="sharing", thing="basket", name="Juniper", friend_name="Milo"),
    StoryParams(place="meadow", activity="sharing", thing="tart", name="Pia", friend_name="Owen"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small comedy story world about sharing in a meadow.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--thing", choices=SHARING_THINGS)
    ap.add_argument("--name")
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
    if args.activity and args.thing:
        if (args.place or "meadow", args.activity, args.thing) not in valid_combos():
            raise StoryError(explain_rejection(args.place or "meadow", args.activity, args.thing))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.thing is None or c[2] == args.thing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, thing = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice([n for n in NAMES if n != name])
    return StoryParams(place=place, activity=activity, thing=thing, name=name, friend_name=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        ACTIVITIES[params.activity],
        SHARING_THINGS[params.thing],
        hero_name=params.name,
        friend_name=params.friend_name,
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for place, act, thing in stories:
            print(f"  {place:8} {act:8} {thing:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.name}: {p.activity} in {p.place} ({p.thing})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
