#!/usr/bin/env python3
"""
A small space-adventure storyworld set on a train platform, where a snapped
signal causes trouble and a careful fix teaches Luna a lasting lesson.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    helper: str
    train: str
    signal: str
    mission: str
    seed: Optional[int] = None
    repair_method: Optional[str] = None
    announcement: Optional[str] = None
    lesson: Optional[str] = None


@dataclass(frozen=True)
class Mission:
    key: str
    title: str
    object: str
    destination: str
    danger: str
    success: str


@dataclass(frozen=True)
class Repair:
    key: str
    method: str
    tool: str
    detail: str


NAMES = ["Luna", "Milo", "Nia", "Orion", "Tess", "Kai"]
HELPERS = ["Ari", "the station keeper", "Pip the robot"]
TRAINS = ["the comet train", "the moon express", "the red planet shuttle"]
SIGNALS = ["a blue platform beacon", "the silver departure lamp", "the star-shaped signal"]
ANNOUNCEMENTS = ["clear and brave", "bright and honest", "short and helpful"]

MISSIONS = [
    Mission("moon_crates", "the Moon-crate mission", "a box of moon seeds", "the Moon Garden",
            "the departure signal snapped just before launch", "the seeds reach the Moon Garden"),
    Mission("star_map", "the star-map mission", "a folded star map", "the Observatory Ring",
            "a snapped signal leaves two routes blinking at once", "the map reaches the observatory"),
    Mission("comet_mail", "the comet-mail mission", "a warm letter", "Comet Station",
            "the signal snaps while the train is waiting beside a dark tunnel", "the letter reaches its reader"),
    Mission("water_tank", "the sky-water mission", "a tank of cloud water", "Mars Valley",
            "the platform signal snaps during a gust from the launch fans", "the water arrives before the valley wells dry"),
]

REPAIRS = [
    Repair("wire", "joined the two safe ends", "a copper clip", "She checked the color marks before fastening them."),
    Repair("lever", "returned the loose lever to its slot", "a flat repair key", "She tested it gently instead of forcing it."),
    Repair("lens", "cleaned and reseated the signal lens", "a soft cloth", "She lined up its tiny star mark with the housing."),
    Repair("panel", "closed the signal panel and tightened its latch", "a little moon wrench", "She counted each turn so the latch would not wobble."),
]

LESSONS = [
    ("check_first", "Check first, then fix.", "Rushing can make a small problem grow."),
    ("ask_help", "Ask for help when a job is important.", "A careful helper can notice what one pair of eyes misses."),
    ("tell_truth", "Tell the truth about a problem.", "An honest announcement lets everyone choose a safe plan."),
    ("test_twice", "Test a repair twice.", "A repair is ready when it works safely, not merely when it looks finished."),
]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def choose(items, key):
    for item in items:
        if item.key == key:
            return item
    raise StoryError(f"Unknown choice: {key}")


def seed_value(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum(ord(ch) for ch in f"{params.name}|{params.helper}|{params.train}")


def complete_params(params: StoryParams) -> None:
    rng = random.Random(seed_value(params) ^ 0xA17F21)
    params.repair_method = params.repair_method or rng.choice(REPAIRS).key
    params.announcement = params.announcement or rng.choice(ANNOUNCEMENTS)
    params.lesson = params.lesson or rng.choice([key for key, _, _ in LESSONS])


def lesson_data(key: str) -> tuple[str, str, str]:
    for item in LESSONS:
        if item[0] == key:
            return item
    raise StoryError(f"Unknown lesson: {key}")


def build_world(params: StoryParams) -> World:
    complete_params(params)
    mission = choose(MISSIONS, params.mission)
    repair = choose(REPAIRS, params.repair_method)
    lesson_key, lesson, consequence = lesson_data(params.lesson)

    w = World()
    child = w.add(Entity(
        "luna", "character", "child", params.name,
        meters={"courage": 0.0, "worry": 0.0, "care": 0.0},
        memes={"lesson": 0.0, "trust": 0.0},
    ))
    helper = w.add(Entity(
        "helper", "character", "helper", params.helper,
        meters={"patience": 2.0, "skill": 2.0},
        memes={"care": 1.0},
    ))
    train = w.add(Entity(
        "train", "vehicle", "space_train", params.train,
        meters={"ready": 1.0},
        memes={"journey": 1.0},
    ))
    signal = w.add(Entity(
        "signal", "object", "platform_signal", params.signal,
        meters={"working": 1.0},
        memes={"safety": 1.0},
    ))

    w.facts.update(
        child=child,
        helper=helper,
        train=train,
        signal=signal,
        mission=mission,
        repair=repair,
        lesson_key=lesson_key,
        lesson=lesson,
        consequence=consequence,
        params=params,
        announced=False,
        repaired=False,
        tested=False,
    )
    return w


def words(w: World) -> dict[str, str]:
    return {
        "name": w.facts["child"].label,
        "helper": w.facts["helper"].label,
        "train": w.facts["train"].label,
        "signal": w.facts["signal"].label,
    }


def begin(w: World) -> None:
    p = w.facts["params"]
    mission = w.facts["mission"]
    w.say(
        f"At the train platform beneath a sky full of stars, {p.name} prepared "
        f"{p.train} for {mission.title}. Its cargo was {mission.object}, bound for {mission.destination}."
    )
    w.say(
        f"The platform lights glittered like tiny planets, and {p.name} felt ready "
        "for a grand space adventure."
    )


def snap_signal(w: World) -> None:
    c = w.facts["child"]
    mission = w.facts["mission"]
    signal = w.facts["signal"]
    c.meters["worry"] += 2
    signal.meters["working"] = 0
    w.say(
        f"Then {mission.danger}. With a sharp SNAP, {signal.label} bent sideways "
        "and flashed red instead of green."
    )
    w.say(
        f"The train doors paused, the launch clock blinked, and {c.label} reached "
        "for the signal before stopping to look closely."
    )


def announce_problem(w: World) -> None:
    c = w.facts["child"]
    h = w.facts["helper"]
    p = w.facts["params"]
    c.memes["trust"] += 1
    w.facts["announced"] = True
    w.say(
        f'"The departure signal has snapped," {c.label} announced. '
        f'"Please wait while we make the platform safe."'
    )
    w.say(
        f'"Good announcement," said {h.label}. "Now nobody will guess or rush. '
        'Let us inspect it together."'
    )


def repair_signal(w: World) -> None:
    c = w.facts["child"]
    h = w.facts["helper"]
    repair = w.facts["repair"]
    c.meters["care"] += 2
    c.meters["worry"] -= 1
    w.say(
        f"{c.label} and {h.label} looked behind the signal. "
        f"{repair.detail} Then {c.label} {repair.method} using {repair.tool}."
    )
    w.say(
        f'"A fix is not a guess," {c.label} said. "We must test it before the train moves."'
    )
    w.say(
        f'"Exactly," replied {h.label}. "A safe space adventure begins with careful work."'
    )
    w.facts["repaired"] = True
    w.facts["signal"].meters["working"] = 1


def test_signal(w: World) -> None:
    c = w.facts["child"]
    signal = w.facts["signal"]
    c.memes["lesson"] += 1
    w.facts["tested"] = True
    w.say(
        f"{c.label} pressed the test button once. The {signal.label} glowed amber. "
        "She waited, checked the cable, and pressed it a second time."
    )
    w.say(
        f"This time the signal shone green and steady. The fix worked because "
        f"{c.label} had checked it twice instead of hurrying."
    )


def launch(w: World) -> None:
    c = w.facts["child"]
    p = w.facts["params"]
    mission = w.facts["mission"]
    c.meters["courage"] += 2
    w.say(
        f"{c.label} announced, '{p.train} may depart safely for {mission.destination}!' "
        "The platform answered with a cheerful chime."
    )
    w.say(
        f"The train lifted from the rails like a silver rocket, carrying "
        f"{mission.object} toward {mission.destination}."
    )


def finish(w: World) -> None:
    c = w.facts["child"]
    lesson = w.facts["lesson"]
    consequence = w.facts["consequence"]
    w.say(
        f"As the stars slid past the windows, {c.label} remembered the lesson: "
        f"{lesson} {consequence}"
    )
    w.say(
        f"At the quiet train platform, the repaired signal kept glowing green, "
        "a small bright promise that careful hands could guide a very big journey."
    )


def tell(params: StoryParams) -> World:
    w = build_world(params)
    begin(w)
    snap_signal(w)
    w.para()
    announce_problem(w)
    repair_signal(w)
    test_signal(w)
    w.para()
    launch(w)
    finish(w)
    return w


def story_qa(w: World) -> list[QAItem]:
    p = w.facts["params"]
    mission = w.facts["mission"]
    repair = w.facts["repair"]
    lesson = w.facts["lesson"]
    return [
        QAItem(
            question=f"Where did {p.name} have to fix the snapped signal?",
            answer=f"{p.name} had to fix the snapped signal at the train platform."
        ),
        QAItem(
            question=f"What was {p.name} carrying on {p.train}?",
            answer=f"{p.name} was carrying {mission.object} to {mission.destination}."
        ),
        QAItem(
            question=f"How did {p.name} fix the {p.signal}?",
            answer=f"{p.name} {repair.method} using {repair.tool}, then tested the repair twice."
        ),
        QAItem(
            question=f"What did {p.name} announce before the fix?",
            answer=f'{p.name} announced, "The departure signal has snapped. Please wait while we make the platform safe."'
        ),
        QAItem(
            question=f"What lesson did {p.name} learn?",
            answer=f"{p.name} learned: {lesson}"
        ),
    ]


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should a broken train signal be fixed before a train departs?",
            answer="A broken signal should be fixed first so people can know when it is safe for the train to move."
        ),
        QAItem(
            question="Why is it useful to announce a problem?",
            answer="Announcing a problem helps others understand what is happening and prevents them from rushing into danger."
        ),
        QAItem(
            question="What does it mean to test a repair?",
            answer="Testing a repair means checking that the repaired thing works safely before relying on it."
        ),
        QAItem(
            question="What is a space adventure?",
            answer="A space adventure is an exciting journey among planets, stars, moons, or other places beyond Earth."
        ),
    ]


def generation_prompts(w: World) -> list[str]:
    p = w.facts["params"]
    mission = w.facts["mission"]
    return [
        f"Write a child-friendly Space Adventure about {p.name} on a train platform.",
        f"Include a snapped signal, an honest announcement, and a careful fix before {p.train} carries {mission.object} to {mission.destination}.",
        f"End with a concrete Lesson Learned about {w.facts['lesson'].lower()}",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out.extend(f"{i}. {q}" for i, q in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    out.append("")
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "train_platform"),
        asp.fact("style", "space_adventure"),
        asp.fact("feature", "lesson_learned"),
        asp.fact("event", "snap"),
        asp.fact("action", "announce"),
        asp.fact("action", "fix"),
        asp.fact("requires", "safe_test"),
    ])


ASP_RULES = r"""
valid_story :-
    setting(train_platform),
    style(space_adventure),
    feature(lesson_learned),
    event(snap),
    action(announce),
    action(fix),
    requires(safe_test).

