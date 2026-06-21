#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/satchel_thought_tease_bad_ending_ghost_story.py
================================================================================

A small storyworld in a ghost-story mood: a child hears a strange thought,
gets teased about a satchel, and the bad ending proves why spooky play can go
wrong. The world is intentionally tiny and constraint-checked: only reasonable
ghost-story setups are allowed, the prose is driven by simulated state, and the
ending changes depending on whether the child listens, hides, or follows the
tease.

The core seed words are:
- satchel
- thought
- tease

The style target is:
- Ghost Story

The feature target is:
- Bad Ending

This script is standalone and uses only the stdlib plus the shared
storyworlds/results.py containers. The ASP twin is inline and imported lazily.
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
SENSE_MIN = 2

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    dark: bool = False
    chill: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    kind: str
    scary: bool = False
    can_hide: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Choice:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    place: str
    object: str
    choice: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
    seed: Optional[int] = None


PLACES = {
    "attic": Place(id="attic", label="the attic", dark=True, chill=True, tags={"dark", "ghost"}),
    "hall": Place(id="hall", label="the old hall", dark=True, chill=False, tags={"dark", "ghost"}),
    "yard": Place(id="yard", label="the back yard", dark=False, chill=True, tags={"ghost"}),
}

OBJECTS = {
    "satchel": ObjectCfg(id="satchel", label="satchel", phrase="a leather satchel", kind="bag", can_hide=True, tags={"satchel"}),
    "lantern": ObjectCfg(id="lantern", label="lantern", phrase="an old lantern", kind="light", scary=True, tags={"light"}),
    "mirror": ObjectCfg(id="mirror", label="mirror", phrase="a cracked mirror", kind="thing", scary=True, tags={"ghost"}),
}

CHOICES = {
    "hide": Choice(id="hide", sense=3, power=3, text="slipped the satchel under the floorboard and told the child to stay quiet", fail="could not hide the satchel before the whisper grew louder", tags={"hide"}),
    "tease_back": Choice(id="tease_back", sense=2, power=2, text="tried to laugh the tease away, but the room answered with a colder draft", fail="only made the room feel meaner", tags={"tease"}),
    "run": Choice(id="run", sense=3, power=1, text="ran for the door and left the satchel behind", fail="ran too late to help", tags={"run"}),
    "ignore": Choice(id="ignore", sense=1, power=0, text="pretended the whisper did not matter", fail="pretended it was nothing", tags={"ignore"}),
}

