#!/usr/bin/env python3
"""
storyworlds/worlds/baptize_gait_pulley_misunderstanding_space_adventure.py
=============================================================================

A standalone *story world* for a space misadventure involving mechanical failure,
misunderstandings across mission control and crew, and a central misunderstanding
that centers around baptizing a new settlement and the altered gait in low gravity
from a damaged pulley system.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 0.6

# Physical meter keys related to the mechanical failure chain
MECH_KINDS = {"damaged", "faulty", "worn", "loose"}

# Body region simulation for zero-gravity gait issues
REGIONS = {"legs", "torso", "arms"}

# ---------------------------------------------------------------------------
# Entities: characters and space equipment share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing" | "settlement"
    type: str = "thing"            # astronaut, engineer, settlement, pulley, ...
    label: str = ""                # short reference, e.g. "gantry crane"
    phrase: str = ""               # full noun phrase, e.g. "the reinforced titanium winch"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None   # who must fix/replace it
    operator: Optional[str] = None    # who is currently using it
    region: str = ""                  # where damage affects functional movement
    critical: bool = False            # if failure endangers mission
    covers: set[str] = field(default_factory=set)   # what regions it shields from malfunction
    plural: bool = False              # "wheels" -> them, "gear" -> it

    # Two numeric dimensions, treated uniformly:
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"engineer", "scientist", "pilot", "commander"}
        male = {"astronaut", "operator", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"commander": "commander", "engineer": "engineer", "astronaut": "astronaut"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "deep space station"
    low_g: bool = True
    affords: set[str] = field(default_factory=set)   # which activities this place supports


@dataclass
class Activity:
    """A central mechanical operation the hero wants to complete."""
    id: str
    verb: str            # after "wanted to ..."             : "test the new winch"
    gerund: str          # loved playing ... and ... : "calibrating the crane"
    rush: str            # tried to ...    : "rush to finish the calibration"
    flaw: str            # what goes wrong if bad state   : "failure to lift"
    locale: str          # where action occurs           : "docking bay"
    region: set[str]     # body regions the flaw affects: {"legs", "torso"}
    risk: str            # description of consequence    : "lose structural integrity"
    keyword: str = ""    # topic word for generation prompts
    tags: set[str] = field(default_factory=set)   # world-knowledge topics it touches


@dataclass
class System:
    """Critical shipboard apparatus whose failure launches the misadventure."""
    label: str
    phrase: str          # full description
    type: str = "pulley"
    flaws: list[str] = field(default_factory=list)  # kinds of damage
    region: str = ""    # region affected when degraded
    owner: str = "station"
    plural: bool = False


@dataclass
class Ceremony:
    """The communal naming ritual that starts the misunderstanding."""
    id: str
    detail: str
    locale: str
    planner: str
    ritual: str = "baptize"
    outcome: str = "save the settlement"
    tags: set[str] = field(default_factory=lambda: {"naming", "tradition"})


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()          # region affected by current flaw
        self.aborted: bool = False
        # Facts recorded during the screenplay, read back by the Q&A generators.
        self.facts: dict = {}
        # Special trace of quoted mission control dialogue
        self.dialogue: list[tuple[str, str, float]] = []

    # -- entity helpers -----------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def engineers(self) -> list[Entity]:
        return [e for e in self.characters() if "engineer" in e.type]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.operator == actor.id]

    def damaged(self, kind: str) -> bool:
        for e in self.entities.values():
            if e.meters[kind] >= THRESHOLD:
                return True
        return False

    # -- narration helpers --------------------------------------------------
    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def dialogue_caption(self, speaker: str, text: str, time: float = 0.0) -> None:
        self.dialogue.append((speaker, text, time))

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
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.dialogue = list(self.dialogue)
        return clone

# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_seize(world: World) -> list[str]:
    """Damaged apparatus grabs & alters gait when operator tries to use it."""
    out: list[str] = []
    flaw = next((f for f in MESS_KINDS if world.damaged(f)), "")
    for actor in world.characters():
        for item in world.worn_items(actor):
            if flaw and item.region in world.zone and not item.critical:
                sig = ("seize", item.id, flaw)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["malfunction"] += 1
                actor.memes["frustration"] += 0.8
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"captured {actor.pronoun('object')} mid-motion, "
                    f"altering {actor.pronoun('possessive')} gait and slowing progress."
                )
    return out

def _r_conflict(world: World) -> list[str]:
    """Mission control vs crew misunderstanding drives emotional memes upward."""
    high_frustration = any(a.memes["frustration"] > THRESHOLD for a in world.characters())
    if high_frustration:
        for actor in world.characters():
            if actor.type == "engineer":
                actor.memes["trust"] = max(0.0, actor.memes["trust"] - 0.5)
                return ["__conflict__"]
    return []

CAUSAL_RULES: list[Rule] = [
    Rule(name="seize", tag="physical", apply=_r_seize),
    Rule(name="misunderstand", tag="social", apply=_r_conflict),
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
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def ritual_at_risk(activity: Activity, system: System) -> bool:
    """Is the ceremony plausibly endangered if a critical system fails?"""
    return system.critical and "central" in activity.locale

def select_patch(activity: Activity, system: System) -> Optional[Entity]:
    """Find a spare that can actually fix the system's flaw."""
    for ent in list(flaw_registry.values()):
        if (system.flaws and ent.type == "spare" and
            ent.id in system.flaws and activity.locale in ent.placement):
            return ent.id
    return None

