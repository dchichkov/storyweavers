#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gender_lesson_learned_mystery_to_solve_whodunit.py
==================================================================================

A small whodunit storyworld about a missing object, a few suspects, and a lesson
learned about assuming things from gender. The stories are state-driven: clues
accumulate, a mistaken assumption causes tension, the detective solves the
mystery, and the ending proves what changed.

This module follows the Storyweavers storyworld contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

GENDER_WORD = "gender"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Clue:
    id: str
    label: str
    place: str
    tells: str
    tag: str = ""
    hidden_by: str = ""


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    alibi: str
    clue: str
    innocent_reason: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    clue: str
    culprit: str
    detective: str
    detective_gender: str
    suspect1: str
    suspect1_gender: str
    suspect2: str
    suspect2_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[str] = set()
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


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _set_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = value


def _add_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        if "reveal" not in world.fired:
            detective = world.get("detective")
            if _meter(detective, "curiosity") >= THRESHOLD:
                world.fired.add("reveal")
                clue = world.get(world.facts["clue_id"])
                helper = world.get("helper")
                suspect = world.get(world.facts["culprit_id"])
                detective.memes["certainty"] = detective.memes.get("certainty", 0.0) + 1
                helper.memes["helpfulness"] = helper.memes.get("helpfulness", 0.0) + 1
                clue.meters["noticed"] = clue.meters.get("noticed", 0.0) + 1
                world.say(
                    f"The clue made {helper.id} point toward the real trail, "
                    f"and {suspect.id} could no longer hide behind a guess."
                )
                changed = True
        if "lesson" not in world.fired:
            detective = world.get("detective")
            if _meter(detective, "understanding") >= THRESHOLD:
                world.fired.add("lesson")
                world.say(
                    f"{detective.id} remembered the lesson: a person's gender does "
                    f"not tell you whether they are honest, kind, or guilty."
                )
                changed = True


def suspicious_first_guess(world: World, detective: Entity, suspect: Entity) -> None:
    detective.memes["assumption"] = detective.memes.get("assumption", 0.0) + 1
    world.say(
        f'{detective.id} glanced at {suspect.id} and made a quick guess based on {GENDER_WORD}.'
    )
    world.say(
        f"But the guess felt shaky, because the mystery still had real clues to read."
    )


def show_clue(world: World, clue: Clue) -> None:
    clue_ent = world.get(clue.id)
    _add_meter(clue_ent, "noticed", 1)
    world.say(
        f"In {clue.place}, they found {clue.label}: {clue.tells}. "
        f"It was the sort of clue that mattered more than a guess."
    )


def ask_questions(world: World, detective: Entity, suspect1: Entity, suspect2: Entity) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0.0) + 1
    world.say(
        f'{detective.id} asked {suspect1.id} and {suspect2.id} where they had been '
        f"when the object vanished."
    )


def alibis(world: World, suspect1: Entity, suspect2: Entity, culprit: Entity) -> None:
    world.say(
        f"{suspect1.id} had a neat alibi, and {suspect2.id} did too. "
        f"But one alibi lined up better with the clue than the others."
    )
    if culprit.id == suspect1.id:
        world.say(f"That left {suspect1.id} looking more suspicious than expected.")
    else:
        world.say(f"That left {suspect2.id} looking more suspicious than expected.")


def solve(world: World, detective: Entity, culprit: Entity, clue: Clue) -> None:
    _add_meter(detective, "understanding", 1)
    _add_meter(detective, "curiosity", 1)
    propagate(world)
    world.say(
        f'{detective.id} pointed to {clue.label} and said, "The clue shows who took it. '
        f"It was {culprit.id}, not because of {GENDER_WORD}, but because the evidence fit."
    )
    world.say(
        f"The room went quiet, and then the truth fit together like the last piece of a puzzle."
    )


def lesson(world: World, detective: Entity, helper: Entity) -> None:
    detective.memes["humility"] = detective.memes.get("humility", 0.0) + 1
    helper.memes["pride"] = helper.memes.get("pride", 0.0) + 1
    world.say(
        f"{helper.id} smiled and said that good detectives listen to clues first. "
        f"{detective.id} nodded and promised to ask before assuming anything about {GENDER_WORD} again."
    )
    world.say(
        f"After that, the search was calmer, and everyone trusted a careful question more than a fast guess."
    )


SETTING_WORDS = {
    "library": ("the library", "a quiet library", "between the tall shelves"),
    "garden": ("the garden", "a little garden", "under the rosemary bush"),
    "classroom": ("the classroom", "a bright classroom", "near the back table"),
    "museum": ("the museum", "a small museum", "beside the display case"),
}

