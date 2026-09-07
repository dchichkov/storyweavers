#!/usr/bin/env python3
"""A gentle bedtime story about a nose, a shared secret, and a small warning."""
from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


NAMES = ("Nell", "Milo", "Rose", "Ada")
OBJECTS = ("bell", "lantern", "acorn")
WEATHERS = ("misty", "windy", "still")
MAX_STEPS = 12


@dataclass
class StoryParams:
    hero: str = "Nell"
    friend: str = "Milo"
    object_name: str = "bell"
    weather: str = "misty"
    world_seed: int = 777
    prose_seed: int = 42


@dataclass
class Entity:
    id: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    id: int
    kind: str
    actor: str
    data: dict
    facts: tuple[str, ...]
    causes: tuple[int, ...]


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity]
    history: list[Event] = field(default_factory=list)
    facts: dict[str, int] = field(default_factory=dict)
    outcome: str = ""

    def record(self, kind, actor, facts=(), needs=(), **data):
        if any(item not in self.facts for item in needs):
            raise StoryError(f"{kind} needs an earlier story fact.")
        causes = tuple(sorted(self.facts[item] for item in needs))
        event = Event(len(self.history), kind, actor, data, tuple(facts), causes)
        self.history.append(event)
        for item in facts:
            self.facts[item] = event.id


def validate_params(p: StoryParams):
    if p.hero not in NAMES or p.friend not in NAMES:
        raise StoryError("Names must come from the name registry.")
    if p.hero == p.friend:
        raise StoryError("The hero and friend need different names.")
    if p.object_name not in OBJECTS:
        raise StoryError("That object is not available.")
    if p.weather not in WEATHERS:
        raise StoryError("That weather is not available.")
    if type(p.world_seed) is not int or type(p.prose_seed) is not int:
        raise StoryError("Seeds must be integers.")


def build_world(p: StoryParams) -> World:
    validate_params(p)
    return World(
        p,
        {
            "hero": Entity("hero", p.hero, "bedroom", memes={"curiosity": 1}),
            "friend": Entity("friend", p.friend, "bedroom", memes={"trust": 1}),
            "nose": Entity("nose", "the warm little nose", "pillow", meters={"warmth": 2}),
            "object": Entity("object", f"the {p.object_name}", "drawer", meters={"shareable": 1}),
            "window": Entity("window", "the window", "bedroom", meters={"latched": 1}),
            "moon": Entity("moon", "the moon", "sky"),
        },
    )


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    w.record("opening", "hero", facts=("bedtime",), weather=p.weather)
    w.record("notice_nose", "hero", facts=("nose_seen",), needs=("bedtime",))
    w.record("share_secret", "hero", facts=("secret_shared",), needs=("nose_seen",))
    w.record("warning", "friend", facts=("warning_heard",), needs=("secret_shared",))
    w.record("listen", "hero", facts=("warning_believed",), needs=("warning_heard",))
    w.record("prepare", "hero", facts=("object_ready",), needs=("warning_believed",))
    w.record("night_change", "friend", facts=("wind_arrives",), needs=("object_ready",))
    w.record("help", "hero", facts=("safe",), needs=("wind_arrives", "object_ready"))
    w.outcome = "safe_together"
    w.record("ending", "friend", facts=("ended",), needs=("safe",))
    validate_world(w)
    return w


def validate_world(w: World):
    if w.outcome != "safe_together" or "ended" not in w.facts:
        raise StoryError("The bedtime story must resolve safely.")
    for event in w.history:
        if any(parent >= event.id for parent in event.causes):
            raise StoryError("An event cannot depend on the future.")


