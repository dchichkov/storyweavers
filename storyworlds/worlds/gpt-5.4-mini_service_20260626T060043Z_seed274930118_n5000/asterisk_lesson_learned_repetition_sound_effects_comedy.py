#!/usr/bin/env python3
"""
A small comedy storyworld about a mischievous asterisk, repeated sound effects,
and a lesson learned the funny way.

Premise:
A child finds a tiny asterisk on a page and keeps using it to "fix" everything.
The asterisk makes the text sound silly, but it also keeps changing meanings.
A helper shows that the asterisk should be used carefully, and the child learns
that little symbols can be powerful.

The world tracks physical state (meters) and emotional state (memes).
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
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
class StoryParams:
    name: str
    gender: str
    helper: str
    item: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_smudge(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    asterisk = world.get("asterisk")
    sheet = world.get("sheet")
    if child.memes.get("mischief", 0) >= THRESHOLD and asterisk.meters.get("used", 0) >= THRESHOLD:
        sig = ("smudge",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        sheet.meters["confused"] = sheet.meters.get("confused", 0) + 1
        child.memes["embarrassed"] = child.memes.get("embarrassed", 0) + 1
        asterisk.meters["sparkle"] = asterisk.meters.get("sparkle", 0) + 1
        out.append("The page went all twisty and silly.")
    return out


def _r_lesson(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    asterisk = world.get("asterisk")
    if child.memes.get("embarrassed", 0) >= THRESHOLD and helper.memes.get("patient", 0) >= THRESHOLD:
        sig = ("lesson",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["understanding"] = child.memes.get("understanding", 0) + 1
        child.memes["mischief"] = 0
        asterisk.meters["used"] = 0
        return ["The child learned to use the tiny star carefully."]
    return []


RULES = [
    Rule("smudge", _r_smudge),
    Rule("lesson", _r_lesson),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: StoryParams) -> World:
    w = World()
    child_type = params.gender
    child = w.add(Entity(id="child", kind="character", type=child_type, label=params.name))
    helper = w.add(Entity(id="helper", kind="character", type="teacher", label=params.helper))
    asterisk = w.add(Entity(id="asterisk", type="symbol", label="asterisk", phrase="a tiny asterisk"))
    sheet = w.add(Entity(id="sheet", type="paper", label="paper", phrase="a neat page"))
    child.memes["curious"] = 1
    child.memes["mischief"] = 1
    helper.memes["patient"] = 1

    w.say(f"{child.label} found {asterisk.phrase} on {sheet.phrase}.")
    w.say(f"{child.label} thought it could fix everything, so {child.pronoun()} tapped it again and again: tap, tap, tap.")
    w.say(f"*ping* *ping* *ping*")
    w.say(f"Every time the little star blinked, the words looked fancier and funnier.")

    w.para()
    w.say(f"{child.label} tried to stick the asterisk after a promise, after a banana, and even after a sneeze.")
    asterisk.meters["used"] = 1
    propagate(w, narrate=True)
    w.say(f"{helper.label} looked over the page and said, 'That little star is not a magic wand.'")
    w.say(f"'{child.label}, the star means something only when you know what it points to,' {helper.pronoun()} said.")

    w.para()
    if w.get("sheet").meters.get("confused", 0) >= THRESHOLD:
        w.say(f"{child.label} blinked at the messy page and whispered, 'Oops.'")
    w.say(f"Then {child.label} erased the extra stars, kept only one, and tried again.")
    w.say("Tap. Tap. Pause.")
    w.say(f"This time the note made sense, and the tiny asterisk sat still like a polite little comet.")
    propagate(w, narrate=True)

    w.facts.update(child=child, helper=helper, asterisk=asterisk, sheet=sheet)
    return w


def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    return [
        f'Write a funny short story for young children about {c.label}, an asterisk, and a lesson learned.',
        f'Write a comedy story where a tiny asterisk keeps causing trouble and the child repeats "tap, tap, tap".',
        f'Create a child-friendly story with sound effects, repetition, and a symbol that teaches a lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    h = world.facts["helper"]
    return [
        QAItem(
            question=f"What did {c.label} find?",
            answer=f"{c.label} found a tiny asterisk on the page.",
        ),
        QAItem(
            question=f"How did the child act before the lesson?",
            answer=f"{c.label} acted curious and a little mischievous, tapping the asterisk again and again.",
        ),
        QAItem(
            question=f"What sound repeated in the story?",
            answer="The story repeated the sound effect 'tap, tap, tap' when the child kept poking the little star.",
        ),
        QAItem(
            question=f"What did {h.label} teach?",
            answer=f"{h.label} taught that an asterisk only works well when you know what it is pointing to.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The lesson learned was to use the asterisk carefully instead of treating it like a magic trick.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an asterisk?",
            answer="An asterisk is a small star-shaped symbol often used to point to a note or extra meaning.",
        ),
        QAItem(
            question="Why are sound effects used in stories?",
            answer="Sound effects help a story feel lively and fun by making actions easier to imagine.",
        ),
        QAItem(
            question="Why can repetition be funny?",
            answer="Repetition can be funny because hearing the same words again and again can feel playful and surprising.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_mischievous :- mischief(child).
asterisk_used :- used(asterisk).
smudge :- child_mischievous, asterisk_used.
lesson_learned :- smudge, patient(helper).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("mischief", "child"),
        asp.fact("patient", "helper"),
        asp.fact("used", "asterisk"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show lesson_learned/0."))
    ok = any(sym.name == "lesson_learned" for sym in model)
    if ok:
        print("OK: ASP reasoning agrees with the Python story turn.")
        return 0
    print("MISMATCH: ASP did not derive lesson_learned.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about an asterisk and a lesson learned.")
    ap.add_argument("--name", default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--helper", default=None)
    ap.add_argument("--item", default="asterisk")
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


NAMES_GIRL = ["Mia", "Zoe", "Luna", "Nora", "Ella"]
NAMES_BOY = ["Max", "Leo", "Finn", "Noah", "Theo"]
HELPERS = ["Mrs. Wren", "Mr. Bean", "Ms. Pine", "Coach Dot"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(name=name, gender=gender, helper=helper, item=args.item)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show lesson_learned/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mia", gender="girl", helper="Mrs. Wren", item="asterisk"),
            StoryParams(name="Max", gender="boy", helper="Mr. Bean", item="asterisk"),
            StoryParams(name="Luna", gender="girl", helper="Ms. Pine", item="asterisk"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name} and the {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
