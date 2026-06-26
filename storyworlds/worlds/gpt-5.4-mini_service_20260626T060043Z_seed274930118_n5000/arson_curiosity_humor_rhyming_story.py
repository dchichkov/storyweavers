#!/usr/bin/env python3
"""
storyworlds/worlds/arson_curiosity_humor_rhyming_story.py
=========================================================

A standalone storyworld for a small rhyming tale about curiosity, humor, and
fire safety. The world keeps the story child-facing: it never teaches how to
start fires, and it treats arson as a bad, dangerous act that must be stopped.

Seed idea:
- A curious child notices fire things, jokes nervously, and learns to choose a
  safe, funny, sensible path instead of doing something dangerous.

The simulation uses physical meters and emotional memes:
- curiosity, humor, worry, courage, soot, damage, safety, relief

The story is always state-driven:
- curiosity pulls the child toward the spark,
- humor lightens the moment,
- a warning raises worry,
- a safe redirection resolves the tension.

This world is intentionally small and constraint-checked. It supports the
standard Storyweavers CLI and a declarative ASP twin.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    lure: str
    risk: str
    mess: str
    zone: set[str]
    requires: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rescue:
    id: str
    label: str
    prep: str
    tail: str
    kind: str = "thing"


@dataclass
class StoryParams:
    place: str
    activity: str
    rescue: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.mode: str = ""

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = [[]]
        w.mode = self.mode
        return w


def clean_speaker(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9'-]+", "", name)


def rhyme_pair(a: str, b: str) -> str:
    return f"{a} and {b}"


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def rhyming_close(word: str) -> str:
    return {
        "spark": "dark",
        "glow": "show",
        "safety": "gracefully",
        "smoke": "joke",
        "flame": "same",
        "match": "catch",
    }.get(word, "bright")


def _act_stir(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.chars():
        if hero.memes.get("curiosity", 0) < THRESHOLD:
            continue
        if hero.meters.get("spark_interest", 0) < THRESHOLD:
            continue
        sig = ("stir", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["humor"] = hero.memes.get("humor", 0) + 1
        out.append("A tiny chuckle popped up like a bubble in soup.")
    return out


def _act_warning(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.chars():
        if hero.memes.get("curiosity", 0) < THRESHOLD:
            continue
        if hero.meters.get("fire_risk", 0) < THRESHOLD:
            continue
        sig = ("warn", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        out.append("A grown-up warned that fire is not a joke to poke.")
    return out


def _act_safe_choice(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.chars():
        if hero.memes.get("worry", 0) < THRESHOLD:
            continue
        if hero.memes.get("humor", 0) < THRESHOLD:
            continue
        sig = ("safe", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["safety"] = hero.memes.get("safety", 0) + 1
        hero.memes["relief"] = hero.memes.get("relief", 0) + 1
        out.append("They chose a safe trick instead, and the room felt light.")
    return out


CAUSAL_RULES = [_act_stir, _act_warning, _act_safe_choice]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_risk(world: World, hero: Entity, act: Activity) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["spark_interest"] += 1
    sim.get(hero.id).meters["fire_risk"] += 1
    sim.get(hero.id).memes["curiosity"] += 1
    propagate(sim, narrate=False)
    h = sim.get(hero.id)
    return {
        "worry": h.memes.get("worry", 0) >= THRESHOLD,
        "safe": h.memes.get("safety", 0) >= THRESHOLD,
    }


def reasonableness_gate(place: Place, act: Activity, rescue: Rescue) -> bool:
    return act.id in place.affords and act.requires == rescue.id


def explain_rejection(place: Place, act: Activity, rescue: Rescue) -> str:
    return (
        f"(No story: {act.verb} at {place.label} does not pair with {rescue.label}. "
        f"The rescue must actually answer the risk, or the rhyme would be a lie.)"
    )


def tell(place: Place, act: Activity, rescue: Rescue, name: str, gender: str,
         parent: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=clean_speaker(name),
        kind="character",
        type=gender,
        meters={"spark_interest": 0.0, "fire_risk": 0.0},
        memes={"curiosity": 1.0, "humor": 1.0},
    ))
    grown = world.add(Entity(id="grownup", kind="character", type=parent, label=parent))
    item = world.add(Entity(
        id="item",
        label=rescue.label,
        kind="thing",
        owner=hero.id,
        caretaker=grown.id,
        worn_by=hero.id,
    ))

    world.say(
        f"{hero.id} was a little {trait} {gender} who liked a bright idea and a funny rhyme."
    )
    world.say(
        f"At {place.label}, {hero.id} could not help asking about {act.keyword}; {hero.pronoun().capitalize()} "
        f"had curiosity that sparkled like a dime."
    )

    world.para()
    world.say(
        f"One day, {hero.id} reached toward {act.lure}, then paused by the {article(rescue.label)} {rescue.label}."
    )
    hero.meters["spark_interest"] += 1
    hero.meters["fire_risk"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"The room felt a little tense, but the hero cracked a joke so small it barely made a croak."
    )
    propagate(world, narrate=True)

    world.para()
    pred = predict_risk(world, hero, act)
    if pred["worry"]:
        world.say(
            f'"Fire can hurt," {parent} said with a serious face. "It is not for play, no way, no day."'
        )
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} blinked, then grinned. {hero.pronoun().capitalize()} liked the joke, but loved staying safe more."
    )
    gear = world.add(Entity(
        id=rescue.id,
        label=rescue.label,
        kind="thing",
        protective=True,
        owner=hero.id,
        caretaker=grown.id,
        worn_by=hero.id,
    ))
    world.say(
        f'{rescue.prep}, and the whole plan turned sweet instead of sore.'
    )
    hero.memes["humor"] = hero.memes.get("humor", 0) + 1
    hero.memes["safety"] = hero.memes.get("safety", 0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["worry"] = 0.0
    world.say(
        f"{hero.id} chose a safer trick and watched the silly idea float away like a kite."
    )
    world.say(
        f"In the end, {hero.id} kept {rescue.label}, kept the house bright, and kept the night polite."
    )

    world.facts.update(hero=hero, grown=grown, item=item, act=act, rescue=gear, place=place)
    return world


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", indoor=True, affords={"candle", "match"}),
    "shed": Place(id="shed", label="the shed", indoor=False, affords={"match", "torch"}),
    "camp": Place(id="camp", label="the campfire circle", indoor=False, affords={"torch"}),
    "hall": Place(id="hall", label="the town hall", indoor=True, affords={"candle"}),
}

ACTIVITIES = {
    "candle": Activity(
        id="candle",
        verb="play with a candle flame",
        gerund="playing with candle flames",
        lure="the candle's little gold glow",
        risk="a dangerous burn or bigger fire",
        mess="smoke",
        zone={"hands", "table"},
        requires="buckets",
        keyword="candle",
        tags={"fire", "danger", "curiosity"},
    ),
    "match": Activity(
        id="match",
        verb="fiddle with a match",
        gerund="fiddling with matches",
        lure="a tiny matchbox",
        risk="a risky spark that could spread",
        mess="smoke",
        zone={"hands", "air"},
        requires="sprinkler",
        keyword="match",
        tags={"fire", "danger", "arson", "curiosity"},
    ),
    "torch": Activity(
        id="torch",
        verb="watch a torch",
        gerund="watching a torch glow",
        lure="the torch's tiny twinkle",
        risk="a hot flame near too much wood",
        mess="smoke",
        zone={"hands", "wood"},
        requires="bucket",
        keyword="torch",
        tags={"fire", "curiosity"},
    ),
}

RESCUES = {
    "buckets": Rescue(
        id="buckets",
        label="two buckets of water",
        prep="They lined up two buckets of water as a safe rhyme",
        tail="stood ready like a tidy little brigade",
    ),
    "sprinkler": Rescue(
        id="sprinkler",
        label="a sprinkler plan",
        prep="They chose a sprinkler plan and a careful game",
        tail="sprang into place like a helpful parade",
    ),
    "bucket": Rescue(
        id="bucket",
        label="a bucket and a blanket",
        prep="They kept a bucket and a blanket near the flame",
        tail="made the setup safer, calmer, and more tame",
    ),
}

NAMES = {
    "girl": ["Mia", "Nora", "Lily", "Ava", "Zoe"],
    "boy": ["Leo", "Finn", "Max", "Theo", "Noah"],
}

TRAITS = ["curious", "jolly", "bright", "silly", "spry"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for aid, act in ACTIVITIES.items():
            if aid not in place.affords:
                continue
            for rid, rescue in RESCUES.items():
                if reasonableness_gate(place, act, rescue):
                    out.append((pid, aid, rid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, place, act = f["hero"], f["place"], f["act"]
    return [
        f'Write a short rhyming story for a child about {hero.id} at {place.label} and the word "{act.keyword}".',
        f"Tell a gentle, funny tale where {hero.id} feels curious about {act.verb} but chooses safety instead.",
        f"Write a small story with a rhyme about curiosity, humor, and a grown-up helping a child avoid fire trouble.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, grown, act, rescue, place = f["hero"], f["grown"], f["act"], f["rescue"], f["place"]
    return [
        QAItem(
            question=f"What made {hero.id} feel curious at {place.label}?",
            answer=f"{hero.id} felt curious about {act.lure} at {place.label}, and that made the moment feel bright and bouncy.",
        ),
        QAItem(
            question=f"Why did {grown.label} warn {hero.id}?",
            answer=f"{grown.label} warned {hero.id} because {act.verb} could lead to danger, and fire is not for play.",
        ),
        QAItem(
            question=f"How did {hero.id} keep the story safe in the end?",
            answer=f"{hero.id} chose {rescue.label} and a safer plan instead of chasing the risky spark.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is arson?",
            answer="Arson means setting a fire on purpose, and it is very dangerous and against the rules.",
        ),
        QAItem(
            question="Why should children stay away from matches?",
            answer="Matches can make fire, and fire can hurt people, animals, and homes very quickly.",
        ),
        QAItem(
            question="What does a bucket of water do in a fire safety plan?",
            answer="A bucket of water can help keep a small flame from growing, but adults should handle fire safety.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="candle", rescue="buckets", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="shed", activity="match", rescue="sprinkler", name="Leo", gender="boy", parent="father", trait="silly"),
    StoryParams(place="camp", activity="torch", rescue="bucket", name="Nora", gender="girl", parent="mother", trait="jolly"),
]


ASP_RULES = r"""
risk(A) :- activity(A), need(A,N), rescue(R), answers(R,N).
safe_story(P,A,R) :- place(P), affords(P,A), risk(A), safe_fix(A,R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("need", aid, a.requires))
    for rid, r in RESCUES.items():
        lines.append(asp.fact("rescue", rid))
        lines.append(asp.fact("answers", rid, rid))
        lines.append(asp.fact("safe_fix", rid, r.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_story/3."))
    return sorted(set(asp.atoms(model, "safe_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world about curiosity, humor, and fire safety.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.place and args.activity and args.rescue:
        place, act, rescue = PLACES[args.place], ACTIVITIES[args.activity], RESCUES[args.rescue]
        if not reasonableness_gate(place, act, rescue):
            raise StoryError(explain_rejection(place, act, rescue))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.rescue is None or c[2] == args.rescue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, act_id, rescue_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place_id, activity=act_id, rescue=rescue_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        ACTIVITIES[params.activity],
        RESCUES[params.rescue],
        params.name,
        params.gender,
        params.parent,
        params.trait,
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
        print(asp_program("#show safe_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show safe_story/3."))
        triples = sorted(set(asp.atoms(model, "safe_story")))
        print(f"{len(triples)} compatible story combos:")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.activity} at {p.place} (rescue: {p.rescue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