CLUES = {
    "blue_button": Clue(
        id="blue_button",
        label="a blue button",
        place="the floor",
        tells="it matched the missing case's latch",
        tag="button",
        hidden_by="the sleeve",
    ),
    "crumbs": Clue(
        id="crumbs",
        label="a trail of crumbs",
        place="the hallway",
        tells="it led straight from the snack box to the bench",
        tag="crumbs",
        hidden_by="the napkin",
    ),
    "paint_smudge": Clue(
        id="paint_smudge",
        label="a paint smudge",
        place="the easel",
        tells="it was fresh on one hand and not the other",
        tag="paint",
        hidden_by="the apron",
    ),
}

SUSPECTS = {
    "ana": Suspect("Ana", "Ana", "girl", "she was reading by the window", "blue_button",
                   "Ana had no reason to take it; the button matched her coat, not the missing item."),
    "ben": Suspect("Ben", "Ben", "boy", "he was sweeping near the door", "crumbs",
                   "Ben had crumbs on his sleeve from lunch, which explained the trail."),
    "cora": Suspect("Cora", "Cora", "girl", "she was painting a poster", "paint_smudge",
                    "Cora had paint on her hands because she was painting, not because she stole anything."),
    "drew": Suspect("Drew", "Drew", "boy", "he was organizing markers", "blue_button",
                    "Drew stayed busy all afternoon and had an ordinary coat button, not a secret."),
}

HELPERS = {
    "teacher": Entity(id="teacher", kind="character", type="woman", label="the teacher", role="helper"),
    "librarian": Entity(id="librarian", kind="character", type="man", label="the librarian", role="helper"),
    "friend": Entity(id="friend", kind="character", type="girl", label="the friend", role="helper"),
}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for setting in SETTING_WORDS:
        for clue_id in CLUES:
            for culprit in SUSPECTS:
                out.append((setting, clue_id, culprit))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld about a mystery, clues, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTING_WORDS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--culprit", choices=SUSPECTS)
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--suspect1", choices=SUSPECTS)
    ap.add_argument("--suspect1-gender", choices=["girl", "boy"])
    ap.add_argument("--suspect2", choices=SUSPECTS)
    ap.add_argument("--suspect2-gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--helper-gender", choices=["girl", "boy", "woman", "man"])
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


