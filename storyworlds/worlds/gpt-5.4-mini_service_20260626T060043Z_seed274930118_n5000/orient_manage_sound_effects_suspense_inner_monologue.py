#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/orient_manage_sound_effects_suspense_inner_monologue.py
================================================================================================

A small, heartwarming story world about a child helping with sound effects for
a tiny show. The core tension is whether the stage will be ready in time, and
the resolution comes from orienting the props, managing the cues, and finding a
kind, steady way to help together.

Seed idea:
---
A child gets to help at a little community show. The child has to orient the
sound board, manage the sound effects, and stay calm while a suspenseful moment
makes the room go quiet. The child thinks hard inside, then solves a small
problem with help from a gentle adult or friend.

This file follows the Storyweavers contract:
- standalone stdlib script
- imports shared results eagerly
- lazy imports storyworlds.asp only inside ASP helpers
- includes Python reasonableness gate and inline ASP twin
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Cue:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    problem: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    cue: str
    gear: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


CUE_KINDS = {
    "rustle": Cue(
        id="rustle",
        verb="make the leaf-rustle sound",
        gerund="making leaf-rustle sounds",
        rush="rush to the prop box",
        mess="scattered",
        problem="scattered everywhere",
        zone={"hands"},
        keyword="rustle",
        tags={"sound", "suspense"},
    ),
    "drumroll": Cue(
        id="drumroll",
        verb="play the drumroll",
        gerund="playing a drumroll",
        rush="hurry to the drum",
        mess="noisy",
        problem="too loud",
        zone={"hands"},
        keyword="drumroll",
        tags={"sound", "suspense"},
    ),
    "doorcreak": Cue(
        id="doorcreak",
        verb="make the door-creak sound",
        gerund="making a door-creak",
        rush="tiptoe to the sound board",
        mess="jumpy",
        problem="spooky",
        zone={"hands"},
        keyword="creak",
        tags={"sound", "suspense"},
    ),
    "gentlebells": Cue(
        id="gentlebells",
        verb="ring the gentle bells",
        gerund="ringing gentle bells",
        rush="reach for the bells",
        mess="bright",
        problem="shiny",
        zone={"hands"},
        keyword="bells",
        tags={"sound", "heartwarming"},
    ),
}

GEAR = [
    Gear("labels", "sticky labels", {"hands"}, {"scattered", "jumpy", "noisy", "bright"}, "put on sticky labels first", "carefully labeled the little controls"),
    Gear("headphones", "small headphones", {"ears"}, {"noisy"}, "put on small headphones", "slipped on the headphones and kept the room calm"),
    Gear("clipboard", "a tiny clipboard", {"hands"}, {"scattered"}, "grab a tiny clipboard", "held the clipboard and checked each cue"),
]

