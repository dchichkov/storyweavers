#!/usr/bin/env python3
"""
Storyworld: chipmunk detective on a continent quest.

A small, self-contained story simulation in the style of a child-facing
detective story. A chipmunk follows clues across a continent on a quest that
tests moral value: whether to tell the truth, share credit, and help others
instead of taking the easy shortcut.

The world model tracks physical state in meters and emotional state in memes.
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
    caretaker: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"chipmunk", "detective"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Continent:
    name: str
    clue_trail: list[str]
    places: list[str]
    weather: str = "clear"


@dataclass
class Quest:
    id: str
    title: str
    goal: str
    moral_value: str
    honest_path: str
    shortcut: str
    clue_key: str
    reward: str


@dataclass
class StoryParams:
    continent: str
    quest: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, continent: Continent, quest: Quest) -> None:
        self.continent = continent
        self.quest = quest
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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
        w = World(self.continent, self.quest)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


def build_continents() -> dict[str, Continent]:
    return {
        "northland": Continent(
            name="Northland",
            clue_trail=["pine needles", "boot prints", "a torn map corner"],
            places=["mossy bridge", "foggy hill", "quiet station"],
            weather="misty",
        ),
        "sunshore": Continent(
            name="Sunshore",
            clue_trail=["salt dust", "a shell token", "a blue ribbon"],
            places=["harbor path", "sand lane", "lighthouse steps"],
            weather="bright",
        ),
        "greenplate": Continent(
            name="Greenplate",
            clue_trail=["leaf ink", "mud marks", "a lantern note"],
            places=["forest road", "market square", "river dock"],
            weather="soft rain",
        ),
    }


def build_quests() -> dict[str, Quest]:
    return {
        "lostkey": Quest(
            id="lostkey",
            title="The Lost Key",
            goal="find the missing key to the old map room",
            moral_value="tell the truth about where the key was found",
            honest_path="return the key to its owner",
            shortcut="keep the key and claim the credit",
            clue_key="key",
            reward="the town's thanks",
        ),
        "stolencake": Quest(
            id="stolencake",
            title="The Missing Cake",
            goal="learn who took the mayor's cake",
            moral_value="share the clue with the baker instead of hiding it",
            honest_path="show the baker the evidence",
            shortcut="blame a stranger to end the case quickly",
            clue_key="crumbs",
            reward="a warm apology and a full table",
        ),
        "bridgebell": Quest(
            id="bridgebell",
            title="The Quiet Bell",
            goal="find the bell that vanished from the bridge",
            moral_value="help the bridge keeper even when nobody is watching",
            honest_path="bring the bell back at once",
            shortcut="pretend the bell was never there",
            clue_key="bell",
            reward="a bright ring across the water",
        ),
    }


def clue_for(quest: Quest, continent: Continent) -> str:
    return {
        "key": continent.clue_trail[2],
        "crumbs": continent.clue_trail[0],
        "bell": continent.clue_trail[1],
    }[quest.clue_key]


def reasonableness_gate(continent: Continent, quest: Quest) -> None:
    if quest.clue_key not in {"key", "crumbs", "bell"}:
        raise StoryError("This quest has no usable clue trail.")
    if not continent.places:
        raise StoryError("This continent has nowhere to search.")
    if not quest.moral_value or not quest.honest_path:
        raise StoryError("The quest needs a moral value and an honest path.")


def setup_world(params: StoryParams) -> World:
    continents = build_continents()
    quests = build_quests()
    if params.continent not in continents:
        raise StoryError("Unknown continent.")
    if params.quest not in quests:
        raise StoryError("Unknown quest.")
    continent = continents[params.continent]
    quest = quests[params.quest]
    reasonableness_gate(continent, quest)
    world = World(continent, quest)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="chipmunk",
        label=params.name,
        location=continent.name,
        meters={"distance": 0.0},
        memes={"curiosity": 2.0, "doubt": 0.0, "resolve": 1.0, "trust": 1.0, "pride": 0.0},
    ))
    mentor = world.add(Entity(
        id="Detective Sage",
        kind="character",
        type="detective",
        label="Detective Sage",
        location=continent.places[0],
        meters={},
        memes={"calm": 2.0, "wisdom": 2.0},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue_for(quest, continent),
        phrase=f"a small clue about the {quest.goal}",
        location=continent.places[0],
        meters={"travel": 0.0},
    ))
    reward = world.add(Entity(
        id="reward",
        kind="thing",
        type="reward",
        label=quest.reward,
        phrase=quest.reward,
        location=continent.places[-1],
    ))
    world.facts.update(hero=hero, mentor=mentor, clue=clue, reward=reward)
    return world


def intro(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    world.say(
        f"{hero.label} was a small chipmunk detective with bright eyes and quick paws."
    )
    world.say(
        f"On {world.continent.name}, {hero.label} loved a good case, especially one with a moral value to prove."
    )


def begin_case(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    mentor: Entity = world.facts["mentor"]  # type: ignore[assignment]
    quest = world.quest
    world.para()
    world.say(
        f"One clear morning, Detective Sage gave {hero.label} a quest: {quest.goal}."
    )
    world.say(
        f"The first clue was tied to {world.continent.places[0]}, so {hero.label} followed it carefully."
    )
    hero.meters["distance"] += 1.0
    hero.memes["resolve"] += 1.0
    mentor.memes["calm"] += 1.0


def discover_temptation(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    quest = world.quest
    clue: Entity = world.facts["clue"]  # type: ignore[assignment]
    world.para()
    world.say(
        f"At the end of the trail, {hero.label} found {clue.label} and a perfect shortcut."
    )
    world.say(
        f"It would have been easy to take the clue home, hide it, and claim the credit."
    )
    hero.memes["doubt"] += 1.0
    hero.memes["pride"] += 1.0
    world.facts["temptation"] = quest.shortcut


def moral_turn(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    mentor: Entity = world.facts["mentor"]  # type: ignore[assignment]
    clue: Entity = world.facts["clue"]  # type: ignore[assignment]
    quest = world.quest
    world.say(
        f"But {hero.label} remembered the moral value of the case: {quest.moral_value}."
    )
    world.say(
        f"Detective Sage had said, “A real detective does not win by being sneaky.”"
    )
    hero.memes["trust"] += 1.0
    hero.memes["doubt"] = max(0.0, hero.memes["doubt"] - 1.0)
    mentor.memes["wisdom"] += 1.0
    world.facts["honest_choice"] = quest.honest_path
    clue.location = world.continent.places[1]


def resolve_case(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    clue: Entity = world.facts["clue"]  # type: ignore[assignment]
    reward: Entity = world.facts["reward"]  # type: ignore[assignment]
    mentor: Entity = world.facts["mentor"]  # type: ignore[assignment]
    quest = world.quest
    world.para()
    world.say(
        f"So {hero.label} chose the honest path and {quest.honest_path}."
    )
    world.say(
        f"{hero.label} carried the clue across {world.continent.places[-1]} and showed everyone the truth."
    )
    reward.location = world.continent.places[-1]
    hero.memes["resolve"] += 1.0
    hero.memes["pride"] = max(0.0, hero.memes["pride"] - 1.0)
    mentor.memes["calm"] += 1.0
    world.say(
        f"In the end, {hero.label} did not just solve the case; {hero.pronoun('subject')} proved that moral value mattered more than a fast win."
    )
    world.say(
        f"The final clue fit, the reward was returned, and {hero.label} stood proudly on {world.continent.name} as a true detective."
    )
    world.facts["solved"] = True


def simulate(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    begin_case(world)
    discover_temptation(world)
    moral_turn(world)
    resolve_case(world)
    return world


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, cont in build_continents().items():
        lines.append(asp.fact("continent", cid))
        for place in cont.places:
            lines.append(asp.fact("place", cid, place))
        for clue in cont.clue_trail:
            lines.append(asp.fact("trail", cid, clue))
    for qid, q in build_quests().items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("moral_value", qid, q.moral_value))
        lines.append(asp.fact("honest_path", qid, q.honest_path))
    return "\n".join(lines)


ASP_RULES = r"""
valid(C, Q) :- continent(C), quest(Q).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Chipmunk detective storyworld.")
    ap.add_argument("--continent", choices=sorted(build_continents()))
    ap.add_argument("--quest", choices=sorted(build_quests()))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    conts = sorted(build_continents())
    quests = sorted(build_quests())
    continent = args.continent or rng.choice(conts)
    quest = args.quest or rng.choice(quests)
    name = args.name or rng.choice(["Pip", "Tiko", "Mimi", "Nip", "Coco", "Rin"])
    return StoryParams(continent=continent, quest=quest, name=name)


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    quest = world.quest
    return [
        f"Write a child-friendly detective story about a chipmunk named {hero.label} on {world.continent.name}.",
        f"Tell a short mystery where {hero.label} must solve {quest.title} and choose the honest path.",
        f"Write a story that includes a chipmunk, a continent, a clue, and a moral value.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    quest = world.quest
    clue: Entity = world.facts["clue"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, a small chipmunk detective on {world.continent.name}.",
        ),
        QAItem(
            question=f"What was the quest?",
            answer=f"The quest was to {quest.goal}.",
        ),
        QAItem(
            question=f"What clue did {hero.label} find?",
            answer=f"{hero.label} found {clue.label}, which helped solve the case.",
        ),
        QAItem(
            question=f"What moral value did {hero.label} remember?",
            answer=f"{hero.label} remembered that {quest.moral_value}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.label} choosing the honest path and proving that a true detective tells the truth.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chipmunk?",
            answer="A chipmunk is a small striped squirrel-like animal that can run fast and store food in cheek pouches.",
        ),
        QAItem(
            question="What is a continent?",
            answer="A continent is a very large piece of land on Earth, bigger than a country.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks for clues and solves mysteries.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good choice people try to follow, like telling the truth or helping others.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} location={e.location}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
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
    StoryParams(continent="northland", quest="lostkey", name="Pip"),
    StoryParams(continent="sunshore", quest="stolencake", name="Mimi"),
    StoryParams(continent="greenplate", quest="bridgebell", name="Tiko"),
]


def asp_verify() -> int:
    import asp
    py = {(c, q) for c in build_continents() for q in build_quests()}
    cl = set(asp_valid())
    if cl == py:
        print(f"OK: clingo gate matches Python ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        for c, q in vals:
            print(f"{c} {q}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
