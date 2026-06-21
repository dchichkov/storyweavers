#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/chowder_kindness_inner_monologue_humor_mystery.py
==============================================================================

A standalone story world for a tiny mystery about a missing pot of chowder.

The world model keeps a small set of typed entities with physical meters and
emotional memes. A child notices that a warm pot of chowder is no longer where
it should be, follows concrete clues, imagines funny wrong answers in an inner
monologue, and discovers that somebody moved it for a kind reason. The ending
shows the mystery solved and kindness shared.

Run it
------
    python storyworlds/worlds/gpt-5.4/chowder_kindness_inner_monologue_humor_mystery.py
    python storyworlds/worlds/gpt-5.4/chowder_kindness_inner_monologue_humor_mystery.py --place harbor_hall
    python storyworlds/worlds/gpt-5.4/chowder_kindness_inner_monologue_humor_mystery.py --problem missing_pot --reason cool_down
    python storyworlds/worlds/gpt-5.4/chowder_kindness_inner_monologue_humor_mystery.py --all
    python storyworlds/worlds/gpt-5.4/chowder_kindness_inner_monologue_humor_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/chowder_kindness_inner_monologue_humor_mystery.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "caretaker"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "caretaker": "caretaker"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    crowd: str
    trail: str
    hide_spot: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    missing_item: str
    display_name: str
    opening: str
    found_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Reason:
    id: str
    action: str
    clue_text: str
    kind_explanation: str
    ending_proof: str
    requires: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class SuspectIdea:
    id: str
    thought: str
    ruled_out: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    chowder = world.entities.get("chowder")
    if child and chowder and chowder.meters["missing"] >= THRESHOLD:
        sig = ("mystery", "missing")
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["curiosity"] += 1
            out.append("__mystery__")
    if child and world.facts.get("found_clue"):
        sig = ("search", world.facts["found_clue"])
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["focus"] += 1
    if child and helper and chowder and chowder.meters["found"] >= THRESHOLD:
        sig = ("solved", "kind")
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["relief"] += 1
            child.memes["kindness"] += 1
            helper.memes["relief"] += 1
            out.append("__solved__")
    if narrate:
        for line in out:
            if not line.startswith("__"):
                world.say(line)
    return out


PLACES = {
    "harbor_hall": Place(
        id="harbor_hall",
        label="the harbor hall",
        opening="Long windows looked out toward bobbing boats, and the room smelled like warm bread and sea air.",
        crowd="Neighbors in bright raincoats tapped their spoons and talked in happy, echoing little waves.",
        trail="A pale drop of chowder shone on the floorboards like a tiny moon.",
        hide_spot="the cool pantry by the back door",
        ending="Soon the chowder steamed from sturdy bowls while rain tapped the windows.",
        tags={"harbor", "hall"},
    ),
    "school_kitchen": Place(
        id="school_kitchen",
        label="the school kitchen",
        opening="Big metal counters gleamed, and paper fish from art class swayed above the doorway.",
        crowd="Parents whispered over folding tables while soup spoons clinked like small bells.",
        trail="A creamy drip dotted the checker floor in a neat, wiggly line.",
        hide_spot="the quiet counter beside the open window",
        ending="Soon the chowder sat in little cups beside the art wall, and everyone slurped with smiles.",
        tags={"school", "kitchen"},
    ),
    "library_basement": Place(
        id="library_basement",
        label="the library basement",
        opening="Upstairs, books slept on their shelves, but downstairs the supper room glowed warm and yellow.",
        crowd="The grown-ups tried to speak softly because it was a library, yet their hungry stomachs made the room feel noisy anyway.",
        trail="A small splash of chowder winked near the chair legs as if it wanted to be noticed.",
        hide_spot="the side table under the big clock",
        ending="Soon the chowder was ladled out while the clock hummed above the room.",
        tags={"library", "basement"},
    ),
}

PROBLEMS = {
    "missing_pot": Problem(
        id="missing_pot",
        missing_item="pot",
        display_name="the pot of chowder",
        opening="When the child came back with napkins, the pot of chowder was gone from the serving table.",
        found_line="At the end of the trail sat the whole pot of chowder, still safe and warm.",
        tags={"pot", "chowder"},
    ),
    "missing_ladle": Problem(
        id="missing_ladle",
        missing_item="ladle",
        display_name="the chowder ladle",
        opening="When the child turned around, the chowder ladle had vanished from the soup pot.",
        found_line="At the end of the trail rested the chowder ladle beside the warm pot.",
        tags={"ladle", "chowder"},
    ),
}

