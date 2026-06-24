#!/usr/bin/env python3
"""
storyworlds/worlds/sectioned_hug_calzone_flower_field_lesson_learned.py
=======================================================================

A small Adventure-style storyworld set in a flower field.

Seed image:
- A flower field adventure
- Something sectioned
- A warm hug
- A calzone
- A clear Lesson Learned ending

The world simulates a tiny quest: children explore a flower field, discover a
sectioned picnic problem, use a hug to steady feelings, and learn that a calzone
should be shared carefully rather than grabbed all at once.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    trail: str
    goal: str
    style_word: str = "adventure"


@dataclass
class SectionedThing:
    id: str
    label: str
    parts: int
    problem: str
    openable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class ComfortAction:
    id: str
    sense: int
    effect: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class StoryParams:
    theme: str
    sectioned: str
    hugger: str
    huggee: str
    calzone: str
    action: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    seed: Optional[int] = None


THEMES = {
    "flower_field": Theme(
        id="flower_field",
        scene="a bright flower field",
        rig="The grass made a soft path, the flowers stood in little rows, and the sun painted everything gold.",
        trail="the flower path",
        goal="the stone arch at the far end",
        style_word="adventure",
    ),
    "sunlit_meadow": Theme(
        id="sunlit_meadow",
        scene="a sunlit meadow",
        rig="The meadow shimmered with daisies, the breeze lifted the petals, and the hill looked like a hidden map.",
        trail="the meadow trail",
        goal="the old gate by the trees",
        style_word="adventure",
    ),
}

SECTIONED = {
    "sectioned_basket": SectionedThing(
        id="sectioned_basket",
        label="sectioned picnic basket",
        parts=3,
        problem="the food was split into neat little sections, but one section was missing",
        tags={"sectioned"},
    ),
    "sectioned_box": SectionedThing(
        id="sectioned_box",
        label="sectioned lunch box",
        parts=4,
        problem="the meal was split into tiny compartments, and the biggest one was empty",
        tags={"sectioned"},
    ),
}

CALZONES = {
    "cheese": SectionedThing(
        id="cheese_calzone",
        label="calzone",
        parts=2,
        problem="it was warm and split down the middle",
        tags={"calzone"},
    ),
    "garden": SectionedThing(
        id="garden_calzone",
        label="calzone",
        parts=4,
        problem="it was folded with savory filling inside",
        tags={"calzone"},
    ),
}

ACTIONS = {
    "share": ComfortAction(
        id="share",
        sense=3,
        effect=2,
        text="carefully split the calzone so everyone got a fair piece",
        fail="tried to split it, but the pieces slid apart and nobody was happy",
        qa_text="split the calzone into fair pieces",
        tags={"calzone"},
    ),
    "hug_and_share": ComfortAction(
        id="hug_and_share",
        sense=3,
        effect=3,
        text="gave a warm hug first, then carefully shared the calzone",
        fail="wanted to share, but the fuss grew too big until someone helped",
        qa_text="gave a hug and shared the calzone",
        tags={"hug", "calzone"},
    ),
    "hold_tight": ComfortAction(
        id="hold_tight",
        sense=2,
        effect=1,
        text="held the calzone tightly and kept it safe until everyone calmed down",
        fail="held on too tightly and made the problem worse",
        qa_text="held the calzone and waited to share",
        tags={"calzone"},
    ),
}

NAMES_G = ["Lina", "Maya", "Nora", "Zoe", "Ivy", "Rosa"]
NAMES_B = ["Finn", "Theo", "Ari", "Milo", "Eli", "Noah"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in THEMES:
        for s in SECTIONED:
            for c in CALZONES:
                combos.append((t, s, c))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.action not in ACTIONS:
        raise StoryError("Unknown action.")
    if ACTIONS[params.action].sense < SENSE_MIN:
        raise StoryError("That action is too weak for this storyworld.")


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for s, item in SECTIONED.items():
        lines.append(asp.fact("sectioned", s))
        lines.append(asp.fact("parts", s, item.parts))
    for c in CALZONES:
        lines.append(asp.fact("calzone", c))
    for a, act in ACTIONS.items():
        lines.append(asp.fact("action", a))
        lines.append(asp.fact("sense", a, act.sense))
        lines.append(asp.fact("effect", a, act.effect))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(T,S,C) :- theme(T), sectioned(S), calzone(C).
sensible(A) :- action(A), sense(A,S), sense_min(M), S >= M.
"""


class TraceRule:
    def __init__(self, name, fn):
        self.name = name
        self.fn = fn