def _pick(rng: random.Random, items: list[str]) -> str:
    return rng.choice(items)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or _pick(rng, list(SETTING_WORDS))
    clue = args.clue or _pick(rng, list(CLUES))
    culprit = args.culprit or _pick(rng, list(SUSPECTS))
    detective = args.detective or _pick(rng, ["Mina", "Noah", "Iris", "Evan", "Luna"])
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    suspect_names = [k for k in SUSPECTS if k != culprit]
    suspect1 = args.suspect1 or suspect_names[0]
    suspect2 = args.suspect2 or suspect_names[1]
    suspect1_gender = args.suspect1_gender or SUSPECTS[suspect1].type
    suspect2_gender = args.suspect2_gender or SUSPECTS[suspect2].type
    helper = args.helper or _pick(rng, list(HELPERS))
    helper_gender = args.helper_gender or HELPERS[helper].type
    if culprit not in SUSPECTS:
        raise StoryError("Unknown culprit.")
    return StoryParams(
        setting=setting,
        clue=clue,
        culprit=culprit,
        detective=detective,
        detective_gender=detective_gender,
        suspect1=suspect1,
        suspect1_gender=suspect1_gender,
        suspect2=suspect2,
        suspect2_gender=suspect2_gender,
        helper=helper,
        helper_gender=helper_gender,
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting_name, setting_desc, clue_place = SETTING_WORDS[params.setting]
    clue = CLUES[params.clue]
    culprit = SUSPECTS[params.culprit]
    detective = world.add(Entity(id=params.detective, kind="character", type=params.detective_gender,
                                 label="the detective", role="detective"))
    s1 = world.add(Entity(id=params.suspect1, kind="character", type=params.suspect1_gender,
                          label=params.suspect1, role="suspect"))
    s2 = world.add(Entity(id=params.suspect2, kind="character", type=params.suspect2_gender,
                          label=params.suspect2, role="suspect"))
    helper = world.add(HELPERS[params.helper])
    clue_ent = world.add(Entity(id=clue.id, kind="thing", type="clue", label=clue.label, role="clue"))
    culprit_ent = world.add(Entity(id=culprit.id, kind="character", type=culprit.type, label=culprit.label, role="suspect"))

    world.facts.update(clue_id=clue_ent.id, culprit_id=culprit_ent.id)

    detective.memes["curiosity"] = 1
    world.say(
        f"On a quiet day in {setting_name}, {detective.id} found a mystery to solve. "
        f"Something small had gone missing, and everyone in the room had looked surprised."
    )
    world.say(f"The place was {setting_desc}, and the clue waited {clue_place}.")
    world.para()
    suspicious_first_guess(world, detective, s1)
    ask_questions(world, detective, s1, s2)
    show_clue(world, clue)
    world.para()
    alibis(world, s1, s2, culprit_ent)
    solve(world, detective, culprit_ent, clue)
    lesson(world, detective, helper)
    world.para()
    world.say(
        f"In the end, the missing thing was returned, the mystery was solved, and "
        f"{detective.id} watched the room feel honest again."
    )
    world.say(
        f"Nobody cared about a fast guess anymore; they cared about careful eyes, fair questions, and the word {GENDER_WORD} not being used as a shortcut."
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    culprit = p["culprit_id"]
    return [
        f"Write a whodunit for a young child that includes the word {GENDER_WORD} and ends with a lesson learned.",
        f"Tell a mystery to solve in which clues matter more than guessing someone's {GENDER_WORD}.",
        f"Write a gentle detective story where {culprit} is identified by evidence, not by assumptions about {GENDER_WORD}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    p = world.facts
    culprit = p["culprit_id"]
    detective = world.get("detective")
    clue = world.get(p["clue_id"])
    helper = world.get("helper")
    return [
        ("What kind of story is this?", "It is a whodunit, so there is a mystery to solve and clues to follow."),
        ("What did the detective learn?", f"{detective.id} learned that a person's {GENDER_WORD} does not tell the truth about who did something."),
        ("How was the mystery solved?", f"The detective solved it by following {clue.label} and seeing which clue fit the evidence best."),
        ("Who helped with the lesson?", f"{helper.id} helped by reminding everyone to listen to clues before making a quick guess."),
        ("Who did it?", f"{culprit} did it, and the story shows that the clue, not the person's {GENDER_WORD}, revealed the answer."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a clue?", "A clue is a small piece of information that helps solve a mystery."),
        ("What does a detective do?", "A detective looks carefully, asks questions, and uses clues to find answers."),
        ("What is a whodunit?", "A whodunit is a mystery story where the reader finds out who did something."),
        ("Why is it bad to guess from gender?", "Because gender does not tell you what a person did, what they know, or whether they are honest."),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
culprit(C) :- culprit_id(C).
clue(K) :- clue_id(K).
gender_word(gender).
lesson_learned :- culprit(C), clue(K), true.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", k) for k in SETTING_WORDS
    ] + [
        asp.fact("clue", k) for k in CLUES
    ] + [
        asp.fact("suspect", k) for k in SUSPECTS
    ] + [asp.fact("gender_word", GENDER_WORD)]


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1. #show clue/1. #show suspect/1."))
    return sorted(set(asp.atoms(model, "setting")))  # simple twin check anchor


def asp_verify() -> int:
    rc = 0
    try:
        combos = valid_combos()
        if not combos:
            raise RuntimeError("no combos")
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, clue=None, culprit=None, detective=None, detective_gender=None,
            suspect1=None, suspect1_gender=None, suspect2=None, suspect2_gender=None,
            helper=None, helper_gender=None
        ), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as e:
        print(f"FAILED: smoke test crashed: {e}")
        rc = 1
    try:
        _ = asp_program("", "#show setting/1.")
        print("OK: ASP program assembled.")
    except Exception as e:
        print(f"FAILED: ASP assembly crashed: {e}")
        rc = 1
    return rc


CURATED = [
    StoryParams(
        setting="library",
        clue="blue_button",
        culprit="ana",
        detective="Mina",
        detective_gender="girl",
        suspect1="Ben",
        suspect1_gender="boy",
        suspect2="Cora",
        suspect2_gender="girl",
        helper="teacher",
        helper_gender="woman",
    ),
    StoryParams(
        setting="garden",
        clue="crumbs",
        culprit="ben",
        detective="Noah",
        detective_gender="boy",
        suspect1="Ana",
        suspect1_gender="girl",
        suspect2="Cora",
        suspect2_gender="girl",
        helper="friend",
        helper_gender="girl",
    ),
    StoryParams(
        setting="classroom",
        clue="paint_smudge",
        culprit="cora",
        detective="Iris",
        detective_gender="girl",
        suspect1="Ana",
        suspect1_gender="girl",
        suspect2="Drew",
        suspect2_gender="boy",
        helper="teacher",
        helper_gender="woman",
    ),
]


def explain_rejection() -> str:
    return "(No story: the chosen options do not make a coherent mystery.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.culprit not in SUSPECTS:
        raise StoryError(explain_rejection())
    if args.setting and args.setting not in SETTING_WORDS:
        raise StoryError(explain_rejection())
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTING_WORDS)),
        clue=args.clue or rng.choice(list(CLUES)),
        culprit=args.culprit or rng.choice(list(SUSPECTS)),
        detective=args.detective or rng.choice(["Mina", "Noah", "Iris", "Evan"]),
        detective_gender=args.detective_gender or rng.choice(["girl", "boy"]),
        suspect1=args.suspect1 or "Ana",
        suspect1_gender=args.suspect1_gender or "girl",
        suspect2=args.suspect2 or "Ben",
        suspect2_gender=args.suspect2_gender or "boy",
        helper=args.helper or "teacher",
        helper_gender=args.helper_gender or "woman",
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


def build_cli() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show setting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
