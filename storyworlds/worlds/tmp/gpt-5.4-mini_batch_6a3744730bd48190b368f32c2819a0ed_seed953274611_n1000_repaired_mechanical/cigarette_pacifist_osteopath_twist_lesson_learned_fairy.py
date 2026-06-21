#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cigarette_pacifist_osteopath_twist_lesson_learned_fairy.py
===========================================================================================

A tiny fairy-tale storyworld about a child, a pacifist warning, and an osteopath
who helps with the strain that follows a frightening little mistake.

Seed words: cigarette, pacifist, osteopath
Features: Twist, Lesson Learned
Style: Fairy Tale

The domain is deliberately small:
- A child in a fairy-tale village finds a cigarette.
- A pacifist friend urges calm and refuses harm.
- An osteopath can predict and treat body strain, soothed breath, and anxiety.
- The twist is that the cigarette is not lit; it is discovered, safely removed,
  and the "lesson learned" ending changes the child's behavior.

The story engine uses typed entities, physical meters, emotional memes, a causal
forward-chaining step, an explanation-aware reasonableness gate, and an inline
ASP twin for parity checks.
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "fairy"}
        male = {"boy", "father", "dad", "man", "prince", "knight"}
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
    place: str
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
class Item:
    id: str
    label: str
    phrase: str
    dangerous: bool = False
    touch_hurt: bool = False
    smoke_hurt: bool = False
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
class Helper:
    id: str
    label: str
    phrase: str
    helps_body: bool = False
    helps_truth: bool = False
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


