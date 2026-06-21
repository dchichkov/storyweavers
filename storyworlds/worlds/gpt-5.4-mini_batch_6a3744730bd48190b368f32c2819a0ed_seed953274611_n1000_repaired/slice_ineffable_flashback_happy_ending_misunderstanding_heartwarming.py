#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/slice_ineffable_flashback_happy_ending_misunderstanding_heartwarming.py
======================================================================================================

A small heartwarming storyworld about a child, a sliced dessert, a brief
misunderstanding, a flashback to a kind memory, and a happy ending.

The world is intentionally tiny: one shared dessert, one child, one helper, and
one caring adult. The narration is driven by simulated state rather than by a
fixed paragraph template, so different choices can yield slightly different but
still coherent stories.

Seed words: slice, ineffable
Features: Flashback, Happy Ending, Misunderstanding
Style: Heartwarming
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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    kind: str
    slices: int
    special: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class FlashbackCue:
    id: str
    memory: str
    sensory: str
    lesson: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class ComfortFix:
    id: str
    sense: int
    warmth: int
    text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    child: str
    child_gender: str
    adult: str
    adult_gender: str
    treat: str
    fix: str
    misunderstanding: str
    flashback: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CHILDREN = ["Mina", "Noah", "Lia", "Owen", "Iris", "Ezra"]
