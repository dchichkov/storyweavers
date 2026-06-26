#!/usr/bin/env python3
"""
A fable-style story world about a small quest, a funny illness, and a gentle
transformation.

Premise:
- A child gets mumps, which makes cheeks puff up and energy drop.
- A wise helper sends the child on a small quest for a simple remedy.
- Along the way, the child learns patience, kindness, and how to laugh at a
  messy day.
- By the end, the swelling fades, the child changes in outlook, and the moral
  lands softly.

The world is intentionally small and constraint-driven:
- mumps is the central trouble
- quest provides the plot motion
- humor keeps the tone light
- transformation is both physical and emotional
- the ending proves what changed
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    action: str
    outcome: str
    humor: str
    causes: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _ensure_meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _set_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = value


def _add_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _add_meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _rule_swollen_cheeks(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters.get("mumps", 0.0) < THRESHOLD:
            continue
        sig = ("swollen", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if hero.meters.get("swollen", 0.0) < 1.0:
            hero.meters["swollen"] = 1.0
            hero.memes["self_conscious"] = hero.memes.get("self_conscious", 0.0) + 1.0
            out.append(f"{hero.id}'s cheeks puffed up like two round buns.")
    return out


def _rule_tired(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters.get("mumps", 0.0) < THRESHOLD:
            continue
        sig = ("tired", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if hero.meters.get("energy", 1.0) > 0.25:
            hero.meters["energy"] = 0.25
            hero.memes["grump"] = hero.memes.get("grump", 0.0) + 1.0
            out.append(f"{hero.id} felt slow and sleepy, as if even a yawn needed a nap.")
    return out


def _rule_humor(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters.get("mumps", 0.0) < THRESHOLD or hero.memes.get("humor", 0.0) >= THRESHOLD:
            continue
        sig = ("humor", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["humor"] = 1.0
        out.append(f"{hero.id} noticed the cheeks made a very serious face look a little silly.")
    return out


def _rule_transformation(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters.get("remedy", 0.0) < THRESHOLD or hero.meters.get("rested", 0.0) < THRESHOLD:
            continue
        sig = ("transform", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["mumps"] = 0.0
        hero.meters["swollen"] = 0.0
        hero.meters["energy"] = 1.0
        hero.memes["gratitude"] = hero.memes.get("gratitude", 0.0) + 1.0
        hero.memes["wisdom"] = hero.memes.get("wisdom", 0.0) + 1.0
        out.append(f"By morning, {hero.id} looked lighter, brighter, and ready to laugh again.")
    return out


RULES = [_rule_swollen_cheeks, _rule_tired, _rule_humor, _rule_transformation]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    quest: str
    remedy: str
    seed: Optional[int] = None


PLACES = {
    "village": Place(name="the village", indoors=False, affords={"walk", "rest", "visit"}),
    "cottage": Place(name="the cottage", indoors=True, affords={"rest", "visit"}),
    "garden": Place(name="the garden", indoors=False, affords={"walk", "rest"}),
    "schoolyard": Place(name="the schoolyard", indoors=False, affords={"walk", "visit"}),
}

QUESTS = {
    "honey": QuestItem(
        id="honey",
        label="a jar of honey",
        phrase="a jar of golden honey",
        region="hand",
    ),
    "tea": QuestItem(
        id="tea",
        label="a warm tea cup",
        phrase="a small cup of warm herbal tea",
        region="hand",
    ),
    "napkin": QuestItem(
        id="napkin",
        label="a soft napkin",
        phrase="a soft cloth napkin",
        region="hand",
    ),
}

REMEDIES = {
    "rest": Remedy(
        id="rest",
        label="rest",
        phrase="a long, quiet rest",
        action="rested in a calm bed",
        outcome="slept",
        humor="even the pillow seemed to smile",
        causes={"honey", "tea", "napkin"},
    ),
    "laugh": Remedy(
        id="laugh",
        label="a laugh",
        phrase="a good laugh with a friend",
        action="laughed at the puffed cheeks",
        outcome="laughed",
        humor="the funny face helped the worry shrink",
        causes={"honey", "tea", "napkin"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Poppy", "Iris"]
BOY_NAMES = ["Toby", "Milo", "Ravi", "Finn", "Owen"]
HELPERS = [("owl", "wise owl"), ("goat", "old goat"), ("grandmother", "grandmother"), ("rabbit", "quick rabbit")]


def build_story(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=["small", "curious", "kind"],
        meters={"mumps": 1.0, "energy": 0.9, "swollen": 0.0, "rested": 0.0, "remedy": 0.0},
        memes={"worry": 1.0, "hope": 0.5, "humor": 0.0, "gratitude": 0.0, "wisdom": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        traits=["wise", "gentle"],
        meters={"helped": 0.0},
        memes={"calm": 1.0},
    ))
    quest = world.add(Entity(
        id="quest_item",
        type="thing",
        label=QUESTS[params.quest].label,
        phrase=QUESTS[params.quest].phrase,
        owner=helper.id,
        region=QUESTS[params.quest].region,
    ))
    world.facts.update(hero=hero, helper=helper, quest=quest, remedy=REMEDIES[params.remedy], params=params)

    world.say(
        f"In {world.place.name}, there lived {hero.id}, a small {hero.type} with a brave heart."
    )
    world.say(
        f"One morning, {hero.id} woke with mumps, and {hero.pronoun('possessive')} cheeks were puffy as little dumplings."
    )
    world.say(
        f"{hero.id} felt embarrassed at first, but {helper.id} the {helper.type} only blinked and said, "
        f"'{world.place.name.split()[-1].capitalize()}s are often solved by patience.'"
    )

    world.para()
    world.say(
        f"{helper.id} gave {hero.id} a small quest: fetch {quest.phrase} and then come home for {REMEDIES[params.remedy].phrase}."
    )
    world.say(
        f"{hero.id} set out with a wobble in {hero.pronoun('possessive')} step, hoping the day would not notice the swelling too much."
    )
    _add_meter(hero, "quest_started", 1.0)

    if params.quest == "honey":
        world.say("At the shop, the honey jar sat high on a shelf, as proud as a king in a yellow coat.")
    elif params.quest == "tea":
        world.say("At the teapot stall, the steam curled up like a tiny dragon wearing socks.")
    else:
        world.say("At the laundry line, the napkin fluttered like a small white flag that had already surrendered.")

    world.say(
        f"The shopkeeper smiled at the puffy cheeks and said, 'That face could teach a pumpkin to grin.'"
    )
    hero.memes["humor"] = 1.0
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 0.5
    _add_meter(hero, "quest_progress", 1.0)

    world.para()
    world.say(
        f"{hero.id} brought back {quest.label}, and {helper.id} nodded as if that were the best treasure in the village."
    )
    _add_meter(hero, "quest_complete", 1.0)
    _add_meter(hero, "remedy", 1.0)
    _add_meter(hero, "rested", 1.0)
    world.say(
        f"Then {hero.id} followed the advice, took {REMEDIES[params.remedy].phrase}, and {REMEDIES[params.remedy].action}."
    )
    world.say(REMEDIES[params.remedy].humor + ".")
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"By the next day, {hero.id}'s cheeks were no longer puffed, and {hero.id} could smile without feeling like a balloon."
    )
    world.say(
        f"{hero.id} thanked {helper.id}, and the little lesson settled kindly into {hero.pronoun('possessive')} heart: "
        f"when trouble makes you funny-looking, a calm step and a kind friend can still carry you through."
    )
    world.say("And so the village learned that a hard day may end with a lighter face and a wiser laugh.")
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_name, place in PLACES.items():
        for quest_id in QUESTS:
            for remedy_id in REMEDIES:
                if "rest" in place.affords or not PLACES[place_name].indoors:
                    combos.append((place_name, quest_id, remedy_id))
    return combos


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_item", qid))
        lines.append(asp.fact("region", qid, q.region))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for c in sorted(r.causes):
            lines.append(asp.fact("causes", rid, c))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Quest, Remedy) :- place(Place), quest(Quest), remedy(Remedy), affords(Place, walk).
valid_story(Place, Quest, Remedy) :- valid(Place, Quest, Remedy).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    c, p = set(asp_valid_combos()), set(valid_combos())
    if c == p:
        print(f"OK: clingo gate matches valid_combos() ({len(c)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if c - p:
        print("  only in clingo:", sorted(c - p))
    if p - c:
        print("  only in python:", sorted(p - c))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    quest = f["quest"]
    remedy = f["remedy"]
    return [
        f'Write a short fable about a {hero.type} named {hero.id} who gets mumps, goes on a small quest, and learns a gentle lesson.',
        f"Tell a story where {hero.id} has puffed cheeks, {helper.id} sends {hero.pronoun('object')} for {quest.label}, and the day ends with {remedy.label}.",
        f'Write a child-friendly tale with humor, a quest, and transformation, ending in a wise lesson about {remedy.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    quest = f["quest"]
    remedy = f["remedy"]
    return [
        QAItem(
            question=f"What made {hero.id}'s cheeks look so puffy at the start?",
            answer=f"{hero.id} had mumps, so {hero.pronoun('possessive')} cheeks swelled up like little buns.",
        ),
        QAItem(
            question=f"Who sent {hero.id} on the small quest?",
            answer=f"{helper.id} the {helper.type} sent {hero.id} on the quest and gave wise, gentle advice.",
        ),
        QAItem(
            question=f"What did {hero.id} need to bring home before resting?",
            answer=f"{hero.id} needed to bring home {quest.phrase} before taking {remedy.phrase}.",
        ),
        QAItem(
            question=f"How did the story turn funny instead of frightening?",
            answer=f"The puffed cheeks made the day look silly, and {hero.id} found enough humor to smile through the trouble.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, the swelling faded, {hero.id} felt rested, and {hero.id} became wiser and more grateful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are mumps?",
            answer="Mumps is an illness that can make the cheeks and jaw swell up, and it can make a person feel tired.",
        ),
        QAItem(
            question="Why do people rest when they are sick?",
            answer="People rest when they are sick because the body needs quiet time and energy to heal.",
        ),
        QAItem(
            question="What is a quest in a story?",
            answer="A quest is a journey to find something, solve a problem, or learn an important lesson.",
        ),
    ]


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
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style story world about mumps, quest, humor, and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["owl", "goat", "grandmother", "rabbit"])
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
    place = args.place or rng.choice(list(PLACES))
    quest = args.quest or rng.choice(list(QUESTS))
    remedy = args.remedy or rng.choice(list(REMEDIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_kind, helper_default = rng.choice(HELPERS)
    helper_type = args.helper_type or helper_kind
    helper_name = args.helper or helper_default
    return StoryParams(
        place=place,
        hero_name=name,
        hero_type=gender,
        helper_name=helper_name,
        helper_type=helper_type,
        quest=quest,
        remedy=remedy,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    world = build_story(world, params)
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
    StoryParams(place="village", hero_name="Mina", hero_type="girl", helper_name="Owl", helper_type="owl", quest="honey", remedy="rest"),
    StoryParams(place="garden", hero_name="Toby", hero_type="boy", helper_name="Grandma", helper_type="grandmother", quest="tea", remedy="laugh"),
    StoryParams(place="cottage", hero_name="Lila", hero_type="girl", helper_name="Goat", helper_type="goat", quest="napkin", remedy="rest"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest, remedy) combos:")
        for place, quest, remedy in combos:
            print(f"  {place:10} {quest:8} {remedy:8}")
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
            header = f"### {p.name}: {p.quest} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
