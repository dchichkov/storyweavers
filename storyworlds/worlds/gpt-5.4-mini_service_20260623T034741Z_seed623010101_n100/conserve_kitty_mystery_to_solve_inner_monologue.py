#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/conserve_kitty_mystery_to_solve_inner_monologue.py
===============================================================================================================

A tiny space-adventure storyworld about a child astronaut, a mysteriously missing
kitty, and a careful habit of conserving ship resources while solving the mystery.
The story includes an inner monologue beat and a concrete reveal that changes the
world state.

Premise:
- On a small starship, a young crewmate notices something strange: the ship's
  soft little kitty is missing from its usual pod.
- The crewmate thinks through clues quietly while conserving oxygen, battery,
  and calm.
- The mystery resolves when the crewmate follows the right clues and finds the
  kitty hiding where a warm, quiet place made sense.
- The ending proves what changed by showing the kitty back where it belongs and
  the ship still running carefully.

The domain is intentionally small and constraint-checked:
- A location can hide the kitty only if it plausibly supports it.
- A clue route can only be chosen if it matches the location's evidence.
- The AS P twin mirrors the Python reasonableness gate.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    worn_by: Optional[str] = None
    contains: set[str] = field(default_factory=set)
    location: str = ""

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
class Habitat:
    id: str
    label: str
    phrase: str
    supports: set[str] = field(default_factory=set)
    cues: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    place: str
    evidence: str
    reveals: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Resource:
    id: str
    label: str
    phrase: str
    conserving: str
    meter: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def conserve_resource(world: World, actor: Entity, resource: Resource) -> None:
    actor.memes["care"] += 1
    actor.meters[resource.meter] += 1
    world.say(
        f"{actor.id} took a slow breath and decided to {resource.conserving}. "
        f"{actor.pronoun().capitalize()} wanted to solve the mystery without wasting anything."
    )


def ask_inner_monologue(world: World, actor: Entity, clue: str) -> None:
    world.say(
        f'Inside {actor.pronoun("possessive")} head, a quiet thought whispered: '
        f'"If I follow the clue near {clue}, maybe the kitty is hiding there."'
    )


def follow_clue(world: World, actor: Entity, clue: Clue, habitat: Habitat) -> None:
    actor.memes["curiosity"] += 1
    world.say(
        f"{actor.id} drifted toward {clue.place}. {actor.pronoun().capitalize()} noticed "
        f"{clue.evidence} and felt the mystery tighten into a real trail."
    )
    world.say(
        f"{actor.id}'s thinking grew sharper: the clue pointed to {habitat.label}."
    )


def find_kitty(world: World, actor: Entity, kitty: Entity, habitat: Habitat) -> None:
    kitty.location = habitat.id
    kitty.meters["found"] += 1
    actor.memes["relief"] += 1
    world.say(
        f"There, tucked inside {habitat.phrase}, was the kitty at last. "
        f"{actor.id} smiled because the clue had been right all along."
    )


def restore_ship(world: World, actor: Entity, resource: Resource) -> None:
    actor.meters[resource.meter] = max(0.0, actor.meters[resource.meter] - 1.0)
    world.say(
        f"{actor.id} carried the kitty back to the command nook and kept {resource.conserving} "
        f"through the whole walk. The ship stayed calm, bright, and careful."
    )


def tell(world_name: str, habitat: Habitat, clue: Clue, resource: Resource,
         hero_name: str = "Nova", hero_type: str = "girl") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="solver"))
    parent = world.add(Entity(id="Captain", kind="character", type="adult", label="the captain"))
    kitty = world.add(Entity(id="kitty", kind="character", type="kitty", label="the kitty"))
    ship = world.add(Entity(id="ship", kind="place", type="ship", label="the ship"))

    hero.attrs["world_name"] = world_name
    hero.attrs["mission"] = "mystery"
    hero.meters["oxygen"] = 0.0
    hero.meters["battery"] = 0.0
    hero.memes["curiosity"] = 0.0
    hero.memes["care"] = 0.0
    hero.memes["relief"] = 0.0
    kitty.location = "missing"
    ship.contains.add("kitty")
    world.facts.update(
        hero=hero,
        parent=parent,
        kitty=kitty,
        ship=ship,
        habitat=habitat,
        clue=clue,
        resource=resource,
    )

    world.say(
        f"On a little starship, {hero.id} noticed that the kitty was missing from {ship.label}."
    )
    world.say(
        f"{hero.id} loved the soft purr and the warm glow it brought to the control room, "
        f"so the missing kitty felt like a real mystery to solve."
    )

    world.para()
    conserve_resource(world, hero, resource)
    ask_inner_monologue(world, hero, clue.label)
    follow_clue(world, hero, clue, habitat)

    world.para()
    find_kitty(world, hero, kitty, habitat)
    restore_ship(world, hero, resource)
    world.say(
        f"At the end, the kitty was back on board, and {hero.id} had solved the mystery "
        f"by thinking carefully instead of rushing."
    )
    return world


SETTINGS = {
    "engine_room": Habitat(
        id="engine_room",
        label="the engine room",
        phrase="the warm engine room",
        supports={"warm", "humming", "hidey"},
        cues={"warm", "humming"},
    ),
    "cargo_bay": Habitat(
        id="cargo_bay",
        label="the cargo bay",
        phrase="the cargo bay between the crates",
        supports={"quiet", "shadow", "hidey"},
        cues={"quiet", "shadow"},
    ),
    "observation_dome": Habitat(
        id="observation_dome",
        label="the observation dome",
        phrase="the glass observation dome",
        supports={"bright", "open"},
        cues={"bright", "open"},
    ),
}

