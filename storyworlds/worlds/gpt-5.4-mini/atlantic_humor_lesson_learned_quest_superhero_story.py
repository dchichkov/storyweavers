#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/atlantic_humor_lesson_learned_quest_superhero_story.py
======================================================================================

A small standalone story world for a superhero-style quest set around the Atlantic.

Domain sketch:
- A child hero and a sidekick are sent on a quest to recover a drifting beacon.
- The Atlantic makes the route tricky: fog, gulls, waves, and a squeaky gadget
  turn the quest humorous rather than grim.
- A wrong shortcut causes trouble; a calmer choice and a learned lesson resolve it.
- The ending proves the change through a repaired signal, a safer plan, and a
  bright image over the Atlantic.

The story is intentionally tiny and constraint-driven rather than freeform. It
supports a small set of plausible variants, a reasonableness gate, and an inline
ASP twin for parity checks.
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
    attrs: dict[str, object] = field(default_factory=dict)

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
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    scene: str
    place: str
    weather: str
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
class Hero:
    id: str
    title: str
    power: str
    gadget: str
    laugh: str
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
class QuestItem:
    id: str
    label: str
    vulnerable: bool
    near: str
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
class Obstacle:
    id: str
    label: str
    danger: str
    funny: str
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
class Fix:
    id: str
    label: str
    power: int
    sense: int
    text: str
    lesson: str
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


