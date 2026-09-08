#!/usr/bin/env python3
"""
A small fable world about a hypothetical hippo succession and a magical
transformation.

A young hippo must learn that succession is not about taking a crown. Magic
transforms the crown into a promise when the heir listens, helps, and serves.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break
from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
hypothetical_case(H) :- hippo(H), imagines(H, succession).
magic_ready(H) :- hippo(H), listens(H), helps(H).
transformed_crown(H) :- magic_ready(H), accepts_duty(H).
wise_heir(H) :- transformed_crown(H), shares(H).
good_succession(H) :- wise_heir(H).
"""

HIPPO_NAMES = ["Luna", "Boma", "Nala", "Tavi", "Momo", "Paka"]
ELDER_NAMES = ["Grandmother Sefu", "Old Kito", "Auntie Rani", "Elder Duma"]
PLACES = ["the silver marsh", "the lily lagoon", "the reed valley", "the moonlit pool"]
TREASURES = ["a blue water-lily", "a shell bell", "a golden reed", "a moonstone"]
LESSONS = [
    "A crown is light when it is shared and heavy when it is hoarded.",
    "The best successor learns to carry a community before carrying a crown.",
    "Magic may change a crown, but kindness decides what it means.",
    "A leader grows large by making room for others.",
]


@dataclass(frozen=True)
class Trial:
    title: str
    premise: str
    worry: str
    temptation: str
    clue: str
    action: str
    transformation: str
    result: str
    lesson: str
    ending: str


TRIALS = [
    Trial(
        title="the disappearing crown",
        premise="The old crown floated away each dawn, although it returned each evening to the palace stone.",
        worry="the crown was testing whether its next keeper wanted glory more than duty",
        temptation="chase it through the reeds and seize it before anyone else could touch it",
        clue="the crown always drifted toward the smallest thirsty puddle",
        action="followed the crown quietly and helped the little animals fill their puddles first",
        transformation="the crown changed from shining gold into a cool ring of woven water grass",
        result="Luna could wear it only while remembering the creatures who depended on the marsh",
        lesson="A crown is light when it is shared and heavy when it is hoarded.",
        ending="At sunset, the grass crown rested gently on Luna's head while frogs sang beside full puddles.",
    ),
    Trial(
        title="the echoing throne",
        premise="During the planned succession, the stone throne began repeating every boast spoken near it.",
        worry="the throne would choose an heir who could listen instead of one who could merely speak",
        temptation="shout the loudest promise and make the throne echo it all day",
        clue="the throne became quiet whenever a small voice was allowed to finish",
        action="invited the youngest animals to speak and listened until each worry had an answer",
        transformation="the throne softened into a round bench with room for many bodies",
        result="the new leader sat among the marsh animals rather than above them",
        lesson="The best successor learns to carry a community before carrying a crown.",
        ending="The broad bench warmed in the sun, and no voice had to shout to be heard.",
    ),
    Trial(
        title="the backwards river",
        premise="On succession day, the river flowed backward and carried every royal object toward the hills.",
        worry="the magic was asking whether the heir would protect symbols or protect the living marsh",
        temptation="save the jeweled staff before the nests and boats along the bank",
        clue="the river slowed whenever someone rescued a neighbor before a treasure",
        action="helped birds, turtles, and fish reach safe water before retrieving the staff",
        transformation="the jeweled staff became a strong bridge rail for the whole community",
        result="the crossing became safer, and the heir understood that authority should connect rather than command",
        lesson="Magic may change a crown, but kindness decides what it means.",
        ending="The river flowed forward again beneath the new bridge, bright with morning light.",
    ),
    Trial(
        title="the silent royal drum",
        premise="The drum that announced the next ruler made no sound when the elders struck it.",
        worry="the drum was waiting for a promise proved by action rather than polished words",
        temptation="decorate the drum and pretend its silence meant approval",
        clue="it gave one soft beat whenever someone repaired a broken path",
        action="worked beside the marsh animals to mend paths, clear reeds, and share dry resting places",
        transformation="the drum turned into a warm wooden table for common meals",
        result="the succession became a gathering where every helper had a place",
        lesson="A leader grows large by making room for others.",
        ending="Steam rose from shared soup as the transformed drum stood at the center of the feast.",
    ),
    Trial(
        title="the mirror of crowns",
        premise="A magic mirror showed every possible future heir wearing a different crown.",
        worry="a hypothetical future could distract the hippos from the needs of today",
        temptation="choose the most splendid reflection and copy its proudest pose",
        clue="the mirror brightened only when the viewer noticed someone else in the glass",
        action="asked each reflection what help the marsh would need and wrote the answers in mud",
        transformation="the mirror became a clear pool that reflected everyone equally",
        result="the succession choice was based on service already begun, not on a grand image",
        lesson="A future is worth imagining only when it guides kind action today.",
        ending="The clear pool held the faces of hippos, birds, and fish beneath one peaceful sky.",
    ),
]


