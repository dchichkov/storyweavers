#!/usr/bin/env python3
"""Nose Sharing: three gentle bedtime troubles become shared care."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
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
    question: str = ""
    cause: str = ""
    result: str = ""


@dataclass
class StoryParams:
    child: str = "Mara"
    friend: str = "Pip"
    path: str = "lantern"
    phrasing: str = "quiet"
    seed: int = 777


NAMES = ("Mara", "Lina", "Nora", "Tessa", "Pip", "Ollie")
PATHS = ("lantern", "blanket", "button")
PHRASINGS = ("quiet", "warm")
PROMPT = "Write a gentle bedtime story about sharing, a nose, and a small kindness foreshadowed earlier."


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "child": Entity("child", params.child, "character", "bedroom",
                            memes={"worry": 0.4, "kindness": 0.7}),
            "friend": Entity("friend", params.friend, "character", "bedroom",
                             memes={"worry": 0.5, "kindness": 0.7}),
            "nose": Entity("nose", "a little nose", "body", "bedroom",
                           meters={"sneeze": 0}, memes={"comfort": 0.4}),
            "moon": Entity("moon", "the moon", "thing", "window"),
        }
        self.history: list[Event] = []

    def scene(self, kind: str, text: str, *, question: str = "",
              cause: str = "", result: str = ""):
        self.history.append(Event(kind, text, question, cause, result))

    def say(self, speaker: str, text: str):
        self.history.append(Event("speech", f'{self.entities[speaker].label} said, "{text}"'))


def validate_params(params: StoryParams):
    if params.path not in PATHS:
        raise StoryError("Choose a known bedtime path.")
    if params.phrasing not in PHRASINGS:
        raise StoryError("Choose a known gentle phrasing.")
    if params.child == params.friend:
        raise StoryError("The two friends need different names.")
    if any(not name or not name[0].isupper() for name in (params.child, params.friend)):
        raise StoryError("Names must begin with capital letters.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    if params.path == "lantern":
        world.entities["lantern"] = Entity(
            "lantern", "the star lantern", "thing", "shelf",
            meters={"brightness": 0.2}, memes={"hope": 0.5})
    elif params.path == "blanket":
        world.entities["blanket"] = Entity(
            "blanket", "the blue blanket", "thing", "bed",
            meters={"warmth": 0.5}, memes={"sharing": 0.6})
    else:
        world.entities["button"] = Entity(
            "button", "a moon-shaped button", "thing", "pillow",
            meters={"shiny": 1}, memes={"belonging": 0.5})
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    child, friend = params.child, params.friend
    world.scene("beginning",
                f"{child} and {friend} were getting ready for bed while the moon watched through the window. "
                f"Earlier, they had agreed that a small comfort was nicer when it was shared.")
    world.say("child", f"I hope tonight feels peaceful.")
    world.say("friend", f"It will, if we notice when the other one needs help.")

    if params.path == "lantern":
        lantern = world.entities["lantern"]
        world.scene("trouble",
                    f"The star lantern on the shelf gave one weak blink, and then the room grew dim. "
                    f"{child}'s nose wrinkled as a sneeze tickled it.",
                    question="Why did the room become difficult for them?",
                    cause="The star lantern was almost out, so the dim room made the bedtime worry feel larger.",
                    result=f"{child} noticed the nose tickle and told {friend} instead of hiding it.")
        world.say("child", "My nose is tickling, and I cannot see the lantern's little stars.")
        world.say("friend", "I remember your idea. We can share my night-light while we fix it.")
        friend_ent = world.entities["friend"]
        friend_ent.beliefs["oil"] = "a drop of oil is in the bedside tin"
        world.scene("information",
                    f"{friend} remembered that a tiny tin beside the bed held a drop of oil for stiff lantern hinges.")
        world.say("child", "I thought the tin was empty.")
        world.say("friend", "The drop is small, but shared light can still be enough.")
        lantern.meters["brightness"] = 1.0
        lantern.location = "bedside table"
        world.entities["nose"].meters["sneeze"] = 0
        world.scene("decision",
                    f"{child} held the lantern steady while {friend} added the drop of oil. "
                    f"They took turns winding it, so neither had to work in the dark.")
        world.scene("resolution",
                    f"The lantern glowed with three golden stars. {child}'s nose stopped twitching, and "
                    f"{friend} tucked the shared light between their beds.",
                    question="How did sharing solve the lantern trouble?",
                    cause=f"{friend} remembered the oil, and {child} held the lantern while they repaired it together.",
                    result="The lantern shone again and made the room calm enough for both friends to sleep.")

    elif params.path == "blanket":
        blanket = world.entities["blanket"]
        world.scene("trouble",
                    f"A cold draft slipped under the window. {friend} pulled the blue blanket close, "
                    f"but {child}'s nose peeked out and began to turn pink.",
                    question="What made bedtime uncomfortable?",
                    cause="A draft came under the window while the only warm blanket covered just one friend.",
                    result=f"{child}'s nose grew cold, so {child} explained the trouble.")
        world.say("child", "My nose is cold, but I do not want to steal your blanket.")
        world.say("friend", "You are not stealing it if we make room for both of us.")
        world.scene("information",
                    f"{child} remembered the old quilt folded at the foot of the bed. "
                    f"{friend} had thought it was only for mornings, but the label showed it was a warm spare.")
        world.say("child", "The quilt can go under us, not just over us.")
        world.say("friend", "Then the blanket can cover our shoulders together.")
        blanket.meters["warmth"] = 1.0
        blanket.location = "shared bed"
        world.scene("decision",
                    f"They spread the quilt beneath their feet and folded the blue blanket across both shoulders. "
                    f"{child} moved closer, and {friend} made a careful pocket of warmth.")
        world.scene("resolution",
                    f"Both noses were warm above the blanket's edge. The draft still whispered, but the friends "
                    f"heard it from a snug little nest made for two.",
                    question="How did the friends share warmth?",
                    cause="They used the spare quilt underneath and folded the blue blanket across both shoulders.",
                    result="The draft remained outside the nest, while both friends became warm enough to rest.")

    else:
        button = world.entities["button"]
        world.scene("trouble",
                    f"When {child} turned toward the pillow, a sharp little button brushed their nose. "
                    f"It had come loose from {friend}'s moon-patterned pajamas.",
                    question="Why did they stop settling down?",
                    cause="A loose moon-shaped button brushed against the nose and could scratch it.",
                    result=f"{child} showed {friend} the button instead of pushing it under the pillow.")
        world.say("child", "This button is poking my nose.")
        world.say("friend", "Thank you for telling me. I know where we can keep it safe.")
        world.scene("information",
                    f"{friend} remembered a small cloth pouch in the bedside drawer, the same pouch they had shared "
                    f"for a lost marble the night before.")
        world.say("child", "The pouch held our marble. It can hold your button too.")
        world.say("friend", "And tomorrow we can sew it back before it gets lost.")
        button.location = "cloth pouch"
        world.scene("decision",
                    f"{child} placed the button in the pouch while {friend} folded the loose thread flat. "
                    f"They set the pouch on the table where morning hands could find it.")
        world.scene("resolution",
                    f"The moon-shaped button rested safely beside the bed, and {child}'s nose met only soft cloth. "
                    f"The friends smiled at the small pouch that had remembered both of them.",
                    question="Where did the loose button end up?",
                    cause="They put it in the shared cloth pouch so it would not scratch a nose or disappear.",
                    result="The button stayed safe on the bedside table until it could be sewn back on.")

    world.scene("ending",
                f"The moon climbed higher. {child} and {friend} whispered good night, and the thing they had shared "
                f"made the room feel kinder than it had before.")
    story_qa = [
        QAItem(e.question, f"{e.cause} {e.result}")
        for e in world.history if e.question
    ]
    sample = StorySample(params=params, story="\n\n".join(e.text for e in world.history),
                         prompts=[PROMPT], story_qa=story_qa,
                         world_qa=[QAItem("What did the friends practice?", "They practiced sharing a small comfort and listening when the other person needed help.")],
                         world=world)
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if not any(e.kind == "speech" for e in world.history):
        raise StoryError("The story needs dialogue.")
    speakers = [e.text for e in world.history if e.kind == "speech"]
    if not any(world.params.child in text for text in speakers) or not any(world.params.friend in text for text in speakers):
        raise StoryError("Both characters must speak.")
    if not any("nose" in e.text.lower() for e in world.history):
        raise StoryError("The required nose detail is missing.")
    if len(sample.story_qa) < 1:
        raise StoryError("Each path needs one causal story question.")
    if world.params.path == "lantern" and world.entities["lantern"].meters["brightness"] != 1.0:
        raise StoryError("The lantern was not repaired.")
    if world.params.path == "blanket" and world.entities["blanket"].location != "shared bed":
        raise StoryError("The blanket was not shared.")
    if world.params.path == "button" and world.entities["button"].location != "cloth pouch":
        raise StoryError("The button was not stored safely.")


ASP_RULES = """
solves(lantern,dim_light).
solves(blanket,cold_draft).
solves(button,loose_button).
#show solves/2.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(fact("path", path) for path in PATHS)


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "solves"))


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--child")
    parser.add_argument("--friend")
    parser.add_argument("--path", choices=PATHS)
    parser.add_argument("--phrasing", choices=PHRASINGS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng):
    child = args.child or rng.choice(NAMES)
    friend = args.friend or rng.choice(tuple(n for n in NAMES if n != child))
    return StoryParams(child=child, friend=friend,
                      path=args.path or rng.choice(PATHS),
                      phrasing=args.phrasing or rng.choice(PHRASINGS),
                      seed=args.seed)


