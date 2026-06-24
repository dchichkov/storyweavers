#!/usr/bin/env python3
"""
A standalone Storyweavers world: reckless curiosity, a cautionary flashback, and
a calm slice-of-life ending.

Seed inspiration:
A child notices a tempting "for later" box on a kitchen shelf, remembers a
previous mess in a brief flashback, asks a careful grown-up, and chooses a safer
way to satisfy curiosity.

This world keeps the scale small and domestic: a kitchen counter, a notebook,
one risky object, one safer substitute, and a gentle ending image proving that
the choice changed the afternoon.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)


@dataclass
class Location:
    id: str
    label: str
    details: str


@dataclass
class Temptation:
    id: str
    label: str
    phrase: str
    risky_use: str
    caution: str
    can_harm: bool = True


@dataclass
class SafeAlternative:
    id: str
    label: str
    phrase: str
    action: str
    comfort: str


@dataclass
class Flashback:
    id: str
    trigger: str
    scene: str
    lesson: str


@dataclass
class StoryParams:
    setting: str
    child: str
    adult: str
    temptation: str
    alternative: str
    flashback: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def get(self, eid: str) -> Entity:
        return self.entities[eid]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Location("kitchen", "the kitchen", "a sunny kitchen with a warm counter"),
    "workshop": Location("workshop", "the workshop", "a small workshop with a crowded bench"),
    "balcony": Location("balcony", "the balcony", "a quiet balcony with potted herbs"),
}

TEMPTATIONS = {
    "marker_caps": Temptation(
        "marker_caps",
        "the marker caps",
        "a cup of bright marker caps",
        "shake them near the table edge",
        "The cap cup looked easy to tip, and the little parts could roll everywhere.",
    ),
    "spice_jar": Temptation(
        "spice_jar",
        "the spice jar",
        "a jar of rainbow sprinkles",
        "open it with wet hands over the floor",
        "A slippery jar could spill, and sticky sprinkles would make a mess fast.",
    ),
    "string_spool": Temptation(
        "string_spool",
        "the string spool",
        "a spool of ribbon",
        "pull too much string at once",
        "Loose ribbon could tangle around feet and chairs.",
    ),
}

ALTERNATIVES = {
    "tray": SafeAlternative(
        "tray",
        "the tray",
        "a shallow tray",
        "sort the pieces one by one onto the tray",
        "The tray keeps little things from rolling away.",
    ),
    "paper": SafeAlternative(
        "paper",
        "the paper",
        "a clean sheet of paper",
        "draw a plan on paper first",
        "Paper gives curiosity a place to land.",
    ),
    "basket": SafeAlternative(
        "basket",
        "the basket",
        "a woven basket",
        "carry the pieces in a basket with both hands",
        "The basket keeps the whole job slow and steady.",
    ),
}

FLASHBACKS = {
    "spill": Flashback(
        "spill",
        "a shaky reach",
        "The child remembered a little spill from last week, when one quick grab sent tiny pieces skittering under the fridge.",
        "Slow hands made less trouble than fast ones.",
    ),
    "scratch": Flashback(
        "scratch",
        "a sharp bend",
        "The child remembered a time a rushed move scratched the table and made everyone sigh.",
        "A careful pause could save both the table and the mood.",
    ),
    "tangle": Flashback(
        "tangle",
        "a tug too far",
        "The child remembered ribbon tangling around a chair leg until the whole room had to stop and untie it.",
        "Curiosity was nicer when it moved gently.",
    ),
}

CHILDREN = ["Mina", "Theo", "Nia", "Ben", "Lena", "Omar", "Iris", "Jules"]
ADULTS = ["Mom", "Dad", "Aunt Rosa", "Uncle Finn", "Grandma", "Grandpa"]


# ---------------------------------------------------------------------------
# ASP twin data
# ---------------------------------------------------------------------------

ASP_RULES = r"""
choice_risky(T) :- temptation(T).
choice_safe(A) :- alternative(A).
flashback_warns(F) :- flashback(F).
cautionary_story :- choice_risky(_), flashback_warns(_), choice_safe(_).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for k in SETTINGS:
        lines.append(asp.fact("setting", k))
    for k, t in TEMPTATIONS.items():
        lines.append(asp.fact("temptation", k))
        if t.can_harm:
            lines.append(asp.fact("can_harm", k))
    for k in ALTERNATIVES:
        lines.append(asp.fact("alternative", k))
    for k in FLASHBACKS:
        lines.append(asp.fact("flashback", k))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_cautionary() -> bool:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show cautionary_story/0.", "#show cautionary_story/0."))
    return any(sym.name == "cautionary_story" for sym in model)


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life cautionary curiosity storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--adult", choices=ADULTS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--alternative", choices=ALTERNATIVES)
    ap.add_argument("--flashback", choices=FLASHBACKS)
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
    if args.temptation and args.temptation not in TEMPTATIONS:
        raise StoryError("Unknown temptation.")
    setting = args.setting or rng.choice(list(SETTINGS))
    child = args.child or rng.choice(CHILDREN)
    adult = args.adult or rng.choice(ADULTS)
    temptation = args.temptation or rng.choice(list(TEMPTATIONS))
    alternative = args.alternative or rng.choice(list(ALTERNATIVES))
    flashback = args.flashback or rng.choice(list(FLASHBACKS))
    if temptation == "string_spool" and alternative == "paper":
        pass
    return StoryParams(setting, child, adult, temptation, alternative, flashback)


