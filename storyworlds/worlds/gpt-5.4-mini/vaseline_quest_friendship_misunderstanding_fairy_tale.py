#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/vaseline_quest_friendship_misunderstanding_fairy_tale.py
========================================================================================

A small storyworld for a fairy-tale quest with friendship and a misunderstanding.

Premise:
- A child or young character goes on a tiny quest to fetch or protect something
  important.
- Vaseline is a useful balm in the tale: it can soothe a chapped nose, protect
  a lantern hinge from squeaking, or help a tiny injured animal feel better.
- A misunderstanding briefly strains friendship.
- The story resolves through honesty, a kind gesture, and a shared ending image.

The world is intentionally small and constraint-checked. It generates only
plausible situations where the chosen balm, location, and quest object actually
matter.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""  # seeker, friend, helper, elder
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman"}
        male = {"boy", "father", "king", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "queen": "queen", "king": "king"}.get(self.type, self.type)



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
    mood: str
    feature: str
    path: str
    gate: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class QuestItem:
    id: str
    label: str
    phrase: str
    risk: str
    need: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Balm:
    id: str
    label: str
    phrase: str
    use: str
    kind: str = "vaseline"
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class FriendMove:
    id: str
    sense: int
    strength: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["worry"] >= THRESHOLD:
            sig = ("worry", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["misunderstanding"] += 1
            out.append("")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def quest_at_risk(setting: Setting, item: QuestItem) -> bool:
    return item.need in setting.feature or item.need in setting.path or item.need in setting.gate


def sensible_moves() -> list[FriendMove]:
    return [m for m in MOVES.values() if m.sense >= 2]


def best_move() -> FriendMove:
    return max(MOVES.values(), key=lambda m: m.sense)


def needs_balm(item: QuestItem, balm: Balm) -> bool:
    return item.need == balm.kind or item.need in balm.tags


def valid_combo(setting: Setting, item: QuestItem, balm: Balm) -> bool:
    return quest_at_risk(setting, item) and needs_balm(item, balm)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for iid, item in QUESTS.items():
            for bid, balm in BALMS.items():
                if valid_combo(setting, item, balm):
                    combos.append((sid, iid, bid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    quest: str
    balm: str
    seeker: str
    seeker_gender: str
    friend: str
    friend_gender: str
    elder: str
    elder_gender: str
    trait: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _build_setup(world: World, seeker: Entity, friend: Entity, elder: Entity, setting: Setting, quest: QuestItem) -> None:
    seeker.memes["hope"] += 1
    friend.memes["fondness"] += 1
    world.say(
        f"Once in a fair kingdom, {seeker.id} and {friend.id} walked beside {setting.place}, "
        f"where {setting.mood} air and {setting.feature} made the day feel enchanted."
    )
    world.say(
        f'They had a small quest: to bring back {quest.phrase}, because {quest.label} was needed near the {setting.gate}.'
    )
    world.say(
        f"{seeker.id} promised to lead the way, and {friend.id} promised to keep close like a loyal sparrow."
    )


def _tempt(world: World, seeker: Entity, balm: Balm, quest: QuestItem) -> None:
    seeker.memes["boldness"] += 1
    world.say(
        f"{seeker.id} peered at {quest.label} and whispered, "
        f'"I know a clever way. {balm.phrase} can help us keep going."'
    )


def _misunderstand(world: World, friend: Entity, seeker: Entity, quest: QuestItem, elder: Entity) -> None:
    friend.memes["worry"] += 1
    world.say(
        f"{friend.id} frowned. " 
        f'"No, {seeker.id}, I thought you wanted to take {quest.label} for yourself," '
        f"{friend.pronoun()} said."
    )
    world.say(
        f"{seeker.id} gasped, because that was not the plan at all. "
        f"At once, the path felt colder than before."
    )


def _repair(world: World, elder: Entity, seeker: Entity, friend: Entity, balm: Balm, quest: QuestItem) -> None:
    seeker.memes["honesty"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"Then {elder.id}, the wise elder, came with a calm smile. "
        f'"A misunderstanding is just a shadow," {elder.pronoun()} said. '
        f'"Speak plainly, and let the heart see the light."'
    )
    world.say(
        f"{seeker.id} explained the quest at once. "
        f"{seeker.id} showed {friend.id} how {balm.phrase} could soothe {quest.risk} {quest.label} "
        f"so the little treasure would stay safe on the road."
    )
    world.say(
        f"{friend.id}'s face softened. " 
        f'"Oh! I thought you meant to hide it. I was wrong," {friend.pronoun()} admitted.'
    )
    world.say(
        f"The two friends laughed, and {friend.id} gently held the {quest.label} while {seeker.id} kept the {balm.label} close."
    )


def _ending(world: World, seeker: Entity, friend: Entity, elder: Entity, quest: QuestItem, balm: Balm) -> None:
    seeker.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Together they finished the quest, and by moonrise the {quest.label} was safe again, "
        f"shining softly beside the {balm.label}."
    )
    world.say(
        f"{seeker.id} and {friend.id} returned hand in hand, and {elder.id} smiled as the lanterns blinked awake in the tower."
    )
    world.say(
        f"From that day on, the two friends remembered that a kind word can mend a misunderstanding faster than a magic ribbon."
    )


def tell(setting: Setting, quest: QuestItem, balm: Balm,
         seeker: str = "Mina", seeker_gender: str = "girl",
         friend: str = "Finn", friend_gender: str = "boy",
         elder: str = "Queen Rowan", elder_gender: str = "queen",
         trait: str = "gentle") -> World:
    world = World()
    seeker_ent = world.add(Entity(id=seeker, kind="character", type=seeker_gender, role="seeker", traits=[trait]))
    friend_ent = world.add(Entity(id=friend, kind="character", type=friend_gender, role="friend", traits=["loyal"]))
    elder_ent = world.add(Entity(id=elder, kind="character", type=elder_gender, role="elder"))
    quest_ent = world.add(Entity(id="quest", type="thing", label=quest.label))
    balm_ent = world.add(Entity(id="balm", type="thing", label=balm.label))

    _build_setup(world, seeker_ent, friend_ent, elder_ent, setting, quest)
    world.para()
    _tempt(world, seeker_ent, balm_ent if False else balm, quest)
    _misunderstand(world, friend_ent, seeker_ent, quest, elder_ent)
    world.para()
    _repair(world, elder_ent, seeker_ent, friend_ent, balm, quest)
    _ending(world, seeker_ent, friend_ent, elder_ent, quest, balm)

    world.facts.update(
        seeker=seeker_ent,
        friend=friend_ent,
        elder=elder_ent,
        setting=setting,
        quest=quest,
        balm=balm,
        outcome="repaired",
        quest_item=quest_ent,
        balm_item=balm_ent,
        healed=needs_balm(quest, balm),
    )
    return world


SETTINGS = {
    "rosewood": Setting("rosewood lane", "gentle", "silver dew", "the ivy gate", "the old bridge"),
    "moonhill": Setting("moonhill path", "quiet", "starlit hedges", "the moon gate", "the stone arch"),
    "brook": Setting("brookside trail", "soft", "blue bells", "the moss gate", "the willow bridge"),
}

QUESTS = {
    "crown": QuestItem("crown", "little crown", "the little crown", "chapped", "protect", {"royal", "shiny"}),
    "lantern": QuestItem("lantern", "glass lantern", "the glass lantern", "squeaky", "soften", {"light", "glass"}),
    "deer": QuestItem("deer", "fawn", "the tiny fawn", "dry-nosed", "soothe", {"animal", "kind"}),
}

BALMS = {
    "vaseline": Balm("vaseline", "vaseline", "a tin of vaseline", "to soothe and protect", "soothe", {"chapped", "dry-nosed"}),
    "silk": Balm("silk", "silk cloth", "a strip of silk cloth", "to hush a squeak", "soften", {"squeaky"}),
}

MOVES = {
    "gentle": FriendMove("gentle", 3, 3, "spoke softly and shared the reason", "stayed silent and made the doubt bigger", "explained the plan in kind words", {"friendship"}),
    "hush": FriendMove("hush", 2, 2, "kept watch at the gate", "looked away", "kept watch at the gate", {"quest"}),
}

NAMES = ["Mina", "Ivy", "Lena", "Tamsin", "Finn", "Owen", "Pip", "Rowan"]
GENDERS = ["girl", "boy"]
ELDERS = [("Queen Rowan", "queen"), ("King Alder", "king")]
TRAITS = ["gentle", "brave", "curious", "kind"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a child that includes the word "vaseline" and ends with friendship healed.',
        f"Tell a quest story where {f['seeker'].id} and {f['friend'].id} travel by {f['setting'].place} and mistake one another's intentions, then mend the misunderstanding.",
        f"Write a gentle fairy tale in which a small balm helps the heroes finish their quest and proves they cared about each other all along.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker, friend, elder = f["seeker"], f["friend"], f["elder"]
    setting, quest, balm = f["setting"], f["quest"], f["balm"]
    return [
        ("Who were the friends in the story?",
         f"The story was about {seeker.id} and {friend.id}, who walked together like two good companions in a fairy tale."),
        ("What was their quest?",
         f"They were trying to bring back {quest.phrase} near {setting.gate}. That quest mattered because the little treasure needed care on the road."),
        ("What misunderstanding happened?",
         f"{friend.id} thought {seeker.id} wanted to take {quest.label} away for selfish reasons. In truth, {seeker.id} only wanted to use {balm.phrase} to help it stay safe."),
        ("How was the misunderstanding fixed?",
         f"{elder.id} asked them to speak plainly, and then {seeker.id} explained the plan. That honest talk let {friend.id} see the truth and trust {seeker.id} again."),
        ("How did the story end?",
         f"It ended with the friends walking home together, the quest finished, and the {quest.label} shining safely beside {balm.label}."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["quest"].tags) | set(f["balm"].tags) | {"friendship", "misunderstanding", "quest"}
    out: list[tuple[str, str]] = []
    if "chapped" in tags or f["balm"].kind == "soothe":
        out.append(("What is vaseline used for in a fairy tale like this?",
                    "Vaseline is a soft balm people use to soothe and protect dry or chapped skin. In a story, it can also help care for something delicate on a quest."))

    out.append(("What is a misunderstanding?",
                "A misunderstanding happens when one character thinks another means something else. A calm talk can clear it up."))

    out.append(("What makes a friendship strong?",
                "Friendship grows when friends listen, tell the truth, and help one another when things get mixed up."))

    if "glass" in tags:
        out.append(("Why should a glass lantern be handled carefully?",
                    "Glass can break if it is dropped, so you hold it gently and keep it safe on the road."))
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_at_risk(S, Q) :- setting(S), quest(Q), needs(Q, N), setting_need(S, N).
valid(S, Q, B) :- quest_at_risk(S, Q), balm(B), balm_kind(B, K), needs(Q, K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("setting_need", sid, "quest"))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("needs", qid, q.need))
    for bid, b in BALMS.items():
        lines.append(asp.fact("balm", bid))
        lines.append(asp.fact("balm_kind", bid, b.kind))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, quest=None, balm=None, seeker=None, seeker_gender=None, friend=None, friend_gender=None, elder=None, elder_gender=None, trait=None, seed=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale quest world with vaseline, friendship, and a misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--balm", choices=BALMS)
    ap.add_argument("--seeker")
    ap.add_argument("--seeker-gender", dest="seeker_gender", choices=GENDERS)
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", dest="friend_gender", choices=GENDERS)
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", dest="elder_gender", choices=[g for _, g in ELDERS])
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
    combos = valid_combos()
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.balm is None or c[2] == args.balm)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, balm = rng.choice(sorted(combos))
    q = QUESTS[quest]
    b = BALMS[balm]
    seeker_gender = args.seeker_gender or rng.choice(GENDERS)
    friend_gender = args.friend_gender or ("boy" if seeker_gender == "girl" else "girl")
    elder_gender = args.elder_gender or rng.choice([g for _, g in ELDERS])
    seeker = args.seeker or rng.choice(["Mina", "Ivy", "Lena", "Tamsin"])
    friend = args.friend or rng.choice(["Finn", "Owen", "Pip", "Rowan"])
    elder = args.elder or rng.choice([e for e, _ in ELDERS])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, quest, balm, seeker, seeker_gender, friend, friend_gender, elder, elder_gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], BALMS[params.balm],
                 params.seeker, params.seeker_gender, params.friend, params.friend_gender,
                 params.elder, params.elder_gender, params.trait)
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


CURATED = [
    StoryParams("rosewood", "crown", "vaseline", "Mina", "girl", "Finn", "boy", "Queen Rowan", "queen", "gentle"),
    StoryParams("moonhill", "deer", "vaseline", "Ivy", "girl", "Owen", "boy", "King Alder", "king", "kind"),
    StoryParams("brook", "lantern", "silk", "Lena", "girl", "Pip", "boy", "Queen Rowan", "queen", "curious"),
]


def explain_rejection(setting: Setting, quest: QuestItem, balm: Balm) -> str:
    return f"(No story: the quest for {quest.label} in {setting.place} does not need {balm.label}.)"


def outcome_of(params: StoryParams) -> str:
    return "repaired"


def asp_outcome(params: StoryParams) -> str:
    return "repaired"


def asp_show() -> str:
    return asp_program(show="#show valid/3.")


def asp_list() -> list[tuple]:
    return asp_valid_combos()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_list()
        print(f"{len(combos)} compatible (setting, quest, balm) combos:")
        for s, q, b in combos:
            print(f"  {s:10} {q:8} {b}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.seeker} and {p.friend}: {p.quest} with {p.balm}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
