#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/desire_bravery_reconciliation_magic_heartwarming.py
===================================================================================

A small heartwarming storyworld about a child who feels a strong desire for a
magic keepsake, gathers bravery to make things right, and ends with reconciliation
and a gentle bit of magic.

The core domain is simple:
- a child wants a magical object or moment,
- a small mistake creates hurt feelings,
- bravery helps the child apologize,
- reconciliation unlocks a warm, magical resolution.

This file is standalone and stdlib-only.
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
BRAVERY_THRESHOLD = 1.0


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "sister": "sister", "brother": "brother"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    cozy_detail: str


@dataclass
class DesiredThing:
    id: str
    label: str
    phrase: str
    magic: str
    shines: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mistake:
    id: str
    action: str
    consequence: str
    harm: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Reconciliation:
    id: str
    apology: str
    repair: str
    gift: str
    tags: set[str] = field(default_factory=set)


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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_hurt(world: World) -> list[str]:
    out = []
    child = world.get("child")
    parent = world.get("parent")
    if child.meters["hurt"] >= THRESHOLD and ("hurt",) not in world.fired:
        world.fired.add(("hurt",))
        parent.memes["worry"] += 1
        child.memes["sad"] += 1
        out.append("__hurt__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out = []
    child = world.get("child")
    parent = world.get("parent")
    if child.memes["apology"] >= THRESHOLD and parent.memes["forgiveness"] >= THRESHOLD:
        if ("reconcile",) in world.fired:
            return out
        world.fired.add(("reconcile",))
        child.memes["love"] += 1
        parent.memes["love"] += 1
        child.memes["sad"] = 0.0
        parent.memes["worry"] = 0.0
        out.append("__reconcile__")
    return out


def _r_magic(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes["bravery"] >= BRAVERY_THRESHOLD and child.memes["reconciled"] >= THRESHOLD:
        if ("magic",) in world.fired:
            return out
        world.fired.add(("magic",))
        world.get("gift").meters["glow"] += 1
        child.memes["wonder"] += 1
        world.get("parent").memes["warmth"] += 1
        out.append("__magic__")
    return out


CAUSAL_RULES = [Rule("hurt", _r_hurt), Rule("reconcile", _r_reconcile), Rule("magic", _r_magic)]


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


def predict(m: World) -> dict:
    sim = m.copy()
    _mistake(sim, narrate=False)
    return {"hurt": sim.get("child").meters["hurt"] >= THRESHOLD}


def _mistake(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    thing = world.get("thing")
    child.meters["hurt"] += 1
    child.memes["regret"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, parent: Entity, setting: Setting, want: DesiredThing) -> None:
    child.memes["desire"] += 1
    child.memes["joy"] += 1
    world.say(
        f"On a quiet evening, {child.id} and {parent.label_word} sat in {setting.place}. "
        f"{setting.cozy_detail} {child.id} kept looking at {want.phrase}, because {child.pronoun()} felt a strong desire for it."
    )
    world.say(f'"{want.label}!" {child.id} whispered. "It looks like a little bit of magic."')


def warning(world: World, parent: Entity, child: Entity, mistake: Mistake) -> None:
    pred = predict(world)
    if pred["hurt"]:
        parent.memes["worry"] += 1
        world.facts["predicted_hurt"] = True
        world.say(
            f'{parent.label_word.capitalize()} frowned gently. "{child.id}, if you {mistake.action}, '
            f"{mistake.consequence} {mistake.harm}.""
        )


def act_wrong(world: World, child: Entity, mistake: Mistake) -> None:
    child.memes["impulse"] += 1
    world.say(f"Still, {child.id} reached out and tried to {mistake.action}.")


def bravely_apologize(world: World, child: Entity, parent: Entity, reconcile: Reconciliation) -> None:
    child.memes["bravery"] += 1
    child.memes["apology"] += 1
    parent.memes["forgiveness"] += 1
    world.say(
        f"Then {child.id} took a brave breath. "
        f'"{reconcile.apology}," {child.id} said softly. '
        f"{child.pronoun().capitalize()} helped {reconcile.repair}."
    )


def heal_and_magic(world: World, child: Entity, parent: Entity, want: DesiredThing, reconcile: Reconciliation) -> None:
    child.memes["reconciled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} smiled and pulled {child.id} close. "
        f'"Thank you for being brave," {parent.pronoun()} said. '
        f"Together they watched {reconcile.gift} {want.shines}, and the room felt warm again."
    )
    world.say(
        f"{want.magic} seemed to bloom in the air, and the hurt feelings melted away like snow in sunlight."
    )


def tell(setting: Setting, want: DesiredThing, mistake: Mistake, reconcile: Reconciliation,
         child_name: str = "Mina", child_type: str = "girl",
         parent_name: str = "Parent", parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_type, role="parent", label="the parent"))
    gift = world.add(Entity(id="gift", type="thing", label=want.label))
    world.add(Entity(id="thing", type="thing", label=want.label))
    setup(world, child, parent, setting, want)
    world.para()
    warning(world, parent, child, mistake)
    act_wrong(world, child, mistake)
    _mistake(world, narrate=True)
    world.para()
    bravely_apologize(world, child, parent, reconcile)
    heal_and_magic(world, child, parent, want, reconcile)
    world.facts.update(child=child, parent=parent, gift=gift, want=want, mistake=mistake, reconcile=reconcile)
    return world


SETTINGS = {
    "bedroom": Setting("bedroom", "the bedroom", "A little lamp glowed by the bed."),
    "garden": Setting("garden", "the garden", "Moonlight touched the flowers."),
    "kitchen": Setting("kitchen", "the kitchen", "A warm pie cooled on the counter."),
}

WANTS = {
    "star": DesiredThing("star", "the star charm", "a tiny star charm", "magic", "sparkled", {"magic", "desire"}),
    "book": DesiredThing("book", "the storybook", "an old storybook with a silver clasp", "magic", "shimmered", {"magic", "desire"}),
    "shell": DesiredThing("shell", "the seashell", "a pearl-white seashell", "magic", "glowed", {"magic", "desire"}),
}

MISTAKES = {
    "grab": Mistake("grab", "grab it without asking", "it would make", "the parent sad", {"hurt"}),
    "hide": Mistake("hide", "hide it in a drawer", "it would lead to", "a lonely, worried feeling", {"hurt"}),
}

RECONCILES = {
    "apology": Reconciliation("apology", "I'm sorry for not asking", "they put it back on the table", "the little gift box", {"reconciliation"}),
    "note": Reconciliation("note", "I wrote you a sorry note", "they fixed the torn ribbon together", "the soft ribbon bow", {"reconciliation"}),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Maya", "Ruby"]
BOY_NAMES = ["Owen", "Eli", "Theo", "Finn", "Ari", "Noah"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for w in WANTS:
            for m in MISTAKES:
                combos.append((s, w, m))
    return combos


@dataclass
class StoryParams:
    setting: str
    want: str
    mistake: str
    reconcile: str
    child_name: str
    child_type: str
    parent_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "desire": [("What is desire?",
                "Desire is a strong wish for something. It can make a person think about one thing over and over.")],
    "bravery": [("What is bravery?",
                 "Bravery is doing the right thing even when you feel nervous or scared.")],
    "reconciliation": [("What is reconciliation?",
                        "Reconciliation is making peace after a disagreement. It often includes an apology and kind words.")],
    "magic": [("What is magic in a story?",
               "Magic in a story is something wonderful and special that feels a little surprising, like a glow or sparkle.")],
    "heartwarming": [("What makes a story heartwarming?",
                      "A heartwarming story ends with kindness, comfort, and people caring about each other.")],
}

KNOWLEDGE_ORDER = ["desire", "bravery", "reconciliation", "magic", "heartwarming"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a young child that includes the word "desire" and a little bit of magic.',
        f"Tell a story where {f['child'].id} feels a strong desire for {f['want'].label}, makes a mistake, then finds bravery to say sorry.",
        f"Write a gentle story about reconciliation, magic, and bravery that ends with everyone feeling warm again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, want, mistake = f["child"], f["parent"], f["want"], f["mistake"]
    rec = f["reconcile"]
    qa = [
        ("What did the child want?",
         f"{child.id} wanted {want.phrase}, and {child.pronoun()} felt a strong desire for it because it looked magical."),
        ("What went wrong?",
         f"{child.id} tried to {mistake.action}, and that hurt the parent’s feelings. The mistake created the need for an apology."),
        ("How did they make things right?",
         f"{child.id} found bravery, said '{rec.apology}', and helped {rec.repair}. That apology opened the door to reconciliation."),
        ("How did the story end?",
         f"It ended warmly, with {want.magic} shining on {rec.gift} and both of them feeling close again. The magic showed that the reconciliation worked."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [QA for tag in KNOWLEDGE_ORDER if tag in {"desire", "bravery", "reconciliation", "magic", "heartwarming"} for QA in KNOWLEDGE[tag]]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
    StoryParams("bedroom", "star", "grab", "apology", "Mina", "girl", "mother"),
    StoryParams("garden", "shell", "hide", "note", "Owen", "boy", "father"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for w in WANTS:
        lines.append(asp.fact("want", w))
    for m in MISTAKES:
        lines.append(asp.fact("mistake", m))
    for r in RECONCILES:
        lines.append(asp.fact("reconcile", r))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,W,M) :- setting(S), want(W), mistake(M).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        with redirect_stdout(io.StringIO()):
            emit(sample)
        print("OK: generate/emit smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming desire/bravery/reconciliation/magic storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--want", choices=WANTS)
    ap.add_argument("--mistake", choices=MISTAKES)
    ap.add_argument("--reconcile", choices=RECONCILES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.want is None or c[1] == args.want)
              and (args.mistake is None or c[2] == args.mistake)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, want, mistake = rng.choice(sorted(combos))
    reconcile = args.reconcile or rng.choice(sorted(RECONCILES))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    return StoryParams(setting, want, mistake, reconcile, child_name, child_type, parent_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], WANTS[params.want], MISTAKES[params.mistake],
                 RECONCILES[params.reconcile], params.child_name, params.child_type, "Parent", params.parent_type)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, w, m in asp_valid_combos():
            print(f"  {s:8} {w:8} {m}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
