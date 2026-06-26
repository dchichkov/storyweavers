#!/usr/bin/env python3
"""
storyworlds/worlds/savanna_skittle_flashback_animal_story.py
=============================================================

A small animal-story world on the savanna, with a flashback beat built into
the simulated state.

Premise:
- A young savanna animal loves a bright skittle treat.
- A parent worries that a risky game on the hot savanna will make the treat
  sticky, dusty, or lost.
- The parent remembers a flashback to an earlier time when a little mistake
  taught a useful lesson.
- The memory helps the family choose a safer, happier way to finish the day.

This script follows the Storyweavers world contract:
- self-contained stdlib script
- StoryParams / registries / build_parser / resolve_params / generate / emit / main
- eager import of results.py
- lazy import of asp.py inside ASP helpers
- Python reasonableness gate plus inline ASP_RULES twin
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"lioness", "cub", "gazelle", "zebra", "meerkat", "cheetah"}
        male = {"lion", "jackal", "warthog", "ostrich", "elephant", "giraffe"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the savanna"
    hot: bool = True
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
    weather: str = "hot"
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
        return any(region in g.region or region in getattr(g, "covers", set()) for g in self.worn_items(actor))

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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("dusty", "sticky"):
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.plural:
                    continue
                if item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got dusty and sticky.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
        out.append(f"That would mean more cleaning for {carer.label_word}.")
    return out


def _r_flashback(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("remember", 0.0) < THRESHOLD:
            continue
        sig = ("flashback", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["softened"] = actor.memes.get("softened", 0.0) + 1
        return ["__flashback__"]
    return []


CAUSAL_RULES = [
    _r_soil,
    _r_worry,
    _r_flashback,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__flashback__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def activity_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved the warm savanna.")


def loves_treat(world: World, hero: Entity, treat: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    treat.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {treat.label} and held {treat.it()} carefully."
    )


def arrives(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"One hot day, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} went to {world.setting.place}."
    )
    world.say(f"The grass shimmered, and the air felt dry enough to crackle.")
    world.say(f"{hero.id} wanted to {activity.verb} right away.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"If you do that, your {prize.label} will get {activity.soil}," {parent.label_word} said.'
    )
    return True


def remember(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["remember"] = hero.memes.get("remember", 0.0) + 1
    world.say(
        f"{parent.label_word} paused, and a flashback tugged at {parent.pronoun('possessive')} memory."
    )
    world.say(
        f"Back then, {hero.id} had dropped {hero.pronoun('possessive')} snack in the dust, and everyone had had to clean up."
    )


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    world.say(f"{hero.id} still wanted to {activity.rush}.")


def offer(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        worn_by=hero.id,
    ))
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{parent.label_word} smiled and said, "How about we {gear_def.prep}?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["defiance"] = 0.0
    world.say(f"{hero.id} brightened and nodded.")
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, and {prize.label} stayed clean."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Mosi",
    hero_type: str = "meerkat",
    parent_type: str = "lioness",
    hero_traits: Optional[list[str]] = None,
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "cheerful"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    world.say(f"{hero.id} had a bright {prize.label} and a big wish for play.")
    loves_treat(world, hero, prize)

    world.para()
    arrives(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    remember(world, parent, hero)
    defy(world, hero, activity)

    world.para()
    gear_def = offer(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        gear=gear_def,
        resolved=gear_def is not None,
        setting=setting,
    )
    return world


SETTINGS = {
    "savanna": Setting(place="the savanna", hot=True, affords={"skittle_chase", "skittle_hide"}),
    "acacia_shade": Setting(place="the acacia shade", hot=True, affords={"skittle_chase", "skittle_hide"}),
}

ACTIVITIES = {
    "skittle_chase": Activity(
        id="skittle_chase",
        verb="chase the skittle across the grass",
        gerund="chasing the skittle across the grass",
        rush="dash after the skittle",
        mess="dusty",
        soil="dusty and sticky",
        zone={"feet", "legs"},
        weather="hot",
        keyword="skittle",
        tags={"savanna", "skittle", "dusty"},
    ),
    "skittle_hide": Activity(
        id="skittle_hide",
        verb="hide the skittle under a rock",
        gerund="hiding the skittle under a rock",
        rush="run to hide the skittle",
        mess="sticky",
        soil="sticky and dusty",
        zone={"hands", "torso"},
        weather="hot",
        keyword="skittle",
        tags={"savanna", "skittle", "sticky"},
    ),
}

PRIZES = {
    "skittle": Prize(
        label="skittle",
        phrase="a tiny rainbow skittle",
        type="skittle",
        region="hands",
    ),
    "pouch": Prize(
        label="snack pouch",
        phrase="a bright snack pouch with one skittle inside",
        type="pouch",
        region="torso",
    ),
    "necklace": Prize(
        label="bead necklace",
        phrase="a shiny bead necklace with a single skittle charm",
        type="necklace",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="shade_mat",
        label="a shade mat",
        covers={"torso", "hands"},
        guards={"sticky"},
        prep="put the skittle on a shade mat first",
        tail="walked to the shade mat",
    ),
    Gear(
        id="paw_wraps",
        label="cool paw wraps",
        covers={"hands"},
        guards={"dusty", "sticky"},
        prep="wrap your paws before we play",
        tail="tucked the skittle into a safe pouch",
    ),
    Gear(
        id="snack_cover",
        label="a snack cover",
        covers={"torso"},
        guards={"sticky", "dusty"},
        prep="cover the snack with a little snack cover",
        tail="used the snack cover and stayed near the acacia",
    ),
]

ANIMAL_NAMES = ["Mosi", "Kira", "Tamu", "Nala", "Biko", "Asha", "Sefu", "Zuri"]
ANIMALS = ["meerkat", "lion cub", "gazelle", "zebra", "elephant calf", "ostrich chick", "hyena pup"]
PARENT_TYPES = ["lioness", "zebra", "elephant", "meerkat", "gazelle"]
TRAITS = ["brave", "curious", "playful", "restless", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if activity_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    animal: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "savanna": [
        ("What is a savanna?", "A savanna is a wide grassland with a few trees and many animals living there."),
    ],
    "skittle": [
        ("What is a skittle?", "A skittle is a small, colorful sweet treat that children sometimes eat as a snack."),
    ],
    "dusty": [
        ("Why does dust stick to sweaty skin?", "Dust can stick when skin is hot or a little damp, because tiny bits cling more easily."),
    ],
    "sticky": [
        ("Why can sticky things pick up dirt?", "Sticky things can catch dirt and crumbs because little pieces cling to them."),
    ],
    "shade": [
        ("Why do animals rest in the shade on a hot day?", "Shade helps animals stay cooler and more comfortable when the sun is strong."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short animal story for a young child that takes place on the {f["setting"].place} and includes the word "savanna".',
        f"Tell a gentle flashback story where {hero.id}, a little {hero.type}, wants to {act.verb} but {parent.label_word} worries about the {prize.label}.",
        f'Write a story with a flashback, a skittle, and a happy ending near the acacia shade.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa: list[QAItem] = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {hero.type}, and {hero.pronoun('possessive')} {parent.label_word}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do on the savanna?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"What was special about the treat?",
            answer=f"The treat was {prize.phrase}, and it mattered because it could get messy on the hot savanna.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did the family solve the problem?",
                answer=f"They used {gear.label} so {hero.id} could {act.verb} without ruining the {prize.label}.",
            )
        )
    if hero.memes.get("remember", 0.0) >= THRESHOLD:
        qa.append(
            QAItem(
                question=f"What was the flashback about?",
                answer=f"The flashback was about an earlier time when the snack got dusty and everyone had to clean up, so the parent remembered to choose a safer plan.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    tags.add("savanna")
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="savanna", activity="skittle_chase", prize="skittle", name="Mosi", animal="meerkat", parent="lioness", trait="curious"),
    StoryParams(place="acacia_shade", activity="skittle_hide", prize="pouch", name="Nala", animal="zebra", parent="zebra", trait="playful"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not activity_risk(activity, prize):
        return f"(No story: {activity.gerund} would not threaten {prize.label} in a believable way.)"
    return f"(No story: there is no good gear that covers the at-risk {prize.label} for this activity.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: this choice is not a natural fit here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
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
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world on the savanna with a flashback and a skittle."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (activity_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    animal = args.animal or rng.choice(ANIMALS)
    name = args.name or rng.choice(ANIMAL_NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, animal=animal, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.animal,
        params.parent,
        [params.trait, "little"],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:")
        for place, act, prize in combos:
            print(f"  {place:12} {act:16} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
