#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/banyan_practice_appetite_lesson_learned_quest_happy.py
======================================================================================

A small fairy-tale story world about a child, a banyan tree, practice, appetite,
a quest, a lesson learned, and a happy ending.

The world simulates:
- a young seeker with desire, patience, and courage
- a banyan tree with a hidden path and a useful fruit
- a practice beat that changes skill and confidence
- an appetite beat that creates the need for a quest
- a lesson learned beat that turns the ending warm and complete

The prose is state-driven rather than template-swapped: meter values and memo
values change the story, and the ending image proves those changes.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/banyan_practice_appetite_lesson_learned_quest_happy.py
    python storyworlds/worlds/gpt-5.4-mini/banyan_practice_appetite_lesson_learned_quest_happy.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/banyan_practice_appetite_lesson_learned_quest_happy.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
ASP_RULES = r"""
ready_to_quest(C) :- appetite(C), practice(C), courageous(C).
lesson_learned(C) :- shared(C), helped(C).
happy_ending(C) :- lesson_learned(C), fed(C).
"""

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "fairy"}
        male = {"boy", "father", "king", "boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    scene: str
    detail: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Quest:
    id: str
    goal: str
    risk: str
    reward: str
    requires_practice: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    setting: str
    quest: str
    seeker_name: str
    seeker_gender: str
    helper_name: str
    helper_gender: str
    appetite_item: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        c.paragraphs = [[]]
        return c

@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_lesson(world: World) -> list[str]:
    out = []
    seeker = world.get("seeker")
    helper = world.get("helper")
    if seeker.meters.get("fed", 0) >= THRESHOLD and seeker.memes.get("shared", 0) >= THRESHOLD:
        sig = ("lesson",)
        if sig not in world.fired:
            world.fired.add(sig)
            seeker.memes["wisdom"] = seeker.memes.get("wisdom", 0) + 1
            helper.memes["pride"] = helper.memes.get("pride", 0) + 1
            out.append("__lesson__")
    return out

RULES = [Rule("lesson", _r_lesson)]

def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    sentences: list[str] = []
    while changed:
        changed = False
        for rule in RULES:
            s = rule.apply(world)
            if s:
                changed = True
                sentences.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in sentences:
            world.say(s)

SETTINGS = {
    "garden": Setting(id="garden", scene="a rose-gold garden", detail="a banyan cast a cool green shade over the path"),
    "courtyard": Setting(id="courtyard", scene="a moonlit courtyard", detail="a banyan stood beside a stone well and a silver gate"),
    "village": Setting(id="village", scene="a little village green", detail="a banyan rose by the baker's door like a patient old guardian"),
}

QUESTS = {
    "moon_fruit": Quest(id="moon_fruit", goal="find the glowing fruit", risk="the path is tangled and dark", reward="a basket of sweet fruit"),
    "song_bell": Quest(id="song_bell", goal="ring the quiet bell in the banyan hollow", risk="the bell is hidden among roots", reward="a gentle blessing"),
    "starlit_honey": Quest(id="starlit_honey", goal="bring home starlit honey from the tree", risk="the bees need calm hands", reward="a shining jar of honey"),
}

APPETITES = {
    "honey_cake": {"dish": "honey cake", "need": "a warm honey cake", "tag": "sweet"},
    "berry_tart": {"dish": "berry tart", "need": "a bright berry tart", "tag": "fruit"},
    "oat_porridge": {"dish": "oat porridge", "need": "a bowl of oat porridge", "tag": "plain"},
}

GIRL_NAMES = ["Mira", "Lina", "Suri", "Ada", "Nina"]
BOY_NAMES = ["Tobin", "Pavel", "Eli", "Ren", "Milo"]

def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, q, a) for s in SETTINGS for q in QUESTS for a in APPETITES]

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for aid in APPETITES:
        lines.append(asp.fact("appetite", aid))
    return "\n".join(lines)

def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        ok = 1
        print("MISMATCH in combo gate.")
        print("python only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))
    try:
        p = resolve_params(argparse.Namespace(setting=None, quest=None, appetite=None, seed=None), random.Random(7))
        s = generate(p)
        assert s.story
        print("OK: normal story generation smoke test passed.")
    except Exception as exc:
        ok = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return ok

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world about banyan, practice, appetite, quest, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--appetite", choices=APPETITES)
    ap.add_argument("--seeker")
    ap.add_argument("--helper")
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
    combos = valid_combos()
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.quest and args.quest not in QUESTS:
        raise StoryError("Unknown quest.")
    if args.appetite and args.appetite not in APPETITES:
        raise StoryError("Unknown appetite.")
    if args.setting and args.quest and args.appetite:
        if (args.setting, args.quest, args.appetite) not in combos:
            raise StoryError("This combination cannot make a reasonable fairy-tale quest.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    quest = args.quest or rng.choice(sorted(QUESTS))
    appetite = args.appetite or rng.choice(sorted(APPETITES))
    seeker = args.seeker or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != seeker])
    gender = "girl" if seeker in GIRL_NAMES else "boy"
    helper_gender = "girl" if helper in GIRL_NAMES else "boy"
    return StoryParams(setting=setting, quest=quest, seeker_name=seeker, seeker_gender=gender, helper_name=helper, helper_gender=helper_gender, appetite_item=appetite)

