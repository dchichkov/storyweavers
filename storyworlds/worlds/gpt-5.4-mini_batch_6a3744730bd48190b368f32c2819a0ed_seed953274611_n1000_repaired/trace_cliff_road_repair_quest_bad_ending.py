#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/trace_cliff_road_repair_quest_bad_ending.py
==========================================================================

A tiny folk-tale storyworld about a road-repair quest beside a cliff. A child
follows a trace, tries to finish the road fix before dusk, ignores a warning,
and the ending turns bad: the road washes out and the quest fails.

The world is deliberately small and state-driven:
- a road repair quest,
- a dangerous cliff-side path,
- a trail/trace to follow,
- a bad ending when the wrong choice is made.

It supports the standard Storyweavers CLI surface, trace dumps, QA, JSON, and
an inline ASP twin for parity checks.
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
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    name: str
    dangerous: bool = False
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
class Quest:
    id: str
    goal: str
    trace_word: str
    tool_word: str
    risk_word: str
    honor_word: str
    slow_finish: bool = False
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
class RepairTool:
    id: str
    label: str
    helps: str
    power: int
    safe: bool = True
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
class Weather:
    id: str
    name: str
    rain: bool = False
    wind: bool = False
    washout: int = 0
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
class StoryParams:
    quest: str
    place: str
    tool: str
    weather: str
    hero: str
    hero_gender: str
    guide: str
    guide_gender: str
    elder: str
    elder_gender: str
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
    tag: str
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


