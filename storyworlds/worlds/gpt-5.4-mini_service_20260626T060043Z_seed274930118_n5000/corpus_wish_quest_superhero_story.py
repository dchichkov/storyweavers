#!/usr/bin/env python3
"""
storyworlds/worlds/corpus_wish_quest_superhero_story.py
========================================================

A small superhero story world built from the seed words corpus and wish.

Premise:
- A young hero wishes to join a city quest.
- The quest needs a real, physical job to do: recover or protect a corpus,
  meaning a stack of clue pages, reports, or comic records.
- The mentor warns that the quest is risky and offers a sensible piece of gear.
- The child accepts, gains courage, and finishes the quest with the corpus safe.

The world is intentionally small and state-driven:
- meters track physical facts like distance, damage, dust, and carried weight
- memes track emotional facts like wish, worry, courage, pride, and relief
- the story changes as the quest progresses, not just as swapped nouns
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
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["distance", "dust", "damage", "weight", "safety"]:
            self.meters.setdefault(k, 0.0)
        for k in ["wish", "worry", "courage", "pride", "relief", "fear", "hope"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    label: str
    verb: str
    gerund: str
    danger: str
    risk: str
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
        self.facts: dict = {}
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone.facts = dict(self.facts)
        return clone


def _apply_quest(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.memes["courage"] < THRESHOLD or hero.meters["distance"] < THRESHOLD:
            continue
        quest = world.facts.get("quest")
        if not quest:
            continue
        for item in world.entities.values():
            if item.id == world.facts.get("corpus").id:
                continue
        if world.facts.get("corpus").meters["damage"] >= THRESHOLD:
            sig = ("quest_fix", hero.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.facts["quest_done"] = True
            out.append("The hero finished the quest and saved the corpus.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = _apply_quest(world)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero quest story world with corpus and wish.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mentor", "captain"])
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


def prize_at_risk(quest: Quest, prize: Prize) -> bool:
    return prize.region in quest.zone


def select_gear(quest: Quest, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if quest.danger in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            quest = QUESTS[qid]
            for pid, pr in PRIZES.items():
                if prize_at_risk(quest, pr) and select_gear(quest, pr):
                    combos.append((place, qid, pid))
    return combos


def tell(setting: Setting, quest: Quest, prize_cfg: Prize, hero_name: str, gender: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, label=hero_name))
    parent = world.add(Entity(id="Guide", kind="character", type=parent_type, label=parent_type))
    corpus = world.add(Entity(
        id="corpus",
        type="corpus",
        label="corpus",
        phrase="a thick corpus of clue pages",
        owner=hero.id,
        caretaker=parent.id,
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        plural=prize_cfg.plural,
    ))

    hero.memes["wish"] += 1
    hero.memes["hope"] += 1
    world.say(f"{hero_name} was a small hero with a big wish: {hero.pronoun('subject')} wanted to help on a real quest.")
    world.say(f"{hero.pronoun('subject').capitalize()} loved the city corpus, a thick stack of clue pages that held old rescue secrets.")
    world.say(f"One morning, {hero_name}'s {parent_type} brought out {prize.phrase} for the mission.")

    world.para()
    world.say(f"The quest led them to {setting.place}.")
    world.say(f"There, the {quest.label} could go wrong because {quest.danger}.")
    hero.memes["worry"] += 1
    world.say(f"{hero_name} wished hard to go anyway, but {hero.pronoun('possessive')} {parent_type} raised a careful hand.")
    world.say(f'“If you rush in, {prize.label} will get {quest.risk},” {parent_type} said. “We need a safer plan.”')

    hero.memes["fear"] += 1
    hero.meters["distance"] += 1
    world.say(f"{hero_name} tried to charge ahead, cape fluttering, but {hero.pronoun('possessive')} boots slipped on the danger trail.")

    gear_def = select_gear(quest, prize)
    if gear_def is None:
        raise StoryError("No reasonable gear exists for this quest and prize.")
    gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, protective=True, covers=set(gear_def.covers), plural=gear_def.plural))
    gear.worn_by = hero.id

    hero.memes["courage"] += 1
    hero.memes["worry"] = 0
    world.say(f'Then {parent_type} smiled and offered {gear_def.label}.')
    world.say(f'"How about we {gear_def.prep} and do the quest together?"')

    if prize.region in gear.covers:
        prize.meters["damage"] = 0.0
        corpus.meters["damage"] = 0.0
        hero.memes["relief"] += 1
        hero.memes["pride"] += 1
        world.say(f"{hero_name} nodded, slipped on the gear, and felt brave enough to try again.")
        world.say(f"They {gear_def.tail}.")
        world.say(f"At last, {hero_name} finished the quest, and the {corpus.label} stayed safe in {hero.pronoun('possessive')} arms.")
        world.facts["quest_done"] = True

    world.facts.update(
        hero=hero, parent=parent, corpus=corpus, prize=prize, quest=quest, gear=gear,
        resolved=True,
    )
    return world


SETTINGS = {
    "museum": Setting(place="the city museum", indoor=True, affords={"archive"}),
    "rooftop": Setting(place="the moonlit rooftop", indoor=False, affords={"signal"}),
    "library": Setting(place="the hero library", indoor=True, affords={"archive", "signal"}),
}

QUESTS = {
    "archive": Quest(
        id="archive",
        label="archive rescue",
        verb="rescue the corpus",
        gerund="rescuing the corpus",
        danger="wind and dust could scatter the pages",
        risk="dusty",
        zone={"hands", "torso"},
        keyword="corpus",
        tags={"corpus", "dust"},
    ),
    "signal": Quest(
        id="signal",
        label="signal quest",
        verb="carry the signal disk",
        gerund="carrying the signal disk",
        danger="rain could make the disk slick",
        risk="wet",
        zone={"hands", "feet"},
        keyword="wish",
        tags={"wish", "wet"},
    ),
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a bright red cape", type="cape", region="torso"),
    "boots": Prize(label="boots", phrase="shiny rescue boots", type="boots", region="feet", plural=True),
    "gloves": Prize(label="gloves", phrase="strong hero gloves", type="gloves", region="hands", plural=True),
}

GEAR = [
    Gear(id="mask", label="a dust mask", covers={"hands", "torso"}, guards={"dusty"}, prep="put on a dust mask first", tail="walked back into the archive with a dust mask on"),
    Gear(id="raincoat", label="a raincoat", covers={"feet", "hands"}, guards={"wet"}, prep="pull on a raincoat first", tail="went back onto the roof wearing a raincoat"),
    Gear(id="gauntlets", label="reinforced gauntlets", covers={"hands"}, guards={"dusty", "wet"}, prep="strap on reinforced gauntlets first", tail="returned with reinforced gauntlets ready"),
]

GIRL_NAMES = ["Nova", "Mira", "Luna", "Ruby", "Ivy", "Zara"]
BOY_NAMES = ["Leo", "Jax", "Milo", "Toby", "Finn", "Eli"]
TRAITS = ["brave", "quick", "kind", "steady", "curious", "bright"]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("danger_of", qid, q.danger))
        for r in sorted(q.zone):
            lines.append(asp.fact("splashes", qid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(Q, P) :- splashes(Q, R), worn_on(P, R).
protects(G, Q, P) :- prize_at_risk(Q, P), gear(G), danger_of(Q, D), guards(G, D), covers(G, R), worn_on(P, R).
valid(Place, Q, P) :- affords(Place, Q), prize_at_risk(Q, P), protects(_, Q, P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(valid_story_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and Python.")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.prize:
        q, p = QUESTS[args.quest], PRIZES[args.prize]
        if not (prize_at_risk(q, p) and select_gear(q, p)):
            raise StoryError("That quest and prize do not make a reasonable superhero problem.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, quest, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mentor", "captain"])
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short superhero story for a child that uses the word "corpus" and includes a wish, a quest, and a safe plan.',
        f"Tell a simple story about {hero.id}, who wishes to help on a quest and must protect the corpus.",
        f"Write a hero story where a mentor warns that the corpus will be damaged, then offers gear that makes the quest safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, quest, prize, corpus = f["hero"], f["parent"], f["quest"], f["prize"], f["corpus"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} wish to do at the start of the story?",
            answer=f"{hero.id} wished to help on a real superhero quest and be useful to the city.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn {hero.id} about the {corpus.label}?",
            answer=f"{parent.label} warned {hero.id} because the {quest.danger} could damage the {corpus.label} and make the mission unsafe.",
        ),
        QAItem(
            question=f"What gear helped {hero.id} finish the quest safely?",
            answer=f"{gear.label} helped {hero.id} finish the quest safely and keep the {corpus.label} protected.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after the plan worked?",
            answer=f"{hero.id} felt relieved, proud, and brave after the safer plan worked.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a corpus?",
            answer="A corpus can mean a collection of pages, records, or writings kept together for study or use.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to do an important job, often with a goal to find, protect, or rescue something.",
        ),
        QAItem(
            question="Why do heroes wear gear?",
            answer="Heroes wear gear to stay safe, block danger, and keep their tools or prizes from getting hurt.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], PRIZES[params.prize], params.name, params.gender, params.parent)
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


CURATED = [
    StoryParams(place="library", quest="archive", prize="gloves", name="Nova", gender="girl", parent="mentor"),
    StoryParams(place="museum", quest="archive", prize="cape", name="Leo", gender="boy", parent="captain"),
    StoryParams(place="library", quest="signal", prize="boots", name="Mira", gender="girl", parent="mentor"),
]


def build_asp_program(show: str) -> str:
    return asp_program(show)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(build_asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(build_asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for row in vals:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
