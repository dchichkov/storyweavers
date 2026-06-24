#!/usr/bin/env python3
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    located_at: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Terminal:
    id: str
    label: str
    phrase: str
    checkpoints: list[str]


@dataclass
class Gate:
    id: str
    terminal: str
    color: str
    number: int
    sign: str
    rhyme: str
    rhyme_word: str
    destination: str
    path: list[str]


@dataclass
class Helper:
    id: str
    type: str
    label: str
    stationed_at: str
    suggest_verb: str
    detail: str


@dataclass
class TravelItem:
    id: str
    label: str
    phrase: str
    hold: str
    dream: str


@dataclass
class StoryParams:
    terminal: str
    gate: str
    helper: str
    item: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, terminal: Terminal) -> None:
        self.terminal = terminal
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.path_index = 0

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
        clone = World(self.terminal)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.path_index = self.path_index
        return clone


TERMINALS = {
    "sun": Terminal(
        id="sun",
        label="Sun Terminal",
        phrase="a bright terminal with glass walls and rolling suitcases",
        checkpoints=["the moon mural", "the snack kiosk", "the moving walkway"],
    ),
    "cloud": Terminal(
        id="cloud",
        label="Cloud Terminal",
        phrase="a high terminal where speakers chimed over neat rows of seats",
        checkpoints=["the tall window", "the book shop", "the silver escalator"],
    ),
    "star": Terminal(
        id="star",
        label="Star Terminal",
        phrase="a busy terminal with shining signs and little toy planes",
        checkpoints=["the fountain globe", "the ticket desk", "the long carpet with stars"],
    ),
}

GATES = {
    "blue2": Gate(
        id="blue2",
        terminal="sun",
        color="blue",
        number=2,
        sign="Blue Gate Two",
        rhyme="Blue Gate Two, the sky door for you.",
        rhyme_word="you",
        destination="the seaside city",
        path=["the moon mural", "the snack kiosk", "the moving walkway"],
    ),
    "green3": Gate(
        id="green3",
        terminal="star",
        color="green",
        number=3,
        sign="Green Gate Three, the right stop for me.",
        rhyme="Green Gate Three, the right stop for me.",
        rhyme_word="me",
        destination="the hill town",
        path=["the fountain globe", "the ticket desk", "the long carpet with stars"],
    ),
    "red4": Gate(
        id="red4",
        terminal="cloud",
        color="red",
        number=4,
        sign="Red Gate Four, past one more door.",
        rhyme="Red Gate Four, past one more door.",
        rhyme_word="door",
        destination="the lake town",
        path=["the tall window", "the book shop", "the silver escalator"],
    ),
    "gold8": Gate(
        id="gold8",
        terminal="sun",
        color="gold",
        number=8,
        sign="Gold Gate Eight, we are not late.",
        rhyme="Gold Gate Eight, we are not late.",
        rhyme_word="late",
        destination="the island city",
        path=["the moon mural", "the snack kiosk", "the moving walkway"],
    ),
}

HELPERS = {
    "agent_sia": Helper(
        id="agent_sia",
        type="agent",
        label="a kind gate agent",
        stationed_at="sun",
        suggest_verb="suggested",
        detail="She wore a scarf the color of a sunrise screen.",
    ),
    "pilot_omar": Helper(
        id="pilot_omar",
        type="pilot",
        label="a smiling pilot",
        stationed_at="cloud",
        suggest_verb="suggested",
        detail="His cap looked neat and his shoes clicked softly.",
    ),
    "cleaner_jo": Helper(
        id="cleaner_jo",
        type="cleaner",
        label="a cheerful cleaner",
        stationed_at="star",
        suggest_verb="suggested",
        detail="Her little cart hummed beside a row of seats.",
    ),
    "mechanic_rae": Helper(
        id="mechanic_rae",
        type="mechanic",
        label="an airport mechanic",
        stationed_at="sun",
        suggest_verb="suggested",
        detail="A silver wrench peeked from a deep pocket.",
    ),
}

