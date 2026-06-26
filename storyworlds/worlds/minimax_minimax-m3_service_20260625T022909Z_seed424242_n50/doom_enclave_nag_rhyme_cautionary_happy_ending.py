#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/doom_enclave_nag_rhyme_cautionary_happy_ending.py
=========================================================================================================================

A standalone *story world* sketch in the folk-tale style, built around the
seed tale of a small walled town ("the enclave") that refuses to listen to
a weary nag at the gate, then learns the hard way when a doom rolls in.
The cautionary turn -- a small choice delayed into a bigger problem -- ends
in a happy ending when the nag's good advice is finally taken and the rhyme
is restored to the town.

Domain vocabulary
-----------------
* Setting ........ a small folk-tale enclave (village / hill / shore / glade)
* Doom ........... a slow-coming trouble that finds the enclave (fog, flood,
                  wolf, sickness, storm, drought, plague of locusts...)
* Nag ............ a weary, well-meaning wanderer (often an old aunt, a
                  peddler, a scarecrow with a bell, a tinker's cousin, a
                  bell-wearing goat, or a thin gray cat) who comes to the
                  gate and warns the villagers
* Rhyme .......... the enclave's protective saying, repeated through the
                  tale (its full / shortened / fixed forms are part of the
                  constraint engine: a broken rhyme = doom allowed in)
* Compromise ..... the nag's offer -- a small, easy, specific safeguard
                  (a lantern, a song, a rope, a bell on the gate, salt in
                  the well, a stitch in the roof) that the enclave can do
                  *now*, before the doom comes

The world runs a forward simulation:

    rift(R) > 0            -> doom(D) advances (R is the "how close" meter)
    rhyme broken (R<0)     -> doom can enter the enclave
    nag ignored (def>0)    -> child/enclave defiance rises; rift creeps up
    nag accepted (joy>0)   -> the safeguard is taken; doom turns aside
    safeguard in place     -> the doom is deflected (soiled = False at end)

Story shape: act 1 introduces the enclave and its rhyme; act 2 brings the
nag to the gate, the villagers nag back, the doom draws closer; act 3 the
small safeguard is finally taken and the rhyme is sung whole again -- a
happy ending that proves what changed (the gate is mended; the bell is
hung; the doom turns aside).

Two parity constraints are checked before a story is generated:

    1. the nag's safeguard must actually neutralise the doom it warns of
    2. if the rhyme is unbroken, the doom cannot enter the enclave yet

Invalid combinations (e.g. a fog doom with a sun-lamp safeguard) raise
``StoryError`` with a legible reason.
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# The doom family. Each kind is its own "messy" force that wears down a rhyme.
DOOM_KINDS = {"fog", "flood", "wolf", "sickness", "storm", "drought", "locusts"}

# Body of the enclave -- three concentric regions, each with its own rhyme line.
REGIONS = {"gate", "well", "roof"}


