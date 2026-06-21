#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/souvlaki_inner_monologue_folk_tale.py
======================================================================

A small folk-tale storyworld about a child, a warm souvlaki, and an inner
monologue that guides a careful choice.

Premise
-------
A child carries a souvlaki across a little village road on the way to a feast.
They are hungry and tempted to eat it alone, but their own inner voice reminds
them that the skewer is meant to be shared with a waiting elder or friend.
Along the way, a small mishap threatens the food; a helper or the child's own
care keeps the souvlaki safe; and the story ends with shared supper.

This world uses:
- typed entities with physical meters and emotional memes
- a forward-chained causal state model
- a Python reasonableness gate and inline ASP twin
- three QA sets grounded in simulated state
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
from typing import Optional

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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    road: bool
    dark: bool
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
class Food:
    id: str
    label: str
    phrase: str
    warmth: str
    shared: bool
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
class Trouble:
    id: str
    label: str
    slip: str
    mess: str
    risk: int
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
class Helper:
    id: str
    label: str
    action: str
    rescue: str
    power: int
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


def _r_hunger(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters["hunger"] >= THRESHOLD and (("hunger",) not in world.fired):
        world.fired.add(("hunger",))
        child.memes["temptation"] += 1
        out.append("__hunger__")
    return out


def _r_spill(world: World) -> list[str]:
    out = []
    child = world.get("child")
    snack = world.get("souvlaki")
    trouble = world.get("trouble")
    if child.meters["stumble"] >= THRESHOLD and snack.meters["carried"] >= THRESHOLD:
        sig = ("spill",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        snack.meters["dropped"] += 1
        trouble.meters["mess"] += 1
        child.memes["fear"] += 1
        out.append("__spill__")
    return out


CAUSAL_RULES = [_r_hunger, _r_spill]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True


def inner_voice(world: World, child: Entity, food: Food, helper: Optional[Entity]) -> None:
    child.memes["thoughtful"] += 1
    helper_part = f" and {helper.label_word} was waiting at home" if helper else ""
    world.say(
        f"{child.id} walked on, and in {child.pronoun('possessive')} own heart "
        f"{child.pronoun('subject')} thought, 'This souvlaki smells so good{helper_part}. "
        f'I must not gobble it all myself. I can bring it there warm and whole.'"
    )


def introduce(world: World, child: Entity, place: Place, food: Food) -> None:
    world.say(
        f"Once in a little village, {child.id} set out along {place.label} with "
        f"{food.phrase} wrapped in a cloth."
    )
    child.memes["joy"] += 1
    child.meters["hunger"] += 1
    world.say(
        f"{child.id} could smell the garlic and meat, and {child.pronoun('subject')} "
        f"felt both proud and hungry."
    )


def temptation(world: World, child: Entity, food: Food) -> None:
    world.say(
        f'"Just one bite," {child.id} whispered, then paused. '
        f"'{food.label} is for sharing, not for sneaking,' {child.id} told "
        f"{child.pronoun('object')}self."
    )
    child.memes["restraint"] += 1


def mishap(world: World, child: Entity, trouble: Trouble, food: Food) -> None:
    child.meters["stumble"] += 1
    propagate(world)
    if food.meters["dropped"] >= THRESHOLD:
        world.say(
            f"At the bend in the road, {trouble.slip} made the cloth twitch, and "
            f"the souvlaki nearly slipped from {child.pronoun('possessive')} hands."
        )
    else:
        world.say(
            f"At the bend in the road, {trouble.slip} made {child.id} wobble, but "
            f"{child.pronoun('subject').capitalize()} clutched the food tight."
        )


def rescue(world: World, child: Entity, helper: Entity, food: Food, trouble: Trouble) -> None:
    if helper is not None:
        world.say(
            f"Then {helper.id} came out with quick feet. {helper.pronoun().capitalize()} "
            f"{helper.action} and {helper.rescue}, while the child held still."
        )
    else:
        world.say(
            f"Then {child.id} took a slow breath, set the cloth right, and held "
            f"the souvlaki close until the danger passed."
        )
    food.meters["saved"] += 1
    trouble.meters["mess"] = 0
    child.memes["relief"] += 1


def feast(world: World, child: Entity, food: Food, helper: Optional[Entity]) -> None:
    child.memes["love"] += 1
    world.say(
        f"By the time the lamps shone in the yard, the souvlaki was still warm."
    )
    if helper is not None:
        world.say(
            f"{child.id} laid it on the wooden table, and {helper.id} smiled as "
            f"they shared it together."
        )
    else:
        world.say(
            f"{child.id} brought it home and shared it at the table, glad to have "
            f"kept the promise."
        )
    world.say(
        f"The child ate with happy hands, and the little village night felt kind."
    )


def tell(place: Place, food: Food, trouble: Trouble, helper: Optional[Helper],
         child_name: str = "Nikos", child_type: str = "boy",
         elder_name: str = "Yiayia", elder_type: str = "grandmother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder"))
    world.add(Entity(id="souvlaki", kind="thing", type="food", label=food.label))
    world.add(Entity(id="trouble", kind="thing", type="trouble", label=trouble.label))
    place_ent = world.add(Entity(id=place.id, kind="thing", type="place", label=place.label))

    child.attrs["home"] = elder_name
    child.attrs["road"] = place_ent.id

    introduce(world, child, place, food)
    world.para()
    inner_voice(world, child, food, elder)
    temptation(world, child, food)

    world.para()
    if place.dark:
        world.say(
            f"The road was dim, and a crooked stone waited in the path."
        )
    else:
        world.say(
            f"The road was bright, but one loose stone still lay where feet might miss it."
        )

    mishap(world, child, trouble, food)

    if helper is not None:
        rescue(world, child, world.add(Entity(id=helper.id, kind="character", type="woman" if helper.id == "neighbor" else "man", role="helper", label=helper.label)), food, trouble)
    else:
        rescue(world, child, None, food, trouble)  # type: ignore[arg-type]

    world.para()
    feast(world, child, food, world.get(helper.id) if helper is not None else elder)
    world.facts.update(
        child=child,
        elder=elder,
        place=place,
        food=food,
        trouble=trouble,
        helper=helper,
        outcome="shared",
    )
    return world


PLACES = {
    "village_road": Place(id="village_road", label="the village road", road=True, dark=True, tags={"road", "folk"}),
    "sunny_lane": Place(id="sunny_lane", label="the sunny lane", road=True, dark=False, tags={"road", "folk"}),
}

FOODS = {
    "souvlaki": Food(id="souvlaki", label="souvlaki", phrase="a warm souvlaki", warmth="warm", shared=True, tags={"souvlaki", "food"}),
    "bread": Food(id="bread", label="bread", phrase="a round loaf of bread", warmth="warm", shared=True, tags={"bread", "food"}),
}

TROUBLES = {
    "stone": Trouble(id="stone", label="a loose stone", slip="a loose stone rolled underfoot", mess="dust", risk=1, tags={"stone"}),
    "wind": Trouble(id="wind", label="a sudden wind", slip="a sudden wind tugged at the cloth", mess="dust", risk=1, tags={"wind"}),
}

HELPERS = {
    "neighbor": Helper(id="neighbor", label="the neighbor", action="caught the cloth before it fell", rescue="picked up the souvlaki and steadied the child", power=2, tags={"helper"}),
    "none": Helper(id="none", label="", action="", rescue="", power=0, tags=set()),
}


@dataclass
class StoryParams:
    place: str
    food: str
    trouble: str
    helper: str
    child_name: str = "Nikos"
    child_type: str = "boy"
    elder_name: str = "Yiayia"
    elder_type: str = "grandmother"
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
    StoryParams(place="village_road", food="souvlaki", trouble="stone", helper="neighbor", child_name="Nikos", child_type="boy", elder_name="Yiayia", elder_type="grandmother"),
    StoryParams(place="sunny_lane", food="souvlaki", trouble="wind", helper="none", child_name="Mara", child_type="girl", elder_name="Papou", elder_type="grandfather"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES:
        for f in FOODS:
            for t in TROUBLES:
                for h in HELPERS:
                    combos.append((p, f, t, h))
    return combos


def explain_rejection(_: str) -> str:
    return "(No story: this little world always has a safe folk-tale path.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld with inner monologue and souvlaki.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    food = args.food or rng.choice(list(FOODS))
    trouble = args.trouble or rng.choice(list(TROUBLES))
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, food=food, trouble=trouble, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a folk tale for a young child that includes the word \"{f['food'].label}\" and uses inner monologue.",
        f"Tell a gentle story where {f['child'].id} thinks carefully about sharing {f['food'].label} on a village road.",
        f"Write a warm folktale about a child carrying {f['food'].label} to an elder, with one small mishap and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    food = f["food"]
    elder = f["elder"]
    return [
        QAItem(
            question=f"Why did {child.id} keep going instead of eating the food alone?",
            answer=f"{child.id} listened to {child.pronoun('possessive')} own inner voice and remembered that {food.label} was meant to be shared. That thought helped {child.pronoun('object')} keep the food warm for {elder.id}.",
        ),
        QAItem(
            question="What happened when the road got tricky?",
            answer=f"A small slip threatened the souvlaki, but {child.id} held on and the helper or steady hands kept it from falling. The worry passed before the food was ruined.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with shared supper. The souvlaki reached the table warm and whole, and the child felt proud for listening to the kind little voice inside.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is souvlaki?",
            answer="Souvlaki is food on a skewer, often grilled and served warm. People share it at meals, which makes it a good feast food in a folk tale.",
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is a story that feels old, simple, and magical in its own gentle way. It often has a lesson, a small test, and a happy ending.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the voice a character hears in their own mind. It can help them think carefully and choose what is right.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(f"- {p}" for p in sample.prompts)
    parts.append("== story qa ==")
    parts.extend(f"Q: {q.question}\nA: {q.answer}" for q in sample.story_qa)
    parts.append("== world qa ==")
    parts.extend(f"Q: {q.question}\nA: {q.answer}" for q in sample.world_qa)
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes} attrs={e.attrs}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,F,T,H) :- place(P), food(F), trouble(T), helper(H).
outcome(shared) :- valid(P,F,T,H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for f in FOODS:
        lines.append(asp.fact("food", f))
    for t in TROUBLES:
        lines.append(asp.fact("trouble", t))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP gate differs from Python gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, food=None, trouble=None, helper=None), random.Random(0)))
        _ = sample.story
    except Exception as e:
        print(f"MISMATCH: generate smoke test failed: {e}")
        return 1
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample)
    if not buf.getvalue().strip():
        print("MISMATCH: emit smoke test produced no output.")
        rc = 1
    if rc == 0:
        print("OK: verify passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.food not in FOODS or params.trouble not in TROUBLES or params.helper not in HELPERS:
        raise StoryError("invalid parameters")
    helper = None if params.helper == "none" else HELPERS[params.helper]
    world = tell(
        PLACES[params.place],
        FOODS[params.food],
        TROUBLES[params.trouble],
        helper,
        child_name=params.child_name,
        child_type=params.child_type,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
    )
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
