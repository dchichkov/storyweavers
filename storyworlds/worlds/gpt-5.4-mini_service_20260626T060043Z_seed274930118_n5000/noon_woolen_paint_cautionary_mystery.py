#!/usr/bin/env python3
"""
Storyworld: Noon Woolen Paint Cautionary Mystery

A small, standalone story world about a child, a cautious noon errand, a woolen
item, and a paint mystery that is solved by careful thinking instead of rash
guessing.

The world is built to feel a little like a mystery and to end with a caution:
pay attention to where paint can travel, and do not trust the obvious clue too
quickly.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    zone: set[str]
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
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
        return any(it.protective and region in getattr(it, "covers", set()) for it in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "art_room": Setting(place="the art room", indoor=True, affords={"paint"}),
    "studio": Setting(place="the studio", indoor=True, affords={"paint"}),
}

ACTIVITIES = {
    "paint": Activity(
        id="paint",
        verb="paint a picture",
        gerund="painting pictures",
        rush="grab the paint brush",
        mess="painted",
        soil="spattered with paint",
        keyword="paint",
        zone={"torso", "hands"},
        tags={"paint", "mystery", "caution"},
    )
}

PRIZES = {
    "woolen_scarf": Prize(
        label="woolen scarf",
        phrase="a warm woolen scarf",
        type="scarf",
        region="torso",
        genders={"girl", "boy"},
    ),
    "woolen_sweater": Prize(
        label="woolen sweater",
        phrase="a soft woolen sweater",
        type="sweater",
        region="torso",
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="apron",
        label="an apron",
        covers={"torso"},
        guards={"painted"},
        prep="put on an apron first",
        tail="put on the apron and returned to the easel",
    ),
    Gear(
        id="smock",
        label="a big smock",
        covers={"torso", "hands"},
        guards={"painted"},
        prep="slip on a big smock before touching the paint",
        tail="slipped on the smock and went back to the easel",
    ),
]

NAMES = ["Mina", "Theo", "Pia", "Eli", "Nora", "Jonah"]
TRAITS = ["curious", "careful", "quiet", "sharp-eyed", "gentle"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
compatible_fix(A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
valid_story(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), compatible_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.mess in gear.guards:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for activity_id in setting.affords:
            activity = ACTIVITIES[activity_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(activity, prize) and select_gear(activity, prize):
                    combos.append((place, activity_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} would not honestly threaten the {prize.label}, "
        f"or no gear in this world can protect it. Choose a different pairing.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: this {PRIZES[prize_id].label} is not restricted by gender here; try --gender {ok}.)"


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    # If a worn item is in the splash zone and not protected, it gets painted.
    for item in world.worn_items(actor):
        if item.protective or item.region not in world.zone:
            continue
        if world.covered(actor, item.region):
            continue
        sig = ("paint", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["painted"] = item.meters.get("painted", 0.0) + 1.0
        item.memes["worry"] = item.memes.get("worry", 0.0) + 1.0
        if narrate:
            world.say(f"{actor.id}'s {item.label} picked up paint specks.")
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1.0


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str, hero_gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, meters={}, memes={}))
    adult = world.add(Entity(id="Caretaker", kind="character", type="mother", label="the caretaker", meters={}, memes={}))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=adult.id,
        worn_by=hero.id,
        plural=prize_cfg.plural,
    ))

    # Act 1: quiet setup.
    world.say(f"At noon, {hero.id} was a {trait} child who liked noticing small things.")
    world.say(f"{hero.pronoun('subject').capitalize()} wore {prize.phrase} because the room felt chilly.")
    world.say(f"On the table sat a box of paint, and the lid was not quite closed.")

    # Act 2: the mystery.
    world.para()
    world.say(f"At noon, {hero.id} went to {setting.place} to {activity.verb}.")
    world.say(f"Then {hero.id} saw a strange little clue: one brush was wet, but the brightest jar was missing.")
    world.say(f"{hero.id} wanted to {activity.rush}, but {hero.pronoun('possessive')} {prize.label} could be ruined if the paint splashed.")
    world.say(f"That was the mystery: who had moved the paint, and why did the floor look freshly dotted?")
    _do_activity(world, hero, activity, narrate=False)

    # Act 3: cautious resolution.
    gear = select_gear(activity, prize)
    if not gear:
        raise StoryError(explain_rejection(activity, prize))
    gear_ent = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        protective=True,
        worn_by=hero.id,
    ))
    gear_ent.covers = set(gear.covers)
    world.para()
    world.say(f"{hero.id}'s {adult.label} frowned at the paint specks and said, \"Let's be careful.\"")
    world.say(f"She asked {hero.id} to {gear.prep}, and only then did the clue make sense.")
    world.say(f"The missing paint had not vanished at all; it had been on the brush, waiting for someone to notice the wet tip.")
    world.say(f"They {gear.tail}. Soon {hero.id} was {activity.gerund}, and {prize.label} stayed clean.")
    world.say(f"By the end, the mystery was solved: the paint was never stolen, just left open, and the lesson was to slow down at noon.")

    world.facts.update(
        hero=hero,
        adult=adult,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
        trait=trait,
        noon=True,
    )
    return world


# ---------------------------------------------------------------------------
# Story generation and QA
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    activity = f["activity"]
    return [
        f'Write a gentle mystery story for a young child set at noon and involving "{activity.keyword}".',
        f"Tell a cautionary story where {hero.id} worries about {prize.label} while trying to {activity.verb}.",
        f"Write a short mystery with paint, a woolen item, and a careful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    activity = f["activity"]
    adult = f["adult"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"What was the mystery in the story?",
            answer=f"The mystery was that the paint looked like it had gone missing, but it had only been left open and marked the floor with small dots.",
        ),
        QAItem(
            question=f"Why did {hero.id} need to be careful with {prize.label}?",
            answer=f"{hero.id} needed to be careful because paint could splash onto the woolen {prize.label} and leave it messy.",
        ),
        QAItem(
            question=f"What did {adult.label} tell {hero.id} to put on before the painting started?",
            answer=f"{adult.label} told {hero.id} to put on {gear.label} first so the {prize.label} would stay clean.",
        ),
        QAItem(
            question=f"What did {hero.id} do after the careful plan?",
            answer=f"{hero.id} went back to {activity.gerund}, and the woolen {prize.label} stayed safe while the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is paint?",
            answer="Paint is a colored liquid that can drip, smear, and leave marks if it is not handled carefully.",
        ),
        QAItem(
            question="What does woolen mean?",
            answer="Woolen means made from wool, which is a soft fiber that helps make warm clothes.",
        ),
        QAItem(
            question="What is noon?",
            answer="Noon is the middle of the day, when the sun is high in the sky.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = [f"type={e.type}"]
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if getattr(e, "covers", None):
            parts.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id}: " + ", ".join(parts))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Noon woolen paint cautionary mystery storyworld.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
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
        act = ACTIVITIES[args.activity]
        pr = PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize = rng.choice(sorted(combos))
    pr = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(pr.genders))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.trait)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for item in stories:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, activity, prize in valid_combos():
            params = StoryParams(
                place=place,
                activity=activity,
                prize=prize,
                name=NAMES[(hash((place, activity, prize)) % len(NAMES))],
                gender="girl" if prize == "woolen_scarf" else "boy",
                trait=TRAITS[(hash((prize, activity)) % len(TRAITS))],
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
