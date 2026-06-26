#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/trillion_satellite_quest_mystery.py
===============================================================================================================

A small mystery-quest storyworld about a careful search for a missing satellite
token, a strange trillion-count clue, and a child who solves the puzzle by
following physical traces and social hunches.

The seed words are honored directly:
- trillion
- satellite

The style aims for child-facing mystery with a clear quest, clues, suspicion,
and a satisfying reveal.
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
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
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
class Place:
    id: str
    label: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    text: str
    kind: str
    hint_place: str = ""


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    value: str
    location: str
    tricky: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    quest: str
    clue: str
    prize: str
    name: str
    companion: str
    seed: Optional[int] = None


PLACES = {
    "observatory": Place(
        id="observatory",
        label="the observatory",
        detail="A round glass dome held the night close like a secret.",
        affords={"search", "listen", "climb"},
    ),
    "museum": Place(
        id="museum",
        label="the museum hall",
        detail="Glass cases lined the room, and every shadow looked important.",
        affords={"search", "ask", "read"},
    ),
    "rooftop": Place(
        id="rooftop",
        label="the rooftop garden",
        detail="Wind brushed the leaves, and antennas pointed at the sky.",
        affords={"search", "climb", "watch"},
    ),
}

QUESTS = {
    "find_satellite": QuestItem(
        id="find_satellite",
        label="the satellite model",
        phrase="a silver satellite model with one blue wing",
        value="satellite",
        location="hidden_box",
        tricky="it had been tucked inside a display crate",
    ),
    "recover_transmitter": QuestItem(
        id="recover_transmitter",
        label="the transmitter",
        phrase="a tiny transmitter with a blinking light",
        value="signal",
        location="tool_drawer",
        tricky="it had slipped behind a row of maps",
    ),
}

CLUES = {
    "dust": Clue(
        id="dust",
        label="dust",
        text="A thin line of dust pointed away from the display shelf.",
        kind="physical",
        hint_place="storage_room",
    ),
    "chime": Clue(
        id="chime",
        label="chime",
        text="A little wind chime kept tapping near the roof door.",
        kind="sound",
        hint_place="rooftop",
    ),
    "sticker": Clue(
        id="sticker",
        label="sticker",
        text="A star sticker clung to the corner of a map drawer.",
        kind="object",
        hint_place="museum",
    ),
    "trillion": Clue(
        id="trillion",
        label="trillion",
        text="Someone had written 'trillion' on a note, but the tall stack of
numbers turned out to be a joke: it meant 'a very, very big count'.",
        kind="message",
        hint_place="observatory",
    ),
}

COMPANIONS = {
    "mom": {"type": "mother", "label": "Mom"},
    "dad": {"type": "father", "label": "Dad"},
    "friend": {"type": "boy", "label": "a friend"},
    "guide": {"type": "woman", "label": "the guide"},
}

NAMES = ["Mia", "Leo", "Nora", "Theo", "Ava", "Ben", "Luna", "Owen"]
TENSIONS = ["curious", "careful", "brave", "quiet", "bright", "wary"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small mystery quest about a missing satellite clue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--prize", choices=["satellite", "signal"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=COMPANIONS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES.values():
        for qid, quest in QUESTS.items():
            for cid, clue in CLUES.items():
                if clue.hint_place in {place.id, "observatory", "museum", "rooftop"}:
                    out.append((place.id, qid, cid))
    return sorted(set(out))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.quest is None or c[1] == args.quest)
        and (args.clue is None or c[2] == args.clue)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, clue = rng.choice(filtered)
    prize = args.prize or QUESTS[quest].value
    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice(list(COMPANIONS))
    return StoryParams(place=place, quest=quest, clue=clue, prize=prize, name=name, companion=companion)


def _do_search(world: World, hero: Entity, quest: QuestItem, clue: Clue) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    hero.meters["searching"] = hero.meters.get("searching", 0.0) + 1
    if clue.id == "trillion":
        world.say("The note said trillion, and that made the whole search feel bigger than the room.")
    if quest.location == "hidden_box":
        world.say("The child lifted the crate lid, and a tiny silver shape flashed underneath.")
    else:
        world.say("The child followed the hint until the place in the clue matched the place in the room.")


