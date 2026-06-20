#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mutton_doze_sharing_curiosity_dialogue_slice_of.py
===================================================================================

A standalone storyworld for a small slice-of-life domain built from the seed words
"mutton" and "doze", with Sharing, Curiosity, and Dialogue as the core narrative
instruments.

Domain premise:
- A child is curious about a cozy meal.
- Someone is sharing a simple dish of mutton.
- A gentle misunderstanding or hesitation is resolved through dialogue.
- The ending lands in a calm domestic image, often with someone dozing after the
  warm meal.

The world is tiny on purpose: fewer plausible variants are better than a loose
generic food story. State drives the prose, and the story ends with a concrete
image proving what changed.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/mutton_doze_sharing_curiosity_dialogue_slice_of.py
    python storyworlds/worlds/gpt-5.4-mini/mutton_doze_sharing_curiosity_dialogue_slice_of.py --all
    python storyworlds/worlds/gpt-5.4-mini/mutton_doze_sharing_curiosity_dialogue_slice_of.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/mutton_doze_sharing_curiosity_dialogue_slice_of.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Food:
    id: str
    label: str
    phrase: str
    aroma: str
    warm: bool = True
    shareable: bool = True
    pairs: int = 2
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
class SharingAction:
    id: str
    method: str
    effect: str
    text: str
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
class Mood:
    id: str
    label: str
    change: str
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


