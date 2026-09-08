#!/usr/bin/env python3
"""The Light Piper: a superhero story about magical tenure, conflict, and change."""

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
    piper: str = "Piper"
    threat: str = "shadow"
    power: str = "light"
    seed: int = 777


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question: str = "",
                cause: str = "", result: str = ""):
        self.history.append(Event(
            kind=kind,
            text=text,
            question=question,
            cause=cause,
            result=result,
            state=self.snapshot(),
        ))

    def speak(self, speaker: str, text: str, listener: str = ""):
        name = self.entities[speaker].label
        target = f" to {self.entities[listener].label}" if listener else ""
        punctuation = "" if text.endswith((".", "!", "?")) else "."
        self.history.append(Event(
            kind="speech",
            text=f'{name}{target} said, "{text}"{punctuation}',
            state=self.snapshot(),
        ))

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(event.question, f"{event.cause} {event.result}")
                for event in self.history
                if event.question
            ],
            world_qa=[
                QAItem(
                    "What gives the Light Piper power?",
                    "The Light Piper's magic turns brave music into a warm beam of light.",
                ),
                QAItem(
                    "What does tenure mean in this story?",
                    "Tenure means the town promises that the old lighthouse will belong to its keeper for a long time.",
                ),
            ],
            world=self,
        )


PROMPT = (
    "Write a dialogue-rich superhero story about Luna and a magical piper "
    "protecting a lighthouse whose tenure is threatened by a living shadow."
)

NAMES = ("Luna", "Piper", "Mira", "Nova", "Sol", "Tessa")
THREATS = {
    "shadow": ("the Hollow Shadow", "a cold black cloud", "fear"),
    "storm": ("the Thunder Storm", "a wall of violet rain", "panic"),
}
POWERS = {
    "light": ("light", "a golden beam"),
    "music": ("music", "a ribbon of shining notes"),
}


