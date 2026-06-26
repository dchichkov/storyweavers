#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/muddy_rhyme_anorexia_rhyme_rhyming_story.py
===============================================================================================================

A tiny, classical story world about a child named Rhyme, a muddy day, a
gentle rhyme contest, and a careful worry about health.

Seed premise:
- muddy
- rhyme
- anorexia

The story is built from a small simulation:
1) Rhyme loves making rhymes.
2) Rhyme wants to splash in muddy puddles while wearing a favorite outfit.
3) A parent worries about the outfit and about Rhyme having skipped meals.
4) The parent gently redirects to a safe, cheerful plan.
5) Rhyme gets help, changes gear, and the day ends with a clean, happy image.

This script follows the shared Storyworld contract:
- `StoryParams`
- registries
- `build_parser`
- `resolve_params`
- `generate`
- `emit`
- `main`

It also includes:
- a Python reasonableness gate
- inline `ASP_RULES`
- `asp_facts()`
- `--verify`, `--asp`, `--show-asp`

The prose style aims to stay close to a classic Rhyming Story: simple, child-facing,
concrete, and musical.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def emo(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def bump_m(self, key: str, amt: float = 1.0) -> None:
        self.meters[key] = self.m(key) + amt

    def bump_e(self, key: str, amt: float = 1.0) -> None:
        self.memes[key] = self.emo(key) + amt

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
    place: str = "the garden"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    weather: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# Registries
SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, affords={"mud", "rhyme"}),
    "yard": Setting(place="the backyard", indoor=False, affords={"mud", "rhyme"}),
    "porch": Setting(place="the porch", indoor=False, affords={"rhyme"}),
}

ACTIVITIES = {
    "mud": Activity(
        id="mud",
        verb="stomp in the mud",
        gerund="stomping in the mud",
        rush="dash to the muddy patch",
        mess="muddy",
        soil="muddy and brown",
        zone={"feet", "legs"},
        weather="rainy",
        keyword="muddy",
        tags={"muddy"},
    ),
    "rhyme": Activity(
        id="rhyme",
        verb="say a rhyme",
        gerund="making up rhymes",
        rush="run to the rhyme mat",
        mess="none",
        soil="",
        zone=set(),
        weather="",
        keyword="rhyme",
        tags={"rhyme"},
    ),
}

PRIZES = {
    "shoes": Prize(
        label="shoes",
        phrase="bright white shoes",
        type="shoes",
        region="feet",
        plural=True,
    ),
    "dress": Prize(
        label="dress",
        phrase="a neat little dress",
        type="dress",
        region="legs",
        genders={"girl"},
    ),
    "shirt": Prize(
        label="shirt",
        phrase="a clean blue shirt",
        type="shirt",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="boots",
        label="mud boots",
        covers={"feet"},
        guards={"muddy"},
        prep="put on the mud boots",
        tail="came back wearing the mud boots",
        plural=True,
    ),
    Gear(
        id="playclothes",
        label="play clothes",
        covers={"feet", "legs", "torso"},
        guards={"muddy"},
        prep="change into play clothes",
        tail="changed into the play clothes",
        plural=True,
    ),
]

