#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/frank_male_rumpus_quest_ghost_story.py
======================================================================

A standalone storyworld for a small ghost-story quest about a child, a calm
ghost, and a spooky rumpus that turns into a helpful rescue.

Seed inspiration:
- Words: frank, male, rumpus
- Feature: Quest
- Style: Ghost Story

The world model is built around a simple mystery:
a child and a ghost must cross a quiet, spooky place to recover a missing,
important item before a noisy rumpus scares everyone away. The story is kept
child-facing, concrete, and state-driven: fear rises and falls, objects move,
and the ending image proves what changed.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/frank_male_rumpus_quest_ghost_story.py
    python storyworlds/worlds/gpt-5.4-mini/frank_male_rumpus_quest_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/frank_male_rumpus_quest_ghost_story.py --qa
    python storyworlds/worlds/gpt-5.4-mini/frank_male_rumpus_quest_ghost_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "ghost"}
        female = {"girl", "woman", "mother"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    dark_place: str
    sound: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Quest:
    id: str
    goal: str
    needed_item: str
    route: str
    clue: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Ghost:
    id: str
    label: str
    type: str = "ghost"
    spooky: str = "glows softly"
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Relief:
    id: str
    label: str
    kind: str = "thing"
    gives_light: bool = False
    calm: int = 0
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_fear(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["spooked"] >= THRESHOLD:
            sig = ("fear", e.id)
            if sig not in world.fired:
                world.fired.add(sig)
                e.memes["fear"] += 1
                out.append("")
    return out


def _r_rumpus(world: World) -> list[str]:
    out = []
    if world.facts.get("rumpus_started") and not world.facts.get("rumpus_settled"):
        sig = ("rumpus",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("hall").meters["noise"] += 1
            for e in list(world.entities.values()):
                if e.kind == "character":
                    e.memes["alarm"] += 1
            out.append("__rumpus__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s and not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("rumpus", _r_rumpus)]


def reasonableness_gate(setting: Setting, quest: Quest, relief: Relief) -> bool:
    return bool(setting.place and quest.goal and relief.gives_light)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for qid in QUESTS:
            for rid in RELIEFS:
                if reasonableness_gate(SETTINGS[sid], QUESTS[qid], RELIEFS[rid]):
                    combos.append((sid, qid, rid))
    return combos


def _pick_name(rng: random.Random, pool: list[str], avoid: str = "") -> str:
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def tell(setting: Setting, quest: Quest, ghost: Ghost, relief: Relief,
         child_name: str = "Frank", child_type: str = "boy",
         helper_name: str = "Mina", helper_type: str = "girl",
         parent_name: str = "Dad", parent_type: str = "father",
         male_word: str = "male", rumpus_word: str = "rumpus") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="seeker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_type, role="adult"))
    hall = world.add(Entity(id="hall", type="room", label="the hall"))
    attic = world.add(Entity(id="attic", type="room", label=setting.dark_place))
    lantern = world.add(Entity(id=relief.id, type="thing", label=relief.label))
    ghost_ent = world.add(Entity(id=ghost.id, kind="character", type="ghost", role="ghost", label=ghost.label))

    child.memes["curiosity"] = 1
    helper.memes["care"] = 1
    ghost_ent.memes["sad"] = 1

    world.say(
        f"On a windy night, {child.id} and {helper.id} found a quest in the old house. "
        f"The {setting.place} was quiet, but {setting.sound} drifted through the dark."
    )
    world.say(
        f'"I am {ghost.label}," said the ghost, frank and plain. "I need help finding {quest.needed_item}. '
        f"It was last seen along {quest.route}."
    )

    world.para()
    world.say(
        f"{child.id} looked at the shadowy {setting.dark_place}. The place felt full of cold corners "
        f"and little tapping sounds."
    )
    world.say(
        f'"We can do it," {helper.id} whispered. "But we need light for the way."'
    )

    world.para()
    world.say(
        f"{ghost.label} led them forward, while {child.id} carried the {relief.label}. "
        f"The soft glow made the stairs look less scary."
    )
    world.say(
        f"Halfway there, a {male_word} voice from the hallway made a {rumpus_word} -- a bang, a bounce, and a clatter."
    )
    world.facts["rumpus_started"] = True
    propagate(world, narrate=False)
    child.meters["spooked"] += 1
    helper.meters["spooked"] += 1

    world.para()
    world.say(
        f'{child.id} gulped. "That noise almost sent us running."'
    )
    world.say(
        f'{ghost.label} lifted {ghost.pronoun("possessive")} hand. "Not if we stay together," {ghost.pronoun()} said.'
    )

    world.para()
    world.say(
        f"They followed {quest.clue} to the last room and found {quest.needed_item} under a dusty chair."
    )
    world.say(
        f'{helper.id} held up the lantern so {child.id} could reach it, and the ghost smiled as the missing thing came back.'
    )

    world.para()
    world.say(
        f"The noisy {rumpus_word} faded at last. In the end, the old house was still dark, "
        f"but the hall was warm with a little light, and {ghost.label} looked much less lonely."
    )
    world.say(
        f"{child.id} and {helper.id} walked out with the {quest.needed_item}, the lantern, and one brave ghost by their side."
    )

    world.facts.update(
        child=child,
        helper=helper,
        parent=parent,
        ghost=ghost_ent,
        setting=setting,
        quest=quest,
        relief=relief,
        male_word=male_word,
        rumpus_word=rumpus_word,
        saved=quest.needed_item,
        completed=True,
        spooked=child.meters["spooked"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost-story quest for a child named {f["child"].id} that includes the words "frank", "male", and "rumpus".',
        f"Tell a spooky-but-kind story where {f['ghost'].label} asks for help finding {f['quest'].needed_item} and a noisy rumpus interrupts the search.",
        f'Write a child-facing quest story in an old house where a small glow helps two kids finish the job and calm a frightened ghost.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    ghost = f["ghost"]
    quest = f["quest"]
    relief = f["relief"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {helper.id}, and {ghost.label}. They work together on a quest in an old house."),
        ("What did the ghost need?",
         f"{ghost.label} needed help finding {quest.needed_item}. It was a missing thing that had to be carried back along {quest.route}."),
        ("Why did the kids need the lantern?",
         f"They needed the lantern because the house was dark and spooky. The light made the stairs and hallway easier to cross."),
        ("What happened when the rumpus started?",
         f"A loud rumpus burst from the hallway and made everyone alarmed. The noise was scary, but they stayed together and kept going."),
        ("How did the story end?",
         f"They found {quest.needed_item} and brought it back to {ghost.label}. The ending is calm and bright, with the lantern still glowing in the hall."),
    ]
    if f.get("completed"):
        qa.append((
            "What changed by the end?",
            f"The missing item was recovered, the ghost felt less lonely, and the kids were no longer as spooked. "
            f"The little light turned the quest from scary to safe enough to finish."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a ghost in a child-friendly story?",
               "A ghost is a pretend spooky character in a story. In a child-friendly tale, a ghost can be kind, lonely, or helpful instead of frightening."),
        QAItem("What does a lantern do?",
               "A lantern gives light in dark places. It helps people see their way without needing to guess."),
        QAItem("What is a quest?",
               "A quest is a story journey where characters look for something, solve a problem, or try to reach an important goal."),
        QAItem("What does frank mean when someone speaks frankly?",
               "If someone is frank, they speak plainly and honestly. They do not hide what they mean."),
        QAItem("What is a rumpus?",
               "A rumpus is a noisy commotion or rowdy disturbance. It can sound like banging, clattering, and excited voices."),
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
    for e in list(world.entities.values()):
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


SETTINGS = {
    "old_house": Setting("old_house", "the old house", "the attic", "a hush of wind", {"ghost", "quest"}),
    "manor": Setting("manor", "the manor", "the upstairs room", "a creak in the floorboards", {"ghost", "quest"}),
    "school": Setting("school", "the school after dark", "the music room", "a faraway bell", {"ghost", "quest"}),
}

QUESTS = {
    "lantern": Quest("lantern", "bring back a lantern", "the silver lantern", "up the narrow stairs", "follow the faint glow", {"quest", "light"}),
    "bell": Quest("bell", "return a small bell", "the brass bell", "through the long hall", "listen for the soft ringing", {"quest", "sound"}),
    "book": Quest("book", "find a storybook", "the old storybook", "past the dusty chairs", "look near the tall shelf", {"quest", "book"}),
}

RELIEFS = {
    "lamp": Relief("lamp", "little lamp", gives_light=True, calm=2, tags={"light"}),
    "lantern": Relief("lantern", "lantern", gives_light=True, calm=3, tags={"light"}),
    "gloworb": Relief("gloworb", "glowing orb", gives_light=True, calm=4, tags={"light"}),
}

GHOSTS = {
    "franklin": Ghost("franklin", "Franklin"),
    "marla": Ghost("marla", "Marla"),
    "noel": Ghost("noel", "Noel"),
}

FRANK_NAMES = ["Frank", "Finn", "Milo", "Theo", "Ben"]
HELPER_NAMES = ["Mina", "Lina", "Ivy", "June", "Nora"]
PARENT_NAMES = ["Dad", "Mom"]
TRAITS = ["curious", "careful", "brave", "gentle"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    quest: str
    relief: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent_name: str
    parent_gender: str
    ghost: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


CURATED = [
    StoryParams("old_house", "lantern", "lamp", "Frank", "boy", "Mina", "girl", "Dad", "father", "franklin"),
    StoryParams("manor", "bell", "lantern", "Frank", "boy", "Nora", "girl", "Mom", "mother", "marla"),
    StoryParams("school", "book", "gloworb", "Frank", "boy", "Ivy", "girl", "Dad", "father", "noel"),
]


def valid_story_choices() -> list[tuple[str, str, str]]:
    return valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story quest world with a frank child, a male voice, and a rumpus.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--relief", choices=RELIEFS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--parent-name")
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
    combos = [c for c in valid_story_choices()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.relief is None or c[2] == args.relief)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, relief = rng.choice(sorted(combos))
    child_name = args.child_name or rng.choice(FRANK_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    parent_name = args.parent_name or rng.choice(PARENT_NAMES)
    ghost = args.ghost or rng.choice(sorted(GHOSTS))
    return StoryParams(setting, quest, relief, child_name, "boy", helper_name, "girl", parent_name,
                       "father" if parent_name == "Dad" else "mother", ghost)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], GHOSTS[params.ghost], RELIEFS[params.relief],
                 params.child_name, params.child_name and "boy" or "boy",
                 params.helper_name, params.helper_name and "girl" or "girl",
                 params.parent_name, params.parent_gender, "male", "rumpus")
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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
valid(S, Q, R) :- setting(S), quest(Q), relief(R).
completed :- valid(S, Q, R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for rid in RELIEFS:
        lines.append(asp.fact("relief", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_story_choices()):
        print(f"OK: gate matches valid_combos() ({len(valid_story_choices())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, quest=None, relief=None, ghost=None,
                                                           child_name=None, helper_name=None, parent_name=None),
                                          random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
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