CLUES = {
    "warm_hum": Clue(
        id="warm_hum",
        label="a warm hum",
        place="the engine room",
        evidence="a soft hum and a little tuft of fur near the vent",
        reveals="engine_room",
        tags={"warm", "hidey"},
    ),
    "quiet_shadow": Clue(
        id="quiet_shadow",
        label="a quiet shadow",
        place="the cargo bay",
        evidence="one tiny paw print in the dust beside a crate",
        reveals="cargo_bay",
        tags={"quiet", "shadow"},
    ),
    "bright_glint": Clue(
        id="bright_glint",
        label="a bright glint",
        place="the observation dome",
        evidence="there was only reflected starlight and no place to hide",
        reveals="observation_dome",
        tags={"bright"},
    ),
}

RESOURCES = {
    "oxygen": Resource(
        id="oxygen",
        label="oxygen",
        phrase="the oxygen meters",
        conserving="conserve oxygen",
        meter="oxygen",
        tags={"oxygen", "conserve"},
    ),
    "battery": Resource(
        id="battery",
        label="battery",
        phrase="the battery charge",
        conserving="conserve battery power",
        meter="battery",
        tags={"battery", "conserve"},
    ),
}

KITTY_NAMES = ["Mochi", "Comet", "Pip", "Orbit"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for hid, habitat in SETTINGS.items():
        for cid, clue in CLUES.items():
            if clue.reveals == hid and clue.tags <= habitat.supports | habitat.cues:
                for rid in RESOURCES:
                    combos.append((hid, cid, rid))
    return combos


@dataclass
class StoryParams:
    setting: str
    clue: str
    resource: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure mystery with a kitty and careful conserving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--resource", choices=RESOURCES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.resource is None or c[2] == args.resource)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, resource = rng.choice(sorted(combos))
    hero_type = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(KITTY_NAMES)
    return StoryParams(setting=setting, clue=clue, resource=resource,
                       hero_name=hero_name, hero_type=hero_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure story for a young child that includes the words "conserve" and "kitty".',
        f"Tell a mystery-to-solve story where {f['hero'].id} finds the missing kitty by following {f['clue'].label} and remembering to conserve {f['resource'].label}.",
        f"Write a gentle spaceship story with an inner monologue where the hero thinks carefully, saves resources, and finds the kitty.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, kitty, clue, resource, habitat = f["hero"], f["kitty"], f["clue"], f["resource"], f["habitat"]
    return [
        QAItem(
            question=f"What mystery was {hero.id} trying to solve on the ship?",
            answer=f"{hero.id} was trying to solve the mystery of the missing kitty. The clues led toward {habitat.label}, where the kitty was hiding.",
        ),
        QAItem(
            question=f"What did {hero.id} think about quietly before following {clue.label}?",
            answer=f"{hero.id} thought that the clue might lead to the kitty if {hero.pronoun('possessive')} stayed calm. That inner monologue helped {hero.id} conserve {resource.label} and keep thinking clearly.",
        ),
        QAItem(
            question=f"How did {hero.id} help the ship conserve {resource.label}?",
            answer=f"{hero.id} moved carefully and did not rush around the ship. That meant the crew could conserve {resource.label} while solving the mystery.",
        ),
        QAItem(
            question=f"Where was the kitty found?",
            answer=f"The kitty was found in {habitat.phrase}. The clue matched that hiding place, so the mystery had a satisfying answer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["resource"].tags) | set(world.facts["clue"].tags) | {"kitty"}
    out = []
    if "conserve" in tags:
        out.append(QAItem("What does it mean to conserve something?", "To conserve something means to use only what you need and save the rest for later. On a ship, that helps keep important supplies ready.")
)
    out.append(QAItem("What is a kitty?", "A kitty is a small cat. In stories, a kitty can be a pet that people care about and look for when it goes missing."))
    out.append(QAItem("What is a mystery?", "A mystery is something puzzling that you do not understand right away. You solve it by looking for clues and thinking carefully."))
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
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(S, C, R) :- setting(S), clue(C), resource(R), clue_reveals(C, S).
story_hint(conserve) :- resource_tag(oxygen).
story_hint(conserve) :- resource_tag(battery).
story_hint(kitty) :- kitty_present.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for tag in sorted(s.supports | s.cues):
            lines.append(asp.fact("setting_tag", sid, tag))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_reveals", cid, c.reveals))
        for tag in sorted(c.tags):
            lines.append(asp.fact("clue_tag", cid, tag))
    for rid, r in RESOURCES.items():
        lines.append(asp.fact("resource", rid))
        for tag in sorted(r.tags):
            lines.append(asp.fact("resource_tag", tag))
    lines.append(asp.fact("kitty_present"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH between python and clingo gates")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        ok = False
    if ok:
        print(f"OK: {len(py)} valid combos; generation smoke test passed.")
        return 0
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS.get(params.setting)
    clue = CLUES.get(params.clue)
    resource = RESOURCES.get(params.resource)
    if not setting or not clue or not resource:
        raise StoryError("Invalid story parameters.")
    if clue.reveals != setting.id:
        raise StoryError("The clue does not match the setting.")
    world = tell(setting.id, setting, clue, resource, params.hero_name, params.hero_type)
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
    StoryParams(setting="engine_room", clue="warm_hum", resource="oxygen", hero_name="Nova", hero_type="girl"),
    StoryParams(setting="cargo_bay", clue="quiet_shadow", resource="battery", hero_name="Sol", hero_type="boy"),
    StoryParams(setting="engine_room", clue="warm_hum", resource="battery", hero_name="Iris", hero_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
