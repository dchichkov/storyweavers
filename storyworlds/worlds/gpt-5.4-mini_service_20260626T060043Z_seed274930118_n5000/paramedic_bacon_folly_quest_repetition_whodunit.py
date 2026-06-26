#!/usr/bin/env python3
"""
A standalone story world about a whodunit at a small roadside diner, where a
paramedic's quest to untangle a bacon-related folly is tested by repetition.

The world is deliberately small: one setting, a few typed entities, a simple
state machine, and a mystery-shaped turn that resolves through evidence rather
than coincidence.
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
    kind: str
    type: str
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    clues: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father", "paramedic"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    shadows: bool = False
    serves: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero: str
    culprit: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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


PARAMEDICS = {
    "Ava": "woman",
    "Milo": "man",
    "Nina": "woman",
    "Owen": "man",
    "Iris": "woman",
    "Theo": "man",
}
CULPRITS = {
    "chef": "man",
    "waitress": "woman",
    "kid": "boy",
    "driver": "man",
}
PLACES = {
    "diner": Place(id="diner", label="the roadside diner", shadows=True, serves={"bacon"}),
    "clinic": Place(id="clinic", label="the small clinic", shadows=False, serves=set()),
}
NAMES = ["Ava", "Milo", "Nina", "Owen", "Iris", "Theo"]
CULPRIT_NAMES = ["Chef Carl", "Wendy", "Ben", "Dale", "Rita", "Finn"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world: a paramedic, bacon, and a folly.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--culprit")
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
    place = args.place or "diner"
    hero = args.hero or rng.choice(NAMES)
    culprit = args.culprit or rng.choice(CULPRIT_NAMES)
    return StoryParams(place=place, hero=hero, culprit=culprit)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hero_gender = PARAMEDICS.get(params.hero, "woman")
    hero = world.add(Entity(id=params.hero, kind="character", type="paramedic", label="the paramedic"))
    suspect = world.add(Entity(id="suspect", kind="character", type="culprit", label=params.culprit))
    bacon = world.add(Entity(id="bacon", kind="thing", type="food", label="bacon", phrase="a plate of bacon", plural=True))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label="grease mark", phrase="a greasy clue"))

    hero.memes["duty"] = 1
    hero.memes["curiosity"] = 1
    hero.memes["quest"] = 1
    suspect.memes["nervous"] = 1
    bacon.meters["smell"] = 1

    world.say(f"{hero.id} was a paramedic with a sharp eye and a steady hand.")
    world.say(f"{hero.pronoun().capitalize()} came to {place.label} on a quiet quest to learn who had caused the trouble.")
    world.say(f"The trouble smelled like bacon, and the smell made the whole room feel like a secret.")

    world.para()
    world.say(f"At first, the case looked simple. {suspect.id} kept repeating the same story: 'I was here, I was here, I was here.'")
    world.say("But the repetition sounded too neat, like a spoon tapping the same cup over and over.")

    world.para()
    clue.clues.append("bacon grease on the counter")
    hero.clues.append("bacon grease on the counter")
    hero.clues.append("a napkin folded in a hurry")
    world.say(f"{hero.id} leaned closer and saw a greasy clue on the counter, right where the bacon had been served.")
    world.say(f"Then {hero.pronoun()} noticed that {suspect.id}'s apron had one clean pocket and one pocket stained with the same shine.")

    world.para()
    if place.shadows:
        world.say(f"The diner was shadowy, so {hero.id} had to ask the same questions again and again to hear the small changes.")
    world.say(f"On the third round of questions, the story finally cracked.")
    world.say(f"{suspect.id} admitted the folly: {suspect.pronoun().capitalize()} had tried to hide the bacon, slipped on the grease, and knocked the tray into the sink.")
    world.say(f"{hero.id} did not smile at the mistake; {hero.pronoun()} simply named the answer, cleaned the scene, and wrote down the truth.")

    world.para()
    world.say(f"In the end, the quest was solved by patience, not luck.")
    world.say(f"The bacon was counted, the folly was admitted, and the same repeated tale turned into a clear whodunit answer.")
    world.facts.update(hero=hero, suspect=suspect, bacon=bacon, clue=clue, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short whodunit story about a paramedic who follows a quest to solve a bacon mystery.",
        f"Tell a mystery tale where {f['hero'].id} keeps hearing repetition before the truth about {f['place'].label} comes out.",
        "Write a child-friendly mystery about bacon, a foolish mistake, and a careful helper who finds the answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    suspect = f["suspect"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was trying to solve the mystery in {place.label}?",
            answer=f"{hero.id} was trying to solve it. {hero.id} was the paramedic on a quest to learn the truth.",
        ),
        QAItem(
            question="What made the story feel like a whodunit?",
            answer="The repeated story, the greasy clue, and the hidden mistake made it feel like a whodunit.",
        ),
        QAItem(
            question=f"Who admitted the folly at the end?",
            answer=f"{suspect.id} admitted the folly and told the truth about what happened to the bacon.",
        ),
        QAItem(
            question="What helped the paramedic find the answer?",
            answer="Patience helped the paramedic find the answer, along with the greasy clue and the repeated questions.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a paramedic do?",
            answer="A paramedic helps people in medical emergencies and can stay calm in stressful moments.",
        ),
        QAItem(
            question="What is bacon?",
            answer="Bacon is a salty meat that is often cooked in strips and can smell very strong.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means saying or doing the same thing more than once.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the reader tries to figure out who caused the problem.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.clues:
            bits.append(f"clues={e.clues}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- paramedic(H).
mystery(M) :- bacon(M).
repeat_story(S) :- repetition(S).
whodunit(S) :- hero(H), mystery(M), repeat_story(S).
solved(S) :- whodunit(S), clue(C), truth(T).
#show whodunit/1.
#show solved/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("paramedic", "hero"),
        asp.fact("bacon", "mystery"),
        asp.fact("repetition", "repeat"),
        asp.fact("clue", "clue"),
        asp.fact("truth", "truth"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    atoms = {(a.name, len(a.arguments)) for a in model}
    ok = ("whodunit", 1) in atoms and ("solved", 1) in atoms
    if ok:
        print("OK: ASP rules produce whodunit and solved.")
        return 0
    print("MISMATCH: ASP reasoning did not produce expected atoms.")
    return 1


def asp_list() -> None:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    print(" ".join(str(a) for a in model))


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_list()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        seeds = [1, 2, 3, 4, 5]
        for i, s in enumerate(seeds):
            params = StoryParams(place="diner", hero=NAMES[i % len(NAMES)], culprit=CULPRIT_NAMES[i % len(CULPRIT_NAMES)], seed=s)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
