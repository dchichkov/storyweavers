#!/usr/bin/env python3
"""
A standalone detective-style story world combining "particular", "rhyme", "twist", and "kindness"
into a TinyStories-style simulation. The premise: a young detective with a passion for rhymes
follows poetic clues that initially suggest mischief, but ultimately exposes a hidden kindness.
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

# Add shared helpers to path so imports resolve regardless of CWD
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Threshold for embedding effects into narration
THRESHOLD = 0.7

# Meter names that indicate conditions for story beats
CLUE_METER = "clue_solved"
KINDNESS_METER = "kindness_exposed"
PRIDE_METER = "pride_in_rhymes"
CURIOSITY_METER = "curiosity"
REALIZATION_METER = "aha_moment"

# Mess kinds that can appear at a scene
RUST = "rusty"
WRINKLE = "wrinkled"
SPLASH = "splattered"
MESS_KINDS = {RUST, WRINKLE, SPLASH}

# Emotional memes the detective accumulates
DETECTIVE_MEMES = {PRIDE_METER, CURIOSITY_METER, REALIZATION_METER}

# ---------------------------------------------------------------------------
# Entities: characters and evidence items share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"           # "character" | "thing"
    type: str = "thing"           # detective, neighbor, clue, note ...
    label: str = ""               # short noun phrase: "first verse", "rusty hinge"
    phrase: str = ""              # full description
    author: Optional[str] = None  # who wrote poetic lines
    witnessed_by: Optional[str] = None
    region: str = ""              # corner, doorstep, mailbox ...
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"neighbor", "mom"}
        male = {"Sam", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mom": "mom", "dad": "dad"}.get(self.type, self.type)

# ---------------------------------------------------------------------------
# Activity: building a poetic case file
# ---------------------------------------------------------------------------
@dataclass
class Verse:
    id: str
    line: str                  # actual poetic clue: "Where hinge groans, the lock betrays"
    rhyme: str                 # end rhyme token: "strays" | "says" | "ways"
    suspect_clue: str          # what the verse hints at if wrong meaning taken
    kindness_clue: str         # what the verse truly conveys
    tags: set[str] = field(default_factory=set)  # rhyme_slot, hinge, pocket ...

# ---------------------------------------------------------------------------
# Recipient: the one receiving the hidden kindness
# ---------------------------------------------------------------------------
@dataclass
class Recipient:
    id: str
    label: str
    phrase: str
    need: str                   # "bored", "lonely", "stuck"
    plural: bool = False

# ---------------------------------------------------------------------------
# Setting: locations where verses appear
# ---------------------------------------------------------------------------
@dataclass
class Scene:
    id: str
    place: str
    detail: str
    affords_verses: set[str]    # verse ids acceptable here

# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, Any] = {}
        self.step = 0

    # -- entity helpers -----------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def evidence(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.type != "character"]

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
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]  # predictions are silent
        clone.facts = dict(self.facts)
        return clone

# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_solve_clue(world: World) -> list[str]:
    """A revealed verse boosts detective pride and curiosity."""
    det = world.get("Sam")
    out: list[str] = []
    for ent in world.evidence():
        if ent.meters.get(CLUE_METER, 0.0) >= THRESHOLD and ent.witnessed_by == det.id:
            sig = ("clue_solved", ent.id)
            if sig not in world.fired:
                world.fired.add(sig)
                det.memes[PRIDE_METER] += 1.0
                det.memes[CURIOSITY_METER] += 0.5
                out.append(
                    f"{det.pronoun().capitalize()} examined the {ent.label} closely, "
                    f"puzzling over every word."
                )
    return out

def _r_kindness_revealed(world: World) -> list[str]:
    """Exposing hidden kindness raises curiosity further."""
    out: list[str] = []
    for ent in world.evidence():
        if ent.meters.get(KINDNESS_METER, 0.0) >= THRESHOLD:
            sig = ("kindness", ent.id)
            if sig not in world.fired:
                world.fired.add(sig)
                carer = world.get(ent.author)
                carer.memes["gratitude"] += 1.0
                out.append(f"That moment warmed {det.pronoun('object')} heart.")
    return out

def _r_aha(world: World) -> list[str]:
    """The burst of insight when the twist appears."""
    det = world.get("Sam")
    if det.memes.get(REALIZATION_METER, 0.0) >= THRESHOLD:
        sig = ("aha",)
        if sig not in world.fired:
            world.fired.add(sig)
            return ["__aha__"]
    return []

CAUSAL_RULES: list[Rule] = [
    Rule(name="clue_solve", tag="process", apply=_r_solve_clue),
    Rule(name="kindness", tag="emotion", apply=_r_kindness_revealed),
    Rule(name="aha", tag="pivot", apply=_r_aha),
]

def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply rules until nothing new fires."""
    produced: list[str] = []
    while True:
        changed = True
        while changed:
            changed = False
            for rule in CAUSAL_RULES:
                sents = rule.apply(world)
                if sents:
                    changed = True
                    produced.extend(s for s in sents if s != "__aha__")
        if narrate:
            for s in produced:
                world.say(s)
        if "__aha__" in produced:
            return produced
        break
    return produced

