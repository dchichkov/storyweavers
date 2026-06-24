#!/usr/bin/env python3
"""
A small storyworld for a pirate tale about caution, curiosity, and an anvil.

A child pirate or deckhand is drawn to a heavy anvil aboard a ship or at a
harbor forge. The captain or parent warns that the anvil is too heavy and may
crush a toe or break the deck. Curiosity pushes the child to peek, tug, or try
to move it anyway. A safer plan follows: the child learns to look, ask, and use
the right tool or helper instead of forcing the anvil.

The prose is driven by a tiny simulation:
- typed entities with physical meters and emotional memes
- anvil weight, footing danger, and curiosity/caution state
- warning, disobedience, near-miss, and resolution as causal state changes

The story remains child-facing and concrete, with a clear turn and ending image.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "captain"}
        if self.type in female and self.type not in male:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male and self.type not in female:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the pirate ship"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    danger: str
    zone: set[str]
    keyword: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


def _r_crush(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("pull", 0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.id != "anvil":
                continue
            if ("crush", actor.id) in world.fired:
                continue
            world.fired.add(("crush", actor.id))
            actor.meters["fear"] = actor.meters.get("fear", 0) + 1
            actor.meters["stopped"] = actor.meters.get("stopped", 0) + 1
            out.append(f"The anvil did not budge, and the ship gave a low groan.")
    return out


def _r_caution(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("warning", 0) < THRESHOLD:
            continue
        if actor.memes.get("curiosity", 0) < THRESHOLD:
            continue
        if ("caution", actor.id) in world.fired:
            continue
        world.fired.add(("caution", actor.id))
        actor.memes["care"] = actor.memes.get("care", 0) + 1
        out.append(f"The warning settled in like a lantern glow.")
    return out


CAUSAL_RULES = [_r_crush, _r_caution]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_push(world: World, actor: Entity, action: Action) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["pull"] = sim.get(actor.id).meters.get("pull", 0) + 1
    sim.get(actor.id).memes["curiosity"] = sim.get(actor.id).memes.get("curiosity", 0) + 1
    propagate(sim, narrate=False)
    return {
        "blocked": sim.get(actor.id).meters.get("stopped", 0) >= THRESHOLD,
        "fear": sim.get(actor.id).meters.get("fear", 0),
    }


def build_reasonable_gate() -> dict[str, list[str]]:
    return {
        "setting": sorted(SETTINGS),
        "action": sorted(ACTIONS),
        "tool": sorted(TOOLS),
    }


SETTINGS = {
    "deck": Setting(place="the ship's deck", affords={"peek"}),
    "hold": Setting(place="the cargo hold", affords={"peek", "pull"}),
    "dock": Setting(place="the moonlit dock", affords={"peek", "pull"}),
}

ACTIONS = {
    "peek": Action(
        id="peek",
        verb="peek at the anvil",
        gerund="peeking at the anvil",
        rush="rush closer for a better look",
        risk="the anvil could slip on the boards",
        danger="a toe could get smashed",
        zone={"feet", "hands"},
        keyword="anvil",
    ),
    "pull": Action(
        id="pull",
        verb="pull the anvil",
        gerund="pulling the anvil",
        rush="grab the rope and heave",
        risk="the anvil was far too heavy to move alone",
        danger="the deck could creak and the foot could be pinched",
        zone={"feet", "hands"},
        keyword="anvil",
    ),
}

TOOLS = {
    "crate": Tool(
        id="crate",
        label="a sturdy crate",
        phrase="a sturdy crate to stand on",
        prep="bring a sturdy crate over",
        tail="moved the anvil only by looking and pointing, not by tugging",
    ),
    "trolley": Tool(
        id="trolley",
        label="a little trolley",
        phrase="a little trolley with iron wheels",
        prep="roll over a little trolley",
        tail="used the trolley to carry the anvil safely",
    ),
}

NAMES = ["Mina", "Tess", "Jory", "Pip", "Nico", "Luna", "Harbor", "Rory"]
ROLE_TYPES = ["girl", "boy"]
PARENT_TYPES = ["captain", "mother", "father"]
TRAITS = ["curious", "cautious", "brave", "lively", "spirited"]


@dataclass
class StoryParams:
    place: str
    action: str
    tool: str
    name: str
    role_type: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for tool in TOOLS:
                if act == "pull" and tool == "trolley":
                    combos.append((place, act, tool))
                if act == "peek" and tool in {"crate", "trolley"}:
                    combos.append((place, act, tool))
    return combos


def explain_rejection(action: Action, tool: Tool) -> str:
    return (
        f"(No story: {action.verb} and {tool.label} do not make a believable pirate-ship fix. "
        f"Choose a safer pairing such as a crate for peeking or a trolley for moving.)"
    )


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for r in sorted(act.zone):
            lines.append(asp.fact("zone", aid, r))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Act, Tool) :- affords(Place, Act), action(Act), tool(Tool),
                           (Act = peek, Tool = crate; Act = peek, Tool = trolley; Act = pull, Tool = trolley).
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
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld about caution and curiosity.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--name")
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
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid pirate-story combination matches the given options.)")
    place, action, tool = rng.choice(sorted(combos))
    role_type = args.gender or rng.choice(ROLE_TYPES)
    name = args.name or rng.choice(NAMES)
    parent_type = args.parent or rng.choice(PARENT_TYPES)
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place, action, tool, name, role_type, parent_type, trait)


def predict_mess(world: World, actor: Entity, action: Action) -> dict:
    sim = world.copy()
    sim.get(actor.id).memes["curiosity"] = sim.get(actor.id).memes.get("curiosity", 0) + 1
    sim.get(actor.id).meters["pull"] = sim.get(actor.id).meters.get("pull", 0) + 1
    propagate(sim, narrate=False)
    return {"blocked": sim.get(actor.id).meters.get("stopped", 0) >= THRESHOLD}


def tell(setting: Setting, action: Action, tool: Tool, hero_name: str, role_type: str,
         parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=role_type, memes={"curiosity": 1.0, "care": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the captain"))
    anvil = world.add(Entity(id="anvil", type="anvil", label="an anvil", phrase="a black iron anvil"))
    crate = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase))
    world.facts.update(hero=hero, parent=parent, action=action, tool=crate, anvil=anvil, trait=trait)

    world.say(f"{hero.id} was a little {trait} {role_type} aboard {setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} loved {action.gerund} because the ship felt full of secret places.")
    world.say(f"Near the mast sat {anvil.phrase}, heavy and shiny like a piece of night.")

    world.para()
    world.say(f"One day, {hero.id} wanted to {action.verb}, but {parent.label} gave a cautious look.")
    world.say(f'"Leave that be," {parent.pronoun("subject")} said. "{action.risk.capitalize()}."')

    hero.memes["warning"] = 1.0
    hero.memes["curiosity"] += 1.0
    if predict_mess(world, hero, action)["blocked"]:
        world.say(f"But curiosity tickled {hero.pronoun("possessive")} nose, and {hero.pronoun("subject")} still {action.rush}.")
    hero.meters["pull"] = hero.meters.get("pull", 0) + 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"Then {parent.pronoun("subject")} pointed to {tool.label} and smiled.")
    world.say(f'"How about we {tool.prep} first?" {parent.pronoun("subject").capitalize()} asked.')
    hero.memes["care"] += 1.0
    hero.memes["curiosity"] += 0.5
    world.say(f"{hero.id} nodded, climbed up on {tool.label}, and studied the anvil without trying to drag it.")

    if action.id == "pull":
        world.say(f"Together, they used the safe gear and did not force the heavy iron at all.")
    else:
        world.say(f"The anvil stayed put, but {hero.id}'s eyes got wide with the fun of learning something new.")
    world.say(f"In the end, {tool.tail}, and the deck stayed sound under their feet.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    return [
        f'Write a short pirate tale for a young child that includes the word "anvil" and a careful warning.',
        f"Tell a story where {hero.id} wants to {action.verb} but learns a safer way aboard a pirate ship.",
        f"Write a gentle cautionary curiosity story about a child pirate, a heavy anvil, and a better plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    action = f["action"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the anvil?",
            answer=f"{hero.id} wanted to {action.verb}, because curiosity pulled hard and the shiny anvil looked interesting.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn {hero.id}?",
            answer=f"{parent.label.capitalize()} warned {hero.id} because {action.risk}, and a heavy anvil could hurt someone if it slipped.",
        ),
        QAItem(
            question=f"How did {tool.label} help at the end?",
            answer=f"{tool.label.capitalize()} gave {hero.id} a safer way to look and work, so the anvil could be handled without forcing it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an anvil?",
            answer="An anvil is a very heavy block of metal that blacksmiths use for hammering and shaping metal.",
        ),
        QAItem(
            question="Why should you be careful around heavy things?",
            answer="Heavy things can slip, fall, or crush toes and fingers, so people use care and the right tools.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more about something, especially something new or interesting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], TOOLS[params.tool],
                 params.name, params.role_type, params.parent_type, params.trait)
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, action, tool) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in [
            StoryParams("deck", "peek", "crate", "Mina", "girl", "captain", "curious"),
            StoryParams("hold", "pull", "trolley", "Jory", "boy", "father", "cautious"),
            StoryParams("dock", "peek", "trolley", "Luna", "girl", "mother", "brave"),
        ]:
            samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


if __name__ == "__main__":
    main()
