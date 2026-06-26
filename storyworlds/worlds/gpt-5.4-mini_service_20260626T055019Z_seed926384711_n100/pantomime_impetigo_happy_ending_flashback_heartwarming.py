#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/pantomime_impetigo_happy_ending_flashback_heartwarming.py
================================================================================================

A small, heartwarming storyworld about a child pantomime show, a bout of impetigo,
and a gentle family compromise that leads to a happy ending.

Premise
-------
A child is excited to perform in a pantomime. They are also dealing with impetigo:
a skin infection that makes their face or arms itchy, tender, and covered with
carefully treated spots. The child wants to rehearse and perform, but an adult
worries that the costume, touching, and backstage crowding could make the skin
feel worse.

Tension
-------
The child loves the show and feels disappointed when asked to rest or cover the
rash. A flashback can appear: the adult remembers a smaller moment of kindness
from earlier, or the child remembers how someone helped them before. This memory
softens the conflict and points toward a sensible plan.

Turn
----
They choose a safe way to keep the child included: washing hands, using ointment,
staying home from the crowded rehearsal, or helping with a quieter job like
choosing props, practicing lines softly, or making a paper sign for the stage.

Resolution
----------
The child still gets to be part of the pantomime, the impetigo is cared for, and
the story ends with a warm image of everyone smiling together.

The world is intentionally small and constraint-driven: fewer valid stories, but
each one should read like a complete, child-facing tale.
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

THERMAL_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    mess: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Concern:
    id: str
    label: str
    body_part: str
    symptom: str
    treatment: str
    safe_helper: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Compromise:
    id: str
    label: str
    prep: str
    tail: str
    protects_from: set[str] = field(default_factory=set)


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


def _who(world: World) -> list[Entity]:
    return [e for e in world.entities.values() if e.kind == "character"]