# ---------------------------------------------------------------------------
# Constraint helpers -- reasonableness gate
# ---------------------------------------------------------------------------
def compatible_clue(verse_id: str, recipient: Recipient) -> bool:
    """Only certain verses fit a recipient's need tag."""
    VerseDef = VERSES[verse_id]
    return recipient.need in VerseDef.tags or "kindness" in VerseDef.tags

# ---------------------------------------------------------------------------
# Prediction helpers (silent forward simulation)
# ---------------------------------------------------------------------------
def predict_outcome(world: World, verse_id: str, recipient_id: str) -> dict:
    sim = world.copy()
    _investigate_clue(sim, sim.get("Sam"), verse_id, narrate=False)
    return {
        "solved": bool(sim.entities[verse_id].meters.get(CLUE_METER, 0.0) >= THRESHOLD),
        "rhyme_lock": sim.entities[verse_id].phrase.lower().endswith(
            sim.entities[verse_id].get("kind").rhyme),
        "kind_revealed": bool(sim.entities[verse_id].meters.get(KINDNESS_METER, 0.0) >= THRESHOLD),
    }

# ---------------------------------------------------------------------------
# Core screen-play verbs
# ---------------------------------------------------------------------------
def introduce_detective(world: World) -> None:
    world.say(
        f"{world.get('Sam').pronoun().capitalize()} was a particular young sleuth "
        f"who noticed tiny details and loved a perfect rhyme. Nothing escaped "
        f"those sharp little eyes."
    )

def buy_casebook(world: World, neighbor: Entity, detective: Entity) -> None:
    world.say(
        f"One afternoon, {neighbor.id}'s {neighbor.label_word} handed "
        f"{detective.pronoun('object')} a crumpled note and said, "
        f'\"This looks like one of your particular riddles to solve,\"'
    )

def collect_evidence(world: World, detective: Entity, verse_id: str, scene_detail: str) -> None:
    verse = VERSES[verse_id]
    suspect_line = verse.suspect_clue
    world.entities[verse_id].meme["clue_solved"] = 0.0
    world.say(
        f"{detective.pronoun().capitalize()} carefully untangled {verse.phrase} "
        f"tucked into {scene_detail}. "
        f"The words \"{suspect_line}\" jumped out at {detective.id}."
    )

def solve_wrong_hint(world: World, detective: Entity, verse_id: str) -> None:
    verse = VERSES[verse_id]
    world.entities[verse_id].meters[CLUE_METER] = THRESHOLD
    world.entities[verse_id].phrase = verse.suspect_clue
    world.get("Sam").memes[PRIDE_METER] += 1
    propagate(world)
    world.say(
        f"{detective.pronoun().capitalize()} pursed {detective.pronoun('possessive')} lips: "
        f"\"A groove like that on {verse.label}? That has to be {verse.suspect_clue}. "
        f"Case closed!\""
    )

