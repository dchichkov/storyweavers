#!/usr/bin/env python3
"""
storyworlds/worlds/arena_rhyme_misunderstanding_myth.py
=======================================================

A small myth-style storyworld about an arena, a rhyme, and a misunderstanding.

Premise:
- A child hero enters an arena to sing a rhyme that is meant to awaken help.
- A misunderstanding makes the song sound like a challenge instead of a plea.
- The hero must clarify the meaning, and the arena's mood changes from tense to bright.

The simulation tracks:
- physical meters: distance, echo, dust, attention, and calm
- emotional memes: hope, pride, confusion, fear, trust, and relief

The story engine is intentionally small and constraint-checked:
- a rhyme can only be sung where echo is strong enough
- a misunderstanding can only arise when a witness hears the rhyme without context
- resolution requires a clarifying line and a returned sign of trust
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
    hears: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Arena:
    name: str = "the arena"
    place: str = "the arena"
    echo: float = 1.0
    crowd: str = "watchful"
    dust: float = 0.0
    calm: float = 0.0
    facts: dict = field(default_factory=dict)


class World:
    def __init__(self, arena: Arena) -> None:
        self.arena = arena
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        clone = World(copy.deepcopy(self.arena))
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    witness_name: str
    witness_type: str
    rhyme_name: str
    seed: Optional[int] = None


HERO_NAMES = ["Lina", "Maro", "Tavi", "Nera", "Ivo", "Sela"]
WITNESS_NAMES = ["Bren", "Kora", "Mika", "Oren", "Pela", "Suri"]
TYPES = ["girl", "boy"]
RHYMES = {
    "stone_key": {
        "title": "the stone-key rhyme",
        "line": "Stone to open, stone to hear, bright gate listen, draw us near",
        "chant": "the stone-key rhyme",
        "meaning": "a call for a hidden gate to open, not a boast",
    },
    "river_fold": {
        "title": "the river-fold rhyme",
        "line": "River bend and river sing, bring the lost a shining ring",
        "chant": "the river-fold rhyme",
        "meaning": "a request to return something lost, not a threat",
    },
    "owl_bridge": {
        "title": "the owl-bridge rhyme",
        "line": "Owl above and bridge below, guide the gentle feet that go",
        "chant": "the owl-bridge rhyme",
        "meaning": "a plea for safe passage, not a challenge",
    },
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A myth-like storyworld about an arena, rhyme, and misunderstanding.")
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--witness-name", choices=WITNESS_NAMES)
    ap.add_argument("--witness-type", choices=TYPES)
    ap.add_argument("--rhyme-name", choices=RHYMES)
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
    rhyme_name = args.rhyme_name or rng.choice(sorted(RHYMES))
    hero_type = args.hero_type or rng.choice(TYPES)
    witness_type = args.witness_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    witness_name = args.witness_name or rng.choice([n for n in WITNESS_NAMES if n != hero_name])
    if hero_name == witness_name:
        raise StoryError("The hero and witness must be different people.")
    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        witness_name=witness_name,
        witness_type=witness_type,
        rhyme_name=rhyme_name,
    )


def _base_world(params: StoryParams) -> World:
    arena = Arena()
    world = World(arena)
    hero = world.add(Entity(
        id=params.hero_name, kind="character", type=params.hero_type,
        label=f"young {params.hero_type}",
        meters={"distance": 0.0, "attention": 0.0},
        memes={"hope": 1.0, "pride": 0.0, "trust": 0.0, "relief": 0.0},
    ))
    witness = world.add(Entity(
        id=params.witness_name, kind="character", type=params.witness_type,
        label=f"watcher {params.witness_type}",
        hears=True,
        meters={"distance": 0.0, "attention": 0.0},
        memes={"confusion": 0.0, "fear": 0.0, "trust": 0.0},
    ))
    rhyme = RHYMES[params.rhyme_name]
    world.arena.facts.update(hero=hero, witness=witness, rhyme=rhyme, params=params)
    return world


def _introduce(world: World) -> None:
    f = world.arena.facts
    hero: Entity = f["hero"]
    witness: Entity = f["witness"]
    rhyme = f["rhyme"]
    world.say(
        f"In the old arena, {hero.id} came under the open sky with a small heart full of hope. "
        f"{hero.pronoun().capitalize()} had learned {rhyme['chant']} and believed the words could wake a blessing."
    )
    world.say(
        f"Near the stone steps stood {witness.id}, listening for any sound that might mean danger."
    )


def _sing_rhyme(world: World) -> None:
    f = world.arena.facts
    hero: Entity = f["hero"]
    rhyme = f["rhyme"]
    if world.arena.echo < THRESHOLD:
        raise StoryError("This arena is too quiet for the rhyme to carry.")
    hero.meters["attention"] += 1
    hero.memes["pride"] += 1
    world.arena.dust += 0.5
    world.say(
        f"{hero.id} stepped into the middle ring and sang: \"{rhyme['line']}\""
    )
    world.say(
        f"The words bounced from wall to wall, and the arena answered with a long bright echo."
    )


def _misunderstanding(world: World) -> None:
    f = world.arena.facts
    hero: Entity = f["hero"]
    witness: Entity = f["witness"]
    rhyme = f["rhyme"]
    sig = ("misunderstanding", hero.id, witness.id, rhyme["title"])
    if sig in world.fired:
        return
    world.fired.add(sig)
    witness.memes["confusion"] += 1
    witness.memes["fear"] += 1
    witness.meters["attention"] += 1
    world.say(
        f"{witness.id} heard only the loudest part of the song and thought it was a challenge."
    )
    world.say(
        f"That was the misunderstanding: the rhyme sounded fierce when it was meant to be kind."
    )


def _clarify(world: World) -> None:
    f = world.arena.facts
    hero: Entity = f["hero"]
    witness: Entity = f["witness"]
    rhyme = f["rhyme"]
    sig = ("clarify", hero.id, witness.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    witness.memes["confusion"] = 0.0
    witness.memes["fear"] = 0.0
    witness.memes["trust"] += 1
    hero.memes["trust"] += 1
    world.arena.calm += 1.0
    world.say(
        f"{hero.id} raised a hand and said, \"I was not calling for a fight. I was asking for help.\""
    )
    world.say(
        f"Then {hero.id} spoke the meaning plainly: {rhyme['meaning']}."
    )


def _resolution(world: World) -> None:
    f = world.arena.facts
    hero: Entity = f["hero"]
    witness: Entity = f["witness"]
    rhyme = f["rhyme"]
    hero.memes["relief"] += 1
    witness.memes["trust"] += 1
    world.arena.calm += 1.0
    world.say(
        f"{witness.id} lowered {witness.pronoun('possessive')} shoulders and nodded."
    )
    world.say(
        f"Together they finished the rhyme as a prayer for the arena, and the dusty floor seemed softer for it."
    )
    world.say(
        f"By the end, the misunderstanding had gone quiet, and {hero.id}'s song stood clear as sunrise."
    )


def generate_world(params: StoryParams) -> World:
    world = _base_world(params)
    _introduce(world)
    world.para()
    _sing_rhyme(world)
    _misunderstanding(world)
    world.para()
    _clarify(world)
    _resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.arena.facts
    hero: Entity = f["hero"]
    rhyme = f["rhyme"]
    return [
        f"Write a myth-like story about an arena where {hero.id} sings {rhyme['chant']} and is misunderstood.",
        f"Tell a short legend in which a child speaks a rhyme in the arena, and another listener mistakes it for a challenge.",
        f"Write a gentle myth with an arena, a bright echo, and a misunderstanding that turns into trust.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.arena.facts
    hero: Entity = f["hero"]
    witness: Entity = f["witness"]
    rhyme = f["rhyme"]
    return [
        QAItem(
            question=f"Who sang in the arena?",
            answer=f"{hero.id} sang in the arena, and {hero.pronoun().capitalize()} meant the song as a careful plea.",
        ),
        QAItem(
            question=f"What did the witness misunderstand?",
            answer=f"{witness.id} misunderstood {hero.id}'s rhyme and thought it sounded like a challenge instead of a request for help.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the misunderstanding cleared away, trust returned, and the arena feeling calm again.",
        ),
        QAItem(
            question=f"What was special about {rhyme['title']}?",
            answer=f"It was a rhyme meant to ask for help and safe passage, not to start a fight.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an arena?",
            answer="An arena is a large open place where people gather to watch, speak, sing, or compete.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a small pattern of words that sound alike, which can make a song or chant easier to remember.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone hears or thinks something the wrong way, so they do not catch the true meaning.",
        ),
        QAItem(
            question="Why can echoes change how words sound?",
            answer="Echoes bounce sound back through a space, so words can seem louder, longer, or more dramatic than they first were.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"arena={world.arena.name} echo={world.arena.echo} dust={world.arena.dust} calm={world.arena.calm}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "arena"),
        asp.fact("feature", "echo"),
        asp.fact("feature", "misunderstanding"),
        asp.fact("feature", "rhyme"),
    ]
    for name in RHYMES:
        lines.append(asp.fact("rhyme", name))
    return "\n".join(lines)


ASP_RULES = r"""
feature_present(arena, echo).
feature_present(arena, rhyme).
feature_present(arena, misunderstanding).

compatible_story(Arena) :- feature_present(Arena, echo), feature_present(Arena, rhyme), feature_present(Arena, misunderstanding).
#show compatible_story/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/1."))
    found = set(asp.atoms(model, "compatible_story"))
    expected = {("arena",)}
    if found == expected:
        print("OK: ASP and Python agree about the arena storyworld.")
        return 0
    print("MISMATCH:", sorted(found), sorted(expected))
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
    StoryParams(hero_name="Lina", hero_type="girl", witness_name="Bren", witness_type="boy", rhyme_name="stone_key"),
    StoryParams(hero_name="Maro", hero_type="boy", witness_name="Kora", witness_type="girl", rhyme_name="river_fold"),
    StoryParams(hero_name="Tavi", hero_type="girl", witness_name="Oren", witness_type="boy", rhyme_name="owl_bridge"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        hero_type=args.hero_type or rng.choice(TYPES),
        witness_name=args.witness_name or rng.choice(WITNESS_NAMES),
        witness_type=args.witness_type or rng.choice(TYPES),
        rhyme_name=args.rhyme_name or rng.choice(sorted(RHYMES)),
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible_story/1."))
        print(sorted(set(asp.atoms(model, "compatible_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.rhyme_name} in the arena"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
