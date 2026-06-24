#!/usr/bin/env python3
"""
storyworlds/worlds/ripple_corduroy_drift_curiosity_mystery_to_solve.py
======================================================================

A small mystery storyworld built from the seed words:
ripple, corduroy, drift

Core premise:
A curious child notices a tiny mystery in a quiet place, follows clues, and
finds a surprising answer. The world model tracks what is seen, what drifts,
what is hidden, and what changes when the mystery is solved.

The style aims for a child-friendly mystery tone: careful noticing, small clues,
a sensible turn, and a surprise that feels earned.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    hidden: bool = False
    revealed: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "drift": 0.0, "noticed": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "surprise": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    has_ripple: bool = False
    has_drift: bool = False


@dataclass
class Clue:
    id: str
    label: str
    clue_kind: str
    reveals: str
    drift_ok: bool = False


@dataclass
class StoryParams:
    setting: str
    clue: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_ripple_notice(world: World) -> list[str]:
    out: list[str] = []
    if not world.setting.has_ripple:
        return out
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("notice", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["noticed"] += 1
        out.append(f"{ent.pronoun().capitalize()} noticed a tiny ripple where the water should have been still.")
    return out


def _r_drift_advance(world: World) -> list[str]:
    out: list[str] = []
    if not world.setting.has_drift:
        return out
    for ent in world.entities.values():
        if ent.kind != "thing":
            continue
        if ent.hidden:
            ent.meters["drift"] += 1
            sig = ("drift", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"The little clue drifted farther along, just enough to make the mystery harder.")
    return out


def _r_surprise_reveal(world: World) -> list[str]:
    out: list[str] = []
    clue = next((e for e in world.entities.values() if e.kind == "thing" and e.hidden), None)
    child = next((e for e in world.entities.values() if e.kind == "character"), None)
    if not clue or not child:
        return out
    if clue.meters["noticed"] < THRESHOLD:
        return out
    if child.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("reveal", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.hidden = False
    clue.revealed = True
    child.memes["surprise"] += 1
    child.memes["relief"] += 1
    out.append("__reveal__")
    return out


CAUSAL_RULES = [
    Rule("ripple_notice", _r_ripple_notice),
    Rule("drift_advance", _r_drift_advance),
    Rule("surprise_reveal", _r_surprise_reveal),
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
                produced.extend(s for s in sents if s != "__reveal__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "pond": Setting(place="the pond", indoors=False, has_ripple=True, has_drift=True),
    "library": Setting(place="the library", indoors=True, has_ripple=False, has_drift=False),
    "attic": Setting(place="the attic", indoors=True, has_ripple=False, has_drift=True),
    "garden": Setting(place="the garden", indoors=False, has_ripple=True, has_drift=False),
}

CLUES = {
    "button": Clue(
        id="button",
        label="a tiny corduroy button",
        clue_kind="button",
        reveals="the missing pocket was on the corduroy coat",
    ),
    "boat": Clue(
        id="boat",
        label="a little paper boat",
        clue_kind="boat",
        reveals="the drift had carried the boat under the bench",
        drift_ok=True,
    ),
    "note": Clue(
        id="note",
        label="a folded note",
        clue_kind="note",
        reveals="the note was hidden inside the corduroy book cover",
    ),
    "shell": Clue(
        id="shell",
        label="a bright shell",
        clue_kind="shell",
        reveals="the shell had fallen from a jar and made the ripple",
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lina", "Ruby", "Ada", "Maya", "Ivy", "Zoe"]
BOY_NAMES = ["Finn", "Theo", "Ben", "Noah", "Leo", "Max", "Owen", "Eli"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, clue in CLUES.items():
            if setting.has_ripple or clue.drift_ok or not setting.indoors:
                combos.append((sid, cid))
    return combos


@dataclass
class StoryParams:
    setting: str
    clue: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly mystery about ripple, corduroy, and drift.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent-gender", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--parent-name")
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
    combos = valid_combos()
    if args.setting and args.clue:
        if (args.setting, args.clue) not in combos:
            raise StoryError("That setting and clue do not make a reasonable mystery together.")
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting) and (args.clue is None or c[1] == args.clue)]
    if not combos:
        raise StoryError("No valid mystery matches the given options.")
    setting, clue = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    parent_name = args.parent_name or (rng.choice(["Mom", "Mum", "Mama"]) if parent_gender == "mother" else rng.choice(["Dad", "Papa", "Dad"]))
    return StoryParams(setting=setting, clue=clue, child_name=child_name, child_gender=gender, parent_name=parent_name, parent_gender=parent_gender)


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_gender, label=params.parent_name))
    clue = world.add(Entity(id="clue", kind="thing", type=CLUES[params.clue].clue_kind, label=CLUES[params.clue].label, hidden=True))
    child.memes["curiosity"] += 1
    child.meters["noticed"] += 0.0

    world.say(f"{child.label} was a curious {params.child_gender} who liked quiet questions.")
    world.say(f"One day, {child.label} and {parent.label} went to {setting.place}, where a small mystery waited.")
    world.para()
    if setting.has_ripple:
        world.say(f"There was a ripple where there should have been still water.")
    else:
        world.say(f"There was a hush in the room, but one little clue felt out of place.")
    world.say(f"{child.label} spotted {clue.label} and wanted to know what it meant.")
    child.memes["curiosity"] += 1
    propagate(world, narrate=True)

    world.para()
    if clue.id == "button":
        world.say(f"{child.label} followed the clue and found the answer hiding in the corduroy coat.")
    elif clue.id == "boat":
        world.say(f"{child.label} watched the little boat drift and searched until the bench gave up its secret.")
    elif clue.id == "note":
        world.say(f"{child.label} opened the corduroy book cover and found a folded note tucked inside.")
    else:
        world.say(f"{child.label} lifted the bright shell and understood why the ripple had appeared.")
    propagate(world, narrate=True)

    world.para()
    child.memes["surprise"] += 1
    child.memes["relief"] += 1
    world.say(f"The surprise was gentle: the missing thing was not lost at all, just hidden by a small twist of the day.")
    world.say(f"{parent.label} smiled, and {child.label} smiled back, happy that the mystery was solved.")
    if clue.id == "boat":
        world.say(f"The tiny boat drifted home in {child.label}'s hands, and the pond looked calm again.")
    elif clue.id == "button":
        world.say(f"The corduroy coat got its button back, and the pocket was whole again.")
    elif clue.id == "note":
        world.say(f"The note was read aloud, and the corduroy cover felt like a secret map no more.")
    else:
        world.say(f"The shell stayed on the shelf, and the water kept only a soft ripple of memory.")

    world.facts.update(
        child=child,
        parent=parent,
        clue=clue,
        setting=params.setting,
        clue_id=params.clue,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    clue = f["clue"]
    return [
        f'Write a short mystery for a 3-to-5-year-old that includes the words "ripple", "corduroy", and "drift".',
        f"Tell a gentle mystery where {child.label} is curious, follows {clue.label}, and solves the surprise with a parent nearby.",
        f"Write a child-friendly story about a clue that drifts, a ripple that catches the eye, and a corduroy detail that helps solve the mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    clue = f["clue"]
    setting = SETTINGS[f["setting"]]
    return [
        QAItem(
            question=f"Who was curious in the story at {setting.place}?",
            answer=f"{child.label} was the curious child. {child.label} kept looking closely because a small mystery was waiting.",
        ),
        QAItem(
            question=f"What clue did {child.label} notice?",
            answer=f"{child.label} noticed {clue.label}. That clue helped point the story toward the answer.",
        ),
        QAItem(
            question=f"Where did the mystery happen?",
            answer=f"The mystery happened at {setting.place}. That was the place where the ripple, the clue, and the surprise all met.",
        ),
        QAItem(
            question=f"Why was the answer a surprise?",
            answer=f"It was a surprise because the missing thing was not truly gone. It was hidden or shifted in a small way, so the mystery could be solved once {child.label} followed the clue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ripple?",
            answer="A ripple is a small wave on water. It often spreads out in circles after something touches the water.",
        ),
        QAItem(
            question="What is corduroy?",
            answer="Corduroy is a fabric with soft ridges. People use it for clothes like coats, pants, and hats.",
        ),
        QAItem(
            question="What does drift mean?",
            answer="Drift means to move slowly along, often because of wind or water.",
        ),
        QAItem(
            question="What does curiosity help you do?",
            answer="Curiosity helps you notice things and ask questions so you can learn what is going on.",
        ),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        if e.revealed:
            bits.append("revealed=True")
        lines.append(f"  {e.id:5} ({e.kind:9}) {e.label or e.type} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
clue(C) :- clue_fact(C).

curious(C) :- child(C).
can_solve(S, C) :- setting(S), clue(C), ripple_setting(S).
can_solve(S, C) :- setting(S), clue(C), drift_clue(C).
valid_story(S, C) :- can_solve(S, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        if s.has_ripple:
            lines.append(asp.fact("ripple_setting", sid))
        if s.has_drift:
            lines.append(asp.fact("drift_setting", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue_fact", cid))
        if c.drift_ok:
            lines.append(asp.fact("drift_clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    mapped = set((s, c) for s, c in python_set if SETTINGS[s].has_ripple or CLUES[c].drift_ok or not SETTINGS[s].indoors)
    if clingo_set == mapped:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - mapped:
        print("  only in clingo:", sorted(clingo_set - mapped))
    if mapped - clingo_set:
        print("  only in python:", sorted(mapped - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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


CURATED = [
    StoryParams(setting="pond", clue="boat", child_name="Mia", child_gender="girl", parent_name="Mom", parent_gender="mother"),
    StoryParams(setting="garden", clue="shell", child_name="Finn", child_gender="boy", parent_name="Dad", parent_gender="father"),
    StoryParams(setting="library", clue="note", child_name="Nora", child_gender="girl", parent_name="Mom", parent_gender="mother"),
    StoryParams(setting="attic", clue="button", child_name="Leo", child_gender="boy", parent_name="Dad", parent_gender="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
