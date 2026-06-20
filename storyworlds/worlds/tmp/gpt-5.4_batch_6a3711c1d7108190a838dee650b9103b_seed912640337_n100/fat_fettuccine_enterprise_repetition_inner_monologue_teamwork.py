#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fat_fettuccine_enterprise_repetition_inner_monologue_teamwork.py
=============================================================================================

A small nursery-rhyme-style story world about a tiny noodle venture: a childlike
animal crew cooks fettuccine, one proud cook tries to move a heavy pot alone,
the pot wobbles, and teamwork carries the supper safely to the table.

Seed requirements reflected directly in the world:
- words: fat, fettuccine, enterprise
- features: Repetition, Inner Monologue, Teamwork
- style: Nursery Rhyme

The story engine models a few physical meters (heat, weight, wobble, distance,
spill) and emotional memes (pride, worry, relief, togetherness). The prose is
driven from those states: the pot becomes too heavy for one small cook, a wobble
appears, friends join, and the ending image proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/fat_fettuccine_enterprise_repetition_inner_monologue_teamwork.py
    python storyworlds/worlds/gpt-5.4/fat_fettuccine_enterprise_repetition_inner_monologue_teamwork.py --sauce cream --vessel brass_pot --tool tray --crew trio
    python storyworlds/worlds/gpt-5.4/fat_fettuccine_enterprise_repetition_inner_monologue_teamwork.py --crew duo --tool towel_handles --vessel brass_pot
    python storyworlds/worlds/gpt-5.4/fat_fettuccine_enterprise_repetition_inner_monologue_teamwork.py --all
    python storyworlds/worlds/gpt-5.4/fat_fettuccine_enterprise_repetition_inner_monologue_teamwork.py --qa --json
    python storyworlds/worlds/gpt-5.4/fat_fettuccine_enterprise_repetition_inner_monologue_teamwork.py --verify
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
SOLO_STRENGTH = 1
MIN_CREW = 2


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
        female = {"girl", "hen", "duck", "goose"}
        male = {"boy", "mouse", "mole", "bear", "frog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Sauce:
    id: str
    label: str
    heft: int
    color: str
    richness: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Vessel:
    id: str
    label: str
    weight: int
    shine: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    bonus: int
    method: str
    chant: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Crew:
    id: str
    total: int
    phrase: str


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        out = World()
        out.entities = copy.deepcopy(self.entities)
        out.fired = set(self.fired)
        out.paragraphs = [[]]
        out.facts = copy.deepcopy(self.facts)
        return out

    def crew_members(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character" and e.role in {"leader", "helper"}]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wobble_from_strain(world: World) -> list[str]:
    out: list[str] = []
    pot = world.get("pot")
    if pot.meters["lifted_by_one"] < THRESHOLD:
        return out
    load = int(world.facts["load"])
    if load <= SOLO_STRENGTH:
        return out
    sig = ("wobble", load)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pot.meters["wobble"] += 1
    pot.meters["spill_risk"] += 1
    for kid in world.crew_members():
        kid.memes["worry"] += 1
    out.append("__wobble__")
    return out


def _r_team_steadies(world: World) -> list[str]:
    out: list[str] = []
    pot = world.get("pot")
    if pot.meters["team_hands"] < THRESHOLD:
        return out
    sig = ("steady", int(pot.meters["team_hands"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    capacity = int(world.facts["capacity"])
    load = int(world.facts["load"])
    if capacity >= load:
        if capacity == load:
            pot.meters["spill"] += 1
        pot.meters["wobble"] = 0.0
        pot.meters["distance"] = 0.0
        for kid in world.crew_members():
            kid.memes["together"] += 1
            kid.memes["relief"] += 1
        out.append("__steady__")
    return out


CAUSAL_RULES = [
    Rule("wobble_from_strain", "physical", _r_wobble_from_strain),
    Rule("team_steadies", "social", _r_team_steadies),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SAUCES = {
    "cream": Sauce("cream", "cream sauce", 2, "pale gold", "fat and silky", tags={"cream", "fat"}),
    "tomato": Sauce("tomato", "tomato sauce", 1, "red", "bright and tangy", tags={"tomato"}),
    "pea": Sauce("pea", "pea sauce", 1, "green", "sweet and buttery", tags={"peas"}),
    "pumpkin": Sauce("pumpkin", "pumpkin sauce", 2, "sunny orange", "thick and velvety", tags={"pumpkin"}),
}

VESSELS = {
    "blue_pot": Vessel("blue_pot", "blue pot", 1, "blue as rain", tags={"pot"}),
    "brass_pot": Vessel("brass_pot", "brass pot", 2, "brassy as a bell", tags={"pot"}),
    "wide_pan": Vessel("wide_pan", "wide pan", 1, "wide and warm", tags={"pan"}),
}

TOOLS = {
    "tray": Tool("tray", "wooden tray", 2, "slid the pot onto a wooden tray", "Lift and step, lift and step!", tags={"tray", "teamwork"}),
    "towel_handles": Tool("towel_handles", "towel handles", 1, "looped two towels under the handles", "Grip and guide, grip and guide!", tags={"towels", "teamwork"}),
    "cart": Tool("cart", "rolling cart", 3, "set the pot on a little rolling cart", "Roll and sing, roll and sing!", tags={"cart", "teamwork"}),
}

CREWS = {
    "duo": Crew("duo", 2, "two small cooks"),
    "trio": Crew("trio", 3, "three small cooks"),
}

NAMES = [
    ("Pip", "mouse"),
    ("Dot", "duck"),
    ("Moss", "mole"),
    ("Hattie", "hen"),
    ("Bram", "bear"),
    ("Puddle", "frog"),
]


def load_of(sauce: Sauce, vessel: Vessel) -> int:
    return sauce.heft + vessel.weight


def capacity_of(tool: Tool, crew: Crew) -> int:
    return tool.bonus + crew.total


def valid_combo(sauce: Sauce, vessel: Vessel, tool: Tool, crew: Crew) -> bool:
    return crew.total >= MIN_CREW and capacity_of(tool, crew) >= load_of(sauce, vessel)


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for sid, sauce in SAUCES.items():
        for vid, vessel in VESSELS.items():
            for tid, tool in TOOLS.items():
                for cid, crew in CREWS.items():
                    if valid_combo(sauce, vessel, tool, crew):
                        out.append((sid, vid, tid, cid))
    return out


@dataclass
class StoryParams:
    sauce: str
    vessel: str
    tool: str
    crew: str
    leader_name: str
    leader_type: str
    helper1_name: str
    helper1_type: str
    helper2_name: str
    helper2_type: str
    seed: Optional[int] = None


def choose_cast(rng: random.Random, crew: Crew) -> tuple[tuple[str, str], tuple[str, str], tuple[str, str]]:
    picks = rng.sample(NAMES, 3)
    if crew.total == 2:
        return picks[0], picks[1], ("", "thing")
    return picks[0], picks[1], picks[2]


def explain_rejection(sauce: Sauce, vessel: Vessel, tool: Tool, crew: Crew) -> str:
    if crew.total < MIN_CREW:
        return "(No story: this little noodle world needs teamwork, so at least two cooks must carry the supper.)"
    load = load_of(sauce, vessel)
    cap = capacity_of(tool, crew)
    return (
        f"(No story: a {vessel.label} of fettuccine with {sauce.label} is too heavy for "
        f"{crew.phrase} using {tool.label} (capacity {cap} < load {load}). Pick more helpers or a stronger carrying tool.)"
    )


def predict_solo(world: World) -> dict:
    sim = world.copy()
    pot = sim.get("pot")
    pot.meters["lifted_by_one"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": pot.meters["wobble"] >= THRESHOLD,
        "spill_risk": pot.meters["spill_risk"] >= THRESHOLD,
    }


def introduce(world: World, leader: Entity, helpers: list[Entity], sauce: Sauce, vessel: Vessel) -> None:
    names = [leader.id] + [h.id for h in helpers]
    pair = ", ".join(names[:-1]) + f", and {names[-1]}" if len(names) > 2 else f"{names[0]} and {names[1]}"
    world.say(
        f"In a snug little kitchen, {pair} began a supper enterprise. "
        f"They twirled long fettuccine ribbons in a {vessel.label} that shone {vessel.shine}."
    )
    world.say(
        f'"Stir it and sing it, stir it and sing it," they chanted. '
        f'The {sauce.label} turned {sauce.color}, {sauce.richness}, and the pot looked fat with dinner.'
    )


def proud_thought(world: World, leader: Entity, sauce: Sauce) -> None:
    leader.memes["pride"] += 1
    world.say(
        f"When the noodles were ready, {leader.id} peeped at the table and thought, "
        f'"I can take this all alone. I can, I can."'
    )
    if sauce.heft >= 2:
        world.say(
            f'But inside {leader.pronoun("possessive")} head another little thought replied, '
            f'"Oh dear, what a hot, fat pot."'
        )


def warn(world: World, leader: Entity, helpers: list[Entity], tool: Tool) -> None:
    pred = predict_solo(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    if not pred["wobble"]:
        return
    helper = helpers[0]
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} saw the steam curl up and said, "Not alone, not alone. '
        f'Let us use the {tool.label} and carry it home."'
    )


def solo_lift(world: World, leader: Entity) -> None:
    pot = world.get("pot")
    pot.meters["lifted_by_one"] += 1
    pot.meters["distance"] = 1
    propagate(world, narrate=False)
    if pot.meters["wobble"] >= THRESHOLD:
        world.say(
            f"{leader.id} tugged the handles. Up came the pot, and wobble went bobble. "
            f"A ribbon of fettuccine slithered to the rim."
        )
    else:
        world.say(f"{leader.id} lifted the pot without a shake.")


def join_hands(world: World, helpers: list[Entity], tool: Tool, crew: Crew) -> None:
    pot = world.get("pot")
    pot.meters["team_hands"] = crew.total
    world.say(
        f"Quick came the helpers. They {tool.method}, and together they sang, "
        f'"{tool.chant}"'
    )
    propagate(world, narrate=False)


def resolve(world: World, leader: Entity, helpers: list[Entity], sauce: Sauce) -> None:
    pot = world.get("pot")
    if pot.meters["spill"] >= THRESHOLD:
        world.say(
            "One fat drop of sauce plopped on the cloth, but no one cried. "
            "The little crew steadied the supper and kept on going."
        )
        world.facts["outcome"] = "splashed"
    else:
        world.say(
            "The pot grew steady as a moon on rails. No noodles escaped, and the steam only hummed."
        )
        world.facts["outcome"] = "smooth"
    for kid in [leader] + helpers:
        kid.memes["joy"] += 1
    names = [leader.id] + [h.id for h in helpers]
    final_names = ", ".join(names[:-1]) + f", and {names[-1]}" if len(names) > 2 else f"{names[0]} and {names[1]}"
    world.say(
        f"Soon {final_names} set the fettuccine on the table, bowed to their brave enterprise, "
        f"and shared the shining noodles strand by strand."
    )
    world.say(
        '"Share it and cheer it, share it and cheer it," they sang, '
        f"and the once-wobbly supper ended warm and safe."
    )


def tell(params: StoryParams) -> World:
    sauce = SAUCES[params.sauce]
    vessel = VESSELS[params.vessel]
    tool = TOOLS[params.tool]
    crew = CREWS[params.crew]

    if not valid_combo(sauce, vessel, tool, crew):
        raise StoryError(explain_rejection(sauce, vessel, tool, crew))

    world = World()
    leader = world.add(Entity(id=params.leader_name, kind="character", type=params.leader_type, role="leader"))
    helper1 = world.add(Entity(id=params.helper1_name, kind="character", type=params.helper1_type, role="helper"))
    helpers = [helper1]
    if crew.total == 3:
        helper2 = world.add(Entity(id=params.helper2_name, kind="character", type=params.helper2_type, role="helper"))
        helpers.append(helper2)

    pot = world.add(Entity(id="pot", type="pot", label=vessel.label))
    pot.meters["heat"] = 1
    pot.meters["weight"] = load_of(sauce, vessel)

    world.facts.update(
        sauce=sauce,
        vessel=vessel,
        tool=tool,
        crew=crew,
        load=load_of(sauce, vessel),
        capacity=capacity_of(tool, crew),
        leader=leader,
        helpers=helpers,
        repeated_line=tool.chant,
    )

    introduce(world, leader, helpers, sauce, vessel)
    world.para()
    proud_thought(world, leader, sauce)
    warn(world, leader, helpers, tool)
    solo_lift(world, leader)
    world.para()
    join_hands(world, helpers, tool, crew)
    resolve(world, leader, helpers, sauce)
    return world


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


KNOWLEDGE = {
    "fettuccine": [
        ("What is fettuccine?",
         "Fettuccine is a kind of pasta made in long, flat ribbons. The ribbons are soft when cooked and easy to twirl.")
    ],
    "teamwork": [
        ("What is teamwork?",
         "Teamwork means people help one another do a job together. A hard job can become easier and safer when many hands share it.")
    ],
    "tray": [
        ("Why can a tray help carry something heavy?",
         "A tray gives a flat, steady place to hold a heavy thing. That makes it easier for several helpers to move it together.")
    ],
    "towels": [
        ("Why would towels help with a hot pot?",
         "Towels can protect hands from heat and help someone grip slippery handles. They make hot carrying safer.")
    ],
    "cart": [
        ("Why is a rolling cart useful?",
         "A rolling cart lets wheels do part of the work. Heavy things can move more smoothly when they roll instead of being lifted high.")
    ],
    "cream": [
        ("Why might cream sauce seem rich and thick?",
         "Cream sauce is made from rich dairy, so it can look thick and silky. That is why it can make a pot feel heavier.")
    ],
    "pot": [
        ("Why does a full pot feel heavy?",
         "A full pot holds both the pot itself and all the food inside it. More food means more weight to lift.")
    ],
}
KNOWLEDGE_ORDER = ["fettuccine", "teamwork", "tray", "towels", "cart", "cream", "pot"]


def generation_prompts(world: World) -> list[str]:
    sauce = world.facts["sauce"]
    tool = world.facts["tool"]
    crew = world.facts["crew"]
    leader = world.facts["leader"]
    return [
        'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "fat", "fettuccine", and "enterprise".',
        f"Tell a rhythmic story where {leader.id} starts a noodle enterprise, thinks about carrying supper alone, and then learns to use teamwork.",
        f"Write a playful kitchen story with repetition, a small inner monologue, and {crew.phrase} using {tool.label} to move a pot of fettuccine with {sauce.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    leader = world.facts["leader"]
    helpers = world.facts["helpers"]
    sauce = world.facts["sauce"]
    vessel = world.facts["vessel"]
    tool = world.facts["tool"]
    crew = world.facts["crew"]
    load = world.facts["load"]
    capacity = world.facts["capacity"]
    outcome = world.facts["outcome"]
    helper_names = " and ".join(h.id for h in helpers) if len(helpers) == 2 else helpers[0].id

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.id} and the other little cooks in a supper enterprise. "
            f"They are making fettuccine together in a snug kitchen."
        ),
        (
            "What made the pot hard to carry?",
            f"The {vessel.label} was full of fettuccine and {sauce.label}, so the supper load was heavy. "
            f"That is why the pot looked fat with dinner and was too much for one small cook."
        ),
        (
            f"What did {leader.id} think to {leader.pronoun('object')}self?",
            f'{leader.id} thought, "I can take this all alone. I can, I can." '
            f"That inner thought shows {leader.pronoun('possessive')} pride before the wobble began."
        ),
    ]
    if world.facts.get("predicted_wobble"):
        qa.append(
            (
                f"Why did {helper_names} tell {leader.id} not to carry the pot alone?",
                f"They could see the hot, heavy pot was likely to wobble if only one cook lifted it. "
                f"Using the {tool.label} and many hands was safer because the crew's carrying strength was {capacity} for a load of {load}."
            )
        )
    if outcome == "smooth":
        qa.append(
            (
                "How did the problem get solved?",
                f"The helpers joined {leader.id}, they {tool.method}, and they moved the pot together. "
                "Once the job was shared, the wobble stopped and the fettuccine reached the table safely."
            )
        )
    else:
        qa.append(
            (
                "Did anything spill, and what happened after that?",
                "Yes, one fat drop of sauce splashed out when the pot had been wobbling. "
                "But the crew steadied the supper together and still brought the fettuccine safely to the table."
            )
        )
    qa.append(
        (
            "How did the story end?",
            "It ended with the little cooks sharing the noodles and singing together. "
            "The ending image shows that teamwork turned a shaky problem into a warm meal."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"fettuccine", "teamwork", "pot"}
    tool = world.facts["tool"]
    tags |= set(tool.tags)
    if world.facts["sauce"].id == "cream":
        tags.add("cream")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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


ASP_RULES = r"""
load(S,V,L) :- sauce(S), sauce_heft(S,H), vessel(V), vessel_weight(V,W), L = H + W.
capacity(T,C,Cap) :- tool(T), tool_bonus(T,B), crew(C), crew_total(C,N), Cap = B + N.
valid(S,V,T,C) :- sauce(S), vessel(V), tool(T), crew(C), crew_total(C,N), min_crew(M), N >= M,
                  load(S,V,L), capacity(T,C,Cap), Cap >= L.

predicted_wobble(S,V) :- load(S,V,L), solo_strength(SS), L > SS.
exact_fit(S,V,T,C) :- valid(S,V,T,C), load(S,V,L), capacity(T,C,Cap), Cap = L.
outcome(S,V,T,C,smooth) :- valid(S,V,T,C), not exact_fit(S,V,T,C).
outcome(S,V,T,C,splashed) :- exact_fit(S,V,T,C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, sauce in SAUCES.items():
        lines.append(asp.fact("sauce", sid))
        lines.append(asp.fact("sauce_heft", sid, sauce.heft))
    for vid, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        lines.append(asp.fact("vessel_weight", vid, vessel.weight))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_bonus", tid, tool.bonus))
    for cid, crew in CREWS.items():
        lines.append(asp.fact("crew", cid))
        lines.append(asp.fact("crew_total", cid, crew.total))
    lines.append(asp.fact("solo_strength", SOLO_STRENGTH))
    lines.append(asp.fact("min_crew", MIN_CREW))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_sauce", params.sauce),
        asp.fact("chosen_vessel", params.vessel),
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_crew", params.crew),
        "chosen_outcome(O) :- chosen_sauce(S), chosen_vessel(V), chosen_tool(T), chosen_crew(C), outcome(S,V,T,C,O).",
    ])
    model = asp.one_model(asp_program(extra, "#show chosen_outcome/1."))
    atoms = asp.atoms(model, "chosen_outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    sauce = SAUCES[params.sauce]
    vessel = VESSELS[params.vessel]
    tool = TOOLS[params.tool]
    crew = CREWS[params.crew]
    if not valid_combo(sauce, vessel, tool, crew):
        raise StoryError(explain_rejection(sauce, vessel, tool, crew))
    return "splashed" if capacity_of(tool, crew) == load_of(sauce, vessel) else "smooth"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for i in range(40):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(i))
        except StoryError:
            continue
        cases.append(p)
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        emit(sample, trace=False, qa=False)
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


CURATED = [
    StoryParams("cream", "brass_pot", "tray", "trio", "Pip", "mouse", "Dot", "duck", "Moss", "mole"),
    StoryParams("tomato", "blue_pot", "towel_handles", "duo", "Hattie", "hen", "Puddle", "frog", "", "thing"),
    StoryParams("pumpkin", "wide_pan", "cart", "duo", "Bram", "bear", "Dot", "duck", "", "thing"),
    StoryParams("pea", "brass_pot", "tray", "duo", "Moss", "mole", "Hattie", "hen", "", "thing"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: a fettuccine enterprise learns teamwork."
    )
    ap.add_argument("--sauce", choices=SAUCES)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--crew", choices=CREWS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sauce and args.vessel and args.tool and args.crew:
        if not valid_combo(SAUCES[args.sauce], VESSELS[args.vessel], TOOLS[args.tool], CREWS[args.crew]):
            raise StoryError(explain_rejection(SAUCES[args.sauce], VESSELS[args.vessel], TOOLS[args.tool], CREWS[args.crew]))

    combos = [
        combo for combo in valid_combos()
        if (args.sauce is None or combo[0] == args.sauce)
        and (args.vessel is None or combo[1] == args.vessel)
        and (args.tool is None or combo[2] == args.tool)
        and (args.crew is None or combo[3] == args.crew)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    sauce, vessel, tool, crew_id = rng.choice(sorted(combos))
    crew = CREWS[crew_id]
    leader, helper1, helper2 = choose_cast(rng, crew)
    return StoryParams(
        sauce=sauce,
        vessel=vessel,
        tool=tool,
        crew=crew_id,
        leader_name=leader[0],
        leader_type=leader[1],
        helper1_name=helper1[0],
        helper1_type=helper1[1],
        helper2_name=helper2[0],
        helper2_type=helper2[1],
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/4.\n#show outcome/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (sauce, vessel, tool, crew) combos:\n")
        for sauce, vessel, tool, crew in combos:
            print(f"  {sauce:8} {vessel:10} {tool:14} {crew}")
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
            header = f"### {p.leader_name}: {p.sauce} in {p.vessel} with {p.tool} ({p.crew}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