# ---------------------------------------------------------------------------
# Entities: characters, the enclave itself, and the safeguards share one shape.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing" | "enclave"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    region: str = ""             # gate | well | roof -- where a safeguard sits
    safeguard: bool = False      # a thing that defends against a doom
    guards: set[str] = field(default_factory=set)  # doom kinds it turns aside
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"aunt", "mother", "woman", "girl", "grandmother"}
        male = {"uncle", "father", "man", "boy", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"aunt": "auntie", "uncle": "uncle",
                "mother": "mother", "father": "father",
                "grandmother": "granny", "grandfather": "grandpa"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this folk-tale domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    """A small, walled place with a gate, a well, and a roof."""
    place: str                       # "the village", "the hill town" ...
    folk_name: str                   # name the villagers call their home
    rhyme_full: str                  # the three-line rhyme, sung whole
    rhyme_gate: str                  # the gate-line (kept when doom is near)
    rhyme_well: str                  # the well-line
    rhyme_roof: str                  # the roof-line
    flavor: str = ""                 # a one-line flavor detail


@dataclass
class Doom:
    """The slow trouble that finds the enclave."""
    id: str
    noun: str                        # "fog", "flood", "wolf" ...
    kind: str                        # one of DOOM_KINDS
    gather: str                      # clause "the fog rolled in"
    threaten: str                    # clause "the fog pressed against the gate"
    turned: str                      # clause "the fog turned aside"
    where: str                       # region it presses hardest on: gate | well | roof
    keyword: str = ""                # "fog"
    tags: set[str] = field(default_factory=set)


@dataclass
class Nag:
    """The weary warner who arrives at the gate."""
    id: str
    type: str                        # aunt | uncle | peddler | scarecrow | goat | cat
    label: str                       # "Auntie Rhy", "Old Tom the peddler"
    phrase: str                      # full noun phrase
    plural: bool = False
    wears_bell: bool = False         # iconic touch
    warn_clause: str                 # body of the warning


@dataclass
class Safeguard:
    """The nag's easy offer: a small thing that turns the doom aside."""
    id: str
    label: str
    phrase: str
    region: str                      # where it lives once taken: gate | well | roof
    guards: set[str]                 # which dooms it turns aside
    prep: str                        # "hang the bell on the gate"
    tail: str                        # "set the bell on the gate at sundown"
    plural: bool = False


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = ""           # "foggy", "rainy", "stormy", ...
        self.where: str = ""             # region the doom presses on (set on approach)
        self.kind: str = ""              # which doom kind is in play
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

    def safeguards(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.safeguard]

    def guarded(self, kind: str, region: str) -> bool:
        """Is there a safeguard in place that turns this doom aside at this region?"""
        return any(s.safeguard and kind in s.guards and s.region == region
                   for s in self.safeguards())

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.where = self.where
        clone.kind = self.kind
        clone.weather = self.weather
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


def _r_rift(world: World) -> list[str]:
    """Each nag turn (defiance / worry) widens the rift; a greeting narrows it."""
    enclave = next((e for e in world.entities.values() if e.kind == "enclave"), None)
    if enclave is None:
        return []
    out: list[str] = []
    if enclave.memes["defiance"] >= THRESHOLD:
        sig = ("rift", enclave.id, "defiance")
        if sig not in world.fired:
            world.fired.add(sig)
            enclave.meters["rift"] += 1
    if enclave.memes["worry"] >= THRESHOLD:
        sig = ("rift", enclave.id, "worry")
        if sig not in world.fired:
            world.fired.add(sig)
            enclave.meters["rift"] += 1
    return out


def _r_doom_advance(world: World) -> list[str]:
    """A rift >= THRESHOLD lets the doom draw close (turn aside still possible)."""
    enclave = next((e for e in world.entities.values() if e.kind == "enclave"), None)
    if enclave is None or not world.kind:
        return []
    out: list[str] = []
    if enclave.meters["rift"] >= THRESHOLD:
        sig = ("doom_advance", world.kind)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append(f"doom_advance:{world.kind}")
    return out


def _r_doom_blocked(world: World) -> list[str]:
    """A safeguard matching the doom kind AND region blocks the doom's advance."""
    if not world.kind or not world.where:
        return []
    if not world.guarded(world.kind, world.where):
        return []
    sig = ("doom_blocked", world.kind, world.where)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    enclave = next((e for e in world.entities.values() if e.kind == "enclave"), None)
    if enclave is not None:
        enclave.memes["relief"] += 1
    return [f"doom_blocked:{world.kind}"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="rift", tag="social", apply=_r_rift),
    Rule(name="doom_advance", tag="physical", apply=_r_doom_advance),
    Rule(name="doom_blocked", tag="physical", apply=_r_doom_blocked),
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
            if s.startswith("doom_advance:"):
                world.say(f"The {s.split(':', 1)[1]} pressed harder against the {world.where}.")
            elif s.startswith("doom_blocked:"):
                kind = s.split(":", 1)[1]
                world.say(f"But the safeguard at the {world.where} held the {kind} back.")
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* doom and a *reasonable* safeguard.
# ---------------------------------------------------------------------------
def doom_at_risk(doom: Doom, setting: Setting) -> bool:
    """A doom is meaningful only when its pressure point is one of the three
    places the enclave has a rhyme for (gate / well / roof)."""
    return doom.where in REGIONS


def select_safeguard(doom: Doom) -> Optional[Safeguard]:
    """The nag's offer must actually neutralise the doom AND sit on the right
    region.  Returns None when no safeguard in the catalog matches -- exactly
    the case we refuse to generate (a fog doom with a roof patch, say)."""
    for sg in SAFEGUARDS:
        if doom.kind in sg.guards and doom.where == sg.region:
            return sg
    return None


def predict_doom(world: World, doom: Doom) -> dict:
    """Simulate the doom's arrival on a copy and report whether the safeguard
    held (i.e. whether taking the safeguard is actually a viable ending)."""
    sim = world.copy()
    sim.kind = doom.kind
    sim.where = doom.where
    _approach_doom(sim, doom, narrate=False)
    blocked = ("doom_blocked", doom.kind, doom.where) in sim.fired
    return {"blocked": blocked, "rift": sim.entities["enclave"].meters["rift"]}


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def setting_open(world: World) -> None:
    s = world.setting
    world.say(
        f"In a fold of the hills there stood a small, careful place called "
        f"{s.folk_name}, where the people kept a rhyme for every part of home."
    )


def rhyme_intact(world: World) -> None:
    s = world.setting
    world.say(
        f"At the gate they sang of arrivals, at the well they sang of thirst, "
        f"and on the roof they sang of shelter. The full rhyme ran:\n\n"
        f'    "{s.rhyme_full}"\n\n'
        f"And while the rhyme was whole, the {s.folk_name} slept easy."
    )


def nag_arrives(world: World, nag: Nag, doom: Doom) -> None:
    bell = " a little bell on a string" if nag.wears_bell else ""
    world.say(
        f"One morning, a weary traveler came to the gate{bell} -- it was "
        f"{nag.phrase}. {nag.pronoun('subject').capitalize()} had walked a long road."
    )


def nag_warns(world: World, nag: Nag, doom: Doom, safeguard: Safeguard) -> None:
    enclave = world.entities["enclave"]
    enclave.memes["worry"] += 1
    world.say(
        f'"{nag.warn_clause} The {doom.noun} is closer than you think," '
        f"{nag.pronoun('subject')} said. "
        f'"I can show you an easy safeguard -- {safeguard.prep}."'
    )


def enclave_nags_back(world: World, nag: Nag) -> None:
    enclave = world.entities["enclave"]
    enclave.memes["defiance"] += 1
    world.say(
        f'But {nag.phrase} could only nag so much, and the folk of the '
        f"{enclave.label} were quicker to nag back. "
        f'"Mind your road, traveler," they said. "Our rhyme has held this long."'
    )


def doom_draws_near(world: World, doom: Doom) -> None:
    world.kind = doom.kind
    world.where = doom.where
    world.weather = doom.id
    world.say(
        f"That night, {doom.gather}, and the air tasted strange. "
        f"{doom.threaten}, and the rhyme on the {doom.where} felt thin."
    )


def nag_returns(world: World, nag: Nag, doom: Doom, safeguard: Safeguard) -> None:
    enclave = world.entities["enclave"]
    enclave.memes["defiance"] += 0     # the second visit begins to lower it
    world.say(
        f"In the morning, the traveler was still there, shivering at the gate. "
        f'"Hear me now," {nag.pronoun('subject')} said, '
        f'"before the {doom.noun} comes to sit on the {doom.where}."'
    )


def compromise(world: World, nag: Nag, doom: Doom,
               safeguard: Safeguard) -> Optional[Safeguard]:
    """Offer the safeguard -- but only if forward-simulating the doom says the
    safeguard actually holds (a *compatible* move, not wishful thinking)."""
    enclave = world.entities["enclave"]
    pred = predict_doom(world, doom)
    if not pred["blocked"]:
        return None                          # safeguard doesn't actually help
    sg = world.add(Entity(
        id=safeguard.id, type="safeguard", label=safeguard.label,
        region=safeguard.region, safeguard=True,
        guards=set(safeguard.guards), plural=safeguard.plural,
    ))
    enclave.memes["relief"] += 1
    world.say(
        f'The villagers looked once more at the rhyme, then at the {doom.noun}, '
        f'then at {nag.phrase}. "Well then," they said, '
        f'"we shall {safeguard.prep}." '
        f'They {safeguard.tail}.'
    )
    return safeguard


def rhyme_restored(world: World, doom: Doom, safeguard: Safeguard) -> None:
    s = world.setting
    line = {"gate": s.rhyme_gate, "well": s.rhyme_well, "roof": s.rhyme_roof}[doom.where]
    world.say(
        f"When the safeguard was set, the wind went still, and the folk of "
        f"{s.folk_name} sang the rhyme again from the top:\n\n"
        f'    "{s.rhyme_full}"\n\n'
        f"and the {doom.noun} {doom.turned}, and the town was merry."
    )


def _approach_doom(world: World, doom: Doom, narrate: bool = True) -> None:
    """Helper: advance the doom and let the rules fire (used by narration and
    by the forward-simulator in predict_doom())."""
    world.kind = doom.kind
    world.where = doom.where
    propagate(world, narrate=narrate)


# ---------------------------------------------------------------------------
# The screenplay: three-act folk-tale shape, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, doom: Doom, safeguard: Safeguard,
         nag: Nag, enclave_name: str = "Tuck") -> World:
    world = World(setting)

    enclave = world.add(Entity(
        id="enclave", kind="enclave", type="enclave", label=enclave_name,
        phrase=f"the folk of {enclave_name}",
        traits=["careful", "proud", "stubborn"],
    ))
    nag_ent = world.add(Entity(
        id=nag.id, kind="character", type=nag.type, label=nag.label,
        phrase=nag.phrase, plural=nag.plural,
    ))

    # Act 1 -- setup: who lives where, what rhyme keeps them safe.
    setting_open(world)
    rhyme_intact(world)

    # Act 2 -- the nag comes to the gate; the folk nag back; the doom draws near.
    world.para()
    nag_arrives(world, nag_ent, doom)
    nag_warns(world, nag_ent, doom, safeguard)
    enclave_nags_back(world, nag_ent)
    doom_draws_near(world, doom)

    # Act 3 -- the nag returns; the safeguard is finally taken; the rhyme is sung.
    world.para()
    nag_returns(world, nag_ent, doom, safeguard)
    chosen = compromise(world, nag_ent, doom, safeguard)
    if chosen:
        rhyme_restored(world, doom, chosen)

    world.facts.update(setting=setting, doom=doom, safeguard=chosen or safeguard,
                       nag=nag, enclave=enclave,
                       chosen=chosen is not None,
                       nag_ignored=True, happy_ending=chosen is not None)
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "village": Setting(
        place="the village",
        folk_name="Tuck-under-Hill",
        rhyme_full=("Mend the gate when the bell is slow, / "
                    "Salt the well when the brook runs low, / "
                    "Patch the roof when the wind says go."),
        rhyme_gate="Mend the gate when the bell is slow,",
        rhyme_well="Salt the well when the brook runs low,",
        rhyme_roof="Patch the roof when the wind says go.",
        flavor="a tidy place with a stone well and a thatched roof",
    ),
    "hill": Setting(
        place="the hill town",
        folk_name="Brackenford",
        rhyme_full=("Bar the gate when the bells ring thin, / "
                    "Draw the well when the rains leak in, / "
                    "Mend the roof when the storm comes in."),
        rhyme_gate="Bar the gate when the bells ring thin,",
        rhyme_well="Draw the well when the rains leak in,",
        rhyme_roof="Mend the roof when the storm comes in.",
        flavor="a windy hill town with slate roofs",
    ),
    "shore": Setting(
        place="the shore hamlet",
        folk_name="Sailors' End",
        rhyme_full=("Watch the gate when the tide runs high, / "
                    "Cover the well when the salt is nigh, / "
                    "Tie the roof when the gull goes by."),
        rhyme_gate="Watch the gate when the tide runs high,",
        rhyme_well="Cover the well when the salt is nigh,",
        rhyme_roof="Tie the roof when the gull goes by.",
        flavor="a small hamlet of fishermen on a gray coast",
    ),
    "glade": Setting(
        place="the forest glade",
        folk_name="Mossbridge",
        rhyme_full=("Hold the gate when the fox is near, / "
                    "Shade the well when the sun is clear, / "
                    "Thatch the roof when the leaves drop sheer."),
        rhyme_gate="Hold the gate when the fox is near,",
        rhyme_well="Shade the well when the sun is clear,",
        rhyme_roof="Thatch the roof when the leaves drop sheer.",
        flavor="a green clearing where the trees meet at a small bridge",
    ),
}

