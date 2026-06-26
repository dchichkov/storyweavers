#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/rabbi_mystery_to_solve_quest_flashback_bedtime.py
=================================================================================================

A small bedtime-story world about a rabbi, a mystery to solve, a quest, and a
gentle flashback that helps the ending feel earned.

Premise:
- A child or young helper is worried about a small mystery.
- A rabbi notices the worry and sends them on a quiet quest to gather clues.
- The search includes a flashback to remember something important from earlier.
- The mystery is solved with a calm, child-facing bedtime ending image.

The world models physical meters and emotional memes, and the prose is driven by
those state changes rather than by a frozen template.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"tired": 0.0, "safe": 0.0, "found": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "hope": 0.0, "calm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "rabbi"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the quiet little synagogue"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    missing: str
    solved_by: str
    place: str
    flashback_trigger: str
    keyword: str = "mystery"


@dataclass
class Quest:
    id: str
    search: str
    step: str
    return_step: str
    item: str
    benefit: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.flashback_seen: bool = False
        self.quest_done: bool = False

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
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.flashback_seen = self.flashback_seen
        clone.quest_done = self.quest_done
        return clone


def _narrate_flashback(world: World) -> None:
    if world.flashback_seen:
        return
    world.flashback_seen = True
    seeker = world.facts["seeker"]
    rabbi = world.facts["rabbi"]
    mystery = world.facts["mystery"]
    world.say(
        f"As {seeker.id} walked, a warm flashback fluttered by like a little candle-light memory. "
        f"Earlier that evening, {rabbi.id} had noticed {seeker.pronoun('possessive')} face and said, "
        f"'{mystery.flashback_trigger}.'"
    )
    seeker.memes["calm"] += 1
    seeker.memes["hope"] += 1


def _solve(world: World) -> None:
    if world.quest_done:
        return
    seeker = world.facts["seeker"]
    rabbi = world.facts["rabbi"]
    mystery = world.facts["mystery"]
    quest = world.facts["quest"]
    if seeker.meters["found"] < THRESHOLD:
        return
    world.quest_done = True
    seeker.memes["worry"] = 0.0
    seeker.memes["calm"] += 1
    seeker.memes["hope"] += 1
    world.say(
        f"Then {seeker.id} found {quest.item}, right where the clue had promised."
    )
    world.say(
        f"It was {mystery.solved_by}, and the missing thing was no longer missing at all."
    )
    world.say(
        f"{rabbi.id} smiled softly and tucked the clue away like a story that had done its job. "
        f"The mystery was solved, and the room felt sleepy and safe again."
    )


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        before_flash = world.flashback_seen
        before_quest = world.quest_done
        _narrate_flashback(world)
        _solve(world)
        if world.flashback_seen != before_flash or world.quest_done != before_quest:
            changed = True


def story_setting_detail(setting: Setting) -> str:
    if setting.indoor:
        return "The lamps glowed low, and the room was quiet enough to hear a page turn."
    return "The evening air was gentle, and the path looked soft under the stars."


def introduce(world: World, seeker: Entity, rabbi: Entity, mystery: Mystery) -> None:
    world.say(
        f"At bedtime, {seeker.id} felt a tiny worry in {seeker.pronoun('possessive')} chest."
    )
    world.say(
        f"{rabbi.id} was a kind {rabbi.type} with a calm voice and a habit of noticing little mysteries."
    )
    world.say(
        f"Something had gone missing: {mystery.missing}. The clue said it might be near {mystery.place}."
    )


def begin_quest(world: World, seeker: Entity, rabbi: Entity, quest: Quest) -> None:
    seeker.memes["curiosity"] += 1
    seeker.memes["worry"] += 1
    world.say(
        f"{rabbi.id} gave {seeker.id} a gentle quest: {quest.search}."
    )
    world.say(
        f"{seeker.id} took a slow breath and went along {quest.step}, trying to be brave."
    )


def follow_clue(world: World, seeker: Entity, mystery: Mystery, quest: Quest) -> None:
    seeker.meters["tired"] += 1
    seeker.memes["hope"] += 1
    world.say(
        f"The clue led {seeker.id} past the softly lit hall and toward {mystery.place}."
    )
    world.say(
        f"Every step felt like part of the quest, and the little clue stayed tucked safely in {seeker.pronoun('possessive')} mind."
    )
    propagate(world)


def find_clue(world: World, seeker: Entity, quest: Quest) -> None:
    seeker.meters["found"] += 1
    world.say(
        f"At last, {seeker.id} noticed {quest.item} resting exactly where {quest.return_step}."
    )
    world.say(
        f"That was the answer to the mystery, and {seeker.id} knew it was time to go back and tell {world.facts['rabbi'].id}."
    )
    propagate(world)


