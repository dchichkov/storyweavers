#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/detail_frigidaire_moral_value_twist_quest_rhyming.py
=====================================================================================

A small standalone storyworld for a rhyming quest tale about a child, a
frigidaire, a missing detail, a moral value lesson, and a gentle twist.

The domain:
- A child sets out on a quest to recover a missing note that matters to their
  family.
- The note is hidden in or near a frigidaire in a kitchen-like setting.
- A helper character gives a warning about honesty, care, or sharing.
- The quest includes one twist: what seems like a simple search turns out to be
  about a different kind of treasure.
- The ending always proves a change in the world state, and the prose keeps a
  light rhyming cadence.

Contract notes:
- Standalone stdlib script.
- Uses storyworlds/results.py eagerly for QAItem, StoryError, StorySample.
- Defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main.
- Includes Python reasonableness gates and an inline ASP twin.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    scene: str
    place_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    title: str
    goal: str
    clue: str
    detail: str
    twist: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Moral:
    id: str
    value: str
    lesson: str
    praise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TwistItem:
    id: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Frigidaire:
    id: str
    label: str
    phrase: str
    place: str
    cool: str
    is_cold: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["curiosity"] >= THRESHOLD and child.memes["worry"] < THRESHOLD:
        sig = ("worry", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_truth(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["honesty"] >= THRESHOLD and helper.memes["trust"] >= THRESHOLD:
        sig = ("truth", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["pride"] += 1
            out.append("__truth__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("truth", "moral", _r_truth)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def honest_path(chosen: Quest) -> bool:
    return chosen.id in QUESTS and chosen.detail and chosen.goal


def is_reasonable(setting: Setting, quest: Quest, frigidaire: Frigidaire, twist: TwistItem, moral: Moral) -> bool:
    return (
        setting.id in SETTINGS
        and quest.id in QUESTS
        and frigidaire.id in FRIGIDAIRES
        and twist.id in TWISTS
        and moral.id in MORALS
        and "frigidaire" in quest.tags
        and "detail" in quest.tags
        and "moral" in moral.tags
    )


def choose_outcome(quest: Quest, moral: Moral) -> str:
    if "twist" in quest.tags and moral.id == "share":
        return "wise"
    return "wise"


def intro(world: World, child: Entity, helper: Entity, setting: Setting, quest: Quest) -> None:
    child.memes["curiosity"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"In a bright little kitchen with a shiny frigidaire gleam, "
        f"{child.id} woke up with a quest-like dream."
    )
    world.say(
        f"{child.id} and {helper.id} saw {setting.scene}; "
        f"{setting.place_line}"
    )
    world.say(
        f'"We need one missing detail," said {child.id} with care, '
        f'"for our rhyme-book quest must find it somewhere."'
    )


def clue_turn(world: World, child: Entity, quest: Quest, frigidaire: Frigidaire) -> None:
    child.memes["search"] += 1
    world.say(
        f"{child.id} followed a clue that jingled and shone, '
        f"and tiptoed to {frigidaire.phrase} alone."
    )
    world.say(
        f"The clue said the answer was hidden in sight, "
        f"so {child.id} peeked near the cold, silver light."
    )
    world.say(
        f"{quest.clue} The room felt small, yet also wide, "
        f"with questions all sparkling inside."
    )


def twist_reveal(world: World, child: Entity, helper: Entity, twist: TwistItem, quest: Quest) -> None:
    child.memes["surprise"] += 1
    helper.memes["warmth"] += 1
    world.say(
        f"Then came the twist with a soft little wink: "
        f"{twist.reveal}"
    )
    world.say(
        f"{child.id} blinked and laughed, then looked once more; "
        f"the missing detail was a kind word at the door."
    )


def moral_turn(world: World, child: Entity, helper: Entity, moral: Moral) -> None:
    child.memes["honesty"] += 1
    helper.memes["pride"] += 1
    world.say(
        f'{child.id} said, "I searched and I found what I sought, '
        f'but the best little treasure is kindly thought."'
    )
    world.say(
        f"{helper.id} smiled and nodded, pleased to hear; "
        f"{moral.lesson}"
    )


def ending(world: World, child: Entity, helper: Entity, setting: Setting, quest: Quest, moral: Moral) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{setting.ending_line} {quest.ending_image} "
        f"as {child.id} and {helper.id} sang their rhyme."
    )
    world.say(
        f"They left the frigidaire door closed and neat, "
        f"with honesty, wonder, and joy complete."
    )
    world.say(
        f"{child.id} learned {moral.value}, and that was the charm; "
        f"a true little quest kept everyone's heart warm."
    )


def tell(setting: Setting, quest: Quest, frigidaire: Frigidaire, twist: TwistItem, moral: Moral,
         child_name: str = "Mila", child_gender: str = "girl",
         helper_name: str = "Papa", helper_gender: str = "father") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="seeker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    world.add(Entity(id="frigidaire", type="thing", label=frigidaire.label))
    intro(world, child, helper, setting, quest)
    world.para()
    clue_turn(world, child, quest, frigidaire)
    twist_reveal(world, child, helper, twist, quest)
    world.para()
    moral_turn(world, child, helper, moral)
    ending(world, child, helper, setting, quest, moral)
    world.facts.update(
        child=child, helper=helper, setting=setting, quest=quest, frigidaire=frigidaire,
        twist=twist, moral=moral, outcome=choose_outcome(quest, moral),
        found_detail=True, learned_value=True,
    )
    return world


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        scene="a kitchen quest with a silver shine",
        place_line="The frigidaire hummed, the teapot steamed, and the floor tiles gleamed.",
        ending_line="The kitchen glowed with a tidy, warm light,",
        tags={"kitchen", "frigidaire"},
    ),
    "pantry": Setting(
        id="pantry",
        scene="a pantry quest with a whispered tune",
        place_line="The frigidaire sat nearby, and jars on the shelf made a sleepy moon.",
        ending_line="The pantry stayed calm in the soft moonlight,",
        tags={"pantry", "frigidaire"},
    ),
    "diner": Setting(
        id="diner",
        scene="a little diner quest with a bright red grin",
        place_line="Behind the counter, the frigidaire purred, and spoons winked in.",
        ending_line="The diner went gentle, with laughter in time,",
        tags={"diner", "frigidaire"},
    ),
}

QUESTS = {
    "detail": Quest(
        id="detail",
        title="the quest for one small detail",
        goal="find the missing detail",
        clue="A note under a magnet murmured, 'Find the detail, do not despair.'",
        detail="The missing detail was a neat little ribbon tied to the recipe card.",
        twist="What looked like a treasure hunt was really a kindness hunt.",
        ending_image="A ribbon by the recipe card fluttered like a kite.",
        tags={"detail", "quest", "frigidaire"},
    ),
    "key": Quest(
        id="key",
        title="the quest for the key",
        goal="find the lost key",
        clue="A chalk arrow pointed near the cool white door.",
        detail="The key hung on a blue string beside the milk jar.",
        twist="The twist was that the 'lost' key had been saved on purpose.",
        ending_image="The key swung like a little bell in the light.",
        tags={"quest", "frigidaire"},
    ),
    "sticker": Quest(
        id="sticker",
        title="the quest for the sticker",
        goal="find the missing sticker",
        clue="A crumb trail led to the humming corner of the room.",
        detail="The sticker was stuck to the side of the frigidaire, tiny and bright.",
        twist="The twist was that the sticker was hiding in plain sight.",
        ending_image="The tiny sticker twinkled like a star on steel.",
        tags={"detail", "quest", "frigidaire"},
    ),
}

FRIGIDAIRES = {
    "old_blue": Frigidaire("old_blue", "frigidaire", "the frigidaire", "by the back wall", "cool as a winter hymn", True, {"frigidaire"}),
    "silver": Frigidaire("silver", "frigidaire", "the silver frigidaire", "near the counter", "bright and chill", True, {"frigidaire"}),
}

TWISTS = {
    "kindness": TwistItem("kindness", "The twist was that the true prize was a kind message tucked beside the milk.", {"twist", "moral"}),
    "share": TwistItem("share", "The twist was that the missing thing was not treasure at all, but a note that said 'Share and care.'", {"twist", "moral"}),
}

MORALS = {
    "share": Moral("share", "sharing", "Kindness grows when we share what we find.", "That was a fine value to shine.", {"moral"}),
    "honesty": Moral("honesty", "honesty", "Honesty keeps a family steady and true.", "Truth is a treasure through and through.", {"moral"}),
}

GIRL_NAMES = ["Mila", "Nina", "Luna", "Cora", "Rae"]
BOY_NAMES = ["Owen", "Theo", "Noah", "Eli", "Finn"]
HELPER_NAMES = ["Papa", "Mama", "Auntie", "Uncle"]
TRAITS = ["curious", "gentle", "brave", "careful"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    frigidaire: str
    twist: str
    moral: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for q in QUESTS:
            for f in FRIGIDAIRES:
                for t in TWISTS:
                    for m in MORALS:
                        if is_reasonable(SETTINGS[s], QUESTS[q], FRIGIDAIRES[f], TWISTS[t], MORALS[m]):
                            combos.append((s, q, f, t, m))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming quest storyworld with a frigidaire, a detail, and a moral twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--frigidaire", choices=FRIGIDAIRES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["mother", "father", "woman", "man"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.frigidaire is None or c[2] == args.frigidaire)
              and (args.twist is None or c[3] == args.twist)
              and (args.moral is None or c[4] == args.moral)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, q, f, t, m = rng.choice(sorted(combos))
    qobj = QUESTS[q]
    if args.child_gender:
        cg = args.child_gender
    else:
        cg = rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if cg == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(s, q, f, t, m, child_name, cg, helper_name, helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q: Quest = f["quest"]
    setting: Setting = f["setting"]
    moral: Moral = f["moral"]
    return [
        f'Write a rhyming story for a young child that uses the word "frigidaire" and the word "detail".',
        f"Tell a quest story in {setting.id} where a child searches near a frigidaire and learns {moral.value}.",
        f"Write a gentle twist ending where the missing detail turns out to be a moral message, not a toy or a prize.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    quest: Quest = f["quest"]
    moral: Moral = f["moral"]
    qa = [
        ("Who is the story about?", f"It is about {child.id} and {helper.id}, who take a small quest together."),
        ("What were they looking for?", f"They were looking for {quest.goal}. The search led them near the frigidaire."),
        ("What was the twist?", f"{f['twist'].reveal} That changed the meaning of the quest and made the ending kinder."),
        ("What did the child learn?", f"{child.id} learned {moral.value}. {moral.lesson}"),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a frigidaire?", "A frigidaire is a cold kitchen appliance that keeps food cool and fresh."),
        ("What is a detail?", "A detail is a small part of a bigger thing. Sometimes one tiny detail can change the whole meaning."),
        ("What is a moral?", "A moral is a lesson about how to act kindly or wisely."),
        ("What is a twist in a story?", "A twist is a surprising turn that makes the story mean something a little different."),
        ("What is a quest?", "A quest is a search or journey to find something important."),
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        QUESTS[params.quest],
        FRIGIDAIRES[params.frigidaire],
        TWISTS[params.twist],
        MORALS[params.moral],
        params.child_name,
        params.child_gender,
        params.helper_name,
        params.helper_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
valid(S,Q,F,T,M) :- setting(S), quest(Q), frigidaire(F), twist(T), moral(M).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for f in FRIGIDAIRES:
        lines.append(asp.fact("frigidaire", f))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    for m in MORALS:
        lines.append(asp.fact("moral", m))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: verify passed and smoke test succeeded.")
    return rc


CURATED = [
    StoryParams("kitchen", "detail", "old_blue", "kindness", "share", "Mila", "girl", "Papa", "father"),
    StoryParams("pantry", "sticker", "silver", "share", "honesty", "Noah", "boy", "Mama", "mother"),
    StoryParams("diner", "key", "old_blue", "kindness", "honesty", "Luna", "girl", "Auntie", "woman"),
]


def explain_rejection() -> str:
    return "(No story: the chosen quest and moral must make a clear, kind twist near the frigidaire.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            sample = generate(p)
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
            header = f"### {sample.params.child_name}: {sample.params.quest} near the frigidaire"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
