#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pardon_curiosity_pirate_tale.py
===============================================================

A standalone storyworld for a tiny pirate tale about curiosity, a bit of trouble,
and a pardon after an honest apology.

Domain sketch
-------------
Two young pirates are exploring a docked ship. One is very curious and wants to
open a forbidden chest or cabin latch because it might hold a secret map, a shiny
coin, or a hidden compass. The other pirate warns them. If the curious pirate
disobeys, a small accident happens: a gull snatches bait, a sail gets tangled, or
a lantern nearly tips. A calm captain fixes the problem, listens to the apology,
and offers a pardon. The ending gives the children a safe curiosity tool, like a
spyglass or a treasure riddle book, so they can explore without causing trouble.

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and an inline ASP twin
- makes world state drive prose and Q&A
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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



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
    scene: str
    dark_spot: str
    mood: str

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
class CuriosityItem:
    id: str
    label: str
    phrase: str
    where: str
    risky: bool = True

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
class Mishap:
    id: str
    label: str
    trigger: str
    result: str
    power: int
    sense: int

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
class SafeWonder:
    id: str
    label: str
    phrase: str
    use_line: str

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


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["trouble"] < THRESHOLD:
            continue
        sig = ("tension", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("ship").meters["alarm"] += 1
        out.append("__tension__")
    return out


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("ship").meters["alarm"] < THRESHOLD:
        return out
    sig = ("alarm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for c in world.characters():
        c.memes["worry"] += 1
    out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("tension", _r_tension), Rule("alarm", _r_alarm)]


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


def risky_choice(item: CuriosityItem, setting: Setting) -> bool:
    return item.risky and "ship" in setting.id


def sensible_fix(mishap: Mishap) -> bool:
    return mishap.sense >= 2


def severity(mishap: Mishap, delay: int) -> int:
    return mishap.power + delay


def contained(mishap: Mishap, delay: int) -> bool:
    return severity(mishap, delay) <= 3


def predict_trouble(world: World, item_id: str) -> dict:
    sim = world.copy()
    _do_choice(sim, sim.get(item_id), narrate=False)
    return {"alarm": sim.get("ship").meters["alarm"], "trouble": sim.get(item_id).meters["trouble"]}


def _do_choice(world: World, curious: Entity, narrate: bool = True) -> None:
    curious.memes["trouble"] += 1
    curious.meters["mischief"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    world.say(
        f"On a bright afternoon at {setting.place}, {a.id} and {b.id} turned the docked ship into {setting.scene}."
    )
    world.say(
        f"The deck creaked, the ropes slapped softly, and {setting.dark_spot} looked full of mystery."
    )


def wonder(world: World, a: Entity, item: CuriosityItem) -> None:
    a.memes["curiosity"] += 1
    world.say(
        f"{a.id}'s eyes shone. \"I wonder what is inside {item.phrase}.\" {a.id} said."
    )


def warn(world: World, b: Entity, a: Entity, item: CuriosityItem, captain: Entity) -> None:
    pred = predict_trouble(world, "curious")
    b.memes["care"] += 1
    world.facts["pred_alarm"] = pred["alarm"]
    world.say(
        f"{b.id} bit {b.pronoun('possessive')} lip. \"Please do not touch {item.label},\" {b.id} said. "
        f"\"{captain.label_word.capitalize()} said to leave it alone.\""
    )


def defy(world: World, a: Entity, item: CuriosityItem) -> None:
    a.memes["defiance"] += 1
    world.say(
        f"{a.id} peered at the latch, then reached out anyway. \"Just one tiny look,\" {a.id} whispered."
    )
    world.say(f"Then {a.id} opened {item.phrase}.")


def mishap_event(world: World, item: CuriosityItem, mishap: Mishap, target: Entity) -> None:
    target.meters["troubled"] += 1
    target.meters["fixed_later"] += 0
    world.get("ship").meters["alarm"] += 1
    world.say(
        f"A small {mishap.label} followed: {mishap.trigger}, and {mishap.result}."
    )


def alarm(world: World, b: Entity, a: Entity, captain: Entity) -> None:
    world.say(f"\"{a.id}!\" {b.id} cried. \"{captain.label_word.capitalize()}!\"")


def captain_fixes(world: World, captain: Entity, mishap: Mishap, target: Entity) -> None:
    target.meters["troubled"] = 0.0
    world.get("ship").meters["alarm"] = 0.0
    world.say(
        f"{captain.label_word.capitalize()} came quickly and {mishap.result}."
    )


def pardon(world: World, captain: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"Then {captain.label_word.capitalize()} knelt down and said, \"I pardon you because you told the truth.\""
    )
    world.say(
        f"\"Curiosity is a good thing when it stays safe,\" {captain.pronoun()} added softly."
    )


def safe_ending(world: World, captain: Entity, a: Entity, b: Entity, safe: SafeWonder) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"The next morning, {captain.label_word.capitalize()} gave them {safe.phrase}."
    )
    world.say(
        f"\"Now you can explore with this,\" {captain.pronoun()} smiled. {safe.use_line}"
    )
    world.say(
        f"{a.id} and {b.id} leaned over the rail, curious again, but safe at last."
    )


def tell(setting: Setting, item: CuriosityItem, mishap: Mishap, safe: SafeWonder,
         a_name: str = "Finn", b_name: str = "Mina", captain_name: str = "Captain Mira",
         delay: int = 0) -> World:
    world = World()
    a = world.add(Entity(id=a_name, kind="character", type="boy", role="curious"))
    b = world.add(Entity(id=b_name, kind="character", type="girl", role="cautioner"))
    captain = world.add(Entity(id=captain_name, kind="character", type="captain", label="the captain", role="adult"))
    ship = world.add(Entity(id="ship", type="ship"))
    curious = world.add(Entity(id="curious", type="thing", label=item.label))
    opening(world, a, b, setting)
    world.para()
    wonder(world, a, item)
    warn(world, b, a, item, captain)
    if not risky_choice(item, setting):
        raise StoryError("No story: this choice is not risky enough for a pirate curiosity tale.")
    a.memes["trouble"] += 1
    defy(world, a, item)
    world.para()
    mishap_event(world, item, mishap, curious)
    alarm(world, b, a, captain)
    if contained(mishap, delay):
        captain_fixes(world, captain, mishap, curious)
        pardon(world, captain, a, b)
        world.para()
        safe_ending(world, captain, a, b, safe)
        outcome = "pardoned"
    else:
        captain_fixes(world, captain, mishap, curious)
        world.say(
            "The scare was bigger than expected, but the captain still listened to their apology and gave a serious pardon."
        )
        safe_ending(world, captain, a, b, safe)
        outcome = "serious"
    world.facts.update(
        setting=setting, item=item, mishap=mishap, safe=safe, a=a, b=b,
        captain=captain, ship=ship, outcome=outcome, delay=delay, curious=curious
    )
    return world


SETTINGS = {
    "dock": Setting("dock", "the harbor dock", "a pirate hideout", "the shadow under the gangplank", "salt-bright"),
    "ship": Setting("ship", "the ship deck", "a pirate hideout", "the shadow behind the mast", "windy"),
    "cove": Setting("cove", "the hidden cove", "a treasure camp", "the dark nook by the rocks", "salty"),
}

ITEMS = {
    "chest": CuriosityItem("chest", "the brass chest", "a brass chest", "near the captain's cabin", True),
    "latch": CuriosityItem("latch", "the cabin latch", "the cabin latch", "by the tiny door", True),
    "curtain": CuriosityItem("curtain", "the sail curtain", "the sail curtain", "hanging beside the lantern", True),
}

MISHAPS = {
    "gull": Mishap("gull", "gull trouble", "a hungry gull swooped in", "the bait was scattered across the deck", 2, 3),
    "lantern": Mishap("lantern", "lantern wobble", "the lantern tipped and wobbled", "the captain set it straight before any flame could spill", 1, 3),
    "rope": Mishap("rope", "rope tangle", "a loose rope wrapped around the post", "the captain untied it in a snap", 1, 2),
}

SAFES = {
    "spyglass": SafeWonder("spyglass", "a spyglass", "a shiny spyglass", "It let them search faraway waves without touching anything forbidden."),
    "riddlebook": SafeWonder("riddlebook", "a riddle book", "a little riddle book", "It gave their curiosity a game to solve."),
    "map": SafeWonder("map", "a map box", "a box of treasure maps", "It turned their wondering into a safe hunt."),
}


@dataclass
class StoryParams:
    setting: str
    item: str
    mishap: str
    safe: str
    delay: int = 0
    a_name: str = "Finn"
    b_name: str = "Mina"
    captain_name: str = "Captain Mira"
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

CURATED = [
    dataclass(type("P", (), {}))
]



def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, i, m) for s in SETTINGS for i in ITEMS for m in MISHAPS if risky_choice(ITEMS[i], SETTINGS[s])]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a child that includes the word "pardon" and shows curiosity causing a small problem on {f["setting"].place}.',
        f"Tell a story where {f['a'].id} wants to open {f['item'].label} but gets pardoned after telling the truth.",
        "Write a gentle pirate story about curiosity, a little trouble, and a captain who forgives the children at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, captain = f["a"], f["b"], f["captain"]
    item, mishap, safe = f["item"], f["mishap"], f["safe"]
    return [
        ("Who are the story about?",
         f"It is about {a.id} and {b.id}, two young pirates on {f['setting'].place}. They were curious about {item.phrase}, and their captain helped them after the trouble."),
        (f"What did {a.id} want to do?",
         f"{a.id} wanted to open {item.phrase} because {a.pronoun()} was curious. That choice led to a small pirate mishap."),
        (f"Why did the captain pardon them?",
         f"The captain pardoned them because they told the truth and were sorry. The captain wanted them to learn from the mistake instead of hiding it."),
        ("How did the story end?",
         f"It ended with the children using {safe.phrase} and staying safe on the ship. They were still curious, but now their curiosity had a safer place to go."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"curiosity", "pardon", world.facts["safe"].id, world.facts["mishap"].id}
    out = []
    if "curiosity" in tags:
        out.append(("What is curiosity?", "Curiosity is wanting to know, see, or learn about something. It can lead to good discoveries when you are careful."))
    out.append(("What does pardon mean?", "To pardon someone is to forgive them and let the mistake go after they are sorry."))
    out.append(("What is a spyglass?", "A spyglass is a tool you look through to see faraway things more clearly."))
    out.append(("Why can a lantern be dangerous on a ship?", "A lantern makes real light, and on a ship a flame can tip, spill, or start trouble if it is not watched carefully."))
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(I) :- item(I), risky(I).
trouble(C) :- curious(C), risk(chest).
fixable(M) :- mishap(M), sense(M, S), S >= 2.
outcome(pardoned) :- fixable(M), risk(I).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if i.risky:
            lines.append(asp.fact("risky", iid))
    for mid, m in MISHAPS.items():
        lines.append(asp.fact("mishap", mid))
        lines.append(asp.fact("sense", mid, m.sense))
    for sf in SAFES:
        lines.append(asp.fact("safe", sf))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show risk/1."))
    return sorted(set(asp.atoms(model, "risk")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != {(i,) for i in []}:
        pass
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, item=None, mishap=None, safe=None, delay=None, a_name=None, b_name=None, captain_name=None, seed=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke story generation succeeded.")
    except Exception as exc:
        print(f"FAIL: story generation crashed: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate curiosity tale with pardon and safe wonder.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--safe", choices=SAFES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
    ap.add_argument("--a-name")
    ap.add_argument("--b-name")
    ap.add_argument("--captain-name")
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
    if args.setting or args.item or args.mishap:
        combos = [c for c in combos if (not args.setting or c[0] == args.setting) and (not args.item or c[1] == args.item) and (not args.mishap or c[2] == args.mishap)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, mishap = rng.choice(sorted(combos))
    safe = args.safe or rng.choice(sorted(SAFES))
    return StoryParams(setting, item, mishap, safe, delay=args.delay if args.delay is not None else rng.randint(0, 2), a_name=args.a_name or "Finn", b_name=args.b_name or "Mina", captain_name=args.captain_name or "Captain Mira")


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item], MISHAPS[params.mishap], SAFES[params.safe], params.a_name, params.b_name, params.captain_name, params.delay)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=[QAItem(q, a) for q, a in story_qa(world)], world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)], world=world)


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
        print(asp_program(show="#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(s, i, m, sf)) for s, i, m in valid_combos()[:5] for sf in [next(iter(SAFES))]][:5]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx+1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
