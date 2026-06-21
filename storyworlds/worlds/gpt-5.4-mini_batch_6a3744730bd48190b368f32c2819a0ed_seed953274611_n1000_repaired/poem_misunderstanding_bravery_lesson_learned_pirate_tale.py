#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/poem_misunderstanding_bravery_lesson_learned_pirate_tale.py
==========================================================================================

A standalone storyworld for a small pirate-tale domain built from the seed words
"poem", "misunderstanding", "bravery", and "lesson learned".

Premise
-------
Two young pirates hear a mysterious poem, misunderstand the message, and rush
toward a risky "treasure" clue. Their brave choice helps them cross a scary
place, but the misunderstanding turns out to be harmless: the poem was really a
riddle about where to find a lost kite, not a warning of a ghost. A grown-up
explains the truth, and the crew learns that brave hearts still need careful
listening.

The simulation uses typed entities with physical meters and emotional memes,
state-driven turns, a reasonableness gate, and an ASP twin.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    dark_spot: str
    wind: str
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
class Clue:
    id: str
    label: str
    poem_line: str
    risk_word: str
    hidden_meaning: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
class StoryParams:
    setting: str
    clue: str
    response: str
    hero1: str
    hero1_gender: str
    hero2: str
    hero2_gender: str
    parent: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def _r_scared(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["mystery"] < THRESHOLD:
            continue
        sig = ("scared", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] += 1
        out.append("")
    return out


def _r_truth(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("misunderstanding") and not world.facts.get("explained"):
        sig = ("truth", 1)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.facts["explained"] = True
    return out


CAUSAL_RULES = [Rule("scared", _r_scared), Rule("truth", _r_truth)]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                for s in sents:
                    if s:
                        world.say(s)


def hazard_at_risk(setting: Setting, clue: Clue) -> bool:
    return "danger" in setting.tags and "warning" in clue.tags


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for sid, setting in SETTINGS.items():
        for cid, clue in CLUES.items():
            for rid, response in RESPONSES.items():
                if hazard_at_risk(setting, clue):
                    combos.append((sid, cid, rid))
    return combos


def hide_and_seek_truth(world: World, clue: Clue) -> None:
    world.facts["misunderstanding"] = True
    world.say(
        f"At the {world.facts['setting'].place}, {clue.poem_line} drifted in on the wind."
    )
    world.say(
        f"The words sounded like a warning, so the crew took the {clue.risk_word} very seriously."
    )


def brave_move(world: World, a: Entity, b: Entity, setting: Setting, clue: Clue) -> None:
    a.memes["bravery"] += 1
    b.memes["bravery"] += 1
    a.meters["determined"] += 1
    b.meters["determined"] += 1
    world.say(
        f'"{a.id}, that sounds like trouble," {b.id} said, but {a.id} lifted '
        f"{a.pronoun('possessive')} chin and stepped toward the {setting.dark_spot}."
    )
    world.say(
        f'Together they crept past the creaky boards, brave enough to check the clue.'
    )


def explain_misunderstanding(world: World, parent: Entity, clue: Clue) -> None:
    world.facts["explained"] = True
    world.say(
        f"{parent.label_word.capitalize()} smiled and read the poem again. "
        f"It was not a ghost warning at all; it was a riddle about a kite hidden near the mast."
    )
    world.say(
        f'"See?" {parent.pronoun()} said. "The poem meant {clue.hidden_meaning}."'
    )


def resolve(world: World, a: Entity, b: Entity, setting: Setting, clue: Clue, response: Response) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"Then the crew found the answer: {clue.hidden_meaning}. {response.text}."
    )
    world.say(
        f"Their brave walk through the {setting.dark_spot} had not been a mistake after all."
    )
    world.say(
        f"They laughed, tied the kite string tight, and sailed home with a lesson learned: "
        f"bravery is strongest when it listens well."
    )


def tell(setting: Setting, clue: Clue, response: Response,
         hero1: Entity, hero2: Entity, parent: Entity) -> World:
    world = World()
    world.add(hero1)
    world.add(hero2)
    world.add(parent)
    world.facts["setting"] = setting
    world.facts["clue"] = clue
    world.facts["response"] = response
    world.facts["misunderstanding"] = False
    world.facts["explained"] = False

    world.say(
        f"One breezy afternoon, {hero1.id} and {hero2.id} were playing pirates at {setting.place}. "
        f"{setting.scene}"
    )
    world.say(
        f"Near the {setting.dark_spot}, they heard a little poem: \"{clue.poem_line}\""
    )
    hide_and_seek_truth(world, clue)

    world.para()
    brave_move(world, hero1, hero2, setting, clue)
    explain_misunderstanding(world, parent, clue)
    resolve(world, hero1, hero2, setting, clue, response)
    return world


SETTINGS = {
    "cove": Setting(
        id="cove",
        place="the moonlit cove",
        scene="The sand was dotted with shells, the little boat rocked softly, and a wooden crate became a pirate chest.",
        dark_spot="rope bridge",
        wind="salt wind",
        tags={"danger", "pirate"},
    ),
    "dock": Setting(
        id="dock",
        place="the old dock",
        scene="The planks creaked, lanterns winked, and a blanket over a barrel made a pretend captain's nest.",
        dark_spot="shadowy pier",
        wind="harbor wind",
        tags={"danger", "pirate"},
    ),
    "ship": Setting(
        id="ship",
        place="the sleepy ship",
        scene="The deck held a map made of chalk, a bucket served as a drum, and the mast cast a long stripe of shade.",
        dark_spot="top deck",
        wind="ocean wind",
        tags={"danger", "pirate"},
    ),
}

CLUES = {
    "kite_poem": Clue(
        id="kite_poem",
        label="poem",
        poem_line="When the gulls sing low and the rope sways slow, look up where the bright thread goes.",
        risk_word="warning",
        hidden_meaning="the kite string was up above, caught by the mast",
        tags={"poem", "warning"},
    ),
    "shell_poem": Clue(
        id="shell_poem",
        label="poem",
        poem_line="Follow the shell that glitters pale; it points the way to the hidden sail.",
        risk_word="secret",
        hidden_meaning="a shell trail led to the hidden sailcloth",
        tags={"poem", "warning"},
    ),
}

RESPONSES = {
    "listen": Response(
        id="listen",
        sense=3,
        power=3,
        text="Their careful listening turned the scary clue into a helpful one",
        fail="tried to solve it too quickly, but the clue stayed confusing",
        qa_text="They listened carefully and found the answer",
        tags={"listen"},
    ),
    "torch": Response(
        id="torch",
        sense=1,
        power=1,
        text="They waved a torch, but that only made the shadows dance",
        fail="shone a torch around, but it did not help",
        qa_text="They used the torch",
        tags={"torch"},
    ),
    "look_up": Response(
        id="look_up",
        sense=3,
        power=3,
        text="They looked up and saw the kite snagged by the mast",
        fail="looked around, but nothing made sense yet",
        qa_text="They looked up and spotted the clue",
        tags={"look_up"},
    ),
}

NAMES_GIRL = ["Lily", "Mina", "Zoe", "Ava"]
NAMES_BOY = ["Tom", "Finn", "Ben", "Max"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with poem, misunderstanding, bravery, and lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name1")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--name2")
    ap.add_argument("--gender2", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("That response is too weak for this storyworld.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, response = rng.choice(sorted(combos))
    g1 = args.gender1 or rng.choice(["girl", "boy"])
    g2 = args.gender2 or ("boy" if g1 == "girl" else "girl")
    name1 = args.name1 or rng.choice(NAMES_GIRL if g1 == "girl" else NAMES_BOY)
    name2 = args.name2 or rng.choice([n for n in (NAMES_GIRL if g2 == "girl" else NAMES_BOY) if n != name1])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        clue=clue,
        response=response,
        hero1=name1,
        hero1_gender=g1,
        hero2=name2,
        hero2_gender=g2,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.clue not in CLUES or params.response not in RESPONSES:
        raise StoryError("Invalid StoryParams for this world.")
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    response = RESPONSES[params.response]
    if response.sense < SENSE_MIN:
        raise StoryError("That response is too weak for this storyworld.")
    h1 = Entity(id=params.hero1, kind="character", type=params.hero1_gender, role="hero")
    h2 = Entity(id=params.hero2, kind="character", type=params.hero2_gender, role="mate")
    parent = Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent")
    world = tell(setting, clue, response, h1, h2, parent)
    world.facts["params"] = params
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s: Setting = f["setting"]
    c: Clue = f["clue"]
    return [
        f'Write a pirate tale for a young child that includes the word "poem" and takes place at {s.place}.',
        f"Tell a story where two little pirates hear a poem, misunderstand it, and then learn the truth with bravery.",
        f"Write a gentle pirate story about a poem clue, a brave choice, and a lesson learned.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    s: Setting = f["setting"]
    c: Clue = f["clue"]
    r: Response = f["response"]
    return [
        ("Where does the story happen?", f"It happens at {s.place}, where the pirates were playing."),
        ("What did the children hear?", f"They heard a poem that sounded like a warning, so they took it seriously."),
        ("What did the poem really mean?", f"It really meant {c.hidden_meaning}."),
        ("How did the children show bravery?", f"They walked toward the scary spot anyway and checked the clue instead of running away."),
        ("What lesson did they learn?", f"They learned that bravery is strongest when it listens well."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a poem?", "A poem is a short piece of writing that can sound musical or playful when you read it aloud."),
        ("What does bravery mean?", "Bravery means doing something scary while still moving forward carefully."),
        ("What is a misunderstanding?", "A misunderstanding happens when someone thinks a message means one thing, but it really means something else."),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if "warning" in c.tags:
            lines.append(asp.fact("warning_clue", cid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S,C,R) :- setting(S), clue(C), response(R), sensible(R), warning_clue(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP gate differs from Python valid_combos().")
        rc = 1
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        print("MISMATCH: ASP sensible responses differ from Python.")
        rc = 1
    else:
        print("OK: sensible responses match.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: ordinary generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_name(gender: str, rng: random.Random, avoid: str = "") -> str:
    pool = [n for n in (NAMES_GIRL if gender == "girl" else NAMES_BOY) if n != avoid]
    return rng.choice(pool)


CURATED = [
    StoryParams(setting="cove", clue="kite_poem", response="listen", hero1="Lily", hero1_gender="girl", hero2="Tom", hero2_gender="boy", parent="mother"),
    StoryParams(setting="dock", clue="shell_poem", response="look_up", hero1="Mina", hero1_gender="girl", hero2="Finn", hero2_gender="boy", parent="father"),
    StoryParams(setting="ship", clue="kite_poem", response="look_up", hero1="Ava", hero1_gender="girl", hero2="Ben", hero2_gender="boy", parent="mother"),
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
        print(asp_program("#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for s, c, r in asp_valid_combos():
            print(f"  {s:8} {c:10} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.hero1} & {p.hero2}: poem at {p.setting}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
