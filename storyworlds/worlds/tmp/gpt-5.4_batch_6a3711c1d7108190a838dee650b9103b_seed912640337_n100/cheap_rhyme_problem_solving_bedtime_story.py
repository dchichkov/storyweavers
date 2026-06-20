#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cheap_rhyme_problem_solving_bedtime_story.py
=======================================================================

A standalone story world about a child, a bedtime problem, and a gentle
problem-solving fix. Each story keeps the mood close to a bedtime tale, uses a
small rhyming couplet as part of the soothing turn, and includes the word
"cheap" naturally in the world.

The world model is intentionally small and concrete:

- a child is trying to fall asleep
- one cheap bedroom object causes a specific bedtime trouble
  (noise, bright glints, or a chilly draft)
- a caring grown-up notices the real cause
- they choose a fix that actually matches that cause
- the room changes, the child calms down, and the ending image proves it

Like the other storyworlds, this script has:
- typed entities with physical meters and emotional memes
- a Python reasonableness gate
- an inline ASP twin
- three QA sets derived from world state
- CLI support for random runs, curated runs, JSON, trace, ASP, and verification
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
# from the repo root or from this nested world directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Story knobs
# ---------------------------------------------------------------------------
@dataclass
class Source:
    id: str
    issue: str              # noise | light | draft
    phrase: str             # "a cheap tin clock"
    label: str              # "clock"
    place: str              # where it is
    bother: str             # sentence body for the trouble
    clue: str               # what the parent notices while investigating
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    handles: set[str]       # source ids this fix truly addresses
    phrase: str             # "a folded scarf"
    action: str             # success narration body
    rhyme1: str             # first soothing line
    rhyme2: str             # second soothing line
    qa_text: str            # clean explanation for QA
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World container
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def child(self) -> Entity:
        return self.get("child")

    def parent(self) -> Entity:
        return self.get("parent")

    def source(self) -> Entity:
        return self.get("source")

    def room(self) -> Entity:
        return self.get("room")

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_source_disturbs(world: World) -> list[str]:
    out: list[str] = []
    src = world.source()
    child = world.child()
    room = world.room()
    if src.meters["active"] < THRESHOLD:
        return out
    issue = src.attrs.get("issue")
    sig = ("disturb", issue)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if issue == "noise":
        room.meters["noise"] += 1
        child.meters["wake"] += 1
        child.memes["worry"] += 1
        out.append("__trouble__")
    elif issue == "light":
        room.meters["brightness"] += 1
        child.meters["wake"] += 1
        child.memes["worry"] += 1
        out.append("__trouble__")
    elif issue == "draft":
        room.meters["cold"] += 1
        child.meters["wake"] += 1
        child.memes["worry"] += 1
        child.meters["chilly"] += 1
        out.append("__trouble__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    src = world.source()
    child = world.child()
    if src.meters["active"] >= THRESHOLD or child.memes["calm"] < THRESHOLD:
        return out
    sig = ("settle", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["sleepy"] += 1
    child.memes["safe"] += 1
    out.append("__settled__")
    return out


CAUSAL_RULES = [
    Rule("source_disturbs", "physical", _r_source_disturbs),
    Rule("settle", "emotional", _r_settle),
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
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def source_can_be_solved(source: Source, fix: Fix) -> bool:
    return fix.sense >= SENSE_MIN and source.id in fix.handles


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for sid, source in SOURCES.items():
        for fid, fix in FIXES.items():
            if source_can_be_solved(source, fix):
                combos.append((sid, fid))
    return combos


def explain_fix_rejection(source: Source, fix: Fix) -> str:
    if fix.sense < SENSE_MIN:
        better = ", ".join(sorted(f.id for f in sensible_fixes()))
        return (
            f"(Refusing fix '{fix.id}': it sounds too weak or fussy for bedtime "
            f"(sense={fix.sense} < {SENSE_MIN}). Try a calmer, more effective fix "
            f"such as {better}.)"
        )
    return (
        f"(No story: {fix.phrase} does not really solve the problem caused by "
        f"{source.phrase}. Pick a fix that matches the true cause.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_trouble(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    child = sim.child()
    room = sim.room()
    return {
        "wake": child.meters["wake"],
        "worry": child.memes["worry"],
        "noise": room.meters["noise"],
        "brightness": room.meters["brightness"],
        "cold": room.meters["cold"],
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def bedtime_setup(world: World, child: Entity, parent: Entity, comfort: str) -> None:
    world.say(
        f"It was bedtime, and {child.id}'s room felt small, warm, and nearly ready for sleep."
    )
    if comfort:
        world.say(
            f"{child.id} tucked {comfort} under one arm while {parent.label_word} smoothed the blanket."
        )
    else:
        world.say(
            f"{parent.label_word.capitalize()} smoothed the blanket and kissed the top of {child.pronoun('possessive')} head."
        )


def introduce_source(world: World, source: Source) -> None:
    world.say(
        f"But {source.place} there was {source.phrase}, and {source.bother}"
    )


def notice_trouble(world: World, child: Entity, source: Source) -> None:
    src = world.source()
    src.meters["active"] += 1
    src.attrs["issue"] = source.issue
    propagate(world, narrate=False)
    if source.issue == "noise":
        world.say(
            f'{child.id} listened, blinked at the ceiling, and whispered, "That little sound keeps peeping into my sleep."'
        )
    elif source.issue == "light":
        world.say(
            f'{child.id} watched the wall and whispered, "Those shiny wiggles keep leaping where my dreams should be."'
        )
    else:
        world.say(
            f'{child.id} pulled the blanket higher and whispered, "A tiny cold breeze keeps sneaking to my toes."'
        )


def ask_for_help(world: World, child: Entity, parent: Entity) -> None:
    child.memes["trust"] += 1
    world.say(
        f'"{parent.label_word.capitalize()}," {child.id} said softly, "something in my room is keeping me awake."'
    )


def investigate(world: World, child: Entity, parent: Entity, source: Source) -> None:
    pred = predict_trouble(world)
    world.facts["predicted"] = pred
    parent.memes["care"] += 1
    if source.issue == "noise":
        reason = "its ticking was poking at the quiet"
    elif source.issue == "light":
        reason = "its silver parts were catching the moon"
    else:
        reason = "a thin edge was letting chilly air inside"
    world.say(
        f"{parent.label_word.capitalize()} stayed calm, looked around, and soon noticed that {source.clue}. "
        f"That meant {reason}."
    )


def think_together(world: World, child: Entity, parent: Entity, source: Source, fix: Fix) -> None:
    child.memes["hope"] += 1
    world.say(
        f'"Let us solve the right problem," {parent.label_word} said. '
        f'"We do not need a big fuss. We just need the right small thing."'
    )
    if fix.id == "cheap_tape":
        world.say(
            f'{child.id} almost asked for some cheap tape, but {parent.label_word} shook {parent.pronoun("possessive")} head. '
            f'"Tape would not make this room rest."'
        )
    else:
        world.say(
            f"{child.id} watched closely, trying to see how the room might change."
        )


def apply_fix(world: World, child: Entity, parent: Entity, source: Source, fix: Fix) -> None:
    src = world.source()
    room = world.room()
    src.meters["active"] = 0.0
    room.meters["noise"] = 0.0
    room.meters["brightness"] = 0.0
    room.meters["cold"] = 0.0
    child.meters["wake"] = 0.0
    child.meters["chilly"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["calm"] += 1
    child.memes["love"] += 1
    parent.memes["love"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} used {fix.phrase} and {fix.action}."
    )


def soothing_rhyme(world: World, child: Entity, parent: Entity, fix: Fix) -> None:
    world.say(
        f'Then {parent.label_word} whispered a little rhyme: "{fix.rhyme1} {fix.rhyme2}"'
    )
    child.memes["joy"] += 1
    child.memes["safe"] += 1
    world.say(
        f"{child.id} said it back in a sleepier voice, and the words made the room feel gentler."
    )


def ending(world: World, child: Entity, comfort: str) -> None:
    if comfort:
        world.say(
            f"Soon {child.id} curled around {comfort}, and even the corners of the room seemed to yawn."
        )
    else:
        world.say(
            f"Soon {child.id} curled into the pillow, and even the corners of the room seemed to yawn."
        )
    world.say(
        f"At last {child.id}'s eyes closed, the blanket stayed still, and bedtime became deep, soft, and sweet."
    )


# ---------------------------------------------------------------------------
# Story screenplay
# ---------------------------------------------------------------------------
def tell(source: Source, fix: Fix, child_name: str = "Mina", child_type: str = "girl",
         parent_type: str = "mother", comfort: str = "a floppy bunny") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    room = world.add(Entity(id="room", type="room", label="bedroom"))
    src = world.add(Entity(id="source", type=source.id, label=source.label, phrase=source.phrase))
    child.attrs["name"] = child_name
    parent.attrs["name"] = parent.label_word
    src.attrs["issue"] = source.issue
    world.facts["child_name"] = child_name
    world.facts["comfort"] = comfort

    bedtime_setup(world, child, parent, comfort)
    introduce_source(world, source)

    world.para()
    notice_trouble(world, child, source)
    ask_for_help(world, child, parent)
    investigate(world, child, parent, source)

    world.para()
    think_together(world, child, parent, source, fix)
    apply_fix(world, child, parent, source, fix)
    soothing_rhyme(world, child, parent, fix)

    world.para()
    ending(world, child, comfort)

    world.facts.update(
        source_cfg=source,
        fix_cfg=fix,
        child=child,
        parent=parent,
        room=room,
        source_ent=src,
        solved=src.meters["active"] < THRESHOLD and child.meters["sleepy"] >= THRESHOLD,
        issue=source.issue,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SOURCES = {
    "clock": Source(
        "clock",
        "noise",
        "a cheap tin clock",
        "clock",
        "on the high shelf",
        "it kept saying tick-tick in the dark, too brisk and bright for a sleepy room",
        "the cheap tin clock on the shelf was clicking much louder than it looked",
        tags={"clock", "noise", "cheap"},
    ),
    "mobile": Source(
        "mobile",
        "light",
        "a cheap silver mobile",
        "mobile",
        "above the bed",
        "it tossed moon-splashes over the wall whenever the night air stirred",
        "the cheap silver mobile above the bed flashed whenever moonlight touched it",
        tags={"mobile", "light", "cheap"},
    ),
    "shade": Source(
        "shade",
        "draft",
        "a cheap paper shade",
        "shade",
        "by the window",
        "it trembled in the frame and let a tiny cold whisper slip into the room",
        "the cheap paper shade by the window did not sit flat against the glass",
        tags={"window", "draft", "cheap"},
    ),
}

FIXES = {
    "scarf_wrap": Fix(
        "scarf_wrap",
        3,
        {"clock"},
        "a folded scarf",
        "wrapped the clock gently so the hard little ticks turned soft and small",
        "Tick-tock, hush the clock.",
        "Night can float on quiet sock.",
        "wrapped the clock in a scarf so its ticking turned soft",
        tags={"clock", "quiet"},
    ),
    "hall_shelf": Fix(
        "hall_shelf",
        3,
        {"clock"},
        "two careful hands",
        "moved the clock out to the hall where its ticking could not peep into bed",
        "Tick away, far from the bed.",
        "Dreams belong inside your head.",
        "moved the clock to the hall so the room could be quiet",
        tags={"clock", "quiet"},
    ),
    "curtain_close": Fix(
        "curtain_close",
        3,
        {"mobile"},
        "the curtains",
        "drew the curtains until the moon could no longer sparkle on the mobile",
        "Silver gleam, softer now.",
        "Moon be kind and make no show.",
        "closed the curtains so moonlight stopped flashing on the mobile",
        tags={"curtain", "moon"},
    ),
    "ribbon_tie": Fix(
        "ribbon_tie",
        2,
        {"mobile"},
        "a blue ribbon",
        "tied the mobile still so it stopped tossing light around the wall",
        "Little swing, rest your ring.",
        "Still things let the dreambirds sing.",
        "tied the mobile still with a ribbon so it stopped flashing and swaying",
        tags={"mobile", "moon"},
    ),
    "draft_snake": Fix(
        "draft_snake",
        3,
        {"shade"},
        "a long cloth draft snake",
        "set it along the window ledge so the chilly thread of air could not creep in",
        "Breeze be slow, do not roam.",
        "Blankets make a warmer home.",
        "placed a cloth draft snake by the window so the cold air stayed out",
        tags={"window", "warm"},
    ),
    "extra_quilt": Fix(
        "extra_quilt",
        2,
        {"shade"},
        "an extra quilt",
        "tucked it around the bed and then pressed the loose shade snug against the frame",
        "Quilt so deep, bundle sleep.",
        "Warm toes keep the night in peace.",
        "added an extra quilt and snugged the loose shade so the draft stopped reaching the bed",
        tags={"window", "warm"},
    ),
    # Known but rejected: the script knows about this weak shortcut and refuses it.
    "cheap_tape": Fix(
        "cheap_tape",
        1,
        set(),
        "some cheap tape",
        "stuck little strips here and there",
        "Tape can flap and tape can peel.",
        "Rest needs a truer, calmer seal.",
        "tried cheap tape",
        tags={"cheap"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Ivy", "Ava", "Ella", "Maya"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Milo", "Ben", "Noah", "Eli", "Sam"]
COMFORTS = ["a floppy bunny", "a small bear", "a soft fox", "a quilted duck", "a sleepy lamb", ""]
TRAITS = ["sleepy", "gentle", "thoughtful", "quiet", "curious"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    source: str
    fix: str
    child_name: str
    child_type: str
    parent_type: str
    comfort: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "cheap": [(
        "What does cheap mean?",
        "Cheap means something costs only a little money. Sometimes cheap things are fine, but sometimes they are flimsy or do not work very well."
    )],
    "clock": [(
        "Why can a ticking clock make bedtime harder?",
        "A steady ticking sound can keep catching your attention when everything else is quiet. That can make it harder for your brain to settle down for sleep."
    )],
    "mobile": [(
        "What is a mobile above a bed?",
        "A mobile is a hanging decoration that can sway gently in the air. If it catches light, it can make moving shapes on the wall."
    )],
    "window": [(
        "What is a draft?",
        "A draft is a little stream of air that slips in through a gap. At night it can make a room feel chilly."
    )],
    "quiet": [(
        "Why does a quiet room help with sleep?",
        "A quiet room gives your ears and brain less to keep noticing. That makes it easier to relax and drift off."
    )],
    "moon": [(
        "Why can moving light on the wall feel distracting at bedtime?",
        "Moving light keeps changing, so your eyes want to follow it. When things stay still and dim, bedtime feels calmer."
    )],
    "warm": [(
        "Why do warm blankets help at bedtime?",
        "Warm blankets help your body feel safe and cozy. When your body is comfortable, it is easier to rest."
    )],
}
KNOWLEDGE_ORDER = ["cheap", "clock", "mobile", "window", "quiet", "moon", "warm"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    source = f["source_cfg"]
    fix = f["fix_cfg"]
    name = f["child_name"]
    return [
        f'Write a short bedtime story for a 3-to-5-year-old that includes the word "cheap", a small rhyme, and a gentle problem-solving fix.',
        f"Tell a cozy bedtime story about a {child.type} named {name} who cannot sleep because of {source.phrase}, and a calm grown-up solves the real problem.",
        f"Write a soothing story where {name} and a parent use {fix.phrase} to make the room restful again, ending with a sleepy image."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    source = f["source_cfg"]
    fix = f["fix_cfg"]
    comfort = f.get("comfort", "")
    parent_word = parent.label_word
    name = f["child_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a child trying to go to sleep, and {name}'s {parent_word} who helps. The story happens in a bedroom at bedtime."
        ),
        (
            "What was the bedtime problem?",
            f"The problem was {source.phrase} {source.place}, because {source.bother}. That kept the room from feeling quiet and sleepy."
        ),
        (
            f"How did {name}'s {parent_word} figure out what was wrong?",
            f"{parent_word.capitalize()} stayed calm and looked for the real cause instead of guessing. Then {parent.pronoun()} noticed that {source.clue}, which showed what was truly disturbing the room."
        ),
        (
            "How did they solve the problem?",
            f"They solved it by using {fix.phrase} and {fix.qa_text}. That changed the room itself, so the trouble stopped instead of only being covered up."
        ),
        (
            "Why did the rhyme help at the end?",
            f"The rhyme helped because it made the fix feel soft and easy to remember. After the room had changed, the gentle words helped {name} feel calm enough to drift toward sleep."
        ),
    ]
    if comfort:
        qa.append((
            f"What was {name} holding at bedtime?",
            f"{name} was holding {comfort}. That made the ending feel even cozier once the room was calm again."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with the room quiet and gentle, and with {name}'s eyes closing under the blanket. The ending image proves that the problem was really solved."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["source_cfg"].tags) | set(world.facts["fix_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("clock", "hall_shelf", "Mina", "girl", "mother", "a floppy bunny", "quiet"),
    StoryParams("mobile", "curtain_close", "Theo", "boy", "father", "a small bear", "thoughtful"),
    StoryParams("shade", "draft_snake", "Lila", "girl", "mother", "a sleepy lamb", "gentle"),
    StoryParams("clock", "scarf_wrap", "Owen", "boy", "father", "a soft fox", "curious"),
    StoryParams("mobile", "ribbon_tie", "Ava", "girl", "mother", "", "sleepy"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(Src, F) :- source(Src), fix(F), sensible(F), handles(F, Src).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SOURCES:
        lines.append(asp.fact("source", sid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        for sid in sorted(fix.handles):
            lines.append(asp.fact("handles", fid, sid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combos match ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sens = {f.id for f in sensible_fixes()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible fixes match ({sorted(py_sens)}).")
    else:
        rc = 1
        print("MISMATCH in sensible fixes:")
        print("  python:", sorted(py_sens))
        print("  clingo:", sorted(asp_sens))

    # Smoke test: ordinary generation must not crash.
    smoke_cases = list(CURATED[:2])
    try:
        for params in smoke_cases:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated empty story during smoke test.")
            if sample.world is None:
                raise StoryError("Missing world object during smoke test.")
        print(f"OK: smoke-generated {len(smoke_cases)} normal stories.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime story world with a small rhyme and a real problem-solving fix."
    )
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible source/fix set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.fix:
        src = SOURCES[args.source]
        fix = FIXES[args.fix]
        if not source_can_be_solved(src, fix):
            raise StoryError(explain_fix_rejection(src, fix))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        src = SOURCES[args.source] if args.source else next(iter(SOURCES.values()))
        raise StoryError(explain_fix_rejection(src, FIXES[args.fix]))

    combos = [
        c for c in valid_combos()
        if (args.source is None or c[0] == args.source)
        and (args.fix is None or c[1] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid source/fix combination matches the given options.)")

    source_id, fix_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    if child_type == "girl":
        name = args.child_name or rng.choice(GIRL_NAMES)
    else:
        name = args.child_name or rng.choice(BOY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    comfort = rng.choice(COMFORTS)
    trait = rng.choice(TRAITS)
    return StoryParams(source_id, fix_id, name, child_type, parent_type, comfort, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SOURCES[params.source],
        FIXES[params.fix],
        params.child_name,
        params.child_type,
        params.parent_type,
        params.comfort,
    )
    world.child().traits.append(params.trait)
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
        print(asp_program("#show sensible/1.\n#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (source, fix) combos:\n")
        for source_id, fix_id in combos:
            print(f"  {source_id:8} {fix_id}")
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
            header = f"### {p.child_name}: {p.source} -> {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
