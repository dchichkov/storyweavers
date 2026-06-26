#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/spread_mystery_to_solve_mystery.py
=========================================================================================================

A standalone *story world* sketch for the "Mystery at the Bakery" tale and
close, constraint-checked variations of it.

Initial story (used to build a world model):
---
On Maple Street, there was a busy little bakery called the Sunrise Bakery.
The baker, Mr. Owl, was proud of his warm loaves and his long table spread
with butter, jam, and honey. Every morning he spread fresh cream on the
shelves, set out six pretty jars in a careful line, and waited for the
first customer.

But on Tuesday, something was wrong. The bakery was still. The smell was
faint. When Mr. Owl looked, he saw that one jar of jam was missing. Then he
saw a wet trail, then a faint line of jam, then a small, soft clue he did
not understand. The shop was quiet. The light was pale. A little mystery
was sitting right there on the counter, and Mr. Owl had to solve it before
the morning was gone.

Causal state updates:
---
    clue noticed          -> baker.curiosity += 1
    clue leads to next    -> baker.focus += 1
    wrong guess           -> baker.doubt += 1
    right guess           -> baker.relief += 1
    spread of jam         -> mess.dirty += 1
    jar missing           -> mess.suspicion += 1
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
# (``python storyworlds/worlds/.../spread_mystery_to_solve_mystery.py``): add
# the package dir (storyworlds/) to the path so ``results`` resolves regardless
# of the current directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Clue kinds recognized by the world.  Order matters for the "chain" rule --
# an item is only a *clue* if the previous kind in the chain has already been
# noticed, so the mystery unfolds step by step rather than all at once.
CLUE_KINDS = ["missing", "trail", "smudge", "sound", "footprint", "trouble"]

