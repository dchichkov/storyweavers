#!/usr/bin/env python3
"""
evaluate_moral_value_quest_sharing_fable.py
===========================================

A tiny fable-style storyworld about a friend evaluating a quest, deciding what
is fair, and learning the value of sharing.

Premise:
- A small hero wants to complete a quest.
- The quest prize is valuable enough that keeping it all would feel selfish.
- The story turns when the hero evaluates the moral choice and shares.

The world is intentionally small and constraint-checked: if the requested
quest/item combination is not a reasonable moral conflict, it raises StoryError.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "hen", "rabbit"}
        male = {"boy", "father", "dad", "man", "brother", "fox", "wolf", "crow"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def item_pronoun(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    verb: str
    reward: str
    risk: str
    moral_test: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    label: str
    phrase: str
    type: str
    plural: bool = False
    can_share: bool = True
    valuable: bool = True


@dataclass
class Helper:
    id: str
    label: str
    role: str
    offers: str
    fairness: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registry content
# ---------------------------------------------------------------------------

SETTINGS = {
    "woods": Setting(place="the woods", outdoors=True, affords={"berries", "lantern"}),
    "meadow": Setting(place="the meadow", outdoors=True, affords={"flowers", "berries"}),
    "river": Setting(place="the riverbank", outdoors=True, affords={"stones", "berries"}),
}

QUESTS = {
    "berries": Quest(
        id="berries",
        goal="gather berries",
        verb="gather berries",
        reward="a basket of berries",
        risk="alone, someone might keep the sweetest berries",
        moral_test="share the basket",
        keyword="berries",
        tags={"food", "share"},
    ),
    "flowers": Quest(
        id="flowers",
        goal="pick flowers",
        verb="pick flowers",
        reward="a bright flower crown",
        risk="one friend could take all the blossoms",
        moral_test="share the flowers",
        keyword="flowers",
        tags={"beauty", "share"},
    ),
    "stones": Quest(
        id="stones",
        goal="collect smooth stones",
        verb="collect smooth stones",
        reward="a pocket of shining stones",
        risk="a greedy friend could hide the prettiest stones",
        moral_test="share the stones",
        keyword="stones",
        tags={"treasure", "share"},
    ),
}

TREASURES = {
    "basket": Treasure(label="basket", phrase="a little basket", type="basket", plural=False),
    "crown": Treasure(label="crown", phrase="a flower crown", type="crown", plural=False),
    "pocket": Treasure(label="pocket of stones", phrase="a pocketful of smooth stones", type="stones", plural=True),
}

HELPERS = {
    "hare": Helper(
        id="hare",
        label="the hare",
        role="friend",
        offers="carry part of the load",
        fairness="hares like to help when a bundle is too heavy",
    ),
    "sparrow": Helper(
        id="sparrow",
        label="the sparrow",
        role="friend",
        offers="count each share carefully",
        fairness="sparrows notice small things and fair turns",
    ),
    "mouse": Helper(
        id="mouse",
        label="the mouse",
        role="friend",
        offers="divide the prize into equal piles",
        fairness="mice are good at making equal shares",
    ),
}

GIRL_NAMES = ["Nina", "Mina", "Lila", "Mara", "Tessa", "Clara"]
BOY_NAMES = ["Owen", "Pip", "Toby", "Hugo", "Ezra", "Bram"]
TRAITS = ["kind", "brave", "thoughtful", "curious", "gentle"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    quest: str
    treasure: str
    hero_name: str
    hero_type: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------

def quest_is_reasonable(quest: Quest, treasure: Treasure) -> bool:
    if not treasure.can_share:
        return False
    # The story needs a real moral decision: a quest reward that can be split.
    return "share" in quest.tags and treasure.valuable


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for q in QUESTS:
            for t in TREASURES:
                if quest_is_reasonable(QUESTS[q], TREASURES[t]):
                    out.append((s, q, t))
    return out


def explain_rejection(quest: Quest, treasure: Treasure) -> str:
    return (
        f"(No story: the quest '{quest.goal}' and the treasure '{treasure.label}' "
        f"do not make a fair-sharing moral choice in this fable. Pick a shareable prize.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def intro(world: World, hero: Entity, helper: Helper, quest: Quest, treasure: Treasure) -> None:
    world.say(
        f"In {world.setting.place}, there lived a little {hero.traits[0]} {hero.type} named {hero.id}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved a good quest, especially one that led to "
        f"{quest.reward}."
    )
    world.say(
        f"One day, {hero.id} met {helper.label}, who said {helper.offers}."
    )
    world.say(
        f"The prize was {treasure.phrase}, and {hero.id} wanted it very much."
    )


def evaluate_choice(world: World, hero: Entity, quest: Quest, treasure: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    hero.memes["care"] = hero.memes.get("care", 0) + 1
    world.say(
        f"But {hero.id} paused and tried to evaluate what was right."
    )
    world.say(
        f"{hero.pronoun().capitalize()} thought, 'If I keep it all, my friend may go home with empty paws.'"
    )
    world.say(
        f"So {hero.id} judged the moral value of the quest and saw that {quest.moral_test} would be the kinder path."
    )


def do_quest(world: World, hero: Entity, quest: Quest, treasure: Entity) -> None:
    treasure.carried_by = hero.id
    hero.meters["load"] = hero.meters.get("load", 0) + 1
    world.say(
        f"{hero.id} and {world.facts['helper'].label} went to {world.setting.place} to {quest.verb}."
    )
    world.say(
        f"Together they found {treasure.phrase}, shining under the leaves."
    )


def split_sharing(world: World, hero: Entity, helper: Helper, treasure: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["generosity"] = hero.memes.get("generosity", 0) + 1
    world.say(
        f"Then {hero.id} smiled and said, 'Let's share it fairly.'"
    )
    world.say(
        f"{hero.id} gave some to {helper.label}, and {helper.label} helped carry the rest."
    )
    world.say(
        f"Soon both friends had enough, and neither one felt left out."
    )


def ending(world: World, hero: Entity, helper: Helper, treasure: Treasure, quest: Quest) -> None:
    world.say(
        f"By the end, {hero.id} learned that a good quest is not only about finding treasure."
    )
    world.say(
        f"It is also about choosing kindness, sharing well, and coming home with a lighter heart."
    )


# ---------------------------------------------------------------------------
# Build a world and tell the story
# ---------------------------------------------------------------------------

def tell(setting: Setting, quest: Quest, treasure_cfg: Treasure, hero_name: str,
         hero_type: str, helper: Helper, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=[trait, "small"],
    ))
    treasure = world.add(Entity(
        id="treasure",
        type=treasure_cfg.type,
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        plural=treasure_cfg.plural,
    ))

    world.facts["helper"] = helper
    world.facts["quest"] = quest
    world.facts["treasure"] = treasure
    world.facts["hero"] = hero

    intro(world, hero, helper, quest, treasure)
    world.para()
    do_quest(world, hero, quest, treasure)
    evaluate_choice(world, hero, quest, treasure)
    world.para()
    split_sharing(world, hero, helper, treasure)
    ending(world, hero, helper, treasure, quest)

    world.facts["shared"] = True
    world.facts["moral_value"] = "sharing"
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    helper = f["helper"]
    return [
        f'Write a short fable about a little {hero.type} named {hero.id} who goes on a quest and learns to share.',
        f"Tell a gentle story in which {hero.id} and {helper.label} look for {quest.reward} but choose fairness over greed.",
        f'Write a child-friendly fable using the word "evaluate" and ending with a fair sharing decision.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Helper = f["helper"]
    quest: Quest = f["quest"]
    treasure: Entity = f["treasure"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who is the little hero in the story?",
            answer=f"The hero is {hero.id}, a little {hero.traits[0]} {hero.type}.",
        ),
        QAItem(
            question=f"What quest did {hero.id} go on?",
            answer=f"{hero.id} went on a quest to {quest.verb}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} on the quest?",
            answer=f"{helper.label} helped {hero.id} in {place}.",
        ),
        QAItem(
            question=f"What treasure did they find?",
            answer=f"They found {treasure.phrase}.",
        ),
        QAItem(
            question=f"What did {hero.id} decide to do with the treasure?",
            answer=f"{hero.id} decided to share it fairly instead of keeping it all.",
        ),
        QAItem(
            question=f"Why was sharing important in this story?",
            answer="Sharing was important because it made the quest fair and kept the friends from feeling left out.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let other people use or have some of what you have.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal or journey where someone looks for something important or tries to do something important.",
        ),
        QAItem(
            question="What does it mean to evaluate something?",
            answer="To evaluate something means to think about it carefully and judge what is best or fairest.",
        ),
        QAItem(
            question="Why is fairness important?",
            answer="Fairness is important because it helps everyone feel respected and included.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A quest is reasonable when it is a sharing-moral quest.
reasonable(Q,T) :- quest(Q), treasure(T), share_quest(Q), shareable(T).

valid_story(S,Q,T) :- setting(S), quest(Q), treasure(T), reasonable(Q,T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        if "share" in q.tags:
            lines.append(asp.fact("share_quest", qid))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        if t.can_share:
            lines.append(asp.fact("shareable", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small fable about evaluating a quest and sharing fairly."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.quest and args.treasure:
        q, t = QUESTS[args.quest], TREASURES[args.treasure]
        if not quest_is_reasonable(q, t):
            raise StoryError(explain_rejection(q, t))
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.quest is None or c[1] == args.quest)
        and (args.treasure is None or c[2] == args.treasure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting_id, quest_id, treasure_id = rng.choice(sorted(combos))
    hero_type = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_id = args.helper or rng.choice(list(HELPERS))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        quest=quest_id,
        treasure=treasure_id,
        hero_name=hero_name,
        hero_type=hero_type,
        helper=helper_id,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        QUESTS[params.quest],
        TREASURES[params.treasure],
        params.hero_name,
        params.hero_type,
        HELPERS[params.helper],
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.kind == "character":
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(setting="woods", quest="berries", treasure="basket", hero_name="Nina", hero_type="girl", helper="mouse", trait="kind"),
    StoryParams(setting="meadow", quest="flowers", treasure="crown", hero_name="Owen", hero_type="boy", helper="sparrow", trait="thoughtful"),
    StoryParams(setting="river", quest="stones", treasure="pocket", hero_name="Lila", hero_type="girl", helper="hare", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:")
        for s, q, t in combos:
            print(f"  {s:8} {q:8} {t:8}")
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.quest} in {p.setting} (treasure: {p.treasure})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
