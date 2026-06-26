#!/usr/bin/env python3
"""
Mythic storyworld: a brave child, an attractive charm, a dangerous twirl,
and a lesson learned with moral value.

This world models a tiny myth-style domain where a young hero is tempted by
something beautiful, performs a risky twirl, and learns bravery with guidance.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("shine", "dust", "risk", "rest"):
            self.meters.setdefault(k, 0.0)
        for k in ("bond", "attraction", "bravery", "fear", "lesson_learned", "moral_value", "wonder", "conflict"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "daughter", "queen", "woman", "maiden"}
        masculine = {"boy", "son", "king", "man", "prince"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    myth_name: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    allure: str
    risk: str
    lesson: str
    moral: str
    shine_gain: float
    risk_gain: float
    place_needed: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    turn: int = 0

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        c.turn = self.turn
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "grove": Setting(place="the moonlit grove", myth_name="the moonlit grove", affords={"twirl", "lesson"}),
    "temple": Setting(place="the old temple", myth_name="the old temple", affords={"twirl", "lesson"}),
    "shore": Setting(place="the silver shore", myth_name="the silver shore", affords={"twirl", "lesson"}),
}

CHARM = {
    "golden_ribbon": Charm(
        id="golden_ribbon",
        label="golden ribbon",
        phrase="an attractive golden ribbon",
        allure="its shine called like a tiny star",
        risk="its bright pull could make the child forget caution",
        lesson="beauty can be admired without being obeyed",
        moral="true bravery listens before it leaps",
        shine_gain=2.0,
        risk_gain=2.0,
        place_needed="grove",
    ),
    "silver_spiral": Charm(
        id="silver_spiral",
        label="silver spiral",
        phrase="an attractive silver spiral",
        allure="its curve looked like a moon path",
        risk="its glitter could tempt a wild twirl",
        lesson="not every bright thing is safe to chase",
        moral="wisdom makes bravery steady",
        shine_gain=2.0,
        risk_gain=2.0,
        place_needed="temple",
    ),
    "sea_pearl": Charm(
        id="sea_pearl",
        label="sea pearl",
        phrase="an attractive sea pearl",
        allure="it gleamed like a kind eye in the surf",
        risk="its beauty could tempt a dizzy twirl on the rocks",
        lesson="care keeps wonder alive",
        moral="moral value grows when courage protects others",
        shine_gain=1.5,
        risk_gain=1.5,
        place_needed="shore",
    ),
}

HERO_NAMES = ["Aria", "Kian", "Nia", "Taro", "Lina", "Eren", "Mira", "Soren"]
GUIDE_NAMES = ["the elder", "the shepherd", "the priestess", "the aunt", "the guardian"]


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for hero in world.characters():
            if hero.meters["risk"] >= THRESHOLD and ("fear", hero.id) not in world.fired:
                world.fired.add(("fear", hero.id))
                hero.memes["fear"] += 1
                out.append(f"{hero.id} felt a shiver at the edge of the path.")
                changed = True
            if hero.memes["bond"] >= THRESHOLD and hero.memes["fear"] >= THRESHOLD and ("brave", hero.id) not in world.fired:
                world.fired.add(("brave", hero.id))
                hero.memes["bravery"] += 1
                out.append(f"{hero.id} found courage because {hero.id}'s bond with the guide held steady.")
                changed = True
            if hero.memes["lesson_learned"] >= THRESHOLD and ("moral", hero.id) not in world.fired:
                world.fired.add(("moral", hero.id))
                hero.memes["moral_value"] += 1
                out.append(f"A moral thought settled in {hero.id}'s heart.")
                changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def intro(world: World, hero: Entity, guide: Entity, charm: Charm) -> None:
    world.say(f"In {world.setting.myth_name}, {hero.id} was a little brave wanderer who loved good stories and bright signs.")
    world.say(f"{hero.pronoun().capitalize()} walked beside {guide.label}, and their bond was warm enough to feel like a lantern in the dark.")
    world.say(f"One day they found {charm.phrase}; {charm.allure}.")


def desire(world: World, hero: Entity, charm: Charm) -> None:
    hero.memes["attraction"] += 1
    world.say(f"{hero.id} reached toward the {charm.label}, because {charm.risk} and {charm.allure}.")
    world.say(f"The charm seemed to invite a twirl, and the air around it looked almost pleased to watch.")


def caution(world: World, guide: Entity, hero: Entity, charm: Charm) -> None:
    hero.meters["risk"] += charm.risk_gain
    guide.memes["bond"] += 1
    world.say(f"{guide.label} raised a hand and said, 'A lovely thing can still lead a child astray.'")
    world.say(f"'Bravery is not spinning faster than your thoughts,' {guide.label} said, 'but choosing well.'")
    propagate(world, narrate=True)


def twirl_event(world: World, hero: Entity, charm: Charm) -> None:
    hero.meters["shine"] += charm.shine_gain
    hero.meters["risk"] += charm.risk_gain
    hero.memes["conflict"] += 1
    world.say(f"{hero.id} twirled once under the bright sign, and the {charm.label} flashed like a tiny sun.")
    world.say(f"Then {hero.id} wobbled, because the ground was not as steady as the beauty looked.")
    propagate(world, narrate=True)


def lesson_turn(world: World, guide: Entity, hero: Entity, charm: Charm) -> None:
    hero.memes["lesson_learned"] += 1
    world.say(f"{guide.label} caught {hero.id}'s elbow before the wobble became a fall.")
    world.say(f"Together they stood still, and {hero.id} learned that {charm.lesson}.")
    world.say(f"{guide.label} called this the kind of bravery that gives a person moral value: courage used to protect, not to show off.")
    propagate(world, narrate=True)


def resolution(world: World, hero: Entity, guide: Entity, charm: Charm) -> None:
    hero.memes["conflict"] = 0.0
    hero.memes["bond"] += 1
    hero.memes["bravery"] += 1
    world.say(f"{hero.id} smiled, took one careful breath, and tucked the {charm.label} into a safe place beside the path.")
    world.say(f"At the end, the grove stayed quiet, the bond between them grew stronger, and {hero.id} walked home without another dizzy twirl.")
    world.say(f"What remained was not the glitter alone, but the lesson learned: {charm.moral}.")


def tell(world: World, hero: Entity, guide: Entity, charm: Charm) -> World:
    intro(world, hero, guide, charm)
    world.para()
    desire(world, hero, charm)
    caution(world, guide, hero, charm)
    world.para()
    twirl_event(world, hero, charm)
    lesson_turn(world, guide, hero, charm)
    world.para()
    resolution(world, hero, guide, charm)
    world.facts.update(hero=hero, guide=guide, charm=charm, setting=world.setting)
    return world


# ---------------------------------------------------------------------------
# Sampling / params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    charm: str
    name: str
    guide: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld of bond, attractive, and twirl.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARM)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--guide", choices=GUIDE_NAMES)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, charm_id) for place in SETTINGS for charm_id, charm in CHARM.items() if charm.place_needed == place]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place and args.charm:
        if (args.place, args.charm) not in combos:
            raise StoryError("That charm does not belong to that setting in this myth.")
    filtered = [c for c in combos if (args.place is None or c[0] == args.place) and (args.charm is None or c[1] == args.charm)]
    if not filtered:
        raise StoryError("No valid mythic combination matches those choices.")
    place, charm = rng.choice(sorted(filtered))
    return StoryParams(
        place=place,
        charm=charm,
        name=args.name or rng.choice(HERO_NAMES),
        guide=args.guide or rng.choice(GUIDE_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Aria", "Nia", "Lina", "Mira"} else "boy"))
    guide = world.add(Entity(id="guide", kind="character", type="woman", label=params.guide))
    charm = CHARM[params.charm]
    world = tell(world, hero, guide, charm)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for children with the words "bond", "attractive", and "twirl".',
        f"Tell a mythic story where {f['hero'].id} meets {f['charm'].phrase} in {f['setting'].myth_name} and learns a lesson.",
        f"Write a gentle myth about bravery, moral value, and a child who almost gets dizzy from a twirl.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    charm: Charm = f["charm"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {world.setting.myth_name}?",
            answer=f"{hero.id} found {charm.phrase}. It looked attractive, but it also carried a small danger.",
        ),
        QAItem(
            question=f"Who helped {hero.id} stay safe after the twirl?",
            answer=f"{guide.label} helped {hero.id} stay safe. Their bond made it easier to listen and slow down.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that {charm.lesson}, and that real bravery has moral value when it protects someone from harm.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bond?",
            answer="A bond is a strong connection between people who care about each other.",
        ),
        QAItem(
            question="What does attractive mean?",
            answer="Attractive means something looks pleasing, beautiful, or appealing to the eye.",
        ),
        QAItem(
            question="What is a twirl?",
            answer="A twirl is a quick spinning turn, often done in dancing or play.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing what is right or needed even when you feel afraid.",
        ),
        QAItem(
            question="What is moral value?",
            answer="Moral value is the goodness a choice shows, like being kind, fair, and careful with others.",
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
        lines.append(f"  {e.id}: meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(grove). place(temple). place(shore).
charm(golden_ribbon). charm(silver_spiral). charm(sea_pearl).

in_place(grove, golden_ribbon).
in_place(temple, silver_spiral).
in_place(shore, sea_pearl).

valid(Place, Charm) :- in_place(Place, Charm).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for c in CHARM:
        lines.append(asp.fact("charm", c))
    for c, charm in CHARM.items():
        lines.append(asp.fact("in_place", charm.place_needed, c))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="grove", charm="golden_ribbon", name="Aria", guide="the elder"),
    StoryParams(place="temple", charm="silver_spiral", name="Kian", guide="the priestess"),
    StoryParams(place="shore", charm="sea_pearl", name="Mira", guide="the guardian"),
]


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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        vals = asp_valid_combos()
        print(f"{len(vals)} valid combos:")
        for p, c in vals:
            print(f"  {p:8} {c}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