def _hold_in_check(world: World) -> list[str]:
    out: list[str] = []
    for actor in _who(world):
        if actor.meters.get("rash_spread", 0.0) < THERMAL_THRESHOLD:
            continue
        if actor.meters.get("resting", 0.0) < THERMAL_THRESHOLD:
            continue
        sig = ("rash_calms", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["itch"] = max(0.0, actor.meters.get("itch", 0.0) - 1.0)
        out.append(f"The medicine helped {actor.id} feel a little better.")
    return out


def _support_from_kindness(world: World) -> list[str]:
    out: list[str] = []
    for actor in _who(world):
        if actor.memes.get("comforted", 0.0) < THERMAL_THRESHOLD:
            continue
        sig = ("brighten", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["hope"] = actor.memes.get("hope", 0.0) + 1.0
        out.append(f"That made {actor.id} smile again.")
    return out


RULES = [_hold_in_check, _support_from_kindness]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTINGS = {
    "school_hall": Setting(place="the school hall", affords={"pantomime"}),
    "living_room": Setting(place="the living room", affords={"pantomime"}),
    "community_stage": Setting(place="the community stage", affords={"pantomime"}),
}

ACTIVITIES = {
    "pantomime": Activity(
        id="pantomime",
        verb="perform in the pantomime",
        gerund="performing in the pantomime",
        risk="the costume and crowd could bother the sore skin",
        mess="tired",
        keyword="pantomime",
        tags={"pantomime"},
    ),
}

CONCERNS = {
    "impetigo": Concern(
        id="impetigo",
        label="impetigo",
        body_part="face",
        symptom="sore, itchy spots",
        treatment="the ointment and clean bandage",
        safe_helper="wash hands carefully",
        tags={"impetigo", "skin", "medicine"},
    ),
}

COMPROMISES = {
    "quiet_help": Compromise(
        id="quiet_help",
        label="a quiet backstage job",
        prep="stay home from the crowded rehearsal and help with a quiet backstage job",
        tail="picked out props, practiced lines softly, and still felt part of the show",
        protects_from={"crowd", "costume", "scratching"},
    ),
    "rest_first": Compromise(
        id="rest_first",
        label="rest first",
        prep="rest at home, use the ointment, and skip the busiest part of rehearsal",
        tail="rested until the skin was calmer and then came back with a brighter smile",
        protects_from={"crowd", "scratching"},
    ),
}


@dataclass
class StoryParams:
    place: str
    activity: str
    concern: str
    compromise: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


NAMES = {
    "girl": ["Maya", "Nora", "Lily", "Zoe", "Ella"],
    "boy": ["Noah", "Ben", "Theo", "Finn", "Leo"],
}
TRAITS = ["brave", "gentle", "cheerful", "quiet", "eager", "kind"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming pantomime storyworld with impetigo and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--concern", choices=CONCERNS)
    ap.add_argument("--compromise", choices=COMPROMISES)
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


def _valid_combo(place: str, activity: str, concern: str, compromise: str) -> bool:
    return place in SETTINGS and activity in ACTIVITIES and concern in CONCERNS and compromise in COMPROMISES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.concern and not _valid_combo(args.place or "school_hall", args.activity, args.concern, args.compromise or "quiet_help"):
        raise StoryError("No reasonable story matches those options.")
    places = [args.place] if args.place else list(SETTINGS)
    acts = [args.activity] if args.activity else list(ACTIVITIES)
    concerns = [args.concern] if args.concern else list(CONCERNS)
    comps = [args.compromise] if args.compromise else list(COMPROMISES)
    combos = [(p, a, c, k) for p in places for a in acts for c in concerns for k in comps if _valid_combo(p, a, c, k)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, concern, compromise = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, concern=concern, compromise=compromise, name=name, gender=gender, parent=parent, trait=trait)


def _flashback(world: World, hero: Entity, parent: Entity) -> None:
    world.say(f"Flashback: {hero.id} remembered how {parent.pronoun('subject')} had once sat beside {hero.pronoun('object')} with a cool cloth and a patient voice.")
    hero.memes["comforted"] = hero.memes.get("comforted", 0.0) + 1.0


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    act = ACTIVITIES[params.activity]
    concern = CONCERNS[params.concern]
    comp = COMPROMISES[params.compromise]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    prop = world.add(Entity(id="script", type="thing", label="a paper script", owner=hero.id))
    hero.meters["itch"] = 1.0
    hero.meters["rash_spread"] = 1.0
    hero.memes["hope"] = 0.0

    world.say(f"{hero.id} was a {params.trait} little {params.gender} who loved {act.gerund} at {setting.place}.")
    world.say(f"{hero.id} had {concern.label}, with {concern.symptom} on {concern.body_part}, so {parent.pronoun('subject')} had to be careful.")
    world.say(f"That evening, {hero.id} still wanted to {act.verb}, because the show was about to begin.")
    world.para()
    world.say(f"At the hall, {hero.id} looked at the bright costumes and the painted stage.")
    world.say(f"{parent.pronoun('subject').capitalize()} worried that {act.risk}.")
    _flashback(world, hero, parent)
    world.say(f'\"I know,\" {hero.id} said softly, \"but I still want to be part of it.\"')
    world.say(f"{parent.pronoun('subject').capitalize()} nodded and said they could find a safer way.")
    world.para()
    if params.compromise == "quiet_help":
        hero.memes["comforted"] = hero.memes.get("comforted", 0.0) + 1.0
        world.say(f"They chose {comp.prep}.")
        world.say(f"{hero.id} {comp.tail}.")
    else:
        hero.meters["resting"] = 1.0
        world.say(f"They chose to {comp.prep}.")
        propagate(world)
        world.say(f"{hero.id} {comp.tail}.")
    world.para()
    world.say(f"By the time the curtain lifted, {hero.id} was smiling, {concern.treatment} had been used, and the room felt calm and kind.")
    world.say(f"After the applause, {hero.id} stood beside {parent.pronoun('object')} with a warm face and a happy heart.")
    world.facts.update(hero=hero, parent=parent, activity=act, concern=concern, compromise=comp, setting=setting, prop=prop)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent = f["hero"], f["parent"]
    act, concern = f["activity"], f["concern"]
    return [
        f'Write a heartwarming short story for a young child about {hero.id}, pantomime, and {concern.label}.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {parent.label} worries about {concern.label}.",
        f"Write a story with a flashback, a kind compromise, and a happy ending at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent = f["hero"], f["parent"]
    act, concern, comp = f["activity"], f["concern"], f["compromise"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at first?",
            answer=f"{hero.id} wanted to {act.verb} because the pantomime was exciting and the show was about to begin.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry?",
            answer=f"{parent.label} worried because {concern.label} could make the child itchy and sore, and the busy stage might bother the skin.",
        ),
        QAItem(
            question="What memory helped the family feel closer?",
            answer=f"In the flashback, {hero.id} remembered how {parent.pronoun('subject')} had once helped with a cool cloth and a patient voice.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They chose {comp.label}, which let {hero.id} stay involved while taking care of the skin gently.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is pantomime?",
            answer="Pantomime is a kind of theater show where people act out a story with costumes, big gestures, and fun characters.",
        ),
        QAItem(
            question="What is impetigo?",
            answer="Impetigo is a skin infection that can cause sore, itchy spots, and it usually needs careful cleaning and medicine.",
        ),
        QAItem(
            question="Why do people wash their hands before helping someone with a skin rash?",
            answer="Washing hands helps keep germs from spreading and helps protect the skin while it heals.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
activity(pantomime).
concern(impetigo).

valid_story(Place,Activity,Concern,Compromise) :-
    setting(Place), activity(Activity), concern(Concern), compromise(Compromise),
    Place = school_hall, Activity = pantomime, Concern = impetigo.

show_pair(A,C) :- valid_story(_,A,C,_).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", pid) for pid in SETTINGS]
    lines += [asp.fact("activity", aid) for aid in ACTIVITIES]
    lines += [asp.fact("concern", cid) for cid in CONCERNS]
    lines += [asp.fact("compromise", cid) for cid in COMPROMISES]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _asp_helpers():
    import asp
    return asp


def asp_verify() -> int:
    asp = _asp_helpers()
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {("school_hall", "pantomime", "impetigo", c) for c in COMPROMISES}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("clingo:", sorted(clingo_set))
    print("python:", sorted(python_set))
    return 1


def asp_valid_stories() -> list[tuple]:
    asp = _asp_helpers()
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


CURATED = [
    StoryParams(place="school_hall", activity="pantomime", concern="impetigo", compromise="quiet_help", name="Maya", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="community_stage", activity="pantomime", concern="impetigo", compromise="rest_first", name="Noah", gender="boy", parent="father", trait="kind"),
]


def explain_rejection() -> str:
    return "(No story: this tiny world only supports a child pantomime tale with impetigo and a kind compromise.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story combos:")
        for row in stories:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.activity} with {p.concern} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
