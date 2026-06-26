#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/installment_protein_pajamas_doctor_s_waiting_room.py
===============================================================================================================

A small folk-tale storyworld set in a doctor's waiting room.

Seed tale:
A child arrives at the doctor's waiting room in pajamas. They are on a little
quest to finish one installment of a protein-rich breakfast before the doctor
calls their name. The child is hungry, the parent is careful, and the waiting
room asks for patience. A simple compromise lets the child keep the pajamas
clean, finish the protein snack, and turn the waiting into a brave little quest.

This world models:
- the physical risk of spilling protein food onto pajamas
- the emotional rise and resolution of hunger, worry, and courage
- a gentle quest structure in a doctor's waiting room
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MESS_KINDS = {"sticky", "spilled"}


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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"sticky": 0.0, "spilled": 0.0, "cleanliness": 0.0}
        if not self.memes:
            self.memes = {"hunger": 0.0, "worry": 0.0, "bravery": 0.0, "joy": 0.0, "patience": 0.0}

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
    place: str = "the doctor's waiting room"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    title: str
    task: str
    gerund: str
    risk: str
    mess: str
    zone: set[str]
    keyword: str = "quest"
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("spill", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                item.meters["cleanliness"] = item.meters.get("cleanliness", 0.0) - 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess}.")
    return out


def _r_caretaker_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("sticky", 0.0) < THRESHOLD and item.meters.get("spilled", 0.0) < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
        out.append(f"That would mean more fuss for {carer.label or carer.id}.")
    return out


def _r_wait_patience(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("patience", 0.0) < THRESHOLD:
            continue
        sig = ("brave", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["bravery"] = actor.memes.get("bravery", 0.0) + 1
        out.append(f"{actor.id} found a brave little way to wait.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("spill", "physical", _r_spill),
    Rule("caretaker_worry", "emotional", _r_caretaker_worry),
    Rule("wait_patience", "emotional", _r_wait_patience),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


def quest_at_risk(quest: Quest, prize: Prize) -> bool:
    return prize.region in quest.zone


def select_gear(quest: Quest, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if quest.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, quest: Quest, prize_id: str) -> dict:
    sim = world.copy()
    _do_quest(sim, sim.get(actor.id), quest, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and (prize.meters.get("sticky", 0.0) >= THRESHOLD or prize.meters.get("spilled", 0.0) >= THRESHOLD)),
    }


def _do_quest(world: World, actor: Entity, quest: Quest, narrate: bool = True) -> None:
    if quest.id not in world.setting.affords:
        return
    world.zone = set(quest.zone)
    actor.meters[quest.mess] = actor.meters.get(quest.mess, 0.0) + 1
    actor.memes["patience"] = actor.memes.get("patience", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "small")
    world.say(f"Once there was a little {trait} {hero.type} named {hero.id} who went wherever the day led.")


def setup(world: World, hero: Entity, parent: Entity, prize: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} arrived in {hero.phrase or 'pajamas'} at {world.setting.place} for a quiet little visit."
    )
    world.say(
        f"{hero.id} loved the careful comfort of {hero.pronoun('possessive')} pajamas and carried a {quest.title} in {hero.pronoun('possessive')} heart."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label or parent.type} had brought {hero.pronoun('object')} to see the doctor and had packed {prize.phrase} for the wait."
    )


