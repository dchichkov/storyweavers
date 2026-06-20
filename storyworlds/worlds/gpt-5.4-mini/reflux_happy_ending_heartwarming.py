#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/reflux_happy_ending_heartwarming.py
===================================================================

A standalone storyworld for a tiny heartwarming reflux tale: a child gets
uncomfortable reflux after a too-quick snack, a caring grown-up notices the
problem, makes a gentle fix, and the day ends with comfort, safety, and a warm
image of recovery.

The world is intentionally small and classical:
- one child
- one caring adult
- one cozy setting
- one food/drink choice that can trigger reflux
- one gentle remedy that actually helps
- one happy ending image that proves the change

The simulated state drives the prose. The story is not a frozen paragraph with
swapped nouns; it is built from a sequence of state changes and causal beats.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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


@dataclass
class Setting:
    id: str
    place: str
    cozy_detail: str
    light: str
    indoors: bool = True


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    trigger: str
    risk: int
    refluxy: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    action: str
    strength: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    tag: str
    apply: Callable[[World], list[str]]


def _r_reflux(world: World) -> list[str]:
    out = []
    kid = world.get("child")
    if kid.meters["reflux"] >= THRESHOLD:
        sig = ("reflux",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        kid.memes["uncomfortable"] += 1
        out.append("__reflux__")
    return out


def _r_worry(world: World) -> list[str]:
    out = []
    kid = world.get("child")
    adult = world.get("adult")
    if kid.meters["reflux"] >= THRESHOLD and ("worry",) not in world.fired:
        world.fired.add(("worry",))
        adult.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_comfort(world: World) -> list[str]:
    out = []
    kid = world.get("child")
    adult = world.get("adult")
    if kid.meters["settled"] >= THRESHOLD and ("comfort",) not in world.fired:
        world.fired.add(("comfort",))
        kid.memes["safe"] += 1
        adult.memes["relief"] += 1
        out.append("__comfort__")
    return out


CAUSAL_RULES = [
    Rule("reflux", "physical", _r_reflux),
    Rule("worry", "social", _r_worry),
    Rule("comfort", "social", _r_comfort),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def trigger_reflux(snack: Snack) -> bool:
    return snack.refluxy


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def can_help(remedy: Remedy, snack: Snack) -> bool:
    return remedy.strength >= snack.risk


def predict_flare(world: World, snack_id: str, remedy_id: str) -> dict:
    sim = world.copy()
    kid = sim.get("child")
    snack = SNACKS[snack_id]
    remedy = REMEDIES[remedy_id]
    if trigger_reflux(snack):
        kid.meters["reflux"] += 1
        propagate(sim, narrate=False)
    if can_help(remedy, snack):
        kid.meters["settled"] += 1
        kid.meters["reflux"] = 0
        propagate(sim, narrate=False)
    return {
        "reflux": sim.get("child").meters["reflux"] >= THRESHOLD,
        "settled": sim.get("child").meters["settled"] >= THRESHOLD,
    }


def setup(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    adult.memes["love"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} and {adult.id} were at {setting.place}. "
        f"{setting.cozy_detail}"
    )


def snack_time(world: World, child: Entity, snack: Snack) -> None:
    child.memes["eager"] += 1
    world.say(
        f"{child.id} reached for {snack.phrase} because {snack.trigger}."
    )
    world.say(
        f"{child.id} liked the taste and took a little too much at once."
    )


def flare(world: World, child: Entity, snack: Snack) -> None:
    child.meters["reflux"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Soon {child.id} felt reflux in {child.pronoun('possessive')} chest, "
        f"and {child.id} wrinkled {child.pronoun('possessive')} nose."
    )


def notice(world: World, adult: Entity, child: Entity) -> None:
    world.say(
        f"{adult.label_word.capitalize()} noticed right away and sat beside {child.id}."
    )
    world.say(
        f'"Are you feeling that burn in your throat, sweetheart?" {adult.id} asked softly.'
    )


def soothe(world: World, adult: Entity, child: Entity, remedy: Remedy) -> None:
    child.meters["settled"] += 1
    child.meters["reflux"] = 0
    propagate(world, narrate=False)
    world.say(
        f"{adult.label_word.capitalize()} used a gentle fix: {remedy.phrase}."
    )
    world.say(
        f"{adult.id} {remedy.action}, then helped {child.id} stay upright and rest."
    )


def heal(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    child.memes["relief"] += 1
    child.memes["love"] += 1
    adult.memes["relief"] += 1
    world.say(
        f"After a while, the ache faded. {child.id} sighed and leaned against "
        f"{adult.id}, warm and safe again."
    )
    world.say(
        f"By the end, the room felt cozy, and {child.id} was smiling under {setting.light}."
    )


def tell(setting: Setting, snack: Snack, remedy: Remedy,
         child_name: str = "Milo", child_gender: str = "boy",
         adult_name: str = "Mom", adult_gender: str = "girl") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    world.facts["snack"] = snack
    world.facts["remedy"] = remedy
    world.facts["setting"] = setting

    setup(world, child, adult, setting)
    world.para()
    snack_time(world, child, snack)
    flare(world, child, snack)
    notice(world, adult, child)
    world.para()
    soothe(world, adult, child, remedy)
    heal(world, child, adult, setting)

    world.facts.update(
        child=child,
        adult=adult,
        settled=child.meters["settled"] >= THRESHOLD,
        refluxed=child.meters["reflux"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "couch": Setting("couch", "the couch by the window", "A soft blanket was folded nearby, and a tiny lamp glowed on the table.", "the lamp"),
    "kitchen": Setting("kitchen", "the kitchen nook", "A bowl of apples waited on the counter, and sunlight was spilling across the floor.", "the sunshine"),
    "bedroom": Setting("bedroom", "the little bedroom", "A stuffed bear watched from the pillow, and the curtains made the room feel calm.", "the nightlight"),
}

SNACKS = {
    "juice": Snack("juice", "juice", "a big cup of orange juice", "it was sweet and went down quickly", 2, tags={"drink", "sweet"}),
    "candy": Snack("candy", "candy", "a handful of candy", "it was a treat and easy to gobble up", 3, tags={"sweet"}),
    "pizza": Snack("pizza", "pizza", "a few quick bites of pizza", "the slices were warm and tasty", 2, tags={"food"}),
    "cookies": Snack("cookies", "cookies", "two cookies and a little milk", "it was bedtime snack time", 2, tags={"food", "sweet"}),
}

REMEDIES = {
    "upright": Remedy("upright", "sit-up cuddle", "a gentle sit-up cuddle", "kept {child} sitting up for a while", 3, 3, tags={"comfort"}),
    "water": Remedy("water", "water", "a little cup of water", "let {child} sip slowly", 2, 2, tags={"drink"}),
    "blanket": Remedy("blanket", "blanket", "a warm blanket and slow breaths", "wrapped {child} in a blanket and counted soft breaths", 2, 2, tags={"comfort"}),
    "doctor": Remedy("doctor", "doctor call", "a quick call to the doctor", "called the doctor for a calm check-in", 4, 3, tags={"help"}),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Ella", "Ruby"]
BOY_NAMES = ["Milo", "Finn", "Leo", "Owen", "Theo", "Noah"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for snack_id, snack in SNACKS.items():
            if not snack.refluxy:
                continue
            for rid, remedy in REMEDIES.items():
                if can_help(remedy, snack):
                    combos.append((sid, snack_id, rid))
    return combos


@dataclass
class StoryParams:
    setting: str
    snack: str
    remedy: str
    child: str
    child_gender: str
    adult: str
    adult_gender: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "reflux": [("What is reflux?", "Reflux is when tummy contents come back up and make the chest or throat feel hot, sour, or uncomfortable.")],
    "upright": [("Why help someone stay upright after reflux?", "Staying upright makes it harder for food and sour liquid to come back up, so the person can feel better.")],
    "water": [("Why can sipping water help after reflux?", "A small sip can feel soothing and help wash away the sour taste, as long as you sip slowly.")],
    "blanket": [("How can a blanket help a sick child feel better?", "A blanket can make a child feel warm and safe while they rest, which is comforting.")],
    "doctor": [("When should you call a doctor?", "A grown-up should call a doctor if something feels serious, lasts a long time, or keeps getting worse.")],
}
KNOWLEDGE_ORDER = ["reflux", "upright", "water", "blanket", "doctor"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the word "{f["snack"].id}" and the word "reflux".',
        f"Tell a gentle happy-ending story where {f['child'].id} gets reflux after {f['snack'].label}, and {f['adult'].id} helps {f['child'].id} feel better.",
        f"Write a cozy story about a child, a caring adult, and a small reflux problem that ends with a safe, comforting fix.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    snack = f["snack"]
    remedy = f["remedy"]
    setting = f["setting"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {adult.id} at {setting.place}. The story centers on a small reflux problem and a gentle kind response."),
        (f"What made {child.id} feel reflux?", f"{child.id} felt reflux after {snack.phrase}. It happened because the snack was eaten too quickly, so it rose up and felt uncomfortable."),
        (f"What did {adult.id} do to help?", f"{adult.id} used {remedy.phrase} and helped {child.id} stay upright. That gentle help gave the reflux time to settle down."),
        (f"How did the story end?", f"It ended happily, with {child.id} feeling safe and comfy again. {adult.id} stayed close, and the room felt warm and peaceful."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {world.facts["snack"].id, world.facts["remedy"].id, "reflux"}
    out = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("couch", "juice", "upright", "Milo", "boy", "Mom", "girl"),
    StoryParams("kitchen", "pizza", "water", "Nora", "girl", "Dad", "boy"),
    StoryParams("bedroom", "cookies", "blanket", "Ivy", "girl", "Mom", "girl"),
    StoryParams("couch", "candy", "doctor", "Finn", "boy", "Mom", "girl"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.snack and args.remedy and not can_help(REMEDIES[args.remedy], SNACKS[args.snack]):
        raise StoryError("(No story: that remedy is too weak to help with that snack's reflux.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.snack is None or c[1] == args.snack)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, snack, remedy = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    child = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    adult_gender = rng.choice(["girl", "boy"])
    adult = "Mom" if adult_gender == "girl" else "Dad"
    if args.child:
        child = args.child
    if args.adult:
        adult = args.adult
    return StoryParams(setting, snack, remedy, child, child_gender, adult, adult_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SNACKS[params.snack], REMEDIES[params.remedy],
                 params.child, params.child_gender, params.adult, params.adult_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming reflux story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child")
    ap.add_argument("--adult")
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


ASP_RULES = r"""
good_snack(S) :- snack(S), refluxy(S).
good_remedy(R) :- remedy(R), sense(R, X), sense_min(M), X >= M.
valid_story(Se, Sn, Re) :- setting(Se), snack(Sn), remedy(Re), refluxy(Sn), helps(Re, Sn).
outcome(settled) :- chosen_snack(Sn), chosen_remedy(Re), helps(Re, Sn).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, sn in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if sn.refluxy:
            lines.append(asp.fact("refluxy", sid))
    for rid, re in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, re.sense))
        lines.append(asp.fact("strength", rid, re.strength))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for snid, sn in SNACKS.items():
            for rid, re in REMEDIES.items():
                if sn.refluxy and can_help(re, sn):
                    combos.append((sid, snid, rid))
    return combos


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
