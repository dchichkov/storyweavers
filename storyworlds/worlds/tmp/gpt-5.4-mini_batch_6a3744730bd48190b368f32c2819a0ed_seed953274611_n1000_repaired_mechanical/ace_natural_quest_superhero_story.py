#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ace_natural_quest_superhero_story.py
====================================================================

A small superhero quest storyworld for a child-facing tale about a hero,
a natural place, and a rescue mission. The seed words are woven into the
world model: an ace hero, a natural path, and a quest that turns into a
complete mini adventure.

The story stays state-driven:
- a hero and helper enter a natural setting
- a quest goal is threatened or delayed
- a sensible superhero tool or power changes the state
- the ending image proves the quest was completed

Run it:
    python storyworlds/worlds/gpt-5.4-mini/ace_natural_quest_superhero_story.py
    python storyworlds/worlds/gpt-5.4-mini/ace_natural_quest_superhero_story.py --qa
    python storyworlds/worlds/gpt-5.4-mini/ace_natural_quest_superhero_story.py --verify
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
    brave: bool = False
    helps_nature: bool = False
    powers: set[str] = field(default_factory=set)

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
class Place:
    id: str
    label: str
    scene: str
    natural: bool = True
    paths: set[str] = field(default_factory=set)
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
class QuestItem:
    id: str
    label: str
    phrase: str
    fragile: bool = False
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
class Threat:
    id: str
    label: str
    phrase: str
    block_text: str
    danger_text: str
    spreads: bool = False
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
class Power:
    id: str
    label: str
    phrase: str
    strength: int
    sense: int
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
class StoryParams:
    place: str
    item: str
    threat: str
    power: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    parent_type: str
    trait: str
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["blocked"] >= THRESHOLD:
            continue
        if e.meters["trouble"] >= THRESHOLD:
            sig = ("trouble", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            if "park" in world.entities:
                world.get("park").meters["alarm"] += 1
            for ent in list(world.entities.values()):
                if ent.kind == "character":
                    ent.memes["worry"] += 1
            out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("spread", _r_spread)]


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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, p in PLACES.items():
        for item_id, item in ITEMS.items():
            if item.fragile and not p.natural:
                continue
            for threat_id, th in THREATS.items():
                for power_id, pw in POWERS.items():
                    if pw.sense >= SENSE_MIN and can_handle(p, item, th, pw):
                        combos.append((place, item_id, threat_id, power_id))
    return combos


def can_handle(place: Place, item: QuestItem, threat: Threat, power: Power) -> bool:
    return place.natural and item.id in threat.tags and power.strength >= threat_strength(threat)


def threat_strength(threat: Threat) -> int:
    return 1 + int(threat.spreads)


def reason_gate(place: Place, item: QuestItem, threat: Threat, power: Power) -> bool:
    return can_handle(place, item, threat, power)


def predict(world: World, item_id: str, threat_id: str) -> dict:
    sim = world.copy()
    sim.get(item_id).meters["trouble"] += 1
    propagate(sim, narrate=False)
    return {"alarm": sim.get("park").meters["alarm"], "trouble": sim.get(item_id).meters["trouble"]}


def start(world: World, hero: Entity, helper: Entity, place: Place, item: QuestItem) -> None:
    hero.memes["hope"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"{hero.id} was an ace hero with a bright cape, and {helper.id} was ready "
        f"to help. One sunny day, they hurried into {place.label}."
    )
    world.say(f"{place.scene} They had come on a quest for {item.phrase}.")


def problem(world: World, hero: Entity, helper: Entity, threat: Threat, item: QuestItem) -> None:
    hero.memes["focus"] += 1
    helper.memes["care"] += 1
    world.say(
        f"But the way forward was blocked by {threat.phrase}. "
        f"{threat.block_text}"
    )
    pred = predict(world, item.id, threat.id)
    world.facts["pred_alarm"] = pred["alarm"]
    world.say(
        f"{helper.id} frowned and warned, \"If we rush, {threat.danger_text}\""
    )


