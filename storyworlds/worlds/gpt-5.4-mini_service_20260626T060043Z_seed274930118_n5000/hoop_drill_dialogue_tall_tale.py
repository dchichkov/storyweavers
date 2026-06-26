#!/usr/bin/env python3
"""
A small storyworld in a tall-tale style about a hoop, a drill, and a talking
problem that gets solved with a smarter plan.
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
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"damage": 0.0, "dust": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "frustration": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


@dataclass
class Tool:
    id: str
    label: str
    verb: str
    noise: str
    mess: str
    risk: str
    reason: str
    fix: str


PLACES = {
    "workshop": "the old workshop",
    "barn": "the red barn",
    "shed": "the little shed",
    "yard": "the wide yard",
}

HEROES = {
    "boy": ["Finn", "Jasper", "Milo", "Toby", "Ned"],
    "girl": ["Ruby", "Mabel", "Hazel", "June", "Daisy"],
}

HELPERS = {
    "father": "father",
    "mother": "mother",
    "grandpa": "grandpa",
    "grandma": "grandma",
}

TOOLS = {
    "hoop": Tool(
        id="hoop",
        label="hoop",
        verb="make the hoop stand straight",
        noise="a loud clang",
        mess="scrape",
        risk="bent",
        reason="the hoop could get bent or scuffed",
        fix="use a steadier guide instead of brute force",
    ),
    "drill": Tool(
        id="drill",
        label="drill",
        verb="drill the holes cleanly",
        noise="a buzzing whirr",
        mess="dust",
        risk="blown out",
        reason="the board could crack or get blown out",
        fix="start with a small mark and a gentle hand",
    ),
}

CURATED = [
    StoryParams(place="workshop", hero="Finn", hero_type="boy", helper="father", helper_type="father"),
    StoryParams(place="barn", hero="Ruby", hero_type="girl", helper="grandpa", helper_type="grandpa"),
    StoryParams(place="shed", hero="Milo", hero_type="boy", helper="mother", helper_type="mother"),
    StoryParams(place="yard", hero="Hazel", hero_type="girl", helper="grandma", helper_type="grandma"),
]


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a small but mighty {hero.type} who could lift a bucket with one hand and a daydream with the other."
    )


def setup(world: World, hero: Entity, helper: Entity, tool: Tool) -> None:
    world.say(
        f"{hero.id} found a {tool.label} and said, \"I can {tool.verb} all by myself!\""
    )
    world.say(
        f"{helper.id} smiled and said, \"Maybe, but even a tall pine leans toward good advice.\""
    )
    world.say(
        f"{hero.id} grinned. \"Then let's see who can work faster, me or the wind!\""
    )
    hero.memes["joy"] += 0.5
    helper.memes["pride"] += 0.5


def predict(world: World, hero: Entity, tool: Tool) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    h.memes["frustration"] += 1.0
    if tool.id == "hoop":
        h.meters["damage"] += 0.0
        return {"damaged": False, "mess": False}
    if tool.id == "drill":
        h.meters["dust"] += 1.0
        return {"damaged": True, "mess": True}
    return {"damaged": False, "mess": False}


def attempt(world: World, hero: Entity, helper: Entity, tool: Tool) -> None:
    world.say(f"Then {hero.id} picked up the {tool.label}.")
    if tool.id == "hoop":
        world.say(
            f"{tool.label.capitalize()} went {tool.noise}, and {hero.id} tried to muscle it into place."
        )
        hero.meters["damage"] += 0.5
        hero.memes["frustration"] += 1.0
        world.say(
            f"The hoop wobbled like a lazy moonbeam, and {hero.id} said, \"That thing has a will of its own!\""
        )
    else:
        world.say(
            f"The drill sang {tool.noise}, and tiny specks of dust danced in the air like brown fireflies."
        )
        hero.meters["dust"] += 1.0
        hero.memes["frustration"] += 1.0
        world.say(
            f"{hero.id} coughed and said, \"This drill is louder than a goose in a trumpet shop!\""
        )


def warn(world: World, helper: Entity, hero: Entity, tool: Tool) -> bool:
    pred = predict(world, hero, tool)
    if not pred["damaged"]:
        return False
    world.say(
        f"\"Hold on now,\" said {helper.id}. \"If you keep at it like that, the {tool.label} will get {tool.risk}, and we'll have a sad ending.\""
    )
    return True


def conflict(world: World, hero: Entity, helper: Entity, tool: Tool) -> None:
    hero.memes["frustration"] += 0.5
    world.say(
        f"{hero.id} planted {hero.pronoun('possessive')} boots and said, \"I don't need help from anybody older than a fence post!\""
    )
    world.say(
        f"{helper.id} answered, \"And I don't need a cracked board telling me I was right.\""
    )


def compromise(world: World, helper: Entity, hero: Entity, tool: Tool) -> None:
    if tool.id == "hoop":
        world.say(
            f"Then {helper.id} fetched a straight board and said, \"Let's guide the hoop gentle-like so it sits where it ought to sit.\""
        )
        world.say(
            f"{hero.id} nodded and said, \"Aha! A hoop may be round, but it likes a sensible road.\""
        )
    else:
        world.say(
            f"Then {helper.id} marked the wood first and said, \"Let's start with a tiny hole so the drill knows its manners.\""
        )
        world.say(
            f"{hero.id} nodded and said, \"A little mark is worth a wagonload of guesswork.\""
        )


def resolve(world: World, hero: Entity, helper: Entity, tool: Tool) -> None:
    hero.memes["frustration"] = 0.0
    hero.memes["joy"] += 1.0
    helper.memes["pride"] += 1.0
    if tool.id == "hoop":
        hero.meters["damage"] = 0.0
        world.say(
            f"Together they set the hoop true, and it stood bright and proud as a silver sunrise."
        )
    else:
        hero.meters["dust"] = 0.0
        world.say(
            f"Together they drilled the holes cleanly, and the board held firm as an oak root."
        )
    world.say(
        f"{helper.id} laughed and said, \"Sometimes the fastest way is the slow, careful one.\""
    )
    world.say(
        f"{hero.id} laughed too, because now the job was done and the whole place felt taller."
    )


def tell(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type))
    tool = TOOLS["hoop" if "hoop" in params.place or params.place in {"yard", "barn"} else "drill"]

    world.facts.update(hero=hero, helper=helper, tool=tool, place=world.place)

    intro(world, hero)
    setup(world, hero, helper, tool)
    world.para()
    world.say(f"One bright afternoon at {world.place}, {hero.id} decided to use the {tool.label}.")
    attempt(world, hero, helper, tool)
    warn(world, helper, hero, tool)
    conflict(world, hero, helper, tool)
    world.para()
    compromise(world, helper, hero, tool)
    resolve(world, hero, helper, tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tool = f["tool"]
    hero = f["hero"]
    helper = f["helper"]
    return [
        f'Write a tall-tale story for a child about a {tool.label} and a careful fix.',
        f'Tell a lively dialogue story where {hero.id} and {helper.id} argue a little, then solve a {tool.label} problem.',
        f"Write a short, funny tale set in {world.place} where a {tool.label} almost causes trouble but ends well.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    tool: Tool = f["tool"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, who was working at {place} with {helper.id}.",
        ),
        QAItem(
            question=f"What tool caused the trouble?",
            answer=f"The trouble came from the {tool.label}, which was loud and hard to handle at first.",
        ),
        QAItem(
            question=f"How did {helper.id} help?",
            answer=f"{helper.id} helped by suggesting a gentler plan, so they could use the {tool.label} without making a bigger mess.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hoop?",
            answer="A hoop is a round ring shape, like a circle made out of metal, wood, or rope.",
        ),
        QAItem(
            question="What does a drill do?",
            answer="A drill spins a bit very fast so it can make holes in wood, walls, or other materials.",
        ),
        QAItem(
            question="Why should you start drilling gently?",
            answer="Starting gently helps the drill make a neat hole and keeps the wood from cracking or splintering.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        out.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(out)


@dataclass
class StoryRegistry:
    places: dict[str, str] = field(default_factory=lambda: dict(PLACES))


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    lines.append(asp.fact("special", "hoop"))
    lines.append(asp.fact("special", "drill"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,T) :- place(P), tool(T), special(T).
#show valid_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {(p, t) for p in PLACES for t in TOOLS if t in {"hoop", "drill"}}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} stories).")
        return 0
    print("MISMATCH")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld about a hoop and a drill.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    hero_type = rng.choice(["boy", "girl"])
    hero = args.name or rng.choice(HEROES[hero_type])
    helper_type = args.helper or rng.choice(list(HELPERS))
    helper = args.helper or HELPERS[helper_type]
    if helper == hero:
        raise StoryError("The helper and hero must be different characters.")
    return StoryParams(place=place, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type)


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid()
        print(f"{len(pairs)} compatible story pairs:")
        for p, t in pairs:
            print(f"  {p:10} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, p in enumerate(CURATED):
            p.seed = base_seed + i
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.hero} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
