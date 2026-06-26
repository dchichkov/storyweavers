#!/usr/bin/env python3
"""
A small animal-story world about a thirsty animal, a guarded source, and a
careful plan that solves the problem without a fight.

Premise:
- An animal protagonist needs something from a source.
- An opponent blocks the easy path.
- The hero thinks through the problem, tries a plan, and changes the world.

Features:
- Problem Solving
- Suspense
- Inner Monologue
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
    position: str = ""
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "dog", "cat", "rabbit", "mouse", "bear", "wolf", "badger"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"bird", "squirrel", "otter", "hedgehog", "deer"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    terrain: str
    source_name: str
    source_phrase: str
    source_type: str
    source_kind: str
    source_water: str
    hidden_path: bool = False


@dataclass
class Plan:
    id: str
    clue: str
    action: str
    reason: str
    risk: str
    reveal: str
    success_condition: str


@dataclass
class StoryParams:
    setting: str
    animal: str
    opponent: str
    plan: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(
        place="the meadow",
        terrain="soft grass",
        source_name="spring",
        source_phrase="a little spring under a flat stone",
        source_type="spring",
        source_kind="water",
        source_water="clear water",
    ),
    "woods": Setting(
        place="the woods",
        terrain="pine needles",
        source_name="brook",
        source_phrase="a narrow brook behind ferns",
        source_type="brook",
        source_kind="water",
        source_water="cold water",
    ),
    "hill": Setting(
        place="the hill",
        terrain="windy rocks",
        source_name="drip",
        source_phrase="a drip of water from a mossy crack",
        source_type="drip",
        source_kind="water",
        source_water="fresh water",
        hidden_path=True,
    ),
}

ANIMALS = {
    "fox": {"type": "fox", "kind": "character", "label": "fox"},
    "rabbit": {"type": "rabbit", "kind": "character", "label": "rabbit"},
    "otter": {"type": "otter", "kind": "character", "label": "otter"},
    "mouse": {"type": "mouse", "kind": "character", "label": "mouse"},
    "squirrel": {"type": "squirrel", "kind": "character", "label": "squirrel"},
    "bird": {"type": "bird", "kind": "character", "label": "bird"},
    "hedgehog": {"type": "hedgehog", "kind": "character", "label": "hedgehog"},
}

OPPONENTS = {
    "raccoon": {
        "type": "raccoon",
        "kind": "character",
        "label": "raccoon",
        "line": "had already chosen the easy path and did not want to share",
        "goal": "keep the source for itself",
    },
    "badger": {
        "type": "badger",
        "kind": "character",
        "label": "badger",
        "line": "stood by the source with crossed paws and a sharp stare",
        "goal": "guard the source",
    },
    "crow": {
        "type": "crow",
        "kind": "character",
        "label": "crow",
        "line": "watched from above and laughed at every careful step",
        "goal": "frighten the others away",
    },
}

PLANS = {
    "bridge": Plan(
        id="bridge",
        clue="a fallen branch",
        action="move the branch over the muddy gap",
        reason="the shortcut was blocked by mud",
        risk="the branch could slip",
        reveal="it made a tiny bridge",
        success_condition="the animal could reach the source without stepping in mud",
    ),
    "wait": Plan(
        id="wait",
        clue="the opponent's shadow moved away at dusk",
        action="wait behind the reeds until the opponent looked elsewhere",
        reason="the opponent was watching the path",
        risk="the animal might stay thirsty too long",
        reveal="the path opened at the right moment",
        success_condition="the animal could slip to the source quietly",
    ),
    "trade": Plan(
        id="trade",
        clue="a bright berry patch nearby",
        action="offer berries in exchange for a turn at the source",
        reason="the opponent wanted something too",
        risk="the opponent might refuse",
        reveal="the opponent paused and listened",
        success_condition="both animals could drink one after the other",
    ),
}

ANIMAL_NAMES = ["Pip", "Milo", "Luna", "Nina", "Toby", "Bram", "Kiki", "Penny"]
OPPONENT_NAMES = ["Rook", "Moss", "Brindle", "Wisp", "Tarn"]


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------
def reasonableness_gate(setting: Setting, animal: str, opponent: str, plan: str) -> None:
    if animal == opponent:
        raise StoryError("The protagonist and opponent must be different animals.")
    if plan not in PLANS:
        raise StoryError("Unknown plan.")
    if setting.hidden_path and plan == "trade":
        raise StoryError("A trade story does not fit this hidden-path setting.")


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
def tell(setting: Setting, hero_cfg: dict, opponent_cfg: dict, plan: Plan) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_cfg["name"],
        kind="character",
        type=hero_cfg["type"],
        label=hero_cfg["label"],
        meters={"thirst": 0.0, "fear": 0.0, "hope": 0.0},
        memes={"worry": 0.0, "thinking": 0.0, "relief": 0.0},
    ))
    foe = world.add(Entity(
        id=opponent_cfg["name"],
        kind="character",
        type=opponent_cfg["type"],
        label=opponent_cfg["label"],
        meters={"guarding": 1.0},
        memes={"stubborn": 1.0},
    ))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type=setting.source_type,
        label=setting.source_name,
        phrase=setting.source_phrase,
        owner=foe.id,
        position="far edge of the clearing",
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="branch" if plan.id == "bridge" else "berries" if plan.id == "trade" else "reeds",
        label={"bridge": "a bent branch", "trade": "a handful of berries", "wait": "a patch of reeds"}[plan.id],
        phrase=plan.clue,
        owner=hero.id,
    ))

    world.say(
        f"In {setting.place}, a small {hero.label} named {hero.id} felt very thirsty."
    )
    world.say(
        f"Near {setting.source_phrase}, the water glimmered, but the {foe.label} named {foe.id} was already there."
    )
    world.say(
        f"{foe.id} {OPPONENTS[opponent_cfg['name']]['line']}."
    )
    world.say(
        f"{hero.id} looked at {setting.terrain}, then at {source.label}, and thought, "
        f"'{setting.source_water} would taste so good if I can just get close enough.'"
    )

    world.para()
    hero.meters["thirst"] += 1.0
    hero.memes["thinking"] += 1.0
    hero.memes["worry"] += 1.0
    world.say(
        f"{hero.id} wanted to drink, but the path felt risky."
    )
    world.say(
        f"'If I rush in,' {hero.pronoun('subject')} thought, 'I might get stuck, and {foe.id} will only glare harder.'"
    )
    world.say(
        f"Then {hero.id} noticed {plan.clue}."
    )
    world.say(
        f"'Maybe I can {plan.action},' {hero.pronoun('subject')} thought. 'That would solve {plan.reason}.'"
    )

    world.para()
    if plan.id == "bridge":
        world.say(
            f"{hero.id} dragged {tool.label} toward the muddy gap."
        )
        world.say(
            f"The branch wobbled once. {hero.id}'s ears went flat. 'Careful, careful,' {hero.pronoun('subject')} whispered."
        )
        world.say(
            f"At last, {tool.label} settled into place. It {plan.reveal}."
        )
        world.say(
            f"{foe.id} blinked at the little bridge, because now the source was not trapped behind the mud anymore."
        )
        hero.memes["relief"] += 1.0
    elif plan.id == "wait":
        world.say(
            f"{hero.id} slipped behind the reeds and held still."
        )
        world.say(
            f"'I can be patient,' {hero.pronoun('subject')} told {hero.pronoun('possessive')} self. 'The water will still be there if I do not panic.'"
        )
        world.say(
            f"The shadows stretched long. Then {foe.id} turned to look at the trees, and the path opened."
        )
        world.say(
            f"{plan.reveal}, and {hero.id} padded forward before anyone could stop {hero.pronoun('object')}."
        )
        hero.memes["relief"] += 1.0
    else:
        world.say(
            f"{hero.id} lifted {tool.label} and offered them to {foe.id} with a shy nod."
        )
        world.say(
            f"'I am thirsty too,' {hero.id} thought. 'Maybe sharing will work better than arguing.'"
        )
        world.say(
            f"{foe.id} paused. The berry scent was sweet, and the sharp look softened."
        )
        world.say(
            f"{foe.id} agreed to take turns, and soon both animals were near the source."
        )
        hero.memes["relief"] += 1.0

    world.para()
    world.say(
        f"In the end, {hero.id} reached {setting.source_name} and drank {setting.source_water}."
    )
    world.say(
        f"{foe.id} no longer looked like a wall in the way; {foe.id} looked like another animal at the same stream."
    )
    world.say(
        f"{hero.id} had solved the problem with a quiet idea, and the water sparkled as if it had been waiting for that very plan."
    )

    world.facts = {
        "setting": setting,
        "hero": hero,
        "opponent": foe,
        "source": source,
        "tool": tool,
        "plan": plan,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story about {f["hero"].id}, an opponent, and a source of water, with suspense and an inner monologue.',
        f"Tell a short story where {f['hero'].id} wants to reach {f['source'].label} but {f['opponent'].id} blocks the way, then solves the problem.",
        f"Write a gentle suspense story for children that includes a clever plan, a thirsty animal, and the word '{f['source'].label}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    foe = f["opponent"]
    setting = f["setting"]
    plan = f["plan"]
    source = f["source"]
    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is mainly about {hero.id}, a little {hero.label} who wanted to reach the {source.label}.",
        ),
        QAItem(
            question=f"Why was {hero.id} nervous near the source?",
            answer=f"{hero.id} was nervous because {foe.id} was guarding the way to {source.phrase}, so the path felt risky.",
        ),
        QAItem(
            question=f"What did {hero.id} think to do instead of rushing in?",
            answer=f"{hero.id} thought of a careful plan: {plan.action}. That solved {plan.reason}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} could drink at {setting.source_name}, and the opponent was no longer a hard block on the path.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting = f["setting"]
    return [
        QAItem(
            question="What is a source of water in a story like this?",
            answer="A source of water is the place where the water comes from, like a spring, brook, or little drip.",
        ),
        QAItem(
            question="What does a problem-solving animal do?",
            answer="A problem-solving animal stops to think, looks for clues, and tries a plan instead of only rushing forward.",
        ),
        QAItem(
            question="Why can suspense make a story exciting?",
            answer="Suspense makes a story exciting because the reader wonders what will happen before the problem is solved.",
        ),
        QAItem(
            question=f"What kind of place is {setting.place} in this world?",
            answer=f"{setting.place.capitalize()} is a quiet outdoor place with {setting.terrain} and a small hidden source of water.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
opponent(O) :- opponent_name(O).
plan(P) :- plan_name(P).

suspense(H,O) :- hero(H), opponent(O), H != O.
needs_solution(H,P) :- hero(H), plan(P).
can_solve(H,O,P) :- suspense(H,O), needs_solution(H,P).

valid_story(S,A,O,P) :- setting(S), animal(A), opponent(O), plan(P),
                        compatible(A,O), compatible_plan(S,P).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
        lines.append(asp.fact("hero_name", a))
    for o in OPPONENTS:
        lines.append(asp.fact("opponent_name", o))
    for p in PLANS:
        lines.append(asp.fact("plan_name", p))
    for a in ANIMALS:
        for o in OPPONENTS:
            if a != o:
                lines.append(asp.fact("compatible", a, o))
    for s in SETTINGS:
        for p in PLANS:
            if not (SETTINGS[s].hidden_path and p == "trade"):
                lines.append(asp.fact("compatible_plan", s, p))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set()
    for s in SETTINGS:
        for a in ANIMALS:
            for o in OPPONENTS:
                if a == o:
                    continue
                for p in PLANS:
                    if SETTINGS[s].hidden_path and p == "trade":
                        continue
                    py.add((s, a, o, p))
    clingo_set = set(asp_valid_stories())
    if py == clingo_set:
        print(f"OK: ASP matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in python:", sorted(py - clingo_set))
    print("only in clingo:", sorted(clingo_set - py))
    return 1


# ---------------------------------------------------------------------------
# Generation and output
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about an opponent and a source.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--opponent", choices=sorted(OPPONENTS))
    ap.add_argument("--plan", choices=sorted(PLANS))
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    animal = args.animal or rng.choice(sorted(ANIMALS))
    opponent = args.opponent or rng.choice(sorted(OPPONENTS))
    plan = args.plan or rng.choice(sorted(PLANS))
    reasonableness_gate(SETTINGS[setting], animal, opponent, plan)
    return StoryParams(setting=setting, animal=animal, opponent=opponent, plan=plan)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    hero_name = ANIMAL_NAMES[hash((params.seed, params.animal)) % len(ANIMAL_NAMES)]
    opp_name = OPPONENT_NAMES[hash((params.seed, params.opponent)) % len(OPPONENT_NAMES)]
    world = tell(setting, {"name": hero_name, **ANIMALS[params.animal]}, {"name": opp_name, **OPPONENTS[params.opponent]}, PLANS[params.plan])
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.position:
            bits.append(f"position={e.position}")
        lines.append(f"{e.id} ({e.type}): " + " ".join(bits))
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        import asp
        model = asp.one_model(asp_program())
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} valid stories:")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for s in sorted(SETTINGS):
            for a in sorted(ANIMALS):
                for o in sorted(OPPONENTS):
                    if a == o:
                        continue
                    for p in sorted(PLANS):
                        if SETTINGS[s].hidden_path and p == "trade":
                            continue
                        params = StoryParams(setting=s, animal=a, opponent=o, plan=p, seed=base_seed)
                        samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(100, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        if len(samples) > 1:
            header = f"### story {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
