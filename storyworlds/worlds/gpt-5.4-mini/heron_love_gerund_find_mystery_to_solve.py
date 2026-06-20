#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/heron_love_gerund_find_mystery_to_solve.py
===========================================================================

A standalone story world for a small slice-of-life mystery: a child and a grown-up
notice a heron appearing in an ordinary place, worry about a little mystery, and
solve it by paying attention to everyday clues.

Seed words / instruments:
- heron
- love-gerund
- find
- Mystery to Solve
- Slice of Life

The world is intentionally small and concrete. The story state is driven by:
- a setting with a pond, path, or yard near water
- a child who loves a gerund activity
- a missing thing that creates a mystery
- a calm clue trail that leads to the answer
- a gentle ending image proving what changed

Supports the standard storyworld CLI:
  -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    has_water: bool = True
    detail: str = ""

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
class Hobby:
    id: str
    gerund: str
    line: str
    clue: str
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
class Mystery:
    id: str
    missing: str
    question: str
    clue_word: str
    answer: str
    solved_image: str
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    child = world.entities.get("child")
    if not child:
        return out
    if child.meters["mystery"] >= THRESHOLD and ("worry", "child") not in world.fired:
        world.fired.add(("worry", "child"))
        child.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_find(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    clue = world.entities.get("clue")
    if not child or not clue:
        return out
    if child.meters["clue_seen"] >= THRESHOLD and ("find", clue.id) not in world.fired:
        world.fired.add(("find", clue.id))
        child.memes["hope"] += 1
        out.append("__find__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("find", "social", _r_find)]


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


def hobby_at_setting(hobby: Hobby, setting: Setting) -> bool:
    return hobby.id in SETTING_HOBBY_MAP.get(setting.id, set())


def mystery_reasonable(hobby: Hobby, mystery: Mystery) -> bool:
    return True if hobby.id in {"watch_heron", "draw"} else True


def clue_to_answer(clue: str, mystery: Mystery) -> bool:
    return clue == mystery.clue_word


def _do_search(world: World, child: Entity, mystery: Mystery, clue: str, narrate: bool = True) -> None:
    child.meters["mystery"] += 1
    if clue == mystery.clue_word:
        child.meters["clue_seen"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, parent: Entity, setting: Setting, hobby: Hobby, mystery: Mystery) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} and {parent.label_word} walked to {setting.place}. "
        f"{setting.detail} {child.id} loved {hobby.gerund}, and the calm water made the day feel unhurried."
    )
    world.say(
        f"Near the bank, a heron stood still like a little statue. {child.id} smiled at the heron, because {child.id} liked to watch it move."
    )
    world.say(
        f"Then something small went missing: {mystery.missing}. That was the start of the mystery."
    )


def ask_mystery(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'{child.id} looked around and whispered, "{mystery.question}"'
    )


def search_clue(world: World, child: Entity, clue: str, mystery: Mystery) -> None:
    world.say(
        f"The first clue was easy to find: {clue}. {child.id} knelt down and noticed {mystery.clue_word} near the water."
    )
    _do_search(world, child, mystery, clue, narrate=True)


def solve(world: World, child: Entity, parent: Entity, mystery: Mystery) -> None:
    child.memes["relief"] += 1
    parent.memes["relief"] += 1
    world.say(
        f"At last, {child.id} and {parent.label_word} found the answer. {mystery.answer}"
    )
    world.say(
        f"The heron was never a problem at all; it had simply been waiting near the water while the missing thing turned up in the grass."
    )
    world.say(
        f"{mystery.solved_image}. {child.id} laughed, held the little found thing close, and kept watching the heron from the path."
    )


def tell(setting: Setting, hobby: Hobby, mystery: Mystery,
         child_name: str = "Maya", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="clue", type="thing", label=mystery.clue_word))
    world.facts["setting"] = setting
    world.facts["hobby"] = hobby
    world.facts["mystery"] = mystery
    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["found"] = mystery.answer

    setup(world, child, parent, setting, hobby, mystery)
    world.para()
    ask_mystery(world, child, mystery)
    search_clue(world, child, mystery.clue_word, mystery)
    world.para()
    solve(world, child, parent, mystery)
    world.facts["solved"] = True
    return world


SETTINGS = {
    "pond": Setting("pond", "the park pond", True, "The path was soft with grass, and the water shone silver."),
    "garden_pond": Setting("garden_pond", "the little garden pond", True, "The garden was quiet except for a few buzzing bees."),
    "riverwalk": Setting("riverwalk", "the riverwalk", True, "The river moved slowly beside the paved path."),
}

HOBBIES = {
    "watch_heron": Hobby("watch_heron", "watching the heron", "watching the heron", "the heron stood still", tags={"heron"}),
    "draw": Hobby("draw", "drawing pictures", "drawing pictures", "a pencil line near the page", tags={"draw"}),
    "skip_stones": Hobby("skip_stones", "skipping stones", "skipping stones", "small circles on the water", tags={"water"}),
}

