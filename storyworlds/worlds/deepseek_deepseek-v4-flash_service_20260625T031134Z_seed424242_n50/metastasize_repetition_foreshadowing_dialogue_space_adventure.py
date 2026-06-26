#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/metastasize_repetition_foreshadowing_dialogue_space_adventure.py
=============================================================================================================

A standalone story world sketch for a space adventure where a strange growth
metastasizes across a ship, and a young cadet must use repetition, foreshadowing,
and dialogue to save the crew.

Initial story (used to build a world model):
---
Once upon a time, there was a young cadet named Nova. She served on the starship
Stardancer, a bright vessel that explored the edges of known space. Nova loved
the hum of the engines and the way the stars streaked past the viewport.

One day, the ship's botanist found a strange purple crystal in a cargo pod.
"It's beautiful," the captain said. "We'll study it." But the crystal began to
grow. It metastasized through the hull, spreading purple veins across every
surface. The ship's systems flickered. The crew grew worried.

Nova noticed the pattern. "The crystal pulses every time we use the engines,"
she said. "It feeds on energy." The captain didn't listen. "We need the engines
to get home," he said.

The crystal metastasized faster. It covered the bridge. It reached the
engine room. Nova knew she had to act. "We must shut down the engines," she
said again. "The crystal metastasizes when we use power."

Finally, the captain agreed. They powered down the ship. The crystal stopped
growing. Nova used a small shuttle to tow the Stardancer to a nearby station.
The crew was safe. The crystal was contained.

Causal state updates:
---
    use_engine                    -> ship.energy += 1
                                    crystal.growth += 1
    crystal.growth >= threshold   -> crystal.metastasize += 1
                                    ship.damage += 1
    cadet.warning                  -> cadet.credibility += 1
    captain.ignore                 -> captain.stubbornness += 1
    captain.listen                 -> captain.trust += 1
    shutdown_engine                -> ship.energy = 0
                                    crystal.growth = 0
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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0
GROWTH_THRESHOLD = 3.0
METASTASIZE_THRESHOLD = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = "bridge"
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"cadet", "captain", "botanist", "engineer"}
        male = set()
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the starship Stardancer"
    danger_level: float = 0.0
    systems_online: bool = True