ADULTS = ["Grandma", "Grandpa", "Mom", "Dad"]
MISUNDERSTANDINGS = {
    "save_for_later": "thought the best slice was being kept away forever",
    "too_small": "thought the last slice was too small to matter",
    "forgotten_note": "thought the note on the plate meant nobody wanted any",
}
FLASHBACKS = {
    "kitchen_lesson": FlashbackCue(
        id="kitchen_lesson",
        memory="the memory of Grandma showing how to cut a cake into neat slices",
        sensory="the sweet smell of vanilla and the soft tap of the knife",
        lesson="sharing can make a treat feel bigger, not smaller",
        tags={"flashback", "memory", "slice"},
    ),
    "birthday_song": FlashbackCue(
        id="birthday_song",
        memory="the memory of everyone singing around a birthday cake",
        sensory="the bright candles and the warm, happy voices",
        lesson="one slice can still carry a whole celebration",
        tags={"flashback", "memory", "slice"},
    ),
}
TREATS = {
    "cake": Treat(
        id="cake",
        label="cake",
        phrase="a small cake with strawberries on top",
        kind="cake",
        slices=4,
        special="slice",
        tags={"slice", "sweet"},
    ),
    "pie": Treat(
        id="pie",
        label="pie",
        phrase="a warm berry pie",
        kind="pie",
        slices=3,
        special="slice",
        tags={"slice", "sweet"},
    ),
    "bread": Treat(
        id="bread",
        label="loaf",
        phrase="a fresh loaf of bread",
        kind="bread",
        slices=5,
        special="slice",
        tags={"slice", "warm"},
    ),
}
FIXES = {
    "share_now": ComfortFix(
        id="share_now",
        sense=3,
        warmth=4,
        text="used a second plate, added a fresh napkin, and shared the slices evenly",
        tags={"share", "kind"},
    ),
    "save_piece": ComfortFix(
        id="save_piece",
        sense=3,
        warmth=5,
        text="wrapped one slice carefully and set it aside for later",
        tags={"share", "kind"},
    ),
    "explain_note": ComfortFix(
        id="explain_note",
        sense=2,
        warmth=3,
        text="pointed to the little note and explained that the saved slice was a kind surprise",
        tags={"share", "kind"},
    ),
    "empty_refill": ComfortFix(
        id="empty_refill",
        sense=1,
        warmth=1,
        text="shook a jar of water and hoped that would fix the misunderstanding",
        tags={"weak", "unreasonable"},
    ),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for tid in TREATS:
        for mid in MISUNDERSTANDINGS:
            for fid, fix in FIXES.items():
                if fix.sense >= SENSE_MIN:
                    for fl in FLASHBACKS:
                        combos.append((tid, mid, fid, fl))
    return combos


def sensible_fixes() -> list[ComfortFix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def explain_rejection(fix_id: str) -> str:
    f = FIXES[fix_id]
    return f"(Refusing fix '{fix_id}': it is too smallhearted or silly for a warm story.)"


def explain_generation(treat: Treat, fix: ComfortFix) -> str:
    return f"(No story: the chosen treat and fix do not support a kind, believable turn.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming slice storyworld with a flashback and a happy ending.")
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--adult", choices=ADULTS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--fix", choices=FIXES)
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
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_rejection(args.fix))
    combos = [c for c in valid_combos()
              if (args.treat is None or c[0] == args.treat)
              and (args.misunderstanding is None or c[1] == args.misunderstanding)
              and (args.fix is None or c[2] == args.fix)
              and (args.flashback is None or c[3] == args.flashback)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    treat, misunderstanding, fix, flashback = rng.choice(sorted(combos))
    child = args.child or rng.choice(CHILDREN)
    adult = args.adult or rng.choice(ADULTS)
    child_gender = "girl" if child in {"Mina", "Lia", "Iris"} else "boy"
    adult_gender = "woman" if adult in {"Grandma", "Mom"} else "man"
    return StoryParams(
        child=child,
        child_gender=child_gender,
        adult=adult,
        adult_gender=adult_gender,
        treat=treat,
        fix=fix,
        misunderstanding=misunderstanding,
        flashback=flashback,
    )


def _setup(world: World, params: StoryParams) -> None:
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child", age=6))
    adult = world.add(Entity(id=params.adult, kind="character", type=params.adult_gender, role="adult", age=70 if params.adult in {"Grandma", "Grandpa"} else 35))
    treat = world.add(Entity(id="treat", kind="thing", type=params.treat, label=TREATS[params.treat].label))
    child.memes["hope"] += 1
    adult.memes["care"] += 1
    world.facts.update(child=child, adult=adult, treat=treat, params=params)


def generate_story(world: World) -> None:
    f = world.facts
    p: StoryParams = f["params"]
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    treat: Entity = f["treat"]
    treat_cfg = TREATS[p.treat]
    flash = FLASHBACKS[p.flashback]
    fix = FIXES[p.fix]

    world.say(f"{child.id} and {adult.id} found {treat_cfg.phrase} cooling on the table. The smell was sweet, and the first {treat_cfg.special} felt almost ineffable, like a tiny promise.")
    world.say(f"{child.id} reached for a {treat_cfg.special}, but a little misunderstanding slipped in: {MISUNDERSTANDINGS[p.misunderstanding]}.")
    child.memes["confusion"] += 1
    adult.memes["worry"] += 1

    world.para()
    world.say(f"Then {adult.id} paused, and a flashback came to mind: {flash.memory}. {flash.sensory}. {flash.lesson.capitalize()}.")
    child.memes["memory"] += 1
    adult.memes["warmth"] += 1

    world.para()
    world.say(f"{adult.id} smiled and gently cleared it up. {adult.id} {fix.text}, and {child.id} listened.")
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    adult.memes["relief"] += 1

    world.para()
    world.say(f"In the end, the treat was shared as {treat_cfg.slices} neat {treat_cfg.special}s. {child.id} got one, {adult.id} got one, and the rest were saved for later in a small covered dish.")
    world.say(f"{child.id} looked at the bright plate, then at {adult.id}, and smiled with an ineffable kind of happiness.")
    child.meters["fed"] += 1
    treat.meters["sliced"] += 1
    world.facts["outcome"] = "happy"


def tell(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    generate_story(world)
    return world


def story_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a heartwarming story that includes the words slice and ineffable, with a small misunderstanding and a kind flashback.",
        f"Tell a gentle story where {p.child} and {p.adult} share a treat, remember a warm moment, and end happily.",
        f"Write a child-friendly story about {TREATS[p.treat].label} that turns a misunderstanding into a happy ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    p: StoryParams = world.facts["params"]
    return [
        ("What did the child and adult find?",
         f"They found {TREATS[p.treat].phrase} on the table. It smelled sweet, and it made the child want a slice right away."),
        ("Why was there a misunderstanding?",
         f"The child misunderstood what the saved slice meant. {MISUNDERSTANDINGS[p.misunderstanding].capitalize()}, so the child felt unsure for a moment."),
        ("What did the flashback help the adult remember?",
         f"It helped {p.adult} remember {FLASHBACKS[p.flashback].memory}. That memory showed a kind way to explain the treats and made the answer gentle."),
        ("How did the story end?",
         f"It ended with the treat shared calmly and fairly, so everyone felt happy. The final plate was full of neat slices and warm feelings."),
    ]


def world_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a slice mean?",
         "A slice is one piece cut from a bigger food, like cake, pie, or bread. People slice food so it can be shared."),
        ("What does ineffable mean?",
         "Ineffable means something is so special or lovely that it is hard to describe with ordinary words. It can mean a feeling that seems bigger than speech."),
        ("What is a flashback in a story?",
         "A flashback is when a story briefly shows an earlier memory. It helps explain why a character feels or acts a certain way."),
        ("What is a misunderstanding?",
         "A misunderstanding happens when someone gets the meaning wrong for a little while. A kind explanation can clear it up."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    if params.treat not in TREATS or params.fix not in FIXES or params.flashback not in FLASHBACKS:
        raise StoryError("(Invalid parameters supplied to generate().)")
    if FIXES[params.fix].sense < SENSE_MIN:
        raise StoryError(explain_rejection(params.fix))
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(f"  {e.id}: meters={meters} memes={memes}")
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(T,F,FB) :- treat(T), fix(F), flashback(FB), sense(F,S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fx.sense))
    for fb in FLASHBACKS:
        lines.append(asp.fact("flashback", fb))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid())
    python_set = set(valid_combos())
    rc = 0
    if clingo_set != python_set:
        print("MISMATCH: ASP and Python valid sets differ.")
        rc = 1
    else:
        print(f"OK: ASP matches Python valid_combos() ({len(clingo_set)} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(child=None, adult=None, treat=None, misunderstanding=None, flashback=None, fix=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams(child="Mina", child_gender="girl", adult="Grandma", adult_gender="woman", treat="cake", fix="save_piece", misunderstanding="save_for_later", flashback="kitchen_lesson"),
    StoryParams(child="Noah", child_gender="boy", adult="Mom", adult_gender="woman", treat="pie", fix="share_now", misunderstanding="too_small", flashback="birthday_song"),
    StoryParams(child="Lia", child_gender="girl", adult="Grandpa", adult_gender="man", treat="bread", fix="explain_note", misunderstanding="forgotten_note", flashback="kitchen_lesson"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_rejection(args.fix))
    combos = [c for c in valid_combos()
              if (args.treat is None or c[0] == args.treat)
              and (args.misunderstanding is None or c[1] == args.misunderstanding)
              and (args.fix is None or c[2] == args.fix)
              and (args.flashback is None or c[3] == args.flashback)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    treat, misunderstanding, fix, flashback = rng.choice(sorted(combos))
    child = args.child or rng.choice(CHILDREN)
    adult = args.adult or rng.choice(ADULTS)
    child_gender = "girl" if child in {"Mina", "Lia", "Iris"} else "boy"
    adult_gender = "woman" if adult in {"Grandma", "Mom"} else "man"
    return StoryParams(child=child, child_gender=child_gender, adult=adult, adult_gender=adult_gender, treat=treat, fix=fix, misunderstanding=misunderstanding, flashback=flashback)


def generate_from_params(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} valid combinations:")
        for t, f, fb in asp_valid():
            print(f"  {t} {f} {fb}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate_from_params(p) for p in CURATED]
    else:
        seen = set()
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
            sample = generate_from_params(params)
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