GIRL_NAMES = ["Rhyme", "Mia", "Lily", "Nora", "Ava"]
BOY_NAMES = ["Finn", "Leo", "Ben", "Noah"]
TRAITS = ["cheerful", "curious", "bouncy", "gentle"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


THRESHOLD = 1.0


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return bool(activity.zone and prize.region in activity.zone)


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} would not touch the {prize.label}, "
            f"so there is no honest mess and no reason for a compromise.)"
        )
    return (
        f"(No story: there is no gear here that can protect the {prize.label} "
        f"from {activity.gerund}.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s item here; try {ok}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyme-and-mud storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
        and (args.gender is None or args.gender in PRIZES[c[2]].genders)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def _do_mud(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.bump_m(activity.mess)
    actor.bump_e("joy")
    if narrate:
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.region in world.zone and not world.covered(actor, item.region):
                item.bump_m(activity.mess)
                item.bump_m("dirty")
                world.say(f"{actor.pronoun('possessive').capitalize()} {item.label} got muddy.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, hero_traits: list[str], parent_type: str) -> World:
    world = World(setting)
    world.weather = activity.weather
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", meters={}, memes={}))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    hero.bump_e("love_rhyme")
    hero.bump_e("love_mud", 0.0)
    world.say(f"{hero.id} was a {hero_traits[0]} little {hero.type} who loved to make a rhyme.")
    world.say(f"{hero.id} liked to tap and clap, and to grin while the words would chime.")
    world.say(f"One day {hero.id}'s {parent.label_word if hasattr(parent, 'label_word') else 'parent'} bought {hero.pronoun('object')} {prize.phrase}.")
    prize.worn_by = hero.id
    world.say(f"{hero.id} wore {prize.it()} and felt as bright as a kite in the sky.")

    world.para()
    world.say(f"Then {hero.id} went to {world.setting.place}.")
    world.say(f"{hero.id} wanted to {activity.verb}, and {activity.gerund} made the day feel light and spry.")
    if activity.id == "mud":
        world.say(f"The mud was soft and squishy, with a shiny brown gleam.")
    if prize.region:
        world.say(f"But the {prize.label} sat on {prize.region}, and that made a mess a bad little dream.")

    world.say(f"{hero.id}'s {parent.label_word if hasattr(parent, 'label_word') else 'parent'} frowned and saw the splashy track.")
    world.say(f'"If you go now," {parent.pronoun("subject")} said, "your {prize.label} will come back muddy and black."')
    hero.bump_e("worry")
    hero.bump_e("defiance")
    world.say(f"{hero.id} stamped one foot and tried to {activity.rush}.")
    world.say(f"But {parent.pronoun('subject').capitalize()} held up a hand and said, " + '"Let us find a kinder way to play and stay bright."')

    # gentle health beat: the parent notices skipped meals and offers help
    hero.bump_e("low_spirit")
    world.say(
        f"At lunch time, {parent.pronoun('subject')} also noticed {hero.id} had not eaten much at all, "
        f"and that made the {parent.label_word if hasattr(parent, 'label_word') else 'parent'} worry in a careful, loving way."
    )
    world.say(
        f"'{hero.id}, we should talk to the doctor and get help if food feels too hard,' {parent.pronoun('subject')} said softly, "
        f"because anorexia is a serious sickness that can make eating feel very difficult."
    )
    hero.bump_e("comfort")
    hero.bump_e("helped")

    world.para()
    gear_def = None
    if prize.region in {"feet", "legs", "torso"}:
        gear_def = select_gear(activity, prize)
    if gear_def:
        gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, protective=True, covers=set(gear_def.covers), plural=gear_def.plural))
        gear.worn_by = hero.id
        world.say(f"Then they chose a safe switch and {gear_def.prep}.")
        world.say(f"{hero.id} smiled, because {gear_def.label} would guard the {prize.label} from the muddy fun.")
        _do_mud(world, hero, activity, narrate=True)
        world.say(f"{hero.id} kept {prize.it()} clean and still got the joy of the day.")
        world.say(f"With the doctor's help and a warm plan, {hero.id} could rhyme again and feel okay.")
    else:
        world.say(f"They chose a calm new game, and the muddy day turned into a rhyme parade.")

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear_def)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short rhyming story for a child named {hero.id} on a muddy day.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label} worries about {prize.phrase}.",
        f"Write a simple story that includes the word 'anorexia' in a caring, age-safe way and ends with a safe plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.type} who loves rhyme and gentle play.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}, because {act.gerund} felt fun and bouncy.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {prize.label}?",
            answer=f"{parent.label.capitalize()} worried because muddy play could make the {prize.label} come back {act.soil}.",
        ),
        QAItem(
            question=f"Why did the parent mention a doctor?",
            answer="The parent wanted help because anorexia is a serious sickness that can make eating feel very hard.",
        ),
        QAItem(
            question=f"What helped the day end well?",
            answer=f"A safe change of gear and a caring plan helped {hero.id} stay clean, rhyme happily, and feel better.",
        ),
    ]


KNOWLEDGE = {
    "muddy": [
        ("What is mud?", "Mud is wet dirt. It can stick to shoes and clothes and leave brown marks."),
    ],
    "rhyme": [
        ("What is a rhyme?", "A rhyme is a word sound that matches another word sound, like cat and hat."),
    ],
    "anorexia": [
        ("What is anorexia?", "Anorexia is a serious illness that can make a person afraid to eat or feel unable to eat enough."),
    ],
    "boots": [
        ("What are boots for?", "Boots help protect feet and shoes from water, mud, and cold ground."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ["muddy", "rhyme", "anorexia", "boots"]:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="yard", activity="mud", prize="shoes", name="Rhyme", gender="girl", parent="mother", trait="cheerful"),
    StoryParams(place="garden", activity="mud", prize="dress", name="Mia", gender="girl", parent="father", trait="gentle"),
]


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
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


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        [params.trait, "stubborn"],
        params.parent,
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

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
