#!/usr/bin/env python3
"""
A small whodunit storyworld with a humorous, cautionary, surprise-shaped mystery.

Premise:
- A child notices a missing snack and a trail of clues.
- The world tracks physical clues ("meters") and emotions ("memes").
- The detective reasons about crumbs, crusted dishes, and who had access.
- The ending reveals the culprit and the fix, with a child-facing twist.

This world is intentionally small and constraint-driven:
- only a few suspects,
- only a few plausible motives,
- a single satisfying solution,
- and an ASP twin that mirrors the Python reasonableness gate.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    role: str = ""  # detective, helper, culprit, snack, clue
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the kitchen"
    morning: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    clue: str
    caution: str
    surprise: str
    culprit_kind: str
    culprit_label: str
    trail: str


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    has_access: bool
    likes: set[str] = field(default_factory=set)
    can_leave_trace: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", morning=True, affords={"snack_mystery"}),
    "pantry": Setting(place="the pantry", morning=False, affords={"snack_mystery"}),
}

MYSTERIES = {
    "pie": Mystery(
        id="pie",
        label="pie",
        phrase="a crusted little pie",
        clue="crusted",
        caution="careful",
        surprise="surprise",
        culprit_kind="cat",
        culprit_label="the orange cat",
        trail="crumbs",
    ),
    "cookie_tin": Mystery(
        id="cookie_tin",
        label="cookie tin",
        phrase="a round cookie tin",
        clue="crusted",
        caution="careful",
        surprise="surprise",
        culprit_kind="mouse",
        culprit_label="the tiny mouse",
        trail="crumbs",
    ),
    "tart": Mystery(
        id="tart",
        label="tart",
        phrase="a berry tart with a shiny crust",
        clue="crusted",
        caution="caution",
        surprise="surprise",
        culprit_kind="bird",
        culprit_label="the sneaky sparrow",
        trail="flakes",
    ),
}

SUSPECTS = {
    "cat": Suspect(id="cat", label="the orange cat", type="cat", has_access=True, likes={"snack"}),
    "mouse": Suspect(id="mouse", label="the tiny mouse", type="mouse", has_access=True, likes={"snack"}),
    "bird": Suspect(id="bird", label="the sneaky sparrow", type="bird", has_access=False, likes={"crumbs"}),
    "dad": Suspect(id="dad", label="Dad", type="father", has_access=True, likes={"tea"}),
}

NAMES = ["Mina", "Toby", "June", "Pia", "Owen", "Lena"]
TRAITS = ["curious", "brave", "careful", "funny", "sharp-eyed"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    child_name: str
    child_gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning / simulation
# ---------------------------------------------------------------------------

def clue_is_plausible(mystery: Mystery) -> bool:
    return mystery.clue == "crusted" and bool(mystery.trail)


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for setting_name, setting in SETTINGS.items():
        if "snack_mystery" not in setting.affords:
            continue
        for mid, mystery in MYSTERIES.items():
            if clue_is_plausible(mystery):
                out.append((setting_name, mid))
    return out


def select_suspect(mystery: Mystery) -> Suspect:
    suspect = SUSPECTS[mystery.culprit_kind]
    if not suspect.has_access:
        raise StoryError("The chosen culprit would not plausibly have access to the scene.")
    return suspect


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("No valid whodunit matches the given choices.")

    setting_name, mystery_id = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_name,
        mystery=mystery_id,
        child_name=child_name,
        child_gender=child_gender,
        trait=trait,
    )


# ---------------------------------------------------------------------------
# Storytelling
# ---------------------------------------------------------------------------

def child_pronouns(gender: str) -> dict[str, str]:
    return {
        "subject": "she" if gender == "girl" else "he",
        "object": "her" if gender == "girl" else "him",
        "possessive": "her" if gender == "girl" else "his",
    }


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    child = world.add(Entity(
        id="child",
        kind="character",
        type="girl" if params.child_gender == "girl" else "boy",
        label=params.child_name,
        role="detective",
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type="father",
        label="Dad",
        role="helper",
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=mystery.clue,
        phrase=f"a {mystery.clue}-dusty note",
        owner="adult",
    ))
    snack = world.add(Entity(
        id="snack",
        kind="thing",
        type="snack",
        label=mystery.label,
        phrase=mystery.phrase,
        caretaker="adult",
        owner="family",
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="character",
        type=mystery.culprit_kind,
        label=mystery.culprit_label,
        role="culprit",
    ))

    # physical evidence
    snack.meters["missing"] = 1
    clue.meters["crusted"] = 1
    culprit.meters["crumbs"] = 1

    # emotional evidence
    child.memes["curiosity"] = 1
    child.memes["suspicion"] = 1
    adult.memes["calm"] = 1

    world.facts.update(
        child=child,
        adult=adult,
        clue=clue,
        snack=snack,
        culprit=culprit,
        mystery=mystery,
        setting=setting,
        pronouns=child_pronouns(params.child_gender),
        trait=params.trait,
    )
    return world


def tell(world: World, params: StoryParams) -> None:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    clue: Entity = f["clue"]
    snack: Entity = f["snack"]
    culprit: Entity = f["culprit"]
    mystery: Mystery = f["mystery"]
    pron = f["pronouns"]
    trait = f["trait"]
    place = world.setting.place

    world.say(
        f"{params.child_name} was a {trait} little {child.type} who loved tidy mysteries."
    )
    world.say(
        f"One morning in {place}, {params.child_name} found that {snack.label} was gone."
    )
    world.say(
        f"On the counter sat a {clue.label} clue, all {mystery.clue}, like it had been wearing a tiny hat made of crumbs."
    )

    world.para()
    world.say(
        f"{pron['subject'].capitalize()} looked under the bowl, behind the jam jar, and beside the spoon."
    )
    world.say(
        f"That was the cautionary part: if a snack vanished quietly, somebody could get blamed before the facts were counted."
    )
    world.say(
        f"{params.child_name} did not guess right away. {pron['subject'].capitalize()} followed the {mystery.trail} trail instead."
    )

    world.para()
    world.say(
        f"The trail led to {culprit.label}, who had crumbs on {culprit.pronoun('possessive')} whiskers and a very innocent face."
    )
    world.say(
        f"{culprit.label} had only nibbled the crust, leaving the middle for later, which was funny in the way that made {params.child_name} snort."
    )
    world.say(
        f"Then came the surprise: the missing snack was not stolen at all. It was hidden in the warm oven because Dad had set it there 'just for a minute' and forgotten."
    )

    world.para()
    world.say(
        f"{params.child_name} laughed, because the real twist was that the cat had not been the villain."
    )
    world.say(
        f"Together they cooled the {snack.label}, wiped the {clue.label} trail, and put a note on the oven door so nobody would panic again."
    )
    world.say(
        f"By the end, {params.child_name} was still {trait}, the kitchen was calm, and the crusted clue had turned into a harmless joke."
    )

    # record outcome
    world.facts["solved"] = True
    world.facts["actual_culprit"] = culprit
    world.facts["red_herring"] = culprit.label


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    child: Entity = f["child"]
    return [
        f'Write a short whodunit for a child that includes the word "{mystery.clue}" and ends with a surprise.',
        f"Tell a humorous cautionary mystery about {child.label} in {world.setting.place} and a missing {mystery.label}.",
        f"Write a gentle detective story where the clue is {mystery.clue} and the answer is not the first suspicious suspect.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    snack: Entity = f["snack"]
    culprit: Entity = f["culprit"]
    mystery: Mystery = f["mystery"]
    pron = f["pronouns"]
    trait = f["trait"]

    return [
        QAItem(
            question=f"What did {child.label} notice was missing in {world.setting.place}?",
            answer=f"{child.label} noticed that {snack.label} was missing from {world.setting.place}.",
        ),
        QAItem(
            question=f"What clue helped {child.label} solve the mystery?",
            answer=f"The clue was a {mystery.clue} little mark that led to the real answer.",
        ),
        QAItem(
            question=f"Who looked suspicious at first?",
            answer=f"{culprit.label} looked suspicious because {culprit.pronoun('possessive')} whiskers had crumbs on them.",
        ),
        QAItem(
            question=f"Where was the snack really found?",
            answer=f"It was really found in the warm oven, where Dad had left it for a minute and forgotten it.",
        ),
        QAItem(
            question=f"How did the story end for {child.label}?",
            answer=f"{pron['subject'].capitalize()} laughed, fixed the mix-up, and ended the day still being {trait} and careful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are crumbs?",
            answer="Crumbs are tiny broken pieces of food, like bits of crust or cookie.",
        ),
        QAItem(
            question="Why should people check the oven before worrying?",
            answer="Because something can be warm or hidden there, and checking first can stop a false alarm.",
        ),
        QAItem(
            question="Why can a crust be a clue?",
            answer="A crust can leave little broken bits behind, and those bits can help a detective notice what happened.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is reasonable if it has a crusted clue and a visible trail.
reasonable_mystery(M) :- mystery(M), clue(M, crusted), trail(M, T), T != "".

% A suspect is plausible if they have access and can leave a trace.
plausible(C) :- suspect(C), access(C), trace(C).

% The culprit is the suspect whose kind matches the mystery's culprit_kind.
culprit(C, M) :- reasonable_mystery(M), culprit_kind(M, K), suspect(C), kind(C, K), plausible(C).

% The story is valid if exactly one culprit is identified for the chosen mystery.
valid_story(S, M) :- setting(S), mystery(M), reasonable_mystery(M), culprit(_, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("trail", mid, m.trail))
        lines.append(asp.fact("culprit_kind", mid, m.culprit_kind))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("kind", sid, s.type))
        if s.has_access:
            lines.append(asp.fact("access", sid))
        if s.can_leave_trace:
            lines.append(asp.fact("trace", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("Python-only:", sorted(py - asp_set))
    print("ASP-only:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small humorous cautionary whodunit world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    lines = ["--- world trace ---"]
    for eid, e in world.entities.items():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {eid}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen", mystery="pie", child_name="Mina", child_gender="girl", trait="curious"),
    StoryParams(setting="pantry", mystery="cookie_tin", child_name="Owen", child_gender="boy", trait="funny"),
    StoryParams(setting="kitchen", mystery="tart", child_name="June", child_gender="girl", trait="careful"),
]


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

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
            except StoryError as e:
                print(e)
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
            header = f"### {p.name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("No valid mystery matches the given options.")

    setting_name, mystery_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_name,
        mystery=mystery_id,
        child_name=name,
        child_gender=gender,
        trait=trait,
    )


if __name__ == "__main__":
    main()
