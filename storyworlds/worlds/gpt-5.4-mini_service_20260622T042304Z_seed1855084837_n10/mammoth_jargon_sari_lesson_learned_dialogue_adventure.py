#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T042304Z_seed1855084837_n10/mammoth_jargon_sari_lesson_learned_dialogue_adventure.py
===============================================================================================================

A standalone storyworld for a small adventure tale about a mammoth, jargon,
and a sari. The world is built around a child-friendly quest, a confusing
phrase, a mistaken plan, and a lesson learned through dialogue.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Robust import path setup: walk upward until we find the storyworlds package.
_HERE = os.path.abspath(os.path.dirname(__file__))
_SCAN = _HERE
while True:
    if os.path.isdir(os.path.join(_SCAN, "storyworlds")):
        if _SCAN not in sys.path:
            sys.path.insert(0, _SCAN)
        break
    parent = os.path.dirname(_SCAN)
    if parent == _SCAN:
        raise RuntimeError("Could not locate storyworlds/results.py")
    _SCAN = parent

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = _copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class Place:
    id: str
    label: str
    detail: str
    adventure: str
    offers: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    risk_word: str
    mislead: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    label: str
    offer: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    quest: str
    guide: str
    child_name: str
    child_gender: str
    adult_name: str
    seed: Optional[int] = None


PLACES = {
    "museum": Place(
        id="museum",
        label="the museum hall",
        detail="Tall glass cases stood like clear towers, and banners waved above the path.",
        adventure="The hallway felt like the start of a treasure hunt.",
        offers={"jargon", "sari"},
    ),
    "market": Place(
        id="market",
        label="the busy market",
        detail="Bright cloth hung from the stalls, and bells tinkled in the wind.",
        adventure="Every turn looked like a new clue.",
        offers={"jargon", "sari"},
    ),
    "hill": Place(
        id="hill",
        label="the windy hill",
        detail="Grass leaned in the breeze, and a dirt trail climbed toward the clouds.",
        adventure="The open path made the day feel bold.",
        offers={"jargon", "sari"},
    ),
}

QUESTS = {
    "trail": Quest(
        id="trail",
        verb="follow the trail",
        gerund="following the trail",
        risk_word="tracks",
        mislead="strange jargon",
        clue="old footprints near the stones",
        tags={"mammoth", "adventure"},
    ),
    "banner": Quest(
        id="banner",
        verb="look under the banner",
        gerund="looking under the banner",
        risk_word="signs",
        mislead="jargon on the sign",
        clue="a fluttering corner of cloth",
        tags={"sari", "dialogue"},
    ),
    "echo": Quest(
        id="echo",
        verb="listen for the echo",
        gerund="listening for the echo",
        risk_word="sounds",
        mislead="mammoth-sized jargon",
        clue="a deep rumble from the far side",
        tags={"mammoth", "dialogue"},
    ),
}

GUIDES = {
    "grandma": Guide(
        id="grandma",
        label="Grandma",
        offer="a sari from the trunk",
        ending="wrapped the sari around her shoulders and smiled",
        tags={"sari", "lesson"},
    ),
    "uncle": Guide(
        id="uncle",
        label="Uncle",
        offer="a clear explanation in plain words",
        ending="pointed to the safe path and nodded",
        tags={"jargon", "lesson"},
    ),
    "sister": Guide(
        id="sister",
        label="Sister",
        offer="a gentle reminder to ask questions",
        ending="held the map steady and grinned",
        tags={"dialogue", "lesson"},
    ),
}

