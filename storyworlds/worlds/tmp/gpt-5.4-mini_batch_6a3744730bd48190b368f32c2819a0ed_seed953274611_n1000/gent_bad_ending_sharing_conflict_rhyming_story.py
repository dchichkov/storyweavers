#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gent_bad_ending_sharing_conflict_rhyming_story.py
==================================================================================

A small storyworld built from the seed words and features:

- word: gent
- features: sharing, conflict, bad ending
- style: rhyming story

This world simulates a tiny child-facing scene about a kind gent, a shared treat,
a growing conflict, and a sad ending image that proves what changed.
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
MOOD_BIG = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"hunger": 0.0, "broken": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"joy": 0.0, "want": 0.0, "hurt": 0.0, "grumble": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "gent"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Scene:
    place: str
    rhyme1: str
    rhyme2: str
    shared_food: str
    share_phrase: str
    conflict_phrase: str
    ending_phrase: str
    bad_end_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ConflictBeat:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    scene: str
    beat: str
    name1: str
    gender1: str
    name2: str
    gender2: str
    gent_name: str
    gent_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
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
        import copy as _copy
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SCENES = {
    "kitchen": Scene(
        place="kitchen",
        rhyme1="The kitchen glowed with morning light,",
        rhyme2="And three small hearts felt peppy and bright.",
        shared_food="a plate of berry buns",
        share_phrase="shared the berry buns in a sunny row",
        conflict_phrase="but one wanted more than a fair little share",
        ending_phrase="The buns were gone, and the room felt bare.",
        bad_end_image="Only crumbs and a lonely plate sat on the sill.",
        tags={"gent", "share", "conflict", "ending"},
    ),
    "porch": Scene(
        place="porch",
        rhyme1="The porch was warm beneath the sun,",
        rhyme2="And sharing there seemed like happy fun.",
        shared_food="a paper cup of plum juice",
        share_phrase="shared the plum juice with a sip-sip cheer",
        conflict_phrase="but one child snatched and started to sneer",
        ending_phrase="The cup tipped over with a splashy tear.",
        bad_end_image="A wet stain shone where the juice ran still.",
        tags={"gent", "share", "conflict", "ending"},
    ),
    "yard": Scene(
        place="yard",
        rhyme1="The yard was wide with clover sweet,",
        rhyme2="And tiny shoes pat-patted on the street.",
        shared_food="three honey cakes",
        share_phrase="shared the honey cakes with a careful grin",
        conflict_phrase="but the greedy tug made trouble begin",
        ending_phrase="The broken plate made the whole game dim.",
        bad_end_image="A cracked plate and a fallen cake lay in the grass.",
        tags={"gent", "share", "conflict", "ending"},
    ),
}

BEATS = {
    "snatch": ConflictBeat(
        id="snatch",
        sense=3,
        power=1,
        text="snatched the sweet and made a sour-faced scene",
        fail="snatched at the treat, but it slipped clean away",
        tags={"conflict", "bad"},
    ),
    "tug": ConflictBeat(
        id="tug",
        sense=3,
        power=1,
        text="tugged on the dish and began to say, 'Mine!'",
        fail="tugged on the dish, but the dish would not stay",
        tags={"conflict", "bad"},
    ),
    "argue": ConflictBeat(
        id="argue",
        sense=2,
        power=2,
        text="argued and argued with a noisy frown",
        fail="argued and argued, then dropped the food down",
        tags={"conflict", "bad"},
    ),
}

