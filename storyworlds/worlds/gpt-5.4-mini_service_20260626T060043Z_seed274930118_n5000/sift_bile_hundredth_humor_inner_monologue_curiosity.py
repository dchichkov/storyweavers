#!/usr/bin/env python3
"""
A small pirate-tale storyworld: a curious deckhand, a grumpy captain, and a
sealed chest that must be opened with wit instead of brute force.

The seed words and style cues are embedded in the world model:
- sift
- bile
- hundredth
- Humor, Inner Monologue, Curiosity
- Pirate Tale
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "deckhand", "mate", "captain", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Deck:
    name: str = "the ship"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str


@dataclass
class Prize:
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
    guards: set[str]
    covers: set[str]
    plural: bool = False


class World:
    def __init__(self, deck: Deck) -> None:
        self.deck = deck
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.deck)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
DECKS = {
    "ship": Deck(name="the ship", affords={"sift"}),
    "cabin": Deck(name="the captain's cabin", affords={"sift"}),
}

ACTIONS = {
    "sift": Action(
        id="sift",
        verb="sift through the powder",
        gerund="sifting through the powder",
        rush="run to the powder barrel",
        mess="dusty",
        soil="all dusty",
        zone={"hands", "torso"},
        keyword="sift",
    ),
    "bile": Action(
        id="bile",
        verb="taste the bile brew",
        gerund="tasting the bile brew",
        rush="gulp the green cup",
        mess="sour",
        soil="all sour",
        zone={"mouth", "hands"},
        keyword="bile",
    ),
    "curiosity": Action(
        id="curiosity",
        verb="peek into the locked chest",
        gerund="peeking into the locked chest",
        rush="run to the chest",
        mess="dusty",
        soil="scratched and dusty",
        zone={"hands", "eyes"},
        keyword="curiosity",
    ),
}

PRIZES = {
    "coat": Prize(label="coat", phrase="a fine blue coat", type="coat", region="torso"),
    "gloves": Prize(label="gloves", phrase="soft white gloves", type="gloves", region="hands", plural=True),
    "hat": Prize(label="hat", phrase="a feathered hat", type="hat", region="head"),
}

TOOLS = [
    Tool(
        id="apron",
        label="a tar apron",
        prep="put on the tar apron first",
        tail="put on the tar apron and went back to the barrel",
        guards={"dusty"},
        covers={"torso"},
    ),
    Tool(
        id="scarf",
        label="a cloth scarf",
        prep="wrap a cloth scarf around his mouth",
        tail="wrapped on a cloth scarf and returned to the cup",
        guards={"sour"},
        covers={"mouth"},
    ),
    Tool(
        id="linen",
        label="a linen hood",
        prep="pull on a linen hood before peeking",
        tail="pulled on a linen hood and crept back to the chest",
        guards={"dusty"},
        covers={"eyes"},
    ),
]

NAMES = ["Finn", "Milo", "Jory", "Beck", "Pip", "Arlo"]
TRAITS = ["curious", "cheeky", "bright-eyed", "quick-witted", "merry"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    deck: str
    action: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region in action.zone


def select_tool(action: Action, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if action.mess in tool.guards and prize.region in tool.covers:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for d in DECKS:
        for a_id, a in ACTIONS.items():
            for p_id, p in PRIZES.items():
                if prize_at_risk(a, p) and select_tool(a, p):
                    out.append((d, a_id, p_id))
    return out


def explain_rejection(action: Action, prize: Prize) -> str:
    if not prize_at_risk(action, prize):
        return (
            f"(No story: {action.gerund} does not reach the {prize.region}, so "
            f"the captain would have no honest reason to object.)"
        )
    return (
        f"(No story: there is no tool that both handles {action.mess} and "
        f"covers the {prize.region}, so this tale would not have a fair fix.)"
    )


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
def _act(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.deck.affords and action.id != "curiosity" and action.id != "bile":
        return
    world.zone = set(action.zone)
    actor.meters[action.mess] = actor.meters.get(action.mess, 0.0) + 1
    actor.memes["excitement"] = actor.memes.get("excitement", 0.0) + 1
    if narrate:
        world.say(f"{actor.id} began {action.gerund}.")


def predict_mess(world: World, actor: Entity, action: Action, prize_id: str) -> dict:
    sim = world.copy()
    _act(sim, sim.get(actor.id), action, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": False, "dusty": actor.meters.get("dusty", 0) > 0, "sour": actor.meters.get("sour", 0) > 0}


def tell(deck: Deck, action: Action, prize_cfg: Prize, hero_name: str) -> World:
    world = World(deck)
    hero = world.add(Entity(id=hero_name, kind="character", type="deckhand", traits=["little", "curious"]))
    captain = world.add(Entity(id="Captain", kind="character", type="captain", label="the captain"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=hero.id, caretaker=captain.id, region=prize_cfg.region, plural=prize_cfg.plural))
    world.facts.update(hero=hero, captain=captain, prize=prize, action=action, deck=deck)

    world.say(f"{hero.id} was a little deckhand aboard {deck.name}, and {hero.pronoun('possessive')} head was always full of questions.")
    world.say(f"{hero.id} loved {action.gerund}, because it felt like hunting for secrets.")
    world.say(f"One day, {captain.label} gave {hero.pronoun('object')} {prize.phrase}, and {hero.id} wore {prize.it()} proudly.")

    world.para()
    world.say(f"On {deck.name}, {hero.id} wanted to {action.verb}, but {captain.label} frowned and said the prize would be ruined.")
    world.say(f'{hero.id} listened, then began an inner monologue: "If I do this the wrong way, {hero.pronoun("possessive")} {prize.label} will end up {action.soil}."')
    world.say(f"Still, {hero.id}'s curiosity kept tugging like a rope in the wind.")
    world.say(f"At the hundredth glance, {hero.id} noticed the old tool chest beside the lantern.")
    world.say(f"With a bit of humor, {hero.id} muttered, 'A pirate who cannot sift without a mess is no pirate at all.'")

    world.para()
    world.say(f"{hero.id} tried to {action.rush}, and {captain.label} raised a hand.")
    world.say(f"That was when {hero.id}'s inner monologue turned into a plan: the safe way must be clever, not loud.")
    tool = select_tool(action, prize)
    if not tool:
        raise StoryError(explain_rejection(action, prize))
    world.say(f"{captain.label} nodded and smiled. '{tool.prep}, and then you may try again,' {captain.label} said.")
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    world.para()
    world.say(f"{hero.id} did just that, and soon {hero.id} was {action.gerund} again, only now the {prize.label} stayed clean.")
    world.say(f"The little deckhand laughed, {captain.label} laughed too, and the ship went on through the salt air with the secret safely kept.")

    world.facts["tool"] = tool
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
fix(A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(T,M), covers(T,R), worn_on(P,R).
valid(D,A,P) :- affords(D,A), prize_at_risk(A,P), fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for d_id, d in DECKS.items():
        lines.append(asp.fact("deck", d_id))
        for a in sorted(d.affords):
            lines.append(asp.fact("affords", d_id, a))
    for a_id, a in ACTIONS.items():
        lines.append(asp.fact("action", a_id))
        lines.append(asp.fact("mess_of", a_id, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", a_id, r))
    for p_id, p in PRIZES.items():
        lines.append(asp.fact("prize", p_id))
        lines.append(asp.fact("worn_on", p_id, p.region))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, g))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale about a curious deckhand named {f["hero"].id} who must {f["action"].verb} without ruining {f["prize"].phrase}.',
        f"Tell a child-friendly pirate story that includes the words sift, bile, and hundredth, and uses humor and inner monologue.",
        f"Write a tale on {f['deck'].name} where curiosity leads to a problem and a clever fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, prize, action, tool = f["hero"], f["captain"], f["prize"], f["action"], f["tool"]
    return [
        QAItem(
            question=f"Who was the little deckhand in the story?",
            answer=f"The little deckhand was {hero.id}, who loved {action.gerund} and asking questions.",
        ),
        QAItem(
            question=f"Why did the captain worry about {prize.label}?",
            answer=f"The captain worried because if {hero.id} went to {action.verb} the {prize.label} would end up {action.soil}.",
        ),
        QAItem(
            question=f"What helped {hero.id} do it safely?",
            answer=f"{tool.label} helped {hero.id} try again without ruining {prize.label}.",
        ),
        QAItem(
            question="What did the hundredth glance reveal?",
            answer=f"The hundredth glance revealed the old tool chest beside the lantern, which gave {hero.id} a clever idea.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the strong wish to know more, which makes someone look closely and ask questions.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is when something is funny and makes people smile or laugh.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the silent voice in a character's mind when they think through a problem.",
        ),
        QAItem(
            question="What does sift mean?",
            answer="To sift means to let small bits pass through while keeping the bigger bits apart.",
        ),
        QAItem(
            question="What is bile?",
            answer="Bile is a bitter liquid in the body that helps break down food.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
    lines = ["--- world model ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(deck="ship", action="sift", prize="coat", name="Finn", trait="curious"),
    StoryParams(deck="cabin", action="curiosity", prize="gloves", name="Pip", trait="cheeky"),
    StoryParams(deck="ship", action="bile", prize="hat", name="Jory", trait="merry"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld: curiosity, humor, and a clever fix.")
    ap.add_argument("--deck", choices=DECKS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS := ["curious", "cheeky", "bright-eyed", "quick-witted", "merry"])
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
    if args.action and args.prize:
        if not (prize_at_risk(ACTIONS[args.action], PRIZES[args.prize]) and select_tool(ACTIONS[args.action], PRIZES[args.prize])):
            raise StoryError(explain_rejection(ACTIONS[args.action], PRIZES[args.prize]))
    combos = [c for c in valid_combos()
              if (args.deck is None or c[0] == args.deck)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    deck, action, prize = rng.choice(sorted(combos))
    return StoryParams(
        deck=deck,
        action=action,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(DECKS[params.deck], ACTIONS[params.action], PRIZES[params.prize], params.name)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