# ---------------------------------------------------------------------------
# Prediction: simulate a plausible patching run to see if the ritual can continue.
# ---------------------------------------------------------------------------
def predict_resolution(world: World, actor: Entity, activity: Activity,
                      system_id: str) -> dict:
    """Simulate installing the spare and report if the ceremony can complete."""
    sim = world.copy()
    if "pulley" in world.get(system_id).phrase:
        sim.get(system_id).meters["loose"] = 0.0
    ceremony = next((e for e in sim.entities.values() if "settlement" in e.type), None)
    return {
        "safe": ceremony is not None and not sim.aborted,
        "trust": sum(e.memes["trust"] for e in sim.characters()),
    }

# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def dusk_desc(setting: Setting) -> str:
    return (
        "The observation deck’s soft blue lights reflected off chrome railings "
        "and the infinite star-field beyond."
    ) if setting.place == "deep space station" else (
        "Morning light crept along the lunar regolith, painting silver streaks "
        "across the solar-panel grid."
    )

def posture_note(flaw: str) -> str:
    return {
        "loose": "teetered with each tug",
        "worn": "gave an unsettling lurch",
        "damaged": "shuddered ominously",
        "faulty": "twitched with false starts",
    }.get(flaw, "felt unsteady")

def _do_activity(world: World, actor: Entity, activity: Activity,
                system: System, narrate: bool = True) -> bool:
    if activity.id not in world.setting.affords:
        return False
    world.zone = set(activity.region)
    if "pulley" in system.phrase:
        world.get(system.id).meters[next(iter(MECH_KINDS))] += 0.4
    actor.memes["duty"] += 1
    propagate(world, narrate=narrate)
    return True

def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "veteran"), "").title()
    desc = f"{trait} {hero.type}".strip()
    world.say(f"{hero.id} was a seasoned {desc} posted to the edge of known space.")

def loves_ritual(world: World, hero: Entity, ceremony: Ceremony) -> None:
    hero.memes["purpose"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} had helped plan {ceremony.detail} for months: "
        f"a week-long ceremony to {ceremony.ritual} the new habitat "
        f"{ceremony.locale} in the settlers' names."
    )

def detect_flaw(world: World, actor: Entity, system: Entity) -> Optional[str]:
    """Engineer finds what’s wrong and warns crew of consequence."""
    flaw = next((f for f in MESS_KINDS if system.meters[f] >= THRESHOLD), None)
    if not flaw:
        return None
    consequence = "structural collapse" if system.critical else "system stuttering"
    world.facts["predicted_failure"] = (system.label, consequence)
    world.say(
        f'"Hold—{system.label} shows {flaw} at the {system.region}! '
        f'{posture_note(flaw)}. We face {consequence} in minutes."'
    )
    world.paragraphs[-1][-1] += f' {actor.pronoun("possessive")} voice cracked with alarm.'
    actor.memes["urgency"] += 1
    return flaw

def tries_twice(world: World, hero: Entity, system: Entity) -> None:
    hero.memes["determination"] += 0.7
    world.say(
        f"{hero.id} clenched controls and tried again—"
        f"the {system.label} {posture_note(next(iter(MECH_KINDS))} "
        f"and rattled like a seized motor."
    )

