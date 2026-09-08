#!/usr/bin/env python3
"""The Red Thread: a cautionary folk tale about asking before touching what is not yours."""

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
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Luna"
    elder: str = "Mara"
    temptation: str = "red_bell"
    approach: str = "ask"
    seed: int = 777


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character", "village",
                           memes={"curiosity": 1.0, "fear": 0.1, "wisdom": 0.2}),
            "elder": Entity("elder", params.elder, "character", "village",
                            memes={"care": 1.0, "trust": 0.8}),
            "bell": Entity("bell", "the red bell", "relic", "shrine",
                           meters={"ring_count": 0, "blood_cost": 1},
                           memes={"danger": 1.0, "mystery": 1.0}),
            "thorn": Entity("thorn", "the thorn", "plant", "hill",
                            meters={"sharpness": 1, "blood_drawn": 0},
                            memes={"warning": 1.0}),
            "lantern": Entity("lantern", "the moon lantern", "tool", "shrine",
                              meters={"lit": 0}, memes={"safety": 1.0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(entity) for key, entity in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question: str = "",
                cause: str = "", result: str = ""):
        self.history.append(Event(kind, text, question, cause, result, self.snapshot()))

    def say(self, speaker: str, text: str):
        if not text.endswith((".", "?", "!")):
            text += "."
        name = self.entities[speaker].label
        verb = "asked" if text.endswith("?") else "said"
        self.history.append(Event("speech", f'"{text}" {name} {verb}.',
                                  state=self.snapshot()))

    def draw_blood(self):
        thorn = self.entities["thorn"]
        if thorn.meters["blood_drawn"]:
            raise StoryError("The thorn has already drawn the warning drop.")
        thorn.meters["blood_drawn"] = 1
        self.entities["hero"].memes["fear"] = 0.8
        self.entities["hero"].beliefs["warning"] = "the red bell asks for blood"


TEMPTATIONS = {
    "red_bell": ("red bell", "ring it before sunset"),
    "silver_key": ("silver key", "turn it in the old gate"),
    "black_flute": ("black flute", "play one note at midnight"),
}
APPROACHES = ("ask", "grab")
NAMES = ("Luna", "Tomas", "Nia", "Pip", "Mara", "Oren")
PROMPT = "Write a cautionary folk tale in which Luna learns why a mysterious village relic must never be touched without asking."


def validate_params(params: StoryParams):
    if params.temptation not in TEMPTATIONS:
        raise StoryError("Choose a known village temptation.")
    if params.approach not in APPROACHES:
        raise StoryError("The approach must be ask or grab.")
    if params.hero == params.elder:
        raise StoryError("The child and elder need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.hero, params.elder)):
        raise StoryError("Names must be simple capitalized words.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    label, action = TEMPTATIONS[params.temptation]
    world.entities["bell"].label = f"the {label}"
    world.entities["bell"].beliefs["proper_action"] = action
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero, elder = params.hero, params.elder
    relic, action = TEMPTATIONS[params.temptation]
    world.narrate(
        "beginning",
        f"At the edge of the village stood a shrine with a {relic} beneath a white cloth. "
        f"{hero} had been told never to touch it while the evening star was bright.",
    )
    world.say("hero", f"What is hidden under that cloth")
    world.say("elder", "A promise older than our houses.")
    world.say("hero", "Promises are only words if nobody rings the bell.")
    world.say("elder", "Some words guard people. Ask before you test them.")
    world.narrate(
        "warning",
        f"{elder} pointed to a thorn fence around the shrine. A single dark drop of blood marked one thorn.",
        question="Why did the elder warn Luna before she touched the relic?",
        cause="The relic was an old promise, and the thorn fence had already hurt someone who ignored the warning.",
        result="Luna knew that curiosity was not permission.",
    )

    if params.approach == "grab":
        world.say("hero", f"I will touch the {relic} just once")
        world.narrate(
            "temptation",
            f"{hero} slipped past the cloth and reached toward the {relic}.",
        )
        world.draw_blood()
        world.narrate(
            "sting",
            f"The thorn caught {hero}'s finger. A bright bead of blood rose, and the shrine bell gave one hollow shiver.",
            question="What stopped Luna from grabbing the relic?",
            cause="The thorn pierced her finger and made the old warning real.",
            result="She pulled her hand back instead of taking the relic.",
        )
        world.say("hero", "It drew blood. I should have listened.")
        world.say("elder", "A small wound can carry a large lesson.")
    else:
        world.say("hero", f"May I touch the {relic} if I keep my hands clean")
        world.say("elder", "Not yet. The promise belongs to the whole village.")
        world.say("hero", "Then what may I do")
        world.say("elder", "Carry the moon lantern, and help me watch the path.")
        world.narrate(
            "choice",
            f"{hero} folded their hands and lifted the moon lantern instead of reaching for the {relic}.",
            question="Why did Luna carry the lantern rather than touch the relic?",
            cause="The elder explained that the promise belonged to the whole village, not to one curious child.",
            result="Luna chose a safe task that helped everyone.",
        )

    world.say("hero", "How will we know when the promise is ready")
    world.say("elder", "When the village speaks together, not when one hand grows impatient.")
    world.say("hero", "Then I will wait and tell the others what happened.")
    world.say("elder", "That is how a warning becomes wisdom.")

    if params.approach == "grab":
        world.entities["hero"].memes["wisdom"] = 1.0
        world.entities["hero"].beliefs["lesson"] = "ask before touching"
        world.entities["lantern"].meters["lit"] = 1
        world.narrate(
            "repair",
            f"{hero} washed the blood from the thorn with spring water, then carried the moon lantern beside {elder}.",
            question="How did Luna repair the trouble she caused?",
            cause="She stopped reaching for the relic, cleaned the small wound, and helped guard the shrine.",
            result="Her mistake became a promise to ask before touching what was not hers.",
        )
    else:
        world.entities["hero"].memes["wisdom"] = 1.0
        world.entities["hero"].beliefs["lesson"] = "patience protects"
        world.entities["lantern"].meters["lit"] = 1
        world.narrate(
            "watch",
            f"{hero} and {elder} lit the moon lantern and watched the shrine until the first village footsteps arrived.",
            question="What did Luna do after choosing not to touch the relic?",
            cause="The elder gave her a safe way to help while the village prepared to decide together.",
            result="Luna guarded the path and waited with patience.",
        )

    world.narrate(
        "ending",
        f"When the evening star faded, the cloth still covered the {relic}. "
        f"The lantern shone beside it, and no fresh blood marked the thorns. "
        f"From that night onward, the children said, 'Ask first,' before reaching for any strange treasure.",
        question="What showed that Luna had learned the lesson?",
        cause="She respected the village's promise and helped protect the shrine instead of claiming the relic.",
        result="The relic remained covered, the thorn fence stayed harmless, and Luna became a careful helper.",
    )
    sample = WorldSample(world, params, PROMPT)
    check_sample(sample)
    return sample


class WorldSample(StorySample):
    def __init__(self, world: World, params: StoryParams, prompt: str):
        story = "\n\n".join(event.text for event in world.history)
        story_qa = [
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in world.history if event.question
        ]
        super().__init__(params=params, story=story, prompts=[prompt],
                         story_qa=story_qa, world_qa=[
                             QAItem("What is a safe rule around an unknown relic?",
                                    "Ask the keeper before touching it, because curiosity is not permission.")
                         ], world=world)


def check_sample(sample: StorySample):
    world = sample.world
    if world.entities["hero"].memes["wisdom"] < 1:
        raise StoryError("The hero must learn the cautionary lesson.")
    if world.entities["lantern"].meters["lit"] != 1:
        raise StoryError("The lantern must be lit in the ending.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs at least three grounded questions.")
    speeches = [event for event in world.history if event.kind == "speech"]
    if len(speeches) < 8:
        raise StoryError("The story needs a sustained exchange of dialogue.")
    if not any("blood" in event.text.lower() for event in world.history):
        raise StoryError("The cautionary tale must include blood.")
    if not any("ask" in event.text.lower() for event in world.history):
        raise StoryError("The dialogue must make asking part of the lesson.")


ASP_RULES = """
safe(Approach) :- approach(Approach, ask).
safe_relic(Relic) :- relic(Relic), safe(ask).
#show safe_relic/1.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        [fact("approach", key, value) for key, value in
         {"ask": "ask", "grab": "grab"}.items()]
        + [fact("relic", key) for key in TEMPTATIONS]
    )


def asp_safe_relics() -> set[tuple]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "safe_relic"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--elder")
    parser.add_argument("--temptation", choices=tuple(TEMPTATIONS))
    parser.add_argument("--approach", choices=APPROACHES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    elder = args.elder or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(
        hero=hero,
        elder=elder,
        temptation=args.temptation or rng.choice(tuple(TEMPTATIONS)),
        approach=args.approach or rng.choice(APPROACHES),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if not asp_safe_relics() == set((key,) for key in TEMPTATIONS):
        raise StoryError("ASP did not identify every relic as safe when approached by asking.")
    count = 0
    for temptation in TEMPTATIONS:
        for approach in APPROACHES:
            sample = generate(StoryParams(temptation=temptation, approach=approach))
            check_sample(sample)
            count += 1
    print(f"OK: {count} story states; ASP agrees on safe approaches.")


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
            print(json.dumps(sorted(asp_safe_relics())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            params_list = [
                StoryParams(hero=args.hero or "Luna",
                            elder=args.elder or "Mara",
                            temptation=temptation,
                            approach=approach,
                            seed=args.seed)
                for temptation in TEMPTATIONS
                for approach in APPROACHES
            ]
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
