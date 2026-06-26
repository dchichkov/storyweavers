#!/usr/bin/env python3
"""
storyworlds/worlds/click_quest_bad_ending_misunderstanding_slice_of.py
======================================================================

A small slice-of-life story world about a click-based quest, a friendly
misunderstanding, and a bad ending that still feels true to everyday life.

Premise:
- A child is excited about a simple click quest at home or in a cozy public place.
- The quest has a clear goal, but the child misreads a clue.
- The misunderstanding causes a small, concrete failure: the quest ends badly.
- The story stays grounded in ordinary objects, feelings, and consequences.

This script follows the storyworld contract:
- standalone stdlib script
- shared result containers imported eagerly
- lazy clingo import via storyworlds/asp.py helpers
- StoryParams, parser, resolve_params, generate, emit, main
- optional ASP twin, verify mode, JSON, QA, trace, seed, all
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister", "grandma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother", "grandpa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    label: str
    verb: str
    goal: str
    clue: str
    click_target: str
    mistake: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    ownerable: bool = True


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("confusion", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("quest_hype", 0.0) < THRESHOLD:
            continue
        sig = ("misunderstanding", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["misunderstood"] = actor.memes.get("misunderstood", 0.0) + 1
        out.append(f"{actor.label} took the clue the wrong way.")
    return out


def _r_bad_ending(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("misunderstood", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("progress", 0.0) < 1.0:
            sig = ("bad_ending", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["disappointment"] = actor.memes.get("disappointment", 0.0) + 1
            out.append(f"The quest ended the wrong way.")
    return out


def _r_spill_regret(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("disappointment", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("mess", 0.0) < THRESHOLD:
            continue
        sig = ("regret", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["regret"] = actor.memes.get("regret", 0.0) + 1
        out.append(f"{actor.label} wished the click had been slower and calmer.")
    return out


CAUSAL_RULES = [_r_misunderstanding, _r_bad_ending, _r_spill_regret]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_story(world: World, hero: Entity, guide: Entity, quest: Quest, prize: Prize) -> None:
    world.say(
        f"{hero.label} was a little {hero.type} who loved a small click quest at {world.place.label}."
    )
    world.say(
        f"The quest was to {quest.verb} and find {quest.goal}; the prize was {prize.phrase}."
    )
    world.para()
    world.say(
        f"One afternoon, {guide.label} pointed at the screen and read the clue: {quest.clue}."
    )
    world.say(
        f"{hero.label} smiled, but {hero.pronoun()} misunderstood it and clicked {quest.click_target} instead."
    )
    hero.memes["quest_hype"] = hero.memes.get("quest_hype", 0.0) + 1
    hero.memes["confusion"] = hero.memes.get("confusion", 0.0) + 1
    hero.meters["mess"] = hero.meters.get("mess", 0.0) + 1
    if quest.id in {"library", "kiosk"}:
        hero.meters["progress"] = 0.0
    else:
        hero.meters["progress"] = 0.5
    propagate(world, narrate=True)
    world.para()
    if hero.memes.get("disappointment", 0.0) >= THRESHOLD:
        world.say(
            f"In the end, {quest.ending}, and {hero.label} sat quietly beside the table."
        )
        world.say(
            f"{guide.label} did not scold {hero.pronoun('object')}; {guide.pronoun()} only said they could try again another day."
        )
    else:
        world.say(
            f"The quest paused with a small sigh, and the room stayed calm and ordinary."
        )

    world.facts.update(hero=hero, guide=guide, quest=quest, prize=prize)


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen table", indoor=True, affords={"tablet", "sticker"}),
    "living_room": Place(id="living_room", label="the living room couch", indoor=True, affords={"tablet", "remote"}),
    "library": Place(id="library", label="the library corner", indoor=True, affords={"terminal", "sticker"}),
}

QUESTS = {
    "tablet": Quest(
        id="tablet",
        label="tablet quest",
        verb="tap the three bright stars",
        goal="the gold badge",
        clue="Click the blue button to begin",
        click_target="the red stop button",
        mistake="the stop button looked like the start button",
        ending="the badge vanished before the stars were counted",
        tags={"click", "quest", "misunderstanding", "bad_ending"},
    ),
    "sticker": Quest(
        id="sticker",
        label="sticker quest",
        verb="click each picture in order",
        goal="the fox sticker",
        clue="Click the picture that looks like a fox first",
        click_target="the squirrel picture",
        mistake="the squirrel looked friendlier than the fox",
        ending="the sticker sheet ran out before the fox was found",
        tags={"click", "quest", "misunderstanding", "bad_ending"},
    ),
    "terminal": Quest(
        id="terminal",
        label="catalog quest",
        verb="click the names in the right order",
        goal="the borrowed book slip",
        clue="Click the name with the orange dot",
        click_target="the gray name tag",
        mistake="the gray tag seemed safe and plain",
        ending="the screen timed out and the slip was lost",
        tags={"click", "quest", "misunderstanding", "bad_ending"},
    ),
}

PRIZES = {
    "badge": Prize(id="badge", label="badge", phrase="a shiny gold badge", type="badge"),
    "sticker": Prize(id="sticker", label="sticker", phrase="a fox sticker", type="sticker"),
    "slip": Prize(id="slip", label="slip", phrase="a borrowed book slip", type="paper"),
}

HERO_NAMES = ["Nia", "Milo", "Ari", "Luna", "Toby", "Pia"]
GUIDE_NAMES = ["Mom", "Dad", "Aunt Jo", "Grandma", "Mr. Lee", "Sister Ana"]
HERO_TYPES = {"girl", "boy"}
GUIDE_TYPES = {"mother", "father", "aunt", "grandma", "man", "woman"}


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    hero_type: str
    guide_name: str
    guide_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for quest_id in place.affords:
            for prize_id in PRIZES:
                combos.append((place_id, quest_id, prize_id))
    return combos


def reasonableness_gate(place: str, quest: Quest, prize: Prize) -> bool:
    return place in PLACES and quest.id in QUESTS and prize.id in PRIZES


def explain_rejection(place: str, quest: Quest, prize: Prize) -> str:
    return (
        f"(No story: {place} does not fit the quest/prize pairing in a natural slice-of-life way.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life click quest with a misunderstanding and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=sorted(HERO_TYPES))
    ap.add_argument("--guide-name")
    ap.add_argument("--guide-type", choices=sorted(GUIDE_TYPES))
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    place_id, quest_id, prize_id = rng.choice(sorted(combos))
    quest = QUESTS[quest_id]
    prize = PRIZES[prize_id]
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    guide_name = args.guide_name or rng.choice(GUIDE_NAMES)
    guide_type = args.guide_type or rng.choice(["mother", "father", "grandma", "aunt", "woman", "man"])
    name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(
        place=place_id,
        quest=quest_id,
        prize=prize_id,
        name=name,
        hero_type=hero_type,
        guide_name=guide_name,
        guide_type=guide_type,
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    prize = PRIZES[params.prize]
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.name))
    guide = world.add(Entity(id="guide", kind="character", type=params.guide_type, label=params.guide_name))
    world.add(Entity(id="quest_item", type=prize.type, label=prize.label, phrase=prize.phrase, owner=hero.id))
    build_story(world, hero, guide, quest, prize)

    prompts = [
        f"Write a short slice-of-life story about a child named {params.name} who tries a click quest at {place.label}.",
        f"Tell a gentle story where a misunderstanding causes a click quest to end badly.",
        f"Write an everyday story with a small mistake, a click, and a disappointing ending image.",
    ]

    story_qa = [
        QAItem(
            question=f"Where did {params.name} try the click quest?",
            answer=f"{params.name} tried the click quest at {place.label}.",
        ),
        QAItem(
            question=f"What went wrong during the quest?",
            answer=f"{params.name} misunderstood the clue and clicked the wrong thing, so the quest ended badly.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with a quiet, disappointing ending instead of a win.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a click quest?",
            answer="A click quest is a small game or task where someone solves clues by clicking the right thing.",
        ),
        QAItem(
            question="What does misunderstanding mean?",
            answer="A misunderstanding happens when someone gets the meaning wrong and acts on the wrong idea.",
        ),
        QAItem(
            question="What is a bad ending in a story?",
            answer="A bad ending is an ending where things do not turn out the way the character hoped.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.location:
            parts.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", quest="tablet", prize="badge", name="Nia", hero_type="girl", guide_name="Mom", guide_type="mother"),
    StoryParams(place="living_room", quest="sticker", prize="sticker", name="Milo", hero_type="boy", guide_name="Dad", guide_type="father"),
    StoryParams(place="library", quest="terminal", prize="slip", name="Ari", hero_type="girl", guide_name="Grandma", guide_type="grandma"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoor:
            lines.append(asp.fact("indoor", pid))
        for q in sorted(place.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_tag", qid, "click"))
        lines.append(asp.fact("quest_tag", qid, "misunderstanding"))
        lines.append(asp.fact("quest_tag", qid, "bad_ending"))
        lines.append(asp.fact("click_target", qid, q.click_target))
    for prize_id in PRIZES:
        lines.append(asp.fact("prize", prize_id))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Quest, Prize) :- place(Place), quest(Quest), prize(Prize), affords(Place, Quest).
"""

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


def world_story_qa(sample: StorySample) -> list[QAItem]:
    return sample.story_qa


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t in asp_valid_combos():
            print(t)
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