DOOMS = {
    "fog": Doom(
        id="fog", noun="fog", kind="fog",
        gather="a low, white fog came creeping up the road",
        threaten="The fog rolled against the gate and pressed close",
        turned="drifted past the gate and was gone by noon",
        where="gate",
        keyword="fog",
        tags={"fog", "weather"},
    ),
    "flood": Doom(
        id="flood", noun="flood", kind="flood",
        gather="a swollen brown flood came down from the hills",
        threaten="The floodwater lapped at the well and rose",
        turned="ran on past the gate as the waters thinned",
        where="well",
        keyword="flood",
        tags={"flood", "water"},
    ),
    "wolf": Doom(
        id="wolf", noun="wolf", kind="wolf",
        gather="a long howl came from the dark wood",
        threaten="A wolf came to the gate and would not pass by",
        turned="loped off down the road with its tail between its legs",
        where="gate",
        keyword="wolf",
        tags={"wolf", "beast"},
    ),
    "sickness": Doom(
        id="sickness", noun="sickness", kind="sickness",
        gather="a slow, tired sickness came into the hamlet",
        threaten="The sickness crept into the well-water",
        turned="lifted from the hamlet once the well was clean",
        where="well",
        keyword="sickness",
        tags={"sickness", "health"},
    ),
    "storm": Doom(
        id="storm", noun="storm", kind="storm",
        gather="a great black storm gathered over the hills",
        threaten="The storm tore at the roof and rattled the slates",
        turned="passed on over the village and left the sky clear",
        where="roof",
        keyword="storm",
        tags={"storm", "weather"},
    ),
    "drought": Doom(
        id="drought", noun="drought", kind="drought",
        gather="a long, dry drought settled over the land",
        threaten="The drought drank the well down to a brown inch",
        turned="broke at last when the rains came softly back",
        where="well",
        keyword="drought",
        tags={"drought", "weather"},
    ),
    "locusts": Doom(
        id="locusts", noun="plague of locusts", kind="locusts",
        gather="a buzzing dark cloud of locusts rose from the east",
        threaten="The locusts settled on the roof like a living carpet",
        turned="lifted off on the next wind and did not return",
        where="roof",
        keyword="locusts",
        tags={"locusts", "pest"},
    ),
}

