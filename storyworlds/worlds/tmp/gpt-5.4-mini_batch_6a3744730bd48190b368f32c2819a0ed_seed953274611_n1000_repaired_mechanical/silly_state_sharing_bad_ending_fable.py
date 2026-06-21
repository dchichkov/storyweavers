#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/silly_state_sharing_bad_ending_fable.py
=======================================================================

A tiny fable-style storyworld about a silly act of sharing that changes state
and ends badly. The domain is small on purpose: a fox, a crow, and a greedy
neighbor each have food in a common clearing. One character chooses to share,
another takes too much, and the ending proves the world state has worsened.

The story includes the words "silly" and "state" and keeps the tone close to a
fable: concrete animals, a simple moral turn, and a bad ending image that shows
what changed.
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "crow", "wolf", "rabbit"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Food:
    id: str
    label: str
    phrase: str
    shareable: bool = True
    messy: bool = False
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
class Place:
    id: str
    label: str
    phrase: str
    quiet: str
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
class Action:
    id: str
    verb: str
    promise: str
    cost: int
    greed: int
    result_text: str
    fail_text: str
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
    place: str
    gift: str
    helper: str
    taker: str
    action: str
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


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    soup = world.entities.get("food")
    if not soup:
        return out
    if soup.meters["taken"] < THRESHOLD:
        return out
    sig = ("spoil", soup.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if "clearing" in world.entities:
        world.get("clearing").meters["quiet"] += 1
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["worry"] += 1
    out.append("__spoil__")
    return out


CAUSAL_RULES = [Rule("spoil", _r_spoil)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def reasonableness_gate(food: Food, action: Action) -> bool:
    return food.shareable and action.cost <= action.greed + 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for gift in FOODS:
            for helper in ANIMALS:
                for taker in ANIMALS:
                    if helper == taker:
                        continue
                    for action in ACTIONS:
                        if reasonableness_gate(FOODS[gift], ACTIONS[action]):
                            combos.append((place, gift, helper, taker, action))
    return combos


def predict_taken(world: World) -> bool:
    sim = world.copy()
    sim.get("food").meters["taken"] += 1
    propagate(sim, narrate=False)
    return sim.get("food").meters["taken"] >= THRESHOLD


def start_story(world: World, place: Place, helper: Entity, taker: Entity, food: Food) -> None:
    helper.memes["hope"] += 1
    taker.memes["want"] += 1
    world.say(
        f"At {place.phrase}, a fox named {helper.id} and a crow named {taker.id} "
        f"met beside a little table. On the table lay {food.phrase}."
    )
    world.say(
        f"The morning looked calm, and the two friends tried to keep a {place.quiet} "
        f"state while they decided what to do."
    )


def offer_share(world: World, helper: Entity, taker: Entity, food: Food, action: Action) -> None:
    helper.memes["kindness"] += 1
    world.say(
        f'{helper.id} smiled. "{action.promise}," {helper.id} said, and it sounded '
        f"silly but warm."
    )
    world.say(
        f"{helper.id} pushed the bowl forward, meaning to share. That was the first "
        f"step that changed the state of the clearing."
    )


def warn(world: World, helper: Entity, taker: Entity, food: Food) -> None:
    if predict_taken(world):
        world.say(
            f'{taker.id} blinked and said, "{helper.id}, if we take too much, there '
            f"will be less for the others.""
        )
    else:
        world.say(
            f'{taker.id} said, "{helper.id}, that is a kind offer, and there is enough '
            f"for a small share.""
        )


def take_too_much(world: World, taker: Entity, food: Food, action: Action) -> None:
    taker.memes["greed"] += 1
    food_ent = world.get("food")
    food_ent.meters["taken"] += action.greed
    world.say(
        f'But {taker.id} laughed, "This is too tasty to leave alone," and took '
        f"more than {action.verb} should have allowed."
    )


def bad_turn(world: World, food: Food) -> None:
    food_ent = world.get("food")
    food_ent.meters["broken"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The bowl tipped, the crumbs scattered, and the nice little pile was ruined."
    )
    world.say(
        f"What had been a sharing table became a messy patch on the ground."
    )


def lesson(world: World, helper: Entity, taker: Entity, place: Place, food: Food) -> None:
    helper.memes["sadness"] += 1
    taker.memes["shame"] += 1
    world.say(
        f"{helper.id} looked down and said, \"Sharing is sweet, but taking without "
        f"thought can spoil a whole state of peace.\""
    )
    world.say(
        f"{taker.id} hung {taker.pronoun('possessive')} head. The {place.label_word} was "
        f"quiet now, but not kindly quiet."
    )


def ending_image(world: World, place: Place, food: Food, helper: Entity, taker: Entity) -> None:
    world.say(
        f"By the end, the sun had moved, the crumbs were gone, and the table stood "
        f"empty in the {place.quiet} clearing."
    )
    world.say(
        f"{helper.id} had no good meal left to offer, and {taker.id} had learned too "
        f"late that a silly choice can leave a bad ending behind."
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES or params.gift not in FOODS or params.helper not in ANIMALS:
        raise StoryError("Unknown story parameters.")
    if params.taker not in ANIMALS or params.action not in ACTIONS:
        raise StoryError("Unknown story parameters.")

    food = FOODS[params.gift]
    action = ACTIONS[params.action]
    if not reasonableness_gate(food, action):
        raise StoryError("This combination does not produce a sensible sharing story.")

    world = World()
    place = PLACES[params.place]
    helper = world.add(Entity(id=params.helper, kind="character", type=ANIMALS[params.helper], role="helper"))
    taker = world.add(Entity(id=params.taker, kind="character", type=ANIMALS[params.taker], role="taker"))
    world.add(Entity(id="clearing", type="place", label=place.label))
    world.add(Entity(id="food", type="food", label=food.label))
    world.facts.update(place=place, food=food, helper=helper, taker=taker, action=action)

    start_story(world, place, helper, taker, food)
    world.para()
    offer_share(world, helper, taker, food, action)
    warn(world, helper, taker, food)
    take_too_much(world, taker, food, action)
    world.para()
    bad_turn(world, food)
    lesson(world, helper, taker, place, food)
    ending_image(world, place, food, helper, taker)
    return world


PLACES = {
    "orchard": Place(id="orchard", label="orchard", phrase="the orchard", quiet="sunlit", tags={"field"}),
    "meadow": Place(id="meadow", label="meadow", phrase="the meadow", quiet="grassy", tags={"field"}),
    "lane": Place(id="lane", label="lane", phrase="the dusty lane", quiet="small", tags={"path"}),
}

FOODS = {
    "berries": Food(id="berries", label="berries", phrase="a basket of berries", shareable=True, tags={"food"}),
    "bread": Food(id="bread", label="bread", phrase="a round loaf of bread", shareable=True, tags={"food"}),
    "honeycake": Food(id="honeycake", label="honeycake", phrase="a honeycake on a cloth", shareable=True, messy=True, tags={"food"}),
}

ANIMALS = {
    "fox": "fox",
    "crow": "crow",
    "hare": "rabbit",
    "wolf": "wolf",
}

ACTIONS = {
    "offer": Action(id="offer", verb="share", promise="we can share it gently", cost=1, greed=2,
                    result_text="shared it kindly", fail_text="shared it badly", tags={"share"}),
    "split": Action(id="split", verb="divide", promise="we can split it fairly", cost=1, greed=3,
                    result_text="split it fairly", fail_text="split it badly", tags={"share"}),
    "taste": Action(id="taste", verb="taste", promise="we can taste a little", cost=0, greed=1,
                    result_text="tasted a little", fail_text="tasted too much", tags={"share"}),
}

CURATED = [
    StoryParams(place="orchard", gift="berries", helper="fox", taker="crow", action="offer"),
    StoryParams(place="meadow", gift="bread", helper="fox", taker="hare", action="split"),
    StoryParams(place="lane", gift="honeycake", helper="crow", taker="wolf", action="taste"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny fable storyworld about sharing and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gift", choices=FOODS)
    ap.add_argument("--helper", choices=ANIMALS)
    ap.add_argument("--taker", choices=ANIMALS)
    ap.add_argument("--action", choices=ACTIONS)
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
              if (args.place is None or c[0] == args.place)
              and (args.gift is None or c[1] == args.gift)
              and (args.helper is None or c[2] == args.helper)
              and (args.taker is None or c[3] == args.taker)
              and (args.action is None or c[4] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, gift, helper, taker, action = rng.choice(sorted(combos))
    return StoryParams(place=place, gift=gift, helper=helper, taker=taker, action=action)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a child that uses the words "silly" and "state" and shows why sharing must be done wisely.',
        f"Tell a fable where a {f['helper'].type} named {f['helper'].id} tries to share {f['food'].phrase} with {f['taker'].id}, but the ending is bad.",
        f'Write a simple animal story about sharing, with a calm beginning and a bad ending that leaves the table empty.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    helper = f["helper"]
    taker = f["taker"]
    food = f["food"]
    place = f["place"]
    return [
        ("Who are the story about?",
         f"It is about {helper.id} and {taker.id} in the {place.label}. They meet beside food and try to decide how to share."),
        ("What was silly about the sharing?",
         f"{helper.id} tried to share kindly, but {taker.id} took too much. That silly choice changed the state from peaceful to messy."),
        ("Why was the ending bad?",
         f"The food got ruined and there was no good meal left. The sharing table ended in crumbs instead of kindness."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does sharing mean?",
         "Sharing means letting someone else have part of something you have. It is kind when it is done fairly."),
        ("What does state mean in a story?",
         "State means how things are at a certain time, like calm, messy, or empty. A story can show state changing."),
        ("Why is greed a problem?",
         "Greed is a strong wish to take too much. It can leave less for others and spoil a good moment."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
shareable(F) :- food(F).
bad_ending(F) :- taken_too_much(F), spoil(F).
sensible(A,F) :- action(A), food(F), shareable(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for fid in FOODS:
        lines.append(asp.fact("food", fid))
        lines.append(asp.fact("shareable", fid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show shareable/1."))
    clingo_set = set(asp.atoms(model, "shareable"))
    python_set = set((fid,) for fid in FOODS)
    rc = 0
    if clingo_set != python_set:
        print("MISMATCH in ASP parity.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    return rc


def valid_storyworld_combos() -> list[tuple[str, str, str, str, str]]:
    return valid_combos()


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.gift not in FOODS or params.helper not in ANIMALS:
        raise StoryError("Unknown story parameters.")
    if params.taker not in ANIMALS or params.action not in ACTIONS:
        raise StoryError("Unknown story parameters.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show shareable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} valid sharing combinations:\n")
        for combo in valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.helper} and {p.taker}: sharing in the {p.place} ({p.gift})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