def wants(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["hunger"] = hero.memes.get("hunger", 0.0) + 1
    world.say(f"{hero.id} wanted to {quest.task}, because the waiting room felt long and the stomach felt empty.")


def warn(world: World, parent: Entity, hero: Entity, quest: Quest, prize: Entity) -> bool:
    pred = predict_mess(world, hero, quest, prize.id)
    if not pred["soiled"]:
        return False
    world.say(
        f'"If you {quest.task}, your {prize.label} could get {quest.risk}," {parent.label or parent.type} said. '
        f'"Then we would have more washing to do."'
    )
    world.facts["predicted_soil"] = quest.risk
    return True


def defy(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(f"{hero.id} still wished to begin the quest at once.")
    world.say(f"{hero.id} tried to {quest.task}, though the room was small and the end was not yet in sight.")


def offer(world: World, parent: Entity, hero: Entity, quest: Quest, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(quest, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, quest, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{parent.label or parent.type} smiled like a wise old tale and said, '
        f'"How about we {gear_def.prep} before you {quest.task}?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, quest: Quest, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    hero.memes["worry"] = 0.0
    world.say(f"{hero.id} brightened and nodded, as if the quest had become a song instead of a wait.")
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {quest.gerund}, {prize.label} stayed clean, and the waiting room seemed smaller and kinder."
    )


def tell(setting: Setting, quest: Quest, prize_cfg: Prize,
         hero_name: str = "Nora", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        phrase="pajamas",
        traits=["little"] + (hero_traits or ["patient", "gentle"]),
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
    ))
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

    intro(world, hero)
    setup(world, hero, parent, prize, quest)
    world.para()
    wants(world, hero, quest)
    warn(world, parent, hero, quest, prize)
    defy(world, hero, quest)
    world.para()
    gear_def = offer(world, parent, hero, quest, prize)
    if gear_def:
        accept(world, parent, hero, quest, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        quest=quest,
        setting=setting,
        gear=gear_def,
        resolved=gear_def is not None,
    )
    return world


SETTING = Setting(place="the doctor's waiting room", indoor=True, affords={"protein_quest"})

QUESTS = {
    "protein_quest": Quest(
        id="protein_quest",
        title="protein quest",
        task="sip the protein shake carefully",
        gerund="sipping the protein shake carefully",
        risk="sticky",
        mess="sticky",
        zone={"torso"},
        keyword="quest",
        tags={"protein", "quest"},
    )
}

PRIZES = {
    "pajamas": Prize(
        label="pajamas",
        phrase="soft striped pajamas",
        type="pajamas",
        region="torso",
        plural=True,
    )
}

GEAR = [
    Gear(
        id="bib",
        label="a little bib",
        covers={"torso"},
        guards={"sticky"},
        prep="put on a little bib",
        tail="walked back to the chair with the bib on",
    )
]

GIRL_NAMES = ["Nora", "Mina", "Lina", "Ada", "Elsie"]
BOY_NAMES = ["Owen", "Finn", "Toby", "Milo", "Theo"]
TRAITS = ["brave", "patient", "curious", "gentle", "bright"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in {"waiting_room": SETTING}.items():
        for qid in setting.affords:
            q = QUESTS[qid]
            for pid, pr in PRIZES.items():
                if quest_at_risk(q, pr) and select_gear(q, pr):
                    combos.append((place, qid))
    return combos


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "protein": [("What is protein?", "Protein is a part of food that helps bodies grow strong and heal.")],
    "pajamas": [("What are pajamas for?", "Pajamas are soft clothes people wear to sleep and rest comfortably.")],
    "quest": [("What is a quest?", "A quest is a special task or search, often with a brave goal to reach.")],
    "doctor": [("What does a doctor do?", "A doctor helps people when they are sick or hurt and checks how their bodies are doing.")],
    "waiting room": [("What is a waiting room?", "A waiting room is a place where people sit until it is their turn to be seen.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, quest, prize = f["hero"], f["parent"], f["quest"], f["prize"]
    return [
        f'Write a short folk-tale story for a child in a doctor\'s waiting room that includes "{quest.keyword}", "{prize.label}", and "protein".',
        f"Tell a gentle quest story where {hero.id} in pajamas waits for the doctor and learns to sip {quest.task}.",
        f"Write a simple story about {hero.id}, {parent.label or parent.type}, and one small {quest.title} in the waiting room.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, quest, prize = f["hero"], f["parent"], f["quest"], f["prize"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {hero.type} in pajamas, and {parent.label or parent.type}, who helps in the doctor's waiting room.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the parent worried about the pajamas?",
            answer=f"{hero.id} wanted to {quest.task}. It was a small quest, but it could make the {prize.label} messy if {hero.id} was not careful.",
        ),
        QAItem(
            question=f"Why did the parent worry about the {prize.label}?",
            answer=f"The parent worried because the protein snack could get {quest.risk} on the {prize.label}, and then there would be more washing to do.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question="How did the child manage to finish the quest without ruining the pajamas?",
            answer=f"They used {gear.label} first, so {hero.id} could {quest.task} carefully while the {prize.label} stayed clean.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and brave. The waiting room turned from a long wait into a small, successful quest.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags)
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags or tag == "doctor":
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["waiting room"])
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="waiting_room", quest="protein_quest", prize="pajamas", name="Nora", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="waiting_room", quest="protein_quest", prize="pajamas", name="Owen", gender="boy", parent="father", trait="patient"),
]


def explain_rejection(quest: Quest, prize: Prize) -> str:
    if not quest_at_risk(quest, prize):
        return f"(No story: {prize.label} would not be at risk during this quest.)"
    return f"(No story: no suitable gear exists for {prize.label} during this quest.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: that prize is not a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
quest_at_risk(Q,P) :- zone(Q,R), worn_on(P,R).
protects(G,Q,P) :- quest(Q), prize_at_risk(Q,P), guards(G,M), quest_mess(Q,M), covers(G,R), worn_on(P,R).
has_fix(Q,P) :- protects(_,Q,P).
valid(P,Q) :- quest(Q), prize(P), prize_at_risk(Q,P), has_fix(Q,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "waiting_room"))
    lines.append(asp.fact("indoor", "waiting_room"))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_mess", qid, q.mess))
        for r in sorted(q.zone):
            lines.append(asp.fact("zone", qid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
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
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld set in a doctor's waiting room.")
    ap.add_argument("--place", choices=["waiting_room"])
    ap.add_argument("--quest", choices=QUESTS)
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


def valid_story_combos() -> list[tuple[str, str, str]]:
    return [("waiting_room", "protein_quest", "pajamas")]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.prize:
        q, p = QUESTS[args.quest], PRIZES[args.prize]
        if not (quest_at_risk(q, p) and select_gear(q, p)):
            raise StoryError(explain_rejection(q, p))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [c for c in valid_story_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, QUESTS[params.quest], PRIZES[params.prize], params.name, params.gender, [params.trait], params.parent)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
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
            header = f"### {p.name}: {p.quest} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