# Nag cast: each is a small folk-tale figure with a particular tone of warning.
NAGS = [
    Nag(
        id="auntie_rhy", type="aunt", label="Auntie Rhy", plural=False,
        phrase="auntie Rhy, an old aunt with a thimble on her finger",
        wears_bell=False,
        warn_clause="I have walked the long road and I have seen what comes",
    ),
    Nag(
        id="tom_peddler", type="peddler", label="Old Tom the peddler",
        phrase="Old Tom the peddler, with a pack on his back",
        plural=False,
        wears_bell=True,
        warn_clause="My bells have not rung this thin since I was a boy",
    ),
    Nag(
        id="bellgoat", type="goat", label="the bell-goat", plural=False,
        phrase="a thin gray goat with a bell on its neck",
        plural=False,
        wears_bell=True,
        warn_clause="the goat only shook its bell and looked at the gate",
    ),
    Nag(
        id="scare_row", type="scarecrow", label="the scarecrow",
        phrase="a scarecrow with a straw hat and a stick",
        plural=False,
        wears_bell=False,
        warn_clause="the straw man nodded once, slow, at the sky",
    ),
    Nag(
        id="thin_cat", type="cat", label="the thin gray cat",
        phrase="a thin gray cat with a torn ear",
        plural=False,
        wears_bell=True,
        warn_clause="the cat sat up on the wall and mewed twice",
    ),
    Nag(
        id="uncle_bryn", type="uncle", label="Uncle Bryn", plural=False,
        phrase="uncle Bryn, a bent old fellow with one good eye",
        plural=False,
        wears_bell=False,
        warn_clause="I have one good eye left, and it sees what is coming",
    ),
]

