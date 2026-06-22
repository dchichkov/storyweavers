#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T011547Z_seed2023889374_n10/earn_story_foreshadowing_transformation_suspense_adventure.py
===============================================================================================================================

A small adventure storyworld about earning a storybook prize, with foreshadowing,
transformation, and suspense. The world tracks typed entities with physical
meters and emotional memes, simulates a short quest, and renders a child-facing
story from the state changes.

Seed prompt:
---
Write a story that includes the following words and narrative instruments.
Words: earn, story
Features: Foreshadowing, Transformation, Suspense
Style: Adventure
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    paths: list[str] = field(default_factory=list)
    hazard_labels: list[str] = field(default_factory=list)


@dataclass
class Quest:
    id: str
    thing: str
    place: str
    reward: str
    clue: str
    transformation: str
    suspense: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Keeper:
    id: str
    type: str
    label: str
    help_word: str
    rescue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    quest: str
    keeper: str
    hero: str
    hero_gender: str
    guide: str
    guide_gender: str
    seed: Optional[int] = None


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
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    quest = world.facts["quest_cfg"]
    signal = world.get("signal")
    if hero.memes.get("worry", 0.0) < THRESHOLD:
        return out
    sig = ("suspense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    signal.meters["glow"] = 1.0
    out.append(f"A faint glow hid near the path, like a clue waiting for the right pair of eyes.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    staff = world.get("staff")
    if hero.memes.get("courage", 0.0) < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    staff.attrs["transformed"] = True
    staff.label = "trail staff"
    staff.meters["lit"] = 1.0
    out.append(f"The plain stick in {hero.id}'s hand seemed to wake up and become a trail staff.")
    return out


CAUSAL_RULES = [
    Rule("suspense", _r_suspense),
    Rule("transform", _r_transform),
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


SETTING_REGISTRY = {
    "cave": Setting(
        id="cave",
        label="the cave",
        paths=["a narrow path", "a low tunnel"],
        hazard_labels=["dark water", "echoing stones"],
    ),
    "jungle": Setting(
        id="jungle",
        label="the jungle",
        paths=["a vine bridge", "a root path"],
        hazard_labels=["thick vines", "muddy turns"],
    ),
    "harbor": Setting(
        id="harbor",
        label="the harbor",
        paths=["a dock lane", "a rope walkway"],
        hazard_labels=["slippery boards", "creaking ropes"],
    ),
}

QUEST_REGISTRY = {
    "map": Quest(
        id="map",
        thing="the lost map",
        place="under a stone arch",
        reward="the map would earn them the next clue",
        clue="a silver mark on the wall",
        transformation="the paper map would unfold into a bigger path",
        suspense="they could hear water behind the wall",
        tags={"map", "story"},
    ),
    "crown": Quest(
        id="crown",
        thing="the small crown",
        place="inside a root hollow",
        reward="the crown would earn a place in the storybook chest",
        clue="a gold glint between roots",
        transformation="the crown would change into a brighter, kinder sign",
        suspense="something moved in the leaves nearby",
        tags={"crown", "story"},
    ),
    "shell": Quest(
        id="shell",
        thing="the blue shell",
        place="at the end of the dock",
        reward="the shell would earn a turn in the story game",
        clue="a blue flash under a coil of rope",
        transformation="the shell would turn into a small compass",
        suspense="the tide was rising fast",
        tags={"shell", "story"},
    ),
}

KEEPER_REGISTRY = {
    "librarian": Keeper(
        id="librarian",
        type="adult",
        label="the librarian",
        help_word="helpful",
        rescue="guided them back with a lantern",
        tags={"book", "story"},
    ),
    "gardener": Keeper(
        id="gardener",
        type="adult",
        label="the gardener",
        help_word="steady",
        rescue="moved the vines aside and pointed to safety",
        tags={"leaf", "story"},
    ),
    "sailor": Keeper(
        id="sailor",
        type="adult",
        label="the sailor",
        help_word="calm",
        rescue="showed them how to keep their balance",
        tags={"rope", "story"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Finn", "Owen", "Eli", "Theo", "Leo"]
GUIDE_NAMES = ["Pip", "June", "Rae", "Milo", "Bea"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTING_REGISTRY:
        for qid in QUEST_REGISTRY:
            for kid in KEEPER_REGISTRY:
                if qid == "map" and sid == "cave" and kid == "librarian":
                    combos.append((sid, qid, kid))
                elif qid == "crown" and sid == "jungle" and kid == "gardener":
                    combos.append((sid, qid, kid))
                elif qid == "shell" and sid == "harbor" and kid == "sailor":
                    combos.append((sid, qid, kid))
    return combos


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTING_REGISTRY:
        lines.append(asp.fact("setting", sid))
    for qid in QUEST_REGISTRY:
        lines.append(asp.fact("quest", qid))
    for kid in KEEPER_REGISTRY:
        lines.append(asp.fact("keeper", kid))
    lines.append(asp.fact("compatible", "cave", "map", "librarian"))
    lines.append(asp.fact("compatible", "jungle", "crown", "gardener"))
    lines.append(asp.fact("compatible", "harbor", "shell", "sailor"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,Q,K) :- compatible(S,Q,K).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def reasonableness_gate(params: StoryParams) -> bool:
    return (params.setting, params.quest, params.keeper) in valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld: a child earns a story through suspense and change."
    )
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--quest", choices=QUEST_REGISTRY)
    ap.add_argument("--keeper", choices=KEEPER_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.keeper is None or c[2] == args.keeper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, keeper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    guide_gender = args.guide_gender or ("boy" if gender == "girl" else "girl")
    guide = args.guide or rng.choice([n for n in GUIDE_NAMES if n != name])
    return StoryParams(setting=setting, quest=quest, keeper=keeper,
                       hero=name, hero_gender=gender, guide=guide,
                       guide_gender=guide_gender)


def _setup_world(params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero,
                        role="hero", traits=["bold"], attrs={}, meters={"progress": 0.0},
                        memes={"hope": 1.0, "worry": 0.0, "courage": 0.0, "joy": 0.0}))
    guide = w.add(Entity(id="guide", kind="character", type=params.guide_gender, label=params.guide,
                         role="guide", traits=["quick"], attrs={}, meters={}, memes={"worry": 0.0}))
    keeper = w.add(Entity(id="keeper", kind="character", type="adult", label=KEEPER_REGISTRY[params.keeper].label,
                          role="keeper", attrs={}, meters={}, memes={"calm": 1.0}))
    signal = w.add(Entity(id="signal", type="thing", label="signal stone", attrs={"seen": False},
                          meters={"glow": 0.0}, memes={}))
    staff = w.add(Entity(id="staff", type="thing", label="plain stick", attrs={"transformed": False},
                         meters={"lit": 0.0}, memes={}))
    world = w
    world.facts["setting_cfg"] = SETTING_REGISTRY[params.setting]
    world.facts["quest_cfg"] = QUEST_REGISTRY[params.quest]
    world.facts["keeper_cfg"] = KEEPER_REGISTRY[params.keeper]
    world.facts["hero"] = hero
    world.facts["guide"] = guide
    world.facts["keeper_ent"] = keeper
    world.facts["signal"] = signal
    world.facts["staff"] = staff
    return world


def tell(params: StoryParams) -> World:
    if not reasonableness_gate(params):
        raise StoryError("Invalid adventure combination.")
    w = _setup_world(params)
    setting = w.facts["setting_cfg"]
    quest = w.facts["quest_cfg"]
    keeper = w.facts["keeper_cfg"]
    hero = w.get("hero")
    guide = w.get("guide")
    staff = w.get("staff")
    signal = w.get("signal")

    hero.memes["hope"] += 1
    guide.memes["worry"] += 1
    w.say(
        f"{hero.id} and {guide.id} set out into {setting.label}, chasing a small adventure."
    )
    w.say(
        f"They were after {quest.thing}, because it could {quest.reward}; that was the story they meant to earn."
    )
    w.say(
        f"At first, {quest.clue} flashed ahead like a promise, but {quest.suspense}."
    )
    w.para()
    hero.memes["worry"] += 1
    w.say(
        f"{guide.id} paused and whispered that the path felt strange."
    )
    propagate(w, narrate=True)
    hero.memes["courage"] += 1
    staff.meters["held"] = 1.0
    w.say(
        f"{hero.id} lifted the plain stick and stepped forward anyway."
    )
    w.say(
        f"That brave step made {quest.transformation}, and the little sign seemed to change shape."
    )
    w.para()
    signal.attrs["seen"] = True
    hero.meters["progress"] = 1.0
    w.say(
        f"Then {quest.place} came into view."
    )
    w.say(
        f"{hero.id} reached for {quest.thing}, and {keeper.label} appeared just in time, {keeper.rescue}."
    )
    hero.memes["joy"] += 1
    hero.memes["worry"] = 0.0
    w.say(
        f"The last piece clicked into place: {quest.thing} was found, the path was safe, and the story was finally theirs to keep."
    )
    w.say(
        f"{hero.id} had earned a real story, one full of suspense and change."
    )
    w.facts.update(
        setting=setting, quest=quest, keeper=keeper, hero=hero, guide=guide,
        outcome="earned", signal=signal, staff=staff,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest_cfg"]
    return [
        f"Write an adventure story where {hero.id} must earn {quest.thing} and the word story appears naturally.",
        f"Tell a suspenseful tale in which a child named {hero.id} follows clues, faces a change, and earns a story prize.",
        f"Write a small adventure with foreshadowing, transformation, and suspense that includes the words earn and story.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    quest = f["quest_cfg"]
    setting = f["setting_cfg"]
    keeper = f["keeper_cfg"]
    return [
        QAItem(
            question=f"What adventure did {hero.id} and {guide.id} go on?",
            answer=f"They went on a small quest through {setting.label} to find {quest.thing}. It began as a careful adventure and turned into a brave one.",
        ),
        QAItem(
            question=f"Why did {hero.id} keep going even when the path felt strange?",
            answer=f"{hero.id} wanted to earn {quest.reward}. The clue and the strange feeling created suspense, but courage let {hero.id} keep moving.",
        ),
        QAItem(
            question=f"What changed when {hero.id} picked up the plain stick?",
            answer=f"The plain stick transformed into a trail staff. That change helped the adventure feel bigger and made the next step possible.",
        ),
        QAItem(
            question=f"How did {keeper.label} help at the end?",
            answer=f"{keeper.label.capitalize()} arrived in time and {keeper.rescue}. That help kept the ending safe after the suspenseful climb.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    quest = f["quest_cfg"]
    tags = set(quest.tags)
    out: list[QAItem] = []
    if "story" in tags:
        out.append(QAItem(
            question="What is a story?",
            answer="A story is a set of events that are told in order. It can have a beginning, a middle, and an ending.",
        ))
    out.append(QAItem(
        question="What does it mean to earn something?",
        answer="To earn something means to get it by trying hard, being careful, or doing a good job. You do not just grab it without effort.",
    ))
    out.append(QAItem(
        question="What is suspense in a story?",
        answer="Suspense is the feeling that makes you wonder what will happen next. It keeps you waiting and paying attention.",
    ))
    out.append(QAItem(
        question="What is foreshadowing?",
        answer="Foreshadowing is a small hint that something important may happen later. It helps the reader notice clues before the big moment.",
    ))
    out.append(QAItem(
        question="What is transformation?",
        answer="Transformation means something changes into a new form or state. In a story, that change can make the ending feel special.",
    ))
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="cave", quest="map", keeper="librarian", hero="Lina", hero_gender="girl", guide="Pip", guide_gender="boy"),
    StoryParams(setting="jungle", quest="crown", keeper="gardener", hero="Finn", hero_gender="boy", guide="June", guide_gender="girl"),
    StoryParams(setting="harbor", quest="shell", keeper="sailor", hero="Nora", hero_gender="girl", guide="Rae", guide_gender="girl"),
]


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


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("MISMATCH: smoke test story was empty.")
            return 1
        print("OK: smoke test generation succeeded.")
        return 0
    print("MISMATCH in combo parity:")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
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
