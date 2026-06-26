#!/usr/bin/env python3
"""
storyworlds/worlds/system_quest_sharing_ghost_story.py
======================================================

A small storyworld in the "Ghost Story" style: a child meets a shy ghost,
learns a sharing system, and finishes a little quest together.

The world is built from a simulated premise:
- a child wants to search the old house for a missing star key,
- a friendly ghost also needs the key to open a tiny moon door,
- they start with tension because only one lantern exists,
- they solve it by sharing the lantern in a turn-taking system,
- and the ending proves the quest changed both the room and their feelings.

This script follows the storyworld contract:
- self-contained stdlib script
- eager results import for QAItem / StoryError / StorySample
- lazy ASP import inside ASP helpers only
- supports the standard CLI flags and verification modes
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old house"
    mood: str = "moonlit"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    clue: str
    need: str
    danger: str
    verb: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareItem:
    id: str
    label: str
    phrase: str
    helps: set[str]
    plural: bool = False


@dataclass
class StoryParams:
    quest: str
    share_item: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


QUESTS = {
    "star_key": Quest(
        id="star_key",
        goal="find the missing star key",
        clue="a pale glitter under the stairs",
        need="a lantern",
        danger="the dark hallway is too full of creaks",
        verb="search the hallway for the star key",
        ending="the tiny moon door clicked open",
        tags={"quest", "key", "ghost"},
    ),
    "blue_note": Quest(
        id="blue_note",
        goal="find the blue note",
        clue="a flutter by the piano",
        need="a lantern",
        danger="the music room is dim and echoey",
        verb="search the music room for the blue note",
        ending="the last note floated back into the song box",
        tags={"quest", "music", "ghost"},
    ),
    "lantern_pearl": Quest(
        id="lantern_pearl",
        goal="find the lantern pearl",
        clue="a spark inside the glass",
        need="a lantern",
        danger="the cellar steps are steep and shadowy",
        verb="search the cellar for the lantern pearl",
        ending="the pearl shone like a small moon",
        tags={"quest", "moon", "ghost"},
    ),
}

SHARE_ITEMS = {
    "lantern": ShareItem(
        id="lantern",
        label="lantern",
        phrase="a warm brass lantern",
        helps={"star_key", "blue_note", "lantern_pearl"},
    ),
    "blanket": ShareItem(
        id="blanket",
        label="blanket",
        phrase="a soft patchwork blanket",
        helps={"star_key", "lantern_pearl"},
    ),
    "bell": ShareItem(
        id="bell",
        label="bell",
        phrase="a little silver bell",
        helps={"blue_note"},
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Ava", "Nora", "Ivy", "Rose", "Ella", "June"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Eli", "Sam", "Noah", "Ben"]
TRAITS = ["curious", "gentle", "brave", "careful", "quiet", "kind"]


class Rule:
    def __init__(self, name: str, fn):
        self.name = name
        self.fn = fn


def _r_shadow(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters.get("fear", 0) < THRESHOLD:
        return out
    if world.facts.get("lantern_shared"):
        sig = ("shadow_clear")
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.meters["fear"] = max(0.0, child.meters.get("fear", 0) - 1.0)
        child.memes["hope"] = child.memes.get("hope", 0) + 1
        out.append("The dark hallway felt less scary once the light moved between them.")
    return out


def _r_resolution(world: World) -> list[str]:
    out = []
    if not world.facts.get("quest_done"):
        return out
    sig = ("done")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    ghost = world.get("ghost")
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    ghost.memes["peace"] = ghost.memes.get("peace", 0) + 1
    out.append("The room settled into a happy hush.")
    return out


CAUSAL_RULES = [Rule("shadow", _r_shadow), Rule("resolution", _r_resolution)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story quest about sharing a light.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--share-item", choices=SHARE_ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["ghost", "spirit"])
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


def valid_story(quest: Quest, item: ShareItem) -> bool:
    return quest.id in item.helps


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.share_item:
        if not valid_story(QUESTS[args.quest], SHARE_ITEMS[args.share_item]):
            raise StoryError("That sharing item does not help with that quest.")
    combos = [
        (q, i)
        for q in QUESTS
        for i in SHARE_ITEMS
        if valid_story(QUESTS[q], SHARE_ITEMS[i])
    ]
    if args.quest:
        combos = [c for c in combos if c[0] == args.quest]
    if args.share_item:
        combos = [c for c in combos if c[1] == args.share_item]
    if not combos:
        raise StoryError("(No valid story matches the given options.)")
    quest_id, item_id = rng.choice(sorted(combos))
    quest = QUESTS[quest_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or "ghost"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        quest=quest_id,
        share_item=item_id,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def tell(world: World, params: StoryParams) -> World:
    quest = QUESTS[params.quest]
    item = SHARE_ITEMS[params.share_item]
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the ghost"))
    tool = world.add(Entity(
        id=item.id,
        type=item.label,
        label=item.label,
        phrase=item.phrase,
        owner=child.id,
        carried_by=child.id,
        plural=item.plural,
    ))

    world.say(
        f"{child.label} was a {params.trait} little {params.gender} who liked quiet rooms and old stories."
    )
    world.say(
        f"One night, {child.label} found {ghost.label} in {world.setting.place}, and {ghost.label} whispered about a quest to {quest.goal}."
    )
    world.say(
        f"{ghost.label} said the clue was {quest.clue}, but the hallway was dark and {quest.danger}."
    )

    world.para()
    child.meters["fear"] = 1.0
    child.memes["want"] = 1.0
    world.say(
        f"{child.label} wanted to help, but there was only one {item.label}. {child.pronoun('possessive').capitalize()} light was needed for the quest."
    )
    world.say(
        f"At first {child.label} held the {item.label} close. {ghost.pronoun('subject').capitalize()} floated nearby, waiting with a patient, chilly smile."
    )

    world.para()
    world.say(
        f"Then {child.label} made a little sharing system: one turn for the child, one turn for the ghost, and back again."
    )
    child.meters["fear"] = 0.0
    child.memes["share"] = 1.0
    ghost.memes["trust"] = 1.0
    world.facts["lantern_shared"] = True
    world.say(
        f"{child.label} held the {item.label} first, and {ghost.label} held {item.label.it()} after that, so both could follow the same light."
    )
    world.say(
        f"Together they {quest.verb}, and {quest.ending}."
    )

    world.facts["quest_done"] = True
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"In the end, {child.label} and {ghost.label} stood in the quiet room with the {item.label} between them, and the old house felt friendly instead of lonely."
    )

    world.facts.update(
        child=child,
        ghost=ghost,
        item=tool,
        quest=quest,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    quest = f["quest"]
    item = f["item"]
    return [
        f'Write a short ghost story for a child named {child.label} about a quest and a sharing system.',
        f"Tell a gentle haunted-house story where {child.label} and a ghost learn to share {item.label} while trying to {quest.verb}.",
        f'Write a moonlit story that uses the word "system" and ends with {quest.ending}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    ghost = f["ghost"]
    item = f["item"]
    quest = f["quest"]
    return [
        QAItem(
            question=f"Who did {child.label} meet in the old house?",
            answer=f"{child.label} met {ghost.label}, a quiet ghost who wanted help with a little quest.",
        ),
        QAItem(
            question=f"What did {child.label} and {ghost.label} need to share?",
            answer=f"They needed to share {item.phrase}, because only one light was enough for both of them to search.",
        ),
        QAItem(
            question=f"What was the quest?",
            answer=f"The quest was to {quest.goal}. The clue was {quest.clue}, and the ending was that {quest.ending}.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer="They made a turn-taking sharing system, so the child and the ghost could each use the light without fighting over it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost in a story is a spooky-looking character that may float through walls or old rooms.",
        ),
        QAItem(
            question="Why can a lantern help in the dark?",
            answer="A lantern gives off light, so it helps people see shadows, stairs, and doors in a dark place.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something too, often by taking turns or splitting it fairly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(quest="star_key", share_item="lantern", name="Mia", gender="girl", helper="ghost", trait="curious"),
    StoryParams(quest="blue_note", share_item="bell", name="Leo", gender="boy", helper="ghost", trait="gentle"),
    StoryParams(quest="lantern_pearl", share_item="blanket", name="Nora", gender="girl", helper="spirit", trait="brave"),
]


ASP_RULES = r"""
quest_help(Q, I) :- quest(Q), share_item(I), helps(I, Q).
valid_story(Q, I) :- quest_help(Q, I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for iid, item in SHARE_ITEMS.items():
        lines.append(asp.fact("share_item", iid))
        for q in sorted(item.helps):
            lines.append(asp.fact("helps", iid, q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = sorted((q, i) for q in QUESTS for i in SHARE_ITEMS if valid_story(QUESTS[q], SHARE_ITEMS[i]))
    clingo_set = asp_valid_stories()
    if set(py) != set(clingo_set):
        print("MISMATCH between clingo and python:")
        print("python:", py)
        print("clingo:", clingo_set)
        return 1
    print(f"OK: clingo gate matches valid_story() ({len(py)} combinations).")
    return 0


def resolve_story(sample_params: StoryParams) -> StorySample:
    world = tell(World(Setting()), sample_params)
    return StorySample(
        params=sample_params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return resolve_story(params)


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_stories()
        print(f"{len(triples)} valid quest/sharing pairs:\n")
        for q, i in triples:
            print(f"  {q:14} {i}")
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.quest} using {p.share_item}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
