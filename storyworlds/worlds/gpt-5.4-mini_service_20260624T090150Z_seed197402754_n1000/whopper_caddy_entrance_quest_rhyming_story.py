#!/usr/bin/env python3
"""
A small storyworld for a Rhyming Story about a Quest with a whopper and a caddy
near an entrance.

The seed tale that shaped this world:
---
A small fox wanted to begin a quest, but the gate to the garden entrance was
stuck. The fox had a caddy full of clever little tools, and in the caddy there
was a whopper of a key. The fox tried small keys first, but none fit. Then the
fox used the big whopper key, and the entrance opened with a click and a cheer.
The fox went inside, smiling, because the quest could finally begin.
---

This world keeps that premise, tension, turn, and resolution in a compact,
child-friendly rhyme.
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
    openable: bool = False
    open_state: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"fox", "boy", "king", "prince"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
            if self.type in {"girl", "queen", "princess"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    rhyme: str
    openable: bool = False


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    power: str
    rhyme: str
    fits: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    verb: str
    rhyme: str
    risk: str
    success: str
    zone: str
    tag: str = "quest"


class World:
    def __init__(self, place: Place, quest: Quest) -> None:
        self.place = place
        self.quest = quest
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.place, self.quest)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.lines = [[]]
        clone.facts = dict(self.facts)
        return clone


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


PLACES = {
    "garden_gate": Place(id="garden_gate", label="the garden gate entrance", rhyme="gate"),
    "castle_arch": Place(id="castle_arch", label="the castle arch entrance", rhyme="arch"),
    "cave_door": Place(id="cave_door", label="the cave door entrance", rhyme="door"),
}

QUESTS = {
    "begin": Quest(
        id="begin",
        goal="begin the quest",
        verb="begin the quest",
        rhyme="quest",
        risk="blocked",
        success="could finally begin",
        zone="entrance",
    ),
    "deliver": Quest(
        id="deliver",
        goal="deliver the whopper",
        verb="deliver the whopper",
        rhyme="whopper",
        risk="stuck",
        success="could be delivered at last",
        zone="entrance",
    ),
}

TOOLS = {
    "tiny_key": Tool(
        id="tiny_key",
        label="tiny key",
        phrase="a tiny key",
        power="small",
        rhyme="key",
        fits={"lock"},
    ),
    "caddy": Tool(
        id="caddy",
        label="caddy",
        phrase="a caddy full of clever tools",
        power="carry",
        rhyme="caddy",
        fits={"key", "tool"},
    ),
    "whopper_key": Tool(
        id="whopper_key",
        label="whopper key",
        phrase="a whopper key",
        power="big",
        rhyme="whopper",
        fits={"lock"},
    ),
}

HEROES = {
    "fox": ("little fox", "fox"),
    "girl": ("little girl", "girl"),
    "boy": ("little boy", "boy"),
}

NAMES = {
    "fox": ["Pip", "Taz", "Milo", "Fenn"],
    "girl": ["Luna", "Nia", "Mina", "Zoe"],
    "boy": ["Finn", "Owen", "Toby", "Ben"],
}


@dataclass
class StoryParams:
    place: str
    quest: str
    hero_type: str
    name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small Rhyming Story quest world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hero-type", choices=HEROES)
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for quest in QUESTS:
            for hero_type in HEROES:
                combos.append((place, quest, hero_type))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.hero_type:
        combos = [c for c in combos if c[2] == args.hero_type]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, quest, hero_type = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES[hero_type])
    return StoryParams(place=place, quest=quest, hero_type=hero_type, name=name)


def _choose_tool_for_quest(quest: Quest) -> Tool:
    return TOOLS["whopper_key"]


def predict_opening(world: World, hero: Entity, tool: Entity) -> bool:
    sim = world.copy()
    gate = sim.get("entrance")
    if tool.id == "whopper_key":
        gate.open_state = True
        return True
    return False


def tell(place: Place, quest: Quest, hero_type: str, name: str) -> World:
    world = World(place, quest)
    hero = world.add(Entity(id=name, kind="character", type=hero_type, label=name))
    caddy = world.add(Entity(id="caddy", type="caddy", label="caddy", phrase="a caddy", owner=hero.id))
    entrance = world.add(Entity(
        id="entrance",
        type="entrance",
        label=place.label,
        phrase=place.label,
        openable=True,
        open_state=False,
    ))
    tiny = world.add(Entity(id="tiny_key", type="key", label="tiny key", phrase="a tiny key", owner=caddy.id, carried_by=hero.id))
    whopper = world.add(Entity(id="whopper_key", type="key", label="whopper key", phrase="a whopper key", owner=caddy.id, carried_by=hero.id))
    world.facts.update(hero=hero, caddy=caddy, entrance=entrance, tiny=tiny, whopper=whopper, quest=quest, place=place)

    world.say(
        f"{name} was a little {hero_type} with a caddy by the way, "
        f"ready for a quest to start."
    )
    world.say(
        f"At {place.label}, the entrance stood tight and neat; "
        f"{name} wanted to {quest.goal}, but the way would not meet."
    )
    world.para()
    world.say(
        f"{name} tried a tiny key first, light as a bee, "
        f"but the entrance stayed shut with a stubborn decree."
    )
    world.say(
        f"The caddy held a whopper, big and bright and bold; "
        f"{name} knew that strong old key might open the fold."
    )
    world.para()
    tool = world.get("whopper_key")
    if predict_opening(world, hero, tool):
        entrance.open_state = True
        world.say(
            f"{name} turned the whopper key, click went the latch, "
            f"and the entrance swung open with a cheery small snatch."
        )
        world.say(
            f"So {name} stepped inside, with a grin and a hop; "
            f"the quest could begin, and the worry could stop."
        )
    else:
        raise StoryError("The story world could not find a believable way to open the entrance.")
    world.facts["resolved"] = entrance.open_state
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    quest = f["quest"]
    return [
        f"Write a short rhyming story about {hero.id}, a caddy, and an entrance at {place.label}.",
        f"Tell a gentle quest story where {hero.id} wants to {quest.goal} but must find the right key.",
        f"Write a child-friendly rhyming tale with the words whopper, caddy, and entrance.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    quest: Quest = f["quest"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who went on the quest at {place.label}?",
            answer=f"{hero.id} went on the quest at {place.label}.",
        ),
        QAItem(
            question="What did the caddy carry that mattered most?",
            answer="The caddy carried a whopper key that could open the entrance.",
        ),
        QAItem(
            question=f"What happened when {hero.id} used the whopper key?",
            answer=f"The entrance opened, and {hero.id} could begin the quest.",
        ),
        QAItem(
            question=f"Why did the tiny key not solve the problem?",
            answer="The tiny key was too small to open the stubborn entrance.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a caddy?",
            answer="A caddy is something that carries or holds tools and other small things.",
        ),
        QAItem(
            question="What is an entrance?",
            answer="An entrance is a place where you go in, like a gate, door, or opening.",
        ),
        QAItem(
            question="What does whopper mean here?",
            answer="Whopper means very big or very large in this story.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or mission to reach a goal or find something important.",
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
        bits = []
        if e.openable:
            bits.append(f"open={e.open_state}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
openable(entrance).
quest(begin).
quest(deliver).
tool(tiny_key).
tool(whopper_key).
tool(caddy).

fits(tiny_key, lock).
fits(whopper_key, lock).
holds(caddy, tiny_key).
holds(caddy, whopper_key).
entrance_needs(entrance, lock).

can_open(T, E) :- tool(T), openable(E), entrance_needs(E, lock), fits(T, lock).
good_choice(caddy, whopper_key) :- holds(caddy, whopper_key).
valid_story(P, Q, H) :- place(P), quest(Q), hero(H).
#show can_open/2.
#show good_choice/2.
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("entrance", place.id))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    lines.append(asp.fact("openable", "entrance"))
    lines.append(asp.fact("entrance_needs", "entrance", "lock"))
    lines.append(asp.fact("holds", "caddy", "tiny_key"))
    lines.append(asp.fact("holds", "caddy", "whopper_key"))
    lines.append(asp.fact("fits", "tiny_key", "lock"))
    lines.append(asp.fact("fits", "whopper_key", "lock"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_open/2.\n#show good_choice/2."))
    atoms = set(asp.atoms(model, "can_open"))
    expected = {("whopper_key", "entrance"), ("tiny_key", "entrance")}
    if atoms != expected:
        print("MISMATCH between ASP and expected tool-opening facts.")
        print("  ASP:", sorted(atoms))
        print("  Expected:", sorted(expected))
        return 1
    print("OK: ASP gate is consistent for opening the entrance.")
    return 0


CURATED = [
    StoryParams(place="garden_gate", quest="begin", hero_type="fox", name="Pip"),
    StoryParams(place="castle_arch", quest="deliver", hero_type="girl", name="Luna"),
    StoryParams(place="cave_door", quest="begin", hero_type="boy", name="Finn"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], QUESTS[params.quest], params.hero_type, params.name)
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
        print(asp_program("#show can_open/2.\n#show good_choice/2.\n#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show can_open/2.\n#show good_choice/2."))
        print("ASP model:")
        for atom in model:
            print(atom)
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.quest} at {p.place} ({p.hero_type})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
