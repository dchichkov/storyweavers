#!/usr/bin/env python3
"""
A child-facing superhero storyworld about encouraging friends in a castle.

The small domain uses rhyme, transformation, and reconciliation as world
mechanics: a worried hero rhymes a brave message, a broken castle beacon is
transformed through teamwork, and two friends reconcile after a misunderstanding.
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
class Setting:
    id: str
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    opening: str
    danger: str
    misunderstanding: str
    clue: str
    first_idea: str
    rhyme: str
    transformation: str
    reconciliation: str
    proof: str
    ending: str


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    power: str
    companion: str
    challenge: str = ""
    telling: str = ""
    seed: Optional[int] = None


SETTINGS = {
    "castle": Setting(
        id="castle",
        place="the moonlit castle",
        affords={"beacon_rescue"},
    )
}

ACTIVITIES = {
    "beacon_rescue": {
        "label": "the beacon rescue",
        "hazard": "a darkened beacon",
        "goal": "restore the castle's guiding light",
    }
}

PRIZES = {
    "hope": {
        "label": "hope for the castle",
        "type": "hope",
    }
}

HEROES = [
    ("Luna", "starlight"),
    ("Milo", "super-strength"),
    ("Zara", "wind-speed"),
    ("Theo", "glowing shields"),
    ("Nia", "kindness beams"),
]

COMPANIONS = ["Pip", "Rae", "Sol", "Tess", "Bo"]
POWERS = ["starlight", "super-strength", "wind-speed", "glowing shields", "kindness beams"]
TELLINGS = ["rhyme_first", "clue_first", "friend_first", "action_first", "quiet_build"]

CHALLENGES = {
    "cracked_beacon": Challenge(
        id="cracked_beacon",
        opening="At sunset, the castle's beacon cracked and its golden light went out.",
        danger="Without the beacon, travelers could miss the safe bridge below the castle.",
        misunderstanding="Luna thought her companion had hidden the repair crystal because he was angry with her.",
        clue="A trail of silver dust showed that the crystal had rolled behind the old tapestry instead.",
        first_idea="Luna wanted to lift the whole tapestry at once, but it was tangled around a sleepy bell rope.",
        rhyme="Be bright, be brave, and help a friend; together we can mend the bend!",
        transformation="They changed a fallen shield, three ribbons, and the repair crystal into a shining lantern frame.",
        reconciliation="Luna apologized for guessing too quickly, and her companion forgave her while adding the final ribbon.",
        proof="The restored beacon sent a warm beam across the bridge, and every traveler found the castle gate.",
        ending="The two friends stood shoulder to shoulder as the castle glowed like a friendly star.",
    ),
    "stormy_tower": Challenge(
        id="stormy_tower",
        opening="A storm rattled the castle tower, and a gust carried the beacon's bright lens into the bell room.",
        danger="The dark tower made the castle paths hard to see in the rain.",
        misunderstanding="Luna believed her companion had taken the lens without asking.",
        clue="A tiny bell chimed from the stairwell, proving the wind had pushed the lens there.",
        first_idea="Luna started to race up the stairs, but wet steps made rushing dangerous.",
        rhyme="Slow feet, clear eyes, climb with care; brave friends bring bright light there!",
        transformation="They transformed a long banner into a safe sling and pulled the lens gently from the stairwell.",
        reconciliation="Luna admitted she had blamed her friend, and her friend said the storm had frightened him too.",
        proof="The lens clicked into place and painted a bright path through the rain.",
        ending="The friends shared a dry cloak beneath the tower while the castle shone below.",
    ),
    "sleeping_guardian": Challenge(
        id="sleeping_guardian",
        opening="The castle's friendly stone guardian fell asleep beside the beacon switch.",
        danger="The unlit switch left the castle courtyard dark just as visitors arrived.",
        misunderstanding="Luna thought her companion had used a spell that made the guardian sleep.",
        clue="A lavender petal on the guardian's nose revealed that the garden breeze had carried sleepy pollen.",
        first_idea="Luna nearly shouted, but the loud sound might have startled the stone guardian.",
        rhyme="Gentle hands and voices low; wake with care and let light grow.",
        transformation="The friends transformed a soft song, a feather fan, and a warm cup of tea into a gentle waking plan.",
        reconciliation="Luna thanked her companion for noticing the petal, and they agreed to ask questions before blaming anyone.",
        proof="The guardian opened one stone eye, pressed the switch, and lit every castle window.",
        ending="The friends laughed softly while the guardian gave them a careful stone high-five.",
    ),
    "missing_flag": Challenge(
        id="missing_flag",
        opening="On festival morning, the castle's friendship flag vanished from the highest pole.",
        danger="The empty pole made the visiting villages think the castle did not welcome them.",
        misunderstanding="Luna suspected her companion had taken the flag to win a flying contest.",
        clue="A red thread caught on a gargoyle showed that a chimney swallow had carried the flag to its nest.",
        first_idea="Luna reached toward the nest, but she stopped when she saw two tiny chicks inside.",
        rhyme="Safe for birds and kind to all; we find a way that helps, not harms, or falls.",
        transformation="The friends transformed spare cloth into a second flag while a keeper returned the first one safely.",
        reconciliation="Luna told her companion she was sorry for suspecting him, and he shared the new flag design.",
        proof="Two flags waved together above the castle, welcoming every village.",
        ending="The festival began beneath twin flags, one fluttering for friendship and one for home.",
    ),
}


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.events: list[str] = []

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld: encourage friends in a castle through rhyme, transformation, and reconciliation."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--activity", choices=ACTIVITIES)
    parser.add_argument("--prize", choices=PRIZES)
    parser.add_argument("--name")
    parser.add_argument("--power", choices=POWERS)
    parser.add_argument("--companion")
    parser.add_argument("--challenge", choices=CHALLENGES)
    parser.add_argument("--telling", choices=TELLINGS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def validate_params(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("This story belongs in the castle.")
    if params.activity not in ACTIVITIES:
        raise StoryError("The castle activity must be the beacon rescue.")
    if params.prize not in PRIZES:
        raise StoryError("The castle's prize must be hope.")
    if params.name == params.companion:
        raise StoryError("The hero and companion must be different characters.")
    if params.challenge not in CHALLENGES:
        raise StoryError("That castle challenge is not available.")


def tell(params: StoryParams, rng: random.Random) -> World:
    validate_params(params)
    setting = SETTINGS[params.place]
    challenge = CHALLENGES[params.challenge]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="superhero",
        label=params.name,
        memes={"courage": 1.0, "encouragement": 0.0, "trust": 0.5},
    ))
    companion = world.add(Entity(
        id=params.companion,
        kind="character",
        type="friend",
        label=params.companion,
        memes={"trust": 0.5, "worry": 0.0},
    ))
    beacon = world.add(Entity(
        id="castle_beacon",
        kind="thing",
        type="beacon",
        label="the castle beacon",
        meters={"light": 0.0, "danger": 1.0},
    ))
    hope = world.add(Entity(
        id="hope",
        kind="thing",
        type="hope",
        label="hope",
        memes={"shared": 0.0},
    ))

    openings = [
        f"In the moonlit castle, {params.name}, a superhero with {params.power}, watched the towers sparkle.",
        f"{params.name} protected the moonlit castle with {params.power}, while {params.companion} hurried beside the drawbridge.",
        f"The moonlit castle was preparing for a bright evening when {params.name}, a superhero with {params.power}, heard trouble above.",
    ]
    world.say(rng.choice(openings))
    world.say(challenge.opening)
    world.para()

    world.say(challenge.danger)
    if params.telling in {"clue_first", "quiet_build"}:
        world.say(challenge.clue)
        world.say(challenge.misunderstanding)
    else:
        world.say(challenge.misunderstanding)
        world.say(f'"Wait," said {params.companion}. "Let us look for a clue before we decide what happened."')
        world.say(challenge.clue)
    world.facts["clue_found"] = True
    world.events.append("clue_found")
    world.para()

    world.say(challenge.first_idea)
    world.say(f'"I can do this alone," said {params.name}.')
    world.say(
        f'"You do not have to," said {params.companion}. "You encourage me, and I can encourage you."'
    )
    world.say(f'"Then let us try together," said {params.name}.')
    world.facts["dialogue_changed_plan"] = True
    hero.memes["encouragement"] = 1.0
    companion.memes["encouragement"] = 1.0
    world.events.append("encouragement_shared")
    world.para()

    world.say(f"{params.name} spoke the brave rhyme aloud: “{challenge.rhyme}”")
    world.say("The words gave the friends a steady rhythm instead of a hurried rush.")
    world.facts["rhyme_used"] = True
    world.events.append("rhyme_used")
    world.para()

    world.say(challenge.transformation)
    world.say("The castle problem did not vanish by magic alone; the friends changed what they had into something useful.")
    beacon.meters["light"] = 1.0
    beacon.meters["danger"] = 0.0
    world.facts["transformed"] = True
    world.events.append("transformation_complete")
    world.para()

    world.say(challenge.reconciliation)
    hero.memes["trust"] = 1.0
    companion.memes["trust"] = 1.0
    hope.memes["shared"] = 1.0
    world.facts["reconciled"] = True
    world.events.append("reconciliation_complete")
    world.para()

    world.say(challenge.proof)
    world.say(challenge.ending)
    world.facts.update(
        hero=hero,
        companion=companion,
        beacon=beacon,
        hope=hope,
        challenge=challenge,
        setting=setting,
        power=params.power,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    challenge = world.facts["challenge"]
    return [
        f"Write a superhero story about {hero.id} encouraging {companion.id} in a castle.",
        f"Use a rhyme to help two friends transform a castle problem into a solution.",
        f"Show reconciliation after a misunderstanding, with a concrete ending image: {challenge.proof}",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    challenge: Challenge = world.facts["challenge"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the superhero in the castle story?",
            answer=f"{hero.id} was the superhero, using {world.facts['power']} to help protect the castle.",
        ),
        QAItem(
            question=f"What danger did {hero.id} discover?",
            answer=challenge.danger,
        ),
        QAItem(
            question=f"What clue changed the friends' understanding?",
            answer=challenge.clue,
        ),
        QAItem(
            question=f"How did {hero.id} and {companion.id} encourage each other?",
            answer=f"They spoke honestly and reminded each other that they could work together: “{challenge.rhyme}”",
        ),
        QAItem(
            question="What transformation solved the castle problem?",
            answer=challenge.transformation,
        ),
        QAItem(
            question="How did the friends reconcile?",
            answer=challenge.reconciliation,
        ),
        QAItem(
            question="What proved that the castle was safe or welcoming again?",
            answer=challenge.proof,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to encourage someone?",
            answer="To encourage someone means to give kind words or help that makes the person feel ready to keep trying.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pattern of words with matching or similar ending sounds.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a meaningful change from one form or condition into another.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means repairing a relationship after a disagreement by listening, apologizing, forgiving, and choosing trust again.",
        ),
        QAItem(
            question="Why can teamwork help in a difficult situation?",
            answer="Teamwork can combine different ideas and strengths while helping people feel less alone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.id:16} ({entity.type:10}) meters={meters} memes={memes}"
        )
    lines.append(f"  events: {', '.join(world.events)}")
    return "\n".join(lines)


ASP_RULES = r"""
encourages(H, F) :- superhero(H), friend(F), rhyme_used, dialogue_changed_plan.
transformed(B) :- beacon(B), teamwork, materials_ready.
reconciled(H, F) :- encourages(H, F), apology, forgiveness.
safe_beacon(B) :- transformed(B), reconciled(_, _).
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("setting", "castle"),
        asp.fact("affords", "castle", "beacon_rescue"),
        asp.fact("activity", "beacon_rescue"),
        asp.fact("prize", "hope"),
        asp.fact("superhero", "hero"),
        asp.fact("friend", "companion"),
        asp.fact("beacon", "castle_beacon"),
        asp.fact("rhyme_used"),
        asp.fact("dialogue_changed_plan"),
        asp.fact("teamwork"),
        asp.fact("materials_ready"),
        asp.fact("apology"),
        asp.fact("forgiveness"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show safe_beacon/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_validity() -> bool:
    import asp

    model = asp.one_model(asp_program("#show safe_beacon/1."))
    return ("castle_beacon",) in asp.atoms(model, "safe_beacon")


def asp_verify() -> int:
    if not asp_validity():
        print("MISMATCH: ASP castle model did not reach a safe beacon.")
        return 1
    rng = random.Random(12345)
    params = resolve_params(build_parser().parse_args([]), rng)
    sample = generate(params)
    required = ["castle", "encourage", "rhyme", "transform", "reconcil"]
    lowered = sample.story.lower()
    missing = [word for word in required if word not in lowered]
    if missing:
        print(f"MISMATCH: generated story is missing {', '.join(missing)}.")
        return 1
    if not sample.world or not sample.world.facts.get("reconciled"):
        print("MISMATCH: Python story did not reconcile the friends.")
        return 1
    print("OK: Python and ASP both describe a transformed, reconciled castle rescue.")
    return 0


CURATED = [
    StoryParams(
        place="castle",
        activity="beacon_rescue",
        prize="hope",
        name="Luna",
        power="starlight",
        companion="Pip",
        challenge="cracked_beacon",
        telling="rhyme_first",
        seed=17,
    ),
    StoryParams(
        place="castle",
        activity="beacon_rescue",
        prize="hope",
        name="Zara",
        power="wind-speed",
        companion="Rae",
        challenge="stormy_tower",
        telling="clue_first",
        seed=31,
    ),
    StoryParams(
        place="castle",
        activity="beacon_rescue",
        prize="hope",
        name="Nia",
        power="kindness beams",
        companion="Sol",
        challenge="sleeping_guardian",
        telling="friend_first",
        seed=43,
    ),
    StoryParams(
        place="castle",
        activity="beacon_rescue",
        prize="hope",
        name="Milo",
        power="super-strength",
        companion="Tess",
        challenge="missing_flag",
        telling="action_first",
        seed=59,
    ),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "castle":
        raise StoryError("This superhero storyworld is set in the castle.")
    if args.activity and args.activity != "beacon_rescue":
        raise StoryError("The castle story must center on restoring its beacon.")
    if args.prize and args.prize != "hope":
        raise StoryError("The story's prize is hope for the castle.")

    if args.name:
        name = args.name
        known = next((power for known_name, power in HEROES if known_name == name), None)
        power = args.power or known or rng.choice(POWERS)
    elif args.power:
        power = args.power
        name = next((known_name for known_name, known_power in HEROES if known_power == power), rng.choice(HEROES)[0])
    else:
        name, power = rng.choice(HEROES)

    companion = args.companion or rng.choice([item for item in COMPANIONS if item != name])
    challenge = args.challenge or rng.choice(sorted(CHALLENGES))
    telling = args.telling or rng.choice(TELLINGS)

    params = StoryParams(
        place="castle",
        activity="beacon_rescue",
        prize="hope",
        name=name,
        power=power,
        companion=companion,
        challenge=challenge,
        telling=telling,
    )
    validate_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    detail_seed = params.seed
    if detail_seed is None:
        detail_seed = sum(ord(char) for char in f"{params.name}:{params.companion}:{params.challenge}:{params.telling}")
    world = tell(params, random.Random(detail_seed ^ 0xC457))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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

    if args.verify:
        raise SystemExit(asp_verify())

    if args.show_asp:
        print(asp_program())
        return

    if args.asp:
        print("ASP castle model:")
        print("  safe_beacon(castle_beacon)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 30, 30):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