SETTINGS = {
    "community_hall": Setting("the community hall", True, {"rustle", "drumroll", "doorcreak", "gentlebells"}),
    "school_stage": Setting("the school stage", True, {"rustle", "drumroll", "gentlebells"}),
    "back_room": Setting("the back room", True, {"doorcreak", "gentlebells"}),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Ella", "Zoe", "Ava", "Ruby"]
BOY_NAMES = ["Owen", "Leo", "Ben", "Noah", "Finn", "Max", "Theo", "Eli"]
TRAITS = ["careful", "brave", "kind", "curious", "patient", "gentle"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_scatter(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("scattered", 0) < THRESHOLD:
            continue
        for e in world.entities.values():
            if e.worn_by == actor.id:
                sig = ("scatter", actor.id, e.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                out.append(f"{actor.id} had to pause and gather the pieces back together.")
    return out


def _r_calm_noise(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("noisy", 0) < THRESHOLD:
            continue
        sig = ("noise", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0) + 1
        out.append(f"The room felt a little too loud, and {actor.id} took a slow breath.")
    return out


RULES = [Rule("scatter", _r_scatter), Rule("calm_noise", _r_calm_noise)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def select_gear(cue: Cue) -> Optional[Gear]:
    for gear in GEAR:
        if cue.mess in gear.guards:
            return gear
    return None


def cue_is_reasonable(cue: Cue, gear: Gear) -> bool:
    return cue.mess in gear.guards and bool(cue.zone & gear.covers)


def cue_at_risk(cue: Cue) -> bool:
    return True


def predict_issue(world: World, actor: Entity, cue: Cue) -> dict:
    sim = world.copy()
    _do_cue(sim, sim.get(actor.id), cue, narrate=False)
    return {
        "worry": sim.get(actor.id).memes.get("worry", 0),
        "scattered": sim.get(actor.id).meters.get("scattered", 0),
    }


def _do_cue(world: World, actor: Entity, cue: Cue, narrate: bool = True) -> None:
    if cue.id not in world.setting.affords:
        return
    world.zone = set(cue.zone)
    actor.meters[cue.mess] = actor.meters.get(cue.mess, 0) + 1
    if cue.id == "drumroll":
        actor.memes["suspense"] = actor.memes.get("suspense", 0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.traits[0]} {hero.type} who liked to help where the room felt important.")


def orient(world: World, hero: Entity, helper: Entity) -> None:
    world.say(f"{hero.id} had to orient the sound table before the show began, and {hero.pronoun('possessive')} {helper.label_word} trusted {hero.pronoun('object')} to try.")
    world.say(f"{hero.id} looked at the little knobs, the cue cards, and the tiny red light, and {hero.pronoun()} thought, 'I can manage this.'")


def setup_sound(world: World, hero: Entity, cue: Cue) -> None:
    world.say(f"{hero.id} loved {cue.gerund}, because each tiny sound made the pretend story feel real.")
    world.say(f"Tonight the tricky part was the suspense cue, the one that made everyone go quiet and wait.")


def arrives(world: World, hero: Entity, helper: Entity, cue: Cue) -> None:
    world.say(f"One evening, {hero.id} and {hero.pronoun('possessive')} {helper.label_word} went to {world.setting.place}.")
    world.say(f"The little stage waited in the middle, and the air felt ready for {cue.keyword}.")


def wants(world: World, hero: Entity, cue: Cue) -> None:
    world.say(f"{hero.id} wanted to {cue.verb}, but the board looked a little tangled.")
    world.say(f"Inside, {hero.id} wondered, 'What if I press the wrong button?'")
    hero.memes["inner_monologue"] = hero.memes.get("inner_monologue", 0) + 1


def warn(world: World, helper: Entity, hero: Entity, cue: Cue) -> bool:
    pred = predict_issue(world, hero, cue)
    if pred["scattered"] < THRESHOLD and pred["worry"] < THRESHOLD:
        return False
    world.say(f'"If the cue cards get mixed up, the suspense sound could come at the wrong time," {helper.label_word} said gently.')
    return True


def hesitate(world: World, hero: Entity, cue: Cue) -> None:
    hero.memes["suspense"] = hero.memes.get("suspense", 0) + 1
    world.say(f"{hero.id} held still for a moment, listening to the quiet before the next cue.")
    world.say(f"Inside, {hero.id} thought, 'I want to help, and I want to do it kindly.'")


def manage(world: World, helper: Entity, hero: Entity, cue: Cue) -> Optional[Gear]:
    gear = select_gear(cue)
    if gear is None:
        return None
    if not cue_is_reasonable(cue, gear):
        return None
    ent = world.add(Entity(id=gear.id, type="gear", label=gear.label, owner=hero.id, caretaker=helper.id, plural=gear.plural))
    ent.worn_by = hero.id
    if predict_issue(world, hero, cue)["scattered"] >= THRESHOLD and gear.id != "labels":
        ent.worn_by = None
        del world.entities[ent.id]
        return None
    world.say(f"Then {helper.label_word} smiled and said, 'How about we {gear.prep} and try together?'")
    return gear


def accept(world: World, helper: Entity, hero: Entity, cue: Cue, gear: Gear) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    hero.memes["worry"] = 0
    world.say(f"{hero.id} nodded and felt the tight knot in {hero.pronoun('possessive')} chest loosen.")
    world.say(f"They {gear.tail}, and soon {hero.id} was {cue.gerund}, with the little stage glowing softly beside {hero.pronoun('object')}.")


def tell(setting: Setting, cue: Cue, gear_cfg: Gear, hero_name: str = "Mina", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, helper_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["careful", "gentle"])))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["cue"] = cue

    intro(world, hero)
    setup_sound(world, hero, cue)
    orient(world, hero, helper)

    world.para()
    arrives(world, hero, helper, cue)
    wants(world, hero, cue)
    warn(world, helper, hero, cue)
    hesitate(world, hero, cue)

    world.para()
    gear = manage(world, helper, hero, cue)
    if gear:
        accept(world, helper, hero, cue, gear)
    world.facts["gear"] = gear
    return world


KNOWLEDGE = {
    "sound": [
        ("What is a sound effect?", "A sound effect is a small sound made to help a story, game, or show feel alive."),
        ("Why do people use sound effects?", "People use sound effects to help the audience imagine what is happening."),
    ],
    "suspense": [
        ("What is suspense?", "Suspense is the waiting feeling you get when you wonder what will happen next."),
    ],
    "inner_monologue": [
        ("What is inner monologue?", "Inner monologue is the quiet thinking inside your head that other people do not hear."),
    ],
    "heartwarming": [
        ("What makes a story heartwarming?", "A heartwarming story leaves you feeling cared for, hopeful, and glad that people helped each other."),
    ],
    "labels": [
        ("What are labels for?", "Labels help you know what something is or where it belongs."),
    ],
}


@dataclass
class StoryParamsLike:
    place: str
    cue: str
    gear: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    cue = f["cue"]
    return [
        f'Write a heartwarming short story for a young child that includes the words "orient" and "manage".',
        f"Tell a gentle story about {hero.id}, who wants to {cue.verb}, but first must orient the sound board and manage the suspense.",
        f"Write a small community-show story where a child thinks aloud, helps with sound effects, and finds a calm, kind solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    cue: Cue = f["cue"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"What did {hero.id} have to orient before the show began?",
            answer=f"{hero.id} had to orient the sound table before the show began so the little cue cards and knobs would make sense.",
        ),
        QAItem(
            question=f"What sound effect did {hero.id} want to manage at the community hall?",
            answer=f"{hero.id} wanted to manage the {cue.keyword} cue, which was the suspense sound for the tiny show.",
        ),
        QAItem(
            question=f"What did {helper.label_word} say that helped {hero.id} feel calmer?",
            answer=f"{helper.label_word} suggested that they take it slowly and use a safer plan, which helped {hero.id} feel less worried.",
        ),
    ]
    if gear is not None:
        qa.append(QAItem(
            question=f"How did {gear.label} help {hero.id} manage the cue?",
            answer=f"They used {gear.label} to keep the controls organized, so {hero.id} could manage the cue without getting mixed up.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["cue"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag in ["sound", "suspense", "inner_monologue", "heartwarming", "labels"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="community_hall", cue="rustle", gear="labels", name="Mina", gender="girl", helper="mother", trait="careful"),
    StoryParams(place="school_stage", cue="drumroll", gear="labels", name="Owen", gender="boy", helper="father", trait="brave"),
    StoryParams(place="back_room", cue="doorcreak", gear="labels", name="Luna", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="community_hall", cue="gentlebells", gear="labels", name="Eli", gender="boy", helper="father", trait="gentle"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for cue_id in setting.affords:
            cue = CUE_KINDS[cue_id]
            for gear in GEAR:
                if cue_is_reasonable(cue, gear):
                    combos.append((place, cue_id, gear.id))
    return combos


def explain_rejection(cue: Cue, gear: Gear) -> str:
    return f"(No story: the {gear.label} does not meaningfully help with {cue.keyword}, so this version would not have a real compromise.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming story world about orienting and managing sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--cue", choices=CUE_KINDS)
    ap.add_argument("--gear", choices=[g.id for g in GEAR])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
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
    if args.cue and args.gear:
        cue = CUE_KINDS[args.cue]
        gear = next(g for g in GEAR if g.id == args.gear)
        if not cue_is_reasonable(cue, gear):
            raise StoryError(explain_rejection(cue, gear))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.cue is None or c[1] == args.cue)
              and (args.gear is None or c[2] == args.gear)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, cue_id, gear_id = rng.choice(sorted(combos))
    cue = CUE_KINDS[cue_id]
    gear = next(g for g in GEAR if g.id == gear_id)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, cue=cue_id, gear=gear_id, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CUE_KINDS[params.cue], next(g for g in GEAR if g.id == params.gear),
                 params.name, params.gender, [params.trait], params.helper)
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


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for c in sorted(s.affords):
            lines.append(asp.fact("affords", pid, c))
    for cid, cue in CUE_KINDS.items():
        lines.append(asp.fact("cue", cid))
        lines.append(asp.fact("mess_of", cid, cue.mess))
        for r in sorted(cue.zone):
            lines.append(asp.fact("zones", cid, r))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


ASP_RULES = r"""
reasonably_matches(C,G) :- cue(C), gear(G), mess_of(C,M), guards(G,M), zones(C,R), covers(G,R).
valid(P,C,G) :- affords(P,C), reasonably_matches(C,G).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cue, gear) combos:\n")
        for p, c, g in combos:
            print(f"  {p:15} {c:12} {g}")
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.cue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
