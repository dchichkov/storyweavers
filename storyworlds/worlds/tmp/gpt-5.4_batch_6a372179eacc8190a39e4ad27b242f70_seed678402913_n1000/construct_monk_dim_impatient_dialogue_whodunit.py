#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/construct_monk_dim_impatient_dialogue_whodunit.py
============================================================================

A gentle little whodunit set in an old abbey hall. A child helper notices that a
crucial piece of a parade construct is missing just before the showing. In the
monk-dim light, a small clue points toward one impatient grown-up helper who
borrowed the piece without asking in order to solve another problem quickly.

The world model keeps the mystery grounded:
- a project construct needs one specific piece
- exactly one suspect could reasonably have borrowed that piece
- borrowing without asking causes delay and worry
- the detective child inspects the spot, questions the suspects, matches the clue,
  and gets the piece returned
- the ending image proves the project is whole again

Run it
------
    python storyworlds/worlds/gpt-5.4/construct_monk_dim_impatient_dialogue_whodunit.py
    python storyworlds/worlds/gpt-5.4/construct_monk_dim_impatient_dialogue_whodunit.py --project kite
    python storyworlds/worlds/gpt-5.4/construct_monk_dim_impatient_dialogue_whodunit.py --culprit gardener
    python storyworlds/worlds/gpt-5.4/construct_monk_dim_impatient_dialogue_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/construct_monk_dim_impatient_dialogue_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4/construct_monk_dim_impatient_dialogue_whodunit.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "lady"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Project:
    id: str
    construct_name: str
    piece: str
    piece_phrase: str
    missing_spot: str
    opening_image: str
    ending_image: str
    clue_kind: str
    culprit: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SuspectProfile:
    id: str
    name: str
    type: str
    role_label: str
    residue: str
    clue_text: str
    place: str
    need: str
    question_reply: str
    confession: str
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


def propagate(world: World) -> None:
    project = world.get("project")
    caretaker = world.get("caretaker")
    detective = world.get("detective")
    culprit = world.get(world.facts["culprit"])

    if project.meters["missing"] >= THRESHOLD and ("delay",) not in world.fired:
        world.fired.add(("delay",))
        caretaker.memes["worry"] += 1
        detective.memes["curiosity"] += 1
        world.get("hall").meters["delay"] += 1

    if culprit.memes["borrowed"] >= THRESHOLD and ("guilt", culprit.id) not in world.fired:
        world.fired.add(("guilt", culprit.id))
        culprit.memes["guilt"] += 1

    if project.meters["whole"] >= THRESHOLD and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        caretaker.memes["relief"] += 1
        detective.memes["pride"] += 1
        culprit.memes["relief"] += 1


PROJECTS = {
    "kite": Project(
        id="kite",
        construct_name="the star-kite construct",
        piece="red cord",
        piece_phrase="the red cord that held the silver tail straight",
        missing_spot="the tail ring",
        opening_image="Its paper stars shivered whenever the abbey door breathed in a little wind.",
        ending_image="The silver tail streamed behind it like a comet.",
        clue_kind="leaf",
        culprit="gardener",
        tags={"construct", "clue", "borrowing"},
    ),
    "swan": Project(
        id="swan",
        construct_name="the paper swan construct",
        piece="wooden clip",
        piece_phrase="the wooden clip that kept one white wing lifted high",
        missing_spot="the wing hinge",
        opening_image="Its long neck curved over a table covered in white feathers cut from paper.",
        ending_image="Both white wings stood proud and even.",
        clue_kind="flour",
        culprit="baker",
        tags={"construct", "clue", "borrowing"},
    ),
    "bellcart": Project(
        id="bellcart",
        construct_name="the little bell-cart construct",
        piece="brass hook",
        piece_phrase="the brass hook that held the front lantern in place",
        missing_spot="the lantern bar",
        opening_image="Tiny copper bells waited along its sides to jingle when it rolled.",
        ending_image="The front lantern glowed steady and warm.",
        clue_kind="soot",
        culprit="lantern_keeper",
        tags={"construct", "clue", "borrowing"},
    ),
}

