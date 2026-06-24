#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T063717Z_seed1230577450_n50/consistency_diffuse_tidal_pool_dialogue_magic_inner.py
=============================================================================================================

A standalone storyworld for a small mythic tidal-pool domain.

Premise:
- In a tidal pool, the tide repeats with great consistency.
- A young keeper wants to share a pearl with a shy sea-spirit.
- Diffuse moon-magic can spread a message, but only if it is focused by an oath.
- Dialogue and inner monologue drive the turn.
- The ending proves what changed: the tide remains steady, and the spirit is no longer hidden.

The story engine supports:
- story text
- three QA sets
- trace output
- JSON output
- an inline ASP twin and parity verification

The prose aims for a small mythic tone: concrete, child-facing, and gently legendary.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    title: str = ""
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def name(self) -> str:
        return self.title or self.label or self.id


@dataclass
class Place:
    id: str
    name: str
    tides: str
    stones: str
    waters: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Force:
    id: str
    name: str
    verb: str
    noun: str
    diffusion: str
    requires_focus: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    name: str
    phrase: str
    shimmer: str
    at_risk_by: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        other = World(self.place)
        other.entities = json.loads(json.dumps({k: _entity_to_plain(v) for k, v in self.entities.items()}))
        # reconstruct lightly
        restored: dict[str, Entity] = {}
        for k, v in other.entities.items():
            restored[k] = Entity(**v)
        other.entities = restored
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


def _entity_to_plain(e: Entity) -> dict:
    return {
        "id": e.id,
        "kind": e.kind,
        "type": e.type,
        "label": e.label,
        "title": e.title,
        "role": e.role,
        "owner": e.owner,
        "meters": e.meters,
        "memes": e.memes,
    }


SETTINGS: dict[str, Place] = {
    "tidal_pool": Place(
        id="tidal_pool",
        name="the tidal pool",
        tides="The tide came and went as steadily as a drumbeat.",
        stones="Black stones ringed the water like old watching seals.",
        waters="Clear water flashed silver in the hollows.",
        tags={"tide", "pool", "sea"},
    )
}

FORCES: dict[str, Force] = {
    "diffuse_magic": Force(
        id="diffuse_magic",
        name="diffuse moon-magic",
        verb="send",
        noun="message",
        diffusion="spread thinly across the water",
        requires_focus=True,
        tags={"magic", "diffuse"},
    )
}

RELICS: dict[str, Relic] = {
    "shell_pearl": Relic(
        id="shell_pearl",
        name="shell-pearl",
        phrase="a small pearl in a shell cup",
        shimmer="it shone like a star caught in a spoon",
        at_risk_by={"salt_spray"},
    )
}

NAMES = ["Mira", "Neri", "Tala", "Sori", "Ira", "Luna"]
GUARDIANS = ["watcher", "keeper", "child"]
SPIRIT_NAMES = ["Tide-Sister", "Little Reef-Spirit", "Moss-Voice", "Sea-Whisper"]


def reasonableness_gate(place: Place, force: Force, relic: Relic) -> bool:
    if place.id != "tidal_pool":
        return False
    if force.id != "diffuse_magic":
        return False
    return "salt_spray" in relic.at_risk_by


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tagged", pid, t))
    for fid, f in FORCES.items():
        lines.append(asp.fact("force", fid))
        lines.append(asp.fact("requires_focus", fid))
        for t in sorted(f.tags):
            lines.append(asp.fact("force_tag", fid, t))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        for t in sorted(r.at_risk_by):
            lines.append(asp.fact("at_risk_by", rid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, F, R) :- place(P), force(F), relic(R),
                        tagged(P, tide), force_tag(F, diffuse), at_risk_by(R, salt_spray).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in SETTINGS.items():
        for fid, force in FORCES.items():
            for rid, relic in RELICS.items():
                if reasonableness_gate(place, force, relic):
                    out.append((pid, fid, rid))
    return out


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


@dataclass
class StoryParams:
    place: str
    force: str
    relic: str
    keeper_name: str
    spirit_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic tidal-pool storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--force", choices=FORCES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--keeper-name")
    ap.add_argument("--spirit-name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.force is None or c[1] == args.force)
              and (args.relic is None or c[2] == args.relic)]
    if not combos:
        raise StoryError("(No valid tidal-pool story matches the given options.)")
    place, force, relic = rng.choice(combos)
    return StoryParams(
        place=place,
        force=force,
        relic=relic,
        keeper_name=args.keeper_name or rng.choice(NAMES),
        spirit_name=args.spirit_name or rng.choice(SPIRIT_NAMES),
    )


def _add_inner(world: World, text: str) -> None:
    world.say(f"Inner Monologue: {text}")


def _dialogue(speaker: str, text: str) -> str:
    return f'"{text}" said {speaker}.'


