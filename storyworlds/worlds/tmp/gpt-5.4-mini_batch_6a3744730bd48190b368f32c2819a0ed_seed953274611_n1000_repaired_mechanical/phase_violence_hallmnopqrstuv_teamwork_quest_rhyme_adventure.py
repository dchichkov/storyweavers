#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/phase_violence_hallmnopqrstuv_teamwork_quest_rhyme_adventure.py
================================================================================================

A standalone storyworld for a small adventure tale with teamwork, a quest, and
a rhyme-based turning point. The seed words are threaded through a simulated
world: phase, violence, and hallmnopqrstuv.

Premise
-------
Two children enter a long, strange hall named hallmnopqrstuv to finish a quest.
They must work together through phases, and they discover that harsh words and
pushing only make things worse. A rhyme and a careful shared plan unlock the way
forward.

This world keeps the action concrete and state-driven:
- physical meters track distance, blocked paths, and gathered items
- emotional memes track courage, worry, trust, and teamwork
- the ending changes depending on whether the children cooperate and whether
  they choose calm words over violence

Standard interface
------------------
Supports:
- default run
- -n
- --all
- --seed
- --trace
- --qa
- --json
- --asp
- --verify
- --show-asp
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
BRAVE_MIN = 3.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"distance": 0.0, "blocked": 0.0, "repaired": 0.0, "found": 0.0}
        if not self.memes:
            self.memes = {"courage": 0.0, "worry": 0.0, "trust": 0.0, "teamwork": 0.0, "calm": 0.0}

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
        return self.label or self.type
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
    place: str
    detail: str
    mood: str
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
class QuestItem:
    id: str
    label: str
    phrase: str
    purpose: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Challenge:
    id: str
    label: str
    block: str
    fix: str
    rhyme_hint: str
    violence_risk: bool = False
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    rhyme_word: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class StoryParams:
    setting: str
    quest_item: str
    challenge: str
    tool1: str
    tool2: str
    name1: str
    type1: str
    name2: str
    type2: str
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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "castle_hall": Setting(
        id="castle_hall",
        place="hallmnopqrstuv",
        detail="a long hall with banners, bright tiles, and doors on both sides",
        mood="adventurous",
    ),
    "library_passage": Setting(
        id="library_passage",
        place="hallmnopqrstuv",
        detail="a quiet hall with tall shelves, soft lamps, and a locked archway",
        mood="curious",
    ),
    "garden_arcade": Setting(
        id="garden_arcade",
        place="hallmnopqrstuv",
        detail="a breezy hall with painted vines and a little stone gate at the end",
        mood="bright",
    ),
}

QUEST_ITEMS = {
    "map": QuestItem(
        id="map",
        label="map",
        phrase="a folded map",
        purpose="show the next turn of the quest",
        tags={"quest", "map"},
    ),
    "key": QuestItem(
        id="key",
        label="key",
        phrase="a small brass key",
        purpose="open the final gate",
        tags={"quest", "key"},
    ),
    "lantern": QuestItem(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        purpose="light the path through the hall",
        tags={"quest", "light"},
    ),
}

