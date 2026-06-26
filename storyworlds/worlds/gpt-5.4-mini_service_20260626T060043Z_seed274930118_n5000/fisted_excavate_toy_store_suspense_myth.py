#!/usr/bin/env python3
"""
A standalone story world for a toy-store myth with suspense.

Premise:
- In a toy store, a small seeker wants to excavate a buried treasure in a sand
  bin beneath the display tables.
- A fisted guardian worries that the dig will crack a fragile toy idol.
- The seeker uses careful tools, listens to signs, and discovers that the "treasure"
  is not gold but a lost tiny crown that belonged to a forgotten puppet king.

The world is modeled with physical meters and emotional memes. The story is
generated from state transitions, and the ASP twin checks the reasonableness gate
for compatible settings, actions, and relics.
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
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "damage": 0.0, "found": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "fear": 0.0, "wonder": 0.0, "resolve": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "priestess"}
        male = {"boy", "father", "man", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the toy store"
    affords: set[str] = field(default_factory=lambda: {"excavate", "search", "listen"})


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    risk: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: str = ""
        self.weather: str = ""
        self.signs: list[str] = []

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
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.zone = self.zone
        clone.weather = self.weather
        clone.signs = list(self.signs)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = Setting(place="the toy store")

ACTIONS = {
    "excavate": Action(
        id="excavate",
        verb="excavate the hidden mound",
        gerund="excavating the hidden mound",
        rush="rush to dig with bare hands",
        mess="dust",
        risk="dusty and scratched",
        clue="the hum of old prizes",
        tags={"excavate", "suspense", "myth"},
    ),
    "search": Action(
        id="search",
        verb="search the shelves for the lost thing",
        gerund="searching the shelves",
        rush="hurry from aisle to aisle",
        mess="dust",
        risk="lost in the aisles",
        clue="a whisper behind the dolls",
        tags={"search", "suspense"},
    ),
}

RELICS = {
    "crown": Relic(
        label="tiny crown",
        phrase="a tiny gold crown",
        type="crown",
        region="hands",
    ),
    "mask": Relic(
        label="silver mask",
        phrase="a silver mask with painted stars",
        type="mask",
        region="hands",
    ),
    "drum": Relic(
        label="drum",
        phrase="a little drum with a red strap",
        type="drum",
        region="hands",
    ),
}

TOOLS = [
    Tool(
        id="brush",
        label="a soft brush",
        prep="take a soft brush from the counter",
        tail="used the soft brush to lift the dust",
        protects={"dust"},
    ),
    Tool(
        id="lantern",
        label="a paper lantern",
        prep="light a paper lantern",
        tail="let the paper lantern glow over the mound",
        protects=set(),
    ),
    Tool(
        id="cloth",
        label="a clean cloth",
        prep="wrap the finds in a clean cloth",
        tail="kept the treasure safe in the clean cloth",
        protects={"dust"},
    ),
]

NAMES = ["Mira", "Niko", "Ira", "Lena", "Orin", "Tala", "Soren", "Pia"]
TRAITS = ["curious", "quiet", "brave", "small", "earnest", "gentle"]
GUARD_TYPES = ["mother", "father", "keeper", "merchant"]
WARD_TYPES = ["girl", "boy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% An action is reasonable in the toy store if the place affords it.
valid_action(P, A) :- affords(P, A).

% A relic is at risk if the action makes dust and the relic is delicate in-hand treasure.
at_risk(A, R) :- action(A), mess_of(A, dust), relic(R).

% A tool is a compatible fix if it protects against the action's mess.
compatible_tool(T, A) :- tool(T), action(A), protects(T, dust).

% A story is valid when the action is valid, the relic is at risk, and some tool fits.
valid_story(P, A, R) :- valid_action(P, A), at_risk(A, R), compatible_tool(_, A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("place", "toy_store"))
    for a in ACTIONS.values():
        lines.append(asp.fact("action", a.id))
        lines.append(asp.fact("mess_of", a.id, a.mess))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for p in sorted(t.protects):
            lines.append(asp.fact("protects", t.id, p))
    for r in RELICS.values():
        lines.append(asp.fact("relic", r.type))
    lines.append(asp.fact("affords", "toy_store", "excavate"))
    lines.append(asp.fact("affords", "toy_store", "search"))
    lines.append(asp.fact("affords", "toy_store", "listen"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid_story/3."))
    cl = set(asp.atoms(model, "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in ["toy_store"]:
        for action in ACTIONS:
            for relic in RELICS:
                if action == "excavate" and relic in {"crown", "mask", "drum"}:
                    combos.append((place, action, relic))
                if action == "search" and relic in {"crown", "mask", "drum"}:
                    combos.append((place, action, relic))
    return combos


def explain_rejection(action: Action, relic: Relic) -> str:
    return (
        f"(No story: {action.verb} does not fit this toy-store relic in a way "
        f"that creates real suspense and a believable rescue.)"
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def predict(world: World, hero: Entity, action: Action, relic_id: str) -> dict:
    sim = world.copy()
    perform_action(sim, sim.get(hero.id), action, narrate=False)
    relic = sim.get(relic_id)
    return {
        "dust": relic.meters["damage"] >= THRESHOLD,
        "found": relic.meters["found"] >= THRESHOLD,
    }


def perform_action(world: World, hero: Entity, action: Action, narrate: bool = True) -> None:
    world.zone = action.id
    hero.meters["dust"] += 1
    hero.memes["resolve"] += 1
    hero.memes["wonder"] += 1
    relic = world.get(world.facts["relic"].id)
    if action.id == "excavate":
        relic.meters["found"] += 1
    if narrate:
        world.say(f"{hero.id} began to {action.verb}, and the air turned {action.risk}.")
        world.say(f"Every small move followed the clue of {action.clue}.")
    if hero.meters["dust"] >= THRESHOLD and narrate:
        world.say(f"The floor went pale with dust, and the shelves seemed to hold their breath.")


def guardian_warns(world: World, guardian: Entity, hero: Entity, action: Action, relic: Entity) -> bool:
    pred = predict(world, hero, action, relic.id)
    if not pred["dust"]:
        return False
    world.facts["predicted_dust"] = True
    world.say(
        f'"Do not {action.verb}," {guardian.pronoun("subject").capitalize()} said, '
        f'"or the {relic.label} will be ruined by dust."'
    )
    return True


def hero_fists(world: World, hero: Entity) -> None:
    hero.memes["fear"] += 1
    world.say(f"{hero.id} fisted {hero.pronoun('possessive')} hands and stood very still.")
    world.say(f"The silence around the toy store felt older than the shelves.")


def show_sign(world: World, action: Action) -> None:
    world.signs.append(action.clue)
    world.say(f"Then a sign appeared: {action.clue}.")
    world.say("It was not a voice, only the feeling that the right tool was waiting somewhere nearby.")


def offer_tool(world: World, guardian: Entity, hero: Entity, action: Action, relic: Entity) -> Optional[Tool]:
    for tool in TOOLS:
        if "dust" not in tool.protects:
            continue
        if predict(world, hero, action, relic.id)["dust"]:
            world.say(
                f"{guardian.id} lifted {tool.label} and said, "
                f'"Take this first. The treasure must be touched gently."'
            )
            return tool
    return None


def accept_tool(world: World, hero: Entity, guardian: Entity, action: Action, relic: Entity, tool: Tool) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["hope"] += 1
    hero.memes["wonder"] += 1
    world.say(
        f"{hero.id} nodded, took {tool.label}, and followed the slow way."
    )
    world.say(
        f"They {tool.tail}, and the {relic.label} rose from the dust without a crack."
    )
    world.say(
        f"In the end, the old treasure glittered like a small moon, and the toy store was quiet again."
    )


def tell_story(hero_name: str, hero_type: str, guardian_type: str, trait: str,
               action: Action, relic: Relic) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    guardian = world.add(Entity(id="Guardian", kind="character", type=guardian_type))
    relic_ent = world.add(Entity(id="relic", type=relic.type, label=relic.label, phrase=relic.phrase))
    world.facts["relic"] = relic_ent

    world.say(f"{hero.id} was a {trait} little {hero.type} who loved the hush of the toy store.")
    world.say(f"Behind the bright dolls, {hero.id} believed something ancient was hiding.")
    world.say(f"It was said that a {relic.label} slept under the sand bin, waiting to be excavated.")

    world.para()
    world.say(f"One evening, {hero.id} went deeper into the toy store where the lamps were low.")
    world.say(f"{hero.id} wanted to {action.verb}, because {action.clue} kept pulling {hero.pronoun('object')} onward.")
    guardian_warns(world, guardian, hero, action, relic_ent)
    hero_fists(world, hero)
    show_sign(world, action)

    world.para()
    tool = offer_tool(world, guardian, hero, action, relic_ent)
    if tool:
        world.say(
            f"{hero.id} took a careful breath and chose the slower path."
        )
        hero.memes["hope"] += 1
        perform_action(world, hero, action, narrate=True)
        accept_tool(world, hero, guardian, action, relic_ent, tool)
    else:
        world.say("No gentle tool was near, so the mystery stayed asleep.")

    world.facts.update(
        hero=hero,
        guardian=guardian,
        action=action,
        relic=relic_ent,
        tool=tool,
        resolved=tool is not None,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    relic = f["relic"]
    return [
        f'Write a short myth-like story set in a toy store where {hero.id} must {action.verb} to find {relic.phrase}.',
        f'Create a suspenseful child-friendly tale about a {hero.type} named {hero.id}, a fisted warning, and a hidden treasure in the toy store.',
        f'Write a small myth in which a gentle tool helps a seeker excavate a buried relic without breaking it.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guardian = f["guardian"]
    action = f["action"]
    relic = f["relic"]
    tool = f.get("tool")
    qa = [
        QAItem(
            question=f"Where did {hero.id} look for the hidden treasure?",
            answer=f"{hero.id} looked in the toy store, where the shelves, lamps, and sand bin made the place feel like an old myth.",
        ),
        QAItem(
            question=f"Why did {guardian.id} warn {hero.id} about {action.verb}?",
            answer=f"{guardian.id} warned {hero.id} because the digging would stir up dust and could ruin the {relic.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} do with {hero.pronoun('possessive')} hands when the warning came?",
            answer=f"{hero.id} fisted {hero.pronoun('possessive')} hands and waited, feeling the suspense of the moment.",
        ),
    ]
    if tool:
        qa.append(
            QAItem(
                question=f"How did {tool.label} help the search end safely?",
                answer=f"{tool.label.capitalize()} helped because it let them lift the dust gently, so the {relic.label} came up whole.",
            )
        )
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"What was discovered in the end?",
                answer=f"In the end, they found the {relic.label}, and it glittered like a small moon after the dust cleared.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "excavate": (
        "What does it mean to excavate something?",
        "To excavate means to dig something carefully out of the ground or out of a buried place.",
    ),
    "dust": (
        "Why can dust be messy in a store?",
        "Dust can cover things, make them look dull, and get into tiny spaces where it is hard to clean.",
    ),
    "toy_store": (
        "What is a toy store?",
        "A toy store is a shop where children can find dolls, games, blocks, puzzles, and many other toys.",
    ),
    "suspense": (
        "What is suspense in a story?",
        "Suspense is the feeling of waiting and wondering what will happen next.",
    ),
    "myth": (
        "What is a myth-like story?",
        "A myth-like story feels old and grand, as if it remembers kings, treasures, and special signs.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["action"].tags)
    tags.add("toy_store")
    out: list[QAItem] = []
    for key in ["toy_store", "excavate", "dust", "suspense", "myth"]:
        if key in tags or key in {"toy_store", "suspense", "myth"}:
            q, a = WORLD_KNOWLEDGE[key]
            out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge Q&A ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  signs: {world.signs}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    action: str
    relic: str
    name: str
    gender: str
    guardian: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Toy-store myth with suspense.")
    ap.add_argument("--place", choices=["toy_store"], default="toy_store")
    ap.add_argument("--action", choices=sorted(ACTIONS))
    ap.add_argument("--relic", choices=sorted(RELICS))
    ap.add_argument("--gender", choices=WARD_TYPES)
    ap.add_argument("--guardian", choices=GUARD_TYPES)
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
    if args.action and args.relic:
        if (args.place, args.action, args.relic) not in valid_combos():
            raise StoryError(explain_rejection(ACTIONS[args.action], RELICS[args.relic]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.relic is None or c[2] == args.relic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, relic = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(WARD_TYPES)
    name = args.name or rng.choice(NAMES)
    guardian = args.guardian or rng.choice(GUARD_TYPES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, action=action, relic=relic, name=name, gender=gender, guardian=guardian, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(
        hero_name=params.name,
        hero_type=params.gender,
        guardian_type=params.guardian,
        trait=params.trait,
        action=ACTIONS[params.action],
        relic=RELICS[params.relic],
    )
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


# ---------------------------------------------------------------------------
# CLI / ASP
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_facts_for_verify() -> str:
    return asp_facts()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("toy_store", "excavate", "crown", "Mira", "girl", "keeper", "curious"),
            StoryParams("toy_store", "search", "mask", "Niko", "boy", "merchant", "brave"),
            StoryParams("toy_store", "excavate", "drum", "Tala", "girl", "mother", "gentle"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