def act(world: World, hero: Entity, power: Power, item: QuestItem) -> None:
    hero.meters["trouble"] += 1
    world.get(item.id).meters["trouble"] += 1
    world.say(
        f"{hero.id} used {power.phrase}. It worked with an ace burst of courage, "
        f"and the path opened."
    )


def finish(world: World, hero: Entity, helper: Entity, parent: Entity, item: QuestItem,
           place: Place) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.get(item.id).meters["found"] += 1
    world.say(
        f"At last, they found {item.phrase} tucked beside a mossy stone. "
        f"{parent.label_word.capitalize()} smiled when they came back."
    )
    world.say(
        f"By dusk, the quest was done, and the natural trail was quiet again. "
        f"{hero.id} stood tall in the golden light, as happy as any hero could be."
    )


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    item = ITEMS[params.item]
    threat = THREATS[params.threat]
    power = POWERS[params.power]

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, role="hero",
                            traits=[params.trait], brave=True, powers={power.id}))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type,
                              role="helper", traits=["careful"]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, role="parent",
                              label="the guardian"))
    park = world.add(Entity(id="park", type="place", label=place.label))
    world.add(Entity(id=item.id, type="quest_item", label=item.label))
    world.add(Entity(id=threat.id, type="threat", label=threat.label))

    start(world, hero, helper, place, item)
    world.para()
    problem(world, hero, helper, threat, item)
    world.para()
    act(world, hero, power, item)
    world.say(
        f"{threat.block_text} Then the trouble faded, and the path felt safe again."
    )
    world.para()
    finish(world, hero, helper, parent, item, place)

    world.facts.update(
        hero=hero, helper=helper, parent=parent, place=place, item=item, threat=threat,
        power=power, outcome="done"
    )
    return world


PLACES = {
    "forest": Place(id="forest", label="the natural forest", scene="The trees swayed softly, and a narrow path curled between ferns.", natural=True, paths={"trail"}, tags={"natural"}),
    "river": Place(id="river", label="the riverbank", scene="The water glimmered, and smooth stones lined the shore.", natural=True, paths={"bank"}, tags={"natural"}),
    "hill": Place(id="hill", label="the grassy hill", scene="The hill was green and open, with wildflowers nodding in the breeze.", natural=True, paths={"slope"}, tags={"natural"}),
}

ITEMS = {
    "map": QuestItem(id="map", label="a treasure map", phrase="a treasure map with a red star", fragile=False, tags={"map"}),
    "gem": QuestItem(id="gem", label="a river gem", phrase="a shining river gem", fragile=False, tags={"gem"}),
    "seed": QuestItem(id="seed", label="a special seed", phrase="a special seed for the garden", fragile=True, tags={"seed"}),
}

THREATS = {
    "fog": Threat(id="fog", label="fog", phrase="a thick fog cloud", block_text="It made the path hard to see.", danger_text="they could lose the trail and the quest item might be missed.", spreads=False, tags={"map", "gem", "seed"}),
    "brambles": Threat(id="brambles", label="brambles", phrase="a wall of brambles", block_text="The thorns scratched close to the trail.", danger_text="the hero could get stuck and the item could stay hidden.", spreads=False, tags={"map", "seed"}),
    "stream": Threat(id="stream", label="stream", phrase="a fast little stream", block_text="Water splashed over the stepping stones.", danger_text="the quest item might wash away before they got there.", spreads=True, tags={"gem", "seed"}),
}

POWERS = {
    "climb": Power(id="climb", label="climbing power", phrase="a quick climbing leap", strength=2, sense=3, tags={"brambles", "hill"}),
    "beam": Power(id="beam", label="beam power", phrase="a bright rescue beam", strength=2, sense=3, tags={"fog", "map"}),
    "glide": Power(id="glide", label="glide power", phrase="a smooth glide across the stones", strength=3, sense=3, tags={"stream", "gem"}),
}

