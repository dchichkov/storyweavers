#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/obtain_chap_storage_closet_mystery_to_solve.py
===============================================================================

A small detective-style storyworld set in a storage closet.

Premise:
- A child detective and a grown-up/helper search a storage closet for a missing
  thing.
- There is a conflict: one character wants to guess or grab too fast, while the
  other wants to inspect clues.
- There is dialogue and a mystery to solve.
- The ending proves the mystery was solved through observation, not random
  guessing.

This file is standalone and uses only the stdlib plus the shared Storyweavers
result containers. It also includes an inline ASP twin for the reasonable-story
gate and a small parity check under --verify.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

TITLE_WORDS = ("obtain", "chap")

THRESHOLD = 1.0
SUSPICION_MIN = 1.0


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    detail: str
    acoustics: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing: str
    missing_phrase: str
    clue_phrase: str
    clue_kind: str
    hidden_in: str
    reveal_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ConflictPlan:
    id: str
    rash_line: str
    careful_line: str
    repair_line: str
    blame_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    conflict: str
    detective_name: str
    detective_gender: str
    partner_name: str
    partner_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "storage_closet": Setting(
        id="storage_closet",
        label="the storage closet",
        detail="The storage closet smelled faintly of cardboard, old paint, and dusty rope.",
        acoustics="Every whisper came back soft and small from the crowded shelves.",
        tags={"closet", "storage"},
    ),
}

MYSTERIES = {
    "missing_key": Mystery(
        id="missing_key",
        missing="the brass key",
        missing_phrase="a brass key on a red string",
        clue_phrase="a red string hanging from a hook",
        clue_kind="string",
        hidden_in="a box labeled winter hats",
        reveal_word="key",
        tags={"key", "hidden"},
    ),
    "missing_note": Mystery(
        id="missing_note",
        missing="the note",
        missing_phrase="a folded note with blue ink",
        clue_phrase="a scrap of blue paper under a crate",
        clue_kind="paper",
        hidden_in="an old shoe box",
        reveal_word="note",
        tags={"note", "hidden"},
    ),
    "missing_lens": Mystery(
        id="missing_lens",
        missing="the lens",
        missing_phrase="a tiny round magnifying lens",
        clue_phrase="a bright circle of dust-free glass",
        clue_kind="glass",
        hidden_in="a tin of buttons",
        reveal_word="lens",
        tags={"lens", "hidden"},
    ),
}

CONFLICTS = {
    "rush": ConflictPlan(
        id="rush",
        rash_line="\"We should just grab the first thing that looks right,\"",
        careful_line="\"Wait,\"",
        repair_line="\"Let's check the clues first,\"",
        blame_line="\"If we guess wrong, we'll make a bigger mess,\"",
        tags={"conflict", "dialogue"},
    ),
    "argue": ConflictPlan(
        id="argue",
        rash_line="\"I know where it is already,\"",
        careful_line="\"No, you don't,\"",
        repair_line="\"The clue will tell us,\"",
        blame_line="\"A rushed guess could waste the whole afternoon,\"",
        tags={"conflict", "dialogue"},
    ),
}

NAMES = ["Mia", "Noah", "Lena", "Ivy", "Theo", "Ben", "Ava", "Milo", "June", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, m, c) for s in SETTINGS for m in MYSTERIES for c in CONFLICTS]


def reasonableness_gate(setting: Setting, mystery: Mystery, conflict: ConflictPlan) -> bool:
    return setting.id == "storage_closet" and mystery.hidden_in.startswith(("a", "an")) and conflict.id in CONFLICTS


def _inject_clue(world: World, mystery: Mystery) -> None:
    clue = world.get("clue")
    clue.meters["noticed"] += 1
    clue.memes["interest"] += 1
    world.get("case").meters["open"] += 1
    world.say(
        f"A clue was there all along: {mystery.clue_phrase}. "
        f"It seemed to point straight toward {mystery.hidden_in}."
    )


def _resolve_case(world: World, detective: Entity, partner: Entity, helper: Entity, mystery: Mystery) -> None:
    detective.memes["pride"] += 1
    partner.memes["relief"] += 1
    helper.memes["warmth"] += 1
    world.say(
        f"{helper.label_word.capitalize()} smiled and reached into {mystery.hidden_in}. "
        f"Out came {mystery.missing_phrase}, right where the clue had promised."
    )
    world.say(
        f"\"We obtained it at last,\" {detective.id} said, grinning. "
        f"\"A true chap solves the case by looking, not leaping.\""
    )
    world.say(
        f"{partner.id} laughed, and the storage closet felt tidy and bright again."
    )


def _start_case(world: World, detective: Entity, partner: Entity, helper: Entity, setting: Setting, mystery: Mystery) -> None:
    detective.memes["curiosity"] += 1
    partner.memes["unease"] += 1
    world.say(
        f"Inside {setting.label}, {detective.id} and {partner.id} began a small mystery. "
        f"{setting.detail}"
    )
    world.say(
        f"They were looking for {mystery.missing_phrase}, but it was gone."
    )
    world.say(
        f"{setting.acoustics}"
    )


def _conflict_and_dialogue(world: World, detective: Entity, partner: Entity, conflict: ConflictPlan, mystery: Mystery) -> None:
    detective.memes["impulse"] += 1
    partner.memes["caution"] += 1
    world.para()
    world.say(
        f"{detective.id} frowned and said, {conflict.rash_line} \"Maybe it fell behind a shelf.\""
    )
    world.say(
        f"{partner.id} shook {partner.pronoun('possessive')} head. {conflict.careful_line} "
        f"{conflict.repair_line} {conflict.blame_line}"
    )
    world.say(
        f"Their voices echoed between boxes, and the mystery got a little sharper."
    )


