#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/drown_insurance_icy_sidewalk_quest_reconciliation_animal.py
==============================================================================================================

A tiny animal storyworld set on an icy sidewalk.

Premise:
- Two small animal friends leave home on a winter quest.
- They need to find an insurance card before a clinic closes.
- The icy sidewalk makes the trip tense, and a disagreement turns into
  reconciliation before the ending.

Design goals:
- Child-facing animal story with a clear beginning, middle turn, and ending.
- Simulated state with physical meters and emotional memes.
- Python reasonableness gate plus an inline ASP twin.
- Grounded prompts, story QA, and world-knowledge QA.

The key seed words are included in the domain:
- drown
- insurance
Setting:
- icy sidewalk
Features:
- Quest
- Reconciliation
Style:
- Animal Story
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"cat", "rabbit", "fox", "mouse", "squirrel", "duck", "bird"}
        male = {"dog", "bear", "otter", "badger", "wolf"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    icy: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str = "sidewalk"
    quest_item: str = "insurance_card"
    hero: str = "Milo"
    hero_type: str = "rabbit"
    friend: str = "Pip"
    friend_type: str = "dog"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


QUESTS = {
    "insurance_card": QuestItem("insurance_card", "insurance card", "a small insurance card", {"insurance"}),
    "red_hat": QuestItem("red_hat", "red hat", "a red hat", {"hat"}),
}

PLACES = {
    "sidewalk": Place("sidewalk", "the icy sidewalk", True, {"icy sidewalk", "ice", "drown"}),
}

GIRL_NAMES = ["Mina", "Tia", "Luna", "Mabel", "Nina"]
BOY_NAMES = ["Milo", "Pip", "Theo", "Ollie", "Rex"]
TRAITS = ["brave", "curious", "gentle", "cheerful", "stubborn"]


def valid_combos() -> list[tuple[str, str]]:
    return [("sidewalk", "insurance_card")]


def reason_check(place: Place, quest: QuestItem) -> bool:
    return place.icy and "insurance" in quest.tags


def explain_rejection(place: Place, quest: QuestItem) -> str:
    return f"(No story: this world needs the icy sidewalk and the insurance quest.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.icy:
            lines.append(asp.fact("icy", pid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest_item", qid))
        for t in sorted(q.tags):
            lines.append(asp.fact("tagged", qid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Q) :- place(P), quest_item(Q), icy(P), tagged(Q, insurance).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH:")
        print(" python:", sorted(py - cl))
        print(" clingo:", sorted(cl - py))
        return 1
    print(f"OK: clingo matches python ({len(py)} combo).")
    sample = generate(resolve_params(argparse.Namespace(place=None, quest_item=None, hero=None, hero_type=None, friend=None, friend_type=None), random.Random(7)))
    assert sample.story
    print("OK: smoke story generated.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld: an icy sidewalk quest and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest-item", choices=QUESTS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=sorted({n for n in ["cat", "rabbit", "fox", "mouse", "squirrel", "dog", "bear", "otter"]}))
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=sorted({n for n in ["cat", "rabbit", "fox", "mouse", "squirrel", "dog", "bear", "otter"]}))
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest_item is None or c[1] == args.quest_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest_item = rng.choice(combos)
    hero_type = args.hero_type or rng.choice(["cat", "rabbit", "fox", "mouse", "squirrel"])
    friend_type = args.friend_type or rng.choice(["dog", "bear", "otter", "cat", "rabbit"])
    hero_pool = GIRL_NAMES + BOY_NAMES
    friend_pool = [n for n in GIRL_NAMES + BOY_NAMES if n != args.hero]
    return StoryParams(
        place=place,
        quest_item=quest_item,
        hero=args.hero or rng.choice(hero_pool),
        hero_type=hero_type,
        friend=args.friend or rng.choice(friend_pool),
        friend_type=friend_type,
    )


def _set(ent: Entity, **vals) -> None:
    for k, v in vals.items():
        ent.meters.setdefault(k, 0.0)
        ent.memes.setdefault(k, 0.0)
        if isinstance(v, (int, float)):
            ent.meters[k] = float(v)
        else:
            ent.memes[k] = float(v)


def tell(place: Place, quest: QuestItem, hero_name: str, hero_type: str, friend_name: str, friend_type: str) -> World:
    w = World(place)
    hero = w.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", label=hero_name, tags={"animal"}))
    friend = w.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend", label=friend_name, tags={"animal"}))
    item = w.add(Entity(id=quest.id, kind="thing", type="paper", label=quest.label, phrase=quest.phrase, tags=set(quest.tags)))
    w.facts.update(hero=hero, friend=friend, item=item, place=place, quest=quest)

    _set(hero, joy=0, worry=0, resolve=0, reconciliation=0)
    _set(friend, joy=0, worry=0, resolve=0, reconciliation=0)
    item.meters.setdefault("carried", 0.0)

    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    w.say(f"On the icy sidewalk, {hero_name} the {hero_type} and {friend_name} the {friend_type} set out together.")
    w.say(f"They were on a little quest to bring back {quest.phrase} before the clinic door closed.")

    w.para()
    hero.memes["worry"] += 1
    friend.memes["resolve"] += 1
    w.say(f"The sidewalk glittered with ice, and the wind made the paper quiver in {hero_name}'s paws.")
    w.say(f"{friend_name} said the trip would be fine, but {hero_name} worried that a slip could drown the bag in a slushy puddle.")

    w.para()
    hero.memes["grumpy"] = 1
    friend.memes["hurt"] = 1
    w.say(f"When {friend_name} hurried ahead, {hero_name} snapped, and the two animals stopped with their backs turned.")
    w.say(f"The quest felt heavy until {hero_name} saw {friend_name} skidding near the curb and called out a warning.")

    w.para()
    hero.memes["reconciliation"] += 1
    friend.memes["reconciliation"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1)
    friend.memes["hurt"] = max(0.0, friend.memes.get("hurt", 0.0) - 1)
    w.say(f"{hero_name} apologized first, and {friend_name} apologized too.")
    w.say(f"They walked slower together, held the insurance card safe, and reached the clinic just in time.")

    w.para()
    item.meters["carried"] = 1.0
    w.say(f"At the end, the insurance card lay warm and dry in {hero_name}'s paws, and the friends went home side by side.")
    w.facts.update(resolved=True)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a young child about a quest on the "{f["place"].label}" and include the word "insurance".',
        f"Tell a gentle animal story where {f['hero'].id} and {f['friend'].id} must find an insurance card on the icy sidewalk and make up after a quarrel.",
        f'Write a short winter story with animals, a slippery sidewalk, a quest, and reconciliation; include the word "drown".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, item, place, quest = f["hero"], f["friend"], f["item"], f["place"], f["quest"]
    return [
        QAItem(
            question=f"What were {hero.id} and {friend.id} trying to do on the icy sidewalk?",
            answer=f"They were on a quest to bring back {quest.phrase} before the clinic closed. The trip mattered because the insurance card had to stay safe and dry.",
        ),
        QAItem(
            question=f"Why did {hero.id} worry while they walked?",
            answer=f"{hero.id} worried because the sidewalk was icy and a slip could send their things into a slushy puddle. That meant the insurance card might get wet if they were careless.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} fix their disagreement?",
            answer=f"{hero.id} apologized first, and {friend.id} apologized too. After that, they slowed down, stayed together, and finished the quest peacefully.",
        ),
        QAItem(
            question=f"What proved that the quest ended well?",
            answer=f"The insurance card was still warm and dry in {hero.id}'s paws at the end. That ending shows they kept the card safe and made up before going home.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does insurance help with?",
            answer="Insurance is a promise or plan that helps pay for help when something goes wrong. It can make a hard problem less scary for a family.",
        ),
        QAItem(
            question="What should you do on an icy sidewalk?",
            answer="You should walk slowly, keep your balance, and stay close to a helper. Slow steps help you avoid slipping on the ice.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means two people make up after a fight. They apologize and start being kind again.",
        ),
        QAItem(
            question="Can something drown in water?",
            answer="Yes. If a living thing gets trapped underwater and cannot breathe, it can drown, so water safety matters.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="sidewalk", quest_item="insurance_card", hero="Milo", hero_type="rabbit", friend="Pip", friend_type="dog"),
    StoryParams(place="sidewalk", quest_item="insurance_card", hero="Mina", hero_type="fox", friend="Tia", friend_type="cat"),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.quest_item not in QUESTS:
        raise StoryError("Invalid story parameters.")
    world = tell(PLACES[params.place], QUESTS[params.quest_item], params.hero, params.hero_type, params.friend, params.friend_type)
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
        model = asp.one_model(asp_program("#show valid/2."))
        for a, b in asp.atoms(model, "valid"):
            print(a, b)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