def validate_params(params: StoryParams):
    if params.hero == params.piper:
        raise StoryError("The superhero and piper must have different names.")
    for name in (params.hero, params.piper):
        if not re.fullmatch(r"[A-Z][a-z]+", name):
            raise StoryError("Names must be simple capitalized words.")
    if params.threat not in THREATS:
        raise StoryError("Unknown threat.")
    if params.power not in POWERS:
        raise StoryError("Unknown magical power.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["hero"] = Entity(
        id="hero",
        label=params.hero,
        kind="superhero",
        location="lighthouse balcony",
        meters={"courage": 0.6, "light": 0.0, "strength": 1.0},
        memes={"hope": 0.6, "trust": 0.5},
    )
    world.entities["piper"] = Entity(
        id="piper",
        label=params.piper,
        kind="magical piper",
        location="lighthouse stair",
        meters={"breath": 1.0, "music": 1.0},
        memes={"hope": 0.7, "trust": 0.5},
    )
    world.entities["lighthouse"] = Entity(
        id="lighthouse",
        label="Beacon Tower",
        kind="lighthouse",
        location="Mooncliff",
        meters={"lamp": 1.0, "tenure": 1.0, "shield": 0.0},
        memes={"belonging": 1.0},
    )
    world.entities["shadow"] = Entity(
        id="shadow",
        label=THREATS[params.threat][0],
        kind="threat",
        location="lighthouse lantern room",
        meters={"darkness": 1.0, "fear": 1.0, "harm": 0.0},
        memes={"anger": 1.0},
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"]
    piper = world.entities["piper"]
    tower = world.entities["lighthouse"]
    shadow = world.entities["shadow"]
    h = hero.label
    p = piper.label
    threat_name, threat_image, threat_feeling = THREATS[params.threat]
    power_name, power_image = POWERS[params.power]

    world.narrate(
        "beginning",
        f"On Mooncliff Hill, {h} guarded Beacon Tower, a lighthouse promised to its keeper by "
        "a special tenure. The promise let the light shine for every boat below.",
    )
    world.speak("hero", f"The tower is ours to protect, and its light must stay bright.", "piper")
    world.speak("piper", f"I hear something climbing the stairs. It sounds like {threat_feeling}.", "hero")
    world.narrate(
        "threat",
        f"A {threat_image} curled around the lantern room. The {threat_name} had come to swallow "
        "the beacon and break the tower's tenure.",
        question="Why did the heroes need to defend the lighthouse?",
        cause="The lighthouse's tenure promised that its light would remain a safe home for the town.",
        result=f"The {threat_name} tried to darken the beacon and take that promise away.",
    )

    world.speak("hero", f"I can push it back with my {power_name} power.", "piper")
    world.speak("piper", "You can push darkness, but you cannot chase away the fear inside it.", "hero")
    hero.meters["courage"] -= 0.2
    shadow.meters["harm"] += 0.2
    world.narrate(
        "conflict",
        f"{h} leaped toward the {threat_name}, but the shadow split into three smoky claws. "
        f"Each claw grew larger when {h} felt {threat_feeling}.",
        question="Why did Luna's first attack fail?",
        cause=f"The {threat_name} grew stronger when Luna fought with fear and anger.",
        result="Her first burst of power scattered the shadow but did not drive it away.",
    )
    world.speak("hero", "Then I need a different plan. What can your pipe do?", "piper")
    world.speak("piper", "It can call the brave part of a frightened heart. Will you listen with me?", "hero")
    hero.memes["trust"] = 0.8
    world.narrate(
        "turn",
        f"{p} lifted a silver pipe. Instead of playing a loud battle tune, {p.lower()} played "
        "three gentle notes that sounded like footsteps coming home.",
        question="What changed the heroes' plan?",
        cause=f"Piper explained that gentle music could reach the fear feeding the {threat_name}.",
        result=f"Luna stopped attacking alone and agreed to join the piper's magic.",
    )
    world.speak("hero", "I will listen first. Then I will shine where the music leads.", "piper")
    world.speak("piper", "Good. Follow the warm note, not the loudest one.", "hero")

    if params.power == "light":
        hero.meters["light"] = 1.0
        tower.meters["shield"] = 1.0
        transformation = (
            f"{h}'s hands changed into small suns. The new light did not burn the shadow; "
            "it showed a tiny frightened moth hiding inside it."
        )
    else:
        hero.meters["light"] = 0.8
        tower.meters["shield"] = 1.0
        transformation = (
            f"{h}'s cape filled with shining notes. The music and the cape became a bridge "
            "between the dark cloud and the waiting lantern."
        )
    world.narrate(
        "transformation",
        transformation,
        question="How did Luna's superhero power change?",
        cause=f"Luna trusted Piper's music and used {power_name} to follow its gentle rhythm.",
        result=f"Her magic transformed into {power_image} that could reveal rather than hurt.",
    )
    world.speak("hero", "I see you. You do not have to hide in the dark.", "piper")
    world.speak("piper", "Let the light give you a place beside us.", "hero")
    shadow.meters["darkness"] = 0.0
    shadow.meters["fear"] = 0.0
    shadow.meters["harm"] = 0.0
    shadow.location = "lighthouse garden"
    shadow.memes["anger"] = 0.0
    world.narrate(
        "resolution",
        f"The little moth flew into the garden, where it became a bright blue lantern-bug. "
        f"The {threat_name} was gone, and the lighthouse lamp shone through the night.",
        question="How did the heroes defeat the shadow?",
        cause="Luna used transformed light while Piper offered the frightened creature a safe place.",
        result="The shadow changed into a lantern-bug instead of being destroyed.",
    )
    tower.meters["lamp"] = 1.0
    tower.meters["tenure"] = 1.0
    hero.memes["hope"] = 1.0
    piper.memes["hope"] = 1.0
    world.speak("hero", "The tower still belongs to the people who need its light.", "piper")
    world.speak("piper", "And now the garden has a new keeper.", "hero")
    world.narrate(
        "ending",
        f"{h} and {p} stood beneath the beacon as the lantern-bug blinked below. "
        "The old tenure held firm, not because the tower was guarded by force, "
        "but because its light made room for one more changed heart.",
        question="What proved that the lighthouse was safe again?",
        cause="The heroes protected the tenure and transformed the shadow into a helpful lantern-bug.",
        result="The beacon remained bright while the new lantern-bug guarded the garden.",
    )

    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if world.entities["lighthouse"].meters["tenure"] != 1.0:
        raise StoryError("The lighthouse tenure must survive the conflict.")
    if world.entities["lighthouse"].meters["lamp"] != 1.0:
        raise StoryError("The ending must restore the beacon light.")
    if world.entities["shadow"].meters["darkness"] != 0.0:
        raise StoryError("The threat must undergo a real transformation.")
    speeches = [event for event in world.history if event.kind == "speech"]
    if len(speeches) < 8:
        raise StoryError("The story needs a sustained dialogue exchange.")
    if not any("Piper" in event.text and "Luna" in event.text for event in speeches):
        raise StoryError("The heroes must speak directly to one another.")
    if len(sample.story_qa) < 4:
        raise StoryError("The story needs causal grounded questions and answers.")


ASP_RULES = """
protected(T) :- tenure(T), light(T), transformed(T).
safe(T) :- protected(T).
#show safe/1.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join([
        fact("tenure", "beacon_tower"),
        fact("light", "beacon_tower"),
        fact("transformed", "hollow_shadow"),
    ])


def asp_safe() -> set[tuple]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "safe"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--piper")
    parser.add_argument("--threat", choices=tuple(THREATS))
    parser.add_argument("--power", choices=tuple(POWERS))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    piper = args.piper or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(
        hero=hero,
        piper=piper,
        threat=args.threat or rng.choice(tuple(THREATS)),
        power=args.power or rng.choice(tuple(POWERS)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if asp_safe() != {("beacon_tower",)}:
        raise StoryError("ASP did not recognize the protected beacon.")
    tested = 0
    for threat in THREATS:
        for power in POWERS:
            sample = generate(StoryParams(threat=threat, power=power))
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; ASP/Python protection parity confirmed.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""):
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
            print(json.dumps(sorted(asp_safe())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            params_list = [
                StoryParams(
                    hero=args.hero or "Luna",
                    piper=args.piper or "Piper",
                    threat=threat,
                    power=power,
                    seed=args.seed,
                )
                for threat in THREATS
                for power in POWERS
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
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