def _r_messy(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["splash"] < THRESHOLD:
            continue
        sig = ("splash", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["drip"] += 1
        out.append("__splash__")
    return out


def _r_humor(world: World) -> list[str]:
    out: list[str] = []
    if "hero" in world.entities and "sidekick" in world.entities:
        h = world.get("hero")
        s = world.get("sidekick")
        if h.meters["oops"] >= THRESHOLD and s.meters["giggle"] < THRESHOLD:
            sig = ("giggle",)
            if sig not in world.fired:
                world.fired.add(sig)
                s.memes["humor"] += 1
                out.append("__giggle__")
    return out


CAUSAL_RULES = [Rule("messy", _r_messy), Rule("humor", _r_humor)]


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


def reasonableness_ok(setting: Setting, item: QuestItem, fix: Fix) -> bool:
    return setting.id in {"atlantic_dock", "atlantic_lighthouse", "atlantic_boat"} and item.vulnerable and fix.sense >= 2


def fix_beats_trouble(fix: Fix, obstacle: Obstacle) -> bool:
    return fix.power >= {"fog": 2, "waves": 3, "seagulls": 1}.get(obstacle.id, 2)


def predict(world: World, item_id: str) -> dict:
    sim = world.copy()
    item = sim.get(item_id)
    item.meters["splash"] += 1
    propagate(sim, narrate=False)
    return {"drip": sim.get(item_id).meters["drip"]}


def setup(world: World, hero: Entity, sidekick: Entity, setting: Setting, item: QuestItem) -> None:
    hero.memes["duty"] += 1
    sidekick.memes["trust"] += 1
    world.say(
        f"In the Atlantic wind, {hero.id} and {sidekick.id} stood on {setting.place}. "
        f"{setting.scene}"
    )
    world.say(
        f'"{hero.id} the {hero.role}!" the townsfolk cheered. '
        f'Their quest was to bring back {item.label} before the harbor went dark.'
    )


def quest_call(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["quest"] += 1
    world.say(
        f"{hero.id} pointed at the horizon. \"We have to go now,\" {hero.pronoun()} said, "
        f"\"or the {obstacle.label} will swallow the signal.\""
    )


def joke(world: World, sidekick: Entity, hero: Entity, obstacle: Obstacle) -> None:
    sidekick.memes["humor"] += 1
    world.say(
        f"{sidekick.id} tried to look brave, but {obstacle.funny} made {sidekick.pronoun('object')} snort-laugh. "
        f"Even the gulls seemed to giggle."
    )


def slip(world: World, item: Entity, obstacle: Obstacle) -> None:
    item.meters["splash"] += 1
    item.meters["oops"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The shortcut backfired: a wave slapped {item.label}, and the {obstacle.label} got worse instead of better."
    )


def warn(world: World, sidekick: Entity, hero: Entity, obstacle: Obstacle, item: QuestItem) -> None:
    pred = predict(world, "artifact")
    sidekick.memes["care"] += 1
    world.facts["predicted_drip"] = pred["drip"]
    world.say(
        f"{sidekick.id} wiped salt from {sidekick.pronoun('possessive')} nose and said, "
        f"\"If we rush, {item.label} will get wet, and the {obstacle.label} will still be there.\""
    )


def fix_it(world: World, hero: Entity, sidekick: Entity, fix: Fix, obstacle: Obstacle, item: Entity) -> None:
    item.meters["splash"] = 0
    world.get("signal").meters["dark"] = 0
    world.say(
        f"{hero.id} nodded and used the {fix.label}. {fix.text} The {obstacle.label} lost its grip on the quest."
    )


def lesson(world: World, hero: Entity, sidekick: Entity, fix: Fix, item: QuestItem) -> None:
    hero.memes["lesson"] += 1
    sidekick.memes["lesson"] += 1
    world.say(
        f"\"Next time,\" {hero.id} said, \"we slow down first.\" {fix.lesson} "
        f"Their {item.label} stayed ready, and the Atlantic shone silver behind them."
    )


def tell(setting: Setting, hero_cfg: Hero, item: QuestItem, obstacle: Obstacle, fix: Fix) -> World:
    world = World()
    hero = world.add(Entity("hero", kind="character", type="boy", label=hero_cfg.title, role="hero"))
    sidekick = world.add(Entity("sidekick", kind="character", type="girl", label="Starling", role="sidekick"))
    artifact = world.add(Entity("artifact", type="thing", label=item.label))
    signal = world.add(Entity("signal", type="thing", label="the harbor signal"))
    world.add(Entity("storm", type="thing", label=obstacle.label))
    world.add(Entity("fix", type="thing", label=fix.label))

    setup(world, hero, sidekick, setting, item)
    world.para()
    quest_call(world, hero, obstacle)
    joke(world, sidekick, hero, obstacle)
    warn(world, sidekick, hero, obstacle, item)
    world.para()
    slip(world, artifact, obstacle)
    world.say(f"The little hero felt the water in {hero_cfg.gadget} and tried not to wobble.")
    world.para()
    fix_it(world, hero, sidekick, fix, obstacle, artifact)
    lesson(world, hero, sidekick, fix, item)

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        setting=setting,
        item=item,
        obstacle=obstacle,
        fix=fix,
        artifact=artifact,
        signal=signal,
    )
    return world


SETTINGS = {
    "atlantic_dock": Setting(
        "atlantic_dock",
        "The dock smelled like salt and old rope, and a lantern blinked from the pier.",
        "the Atlantic dock",
        "windy",
        tags={"atlantic"},
    ),
    "atlantic_lighthouse": Setting(
        "atlantic_lighthouse",
        "The lighthouse beam spun in circles while foamy waves cheered below.",
        "the Atlantic lighthouse",
        "misty",
        tags={"atlantic"},
    ),
    "atlantic_boat": Setting(
        "atlantic_boat",
        "Their tiny boat bobbed like a joke on a giant blue giggle.",
        "the Atlantic boat",
        "brisk",
        tags={"atlantic"},
    ),
}

HEROES = {
    "wave_kid": Hero("Wave Kid", "Wave Kid", "wave sense", "pocket compass", "heh", tags={"atlantic"}),
    "caped_mini": Hero("Caped Mini", "Caped Mini", "quick leaps", "signal whistle", "ha!", tags={"atlantic"}),
}

ITEMS = {
    "beacon": QuestItem("beacon", "the beacon", True, "near the waterline", tags={"atlantic"}),
    "lantern_key": QuestItem("lantern_key", "the lantern key", True, "inside the signal box", tags={"atlantic"}),
}

OBSTACLES = {
    "fog": Obstacle("fog", "fog", "hides the way", "looked like a giant cotton ball with a secret", tags={"atlantic"}),
    "waves": Obstacle("waves", "waves", "splashes everything", "kept trying to high-five their boots", tags={"atlantic"}),
    "seagulls": Obstacle("seagulls", "seagulls", "nabs snacks", "argued like tiny alarms", tags={"atlantic"}),
}

FIXES = {
    "slow_map": Fix("slow_map", "a slow map", 2, 3, "They unfolded a map, matched the lighthouse marks, and walked one careful step at a time.", "The lesson was simple: a careful plan beats a flashy rush.", tags={"lesson"}),
    "signal_glove": Fix("signal_glove", "a signal glove", 3, 2, "They hooked the beacon with the glove and kept it steady above the foam.", "They learned that the right tool and a calm hand can save the day.", tags={"quest"}),
    "rope_bridge": Fix("rope_bridge", "a rope bridge", 3, 2, "They tied a short rope line and crossed where the water was shallow.", "They learned that teamwork can turn a risky shortcut into a safe path.", tags={"quest"}),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    hero: str
    item: str
    obstacle: str
    fix: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for iid in ITEMS:
            for oid in OBSTACLES:
                for fid in FIXES:
                    if reasonableness_ok(SETTINGS[sid], ITEMS[iid], FIXES[fid]) and fix_beats_trouble(FIXES[fid], OBSTACLES[oid]):
                        combos.append((sid, iid, oid, fid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero quest story world for the Atlantic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--fix", choices=FIXES)
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
    if args.fix and FIXES[args.fix].sense < 2:
        raise StoryError("The fix is too silly for a believable quest.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.obstacle is None or c[2] == args.obstacle)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, iid, oid, fid = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(sorted(HEROES))
    return StoryParams(sid, hero, iid, oid, fid)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], HEROES[params.hero], ITEMS[params.item], OBSTACLES[params.obstacle], FIXES[params.fix])
    story = world.render()
    prompts = [
        f"Write a superhero quest story about the Atlantic, using the word atlantic and a funny problem that needs a lesson.",
        f"Tell a child-friendly superhero adventure where {params.hero.replace('_', ' ')} has to recover {ITEMS[params.item].label} near the Atlantic.",
        f"Write a story with Humor, Lesson Learned, and Quest in a superhero style ending with a safer plan.",
    ]
    story_qa = [
        QAItem("What was the quest?", f"The quest was to recover {ITEMS[params.item].label} and keep the harbor signal strong. The heroes needed a calm fix because the Atlantic made the trip tricky."),
        QAItem("Why did the plan go wrong at first?", f"It went wrong because the heroes rushed and a wave splashed the artifact. The shortcut made the obstacle worse instead of solving it."),
        QAItem("How did the story end?", f"It ended with a safer plan, a useful tool, and a lesson learned. The beacon stayed ready, and the Atlantic glowed behind them."),
    ]
    world_qa = [
        QAItem("What is the Atlantic?", "The Atlantic is a huge ocean. In stories like this, it can make quests windy, wet, and a little funny."),
        QAItem("What is a quest?", "A quest is a mission to go find, fix, or deliver something important. Heroes often use teamwork and courage on a quest."),
        QAItem("Why can waves be a problem?", "Waves can splash people, knock things over, and make a careful job harder. That is why a steady plan matters."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("atlantic_dock", "wave_kid", "beacon", "fog", "slow_map"),
    StoryParams("atlantic_lighthouse", "caped_mini", "lantern_key", "seagulls", "signal_glove"),
    StoryParams("atlantic_boat", "wave_kid", "beacon", "waves", "rope_bridge"),
]


ASP_RULES = r"""
valid(S, I, O, F) :- setting(S), item(I), obstacle(O), fix(F),
    reason_ok(S, I), beats(F, O).
reason_ok(S, I) :- atlantic(S), vulnerable(I).
beats(F, O) :- power(F, P), danger(O, D), P >= D.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("atlantic", sid))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if i.vulnerable:
            lines.append(asp.fact("vulnerable", iid))
    for oid, o in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("danger", oid, {"fog": 2, "waves": 3, "seagulls": 1}[oid]))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, f.power))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid combos differ.")
    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generation smoke test failed: {e}")
    else:
        print("OK: smoke test passed and story generation works.")
    return rc


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible quest combos:\n")
        for c in combos:
            print("  ", c)
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
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        header = ""
        if args.all:
            p = s.params
            header = f"### {p.setting} / {p.item} / {p.obstacle} / {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
