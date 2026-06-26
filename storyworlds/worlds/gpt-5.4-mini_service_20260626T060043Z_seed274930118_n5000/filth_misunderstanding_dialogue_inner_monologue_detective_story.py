#!/usr/bin/env python3
"""
A standalone story world for a small detective-style misunderstanding about filth.

Premise:
A child detective sees a messy clue, misunderstands who made the filth, asks
questions out loud, and privately pieces together the truth before the ending
reveals the real cause.

This script follows the Storyworld contract:
- self-contained stdlib script
- shared result containers imported eagerly
- ASP helper imported lazily
- StoryParams / registries / parser / resolve_params / generate / emit / main
- world state drives the prose
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    clues: list[str] = field(default_factory=list)
    affordances: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    phrase: str
    mess: str
    soil: str
    clue: str
    where: str
    misleading_hint: str
    truth: str


@dataclass
class SuspectGear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    repair: str


@dataclass
class StoryParams:
    setting: str
    cause: str
    suspect: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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


def _r_filth_spreads(world: World) -> list[str]:
    out: list[str] = []
    cause = world.facts.get("cause")
    if not cause:
        return out
    c: Cause = cause
    culprit = world.get(c.id)
    if culprit.meters.get(c.mess, 0) < THRESHOLD:
        return out
    sig = ("spread", c.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["filth_present"] = True
    world.say(f"The {c.mess} on the floor looked fresh, like it had a story to tell.")
    out.append(c.clue)
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("filth_present"):
        return out
    if world.facts.get("misunderstanding_spoken"):
        return out
    detective: Entity = world.facts["detective"]
    suspect: Entity = world.facts["suspect"]
    if detective.memes.get("suspicion", 0) < THRESHOLD:
        return out
    world.facts["misunderstanding_spoken"] = True
    out.append(
        f'"{suspect.label} must have made this mess," {detective.id} thought, '
        f'while staring at the {world.facts["cause"].mess}.'
    )
    return out


def _r_truth(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("filth_present"):
        return out
    if world.facts.get("truth_seen"):
        return out
    detective: Entity = world.facts["detective"]
    helper: Entity = world.facts["helper"]
    cause: Cause = world.facts["cause"]
    suspect: Entity = world.facts["suspect"]
    if detective.memes.get("curiosity", 0) < THRESHOLD:
        return out
    if helper.meters.get(cause.mess, 0) < THRESHOLD:
        return out
    world.facts["truth_seen"] = True
    world.facts["misunderstanding_fixed"] = True
    detective.memes["relief"] = detective.memes.get("relief", 0) + 1
    out.append(
        f'But {helper.id} pointed at the {cause.clue} and said, "{cause.truth}"'
    )
    out.append(
        f'{suspect.label} had only been near the spot after the real trouble started.'
    )
    return out


CAUSAL_RULES = [
    _r_filth_spreads,
    _r_misunderstanding,
    _r_truth,
]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    for line in produced:
        world.say(line)
    return produced


def setting_detail(setting: Setting, cause: Cause) -> str:
    if setting.indoor:
        return f"The room was quiet, except for one ugly stain near the desk."
    return f"{setting.place.capitalize()} looked ordinary, until the filth caught the eye."


def introduce_detective(world: World, detective: Entity) -> None:
    trait = next((t for t in detective.traits if t != "little"), "sharp")
    world.say(
        f"{detective.id} was a little {trait} detective who noticed every smudge, crumb, and stain."
    )


def introduce_helper(world: World, helper: Entity) -> None:
    world.say(
        f"{helper.id} was the kind of friend who listened carefully and asked good questions."
    )


def seed_the_scene(world: World, detective: Entity, helper: Entity, cause: Cause, suspect: Entity) -> None:
    world.say(
        f"One day, {detective.id} and {helper.id} went to {world.setting.place} to look around."
    )
    world.say(setting_detail(world.setting, cause))
    world.say(
        f"{detective.id} saw the {cause.mess} and immediately thought of {suspect.label}."
    )
    detective.memes["suspicion"] = detective.memes.get("suspicion", 0) + 1
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    world.facts["filth_present"] = True


def dialogue_scene(world: World, detective: Entity, helper: Entity, cause: Cause, suspect: Entity) -> None:
    world.para()
    world.say(f'"Did you see this?" {detective.id} asked.')
    world.say(f'"I did," said {helper.id}, "but seeing is not the same as knowing."')
    world.say(
        f'"Maybe {suspect.label} did it," {detective.id} said, trying to sound brave.'
    )
    world.say(
        f'"Maybe," said {helper.id}, "or maybe the filth came from {cause.where}."'
    )
    world.facts["misunderstanding_spoken"] = True


def inner_monologue_scene(world: World, detective: Entity, cause: Cause) -> None:
    world.para()
    world.say(
        f"{detective.id} frowned. Maybe I blamed the wrong person, the detective thought."
    )
    world.say(
        f"If the clue at {cause.where} matched the stain, the answer might be simpler than it looked."
    )


def resolution_scene(world: World, detective: Entity, helper: Entity, cause: Cause, suspect: Entity) -> None:
    world.para()
    helper.meters[cause.mess] = helper.meters.get(cause.mess, 0) + 1
    propagate(world)
    if not world.facts.get("misunderstanding_fixed"):
        world.say(
            f"Then {helper.id} wiped the clue clean and the truth became easier to see."
        )
        world.facts["misunderstanding_fixed"] = True
    world.say(
        f'{detective.id} blinked, then nodded. "Oh," {detective.id} said, "the filth came from {cause.truth.lower()}"'
    )
    world.say(
        f'{suspect.label} was innocent, and the real mess had a much smaller, stranger cause.'
    )
    detective.memes["suspicion"] = 0
    detective.memes["relief"] = detective.memes.get("relief", 0) + 1


def tell(setting: Setting, cause: Cause, suspect: Entity, detective_name: str, detective_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        traits=["little", "sharp", "careful"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        traits=["kind", "patient"],
    ))
    suspect_ent = world.add(Entity(
        id=suspect.id,
        kind="character",
        type=suspect.type,
        label=suspect.label,
        traits=suspect.traits,
    ))
    culprit = world.add(Entity(
        id=cause.id,
        kind="thing",
        type="thing",
        label=cause.label,
        phrase=cause.phrase,
    ))
    culprit.meters[cause.mess] = 1
    world.facts.update(detective=detective, helper=helper, suspect=suspect_ent, cause=cause)

    introduce_detective(world, detective)
    introduce_helper(world, helper)
    seed_the_scene(world, detective, helper, cause, suspect_ent)
    dialogue_scene(world, detective, helper, cause, suspect_ent)
    inner_monologue_scene(world, detective, cause)
    resolution_scene(world, detective, helper, cause, suspect_ent)
    return world


SETTINGS = {
    "library": Setting(place="the library", indoor=True, clues=["dusty shelf", "open window"], affordances={"quiet"}),
    "station": Setting(place="the station", indoor=True, clues=["muddy bootprint", "wet floor"], affordances={"quiet"}),
    "alley": Setting(place="the alley", indoor=False, clues=["spilled crate", "dripping pipe"], affordances={"search"}),
}

CAUSES = {
    "ink": Cause(
        id="inkpot",
        label="an inkpot",
        phrase="a tipped inkpot",
        mess="inky",
        soil="inky",
        clue="ink trail",
        where="the desk",
        misleading_hint="someone sneaky",
        truth="the wind blew the window open and knocked it over",
    ),
    "jam": Cause(
        id="jar",
        label="a jam jar",
        phrase="a broken jam jar",
        mess="sticky",
        soil="sticky",
        clue="sweet smear",
        where="the shelf",
        misleading_hint="a thief with quick hands",
        truth="the jar cracked after it was left too close to the edge",
    ),
    "mud": Cause(
        id="boot",
        label="a muddy boot",
        phrase="a muddy boot by the door",
        mess="muddy",
        soil="muddy",
        clue="bootprint",
        where="the doorway",
        misleading_hint="a burglar",
        truth="a delivery worker stepped in after the rain and tracked mud inside",
    ),
}

SUSPECTS = {
    "cat": Entity(id="Milo", type="cat", label="Milo the cat", traits=["quiet", "curious"]),
    "janitor": Entity(id="MsPine", type="woman", label="Ms. Pine", traits=["busy", "careful"]),
    "visitor": Entity(id="Theo", type="boy", label="Theo", traits=["new", "shy"]),
}

GIRL_NAMES = ["Nina", "Maya", "Lina", "Ava", "Ivy", "Rosa"]
BOY_NAMES = ["Owen", "Noah", "Finn", "Eli", "Jasper", "Theo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for c in CAUSES:
            for sus in SUSPECTS:
                combos.append((s, c, sus))
    return combos


def explain_rejection() -> str:
    return "(No story: the requested clues would not support a believable filth mystery.)"


def explain_gender(thing: str, gender: str) -> str:
    return f"(No story: {thing} is not a typical {gender}'s role in this small case.)"


@dataclass
class WorldView:
    setting: Setting
    cause: Cause
    suspect: Entity
    detective: Entity
    helper: Entity
    paragraphs: list[list[str]] = field(default_factory=list)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c: Cause = f["cause"]
    d: Entity = f["detective"]
    h: Entity = f["helper"]
    s: Entity = f["suspect"]
    return [
        f'Write a short detective story for a young child that includes the word "filth" and a misunderstanding.',
        f"Tell a story where {d.id} thinks {s.label} made the filth, but {h.id} helps {d.id} see the truth.",
        f"Write a gentle mystery with dialogue and inner monologue set at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    helper: Entity = f["helper"]
    suspect: Entity = f["suspect"]
    cause: Cause = f["cause"]
    setting = world.setting.place
    return [
        QAItem(
            question=f"Where did {detective.id} and {helper.id} look for clues?",
            answer=f"They looked around {setting}, where the filth was easy to spot.",
        ),
        QAItem(
            question=f"Who did {detective.id} first think made the mess?",
            answer=f"{detective.id} first thought {suspect.label} made the filth.",
        ),
        QAItem(
            question=f"What helped {detective.id} understand the mistake?",
            answer=f"The clue from {cause.where}, plus {helper.id}'s careful words, helped {detective.id} understand the mistake.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"It ended when {detective.id} realized the filth came from {cause.truth.lower()}, not from {suspect.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is filth?",
            answer="Filth is very dirty or messy stuff, like mud, sticky goo, or grime on a floor.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks the wrong thing because they do not have the full truth.",
        ),
        QAItem(
            question="Why do detectives ask questions?",
            answer="Detectives ask questions so they can gather clues and figure out what really happened.",
        ),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="library", cause="ink", suspect="cat", detective_name="Nina", detective_gender="girl", helper_name="Owen", helper_gender="boy"),
    StoryParams(setting="station", cause="mud", suspect="visitor", detective_name="Eli", detective_gender="boy", helper_name="Maya", helper_gender="girl"),
    StoryParams(setting="alley", cause="jam", suspect="janitor", detective_name="Ava", detective_gender="girl", helper_name="Jasper", helper_gender="boy"),
]


ASP_RULES = r"""
filthy(C) :- cause(C).
misunderstanding(D,S) :- detective(D), suspect(S), thinks_wrong(D,S).
truth_seen(D) :- clue_reveals_truth(D).
resolved :- truth_seen(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for c in s.clues:
            lines.append(asp.fact("clue", sid, c))
    for cid, c in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("mess", cid, c.mess))
    for sid, sus in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    models = asp.solve(asp_program("#show cause/1."), models=1)
    if models:
        print("OK: ASP program grounds and solves.")
        return 0
    print("ASP verification failed: no model.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world about filth, misunderstanding, dialogue, and inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting)
              and (args.cause is None or c[1] == args.cause)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, cause, suspect = rng.choice(sorted(combos))
    det_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if det_gender == "girl" else "girl")
    det_name = args.name or rng.choice(GIRL_NAMES if det_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    return StoryParams(setting=setting, cause=cause, suspect=suspect, detective_name=det_name, detective_gender=det_gender, helper_name=helper_name, helper_gender=helper_gender)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    cause = CAUSES[params.cause]
    suspect = SUSPECTS[params.suspect]
    world = tell(setting, cause, suspect, params.detective_name, params.detective_gender, params.helper_name, params.helper_gender)
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
        print(asp_program("#show cause/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
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
            header = f"### {p.detective_name}: {p.cause} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
