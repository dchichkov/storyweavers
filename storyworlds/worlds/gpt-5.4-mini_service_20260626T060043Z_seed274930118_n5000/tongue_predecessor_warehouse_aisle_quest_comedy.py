#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tongue_predecessor_warehouse_aisle_quest_comedy.py
==============================================================================================================

A small comedy-leaning story world set in a warehouse aisle, with a quest, a
tongue-shaped mishap, and a predecessor who leaves behind a very silly clue.

The seed image is a short tale: a junior warehouse helper arrives in a narrow
aisle, follows a predecessor's old note, gets tangled up in a tongue-related
mix-up, and finishes the quest by solving the problem with laughs instead of
grumpiness.

The world is modeled as state:
- typed entities with physical meters and emotional memes
- a quest that changes location, risk, and mood
- a predecessor who can be helpful, teasing, or absent
- a comedic turn where the tongue detail matters both literally and figuratively

The story remains child-facing and complete: beginning, middle turn, and ending
image are all driven by the simulated world.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class WarehouseAisle:
    aisle_name: str = "warehouse aisle"
    place_phrase: str = "the warehouse aisle"
    rows: int = 5
    narrow: bool = True
    inventory: list[str] = field(default_factory=list)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    risk: str
    clue: str
    plural: bool = False


@dataclass
class Quest:
    id: str
    title: str
    goal: str
    action: str
    stumble: str
    resolution: str
    keyword: str = "quest"


@dataclass
class World:
    setting: WarehouseAisle
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: Entity(**{
            "id": e.id, "kind": e.kind, "type": e.type, "label": e.label,
            "phrase": e.phrase, "owner": e.owner, "caretaker": e.caretaker,
            "plural": e.plural, "meters": dict(e.meters), "memes": dict(e.memes)
        }) for k, e in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    predecessor_name: str
    predecessor_type: str
    item: str
    quest: str
    seed: Optional[int] = None


HERO_NAMES = ["Milo", "Pia", "Jun", "Tess", "Nora", "Ari"]
HERO_TYPES = ["boy", "girl"]
PREDECESSOR_NAMES = ["Mabel", "Otto", "Rina", "Bert"]
PREDECESSOR_TYPES = ["woman", "man"]
TRAITS = ["curious", "spry", "cheerful", "silly"]
SETTING = WarehouseAisle()

QUEST_ITEMS = {
    "tongue_tag": QuestItem(
        id="tongue_tag",
        label="tongue tag",
        phrase="a bright tongue-shaped tag",
        risk="kept getting stuck in tape",
        clue="look for the tongue tag near the blue crate",
    ),
    "clipboard": QuestItem(
        id="clipboard",
        label="clipboard",
        phrase="an old clipboard",
        risk="got bumped by a swinging box flap",
        clue="the clipboard waits behind the snack shelf",
    ),
    "bell": QuestItem(
        id="bell",
        label="delivery bell",
        phrase="a tiny delivery bell",
        risk="kept jingling and giving away the hiding spot",
        clue="listen for the bell beside aisle four",
    ),
}

QUESTS = {
    "find_tongue_tag": Quest(
        id="find_tongue_tag",
        title="The Tongue Tag Quest",
        goal="find the missing tongue tag",
        action="follow the clue and rescue the tag",
        stumble="the tongue kept sticking out whenever the hero got flustered",
        resolution="the predecessor's joke map pointed straight to the tag",
    ),
    "return_clipboard": Quest(
        id="return_clipboard",
        title="The Clipboard Quest",
        goal="return the old clipboard",
        action="carry it through the aisle without dropping it",
        stumble="the clipboard slid whenever the hero laughed too hard",
        resolution="a careful two-handed grip made the rest of the trip easy",
    ),
    "ring_bell": Quest(
        id="ring_bell",
        title="The Bell Quest",
        goal="ring the tiny delivery bell",
        action="tiptoe to the end of the aisle and ring it",
        stumble="the bell only worked when the hero stopped giggling",
        resolution="one brave tap made the whole aisle cheer",
    ),
}


