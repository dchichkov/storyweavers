#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/karate_hypoallergenic_lesson_learned_superhero_story.py
=======================================================================================

A tiny superhero storyworld for a child-friendly lesson-learned tale about a
hero, a soft sidekick, and a hypoallergenic suit that keeps the mission safe.

Seed words:
- karate
- hypoallergenic

Style:
- Superhero Story

The premise: a young hero wants to impress everybody with karate moves, but a
hasty choice about gear causes sneezing and trouble. A careful friend points out
the problem, the hero fixes it, and the team learns that the safest choice is
also the bravest one.

This file is standalone and uses only the stdlib plus the shared result/ASP
helpers from the Storyweavers repo.
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
CAUTIOUS_MIN = 1.0


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
    hypoallergenic: bool = False
    costume: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Costume:
    id: str
    label: str
    phrase: str
    hypoallergenic: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    sneeze: bool
    discomfort: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    strength: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    mentor_type: str
    costume: str
    hazard: str
    fix: str
    mission: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_sneeze(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["sneeze"] < THRESHOLD:
            continue
        sig = ("sneeze", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["embarrassed"] += 1
        hero = world.get("hero")
        hero.memes["worry"] += 1
        out.append("__sneeze__")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["lesson"] >= THRESHOLD:
        sig = ("lesson", hero.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        hero.memes["calm"] += 1
        out.append("__lesson__")
    return out


CAUSAL_RULES = [Rule("sneeze", _r_sneeze), Rule("lesson", _r_lesson)]


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


def mishap_risk(costume: Costume, hazard: Hazard) -> bool:
    return (not costume.hypoallergenic) and hazard.sneeze


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= 2]


def chosen_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def is_beatable(fix: Fix, hazard: Hazard) -> bool:
    return fix.strength >= hazard.discomfort


def predict_mishap(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    _cause_mishap(sim, narrate=False)
    return {
        "sneeze": sim.get("sidekick").meters["sneeze"] >= THRESHOLD,
        "worry": sim.get("hero").memes["worry"],
    }


def _cause_mishap(world: World, narrate: bool = True) -> None:
    sidekick = world.get("sidekick")
    sidekick.meters["sneeze"] += 1
    sidekick.meters["itch"] += 1
    propagate(world, narrate=narrate)


def open_scene(world: World, hero: Entity, sidekick: Entity, mentor: Entity, mission: str) -> None:
    hero.memes["hope"] += 1
    sidekick.memes["hope"] += 1
    world.say(
        f"In a bright city with shining windows, {hero.id} and {sidekick.id} "
        f"stood on the rooftop in the middle of {mission}."
    )
    world.say(
        f'"{hero.id} karate!" {hero.id} said, throwing a practice pose like a real hero.'
    )
    world.say(
        f"{mentor.label_word.capitalize()} watched from the doorway, ready to help."
    )


def show_gear(world: World, hero: Entity, costume: Costume) -> None:
    world.say(
        f"{hero.id} wore {costume.phrase}, because every hero needs a suit that "
        f"works on a busy day."
    )


def warn(world: World, sidekick: Entity, costume: Costume, hazard: Hazard, mentor: Entity) -> None:
    pred = predict_mishap(world, hazard.id)
    sidekick.memes["caution"] += 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{sidekick.id} pointed at the suit and said, "{costume.label} can make '
        f'{sidekick.pronoun("object")} sneeze. {mentor.label_word.capitalize()} '
        f"would want the safe choice.""
    )


def trouble(world: World, hazard: Hazard) -> None:
    _cause_mishap(world)
    world.say(
        f"At the next spin, the {hazard.label} drifted into the room. "
        f"The sidekick sniffled, then sneezed again."
    )


def fix_it(world: World, mentor: Entity, fix: Fix, costume: Costume, hazard: Hazard) -> None:
    world.get("sidekick").memes["lesson"] += 1
    body = fix.phrase.replace("{hazard}", hazard.label)
    world.say(
        f"{mentor.label_word.capitalize()} came in fast and {body}."
    )
    if costume.hypoallergenic:
        world.say(
            f"The new suit stayed smooth and safe, and nobody sneezed anymore."
        )
    else:
        world.say(
            f"The old suit went into a drawer, because it was not right for a hero's nose."
        )


def lesson_learned(world: World, hero: Entity, sidekick: Entity, mentor: Entity) -> None:
    hero.memes["lesson"] += 1
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"For a moment, the rooftop was quiet. Then {mentor.label_word.capitalize()} "
        f"knelt down and said, \"Being brave means picking the safe thing.\""
    )
    world.say(
        f"{hero.id} nodded. {sidekick.id} smiled, and both heroes promised to "
        f"choose a hypoallergenic suit next time."
    )


def ending(world: World, hero: Entity, sidekick: Entity, costume: Costume) -> None:
    world.say(
        f"After that, {hero.id} and {sidekick.id} leaped back into the sky, "
        f"{costume.label} shining in the sun, ready for the next rescue."
    )


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type))
    sidekick = world.add(Entity(id="sidekick", kind="character", type=params.sidekick_type, role="sidekick"))
    mentor = world.add(Entity(id="mentor", kind="character", type=params.mentor_type, role="mentor"))
    costume = COSTUMES[params.costume]
    hazard = HAZARDS[params.hazard]
    fix = FIXES[params.fix]

    hero.id = params.hero_name
    sidekick.id = params.sidekick_name
    mentor.label = "the mentor"

    hero.memes["bravery"] = 1.0
    sidekick.memes["caution"] = 1.0

    open_scene(world, hero, sidekick, mentor, params.mission)
    world.para()
    show_gear(world, hero, costume)
    warn(world, sidekick, costume, hazard, mentor)

    if mishap_risk(costume, hazard):
        trouble(world, hazard)
        world.para()
        fix_it(world, mentor, fix, costume, hazard)
        lesson_learned(world, hero, sidekick, mentor)
        world.para()
        ending(world, hero, sidekick, costume)
    else:
        hero.memes["lesson"] += 1
        world.say(
            f"{sidekick.id} was right: the hypoallergenic suit kept the mission calm, "
            f"so the heroes finished without a sneeze."
        )
        world.say(
            f"{hero.id} thanked {sidekick.id} for the warning and kept flying."
        )
        world.para()
        ending(world, hero, sidekick, costume)

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        mentor=mentor,
        costume=costume,
        hazard=hazard,
        fix=fix,
        outcome="mishap" if mishap_risk(costume, hazard) else "safe",
        learned=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


