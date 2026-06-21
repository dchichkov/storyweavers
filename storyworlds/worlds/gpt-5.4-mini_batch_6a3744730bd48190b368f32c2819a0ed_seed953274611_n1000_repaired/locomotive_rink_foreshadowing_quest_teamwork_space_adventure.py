#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/locomotive_rink_foreshadowing_quest_teamwork_space_adventure.py
==============================================================================================

A small standalone storyworld for a space-adventure tale with a locomotive,
an ice rink, foreshadowing, a quest, and teamwork.

The premise: a child crew wants to cross a moon rink to reach a beacon tower and
recover a lost star key. A cautious clue early on hints that the rink's ice is
thin near a glowing rail line, so the crew must use teamwork, a locomotive,
and a safe path to complete the quest.

The ending is state-driven: the key is found, the crew's tools and feelings
change, and the final image proves the mission succeeded.
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
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    track: str
    rink: str
    quest_goal: str
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
class Crew:
    id: str
    label: str
    type: str
    role: str
    brave: int = 5
    careful: int = 5
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
class Vehicle:
    id: str
    label: str
    type: str
    sound: str
    helps: str
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
    hidden_in: str
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
    setting: str
    crew: str
    vehicle: str
    item: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["ice_warning"] >= THRESHOLD and ("alarm", e.id) not in world.fired:
            world.fired.add(("alarm", e.id))
            for c in crew_entities(world):
                c.memes["attention"] += 1
            out.append("__alarm__")
    return out


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    if world.get("team").meters["trust"] >= THRESHOLD and world.get("locomotive").meters["ready"] >= THRESHOLD:
        if ("help",) not in world.fired:
            world.fired.add(("help",))
            world.get("team").memes["hope"] += 1
            out.append("__help__")
    return out


CAUSAL_RULES = [Rule("alarm", "foreshadow", _r_alarm), Rule("help", "teamwork", _r_help)]


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


def crew_entities(world: World) -> list[Entity]:
    return [e for e in world.entities.values() if e.role in {"captain", "helper"}]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid in CREWS:
            for vid in VEHICLES:
                for iid in ITEMS:
                    if reasonableness_gate(SETTINGS[sid], CREWS[cid], VEHICLES[vid], ITEMS[iid]):
                        combos.append((sid, cid, vid, iid))
    return combos


def reasonableness_gate(setting: Setting, crew: Crew, vehicle: Vehicle, item: QuestItem) -> bool:
    return "rink" in setting.tags and "locomotive" in vehicle.tags and "quest" in item.tags


def predict_trip(world: World, item_id: str) -> dict:
    sim = world.copy()
    _do_trip(sim, narrate=False)
    return {"found": sim.get("treasure").meters["found"] >= THRESHOLD, "hope": sim.get("team").memes["hope"]}


def _do_trip(world: World, narrate: bool = True) -> None:
    world.get("train").meters["moving"] += 1
    world.get("locomotive").meters["ready"] += 1
    world.get("rink").meters["ice_warning"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, setting: Setting, crew: Crew, item: QuestItem, vehicle: Vehicle) -> None:
    world.say(
        f"On the silver moon base, {crew.label} and the team rolled out beside the {setting.rink}. "
        f"A small locomotive waited on the rail like a patient metal beetle."
    )
    world.say(
        f"{crew.label} wanted to complete the quest for the {item.label}, but the rink shone with a strange blue crack. "
        f"That was the first hint that the ice might not be safe."
    )


def foreshadow(world: World, setting: Setting, crew: Crew, item: QuestItem) -> None:
    world.say(
        f"{crew.label} knelt and touched the frost. It felt thin near the glowing rail line, and {crew.pronoun()} noticed little bubbles trapped under the ice."
    )
    world.say(
        f'"We should watch the rink carefully," {crew.label} said. "Something under there is making the ice whisper."'
    )


def quest_turn(world: World, crew: Crew, item: QuestItem, vehicle: Vehicle) -> None:
    crew.memes["determination"] += 1
    world.say(
        f"The crew pointed the locomotive toward the safe edge of the rink. "
        f"It rumbled {vehicle.sound}, and {vehicle.helps} while the team searched for the hidden {item.label}."
    )


def teamwork(world: World, crew: Crew, item: QuestItem, vehicle: Vehicle) -> None:
    world.get("team").memes["trust"] += 1
    world.get("team").memes["joy"] += 1
    world.get("treasure").meters["found"] += 1
    world.say(
        f"One child watched the ice, another guided the locomotive, and a third checked the map. "
        f"Together they crossed the rink without slipping."
    )


def ending(world: World, crew: Crew, item: QuestItem) -> None:
    world.say(
        f"At last they found the {item.label} tucked inside the beacon tower. "
        f"With the star key in hand, the locomotive glimmered behind them and the rink stayed quiet under the moonlight."
    )
    world.say(
        f"{crew.label} smiled, because the clue had saved them from a bad step and teamwork had carried the quest home."
    )


