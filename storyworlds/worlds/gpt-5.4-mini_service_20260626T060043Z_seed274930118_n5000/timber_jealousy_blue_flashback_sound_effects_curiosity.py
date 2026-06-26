#!/usr/bin/env python3
"""
A bedtime-story world about timber, jealousy, and blue things in a cozy little
cabin. The child hero starts out curious, feels a jealous twinge, remembers a
flashback, and ends by sharing something beautiful.

The simulated world keeps physical meters and emotional memes so the story is
not just a noun swap: the timber can be built, the blue object can be carried,
and the jealousy can rise and then soften.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Setting:
    place: str = "the little cabin"
    indoors: bool = True


@dataclass
class Prize:
    label: str
    phrase: str
    type: str


@dataclass
class StoryParams:
    place: str
    prize: str
    name: str
    gender: str
    sibling: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------
SETTINGS = {
    "cabin": Setting(place="the little cabin", indoors=True),
    "attic": Setting(place="the dusty attic", indoors=True),
    "porch": Setting(place="the front porch", indoors=False),
}

PRIZES = {
    "blue_blanket": Prize(label="blue blanket", phrase="a soft blue blanket", type="blanket"),
    "blue_lantern": Prize(label="blue lantern", phrase="a small blue lantern", type="lantern"),
    "timber_block": Prize(label="timber block", phrase="a smooth timber block", type="block"),
    "timber_boat": Prize(label="timber boat", phrase="a tiny timber boat", type="boat"),
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Poppy"]
BOY_NAMES = ["Finn", "Theo", "Milo", "Ari", "Ben"]
TRAITS = ["curious", "gentle", "sleepy", "brave", "soft-spoken"]


def valid_pairs() -> list[tuple[str, str]]:
    # Small, deliberate set: every prize works in every setting for this world.
    return [(place, prize) for place in SETTINGS for prize in PRIZES]


# ---------------------------------------------------------------------------
# Reasonable-story gate
# ---------------------------------------------------------------------------
def explain_rejection(place: str, prize: str) -> str:
    return f"(No story: the world does not have a safe, bedtime-friendly path for {prize} at {place}.)"


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def setup_story(world: World, hero: Entity, sibling: Entity, prize: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved quiet nights and cozy corners.")
    world.say(f"{hero.pronoun().capitalize()} was especially curious about {prize.label}.")
    world.say(f"{sibling.id} lived with {hero.id} and had a calm way of smiling at bedtime.")
    world.say(f"{hero.id} also loved the warm smell of timber, like a wooden toy after rain.")


def start_wish(world: World, hero: Entity, sibling: Entity, prize: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"One evening, {hero.id} looked at {sibling.id}'s {prize.label} and felt a little tug of jealousy."
    )
    world.say(
        f'"I want to know why {prize.it()} looks so special," {hero.pronoun()} whispered, '
        f'and the room answered with a soft tap-tap from the floorboards.'
    )


def flashback(world: World, hero: Entity, sibling: Entity, prize: Entity) -> None:
    hero.memes["flashback"] += 1
    world.say(
        f"Then {hero.id} remembered something kind from yesterday: {sibling.id} had let {hero.pronoun("object")} "
        f"hold the {prize.label} for a moment while the lantern glowed blue-blue."
    )
    world.say(
        f"In the flashback, the toy made a quiet creak, and {sibling.id} had said, "
        f'"Sharing makes the light last longer."'
    )


def ask_and_learn(world: World, hero: Entity, sibling: Entity, prize: Entity) -> None:
    hero.memes["jealousy"] = max(0.0, hero.memes["jealousy"] - 1.0)
    hero.memes["trust"] += 1
    world.say(
        f"So {hero.id} asked instead of pouting. {hero.pronoun().capitalize()} asked why the {prize.label} felt so nice to use."
    )
    world.say(
        f"{sibling.id} smiled and said the {prize.label} was special because it had been made with smooth timber and careful hands."
    )


def build_together(world: World, hero: Entity, sibling: Entity, prize: Entity) -> None:
    hero.meters["togetherness"] += 1
    sibling.meters["togetherness"] += 1
    world.say(
        f"Together they set the timber pieces in a little line: tap, tap, tap."
    )
    world.say(
        f"The {prize.label} shone blue on the windowsill, and the timber pieces became a tiny shape that looked ready for dreams."
    )
    world.say(
        f"At last the room grew quiet again, and {hero.id} felt warm instead of jealous."
    )


def ending_image(world: World, hero: Entity, sibling: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} and {sibling.id} lay down to sleep with the {prize.label} nearby, blue and peaceful."
    )
    world.say(
        f"The timber toy stayed beside the bed, and the little cabin sounded like a soft, sleepy hush."
    )


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def _r_jealousy(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.memes["jealousy"] < THRESHOLD:
            continue
        sig = ("jealous", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{ent.id} had a jealous feeling, but it was small and flickery.")
    return out


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("curious", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{ent.id} leaned closer, curious enough to ask a question.")
    return out


RULES = [
    Rule("jealousy", _r_jealousy),
    Rule("curiosity", _r_curiosity),
]


def tell(setting: Setting, prize_cfg: Prize, hero_name: str, hero_type: str, sibling_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    sibling = world.add(Entity(id=sibling_name, kind="character", type="girl"))
    prize = world.add(Entity(id=prize_cfg.label, type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))
    prize.carried_by = sibling.id

    setup_story(world, hero, sibling, prize)
    world.para()
    start_wish(world, hero, sibling, prize)
    propagate(world, narrate=True)
    flashback(world, hero, sibling, prize)
    ask_and_learn(world, hero, sibling, prize)
    world.para()
    build_together(world, hero, sibling, prize)
    ending_image(world, hero, sibling, prize)

    world.facts.update(hero=hero, sibling=sibling, prize=prize, setting=setting, trait=trait)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(cabin). place(attic). place(porch).
prize(blue_blanket). prize(blue_lantern). prize(timber_block). prize(timber_boat).

valid(Place, Prize) :- place(Place), prize(Prize).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for pr in PRIZES:
        lines.append(asp.fact("prize", pr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_pairs())
    ac = set(asp_valid_pairs())
    if py == ac:
        print(f"OK: clingo gate matches valid_pairs() ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    if py - ac:
        print("  only in python:", sorted(py - ac))
    if ac - py:
        print("  only in clingo:", sorted(ac - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle bedtime story about {f["hero"].id}, jealousy, and a {f["prize"].label}.',
        f"Tell a cozy story where {f['hero'].id} feels curious and a little jealous about {f['prize'].label}, then remembers a kind flashback.",
        f'Write a bedtime story that uses the word "blue" and ends with sharing and calm breathing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sibling, prize = f["hero"], f["sibling"], f["prize"]
    return [
        QAItem(
            question=f"Why did {hero.id} feel jealous in the story?",
            answer=f"{hero.id} felt jealous because {sibling.id} had the {prize.label}, and it looked special and blue in the cozy room.",
        ),
        QAItem(
            question=f"What did {hero.id} remember before asking about the {prize.label}?",
            answer=f"{hero.id} remembered a flashback from yesterday when {sibling.id} had shared the {prize.label} kindly.",
        ),
        QAItem(
            question=f"What did the children do at the end?",
            answer=f"They worked together with the timber pieces, shared the {prize.label}, and fell asleep feeling warm and calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is timber?",
            answer="Timber is wood that has been cut and used to make things like toys, houses, and little bridges.",
        ),
        QAItem(
            question="What is jealousy?",
            answer="Jealousy is a feeling that can show up when someone wants what another person has.",
        ),
        QAItem(
            question="Why do people like the color blue at bedtime?",
            answer="Blue often feels quiet and peaceful, so people use it for blankets, lights, and calm bedtime scenes.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Sound effects like tap-tap or creak help a reader imagine the little sounds in the scene.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone want to look, ask, and learn more.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: timber, jealousy, blue, flashback, sound effects, curiosity.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--sibling")
    ap.add_argument("--trait", choices=TRAITS)
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
    pairs = valid_pairs()
    if args.place and args.prize:
        if (args.place, args.prize) not in pairs:
            raise StoryError(explain_rejection(args.place, args.prize))
    choices = [p for p in pairs if (args.place is None or p[0] == args.place) and (args.prize is None or p[1] == args.prize)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, prize = rng.choice(choices)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sibling = args.sibling or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, prize=prize, name=name, gender=gender, sibling=sibling, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PRIZES[params.prize], params.name, params.gender, params.sibling, params.trait)
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
    StoryParams(place="cabin", prize="blue_lantern", name="Milo", gender="boy", sibling="Mina", trait="curious"),
    StoryParams(place="attic", prize="blue_blanket", name="Nora", gender="girl", sibling="Theo", trait="gentle"),
    StoryParams(place="porch", prize="timber_boat", name="Finn", gender="boy", sibling="Luna", trait="sleepy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible pairs:")
        for place, prize in combos:
            print(f"  {place:8} {prize}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.prize} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
