#!/usr/bin/env python3
"""
storyworlds/worlds/desperate_manipulate_moo_moral_value_rhyme_dialogue.py
=========================================================================

A small pirate-tale storyworld about a desperate deckhand, a crafty trick,
and a moody cow on a ship. The premise is deliberately tiny and classical:
someone wants a prize, someone tries to manipulate the moment, the cow says
"moo," and the crew learns a moral value before the tide turns.

This world includes:
- desperate
- manipulate
- moo
- moral value
- rhyme
- dialogue

The simulation keeps state in meters and memes:
- meters model physical things: rope, crate, lantern, tide, milk, etc.
- memes model emotional/social things: desperation, trust, guilt, pride, delight

The plot arc is:
1) Setup: a pirate crew on a small ship, with a cow and a shared goal.
2) Tension: one character tries to manipulate another with a rhyming bargain.
3) Turn: the lie is noticed, the cow's "moo" interrupts the scheme.
4) Resolution: honesty wins, the moral value is stated in a child-friendly way.

The story is intentionally narrow so that every generated sample reads as a
complete tiny tale rather than a loose event log.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"pirate", "captain", "sailor", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little ship"
    setting_detail: str = "a salty little ship with a creaky mast"
    affords: set[str] = field(default_factory=lambda: {"milk", "sing", "sail"})


@dataclass
class Goal:
    id: str
    label: str
    prize: str
    risk: str
    moral_value: str
    rhyme_line: str
    dialogue_offer: str
    dialogue_refusal: str
    dialogue_truth: str


@dataclass
class StoryParams:
    goal: str
    hero_name: str
    hero_type: str
    hero_trait: str
    trickster_name: str
    trickster_type: str
    trickster_trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


GOALS = {
    "milk": Goal(
        id="milk",
        label="milk pail",
        prize="a pail of milk for the crew's supper",
        risk="spill the milk",
        moral_value="Honesty is better than a sneaky trick.",
        rhyme_line="A lie may fly, but truth stays nigh.",
        dialogue_offer="If you let me have the pail, I'll sing you a shiny rhyme.",
        dialogue_refusal="That sounds too sly for a tidy sky.",
        dialogue_truth="I was trying to manipulate you, and that was wrong.",
    ),
    "lantern": Goal(
        id="lantern",
        label="lantern oil",
        prize="lantern oil to light the deck at night",
        risk="tip the oil",
        moral_value="A good plan should not be built on a lie.",
        rhyme_line="A clever scheme can lose its gleam.",
        dialogue_offer="Trade me the oil and I'll make a rhyme so fine it will sparkle.",
        dialogue_refusal="Your rhyme is bright, but your plan feels light.",
        dialogue_truth="I tried to manipulate the crew, but I should have asked honestly.",
    ),
    "rope": Goal(
        id="rope",
        label="rope coil",
        prize="a strong rope coil for the mast",
        risk="tangle the rope",
        moral_value="Being fair keeps friends close.",
        rhyme_line="A greedy grin can sink within.",
        dialogue_offer="Let me keep the rope, and I'll tell a joke that rhymes.",
        dialogue_refusal="No trick can stick when the answer is quick.",
        dialogue_truth="I wanted to manipulate the outcome, but I should have shared.",
    ),
}


HERO_TYPES = ["pirate", "sailor", "deckhand"]
TRAITS = ["brave", "small", "curious", "cheerful", "stubborn", "restless"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny pirate tale storyworld with moral value, rhyme, and dialogue.")
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--name")
    ap.add_argument("--trickster")
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
    goal = args.goal or rng.choice(list(GOALS))
    hero_name = args.name or rng.choice(["Finn", "Mira", "Jory", "Pip", "Nell", "Bram"])
    trickster = args.trickster or rng.choice(["Captain Reed", "Old Salt", "Maggie", "Torn Jack"])
    return StoryParams(
        goal=goal,
        hero_name=hero_name,
        hero_type=rng.choice(HERO_TYPES),
        hero_trait=rng.choice(TRAITS),
        trickster_name=trickster,
        trickster_type=rng.choice(["pirate", "captain", "sailor"]),
        trickster_trait=rng.choice(["sly", "shifty", "smooth-talking", "greedy"]),
        seed=args.seed,
    )


def _speak(entity: Entity, text: str) -> str:
    return text.replace("{he}", entity.pronoun()).replace("{his}", entity.pronoun("possessive")).replace("{him}", entity.pronoun("object"))


def introduce(world: World, hero: Entity, trickster: Entity, goal: Goal) -> None:
    world.say(f"{hero.id} was a {hero.meters.get('size_word', 0) and 'tiny' or 'little'} {hero.type} with a {hero.memes.get('trait_mark', 0) or ''} heart.".replace("  ", " ").replace(" .", "."))
    world.say(f"On {world.setting.place}, {hero.id} and {trickster.id} both wanted {goal.prize}.")
    world.say(f"The ship was {world.setting.setting_detail}, and a cow named Mabel stood near the rail.")
    world.say(f"Mabel gave a long {goal.id == 'milk' and 'moo' or 'moo'} from the deck, as if she knew a tale was coming.")


def setup_conflict(world: World, hero: Entity, trickster: Entity, goal: Goal) -> None:
    hero.memes["want"] = 1
    hero.memes["desperate"] = 1
    trickster.memes["greed"] = 1
    world.say(f"{hero.id} became desperate because {goal.prize} would help the crew.")
    world.say(f"{trickster.id} leaned close and tried to manipulate {hero.id} with a rhyme.")
    world.say(f'"{goal.dialogue_offer}" {trickster.id} said.')
    world.say(f'"{goal.rhyme_line}" {hero.id} muttered back, not trusting the smooth words."')


def escalate(world: World, hero: Entity, trickster: Entity, goal: Goal) -> None:
    world.para()
    world.say(f'"{goal.dialogue_refusal}" {hero.id} said.')
    world.say(f"{trickster.id} kept pressing, but the lie sounded too shiny.")
    world.say(f'Mabel the cow stamped once and said, "Moo!"')


def resolve(world: World, hero: Entity, trickster: Entity, goal: Goal) -> None:
    world.para()
    hero.memes["trust"] = 1
    trickster.memes["guilt"] = 1
    world.say(f"At last {trickster.id} looked down and spoke plainly.")
    world.say(f'"{goal.dialogue_truth}" {trickster.id} said.')
    world.say(f"{hero.id} nodded, and the crew chose the fair way.")
    world.say(f"They shared the {goal.label}, and nobody had to keep a sneaky secret.")
    world.say(f"{goal.moral_value} The little ship sailed on with Mabel's gentle moo behind them.")


def tell_story(params: StoryParams) -> World:
    world = World(Setting())
    goal = GOALS[params.goal]
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, meters={}, memes={}))
    trickster = world.add(Entity(id=params.trickster_name, kind="character", type=params.trickster_type, meters={}, memes={}))
    world.facts.update(goal=goal, hero=hero, trickster=trickster)
    introduce(world, hero, trickster, goal)
    setup_conflict(world, hero, trickster, goal)
    escalate(world, hero, trickster, goal)
    resolve(world, hero, trickster, goal)
    return world


def generation_prompts(world: World) -> list[str]:
    goal: Goal = world.facts["goal"]
    hero: Entity = world.facts["hero"]
    trickster: Entity = world.facts["trickster"]
    return [
        f'Write a pirate tale for a young child about {hero.id}, a desperate deckhand, and a trick about {goal.label}.',
        f'Write a short story with dialogue and a rhyme where {trickster.id} tries to manipulate {hero.id} on a ship, but truth wins.',
        f'Create a gentle pirate story that includes the word "moo" and ends with a moral value.',
    ]


def story_qa(world: World) -> list[QAItem]:
    goal: Goal = world.facts["goal"]
    hero: Entity = world.facts["hero"]
    trickster: Entity = world.facts["trickster"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {hero.type} who became desperate over {goal.prize}, and {trickster.id}, who tried to manipulate the choice.",
        ),
        QAItem(
            question=f"What did the trickster try to do?",
            answer=f"{trickster.id} tried to manipulate {hero.id} with a rhyming promise so {trickster.pronoun('subject')} could keep {goal.label}.",
        ),
        QAItem(
            question=f"What sound did the cow make?",
            answer="Mabel the cow said, 'Moo!' when the sneaky plan started to wobble.",
        ),
        QAItem(
            question=f"What lesson did the crew learn?",
            answer=goal.moral_value,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a rhyme?", answer="A rhyme is when words sound alike at the end, like light and night."),
        QAItem(question="Why should people be honest?", answer="Being honest helps people trust each other and make fair choices."),
        QAItem(question="What does a cow say?", answer="A cow says moo."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: type={e.type} kind={e.kind} memes={dict(e.memes)} meters={dict(e.meters)}")
    return "\n".join(out)


ASP_RULES = r"""
% Tiny declarative twin: a story is reasonable if a character is desperate,
% another tries to manipulate, and a cow says moo before the moral is stated.
desperate(H) :- hero(H), wants_prize(H), not calm(H).
manipulates(T, H) :- trickster(T), hero(H), says_offer(T).
moo_event :- cow(C), says_moo(C).
moral_turn :- desperate(H), manipulates(T, H), moo_event.
complete_story :- moral_turn.
#show complete_story/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "hero"),
        asp.fact("trickster", "trickster"),
        asp.fact("cow", "mabel"),
        asp.fact("wants_prize", "hero"),
        asp.fact("says_offer", "trickster"),
        asp.fact("says_moo", "mabel"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show complete_story/0."))
    ok = any(sym.name == "complete_story" for sym in model)
    if ok:
        print("OK: ASP twin produces a complete story model.")
        return 0
    print("MISMATCH: ASP twin did not produce complete_story.")
    return 1


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(goal="milk", hero_name="Finn", hero_type="deckhand", hero_trait="brave", trickster_name="Captain Reed", trickster_type="captain", trickster_trait="sly"),
        StoryParams(goal="lantern", hero_name="Mira", hero_type="pirate", hero_trait="curious", trickster_name="Old Salt", trickster_type="sailor", trickster_trait="shifty"),
        StoryParams(goal="rope", hero_name="Pip", hero_type="sailor", hero_trait="restless", trickster_name="Maggie", trickster_type="pirate", trickster_trait="smooth-talking"),
    ]


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show complete_story/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in build_curated():
            samples.append(generate(p))
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_story_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in {s.story for s in samples}:
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
