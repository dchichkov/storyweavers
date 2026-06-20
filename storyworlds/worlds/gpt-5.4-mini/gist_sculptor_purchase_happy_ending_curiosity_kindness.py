#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gist_sculptor_purchase_happy_ending_curiosity_kindness.py
========================================================================================

A small, standalone story world for an adventure-flavored, child-friendly tale
about curiosity, kindness, a sculptor, and a purchase that helps things end
well.

Seed words:
- gist
- sculptor
- purchase

Story shape:
- A curious child or helper meets a sculptor.
- A needed purchase is made.
- Kindness changes the outcome.
- The ending is happy and concrete.

The world is intentionally small and classical: a few typed entities, physical
meters and emotional memes, a causal step or two, and a renderer that turns the
simulated state into prose.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/gist_sculptor_purchase_happy_ending_curiosity_kindness.py
    python storyworlds/worlds/gpt-5.4-mini/gist_sculptor_purchase_happy_ending_curiosity_kindness.py --all
    python storyworlds/worlds/gpt-5.4-mini/gist_sculptor_purchase_happy_ending_curiosity_kindness.py -n 5 --seed 777 --qa
    python storyworlds/worlds/gpt-5.4-mini/gist_sculptor_purchase_happy_ending_curiosity_kindness.py --verify
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
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
class Place:
    id: str
    label: str
    scene: str
    mood: str
    allows: set[str] = field(default_factory=set)

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
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    safe: bool = True

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
class PurchaseNeed:
    id: str
    item: str
    reason: str
    benefit: str
    kind: str

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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    sculptor = world.get("sculptor")
    need = world.facts["need"]
    if sculptor.meters["missing"] >= THRESHOLD and helper.memes["kindness"] >= THRESHOLD:
        sig = ("kindness",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        sculptor.memes["hope"] += 1
        helper.memes["joy"] += 1
        out.append(
            f"{helper.id} listened to the gist, and their kindness made the plan feel possible."
        )
    return out


def _r_purchase_complete(world: World) -> list[str]:
    out: list[str] = []
    buyer = world.get("helper")
    if world.facts.get("purchased"):
        return out
    if buyer.meters["coins"] >= 2:
        sig = ("purchase",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        buyer.meters["coins"] -= 2
        world.facts["purchased"] = True
        buyer.meters["purchase"] += 1
        out.append(
            f"{buyer.id} made the purchase and carried the needed item back through the market."
        )
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    sculptor = world.get("sculptor")
    helper = world.get("helper")
    need = world.facts["need"]
    if not world.facts.get("purchased"):
        return out
    if sculptor.meters["missing"] < THRESHOLD:
        return out
    sig = ("fix",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sculptor.meters["missing"] = 0
    sculptor.meters["steady"] += 1
    helper.memes["relief"] += 1
    out.append(
        f"With the new {need.item}, the sculptor could work again and the broken shape became whole."
    )
    return out


CAUSAL_RULES = [
    Rule("kindness", "social", _r_kindness),
    Rule("purchase", "physical", _r_purchase_complete),
    Rule("fix", "physical", _r_fix),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(need: PurchaseNeed, tool: Tool) -> bool:
    return need.kind == tool.id and tool.safe


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for need_id, need in NEEDS.items():
            for tool_id, tool in TOOLS.items():
                if reasonableness_gate(need, tool):
                    combos.append((place, need_id, tool_id))
    return combos


def story_intro(world: World, hero: Entity, sculptor: Entity, place: Place, need: PurchaseNeed) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["joy"] += 1
    sculptor.meters["missing"] += 1
    world.say(
        f"At {place.label}, {hero.id} found {sculptor.id}, a sculptor with a half-finished statue and a quiet worry."
    )
    world.say(
        f"{hero.id} was full of curiosity, so {hero.pronoun()} asked for the gist of the problem."
    )
    world.say(
        f"{sculptor.id} explained that the statue needed {need.item} before the final detail could be shaped."
    )


def seek_help(world: World, hero: Entity, helper: Entity, place: Place, need: PurchaseNeed) -> None:
    helper.memes["kindness"] += 1
    hero.memes["kindness"] += 1
    world.say(
        f"{helper.id} smiled kindly and said they could help with the purchase at the market."
    )
    world.say(
        f"That was the gist: buy {need.item}, return quickly, and keep the sculptor's work safe."
    )


def shopping(world: World, helper: Entity, need: PurchaseNeed, tool: Tool) -> None:
    helper.meters["coins"] = 2
    helper.meters["walking"] += 1
    world.say(
        f"So {helper.id} walked to the stall and made the purchase of {tool.phrase}."
    )
    world.say(
        f"The shopkeeper wrapped it up, and {helper.id} hurried back with a bright, helpful step."
    )


def resolve_scene(world: World, sculptor: Entity, helper: Entity, need: PurchaseNeed) -> None:
    world.para()
    propagate(world, narrate=True)
    if world.facts.get("purchased"):
        world.say(
            f"{sculptor.id} used the new {need.item}, and the statue's crack turned into a smooth line."
        )
        world.say(
            f"{helper.id} watched the finish emerge and felt proud that a kind purchase had saved the day."
        )
    else:
        raise StoryError("the story could not reach a happy ending")


def tell(place: Place, need: PurchaseNeed, tool: Tool,
         hero_name: str = "Mina", hero_gender: str = "girl",
         helper_name: str = "Ari", helper_gender: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="curious_child", traits=["curious"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="kind_helper", traits=["kind"]))
    sculptor = world.add(Entity(id="sculptor", kind="character", type="person", role="sculptor", traits=["patient"]))
    market = world.add(Entity(id="market", kind="place", type="place", label="the market"))
    hero.memes["curiosity"] = 1
    helper.memes["kindness"] = 1
    world.facts.update(place=place, need=need, tool=tool, hero=hero, helper=helper, sculptor=sculptor, market=market)

    world.say(
        f"One bright morning, {hero.id} and {helper.id} explored {place.label} like little adventurers."
    )
    story_intro(world, hero, sculptor, place, need)
    world.para()
    seek_help(world, hero, helper, place, need)
    shopping(world, helper, need, tool)
    world.para()
    sculptor.meters["missing"] += 1
    resolve_scene(world, sculptor, helper, need)
    return world


PLACES = {
    "square": Place("square", "the old town square", "a sunny square with stone paths", "open", {"polish", "clay"}),
    "museum": Place("museum", "the small museum courtyard", "a quiet courtyard with echoing arches", "careful", {"brush", "glaze"}),
    "harbor": Place("harbor", "the harbor steps", "stone steps beside a bright harbor", "adventurous", {"rope", "sealant"}),
}

NEEDS = {
    "brush": PurchaseNeed("brush", "a soft brush", "tiny dust kept falling from the statue", "it would smooth the edges", "brush"),
    "glaze": PurchaseNeed("glaze", "a jar of glaze", "the statue needed a shiny finish", "it would make the statue glow", "glaze"),
    "rope": PurchaseNeed("rope", "a coil of rope", "the sculptor needed a way to steady the statue", "it would hold things safely", "rope"),
    "sealant": PurchaseNeed("sealant", "a small tin of sealant", "the stone had a little crack from the sea air", "it would protect the crack", "sealant"),
    "polish": PurchaseNeed("polish", "a tin of polish", "the statue looked dull after a long week", "it would bring back the shine", "polish"),
    "clay": PurchaseNeed("clay", "a lump of clay", "a missing piece had to be filled in", "it would replace the missing shape", "clay"),
}

TOOLS = {
    "brush": Tool("brush", "a soft brush", "a soft brush with a wooden handle", "brush"),
    "glaze": Tool("glaze", "a jar of glaze", "a jar of warm gold glaze", "glaze"),
    "rope": Tool("rope", "a coil of rope", "a coil of strong rope", "rope"),
    "sealant": Tool("sealant", "a small tin of sealant", "a small tin of clear sealant", "sealant"),
    "polish": Tool("polish", "a tin of polish", "a tin of bright polish", "polish"),
    "clay": Tool("clay", "a lump of clay", "a lump of soft clay", "clay"),
}


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    sculptor: Entity = f["sculptor"]
    need: PurchaseNeed = f["need"]
    tool: Tool = f["tool"]
    place: Place = f["place"]
    return [
        ("Who was the story about?",
         f"It was about {hero.id}, {helper.id}, and {sculptor.id} the sculptor. They met at {place.label} on an adventure that began with curiosity."),
        ("What did {0} want to know?".format(hero.id),
         f"{hero.id} wanted the gist of why the sculptor looked worried. That curiosity led to a helpful trip to buy {need.item}."),
        ("What purchase was made?",
         f"They made the purchase of {tool.phrase}. The new item was exactly what the sculptor needed to finish the work."),
        ("How did kindness change the story?",
         f"{helper.id} listened kindly, offered help, and stayed gentle while solving the problem. That kindness turned the worry into a happy ending."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    need: PurchaseNeed = f["need"]
    place: Place = f["place"]
    return [
        f'Write an adventure story for a young child that includes the words "gist", "sculptor", and "purchase".',
        f"Tell a happy story where a curious child meets a sculptor at {place.label} and helps with a purchase.",
        f"Write a kindness-filled adventure about buying {need.item} so a sculptor can finish a statue.",
    ]


WORLD_KNOWLEDGE = {
    "curiosity": [("What is curiosity?",
                   "Curiosity is the desire to know more about something. It helps a person ask questions and learn new things.")],
    "kindness": [("What is kindness?",
                  "Kindness means being gentle, helpful, and caring to others. A kind action can make a hard moment feel better.")],
    "sculptor": [("What does a sculptor do?",
                  "A sculptor makes art by shaping stone, clay, wood, or other materials into a statue or figure.")],
    "purchase": [("What is a purchase?",
                  "A purchase is something you buy by giving money and receiving an item in return.")],
    "market": [("What is a market?",
                 "A market is a place where people sell things, and other people can buy what they need.")],
    "adventure": [("What is an adventure?",
                   "An adventure is an exciting story or trip where someone explores, solves problems, or discovers something new.")],
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"curiosity", "kindness", "sculptor", "purchase", "market", "adventure"}
    out: list[tuple[str, str]] = []
    for tag in tags:
        out.extend(WORLD_KNOWLEDGE[tag])
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
    lines.append("== (3) World knowledge ==")
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




def explain_rejection(need: PurchaseNeed, tool: Tool) -> str:
    if not reasonableness_gate(need, tool):
        return f"(No story: the needed item is {need.item}, but the chosen purchase does not fit that need.)"
    return "(No story: invalid combination.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: curiosity, kindness, sculptor, and purchase.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


@dataclass
class StoryParams:
    place: str
    need: str
    tool: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
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
    ("square", "brush", "brush"),
    ("museum", "glaze", "glaze"),
    ("harbor", "sealant", "sealant"),
    ("square", "polish", "polish"),
    ("museum", "clay", "clay"),
]



def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.need is None or c[1] == args.need)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, need_id, tool_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(["Mina", "Tari", "Lina", "Noa", "Bela", "Eli"])
    helper = args.helper or rng.choice(["Ari", "Sami", "Jude", "Moro", "Pia", "Nico"])
    return StoryParams(place, need_id, tool_id, hero, hero_gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], NEEDS[params.need], TOOLS[params.tool],
                 params.hero, params.hero_gender, params.helper, params.helper_gender)
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


ASP_RULES = r"""
valid(P, N, T) :- place(P), need(N), tool(T), fit(N, T).
happy :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for n in NEEDS:
        lines.append(asp.fact("need", n))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for n, need in NEEDS.items():
        lines.append(asp.fact("fit", n, need.kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, need=None, tool=None, hero=None, hero_gender=None, helper=None, helper_gender=None), random.Random(7)))
        assert sample.story
        print("OK: generate() smoke test produced a story.")
    except Exception as e:
        print(f"FAIL: generate() smoke test crashed: {e}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for place, need, tool in CURATED:
            params = StoryParams(place, need, tool, "Mina", "girl", "Ari", "boy")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
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
