#!/usr/bin/env python3
"""A fairy-tale zoo comedy about a ferry crash on a wobbly river.

Internal source tale:
In a bright little zoo, two children try to float a treat to a favorite animal
along a wobbly river on a toy ferry. The ferry makes a silly crash, and for one
moment the children are tempted to blame magic. Instead, they follow a
repeating physical clue, inspect the right part, fix the real fault with a zoo
keeper's help, and end the day with safe laughter beside the water.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


SOURCE_TALE = (
    "In a bright little zoo, two children send a special treat across a wobbly river "
    "on a toy ferry. The ferry crashes in a funny way, but the children stop guessing, "
    "follow a repeating clue, repair the real fault, and end with a safe happy launch."
)


@dataclass(frozen=True)
class Exhibit:
    key: str
    name: str
    opening: str
    animal_name: str
    animal_kind: str
    comic_detail: str
    treat: str
    ending_image: str
    sites: tuple[str, ...]


@dataclass(frozen=True)
class Fault:
    key: str
    place: str
    kind: str
    crash_text: str
    clue_text: str
    discovery: str
    mechanism: str
    repair_result: str


@dataclass(frozen=True)
class Fix:
    key: str
    solves: str
    tool: str
    action: str
    proof: str
    lesson: str


@dataclass(frozen=True)
class PairChoice:
    key: str
    first: str
    first_type: str
    second: str
    second_type: str


@dataclass(frozen=True)
class KeeperChoice:
    key: str
    name: str
    type: str
    role: str
    trait: str
    advice: str


@dataclass
class StoryParams:
    exhibit: str
    fault: str
    fix: str
    pair: str
    keeper: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: str | None = None


@dataclass
class ZooCrashWorld:
    params: StoryParams
    exhibit: Exhibit
    fault: Fault
    fix: Fix
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str | bool | int | float] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        if entity.role:
            self.entities[entity.role] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, event_id: str, text: str, actor: str, target: str | None = None) -> None:
        self.history.append(Event(event_id, text, actor, target))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(bits) for bits in self.paragraphs if bits)

    def trace(self) -> str:
        lines = ["TRACE"]
        for event in self.history:
            target = f" -> {event.target}" if event.target else ""
            lines.append(f"- {event.id}: {event.actor}{target}: {event.text}")
        lines.append("ENTITIES")
        seen: set[str] = set()
        for entity in self.entities.values():
            if entity.id in seen:
                continue
            seen.add(entity.id)
            lines.append(f"  {entity.id} | {entity.kind} | {entity.label}")
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            if meters:
                lines.append(f"    meters={meters}")
            if memes:
                lines.append(f"    memes={memes}")
        lines.append("FACTS")
        for key in sorted(self.facts):
            lines.append(f"  {key}={self.facts[key]}")
        return "\n".join(lines)


EXHIBITS: dict[str, Exhibit] = {
    "hippo_hollow": Exhibit(
        key="hippo_hollow",
        name="Hippo Hollow",
        opening="At Bellflower Zoo, a wobbly river looped through Hippo Hollow beneath bunting made of painted water lilies and gold stars.",
        animal_name="Duchess Bubbles",
        animal_kind="hippo",
        comic_detail="Duchess Bubbles tried to look grand at all times, yet every time a sweet bun appeared she snorted so hard that nearby reeds nodded yes.",
        treat="the honey bun crown",
        ending_image="Duchess Bubbles wore the honey bun crown like a queen, while the little ferry skimmed the dusk water and the lily lights trembled with laughter",
        sites=("axle", "guide_rail"),
    ),
    "penguin_promenade": Exhibit(
        key="penguin_promenade",
        name="Penguin Promenade",
        opening="At the silver gate of Bellflower Zoo, a wobbly river curved around Penguin Promenade where lantern shells chimed above the stepping stones.",
        animal_name="Lord Pebble",
        animal_kind="penguin",
        comic_detail="Lord Pebble marched with solemn dignity until food arrived, and then he flapped in such a hurry that he nearly applauded himself.",
        treat="the fish-pie ribbon",
        ending_image="Lord Pebble bowed over the bank, the fish-pie ribbon reached him without a splash, and even the lantern shells seemed to ring a happy tune",
        sites=("bell_line", "axle"),
    ),
    "lemur_lantern_walk": Exhibit(
        key="lemur_lantern_walk",
        name="Lemur Lantern Walk",
        opening="In the brightest corner of Bellflower Zoo, a wobbly river hurried past Lemur Lantern Walk where paper moons turned above a painted bend.",
        animal_name="Prince Skip",
        animal_kind="lemur",
        comic_detail="Prince Skip saluted every passing boat, although he almost always got so excited that he saluted with both hands and lost his balance on purpose.",
        treat="the mango tart moon",
        ending_image="Prince Skip hugged the mango tart moon on the mossy bank while the paper moons spun gently and the river forgot all about crashing",
        sites=("guide_rail", "bell_line"),
    ),
}


FAULTS: dict[str, Fault] = {
    "pebble_wedge": Fault(
        key="pebble_wedge",
        place="axle",
        kind="wedge",
        crash_text="The toy ferry paddled three brave splashes, gave a merry crash against a painted mushroom post, and flung its paper pennant straight onto a turtle statue's nose.",
        clue_text="Every restart ended with the same clicking hiccup at the axle, and the same silver pebble flashed between the wet spokes.",
        discovery="When the children crouched beside the paddle housing, they found a smooth river pebble wedged beside the axle tooth.",
        mechanism="That pebble jammed the axle on every turn, so the ferry lurched sideways instead of gliding along the middle of the stream.",
        repair_result="Once the pebble came free, the paddle turned round and even, and the ferry stopped butting its nose into posts.",
    ),
    "banana_slick": Fault(
        key="banana_slick",
        place="guide_rail",
        kind="slick",
        crash_text="At the crooked bend, the ferry slid with a cheerful crash into the lily barrel, and a yellow smear on the rail looked so much like a grin that both children blinked at it.",
        clue_text="At every launch, the same yellow gleam made the side runner skate away from the guide rail at the very same bend.",
        discovery="Pressed flat against the rail was a banana peel, shiny as butter and slippery enough to make the runner lose its hold.",
        mechanism="The slick peel made the runner slide off the guide rail, so the current pushed the ferry into the bend too fast.",
        repair_result="After the rail was scrubbed clean, the runner hugged the bend neatly and the ferry floated exactly where it was meant to go.",
    ),
    "sleepy_knot": Fault(
        key="sleepy_knot",
        place="bell_line",
        kind="slip",
        crash_text="The bell line flopped loose, the bow swung wide, and the ferry made a soft crash into the welcome sign so quickly that even the ducks forgot to quack.",
        clue_text="The same loop kept yawning open in the bell line whenever the current tugged, letting the bow wander before the turn.",
        discovery="Near the brass bell ring, the children found a knot rubbed smooth and half-open like a drowsy little mouth.",
        mechanism="Because that knot kept slipping, the guiding line never held the bow steady through the turn.",
        repair_result="With the knot snug again, the bell line stayed firm and the bow followed the curve like a duckling after its mother.",
    ),
}


FIXES: dict[str, Fix] = {
    "moon_spoon_wrench": Fix(
        key="moon_spoon_wrench",
        solves="wedge",
        tool="the moon-spoon wrench",
        action="{keeper} passed them {tool}. {first} steadied the ferry while {second} eased the spoon tip under the trapped pebble and coaxed it free with one patient twist.",
        proof="When they spun the paddle again, it answered with a smooth little whirr instead of a stubborn click.",
        lesson="They solved the trouble by removing the one hard thing that kept returning to the same tight place.",
    ),
    "mint_brush": Fix(
        key="mint_brush",
        solves="slick",
        tool="the mint-bristle scrub brush",
        action="{first} held the ferry close to the bank while {second} worked {tool} along the rail, and {keeper} poured a dipper of clean water until the silly yellow smear slid away.",
        proof="The side runner then gripped the rail so neatly that the ferry rounded the bend without even wobbling its grin.",
        lesson="They solved the trouble by cleaning the exact surface that had turned every launch slippery.",
    ),
    "double_loop_ring": Fix(
        key="double_loop_ring",
        solves="slip",
        tool="the striped double-loop ring",
        action="{keeper} showed them how to thread the bell line through {tool}. {second} pulled both ends even while {first} tied a bright double loop that sat tight against the bell ring.",
        proof="At the next tug, the loop held fast and the bow stayed pointed where the children had aimed it.",
        lesson="They solved the trouble by giving the loose line the exact kind of hold it had been missing.",
    ),
}


PAIRS: dict[str, PairChoice] = {
    "ada_finn": PairChoice("ada_finn", "Ada", "girl", "Finn", "boy"),
    "leila_milo": PairChoice("leila_milo", "Leila", "girl", "Milo", "boy"),
    "nina_ruz": PairChoice("nina_ruz", "Nina", "girl", "Ruz", "boy"),
    "suri_teo": PairChoice("suri_teo", "Suri", "girl", "Teo", "boy"),
}


KEEPERS: dict[str, KeeperChoice] = {
    "bea": KeeperChoice(
        key="bea",
        name="Keeper Bea",
        type="woman",
        role="lantern-barge keeper",
        trait="patient",
        advice='"A clue that comes back is trying to be helpful."',
    ),
    "hollis": KeeperChoice(
        key="hollis",
        name="Keeper Hollis",
        type="man",
        role="river-path keeper",
        trait="calm",
        advice='"If the funny part repeats, look where the wheel or rope repeats too."',
    ),
    "mei": KeeperChoice(
        key="mei",
        name="Keeper Mei",
        type="woman",
        role="treat-ferry keeper",
        trait="observant",
        advice='"Do not scold the whole river when one small part is asking for attention."',
    ),
}


PLACE_LABELS = {
    "axle": "the paddle axle under the ferry's side wheel",
    "guide_rail": "the painted guide rail at the bend",
    "bell_line": "the brass bell line at the bow",
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for exhibit_key, exhibit in sorted(EXHIBITS.items()):
        for fault_key, fault in sorted(FAULTS.items()):
            for fix_key, fix in sorted(FIXES.items()):
                if fault.place not in exhibit.sites:
                    continue
                if fix.solves != fault.kind:
                    continue
                combos.append((exhibit_key, fault_key, fix_key))
    return combos


def _unknown_reason(kind: str, value: str, options: Iterable[str]) -> str:
    opts = ", ".join(sorted(options))
    return f"No story: unknown {kind} {value!r}. Try one of: {opts}."


def explain_rejection(exhibit_key: str, fault_key: str, fix_key: str) -> str:
    if exhibit_key not in EXHIBITS:
        return _unknown_reason("exhibit", exhibit_key, EXHIBITS)
    if fault_key not in FAULTS:
        return _unknown_reason("fault", fault_key, FAULTS)
    if fix_key not in FIXES:
        return _unknown_reason("fix", fix_key, FIXES)
    exhibit = EXHIBITS[exhibit_key]
    fault = FAULTS[fault_key]
    fix = FIXES[fix_key]
    if fault.place not in exhibit.sites:
        sites = ", ".join(exhibit.sites)
        return (
            f"No story: {exhibit.name} does not support a {fault.place} failure. "
            f"That zoo ferry scene only uses these repair sites: {sites}."
        )
    if fix.solves != fault.kind:
        return (
            f"No story: fix {fix_key!r} solves {fix.solves}, but fault {fault_key!r} is a {fault.kind} problem. "
            "Use the tool that matches the physical trouble."
        )
    return "No story: invalid zoo ferry setup."


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.pair not in PAIRS:
        return False, _unknown_reason("pair", params.pair, PAIRS)
    if params.keeper not in KEEPERS:
        return False, _unknown_reason("keeper", params.keeper, KEEPERS)
    reason = explain_rejection(params.exhibit, params.fault, params.fix)
    if reason == "No story: invalid zoo ferry setup.":
        return True, ""
    return False, reason


def _pick_pair(seed: int) -> str:
    return random.Random(seed * 17 + 3).choice(sorted(PAIRS))


def _pick_keeper(seed: int) -> str:
    return random.Random(seed * 31 + 9).choice(sorted(KEEPERS))


def params_from_combo(combo: tuple[str, str, str], seed: int) -> StoryParams:
    return StoryParams(
        exhibit=combo[0],
        fault=combo[1],
        fix=combo[2],
        pair=_pick_pair(seed),
        keeper=_pick_keeper(seed),
        seed=seed,
    )


def matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = valid_combos()
    return [
        combo
        for combo in combos
        if (args.exhibit is None or combo[0] == args.exhibit)
        and (args.fault is None or combo[1] == args.fault)
        and (args.fix is None or combo[2] == args.fix)
    ]


def build_world(params: StoryParams) -> ZooCrashWorld:
    exhibit = EXHIBITS[params.exhibit]
    fault = FAULTS[params.fault]
    fix = FIXES[params.fix]
    pair = PAIRS[params.pair]
    keeper_choice = KEEPERS[params.keeper]

    world = ZooCrashWorld(params=params, exhibit=exhibit, fault=fault, fix=fix)

    first = world.add(Entity("first", "character", pair.first_type, pair.first, role="first", traits=["curious"]))
    second = world.add(Entity("second", "character", pair.second_type, pair.second, role="second", traits=["steady"]))
    keeper = world.add(
        Entity("keeper", "character", keeper_choice.type, keeper_choice.name, role="keeper", traits=[keeper_choice.trait])
    )
    duo = world.add(
        Entity(
            "duo",
            "group",
            "children",
            f"{pair.first} and {pair.second}",
            role="duo",
            traits=["playful", "careful"],
        )
    )
    animal = world.add(
        Entity(
            "animal",
            "animal",
            exhibit.animal_kind,
            exhibit.animal_name,
            role="animal",
            traits=["funny", "eager"],
        )
    )
    ferry = world.add(
        Entity(
            "ferry",
            "object",
            "toy_ferry",
            "the toy ferry",
            role="ferry",
            traits=["painted", "tiny"],
        )
    )
    river = world.add(
        Entity(
            "river",
            "place",
            "river",
            "the wobbly river",
            role="river",
            traits=["sparkling", "tricky"],
        )
    )
    site = world.add(
        Entity(
            fault.place,
            "mechanism",
            fault.place,
            PLACE_LABELS[fault.place],
            role="site",
            traits=["small", "important"],
        )
    )

    ferry.meters["straightness"] = 0.2
    ferry.meters["damage"] = 0.5
    river.meters["wobble"] = 1.0
    river.meters["flow"] = 1.0
    site.meters["blocked"] = 1.0
    duo.memes["wonder"] = 1.0
    duo.memes["worry"] = 0.2
    duo.memes["humor"] = 0.7
    duo.memes["resolve"] = 0.2
    animal.memes["trust"] = 0.8
    animal.memes["hunger"] = 1.0
    keeper.memes["patience"] = 1.0

    world.facts["source_tale"] = SOURCE_TALE
    world.facts["seed_words"] = "wobbly river, crash"
    world.facts["setting"] = "zoo"
    world.facts["site"] = fault.place
    world.facts["site_label"] = PLACE_LABELS[fault.place]
    world.facts["problem_kind"] = fault.kind
    world.facts["tool"] = fix.tool
    world.facts["keeper_role"] = keeper_choice.role
    world.facts["treat"] = exhibit.treat
    world.facts["solved"] = False
    world.facts["ending"] = "pending"
    return world


def build_false_guess(world: ZooCrashWorld) -> str:
    animal = world.get("animal").label
    place = world.fault.place
    if place == "axle":
        return (
            f"For one ridiculous breath, the children wondered whether {animal} had bowed so grandly that the whole river hopped sideways. "
            "Then the same click came back from the same place, which sounded much more like a clue than a curtsy."
        )
    if place == "guide_rail":
        return (
            "They nearly blamed a banana goblin for painting a joke onto the bend. "
            "Then the same yellow gleam returned at the same rail, and the joke turned into evidence."
        )
    return (
        "For a blink, they suspected the bell wanted to dance harder than the boat. "
        "Then the same loop yawned open again, and they knew something real was slipping."
    )


def tell(world: ZooCrashWorld) -> ZooCrashWorld:
    first = world.get("first")
    second = world.get("second")
    keeper = world.get("keeper")
    duo = world.get("duo")
    animal = world.get("animal")
    ferry = world.get("ferry")
    site = world.get("site")
    exhibit = world.exhibit
    fault = world.fault
    fix = world.fix
    keeper_role = str(world.facts["keeper_role"])
    site_label = str(world.facts["site_label"])

    world.record(
        "opening",
        f"{exhibit.opening} There lived {animal.label}, the most entertaining {animal.type} in that part of the zoo. {exhibit.comic_detail}",
        actor="narrator",
        target="river",
    )
    world.record(
        "goal",
        f"That morning, {first.label} and {second.label} tucked {exhibit.treat} into the toy ferry because they wanted to send it across the water to {animal.label} in the grandest fairy-tale style they could invent.",
        actor="duo",
        target="ferry",
    )
    world.para()

    world.record("crash", fault.crash_text, actor="ferry", target=fault.place)
    duo.memes["worry"] += 0.7
    duo.memes["wonder"] += 0.2
    animal.memes["trust"] -= 0.1
    world.record("false_guess", build_false_guess(world), actor="duo", target="river")
    world.record("clue", fault.clue_text, actor="duo", target=fault.place)
    world.record(
        "keeper_hint",
        f'{keeper.label}, the {keeper_role}, crouched by the bank and said, {KEEPERS[world.params.keeper].advice}',
        actor="keeper",
        target=fault.place,
    )
    world.para()

    world.record(
        "inspect",
        f"So {first.label} and {second.label} followed the repeating sign to {site_label} instead of scolding the whole ferry or the whole river.",
        actor="duo",
        target=fault.place,
    )
    world.record("discovery", fault.discovery, actor="duo", target=fault.place)
    world.record("diagnosis", fault.mechanism, actor="duo", target=fault.place)
    duo.memes["resolve"] += 0.9
    world.para()

    world.record(
        "solve",
        fix.action.format(first=first.label, second=second.label, keeper=keeper.label, tool=fix.tool),
        actor="duo",
        target=fault.place,
    )
    site.meters["blocked"] = 0.0
    ferry.meters["straightness"] = 1.0
    ferry.meters["damage"] = 0.0
    duo.memes["worry"] = 0.0
    duo.memes["humor"] += 0.3
    animal.memes["trust"] += 0.4
    world.record("proof", f"{fix.proof} {fault.repair_result}", actor="ferry", target="ferry")
    world.facts["solved"] = True
    world.para()

    world.record(
        "ending",
        f"When they launched the ferry again, it glided straight to {animal.label}. {animal.label} accepted {exhibit.treat} with such royal seriousness that {keeper.label} had to cover a laugh with one hand. By evening, {exhibit.ending_image}. {fix.lesson}",
        actor="duo",
        target="animal",
    )
    world.facts["ending"] = "happy"
    return world


def generation_prompts(world: ZooCrashWorld) -> list[str]:
    first = world.get("first").label
    second = world.get("second").label
    return [
        'Write a child-friendly fairy tale set in a zoo that includes the exact phrase "wobbly river."',
        f"Give {first} and {second} a funny ferry crash, but let them solve it by following a physical clue instead of using magic.",
        "End with a vivid happy image that proves the river ride is safe again.",
    ]


def fault_cause_answer(fault: Fault) -> str:
    mechanism = fault.mechanism.strip()
    lowered = mechanism.lower()
    if lowered.startswith("because "):
        return mechanism[8].upper() + mechanism[9:]
    return mechanism


def story_grounded_qa(world: ZooCrashWorld) -> list[QAItem]:
    first = world.get("first").label
    second = world.get("second").label
    keeper = world.get("keeper").label
    animal = world.get("animal").label
    exhibit = world.exhibit
    fault = world.fault
    fix = world.fix
    site_label = str(world.facts["site_label"])
    return [
        QAItem(
            "Why did the toy ferry crash?",
            f"The ferry crashed because {fault_cause_answer(fault)[0].lower() + fault_cause_answer(fault)[1:]} That pushed it off its path before {first} and {second} could deliver the treat to {animal}.",
        ),
        QAItem(
            "What clue showed the children where to look?",
            f"The clue was this: {fault.clue_text.lower()} Because the sign returned in the same place each time, the children knew they should inspect {site_label} instead of making wild guesses.",
        ),
        QAItem(
            "How did the children fix the problem?",
            f"They used {fix.tool} exactly where the clue pointed. {fix.proof} That showed the repair matched the real fault instead of hiding the trouble for one more launch.",
        ),
        QAItem(
            "What part did the zoo keeper play in the solution?",
            f"{keeper} helped by slowing the children down and teaching them to trust the repeating clue. The keeper also shared the right tool or method, but left the children to do the careful problem solving themselves.",
        ),
        QAItem(
            "Why is the story humorous as well as tense?",
            f"The crash is funny because the ferry bumps into something silly and leaves a playful image behind instead of causing real harm. The tension still matters because the children must stop laughing long enough to notice the pattern and solve the true problem.",
        ),
        QAItem(
            "How does the ending prove the story has a happy ending?",
            f"The ending proves it because {exhibit.ending_image}. That peaceful image only works after the ferry stops crashing and reaches {animal} the proper way.",
        ),
    ]


def world_knowledge_qa(world: ZooCrashWorld) -> list[QAItem]:
    return [
        QAItem(
            "Why must each fix match the kind of fault in this world?",
            "Every problem in this world is physical, such as a wedge, a slick surface, or a slipping line. A good ending feels earned only when the chosen fix matches the material trouble instead of pretending any cheerful action can repair everything.",
        ),
        QAItem(
            "Why is the repeating clue important in this zoo river world?",
            "The repeating clue keeps the story grounded in the simulated world instead of in random magic. It gives the children a testable sign, so the middle turn becomes observation and problem solving rather than lucky guessing.",
        ),
        QAItem(
            "Which object changes most clearly from the beginning to the end?",
            "The toy ferry changes most clearly. At first it crashes and wanders, but after the repair it travels straight, carries the treat safely, and becomes visible proof that the problem is over.",
        ),
        QAItem(
            "Why does the zoo setting matter in this story?",
            "The zoo setting matters because the goal is to deliver a treat to a specific animal in a public exhibit with keepers, rails, signs, and river paths sized for visitors. Those details shape both the comedy and the practical repair, so the setting is part of the causality rather than decoration.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = tell(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_grounded_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(E,F,X) :-
    exhibit(E),
    fault(F),
    fix(X),
    fault_place(F, P),
    exhibit_site(E, P),
    fault_kind(F, K),
    fix_solves(X, K).

ok :- chosen(E, F, X), valid(E, F, X).

#show valid/3.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    lines: list[str] = []
    for exhibit_key, exhibit in sorted(EXHIBITS.items()):
        lines.append(fact("exhibit", exhibit_key))
        for site in exhibit.sites:
            lines.append(fact("exhibit_site", exhibit_key, site))
    for fault_key, fault in sorted(FAULTS.items()):
        lines.append(fact("fault", fault_key))
        lines.append(fact("fault_place", fault_key, fault.place))
        lines.append(fact("fault_kind", fault_key, fault.kind))
    for fix_key, fix in sorted(FIXES.items()):
        lines.append(fact("fix", fix_key))
        lines.append(fact("fix_solves", fix_key, fix.solves))
    if params is not None:
        lines.append(fact("chosen", params.exhibit, params.fault, params.fix))
    return "\n".join(lines) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> list[tuple[str, str, str]]:
    from storyworlds.asp import atoms, one_model

    return sorted(atoms(one_model(asp_program()), "valid"))


def verify_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise AssertionError("sample world is missing")
    story_lower = sample.story.lower()
    for needle in ("wobbly river", "crash", "zoo"):
        if needle not in story_lower:
            raise AssertionError(f"story is missing {needle!r}")
    if sample.story.count("\n\n") < 3:
        raise AssertionError("story should have at least four paragraphs")
    if "{" in sample.story or "}" in sample.story:
        raise AssertionError("story leaked unresolved formatting")
    if "meters=" in sample.story or "memes=" in sample.story:
        raise AssertionError("story leaked debug language")
    if world.get("ferry").meters.get("straightness", 0) < 1.0:
        raise AssertionError("ferry never recovered a straight path")
    if world.get("ferry").meters.get("damage", 1.0) != 0.0:
        raise AssertionError("ferry still shows crash damage")
    if world.get("site").meters.get("blocked", 1.0) != 0.0:
        raise AssertionError("problem site stayed unresolved")
    if world.get("duo").memes.get("resolve", 0.0) < 1.0:
        raise AssertionError("children never reached a problem-solving turn")
    if world.get("duo").memes.get("worry", 1.0) != 0.0:
        raise AssertionError("worry never settled")
    if world.facts.get("ending") != "happy":
        raise AssertionError("story did not reach a happy ending")
    if world.facts.get("solved") is not True:
        raise AssertionError("world never recorded the repair as solved")
    event_ids = {event.id for event in world.history}
    for required in ("crash", "clue", "discovery", "solve", "ending"):
        if required not in event_ids:
            raise AssertionError(f"missing event {required!r}")
    if len(sample.prompts) != 3:
        raise AssertionError("expected exactly three prompts")
    if len(sample.story_qa) < 5 or len(sample.world_qa) < 3:
        raise AssertionError("QA sets are too thin")
    for item in list(sample.story_qa) + list(sample.world_qa):
        if len(item.answer.split()) < 12:
            raise AssertionError(f"answer is too short: {item.question}")


def asp_verify() -> int:
    py = sorted(valid_combos())
    lp = asp_valid_combos()
    if py != lp:
        only_py = sorted(set(py) - set(lp))
        only_lp = sorted(set(lp) - set(py))
        print("MISMATCH between Python and ASP gates:", file=sys.stderr)
        if only_py:
            print(f"  only in Python: {only_py}", file=sys.stderr)
        if only_lp:
            print(f"  only in ASP: {only_lp}", file=sys.stderr)
        return 1
    print(f"OK: ASP parity matches Python gate ({len(py)} valid zoo ferry setups).")
    for index, combo in enumerate(py):
        verify_sample(generate(params_from_combo(combo, 2000 + index)))
    print(f"OK: generated stories and QA passed for all {len(py)} valid combinations.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a fairy-tale zoo story about a wobbly river, a funny crash, and problem solving."
    )
    parser.add_argument("--exhibit", choices=sorted(EXHIBITS))
    parser.add_argument("--fault", choices=sorted(FAULTS))
    parser.add_argument("--fix", choices=sorted(FIXES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None, index: int = 0) -> StoryParams:
    seed = (args.seed if args.seed is not None else 1) + index
    combos = matching_combos(args)
    if not combos:
        exhibit = args.exhibit or next(iter(EXHIBITS))
        fault = args.fault or next(iter(FAULTS))
        fix = args.fix or next(iter(FIXES))
        raise StoryError(explain_rejection(exhibit, fault, fix))

    explicit = all(getattr(args, field) is not None for field in ("exhibit", "fault", "fix"))
    if explicit:
        params = params_from_combo((args.exhibit, args.fault, args.fix), seed)
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params

    chooser = rng or random.Random(seed)
    return params_from_combo(chooser.choice(combos), seed)


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        combos = matching_combos(args)
        if not combos:
            exhibit = args.exhibit or next(iter(EXHIBITS))
            fault = args.fault or next(iter(FAULTS))
            fix = args.fix or next(iter(FIXES))
            raise StoryError(explain_rejection(exhibit, fault, fix))
        return [generate(params_from_combo(combo, args.seed + index)) for index, combo in enumerate(combos)]

    samples: list[StorySample] = []
    for index in range(max(1, args.n)):
        seed = args.seed + index
        samples.append(generate(resolve_params(args, random.Random(seed), index)))
    return samples


def format_qa(sample: StorySample) -> str:
    lines = ["PROMPTS"]
    for prompt in sample.prompts:
        lines.append(f"- {prompt}")
    lines.append("")
    lines.append("STORY QA")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("WORLD KNOWLEDGE QA")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.show_asp:
        print(asp_program())
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid zoo ferry setups:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:18}" for part in combo))
        return 0

    try:
        samples = samples_from_args(args)
    except StoryError as exc:
        parser.error(str(exc))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for index, sample in enumerate(samples, 1):
        header = ""
        if len(samples) > 1:
            header = f"=== wobbly_river_crash_zoo_humor_happy_ending_2 #{index} seed={sample.params.seed} ==="
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