SUSPECTS = {
    "gardener": SuspectProfile(
        id="gardener",
        name="Marta",
        type="woman",
        role_label="the gardener",
        residue="leaf",
        clue_text="a thin green leaf stuck near the empty ring",
        place="the herb court",
        need="tie up a bean vine that kept slumping over its little arch",
        question_reply='"I was in the herb court," Marta said. "The vine by the arch would not behave."',
        confession='"You found me out," Marta said. "I borrowed the cord because the vine kept falling, and I was too impatient to walk back and ask first."',
        tags={"leaf", "gardener"},
    ),
    "baker": SuspectProfile(
        id="baker",
        name="Pietro",
        type="man",
        role_label="the baker",
        residue="flour",
        clue_text="a pale dusting of flour on the table by the missing hinge",
        place="the bake room",
        need="clip shut a flour sack before it puffed all over the room",
        question_reply='"I was in the bake room," Pietro said. "A flour sack burst open like a sneeze."',
        confession='"You found me out," Pietro said. "I used the clip on the flour sack, and I was too impatient to ask before borrowing it."',
        tags={"flour", "baker"},
    ),
    "lantern_keeper": SuspectProfile(
        id="lantern_keeper",
        name="Brother Ansel",
        type="man",
        role_label="the lantern keeper",
        residue="soot",
        clue_text="a soft soot smudge on the wood beneath the empty bar",
        place="the lamp stand by the north arch",
        need="hang a wobbling lantern before it tipped and went dark",
        question_reply='"I was by the north arch," Brother Ansel said. "One lantern kept twisting on its chain."',
        confession='"You found me out," Brother Ansel said. "I borrowed the hook for the lantern, and I was too impatient to come and explain."',
        tags={"soot", "lantern"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Tess", "Ava", "June"]
BOY_NAMES = ["Owen", "Ben", "Milo", "Finn", "Theo", "Sam"]
TRAITS = ["careful", "sharp-eyed", "quiet", "thoughtful", "steady"]
PARENTS = ["mother", "father"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for pid, project in PROJECTS.items():
        if project.culprit in SUSPECTS and SUSPECTS[project.culprit].residue == project.clue_kind:
            combos.append((pid, project.culprit))
    return sorted(combos)


def explain_rejection(project: Project, culprit: SuspectProfile) -> str:
    return (
        f"(No story: {culprit.role_label} does not fit {project.construct_name}. "
        f"The missing clue there is {project.clue_kind}, but {culprit.role_label} "
        f"would leave {culprit.residue} instead.)"
    )


@dataclass
class StoryParams:
    project: str
    culprit: str
    detective_name: str
    detective_gender: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        project="kite",
        culprit="gardener",
        detective_name="Lina",
        detective_gender="girl",
        caretaker="mother",
        trait="sharp-eyed",
        seed=101,
    ),
    StoryParams(
        project="swan",
        culprit="baker",
        detective_name="Owen",
        detective_gender="boy",
        caretaker="father",
        trait="careful",
        seed=102,
    ),
    StoryParams(
        project="bellcart",
        culprit="lantern_keeper",
        detective_name="Mira",
        detective_gender="girl",
        caretaker="mother",
        trait="quiet",
        seed=103,
    ),
]


def clue_line(project: Project, suspect: SuspectProfile) -> str:
    return suspect.clue_text


def introduction(world: World, detective: Entity, caretaker: Entity, project: Project) -> None:
    world.say(
        f"In the monk-dim hall of the old abbey, {detective.id} stood beside {project.construct_name}. "
        f"{project.opening_image}"
    )
    world.say(
        f'{detective.id} had helped construct it all morning, and {detective.pronoun("possessive")} '
        f'{caretaker.label_word} said, "One more check, and the showing can begin."'
    )


def discover_missing(world: World, detective: Entity, caretaker: Entity, project: Project) -> None:
    project_ent = world.get("project")
    project_ent.meters["missing"] += 1
    propagate(world)
    world.say(
        f"But when {detective.id} reached for {project.piece_phrase}, it was gone. "
        f'Only the empty place at {project.missing_spot} stared back.'
    )
    world.say(
        f'"The {project.piece} is missing," {detective.id} whispered. '
        f'"Without it, {project.construct_name} cannot be finished."'
    )
    world.say(
        f'"Then we have a mystery," said {caretaker.label_word.capitalize()}. '
        f'"Look close before the hall grows any busier."'
    )


def inspect_clue(world: World, detective: Entity, project: Project, culprit_profile: SuspectProfile) -> None:
    detective.memes["focus"] += 1
    world.facts["clue"] = culprit_profile.residue
    world.say(
        f"{detective.id} knelt by {project.missing_spot} and peered at the wood. "
        f"There, beside the gap, lay {clue_line(project, culprit_profile)}."
    )
    world.say(
        f'"That is a clue," {detective.id} said softly. '
        f'"Whoever touched the {project.piece} left a little trail behind."'
    )


def question_one(world: World, detective: Entity, suspect: Entity, culprit_id: str) -> None:
    world.say(
        f'{detective.id} found {suspect.id} first. "{suspect.id}, did you see the missing piece?"'
    )
    if suspect.id == culprit_id:
        world.say(
            f'{suspect.question_reply} {suspect.pronoun("subject").capitalize()} did not meet '
            f'{detective.id}\'s eyes.'
        )
        suspect.memes["nervous"] += 1
    else:
        world.say(f"{suspect.question_reply} {suspect.pronoun('subject').capitalize()} looked surprised.")
        suspect.memes["calm"] += 1


def question_suspects(world: World, detective: Entity, culprit_id: str) -> None:
    order = ["gardener", "baker", "lantern_keeper"]
    for sid in order:
        world.say("")
        question_one(world, detective, world.get(sid), culprit_id)


def reveal(world: World, detective: Entity, caretaker: Entity, project: Project, culprit: Entity) -> None:
    residue = world.facts["clue"]
    detective.memes["certainty"] += 1
    world.para()
    world.say(
        f'At last {detective.id} turned back to {culprit.id}. "{culprit.id}," '
        f'{detective.pronoun("subject")} said, "the clue by {project.missing_spot} matched your work. '
        f"It was {residue}, and you were the one who needed the {project.piece}."'
    )
    world.say(
        f'"You did not mean to spoil the showing," said {caretaker.label_word}, '
        f'"but you did borrow it without asking."'
    )


def confession_and_return(world: World, detective: Entity, caretaker: Entity, project: Project, culprit: Entity) -> None:
    culprit.memes["borrowed"] += 1
    world.say(culprit.confession)
    world.say(
        f'{detective.id} answered, "Please bring it back. We can help with your problem after we finish this one."'
    )
    world.say(
        f'"Of course," {culprit.id} said, and hurried away.'
    )
    world.para()
    project_ent = world.get("project")
    project_ent.meters["missing"] = 0.0
    project_ent.meters["whole"] += 1
    culprit.memes["sorry"] += 1
    propagate(world)
    world.say(
        f'Soon {culprit.id} returned with the {project.piece}. Together they set it back at {project.missing_spot}, '
        f'and {project.construct_name} was whole again.'
    )
    world.say(
        f'"Next time I will ask," {culprit.id} said. '
        f'"Being impatient made a small problem into a bigger one."'
    )


def ending(world: World, detective: Entity, caretaker: Entity, project: Project, culprit: Entity) -> None:
    detective.memes["joy"] += 1
    caretaker.memes["joy"] += 1
    culprit.memes["trust"] += 1
    world.say(
        f'{caretaker.label_word.capitalize()} squeezed {detective.id}\'s shoulder. '
        f'"You solved it by looking, listening, and thinking."'
    )
    world.say(
        f'Then the abbey doors opened wide, the crowd stepped into the monk-dim hall, and {project.construct_name} '
        f'rolled forward at last. {project.ending_image}'
    )


def tell(
    project_cfg: Project,
    culprit_cfg: SuspectProfile,
    detective_name: str,
    detective_gender: str,
    caretaker_type: str,
    trait: str,
) -> World:
    world = World()
    detective = world.add(
        Entity(
            id=detective_name,
            kind="character",
            type=detective_gender,
            role="detective",
            traits=["little", trait],
            label=detective_name,
        )
    )
    caretaker = world.add(
        Entity(
            id="Caretaker",
            kind="character",
            type=caretaker_type,
            role="caretaker",
            label="the caretaker",
        )
    )
    project_ent = world.add(
        Entity(
            id="project",
            kind="thing",
            type="construct",
            role="project",
            label=project_cfg.construct_name,
            phrase=project_cfg.construct_name,
            tags=set(project_cfg.tags),
        )
    )
    hall = world.add(
        Entity(
            id="hall",
            kind="thing",
            type="hall",
            role="place",
            label="abbey hall",
            phrase="the monk-dim abbey hall",
        )
    )

    for sid, profile in SUSPECTS.items():
        ent = world.add(
            Entity(
                id=profile.name,
                kind="character",
                type=profile.type,
                role=sid,
                label=profile.role_label,
                phrase=profile.role_label,
                attrs={
                    "suspect_id": sid,
                    "residue": profile.residue,
                    "need": profile.need,
                    "place": profile.place,
                },
                tags=set(profile.tags),
            )
        )
        ent.question_reply = profile.question_reply  # type: ignore[attr-defined]
        ent.confession = profile.confession  # type: ignore[attr-defined]

    culprit_ent = None
    for ent in world.entities.values():
        if ent.role == culprit_cfg.id:
            culprit_ent = ent
            break
    if culprit_ent is None:
        raise StoryError("(Internal error: culprit entity not found.)")

    world.facts.update(
        detective=detective,
        caretaker=caretaker,
        project_cfg=project_cfg,
        culprit=culprit_ent.id,
        culprit_role=culprit_cfg.id,
        clue=project_cfg.clue_kind,
        suspects=[world.get(SUSPECTS["gardener"].name), world.get(SUSPECTS["baker"].name), world.get(SUSPECTS["lantern_keeper"].name)],
    )

    introduction(world, detective, caretaker, project_cfg)
    world.para()
    discover_missing(world, detective, caretaker, project_cfg)
    inspect_clue(world, detective, project_cfg, culprit_cfg)
    world.para()
    question_suspects(world, detective, culprit_ent.id)
    reveal(world, detective, caretaker, project_cfg, culprit_ent)
    confession_and_return(world, detective, caretaker, project_cfg, culprit_ent)
    world.para()
    ending(world, detective, caretaker, project_cfg, culprit_ent)

    world.facts.update(
        solved=detective.memes["certainty"] >= THRESHOLD,
        returned=project_ent.meters["whole"] >= THRESHOLD,
        worried=caretaker.memes["worry"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "construct": [
        (
            "What is a construct?",
            "A construct is something people build by putting parts together carefully. It can be a toy, a model, or a parade piece.",
        )
    ],
    "clue": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you figure out what happened. It might be a mark, a sound, or something left behind.",
        )
    ],
    "borrowing": [
        (
            "Why should you ask before borrowing something?",
            "You should ask first so other people know where their things are and can still use them. Asking also shows respect.",
        )
    ],
    "leaf": [
        (
            "Why might a leaf be an important clue?",
            "A leaf can show that someone came from a garden or touched a plant. Tiny things can tell a big story in a mystery.",
        )
    ],
    "flour": [
        (
            "What does flour look like?",
            "Flour is a soft pale powder used for baking. It can leave dusty marks on hands, aprons, or tables.",
        )
    ],
    "soot": [
        (
            "What is soot?",
            "Soot is soft black dust made by smoke or a flame. It can rub off on fingers or wood if something smoky was nearby.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective pays close attention, asks questions, and fits clues together. The job is to find the truth, not just to guess.",
        )
    ],
}
KNOWLEDGE_ORDER = ["construct", "clue", "borrowing", "leaf", "flour", "soot", "detective"]


def generation_prompts(world: World) -> list[str]:
    detective = world.facts["detective"]
    project = world.facts["project_cfg"]
    culprit_role = world.facts["culprit_role"]
    culprit = SUSPECTS[culprit_role]
    return [
        (
            f'Write a gentle whodunit for a 3-to-5-year-old with dialogue in a monk-dim abbey hall. '
            f'The story should include the word "construct" and end with a missing piece being found.'
        ),
        (
            f"Tell a mystery where a child named {detective.id} notices that {project.piece_phrase} is gone from "
            f"{project.construct_name}, interviews helpers, and discovers that {culprit.role_label} borrowed it."
        ),
        (
            f'Write a story with dialogue where an impatient helper takes a small part without asking, a child follows a clue, '
            f'and the construct is mended before the showing begins.'
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    detective = world.facts["detective"]
    caretaker = world.facts["caretaker"]
    project = world.facts["project_cfg"]
    culprit_role = world.facts["culprit_role"]
    culprit = SUSPECTS[culprit_role]
    culprit_name = world.get(world.facts["culprit"]).id
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a sharp little solver in the old abbey hall, and {caretaker.label_word} who trusted {detective.pronoun('object')} to look carefully. It is also about {culprit_name}, who borrowed a piece and had to make things right.",
        ),
        (
            f"What was missing from {project.construct_name}?",
            f"The missing piece was {project.piece_phrase}. Without it, the construct could not be finished for the showing.",
        ),
        (
            "What clue did the detective find?",
            f"{detective.id} found {culprit.clue_text}. That small sign matched the work {culprit.role_label} had been doing nearby.",
        ),
        (
            f"How did {detective.id} solve the mystery?",
            f"{detective.id} looked at the missing spot first, then asked the helpers where they had been. The clue and the borrowed need fit together, so {detective.pronoun('subject')} knew who had taken the piece.",
        ),
        (
            f"Why did {culprit_name} take the {project.piece}?",
            f"{culprit_name} needed it to {culprit.need}. {culprit.pronoun('subject').capitalize()} did not want to cause trouble, but being impatient led {culprit.pronoun('object')} to borrow it without asking.",
        ),
        (
            "How did the story end?",
            f"{culprit_name} returned the piece, apologized, and helped set the construct right again. In the end the showing could begin, which proved the mystery had truly been solved.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    project = world.facts["project_cfg"]
    culprit = SUSPECTS[world.facts["culprit_role"]]
    tags = {"construct", "clue", "borrowing", "detective"} | set(project.tags) | set(culprit.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:14} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
project_matches_culprit(P, C) :- project(P), culprit(C), project_culprit(P, C), project_clue(P, K), suspect_residue(C, K).
valid(P, C) :- project_matches_culprit(P, C).

solved(P, C) :- valid(P, C).
returned(P, C) :- solved(P, C).

#show valid/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, project in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("project_culprit", pid, project.culprit))
        lines.append(asp.fact("project_clue", pid, project.clue_kind))
    for sid, suspect in SUSPECTS.items():
        lines.append(asp.fact("culprit", sid))
        lines.append(asp.fact("suspect_residue", sid, suspect.residue))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between Python and ASP valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in asp:", sorted(cl - py))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small dialogue whodunit in a monk-dim abbey hall."
    )
    ap.add_argument("--project", choices=sorted(PROJECTS))
    ap.add_argument("--culprit", choices=sorted(SUSPECTS))
    ap.add_argument("--caretaker", choices=PARENTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible mystery pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.culprit:
        project = PROJECTS[args.project]
        culprit = SUSPECTS[args.culprit]
        if (args.project, args.culprit) not in valid_combos():
            raise StoryError(explain_rejection(project, culprit))

    combos = [
        combo for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.culprit is None or combo[1] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, culprit_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caretaker = args.caretaker or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        project=project_id,
        culprit=culprit_id,
        detective_name=name,
        detective_gender=gender,
        caretaker=caretaker,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.culprit not in SUSPECTS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if (params.project, params.culprit) not in valid_combos():
        raise StoryError(explain_rejection(PROJECTS[params.project], SUSPECTS[params.culprit]))

    world = tell(
        project_cfg=PROJECTS[params.project],
        culprit_cfg=SUSPECTS[params.culprit],
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        caretaker_type=params.caretaker,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (project, culprit) pairs:\n")
        for project_id, culprit_id in combos:
            print(f"  {project_id:10} {culprit_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
            header = f"### {p.detective_name}: {p.project} mystery ({p.culprit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
