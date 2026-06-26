#!/usr/bin/env python3
"""
A small storyworld about a child, a mistaken twist, and a warm reconciliation.

Premise:
A child wants to help a multitude of tiny garden visitors. Their overalls are
special, and the child thinks the visitors might ruin them. A mistaken turn
creates hurt feelings, then a gentle apology and a shared task bring everyone
back together.

The world model tracks physical state in meters and emotional state in memes.
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
# World data
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the garden"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    mess: str
    zone: set[str]
    keyword: str
    twist: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Compromise:
    id: str
    label: str
    phrase: str
    fits: set[str]
    soothes: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the garden", affords={"help", "feed"}),
    "porch": Setting(place="the porch", affords={"help"}),
    "yard": Setting(place="the yard", affords={"help", "feed"}),
}

ACTIVITIES = {
    "help_bees": Activity(
        id="help_bees",
        verb="help the bees",
        gerund="helping the bees",
        risk="sting",
        mess="pollen",
        zone={"hands", "torso"},
        keyword="bees",
        twist="a buzzing misunderstanding",
    ),
    "feed_birds": Activity(
        id="feed_birds",
        verb="feed the birds",
        gerund="feeding the birds",
        risk="spill",
        mess="crumbs",
        zone={"hands"},
        keyword="birds",
        twist="a crumbly surprise",
    ),
    "gather_flowers": Activity(
        id="gather_flowers",
        verb="gather flowers",
        gerund="gathering flowers",
        risk="tear",
        mess="mud",
        zone={"hands", "legs"},
        keyword="flowers",
        twist="a muddy little detour",
    ),
}

PRIZES = {
    "overalls": Prize(
        label="overalls",
        phrase="a pair of soft blue overalls",
        type="overalls",
        region="torso",
        plural=True,
    ),
    "shirt": Prize(
        label="shirt",
        phrase="a bright yellow shirt",
        type="shirt",
        region="torso",
    ),
    "boots": Prize(
        label="boots",
        phrase="sturdy little boots",
        type="boots",
        region="feet",
        plural=True,
    ),
}

COMPROMISES = [
    Compromise(
        id="apron",
        label="an apron",
        phrase="a clean apron",
        fits={"torso"},
        soothes="kept the clothes tidy",
    ),
    Compromise(
        id="mittens",
        label="soft mittens",
        phrase="soft mittens",
        fits={"hands"},
        soothes="kept the hands clean",
        plural=True,
    ),
    Compromise(
        id="patches",
        label="patch pockets",
        phrase="patch pockets",
        fits={"torso"},
        soothes="gave everyone a way to share small treasures",
        plural=True,
    ),
]

NAMES = ["Mia", "Noah", "Lila", "Eli", "Nora", "Finn"]
TRAITS = ["gentle", "curious", "cheerful", "patient", "kind"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or prize.region == "torso" and activity.id == "help_bees"


def select_compromise(activity: Activity, prize: Prize) -> Optional[Compromise]:
    for comp in COMPROMISES:
        if prize.region in comp.fits:
            return comp
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not reasonably threaten {prize.label}. "
        f"Try a prize worn on the {sorted(activity.zone)} or a different activity.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: {PRIZES[prize_id].label} is not a typical {gender}'s item here.)"


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, plural=False))
    friend = world.add(Entity(id="Friend", kind="character", type="child", label="the friend"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        plural=prize_cfg.plural,
        owner=hero.id,
        caretaker=friend.id,
    ))

    # Act 1
    world.say(f"{name} was a {trait} little {gender} who loved the garden and noticed every tiny thing.")
    world.say(f"{hero.pronoun('subject').capitalize()} loved {activity.gerund}, especially when a multitude of tiny visitors gathered nearby.")
    world.say(f"One sunny afternoon, {name} wore {hero.pronoun('possessive')} {prize.label} and went to {setting.place}.")
    world.say(f"{prize.phrase} felt special to {name}, because it was the kind of thing that made the day feel safe and bright.")

    # Act 2: twist
    world.para()
    world.say(
        f"At {setting.place}, a multitude of bees and birds arrived at once, and {activity.twist} made {name} jump back."
    )
    world.say(
        f"{name} worried that {activity.gerund} would leave {hero.pronoun('possessive')} {prize.label} dirty or torn."
    )
    world.say(
        f"So {name} folded {hero.pronoun('possessive')} arms and said {activity.risk and '"No more!"'}"
    )
    world.say(
        f"But that sounded harsher than {name} meant, and the little crowd went quiet."
    )

    # Act 3: reconciliation
    world.para()
    comp = select_compromise(activity, prize)
    if comp is None:
        raise StoryError(explain_rejection(activity, prize))
    world.say(
        f"{name} took a slow breath, apologized to the tiny visitors, and admitted that the scare was only a mistake."
    )
    world.say(
        f"The friend smiled and offered {comp.label}, which {comp.soothes}."
    )
    world.say(
        f"With {comp.label} on, {name} could go back to {activity.gerund}, and the multitude stayed happily nearby."
    )
    world.say(
        f"By the end, {name} was laughing again, {prize.phrase} was still neat, and the garden felt warm with reconciliation."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        activity=activity,
        setting=setting,
        compromise=comp,
        trait=trait,
        resolved=True,
        twist=activity.twist,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    activity = f["activity"]
    return [
        f'Write a heartwarming story about a child named {hero.id}, a multitude of tiny visitors, and {prize.label}.',
        f"Tell a gentle story where {hero.id} worries that {activity.verb} will ruin {hero.pronoun('possessive')} {prize.label}.",
        f'Write a story with a twist and a reconciliation, using the word "multitude".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    activity = f["activity"]
    comp = f["compromise"]
    qa = [
        QAItem(
            question=f"What did {hero.id} love to do in the garden?",
            answer=f"{hero.id} loved {activity.gerund}, especially with a multitude of tiny visitors nearby.",
        ),
        QAItem(
            question=f"What special thing was {hero.id} wearing?",
            answer=f"{hero.id} was wearing {prize.phrase}. It mattered because it was a favorite piece of clothing.",
        ),
        QAItem(
            question="What caused the twist in the story?",
            answer=f"A multitude of bees and birds arrived at once, and {activity.twist} startled {hero.id}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"{hero.id} apologized, accepted {comp.label}, and went back to {activity.gerund}. "
                f"The story ended with everyone feeling close again."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does multitude mean?",
            answer="A multitude means a very large number of things or people all together.",
        ),
        QAItem(
            question="What are overalls?",
            answer="Overalls are clothes with a bib and straps that cover the front of the body and often the legs.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and become friendly again after a disagreement.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what you expected to happen next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
has_fix(P) :- prize(P), worn_on(P,torso), fits(_,torso).
has_fix(P) :- prize(P), worn_on(P,hands), fits(_,hands).

valid(S,A,P) :- setting(S), affords(S,A), prize(P), prize_at_risk(A,P), has_fix(P).
valid_story(S,A,P,G) :- valid(S,A,P), wears(G,P).
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
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for c in COMPROMISES:
        lines.append(asp.fact("compromise", c.id))
        for f in sorted(c.fits):
            lines.append(asp.fact("fits", c.id, f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid in setting.affords:
            act = ACTIVITIES[aid]
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_compromise(act, prize):
                    combos.append((sid, aid, pid))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld with a twist and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        prize = PRIZES[args.prize]
        if not prize_at_risk(act, prize) or not select_compromise(act, prize):
            raise StoryError(explain_rejection(act, prize))
        if args.gender and args.gender not in prize.genders:
            raise StoryError(explain_gender(args.prize, args.gender))
    combos = [
        (s, a, p)
        for s, a, p in valid_combos()
        if (args.setting is None or s == args.setting)
        and (args.activity is None or a == args.activity)
        and (args.prize is None or p == args.prize)
        and (args.gender is None or args.gender in PRIZES[p].genders)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, prize = rng.choice(sorted(combos))
    prize_cfg = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(prize_cfg.genders))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, activity=activity, prize=prize, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.trait)
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
        raise SystemExit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):\n")
        for s, a, p in triples:
            genders = sorted(g for (ss, aa, pp, g) in stories if (ss, aa, pp) == (s, a, p))
            print(f"  {s:8} {a:14} {p:8} [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("garden", "help_bees", "overalls", "Mia", "girl", "gentle"),
            StoryParams("yard", "feed_birds", "shirt", "Noah", "boy", "curious"),
            StoryParams("porch", "gather_flowers", "overalls", "Lila", "girl", "cheerful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
