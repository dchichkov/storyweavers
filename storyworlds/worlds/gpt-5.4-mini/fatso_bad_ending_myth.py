#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fatso_bad_ending_myth.py
========================================================

A standalone storyworld for a small mythic domain built from the seed word
"fatso" and the requested "Bad Ending" / "Myth" style.

Premise:
- A boastful village child nicknamed Fatso climbs a sacred hill to ring a stone
  bell for rain.
- The hill has rules, the bell has a cost, and the child wants glory.

Tension:
- The child ignores a warning from an older helper and takes a forbidden token
  meant only for careful hands.
- The world reacts through physical meters and emotional memes.

Turn:
- The bell is rung too hard, the ritual goes wrong, and the charm that should
  call rain instead summons a harsh wind and a cracked shrine.

Ending:
- The village is saved from hunger, but the hill is scarred and the bell is lost.
  The story ends with a sober mythic lesson rather than a happy rescue.

This file follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, main
- supports --trace, --qa, --json, --asp, --verify, --show-asp, --all, -n,
  --seed
- includes Python and inline ASP reasonableness gates
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MORAL_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Item:
    id: str
    label: str
    sacred: bool = False
    risky: bool = False
    gives_weather: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Rite:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

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
class Place:
    id: str
    label: str
    dark: bool = False

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
        self.items: dict[str, Item] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

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
        clone.items = copy.deepcopy(self.items)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_rupture(world: World) -> list[str]:
    out: list[str] = []
    bell = world.items["bell"]
    if bell.meters["cracked"] < THRESHOLD:
        return out
    sig = ("rupture",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.items["hill"].meters["danger"] += 1
    for ent in list(world.entities.values()):
        ent.memes["fear"] += 1
    out.append("__rupture__")
    return out


def _r_rain_or_wind(world: World) -> list[str]:
    out: list[str] = []
    if world.items["bell"].meters["cracked"] < THRESHOLD:
        return out
    sig = ("weather",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.items["sky"].meters["storm"] += 1
    out.append("__weather__")
    return out


RULES = [
    _r_rupture,
    _r_rain_or_wind,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            out = rule(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def dangerous(tool: Item, place: Place) -> bool:
    return tool.risky and place.dark


def reasonable_rites() -> list[Rite]:
    return [r for r in RITES.values() if r.sense >= MORAL_MIN]


def best_rite() -> Rite:
    return max(RITES.values(), key=lambda r: r.sense)


def storm_strength(delay: int) -> int:
    return 2 + delay


def can_hold(rite: Rite, delay: int) -> bool:
    return rite.power >= storm_strength(delay)


def predict(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_rite(sim, sim.get("child"), sim.items[target_id], narrate=False)
    return {
        "cracked": sim.items["bell"].meters["cracked"] >= THRESHOLD,
        "danger": sim.items["hill"].meters["danger"],
    }


def _do_rite(world: World, child: Entity, token: Item, narrate: bool = True) -> None:
    token.meters["used"] += 1
    if token.risky:
        world.items["bell"].meters["rung"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, elder: Entity, place: Place) -> None:
    world.say(
        f"In the old days, {child.id} and {elder.id} climbed {place.label}, where "
        f"the stones remembered every oath. {child.id} was known as fatso, not for shame, "
        f"but because the village children had given the name to the biggest laugher in the lane."
    )
    world.say(
        f"They came to the shrine because the fields were dry and the wheat bent like tired reeds."
    )


def desire(world: World, child: Entity, place: Place) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{child.id} stared at the cracked altar and said, "
        f'"If I ring the bell, the rain will come and the hill will praise me."'
    )
    world.say(
        f"The bell sat in shadow, and {place.label} felt older than the houses below."
    )


def warning(world: World, elder: Entity, child: Entity, tool: Item) -> None:
    elder.memes["caution"] += 1
    world.say(
        f'{elder.id} touched {child.pronoun("possessive")} sleeve and whispered, '
        f'"Do not take {tool.label}. It is for careful hands, and the hill keeps a price."' 
    )


def defy(world: World, child: Entity, tool: Item) -> None:
    child.memes["pride"] += 1
    world.say(
        f'But {child.id} laughed, puffed up with daring, and snatched {tool.label} anyway.'
    )


def ring(world: World, child: Entity, tool: Item, place: Place) -> None:
    world.say(
        f"{child.id} climbed the last stone step, held {tool.label} high, and struck the bell."
    )
    if tool.risky:
        world.say("The sound rolled over the valley like thunder wearing a crown.")
    tool.meters["used"] += 1
    if tool.risky:
        world.items["bell"].meters["cracked"] += 1
    propagate(world, narrate=False)


def alarm(world: World, elder: Entity) -> None:
    world.say(
        f"{elder.id} gasped as the sky turned thin and white, and the ravens wheeled away from the shrine."
    )


def outcome_good(world: World, elder: Entity, child: Entity, rite: Rite) -> None:
    world.say(
        f"Then {elder.id} knelt beside {child.id} and said the old words of thanks. "
        f'"You called for help, but you must never steal a sacred thing," {elder.id} said.'
    )
    world.say(
        f"At last {elder.id} used {rite.text} and the clouds answered at once."
    )


def outcome_bad(world: World, elder: Entity, child: Entity, rite: Rite) -> None:
    world.say(
        f"At last, the bell split with a sharp cry, and the charm was ruined."
    )
    world.say(
        f"{rite.fail} The valley got the rain it needed, but the shrine was never whole again."
    )
    world.say(
        f"That night {child.id} went home quiet, with only the taste of dust and the memory of broken stone."
    )


def tell(place: Place, tool: Item, bell: Item, rite: Rite, delay: int,
         child_name: str = "Milo", child_gender: str = "boy",
         elder_name: str = "Sera", elder_gender: str = "girl") -> World:
    world = World()
    child = world.add_entity(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    elder = world.add_entity(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    world.add_item(tool)
    world.add_item(bell)
    world.add_item(Item("hill", "the hill"))
    world.add_item(Item("sky", "the sky"))
    world.add_item(Item("altar", "the altar"))
    world.facts["place"] = place
    world.facts["tool"] = tool
    world.facts["bell"] = bell
    world.facts["rite"] = rite
    world.facts["delay"] = delay

    opening(world, child, elder, place)
    desire(world, child, place)
    world.para()
    warning(world, elder, child, tool)
    defy(world, child, tool)
    ring(world, child, tool, place)
    alarm(world, elder)
    world.para()
    if can_hold(rite, delay):
        outcome_good(world, elder, child, rite)
        outcome = "contained"
    else:
        outcome_bad(world, elder, child, rite)
        outcome = "burned"
    world.facts["outcome"] = outcome
    world.facts["child"] = child
    world.facts["elder"] = elder
    world.facts["used_tool"] = tool.meters["used"] >= THRESHOLD
    world.facts["bell_cracked"] = bell.meters["cracked"] >= THRESHOLD
    return world


PACES = {
    "hill": Place("hill", "the sacred hill", dark=True),
    "grove": Place("grove", "the moonlit grove", dark=True),
    "well": Place("well", "the old stone well", dark=True),
}

TOOLS = {
    "iron_clapper": Item("iron_clapper", "an iron clapper", risky=True),
    "bone_rattle": Item("bone_rattle", "a bone rattle", risky=False),
    "ember_stick": Item("ember_stick", "a glowing ember stick", risky=True),
}

RITES = {
    "cloud_words": Rite("cloud_words", 3, 4,
                        "spoke the cloud words and raised a bowl of clean water",
                        "spoke too late, and the clouds fled",
                        "spoke the cloud words"),
    "quiet_prayer": Rite("quiet_prayer", 2, 3,
                         "kindled a quiet prayer and set bread on the stone",
                         "murmured a prayer, but the sky stayed hard",
                         "made a quiet prayer"),
    "drum_rite": Rite("drum_rite", 3, 2,
                      "beat the rain drum softly under the eaves",
                      "beat the drum, but the thunder answered first",
                      "beat the rain drum"),
}


GIRLS = ["Sera", "Iris", "Nia", "Mira", "Luna"]
BOYS = ["Milo", "Otis", "Theo", "Bram", "Cato"]
DARK_KNOWLEDGE = {
    "hill": [("What is a hill?", "A hill is a raised piece of land that slopes up from the ground.")],
    "bell": [("What does a bell do?", "A bell makes a sound when it is rung or struck.")],
    "storm": [("What is a storm?", "A storm is weather with strong wind, rain, thunder, or lightning.")],
    "prayer": [("What is a prayer?", "A prayer is when someone speaks or thinks words asking for help, thanks, or hope.")],
    "sacred": [("What does sacred mean?", "Sacred means special in a very serious way, like something people treat with respect.")],
    "rain": [("Why is rain important?", "Rain helps plants grow and fills streams, wells, and fields.")],
    "oath": [("What is an oath?", "An oath is a serious promise.")],
}
KNOWLEDGE_ORDER = ["hill", "bell", "storm", "prayer", "sacred", "rain", "oath"]


def valid_combos() -> list[tuple[str, str, str, int]]:
    combos = []
    for p in PACES:
        for t in TOOLS:
            for r in RITES:
                for d in range(3):
                    if dangerous(TOOLS[t], PACES[p]):
                        combos.append((p, t, r, d))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    tool: str
    rite: str
    delay: int
    child_name: str
    child_gender: str
    elder_name: str
    elder_gender: str
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
    ap = argparse.ArgumentParser(description="Mythic bad-ending storyworld about a dangerous shrine ritual.")
    ap.add_argument("--place", choices=PACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("--name")
    ap.add_argument("--elder")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--elder-gender", choices=["boy", "girl"])
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
              and (args.tool is None or c[1] == args.tool)
              and (args.rite is None or c[2] == args.rite)
              and (args.delay is None or c[3] == args.delay)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, tool, rite, delay = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["boy", "girl"])
    child_name = args.name or rng.choice(BOYS if gender == "boy" else GIRLS)
    elder_gender = args.elder_gender or ("girl" if gender == "boy" else "boy")
    elder_name = args.elder or rng.choice(GIRLS if elder_gender == "girl" else BOYS)
    return StoryParams(place, tool, rite, delay, child_name, gender, elder_name, elder_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic story for a young child that includes the word "fatso" and ends sadly.',
        f"Tell a myth about {f['child'].id}, called fatso, who climbs {f['place'].label} "
        f"to seek rain but makes a dangerous choice.",
        f"Write a short myth where a child ignores a warning, breaks a sacred thing, and learns too late."
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    e = world.facts["elder"]
    rite = world.facts["rite"]
    place = world.facts["place"]
    out = world.facts["outcome"]
    qas = [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {c.id}, the child called fatso, and {e.id}, the older helper on the hill."
        ),
        QAItem(
            question="Why did they go to the shrine?",
            answer="They went because the fields were dry and everyone wanted rain for the crops. The hill was a sacred place where people hoped the sky would listen."
        ),
    ]
    if out == "burned":
        qas.append(QAItem(
            question="What happened after the child used the risky tool?",
            answer="The bell cracked, the ritual broke, and the shrine was ruined. The valley still got rain, but the sacred place never became whole again."
        ))
        qas.append(QAItem(
            question="Did the ending turn out happy?",
            answer="No. It was a bad ending, because the child got the rain but lost the bell and scarred the hill."
        ))
    else:
        qas.append(QAItem(
            question="What did the older helper do at the end?",
            answer=f"{e.id} used the careful rite and asked for rain the safe way. The story still ended sadly for the broken rule, but the village was spared a worse drought."
        ))
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"hill", "bell", "storm", "sacred", "rain", "oath"}
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            q, a = DARK_KNOWLEDGE[key]
            out.append(QAItem(q, a))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    for i in world.items.values():
        meters = {k: v for k, v in i.meters.items() if v}
        if meters:
            lines.append(f"  {i.id:8} (item   ) meters={dict(meters)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(tool: Item) -> str:
    return f"(No story: {tool.label} is not risky enough for a mythic bad ending.)"


def asp_facts() -> str:
    import asp
    lines = []
    for p in PACES:
        lines.append(asp.fact("place", p))
    for t, tool in TOOLS.items():
        lines.append(asp.fact("tool", t))
        if tool.risky:
            lines.append(asp.fact("risky", t))
    for r in RITES:
        lines.append(asp.fact("rite", r))
        lines.append(asp.fact("sense", r, RITES[r].sense))
        lines.append(asp.fact("power", r, RITES[r].power))
    lines.append(asp.fact("moral_min", MORAL_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,R,D) :- place(P), tool(T), risky(T), rite(R), delay(D).
reasonable(R) :- rite(R), sense(R,S), moral_min(M), S >= M.
bad_ending :- chosen_delay(D), chosen_rite(R), power(R,P), storm_need(D,N), P < N.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_reasonable() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/1."))
    return sorted(r for (r,) in asp.atoms(model, "reasonable"))


def asp_verify() -> int:
    rc = 0
    try:
        combos = set(asp_valid_combos())
        py = set(valid_combos())
        if combos != py:
            rc = 1
            print("MISMATCH: valid_combos differ.")
        else:
            print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    except Exception as e:
        print(f"ASP error: {e}")
        return 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate smoke test produced a story.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PACES[params.place], TOOLS[params.tool], Item("bell", "the stone bell", sacred=True, risky=True),
                 RITES[params.rite], params.delay, params.child_name, params.child_gender,
                 params.elder_name, params.elder_gender)
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
    StoryParams("hill", "iron_clapper", "cloud_words", 2, "Milo", "boy", "Sera", "girl"),
    StoryParams("grove", "ember_stick", "quiet_prayer", 1, "Iris", "girl", "Bram", "boy"),
    StoryParams("well", "iron_clapper", "drum_rite", 0, "Cato", "boy", "Luna", "girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/4.\n#show reasonable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{x}" for x in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
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
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