#show valid_story/0.
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    ok = bool(asp.atoms(model, "valid_story"))
    if not ok:
        print("MISMATCH: ASP gate failed.")
        return 1
    for params in CURATED:
        sample = generate(params)
        required = ["snap", "announced", "fix", "lesson"]
        text = sample.story.lower()
        if "snap" not in text or "announced" not in text or "fix" not in text or "lesson" not in text:
            print("MISMATCH: generated story omitted a required narrative instrument.")
            return 1
    print("OK: ASP and Python gates agree; generated stories passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A space adventure on a train platform.")
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--train", choices=TRAINS)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--mission", choices=[m.key for m in MISSIONS])
    ap.add_argument("--repair-method", choices=[r.key for r in REPAIRS])
    ap.add_argument("--announcement", choices=ANNOUNCEMENTS)
    ap.add_argument("--lesson", choices=[x[0] for x in LESSONS])
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
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        train=args.train or rng.choice(TRAINS),
        signal=args.signal or rng.choice(SIGNALS),
        mission=args.mission or rng.choice(MISSIONS).key,
        repair_method=args.repair_method or rng.choice(REPAIRS).key,
        announcement=args.announcement or rng.choice(ANNOUNCEMENTS),
        lesson=args.lesson or rng.choice([x[0] for x in LESSONS]),
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
        print("--- trace ---")
        for entity in sample.world.entities.values():
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            print(f"{entity.label}: meters={meters} memes={memes}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "Ari", "the comet train", "a blue platform beacon", "moon_crates"),
    StoryParams("Milo", "the station keeper", "the moon express", "the silver departure lamp", "star_map"),
    StoryParams("Nia", "Pip the robot", "the red planet shuttle", "the star-shaped signal", "water_tank"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(args.n * 20, 50)):
            if len(samples) >= args.n:
                break
            current_seed = base_seed + index
            params = resolve_params(args, random.Random(current_seed))
            params.seed = current_seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa,
             header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