def crack_twist(world: World, detective: Entity, verse_entity: Entity, recipient: Entity) -> bool:
    twist_found = "twist" in verse_entity.tags or "kindness" in verse_entity.tags
    verse_entity.meters[REALIZATION_METER] = THRESHOLD * 2.0
    verse_entity.meters[KINDNESS_METER] = THRESHOLD * 2.0
    world.get("Sam").memes[REALIZATION_METER] = THRESHOLD
    world.para()
    world.say(
        f"Then Sam frowned. {detective.pronoun().capitalize()} read the clue backward: "
        f"\"{verse_entity.kindness_clue}\"."
    )
    world.say(
        f'\"This isn\'t about mischief at all,\" {detective.pronoun()} muttered, '
        f"\"it\'s a secret kindness meant for {recipient.id}.\""
    )
    world.say(
        f"Under the rust and grime lay hidden kindness: {recipient.phrase} "
        f"had felt lonely until today."
    )
    return twist_found

def celebrate_kindness(world: World, neighbor: Entity, recipient: Entity) -> None:
    world.say(
        f"{neighbor.pronoun().capitalize()} {neighbor.label_word} gasped with delight. "
        f'\"So THAT\'s what {recipient.label} really needed!\" {neighbor.pronoun()} exclaimed.'
    )
    world.say(
        f"{world.get('Sam').pronoun()} beamed. "
        f"All those particular rhymes had been guiding them toward a good deed."
    )

# ---------------------------------------------------------------------------
# Screen-play driver
# ---------------------------------------------------------------------------
def solve_case(scene: Scene, verse_id: str, recipient_cfg: Recipient,
              name: str = "Sam", neighbor_name: str = "Olive") -> World:
    world = World(scene)
    detective = world.add(Entity(
        id=name, kind="character", type="detective",
        label="Sam", phrase="a young detective named Sam",
    ))
    neighbor = world.add(Entity(
        id=neighbor_name, kind="character", type="neighbor",
        traits=["observant"], label_word="neighbor",
    ))
    verse = VERSES[verse_id]
    verse_entity = world.add(Entity(
        id=verse_id, kind="thing", type="verse",
        label=verse.label, phrase=verse.line, author=neighbor.id, region=scene.detail,
    ))
    recipient = world.add(Entity(
        id="recipient", kind="thing", type="recipient",
        label=recipient_cfg.label, phrase=recipient_cfg.phrase,
        need=recipient_cfg.need, plural=recipient_cfg.plural,
    ))

    # Act 1: setup the case and the particular detective lens
    world.para()
    introduce_detective(world)
    world.para()
    buy_casebook(world, neighbor, detective)

    # Act 2: follow the rhyming clue, reach wrong but reasonable conclusion
    world.para()
    collect_evidence(world, detective, verse_id, scene.detail)
    solve_wrong_hint(world, detective, verse_id)
    false_outcome = predict_outcome(world, verse_id, "recipient")
    if not false_outcome["kind_revealed"]:
        return world   # story ends at the false closure

    # Act 3: the twist appears; hidden kindness is exposed
    world.para()
    if crack_twist(world, detective, verse_entity, recipient):
        world.facts["twist"] = True
    world.para()
    celebrate_kindness(world, neighbor, recipient)

    # Record facts for Q&A
    world.facts.update(
        detective=detective, recipient=recipient, neighbor=neighbor,
        verse=verse, scene=scene, twist_found=twist_found,
    )
    return world

# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
VERSES = {
    # Hinge rhymes
    "hinge_clue": Verse(
        id="hinge_clue", line="Where hinge groans, the lock betrays",
        rhyme="strays", suspect_clue="someone pried the pantry door",
        kindness_clue="someone left warm jam when hall light stayed",
        tags={"rhyme_slant", "hinge", "pantry"},
    ),
    # Rusty patterns
    "rust_note": Verse(
        id="rust_note", line="Scraped the rail; the ladder’s rust betray",
        rhyme="betray", suspect_clue="vandal scraped then laughed away",
        kindness_clue="kind neighbor scraped off rusty taint",
        tags={"rhyme_exact", "rusty", "rail"},
    ),
    # Wrinkled clues
    "pocket_crumple": Verse(
        id="pocket_crumple", line="Left the note in pocket, neatly wrinkled so",
        rhyme="so", suspect_clue="tiny hands stole snack money though",
        kindness_clue="left quarters when coin purse felt slow",
        tags={"rhyme_exact", "pocket", "coins"},
    ),
    # Splattered evidence
    "porch_puddle": Verse(
        id="porch_puddle", line="Painted the porch milk splashed round the brim",
        rhyme="brim", suspect_clue="someone tipped bucket over rim",
        kindness_clue="someone swept milk that nearly did swim",
        tags={"rhyme_true", "porch", "cleanup"},
    ),
}

