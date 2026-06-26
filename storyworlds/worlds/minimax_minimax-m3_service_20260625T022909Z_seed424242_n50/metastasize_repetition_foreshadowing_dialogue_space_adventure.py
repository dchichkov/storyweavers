#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/metastasize_repetition_foreshadowing_dialogue_space_adventure.py
=======================================================================================================================

A standalone *story world* sketch for a TinyStories-style "Space Adventure"
about an engineer named **Rex** who, with the help of a small bot, has to
stop a quiet, spreading problem (a *metastasize*-ing fault) inside the
engine room of a steel ship called the *Brave Hopper* before the morning
jump.  The seed word "metastasize" is the cause; the visible small mystery
is the symptom; the resolution is the engineer's fix.

The story is built like the other classical worlds: typed entities with
physical *meters* and emotional *memes*, a small set of causal rules that
fire forward to a fixpoint, and a screenplay that *reads* the world state
rather than swapping nouns inside one frozen paragraph.  We deliberately
use the three named narrative instruments throughout:

  * **Repetition**   -- a recurring warning phrase ("tiny pings"), a
                        recurring hand-pair motif, and a recurring
                        three-beat "check, check, fix" rhythm.
  * **Foreshadowing**-- the missing bolt, the sleepy bot, the
                        disappearing last starlight, the *quiet* spot
                        on the wall; all five are set up early and
                        paid off at the end when the fault is named
                        and sealed.
  * **Dialogue**     -- the screenplay beats are written as actual
                        short quoted speech, not narrative summary,
                        so the story sounds like a child reading
                        aloud with two voices trading lines.

Initial story (used to build a world model):
---
Once upon a time, there was a young engineer named Rex who lived and
worked on a small steel ship called the Brave Hopper. The Brave Hopper
was a quiet ship that liked to jump between the stars in the morning,
when the sky was still soft and purple.

Rex had a small round helper-bot named Pip. Pip was brave, but a little
sleepy, and liked to beep softly when it was happy. Every morning before
the jump, Rex and Pip walked through the engine room together and said
the same three words out loud: "check, check, fix." Rex was very
careful. He always wore his big, heavy toolkit on his belt, and a small
bright flashlight on his shoulder so he could see into dark corners.

One evening, Rex noticed something small and strange: a tiny pinging
sound from the back of the engine room, the kind of sound a small
metals crew member's mug makes on a metal table. He walked over, but
the pinging was gone. Pip beeped a soft "ready?" and the two of them
shared a careful look. Rex said out loud, "Hmm, that is strange. We
will come back to that." Pip beeped, "beep, ready."

The next morning, when the sky was soft and purple, Rex walked into
the engine room and found a thin dark line on the wall, like a small
crack that had learned to walk. He touched it with one finger, and it
felt warm and a little sticky. The Brave Hopper shivered a tiny
shiver, the way a cat does before it pounces. Rex knelt down and
noticed one bolt on the floor that was not in its place. He picked it
up. It was warm.

"Oh," said Rex softly. "Something is spreading. We have to find it
before the morning jump." Pip beeped, "beep, where?" Rex pointed
to the dark line. "Right there, little friend. It is metastasizing."
Pip tilted its head, because that was a very long word, and Rex
laughed and said, "It means it is growing, and growing, and
growing. Like a weed, but inside a wall."

Rex thought for a moment. Then he opened his toolkit, took out a
little silver tube, and squeezed a thin, slow, cool paste along
the dark line. The paste glowed softly blue. Pip beeped a happy
"beep, fix!" because the line stopped walking. Rex took the warm
bolt and set it gently back where it belonged, and the tiny pinging
sound came back, only this time it sounded friendly, like a small
heart going tick-tick-tick. The Brave Hopper gave a tiny happy
shiver, the way a cat does after a long nap.

