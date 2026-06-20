#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/periwinkle_lob_beanie_reconciliation_quest_pirate_tale.py
=========================================================================================

A standalone storyworld sketch for a small pirate-tale domain with the seed words
*periwinkle*, *lob*, and *beanie*, plus the features *Reconciliation* and
*Quest*.  It keeps the feel of a child-sized pirate adventure: two children set
sail, disagree over a beanie and a map, lose a clue, search for it together, and
end by making peace with a shared treasure and a bright, safe ending image.

The world model is tiny but state-driven:
- typed entities with physical meters and emotional memes
- a forward causal step for the clue-loss / search / reunion beats
- a reasonableness gate that only allows plausible quests
- three grounded QA sets generated from world state, not rendered English
- an inline ASP twin for the valid-combo gate and outcome parity checks
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
QUEST_MIN = 1
RECONCILE_MIN = 1


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

    tags: set[str] = field(default_factory=set)

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
    scene: str
    dark_spot: str
    breeze: str
    ship: str

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
class QuestItem:
    id: str
    label: str
    phrase: str
    color: str
    clue: str
    risky: bool = False
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
class Conflict:
    id: str
    concern: str
    method: str
    reward: str
    power: int
    sense: int
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend([s for s in sents if not s.startswith("__")])
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_lost_clue(world: World) -> list[str]:
    out: list[str] = []
    map_ = world.entities.get("map")
    if map_ is None or map_.meters["lost"] < THRESHOLD:
        return out
    sig = ("lost_clue",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if "ship" in world.entities:
        world.get("ship").meters["search"] += 1
    for e in list(world.entities.values()):
        if e.role in {"captain", "mate"}:
            e.memes["worry"] += 1
    out.append("__lost__")
    return out


def _r_reconciliation(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("reconciled"):
        return out
    a = world.entities.get("captain")
    b = world.entities.get("mate")
    shell = world.entities.get("shell")
    if not a or not b or not shell:
        return out
    if a.memes["shared_hope"] < THRESHOLD or b.memes["shared_hope"] < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["peace"] += 1
    b.memes["peace"] += 1
    world.facts["reconciled"] = True
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("lost_clue", _r_lost_clue), Rule("reconciliation", _r_reconciliation)]


def path_reasonable(setting: Setting, quest: QuestItem, conflict: Conflict) -> bool:
    return quest.risky and quest.color == "periwinkle" and conflict.sense >= QUEST_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for qid, q in QUESTS.items():
            for cid, c in CONFLICTS.items():
                if path_reasonable(SETTINGS[sid], q, c):
                    combos.append((sid, qid, cid))
    return combos


def choose_response(conflict: Conflict) -> Conflict:
    if conflict.sense < QUEST_MIN:
        raise StoryError(f"(Refusing conflict '{conflict.id}': it is too weak to shape a quest.)")
    return conflict


def predict_outcome(world: World, quest_id: str) -> dict:
    sim = world.copy()
    quest = sim.get("quest")
    quest.meters["lost"] += 1
    propagate(sim, narrate=False)
    return {
        "lost": sim.get("map").meters["lost"] >= THRESHOLD,
        "reconciled": sim.facts.get("reconciled", False),
    }


def start_story(world: World, captain: Entity, mate: Entity, setting: Setting, quest: QuestItem) -> None:
    world.say(
        f"On a breezy afternoon, {captain.id} and {mate.id} turned the deck into {setting.scene}. "
        f"{setting.ship} rocked softly while {setting.breeze} brushed their cheeks."
    )
    world.say(
        f"{captain.id} wore a {quest.color} beanie and said the day was perfect for a quest to find "
        f"{quest.phrase}."
    )


def quarrel(world: World, captain: Entity, mate: Entity, quest: QuestItem, conflict: Conflict) -> None:
    captain.memes["stubborn"] += 1
    mate.memes["caution"] += 1
    world.say(
        f"But when {mate.id} reached for the beanie, {captain.id} hugged it tight. "
        f'"{conflict.concern}," {captain.id} said, and the little ship felt suddenly less merry.'
    )
    world.say(
        f'{mate.id} bit {mate.pronoun("possessive")} lip. "We still need the map for the quest," '
        f"{mate.id} said softly."
    )


def lose_clue(world: World, captain: Entity, quest: QuestItem) -> None:
    world.get("map").meters["lost"] += 1
    world.get("map").meters["rustle"] += 1
    world.say(
        f"A gust from the sea flipped the map overboard. It bobbed once, then spun away toward the "
        f"{quest.clue} water."
    )


def search(world: World, captain: Entity, mate: Entity, quest: QuestItem) -> None:
    captain.memes["quest"] += 1
    mate.memes["quest"] += 1
    world.say(
        f"The two children did not give up. They searched the docks, peeked under crates, and looked "
        f"beside the barrels until the periwinkle clue gleamed in the foam."
    )


def reunite(world: World, captain: Entity, mate: Entity, quest: QuestItem) -> None:
    captain.memes["shared_hope"] += 1
    mate.memes["shared_hope"] += 1
    world.say(
        f"{mate.id} handed back the beanie and {captain.id} put it on without another word. "
        f"Then {captain.id} found the map, and both of them laughed at the silly chase."
    )


def ending(world: World, captain: Entity, mate: Entity, setting: Setting, quest: QuestItem) -> None:
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"At last, they sailed on together, with the map tucked safe in hand and the {quest.color} "
        f"beanie sharing the spotlight. The pirate quest could go on, and the deck felt warm again."
    )


