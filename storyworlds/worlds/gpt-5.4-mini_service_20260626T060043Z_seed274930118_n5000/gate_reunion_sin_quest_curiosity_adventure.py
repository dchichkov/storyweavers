#!/usr/bin/env python3
"""
Storyworld: Gate Reunion Quest

A small adventure storyworld about a child whose curiosity leads to a quest
to open a gate and reach a reunion. A mistaken choice causes trouble, but the
story turns through honest repair and a joyful return.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

GATE_STRENGTH = 2.0
TRUST_THRESHOLD = 1.0
CURIOUS_THRESHOLD = 1.0
SINCERITY_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    name: str
    beyond_gate: bool = False
    can_host_quest: bool = True
    can_host_reunion: bool = True


@dataclass
class QuestDef:
    id: str
    goal: str
    action: str
    risk: str
    reward: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GateDef:
    id: str
    label: str
    blocks: set[str]
    opens_with: set[str]
    hint: str
    theme: str = "adventure"


@dataclass
class StoryParams:
    location: str
    quest: str
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    gate: str
    seed: Optional[int] = None


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.history: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _rule_gate_is_locked(world: World) -> list[str]:
    gate = world.get("gate")
    if gate.meter("open") >= GATE_STRENGTH:
        return []
    if ("gate_closed",) in world.fired:
        return []
    world.fired.add(("gate_closed",))
    return [f"The gate stayed shut, and its iron bars looked stubborn."]


def _rule_reunion_waits(world: World) -> list[str]:
    hero = world.get("hero")
    companion = world.get("companion")
    if hero.meter("beyond_gate") >= 1 and companion.meter("present") >= 1:
        return []
    if ("reunion_waits",) in world.fired:
        return []
    world.fired.add(("reunion_waits",))
    return [f"The reunion could not begin until someone found a way through the gate."]


def _rule_sin_hurts_trust(world: World) -> list[str]:
    hero = world.get("hero")
    companion = world.get("companion")
    if hero.meme("sin") < SINCERITY_THRESHOLD:
        return []
    if ("sin_hurts_trust",) in world.fired:
        return []
    world.fired.add(("sin_hurts_trust",))
    companion.memes["trust"] = max(0.0, companion.meme("trust") - 1.0)
    return [f"The dishonest choice made the waiting feel lonelier."]


def _rule_apology_rebuilds(world: World) -> list[str]:
    hero = world.get("hero")
    companion = world.get("companion")
    gate = world.get("gate")
    if hero.meme("sincere") < SINCERITY_THRESHOLD:
        return []
    if companion.meme("trust") >= TRUST_THRESHOLD and gate.meter("open") >= GATE_STRENGTH:
        return []
    if ("apology",) in world.fired:
        return []
    world.fired.add(("apology",))
    companion.memes["trust"] = companion.meme("trust") + 1.0
    gate.meters["open"] = gate.meter("open") + 1.0
    return [f"An honest apology loosened the latch a little."]


CAUSAL_RULES = [
    _rule_gate_is_locked,
    _rule_reunion_waits,
    _rule_sin_hurts_trust,
    _rule_apology_rebuilds,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_world(params: StoryParams) -> World:
    loc = LOCATIONS[params.location]
    world = World(loc)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        label=params.hero_name,
        type=params.hero_type,
        meters={"at_gate": 0.0, "beyond_gate": 0.0},
        memes={"curiosity": 1.0, "hope": 1.0, "sin": 0.0, "sincere": 0.0, "joy": 0.0},
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        label=params.companion_name,
        type=params.companion_type,
        meters={"present": 1.0},
        memes={"trust": 1.0, "joy": 0.5},
    ))
    gate = world.add(Entity(
        id="gate",
        kind="thing",
        label="the gate",
        type="gate",
        meters={"open": 0.0, "rust": 1.0},
        memes={"mystery": 1.0},
    ))

    quest = QUESTS[params.quest]
    gate_def = GATES[params.gate]
    world.facts.update(hero=hero, companion=companion, gate=gate, quest=quest, gate_def=gate_def, location=loc)

    world.say(f"{hero.label} loved {quest.keyword} and had a bright curiosity that never stayed still for long.")
    world.say(f"{companion.label} was waiting beyond {gate.label}, and {hero.label} wanted a reunion.")
    world.para()
    world.say(f"Near the path, {gate.label} stood at the edge of the adventure, blocking the way.")
    world.say(f"{gate_def.hint} That made the quest feel bigger than a simple walk.")

    hero.meters["at_gate"] = 1.0
    hero.memes["curiosity"] += 0.5
    propagate(world, narrate=True)

    world.para()
    world.say(f"{hero.label} chose to begin the quest by looking closely at the latch, the stones, and the old track marks.")
    hero.meters["looked"] = 1.0
    hero.memes["curiosity"] += 1.0

    # The mistake: a curious but wrong choice, the 'sin' in the seed sense.
    if params.quest == "key-quest":
        world.say(f"Wanting the answer too quickly, {hero.label} tried a sneaky trick instead of asking for help.")
        hero.memes["sin"] += 1.0
        hero.memes["sincere"] += 0.0
        companion.memes["trust"] = max(0.0, companion.meme("trust") - 0.5)
    elif params.quest == "map-quest":
        world.say(f"Curiosity tempted {hero.label} to hide the map for a moment, just to see what would happen.")
        hero.memes["sin"] += 1.0
        hero.memes["sincere"] += 0.0
        companion.memes["trust"] = max(0.0, companion.meme("trust") - 0.5)
    else:
        world.say(f"Curiosity led {hero.label} to tap the gate, but the gate would not answer.")

    propagate(world, narrate=True)

    world.para()
    if hero.meme("sin") >= SINCERITY_THRESHOLD:
        world.say(f"Then {hero.label} felt the wrongness of that choice and told the truth at once.")
        hero.memes["sincere"] += 1.0
        world.say(f"{hero.label} explained the mistake, shared the clue, and asked to try again the honest way.")
        companion.memes["trust"] += 1.0
    else:
        world.say(f"{hero.label} kept searching, patient and careful, until a better way appeared.")
        hero.memes["sincere"] += 1.0

    if gate_def.id in {"key", "bell"}:
        gate.meters["open"] += 1.0
    gate.meters["open"] += 1.0

    propagate(world, narrate=True)

    if gate.meter("open") >= GATE_STRENGTH:
        hero.meters["beyond_gate"] = 1.0
        companion.meters["present"] = 1.0
        hero.memes["joy"] += 1.0
        companion.memes["joy"] += 1.0
        world.say(f"The gate finally opened, and {hero.label} hurried through with a hopeful grin.")
        world.say(f"At last there was a reunion: {hero.label} and {companion.label} met again with laughter and relief.")
        world.say(f"The adventure ended with warm hugs on the other side of the gate.")
    else:
        world.say(f"The gate still held, but the honest quest had made the path clearer for tomorrow.")

    return world


def prize_was_clean(entity: Entity, prize: Entity) -> str:
    return f"{entity.label}'s {prize.label} stayed clean"


LOCATIONS = {
    "courtyard": Location(name="the courtyard"),
    "hill": Location(name="the hill"),
    "harbor": Location(name="the harbor"),
}

QUESTS = {
    "key-quest": QuestDef(
        id="key-quest",
        goal="find the key",
        action="look under the stones",
        risk="trusting the wrong shortcut",
        reward="the gate opens",
        keyword="Quest",
        tags={"quest", "curiosity"},
    ),
    "map-quest": QuestDef(
        id="map-quest",
        goal="follow the map",
        action="read the old marks",
        risk="hiding the map too long",
        reward="the reunion begins",
        keyword="Curiosity",
        tags={"quest", "curiosity"},
    ),
    "bell-quest": QuestDef(
        id="bell-quest",
        goal="ring the bell",
        action="listen for the echo",
        risk="calling without honesty",
        reward="the gatekeeper listens",
        keyword="Adventure",
        tags={"quest", "curiosity"},
    ),
}

GATES = {
    "rusted-gate": GateDef(
        id="rusted-gate",
        label="the rusted gate",
        blocks={"courtyard"},
        opens_with={"truth", "key"},
        hint="Its lock looked old, as if it had waited for a careful hand.",
    ),
    "hill-gate": GateDef(
        id="hill-gate",
        label="the hill gate",
        blocks={"hill"},
        opens_with={"truth", "map"},
        hint="The gate stood high in the wind, and it seemed to notice every secret.",
    ),
    "harbor-gate": GateDef(
        id="harbor-gate",
        label="the harbor gate",
        blocks={"harbor"},
        opens_with={"truth", "bell"},
        hint="Somewhere nearby, a bell promised that brave honesty would be heard.",
    ),
}

NAMES = ["Mina", "Toby", "Lina", "Owen", "Sara", "Nico", "Ari", "Ivy"]
KINDS = ["girl", "boy"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for loc in LOCATIONS:
        for q in QUESTS:
            for g in GATES:
                out.append((loc, q, g))
    return out


def explain_rejection() -> str:
    return "(No story: this combination cannot make a good gate-and-reunion adventure.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small adventure storyworld of gate, quest, curiosity, and reunion.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gate", choices=GATES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=KINDS)
    ap.add_argument("--companion-name")
    ap.add_argument("--companion-type", choices=KINDS)
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
    loc = args.location or rng.choice(list(LOCATIONS))
    quest = args.quest or rng.choice(list(QUESTS))
    gate = args.gate or rng.choice(list(GATES))
    hero_type = args.hero_type or rng.choice(KINDS)
    companion_type = args.companion_type or ("girl" if hero_type == "boy" else "boy")
    hero_name = args.hero_name or rng.choice(NAMES)
    companion_name = args.companion_name or rng.choice([n for n in NAMES if n != hero_name])
    if loc not in LOCATIONS or quest not in QUESTS or gate not in GATES:
        raise StoryError(explain_rejection())
    return StoryParams(
        location=loc,
        quest=quest,
        hero_name=hero_name,
        hero_type=hero_type,
        companion_name=companion_name,
        companion_type=companion_type,
        gate=gate,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    gate = f["gate_def"]
    return [
        f"Write a short adventure story about {hero.label}, {quest.keyword}, and a gate that must open for a reunion.",
        f"Tell a child-friendly tale where curiosity leads {hero.label} toward {gate.label} and the truth helps them through.",
        f"Create a gentle adventure with a quest, a mistake, and a reunion on the far side of a gate.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    companion: Entity = world.facts["companion"]
    quest: QuestDef = world.facts["quest"]
    gate: GateDef = world.facts["gate_def"]
    return [
        QAItem(
            question=f"Who wanted the reunion in the story?",
            answer=f"{hero.label} wanted the reunion and hoped to reach {companion.label} beyond {gate.label}.",
        ),
        QAItem(
            question=f"What did {hero.label}'s curiosity lead them to do?",
            answer=f"{hero.label} looked closely at the gate and began a quest to solve it the honest way.",
        ),
        QAItem(
            question=f"What was the risky mistake in the story?",
            answer=f"The risky mistake was a dishonest choice that slowed the reunion and hurt trust for a little while.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The gate opened, {hero.label} reached {companion.label}, and the story ended with a happy reunion.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a gate?", answer="A gate is a barrier that can open and close to let someone pass through."),
        QAItem(question="What is curiosity?", answer="Curiosity is the wish to learn, look closely, and ask questions."),
        QAItem(question="What is a quest?", answer="A quest is a journey or task done to reach a goal."),
        QAItem(question="What is reunion?", answer="A reunion is when people meet again after being apart."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"  history={len(world.history)} lines")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.

valid(L,Q,G) :- location(L), quest(Q), gate(G).

% A story is especially fitting if the gate can be opened by truth and the quest
% has room for curiosity and a reunion.
fitting(L,Q,G) :- valid(L,Q,G), location_tag(L, adventure),
                  quest_tag(Q, curiosity), gate_tag(G, reunion).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for loc in LOCATIONS:
        lines.append(asp.fact("location", loc))
        lines.append(asp.fact("location_tag", loc, "adventure"))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
        lines.append(asp.fact("quest_tag", q, "curiosity"))
    for g in GATES:
        lines.append(asp.fact("gate", g))
        lines.append(asp.fact("gate_tag", g, "reunion"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(location="courtyard", quest="key-quest", hero_name="Mina", hero_type="girl", companion_name="Toby", companion_type="boy", gate="rusted-gate"),
    StoryParams(location="hill", quest="map-quest", hero_name="Ari", hero_type="boy", companion_name="Ivy", companion_type="girl", gate="hill-gate"),
    StoryParams(location="harbor", quest="bell-quest", hero_name="Lina", hero_type="girl", companion_name="Nico", companion_type="boy", gate="harbor-gate"),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (location, quest, gate) combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(str(err))
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
            header = f"### {p.hero_name}: {p.quest} at {p.location} (gate: {p.gate})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