# A "spread" is the messy source the detective follows through the bakery.
SPREAD_KINDS = ["jam", "honey", "butter", "flour", "syrup", "cream"]


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # baker, cat, jar, crumb, ...
    label: str = ""                # short reference, e.g. "jam jar"
    phrase: str = ""               # full noun phrase, e.g. "a little jar of jam"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    region: str = ""               # counter | window | floor | shelf
    plural: bool = False
    # Two numeric dimensions, treated uniformly (cf. story.py memeplex model):
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "baker_woman", "cat", "mouse", "duck"}
        male = {"boy", "father", "dad", "man", "baker", "baker_man", "dog", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.type


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the bakery"          # e.g. "the bakery", "the kitchen", "the pantry"
    indoor: bool = True
    surface: str = "the long counter"  # where the spread is laid out
    hour: str = "morning"              # morning | afternoon | evening
    affords: set[str] = field(default_factory=set)   # which clues this place supports


@dataclass
class Clue:
    """A step in the mystery chain: an observable sign the baker notices."""
    id: str
    label: str                  # short noun, e.g. "wet trail", "tiny footprint"
    phrase: str                 # full clause after 'he saw a ...', e.g. "a wet trail near the flour"
    needs: str                  # prior clue kind that has to be noticed first
    points_to: str              # suspect type this clue implicates
    where: str                  # region of the bakery where the clue sits
    tags: set[str] = field(default_factory=set)   # world-knowledge topics it touches


@dataclass
class Suspect:
    """A small character who might be the cause of the missing jar."""
    id: str
    type: str                   # cat, dog, mouse, duck, fox, baker_woman, baker_man
    label: str                  # "a little orange cat", "a nosy brown mouse"
    motive: str                 # phrase: "loves the smell of jam"
    tells: set[str]             # observable behaviors
    final: str                  # the closing line where the suspect is unmasked
    region: str = "floor"       # where they tend to leave traces


@dataclass
class Spread:
    """The messy thing the suspects love and that gets tracked around the shop."""
    id: str
    label: str                  # "jam", "honey", "cream", "flour"
    plural: bool = False
    color: str = "deep red"     # used in descriptions
    feel: str = "sticky"        # used in descriptions
    smell: str = "sweet"        # used in descriptions
    verb: str = "spread"        # what the baker did with it this morning
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
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


def _r_chain(world: World) -> list[str]:
    """Each clue, once noticed, raises curiosity; if it follows a previous
    kind, it also raises focus (the detective is onto something)."""
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("clue", 0) < THRESHOLD:
            continue
        sig = ("chain", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        # Find the baker and update.
        baker = next((e for e in world.characters() if e.type in {"baker", "baker_man", "baker_woman"}), None)
        if baker is None:
            continue
        baker.memes["curiosity"] += 1
        kind = ent.meters.get("clue_kind", "")
        prev_index = CLUE_KINDS.index(kind) - 1 if kind in CLUE_KINDS else -1
        if prev_index >= 0 and any(e.meters.get("clue_kind") == CLUE_KINDS[prev_index]
                                    for e in world.entities.values()):
            baker.memes["focus"] += 1
    return out


def _r_spread(world: World) -> list[str]:
    """The spread is what's left smeared on the counter/floor -- it tracks the
    path of the suspect.  A region the spread touched is 'soiled'."""
    out: list[str] = []
    spread = world.entities.get("spread")
    if not spread:
        return out
    for ent in list(world.entities.values()):
        if ent.id == "spread":
            continue
        if ent.meters.get("touched_spread", 0) >= THRESHOLD:
            sig = ("spread", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            spread.meters["dirty"] += 1
    return out


def _r_guess(world: World) -> list[str]:
    """A wrong guess raises doubt; a right guess (points_to == culprit) raises
    relief.  The screenplay only ever fires one of these per story."""
    return []


def _r_close(world: World) -> list[str]:
    """When the culprit is identified, conflict is cleared and warmth rises."""
    baker = next((e for e in world.characters() if e.type in {"baker", "baker_man", "baker_woman"}), None)
    culprit_id = world.facts.get("culprit_id")
    if not baker or not culprit_id:
        return []
    if baker.memes.get("identified", 0) < THRESHOLD:
        return []
    sig = ("close", baker.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    baker.memes["conflict"] = 0.0
    baker.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="chain", tag="cognitive", apply=_r_chain),
    Rule(name="spread", tag="physical", apply=_r_spread),
    Rule(name="guess", tag="cognitive", apply=_r_guess),
    Rule(name="close", tag="social", apply=_r_close),
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
# Constraint helpers -- what makes a *reasonable* mystery in this world.
# ---------------------------------------------------------------------------
def chain_complete(place: str, clue_ids: list[str]) -> bool:
    """The chosen clues must form a connected chain under their `needs`
    relationship (each clue's `needs` was noticed before it)."""
    noticed: set[str] = set()
    # The first clue in CLUE_KINDS is always available.
    noticed.add(CLUE_KINDS[0])
    for cid in clue_ids:
        c = CLUES[cid]
        if c.id not in CLUE_KINDS and c.needs not in noticed:
            return False
        if c.needs in noticed or c.id == CLUE_KINDS[0]:
            noticed.add(c.id)
        else:
            return False
    return True


def suspect_matches(culprit_id: str, clue_ids: list[str]) -> bool:
    """At least one of the clues must point to the culprit's type."""
    culprit = SUSPECTS[culprit_id]
    for cid in clue_ids:
        if CLUES[cid].points_to == culprit.type:
            return True
    return False


def spread_compatible(spread_id: str, suspect_id: str) -> bool:
    """A spread is 'compatible' with a suspect if it shows up in the suspect's
    tells (i.e. they are known to love the smell/taste of it)."""
    return spread_id in SUSPECTS[suspect_id].tells


def valid_mystery(place: str, clue_ids: list[str], spread_id: str, suspect_id: str) -> bool:
    """Top-level constraint: a valid (place, clues, spread, suspect) tuple."""
    if place not in PLACES:
        return False
    if any(c not in CLUES for c in clue_ids):
        return False
    if spread_id not in SPREADS:
        return False
    if suspect_id not in SUSPECTS:
        return False
    if not chain_complete(place, clue_ids):
        return False
    if not suspect_matches(suspect_id, clue_ids):
        return False
    if not spread_compatible(spread_id, suspect_id):
        return False
    return True


# ---------------------------------------------------------------------------
# Prediction: the baker imagines how the morning will unfold.
# ---------------------------------------------------------------------------
def predict_chain(world: World, baker: Entity, clue_ids: list[str]) -> dict:
    """Simulate the discovery chain silently and report whether the culprit
    would be reached."""
    sim = world.copy()
    for cid in clue_ids:
        _see_clue(sim, sim.get(baker.id), CLUES[cid], narrate=False)
    return {"ended_focus": baker.memes["focus"] >= 1.0 for _ in [None]} or {"ended_focus": True}


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def setting_detail(setting: Setting, spread: Spread) -> str:
    parts = []
    if setting.hour == "morning":
        parts.append("The morning light came in soft through the window")
    elif setting.hour == "afternoon":
        parts.append("The afternoon sun stretched across the floor")
    else:
        parts.append("The evening lamps made the room warm and quiet")
    parts.append(f"and {setting.place} smelled of {spread.smell} bread")
    return parts[0] + ", " + parts[1] + "."


def introduce_baker(world: World, baker: Entity) -> None:
    world.say(
        f"Once upon a time, in a little shop on a quiet street, there was a "
        f"careful {baker.type} named {baker.id}."
    )


def morning_routine(world: World, baker: Entity, spread: Spread) -> None:
    baker.memes["pride"] += 1
    world.say(
        f"Every {world.setting.hour}, {baker.id} would {spread.verb} the "
        f"{spread.label} across the {world.setting.surface}, set out the "
        f"pretty jars, and wait for the first customer."
    )


def something_wrong(world: World, baker: Entity) -> None:
    baker.memes["alert"] += 1
    world.say(
        f"But on this {world.setting.hour}, something was wrong. "
        f"{baker.id.capitalize()} could feel it the moment he stepped behind "
        f"the {world.setting.surface}."
    )


def _see_clue(world: World, baker: Entity, clue: Clue, narrate: bool = True) -> None:
    """The baker notices a clue; this is the heart of the chain."""
    baker.memes["curiosity"] += 1
    baker.memes["focus"] += 0.5
    # The clue object: a record of the observation.
    ent = world.add(Entity(
        id=f"clue_{clue.id}", type="clue", label=clue.label, phrase=clue.phrase,
        region=clue.where,
    ))
    ent.meters["clue"] += 1
    ent.meters["clue_kind"] = CLUE_KINDS.index(clue.id) if clue.id in CLUE_KINDS else -1
    if narrate:
        world.say(f"{baker.id.capitalize()} noticed a {clue.phrase}.")


def notice_chain(world: World, baker: Entity, clue_ids: list[str]) -> None:
    for cid in clue_ids:
        _see_clue(world, baker, CLUES[cid])


def first_wrong_guess(world: World, baker: Entity, decoy: Suspect) -> None:
    baker.memes["doubt"] += 1
    world.say(
        f'For a moment, {baker.id} thought it must have been {decoy.label}, '
        f'because {decoy.motive}.'
    )
    world.say(
        f"But then {baker.id} looked again, and the answer did not fit."
    )


def right_guess(world: World, baker: Entity, culprit: Suspect) -> None:
    baker.memes["identified"] += 1
    baker.memes["relief"] += 1
    world.facts["culprit_id"] = culprit.id
    propagate(world, narrate=False)
    world.say(
        f"{baker.id.capitalize()} took a slow breath and looked at all the "
        f"clues at once. The {culprit.type} was the one who {culprit.motive}."
    )
    world.say(
        f'"Of course," {baker.id} said quietly. "It had to be you, '
        f'{culprit.label}."'
    )


def reveal(world: World, baker: Entity, culprit: Suspect, spread: Spread) -> None:
    baker.memes["warmth"] += 1
    world.say(
        f"The {culprit.type} blinked, licked a tiny bit of {spread.label} "
        f"off one paw, and looked up at {baker.id}."
    )
    world.say(culprit.final)


def close(world: World, baker: Entity) -> None:
    baker.memes["relief"] += 1
    world.say(
        f"{baker.id.capitalize()} smiled, set the missing jar back where it "
        f"belonged, and opened the shop for the day."
    )
    world.say("And that is how the little mystery at the bakery was solved.")


# ---------------------------------------------------------------------------
# The screenplay: three-act mystery, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, clues: list[Clue], spread: Spread,
         culprit: Suspect, decoy: Suspect, baker_name: str = "Mr. Owl",
         baker_type: str = "baker") -> World:
    world = World(setting)
    world.weather = "soft"  # used for the "soft light" line; not weather exactly

    baker = world.add(Entity(
        id=baker_name, kind="character", type=baker_type,
        traits=["careful", "gentle"],
    ))

    # Track the spread as an entity so the rules can see it.
    world.add(Entity(
        id="spread", type="spread", label=spread.label, plural=spread.plural,
    ))

    # Act 1 -- setup: the bakery, the morning, the spread on the counter.
    introduce_baker(world, baker)
    morning_routine(world, baker, spread)

    # Act 2 -- the mystery unfolds as a chain of clues.
    world.para()
    something_wrong(world, baker)
    world.para()
    notice_chain(world, baker, [c.id for c in clues])
    first_wrong_guess(world, baker, decoy)

    # Act 3 -- the right answer, the reveal, the close.
    world.para()
    right_guess(world, baker, culprit)
    reveal(world, baker, culprit, spread)
    world.para()
    close(world, baker)

    # Record facts for the Q&A generators (grounded in the simulated world).
    world.facts.update(
        baker=baker, culprit=culprit, decoy=decoy, spread=spread, clues=clues,
        setting=setting, mystery_solved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
PLACES = {
    "bakery": Setting(
        place="the bakery", indoor=True, surface="the long counter",
        hour="morning", affords={"missing", "trail", "smudge", "sound", "footprint", "trouble"},
    ),
    "kitchen": Setting(
        place="the kitchen", indoor=True, surface="the wooden table",
        hour="morning", affords={"missing", "trail", "smudge", "sound", "footprint", "trouble"},
    ),
    "pantry": Setting(
        place="the pantry", indoor=True, surface="the open shelf",
        hour="afternoon", affords={"missing", "trail", "smudge", "footprint", "trouble"},
    ),
}

CLUES = {
    "missing": Clue(
        id="missing", label="missing jar",
        phrase=f"missing jar of {{spread}}",
        needs="", points_to="baker",  # overwritten in narrate by spread noun
        where="counter",
        tags={"mystery", "jar"},
    ),
    "trail": Clue(
        id="trail", label="wet trail",
        phrase="wet trail across the floor", needs="missing",
        points_to="cat", where="floor",
        tags={"mystery", "trail"},
    ),
    "smudge": Clue(
        id="smudge", label="smudge", phrase="smudge of color on the windowsill",
        needs="trail", points_to="cat", where="window",
        tags={"mystery", "smudge"},
    ),
    "sound": Clue(
        id="sound", label="soft sound", phrase="soft sound behind the flour sacks",
        needs="smudge", points_to="mouse", where="shelf",
        tags={"mystery", "sound"},
    ),
    "footprint": Clue(
        id="footprint", label="tiny footprint", phrase="tiny footprint by the oven",
        needs="sound", points_to="mouse", where="floor",
        tags={"mystery", "footprint"},
    ),
    "trouble": Clue(
        id="trouble", label="a small trouble",
        phrase="small trouble on the counter", needs="footprint",
        points_to="mouse", where="counter",
        tags={"mystery"},
    ),
}

# Re-point the "missing" clue at the spread rather than a fixed target, so the
# ASP gate and the world both use the actual spread's noun in the missing jar.
CLUES["missing"].points_to = "spread"   # a special pseudo-target handled in code


SUSPECTS = {
    "cat": Suspect(
        id="cat", type="cat", label="a little orange cat",
        motive="loves the smell of sweet things and would have followed the trail",
        tells={"jam", "honey", "cream"},
        final=(
            "The little cat had been tasting the spread, and was not sorry at all."
        ),
        region="window",
    ),
    "mouse": Suspect(
        id="mouse", type="mouse", label="a nosy little mouse",
        motive="had been sneaking along the wall all morning, looking for crumbs",
        tells={"flour", "butter", "syrup"},
        final=(
            "The little mouse had carried a tiny bit of the spread to its secret corner."
        ),
        region="floor",
    ),
    "duck": Suspect(
        id="duck", type="duck", label="a curious little duck",
        motive="always wants to know what is in every jar",
        tells={"honey", "syrup", "jam"},
        final=(
            "The little duck had been dipping its beak into the jars, one by one."
        ),
        region="floor",
    ),
    "fox": Suspect(
        id="fox", type="fox", label="a sly little fox",
        motive="had crept in through the back door, looking for something sweet",
        tells={"honey", "cream", "syrup"},
        final=(
            "The fox had carried a jar lid out the back, just to be mischievous."
        ),
        region="floor",
    ),
}

# Spread registry: which messy thing is on the counter this morning.
SPREADS = {
    "jam": Spread(
        id="jam", label="jam", plural=False, color="deep red",
        feel="sticky", smell="sweet", verb="spread",
        tags={"jam", "sweet", "spread"},
    ),
    "honey": Spread(
        id="honey", label="honey", plural=False, color="golden",
        feel="thick", smell="sweet", verb="pour",
        tags={"honey", "sweet", "spread"},
    ),
    "butter": Spread(
        id="butter", label="butter", plural=False, color="pale yellow",
        feel="soft", smell="creamy", verb="spread",
        tags={"butter", "spread"},
    ),
    "flour": Spread(
        id="flour", label="flour", plural=False, color="white",
        feel="powdery", smell="plain", verb="dust",
        tags={"flour", "spread"},
    ),
    "syrup": Spread(
        id="syrup", label="syrup", plural=False, color="brown",
        feel="sticky", smell="rich", verb="pour",
        tags={"syrup", "sweet", "spread"},
    ),
    "cream": Spread(
        id="cream", label="cream", plural=False, color="white",
        feel="soft", smell="fresh", verb="spread",
        tags={"cream", "spread"},
    ),
}

BAKER_NAMES = ["Mr. Owl", "Mr. Bear", "Mr. Fox", "Mr. Wren", "Mr. Hare"]
BAKER_WOMAN_NAMES = ["Mrs. Hare", "Mrs. Wren", "Mrs. Owl", "Mrs. Bear"]


def valid_combos() -> list[tuple[str, tuple[str, ...], str, str]]:
    """(place, clues-tuple, spread, suspect) quads that pass the constraint."""
    combos: list[tuple[str, tuple[str, ...], str, str]] = []
    for place in PLACES:
        for spread_id in SPREADS:
            for culprit_id in SUSPECTS:
                if not spread_compatible(spread_id, culprit_id):
                    continue
                # Build a minimal valid chain: include the first kind and any
                # clues whose points_to matches the culprit, in CLUE_KINDS order.
                chain = [CLUE_KINDS[0]]
                for kind in CLUE_KINDS[1:]:
                    if CLUES[kind].points_to == SUSPECTS[culprit_id].type:
                        chain.append(kind)
                if len(chain) < 2:
                    continue
                if not chain_complete(place, chain):
                    continue
                if not suspect_matches(culprit_id, chain):
                    continue
                combos.append((place, tuple(chain), spread_id, culprit_id))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    clues: tuple[str, ...]        # chain of clue ids, in order
    spread: str
    culprit: str
    baker_name: str
    baker_type: str
    decoy: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "mystery": [("What is a mystery?",
                 "A mystery is something that is hard to explain, like when a "
                 "thing goes missing and no one is sure who took it or why.")],
    "jar": [("What is a jar?",
             "A jar is a small, round container, often made of glass, that "
             "holds jam, honey, or other sweet things.")],
    "trail": [("What is a trail?",
               "A trail is a line of marks left behind on the ground by someone "
               "or something that has just passed by.")],
    "smudge": [("What is a smudge?",
                "A smudge is a dirty mark, often made when something wet or "
                "sticky is touched and then pressed against a surface.")],
    "footprint": [("What is a footprint?",
                   "A footprint is a mark left by a foot on a soft surface, "
                   "like a footprint in flour or in mud.")],
    "jam": [("What is jam?",
             "Jam is a sweet food made by cooking fruit and sugar together "
             "until it is thick, and it is usually spread on bread.")],
    "honey": [("What is honey?",
               "Honey is a sweet, sticky food that bees make from flower "
               "nectar, and it is often poured on bread or into tea.")],
    "butter": [("What is butter?",
                "Butter is a soft, yellow food made from cream, and it is "
                "spread on bread to make it taste rich.")],
    "flour": [("What is flour?",
               "Flour is a soft, white powder made by grinding wheat, and "
               "bakers use it to make bread and cakes.")],
    "syrup": [("What is syrup?",
               "Syrup is a thick, sweet liquid, and it is often poured on "
               "pancakes or used to sweeten drinks.")],
    "cream": [("What is cream?",
               "Cream is the soft, fatty part of milk that rises to the top; "
               "it is used in cooking and on desserts.")],
    "spread": [("What does it mean to spread something?",
                "To spread something is to push it gently across a surface "
                "with a knife, so it makes a thin, even layer.")],
}
KNOWLEDGE_ORDER = ["mystery", "jar", "trail", "smudge", "footprint",
                   "jam", "honey", "butter", "flour", "syrup", "cream", "spread"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    baker, culprit, spread, setting = f["baker"], f["culprit"], f["spread"], f["setting"]
    kw = "mystery"
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a small '
        f'mystery at the {setting.place}" that includes the word "{kw}".',
        f'Tell a gentle mystery story where {baker.id} the {baker.type} '
        f'discovers a {spread.label} trail and solves it.',
        f'Write a simple story that uses the noun "{kw}" and ends with the '
        f'mystery solved and the shop ready for the day.',
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    baker, culprit, decoy, spread, setting = (
        f["baker"], f["culprit"], f["decoy"], f["spread"], f["setting"],
    )
    sub, obj, pos = baker.pronoun("subject"), baker.pronoun("object"), baker.pronoun("possessive")
    chain_labels = [c.label for c in f["clues"]]
    chain_phrase = ", a ".join(chain_labels)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"What was wrong at {setting.place} when {baker.id} the {baker.type} "
                f"came in to set out the {spread.label}?"
            ),
            answer=(
                f"Something was wrong at {setting.place} on that {setting.hour}. "
                f"{baker.id.capitalize()} could feel it the moment he stepped behind "
                f"the {setting.surface}."
            ),
        ),
        QAItem(
            question=(
                f"Which chain of clues did {baker.id} follow at {setting.place} "
                f"to find the missing jar?"
            ),
            answer=(
                f"{baker.id.capitalize()} noticed a {chain_phrase}. Each one "
                f"told a small part of the story, and together they pointed at "
                f"the answer."
            ),
        ),
        QAItem(
            question=(
                f"Why did {baker.id} first think {decoy.label} might be the "
                f"one who took the jar at {setting.place}?"
            ),
            answer=(
                f"{baker.id.capitalize()} thought it must have been {decoy.label}, "
                f"because {decoy.motive}. But when he looked again, the answer "
                f"did not fit."
            ),
        ),
        QAItem(
            question=(
                f"How did {baker.id} finally solve the {spread.label} mystery at "
                f"{setting.place}?"
            ),
            answer=(
                f"{baker.id.capitalize()} took a slow breath and looked at all "
                f"the clues at once. The {culprit.type} was the one who "
                f"{culprit.motive}. {culprit.final}"
            ),
        ),
        QAItem(
            question=(
                f"What did {baker.id} do at the end of the morning at "
                f"{setting.place} once the mystery was solved?"
            ),
            answer=(
                f"{baker.id.capitalize()} smiled, set the missing jar back where "
                f"it belonged, and opened the shop for the day. The little "
                f"mystery at {setting.place} was solved."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = set(f["spread"].tags) | {"mystery"}
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:18} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="bakery", clues=("missing", "trail", "smudge"),
        spread="jam", culprit="cat", baker_name="Mr. Owl", baker_type="baker",
        decoy="mouse",
    ),
    StoryParams(
        place="kitchen", clues=("missing", "trail", "sound", "footprint"),
        spread="flour", culprit="mouse", baker_name="Mr. Bear",
        baker_type="baker", decoy="cat",
    ),
    StoryParams(
        place="pantry", clues=("missing", "trail", "smudge"),
        spread="honey", culprit="cat", baker_name="Mr. Wren",
        baker_type="baker", decoy="duck",
    ),
    StoryParams(
        place="bakery", clues=("missing", "trail", "sound", "footprint"),
        spread="syrup", culprit="mouse", baker_name="Mr. Fox",
        baker_type="baker", decoy="cat",
    ),
    StoryParams(
        place="kitchen", clues=("missing", "trail", "smudge"),
        spread="honey", culprit="duck", baker_name="Mrs. Hare",
        baker_type="baker_woman", decoy="mouse",
    ),
]


