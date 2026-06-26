#!/usr/bin/env python3
"""
storyworlds/worlds/flare_succotash_teamwork_dialogue_detective_story.py
=======================================================================

A small, constraint-checked detective-story world built around:
- flare
- succotash
- teamwork
- dialogue

Premise:
A young detective and a helper investigate why a bright flare and a pot of
succotash are both missing from a harbor snack stand.

World model:
- meters: physical state like clue strength, hidden items, served food
- memes: emotional/social state like curiosity, teamwork, relief, trust

The simulation drives a short mystery with:
- setup
- investigation through dialogue
- a turn where teamwork reveals the answer
- a resolution image proving what changed
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden: bool = False
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    mystery: str
    clue_noun: str
    clue_phrase: str
    verb: str
    search: str
    reveal: str
    target_room: str
    smoke_reason: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Evidence:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    protects: set[str] = field(default_factory=set)
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    helps: set[str]
    plural: bool = False


SETTINGS = {
    "harbor": Setting(place="the harbor snack stand", indoor=False, affords={"signal", "cook"}),
    "station": Setting(place="the little station kitchen", indoor=True, affords={"signal", "cook"}),
    "pier": Setting(place="the pier office", indoor=False, affords={"signal"}),
}

CASES = {
    "flare": Case(
        id="flare",
        mystery="the missing flare",
        clue_noun="flare",
        clue_phrase="a bright red flare",
        verb="search for the missing flare",
        search="look for the flare case",
        reveal="the flare was behind the lunch crate",
        target_room="crate corner",
        smoke_reason="the shiny flare had rolled and glinted under the crate",
        tags={"flare", "signal"},
    ),
    "succotash": Case(
        id="succotash",
        mystery="the missing succotash",
        clue_noun="succotash",
        clue_phrase="a warm pan of succotash",
        verb="search for the missing succotash",
        search="look for the spoon marks",
        reveal="the succotash was in the warmer",
        target_room="warming shelf",
        smoke_reason="the pot had been moved to keep it from getting cold",
        tags={"succotash", "cook"},
    ),
}

EVIDENCE = {
    "flare_case": Evidence(
        id="flare_case",
        label="a dented tin case",
        phrase="a dented tin case with a red mark",
        region="table",
        protects={"signal"},
        genders={"girl", "boy"},
    ),
    "stir_spoon": Evidence(
        id="stir_spoon",
        label="a wooden spoon",
        phrase="a wooden spoon with corn on it",
        region="kitchen",
        protects={"cook"},
    ),
}

GEAR = {
    "notebook": Gear(
        id="notebook",
        label="a small notebook",
        phrase="a small notebook for clues",
        helps={"investigate"},
    ),
    "flashlight": Gear(
        id="flashlight",
        label="a flashlight",
        phrase="a flashlight with a round beam",
        helps={"signal", "investigate"},
    ),
}

HERO_NAMES = ["Mina", "Theo", "Nora", "Pip", "Iris", "Jude", "Lena", "Max"]
HELPER_NAMES = ["Sol", "Bea", "Kit", "Rowan", "Tess", "Finn", "June", "Ari"]
TRAITS = ["curious", "careful", "brave", "patient", "quick-thinking", "gentle"]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes["teamwork"] < THRESHOLD or helper.memes["teamwork"] < THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["trust"] += 1
    helper.memes["trust"] += 1
    out.append("They worked side by side, and their teamwork made both of them steadier.")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    case = world.facts["case"]
    clue = world.get("clue")
    if hero.meters["searched"] < THRESHOLD or clue.hidden:
        return out
    sig = ("clue", case.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.hidden = False
    hero.meters["clues"] += 1
    out.append(f"A clue turned up: {case.smoke_reason}.")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    case = world.facts["case"]
    if hero.meters["clues"] < THRESHOLD or helper.meters["clues"] < THRESHOLD:
        return out
    sig = ("reveal", case.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["solved"] = True
    out.append(f"Together they figured it out: {case.reveal}.")
    return out


CAUSAL_RULES = [
    Rule("teamwork", _r_teamwork),
    Rule("clue", _r_clue),
    Rule("reveal", _r_reveal),
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


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, case: Case) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} little detective who loved {case.mystery}."
    )
    world.say(
        f"{helper.id} stayed close, because good detectives liked teamwork and careful dialogue."
    )


def setup(world: World, hero: Entity, helper: Entity, case: Case) -> None:
    world.say(
        f"At {world.setting.place}, someone had lost {case.clue_phrase}, and the stand felt too quiet."
    )
    world.say(
        f"{hero.id} opened {world.get('notebook').label} and asked, \"What was here before the clue went missing?\""
    )
    helper.memes["teamwork"] += 1
    hero.memes["teamwork"] += 1


def question(world: World, speaker: Entity, listener: Entity, text: str) -> None:
    world.say(f'"{text}" {speaker.id} asked.')
    world.say(f'"{listener.id}," {listener.pronoun()} said, "let us check the corners together."')


def search_scene(world: World, hero: Entity, helper: Entity, case: Case) -> None:
    world.say(
        f"{hero.id} and {helper.id} moved from table to shelf, peeking under boxes and behind cups."
    )
    hero.meters["searched"] += 1
    helper.meters["searched"] += 1
    propagate(world, narrate=True)


def inspect_clue(world: World, hero: Entity, helper: Entity, case: Case) -> None:
    clue = world.get("clue")
    world.say(
        f'{helper.id} pointed at {clue.label}. "{case.search}," {helper.id} said.'
    )
    world.say(
        f'"Good eye," {hero.id} said. "{case.verb} means we need both clues and teamwork."'
    )
    hero.meters["clues"] += 1
    helper.meters["clues"] += 1
    propagate(world, narrate=True)


def reveal_and_restore(world: World, hero: Entity, helper: Entity, case: Case) -> None:
    if not world.facts.get("solved"):
        return
    world.say(
        f'{hero.id} smiled. "{case.reveal}," {hero.id} said, and {helper.id} laughed in relief.'
    )
    world.say(
        f"They brought the {case.clue_noun} back, and the snack stand finally looked ready again."
    )
    if case.id == "succotash":
        world.say("Soon the warm succotash was back on the counter, steamy and safe.")
    else:
        world.say("Soon the bright flare sat where it belonged, neat in its tin case.")


def finish_image(world: World, hero: Entity, helper: Entity, case: Case) -> None:
    if case.id == "flare":
        world.say(
            f'By the end, {hero.id} had the flare in hand, {helper.id} had the notebook, and the harbor was calm.'
        )
    else:
        world.say(
            f'By the end, {hero.id} and {helper.id} stood beside the warm succotash, proud of their neat little mystery.'
        )


def tell(setting: Setting, case: Case, hero_name: str, helper_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl" if hero_name in {"Mina", "Nora", "Iris", "Lena"} else "boy", traits=[trait, "detective"]))
    helper = world.add(Entity(id=helper_name, kind="character", type="girl" if helper_name in {"Bea", "Tess", "June"} else "boy", traits=["helpful", "steady"]))
    world.add(Entity(id="notebook", type="thing", label="a small notebook"))
    world.add(Entity(id="clue", type="thing", label=case.clue_phrase, hidden=True))

    world.facts.update(hero=hero, helper=helper, case=case)

    introduce(world, hero, helper, case)
    world.para()
    setup(world, hero, helper, case)
    question(world, hero, helper, f"Who moved {case.clue_noun}?")
    search_scene(world, hero, helper, case)
    world.para()
    inspect_clue(world, hero, helper, case)
    reveal_and_restore(world, hero, helper, case)
    finish_image(world, hero, helper, case)
    return world


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    case: str
    hero: str
    helper: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="harbor", case="flare", hero="Mina", helper="Sol", trait="curious"),
    StoryParams(place="station", case="succotash", hero="Nora", helper="Bea", trait="careful"),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: Case = f["case"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    return [
        f'Write a short detective story for young children about {case.mystery} at {world.setting.place}.',
        f'Tell a teamwork story where {hero.id} and {helper.id} use dialogue to solve a mystery involving {case.clue_noun}.',
        f'Create a gentle mystery story that includes the words "{case.clue_noun}" and "teamwork".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = f["case"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    qa = [
        QAItem(
            question=f"What was missing at {world.setting.place}?",
            answer=f"{case.clue_phrase} was missing, so {hero.id} and {helper.id} went to investigate together.",
        ),
        QAItem(
            question=f"Who solved the mystery by working together?",
            answer=f"{hero.id} and {helper.id} solved it by using teamwork and careful dialogue.",
        ),
        QAItem(
            question=f"What did they find at the end?",
            answer=case.reveal + ".",
        ),
    ]
    if world.facts.get("solved"):
        qa.append(
            QAItem(
                question=f"Why did their teamwork matter?",
                answer=f"The teamwork helped {hero.id} and {helper.id} notice the clue and understand where {case.clue_noun} had gone.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = f["case"]
    if case.id == "flare":
        return [
            QAItem(
                question="What is a flare for?",
                answer="A flare is used to make a bright signal that people can see from far away.",
            ),
            QAItem(
                question="Why might a flare be kept in a case?",
                answer="A flare is often kept in a case so it stays safe, dry, and ready when needed.",
            ),
        ]
    return [
        QAItem(
            question="What is succotash?",
            answer="Succotash is a warm dish made from corn and beans or other vegetables.",
        ),
        QAItem(
            question="Why is succotash best when it stays warm?",
            answer="Warm succotash tastes better and is ready to serve as a comforting meal.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A case is valid when the setting affords the case's action.
valid_case(S, C) :- setting(S), case(C), affords(S, C).

% A story is valid when the chosen setting can host the case.
valid_story(S, C) :- valid_case(S, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CASES.items():
        lines.append(asp.fact("case", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("tag", cid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_case/2."))
    return sorted(set(asp.atoms(model, "valid_case")))


def asp_verify() -> int:
    python_set = {(sid, cid) for sid, s in SETTINGS.items() for cid, c in CASES.items() if cid in s.affords}
    clingo_set = set(asp_valid_cases())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} valid cases).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Parser / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective-story world about flare, succotash, teamwork, and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    place = args.place or rng.choice(list(SETTINGS))
    case = args.case or rng.choice([c for c in CASES if c in SETTINGS[place].affords])
    if case not in SETTINGS[place].affords:
        raise StoryError(f"(No story: {SETTINGS[place].place} cannot host the {case} mystery.)")
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([h for h in HELPER_NAMES if h != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, case=case, hero=hero, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CASES[params.case], params.hero, params.helper, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_case/2.\n#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_case/2."))
        vals = sorted(set(asp.atoms(model, "valid_case")))
        print(f"{len(vals)} valid cases:")
        for sid, cid in vals:
            print(f"  {sid}: {cid}")
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
            header = f"### {p.hero} and {p.helper}: {p.case} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
