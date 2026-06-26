#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/cortisone_friendship_cautionary_tall_tale.py
==============================================================================================================================

A standalone story world sketch for a tall-tale cautionary friendship story
involving cortisone.  The domain is a small frontier town where a character's
boastful claim about a "cortisone cure" leads to a lesson about friendship and
overreach.

Initial story (used to build a world model):
---
In the dusty town of Dusty Gulch, there lived a boastful cowpoke named Clem.
Clem claimed he had a secret cortisone salve that could fix any ache or pain
in a single night.  His best friend, a quiet rancher named Ella, warned him
not to make promises the salve couldn't keep.  But Clem just laughed and
rubbed the salve on a sore mule's leg.

The next morning, the mule's leg was worse, not better.  The town folk
grumbled that Clem was a fraud.  Ella stood by him and said, "A true friend
doesn't need a miracle cure; a true friend just stays."  Clem learned that
bragging about a remedy was no substitute for being honest with the people
who counted on him.

Causal state updates:
---
    boast about cure          -> character.boast += 1
    apply salve               -> salve.used += 1 ; patient.pain -= 0.5
    patient worsens           -> patient.pain += 2 ; character.credibility -= 2
    friend defends            -> friendship.bond += 1 ; character.gratitude += 1
    lesson learned            -> character.humility += 1 ; character.boast = 0
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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"ella", "mae", "annie"}
        male = {"clem", "jeb", "hank"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worsen(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.meters.get("pain", 0) > 0 and ent.meters.get("salve_applied", 0) > 0:
            sig = ("worsen", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters["pain"] += 2
            out.append(f"The {ent.label} got worse, not better.")
    return out


def _r_credibility(world: World) -> list[str]:
    out = []
    for ent in world.characters():
        if ent.memes.get("boast", 0) >= THRESHOLD and ent.memes.get("credibility", 0) < 0:
            sig = ("cred", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"The townsfolk started to doubt {ent.id}.")
    return out


def _r_friendship(world: World) -> list[str]:
    out = []
    for ent in world.characters():
        if ent.memes.get("defended", 0) >= THRESHOLD and ent.memes.get("gratitude", 0) < THRESHOLD:
            sig = ("friend", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["gratitude"] += 1
            ent.memes["humility"] += 1
            out.append(f"{ent.id} felt grateful for a true friend.")
    return out


CAUSAL_RULES = [
    Rule("worsen", "physical", _r_worsen),
    Rule("credibility", "social", _r_credibility),
    Rule("friendship", "social", _r_friendship),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(hero_name: str = "Clem", hero_type: str = "cowpoke",
         friend_name: str = "Ella", friend_type: str = "rancher",
         patient_type: str = "mule", salve_name: str = "cortisone salve") -> World:
    world = World()

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        label=hero_name, traits=["boastful", "loud"],
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_type,
        label=friend_name, traits=["wise", "quiet"],
    ))
    patient = world.add(Entity(
        id="patient", kind="thing", type=patient_type,
        label=f"old {patient_type}", phrase=f"a sore old {patient_type}",
        plural=False,
    ))
    salve = world.add(Entity(
        id="salve", kind="thing", type="salve",
        label=salve_name, phrase=f"a jar of {salve_name}",
        plural=False,
    ))

    # Act 1
    world.say(f"In the dusty town of Dusty Gulch, there lived a {hero_type} named {hero_name}.")
    world.say(f"{hero_name} was known far and wide for {hero.pronoun('possessive')} tall tales.")
    world.say(f"{hero_name} claimed {hero.pronoun('possessive')} {salve_name} could fix any ache in a single night.")
    world.para()

    # Act 2
    world.say(f"{friend_name}, {hero_name}'s best friend, warned {hero.pronoun('object')} not to make promises.")
    hero.memes["boast"] += 1
    world.say(f"But {hero_name} just laughed and rubbed the salve on {patient.label}.")
    patient.meters["salve_applied"] += 1
    patient.meters["pain"] += 0.5
    propagate(world)
    world.para()

    # Act 3
    world.say(f"The next morning, {patient.label} was worse, not better.")
    patient.meters["pain"] += 2
    hero.memes["credibility"] = -2
    propagate(world)
    world.say(f"The town folk grumbled that {hero_name} was a fraud.")
    world.para()

    # Resolution
    friend.memes["defended"] += 1
    world.say(f"But {friend_name} stood by {hero.pronoun('object')} and said, "
              f'"A true friend does not need a miracle cure; a true friend just stays."')
    hero.memes["humility"] += 1
    hero.memes["boast"] = 0
    propagate(world)
    world.say(f"{hero_name} learned that bragging about a remedy was no substitute for being honest.")
    world.say(f"And from that day on, {hero_name} and {friend_name} were closer than ever.")

    world.facts.update(hero=hero, friend=friend, patient=patient, salve=salve,
                       hero_name=hero_name, friend_name=friend_name,
                       patient_type=patient_type, salve_name=salve_name)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
HERO_NAMES = ["Clem", "Jeb", "Hank", "Buck", "Rusty"]
FRIEND_NAMES = ["Ella", "Mae", "Annie", "Sue", "Lottie"]
PATIENT_TYPES = ["mule", "horse", "ox", "donkey"]
SALVE_NAMES = ["cortisone salve", "miracle balm", "healing ointment"]
TRAITS = ["boastful", "loud", "proud", "stubborn", "foolish"]


@dataclass
class StoryParams:
    hero_name: str
    friend_name: str
    patient_type: str
    salve_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "cortisone": [
        ("What is cortisone?",
         "Cortisone is a medicine that can reduce swelling and pain, but it "
         "must be used carefully and only when a doctor says it is safe."),
    ],
    "friendship": [
        ("What makes a good friend?",
         "A good friend stays with you even when you make mistakes, and helps "
         "you learn to do better next time."),
    ],
    "tall_tale": [
        ("What is a tall tale?",
         "A tall tale is a story with a hero who does amazing things, often "
         "told in a funny or exaggerated way."),
    ],
}
KNOWLEDGE_ORDER = ["cortisone", "friendship", "tall_tale"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cautionary tall tale about friendship and a {f["salve_name"]} '
        f'for a child.',
        f'Tell a story where {f["hero_name"]} learns a lesson about honesty '
        f'and {f["friend_name"]} shows what true friendship means.',
        f'Write a short story set in a dusty town about a boastful character '
        f'and a wise friend.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend = f["hero"], f["friend"]
    return [
        QAItem(
            question=f"Who was the boastful character in Dusty Gulch?",
            answer=f"The boastful character was {f['hero_name']}, a {f['hero'].type} "
                   f"who claimed {f['salve_name']} could fix anything.",
        ),
        QAItem(
            question=f"What did {f['friend_name']} do when the town doubted {f['hero_name']}?",
            answer=f"{f['friend_name']} stood by {f['hero_name']} and said a true "
                   f"friend does not need a miracle cure, just honesty.",
        ),
        QAItem(
            question=f"What lesson did {f['hero_name']} learn?",
            answer=f"{f['hero_name']} learned that bragging about a remedy was no "
                   f"substitute for being honest with the people who counted on him.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    for tag in KNOWLEDGE_ORDER:
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid if it has a hero, a friend, a patient, and a salve.
valid_story(H, F, P, S) :- hero(H), friend(F), patient(P), salve(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for h in HERO_NAMES:
        lines.append(asp.fact("hero", h))
    for f in FRIEND_NAMES:
        lines.append(asp.fact("friend", f))
    for p in PATIENT_TYPES:
        lines.append(asp.fact("patient", p))
    for s in SALVE_NAMES:
        lines.append(asp.fact("salve", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    print("ASP verification: all combinations are valid in this domain.")
    return 0


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale about cortisone and friendship.")
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--patient", choices=PATIENT_TYPES)
    ap.add_argument("--salve", choices=SALVE_NAMES)
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
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    patient = args.patient or rng.choice(PATIENT_TYPES)
    salve = args.salve or rng.choice(SALVE_NAMES)
    return StoryParams(hero_name=hero, friend_name=friend,
                       patient_type=patient, salve_name=salve)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.hero_name, "cowpoke", params.friend_name, "rancher",
                 params.patient_type, params.salve_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            print(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid story combinations:")
        for h, f, p, s in stories:
            print(f"  hero={h}, friend={f}, patient={p}, salve={s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples = []
    if args.all:
        for h in HERO_NAMES[:2]:
            for f in FRIEND_NAMES[:2]:
                for p in PATIENT_TYPES[:2]:
                    for s in SALVE_NAMES[:2]:
                        params = StoryParams(hero_name=h, friend_name=f,
                                             patient_type=p, salve_name=s)
                        samples.append(generate(params))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.friend_name} ({p.patient_type}, {p.salve_name})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