ITEMS = {
    "backpack": TravelItem(
        id="backpack",
        label="backpack",
        phrase="a small backpack with a rocket patch",
        hold="held the strap of the backpack",
        dream="It made the trip feel like the start of a mission.",
    ),
    "notebook": TravelItem(
        id="notebook",
        label="notebook",
        phrase="a star notebook tucked under one arm",
        hold="held the notebook close",
        dream="The shiny stars on the cover looked like tiny maps.",
    ),
    "robot": TravelItem(
        id="robot",
        label="toy robot",
        phrase="a toy robot with bright button eyes",
        hold="held the toy robot against the chest",
        dream="The robot looked ready to beep its way onto a brave adventure.",
    ),
    "pillow": TravelItem(
        id="pillow",
        label="travel pillow",
        phrase="a moon-shaped travel pillow",
        hold="hugged the travel pillow",
        dream="Its curved shape felt like a soft moon for the trip.",
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Zoe", "Ivy", "Ella", "Ruby", "Cora"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Theo", "Jude", "Nico", "Leo", "Eli"]
TRAITS = ["curious", "brave", "bright-eyed", "eager", "gentle", "lively"]

CURATED = [
    StoryParams(
        terminal="sun",
        gate="blue2",
        helper="agent_sia",
        item="backpack",
        name="Lina",
        gender="girl",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        terminal="cloud",
        gate="red4",
        helper="pilot_omar",
        item="robot",
        name="Milo",
        gender="boy",
        parent="father",
        trait="brave",
    ),
    StoryParams(
        terminal="star",
        gate="green3",
        helper="cleaner_jo",
        item="notebook",
        name="Nora",
        gender="girl",
        parent="mother",
        trait="eager",
    ),
    StoryParams(
        terminal="sun",
        gate="gold8",
        helper="mechanic_rae",
        item="pillow",
        name="Theo",
        gender="boy",
        parent="father",
        trait="bright-eyed",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for gate_id, gate in GATES.items():
        for helper_id, helper in HELPERS.items():
            if helper.stationed_at == gate.terminal and gate.rhyme:
                for item_id in ITEMS:
                    out.append((gate.terminal, gate_id, helper_id, item_id))
    return out


def explain_terminal_gate(terminal: str, gate: str) -> str:
    g = GATES[gate]
    return (
        f"(No story: {g.sign} is in {TERMINALS[g.terminal].label}, not in "
        f"{TERMINALS[terminal].label}. The airport quest needs the child, the helper, "
        f"and the gate to live in the same terminal.)"
    )


def explain_helper(helper: str, terminal: str) -> str:
    h = HELPERS[helper]
    return (
        f"(No story: {h.label} works in {TERMINALS[h.stationed_at].label}, not in "
        f"{TERMINALS[terminal].label}. The helper has to be nearby to suggest the rhyme.)"
    )


def introduce(world: World, hero: Entity, parent: Entity, item: TravelItem) -> None:
    trait = hero.traits[0] if hero.traits else "small"
    world.say(
        f"{hero.id} was a little {trait} {hero.type} at the airport with {hero.pronoun('possessive')} "
        f"{parent.type}. {hero.pronoun().capitalize()} carried {item.phrase}. {item.dream}"
    )


def airport_scene(world: World, hero: Entity) -> None:
    world.say(
        f"They entered {world.terminal.label}, {world.terminal.phrase}. "
        f"The airport clamor rolled around them with wheels, voices, and dinging screens."
    )
    hero.meters["noise"] += 1
    hero.memes["wonder"] += 1


def hear_clamor(world: World, hero: Entity, gate: Gate) -> None:
    if hero.meters["noise"] >= THRESHOLD:
        hero.memes["worry"] += 1
        hero.memes["confusion"] += 1
        world.say(
            f"{hero.id} tried to remember {gate.sign}, but the clamor made the number feel slippery. "
            f"For one tight moment, the gate name floated away like a tiny ship in fog."
        )


def parent_notices(world: World, hero: Entity, parent: Entity, item: TravelItem) -> None:
    world.say(
        f"{parent.type.capitalize()} saw {hero.pronoun('object')} {item.hold} and slow down. "
        f'"It is all right," {parent.pronoun()} said. "We can find the right gate together."'
    )


def helper_arrives(world: World, helper_ent: Entity, helper: Helper) -> None:
    world.say(f"Nearby stood {helper.label}. {helper.detail}")


def suggest_rhyme(world: World, hero: Entity, helper_ent: Entity, helper: Helper, gate: Gate) -> None:
    hero.memes["hope"] += 1
    hero.memes["memory"] += 1
    world.say(
        f'{helper.label.capitalize()} {helper.suggest_verb} a remembering rhyme: '
        f'"{gate.rhyme}"'
    )
    world.say(
        f"The line was small enough to hold in a child mind, like a warm light in a long hall."
    )


def recite_rhyme(world: World, hero: Entity, gate: Gate) -> None:
    if hero.memes["memory"] < THRESHOLD:
        return
    hero.memes["courage"] += 1
    hero.memes["confusion"] = max(0.0, hero.memes["confusion"] - 1)
    world.say(
        f'{hero.id} whispered, "{gate.rhyme}" and took a steadier breath. '
        f'Now the airport felt less like a maze and more like a quest.'
    )


def advance(world: World, hero: Entity, gate: Gate) -> None:
    if hero.memes["memory"] < THRESHOLD:
        return
    while world.path_index < len(gate.path):
        spot = gate.path[world.path_index]
        world.path_index += 1
        hero.meters["steps"] += 1
        world.say(
            f"They passed {spot}. Each time {hero.id} repeated the rhyme, the next sign felt clearer."
        )


def arrive_gate(world: World, hero: Entity, parent: Entity, gate: Gate) -> None:
    if world.path_index < len(gate.path):
        return
    hero.memes["joy"] += 1
    hero.memes["worry"] = 0.0
    hero.memes["calm"] += 1
    world.say(
        f"At last they saw the sign for {gate.sign}. {hero.id}'s shoulders dropped in relief. "
        f'"We found it!" {hero.pronoun()} said.'
    )
    world.say(
        f"Beyond the window, the plane waited with shining wings. To {hero.id}, it looked less like an airplane "
        f"and more like a silver ship ready for a space adventure to {gate.destination}."
    )
    world.say(
        f"{parent.type.capitalize()} squeezed {hero.pronoun('possessive')} hand, and {hero.id} climbed into the gate seat "
        f"still softly saying the rhyme that had guided the quest."
    )


def tell(params: StoryParams) -> World:
    terminal = TERMINALS[params.terminal]
    gate = GATES[params.gate]
    helper = HELPERS[params.helper]
    item = ITEMS[params.item]

    world = World(terminal)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.gender == "girl" else "boy",
        traits=[params.trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=params.parent,
    ))
    helper_ent = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper.type,
        label=helper.label,
    ))
    thing = world.add(Entity(
        id="Item",
        kind="thing",
        type=item.id,
        label=item.label,
        phrase=item.phrase,
        owner=hero.id,
    ))

    world.facts.update(
        hero=hero,
        parent=parent,
        helper=helper,
        helper_ent=helper_ent,
        gate=gate,
        terminal=terminal,
        item=item,
        quest_complete=False,
    )

    introduce(world, hero, parent, item)
    airport_scene(world, hero)

    world.para()
    hear_clamor(world, hero, gate)
    parent_notices(world, hero, parent, item)
    helper_arrives(world, helper_ent, helper)
    suggest_rhyme(world, hero, helper_ent, helper, gate)

    world.para()
    recite_rhyme(world, hero, gate)
    advance(world, hero, gate)
    arrive_gate(world, hero, parent, gate)

    world.facts["quest_complete"] = hero.memes["calm"] >= THRESHOLD
    world.facts["hero_confused"] = hero.memes["confusion"] < THRESHOLD
    world.facts["steps"] = hero.meters["steps"]
    world.facts["rhyme"] = gate.rhyme
    world.facts["destination"] = gate.destination
    return world


