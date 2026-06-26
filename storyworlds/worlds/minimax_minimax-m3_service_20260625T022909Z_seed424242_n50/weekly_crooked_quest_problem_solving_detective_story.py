#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/weekly_crooked_quest_problem_solving_detective_story.py
=============================================================================================================================

A standalone *story world* sketch in the "Detective Story" style for the tale
of "The Weekly Crooked Quest" -- a tiny, constraint-checked domain about a
young weekend detective who solves a small weekly mystery with the help of a
trusty grown-up, a notebook, and a few clues.

Initial story (used to build a world model):
---
Once upon a time, there was a little boy named Sam who loved solving tiny
mysteries in his quiet town. Every Saturday morning, he would visit the
grand library on Maple Street, borrow a fresh notebook, and start a new
weekly quest.

One Saturday, the town baker, Mr. Perry, came to Sam looking worried. Three
loaves of bread had vanished from the bakery window, and the price sign was
turned crooked. "Can you solve this little case for me?" asked Mr. Perry.
"Please be kind, and please be careful with the clues."

Sam walked to the bakery with his notebook and a bright magnifying glass.
He saw floury footprints on the floor, a crooked sign that had been nudged,
and a torn ribbon near the back door. He wrote each clue in his notebook:
flour, footprints, crooked sign, torn ribbon.

He followed the trail through the alley behind the bakery. There, by a
small green bench, he found a paper bag with a soft bite taken out of one
loaf, and a little round button from a familiar blue coat. Sam thought
hard: who wears a blue coat and likes soft bread? It was Mr. Pipp, the
postman, who always passed the bakery on his rounds.

Sam walked to the post office and found Mr. Pipp trying a new key on the
mailroom door. Sam did not shout. He showed Mr. Pipp the button and the
floury footprints, and asked, very kindly, if the bread could please come
home. Mr. Pipp's face went pink. He had been hungry, and he had meant to
put the bread back. Sam nodded and said they could solve it together.