def _wrong_turn(world: World, detective: Entity) -> None:
    detective.memes["frustration"] += 1
    world.say(
        f"{detective.id} almost reached for the nearest box, but {detective.pronoun()} stopped."
    )


def tell(setting: Setting, mystery: Mystery, conflict: ConflictPlan,
         detective_name: str, detective_gender: str,
         partner_name: str, partner_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        traits=["curious", "careful"],
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        traits=["impatient", "brave"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=["calm", "observant"],
    ))
    world.add(Entity(id="case", type="case", label="the case"))
    world.add(Entity(id="clue", type="clue", label="the clue"))
    world.add(Entity(id="drawer", type="container", label="the drawer"))

    _start_case(world, detective, partner, helper, setting, mystery)
    _conflict_and_dialogue(world, detective, partner, conflict, mystery)
    _wrong_turn(world, detective)
    world.para()
    _inject_clue(world, mystery)
    helper.memes["confidence"] += 1
    world.say(
        f"{helper.id} pointed at the clue and said, \"See? The closet is telling us something.\""
    )
    _resolve_case(world, detective, partner, helper, mystery)

    world.facts.update(
        detective=detective,
        partner=partner,
        helper=helper,
        setting=setting,
        mystery=mystery,
        conflict=conflict,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a 3-to-5-year-old set in {f["setting"].label} where a child tries to {f["conflict"].id} too fast, but then follows a clue to solve the mystery.',
        f'Write a small mystery story that includes the words "obtain" and "chap", has dialogue, and ends with {f["mystery"].missing} being found in a closet.',
        f'Tell a child-friendly detective story in a storage closet where the characters disagree, talk it through, and obtain the missing item at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    partner = f["partner"]
    helper = f["helper"]
    mystery = f["mystery"]
    conflict = f["conflict"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer=f"It is a detective story about a mystery in {f['setting'].label}. The characters use clues and dialogue to solve it instead of just guessing."
        ),
        QAItem(
            question=f"What did {detective.id} and {partner.id} argue about?",
            answer=f"{detective.id} wanted to move too fast, but {partner.id} wanted to follow the clue first. That conflict mattered because guessing could have sent them to the wrong box."
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{helper.id} noticed the clue and showed them where to look, so they found {mystery.missing_phrase} in {mystery.hidden_in}. That careful step is what turned the argument into a solved case."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a storage closet?",
            answer="A storage closet is a small room used to keep boxes, tools, and other things that people want to store out of the way."
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and tries to solve mysteries by paying attention to small details."
        ),
        QAItem(
            question="Why is a clue helpful in a mystery?",
            answer="A clue can point toward the answer. It helps the detective choose the right place to look instead of guessing blindly."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="storage_closet", mystery="missing_key", conflict="rush",
                detective_name="Mina", detective_gender="girl",
                partner_name="Chap", partner_gender="boy",
                helper_name="Aunt June", helper_gender="woman"),
    StoryParams(setting="storage_closet", mystery="missing_note", conflict="argue",
                detective_name="Eli", detective_gender="boy",
                partner_name="Nora", partner_gender="girl",
                helper_name="Uncle Ben", helper_gender="man"),
    StoryParams(setting="storage_closet", mystery="missing_lens", conflict="rush",
                detective_name="Ava", detective_gender="girl",
                partner_name="Chap", partner_gender="boy",
                helper_name="Dad", helper_gender="man"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld set in a storage closet.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-name")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["woman", "man", "girl", "boy"])
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
    if args.setting and args.setting != "storage_closet":
        raise StoryError("This storyworld only supports the storage closet setting.")
    setting = args.setting or "storage_closet"
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    conflict = args.conflict or rng.choice(list(CONFLICTS))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man", "girl", "boy"])
    detective_name = args.detective_name or rng.choice(NAMES)
    partner_name = args.partner_name or ("Chap" if rng.random() < 0.5 else rng.choice([n for n in NAMES if n != detective_name]))
    helper_name = args.helper_name or rng.choice(["Mom", "Dad", "Aunt June", "Uncle Ben"])
    if detective_name == partner_name:
        raise StoryError("The detective and partner need different names.")
    if not reasonableness_gate(SETTINGS[setting], MYSTERIES[mystery], CONFLICTS[conflict]):
        raise StoryError("The selected options do not form a reasonable mystery story.")
    return StoryParams(
        setting=setting,
        mystery=mystery,
        conflict=conflict,
        detective_name=detective_name,
        detective_gender=detective_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in (("setting", SETTINGS), ("mystery", MYSTERIES), ("conflict", CONFLICTS)):
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        CONFLICTS[params.conflict],
        params.detective_name,
        params.detective_gender,
        params.partner_name,
        params.partner_gender,
        params.helper_name,
        params.helper_gender,
    )
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
setting_ok(storage_closet).
mystery_ok(missing_key).
mystery_ok(missing_note).
mystery_ok(missing_lens).
conflict_ok(rush).
conflict_ok(argue).
reasonable(S, M, C) :- setting_ok(S), mystery_ok(M), conflict_ok(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_ok", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery_ok", mid))
    for cid in CONFLICTS:
        lines.append(asp.fact("conflict_ok", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate.")
        print("python only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, m, c) for s in SETTINGS for m in MYSTERIES for c in CONFLICTS]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("reasonable combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name} in {p.setting} ({p.mystery}, {p.conflict})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