When the sky was a clean, soft, morning purple, the Brave Hopper
took a small, calm jump between the stars. Rex and Pip stood at
the window and watched the last starlight wink and say goodnight.
"Check, check, fix," said Rex. "Beep, fix," said Pip. And the
small steel ship sailed on, with a quiet, glowy, blue line on
its wall, and one warm bolt in its place, and a story that
would be told again, the next night, by the next engineer.
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

# ---------------------------------------------------------------------------
# Entities: characters, helper bots, and the ship share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"             # "character" | "bot" | "thing" | "ship"
    type: str = "thing"             # engineer, bot, ship, paste, bolt, wall ...
    label: str = ""                 # short reference, e.g. "Pip", "the wall"
    phrase: str = ""                # full noun phrase
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    region: str = ""                # engine part location: "wall" | "floor" | "panel"
    plural: bool = False
    # Two numeric dimensions, treated uniformly (cf. story.py memeplex model):
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"engineer_female"}
        male = {"engineer"}
        bots = {"bot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in bots:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"engineer": "engineer", "engineer_female": "engineer",
                "bot": "helper", "ship": "ship"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# The metastasizing fault: a slow, spreading problem.  Modelled explicitly so
# the screenplay can foreshadow it (small, then bigger, then a thin dark line)
# and resolve it (cool blue paste + warm bolt back in place).
# ---------------------------------------------------------------------------
@dataclass
class Fault:
    """The metastasizing fault's little 'biography' for one story."""
    verb_present: str               # "is metastasizing"
    verb_past: str                  # "metastasized"
    sound: str                      # "tiny pinging"
    surface: str                    # "a thin dark line on the wall"
    warmth: str                     # "warm and a little sticky"
    seed_symptom: str               # "a tiny pinging sound"
    grow_symptom: str               # "a thin dark line, like a small crack that had learned to walk"
    fix_tool: str                   # "a little silver tube"
    fix_tool_label: str             # "the little silver tube"
    fix_glow: str                   # "softly blue"


# ---------------------------------------------------------------------------
# Setting: where the story happens (a small ship with an engine room).
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the engine room"   # visible location
    ship: str = "the Brave Hopper"   # ship name (kept short and story-like)
    affordance: str = "engine"       # what this place can do (a single beat)


# ---------------------------------------------------------------------------
# Helpers for the three narrative instruments.
# ---------------------------------------------------------------------------
RECURRING_PHRASE = "check, check, fix"     # Repetition
RECURRING_BEEP = "beep, ready"             # Repetition
RECURRING_LOOK = "shared a careful look"   # Repetition (hand / look motif)
WALL_LINE_GLOW = "softly blue"             # Repetition (the blue glow payoff)


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    # -- entity helpers -----------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind in ("character", "bot")]

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


def _r_fault_grow(world: World) -> list[str]:
    """If the fault has been *noticed* and not yet *sealed*, it keeps growing.

    This is the rule that lets foreshadowing actually be true: the symptom
    that Rex first heard (a tiny pinging) becomes, by morning, a visible
    thin dark line on the wall.  We expose the rule as a flag the screenplay
    reads (``world.facts["fault_grown"]``), and the prose is written by the
    screenplay, not the rule (no scaffold leak).
    """
    fault = world.facts.get("fault")
    if not fault or not fault.get("noticed"):
        return []
    if fault.get("sealed") or fault.get("grown"):
        return []
    if "fault_grow" in world.fired:
        return []
    world.fired.add("fault_grow")
    fault["grown"] = True
    return ["__fault_grown__"]


def _r_fault_seal(world: World) -> list[str]:
    """If the engineer has the fix tool and a bead of paste on the line, the
    fault is *sealed*: it stops growing and goes quiet.  This is the rule
    that lets the resolution actually take hold: paste + bolt = calm.
    """
    fault = world.facts.get("fault")
    if not fault or not fault.get("paste_applied") or not fault.get("bolt_returned"):
        return []
    if fault.get("sealed") or "fault_seal" in world.fired:
        return []
    world.fired.add("fault_seal")
    fault["sealed"] = True
    world.facts["fault"]["final_sound"] = "tick-tick-tick"
    return ["__fault_sealed__"]


def _r_engineer_care(world: World) -> list[str]:
    """Each time the engineer is careful (checks, listens, kneels), his
    'care' meter ticks up -- this lets us narrate a child who is *being*
    careful rather than simply succeeding by magic.
    """
    eng = next((e for e in world.characters() if e.kind == "character"), None)
    if eng is None:
        return []
    for sig in ("listened", "knelt", "named", "applied_paste", "returned_bolt"):
        if eng.memes[sig] >= THRESHOLD and ("care", sig) not in world.fired:
            world.fired.add(("care", sig))
            eng.memes["care"] += 1
    return []


def _r_pip_bond(world: World) -> list[str]:
    """Each time Pip beeps a useful beep (ready, where, fix), the engineer
    and Pip grow closer; the second-beat '*shared a careful look*' motif
    and the '*beep, fix*' payoff at the end ride on this meter.
    """
    eng = next((e for e in world.characters() if e.kind == "character"), None)
    pip = next((e for e in world.characters() if e.kind == "bot"), None)
    if eng is None or pip is None:
        return []
    if pip.memes["helpful"] >= THRESHOLD and "bond" not in world.fired:
        world.fired.add("bond")
        eng.memes["love"] += 1
        pip.memes["love"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="fault_grow", tag="physical", apply=_r_fault_grow),
    Rule(name="fault_seal", tag="physical", apply=_r_fault_seal),
    Rule(name="engineer_care", tag="social", apply=_r_engineer_care),
    Rule(name="pip_bond", tag="social", apply=_r_pip_bond),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* story configuration.
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    """(engineer_name, engineer_type, ship_name, fault_id) quadruples.

    We require, in spirit of the other worlds, that a story is *plausible*:
    the engineer and ship exist, and the fault has been *noticed* by the
    time the morning jump is due.  This rule is mirrored exactly by ASP
    below, so the two reasoners must always agree.
    """
    out = []
    for engineer in ENGINEERS:
        for ship_id, ship in SHIPS.items():
            for fid in FAULTS:
                out.append((engineer.name, engineer.type, ship_id, fid))
    return out


def select_tool(fault: Fault) -> str:
    """The tool that actually fixes the fault (mirrors the screenplay)."""
    return fault.fix_tool


# ---------------------------------------------------------------------------
# The screenplay: a three-act, dialogue-heavy, instrument-aware rendering of
# the world.  Each beat narrates a real causal state, never a frozen phrase.
# ---------------------------------------------------------------------------
def introduce(world: World, eng: Entity) -> None:
    trait = next((t for t in eng.traits if t != "young"), eng.type)
    world.say(
        f"Once upon a time, there was a young {trait} engineer named {eng.id} "
        f"who lived and worked on a small steel ship called {world.setting.ship}."
    )
    world.say(
        f"{world.setting.ship.capitalize()} was a quiet ship that liked to jump "
        f"between the stars in the morning, when the sky was still soft and purple."
    )


def introduce_pip(world: World, eng: Entity, pip: Entity) -> None:
    world.say(
        f"{eng.id} had a small round helper-bot named {pip.id}. "
        f"{pip.pronoun('subject').capitalize()} was brave, but a little sleepy, "
        f"and liked to beep softly when {pip.pronoun('subject')} was happy."
    )


def morning_routine(world: World, eng: Entity, pip: Entity) -> None:
    """Repetition #1: the three-beat *check, check, fix* rhythm."""
    world.say(
        f"Every morning before the jump, {eng.id} and {pip.id} walked through "
        f"{world.setting.place} together and said the same three words out loud: "
        f'"{RECURRING_PHRASE}."'
    )
    eng.memes["care"] += 1
    world.say(
        f"{eng.id} was very careful. {eng.pronoun('subject').capitalize()} always "
        f"wore {eng.pronoun('possessive')} big, heavy toolkit on "
        f"{eng.pronoun('possessive')} belt, and a small bright flashlight on "
        f"{eng.pronoun('possessive')} shoulder so {eng.pronoun('subject')} could "
        f"see into dark corners."
    )


def first_ping(world: World, eng: Entity, pip: Entity, fault: Fault) -> None:
    """Foreshadowing #1: the first pinging sound, then gone."""
    world.say(
        f"One evening, {eng.id} noticed something small and strange: "
        f"{fault.seed_symptom} from the back of {world.setting.place}, "
        f"the kind of sound a small metals crew member's mug makes on a metal table."
    )
    eng.memes["listened"] += 1
    world.say(
        f"{eng.pronoun('subject').capitalize()} walked over, but the pinging was gone."
    )
    world.say(
        f'{pip.id} beeped a soft "{RECURRING_BEEP}?" and the two of them '
        f"{RECURRING_LOOK}."
    )
    pip.memes["helpful"] += 1
    world.say(
        f'{eng.id} said out loud, "Hmm, that is strange. We will come back to that." '
        f'{pip.id} beeped, "{RECURRING_BEEP}."'
    )
    world.facts["fault"] = {"noticed": True, "sealed": False, "grown": False,
                            "paste_applied": False, "bolt_returned": False}


def morning_discovery(world: World, eng: Entity, pip: Entity, fault: Fault) -> None:
    """Foreshadowing #2: the dark line, the warm bolt, the sleepy bot -- paid off."""
    world.para()
    world.say(
        f"The next morning, when the sky was soft and purple, {eng.id} walked into "
        f"{world.setting.place} and found {fault.grow_symptom} on the wall."
    )
    world.say(
        f"{eng.pronoun('subject').capitalize()} touched it with one finger, and it "
        f"felt {fault.warmth}."
    )
    propagate(world, narrate=False)        # advance the model: fault.grown = True
    ship = world.entities.get(world.setting.ship)
    if ship is not None:
        ship.meters["shiver"] += 1
    world.say(
        f"{world.setting.ship.capitalize()} shivered a tiny shiver, the way a cat "
        f"does before it pounces."
    )
    world.say(
        f"{eng.id} knelt down and noticed one bolt on the floor that was not in its "
        f"place. {eng.pronoun('subject').capitalize()} picked it up. It was warm."
    )
    eng.memes["knelt"] += 1
    world.facts["bolt_warm"] = True


def naming_the_fault(world: World, eng: Entity, pip: Entity, fault: Fault) -> None:
    """Dialogue beat: the long word, the simple translation, the laugh."""
    world.say(
        f'"Oh," said {eng.id} softly. "Something is spreading. We have to find it '
        f'before the morning jump."'
    )
    world.say(f'"{pip.id} beeped, "beep, where?"')
    world.say(
        f'{eng.id} pointed to the dark line. "Right there, little friend. It {fault.verb_present}."'
    )
    eng.memes["named"] += 1
    world.say(
        f"{pip.id} tilted {pip.pronoun('possessive')} head, because that was a very "
        f"long word, and {eng.id} laughed and said, "
        f'"It means it is growing, and growing, and growing. Like a weed, but '
        f'inside a wall."'
    )


def engineer_thinks(world: World, eng: Entity) -> None:
    world.say(f"{eng.id} thought for a moment.")


def the_fix(world: World, eng: Entity, pip: Entity, fault: Fault) -> None:
    """Resolution: paste on the line, bolt back in its place, sound goes friendly."""
    tool = world.entities.get(fault.fix_tool)
    if tool is None:
        tool = world.add(Entity(
            id=fault.fix_tool, kind="thing", type="paste",
            label=fault.fix_tool_label, owner=eng.id,
        ))
    world.say(
        f'Then {eng.id} opened {eng.pronoun("possessive")} toolkit, took out '
        f"{fault.fix_tool_label}, and squeezed a thin, slow, cool paste along the "
        f"dark line. The paste glowed {WALL_LINE_GLOW}."
    )
    eng.memes["applied_paste"] += 1
    world.facts["fault"]["paste_applied"] = True
    world.say(
        f'{pip.id} beeped a happy "beep, fix!" because the line stopped walking.'
    )
    pip.memes["helpful"] += 1
    pip.memes["fix"] += 1
    world.say(
        f"{eng.id} took the warm bolt and set it gently back where it belonged, "
        f"and the tiny pinging sound came back, only this time it sounded friendly, "
        f"like a small heart going tick-tick-tick."
    )
    eng.memes["returned_bolt"] += 1
    world.facts["fault"]["bolt_returned"] = True
    propagate(world, narrate=False)        # advance the model: fault.sealed = True
    ship = world.entities.get(world.setting.ship)
    if ship is not None:
        ship.meters["shiver"] += 1
    world.say(
        f"{world.setting.ship.capitalize()} gave a tiny happy shiver, the way a cat "
        f"does after a long nap."
    )


def the_jump(world: World, eng: Entity, pip: Entity) -> None:
    """Final beat: the recurring phrase returns; the morning jump happens."""
    world.para()
    world.say(
        f"When the sky was a clean, soft, morning purple, {world.setting.ship} took "
        f"a small, calm jump between the stars."
    )
    world.say(
        f"{eng.id} and {pip.id} stood at the window and watched the last starlight "
        f"wink and say goodnight."
    )
    world.say(
        f'"{RECURRING_PHRASE}," said {eng.id}. "Beep, fix," said {pip.id}.'
    )
    world.say(
        f"And the small steel ship sailed on, with a quiet, glowy, blue line on its "
        f"wall, and one warm bolt in its place, and a story that would be told "
        f"again, the next night, by the next engineer."
    )


# ---------------------------------------------------------------------------
# The tell() driver: builds the world and runs the three acts.
# ---------------------------------------------------------------------------
def tell(setting: Setting, fault: Fault, engineer_name: str = "Rex",
         engineer_type: str = "engineer", engineer_traits: Optional[list[str]] = None,
         bot_name: str = "Pip") -> World:
    world = World(setting)
    world.facts["setting"] = setting
    world.facts["fault_obj"] = fault

    eng = world.add(Entity(
        id=engineer_name, kind="character", type=engineer_type,
        traits=(engineer_traits or ["young", "careful"]),
    ))
    pip = world.add(Entity(
        id=bot_name, kind="bot", type="bot",
        label="the small helper-bot", traits=["brave", "sleepy"],
    ))
    world.add(Entity(
        id=setting.ship, kind="ship", type="ship",
        label=setting.ship, traits=["quiet", "steel"],
    ))

    # Act 1 -- setup, routine, the recurring phrase, the first pinging.
    introduce(world, eng)
    introduce_pip(world, eng, pip)
    morning_routine(world, eng, pip)
    first_ping(world, eng, pip, fault)

    # Act 2 -- conflict: the fault has grown; the engineer names and explains it.
    morning_discovery(world, eng, pip, fault)
    naming_the_fault(world, eng, pip, fault)

    # Act 3 -- resolution: paste, bolt, calm ship, the recurring phrase returns.
    engineer_thinks(world, eng)
    the_fix(world, eng, pip, fault)
    the_jump(world, eng, pip)

    world.facts.update(eng=eng, pip=pip, ship=world.entities[setting.ship],
                       fault=fault, named=eng.memes["named"] >= THRESHOLD,
                       sealed=world.facts.get("fault", {}).get("sealed", False),
                       grown=world.facts.get("fault", {}).get("grown", False),
                       bolt_warm=world.facts.get("bolt_warm", False))
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "hopper": Setting(place="the engine room", ship="the Brave Hopper",
                      affordance="engine"),
    "wren":   Setting(place="the engine room", ship="the Little Wren",
                      affordance="engine"),
    "comet":  Setting(place="the engine room", ship="the Silver Comet",
                      affordance="engine"),
}