CHILD_NAMES = ["Mia", "Lena", "Noah", "Eli", "Ava", "Ivy"]
ADULT_NAMES = ["Mom", "Dad", "Aunt Nora", "Uncle Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for obj in OBJECTS:
            for choice in CHOICES:
                if place == "yard" and obj == "mirror":
                    continue
                if choice == "hide" and not OBJECTS[obj].can_hide:
                    continue
                if choice == "ignore" and not PLACES[place].dark:
                    continue
                if obj == "satchel":
                    out.append((place, obj, choice))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with a satchel, a thought, and a tease.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult-name")
    ap.add_argument("--adult-gender", choices=["woman", "man"])
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


def reasonableness_gate(place: Place, obj: ObjectCfg, choice: Choice) -> bool:
    return obj.id == "satchel" and place.dark


def explain_rejection(place: Place, obj: ObjectCfg, choice: Choice) -> str:
    return f"(No story: this ghost-story seed wants a satchel in a dark place, not {obj.label} in {place.label}.)"


def sensible_choices() -> list[Choice]:
    return [c for c in CHOICES.values() if c.sense >= SENSE_MIN]


def choice_effect(choice: Choice, threat: int) -> bool:
    return choice.power >= threat


def hazard_level(place: Place, obj: ObjectCfg) -> int:
    return 2 + (1 if place.chill else 0) + (1 if obj.scary else 0)


def predict_ending(world: World, choice: Choice) -> dict:
    sim = world.copy()
    return {"survives": choice.power >= sim.facts["threat"], "teased": True}


def tell(world: World, place: Place, obj: ObjectCfg, choice: Choice,
         child: Entity, adult: Entity) -> None:
    threat = hazard_level(place, obj)
    world.facts["threat"] = threat
    world.facts["choice"] = choice
    world.facts["place"] = place
    world.facts["object"] = obj
    world.facts["child"] = child
    world.facts["adult"] = adult

    child.memes["unease"] += 1
    child.memes["curiosity"] += 1
    world.say(f"That evening, {child.id} wandered into {place.label} with {obj.phrase} swinging at {child.pronoun('possessive')} side.")
    world.say(f"{child.id} thought the house was listening. Then a thin, mean tease slipped through the dark, like a whisper with teeth.")
    world.para()
    if choice.id == "ignore":
        child.memes["fear"] += 1
        world.say(f"{child.id} heard the tease and pretended not to care, but {child.pronoun('possessive')} heart beat faster and faster.")
        world.say(f"The satchel bumped the wall, and the sound came back twice, as if something unseen had answered.")
        world.say("By the time {adult} called from downstairs, the whole hall felt cold enough to keep the night forever.".format(adult=adult.label_word))
        world.say(f"{child.id} never found out what was inside the satchel, because {child.pronoun('subject')} left it where the shadows could keep it.")
        world.facts["ending"] = "lost"
        return
    child.memes["defiance"] += 1
    if choice.id == "tease_back":
        world.say(f"{child.id} teased the darkness right back, trying to sound brave.")
    elif choice.id == "hide":
        world.say(f"{child.id} thought the satchel should be hidden, so {child.pronoun('subject')} crouched to tuck it away.")
    else:
        world.say(f"{child.id} ran for the door, but the tease stayed behind in the dark hall.")
    world.say(f"Then {adult.id} stepped in, seeing the worry on {child.id}'s face.")
    if choice_effect(choice, threat):
        adult.memes["calm"] += 1
        world.say(f"{adult.id} took the satchel, opened it under the lamp, and found only old paper, a ribbon, and a note that read: 'I thought you would come back.'")
        world.say(f"The room should have felt safer, but the whisper did not leave. It slid out with the draft and rustled the curtains anyway.")
        world.say(f"{child.id} and {adult.id} listened to the house sigh, and the tease came again from somewhere above the stairs.")
        world.say("Nobody slept well after that. In the morning, the satchel was gone, and the floorboard stayed warm as if a hand had been resting there all night.")
        world.facts["ending"] = "bad"
    else:
        world.say(f"{adult.id} reached for the satchel, but the whisper grew colder and the lamp dimmed.")
        world.say(f"{child.id} cried out, and the tease answered from the ceiling.")
        world.say("By dawn, the hallway was empty, except for the satchel and a footprint that did not belong to anyone who was still alive.")
        world.facts["ending"] = "worse"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a ghost story for a young child that includes the words satchel, thought, and tease.",
        f"Tell a spooky story set in {f['place'].label} where a child carries a satchel, has a strange thought, and gets teased by something in the dark.",
        "Make the ending bad: the child should not get a happy rescue, only a creepy final image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    adult = world.facts["adult"]
    choice = world.facts["choice"]
    ending = world.facts["ending"]
    place = world.facts["place"]
    return [
        QAItem(
            question="What strange thing happened in the story?",
            answer=f"A teasing whisper came out of the dark and made {child.id} feel like the {place.label} was awake. The sound followed the satchel, so the night never felt normal again.",
        ),
        QAItem(
            question="What did the child think about?",
            answer=f"{child.id} thought the satchel might be important, but also a little scary. That thought made {child.pronoun('subject')} act differently, because {child.pronoun('subject')} kept listening for the tease instead of relaxing.",
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended badly, with {child.id} still unsettled and the house feeling colder than before. "
                f"The satchel was left behind, and the final image showed that the tease had not been made safe."
            ),
        ),
        QAItem(
            question="What did {adult} do?".format(adult=adult.id),
            answer=(
                f"{adult.id} came in, but the help was too late to turn the night into a happy one. "
                f"The child was already shaken, so the ending stayed eerie instead of warm."
            ),
        ),
        QAItem(
            question="Did the choice matter?",
            answer=f"Yes. The chosen action was {choice.id}, and it led to the ending becoming {ending}. The world state changed the mood, but it could not fix the damage in time.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "satchel": [(
        "What is a satchel?",
        "A satchel is a bag with a strap. People can carry small things in it, like notes, pencils, or treasures.",
    )],
    "thought": [(
        "What is a thought?",
        "A thought is something your mind makes when you wonder, remember, or imagine. Thoughts can be calm, curious, or worried.",
    )],
    "tease": [(
        "What does tease mean?",
        "To tease means to joke at someone in a way that can make them feel embarrassed or upset. Gentle teasing should stop if it stops being fun.",
    )],
    "ghost": [(
        "What is a ghost story?",
        "A ghost story is a spooky tale about mysterious sounds, shadows, and the feeling that something unseen is nearby.",
    )],
}
WORLD_ORDER = ["satchel", "thought", "tease", "ghost"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["object"].tags) | {"ghost", "thought", "tease"}
    out: list[QAItem] = []
    for key in WORLD_ORDER:
        if key in tags:
            for q, a in WORLD_KNOWLEDGE[key]:
                out.append(QAItem(question=q, answer=a))
    return out


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,O,C) :- place(P), object(O), choice(C), dark(P), satchel(O).
bad_end(C) :- choice(C), sense(C,S), sense_min(M), S < M.
bad_end(C) :- choice(C), power(C,P), threat(T), P < T.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dark:
            lines.append(asp.fact("dark", pid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
        if oid == "satchel":
            lines.append(asp.fact("satchel", oid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("sense", cid, c.sense))
        lines.append(asp.fact("power", cid, c.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("threat", 3))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    # smoke test normal generation
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generation smoke test failed: {e}")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.object and args.object != "satchel":
        raise StoryError(explain_rejection(PLACES[args.place] if args.place else PLACES["attic"], OBJECTS[args.object], CHOICES[args.choice] if args.choice else CHOICES["hide"]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.object is None or c[1] == args.object)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj, choice = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        object=obj,
        choice=choice,
        child_name=args.child_name or rng.choice(CHILD_NAMES),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        adult_name=args.adult_name or rng.choice(ADULT_NAMES),
        adult_gender=args.adult_gender or rng.choice(["woman", "man"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.object not in OBJECTS or params.choice not in CHOICES:
        raise StoryError("invalid params")
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    adult = world.add(Entity(id=params.adult_name, kind="character", type=params.adult_gender, role="adult"))
    tell(world, PLACES[params.place], OBJECTS[params.object], CHOICES[params.choice], child, adult)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    StoryParams(place="attic", object="satchel", choice="hide", child_name="Mia", child_gender="girl", adult_name="Mom", adult_gender="woman"),
    StoryParams(place="hall", object="satchel", choice="tease_back", child_name="Noah", child_gender="boy", adult_name="Dad", adult_gender="man"),
    StoryParams(place="attic", object="satchel", choice="ignore", child_name="Ava", child_gender="girl", adult_name="Aunt Nora", adult_gender="woman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show bad_end/1."))
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
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