def tell(place: Place, quest: QuestItem, clue: Clue, hero_name: str, companion_key: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="child", label=hero_name))
    comp_info = COMPANIONS[companion_key]
    companion = world.add(Entity(id="companion", kind="character", type=comp_info["type"], label=comp_info["label"]))
    prize = world.add(Entity(
        id="prize",
        type=quest.value,
        label=quest.label,
        phrase=quest.phrase,
        owner=hero.id,
        caretaker=companion.id,
        hidden_in=quest.location,
    ))
    note = world.add(Entity(id="note", type="note", label="the note", phrase=clue.text))
    hero.memes["curiosity"] = 1.0
    companion.memes["care"] = 1.0

    world.say(f"{hero.id} and {companion.label} came to {place.label}.")
    world.say(place.detail)
    world.say(f"They were on a quest for {prize.phrase}, but the room had a mystery in it.")
    world.para()
    world.say(f"{clue.text}")
    _do_search(world, hero, quest, clue)
    world.say(f"{companion.label} frowned at the clue and said the answer had to be hiding somewhere simple.")
    world.para()
    prize.meters["found"] = 1.0
    prize.hidden_in = None
    hero.memes["joy"] = 1.0
    world.say(f"At last, {hero.id} found {prize.phrase}.")
    world.say(f"It had been {quest.tricky}, but now the satellite was safe in {hero.id}'s hands.")
    world.say(f"The little quest ended with a quiet grin, and the night felt less mysterious than before.")

    world.facts.update(hero=hero, companion=companion, prize=prize, clue=clue, quest=quest, note=note, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    return [
        f"Write a child-friendly mystery about {hero.id} solving a quest for {quest.label}.",
        f"Tell a short story with the words trillion and satellite, where a clue helps uncover the answer.",
        f"Write a gentle mystery where a child follows a clue, asks careful questions, and finishes the quest.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    comp = f["companion"]
    quest = f["quest"]
    clue = f["clue"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who went on the quest in {place.label}?",
            answer=f"{hero.id} went with {comp.label} on a quiet quest in {place.label}.",
        ),
        QAItem(
            question="What clue made the search feel strange?",
            answer=f"The clue about {clue.label} made the search feel strange, and it even used the word trillion.",
        ),
        QAItem(
            question=f"What did they finally find?",
            answer=f"They finally found {quest.phrase}, which was the lost satellite model.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a satellite?",
            answer="A satellite is something that goes around a planet, or a model made to look like one.",
        ),
        QAItem(
            question="What does a clue do in a mystery?",
            answer="A clue gives a hint that can help someone solve a mystery.",
        ),
        QAItem(
            question="What does trillion mean?",
            answer="Trillion is a very, very big number. People also use it to mean an enormous amount.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  place={world.place.id}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], QUESTS[params.quest], CLUES[params.clue], params.name, params.companion)
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


ASP_RULES = r"""
place(P) :- setting(P).
quest(Q) :- quest_item(Q).
clue(C) :- clue_item(C).

fits(P,Q,C) :- place(P), quest(Q), clue(C), clue_hint(C,P).
valid(P,Q,C) :- fits(P,Q,C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest_item", qid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue_item", cid))
        lines.append(asp.fact("clue_hint", cid, clue.hint_place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
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


def build_story_samples(args: argparse.Namespace, base_seed: int) -> list[StorySample]:
    samples: list[StorySample] = []
    seen: set[str] = set()
    if args.all:
        curated = [
            StoryParams("observatory", "find_satellite", "trillion", "satellite", "Mia", "mom"),
            StoryParams("museum", "recover_transmitter", "sticker", "signal", "Leo", "dad"),
            StoryParams("rooftop", "find_satellite", "chime", "satellite", "Nora", "guide"),
        ]
        for p in curated:
            samples.append(generate(p))
        return samples
    i = 0
    while len(samples) < args.n and i < max(args.n * 50, 50):
        seed = base_seed + i
        i += 1
        rng = random.Random(seed)
        try:
            params = resolve_params(args, rng)
        except StoryError as e:
            print(e)
            return []
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, quest, clue) combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = build_story_samples(args, base_seed)
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
            header = f"### {p.name}: {p.quest} at {p.place} (clue: {p.clue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