def render(w: World, prose_seed: int):
    rng = random.Random(prose_seed)
    p = w.params
    lines = []
    qa = []

    def choose(*items):
        return rng.choice(items)

    for event in w.history:
        k = event.kind
        if k == "opening":
            lines.append(
                f"At bedtime, {p.hero} and {p.friend} curled beneath one quilt while the {event.data['weather']} night whispered at the window."
            )
        elif k == "notice_nose":
            lines.append(
                f"{p.hero} noticed {p.friend}'s warm little nose peeping above the blanket. It twitched whenever the old house creaked."
            )
            lines.append(f'"Your nose knows something," said {p.hero}.')
            lines.append(f'"It knows the wind is coming," said {p.friend}.')
            qa.append(QAItem(
                "What did the nose seem to notice?",
                "The nose twitched at the creaks and seemed to sense that the wind was coming."
            ))
        elif k == "share_secret":
            lines.append(
                f"{p.hero} shared a secret: the tiny {p.object_name} in the drawer could make a soft sound if the night became too dark."
            )
            lines.append(f'"I will share it with you," said {p.hero}.')
            lines.append(f'"Then I will share my warning with you," said {p.friend}.')
        elif k == "warning":
            lines.append(
                f"{p.friend} pointed toward the window. A thin silver thread of moonlight trembled beneath the latch."
            )
            lines.append(f'"The wind will open it," {p.friend} whispered. "Listen for the first cold breath."')
            qa.append(QAItem(
                "What warning did the friend give?",
                "The friend warned that the wind might open the window and told the hero to listen for its first cold breath."
            ))
        elif k == "listen":
            lines.append(
                f"{p.hero} listened instead of laughing. Beneath the quiet, the window gave a tiny click."
            )
            lines.append(f'"You were right," said {p.hero}. "Your nose heard the night before I did."')
            lines.append(f'"And you shared the secret before the night needed it," said {p.friend}.')
        elif k == "prepare":
            lines.append(
                f"Together they placed the little {p.object_name} beside the bed, where either child could reach it."
            )
        elif k == "night_change":
            lines.append(
                "The promised wind arrived. It pressed its cool fingers against the window, and the latch lifted."
            )
            qa.append(QAItem(
                "What happened after the warning?",
                "The wind arrived and lifted the window latch, just as the friend had predicted."
            ))
        elif k == "help":
            lines.append(
                f"{p.hero} rang the {p.object_name} once. A grown-up came, closed the window, and tucked the children safely beneath the quilt."
            )
            lines.append(f'"Sharing helped us notice," said {p.hero}.')
            lines.append(f'"And listening helped us act," said {p.friend}.')
        elif k == "ending":
            lines.append(
                f"At last, {p.friend}'s nose grew warm again. The {p.object_name} rested between them, and the moon laid a quiet stripe across the floor."
            )
            lines.append(
                f"Then {p.hero} and {p.friend} fell asleep, sharing the blanket, the secret, and the little courage that had kept their room safe."
            )
            qa.append(QAItem(
                "How did the children stay safe?",
                f"They shared the warning, listened for the window's click, and rang the {p.object_name} so a grown-up could close the window."
            ))
    return "\n\n".join(lines), qa


ASP_RULES = """
warning_shared :- secret_shared.
safe :- warning_shared, wind_arrives, object_ready.
#show warning_shared/0.
#show safe/0.
"""


def asp_facts():
    from asp import fact
    return "\n".join([
        fact("secret_shared"),
        fact("wind_arrives"),
        fact("object_ready"),
    ])


def verify():
    from asp import atoms, one_model
    model = one_model(asp_facts() + ASP_RULES)
    if set(atoms(model, "warning_shared")) != {()}:
        raise StoryError("ASP did not derive the shared warning.")
    if set(atoms(model, "safe")) != {()}:
        raise StoryError("ASP did not derive the safe ending.")
    for name in NAMES:
        for obj in OBJECTS:
            sample = generate(StoryParams(hero=name, friend="Milo" if name != "Milo" else "Nell",
                                          object_name=obj))
            if "nose" not in sample.story.lower():
                raise StoryError("The nose disappeared from a generated story.")
    print("OK: Python and ASP agree; generated stories resolve safely.")


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    story, qa = render(world, params.prose_seed)
    return StorySample(
        params=params,
        story=story,
        prompts=[f"Write a bedtime story about {params.hero} sharing a warning with {params.friend}'s nose."],
        story_qa=qa,
        world_qa=[
            QAItem("Why is sharing useful in this world?", "Sharing lets the children combine what each one notices and choose a safe action together."),
            QAItem("What does foreshadowing do here?", "The twitching nose and the friend's warning prepare us for the wind opening the window."),
        ],
        world=world,
    )


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--friend", choices=NAMES)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
    parser.add_argument("--weather", choices=WEATHERS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng, index=0, sample=False):
    hero = args.hero or (rng.choice(NAMES) if sample else "Nell")
    choices = tuple(name for name in NAMES if name != hero)
    friend = args.friend or (rng.choice(choices) if sample else "Milo")
    p = StoryParams(
        hero=hero,
        friend=friend,
        object_name=args.object_name or (rng.choice(OBJECTS) if sample else "bell"),
        weather=args.weather or (rng.choice(WEATHERS) if sample else "misty"),
        world_seed=args.seed + index,
        prose_seed=args.prose_seed + index,
    )
    validate_params(p)
    return p


def emit(sample, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "outcome": sample.world.outcome,
            "history": [asdict(event) for event in sample.world.history],
        }, indent=2))


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            from asp import atoms, one_model
            print(json.dumps(sorted(atoms(one_model(asp_facts() + ASP_RULES), "safe"))))
            return 0
        rng = random.Random(args.seed)
        if args.all:
            params = [
                StoryParams(hero=hero, friend=friend, object_name=obj, weather=weather,
                            world_seed=args.seed + i, prose_seed=args.prose_seed + i)
                for i, (hero, friend, obj, weather) in enumerate(
                    (h, f, o, w)
                    for h in NAMES
                    for f in NAMES
                    if h != f
                    for o in OBJECTS
                    for w in WEATHERS
                )
            ]
        else:
            params = [resolve_params(args, rng, i, sample=args.n > 1) for i in range(args.n)]
        samples = [generate(p) for p in params]
        if args.json:
            data = [sample.to_dict() for sample in samples]
            print(json.dumps(data[0] if len(data) == 1 else data, ensure_ascii=False, indent=2))
        else:
            for i, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {i + 1}\n" if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