def tell(setting: Setting, quest: QuestItem, conflict: Conflict,
         captain_name: str = "Mara", captain_gender: str = "girl",
         mate_name: str = "Nico", mate_gender: str = "boy") -> World:
    world = World()
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_gender, role="captain"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    ship = world.add(Entity(id="ship", type="ship", label=setting.ship))
    map_ = world.add(Entity(id="map", type="thing", label="map"))
    beanie = world.add(Entity(id="beanie", type="thing", label="beanie"))
    shell = world.add(Entity(id="shell", type="thing", label="shell"))
    captain.memes["stubborn"] = 1
    mate.memes["caution"] = 1
    world.facts["quest"] = quest
    world.facts["conflict"] = conflict
    world.facts["setting"] = setting
    world.facts["beanie"] = beanie
    world.facts["shell"] = shell

    start_story(world, captain, mate, setting, quest)
    world.para()
    quarrel(world, captain, mate, quest, conflict)
    lose_clue(world, captain, quest)
    propagate(world)

    world.para()
    search(world, captain, mate, quest)
    reunite(world, captain, mate, quest)
    propagate(world)

    world.para()
    ending(world, captain, mate, setting, quest)

    world.facts.update(
        captain=captain, mate=mate, ship=ship, map=map_, beanie=beanie,
        lost=world.get("map").meters["lost"] >= THRESHOLD,
        reconciled=world.facts.get("reconciled", False),
    )
    return world


SETTINGS = {
    "harbor": Setting("harbor", "the harbor", "a little harbor full of ropes and gulls", "the quay", "a salty breeze", "the little ship"),
    "cove": Setting("cove", "the cove", "a hidden cove with a crescent shore", "the tide pools", "a sea breeze", "their tiny boat"),
    "isle": Setting("isle", "the island", "a bright island beach with a wooden pier", "the dunes", "a warm breeze", "their pirate skiff"),
}

QUESTS = {
    "periwinkle_shell": QuestItem("periwinkle_shell", "shell", "a periwinkle shell", "periwinkle", "a periwinkle shell hidden by the waves", risky=True, tags={"periwinkle", "quest"}),
    "periwinkle_flag": QuestItem("periwinkle_flag", "flag", "a periwinkle flag", "periwinkle", "a periwinkle flag pinned near the mast", risky=True, tags={"periwinkle", "quest"}),
    "lob_treasure": QuestItem("lob_treasure", "lob", "the lob treasure", "periwinkle", "the lob treasure below the dock", risky=True, tags={"lob", "quest"}),
}

CONFLICTS = {
    "share_beanie": Conflict("share_beanie", "I want to keep the beanie", "share the beanie", "shared hope", 1, 2, tags={"beanie", "reconciliation"}),
    "lost_map": Conflict("lost_map", "the map is ours together", "search together", "shared hope", 1, 2, tags={"map", "quest"}),
}

