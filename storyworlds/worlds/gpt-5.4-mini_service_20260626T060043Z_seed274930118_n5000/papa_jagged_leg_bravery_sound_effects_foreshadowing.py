#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/papa_jagged_leg_bravery_sound_effects_foreshadowing.py
==============================================================================================================================

A tiny bedtime story world about Papa, a jagged thing, a worried leg, and a
brave little turn of heart.

Premise:
- Papa and a child discover a jagged obstacle in a quiet evening setting.
- Papa worries that a leg might get scratched.
- Brave behavior, soft sound effects, and a foreshadowed safe choice lead to a
  gentle resolution.

This script follows the Storyweavers storyworld contract:
- typed entities with meters and memes
- state-driven prose
- generation, QA, JSON, trace, and ASP parity/verification support
"""

from __future__ import annotations

import argparse
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"risk": 0.0, "scratch": 0.0, "bravery": 0.0, "comfort": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "love": 0.0, "hope": 0.0, "calm": 0.0, "fear": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man", "papa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little porch"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    name: str
    sound: str
    foreshadow: str
    risk_line: str
    zone: set[str]
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeChoice:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
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
            self.events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _safe_items_for(hazard: Hazard) -> list[SafeChoice]:
    return [c for c in SAFE_CHOICES if hazard.mess in c.guards and hazard.zone.issubset(c.covers)]


def hazard_at_risk(hazard: Hazard, leg: Entity) -> bool:
    return "leg" in hazard.zone and leg.region == "leg"


def predict(world: World, papa: Entity, hazard: Hazard, leg_id: str) -> dict:
    sim = world.copy()
    _do_scene(sim, sim.get(papa.id), sim.facts["child"], hazard, narrate=False)
    leg = sim.get(leg_id)
    return {"scratched": leg.meters["scratch"] >= THRESHOLD}


def _do_scene(world: World, papa: Entity, child: Entity, hazard: Hazard, narrate: bool = True) -> None:
    if hazard.id not in world.setting.affords:
        return
    if world.facts.get("foreshadowed"):
        papa.memes["worry"] += 0.5
    papa.meters["risk"] += 1
    world.say(f"In the hush of evening, {hazard.foreshadow}")
    world.say(f"{hazard.sound} went the little sound in the quiet air.")
    child.meters["bravery"] += 1
    papa.memes["fear"] += 1
    if hazard_at_risk(hazard, world.facts["leg"]):
        world.facts["predicted"] = True
        world.say(f"{papa.id} looked at {world.facts['leg'].label} and said, '{hazard.risk_line}'")
    if narrate:
        for item in WORLD_RULES:
            item(world)


def rule_risk(world: World) -> None:
    papa = world.facts["papa"]
    leg = world.facts["leg"]
    hazard = world.facts["hazard"]
    sig = ("risk", hazard.id)
    if sig in world.fired:
        return
    if hazard_at_risk(hazard, leg):
        world.fired.add(sig)
        leg.meters["risk"] += 1
        papa.memes["worry"] += 1
        world.say(f"{papa.id} kept one careful eye on {leg.label}, because the jagged edge looked sharp.")


def rule_scrape(world: World) -> None:
    papa = world.facts["papa"]
    leg = world.facts["leg"]
    hazard = world.facts["hazard"]
    sig = ("scrape", hazard.id)
    if sig in world.fired:
        return
    if papa.meters["risk"] >= THRESHOLD and world.facts.get("step_close"):
        world.fired.add(sig)
        leg.meters["scratch"] += 1
        world.say(f"Scratch-swish! The edge nearly caught {papa.pronoun('possessive')} leg, but only a tiny nip of worry remained.")


def rule_calm(world: World) -> None:
    papa = world.facts["papa"]
    child = world.facts["child"]
    if world.facts.get("safe_choice") and papa.memes["worry"] >= THRESHOLD:
        papa.memes["worry"] = 0.0
        papa.memes["calm"] += 1
        child.memes["hope"] += 1
        world.say(f"{papa.id} breathed out slowly, and the room felt softer right away.")


WORLD_RULES = [rule_risk, rule_scrape, rule_calm]


def tell(world: World, papa: Entity, child: Entity, hazard: Hazard, safe: Optional[SafeChoice]) -> World:
    world.facts["papa"] = papa
    world.facts["child"] = child
    world.facts["hazard"] = hazard
    leg = world.add(Entity(id="leg", kind="thing", type="leg", label="the sleepy leg", region="leg"))
    world.facts["leg"] = leg

    world.say(f"{papa.id} was a kind papa who loved quiet nights and warm blankets.")
    world.say(f"The little child loved staying close to {papa.id} when the house sounded sleepy.")
    world.say(f"One night, {hazard.name} waited near the path like a tiny secret.")

    world.para()
    world.say(f"{hazard.foreshadow}")
    world.say(f"{hazard.sound} went the night air.")
    world.say(f"{child.id} pointed, and {papa.id} saw the {hazard.name} at once.")
    world.say(f'"{hazard.risk_line}" {papa.id} whispered.')

    world.facts["foreshadowed"] = True
    world.facts["step_close"] = True
    _do_scene(world, papa, child, hazard, narrate=True)

    world.para()
    if safe:
        world.facts["safe_choice"] = True
        world.say(f"{papa.id} held up a gentle hand and said, \"First we use {safe.label}.\"")
        world.say(f"{child.id} nodded bravely, even though the jagged edge still glinted in the lamplight.")
        world.say(f"Then they {safe.prep}.")
        if hazard.mess in safe.guards and "leg" in safe.covers:
            world.say(f"{safe.tail}.")
            leg.meters["scratch"] = 0.0
            papa.memes["worry"] = 0.0
            papa.memes["calm"] += 1
            child.memes["bravery"] += 1
            world.say(f"At last, {child.id} stepped past the jagged place without a scratch, and {papa.id} smiled.")
            world.say(f"The bedtime light made {leg.label} look safe and golden.")
        else:
            world.say(f"But the choice was not quite right, and the sharp place still felt too close.")
    else:
        world.say(f"They paused together and chose to wait until morning, when the sharp place could be moved safely.")

    return world


SETTINGS = {
    "porch": Setting(place="the little porch", indoor=False, affords={"jagged"}),
    "hall": Setting(place="the quiet hall", indoor=True, affords={"jagged"}),
    "garden_path": Setting(place="the garden path", indoor=False, affords={"jagged"}),
}

HAZARDS = {
    "jagged": Hazard(
        id="jagged",
        name="a jagged edge",
        sound="tick-tick",
        foreshadow="Before anyone moved, the shadow of the jagged edge made a warning shape on the floor.",
        risk_line="Careful now — that jagged edge could scratch a leg.",
        zone={"leg"},
        mess="scratch",
        tags={"jagged", "foreshadowing", "sound"},
    ),
}

SAFE_CHOICES = [
    SafeChoice(
        id="blanket",
        label="a folded blanket",
        prep="wrap the sharp place carefully",
        tail="The blanket softened the edge, so the path looked friendly again",
        covers={"leg"},
        guards={"scratch"},
    ),
    SafeChoice(
        id="stool",
        label="the little step stool",
        prep="move the stool between the leg and the edge",
        tail="The stool gave the jagged place a proper distance",
        covers={"leg"},
        guards={"scratch"},
    ),
]

PAPA_NAMES = ["Papa", "Pablo", "Noah", "Eli", "Jonah"]
CHILD_NAMES = ["Mina", "Tess", "Lulu", "Ivy", "Nico"]


@dataclass
class StoryParams:
    setting: str
    hazard: str
    safe_choice: str
    papa_name: str
    child_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime story world about Papa, a jagged edge, a leg, bravery, sound effects, and foreshadowing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--safe-choice", choices=[c.id for c in SAFE_CHOICES])
    ap.add_argument("--papa-name", choices=PAPA_NAMES)
    ap.add_argument("--child-name", choices=CHILD_NAMES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    hazard = args.hazard or rng.choice(list(HAZARDS))
    safe_choice = args.safe_choice or rng.choice([c.id for c in _safe_items_for(HAZARDS[hazard])])
    papa_name = args.papa_name or rng.choice(PAPA_NAMES)
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    if safe_choice not in {c.id for c in _safe_items_for(HAZARDS[hazard])}:
        raise StoryError("The chosen safe choice does not actually protect the leg from the jagged edge.")
    return StoryParams(setting=setting, hazard=hazard, safe_choice=safe_choice, papa_name=papa_name, child_name=child_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a bedtime story about Papa noticing a jagged edge before a sleepy leg gets scratched.",
        f"Tell a gentle story where {f['papa'].id} uses bravery and a soft sound effect to keep {f['leg'].label} safe.",
        "Use foreshadowing and a calming ending image in a child-friendly bedtime style.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    papa = f["papa"]
    child = f["child"]
    hazard = f["hazard"]
    leg = f["leg"]
    safe = f.get("safe")
    qa = [
        QAItem(
            question=f"Who was worried about the jagged edge in the story?",
            answer=f"{papa.id} was worried because the jagged edge could scratch {papa.pronoun('possessive')} leg.",
        ),
        QAItem(
            question=f"What sound did the jagged edge make in the quiet scene?",
            answer=f"It made a little {hazard.sound} sound, which helped foreshadow that it was sharp.",
        ),
        QAItem(
            question=f"What body part needed protecting?",
            answer=f"The leg needed protecting, because it was the part that could have been scratched.",
        ),
    ]
    if safe:
        qa.append(
            QAItem(
                question=f"How did Papa show bravery?",
                answer=f"{papa.id} showed bravery by staying calm, using {safe.label}, and helping {child.id} choose the safe way past the jagged edge.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small hint about something important before it happens.",
        ),
        QAItem(
            question="Why do sound effects help a bedtime story?",
            answer="Sound effects help make the scene feel alive and easy to imagine, like hearing a tiny tick-tick in the dark.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the careful or kind thing even when you feel a little scared.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
safe_choice(S) :- choice(S), protects_leg(S), guards_scratch(S).
valid_story(Set, Haz, Safe) :- setting(Set), hazard(Haz), safe_choice(Safe), affords(Set, Haz).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for h in sorted(s.affords):
            lines.append(asp.fact("affords", sid, h))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("hazard_name", hid, h.name))
        for z in sorted(h.zone):
            lines.append(asp.fact("zone", hid, z))
        lines.append(asp.fact("sound", hid, h.sound))
    for c in SAFE_CHOICES:
        lines.append(asp.fact("choice", c.id))
        for cov in sorted(c.covers):
            lines.append(asp.fact("covers", c.id, cov))
        for g in sorted(c.guards):
            lines.append(asp.fact("guards_scratch", c.id))
    lines.append(asp.fact("protects_leg", "blanket"))
    lines.append(asp.fact("protects_leg", "stool"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, h, s) for p in SETTINGS for h in HAZARDS for s in _safe_items_for(HAZARDS[h])}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid stories).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    papa = world.add(Entity(id=params.papa_name, kind="character", type="papa", label="Papa"))
    child = world.add(Entity(id=params.child_name, kind="character", type="child", label="the child"))
    safe = next(c for c in SAFE_CHOICES if c.id == params.safe_choice)
    hazard = HAZARDS[params.hazard]
    world.facts["safe"] = safe

    tell(world, papa, child, hazard, safe)
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
    StoryParams(setting="porch", hazard="jagged", safe_choice="blanket", papa_name="Papa", child_name="Mina"),
    StoryParams(setting="hall", hazard="jagged", safe_choice="stool", papa_name="Pablo", child_name="Tess"),
    StoryParams(setting="garden_path", hazard="jagged", safe_choice="blanket", papa_name="Noah", child_name="Lulu"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