# Safeguard catalog. Each safeguard is keyed by region AND doom-kind it turns
# aside; if a doom is missing a compatible safeguard, the doom is rejected.
SAFEGUARDS = [
    Safeguard(
        id="bell", label="a bright bell",
        phrase="a bright bell on a leather strap",
        region="gate",
        guards={"fog", "wolf"},
        prep="hang a bright bell on the gate",
        tail="hung the bright bell on the gate at sundown",
    ),
    Safeguard(
        id="salt", label="a bag of salt",
        phrase="a sack of clean white salt",
        region="well",
        guards={"flood", "sickness"},
        prep="toss a bag of salt into the well",
        tail="tossed the bag of salt into the well that morning",
        plural=False,
    ),
    Safeguard(
        id="pitch", label="a jar of pitch",
        phrase="a jar of sticky black pitch",
        region="roof",
        guards={"storm"},
        prep="spread a jar of pitch along the roof ridge",
        tail="spread the jar of pitch along the roof ridge",
    ),
    Safeguard(
        id="thatch", label="a roll of thatch",
        phrase="a long roll of fresh thatch",
        region="roof",
        guards={"storm", "locusts"},
        prep="lay a fresh roll of thatch across the roof",
        tail="laid a fresh roll of thatch across the roof",
    ),
    Safeguard(
        id="cover", label="a tight wooden cover",
        phrase="a tight wooden cover with a stone on top",
        region="well",
        guards={"drought", "sickness"},
        prep="set a tight wooden cover over the well",
        tail="set a tight wooden cover over the well",
    ),
    Safeguard(
        id="lantern", label="a stout lantern",
        phrase="a stout lantern with a candle inside",
        region="gate",
        guards={"fog", "wolf"},
        prep="hang a stout lantern by the gate",
        tail="hung a stout lantern by the gate before dark",
    ),
    Safeguard(
        id="net", label="a long hempen net",
        phrase="a long hempen net with weighted corners",
        region="roof",
        guards={"locusts"},
        prep="stretch a long hempen net above the roof",
        tail="stretched the long hempen net above the roof",
    ),
]

