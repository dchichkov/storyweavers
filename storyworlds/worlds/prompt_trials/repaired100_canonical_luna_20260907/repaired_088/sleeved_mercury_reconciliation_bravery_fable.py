#!/usr/bin/env python3
"""
A small fable storyworld about a sleeved traveler, a silver mercury bird,
reconciliation, and bravery.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    traveler_name: str
    bird_name: str
    village_name: str
    seed: Optional[int] = None
    trial_id: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Trial:
    id: str
    trouble: str
    warning: str
    false_belief: str
    brave_act: str
    exchange: str
    reconciliation: str
    lesson: str
    ending: str


TRIALS = [
    Trial(
        "broken_bridge",
        "the moon bridge cracked above a dark stream",
        "a silver feather lay beside the first broken plank",
        "the traveler believed the mercury bird had flown away in anger",
        "crossed the shaking bridge with a rope tied around one careful sleeve",
        '"I did not leave you," said the mercury bird. "I was searching for a safe crossing."',
        "the traveler apologized for accusing the bird, and the bird forgave the traveler for doubting it",
        "Bravery is not charging ahead; it is asking for help when the path trembles",
        "Together they repaired the bridge, and the mercury bird flew beside the traveler beneath the bright moon",
    ),
    Trial(
        "silent_bell",
        "the village bell stopped ringing before the harvest feast",
        "a drop of mercury trembled inside the bell rope's silver clasp",
        "the traveler believed the bird had hidden the bell's voice",
        "climbed the bell tower while the wind pulled hard at the traveler's sleeved coat",
        '"You heard my warning as a trick," said the bird. "I was trying to show you the loose clasp."',
        "the traveler admitted the mistake, and the bird helped tighten the clasp",
        "A brave heart can make room for a truth it does not wish to hear",
        "The bell rang again, and the former doubters shared warm bread beneath it",
    ),
    Trial(
        "thorn_gate",
        "a thorn gate closed the road to the village spring",
        "mercury shone on a path beneath the thorns",
        "the traveler thought the bird had led everyone into a trap",
        "held the thorns apart while the bird carried a small key through the narrow gap",
        '"Trust me for one more wingbeat," called the bird. "The key is for the spring gate."',
        "the traveler thanked the bird for its patience, and the bird accepted the thanks",
        "Reconciliation begins when blame gives way to a shared task",
        "The spring gate opened, and water glittered like mercury in the evening sun",
    ),
    Trial(
        "lost_seed",
        "the village's first planting seed vanished from its clay bowl",
        "a bright mercury trail curved toward the old stone wall",
        "the traveler believed the bird had stolen the seed for its nest",
        "searched the wall in the rain instead of hiding from the angry villagers",
        '"The trail is mine, but the seed is not," said the bird. "A mouse carried it under the wall."',
        "the traveler defended the bird, and the bird helped retrieve the seed",
        "Bravery protects the innocent even when doubt is loud",
        "The seed returned to its bowl, and the bird and traveler planted it side by side",
    ),
    Trial(
        "storm_lantern",
        "a storm extinguished the lantern that guided travelers home",
        "the mercury bird's wing flashed near a heap of wet branches",
        "the traveler thought the bird had abandoned the lantern keeper",
        "entered the windy grove with a sleeved arm shielding the last ember",
        '"I was finding dry bark," said the bird. "You mistook my search for escape."',
        "the traveler listened, apologized, and shared the ember with the bird",
        "Courage is sometimes a small flame carried carefully through bad weather",
        "The lantern glowed again, and no traveler was left outside the village gate",
    ),
]

TRIAL_BY_ID = {t.id: t for t in TRIALS}
TRAVELERS = ["Luna", "Milo", "Tara", "Niko", "Pia"]
BIRDS = ["Mercury", "Silverwing", "Shine", "Quickwing"]
VILLAGES = ["Willowmere", "Bellhollow", "Moonmead", "Hearthvale"]
MODES = ["direct", "dialogue", "warning", "quiet", "question"]
FOLLOW_THROUGHS = [
    "They made a promise to ask before making another accusation",
    "They placed a silver mark beside the repaired path",
    "They invited the whole village to hear both sides of every quarrel",
    "They kept a brave-help basket near the village gate",
]


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0x4D455243)
    text = "|".join((params.traveler_name, params.bird_name, params.village_name, params.trial_id or ""))
    return random.Random(sum((i + 1) * ord(c) for i, c in enumerate(text)))


def build_world(params: StoryParams) -> World:
    rng = _rng(params)
    trial = TRIAL_BY_ID.get(params.trial_id or "") or rng.choice(TRIALS)
    mode = params.telling_mode if params.telling_mode in MODES else rng.choice(MODES)
    traveler = Entity(
        params.traveler_name, "character", "traveler", params.traveler_name,
        meters={"courage": 1.0}, memes={"trust": 0.0, "doubt": 1.0},
    )
    bird = Entity(
        params.bird_name, "character", "mercury_bird", "the mercury bird",
        meters={"shine": 1.0}, memes={"patience": 1.0, "hope": 1.0},
    )
    village = Entity(params.village_name, "place", "village", params.village_name)
    world = World()
    world.add(traveler)
    world.add(bird)
    world.add(village)

    opening = {
        "direct": f"In {params.village_name}, {trial.trouble}.",
        "dialogue": f'"Something is wrong," said {params.traveler_name}, when {trial.trouble}.',
        "warning": f"The old bell gave a warning, for {trial.trouble}.",
        "quiet": f"At dawn, {params.village_name} was quiet because {trial.trouble}.",
        "question": f"What could a brave traveler do when {trial.trouble}?",
    }[mode]
    world.say(opening)
    world.say(f"{trial.warning.capitalize()}.")
    world.facts.update(trial=trial, mode=mode, place=params.village_name)
    world.para()

    world.say(f"{params.traveler_name} wore a long sleeved coat and looked toward {params.bird_name}.")
    world.say(f"At first, {params.traveler_name} believed that {trial.false_belief}.")
    world.say(trial.exchange)
    traveler.memes["doubt"] = 0.5
    bird.memes["patience"] += 1
    world.para()

    world.say(f"The traveler chose bravery and {trial.brave_act}.")
    traveler.meters["courage"] += 2
    traveler.memes["trust"] += 1
    world.say(f"Once they worked side by side, the true trouble became clear: {trial.trouble}.")
    world.say(f"{trial.reconciliation.capitalize()}.")
    bird.memes["hope"] += 1
    world.para()

    follow = rng.choice(FOLLOW_THROUGHS)
    world.say(f"{trial.ending}.")
    world.say(f"{follow}, and they remembered this lesson: {trial.lesson}.")
    world.facts.update(
        traveler=traveler,
        bird=bird,
        village=village,
        actual_trouble=trial.trouble,
        brave_act=trial.brave_act,
        reconciliation=trial.reconciliation,
        lesson=trial.lesson,
        follow_through=follow,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly fable set in {f['place']} where {f['trial'].trouble}.",
        f"Include {f['traveler'].id} in a sleeved coat, a mercury bird, Bravery, and Reconciliation.",
        f"Show how the characters move from doubt to trust through this brave act: {f['brave_act']}. End with a concrete peaceful image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            f"What trouble came to {f['place']}?",
            f"The trouble was that {f['actual_trouble']}. This danger disturbed the village and required careful help.",
        ),
        QAItem(
            f"Why did {f['traveler'].id} doubt the mercury bird?",
            f"{f['traveler'].id} first believed that {f['trial'].false_belief}. The belief was mistaken because the bird was trying to help.",
        ),
        QAItem(
            "How did bravery change the story?",
            f"Bravery led the traveler to {f['brave_act']}. That action revealed the truth instead of allowing fear to guide the decision.",
        ),
        QAItem(
            "How did reconciliation happen?",
            f"{f['reconciliation'].capitalize()}. The two friends repaired their trust by listening and working together.",
        ),
        QAItem(
            "What lesson did the fable teach?",
            f"The fable taught that {f['lesson'].lower()}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is bravery?", "Bravery is choosing a helpful or right action even when something feels frightening."),
        QAItem("What is reconciliation?", "Reconciliation is the making of peace after people have hurt, blamed, or misunderstood one another."),
        QAItem("What is mercury?", "Mercury is a shiny, silver-colored metal; in this fable it also names a bright magical bird."),
        QAItem("What does sleeved mean?", "Sleeved means covered or fitted with sleeves, such as a sleeved coat."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.type} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  solved={world.facts.get('solved')}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "village"),
        asp.fact("material", "sleeved"),
        asp.fact("material", "mercury"),
        asp.fact("virtue", "bravery"),
        asp.fact("virtue", "reconciliation"),
        asp.fact("action", "listen"),
        asp.fact("action", "help"),
        asp.fact("action", "repair"),
    ])


ASP_RULES = r"""
has_story_tools :- material(sleeved), material(mercury).
has_virtues :- virtue(bravery), virtue(reconciliation).
has_turn :- action(listen), action(help).
has_ending :- action(repair).
valid_story :- setting(village), has_story_tools, has_virtues, has_turn, has_ending.
#show valid_story/0.
"""


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    valid = any(sym.name == "valid_story" for sym in model)
    if not valid:
        print("MISMATCH: ASP twin rejected the storyworld.")
        return 1
    sample = generate(StoryParams("Luna", "Mercury", "Willowmere", seed=88, trial_id="broken_bridge"))
    if not sample.story or "brave" not in sample.story.lower() or "mercury" not in sample.story.lower():
        print("MISMATCH: generated story failed the content gate.")
        return 1
    print("OK: ASP twin and generated story agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A fable storyworld of mercury, bravery, and reconciliation.")
    parser.add_argument("--name")
    parser.add_argument("--bird")
    parser.add_argument("--village")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        traveler_name=args.name or rng.choice(TRAVELERS),
        bird_name=args.bird or rng.choice(BIRDS),
        village_name=args.village or rng.choice(VILLAGES),
        trial_id=rng.choice(TRIALS).id,
        telling_mode=rng.choice(MODES),
    )


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


CURATED = [
    StoryParams("Luna", "Mercury", "Willowmere", trial_id="broken_bridge", telling_mode="dialogue"),
    StoryParams("Milo", "Silverwing", "Bellhollow", trial_id="silent_bell", telling_mode="warning"),
    StoryParams("Tara", "Shine", "Moonmead", trial_id="thorn_gate", telling_mode="direct"),
    StoryParams("Niko", "Quickwing", "Hearthvale", trial_id="lost_seed", telling_mode="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
