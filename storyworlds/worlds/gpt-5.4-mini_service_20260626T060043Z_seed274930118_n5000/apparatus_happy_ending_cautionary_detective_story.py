#!/usr/bin/env python3
"""
A tiny storyworld for a cautionary detective tale with a happy ending.

Premise:
- A young detective notices that an apparatus in a small setting has gone wrong.
- Careless use of the apparatus creates a problem.
- Careful observation, a clue trail, and a sensible fix restore order.
- The ending is reassuring: the problem is solved, and the apparatus is safe to use.

This world is intentionally small and constraint-checked so the generated
stories stay coherent and child-facing.
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
# Core entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    broken: bool = False
    clean: bool = True
    safe: bool = True
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    indoors: bool
    noise: str


@dataclass
class Apparatus:
    id: str
    label: str
    phrase: str
    function: str
    clue: str
    risk: str
    fix: str
    is_delicate: bool = True
    uses: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    apparatus: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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
        w.events = list(self.events)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "workshop": Setting(place="the workshop", indoors=True, noise="a soft hum"),
    "attic": Setting(place="the attic", indoors=True, noise="a squeaky floorboard"),
    "garden_shed": Setting(place="the garden shed", indoors=False, noise="the wind tapping at the door"),
}

APPARATUSES = {
    "kite_launcher": Apparatus(
        id="kite_launcher",
        label="kite launcher",
        phrase="a small kite launcher with a red lever",
        function="lift a kite into the air",
        clue="a bent string near the lever",
        risk="it could snap the string and send the kite sideways",
        fix="straighten the string and reset the lever",
        uses={"string", "lever", "wind"},
    ),
    "cookie_press": Apparatus(
        id="cookie_press",
        label="cookie press",
        phrase="a shiny cookie press with a round handle",
        function="shape dough into neat cookies",
        clue="sticky dough on the handle",
        risk="it could jam and squish the dough into a blob",
        fix="wash the handle and clear the jam",
        uses={"dough", "handle", "cookie"},
    ),
    "lantern_organizer": Apparatus(
        id="lantern_organizer",
        label="lantern organizer",
        phrase="a little lantern organizer with three hooks",
        function="keep lanterns steady and in order",
        clue="a hook hanging crooked",
        risk="it could let a lantern swing loose",
        fix="tighten the hook and hang the lantern back up",
        uses={"hook", "lantern", "steady"},
    ),
}

DETECTIVE_NAMES = ["Mina", "Noah", "Ivy", "Leo", "Zara", "Ben", "Nia", "Theo"]
HELPER_NAMES = ["Pip", "June", "Milo", "Rose", "Tess", "Ollie"]
KINDS = ["girl", "boy"]


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for a in APPARATUSES:
            combos.append((s, a))
    return combos


def explain_invalid(setting: str, apparatus: str) -> str:
    return f"(No story: the {apparatus} does not fit the {setting} case in a sensible detective tale.)"


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def investigate(world: World, detective: Entity, helper: Entity, app: Apparatus) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    helper.memes["concern"] = helper.memes.get("concern", 0) + 1
    world.say(
        f"{detective.id} was a little {detective.type} detective who liked noticing tiny clues."
    )
    world.say(
        f"{detective.pronoun().capitalize()} and {helper.id} were looking after {app.phrase}."
    )
    world.say(
        f"It helped {app.function}, but today something felt wrong: {app.risk}."
    )


def notice_clue(world: World, detective: Entity, app: Apparatus) -> None:
    detective.memes["focus"] = detective.memes.get("focus", 0) + 1
    world.say(
        f"Then {detective.id} spotted {app.clue}."
    )
    world.say(
        f"That clue made {detective.pronoun('object')} look closer instead of rushing ahead."
    )


def caution(world: World, helper: Entity, app: Apparatus) -> None:
    helper.memes["worry"] = helper.memes.get("worry", 0) + 1
    world.say(
        f'"Careful," {helper.id} said. "If we are rough with it, {app.risk}."'
    )


def solve(world: World, detective: Entity, helper: Entity, app: Apparatus) -> None:
    detective.memes["confidence"] = detective.memes.get("confidence", 0) + 1
    app_state = world.get(app.id)
    app_state.broken = False
    app_state.safe = True
    app_state.clean = True
    world.facts["fixed"] = True
    world.say(
        f"{detective.id} smiled and showed {helper.id} the best fix: {app.fix}."
    )
    world.say(
        f"They did it together, and soon the {app.label} worked again."
    )
    world.say(
        f"In the end, {app.label} was safe, tidy, and ready for the next careful use."
    )


def tell(setting: Setting, app: Apparatus, detective_name: str, detective_type: str,
         helper_name: str, helper_type: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    apparatus = world.add(Entity(
        id=app.id,
        type=app.id,
        label=app.label,
        phrase=app.phrase,
        caretaker=helper.id,
        clean=False,
        safe=False,
        broken=True,
    ))

    world.facts.update(setting=setting, apparatus=app, detective=detective, helper=helper)

    world.say(
        f"One day in {setting.place}, there was {setting.noise} and a curious mystery."
    )
    world.say(
        f"{detective.id} and {helper.id} stood beside {apparatus.phrase}."
    )

    world.para()
    investigate(world, detective, helper, app)

    world.para()
    caution(world, helper, app)
    notice_clue(world, detective, app)

    world.para()
    solve(world, detective, helper, app)

    return world


# ---------------------------------------------------------------------------
# Narrative registries
# ---------------------------------------------------------------------------
@dataclass
class StoryWorld:
    pass


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting: Setting = f["setting"]  # type: ignore[assignment]
    app: Apparatus = f["apparatus"]  # type: ignore[assignment]
    detective: Entity = f["detective"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    return [
        f'Write a short detective story for children set in {setting.place} about {detective.id} and {helper.id}, featuring an apparatus.',
        f"Tell a cautious but happy mystery where {detective.id} finds the clue that fixes the {app.label}.",
        f"Write a story with a small problem, a careful clue, and a cheerful ending involving {app.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting: Setting = f["setting"]  # type: ignore[assignment]
    app: Apparatus = f["apparatus"]  # type: ignore[assignment]
    detective: Entity = f["detective"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Who solved the mystery about the {app.label}?",
            answer=f"{detective.id} solved it with help from {helper.id}.",
        ),
        QAItem(
            question=f"What clue did {detective.id} notice near the {app.label}?",
            answer=f"{detective.id} noticed {app.clue}.",
        ),
        QAItem(
            question=f"What did the helper warn might happen to the {app.label}?",
            answer=f"{helper.id} warned that {app.risk}.",
        ),
        QAItem(
            question=f"How did the story end in {setting.place}?",
            answer=f"It ended happily, because the {app.label} was fixed and safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    app: Apparatus = f["apparatus"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What is an apparatus?",
            answer="An apparatus is a machine or device made from several parts that work together to do a job.",
        ),
        QAItem(
            question=f"Why should you be careful with a {app.label}?",
            answer=f"You should be careful because rough use could make it stop working well or cause a small accident.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A setting and an apparatus form a valid detective story when the apparatus
% is a sensible object for the child mystery domain.
valid_story(S, A) :- setting(S), apparatus(A).

% A clue-based happy ending happens when the apparatus has a fix and a risk.
has_caution(A) :- apparatus(A), risk(A, _).
has_happy_ending(A) :- apparatus(A), fix(A, _).
compatible_story(S, A) :- valid_story(S, A), has_caution(A), has_happy_ending(A).
#show compatible_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in APPARATUSES.items():
        lines.append(asp.fact("apparatus", aid))
        lines.append(asp.fact("risk", aid, a.risk))
        lines.append(asp.fact("fix", aid, a.fix))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/2."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if len(clingo_set) == len(python_set):
        print(f"OK: ASP and Python both accept {len(python_set)} story combos.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("ASP:", sorted(clingo_set))
    print("PY :", sorted(python_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly detective storyworld with an apparatus.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--apparatus", choices=APPARATUSES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=KINDS)
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
    if args.setting and args.apparatus and (args.setting, args.apparatus) not in valid_combos():
        raise StoryError(explain_invalid(args.setting, args.apparatus))
    setting = args.setting or rng.choice(list(SETTINGS))
    apparatus = args.apparatus or rng.choice(list(APPARATUSES))
    gender = args.gender or rng.choice(KINDS)
    detective_name = args.name or rng.choice(DETECTIVE_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    detective_type = gender
    helper_type = "boy" if gender == "girl" else "girl"
    return StoryParams(
        setting=setting,
        apparatus=apparatus,
        detective_name=detective_name,
        detective_type=detective_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        APPARATUSES[params.apparatus],
        params.detective_name,
        params.detective_type,
        params.helper_name,
        params.helper_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.kind == "character":
            bits.append("character")
        if e.broken:
            bits.append("broken")
        if not e.clean:
            bits.append("dirty")
        if not e.safe:
            bits.append("unsafe")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
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


CURATED = [
    StoryParams(setting="workshop", apparatus="cookie_press", detective_name="Mina", detective_type="girl", helper_name="Pip", helper_type="boy"),
    StoryParams(setting="attic", apparatus="lantern_organizer", detective_name="Leo", detective_type="boy", helper_name="June", helper_type="girl"),
    StoryParams(setting="garden_shed", apparatus="kite_launcher", detective_name="Ivy", detective_type="girl", helper_name="Milo", helper_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for s, a in combos:
            print(f"{s} {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.detective_name}: {p.apparatus} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