MYSTERIES = {
    "sandwich": Mystery("sandwich", "a sandwich from lunch", "Where did the sandwich go?", "crumbs", "It had slid behind the park bench.",
                        "On the bench, the missing sandwich was finally found", tags={"find", "sandwich"}),
    "hat": Mystery("hat", "a straw hat", "Who had the hat?", "feather", "The hat was caught in the low bush by the path.",
                   "In the bush, the hat sat in plain sight", tags={"find", "hat"}),
    "keys": Mystery("keys", "the house keys", "Where are the keys?", "shiny", "They had fallen under the picnic blanket.",
                    "Under the blanket, the keys flashed back at them", tags={"find", "keys"}),
}

SETTING_HOBBY_MAP = {
    "pond": {"watch_heron", "skip_stones"},
    "garden_pond": {"watch_heron", "draw"},
    "riverwalk": {"watch_heron", "skip_stones"},
}

GIRL_NAMES = ["Maya", "Lila", "Nora", "Zoe", "Ivy", "Ella"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Milo", "Noah", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for hid, hobby in HOBBIES.items():
            if not hobby_at_setting(hobby, setting):
                continue
            for mid, mystery in MYSTERIES.items():
                if clue_to_answer(mystery.clue_word, mystery):
                    combos.append((sid, hid, mid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    hobby: str
    mystery: str
    child: str
    child_gender: str
    parent: str
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


KNOWLEDGE = {
    "heron": [("What is a heron?", "A heron is a tall bird that often stands very still near water. It uses its sharp eyes to look for fish and frogs.")],
    "find": [("What does it mean to find something?", "To find something means to notice where it is after looking for it. Sometimes it was hidden, and sometimes it simply had fallen somewhere nearby.")],
    "keys": [("What are keys for?", "Keys open locks on doors, gates, and sometimes boxes. Grown-ups often keep house keys in a pocket or bag.")],
    "sandwich": [("Why do sandwiches make a good lunch?", "A sandwich is easy to carry and easy to eat. It can be a simple meal for a busy day outside.")],
    "hat": [("What does a hat do?", "A hat can shade your face from the sun and keep your head warm or cool, depending on the kind of hat.")],
}
KNOWLEDGE_ORDER = ["heron", "find", "keys", "sandwich", "hat"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s, h, m = f["setting"], f["hobby"], f["mystery"]
    return [
        f'Write a slice-of-life mystery story for a small child that includes the word "heron" and the idea of finding {m.missing}.',
        f"Tell a gentle story where {f['child'].id} loves {h.gerund}, notices a heron, and solves a small mystery near {s.place}.",
        f'Write a calm story where someone asks, "{m.question}" and the answer is found in an ordinary place.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, setting, hobby, mystery = f["child"], f["parent"], f["setting"], f["hobby"], f["mystery"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.label_word}, who spent a quiet day at {setting.place}."),
        ("What did the child love doing?",
         f"{child.id} loved {hobby.gerund}, and that is why the walk felt so peaceful."),
        ("What mystery did they need to solve?",
         f"They needed to find {mystery.missing}. The missing thing made everyone look carefully at the ground, the bench, and the grass."),
        ("What bird did they see?",
         f"They saw a heron standing near the water. It was calm and still, which fit the quiet day."),
        ("How was the mystery solved?",
         f"They followed the clue word {mystery.clue_word} and found the missing thing in an ordinary place. The answer was simple, and that made the ending feel warm."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["mystery"].tags) | set(world.facts["hobby"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pond", "watch_heron", "sandwich", "Maya", "girl", "mother"),
    StoryParams("garden_pond", "draw", "hat", "Theo", "boy", "father"),
    StoryParams("riverwalk", "skip_stones", "keys", "Lila", "girl", "mother"),
]


def explain_rejection(setting: Setting, hobby: Hobby, mystery: Mystery) -> str:
    return "(No story: the chosen pieces do not make a believable small mystery.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.has_water:
            lines.append(asp.fact("water", sid))
        for hid in SETTING_HOBBY_MAP.get(sid, set()):
            lines.append(asp.fact("affords", sid, hid))
    for hid, h in HOBBIES.items():
        lines.append(asp.fact("hobby", hid))
        for t in sorted(h.tags):
            lines.append(asp.fact("hobby_tag", hid, t))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_word", mid, m.clue_word))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,H,M) :- setting(S), affords(S,H), hobby(H), mystery(M), clue_word(M,_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid_combos differs from Python")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, hobby=None, mystery=None, child=None, child_gender=None, parent=None), random.Random(0)))
        _ = sample.story
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    else:
        print("OK: ASP parity and story generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life heron mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hobby", choices=HOBBIES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.hobby is None or c[1] == args.hobby)
              and (args.mystery is None or c[2] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hobby, mystery = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, hobby, mystery, child, child_gender, parent)


GIRL_NAMES = ["Maya", "Lila", "Nora", "Zoe", "Ivy", "Ella", "Mina"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Milo", "Noah", "Eli", "Arlo"]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], HOBBIES[params.hobby], MYSTERIES[params.mystery],
                 params.child, params.child_gender, params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = "### variant %d" % (i + 1) if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
