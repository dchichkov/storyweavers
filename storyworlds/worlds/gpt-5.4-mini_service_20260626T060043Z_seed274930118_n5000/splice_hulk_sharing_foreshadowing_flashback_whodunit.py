#!/usr/bin/env python3
"""
A standalone storyworld: a small whodunit about a shared treat, a missing clue,
and a gentle resolution.

Seed premise:
- A child notices something missing.
- A helper remembers a past moment.
- A mistaken suspicion turns into a fair solution through sharing.

Narrative instruments:
- foreshadowing: small early clues point toward the answer
- flashback: a remembered earlier moment explains a later fact
- sharing: the ending resolves through splitting or lending
- whodunit tone: a mystery is posed, investigated, and solved

This world intentionally keeps the setting compact and the causal chain tight so
the story reads like a complete tiny mystery rather than a frozen template.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    holder: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str = "library"
    hero: str = "Mina"
    helper: str = "Owen"
    suspect: str = "Tess"
    treasure: str = "cookie box"
    clue: str = "crumbs"
    seed: Optional[int] = None


PLACES = {
    "library": "the little library corner",
    "kitchen": "the sunny kitchen",
    "classroom": "the classroom",
}

HEROES = ["Mina", "Nico", "Luna", "Ari", "Tessa", "Juno"]
HELPERS = ["Owen", "Pia", "Milo", "Ivy", "Noah", "Ruby"]
SUSPECTS = ["Tess", "Bea", "Leo", "Finn", "Mira", "June"]

TREASURES = {
    "cookie box": {
        "label": "cookie box",
        "phrase": "a small cookie box",
        "split": "spliced into two neat halves",
        "share": "split the cookies",
        "mystery": "the box was nearly empty",
        "at_risk": "the treats were missing",
    },
    "crayon tin": {
        "label": "crayon tin",
        "phrase": "a shiny crayon tin",
        "split": "spliced into tidy rows",
        "share": "share the crayons",
        "mystery": "the red crayon was gone",
        "at_risk": "the colors looked mixed up",
    },
    "sandwich": {
        "label": "sandwich",
        "phrase": "a soft sandwich",
        "split": "spliced down the middle",
        "share": "share the sandwich",
        "mystery": "one half had vanished",
        "at_risk": "the plate looked too neat",
    },
}

CLUES = {
    "crumbs": "tiny crumbs on the table",
    "red dust": "a dusting of red color on a sleeve",
    "napkin": "a folded napkin with a bite mark",
}

SETTING_LINES = {
    "library": "The little library corner was quiet, with a low table, a rug, and a lamp like a moon.",
    "kitchen": "The sunny kitchen smelled warm, and a small table stood near the window.",
    "classroom": "The classroom was calm after snack time, with paper stars on the wall.",
}


# ---------------------------------------------------------------------------
# ASP twin and gates
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A treasure is at risk if it is held in a place where the clue appears.
at_risk(T) :- treasure(T), clue_matches(T).

% A fair fix exists if the child can share the treasure after the mystery is solved.
has_fix(T) :- treasure(T), shareable(T).

valid_story(P, T) :- place(P), treasure(T), at_risk(T), has_fix(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TREASURES:
        lines.append(asp.fact("treasure", t))
        lines.append(asp.fact("shareable", t))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for treasure in TREASURES:
            combos.append((place, treasure))
    return combos


def explain_rejection(place: str, treasure: str) -> str:
    return f"(No story: the mystery at {place} does not fit the clue pattern for {treasure}.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
class Story:
    def __init__(self, params: StoryParams):
        self.params = params
        self.world = World(place=params.place)
        self.hero = self.world.add(Entity(id=params.hero, kind="character", type="girl"))
        self.helper = self.world.add(Entity(id=params.helper, kind="character", type="boy"))
        self.suspect = self.world.add(Entity(id=params.suspect, kind="character", type="girl"))
        self.treasure = self.world.add(Entity(
            id=params.treasure,
            type="thing",
            label=params.treasure,
            phrase=TREASURES[params.treasure]["phrase"],
            owner=self.hero.id,
            holder=self.hero.id,
        ))
        self.clue = params.clue
        self.world.facts.update(
            hero=self.hero,
            helper=self.helper,
            suspect=self.suspect,
            treasure=self.treasure,
            clue=self.clue,
            place=params.place,
        )

    def intro(self) -> None:
        w = self.world
        w.say(f"{self.hero.id} was a careful little child who noticed when little things did not add up.")
        w.say(f"{self.helper.id} liked solving puzzles, and {self.suspect.id} always seemed to know a secret.")
        w.say(SETTING_LINES[self.params.place])

    def setup_mystery(self) -> None:
        w = self.world
        treasure_info = TREASURES[self.params.treasure]
        w.para()
        w.say(f"One day, {self.hero.id} found {treasure_info['mystery']} and froze in surprise.")
        w.say(f"Near the table, there were {CLUES[self.params.clue]}; that was the first clue.")
        w.say(f"{self.hero.id} wondered who had taken a bite, a color, or a piece.")

    def flashback(self) -> None:
        w = self.world
        w.para()
        w.say(f"Then {self.helper.id} had a flashback.")
        w.say(
            f"Earlier, {self.suspect.id} had asked to {TREASURES[self.params.treasure]['share']} "
            f"and had carefully {TREASURES[self.params.treasure]['split']} for everyone."
        )
        w.say(f"That memory made {self.helper.id} look back at the clue again.")

    def investigate(self) -> None:
        w = self.world
        w.para()
        w.say(f"{self.hero.id} and {self.helper.id} followed the clue with tiny steps and quiet eyes.")
        w.say(f"The crumbs pointed to the table, and the table pointed to {self.suspect.id}.")
        w.say(
            f"But when they asked gently, {self.suspect.id} did not look guilty at all; "
            f"{self.suspect.id} looked worried."
        )
        w.say(f"{self.suspect.id} admitted {self.params.treasure} had been shared earlier, but only one piece was left.")
        w.facts["foreshadowed"] = True

    def solve(self) -> None:
        w = self.world
        w.para()
        w.say(
            f"At last, {self.hero.id} understood the trick: no one had stolen anything; "
            f"the shared treat had simply been eaten in pieces."
        )
        w.say(
            f"{self.hero.id} chose a fair ending and asked everyone to {TREASURES[self.params.treasure]['share']} "
            f"the last piece together."
        )
        w.say(
            f"So the mystery closed with a smile, and the once-missing {self.params.treasure} "
            f"was no longer a problem."
        )
        self.world.facts["solved"] = True

    def story(self) -> str:
        self.intro()
        self.setup_mystery()
        self.flashback()
        self.investigate()
        self.solve()
        return self.world.render()


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["place"]
    t = world.facts["treasure"].label
    return [
        f"Write a short whodunit for a young child set in {p} where a shared {t} seems to go missing.",
        f"Tell a gentle mystery story that includes a flashback, a clue, and a fair sharing ending.",
        f"Write a simple detective story where {world.facts['hero'].id} uses a clue to solve a small problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    suspect = world.facts["suspect"]
    treasure = world.facts["treasure"].label
    place = world.facts["place"]
    clue = world.facts["clue"]
    return [
        QAItem(
            question=f"What was the mystery in the {place}?",
            answer=f"The mystery was that the {treasure} seemed to be missing, and everyone wondered what happened.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} and {helper.id} solve the mystery?",
            answer=f"They noticed {CLUES[clue]}, which pointed them toward the table and helped them think more carefully.",
        ),
        QAItem(
            question=f"Why was there a flashback in the story?",
            answer=f"{helper.id} remembered an earlier moment when {suspect.id} had asked to share the {treasure}, which explained the clue.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with everyone sharing the last piece fairly, so the little mystery was solved kindly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    treasure = world.facts["treasure"].label
    if treasure == "cookie box":
        return [
            QAItem(
                question="What does sharing mean?",
                answer="Sharing means letting other people use, eat, or enjoy some of what you have too.",
            ),
            QAItem(
                question="What is a clue?",
                answer="A clue is a small piece of information that helps you solve a mystery.",
            ),
        ]
    if treasure == "crayon tin":
        return [
            QAItem(
                question="What is a mystery?",
                answer="A mystery is a question or problem that people try to figure out by looking for clues.",
            ),
            QAItem(
                question="What does a flashback do in a story?",
                answer="A flashback shows something that happened earlier, so readers understand the present better.",
            ),
        ]
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means giving some of something to someone else so everyone can enjoy it.",
        ),
        QAItem(
            question="Why do detectives look at clues?",
            answer="Detectives look at clues because clues help them figure out what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.holder:
            bits.append(f"holder={e.holder}")
        lines.append(f"  {e.id:12} {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    treasure = args.treasure or rng.choice(list(TREASURES))
    if args.place and args.treasure and (place, treasure) not in valid_combos():
        raise StoryError(explain_rejection(place, treasure))
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice([h for h in HELPERS if h != hero])
    suspect = args.suspect or rng.choice([s for s in SUSPECTS if s != hero and s != helper])
    clue = args.clue or rng.choice(list(CLUES))
    return StoryParams(place=place, hero=hero, helper=helper, suspect=suspect, treasure=treasure, clue=clue)


def generate(params: StoryParams) -> StorySample:
    story = Story(params)
    text = story.story()
    return StorySample(
        params=params,
        story=text,
        prompts=generation_prompts(story.world),
        story_qa=story_qa(story.world),
        world_qa=world_knowledge_qa(story.world),
        world=story.world,
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="library", hero="Mina", helper="Owen", suspect="Tess", treasure="cookie box", clue="crumbs"),
    StoryParams(place="kitchen", hero="Nico", helper="Pia", suspect="Bea", treasure="crayon tin", clue="red dust"),
    StoryParams(place="classroom", hero="Luna", helper="Milo", suspect="Finn", treasure="sandwich", clue="napkin"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld about clues, flashbacks, and sharing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--clue", choices=CLUES)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for place, treasure in stories:
            print(f"  {place:10} {treasure}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} in {p.place} with {p.treasure}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
