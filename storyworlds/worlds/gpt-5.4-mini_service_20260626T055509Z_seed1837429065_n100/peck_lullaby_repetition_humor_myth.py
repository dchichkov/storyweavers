#!/usr/bin/env python3
"""
storyworlds/worlds/peck_lullaby_repetition_humor_myth.py
=========================================================

A tiny mythic storyworld about a small peck, a soft lullaby, and the comic
power of repetition.

Premise:
- A little woodpecker loves to peck at a sacred drum-stump in a moonlit grove.
- The pecking wakes grumpy sprites and rattles a fragile moon-shell.
- A grandmother bird answers with a lullaby, and the pecking becomes gentle,
  rhythmic, and funny instead of chaotic.

The world is built from a few state variables:
- physical meters: noise, crack, calm, sparkle
- emotional memes: curiosity, worry, joy, pride, sleepiness

The stories are shaped like little myths:
- a named creature with a customary habit
- a warning about balance and consequence
- a comic escalation through repetition
- a soothing turn through music
- a resolution image that proves the change

The domain includes the seed words "peck" and "lullaby", and the prose aims
for repetition, humor, and a mythic voice.
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
# Story model
# ---------------------------------------------------------------------------
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"bird", "girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "grove": Setting(place="the moonlit grove", mood="silver", affords={"peck"}),
    "cliff": Setting(place="the singing cliff", mood="windy", affords={"peck"}),
    "orchard": Setting(place="the apple orchard", mood="sweet", affords={"peck"}),
}

ACTIVITIES = {
    "peck": Activity(
        id="peck",
        verb="peck the sacred drum-stump",
        gerund="pecking the sacred drum-stump",
        rush="peck faster and faster",
        sound="peck, peck, peck",
        mess="noise",
        zone={"ears", "sleep"},
        keyword="peck",
        tags={"peck", "noise"},
    ),
}

PRIZES = {
    "moon_shell": Prize(
        label="moon-shell",
        phrase="a fragile moon-shell",
        type="shell",
        region="sleep",
    ),
    "berry_tart": Prize(
        label="berry tart",
        phrase="a sweet berry tart for the sprites",
        type="tart",
        region="sleep",
    ),
    "bell_charm": Prize(
        label="bell charm",
        phrase="a tiny bell charm of polished bronze",
        type="charm",
        region="sleep",
    ),
}

GIRL_NAMES = ["Ari", "Luma", "Nia", "Mira", "Suri"]
BOY_NAMES = ["Pek", "Ori", "Tavi", "Milo", "Rin"]
CAREGIVERS = ["grandmother", "mother", "aunt"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    caregiver: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin and reasonableness
# ---------------------------------------------------------------------------
ASP_RULES = r"""
risk(A,P) :- activity(A), prize(P), splashes(A,R), worn_on(P,R).
soothed(A,P) :- risk(A,P), lullaby_can_help(A,P).
valid_story(Place,A,P,G) :- affords(Place,A), risk(A,P), soothed(A,P), wears(G,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in ["girl", "boy"]:
            lines.append(asp.fact("wears", g, pid))
    lines.append(asp.fact("lullaby_can_help", "peck", "moon_shell"))
    lines.append(asp.fact("lullaby_can_help", "peck", "berry_tart"))
    lines.append(asp.fact("lullaby_can_help", "peck", "bell_charm"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                combos.append((place, act, prize))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, a, pr) for p, a, pr in valid_combos()}
    clingo = {(p, a, pr) for (p, a, pr, g) in asp_valid_combos()}
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - clingo:
        print("  only in python:", sorted(py - clingo))
    if clingo - py:
        print("  only in clingo:", sorted(clingo - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def reasonability_check(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if params.prize not in PRIZES:
        raise StoryError("Unknown prize.")


def predict(world: World, actor: Entity, activity: Activity, prize: Entity) -> dict:
    sim = world.copy()
    act = sim.get(actor.id)
    act.meters["noise"] = act.meters.get("noise", 0.0) + 1
    sim.get(prize.id).meters["crack"] = 1.0
    return {"crack": True, "noise": act.meters["noise"]}


def _do_peck(world: World, hero: Entity, activity: Activity, prize: Entity, narrate: bool = True) -> None:
    hero.meters["noise"] = hero.meters.get("noise", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    prize.meters["crack"] = prize.meters.get("crack", 0.0) + 0.5
    if narrate:
        world.say(f"{hero.id} went {activity.gerund}.")
        world.say(f"{activity.sound}. {activity.sound}. {activity.sound}.")

    if prize.meters["crack"] >= THRESHOLD:
        prize.memes["worry"] = prize.memes.get("worry", 0.0) + 1


def introduce(world: World, hero: Entity) -> None:
    world.say(f"In the old stories, {hero.id} was a little {hero.type} who loved a noisy trick.")


def setup(world: World, hero: Entity, caregiver: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} loved to peck, peck, peck at the drum-stump until the grove laughed with echoes."
    )
    world.say(
        f"Beside the roots, {caregiver.id} watched {hero.pronoun('object')} guard {hero.pronoun('possessive')} {prize.label}."
    )
    world.say(
        f"The {prize.label} was so fragile that even a joke could make it tremble."
    )
    world.facts.update(hero=hero, caregiver=caregiver, prize=prize, activity=activity)


def warning(world: World, caregiver: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, activity, prize)
    if not pred["crack"]:
        return False
    world.say(
        f'"If you keep going," {caregiver.id} said, "your {prize.label} will crack like a sleepy nut."'
    )
    return True


def humor_turn(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} tried to peck more softly, but soft pecks only made the rhythm sillier."
    )
    world.say(
        f"Peck, peck. Peck, peck. Peck—then a sneezy bird on a branch answered, and the whole grove snorted."
    )


def lullaby_turn(world: World, caregiver: Entity, hero: Entity, prize: Entity) -> None:
    caregiver.memes["calm"] = caregiver.memes.get("calm", 0.0) + 1
    hero.memes["sleepiness"] = hero.memes.get("sleepiness", 0.0) + 1
    prize.meters["crack"] = max(0.0, prize.meters.get("crack", 0.0) - 0.5)
    world.say(
        f"Then {caregiver.id} began a lullaby, low and round, like moonlight rocking a bowl of milk:"
    )
    world.say(
        '"Hush now, peck now, slow little beak now, / peck with a pillow, peck with a cloud."'
    )


def resolution(world: World, hero: Entity, caregiver: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(
        f"{hero.id} pecked to the lullaby instead of to the clatter, and the stump sounded like a tiny drum in a dream."
    )
    world.say(
        f"The {prize.label} stayed whole, the sprites stopped frowning, and the moon seemed to nod along."
    )
    world.say(
        f"At the end, {hero.id} still pecked, but now {hero.pronoun('possessive')} pecking had a joke in it and a song in it."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, caregiver_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    caregiver = world.add(Entity(id=caregiver_type.capitalize(), kind="character", type=caregiver_type))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        caretaker=caregiver.id,
    ))

    introduce(world, hero)
    setup(world, hero, caregiver, prize, activity)
    world.para()
    warning(world, caregiver, hero, activity, prize)
    humor_turn(world, hero, activity)
    world.para()
    lullaby_turn(world, caregiver, hero, prize)
    resolution(world, hero, caregiver, prize, activity)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, caregiver, activity, prize = f["hero"], f["caregiver"], f["activity"], f["prize"]
    return [
        f'Write a short myth for children about a little {hero.type} who loves to {activity.verb} and learns a lullaby can calm the trouble.',
        f"Tell a funny, repetitive story where {hero.id} keeps pecking, pecking, pecking until {caregiver.id} sings a lullaby.",
        f'Write a moonlit tale that includes the words "peck" and "lullaby" and ends with {prize.label} staying safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, caregiver, prize, activity = f["hero"], f["caregiver"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} keep doing in the grove?",
            answer=f"{hero.id} kept pecking, pecking, pecking at the sacred drum-stump until the echoes turned funny.",
        ),
        QAItem(
            question=f"Why did {caregiver.id} start singing a lullaby?",
            answer=f"{caregiver.id} sang a lullaby to calm the noise and keep {hero.pronoun('possessive')} {prize.label} from cracking.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id}'s pecking became gentle and musical, and the {prize.label} stayed whole.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lullaby?",
            answer="A lullaby is a soft song sung to help someone calm down or fall asleep.",
        ),
        QAItem(
            question="What does pecking mean?",
            answer="Pecking means tapping or striking quickly with a beak, often again and again.",
        ),
        QAItem(
            question="Why can repetition be funny in a story?",
            answer="Repetition can be funny because the same sound or action comes back so often that it feels bouncy, musical, or surprising.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic peck-and-lullaby storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--caregiver", choices=CAREGIVERS)
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
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize.")

    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or "peck"
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.caregiver:
        caregiver = args.caregiver
    else:
        caregiver = rng.choice(CAREGIVERS)
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(names)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, caregiver=caregiver)


def generate(params: StoryParams) -> StorySample:
    reasonability_check(params)
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.caregiver,
    )
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for place, act, prize, gender in combos:
            print(f"  {place:8} {act:6} {prize:10} {gender}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            for prize in PRIZES:
                p = StoryParams(
                    place=place,
                    activity="peck",
                    prize=prize,
                    name="Piko",
                    gender="boy",
                    caregiver="grandmother",
                )
                samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
