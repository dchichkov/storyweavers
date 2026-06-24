#!/usr/bin/env python3
"""
storyworlds/worlds/chump_queer_proper_inner_monologue_quest_adventure.py
========================================================================

A small adventure storyworld about a chump who thinks a quest is impossible,
then discovers a proper way through after an inner monologue and a helper's
nudge. The setting is a little trail-world: a map, a gate, a key, and a place
that only opens for a careful, honest plan.

This world keeps the classic story shape:
- premise: a chump wants a quest prize
- tension: the path is blocked and the chump feels silly / queer / out of place
- turn: inner monologue changes the plan
- resolution: a proper action solves the quest

The story uses typed entities with meters and memes, a reasonableness gate, a
Python/ASP twin, and grounded QA.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        gender = self.attrs.get("gender", "")
        if gender == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    afford: set[str] = field(default_factory=set)
    mood: str = ""


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    risk: str
    solved_by: str
    tags: set[str] = field(default_factory=set)


@dataclass
class InnerThought:
    id: str
    label: str
    trigger: str
    turn: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for quest_id, quest in QUESTS.items():
            if quest.risk in place.afford:
                for thought_id in THOUGHTS:
                    combos.append((place_id, quest_id, thought_id))
    return combos


@dataclass
class StoryParams:
    place: str
    quest: str
    thought: str
    hero: str
    gender: str
    helper: str
    seed: Optional[int] = None


HEROES = {"boy": ["Pip", "Otto", "Finn", "Milo"], "girl": ["Ada", "Nia", "Luna", "Maya"]}
HELPERS = ["the fox", "the crow", "the old guide", "the squirrel"]

PLACES = {
    "bridge": Place(id="bridge", label="the bridge", afford={"gap"}, mood="windy"),
    "grove": Place(id="grove", label="the grove", afford={"riddle", "gap"}, mood="quiet"),
    "cave": Place(id="cave", label="the cave mouth", afford={"dark", "gap"}, mood="echoing"),
}

QUESTS = {
    "key": QuestItem(id="key", label="a brass key", phrase="a little brass key", risk="gap", solved_by="proper plan", tags={"key", "quest"}),
    "lantern": QuestItem(id="lantern", label="a lantern", phrase="a lantern with a blue handle", risk="dark", solved_by="proper light", tags={"lantern", "quest"}),
    "riddle_stone": QuestItem(id="riddle_stone", label="a riddle stone", phrase="a stone with a riddle on it", risk="riddle", solved_by="proper words", tags={"riddle", "quest"}),
}

THOUGHTS = {
    "chump": InnerThought(id="chump", label="chump", trigger="feeling like a chump", turn="remembering that a chump can still be brave", tags={"chump"}),
    "queer": InnerThought(id="queer", label="queer", trigger="feeling queer and out of place", turn="realizing that queer could mean unusual, and unusual could still be proper", tags={"queer"}),
    "proper": InnerThought(id="proper", label="proper", trigger="wanting to do it the proper way", turn="choosing a careful plan instead of a rushed one", tags={"proper"}),
}


def story_prompt_words() -> list[str]:
    return ["chump", "queer", "proper", "Inner Monologue", "Quest"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: a chump, an inner monologue, and a quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--thought", choices=THOUGHTS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["boy", "girl", "they"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.thought is None or c[2] == args.thought)]
    if not combos:
        raise StoryError("No valid quest matches the chosen filters.")
    place, quest, thought = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["boy", "girl", "they"])
    hero = args.hero or rng.choice(HEROES.get(gender, HEROES["boy"] + HEROES["girl"]))
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, quest=quest, thought=thought, hero=hero, gender=gender, helper=helper)


def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    thought = THOUGHTS[params.thought]
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type="child", label=params.hero, attrs={"gender": params.gender}))
    helper = world.add(Entity(id="helper", kind="character", type="helper", label=params.helper))
    item = world.add(Entity(id="item", type="quest", label=quest.label, attrs={"phrase": quest.phrase}, tags=set(quest.tags)))
    gate = world.add(Entity(id="gate", type="thing", label=f"the blocked way at {place.label}", meters={"blocked": 1.0}, tags={"gate"}))
    hero.meters["travel"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["hope"] = 0.0
    hero.memes["resolve"] = 0.0
    helper.memes["steadiness"] = 1.0
    world.facts.update(hero=hero, helper=helper, item=item, gate=gate, quest=quest, thought=thought, place=place)
    world.say(f"{params.hero} stood at {place.label} with a quest in mind.")
    world.say(f"{params.hero} wanted {quest.phrase}, but {place.label} hid a blocked way.")
    world.para()
    hero.memes["worry"] += 1.0
    world.say(f"In {params.hero}'s head, an inner monologue began: first {thought.trigger}.")
    world.say(f"Then the thought turned: {thought.turn}.")
    hero.memes["resolve"] += 1.0
    hero.memes["hope"] += 1.0
    gate.meters["blocked"] = 0.0
    hero.meters["travel"] += 1.0
    world.para()
    world.say(f"{helper} pointed to a proper way through, and {params.hero} tried it step by step.")
    world.say(f"That careful path reached {quest.label}, so {params.hero} took it home like treasure.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].label
    item = f["item"].label
    place = f["place"].label
    thought = f["thought"].label
    return [
        f'Write an adventure story for a young child about {hero}, a quest, and the word "{thought}".',
        f"Tell a gentle quest story where {hero} feels like a {thought} but finds a proper way through {place} to get {item}.",
        f'Write a short story that includes "Inner Monologue" and "Quest" and ends with {hero} reaching the prize.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    helper = f["helper"].label
    quest = f["quest"]
    thought = f["thought"]
    place = f["place"].label
    return [
        QAItem(question=f"What did {hero} want at {place}?", answer=f"{hero} wanted {quest.phrase}."),
        QAItem(question=f"What did the inner monologue change for {hero}?", answer=f"It changed {hero}'s plan from worry to a proper way forward."),
        QAItem(question=f"Who helped {hero} through the blocked way?", answer=f"{helper} helped by pointing out a careful route."),
        QAItem(question=f"Why is the story called a quest?", answer=f"Because {hero} was trying to reach a prize and had to solve a problem along the way."),
        QAItem(question=f"What did the word {thought.label} mean in the story?", answer=f"It was the feeling and idea that shaped {hero}'s thinking before {hero} chose a better plan."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(question="What is a quest?", answer="A quest is a journey to find something important or solve a problem."),
        QAItem(question="What is an inner monologue?", answer="An inner monologue is the voice of thoughts in a character's head."),
        QAItem(question="What does proper mean?", answer="Proper means right, careful, or suitable for the situation."),
    ]
    f = world.facts
    if f["thought"].label == "queer":
        out.append(QAItem(question="What can queer mean?", answer="Here it means unusual or different, not wrong, just a little surprising."))
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: label={e.label!r} meters={e.meters} memes={e.memes} attrs={e.attrs}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Q, T) :- place(P), quest(Q), thought(T), risk(Q, R), affords(P, R).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.afford):
            lines.append(asp.fact("affords", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("risk", qid, q.risk))
    for tid in THOUGHTS:
        lines.append(asp.fact("thought", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    return 0 if set(asp_valid_combos()) == set(valid_combos()) else 1


CURATED = [
    StoryParams(place="bridge", quest="key", thought="chump", hero="Pip", gender="boy", helper="the fox"),
    StoryParams(place="grove", quest="riddle_stone", thought="queer", hero="Ada", gender="girl", helper="the old guide"),
    StoryParams(place="cave", quest="lantern", thought="proper", hero="Milo", gender="boy", helper="the crow"),
]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        print("\n== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()