def _r_shared(world: World) -> list[str]:
    out: list[str] = []
    table = world.entities.get("table")
    dish = world.entities.get("dish")
    if not table or not dish:
        return out
    if dish.meters["shared"] < THRESHOLD:
        return out
    sig = ("shared", dish.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    table.meters["warmth"] += 1
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["contentment"] += 1
    out.append("__warm__")
    return out


def _r_doze(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.kind != "character":
            continue
        if ent.memes["contentment"] < THRESHOLD:
            continue
        sig = ("doze", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["dozing"] += 1
        out.append("__doze__")
    return out


CAUSAL_RULES = [Rule("shared", "social", _r_shared), Rule("doze", "physical", _r_doze)]


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


def ask_to_share(world: World, child: Entity, adult: Entity, food: Food) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a slow afternoon, {child.id} noticed the smell of {food.label} drifting from the kitchen. "
        f"{child.id} peeked at the table and asked, \"What is that?\""
    )
    world.say(
        f"{adult.label_word.capitalize()} smiled. \"It is {food.phrase},\" {adult.pronoun()} said. "
        f"\"Would you like to share some with me?\""
    )


def hesitate(world: World, child: Entity, food: Food) -> None:
    child.memes["hesitation"] += 1
    world.say(
        f"{child.id} leaned closer, then glanced at the steaming bowl. "
        f"\"Mutton?\" {child.pronoun()} said softly. \"Is it spicy?\""
    )


def answer(world: World, adult: Entity, child: Entity, food: Food) -> None:
    adult.memes["patience"] += 1
    world.say(
        f"\"Just a little savory,\" {adult.label_word.capitalize()} said. "
        f"\"We can start with a small bite. If you do not like it, you do not have to finish it.\""
    )
    world.say(
        f"{child.id} nodded. \"Can I share your spoon?\" {child.pronoun()} asked."
    )


def share(world: World, child: Entity, adult: Entity, food: Food, method: SharingAction) -> None:
    dish = world.get("dish")
    child.memes["trust"] += 1
    dish.meters["shared"] += 1
    world.say(
        f"\"Yes,\" {adult.pronoun()} said, and {method.text.format(food=food.label)}"
    )


def soften(world: World, child: Entity, adult: Entity, food: Food, mood: Mood) -> None:
    child.memes["joy"] += 1
    adult.memes["joy"] += 1
    world.say(
        f"The room grew {mood.label}. The {food.label} tasted simple and good, and the worry in {child.id}'s face melted away."
    )


def doze(world: World, adult: Entity, child: Entity) -> None:
    propagate(world, narrate=False)
    if adult.meters["dozing"] >= THRESHOLD:
        world.say(
            f"After a while, {adult.id} leaned back in the chair and began to {adult.type == 'mother' and 'doze' or 'doze'}, "
            f"the kind of sleepy rest that comes after a warm meal and a quiet talk."
        )
    if child.meters["dozing"] >= THRESHOLD:
        world.say(
            f"{child.id} rubbed {child.pronoun('possessive')} eyes and yawned too."
        )


def tell(food: Food, method: SharingAction, mood: Mood,
         child_name: str = "Mina", child_gender: str = "girl",
         adult_name: str = "Aunt June", adult_gender: str = "aunt") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="curious child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="sharing adult"))
    table = world.add(Entity(id="table", type="place", label="the little table"))
    dish = world.add(Entity(id="dish", type="food", label=food.label))
    child.memes["curiosity"] = 1.0

    world.say(
        f"{child.id} was helping set the little table when {food.phrase} was brought out in a warm bowl."
    )
    world.say(
        f"{food.phrase.capitalize()} smelled {food.aroma}, and the steam curled up like a tiny cloud."
    )
    world.para()
    ask_to_share(world, child, adult, food)
    hesitate(world, child, food)
    answer(world, adult, child, food)
    share(world, child, adult, food, method)
    world.para()
    soften(world, child, adult, food, mood)
    world.say(
        f"The bowl was passed back and forth carefully, and the two of them kept chatting about ordinary things: school, rain, and the neighbor's cat."
    )
    doze(world, adult, child)
    world.say(
        f"When the plate was empty, the little table stayed warm, and {child.id} felt calm enough to lean against the chair and watch {adult.id} {('doze' if adult.type == 'aunt' else 'rest')} in the sunlight."
    )

    world.facts.update(
        child=child, adult=adult, table=table, dish=dish, food=food,
        method=method, mood=mood,
        shared=dish.meters["shared"] >= THRESHOLD,
        dozed=adult.meters["dozing"] >= THRESHOLD or child.meters["dozing"] >= THRESHOLD,
    )
    return world


FOODS = {
    "mutton": Food("mutton", "mutton stew", "a bowl of mutton stew", "rich and peppery", tags={"mutton"}),
    "mutton_pie": Food("mutton_pie", "mutton pie", "a mutton pie", "buttery and warm", tags={"mutton"}),
    "soup": Food("soup", "mutton soup", "a pot of mutton soup", "soft and savory", tags={"mutton"}),
}

SHARING = {
    "spoon": SharingAction("spoon", "spoon", "shared by spoon", "passed the spoon to {food}",
                           tags={"sharing", "dialogue"}),
    "bowl": SharingAction("bowl", "bowl", "shared from one bowl", "held out the bowl for a small taste of {food}",
                          tags={"sharing"}),
    "plate": SharingAction("plate", "plate", "shared on a plate", "broke off a little piece and set it on a plate",
                           tags={"sharing"}),
}

MOODS = {
    "sunny": Mood("sunny", "sunny", "bright and calm", tags={"slice_of_life"}),
    "quiet": Mood("quiet", "quiet", "soft and easy", tags={"slice_of_life"}),
    "cozy": Mood("cozy", "cozy", "warm and friendly", tags={"slice_of_life"}),
}


@dataclass
@dataclass
class StoryParams:
    food: str
    sharing: str
    mood: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(f, s, m) for f in FOODS for s in SHARING for m in MOODS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with mutton, sharing, curiosity, and dialogue.")
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--sharing", choices=SHARING)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["mother", "father", "aunt", "uncle"])
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
              if (args.food is None or c[0] == args.food)
              and (args.sharing is None or c[1] == args.sharing)
              and (args.mood is None or c[2] == args.mood)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    food, sharing, mood = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(["Mina", "Lena", "Toby", "Nico", "Sana", "Iris"])
    adult_gender = args.adult_gender or rng.choice(["aunt", "mother", "uncle", "father"])
    adult_name = args.adult or rng.choice(["Aunt June", "Mom", "Dad", "Uncle Ben", "Aunt Kim"])
    return StoryParams(food, sharing, mood, child_name, gender, adult_name, adult_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle slice-of-life story that includes the word "{f["food"].label}" and centers on sharing at a small table.',
        f"Tell a cozy story where {f['child'].id} is curious about {f['adult'].id}'s meal, asks questions, and learns to share a taste.",
        f'Write a simple dialogue-driven story with the words "mutton" and "doze" that ends in a calm, sleepy home image.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, adult, food = f["child"], f["adult"], f["food"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {adult.id}. The story follows a small moment at the table where curiosity turns into a shared meal."),
        (f"What did {child.id} want to know?", f"{child.id} wanted to know what was in the warm bowl and whether it would be spicy. That question opened the door to a calm conversation instead of a worry."),
        (f"How did they share the food?", f"They shared it {f['method'].method} so {child.id} could have a small taste first. That made the meal feel gentle and fair."),
        (f"What changed after they ate?", f"They felt content and the room turned cozy. The meal settled everyone down, and the quiet made it easy to doze."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is mutton?", "Mutton is meat from a sheep. People can cook it in stew, soup, or pie."),
        ("What does it mean to doze?", "To doze means to sleep lightly or nod off for a short time, usually when you feel warm and sleepy."),
        ("Why is sharing nice?", "Sharing lets more than one person enjoy the same thing. It can make people feel kind, included, and cared for."),
        ("What is curiosity?", "Curiosity is the wish to know more about something. It helps children ask questions and learn."),
        ("Why do people talk at the table?", "People often talk at the table because meals are a calm time to listen, ask questions, and spend time together."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("mutton", "spoon", "cozy", "Mina", "girl", "Aunt June", "aunt"),
    StoryParams("mutton_pie", "bowl", "quiet", "Toby", "boy", "Mom", "mother"),
    StoryParams("soup", "plate", "sunny", "Iris", "girl", "Dad", "father"),
]


ASP_RULES = r"""
shared(D) :- dish(D), shared_count(D, C), C >= 1.
dozing(P) :- person(P), contentment(P, C), C >= 1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for fid in FOODS:
        lines.append(asp.fact("food", fid))
    for sid in SHARING:
        lines.append(asp.fact("sharing", sid))
    for mid in MOODS:
        lines.append(asp.fact("mood", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show food/1."))
    _ = asp.atoms(model, "food")
    print("OK: ASP program loads.")
    cases = [resolve_params(argparse.Namespace(food=None, sharing=None, mood=None, name=None, gender=None, adult=None, adult_gender=None),
                            random.Random(7))]
    for p in cases:
        sample = generate(p)
        if not sample.story.strip():
            return 1
    print("OK: generate() smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(FOODS[params.food], SHARING[params.sharing], MOODS[params.mood],
                 params.child_name, params.child_gender, params.adult_name, params.adult_gender)
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
        print(asp_program("#show food/1.\n#show sharing/1.\n#show mood/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(sorted(FOODS)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