COSTUMES = {
    "cape": Costume(id="cape", label="a shiny cape", phrase="a shiny cape", hypoallergenic=False),
    "suit": Costume(id="suit", label="a hypoallergenic suit", phrase="a hypoallergenic suit", hypoallergenic=True),
    "mask": Costume(id="mask", label="a hypoallergenic mask", phrase="a hypoallergenic mask", hypoallergenic=True),
    "gloves": Costume(id="gloves", label="soft gloves", phrase="soft gloves", hypoallergenic=False),
}

HAZARDS = {
    "dust": Hazard(id="dust", label="dusty attic dust", sneeze=True, discomfort=2, tags={"dust"}),
    "flowers": Hazard(id="flowers", label="pollen from the park flowers", sneeze=True, discomfort=3, tags={"pollen"}),
    "smoke": Hazard(id="smoke", label="campfire smoke", sneeze=True, discomfort=4, tags={"smoke"}),
    "breeze": Hazard(id="breeze", label="a cool breeze", sneeze=False, discomfort=1, tags={"breeze"}),
}

FIXES = {
    "switch_suit": Fix(id="switch_suit", label="switch suits", phrase="swapped the old gear for a hypoallergenic suit", strength=4, sense=3, tags={"suit"}),
    "clean_up": Fix(id="clean_up", label="clean up the air", phrase="opened a window and cleared the air", strength=2, sense=2, tags={"air"}),
    "calm_down": Fix(id="calm_down", label="calm down", phrase="helped everyone breathe slowly", strength=1, sense=1, tags={"calm"}),
}

MISSIONS = {
    "rescue_day": "a rescue day above the city",
    "practice": "hero practice before sunset",
    "patrol": "a rooftop patrol at noon",
}