GIRL_NAMES = ["Asha", "Mira", "Nina", "Lila", "Tara", "Zoya"]
BOY_NAMES = ["Ravi", "Arun", "Kiran", "Dev", "Omar", "Sami"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES.values():
        for quest in QUESTS.values():
            for guide in GUIDES.values():
                if "mammoth" in quest.tags or "dialogue" in guide.tags or "sari" in place.offers:
                    combos.append((place.id, quest.id, guide.id))
    return combos


def explain_rejection(place: str, quest: str, guide: str) -> str:
    return f"(No story: {place}, {quest}, and {guide} do not make a reasonable adventure.)"


ASP_RULES = r"""
place(P) :- place_id(P).
quest(Q) :- quest_id(Q).
guide(G) :- guide_id(G).

valid(P,Q,G) :- place(P), quest(Q), guide(G), has_adventure(P), has_conflict(Q), has_lesson(G).

has_adventure(P) :- place_id(P).
has_conflict(Q) :- quest_id(Q).
has_lesson(G) :- guide_id(G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place_id", pid))
        lines.append(asp.fact("has_adventure", pid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest_id", qid))
        if "mammoth" in q.tags:
            lines.append(asp.fact("quest_mammoth", qid))
        if "dialogue" in q.tags:
            lines.append(asp.fact("quest_dialogue", qid))
    for gid, g in GUIDES.items():
        lines.append(asp.fact("guide_id", gid))
        if "sari" in g.tags:
            lines.append(asp.fact("guide_sari", gid))
        if "lesson" in g.tags:
            lines.append(asp.fact("guide_lesson", gid))
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
    if py != cl:
        print("MISMATCH between Python and ASP valid-combos gates.")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, quest=None, guide=None, name=None, gender=None, adult=None), random.Random(777)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: Python and ASP agree on {len(py)} combinations; story generation works.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with mammoth, jargon, and sari.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--quest", choices=QUESTS.keys())
    ap.add_argument("--guide", choices=GUIDES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("-n", "--n", type=int, default=1)
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
              and (args.quest is None or c[1] == args.quest)
              and (args.guide is None or c[2] == args.guide)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, guide = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["Grandma", "Uncle", "Sister"])
    return StoryParams(place=place, quest=quest, guide=guide, child_name=name, child_gender=gender, adult_name=adult)


def make_child(world: World, params: StoryParams) -> Entity:
    return world.add(
        Entity(
            id=params.child_name,
            kind="character",
            type=params.child_gender,
            role="child",
            meters={"joy": 0.0},
            memes={"curiosity": 1.0, "lesson": 0.0, "joy": 0.0},
        )
    )


def make_adult(world: World, params: StoryParams) -> Entity:
    return world.add(
        Entity(
            id=params.adult_name,
            kind="character",
            type="woman" if params.adult_name == "Grandma" else "man",
            role="guide",
            label=params.adult_name,
            meters={"patience": 1.0},
            memes={"calm": 1.0},
        )
    )


def tell(place: Place, quest: Quest, guide: Guide, child: Entity, adult: Entity) -> World:
    w = World()
    child = w.add(child)
    adult = w.add(adult)
    spot = w.add(Entity(id="spot", kind="thing", type="thing", label="the strange sign", phrase=quest.mislead, tags={"jargon"}))
    mammoth = w.add(Entity(id="mammoth", kind="thing", type="mammoth", label="a mammoth", phrase="a shaggy mammoth", tags={"mammoth"}))
    sari = w.add(Entity(id="sari", kind="thing", type="cloth", label="a sari", phrase="a bright sari", tags={"sari"}))
    w.facts["place"] = place
    w.facts["quest"] = quest
    w.facts["guide"] = guide
    w.facts["spot"] = spot
    w.facts["mammoth"] = mammoth
    w.facts["sari"] = sari
    w.say(f"{child.id} and {adult.label_word} stepped into {place.label}. {place.detail}")
    w.say(f"The air felt adventurous, and the path promised a small mystery.")
    w.para()
    w.say(f'{child.id} pointed at the sign. "It says {quest.mislead}," {child.id} said. "What does that mean?"')
    w.say(f'{adult.label_word} smiled. "{guide.offer}," {adult.label_word} said. "But first, let\'s keep the plan simple."')
    w.para()
    if guide.id == "grandma":
        w.say(f"They found {sari.phrase} waiting near the old trunk, and {child.id} gasped at its bright colors.")
    elif guide.id == "uncle":
        w.say(f"They heard a low rumble ahead, and then they saw {mammoth.phrase} near the trail.")
    else:
        w.say(f"They spotted {mammoth.phrase}, then noticed {sari.phrase} folded neatly beside the map.")
    w.say(f'{child.id} asked, "So the {quest.risk_word} are the clues?"')
    w.say(f'"Yes," said {adult.label_word}, "and your question was better than the jargon on the sign."')
    w.para()
    child.memes["lesson"] = child.memes.get("lesson", 0.0) + 1.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    child.meters["joy"] = child.meters.get("joy", 0.0) + 1.0
    w.say(f'That made {child.id} laugh, and {adult.label_word} {guide.ending}.')
    w.say(f'Together they chose the clear clue and moved on, with the {quest.gerund} adventure feeling easy to follow.')
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["place"]
    q = world.facts["quest"]
    g = world.facts["guide"]
    return [
        f'Write a short adventure story for a young child set in {p.label} that includes the words "mammoth", "jargon", and "sari".',
        f"Tell a dialogue-filled adventure where a child asks what jargon means, sees a mammoth, and learns something kind about a sari.",
        f"Write a simple story about {q.verb} at {p.label} with {g.label} helping the child choose clear words instead of jargon.",
    ]


def story_qa(world: World) -> list[QAItem]:
    place: Place = world.facts["place"]  # type: ignore[assignment]
    quest: Quest = world.facts["quest"]  # type: ignore[assignment]
    guide: Guide = world.facts["guide"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did the child ask about the jargon in {place.label}?",
            answer=f"The child saw confusing words on the sign and wanted the plan to make sense. The adult answered with plain words so the adventure stayed clear.",
        ),
        QAItem(
            question="What did the story show about the mammoth?",
            answer=f"The mammoth was part of the adventure and helped make the place feel exciting. It also gave the child something real to notice instead of guessing from jargon.",
        ),
        QAItem(
            question="How did the sari fit into the lesson learned?",
            answer=f"The sari was bright and memorable, so the child could talk about it with wonder instead of confusion. That helped the story end with better questions and clearer thinking.",
        ),
        QAItem(
            question=f"What changed after the child asked about {quest.risk_word}?",
            answer=f"The child stopped trusting the confusing wording and listened to the guide instead. By the end, the child chose the clear clue and learned that asking questions can help on an adventure.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mammoth?",
            answer="A mammoth was a huge, shaggy animal with big tusks that lived long ago.",
        ),
        QAItem(
            question="What is jargon?",
            answer="Jargon is special or confusing language that can make a message hard to understand.",
        ),
        QAItem(
            question="What is a sari?",
            answer="A sari is a long piece of cloth worn as clothing in some places, often in bright colors.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(f"- {p}" for p in sample.prompts)
    parts.append("")
    parts.append("== story QA ==")
    for qa in sample.story_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    parts.append("")
    parts.append("== world QA ==")
    for qa in sample.world_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="museum", quest="banner", guide="grandma", child_name="Asha", child_gender="girl", adult_name="Grandma"),
    StoryParams(place="market", quest="trail", guide="uncle", child_name="Ravi", child_gender="boy", adult_name="Uncle"),
    StoryParams(place="hill", quest="echo", guide="sister", child_name="Lila", child_gender="girl", adult_name="Sister"),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.quest not in QUESTS or params.guide not in GUIDES:
        raise StoryError("Invalid story parameters.")
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    guide = GUIDES[params.guide]
    world = tell(place, quest, guide, make_child(World(), params), make_adult(World(), params))
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                p = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
