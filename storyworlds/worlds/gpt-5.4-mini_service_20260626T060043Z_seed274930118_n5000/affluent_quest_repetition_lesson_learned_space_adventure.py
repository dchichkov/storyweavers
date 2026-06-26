#!/usr/bin/env python3
"""
A standalone storyworld for an affluent space adventure: a young explorer on a
small quest, a repeated mistake, and a lesson learned that changes the ending.

The world is built around a luxurious starliner and a careful little mission.
The hero wants to reach a distant observatory, but repetition matters: trying
the same flashy shortcut twice makes the same problem worse. The lesson learned
is that speed is not the same as success; listening, checking, and using the
right tool wins the quest.

This script follows the Storyweavers storyworld contract:
- one self-contained stdlib script
- results.py imported eagerly
- asp.py imported lazily inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot", "boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    id: str
    label: str
    indoors: bool
    lux: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    shortcut: str
    risk: str
    tag: str
    place_hint: str
    demands: set[str] = field(default_factory=set)
    rewards: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    guards: set[str]
    tags: set[str]
    covers: set[str]
    plural: bool = False


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.location)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _safe_meters(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _safe_memes(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _set_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = value


def _inc_meter(ent: Entity, key: str, delta: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _inc_meme(ent: Entity, key: str, delta: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if _safe_memes(hero, "stuck") < THRESHOLD:
        return out
    sig = ("repeat", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _inc_memes(hero, "frustration", 1.0)
    out.append("The same mistake was beginning to feel bigger the second time.")
    return out


def _r_tool_fix(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    tool = world.entities.get("tool")
    if not hero or not tool:
        return out
    if _safe_memes(hero, "planning") < THRESHOLD:
        return out
    if _safe_memes(hero, "frustration") < THRESHOLD:
        return out
    sig = ("tool_fix", hero.id, tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _set_meter(tool, "ready", 1.0)
    out.append("With a careful plan, the right tool finally became useful.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if _safe_memes(hero, "insight") >= THRESHOLD:
        return out
    if _safe_memes(hero, "frustration") < THRESHOLD:
        return out
    sig = ("lesson", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _inc_meme(hero, "insight", 1.0)
    _set_meter(hero, "calm", 1.0)
    out.append("The hero learned that rushing twice is still rushing.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    rules = [_r_repeat, _r_tool_fix, _r_lesson]
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in rules:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def setting_detail(location: Location, quest: Quest) -> str:
    if location.indoors:
        return f"Inside {location.label}, polished rails glowed like silver stars."
    return f"{location.label.capitalize()} shimmered under a wide black sky."


def quest_risk_text(quest: Quest) -> str:
    return {
        "drift": "the ship drifted off course",
        "lockout": "the door would stay sealed",
        "signal": "the beacon would fade",
        "shortage": "the supplies would run low",
    }.get(quest.risk, "the mission would get harder")


def _do_attempt(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    if quest.id not in world.location.affords:
        raise StoryError("This location cannot host that quest.")
    _inc_meme(hero, "stuck", 1.0)
    _inc_meter(hero, "effort", 1.0)
    propagate(world, narrate=narrate)


def introduction(world: World, hero: Entity, adult: Entity, quest: Quest, reward: Entity) -> None:
    wealth_word = "affluent"
    world.say(
        f"{hero.id} lived on an {wealth_word} starliner where the hallways were bright and clean."
    )
    world.say(
        f"{hero.id} loved the little quest to {quest.verb}, because the reward was {reward.phrase}."
    )
    world.say(
        f"{adult.label.capitalize()} had bought {hero.pronoun('object')} the {reward.label} for the journey."
    )


def setup(world: World, hero: Entity, adult: Entity, quest: Quest, reward: Entity) -> None:
    world.para()
    world.say(setting_detail(world.location, quest))
    world.say(
        f"One day, {hero.id} and {adult.label} went to {world.location.label} for the mission."
    )
    world.say(
        f"{hero.id} wanted to {quest.verb}, but the path to the {quest.place_hint} was tricky."
    )
    _inc_meme(hero, "desire", 1.0)


def warning(world: World, hero: Entity, adult: Entity, quest: Quest, reward: Entity) -> None:
    hero.memes["planning"] = hero.memes.get("planning", 0.0)
    world.say(
        f'"If you take the {quest.shortcut}, {reward.label} could get {quest.risk}," '
        f"{adult.label} said."
    )
    world.say(
        f'"Then {quest_risk_text(quest)}," {adult.label} added, "so let us be careful."'
    )


def first_try(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"But {hero.id} hurried anyway and tried to {quest.shortcut}."
    )
    _do_attempt(world, hero, quest, narrate=False)
    world.say(
        f"The first try did not work, and {hero.id} felt the ship's quiet lights watch closely."
    )


def second_try(world: World, hero: Entity, quest: Quest, tool: Entity) -> None:
    _inc_meme(hero, "frustration", 1.0)
    world.say(
        f"So {hero.id} tried the very same shortcut again, hoping speed would help."
    )
    _do_attempt(world, hero, quest, narrate=True)
    if _safe_meters(tool, "ready") >= THRESHOLD:
        world.say(
            f"This time, {hero.id} stopped, used the {tool.label}, and followed the safe route."
        )


def resolve(world: World, hero: Entity, adult: Entity, quest: Quest, reward: Entity, tool: Entity) -> None:
    if _safe_memes(hero, "insight") < THRESHOLD:
        _inc_meme(hero, "insight", 1.0)
    world.say(
        f"{hero.id} finally understood that repeating a mistake does not make it smarter."
    )
    world.say(
        f"With {adult.label}'s help and the {tool.label}, {hero.id} reached the {quest.place_hint}."
    )
    world.say(
        f"At the end of the quest, {hero.id} held the {reward.label}, and the ship stayed safe and bright."
    )


def build_world(location: Location, quest: Quest, reward: RewardSpec, hero_name: str, hero_type: str,
                adult_type: str, trait: str) -> World:
    world = World(location)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        traits=[trait, "curious"],
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=adult_type,
        label="captain",
        traits=["careful", "patient"],
    ))
    reward_ent = world.add(Entity(
        id="reward",
        kind="thing",
        type=reward.type,
        label=reward.label,
        phrase=reward.phrase,
        owner=hero.id,
        caretaker=adult.id,
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=reward.tool_label,
        phrase=reward.tool_phrase,
        owner=hero.id,
        caretaker=adult.id,
        plural=reward.plural,
    ))

    introduction(world, hero, adult, quest, reward_ent)
    setup(world, hero, adult, quest, reward_ent)
    warning(world, hero, adult, quest, reward_ent)
    first_try(world, hero, quest)
    world.para()
    second_try(world, hero, quest, tool)
    resolve(world, hero, adult, quest, reward_ent, tool)

    world.facts = {
        "hero": hero,
        "adult": adult,
        "reward": reward_ent,
        "tool": tool,
        "quest": quest,
        "location": location,
        "trait": trait,
    }
    return world


@dataclass
class RewardSpec:
    label: str
    phrase: str
    type: str
    tool_label: str
    tool_phrase: str
    plural: bool = False


LOCATIONS = {
    "starliner": Location(
        id="starliner",
        label="the starliner",
        indoors=True,
        lux="affluent",
        affords={"quest",
                 "signal"},
    ),
    "observatory": Location(
        id="observatory",
        label="the observatory",
        indoors=True,
        lux="affluent",
        affords={"quest", "lockout"},
    ),
    "dock": Location(
        id="dock",
        label="the moon dock",
        indoors=False,
        lux="affluent",
        affords={"quest", "drift", "signal"},
    ),
}

QUESTS = {
    "quest": Quest(
        id="quest",
        verb="finish the quest",
        gerund="finishing the quest",
        shortcut="dash through the glittering side passage",
        risk="lockout",
        tag="quest",
        place_hint="old observatory",
        demands={"key"},
        rewards={"map"},
    ),
    "signal": Quest(
        id="signal",
        verb="send the beacon signal",
        gerund="sending the beacon signal",
        shortcut="press the bright button twice",
        risk="signal",
        tag="signal",
        place_hint="signal tower",
        demands={"antenna"},
        rewards={"signal"},
    ),
    "drift": Quest(
        id="drift",
        verb="guide the pod home",
        gerund="guiding the pod home",
        shortcut="cut the course through the blue dust",
        risk="drift",
        tag="drift",
        place_hint="home port",
        demands={"chart"},
        rewards={"pod"},
    ),
}

REWARDS = {
    "map": RewardSpec(
        label="star map",
        phrase="a star map with golden edges",
        type="map",
        tool_label="navigation compass",
        tool_phrase="a navigation compass",
    ),
    "signal": RewardSpec(
        label="beacon crystal",
        phrase="a beacon crystal in a velvet case",
        type="crystal",
        tool_label="quiet antenna",
        tool_phrase="a quiet antenna",
    ),
    "pod": RewardSpec(
        label="return pod",
        phrase="a tiny return pod with a red seat",
        type="pod",
        tool_label="course chart",
        tool_phrase="a course chart",
    ),
}

TRAITS = ["brave", "curious", "gentle", "cheerful", "careful"]

GIRL_NAMES = ["Nova", "Mira", "Luna", "Iris", "Aria"]
BOY_NAMES = ["Orion", "Finn", "Theo", "Jace", "Kai"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for lid, loc in LOCATIONS.items():
        for qid in loc.affords:
            if qid in QUESTS:
                for rid in REWARDS:
                    combos.append((lid, qid, rid))
    return combos


@dataclass
class StoryParams:
    location: str
    quest: str
    reward: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "affluent": [
        ("What does affluent mean?",
         "Affluent means having a lot of money or valuable things, so life can feel comfortable and rich."),
    ],
    "quest": [
        ("What is a quest?",
         "A quest is a special trip or mission to get something or solve a problem."),
    ],
    "repetition": [
        ("What is repetition?",
         "Repetition means doing the same thing again and again."),
    ],
    "lesson": [
        ("What is a lesson learned?",
         "A lesson learned is a helpful idea someone understands after experience, so they can do better next time."),
    ],
    "space": [
        ("What is outer space?",
         "Outer space is the huge area beyond Earth where stars, planets, and spacecraft are found."),
    ],
    "signal": [
        ("What is a beacon?",
         "A beacon is a bright sign or signal that helps people find a place or know where to go."),
    ],
    "map": [
        ("What does a map do?",
         "A map shows where things are and helps someone find the right path."),
    ],
    "pod": [
        ("What is a pod?",
         "A pod is a small enclosed vehicle or capsule."),
    ],
    "drift": [
        ("What does drift mean in space?",
         "Drift means to move slowly without enough control, like a ship sliding away from its path."),
    ],
}
KNOWLEDGE_ORDER = ["affluent", "quest", "repetition", "lesson", "space", "signal", "map", "pod", "drift"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly space adventure story that uses the word "affluent" and includes a quest.',
        f"Tell a story about {f['hero'].label} on the {f['location'].label} where a repeated mistake leads to a lesson learned.",
        f"Write a short space story where a careful adult and a curious child choose a safer way after trying the same shortcut twice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    adult: Entity = f["adult"]
    reward: Entity = f["reward"]
    quest: Quest = f["quest"]
    location: Location = f["location"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, a {hero.traits[0]} {hero.type} on an {location.lux} space journey.",
        ),
        QAItem(
            question=f"What did {hero.label} want to do?",
            answer=f"{hero.label} wanted to {quest.verb} and bring home {reward.phrase}.",
        ),
        QAItem(
            question=f"What happened when {hero.label} tried the shortcut again?",
            answer=f"{hero.label} repeated the same shortcut, got more frustrated, and then learned to use the safer way instead.",
        ),
        QAItem(
            question=f"Why did the adult worry about the shortcut?",
            answer=f"{adult.label} worried because taking the shortcut could cause {quest_risk_text(quest)}.",
        ),
        QAItem(
            question=f"What was the lesson learned at the end?",
            answer="The lesson learned was that repeating a mistake does not fix it; careful steps and the right tool do.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {"affluent", "quest", "repetition", "lesson", "space"}
    tags.add(world.facts["quest"].tag)
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- entity(H), kind(H,character).
adult(A) :- entity(A), kind(A,character).
repeated(H) :- stuck(H, N), N >= 2.
lesson_learned(H) :- frustration(H, F), F >= 1, insight(H, I), I >= 1.
safe_finish(H) :- lesson_learned(H), tool_ready(tool), quest_done(H).
risk(quest, lockout).
risk(signal, signal).
risk(drift, drift).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        if loc.indoors:
            lines.append(asp.fact("indoors", lid))
        for a in sorted(loc.affords):
            lines.append(asp.fact("affords", lid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("risk_of", qid, q.risk))
    for rid in REWARDS:
        lines.append(asp.fact("reward", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show risk_of/2."))
    asp_risks = sorted(set(asp.atoms(model, "risk_of")))
    py_risks = sorted((qid, q.risk) for qid, q in QUESTS.items())
    if asp_risks == py_risks:
        print(f"OK: clingo gate matches quest risks ({len(py_risks)} quests).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  clingo:", asp_risks)
    print("  python:", py_risks)
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show afford/2."))
    return sorted(set(asp.atoms(model, "affords")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Affluent space adventure storyworld.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["captain", "parent"])
    ap.add_argument("--name")
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
              if (args.location is None or c[0] == args.location)
              and (args.quest is None or c[1] == args.quest)
              and (args.reward is None or c[2] == args.reward)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    location, quest, reward = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(location=location, quest=quest, reward=reward, name=name, gender=gender, adult=adult, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(
        LOCATIONS[params.location],
        QUESTS[params.quest],
        REWARDS[params.reward],
        params.name,
        "girl" if params.gender == "girl" else "boy",
        "captain",
        params.trait,
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


CURATED = [
    StoryParams(location="starliner", quest="quest", reward="map", name="Nova", gender="girl", adult="captain", trait="curious"),
    StoryParams(location="observatory", quest="quest", reward="map", name="Orion", gender="boy", adult="captain", trait="careful"),
    StoryParams(location="dock", quest="drift", reward="pod", name="Mira", gender="girl", adult="captain", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show risk_of/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show risk_of/2."))
        risks = sorted(set(asp.atoms(model, "risk_of")))
        print(f"{len(risks)} quest risks:\n")
        for qid, risk in risks:
            print(f"  {qid}: {risk}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.quest} at {p.location} (reward: {p.reward})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