def tell(setting: Setting, crew_cfg: Crew, vehicle: Vehicle, item: QuestItem) -> World:
    world = World()
    team = world.add(Entity(id="team", kind="character", type=crew_cfg.type, label=crew_cfg.label, role=crew_cfg.role))
    crew_ent = world.add(Entity(id="captain", kind="character", type=crew_cfg.type, label=crew_cfg.label, role="captain"))
    helper = world.add(Entity(id="helper", kind="character", type=crew_cfg.type, label="the helper", role="helper"))
    train = world.add(Entity(id="train", kind="thing", type=vehicle.type, label=vehicle.label, tags=set(vehicle.tags)))
    loco = world.add(Entity(id="locomotive", kind="thing", type="locomotive", label="the locomotive", tags=set(vehicle.tags)))
    rink = world.add(Entity(id="rink", kind="thing", type="rink", label=setting.rink, tags=set(setting.tags)))
    treasure = world.add(Entity(id="treasure", kind="thing", type="quest_item", label=item.label, tags=set(item.tags)))

    world.facts.update(team=team, crew=crew_ent, helper=helper, train=train, locomotive=loco, rink=rink, treasure=treasure, setting=setting, item=item, vehicle=vehicle)

    opening(world, setting, crew_cfg, item, vehicle)
    world.para()
    foreshadow(world, setting, crew_cfg, item)
    world.para()
    quest_turn(world, crew_cfg, item, vehicle)
    teamwork(world, crew_cfg, item, vehicle)
    world.para()
    ending(world, crew_cfg, item)
    return world


SETTINGS = {
    "moon_rink": Setting(
        id="moon_rink",
        place="Moon Base Nine",
        scene="a bright space station concourse",
        track="a silver track",
        rink="the moon rink",
        quest_goal="the star key",
        tags={"space", "rink", "foreshadowing", "quest", "teamwork"},
    )
}

CREWS = {
    "cadets": Crew(
        id="cadets",
        label="the cadets",
        type="crew",
        role="crew",
        brave=6,
        careful=6,
        tags={"teamwork"},
    )
}

VEHICLES = {
    "locomotive": Vehicle(
        id="locomotive",
        label="a little locomotive",
        type="locomotive",
        sound="huff-huff",
        helps="its warm lights blinked across the rail",
        tags={"locomotive", "space"},
    )
}

ITEMS = {
    "star_key": QuestItem(
        id="star_key",
        label="star key",
        phrase="a star key",
        hidden_in="the beacon tower",
        tags={"quest"},
    )
}

CURATED = [
    StoryParams(setting="moon_rink", crew="cadets", vehicle="locomotive", item="star_key", seed=1),
]


KNOWLEDGE = {
    "locomotive": [("What is a locomotive?", "A locomotive is the engine that pulls a train. It has strong wheels and can help move cars along a track.")],
    "rink": [("What is a rink?", "A rink is a smooth place for sliding or skating. Ice rinks are slippery, so people have to move carefully.")],
    "foreshadowing": [("What is foreshadowing?", "Foreshadowing is an early clue that hints something important will happen later.")],
    "quest": [("What is a quest?", "A quest is a mission to find something important or help someone. It often has a goal and a journey.")],
    "teamwork": [("What is teamwork?", "Teamwork means people help each other and work together. Everyone does a part, and that makes hard jobs easier.")],
}
KNOWLEDGE_ORDER = ["locomotive", "rink", "foreshadowing", "quest", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short space-adventure story that uses the words "locomotive" and "rink".',
        'Tell a child-friendly quest story where a crew notices a clue about the rink before crossing it.',
        'Write a teamwork story on a moon base where a locomotive helps the heroes finish a quest.',
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="Where does the story happen?", answer="It happens on a moon base near a rink, with a silver rail line and a glowing tower nearby."),
        QAItem(question="What clue warned the crew?", answer="They saw a strange crack and bubbles under the ice, which hinted the rink was thin and needed careful travel."),
        QAItem(question="How did the team finish the quest?", answer="They used the locomotive, watched the ice, and worked together so they could cross safely and find the star key."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {"locomotive", "rink", "foreshadowing", "quest", "teamwork"}
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_params() -> list[StoryParams]:
    return [StoryParams(setting=s, crew=c, vehicle=v, item=i) for s, c, v, i in valid_combos()]


def explain_rejection() -> str:
    return "(No story: this world needs a moon rink, a locomotive, and a quest item so the clue, the journey, and the teamwork all matter.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    settings = [args.setting] if getattr(args, "setting", None) else list(SETTINGS)
    crews = [args.crew] if getattr(args, "crew", None) else list(CREWS)
    vehicles = [args.vehicle] if getattr(args, "vehicle", None) else list(VEHICLES)
    items = [args.item] if getattr(args, "item", None) else list(ITEMS)
    combos = [(s, c, v, i) for s in settings for c in crews for v in vehicles for i in items if (s, c, v, i) in valid_combos()]
    if not combos:
        raise StoryError(explain_rejection())
    s, c, v, i = rng.choice(combos)
    return StoryParams(setting=s, crew=c, vehicle=v, item=i)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.crew not in CREWS or params.vehicle not in VEHICLES or params.item not in ITEMS:
        raise StoryError("Invalid StoryParams selection.")
    world = tell(SETTINGS[params.setting], CREWS[params.crew], VEHICLES[params.vehicle], ITEMS[params.item])
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


ASP_RULES = r"""
valid(S,C,V,I) :- setting(S), crew(C), vehicle(V), item(I), has_rink(S), has_locomotive(V), has_quest(I).
has_rink(moon_rink).
has_locomotive(locomotive).
has_quest(star_key).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        if "rink" in SETTINGS[sid].tags:
            lines.append(asp.fact("has_rink", sid))
    for cid in CREWS:
        lines.append(asp.fact("crew", cid))
    for vid in VEHICLES:
        lines.append(asp.fact("vehicle", vid))
        if "locomotive" in VEHICLES[vid].tags:
            lines.append(asp.fact("has_locomotive", vid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
        if "quest" in ITEMS[iid].tags:
            lines.append(asp.fact("has_quest", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos disagree.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        rc = 1
        print(f"MISMATCH: smoke test failed: {e}")
    else:
        print("OK: verify passed and story generation smoke test succeeded.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with a locomotive, a rink, a quest, foreshadowing, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--crew", choices=CREWS)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--item", choices=ITEMS)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