SCENES = {
    "porch": Scene(
        id="porch", place="the porch", detail="peeling blue bench",
        affords_verses={"porch_puddle"},
    ),
    "pantry": Scene(
        id="pantry", place="the pantry", detail="warped pantry door",
        affords_verses={"hinge_clue"},
    ),
    "rail": Scene(
        id="rail", place="the backyard rail", detail="bent iron ladder",
        affords_verses={"rust_note"},
    ),
    "bench": Scene(
        id="bench", place="the garden bench", detail="wrinkled jacket pocket",
        affords_verses={"pocket_crumple"},
    ),
}

# Recipients who benefit from hidden kindness through poetic guidance
RECIPIENTS = {
    "lonely_jane": Recipient(
        id="Jane", label="Jane", phrase="old rocking chair on the porch",
        need="lonely",
    ),
    "bored_lucy": Recipient(
        id="Lucy", label="Lucy", phrase="pocket change hidden deep",
        need="bored", plural=True,
    ),
    "stuck_old_ben": Recipient(
        id="Ben", label="Ben's slippers", phrase="splattered rain boots",
        need="stuck",
    ),
}

# Names and traits
GIRL_NAMES = ["Olive", "Mae", "Lila", "Clara", "June"]
TRAITS = ["observant", "curious", "particular"]

# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    scene: str
    verse: str
    recipient: str
    name: str
    neighbor: str
    trait: str = "observant"
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# Q&A generation – three separate, story-grounded sets
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    det, verse, scene, recip = facts["detective"], facts["verse"], facts["scene"], facts["recipient"]
    return [
        f"Write a 3-to-5-paragraph detective tale for young readers around the theme 'particular rhymes reveal hidden kindness'. "
        f"Include the exact phrase '{verse.line}'.",
        f"Tell a simple story about {det.id}, a {det.traits[0]} {det.type} who follows rhyming clues to help {recip.phrase}. "
        f"End with an image explaining what changed due to the kindness.",
    ]

def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    det, verse, scene, recip = facts["detective"], facts["verse"], facts["scene"], facts["recipient"]
    prize_word = recip.label if " " not in recip.label else "the " + recip.label
    kindness_descr = "a hidden act of kindness" if facts.get("twist_found") else "a kind surprise"
    muddled_word = verse.suspect_clue.split(",")[0] if "," in verse.suspect_clue else verse.suspect_clue
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who was the particular detective in this rhyme-guided case on {scene.place}?"
            ),
            answer=(
                f"The particular sleuth was {det.id}, a {det.type} who treasured "
                f"rhyming clues and solved tiny mysteries everywhere."
            ),
        ),
        QAItem(
            question=(
                f"What small clue did {det.id} first suspect after examining {verse.label} near {scene.detail}?"
            ),
            answer=(
                f"At first, {det.id} suspected {muddled_word}. "
                f"The rhyme misled {det.pronoun()} toward what seemed like mischief."
            ),
        ),
        QAItem(
            question=(
                f"Who really benefited from the hidden verses that {det.id} found?"
            ),
            answer=(
                f"The hidden kindness reached {recip.id} in the form of {recip.phrase}, "
                f"who needed exactly that secret help."
            ),
        ),
    ]
    # Embedded reasoning about the twist
    if facts.get("twist_found"):
        qa.append(QAItem(
            question=(
                f"Why was the first guess about {muddled_word} actually a twist "
                f"toward kindness?"
            ),
            answer=(
                f"Sam realized the same rhymes also delivered a kindness clue: "
                f"{verse.kindness_clue}. Both messages used identical rhymes but pushed in opposite "
                f"directions: mischief vs. secret care. Once {det.id} read the kindness clue, "
                f"the hidden purpose became clear."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did following the particular rhymes bring about a happy ending "
                f"for {recip.id}?"
            ),
            answer=(
                f"Sam’s particular eye for rhymes guided them past the misleading "
                f"suspect line to the true kindness message. Once the twist surfaced, "
                f"{recip.id} felt acknowledged and no longer {recip.need}."
            ),
        ))
    return qa

