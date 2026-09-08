#!/usr/bin/env python3
"""
A small detective storyworld about a helpful servant, a mistaken sound, and a
quest to find what is making a mysterious noise.
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


SETTINGS = {
    "old_manor": {
        "place": "the old manor",
        "detail": "Rain tapped the tall windows, and long hallways curled around the quiet old manor.",
        "affords": {"investigate", "search"},
    },
    "harbor_house": {
        "place": "the harbor house",
        "detail": "Gulls cried outside while ropes knocked softly against the pilings below the harbor house.",
        "affords": {"investigate", "search"},
    },
    "clocktower_lodge": {
        "place": "the clocktower lodge",
        "detail": "A giant clock watched over the lodge, and every small sound seemed to echo twice.",
        "affords": {"investigate", "search"},
    },
}

NAMES = ["Luna", "Milo", "Nora", "Tess", "Arlo", "Pia", "Kian", "Ivy"]
NAME_GENDERS = {
    "Luna": "girl", "Milo": "boy", "Nora": "girl", "Tess": "girl",
    "Arlo": "boy", "Pia": "girl", "Kian": "boy", "Ivy": "girl",
}
SERVANTS = ["Marta", "Jules", "Nell", "Bram"]
TRAITS = ["curious", "careful", "brave", "patient", "clever", "cheerful"]

CASES = [
    {
        "id": "silver_tray",
        "arrival": "The household's silver tray vanished just before supper.",
        "sound": "A bright clink-clink came from behind the library wall.",
        "mistake": "Everyone thought the servant had hidden the tray because the sound followed the servant's footsteps.",
        "clue": "Luna noticed that the clink came one heartbeat after each step, not at the same time.",
        "quest": "They followed the sound through the library, past the coat room, and into the pantry.",
        "reveal": "A loose spoon had fallen into a rolling bread cart and was tapping its metal wheel.",
        "ending": "The silver tray was found under a folded tablecloth, while the spoon rested in the bread cart like a tiny bell.",
        "lesson": "a repeated sound can make a wrong story seem true",
        "servant_line": "I carried the tray to the pantry, but I did not put it behind a wall.",
        "child_line": "Then the sound must be telling us where it is not.",
        "object": "silver tray",
    },
    {
        "id": "missing_key",
        "arrival": "The brass key to the music room disappeared before the evening concert.",
        "sound": "A soft jingle came from the servant's cupboard.",
        "mistake": "The guests suspected the servant had taken the key to keep everyone out.",
        "clue": "Luna heard the jingle only when the cupboard door trembled in the draft.",
        "quest": "The team searched the cupboard, the coat hooks, and the narrow stair beneath the music room.",
        "reveal": "The key had slipped into a wool scarf, and the scarf was brushing the cupboard door.",
        "ending": "The key opened the music room, and the scarf hung quietly without pretending to be a suspect.",
        "lesson": "a fair detective checks the source of a sound before blaming a person",
        "servant_line": "I know every cupboard in this house, and that key is not hiding from me on purpose.",
        "child_line": "We will ask the cupboard what it knows, but gently.",
        "object": "brass key",
    },
    {
        "id": "crying_window",
        "arrival": "A guest reported that a child was crying behind the nursery window.",
        "sound": "Wah-wah-wah floated through the hall whenever the wind blew.",
        "mistake": "The servant hurried to rescue a child who was not there.",
        "clue": "Luna saw the curtain puff outward exactly when the sound began.",
        "quest": "They followed the eerie wail from the nursery to the attic and then along the roof-side passage.",
        "reveal": "A loose shutter was rubbing against a wooden sign painted with a sad face.",
        "ending": "The shutter was fastened, and the sad painted face became just a face again.",
        "lesson": "listening and looking together can turn a frightening misunderstanding into a simple repair",
        "servant_line": "I heard a cry, so I came quickly. I am glad we found a shutter instead of a child in danger.",
        "child_line": "The window was acting like an actor, but it forgot to say it was pretending.",
        "object": "window shutter",
    },
    {
        "id": "footsteps",
        "arrival": "The manor bell rang once, and then mysterious footsteps crossed the empty gallery.",
        "sound": "Tap, tap, tap echoed behind the servant's room.",
        "mistake": "The household guessed that the servant had invited a secret visitor.",
        "clue": "Luna found three damp spots on the floor, each directly below a ceiling leak.",
        "quest": "They followed the taps through the gallery, down the back stairs, and into the laundry.",
        "reveal": "Rainwater was dropping onto three upside-down buckets.",
        "ending": "The buckets were moved beneath the leaks, and the ghostly footsteps stopped.",
        "lesson": "a pattern can point to weather and objects instead of a hidden person",
        "servant_line": "No visitor came through my room. The rain may be the one knocking.",
        "child_line": "Then we should interview the buckets before they dry up.",
        "object": "three buckets",
    },
    {
        "id": "whistle",
        "arrival": "A silver whistle went missing from the guard's desk during a windy afternoon.",
        "sound": "A sharp tweet came from the servant's garden basket.",
        "mistake": "The guard believed the servant had taken the whistle for a joke.",
        "clue": "Luna found a reed caught in the basket weave, with a hole shaped like a tiny mouth.",
        "quest": "The detectives carried the basket through the garden, greenhouse, and tool shed to test the wind.",
        "reveal": "Air was blowing through the reed and making the whistle sound.",
        "ending": "The real whistle was found in the guard's pocket, and the reed received no badge.",
        "lesson": "sound effects can imitate an object without being the object",
        "servant_line": "I never touched the guard's whistle. The basket may be making a very poor imitation.",
        "child_line": "It has the sound, but not the permission to call itself a whistle.",
        "object": "garden basket",
    },
    {
        "id": "hidden_letter",
        "arrival": "A sealed letter for the mayor disappeared from the front table.",
        "sound": "Scratch-scratch came from inside the servant's travel trunk.",
        "mistake": "The mayor's aide thought the servant was hiding the important letter.",
        "clue": "Luna saw a thin line of paper beneath the trunk lid and heard the scratching pause whenever the lid moved.",
        "quest": "They searched the entry, the servant's room, and the luggage room without opening anything that was locked.",
        "reveal": "A dry leaf was trapped with the letter beneath the trunk lid, and the leaf scratched the wood.",
        "ending": "The letter was delivered, while the dry leaf was swept outside to scratch in the garden.",
        "lesson": "a careful quest protects people from guesses and objects from careless handling",
        "servant_line": "I want the letter found, but I also want its seal kept whole.",
        "child_line": "A quiet detective can be quick without being rough.",
        "object": "sealed letter",
    },
    {
        "id": "clock_growl",
        "arrival": "The old clock began to growl before every dinner bell.",
        "sound": "Grrr-rumble came from the servant's pantry shelf.",
        "mistake": "The cook suspected that the servant had placed a hungry animal among the pots.",
        "clue": "Luna felt the shelf vibrate whenever the clock's heavy weight dropped.",
        "quest": "They traced the vibration from the pantry to the clock room and up the winding stairs.",
        "reveal": "A loose clock panel was rubbing against the wall and turning a tick into a growl.",
        "ending": "The panel was tightened, and the dinner bell sounded clear instead of hungry.",
        "lesson": "vibration can change a small sound into a frightening one",
        "servant_line": "There is no animal in my pantry, unless the clock has learned to eat time.",
        "child_line": "Let us inspect the clock before we serve it supper.",
        "object": "clock panel",
    },
    {
        "id": "vanishing_cup",
        "arrival": "A blue teacup disappeared from the breakfast table each morning.",
        "sound": "Clatter-clatter came from the servant's linen cart.",
        "mistake": "The family thought the servant was collecting cups without telling anyone.",
        "clue": "Luna noticed a blue thread caught on the cart's wheel.",
        "quest": "They rolled the cart from the breakfast room to the linen closet and checked every turn.",
        "reveal": "The cup had been placed on the cart and slid beneath a folded blanket when the wheel bumped the door.",
        "ending": "The blue cup returned to the breakfast table, and the cart carried linens without any secrets.",
        "lesson": "following a small physical clue can solve a large misunderstanding",
        "servant_line": "I moved the linens, not the cup. The cart may have carried more than I knew.",
        "child_line": "Then the wheel is our witness, and the blanket is hiding the evidence.",
        "object": "blue teacup",
    },
]

ROUTES = [
    ("One rainy evening", "The first clue appeared when", "At last"),
    ("Before the household woke", "Instead of blaming anyone,", "After a careful search"),
    ("Near the end of supper", "Then Luna noticed something important:", "By following the sound"),
    ("During a stormy afternoon", "The detective paused and asked,", "A few minutes later"),
    ("Just after the bell rang", "The quest changed when", "Once the evidence was checked"),
    ("In the quietest hallway", "Luna listened again.", "With everyone working together"),
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    servant: str
    trait: str
    seed: Optional[int] = None
    case: int = 0
    route: int = 0
    sound_style: int = 0
    cadence: int = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A detective storyworld about a servant, a misunderstanding, and mysterious sound effects."
    )
    parser.add_argument("--place", choices=SETTINGS.keys())
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--servant", choices=SERVANTS)
    parser.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    return StoryParams(
        place=args.place or rng.choice(list(SETTINGS)),
        name=name,
        gender=args.gender or NAME_GENDERS[name],
        servant=args.servant or rng.choice(SERVANTS),
        trait=args.trait or rng.choice(TRAITS),
        case=rng.randrange(len(CASES)),
        route=rng.randrange(len(ROUTES)),
        sound_style=rng.randrange(8),
        cadence=rng.randrange(64),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("The detective needs a known setting.")
    if params.name not in NAMES:
        raise StoryError("The child detective must have a registered name.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("The detective must be identified as a girl or boy.")
    if params.servant not in SERVANTS:
        raise StoryError("The servant must be chosen from the servant registry.")
    if not 0 <= params.case < len(CASES):
        raise StoryError("The selected case is outside the case registry.")


def _build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    setting = SETTINGS[params.place]
    case = CASES[params.case]
    route = ROUTES[params.route % len(ROUTES)]
    world = World(place=setting["place"])

    child = world.add(Entity(
        id="Detective",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"curiosity": 1.0, "care": 1.0},
        memes={"patience": 1.0},
    ))
    servant = world.add(Entity(
        id="Servant",
        kind="character",
        type="servant",
        label=params.servant,
        meters={"worry": 1.0, "helpfulness": 1.0},
        memes={"trust": 1.0},
    ))
    sound = world.add(Entity(
        id="Sound",
        kind="effect",
        type="sound_effect",
        label="mysterious sound",
        phrase=case["sound"],
        meters={"loudness": 0.7, "certainty": 0.0},
        memes={"mystery": 1.0},
    ))
    clue = world.add(Entity(
        id="Clue",
        kind="evidence",
        type="physical_clue",
        label="physical clue",
        phrase=case["clue"],
        meters={"reliability": 1.0},
        memes={"usefulness": 1.0},
    ))
    quest = world.add(Entity(
        id="Quest",
        kind="task",
        type="investigation",
        label="sound investigation",
        meters={"progress": 0.0, "risk": 0.2},
        memes={"fairness": 1.0},
    ))
    suspect = world.add(Entity(
        id="SuspectedServant",
        kind="role",
        type="misunderstanding",
        label="wrong suspicion",
        meters={"truth": 0.0},
        memes={"confusion": 1.0},
    ))
    cause = world.add(Entity(
        id="Cause",
        kind="thing",
        type="hidden_cause",
        label=case["object"],
        meters={"found": 0.0},
        memes={"ordinary": 1.0},
    ))

    sound_openings = [
        "The noise sounded like a tiny warning bell.",
        "The noise bounced through the rooms as if it had feet.",
        "The noise was so strange that even the clock seemed to listen.",
        "The noise arrived in three neat beats and then vanished.",
        "The noise made the hallway feel much longer than it was.",
        "The noise had a comic little wobble at the end.",
        "The noise whispered, clattered, and then pretended nothing had happened.",
        "The noise was not loud, but it was very good at getting attention.",
    ]
    detective_notes = [
        "Luna wrote the sound in her notebook as evidence, not as a conclusion.",
        "The detective drew three arrows and refused to draw a suspect.",
        "A careful question was placed beside the sound mark in the notebook.",
        "The child counted the pauses between the noises before making a guess.",
        "The detective listened once with eyes closed and once while watching the room.",
        "The notebook received a large question mark and a very small exclamation point.",
        "Luna compared the sound's rhythm with the movement of nearby objects.",
        "The child decided that a mystery deserved curiosity before courage.",
    ]
    transition_lines = [
        "The hallway seemed to hold its breath.",
        "For a moment, the whole household waited for the sound to speak again.",
        "The rain softened, making the next clue easier to hear.",
        "Even the servant stopped polishing the rail and listened.",
        "The old building offered one more echo, but no answer.",
        "A loose curtain lifted, then fell, as if pointing.",
        "The sound repeated, but this time it carried a useful delay.",
        "The mystery became smaller when everyone described exactly what they had heard.",
    ]
    ending_notes = [
        "The household apologized to the servant and thanked them for helping.",
        "The servant smiled, and the false suspicion disappeared as quickly as the sound.",
        "Everyone agreed that a clue should be tested before a person is judged.",
        "The servant returned to work with a lighter step and a trusted name.",
        "The case went into the notebook under Solved, not Blamed.",
        "The house grew peaceful again, except for one harmless creak asking for attention.",
    ]

    world.say(f"{route[0]}, {params.name}, a {params.trait} {params.gender}, became a detective for one evening at {world.place}.")
    world.say(setting["detail"])
    world.say(f"{params.servant}, the household servant, was carrying out careful chores when the mystery began.")
    world.say(case["arrival"])
    world.para()
    world.say(case["sound"])
    world.say(sound_openings[params.sound_style])
    world.say(case["mistake"])
    world.say(f"{params.name} knew that a misunderstanding was not proof. {detective_notes[params.cadence % len(detective_notes)]}")
    world.say(f'{params.servant} said, "{case["servant_line"]}"')
    world.say(f'{params.name} answered, "{case["child_line"]}"')
    world.say("Their brief exchange changed the plan: instead of accusing the servant, they began a fair quest to trace the sound.")
    world.say(transition_lines[(params.cadence // 2) % len(transition_lines)])
    world.para()
    world.say(f"{route[1]} {case['clue']}")
    world.say(case["quest"])
    world.say(f"{params.name} checked each place while {params.servant} carried a small lamp and opened only safe, ordinary doors.")
    world.say("The sound effect repeated, but its rhythm now matched a physical object rather than a person's footsteps.")
    quest.meters["progress"] = 0.75
    world.say(f"{route[2]}, {case['reveal']}")
    world.say("The servant had not caused the trouble. The misunderstanding had grown from a sound, a delay, and a hurried guess.")
    world.para()
    cause.meters["found"] = 1.0
    sound.meters["certainty"] = 1.0
    quest.meters["progress"] = 1.0
    suspect.meters["truth"] = 1.0
    servant.meters["worry"] = 0.0
    servant.memes["trust"] = 2.0
    child.memes["patience"] = 2.0
    world.say(case["ending"])
    world.say(f"{params.name} learned that {case['lesson']}.")
    world.say(ending_notes[params.cadence % len(ending_notes)])
    world.say("The next mysterious noise received the same treatment: listen, look, ask, and only then decide.")

    world.facts.update(
        detective=child,
        servant=servant,
        sound=sound,
        clue=clue,
        quest=quest,
        suspect=suspect,
        cause=cause,
        case=case,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    case = world.facts["case"]
    return [
        f"Write a child-friendly detective story about {params.name}, a servant named {params.servant}, and a mysterious sound at {world.place}.",
        f"Tell a story with a misunderstanding, a fair quest, sound effects, and the clue that {case['lesson']}.",
        f"Write a gentle detective mystery in which the servant is wrongly suspected and dialogue changes the investigation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    case = world.facts["case"]
    return [
        QAItem(
            question=f"Who became the detective in the story?",
            answer=f"{params.name}, a {params.trait} {params.gender}, became the detective at {world.place}.",
        ),
        QAItem(
            question="Why was the servant misunderstood?",
            answer=f"The servant was misunderstood because {case['mistake'].lower().rstrip('.')}.",
        ),
        QAItem(
            question="What sound effect began the quest?",
            answer=f"The quest began with this sound effect: {case['sound']}",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=case["clue"],
        ),
        QAItem(
            question="What was the real cause of the sound?",
            answer=case["reveal"],
        ),
        QAItem(
            question="What did the detective learn?",
            answer=f"{params.name} learned that {case['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective gathers clues, asks questions, and tests ideas to solve a mystery.",
        ),
        QAItem(
            question="What is a servant?",
            answer="A servant is a person whose work is to help care for a household or serve other people.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong meaning or makes an incorrect guess about a situation.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful journey or search for something important.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are noises used to show or imitate actions, objects, or events.",
        ),
    ]


ASP_RULES = r"""
#show compatible/1.
compatible(story) :-
    servant_present,
    misunderstanding_checked,
    quest_completed,
    sound_explained,
    dialogue_changed_plan.
