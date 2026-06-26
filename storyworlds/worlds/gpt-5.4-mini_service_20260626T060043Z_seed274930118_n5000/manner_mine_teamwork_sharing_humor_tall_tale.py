#!/usr/bin/env python3
"""
storyworlds/worlds/manner_mine_teamwork_sharing_humor_tall_tale.py
===================================================================

A small tall-tale storyworld about a child-sized crew, a mine, and a shared
job that only works through teamwork, sharing, and a little humor.

Seed idea:
- A young helper in a frontier town wants to go into a mine.
- The grown-up worries about safety and the lantern, rope, and cart.
- The crew finds a mannerly way to share tools and laugh together.
- The work becomes easier, the danger fades, and the mine ends with a bright
  haul and a bigger smile.

This world keeps a classical simulation: characters, tools, places, and
emotional/physical state evolve as the story is told.
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
    carried_by: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"safe": 0.0, "shine": 0.0, "dust": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "humor": 0.0, "teamwork": 0.0, "sharing": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the mine"
    afford: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    kind: str
    shareable: bool = True


@dataclass
class Goal:
    id: str
    noun: str
    verb: str
    reward: str
    hazard: str
    zone: str
    requires: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def chars(self):
        return [e for e in self.entities.values() if e.kind == "character"]

    def tools(self):
        return [e for e in self.entities.values() if e.kind == "tool"]


def _act_teamwork(world: World) -> list[str]:
    out = []
    crew = world.chars()
    if len(crew) >= 2 and ("teamwork",) not in world.fired:
        if sum(e.memes["teamwork"] for e in crew) >= THRESHOLD:
            world.fired.add(("teamwork",))
            out.append("The little crew worked together as neatly as three ants on a sugar crumb.")
    return out


def _act_sharing(world: World) -> list[str]:
    out = []
    for tool in world.tools():
        if tool.meters.get("shared", 0) < THRESHOLD:
            continue
        sig = ("sharing", tool.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"They shared {tool.label} kindly so nobody had to do the job alone.")
    return out


def _act_humor(world: World) -> list[str]:
    out = []
    for ent in world.chars():
        if ent.memes["humor"] < THRESHOLD:
            continue
        sig = ("humor", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"A joke rolled through the tunnel and chased away the grumbly echoes.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_act_teamwork, _act_sharing, _act_humor):
            lines = fn(world)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for line in out:
            world.say(line)
    return out


def build_story(world: World, hero: Entity, elder: Entity, goal: Goal, tools: list[Entity]) -> None:
    world.say(f"{hero.id} was a nimble little helper with a manner so polite it could smooth a wrinkled map.")
    world.say(f"{hero.id} loved the old mine because it promised {goal.reward}, even if the dark tunnels looked long as winter.")
    world.say(f"One bright morning, {hero.id} and {elder.id} went to {world.setting.place}, where the rocks sang softly under their boots.")
    world.para()

    hero.memes["worry"] += 1
    elder.memes["worry"] += 1
    world.say(
        f"{hero.id} wanted to {goal.verb}, but {elder.id} held up a hand. "
        f"\"Not unless we keep our manner and our wits,\" {elder.id} said, peering at the {goal.hazard} in the shaft."
    )
    world.say(f"{hero.id} grinned anyway. \"Then let's make it a fine old team job,\" {hero.id} said.")
    hero.memes["humor"] += 1
    hero.memes["teamwork"] += 1
    elder.memes["teamwork"] += 1
    propagate(world)
    world.para()

    lantern, rope, cart = tools
    lantern.meters["shared"] = 1
    rope.meters["shared"] = 1
    cart.meters["shared"] = 1
    hero.memes["sharing"] += 1
    elder.memes["sharing"] += 1
    world.say(
        f"They shared the {lantern.label}, the {rope.label}, and the {cart.label}, "
        f"passing each tool with the care of folks handling a pie at Sunday supper."
    )
    world.say(
        f"{hero.id} held the light, {elder.id} steadied the rope, and together they nudged the cart along the rails."
    )
    propagate(world)
    world.para()

    world.say(
        f"Then the mine gave a mighty clink and out popped {goal.reward}, bright as a breakfast moon."
    )
    world.say(
        f"{hero.id} laughed so hard the dust shook off the beams. \"Well, that's the biggest little victory I ever saw,\" "
        f"{elder.id} said."
    )
    hero.memes["joy"] += 2
    elder.memes["joy"] += 1
    hero.meters["shine"] += 1
    world.say(
        f"By sunset, {hero.id} had {goal.reward}, {goal.hazard} looked less scary, and the mine felt friendlier than a porch swing."
    )

    world.facts.update(hero=hero, elder=elder, goal=goal, tools=tools)


SETTINGS = {
    "mine": Setting(place="the old mine", afford={"dig", "carry", "sort"}),
    "hill": Setting(place="the hill mine", afford={"dig", "carry", "sort"}),
    "cave": Setting(place="the cave mine", afford={"dig", "carry", "sort"}),
}

GOALS = {
    "gold": Goal(
        id="gold",
        noun="gold",
        verb="dig for gold",
        reward="a pan of gold dust",
        hazard="loose stone",
        zone="tunnel",
        requires={"lantern", "rope", "cart"},
    ),
    "ore": Goal(
        id="ore",
        noun="ore",
        verb="carry ore",
        reward="a cart full of shining ore",
        hazard="dark bends",
        zone="rail",
        requires={"lantern", "rope", "cart"},
    ),
    "gem": Goal(
        id="gem",
        noun="gem",
        verb="search for gems",
        reward="a glassy blue gem",
        hazard="small cave-ins",
        zone="wall",
        requires={"lantern", "rope"},
    ),
}

TOOLS = {
    "lantern": Tool(id="lantern", label="lantern", phrase="a brass lantern", kind="light"),
    "rope": Tool(id="rope", label="rope", phrase="a sturdy rope", kind="support"),
    "cart": Tool(id="cart", label="cart", phrase="a little ore cart", kind="carry"),
}

NAMES = {
    "girl": ["Mabel", "Nell", "Ada", "June", "Bess"],
    "boy": ["Hank", "Otis", "Clive", "Wes", "Bo"],
}
ELDERS = ["Granny Pike", "Uncle Red", "Marshal Dot", "Old Finn"]


@dataclass
class StoryParams:
    place: str
    goal: str
    name: str
    gender: str
    elder: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(p, g) for p in SETTINGS for g in GOALS]


def reasonableness_gate(place: str, goal: str) -> bool:
    return place in SETTINGS and goal in GOALS


def _story_intro(hero: Entity, elder: Entity, goal: Goal) -> None:
    pass


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    elder = world.add(Entity(id=params.elder, kind="character", type="adult"))

    goal = GOALS[params.goal]
    lantern = world.add(Entity(id="lantern", kind="tool", type="tool", label="lantern", phrase="a brass lantern", owner=hero.id))
    rope = world.add(Entity(id="rope", kind="tool", type="tool", label="rope", phrase="a sturdy rope", owner=hero.id))
    cart = world.add(Entity(id="cart", kind="tool", type="tool", label="cart", phrase="a little ore cart", owner=elder.id))

    build_story(world, hero, elder, goal, [lantern, rope, cart])
    world.facts["goal"] = goal
    world.facts["hero"] = hero
    world.facts["elder"] = elder
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    goal: Goal = f["goal"]
    return [
        f"Write a tall tale about {hero.id}, a polite helper, who goes to the mine to {goal.verb} with a friend.",
        f"Tell a child-friendly frontier story where teamwork, sharing, and humor help {hero.id} bring home {goal.reward}.",
        f"Write a short story about a mine trip that starts with worry and ends with a funny shared success.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    goal: Goal = f["goal"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, who goes to the mine with {elder.id} and learns to work together politely.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the mine?",
            answer=f"{hero.id} wanted to {goal.verb}, and that led to a careful plan with tools and teamwork.",
        ),
        QAItem(
            question=f"How did the crew solve the problem in the mine?",
            answer=f"They shared the lantern, rope, and cart, used humor to stay brave, and made teamwork do the heavy lifting.",
        ),
        QAItem(
            question=f"What did they bring home at the end?",
            answer=f"They brought home {goal.reward}, and the mine ended up feeling safer and friendlier.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mine?",
            answer="A mine is a place where people go deep underground or into rock to look for useful things like ore or gold.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting more than one person use the same thing or enjoy the same thing fairly.",
        ),
        QAItem(
            question="Why does teamwork help?",
            answer="Teamwork helps because two or more people can combine their strength and ideas to do a job better.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is something funny that makes people smile or laugh, which can help them feel braver.",
        ),
        QAItem(
            question="What does manner mean?",
            answer="Manner means the way someone acts toward others, like being polite, gentle, and respectful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
goal_combo(P,G) :- place(P), goal(G).
valid_story(P,G) :- goal_combo(P,G), place(P), goal(G).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for g in GOALS:
        lines.append(asp.fact("goal", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python")
    if py - asp_set:
        print("Only in Python:", sorted(py - asp_set))
    if asp_set - py:
        print("Only in ASP:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale mine storyworld about teamwork, sharing, and humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=ELDERS)
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
    if args.place and args.goal and not reasonableness_gate(args.place, args.goal):
        raise StoryError("That place-goal pair does not make a reasonable mine story.")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.goal:
        combos = [c for c in combos if c[1] == args.goal]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, goal = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    elder = args.elder or rng.choice(ELDERS)
    return StoryParams(place=place, goal=goal, name=name, gender=gender, elder=elder)


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


CURATED = [
    StoryParams(place="mine", goal="gold", name="Mabel", gender="girl", elder="Uncle Red"),
    StoryParams(place="hill", goal="ore", name="Hank", gender="boy", elder="Granny Pike"),
    StoryParams(place="cave", goal="gem", name="June", gender="girl", elder="Marshal Dot"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