KNOWLEDGE = {
    "rhyme": [
        ("What is a slant rhyme?",
         "A slant rhyme uses similar but not identical sounds at the end of lines, "
         "like 'moon' and 'on'."),
    ],
    "kindness": [
        ("What does it mean to leave something for someone?",
         "Leaving something for someone on purpose shows you thought of them "
         "and hoped they’d feel cared for."),
    ],
    "detective": [
        ("What do detectives do?",
         "Detectives watch small details, follow clues, and piece together what "
         "happened so they can explain the story behind the mystery."),
    ],
}

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set()
    if "twist" in world.facts:
        tags.add("twist")
    for e in world.evidence():
        tags.update(e.tags)
    tags.add("rhyme")
    qa: list[QAItem] = []
    for key in ["rhyme", "kindness", "detective"]:
        if key in tags or key == "rhyme":  # always show rhyme knowledge
            for q, a in KNOWLEDGE[key]:
                qa.append(QAItem(question=q, answer=a))
    return qa

def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== Child-level world knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# ASP Twin – declarative gatekeeping
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A clue is valid if it affords a kindness hidden inside its rhyming words.
valid_story(Place, Verse, Recip, Name, Neighbor) :-
    scene(Place, _, Detail, Verses),
    member(Verse, Verses),
    member_tag(Verse, RecipNeed),
    recipient(Recip, RecipNeed),
    first_line(Verse, Line),
    kind_clue(Verse, Line, Hidden),
    poet(Neighbor).

% Detectives are named Sam or Olive.
detective(Name) :- Name = "Sam"; Name = "Olive".

% Neighbors are any other character present.
poet(P) :- character(P), P != "Sam", P != "Olive".

% Any scene may host its allowed verses.
may_host(Place, Verse) :- scene(Place, _, _, Verses), member(Verse, Verses).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, sc in SCENES.items():
        lines.append(asp.fact("scene", sid, sc.place, sc.detail, sorted(sc.affords_verses)))
        lines.append(asp.fact("setting", sid, sc.id))
    for vid, v in VERSES.items():
        lines.append(asp.fact("verse", vid, v.line))
        lines.append(asp.fact("first_line", vid, v.line))
        lines.append(asp.fact("has_word", vid, "rhyme"))
        for t in sorted(v.tags):
            lines.append(asp.fact("tagged", vid, t))
        lines.append(asp.fact("kind_clue", vid, v.line, v.kindness_clue))
        lines.append(asp.fact("suspect_clue", vid, v.suspect_clue))
    for rid, r in RECIPIENTS.items():
        lines.append(asp.fact("recipient", rid, r.need))
        for need in [r.need]:
            lines.append(asp.fact("needs", rid, need))
    for name in GIRL_NAMES + ["Sam", "Olive"]:
        lines.append(asp.fact("character", name))
    for name in GIRL_NAMES:
        lines.append(asp.fact("name_girl", name))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    if not model:
        return []
    atoms = asp.atoms(model, "valid_story")
    return sorted(set(atoms))

def asp_verify() -> int:
    py_set = set()
    for sc in SCENES.values():
        for vid in sc.affords_verses:
            for rid, r in RECIPIENTS.items():
                if compatible_clue(vid, r):
                    for name in GIRL_NAMES + ["Sam", "Olive"]:
                        for neigh in GIRL_NAMES:
                            if name == "Sam" and "Sam" != name:
                                continue
                            if name == "Olive" and name != "Olive":
                                continue
                            py_set.add((sc.id, vid, rid, name, neigh))
    clingo_set = set(asp_valid_stories())
    if py_set == clingo_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} compatible stories).")
        return 0
    print("Mismatch between ASP and Python logic:")
    if clingo_set - py_set:
        print("  only in ASP:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in Python:", sorted(py_set - clingo_set))
    return 1