They carried the loaves back to the bakery. Mr. Perry smiled, set the sign
straight, and gave each of them a warm bun. Sam wrote one last line in his
notebook: "Solved with kindness, and the price sign stood tall again."
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
# (``python storyworlds/worlds/.../weekly_crooked_quest_problem_solving_detective_story.py``).
sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath__file__)))
        if False else
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # detective, baker, postman, parent, notebook, ...
    label: str = ""                # short reference, e.g. "the baker"
    phrase: str = ""               # full noun phrase, e.g. "the round town baker"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    helper_for: Optional[str] = None   # who relies on this detective
    note: str = ""                     # tiny contextual cue, used in prose
    plural: bool = False
    # Two numeric dimensions, treated uniformly (cf. story.py memeplex model).
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "detective", "baker", "postman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Case:
    """A weekly mystery the detective takes on.

    `stolen`     - the noun that has gone missing (loaves of bread, garden tools, ...)
    `crooked`    - the small clue that the place was touched (sign, gate, ribbon, ...)
    `trail`      - the kind of trail left behind (floury footprints, muddy prints, ...)
    `weak_link`  - the soft piece of evidence that points to the kindly culprit
    `culprit`    - the role of the kindly person responsible
    `kind_word`  - what the culprit says when caught ("I was hungry", ...)
    `keyword`    - topic word used in generation prompts
    `tags`       - world-knowledge topics the case touches
    """
    id: str
    stolen: str
    stolen_label: str              # the prize-like thing that vanished
    stolen_plural: bool            # "loaves" -> them
    crooked: str                   # the crooked clue: "the price sign"
    trail: str                     # "floury footprints"
    weak_link: str                 # "a torn ribbon" / "a little round button"
    culprit: str                   # "the postman"
    kind_word: str                 # "I was hungry"
    fix_phrase: str                # how the case is resolved
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    """A piece of detective kit that helps solve the case."""
    id: str
    label: str
    phrase: str
    helps: set[str]                # which clue kinds this tool uncovers


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        self.case: Optional[Case] = None
        # Facts recorded during the screenplay, read back by the Q&A generators.
        self.facts: dict = {}

    # -- entity helpers -----------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    # -- narration helpers --------------------------------------------------
    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        """Throwaway clone used for forward-simulation (prediction)."""
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.case = self.case
        clone.paragraphs = [[]]            # predictions are silent
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_case_open(world: World) -> list[str]:
    """Once the detective hears the case, the worry meter rises."""
    for c in world.characters():
        if c.memes["case_open"] < THRESHOLD:
            continue
        sig = ("case_open", c.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        c.memes["resolve"] += 1
        c.memes["care"] += 1
    return []


def _r_clue_logged(world: World) -> list[str]:
    """Each clue written in the notebook raises the detective's focus."""
    for c in world.characters():
        if c.meters["clues"] < THRESHOLD:
            continue
        sig = ("clue_logged", c.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        c.memes["focus"] += 1
        c.memes["pride"] += 1
    return []


def _r_culprit_kind(world: World) -> list[str]:
    """When the culprit is found and is kind, the case softens to a fix."""
    for c in world.characters():
        if c.memes["kindly"] < THRESHOLD:
            continue
        sig = ("kind", c.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        c.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="case_open", tag="social", apply=_r_case_open),
    Rule(name="clue_logged", tag="mental", apply=_r_clue_logged),
    Rule(name="culprit_kind", tag="social", apply=_r_culprit_kind),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply all rules until nothing new fires (forward chaining to fixpoint)."""
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* case and a *reasonable* fix.
# ---------------------------------------------------------------------------
def case_uses_weekly(case: Case) -> bool:
    """Every case in this world must be a 'weekly' quest."""
    return True   # by construction; placeholder for future constraint


def case_uses_crooked(case: Case) -> bool:
    """Every case must mention something that was found crooked."""
    return bool(case.crooked)


def case_has_quest(case: Case) -> bool:
    """A quest needs a stolen thing, a trail, a weak link, and a culprit."""
    return all([case.stolen, case.trail, case.weak_link, case.culprit])


def case_supports_problem_solving(case: Case) -> bool:
    """Problem solving needs a trail of clues (>=2) and a tool that helps."""
    return bool(case.trail) and bool(case.weak_link)


def select_tool(case: Case) -> Optional[Tool]:
    """A tool that *actually* uncovers a clue for this case."""
    for tool in TOOLS:
        if tool.helps & {case.crooked.split()[-1] if case.crooked else "",
                         case.trail.split()[-1] if case.trail else ""}:
            return tool
        # also accept a tool that helps with any generic clue kind
        if tool.helps & {"clues", "clue", "footprints", "print", "ribbon", "button"}:
            return tool
    return None


# ---------------------------------------------------------------------------
# Prediction: the detective runs the world model forward on a copy.
# ---------------------------------------------------------------------------
def predict_case(world: World, detective: Entity, case: Case) -> dict:
    """Simulate the case silently and report what the notebook will record."""
    sim = world.copy()
    _accept_case(sim, sim.get(detective.id), case, narrate=False)
    _find_clue(sim, sim.get(detective.id), case, None, narrate=False)
    return {
        "clues": sum(e.meters["clues"] for e in sim.characters()),
        "focus": sum(e.memes["focus"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def _accept_case(world: World, detective: Entity, case: Case, narrate: bool = True) -> None:
    detective.memes["case_open"] += 1
    detective.memes["care"] += 1
    if narrate:
        world.case = case
        world.say(
            f"One Saturday morning, the {case.culprit} came to {detective.id} "
            f"looking worried. Three {case.stolen} had vanished from the town "
            f"shop, and the {case.crooked} had been turned crooked."
        )
        world.say(
            f'"Can you solve this little weekly case for me?" asked the '
            f"{case.culprit}. 'Please be kind, and please be careful with the clues.'"
        )


def introduce(world: World, detective: Entity) -> None:
    trait = next((t for t in detective.traits if t != "little"), "")
    desc = f"little {trait} {detective.type}".strip()
    world.say(
        f"{detective.id} was a {desc} who noticed every small clue in his quiet town."
    )


def loves_quest(world: World, detective: Entity) -> None:
    detective.memes["love_quest"] += 1
    world.say(
        f"Every weekend, {detective.id} would visit the grand library on Maple "
        f"Street, borrow a fresh notebook, and start a new weekly quest. The work "
        f"made {detective.pronoun('object')} feel useful and bright."
    )


def _find_clue(world: World, detective: Entity, case: Case, tool: Optional[Tool],
               narrate: bool = True) -> None:
    detective.meters["clues"] += 1
    if narrate:
        head = f"{detective.id} walked to the town shop with a notebook"
        if tool:
            head += f" and a {tool.label}"
        head += "."
        world.say(head)
        world.say(
            f"{detective.pronoun('subject').capitalize()} saw {case.trail} on the "
            f"floor, a crooked {case.crooked.replace('the ', '')} that had been "
            f"nudged, and {case.weak_link} near the back door."
        )
        world.say(
            f"{detective.pronoun('subject').capitalize()} wrote each clue in "
            f"{detective.pronoun('possessive')} notebook: {case.trail}, crooked "
            f"{case.crooked.replace('the ', '')}, and {case.weak_link}."
        )


def follow_trail(world: World, detective: Entity, case: Case) -> None:
    detective.memes["focus"] += 1
    world.say(
        f"{detective.id} followed the trail through the alley behind the shop. "
        f"There, by a small green bench, {detective.pronoun('subject')} found a "
        f"soft piece of {case.stolen} and {case.weak_link} that pointed to "
        f"someone {detective.pronoun('subject')} knew."
    )


def confront(world: World, detective: Entity, case: Case) -> None:
    detective.memes["resolve"] += 1
    detective.memes["kindness"] += 1
    world.say(
        f"{detective.id} did not shout. {detective.pronoun('subject').capitalize()} "
        f"showed {case.culprit} the {case.weak_link} and the {case.trail}, and asked, "
        f'very kindly, "Could the {case.stolen} please come home?"'
    )


def confess(world: World, detective: Entity, case: Case) -> None:
    for c in world.characters():
        if c.label == case.culprit or c.type == case.culprit.split()[-1] or c.id == "culprit":
            c.memes["kindly"] += 1
            c.memes["shame"] += 1
            c.memes["relief"] += 1
            world.say(
                f"The {case.culprit}'s face went pink. '{case.kind_word.capitalize()},"
                f"' the {case.culprit} said softly, 'and I meant to put it back. "
                f"I am sorry.'"
            )
            return
    # Fallback: a generic but grounded confession line.
    world.say(
        f"The {case.culprit}'s face went pink. '{case.kind_word.capitalize()},' "
        f"the {case.culprit} said softly, 'and I meant to put it back. I am sorry.'"
    )


def solve_together(world: World, detective: Entity, case: Case) -> None:
    detective.memes["relief"] += 1
    detective.memes["pride"] += 1
    detective.memes["case_open"] = 0.0     # resolution clears the open case
    world.say(
        f"{detective.id} nodded and said they could solve it together. They "
        f"carried the {case.stolen} back to the town shop, and the {case.culprit} "
        f"helped set the {case.crooked} straight."
    )
    world.say(
        f"The shopkeeper smiled, and gave each of them a warm thank-you. "
        f"{detective.id} wrote one last line in {detective.pronoun('possessive')} "
        f"notebook: 'Solved with kindness, and the {case.crooked} stood tall again.'"
    )


# ---------------------------------------------------------------------------
# The screenplay: coarse three-act shape, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(case: Case, detective_name: str = "Sam", detective_type: str = "boy",
         detective_traits: Optional[list[str]] = None) -> World:
    world = World()
    world.case = case

    detective = world.add(Entity(
        id=detective_name, kind="character", type=detective_type,
        traits=["little"] + (detective_traits or ["careful", "kind"]),
    ))
    culprit = world.add(Entity(
        id="culprit", kind="character", type=case.culprit.split()[-1],
        label=case.culprit, phrase=case.culprit,
    ))

    # Act 1 -- setup: who, what they love, the case that arrives.
    introduce(world, detective)
    loves_quest(world, detective)
    _accept_case(world, detective, case, narrate=True)

    # Act 2 -- problem solving: clues found, trail followed, gentle confrontation.
    world.para()
    tool = select_tool(case)
    _find_clue(world, detective, case, tool, narrate=True)
    follow_trail(world, detective, case)
    confront(world, detective, case)

    # Act 3 -- resolution: kind confession and a joint fix.
    world.para()
    confess(world, detective, case)
    solve_together(world, detective, case)

    # Record facts for the Q&A generators (grounded in the simulated world).
    world.facts.update(
        detective=detective,
        culprit=culprit,
        case=case,
        tool=tool,
        clues=detective.meters["clues"],
        focus=detective.memes["focus"],
        kindness=detective.memes["kindness"],
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
CASES = {
    "bread": Case(
        id="bread",
        stolen="loaves of bread",
        stolen_label="loaves",
        stolen_plural=True,
        crooked="the price sign",
        trail="floury footprints",
        weak_link="a torn ribbon",
        culprit="the baker",
        kind_word="i was hungry",
        fix_phrase="set the sign straight and shared a warm bun",
        keyword="bread",
        tags={"bread", "baker", "loaves"},
    ),
    "tools": Case(
        id="tools",
        stolen="garden tools",
        stolen_label="tools",
        stolen_plural=True,
        crooked="the garden gate",
        trail="muddy footprints",
        weak_link="a little round button",
        culprit="the neighbor",
        kind_word="i was fixing my fence",
        fix_phrase="set the gate straight and lent a hand",
        keyword="tools",
        tags={"tools", "garden", "gate"},
    ),
    "letters": Case(
        id="letters",
        stolen="stacked letters",
        stolen_label="letters",
        stolen_plural=True,
        crooked="the mail slot",
        trail="ink smudges",
        weak_link="a small blue glove",
        culprit="the postman",
        kind_word="i meant to deliver them first thing",
        fix_phrase="set the mail slot straight and delivered the letters",
        keyword="letters",
        tags={"letters", "postman", "mail"},
    ),
    "paint": Case(
        id="paint",
        stolen="paint pots",
        stolen_label="paint pots",
        stolen_plural=True,
        crooked="the studio curtain",
        trail="bright drips",
        weak_link="a soft paintbrush",
        culprit="the painter",
        kind_word="i wanted to finish my picture",
        fix_phrase="set the curtain straight and shared the brushes",
        keyword="paint",
        tags={"paint", "painter", "curtain"},
    ),
    "books": Case(
        id="books",
        stolen="library books",
        stolen_label="books",
        stolen_plural=True,
        crooked="the library sign",
        trail="soft scuff marks",
        weak_link="a paper bookmark",
        culprit="the librarian",
        kind_word="i was reading one more chapter",
        fix_phrase="set the sign straight and returned the books",
        keyword="books",
        tags={"books", "library", "sign"},
    ),
}

# Order matters: more specific tools first, generic fallback last.
TOOLS = [
    Tool(
        id="magnifier",
        label="bright magnifying glass",
        phrase="a bright magnifying glass",
        helps={"footprints", "print", "smudges", "drips", "scuff", "ribbon", "button",
               "clues", "clue"},
    ),
    Tool(
        id="notebook",
        label="fresh notebook",
        phrase="a fresh notebook",
        helps={"clues", "clue"},
    ),
    Tool(
        id="pencil",
        label="sharp pencil",
        phrase="a sharp pencil",
        helps={"clues", "clue"},
    ),
]

DETECTIVE_TYPES = ["boy", "girl"]
GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Sam", "Ben", "Max", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Tim"]
TRAITS = ["careful", "curious", "kind", "patient", "bright", "quiet"]


def valid_combos() -> list[tuple[str, str]]:
    """(case_id, detective_type) pairs that pass the reasonableness constraint."""
    combos = []
    for case_id, c in CASES.items():
        if not (case_uses_weekly(c) and case_uses_crooked(c)
                and case_has_quest(c) and case_supports_problem_solving(c)):
            continue
        for dtype in DETECTIVE_TYPES:
            combos.append((case_id, dtype))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    case: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "bread": [("What is bread made of?",
               "Bread is made by mixing flour, water, a little salt, and often "
               "yeast, then baking the soft dough in a hot oven until it rises "
               "and turns golden.")],
    "baker": [("What does a baker do?",
               "A baker is a person who bakes bread, buns, cakes, and other "
               "goods, usually early in the morning, for a town shop.")],
    "loaves": [("What is a loaf of bread?",
                "A loaf of bread is one whole shaped piece of bread, baked "
                "together so it can be sliced and shared.")],
    "tools": [("What are garden tools?",
               "Garden tools are simple hand tools like trowels, rakes, and "
               "watering cans, used to tend small plants and tidy a garden.")],
    "garden": [("What is a garden?",
                "A garden is a small patch of ground where people grow "
                "flowers, herbs, or vegetables.")],
    "gate": [("What is a garden gate?",
              "A garden gate is a small door in a fence that lets people "
              "walk into a garden and keeps animals out.")],
    "letters": [("What is a letter?",
                 "A letter is a piece of paper with a written message, "
                 "folded and sent to someone through the post.")],
    "postman": [("What does a postman do?",
                 "A postman is a person who carries letters and small "
                 "packages from the post office to people's homes.")],
    "mail": [("What is the mail?",
              "The mail is the letters and packages that are sent through "
              "the post office to people in a town.")],
    "paint": [("What is paint?",
               "Paint is a colored liquid that you can spread on paper, "
               "walls, or canvas with a brush to make a picture.")],
    "painter": [("What does a painter do?",
                 "A painter is a person who uses paint and brushes to make "
                 "pictures on paper or walls.")],
    "curtain": [("What is a curtain for?",
                 "A curtain is a piece of cloth you hang in front of a "
                 "window or doorway, and you can pull it to one side to "
                 "let light in or keep it dark.")],
    "books": [("What is a book?",
               "A book is a stack of pages held together by a cover, "
               "with words and pictures that tell a story or share ideas.")],
    "library": [("What is a library?",
                 "A library is a quiet room or building full of books "
                 "that people can borrow to read at home.")],
    "sign": [("What is a sign?",
              "A sign is a piece of wood, paper, or metal with words or "
              "pictures on it, used to share information with people who pass by.")],
    "detective": [("What does a detective do?",
                   "A detective is a person who looks for clues, asks kind "
                   "questions, and tries to find out what happened in a "
                   "small mystery.")],
    "clues": [("What is a clue?",
               "A clue is a small piece of information that helps you "
               "figure out what happened, like a footprint, a button, or a note.")],
    "footprints": [("What is a footprint?",
                    "A footprint is the mark a shoe or foot leaves on the "
                    "ground when someone walks across a soft surface.")],
    "ribbon": [("What is a ribbon?",
                "A ribbon is a long, thin strip of cloth, often used to "
                "tie or decorate things.")],
    "button": [("What is a button?",
                "A button is a small round fastener that holds two pieces "
                "of cloth together on a coat or shirt.")],
    "notebook": [("What is a notebook for?",
                  "A notebook is a small book of blank pages used for "
                  "writing down ideas, clues, or stories.")],
}
KNOWLEDGE_ORDER = [
    "detective", "clues", "footprints", "ribbon", "button", "notebook",
    "bread", "baker", "loaves",
    "tools", "garden", "gate",
    "letters", "postman", "mail",
    "paint", "painter", "curtain",
    "books", "library", "sign",
]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    detective, case = f["detective"], f["case"]
    kw = case.keyword or case.stolen.split()[-1]
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a weekly '
        f'mystery, a crooked clue, a kind fix" that includes the word "{kw}".',
        f"Tell a gentle detective-style story where a little {detective.type} "
        f"named {detective.id} solves a small weekly mystery about missing "
        f"{case.steven_label if hasattr(case, 'steven_label') else case.stolen} "
        f"by following clues and being kind to the {case.culprit}.",
        f"Write a simple story that uses the word \"{kw}\", begins at the "
        f"grand library, and ends with the crooked thing standing tall again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    detective, case = f["detective"], f["case"]
    sub, obj, pos = (detective.pronoun("subject"), detective.pronoun("object"),
                     detective.pronoun("possessive"))
    trait = next((t for t in detective.traits if t != "little"), detective.type)
    day = "Saturday morning"
    stolen_noun = case.stolen
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who came to {detective.id} on {day} to ask for help with the "
                f"weekly mystery about the missing {stolen_noun}?"
            ),
            answer=(
                f"On {day}, the {case.culprit} came to {detective.id} looking "
                f"worried. Three {stolen_noun} had vanished from the town shop, "
                f"and the {case.crooked} had been turned crooked."
            ),
        ),
        QAItem(
            question=(
                f"What did little {detective.id} do every weekend before the "
                f"weekly mystery about the {stolen_noun} arrived?"
            ),
            answer=(
                f"Every weekend, {detective.id} would visit the grand library "
                f"on Maple Street, borrow a fresh notebook, and start a new "
                f"weekly quest."
            ),
        ),
        QAItem(
            question=(
                f"What clues did the {trait} detective {detective.id} write "
                f"in {pos} notebook for the {stolen_noun} case?"
            ),
            answer=(
                f"{sub.capitalize()} saw {case.trail} on the floor, a crooked "
                f"{case.crooked.replace('the ', '')} that had been nudged, and "
                f"{case.weak_link} near the back door. {sub.capitalize()} "
                f"wrote each clue in {pos} notebook."
            ),
        ),
    ]
    if f.get("resolved"):
        tool = f.get("tool")
        tool_phrase = f" and a {tool.label}" if tool else ""
        qa.append(QAItem(
            question=(
                f"How did {detective.id} solve the {stolen_noun} mystery "
                f"without shouting at the {case.culprit}?"
            ),
            answer=(
                f"{sub.capitalize()} showed the {case.culprit} the "
                f"{case.weak_link} and the {case.trail}, and asked, very "
                f"kindly, if the {stolen_noun} could please come home. The "
                f"{case.culprit} admitted '{case.kind_word}' and they carried "
                f"the {stolen_noun} back together."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {trait} {detective.id} feel at the end of the weekly "
                f"mystery about the {stolen_noun}?"
            ),
            answer=(
                f"{detective.id} felt proud and kind, and wrote one last line "
                f"in {pos} notebook: 'Solved with kindness, and the "
                f"{case.crooked} stood tall again.'"
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = set(f["case"].tags)
    if f.get("tool"):
        tags.add(f["tool"].id)
    tags.add("detective")
    tags.add("clues")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(case="bread",  name="Sam", gender="boy",  trait="kind"),
    StoryParams(case="tools",  name="Mia", gender="girl", trait="patient"),
    StoryParams(case="letters",name="Ben", gender="boy",  trait="bright"),
    StoryParams(case="paint",  name="Lily",gender="girl", trait="careful"),
    StoryParams(case="books",  name="Max", gender="boy",  trait="curious"),
]


def explain_rejection(case_id: str) -> str:
    if case_id not in CASES:
        return (f"(No story: '{case_id}' is not a known weekly case. "
                f"Try one of: {', '.join(sorted(CASES))}.)")
    c = CASES[case_id]
    if not case_uses_crooked(c):
        return (f"(No story: the {case_id} case has no crooked clue -- "
                f"this domain requires a small thing found turned crooked.)")
    if not case_has_quest(c):
        return (f"(No story: the {case_id} case is missing pieces of the "
                f"quest (stolen thing, trail, weak link, or culprit).)")
    if not case_supports_problem_solving(c):
        return (f"(No story: the {case_id} case has no trail of clues to "
                f"follow, so the problem solving has nothing to work on.)")
    return f"(No story: '{case_id}' was rejected for an unknown reason.)"


def explain_gender(case_id: str, gender: str) -> str:
    return (f"(No story: a '{gender}' detective is not allowed for case "
            f"'{case_id}'. Try --gender {{boy,girl}}.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Every case must be a weekly quest, must involve a crooked clue, and must
% support problem solving (a trail and a weak link).
valid_case(C) :- case(C), crooked(C, _), trail(C, _), weak_link(C, _),
                 stolen(C, _), culprit(C, _).
valid_case_kind(C) :- valid_case(C).
valid(CT) :- case_kind(CT), valid_case_kind(CT).
valid_story(C, D) :- valid(C), detective(D).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for cid, c in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("stolen", cid, c.stolen))
        lines.append(asp.fact("crooked", cid, c.crooked))
        lines.append(asp.fact("trail", cid, c.trail))
        lines.append(asp.fact("weak_link", cid, c.weak_link))
        lines.append(asp.fact("culprit", cid, c.culprit))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", t.id, h))
    for dt in DETECTIVE_TYPES:
        lines.append(asp.fact("detective", dt))
    # Tag each case as a "case_kind" so valid/1 enumerates them.
    for cid in CASES:
        lines.append(asp.fact("case_kind", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (case, detective) pairs."""
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos()."""
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
# Standard storyworld interface (see storyworlds/AGENTS.md).
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a weekly crooked quest, a detective, "
                    "a kind fix. Unspecified choices are picked at random (seeded).")
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--gender", choices=DETECTIVE_TYPES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    # Clingo (ASP) modes -- the inline declarative reasoner (needs clingo).
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in any unspecified choices at random, keeping the combo reasonable.

    Raises StoryError if the *explicit* options describe an invalid story."""
    if args.case and args.case not in CASES:
        raise StoryError(explain_rejection(args.case))
    if args.case:
        c = CASES[args.case]
        if not (case_uses_crooked(c) and case_has_quest(c)
                and case_supports_problem_solving(c)):
            raise StoryError(explain_rejection(args.case))

    combos = [cc for cc in valid_combos()
              if (args.case is None or cc[0] == args.case)
              and (args.gender is None or cc[1] == args.gender)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    case_id, gender = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(case=case_id, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    world = tell(CASES[params.case], params.name, params.gender,
                 [params.trait, "kind"])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        pairs = asp_valid_combos()
        print(f"{len(pairs)} compatible (case, detective) combos:\n")
        for case_id, det in pairs:
            print(f"  {case_id:8} {det:5}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.case} case (detective: {p.gender})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
