#!/usr/bin/env python3
"""
A small mythic storyworld about Luna, a shard of shale, and a remembered promise.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    companion: str
    mountain: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trial:
    name: str
    danger: str
    memory: str
    clue: str
    choice: str
    truth: str
    repair: str
    ending: str
    lesson: str


NAMES = ["Luna", "Mira", "Nia", "Tala", "Iris"]
COMPANIONS = ["fox", "raven", "goat", "hare", "little bear"]
MOUNTAINS = ["the blue mountain", "the sleeping ridge", "the mountain of seven stones"]

TRIALS = [
    Trial(
        "the silent bridge",
        "a narrow bridge of shale cracked above a deep ravine",
        "Long ago, Luna's grandmother had touched a shale bridge and waited for the mountain to stop trembling",
        "three flat shale pieces formed a safer path beside the broken span",
        "to test each stone with a staff instead of rushing across",
        "the mountain was not angry; it was warning travelers to use the older path",
        "laid the loose stones firmly and marked the safe crossing with white pebbles",
        "the ravine filled with gold evening light, and the shale path shone like a quiet staircase",
        "Courage listens before it leaps.",
    ),
    Trial(
        "the thirsty spring",
        "the spring had vanished beneath a slide of sharp shale",
        "In a flashback, Luna remembered an elder saying that water remembers the shape of a patient hand",
        "a cool breath rose from a crack where dark shale met pale clay",
        "to clear the stones gently and leave room for the water to choose its way",
        "the spring had been covered, not lost, and the mountain still held its promise",
        "moved the smallest stones, built a little channel, and protected the spring with a ring of shale",
        "water sang through the valley while Luna rested her chin on her hands and listened",
        "Care can uncover what force would break.",
    ),
    Trial(
        "the echoing gate",
        "a stone gate would not open, though its shale lintel trembled",
        "Luna flashed back to a childhood lesson: a gate that answers an honest word is older than any king",
        "the lintel bore a tiny mark shaped like a crescent chin",
        "to speak the promise she had once made to protect travelers",
        "the gate opened because the mountain recognized the promise, not because Luna was strong",
        "she repaired the fallen marker and invited her companion through first",
        "moonlight poured across the threshold, and the old gate welcomed them without a groan",
        "A promise becomes a key when it is kept.",
    ),
    Trial(
        "the sleeping giant",
        "a giant-shaped hill blocked the trail, covered in warm gray shale",
        "A flashback returned: as a small child, Luna had seen her mother place a hand beneath her chin and say, 'Notice what is sleeping'",
        "the shale flakes moved in a slow rhythm like breathing",
        "to lower her voice, study the rhythm, and guide the travelers around the hill",
        "the giant was only a sleeping mountain spirit, and loud footsteps would have woken it",
        "she gathered scattered shale into a crescent boundary so no one would disturb the spirit",
        "the spirit dreamed beneath the hill while stars gathered over Luna's careful path",
        "Wisdom protects even what cannot speak.",
    ),
]


def tell_story(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    trial = TRIALS[rng.randrange(len(TRIALS))]
    world = World(place=params.mountain)
    child = world.add(Entity(params.name, "character", "child"))
    companion = world.add(Entity(params.companion, "character", params.companion))
    shale = world.add(Entity("shale", "thing", "shale", "gray shale"))
    chin = world.add(Entity("chin", "thing", "chin", "thoughtful chin"))

    world.say(
        f"At the foot of {params.mountain}, {params.name} walked beneath a sky pale as a silver bowl. "
        f"{params.companion.capitalize()} trotted beside {params.name}, and a small shard of shale rested in "
        f"{params.name}'s pocket like a piece of the mountain's old memory."
    )
    world.say(
        f"The trail led to {trial.danger}. A wind touched {params.name}'s chin, and suddenly a flashback "
        f"opened in the mind: {trial.memory}."
    )
    world.say(
        f'"The mountain is speaking in small signs," {params.name} said. '
        f'"Can you hear it?" {params.companion.capitalize()} asked. '
        f'"I can hear enough to be careful," {params.name} answered.'
    )

    world.para()
    world.say(
        f"At first, {params.name} wanted to turn back. Then {params.name} noticed that {trial.clue}. "
        f"The shard of shale in the pocket grew warm, as if the ancient stone remembered the same lesson."
    )
    world.say(
        f'"Should we hurry before darkness comes?" asked {params.companion.capitalize()}. '
        f'"No. We will choose the path that lets everyone return," said {params.name}.'
    )
    world.say(f"{params.name} decided {trial.choice}.")
    world.say(
        f"The choice changed the trail. What looked like a threat became a message: {trial.truth}."
    )

    world.para()
    world.say(f"Together, {params.name} and {params.companion} {trial.repair}.")
    child.memes["wisdom"] = 1.0
    child.memes["courage"] = 1.0
    companion.memes["trust"] = 1.0
    shale.meters["understood"] = 1.0
    chin.meters["thoughtful"] = 1.0
    world.say(
        f"The mountain grew quiet. {params.name} touched a hand to {params.name}'s chin and remembered "
        f"that old flashback not as a warning of fear, but as a gift of understanding."
    )
    world.say(f"{trial.ending}. {trial.lesson}")

    world.facts.update(
        child=child,
        companion=companion,
        shale=shale,
        chin=chin,
        trial=trial,
        place=world.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    trial: Trial = world.facts["trial"]
    child: Entity = world.facts["child"]
    return [
        f"Write a mythic story about {child.id}, shale, and a flashback that reveals how to solve {trial.name}.",
        f"Tell a gentle mountain myth in which {child.id} uses patience instead of force.",
        f"Write a child-facing tale where a remembered promise changes the hero's choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    companion: Entity = f["companion"]
    trial: Trial = f["trial"]
    return [
        QAItem(
            question=f"What danger did {child.id} discover?",
            answer=f"{child.id} discovered that {trial.danger}.",
        ),
        QAItem(
            question=f"What did the flashback help {child.id} remember?",
            answer=f"The flashback helped {child.id} remember that {trial.memory}.",
        ),
        QAItem(
            question=f"What clue changed {child.id}'s decision?",
            answer=f"The clue was that {trial.clue}. It showed that the mountain was giving a careful warning.",
        ),
        QAItem(
            question=f"How did {child.id} and {companion.id} solve the problem?",
            answer=f"They {trial.repair}. Their patient action revealed that {trial.truth}.",
        ),
        QAItem(
            question=f"What did {child.id} learn?",
            answer=f"{child.id} learned that {trial.lesson}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is shale?",
            answer="Shale is a layered rock that can split into thin, flat pieces.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene that returns to an earlier time so a character or reader can understand something important.",
        ),
        QAItem(
            question="Why can a myth use a mountain as a character?",
            answer="A myth can give a mountain a voice, memory, or spirit to explore ideas about nature, courage, and responsibility.",
        ),
        QAItem(
            question="Why did the character touch their chin?",
            answer="Touching the chin showed thoughtful attention before making a careful decision.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    return "\n".join(lines)


ASP_RULES = r"""
safe_path :- patient_choice, clue_seen.
truth_found :- safe_path, memory_recalled.
happy_ending :- truth_found, repaired.
#show safe_path/0.
#show truth_found/0.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("patient_choice"),
            asp.fact("clue_seen"),
            asp.fact("memory_recalled"),
            asp.fact("repaired"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/0."))
    if asp.atoms(model, "happy_ending"):
        params = StoryParams("Luna", "fox", "the blue mountain", 1)
        sample = generate(params)
        if sample.story and "shale" in sample.story and "chin" in sample.story:
            print("OK: ASP and Python agree on the repaired mythic ending.")
            return 0
    print("MISMATCH: the mythic ending could not be verified.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic flashback story about shale and a thoughtful chin.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--mountain", choices=MOUNTAINS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        mountain=args.mountain or rng.choice(MOUNTAINS),
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.type:10}) meters={meters} memes={memes}"
        )
    return "\n".join(lines)


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
    StoryParams("Luna", "fox", "the blue mountain", 101),
    StoryParams("Mira", "raven", "the sleeping ridge", 102),
    StoryParams("Nia", "hare", "the mountain of seven stones", 103),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_path/0. #show truth_found/0. #show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(
            asp_program("#show safe_path/0. #show truth_found/0. #show happy_ending/0.")
        )
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
