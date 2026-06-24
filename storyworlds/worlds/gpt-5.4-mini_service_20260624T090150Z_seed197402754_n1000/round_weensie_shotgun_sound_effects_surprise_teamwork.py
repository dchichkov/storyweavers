#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/round_weensie_shotgun_sound_effects_surprise_teamwork.py
===============================================================================================

A small folk-tale story world about a round weensie helper, a noisy shotgun,
sound effects, surprise, and teamwork.

Seed tale:
---
In a little village by a silver pond lived a round weensie mouse named Pip.
Pip loved helping the old miller sing to the ducks at dawn. One morning the
miller found fresh holes in the grain sacks and frowned. "Bang-bang!" went the
old shotgun hanging above the door when it slipped off a nail, and everyone
jumped.

The village thought a beast must be loose in the barn. But the surprise was a
bursty little pop from a sack of beans that Pip had been carrying. The beans
had spilled, the ducks had pecked, and the whole barn had become noisy with
quacks and feet. Pip called the baker, the miller, and the washerwoman. Together
they mended the sacks, sorted the grain, and set a tin pot to tap-tap-tap
whenever the door rattled. Soon the barn was calm again, and everyone laughed
at the big fear that had turned out small.

World idea:
---
- "round" and "weensie" are physical/social descriptors of the hero.
- "shotgun" is an old village heirloom that makes a startling sound when it
  bumps or slips, but it is not used for harm in the story.
- Sound effects matter as cues in the plot and in the surprise turn.
- Teamwork resolves the trouble: several villagers each do one small task.
- Meter-like state tracks tangible changes; meme-like state tracks fear, relief,
  and shared delight.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CharacterSpec:
    id: str
    kind: str
    label: str
    phrase: str
    gender: str
    size: str
    role: str
    traits: tuple[str, ...] = ()
    plural: bool = False


@dataclass(frozen=True)
class ObjectSpec:
    id: str
    label: str
    phrase: str
    kind: str
    owner: str = ""
    plural: bool = False
    fragile: bool = False


@dataclass(frozen=True)
class PlaceSpec:
    id: str
    label: str
    phrase: str


@dataclass(frozen=True)
class StoryParams:
    place: str
    hero: str
    helper: str
    trouble: str
    seed: Optional[int] = None


PLACES = {
    "village": PlaceSpec("village", "the village green", "the village green"),
    "mill": PlaceSpec("mill", "the old mill", "the old mill by the pond"),
    "barn": PlaceSpec("barn", "the barn", "the barn with the creaky door"),
}

CHARACTERS = {
    "pip": CharacterSpec(
        id="pip",
        kind="character",
        label="Pip",
        phrase="a round weensie mouse",
        gender="they",
        size="weensie",
        role="helper",
        traits=("round", "weensie", "cheerful"),
    ),
    "miller": CharacterSpec(
        id="miller",
        kind="character",
        label="Martha",
        phrase="the miller",
        gender="she",
        size="grown",
        role="keeper",
        traits=("kind", "steady"),
    ),
    "baker": CharacterSpec(
        id="baker",
        kind="character",
        label="Bram",
        phrase="the baker",
        gender="he",
        size="grown",
        role="maker",
        traits=("busy", "gentle"),
    ),
    "washer": CharacterSpec(
        id="washer",
        kind="character",
        label="Nell",
        phrase="the washerwoman",
        gender="she",
        size="grown",
        role="mender",
        traits=("quick", "helpful"),
    ),
}

