#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/squirrel_tofu_quest_bravery_fairy_tale.py
=========================================================================

A small, standalone storyworld for a fairy-tale quest about a squirrel, tofu,
and a brave choice.

Domain premise
--------------
A little squirrel sets off on a quest to bring a humble tofu offering to a
sleepy castle or glade. The quest becomes tense when a gust, a stream, or a
noisy shortcut threatens the tofu. A brave helper or the squirrel's own brave
heart helps them choose a safer path, and the ending proves what changed: the
tofu is delivered, shared, or replaced with care, and the hero returns wiser.

This world is intentionally tiny and classical:
- typed entities with physical meters and emotional memes
- a forward-chained world model
- a reasonableness gate and inline ASP twin
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVE_MIN = 4.0


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
        female = {"girl", "mother", "mom", "woman", "queen", "princess"}
        male = {"boy", "father", "dad", "man", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "queen": "queen", "king": "king"}.get(self.type, self.type)



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
    mood: str
    path: str
    ending: str
    quest_lift: str
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
class Quest:
    id: str
    aim: str
    prize: str
    token: str
    route: str
    line: str
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
class Barrier:
    id: str
    label: str
    danger: str
    risk: int
    can_turn: bool = False
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
class Aid:
    id: str
    label: str
    method: str
    power: int
    calm: str
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _r_fear(world: World) -> list[str]:
    out = []
    squirrel = world.entities.get("squirrel")
    if squirrel and squirrel.meters["trouble"] >= THRESHOLD and ("fear", "trouble") not in world.fired:
        world.fired.add(("fear", "trouble"))
        squirrel.memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_bravery(world: World) -> list[str]:
    out = []
    squirrel = world.entities.get("squirrel")
    helper = world.entities.get("helper")
    if squirrel and helper and helper.memes["bravery"] >= BRAVE_MIN and ("bravery", helper.id) not in world.fired:
        world.fired.add(("bravery", helper.id))
        squirrel.memes["hope"] += 1
        out.append("__hope__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("bravery", _r_bravery)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def barrier_at_risk(quest: Quest, barrier: Barrier) -> bool:
    return quest.token in barrier.danger or barrier.can_turn


def sensible_aid(aid: Aid, barrier: Barrier) -> bool:
    return aid.power >= barrier.risk


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for qid in QUESTS:
            for bid in BARRIERS:
                if barrier_at_risk(QUESTS[qid], BARRIERS[bid]):
                    combos.append((sid, qid, bid))
    return combos


def _pick_name(rng: random.Random, pool: list[str]) -> str:
    return rng.choice(pool)


def predict(world: World, barrier_id: str) -> dict:
    sim = world.copy()
    _do_barrier(sim, sim.get("squirrel"), BARRIERS[barrier_id], narrate=False)
    return {"trouble": sim.get("squirrel").meters["trouble"], "safeguard": sim.get("squirrel").memes["hope"]}


def _do_barrier(world: World, squirrel: Entity, barrier: Barrier, narrate: bool = True) -> None:
    squirrel.meters["trouble"] += 1
    if barrier.risk > 1:
        squirrel.memes["worry"] += 1
    propagate(world, narrate=narrate)


def begin(world: World, squirrel: Entity, setting: Setting, quest: Quest) -> None:
    squirrel.memes["joy"] += 1
    world.say(
        f"Once upon a soft morning, {squirrel.id} the squirrel wandered from {setting.place}, "
        f"where {setting.mood} songs floated through the trees."
    )
    world.say(
        f"{squirrel.id} had a quest: to bring {quest.prize} to {quest.aim}, following {quest.route} and the old fairy-tale line, '{quest.line}'"
    )


def tempter(world: World, squirrel: Entity, barrier: Barrier) -> None:
    squirrel.memes["curiosity"] += 1
    world.say(
        f"Along the way, a tempting {barrier.label} waited. It promised a faster path, but it also sounded risky and wild."
    )


def warn(world: World, helper: Entity, squirrel: Entity, barrier: Barrier) -> None:
    pred = predict(world, barrier.id)
    helper.memes["bravery"] += 1
    world.facts["predicted_trouble"] = pred["trouble"]
    world.say(
        f"{helper.id} stepped from the brambles and said, '{squirrel.id}, that path may bring trouble. Brave hearts choose wisely, not quickly.'"
    )


def choose(world: World, squirrel: Entity, helper: Entity, barrier: Barrier) -> bool:
    if helper.memes["bravery"] >= BRAVE_MIN and helper.attrs.get("older", False):
        squirrel.memes["trust"] += 1
        world.say(
            f"{squirrel.id} listened, held the little bundle tight, and chose the safer lane through the ferns."
        )
        return True
    squirrel.memes["defiance"] += 1
    world.say(
        f"{squirrel.id} shook a tiny paw and leapt toward the shortcut anyway."
    )
    return False


def scurry(world: World, squirrel: Entity, barrier: Barrier) -> None:
    _do_barrier(world, squirrel, barrier)
    world.say(
        f"A snag of wind sent the bundle tumbling. The {barrier.label} stirred the journey into a messy little danger."
    )


def rescue(world: World, helper: Entity, aid: Aid, barrier: Barrier) -> bool:
    squirrel = world.get("squirrel")
    if aid.power >= barrier.risk:
        squirrel.meters["trouble"] = 0
        squirrel.memes["relief"] += 1
        world.say(
            f"{helper.id} used {aid.label} in a calm, steady way, and {aid.calm} until the trouble was gone."
        )
        return True
    squirrel.meters["trouble"] += 1
    world.say(
        f"{helper.id} tried {aid.label}, but the mishap was too big for that small help."
    )
    return False


def ending(world: World, squirrel: Entity, setting: Setting, quest: Quest, aid: Aid, success: bool) -> None:
    if success:
        squirrel.memes["joy"] += 1
        world.say(
            f"At last, {squirrel.id} reached {quest.aim}, where the tofu was welcomed like moon-bright treasure."
        )
        world.say(
            f"Then the squirrel returned home through {setting.ending}, brave enough to remember the lesson and gentle enough to share the tofu feast."
        )
    else:
        squirrel.memes["sadness"] += 1
        world.say(
            f"At last, the squirrel still reached home, but the quest ended with a tired heart and a lesson about choosing stronger help next time."
        )


def tell(setting: Setting, quest: Quest, barrier: Barrier, aid: Aid, squirrel_name: str = "Squirrel", helper_name: str = "Fairy", squirrel_type: str = "squirrel", helper_type: str = "fairy") -> World:
    world = World()
    squirrel = world.add(Entity(id=squirrel_name, kind="character", type=squirrel_type, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", attrs={"older": True}))
    world.add(Entity(id="path", type="path", label=setting.place))
    world.add(Entity(id="tofu", type="thing", label="tofu"))
    squirrel.memes["bravery"] = 3.0
    helper.memes["bravery"] = 5.0

    begin(world, squirrel, setting, quest)
    world.para()
    tempter(world, squirrel, barrier)
    warn(world, helper, squirrel, barrier)
    choose(world, squirrel, helper, barrier)
    world.para()
    scurry(world, squirrel, barrier)
    success = rescue(world, helper, aid, barrier)
    world.para()
    ending(world, squirrel, setting, quest, aid, success)

    world.facts.update(
        squirrel=squirrel,
        helper=helper,
        setting=setting,
        quest=quest,
        barrier=barrier,
        aid=aid,
        success=success,
    )
    return world


SETTINGS = {
    "forest": Setting("forest", "an emerald forest", "birdsong", "the mossy path", "the silver lane home", "carry the tofu with care", tags={"forest"}),
    "glade": Setting("glade", "a moonlit glade", "soft lantern light", "the fern path", "the moonlit lane home", "carry the tofu with care", tags={"glade"}),
    "castle": Setting("castle", "a sleeping castle", "distant bells", "the ivy path", "the winding lane home", "carry the tofu with care", tags={"castle"}),
}

QUESTS = {
    "gift": Quest("gift", "the sleepy queen", "tofu", "the tofu parcel", "the stone bridge", "for the good of the realm", tags={"quest", "tofu"}),
    "feast": Quest("feast", "the hungry village", "tofu", "the tofu dish", "the river trail", "for a kindly feast", tags={"quest", "tofu"}),
    "spirit": Quest("spirit", "the lantern spirits", "tofu", "the tofu offering", "the moon path", "for a blessing", tags={"quest", "tofu"}),
}

BARRIERS = {
    "wind": Barrier("wind", "whirling wind", "tossing the tofu", 2, False, tags={"wind"}),
    "brook": Barrier("brook", "swift brook", "soaking the tofu", 3, False, tags={"brook"}),
    "bramble": Barrier("bramble", "thorny bramble", "tearing the tofu wrap", 1, True, tags={"bramble"}),
}

AIDS = {
    "basket": Aid("basket", "a woven basket", "tied the bundle snug and steady", 3, "kept the tofu safe", tags={"basket"}),
    "cloak": Aid("cloak", "a velvet cloak", "wrapped the parcel against the wind", 2, "held the tofu close", tags={"cloak"}),
    "stepstones": Aid("stepstones", "kind step-stones", "helped cross the brook slowly", 4, "made the crossing safe", tags={"steps"}),
}

SQUIRREL_NAMES = ["Pip", "Nell", "Rowan", "Toby", "Mina", "Syl", "Brin"]
FAIRY_NAMES = ["Merry", "Luna", "Elin", "Faye", "Thistle"]
TRAITS = ["brave", "curious", "gentle", "quick", "careful"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    quest: str
    barrier: str
    aid: str
    squirrel_name: str
    squirrel_type: str
    helper_name: str
    helper_type: str
    trait: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale quest world: squirrel, tofu, bravery, and a safer path.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--barrier", choices=BARRIERS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.aid and args.barrier and not sensible_aid(AIDS[args.aid], BARRIERS[args.barrier]):
        raise StoryError("The chosen aid is too small for that barrier.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.barrier is None or c[2] == args.barrier)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, barrier = rng.choice(sorted(combos))
    aid = args.aid or rng.choice(sorted(AIDS))
    squirrel_name = args.name or rng.choice(SQUIRREL_NAMES)
    helper_name = args.helper or rng.choice(FAIRY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(setting, quest, barrier, aid, squirrel_name, "squirrel", helper_name, "fairy", trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale quest story for a young child that includes the words "squirrel" and "tofu".',
        f"Tell a brave squirrel quest with a helpful fairy, a risky shortcut, and a gentle ending in {f['setting'].place}.",
        f"Write a story where {f['squirrel'].id} carries tofu on a quest and learns bravery by choosing the safer path.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    squirrel = f["squirrel"]
    helper = f["helper"]
    quest = f["quest"]
    barrier = f["barrier"]
    aid = f["aid"]
    qs = [
        QAItem(
            question="Who goes on the quest?",
            answer=f"{squirrel.id} the squirrel goes on the quest, and {helper.id} the fairy helps along the way.",
        ),
        QAItem(
            question="What does the squirrel carry?",
            answer="The squirrel carries tofu as a little quest offering. It is treated like something precious and worth protecting.",
        ),
        QAItem(
            question="Why does the helper warn about the shortcut?",
            answer=f"{helper.id} warns because the {barrier.label} could cause trouble for the tofu. Brave helpers notice danger early and choose the safer path.",
        ),
    ]
    if f["success"]:
        qs.append(QAItem(
            question="How was the problem solved?",
            answer=f"They used {aid.label} and that was strong enough to keep the tofu safe. The help matched the danger, so the quest could end well.",
        ))
        qs.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with the squirrel bringing tofu safely to {quest.aim}. The ending shows bravery as careful choosing, not noisy rushing.",
        ))
    else:
        qs.append(QAItem(
            question="How did the story end?",
            answer="It ended sadly, with the quest needing stronger help next time. Even so, the squirrel stayed safe and learned from the mistake.",
        ))
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags) | set(world.facts["barrier"].tags) | set(world.facts["aid"].tags)
    out = []
    if "quest" in tags:
        out.append(QAItem("What is a quest?", "A quest is a journey or mission to do something important. In fairy tales, it often means going somewhere brave and hard."))
    if "tofu" in tags:
        out.append(QAItem("What is tofu?", "Tofu is a soft food made from soybeans. People can cook it in many ways, and it can be carried carefully in a story."))
    if "bramble" in tags:
        out.append(QAItem("What is a bramble?", "A bramble is a patch of thorny plants. It can scratch cloth and make a path harder to cross."))
    if "wind" in tags:
        out.append(QAItem("What can wind do to a bundle?", "Wind can tug, shake, and topple a bundle if it is not tied down well."))
    if "brook" in tags:
        out.append(QAItem("What is a brook?", "A brook is a small, flowing stream of water. It can make things wet if they are not protected."))
    if "basket" in tags:
        out.append(QAItem("What does a basket help with?", "A basket helps keep things snug and steady so they do not tumble about."))
    if "cloak" in tags:
        out.append(QAItem("What does a cloak do in a windy tale?", "A cloak can wrap around a parcel and shield it from gusts."))
    if "steps" in tags:
        out.append(QAItem("What are step-stones for?", "Step-stones help someone cross water one careful step at a time."))
    return out


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for bid, b in BARRIERS.items():
        lines.append(asp.fact("barrier", bid))
        lines.append(asp.fact("risk", bid, b.risk))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        lines.append(asp.fact("power", aid, a.power))
    lines.append(asp.fact("brave_min", BRAVE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, Q, B) :- setting(S), quest(Q), barrier(B), barrier(B).
sensible(A, B) :- aid(A), barrier(B), power(A, P), risk(B, R), P >= R.
outcome(success) :- chosen_aid(A), chosen_barrier(B), sensible(A, B).
outcome(fail) :- chosen_aid(A), chosen_barrier(B), not sensible(A, B).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_aid", params.aid), asp.fact("chosen_barrier", params.barrier)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    try:
        generate(CURATED[0])
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    for p in CURATED:
        if asp_outcome(p) != ("success" if sensible_aid(AIDS[p.aid], BARRIERS[p.barrier]) else "fail"):
            rc = 1
            print("MISMATCH in outcome:", p)
            break
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], BARRIERS[params.barrier], AIDS[params.aid], params.squirrel_name, params.helper_name, params.squirrel_type, params.helper_type)
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


CURATED = [
    StoryParams("forest", "gift", "bramble", "basket", "Pip", "squirrel", "Merry", "fairy", "brave"),
    StoryParams("glade", "feast", "wind", "cloak", "Nell", "squirrel", "Luna", "fairy", "careful"),
    StoryParams("castle", "spirit", "brook", "stepstones", "Rowan", "squirrel", "Elin", "fairy", "gentle"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations.")
    filtered = [c for c in combos if (args.setting is None or c[0] == args.setting) and (args.quest is None or c[1] == args.quest) and (args.barrier is None or c[2] == args.barrier)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, barrier = rng.choice(sorted(filtered))
    aid = args.aid or rng.choice(sorted(AIDS))
    if not sensible_aid(AIDS[aid], BARRIERS[barrier]):
        aid = next(k for k, v in AIDS.items() if sensible_aid(v, BARRIERS[barrier]))
    return StoryParams(setting, quest, barrier, aid, args.name or rng.choice(SQUIRREL_NAMES), "squirrel", args.helper or rng.choice(FAIRY_NAMES), "fairy", rng.choice(TRAITS))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for qid in QUESTS:
            for bid, b in BARRIERS.items():
                if b.can_turn or b.risk >= 1:
                    combos.append((sid, qid, bid))
    return combos


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("", "#show valid/3."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