# ---------------------------------------------------------------------------
# Standard CLI interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A detective tale of particular rhymes, hidden twists, and secret kindnesses")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--verse", choices=VERSES)
    ap.add_argument("--recipient", choices=RECIPIENTS)
    ap.add_argument("--name", choices=GIRL_NAMES + ["Sam", "Olive"])
    ap.add_argument("--neighbor", choices=GIRL_NAMES)
    ap.add_argument("-n", type=int, default=1, help="number of cases to generate")
    ap.add_argument("--seed", type=int, default=None, help="random seed for reproducibility")
    ap.add_argument("--all", action="store_true", help="show curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model trace")
    ap.add_argument("--qa", action="store_true", help="include three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="print ASP-valid stories")
    ap.add_argument("--verify", action="store_true", help="validate ASP gate")
    ap.add_argument("--show-asp", action="store_true", help="dump full ASP program")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.verse and args.recipient and not compatible_clue(args.verse, RECIPIENTS[args.recipient]):
        raise StoryError(
            f"Verse '{args.verse}' cannot match recipient '{args.recipient}' need: "
            f"{RECIPIENTS[args.recipient].need}."
        )
    choices = []
    for sc_id in (args.scene.split(",") if args.scene else SCENES):
        sc = SCENES[sc_id]
        for v_id in sc.affords_verses:
            for r_id in RECIPIENTS:
                if compatible_clue(v_id, RECIPIENTS[r_id]):
                    for name in GIRL_NAMES + ["Sam", "Olive"]:
                        for n in GIRL_NAMES:
                            choices.append((sc_id, v_id, r_id, name, n))
    if not choices:
        raise StoryError("(No valid scene–clue–recipient combination found.)")
    sc_id, v_id, r_id, name, neighbor = rng.choice(choices)
    return StoryParams(
        scene=sc_id, verse=v_id, recipient=r_id, name=name, neighbor=neighbor,
        trait=rng.choice(TRAITS), seed=args.seed if args.seed is not None else rng.randrange(2**31),
    )

def generate(params: StoryParams) -> StorySample:
    scene = SCENES[params.scene]
    world = solve_case(
        scene,
        params.verse,
        RECIPIENTS[params.recipient],
        params.name,
        params.neighbor,
    )
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
    if trace and sample.world:
        lines = ["--- world state ---"]
        for eid, ent in sample.world.entities.items():
            ms = {k: v for k, v in ent.meters.items() if v >= 0.01}
            mems = {k: v for k, v in ent.memes.items() if v >= 0.01}
            bits = []
            if ms:
                bits.append(f"meters={ms}")
            if mems:
                bits.append(f"memes={mems}")
            lines.append(f"  {eid:12} ({ent.type:9}) {' '.join(bits)}")
        lines.append(f"  fired_rules={sorted(set(n for n,_ in sample.world.fired))}")
        print("\n".join(lines))
    if qa:
        print("\n" + format_qa(sample))

# Curated selection used by --all
CURATED = [
    StoryParams(scene="porch", verse="porch_puddle", recipient="lonely_jane", name="Sam", neighbor="Olive"),
    StoryParams(scene="pantry", verse="hinge_clue", recipient="lonely_jane", name="Sam", neighbor="Clara"),
    StoryParams(scene="rail", verse="rust_note", recipient="bored_lucy", name="Olive", neighbor="Mae"),
    StoryParams(scene="bench", verse="pocket_crumple", recipient="stuck_old_ben", name="Sam", neighbor="June"),
]

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible detective stories:\n")
        for sc, v, r, det, nb in stories[:50]:
            print(f"  {det} at {sc} with verse '{v}' toward {r}  (neighbor {nb})")
        return

    base_seed = args.seed or random.randrange(2**31 - 1)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        trials = 0
        while len(samples) < args.n and trials < max(args.n * 30, 100):
            trials += 1
            seed = base_seed + trials
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
            header = f"### {p.name} at {SCENES[p.scene].place}: {VERSES[p.verse].line[:25]}..."
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
