#!/usr/bin/env python3
from __future__ import annotations

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
    label: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    label: str
    sound: str
    hazard: str


@dataclass
class Quest:
    id: str
    title: str
    object_label: str
    clue: str
    obstacle: str
    turn: str
    resolution: str
    proof: str
    lesson: str


@dataclass
class World:
    setting: Setting
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


SETTINGS = {
    "moonlit_cove": Setting(
        id="moonlit_cove",
        label="Moonlit Cove",
        affords={"clam_quest"},
    )
}

ACTIVITIES = {
    "clam_quest": Activity(
        id="clam_quest",
        label="search for the bell clam",
        sound="clonk-clonk",
        hazard="a reef of sharp shells",
    )
}

QUESTS = {
    "bell_clam": Quest(
        id="bell_clam",
        title="The Quest of the Bell Clam",
        object_label="the silver bell clam",
        clue="a tiny silver note floated from beneath the pier",
        obstacle="the tide had covered the safe stepping stones, and dark waves slapped against a sharp shell reef",
        turn="the sound came from a loose buoy, not from the clam; following it would lead the crew into deeper water",
        resolution="the crew used a rope, a lantern, and the old tide map to circle the reef and lift the real clam from a shallow pool",
        proof="the clam rang a bright note when moonlight touched its ridged shell",
        lesson="A brave crew listens closely and checks a clue before rushing into danger.",
    )
}

NAMES = [
    ("Luna", "captain"),
    ("Pip", "deckhand"),
    ("Mara", "navigator"),
    ("Toby", "cabin boy"),
    ("Nell", "lookout"),
]

TRAITS = ["curious", "kind", "cheerful", "patient", "bold"]
TELLINGS = ["moonrise", "sound_first", "map_first", "crew_first", "jester_first"]

SOUND_EFFECTS = [
    "Clonk-clonk went the loose buoy.",
    "Splash-swish answered the tide.",
    "Scritch-scratch whispered over the shells.",
    "Plip-plop fell from the pier ropes.",
    "Whoosh went the warm sea wind.",
]

JESTER_LINES = [
    '"A clam with a bell? I hope it knows a good song!"',
    '"If the sea says clonk, we should ask what it means before we shout back!"',
    '"My hat is brave, but it cannot swim. Let us use the rope instead."',
    '"A proper quest needs two things: careful feet and a very silly face."',
    '"I can make a funny noise, but I cannot make a safe tide. Let us read the map!"',
]


@dataclass
class StoryParams:
    place: str
    activity: str
    quest: str
    name: str
    role: str
    trait: str
    telling: str = ""
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pirate tale quest about a bunt, a clam, a jester, and sound effects."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--activity", choices=ACTIVITIES)
    parser.add_argument("--quest", choices=QUESTS)
    parser.add_argument("--name")
    parser.add_argument("--role", choices=[role for _, role in NAMES])
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--telling", choices=TELLINGS)
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
    if args.place and args.place != "moonlit_cove":
        raise StoryError("This pirate tale takes place only in Moonlit Cove.")
    if args.activity and args.activity != "clam_quest":
        raise StoryError("Only the clam quest belongs to this storyworld.")
    if args.quest and args.quest != "bell_clam":
        raise StoryError("Only the bell clam quest is available.")
    if args.name is None and args.role is None:
        name, role = rng.choice(NAMES)
    elif args.name is not None and args.role is not None:
        name, role = args.name, args.role
    elif args.name is not None:
        name = args.name
        role = next((r for n, r in NAMES if n == name), "captain")
    else:
        role = args.role
        name = next((n for n, r in NAMES if r == role), "Luna")
    return StoryParams(
        place="moonlit_cove",
        activity="clam_quest",
        quest="bell_clam",
        name=name,
        role=role,
        trait=args.trait or rng.choice(TRAITS),
        telling=args.telling or rng.choice(TELLINGS),
    )


