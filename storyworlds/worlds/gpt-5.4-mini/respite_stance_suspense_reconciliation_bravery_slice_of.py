#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/respite_stance_suspense_reconciliation_bravery_slice_of.py
==========================================================================================

A small slice-of-life storyworld about a child, a tense moment, a brave pause,
and a gentle reconciliation.

Seed words:
- respite
- stance

Features:
- Suspense
- Reconciliation
- Bravery

Style:
- Slice of Life

The world simulates a simple everyday scene: two children have a quiet disagreement
during a small performance practice, one child worries about speaking up, and a
kind pause creates enough respite for everyone to settle into a better stance.
The story can end in a calm apology, a shared plan, and a visible change in the
children's moods and behavior.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/respite_stance_suspense_reconciliation_bravery_slice_of.py
    python storyworlds/worlds/gpt-5.4-mini/respite_stance_suspense_reconciliation_bravery_slice_of.py --qa
    python storyworlds/worlds/gpt-5.4-mini/respite_stance_suspense_reconciliation_bravery_slice_of.py --all
    python storyworlds/worlds/gpt-5.4-mini/respite_stance_suspense_reconciliation_bravery_slice_of.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Scene:
    id: str
    place: str
    activity: str
    tension_spike: str
    calm_spot: str
    respite_image: str
    stance_image: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Conflict:
    id: str
    trigger: str
    mistake: str
    apology: str
    repair: str
    suspense: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Resolution:
    id: str
    pause: str
    brave_move: str
    reconciliation: str
    ending: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["tension"] < THRESHOLD:
            continue
        sig = ("fear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in list(world.entities.values()):
            if kid.role in {"lead", "friend"}:
                kid.memes["worry"] += 1
        out.append("__suspense__")
    return out


def _r_respite(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["pause"] < THRESHOLD:
            continue
        sig = ("respite", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in list(world.entities.values()):
            if kid.role in {"lead", "friend"}:
                kid.memes["calm"] += 1
                kid.memes["bravery"] += 1
        out.append("__respite__")
    return out


def _r_reconcile(world: World) -> list[str]:
    for e in list(world.entities.values()):
        if e.meters["repair"] < THRESHOLD:
            continue
        sig = ("reconcile", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["warmth"] += 1
        e.memes["pride"] += 1
        return ["__reconcile__"]
    return []


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("respite", _r_respite), Rule("reconcile", _r_reconcile)]


def choose_scene(rng: random.Random) -> Scene:
    return rng.choice(list(SCENES.values()))


def choose_conflict(rng: random.Random) -> Conflict:
    return rng.choice(list(CONFLICTS.values()))


def choose_resolution(rng: random.Random) -> Resolution:
    return rng.choice(list(RESOLUTIONS.values()))


def tell(scene: Scene, conflict: Conflict, resolution: Resolution,
         lead_name: str, lead_gender: str, friend_name: str, friend_gender: str,
         adult_name: str, adult_gender: str) -> World:
    w = World()
    lead = w.add(Entity(lead_name, kind="character", type=lead_gender, role="lead"))
    friend = w.add(Entity(friend_name, kind="character", type=friend_gender, role="friend"))
    adult = w.add(Entity(adult_name, kind="character", type=adult_gender, role="adult"))
    bench = w.add(Entity("bench", label="the bench"))
    stage = w.add(Entity("stage", label="the little stage"))
    lead.memes["bravery"] = 1.0
    friend.memes["worry"] = 0.0

    w.say(f"On a quiet afternoon, {lead.id} and {friend.id} met at {scene.place}.")
    w.say(f"They were getting ready for {scene.activity}, and {scene.stance_image}")
    w.say(f"{lead.id} liked the calm of the room, but {friend.id} kept looking toward {scene.tension_spike}.")

    w.para()
    lead.meters["tension"] += 1
    friend.memes["worry"] += 1
    w.say(f"Then came a small snag: {conflict.trigger}. {conflict.suspense}")
    w.say(f"{lead.id} made a {scene.id} {conflict.mistake}.")
    propagate(w, narrate=False)
    w.say(f"{friend.id} went quiet, and the room felt smaller for a moment.")

    w.para()
    w.say(f"At last, {resolution.pause}. {resolution.pause.capitalize()} gave everyone a little respite.")
    w.get("bench").meters["pause"] += 1
    propagate(w, narrate=False)
    w.say(f"{resolution.brave_move}")
    w.say(f"{adult.id} noticed the change, smiled, and helped without making a big fuss.")

    w.para()
    w.get("stage").meters["repair"] += 1
    propagate(w, narrate=False)
    w.say(f"{resolution.reconciliation}")
    w.say(f"{resolution.ending}")

    w.facts.update(
        lead=lead, friend=friend, adult=adult, scene=scene, conflict=conflict,
        resolution=resolution, tense=True, repaired=True,
        brave=lead.memes["bravery"] >= THRESHOLD, calm=friend.memes["calm"] >= THRESHOLD,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene, conflict, resolution = f["scene"], f["conflict"], f["resolution"]
    return [
        f'Write a slice-of-life story that includes the words "respite" and "stance" and has a quiet suspenseful moment before a friendly reconciliation.',
        f"Tell a small everyday story at {scene.place} where a child has to rethink {conflict.mistake} and find a braver stance.",
        f"Write a gentle story with suspense, bravery, and reconciliation that ends with a calm shared moment and the word respite.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    lead, friend, adult = f["lead"], f["friend"], f["adult"]
    scene, conflict, resolution = f["scene"], f["conflict"], f["resolution"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer=f"It is a quiet slice-of-life story about {lead.id}, {friend.id}, and a small problem at {scene.place}. The trouble never becomes huge; it settles through patience, bravery, and kindness."
        ),
        QAItem(
            question=f"Why did the room feel tense?",
            answer=f"The room felt tense because {conflict.trigger} made {lead.id} choose {conflict.mistake}, and {friend.id} worried something might go wrong. That worry added suspense until everyone had a chance to pause."
        ),
        QAItem(
            question=f"What helped the children find respite?",
            answer=f"{resolution.pause} helped them stop and breathe, which gave everyone respite. That quiet pause made it easier for {lead.id} to be brave and for {friend.id} to soften."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with reconciliation: {resolution.reconciliation} {resolution.ending} The ending shows that the children were calmer and closer than before."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does respite mean?", "Respite means a short rest or break from worry, noise, or hard work."),
        QAItem("What does stance mean?", "A stance is the way someone stands or the position they choose to take, with their body or in a situation."),
        QAItem("What is bravery?", "Bravery means doing the right thing even when you feel nervous or unsure."),
        QAItem("What is reconciliation?", "Reconciliation is when people make up after a disagreement and become friendly again."),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


SCENES = {
    "rehearsal": Scene(
        "rehearsal", "the community room", "a little reading rehearsal",
        "the doorway", "the folding chairs", "The chairs made a neat row, and the stage light was still off.",
        "They stood with careful shoulders, as if waiting for a cue.",
        tags={"respite", "stance", "slice", "bravery"},
    ),
    "kitchen": Scene(
        "kitchen", "the kitchen", "a song practice before dinner",
        "the window", "the table", "The table made a cozy corner, and their cups waited nearby.",
        "They held a steady stance beside the table, trying to stay calm.",
        tags={"respite", "stance", "slice", "bravery"},
    ),
    "porch": Scene(
        "porch", "the porch", "a short puppet show",
        "the steps", "the little stool", "The stool sat in the sunlight, and the porch boards were warm.",
        "They took a brave stance by the railing, ready to begin.",
        tags={"respite", "stance", "slice", "bravery"},
    ),
}

CONFLICTS = {
    "missed_line": Conflict(
        "missed_line", "the next line got forgotten", "an unsure pause", "a soft apology", "a quick fix to the page",
        "For a second, nobody knew what would happen next.", tags={"suspense", "reconciliation"},
    ),
    "mixed_up_cue": Conflict(
        "mixed_up_cue", "the cue came too early", "a wrong step", "a careful apology", "a slow breath and a new start",
        "The silence stretched just long enough to feel suspenseful.", tags={"suspense", "reconciliation"},
    ),
    "snapped_tone": Conflict(
        "snapped_tone", "a sharp comment slipped out", "a hurtful tone", "a sorry whisper", "a gentler way to say it",
        "The words hung in the air, and both children went still.", tags={"suspense", "reconciliation"},
    ),
}

RESOLUTIONS = {
    "pause_breathe": Resolution(
        "pause_breathe", "they all took a small pause",
        "Bravely, {lead} stepped back, looked at {friend}, and spoke more softly.",
        "Then {lead} and {friend} traded a shy apology and a nod.",
        "Soon the little practice felt friendly again, and the scene could go on.",
        tags={"respite", "stance", "bravery", "reconciliation"},
    ),
    "restage": Resolution(
        "restage", "the adults asked for one more minute",
        "With a brave stance, {lead} moved closer and tried again the right way.",
        "After that, {lead} said sorry, and {friend} answered with a small smile.",
        "By the end, the group had a better rhythm and an easier mood.",
        tags={"respite", "stance", "bravery", "reconciliation"},
    ),
    "gentle_reset": Resolution(
        "gentle_reset", "they took a quiet breath together",
        "This time, {lead} held a steadier stance and waited for {friend}.",
        "That gave room for a real apology and a warm yes in return.",
        "The practice ended with a soft laugh and a peaceful room.",
        tags={"respite", "stance", "bravery", "reconciliation"},
    ),
}

GIRL_NAMES = ["Maya", "Lila", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Finn", "Max"]
ADULT_NAMES = ["Mom", "Dad", "Aunt Kim", "Uncle Ben"]


@dataclass
@dataclass
class StoryParams:
    scene: str
    conflict: str
    resolution: str
    lead_name: str
    lead_gender: str
    friend_name: str
    friend_gender: str
    adult_name: str
    adult_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, r) for s in SCENES for c in CONFLICTS for r in RESOLUTIONS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life storyworld about respite, stance, suspense, reconciliation, and bravery.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--lead")
    ap.add_argument("--lead-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["mother", "father"])
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
    scene = args.scene or rng.choice(sorted(SCENES))
    conflict = args.conflict or rng.choice(sorted(CONFLICTS))
    resolution = args.resolution or rng.choice(sorted(RESOLUTIONS))
    lead_gender = args.lead_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if lead_gender == "girl" else "girl")
    lead = args.lead or rng.choice(GIRL_NAMES if lead_gender == "girl" else BOY_NAMES)
    friend_pool = [n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != lead]
    friend = args.friend or rng.choice(friend_pool)
    adult_gender = args.adult_gender or rng.choice(["mother", "father"])
    adult = args.adult or rng.choice(ADULT_NAMES)
    if friend == lead:
        raise StoryError("lead and friend must be different children.")
    return StoryParams(scene, conflict, resolution, lead, lead_gender, friend, friend_gender, adult, adult_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SCENES[params.scene], CONFLICTS[params.conflict], RESOLUTIONS[params.resolution],
        params.lead_name, params.lead_gender, params.friend_name, params.friend_gender,
        params.adult_name, params.adult_gender,
    )
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
scene(scene).
conflict(conflict).
resolution(resolution).

suspense(X) :- conflict(X).
brave(X) :- resolution(X).
reconcile(X) :- resolution(X).
valid(S, C, R) :- scene(S), conflict(C), resolution(R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for cid in CONFLICTS:
        lines.append(asp.fact("conflict", cid))
    for rid in RESOLUTIONS:
        lines.append(asp.fact("resolution", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP valid combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story.strip()
        print("OK: default generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


CURATED = [
    StoryParams("rehearsal", "missed_line", "pause_breathe", "Maya", "girl", "Eli", "boy", "Mom", "mother"),
    StoryParams("kitchen", "mixed_up_cue", "restage", "Theo", "boy", "Ava", "girl", "Dad", "father"),
    StoryParams("porch", "snapped_tone", "gentle_reset", "Nora", "girl", "Max", "boy", "Aunt Kim", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return
    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            p = resolve_params(args, random.Random(rng_base + i))
            p.seed = rng_base + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
