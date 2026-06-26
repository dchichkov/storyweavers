#!/usr/bin/env python3
"""
storyworlds/worlds/mobile_repetition_reconciliation_curiosity_mystery.py
=======================================================================

A small story world about a curious child, a mysterious mobile, and a gentle
reconciliation after repetition of a noisy mistake.

Source-tale seed, imagined into a world:
---
A child finds a hanging mobile in a quiet room. It spins and clicks in the same
little pattern over and over. The child grows curious and keeps going back to
listen, but each time the mobile gets nudged it wakes a sleeping sibling. A
parent explains the mystery: the mobile is meant to hang still above the crib.
The child learns to look without touching, then helps set it right, and the room
feels calm again.

Story shape:
- setup: the child notices the mobile and wants to understand it
- tension: repeated touching makes the same sound and causes the same problem
- turn: the child learns the reason for the mystery
- resolution: everyone agrees on a careful, kinder way to look
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the nursery"
    quiet: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectItem:
    label: str
    phrase: str
    type: str
    fragile: bool = False


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    mobile = world.entities.get("mobile")
    sibling = world.entities.get("sibling")
    if not child or not mobile or not sibling:
        return out
    if child.memes["curiosity"] < THRESHOLD:
        return out
    if mobile.meters["touched"] < THRESHOLD:
        return out
    sig = ("repeat", child.id, mobile.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mobile.meters["clicks"] += 1
    sibling.meters["woken"] += 1
    out.append(f"The mobile clicked again, and the sleeping room stirred.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    parent = world.entities.get("parent")
    mobile = world.entities.get("mobile")
    sibling = world.entities.get("sibling")
    if not child or not parent or not mobile or not sibling:
        return out
    if child.memes["conflict"] < THRESHOLD:
        return out
    sig = ("reconcile", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["conflict"] = 0.0
    child.memes["trust"] += 1
    sibling.meters["woken"] = 0.0
    mobile.meters["repaired"] += 1
    out.append(f"The room settled again, as if it had been listening for the right answer.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("repeat", "physical", _r_repeat),
    Rule("reconcile", "social", _r_reconcile),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    if setting.quiet:
        return f"The {setting.place.removeprefix('the ')} was very quiet, and even tiny sounds felt big."
    return f"{setting.place.capitalize()} was bright, but the corners still held little shadows."


def predict_effect(world: World, child: Entity) -> dict:
    sim = world.copy()
    sim.entities["mobile"].meters["touched"] += 1
    sim.get(child.id).memes["curiosity"] += 1
    propagate(sim, narrate=False)
    return {
        "woken": sim.entities["sibling"].meters["woken"] >= THRESHOLD,
        "clicks": sim.entities["mobile"].meters["clicks"],
    }


def introduce(world: World, child: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "curious")
    world.say(f"{child.id} was a little {trait} {child.type} who noticed every quiet thing.")


def loves_mystery(world: World, child: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.pronoun().capitalize()} loved mysteries, especially the kind that hid in ordinary rooms."
    )


def discover(world: World, child: Entity, mobile: Entity) -> None:
    child.memes["curiosity"] += 1
    mobile.meters["seen"] += 1
    world.say(
        f"One day, {child.id} found a hanging mobile above the little bed."
    )
    world.say(
        f"It swayed in a slow pattern, and {child.id} kept watching because the shapes looked almost like a secret."
    )


def repeat_tap(world: World, child: Entity, mobile: Entity, sibling: Entity) -> None:
    child.meters["taps"] += 1
    mobile.meters["touched"] += 1
    world.say(
        f"{child.id} reached up and gave the mobile a soft tap."
    )
    propagate(world, narrate=False)
    if sibling.meters["woken"] >= THRESHOLD:
        world.say(
            f"The same little click happened again, and the baby stirred awake with a fussy sound."
        )
        world.say(
            f"{child.id} tried once more, hoping the answer would change, but the mystery only got noisier."
        )


def warn(world: World, parent: Entity, child: Entity, mobile: Entity) -> None:
    pred = predict_effect(world, child)
    if pred["woken"]:
        world.say(
            f'"If you keep touching it, {mobile.label} will keep clicking and wake the baby," '
            f"{parent.label_word} said."
        )
        child.memes["conflict"] += 1
        world.facts["warned"] = True


def wonder(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} frowned, because the mobile was pretty and the rule felt strange."
    )
    world.say(
        f"Why should a thing made for looking not be touched at all?"
    )


def explain(world: World, parent: Entity, child: Entity, mobile: Entity) -> None:
    world.say(
        f"{parent.label_word} knelt beside {child.id} and pointed to the little bed."
    )
    world.say(
        f'"The mobile is for watching," {parent.label_word} said. "It hangs there to spin gently, not to be pulled."'
    )
    world.say(
        f"Then the mystery made sense: the clicking was not magic at all, only a tiny piece knocking each time {child.id} nudged it."
    )


def reconcile(world: World, parent: Entity, child: Entity, mobile: Entity, sibling: Entity) -> None:
    child.memes["trust"] += 1
    child.memes["curiosity"] += 1
    child.memes["conflict"] += 1
    world.say(
        f"{child.id} nodded and carefully took {child.pronoun('possessive')} hand back."
    )
    world.say(
        f'"I can look with my eyes," {child.id} said, "and use my fingers for something kinder."'
    )
    world.say(
        f"Together they straightened the mobile, and the baby slept again while the colored pieces turned softly above the crib."
    )
    propagate(world, narrate=False)
    child.memes["conflict"] = 0.0


def tell(setting: Setting, activity: Activity, mobile_name: str = "mobile") -> World:
    world = World(setting)
    child = world.add(Entity(id="Mina", kind="character", type="girl", traits=["little", "curious", "patient"]))
    parent = world.add(Entity(id="parent", kind="character", type="mother", label="the parent"))
    sibling = world.add(Entity(id="baby", kind="character", type="baby", label="the baby"))
    mobile = world.add(Entity(id="mobile", type="mobile", label="mobile", phrase="a hanging mobile"))
    world.facts.update(child=child, parent=parent, sibling=sibling, mobile=mobile, activity=activity, setting=setting)

    introduce(world, child)
    loves_mystery(world, child)
    world.say(setting_detail(setting))
    discover(world, child, mobile)

    world.para()
    world.say(f"{child.id} wanted to {activity.verb}, because the motion looked like a clue.")
    warn(world, parent, child, mobile)
    wonder(world, child)
    repeat_tap(world, child, mobile, sibling)

    world.para()
    explain(world, parent, child, mobile)
    reconcile(world, parent, child, mobile, sibling)
    return world


SETTINGS = {
    "nursery": Setting(place="the nursery", quiet=True, affords={"look", "tap"}),
    "bedroom": Setting(place="the bedroom", quiet=True, affords={"look", "tap"}),
    "playroom": Setting(place="the playroom", quiet=False, affords={"look", "tap"}),
}

ACTIVITIES = {
    "tap": Activity(
        id="tap",
        verb="tap the mobile",
        gerund="tapping the mobile",
        rush="reach up and tap the mobile again",
        mess="noise",
        soil="noisy",
        keyword="mobile",
        tags={"mobile", "curiosity", "repetition", "mystery"},
    ),
    "look": Activity(
        id="look",
        verb="look closely at the mobile",
        gerund="looking closely at the mobile",
        rush="lean in for another look",
        mess="none",
        soil="",
        keyword="mobile",
        tags={"mobile", "curiosity", "mystery"},
    ),
}

CURATED = [
    ("nursery", "tap"),
    ("bedroom", "tap"),
    ("nursery", "look"),
]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str = "Mina"
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, parent, mobile, activity = f["child"], f["parent"], f["mobile"], f["activity"]
    return [
        f'Write a short mystery story for a child named {child.id} about a {mobile.label} in {f["setting"].place}.',
        f"Tell a gentle story where {child.id} keeps wanting to {activity.verb} but learns why the {mobile.label} should be watched, not touched.",
        f'Write a child-friendly mystery with repetition, where the same click keeps happening until {child.id} and {parent.label_word} solve it together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, sibling, mobile, activity = f["child"], f["parent"], f["sibling"], f["mobile"], f["activity"]
    qa = [
        QAItem(
            question=f"Who was curious about the mobile in {f['setting'].place}?",
            answer=f"{child.id} was curious about the mobile in {f['setting'].place}, because {child.pronoun()} liked trying to understand quiet, puzzling things.",
        ),
        QAItem(
            question=f"What happened when {child.id} tried to {activity.verb} again?",
            answer=f"When {child.id} tried to {activity.verb} again, the mobile clicked once more and the baby woke up.",
        ),
        QAItem(
            question=f"How did {child.id} and {parent.label_word} fix the problem?",
            answer=f"They agreed to stop touching the mobile, set it straight, and let it hang calmly above the crib.",
        ),
    ]
    if sibling.meters["woken"] >= THRESHOLD:
        qa.append(
            QAItem(
                question=f"Why did the parent warn {child.id} about the mobile?",
                answer=f"The parent warned {child.id} because each tap made the mobile click again, and that sound kept waking the baby.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mobile?",
            answer="A mobile is a hanging object with pieces that can move gently in the air, often above a crib or bed.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to learn about something because it seems interesting or mysterious.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing the same thing again and again.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a problem or disagreement.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
curious(C) :- child(C), curiosity(C).
repeated(M) :- mobile(M), touched(M), clicked(M).
problem(C) :- curious(C), repeated(mobile), wakes(baby).
resolved(C) :- problem(C), reconciled(C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tagged", aid, t))
    lines.append(asp.fact("child", "mina"))
    lines.append(asp.fact("mobile", "mobile"))
    lines.append(asp.fact("baby", "baby"))
    lines.append(asp.fact("parent", "parent"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            if "mobile" in act.tags:
                combos.append((place, act_id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1. #show activity/1."))
    return sorted(set(asp.atoms(model, "setting"))), sorted(set(asp.atoms(model, "activity")))


def asp_verify() -> int:
    clingo_set = set(valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: mobile, repetition, reconciliation, curiosity, mystery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos() if (args.place is None or c[0] == args.place) and (args.activity is None or c[1] == args.activity)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity = rng.choice(sorted(combos))
    return StoryParams(place=place, activity=activity, name=args.name or rng.choice(["Mina", "Lena", "Noah", "Owen"]))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show setting/1. #show activity/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(place=p, activity=a)) for p, a in CURATED]
    else:
        seen: set[str] = set()
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place}: {p.activity}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