@dataclass
class Threat:
    id: str
    name: str
    verb: str
    effect: str
    warning: str
    solution: str
    keyword: str = "crystal"
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    label: str
    phrase: str
    action: str
    risk: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.warning_count: int = 0
        self.dialogue_count: int = 0

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.warning_count = self.warning_count
        clone.dialogue_count = self.dialogue_count
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_metastasize(world: World) -> list[str]:
    out: list[str] = []
    for entity in world.entities.values():
        if entity.type == "crystal" and entity.meters["growth"] >= GROWTH_THRESHOLD:
            sig = ("metastasize", entity.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            entity.meters["metastasize"] += 1
            world.setting.danger_level += 1
            for ship in world.entities.values():
                if ship.type == "ship":
                    ship.meters["damage"] += 1
            out.append(f"The crystal metastasized further across the ship.")
    return out


def _r_engine_use(world: World) -> list[str]:
    out: list[str] = []
    for entity in world.entities.values():
        if entity.type == "ship" and entity.meters["energy"] >= THRESHOLD:
            for crystal in world.entities.values():
                if crystal.type == "crystal":
                    sig = ("feed", crystal.id)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    crystal.meters["growth"] += 1
                    out.append("The crystal pulsed brighter as the engines hummed.")
    return out


def _r_dialogue_effect(world: World) -> list[str]:
    out: list[str] = []
    for cadet in world.characters():
        if cadet.type == "cadet" and cadet.memes["credibility"] >= THRESHOLD:
            for captain in world.characters():
                if captain.type == "captain":
                    sig = ("listen", captain.id)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    captain.memes["trust"] += 1
                    captain.memes["stubbornness"] = max(0, captain.memes["stubbornness"] - 1)
                    out.append("The captain finally listened.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="metastasize", tag="physical", apply=_r_metastasize),
    Rule(name="engine_use", tag="physical", apply=_r_engine_use),
    Rule(name="dialogue_effect", tag="social", apply=_r_dialogue_effect),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


THREATS = {
    "crystal": Threat(
        id="crystal",
        name="purple crystal",
        verb="metastasize",
        effect="spreading purple veins across every surface",
        warning="The crystal metastasizes when we use power",
        solution="shut down the engines",
        keyword="crystal",
        tags={"crystal", "growth", "energy"},
    ),
    "fungus": Threat(
        id="fungus",
        name="glowing fungus",
        verb="spread",
        effect="covering the walls with green spores",
        warning="The fungus spreads when we use the lights",
        solution="turn off the lights",
        keyword="fungus",
        tags={"fungus", "spores", "darkness"},
    ),
    "vines": Threat(
        id="vines",
        name="metal vines",
        verb="entangle",
        effect="wrapping around the machinery",
        warning="The vines entangle when we move the ship",
        solution="stop the ship",
        keyword="vines",
        tags={"vines", "metal", "entangle"},
    ),
}

SOLUTIONS = {
    "shutdown": Solution(
        label="shutdown",
        phrase="shut down the engines",
        action="powered down the ship",
        risk="drifting in space",
    ),
    "darkness": Solution(
        label="darkness",
        phrase="turn off all lights",
        action="plunged the ship into darkness",
        risk="navigating in the dark",
    ),
    "stop": Solution(
        label="stop",
        phrase="stop the ship completely",
        action="halted all movement",
        risk="being stranded",
    ),
}

CADET_NAMES = ["Nova", "Orion", "Vega", "Lyra", "Andromeda", "Phoenix", "Aurora", "Comet", "Nebula", "Star"]
CAPTAIN_NAMES = ["Rigel", "Sirius", "Altair", "Polaris", "Arcturus", "Vega", "Deneb", "Procyon", "Aldebaran", "Betelgeuse"]
TRAITS = ["brave", "clever", "observant", "determined", "resourceful", "patient"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for threat_id in THREATS:
        for solution_id in SOLUTIONS:
            combos.append((threat_id, solution_id))
    return combos


@dataclass
class StoryParams:
    threat: str
    solution: str
    cadet_name: str
    captain_name: str
    trait: str
    seed: Optional[int] = None


def introduce(world: World, cadet: Entity, captain: Entity) -> None:
    world.say(f"Once upon a time, there was a young cadet named {cadet.id}.")
    world.say(f"{cadet.pronoun('possessive').capitalize()} captain was {captain.id}, "
              f"a seasoned leader of the starship Stardancer.")
    world.say(f"{cadet.id} loved the hum of the engines and the way the stars "
              f"streaked past the viewport.")


def discover_threat(world: World, cadet: Entity, captain: Entity, threat: Threat) -> None:
    world.say(f"One day, the ship's botanist found a strange {threat.name} in a cargo pod.")
    world.say(f'"It\'s beautiful," {captain.id} said. "We\'ll study it."')
    world.say(f"But the {threat.keyword} began to grow.")
    world.say(f"It metastasized through the hull, {threat.effect}.")
    world.say(f"The ship's systems flickered. The crew grew worried.")


def foreshadow_warning(world: World, cadet: Entity, threat: Threat) -> None:
    world.say(f"{cadet.id} noticed the pattern.")
    world.say(f'"The {threat.keyword} pulses every time we use the engines," she said.')
    world.say(f'"It feeds on energy."')
    world.facts["foreshadow"] = True


def captain_ignores(world: World, captain: Entity, cadet: Entity) -> None:
    world.say(f"The captain didn't listen.")
    world.say(f'"We need the engines to get home," {captain.id} said.')
    captain.memes["stubbornness"] += 1


def threat_metastasizes(world: World, threat: Threat) -> None:
    world.say(f"The {threat.keyword} metastasized faster.")
    world.say(f"It covered the bridge. It reached the engine room.")
    for entity in world.entities.values():
        if entity.type == "crystal":
            entity.meters["growth"] += 2
    propagate(world)


def cadet_repeats_warning(world: World, cadet: Entity, threat: Threat) -> None:
    world.warning_count += 1
    world.say(f"{cadet.id} knew she had to act.")
    world.say(f'"We must shut down the engines," she said again.')
    world.say(f'"The {threat.keyword} metastasizes when we use power."')
    cadet.memes["credibility"] += 1
    propagate(world)


def captain_agrees(world: World, captain: Entity, cadet: Entity, solution: Solution) -> None:
    world.say(f"Finally, {captain.id} agreed.")
    world.say(f'"You were right, {cadet.id}. We {solution.action}."')
    captain.memes["trust"] += 1
    captain.memes["stubbornness"] = 0


def resolve(world: World, cadet: Entity, captain: Entity, threat: Threat, solution: Solution) -> None:
    world.say(f"They {solution.action}.")
    world.say(f"The {threat.keyword} stopped growing.")
    world.say(f"{cadet.id} used a small shuttle to tow the Stardancer to a nearby station.")
    world.say(f"The crew was safe. The {threat.keyword} was contained.")
    world.say(f"{captain.id} looked at {cadet.id} and smiled.")
    world.say(f'"Your persistence saved us," {captain.id} said.')
    world.say(f"{cadet.id} nodded. She had learned that sometimes you have to "
              f"say something more than once for it to be heard.")


def tell(threat_cfg: Threat, solution_cfg: Solution,
         cadet_name: str = "Nova", captain_name: str = "Rigel",
         cadet_traits: Optional[list[str]] = None) -> World:
    world = World(Setting())
    cadet = world.add(Entity(
        id=cadet_name, kind="character", type="cadet",
        traits=["young"] + (cadet_traits or ["brave", "observant"]),
    ))
    captain = world.add(Entity(
        id=captain_name, kind="character", type="captain",
        traits=["seasoned", "stubborn"],
    ))
    ship = world.add(Entity(
        id="Stardancer", kind="thing", type="ship",
        label="starship Stardancer",
    ))
    crystal = world.add(Entity(
        id="threat", type="crystal", label=threat_cfg.name,
        location="cargo pod",
    ))

    world.para()
    introduce(world, cadet, captain)

    world.para()
    discover_threat(world, cadet, captain, threat_cfg)

    world.para()
    foreshadow_warning(world, cadet, threat_cfg)

    world.para()
    captain_ignores(world, captain, cadet)

    world.para()
    threat_metastasizes(world, threat_cfg)

    world.para()
    cadet_repeats_warning(world, cadet, threat_cfg)

    world.para()
    captain_agrees(world, captain, cadet, solution_cfg)

    world.para()
    resolve(world, cadet, captain, threat_cfg, solution_cfg)

    world.facts.update(
        cadet=cadet,
        captain=captain,
        threat=threat_cfg,
        solution=solution_cfg,
        ship=ship,
        crystal=crystal,
        warning_count=world.warning_count,
        dialogue_count=world.dialogue_count,
    )
    return world


KNOWLEDGE = {
    "crystal": [("What is a crystal?",
                 "A crystal is a solid material with a repeating pattern inside. "
                 "Some crystals grow when they absorb energy.")],
    "growth": [("How do things grow in space?",
                "Things in space can grow when they absorb energy from stars, "
                "engines, or other power sources.")],
    "energy": [("What is energy?",
                "Energy is what makes things move and work. Engines use energy "
                "to push a ship through space.")],
    "metastasize": [("What does metastasize mean?",
                     "Metastasize means something spreads quickly to new places. "
                     "It is often used for things that grow out of control.")],
    "shutdown": [("Why would you shut down a ship's engines?",
                  "Shutting down engines stops the ship from moving and can "
                  "prevent dangerous things from growing or spreading.")],
    "dialogue": [("Why is talking important on a spaceship?",
                  "Talking helps the crew share ideas and warnings. Sometimes "
                  "you have to say something more than once for people to listen.")],
    "repetition": [("Why do people repeat themselves?",
                    "People repeat themselves to make sure others understand. "
                    "Repeating a warning can save lives.")],
    "foreshadow": [("What is foreshadowing?",
                    "Foreshadowing is when a story gives hints about what will "
                    "happen later. It helps prepare the reader.")],
}
KNOWLEDGE_ORDER = ["crystal", "growth", "energy", "metastasize", "shutdown",
                   "dialogue", "repetition", "foreshadow"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cadet, captain, threat = f["cadet"], f["captain"], f["threat"]
    return [
        f'Write a short space adventure story for a child about a {cadet.type} '
        f'named {cadet.id} who must stop a {threat.name} from metastasizing.',
        f"Tell a story where {cadet.id} uses repetition and dialogue to convince "
        f"{captain.id} to listen about the {threat.keyword}.",
        f'Write a simple story that includes the word "{threat.keyword}" and '
        f"shows how foreshadowing helps the crew survive.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cadet, captain, threat, solution = f["cadet"], f["captain"], f["threat"], f["solution"]
    qa: list[QAItem] = [
        QAItem(
            question=f"Who is the story about on the starship Stardancer?",
            answer=f"It is about a young {cadet.type} named {cadet.id} and "
                   f"her captain, {captain.id}. They face a {threat.name} "
                   f"that metastasizes through the ship.",
        ),
        QAItem(
            question=f"What did the crew find in the cargo pod?",
            answer=f"The crew found a strange {threat.name} in a cargo pod. "
                   f"It began to grow and metastasize across the ship.",
        ),
        QAItem(
            question=f"Why did {cadet.id} repeat her warning?",
            answer=f"{cadet.id} repeated her warning because {captain.id} "
                   f"did not listen the first time. She knew the {threat.keyword} "
                   f"would keep metastasizing if they used the engines.",
        ),
    ]
    if f.get("foreshadow"):
        qa.append(QAItem(
            question=f"How did {cadet.id} foreshadow the danger?",
            answer=f"{cadet.id} noticed the {threat.keyword} pulsed when the "
                   f"engines were used. She said it fed on energy, which was "
                   f"a hint about what would happen later.",
        ))
    qa.append(QAItem(
        question=f"How did the story end for {cadet.id} and {captain.id}?",
        answer=f"They {solution.action}. The {threat.keyword} stopped growing. "
               f"{captain.id} thanked {cadet.id} for her persistence. "
               f"The crew was safe.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["threat"].tags)
    tags.add("dialogue")
    tags.add("repetition")
    tags.add("foreshadow")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  warning_count={world.warning_count}")
    lines.append(f"  dialogue_count={world.dialogue_count}")
    lines.append(f"  danger_level={world.setting.danger_level}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        threat="crystal",
        solution="shutdown",
        cadet_name="Nova",
        captain_name="Rigel",
        trait="brave",
    ),
    StoryParams(
        threat="fungus",
        solution="darkness",
        cadet_name="Lyra",
        captain_name="Polaris",
        trait="clever",
    ),
    StoryParams(
        threat="vines",
        solution="stop",
        cadet_name="Orion",
        captain_name="Sirius",
        trait="determined",
    ),
]


def explain_rejection(threat: Threat, solution: Solution) -> str:
    return (f"(No story: {threat.name} and {solution.label} don't match. "
            f"Try a different combination.)")


ASP_RULES = r"""
threat(T) :- threat_id(T).
solution(S) :- solution_id(S).
valid(T, S) :- threat(T), solution(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THREATS:
        lines.append(asp.fact("threat_id", tid))
    for sid in SOLUTIONS:
        lines.append(asp.fact("solution_id", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space adventure story world: a threat metastasizes, "
                    "a cadet uses repetition and dialogue to save the crew.")
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--cadet-name")
    ap.add_argument("--captain-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.threat and args.solution:
        if args.threat not in THREATS or args.solution not in SOLUTIONS:
            raise StoryError("Invalid threat or solution specified.")

    combos = [c for c in valid_combos()
              if (args.threat is None or c[0] == args.threat)
              and (args.solution is None or c[1] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    threat_id, solution_id = rng.choice(sorted(combos))
    cadet_name = args.cadet_name or rng.choice(CADET_NAMES)
    captain_name = args.captain_name or rng.choice(CAPTAIN_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        threat=threat_id,
        solution=solution_id,
        cadet_name=cadet_name,
        captain_name=captain_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(THREATS[params.threat], SOLUTIONS[params.solution],
                 params.cadet_name, params.captain_name,
                 [params.trait, "observant"])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (threat, solution) combos:\n")
        for threat, solution in combos:
            print(f"  {threat:10} {solution:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.cadet_name}: {p.threat} threat ({p.solution} solution)"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
