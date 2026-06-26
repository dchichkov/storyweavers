#!/usr/bin/env python3
"""
A standalone Storyweavers storyworld for a small adventure tale centered on a
probe, inner monologue, teamwork, and a moral choice.

The world is a compact expedition: a child, a helper friend, and a short
journey across a cliff path toward a hidden garden gate. They carry a probe to
test a risky path. The tension is whether they will rush ahead or work together,
listen to the quiet inner voice that says "be careful and be fair," and choose a
kind, honest plan.

This script follows the Storyweavers world contract:
- self-contained stdlib storyworld
- imports shared result containers eagerly
- lazy imports asp only in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    signal: str
    risk: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Probe:
    id: str
    label: str
    verb: str
    use: str
    guards: set[str]
    fits: set[str]


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    risk_kind: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Moral:
    id: str
    value: str
    note: str
    action: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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


SETTINGS = {
    "ridge": Setting(place="the windy ridge", signal="the path curled like a ribbon over stone", risk="a hidden drop", affords={"bridge", "cave"}),
    "cove": Setting(place="the salt cove", signal="the tide whispered at the rocks", risk="a slippery ledge", affords={"bridge"}),
    "ruins": Setting(place="the old ruins", signal="broken arches leaned over moss", risk="a loose floor tile", affords={"cave", "bridge"}),
}

CHALLENGES = {
    "bridge": Challenge(
        id="bridge",
        verb="cross the old bridge",
        gerund="crossing the old bridge",
        rush="dash onto the planks",
        danger="the planks might crack",
        risk_kind="dangerous",
        zone={"feet"},
        keyword="bridge",
        tags={"bridge", "wood"},
    ),
    "cave": Challenge(
        id="cave",
        verb="enter the dark cave",
        gerund="entering the dark cave",
        rush="step into the shadows",
        danger="the ground could sink",
        risk_kind="dangerous",
        zone={"feet"},
        keyword="cave",
        tags={"cave", "dark"},
    ),
}

PROBES = {
    "stick_probe": Probe(
        id="stick_probe",
        label="a smooth probe stick",
        verb="probe the ground",
        use="tap the path first",
        guards={"dangerous"},
        fits={"bridge", "cave"},
    ),
    "rope_probe": Probe(
        id="rope_probe",
        label="a rope probe",
        verb="probe the edge",
        use="test the edge with a rope loop",
        guards={"dangerous"},
        fits={"bridge"},
    ),
}

MORALS = {
    "honesty": Moral(id="honesty", value="honesty", note="tell the truth about what you find", action="be honest"),
    "teamwork": Moral(id="teamwork", value="teamwork", note="share the job so nobody gets hurt", action="work together"),
}

NAMES = ["Ari", "Mina", "Tess", "Noah", "Finn", "Luca", "June", "Pia"]
SECOND_NAMES = ["Rae", "Sol", "Bram", "Ivy", "Kai", "Rin"]
TYPES = ["girl", "boy"]
PARENTS = ["mother", "father"]
TRAITS = ["brave", "curious", "steady", "quick-thinking", "kind"]


def challenge_unsafe(ch: Challenge) -> bool:
    return ch.risk_kind == "dangerous"


def select_probe(ch: Challenge) -> Optional[Probe]:
    for probe in PROBES.values():
        if ch.id in probe.fits and challenge_unsafe(ch):
            return probe
    return None


@dataclass
class StoryParams:
    place: str
    challenge: str
    probe: str
    name: str
    companion: str
    gender: str
    parent: str
    trait: str
    moral: str
    seed: Optional[int] = None


def intro_line(hero: Entity, companion: Entity, setting: Setting, challenge: Challenge) -> str:
    return (
        f"{hero.id} and {companion.id} set out for {setting.place} after breakfast, "
        f"drawn by the promise of {challenge.verb}."
    )


def inner_monologue(hero: Entity, challenge: Challenge, setting: Setting, moral: Moral) -> str:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    return (
        f"In {hero.pronoun('possessive')} quiet thoughts, {hero.id} wondered if "
        f"{setting.risk} was waiting ahead. {hero.pronoun().capitalize()} told "
        f"{hero.pronoun('object')} to {moral.action} and not rush."
    )


def teamwork_setup(hero: Entity, companion: Entity, probe: Probe) -> str:
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    companion.memes["trust"] = companion.memes.get("trust", 0) + 1
    return (
        f"{companion.id} held up {probe.label}, and {hero.id} nodded. "
        f"They agreed to {probe.use} before going farther."
    )


def risk_update(world: World, hero: Entity, challenge: Challenge, probe: Probe) -> None:
    world.zone = set(challenge.zone)
    hero.meters[challenge.id] = hero.meters.get(challenge.id, 0) + 1
    hero.memes["alert"] = hero.memes.get("alert", 0) + 1
    if probe and challenge.id in probe.fits:
        hero.memes["confidence"] = hero.memes.get("confidence", 0) + 1


def progress_with_probe(world: World, hero: Entity, companion: Entity, challenge: Challenge, probe: Probe) -> list[str]:
    out = []
    out.append(f"They let the {probe.label} touch the ground first.")
    if challenge.id == "bridge":
        out.append("The stick found a soft plank, and the friends stepped around it.")
    else:
        out.append("The stick found a loose patch, and the friends chose the firmer stones instead.")
    world.facts["safe"] = True
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    companion.memes["joy"] = companion.memes.get("joy", 0) + 1
    return out


def moral_turn(hero: Entity, companion: Entity, moral: Moral, challenge: Challenge) -> str:
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    companion.memes["pride"] = companion.memes.get("pride", 0) + 1
    return (
        f"{hero.id} told {companion.id} the truth about the shaky spot, because "
        f"{moral.value} meant nobody should pretend the danger was smaller than it was."
    )


def ending_image(hero: Entity, companion: Entity, setting: Setting, probe: Probe, challenge: Challenge, moral: Moral) -> str:
    return (
        f"By sunset, {hero.id} and {companion.id} were on the far side of {setting.place}, "
        f"carrying {probe.label} back in calm hands. {moral.note.capitalize()}, and "
        f"the path behind them looked safe in the last orange light."
    )


def tell(setting: Setting, challenge: Challenge, probe_def: Probe, hero_name: str, companion_name: str,
         gender: str, parent: str, trait: str, moral: Moral) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, meters={}, memes={}))
    companion = world.add(Entity(id=companion_name, kind="character", type="boy" if gender == "girl" else "girl", meters={}, memes={}))
    _parent = world.add(Entity(id=parent, kind="character", type=parent, meters={}, memes={}))

    world.say(f"{hero.id} was a {trait} child who loved adventure, especially when a small problem could be solved with care.")
    world.say(f"{companion.id} was {hero.id}'s best helper on long walks, always ready to carry gear and listen.")
    world.say(intro_line(hero, companion, setting, challenge))

    world.para()
    world.say(f"At {setting.signal}, {hero.id} felt a tiny knot of worry.")
    world.say(inner_monologue(hero, challenge, setting, moral))
    world.say(teamwork_setup(hero, companion, probe_def))

    world.para()
    world.say(f"They reached the place where {setting.risk} seemed possible.")
    risk_update(world, hero, challenge, probe_def)
    world.say(f"{hero.id} wanted to {challenge.rush}, but {companion.id} waited for the probe to do its work.")
    world.say(progress_with_probe(world, hero, companion, challenge, probe_def)[0])
    world.say(progress_with_probe(world, hero, companion, challenge, probe_def)[1])
    world.say(moral_turn(hero, companion, moral, challenge))

    world.para()
    world.say(ending_image(hero, companion, setting, probe_def, challenge, moral))

    world.facts.update(hero=hero, companion=companion, parent=_parent, setting=setting, challenge=challenge, probe=probe_def, moral=moral)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a young child about a {f["probe"].label} and a careful crossing.',
        f"Tell a gentle adventure where {f['hero'].id} and {f['companion'].id} work together, listen to a quiet inner voice, and choose {f['moral'].value}.",
        f'Create a simple story that includes the word "probe" and ends with a safe, kind choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    setting: Setting = f["setting"]
    challenge: Challenge = f["challenge"]
    probe: Probe = f["probe"]
    moral: Moral = f["moral"]
    return [
        QAItem(
            question=f"Why did {hero.id} pause before {challenge.verb} at {setting.place}?",
            answer=f"{hero.id} paused because {hero.pronoun('possessive')} quiet thoughts warned that {setting.risk} might be ahead, so {hero.pronoun()} chose to be careful.",
        ),
        QAItem(
            question=f"How did {hero.id} and {companion.id} use the {probe.label} during the adventure?",
            answer=f"They worked together and used {probe.label} to test the path first, which helped them avoid the risky spot.",
        ),
        QAItem(
            question=f"What moral value did the story show when the friends reached the dangerous place?",
            answer=f"The story showed {moral.value}, because {hero.id} told the truth about the danger and they chose a safer way together.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the friends had crossed safely, their worry had turned into confidence, and the {probe.label} had helped them protect each other.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a probe?", answer="A probe is a tool or object used to test or inspect something carefully before going farther."),
        QAItem(question="What is teamwork?", answer="Teamwork means people help one another and share the job so the task becomes easier and safer."),
        QAItem(question="What is a moral value?", answer="A moral value is a good way of behaving, like honesty or kindness, that helps people choose well."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="ridge", challenge="bridge", probe="stick_probe", name="Ari", companion="Mina", gender="boy", parent="mother", trait="brave", moral="teamwork"),
    StoryParams(place="ruins", challenge="cave", probe="stick_probe", name="June", companion="Kai", gender="girl", parent="father", trait="curious", moral="honesty"),
    StoryParams(place="cove", challenge="bridge", probe="rope_probe", name="Noah", companion="Rae", gender="boy", parent="mother", trait="steady", moral="teamwork"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for ch_id in setting.affords:
            ch = CHALLENGES[ch_id]
            for probe in PROBES.values():
                if ch.id in probe.fits and challenge_unsafe(ch):
                    combos.append((place, ch_id, probe.id))
    return combos


def select_gender(name: str) -> str:
    return "girl" if name in {"Mina", "June", "Rae", "Pia"} else "boy"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.challenge and args.probe:
        ch = CHALLENGES[args.challenge]
        pr = PROBES[args.probe]
        if ch.id not in pr.fits or not challenge_unsafe(ch):
            raise StoryError("The chosen probe does not reasonably help with that challenge.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.probe is None or c[2] == args.probe)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge, probe = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(NAMES)
    gender = args.gender or select_gender(hero_name)
    companion = args.companion or rng.choice([n for n in SECOND_NAMES if n != hero_name])
    parent = args.parent or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS)
    moral = args.moral or rng.choice(list(MORALS))
    return StoryParams(place=place, challenge=challenge, probe=probe, name=hero_name, companion=companion,
                       gender=gender, parent=parent, trait=trait, moral=moral)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CHALLENGES[params.challenge], PROBES[params.probe],
                 params.name, params.companion, params.gender, params.parent, params.trait, MORALS[params.moral])
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with a probe, teamwork, and moral choice.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--probe", choices=PROBES)
    ap.add_argument("--name")
    ap.add_argument("--companion")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--moral", choices=MORALS)
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for r in sorted(c.zone):
            lines.append(asp.fact("zone", cid, r))
        lines.append(asp.fact("danger", cid, c.risk_kind))
    for pid, p in PROBES.items():
        lines.append(asp.fact("probe", pid))
        for f in sorted(p.fits):
            lines.append(asp.fact("fits", pid, f))
        for g in sorted(p.guards):
            lines.append(asp.fact("guards", pid, g))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Ch, Probe) :- affords(Place, Ch), danger(Ch, dangerous), probe(Probe), fits(Probe, Ch).
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
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, challenge, probe) combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
