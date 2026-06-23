#!/usr/bin/env python3
"""
storyworlds/worlds/award_patty_dialogue_teamwork_rhyming_story.py
==================================================================

A compact storyworld for a rhyming teamwork tale about making a patty and
winning an award. The domain is small on purpose: one child-led kitchen scene,
one helper, one food item, one prize, dialogue, teamwork, and a cheerful ending
that proves what changed.

The story premise:
- A child and a helper want to make a patty for a small contest.
- The first try is rough: the patty is lopsided, and the kitchen gets messy.
- They talk, split the work, and fix it together.
- Their teamwork helps them serve a tidy patty and earn an award.

The prose is intentionally simple and rhyming, but the state still drives it:
meters track cooking progress, mess, neatness, and pride; memes track worry,
hope, and joy. Dialogue comes from the world model, and the ending image proves
the world changed from unfinished to successful.

This file is self-contained and uses only the stdlib plus the shared
storyworlds/results.py and storyworlds/asp.py helpers.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# Robust direct-import path handling: walk upward from __file__ until results.py
# is found, then add that directory so "results" and "asp" resolve everywhere.
_HERE = os.path.abspath(os.path.dirname(__file__))
_ROOT = _HERE
while True:
    if os.path.exists(os.path.join(_ROOT, "results.py")):
        break
    parent = os.path.dirname(_ROOT)
    if parent == _ROOT:
        break
    _ROOT = parent
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wears: str = ""
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

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Kitchen:
    name: str
    setting_line: str
    afford_award: bool = True


@dataclass
class StoryParams:
    kitchen: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    helper_role: str
    award: str
    patty_style: str
    seed: Optional[int] = None


class World:
    def __init__(self, kitchen: Kitchen) -> None:
        self.kitchen = kitchen
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
        clone = World(self.kitchen)
        clone.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, phrase=v.phrase,
            role=v.role, plural=v.plural, owner=v.owner, caretaker=v.caretaker,
            wears=v.wears, attrs=dict(v.attrs),
            meters=defaultdict(float, v.meters), memes=defaultdict(float, v.memes)
        ) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _make_story_word(style: str, patty_style: str) -> str:
    return f"{style} {patty_style}".strip()


def _setup_world(params: StoryParams) -> World:
    kitchen = KITCHENS[params.kitchen]
    world = World(kitchen)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
        role="hero",
        attrs={"style": "kind", "talent": "careful"},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_gender,
        role=params.helper_role,
        attrs={"style": "cheerful", "talent": "steady"},
    ))
    patty = world.add(Entity(
        id="patty",
        kind="thing",
        type="food",
        label="patty",
        phrase=_make_story_word("round", params.patty_style),
        owner=hero.id,
        caretaker=helper.id,
        attrs={"material": "beans", "shape": "round"},
    ))
    award = world.add(Entity(
        id="award",
        kind="thing",
        type="prize",
        label="award",
        phrase=f"shiny {params.award}",
        owner=hero.id,
        attrs={"material": "golden paper", "reason": "teamwork"},
    ))
    pan = world.add(Entity(
        id="pan",
        kind="thing",
        type="tool",
        label="pan",
        phrase="small pan",
        owner=helper.id,
        attrs={"heat": "warm"},
    ))
    world.facts.update(hero=hero.id, helper=helper.id, patty="patty", award="award", pan="pan")
    world.facts["helper_role"] = params.helper_role
    world.facts["kitchen"] = kitchen.name
    world.facts["patty_style"] = params.patty_style
    world.facts["award_word"] = params.award
    return world


def _cook_and_tell(world: World) -> None:
    hero = world.get(world.facts["hero"])
    helper = world.get(world.facts["helper"])
    patty = world.get("patty")
    award = world.get("award")
    hero.memes["hope"] += 1
    helper.memes["hope"] += 1
    world.say(f"In {world.kitchen.name}, with a soft little sigh, {hero.id} smiled at {helper.id} nearby.")
    world.say(f'"Let us make a patty," {hero.id} said bright, "and work as a team from morning to night."')
    world.say(f'"I will mix, and you will press," {helper.id} said. "Together we do our very best."')
    patty.meters["mixed"] += 1
    patty.meters["shaped"] += 1
    patty.meters["neat"] += 1
    patty.meters["cooked"] += 1
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(f'They mixed the patty with careful care, then pressed it smooth with a steady flair.')
    world.say(f'The pan gave a hiss, the patty gave a sizzle, and the little kitchen began to drizzle with cheer.')
    award.meters["earned"] += 1
    award.meters["given"] += 1
    hero.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.say(f'"Look," {helper.id} said, "our teamwork grew, and the tasty patty came out true."')
    world.say(f'The judge handed over an {award.label}, and {hero.id} held it high with delight.')
    world.say(f'They shared the patty, warm and round, and their happy rhyme rang through the town.')


def _add_turn(world: World) -> None:
    hero = world.get(world.facts["hero"])
    helper = world.get(world.facts["helper"])
    patty = world.get("patty")
    hero.memes["worry"] += 1
    patty.meters["mess"] += 1
    patty.meters["shape"] += 0.5
    world.say(f'At first the patty slipped and slid. "Oh no," said {hero.id}, "this is not how I hoped it did."')
    world.say(f'"Do not fret," {helper.id} replied with a grin, "we can team up and try again."')


def tell_story(params: StoryParams) -> World:
    world = _setup_world(params)
    hero = world.get(world.facts["hero"])
    helper = world.get(world.facts["helper"])
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(f"{hero.id} was ready and glad, for a {params.award} prize had been promised in the kitchen they had.")
    world.say(f"{helper.id} came to help with a patty so neat, for teamwork and rhythm would make it complete.")
    world.para()
    _add_turn(world)
    world.para()
    _cook_and_tell(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a young child about {f["hero"]} and {f["helper"]} making a patty together and winning an award.',
        f'Tell a gentle teamwork story with dialogue that includes the words "award" and "patty".',
        f'Write a simple rhyme where two helpers share the work, fix a messy patty, and celebrate with an award.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get(world.facts["hero"])
    helper = world.get(world.facts["helper"])
    patty = world.get("patty")
    award = world.get("award")
    return [
        QAItem(
            question=f"Who worked together to make the patty in {world.kitchen.name}?",
            answer=f"{hero.id} and {helper.id} worked together. They shared the job, talked kindly, and made the patty as a team.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel worried before the patty was finished?",
            answer=f"The patty was sliding and messy at first, so {hero.id} worried it might not turn out right. Then {helper.id} helped fix it by sharing the work.",
        ),
        QAItem(
            question=f"What did they win after the patty was cooked well?",
            answer=f"They won an {award.label}. They earned it because their teamwork made the patty turn out neat and tasty.",
        ),
        QAItem(
            question=f"How did the dialogue help the story move forward?",
            answer=f"The talking gave them a plan. When {helper.id} said they could try again, {hero.id} felt calmer and kept working.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people share the work and help each other do one job together.",
        ),
        QAItem(
            question="What is an award?",
            answer="An award is a prize or honor given to someone for doing something well.",
        ),
        QAItem(
            question="What is a patty?",
            answer="A patty is a small flat piece of food, often shaped by hand before it is cooked.",
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
    lines.append("== (3) World knowledge ==")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for kitchen in KITCHENS:
        for award in AWARDS:
            for patty_style in PATTY_STYLES:
                combos.append((kitchen, award, patty_style))
    return combos


ASP_RULES = r"""
kitchen(kitchen).
award(word_award).
patty(style_simple).
valid(K, A, P) :- kitchen(K), award(A), patty(P).
teamwork_story :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for k in KITCHENS:
        lines.append(asp.fact("kitchen", k))
    for a in AWARDS:
        lines.append(asp.fact("award", a))
    for p in PATTY_STYLES:
        lines.append(asp.fact("patty", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        py = set(valid_combos())
        cl = set(asp_valid_combos())
        if py == cl:
            print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        else:
            rc = 1
            print("MISMATCH in valid_combos():")
            print("  only in python:", sorted(py - cl))
            print("  only in clingo:", sorted(cl - py))
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception:
        traceback.print_exc()
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming teamwork storyworld about a patty and an award.")
    ap.add_argument("--kitchen", choices=KITCHENS.keys())
    ap.add_argument("--award", choices=AWARDS.keys())
    ap.add_argument("--patty-style", dest="patty_style", choices=PATTY_STYLES.keys())
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-role", choices=["friend", "sibling", "neighbor"])
    ap.add_argument("-n", "--n", type=int, default=1)
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
    kitchen = args.kitchen or rng.choice(list(KITCHENS.keys()))
    award = args.award or rng.choice(list(AWARDS.keys()))
    patty_style = args.patty_style or rng.choice(list(PATTY_STYLES.keys()))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_pool = [n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != hero_name]
    helper_name = args.helper_name or rng.choice(helper_pool)
    helper_role = args.helper_role or rng.choice(list(HELPER_ROLES.keys()))
    return StoryParams(
        kitchen=kitchen,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_role=helper_role,
        award=award,
        patty_style=patty_style,
    )


def generate(params: StoryParams) -> StorySample:
    if params.kitchen not in KITCHENS or params.award not in AWARDS or params.patty_style not in PATTY_STYLES:
        raise StoryError("Invalid parameters for this storyworld.")
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


def _asp_modes() -> None:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    combos = sorted(set(asp.atoms(model, "valid")))
    print(f"{len(combos)} compatible combos:")
    for c in combos:
        print(" ", c)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        _asp_modes()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(
            kitchen=k, hero_name="Mia", hero_gender="girl",
            helper_name="Noah", helper_gender="boy", helper_role="friend",
            award=a, patty_style=p)) for (k, a, p) in valid_combos()[:3]]
    else:
        for i in range(args.n):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


KITCHENS = {
    "sunny": Kitchen(name="the sunny kitchen", setting_line="The sunny kitchen smelled warm and kind."),
    "cozy": Kitchen(name="the cozy kitchen", setting_line="The cozy kitchen glowed soft and bright."),
    "school": Kitchen(name="the school kitchen", setting_line="The school kitchen hummed with cheerful light."),
}

AWARDS = {
    "star": "star",
    "ribbon": "ribbon",
    "medal": "medal",
}

PATTY_STYLES = {
    "round": "round",
    "golden": "golden",
    "crisp": "crisp",
}

HELPER_ROLES = {
    "friend": "friend",
    "sibling": "sibling",
    "neighbor": "neighbor",
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Noah", "Eli", "Leo", "Theo", "Ben", "Max"]


if __name__ == "__main__":
    main()