def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    appetite = APPETITES[params.appetite_item]
    seeker = world.add(Entity(id="seeker", kind="character", type=params.seeker_gender, label=params.seeker_name, role="seeker"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper_name, role="helper"))
    tree = world.add(Entity(id="banyan", kind="thing", type="tree", label="the banyan tree"))
    dish = world.add(Entity(id="dish", kind="thing", type="food", label=appetite["dish"]))
    seeker.memes["appetite"] = 1
    seeker.memes["courage"] = 1
    helper.memes["kindness"] = 1
    world.say(f"Once in {setting.scene}, {seeker.label} and {helper.label} came beneath {tree.label}, where {setting.detail}.")
    world.say(f"{seeker.label} had a strong appetite for {appetite['need']}, but the kitchen was empty and the stars were already out.")
    world.para()
    seeker.memes["practice"] = 1
    seeker.memes["skill"] = 1
    world.say(f"First, {helper.label} said, \"We must practice before any quest.\" So they practiced {quest.goal} steps three times by the roots.")
    world.say(f"Each time, {seeker.label} grew steadier, and the banyan leaves whispered like a kindly audience.")
    world.para()
    seeker.memes["quest"] = 1
    world.say(f"Then they began the quest: to {quest.goal}, though {quest.risk}.")
    if params.quest == "moon_fruit":
        world.say("Deep in a fork of the banyan, they found a basket of glowing fruit that shone like little moons.")
    elif params.quest == "song_bell":
        world.say("Inside a hollow of the banyan, they found the quiet bell, and it sang a soft note like falling rain.")
    else:
        world.say("At the banyan blossoms, they waited kindly, and the bees gave them a shining jar of honey.")
    seeker.memes["shared"] = 1
    seeker.meters["fed"] = 1
    world.say(f"{seeker.label} shared the treasure with {helper.label}, and {appetite['need']} became enough for two.")
    propagate(world, narrate=False)
    world.para()
    if seeker.memes.get("wisdom", 0) >= THRESHOLD:
        world.say(f"At last, {seeker.label} learned that practice makes a quest steadier, appetite can be patient, and sharing makes a treasure sweeter.")
        world.say(f"They carried home {quest.reward}, sat under the banyan's wide arms, and ate with smiles as the moon climbed high.")
    else:
        world.say(f"At last, they came home happy anyway, with {quest.reward} and a full moon above the banyan.")
    world.facts.update(
        setting=setting, quest=quest, appetite=appetite,
        seeker=seeker, helper=helper, tree=tree, dish=dish,
        outcome="happy", practiced=True, fed=True, shared=True,
    )
    return world

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a fairy tale for a child that includes the words banyan, practice, and appetite, and ends in a happy way.",
        f"Tell a quest story where {f['seeker'].label} must practice before going under the banyan tree to satisfy an appetite.",
        f"Write a gentle fairy tale about a banyan tree, a practice round, and a hungry child who learns a kind lesson.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    s = f["seeker"]
    h = f["helper"]
    q = f["quest"]
    a = f["appetite"]
    return [
        QAItem(question="What did the child want at the start?", answer=f"{s.label} had an appetite for {a['need']}, so the story began with a hungry wish."),
        QAItem(question="Why did they practice first?", answer=f"They practiced because the quest needed careful steps. Practice made {s.label} steadier before going close to the banyan roots."),
        QAItem(question="What did they learn by the end?", answer=f"They learned that practice helps a quest go well, appetite can wait, and sharing makes a happy ending feel even better."),
        QAItem(question="How did the story end?", answer=f"It ended happily with {q.reward} and a quiet meal under the banyan tree."),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a banyan tree?", answer="A banyan is a big tree with strong branches and hanging roots that can make a shady place to rest."),
        QAItem(question="What does practice do?", answer="Practice helps someone get better at a task by trying it again and again."),
        QAItem(question="What is appetite?", answer="Appetite is the feeling of wanting to eat food because you are hungry."),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: meters={e.meters} memes={e.memes} role={e.role}")
    out.append(f"facts={world.facts}")
    return "\n".join(out)

def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Invalid setting.")
    if params.quest not in QUESTS:
        raise StoryError("Invalid quest.")
    if params.appetite_item not in APPETITES:
        raise StoryError("Invalid appetite.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

CURATED = [
    StoryParams(setting="garden", quest="moon_fruit", seeker_name="Mira", seeker_gender="girl", helper_name="Eli", helper_gender="boy", appetite_item="honey_cake"),
    StoryParams(setting="courtyard", quest="song_bell", seeker_name="Tobin", seeker_gender="boy", helper_name="Lina", helper_gender="girl", appetite_item="berry_tart"),
    StoryParams(setting="village", quest="starlit_honey", seeker_name="Suri", seeker_gender="girl", helper_name="Pavel", helper_gender="boy", appetite_item="oat_porridge"),
]

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
        print(asp_program(show="#show ready_to_quest/1.\n#show lesson_learned/1.\n#show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program(show="#show ready_to_quest/1.\n#show lesson_learned/1.\n#show happy_ending/1."))
        print("ready_to_quest:", asp.atoms(model, "ready_to_quest"))
        print("lesson_learned:", asp.atoms(model, "lesson_learned"))
        print("happy_ending:", asp.atoms(model, "happy_ending"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
                params.seed = base_seed + i
                sample = generate(params)
            except StoryError as exc:
                print(exc)
                return
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
            header = f"### {p.seeker_name} at the {p.setting}: {p.quest} / {p.appetite_item}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
