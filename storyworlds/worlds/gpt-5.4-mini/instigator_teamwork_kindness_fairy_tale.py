#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/instigator_teamwork_kindness_fairy_tale.py
==========================================================================

A small storyworld for a fairy-tale domain about an instigator who stirs trouble,
a kind helper, and a teamwork-based recovery. The world is built to generate
short, child-facing stories with a clear turn: a character proposes a risky or
selfish choice, a kind helper notices a problem, the two work together, and the
ending proves something has changed.

Core premise:
- In a fairy-tale village, a child or small hero wants to do something bold
  (usually to help, show off, or get attention).
- A neighboring character responds with kindness and teamwork.
- Their combined action repairs the situation and ends with a warm image.

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
MOOD_MIN = 0.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "fairy", "woman"}
        male = {"boy", "father", "king", "knight", "man"}
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
class Setting:
    id: str
    place: str
    opening: str
    mood: str
    treasure: str
    helper_need: str

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
class Instigation:
    id: str
    act: str
    want: str
    object: str
    risk: str
    reason: str
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
class Kindness:
    id: str
    act: str
    offer: str
    method: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

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
class Rule:
    name: str
    tag: str
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


def _r_worry(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["trouble"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ally in list(world.entities.values()):
            if ally.role == "helper":
                ally.memes["concern"] += 1
        out.append("__worry__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out = []
    if world.facts.get("helped"):
        sig = ("teamwork", world.facts.get("helper", ""))
        if sig not in world.fired:
            world.fired.add(sig)
            for e in list(world.entities.values()):
                if e.kind == "character":
                    e.memes["pride"] += 1
            out.append("__team__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("teamwork", "social", _r_teamwork)]


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


def reasonableness_gate(inst: Instigation, kindness: Kindness) -> bool:
    return inst.id in {"greedy_spell", "proud_plan", "lonely_call"} and kindness.id in {"share_cake", "lift_stone", "mend_banner"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for iid, inst in INSTIGATIONS.items():
            for kid, kind in KINDNESSES.items():
                if reasonableness_gate(inst, kind):
                    combos.append((sid, iid, kid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    instigation: str
    kindness: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    ruler: str
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


SETTINGS = {
    "lantern_village": Setting(
        "lantern_village",
        "Lantern Village",
        "In Lantern Village, where the cottages had blue roofs and the lanes smelled of honeybread, the old well slept beside the square.",
        "gentle",
        "a silver key",
        "the well needed mending",
    ),
    "rose_bridge": Setting(
        "rose_bridge",
        "Rose Bridge",
        "At Rose Bridge, the river sang under the stones, and the flower stalls bowed in the wind like little queens.",
        "bright",
        "a lost ribbon",
        "the bridge needed strength",
    ),
    "moss_castle": Setting(
        "moss_castle",
        "Moss Castle",
        "In Moss Castle, ivy climbed the walls and the bells rang like teaspoons in a cup.",
        "quiet",
        "a golden comb",
        "the gate needed fixing",
    ),
}

INSTIGATIONS = {
    "greedy_spell": Instigation("greedy_spell", "cast a greedy spell", "to keep all the sparkle", "spellbook", "the magic could spill everywhere", "the hero wanted to impress the court", {"magic", "spirit"}),
    "proud_plan": Instigation("proud_plan", "rush ahead alone", "to be the first to find the treasure", "map", "the trail could break underfoot", "the hero wanted applause", {"quest", "pride"}),
    "lonely_call": Instigation("lonely_call", "call out too loudly", "to make everyone look", "bell", "the birds could scatter and the path would be lost", "the hero felt left out", {"call", "lonely"}),
}

KINDNESSES = {
    "share_cake": Kindness("share_cake", "share a small cake", "brought a warm cake", "to calm everyone and make them think together", "the mood softened like butter", {"kind", "food"}),
    "lift_stone": Kindness("lift_stone", "lift the fallen stone", "offered both hands", "to move it together", "the path opened again", {"kind", "strength"}),
    "mend_banner": Kindness("mend_banner", "mend the torn banner", "came with needle and thread", "to stitch it side by side", "the banner fluttered whole", {"kind", "repair"}),
}

GIRL_NAMES = ["Lina", "Mara", "Nessa", "Elin", "Talia", "Rosie", "Sera", "Ivy"]
BOY_NAMES = ["Oren", "Pip", "Bram", "Alfie", "Tobin", "Nico", "Jasper", "Finn"]
TRAITS = ["brave", "thoughtful", "curious", "gentle", "quick", "bright"]


def valid_story_params(p: StoryParams) -> bool:
    return p.setting in SETTINGS and p.instigation in INSTIGATIONS and p.kindness in KINDNESSES


def tell(setting: Setting, inst: Instigation, kind: Kindness, hero: Entity, helper: Entity, ruler: Entity) -> World:
    world = World(setting)
    hero.memes["hope"] += 1
    helper.memes["kindness"] += 1
    world.add(hero)
    world.add(helper)
    world.add(ruler)
    world.add(Entity("object", label=inst.object))
    world.say(setting.opening)
    world.say(
        f"{hero.id} was the sort of child who liked to {inst.act} {inst.want}. "
        f"{hero.id} carried a little {inst.object} and kept glancing toward the palace gate."
    )
    world.say(
        f'\"I can do it alone,\" {hero.id} said, though {hero.pronoun("possessive")} heart beat fast. '
        f"That was the instigator's habit: to reach first and think later."
    )
    world.para()
    hero.meters["trouble"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {helper.id} saw the trouble coming. {helper.id} was kind enough to stop and listen, "
        f"and {helper.id} knew that {setting.helper_need}."
    )
    world.say(
        f'\"Let us work together,\" {helper.id} said. \"I {kind.offer}, and you can {kind.act} with me.\"'
    )
    if kind.id == "share_cake":
        world.say(f"{helper.id} smiled and broke the cake into two careful pieces.")
    elif kind.id == "lift_stone":
        world.say(f"{helper.id} set both hands on the stone, and {hero.id} joined in.")
    else:
        world.say(f"{helper.id} threaded the needle while {hero.id} held the cloth still.")
    world.para()
    world.facts["helped"] = True
    world.facts["helper"] = helper.id
    propagate(world, narrate=False)
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    ruler.memes["relief"] += 1
    world.say(
        f"Together they followed the plan, and {kind.ending}. "
        f"{ruler.label_word.capitalize()} only had to watch the small, careful work from the doorway."
    )
    world.say(
        f"In the end, {hero.id} was no longer alone. {helper.id} stood beside {hero.id}, "
        f"and the village glowed as if the moon itself had learned to share light."
    )
    world.facts.update(setting=setting, instigation=inst, kindness=kind, hero=hero, helper=helper, ruler=ruler)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a fairy-tale story for a young child that includes the word 'instigator' and shows kindness after a risky plan.",
        f"Tell a story about {f['hero'].id} and {f['helper'].id} in {f['setting'].place} where teamwork solves a problem gently.",
        f"Write a warm fairy tale where the instigator learns to slow down, accept help, and end with a peaceful village image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, ruler = f["hero"], f["helper"], f["ruler"]
    inst, kind, setting = f["instigation"], f["kindness"], f["setting"]
    return [
        ("Who is the story about?", f"It is about {hero.id}, who acted like an instigator, and {helper.id}, who answered with kindness. {ruler.label_word.capitalize()} is part of the castle world that watched them from afar."),
        ("What did {0} want to do?".format(hero.id), f"{hero.id} wanted to {inst.act} so {hero.pronoun('possessive')} plan would happen right away. That choice caused trouble because it was a little too hasty."),
        ("How did {0} help?".format(helper.id), f"{helper.id} helped by {kind.method}. The kind offer turned a lonely plan into teamwork."),
        ("How did the story end?", f"It ended with {kind.ending} and with {hero.id} and {helper.id} standing together. The village felt safer and warmer because they chose kindness over pride."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is teamwork?", "Teamwork means people help each other and do a job together. It often makes hard jobs feel lighter."),
        ("What is kindness?", "Kindness means being gentle, caring, and helpful to others. A kind choice can calm fear and make a problem smaller."),
        ("What is a fairy tale?", "A fairy tale is a story with a magical feeling, a brave choice, and a clear ending. It often has castles, villages, or enchanted places."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("lantern_village", "greedy_spell", "share_cake", "Lina", "girl", "Pip", "boy", "Queen Ada"),
    StoryParams("rose_bridge", "proud_plan", "lift_stone", "Bram", "boy", "Mara", "girl", "King Rowan"),
    StoryParams("moss_castle", "lonely_call", "mend_banner", "Nessa", "girl", "Oren", "boy", "Queen Elspeth"),
]


def explain_rejection() -> str:
    return "(No story: the chosen parts do not make a good fairy-tale teamwork problem.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about an instigator, kindness, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--instigation", choices=INSTIGATIONS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--ruler")
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
    if not combos:
        raise StoryError(explain_rejection())
    filtered = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.instigation is None or c[1] == args.instigation)
        and (args.kindness is None or c[2] == args.kindness)
    ]
    if not filtered:
        raise StoryError(explain_rejection())
    setting, instigation, kindness = rng.choice(sorted(filtered))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (BOY_NAMES if helper_gender == "boy" else GIRL_NAMES) if n != hero])
    ruler = args.ruler or rng.choice(["Queen Ada", "King Rowan", "Queen Elspeth"])
    return StoryParams(setting, instigation, kindness, hero, hero_gender, helper, helper_gender, ruler)


def generate(params: StoryParams) -> StorySample:
    if not valid_story_params(params):
        raise StoryError(explain_rejection())
    setting = SETTINGS[params.setting]
    inst = INSTIGATIONS[params.instigation]
    kind = KINDNESSES[params.kindness]
    hero = Entity(params.hero, kind="character", type=params.hero_gender, role="instigator", traits=["bold"])
    helper = Entity(params.helper, kind="character", type=params.helper_gender, role="helper", traits=["kind"])
    ruler = Entity("ruler", kind="character", type="queen" if "Queen" in params.ruler else "king", label=params.ruler, role="ruler")
    world = tell(setting, inst, kind, hero, helper, ruler)
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


ASP_RULES = r"""
good_combo(S, I, K) :- setting(S), instigation(I), kindness(K).
trouble(E) :- entity(E), trouble_meter(E, V), V >= 1.
teamwork :- helped(H), kindness(K), kind(K).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in INSTIGATIONS:
        lines.append(asp.fact("instigation", iid))
    for kid in KINDNESSES:
        lines.append(asp.fact("kindness", kid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show good_combo/3."))
    return sorted(set(asp.atoms(model, "good_combo")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show good_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{s} {i} {k}" for s, i, k in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.helper}: {p.instigation} + {p.kindness}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
