#!/usr/bin/env python3
"""
A small folk-tale story world about a treasured bead, a risky little errand,
and a kind fix that turns suspense into relief.

The world is deliberately tiny and constraint-checked:
- physical state: a bead can roll, drop, shine, or go missing
- emotional state: a child can grow hopeful, worried, or relieved
- the story is built from a simulated sequence, not from a frozen paragraph

This file follows the Storyweavers contract:
- stdlib storyworld script
- eager import of results containers
- lazy import of asp helpers
- StoryParams, registries, parser, resolve_params, generate, emit, main
- inline ASP twin and Python reasonableness gate
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
    worn_by: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    sound: str = ""


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    risk: str
    plural: bool = False


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)


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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def join_items(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + ", and " + items[-1]


def bead_name() -> str:
    return "bead"


SETTINGS = {
    "cottage": Setting(place="the cottage yard", affords={"thread", "chase"}, sound="the wind hummed in the grass"),
    "forest": Setting(place="the forest path", affords={"thread", "chase"}, sound="the leaves whispered overhead"),
    "brook": Setting(place="the brook bank", affords={"wash", "chase"}, sound="the water went trickle and tap"),
    "market": Setting(place="the market lane", affords={"thread", "chase"}, sound="the carts went clatter and creak"),
}

ACTIVITIES = {
    "thread": Activity(
        id="thread",
        verb="thread the bead onto a cord",
        gerund="threading the bead onto a cord",
        rush="snatch up the cord before it slipped away",
        mess="snagged",
        soil="scratched and dull",
        sound="click",
        tags={"bead", "string"},
    ),
    "wash": Activity(
        id="wash",
        verb="wash the bead in the brook",
        gerund="washing the bead in the brook",
        rush="reach down before the current tugged",
        mess="wet",
        soil="wet and muddy",
        sound="splish",
        tags={"bead", "water"},
    ),
    "chase": Activity(
        id="chase",
        verb="follow the rolling bead",
        gerund="chasing the rolling bead",
        rush="run after the bead over the stones",
        mess="lost",
        soil="lost in the grass",
        sound="skitter",
        tags={"bead", "rolling"},
    ),
}

PRIZES = {
    "bead": Prize(label="bead", phrase="a bright little bead", risk="lost"),
    "beads": Prize(label="beads", phrase="a handful of bright beads", risk="lost", plural=True),
}

FIXES = [
    Fix(
        id="dish",
        label="a wooden dish",
        prep="set the bead in a wooden dish",
        tail="placed the bead in a wooden dish",
        guards={"lost", "wet"},
    ),
    Fix(
        id="pouch",
        label="a cloth pouch",
        prep="tuck the bead into a cloth pouch",
        tail="tucked the bead into a cloth pouch",
        guards={"lost", "snagged"},
    ),
    Fix(
        id="tray",
        label="a shallow tray",
        prep="keep the bead on a shallow tray",
        tail="kept the bead on a shallow tray",
        guards={"lost", "wet", "snagged"},
    ),
]

GIRL_NAMES = ["Mira", "Talia", "Lina", "Nessa", "Runa", "Ona"]
BOY_NAMES = ["Perrin", "Jory", "Tobin", "Marek", "Niko", "Eden"]
TRAITS = ["gentle", "bright-eyed", "curious", "kind", "steady", "soft-spoken"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return activity.mess == prize.risk or prize.risk in activity.tags or activity.id == "chase"


def select_fix(activity: Activity, prize: Prize) -> Optional[Fix]:
    for fx in FIXES:
        if prize.risk in fx.guards and activity.mess in fx.guards:
            return fx
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_fix(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not have a sensible kind fix for {prize.label}. "
        f"Try a different activity or prize.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: {PRIZES[prize_id].label} is not a typical {gender}'s item in this tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale bead story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_fix(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    if args.gender and args.prize:
        if args.gender == "girl" and args.prize == "beads":
            pass
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, trait=trait)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {hero.meters.get('age', 0) or 'little'} {hero.memes.get('trait_word', 'child')} who listened closely to old stories.")


def tell_story(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={"age": 1}, memes={"trait_word": params.trait}))
    parent_type = "mother" if params.gender == "girl" else "father"
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(id="prize", type="bead" if params.prize == "bead" else "beads", label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner=hero.id, caretaker=parent.id, plural=PRIZES[params.prize].plural))
    act = ACTIVITIES[params.activity]

    hero.memes["hope"] = 1
    world.say(f"In {world.setting.place}, {hero.id} found {prize.phrase} in an old bowl.")
    world.say(f"{hero.pronoun().capitalize()} treasured the bead, because it had once belonged to a kindly grandmother and shone like a drop of dawn.")

    world.para()
    world.say(f"One day, {hero.id} wanted to {act.verb}.")
    world.say(f"{world.setting.sound.capitalize()}, and {act.sound}, and for a moment the little bead looked ready to dance away.")
    hero.memes["suspense"] = 1
    if act.id == "chase":
        prize.meters = {"rolling": 1}
        world.say(f"The bead went {act.sound}-skitter over the stones, and everyone held a breath.")
    elif act.id == "wash":
        prize.meters = {"wet": 1}
        world.say(f"The bead flashed in the brook, but the current made it tremble in place.")
    else:
        prize.meters = {"snagged": 1}
        world.say(f"The cord caught on a twig, and the bead gave a tiny click.")

    world.para()
    fx = select_fix(act, prize)
    if not fx:
        raise StoryError("No compatible kind fix exists for this story.")
    world.say(f"{parent.pronoun('possessive').capitalize()} {parent.label} looked close and said, \"Easy now. We can {fx.prep}.\"")
    world.say(f"That was the kind way: not a shove, not a scold, just careful hands and a soft voice.")
    hero.memes["trust"] = 1
    hero.memes["suspense"] = 0.0
    world.say(f"So {hero.id} nodded, and together they {fx.tail}.")
    world.say(f"The bead stayed safe at last, bright as a star in the dark of a pocket, and {hero.id} smiled as the tale ended well.")

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=act, fix=fx, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a short folk tale for a small child about a {hero.type} named {hero.id} and a treasured {prize.label}.',
        f"Tell a gentle story where someone wants to {act.verb} but must use a kind fix to keep the {prize.label} safe.",
        f'Write a suspenseful but warm story that includes the word "bead" and ends with relief.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, prize, act, fix = f["hero"], f["prize"], f["activity"], f["fix"]
    return [
        QAItem(
            question=f"What did {hero.id} treasure in the story?",
            answer=f"{hero.id} treasured {prize.phrase}, the little bead that had belonged to a kindly grandmother.",
        ),
        QAItem(
            question=f"What was the risky thing {hero.id} wanted to do?",
            answer=f"{hero.id} wanted to {act.verb}, which made the bead seem ready to slip away.",
        ),
        QAItem(
            question=f"How did the grown-up keep the bead safe?",
            answer=f"They used {fix.label} and careful hands, so the bead stayed safe while {hero.id} followed through with the plan.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a bead?", answer="A bead is a small, often round piece that people thread, wear, or use to decorate things."),
        QAItem(question="Why do people use a pouch?", answer="A pouch helps carry small things so they do not fall out or get lost."),
        QAItem(question="What does suspense mean in a story?", answer="Suspense is the worried, waiting feeling that happens when something important might go wrong."),
        QAItem(question="What are sound effects in a story?", answer="Sound effects are words like click, skitter, or splish that help you hear the action in your mind."),
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
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cottage", activity="chase", prize="bead", name="Mira", gender="girl", trait="kind"),
    StoryParams(place="forest", activity="thread", prize="bead", name="Perrin", gender="boy", trait="curious"),
    StoryParams(place="brook", activity="wash", prize="beads", name="Talia", gender="girl", trait="gentle"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), risky(A,P).
has_fix(A,P) :- prize_at_risk(A,P), fix(F), guards(F, wet), guards(F, snagged).
valid(Place,A,P) :- setting(Place), affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risky", aid, a.mess))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("risky", pid, p.risk))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for g in sorted(fx.guards):
            lines.append(asp.fact("guards", fx.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
