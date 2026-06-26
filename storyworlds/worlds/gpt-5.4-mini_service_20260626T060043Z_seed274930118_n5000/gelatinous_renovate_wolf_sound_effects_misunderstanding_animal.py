#!/usr/bin/env python3
"""
A standalone storyworld for an animal-story misunderstanding about sound effects
during a renovation, with a gelatinous surprise and a wolf-sized problem that
turns gentle in the end.

The seed tale idea:
- A small animal friend hears strange renovation sounds.
- A gelatinous thing and a wolf cause a misunderstanding.
- The noisy work is explained, the fear softens, and the story ends with a
  safer, friendlier result.

The world is built around:
- physical meters: noise, mess, calm, progress
- emotional memes: worry, suspicion, relief, trust

The prose should always be state-driven, with an actual turn from fear to
understanding rather than a frozen template.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother", "wolf"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False


@dataclass
class NoiseEvent:
    id: str
    sound: str
    cause: str
    meaning: str
    evidence: str


@dataclass
class Item:
    id: str
    label: str
    state: str
    region: str


@dataclass
class StoryParams:
    place: str
    noise: str
    cause: str
    misunderstanding: str
    hero: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.events = list(self.events)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "barn": Setting(place="the old barn", indoor=True),
    "house": Setting(place="the little house", indoor=True),
    "workshop": Setting(place="the workshop", indoor=True),
    "attic": Setting(place="the attic", indoor=True),
}

NOISES = {
    "hammering": NoiseEvent(
        id="hammering",
        sound="bang-bang-bang",
        cause="hammering nails",
        meaning="renovation work",
        evidence="boards were being fixed",
    ),
    "drilling": NoiseEvent(
        id="drilling",
        sound="vrrrrr",
        cause="drilling holes",
        meaning="repair work",
        evidence="a new shelf was going up",
    ),
    "scraping": NoiseEvent(
        id="scraping",
        sound="skrrrk",
        cause="scraping old paint",
        meaning="clean-up work",
        evidence="peeling paint was coming off",
    ),
}

CAUSES = {
    "gelatin": "a gelatinous puddle of craft paste",
    "bucket": "a bucket rolling across the floor",
    "wolf": "a wolf-shaped helper carrying boards",
}

MISUNDERSTANDINGS = {
    "monster": "a monster was hiding inside",
    "trouble": "someone was in trouble",
    "danger": "something dangerous was loose",
}

HEROES = [
    ("Mina", "girl"),
    ("Toby", "boy"),
    ("Pip", "mouse"),
    ("Nori", "fox"),
]

GUESTS = [
    ("wolf", "wolf"),
    ("helper", "dog"),
    ("builder", "badger"),
    ("painter", "rabbit"),
]

ITEMS = {
    "wall": Item(id="wall", label="wall", state="old", region="room"),
    "bench": Item(id="bench", label="bench", state="wobbly", region="room"),
    "floor": Item(id="floor", label="floor", state="dusty", region="room"),
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A noise can be misunderstood if the listener has a reason to worry.
misunderstood(H, N) :- hears(H, N), worries(H), noisy(N).

% Renovation work explains the noise.
explains(N) :- noise(N), renovation(N).

% A good ending happens when the misunderstanding is corrected.
resolved(H, N) :- misunderstood(H, N), explains(N), told_truth(H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for nid, n in NOISES.items():
        lines.append(asp.fact("noise", nid))
        lines.append(asp.fact("noisy", nid))
        lines.append(asp.fact("sound", nid, n.sound))
        lines.append(asp.fact("cause", nid, n.cause))
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    for cid in CAUSES:
        lines.append(asp.fact("possible_cause", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_patterns() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show resolved/2."))
    return sorted(set(asp.atoms(model, "resolved")))


def asp_verify() -> int:
    py = set(valid_patterns())
    cl = set(asp_valid_patterns())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} patterns).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print(" only python:", sorted(py - cl))
    print(" only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Python reasonableness gate
# ---------------------------------------------------------------------------

def valid_patterns() -> list[tuple[str, str]]:
    out = []
    for hero_id, _ in HEROES:
        for noise_id in NOISES:
            out.append((hero_id, noise_id))
    return out


def plausible_story(params: StoryParams) -> bool:
    return params.place in SETTINGS and params.noise in NOISES and params.hero in {h for h, _ in HEROES}


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero_name, hero_type = next((h, t) for h, t in HEROES if h == params.hero)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    helper_type = "wolf" if params.cause == "wolf" else "dog"
    helper_name = "Wolfie" if helper_type == "wolf" else "Patch"
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name))
    goo = world.add(Entity(id="goo", kind="thing", type="gelatinous", label="gelatinous paste"))
    world.add(Entity(id="item", kind="thing", type="thing", label="cover sheet"))

    # setup meters
    hero.memes.update(worry=0.0, suspicion=0.0, relief=0.0, trust=0.0)
    helper.memes.update(calm=0.0, trust=0.0)
    goo.meters.update(slide=0.0, mess=0.0)
    world.facts.update(hero=hero, helper=helper, goo=goo, noise=NOISES[params.noise], params=params)

    return world


def tell_story(world: World, params: StoryParams) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    goo: Entity = world.facts["goo"]  # type: ignore[assignment]
    noise: NoiseEvent = world.facts["noise"]  # type: ignore[assignment]

    world.say(f"{hero.label} was in {world.setting.place} when the air went {noise.sound}.")
    hero.memes["worry"] += 1
    hero.memes["suspicion"] += 1
    world.say(f"{hero.label} froze and thought {MISUNDERSTANDINGS[params.misunderstanding]}.")
    world.say(f"The sound came from {noise.cause}, and the boards were moving for {noise.meaning}.")
    if params.cause == "gelatin":
        goo.meters["slide"] += 1
        goo.meters["mess"] += 1
        world.say("Near the floor, a gelatinous blob wobbled across a cloth like a wiggly puddle.")
    elif params.cause == "wolf":
        helper.memes["trust"] += 1
        world.say(f"A wolf named {helper.label} was carrying planks very carefully.")
    else:
        world.say(f"A helper moved a bucket into place, which made the room echo.")

    world.say(f"{hero.label} backed up, because {hero.pronoun()} could not tell what the noise meant.")
    world.say(f"Then {helper.label} lifted a tool and said, 'No danger, just {noise.meaning}.'")
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1)
    hero.memes["suspicion"] = max(0.0, hero.memes["suspicion"] - 1)
    hero.memes["relief"] += 1
    hero.memes["trust"] += 1
    helper.memes["calm"] += 1
    world.say(f"{hero.label} listened again and heard the same {noise.sound}, but now it sounded busy instead of scary.")
    world.say(f"At last, {hero.label} smiled, and the work went on with a gentle thump and a happy tap.")


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        f'Write a short animal story for children about "{params.hero}" hearing "{NOISES[params.noise].sound}" and misunderstanding it.',
        f"Tell a gentle story where a {params.hero} thinks a {params.misunderstanding} is happening, but the sound is only renovation work.",
        f'Write a story with a gelatinous surprise, a wolf helper, and a child who learns the noise was not danger.',
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    noise: NoiseEvent = world.facts["noise"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What sound did {hero.label} hear in {world.setting.place}?",
            answer=f"{hero.label} heard {noise.sound}, which sounded loud and strange at first.",
        ),
        QAItem(
            question=f"Why did {hero.label} think something bad was happening?",
            answer=f"{hero.label} misunderstood the noise and thought {MISUNDERSTANDINGS[params.misunderstanding]}.",
        ),
        QAItem(
            question=f"What was the noise really from?",
            answer=f"It was really from {noise.cause}, which was part of {noise.meaning}.",
        ),
        QAItem(
            question=f"Who explained the noise to {hero.label}?",
            answer=f"{helper.label} explained that the sound came from {noise.meaning}.",
        ),
        QAItem(
            question=f"How did {hero.label} feel at the end?",
            answer=f"{hero.label} felt relieved and trusted the helper after hearing the explanation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is renovation?",
            answer="Renovation is work done to fix, change, or improve a place, like repairing walls or floors.",
        ),
        QAItem(
            question="Why can hammering sound so loud?",
            answer="Hammering can sound loud because each hit makes a sharp noise that bounces through a room.",
        ),
        QAItem(
            question="What does gelatinous mean?",
            answer="Gelatinous means soft, wobbly, and jelly-like.",
        ),
        QAItem(
            question="Why do animals sometimes misunderstand sounds?",
            answer="Animals can misunderstand sounds when they cannot see the source and imagine a scarier cause than the real one.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts.keys()}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld: sound effects, misunderstanding, and a gentle reveal.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--noise", choices=sorted(NOISES))
    ap.add_argument("--cause", choices=sorted(CAUSES))
    ap.add_argument("--misunderstanding", choices=sorted(MISUNDERSTANDINGS))
    ap.add_argument("--hero", choices=[h for h, _ in HEROES])
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
    place = args.place or rng.choice(list(SETTINGS))
    noise = args.noise or rng.choice(list(NOISES))
    cause = args.cause or rng.choice(list(CAUSES))
    misunderstanding = args.misunderstanding or rng.choice(list(MISUNDERSTANDINGS))
    hero = args.hero or rng.choice([h for h, _ in HEROES])

    params = StoryParams(place=place, noise=noise, cause=cause, misunderstanding=misunderstanding, hero=hero)
    if not plausible_story(params):
        raise StoryError("The requested options do not form a plausible story.")
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
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
    StoryParams(place="barn", noise="hammering", cause="gelatin", misunderstanding="monster", hero="Mina"),
    StoryParams(place="house", noise="drilling", cause="wolf", misunderstanding="danger", hero="Toby"),
    StoryParams(place="workshop", noise="scraping", cause="bucket", misunderstanding="trouble", hero="Pip"),
]


def asp_show_program() -> str:
    return asp_program("#show resolved/2.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_show_program())
        pairs = sorted(set(asp.atoms(model, "resolved")))
        for p in pairs:
            print(p)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(args.n, 1)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### sample {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