def grasp_protocol(world: World, operator: Entity, engineer: Entity) -> None:
    engineer.memes["trust"] -= 0.3
    engineer.memes["frustration"] += 0.9
    world.dialogue_caption(
        "Operator",
        '"They’re overriding my sequence! We hit the docking window in nine minutes!"',
        3.2,
    )
    world.dialogue_caption(
        "Engineer",
        '"Stand down until the inspection is green—we can’t risk the pulley!"',
        3.3,
    )
    world.say(
        f"{engineer.pronoun('possessive').capitalize()} commands vibrated "
        f"through the intercom, sharp enough to cut glass."
    )

def halts_procedure(world: World, operator: Entity, ceremony: Ceremony) -> None:
    world.aborted = True
    ceremony.planner = operator.id
    world.say(
        f"{operator.id} slammed a palm on the console and cut the feed. "
        f"{ceremony.detail} was postponed."
    )

def locate_spare(world: World, actor: Entity, system: System) -> Optional[Entity]:
    """Search for a part that fixes the specific flaw."""
    for spare_id, spare in SPARES.items():
        if (system.flaws and spare.type == "spare" and
            spare_id in system.flaws and system.region in spare.covers):
            actor.memes["hope"] += 1
            return world.add(Entity(
                id=spare_id,
                type="spare", label=spare.label, phrase=spare.phrase,
                owner=actor.id, region=system.region, covers=spare.covers,
            ))
    return None

def patch_attempt(world: World, actor: Entity, system: Entity, spare: Entity) -> bool:
    """Attempt to swap in the spare."""
    flaw = next((f for f in MESS_KINDS if system.meters[f] >= THRESHOLD), None)
    if not flaw:
        return False
    world.facts["patched"] = True
    actor.memes["relief"] += 1
    system.meters[flaw] = 0.0
    world.say(
        f"{actor.id} swapped the {spare.label} in and powered the "
        f"{system.label}—after a shudder, it spun smooth again."
    )
    return True

def continue_ritual(world: World, ceremony: Ceremony, settler: Entity) -> None:
    """A shortened, symbolic ceremony saves the moment."""
    world.say(
        f"At twilight, under the colony’s canopy of mirrors and LEDs, "
        f"{settler.pronoun()} {ceremony.ritual}ed the hallowed dome "
        f"in absentia, naming it '{ceremony.locale.title()}' for generations yet unborn."
    )
    settler.memes["legacy"] += 1

# ---------------------------------------------------------------------------
# The screenplay: three-act structure tailored for high-stakes space misadventure.
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity,
         system_cfg: System, ceremony_cfg: Ceremony,
         hero_name: str = "Riley", hero_type: str = "engineer",
         lead_type: str = "commander") -> World:
    world = World(setting)

    # Primary cast
    hero = world.add(Entity(
        id=hero_name,
        kind="character", type=hero_type,
        traits=["veteran", "methodical"],
    ))
    lead = world.add(Entity(id="Lead", kind="character", type=lead_type, label="the duty officer"))

    # Central mechanical antagonist
    system = world.add(Entity(
        id="primary_pulley",
        type=system_cfg.type,
        label=system_cfg.label,
        phrase=system_cfg.phrase,
        owner="station", critical=True, region=system_cfg.region,
    ))

    # Settlement to name
    settlement = world.add(Entity(
        id="NewHaven",
        kind="settlement", type="habitat",
        label="New Haven",
        phrase="the cylindrical habitat ring designated New Haven",
    ))

    # Central ceremonial goal
    ceremony = world.add(Entity(
        id=ceremony_cfg.id,
        type="ceremony", label=ceremony_cfg.ritual,
        phrase=ceremony_cfg.detail,
        owner=ceremony_cfg.planner,
    ))

    # Act 1 – Setup: personnel, equipment, upcoming importance of naming
    introduce(world, hero)
    hero.memes["task"] += 1
    loves_ritual(world, lead, ceremony)

    # Act 2 – Conflict: flaw discovered, communication collapse, near abort
    world.para()
    world.say(dusk_desc(setting))
    world.say(
        f"Tonight, the crew would {ceremony.ritual} {settlement.label} "
        f"in a simple, communal act of binding."
    )

    _do_activity(world, hero, activity, system)
    flaw_detected = detect_flaw(world, hero, system)
    if flaw_detected:
        spare = locate_spare(world, hero, system_cfg)
        if not spare:
            world.para()
            tries_twice(world, hero, system)
            world.para()
            grasp_protocol(world, lead, hero)
            world.para()
            halts_procedure(world, lead, ceremony)
            world.facts["resolved"] = False
            return world

        world.para()
        patch_ok = patch_attempt(world, hero, system, spare)
        if patch_ok:
            world.facts["resolved"] = True
            continue_ritual(world, ceremony, settlement)
        else:
            world.para()
            halts_procedure(world, lead, ceremony)
            world.facts["resolved"] = False

    # Record world facts for QA
    world.facts.update(
        hero=hero, lead=lead, system=system,
        ceremony=ceremony, settlement=settlement,
        flaw=flaw_detected, resolved=world.facts.get("resolved"),
        dialogue=world.dialogue,
    )
    return world

# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "station": Setting(
        place="deep space station", low_g=True,
        affords={"calibrate", "inspect", "repair"},
    ),
    "lunar": Setting(
        place="surface moon base", low_g=False,
        affords={"deploy", "erect"},
    ),
}

ACTIVITIES = {
    "calibrate": Activity(
        id="calibrate",
        verb="calibrate the new winch",
        gerund="carefully calibrating the docking crane",
        rush="rush to finish the calibration before shift change",
        flaw="gives a false lift reading",
        locale="docking bay",
        region={"torso", "arms"},
        risk="misaligned module anchoring",
        keyword="pulley",
        tags={"calibration", "mechanical", "spacewalk"},
    ),
    "deploy": Activity(
        id="deploy",
        verb="deploy the feed mast",
        gerund="meticulously deploying the feed mast",
        rush="speed the mast into position before lunar dusk",
        flaw="refuses correct orientation",
        locale="south ridge",
        region={"legs"},
        risk="loss of solar collection for a week",
        keyword="gait",
        tags={"solar", "structural", "lunar"},
    ),
}

SYSTEMS = {
    "winch": System(
        label="primary starboard winch",
        phrase="the reinforced titanium winch at the docking port",
        region="torso",
        flaws=["loose", "worn"],
        owner="station",
    ),
    "pulley": System(
        label="axial pulley hub",
        phrase="the central winch assembly that governs habitat module orientation",
        region="torso",
        flaws=["damaged", "faulty"],
    ),
    "feed": System(
        label="feed mast",
        phrase="the 3-meter solar-feed mast on the ridge",
        region="legs",
        flaws=["loose", "worn"],
    ),
}

CEREMONIES = {
    "name": Ceremony(
        id="name_ritual",
        detail="the naming of the New Haven ring at dusk tomorrow",
        locale="New Haven",
        planner="settlers' council",
    ),
}

SPARES = {
    "conduit_spacer": System(
        label="short conduit spacer",
        phrase="an exact-fit titanium spacer for the axial pulley hub",
        type="spare", region="torso",
        covers={"torso"},
    ),
    "adapter": System(
        label="male adapter ring",
        phrase="an adapter ring for the lunar feed mast socket",
        type="spare", region="legs",
        covers={"legs"},
    ),
}

GIVEN_NAMES = ["Riley", "Jamie", "Alex", "Case", "Taylor", "Morgan"]
TRAITS = ["methodical", "patient", "tenacious", "curious", "logical"]