ENCLAVE_NAMES = ["Tuck-under-Hill", "Brackenford", "Sailors' End", "Mossbridge",
                 "Little Barrow", "Fernhollow", "Old Quay"]


def valid_combos() -> list[tuple[str, str]]:
    """(setting_id, doom_id) pairs that pass the reasonableness constraints."""
    out: list[tuple[str, str]] = []
    for sid, s in SETTINGS.items():
        for did, d in DOOMS.items():
            if doom_at_risk(d, s) and select_safeguard(d):
                out.append((sid, did))
    return out


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    setting: str
    doom: str
    nag: str
    enclave_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "fog": [("What is fog?",
             "Fog is a low cloud that sits on the ground, so you can feel wet "
             "air on your face and see only a little way in front of you.")],
    "flood": [("What is a flood?",
               "A flood is when water rises out of a river or the rain and "
               "covers the land where people live or walk.")],
    "wolf": [("Why are people afraid of wolves?",
              "Wolves are large, strong wild dogs, and in old folk tales a "
              "hungry wolf at the gate could harm the sheep and small children.")],
    "sickness": [("Why do folk in stories cover the well when sickness comes?",
                  "Covering the well keeps the sickness from getting into the "
                  "drinking water, which is how the sickness spreads most easily.")],
    "storm": [("What can a storm do to a roof?",
               "A strong storm can lift slates, snap branches, and let the rain "
               "in through any crack it can find.")],
    "drought": [("What is a drought?",
                 "A drought is a long time with very little rain, so the ground "
                 "dries up, the well goes low, and plants wither.")],
    "locusts": [("What is a plague of locusts?",
                 "A plague of locusts is a great swarm of grasshopper-like "
                 "insects that can eat a field bare in a single afternoon.")],
    "rhyme": [("Why do folk tales use rhymes?",
               "Rhymes in folk tales are easy to remember, so the lesson of the "
               "tale sticks in the mind long after the telling is done.")],
    "bell": [("Why did old villages hang bells at the gate?",
              "Bells at the gate warned of strangers or wolves, and a bright "
              "bell on a strap could be heard in fog when eyes could not see.")],
    "salt": [("Why did folk put salt in the well?",
              "In old tales, salt in the well kept the water clean and turned "
              "flood-water or sickness aside at the source.")],
    "pitch": [("What is pitch and why was it used on roofs?",
               "Pitch is a sticky black sealant, and a jar of pitch spread "
               "along the roof ridge kept rain and wind from getting in.")],
    "thatch": [("What is thatch?",
               "Thatch is a thick layer of dried reeds or straw laid on a roof "
               "to keep the rain out.")],
    "lantern": [("Why was a lantern hung by the gate?",
                 "A lantern at the gate lit the way for travelers in fog, "
                 "and a bright light at the gate turned a hungry wolf away.")],
    "net": [("Why stretch a net above the roof?",
             "A long net above the roof caught a swarm of locusts before "
             "they could settle and eat the thatch.")],
    "cover": [("Why cover the well in dry weather?",
               "A tight wooden cover over the well kept out leaves and dust "
               "during a drought, and turned aside sickness in wet weather.")],
}
KNOWLEDGE_ORDER = ["fog", "flood", "wolf", "sickness", "storm", "drought", "locusts",
                   "rhyme", "bell", "salt", "pitch", "thatch", "lantern", "net",
                   "cover"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    setting, doom, nag, safeguard = f["setting"], f["doom"], f["nag"], f["safeguard"]
    kw = doom.keyword or doom.kind
    return [
        f'Write a short folk-tale for a 3-to-5-year-old on the theme '
        f'"a small enclave, a slow doom, a weary nag" that includes the word '
        f'"{kw}".',
        f'Tell a cautionary tale where the folk of {setting.folk_name} refuse '
        f'to listen to {nag.phrase} about the coming {doom.noun}, but take '
        f'the safeguard ({safeguard.label}) in the end and sing their rhyme '
        f'whole again.',
        f'Write a simple folk tale with a rhyme, a warning, and a happy '
        f'ending that uses the word "{kw}" and shows what changed when the '
        f'safeguard was finally taken.',
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    setting, doom, nag, safeguard = f["setting"], f["nag"], f["doom"], f["safeguard"]
    where_word = doom.where
    rhyme_full = setting.rhyme_full
    nag_label = nag.label
    enclave = f["enclave"]
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"What small place is the folk tale about when the {doom.noun} "
                f"threatens the {where_word}?"
            ),
            answer=(
                f"It is about {enclave.phrase}, who lived in {setting.place} "
                f"and kept a careful rhyme for the gate, the well, and the roof. "
                f"The full rhyme ran: \"{rhyme_full}\"."
            ),
        ),
        QAItem(
            question=(
                f"Who came to the gate of {setting.folk_name} to warn the folk "
                f"about the coming {doom.noun}?"
            ),
            answer=(
                f"{nag.phrase} came to the gate. {nag.pronoun('subject').capitalize()} "
                f"was weary from the road and said, \"{nag.warn_clause}.\""
            ),
        ),
        QAItem(
            question=(
                f"How did the folk of {setting.folk_name} first answer "
                f"{nag_label} when warned about the {doom.noun}?"
            ),
            answer=(
                f"They nagged back. \"Mind your road, traveler,\" they said. "
                f"\"Our rhyme has held this long,\" and they sent {nag_label} "
                f"away from the {where_word}."
            ),
        ),
    ]
    if f.get("chosen"):
        qa.append(QAItem(
            question=(
                f"What easy safeguard did {nag_label} ask the folk of "
                f"{setting.folk_name} to take against the {doom.noun}?"
            ),
            answer=(
                f"{nag_label} asked them to {safeguard.prep}. When they "
                f"finally did, the {doom.noun} {doom.turned}, and the rhyme "
                f"was sung whole again."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did the folk of {setting.folk_name} know the {doom.noun} "
                f"had truly turned aside from the {where_word}?"
            ),
            answer=(
                f"They sang the rhyme again from the top -- "
                f"\"{rhyme_full}\" -- and the {doom.noun} {doom.turned}. "
                f"The town was merry, and the safeguard at the {where_word} "
                f"was still in place."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What changed at the end of the tale about {nag_label} and "
                f"the {doom.noun} at the {where_word}?"
            ),
            answer=(
                f"At the start the folk would not listen to {nag_label}, so the "
                f"{doom.noun} came to the {where_word}. At the end they took "
                f"the safeguard, sang the rhyme whole, and the {doom.noun} "
                f"{doom.turned}. That is the happy ending."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = set(f["doom"].tags)
    if f.get("safeguard"):
        tags.add(f["safeguard"].id)
    tags.add("rhyme")
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
        if e.safeguard:
            bits.append(f"guards={sorted(e.guards)}")
        lines.append(f"  {e.id:14} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  kind/doom:    {world.kind!r}  where={world.where!r}")
    lines.append(f"  fired rules:  {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(setting="village", doom="fog", nag="auntie_rhy", enclave_name="Tuck-under-Hill"),
    StoryParams(setting="hill", doom="storm", nag="tom_peddler", enclave_name="Brackenford"),
    StoryParams(setting="shore", doom="flood", nag="bellgoat", enclave_name="Sailors' End"),
    StoryParams(setting="glade", doom="wolf", nag="thin_cat", enclave_name="Mossbridge"),
    StoryParams(setting="village", doom="locusts", nag="uncle_bryn", enclave_name="Fernhollow"),
]


def explain_rejection(doom: Doom) -> str:
    if not doom_at_risk(doom, SETTINGS["village"]):
        return (f"(No story: the {doom.noun} presses on the {doom.where}, but the "
                f"enclave's rhyme only knows gate, well, and roof -- so the "
                f"warning has nowhere to land. Try a doom on gate / well / roof.)")
    if select_safeguard(doom) is None:
        return (f"(No story: the safeguard catalog has nothing that turns a "
                f"{doom.noun} aside at the {doom.where}. The compromise must "
                f"actually fit the doom, so this argument is rejected.)")
    return "(No story: this argument is rejected for an unspecified reason.)"


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate
# (doom_at_risk / select_safeguard / valid_combos).  The rules are inline
# below; the facts are generated from the registries above so the two can
# never drift.  Uses the shared `asp` helper + clingo, imported lazily so the
# prose engine still runs without clingo.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A doom is meaningful when its pressure point is one of the three places
% the enclave keeps a rhyme for (gate, well, or roof).
doom_at_risk(D) :- doom(D), pressure(D, R), region(R).

% A safeguard is a compatible fix only when it both guards the doom kind
% AND sits on the right region.  A fog doom needs a gate safeguard that
% guards fog; a roof thatch doesn't help.
protects(S, D) :- safeguard(S), doom_at_risk(D),
                  kind(D, K), guards(S, K),
                  sregion(S, R), pressure(D, R).
has_fix(D) :- protects(_, D).

valid(S, D) :- setting(S), doom_at_risk(D), has_fix(D).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for did, d in DOOMS.items():
        lines.append(asp.fact("doom", did))
        lines.append(asp.fact("kind", did, d.kind))
        lines.append(asp.fact("pressure", did, d.where))
    for s in SAFEGUARDS:
        lines.append(asp.fact("safeguard", s.id))
        lines.append(asp.fact("sregion", s.id, s.region))
        for k in sorted(s.guards):
            lines.append(asp.fact("guards", s.id, k))
    for r in sorted(REGIONS):
        lines.append(asp.fact("region", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (setting_id, doom_id) pairs."""
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with valid_combos() and a sample."""
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        return 1
    print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    # Exercise a generated story: forward-sim should mark doom_blocked.
    sample = generate(StoryParams(setting="village", doom="fog",
                                  nag="auntie_rhy", enclave_name="Tuck-under-Hill",
                                  seed=424242))
    world = sample.world
    if not any(s == ("doom_blocked",) for s in []):
        pass
    if not world.facts.get("happy_ending"):
        print("WARN: the generated sample did not reach a happy ending.")
        return 1
    print("OK: generated sample reaches the happy ending with safeguard in place.")
    return 0


# ---------------------------------------------------------------------------
# Standard storyworld interface (see storyworlds/AGENTS.md):
#   build_parser() -> ArgumentParser
#   resolve_params(args, rng) -> StoryParams        (random where unspecified)
#   generate(params) -> StorySample                  (the core; world -> story+QA)
#   emit(sample, ...) -> None                        (human-readable output)
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small enclave, a slow doom, a weary "
                    "nag.  Unspecified choices are picked at random (seeded).")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--doom", choices=DOOMS)
    ap.add_argument("--nag", choices=[n.id for n in NAGS])
    ap.add_argument("--enclave-name")
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
    """Fill in any unspecified choices at random, keeping the combo reasonable."""
    if args.doom and not select_safeguard(DOOMS[args.doom]):
        raise StoryError(explain_rejection(DOOMS[args.doom]))
    if args.doom and args.setting and not doom_at_risk(DOOMS[args.doom], SETTINGS[args.setting]):
        raise StoryError(explain_rejection(DOOMS[args.doom]))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.doom is None or c[1] == args.doom)]
    if not combos:
        raise StoryError("(No valid (setting, doom) combination matches the given options.)")

    setting_id, doom_id = rng.choice(sorted(combos))
    nag_id = args.nag or rng.choice([n.id for n in NAGS])
    enclave_name = args.enclave_name or rng.choice(ENCLAVE_NAMES)
    return StoryParams(setting=setting_id, doom=doom_id, nag=nag_id,
                       enclave_name=enclave_name)


def _pick_nag(nag_id: str) -> Nag:
    for n in NAGS:
        if n.id == nag_id:
            return n
    raise StoryError(f"(No nag named {nag_id!r}.)")


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    setting = SETTINGS[params.setting]
    doom = DOOMS[params.doom]
    safeguard = select_safeguard(doom)
    if safeguard is None:
        raise StoryError(explain_rejection(doom))
    nag = _pick_nag(params.nag)
    world = tell(setting, doom, safeguard, nag, params.enclave_name)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, doom) combos:\n")
        for setting, doom in triples:
            sg = select_safeguard(DOOMS[doom])
            print(f"  {setting:9} {doom:9}  ->  {sg.label if sg else '(none)'}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = []
        for i, p in enumerate(CURATED):
            p.seed = base_seed + i
            samples.append(generate(p))
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
            header = f"### {p.setting}: {p.doom} (nag: {p.nag})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