SENSE_MIN = 2
HERO_NAMES = ["Ace", "Nova", "Sky", "Mira"]
HELPER_NAMES = ["Pip", "Juno", "Bea", "Tess"]
TRAITS = ["brave", "kind", "quick", "steady"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero quest storyworld with ace/natural seeds.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.item and args.item not in ITEMS:
        raise StoryError("Unknown item.")
    if args.threat and args.threat not in THREATS:
        raise StoryError("Unknown threat.")
    if args.power and args.power not in POWERS:
        raise StoryError("Unknown power.")
    if args.place and args.item and args.threat and args.power:
        if not reason_gate(PLACES[args.place], ITEMS[args.item], THREATS[args.threat], POWERS[args.power]):
            raise StoryError("That quest combination is not reasonable.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.threat is None or c[2] == args.threat)
              and (args.power is None or c[3] == args.power)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, item, threat, power = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        item=item,
        threat=threat,
        power=power,
        hero_name=args.name or rng.choice(HERO_NAMES),
        hero_type="boy" if rng.random() < 0.5 else "girl",
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        helper_type="boy" if rng.random() < 0.5 else "girl",
        parent_type=args.parent or rng.choice(["mother", "father"]),
        trait=rng.choice(TRAITS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero quest story that includes the words "ace" and "natural".',
        f"Tell a child-friendly hero story where {f['hero'].id} and {f['helper'].id} explore a natural place and finish a quest.",
        f"Write a short adventure where a brave hero overcomes {f['threat'].label} and finds {f['item'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    threat = f["threat"]
    power = f["power"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, an ace hero, and {helper.id}, who helped on the quest. Together they made the story feel like a real superhero adventure."
        ),
        QAItem(
            question="What made the quest difficult?",
            answer=f"{threat.phrase} blocked the way. That mattered because the path was in a natural place, so the hero had to use the right power instead of just rushing ahead."
        ),
        QAItem(
            question="How did they finish the quest?",
            answer=f"{hero.id} used {power.phrase} to get past the problem, and then they found {item.phrase}. The ending shows the quest was completed and the path became calm again."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does 'natural' mean here?",
            answer="It means the story happens in a place like a forest, riverbank, or hill, where trees, stones, and grass are part of the setting."
        ),
        QAItem(
            question="Why is a quest exciting?",
            answer="A quest is exciting because someone has a goal to reach, and there may be a problem to solve before they can get there."
        ),
        QAItem(
            question="What is an ace hero?",
            answer="An ace hero is a very capable hero who feels bold, helpful, and ready to solve problems."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for tid in THREATS:
        lines.append(asp.fact("threat", tid))
    for pid in POWERS:
        lines.append(asp.fact("power", pid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
reason_ok(P,I,T,W) :- place(P), item(I), threat(T), power(W), natural(P), allowed(I,T), sense(W,S), sense_min(M), S >= M, strength(W,PW), need(T,N), PW >= N.
valid(P,I,T,W) :- reason_ok(P,I,T,W).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


CURATED = [
    StoryParams(place="forest", item="map", threat="fog", power="beam", hero_name="Ace", hero_type="boy", helper_name="Mina", helper_type="girl", parent_type="mother", trait="brave"),
    StoryParams(place="river", item="gem", threat="stream", power="glide", hero_name="Nova", hero_type="girl", helper_name="Pip", helper_type="boy", parent_type="father", trait="steady"),
    StoryParams(place="hill", item="seed", threat="brambles", power="climb", hero_name="Sky", hero_type="boy", helper_name="Tess", helper_type="girl", parent_type="mother", trait="kind"),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.item not in ITEMS or params.threat not in THREATS or params.power not in POWERS:
        raise StoryError("Invalid story parameters.")
    if not reason_gate(PLACES[params.place], ITEMS[params.item], THREATS[params.threat], POWERS[params.power]):
        raise StoryError("That combination is not reasonable for this quest.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible quest combos:")
        for combo in asp_valid_combos():
            print("  ", combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