FAULTS = {
    "warm_line": Fault(
        verb_present="is metastasizing",
        verb_past="metastasized",
        sound="tiny pinging",
        surface="a thin dark line on the wall",
        warmth="warm and a little sticky",
        seed_symptom="a tiny pinging sound",
        grow_symptom=("a thin dark line on the wall, like a small crack that "
                      "had learned to walk"),
        fix_tool="a little silver tube",
        fix_tool_label="the little silver tube",
        fix_glow="softly blue",
    ),
    "cool_line": Fault(
        verb_present="is growing",
        verb_past="grew",
        sound="soft tapping",
        surface="a soft silver line on the panel",
        warmth="cool and a little tingly",
        seed_symptom="a soft tapping sound",
        grow_symptom=("a soft silver line on the panel, like a small wire that "
                      "had learned to stretch"),
        fix_tool="a small round cap",
        fix_tool_label="the small round cap",
        fix_glow="softly green",
    ),
    "warm_cracks": Fault(
        verb_present="is spreading",
        verb_past="spread",
        sound="tiny hissing",
        surface="a small warm crack on the floor",
        warmth="warm and a little rough",
        seed_symptom="a tiny hissing sound",
        grow_symptom=("a small warm crack on the floor, like a path a tiny "
                      "lizard had decided to walk"),
        fix_tool="a cool blue patch",
        fix_tool_label="the cool blue patch",
        fix_glow="softly blue",
    ),
}

