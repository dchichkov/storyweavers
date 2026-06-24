#!/usr/bin/env python3
"""
A detective-style story world about a small mystery:
a magic frankfurter, a sudden case of laryngitis, and a careful investigation.

The world is intentionally tiny and classical:
- one child detective
- one worried helper
- one magical snack with a real consequence
- one conflict that is resolved by methodical clue-finding

The story text is simulated from state updates rather than a frozen template.
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
# World data
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "lady"}
        male = {"boy", "father", "dad", "man", "gentleman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    title: str
    clue: str
    cause: str
    effect: str
    remedy: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    use: str
    helps: set[str]


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "diner": Setting(place="the little diner", mood="noisy", affords={"investigate", "question", "serve"}),
    "fair": Setting(place="the night fair", mood="bright", affords={"investigate", "question", "search"}),
    "kitchen": Setting(place="the back kitchen", mood="warm", affords={"investigate", "search", "serve"}),
}

CASES = {
    "frankfurter": Case(
        id="frankfurter",
        title="The Frankfurter Case",
        clue="a mustard smear on a napkin",
        cause="a magic frankfurter",
        effect="laryngitis",
        remedy="a glass of warm honey water",
        tags={"frankfurter", "magic", "laryngitis"},
    ),
    "lantern": Case(
        id="lantern",
        title="The Lantern Case",
        clue="a glitter trail on the floor",
        cause="a magic spell",
        effect="a stuck whisper",
        remedy="a careful undoing spell",
        tags={"magic", "conflict"},
    ),
}

TOOLS = {
    "notebook": Tool(
        id="notebook",
        label="a small notebook",
        use="write down clues",
        helps={"investigate", "question"},
    ),
    "magnifier": Tool(
        id="magnifier",
        label="a round magnifying glass",
        use="inspect tiny marks",
        helps={"investigate", "search"},
    ),
    "honey": Tool(
        id="honey",
        label="a cup of warm honey water",
        use="soothe a sore throat",
        helps={"laryngitis"},
    ),
    "spellbook": Tool(
        id="spellbook",
        label="an old spellbook",
        use="read the undoing words",
        helps={"magic"},
    ),
}

DETECTIVE_NAMES = ["Mina", "Noah", "Lila", "Eli", "Nora", "Theo"]
HELPER_NAMES = ["Aunt June", "Mr. Pike", "Mrs. Vale", "Uncle Ben"]


@dataclass
class StoryParams:
    setting: str
    case: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A case is reasonable when the setting supports investigation and the case
% has a real cause/effect pair that the available tools can address.
reasonable_case(S, C) :- setting(S), case(C), affords(S, investigate), cause(C, _), effect(C, _).
has_fix(C) :- case(C), remedy(C, R), tool(T), helps(T, R).
valid_story(S, C) :- reasonable_case(S, C), has_fix(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("cause", cid, case.cause))
        lines.append(asp.fact("effect", cid, case.effect))
        lines.append(asp.fact("remedy", cid, case.remedy))
        for t in sorted(case.tags):
            lines.append(asp.fact("tag", cid, t))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        if "investigate" not in setting.affords:
            continue
        for cid in CASES:
            combos.append((sid, cid))
    return combos


def explain_rejection(setting: str, case: str) -> str:
    return f"(No story: {setting} cannot support a proper detective investigation of the {case} case.)"


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

class Token:
    def __init__(self, text: str):
        self.text = text


def _speak(world: World, text: str) -> None:
    world.say(text)


def introduce(world: World, detective: Entity, helper: Entity, case: Case) -> None:
    world.say(
        f"{detective.id} was a small detective with a sharp pencil and a brave way of looking at clues."
    )
    world.say(
        f"{helper.id} kept the counter tidy, but today {helper.pronoun('possessive')} voice had gone rough from laryngitis."
    )
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    helper.memes["worry"] = helper.memes.get("worry", 0) + 1
    world.facts["case"] = case.id
    world.facts["clue"] = case.clue
    world.facts["effect"] = case.effect
    world.facts["cause"] = case.cause
    world.facts["remedy"] = case.remedy


def describe_scene(world: World, case: Case) -> None:
    world.say(
        f"At {world.setting.place}, the lights were bright and the air smelled like ketchup, onions, and surprise."
    )
    world.say(
        f"A little mystery had landed on the table: {case.title}."
    )


def investigate(world: World, detective: Entity, case: Case) -> None:
    detective.meters["observations"] = detective.meters.get("observations", 0) + 1
    world.say(
        f"{detective.id} opened {TOOLS['notebook'].label} and wrote down {case.clue}."
    )
    world.say(
        f"The clue pointed to {case.cause}, not to ordinary bad luck."
    )


def conflict_beats(world: World, helper: Entity, case: Case) -> None:
    helper.memes["conflict"] = helper.memes.get("conflict", 0) + 1
    world.say(
        f"{helper.id} tried to explain, but {helper.pronoun('possessive')} throat was scratchy, so the words came out thin and weak."
    )
    world.say(
        f"That made the room tense, because nobody could agree on how the trouble had started."
    )


def discover_cause(world: World, detective: Entity, case: Case) -> None:
    detective.meters["clues"] = detective.meters.get("clues", 0) + 1
    world.say(
        f"{detective.id} found the tiny truth: a magic frankfurter had been traded for the first bite, and the spell had left {case.effect} behind."
    )
    world.facts["found_cause"] = True


def resolve(world: World, detective: Entity, helper: Entity, case: Case) -> None:
    helper.meters["relief"] = helper.meters.get("relief", 0) + 1
    helper.memes["conflict"] = max(0, helper.memes.get("conflict", 0) - 1)
    detective.memes["pride"] = detective.memes.get("pride", 0) + 1
    world.say(
        f"{detective.id} passed over {TOOLS['honey'].label}, and {helper.id} sipped it slowly."
    )
    world.say(
        f"Then {helper.id} whispered the missing detail clearly enough to solve the case, and the little detective smiled."
    )
    world.say(
        f"By the end, the magic was quiet, the frankfurter was found, and the diner felt warm again."
    )
    world.facts["resolved"] = True


def tell_story(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    detective = world.add(Entity(id=params.detective_name, kind="character", type=params.detective_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    case = CASES[params.case]

    introduce(world, detective, helper, case)
    world.para()
    describe_scene(world, case)
    investigate(world, detective, case)
    conflict_beats(world, helper, case)
    world.para()
    discover_cause(world, detective, case)
    resolve(world, detective, helper, case)
    world.facts.update(detective=detective, helper=helper, setting=params.setting)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    case = CASES[world.facts["case"]]
    det = world.facts["detective"]
    helper = world.facts["helper"]
    return [
        f"Write a short detective story for a young child about {det.id} solving {case.title} at {world.setting.place}.",
        f"Tell a gentle mystery where a magic frankfurter leads to laryngitis, and {helper.id} can only help after a clue is found.",
        f"Write a simple detective story that includes the words frankfurter and laryngitis, with a problem and a clear ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = CASES[world.facts["case"]]
    det = world.facts["detective"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"Who was the little detective in the story?",
            answer=f"The little detective was {det.id}, who watched for clues and kept the case moving.",
        ),
        QAItem(
            question=f"Why was {helper.id} having trouble speaking?",
            answer=f"{helper.id} had laryngitis, so {helper.pronoun('possessive')} voice came out rough and thin.",
        ),
        QAItem(
            question=f"What clue helped {det.id} figure out what happened?",
            answer=f"{case.clue} helped {det.id} connect the trouble to {case.cause}.",
        ),
        QAItem(
            question=f"How did the case get solved in the end?",
            answer=f"{det.id} gave {helper.id} {case.remedy}, the truth came out clearly, and the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a detective for?",
            answer="A detective looks carefully for clues and uses them to solve a mystery.",
        ),
        QAItem(
            question="What is laryngitis?",
            answer="Laryngitis is when the throat gets sore or swollen and a person may sound hoarse or have trouble speaking.",
        ),
        QAItem(
            question="What is a frankfurter?",
            answer="A frankfurter is a sausage that is often served in a bun like a hot dog.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic is when something can happen in a special, surprising way that does not work like ordinary everyday things.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: frankfurter, laryngitis, magic, conflict.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--case", choices=CASES.keys())
    ap.add_argument("--detective-name", dest="detective_name")
    ap.add_argument("--helper-name", dest="helper_name")
    ap.add_argument("--detective-type", choices=["girl", "boy"], dest="detective_type")
    ap.add_argument("--helper-type", choices=["woman", "man", "girl", "boy"], dest="helper_type")
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
    combos = valid_combos()
    if args.setting and args.case:
        if (args.setting, args.case) not in combos:
            raise StoryError(explain_rejection(args.setting, args.case))
    filtered = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.case is None or c[1] == args.case)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, case = rng.choice(sorted(filtered))
    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    helper_type = args.helper_type or rng.choice(["woman", "man"])
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        setting=setting,
        case=case,
        detective_name=detective_name,
        detective_type=detective_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


CURATED = [
    StoryParams(setting="diner", case="frankfurter", detective_name="Mina", detective_type="girl", helper_name="Mr. Pike", helper_type="man"),
    StoryParams(setting="fair", case="frankfurter", detective_name="Eli", detective_type="boy", helper_name="Aunt June", helper_type="woman"),
    StoryParams(setting="kitchen", case="lantern", detective_name="Nora", detective_type="girl", helper_name="Mrs. Vale", helper_type="woman"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for s, c in stories:
            print(f"  {s:10} {c}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
