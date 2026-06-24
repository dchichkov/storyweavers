#!/usr/bin/env python3
"""
A small cautionary adventure storyworld about a cat and a whirly thing.

Seed tale:
---
A curious cat named Pippin found a whirly toy in the attic. It spun fast and
looked magical. Pippin wanted to chase it, but a wise older cat warned that the
whirly toy could knock over little things and scare the baby mice below. Pippin
paused, then used a string to watch the toy spin from a safe spot. The toy
whirled, the mice stayed calm, and Pippin learned that some exciting things are
best enjoyed with care.

This world turns that premise into a tiny state-driven simulation:
- the cat has curiosity, fear, pride, and relief as emotional memes;
- the whirly object has spin, wobble, and danger as physical meters;
- cautionary advice can avert a mess, or ignored advice can trigger one;
- the ending image proves what changed: safe distance, calmer house, wiser cat.
"""

from __future__ import annotations

import argparse
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"cat"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the attic"
    shadowy: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class WhirlyThing:
    id: str
    label: str
    phrase: str
    type: str
    danger: str
    noise: str
    zone: set[str]
    fixable: bool = True


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    guards: set[str]
    covers_distance: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def _read_spin(world: World) -> list[str]:
    out = []
    cat = world.get("cat")
    whirly = world.get("whirly")
    if cat.memes.get("curiosity", 0) >= THRESHOLD and whirly.meters.get("spin", 0) >= THRESHOLD:
        sig = ("stare",)
        if sig not in world.fired:
            world.fired.add(sig)
            cat.memes["temptation"] = cat.memes.get("temptation", 0) + 1
            out.append("The spinning made the cat itch to chase.")
    return out