REASONS = {
    "cool_down": Reason(
        id="cool_down",
        action="moved the chowder so it could cool a little",
        clue_text="The trail led away from the noisy crowd toward a calmer, cooler corner.",
        kind_explanation="A little child had reached for the steam, so the helper moved it to a safer place until serving time.",
        ending_proof="By the end, the bowls were no longer too hot for small hands.",
        requires={"missing_pot"},
        tags={"steam", "safety", "kindness"},
    ),
    "share_with_shy_guest": Reason(
        id="share_with_shy_guest",
        action="carried the chowder to someone who felt too shy to join the line",
        clue_text="The trail passed a folded chair and a lonely little place setting near the wall.",
        kind_explanation="An older neighbor felt embarrassed about a shaky leg and did not want everyone to watch, so the helper brought the chowder over first.",
        ending_proof="By the end, the shy guest was smiling into a bowl and sitting with everyone else.",
        requires={"missing_pot", "missing_ladle"},
        tags={"sharing", "kindness", "guest"},
    ),
    "wipe_spill": Reason(
        id="wipe_spill",
        action="set the chowder aside for a minute to wipe up a slippery spill",
        clue_text="The trail stopped beside a rag bucket and a floor sign with a crooked arrow.",
        kind_explanation="A slippery drip had landed on the floor, and the helper did not want anyone to skid while carrying bowls.",
        ending_proof="By the end, the floor was clean and the chowder came back with a steadier tray.",
        requires={"missing_pot", "missing_ladle"},
        tags={"cleanup", "safety", "kindness"},
    ),
}

SUSPECTS = {
    "seagull": SuspectIdea(
        id="seagull",
        thought='For one wild second, the child thought, "A seagull has solved soup and become a thief."',
        ruled_out="Then the child remembered that even a very rude seagull could not carry a whole soup pot without making a much bigger mess.",
        tags={"bird", "humor"},
    ),
    "cat": SuspectIdea(
        id="cat",
        thought='The child thought, "Maybe a cat in a detective hat tiptoed in and borrowed it."',
        ruled_out="But the clue drops were slow and careful, not splashed like cat paws.",
        tags={"cat", "humor"},
    ),
    "ghost": SuspectIdea(
        id="ghost",
        thought='The child shivered happily and thought, "What if a basement ghost likes chowder?"',
        ruled_out="A moment later, the child saw warm drips and decided ghosts would be tidier, or at least floatier.",
        tags={"ghost", "humor"},
    ),
}

HELPERS = {
    "friend": {"type": "girl", "names": ["June", "Mina", "Tess", "Ruth"], "label": "the helper"},
    "caretaker": {"type": "caretaker", "names": ["Mr. Reed", "Mr. Bell", "Mr. Pike"], "label": "the caretaker"},
    "aunt": {"type": "aunt", "names": ["Aunt May", "Aunt June", "Aunt Clara"], "label": "the cook"},
}

CHILD_NAMES = {
    "girl": ["Lina", "Mara", "Poppy", "Nell", "Elsie", "Ada"],
    "boy": ["Owen", "Milo", "Theo", "Bram", "Nico", "Jules"],
}
TRAITS = ["curious", "careful", "brisk", "gentle", "observant", "funny"]


def valid_reason(problem_id: str, reason_id: str) -> bool:
    return problem_id in REASONS[reason_id].requires


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for problem_id in PROBLEMS:
            for reason_id in REASONS:
                if valid_reason(problem_id, reason_id):
                    combos.append((place_id, problem_id, reason_id))
    return combos


@dataclass
class StoryParams:
    place: str
    problem: str
    reason: str
    suspect: str
    helper_role: str
    child_name: str
    child_gender: str
    helper_name: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


def explain_rejection(problem_id: str, reason_id: str) -> str:
    reason = REASONS[reason_id]
    problem = PROBLEMS[problem_id]
    return (
        f"(No story: {reason.id} does not fit {problem.id}. "
        f"This world only allows reasons that make sense for {problem.display_name}.)"
    )


