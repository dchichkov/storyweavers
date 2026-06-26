#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/jettison_transcription_mystery_to_solve_animal_story.py
=============================================================================================================================

A standalone *story world* sketch for "The Jettison Transcription" tale
and close, constraint-checked variations of it.

Initial story (used to build a world model):
---
Once upon a time, in a quiet meadow beside a little fishing pond, there lived
a tidy brown badger named Bramble who worked as the meadow's letter keeper.
Every morning he would walk to the stone post at the water's edge and read the
old paper trail that floated in on the current -- notes from otters, lists
from frogs, and the long weather report that the wind dropped into the reeds.
Bramble could read every scratch, and he kept a careful transcription of each
one in a small blue notebook tucked under his vest.

One bright morning a strange thing happened. The current brought in a sealed
tin canister, the kind that ships use when they jettison their papers at sea.
Inside the canister was a single folded page, half-printed and half-handed,
with a fat ink blot where the signature should have been. The page was a clue
to a mystery everyone in the meadow had been whispering about: who had been
moving the pond stones into a new ring in the middle of the night?

Bramble set the tin on the post, smoothed the page flat, and read it three
times. The transcription said: "Two went down, three went back. The ring is
built in the order of paws." He chewed his pencil, then asked his friends to
come and look. Owl arrived first, peering through small round spectacles. Then
came Otter, who still had pond water dripping from her whiskers. Toad hopped
along, leaving damp footprints on the path.

Together they walked to the pond and counted the ring stones. Bramble checked
his transcription again and again. At last Owl said, "Look at the mud on the
third stone." On the back of the third stone, pressed deep into the clay, was
the print of a single broad paw -- the kind that only belongs to Toad. Toad's
eyes went wide and his green cheeks turned pink. "I just like the way they
line up," he said softly.

Owl folded the page so the ink blot was hidden, and Bramble closed his blue
notebook. "The mystery is solved," said Owl, "and the meadow can sleep again."
They all walked home together as the current carried the empty tin back out
to sea.

Causal state updates:
---
    object carries a transcription       -> clue.<read> += 1, clue.<readable> += 1
    clue.ink_blot present               -> clue.<legible> stays low, clue.<doubt> += 1
    helper examines a clue              -> helper.<focus> += 1
    helper's focus crosses the threshold -> suspect.<suspect> += 1
    suspect identified by paw print      -> suspect.<caught> += 1, suspect.<embarrass> += 1
    mystery resolved                    -> actor.<joy> += 1, meadow.<safe> += 1

