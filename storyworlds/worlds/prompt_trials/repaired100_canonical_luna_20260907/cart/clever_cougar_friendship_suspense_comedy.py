#!/usr/bin/env python3
"""Clever Cougar Friendship: a funny suspense story about a careful rescue."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    speaker: str = ""
    listener: str = ""
    revealed: str = ""
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Luna"
    friend: str = "Pip"
    animal: str = "cougar"
    trick: str = "bell"
    approach: str = "listen"
    seed: int = 777


NAMES = ("Luna", "Pip", "Mara", "Toby", "Nia", "Owen")
TRICKS = {
    "bell": ("brass bell", "a bright ding"),
    "shadow": ("striped blanket", "a wiggly shadow"),
    "drum": ("small drum", "a gentle rumble"),
}
APPROACHES = ("listen", "rush")
PROMPT = (
    "Write a funny, suspenseful children's story about Luna and a friend "
    "using clever teamwork to help a cougar safely leave a picnic cart."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character", memes={"bravery": 0.5, "trust": 0.5}),
            "friend": Entity("friend", params.friend, "character", memes={"bravery": 0.5, "trust": 0.5}),
            "cougar": Entity(
                "cougar", "the cougar", "animal", "cart",
                meters={"distance_to_trail": 8, "calm": 0.2},
                memes={"curiosity": 0.8, "trust": 0.1},
            ),
            "cart": Entity(
                "cart", "the picnic cart", "vehicle", "meadow",
                meters={"wheel_turns": 0, "rope_tight": 1},
            ),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question="", cause="", result=""):
        self.history.append(Event(
            kind=kind, text=text, question=question, cause=cause,
            result=result, state=self.snapshot()
        ))

    def say(self, speaker: str, text: str, *, to="", reveal="", tag="said"):
        actor = self.entities[speaker]
        if reveal:
            if not to or reveal not in actor.beliefs:
                raise StoryError("A character cannot share information they have not learned.")
            self.entities[to].beliefs[reveal] = actor.beliefs[reveal]
        if text.endswith("?") and tag == "said":
            tag = "asked"
        clean = text[:-1] + "," if text.endswith(".") else text
        self.history.append(Event(
            kind="speech",
            text=f'"{clean}" {actor.label} {tag}.',
            speaker=speaker,
            listener=to,
            revealed=reveal,
            state=self.snapshot(),
        ))

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(event.question, f"{event.cause} {event.result}")
                for event in self.history if event.question
            ],
            world_qa=[
                QAItem(
                    "What should people do around a wild cougar?",
                    "They should stay calm, keep their distance, and ask a trained adult or wildlife helper for assistance.",
                )
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.animal != "cougar":
        raise StoryError("This story domain only supports a cougar.")
    if params.trick not in TRICKS or params.approach not in APPROACHES:
        raise StoryError("Choose a listed trick and approach.")
    if params.hero == params.friend:
        raise StoryError("The two friends need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.hero, params.friend)):
        raise StoryError("Use simple capitalized names, such as Luna and Pip.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["rope"] = Entity(
        "rope", "the cart rope", "tool", "cart",
        meters={"length": 3, "loose": 0},
    )
    world.entities["gate"] = Entity(
        "gate", "the trail gate", "barrier", "trail",
        meters={"opening": 1, "needed": 1},
    )
    return world


def release_cart(world: World):
    cart = world.entities["cart"]
    rope = world.entities["rope"]
    cougar = world.entities["cougar"]
    if world.entities["hero"].beliefs.get("plan") != "release":
        raise StoryError("The friends must agree on a safe release plan.")
    if world.entities["friend"].beliefs.get("plan") != "release":
        raise StoryError("Both friends must know and accept the release plan.")
    if rope.meters["loose"] != 1:
        raise StoryError("The rope must be loosened before the cart can roll.")
    cart.meters["rope_tight"] = 0
    cart.location = "beside_meadow"
    cougar.location = "trail"
    cougar.meters["distance_to_trail"] = 0
    cougar.meters["calm"] = 1.0
    cougar.memes["trust"] = 0.8


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero, friend = world.entities["hero"], world.entities["friend"]
    h, f = hero.label, friend.label
    trick_name, sound = TRICKS[params.trick]

    world.narrate(
        "beginning",
        f"{h} and {f} were packing a picnic when a clever cougar climbed into the open cart. "
        f"It had not stolen the sandwiches. It had stolen the cart's best seat."
    )
    world.say("hero", "Please do not start the cart.")
    world.say("friend", "I was only going to move it one inch.")
    world.say("hero", "The cougar is beside the wheel. One inch could become a very exciting inch.")
    world.say("friend", "How exciting?"
    )
    world.say("hero", "The kind where we remember to breathe.")

    cougar = world.entities["cougar"]
    cougar.beliefs["reason"] = "the rope tugs whenever the cart moves"
    world.say("hero", "Look at its ears. The rope is tight, and every wheel wiggle scares it.",
              to="friend", reveal="reason")

    if params.approach == "rush":
        hero.memes["bravery"] += 0.2
        world.say("friend", "I can yank the rope loose right now.")
        world.narrate(
            "mistake",
            f"{f} reached for the rope, but the cougar gave a deep growl and {f} froze with one hand in the air.",
            question="Why did Pip stop reaching for the rope?",
            cause="The tight rope made the cougar nervous, and a sudden grab made the danger worse.",
            result="Pip held still so the cougar would not panic.",
        )
        world.say("hero", "Good stopping. We need a plan quieter than your elbow.")
        world.say("friend", "My elbow is usually very persuasive.")
    else:
        world.say("friend", "Then we should watch before we touch anything.")
        world.narrate(
            "listening",
            f"They watched without stepping closer. The cougar relaxed whenever the cart stayed still, "
            f"but it stiffened whenever the rope pulled.",
            question="What clue helped the friends understand the danger?",
            cause="The cougar stayed calmer when the cart was still and grew tense when the rope pulled.",
            result="The friends decided to loosen the rope before moving the cart.",
        )

    hero.beliefs["plan"] = "release"
    world.say("hero", f"Let's use the {trick_name} to draw its eyes toward the trail, then loosen the rope.",
              to="friend", reveal="plan")
    friend.beliefs["plan"] = "release"
    world.say("friend", "I agree. I will make the sound from far away.")
    world.say("hero", "And I will pull the rope only after the cougar follows the sound.")
    world.say("friend", "If it follows me, I shall walk like a calm picnic.")

    if params.trick == "bell":
        world.narrate(
            "distraction",
            f"{f} stepped several paces away and rang the {trick_name}. {sound} floated toward the trail. "
            f"The cougar lifted its head, as if someone had announced dessert.",
        )
    elif params.trick == "shadow":
        world.narrate(
            "distraction",
            f"{f} held up the {trick_name} and slowly waved it near the trail. "
            f"The {sound} slid over the grass, and the cougar followed it with wide eyes.",
        )
    else:
        world.narrate(
            "distraction",
            f"{f} tapped the {trick_name} softly near the trail. "
            f"The sound rolled across the meadow, and the cougar turned toward it.",
        )

    world.say("friend", "It is looking at the trail!")
    world.say("hero", "Keep walking slowly. No sudden picnic dancing.")
    world.say("friend", "I make no promises about my usual dancing.")

    cougar.beliefs["safe_path"] = "the open trail"
    world.say("hero", "The trail is open now. I am loosening the rope.", to="friend", reveal="safe_path")
    world.entities["rope"].meters["loose"] = 1
    world.narrate(
        "turn",
        f"{h} loosened the rope with careful fingers. The cart gave a tiny squeak, "
        f"but the cougar kept walking toward the open trail.",
        question="What changed the cougar's behavior?",
        cause="Pip used a gentle {0} to draw the cougar toward the open trail while Luna loosened the rope slowly.".format(trick_name),
        result="The cart stopped tugging, so the cougar could leave without being chased.",
    )

    release_cart(world)
    world.narrate(
        "resolution",
        f"The cougar padded through the trail gate and vanished among the pines. "
        f"The cart rolled free with one last squeak, which sounded exactly like a tiny laugh.",
        question="How did the friends help the cougar leave safely?",
        cause="They used a distant distraction and loosened the cart rope instead of rushing the animal.",
        result="The cougar walked through the open trail gate while the cart was released.",
    )
    world.say("friend", "Do you think it will come back for the sandwiches?")
    world.say("hero", "Only if you keep calling them an all-you-can-eat picnic.")
    world.say("friend", "Then I shall rename them three careful sandwiches.")
    world.narrate(
        "ending",
        "The friends packed the food, closed the cart, and sat far from the trail. "
        "In the pine shadows, a golden tail flicked once, as if the clever cougar approved.",
        question="What showed that the problem was truly over?",
        cause="The cougar had reached the trail, and the cart was no longer tugging it.",
        result="The friends could pack their food safely while the cougar disappeared into the pines.",
    )

    sample = world.sample()
    check_sample(sample)
    return sample


def check_ending(world: World):
    cougar = world.entities["cougar"]
    cart = world.entities["cart"]
    rope = world.entities["rope"]
    if cougar.location != "trail" or cougar.meters["calm"] < 1:
        raise StoryError("The cougar must reach the trail calmly.")
    if cart.meters["rope_tight"] != 0 or rope.meters["loose"] != 1:
        raise StoryError("The cart rope must be released at the ending.")


def check_sample(sample: StorySample):
    check_ending(sample.world)
    speech = [event for event in sample.world.history if event.kind == "speech"]
    if len(speech) < 12:
        raise StoryError("The friendship story needs a sustained exchange.")
    if any(sum(event.speaker == key for event in speech) < 5 for key in ("hero", "friend")):
        raise StoryError("Both friends must contribute meaningful dialogue.")
    if not any(event.revealed for event in speech):
        raise StoryError("Dialogue must pass useful information between friends.")
    if len(sample.story_qa) < 4:
        raise StoryError("The story needs several grounded questions and answers.")
    if any(word in sample.story.lower() for word in ("meters", "memes", "hero", "friend")):
        raise StoryError("Internal simulation vocabulary leaked into the story.")


ASP_RULES = """
safe_plan(release) :- animal(cougar), tool(rope), gate(open).
#show safe_plan/1.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join([
        fact("animal", "cougar"),
        fact("tool", "rope"),
        fact("gate", "open"),
    ])


