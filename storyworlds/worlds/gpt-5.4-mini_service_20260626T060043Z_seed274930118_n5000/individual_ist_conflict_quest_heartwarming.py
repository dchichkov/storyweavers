#!/usr/bin/env python3
"""
A small heartwarming story world about an individualist child, a quest, and a
gentle conflict about doing things alone versus accepting help.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Object:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    can_quest: set[str] = field(default_factory=set)
    mood: str = ""


@dataclass
class Quest:
    id: str
    goal: str
    verb: str
    path: str
    reward: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    quest: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


PLACES = {
    "garden": Place(id="garden", label="the garden", can_quest={"find_lantern", "collect_apples"}, mood="soft and bright"),
    "attic": Place(id="attic", label="the attic", can_quest={"find_lantern", "find_button"}, mood="dusty and quiet"),
    "beach": Place(id="beach", label="the beach", can_quest={"collect_shell", "find_bottle"}, mood="windy and warm"),
}

QUESTS = {
    "find_lantern": Quest(
        id="find_lantern",
        goal="find the little lantern",
        verb="search for the lantern",
        path="follow the hallway to the closet and then look behind the old boxes",
        reward="a warm little glow",
        risk="the room stayed dark and lonely",
        keyword="lantern",
        tags={"light", "find", "dark"},
    ),
    "collect_apples": Quest(
        id="collect_apples",
        goal="pick three apples",
        verb="gather the apples",
        path="walk to the tree and fill a small basket",
        reward="a sweet snack for later",
        risk="the basket might stay empty",
        keyword="apple",
        tags={"fruit", "pick", "share"},
    ),
    "collect_shell": Quest(
        id="collect_shell",
        goal="collect one shiny shell",
        verb="search for a shell",
        path="scan the tide line and kneel near the foam",
        reward="a pretty treasure from the shore",
        risk="the child might go home with nothing",
        keyword="shell",
        tags={"beach", "treasure", "find"},
    ),
    "find_button": Quest(
        id="find_button",
        goal="find the missing button",
        verb="look for the button",
        path="sift through the sewing tin and check under the cloth",
        reward="a repaired favorite shirt",
        risk="the shirt would stay unfinished",
        keyword="button",
        tags={"fix", "small", "help"},
    ),
}

HEROES = ["Maya", "Nia", "Theo", "Arlo", "Lena", "Iris", "Finn", "Milo"]
HELPERS = ["Mom", "Dad", "Aunt Jo", "Grandpa", "Big Sister", "Neighbor Ben"]
TRAITS = ["independent", "quiet", "stubborn", "careful", "determined", "bright"]


class World:
    def __init__(self, place: Place, quest: Quest) -> None:
        self.place = place
        self.quest = quest
        self.entities: dict[str, object] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.trace: list[str] = []

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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


def _r_conflict(world: World) -> list[str]:
    hero: Character = world.get("hero")
    if hero.memes.get("wants_alone", 0) >= 1 and hero.memes.get("help_offered", 0) >= 1:
        if "conflict" in world.fired:
            return []
        world.fired.add("conflict")
        hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
        return ["__conflict__"]
    return []


def _r_soften(world: World) -> list[str]:
    hero: Character = world.get("hero")
    helper: Character = world.get("helper")
    if hero.memes.get("conflict", 0) >= 1 and hero.memes.get("help_accepted", 0) >= 1:
        if "soften" in world.fired:
            return []
        world.fired.add("soften")
        hero.memes["conflict"] = 0
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        helper.memes["joy"] = helper.memes.get("joy", 0) + 1
        return ["__soften__"]
    return []


def _r_reward(world: World) -> list[str]:
    if "reward" in world.fired:
        return []
    hero: Character = world.get("hero")
    if hero.meters.get("quest_done", 0) >= 1:
        world.fired.add("reward")
        return ["__reward__"]
    return []


RULES = [_r_conflict, _r_soften, _r_reward]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            got = rule(world)
            if got:
                changed = True
                out.extend(got)
    if narrate:
        for item in out:
            if item not in {"__conflict__", "__soften__", "__reward__"}:
                world.say(item)
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming individualist quest story world.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def quest_supported(place: Place, quest: Quest) -> bool:
    return quest.id in place.can_quest


def valid_combos() -> list[tuple[str, str]]:
    return [(p.id, q.id) for p in PLACES.values() for q in QUESTS.values() if quest_supported(p, q)]


def explain_rejection(place: Place, quest: Quest) -> str:
    return f"(No story: {place.label} does not fit the quest to {quest.goal}. Pick a place that can honestly support that search.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.quest:
        if not quest_supported(PLACES[args.place], QUESTS[args.quest]):
            raise StoryError(explain_rejection(PLACES[args.place], QUESTS[args.quest]))

    combos = [
        (p, q)
        for p, q in valid_combos()
        if (args.place is None or p == args.place) and (args.quest is None or q == args.quest)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, quest = rng.choice(sorted(combos))
    name = args.name or rng.choice(HEROES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, quest=quest, hero_name=name, helper_name=helper)


def start_story(world: World, hero: Character, helper: Character) -> None:
    world.say(
        f"{hero.id} was the kind of child who liked doing things on {hero.pronoun('possessive')} own. "
        f"{hero.pronoun('subject').capitalize()} felt proud when {hero.pronoun('subject')} could solve a problem all by {hero.pronoun('object')}."
    )
    world.say(
        f"One afternoon, {hero.id} had a little quest in {world.place.label}: {world.quest.goal}."
    )


def conflict_scene(world: World, hero: Character, helper: Character) -> None:
    hero.memes["wants_alone"] = hero.memes.get("wants_alone", 0) + 1
    world.say(
        f"{hero.id} wanted to {world.quest.verb} alone, because {hero.pronoun('subject')} liked being independent."
    )
    helper.memes["help_offered"] = helper.memes.get("help_offered", 0) + 1
    world.say(
        f"But {helper.id} noticed the worry on {hero.pronoun('possessive')} face and said, "
        f'"I can help if you want."'
    )
    propagate(world, narrate=False)
    if hero.memes.get("conflict", 0) >= 1:
        world.say(
            f"{hero.id} frowned a little. {hero.pronoun('subject').capitalize()} wanted to prove {hero.pronoun('subject')} could do it alone, but the quest felt bigger in the dark."
        )


def turn_scene(world: World, hero: Character, helper: Character) -> None:
    hero.memes["help_accepted"] = hero.memes.get("help_accepted", 0) + 1
    world.say(
        f"Then {hero.id} took a slow breath and said, \"Okay. You can help me look.\""
    )
    propagate(world, narrate=False)
    world.say(
        f"Together they followed {world.quest.path}, and each small step made the quest feel less scary."
    )


def resolution_scene(world: World, hero: Character, helper: Character) -> None:
    hero.meters["quest_done"] = 1
    world.say(
        f"At last, {hero.id} found {world.quest.reward}."
    )
    world.say(
        f"{helper.id} smiled and let {hero.id} keep the final find, because this was still {hero.pronoun('possessive')} quest."
    )
    world.say(
        f"{hero.id} had not stopped being independent at all; {hero.pronoun('subject')} had simply learned that accepting a hand could make the adventure warmer."
    )


def tell_story(params: StoryParams) -> World:
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    world = World(place, quest)
    hero = world.add(Character(id=params.hero_name, type="child", label=params.hero_name, traits=["individualist", "determined"]))
    helper = world.add(Character(id=params.helper_name, type="adult", label=params.helper_name, traits=["kind"]))
    world.facts.update(hero=hero, helper=helper, place=place, quest=quest)

    start_story(world, hero, helper)
    world.para()
    conflict_scene(world, hero, helper)
    world.para()
    turn_scene(world, hero, helper)
    resolution_scene(world, hero, helper)
    world.facts["resolved"] = True
    world.facts["conflicted"] = hero.memes.get("conflict", 0) >= 1
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Character = f["hero"]
    helper: Character = f["helper"]
    quest: Quest = f["quest"]
    return [
        f'Write a heartwarming story about an individualist child named {hero.id} who wants to {quest.verb} by {hero.pronoun("object")}self.',
        f"Tell a gentle conflict-and-quest story where {hero.id} is proud to work alone, but {helper.id} offers help during {quest.goal}.",
        f'Write a short child-friendly story that includes the word "{quest.keyword}" and ends with a warmer feeling than it began.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Character = f["hero"]
    helper: Character = f["helper"]
    quest: Quest = f["quest"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Why was {hero.id} in {place.label}?",
            answer=f"{hero.id} was there to {quest.goal}. It was a small quest, and {hero.id} wanted to manage it with care.",
        ),
        QAItem(
            question=f"What made the story feel like a conflict?",
            answer=f"The conflict came from {hero.id} wanting to do the quest alone while {helper.id} offered help. {hero.id} cared about independence, so accepting help was not easy at first.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} finishing the quest and feeling glad that help had made the journey gentler. {helper.id} still left {hero.id} with the final reward, so {hero.id}'s independence stayed important too.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    q = world.facts["quest"]
    out = [
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal or search that someone chooses to go on, usually because they want to find, fix, or bring back something important.",
        ),
        QAItem(
            question="What does independent mean?",
            answer="Independent means being able to do things on your own, without needing someone else to do every part for you.",
        ),
    ]
    if "light" in q.tags:
        out.append(QAItem(question="What does a lantern do?", answer="A lantern gives off light, so it helps people see when it is dark."))
    if "fix" in q.tags:
        out.append(QAItem(question="Why is a missing button important?", answer="A missing button can keep a shirt from being finished, so finding it helps repair the clothes."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.extend(world.trace)
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
supported(P,Q) :- place(P), quest(Q), can_quest(P,Q).

valid(P,Q) :- supported(P,Q).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for q in sorted(p.can_quest):
            lines.append(asp.fact("can_quest", pid, q))
    for qid in QUESTS:
        lines.append(asp.fact("quest_item", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
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
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="garden", quest="collect_apples", hero_name="Maya", helper_name="Mom"),
    StoryParams(place="attic", quest="find_lantern", hero_name="Theo", helper_name="Dad"),
    StoryParams(place="beach", quest="collect_shell", hero_name="Lena", helper_name="Aunt Jo"),
    StoryParams(place="attic", quest="find_button", hero_name="Iris", helper_name="Grandpa"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for p, q in asp_valid_combos():
            print(p, q)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(100, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