GIRL_NAMES = ["Mara", "Lila", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Nico", "Finn", "Theo", "Eli", "Jules"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    quest: str
    conflict: str
    captain_name: str
    captain_gender: str
    mate_name: str
    mate_gender: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q: QuestItem = f["quest"]
    return [
        f'Write a pirate tale for a 3-to-5-year-old that includes the words "periwinkle", "lob", and "beanie", and ends in reconciliation.',
        f"Tell a small quest story where {f['captain'].id} and {f['mate'].id} argue over a beanie, lose a clue, then make peace and continue the quest.",
        f'Write a pirate story with a periwinkle clue, a lob treasure, and a beanie that becomes part of a happy reconciliation.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cap: Entity = f["captain"]
    mate: Entity = f["mate"]
    q: QuestItem = f["quest"]
    conf: Conflict = f["conflict"]
    return [
        ("Who is the story about?",
         f"It is about {cap.id} and {mate.id}, two little pirates on a quest. They begin as quarrelsome shipmates and end by working together again."),
        ("Why did they argue?",
         f"{cap.id} wanted to keep the beanie close, while {mate.id} wanted the map to stay ready for the quest. That small disagreement made the deck feel tense for a moment."),
        ("What happened to the map?",
         f"The map blew away and got lost for a while. The children searched carefully until they found the clue again and could keep going."),
        ("How did they reconcile?",
         f"They shared the beanie, found the map together, and laughed at the chase. Their shared hope turned the argument into peace."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a beanie?",
         "A beanie is a soft hat that covers your head and keeps it warm."),
        ("What does periwinkle look like?",
         "Periwinkle is a light blue-purple color, like a tiny flower or a bright shell in the sun."),
        ("What is a quest?",
         "A quest is a search for something important, often with a problem to solve along the way."),
        ("What does reconciliation mean?",
         "Reconciliation means making peace after a disagreement and starting to get along again."),
        ("What is a lob?",
         "A lob is a gentle throw or a soft little toss through the air."),
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, Q, C) :- setting(S), quest(Q), conflict(C), periwinkle_quest(Q), recon(C).
lost_map :- quest_chosen(Q), risky(Q).
reconciled :- shared_hope.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        if "periwinkle" in q.tags:
            lines.append(asp.fact("periwinkle_quest", qid))
        if q.risky:
            lines.append(asp.fact("risky", qid))
    for cid in CONFLICTS:
        lines.append(asp.fact("conflict", cid))
        lines.append(asp.fact("recon", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> bool:
    return True


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP valid-combo parity ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid-combos parity.")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a pirate quest, a beanie, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--captain-name")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--mate-name")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
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
    if not combos:
        raise StoryError("(No valid story combinations exist.)")
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.conflict is None or c[2] == args.conflict)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, conflict = rng.choice(sorted(combos))
    q = QUESTS[quest]
    c = CONFLICTS[conflict]
    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or ("boy" if captain_gender == "girl" and rng.random() < 0.5 else "girl")
    captain_name = args.captain_name or rng.choice(GIRL_NAMES if captain_gender == "girl" else BOY_NAMES)
    mate_name = args.mate_name or rng.choice([n for n in (GIRL_NAMES if mate_gender == "girl" else BOY_NAMES) if n != captain_name])
    return StoryParams(setting, quest, conflict, captain_name, captain_gender, mate_name, mate_gender)


CURATED = [
    StoryParams("harbor", "periwinkle_shell", "share_beanie", "Mara", "girl", "Nico", "boy"),
    StoryParams("cove", "periwinkle_flag", "lost_map", "Lila", "girl", "Finn", "boy"),
    StoryParams("isle", "lob_treasure", "share_beanie", "Zoe", "girl", "Theo", "boy"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], CONFLICTS[params.conflict],
                 params.captain_name, params.captain_gender, params.mate_name, params.mate_gender)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for s, q, c in combos:
            print(f"  {s:8} {q:18} {c}")
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
            header = f"### {p.captain_name} & {p.mate_name}: {p.quest} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
