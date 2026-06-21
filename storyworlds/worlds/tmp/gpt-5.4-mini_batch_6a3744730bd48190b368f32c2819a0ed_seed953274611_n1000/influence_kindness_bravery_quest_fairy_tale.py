#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/influence_kindness_bravery_quest_fairy_tale.py
==============================================================================

A small fairy-tale storyworld about an influence that can bend a quest one way
or another: a kind act gives courage, a brave choice changes the path, and a
quest ends with a gift or a lesson.

The world simulates:
- a child or young hero on a quest,
- a helpful companion or elder,
- an influence token (charm, whisper, song, or rumor),
- a vulnerable goal (a gate, bridge, grove, or tower),
- two core forces: kindness and bravery.

If the influence is kind, it helps the hero choose a gentler, braver path.
If it is unkind, the hero may still finish the quest, but with more fear and a
harder turn. The story always reads as a complete fairy tale with a beginning,
turn, and ending image proving what changed.
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "fairy", "woman"}
        male = {"boy", "father", "king", "knight", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    hush: str
    light: str
    quest_site: str


@dataclass
class HeroCfg:
    id: str
    title: str
    type: str
    goal: str
    courage_start: float = 3.0


@dataclass
class InfluenceCfg:
    id: str
    label: str
    kind: str  # kind | unkind
    whisper: str
    effect: str
    omen: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuestCfg:
    id: str
    name: str
    path: str
    prize: str
    risk: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CompanionCfg:
    id: str
    title: str
    type: str
    advice: str
    helper: str


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


def _r_influence(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    infl = world.get("influence")
    if hero.meters["influenced"] < THRESHOLD:
        return out
    sig = ("influence",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if infl.attrs.get("kind") == "kind":
        hero.memes["kindness"] += 1
        hero.memes["bravery"] += 1
        out.append("__soft__")
    else:
        hero.memes["fear"] += 1
        out.append("__sharp__")
    return out


def _r_quest(world: World) -> list[str]:
    hero = world.get("hero")
    quest = world.get("quest")
    if hero.memes["bravery"] < THRESHOLD:
        return []
    sig = ("quest",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    quest.meters["progress"] += 1
    return [f"{hero.id} took one brave step along the quest path."]


CAUSAL_RULES = [Rule("influence", _r_influence), Rule("quest", _r_quest)]


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


def influence_safe(cfg: InfluenceCfg) -> bool:
    return cfg.kind in {"kind", "unkind"}


def quest_viable(quest: QuestCfg) -> bool:
    return bool(quest.path and quest.prize and quest.ending_image)


def outcome_score(infl: InfluenceCfg, quest: QuestCfg) -> int:
    return 2 if infl.kind == "kind" else 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for iid, infl in INFLUENCES.items():
            for qid, quest in QUESTS.items():
                if influence_safe(infl) and quest_viable(quest):
                    combos.append((sid, iid, qid))
    return combos


def predict(world: World, infl: InfluenceCfg) -> dict:
    sim = world.copy()
    sim.get("hero").meters["influenced"] += 1
    sim.get("influence").attrs["kind"] = infl.kind
    propagate(sim, narrate=False)
    return {
        "bravery": sim.get("hero").memes["bravery"],
        "kindness": sim.get("hero").memes["kindness"],
        "progress": sim.get("quest").meters["progress"],
    }


def introduce(world: World, setting: Setting, hero: Entity, comp: Entity) -> None:
    hero.memes["kindness"] += 1
    world.say(
        f"Once upon a time, in {setting.place}, {hero.id} lived under a {setting.mood} sky. "
        f"{comp.id} was there too, and the {setting.light} made everything look like a promise."
    )


def call_quest(world: World, hero: Entity, quest: QuestCfg, comp: Entity) -> None:
    world.say(
        f"{hero.id} longed for {quest.name}. {comp.id} spoke softly: \"{comp.attrs['advice']}\" "
        f"Their path led toward {quest.path}, where {quest.risk} waited."
    )


def meet_influence(world: World, infl: InfluenceCfg, quest: QuestCfg) -> None:
    world.say(
        f"Then came {infl.label}, a little influence that {infl.whisper}. "
        f"It left behind {infl.effect} and a tiny omen of {infl.omen} near the quest site."
    )


def choose(world: World, hero: Entity, infl: InfluenceCfg, comp: Entity, quest: QuestCfg) -> None:
    hero.meters["influenced"] += 1
    hero.memes["bravery"] += 1 if infl.kind == "kind" else 0
    hero.memes["fear"] += 0 if infl.kind == "kind" else 1
    world.say(
        f"{hero.id} looked at {comp.id}, and {comp.id} showed {comp.attrs['helper']}. "
        f"That small kindness gave {hero.id} enough courage to keep going."
    )


def resolve(world: World, hero: Entity, quest: QuestCfg, infl: InfluenceCfg, setting: Setting) -> None:
    if infl.kind == "kind":
        world.say(
            f"{hero.id} finished the quest with a brave heart. At last, {quest.ending_image}, "
            f"and the whole {setting.place} felt warmer for it."
        )
    else:
        world.say(
            f"{hero.id} still finished the quest, but the road felt colder and harder. "
            f"At last, {quest.ending_image}, and {hero.id} remembered to choose kinder words next time."
        )


def tell(setting: Setting, hero_cfg: HeroCfg, infl: InfluenceCfg, quest: QuestCfg, comp_cfg: CompanionCfg) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_cfg.type, label=hero_cfg.title))
    comp = world.add(Entity(id="companion", kind="character", type=comp_cfg.type, label=comp_cfg.title))
    influence = world.add(Entity(id="influence", type="thing", label=infl.label, attrs={"kind": infl.kind}))
    quest_ent = world.add(Entity(id="quest", type="thing", label=quest.name))
    hero.memes["bravery"] = hero_cfg.courage_start
    comp.attrs["advice"] = comp_cfg.advice
    comp.attrs["helper"] = comp_cfg.helper
    world.facts.update(setting=setting, hero_cfg=hero_cfg, infl=infl, quest=quest, comp_cfg=comp_cfg)
    introduce(world, setting, hero, comp)
    world.para()
    call_quest(world, hero, quest, comp)
    meet_influence(world, infl, quest)
    choose(world, hero, infl, comp, quest)
    propagate(world, narrate=True)
    world.para()
    resolve(world, hero, quest, infl, setting)
    world.facts.update(
        hero=hero, companion=comp, influence=influence, quest=quest_ent,
        outcome="kind" if infl.kind == "kind" else "mixed"
    )
    return world


SETTINGS = {
    "forest": Setting(id="forest", place="the whispering forest", mood="green",
                      hush="quiet", light="golden", quest_site="mossy stones"),
    "castle": Setting(id="castle", place="the old castle garden", mood="moonlit",
                      hush="still", light="silver", quest_site="ivy arch"),
    "meadow": Setting(id="meadow", place="the bright meadow", mood="sunny",
                      hush="gentle", light="soft", quest_site="rose hill"),
}

HEROS = {
    "girl": HeroCfg(id="girl", title="Ella", type="girl", goal="a better path", courage_start=3.0),
    "boy": HeroCfg(id="boy", title="Owen", type="boy", goal="a better path", courage_start=3.0),
}

INFLUENCES = {
    "kind_charm": InfluenceCfg(id="kind_charm", label="a kind charm", kind="kind",
                               whisper="made everyone share what they knew",
                               effect="a glow of good cheer", omen="a white feather",
                               tags={"influence", "kindness"}),
    "brave_song": InfluenceCfg(id="brave_song", label="a brave song", kind="kind",
                               whisper="made even shy hearts stand taller",
                               effect="a ringing note of courage", omen="a bellflower",
                               tags={"influence", "bravery"}),
    "cold_rumor": InfluenceCfg(id="cold_rumor", label="a cold rumor", kind="unkind",
                               whisper="made the shadows seem larger",
                               effect="a chill across the path", omen="a snapped twig",
                               tags={"influence"}),
}

QUESTS = {
    "bridge": QuestCfg(id="bridge", name="the silver bridge", path="the river gate",
                       prize="a lost key", risk="the river below",
                       ending_image="the silver bridge shone under their feet",
                       tags={"quest"}),
    "tower": QuestCfg(id="tower", name="the ivy tower", path="the spiral stair",
                      prize="a sleeping bell", risk="the high dark wind",
                      ending_image="the ivy tower window opened at last",
                      tags={"quest"}),
    "grove": QuestCfg(id="grove", name="the secret grove", path="the thorny lane",
                      prize="a moonlit flower", risk="the thorn hedge",
                      ending_image="the moonlit flower blinked awake",
                      tags={"quest"}),
}

COMPANIONS = {
    "fairy": CompanionCfg(id="fairy", title="Maribel", type="fairy",
                          advice="Kindness can be a lantern on the darkest road.",
                          helper="a basket of flowers for the gatekeeper"),
    "elder": CompanionCfg(id="elder", title="Grandmama Rose", type="woman",
                          advice="Bravery is not being loud; it is taking the next step.",
                          helper="a calm hand and a steady smile"),
    "knight": CompanionCfg(id="knight", title="Sir Rowan", type="knight",
                           advice="A brave heart should still be gentle.",
                           helper="a shield polished like moonlight"),
}


@dataclass
class StoryParams:
    setting: str
    hero: str
    influence: str
    quest: str
    companion: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about influence, kindness, bravery, and a quest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROS)
    ap.add_argument("--influence", choices=INFLUENCES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--companion", choices=COMPANIONS)
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
    if args.influence and args.influence not in INFLUENCES:
        raise StoryError("Unknown influence.")
    if args.quest and args.quest not in QUESTS:
        raise StoryError("Unknown quest.")
    choices = [c for c in valid_combos()
               if (args.setting is None or c[0] == args.setting)
               and (args.hero is None or c[1] == args.hero)
               and (args.influence is None or c[1] == c[1])
               and (args.quest is None or c[2] == args.quest)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hero, quest = rng.choice(sorted(choices))
    infl = args.influence or rng.choice(sorted(INFLUENCES))
    comp = args.companion or rng.choice(sorted(COMPANIONS))
    return StoryParams(setting=setting, hero=hero, influence=infl, quest=quest, companion=comp)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story that includes the word "influence" and shows {f["hero_cfg"].title} choosing kindness on a quest.',
        f"Tell a gentle story where {f['hero_cfg'].title} is swayed by an influence, but bravery and kindness help finish the quest.",
        f"Write a child-facing fairy tale about influence, kindness, bravery, and a quest with a bright ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    infl = f["infl"]
    setting = f["setting"]
    return [
        QAItem(
            question="Who was on the quest?",
            answer=f"{hero.title} was on the quest, with a companion nearby to help. The story followed {hero.title} from the beginning through the final moment."
        ),
        QAItem(
            question="How did the influence change the story?",
            answer=f"The influence nudged the hero toward either a kinder or colder choice, and that changed how much bravery the hero carried forward. Because the choice mattered, the quest felt different from start to finish."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {quest.ending_image}. That ending image proves the quest was finished in {setting.place}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helping others, and choosing words or actions that do not hurt."
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the next right thing even when you feel a little scared."
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey with a goal, like finding something, helping someone, or reaching a special place."
        ),
    ]


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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.attrs:
            bits.append(f"attrs={ {k: v for k, v in e.attrs.items() if v} }")
        out.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
influence_kind(kind_charm).
influence_kind(brave_song).
quest_good(bridge).
quest_good(tower).
quest_good(grove).
valid(S,H,I,Q) :- setting(S), hero(H), influence(I), quest(Q), influence_kind(I), quest_good(Q).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for h in HEROS:
        lines.append(asp.fact("hero", h))
    for i in INFLUENCES:
        lines.append(asp.fact("influence", i))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        print("MISMATCH: ASP gate differs from Python.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, hero=None, influence=None, quest=None, companion=None), random.Random(1)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams(setting="forest", hero="girl", influence="kind_charm", quest="bridge", companion="fairy", seed=1),
    StoryParams(setting="castle", hero="boy", influence="brave_song", quest="tower", companion="knight", seed=2),
    StoryParams(setting="meadow", hero="girl", influence="cold_rumor", quest="grove", companion="elder", seed=3),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.hero not in HEROS or params.influence not in INFLUENCES or params.quest not in QUESTS or params.companion not in COMPANIONS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], HEROS[params.hero], INFLUENCES[params.influence], QUESTS[params.quest], COMPANIONS[params.companion])
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(" ".join(map(str, row)) for row in asp_valid_combos()))
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = [generate(p) for p in CURATED] if args.all else []
    if not samples:
        for i in range(args.n):
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
