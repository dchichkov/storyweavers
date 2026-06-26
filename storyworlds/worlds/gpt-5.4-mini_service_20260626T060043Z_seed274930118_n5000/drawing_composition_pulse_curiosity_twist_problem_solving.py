#!/usr/bin/env python3
"""
storyworlds/worlds/drawing_composition_pulse_curiosity_twist_problem_solving.py
================================================================================

A small folk-tale story world about a child making a drawing, shaping its
composition, and learning how a picture can find its pulse through curiosity,
a twist, and a bit of problem solving.

Seed tale:
---
Once there was a little child named Mina who loved drawing more than anything.
One spring morning, Mina set out to make a picture for the village fair. Mina
wanted the composition to be grand, with hills, a river, and a bright little
house. But the page looked stiff and still, like a pond with no breeze upon it.

Mina grew curious and asked the old baker, the willow-mender, and the mill boy
what a picture needed to feel alive. Before long, a twist came: a gust of wind
tipped berry juice across the page. Mina nearly wept. Then the old willow-mender
smiled and said the stain could become a red fox racing through the meadow.

So Mina solved the problem by drawing around the blot instead of fighting it.
The fox gave the picture pulse, the hills seemed to breathe, and the village
folk praised Mina's brave little composition.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
    affordances: set[str] = field(default_factory=set)


@dataclass
class Material:
    id: str
    label: str
    hue: str
    stain: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CompositionNeed:
    id: str
    label: str
    scene: str
    risk: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    material: str
    need: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


SETTINGS = {
    "village_green": Setting("the village green", {"drawing"}),
    "bakery_corner": Setting("the bakery corner", {"drawing"}),
    "riverbank": Setting("the riverbank", {"drawing"}),
}

MATERIALS = {
    "charcoal": Material("charcoal", "charcoal", "black", "smudged", "quiet", {"dark", "drawing"}),
    "berry_ink": Material("berry_ink", "berry ink", "red", "stained", "bright", {"drawing", "red"}),
    "blue_dye": Material("blue_dye", "blue dye", "blue", "smeared", "cool", {"drawing", "blue"}),
    "gold_paint": Material("gold_paint", "gold paint", "gold", "spattered", "sparkly", {"drawing", "bright"}),
}

NEEDS = {
    "pulse": CompositionNeed(
        "pulse",
        "pulse",
        scene="something moving through the picture",
        risk="flat and still",
        fix="draw a fox, a bird, or a ribbon of wind",
        tags={"pulse", "twist"},
    ),
    "composition": CompositionNeed(
        "composition",
        "composition",
        scene="the way the pieces fit together",
        risk="crowded and lopsided",
        fix="move the house, the river, or the tree until it breathes",
        tags={"composition", "problem_solving"},
    ),
    "curiosity": CompositionNeed(
        "curiosity",
        "curiosity",
        scene="a reason to look and ask",
        risk="quiet and unfinished",
        fix="ask a helper what the page wants next",
        tags={"curiosity"},
    ),
}

HELPERS = {
    "baker": "the old baker",
    "willow_mender": "the willow-mender",
    "mill_boy": "the mill boy",
}

GIRL_NAMES = ["Mina", "Lina", "Tessa", "Anya", "Mira", "Pia"]
BOY_NAMES = ["Oren", "Bram", "Eli", "Jonah", "Rafi", "Timo"]
TRAITS = ["curious", "gentle", "brave", "patient", "lively", "clever"]


class Rule:
    def __init__(self, name: str, apply) -> None:
        self.name = name
        self.apply = apply


def _r_smudge(world: World) -> list[str]:
    out = []
    child = world.get("child")
    page = world.get("page")
    for mat in MATERIALS.values():
        if child.meters.get(mat.id, 0.0) < THRESHOLD:
            continue
        if page.meters.get("clean", 0.0) < THRESHOLD:
            continue
        sig = ("smudge", mat.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        page.meters["clean"] = 0.0
        page.meters["stained"] = 1.0
        out.append(f"A splash of {mat.label} touched the page.")
    return out


def _r_pulse(world: World) -> list[str]:
    out = []
    page = world.get("page")
    if page.meters.get("fox_added", 0.0) >= THRESHOLD and page.meters.get("pulse", 0.0) < THRESHOLD:
        sig = ("pulse",)
        if sig not in world.fired:
            world.fired.add(sig)
            page.meters["pulse"] = 1.0
            out.append("The fox gave the picture a lively pulse.")
    return out


def _r_balance(world: World) -> list[str]:
    out = []
    page = world.get("page")
    if page.meters.get("balanced", 0.0) >= THRESHOLD:
        return out
    if page.meters.get("pulse", 0.0) >= THRESHOLD and page.meters.get("stained", 0.0) >= THRESHOLD:
        sig = ("balance",)
        if sig not in world.fired:
            world.fired.add(sig)
            page.meters["balanced"] = 1.0
            out.append("The stain became part of the scene, and the whole composition settled.")
    return out


CAUSAL_RULES = [
    Rule("smudge", _r_smudge),
    Rule("pulse", _r_pulse),
    Rule("balance", _r_balance),
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


def reason_gate(setting: Setting, material: Material, need: CompositionNeed) -> bool:
    if "drawing" not in setting.affordances:
        return False
    return True


def tell(setting: Setting, material: Material, need: CompositionNeed, name: str,
         gender: str, helper: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity("child", kind="character", type=gender, label=name))
    page = world.add(Entity("page", type="paper", label="page", meters={"clean": 1.0, "pulse": 0.0}))
    mentor = world.add(Entity("mentor", kind="character", type="elder", label=HELPERS[helper]))
    child.memes["curiosity"] = 1.0

    world.say(f"{name} was a little {trait} {gender} who loved {material.label} and drawing.")
    world.say(
        f"One morning {name} sat at {setting.place} with a page and began a composition about "
        f"{need.scene}."
    )
    world.para()
    world.say(
        f"But the first drawing looked {need.risk}. {name} felt the itch of curiosity and went to ask "
        f"{mentor.label} what a picture needed to live."
    )
    child.memes["curiosity"] += 1.0
    world.say(
        f"{mentor.label} said, 'A good picture has a clear composition, and sometimes it needs a pulse.'"
    )
    world.para()
    world.say(
        f"Then came a twist: a gust of wind tipped {material.label} across the page."
    )
    child.meters[material.id] = 1.0
    propagate(world, narrate=True)
    world.say(
        f"{name} did not cry for long. {name} used {need.fix} and drew around the stain instead."
    )
    page.meters["fox_added"] = 1.0
    page.meters["balanced"] = 1.0
    propagate(world, narrate=True)
    world.say(
        f"At last the red shape became a fox racing through the meadow, and the composition found its pulse."
    )
    world.facts.update(
        child=child,
        page=page,
        mentor=mentor,
        material=material,
        need=need,
        setting=setting,
        helper=helper,
        trait=trait,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a child about {f["child"].label} making a drawing that learns its pulse.',
        f"Tell a gentle story where a {f['trait']} child asks for help with a {f['need'].label} and a {f['material'].label} twist.",
        f"Write a tiny tale about curiosity, a surprise stain, and problem solving in a drawing composition.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    mentor: Entity = f["mentor"]
    material: Material = f["material"]
    need: CompositionNeed = f["need"]
    return [
        QAItem(
            question=f"What was {child.label} making at {world.setting.place}?",
            answer=f"{child.label} was making a drawing with a careful composition."
        ),
        QAItem(
            question=f"Why did {child.label} go ask {mentor.label} for help?",
            answer=f"{child.label} was curious and wanted to know how the picture could feel alive instead of flat."
        ),
        QAItem(
            question=f"What surprise changed the drawing?",
            answer=f"A gust of wind tipped {material.label} across the page, and that twist gave {child.label} a problem to solve."
        ),
        QAItem(
            question=f"How did {child.label} solve the problem?",
            answer=f"{child.label} turned the stain into part of the picture by drawing around it, so the composition could keep its pulse."
        ),
        QAItem(
            question=f"What did the page become in the end?",
            answer=f"The page became a lively drawing with a fox racing through the meadow."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(
            question="What is a composition in a picture?",
            answer="A composition is the way the pieces of a picture are placed and balanced together."
        ),
        QAItem(
            question="What does pulse mean in a story about art?",
            answer="Here, pulse means a feeling of movement and life inside the picture."
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to ask questions and learn more about something."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a sudden turn that changes what is happening and makes the story interesting."
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means finding a way through a trouble instead of giving up."
        ),
    ]
    return out


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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:7} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("village_green", "berry_ink", "pulse", "Mina", "girl", "willow_mender", "curious"),
    StoryParams("bakery_corner", "blue_dye", "composition", "Oren", "boy", "baker", "clever"),
    StoryParams("riverbank", "gold_paint", "curiosity", "Tessa", "girl", "mill_boy", "brave"),
]


ASP_RULES = r"""
need_ok(S,N) :- setting(S), need(N).
valid_story(S,M,N) :- need_ok(S,N), material(M), afford_drawing(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("afford_drawing", sid) if a == "drawing" else asp.fact("affords", sid, a))
    for mid, m in MATERIALS.items():
        lines.append(asp.fact("material", mid))
    for nid, n in NEEDS.items():
        lines.append(asp.fact("need", nid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(s, m, n) for s in SETTINGS for m in MATERIALS for n in NEEDS if reason_gate(SETTINGS[s], MATERIALS[m], NEEDS[n])}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches reason gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    if clingo_set - python_set:
        print("only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale world: drawing, composition, pulse, curiosity, twist, problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list(HELPERS))
    ap.add_argument("--trait", choices=TRAITS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    material = args.material or rng.choice(list(MATERIALS))
    need = args.need or rng.choice(list(NEEDS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    trait = args.trait or rng.choice(TRAITS)
    if not reason_gate(SETTINGS[setting], MATERIALS[material], NEEDS[need]):
        raise StoryError("That combination cannot make a drawing story in this world.")
    return StoryParams(setting, material, need, name, gender, helper, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MATERIALS[params.material], NEEDS[params.need],
                 params.name, params.gender, params.helper, params.trait)
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
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for s, m, n in combos:
            print(f"  {s:14} {m:12} {n}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.need} with {p.material} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