@dataclass
class Character:
    id: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str


@dataclass
class StoryParams:
    hippo: str
    elder: str
    place: str
    treasure: str
    lesson: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    hero: Character
    elder: Character
    treasure: str
    trial: Trial
    route: int = 0
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A magical hippo succession fable.")
    ap.add_argument("--hippo", choices=HIPPO_NAMES)
    ap.add_argument("--elder", choices=ELDER_NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--lesson", choices=LESSONS)
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
    return StoryParams(
        hippo=args.hippo or rng.choice(HIPPO_NAMES),
        elder=args.elder or rng.choice(ELDER_NAMES),
        place=args.place or rng.choice(PLACES),
        treasure=args.treasure or rng.choice(TREASURES),
        lesson=args.lesson or rng.choice(LESSONS),
    )


def make_world(params: StoryParams) -> World:
    if params.hippo == params.elder:
        raise StoryError("The hippo heir and elder must be different characters.")
    hero = Character(
        id=params.hippo,
        role="hypothetical heir",
        meters={"courage": 0.5, "listening": 0.2, "service": 0.2},
        memes={"humility": 0.3, "wonder": 0.8},
    )
    elder = Character(
        id=params.elder,
        role="elder guide",
        meters={"wisdom": 1.0},
        memes={"patience": 1.0},
    )
    key = params.seed if params.seed is not None else sum(ord(c) for c in "|".join(vars(params).values() if False else [params.hippo, params.elder, params.place, params.treasure]))
    trial = TRIALS[key % len(TRIALS)]
    return World(
        setting=Setting(params.place),
        hero=hero,
        elder=elder,
        treasure=params.treasure,
        trial=trial,
        route=(key // len(TRIALS)) % 3,
    )


def tell(world: World) -> None:
    h, e, t = world.hero, world.elder, world.trial
    world.say(
        f"In {world.setting.place}, {h.id} the hippo wondered about a hypothetical succession. "
        f"{t.premise}"
    )
    world.say(
        f"{e.id} showed {h.id} the royal {world.treasure} and said, "
        f'"A successor is not the hippo who grabs first. It is the one who notices who needs help."'
    )
    world.para()
    world.say(
        f"{h.id} felt a tug of excitement and wanted to {t.temptation}. "
        f'"But what if I fail?" asked {h.id}. '
        f'"Then listen for the true clue," replied {e.id}.'
    )
    world.say(
        f"The clue was that {t.clue}. {h.id} stopped, listened, and realized that {t.worry}."
    )
    world.para()
    world.say(
        f"Instead of rushing toward a crown, {h.id} {t.action}. "
        f"The hippo's listening rose, and the old magic stirred."
    )
    world.say(
        f"With a soft flash, {t.transformation}. Then {t.result}. "
        f"{h.id} understood that succession meant accepting a duty, not collecting a prize."
    )
    world.para()
    world.say(
        f'"I can lead only if I remember everyone," said {h.id}. '
        f'"That is the promise the magic was waiting for," said {e.id}.'
    )
    world.say(
        f"The fable taught this: {t.lesson} {t.ending}"
    )
    world.hero.meters.update(listening=1.0, service=1.0, courage=0.9)
    world.hero.memes.update(humility=1.0, wonder=1.0)
    world.facts.update(
        hero=h,
        elder=e,
        setting=world.setting,
        trial=t,
        clue=t.clue,
        action=t.action,
        transformation=t.transformation,
        result=t.result,
        lesson=t.lesson,
        ending=t.ending,
    )


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hippo", "hero"),
        asp.fact("imagines", "hero", "succession"),
        asp.fact("listens", "hero"),
        asp.fact("helps", "hero"),
        asp.fact("accepts_duty", "hero"),
        asp.fact("shares", "hero"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_succession/1."))
    found = set(asp.atoms(model, "good_succession"))
    if found != {("hero",)}:
        print(f"MISMATCH: {found}")
        return 1
    for params in curated():
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 3:
            print("MISMATCH: generated story was incomplete")
            return 1
    print("OK: ASP parity and generated stories verified.")
    return 0


def generation_prompts(world: World) -> list[str]:
    t = world.trial
    return [
        f"Write a child-friendly fable about {world.hero.id}, a hippo facing a hypothetical succession in {world.setting.place}.",
        f"Show how the magical clue '{t.clue}' changes the heir's decision.",
        f"End with a transformation proving that leadership means service, not possession.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h, e, t = world.hero, world.elder, world.trial
    return [
        QAItem(
            question=f"What was {h.id} wondering about?",
            answer=f"{h.id} was wondering about a hypothetical succession and what it would mean to become the next leader.",
        ),
        QAItem(
            question=f"What clue changed {h.id}'s plan?",
            answer=f"The clue was that {t.clue}, so {h.id} stopped chasing the prize and paid attention to the marsh's needs.",
        ),
        QAItem(
            question=f"How did {h.id} respond to the magical test?",
            answer=f"{h.id} {t.action}. This showed listening and service instead of greed.",
        ),
        QAItem(
            question="What transformation happened?",
            answer=f"{t.transformation} The changed object showed that magic had turned authority into a useful duty.",
        ),
        QAItem(
            question="What did the succession teach the hippo?",
            answer=f"It taught {h.id} that {t.lesson}",
        ),
        QAItem(
            question="How did the ending prove that the hippo had changed?",
            answer=f"{t.ending} The final image shows that the new leader was caring for the community rather than merely wearing a royal object.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is succession?",
            answer="Succession is the peaceful change from one leader to the next leader.",
        ),
        QAItem(
            question="What makes magic useful in this fable?",
            answer="The magic reveals character and transforms a royal object into something that serves the whole community.",
        ),
        QAItem(
            question="Why does the fable use a hypothetical situation?",
            answer="The hypothetical situation lets the hippo imagine a future choice and learn how present actions can prepare a wise successor.",
        ),
    ]


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world model state ---",
        f"hero={world.hero.id} role={world.hero.role}",
        f"hero_meters={world.hero.meters}",
        f"hero_memes={world.hero.memes}",
        f"elder={world.elder.id} role={world.elder.role}",
        f"place={world.setting.place}",
        f"treasure={world.treasure}",
        f"trial={world.trial.title}",
        f"clue={world.trial.clue}",
        f"transformation={world.trial.transformation}",
        f"result={world.trial.result}",
    ])


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def curated() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Grandmother Sefu", "the silver marsh", "a blue water-lily", LESSONS[0]),
        StoryParams("Boma", "Old Kito", "the lily lagoon", "a shell bell", LESSONS[1]),
        StoryParams("Nala", "Auntie Rani", "the reed valley", "a golden reed", LESSONS[2]),
        StoryParams("Tavi", "Elder Duma", "the moonlit pool", "a moonstone", LESSONS[3]),
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_succession/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program(
            "#show hypothetical_case/1.\n"
            "#show magic_ready/1.\n"
            "#show transformed_crown/1.\n"
            "#show wise_heir/1.\n"
            "#show good_succession/1."
        ))
        print("\n".join(str(atom) for atom in model))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        for i in range(args.n):
            rng = random.Random(base + i)
            params = resolve_params(args, rng)
            params.seed = base + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