# ---------------------------------------------------------------------------
# StoryParams – the per-world knobs.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    system: str
    ceremony: str
    name: str
    role: str
    lead_role: str
    trait: str
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# Q&A generation – three distinct sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "baptize": [("What does it mean to baptize a habitat?",
                 "Baptizing a habitat means giving it an official name "
                 "in a brief naming ceremony so settlers feel a sense of home "
                 "and continuity,"),
                 ("Why do space settlers name places?",
                 "Naming a place links memory, purpose, and community identity, "
                 "turning mechanical outposts into claimed homes.")],
    "pulley": [("What is a pulley?",
                "A pulley is a wheel with a rope or chain that changes the "
                "direction of a force, used here to raise or orient heavy modules.")],
    "gait": [("Why is gait important in low gravity?",
              "Low gravity changes how astronauts move; irregular gait can "
              "signal equipment interference or even suit damage.")],
    "misunderstand": [("What causes misunderstandings in space crews?",
                     "Misunderstandings arise from communication delays, "
                     "pressure to act, and ambiguous sensor data that humans must "
                     "interpret in real time.")],
}

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act, sys, cer = f["activity"], f["system"], f["ceremony"]
    return [
        f'Write a short story for children about a space adventure titled '
        f'"Pulling Together" featuring the words {act.keyword}, '
        f'{sys.label}, and the {cer.detail}.',
        f"Tell a STEM-friendly story where a {f['hero'].type} tries to "
        f"{act.verb} but a small mechanical flaw creates "
        f"a misunderstanding between astronauts and mission control.",
        f'Craft a gentle space tale that includes the noun "{act.keyword}" '
        f"and describes a calm resolution after communication breaks down.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h, l = f["hero"], f["lead"]
    sub, obj, pos = h.pronoun("subject"), h.pronoun("object"), h.pronoun("possessive")
    sys, act = f["system"], f["activity"]
    where = "zero-gravity bay" if world.setting.low_g else "lunar ridge"

    qa: list[QAItem] = [
        QAItem(
            question=("Who was the veteran engineer trying to finish the "
                     f"{act.gerund} in {where} at twilight?"),
            answer=(
                f"The veteran {h.type} {h.id} was the engineer in charge of "
                f"the {act.gerund} in {where} at twilight using the "
                f"{sys.phrase}."
            ),
        ),
        QAItem(
            question=(
                f"What simple communal ritual would the crew perform "
                f"that evening in New Haven?"
            ),
            answer=(
                f"That evening, the crew would {f['ceremony'].phrase}— "
                f"a naming ceremony that bound settlers to their new home."
            ),
        ),
        QAItem(
            question=(
                f"What mechanical flaw in the {sys.label} revealed itself "
                f"just as {h.id} started {act.gerund}?"
            ),
            answer=(
                f"As {h.id} prepared to {act.gerund}, the {sys.label} "
                f"showed {next(iter(MECH_KINDS))} at the {sys.region}; "
                f"it began {sys.phrase} {posture_note(next(iter(MECH_KINDS))}."
            ),
        ),
    ]

    if f.get("flaw"):
        qa.append(QAItem(
            question=(
                f"Why did mission control have to postpone the naming "
                f"ritual {f['ceremony'].id}?"
            ),
            answer=(
                f"Because the {sys.label} was critical to station alignment "
                f"and {h.id}’s attempt to patch it failed; Lead ordered a "
                f"hold to avoid risking collapse."
            ),
        ))

    if f.get("resolved"):
        qa.append(QAItem(
            question=(
                f"How did the crew finally finish the baptism of New Haven "
                f"after the mechanical fault?"
            ),
            answer=(
                f"They installed a {next(s for s in SPARES.values()).label}, "
                f"mitigated the {next(iter(MESS_KINDS))} in the {sys.label}, "
                f"and completed a symbolic naming rite at twilight under "
                f"LEDs and mirrors."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did the veteran {h.type} feel once the {sys.label} "
                f"rotated smoothly again?"
            ),
            answer=(
                f"{h.id} felt quiet relief; the crew could now proceed "
                f"with {f['ceremony'].ritual}ing New Haven in absentia, "
                "leaving a name for future settlers."
            ),
        ))

    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {act.keyword for act in ACTIVITIES.values()}
    if f.get("system"):
        tags.update(f["system"].flaws)
    if f.get("dialogue"):
        tags.add("misunderstand")
    out: list[QAItem] = []
    for tag in ["baptize", "pulley", "gait", "misunderstand"]:
        if tag in tags:
            out.extend(QAItem(q,a) for q,a in KNOWLEDGE[tag])
    return out

def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# ASP twin – inline clingo rules validating story combinations.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A ceremony can only happen if no critical system malfunctions.
safe_for_ceremony(C) :- ceremony(C), not critical_failure.

% Critical failures are systems whose meter crossed a threshold.
critical_failure :- system(S), critical(S), damaged(S, M, V), V >= 0.6.

% A patch must match the system’s flaw and region to resolve it.
patches_system(P,S) :- spare(P), system(S), flaw_of(P,M), covers(P,R),
                       covers(S,R), mess_of(S,M).

% Activity locale must be supported by the current setting.
place_supports(P, L, A) :- place(P), locale(A, L), setting_supports(P,A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("setting_supports", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("locale", aid, a.locale))
        if a.keyword:
            lines.append(asp.fact("keyword", aid, a.keyword))
    for sid, sys in SYSTEMS.items():
        lines.append(asp.fact("system", sid))
        if sys.critical:
            lines.append(asp.fact("critical", sid))
        for r in sorted(sys.region.split()):
            lines.append(asp.fact("covers", sid, r))
        for f in sys.flaws:
            lines.append(asp.fact("flaw_of", sid, f))
    for cid, cer in CEREMONIES.items():
        lines.append(asp.fact("ceremony", cid))
        lines.append(asp.fact("ritual", cid, cer.ritual))
    for pid, spare in SPARES.items():
        lines.append(asp.fact("spare", pid))
        lines.append(asp.fact("type", pid, "spare"))
        for r in sorted(spare.covers):
            lines.append(asp.fact("covers", pid, r))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_for_ceremony/1."))
    return sorted(set(asp.atoms(model, "safe_for_ceremony")))

def asp_verify() -> int:
    import asp
    clingo_ok = set(asp_valid_stories())
    python_ok = {True}
    if clingo_ok == python_ok:
        print("OK: both ASP and Python declare the domain reasonable.")
        return 0
    print("MISMATCH: ASP and Python parity failure.")
    return 1

# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space-adventure story world: a mechanical flaw, "
                    "miscommunication, and a naming ceremony that threads it together.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--system", choices=SYSTEMS)
    ap.add_argument("--ceremony", choices=CEREMONIES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["engineer", "captain", "pilot"])
    ap.add_argument("--lead-role", choices=["commander", "lead_operator"])
    ap.add_argument("--trait")
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
    if args.activity and args.system:
        act, sys = ACTIVITIES[args.activity], SYSTEMS[args.system]
        if not ritual_at_risk(act, sys):
            raise StoryError(
                f"(No story: {sys.label} is not critical for the "
                f"{act.detail} in {act.locale}; choose something central.)"
            )

    gender_ok = ("role" not in args) or args.role in ["engineer", "pilot", "captain"]
    if not gender_ok:
        raise StoryError("(No story: --role must be engineer, pilot, or captain.)")

    settings = [s for s in SETTINGS.keys()]
    activities = [a for a in ACTIVITIES.keys() if not args.activity or a == args.activity]
    systems   = [s for s in SYSTEMS.keys()   if not args.system   or s == args.system]
    roles     = ["engineer"] if not args.role else [args.role]
    leads     = ["commander"] if not args.lead_role else [args.lead_role]

    # Curated combos (subset of valid stories used by --all)
    CURATED = [
        StoryParams(
            place="station", activity="calibrate", system="winch",
            ceremony="name", name="Riley", role="engineer",
            lead_role="commander", trait="methodical",
        ),
        StoryParams(
            place="lunar", activity="deploy", system="feed",
            ceremony="name", name="Jamie", role="pilot",
            lead_role="commander", trait="patient",
        ),
    ]

    if args.all:
        return rng.choice(CURATED)

    candidates = [
        StoryParams(
            place=rng.choice(settings),
            activity=rng.choice(activities),
            system=rng.choice(systems),
            ceremony="name",
            name=rng.choice(GIVEN_NAMES),
            role=rng.choice(roles),
            lead_role=rng.choice(leads),
            trait=rng.choice(TRAITS),
        )
        for _ in range(100)
    ]
    # Filter for stories where:
    #  - activity locale is supported by setting
    #  - system is critical OR locale matches activity locale
    candidates = [
        p for p in candidates
        if SETTINGS[p.place].affords & {p.activity} and (
            SYSTEMS[p.system].critical or
            ACTIVITIES[p.activity].locale in {"docking bay", "south ridge"}
        )
    ]
    if not candidates:
        raise StoryError("(No valid combination matches constraints.)")

    return rng.choice(candidates)

def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        SYSTEMS[params.system],
        CEREMONIES[params.ceremony],
        params.name, params.role, params.lead_role,
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
        print("\n--- world live model ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v and k in MESS_KINDS}
            if meters:
                print(f"{e.id:20} meters={meters}")
        print(f"\nrules fired: {sorted(set(sample.world.fired))}")
    if qa:
        print("\n" + format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe_for_ceremony/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        safe = asp_valid_stories()
        print(f"{len(safe)} clergy-safe stories ready for the Curated Set.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(
            place="station", activity="calibrate", system="winch",
            ceremony="name", name="Riley", role="engineer", lead_role="commander",
            trait="methodical",
        ))]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.role} vs {p.system} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
