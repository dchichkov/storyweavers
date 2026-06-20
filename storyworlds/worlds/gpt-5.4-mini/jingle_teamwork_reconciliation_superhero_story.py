#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jingle_teamwork_reconciliation_superhero_story.py
=================================================================================

A standalone story world for a tiny superhero tale: two young heroes hear a
helpful jingle, disagree about how to save the day, then reunite their strengths
to finish the rescue together.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- state-driven narration, not a frozen paragraph with swapped nouns
- a forward-chained causal model
- a reasonableness gate plus an inline ASP twin
- child-facing QA generated from simulated world state

Seed words / features:
- jingle
- teamwork
- reconciliation
- superhero story
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
MAGIC_MIN = 2
RECONCILE_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class HeroGear:
    id: str
    label: str
    power: str
    sound: str
    helps: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    place: str
    danger: str
    spread: int
    needs: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    title: str
    reason: str
    fix: str
    power: int
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
    tag: str
    apply: Callable[[World], list[str]]


def _r_spark(world: World) -> list[str]:
    out: list[str] = []
    for t in TROUBLES.values():
        if world.get("trouble").meters["active"] < THRESHOLD:
            continue
    if "trouble" in world.entities and world.get("trouble").meters["active"] >= THRESHOLD:
        if ("spark",) in world.fired:
            return []
        world.fired.add(("spark",))
        for hero in world.characters():
            hero.memes["worry"] += 1
        world.get("trouble").meters["spread"] += 1
        out.append("__spark__")
    return out