KNOWLEDGE = {
    "airport": [
        (
            "What is an airport?",
            "An airport is a place where people go to ride on airplanes, check signs, and wait at gates before flying."
        )
    ],
    "gate": [
        (
            "What is an airport gate?",
            "An airport gate is the place where travelers wait and then walk onto the airplane when it is time to board."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is a pair or group of words that sound alike, like 'me' and 'three.' Rhymes can help people remember things."
        )
    ],
    "clamor": [
        (
            "What does clamor mean?",
            "Clamor means a lot of loud sounds all together, like many voices, wheels, and beeps making a busy noise."
        )
    ],
    "suggest": [
        (
            "What does suggest mean?",
            "Suggest means to offer an idea that might help, like telling someone a good way to remember a gate."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey to reach a goal. In a story, even a walk to the right gate can feel like a quest."
        )
    ],
}

KNOWLEDGE_ORDER = ["airport", "gate", "rhyme", "clamor", "suggest", "quest"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    gate = world.facts["gate"]
    helper = world.facts["helper"]
    return [
        'Write a gentle TinyStories-style tale set in an airport, with a child hero, the word "clamor," and a helper who uses a rhyme.',
        f"Tell a child-facing airport quest about {hero.id}, who forgets {gate.sign} in the noisy terminal until {helper.label} suggests a rhyme.",
        "Write a simple space-adventure-flavored story where an airport feels like a launch station and a rhyme helps a child find the right gate.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    gate = world.facts["gate"]
    helper = world.facts["helper"]
    item = world.facts["item"]
    terminal = world.facts["terminal"]
    return [
        QAItem(
            question=f"Where was {hero.id} at the beginning of the story?",
            answer=(
                f"{hero.id} was at {terminal.label} in the airport with {hero.pronoun('possessive')} {parent.type}. "
                f"{hero.pronoun().capitalize()} carried {item.phrase} and was getting ready for a trip."
            ),
        ),
        QAItem(
            question=f"Why did {hero.id} feel mixed up in the airport?",
            answer=(
                f"{hero.id} felt mixed up because the airport clamor was loud with voices, wheels, and sounds from the screens. "
                f"That noise made it hard to hold onto the gate name in {hero.pronoun('possessive')} mind."
            ),
        ),
        QAItem(
            question=f"Who helped {hero.id}, and what did that helper suggest?",
            answer=(
                f"{helper.label.capitalize()} helped {hero.id}. {helper.label.capitalize()} suggested a remembering rhyme: "
                f'"{gate.rhyme}" The rhyme gave the child a small, clear way to remember the gate.'
            ),
        ),
        QAItem(
            question=f"How did the rhyme help on the quest to {gate.sign}?",
            answer=(
                f"Each time {hero.id} said the rhyme again, the path through the terminal felt clearer. "
                f"The rhyme turned the walk into a quest with a guide, so {hero.pronoun()} could keep moving toward {gate.sign}."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"By the end, {hero.id} and {parent.type} reached {gate.sign}. "
                f"{hero.id}'s worry faded, and the waiting plane looked like a silver ship ready for a space adventure to {gate.destination}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(parts)}")
    lines.append(f"  quest_steps: {world.path_index}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
same_terminal(T,G) :- gate(G), gate_terminal(G,T).
same_terminal(T,H) :- helper(H), helper_terminal(H,T).

valid(T,G,H,I) :- terminal(T), gate(G), helper(H), item(I),
                  gate_terminal(G,T), helper_terminal(H,T), has_rhyme(G).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in TERMINALS:
        lines.append(asp.fact("terminal", tid))
    for gid, gate in GATES.items():
        lines.append(asp.fact("gate", gid))
        lines.append(asp.fact("gate_terminal", gid, gate.terminal))
        if gate.rhyme:
            lines.append(asp.fact("has_rhyme", gid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_terminal", hid, helper.stationed_at))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(show_rules: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show_rules}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Airport quest storyworld with rhyme, clamor, and a space-adventure feeling."
    )
    ap.add_argument("--terminal", choices=TERMINALS)
    ap.add_argument("--gate", choices=GATES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true", help="list valid terminal/gate/helper/item combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.terminal and args.gate:
        if GATES[args.gate].terminal != args.terminal:
            raise StoryError(explain_terminal_gate(args.terminal, args.gate))
    if args.terminal and args.helper:
        if HELPERS[args.helper].stationed_at != args.terminal:
            raise StoryError(explain_helper(args.helper, args.terminal))
    if args.gate and args.helper:
        if GATES[args.gate].terminal != HELPERS[args.helper].stationed_at:
            raise StoryError(
                f"(No story: {HELPERS[args.helper].label} is not stationed near {GATES[args.gate].sign}. "
                f"The helper needs to be in the same terminal to suggest the rhyme in time.)"
            )

    combos = [
        combo for combo in valid_combos()
        if (args.terminal is None or combo[0] == args.terminal)
        and (args.gate is None or combo[1] == args.gate)
        and (args.helper is None or combo[2] == args.helper)
        and (args.item is None or combo[3] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid airport quest matches the given options.)")

    terminal, gate, helper, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        terminal=terminal,
        gate=gate,
        helper=helper,
        item=item,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for terminal, gate, helper, item in asp_valid_combos():
            print(f"{terminal:6} {gate:7} {helper:12} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.name}: {p.gate} in {p.terminal} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
