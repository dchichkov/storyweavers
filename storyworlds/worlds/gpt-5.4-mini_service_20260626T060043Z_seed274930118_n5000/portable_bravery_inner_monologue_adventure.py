#!/usr/bin/env python3
"""
portable_bravery_inner_monologue_adventure.py
==============================================

A small storyworld about portable bravery: a child steps into a little
adventure, hears their own inner monologue, and learns that courage can travel
with them.

Premise:
- A child wants to cross a small wild place to do something helpful or daring.
- They feel fear, but they have a portable helper object that makes the task
  feel possible.
- Their inner monologue changes from doubt to planning to bravery.
- The ending proves the change with a concrete action and a calmer world state.
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
    carrier: Optional[str] = None
    portable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    detail: str
    danger: str
    afford: str
    challenge: str
    help_text: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    kind: str
    helps_against: set[str]
    boost: float
    portable: bool = True


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    risk: str
    need: str
    reward: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    goal: str
    tool: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "woods": Place(
        id="woods",
        label="the whispering woods",
        detail="The trees stood close together, and the path curved around roots and stones.",
        danger="a dark thicket and a narrow creek",
        afford="cross the creek",
        challenge="the water looked cold and quick",
        help_text="A small light or steady reminder could help here.",
    ),
    "cave": Place(
        id="cave",
        label="the small cave",
        detail="The cave mouth was round like a door, and the inside looked dim and quiet.",
        danger="a deep shadow and a slippery floor",
        afford="walk through the cave",
        challenge="the dark made every step feel bigger",
        help_text="A portable lamp or brave thought could help here.",
    ),
    "hill": Place(
        id="hill",
        label="the windy hill",
        detail="Grass bent in the wind, and the hilltop was far enough away to feel like a journey.",
        danger="a steep path and a sudden gust",
        afford="reach the hilltop",
        challenge="the wind tugged at clothes and courage",
        help_text="A map or a pocket charm could help here.",
    ),
    "harbor": Place(
        id="harbor",
        label="the harbor walkway",
        detail="Boats bumped softly below, and the boards creaked above the water.",
        danger="a wobbly dock and splashing waves",
        afford="cross the dock",
        challenge="the boards moved underfoot",
        help_text="A steadying tool or brave inner voice could help here.",
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="a little lantern",
        phrase="a little lantern with a warm glow",
        kind="light",
        helps_against={"dark", "shadow"},
        boost=1.5,
    ),
    "map": Tool(
        id="map",
        label="a folded map",
        phrase="a folded map with a bright red line",
        kind="direction",
        helps_against={"lost", "uncertain"},
        boost=1.0,
    ),
    "whistle": Tool(
        id="whistle",
        label="a tin whistle",
        phrase="a tiny tin whistle on a blue string",
        kind="signal",
        helps_against={"lonely", "afraid"},
        boost=0.9,
    ),
    "coin": Tool(
        id="coin",
        label="a lucky coin",
        phrase="a lucky coin that fit in a palm",
        kind="comfort",
        helps_against={"afraid", "shaky"},
        boost=0.8,
    ),
}

GOALS = {
    "message": Goal(
        id="message",
        label="deliver a message",
        phrase="deliver a message to the far side",
        risk="getting lost on the path",
        need="knowing the way and keeping calm",
        reward="someone waiting on the other side would get good news",
    ),
    "berries": Goal(
        id="berries",
        label="pick berries",
        phrase="pick berries from the hill",
        risk="slipping before reaching the bushes",
        need="watching the ground and moving carefully",
        reward="there would be a bright bowl of berries at the end",
    ),
    "lantern": Goal(
        id="lantern",
        label="return the lantern",
        phrase="return a borrowed lantern to the ranger",
        risk="the cave being too dark to trust",
        need="a steady step and a brave thought",
        reward="the ranger would smile and thank them",
    ),
}

TRAITS = ["curious", "gentle", "stubborn", "spirited", "quiet", "bright"]
GIRL_NAMES = ["Mia", "Lina", "Nora", "Ava", "Zoe", "Ella", "Iris", "May", "Ada", "Rose"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Noah", "Eli", "Ben", "Sam", "Tom", "Jack"]


def _inner_voice(hero: Entity, fear: float, courage: float) -> str:
    if fear >= 2.0 and courage < 1.0:
        return f"{hero.id} thought, 'This is bigger than I expected.'"
    if courage >= fear:
        return f"{hero.id} thought, 'I can do one careful step at a time.'"
    return f"{hero.id} thought, 'Keep breathing. The next step is enough.'"


def _boost_from_tool(world: World, hero: Entity, tool: Entity, danger: str) -> float:
    boost = 0.0
    for tag in tool.meters.get("helps_against", set()):
        if tag in danger:
            boost += 1.0
    boost += tool.meters.get("boost", 0.0)
    if tool.carrier == hero.id:
        boost += 0.5
    return boost


def _can_succeed(world: World, hero: Entity, goal: Goal, tool: Entity) -> bool:
    fear = hero.memes.get("fear", 0.0)
    courage = hero.memes.get("courage", 0.0)
    preparation = tool.meters.get("boost", 0.0)
    return courage + preparation >= fear or tool.kind in {"light", "direction", "comfort", "signal"}


def tell(place: Place, goal: Goal, tool_def: Tool, hero_name: str, hero_gender: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        meters={"steps": 0.0},
        memes={"fear": 1.5, "courage": 0.5, "hope": 0.3, "worry": 1.0},
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type="adult",
        label="the guide",
        meters={},
        memes={"calm": 1.0},
    ))
    tool = world.add(Entity(
        id=tool_def.id,
        kind="object",
        type=tool_def.kind,
        label=tool_def.label,
        phrase=tool_def.phrase,
        owner=hero.id,
        portable=True,
        meters={"boost": tool_def.boost},
    ))
    tool.meters["helps_against"] = set(tool_def.helps_against)  # type: ignore[assignment]
    tool.carrier = hero.id

    world.say(f"{hero.id} was a {trait} little {hero_gender} who loved adventures, even the sort that made a stomach flutter.")
    world.say(f"One day, {hero.id} had to {goal.phrase} through {place.label}. {place.detail}")
    world.say(f"{hero.id} carried {tool.phrase}; it felt small, but it was portable and stayed close like a secret helper.")

    world.para()
    world.say(f"The path asked for {place.challenge}. {place.help_text}")
    world.say(_inner_voice(hero, hero.memes["fear"], hero.memes["courage"]))
    hero.memes["fear"] += 0.5
    hero.memes["worry"] += 0.5

    if tool_def.kind == "light":
        world.say(f"{hero.id} lifted {tool.label}, and the dark corners shrank into plain, readable shapes.")
    elif tool_def.kind == "direction":
        world.say(f"{hero.id} opened {tool.label}, and the folded line showed where to step next.")
    elif tool_def.kind == "signal":
        world.say(f"{hero.id} touched {tool.label} and remembered that help was only a call away.")
    else:
        world.say(f"{hero.id} closed a hand around {tool.label} and felt a brave, steady tick in the palm.")

    boost = _boost_from_tool(world, hero, tool, place.danger)
    hero.memes["courage"] += boost
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.6)

    world.say(_inner_voice(hero, hero.memes["fear"], hero.memes["courage"]))

    success = _can_succeed(world, hero, goal, tool)
    if not success:
        world.say(f"{hero.id} stopped, because the way still felt too hard to trust.")
        world.facts.update(hero=hero, guide=guide, tool=tool, goal=goal, success=False)
        return world

    world.para()
    hero.meters["steps"] += 1
    hero.meters["steps"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.8)
    hero.memes["courage"] += 0.8
    world.say(f"{hero.id} took one careful step, then another.")
    world.say(f"The small tool stayed in {hero.id}'s hand, and the hand stayed steady.")
    world.say(f"At the hardest spot, {hero.id} whispered, 'I am scared, but I am still going.'")
    world.say(f"That was the brave part: {hero.id} did not wait for fear to vanish before moving.")

    world.para()
    if goal.id == "message":
        world.say(f"At the far side, {hero.id} reached the place where the message was needed.")
        world.say(f"{goal.reward.capitalize()}; {hero.id} was proud, and the creek no longer looked like a wall.")
    elif goal.id == "berries":
        world.say(f"{hero.id} reached the bushes and picked the berries with careful fingers.")
        world.say(f"{goal.reward.capitalize()}, and the bowl looked bright against the grass.")
    else:
        world.say(f"{hero.id} brought the borrowed lantern back, and the cave no longer felt mean or mysterious.")
        world.say(f"{goal.reward.capitalize()}, and the dark seemed smaller on the walk home.")
    world.say(f"{hero.id} looked back once and knew the truth: a portable brave thought can travel anywhere.")

    world.facts.update(hero=hero, guide=guide, tool=tool, goal=goal, success=True)
    return world


def choose_keyed(rng: random.Random, args_value: Optional[str], choices: dict) -> str:
    if args_value is not None:
        if args_value not in choices:
            raise StoryError(f"Unknown choice: {args_value}")
        return args_value
    return rng.choice(list(choices))


@dataclass
class Registry:
    places: dict[str, Place] = field(default_factory=lambda: PLACES)
    tools: dict[str, Tool] = field(default_factory=lambda: TOOLS)
    goals: dict[str, Goal] = field(default_factory=lambda: GOALS)


REGISTRY = Registry()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A portable bravery adventure with inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    place = choose_keyed(rng, args.place, PLACES)
    goal = choose_keyed(rng, args.goal, GOALS)
    tool = choose_keyed(rng, args.tool, TOOLS)
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    if tool == "map" and place == "cave":
        pass
    if tool == "whistle" and goal == "berries":
        pass
    if tool == "coin" and place == "woods":
        pass
    if tool == "lantern" and place in {"woods", "cave", "harbor"}:
        pass
    return StoryParams(place=place, goal=goal, tool=tool, name=name, gender=gender, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["goal"].phrase
    return [
        f'Write a gentle adventure for a young child about {hero.id}, a portable helper, and a brave inner voice.',
        f"Tell a story where {hero.id} has to {place} and learns to be brave one step at a time.",
        f'Write a short adventure that includes the word "portable" and ends with a child feeling brave.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    tool: Entity = f["tool"]
    goal: Goal = f["goal"]
    place: Place = world.place
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to do in {place.label}?",
            answer=f"{hero.id} was trying to {goal.phrase}. The trip took {hero.id} through {place.label}.",
        ),
        QAItem(
            question=f"What portable thing did {hero.id} carry?",
            answer=f"{hero.id} carried {tool.phrase}, a small portable helper that stayed close during the adventure.",
        ),
        QAItem(
            question=f"What changed in {hero.id} during the story?",
            answer=f"{hero.id} started out worried, but by the end {hero.pronoun('subject')} felt braver and kept going.",
        ),
    ]
    if f.get("success"):
        qa.append(QAItem(
            question=f"How did {hero.id} get past the hardest part?",
            answer=f"{hero.id} used {tool.label} and a brave inner voice, then took careful steps until the hard part was behind {hero.pronoun('object')}.",
        ))
        qa.append(QAItem(
            question=f"What did {hero.id} say to {hero.pronoun('object')}self?",
            answer=f"{hero.id} thought that one careful step at a time was enough, and that fear did not have to disappear before moving.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tool: Entity = f["tool"]
    place: Place = world.place
    out = [
        QAItem(
            question="What does portable mean?",
            answer="Portable means easy to carry from one place to another.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice a person hears in their own mind when they think.",
        ),
    ]
    if tool.type == "light":
        out.append(QAItem(
            question="What does a lantern help with?",
            answer="A lantern helps by giving light, so dark places are easier to see.",
        ))
    if tool.type == "direction":
        out.append(QAItem(
            question="What does a map help with?",
            answer="A map helps people find their way and understand where to go.",
        ))
    out.append(QAItem(
        question=f"What kind of place was {place.label}?",
        answer=f"{place.label.capitalize()} was a place with a bit of danger and a small adventure waiting in it.",
    ))
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.portable:
            bits.append("portable=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
tool(T) :- portable_tool(T).
goal(G) :- quest(G).

portable_advantage(T, D) :- portable_tool(T), helps_against(T, D).
brave_plan(P, T, G) :- setting(P), portable_tool(T), quest(G), matches(P, T, G).
safe_finish(P, T, G) :- brave_plan(P, T, G), portable_advantage(T, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for d in p.danger.split():
            lines.append(asp.fact("danger_word", pid, d.strip(".,;:!?")))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("portable_tool", tid))
        lines.append(asp.fact("tool_kind", tid, t.kind))
        for k in sorted(t.helps_against):
            lines.append(asp.fact("helps_against", tid, k))
    for gid, g in GOALS.items():
        lines.append(asp.fact("quest", gid))
    for pid, p in PLACES.items():
        for tid, t in TOOLS.items():
            for gid, g in GOALS.items():
                if any(word in p.danger for word in t.helps_against):
                    lines.append(asp.fact("matches", pid, tid, gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show safe_finish/3."))
    atoms = sorted(set(asp.atoms(model, "safe_finish")))
    py = sorted(
        (pid, tid, gid)
        for pid, p in PLACES.items()
        for tid, t in TOOLS.items()
        for gid, g in GOALS.items()
        if any(word in p.danger for word in t.helps_against)
    )
    if atoms == py:
        print(f"OK: ASP matches Python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("ASP:", atoms)
    print("PY :", py)
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, p in PLACES.items():
        for tid, t in TOOLS.items():
            for gid, g in GOALS.items():
                if any(word in p.danger for word in t.helps_against):
                    combos.append((pid, tid, gid))
    return combos


CURATED = [
    StoryParams(place="woods", goal="message", tool="lantern", name="Mia", gender="girl", trait="curious"),
    StoryParams(place="cave", goal="lantern", tool="lantern", name="Leo", gender="boy", trait="quiet"),
    StoryParams(place="hill", goal="berries", tool="map", name="Ava", gender="girl", trait="spirited"),
    StoryParams(place="harbor", goal="message", tool="whistle", name="Finn", gender="boy", trait="stubborn"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], GOALS[params.goal], TOOLS[params.tool], params.name, params.gender, params.trait)
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
        print(asp_program("#show safe_finish/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as e:
            print(f"ASP unavailable: {e}")
            return
        model = asp.one_model(asp_program("#show safe_finish/3."))
        triples = sorted(set(asp.atoms(model, "safe_finish")))
        print(f"{len(triples)} safe combinations:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.goal} with {p.tool} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
