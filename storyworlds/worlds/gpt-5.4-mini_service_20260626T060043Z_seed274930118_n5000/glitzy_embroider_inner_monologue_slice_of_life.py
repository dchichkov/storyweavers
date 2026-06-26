#!/usr/bin/env python3
"""
A tiny slice-of-life storyworld about a glitzy embroidery project.

Premise:
- A child or young teen wants to embroider something glitzy for an ordinary day.
- The project may be a little too fancy for the setting or moment.
- A helper suggests a practical compromise: choose a calmer thread, a smaller pattern,
  or a fabric backing so the glittery work still feels special without becoming fussy.

The world model tracks:
- physical meters: neatness, sparkle, progress, fray, confidence
- emotional memes: excitement, worry, pride, relief, patience

The story is driven by a forward simulation:
- the maker chooses a design
- glittery materials create sparkle but also a little chaos
- mistakes raise worry and slow progress
- inner monologue turns the conflict into a reflective, child-facing slice-of-life story
- a small adjustment resolves the scene and leaves a finished object behind
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING_REGISTRY = {
    "kitchen_table": {
        "label": "the kitchen table",
        "details": "The table was warm from lunch and a little crowded with a mug, a napkin, and a folded cloth.",
        "affords": {"embroider"},
    },
    "sunroom": {
        "label": "the sunroom",
        "details": "Sunlight spilled across the floor, and the window made everything look calm and bright.",
        "affords": {"embroider"},
    },
    "bedroom_desk": {
        "label": "the bedroom desk",
        "details": "The desk was tidy except for a spool of thread, a small hoop, and a pencil cup.",
        "affords": {"embroider"},
    },
}

PROJECT_REGISTRY = {
    "pouch": {
        "label": "a little pouch",
        "material": "canvas",
        "surface": "front",
        "risk": "frayed edges",
        "finish": "a tiny pouch that could hold coins or buttons",
        "zone": {"surface"},
        "sparkle": "glitzy",
        "keyword": "glitzy",
    },
    "handkerchief": {
        "label": "a handkerchief",
        "material": "cotton",
        "surface": "corner",
        "risk": "loose stitches",
        "finish": "a soft handkerchief with one bright corner",
        "zone": {"surface"},
        "sparkle": "glitzy",
        "keyword": "glitzy",
    },
    "bookmark": {
        "label": "a bookmark",
        "material": "felt",
        "surface": "edge",
        "risk": "crooked thread",
        "finish": "a bookmark with a neat shiny vine",
        "zone": {"surface"},
        "sparkle": "glitzy",
        "keyword": "glitzy",
    },
}

THREAD_REGISTRY = {
    "gold": {
        "label": "gold thread",
        "spark": 2,
        "mess": 1,
        "guards": {"gentle"},
        "reason": "It shines a lot, but it can make the maker extra careful.",
    },
    "silver": {
        "label": "silver thread",
        "spark": 2,
        "mess": 1,
        "guards": {"gentle"},
        "reason": "It gives the work a bright look without needing a huge pattern.",
    },
    "blue": {
        "label": "blue thread",
        "spark": 0,
        "mess": 0,
        "guards": {"steady"},
        "reason": "It is calmer and helps keep the stitches easy to follow.",
    },
    "pink": {
        "label": "pink thread",
        "spark": 1,
        "mess": 0,
        "guards": {"steady"},
        "reason": "It feels cheerful and still lets the maker focus on neat rows.",
    },
}

PATTERN_REGISTRY = {
    "stars": {
        "label": "little stars",
        "complexity": 2,
        "shine": 2,
        "requires": {"sparkly"},
        "line": "tiny stars are easy to love but a little tricky to place evenly",
    },
    "flowers": {
        "label": "small flowers",
        "complexity": 1,
        "shine": 1,
        "requires": {"gentle"},
        "line": "small flowers look sweet and give the needle an easy path",
    },
    "waves": {
        "label": "curving waves",
        "complexity": 1,
        "shine": 1,
        "requires": {"steady"},
        "line": "curving waves are calm enough to stitch one bend at a time",
    },
}

HELPER_REGISTRY = {
    "mother": {
        "label": "Mom",
        "verb": "showed",
        "offer": "a steadier pattern",
        "offer_detail": "Let's choose the part that feels lovely and not too busy.",
    },
    "father": {
        "label": "Dad",
        "verb": "pointed to",
        "offer": "a backing cloth",
        "offer_detail": "A backing cloth can help the stitches sit neatly while you work.",
    },
    "grandparent": {
        "label": "Grandma",
        "verb": "found",
        "offer": "a calmer thread",
        "offer_detail": "Sometimes a calmer thread makes the whole piece feel easier.",
    },
}

CHARACTER_NAMES = {
    "girl": ["Mia", "Lina", "June", "Nora", "Tessa", "Ivy"],
    "boy": ["Eli", "Noah", "Theo", "Finn", "Milo", "Owen"],
}

TRAITS = ["quiet", "curious", "careful", "dreamy", "patient", "shy"]


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    setting: str
    project: str
    thread: str
    pattern: str
    helper: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def _add_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def project_label(params: StoryParams) -> str:
    return PROJECT_REGISTRY[params.project]["label"]


def resolve_relevance(params: StoryParams) -> bool:
    return params.pattern in PATTERN_REGISTRY and params.thread in THREAD_REGISTRY


def predict_fuss(thread_id: str, pattern_id: str) -> bool:
    thread = THREAD_REGISTRY[thread_id]
    pattern = PATTERN_REGISTRY[pattern_id]
    return thread["spark"] + pattern["complexity"] >= 3


def tell(params: StoryParams) -> World:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError("Unknown setting.")
    if params.project not in PROJECT_REGISTRY:
        raise StoryError("Unknown project.")
    if params.thread not in THREAD_REGISTRY:
        raise StoryError("Unknown thread.")
    if params.pattern not in PATTERN_REGISTRY:
        raise StoryError("Unknown pattern.")
    if params.helper not in HELPER_REGISTRY:
        raise StoryError("Unknown helper.")
    if not resolve_relevance(params):
        raise StoryError("The chosen thread and pattern do not make a believable embroidery project.")

    world = World(setting=params.setting)
    maker = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"neatness": 1.0, "progress": 0.0, "fray": 0.0},
        memes={"excitement": 1.0, "worry": 0.0, "pride": 0.0, "relief": 0.0, "patience": 0.0},
    ))
    helper_cfg = HELPER_REGISTRY[params.helper]
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=helper_cfg["label"],
        meters={"calm": 1.0},
        memes={"patience": 1.0},
    ))
    project = world.add(Entity(
        id="project",
        type=params.project,
        label=project_label(params),
        owner=maker.id,
        caretaker=maker.id,
        meters={"sparkle": 0.0, "progress": 0.0, "fray": 0.0, "neatness": 1.0},
    ))

    thread = THREAD_REGISTRY[params.thread]
    pattern = PATTERN_REGISTRY[params.pattern]
    setting = SETTING_REGISTRY[params.setting]

    world.say(f"{maker.id} sat at {setting['label']} with {project.label} in front of {maker.pronoun('object')}.")
    world.say(setting["details"])
    world.say(f"In {maker.pronoun('possessive')} head, {maker.id} thought, 'I want this to look {thread['label'].split()[0]} and {params.pattern} pretty.'")
    _add_meme(maker, "excitement", 1.0)
    _add_meter(project, "sparkle", float(thread["spark"]))
    _add_meter(project, "progress", 0.5)
    _add_meter(project, "neatness", 0.2)

    world.para()
    world.say(f"{maker.id} picked up {thread['label']} and started {pattern['label']}.")
    world.say(f"{pattern['line'].capitalize()}.")
    if predict_fuss(params.thread, params.pattern):
        _add_meme(maker, "worry", 1.0)
        _add_meter(maker, "fray", 1.0)
        _add_meter(project, "fray", 1.0)
        world.say(f"In {maker.pronoun('possessive')} mind, {maker.id} worried, 'This is a little too shiny and busy; I might mess up the corners.'")
        world.say(f"The first few stitches looked glitzy, but a tiny tangle made the thread catch.")
    else:
        world.say(f"In {maker.pronoun('possessive')} mind, {maker.id} thought, 'This feels okay; I can do one small stitch at a time.'")

    world.para()
    world.say(f"{helper_cfg['label']} {helper_cfg['verb']} the half-finished work and smiled.")
    world.say(f"'{helper_cfg['offer_detail']}'")

    if params.thread in {"gold", "silver"} and params.pattern == "stars":
        _add_meme(helper, "patience", 1.0)
        _add_meme(maker, "worry", 0.5)
        world.say(f"{maker.id} listened and thought, 'Maybe I do not need all the sparkle at once.'")
        world.say(f"{maker.id} switched to a slower rhythm, one tiny shape after another.")
        _add_meme(maker, "patience", 1.0)
        _add_meter(project, "progress", 1.0)
        _add_meter(project, "neatness", 0.8)
        _add_meter(project, "fray", -0.5)
        if params.helper == "grandparent":
            world.say(f"In {maker.pronoun('possessive')} head, {maker.id} felt grateful for the calmer advice.")
        else:
            world.say(f"In {maker.pronoun('possessive')} head, {maker.id} felt better because the work had a plan.")
    else:
        world.say(f"{maker.id} thought, 'A steadier choice might make this easier.'")
        _add_meme(maker, "patience", 1.0)
        _add_meter(project, "progress", 1.0)
        _add_meter(project, "neatness", 0.6)

    world.para()
    _add_meter(project, "sparkle", 1.0)
    _add_meter(project, "progress", 1.0)
    _add_meter(project, "neatness", 0.7)
    _add_meme(maker, "pride", 1.0)
    _add_meme(maker, "relief", 1.0)
    world.say(f"By the end, the embroidery looked finished enough to hold in both hands.")
    world.say(f"It was {thread['label']} in the best way, with {pattern['label']} that stayed neat instead of wobbly.")
    world.say(f"{maker.id} thought, 'That looks like mine.'")
    world.say(f"{maker.id} smiled at the little {project.label} and felt proud that the glitzy idea had become something real.")

    world.facts.update(
        maker=maker,
        helper=helper,
        project=project,
        thread=params.thread,
        pattern=params.pattern,
        setting=params.setting,
        helper_kind=params.helper,
        thread_label=thread["label"],
        pattern_label=pattern["label"],
        sparkle=project.meters.get("sparkle", 0.0),
        worry=maker.memes.get("worry", 0.0),
        resolved=True,
        used_glitzy=(params.thread in {"gold", "silver"} or params.pattern == "stars"),
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle slice-of-life story about {f['maker'].id} trying to embroider something {f['thread_label']} at {SETTING_REGISTRY[f['setting']]['label']}.",
        f"Tell a story with inner monologue where {f['maker'].id} starts a {f['pattern_label']} embroidery project and then chooses a calmer way to finish it.",
        f"Write a short child-friendly story about a glitzy embroidery project that becomes neat after a small change.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    maker: Entity = f["maker"]
    helper: Entity = f["helper"]
    project: Entity = f["project"]
    setting = SETTING_REGISTRY[f["setting"]]["label"]
    thread = THREAD_REGISTRY[f["thread"]]["label"]
    pattern = PATTERN_REGISTRY[f["pattern"]]["label"]
    helper_label = HELPER_REGISTRY[f["helper_kind"]]["label"]

    return [
        QAItem(
            question=f"Where was {maker.id} working on {project.label}?",
            answer=f"{maker.id} was working on {project.label} at {setting}.",
        ),
        QAItem(
            question=f"What kind of thread did {maker.id} first want to use?",
            answer=f"{maker.id} wanted to use {thread}, because {maker.pronoun('possessive')} idea felt glitzy and special.",
        ),
        QAItem(
            question=f"What pattern was {maker.id} trying to stitch?",
            answer=f"{maker.id} was trying to stitch {pattern}.",
        ),
        QAItem(
            question=f"Who helped {maker.id} finish the project?",
            answer=f"{helper_label} helped {maker.id} by suggesting a calmer, neater way to keep going.",
        ),
        QAItem(
            question=f"How did {maker.id} feel at the end?",
            answer=f"{maker.id} felt proud and relieved because the embroidery looked finished and stayed neat.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "glitzy": (
        "What does glitzy mean?",
        "Glitzy means shiny, flashy, or fancy-looking in a way that catches your eye.",
    ),
    "embroider": (
        "What is embroidery?",
        "Embroidery is decorating cloth by sewing patterns with a needle and thread.",
    ),
    "thread": (
        "Why do people use thread when sewing?",
        "People use thread to join pieces together or make stitched pictures and patterns on fabric.",
    ),
    "pattern": (
        "What is a pattern in sewing?",
        "A pattern is a design or shape that can be repeated, like stars, flowers, or waves.",
    ),
}


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = []
    out.append(QAItem(*WORLD_KNOWLEDGE["glitzy"]))
    out.append(QAItem(*WORLD_KNOWLEDGE["embroider"]))
    out.append(QAItem(*WORLD_KNOWLEDGE["thread"]))
    out.append(QAItem(*WORLD_KNOWLEDGE["pattern"]))
    if f.get("used_glitzy"):
        out.append(QAItem(
            question="Why can a glitzy embroidery project be a little tricky?",
            answer="A glitzy embroidery project can be tricky because shiny thread and busy shapes can make it harder to keep the stitches neat.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/4.

valid(Setting, Project, Thread, Pattern) :-
    afford(Setting, embroider),
    thread(Thread),
    project(Project),
    pattern(Pattern),
    thread_shiny(Thread, Shine),
    pattern_complexity(Pattern, Complexity),
    Shine + Complexity >= 2.

glitzy_combo(Setting, Project, Thread, Pattern) :-
    valid(Setting, Project, Thread, Pattern),
    thread_shiny(Thread, Shine),
    Shine >= 1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTING_REGISTRY.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s["affords"]):
            lines.append(asp.fact("afford", sid, a))
    for pid, p in PROJECT_REGISTRY.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("project_label", pid, p["label"]))
    for tid, t in THREAD_REGISTRY.items():
        lines.append(asp.fact("thread", tid))
        lines.append(asp.fact("thread_shiny", tid, t["spark"]))
    for patid, pat in PATTERN_REGISTRY.items():
        lines.append(asp.fact("pattern", patid))
        lines.append(asp.fact("pattern_complexity", patid, pat["complexity"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s in SETTING_REGISTRY:
        for p in PROJECT_REGISTRY:
            for t in THREAD_REGISTRY:
                for pat in PATTERN_REGISTRY:
                    if SETTING_REGISTRY[s]["affords"] and THREAD_REGISTRY[t]["spark"] + PATTERN_REGISTRY[pat]["complexity"] >= 2:
                        out.append((s, p, t, pat))
    return out


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Resolution, generation, CLI
# ---------------------------------------------------------------------------

@dataclass
class ChoicePack:
    setting: str
    project: str
    thread: str
    pattern: str
    helper: str


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life embroidery storyworld with inner monologue.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY.keys())
    ap.add_argument("--project", choices=PROJECT_REGISTRY.keys())
    ap.add_argument("--thread", choices=THREAD_REGISTRY.keys())
    ap.add_argument("--pattern", choices=PATTERN_REGISTRY.keys())
    ap.add_argument("--helper", choices=HELPER_REGISTRY.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    project = args.project or rng.choice(list(PROJECT_REGISTRY))
    thread = args.thread or rng.choice(list(THREAD_REGISTRY))
    pattern = args.pattern or rng.choice(list(PATTERN_REGISTRY))
    helper = args.helper or rng.choice(list(HELPER_REGISTRY))

    if setting not in SETTING_REGISTRY:
        raise StoryError("Unknown setting.")
    if project not in PROJECT_REGISTRY:
        raise StoryError("Unknown project.")
    if thread not in THREAD_REGISTRY:
        raise StoryError("Unknown thread.")
    if pattern not in PATTERN_REGISTRY:
        raise StoryError("Unknown pattern.")
    if helper not in HELPER_REGISTRY:
        raise StoryError("Unknown helper.")

    if THREAD_REGISTRY[thread]["spark"] + PATTERN_REGISTRY[pattern]["complexity"] < 2:
        raise StoryError("That thread and pattern do not make a believable glitzy embroidery scene.")

    gender = args.gender or rng.choice(["girl", "boy"])
    if gender not in CHARACTER_NAMES:
        raise StoryError("Unknown gender.")
    name = args.name or rng.choice(CHARACTER_NAMES[gender])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, project=project, thread=thread, pattern=pattern, helper=helper, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        lines.append(f"  {e.id:8} ({e.kind:9}) {e.type:12} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen_table", "pouch", "gold", "stars", "mother", "Mia", "girl", "curious"),
    StoryParams("sunroom", "bookmark", "silver", "waves", "grandparent", "Theo", "boy", "careful"),
    StoryParams("bedroom_desk", "handkerchief", "pink", "flowers", "father", "Nora", "girl", "quiet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.thread} / {p.pattern} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