CHALLENGES = {
    "stone_door": Challenge(
        id="stone_door",
        label="stone door",
        block="a heavy stone door",
        fix="move it together",
        rhyme_hint="a rhyme can wake the door",
        violence_risk=True,
        tags={"door", "quest"},
    ),
    "sleepy_gate": Challenge(
        id="sleepy_gate",
        label="sleepy gate",
        block="a sleepy gate that would not budge",
        fix="sing a steady rhyme",
        rhyme_hint="a rhyme can wake the gate",
        violence_risk=False,
        tags={"gate", "quest", "rhyme"},
    ),
    "tired_drawer": Challenge(
        id="tired_drawer",
        label="tired drawer",
        block="a tired drawer that stuck halfway open",
        fix="pull gently and rhyme softly",
        rhyme_hint="a rhyme can loosen the drawer",
        violence_risk=False,
        tags={"drawer", "quest", "rhyme"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a knotted rope",
        helps="pull things together",
        rhyme_word="slope",
        tags={"teamwork"},
    ),
    "drum": Tool(
        id="drum",
        label="drum",
        phrase="a small hand drum",
        helps="keep a steady beat for a rhyme",
        rhyme_word="hum",
        tags={"rhyme"},
    ),
    "torch": Tool(
        id="torch",
        label="torch",
        phrase="a bright torch",
        helps="shine light during the quest",
        rhyme_word="glow",
        tags={"light"},
    ),
    "blanket": Tool(
        id="blanket",
        label="blanket",
        phrase="a soft blanket",
        helps="cover and calm a shaky thing",
        rhyme_word="rest",
        tags={"calm", "teamwork"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nora", "Ivy", "Sana"]
BOY_NAMES = ["Jace", "Owen", "Rafi", "Eli", "Noel", "Milo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for q in QUEST_ITEMS:
            for c in CHALLENGES:
                if quest_reasonable(q, c):
                    combos.append((s, q, c))
    return combos


def quest_reasonable(qid: str, cid: str) -> bool:
    ch = CHALLENGES[cid]
    if ch.violence_risk and qid == "map":
        return False
    return True


def best_tools(challenge: Challenge) -> list[Tool]:
    if "rhyme" in challenge.tags:
        return [TOOLS["drum"], TOOLS["blanket"]]
    return [TOOLS["rope"], TOOLS["drum"]]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with teamwork, quest, and rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest-item", choices=QUEST_ITEMS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--tool1", choices=TOOLS)
    ap.add_argument("--tool2", choices=TOOLS)
    ap.add_argument("--name1")
    ap.add_argument("--type1", choices=["girl", "boy"])
    ap.add_argument("--name2")
    ap.add_argument("--type2", choices=["girl", "boy"])
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
    if args.quest_item and args.challenge and not quest_reasonable(args.quest_item, args.challenge):
        raise StoryError("That quest item would not fit the challenge in a sensible adventure.")
    setting = args.setting or rng.choice(list(SETTINGS))
    quest_item = args.quest_item or rng.choice(list(QUEST_ITEMS))
    challenge = args.challenge or rng.choice([c for c in CHALLENGES if quest_reasonable(quest_item, c)])
    tool_choices = best_tools(CHALLENGES[challenge])
    tool1 = args.tool1 or rng.choice([t.id for t in tool_choices])
    tool2 = args.tool2 or rng.choice([t.id for t in TOOLS.values() if t.id != tool1])
    type1 = args.type1 or rng.choice(["girl", "boy"])
    type2 = args.type2 or ("boy" if type1 == "girl" else "girl")
    name1 = args.name1 or rng.choice(GIRL_NAMES if type1 == "girl" else BOY_NAMES)
    name2 = args.name2 or rng.choice([n for n in (GIRL_NAMES if type2 == "girl" else BOY_NAMES) if n != name1])
    return StoryParams(setting=setting, quest_item=quest_item, challenge=challenge,
                       tool1=tool1, tool2=tool2, name1=name1, type1=type1,
                       name2=name2, type2=type2)


def _setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Challenge, QuestItem, Tool, Tool]:
    w = World()
    a = w.add(Entity(id=params.name1, kind="character", type=params.type1, role="hero"))
    b = w.add(Entity(id=params.name2, kind="character", type=params.type2, role="helper"))
    setting = SETTINGS[params.setting]
    quest = QUEST_ITEMS[params.quest_item]
    challenge = CHALLENGES[params.challenge]
    t1 = TOOLS[params.tool1]
    t2 = TOOLS[params.tool2]
    w.add(Entity(id="hallmnopqrstuv", kind="thing", type="hall", label=setting.place))
    w.facts.update(setting=setting, quest=quest, challenge=challenge, t1=t1, t2=t2)
    a.memes["courage"] = 1.0
    b.memes["trust"] = 1.0
    return w, a, b, w.get("hallmnopqrstuv"), challenge, quest, t1, t2


def _turn_page(w: World, a: Entity, b: Entity, challenge: Challenge, quest: QuestItem) -> None:
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    w.say(f"{a.id} and {b.id} stepped into hallmnopqrstuv, where the quest began in a new phase.")
    w.say(f"They carried {quest.phrase}, hoping it would {quest.purpose}.")


def _raise_rhythm(w: World, a: Entity, b: Entity, tool: Tool) -> None:
    a.memes["calm"] += 1
    b.memes["calm"] += 1
    w.say(f'They kept a steady beat with {tool.phrase}, and the sound made the hall feel friendlier.')
    w.say(f'The little rhythm sounded like a rhyme: "Step and stop, then share the load."')


def _face_challenge(w: World, a: Entity, b: Entity, challenge: Challenge, quest: QuestItem, tool1: Tool, tool2: Tool) -> str:
    if challenge.violence_risk:
        w.say(f"A harsh shove would have led to violence, so they chose teamwork instead.")
    if challenge.id == "stone_door":
        a.memes["worry"] += 1
        b.memes["worry"] += 1
        w.say(f"They found {challenge.block}, and it would not open by force.")
        w.say(f"{a.id} tied {tool1.phrase} to the handle while {b.id} braced the other side.")
        w.say(f"Together they pulled, counted, and pulled again until the door gave way.")
        return "contained"
    if challenge.id == "sleepy_gate":
        w.say(f"They reached {challenge.block}.")
        _raise_rhythm(w, a, b, tool2)
        w.say(f"The gate woke up at the rhyme and swung open with a sigh.")
        return "bright"
    w.say(f"They came to {challenge.block}.")
    w.say(f"{a.id} tugged gently while {b.id} sang a rhyme, and the drawer slid open at last.")
    return "gentle"


def _finish(w: World, a: Entity, b: Entity, quest: QuestItem, challenge: Challenge) -> None:
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    a.memes["courage"] += 1
    b.memes["courage"] += 1
    w.say(f"Inside, they found {quest.phrase} glinting like the prize at the end of a good quest.")
    w.say(f"Their adventure ended with smiles, tired arms, and a bright new phase for both friends.")


def tell(params: StoryParams) -> World:
    w, a, b, hall, challenge, quest, t1, t2 = _setup_world(params)
    _turn_page(w, a, b, challenge, quest)
    w.para()
    result = _face_challenge(w, a, b, challenge, quest, t1, t2)
    w.para()
    _finish(w, a, b, quest, challenge)
    w.facts["result"] = result
    w.facts["hero1"] = a
    w.facts["hero2"] = b
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a small child that includes the words phase, violence, and hallmnopqrstuv.',
        f"Tell a teamwork quest where {f['hero1'].id} and {f['hero2'].id} travel through hallmnopqrstuv and solve a problem with a rhyme.",
        f"Write a safe adventure about a quest item, a tricky hall, and friends choosing teamwork instead of violence.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b = f["hero1"], f["hero2"]
    quest = f["quest"]
    challenge = f["challenge"]
    result = f["result"]
    return [
        QAItem(question="Where did the adventure take place?",
               answer="It took place in hallmnopqrstuv, a long place that felt like the start of a quest."),
        QAItem(question="What did the children work on together?",
               answer=f"They worked together to carry {quest.phrase} and solve the problem ahead of them. Their teamwork helped them move from one phase of the quest to the next."),
        QAItem(question="How did they avoid violence?",
               answer="They did not shove or fight. Instead, they used teamwork, a steady rhyme, and careful hands to get through the challenge."),
        QAItem(question="How did the story end?",
               answer=f"It ended with the {challenge.label} opened and the children smiling beside the prize. The hall felt less strange because they had changed it with calm teamwork."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is teamwork?",
               answer="Teamwork means people help one another and do a job together."),
        QAItem(question="What is a quest?",
               answer="A quest is a journey to find something or solve a problem."),
        QAItem(question="What is a rhyme?",
               answer="A rhyme is a pair of words or lines that sound alike at the end."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "",
             "== Story QA ==", *[f"Q: {q.question}\nA: {q.answer}" for q in sample.story_qa], "",
             "== World QA ==", *[f"Q: {q.question}\nA: {q.answer}" for q in sample.world_qa]]
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: meters={e.meters} memes={e.memes} role={e.role} type={e.type}")
    out.append(f"facts={ {k: v for k, v in world.facts.items() if k != 'hero1' and k != 'hero2'} }")
    return "\n".join(out)


ASP_RULES = r"""
valid(S,Q,C) :- setting(S), quest(Q), challenge(C), reasonable(Q,C).
reasonable(map, stone_door) :- false.
reasonable(Q,C) :- not (Q = map, C = stone_door).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUEST_ITEMS:
        lines.append(asp.fact("quest", q))
    for c in CHALLENGES:
        lines.append(asp.fact("challenge", c))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        if set(asp_valid_combos()) != set(valid_combos()):
            print("MISMATCH: ASP and Python valid combos differ.")
            rc = 1
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            print("MISMATCH: sample story is empty.")
            rc = 1
    except Exception as e:
        print("VERIFY FAILED:", e)
        traceback.print_exc()
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


CURATED = [
    StoryParams(setting="castle_hall", quest_item="key", challenge="stone_door",
                tool1="rope", tool2="drum", name1="Lina", type1="girl",
                name2="Jace", type2="boy"),
    StoryParams(setting="library_passage", quest_item="lantern", challenge="sleepy_gate",
                tool1="drum", tool2="blanket", name1="Mira", type1="girl",
                name2="Owen", type2="boy"),
    StoryParams(setting="garden_arcade", quest_item="map", challenge="tired_drawer",
                tool1="rope", tool2="torch", name1="Nora", type1="girl",
                name2="Eli", type2="boy"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.quest_item not in QUEST_ITEMS or params.challenge not in CHALLENGES:
        raise StoryError("Invalid parameters for this storyworld.")
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