GENTS = {
    "gent": {"label": "the gent", "type": "gent"},
    "uncle": {"label": "Uncle Gent", "type": "gent"},
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Leo", "Max", "Finn"]


def valid_combos() -> list[tuple[str, str]]:
    return [(scene_id, beat_id) for scene_id in SCENES for beat_id in BEATS]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for bid, b in BEATS.items():
        lines.append(asp.fact("beat", bid))
        lines.append(asp.fact("sense", bid, b.sense))
        lines.append(asp.fact("power", bid, b.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,B) :- scene(S), beat(B).
safe(B) :- beat(B), sense(B, N), sense_min(M), N >= M.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    if a - b:
        print(" only in ASP:", sorted(a - b))
    if b - a:
        print(" only in Python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld with gent, sharing, conflict, and a bad ending.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--beat", choices=BEATS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              if (args.scene is None or c[0] == args.scene)
              and (args.beat is None or c[1] == args.beat)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, beat = rng.choice(sorted(combos))
    n1 = rng.choice(GIRL_NAMES + BOY_NAMES)
    n2 = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != n1])
    g1 = "girl" if n1 in GIRL_NAMES else "boy"
    g2 = "girl" if n2 in GIRL_NAMES else "boy"
    return StoryParams(scene=scene, beat=beat, name1=n1, gender1=g1, name2=n2, gender2=g2,
                       gent_name="Gent", gent_gender="gent")


def tell(scene: Scene, beat: ConflictBeat, a: Entity, b: Entity, gent: Entity) -> World:
    world = World()
    world.add(a)
    world.add(b)
    world.add(gent)
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    gent.memes["joy"] += 1

    world.say(f"{scene.rhyme1} {scene.rhyme2}")
    world.say(f"{a.id} and {b.id} had {scene.shared_food}, and the kind gent came by with a grin.")
    world.say(f'The gent said, "Let\'s {scene.share_phrase}," and the day felt thin.')

    world.para()
    a.memes["want"] += 1
    b.memes["want"] += 1
    a.memes["grumble"] += 1
    world.say(f"But {a.id} wanted more, and {b.id} felt sore, for {beat.text}.")
    world.say(f'The gent tried to smooth it over, but the little spat still met.')

    world.para()
    if beat.power >= 2:
        a.meters["broken"] += 1
        b.meters["broken"] += 1
    gent.memes["hurt"] += 1
    world.say(f"{scene.ending_phrase}")
    world.say(f"In the end, no one laughed; {scene.bad_end_image}")
    world.say(f"The kind gent stood quiet and small, and the sharing game went wrong.")

    world.facts.update(scene=scene, beat=beat, a=a, b=b, gent=gent)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene: Scene = f["scene"]
    beat: ConflictBeat = f["beat"]
    return [
        f'Write a rhyming story for a young child that uses the word "gent" and ends sadly.',
        f'Tell a rhyming story about sharing in the {scene.place}, where a gent tries to help but a conflict grows.',
        f'Write a short rhyming tale where {beat.text} and the ending is a bad one.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    scene: Scene = f["scene"]
    beat: ConflictBeat = f["beat"]
    a: Entity = f["a"]
    b: Entity = f["b"]
    gent: Entity = f["gent"]
    return [
        ("Who was in the story?",
         f"It was about {a.id}, {b.id}, and {gent.id}, who all shared the same little scene."),
        ("What were they trying to do?",
         f"They were trying to share food together, but a conflict grew when one child wanted more."),
        ("What went wrong?",
         f"{beat.text.capitalize()}. That made the sharing turn into a sad argument instead of a kind moment."),
        ("How did the story end?",
         f"It ended badly. {scene.bad_end_image} The gent could not fix it in time."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a gent?",
         "A gent is a kind, polite man. In stories, a gent often tries to help calmly."),
        ("What does sharing mean?",
         "Sharing means letting someone else use or have part of something. It is a kind way to play together."),
        ("What is a conflict?",
         "A conflict is a fight or disagreement. It happens when people want different things and cannot agree."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)} role={e.role} type={e.type}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.beat not in BEATS or params.gent_name.lower() != "gent":
        raise StoryError("Invalid story parameters.")
    scene = SCENES[params.scene]
    beat = BEATS[params.beat]
    w = tell(
        scene=scene,
        beat=beat,
        a=Entity(id=params.name1, kind="character", type=params.gender1, role="child"),
        b=Entity(id=params.name2, kind="character", type=params.gender2, role="child"),
        gent=Entity(id=params.gent_name, kind="character", type=params.gent_gender, role="gent"),
    )
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(w)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(w)],
        world=w,
    )


CURATED = [
    StoryParams(scene="kitchen", beat="snatch", name1="Mia", gender1="girl", name2="Tom", gender2="boy", gent_name="Gent", gent_gender="gent"),
    StoryParams(scene="porch", beat="tug", name1="Lily", gender1="girl", name2="Ben", gender2="boy", gent_name="Gent", gent_gender="gent"),
    StoryParams(scene="yard", beat="argue", name1="Nora", gender1="girl", name2="Finn", gender2="boy", gent_name="Gent", gent_gender="gent"),
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
        print(asp_program("#show valid/2.\n#show safe/1."))
        return
    if args.verify:
        rc = asp_verify()
        try:
            sample = generate(CURATED[0])
            _ = sample.story
        except Exception as exc:
            print(f"SMOKE TEST FAILED: {exc}")
            rc = 1
        sys.exit(rc)
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for scene, beat in combos:
            print(f"  {scene:8} {beat}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
