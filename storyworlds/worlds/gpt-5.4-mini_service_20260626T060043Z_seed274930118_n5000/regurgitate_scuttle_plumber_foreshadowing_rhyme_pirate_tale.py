#!/usr/bin/env python3
"""
A standalone storyworld for a tiny Pirate Tale domain with foreshadowing and rhyme.

Premise:
- A small crew sails with a noisy captain, a cautious plumber, and a very seasick parrot.
- A leak threatens the ship.
- Foreshadowing hints at trouble before the reveal.
- Rhyme is used as a recurring child-facing narrative instrument.

The world simulation tracks physical meters and emotional memes, and the story
emerges from that state rather than from a frozen paragraph.
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

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "leak": 0.0, "fixed": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "hope": 0.0, "pride": 0.0, "gloom": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "maid"}
        male = {"boy", "man", "father", "captain", "plumber", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str = "the Merry Gull"
    setting: str = "at sea"
    leak_spot: str = "the bilge"
    leak_open: bool = True
    fixed: bool = False
    rhyme: bool = True
    foreshadowing: bool = True
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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

    def copy(self) -> "Ship":
        import copy as _copy
        clone = Ship(name=self.name, setting=self.setting, leak_spot=self.leak_spot,
                     leak_open=self.leak_open, fixed=self.fixed, rhyme=self.rhyme,
                     foreshadowing=self.foreshadowing)
        clone.paragraphs = [[]]
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b}"


def foreshadow_line(ship: Ship) -> str:
    return "A drip in the dark made a plip-plop start, like the ship had a secret under its heart."


def crew_name(role: str) -> str:
    return {
        "captain": "Captain Brine",
        "plumber": "Pipejack",
        "parrot": "Mango",
        "mate": "Nell",
    }[role]


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------

def propagate(ship: Ship, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        # Leak spreads worry while open.
        if ship.leak_open and ("leak", "worry") not in ship.fired:
            ship.fired.add(("leak", "worry"))
            for c in ship.characters():
                c.memes["worry"] += 1
            produced.append("The crew felt a little worry as the water kept whispering through the boards.")
            changed = True

        # Seasickness can make the parrot regurgitate.
        parrot = ship.entities.get("parrot")
        if parrot and parrot.memes.get("sick", 0.0) >= THRESHOLD and ("parrot", "regurgitate") not in ship.fired:
            ship.fired.add(("parrot", "regurgitate"))
            parrot.meters["wet"] += 1
            produced.append("Mango regurgitated a salty splash onto the deck.")
            changed = True

        # Fixing the leak resolves gloom and raises hope.
        if ship.fixed and ("fixed", "hope") not in ship.fired:
            ship.fired.add(("fixed", "hope"))
            for c in ship.characters():
                c.memes["hope"] += 1
                c.memes["gloom"] = 0
            produced.append("The board stayed tight, and the crew's hope rose bright.")
            changed = True

    if narrate:
        for line in produced:
            ship.say(line)
    return produced


def predict_leak(ship: Ship) -> dict:
    sim = ship.copy()
    sim.leak_open = True
    propagate(sim, narrate=False)
    return {
        "worry": sum(e.memes.get("worry", 0.0) for e in sim.characters()),
        "wet": sim.get("parrot").meters["wet"] if "parrot" in sim.entities else 0.0,
    }


# ---------------------------------------------------------------------------
# Story registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    captain: str = "Brine"
    mate: str = "Nell"
    plumber: str = "Pipejack"
    parrot: str = "Mango"
    ship: str = "the Merry Gull"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> Ship:
    ship = Ship(name=params.ship)
    captain = ship.add(Entity(id="captain", kind="character", type="captain", label=crew_name("captain")))
    mate = ship.add(Entity(id="mate", kind="character", type="pirate", label=crew_name("mate")))
    plumber = ship.add(Entity(id="plumber", kind="character", type="plumber", label=crew_name("plumber")))
    parrot = ship.add(Entity(id="parrot", kind="character", type="parrot", label=crew_name("parrot")))

    # Setup
    ship.say(f"On {ship.name}, {captain.label} liked a bold tune, and {mate.label} hummed it back with a swoon.")
    ship.say(f"{plumber.label} was the ship's plumber, proud of pipes, pumps, and a snug little clamp.")
    ship.say(f"{parrot.label} perched nearby, eyes a bit green, as if the sea breeze was too much for the bird to ramble.")
    if ship.foreshadowing:
        ship.say(foreshadow_line(ship))

    ship.para()

    # Turn: leak + sickness
    captain.memes["pride"] += 1
    mate.memes["worry"] += 0.5
    parrot.memes["sick"] = 1.0
    ship.say(f"Then the deck gave a squeak, and a trickle ran weak; the water was sneaking in under the beak of the ship.")
    ship.say("The captain frowned, the mate looked down, and Mango made a gulping chirp.")
    propagate(ship)

    ship.para()

    # Tension: plumber notices and proposes repair
    leak_report = predict_leak(ship)
    ship.facts["predicted_worry"] = leak_report["worry"]
    ship.facts["predicted_wet"] = leak_report["wet"]
    ship.say(f"{plumber.label} knelt by the boards and said, \"If we leave it alone, the bilge will groan.\"")
    ship.say(f"\"Fix it now, or the whole crew will frown,\" {plumber.label} said, \"and Mango may regurgitate down.\"")

    # Resolution: plumber fixes leak
    ship.leak_open = False
    ship.fixed = True
    ship.get("plumber").meters["fixed"] += 1
    ship.get("plumber").memes["pride"] += 1
    ship.say(f"{plumber.label} twisted a valve, tucked a patch, and tapped the seam with a careful catch.")
    ship.say("Plip went the drip, then stop went the flop; the leak was mended from bottom to top.")
    propagate(ship)

    ship.para()

    ship.say(f"{captain.label} laughed, {mate.label} clapped, and Mango shook off the last little splash.")
    ship.say(f"By sunset, {ship.name} sailed smooth and neat, and even the pipes seemed to sing to the beat.")

    ship.facts.update(
        captain=captain,
        mate=mate,
        plumber=plumber,
        parrot=parrot,
        ship=ship,
        leak_fixed=True,
    )
    return ship


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: Ship) -> list[str]:
    return [
        f'Write a short pirate story for a child that includes the words "regurgitate", "scuttle", and "plumber".',
        f"Tell a pirate tale where {world.get('plumber').label} fixes a leak before Mango gets any wetter.",
        "Write a rhyming pirate story with foreshadowing, a little trouble, and a clever repair.",
    ]


def story_qa(world: Ship) -> list[QAItem]:
    captain = world.get("captain")
    plumber = world.get("plumber")
    parrot = world.get("parrot")
    mate = world.get("mate")
    return [
        QAItem(
            question="Who was the plumber in the story?",
            answer=f"The plumber was {plumber.label}, the crew member who knew how to fix pipes and leaks.",
        ),
        QAItem(
            question="Why did the crew get worried?",
            answer="They got worried because water was sneaking into the ship, and the leak could make the deck wet and messy.",
        ),
        QAItem(
            question="What happened to Mango before the repair?",
            answer=f"Mango felt seasick and regurgitated a salty splash onto the deck before {plumber.label} finished the fix.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the leak sealed, the crew smiling, and {world.name} sailing smoothly again.",
        ),
    ]


def world_knowledge_qa(world: Ship) -> list[QAItem]:
    return [
        QAItem(
            question="What does a plumber do?",
            answer="A plumber fixes pipes, drains, and leaks so water goes where it should.",
        ),
        QAItem(
            question="What does regurgitate mean?",
            answer="Regurgitate means to bring food or liquid back up from the stomach or throat.",
        ),
        QAItem(
            question="What does scuttle mean on a ship?",
            answer="To scuttle a ship means to sink it or make it go under, usually on purpose.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small hint about trouble or an important event that will happen later.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like cat and hat.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: Ship) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  leak_open={world.leak_open} fixed={world.fixed}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A leak is present when the ship's bilge is open.
leak_present(ship).

% If a plumber fixes the leak, the ship is no longer leaky.
fixed(ship) :- plumber(plumber).

% A parrot regurgitates if it is seasick.
regurgitates(parrot) :- sick(parrot).

% A story is reasonable when it includes a plumber, a leak, and a compatible repair.
reasonable_story :- plumber(plumber), leak_present(ship), fixed(ship).

#show reasonable_story/0.
#show regurgitates/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("plumber", "plumber"),
        asp.fact("pirate", "captain"),
        asp.fact("pirate", "mate"),
        asp.fact("parrot", "parrot"),
        asp.fact("sick", "parrot"),
        asp.fact("leak_present", "ship"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable_story/0.\n#show regurgitates/1."))
    return asp.atoms(model, "regurgitates")


def asp_verify() -> int:
    py = True
    asp_model = asp_reasonable()
    if py and asp_model == [("parrot",)]:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", asp_model)
    return 1


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate Tale storyworld with foreshadowing and rhyme.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        captain="Brine",
        mate="Nell",
        plumber="Pipejack",
        parrot="Mango",
        ship="the Merry Gull",
        seed=args.seed,
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
        print(asp_program("#show reasonable_story/0.\n#show regurgitates/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is present for parity checks.")
        print("regurgitates:", asp_reasonable())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        params = StoryParams(seed=base_seed)
        samples = [generate(params)]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
