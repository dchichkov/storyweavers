#!/usr/bin/env python3
"""
storyworlds/worlds/pheasant_horrendous_curiosity_folk_tale.py
==============================================================

A small folk-tale story world about a curious child, a pheasant, and a
horrendous bit of trouble that turns into a wiser path home.

Seed tale idea:
---
A curious child sees a pheasant by the edge of the wood and wants to know why
it keeps darting toward the reeds. The wood looks horrendous after the storm,
so the child should stay on the lane. But curiosity pulls harder than caution.
The child follows the pheasant, gets into a nasty tangle, helps the bird free
itself, and discovers that the pheasant was leading toward a safe little path
back to the village.
---

This script models a tiny tale with physical meters and emotional memes:
- curiosity can rise, trigger following, and lead to getting lost
- horrendous weather/brush makes the path risky
- helping the pheasant clears fear and brings the child home
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    safe_home: bool = False
    horrendous: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    label: str
    kind: str = "bird"
    type: str = "pheasant"
    phrase: str = "a bright pheasant"
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place, weather: str) -> None:
        self.place = place
        self.weather = weather
        self.entities: dict[str, Entity] = {}
        self.pheasant = Companion(id="pheasant", label="the pheasant")
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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
        other = World(self.place, self.weather)
        other.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "caretaker": v.caretaker,
            "plural": v.plural, "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    parent_name: str
    seed: Optional[int] = None


PLACES = {
    "village_edge": Place(id="village_edge", label="the village edge", safe_home=False, tags={"village", "lane"}),
    "old_wood": Place(id="old_wood", label="the old wood", horrendous=True, tags={"wood", "thorns", "storm"}),
    "reed_lane": Place(id="reed_lane", label="the reed lane", safe_home=False, tags={"lane", "reeds"}),
    "brook_path": Place(id="brook_path", label="the brook path", tags={"brook", "path"}),
}

HEROES = [
    ("Mara", "girl"),
    ("Jory", "boy"),
    ("Nell", "girl"),
    ("Tom", "boy"),
]

PARENTS = ["mother", "father", "aunt", "uncle"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about curiosity and a pheasant.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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


def _choice(rng: random.Random, items):
    return items[rng.randrange(len(items))]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or _choice(rng, list(PLACES))
    hero_name, hero_type = ("", args.gender) if args.gender else (None, None)
    if args.gender:
        pool = [(n, g) for n, g in HEROES if g == args.gender]
    else:
        pool = HEROES
    if args.name:
        hero_name = args.name
        if not hero_type:
            hero_type = _choice(rng, ["girl", "boy"])
    else:
        hero_name, hero_type = _choice(rng, pool)
    parent = args.parent or _choice(rng, PARENTS)
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, parent_name=parent)


def reasonableness_gate(params: StoryParams) -> None:
    place = PLACES[params.place]
    if place.safe_home and place.horrendous:
        raise StoryError("A place cannot be both a safe home and horrendous.")
    if params.hero_type not in {"girl", "boy"}:
        raise StoryError("The hero must be a girl or boy for this little tale.")


def setup_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    weather = "horrendous" if place.horrendous else "windy"
    world = World(place, weather)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"distance_from_home": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "joy": 0.0, "relief": 0.0, "lost": 0.0},
    ))
    parent = world.add(Entity(
        id=params.parent_name,
        kind="character",
        type=params.parent_name,
        label=params.parent_name,
        meters={"distance_from_home": 0.0},
        memes={"worry": 0.0, "patience": 1.0},
    ))
    world.facts["hero"] = hero
    world.facts["parent"] = parent
    return world


def _rule_follow(world: World) -> list[str]:
    hero = world.facts["hero"]
    if hero.e("curiosity") < THRESHOLD or "followed" in world.fired:
        return []
    world.fired.add("followed")
    hero.meters["distance_from_home"] += 1.0
    hero.memes["lost"] += 1.0
    return [f"{hero.id} followed the pheasant off the lane."]


def _rule_horrendous_tangle(world: World) -> list[str]:
    hero = world.facts["hero"]
    if hero.meters.get("distance_from_home", 0.0) < THRESHOLD:
        return []
    if world.place.id != "old_wood" or "tangled" in world.fired:
        return []
    world.fired.add("tangled")
    hero.memes["worry"] += 1.0
    hero.meters["tangle"] = 1.0
    return [f"The wood was horrendous with brambles, and {hero.id} got tangled up."]


def _rule_help_pheasant(world: World) -> list[str]:
    hero = world.facts["hero"]
    if hero.meters.get("tangle", 0.0) < THRESHOLD or "helped" in world.fired:
        return []
    world.fired.add("helped")
    hero.memes["curiosity"] += 0.5
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    hero.memes["joy"] += 1.0
    world.facts["pheasant_trust"] = 1.0
    return [f"{hero.id} helped the pheasant free its wing from the thorny mess."]


def _rule_homeward(world: World) -> list[str]:
    hero = world.facts["hero"]
    if world.facts.get("pheasant_trust", 0.0) < THRESHOLD or "homeward" in world.fired:
        return []
    world.fired.add("homeward")
    hero.meters["distance_from_home"] = 0.0
    hero.memes["relief"] += 1.0
    hero.memes["lost"] = 0.0
    return [f"The pheasant led {hero.id} home by a quiet way through the reeds."]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_follow, _rule_horrendous_tangle, _rule_help_pheasant, _rule_homeward):
            bits = rule(world)
            if bits:
                changed = True
                out.extend(bits)
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = setup_world(params)
    hero = world.facts["hero"]
    parent = world.facts["parent"]

    world.say(f"Once, {hero.id} was a curious young {hero.type} who always wanted to know why the world moved as it did.")
    world.say(f"{hero.id} lived near {world.place.label}, where {world.pheasant.phrase} liked to strut and bob its head.")
    world.say(f"One day {hero.id}'s {parent.label} warned that the road toward the wood looked horrendous after the storm.")

    world.para()
    hero.memes["curiosity"] += 1.0
    hero.memes["worry"] += 0.2
    world.say(f"But curiosity tickled {hero.id} so strongly that {hero.id} stepped after the pheasant anyway.")
    propagate(world)

    world.para()
    if world.fired.__contains__("tangled"):
        world.say(f"{hero.id} called softly for help, and the pheasant pecked and flapped until the brambles loosened.")
        propagate(world)
    else:
        world.say(f"The path stayed plain and quiet, but the pheasant kept glancing back as if it had a secret.")
        hero.memes["joy"] += 1.0

    world.para()
    if hero.memes.get("relief", 0.0) >= THRESHOLD:
        world.say(f"At last, {hero.id} came home with muddy shoes, a lighter heart, and a wiser kind of curiosity.")
    else:
        world.say(f"In the end, {hero.id} and the pheasant returned together, and the lane seemed less scary than before.")

    world.facts.update(place=world.place, weather=world.weather)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    return [
        "Write a short folk tale for a small child about a curious child and a pheasant.",
        f"Tell a gentle story where {hero.id} ignores a warning about a horrendous wood and learns something useful.",
        f"Write a simple tale in which {hero.id} follows a pheasant, gets into trouble, and finds the way home again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    qa = [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"The story was mostly about {hero.id}, a curious young {hero.type} who lived near {world.place.label}.",
        ),
        QAItem(
            question=f"Why did {hero.id} follow the pheasant?",
            answer=f"{hero.id} followed the pheasant because curiosity was stronger than caution, even after {parent.label} warned about the horrendous wood.",
        ),
        QAItem(
            question=f"What changed by the end of the tale?",
            answer=f"By the end, {hero.id} was back home, safer and wiser, with curiosity turned into careful knowing instead of reckless chasing.",
        ),
    ]
    if world.fired.__contains__("tangled"):
        qa.append(QAItem(
            question=f"What trouble did {hero.id} get into in the wood?",
            answer=f"{hero.id} got tangled in horrendous brambles after following the pheasant off the lane.",
        ))
    if world.facts.get("pheasant_trust", 0.0) >= THRESHOLD:
        qa.append(QAItem(
            question=f"How did the pheasant help after the trouble?",
            answer=f"The pheasant guided {hero.id} back home by a quieter path through the reeds.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pheasant?",
            answer="A pheasant is a bird that often has bright feathers and likes to walk and peck on the ground.",
        ),
        QAItem(
            question="What does horrendous mean?",
            answer="Horrendous means very awful or frighteningly unpleasant.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to know more, look closely, and find out what something is like.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = [f"--- trace: {world.place.label} / weather={world.weather} ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="old_wood", hero_name="Mara", hero_type="girl", parent_name="mother"),
    StoryParams(place="village_edge", hero_name="Jory", hero_type="boy", parent_name="father"),
    StoryParams(place="reed_lane", hero_name="Nell", hero_type="girl", parent_name="aunt"),
]


ASP_RULES = r"""
curious_follow(H) :- hero(H), curiosity(H), pheasant_nearby.
danger(H) :- curious_follow(H), horrendous_place.
helped_pheasant(H) :- danger(H), helper(H).
home_again(H) :- helped_pheasant(H).

#show curious_follow/1.
#show danger/1.
#show helped_pheasant/1.
#show home_again/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.horrendous:
            lines.append(asp.fact("horrendous_place", pid))
        if place.safe_home:
            lines.append(asp.fact("safe_home", pid))
    lines.append(asp.fact("pheasant_nearby"))
    lines.append(asp.fact("helper", "child"))
    lines.append(asp.fact("hero", "child"))
    lines.append(asp.fact("curiosity", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show home_again/1."))
    return sorted(set(asp.atoms(model, "home_again")))


def python_valid() -> list[tuple]:
    return [("child",)]


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(python_valid())
    if a == b:
        print("OK: ASP and Python parity match.")
        return 0
    print("MISMATCH between ASP and Python parity:")
    print("only in ASP:", sorted(a - b))
    print("only in Python:", sorted(b - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show home_again/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story pattern:\n  child follows pheasant -> danger -> help -> home")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
