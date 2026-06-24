#!/usr/bin/env python3
"""
storyworlds/worlds/septic_silent_kindness_inner_monologue_reconciliation_slice.py
=================================================================================

A small slice-of-life story world about a quiet household moment where a child
notices a septic problem, thinks it through in an inner monologue, and chooses
a kind, careful reconciliation instead of making things harder.

Seed tale sketch:
---
Mina lived with her aunt in a small house at the edge of town. One evening, Mina
heard that the usual backyard hum had gone silent. Her aunt looked worried and
said the septic tank might be acting up. Mina wanted to help right away, but she
also knew the house was resting quiet after dinner, and the baby next door had
just fallen asleep.

Mina thought to herself that the best help was the kind that did not make a
bigger mess. She brought her aunt the flashlight, held the gate open, and spoke
in a whisper. Together they checked the path, called the plumber, and waited
without fuss. When the plumber came, the problem was fixed, and Mina's aunt
smiled at her for being thoughtful and calm.

Causal state updates:
---
    noticing a septic problem   -> concern += 1
    silent helpful action       -> calm += 1, trust += 1
    hurried noisy action        -> alarm += 1, conflict += 1
    careful help + apology      -> conflict -> 0, trust += 1, warmth += 1

Narrative instruments:
---
    inner monologue            -> child.reflect += 1, child.calm += 1
    kindness offer             -> caregiver.trust += 1
    reconciliation accepted    -> both warmth += 1, conflict -> 0
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"mess": 0.0}
        if not self.memes:
            self.memes = {"calm": 0.0, "trust": 0.0, "warmth": 0.0, "conflict": 0.0, "concern": 0.0,
                          "reflection": 0.0, "kindness": 0.0, "alarm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Issue:
    id: str
    label: str
    clue: str
    risk: str
    worry: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelpItem:
    id: str
    label: str
    offer: str
    effect: str
    quiet: bool = True


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
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_concern(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("concern", 0) < THRESHOLD:
            continue
        sig = ("concerned", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{e.id} felt a small worry settle in.")
    return out


def _r_inner_reflection(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    if not child:
        return out
    if child.memes.get("reflection", 0) < THRESHOLD:
        return out
    sig = ("reflection", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(f"{child.id} paused and listened to their own thoughts.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    caregiver = next((e for e in world.characters() if e.kind == "character" and e.type in {"mother", "father", "aunt", "uncle"}), None)
    if not child or not caregiver:
        return out
    if child.memes.get("alarm", 0) < THRESHOLD:
        return out
    sig = ("alarm_conflict", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["conflict"] += 1
    caregiver.memes["conflict"] += 1
    out.append(f"The hurried moment made both of them feel tense.")
    return out


CAUSAL_RULES = [
    Rule("concern", "social", _r_concern),
    Rule("reflection", "social", _r_inner_reflection),
    Rule("conflict", "social", _r_conflict),
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


def predict(world: World, child: Entity, issue: Issue, help_item: HelpItem) -> dict:
    sim = world.copy()
    do_notice(sim, sim.get(child.id), issue, narrate=False)
    do_help(sim, sim.get(child.id), sim.get("Caregiver"), help_item, narrate=False)
    return {
        "calm": sim.get(child.id).memes["calm"],
        "conflict": sim.get("Caregiver").memes["conflict"] + sim.get(child.id).memes["conflict"],
    }


def do_notice(world: World, child: Entity, issue: Issue, narrate: bool = True) -> None:
    child.memes["concern"] += 1
    world.facts["issue_seen"] = issue.id
    if narrate:
        world.say(f"{child.id} noticed that the {issue.label} had gone {issue.clue}.")


def do_inner_monologue(world: World, child: Entity, issue: Issue, narrate: bool = True) -> None:
    child.memes["reflection"] += 1
    child.memes["calm"] += 1
    if narrate:
        world.say(
            f"{child.id} thought, 'If I stay quiet and careful, I can help without making the {issue.label} harder to fix.'"
        )


def do_alarm(world: World, child: Entity, narrate: bool = True) -> None:
    child.memes["alarm"] += 1
    if narrate:
        world.say(f"{child.id} almost rushed to fix everything at once.")


def do_help(world: World, child: Entity, caregiver: Entity, help_item: HelpItem, narrate: bool = True) -> None:
    child.memes["kindness"] += 1
    child.memes["trust"] += 1
    caregiver.memes["trust"] += 1
    caregiver.memes["warmth"] += 1
    if narrate:
        world.say(help_item.offer)
        world.say(help_item.effect)


def do_reconcile(world: World, child: Entity, caregiver: Entity, narrate: bool = True) -> None:
    child.memes["conflict"] = 0
    caregiver.memes["conflict"] = 0
    child.memes["warmth"] += 1
    caregiver.memes["warmth"] += 1
    if narrate:
        world.say(
            f"{caregiver.id} smiled, and {child.id} felt the argument soften into understanding."
        )


def build_scene(setting: Setting, issue: Issue, help_item: HelpItem,
                name: str = "Mina", child_type: str = "girl", caregiver_type: str = "aunt") -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=child_type, traits=["quiet", "thoughtful"]))
    caregiver = world.add(Entity(id="Caregiver", kind="character", type=caregiver_type, label="the caregiver"))
    world.add(Entity(id="Issue", kind="thing", type="thing", label=issue.label, phrase=issue.keyword))

    world.say(f"{child.id} lived in {setting.place}, where the evenings often felt soft and still.")
    world.say(f"That day, the {issue.label} was {issue.clue}, and the whole yard felt a little too silent.")

    world.para()
    do_notice(world, child, issue)
    do_inner_monologue(world, child, issue)
    do_alarm(world, child)
    propagate(world)

    world.para()
    if child.memes["alarm"] >= THRESHOLD:
        world.say(f"{child.id} wanted to rush, but remembered that loud hurry would only add more worry.")
    do_help(world, child, caregiver, help_item)
    do_reconcile(world, child, caregiver)

    world.para()
    world.say(
        f"In the end, they handled the {issue.label} together, and the house felt calm again."
    )
    world.say(
        f"{child.id} kept the quiet kindness of that evening in their heart as the last light faded."
    )

    world.facts.update(child=child, caregiver=caregiver, issue=issue, help_item=help_item, setting=setting)
    return world


SETTINGS = {
    "house": Setting(place="a small house at the edge of town", indoor=False, affords={"septic"}),
    "garden": Setting(place="a narrow yard behind the house", indoor=False, affords={"septic"}),
    "kitchen": Setting(place="a warm kitchen with an open window", indoor=True, affords={"septic"}),
}

ISSUES = {
    "septic": Issue(
        id="septic",
        label="septic tank",
        clue="gone silent",
        risk="stayed unnoticed",
        worry="the yard would need attention",
        keyword="septic",
        tags={"septic", "silent"},
    ),
    "pump": Issue(
        id="pump",
        label="water pump",
        clue="too quiet",
        risk="would leave no water for chores",
        worry="the sink would not work",
        keyword="silent",
        tags={"silent"},
    ),
}

HELPS = {
    "flashlight": HelpItem(
        id="flashlight",
        label="a flashlight",
        offer="So the child brought a flashlight and held it steady while whispering to the caregiver.",
        effect="That small help made the dark corner easier to check.",
    ),
    "kettle": HelpItem(
        id="kettle",
        label="a kettle of warm water",
        offer="The child quietly brought a kettle of warm water, careful not to clatter the tray.",
        effect="The gentle offering gave the caregiver one less thing to carry.",
    ),
    "gate": HelpItem(
        id="gate",
        label="the gate",
        offer="The child opened the gate slowly and kept it from creaking.",
        effect="That careful move kept the whole yard peaceful.",
    ),
}

CURATED = [
    ("house", "septic", "flashlight"),
    ("garden", "septic", "gate"),
    ("kitchen", "pump", "kettle"),
]


@dataclass
class StoryParams:
    place: str
    issue: str
    help_item: str
    name: str
    child_type: str
    caregiver_type: str
    trait: str
    seed: Optional[int] = None


def issue_at_risk(issue: Issue, setting: Setting) -> bool:
    return issue.id in setting.affords


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p, setting in SETTINGS.items():
        for i, issue in ISSUES.items():
            if not issue_at_risk(issue, setting):
                continue
            for h in HELPS:
                combos.append((p, i, h))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about septic quiet, kindness, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--issue", choices=ISSUES)
    ap.add_argument("--help-item", choices=HELPS)
    ap.add_argument("--gender", dest="child_type", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["aunt", "mother", "father", "uncle"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.issue is None or c[1] == args.issue)
              and (args.help_item is None or c[2] == args.help_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, issue, help_item = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Mina", "Noa", "Lena", "Eli", "Tess", "Owen"])
    caregiver_type = args.caregiver or rng.choice(["aunt", "mother", "father", "uncle"])
    trait = args.trait or rng.choice(["quiet", "thoughtful", "gentle", "patient"])
    return StoryParams(place=place, issue=issue, help_item=help_item, name=name, child_type=child_type,
                       caregiver_type=caregiver_type, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child about "{f["issue"].keyword}" and a quiet way of helping.',
        f"Tell a gentle story where {f['child'].id} notices a septic problem, thinks to themself, and helps without making noise.",
        "Write a calm story about kindness, inner monologue, and reconciliation in a small home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    issue = f["issue"]
    help_item = f["help_item"]
    return [
        QAItem(
            question=f"What did {child.id} notice about the {issue.label}?",
            answer=f"{child.id} noticed that the {issue.label} had gone {issue.clue}.",
        ),
        QAItem(
            question=f"What did {child.id} think to themself before helping?",
            answer="They thought that staying quiet and careful would help more than rushing.",
        ),
        QAItem(
            question=f"How did {child.id} help {caregiver.id}?",
            answer=f"{child.id} helped by using {help_item.label} and keeping the moment calm and quiet.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and {caregiver.id}?",
            answer=f"They ended the evening with reconciliation, and both felt warmer and more peaceful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a septic tank?",
            answer="A septic tank is a container underground that helps handle wastewater from a house.",
        ),
        QAItem(
            question="Why can being silent help in a busy moment?",
            answer="Being silent can help because it keeps people calm and avoids waking others or adding more stress.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset and make peace again.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone chooses to help, care, or be gentle with another person.",
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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
issue_at_risk(P,I) :- setting(P), issue(I), afford(P,I).
kind_help(H) :- help_item(H).
valid_story(P,I,H) :- issue_at_risk(P,I), kind_help(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for iid in ISSUES:
        lines.append(asp.fact("issue", iid))
    for hid in HELPS:
        lines.append(asp.fact("help_item", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_scene(SETTINGS[params.place], ISSUES[params.issue], HELPS[params.help_item],
                        name=params.name, child_type=params.child_type, caregiver_type=params.caregiver_type)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, issue=i, help_item=h, name="Mina", child_type="girl",
                                        caregiver_type="aunt", trait="quiet"))
                   for p, i, h in CURATED]
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