def close_bedtime(world: World, seeker: Entity, rabbi: Entity, mystery: Mystery) -> None:
    world.say(
        f"Back inside, {rabbi.id} wrapped the happy ending around the room like a blanket."
    )
    world.say(
        f"{seeker.id} smiled, no longer worried, because the little mystery was solved before sleep."
    )
    world.say(
        f"And under the quiet light, the last thing {seeker.id} saw was {mystery.missing} back where it belonged, safe and found."
    )


def tell(setting: Setting, mystery: Mystery, quest: Quest, seeker_name: str, seeker_type: str,
         rabbi_name: str = "Rabbi Miriam", rabbi_type: str = "rabbi") -> World:
    world = World(setting)
    seeker = world.add(Entity(
        id=seeker_name,
        kind="character",
        type=seeker_type,
        traits=["little", "sleepy", "curious"],
    ))
    rabbi = world.add(Entity(
        id=rabbi_name,
        kind="character",
        type=rabbi_type,
        label="rabbi",
        traits=["kind", "calm"],
    ))

    world.facts.update(seeker=seeker, rabbi=rabbi, mystery=mystery, quest=quest)

    world.say(story_setting_detail(setting))
    introduce(world, seeker, rabbi, mystery)
    world.para()
    begin_quest(world, seeker, rabbi, quest)
    world.para()
    follow_clue(world, seeker, mystery, quest)
    find_clue(world, seeker, quest)
    world.para()
    close_bedtime(world, seeker, rabbi, mystery)
    return world


SETTINGS = {
    "synagogue": Setting(place="the quiet little synagogue", indoor=True, affords={"search"}),
    "study": Setting(place="the warm study room", indoor=True, affords={"search"}),
    "garden": Setting(place="the moonlit garden", indoor=False, affords={"search"}),
}

MYSTERIES = {
    "missing_candle": Mystery(
        id="missing_candle",
        clue="a tiny drop of wax on the windowsill",
        missing="a silver candle holder",
        solved_by="it had been moved to the shelf near the prayer books",
        place="the shelf near the prayer books",
        flashback_trigger="Think of where careful hands would put something shiny so it stays safe.",
        keyword="mystery",
    ),
    "missing_key": Mystery(
        id="missing_key",
        clue="a little ring-shaped shadow by the door",
        missing="the little brass key",
        solved_by="it had slipped into the basket with the scarves",
        place="the basket with the scarves",
        flashback_trigger="Remember the last person who wanted the key to stay close and warm.",
        keyword="quest",
    ),
    "missing_book": Mystery(
        id="missing_book",
        clue="a bent bookmark on the table",
        missing="the bedtime storybook",
        solved_by="it had been placed beside the pillow for tonight's reading",
        place="beside the pillow",
        flashback_trigger="Think back to the last calm moment before lights-out.",
        keyword="flashback",
    ),
}

QUESTS = {
    "search_shelves": Quest(
        id="search_shelves",
        search="follow the clue and search the shelves until the missing thing is found",
        step="the narrow hallway",
        return_step="the shelf near the prayer books",
        item="the silver candle holder",
        benefit="the room could shine softly again",
        tags={"mystery", "search"},
    ),
    "check_basket": Quest(
        id="check_basket",
        search="take a careful quest to look through the basket and see what was tucked inside",
        step="the side corridor",
        return_step="the basket with the scarves",
        item="the little brass key",
        benefit="the door could be opened with a calm hand",
        tags={"quest", "search"},
    ),
    "find_storybook": Quest(
        id="find_storybook",
        search="go on a bedtime quest to look beside the pillow for the missing storybook",
        step="the lamp-lit path",
        return_step="beside the pillow",
        item="the bedtime storybook",
        benefit="the tale could be read before sleep",
        tags={"flashback", "bedtime"},
    ),
}

