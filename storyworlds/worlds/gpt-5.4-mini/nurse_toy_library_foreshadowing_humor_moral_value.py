#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/nurse_toy_library_foreshadowing_humor_moral_value.py
====================================================================================

A standalone story world for a small fairy-tale domain set in a toy library.

Premise
-------
A child visits a toy library, wants to borrow a special toy too quickly, and a
kind nurse notices little foreshadowing clues that trouble is coming. The nurse
uses humor to calm things down, then models a moral value: take care, share
fairly, and return borrowed things as promised.

The domain is intentionally small and classical:
- a toy library with shelves, a checkout desk, and return bins
- a nurse who helps keep the place calm and kind
- a child whose eagerness causes a small, funny near-miss
- a patient turn toward responsibility and a warm ending

Features
--------
- Foreshadowing: tiny clues warn that something is about to wobble, squeak, or
  spill.
- Humor: a harmless comic beat eases tension.
- Moral Value: the story ends with a clear lesson about care and fairness.

The story is rendered from simulated state, not from a frozen template.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "nurse"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"nurse": "nurse"}.get(self.type, self.type)



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
    shelves: str
    desk: str

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
class Child:
    id: str
    type: str
    trait: str
    wish: str
    mistake: str
    lesson: str
    age: int = 0

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
class Nurse:
    id: str
    type: str
    title: str = "nurse"
    laugh: str = "smiled like she had heard a dozen squeaky jokes"

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
class Toy:
    id: str
    label: str
    phrase: str
    squeaks: bool = False
    fragile: bool = False

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
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.clues: int = 0

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
        clone.clues = self.clues
        return clone

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
class Rule:
    name: str
    tag: str
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    toy = world.get("toy")
    stack = world.get("stack")
    if child.memes["rushing"] >= THRESHOLD and toy.meters["squeak"] >= THRESHOLD:
        sig = ("wobble", toy.id)
        if sig not in world.fired:
            world.fired.add(sig)
            stack.meters["wobble"] += 1
            child.memes["worry"] += 1
            out.append("__clue__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["worry"] >= THRESHOLD and child.memes["clumsy"] >= THRESHOLD:
        sig = ("spill", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("table").meters["mess"] += 1
            out.append("__spill__")
    return out


CAUSAL_RULES = [
    Rule("wobble", "foreshadowing", _r_wobble),
    Rule("spill", "humor", _r_spill),
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


def predict_misstep(world: World) -> dict:
    sim = world.copy()
    sim.get("child").memes["rushing"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("stack").meters["wobble"],
        "mess": sim.get("table").meters["mess"],
    }


def setup(world: World, child: Entity, nurse: Entity, toy: Entity, setting: Setting) -> None:
    child.memes["curious"] += 1
    child.memes["joy"] += 1
    nurse.memes["kind"] += 1
    world.say(
        f"Once upon a bright morning, {child.id} went to {setting.place}, "
        f"where {setting.shelves} stood tidy and {setting.desk} shone like a small moon."
    )
    world.say(
        f"At the desk sat {nurse.id}, the nurse, who watched the room with a gentle eye."
    )
    world.say(
        f"On the middle shelf rested {toy.phrase}; it looked harmless, but {toy.label} "
        f"already had a tiny {('squeak' if toy.squeaks else 'shine')} tucked inside it."
    )


def wish(world: World, child: Entity, toy: Toy) -> None:
    child.memes["rushing"] += 1
    world.say(
        f'"I want {toy.phrase} now," said {child.id}, reaching up on tiptoe.'
    )


def foreshadow(world: World, nurse: Entity, toy: Toy) -> None:
    world.clues += 1
    nurse.memes["concern"] += 1
    world.say(
        f"{nurse.id} noticed a little clue: the toy gave a {('tiny squeak' if toy.squeaks else 'small creak')}, "
        f"and the shelf answered with a wobble."
    )
    world.say(
        f'"When a shelf sings that way," {nurse.id} said, "something might tumble like a spoon in a soup pot."'
    )


def humor(world: World, child: Entity, nurse: Entity) -> None:
    child.memes["embarrassed"] += 1
    world.say(
        f"{child.id} froze, and then sneezed so softly that even the teddy bears seemed to grin."
    )
    world.say(
        f'{nurse.id} chuckled. "Goodness," {nurse.id} said, "that was the smallest trumpet in the kingdom."'
    )


def moral_value(world: World, child: Entity, nurse: Entity, toy: Toy) -> None:
    child.memes["understanding"] += 1
    child.memes["kindness"] += 1
    world.say(
        f'{nurse.id} knelt beside {child.id} and said, "Borrowing is a promise. '
        f'We take only what we can care for, and we bring it back with a happy heart."'
    )
    world.say(
        f'{child.id} nodded and hugged {toy.label}. "I will be careful," {child.id} promised. '
        f'"A borrowed toy should go home smiling."'
    )


def resolve(world: World, child: Entity, nurse: Entity, toy: Toy) -> None:
    child.memes["joy"] += 1
    child.memes["calm"] += 1
    toy.meters["returned"] += 1
    world.say(
        f"{nurse.id} helped {child.id} carry {toy.phrase} to the checkout desk."
    )
    world.say(
        f"Together they set it in the return bin, and the toy library felt peaceful again."
    )
    world.say(
        f"{child.id} left with an empty hand and a full smile, ready to come back another day."
    )


def tell(setting: Setting, child_cfg: Child, toy: Toy, nurse_cfg: Nurse) -> World:
    world = World()
    child = world.add(Entity(id=child_cfg.id, kind="character", type=child_cfg.type, role="child"))
    nurse = world.add(Entity(id=nurse_cfg.id, kind="character", type=nurse_cfg.type, role="helper"))
    stack = world.add(Entity(id="stack", label="toy stack", type="thing"))
    table = world.add(Entity(id="table", label="checkout table", type="thing"))
    world.add(Entity(id="library", label=setting.place, type="place"))
    world.add(Entity(id="toy", label=toy.label, type="toy", attrs={"phrase": toy.phrase}))

    toy_ent = world.get("toy")
    if toy.squeaks:
        toy_ent.meters["squeak"] += 1
    if toy.fragile:
        toy_ent.meters["fragile"] += 1

    setup(world, child, nurse, toy, setting)
    world.para()
    wish(world, child, toy)
    foreshadow(world, nurse, toy)

    predicted = predict_misstep(world)
    world.facts["predicted_wobble"] = predicted["wobble"]
    world.facts["predicted_mess"] = predicted["mess"]
    world.facts["toy"] = toy
    world.facts["setting"] = setting
    world.facts["child"] = child
    world.facts["nurse"] = nurse

    if predicted["wobble"] >= THRESHOLD:
        child.memes["clumsy"] += 1
        propagate(world, narrate=False)
        world.para()
        humor(world, child, nurse)
        moral_value(world, child, nurse, toy)
        world.para()
        resolve(world, child, nurse, toy)
    else:
        # This branch still keeps the story complete and gentle.
        world.para()
        moral_value(world, child, nurse, toy)
        world.para()
        resolve(world, child, nurse, toy)

    world.facts["ending"] = "peaceful"
    return world


SETTINGS = {
    "toy_library": Setting(
        id="toy_library",
        place="the toy library",
        shelves="the toy shelves",
        desk="the checkout desk",
    ),
}

CHILDREN = [
    Child("Mina", "girl", "eager", "borrow the shiny toy", "rush too fast", "share and return"),
    Child("Owen", "boy", "careful", "choose a new toy", "climb too quickly", "wait their turn"),
    Child("Pip", "child", "curious", "find a helpful toy", "reach too high", "borrow gently"),
]

NURSES = [
    Nurse("Nora", "nurse"),
    Nurse("Iris", "nurse"),
]

TOYS = {
    "drum": Toy("drum", "the little drum", "a little drum", squeaks=True),
    "horse": Toy("horse", "the wooden horse", "a wooden horse", fragile=True),
    "crown": Toy("crown", "the golden play crown", "a golden play crown", squeaks=True),
    "kite": Toy("kite", "the ribbon kite", "a ribbon kite", fragile=True),
}



@dataclass
class StoryParams:
    setting: str
    child: str
    child_type: str
    nurse: str
    toy: str
    trait: str
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
    StoryParams("toy_library", "Mina", "girl", "Nora", "drum", "kind", 1),
    StoryParams("toy_library", "Owen", "boy", "Iris", "horse", "patient", 2),
    StoryParams("toy_library", "Pip", "child", "Nora", "crown", "gentle", 3),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for child in CHILDREN:
            for toy in TOYS:
                combos.append((setting, child.id, toy))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a nurse and a child in a toy library."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child", choices=[c.id for c in CHILDREN])
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--nurse", choices=[n.id for n in NURSES])
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
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.child:
        combos = [c for c in combos if c[1] == args.child]
    if args.toy:
        combos = [c for c in combos if c[2] == args.toy]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, child, toy = rng.choice(combos)
    nurse = args.nurse or rng.choice([n.id for n in NURSES])
    child_cfg = next(c for c in CHILDREN if c.id == child)
    return StoryParams(setting, child_cfg.id, child_cfg.type, nurse, toy, child_cfg.trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    nurse = f["nurse"]
    toy = f["toy"]
    return [
        f'Write a fairy-tale style story set in a toy library that includes the word "nurse" and the toy "{toy.label}".',
        f"Tell a gentle story about {child.id} and {nurse.id} in the toy library, with a small warning before a funny near-miss and a moral ending.",
        f"Write a story with foreshadowing, humor, and moral value where a child borrows {toy.phrase} from a toy library.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    nurse = f["nurse"]
    toy = f["toy"]
    setting = f["setting"]
    return [
        QAItem(
            question="Where does the story take place?",
            answer=f"It takes place in {setting.place}, where toys are borrowed and returned with care."
        ),
        QAItem(
            question="Who helps the child?",
            answer=f"{nurse.id}, the nurse, helps {child.id} stay calm and choose the careful way."
        ),
        QAItem(
            question=f"Why did {nurse.id} warn {child.id}?",
            answer=(
                f"{nurse.id} noticed the toy shelf wobble and heard a little squeak before anything fell. "
                f"That clue warned that rushing could make a funny mess, so {nurse.id} spoke up before trouble grew."
            ),
        ),
        QAItem(
            question="What lesson does the story teach?",
            answer=(
                "The lesson is that borrowed things should be handled carefully and returned on time. "
                "Being gentle and fair keeps the toy library peaceful for everyone."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    toy = f["toy"]
    out = [
        QAItem(
            question="What is a nurse?",
            answer="A nurse is a kind helper who takes care of people and notices when someone needs comfort or help."
        ),
        QAItem(
            question="What is a toy library?",
            answer="A toy library is a place where children can borrow toys for a while and bring them back later."
        ),
    ]
    if toy.squeaks:
        out.append(QAItem(
            question="Why can a squeaky toy be funny in a story?",
            answer="A squeaky toy can make a silly little sound at just the wrong moment, which turns worry into a harmless joke."
        ))
    if toy.fragile:
        out.append(QAItem(
            question="Why should a fragile toy be handled gently?",
            answer="A fragile toy can break if it is rushed or dropped, so careful hands help keep it whole."
        ))
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if bits:
            lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  clues: {world.clues}")
    return "\n".join(lines)


ASP_RULES = r"""
clue(wobble) :- child(rushing), toy(squeaks).
mess(spill) :- clue(wobble), child(clumsy).
story_ready :- setting(toy_library), helper(nurse), toy(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    lines.append(asp.fact("helper", "nurse"))
    for toy_id, toy in TOYS.items():
        lines.append(asp.fact("toy", toy_id))
        if toy.squeaks:
            lines.append(asp.fact("squeaks", toy_id))
        if toy.fragile:
            lines.append(asp.fact("fragile", toy_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show story_ready/0."))
    ok = bool(asp.atoms(model, "story_ready"))
    smoke = True
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, child=None, toy=None, nurse=None), random.Random(7)))
        smoke = bool(sample.story)
    except Exception:
        smoke = False
    if ok and smoke:
        print("OK: ASP gate and generation smoke test passed.")
        return 0
    print("MISMATCH or smoke test failure.")
    return 1


def generate(params: StoryParams) -> StorySample:
    child_cfg = next(c for c in CHILDREN if c.id == params.child)
    nurse_cfg = next(n for n in NURSES if n.id == params.nurse)
    world = tell(SETTINGS[params.setting], child_cfg, TOYS[params.toy], nurse_cfg)
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
        print(asp_program("", "#show story_ready/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("story-ready set available")
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
