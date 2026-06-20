#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/satin_bedding_noodle_repetition_moral_value_lesson.py
=====================================================================================

A standalone storyworld for a tiny comedic domestic mishap: a child tries to
make a fancy bed with satin bedding, a noodle becomes an absurd tool of
repetition, the situation gets silly, and a grown-up turns it into a moral
lesson about caring for things and sharing the work.

Seed words: satin, bedding, noodle
Features: Repetition, Moral Value, Lesson Learned
Style: Comedy
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
class Room:
    id: str
    label: str
    satin: bool = True
    bedding: bool = True
    noodle: bool = True
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
class Prop:
    id: str
    label: str
    phrase: str
    kind: str
    playful: bool = False
    tidy: bool = True
    repeatable: bool = False
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]

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
        self.room = Room("room", "the bedroom")
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
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
        clone.room = copy.deepcopy(self.room)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["repeating"] < THRESHOLD:
            continue
        sig = ("repeat", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.room.memes["mess"] += 1
        ent.memes["glee"] += 1
        out.append("__repeat__")
    return out


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    if world.room.memes["mess"] < THRESHOLD:
        return out
    sig = ("mess", "room")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.room.meters["wrinkled"] += 1
    out.append("The bed looked extra floppy and silly.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    if world.room.meters["wrinkled"] < THRESHOLD:
        return out
    sig = ("lesson", "spoken")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    parent = next((e for e in world.characters() if e.role == "parent"), None)
    child = next((e for e in world.characters() if e.role == "child"), None)
    if parent and child:
        parent.memes["wisdom"] += 1
        child.memes["lesson"] += 1
        out.append("__lesson__")
    return out


CAUSAL_RULES = [
    Rule("repeat", "comedy", _r_repeat),
    Rule("mess", "physical", _r_mess),
    Rule("lesson", "moral", _r_lesson),
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


def moral_gate(action: str, prop: Prop) -> bool:
    return action in {"tidy", "show", "share"} and prop.tidy


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for child in CHILDREN:
        for prop in PROPS:
            for action in ACTIONS:
                if moral_gate(action, prop):
                    combos.append((child, prop.id, action))
    return combos


def _do_nesting(world: World, child: Entity, prop: Prop, action: str, narrate: bool = True) -> None:
    if action == "tidy":
        child.memes["helpfulness"] += 1
        world.room.meters["tidy"] += 1
    elif action == "share":
        child.memes["kindness"] += 1
        world.room.memes["shared"] += 1
    else:
        child.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def predict(world: World, child: Entity) -> dict:
    sim = world.copy()
    sim.get(child.id).memes["repeating"] += 1
    propagate(sim, narrate=False)
    return {"mess": sim.room.memes["mess"], "wrinkled": sim.room.meters["wrinkled"]}


def intro(world: World, child: Entity, parent: Entity, prop: Prop) -> None:
    world.say(
        f"{child.id} loved the bedroom because {prop.phrase} made everything feel fancy, "
        f"like a tiny castle with clean corners."
    )
    world.say(
        f"One afternoon, {child.id} spotted the satin bedding and grinned. "
        f'"This bed needs one more touch," {child.pronoun()} said.'
    )


def noodle_bit(world: World, child: Entity, prop: Prop) -> None:
    child.memes["repeating"] += 1
    world.say(
        f"{child.id} waved a noodle like a royal wand. "
        f'"A noodle on the pillow! A noodle on the pillow!" {child.pronoun()} sang.'
    )
    world.say("Then the same line came again, because the noodle was clearly having a big day.")
    if prop.repeatable:
        world.say(f'"One more noodle," {child.id} said. "Just one more noodle."')


def warn(world: World, parent: Entity, child: Entity, prop: Prop) -> None:
    pred = predict(world, child)
    world.facts["pred"] = pred
    world.say(
        f'{parent.id} peeked in and said, "{child.id}, that fancy {prop.label} is '
        f'not a noodle plate. If you keep waving noodles at it, the bedding will '
        f'end up in a funny heap."'
    )


def reveal(world: World, parent: Entity, child: Entity, prop: Prop) -> None:
    world.say(
        f'{child.id} tried to repeat the noodle trick again, and the satin bedding '
        f'slithered into a shiny tangle on the floor.'
    )
    world.room.meters["wrinkled"] += 1
    propagate(world, narrate=False)


def lesson(world: World, parent: Entity, child: Entity, prop: Prop) -> None:
    child.memes["lesson"] += 1
    parent.memes["wisdom"] += 1
    world.say(
        f"{parent.label_word.capitalize()} did not laugh too hard, though it was very hard not to. "
        f'"A noodle is for soup, not for decorating the bed," {parent.pronoun()} said. '
        f'"When something is precious, we treat it gently."'
    )
    world.say(f"{child.id} blinked, then nodded, because the shiny bed was now definitely wiser than it looked.")


def repair(world: World, parent: Entity, child: Entity, prop: Prop, remedy: str) -> None:
    child.memes["relief"] += 1
    world.room.meters["wrinkled"] = 0.0
    world.room.memes["mess"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} showed {child.id} how to smooth the satin bedding with careful hands, "
        f"then handed over a bowl of actual noodles for lunch."
    )
    world.say(
        f'"{"No noodle on the bedding," if remedy == "share" else "First work, then play,"}" '
        f'{child.id} repeated, and this time the repetition was helpful.'
    )
    world.say(
        f"By the end, the bed was neat again, the noodles stayed in the bowl, and the room looked calm and shiny."
    )


def tell(child_name: str, child_gender: str, parent_gender: str, prop: Prop, action: str, remedy: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_gender, role="parent", label="the parent"))
    intro(world, child, parent, prop)
    world.para()
    noodle_bit(world, child, prop)
    warn(world, parent, child, prop)
    reveal(world, parent, child, prop)
    world.para()
    lesson(world, parent, child, prop)
    repair(world, parent, child, prop, remedy)
    world.facts.update(child=child, parent=parent, prop=prop, action=action, remedy=remedy, outcome="lesson")
    return world


PROPS = [
    Prop("satin", "satin bedding", "the satin bedding", "bedding", playful=True, tidy=True, repeatable=True, tags={"satin", "bedding"}),
    Prop("blanket", "a blanket", "the blanket", "bedding", playful=True, tidy=True, tags={"bedding"}),
    Prop("pillow", "a pillow fort", "the pillow fort", "bedding", playful=True, tidy=True, tags={"bedding"}),
]

ACTIONS = ["tidy", "share", "show"]

CHILDREN = ["Milo", "Mina", "Ruby", "Theo", "Luna", "Otis", "Ivy", "Nia"]
CHILD_GENDERS = ["boy", "girl"]


@dataclass
@dataclass
class StoryParams:
    child: str
    child_gender: str
    parent_gender: str
    prop: str
    action: str
    remedy: str = "share"
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
    child, prop = f["child"], f["prop"]
    return [
        f'Write a funny moral story for a young child that includes the words "satin", "bedding", and "noodle".',
        f"Tell a comedy about {child.id} and {prop.label}, where a noodle gets repeated a little too much and a grown-up turns it into a lesson.",
        f"Write a short bedtime-style story about fancy bedding, a noodle, and learning to treat nice things carefully.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, prop = f["child"], f["parent"], f["prop"]
    return [
        QAItem(
            question=f"What did {child.id} keep repeating?",
            answer=f'{child.id} kept repeating a silly noodle line, and the repetition made the story funny. It also helped show why the satin bedding got tangled.'
        ),
        QAItem(
            question=f"Why did {parent.id} give a lesson?",
            answer=f'{parent.id} gave a lesson because the satin bedding turned into a wrinkly mess. That made it a good moment to teach that precious things should be treated gently.'
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the bedding smoothed out again and the noodles back where they belonged. The child learned a moral value: care for nice things and use objects for their proper purpose."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is satin?",
            answer="Satin is a smooth, shiny fabric that can look fancy and slippery. It can be nice on bedding because it shines in the light."
        ),
        QAItem(
            question="What is bedding?",
            answer="Bedding is the sheets, blankets, and other soft things on a bed. People use bedding to make sleeping places warm and comfy."
        ),
        QAItem(
            question="What is a noodle?",
            answer="A noodle is a long strip of food, often cooked soft in soup or sauce. Noodles are for eating, not for decorating beds."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
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
    lines.append(f"  room: meters={dict(world.room.meters)} memes={dict(world.room.memes)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(prop: Prop) -> str:
    return f"(No story: this world wants satin bedding and a noodle in a funny moral lesson.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and args.action not in ACTIONS:
        raise StoryError("(Invalid action.)")
    prop_id = args.prop or rng.choice([p.id for p in PROPS])
    action = args.action or rng.choice(ACTIONS)
    child_gender = args.child_gender or rng.choice(CHILD_GENDERS)
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    child = args.child or rng.choice(CHILDREN)
    remedy = args.remedy or "share"
    if action not in {"tidy", "share", "show"}:
        raise StoryError("(No story: the lesson here needs a gentle action.)")
    return StoryParams(child, child_gender, parent_gender, prop_id, action, remedy)


def generate(params: StoryParams) -> StorySample:
    prop = next(p for p in PROPS if p.id == params.prop)
    world = tell(params.child, params.child_gender, params.parent_gender, prop, params.action, params.remedy)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic storyworld about satin bedding, a noodle, and a moral lesson.")
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["boy", "girl"])
    ap.add_argument("--parent-gender", choices=["mother", "father"])
    ap.add_argument("--prop", choices=[p.id for p in PROPS])
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--remedy", choices=["share"])
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


ASP_RULES = r"""
prop(prop_satin).
action(tidy). action(share). action(show).
valid(C,P,A) :- prop(P), action(A), A != show.
lesson(C) :- valid(C,P,A).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("prop", p.id) for p in PROPS]
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(valid_combos_asp()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combo gates differ.")
        rc = 1
    try:
        sample = generate(StoryParams("Milo", "boy", "mother", "satin", "share"))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    else:
        print("OK: generation smoke test passed.")
    return rc


CURATED = [
    StoryParams("Milo", "boy", "mother", "satin", "share"),
    StoryParams("Mina", "girl", "father", "satin", "tidy"),
    StoryParams("Ruby", "girl", "mother", "satin", "show"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(valid_combos_asp())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
