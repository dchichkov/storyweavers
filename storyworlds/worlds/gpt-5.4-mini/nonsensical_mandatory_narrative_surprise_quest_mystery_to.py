#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/nonsensical_mandatory_narrative_surprise_quest_mystery_to.py
============================================================================================

A tiny storyworld about an adventurous child, a mandatory errand, a surprising
clue, and a mystery to solve.

Seed-inspired premise
---------------------
A child is told to complete a mandatory task, but the path to finish it feels
nonsensical at first. A surprise reveals that the strange clue matters, and the
quest becomes a mystery to solve. The ending proves the child learned how to
follow clues, ask for help, and finish the task.

This script is standalone and stdlib-only. It follows the Storyweavers contract:
typed world entities with physical meters and emotional memes, a reasonableness
gate, inline ASP twin, story-grounded QA, and a traceable simulated world.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
    place: str
    scene: str
    mood: str
    contains: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    clue: str
    mand: str
    surprise: str
    solves: str
    risky: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    reveal: str
    helper: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    question: str
    answer: str
    proof: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    item = world.get("quest")
    if hero.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("clue", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("map").meters["marked"] += 1
    hero.memes["hope"] += 1
    out.append("__clue__")
    return out


def _r_mystery(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    mystery = world.get("mystery")
    clue = world.get("map")
    if clue.meters["marked"] < THRESHOLD:
        return out
    sig = ("mystery", mystery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mystery.meters["solved"] += 1
    hero.memes["focus"] += 1
    out.append("__solve__")
    return out


CAUSAL_RULES = [
    Rule("clue", "quest", _r_clue),
    Rule("mystery", "solve", _r_mystery),
]


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


def valid_combo(setting: str, quest: str, surprise: str, mystery: str) -> bool:
    return setting in SETTINGS and quest in QUESTS and surprise in SURPRISES and mystery in MYSTERIES


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid, s in SETTINGS.items():
        for qid, q in QUESTS.items():
            for suid, su in SURPRISES.items():
                for mid, m in MYSTERIES.items():
                    if q.risky and q.id in s.contains:
                        combos.append((sid, qid, suid, mid))
    return combos


def should_reject(quest: QuestItem) -> bool:
    return not quest.risky


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld: a mandatory quest, a surprise clue, and a mystery to solve."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "friend"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    if args.quest and should_reject(QUESTS[args.quest]):
        raise StoryError(f"(No story: {QUESTS[args.quest].label} is not a real quest challenge.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.surprise is None or c[2] == args.surprise)
              and (args.mystery is None or c[3] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, surprise, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "friend"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, quest, surprise, mystery, name, gender, helper, trait)


def tell(setting: Setting, quest: QuestItem, surprise: Surprise, mystery: Mystery,
         hero_name: str, hero_gender: str, helper: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait]))
    adult = world.add(Entity(id="Helper", kind="character", type=helper if helper in {"mother", "father"} else "thing", role="helper", label=f"the {helper}" if helper != "friend" else "a friend"))
    map_ent = world.add(Entity(id="map", type="thing", label=quest.label))
    q = world.add(Entity(id="quest", type="thing", label=quest.label))
    m = world.add(Entity(id="mystery", type="thing", label=mystery.label))
    hero.memes["curiosity"] = 2.0
    hero.memes["bravery"] = 2.0
    world.say(f"{hero.id} stepped into {setting.place}, where {setting.scene} and {setting.mood} air filled the day.")
    world.say(f"{hero.id} had a mandatory task: {quest.phrase}. {quest.mand}.")

    world.para()
    hero.memes["curiosity"] += 1
    world.say(f"At first the clue felt nonsensical. {surprise.reveal}")
    world.say(f"But then the surprise made sense: {surprise.helper}, and the strange mark pointed the way.")

    world.para()
    propagate(world, narrate=False)
    world.say(f"{hero.id} studied the mark and asked the mystery question: {mystery.question}")
    world.say(f"Together they solved it by using {quest.label} the right way. {mystery.proof}")

    world.para()
    hero.memes["joy"] += 2
    hero.memes["focus"] += 1
    q.meters["done"] += 1
    m.meters["solved"] += 1
    world.say(f"The quest was finished, and the answer was clear at last: {mystery.answer}.")
    world.say(f"{hero.id} walked home with {quest.solves}, and the adventure ended with a bright surprise instead of confusion.")

    world.facts.update(hero=hero, helper=adult, quest_cfg=quest, surprise=surprise, mystery=mystery,
                       setting=setting, map=map_ent, outcome="solved", task_done=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest_cfg"]
    mystery = f["mystery"]
    return [
        f'Write an adventure story for a young child that includes the words "nonsensical", "mandatory", and "narrative".',
        f"Tell a quest story where {hero.id} must finish a mandatory task, follows a surprising clue, and solves a mystery.",
        f"Write a child-facing adventure with a strange first clue, a real mystery to solve, and a happy ending.",
        f"Include a surprise, a quest, and the mystery question: {mystery.question}",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest_cfg"]
    mystery = f["mystery"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, who had to go on a small adventure and finish a mandatory task. The story follows {hero.id} from the first clue to the final answer."),
        ("What made the clue seem strange at first?",
         f"The clue seemed nonsensical because it did not make sense right away. Then the surprise showed why it mattered, and the child could use it to keep going."),
        ("How was the mystery solved?",
         f"{hero.id} followed the clue, asked the mystery question, and used {quest.label} the right way. That careful work made the answer clear at the end."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["quest_cfg"].tags) | set(world.facts["surprise"].tags) | set(world.facts["mystery"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    setting: str
    quest: str
    surprise: str
    mystery: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "cabin": Setting("cabin", "the cabin", "a lantern-lit hallway", "quiet"),
    "harbor": Setting("harbor", "the harbor", "wooden docks and waving flags", "windy"),
    "forest": Setting("forest", "the forest", "tall trees and twisting paths", "mysterious"),
}

QUESTS = {
    "deliver_note": QuestItem("deliver_note", "a sealed note", "deliver a sealed note", "The note had to reach the old lookout", "It was mandatory to bring it there", "A chalk arrow appeared on the table", "and the lookout keeper knew the secret signal", tags={"note", "mystery"}),
    "find_compass": QuestItem("find_compass", "a lost compass", "find a lost compass", "The path had to be checked twice", "It was mandatory to bring back the compass", "A shell shaped like an arrow pointed ahead", "and the compass needle turned true", tags={"compass", "quest"}),
    "count_stars": QuestItem("count_stars", "a star chart", "count the stars on the chart", "The captain wanted an exact count", "It was mandatory to finish the count before sunset", "A lantern flickered three times in a row", "and the chart made sense at last", tags={"stars", "chart"}),
}

SURPRISES = {
    "chalk": Surprise("chalk", "a chalk mark", "A chalk mark ran across the floor.", "it was left by a helper with good eyes", tags={"note", "mystery"}),
    "shell": Surprise("shell", "a shell clue", "A shell sat beside the door.", "it pointed toward the hidden path", tags={"compass", "quest"}),
    "lantern": Surprise("lantern", "a lantern flicker", "The lantern blinked three times.", "it matched the secret code", tags={"stars", "chart"}),
}

MYSTERIES = {
    "who_left_it": Mystery("who_left_it", "who left the clue", "Who left the clue behind?", "a helper left it there on purpose", "The mark matched the helper's signal.", tags={"note", "mystery"}),
    "where_path": Mystery("where_path", "where the path went", "Where did the path lead?", "the path led to the lookout", "The sign showed the way at last.", tags={"compass", "quest"}),
    "why_light": Mystery("why_light", "why the lantern blinked", "Why did the lantern blink three times?", "because it was a secret message", "The blinking matched the code exactly.", tags={"stars", "chart"}),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Max", "Theo", "Sam", "Noah"]
TRAITS = ["curious", "brave", "quick", "patient", "careful"]

KNOWLEDGE = {
    "note": [("What is a sealed note?", "A sealed note is a message that is closed up so nobody can read it until it is opened.")],
    "compass": [("What does a compass do?", "A compass shows direction and helps people find their way.")],
    "stars": [("Why do people use star charts?", "People use star charts to learn where stars are in the sky.")],
    "quest": [("What is a quest?", "A quest is a journey to find or do something important.")],
    "mystery": [("What is a mystery?", "A mystery is a question you do not know yet, so you look for clues until you find the answer.")],
    "chart": [("What is a chart?", "A chart is a picture or list that helps organize information.")],
}
KNOWLEDGE_ORDER = ["note", "compass", "stars", "quest", "mystery", "chart"]


CURATED = [
    StoryParams("cabin", "deliver_note", "chalk", "who_left_it", "Mia", "girl", "mother", "curious"),
    StoryParams("harbor", "find_compass", "shell", "where_path", "Leo", "boy", "father", "brave"),
    StoryParams("forest", "count_stars", "lantern", "why_light", "Nora", "girl", "mother", "careful"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for suid in SURPRISES:
        lines.append(asp.fact("surprise", suid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,Q,U,M) :- setting(S), quest(Q), surprise(U), mystery(M).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP and Python gates differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, quest=None, surprise=None, mystery=None, name=None, gender=None, helper=None, seed=None), random.Random(777)))
        assert sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], SURPRISES[params.surprise], MYSTERIES[params.mystery], params.name, params.gender, params.helper, params.trait)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for c in combos:
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            except StoryError as e:
                print(e)
                return
            p.seed = seed
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