def tell(params: StoryParams, rng: random.Random) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    quest = QUESTS[params.quest]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.role,
        label=params.name,
        meters={"courage": 1.0, "care": 1.0},
        memes={"listening": 0.0},
    ))
    jester = world.add(Entity(
        id="jester",
        kind="character",
        type="jester",
        label="Jester Jory",
        meters={"courage": 1.0},
        memes={"humor": 1.0},
    ))
    clam = world.add(Entity(
        id="clam",
        kind="thing",
        type="clam",
        label=quest.object_label,
        meters={"hidden": 1.0, "safe": 0.0},
        memes={},
    ))
    bunt = world.add(Entity(
        id="bunt",
        kind="thing",
        type="flag",
        label="the bunt",
        meters={"raised": 0.0},
        memes={},
    ))

    opening = {
        "moonrise": f"Moonlight spilled across Moonlit Cove while {hero.label}, a {params.trait} pirate {params.role}, watched the waves from the deck.",
        "sound_first": f'"Clonk-clonk!" cried a sound from Moonlit Cove. {hero.label}, a {params.trait} pirate {params.role}, hurried to the rail.',
        "map_first": f"{hero.label}, a {params.trait} pirate {params.role}, spread an old tide map beneath the lantern as Moonlit Cove glittered below.",
        "crew_first": f"The crew of the little ship trusted {hero.label}, a {params.trait} pirate {params.role}, to notice small troubles before they grew.",
        "jester_first": f"Jester Jory wore a crooked hat and a serious smile as {hero.label}, a {params.trait} pirate {params.role}, steered toward Moonlit Cove.",
    }[params.telling]
    world.say(opening)
    world.say("The captain had promised a gentle quest: find the silver bell clam and bring its song back to the ship.")
    world.say(f"{SOUND_EFFECTS[0]} From beneath the pier came {quest.clue}.")
    world.facts["sound_heard"] = True
    world.para()

    if params.telling == "map_first":
        world.say("The tide map showed a shallow pool beyond the reef, but it also showed a dangerous bend.")
        world.say(quest.obstacle.capitalize() + ".")
    else:
        world.say(quest.obstacle.capitalize() + ".")
        world.say("The crew could not see the pool through the moonlit spray, so the map became important.")
    world.say(f'Jester Jory waved the bunt and called, {rng.choice(JESTER_LINES)}')
    world.say(f'{hero.label} answered, "First we learn which sound is real. Then we choose the safe way."')
    world.say("The exchange changed the plan: nobody would chase a noise into deep water.")
    hero.memes["listening"] = 1.0
    bunt.meters["raised"] = 1.0
    world.facts["bunt_raised"] = True
    world.para()

    world.say(quest.turn.capitalize() + ".")
    world.say(f"{SOUND_EFFECTS[1]} The loose buoy knocked against the pier in the same rhythm as the false call.")
    world.say(f"{hero.label} tapped the bunt twice, and the crew answered from the safe side of the cove.")
    world.say("The echoes showed them that the real clam was farther around the reef, where the tide map marked a shallow pool.")
    world.facts["false_sound_found"] = True
    world.facts["route_known"] = True
    world.para()

    world.say(quest.resolution.capitalize() + ".")
    clam.meters["hidden"] = 0.0
    clam.meters["safe"] = 1.0
    world.facts["resolved"] = True
    world.say(f"{SOUND_EFFECTS[2]} The shell brushed the rope, but the careful route kept every pirate safe.")
    world.say(quest.proof.capitalize() + ".")
    world.para()

    world.say("Back aboard, Jester Jory gave the bunt a grand bow.")
    world.say(f"{hero.label} laughed, and the clam answered with one soft ring: {activity.sound}.")
    world.say(f"The cove grew quiet except for the tide, and the crew remembered: {quest.lesson}")
    world.facts.update(
        hero=hero,
        jester=jester,
        clam=clam,
        bunt=bunt,
        quest=quest,
        activity=activity,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    seed = params.seed if params.seed is not None else sum(ord(c) for c in params.name + params.telling)
    world = tell(params, random.Random(seed ^ 0xBUNT))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=make_story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    return [
        f"Write a child-friendly pirate tale about {hero.label}'s quest for a bell clam.",
        "Include a bunt, a jester, sound effects, a misleading clue, and a safe resolution.",
        "Let a pirate listen carefully before choosing a route across a dangerous tide.",
    ]


def make_story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    quest = world.facts["quest"]
    return [
        QAItem(
            question=f"Who led the quest in Moonlit Cove?",
            answer=f"{hero.label}, a {hero.type}, led the quest with careful listening.",
        ),
        QAItem(
            question="What did the crew hope to find?",
            answer=f"They hoped to find {quest.object_label} and bring its gentle song back to the ship.",
        ),
        QAItem(
            question="What did the first clonk-clonk sound really come from?",
            answer="The first sound came from a loose buoy knocking against the pier, not from the clam.",
        ),
        QAItem(
            question="How did the bunt help the pirates?",
            answer="The raised bunt helped the crew signal across the cove and test echoes while they stayed on safe ground.",
        ),
        QAItem(
            question="How did the crew reach the clam safely?",
            answer="They used a rope, a lantern, and the old tide map to circle the sharp reef and reach the shallow pool.",
        ),
        QAItem(
            question="What proved that the quest succeeded?",
            answer=quest.proof.capitalize() + ".",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clam?",
            answer="A clam is a shelled sea animal that can live in sand or shallow water.",
        ),
        QAItem(
            question="What is a bunt?",
            answer="A bunt is a flag or cloth signal raised so people can see a message from a distance.",
        ),
        QAItem(
            question="What does a jester do?",
            answer="A jester entertains people with jokes, playful ideas, and funny performances.",
        ),
        QAItem(
            question="Why should sailors check a sound before following it?",
            answer="A sound can come from a different object than expected, so checking it helps sailors avoid danger.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id:8} ({entity.type:8}) meters={meters} memes={memes}")
    lines.append(f"  facts: resolved={world.facts.get('resolved', False)}, route_known={world.facts.get('route_known', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
heard_sound :- activity(clam_quest), sound_effect(clam_quest).
safe_route :- map_used, echo_checked, bunt_raised.
found_clam :- safe_route, clam_hidden.
resolved :- found_clam, clam_safe.
"""


def asp_facts() -> str:
    import asp
    facts = [
        asp.fact("setting", "moonlit_cove"),
        asp.fact("affords", "moonlit_cove", "clam_quest"),
        asp.fact("activity", "clam_quest"),
        asp.fact("quest", "bell_clam"),
        asp.fact("object", "bell_clam", "clam"),
        asp.fact("sound_effect", "clam_quest"),
        asp.fact("clam_hidden"),
        asp.fact("map_used"),
        asp.fact("echo_checked"),
        asp.fact("bunt_raised"),
        asp.fact("clam_safe"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show resolved/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show resolved/0."))
        resolved = bool(asp.atoms(model, "resolved"))
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if not resolved:
        print("MISMATCH: ASP did not resolve the safe clam quest.")
        return 1
    sample = generate(CURATED[0])
    required = ["bunt", "clam", "jester", "clonk-clonk"]
    missing = [word for word in required if word not in sample.story.lower()]
    if missing:
        print("MISMATCH: generated story lacks " + ", ".join(missing))
        return 1
    print("OK: Python story and ASP twin agree on the resolved quest.")
    return 0


CURATED = [
    StoryParams(
        place="moonlit_cove",
        activity="clam_quest",
        quest="bell_clam",
        name="Luna",
        role="captain",
        trait="curious",
        telling="moonrise",
        seed=501,
    ),
    StoryParams(
        place="moonlit_cove",
        activity="clam_quest",
        quest="bell_clam",
        name="Mara",
        role="navigator",
        trait="patient",
        telling="map_first",
        seed=502,
    ),
    StoryParams(
        place="moonlit_cove",
        activity="clam_quest",
        quest="bell_clam",
        name="Pip",
        role="deckhand",
        trait="cheerful",
        telling="jester_first",
        seed=503,
    ),
]


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

    if args.verify:
        raise SystemExit(asp_verify())

    if args.show_asp:
        print(asp_program())
        return

    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program("#show resolved/0."))
            print("ASP model:")
            print("  resolved" if asp.atoms(model, "resolved") else "  unresolved")
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(20, args.n * 20):
            seed = base_seed + attempt
            attempt += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as exc:
                print(exc)
                return
            params.seed = seed
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
