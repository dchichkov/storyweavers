#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T042304Z_seed1855084837_n10/tremendous_kindness_space_adventure.py
===============================================================================================================

A tiny standalone storyworld about a space trip, a stranded friend, and a
tremendous act of kindness.

Premise:
- A young space crew is on a small mission between moon stations.
- Their ship's cargo includes a kindness kit and a rescue pod.
- When they meet a stranded traveler, one crew member wants to keep the ship on schedule.
- A gentler choice creates a better ending: they share supplies, repair the pod, and continue together.

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n, --seed
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

def _add_repo_root_to_path() -> None:
    here = os.path.abspath(__file__)
    cur = os.path.dirname(here)
    while True:
        if os.path.exists(os.path.join(cur, "storyworlds", "results.py")):
            if cur not in sys.path:
                sys.path.insert(0, cur)
            return
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent

_add_repo_root_to_path()
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

GIRL_NAMES = ["Mina", "Luna", "Ari", "Nia", "Zoe", "Tia"]
BOY_NAMES = ["Kai", "Jin", "Oren", "Leo", "Sam", "Pax"]
TRAITS = ["brave", "curious", "gentle", "quick-thinking", "bright"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Site:
    id: str
    label: str
    description: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    label: str
    verb: str
    challenge: str
    risk: str
    solution_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    protects: set[str]
    tags: set[str] = field(default_factory=set)

    @property
    def label_word(self) -> str:
        return self.label


@dataclass
class StoryParams:
    site: str
    mission: str
    cargo: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, site: Site) -> None:
        self.site = site
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.site)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def _r_rescue(world: World) -> list[str]:
    out: list[str] = []
    traveler = world.entities.get("traveler")
    pod = world.entities.get("pod")
    if not traveler or not pod:
        return out
    if traveler.meters["stuck"] < THRESHOLD or pod.meters["broken"] < THRESHOLD:
        return out
    sig = ("rescued",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    traveler.meters["hope"] += 1
    pod.meters["fixed"] += 1
    out.append("__rescued__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    traveler = world.entities.get("traveler")
    if not hero or not traveler:
        return out
    if hero.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    traveler.memes["relief"] += 1
    hero.memes["pride"] += 1
    out.append("__kindness__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_rescue, _r_kindness):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for site_id, site in SITES.items():
        for mission_id in site.supports:
            mission = MISSIONS[mission_id]
            for cargo_id, cargo in CARGOS.items():
                if cargo.protects & mission.tags:
                    combos.append((site_id, mission_id, cargo_id))
    return combos


def predicts_fix(world: World, hero: Entity, mission: Mission) -> bool:
    sim = world.copy()
    sim.get("hero").memes["kindness"] += 1
    sim.get("traveler").meters["stuck"] += 1
    sim.get("pod").meters["broken"] += 1
    propagate(sim, narrate=False)
    return sim.get("traveler").meters["hope"] >= THRESHOLD


def tell(site: Site, mission: Mission, cargo: Cargo, hero_name: str, hero_gender: str,
         helper_name: str, helper_gender: str, parent: str, trait: str) -> World:
    world = World(site)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name))
    adult = world.add(Entity(id="adult", kind="character", type=parent, label=f"the {parent}"))
    traveler = world.add(Entity(id="traveler", kind="character", type="person", label="the traveler"))
    pod = world.add(Entity(id="pod", type="thing", label="rescue pod", phrase="a small rescue pod"))
    kit = world.add(Entity(id="kit", type="thing", label=cargo.label, phrase=cargo.phrase))
    world.facts.update(
        hero=hero,
        helper=helper,
        adult=adult,
        traveler=traveler,
        pod=pod,
        kit=kit,
        mission=mission,
        cargo=cargo,
        site=site,
    )
    hero.memes["kindness"] += 1
    helper.memes["worry"] += 1

    world.say(f"On a quiet run between star stations, {hero.label_word} and {helper.label_word} flew past {site.label}.")
    world.say(f"Their ship carried {cargo.phrase}, and {site.description}")
    world.para()
    world.say(f"They were on a mission to {mission.verb}, but {mission.challenge} was waiting ahead.")
    world.say(f"{hero.label_word} loved the view, and {helper.label_word} loved how the ship hummed like a happy bee.")

    world.para()
    world.say(f"Then they found {traveler.label_word}, drifting beside a broken pod near the station lights.")
    world.say(f"{helper.label_word} worried the schedule would slip, because {mission.risk}.")
    world.say(f"But {hero.label_word} saw {traveler.label_word}'s face and felt a tremendous kindness in {hero.pronoun('possessive')} chest.")

    world.para()
    if predicts_fix(world, hero, mission):
        traveler.meters["stuck"] += 1
        pod.meters["broken"] += 1
        world.say(f'"We can help," {hero.label_word} said. "Kindness is the best rescue light."')
        world.say(f"{hero.label_word} shared {cargo.label_word}, and {helper.label_word} used the kit to mend the pod.")
        traveler.meters["stuck"] = 0.0
        pod.meters["broken"] = 0.0
        traveler.memes["relief"] += 1
        hero.memes["kindness"] += 1
        helper.memes["joy"] += 1
        propagate(world, narrate=False)
        world.say(f"Soon the traveler waved from the fixed pod, and the ship made up the time on the bright route home.")
        world.say(f"At the end, the stars looked even bigger, because one tremendous act of kindness had turned a problem into a friend.")
    else:
        world.say(f"{hero.label_word} tried to help, but the fix was not enough, and the pod stayed broken.")
        world.say(f"They still shared supplies and called for backup, so the traveler was safe by the time the patrol arrived.")
        traveler.memes["relief"] += 1
        hero.memes["kindness"] += 1
        world.say("The stars were dark, but the crew kept their promise to be gentle and brave.")

    world.facts["resolved"] = traveler.meters["stuck"] < THRESHOLD and pod.meters["broken"] < THRESHOLD
    return world


SITES = {
    "orbit": Site(id="orbit", label="the orbit lane", description="A silver ribbon of station lights blinked far below.", tags={"space", "station", "rescue"}),
    "moonbase": Site(id="moonbase", label="Moonbase Pine", description="Dusty docks and glass tunnels glowed under a pale moon.", tags={"moon", "station", "rescue"}),
    "asteroid": Site(id="asteroid", label="the comet road", description="Tiny pebbles floated past the windows like sparkling crumbs.", tags={"asteroid", "rescue", "space"}),
}
MISSIONS = {
    "deliver": Mission(id="deliver", label="deliver crystals", verb="deliver the star crystals", challenge="a delivery clock was ticking", risk="the cargo would arrive late", solution_hint="keep the route steady", tags={"delivery"}),
    "survey": Mission(id="survey", label="survey lights", verb="survey the glowing rings", challenge="a new map had to be finished", risk="the map would miss the rescue dock", solution_hint="pause and look carefully", tags={"map"}),
    "tow": Mission(id="tow", label="tow the pod", verb="tow the broken pod", challenge="the pod was spinning in the cold dark", risk="the pod could drift away", solution_hint="move slowly and gently", tags={"rescue", "pod"}),
}
CARGOS = {
    "rope": Cargo(id="rope", label="soft rope", phrase="a coil of soft rope", protects={"rescue", "pod"}, tags={"rope"}),
    "kit": Cargo(id="kit", label="repair kit", phrase="a bright repair kit", protects={"rescue", "pod", "map"}, tags={"repair"}),
    "lamp": Cargo(id="lamp", label="signal lamp", phrase="a small signal lamp", protects={"map", "space"}, tags={"lamp"}),
}
KNOWLEDGE = {
    "kindness": [("What is kindness?", "Kindness means choosing to help, share, and be gentle with someone else.")],
    "rescue": [("What does rescue mean?", "Rescue means helping someone get safe when they are in trouble.")],
    "pod": [("What is a pod in space stories?", "A pod is a small round ship or capsule that can carry people or cargo.")],
    "station": [("What is a space station?", "A space station is a place built in space where people can live and work.")],
    "moon": [("What is the Moon?", "The Moon is the round rock that goes around Earth and shines in the night sky.")],
    "tremendous": [("What does tremendous mean?", "Tremendous means very, very big or very strong.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short space adventure for a child that includes the word "tremendous" and a moment of kindness.',
        f"Tell a space story where {f['hero'].label_word} and {f['helper'].label_word} meet {f['traveler'].label_word} near {f['site'].label} and choose to help.",
        f"Write a gentle outer-space rescue story about a broken pod, a useful cargo kit, and a friendly ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    traveler: Entity = f["traveler"]  # type: ignore[assignment]
    site: Site = f["site"]  # type: ignore[assignment]
    mission: Mission = f["mission"]  # type: ignore[assignment]
    cargo: Cargo = f["cargo"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"Who were the story's space helpers at {site.label}?",
            answer=f"The story was about {hero.label_word} and {helper.label_word}. They were flying near {site.label} when they met {traveler.label_word} and decided what to do next.",
        ),
        QAItem(
            question=f"What problem did {traveler.label_word} have near the ship?",
            answer=f"{traveler.label_word} was stuck beside a broken pod. That made the mission tricky because {mission.risk}.",
        ),
        QAItem(
            question=f"What did {hero.label_word} share to help?",
            answer=f"{hero.label_word} shared {cargo.label_word}. That gave the crew a useful way to fix the pod and keep moving.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"Why did the ending feel tremendous?",
            answer=f"It felt tremendous because one kind choice changed the whole trip. The crew helped {traveler.label_word}, fixed the pod, and finished the journey with a new friend.",
        ))
    else:
        qa.append(QAItem(
            question=f"Why was the ending still kind even without a full repair?",
            answer=f"It was still kind because the crew did not leave {traveler.label_word} alone. They shared supplies and called for backup, which kept everyone safe.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["site"].tags) | set(world.facts["mission"].tags) | set(world.facts["cargo"].tags)
    if world.facts.get("resolved"):
        tags.add("kindness")
    tags.add("tremendous")
    out: list[QAItem] = []
    for key in ["kindness", "rescue", "pod", "station", "moon", "tremendous"]:
        if key in tags and key in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for p in sample.prompts:
        parts.append(f"- {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)} label={e.label}")
    return "\n".join(lines)


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


ASP_RULES = r"""
site(S) :- site_fact(S).
mission(M) :- mission_fact(M).
cargo(C) :- cargo_fact(C).
compatible(S,M,C) :- site_fact(S), mission_fact(M), cargo_fact(C), supports(S,M), protects(C,T), mission_tag(M,T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SITES.items():
        lines.append(asp.fact("site_fact", sid))
        for m in sorted(s.tags):
            lines.append(asp.fact("site_tag", sid, m))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission_fact", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("mission_tag", mid, t))
    for cid, c in CARGOS.items():
        lines.append(asp.fact("cargo_fact", cid))
        for t in sorted(c.protects):
            lines.append(asp.fact("protects", cid, t))
    for sid, s in SITES.items():
        for mid in s.supports:
            lines.append(asp.fact("supports", sid, mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    try:
        import asp
        py = set(valid_combos())
        cl = set(asp_valid_combos())
        ok = py == cl
        sample = generate(resolve_params(argparse.Namespace(site=None, mission=None, cargo=None, hero=None, hero_gender=None, helper=None, helper_gender=None, parent=None, trait=None, seed=None, all=False, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False, n=1), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        if ok:
            print(f"OK: ASP matches Python for {len(py)} combos.")
            return 0
        print("MISMATCH between ASP and Python.")
        print("py only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))
        return 1
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with a tremendous kindness turn.")
    ap.add_argument("--site", choices=SITES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
              if (args.site is None or c[0] == args.site)
              and (args.mission is None or c[1] == args.mission)
              and (args.cargo is None or c[2] == args.cargo)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    site, mission, cargo = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" and rng.random() < 0.5 else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(site=site, mission=mission, cargo=cargo, hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    site = SITES.get(params.site)
    mission = MISSIONS.get(params.mission)
    cargo = CARGOS.get(params.cargo)
    if not site or not mission or not cargo:
        raise StoryError("invalid parameters")
    world = World(site)
    world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero))
    world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper))
    world.add(Entity(id="adult", kind="character", type=params.parent, label=f"the {params.parent}"))
    world.add(Entity(id="traveler", kind="character", type="person", label="the traveler"))
    world.add(Entity(id="pod", type="thing", label="rescue pod", phrase="a small rescue pod"))
    world.add(Entity(id="kit", type="thing", label=cargo.label, phrase=cargo.phrase))
    world.facts.update(site=site, mission=mission, cargo=cargo)
    story = tell(site, mission, cargo, params.hero, params.hero_gender, params.helper, params.helper_gender, params.parent, params.trait)
    return StorySample(params=params, story=story.render(), prompts=generation_prompts(story), story_qa=story_qa(story), world_qa=world_knowledge_qa(story), world=story)


CURATED = [
    StoryParams(site="orbit", mission="tow", cargo="kit", hero="Mina", hero_gender="girl", helper="Kai", helper_gender="boy", parent="mother", trait="kind"),
    StoryParams(site="moonbase", mission="deliver", cargo="rope", hero="Leo", hero_gender="boy", helper="Luna", helper_gender="girl", parent="father", trait="gentle"),
    StoryParams(site="asteroid", mission="survey", cargo="lamp", hero="Ari", hero_gender="girl", helper="Pax", helper_gender="boy", parent="mother", trait="curious"),
]

SITES["orbit"].supports = {"tow", "deliver"}
SITES["moonbase"].supports = {"tow", "survey"}
SITES["asteroid"].supports = {"survey", "deliver"}


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
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