def _chase_breakage(world: World) -> list[str]:
    out = []
    cat = world.get("cat")
    whirly = world.get("whirly")
    mice = world.get("mice")
    if cat.memes.get("chase", 0) < THRESHOLD:
        return out
    sig = ("breakage",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    whirly.meters["wobble"] = whirly.meters.get("wobble", 0) + 1
    if whirly.meters["wobble"] >= THRESHOLD:
        mice.memes["startle"] = mice.memes.get("startle", 0) + 1
        cat.memes["guilt"] = cat.memes.get("guilt", 0) + 1
        out.append("The whirly thing wobbled, and the little mice below got a fright.")
    return out


def _safe_distance(world: World) -> list[str]:
    out = []
    cat = world.get("cat")
    whirly = world.get("whirly")
    if cat.meters.get("distance", 0) >= THRESHOLD and whirly.meters.get("spin", 0) >= THRESHOLD:
        sig = ("safed",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        cat.memes["pride"] = cat.memes.get("pride", 0) + 1
        cat.memes["relief"] = cat.memes.get("relief", 0) + 1
        out.append("From a safe distance, the cat could watch without causing trouble.")
    return out


CAUSAL_RULES = [_read_spin, _chase_breakage, _safe_distance]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_consequence(world: World, cat: Entity, whirly: WhirlyThing) -> dict:
    sim = world.copy()
    sim.get("cat").memes["chase"] = 1
    sim.get("whirly").meters["spin"] = 1
    propagate(sim, narrate=False)
    return {
        "startle": sim.get("mice").memes.get("startle", 0) >= THRESHOLD,
        "guilt": sim.get("cat").memes.get("guilt", 0) >= THRESHOLD,
    }


def tell(setting: Setting, whirly: WhirlyThing, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    cat = world.add(Entity(id="cat", kind="character", type="cat", label=hero_name))
    elder = world.add(Entity(id="elder", kind="character", type="cat", label=helper_name))
    mice = world.add(Entity(id="mice", kind="character", type="mouse", label="the baby mice", plural=True))
    whirl = world.add(Entity(id="whirly", type="thing", label=whirly.label, phrase=whirly.phrase))
    world.add(Entity(id="string", type="thing", label="a long string", phrase="a long string"))

    cat.memes.update(curiosity=1, courage=1)
    elder.memes.update(wisdom=1)
    mice.memes.update(calm=1)
    whirl.meters.update(spin=1)

    world.say(f"{cat.ref()} was a curious cat who loved a good adventure.")
    world.say(f"One day {cat.ref()} found {whirly.phrase} in {setting.place}, and it began to spin like a tiny storm.")
    world.say(f"{elder.ref()} saw it first and called, \"Careful now. Some whirly things are fun, but they can cause trouble.\"")

    world.para()
    world.say(f"{cat.ref()} wanted to pounce on it right away.")
    cat.memes["chase"] = 1
    propagate(world, narrate=True)

    if cat.memes.get("guilt", 0) >= THRESHOLD:
        world.para()
        world.say(f"{cat.ref()} froze, ears low, because the fright below had been real.")
        world.say(f"{elder.ref()} nodded and pointed to the long string. \"Watch it from here,\" {elder.pronoun()} said.")
        cat.meters["distance"] = 1
        whirl.meters["spin"] = 1
        propagate(world, narrate=True)
        world.say(f"{cat.ref()} stayed back, tugged the string, and watched the whirly toy dance without harm.")
        world.say(f"The mice settled down, and the attic felt safe again.")

    world.facts.update(cat=cat, elder=elder, mice=mice, whirly=whirl, setting=setting)
    return world


SETTINGS = {
    "attic": Setting(place="the attic", shadowy=True, affords={"whirly"}),
    "shed": Setting(place="the shed", shadowy=False, affords={"whirly"}),
}

WHIRLIES = {
    "toy": WhirlyThing(
        id="toy",
        label="a whirly toy",
        phrase="a whirly toy",
        type="toy",
        danger="wobbly",
        noise="whirr",
        zone={"floor", "ears"},
    ),
    "fan": WhirlyThing(
        id="fan",
        label="a whirly fan",
        phrase="a whirly fan",
        type="fan",
        danger="blowy",
        noise="whoosh",
        zone={"fur", "ears"},
    ),
}

CAT_NAMES = ["Pippin", "Milo", "Luna", "Toby", "Nori", "Clover"]
ELDER_NAMES = ["Mira", "Bram", "Sage", "Aster", "Moss"]


@dataclass
class StoryParams:
    setting: str
    whirly: str
    cat_name: str
    elder_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary adventure about a cat and a whirly thing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--whirly", choices=WHIRLIES)
    ap.add_argument("--name")
    ap.add_argument("--elder")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    whirly = args.whirly or rng.choice(list(WHIRLIES))
    return StoryParams(
        setting=setting,
        whirly=whirly,
        cat_name=args.name or rng.choice(CAT_NAMES),
        elder_name=args.elder or rng.choice(ELDER_NAMES),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cautionary adventure story for a small child about a cat named {f["cat"].label} and a whirly thing.',
        f"Tell a gentle but suspenseful story where {f['cat'].label} wants to chase {f['whirly'].phrase} but learns to be careful.",
        f"Write a short story that ends with {f['cat'].label} enjoying {f['whirly'].phrase} from a safe distance.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cat = f["cat"]
    elder = f["elder"]
    whirly = f["whirly"]
    return [
        QAItem(
            question=f"Who is the adventure about?",
            answer=f"It is about {cat.label}, a curious cat who finds {whirly.phrase} and learns to be careful."
        ),
        QAItem(
            question=f"What warning did {elder.label} give about {whirly.label}?",
            answer=f"{elder.label} warned that the whirly thing could cause trouble, so {cat.label} should watch it carefully."
        ),
        QAItem(
            question=f"How did {cat.label} enjoy the whirly thing at the end?",
            answer=f"{cat.label} used a long string and stayed at a safe distance, so the whirly thing could spin without hurting anyone."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does cautious mean?", answer="Cautious means being careful and thinking about danger before acting."),
        QAItem(question="What is a whirly thing?", answer="A whirly thing is something that spins around, often fast and noisily."),
        QAItem(question="Why should tiny animals be protected from big surprises?", answer="Tiny animals can get scared or hurt more easily, so gentle choices keep them safe."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {e.ref()} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], WHIRLIES[params.whirly], params.cat_name, params.elder_name)
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
% A whirly thing is risky when it spins and the cat wants to chase it.
risk(cat, W) :- spins(W), curious(cat), wants_chase(cat, W).

% Safe play happens when the cat keeps distance and uses a string to watch.
safe(cat, W) :- spins(W), safe_distance(cat), uses_string(cat).

% A cautionary adventure is valid when there is a risk and a safe resolution.
valid_story(S, W) :- setting(S), whirly(W), risk(cat, W), safe(cat, W).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for wid in WHIRLIES:
        lines.append(asp.fact("whirly", wid))
        lines.append(asp.fact("spins", wid))
    lines.append(asp.fact("curious", "cat"))
    lines.append(asp.fact("wants_chase", "cat", "toy"))
    lines.append(asp.fact("safe_distance", "cat"))
    lines.append(asp.fact("uses_string", "cat"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show risk/2. #show safe/2."))
    risk_atoms = set(asp.atoms(model, "risk"))
    safe_atoms = set(asp.atoms(model, "safe"))
    if ("cat", "toy") in risk_atoms and ("cat", "toy") in safe_atoms:
        print("OK: ASP sees both danger and resolution.")
        return 0
    print("MISMATCH: ASP twin did not produce expected atoms.")
    return 1


def valid_combos() -> list[tuple[str, str]]:
    return [(s, w) for s in SETTINGS for w in WHIRLIES]


CURATED = [
    StoryParams(setting="attic", whirly="toy", cat_name="Pippin", elder_name="Mira"),
    StoryParams(setting="shed", whirly="fan", cat_name="Luna", elder_name="Sage"),
]


def resolve_explicit(args: argparse.Namespace) -> None:
    if args.whirly and args.whirly not in WHIRLIES:
        raise StoryError("Unknown whirly choice.")
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting choice.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp_valid_stories()
        print(f"{len(models)} valid stories")
        for item in models:
            print(item)
        return

    resolve_explicit(args)
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