def opening_scene(world: World, place: Place, child: Entity) -> None:
    world.say(
        f"{child.id} hurried into {place.label} with a stack of napkins tucked under one arm. "
        f"{place.opening}"
    )
    world.say(place.crowd)
    child.memes["joy"] += 1


def discover_missing(world: World, problem: Problem, child: Entity, chowder: Entity) -> None:
    chowder.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(problem.opening)
    child.memes["alarm"] += 1
    world.say(
        f'{child.id} blinked. In {child.pronoun("possessive")} head, the room changed at once from supper room to mystery room.'
    )


def inner_monologue(world: World, suspect: SuspectIdea, child: Entity) -> None:
    child.memes["imagination"] += 1
    world.say(suspect.thought)
    world.say(suspect.ruled_out)
    world.say(
        f'{child.id} took a slow breath. "{child.pronoun("subject").capitalize()} need facts," {child.pronoun("subject")} told {child.pronoun("object")}self in a very detective voice.'
    )


def find_clue(world: World, place: Place, reason: Reason, child: Entity) -> None:
    world.facts["found_clue"] = reason.id
    propagate(world, narrate=False)
    child.meters["steps"] += 1
    world.say(place.trail)
    world.say(reason.clue_text)
    world.say(
        f"{child.id} followed the clue on tiptoe, trying to look stern, though the tiptoeing made {child.pronoun('object')} look more like a hopping sparrow than a detective."
    )


def reveal(world: World, place: Place, problem: Problem, reason: Reason, child: Entity, helper: Entity, chowder: Entity) -> None:
    chowder.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(f"{problem.found_line} It was waiting in {place.hide_spot}.")
    world.say(
        f"Beside it stood {helper.id}, who looked surprised and then relieved to see {child.id}."
    )
    world.say(
        f'"I was not stealing supper," {helper.id} said. "I {reason.action}."'
    )
    world.say(reason.kind_explanation)


def respond_kindly(world: World, child: Entity, helper: Entity, problem: Problem, reason: Reason) -> None:
    child.memes["kindness"] += 1
    helper.memes["gratitude"] += 1
    if reason.id == "share_with_shy_guest":
        world.say(
            f'{child.id} felt the mystery untie itself inside {child.pronoun("possessive")} chest. '
            f'"That was kind," {child.pronoun("subject")} said. "Want me to carry the spoons so nobody stares?"'
        )
    elif reason.id == "cool_down":
        world.say(
            f'{child.id} looked at the steam and nodded. "{problem.display_name.capitalize()} did look fierce," {child.pronoun("subject")} admitted. '
            f'"It was only pretending to be calm."'
        )
        world.say(
            f'"Want me to tell the little ones to wait until the steam stops puffing like an angry dragon?" {child.id} asked.'
        )
    else:
        world.say(
            f'{child.id} looked down at the floor sign and then back at {helper.id}. '
            f'"Oh," {child.pronoun("subject")} said softly. "You were saving ankles and supper at the same time."'
        )
        world.say(f'"I can help carry things while you finish," {child.id} offered.')
    world.say(
        f"{helper.id} smiled so suddenly that the whole mystery seemed to turn warm. Together they brought everything back."
    )


def ending(world: World, place: Place, child: Entity, helper: Entity, reason: Reason) -> None:
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    world.say(place.ending)
    world.say(reason.ending_proof)
    world.say(
        f"{child.id} tasted the chowder at last and decided that solving a mystery felt good, but helping after the mystery felt even better."
    )
    world.say(
        f'In {child.pronoun("possessive")} head, {child.pronoun("subject")} gave the case a grand name: "The Curious Chowder Clue." Then {child.pronoun("subject")} had to laugh, because the only villain had been hurry.'
    )