"""


def asp_facts() -> str:
    return "\n".join([
        "servant_present.",
        "misunderstanding_checked.",
        "quest_completed.",
        "sound_explained.",
        "dialogue_changed_plan.",
    ])


def asp_program(show: str = "#show compatible/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        from storyworlds import asp
        symbols = asp.one_model(asp_program())
        compatible = asp.atoms(symbols, "compatible")
        if compatible != [()]:
            print("ASP verification failed: no compatible story.", file=sys.stderr)
            return 1
    except Exception as exc:
        print(f"ASP verification failed: {exc}", file=sys.stderr)
        return 1

    for params in CURATED:
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 4:
            print("Python verification failed: incomplete generated story.", file=sys.stderr)
            return 1
        if "servant" not in sample.story.lower():
            print("Python verification failed: servant missing from prose.", file=sys.stderr)
            return 1
        if "?" not in sample.story and '"' not in sample.story:
            print("Python verification failed: dialogue missing.", file=sys.stderr)
            return 1
    return 0


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        parts = []
        if entity.meters:
            parts.append(f"meters={entity.meters}")
        if entity.memes:
            parts.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:18} ({entity.type:16}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="old_manor",
        name="Luna",
        gender="girl",
        servant="Marta",
        trait="curious",
        case=0,
        route=0,
        sound_style=1,
        cadence=7,
    ),
    StoryParams(
        place="harbor_house",
        name="Milo",
        gender="boy",
        servant="Jules",
        trait="careful",
        case=4,
        route=3,
        sound_style=5,
        cadence=18,
    ),
    StoryParams(
        place="clocktower_lodge",
        name="Nora",
        gender="girl",
        servant="Nell",
        trait="brave",
        case=6,
        route=5,
        sound_style=2,
        cadence=31,
    ),
]


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            from storyworlds import asp
            symbols = asp.one_model(asp_program())
            atoms = asp.atoms(symbols, "compatible")
            print("compatible(story)." if atoms else "no compatible story.")
        except Exception as exc:
            print(f"ASP unavailable: {exc}", file=sys.stderr)
            raise SystemExit(1)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(max(0, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name}: the servant's sound mystery"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