NAMES = ["Nova", "Kai", "Mina", "Zane", "Luna", "Finn", "Riley", "Aria"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for costume_id, costume in COSTUMES.items():
        for hazard_id, hazard in HAZARDS.items():
            for fix_id, fix in FIXES.items():
                if mishap_risk(costume, hazard) or costume.hypoallergenic:
                    if fix.sense >= 2:
                        combos.append((costume_id, hazard_id, fix_id))
    return combos


def explain_rejection(costume: Costume, hazard: Hazard) -> str:
    if not mishap_risk(costume, hazard):
        return "(No story: this setup does not create a real superhero lesson. Pick a hazard that can trigger the hypoallergenic problem.)"
    return "(No story: the fix is too weak for this superhero lesson.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero storyworld: karate, a hypoallergenic suit, and a lesson learned."
    )
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--sidekick", choices=NAMES)
    ap.add_argument("--mentor", choices=["mother", "father", "adult"])
    ap.add_argument("--costume", choices=COSTUMES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--mission", choices=MISSIONS)
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
    if args.costume and args.hazard and not mishap_risk(COSTUMES[args.costume], HAZARDS[args.hazard]):
        raise StoryError(explain_rejection(COSTUMES[args.costume], HAZARDS[args.hazard]))
    combos = [c for c in valid_combos()
              if (args.costume is None or c[0] == args.costume)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    costume_id, hazard_id, fix_id = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    sidekick = args.sidekick or rng.choice([n for n in NAMES if n != hero])
    mentor = args.mentor or rng.choice(["mother", "father", "adult"])
    mission = args.mission or rng.choice(list(MISSIONS))
    return StoryParams(
        hero_name=hero,
        hero_type="boy" if hero in {"Kai", "Zane", "Finn"} else "girl",
        sidekick_name=sidekick,
        sidekick_type="girl" if sidekick in {"Nova", "Mina", "Luna", "Aria", "Riley"} else "boy",
        mentor_type=mentor,
        costume=costume_id,
        hazard=hazard_id,
        fix=fix_id,
        mission=mission,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a 3-to-5-year-old that includes the words "karate" and "hypoallergenic".',
        f"Tell a lesson-learned story where {f['hero'].id} wants to do karate on a rooftop, but a safe, hypoallergenic choice matters.",
        "Write a bright superhero rescue story where a child learns to choose gear that won't cause sneezing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    mentor = f["mentor"]
    costume = f["costume"]
    hazard = f["hazard"]
    fix = f["fix"]
    qa = [
        QAItem(
            question="What did the hero want to do?",
            answer=f"{hero.id} wanted to practice karate like a real superhero, and the team was trying to finish the mission together."
        ),
        QAItem(
            question="Why did the sidekick warn them?",
            answer=f"{sidekick.id} warned them because {costume.label} could bring on a sneezy problem when {hazard.label} was in the air. That meant the mission needed a safer choice."
        ),
        QAItem(
            question="What did the mentor do to help?",
            answer=f"{mentor.label_word.capitalize()} came in and {fix.phrase}. That fixed the trouble and helped the heroes keep going safely."
        ),
        QAItem(
            question="What lesson did they learn?",
            answer="They learned that brave heroes do not just move fast; they also choose the safe gear. A hypoallergenic choice can be the smartest kind of strong."
        ),
    ]
    if f["outcome"] == "mishap":
        qa.append(
            QAItem(
                question="What happened before the lesson?",
                answer=f"The wrong suit made the sidekick sneeze, and the rooftop mission got messy for a moment. After that, everyone saw why the safer gear mattered."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    items = []
    items.append(QAItem(
        question="What does hypoallergenic mean?",
        answer="Hypoallergenic means it is made to be less likely to cause sneezing or skin trouble. People choose it when they want something gentler."
    ))
    items.append(QAItem(
        question="What is karate?",
        answer="Karate is a kind of martial art with kicks, blocks, and careful practice. People learn it by training their bodies and being controlled."
    ))
    if f["hazard"].sneeze:
        items.append(QAItem(
            question="Why can dust or pollen be a problem?",
            answer="Dust and pollen can make some people sneeze or feel scratchy. That is why a clean, gentle suit can help."
        ))
    items.append(QAItem(
        question="What should a superhero do before a mission?",
        answer="A superhero should check the gear, listen to warnings, and pick safe tools. That keeps the mission strong from the start."
    ))
    return items


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
        if e.hypoallergenic:
            bits.append("hypoallergenic=True")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for cid, c in COSTUMES.items():
        lines.append(asp.fact("costume", cid))
        if c.hypoallergenic:
            lines.append(asp.fact("hypoallergenic", cid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.sneeze:
            lines.append(asp.fact("sneeze", hid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("strength", fid, f.strength))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
good_combo(C,H,F) :- costume(C), hazard(H), fix(F), sense(F,S), sense_min(M), S >= M.
mishap(C,H) :- costume(C), hazard(H), not hypoallergenic(C), sneeze(H).
lesson_learned :- good_combo(C,H,F).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show good_combo/3."))
    return sorted(set(asp.atoms(model, "good_combo")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gates.")
    try:
        sample = generate(resolve_params(argparse.Namespace(hero=None, sidekick=None, mentor=None, costume=None, hazard=None, fix=None, mission=None), random.Random(7)))
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams(hero_name="Nova", hero_type="girl", sidekick_name="Kai", sidekick_type="boy", mentor_type="mother", costume="cape", hazard="dust", fix="switch_suit", mission="rescue_day"),
    StoryParams(hero_name="Aria", hero_type="girl", sidekick_name="Finn", sidekick_type="boy", mentor_type="father", costume="gloves", hazard="flowers", fix="clean_up", mission="practice"),
    StoryParams(hero_name="Zane", hero_type="boy", sidekick_name="Luna", sidekick_type="girl", mentor_type="adult", costume="suit", hazard="smoke", fix="switch_suit", mission="patrol"),
]


def generate(params: StoryParams) -> StorySample:
    for key in ("costume", "hazard", "fix"):
        if getattr(params, key) not in globals()[key.upper() + "S"]:
            raise StoryError(f"Unknown {key}: {getattr(params, key)}")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show good_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
