#!/usr/bin/env python3
"""
A small heartwarming storyworld about a tourist, a lotus pond, and a spluttery
moment that turns into friendship.

This world is built from the seed words:
- tour-ist
- lotus
- splutter

Narrative instruments:
- Curiosity
- Humor
- Friendship
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    pronoun_set: str = "it"

    def pronoun(self, case: str = "subject") -> str:
        if self.pronoun_set == "she":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.pronoun_set == "he":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    affordances: set[str] = field(default_factory=set)
    detail: str = ""


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    splash: str
    surprise: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    pronouns: str
    friend_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        nw = World(self.place)
        nw.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "traits": list(v.traits), "owner": v.owner,
            "meters": dict(v.meters), "memes": dict(v.memes), "pronoun_set": v.pronoun_set
        }) for k, v in self.entities.items()}
        nw.paragraphs = [[]]
        nw.facts = dict(self.facts)
        nw.fired = set(self.fired)
        return nw


@dataclass
class Rule:
    name: str
    apply: callable


def _r_splutter(world: World) -> list[str]:
    out = []
    tourist = world.entities.get("tourist")
    pond = world.entities.get("pond")
    if not tourist or not pond:
        return out
    if tourist.meters.get("curiosity", 0.0) < THRESHOLD:
        return out
    if ("splutter", tourist.id) in world.fired:
        return out
    world.fired.add(("splutter", tourist.id))
    tourist.meters["wet"] = tourist.meters.get("wet", 0.0) + 1
    tourist.memes["embarrassment"] = tourist.memes.get("embarrassment", 0.0) + 1
    out.append(f"{tourist.pronoun().capitalize()} leaned too close and spluttered at the water.")
    return out


def _r_laugh_turn(world: World) -> list[str]:
    out = []
    tourist = world.entities.get("tourist")
    friend = world.entities.get("friend")
    if not tourist or not friend:
        return out
    if tourist.memes.get("embarrassment", 0.0) < THRESHOLD:
        return out
    sig = ("laugh_turn",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.memes["humor"] = friend.memes.get("humor", 0.0) + 1
    out.append(f"{friend.id} laughed kindly and handed over a soft cloth.")
    return out


def _r_friendship(world: World) -> list[str]:
    out = []
    tourist = world.entities.get("tourist")
    friend = world.entities.get("friend")
    if not tourist or not friend:
        return out
    if tourist.memes.get("embarrassment", 0.0) < THRESHOLD:
        return out
    if friend.memes.get("humor", 0.0) < THRESHOLD:
        return out
    sig = ("friendship",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tourist.memes["friendship"] = tourist.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    out.append("Soon they were smiling together like old friends.")
    return out


RULES = [Rule("splutter", _r_splutter), Rule("laugh_turn", _r_laugh_turn), Rule("friendship", _r_friendship)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "lotus_pond": Place(
        id="lotus_pond",
        label="the lotus pond",
        affordances={"look", "listen", "lean"},
        detail="The lotus pond was still and bright, with green leaves resting on the water.",
    ),
    "garden_path": Place(
        id="garden_path",
        label="the garden path",
        affordances={"look", "listen", "lean"},
        detail="The garden path curved past flower beds and a tiny pond at its center.",
    ),
}

ACTIVITIES = {
    "lotus": Activity(
        id="lotus",
        verb="look at the lotus flowers",
        gerund="looking at lotus flowers",
        splash="splutter",
        surprise="The petals looked like little painted boats.",
        keyword="lotus",
        tags={"lotus", "curiosity"},
    ),
    "lotus_breeze": Activity(
        id="lotus_breeze",
        verb="watch the lotus leaves bob",
        gerund="watching the lotus leaves bob",
        splash="splutter",
        surprise="The leaves nodded like they were telling a secret joke.",
        keyword="lotus",
        tags={"lotus", "humor"},
    ),
}

NAMES = ["Mina", "Taro", "Ivy", "Leo", "Nora", "Owen", "Ari", "Pia"]
FRIEND_NAMES = ["June", "Sam", "Milo", "Elle", "Zuri", "Ben", "Tess", "Kai"]


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    pronoun_set = params.pronouns

    tourist = world.add(Entity(
        id="tourist",
        kind="character",
        type="tourist",
        label=params.name,
        traits=["curious", "gentle"],
        meters={"curiosity": 1.0},
        pronoun_set=pronoun_set,
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type="child",
        label=params.friend_name,
        traits=["friendly", "cheerful"],
        pronoun_set="she" if pronoun_set == "she" else "he" if pronoun_set == "he" else "it",
    ))
    pond = world.add(Entity(
        id="pond",
        kind="thing",
        type="lotus pond",
        label="the lotus pond",
        phrase="a quiet lotus pond with shining leaves",
    ))

    act = ACTIVITIES[params.activity]
    world.facts.update(tourist=tourist, friend=friend, pond=pond, activity=act, place=place)

    world.say(f"{tourist.label} was a little tourist who loved to wander and wonder.")
    world.say(f"{tourist.pronoun().capitalize()} had a big curiosity and a soft heart for pretty places.")
    world.say(f"{friend.label} liked walking nearby, because {friend.label.lower()} always noticed when someone needed a smile.")
    world.para()
    world.say(place.detail)
    world.say(f"One afternoon, {tourist.label} went there with {friend.label} to {act.gerund}.")
    world.say(act.surprise)
    world.say(f"{tourist.pronoun().capitalize()} wanted to {act.verb} just a little closer, because the lotus flowers looked so inviting.")
    world.para()
    world.say(f"Then {tourist.pronoun()} leaned in too far and {act.splash}ed.")
    propagate(world, narrate=True)
    world.para()
    if tourist.memes.get("friendship", 0.0) >= THRESHOLD:
        world.say(f"{friend.label} and {tourist.label} laughed softly, and the moment felt warm instead of awkward.")
        world.say(f"By the end, {tourist.label} was no longer just a visitor; {tourist.pronoun()} had made a friend beside the lotus pond.")
    else:
        world.say(f"{friend.label} still stayed close, ready with a smile.")
    return world


def generation_prompts(world: World) -> list[str]:
    act: Activity = world.facts["activity"]
    place: Place = world.facts["place"]
    return [
        f'Write a heartwarming story for a young child about a curious tour-ist at {place.label} who notices a {act.keyword}.',
        f'Write a gentle story where a tourist wants to {act.verb} and ends up with a funny {act.splash} before finding friendship.',
        f'Create a small story that includes the words "{act.keyword}" and "splutter" and ends with kindness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    tourist: Entity = world.facts["tourist"]
    friend: Entity = world.facts["friend"]
    act: Activity = world.facts["activity"]
    place: Place = world.facts["place"]
    return [
        QAItem(
            question=f"Who went to {place.label} in the story?",
            answer=f"{tourist.label} the tourist went there with {friend.label}.",
        ),
        QAItem(
            question=f"What did {tourist.label} want to do near the lotus flowers?",
            answer=f"{tourist.label} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"What happened when {tourist.label} leaned too close to the water?",
            answer=f"{tourist.label} spluttered at the water, and the moment turned funny instead of bad.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {tourist.label} and {friend.label} smiling together and feeling like friends.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lotus?",
            answer="A lotus is a water flower that grows with round leaves on top of quiet water.",
        ),
        QAItem(
            question="Why do people laugh kindly when someone splutters?",
            answer="They may laugh kindly because spluttering can sound funny, and a kind laugh helps the other person feel better.",
        ),
        QAItem(
            question="What does curiosity help people do?",
            answer="Curiosity helps people notice new things, ask questions, and learn about the world around them.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, share smiles, and try to be helpful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(r for r, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affordances):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
        lines.append(asp.fact("splashes", aid, "water"))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(A) :- activity(A), splashes(A, water).
funny_moment(A) :- activity(A), at_risk(A).
kind_turn :- funny_moment(A).
friendly_end :- kind_turn.
#show at_risk/1.
#show funny_moment/1.
#show kind_turn/0.
#show friendly_end/0.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    shown = {sym.name for sym in model}
    expected = {"at_risk", "funny_moment", "kind_turn", "friendly_end"}
    if expected.issubset(shown):
        print("OK: ASP rules are present and solvable.")
        return 0
    print("MISMATCH: ASP verification failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming storyworld about a tourist, lotus flowers, and friendship.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--name")
    ap.add_argument("--pronouns", choices=["she", "he", "it"])
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
    place = args.place or rng.choice(list(PLACES))
    activity = args.activity or rng.choice(list(ACTIVITIES))
    pronouns = args.pronouns or rng.choice(["she", "he"])
    name = args.name or rng.choice(NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    if name == friend_name:
        friend_name = rng.choice([n for n in FRIEND_NAMES if n != friend_name])
    return StoryParams(place=place, activity=activity, name=name, pronouns=pronouns, friend_name=friend_name)


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
    StoryParams(place="lotus_pond", activity="lotus", name="Mina", pronouns="she", friend_name="June"),
    StoryParams(place="garden_path", activity="lotus_breeze", name="Leo", pronouns="he", friend_name="Tess"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("\n".join(str(sym) for sym in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
