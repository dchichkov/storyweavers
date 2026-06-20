#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/attention_twist_bad_ending_moral_value_whodunit.py
===================================================================================

A standalone storyworld for a tiny whodunit about attention, a twist, a bad
ending, and a moral value. Children follow clues around a small room, but the
real lesson is that looking carefully matters.

This world intentionally supports only a few plausible cases: a careful
detective notices what changed, a distracted helper misses a clue, and the final
ending may turn bad when the wrong person is blamed or the real problem is left
unfixed. Every sample is driven by simulated state, not fixed prose.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/attention_twist_bad_ending_moral_value_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/attention_twist_bad_ending_moral_value_whodunit.py --all
    python storyworlds/worlds/gpt-5.4-mini/attention_twist_bad_ending_moral_value_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/attention_twist_bad_ending_moral_value_whodunit.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


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

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    details: str
    clue_spot: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    where: str
    reveals: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Twist:
    id: str
    reveal: str
    moral: str
    ending: str
    bad_end: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_attention(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.role != "detective":
            continue
        if e.memes["attention"] < THRESHOLD:
            continue
        sig = ("attention", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["noticed"] += 1
        out.append("__noticed__")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("twist_seen"):
        return out
    detective = next((e for e in list(world.entities.values()) if e.role == "detective"), None)
    if not detective or detective.memes["noticed"] < THRESHOLD:
        return out
    if world.facts.get("wrong_suspect"):
        world.facts["twist_seen"] = True
        out.append("__twist__")
    return out


CAUSAL_RULES = [
    Rule("attention", "mind", _r_attention),
    Rule("twist", "plot", _r_twist),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_check(setting: Setting, clue: Clue, twist: Twist) -> bool:
    return bool(setting.place and clue.where and twist.reveal)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid in CLUES:
            for tid in TWISTS:
                if reasonableness_check(SETTINGS[sid], CLUES[cid], TWISTS[tid]):
                    combos.append((sid, cid, tid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    twist: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    culprit_name: str
    culprit_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def introduce(world: World, detective: Entity, helper: Entity, setting: Setting) -> None:
    detective.memes["attention"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"At {setting.place}, {detective.id} and {helper.id} were solving a little mystery. "
        f"{setting.details}"
    )
    world.say(
        f"{detective.id} paid close attention to every little thing, while {helper.id} "
        f"kept glancing at the wrong spots."
    )


def show_clue(world: World, clue: Clue, detective: Entity) -> None:
    world.say(
        f"Near {clue.where}, {detective.id} found {clue.phrase}. "
        f"{detective.pronoun().capitalize()} noticed that it pointed toward {clue.reveals}."
    )


def ignore_clue(world: World, helper: Entity, clue: Clue) -> None:
    helper.memes["distracted"] += 1
    world.say(
        f"{helper.id} did not look carefully at {clue.where}, so {helper.pronoun()} "
        f"missed the clue completely."
    )


def accusation(world: World, detective: Entity, culprit: Entity, helper: Entity) -> None:
    culprit.memes["suspicion"] += 1
    world.facts["wrong_suspect"] = True
    world.say(
        f"{detective.id} pointed at {culprit.id} and said it must have been {culprit.id}. "
        f"But {helper.id} was still not listening well enough to object."
    )


def reveal_twist(world: World, twist: Twist, detective: Entity, culprit: Entity) -> None:
    world.say(
        f"Then came the twist: {twist.reveal}. {detective.id} had to look again, "
        f"because the first answer was not the whole truth."
    )
    if twist.bad_end:
        world.say(
            f"The ending turned bad. The real trouble stayed on the table, and {culprit.id} "
            f"was blamed unfairly while the room went quiet."
        )
    else:
        world.say(
            f"With one careful look, {detective.id} fixed the mistake, and everyone felt better."
        )


def moral(world: World, twist: Twist, detective: Entity, helper: Entity) -> None:
    detective.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f"The moral was simple: {twist.moral}. {detective.id} learned that attention can "
        f"solve a mystery, but careless guesses can hurt people."
    )


def bad_ending_image(world: World, twist: Twist, setting: Setting) -> None:
    world.say(
        f"By the end, {twist.ending}. {setting.place} looked the same, but the feeling in the "
        f"room had changed for the worse."
    )


def tell(setting: Setting, clue: Clue, twist: Twist, detective_name: str = "Nina",
         detective_gender: str = "girl", helper_name: str = "Leo",
         helper_gender: str = "boy", culprit_name: str = "Mina",
         culprit_gender: str = "girl") -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender,
                                  role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender,
                              role="helper"))
    culprit = world.add(Entity(id=culprit_name, kind="character", type=culprit_gender,
                               role="culprit"))
    world.facts["wrong_suspect"] = False
    world.facts["twist_seen"] = False

    introduce(world, detective, helper, setting)
    world.para()
    show_clue(world, clue, detective)
    ignore_clue(world, helper, clue)
    accusation(world, detective, culprit, helper)
    propagate(world, narrate=False)

    world.para()
    reveal_twist(world, twist, detective, culprit)
    moral(world, twist, detective, helper)
    if twist.bad_end:
        bad_ending_image(world, twist, setting)
    else:
        world.say(
            f"In the end, {detective.id} remembered to slow down and pay attention, "
            f"and the mystery made sense at last."
        )

    world.facts.update(
        setting=setting,
        clue=clue,
        twist=twist,
        detective=detective,
        helper=helper,
        culprit=culprit,
        ending="bad" if twist.bad_end else "good",
    )
    return world


SETTINGS = {
    "library": Setting("library", "the library", "The shelves were tall, the carpet was soft, and every whisper seemed important.", "the reading nook"),
    "kitchen": Setting("kitchen", "the kitchen", "The counters were neat, but one tiny thing on the floor did not belong.", "the sink"),
    "classroom": Setting("classroom", "the classroom", "The desks were tidy, and the teacher's desk had a stack of papers beside it.", "the chalkboard"),
}

CLUES = {
    "crumb": Clue("crumb", "a crumb trail", "a crumb trail", "the rug", "the snack box", {"food", "attention"}),
    "button": Clue("button", "a red button", "a red button", "the chair", "the coat pocket", {"button", "attention"}),
    "note": Clue("note", "a folded note", "a folded note", "the table corner", "the drawer", {"note", "attention"}),
}

TWISTS = {
    "cat": Twist("cat", "the missing thing was not stolen at all; the cat had pushed it under the couch", "look carefully before accusing", "the wrong suspect went home upset", bad_end=True, tags={"cat", "twist", "bad"}),
    "wind": Twist("wind", "the open window let the wind move the clue, so the first guess was wrong", "do not trust the first guess when the clues can move", "the room stayed messy because nobody checked again", bad_end=True, tags={"wind", "twist", "bad"}),
    "kind_helper": Twist("kind_helper", "the helper had secretly fixed the problem earlier and forgot to say so", "ask questions before deciding", "the misunderstanding made the helper sad for a while", bad_end=True, tags={"helper", "twist", "bad"}),
}


GIRL_NAMES = ["Nina", "Maya", "Luna", "Ella", "Zoe", "Ava"]
BOY_NAMES = ["Leo", "Milo", "Ben", "Noah", "Theo", "Finn"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit story world about attention and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--culprit-name")
    ap.add_argument("--culprit-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, twist = rng.choice(sorted(combos))
    dg = args.detective_gender or rng.choice(["girl", "boy"])
    hg = args.helper_gender or rng.choice(["girl", "boy"])
    cg = args.culprit_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        setting=setting,
        clue=clue,
        twist=twist,
        detective_name=args.detective_name or rng.choice(GIRL_NAMES if dg == "girl" else BOY_NAMES),
        detective_gender=dg,
        helper_name=args.helper_name or rng.choice(GIRL_NAMES if hg == "girl" else BOY_NAMES),
        helper_gender=hg,
        culprit_name=args.culprit_name or rng.choice(GIRL_NAMES if cg == "girl" else BOY_NAMES),
        culprit_gender=cg,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s, c, t = f["setting"], f["clue"], f["twist"]
    d, h, u = f["detective"], f["helper"], f["culprit"]
    return [
        f'Write a whodunit story for a 3-to-5-year-old that uses the word "attention" and ends with a twist in {s.place}.',
        f"Tell a mystery where {d.id} notices {c.phrase}, but {h.id} misses it and the story turns into a bad ending.",
        f"Write a short detective tale with a moral value about why attention matters, and include {t.reveal.lower()}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    s, c, t = f["setting"], f["clue"], f["twist"]
    d, h, u = f["detective"], f["helper"], f["culprit"]
    qa = [
        ("Who was paying close attention?",
         f"{d.id} was the one paying close attention. That is why {d.pronoun()} noticed the clue first."),
        ("What clue was found?",
         f"{d.id} found {c.phrase} near {c.where}. It seemed small, but it pointed toward {c.reveals}."),
        ("What went wrong in the story?",
         f"{h.id} missed the clue, and {d.id} accused {u.id} too quickly. That mistake mattered because the truth was still hidden."),
        ("What was the twist?",
         f"{t.reveal.capitalize()}. The first answer was not the whole truth, so the detective had to look again."),
        ("What moral did the story teach?",
         f"{t.moral.capitalize()}. The story showed that attention helps you solve puzzles, while rushing can lead to a bad ending."),
    ]
    if f["ending"] == "bad":
        qa.append((
            "How did the story end?",
            f"It ended badly. {u.id} was blamed unfairly, and the real problem was not fixed, so the room stayed unhappy."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["clue"].tags) | set(f["twist"].tags) | {"attention"}
    out = []
    if "attention" in tags:
        out.append(("What does attention mean?", "Attention means looking and listening carefully so you notice important details."))
    if "twist" in tags:
        out.append(("What is a twist in a story?", "A twist is a surprise that changes what you thought was true."))
    if "bad" in tags:
        out.append(("What is a bad ending?", "A bad ending is when the problem is not solved and the characters end in a sad or unfair place."))
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
        if TWISTS[tid].bad_end:
            lines.append(asp.fact("bad_end", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, T) :- setting(S), clue(C), twist(T).
notice(attention) :- valid(_, _, _).
show_twist(T) :- twist(T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, clue=None, twist=None,
            detective_name=None, detective_gender=None,
            helper_name=None, helper_gender=None,
            culprit_name=None, culprit_gender=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generate() completed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_world(params: StoryParams) -> World:
    return tell(SETTINGS[params.setting], CLUES[params.clue], TWISTS[params.twist],
                params.detective_name, params.detective_gender,
                params.helper_name, params.helper_gender,
                params.culprit_name, params.culprit_gender)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, c, t in combos:
            print(f"  {s:10} {c:10} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("library", "crumb", "cat", "Nina", "girl", "Leo", "boy", "Mina", "girl"),
            StoryParams("kitchen", "button", "wind", "Leo", "boy", "Ava", "girl", "Maya", "girl"),
            StoryParams("classroom", "note", "kind_helper", "Maya", "girl", "Finn", "boy", "Theo", "boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