def _build_world(params: StoryParams) -> World:
    w = World()
    setting = SETTINGS[params.setting]
    child = w.add(Entity(params.child, kind="character", type="child", role="curious",
                         memes={"curiosity": 2.0, "reckless": 1.0, "caution": 0.0}))
    adult = w.add(Entity(params.adult, kind="character", type="adult", role="guide",
                         memes={"caution": 2.0, "warmth": 1.0}))
    temp = TEMPTATIONS[params.temptation]
    alt = ALTERNATIVES[params.alternative]
    fb = FLASHBACKS[params.flashback]
    w.add(Entity(setting.id, kind="place", label=setting.label, attrs={"details": setting.details}))
    w.add(Entity(temp.id, kind="thing", label=temp.label, attrs={"phrase": temp.phrase}))
    w.add(Entity(alt.id, kind="thing", label=alt.label, attrs={"phrase": alt.phrase}))
    w.add(Entity(fb.id, kind="memory", label=fb.id, attrs={"scene": fb.scene}))
    return w


def generate(params: StoryParams) -> StorySample:
    w = _build_world(params)
    child = w.get(params.child)
    adult = w.get(params.adult)
    temp = TEMPTATIONS[params.temptation]
    alt = ALTERNATIVES[params.alternative]
    fb = FLASHBACKS[params.flashback]
    setting = SETTINGS[params.setting]

    child.memes["curiosity"] += 1
    child.memes["reckless"] += 1
    w.say(
        f"On a quiet afternoon, {child.id} was in {setting.details}. "
        f"{child.id} had {temp.phrase} on the counter and wanted to see what would happen."
    )
    w.say(
        f"It felt a little reckless, but the kind of reckless that comes from wanting to know more."
    )
    w.para()
    child.memes["flashback"] = 1.0
    child.memes["caution"] += 1
    w.say(
        f"As {child.id} reached out, a flashback slipped in. {fb.scene} {fb.lesson}"
    )
    w.say(
        f"{child.id} froze, then looked at {adult.id}. \"I think I should do this the slow way,\" {child.id} said."
    )
    adult.memes["pride"] = 1.0
    adult.memes["warmth"] += 1
    w.say(
        f"{adult.id} smiled and pointed to {alt.phrase}. \"That is a better idea,\" {adult.id} said. "
        f\"You can {alt.action}.\""
    )
    w.para()
    child.memes["curiosity"] += 1
    child.memes["reckless"] = 0.0
    child.memes["caution"] += 1
    w.say(
        f"So {child.id} moved the pieces one by one onto {alt.label}. "
        f"The little job took longer, but it stayed neat and calm."
    )
    w.say(
        f"By the end, the counter was clean, the pieces were sorted, and {child.id} had a better answer to curiosity."
    )
    w.say(
        f"The afternoon stayed ordinary in the nicest way, with {setting.label} warm, tidy, and peaceful."
    )

    story = w.render()
    prompts = [
        f"Write a slice-of-life story where {params.child} feels reckless curiosity about {temp.label}, remembers a cautionary flashback, and chooses a safer way.",
        f"Tell a calm everyday story in {setting.label} where {params.child} nearly makes a mess with {temp.label} but listens to {params.adult}.",
        f"Use a flashback to explain why {params.child} slows down and uses {alt.label} instead of {temp.label}.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.child} want to do at first?",
            answer=f"{params.child} wanted to mess with {temp.label}, because curiosity was pulling hard."
        ),
        QAItem(
            question=f"What made {params.child} stop and think?",
            answer=f"A flashback about {fb.scene} made {params.child} remember {fb.lesson.lower()}"
        ),
        QAItem(
            question=f"What did {params.adult} suggest instead?",
            answer=f"{params.adult} suggested using {alt.phrase} so the task could stay calm and safe."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{params.child} chose the slower, safer choice, and the room stayed neat and peaceful."
        ),
    ]
    world_qa = [
        QAItem("What is curiosity?", "Curiosity is the feeling that makes someone want to learn, look closely, or ask questions."),
        QAItem("What does reckless mean?", "Reckless means doing something without enough care for what could go wrong."),
        QAItem("Why can a flashback matter in a story?", "A flashback can remind a character of an earlier mistake or lesson, which helps guide a new choice."),
        QAItem("What is a slice-of-life story?", "A slice-of-life story shows an ordinary moment from everyday life, usually with a small but meaningful change."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=w)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, asdict(e))
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print("-", p)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def asp_verify() -> int:
    ok = asp_cautionary()
    print("OK: ASP twin says cautionary_story." if ok else "MISMATCH: ASP twin failed.")
    return 0 if ok else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show cautionary_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("cautionary_story")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s in TEMPTATIONS:
            p = StoryParams(
                setting="kitchen",
                child=CHILDREN[0],
                adult=ADULTS[0],
                temptation=s,
                alternative="tray",
                flashback="spill",
            )
            samples.append(generate(p))
    else:
        for i in range(max(1, args.n)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
