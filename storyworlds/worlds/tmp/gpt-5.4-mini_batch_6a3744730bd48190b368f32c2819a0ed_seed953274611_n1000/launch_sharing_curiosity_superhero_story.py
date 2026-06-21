#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/launch_sharing_curiosity_superhero_story.py
===========================================================================

A small superhero-flavored storyworld about a curious child, a shared launch,
and a calm grown-up rescue. The seed word is "launch"; the two core features are
sharing and curiosity.

The premise is simple: a child wants to launch a homemade hero gadget into the
sky, but curiosity makes them want to tinker with it alone. Sharing changes the
plan, a helper joins in, and the launch succeeds in a bright, concrete ending.

This script follows the storyworld contract:
- self-contained stdlib storyworld
- typed entities with meters and memes
- Python reasonableness gate + inline ASP twin
- StoryParams, build_parser, resolve_params, generate, emit, main
- QA from world state, not rendered English
- verify mode checks ASP parity and runs a generate smoke test
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
COURAGE_INIT = 5.0
CURIOSITY_INIT = 4.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

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


@dataclass
class LaunchPad:
    id: str
    label: str
    phrase: str
    glow: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class SharedItem:
    id: str
    label: str
    phrase: str
    helps: str
    needed_for_launch: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class CuriosityTrigger:
    id: str
    line: str
    question: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LaunchRisk:
    id: str
    label: str
    phrase: str
    danger: str
    risky: bool = True
    tags: set[str] = field(default_factory=set)


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _mk_meters() -> dict[str, float]:
    return {"curiosity": 0.0, "sharing": 0.0, "stress": 0.0, "launch_ready": 0.0, "safe": 0.0}


def _mk_memes() -> dict[str, float]:
    return {"joy": 0.0, "worry": 0.0, "pride": 0.0, "greed": 0.0, "trust": 0.0, "courage": 0.0}


def _ensure_meter(e: Entity) -> None:
    for k, v in _mk_meters().items():
        e.meters.setdefault(k, v)
    for k, v in _mk_memes().items():
        e.memes.setdefault(k, v)


def _make_world_entities(world: World, hero: str, helper: str, parent: str,
                         pad: LaunchPad, item: SharedItem, risk: LaunchRisk) -> None:
    h = world.add(Entity(id=hero, kind="character", type="boy", role="hero", traits=["curious"], attrs={"paired": helper}, meters=_mk_meters(), memes=_mk_memes()))
    k = world.add(Entity(id=helper, kind="character", type="girl", role="helper", traits=["kind", "sharing"], attrs={"paired": hero}, meters=_mk_meters(), memes=_mk_memes()))
    p = world.add(Entity(id=parent, kind="character", type="mother", role="parent", label="the parent", meters=_mk_meters(), memes=_mk_memes()))
    for e in (h, k, p):
        _ensure_meter(e)
    world.add(Entity(id=pad.id, type="thing", label=pad.label, attrs={"phrase": pad.phrase, "glow": pad.glow}, meters={"assembled": 1.0}, memes={}))
    world.add(Entity(id=item.id, type="thing", label=item.label, attrs={"phrase": item.phrase, "helps": item.helps}, meters={"shared": 0.0}, memes={}))
    world.add(Entity(id=risk.id, type="thing", label=risk.label, attrs={"phrase": risk.phrase, "danger": risk.danger}, meters={"bad": 0.0}, memes={}))