class ReasonableQuestGate:
    @staticmethod
    def valid(params: StoryParams) -> bool:
        return params.item in QUEST_ITEMS and params.quest in QUESTS

    @staticmethod
    def explain_invalid(params: StoryParams) -> str:
        return "The chosen item or quest does not fit this warehouse aisle comedy."


def infer_vibe(item: QuestItem, quest: Quest) -> str:
    if item.id == "tongue_tag":
        return "tongue-in-cheek"
    if item.id == "clipboard":
        return "bookish"
    return "bouncy"


def set_emotion(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def set_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def intro(world: World, hero: Entity, predecessor: Entity, item: QuestItem, quest: Quest) -> None:
    set_emotion(hero, "curiosity", 1)
    set_emotion(predecessor, "fondness", 1)
    world.say(
        f"{hero.id} was a little {hero.type} with a bright grin and a big wish to finish "
        f"{quest.goal} in {world.setting.place_phrase}."
    )
    world.say(
        f"{hero.id}'s predecessor, {predecessor.id}, had left behind {item.phrase} and a note "
        f"that read, '{item.clue}.'"
    )
    world.say(
        f"It sounded like a proper quest, even though the note was folded into a paper boat "
        f"and had a doodle of a smiling tongue on the back."
    )


def setup(world: World, hero: Entity, item: QuestItem, quest: Quest) -> None:
    set_emotion(hero, "hope", 1)
    set_meter(hero, "prepared", 1)
    world.say(
        f"{hero.id} tucked the note into {hero.pronoun('possessive')} pocket and set off to "
        f"{quest.action}."
    )
    world.say(
        f"The {world.setting.aisle_name} was narrow, with tall boxes on both sides and enough "
        f"echo to make every little step sound like a drum roll."
    )


def stumble(world: World, hero: Entity, predecessor: Entity, item: QuestItem, quest: Quest) -> None:
    set_emotion(hero, "flustered", 1)
    set_emotion(hero, "joy", 1)
    set_meter(hero, "messy", 1)
    world.say(
        f"But the moment {hero.id} tried to hurry, {quest.stumble}, and {hero.pronoun()} ended "
        f"up sticking {hero.pronoun('possessive')} tongue out so far that even {predecessor.id} "
        f"would have laughed."
    )
    world.say(
        f"A strip of packing tape tickled {hero.id}'s sleeve, and that made the whole search feel "
        f"like a goofy dance instead of a serious job."
    )


def hint(world: World, hero: Entity, predecessor: Entity, item: QuestItem, quest: Quest) -> None:
    set_emotion(predecessor, "pride", 1)
    world.say(
        f"Then {predecessor.id}'s old joke map turned out to be useful after all: it pointed to the "
        f"blue crate, just where {item.label} had been hiding."
    )
    world.say(
        f"{hero.id} snorted a laugh, wiped {hero.pronoun('possessive')} nose, and followed the map "
        f"with a much steadier step."
    )


def resolve(world: World, hero: Entity, predecessor: Entity, item: QuestItem, quest: Quest) -> None:
    set_emotion(hero, "pride", 1)
    set_emotion(hero, "relief", 1)
    set_meter(hero, "quest_done", 1)
    world.say(
        f"At last, {hero.id} lifted {item.phrase} with both hands and finished the quest."
    )
    world.say(
        f"{predecessor.id} clapped, the boxes seemed less tall, and the silly tongue on the note "
        f"felt less like a joke and more like a cheerful clue."
    )
    world.say(
        f"By the end, {hero.id} was smiling in {world.setting.place_phrase}, and the aisle looked "
        f"as if it had been made for jokes, clues, and brave little helpers."
    )


def build_world(params: StoryParams) -> World:
    if not ReasonableQuestGate.valid(params):
        raise StoryError(ReasonableQuestGate.explain_invalid(params))

    world = World(setting=SETTING)
    item = QUEST_ITEMS[params.item]
    quest = QUESTS[params.quest]

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name.lower(),
        phrase=f"a cheerful little {params.hero_type}",
    ))
    predecessor = world.add(Entity(
        id=params.predecessor_name,
        kind="character",
        type=params.predecessor_type,
        label=params.predecessor_name.lower(),
        phrase=f"a kind old {params.predecessor_type}",
    ))
    world.add(Entity(
        id=item.id,
        kind="thing",
        type="item",
        label=item.label,
        phrase=item.phrase,
        owner=hero.id,
        caretaker=predecessor.id,
    ))

    world.facts.update(
        hero=hero,
        predecessor=predecessor,
        item=item,
        quest=quest,
    )

    intro(world, hero, predecessor, item, quest)
    world.para()
    setup(world, hero, item, quest)
    stumble(world, hero, predecessor, item, quest)
    world.para()
    hint(world, hero, predecessor, item, quest)
    resolve(world, hero, predecessor, item, quest)
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [(item_id, quest_id) for item_id in QUEST_ITEMS for quest_id in QUESTS]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for item_id in QUEST_ITEMS:
        lines.append(asp.fact("item", item_id))
    for quest_id in QUESTS:
        lines.append(asp.fact("quest", quest_id))
    return "\n".join(lines)