def _r_teamup(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("hero_a")
    b = world.get("hero_b")
    if a.memes["trust"] >= THRESHOLD and b.memes["trust"] >= THRESHOLD and (a.memes["hurt"] >= THRESHOLD or b.memes["hurt"] >= THRESHOLD):
        sig = ("teamup",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        a.memes["teamwork"] += 1
        b.memes["teamwork"] += 1
        out.append("__teamup__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("hero_a")
    b = world.get("hero_b")
    if a.memes["regret"] >= THRESHOLD and b.memes["forgive"] >= THRESHOLD:
        sig = ("reconcile",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        a.memes["peace"] += 1
        b.memes["peace"] += 1
        out.append("__reconcile__")
    return out


CAUSAL_RULES = [
    Rule("spark", "physical", _r_spark),
    Rule("teamup", "social", _r_teamup),
    Rule("reconcile", "social", _r_reconcile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reason_ok(challenge: Challenge, trouble: Trouble, gear: HeroGear) -> bool:
    return challenge.fix == gear.helps and challenge.power >= trouble.spread


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for cid in CHALLENGES:
        ch = CHALLENGES[cid]
        for tid in TROUBLES:
            tr = TROUBLES[tid]
            for gid in GEAR:
                if reason_ok(ch, tr, GEAR[gid]):
                    out.append((cid, tid, gid))
    return out


def choose_names(rng: random.Random) -> tuple[tuple[str, str], tuple[str, str]]:
    girl = rng.choice(GIRL_NAMES)
    boy = rng.choice(BOY_NAMES)
    if rng.random() < 0.5:
        return (girl, "girl"), (boy, "boy")
    return (boy, "boy"), (girl, "girl")


def predict(world: World, trouble_id: str, challenge_id: str) -> dict:
    sim = world.copy()
    sim.get("trouble").meters["active"] = 1
    propagate(sim, narrate=False)
    tr = TROUBLES[trouble_id]
    ch = CHALLENGES[challenge_id]
    return {"spread": sim.get("trouble").meters["spread"], "can_fix": ch.power >= tr.spread}


def start(world: World, a: Entity, b: Entity, tr: Trouble) -> None:
    a.memes["pride"] += 1
    b.memes["pride"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} became city heroes. "
        f"Their capes fluttered over the rooftops, and {tr.label} waited below by {tr.place}."
    )
    world.say(
        f"Then a small rescue alarm gave a cheerful jingle from their wrist radios, "
        f"and both heroes sprang to attention."
    )


def conflict(world: World, a: Entity, b: Entity, tr: Trouble) -> None:
    a.memes["anger"] += 1
    b.memes["anger"] += 1
    world.say(
        f"{a.id} wanted to rush in first, but {b.id} wanted to guide the plan. "
        f"They both stared at {tr.label} and forgot to listen for a moment."
    )


def jingle_call(world: World, gear: HeroGear) -> None:
    world.say(
        f"The wrist radio gave its little {gear.sound}, and the sound made the plan feel clear again."
    )


def disagreement_turns(world: World, a: Entity, b: Entity) -> None:
    a.memes["hurt"] += 1
    b.memes["hurt"] += 1
    world.say(
        f"{a.id} felt hurt, and {b.id} did too. "
        f"For a breath, the team felt broken apart."
    )


def apology(world: World, a: Entity, b: Entity) -> None:
    a.memes["regret"] += 1
    b.memes["forgive"] += 1
    world.say(
        f"Then {a.id} looked down and said sorry for pushing ahead. "
        f"{b.id} nodded, took a slow breath, and forgave {a.pronoun('object')}."
    )


def team_move(world: World, a: Entity, b: Entity, gear: HeroGear, tr: Trouble, ch: Challenge) -> None:
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    tr_ent = world.get("trouble")
    tr_ent.meters["active"] = 0
    tr_ent.meters["safe"] = 1
    world.say(
        f"Together they used {gear.label}: one lifted the fallen gate, the other held the light, "
        f"and the problem shrank fast. {ch.title} worked because they did it side by side."
    )


def reconciliation_end(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f"After the rescue, {a.id} and {b.id} bumped fists and smiled. "
        f"That night the city glittered below them, and the two heroes felt stronger because they were friends again."
    )


def tell(challenge: Challenge, trouble: Trouble, gear: HeroGear,
         hero_a: tuple[str, str] = ("Nova", "girl"),
         hero_b: tuple[str, str] = ("Comet", "boy")) -> World:
    world = World()
    a = world.add(Entity(id="hero_a", kind="character", type=hero_a[1], role="hero", label=hero_a[0]))
    b = world.add(Entity(id="hero_b", kind="character", type=hero_b[1], role="hero", label=hero_b[0]))
    t = world.add(Entity(id="trouble", type="trouble", label=trouble.label))
    a.id, b.id = hero_a[0], hero_b[0]
    a.label, b.label = hero_a[0], hero_b[0]
    a.memes["trust"] = 1
    b.memes["trust"] = 1
    t.meters["active"] = 1

    start(world, a, b, trouble)
    world.para()
    conflict(world, a, b, trouble)
    jingle_call(world, gear)
    disagreement_turns(world, a, b)
    apology(world, a, b)
    team_move(world, a, b, gear, trouble, challenge)
    propagate(world, narrate=False)
    world.para()
    reconciliation_end(world, a, b)

    world.facts.update(hero_a=a, hero_b=b, trouble=trouble, challenge=challenge, gear=gear,
                       outcome="fixed", jingle=gear.sound)
    return world


GIRL_NAMES = ["Nova", "Stella", "Ruby", "Mira", "Ivy", "Piper", "Zara", "Luna"]
BOY_NAMES = ["Comet", "Dash", "Jet", "Kai", "Leo", "Finn", "Miles", "Tate"]

GEAR = {
    "signal_belt": HeroGear("signal_belt", "signal belt", "rescue plan", "jingle", "helped them hear each other", {"jingle"}),
    "team_gloves": HeroGear("team_gloves", "team gloves", "lift together", "jingle-jingle", "helped them work as one", {"jingle"}),
    "sky_map": HeroGear("sky_map", "sky map", "find the path", "ching", "helped them point the way", {"jingle"}),
}

TROUBLES = {
    "bridge_gate": Trouble("bridge_gate", "the stuck bridge gate", "the bridge", "blocked path", 2, "rescue plan", {"city"}),
    "cat_lift": Trouble("cat_lift", "a kitten on a ledge", "the tower ledge", "small danger", 1, "lift together", {"city"}),
    "bus_bend": Trouble("bus_bend", "a bent bus sign", "the corner street", "crooked sign", 2, "find the path", {"city"}),
}

CHALLENGES = {
    "plan": Challenge("plan", "their rescue plan", "they needed to think before rushing", "rescue plan", 2, {"teamwork"}),
    "lift": Challenge("lift", "their lift-together move", "the problem was too heavy for one hero", "lift together", 1, {"teamwork"}),
    "path": Challenge("path", "their path-finding move", "the street was confusing without a clear sign", "find the path", 2, {"teamwork"}),
}

CURATED = [
    ("Nova", "girl", "Comet", "boy", "signal_belt", "bridge_gate", "plan"),
    ("Stella", "girl", "Kai", "boy", "team_gloves", "cat_lift", "lift"),
    ("Ruby", "girl", "Finn", "boy", "sky_map", "bus_bend", "path"),
]


@dataclass
class StoryParams:
    hero1: str
    hero1_gender: str
    hero2: str
    hero2_gender: str
    gear: str
    trouble: str
    challenge: str
    seed: Optional[int] = None


def explain_rejection(challenge: Challenge, trouble: Trouble, gear: HeroGear) -> str:
    return (
        f"(No story: {challenge.title} and {gear.label} do not solve {trouble.label} together. "
        f"The rescue must be a real fit, or the story would not have an honest teamwork turn.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world about jingle cues, teamwork, and reconciliation.")
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--gender2", choices=["girl", "boy"])
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
    if args.gear and args.trouble and args.challenge:
        if (args.challenge, args.trouble, args.gear) not in combos:
            raise StoryError(explain_rejection(CHALLENGES[args.challenge], TROUBLES[args.trouble], GEAR[args.gear]))
    combos = [c for c in combos if (not args.gear or c[2] == args.gear) and (not args.trouble or c[1] == args.trouble) and (not args.challenge or c[0] == args.challenge)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    challenge, trouble, gear = rng.choice(sorted(combos))
    h1 = args.name1 or rng.choice(GIRL_NAMES + BOY_NAMES)
    h2 = args.name2 or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != h1])
    g1 = args.gender1 or rng.choice(["girl", "boy"])
    g2 = args.gender2 or ("boy" if g1 == "girl" else "girl")
    return StoryParams(h1, g1, h2, g2, gear, trouble, challenge)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a small child that includes the word "jingle" and shows teamwork.',
        f"Tell a story where {f['hero_a'].id} and {f['hero_b'].id} hear a jingle, argue for a moment, then work together to save {f['trouble'].label}.",
        f"Write a gentle action story that ends with reconciliation and a shiny teamwork win."
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b = f["hero_a"], f["hero_b"]
    tr, ch, gear = f["trouble"], f["challenge"], f["gear"]
    return [
        QAItem(
            question="Who are the story heroes?",
            answer=f"The story is about {a.id} and {b.id}. They are the two heroes who start out excited, then learn how to work together."
        ),
        QAItem(
            question="Why did the heroes stop arguing?",
            answer=f"They stopped arguing because they realized the rescue needed both of them. After the apology, they trusted each other again and made one shared plan."
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"They used the {gear.label} and solved {tr.label} together. One hero helped with the {ch.title.lower()}, and the other held the important part steady, so the rescue worked."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is teamwork?", "Teamwork means people use their different strengths together to reach the same goal. It often works better than trying to do everything alone."),
        QAItem("What does reconciliation mean?", "Reconciliation means making peace again after a disagreement. People apologize, forgive, and feel friendly once more."),
        QAItem("What is a jingle?", "A jingle is a small, cheerful sound that rings or chimes. In stories, a jingle can be a signal that helps everyone pay attention."),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(C, T, G) :- challenge(C), trouble(T), gear(G), fix_of(C, F), helps(G, F), power(C, P), spread(T, S), P >= S.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        lines.append(asp.fact("helps", gid, g.helps))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("spread", tid, t.spread))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("fix_of", cid, c.fix))
        lines.append(asp.fact("power", cid, c.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(gear=None, trouble=None, challenge=None, name1=None, name2=None, gender1=None, gender2=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        CHALLENGES[params.challenge],
        TROUBLES[params.trouble],
        GEAR[params.gear],
        hero_a=(params.hero1, params.hero1_gender),
        hero_b=(params.hero2, params.hero2_gender),
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("", "#show valid/3."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(*c, seed=i)) for i, c in enumerate(CURATED)]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
