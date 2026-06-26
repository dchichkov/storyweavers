#!/usr/bin/env python3
"""
youngster_bazooka_gymnast_quest_comedy.py
=========================================

A small comedy storyworld about a youngster, a foam bazooka, a gymnast,
and a quest that starts as a big boast and ends as a silly rescue.

Premise:
- A youngster wants to do a dramatic quest with a bazooka.
- The local gymnast knows how to do flips, balance, and make a plan.
- The bazooka is not a real weapon here; it is a harmless prop that shoots
  streamers, confetti, or bubbles in a playful show.

Tension:
- The youngster wants instant glory.
- The gymnast warns that the quest is impossible without practice and props.
- The youngster tries anyway and makes a mess of the stage.

Turn:
- The gymnast turns the whole mishap into a funny training quest.
- They learn to aim the prop, time the launch, and work as a team.

Resolution:
- The youngster completes the quest with the gymnast's help.
- The ending image proves the change: fewer spills, more applause, and a
  very silly heroic pose.

This world uses physical meters and emotional memes, and it includes a Python
reasonableness gate plus an inline ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# -----------------------------------------------------------------------------
# World model
# -----------------------------------------------------------------------------
THRESHOLD = 1.0


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
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"mess": 0.0, "spark": 0.0, "cleanup": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "confidence": 0.0, "anxiety": 0.0, "pride": 0.0, "conflict": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "youngster"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Quest:
    id: str
    title: str
    aim: str
    hurdle: str
    reward: str
    mess: str
    mess_kind: str
    zone: set[str]
    keyword: str = "quest"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------
SETTINGS = {
    "gym": Setting(place="the gym", indoor=True, affords={"flip", "bounce", "drill"}),
    "hall": Setting(place="the practice hall", indoor=True, affords={"flip", "bounce", "drill"}),
    "stage": Setting(place="the little stage", indoor=True, affords={"flip", "bounce"}),
}

QUESTS = {
    "flip": Quest(
        id="flip",
        title="the upside-down rescue",
        aim="flip over a row of cones",
        hurdle="the cones kept wobbling",
        reward="the medal at the end of the mat",
        mess="scattered cones",
        mess_kind="mess",
        zone={"floor"},
        keyword="quest",
        tags={"gymnast", "quest", "flip"},
    ),
    "bounce": Quest(
        id="bounce",
        title="the bouncy parade",
        aim="bounce across the spring mat",
        hurdle="the mat kept making goofy boings",
        reward="the glitter ribbon basket",
        mess="bouncy bits everywhere",
        mess_kind="spark",
        zone={"floor"},
        keyword="quest",
        tags={"gymnast", "quest", "bounce"},
    ),
    "drill": Quest(
        id="drill",
        title="the aim-and-smile mission",
        aim="aim the foam bazooka at the target",
        hurdle="the target was tiny and kept swaying",
        reward="the gold star sticker",
        mess="confetti on the floor",
        mess_kind="mess",
        zone={"floor", "torso"},
        keyword="quest",
        tags={"bazooka", "quest", "comedy"},
    ),
}

PROPS = {
    "foam_bazooka": Prop(
        id="foam_bazooka",
        label="a foam bazooka",
        phrase="a foam bazooka that shoots confetti",
        guards={"mess"},
        covers={"floor", "torso"},
        prep="pick up the foam bazooka and practice the aim",
        tail="marched back to the target with their foam bazooka",
    ),
    "safety_goggles": Prop(
        id="safety_goggles",
        label="safety goggles",
        phrase="bright safety goggles",
        guards={"spark", "mess"},
        covers={"eyes"},
        prep="put on safety goggles first",
        tail="trotted back with the goggles on",
    ),
    "grip_shoes": Prop(
        id="grip shoes",
        label="grip shoes",
        phrase="grip shoes with sticky soles",
        guards={"spark", "mess"},
        covers={"feet"},
        prep="lace up grip shoes before the quest",
        tail="stomped back with sticky shoes",
        plural=True,
    ),
}

NAME_POOL = ["Ari", "Milo", "Pip", "Nina", "Toby", "Rosa", "Jules", "Kira"]
TRAITS = ["curious", "silly", "bold", "cheery", "dramatic"]


# -----------------------------------------------------------------------------
# Python reasonableness gate
# -----------------------------------------------------------------------------
def quest_at_risk(quest: Quest) -> bool:
    return "floor" in quest.zone or "torso" in quest.zone


def select_prop(quest: Quest) -> Optional[Prop]:
    for prop in PROPS.values():
        if quest.mess_kind in prop.guards and (quest.zone & prop.covers):
            return prop
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            quest = QUESTS[qid]
            if quest_at_risk(quest) and select_prop(quest):
                out.append((place, qid))
    return out


def explain_rejection(quest: Quest) -> str:
    return (
        f"(No story: the quest '{quest.title}' has no reasonable prop in the catalog "
        f"that both fits the messy zone and solves the problem. The comedy needs a "
        f"clear fix, not a random object swap.)"
    )


# -----------------------------------------------------------------------------
# Story screenplay
# -----------------------------------------------------------------------------
def _do_quest(world: World, actor: Entity, quest: Quest, narrate: bool = True) -> None:
    world.zone = set(quest.zone)
    actor.meters["spark"] += 1
    actor.memes["confidence"] += 1
    if quest.id == "drill":
        actor.meters["mess"] += 1
    if narrate:
        world.say(f"{actor.id} charged into the {quest.keyword} with far too much swagger.")


def predict(world: World, actor: Entity, quest: Quest) -> dict:
    sim = world.copy()
    _do_quest(sim, sim.get(actor.id), quest, narrate=False)
    return {
        "mess": sim.entities[actor.id].meters["mess"],
        "confidence": sim.entities[actor.id].memes["confidence"],
    }


def introduce(world: World, hero: Entity, gymnast: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved big plans and louder announcements."
    )
    world.say(
        f"{gymnast.id} was a gymnast who could land on {gymnast.pronoun('possessive')} feet "
        f"without even wobbling."
    )
    world.say(
        f"One day they heard about {quest.title}, a {quest.keyword} that sounded heroic "
        f"and a bit ridiculous."
    )


def want_quest(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} wanted to {quest.aim}, because {hero.pronoun('subject')} thought "
        f"the whole thing would make a splendid story."
    )


def warn(world: World, gymnast: Entity, hero: Entity, quest: Quest) -> bool:
    pred = predict(world, hero, quest)
    if pred["mess"] < THRESHOLD:
        return False
    world.facts["predicted_mess"] = quest.mess
    world.say(
        f'"Careful," said {gymnast.id}. "If you rush the {quest.keyword}, the floor will end up '
        f"{quest.mess}.""
    )
    return True


def refuse(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["anxiety"] += 1
    world.say(
        f"{hero.id} grinned anyway and tried to start the {quest.keyword} all by {hero.pronoun('object')}. "
        f"{hero.pronoun('subject').capitalize()} took one dramatic step and nearly tipped over."
    )


def chaos(world: World, hero: Entity, quest: Quest) -> None:
    hero.meters["mess"] += 1
    world.say(
        f"The cones bumped, the mat squeaked, and the {quest.keyword} turned into a silly wobble parade."
    )


def offer_prop(world: World, gymnast: Entity, hero: Entity, quest: Quest) -> Optional[Prop]:
    prop = select_prop(quest)
    if prop is None:
        return None
    world.say(
        f"{gymnast.id} pointed at {prop.label} and said, "
        f'"How about we {prop.prep}?"'
    )
    inst = world.add(
        Entity(
            id=prop.id,
            kind="thing",
            type="prop",
            label=prop.label,
            phrase=prop.phrase,
            owner=hero.id,
            caretaker=gymnast.id,
            protective=True,
            covers=set(prop.covers),
            plural=prop.plural,
        )
    )
    inst.worn_by = hero.id
    if predict(world, hero, quest)["mess"] < THRESHOLD:
        return prop
    inst.worn_by = None
    del world.entities[inst.id]
    return None


def accept(world: World, hero: Entity, gymnast: Entity, quest: Quest, prop: Prop) -> None:
    hero.memes["joy"] += 1
    hero.memes["anxiety"] = 0
    hero.memes["confidence"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id}'s eyes widened, and {hero.pronoun('subject')} nodded so fast it looked like a tiny bow."
    )
    world.say(
        f"Together they {prop.tail}. This time {hero.id} could {quest.aim}, "
        f"and the clever prop kept the mess from taking over."
    )
    world.say(
        f"In the end, the gymnast did a clean landing, the youngster did a heroic pose, "
        f"and everybody laughed because the foam bazooka only shot confetti."
    )


def tell(setting: Setting, quest: Quest, hero_name: str = "Baz", gymnast_name: str = "Mina") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="youngster"))
    gymnast = world.add(Entity(id=gymnast_name, kind="character", type="gymnast"))
    world.facts.update(hero=hero, gymnast=gymnast, quest=quest, setting=setting)

    introduce(world, hero, gymnast, quest)
    world.para()
    want_quest(world, hero, quest)
    warn(world, gymnast, hero, quest)
    refuse(world, hero, quest)
    chaos(world, hero, quest)
    world.para()
    prop = offer_prop(world, gymnast, hero, quest)
    if prop:
        accept(world, hero, gymnast, quest, prop)
    world.facts["prop"] = prop
    world.facts["resolved"] = prop is not None
    return world


# -----------------------------------------------------------------------------
# StoryParams and registries
# -----------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    gymnast: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="gym", quest="drill", name="Baz", gymnast="Mina"),
    StoryParams(place="hall", quest="flip", name="Pip", gymnast="Rosa"),
    StoryParams(place="stage", quest="bounce", name="Ari", gymnast="Jules"),
]


# -----------------------------------------------------------------------------
# QA generation
# -----------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, gymnast, quest = f["hero"], f["gymnast"], f["quest"]
    return [
        f'Write a short comedy story for a child about a youngster named {hero.id}, a gymnast, and a {quest.keyword}.',
        f"Tell a funny story where {hero.id} wants to {quest.aim} but {gymnast.id} suggests a safer, sillier plan.",
        f'Write a playful story that includes a foam bazooka and ends with teamwork and applause.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, gymnast, quest = f["hero"], f["gymnast"], f["quest"]
    prop = f.get("prop")
    qa = [
        QAItem(
            question=f"Who wanted to do the {quest.keyword} in the story?",
            answer=f"{hero.id}, the youngster, wanted to do the {quest.keyword} because {hero.pronoun('subject')} thought it would be exciting.",
        ),
        QAItem(
            question=f"Who helped make the messy plan safer?",
            answer=f"{gymnast.id} the gymnast helped by offering a better prop and a calmer plan.",
        ),
        QAItem(
            question=f"What problem did the gymnast worry about?",
            answer=f"{gymnast.id} worried that the {quest.keyword} would leave the floor {quest.mess_kind} if nobody used the right prop.",
        ),
    ]
    if prop:
        qa.append(
            QAItem(
                question=f"How did {prop.label} help the youngster?",
                answer=f"{prop.label.capitalize()} helped {hero.id} finish the {quest.keyword} safely, so the fun stayed funny instead of turning into a real mess.",
            )
        )
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"What changed by the end of the story?",
                answer=f"By the end, {hero.id} trusted {gymnast.id}, the quest was finished, and the confetti stayed in the right place.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "gymnast": [
        QAItem(
            question="What does a gymnast do?",
            answer="A gymnast practices flips, balances, jumps, and other careful moves.",
        )
    ],
    "bazooka": [
        QAItem(
            question="What is a bazooka in this storyworld?",
            answer="It is a silly foam prop that shoots confetti or streamers, not a real weapon.",
        )
    ],
    "quest": [
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal or mission that a character tries to complete, often with a challenge along the way.",
        )
    ],
    "comedy": [
        QAItem(
            question="What makes a story funny?",
            answer="A comedy story often has silly mistakes, surprising turns, and a happy ending that makes people smile.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["quest"].tags)
    out: list[QAItem] = []
    for tag in ["gymnast", "bazooka", "quest", "comedy"]:
        if tag in tags or tag in {"gymnast", "quest", "comedy"}:
            out.extend(WORLD_KNOWLEDGE[tag])
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


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------
ASP_RULES = r"""
quest_at_risk(Q) :- zone(Q,R).
prop_fixes(P,Q) :- quest_at_risk(Q), prop(P), guards(P,M), mess_kind(Q,M), covers(P,R), zone(Q,R).
valid(Place,Q) :- affords(Place,Q), quest_at_risk(Q), prop_fixes(_,Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("mess_kind", qid, q.mess_kind))
        for z in sorted(q.zone):
            lines.append(asp.fact("zone", qid, z))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        for g in sorted(p.guards):
            lines.append(asp.fact("guards", pid, g))
        for c in sorted(p.covers):
            lines.append(asp.fact("covers", pid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world: youngster, bazooka, gymnast, and quest.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--gymnast")
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
    if args.place and args.quest:
        if args.quest not in SETTINGS[args.place].affords:
            raise StoryError("(No valid combination matches the given options.)")
        if select_prop(QUESTS[args.quest]) is None:
            raise StoryError(explain_rejection(QUESTS[args.quest]))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAME_POOL)
    gymnast = args.gymnast or rng.choice(NAME_POOL)
    return StoryParams(place=place, quest=quest, name=name, gymnast=gymnast)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], params.name, params.gymnast)
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest) combos:\n")
        for place, quest in combos:
            print(f"  {place:12} {quest}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