def _hug(world: World) -> list[str]:
    out = []
    if world.get("friend").memes.get("worry", 0) >= THRESHOLD:
        sig = ("hug",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("friend").memes["worry"] = 0
            world.get("hero").memes["care"] = world.get("hero").memes.get("care", 0) + 1
            out.append("The hug made the worry shrink.")
    return out


RULES = [TraceRule("hug", _hug)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            out = rule.fn(world)
            if out:
                changed = True
                for s in out:
                    world.say(s)


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(NAMES_G if gender == "girl" else NAMES_B)


def tell(theme: Theme, sectioned: SectionedThing, calzone: SectionedThing, action: ComfortAction,
         hero: str, hero_gender: str, friend: str, friend_gender: str) -> World:
    w = World()
    h = w.add(Entity(id="hero", kind="character", type=hero_gender, label=hero, role="hero"))
    f = w.add(Entity(id="friend", kind="character", type=friend_gender, label=friend, role="friend"))
    basket = w.add(Entity(id="basket", label=sectioned.label))
    pie = w.add(Entity(id="calzone", label=calzone.label))
    w.facts.update(theme=theme, sectioned=sectioned, calzone=calzone, action=action,
                   hero=h, friend=f, basket=basket, pie=pie)
    h.memes["curiosity"] = 1
    f.memes["worry"] = 1

    w.say(f"On an adventure in {theme.scene}, {hero} and {friend} followed {theme.trail}.")
    w.say(theme.rig)
    w.para()
    w.say(f"They found a {sectioned.label}, and it had a problem: {sectioned.problem}.")
    w.say(f"Inside it sat a warm {calzone.label}, {calzone.problem}.")
    w.say(f'"Look," said {hero}, "the snack is all sectioned up."')
    w.say(f'{friend} frowned. "That makes it hard to share."')
    w.para()

    # emotional turn
    w.say(f"{hero} stepped closer and gave {friend} a hug.")
    w.say(f"That hug was small, but it helped {friend} breathe easier.")
    propagate(w)

    w.para()
    w.say(f"Then {hero} {action.text}.")
    if action.id == "hold_tight":
        w.say("But the plan felt sticky, because nobody could enjoy a snack that was never passed around.")
    else:
        w.say("The little pieces passed from hand to hand like treasure on a quest.")

    w.para()
    w.say(f"In the end, {hero} and {friend} reached {theme.goal} with full bellies and calmer hearts.")
    w.say("Lesson Learned: good adventure means sharing, taking turns, and using a hug to cool a worried moment.")

    w.facts.update(
        outcome="shared",
        lesson=True,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an adventure story in {f['theme'].scene} where {f['hero'].label} and {f['friend'].label} find a {f['sectioned'].label} and a {f['calzone'].label}. Include a hug and end with Lesson Learned.",
        f"Tell a child-friendly adventure about a sectioned snack in a flower field, where a hug helps two friends decide how to share a calzone.",
        f"Make a short adventure story with a flower field, a sectioned basket, and a calzone, and show that sharing is better than grabbing the whole thing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="Where did the adventure happen?",
            answer=f"It happened in {f['theme'].scene}, where the flowers and sun made the path feel like a quest.",
        ),
        QAItem(
            question="What was sectioned in the story?",
            answer=f"A {f['sectioned'].label} was sectioned, which meant the food was split into separate parts.",
        ),
        QAItem(
            question="What warm food did the children find?",
            answer=f"They found a {f['calzone'].label} and wanted to share it.",
        ),
        QAItem(
            question="What helped the worried friend feel better?",
            answer="A hug helped the worried friend feel better before they shared the snack.",
        ),
        QAItem(
            question="What lesson did the story teach?",
            answer="It taught that sharing, taking turns, and giving a hug can turn a small problem into a happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a calzone?",
            answer="A calzone is a folded bread snack with filling inside, a bit like a pocket of warm food.",
        ),
        QAItem(
            question="What does sectioned mean?",
            answer="Sectioned means split into parts or sections so the pieces are separated.",
        ),
        QAItem(
            question="Why can a hug help in a story?",
            answer="A hug can help because it makes someone feel safe, calm, and cared for.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} label={e.label!r} memes={dict(e.memes)} meters={dict(e.meters)}")
    lines.append(f"  fired rules: {sorted(r for r, in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "",
             "== (2) Story questions =="]
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    theme = args.theme or rng.choice(list(THEMES))
    sectioned = args.sectioned or rng.choice(list(SECTIONED))
    calzone = args.calzone or rng.choice(list(CALZONES))
    action = args.action or rng.choice(["share", "hug_and_share"])
    reasonableness_gate(StoryParams(theme, sectioned, "A", "B", calzone, action, "Hero", "girl", "Friend", "boy"))
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if hero_gender == "girl" else "girl"
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender)
    return StoryParams(theme, sectioned, hero, friend, calzone, action, hero, hero_gender, friend, friend_gender, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], SECTIONED[params.sectioned], CALZONES[params.calzone],
                 ACTIONS[params.action], params.hero, params.hero_gender, params.friend, params.friend_gender)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld in a flower field with a sectioned snack and a lesson learned.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--sectioned", choices=SECTIONED)
    ap.add_argument("--calzone", choices=CALZONES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_sensible() -> list[str]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP combos match Python combos.")
    else:
        rc = 1
        print("MISMATCH: ASP combos differ.")
    if set(asp_sensible()) == {k for k, v in ACTIONS.items() if v.sense >= SENSE_MIN}:
        print("OK: ASP sensible actions match Python gate.")
    else:
        rc = 1
        print("MISMATCH: sensible actions differ.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid_combo/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible actions: {', '.join(asp_sensible())}")
        print(f"combos: {len(asp_valid_combos())}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for theme, sectioned, calzone in valid_combos():
            p = StoryParams(
                theme=theme,
                sectioned=sectioned,
                hugger="",
                huggee="",
                calzone=calzone,
                action="hug_and_share",
                hero="Lina",
                hero_gender="girl",
                friend="Finn",
                friend_gender="boy",
                seed=base_seed,
            )
            samples.append(generate(p))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            p = resolve_params(args, rng)
            p.seed = base_seed + i
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