def verify():
    if asp_combos() != {("lantern", "dim_light"), ("blanket", "cold_draft"),
                        ("button", "loose_button")}:
        raise StoryError("ASP and Python path rules disagree.")
    for path in PATHS:
        generate(StoryParams(path=path))
    print("OK: 3 complete bedtime paths verified.")


def emit(sample, *, trace=False, qa=False):
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({"entities": {k: asdict(v) for k, v in sample.world.entities.items()},
                          "history": [asdict(e) for e in sample.world.history]}, indent=2))


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
            print(json.dumps(sorted(asp_combos())))
            return 0
        rng = random.Random(args.seed)
        if args.all:
            params_list = [
                StoryParams(child=args.child or child, friend=args.friend or friend,
                            path=path, phrasing=args.phrasing or phrasing,
                            seed=args.seed)
                for path in PATHS
                for child, friend in [(args.child or rng.choice(NAMES),
                                      args.friend or rng.choice(NAMES))]
                for phrasing in PHRASINGS
                if (args.child or child) != (args.friend or friend)
                and (args.phrasing is None or phrasing == args.phrasing)
            ]
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]
        samples = [generate(p) for p in params_list]
        if args.json:
            payload = [s.to_dict() for s in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
        else:
            for i, sample in enumerate(samples):
                if len(samples) > 1:
                    print(f"\n### Story {i + 1}\n")
                emit(sample, trace=args.trace, qa=args.qa)
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