def tell(
    place: Place,
    problem: Problem,
    reason: Reason,
    suspect: SuspectIdea,
    child_name: str,
    child_gender: str,
    helper_role: str,
    helper_name: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        label=child_name,
        attrs={"trait": trait},
    ))
    helper_type = HELPERS[helper_role]["type"]
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        role="helper",
        label=HELPERS[helper_role]["label"],
        attrs={"helper_role": helper_role},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    chowder = world.add(Entity(
        id="chowder",
        kind="thing",
        type="food",
        label=problem.display_name,
        phrase="a warm pot of chowder",
        tags={"chowder"},
    ))

    opening_scene(world, place, child)
    world.para()
    discover_missing(world, problem, child, chowder)
    inner_monologue(world, suspect, child)
    world.para()
    find_clue(world, place, reason, child)
    reveal(world, place, problem, reason, child, helper, chowder)
    world.para()
    respond_kindly(world, child, helper, problem, reason)
    ending(world, place, child, helper, reason)

    world.facts.update(
        place=place,
        problem=problem,
        reason=reason,
        suspect=suspect,
        child=child,
        helper=helper,
        parent=parent,
        chowder=chowder,
        solved=chowder.meters["found"] >= THRESHOLD,
        kindness=child.memes["kindness"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "chowder": [
        (
            "What is chowder?",
            "Chowder is a thick soup, often made warm and creamy with pieces of food in it. People usually eat it from a bowl with a spoon."
        )
    ],
    "steam": [
        (
            "Why can hot steam be a problem for little hands?",
            "Steam means something is very hot. If a bowl or pot is too hot, a grown-up may move it so nobody gets burned."
        )
    ],
    "sharing": [
        (
            "How can bringing food to someone be kind?",
            "It can help a shy, tired, or worried person feel included. Small helpful actions can make a meal feel welcoming."
        )
    ],
    "cleanup": [
        (
            "Why should a spill be cleaned up quickly?",
            "A spill can make the floor slippery. Cleaning it quickly helps keep people safe."
        )
    ],
    "mystery": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you figure something out. It can be a mark, a sound, or something left behind."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help, comfort, or think about someone else. It often shows up in small actions."
        )
    ],
}
KNOWLEDGE_ORDER = ["chowder", "mystery", "steam", "sharing", "cleanup", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    reason = f["reason"]
    return [
        'Write a short mystery story for a 3-to-5-year-old that includes the word "chowder", a funny inner monologue, and a kind ending.',
        f"Tell a gentle mystery set in {place.label} where {child.id} follows clues after some chowder seems to go missing and finds a caring explanation.",
        f"Write a child-facing story with humor and kindness in which a detective-minded child solves a tiny food mystery and learns that {reason.kind_explanation[:-1].lower()}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    problem = f["problem"]
    reason = f["reason"]
    suspect = f["suspect"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who notices a mystery around chowder in {place.label}, and {helper.id}, who turns out to be helping instead of causing trouble."
        ),
        (
            f"What mystery did {child.id} notice?",
            f"{child.id} saw that {problem.display_name} was missing from where it should have been. That missing chowder item is what made the room feel like a mystery."
        ),
        (
            f"What funny idea did {child.id} imagine first?",
            f"{suspect.thought[0].upper()}{suspect.thought[1:]} {suspect.ruled_out} The silly guess shows how {child.id}'s thoughts jumped before the clues were checked."
        ),
        (
            f"How did {child.id} solve the mystery?",
            f"{child.id} looked for clues instead of staying with the first silly guess. The little drips and signs led {child.pronoun('object')} to {place.hide_spot}, where the chowder had been moved."
        ),
        (
            f"Why had {helper.id} moved the chowder?",
            f"{helper.id} had {reason.action}. {reason.kind_explanation} That kind reason changed the mystery from something sneaky into something caring."
        ),
        (
            f"How did {child.id} act kindly after learning the truth?",
            f"{child.id} did not stay cross or embarrassed. Instead, {child.pronoun('subject')} offered help, because the clues showed that {helper.id} had been protecting or helping someone."
        ),
        (
            "How did the story end?",
            f"The chowder came back, the room felt warm again, and the mystery was solved. {reason.ending_proof} The ending shows that kindness, not trickery, was at the center of the case."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"chowder", "mystery", "kindness"} | set(world.facts["reason"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits: list[str] = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="harbor_hall",
        problem="missing_pot",
        reason="cool_down",
        suspect="seagull",
        helper_role="caretaker",
        child_name="Lina",
        child_gender="girl",
        helper_name="Mr. Reed",
        parent_type="mother",
        trait="observant",
        seed=1,
    ),
    StoryParams(
        place="library_basement",
        problem="missing_ladle",
        reason="share_with_shy_guest",
        suspect="ghost",
        helper_role="aunt",
        child_name="Owen",
        child_gender="boy",
        helper_name="Aunt May",
        parent_type="father",
        trait="curious",
        seed=2,
    ),
    StoryParams(
        place="school_kitchen",
        problem="missing_pot",
        reason="wipe_spill",
        suspect="cat",
        helper_role="friend",
        child_name="Mara",
        child_gender="girl",
        helper_name="June",
        parent_type="mother",
        trait="funny",
        seed=3,
    ),
]


ASP_RULES = r"""
requires(cool_down, missing_pot).
requires(share_with_shy_guest, missing_pot).
requires(share_with_shy_guest, missing_ladle).
requires(wipe_spill, missing_pot).
requires(wipe_spill, missing_ladle).

valid(Place, Problem, Reason) :- place(Place), problem(Problem), reason(Reason), requires(Reason, Problem).

solved :- chosen_reason(R), chosen_problem(P), requires(R, P).
ending(kind_resolution) :- solved.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for problem_id in PROBLEMS:
        lines.append(asp.fact("problem", problem_id))
    for reason_id in REASONS:
        lines.append(asp.fact("reason", reason_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_ending(problem_id: str, reason_id: str) -> str:
    import asp
    extra = f"chosen_problem({problem_id}).\nchosen_reason({reason_id})."
    model = asp.one_model(asp_program(extra, "#show ending/1."))
    atoms = asp.atoms(model, "ending")
    return atoms[0][0] if atoms else "none"


def outcome_of(params: StoryParams) -> str:
    if not valid_reason(params.problem, params.reason):
        return "invalid"
    return "kind_resolution"


def _validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(No story: unknown problem '{params.problem}'.)")
    if params.reason not in REASONS:
        raise StoryError(f"(No story: unknown reason '{params.reason}'.)")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"(No story: unknown suspect '{params.suspect}'.)")
    if params.helper_role not in HELPERS:
        raise StoryError(f"(No story: unknown helper_role '{params.helper_role}'.)")
    if not valid_reason(params.problem, params.reason):
        raise StoryError(explain_rejection(params.problem, params.reason))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    for params in CURATED:
        if asp_ending(params.problem, params.reason) != outcome_of(params):
            rc = 1
            print(f"MISMATCH in ending for curated params: {params}")
            break
    else:
        print(f"OK: ending model matches outcome_of() on {len(CURATED)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny mystery story world: missing chowder, funny thoughts, and a kind explanation."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--reason", choices=sorted(REASONS))
    ap.add_argument("--suspect", choices=sorted(SUSPECTS))
    ap.add_argument("--helper-role", choices=sorted(HELPERS), dest="helper_role")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.reason and not valid_reason(args.problem, args.reason):
        raise StoryError(explain_rejection(args.problem, args.reason))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.problem is None or combo[1] == args.problem)
        and (args.reason is None or combo[2] == args.reason)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, problem_id, reason_id = rng.choice(sorted(combos))
    suspect_id = args.suspect or rng.choice(sorted(SUSPECTS))
    helper_role = args.helper_role or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES[gender])
    helper_name = rng.choice(HELPERS[helper_role]["names"])
    parent_type = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    params = StoryParams(
        place=place_id,
        problem=problem_id,
        reason=reason_id,
        suspect=suspect_id,
        helper_role=helper_role,
        child_name=child_name,
        child_gender=gender,
        helper_name=helper_name,
        parent_type=parent_type,
        trait=trait,
        seed=None,
    )
    _validate_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        place=PLACES[params.place],
        problem=PROBLEMS[params.problem],
        reason=REASONS[params.reason],
        suspect=SUSPECTS[params.suspect],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_role=params.helper_role,
        helper_name=params.helper_name,
        parent_type=params.parent_type,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, reason) combos:\n")
        for place_id, problem_id, reason_id in combos:
            print(f"  {place_id:16} {problem_id:14} {reason_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.child_name}: {p.problem} at {p.place} ({p.reason})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
