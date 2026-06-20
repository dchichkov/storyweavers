#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/threesome_european_marigold_bad_ending_fairy_tale.py
====================================================================================

A small fairy-tale storyworld about three children in a European village, a
golden marigold bed, and a bad ending caused by a selfish wish.

The domain stays tiny and classical:
- a threesome of children exploring a garden behind a cottage,
- a magical marigold that grants only one wish,
- a warning from the wisest child,
- a greedy choice that ruins the flowers and leaves the village sorry.

The world is intentionally constrained so it can generate complete, child-facing
stories with a clear beginning, middle turn, and ending image proving what
changed. It also includes QA and a lightweight ASP twin for parity checks.
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
SENSE_MIN = 2
BRAVERY_INIT = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "maid", "princess"}
        male = {"boy", "father", "dad", "man", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "queen": "queen", "king": "king"}.get(self.type, self.type)



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
    phrase: str
    weather: str

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
class Wish:
    id: str
    wish_text: str
    greedy: bool
    power: int

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
class Flower:
    id: str
    label: str
    phrase: str
    bloom: str
    fragile: bool = True
    glowing: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

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


def _r_wilt(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["stolen"] < THRESHOLD:
            continue
        sig = ("wilt", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "garden" in world.entities:
            world.get("garden").meters["trouble"] += 1
        for c in world.characters():
            c.memes["regret"] += 1
        out.append("__wilt__")
    return out


CAUSAL_RULES = [Rule("wilt", "physical", _r_wilt)]


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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def hazard_at_risk(wish: Wish, flower: Flower) -> bool:
    return wish.greedy and flower.fragile


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for wid, wish in WISHES.items():
            for fid, flower in FLOWERS.items():
                if hazard_at_risk(wish, flower):
                    combos.append((setting, wid, fid))
    return combos


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def outcome_of(params: "StoryParams") -> str:
    return "burned" if RESPONSES[params.response].power < FLOWERS[params.flower].meters.get("severity", 2) else "contained"


def predict(world: World, flower_id: str) -> dict:
    sim = world.copy()
    _take_wish(sim, sim.get("wish"), sim.get(flower_id), narrate=False)
    return {"stolen": sim.get(flower_id).meters["stolen"] >= THRESHOLD, "trouble": sim.get("garden").meters["trouble"]}


def _take_wish(world: World, wish_ent: Entity, flower_ent: Entity, narrate: bool = True) -> None:
    flower_ent.meters["stolen"] += 1
    flower_ent.meters["faded"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, a: Entity, b: Entity, c: Entity, setting: Setting) -> None:
    for kid in (a, b, c):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright morning in {setting.place}, {a.id}, {b.id}, and {c.id} walked together through {setting.phrase}."
    )
    world.say(
        f"They were a little threesome, and the lane smelled of bread, rain, and summer leaves."
    )


def find_flower(world: World, flower: Flower, setting: Setting) -> None:
    world.say(
        f"Behind the cottage, they found {flower.phrase}, glowing like small suns in the green bed."
    )
    world.say(
        f"The marigolds looked too lovely to pick, and yet one of them shone brighter than the rest."
    )


def wish_offer(world: World, greedy: Entity, wish: Wish) -> None:
    greedy.memes["greed"] += 1
    world.say(
        f'{greedy.id} pointed at the brightest bloom and whispered, "I know a better use for that marigold. {wish.wish_text}"'
    )


def warn(world: World, careful: Entity, greedy: Entity, flower: Flower) -> None:
    careful.memes["caution"] += 1
    world.say(
        f'{careful.id} frowned and said, "{greedy.id}, the marigold belongs here. If you pluck it for yourself, the whole bed may wilt."'
    )


def defy(world: World, greedy: Entity, flower: Flower, wish: Wish) -> None:
    greedy.memes["defiance"] += 1
    world.say(
        f'But {greedy.id} did not listen. With one quick pull, {greedy.id} took the marigold from the stem and held it up to the sun.'
    )
    world.say(
        f'For a moment the flower seemed to glow harder, as if it were listening to {greedy.id}\'s wish.'
    )


def invoke(world: World, flower: Flower, wish: Wish) -> None:
    _take_wish(world, world.get("wish"), world.get(flower.id))
    world.say(
        f"Then the wish came true just enough to cause trouble: {wish.wish_text}."
    )
    world.say(
        f"The marigold's golden petals curled, and a soft shadow spread through the bed."
    )


def rescue_fail(world: World, response: Response, flower: Flower) -> None:
    flower.meters["severity"] = float(response.power)
    world.get("garden").meters["trouble"] += 2
    body = response.fail.replace("{target}", flower.label)
    world.say(f"Someone ran to help, but {body}.")
    world.say(
        f"The marigold bed lost its shine, and the stems sagged like tired little heads."
    )


def ending_bad(world: World, a: Entity, b: Entity, c: Entity, setting: Setting, flower: Flower, wish: Wish) -> None:
    for kid in (a, b, c):
        kid.memes["regret"] += 1
    world.say(
        f"By sunset, the whole garden was quiet. The brightest marigold was gone, and the rest stood bent and dull."
    )
    world.say(
        f"{a.id}, {b.id}, and {c.id} had the same thought at once: some beautiful things should never be taken for selfish wishes."
    )


SETTINGS = {
    "european_village": Setting("european_village", "a little European village", "the herb path behind the cottage", "soft"),
    "cottage_garden": Setting("cottage_garden", "the cottage garden", "the rose hedge and the old stone wall", "clear"),
    "market_lane": Setting("market_lane", "the market lane", "the quiet lane by the baker's door", "warm"),
}

WISHES = {
    "crown": Wish("crown", "I wish I had a gold crown as bright as the sun.", True, 1),
    "coin": Wish("coin", "I wish this marigold would turn into gold coins.", True, 1),
    "music": Wish("music", "I wish the flower would sing just for me.", False, 2),
}

FLOWERS = {
    "marigold": Flower("marigold", "marigold", "a tall marigold with a honey-gold face", "glowing"),
    "bed": Flower("bed", "flower bed", "the whole marigold bed", "glowing"),
}

RESPONSES = {
    "too_late": Response("too_late", 3, 1, "called for the gardener, but the damage was already done", "called for the gardener, but the damage was already done", "called for the gardener"),
    "pull_back": Response("pull_back", 2, 2, "pulled at the stem and tried to press the bloom back into place", "pulled at the stem and tried to press the bloom back into place", "pulled the flower back into place"),
    "water_pail": Response("water_pail", 1, 1, "fetched a pail of water and splashed it over the bed", "fetched a pail of water and splashed it over the bed, but it only made the petals droop faster", "fetched a pail of water"),
}

KID_NAMES = ["Anna", "Mira", "Elsa", "Jon", "Theo", "Lena", "Pavel", "Sofia", "Nina", "Mila"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    wish: str
    flower: str
    response: str
    a: str
    b: str
    c: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: threesome, marigold, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--wish", choices=WISHES)
    ap.add_argument("--flower", choices=FLOWERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--name3")
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
    if args.wish and args.flower:
        if not hazard_at_risk(WISHES[args.wish], FLOWERS[args.flower]):
            raise StoryError("(No story: this wish is not selfish enough to spoil the marigold tale.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.wish is None or c[1] == args.wish)
              and (args.flower is None or c[2] == args.flower)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, wish, flower = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    names = [args.name1, args.name2, args.name3]
    picked = []
    pool = KID_NAMES[:]
    rng.shuffle(pool)
    for i, nm in enumerate(names):
        picked.append(nm or pool[i])
    return StoryParams(setting, wish, flower, response, picked[0], picked[1], picked[2])


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    wish = WISHES[params.wish]
    flower = FLOWERS[params.flower]
    response = RESPONSES[params.response]

    a = world.add(Entity(id=params.a, kind="character", type="girl", role="greedy", traits=["bright"]))
    b = world.add(Entity(id=params.b, kind="character", type="boy", role="careful", traits=["careful"]))
    c = world.add(Entity(id=params.c, kind="character", type="girl", role="witness", traits=["gentle"]))
    garden = world.add(Entity(id="garden", kind="thing", type="garden", label="the garden"))
    world.add(Entity(id="wish", kind="thing", type="wish", label=wish.id))
    m = world.add(Entity(id=flower.id, kind="thing", type="flower", label=flower.label))
    world.facts["flower"] = flower
    world.facts["wish"] = wish

    setup(world, a, b, c, setting)
    find_flower(world, flower, setting)
    world.para()
    wish_offer(world, a, wish)
    warn(world, b, a, flower)
    defy(world, a, flower, wish)
    invoke(world, flower, wish)
    world.para()
    rescue_fail(world, response, flower)
    ending_bad(world, a, b, c, setting, flower, wish)

    world.facts.update(a=a, b=b, c=c, setting=setting, response=response, garden=garden, flower_ent=m, outcome="burned")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a fairy tale for a preschooler that includes the words "threesome" and "marigold".',
        f"Tell a small European fairy tale where {f['a'].id}, {f['b'].id}, and {f['c'].id} find a glowing marigold and make a greedy wish.",
        "Write a cautionary fairy tale with flowers, a warning, and a sad ending where selfishness spoils the magic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, c = f["a"], f["b"], f["c"]
    flower: Flower = f["flower"]
    wish: Wish = f["wish"]
    return [
        QAItem(question="Who is the story about?", answer=f"It is about a threesome of children: {a.id}, {b.id}, and {c.id}. They wandered through a little European village garden together."),
        QAItem(question="What did they find in the garden?", answer=f"They found a marigold, a bright flower with a honey-gold face. It looked magical because it glowed in the garden bed."),
        QAItem(question=f"What did {a.id} want to do?", answer=f"{a.id} wanted to use the marigold for a selfish wish: {wish.wish_text} That choice mattered because the flower was fragile and meant to be left in the bed."),
        QAItem(question=f"Why did {b.id} warn {a.id}?", answer=f"{b.id} warned {a.id} because plucking the marigold could spoil the whole bed. The warning was sensible, but {a.id} did not listen."),
        QAItem(question="How did the story end?", answer="It ended badly. The marigold bed lost its shine, the petals curled, and the garden became quiet and sad."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a marigold?", answer="A marigold is a flower with bright yellow or orange petals. People often grow them in gardens because they look sunny and cheerful."),
        QAItem(question="What does the word threesome mean?", answer="A threesome means a group of three. In a story, it can mean three children going together on the same adventure."),
        QAItem(question="What is a fairy tale?", answer="A fairy tale is a make-believe story with simple heroes, magical events, and a clear lesson. It often ends with a strong feeling of good or bad change."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions ==",]
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("european_village", "coin", "marigold", "too_late", "Anya", "Borin", "Clara"),
    StoryParams("cottage_garden", "crown", "marigold", "pull_back", "Lina", "Marek", "Sofia"),
    StoryParams("market_lane", "coin", "bed", "water_pail", "Eva", "Tomas", "Nora"),
]


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for wid, w in WISHES.items():
        lines.append(asp.fact("wish", wid))
        if w.greedy:
            lines.append(asp.fact("greedy", wid))
    for fid in FLOWERS:
        lines.append(asp.fact("flower", fid))
        lines.append(asp.fact("fragile", fid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(W, F) :- greedy(W), fragile(F).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, W, F) :- setting(S), wish(W), flower(F), greedy(W), fragile(F).
outcome(burned) :- chosen_response(R), chosen_wish(W), chosen_flower(F), power(R, P), severity(F, V), P < V.
outcome(contained) :- chosen_response(R), chosen_wish(W), chosen_flower(F), power(R, P), severity(F, V), P >= V.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scen = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("chosen_wish", params.wish),
        asp.fact("chosen_flower", params.flower),
        asp.fact("severity", params.flower, 2),
    ])
    model = asp.one_model(asp_program(scen, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"FAIL: generate smoke test crashed: {e}")
    return rc


def build_sample(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, wish, flower) combos:\n")
        for s, w, f in combos:
            print(f"  {s:18} {w:8} {f}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