OBJECTS = {
    "shotgun": ObjectSpec(
        id="shotgun",
        label="shotgun",
        phrase="the old shotgun on its peg",
        kind="thing",
    ),
    "grain": ObjectSpec(
        id="grain",
        label="grain sacks",
        phrase="two grain sacks",
        kind="thing",
        plural=True,
        fragile=True,
    ),
    "beans": ObjectSpec(
        id="beans",
        label="bean sack",
        phrase="a little sack of beans",
        kind="thing",
        fragile=True,
    ),
    "tinpot": ObjectSpec(
        id="tinpot",
        label="tin pot",
        phrase="a bright tin pot",
        kind="thing",
    ),
}


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str
    label: str
    phrase: str = ""
    traits: tuple[str, ...] = ()
    plural: bool = False
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.id == "pip":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.id in {"miller", "washer"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.id == "baker":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: PlaceSpec
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def is_reasonable(params: StoryParams) -> bool:
    return params.place in PLACES and params.hero in CHARACTERS and params.helper in CHARACTERS and params.trouble in {"shotgun", "beans"}


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(pip). helper(miller). helper(baker). helper(washer).
place(village). place(mill). place(barn).

size(pip,weensie). shape(pip,round).
object(shotgun). object(grain). object(beans). object(tinpot).

trouble(shotgun). trouble(beans).

surprise(shotgun) :- trouble(shotgun).
sound_effect(shotgun,bang).
sound_effect(beans,pop).

teamwork(miller,pip).
teamwork(baker,pip).
teamwork(washer,pip).

reasonable(P,H,He,T) :- place(P), hero(H), helper(He), trouble(T), teamwork(He,H).
#show reasonable/4.
#show surprise/1.
#show sound_effect/2.
"""


def asp_facts() -> str:
    from storyworlds import asp
    lines = [
        asp.fact("hero", "pip"),
        asp.fact("helper", "miller"),
        asp.fact("helper", "baker"),
        asp.fact("helper", "washer"),
        asp.fact("place", "village"),
        asp.fact("place", "mill"),
        asp.fact("place", "barn"),
        asp.fact("size", "pip", "weensie"),
        asp.fact("shape", "pip", "round"),
        asp.fact("object", "shotgun"),
        asp.fact("object", "grain"),
        asp.fact("object", "beans"),
        asp.fact("object", "tinpot"),
        asp.fact("trouble", "shotgun"),
        asp.fact("trouble", "beans"),
        asp.fact("surprise", "shotgun"),
        asp.fact("sound_effect", "shotgun", "bang"),
        asp.fact("sound_effect", "beans", "pop"),
        asp.fact("teamwork", "miller", "pip"),
        asp.fact("teamwork", "baker", "pip"),
        asp.fact("teamwork", "washer", "pip"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    from storyworlds import asp
    model = asp.one_model(asp_program("#show reasonable/4."))
    asp_set = set(asp.atoms(model, "reasonable"))
    py_set = {(p, "pip", helper, "shotgun") for p in PLACES if helper in {"miller", "baker", "washer"} and p == "village"}
    if ("village", "pip", "miller", "shotgun") in asp_set:
        print("OK: ASP model produced the expected reasonable story family.")
        return 0
    print("ASP verification failed.")
    print(sorted(asp_set))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    world.add(Entity("pip", "character", "Pip", CHARACTERS["pip"].phrase, CHARACTERS["pip"].traits))
    world.add(Entity("miller", "character", "Martha", CHARACTERS["miller"].phrase, CHARACTERS["miller"].traits))
    world.add(Entity("baker", "character", "Bram", CHARACTERS["baker"].phrase, CHARACTERS["baker"].traits))
    world.add(Entity("washer", "character", "Nell", CHARACTERS["washer"].phrase, CHARACTERS["washer"].traits))
    world.add(Entity("shotgun", "thing", "shotgun", OBJECTS["shotgun"].phrase))
    world.add(Entity("grain", "thing", "grain sacks", OBJECTS["grain"].phrase, plural=True))
    world.add(Entity("beans", "thing", "bean sack", OBJECTS["beans"].phrase))
    world.add(Entity("tinpot", "thing", "tin pot", OBJECTS["tinpot"].phrase))
    return world


def tell_story(world: World, params: StoryParams) -> None:
    pip = world.get("pip")
    miller = world.get("miller")
    baker = world.get("baker")
    washer = world.get("washer")

    pip.meters["help"] = 1
    pip.memes["joy"] = 1
    world.say(
        f"In {world.place.phrase}, there lived {pip.phrase}, "
        f"as round and weensie as a berry and as quick as a blink."
    )
    world.say(
        f"{pip.label} loved helping {miller.pronoun('possessive')} mill and listening "
        f"for the little sounds of morning."
    )

    world.para()
    if params.trouble == "shotgun":
        world.facts["sound"] = "bang"
        world.facts["surprise"] = True
        world.say(
            f"One morning, the old shotgun on its peg gave a sudden bang! and a crack."
        )
        pip.memes["startle"] = 1
        miller.memes["fear"] = 1
        world.say(
            f"Everyone jumped, and even the ducks cried, \"Quack! Quack!\" at the sharp sound."
        )
        world.say(
            f"The village thought some giant beast must be hiding by the barn door."
        )
    else:
        world.facts["sound"] = "pop"
        world.facts["surprise"] = True
        world.say(
            f"Then the bean sack gave a tiny pop! and a cheerful rattle."
        )
        pip.memes["startle"] = 1
        world.say(
            f"That surprise sound made the chickens flap and the ducks answer, \"Peep-peep!\""
        )

    world.para()
    world.say(
        f"But the surprise was not a beast at all."
    )
    world.say(
        f"It was {pip.pronoun('subject')} trying to carry {world.get('beans').phrase}, "
        f"and the little sack had burst open."
    )
    world.get("beans").meters["open"] = 1
    world.get("grain").meters["scattered"] = 1
    world.say(
        f"Beans rolled like marbles, the ducks pecked at them, and the grain sacks slipped askew."
    )

    world.para()
    world.say(
        f"Then {pip.label} called, \"Martha, Bram, Nell—come quick!\""
    )
    pip.memes["brave"] = 1
    miller.memes["resolve"] = 1
    baker.memes["resolve"] = 1
    washer.memes["resolve"] = 1
    world.say(
        f"Together they worked as a team: {miller.label} tied the torn sacks, "
        f"{baker.label} gathered the beans, and {washer.label} set {world.get('tinpot').phrase} "
        f"by the door to go ting-ting-ting if it shook."
    )
    world.say(
        f"Pip tucked the last bean into place and smiled at the tidy floor."
    )

    world.para()
    pip.memes["joy"] += 2
    miller.memes["joy"] = 1
    baker.memes["joy"] = 1
    washer.memes["joy"] = 1
    world.say(
        f"At dusk, the barn was calm again, and the only sounds were a soft hum, a friendly chirp, "
        f"and the tinny ting of the little pot."
    )
    world.say(
        f"The round weensie mouse had not beaten the trouble alone; "
        f"{pip.pronoun('subject').capitalize()} had brought everyone together, and that was the true folk-tale magic."
    )

    world.facts.update(
        hero=pip,
        helpers=[miller, baker, washer],
        place=world.place,
        trouble=params.trouble,
        sound=world.facts["sound"],
        surprise=world.facts["surprise"],
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a folk-tale for a young child about a round weensie helper, a sudden sound, and a kind surprise.',
        f"Tell a short story set at {world.place.label} where the word 'shotgun' appears as a startling sound cue, not as a threat.",
        'Write a gentle story that includes bang! and pop! and ends with everyone working together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    pip = world.get("pip")
    miller = world.get("miller")
    baker = world.get("baker")
    washer = world.get("washer")
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {pip.phrase}, a round weensie mouse named Pip.",
        ),
        QAItem(
            question="What sound surprised everyone at the mill?",
            answer=f"The old shotgun made a sudden bang! and crack!, which startled everyone.",
        ),
        QAItem(
            question="What was the surprise in the story?",
            answer="The surprise was that the scary noise came from a small problem, not from a beast.",
        ),
        QAItem(
            question="How did the village fix the trouble?",
            answer=(
                f"{miller.label}, {baker.label}, and {washer.label} worked together to mend the sacks, "
                f"gather the spilled beans, and make the barn tidy again."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a special noise, like bang! or pop!, that helps tell a story what is happening.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do different jobs together to finish a job.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes people stop and look around.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"{e.id}: {e.kind} {e.label} {' '.join(bits)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk-tale story world about a round weensie helper and a surprise sound.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero", choices=sorted(CHARACTERS), default="pip")
    ap.add_argument("--helper", choices=["miller", "baker", "washer"])
    ap.add_argument("--trouble", choices=["shotgun", "beans"])
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
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or "pip"
    helper = args.helper or rng.choice(["miller", "baker", "washer"])
    trouble = args.trouble or rng.choice(["shotgun", "beans"])
    params = StoryParams(place=place, hero=hero, helper=helper, trouble=trouble)
    if not is_reasonable(params):
        raise StoryError("The chosen setup does not make a calm folk tale.")
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams("village", "pip", "miller", "shotgun"),
            StoryParams("mill", "pip", "baker", "beans"),
            StoryParams("barn", "pip", "washer", "shotgun"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        samples = []
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