def generate(params: StoryParams) -> StorySample:
    place = SETTINGS[params.place]
    force = FORCES[params.force]
    relic = RELICS[params.relic]

    world = World(place)
    keeper = world.add(Entity(id="keeper", kind="character", type="child", label=params.keeper_name, role="keeper"))
    spirit = world.add(Entity(id="spirit", kind="character", type="spirit", label=params.spirit_name, role="spirit"))
    pearl = world.add(Entity(id="pearl", kind="object", type="relic", label=relic.name, title=relic.phrase, owner="spirit"))

    keeper.memes["wonder"] = 1
    keeper.memes["consistency"] = 1
    spirit.memes["shyness"] = 1
    spirit.memes["hidden"] = 1
    pearl.meters["shine"] = 1

    world.say(f"At {place.name}, {place.tides}")
    world.say(place.stones)
    world.say(f"{keeper.label} found {pearl.title}; {pearl.title} {relic.shimmer}.")
    _add_inner(world, f"{keeper.label} thought the sea always returned in the same way; that kind of consistency felt like a promise.")
    world.para()
    world.say(f"{keeper.label} watched the foam and spoke to the empty water: {_dialogue(keeper.label, 'Who listens when the moon is thin?')}")
    world.say(f"From behind a dark stone, {spirit.label} answered: {_dialogue(spirit.label, 'I listen, but I do not like to be seen.')}")
    _add_inner(world, f"{keeper.label} wondered if a message could reach such a shy heart without breaking apart.")
    world.say(f"{keeper.label} lifted one hand and tried {force.name}, letting it {force.diffusion}.")
    world.say(f"The magic was beautiful, but it could not keep its shape for long.")
    if force.requires_focus:
        world.say(f"So {keeper.label} pressed the shell close and whispered a steady vow.")
        _add_inner(world, f"If the words stayed true, the magic might gather instead of fading.")
    world.para()
    world.say(f"{keeper.label} said, {_dialogue(keeper.label, 'I will keep your secret and bring you the pearl when the tide turns back.')}")
    world.say(f"{spirit.label} peered out and replied, {_dialogue(spirit.label, 'Then I will not hide from you.')}")
    spirit.memes["hidden"] = 0
    spirit.memes["trust"] = 1
    keeper.memes["joy"] = 1
    keeper.memes["peace"] = 1
    world.say(f"The tide stayed steady, the promise held, and {spirit.label} came to the edge of the water.")
    world.say(f"In the end, {keeper.label} placed {pearl.title} on a flat stone, and {spirit.label} touched it with a smiling hand.")
    world.say(f"The tidal pool still rose and fell in the same old rhythm, but now it held a friend.")

    world.facts.update(
        keeper=keeper,
        spirit=spirit,
        pearl=pearl,
        place=place,
        force=force,
        relic=relic,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a small myth about a tidal pool, a hidden spirit, and a promise that steadies magic.",
        f"Tell a mythic story set at {f['place'].name} where {f['keeper'].label} speaks to {f['spirit'].label} with dialogue and inner thought.",
        "Write a child-friendly legend in which diffuse magic must be guided by a vow so a shy sea-spirit will answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    k = world.facts["keeper"]
    s = world.facts["spirit"]
    p = world.facts["pearl"]
    place = world.facts["place"]
    force = world.facts["force"]
    return [
        QAItem(
            question=f"Where did {k.label} meet {s.label}?",
            answer=f"{k.label} met {s.label} at {place.name}, where the tide kept returning with calm consistency.",
        ),
        QAItem(
            question=f"What kind of magic did {k.label} use?",
            answer=f"{k.label} used {force.name}, which could spread thinly over the water unless it was guided by a steady promise.",
        ),
        QAItem(
            question=f"What did the pearl do in the end?",
            answer=f"The pearl ended up on a flat stone by the tidal pool, where {s.label} could touch it without fear.",
        ),
        QAItem(
            question=f"Why did {s.label} stay hidden at first?",
            answer=f"{s.label} stayed hidden because {s.label.lower() if hasattr(s, 'lower') else 'the spirit'} feared being seen, until {k.label}'s vow made the meeting feel safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tidal pool?",
            answer="A tidal pool is a shallow pocket of seawater left among rocks when the tide moves away.",
        ),
        QAItem(
            question="What does consistency mean?",
            answer="Consistency means something keeps happening in the same steady way again and again.",
        ),
        QAItem(
            question="What does diffuse mean?",
            answer="Diffuse means to spread out thinly, like mist or light across the water.",
        ),
        QAItem(
            question="Why can magic in a story need a vow?",
            answer="A vow can give a story magic a clear shape, so it does not drift away before it reaches the right heart.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} label={e.label} memes={e.memes} meters={e.meters}")
    return "\n".join(lines)


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


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
    StoryParams(place="tidal_pool", force="diffuse_magic", relic="shell_pearl", keeper_name="Mira", spirit_name="Tide-Sister"),
    StoryParams(place="tidal_pool", force="diffuse_magic", relic="shell_pearl", keeper_name="Tala", spirit_name="Little Reef-Spirit"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(args.n * 10, 10):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx + 1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