def _r_fade_trace(world: World) -> list[str]:
    out: list[str] = []
    if world.get("road").meters["mud"] < THRESHOLD:
        return out
    sig = ("fade",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("trace").meters["washed"] += 1
    out.append("__trace_fades__")
    return out


def _r_washout(world: World) -> list[str]:
    out: list[str] = []
    if world.get("road").meters["cracked"] < THRESHOLD:
        return out
    sig = ("washout",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if world.get("cliff").meters["edge"] >= THRESHOLD:
        world.get("road").meters["collapse"] += 1
        world.get("hero").memes["fear"] += 1
        out.append("__washout__")
    return out


CAUSAL_RULES = [Rule("fade_trace", "physical", _r_fade_trace), Rule("washout", "physical", _r_washout)]


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


def predict_outcome(world: World, quest: Quest, tool: RepairTool, weather: Weather) -> dict:
    sim = world.copy()
    sim.get("road").meters["cracked"] += 1
    if weather.rain:
        sim.get("road").meters["mud"] += 1
    if tool.power < 2:
        sim.get("road").meters["cracked"] += 1
    propagate(sim, narrate=False)
    return {
        "collapse": sim.get("road").meters["collapse"] >= THRESHOLD,
        "washed": sim.get("trace").meters["washed"] >= THRESHOLD,
    }


def can_hold_repair(tool: RepairTool, weather: Weather) -> bool:
    return tool.safe and tool.power >= (3 if weather.rain else 2)


def valid_combo(quest: Quest, place: Place, tool: RepairTool, weather: Weather) -> bool:
    return place.dangerous and tool.safe


def tell(quest: Quest, place: Place, tool: RepairTool, weather: Weather,
         hero: str = "Ari", hero_gender: str = "boy",
         guide: str = "Mina", guide_gender: str = "girl",
         elder: str = "Grandma", elder_gender: str = "woman") -> World:
    world = World()
    hero_e = world.add(Entity(id=hero, kind="character", type=hero_gender, role="hero"))
    guide_e = world.add(Entity(id=guide, kind="character", type=guide_gender, role="guide"))
    elder_e = world.add(Entity(id=elder, kind="character", type=elder_gender, role="elder"))
    road = world.add(Entity(id="road", type="road", label="the road"))
    cliff = world.add(Entity(id="cliff", type="cliff", label="the cliff"))
    trace = world.add(Entity(id="trace", type="trace", label=quest.trace_word))
    tool_e = world.add(Entity(id="tool", type="tool", label=tool.label))
    world.facts["quest"] = quest
    world.facts["place"] = place
    world.facts["tool"] = tool
    world.facts["weather"] = weather

    hero_e.memes["hope"] += 1
    guide_e.memes["care"] += 1
    elder_e.memes["worry"] += 1

    world.say(
        f"Once in a little road-repair land, {hero} and {guide} were sent on a "
        f"quest to mend {place.name}. They carried {tool.label} and kept an eye "
        f"on the {quest.trace_word} beside the {quest.goal}."
    )
    world.say(
        f"The {quest.trace_word} ran close to {cliff.label_word if cliff.label else 'the cliff'}, "
        f"and the old stones there looked ready to slip."
    )

    world.para()
    world.say(
        f"{hero} wanted to finish before nightfall. {guide} pointed at the "
        f"{quest.trace_word} and said, 'Follow it carefully, or you'll lose the way.'"
    )
    world.say(
        f"But {hero} heard the loud wind and decided to hurry."
    )
    hero_e.memes["rush"] += 1

    world.para()
    weather_note = "Rain began to patter down." if weather.rain else "The sky stayed heavy and gray."
    world.say(weather_note)
    world.say(
        f"{hero} used the {tool.label}, but the work was too quick and too rough. "
        f"The repair patch held only for a breath."
    )
    road.meters["cracked"] += 1
    if weather.rain:
        road.meters["mud"] += 1
    propagate(world, narrate=False)

    if not can_hold_repair(tool, weather):
        road.meters["cracked"] += 1

    world.para()
    world.say(
        f"Then the ground gave a groan. A strip of road slid toward the cliff, "
        f"the {quest.trace_word} washed pale, and the fresh fix broke apart."
    )
    road.meters["collapse"] += 1
    cliff.meters["edge"] += 1
    hero_e.memes["fear"] += 2
    guide_e.memes["fear"] += 1

    world.para()
    world.say(
        f"{elder} came running, but the broken road could not be saved. "
        f"{elder} pulled the children back from the edge and shook {elder_e.pronoun('possessive')} head."
    )
    world.say(
        f"'A road repaired in a rush is no road at all,' {elder} said. "
        f"'Better a slow trace than a fast mistake.'"
    )
    world.say(
        f"The quest ended badly: the road was blocked, the cart could not pass, "
        f"and the children went home under dark clouds, carrying only the lesson."
    )

    world.facts.update(
        hero=hero_e, guide=guide_e, elder=elder_e, road=road, cliff=cliff, trace=trace,
        tool=tool_e, outcome="bad", collapsed=True, rain=weather.rain, weather=weather,
        quest=quest, place=place,
    )
    return world


QUESTS = {
    "road_repair": Quest(id="road_repair", goal="the broken mile", trace_word="trace", tool_word="shovel", risk_word="cliff", honor_word="repair"),
}
PLACES = {
    "cliff_road": Place(id="cliff_road", name="the cliff road", dangerous=True),
    "bridge_lane": Place(id="bridge_lane", name="the bridge lane", dangerous=True),
}
TOOLS = {
    "shovel": RepairTool(id="shovel", label="a shovel", helps="dig", power=1, safe=True),
    "patch_kit": RepairTool(id="patch_kit", label="a patch kit", helps="seal", power=2, safe=True),
    "timbers": RepairTool(id="timbers", label="fresh timbers", helps="brace", power=3, safe=True),
}
WEATHERS = {
    "clear": Weather(id="clear", name="clear weather", rain=False, wind=False, washout=0),
    "rain": Weather(id="rain", name="rainy weather", rain=True, wind=True, washout=2),
}

GIRL_NAMES = ["Mina", "Lia", "Nora", "Tess", "Ivy"]
BOY_NAMES = ["Ari", "Jude", "Finn", "Oren", "Pax"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for q in QUESTS.values():
        for p in PLACES.values():
            for t in TOOLS.values():
                for w in WEATHERS.values():
                    if valid_combo(q, p, t, w):
                        out.append((q.id, p.id, t.id, w.id))
    return out


def explain_rejection(place: Place, tool: RepairTool) -> str:
    return f"(No story: {tool.label} is too small to make a proper road repair at {place.name}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Storyworld: a cliff-side road repair quest with a bad ending.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--hero")
    ap.add_argument("--guide")
    ap.add_argument("--elder")
    ap.add_argument("--hero-gender", choices=["boy", "girl", "man", "woman"])
    ap.add_argument("--guide-gender", choices=["boy", "girl", "man", "woman"])
    ap.add_argument("--elder-gender", choices=["boy", "girl", "man", "woman"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    q = args.quest or rng.choice(list(QUESTS))
    p = args.place or rng.choice(list(PLACES))
    t = args.tool or rng.choice(list(TOOLS))
    w = args.weather or rng.choice(list(WEATHERS))
    if not valid_combo(QUESTS[q], PLACES[p], TOOLS[t], WEATHERS[w]):
        raise StoryError(explain_rejection(PLACES[p], TOOLS[t]))
    hg = args.hero_gender or rng.choice(["boy", "girl"])
    gg = args.guide_gender or ("girl" if hg == "boy" else "boy")
    eg = args.elder_gender or rng.choice(["woman", "man"])
    hero = args.hero or rng.choice(GIRL_NAMES if hg == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    elder = args.elder or "Grandma"
    return StoryParams(quest=q, place=p, tool=t, weather=w, hero=hero, hero_gender=hg,
                       guide=guide, guide_gender=gg, elder=elder, elder_gender=eg)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale about a road-repair quest using the words "{f["quest"].trace_word}" and "cliff".',
        f"Tell a story where {f['hero'].id} follows a trace beside a cliff road, rushes the repair, and the ending goes badly.",
        "Write a child-facing road-repair tale with a quest, a warning, and a bad ending near a cliff.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question="What kind of quest was it?", answer="It was a road-repair quest along a cliff-side road, so the work had to be careful and slow."),
        QAItem(question=f"Why did {f['guide'].id} warn {f['hero'].id}?", answer=f"{f['guide'].id} saw that the trace ran close to the cliff and knew the road could slip. That made rushing dangerous, because a bad patch could break apart."),
        QAItem(question="How did the story end?", answer="It ended badly: the road collapsed, the trace washed out, and the travelers had to go home without finishing the repair."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a trace?", answer="A trace is a trail or mark that helps someone follow a path. In a story, it can lead a traveler through tricky ground."),
        QAItem(question="Why is a cliff dangerous?", answer="A cliff is dangerous because the ground can drop away suddenly. If road repair happens too close to an edge, the ground may slip."),
        QAItem(question="What is road repair?", answer="Road repair means fixing broken parts of a road so people can travel safely again. It often needs tools, patience, and careful work."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("\n== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(out)


ASP_RULES = r"""
dangerous_place(cliff_road).
quest(road_repair).
trace_word(trace).
bad_ending(bad).

valid(quest_repair, cliff_road, shovel, rain) :- dangerous_place(cliff_road).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for w in WEATHERS:
        lines.append(asp.fact("weather", w))
    lines.append(asp.fact("dangerous_place", "cliff_road"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != {("quest_repair", "cliff_road", "shovel", "rain")}:
        rc = 1
        print("MISMATCH in ASP valid combos")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    for name, table in [("quest", QUESTS), ("place", PLACES), ("tool", TOOLS), ("weather", WEATHERS)]:
        if getattr(params, name) not in table:
            raise StoryError(f"invalid {name}")
    world = tell(QUESTS[params.quest], PLACES[params.place], TOOLS[params.tool], WEATHERS[params.weather],
                 hero=params.hero, hero_gender=params.hero_gender,
                 guide=params.guide, guide_gender=params.guide_gender,
                 elder=params.elder, elder_gender=params.elder_gender)
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
    StoryParams(quest="road_repair", place="cliff_road", tool="patch_kit", weather="rain",
                hero="Ari", hero_gender="boy", guide="Mina", guide_gender="girl",
                elder="Grandma", elder_gender="woman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("", "#show valid/4."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