def _r_smoke(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["smoke"] >= THRESHOLD and ("smoke" not in world.fired):
            pass
    for e in list(world.entities.values()):
        if e.meters["smoke"] < THRESHOLD:
            continue
        sig = ("smoke", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in list(world.entities.values()):
            if kid.role in {"child", "pacifist"}:
                kid.memes["fear"] += 1
        out.append("__smoke__")
    return out


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["fear"] < THRESHOLD:
            continue
        sig = ("tension", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("room").meters["tension"] += 1
        out.append("The room grew tense.")
    return out


CAUSAL_RULES = [Rule("smoke", _r_smoke), Rule("tension", _r_tension)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            if not s.startswith("__"):
                world.say(s)
    return out


def hazard(item: Item) -> bool:
    return item.dangerous


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def is_burned(item: Item, delay: int) -> bool:
    return item.touch_hurt and delay > 1


def predict(world: World, item_id: str) -> dict:
    sim = world.copy()
    sim.get(item_id).meters["smoke"] += 1
    propagate(sim, narrate=False)
    return {"fear": sum(e.memes["fear"] for e in sim.entities.values()), "tension": sim.get("room").meters["tension"]}


def setup(world: World, child: Entity, pacifist: Entity, helper: Entity, setting: Setting, item: Item) -> None:
    child.memes["curiosity"] += 1
    pacifist.memes["calm"] += 1
    world.say(
        f"Long ago, in {setting.place}, {child.id} and {pacifist.id} wandered under {setting.detail}."
    )
    world.say(
        f"They met {helper.phrase}, and beside the stone path lay {item.phrase}."
    )


def warn(world: World, pacifist: Entity, helper: Entity, item: Item) -> None:
    world.say(
        f'"No flames," said {pacifist.id}, for {pacifist.pronoun()} was a pacifist and never chose harm. '
        f'"That {item.label} is not a toy."'
    )
    prediction = predict(world, "cigarette")
    world.facts["predicted_fear"] = prediction["fear"]
    world.say(
        f'{helper.id} nodded and said, "I can help the body and the breath stay steady, but we must put it away."'
    )


def twist(world: World, child: Entity, item: Item) -> None:
    child.memes["surprise"] += 1
    world.say(
        f"{child.id} blinked. The tiny rolled thing looked like a magic straw, but it was only a cigarette, left behind by a careless traveler."
    )


def remove_item(world: World, helper: Entity, child: Entity, item: Item) -> None:
    item_m = world.get(item.id)
    item_m.meters["gone"] = 1
    world.say(
        f"{helper.id} wrapped it in a leaf and tucked it far from the path, where no child could reach it."
    )


def lesson(world: World, helper: Entity, child: Entity, item: Item, response: Response) -> None:
    child.memes["lesson"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{helper.id} rubbed {child.pronoun('possessive')} shoulders and showed how the body loosens when fear is breathed through and set down."
    )
    world.say(
        f'"{response.qa_text}," {helper.id} said, "and that is the kindest way to keep everyone safe."'
    )
    world.say(
        f"{child.id} promised to call a grown-up next time, and the path felt bright again."
    )


def safe_ending(world: World, setting: Setting, child: Entity, pacifist: Entity) -> None:
    world.say(
        f"At sunset, {setting.place} shimmered gold, and {child.id} walked home with a clear head and a gentler heart."
    )
    world.say(
        f"Beside {child.pronoun('object')}, {pacifist.id} smiled, happy that peace had won without a fight."
    )


def tell(setting: Setting, item: Item, response: Response,
         child_name: str = "Elsa", child_type: str = "girl",
         pacifist_name: str = "Milo", pacifist_type: str = "boy",
         helper_name: str = "Nessa", helper_type: str = "woman") -> World:
    world = World()
    room = world.add(Entity(id="room", kind="room", type="room", label="the room"))
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    pacifist = world.add(Entity(id=pacifist_name, kind="character", type=pacifist_type, role="pacifist"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    cig = world.add(Entity(id=item.id, kind="thing", type="thing", label=item.label))
    setup(world, child, pacifist, helper, setting, item)
    world.para()
    warn(world, pacifist, helper, item)
    twist(world, child, item)
    remove_item(world, helper, child, item)
    world.para()
    lesson(world, helper, child, item, response)
    safe_ending(world, setting, child, pacifist)
    world.facts.update(child=child, pacifist=pacifist, helper=helper, item=item, response=response, setting=setting, room=room)
    return world


SETTINGS = {
    "woods": Setting(id="woods", place="the moonlit woods", detail="the silver boughs of old trees"),
    "village": Setting(id="village", place="the little village", detail="golden lanterns on the cottages"),
}

ITEMS = {
    "cigarette": Item(id="cigarette", label="cigarette", phrase="a cigarette dropped beside the path", dangerous=True, touch_hurt=True, smoke_hurt=True, tags={"cigarette", "smoke"}),
}

RESPONSES = {
    "wash_hands": Response(id="wash_hands", sense=3, power=2, text="washed their hands and breathed slowly until the fear passed", fail="tried to calm the child, but the worry stayed too big", qa_text="washed their hands, breathed slowly, and calmed the fear", tags={"calm"}),
    "call_guard": Response(id="call_guard", sense=3, power=2, text="called the village guard and had the cigarette taken away safely", fail="called for help, but the guard came too late", qa_text="called the village guard and had it taken away safely", tags={"help"}),
    "heart_tea": Response(id="heart_tea", sense=2, power=2, text="made warm tea and spoke kindly until the child felt steady again", fail="made tea, but it was not enough to settle the fright", qa_text="made warm tea and spoke kindly until the child felt steady again", tags={"kindness"}),
}

@dataclass
class StoryParams:
    setting: str
    item: str
    response: str
    child_name: str = "Elsa"
    child_type: str = "girl"
    pacifist_name: str = "Milo"
    pacifist_type: str = "boy"
    helper_name: str = "Nessa"
    helper_type: str = "woman"
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


CURATED = [
    StoryParams(
        setting="woods",
        item="cigarette",
        response="wash_hands",
        child_name="Elsa",
        child_type="girl",
        pacifist_name="Milo",
        pacifist_type="boy",
        helper_name="Nessa",
        helper_type="woman",
        seed=1,
    ),
    StoryParams(
        setting="village",
        item="cigarette",
        response="call_guard",
        child_name="Ari",
        child_type="boy",
        pacifist_name="Lina",
        pacifist_type="girl",
        helper_name="Bran",
        helper_type="man",
        seed=2,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, i, r) for s in SETTINGS for i in ITEMS for r in sensible_responses_by_id()]


def sensible_responses_by_id() -> list[str]:
    return [r.id for r in sensible_responses()]


def explain_rejection(item: Item) -> str:
    return f"(No story: {item.label} is not a reasonable centerpiece.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: a cigarette is found, a pacifist warns, and an osteopath-like healer helps with the lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.item and args.item not in ITEMS:
        raise StoryError(explain_rejection(ITEMS["cigarette"]))
    setting = args.setting or rng.choice(list(SETTINGS))
    item = args.item or "cigarette"
    response = args.response or rng.choice(sensible_responses_by_id())
    if response not in RESPONSES:
        raise StoryError("(No story: unknown response.)")
    return StoryParams(
        setting=setting,
        item=item,
        response=response,
        child_name=rng.choice(["Elsa", "Ari", "Mina", "Oren"]),
        child_type=rng.choice(["girl", "boy"]),
        pacifist_name=rng.choice(["Milo", "Lina", "Tess"]),
        pacifist_type=rng.choice(["boy", "girl"]),
        helper_name=rng.choice(["Nessa", "Bran", "Iris"]),
        helper_type=rng.choice(["woman", "man"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.item not in ITEMS or params.response not in RESPONSES:
        raise StoryError("Invalid parameters.")
    world = tell(SETTINGS[params.setting], ITEMS[params.item], RESPONSES[params.response],
                 params.child_name, params.child_type, params.pacifist_name,
                 params.pacifist_type, params.helper_name, params.helper_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a fairy tale that includes the words "cigarette", "pacifist", and "osteopath", and ends with a lesson learned.',
        f'Tell a gentle fairy story where {world.facts["child"].id} finds a cigarette, a pacifist warns them, and a healer helps them choose peace.',
        f'Write a child-friendly fairy tale with a twist: a cigarette is found beside the path, but the ending teaches a calm lesson.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    c = world.facts["child"]
    p = world.facts["pacifist"]
    h = world.facts["helper"]
    response = world.facts["response"]
    return [
        ("Who is the story about?", f"It is about {c.id}, {p.id}, and {h.id}. They meet in a fairy-tale place and solve a small danger without violence."),
        ("What did the child find?", "The child found a cigarette beside the path. That was the twist, because the little rolled thing looked harmless at first but was not safe."),
        ("Who warned the child?", f"{p.id} warned the child. {p.id} was a pacifist, so {p.id} chose calm words instead of anger or harm."),
        ("How did the helper help?", f"{h.id} helped by staying steady and soothing the body and breath. {response.qa_text.capitalize()}."),
        ("How did the story end?", "It ended with a lesson learned: the child promised to call a grown-up and leave dangerous things alone. The path became calm again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a cigarette?", "A cigarette is a small rolled tobacco stick that makes smoke when it is lit. It is not safe for children to use."),
        ("What is a pacifist?", "A pacifist is someone who believes in peace and tries not to use violence."),
        ("What does an osteopath do?", "An osteopath helps people move more comfortably by working with the body gently. They can help with sore muscles, stiff backs, and other aches."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines += [f"{i+1}. {p}" for i, p in enumerate(sample.prompts)]
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: role={e.role} meters={dict((k,v) for k,v in e.meters.items() if v)} memes={dict((k,v) for k,v in e.memes.items() if v)}")
    return "\n".join(out)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S,I,R) :- setting(S), item(I), response(R), sensible(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


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
    import io
    from contextlib import redirect_stdout
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP parity.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


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
        print(f"sensible responses: {', '.join(asp_sensible())}")
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
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
        if len(samples) > 1:
            print(f"### variant {i+1}")
        emit(s, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