def _r_curiosity(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes["curiosity"] >= THRESHOLD and ("curiosity",) not in world.fired:
        world.fired.add(("curiosity",))
        hero.memes["joy"] += 1
        out.append("__curious__")
    return out


def _r_sharing(world: World) -> list[str]:
    out = []
    helper = world.get("helper")
    item = world.get("item")
    if item.meters["shared"] >= THRESHOLD and ("sharing",) not in world.fired:
        world.fired.add(("sharing",))
        helper.memes["trust"] += 1
        helper.meters["safe"] += 1
        out.append("__shared__")
    return out


def _r_risk(world: World) -> list[str]:
    out = []
    risk = world.get("risk")
    pad = world.get("pad")
    if risk.meters["bad"] >= THRESHOLD and pad.meters["assembled"] >= THRESHOLD and ("risk",) not in world.fired:
        world.fired.add(("risk",))
        world.get("hero").memes["worry"] += 1
        world.get("helper").memes["worry"] += 1
        out.append("__risk__")
    return out


CAUSAL_RULES = [_r_curiosity, _r_sharing, _r_risk]


def propagate(world: World, narrate: bool = True) -> list[str]:
    msgs: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule(world)
            if got:
                changed = True
                msgs.extend([g for g in got if not g.startswith("__")])
    if narrate:
        for msg in msgs:
            world.say(msg)
    return msgs


def _predict(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").memes["curiosity"] += 1
    sim.get("item").meters["shared"] += 1
    sim.get("risk").meters["bad"] += 1
    propagate(sim, narrate=False)
    return {
        "shared": sim.get("item").meters["shared"] >= THRESHOLD,
        "risky": sim.get("risk").meters["bad"] >= THRESHOLD,
    }


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for scene in SCENES:
        for item in ITEMS:
            for risk in RISKS:
                if scene["fits"](item, risk):
                    out.append((scene["id"], item["id"], risk["id"]))
    return out


def explain_rejection(item: LaunchRisk, risk: LaunchRisk) -> str:
    return f"(No story: {item.label} does not fit with {risk.label} in a way that makes a real launch problem.)"


@dataclass
class StoryParams:
    scene: str
    item: str
    risk: str
    hero: str
    helper: str
    parent: str
    seed: Optional[int] = None


SCENES = [
    {"id": "rooftop", "name": "the rooftop", "launch": "launch their paper-wing glider", "fits": lambda item, risk: True},
    {"id": "alley", "name": "the sunlit alley", "launch": "launch their tiny hero kite", "fits": lambda item, risk: True},
    {"id": "playground", "name": "the playground", "launch": "launch their star balloon", "fits": lambda item, risk: True},
]

ITEMS = [
    {"id": "banner", "label": "the red banner", "phrase": "a bright red banner", "helps": "helps them see the wind", "needed": True, "tags": {"launch", "sharing"}},
    {"id": "map", "label": "the folded map", "phrase": "a folded map", "helps": "shows the best way to aim", "needed": True, "tags": {"launch", "curiosity"}},
    {"id": "string", "label": "the silver string", "phrase": "a silver string", "helps": "keeps the launch steady", "needed": True, "tags": {"launch", "sharing"}},
]

RISKS = [
    {"id": "gust", "label": "the wind gust", "phrase": "a sudden wind gust", "danger": "can push the launch off course", "tags": {"launch"}},
    {"id": "tangle", "label": "the kite tangle", "phrase": "a twisty kite tangle", "danger": "can stop the launch from rising", "tags": {"launch"}},
    {"id": "loose", "label": "the loose latch", "phrase": "a loose latch", "danger": "can make the launcher wobble", "tags": {"launch"}},
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-style storyworld about launch, sharing, and curiosity.")
    ap.add_argument("--scene", choices=[s["id"] for s in SCENES])
    ap.add_argument("--item", choices=[i["id"] for i in ITEMS])
    ap.add_argument("--risk", choices=[r["id"] for r in RISKS])
    ap.add_argument("--hero")
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
    scene = args.scene or rng.choice([s["id"] for s in SCENES])
    item = args.item or rng.choice([i["id"] for i in ITEMS])
    risk = args.risk or rng.choice([r["id"] for r in RISKS])
    hero = args.hero or rng.choice(["Milo", "Nova", "Tess", "Arlo", "Ivy", "Finn"])
    helper = args.helper or rng.choice([n for n in ["Maya", "Zara", "Jade", "Leo", "Pia", "Kai"] if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(scene=scene, item=item, risk=risk, hero=hero, helper=helper, parent=parent)


def _story_setup(world: World, params: StoryParams) -> None:
    scene = next(s for s in SCENES if s["id"] == params.scene)
    item = next(i for i in ITEMS if i["id"] == params.item)
    risk = next(r for r in RISKS if r["id"] == params.risk)
    _make_world_entities(
        world, params.hero, params.helper, params.parent,
        LaunchPad(id="pad", label=f"the {scene['id']} launch pad", phrase="a launch pad", glow="glowed like a stage", safe=True, tags={"launch"}),
        SharedItem(id="item", label=item["label"], phrase=item["phrase"], helps=item["helps"], tags=item["tags"]),
        LaunchRisk(id="risk", label=risk["label"], phrase=risk["phrase"], danger=risk["danger"], tags=risk["tags"]),
    )


def tell(world: World, params: StoryParams) -> None:
    scene = next(s for s in SCENES if s["id"] == params.scene)
    item = next(i for i in ITEMS if i["id"] == params.item)
    risk = next(r for r in RISKS if r["id"] == params.risk)
    hero = world.get(params.hero)
    helper = world.get(params.helper)
    parent = world.get(params.parent)
    pad = world.get("pad")
    it = world.get("item")
    rg = world.get("risk")

    hero.memes["curiosity"] += CURIOSITY_INIT
    hero.memes["courage"] += COURAGE_INIT
    helper.memes["trust"] += 1
    helper.memes["pride"] += 1

    world.say(
        f"On a bright afternoon, {hero.id} and {helper.id} stood at {scene['name']}. "
        f"They were superheroes for the day, and the launch pad waited like a tiny city rooftop."
    )
    world.say(
        f"{hero.id} held up {item['phrase']}. {helper.id} held the other side, because this mission was better with two hands."
    )
    world.para()
    world.say(
        f"{hero.id}'s curiosity woke up first. {hero.id} wanted to ask one more question before the launch, and {helper.id} leaned in to help."
    )
    pred = _predict(world)
    if pred["risky"]:
        world.say(
            f'"Careful," {helper.id} said. "That {risk["label"]} can {risk["danger"]}. '
            f"We should share the job and check it together."'
        )
        hero.memes["curiosity"] += 1
        it.meters["shared"] += 1
        hero.meters["launch_ready"] += 1
        helper.meters["launch_ready"] += 1
        parent.memes["pride"] += 1
        world.say(
            f"{hero.id} nodded. {hero.id} shared the {item['label']} instead of grabbing it alone, and {helper.id} held the safe side while they fixed the problem."
        )
    world.para()
    rg.meters["bad"] = 0.0
    hero.meters["launch_ready"] += 1
    helper.meters["launch_ready"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {parent.label_word} came over with a smile, checked the last part, and gave the signal. "
        f'"Launch!"'
    )
    world.say(
        f"The glider shot up, the string stayed steady, and the little hero shape sailed into the sky. '
        f'{helper.id} laughed, and {hero.id} felt big enough to save the day."
    )
    world.para()
    world.say(
        f"At the end, {hero.id} and {helper.id} stood shoulder to shoulder beneath the open sky. "
        f"They had shared the work, followed their curiosity, and watched their launch glow bright above them."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        scene=scene,
        item=item,
        risk=risk,
        pad=pad,
        outcome="shared_launch",
        shared=it.meters["shared"] >= THRESHOLD,
        curious=hero.memes["curiosity"] >= THRESHOLD,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in [s["id"] for s in SCENES]:
        raise StoryError("Unknown scene.")
    if params.item not in [i["id"] for i in ITEMS]:
        raise StoryError("Unknown item.")
    if params.risk not in [r["id"] for r in RISKS]:
        raise StoryError("Unknown risk.")
    world = World()
    _story_setup(world, params)
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that includes the word "launch" and features sharing and curiosity.',
        f"Tell a short story where {f['hero'].id} and {f['helper'].id} share a mission, stay curious, and launch something safely.",
        f"Write a gentle superhero adventure with a launch, a shared tool, and a curious question that helps the team succeed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, parent = f["hero"], f["helper"], f["parent"]
    item, risk = f["item"], f["risk"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {helper.id}, two little superheroes who work as a team. Their parent helps keep the launch safe."),
        ("Why did they need to share?",
         f"They needed to share the {item['label']} because the launch worked best when both of them held it together. Sharing also kept anyone from making the mistake alone."),
        ("How did curiosity help the story?",
         f"Curiosity made {hero.id} ask one more question before the launch. That question helped them notice the {risk['label']} and fix the problem before it could cause trouble."),
        ("How did the story end?",
         f"Their launch rose into the sky, steady and bright. They ended shoulder to shoulder, happy that they shared the work and listened to their curiosity."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a launch?",
         "A launch is when something starts moving into the air or out into action. In superhero stories, a launch can feel exciting and brave."),
        ("What does sharing mean?",
         "Sharing means letting someone else help or use something with you. It can make a job easier and kinder."),
        ("What is curiosity?",
         "Curiosity is the feeling that makes you want to ask questions and learn more. It helps you notice important details."),
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
    parts = ["--- world model state ---"]
    for e in world.entities.values():
        parts.append(f"  {e.id:8} ({e.type:7}) meters={dict(e.meters)} memes={dict(e.memes)} attrs={e.attrs}")
    parts.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(parts)


CURATED = [
    StoryParams(scene="rooftop", item="banner", risk="gust", hero="Milo", helper="Maya", parent="mother"),
    StoryParams(scene="alley", item="map", risk="tangle", hero="Nova", helper="Zara", parent="father"),
    StoryParams(scene="playground", item="string", risk="loose", hero="Tess", helper="Kai", parent="mother"),
]


ASP_RULES = r"""
shared(item) :- launch_item(item).
curious(hero) :- curiosity(hero, C), C >= 1.
launch_safe :- shared(item), curious(hero), not risky(risk).
risky(risk) :- launch_risk(risk).
outcome(shared_launch) :- shared(item), curious(hero).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SCENES:
        lines.append(asp.fact("scene", s["id"]))
    for i in ITEMS:
        lines.append(asp.fact("launch_item", i["id"]))
    for r in RISKS:
        lines.append(asp.fact("launch_risk", r["id"]))
    lines.append(asp.fact("curiosity", "hero", 1))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show outcome/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_outcome() -> str:
    import asp
    model = asp.one_model(asp_program())
    items = asp.atoms(model, "outcome")
    return items[0][0] if items else "?"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show launch_item/1."))
    return sorted(set(asp.atoms(model, "launch_item")))


def asp_verify() -> int:
    rc = 0
    if len(valid_combos()) != len(SCENES) * len(ITEMS) * len(RISKS):
        rc = 1
        print("MISMATCH: valid_combos() returned an unexpected count.")
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    else:
        print("OK: story generation smoke test passed.")
    try:
        _ = asp_outcome()
        print("OK: ASP program parsed.")
    except Exception as exc:
        rc = 1
        print(f"ASP FAILED: {exc}")
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
        print(asp_program(show="#show outcome/1.\n#show launch_item/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("launch items:", ", ".join(i["id"] for i in ITEMS))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that includes the word "launch" and features sharing and curiosity.',
        f"Tell a short story where {f['hero'].id} and {f['helper'].id} share a mission, stay curious, and launch something safely.",
        f"Write a gentle superhero adventure with a launch, a shared tool, and a curious question that helps the team succeed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, parent = f["hero"], f["helper"], f["parent"]
    item, risk = f["item"], f["risk"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {helper.id}, two little superheroes who work as a team. Their parent helps keep the launch safe."),
        ("Why did they need to share?",
         f"They needed to share the {item['label']} because the launch worked best when both of them held it together. Sharing also kept anyone from making the mistake alone."),
        ("How did curiosity help the story?",
         f"Curiosity made {hero.id} ask one more question before the launch. That question helped them notice the {risk['label']} and fix the problem before it could cause trouble."),
        ("How did the story end?",
         f"Their launch rose into the sky, steady and bright. They ended shoulder to shoulder, happy that they shared the work and listened to their curiosity."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a launch?",
         "A launch is when something starts moving into the air or out into action. In superhero stories, a launch can feel exciting and brave."),
        ("What does sharing mean?",
         "Sharing means letting someone else help or use something with you. It can make a job easier and kinder."),
        ("What is curiosity?",
         "Curiosity is the feeling that makes you want to ask questions and learn more. It helps you notice important details."),
    ]


if __name__ == "__main__":
    main()
