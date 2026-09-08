#!/usr/bin/env python3
"""
A small mythic storyworld about a calzone, a twentieth bell, and a lesson
learned through gentle humor.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
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
    facts: dict[str, object] = field(default_factory=dict)
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
    hero_name: str
    helper_name: str
    deity_name: str
    seed: Optional[int] = None
    trial_id: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Trial:
    id: str
    omen: str
    mistake: str
    funny_sign: str
    test: str
    revelation: str
    lesson: str
    repair: str
    ending: str


HERO_NAMES = ["Luna", "Mara", "Theo", "Pia", "Niko", "Suri"]
HELPER_NAMES = ["Bram", "Tavi", "Mina", "Oren", "Kiri"]
DEITY_NAMES = ["the Hearth Moon", "the Laughing Oven", "the Old Olive Tree", "the Star Baker"]
TELLING_MODES = ["omen_first", "dialogue_first", "bell_countdown", "quiet_myth", "question_open"]

TRIALS = [
    Trial(
        id="moon_cheese",
        omen="On the twentieth night of summer, the moon wore a golden ring",
        mistake="Luna placed a calzone meant for the village feast on the altar of the Hearth Moon",
        funny_sign="the calzone answered every prayer with a loud, buttery burp",
        test="Luna tried to bow solemnly, but the calzone rolled away and bumped the sacred drum",
        revelation="the priestess noticed that the feast basket, not the altar, was empty",
        lesson="a beautiful sign is not always a command, and hungry neighbors should be checked before grand guesses",
        repair="Luna carried the calzone to the feast and baked a fresh round for the altar",
        ending="At midnight, the moon ring faded, while twenty guests laughed around the properly placed calzone",
    ),
    Trial(
        id="talking_crust",
        omen="At the twentieth bell, the village oven began to whisper through its chimney",
        mistake="Luna believed the whisper named her as the chosen guardian of the royal calzone",
        funny_sign="each grand whisper ended with a tiny sneeze of flour",
        test="She announced her destiny, but the oven replied by puffing flour into her eyebrows",
        revelation="the helper found a loose vent flap tapping against the chimney",
        lesson="before trusting a mysterious voice, listen for ordinary causes and ask a friend to look with you",
        repair="Luna fixed the vent and shared the warm calzone with the oven keeper",
        ending="The twentieth bell rang clearly, and Luna's floury eyebrows became the village's favorite crown",
    ),
    Trial(
        id="olive_oracle",
        omen="Twenty olive stones formed a perfect circle around a cooling calzone",
        mistake="Luna thought the circle meant she must guard the calzone alone",
        funny_sign="whenever she turned her back, one olive stone wore her tiny shoe",
        test="She blamed a mountain spirit, until her own shoe slid out from behind the basket",
        revelation="the stones had been moved by children making a game while waiting for supper",
        lesson="a mystery can be playful rather than dangerous, and sharing a puzzle is wiser than guarding it in fear",
        repair="Luna invited the children to finish the circle and divided the calzone into twenty pieces",
        ending="The stones became game counters, and every child received a warm piece beneath the patient stars",
    ),
    Trial(
        id="golden_fold",
        omen="The twentieth fold in the baker's cloth shone like a small sunrise",
        mistake="Luna assumed the shine proved that her calzone was too important to touch",
        funny_sign="the sacred shine appeared only when someone lifted a greasy spoon",
        test="She called for silence, but Bram's stomach growled louder than the temple bell",
        revelation="the shine was sunlight bouncing from a spoon hidden in the cloth",
        lesson="importance should be tested with care, because a dazzling sign may have a simple explanation",
        repair="Luna cleaned the spoon, unfolded the cloth, and served the calzone before it grew cold",
        ending="The sunrise-colored cloth covered the table, where even the grandest myth made room for supper",
    ),
]

TRIAL_BY_ID = {trial.id: trial for trial in TRIALS}


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xC47A20)
    text = "|".join((params.hero_name, params.helper_name, params.deity_name, params.trial_id or ""))
    return random.Random(sum((i + 1) * ord(c) for i, c in enumerate(text)))


def _opening(mode: str, hero: str, trial: Trial) -> str:
    openings = {
        "omen_first": f"On the twentieth night, {trial.omen.lower()}.",
        "dialogue_first": f'"Something important is happening," {hero} whispered, for {trial.omen.lower()}.',
        "bell_countdown": f"At the twentieth bell, the old myth began: {trial.omen.lower()}.",
        "quiet_myth": f"The village was quiet until {trial.omen.lower()}.",
        "question_open": f"What could {hero} do when {trial.omen.lower()}?",
    }
    return openings[mode]


def build_world(params: StoryParams) -> World:
    rng = _rng(params)
    trial = TRIAL_BY_ID.get(params.trial_id or "")
    if trial is None:
        trial = rng.choice(TRIALS)
    mode = params.telling_mode if params.telling_mode in TELLING_MODES else rng.choice(TELLING_MODES)

    world = World()
    hero = world.add(Entity(params.hero_name, "character", "child", params.hero_name))
    helper = world.add(Entity(params.helper_name, "character", "helper", params.helper_name))
    deity = world.add(Entity("deity", "spirit", "deity", params.deity_name))
    calzone = world.add(Entity("calzone", "thing", "food", "calzone"))
    bell = world.add(Entity("bell", "thing", "bell", "twentieth bell"))

    hero.memes.update(courage=1.0, certainty=1.0)
    helper.memes.update(wisdom=1.0, humor=1.0)
    deity.memes["patience"] = 1.0
    calzone.meters.update(warmth=1.0, fullness=1.0)
    bell.meters["count"] = 20.0

    world.say(_opening(mode, hero.id, trial))
    world.say(f"The sign seemed to point toward a single golden calzone, and {trial.mistake}.")
    world.facts.update(trial=trial, mode=mode, hero=hero, helper=helper, deity=deity, calzone=calzone, bell=bell)

    world.para()
    world.say(f'"The gods have chosen this calzone!" {hero.id} cried.')
    world.say(f'"Perhaps," said {helper.id}, "but let us ask why {trial.funny_sign}."')
    world.say(f"{trial.funny_sign.capitalize()}. The solemn villagers tried not to laugh, which made their cheeks wobble.")
    hero.memes["certainty"] += 1.0
    helper.memes["humor"] += 1.0

    world.para()
    world.say(f"{hero.id} attempted a grand test: {trial.test}.")
    world.say(f"The joke loosened the fear in the air, and the two friends examined the evidence together.")
    world.say(f"Then they discovered the truth: {trial.revelation}.")
    hero.memes["curiosity"] = 1.0
    helper.memes["guidance"] = 1.0
    world.facts["revelation"] = trial.revelation

    world.para()
    world.say(f"{hero.id} lowered their voice and learned that {trial.lesson}.")
    world.say(f'"A myth should teach us how to see," said {helper.id}. "It should not stop us from seeing."')
    world.say(f"{trial.repair}.")
    calzone.meters["warmth"] = 2.0
    calzone.meters["shared"] = 1.0
    hero.memes["humility"] = 1.0
    helper.memes["trust"] = 1.0

    world.say(f"{trial.ending}.")
    world.say(f"The village remembered the lesson, and it remembered the humor too: wisdom is easier to carry when it makes room for a laugh.")
    world.facts.update(
        lesson=trial.lesson,
        repair=trial.repair,
        ending=trial.ending,
        solved=True,
        twentieth=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    trial: Trial = f["trial"]
    return [
        f"Write a child-friendly myth about {f['hero'].id}, a calzone, and the twentieth bell.",
        f"Include gentle humor when {trial.funny_sign}, then let {f['hero'].id} and {f['helper'].id} discover the truth.",
        f"End with the Lesson Learned that {trial.lesson}, followed by a concrete shared feast.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    trial: Trial = f["trial"]
    return [
        QAItem(
            question=f"What happened on the twentieth night or bell?",
            answer=f"The myth began when {trial.omen.lower()}. This made the calzone seem like part of a grand omen.",
        ),
        QAItem(
            question=f"Why did {f['hero'].id} become confused?",
            answer=f"{f['hero'].id} mistook the omen for a command and believed that {trial.mistake.lower()}.",
        ),
        QAItem(
            question="What made the story humorous?",
            answer=f"The humor came from the ordinary, funny detail that {trial.funny_sign}. It helped everyone relax enough to investigate.",
        ),
        QAItem(
            question="How was the mystery explained?",
            answer=f"The friends found that {trial.revelation}. The evidence showed that the strange sign had a simple cause.",
        ),
        QAItem(
            question="What Lesson Learned did the myth teach?",
            answer=f"It taught that {trial.lesson}. The lesson mattered because it changed what the hero did next.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a calzone?",
            answer="A calzone is a folded piece of dough filled with ingredients and baked until warm.",
        ),
        QAItem(
            question="What does twentieth mean?",
            answer="Twentieth means coming after nineteen and before twenty-one in an ordered list.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is a traditional story that may use marvelous events to explain an idea or teach a lesson.",
        ),
        QAItem(
            question="Why can humor help during a problem?",
            answer="Humor can soften fear and help people think clearly, especially when they still take the problem seriously.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.type} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: solved={world.facts.get('solved')} twentieth={world.facts.get('twentieth')}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "mythic_village"),
            asp.fact("object", "calzone"),
            asp.fact("ordinal", "twentieth"),
            asp.fact("feature", "humor"),
            asp.fact("feature", "lesson_learned"),
            asp.fact("action", "question_omen"),
            asp.fact("action", "share_food"),
            asp.fact("action", "learn"),
        ]
    )


ASP_RULES = r"""
myth_present :- setting(mythic_village), object(calzone), ordinal(twentieth).
humor_present :- feature(humor), action(question_omen).
lesson_learned :- feature(lesson_learned), action(learn).
shared_resolution :- action(share_food), myth_present.
valid_story :- myth_present, humor_present, lesson_learned, shared_resolution.
#show valid_story/0.
"""


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    valid = any(symbol.name == "valid_story" for symbol in model)
    if not valid:
        print("MISMATCH: ASP twin did not confirm validity.")
        return 1
    for seed in range(3):
        params = StoryParams("Luna", "Bram", "the Hearth Moon", seed=seed)
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("solved"):
            print("MISMATCH: generated story was not solved.")
            return 1
    print("OK: ASP twin confirms the mythic storyworld.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mythic calzone storyworld.")
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--deity")
    parser.add_argument("--trial")
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
    if args.trial and args.trial not in TRIAL_BY_ID:
        raise StoryError(f"Unknown trial '{args.trial}'. Choose one of: {', '.join(TRIAL_BY_ID)}.")
    return StoryParams(
        hero_name=args.name or rng.choice(HERO_NAMES),
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        deity_name=args.deity or rng.choice(DEITY_NAMES),
        trial_id=args.trial or rng.choice(TRIALS).id,
        telling_mode=rng.choice(TELLING_MODES),
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
    StoryParams("Luna", "Bram", "the Hearth Moon", trial_id="moon_cheese"),
    StoryParams("Mara", "Tavi", "the Laughing Oven", trial_id="talking_crust"),
    StoryParams("Theo", "Mina", "the Old Olive Tree", trial_id="olive_oracle"),
    StoryParams("Pia", "Oren", "the Star Baker", trial_id="golden_fold"),
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
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
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