Scripted social/emotional beats:
---
    helper called in                    -> meadow.<attention> += 1
    ink blot hides a signature          -> clue.<tampered> += 1
    gentle admission                    -> suspect.<calm> += 1 ; meadow.<kindness> += 1
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
# (``python storyworlds/worlds/.../jettison_transcription_mystery_to_solve_animal_story.py``):
# add the package dir (storyworlds/) to the path so ``results`` resolves.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # badger, owl, otter, toad, tin, page, ...
    label: str = ""                # short reference, e.g. "tin canister"
    phrase: str = ""               # full noun phrase, e.g. "a sealed tin canister"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    role: str = ""                 # keeper, helper, suspect, witness
    plural: bool = False
    # Two numeric dimensions, treated uniformly (cf. story.py memeplex model):
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"vixen", "doe", "hen", "she-bear", "owl", "otter"}
        male = {"badger", "boar", "buck", "toad", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"owl": "owl", "otter": "otter", "toad": "toad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the meadow"
    afford: str = ""              # what evidence the place produces
    note: str = ""                # one-line atmospheric sentence


@dataclass
class Container:
    """The thing that was jettisoned and washed up. It carries a clue."""
    id: str
    label: str
    phrase: str
    washed_up: bool = True
    ink_blot: bool = False        # the signature is hidden
    has_order: bool = True        # the clue mentions a sequence


@dataclass
class Clue:
    """A transcription found inside the container -- the puzzle's text."""
    id: str
    text: str
    reveals: str                  # "paw" | "paw_size" | "order"
    ink_blot: bool = False


@dataclass
class Helper:
    """An animal called in to read the clue alongside the keeper."""
    type: str            # owl, otter, fox
    label: str
    prep: str            # "put on small round spectacles"
    trait: str
    phrase: str          # full noun phrase


@dataclass
class Suspect:
    """An animal whose paws could match the print on the pond stone."""
    type: str
    label: str
    paw: str             # "broad", "narrow", "webbed", "small"
    admits: bool = True


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]

    # -- entity helpers -----------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def things(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "thing"]

    def find(self, type_name: str) -> Optional[Entity]:
        for e in self.entities.values():
            if e.type == type_name:
                return e
        return None

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_transcription(world: World) -> list[str]:
    """A container holds a clue -> the keeper reads it (legibility tracked)."""
    out: list[str] = []
    keeper = world.find("keeper")
    if keeper is None:
        return out
    for cont in world.things():
        if cont.type != "container":
            continue
        for clue in world.things():
            if clue.type != "clue":
                continue
            sig = ("transcription", keeper.id, clue.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            clue.meters["read"] += 1
            if not clue.ink_blot:
                clue.meters["legible"] += 1
            keeper.meters["focus"] += 1
            out.append(f"{keeper.id} read the transcription in {cont.label}.")
    return out


def _r_doubt(world: World) -> list[str]:
    """An ink-blot clue undermines certainty -> the keeper doubts the signature."""
    out: list[str] = []
    keeper = world.find("keeper")
    if keeper is None:
        return out
    for clue in world.things():
        if clue.type != "clue" or not clue.ink_blot:
            continue
        if clue.meters["doubt"] >= THRESHOLD:
            continue
        sig = ("doubt", keeper.id, clue.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        clue.meters["doubt"] += 1
        keeper.memes["doubt"] += 1
        out.append(f"The ink blot hid the signature on the clue.")
    return out


def _r_helper_examines(world: World) -> list[str]:
    """A helper who arrives with focus crosses the threshold -> the meadow pays attention."""
    out: list[str] = []
    for helper in world.characters():
        if helper.role != "helper":
            continue
        if helper.meters["focus"] < THRESHOLD:
            continue
        sig = ("attention", helper.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        helper.memes["attention"] += 1
        out.append(f"{helper.label} joined the pond and looked carefully at the ring.")
    return out


def _r_suspect_caught(world: World) -> list[str]:
    """A suspect identified by paw print -> caught + a small embarrassment."""
    out: list[str] = []
    keeper = world.find("keeper")
    if keeper is None:
        return out
    for suspect in world.characters():
        if suspect.role != "suspect":
            continue
        if suspect.meters["caught"] >= THRESHOLD:
            continue
        if not keeper.memes.get("suspect"):
            continue
        sig = ("caught", suspect.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        suspect.meters["caught"] += 1
        suspect.memes["embarrass"] += 1
        out.append(f"{suspect.label}'s cheeks turned pink.")
    return out


def _r_resolved(world: World) -> list[str]:
    """Mystery solved when the keeper + a helper agree on the suspect."""
    out: list[str] = []
    keeper = world.find("keeper")
    if keeper is None:
        return out
    any_helper = any(h.role == "helper" and h.memes.get("attention", 0) >= THRESHOLD
                     for h in world.characters())
    any_caught = any(s.role == "suspect" and s.meters["caught"] >= THRESHOLD
                     for s in world.characters())
    if not (any_helper and any_caught):
        return out
    sig = ("resolved", keeper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    keeper.memes["joy"] += 1
    keeper.memes["doubt"] = 0.0
    for s in world.characters():
        if s.role == "helper":
            s.memes["joy"] += 1
    out.append("The mystery was solved.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="transcription", tag="physical", apply=_r_transcription),
    Rule(name="doubt", tag="social", apply=_r_doubt),
    Rule(name="helper_examines", tag="social", apply=_r_helper_examines),
    Rule(name="suspect_caught", tag="social", apply=_r_suspect_caught),
    Rule(name="resolved", tag="social", apply=_r_resolved),
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
# Constraint helpers -- what makes a *reasonable* mystery and a *reasonable*
# fix.
# ---------------------------------------------------------------------------
def helper_sees_clue(helper: Helper, clue: Clue) -> bool:
    """Can this helper actually read a transcription? Fox cannot -- she is shy
    of ink; owl and otter can.  This is the readability gate."""
    return helper.type in {"owl", "otter"}


def paw_matches(suspect: Suspect, clue: Clue) -> bool:
    """Does this suspect's paw type match what the clue reveals?"""
    return clue.reveals in {"paw", suspect.paw}


def puzzle_holds(container: Container, clue: Clue) -> bool:
    """A puzzle must have an order hint unless the ink blot already supplies
    the twist; otherwise there is nothing to solve."""
    return container.has_order or clue.ink_blot


def select_helper(suspect_type: str) -> Optional[Helper]:
    """A helper who can read the clue AND whose presence leads the meadow to
    pay attention.  Owl fits every case; otter fits when the suspect is not
    an otter (avoids double identity noise)."""
    for h in HELPERS:
        if h.type == "owl":
            return h
        if h.type == "otter" and suspect_type != "otter":
            return h
    return HELPERS[0]


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def setting_detail(setting: Setting) -> str:
    if setting.note:
        return setting.note
    return f"{setting.place.capitalize()} was quiet, and the current stilled at the post."


def keeper_introduce(world: World, keeper: Entity) -> None:
    trait = next((t for t in keeper.traits if t != "tidy"), "tidy")
    world.say(
        f"{keeper.id} was a {trait} {keeper.type} who kept a careful "
        f"transcription of every note the current carried to {world.setting.place}."
    )


def keeper_arrives(world: World, keeper: Entity) -> None:
    world.say(
        f"Every morning, {keeper.id} walked to the stone post at the water's "
        f"edge and read the paper trail that floated in on the current."
    )


def jettison_arrives(world: World, container: Entity) -> None:
    word = "washed" if container.washed_up else "tumbled"
    world.say(
        f"One bright morning the current brought in a sealed {container.label} -- "
        f"the kind that ships use when they jettison their papers at sea -- "
        f"and it {word} up against the post."
    )


def clue_revealed(world: World, keeper: Entity, clue: Entity,
                  container: Entity, helper: Helper) -> None:
    if clue.ink_blot:
        world.say(
            f"Inside the {container.label} was a single folded page, half-printed "
            f"and half-handed, with a fat ink blot where the signature should have been."
        )
    else:
        world.say(
            f"Inside the {container.label} was a single folded page, half-printed "
            f"and half-handed, with the signature clearly written at the bottom."
        )
    world.say(f'The page read: "{clue.label}."')


def helper_called(world: World, keeper: Entity, helper: Helper) -> Entity:
    h = world.add(Entity(
        id=f"H{helper.type}", kind="character", type=helper.type,
        label=helper.label, role="helper", traits=[helper.trait],
    ))
    h.meters["focus"] += 1
    world.say(f"{keeper.id} asked his friends to come and look.")
    world.say(f"{helper.label} arrived first, {helper.prep}.")
    propagate(world, narrate=False)
    return h


def walk_to_pond(world: World, keeper: Entity, helper: Entity) -> None:
    world.para()
    world.say(
        f"Together they walked to the pond and counted the ring stones, "
        f"while {keeper.id} checked the transcription again and again."
    )


def helper_examines(world: World, helper: Entity, clue: Entity) -> None:
    if helper.type == "owl":
        world.say(
            f'At last {helper.label} said, "Look at the mud on the third stone."'
        )
    elif helper.type == "otter":
        world.say(
            f'At last {helper.label} said, "Look at the print on the third stone -- '
            f"it is still damp."
        )
    else:
        world.say(
            f'At last {helper.label} said, "There is a paw print on the third stone."'
        )
    keeper = world.find("keeper")
    if keeper is not None:
        keeper.memes["suspect"] += 1
    propagate(world, narrate=False)


def paw_print(world: World, suspect: Entity) -> None:
    paw = suspect.memes.get("paw", "broad")
    world.say(
        f"On the back of the third stone, pressed deep into the clay, was the "
        f"print of a single {paw} paw."
    )


def suspect_admits(world: World, suspect: Entity) -> None:
    if suspect.admits:
        suspect.memes["calm"] += 1
        world.say(
            f"{suspect.id}'s eyes went wide and {suspect.pronoun('possessive')} "
            f'cheeks turned pink. "I just like the way they line up," '
            f"{suspect.pronoun()} said softly."
        )
    else:
        world.say(
            f"{suspect.id} looked away, but said nothing more, and the ring "
            f"stayed just as it was."
        )


def mystery_solved(world: World, keeper: Entity, helper: Helper) -> None:
    world.para()
    world.say(
        f'{helper.label} folded the page so the ink blot was hidden, and '
        f"{keeper.id} closed his blue notebook."
    )
    world.say(
        f'"The mystery is solved," said {helper.label}, "and the meadow can sleep again."'
    )


def walk_home(world: World, keeper: Entity) -> None:
    world.say(
        f"They all walked home together as the current carried the empty tin "
        f"back out to sea."
    )


# ---------------------------------------------------------------------------
# The screenplay: coarse three-act shape, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, container: Container, clue: Clue,
         suspect: Suspect, helper: Helper,
         keeper_name: str = "Bramble", keeper_type: str = "badger",
         keeper_traits: Optional[list[str]] = None) -> World:
    world = World(setting)

    keeper = world.add(Entity(
        id=keeper_name, kind="character", type=keeper_type,
        traits=["tidy"] + (keeper_traits or ["patient", "careful"]),
        role="keeper",
    ))
    cont = world.add(Entity(
        id="container", kind="thing", type="container",
        label=container.label, phrase=container.phrase,
    ))
    cl = world.add(Entity(
        id="clue", kind="thing", type="clue",
        label=clue.text, phrase=clue.text,
    ))
    cl.ink_blot = clue.ink_blot
    sus = world.add(Entity(
        id=suspect.label, kind="character", type=suspect.type,
        label=suspect.label, role="suspect",
    ))
    sus.memes["paw"] = suspect.paw

    # Act 1 -- setup: the keeper, the setting, and the jettisoned container.
    keeper_introduce(world, keeper)
    keeper_arrives(world, keeper)
    world.para()
    jettison_arrives(world, cont)
    clue_revealed(world, keeper, cl, cont, helper)

    # Act 2 -- investigation: helper called, they walk, the paw print appears.
    world.para()
    h = helper_called(world, keeper, helper)
    walk_to_pond(world, keeper, h)
    helper_examines(world, h, cl)
    paw_print(world, sus)
    suspect_admits(world, sus)
    propagate(world, narrate=False)

    # Act 3 -- resolution: the meadow agrees, the current carries the tin home.
    mystery_solved(world, keeper, helper)
    walk_home(world, keeper)

    # Record facts for the Q&A generators (grounded in the simulated world).
    world.facts.update(
        keeper=keeper, helper=helper, suspect=sus, container=container,
        clue=clue, setting=setting, ink_blot=clue.ink_blot,
        resolved=True, paw=suspect.paw,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(
        place="the meadow",
        afford="papers",
        note="The meadow was quiet, and the current stilled at the post.",
    ),
    "riverbank": Setting(
        place="the riverbank",
        afford="papers",
        note="The riverbank smelled of reeds, and the post leaned toward the flow.",
    ),
    "pond_edge": Setting(
        place="the pond edge",
        afford="papers",
        note="The pond edge was ringed with smooth flat stones, and the water barely moved.",
    ),
    "harbor": Setting(
        place="the little harbor",
        afford="papers",
        note="The little harbor held a rope coil and a tin float, and the tide came in slow.",
    ),
}

CONTAINERS = {
    "tin": Container(
        id="tin", label="tin canister", phrase="a sealed tin canister",
        washed_up=True, ink_blot=True, has_order=True,
    ),
    "bottle": Container(
        id="bottle", label="glass bottle", phrase="a stoppered glass bottle",
        washed_up=True, ink_blot=False, has_order=True,
    ),
    "box": Container(
        id="box", label="small wooden box", phrase="a small wooden box with a tight lid",
        washed_up=True, ink_blot=False, has_order=True,
    ),
    "scroll": Container(
        id="scroll", label="waterproof scroll", phrase="a waterproof scroll wound with twine",
        washed_up=False, ink_blot=False, has_order=True,
    ),
}

CLUES = {
    "two_three": Clue(
        id="two_three",
        text="Two went down, three went back. The ring is built in the order of paws.",
        reveals="paw", ink_blot=True,
    ),
    "broad": Clue(
        id="broad",
        text="The print on the third stone was made by a broad paw, and only one animal has that.",
        reveals="broad", ink_blot=False,
    ),
    "order": Clue(
        id="order",
        text="Five stones, five moves, and only the order can tell who did it.",
        reveals="paw", ink_blot=False,
    ),
    "webbed": Clue(
        id="webbed",
        text="A webbed print lay on the clay, half-hidden by the morning dew.",
        reveals="webbed", ink_blot=False,
    ),
}

HELPERS = [
    Helper(
        type="owl", label="Owl", prep="peering through small round spectacles",
        trait="wise", phrase="Owl",
    ),
    Helper(
        type="otter", label="Otter", prep="with pond water still dripping from her whiskers",
        trait="quick", phrase="Otter",
    ),
    Helper(
        type="fox", label="Fox", prep="with her brush held close",
        trait="quiet", phrase="Fox",
    ),
]

SUSPECTS = {
    "toad": Suspect(type="toad", label="Toad", paw="broad", admits=True),
    "otter": Suspect(type="otter", label="Otter", paw="webbed", admits=True),
    "vole": Suspect(type="vole", label="Vole", paw="small", admits=True),
    "beaver": Suspect(type="beaver", label="Beaver", paw="broad", admits=False),
}

KEEPER_NAMES = ["Bramble", "Thistle", "Rowan", "Hazel", "Brock", "Merrick"]
KEEPER_TRAITS = ["patient", "careful", "tidy", "gentle", "earnest"]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    """(place, container, clue, suspect, helper) tuples that pass the constraints."""
    combos = []
    for place in SETTINGS:
        for cont_id, cont in CONTAINERS.items():
            for clue_id, clue in CLUES.items():
                if not puzzle_holds(cont, clue):
                    continue
                for sus_id, sus in SUSPECTS.items():
                    if not paw_matches(sus, clue):
                        continue
                    for helper in HELPERS:
                        if not helper_sees_clue(helper, clue):
                            continue
                        combos.append((place, cont_id, clue_id, sus_id, helper.type))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    container: str
    clue: str
    suspect: str
    helper: str
    name: str
    keeper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "jettison": [(
        "What does it mean to jettison something?",
        "To jettison something means to throw it overboard or let it go, usually "
        "to make a ship lighter or to get rid of papers that are no longer needed.",
    )],
    "transcription": [(
        "What is a transcription?",
        "A transcription is a written copy of something, made carefully so that "
        "every word from the original is recorded in the new page.",
    )],
    "ink_blot": [(
        "Why does an ink blot hide a signature?",
        "An ink blot is a wet mark from spilled ink. When it lands on a "
        "signature, it spreads over the name and makes the writing hard to read.",
    )],
    "paw_print": [(
        "How can a paw print help solve a mystery?",
        "A paw print is left in soft mud or clay. The size and shape of the "
        "pads and toes tell which animal walked there, which can show who was "
        "at a place.",
    )],
    "ring": [(
        "What is a ring of stones?",
        "A ring of stones is a circle made by laying flat stones edge to edge. "
        "It can be used as a marker, a path, or a quiet place to sit.",
    )],
    "keeper": [(
        "What does a letter keeper do?",
        "A letter keeper collects the notes and pages that arrive in a place, "
        "reads them carefully, and writes a clean copy so the message is not lost.",
    )],
    "owl": [(
        "Why are owls good at solving puzzles?",
        "Owls have very sharp eyes and they think slowly before they speak. "
        "They notice small details that others miss, which helps them put clues together.",
    )],
    "otter": [(
        "What do otters know about water?",
        "Otters spend much of their day in water. They know how currents move "
        "things and how a wet print can still be read after it is left.",
    )],
    "toad": [(
        "What kind of paws does a toad have?",
        "A toad has broad front paws with short toes. The print is wider than "
        "it is long, and the toe marks are small and close together.",
    )],
}
KNOWLEDGE_ORDER = ["jettison", "transcription", "ink_blot", "paw_print",
                   "ring", "keeper", "owl", "otter", "toad"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    keeper, helper, suspect = f["keeper"], f["helper"], f["suspect"]
    cont, clue = f["container"], f["clue"]
    place = world.setting.place
    return [
        f'Write a short animal story for a 4-to-6-year-old on the theme "a '
        f'mystery to solve" that uses the word "jettison" and includes a transcription.',
        f"Tell a gentle story set in {place} where a {keeper.type} named "
        f"{keeper.id} finds a {cont.phrase} with a transcription inside, and "
        f"a {helper.type} helps {keeper.pronoun('object')} read it and find "
        f"the {suspect.type} who moved the stones.",
        f'Write a cozy story with the word "transcription" in which an animal '
        f"keeper uses a clue from a jettisoned container to solve a small mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    keeper, helper, suspect = f["keeper"], f["helper"], f["suspect"]
    cont, clue = f["container"], f["clue"]
    pos = keeper.pronoun("possessive")
    sub = keeper.pronoun("subject")
    obj = keeper.pronoun("object")
    place = world.setting.place
    trait = next((t for t in keeper.traits if t != "tidy"), "patient")
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {keeper.id} lives at {place} "
                f"and finds a {cont.label}?"
            ),
            answer=(
                f"It is about a {trait} {keeper.type} named {keeper.id} who "
                f"keeps a careful transcription of every note the current "
                f"carries to {place}."
            ),
        ),
        QAItem(
            question=(
                f"What kind of {cont.label} did the current bring to {place} "
                f"for {trait} {keeper.id} to read?"
            ),
            answer=(
                f"The current brought a {cont.phrase}, the kind ships use when "
                f"they jettison their papers at sea, and inside was a single "
                f"folded page with a transcription."
            ),
        ),
        QAItem(
            question=(
                f"What did the transcription on the clue say when {keeper.id} "
                f"opened the {cont.label} at {place}?"
            ),
            answer=(
                f"The transcription read: \"{clue.text}\""
                + (" It also had an ink blot where the signature should have been." if clue.ink_blot else "")
            ),
        ),
    ]
    if helper is not None:
        qa.append(QAItem(
            question=(
                f"Who helped {trait} {keeper.id} read the transcription at "
                f"{place} and look at the ring of stones?"
            ),
            answer=(
                f"{helper.label} helped, {helper.prep}. Together they walked to "
                f"the pond and counted the ring stones, while {keeper.id} "
                f"checked the transcription again and again."
            ),
        ))
    if suspect is not None:
        qa.append(QAItem(
            question=(
                f"How did the {helper.type if helper else 'owl'} point to the "
                f"{suspect.type} as the one who moved the stones?"
            ),
            answer=(
                f"{helper.label if helper else 'Owl'} said to look at the mud "
                f"on the third stone, where the print of a single "
                f"{suspect.memes.get('paw', 'broad')} paw was pressed into "
                f"the clay, which only matches the {suspect.type}."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What did the {suspect.type} say after {trait} {keeper.id} "
                f"and {helper.label if helper else 'Owl'} found the print?"
            ),
            answer=(
                f"The {suspect.type}'s eyes went wide and "
                f"{suspect.pronoun('possessive')} cheeks turned pink. "
                f'"{suspect.pronoun().capitalize()} just like the way they '
                f'line up," {suspect.pronoun()} said softly.'
            ),
        ))
    qa.append(QAItem(
        question=(
            f"How was the mystery solved at {place} after the {cont.label} "
            f"washed up for {trait} {keeper.id}?"
        ),
        answer=(
            f"{helper.label if helper else 'Owl'} folded the page so the ink "
            f"blot was hidden, {keeper.id} closed {pos} blue notebook, and "
            f"they all walked home together as the current carried the empty "
            f"{cont.label} back out to sea."
        ),
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags: set[str] = {"jettison", "transcription"}
    if f.get("ink_blot"):
        tags.add("ink_blot")
    tags.add("paw_print")
    tags.add("ring")
    tags.add("keeper")
    helper = f.get("helper")
    if helper is not None:
        tags.add(helper.type)
    suspect = f.get("suspect")
    if suspect is not None:
        tags.add(suspect.type)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:14} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="meadow", container="tin", clue="two_three",
        suspect="toad", helper="owl",
        name="Bramble", keeper="badger", trait="patient",
    ),
    StoryParams(
        place="riverbank", container="bottle", clue="webbed",
        suspect="otter", helper="otter",
        name="Thistle", keeper="badger", trait="careful",
    ),
    StoryParams(
        place="pond_edge", container="box", clue="broad",
        suspect="toad", helper="owl",
        name="Rowan", keeper="badger", trait="gentle",
    ),
    StoryParams(
        place="harbor", container="scroll", clue="order",
        suspect="vole", helper="owl",
        name="Hazel", keeper="badger", trait="earnest",
    ),
    StoryParams(
        place="meadow", container="tin", clue="two_three",
        suspect="beaver", helper="owl",
        name="Brock", keeper="badger", trait="tidy",
    ),
]


def explain_rejection(container: Container, clue: Clue,
                     suspect: Suspect, helper: Helper) -> str:
    if not puzzle_holds(container, clue):
        return (f"(No story: the {container.label} has no order hint and the clue "
                f"has no ink blot -- there is nothing to solve.  Try a container "
                f"that carries an order or a clue with an ink blot.)")
    if not helper_sees_clue(helper, clue):
        return (f"(No story: {helper.label} cannot read a transcription -- "
                f"foxes are shy of ink.  Use owl or otter to read the clue.)")
    if not paw_matches(suspect, clue):
        return (f"(No story: the {suspect.type}'s {suspect.paw} paw does not "
                f"match what the clue reveals ({clue.reveals}).  Try a suspect "
                f"whose paw matches the clue.)")
    return "(No story: the chosen elements do not form a coherent mystery.)"


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate
# (puzzle_holds / helper_sees_clue / paw_matches / valid_combos).  The rules
# are inline below; the facts come from the registries so the two cannot drift.
# Uses the shared `asp` helper + clingo, imported lazily so the prose engine
# runs without them.  See `--verify`.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A clue is solvable when the container carries an order OR the clue has an ink blot.
puzzle_holds(C, K) :- container(C), clue(K), has_order(C).
puzzle_holds(C, K) :- container(C), clue(K), ink_blot(K).

% Helpers who can read a transcription.
can_read(H) :- helper(H), not shy_of_ink(H).

% A clue matches a suspect when the clue reveals the suspect's paw shape,
% or simply "paw" (which matches every suspect).
paw_match(S, K) :- suspect(S, P), clue(K), reveals(K, P).
paw_match(S, K) :- suspect(S, _), clue(K), reveals(K, paw).

% A valid mystery requires a readable clue, a matching suspect, and any helper.
valid(P, C, K, S, H) :- setting(P), container(C), clue(K), suspect(S), helper(H),
                         puzzle_holds(C, K), can_read(H), paw_match(S, K).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.note:
            lines.append(asp.fact("place_note", pid))
    for cid, c in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        if c.has_order:
            lines.append(asp.fact("has_order", cid))
        if c.ink_blot:
            lines.append(asp.fact("container_ink", cid))
    for kid, k in CLUES.items():
        lines.append(asp.fact("clue", kid))
        lines.append(asp.fact("reveals", kid, k.reveals))
        if k.ink_blot:
            lines.append(asp.fact("ink_blot", kid))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.type))
        if h.type == "fox":
            lines.append(asp.fact("shy_of_ink", h.type))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid, s.paw))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (place, container, clue, suspect, helper)."""
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with Python valid_combos()."""
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
# Standard storyworld interface (see storyworlds/AGENTS.md):
#   build_parser() -> ArgumentParser
#   resolve_params(args, rng) -> StoryParams        (random where unspecified)
#   generate(params) -> StorySample                  (the core; world -> story+QA)
#   emit(sample, ...) -> None                        (human-readable output)
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a jettisoned container, a transcription, "
                    "and a mystery to solve.  Unspecified choices are picked at random "
                    "(seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--helper", choices=[h.type for h in HELPERS])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-mystery set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in any unspecified choices at random, keeping the combo reasonable.

    Raises StoryError if the *explicit* options describe an invalid story."""
    if args.container and args.clue and args.suspect and args.helper:
        cont = CONTAINERS[args.container]
        clue = CLUES[args.clue]
        sus = SUSPECTS[args.suspect]
        helper = next(h for h in HELPERS if h.type == args.helper)
        if not (puzzle_holds(cont, clue) and helper_sees_clue(helper, clue)
                and paw_matches(sus, clue)):
            raise StoryError(explain_rejection(cont, clue, sus, helper))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.container is None or c[1] == args.container)
              and (args.clue is None or c[2] == args.clue)
              and (args.suspect is None or c[3] == args.suspect)
              and (args.helper is None or c[4] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, container_id, clue_id, suspect_id, helper_type = rng.choice(sorted(combos))
    name = args.name or rng.choice(KEEPER_NAMES)
    keeper = "badger"
    trait = rng.choice(KEEPER_TRAITS)
    return StoryParams(
        place=place,
        container=container_id,
        clue=clue_id,
        suspect=suspect_id,
        helper=helper_type,
        name=name,
        keeper=keeper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    helper = next(h for h in HELPERS if h.type == params.helper)
    world = tell(
        SETTINGS[params.place],
        CONTAINERS[params.container],
        CLUES[params.clue],
        SUSPECTS[params.suspect],
        helper,
        keeper_name=params.name,
        keeper_type=params.keeper,
        keeper_traits=[params.trait, "careful"],
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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, container, clue, suspect, helper) combos:\n")
        for place, cont, clue, sus, helper in combos:
            print(f"  {place:11} {cont:9} {clue:11} {sus:8} [{helper}]")
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
            header = f"### {p.name}: {p.clue} in a {p.container} at {p.place} (suspect: {p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
