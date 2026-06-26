#!/usr/bin/env python3
"""
storyworlds/worlds/feather_boozer_vegetable_garden_quest_detective_story.py
============================================================================

A small detective-story world set in a vegetable garden, built from the seed
words "feather" and "boozer" with a quest-shaped mystery.

The premise:
- A young detective is asked to find a missing feather in a vegetable garden.
- Clues point toward Boozer, a thirsty little garden goose who likes shiny things
  and wanders among the lettuce rows.
- The detective follows physical evidence and social tension through a short,
  state-driven mystery, then resolves it by understanding Boozer's motive.

This world keeps a classical TinyStories-style arc:
setup -> clue trail -> suspicion -> reveal -> resolution.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "detective"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the vegetable garden"
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    kind: str
    text: str
    value: str


@dataclass
class StoryParams:
    place: str = "garden"
    quest: str = "feather"
    suspect: str = "boozer"
    detective_name: str = "Mina"
    detective_type: str = "girl"
    helper_name: str = "Tom"
    helper_type: str = "boy"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.clues_found: list[str] = []
        self.suspect_points: dict[str, int] = {"boozer": 0, "wind": 0}
        self.weather: str = "still"
        self.trace_notes: list[str] = []

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


QUESTS = {
    "feather": Clue(
        id="feather",
        kind="object",
        text="a pale feather",
        value="feather",
    )
}

LOCATIONS = {
    "garden": Setting(place="the vegetable garden", affords={"search"}),
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Lena", "Ruby"]
BOY_NAMES = ["Tom", "Ezra", "Finn", "Owen", "Jude"]


def build_storyline() -> list[str]:
    return [
        "setup",
        "clues",
        "suspicion",
        "reveal",
        "resolution",
    ]


def is_reasonable(params: StoryParams) -> bool:
    return params.place == "garden" and params.quest == "feather" and params.suspect == "boozer"


def reasonableness_reason() -> str:
    return "(No story: this world only supports a feather mystery in the vegetable garden with Boozer as the gentle suspect.)"


def introduce(world: World, detective: Entity, helper: Entity, quest: Clue) -> None:
    world.say(
        f"{detective.id} was a small detective who loved tricky questions and tidy clues. "
        f"{helper.id} helped carry a notebook, because every quest needed careful eyes."
    )
    world.say(
        f"That morning, someone in the vegetable garden noticed {quest.text} missing from the bean trellis."
    )
    world.facts["quest"] = quest
    world.facts["detective"] = detective
    world.facts["helper"] = helper


def search_rows(world: World, detective: Entity, quest: Clue) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    world.say(
        f"{detective.id} searched between the carrots and lettuce rows, looking for {quest.value} tracks."
    )
    world.clues_found.append("soft_rustle")
    world.say("A soft rustle in the pea vines made the case feel alive.")


def find_clue(world: World) -> None:
    feather = world.add(Entity(id="feather", type="thing", label="feather"))
    feather.meters["found"] = 1
    world.clues_found.append("feather")
    world.say(
        "Under a cabbage leaf, the detective found a pale feather, light as thistledown."
    )
    world.suspect_points["boozer"] += 1
    world.trace_notes.append("feather found under cabbage")


def suspect_boozer(world: World, detective: Entity) -> None:
    boozer = world.add(Entity(id="boozer", kind="character", type="goose", label="Boozer"))
    boozer.memes["nervous"] = 1
    boozer.meters["mud"] = 1
    world.say(
        f"The muddy tracks pointed to Boozer, the garden goose, who had been waddling near the beans."
    )
    detective.memes["doubt"] = detective.memes.get("doubt", 0) + 1
    world.say(
        f"{detective.id} narrowed {detective.pronoun('possessive')} eyes. "
        f'"Boozer, did you take the feather?"'
    )
    world.suspect_points["boozer"] += 1
    world.trace_notes.append("boozer suspected")


def reveal_motive(world: World) -> None:
    boozer = world.get("boozer")
    boozer.memes["hungry"] = 1
    boozer.memes["hope"] = 1
    world.say(
        "Boozer hung his head and blinked. The goose had not stolen the feather to be mean."
    )
    world.say(
        "He had carried it to line a nest tucked behind the tomato vines, where a shy egg stayed warm."
    )
    world.suspect_points["boozer"] += 1
    world.trace_notes.append("nest reveal")


def resolution(world: World, detective: Entity, helper: Entity) -> None:
    detective.memes["relief"] = detective.memes.get("relief", 0) + 1
    detective.memes["kindness"] = detective.memes.get("kindness", 0) + 1
    world.say(
        f"{detective.id} smiled and gave Boozer the feather back. "
        "The little detective even helped gather a few soft weeds for the nest."
    )
    world.say(
        f"By sunset, {helper.id} was laughing, Boozer was calm, and the vegetable garden felt peaceful again."
    )
    world.trace_notes.append("resolution")


def tell(params: StoryParams) -> World:
    world = World(LOCATIONS[params.place])
    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        label="detective",
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        label="helper",
    ))
    quest = QUESTS[params.quest]

    world.say("The vegetable garden was full of green rows, damp soil, and one missing feather.")
    introduce(world, detective, helper, quest)

    world.para()
    search_rows(world, detective, quest)
    find_clue(world)

    world.para()
    suspect_boozer(world, detective)
    reveal_motive(world)

    world.para()
    resolution(world, detective, helper)

    world.facts.update(
        detective=detective,
        helper=helper,
        quest=quest,
        suspect=params.suspect,
        place=params.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    quest = f["quest"]
    return [
        f'Write a short detective story for a young child set in a vegetable garden where a {quest.value} goes missing.',
        f"Tell a gentle mystery about {detective.id} and {helper.id} looking for a {quest.value} among the garden beds.",
        "Make the story feel like a small quest, with clues, a suspicious goose, and a kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    quest = f["quest"]
    return [
        QAItem(
            question=f"What was missing from the vegetable garden?",
            answer=f"A {quest.value} was missing from the garden, and that started the little detective quest.",
        ),
        QAItem(
            question=f"Who searched the garden for clues?",
            answer=f"{detective.id} searched the vegetable garden while {helper.id} helped carry a notebook.",
        ),
        QAItem(
            question=f"Why did Boozer seem suspicious at first?",
            answer="Boozer had muddy tracks and had been wandering near the bean rows, so the detective thought he might know something.",
        ),
        QAItem(
            question="What was the feather really being used for?",
            answer="Boozer had taken the feather to line a nest behind the tomato vines, where a shy egg stayed warm.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{detective.id} gave the feather back, helped gather soft weeds, and the vegetable garden became peaceful again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vegetable garden?",
            answer="A vegetable garden is a place where people grow plants like beans, carrots, lettuce, and tomatoes.",
        ),
        QAItem(
            question="What is a feather?",
            answer="A feather is a soft, light part of a bird's body that helps cover it and can float on the wind.",
        ),
        QAItem(
            question="Why might a goose use grass or weeds in a nest?",
            answer="A goose may use soft plant material in a nest to make it warm and comfy for eggs.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    lines.append(f"  clues_found={world.clues_found}")
    lines.append(f"  suspect_points={world.suspect_points}")
    lines.append(f"  trace_notes={world.trace_notes}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_missing(quest) :- quest_item(quest).
clue_points_to_boozer(feather) :- found(feather), muddy(boozer).
resolved(feather) :- clue_points_to_boozer(feather), nest(boozer).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    lines.append(asp.fact("quest_item", "feather"))
    lines.append(asp.fact("found", "feather"))
    lines.append(asp.fact("muddy", "boozer"))
    lines.append(asp.fact("nest", "boozer"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show resolved/1."))
    resolved = set(asp.atoms(model, "resolved"))
    if resolved == {("feather",)}:
        print("OK: ASP verifies the feather mystery.")
        return 0
    print("MISMATCH: ASP did not resolve the feather mystery as expected.")
    return 1


@dataclass
class Registry:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective-story world in a vegetable garden.")
    ap.add_argument("--place", choices=["garden"])
    ap.add_argument("--quest", choices=["feather"])
    ap.add_argument("--suspect", choices=["boozer"])
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
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
    if args.place and args.place != "garden":
        raise StoryError("(No story: this mystery only happens in the vegetable garden.)")
    if args.quest and args.quest != "feather":
        raise StoryError("(No story: this world only supports the feather quest.)")
    if args.suspect and args.suspect != "boozer":
        raise StoryError("(No story: Boozer is the only suspect in this world.)")

    gender = args.gender or rng.choice(["girl", "boy"])
    detective_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(BOY_NAMES if gender == "girl" else GIRL_NAMES)
    return StoryParams(
        place="garden",
        quest="feather",
        suspect="boozer",
        detective_name=detective_name,
        detective_type=gender,
        helper_name=helper_name,
        helper_type="boy" if gender == "girl" else "girl",
    )


def generate(params: StoryParams) -> StorySample:
    if not is_reasonable(params):
        raise StoryError(reasonableness_reason())
    world = tell(params)
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
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print(asp.atoms(model, "resolved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams()
        params.seed = base_seed
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
