#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/amputate_foreshadowing_bedtime_story.py
=======================================================================

A small bedtime-style story world about a sleepy child, a careful grown-up,
and a tiny animal scare that is gently foreshadowed and then eased.

Premise
-------
A child notices that a pet or toy companion is walking funny after a small
injury. A grown-up quietly explains what might happen if the problem gets worse,
including the rare word "amputate", and then shows a safer, kinder way to help.
The story stays soft, concrete, and bedtime-like: lantern light, blankets,
whispers, and a clear ending image proving the danger passed.

This world intentionally uses foreshadowing:
- a early clue hints that the injury could worsen
- a later choice either prevents the worse outcome or leads to a careful fix
- the ending changes the animal's state and the child's feelings

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/amputate_foreshadowing_bedtime_story.py
    python storyworlds/worlds/gpt-5.4-mini/amputate_foreshadowing_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/amputate_foreshadowing_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/amputate_foreshadowing_bedtime_story.py --verify
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
    kind: str = "thing"  # "character" | "pet" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    room: str
    bedtime_image: str
    companion: str
    soft_ending: str


@dataclass
class Injury:
    id: str
    label: str
    phrase: str
    clue: str
    risk: int
    can_amputate: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Care:
    id: str
    label: str
    phrase: str
    action: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    theme: Theme
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        w = World(self.theme)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["hurt"] < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_sleepy(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind == "character" and e.memes["safe"] >= THRESHOLD:
            sig = ("sleepy", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["sleepiness"] += 1
            out.append("__sleep__")
    return out


RULES = [Rule("worry", _r_worry), Rule("sleepy", _r_sleepy)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def will_need_amputate(injury: Injury, delay: int) -> bool:
    return injury.can_amputate and (injury.risk + delay) >= 4


def can_save(injury: Injury, care: Care, delay: int) -> bool:
    return care.power >= injury.risk + delay


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for tid in THEMES:
        for iid, inj in INJURIES.items():
            for cid, car in CARES.items():
                if inj.can_amputate and car.sense >= 2:
                    out.append((tid, iid, cid))
    return out


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for iid, inj in INJURIES.items():
        lines.append(asp.fact("injury", iid))
        if inj.can_amputate:
            lines.append(asp.fact("can_amputate", iid))
        lines.append(asp.fact("risk", iid, inj.risk))
    for cid, car in CARES.items():
        lines.append(asp.fact("care", cid))
        lines.append(asp.fact("sense", cid, car.sense))
        lines.append(asp.fact("power", cid, car.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T,I,C) :- theme(T), injury(I), care(C), can_amputate(I), sense(C,S), sense_min(M), S >= M.
need_amputate(I,D) :- risk(I,R), delay(D), R + D >= 4.
saved(I,C,D) :- power(C,P), risk(I,R), delay(D), P >= R + D.
outcome(saved) :- saved(_,_,_).
outcome(amputate) :- need_amputate(_,D), not saved(_,_,D).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: "StoryParams") -> str:
    import asp
    scenario = "\n".join([asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


@dataclass
class StoryParams:
    theme: str
    injury: str
    care: str
    child: str
    child_gender: str
    grownup: str
    seed: Optional[int] = None
    delay: int = 0


THEMES = {
    "moon_room": Theme("moon_room", "the moonlit bedroom", "a little lamp glowed like a star", "a sleepy friend", "the soft ending was a warm blanket and a quiet song"),
    "window_nook": Theme("window_nook", "the cozy window seat", "rain tapped gently at the glass", "a plush rabbit", "the soft ending was a pillow nest and a long yawn"),
    "tent": Theme("tent", "the little blanket tent", "the blanket tent smelled like lavender soap", "a teddy bear guard", "the soft ending was a tucked-in tail and moonbeams on the floor"),
}

INJURIES = {
    "thorn": Injury("thorn", "a thorn scratch", "a small thorn scratch", "one tiny drop of red", 1, can_amputate=True, tags={"wound"}),
    "splinter": Injury("splinter", "a splinter", "a little splinter", "a tiny stuck sliver", 2, can_amputate=True, tags={"wound"}),
    "bite": Injury("bite", "a bad bite", "a sore bite", "a warm, swollen paw", 3, can_amputate=True, tags={"wound"}),
}

CARES = {
    "wash": Care("wash", "warm water", "warm water and a soft cloth", "washed the spot", 1, 2, tags={"wash"}),
    "bandage": Care("bandage", "bandage", "a clean bandage", "wrapped the paw", 3, 3, tags={"bandage"}),
    "vet": Care("vet", "the vet", "the vet's careful medicine", "called the vet", 4, 3, tags={"vet"}),
}

GIRL_NAMES = ["Maya", "Lily", "Nora", "Zoe", "Ivy"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Sam", "Ben"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with foreshadowing and a gentle injury scare.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--injury", choices=INJURIES)
    ap.add_argument("--care", choices=CARES)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.care and CARES[args.care].sense < 2:
        raise StoryError("Choose a calmer kind of help.")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.injury is None or c[1] == args.injury)
              and (args.care is None or c[2] == args.care)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, injury, care = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grownup = args.grownup or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(theme, injury, care, child, gender, grownup, delay=delay)


def tell(theme: Theme, injury: Injury, care: Care, child: str, gender: str, grownup: str, delay: int) -> World:
    world = World(theme)
    kid = world.add(Entity(child, kind="character", type=gender, role="child"))
    adult = world.add(Entity("Grownup", kind="character", type=grownup, label="the grown-up", role="grownup"))
    pet = world.add(Entity("Pip", kind="pet", type="thing", label="Pip", role="pet"))
    pet.meters["hurt"] = 1.0
    kid.memes["love"] += 1
    world.say(f"{child} was almost asleep in {theme.room}. {theme.bedtime_image}.")
    world.say(f"Then {pet.label} hopped close, and {child} noticed {injury.clue} on a little paw.")
    world.para()
    world.say(f"{child} whispered to {grownup}: \"What does {injury.label} mean?\"")
    if care.id == "wash":
        world.say(f"{grownup.capitalize()} smiled and said it meant the paw needed rest, warmth, and cleaning.")
        world.say(f"\"If it got worse,\" {grownup} added softly, \"a vet might have to amputate the hurt part to keep {pet.label} safe.\"")
        world.say("That was the foreshadowing: a small warning, like a cloud before rain.")
    elif care.id == "bandage":
        world.say(f"{grownup.capitalize()} wrapped the paw in a clean bandage and tucked {pet.label} beside the pillow.")
        world.say(f"\"If the swelling stayed big,\" {grownup} said, \"the vet would watch it closely, because a tiny part might need to be amputate later.\"")
    else:
        world.say(f"{grownup.capitalize()} called the vet right away, because the bite looked serious.")
        world.say(f"The vet explained that waiting could mean we might have to amputate the damaged part, so quick help mattered.")
    world.para()
    if can_save(injury, care, delay):
        pet.memes["safe"] += 1
        pet.meters["hurt"] = 0.0
        propagate(world, narrate=False)
        world.say(f"So {grownup} {care.action}, and the little paw grew calmer each minute.")
        world.say(f"By bedtime, {pet.label} was breathing slow and even, with no need to amputate anything.")
        world.say(f"{child} smiled into the blanket dark, hearing only soft breathing and the hush of the room.")
        world.say(f"{theme.soft_ending.capitalize()}.")
        outcome = "saved"
    else:
        pet.meters["hurt"] += 1
        propagate(world, narrate=False)
        world.say(f"But the night slipped by too fast, and the hurt part stayed angry despite the care.")
        world.say(f"The vet came back with a tiny lantern and a very careful plan: sometimes they had to amputate the bad part to keep the rest healthy.")
        world.say(f"After that, {pet.label} was bandaged, safe, and tucked under a quilt while everyone breathed again.")
        world.say(f"{child} learned that grown-ups can say hard words gently when they are trying to help.")
        outcome = "amputate"
    world.facts.update(theme=theme, injury=injury, care=care, child=kid, grownup=adult, pet=pet, delay=delay, outcome=outcome)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a young child that quietly foreshadows what might happen if a pet injury gets worse. Include the word "amputate".',
        f"Tell a soft, sleepy story where {f['child'].id} notices a small injury on a pet and a grown-up explains it carefully before bedtime.",
        f'Write a gentle story with foreshadowing, blankets, and lantern light that uses the word "amputate" in a calm, child-friendly way.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"].id
    pet = f["pet"].label
    grownup = f["grownup"].label_word
    injury = f["injury"].label
    care = f["care"].phrase
    q = [
        ("Who is the story about?", f"It is about {child}, {pet}, and {grownup}, all in a sleepy bedtime room."),
        (f"What did {child} notice?", f"{child} noticed {injury} on {pet}'s paw, which made the room feel very still."),
        ("What was the foreshadowing in the story?", f"The grown-up quietly explained that if the hurt part got worse, they might have to amputate it. That warning came early, before bedtime, so the child could understand the risk.")
    ]
    if f["outcome"] == "saved":
        q.append((f"How did the story end?", f"It ended safely. {grownup.capitalize()} used {care}, and by bedtime there was no need to amputate anything."))
    else:
        q.append((f"How did the story end?", f"It ended with careful help and a hard choice. The vet had to amputate the bad part, but that kept {pet} safe and calm."))
    return q


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does foreshadowing mean?",
         "Foreshadowing is when a story gives a small clue early on that hints at something important later."),
        ("What is bedtime story style?",
         "Bedtime story style is soft, calm, and cozy, with gentle words, quiet feelings, and a peaceful ending."),
        ("What does amputate mean?",
         "To amputate means to remove a part of a body, usually because it is badly hurt or sick and must be taken off to keep the rest safe."),
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moon_room", "thorn", "wash", "Maya", "girl", "mother", delay=0),
    StoryParams("window_nook", "splinter", "bandage", "Eli", "boy", "father", delay=1),
    StoryParams("tent", "bite", "vet", "Nora", "girl", "mother", delay=0),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], INJURIES[params.injury], CARES[params.care], params.child, params.child_gender, params.grownup, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP gate.")
        return 1
    ok = 0
    for p in CURATED:
        if asp_outcome(p) not in {"saved", "amputate"}:
            ok = 1
    print("OK: ASP gate and smoke tests passed.")
    return ok


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t, i, c in asp_valid_combos():
            print(t, i, c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