# Engineers, with names that read well in dialogue.
@dataclass
class Engineer:
    name: str
    type: str
    gender: str
    pronouns: str                   # "he" | "she" | "they"
    trait: str
    bot_name: str

ENGINEERS = [
    Engineer(name="Rex", type="engineer", gender="boy",  pronouns="he",  trait="careful",  bot_name="Pip"),
    Engineer(name="Mae", type="engineer_female", gender="girl", pronouns="she", trait="gentle", bot_name="Bop"),
    Engineer(name="Ari", type="engineer", gender="boy",  pronouns="they", trait="quiet",  bot_name="Tic"),
]

GIRL_NAMES = ["Mae", "Lia", "Noa", "Ivy", "June"]
BOY_NAMES = ["Rex", "Theo", "Kit", "Ari", "Jules"]
NEUTRAL_NAMES = ["Ari", "Kit", "Sage", "Quinn", "Rowan"]
BOT_NAMES = ["Pip", "Bop", "Tic", "Bee", "Dot"]


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live
# in storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    setting: str
    fault: str
    engineer: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    eng, pip, ship, fault = f["eng"], f["pip"], f["ship"], f["fault_obj"]
    return [
        f'Write a short bedtime story for a 3-to-5-year-old on the theme '
        f'"a quiet ship, a careful engineer, a small spreading problem" that '
        f'includes the word "metastasize."',
        f'Tell a gentle space-adventure story where {eng.id}, a young engineer, '
        f'and {pip.id}, a small round helper-bot, listen to a tiny sound in '
        f'{ship.label}\'s engine room and have to find and fix the problem before '
        f'the morning jump.',
        f'Write a simple story in dialogue that uses the phrase "check, check, fix" '
        f'at the beginning and the end, and explains the long word "metastasize" '
        f'in a child\'s words.',
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    eng, pip, ship, fault = f["eng"], f["pip"], f["ship"], f["fault_obj"]
    sub, obj, pos = (eng.pronoun("subject"), eng.pronoun("object"),
                     eng.pronoun("possessive"))
    place = world.setting.place
    ship_name = world.setting.ship
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who lives and works on {ship_name}, where the morning jump "
                f"happens in a soft, purple sky?"
            ),
            answer=(
                f"A young {eng.traits[0] if eng.traits else 'careful'} engineer "
                f"named {eng.id} lives and works on {ship_name}, a small steel "
                f"ship. {sub.capitalize()} is helped by a small round helper-bot "
                f"named {pip.id}, who is brave but a little sleepy."
            ),
        ),
        QAItem(
            question=(
                f"What three words do {eng.id} and {pip.id} say out loud every "
                f"morning before the jump, in {place}?"
            ),
            answer=(
                f'Every morning they say the same three words out loud: "check, '
                f'check, fix." It is a small habit, like a song, that reminds '
                f"them to be careful and look at the ship before the day begins."
            ),
        ),
        QAItem(
            question=(
                f"What is the first, smallest sign that something is wrong on "
                f"{ship_name}, the night before the engineer finds the line?"
            ),
            answer=(
                f"The first sign is {fault.seed_symptom} from the back of "
                f"{place}. It is the kind of sound a small metals crew member's "
                f"mug makes on a metal table. When {eng.id} walks over, the "
                f"sound is gone, so {sub} says, 'We will come back to that.'"
            ),
        ),
    ]
    if f.get("grown"):
        qa.append(QAItem(
            question=(
                f"What does {eng.id} find on the wall of {place} the next morning, "
                f"and why is it a worry?"
            ),
            answer=(
                f"{sub.capitalize()} finds {fault.grow_symptom}. It feels "
                f"{fault.warmth}. The line had been growing all night, and it "
                f"is a worry because the ship is meant to jump in the morning, "
                f"and a spreading line in the wall could make the jump unsafe."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How does {eng.id} explain the long word that describes the "
                f"spreading line to {pip.id} in a child's words?"
            ),
            answer=(
                f'{eng.id} says, "It {fault.verb_present}." Then, because '
                f"{pip.id} tilts {pip.pronoun('possessive')} head, {eng.id} "
                f'laughs and says, "It means it is growing, and growing, and '
                f'growing. Like a weed, but inside a wall."'
            ),
        ))
    if f.get("sealed"):
        qa.append(QAItem(
            question=(
                f"How does {eng.id} finally calm the spreading line in the wall "
                f"of {ship_name} before the morning jump?"
            ),
            answer=(
                f"{sub.capitalize()} opens {pos} toolkit, takes out "
                f"{fault.fix_tool_label}, and squeezes a thin, slow, cool paste "
                f"along the dark line. The paste glows {fault.fix_glow}. Then "
                f"{sub} picks up the warm bolt from the floor and sets it gently "
                f"back where it belongs. The line stops walking, and the tiny "
                f"pinging sound comes back friendly, like a small heart going "
                f"tick-tick-tick."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What do {eng.id} and {pip.id} say at the very end of the "
                f"story, as the last starlight winks?"
            ),
            answer=(
                f'"{RECURRING_PHRASE}," says {eng.id}, the same three words from '
                f'the morning. "Beep, fix," says {pip.id}, a happy little echo.'
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    eng, pip, fault = f["eng"], f["pip"], f["fault_obj"]
    out: list[QAItem] = [
        QAItem(
            question="What is a spaceship's engine room?",
            answer=(
                "An engine room is the part of a spaceship where the engine "
                "lives, the way a kitchen is the part of a house where the "
                "stove lives. It is where the engineer checks the ship before "
                "a big journey."
            ),
        ),
        QAItem(
            question="What does it mean to metastasize, in a child's words?",
            answer=(
                "To metastasize means to grow, and grow, and grow, like a weed "
                "but inside a wall. A small crack can metastasize if nobody "
                "fixes it, and it can spread across the whole wall."
            ),
        ),
        QAItem(
            question="What is a helper-bot?",
            answer=(
                "A helper-bot is a small, round robot that helps a person do "
                "their job. Some helper-bots are brave but a little sleepy, and "
                "they like to beep softly when they are happy."
            ),
        ),
        QAItem(
            question="Why do engineers check their ship before a big trip?",
            answer=(
                "Engineers check their ship before a big trip so they can find "
                "small problems while they are still small. A tiny pinging "
                "sound is much easier to fix than a big spreading line."
            ),
        ),
        QAItem(
            question=(
                f"Why does {eng.id} keep a small bright flashlight on "
                f"{eng.pronoun('possessive')} shoulder?"
            ),
            answer=(
                f"{eng.id} keeps a small bright flashlight on {eng.pronoun('possessive')} "
                f"shoulder so {eng.pronoun('subject')} can see into dark corners of "
                f"the engine room. Dark corners are where small, quiet problems "
                f"like to hide."
            ),
        ),
    ]
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
        lines.append(f"  {e.id:14} ({e.type:9}) {' '.join(bits)}")
    f = world.facts.get("fault", {})
    lines.append(f"  fault noticed={f.get('noticed')} grown={f.get('grown')} "
                 f"paste_applied={f.get('paste_applied')} "
                 f"bolt_returned={f.get('bolt_returned')} "
                 f"sealed={f.get('sealed')}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(setting="hopper", fault="warm_line", engineer="Rex"),
    StoryParams(setting="wren",   fault="cool_line", engineer="Mae"),
    StoryParams(setting="comet",  fault="warm_cracks", engineer="Ari"),
]


def explain_rejection(engineer: Engineer, ship_id: str, fault_id: str) -> str:
    return ("(No story: every engineer / ship / fault combination in this world is "
            "a valid one, so an explicit combo shouldn't be rejected. The only "
            "real constraint is the long word 'metastasize,' and that lives in "
            "the fault registry.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of valid_combos().  Inline so
# the prose engine runs without clingo; loaded lazily for --asp / --verify.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the engineer, ship, and fault all exist together.
valid(E, S, F) :- engineer(E), ship(S), fault(F).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for eng in ENGINEERS:
        lines.append(asp.fact("engineer", eng.name))
        lines.append(asp.fact("pronoun", eng.name, eng.pronouns))
    for sid in SETTINGS:
        lines.append(asp.fact("ship", sid))
    for fid in FAULTS:
        lines.append(asp.fact("fault", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = {tuple(sorted(c)) for c in asp_valid_stories()}
    python_set = {tuple(sorted(c)) for c in valid_combos()}
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
        description="Story world sketch: a careful engineer, a sleepy helper-bot, "
                    "and a metastasizing fault in a small steel ship's engine room.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--fault", choices=FAULTS)
    ap.add_argument("--engineer", choices=[e.name for e in ENGINEERS])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="render the curated set")
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
    if args.setting and args.fault and args.engineer:
        if not any(c == (args.engineer, args.setting, args.fault) for c in valid_combos()):
            raise StoryError(explain_rejection(
                next(e for e in ENGINEERS if e.name == args.engineer),
                args.setting, args.fault))
    combos = [c for c in valid_combos()
              if (args.engineer is None or c[0] == args.engineer)
              and (args.setting is None or c[1] == args.setting)
              and (args.fault is None or c[2] == args.fault)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    engineer, setting, fault = rng.choice(sorted(combos))
    return StoryParams(setting=setting, fault=fault, engineer=engineer)


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    eng = next(e for e in ENGINEERS if e.name == params.engineer)
    world = tell(SETTINGS[params.setting], FAULTS[params.fault],
                 engineer_name=eng.name, engineer_type=eng.type,
                 engineer_traits=[eng.trait, "careful"], bot_name=eng.bot_name)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible (engineer, setting, fault) combos:\n")
        for eng, sid, fid in triples:
            print(f"  {eng:5} {sid:7} {fid}")
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
            header = f"### {p.engineer}: {p.fault} on {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