ASP_RULES = r"""
valid(I,Q) :- item(I), quest(Q).
#show valid/2.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("Python only:", sorted(py - cl))
    print("ASP only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy quest in a warehouse aisle.")
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--predecessor", choices=PREDECESSOR_NAMES)
    ap.add_argument("--predecessor-type", choices=PREDECESSOR_TYPES)
    ap.add_argument("--item", choices=QUEST_ITEMS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    item = args.item or rng.choice(list(QUEST_ITEMS))
    quest = args.quest or rng.choice(list(QUESTS))
    name = args.name or rng.choice(HERO_NAMES)
    hero_type = args.gender or rng.choice(HERO_TYPES)
    predecessor_name = args.predecessor or rng.choice(PREDECESSOR_NAMES)
    predecessor_type = args.predecessor_type or rng.choice(PREDECESSOR_TYPES)
    params = StoryParams(
        hero_name=name,
        hero_type=hero_type,
        predecessor_name=predecessor_name,
        predecessor_type=predecessor_type,
        item=item,
        quest=quest,
    )
    if not ReasonableQuestGate.valid(params):
        raise StoryError(ReasonableQuestGate.explain_invalid(params))
    return params


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item: QuestItem = f["item"]
    quest: Quest = f["quest"]
    hero: Entity = f["hero"]
    predecessor: Entity = f["predecessor"]
    return [
        f'Write a funny story for a young child about a warehouse aisle quest and the word "{item.label}".',
        f"Tell a comedy story where {hero.id} follows a predecessor's clue to {quest.goal} in the warehouse aisle.",
        f"Write a playful quest story with a silly note, a tongue-related joke, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    predecessor: Entity = f["predecessor"]
    item: QuestItem = f["item"]
    quest: Quest = f["quest"]
    return [
        QAItem(
            question=f"Who went on the quest in the warehouse aisle?",
            answer=f"{hero.id} went on the quest, and {predecessor.id} helped by leaving a clue."
        ),
        QAItem(
            question=f"What did {predecessor.id} leave behind for {hero.id}?",
            answer=f"{predecessor.id} left behind {item.phrase} and a silly note that pointed to the next step."
        ),
        QAItem(
            question=f"How did the quest end?",
            answer=f"It ended happily when {hero.id} found {item.label} and finished {quest.goal}."
        ),
        QAItem(
            question=f"Why was the story funny?",
            answer="It was funny because the clue had a tongue joke, the aisle echoed like a drum, and the hero got flustered in a harmless way."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a warehouse aisle?",
            answer="A warehouse aisle is a long, narrow path between stacks of boxes or shelves where people can walk and carry things."
        ),
        QAItem(
            question="What is a predecessor?",
            answer="A predecessor is someone who had the job or place before another person did."
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or search for something important, and it usually has a goal to reach."
        ),
        QAItem(
            question="What does a tongue do?",
            answer="A tongue helps you taste, talk, and make funny faces when you are playing or thinking hard."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible item/quest combos:")
        for item, quest in combos:
            print(f"  {item:12} {quest}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for item in QUEST_ITEMS:
            for quest in QUESTS:
                params = StoryParams(
                    hero_name="Milo",
                    hero_type="boy",
                    predecessor_name="Mabel",
                    predecessor_type="woman",
                    item=item,
                    quest=quest,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
