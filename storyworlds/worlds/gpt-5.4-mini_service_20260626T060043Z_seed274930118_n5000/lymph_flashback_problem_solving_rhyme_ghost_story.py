#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/lymph_flashback_problem_solving_rhyme_ghost_story.py
===============================================================================================================

A standalone story world for a small ghost-story domain with:
- lymph as the seed word and spooky substance
- flashback as a narrative turn
- problem solving as the core action
- rhyme as a child-friendly repeated instrument

The world is built to produce short, complete stories about a haunted place,
a missing glow, and a careful, gentle solution.

Premise:
A shy child meets a moon-touched ghost in an old house. The ghost's lantern
has gone dim because its glow-stuff, called lymph, leaked away. A flashback
shows where the lymph used to be kept and why it mattered. The child then
solves the problem by finding the right container, sealing the leak, and
restoring the lantern.

The story style is close to a ghost story, but it stays soft, concrete, and
child-facing. It uses meter-like physical state for glow, dampness, and
distance, and meme-like emotional state for fear, hope, and relief.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "boy", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"ghost"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    ghost_name: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    shadowy: bool = True


@dataclass
class Problem:
    id: str
    missing: str
    leak: str
    fix: str
    rhyme: str
    clue: str
    flashback_line: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        other = World(self.setting)
        other.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "phrase": v.phrase,
            "owner": v.owner, "carried_by": v.carried_by, "location": v.location, "plural": v.plural,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


SETTINGS = {
    "old_house": Setting(place="the old house", shadowy=True),
    "graveyard_gate": Setting(place="the gate by the graveyard", shadowy=True),
    "attic": Setting(place="the attic", shadowy=True),
}

PROBLEMS = {
    "dim_lantern": Problem(
        id="dim_lantern",
        missing="the ghost's lantern glow",
        leak="the glow had leaked out through a crack",
        fix="seal the crack with a silver jar and fresh ribbon",
        rhyme="When the lantern sighs and light turns thin, / a careful hand can guide it in.",
        clue="a silver drip on the floorboard",
        flashback_line="Long ago, the ghost had stored the shining lymph in a jar beside the window.",
    ),
    "lost_song": Problem(
        id="lost_song",
        missing="the ghost's song",
        leak="the tune had slipped away into the rafters",
        fix="find the old music box and wind it gently",
        rhyme="When the night is hush and the rafters hum, / the right little tune can lead it home.",
        clue="a tiny key hanging from a nail",
        flashback_line="The ghost remembered singing that tune when the house was warm and bright.",
    ),
    "cold_window": Problem(
        id="cold_window",
        missing="the ghost's warm glow",
        leak="the window had been left open and the moon wind had stolen the warmth",
        fix="shut the window and tuck in the curtain",
        rhyme="If the wind slips in and the candles sway, / close the gap and chase it away.",
        clue="a curtain fluttering like a white flag",
        flashback_line="In the flashback, the ghost had promised to keep the room snug for winter.",
    ),
}

HERO_NAMES = ["Mina", "Jasper", "Nell", "Theo", "Iris", "Lena"]
GHOST_NAMES = ["Murmur", "Pale Will", "Noah of the Stairs", "Bell", "Wisp", "Juniper"]
TYPES = ["girl", "boy", "child"]


def build_problem(place: str) -> Problem:
    if place == "attic":
        return PROBLEMS["dim_lantern"]
    if place == "old_house":
        return PROBLEMS["lost_song"]
    return PROBLEMS["cold_window"]


def introduce(world: World, hero: Entity, ghost: Entity) -> None:
    world.say(
        f"One quiet night, {hero.id} went to {world.setting.place} and heard a soft, "
        f"shivery hello from {ghost.id}."
    )
    world.say(
        f"{ghost.id} was a pale little ghost who floated near the dark corners, "
        f"but {ghost.pronoun('possessive')} eyes were kind."
    )


def establish_problem(world: World, hero: Entity, ghost: Entity, prob: Problem) -> None:
    ghost.meters["glow"] = 1
    ghost.memes["worry"] = 1
    world.say(
        f"{ghost.id} whispered that {prob.missing} was gone because {prob.leak}."
    )
    world.say(f"{hero.id} saw {prob.clue} and felt a brave idea begin to sparkle.")


def flashback(world: World, ghost: Entity, prob: Problem) -> None:
    ghost.memes["nostalgia"] = 1
    world.say(
        f"In a flashback, {ghost.id} remembered when {prob.flashback_line}"
    )


