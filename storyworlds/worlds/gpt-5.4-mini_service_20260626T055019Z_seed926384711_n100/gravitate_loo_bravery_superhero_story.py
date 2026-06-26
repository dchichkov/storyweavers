#!/usr/bin/env python3
"""
A small superhero-story world about bravery, a strange gravitate pull, and a loo
mix-up that turns into a courageous rescue.

The premise:
- A young hero wants to help.
- A slippery signal called gravitate keeps tugging them toward trouble.
- A nearby loo causes an embarrassing delay or obstruction.
- Bravery lets the hero choose action over fear and finish the rescue.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    detail: str


@dataclass
class Hazard:
    id: str
    label: str
    verb: str
    pull: str
    risk: str
    trigger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    verb: str
    fix: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_panic(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("stuck", 0) >= THRESHOLD and e.memes.get("fear", 0) >= THRESHOLD:
            sig = ("panic", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["panic"] = e.memes.get("panic", 0) + 1
            out.append(f"{e.id}'s heart thumped faster, but {e.pronoun()} kept looking for a way through.")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("bravery", 0) < THRESHOLD:
            continue
        sig = ("bravery", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["steady"] = e.memes.get("steady", 0) + 1
        out.append(f"{e.id} straightened up, because bravery made the next step feel possible.")
    return out


CAUSAL_RULES = [_r_panic, _r_bravery]


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


def predict_block(world: World, hero: Entity, hazard: Hazard) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["fear"] = sim.get(hero.id).memes.get("fear", 0) + 1
    sim.get(hero.id).memes["stuck"] = sim.get(hero.id).memes.get("stuck", 0) + 1
    propagate(sim, narrate=False)
    return {
        "panic": sim.get(hero.id).memes.get("panic", 0) >= THRESHOLD,
    }


def build_intro(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    world.say(
        f"{hero.id} was a small {hero.type} with a brave cape and a habit of helping."
    )
    world.say(
        f"{friend.id} stayed close by, because the city felt safer when they were together."
    )
    world.say(place.detail)


def build_problem(world: World, hero: Entity, hazard: Hazard, tool: Tool) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"One afternoon, a strange force called gravitate began to tug {hero.pronoun('object')} toward the {hazard.label}."
    )
    world.say(
        f"{hazard.trigger}, and that made the path harder to cross."
    )
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    hero.memes["stuck"] = hero.memes.get("stuck", 0) + 1
    world.say(
        f"Then a crowded loo door slammed shut ahead, and the narrow hallway turned awkward and tight."
    )
    if predict_block(world, hero, hazard)["panic"]:
        world.say(
            f"{hero.id} almost froze, because the pull felt bigger than {hero.pronoun('possessive')} legs."
        )


def build_turn(world: World, hero: Entity, friend: Entity, hazard: Hazard, tool: Tool) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    world.say(
        f"{friend.id} pointed at the mess and said, \"You can do this. Brave heroes do not stop at the first wobble.\""
    )
    propagate(world, narrate=True)
    world.say(
        f"{hero.id} took a deep breath, backed away from the loo, and used {tool.label} to steady the slippery spot."
    )
    world.say(
        f"That gave {hero.pronoun('object')} room to move around the gravitate tug instead of into it."
    )


def build_resolution(world: World, hero: Entity, friend: Entity, hazard: Hazard) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    hero.memes["fear"] = 0
    hero.memes["stuck"] = 0
    world.say(
        f"At last, {hero.id} reached the {hazard.label}, and the trapped kitten popped free."
    )
    world.say(
        f"The little rescue made {hero.id} grin, and even the loo hallway seemed less cramped after that."
    )
    world.say(
        f"{friend.id} laughed and said the city had just seen a real brave superhero at work."
    )


@dataclass
class StoryParams:
    name: str
    sidekick: str
    gender: str
    seed: Optional[int] = None


HERO_NAMES = ["Nova", "Milo", "Pip", "Iris", "Zane", "Mina", "Arlo", "Tess"]
SIDEKICK_NAMES = ["Bram", "Luna", "Beck", "Mira", "Jules", "Nia"]
GENDERS = ["girl", "boy"]

PLACE = Place(
    name="the city block",
    detail="The city block was bright, with a narrow lane, a shiny doorway, and one tricky little corner.",
)

HAZARDS = {
    "kitten": Hazard(
        id="kitten",
        label="kitty",
        verb="rescue the kitten",
        pull="gravitate kept tugging toward the trapped kitten",
        risk="the kitten was stuck behind a cracked fence",
        trigger="A small cry came from beside the alley",
        tags={"gravitate", "rescue", "bravery"},
    )
}

TOOLS = {
    "stabilizer": Tool(
        id="stabilizer",
        label="a bright stabilizer baton",
        verb="steady the path",
        fix="kept the feet from slipping",
        tags={"bravery", "rescue"},
    )
}


def valid_combos() -> list[tuple[str, str]]:
    return [(PLACE.name, "kitten")]


@dataclass
class DummyReg:
    pass


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    hazard = f["hazard"]
    return [
        f'Write a short superhero story for a young child that includes the word "gravitate" and the word "loo".',
        f"Tell a brave rescue story about {hero.id}, who keeps helping even when gravitate tugs toward a {hazard.label}.",
        f"Write a child-friendly superhero tale where a hero faces a loo problem, chooses bravery, and saves the day.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    hazard = f["hazard"]
    return [
        QAItem(
            question=f"Who was the brave superhero in the story?",
            answer=f"The brave superhero was {hero.id}, and {friend.id} stayed by {hero.pronoun('possessive')} side.",
        ),
        QAItem(
            question=f"What strange force kept tugging at {hero.id}?",
            answer=f"A strange force called gravitate kept tugging {hero.pronoun('object')} toward the {hazard.label}.",
        ),
        QAItem(
            question=f"What problem made the hallway awkward?",
            answer="A crowded loo door and a narrow hallway made the path feel tight and hard to cross.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} used bravery, listened to {friend.pronoun('object')}, and steadied the slippery spot with a bright stabilizer baton.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel scared or nervous.",
        ),
        QAItem(
            question="What is a loo?",
            answer="A loo is a bathroom or toilet room.",
        ),
        QAItem(
            question="What is gravity?",
            answer="Gravity is the force that pulls things toward the ground and keeps us from floating away.",
        ),
        QAItem(
            question="Why do heroes use tools?",
            answer="Heroes use tools to make a hard task safer or easier, like steadying a slippery path.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- brave(X).
problem(X) :- gravitate_pull(X), loo_block(X).
resolution(X) :- brave(X), tool_used(X), rescued(X).
#show hero/1.
#show problem/1.
#show resolution/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("brave", "nova"),
        asp.fact("gravitate_pull", "nova"),
        asp.fact("loo_block", "nova"),
        asp.fact("tool_used", "nova"),
        asp.fact("rescued", "nova"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show hero/1.\n#show problem/1.\n#show resolution/1."))
    atoms = {sym.name for sym in model}
    ok = {"hero", "problem", "resolution"} <= atoms
    if ok:
        print("OK: ASP twin produced the expected superhero story markers.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected markers.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world about bravery, gravitate, and a loo.")
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICK_NAMES)
    ap.add_argument("--gender", choices=GENDERS)
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
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICK_NAMES)
    return StoryParams(name=name, sidekick=sidekick, gender=gender)


def tell(params: StoryParams) -> World:
    world = World(PLACE)
    hero_type = "girl" if params.gender == "girl" else "boy"
    hero = world.add(Entity(id=params.name, kind="character", type=hero_type, traits=["brave", "kind"]))
    friend = world.add(Entity(id=params.sidekick, kind="character", type="friend"))
    hazard = HAZARDS["kitten"]
    tool = TOOLS["stabilizer"]

    world.facts = {"hero": hero, "friend": friend, "hazard": hazard, "tool": tool}

    build_intro(world, hero, friend, PLACE)
    world.para()
    build_problem(world, hero, hazard, tool)
    world.para()
    build_turn(world, hero, friend, hazard, tool)
    world.para()
    build_resolution(world, hero, friend, hazard)
    return world


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
        print(asp_program("#show hero/1.\n#show problem/1.\n#show resolution/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show hero/1.\n#show problem/1.\n#show resolution/1."))
        print("ASP atoms:", [str(a) for a in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(name=HERO_NAMES[0], sidekick=SIDEKICK_NAMES[0], gender="girl")
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
