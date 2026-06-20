#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/brittle_oomph_practice_sound_effects_conflict_transformation.py
===============================================================================================

A standalone storyworld in a small space-adventure domain.

Premise:
- Two kids are in a tiny starship playroom.
- They are practicing sound effects for a space show.
- One child wants to use a brittle old prop as a "meteor" sound maker.
- The other warns it will crack and cause a conflict.
- A calm grown-up helps transform the brittle prop into a safe practice object.
- The ending proves the change by giving the children a better sound effect tool.

This world is built to satisfy the Storyweavers contract:
- typed entities with physical meters and emotional memes
- a Python reasonableness gate plus inline ASP twin
- three QA sets grounded in world state
- complete CLI with --all, -n, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
SENSE_MIN = 2

GIRL_NAMES = ["Luna", "Mira", "Nova", "Ivy", "Aria", "Cleo", "Zoe", "Nia"]
BOY_NAMES = ["Finn", "Theo", "Milo", "Eli", "Otis", "Jace", "Noah", "Pax"]
TRAITS = ["careful", "curious", "steady", "clever", "patient", "brave"]


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
class Setting:
    id: str
    place: str
    view: str
    mood: str
    dark: str


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    sound: str
    brittleness: int
    safe_transform: str
    flinch: str
    brittle: bool = False
    makes_sound: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Practice:
    id: str
    label: str
    phrase: str
    action: str
    rehearsal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_conflict(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.role != "practicer":
            continue
        if ent.memes["defiance"] >= THRESHOLD and ent.memes["warning"] >= THRESHOLD:
            sig = ("conflict", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["conflict"] += 1
            out.append("__conflict__")
    return out


def _r_crack(world: World) -> list[str]:
    out = []
    prop = world.facts.get("prop_ent")
    if not prop:
        return out
    if prop.meters["stress"] < THRESHOLD:
        return out
    sig = ("crack", prop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prop.meters["cracked"] += 1
    world.get("room").meters["mess"] += 1
    out.append("__crack__")
    return out


CAUSAL_RULES = [Rule("conflict", "social", _r_conflict), Rule("crack", "physical", _r_crack)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def reasonableness_ok(prop: Prop, practice: Practice) -> bool:
    return prop.brittle and practice.id in {"practice", "rehearse"} and prop.makes_sound


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(prop: Prop, delay: int) -> int:
    return prop.brittleness + delay


def is_transformed(response: Response, prop: Prop, delay: int) -> bool:
    return response.power >= fire_severity(prop, delay)


def predict(world: World, prop_id: str) -> dict:
    sim = world.copy()
    _use_prop(sim, sim.get(prop_id), narrate=False)
    return {
        "cracked": sim.get(prop_id).meters["cracked"] >= THRESHOLD,
        "mess": sim.get("room").meters["mess"],
    }


def _use_prop(world: World, prop: Entity, narrate: bool = True) -> None:
    prop.meters["stress"] += 1
    prop.meters["used"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, a: Entity, b: Entity, setting: Setting, practice: Practice) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a quiet afternoon in {setting.place}, {a.id} and {b.id} turned the playroom "
        f"into {setting.view}. {setting.mood} lights blinked across the walls, and {setting.dark} "
        f"made the far corner feel like deep space."
    )
    world.say(
        f'"We are practicing for the space show," {a.id} said. "{practice.action}!"'
    )


def need_sound(world: World, practice: Practice) -> None:
    world.say(
        f"But the ship was quiet, and the children needed a sound for the meteor scene. "
        f"They looked at their props and listened to the silence."
    )
    world.say(f'"We need {practice.label}," one of them whispered.')


def tempt(world: World, a: Entity, prop: Prop) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'{a.id} picked up {prop.phrase}. "{prop.sound}" {a.id} said. '
        f'"It will sound perfect for the meteor crash."'
    )
    world.say("The idea felt exciting for one bright second.")


def warn(world: World, b: Entity, a: Entity, prop: Prop) -> None:
    b.memes["warning"] += 1
    pred = predict(world, prop.id)
    world.facts["predicted_mess"] = pred["mess"]
    world.say(
        f'{b.id} frowned. "{a.id}, that prop is brittle. If you slam it too hard, '
        f"it might crack."'
    )
    world.say(
        f'"I know," {b.id} added softly. "We are in the middle of {world.facts["practice"].label}, '
        f"not a real crash."'
    )


def defy(world: World, a: Entity) -> None:
    world.say(f'"Oomph!" {a.id} said, and tried it anyway.')


def break_sound(world: World, prop_ent: Entity, prop: Prop) -> None:
    _use_prop(world, prop_ent)
    world.say(
        f'{prop.sound} went the prop, then — "crick!" — its edge snapped. '
        f"A brittle piece bounced across the floor."
    )


def alarm(world: World, b: Entity, a: Entity, prop: Prop) -> None:
    world.say(
        f'"{a.id}!" {b.id} cried. "Stop! It broke!"'
    )


def transform(world: World, parent: Entity, response: Response, prop_ent: Entity, prop: Prop, practice: Practice) -> None:
    prop_ent.meters["stress"] = 0.0
    prop_ent.meters["cracked"] = 0.0
    world.get("room").meters["mess"] = 0.0
    body = response.text.replace("{prop}", prop.label)
    world.say(
        f"{parent.label_word.capitalize()} came in calmly and {body}."
    )
    world.say(
        f"The old thing changed from a brittle crash prop into {prop.safe_transform}, "
        f"and the children could keep practicing."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, prop: Prop, practice: Practice) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {parent.label_word.capitalize()} smiled and said, "
        f'"You can make a big sound without hurting the prop. Practice is for learning, '
        f'not for breaking things."'
    )
    world.say(f'"We know," {a.id} and {b.id} said together, a little sheepish and a lot calmer.')
    world.say(
        f"They tried {practice.rehearsal}, and the room filled with the right kind of noise."
    )


def finish(world: World, a: Entity, b: Entity, practice: Practice, prop: Prop) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["confidence"] += 1
    world.say(
        f"By the end, the playroom was no longer quiet. {practice.rehearsal} made a cheerful "
        f"{prop.sound.lower()}-style sound, and the children grinned at the safe result."
    )
    world.say(
        f"The brittle prop stayed whole enough to use again, and the space show went on."
    )


def tell(setting: Setting, prop: Prop, practice: Practice, response: Response,
         kid1: str = "Luna", kid1_gender: str = "girl",
         kid2: str = "Milo", kid2_gender: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    a = world.add(Entity(kid1, "character", kid1_gender, role="practicer"))
    b = world.add(Entity(kid2, "character", kid2_gender, role="cautioner"))
    parent = world.add(Entity("Parent", "character", parent_type, label="the parent", role="parent"))
    room = world.add(Entity("room", "room", label="the playroom"))
    prop_ent = world.add(Entity("prop", "thing", label=prop.label))
    world.facts.update(setting=setting, prop=prop, practice=practice, response=response, prop_ent=prop_ent, delay=delay)
    setup(world, a, b, setting, practice)
    need_sound(world, practice)
    world.para()
    tempt(world, a, prop)
    warn(world, b, a, prop)
    world.para()
    if reasonableness_ok(prop, practice):
        defy(world, a)
        break_sound(world, prop_ent, prop)
        alarm(world, b, a, prop)
        contained = is_transformed(response, prop, delay)
        world.para()
        if contained:
            transform(world, parent, response, prop_ent, prop, practice)
            lesson(world, parent, a, b, prop, practice)
            world.para()
            finish(world, a, b, practice, prop)
            outcome = "transformed"
        else:
            world.say(
                f"{parent.label_word.capitalize()} tried to help, but the crack had already made a mess."
            )
            world.say(
                f"The children still got out safely, yet the room felt sad and quiet after the noise."
            )
            outcome = "brittle"
    else:
        world.say("They paused and chose a safer rehearsal sound right away.")
        world.say(
            f"{practice.rehearsal} worked better than a crash, and the playroom stayed calm."
        )
        outcome = "avoided"
    world.facts.update(instigator=a, cautioner=b, parent=parent, outcome=outcome)
    return world


@dataclass
class StoryParams:
    setting: str
    prop: str
    practice: str
    response: str
    kid1: str
    kid1_gender: str
    kid2: str
    kid2_gender: str
    parent: str
    delay: int = 0
    seed: Optional[int] = None


SETTINGS = {
    "playroom_ship": Setting("playroom_ship", "the ship-shaped playroom", "a tiny starship bridge", "soft", "the dim window"),
    "garage_cargo": Setting("garage_cargo", "the garage corner", "a cargo bay with cardboard stars", "flickering", "the shadow by the shelf"),
    "hallway_launch": Setting("hallway_launch", "the hallway", "a moon tunnel of blankets and chairs", "glowy", "the far end of the corridor"),
}

PROPS = {
    "brittle_panel": Prop("brittle_panel", "a brittle panel", "brittle panel", "Oomph!", 2, "a safe sound pad", "a loud crack", True, True, {"brittle"}),
    "brittle_crate": Prop("brittle_crate", "a brittle crate lid", "brittle crate lid", "Crunch!", 3, "a padded practice drum", "a sharp snap", True, True, {"brittle"}),
    "brittle_shell": Prop("brittle_shell", "a brittle shell prop", "brittle shell prop", "Whack!", 4, "a foam meteor", "a worrying rattle", True, True, {"brittle"}),
}

PRACTICES = {
    "practice": Practice("practice", "practice", "practice", "strike the beat", "a steady tap-tap rhythm", {"practice"}),
    "rehearse": Practice("rehearse", "practice sound effects", "practice sound effects", "make the meteor sound", "a soft boom-boom with the drum", {"practice", "sound"}),
    "sound_effects": Practice("sound_effects", "sound effects", "sound effects", "match the crash sound", "a safe whoosh with their hands", {"sound"}),
}

RESPONSES = {
    "pad": Response("pad", 3, 4, "set the cracked piece onto a padded table and taped the edges into a safe shape", "could not stop the crack from spreading", "set the cracked piece onto a padded table and taped the edges into a safe shape", {"safe"}),
    "foam": Response("foam", 3, 5, "swapped the brittle prop for a foam version and kept the same big space sound", "the foam piece was too late to help", "swapped the brittle prop for a foam version and kept the same big space sound", {"safe"}),
    "repair": Response("repair", 2, 3, "glued the brittle piece back together and turned it into a practice prop", "the repair did not hold", "glued the brittle piece back together and turned it into a practice prop", {"safe"}),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, p in PROPS.items():
            for rid, r in PRACTICES.items():
                if p.brittle and r.id in {"practice", "rehearse", "sound_effects"}:
                    combos.append((sid, pid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with brittle props, practice sounds, conflict, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--practice", choices=PRACTICES)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.prop and args.practice:
        if not reasonableness_ok(PROPS[args.prop], PRACTICES[args.practice]):
            raise StoryError("That prop and practice do not make a reasonable space-adventure conflict.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.prop is None or c[1] == args.prop)
              and (args.practice is None or c[2] == args.practice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prop, practice = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    parent = args.parent or rng.choice(["mother", "father"])
    k1 = rng.choice(GIRL_NAMES)
    k2 = rng.choice([n for n in BOY_NAMES if n != k1])
    g1 = "girl"
    g2 = "boy"
    return StoryParams(setting, prop, practice, response, k1, g1, k2, g2, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROPS[params.prop], PRACTICES[params.practice], RESPONSES[params.response],
                 params.kid1, params.kid1_gender, params.kid2, params.kid2_gender, params.parent, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure story for a young child that includes the words "brittle", "oomph", and "practice".',
        f"Tell a story where {f['instigator'].id} and {f['cautioner'].id} are practicing sound effects in a starship playroom and disagree about a brittle prop.",
        f"Write a gentle conflict-and-transformation story about space play, sound effects, and a safe replacement for a brittle object.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent = f["instigator"], f["cautioner"], f["parent"]
    prop, practice = f["prop"], f["practice"]
    qa = [
        ("What were the children doing?", f"They were practicing {practice.label} in a space-themed playroom. They wanted the sound to feel big and exciting for their pretend starship show."),
        ("Why did the cautioning child worry?", f"{b.id} worried because the prop was brittle and could crack if it was hit too hard. That would make a mess and ruin the practice."),
        ("What happened after the loud sound?", f"The prop cracked, and the room changed from quiet pretend space into a messy conflict. The crack showed that the brittle object could not handle the rough sound effect."),
    ]
    if f["outcome"] == "transformed":
        qa.append(("How did the grown-up help?", f"{parent.id} helped by turning the brittle prop into {prop.safe_transform}. That change kept the space show going and gave the children a safer way to practice."))
        qa.append(("How did the story end?", f"It ended with the children using a safer sound and smiling in the starship playroom. The brittle thing had become something useful instead of something breakable."))
    elif f["outcome"] == "avoided":
        qa.append(("How was the conflict prevented?", f"The children stopped before the prop cracked and chose a safer rehearsal sound instead. That let them keep practicing without breaking anything."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["prop"].tags) | set(f["practice"].tags)
    out = []
    if "brittle" in tags:
        out.append(("What does brittle mean?", "Brittle means something breaks or snaps easily when it is pressed, bent, or hit.")) 
    if "practice" in tags:
        out.append(("Why do people practice?", "People practice so they can get better at a skill, remember the steps, and feel more confident.")) 
    if "sound" in tags or f["practice"].id == "sound_effects":
        out.append(("What are sound effects?", "Sound effects are made-up or special sounds that help a story, show, or game feel more real and exciting."))
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if p.brittle:
            lines.append(asp.fact("brittle", pid))
        lines.append(asp.fact("brittleness", pid, p.brittleness))
    for rid in PRACTICES:
        lines.append(asp.fact("practice", rid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
reasonably_valid(S, P, R) :- setting(S), prop(P), practice(R), brittle(P).
conflict_happens(P, R) :- brittle(P), practice(R).
transformed(RS) :- chosen_response(RS), power(RS, P), prop_brittleness(B), delay(D), P >= B + D.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonably_valid/3."))
    return sorted(set(asp.atoms(model, "reasonably_valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("prop_brittleness", PROPS[params.prop].brittleness),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show transformed/1."))
    return "transformed" if asp.atoms(model, "transformed") else "avoided"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    # smoke test generation
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, prop=None, practice=None, response=None, parent=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: generation smoke test passed.")
    return rc


CURATED = [
    StoryParams("playroom_ship", "brittle_panel", "practice", "foam", "Luna", "girl", "Milo", "boy", "mother", 0),
    StoryParams("garage_cargo", "brittle_crate", "rehearse", "pad", "Nova", "girl", "Finn", "boy", "father", 0),
    StoryParams("hallway_launch", "brittle_shell", "sound_effects", "repair", "Mira", "girl", "Theo", "boy", "mother", 0),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def explain_rejection(prop: Prop, practice: Practice) -> str:
    return f"(No story: {prop.label} and {practice.label} do not create a reasonable space-adventure conflict.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prop and args.practice and not reasonableness_ok(PROPS[args.prop], PRACTICES[args.practice]):
        raise StoryError(explain_rejection(PROPS[args.prop], PRACTICES[args.practice]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.prop is None or c[1] == args.prop)
              and (args.practice is None or c[2] == args.practice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prop, practice = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    parent = args.parent or rng.choice(["mother", "father"])
    kid1 = rng.choice(GIRL_NAMES)
    kid2 = rng.choice([n for n in BOY_NAMES if n != kid1])
    return StoryParams(setting, prop, practice, response, kid1, "girl", kid2, "boy", parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROPS[params.prop], PRACTICES[params.practice], RESPONSES[params.response],
                 params.kid1, params.kid1_gender, params.kid2, params.kid2_gender, params.parent, params.delay)
    return StorySample(params=params, story=world.render(),
                        prompts=generation_prompts(world),
                        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
                        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
                        world=world)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure world with brittle props, practice sounds, conflict, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--practice", choices=PRACTICES)
    ap.add_argument("--response", choices=RESPONSES)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show reasonably_valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for item in combos[:50]:
            print(item)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
