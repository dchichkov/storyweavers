#!/usr/bin/env python3
"""
A child-friendly adventure storyworld about suspicion, mysterious sound effects,
and the humor that helps friends investigate bravely.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Toby"
    guardian: str = "Captain Reed"
    creature: str = "red fox"
    place: str = "the Echoing Hills"
    object: str = "brass compass"
    sound: str = "clank-squeak"
    task: str = "find the lost trail marker"


@dataclass(frozen=True)
class Mystery:
    title: str
    suspicion: str
    sound_source: str
    clue: str
    wrong_turn: str
    helper_job: str
    hero_job: str
    creature_job: str
    repair: str
    lesson: str
    ending: str


MYSTERIES = [
    Mystery(
        "The Clanking Backpack",
        "Luna suspected Toby was hiding the trail marker in his backpack",
        "a loose cooking cup was bumping against a metal water bottle",
        "the clank happened whenever Toby hopped over a stone",
        "they marched in circles while accusing one another",
        "counted the trail stones and marked the safe route with chalk",
        "checked every backpack pocket and listened for the sound's pattern",
        "sniffed the ground beside a patch of bent grass",
        "tightened the cup strap and found the marker beneath the bent grass",
        "Suspicion shrinks when people test a guess together.",
        "the trail marker stood upright while the backpack made one harmless little clank",
    ),
    Mystery(
        "The Squeaky Cave",
        "Toby suspected the red fox was copying their voices to scare them",
        "a rubbery vine was rubbing against the cave wall",
        "the squeak stopped whenever the vine was lifted",
        "they shouted at the cave until their echoes shouted back",
        "held the lantern steady and made a quiet map of the cave",
        "lifted the vine with a walking stick and listened again",
        "dropped a berry, then chased it in a very undignified tumble",
        "moved the vine aside and discovered a hidden painted arrow",
        "A loud mystery deserves a calm experiment, not a louder argument.",
        "the cave gave one final squeak as everyone laughed at the fox's berry-covered nose",
    ),
    Mystery(
        "The Rattling Bridge",
        "Luna suspected Captain Reed had warned them away from the bridge as a joke",
        "a row of seed pods was rattling beneath the bridge boards",
        "the rattling matched the wind gusts, not anyone's footsteps",
        "they tied three scarves over the bridge, which only made it look like a dancing snake",
        "tested the bridge boards one at a time with a long branch",
        "watched the seed pods and compared their rhythm with the wind",
        "stood at the far side and barked whenever a scarf flew loose",
        "removed the scarves and crossed after securing the noisy pods",
        "Evidence can turn a frightening sound into a useful warning.",
        "the bridge hummed softly while the scarves waved like a silly parade",
    ),
    Mystery(
        "The Boom in the Bushes",
        "Toby suspected the creature had stolen their lunch and was celebrating",
        "a hollow log was rolling down a small slope",
        "the boom grew softer whenever the log reached a patch of moss",
        "they hid behind a tree, but their own stomachs made louder noises",
        "searched the bushes for a safe place to rest and eat",
        "followed the rolling marks instead of blaming the fox",
        "pretended to be a drum major and marched beside the log",
        "wedged the log safely against a stump and shared the lunch",
        "Hunger and fear can make a guess seem more certain than it is.",
        "the rescued lunch tasted even better beside the quiet, mossy log",
    ),
    Mystery(
        "The Whistling Map",
        "Luna suspected the old map was warning them that Toby could not be trusted",
        "a tiny reed whistle was tucked inside the map case",
        "the whistle sounded when the map case swung from Luna's belt",
        "they folded the map backward and briefly lost the only marked path",
        "copied the landmarks onto a fresh page",
        "opened the case carefully and checked what was inside",
        "chased the whistle's tune and returned with a feather",
        "removed the reed and followed the landmarks in the right order",
        "A strange message may have a simple source, so inspect before interpreting.",
        "the map lay flat beneath a laughing feather while the real path led onward",
    ),
    Mystery(
        "The Sneezing Stones",
        "Toby suspected someone was hiding behind the stones and spying on them",
        "dry dust puffed through cracks whenever the wind blew",
        "the dust marks formed little gray rings on the ground",
        "they challenged the stones to come out, then apologized when nothing answered",
        "checked the cracks from a safe distance",
        "waved a scarf to see whether the dust moved with the wind",
        "sneezed so loudly that a bird dropped a twig",
        "cleared the loose dust and found a carved arrow behind the stones",
        "Careful observation can replace suspicion with a safer plan.",
        "the stones kept their secret no longer, and the carved arrow pointed to camp",
    ),
    Mystery(
        "The Giggle Trap",
        "Luna suspected Toby had rigged a trap to make her look foolish",
        "a hollow gourd was bouncing on a cord and making giggle-like thumps",
        "the cord was tied to a branch that bent in the breeze",
        "Toby tried to look brave, slipped on a leaf, and made the gourd giggle harder",
        "held the branch still while Luna examined the cord",
        "apologized for the accusation and measured the cord's reach",
        "performed an accidental bow to the gourd",
        "untied the cord and found a trail ribbon beneath the leaves",
        "Humor can soften an apology, but checking facts completes the repair.",
        "the gourd became a harmless camp drum for their victory march",
    ),
    Mystery(
        "The Drumming Pack",
        "Toby suspected the creature had taken the supplies and was drumming on them",
        "a pinecone was bouncing inside a hollow pack",
        "the drumming stopped whenever the pack was set upright",
        "they opened every pocket except the one holding the actual clue",
        "organized the supplies so nothing heavy could roll",
        "turned the pack upright and inspected the bottom pocket",
        "sat on the pack for one second and sprang up when it puffed",
        "removed the pinecone and found the missing trail marker",
        "A small test can save a team from a large and silly search.",
        "the pack rested quietly while the marker flashed in the afternoon sun",
    ),
]

OPENINGS = [
    "At sunrise",
    "Beyond the last village gate",
    "On a bright morning",
    "Near the edge of the wild hills",
    "Before the first mountain cloud appeared",
    "Under a sky full of kite-shaped clouds",
    "At the start of the explorers' trail",
]

QUESTIONS = [
    "What did we actually hear, and when did it happen?",
    "Can we test the sound before we blame anyone?",
    "Let us follow the clue instead of the suspicion.",
    "Who can watch the sound while someone else checks the path?",
    "Could the noise have a simpler cause?",
    "We can be brave without being unfair.",
]

TEAMWORK_IMAGES = [
    "They divided the investigation into listening, looking, and marking.",
    "They made a tiny plan and repeated it so everyone knew the next step.",
    "One friend watched the sound while the other checked the ground.",
    "They compared their observations before choosing a direction.",
    "They used a stick, a lantern, and a chalk mark instead of wild guesses.",
    "They laughed once, then returned to the evidence.",
]

PERSPECTIVES = [
    "Luna remembered that courage included admitting a wrong guess.",
    "Toby decided every future expedition would include a listening break.",
    "Captain Reed praised their careful investigation more than their speed.",
    "The red fox learned that a silly face could cheer a worried team.",
    "The explorers added the clue to their camp journal.",
    "Everyone agreed that the funniest part was safer after the mystery was solved.",
]


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    params: StoryParams
    hero: Entity
    helper: Entity
    guardian: Entity
    creature: Entity
    place: str
    mystery: Mystery
    suspicious: bool = False
    investigated: bool = False
    resolved: bool = False
    sound_explained: bool = False
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        description="An adventure world of suspicion, sound effects, and careful humor."
    )
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--guardian")
    parser.add_argument("--creature")
    parser.add_argument("--place")
    parser.add_argument("--object")
    parser.add_argument("--sound")
    parser.add_argument("--task")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(["Luna", "Mara", "Nell", "Suki"]),
        helper=args.helper or rng.choice(["Toby", "Finn", "Jo", "Pax"]),
        guardian=args.guardian or rng.choice(["Captain Reed", "Ranger Sol", "Aunt Mira"]),
        creature=args.creature or rng.choice(["red fox", "young badger", "cheeky raven"]),
        place=args.place or rng.choice(["the Echoing Hills", "Whistlewood Forest", "the Moonstone Pass"]),
        object=args.object or rng.choice(["brass compass", "silver whistle", "blue trail marker"]),
        sound=args.sound or rng.choice(["clank-squeak", "boom-boom", "whistle-pop"]),
        task=args.task or "find the lost trail marker",
    )


def _validate(params: StoryParams) -> None:
    forbidden = {"poison", "weapon", "dangerous", "broken"}
    for value, label in [
        (params.hero, "hero"),
        (params.helper, "helper"),
        (params.guardian, "guardian"),
        (params.creature, "creature"),
        (params.place, "place"),
        (params.object, "object"),
        (params.sound, "sound"),
        (params.task, "task"),
    ]:
        if not value or not value.strip():
            raise StoryError(f"The {label} must not be empty.")
        if value.lower().strip() in forbidden:
            raise StoryError(f"The {label} must describe a gentle adventure, not {value!r}.")


def _stable_rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xA71D5)
    key = "|".join(
        [
            params.hero,
            params.helper,
            params.guardian,
            params.creature,
            params.place,
            params.object,
            params.sound,
            params.task,
        ]
    )
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _ground(mystery: Mystery, params: StoryParams) -> Mystery:
    values = {
        "hero": params.hero,
        "helper": params.helper,
        "guardian": params.guardian,
        "creature": params.creature,
        "object": params.object,
        "sound": params.sound,
    }

    def apply(text: str) -> str:
        return text.format(**values)

    return Mystery(
        title=apply(mystery.title),
        suspicion=apply(mystery.suspicion),
        sound_source=apply(mystery.sound_source),
        clue=apply(mystery.clue),
        wrong_turn=apply(mystery.wrong_turn),
        helper_job=apply(mystery.helper_job),
        hero_job=apply(mystery.hero_job),
        creature_job=apply(mystery.creature_job),
        repair=apply(mystery.repair),
        lesson=apply(mystery.lesson),
        ending=apply(mystery.ending),
    )


def _setup(world: World, opening: str) -> None:
    p = world.params
    world.say(
        f"{opening}, {p.hero} and {p.helper} set out through {p.place}. "
        f"They carried a lantern, a walking stick, and a {p.object} for their adventure."
    )
    world.say(
        f"{p.guardian} had asked them to {p.task}. The path was quiet until the bushes made "
        f"a strange sound: '{p.sound}!' Even the {p.creature} froze with one paw in the air."
    )


def _suspicion(world: World) -> None:
    p = world.params
    mystery = world.mystery
    world.para()
    world.suspicious = True
    world.hero.add_meme("worry", 1)
    world.helper.add_meme("uncertainty", 1)
    world.creature.add_meme("curiosity", 1)
    world.say(f"The mystery became known as {mystery.title}. {mystery.suspicion}.")
    world.say(f"{_name(p.hero)} said, \"I heard {p.sound}. Did you do that?\"")
    world.say(f"{_name(p.helper)} replied, \"No! But I thought you did. Maybe the {p.creature} did it.\"")
    world.say(f"Then {mystery.wrong_turn}. The sound answered with another ridiculous '{p.sound}!'.")


def _investigate(world: World, question: str, method: str) -> None:
    p = world.params
    mystery = world.mystery
    world.para()
    world.investigated = True
    world.hero.add_meme("courage", 1)
    world.helper.add_meme("patience", 1)
    world.say(f"{_name(p.hero)} raised the {p.object} and said, \"{question}\"")
    world.say(f"{_name(p.helper)} answered, \"Good plan. {method}\"")
    world.say(f"They listened again. The important clue was this: {mystery.clue}.")
    world.say(
        f"Together they discovered the real source: {mystery.sound_source}. "
        f"The suspicion loosened as neatly as a knot pulled by patient fingers."
    )
    world.say(
        f"{_name(p.helper)} {mystery.helper_job}; {_name(p.hero)} {mystery.hero_job}; "
        f"and the {p.creature} {mystery.creature_job}."
    )


def _resolve(world: World, perspective: str) -> None:
    p = world.params
    mystery = world.mystery
    world.para()
    world.resolved = True
    world.sound_explained = True
    world.hero.add_meme("trust", 1)
    world.helper.add_meme("trust", 1)
    world.say(f"The repair worked: they {mystery.repair}.")
    world.say(
        f"{_name(p.hero)} told {p.helper}, \"I am sorry I let my suspicion speak first.\" "
        f"{_name(p.helper)} smiled. \"I am sorry I guessed too. Next time, we investigate together.\""
    )
    world.say(f"{_name(p.guardian)} later said, \"{mystery.lesson}\"")
    world.say(
        f"At last, {mystery.ending}. {perspective} "
        f"The expedition continued with brave questions instead of unfair blame."
    )


def _name(value: str) -> str:
    return value[:1].upper() + value[1:]


def tell(params: StoryParams) -> World:
    _validate(params)
    rng = _stable_rng(params)
    mystery = _ground(rng.choice(MYSTERIES), params)
    world = World(
        params=params,
        hero=Entity(params.hero, "hero"),
        helper=Entity(params.helper, "helper"),
        guardian=Entity(params.guardian, "guardian"),
        creature=Entity(params.creature, "creature"),
        place=params.place,
        mystery=mystery,
    )
    _setup(world, rng.choice(OPENINGS))
    _suspicion(world)
    _investigate(world, rng.choice(QUESTIONS), rng.choice(TEAMWORK_IMAGES))
    _resolve(world, rng.choice(PERSPECTIVES))
    world.facts = {
        "place": params.place,
        "hero": params.hero,
        "helper": params.helper,
        "guardian": params.guardian,
        "creature": params.creature,
        "object": params.object,
        "sound": params.sound,
        "mystery": mystery.title,
        "suspicion": mystery.suspicion,
        "sound_source": mystery.sound_source,
        "clue": mystery.clue,
        "repair": mystery.repair,
        "resolved": world.resolved,
    }
    return world


ASP_RULES = r"""
hero(X) :- hero_name(X).
helper(X) :- helper_name(X).
suspicion :- hears(hero, sound), guesses(hero, helper).
investigated :- asks_test(hero), observes(helper), observes(creature).
resolved :- suspicion, investigated, explains_sound(helper), repairs_trust(hero, helper).
#show suspicion/0.
#show investigated/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hero_name", "luna"),
            asp.fact("helper_name", "toby"),
            asp.fact("hears", "hero", "sound"),
            asp.fact("guesses", "hero", "helper"),
            asp.fact("asks_test", "hero"),
            asp.fact("observes", "helper"),
            asp.fact("observes", "creature"),
            asp.fact("explains_sound", "helper"),
            asp.fact("repairs_trust", "hero", "helper"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception:
        print("ASP verification unavailable: clingo helper not installed.")
        return 1
    model = asp.one_model(
        asp_program(
            "#show suspicion/0.\n#show investigated/0.\n#show resolved/0."
        )
    )
    found = {str(atom) for atom in model}
    expected = {"suspicion", "investigated", "resolved"}
    if expected.issubset(found):
        sample = generate(StoryParams(seed=17))
        if not sample.story or not sample.story_qa:
            print("MISMATCH: generated story verification failed.")
            return 1
        print("OK: ASP and Python both reach a repaired adventure.")
        return 0
    print("MISMATCH: ASP twin did not reach the expected state.")
    return 1


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write an adventure about {p.hero} and {p.helper} investigating suspicion caused by a '{p.sound}' sound.",
        f"Tell a funny, child-friendly mystery in {p.place} where a sound effect seems suspicious but has a simple cause.",
        f"Write a story where {p.hero} and {p.helper} use teamwork to finish the task: {p.task}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    mystery = world.mystery
    return [
        QAItem(
            question=f"Why did {p.hero} and {p.helper} become suspicious?",
            answer=f"They heard a strange '{p.sound}' sound and each briefly guessed that someone else had caused it. The sound made the ordinary adventure seem mysterious.",
        ),
        QAItem(
            question="What clue helped the explorers investigate?",
            answer=f"They noticed that {mystery.clue}. That pattern helped them test the sound instead of relying on suspicion.",
        ),
        QAItem(
            question="What really caused the sound?",
            answer=f"The sound came from {mystery.sound_source}. It was a harmless cause, not a secret trick by a teammate.",
        ),
        QAItem(
            question=f"How did {p.hero} and {p.helper} repair their teamwork?",
            answer=f"They listened, compared observations, apologized for their guesses, and worked together to {mystery.repair}.",
        ),
        QAItem(
            question="What final image showed that the adventure was resolved?",
            answer=f"At the end, {mystery.ending}. That concrete image showed that the trail was safe and trust had returned.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question="What is suspicion?",
            answer="Suspicion is a worried feeling that someone may have done something wrong before there is enough evidence.",
        ),
        QAItem(
            question="Why should people test a suspicion?",
            answer="Testing a suspicion helps people use evidence instead of blaming someone because of a guess.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer=f"A sound effect is a noise used to make an event clear or interesting, such as the '{p.sound}' heard on the adventure.",
        ),
        QAItem(
            question="How can humor help during an adventure?",
            answer="Humor can make a tense moment feel safer, but people should still investigate carefully and repair mistakes honestly.",
        ),
        QAItem(
            question="What makes an adventure?",
            answer="An adventure is a journey with a goal, unexpected problems, discoveries, and choices that help the travelers move forward.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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
    lines = ["--- world trace ---"]
    for entity in [world.hero, world.helper, world.guardian, world.creature]:
        lines.append(
            f"{entity.kind}: {entity.name} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(
        "state: "
        f"suspicious={world.suspicious} investigated={world.investigated} "
        f"sound_explained={world.sound_explained} resolved={world.resolved}"
    )
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hero="Luna",
        helper="Toby",
        guardian="Captain Reed",
        creature="red fox",
        place="the Echoing Hills",
        object="brass compass",
        sound="clank-squeak",
        task="find the lost trail marker",
    ),
    StoryParams(
        hero="Mara",
        helper="Finn",
        guardian="Ranger Sol",
        creature="cheeky raven",
        place="Whistlewood Forest",
        object="silver whistle",
        sound="boom-boom",
        task="return the blue trail ribbon",
    ),
    StoryParams(
        hero="Nell",
        helper="Pax",
        guardian="Aunt Mira",
        creature="young badger",
        place="the Moonstone Pass",
        object="blue trail marker",
        sound="whistle-pop",
        task="map the safest path home",
    ),
]


def asp_available() -> bool:
    try:
        import clingo  # noqa: F401
        return True
    except Exception:
        return False


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

    if args.show_asp:
        print(
            asp_program(
                "#show suspicion/0.\n#show investigated/0.\n#show resolved/0."
            )
        )
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        if not asp_available():
            print("ASP mode unavailable: clingo is not installed.")
            return
        import asp

        model = asp.one_model(
            asp_program(
                "#show suspicion/0.\n#show investigated/0.\n#show resolved/0."
            )
        )
        print("ASP model:", ", ".join(sorted(str(atom) for atom in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and attempt < limit:
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
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
        if args.all:
            header = f"### {sample.params.hero} and {sample.params.helper} in {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
