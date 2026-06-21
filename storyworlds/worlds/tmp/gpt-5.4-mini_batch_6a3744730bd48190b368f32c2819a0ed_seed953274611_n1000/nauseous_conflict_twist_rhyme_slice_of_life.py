#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/nauseous_conflict_twist_rhyme_slice_of_life.py
===============================================================================

A small slice-of-life storyworld about a child who feels nauseous, has a gentle
conflict with a caregiver, and discovers a surprising twist: the problem is not
a big drama at all, but a simple need for rest, fresh air, and a little ginger
tea. The ending is light, concrete, and lightly rhymed.

The world supports:
- typed entities with physical meters and emotional memes
- a reasonableness gate
- inline ASP facts/rules twin
- prompts, story QA, and world-knowledge QA
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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

THRESHOLD = 1.0
SENSE_MIN = 2

KIND_HUMAN = {"girl", "boy", "mother", "father", "grandparent", "nurse"}
KIND_THING = {"cup", "tea", "blanket", "bench", "window", "bag", "snack", "note"}

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandparent", "nurse"}
        male = {"boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)

@dataclass
class StoryParams:
    child_name: str = "Mia"
    child_gender: str = "girl"
    caregiver_name: str = "Mom"
    caregiver_gender: str = "mother"
    place: str = "kitchen"
    conflict: str = "breakfast"
    twist: str = "ginger_tea"
    rhyme: str = "star"
    seed: Optional[int] = None

@dataclass
class Setting:
    id: str
    label: str
    detail: str
    cozy: bool = True

@dataclass
class ConflictBeat:
    id: str
    setup: str
    want: str
    warning: str
    risk: str
    tags: set[str] = field(default_factory=set)

@dataclass
class Twist:
    id: str
    reveal: str
    fix: str
    ending: str
    tags: set[str] = field(default_factory=set)

class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

def _r_nausea(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["nauseous"] < THRESHOLD:
            continue
        sig = ("nausea", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "child" in world.entities:
            world.get("child").memes["worry"] += 1
        if "caregiver" in world.entities:
            world.get("caregiver").memes["alert"] += 1
        out.append("")
    return out

def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["calm"] < THRESHOLD:
        return out
    sig = ("calm", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1)
    out.append("")
    return out

CAUSAL_RULES = [Rule("nausea", _r_nausea), Rule("calm", _r_calm)]

def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True

SETTINGS = {
    "kitchen": Setting(id="kitchen", label="the kitchen", detail="sunlight sat on the table by the window."),
    "porch": Setting(id="porch", label="the porch", detail="a breeze drifted through the screen door."),
    "bus_stop": Setting(id="bus_stop", label="the bus stop", detail="the morning waited quietly by the curb."),
}

CONFLICTS = {
    "breakfast": ConflictBeat(
        id="breakfast",
        setup="the bowl sat warm on the table",
        want="eat breakfast before going out",
        warning="the smell of the food turned the child's stomach",
        risk="the child might not be able to keep the food down",
        tags={"food", "morning", "nauseous"},
    ),
    "schoolbag": ConflictBeat(
        id="schoolbag",
        setup="the schoolbag was packed by the door",
        want="leave right away and not be late",
        warning="the child felt too dizzy to hurry",
        risk="the child might wobble and drop the bag",
        tags={"school", "rush", "nauseous"},
    ),
    "music": ConflictBeat(
        id="music",
        setup="a little speaker played a bouncy tune",
        want="keep dancing with the music",
        warning="the fast song made the room spin",
        risk="the child might need to sit down fast",
        tags={"music", "spin", "nauseous"},
    ),
}

TWISTS = {
    "ginger_tea": Twist(
        id="ginger_tea",
        reveal="the caregiver noticed the child had only a mild tummy ache, not a big sickness",
        fix="made ginger tea and opened the window for cool air",
        ending="soon the child could sip, sit, and breathe in a calmer beat",
        tags={"tea", "window", "rest"},
    ),
    "toast": Twist(
        id="toast",
        reveal="the caregiver remembered the child was hungry, not just sick",
        fix="buttered a piece of toast and cut it into tiny squares",
        ending="soon the child could nibble slowly and feel steadier",
        tags={"food", "rest"},
    ),
    "blanket": Twist(
        id="blanket",
        reveal="the caregiver saw the child was chilly and shaky from standing too long",
        fix="wrapped the child in a soft blanket and let them lie on the couch",
        ending="soon the child could rest until the room felt gentler",
        tags={"blanket", "rest"},
    ),
}

RHYMES = {
    "star": ("star", "spar", "glow"),
    "moon": ("moon", "spoon", "glow"),
    "sun": ("sun", "run", "glow"),
}

def reasonableness_ok(conflict: ConflictBeat, twist: Twist) -> bool:
    return "nauseous" in conflict.tags and "rest" in twist.tags

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CONFLICTS:
            for t in TWISTS:
                if reasonableness_ok(CONFLICTS[c], TWISTS[t]):
                    combos.append((s, c, t))
    return combos

def setting_line(setting: Setting, conflict: ConflictBeat) -> str:
    return f"{setting.detail} That was where {conflict.setup}."

def _slow_breath(world: World, child: Entity) -> None:
    child.memes["calm"] += 1
    child.meters["nauseous"] = max(0.0, child.meters["nauseous"] - 0.25)

def tell(setting: Setting, conflict: ConflictBeat, twist: Twist, rhyme_word: str,
         child_name: str, child_gender: str, caregiver_name: str, caregiver_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    caregiver = world.add(Entity(id=caregiver_name, kind="character", type=caregiver_gender, role="caregiver"))
    world.add(Entity(id="scene", type="thing", label=setting.label))
    child.meters["nauseous"] = 1.0
    child.memes["worry"] = 1.0
    world.say(f"At {setting.label}, {child.id} tried to start a normal little day, but {setting_line(setting, conflict).lower()}")
    world.say(f"{child.id} wanted to {conflict.want}, yet {caregiver.label_word} noticed {conflict.warning}.")
    world.para()
    child.memes["conflict"] += 1
    caregiver.memes["care"] += 1
    world.say(f'"I feel {rhyme_word}-nauseous," {child.id} mumbled, clutching {child.pronoun("possessive")} middle.')
    world.say(f"{caregiver.label_word.capitalize()} did not make a fuss. {caregiver.pronoun().capitalize()} paused, listened, and said they would slow the morning down.")
    world.para()
    _slow_breath(world, child)
    world.say(f"Then came the twist: {twist.reveal}. {caregiver.label_word.capitalize()} {twist.fix}.")
    world.say(f"{twist.ending.capitalize()}, and the little room felt soft again.")
    world.para()
    child.memes["conflict"] = 0.0
    child.memes["relief"] += 1
    caregiver.memes["relief"] += 1
    child.meters["nauseous"] = 0.0
    if setting.id == "kitchen":
        world.say(f"In the end, the child sat by the window, warm tea in hand, and the day went on at a gentle pace.")
    elif setting.id == "porch":
        world.say(f"In the end, the child sat on the porch step, watching leaves drift by, and the air helped the ache fade.")
    else:
        world.say(f"In the end, the child waited by the curb with steadier steps, and the morning did not feel so sharp anymore.")
    world.say(f"It was a quiet little fix, plain as can be: less rush, more hush, and a line that rhymed with {rhyme_word}.")
    world.facts.update(child=child, caregiver=caregiver, setting=setting, conflict=conflict, twist=twist, rhyme_word=rhyme_word)
    return world

PROMPTS = [
    "Write a slice-of-life story for a young child where someone feels nauseous, has a small conflict, and then gets a gentle surprise that helps.",
    "Tell a quiet everyday story that includes the word 'nauseous' and ends with a soft rhyming line.",
    "Write a simple morning story where a child feels nauseous, a caregiver notices, and the problem turns out to need a small twist rather than a big drama.",
]

def generation_prompts(world: World) -> list[str]:
    return PROMPTS

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, caregiver, conflict, twist = f["child"], f["caregiver"], f["conflict"], f["twist"]
    return [
        QAItem(
            question=f"What was wrong with {child.id} at the start?",
            answer=f"{child.id} felt nauseous and had trouble getting through the morning. The feeling made the little conflict feel bigger until the caregiver slowed everything down."
        ),
        QAItem(
            question=f"Why did {caregiver.id} step in?",
            answer=f"{caregiver.id} noticed the child was not ready to push through the morning as usual. That was why {caregiver.pronoun()} chose a calm answer instead of arguing."
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that the problem was not a big crisis at all. {twist.reveal}, so {twist.fix}."
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does nauseous mean?",
            answer="Nauseous means feeling like you might throw up or that your stomach feels upset. People often want to sit down, breathe slowly, and rest when they feel that way."
        ),
        QAItem(
            question="Why can fresh air help a queasy person?",
            answer="Fresh air can make a person feel less cramped and less overheated. That can help the stomach settle a little."
        ),
        QAItem(
            question="Why is ginger tea used in gentle home remedies?",
            answer="Many people think ginger can help calm an upset stomach. It is a simple warm drink that can feel comforting."
        ),
    ]

def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters: bits.append(f"meters={meters}")
        if memes: bits.append(f"memes={memes}")
        if e.role: bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)

CURATED = [
    StoryParams(child_name="Mia", child_gender="girl", caregiver_name="Mom", caregiver_gender="mother", place="kitchen", conflict="breakfast", twist="ginger_tea", rhyme="star"),
    StoryParams(child_name="Noah", child_gender="boy", caregiver_name="Dad", caregiver_gender="father", place="porch", conflict="music", twist="blanket", rhyme="moon"),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: nauseous conflict, twist, rhyme, slice of life.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.conflict is None or c[1] == args.conflict)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, conflict, twist = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    caregiver = args.caregiver or ("mother" if gender == "girl" else "father")
    name = args.name or rng.choice(["Mia", "Noah", "Ava", "Leo", "Luna", "Ben"])
    rhyme = rng.choice(list(RHYMES))
    return StoryParams(child_name=name, child_gender=gender, caregiver_name=("Mom" if caregiver == "mother" else "Dad"), caregiver_gender=caregiver, place=place, conflict=conflict, twist=twist, rhyme=rhyme)

def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.conflict not in CONFLICTS or params.twist not in TWISTS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.place], CONFLICTS[params.conflict], TWISTS[params.twist], params.rhyme, params.child_name, params.child_gender, params.caregiver_name, params.caregiver_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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

ASP_RULES = r"""
setting(kitchen).
setting(porch).
setting(bus_stop).

conflict(breakfast).
conflict(schoolbag).
conflict(music).

twist(ginger_tea).
twist(toast).
twist(blanket).

reasonably_valid(S, C, T) :- setting(S), conflict(C), twist(T), conflict_needs_rest(C), twist_is_rest(T).
conflict_needs_rest(breakfast).
conflict_needs_rest(schoolbag).
conflict_needs_rest(music).
twist_is_rest(ginger_tea).
twist_is_rest(toast).
twist_is_rest(blanket).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CONFLICTS:
        lines.append(asp.fact("conflict", c))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonably_valid/3."))
    return sorted(set(asp.atoms(model, "reasonably_valid")))

def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP gate differs from Python gate.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as ex:
        print(f"SMOKE TEST FAILED: {ex}")
        rc = 1
    return rc

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reasonably_valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