NAMES = ["Ari", "Noa", "Mina", "Seth", "Leah", "Ezra", "Talia", "Ben", "Ira", "Maya"]
TYPES = ["girl", "boy"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    quest: str
    name: str
    type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about a rabbi, a mystery, and a gentle quest.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--type", choices=TYPES)
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
    place = args.place or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    quest = args.quest or rng.choice(list(QUESTS))
    if args.place and not SETTINGS[args.place].affords:
        raise StoryError("The chosen place does not support a quiet quest.")
    if args.mystery and args.quest:
        if args.mystery == "missing_book" and args.quest == "search_shelves":
            raise StoryError("That quest does not fit the bedtime book mystery.")
    name = args.name or rng.choice(NAMES)
    type_ = args.type or rng.choice(TYPES)
    return StoryParams(place=place, mystery=mystery, quest=quest, name=name, type=type_)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    mystery = f["mystery"]
    quest = f["quest"]
    rabbi = f["rabbi"]
    return [
        f'Write a bedtime story about a rabbi, a mystery to solve, and a quiet quest in {world.setting.place}.',
        f"Tell a gentle story where {rabbi.id} sends {seeker.id} on a quest to solve a mystery about {mystery.missing}.",
        f'Write a calm story with a flashback that helps {seeker.id} finish a quest and find {mystery.missing}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker = f["seeker"]
    rabbi = f["rabbi"]
    mystery = f["mystery"]
    quest = f["quest"]
    return [
        QAItem(
            question=f"Who helped {seeker.id} solve the mystery in the story?",
            answer=f"{rabbi.id} helped {seeker.id} with a gentle quest and a calm voice.",
        ),
        QAItem(
            question=f"What was the mystery about?",
            answer=f"The mystery was about {mystery.missing}, which had gone missing before bedtime.",
        ),
        QAItem(
            question=f"What did the flashback remind {seeker.id} to think about?",
            answer=f"The flashback reminded {seeker.id} to think about the safest place for something shiny or important.",
        ),
        QAItem(
            question=f"How did {seeker.id} solve the quest?",
            answer=f"{seeker.id} followed the clue, searched carefully, and found {quest.item} exactly where it had been tucked away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a small search or mission to find something, learn something, or help someone.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="Why are bedtime stories often calm?",
            answer="Bedtime stories are often calm so children can feel safe, relaxed, and ready to sleep.",
        ),
    ]


ASP_RULES = r"""
mystery_story(P,M,Q) :- place(P), mystery(M), quest(Q), fits(M,Q).
fits(missing_candle,search_shelves).
fits(missing_key,check_basket).
fits(missing_book,find_storybook).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery_story/3."))
    return sorted(set(asp.atoms(model, "mystery_story")))


def asp_verify() -> int:
    py = {(p, m, q) for p in SETTINGS for m in MYSTERIES for q in QUESTS if
          (m == "missing_candle" and q == "search_shelves") or
          (m == "missing_key" and q == "check_basket") or
          (m == "missing_book" and q == "find_storybook")}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:12} ({e.type:8}) meters={e.meters} memes={e.memes}")
    lines.append(f"  flashback_seen={world.flashback_seen}")
    lines.append(f"  quest_done={world.quest_done}")
    return "\n".join(lines)


def explain_rejection(mystery: Mystery, quest: Quest) -> str:
    return f"(No story: that quest does not fit the {mystery.id} mystery.)"


def resolve_story_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str]:
    if args.mystery and args.quest:
        if args.mystery == "missing_book" and args.quest != "find_storybook":
            raise StoryError(explain_rejection(MYSTERIES[args.mystery], QUESTS[args.quest]))
        if args.mystery == "missing_key" and args.quest != "check_basket":
            raise StoryError(explain_rejection(MYSTERIES[args.mystery], QUESTS[args.quest]))
        if args.mystery == "missing_candle" and args.quest != "search_shelves":
            raise StoryError(explain_rejection(MYSTERIES[args.mystery], QUESTS[args.quest]))
    combos = [
        ("synagogue", "missing_candle", "search_shelves"),
        ("study", "missing_key", "check_basket"),
        ("garden", "missing_book", "find_storybook"),
    ]
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.quest is None or c[2] == args.quest)]
    if not combos:
        raise StoryError("No valid story combination matches the given options.")
    return rng.choice(combos)


CURATED = [
    StoryParams(place="synagogue", mystery="missing_candle", quest="search_shelves", name="Ari", type="boy"),
    StoryParams(place="study", mystery="missing_key", quest="check_basket", name="Mina", type="girl"),
    StoryParams(place="garden", mystery="missing_book", quest="find_storybook", name="Leah", type="girl"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        MYSTERIES[params.mystery],
        QUESTS[params.quest],
        params.name,
        params.type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        print(asp_program("#show mystery_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery_story/3."))
        atoms = sorted(set(asp.atoms(model, "mystery_story")))
        print(f"{len(atoms)} mystery-story combos:")
        for a in atoms:
            print(" ", a)
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
            rng = random.Random(seed)
            try:
                place, mystery, quest = resolve_story_combo(args, rng)
                name = args.name or rng.choice(NAMES)
                type_ = args.type or rng.choice(TYPES)
                params = StoryParams(place=place, mystery=mystery, quest=quest, name=name, type=type_, seed=seed)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.mystery} at {p.place} (quest: {p.quest})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