def asp_plan() -> set[tuple[str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "safe_plan"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--trick", choices=tuple(TRICKS))
    parser.add_argument("--approach", choices=APPROACHES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    friend_choices = [name for name in NAMES if name != hero]
    friend = args.friend or rng.choice(friend_choices)
    params = StoryParams(
        hero=hero,
        friend=friend,
        trick=args.trick or rng.choice(tuple(TRICKS)),
        approach=args.approach or rng.choice(APPROACHES),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if asp_plan() != {("release",)}:
        raise StoryError("Python and ASP disagree about the safe plan.")
    tested = 0
    for trick in TRICKS:
        for approach in APPROACHES:
            sample = generate(StoryParams(trick=trick, approach=approach))
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; ASP confirms the release plan.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "entities": sample.world.snapshot(),
            "history": [asdict(event) for event in sample.world.history],
        }, indent=2))


def main() -> int:
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
            print(json.dumps(sorted(asp_plan())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            params_list = [
                StoryParams(
                    hero=args.hero or "Luna",
                    friend=args.friend or "Pip",
                    trick=trick,
                    approach=approach,
                    seed=args.seed,
                )
                for trick in TRICKS
                for approach in APPROACHES
                if args.trick is None or trick == args.trick
                if args.approach is None or approach == args.approach
            ]
            for params in params_list:
                validate_params(params)
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload, ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
