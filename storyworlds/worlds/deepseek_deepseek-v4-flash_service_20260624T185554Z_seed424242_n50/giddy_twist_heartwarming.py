#!/usr/bin/env python3
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
REGIONS = {"indoors", "outdoors"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = "girl"
        male = "boy"
        if self.type in (female, "mother", "mom", "woman"):
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in (male, "father", "dad", "man"):
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)

    @property
    def friendly_label(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str]


@dataclass
class Expectation:
    """What the hero expects to happen."""
    id: str
    verb: str
    gerund: str
    rush: str
    twist_emotion: str        # e.g. "disappointed" -> turned into heartwarming
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class TwistGear:
    """The unexpected thing that turns the mood around."""
    id: str
    label: str
    covers: set[str]
    guard_emotion: str
    prep: str
    tail: str


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.owner == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_anticipation_grows(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["excited"] >= THRESHOLD and actor.memes["giddy"] < 0.5:
            sig = ("giddy", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                actor.memes["giddy"] += 1.0
                out.append(f"{actor.id} felt a giddy flutter in {actor.pronoun('possessive')} tummy.")
    return out


def _r_twist_cure(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["disappointed"] >= THRESHOLD and actor.memes["heartwarming"] >= THRESHOLD:
            sig = ("twist", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                actor.memes["disappointed"] = 0.0
                actor.memes["joy"] += 1.0
                out.append(f"{actor.id} forgot all about the old plan and smiled.")
    return out


CAUSAL_RULES = [
    Rule(name="giddy", tag="emotional", apply=_r_anticipation_grows),
    Rule(name="twist_cure", tag="emotional", apply=_r_twist_cure),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_twist(world: World, actor: Entity, expectation: Expectation) -> dict:
    sim = world.copy()
    sig = ("twist", actor.id)
    if sig in sim.fired:
        sim.fired.remove(sig)
    # Simulate disappointment then heartwarming from twist gear
    actor_sim = sim.get(actor.id)
    actor_sim.memes["disappointed"] = 1.0
    actor_sim.memes["heartwarming"] = 1.0
    propagate(sim, narrate=False)
    return {"resolved": actor_sim.memes["disappointed"] < 0.5}


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who always looked forward to the next happy thing.")


def loves_expecting(world: World, hero: Entity, expectation: Expectation) -> None:
    hero.memes["love_anticipation"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved {expectation.gerund}; it made every day sparkle.")


def expect_big(world: World, parent: Entity, hero: Entity, prize: Prize, expectation: Expectation) -> None:
    world.say(
        f"{hero.id} was sure that today would bring {prize.phrase}. "
        f"{hero.pronoun().capitalize()} could already imagine the {expectation.keyword}."
    )


def arrive(world: World, hero: Entity, parent: Entity, expectation: Expectation) -> None:
    world.say(
        f"On the morning of the big day, {hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} gathered in the {world.setting.place}."
    )
    hero.memes["excited"] += 1.0
    world.say(f"{hero.id} was almost too giddy to stand still.")


def announce_anticipation(world: World, parent: Entity, hero: Entity, expectation: Expectation) -> None:
    world.say(
        f'"{hero.id}, I have a surprise for you," said {parent.label_word}. '
        f"{hero.id}'s eyes went wide."
    )


def twist_reveal(world: World, parent: Entity, hero: Entity, expectation: Expectation, prize: Prize,
                 twist: TwistGear) -> Optional[TwistGear]:
    """The parent reveals something different from what the hero expected."""
    hero.memes["disappointed"] += 1.0
    world.say(
        f"But instead of {expectation.verb}, {parent.label_word} gently said, "
        f'"We are going to {twist.prep}."'
    )
    world.say(
        f"{hero.id} blinked. This was not the surprise {hero.pronoun()} had hoped for."
    )
    # Check if the twist will actually resolve
    if predict_twist(world, hero, expectation)["resolved"]:
        return twist
    return None


def heartwarming_turn(world: World, hero: Entity, twist: TwistGear) -> None:
    hero.memes["heartwarming"] += 1.0
    world.say(
        f"But then {hero.id} saw that {twist.tail}. "
        f"A warm, giddy feeling flooded through {hero.pronoun('object')}."
    )
    propagate(world)


def accept_twist(world: World, hero: Entity, parent: Entity, twist: TwistGear) -> None:
    hero.memes["joy"] += 1.0
    hero.memes["giddy"] += 1.0
    world.say(
        f"{hero.id} hugged {hero.pronoun('possessive')} {parent.label_word} and said, "
        f'"This is even better than I imagined! I love it."'
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, expectation: Expectation, prize_cfg: Prize,
         hero_name: str = "Alex", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None,
         parent_type: str = "mother") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["hopeful", "curious"]),
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label="the parent"
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    # Act 1
    introduce(world, hero)
    loves_expecting(world, hero, expectation)
    expect_big(world, parent, hero, prize, expectation)

    # Act 2
    world.para()
    arrive(world, hero, parent, expectation)
    announce_anticipation(world, parent, hero, expectation)
    twist = TWISTS[expectation.id]
    used_twist = twist_reveal(world, parent, hero, expectation, prize_cfg, twist)
    if used_twist is None:
        # fallback – always use the defined twist
        used_twist = twist
    world.para()
    heartwarming_turn(world, hero, used_twist)
    accept_twist(world, hero, parent, used_twist)

    world.facts.update(
        hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
        expectation=expectation, setting=setting,
        twist=used_twist,
        resolved=hero.memes["disappointed"] < 0.5
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "home": Setting(place="the living room", indoor=True, affords={"surprise", "gift"}),
    "backyard": Setting(place="the backyard", indoor=False, affords={"surprise", "party"}),
    "park": Setting(place="the park", indoor=False, affords={"surprise", "gift", "party"}),
}

EXPECTATIONS = {
    "surprise": Expectation(
        id="surprise",
        verb="receive a big wrapped present",
        gerund="imagining a giant gift",
        rush="tear open the paper",
        twist_emotion="disappointed",
        zone={"indoors"},
        keyword="present",
        tags={"surprise", "gift"},
    ),
    "party": Expectation(
        id="party",
        verb="have a big party with a bounce house",
        gerund="dreaming of a party",
        rush="run to the backyard",
        twist_emotion="disappointed",
        zone={"outdoors"},
        keyword="party",
        tags={"party", "celebration"},
    ),
    "gift": Expectation(
        id="gift",
        verb="open a shiny new toy",
        gerund="thinking about a new toy",
        rush="unwrap the box",
        twist_emotion="disappointed",
        zone={"indoors"},
        keyword="toy",
        tags={"toy", "treasure"},
    ),
}

TWISTS = {
    "surprise": TwistGear(
        id="twist_surprise",
        label="a quiet tea party with grandma",
        covers={"indoors"},
        guard_emotion="disappointed",
        prep="have a quiet tea party with Grandma instead",
        tail="Grandma was there with cookies and a candle, and the whole room felt cozy and special",
    ),
    "party": TwistGear(
        id="twist_party",
        label="a star-gazing picnic",
        covers={"outdoors"},
        guard_emotion="disappointed",
        prep="go on a star-gazing picnic together",
        tail="the sunset painted the sky pink, and a blanket full of treats waited under the big oak tree",
    ),
    "gift": TwistGear(
        id="twist_gift",
        label="a handmade coupon book",
        covers={"indoors"},
        guard_emotion="disappointed",
        prep="make a special coupon book full of adventures together",
        tail="the pages promised trips to the library, ice cream dates, and extra bedtime stories",
    ),
}

PRIZES = {
    "toy": Prize(label="toy", phrase="a shiny new toy in a colourful box", type="toy", region="indoors"),
    "cake": Prize(label="cake", phrase="a big chocolate cake with sprinkles", type="cake", region="indoors", plural=False),
    "balloon": Prize(label="balloon", phrase="a huge bunch of rainbow balloons", type="balloon", region="indoors", plural=True),
}

NAMES = {
    "boy": ["Alex", "Sam", "Leo", "Eli", "Noah"],
    "girl": ["Mia", "Zoe", "Lily", "Eva", "Ava"]
}

TRAITS = ["hopeful", "curious", "energetic", "sweet"]


def prize_at_risk(expectation: Expectation, prize: Prize) -> bool:
    return prize.region in expectation.zone


def select_twist(expectation: Expectation) -> Optional[TwistGear]:
    return TWISTS.get(expectation.id)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for exp_id in setting.affords:
            exp = EXPECTATIONS[exp_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(exp, prize) and select_twist(exp):
                    combos.append((place, exp_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    expectation: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    exp = f["expectation"]
    prize_cfg = f["prize_cfg"]
    return [
        f'Write a heartwarming story about a {hero.type} named {hero.id} who expects {exp.verb} '
        f'but discovers something even better with {hero.pronoun("possessive")} {parent.label_word}.',
        f'A story that starts with giddy anticipation and ends with a cozy surprise. Use the word "giddy".',
        f"Tell a short tale about a little {hero.type} whose wish changes into a deeper joy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    exp = f["expectation"]
    prize_cfg = f["prize_cfg"]
    twist = f["twist"]
    pos = hero.pronoun("possessive")
    obj = hero.pronoun("object")
    sub = hero.pronoun("subject")
    qa = [
        QAItem(
            question=f"What did {hero.id} feel when {pos} {parent.label_word} "
                     f"announced a surprise?",
            answer=f"{hero.id} felt a giddy excitement, sure that {pos} wish for "
                   f"{exp.verb} was about to come true.",
        ),
        QAItem(
            question=f"What did {parent.label_word} actually plan for {hero.id}?",
            answer=f"Instead of {exp.verb}, {parent.label_word} planned {twist.prep}. "
                   f"It was a quiet, heartwarming surprise.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did {hero.id} feel after seeing the twist?",
            answer=f"{hero.id} felt a warm, giddy happiness because {twist.tail}. "
                   f"{sub} realized this was even better.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does it mean to feel giddy?",
               "Feeling giddy means you are so excited that your tummy feels light "
               "and you almost can't stop smiling."),
        QAItem("Why can a quiet surprise be better than a big one?",
               "A quiet surprise often lets you spend cozy time with people you love, "
               "and that can feel more special than a loud party."),
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="home", expectation="surprise", prize="toy", name="Mia",
                gender="girl", parent="mother", trait="hopeful"),
    StoryParams(place="backyard", expectation="party", prize="cake", name="Sam",
                gender="boy", parent="father", trait="curious"),
    StoryParams(place="park", expectation="gift", prize="balloon", name="Leo",
                gender="boy", parent="father", trait="energetic"),
]


def explain_rejection(expectation: Expectation, prize: Prize) -> str:
    return (f"(No story: {expectation.gerund} doesn't match the prize "
            f"{prize.label}. Try a different combo.)")


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(E, P) :- expectation(E), prize(P), zone(E, R), region(P, R).
protects(T, E, P) :- twist_gear(T), prize_at_risk(E, P),
                     guarded_emotion(T, EM), twist_emotion(E, EM),
                     covers_zone(T, R), zone(E, R).
has_fix(E, P) :- protects(_, E, P).
valid(Place, E, P) :- affords(Place, E), prize_at_risk(E, P), has_fix(E, P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for eid, e in EXPECTATIONS.items():
        lines.append(asp.fact("expectation", eid))
        lines.append(asp.fact("twist_emotion", eid, e.twist_emotion))
        for r in sorted(e.zone):
            lines.append(asp.fact("zone", eid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for tid, t in TWISTS.items():
        lines.append(asp.fact("twist_gear", tid))
        lines.append(asp.fact("guarded_emotion", tid, t.guard_emotion))
        for r in sorted(t.covers):
            lines.append(asp.fact("covers_zone", tid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--expectation", choices=EXPECTATIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.expectation and args.prize:
        exp = EXPECTATIONS[args.expectation]
        pr = PRIZES[args.prize]
        if not (prize_at_risk(exp, pr) and select_twist(exp)):
            raise StoryError(explain_rejection(exp, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.expectation is None or c[1] == args.expectation)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, exp_id, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, expectation=exp_id, prize=prize_id,
                       name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], EXPECTATIONS[params.expectation],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait], params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace=False, qa=False, header="") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for p, e, pr in triples:
            print(f"  {p:9} {e:9} {pr:9}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.expectation} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
