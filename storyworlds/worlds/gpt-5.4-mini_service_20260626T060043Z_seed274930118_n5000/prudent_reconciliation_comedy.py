#!/usr/bin/env python3
"""
storyworlds/worlds/prudent_reconciliation_comedy.py
====================================================

A compact story world about a careful, funny misunderstanding that ends in
reconciliation.

Premise:
- A child loves a silly comedy prop.
- Another child worries the prop will get ruined or cause trouble.
- A prudent adult or friend suggests a small, sensible fix.
- The children reconcile and finish with laughter.

The domain is intentionally small: a few settings, a few props, and a few
compatible compromises. The simulated world tracks both physical state
(meters) and feelings (memes), and the prose is generated from that state
rather than from a fixed paragraph template.

The style target is comedy: playful mishaps, concrete objects, and a warm
ending where everyone can laugh together.
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
# Shared domain model
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
    held_by: Optional[str] = None
    fragile: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    place: str
    indoors: bool
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
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    label: str
    phrase: str
    region: str
    mess_risk: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    protects: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        c.zone = set(self.zone)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"pie", "silly_string"}),
    "backyard": Setting(place="the backyard", indoors=False, affords={"pie", "silly_string"}),
    "stage": Setting(place="the school stage", indoors=True, affords={"pie", "joke_book"}),
}

ACTIVITIES = {
    "pie": Activity(
        id="pie",
        verb="use the cream pie prop",
        gerund="using the cream pie prop",
        rush="grab the pie prop",
        mess="sticky",
        soil="sticky and silly",
        keyword="pie",
        tags={"pie", "sticky", "comedy"},
    ),
    "silly_string": Activity(
        id="silly_string",
        verb="spray the silly string",
        gerund="spraying silly string",
        rush="spray the string everywhere",
        mess="stringy",
        soil="covered in silly string",
        keyword="string",
        tags={"string", "comedy"},
    ),
    "joke_book": Activity(
        id="joke_book",
        verb="read jokes aloud",
        gerund="reading jokes aloud",
        rush="snatch the joke book",
        mess="creased",
        soil="creased and wrinkled",
        keyword="jokes",
        tags={"book", "comedy"},
    ),
}

PROPS = {
    "pie_plate": Prop(
        label="pie prop",
        phrase="a foam pie prop with a bright crust",
        region="hands",
        mess_risk="sticky",
    ),
    "joke_book": Prop(
        label="joke book",
        phrase="a funny joke book with a red cover",
        region="hands",
        mess_risk="creased",
    ),
    "string_can": Prop(
        label="silly string can",
        phrase="a can of silly string",
        region="hands",
        mess_risk="stringy",
    ),
}

FIXES = [
    Fix(
        id="napkins",
        label="a stack of napkins",
        prep="put a stack of napkins on the table first",
        tail="set the prop down on the napkins and took turns",
        guards={"sticky"},
        protects={"hands"},
    ),
    Fix(
        id="timer",
        label="a kitchen timer",
        prep="set a kitchen timer for each turn",
        tail="kept the timer ticking and shared the prop",
        guards={"sticky", "stringy", "creased"},
        protects={"hands"},
    ),
    Fix(
        id="bookstand",
        label="a little bookstand",
        prep="set the joke book on a little bookstand",
        tail="used the bookstand and read the jokes without wrinkling the pages",
        guards={"creased"},
        protects={"hands"},
    ),
]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prop: str
    name: str
    gender: str
    friend_name: str
    parent: str
    trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mia", "Zoe", "Lily", "Nora", "Ava", "Ella", "Maya"]
BOY_NAMES = ["Leo", "Finn", "Max", "Theo", "Ben", "Noah", "Sam"]
FRIEND_NAMES = ["Pip", "Benny", "June", "Toby", "Ivy", "Dot"]
TRAITS = ["prudent", "cheerful", "curious", "silly", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prop_id, prop in PROPS.items():
                if prop.mess_risk == act.mess:
                    for fix in FIXES:
                        if act.mess in fix.guards and prop.region in fix.protects:
                            out.append((place, act_id, prop_id))
    return out


def explain_rejection(activity: Activity, prop: Prop) -> str:
    return (
        f"(No story: {activity.gerund} would threaten the {prop.label}, but no "
        f"prudent fix in this tiny world both handles {activity.mess} and protects "
        f"the {prop.region}.)"
    )


def explain_gender(prop_id: str, gender: str) -> str:
    return (
        f"(No story: this prop is not a typical {gender}'s fit here; try one of "
        f"{sorted(PROPS[prop_id].genders)}.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def prudence_gate(activity: Activity, prop: Prop) -> Optional[Fix]:
    for fix in FIXES:
        if activity.mess in fix.guards and prop.region in fix.protects:
            return fix
    return None


def predict(world: World, hero: Entity, activity: Activity, prop_id: str) -> dict[str, object]:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    prop = sim.entities.get(prop_id)
    return {"soiled": bool(prop and prop.meters.get("dirty", 0) >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = {"hands"}
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["excitement"] = actor.memes.get("excitement", 0) + 1
    for ent in world.entities.values():
        if ent.held_by == actor.id and ent.kind == "thing":
            if ent.fragile and activity.mess == ent.mess_risk:
                ent.meters["dirty"] = ent.meters.get("dirty", 0) + 1
                ent.meters[activity.mess] = ent.meters.get(activity.mess, 0) + 1
                if narrate:
                    world.say(f"{actor.pronoun('possessive').capitalize()} {ent.label} got messy.")
    if narrate:
        world.say(f"{actor.pronoun().capitalize()} started {activity.gerund}.")


def maybe_concern(world: World, parent: Entity, hero: Entity, activity: Activity, prop: Entity) -> bool:
    pred = predict(world, hero, activity, prop.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"If you {activity.verb}, the {prop.label} could end up {activity.soil}," '
        f"{parent.pronoun('possessive')} {parent.type} said."
    )
    return True


def tell(world: World, hero: Entity, friend: Entity, parent: Entity, activity: Activity, prop: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait', 'prudent')} {hero.type} who loved comedy."
    )
    world.say(
        f"{hero.id} and {friend.id} both loved {activity.gerund} with {prop.phrase}."
    )
    world.say(
        f"One day at {world.setting.place}, they found {prop.phrase} and got ready for a funny scene."
    )

    world.para()
    world.say(
        f"{hero.id} wanted to {activity.verb}, but {friend.id} worried the prop would get ruined."
    )
    maybe_concern(world, parent, hero, activity, prop)
    world.say(
        f"{hero.id} reached for it anyway, and {friend.id} made a tiny face that said, 'Uh-oh.'"
    )

    world.para()
    world.say(
        f"Then {parent.id} had a {hero.memes.get('trait', 'prudent')} idea: {world.facts['fix'].prep}."
    )
    fix: Fix = world.facts["fix"]  # type: ignore[assignment]
    world.say(
        f"{hero.id} blinked, then laughed. {friend.id} laughed too, because it was a sensible kind of funny."
    )
    hero.memes["conflict"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    world.say(
        f"They {fix.tail}, and the joke turned from a squabble into a shared giggle."
    )

    if activity.id == "pie":
        world.say(
            f"The pie stayed fluffy, the table stayed clean, and {friend.id} got the first silly bow."
        )
    elif activity.id == "silly_string":
        world.say(
            f"The string sparkled in neat curls instead of tangling in a knot."
        )
    else:
        world.say(
            f"The joke book stayed smooth, and the best punch line landed right on time."
        )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    prop = PROPS[params.prop]

    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={},
        memes={"trait": 1.0, "joy": 0.0, "conflict": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type="boy" if params.gender == "girl" else "girl",
        memes={"joy": 0.0, "worry": 0.0},
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))

    prop_ent = world.add(Entity(
        id=prop.label,
        kind="thing",
        type="thing",
        label=prop.label,
        phrase=prop.phrase,
        owner=params.name,
        caretaker="Parent",
        held_by=params.name,
        fragile=True,
    ))
    prop_ent.mess_risk = prop.mess_risk  # type: ignore[attr-defined]

    fix = prudence_gate(activity, prop)
    if fix is None:
        raise StoryError(explain_rejection(activity, prop))
    world.facts["fix"] = fix

    world.say(
        f"{params.name} was a {params.trait} little {params.gender} who liked jokes that made everybody snort."
    )
    world.say(
        f"{params.friend_name} liked the same prop, and the two friends always reached for it at the same time."
    )
    world.say(
        f"{params.parent} kept a careful eye on the prop because comedy is funnier when nothing breaks."
    )

    world.para()
    tell(world, hero, friend, parent, activity, prop_ent)

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        activity=activity,
        prop=prop_ent,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    activity: Activity = f["activity"]  # type: ignore[assignment]
    prop: Entity = f["prop"]  # type: ignore[assignment]
    fix: Fix = f["fix"]  # type: ignore[assignment]
    return [
        f'Write a short comedy story for a young child about "{activity.keyword}" and a prudent compromise.',
        f"Tell a gentle, funny story where {hero.id} wants to {activity.verb} but a friend worries about {prop.label}, and they reconcile.",
        f"Write a child-facing story that includes the word 'prudent' and ends with everyone laughing together.",
        f"Create a playful reconciliation story in {world.setting.place} using {fix.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    activity: Activity = f["activity"]  # type: ignore[assignment]
    prop: Entity = f["prop"]  # type: ignore[assignment]
    fix: Fix = f["fix"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Why did {friend.id} worry when {hero.id} wanted to {activity.verb}?",
            answer=(
                f"{friend.id} worried because the {prop.label} could get {activity.soil}. "
                f"The joke was funny, but the prop was not a toy that liked rough handling."
            ),
        ),
        QAItem(
            question=f"What was the prudent idea that helped the friends reconcile?",
            answer=(
                f"{parent.id} suggested {fix.prep}. That was prudent because it let the friends share "
                f"the prop without ruining it."
            ),
        ),
        QAItem(
            question=f"How did the story end after {hero.id} and {friend.id} settled their squabble?",
            answer=(
                f"They used {fix.label} and stayed happy. By the end they were laughing together, and "
                f"the {prop.label} was still in good shape."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "pie": [
        QAItem(
            question="What is a pie prop in a comedy show?",
            answer="A pie prop is a pretend pie used for a joke, so it can make people laugh without being a real mess.",
        )
    ],
    "string": [
        QAItem(
            question="What is silly string used for?",
            answer="Silly string is often used for playful celebrations because it sprays out in bright, twisty strands.",
        )
    ],
    "book": [
        QAItem(
            question="Why do people use a bookstand?",
            answer="A bookstand holds a book open so the pages do not bend or wrinkle while someone reads.",
        )
    ],
    "comedy": [
        QAItem(
            question="What makes a comedy scene funny?",
            answer="Comedy scenes are funny when small problems, silly faces, or surprise ideas make people laugh.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    activity: Activity = f["activity"]  # type: ignore[assignment]
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in activity.tags:
            out.extend(items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
at_risk(A,P) :- mess_of(A,M), prop_risk(P,M).
good_fix(F,A,P) :- fix_guard(F,M), mess_of(A,M), fix_protects(F,R), prop_region(P,R).
valid(Place,A,P) :- affords(Place,A), at_risk(A,P), good_fix(_,A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), fits_gender(P,Gender).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("prop_risk", pid, p.mess_risk))
        lines.append(asp.fact("prop_region", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("fits_gender", pid, g))
    for fix in FIXES:
        lines.append(asp.fact("fix", fix.id))
        for g in sorted(fix.guards):
            lines.append(asp.fact("fix_guard", fix.id, g))
        for r in sorted(fix.protects):
            lines.append(asp.fact("fix_protects", fix.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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
        print(f"OK: clingo matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI / core API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Prudent reconciliation comedy storyworld."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    if args.activity and args.prop:
        act = ACTIVITIES[args.activity]
        prop = PROPS[args.prop]
        if not prudence_gate(act, prop):
            raise StoryError(explain_rejection(act, prop))
    if args.gender and args.prop and args.gender not in PROPS[args.prop].genders:
        raise StoryError(explain_gender(args.prop, args.gender))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prop is None or c[2] == args.prop)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, act_id, prop_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != name])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or "prudent"
    return StoryParams(place=place, activity=act_id, prop=prop_id, name=name, gender=gender,
                       friend_name=friend_name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print()
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v and k != "trait"}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"  {e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="kitchen", activity="pie", prop="pie_plate", name="Mia", gender="girl",
                friend_name="Pip", parent="mother", trait="prudent"),
    StoryParams(place="backyard", activity="silly_string", prop="string_can", name="Leo", gender="boy",
                friend_name="June", parent="father", trait="cheerful"),
    StoryParams(place="stage", activity="joke_book", prop="joke_book", name="Nora", gender="girl",
                friend_name="Toby", parent="father", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} valid combos ({len(stories)} with gender):")
        for place, act, prop in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prop))
            print(f"  {place:10} {act:12} {prop:12} [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