def solve(world: World, hero: Entity, ghost: Entity, prob: Problem) -> None:
    ghost.memes["hope"] = 1
    hero.memes["focus"] = 1
    if prob.id == "dim_lantern":
        lantern = world.add(Entity(id="lantern", label="lantern", kind="thing", type="lantern"))
        jar = world.add(Entity(id="jar", label="silver jar", kind="thing", type="jar"))
        ribbon = world.add(Entity(id="ribbon", label="fresh ribbon", kind="thing", type="ribbon"))
        lantern.meters["glow"] = 0
        jar.meters["seal"] = 1
        ribbon.meters["tied"] = 1
        world.say(
            f"{hero.id} found a silver jar, tied it with a fresh ribbon, and sealed the crack."
        )
        lantern.meters["glow"] = 2
        ghost.meters["glow"] = 3
    elif prob.id == "lost_song":
        box = world.add(Entity(id="music_box", label="music box", kind="thing", type="music_box"))
        key = world.add(Entity(id="key", label="tiny key", kind="thing", type="key"))
        box.meters["wind"] = 1
        key.meters["found"] = 1
        world.say(
            f"{hero.id} found the music box, picked up the tiny key, and wound it gently."
        )
        ghost.meters["glow"] = 2
    else:
        window = world.add(Entity(id="window", label="window", kind="thing", type="window"))
        curtain = world.add(Entity(id="curtain", label="curtain", kind="thing", type="curtain"))
        window.meters["open"] = 0
        curtain.meters["closed"] = 1
        world.say(
            f"{hero.id} shut the window and tucked in the curtain so the moon wind could not sneak back in."
        )
        ghost.meters["glow"] = 2

    world.say(
        f"{ghost.id} smiled, because {prob.fix} had helped {prob.missing} return."
    )


def rhyme_close(world: World, hero: Entity, ghost: Entity, prob: Problem) -> None:
    ghost.memes["relief"] = 1
    hero.memes["joy"] = 1
    world.say(prob.rhyme)
    world.say(
        f"At the end, {ghost.id} glowed softly in the dark, and {hero.id} walked home with a brave little smile."
    )


def tell(setting: Setting, hero_name: str, hero_type: str, ghost_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    ghost = world.add(Entity(id=ghost_name, kind="character", type="ghost"))
    prob = build_problem(setting.place)
    world.facts.update(hero=hero, ghost=ghost, problem=prob, setting=setting)

    introduce(world, hero, ghost)
    world.para()
    establish_problem(world, hero, ghost, prob)
    world.para()
    flashback(world, ghost, prob)
    world.para()
    solve(world, hero, ghost, prob)
    rhyme_close(world, hero, ghost, prob)

    world.facts["resolved"] = True
    return world


KNOWLEDGE = {
    "ghost": [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky character that can float, whisper, and show up in dark places in a story."
        ),
    ],
    "flashback": [
        QAItem(
            question="What does a flashback do in a story?",
            answer="A flashback shows something that happened earlier, so the reader can understand why the present problem matters."
        ),
    ],
    "rhyme": [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like light and night."
        ),
    ],
    "lymph": [
        QAItem(
            question="What word is the spooky glow-stuff called in this story world?",
            answer="In this story world, the spooky glow-stuff is called lymph, and it helps a ghost's lantern shine."
        ),
    ],
    "problem_solving": [
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means noticing what is wrong, thinking about clues, and choosing a helpful step to fix it."
        ),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    prob: Problem = f["problem"]
    return [
        f'Write a short ghost story for young children that includes the word "lymph" and a flashback.',
        f"Tell a gentle spooky story where {f['hero'].id} helps a ghost fix {prob.missing} by solving a clue.",
        f"Write a child-friendly ghost story with a rhyme at the end about {prob.fix}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ghost, prob = f["hero"], f["ghost"], f["problem"]
    return [
        QAItem(
            question=f"Who visited {world.setting.place} on the quiet night?",
            answer=f"{hero.id} visited {world.setting.place} and met {ghost.id} there."
        ),
        QAItem(
            question=f"What was wrong for {ghost.id} at first?",
            answer=f"{prob.missing} was gone because {prob.leak}."
        ),
        QAItem(
            question=f"What clue helped {hero.id} notice how to help?",
            answer=f"{prob.clue} helped {hero.id} figure out where to start."
        ),
        QAItem(
            question=f"What happened in the flashback?",
            answer=f"In the flashback, {ghost.id} remembered {prob.flashback_line.lower()}"
        ),
        QAItem(
            question=f"How did the problem get fixed?",
            answer=f"{hero.id} used problem solving to do this: {prob.fix}."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The story ended with {ghost.id} glowing softly and {hero.id} going home with a brave smile."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [item for key in ("lymph", "flashback", "problem_solving", "rhyme", "ghost") for item in KNOWLEDGE[key]]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="old_house", hero_name="Mina", hero_type="girl", ghost_name="Murmur"),
    StoryParams(place="attic", hero_name="Jasper", hero_type="boy", ghost_name="Wisp"),
    StoryParams(place="graveyard_gate", hero_name="Nell", hero_type="child", ghost_name="Bell"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story world with lymph, flashbacks, and rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--ghost")
    ap.add_argument("--gender", choices=["girl", "boy", "child"])
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
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(TYPES)
    hero_name = args.name or rng.choice(HERO_NAMES)
    ghost_name = args.ghost or rng.choice(GHOST_NAMES)
    return StoryParams(place=place, hero_name=hero_name, hero_type=gender, ghost_name=ghost_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.hero_name, params.hero_type, params.ghost_name)
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


ASP_RULES = r"""
storyworld(place, lymph, flashback, problem_solving, rhyme).

ghost_story(P) :- storyplace(P).
problem(P) :- storyproblem(P).
flashback_used :- storyflashback.
rhyme_used :- storyrhyme.
valid_story(P) :- storyplace(P), storylymph, storyflashback, storyproblem_solving, storyrhyme.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("storyplace", pid))
    lines.append(asp.fact("storylymph"))
    lines.append(asp.fact("storyflashback"))
    lines.append(asp.fact("storyproblem_solving"))
    lines.append(asp.fact("storyrhyme"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