def explain_rejection(reason: str) -> str:
    return f"(No story: {reason})"


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate
# (chain_complete / suspect_matches / spread_compatible / valid_mystery).
# The rules are inline below; the facts are generated from the registries
# above so the two can never drift.  Uses the shared `asp` helper + clingo,
# imported lazily so the prose engine runs without them.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Each clue kind is "available" if the kind it needs has already been noticed.
available(K) :- first_kind(K).
available(K) :- clue(K), needs(K, N), available(N).

% A chain of clues is "complete" if every clue in it is available and they
% all sit at the same place.
complete(Place, K) :- available(K), seen_at(Place, K).

% A suspect matches a chain if at least one clue in the chain points to it.
matches(Suspect, K) :- clue(K), points_to(K, S), suspect(Suspect), S = Suspect.

% A spread is compatible with a suspect if it is in the suspect's tells.
spreads_compatible(Spread, Suspect) :- spread(Spread), suspect(Suspect),
                                       loves(Suspect, Spread).

% A story is valid if its place affords all clue kinds, the chain is complete,
% the spread is compatible with the suspect, and the chain matches the suspect.
valid(Place, K, Spread, Suspect) :- place(Place), affords(Place, K),
                                    complete(Place, K),
                                    spreads_compatible(Spread, Suspect),
                                    matches(Suspect, K).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for pid, s in PLACES.items():
        lines.append(asp.fact("place", pid))
        for k in sorted(s.affords):
            lines.append(asp.fact("affords", pid, k))
            lines.append(asp.fact("seen_at", pid, k))
    # Clue kinds + their dependencies + their targets.
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.needs:
            lines.append(asp.fact("needs", cid, c.needs))
        else:
            lines.append(asp.fact("first_kind", cid))
        # points_to may be a suspect type or the special "spread" pseudo-target;
        # we emit only the suspect targets so the matches rule fires.
        if c.points_to in {s.type for s in SUSPECTS.values()}:
            for sid, s in SUSPECTS.items():
                if s.type == c.points_to:
                    lines.append(asp.fact("points_to", cid, sid))
    # Suspects and the spreads they love.
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        for sp in sorted(s.tells):
            lines.append(asp.fact("loves", sid, sp))
    # Spreads.
    for sp in SPREADS:
        lines.append(asp.fact("spread", sp))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (place, clue, spread, suspect) quads."""
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos()."""
    clingo_set = {(p, c[0], s, su) for (p, c, s, su) in asp_valid_combos()}
    python_set = {(p, c[0], s, su) for (p, c, s, su) in valid_combos()}
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
        description="Story world sketch: a small mystery at the bakery. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--spread", choices=list(SPREADS))
    ap.add_argument("--culprit", choices=list(SUSPECTS))
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.spread is None or c[2] == args.spread)
              and (args.culprit is None or c[3] == args.culprit)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, clues, spread_id, culprit_id = rng.choice(sorted(combos))
    culprit = SUSPECTS[culprit_id]
    # Decoy: a different suspect, to feed the wrong-guess beat.
    decoys = [s for s in SUSPECTS.values() if s.id != culprit_id]
    decoy = rng.choice(decoys)
    baker_name = args.name or rng.choice(BAKER_NAMES)
    baker_type = "baker"
    return StoryParams(
        place=place,
        clues=clues,
        spread=spread_id,
        culprit=culprit_id,
        baker_name=baker_name,
        baker_type=baker_type,
        decoy=decoy.id,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    setting = PLACES[params.place]
    clue_objs = [CLUES[c] for c in params.clues]
    spread = SPREADS[params.spread]
    culprit = SUSPECTS[params.culprit]
    decoy = SUSPECTS[params.decoy]
    world = tell(setting, clue_objs, spread, culprit, decoy,
                 params.baker_name, params.baker_type)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        quads = asp_valid_combos()
        print(f"{len(quads)} compatible (place, clue, spread, suspect) combos:\n")
        for place, clue, spread, suspect in quads:
            print(f"  {place:9} {clue:10} {spread:8} {suspect}")
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
            header = f"### {p.baker_name}: mystery at {p.place} (culprit: {p.culprit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
